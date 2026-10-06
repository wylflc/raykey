"""估值口径候选的公允性检验（§12.1「估值准确性」；读数口径同 `data/experiments/exp_oi217f_20260925/preregister.md`）。

对照臂 C 与若干候选臂的候选侧带与逐日状态（各臂目录含 `roic_bands.csv`、`roic_daily_raw.csv`），取 ROIC 路径月末 `valuation_ratio`
对其后 3／5 年含分红年化回报：
1. 分歧分布：`d = ln(PV_臂 / PV_C)` 分位数、`|d| ≥ 0.10` 占比、平均分歧最大的股票；
2. 排序力：每月截面 Spearman，各臂与对 C 配对差的月均值、Newey-West t；
3. 包含检验（主读数）：`y = a_t + b·ln PV_C + g·d`，每个候选单独一式，`λ = g / b`，按股票整体重抽取 90% 区间；稳健性为行业 × 月效应；
4. 分歧样本校准：一致组 `|d| < 0.02` 拟合 `y = a_t + b·ln PV`，分歧组 `|d| ≥ 0.15` 按 `d` 正负分开报 C 与候选的平均残差；
5. 分组：调用方给出逐观测的分组标签（取自 C 带），各组重复 3、4；
6. 个股：逐年 12 月末各臂 `P/V`、其后实际年化与一致组校准的预测、预测平均绝对误差。

    from caliber_fairness import run
    run(exp_dir, arms={'C': path, 'G1': path, ...}, groups=func, cases=[...], start='2010-01-01')
"""
from __future__ import annotations

import bisect
import csv
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import build_historical_valuation_bands as bhv  # noqa: E402
from divspread_names import is_divspread_financial  # noqa: E402
from moat_param_lab import forward_annualized, total_return_index  # noqa: E402

PANEL = ROOT / 'data/processed/pit_attention/panel_moat_bank_v6b.csv'
ROIC_PATHS = {'growth', 'zero_growth'}
PV_RANGE = (0.2, 5.0)
NEUTRAL, DISPUTED = 0.02, 0.15
HORIZONS = (3, 5)


