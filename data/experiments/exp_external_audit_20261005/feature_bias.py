"""外部审计对照（preregister.md）：模型 P/V 相同时，净现金占比 S、TTM 下行 T、轻资产增长 D、高回报 R 四个特征与其后回报。

    python3 feature_bias.py            # 读数 1～5 → results.json、cases.csv、pool_exposure.csv；逐月观测写 cache/observations.csv
    EXP_TEST=1 python3 feature_bias.py # 冒烟：只取 40 只、重抽 50 次，只写 cache/
"""
import bisect
import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import build_historical_valuation_bands as bhv  # noqa: E402
from divspread_names import is_divspread_financial  # noqa: E402
from moat_param_lab import forward_annualized, total_return_index  # noqa: E402

TEST = os.environ.get('EXP_TEST') == '1'
STATES = ROOT / 'data/processed/a_share_daily_states_adopted.csv'
BANDS = ROOT / 'data/processed/roic_bands.csv'
POOL = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
SCAN = ROOT / 'data/processed/daily_buy_candidates.csv'
PANEL = ROOT / 'data/processed/pit_attention/panel_moat_bank_v6b.csv'
OUT = EXP / 'cache' if TEST else EXP
START = '2010-01-01'
ROIC_PATHS = {'growth', 'zero_growth'}
PV_RANGE = (0.2, 5.0)
HORIZONS = (1, 3)
BOOT = 50 if TEST else 1000
NAMED = ('000651', '601717', '920599')
FEATURES = ('S', 'T', 'D', 'R')
BUCKETS = {
    'S': ((0.0, 0.1), (0.1, 0.3), (0.3, 0.5), (0.5, 1.01)),
    'T': ((-1.0, 1e-9), (1e-9, 0.1054), (0.1054, 0.2231), (0.2231, 99.0)),   # ttm ≥1、[0.9,1)、[0.8,0.9)、<0.8
    'D': ((-0.5, 0.5), (0.5, 1.5)),
    'R': ((-1.0, 0.2231), (0.2231, 0.9163), (0.9163, 1.6094), (1.6094, 99.0)),   # roic0 <15%、[15,30)、[30,60)、≥60%
}
BUCKET_LABELS = {
    'S': ('[0,0.1)', '[0.1,0.3)', '[0.3,0.5)', '[0.5,1]'),
    'T': ('ttm≥1', '[0.9,1)', '[0.8,0.9)', '<0.8'),
    'D': ('否', '是'),
    'R': ('<15%', '[15%,30%)', '[30%,60%)', '≥60%'),
}


