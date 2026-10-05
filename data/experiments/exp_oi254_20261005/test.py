"""OI-254 读数（preregister.md 读数 1～5）：11 只需求周期型资本品在 C／A1／A2 三臂下的 `P/V` 对其后回报。

校准样本 = 生产候选侧月末观测（`../exp_external_audit_20261005/cache/observations.csv`）中其余 ROIC 路径非金融公司。

    python3 test.py      # → readings.json、cases.csv
"""
import bisect
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
AUDIT = ROOT / 'data/experiments/exp_external_audit_20261005'
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import build_historical_valuation_bands as bhv  # noqa: E402
from moat_param_lab import forward_annualized, total_return_index  # noqa: E402

ARMS = ('C', 'A1', 'A2')
CODES = [c.strip() for c in (EXP / 'demand_cycle_codes.txt').read_text(encoding='utf-8').splitlines() if c.strip()]
POOL = ('600031', '600066', '601717', '603508', '688516', '920599', '300316')
START, PV_RANGE, BOOT, SEED = '2010-01-01', (0.2, 5.0), 1000, 20261005
PERIODS = (('2010-01', '2014-12'), ('2015-01', '2018-12'), ('2019-01', '2023-12'))


def num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def arm_month_ends(arm):
    folder = EXP / 'states' / arm
    info, rejected = {}, defaultdict(list)
    with (folder / 'roic_bands.csv').open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ok = r['status'] == 'ok'
            info[(r['security_code'], r['report_date'], r['available_at'])] = (ok, r['roic_path'], num(r['intrinsic_value']))
            if not ok:
                rejected[r['security_code']].append((r['available_at'], r['report_date']))
    steps = {}
    for code, rows in rejected.items():
        rows.sort()
        keys, best, cur = [], [], ''
        for av, rep in rows:
            cur = max(cur, rep); keys.append(av); best.append(cur)
        steps[code] = (keys, best)
    out = {}
    with (folder / 'roic_daily_raw.csv').open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['date'] < START:
                continue
            key = (r['security_code'], r['date'][:7])
            if key not in out or r['date'] > out[key]['date']:
                out[key] = r
    res = {}
    for key, r in out.items():
        code = key[0]
        band = info.get((code, r['band_report_date'], r['band_available_at']))
        if band is None or not band[0] or band[1] not in ('growth', 'zero_growth'):
            continue
        step = steps.get(code)
        if step:
            i = bisect.bisect_right(step[0], r['date'])
            if i and step[1][i - 1] > r['band_report_date']:
                continue
        pv = num(r['valuation_ratio'])
        if pv and pv > 0:
            res[key] = (r['date'], pv)
    return res