def load_bands(folder: Path):
    """行键 → (ok, ROIC 路径, 原行)；逐票拒绝带的「可得日 → 已拒最新报告期」阶梯，用于判沿用旧带。"""
    info, rejected = {}, defaultdict(list)
    with (folder / 'roic_bands.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ok = r['status'] == 'ok'
            info[(r['security_code'], r['report_date'], r['available_at'])] = (ok, r['roic_path'] in ROIC_PATHS, r)
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


def month_ends(path: Path, codes: set, start: str) -> dict:
    out = {}
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        h = next(reader)
        ic, idt, irp, iav, ipv = (h.index(k) for k in ('security_code', 'date', 'band_report_date', 'band_available_at', 'valuation_ratio'))
        for row in reader:
            code = row[ic]
            if code not in codes or row[idt] < start:
                continue
            key = (code, row[idt][:7])
            if key not in out or row[idt] > out[key][0]:
                out[key] = (row[idt], row[ipv], row[irp], row[iav])
    return out


def judge(rec, code, info, steps):
    if rec is None or not rec[1]:
        return None, None
    day, pv, report, avail = rec
    band = info.get((code, report, avail))
    if band is None or not band[0] or not band[1]:
        return None, None
    step = steps.get(code)
    if step:
        i = bisect.bisect_right(step[0], day)
        if i and step[1][i - 1] > report:
            return None, None
    value = float(pv)
    return (value, band[2]) if value > 0 else (None, None)


def collect(arms: dict, start: str, groups=None) -> list[dict]:
    bands = {a: load_bands(p) for a, p in arms.items()}
    names = {}
    with (ROOT / 'data/raw/a_share_securities.csv').open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            names[r['security_code'].zfill(6)] = (r['security_name'], r.get('industry') or '')
    with PANEL.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            names.setdefault(r['security_code'].zfill(6), (r['security_name'], ''))
    codes = {k[0] for k, (ok, roic, _r) in bands['C'][0].items() if ok and roic}
    codes = {c for c in codes if not is_divspread_financial(c, names.get(c, ('', ''))[0])}
    states = {a: month_ends(p / 'roic_daily_raw.csv', codes, start) for a, p in arms.items()}
    spans = defaultdict(list)
    with PANEL.open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            spans[r['security_code'].zfill(6)].append((r['effective_from'], r.get('effective_to') or '9999-12-31'))
    actions = bhv.load_actions()
    by_code = defaultdict(list)
    for key in states['C']:
        by_code[key[0]].append(key)
    rows = []
    for code in sorted(codes):
        prices = bhv.load_ohlcv(code)
        if not prices:
            continue
        days = [d for d, _ in prices]
        tr = total_return_index(prices, actions.get(code, []))
        for key in sorted(by_code.get(code, ())):
            pvs, band_c = {}, None
            for arm in arms:
                pv, band = judge(states[arm].get(key), code, *bands[arm])
                pvs[arm] = pv
                if arm == 'C':
                    band_c = band
            if pvs['C'] is None:
                continue
            day = states['C'][key][0]
            fwd = {h: (forward_annualized(tr, days, day, h) if day in tr else None) for h in HORIZONS}
            rec = dict(code=code, name=names.get(code, ('', ''))[0], industry=(names.get(code, ('', ''))[1] or 'NA')[:2], month=key[1],
                       date=day, panel=any(a <= day <= b for a, b in spans.get(code, ())), f3=fwd[3], f5=fwd[5],
                       **{f'pv_{a}': v for a, v in pvs.items()})
            rec['groups'] = groups(band_c, rec) if groups else {}
            rows.append(rec)
    return rows


# ---------- 统计工具（同 exp_oi217f 的 fairness.py） ----------

def demean(groups, w, *cols):
    total = np.bincount(groups, weights=w)
    safe = np.where(total > 0, total, 1.0)
    return [c - (np.bincount(groups, weights=w * c) / safe)[groups] for c in cols]


def wls(y, X, w):
    Xw = X * w[:, None]
    return np.linalg.solve(X.T @ Xw, Xw.T @ y)


def boot_weights(stock_idx, n_stocks, rng):
    counts = np.bincount(rng.integers(0, n_stocks, n_stocks), minlength=n_stocks).astype(float)
    return counts[stock_idx]


def interval(values):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)])
    return [float(np.percentile(v, 5)), float(np.percentile(v, 95))] if len(v) else [None, None]


def newey_west_t(series, lag):
    x = np.asarray(series, float)
    n = len(x)
    if n < 3:
        return None
    e = x - x.mean()
    var = e @ e / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(x.mean() / math.sqrt(var / n)) if var > 0 else None


class Sample:
    def __init__(self, rows, arm, horizon, clip=True, winsor=False, group=None):
        rows = [r for r in rows if r.get(f'pv_{arm}') is not None and r[f'f{horizon}'] is not None
                and (group is None or r['groups'].get(group))]
        if clip:
            rows = [r for r in rows if PV_RANGE[0] <= r['pv_C'] <= PV_RANGE[1]]
        self.rows = rows
        self.n = len(rows)
        if not rows:
            return
        self.y = np.log1p(np.array([r[f'f{horizon}'] for r in rows]))
        self.x = np.log(np.array([r['pv_C'] for r in rows]))
        self.xa = np.log(np.array([r[f'pv_{arm}'] for r in rows]))
        self.d = self.xa - self.x
        if winsor:
            for name in ('x', 'd'):
                v = getattr(self, name)
                lo, hi = np.percentile(v, [1, 99])
                setattr(self, name, np.clip(v, lo, hi))
        codes = {c: i for i, c in enumerate(sorted({r['code'] for r in rows}))}
        self.stock = np.array([codes[r['code']] for r in rows], int)
        self.n_stocks = len(codes)
        months = {m: i for i, m in enumerate(sorted({r['month'] for r in rows}))}
        self.month = np.array([months[r['month']] for r in rows], int)
        cells = {c: i for i, c in enumerate(sorted({(r['month'], r['industry']) for r in rows}))}
        self.cell = np.array([cells[(r['month'], r['industry'])] for r in rows], int)