def num(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def features(r) -> dict | None:
    """带行 → 四个特征；模型价值不可用时返回 None。"""
    iv, fin = num(r['intrinsic_value']), num(r['fin_net_debt_ps'])
    if iv is None or iv <= 0:
        return None
    s = min(1.0, max(0.0, -(fin or 0.0) / iv))
    ttm = num(r.get('ttm_factor'))
    t = max(0.0, -math.log(ttm)) if ttm and ttm > 0 else 0.0
    g0, gtr = num(r.get('g0')), num(r.get('g_trailing'))
    d = 1.0 if (g0 is not None and g0 <= 0 and gtr is not None and gtr >= 0.05) else 0.0
    roic0 = num(r.get('roic0'))
    rr = min(3.0, max(0.0, math.log(roic0 / 0.12))) if roic0 and roic0 > 0 else 0.0
    return dict(S=s, T=t, D=d, R=rr, ttm=ttm, g0=g0, g_trailing=gtr, roic0=roic0, trust=num(r.get('growth_trust')),
                fin_nd=fin, iv=iv)


def load_bands():
    info, rejected = {}, defaultdict(list)
    with BANDS.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ok = r['status'] == 'ok'
            key = (r['security_code'], r['report_date'], r['available_at'])
            info[key] = (ok, r['roic_path'], features(r) if ok and r['roic_path'] in ROIC_PATHS else None)
            if not ok:
                rejected[r['security_code']].append((r['available_at'], r['report_date']))
    steps = {}
    for code, rows in rejected.items():
        rows.sort()
        keys, best, cur = [], [], ''
        for avail, report in rows:
            cur = max(cur, report)
            keys.append(avail); best.append(cur)
        steps[code] = (keys, best)
    return info, steps


def month_ends(codes: set) -> dict:
    out = {}
    with STATES.open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        h = next(reader)
        ic, idt, irp, iav, ipv = (h.index(k) for k in ('security_code', 'date', 'band_report_date', 'band_available_at', 'valuation_ratio'))
        for row in reader:
            code = row[ic]
            if code not in codes or row[idt] < START:
                continue
            key = (code, row[idt][:7])
            if key not in out or row[idt] > out[key][0]:
                out[key] = (row[idt], row[ipv], row[irp], row[iav])
    return out


def judge(rec, code, info, steps):
    """(P/V, 特征) 或 None：ok 的 ROIC 路径带、非沿用旧带、P/V > 0。"""
    if rec is None or not rec[1]:
        return None
    day, pv, report, avail = rec
    band = info.get((code, report, avail))
    if band is None or not band[0] or band[1] not in ROIC_PATHS or band[2] is None:
        return None
    step = steps.get(code)
    if step:
        i = bisect.bisect_right(step[0], day)
        if i and step[1][i - 1] > report:
            return None
    value = num(pv)
    return (value, band[2]) if value and value > 0 else None


def load_names():
    names = {}
    for path in (ROOT / 'data/raw/a_share_securities.csv', ROOT / 'data/processed/a_share_company_analysis_index.csv', PANEL):
        with path.open(newline='', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                names.setdefault(r['security_code'].zfill(6), r['security_name'])
    return names


def load_spans() -> dict:
    spans = defaultdict(list)
    with PANEL.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            spans[r['security_code'].zfill(6)].append((r['effective_from'], r.get('effective_to') or '9999-12-31'))
    return spans


def collect():
    info, steps = load_bands()
    names = load_names()
    codes = {k[0] for k, (ok, path, _f) in info.items() if ok and path in ROIC_PATHS}
    codes = {c for c in codes if not is_divspread_financial(c, names.get(c, ''))}
    if TEST:
        codes = set(sorted(codes)[:37]) | set(NAMED)
    states = month_ends(codes)
    spans = load_spans()
    actions = bhv.load_actions()
    by_code = defaultdict(list)
    for key in states:
        by_code[key[0]].append(key)
    rows = []
    for code in sorted(codes):
        prices = bhv.load_ohlcv(code)
        if not prices:
            continue
        days = [d for d, _ in prices]
        tr = total_return_index(prices, actions.get(code, []))
        for key in sorted(by_code.get(code, ())):
            got = judge(states[key], code, info, steps)
            if got is None:
                continue
            pv, feat = got
            day = states[key][0]
            fwd = {h: (forward_annualized(tr, days, day, h) if day in tr else None) for h in HORIZONS}
            rows.append(dict(code=code, name=names.get(code, ''), month=key[1], date=day,
                             panel=any(a <= day <= b for a, b in spans.get(code, ())), pv=pv,
                             **{k: feat[k] for k in ('S', 'T', 'D', 'R', 'ttm', 'g0', 'g_trailing', 'roic0', 'trust')},
                             **{f'f{h}': fwd[h] for h in HORIZONS}))
    return rows


# ---------- 统计 ----------

def demean(groups, w, *cols):
    total = np.bincount(groups, weights=w)
    safe = np.where(total > 0, total, 1.0)
    return [c - (np.bincount(groups, weights=w * c) / safe)[groups] for c in cols]


def wls(y, X, w):
    Xw = X * w[:, None]
    return np.linalg.solve(X.T @ Xw, Xw.T @ y)


def interval(values):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)])
    return [float(np.percentile(v, 5)), float(np.percentile(v, 95))] if len(v) else [None, None]


