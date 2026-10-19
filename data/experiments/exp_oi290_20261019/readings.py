"""OI-290 读数 1～5 与 7（preregister.md）：输入预测力、受影响月份校准、包含检验、分时期、截面排序、当前池。

    python3 readings.py      # 读 collect.py 的 observations.csv 与四臂 roic_bands.csv → readings.json、readings.md
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
ARMS = ('C', 'F3', 'F5', 'FR')
SCRATCH = ROOT / 'data/scratch/experiments/exp_oi290_20261019'
PV_RANGE, BOOT, SEED = (0.2, 5.0), 1000, 20261019
PERIODS = (('2010-01', '2014-12'), ('2015-01', '2018-12'), ('2019-01', '2023-12'))
HORIZONS = ('f3', 'f5')
G_T, FADE_N = 0.03, 10
BUY_LINE = 1.0034
SCAN_DATE = '2026-10-16'


# ---------- 读数 1：输入预测力 ----------

def annual_bands(arm: str) -> pd.DataFrame:
    rows = []
    with (SCRATCH / 'states' / arm / 'roic_bands.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['report_date'].endswith('-12-31') and r['status'] == 'ok' and r['roic_path'] == 'growth':
                rows.append((r['security_code'], int(r['report_date'][:4]), r['roic_g_source'], float(r['g0'])))
    return pd.DataFrame(rows, columns=['code', 'year', f'src_{arm}', f'g0_{arm}']).drop_duplicates(['code', 'year'])


def panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    parts = []
    for y in range(1998, 2026):
        fn = ROOT / 'data/raw/financials' / f'{y}-12-31.csv'
        if fn.exists():
            d = pd.read_csv(fn, dtype={'security_code': str}, usecols=['security_code', 'parent_netprofit', 'total_operate_income'])
            d['year'] = y
            parts.append(d)
    p = pd.concat(parts).drop_duplicates(['security_code', 'year'], keep='last')
    return (p.pivot(index='security_code', columns='year', values='parent_netprofit'),
            p.pivot(index='security_code', columns='year', values='total_operate_income'))


def cagr(a, b, h):
    if a is None or b is None or not (a > 0) or not np.isfinite(b):
        return np.nan
    return (b / a) ** (1 / h) - 1 if b > 0 else -1.0


def reading_predictability() -> dict:
    df = annual_bands('C')
    for arm in ARMS[1:]:
        df = df.merge(annual_bands(arm), on=['code', 'year'], how='inner')
    npv, rev = panel()

    def get(tbl, c, y):
        try:
            v = tbl.at[c, y]
            return float(v) if pd.notna(v) else None
        except KeyError:
            return None
    real_np, real_rev = [], []
    for c, y in zip(df['code'], df['year']):
        s = [get(npv, c, y - 1), get(npv, c, y)]
        e = [get(npv, c, y + 4), get(npv, c, y + 5)]
        real_np.append(cagr(sum(s) / 2 if None not in s else None, sum(e) / 2 if None not in e else np.nan, 5))
        real_rev.append(cagr(get(rev, c, y), get(rev, c, y + 5) if get(rev, c, y + 5) is not None else np.nan, 5))
    df['real_np'], df['real_rev'] = real_np, real_rev
    df = df[(df['year'] >= 2008) & (df['year'] <= 2020)]
    out = {'rows': int(len(df)), 'affected_rows': int((df['src_C'] == 'none').sum())}
    aff = df[df['src_C'] == 'none']
    for target in ('real_np', 'real_rev'):
        res = {}
        sub = aff[aff[target].notna() & (aff[target] > -1)]
        yv = sub[target].clip(-0.5, 0.6)
        for arm in ARMS:
            g = sub[f'g0_{arm}']
            impl = g + (G_T - g) * 6 / (2 * FADE_N)
            res[arm] = dict(n=int(len(sub)), median_bias=float(np.median(impl - yv)), mae=float(np.median(np.abs(impl - yv))),
                            implied_median=float(np.median(impl)), realized_median=float(np.median(yv)))
        out[f'affected_{target}'] = res
        rho = {}
        for arm in ARMS:
            vals = []
            for _, gg in df[df[target].notna()].groupby('year'):
                if len(gg) >= 30:
                    vals.append(gg[f'g0_{arm}'].rank().corr(gg[target].rank()))
            rho[arm] = dict(median=float(np.median(vals)), years=len(vals), positive=int(sum(v > 0 for v in vals)))
        out[f'rank_corr_{target}'] = rho
    return out


# ---------- 读数 2～5：校准、包含检验、分时期、截面排序 ----------

def load_obs() -> pd.DataFrame:
    d = pd.read_csv(SCRATCH / 'observations.csv', dtype={'code': str})
    d['affected'] = d['affected'].astype(str) == 'True'
    return d


def fixed_effect_fit(t, x, y, n_months):
    cnt = np.bincount(t, minlength=n_months).astype(float)
    safe = np.where(cnt > 0, cnt, 1.0)
    dm = lambda v: v - (np.bincount(t, weights=v, minlength=n_months) / safe)[t]
    b = float(dm(x) @ dm(y) / (dm(x) @ dm(x)))
    a = (np.bincount(t, weights=y, minlength=n_months) - b * np.bincount(t, weights=x, minlength=n_months)) / safe
    return a, b, cnt > 0


def reading_calibration(obs: pd.DataFrame, horizon: str, rng) -> dict:
    valid = obs[obs[horizon].notna() & (obs[horizon] > -1)]
    in_range = np.ones(len(valid), dtype=bool)
    for arm in ARMS:
        in_range &= valid[f'pv_{arm}'].between(*PV_RANGE).to_numpy()
    valid = valid[in_range]
    calib = valid[~valid['affected']]
    sample = valid[valid['affected']]
    months = sorted(set(valid['month']))
    mi = {m: i for i, m in enumerate(months)}
    t = calib['month'].map(mi).to_numpy()
    a, b, has = fixed_effect_fit(t, np.log(calib['pv_C'].to_numpy()), np.log1p(calib[horizon].to_numpy()), len(months))
    sample = sample[has[sample['month'].map(mi).to_numpy()]]
    ts = sample['month'].map(mi).to_numpy()
    ys = np.log1p(sample[horizon].to_numpy())
    codes = sorted(set(sample['code']))
    cidx = sample['code'].map({c: i for i, c in enumerate(codes)}).to_numpy()
    resid = {arm: ys - (a[ts] + b * np.log(sample[f'pv_{arm}'].to_numpy())) for arm in ARMS}

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
    res = dict(calibration_b=b, calibration_n=int(len(calib)), sample=int(len(sample)), stocks=len(codes), main=summary(one))
    res['periods'] = {f'{lo}～{hi}': summary(np.array([1.0 if lo <= m <= hi else 0.0 for m in sample['month']]))
                      for lo, hi in PERIODS}
    # 包含检验：全样本 y = a_t + b ln PV_C + g d，d 只在受影响月份非 0
    Y = np.log1p(valid[horizon].to_numpy())
    X = np.log(valid['pv_C'].to_numpy())
    T = valid['month'].map(mi).to_numpy()
    G = valid['code'].map({c: i for i, c in enumerate(sorted(set(valid['code'])))}).to_numpy()
    n_groups = int(G.max()) + 1
    lam = {}
    for arm in ARMS[1:]:
        D = np.log(valid[f'pv_{arm}'].to_numpy() / valid['pv_C'].to_numpy())

        def fit(w):
            tot = np.bincount(T, weights=w, minlength=len(months)); sf = np.where(tot > 0, tot, 1.0)
            dd = lambda v: v - (np.bincount(T, weights=w * v, minlength=len(months)) / sf)[T]
            M = np.column_stack([dd(X), dd(D)]); Mw = M * w[:, None]
            return np.linalg.solve(M.T @ Mw, Mw.T @ dd(Y))
        beta = fit(np.ones(len(Y)))
        draws = []
        for _ in range(BOOT):
            w = np.bincount(rng.integers(0, n_groups, n_groups), minlength=n_groups).astype(float)[G]
            if (w * (D != 0)).sum() == 0:
                continue
            try:
                bb = fit(w)
            except np.linalg.LinAlgError:
                continue
            draws.append(bb[1] / bb[0])
        lam[arm] = dict(b=float(beta[0]), g=float(beta[1]), lam=float(beta[1] / beta[0]),
                        ci=[float(np.percentile(draws, 5)), float(np.percentile(draws, 95))], draws=len(draws),
                        mean_d=float(D[D != 0].mean()) if (D != 0).any() else 0.0, nonzero=int((D != 0).sum()))
    res['encompass'] = lam
    # 截面排序：每月 corr(−ln P/V, 回报) 的臂间配对差
    rank = {}
    for arm in ARMS[1:]:
        diffs = []
        for _, g in valid.groupby('month'):
            if len(g) < 30:
                continue
            fr = g[horizon].rank()
            rc = (-np.log(g['pv_C'])).rank().corr(fr)
            ra = (-np.log(g[f'pv_{arm}'])).rank().corr(fr)
            diffs.append(ra - rc)
        rank[arm] = dict(months=len(diffs), median_diff=float(np.median(diffs)), positive_share=float(np.mean(np.array(diffs) > 0)))
    res['ranking'] = rank
    return res


def verdict(cal: dict) -> dict:
    """预登记判定：读数 2 残差、读数 3 λ、读数 4 时期（读数 1 另核）。"""
    out = {}
    c = cal['main']['C']
    for arm in ARMS[1:]:
        m = cal['main'][arm]
        r2 = abs(m['mean']) < abs(c['mean']) and m['ci'][0] <= 0 <= m['ci'][1] and not (c['ci'][0] <= 0 <= c['ci'][1])
        lam = cal['encompass'][arm]['ci']
        r3 = not (lam[0] <= 0 <= lam[1])
        same = sum(1 for p in cal['periods'].values()
                   if p[arm]['mean'] is not None and p['C']['mean'] is not None and abs(p[arm]['mean']) < abs(p['C']['mean']))
        r4 = same >= 2
        out[arm] = dict(residual=r2, encompass=r3, periods=r4, periods_better=same)
    return out


# ---------- 读数 7：当前池 ----------

def reading_current() -> dict:
    latest = {}
    for arm in ARMS:
        best = {}
        with (SCRATCH / 'states' / arm / 'roic_bands.csv').open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['status'] != 'ok' or r['available_at'] > SCAN_DATE:
                    continue
                k = r['security_code']
                if k not in best or r['available_at'] >= best[k][0]:
                    best[k] = (r['available_at'], float(r['intrinsic_value']), r['roic_g_source'], float(r['g0']))
        latest[arm] = best
    cand = pd.read_csv(ROOT / 'data/processed/daily_buy_candidates.csv', dtype={'security_code': str})
    out = {}
    for arm in ARMS[1:]:
        rows = []
        for code, name, pv in zip(cand['security_code'], cand['security_name'], cand['model_pv']):
            c, a = latest['C'].get(code), latest[arm].get(code)
            if not (c and a and np.isfinite(pv)) or c[2] != 'none':
                continue
            ratio = a[1] / c[1] if c[1] > 0 else None
            if not ratio:
                continue
            rows.append(dict(code=code, name=name, pv_C=float(pv), pv_arm=float(pv / ratio), v_ratio=float(ratio), g0_arm=a[3]))
        ent = [r for r in rows if r['pv_C'] > BUY_LINE >= r['pv_arm']]
        out[arm] = dict(affected=len(rows), v_ratio_median=float(np.median([r['v_ratio'] for r in rows])) if rows else None,
                        enter=[f"{r['name']}（{r['pv_C']:.3f}→{r['pv_arm']:.3f}）" for r in ent], rows=rows)
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    readings = dict(predictability=reading_predictability())
    obs = load_obs()
    readings['observations'] = int(len(obs))
    readings['affected_months'] = int(obs['affected'].sum())
    unaffected = obs[~obs['affected']]
    readings['unaffected_identical'] = {arm: float((unaffected[f'pv_{arm}'] / unaffected['pv_C'] - 1).abs().max())
                                        for arm in ARMS[1:]}
    for h in HORIZONS:
        cal = reading_calibration(obs, h, rng)
        cal['verdict'] = verdict(cal)
        readings[h] = cal
    readings['current'] = reading_current()
    (EXP / 'readings.json').write_text(json.dumps(readings, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in readings.items() if k != 'current'}, ensure_ascii=False, indent=1)[:6000])
    for arm, cur in readings['current'].items():
        print(arm, '受影响', cur['affected'], 'V 比中位', cur['v_ratio_median'], '新进买入区', '、'.join(cur['enter']) or '无')


if __name__ == '__main__':
    main()