def encompass(s: Sample, w, groups):
    ym, xm, dm = demean(groups, w, s.y, s.x, s.d)
    return wls(ym, np.column_stack([xm, dm]), w)


def readout_encompass(s: Sample, rng, boot, fe='month'):
    if s.n < 50 or s.n_stocks < 10 or not np.any(np.abs(s.d) > 1e-9):
        return dict(n=s.n, stocks=getattr(s, 'n_stocks', 0), note='样本或分歧不足')
    groups = s.month if fe == 'month' else s.cell
    beta = encompass(s, np.ones(s.n), groups)
    draws = [encompass(s, boot_weights(s.stock, s.n_stocks, rng), groups) for _ in range(boot)]
    return dict(n=s.n, stocks=s.n_stocks, b=float(beta[0]), b_ci=interval([d[0] for d in draws]), g=float(beta[1]),
                lam=float(beta[1] / beta[0]), lam_ci=interval([d[1] / d[0] for d in draws if d[0] != 0]))


def calibrate(s: Sample, w):
    neutral = np.abs(s.d) < NEUTRAL
    wn = w * neutral
    ym, xm = demean(s.month, wn, s.y, s.x)
    b = float((wn * xm) @ ym / ((wn * xm) @ xm))
    total = np.bincount(s.month, weights=wn, minlength=s.month.max() + 1)
    safe = np.where(total > 0, total, 1.0)
    a = (np.bincount(s.month, weights=wn * s.y, minlength=len(total)) - b * np.bincount(s.month, weights=wn * s.x, minlength=len(total))) / safe
    return b, a, total > 0


def residual(s, w, b, a, has, mask, xs):
    m = mask & has[s.month]
    weight = w * m
    return float((weight * (s.y - (a[s.month] + b * xs))).sum() / weight.sum()) if weight.sum() > 0 else None


def readout_calibration(s: Sample, rng, boot):
    if s.n < 50 or not np.any(np.abs(s.d) < NEUTRAL):
        return dict(note='样本不足')
    masks = {'调低V(d>0)': s.d >= DISPUTED, '调高V(d<0)': s.d <= -DISPUTED}
    one = np.ones(s.n)
    b, a, has = calibrate(s, one)
    out = dict(b=b, n_neutral=int((np.abs(s.d) < NEUTRAL).sum()))
    draws = []
    for _ in range(boot):
        w = boot_weights(s.stock, s.n_stocks, rng)
        bb, aa, hh = calibrate(s, w)
        draws.append({g: (residual(s, w, bb, aa, hh, m, s.x), residual(s, w, bb, aa, hh, m, s.xa)) for g, m in masks.items()})
    for g, m in masks.items():
        n = int((m & has[s.month]).sum())
        out[g] = dict(n=n, stocks=int(len(set(s.stock[m & has[s.month]]))),
                      C=residual(s, one, b, a, has, m, s.x), arm=residual(s, one, b, a, has, m, s.xa),
                      C_ci=interval([d[g][0] for d in draws]), arm_ci=interval([d[g][1] for d in draws]))
    return out


def readout_rank(rows, arm, horizon):
    per, by_month = {'C': [], arm: []}, defaultdict(list)
    for r in rows:
        if r.get(f'pv_{arm}') is not None and r[f'f{horizon}'] is not None and PV_RANGE[0] <= r['pv_C'] <= PV_RANGE[1]:
            by_month[r['month']].append(r)
    diffs = []
    for m in sorted(by_month):
        rs = by_month[m]
        if len(rs) < 20:
            continue
        ry = rankdata([r[f'f{horizon}'] for r in rs])
        rc = float(np.corrcoef(rankdata([r['pv_C'] for r in rs]), ry)[0, 1])
        ra = float(np.corrcoef(rankdata([r[f'pv_{arm}'] for r in rs]), ry)[0, 1])
        per['C'].append(rc); per[arm].append(ra); diffs.append(ra - rc)
    lag = 12 * horizon
    return dict(months=len(diffs), C=float(np.mean(per['C'])) if diffs else None, arm=float(np.mean(per[arm])) if diffs else None,
                diff=float(np.mean(diffs)) if diffs else None, diff_t=newey_west_t(diffs, lag) if diffs else None)