class Sample:
    def __init__(self, rows, horizon):
        rows = [r for r in rows if r[f'f{horizon}'] is not None and r[f'f{horizon}'] > -1 and PV_RANGE[0] <= r['pv'] <= PV_RANGE[1]]
        self.rows = rows
        self.y = np.log1p(np.array([r[f'f{horizon}'] for r in rows]))
        self.x = np.log(np.array([r['pv'] for r in rows]))
        self.F = {k: np.array([r[k] for r in rows], float) for k in FEATURES}
        codes = {c: i for i, c in enumerate(sorted({r['code'] for r in rows}))}
        self.stock = np.array([codes[r['code']] for r in rows], int)
        self.n_stocks = len(codes)
        months = {m: i for i, m in enumerate(sorted({r['month'] for r in rows}))}
        self.month = np.array([months[r['month']] for r in rows], int)


def boot_weights(s: Sample, rng):
    return np.bincount(rng.integers(0, s.n_stocks, s.n_stocks), minlength=s.n_stocks).astype(float)[s.stock]


def regress(s: Sample, w, feats):
    cols = demean(s.month, w, s.y, s.x, *(s.F[k] for k in feats))
    return wls(cols[0], np.column_stack(cols[1:]), w)


def readout_regressions(s: Sample, rng):
    one = np.ones(len(s.y))
    specs = [(k,) for k in FEATURES] + [FEATURES]
    draws_w = [boot_weights(s, rng) for _ in range(BOOT)]
    out = {}
    base = regress(s, one, ())
    out['b_only'] = dict(b=float(base[0]), b_ci=interval([regress(s, w, ())[0] for w in draws_w[:200]]))
    for feats in specs:
        beta = regress(s, one, feats)
        draws = []
        for w in draws_w:
            try:
                draws.append(regress(s, w, feats))
            except np.linalg.LinAlgError:
                continue
        entry = dict(b=float(beta[0]), b_ci=interval([d[0] for d in draws]))
        for i, k in enumerate(feats, 1):
            entry[f'c_{k}'] = float(beta[i])
            entry[f'delta_{k}'] = float(beta[i] / beta[0])
            entry[f'delta_{k}_ci'] = interval([d[i] / d[0] for d in draws if d[0] != 0])
            entry[f'share_{k}'] = float((s.F[k] > 0).mean())
            entry[f'mean_{k}'] = float(s.F[k].mean())
        out['+'.join(feats)] = entry
    return out


def calibrate(s: Sample, w):
    ym, xm = demean(s.month, w, s.y, s.x)
    b = float((w * xm) @ ym / ((w * xm) @ xm))
    total = np.bincount(s.month, weights=w, minlength=s.month.max() + 1)
    safe = np.where(total > 0, total, 1.0)
    a = (np.bincount(s.month, weights=w * s.y, minlength=len(total)) - b * np.bincount(s.month, weights=w * s.x, minlength=len(total))) / safe
    return b, a


def readout_buckets(s: Sample, rng):
    one = np.ones(len(s.y))
    b, a = calibrate(s, one)
    resid = s.y - (a[s.month] + b * s.x)
    draws = []
    for _ in range(BOOT):
        w = boot_weights(s, rng)
        bb, aa = calibrate(s, w)
        draws.append((w, s.y - (aa[s.month] + bb * s.x)))
    out = dict(b=b)
    for k in FEATURES:
        cells = []
        for (lo, hi), label in zip(BUCKETS[k], BUCKET_LABELS[k]):
            m = (s.F[k] >= lo) & (s.F[k] < hi)
            n = int(m.sum())
            if not n:
                cells.append(dict(bucket=label, n=0))
                continue
            vals = [float((w * m * r).sum() / (w * m).sum()) for w, r in draws if (w * m).sum() > 0]
            cells.append(dict(bucket=label, n=n, stocks=int(len(set(s.stock[m]))), mean_resid=float(resid[m].mean()),
                              ci=interval(vals), median_pv=float(np.exp(np.median(s.x[m]))),
                              median_fwd=float(np.expm1(np.median(s.y[m])))))
        out[k] = cells
    return out