def main():
    base = [r for r in csv.DictReader((AUDIT / 'cache/observations.csv').open(encoding='utf-8'))]
    calib = [r for r in base if r['code'] not in CODES and num(r['f3']) is not None and num(r['f3']) > -1
             and PV_RANGE[0] <= float(r['pv']) <= PV_RANGE[1]]
    prod = {(r['code'], r['month']): r for r in base if r['code'] in CODES}
    arms = {a: arm_month_ends(a) for a in ARMS}
    # C 复现生产月末 P/V
    mism, both = 0, 0
    for key, (day, pv) in arms['C'].items():
        p = prod.get(key)
        if p:
            both += 1
            if abs(pv / float(p['pv']) - 1) > 1e-3:
                mism += 1
    # 11 只的观测：三臂都可估的月份
    actions = bhv.load_actions()
    obs = []
    for code in CODES:
        prices = bhv.load_ohlcv(code)
        if not prices:
            continue
        days = [d for d, _ in prices]
        tr = total_return_index(prices, actions.get(code, []))
        months = sorted({k[1] for k in arms['C'] if k[0] == code})
        for m in months:
            key = (code, m)
            if not all(key in arms[a] for a in ARMS):
                continue
            day = arms['C'][key][0]
            f3 = forward_annualized(tr, days, day, 3) if day in tr else None
            f1 = forward_annualized(tr, days, day, 1) if day in tr else None
            obs.append(dict(code=code, month=m, date=day, f1=f1, f3=f3, **{f'pv_{a}': arms[a][key][1] for a in ARMS}))
    # 校准：月固定效应 + 共同斜率（其余公司）
    months = sorted({r['month'] for r in calib} | {r['month'] for r in obs})
    mi = {m: i for i, m in enumerate(months)}
    y = np.log1p(np.array([float(r['f3']) for r in calib]))
    x = np.log(np.array([float(r['pv']) for r in calib]))
    t = np.array([mi[r['month']] for r in calib])
    cnt = np.bincount(t, minlength=len(months)).astype(float)
    safe = np.where(cnt > 0, cnt, 1.0)
    dm = lambda v: v - (np.bincount(t, weights=v, minlength=len(months)) / safe)[t]
    b = float(dm(x) @ dm(y) / (dm(x) @ dm(x)))
    a = (np.bincount(t, weights=y, minlength=len(months)) - b * np.bincount(t, weights=x, minlength=len(months))) / safe
    has = cnt > 0
    sample = [r for r in obs if r['f3'] is not None and r['f3'] > -1 and has[mi[r['month']]]
              and all(PV_RANGE[0] <= r[f'pv_{a2}'] <= PV_RANGE[1] for a2 in ARMS)]
    rng = np.random.default_rng(SEED)
    codes = sorted({r['code'] for r in sample})
    cidx = np.array([codes.index(r['code']) for r in sample])
    ys = np.log1p(np.array([r['f3'] for r in sample]))
    ts = np.array([mi[r['month']] for r in sample])
    resid = {arm: ys - (a[ts] + b * np.log(np.array([r[f'pv_{arm}'] for r in sample]))) for arm in ARMS}

    def summary(mask):
        out = {}
        for arm in ARMS:
            vals = []
            for _ in range(BOOT):
                w = np.bincount(rng.integers(0, len(codes), len(codes)), minlength=len(codes)).astype(float)[cidx] * mask
                if w.sum() > 0:
                    vals.append(float((w * resid[arm]).sum() / w.sum()))
            out[arm] = dict(mean=float(resid[arm][mask > 0].mean()) if mask.sum() else None,
                            ci=[float(np.percentile(vals, 5)), float(np.percentile(vals, 95))] if vals else None)
        out['n'], out['stocks'] = int(mask.sum()), int(len(set(cidx[mask > 0])))
        return out
    one = np.ones(len(sample))
    readings = dict(control_reproduction=dict(months=both, mismatch=mism), calibration_b=b, calibration_n=len(calib),
                    sample=len(sample), stocks=len(codes), main=summary(one))
    readings['periods'] = {f'{lo}～{hi}': summary(np.array([1.0 if lo <= r['month'] <= hi else 0.0 for r in sample]))
                           for lo, hi in PERIODS}
    # 包含检验：合并样本 y = a_t + b ln PV_C + g d
    lam = {}
    for arm in ('A1', 'A2'):
        Y = np.concatenate([y, ys]); X = np.concatenate([x, np.log([r['pv_C'] for r in sample])])
        D = np.concatenate([np.zeros(len(y)), np.log([r[f'pv_{arm}'] / r['pv_C'] for r in sample])])
        T = np.concatenate([t, ts])
        groups = np.concatenate([np.array([r['code'] for r in calib]), np.array([r['code'] for r in sample])])
        ucode = {c: i for i, c in enumerate(sorted(set(groups)))}
        G = np.array([ucode[c] for c in groups])
        cntT = np.bincount(T, minlength=len(months)).astype(float)

        def fit(w):
            tot = np.bincount(T, weights=w, minlength=len(months)); sf = np.where(tot > 0, tot, 1.0)
            dd = lambda v: v - (np.bincount(T, weights=w * v, minlength=len(months)) / sf)[T]
            M = np.column_stack([dd(X), dd(D)]); Mw = M * w[:, None]
            beta = np.linalg.solve(M.T @ Mw, Mw.T @ dd(Y))
            return beta
        beta = fit(np.ones(len(Y)))
        draws = []
        for _ in range(BOOT):
            w = np.bincount(rng.integers(0, len(ucode), len(ucode)), minlength=len(ucode)).astype(float)[G]
            if (w * (D != 0)).sum() == 0:
                continue
            try:
                bb = fit(w)
            except np.linalg.LinAlgError:
                continue
            draws.append(bb[1] / bb[0])
        lam[arm] = dict(b=float(beta[0]), g=float(beta[1]), lam=float(beta[1] / beta[0]),
                        ci=[float(np.percentile(draws, 5)), float(np.percentile(draws, 95))], draws=len(draws),
                        mean_d=float(np.mean([math.log(r[f'pv_{arm}'] / r['pv_C']) for r in sample])))
    readings['encompass'] = lam
    by = defaultdict(list)
    for r, i in zip(sample, range(len(sample))):
        by[r['code']].append(i)
    readings['by_stock'] = {c: dict(months=len(ix), **{arm: float(resid[arm][ix].mean()) for arm in ARMS}) for c, ix in by.items()}
    # 现值：池内 7 只三臂最新月末 V 与 P/V
    latest = {}
    for arm in ARMS:
        with (EXP / 'states' / arm / 'roic_daily_raw.csv').open(encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['security_code'] in POOL:
                    k = (arm, r['security_code'])
                    if k not in latest or r['date'] > latest[k]['date']:
                        latest[k] = r
    readings['current'] = {c: {arm: dict(date=latest[(arm, c)]['date'], v=num(latest[(arm, c)]['intrinsic_value']),
                                         pv=num(latest[(arm, c)]['valuation_ratio'])) for arm in ARMS if (arm, c) in latest}
                           for c in POOL}
    (EXP / 'readings.json').write_text(json.dumps(readings, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    with (EXP / 'cases.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(obs[0])); w.writeheader(); w.writerows(obs)
    print(json.dumps({k: v for k, v in readings.items() if k != 'by_stock'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