def readout_disagreement(rows, arm):
    d = np.array([math.log(r[f'pv_{arm}'] / r['pv_C']) for r in rows if r.get(f'pv_{arm}') is not None])
    if not len(d):
        return dict(n=0)
    by = defaultdict(list)
    for r in rows:
        if r.get(f'pv_{arm}') is not None:
            by[(r['code'], r['name'])].append(math.log(r[f'pv_{arm}'] / r['pv_C']))
    top = sorted(((abs(np.mean(v)), k, float(np.mean(v)), len(v)) for k, v in by.items()), reverse=True)[:8]
    return dict(n=int(len(d)), q=[float(x) for x in np.percentile(d, [1, 5, 25, 50, 75, 95, 99])],
                share_abs_ge_010=float(np.mean(np.abs(d) >= 0.10)), unvaluable=sum(1 for r in rows if r.get(f'pv_{arm}') is None),
                top=[dict(code=k[0], name=k[1], mean_d=m, months=n) for _a, k, m, n in top])


def readout_cases(rows, arm, codes):
    out = []
    for code in codes:
        recs = [r for r in rows if r['code'] == code and r['month'].endswith('-12')]
        for r in recs:
            out.append(dict(code=code, name=r['name'], month=r['month'], pv_C=r['pv_C'], pv_arm=r.get(f'pv_{arm}'), f3=r['f3'], f5=r['f5']))
    return out


def run(exp: Path, arms: dict, groups=None, group_names=(), cases=(), start='2010-01-01', boot=1000, seed=20261006) -> dict:
    """读数 1～6，写 `exp/results.json` 与 `exp/cases.csv`；逐月观测缓存 `exp/cache/observations.json`。"""
    exp = Path(exp)
    (exp / 'cache').mkdir(exist_ok=True)
    cache = exp / 'cache/observations.json'
    if cache.exists() and os.environ.get('FAIRNESS_RECOLLECT') != '1':
        rows = json.loads(cache.read_text())
    else:
        rows = collect(arms, start, groups)
        cache.write_text(json.dumps(rows, ensure_ascii=False))
    rng = np.random.default_rng(seed)
    res = dict(start=start, arms=list(arms), observations=len(rows), readings={})
    for arm in [a for a in arms if a != 'C']:
        entry = dict(disagreement=readout_disagreement(rows, arm))
        for pop, subset in (('panel', [r for r in rows if r['panel']]), ('all', rows)):
            for h in HORIZONS:
                key = f'{pop}_{h}y'
                s = Sample(subset, arm, h)
                entry[key] = dict(rank=readout_rank(subset, arm, h), encompass=readout_encompass(s, rng, boot),
                                  encompass_industry=readout_encompass(s, rng, boot // 5, fe='cell'),
                                  winsor=readout_encompass(Sample(subset, arm, h, clip=False, winsor=True), rng, boot // 5),
                                  calibration=readout_calibration(s, rng, boot // 5))
                entry[key]['groups'] = {g: dict(encompass=readout_encompass(Sample(subset, arm, h, group=g), rng, boot // 5),
                                                calibration=readout_calibration(Sample(subset, arm, h, group=g), rng, boot // 10))
                                        for g in group_names}
        entry['cases'] = readout_cases(rows, arm, cases)
        res['readings'][arm] = entry
        print('done', arm, flush=True)
    (exp / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + '\n')
    with (exp / 'cases.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['arm', 'code', 'name', 'month', 'pv_C', 'pv_arm', 'f3', 'f5'])
        for arm, entry in res['readings'].items():
            for c in entry['cases']:
                w.writerow([arm, c['code'], c['name'], c['month'], c['pv_C'], c['pv_arm'], c['f3'], c['f5']])
    return res