def cases(rows, horizon=3):
    s = Sample(rows, horizon)
    b, a = calibrate(s, np.ones(len(s.y)))
    months = {m: i for i, m in enumerate(sorted({r['month'] for r in s.rows}))}
    table, summary = [], {}
    for code in NAMED:
        mine = [r for r in rows if r['code'] == code]
        if not mine:
            continue
        last = max(r['month'] for r in mine)
        resid = []
        for r in mine:
            t = months.get(r['month'])
            pred = math.expm1(a[t] + b * math.log(r['pv'])) if t is not None and PV_RANGE[0] <= r['pv'] <= PV_RANGE[1] else None
            if pred is not None and r['f3'] is not None:
                resid.append(math.log1p(r['f3']) - math.log1p(pred))
            if r['month'][5:] == '12' or r['month'] == last:
                table.append(dict(code=code, name=r['name'], month=r['month'], pv=round(r['pv'], 4), S=round(r['S'], 3),
                                  ttm=r['ttm'], D=r['D'], roic0=r['roic0'], f1=r['f1'], f3=r['f3'],
                                  pred3=None if pred is None else round(pred, 4)))
        summary[code] = dict(name=mine[0]['name'], months=len(mine), months_with_f3=len(resid),
                             mean_resid3=float(np.mean(resid)) if resid else None,
                             share_negative=float(np.mean([x < 0 for x in resid])) if resid else None)
    return table, summary


def pool_exposure():
    names = load_names()
    pv = {}
    with SCAN.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            pv[r['security_code'].zfill(6)] = (num(r.get('model_pv')), r.get('trade_date'))
    out = []
    with POOL.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            code = r['security_code'].zfill(6)
            if r['status'] != 'ok' or r['roic_path'] not in ROIC_PATHS or is_divspread_financial(code, names.get(code, r['security_name'])):
                continue
            feat = features(r)
            if feat is None:
                continue
            p, day = pv.get(code, (None, None))
            out.append(dict(code=code, name=r['security_name'], pv=p, scan_date=day, S=round(feat['S'], 3), ttm=feat['ttm'],
                            T=round(feat['T'], 3), trust=feat['trust'], D=feat['D'], g0=feat['g0'], g_trailing=feat['g_trailing'],
                            roic0=feat['roic0'], nopat_mode=r.get('roic_nopat_mode'), peak_weight=num(r.get('peak_weight'))))
    return out


def main():
    rows = collect()
    cache = EXP / 'cache'
    cache.mkdir(exist_ok=True)
    with (cache / ('test_observations.csv' if TEST else 'observations.csv')).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    rng = np.random.default_rng(20261005)
    results = dict(test=TEST, boot=BOOT, observations=len(rows), stocks=len({r['code'] for r in rows}))
    for universe, sel in (('面板', [r for r in rows if r['panel']]), ('全部ROIC', rows)):
        for h in HORIZONS:
            s = Sample(sel, h)
            key = f'{universe}_{h}y'
            results[key] = dict(n=len(s.y), stocks=s.n_stocks, months=int(s.month.max() + 1),
                                regressions=readout_regressions(s, rng), buckets=readout_buckets(s, rng))
            joint = results[key]['regressions']['+'.join(FEATURES)]
            print(key, 'n', len(s.y), 'stocks', s.n_stocks, 'b %.3f' % joint['b'],
                  ' '.join(f"δ{k} {joint[f'delta_{k}']:.2f} {[round(x, 2) for x in joint[f'delta_{k}_ci']]}" for k in FEATURES), flush=True)
    table, summary = cases(rows)
    results['cases'] = summary
    exposure = pool_exposure()
    results['pool'] = dict(n=len(exposure), S_ge_03=sum(x['S'] >= 0.3 for x in exposure), S_ge_05=sum(x['S'] >= 0.5 for x in exposure),
                           ttm_lt_09=sum((x['ttm'] or 1) < 0.9 for x in exposure), D=sum(x['D'] for x in exposure))
    (OUT / ('test_results.json' if TEST else 'results.json')).write_text(json.dumps(results, ensure_ascii=False, indent=1) + '\n')
    for name, data in ((('test_cases.csv' if TEST else 'cases.csv'), table), (('test_pool_exposure.csv' if TEST else 'pool_exposure.csv'), exposure)):
        with (OUT / name).open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader(); w.writerows(data)


if __name__ == '__main__':
    main()
