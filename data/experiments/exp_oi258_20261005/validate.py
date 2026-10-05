"""OI-258 保险 ROE 锚的历史验证（preregister.md 读数 1～5）：只换五家保险 V_DDM 的 roe0，bps、派息率与 Ḡ 同 OI-232 I1c。

    python3 validate.py      # → candidates.csv、readings.json、readings.md（insurer_history.csv 存在时加 C5）
"""
import bisect
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
OI232 = ROOT / 'data/experiments/exp_oi232_20260930'
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(OI232))
import bank_valuation as bv  # noqa: E402
from build_historical_valuation_bands import exright_adjust  # noqa: E402
import analyze as a232  # noqa: E402
from divspread_names import INSURER_CODES  # noqa: E402

BANDS = ROOT / 'data/processed/roic_bands.csv'
OBS = OI232 / 'candidates.csv'
HISTORY = EXP / 'insurer_history.csv'
SCAN = ROOT / 'data/processed/daily_buy_candidates.csv'
INDEX = ROOT / 'data/raw/ohlcv/INDEX_000300.csv'
SIGNAL = '2026-09-30'
INS = sorted(INSURER_CODES)
NAMES = {'601318': '中国平安', '601601': '中国太保', '601628': '中国人寿', '601336': '新华保险', '601319': '中国人保'}
BOOT, SEED = 1000, 20261005
CANDS = ('C0', 'C1', 'C2', 'C3', 'C4', 'C5')
LABELS = dict(C0='C0 现行', C1='C1 去 TTM', C2='C2 末年 ROE', C3='C3 三年中位', C4='C4 五年中位', C5='C5 营运利润')


def fnum(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


class Fund(bv.BankFundamentals):
    """生产阶梯另带每行的报告期，供按「当日已知的年报」取锚。"""

    def __init__(self, bands, codes):
        super().__init__(bands, codes)
        rows = defaultdict(list)
        with Path(bands).open(encoding='utf-8', newline='') as fh:
            for r in csv.DictReader(fh):
                code = r['security_code'].zfill(6)
                if code in codes and len(r.get('available_at') or '') == 10 and r['status'] == 'ok':
                    rows[code].append(dict(av=r['available_at'], report=r['report_date'], roe0=fnum(r['roe0']),
                                           roe_ttm=fnum(r['roe_ttm']), ttm=fnum(r['ttm_factor'])))
        self.rows = {c: sorted(v, key=lambda x: (x['av'], x['report'])) for c, v in rows.items()}

    def annual_known(self, code, day):
        """当日已知的各财年年报行（同一财年多版本取可得日最近者），按财年升序。"""
        best = {}
        for r in self.rows.get(code, ()):
            if r['av'] <= day and r['report'].endswith('12-31'):
                best[r['report']] = r
        return [best[k] for k in sorted(best)]

    def annual_final(self, code):
        best = {}
        for r in self.rows.get(code, ()):
            if r['report'].endswith('12-31'):
                best[r['report']] = r
        return {k[:4]: v['roe_ttm'] for k, v in best.items() if v['roe_ttm'] is not None}


def load_opat():
    """insurer_history.csv → {代码: [(可得日, 财年, 营运利润 ROE)]}。营运利润取各财年首次披露版本（`restated = N`），
    可得日取出处中的公告日；ROE = 营运利润 ÷ (期初 + 期末归母权益) / 2。期初权益取同一份报告给出的上年数（有重述行且公告日
    相同时取重述值，即新准则切换年按新口径），否则取上年首次披露版本。"""
    if not HISTORY.exists():
        return {}
    import re

    def day(r):
        m = re.search(r'(20\d\d-\d\d-\d\d)', r.get('source') or '')
        return m.group(1) if m else f"{int(r['period'][:4]) + 1}-04-30"
    first, restated = defaultdict(dict), defaultdict(lambda: defaultdict(list))
    with HISTORY.open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            if (r.get('period_type') or '').upper() != 'FY':
                continue
            code, fy = r['security_code'].zfill(6), r['period'][:4]
            if (r.get('restated') or 'N').upper() == 'N':
                first[code].setdefault(fy, r)
            else:
                restated[code][fy].append(r)
    out = {}
    for code, by in first.items():
        seq = []
        for fy, r in sorted(by.items()):
            opat, eq = fnum(r.get('opat_parent_yi')), fnum(r.get('equity_parent_yi'))
            avail = day(r)
            prior = str(int(fy) - 1)
            same = [x for x in restated[code].get(prior, []) if day(x) == avail]
            prev = same[0] if same else by.get(prior)
            eq0 = fnum(prev.get('equity_parent_yi')) if prev else None
            if opat is None or eq is None or eq0 is None or eq + eq0 <= 0:
                continue
            seq.append((avail, fy, opat / ((eq + eq0) / 2)))
        out[code] = sorted(seq)
    return out


def roe_candidates(fund, opat, code, day):
    f = fund.at(code, day)
    if not f:
        return None, {}
    annual = fund.annual_known(code, day)
    roes = [r['roe_ttm'] for r in annual if r['roe_ttm'] is not None]
    out = dict(C0=f[2], C1=annual[-1]['roe0'] if annual else None, C2=roes[-1] if roes else None,
               C3=statistics.median(roes[-3:]) if len(roes) >= 3 else None,
               C4=statistics.median(roes[-5:]) if len(roes) >= 3 else None, C5=None)
    seq = [x for x in opat.get(code, ()) if x[0] <= day]
    if seq:
        out['C5'] = seq[-1][2]
    return f, out


def v_ddm(f, roe0, actions, day):
    band_av, bps, _roe, payout, basis = f
    if not bps or bps <= 0 or roe0 is None or roe0 <= 0:
        return None
    v = bv.ddm_value(bps, roe0, payout)
    if v is None or v <= 0:
        return None
    (adj,), _fa, _ca = exright_adjust(actions, band_av, day, (v,), split_since=basis)
    return adj if adj > 0 else None


def realized(fund, code, day, years=3):
    final = fund.annual_final(code)
    y0 = int(day[:4])
    vals = [final.get(str(y)) for y in range(y0, y0 + years)]
    return statistics.mean(vals) if all(v is not None for v in vals) else None


def index_quarters():
    closes = {}
    with INDEX.open(encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            closes[r['date']] = float(r['close'])
    days = sorted(closes)
    return closes, days


def main():
    import screen_daily_volume_price_signals as scan
    acts = scan._corporate_actions()
    fund = Fund(BANDS, set(INS))
    opat = load_opat()
    with OBS.open(encoding='utf-8', newline='') as fh:
        obs = list(csv.DictReader(fh))
    rows, mismatch = [], 0
    for r in obs:
        code, day, gb = r['code'], r['date'], fnum(r['g_bar'])
        f, roes = roe_candidates(fund, opat, code, day)
        if f is None:
            continue
        row = dict(code=code, month=r['month'], date=day, panel=r['panel'], close=fnum(r['close']), rf=fnum(r['rf']),
                   g_bar=gb, f3=fnum(r['f3']), f5=fnum(r['f5']), realized3=realized(fund, code, day))
        for k in CANDS:
            dd = v_ddm(f, roes[k], acts.get(code, []), day)
            v = dd * gb if dd and gb else None
            row[f'roe_{k}'] = roes[k]
            row[f'v_{k}'] = v
            row[f'pv_{k}'] = row['close'] / v if v and row['close'] else None
        ref = fnum(r['v_I1c'])
        if ref and row['v_C0'] and abs(row['v_C0'] / ref - 1) > 1e-3:
            mismatch += 1
        rows.append(row)
    with (EXP / 'candidates.csv').open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    rng = np.random.default_rng(SEED)
    res = dict(rows=len(rows), c0_mismatch=mismatch, opat_codes=sorted(opat), readings={})

    # 读数 1：基本面准确性（月末 roe0 vs 其后三个财年实现 ROE 均值）
    def accuracy(cands, subset):
        sample = [r for r in rows if r['realized3'] is not None and r['date'] <= '2023-12-31' and subset(r)
                  and all(r[f'roe_{k}'] is not None for k in cands)]
        if not sample:
            return None
        clusters = {cl: i for i, cl in enumerate(sorted({(r['code'], r['date'][:4]) for r in sample}))}
        idx = np.array([clusters[(r['code'], r['date'][:4])] for r in sample])
        y = np.array([r['realized3'] for r in sample])
        err = {k: np.array([r[f'roe_{k}'] for r in sample]) - y for k in cands}
        out = dict(n=len(sample), clusters=len(clusters), codes=sorted({r['code'] for r in sample}))
        draws = defaultdict(list)
        for _ in range(BOOT):
            w = np.bincount(rng.integers(0, len(clusters), len(clusters)), minlength=len(clusters)).astype(float)[idx]
            base = (w * np.abs(err['C0'])).sum() / w.sum()
            for k in cands:
                draws[k].append((w * np.abs(err[k])).sum() / w.sum() - base)
        for k in cands:
            d = np.array(draws[k])
            out[k] = dict(bias=float(err[k].mean()), mae=float(np.abs(err[k]).mean()),
                          mae_minus_c0=float(np.abs(err[k]).mean() - np.abs(err['C0']).mean()),
                          ci=[float(np.percentile(d, 5)), float(np.percentile(d, 95))])
        return out
    base_c = [k for k in CANDS if k != 'C5']
    res['readings']['accuracy_all'] = accuracy(base_c, lambda r: True)
    res['readings']['accuracy_by_code'] = {c: accuracy(base_c, lambda r, c=c: r['code'] == c) for c in INS}
    if opat:
        res['readings']['accuracy_opat_subset'] = accuracy(list(CANDS), lambda r: r['roe_C5'] is not None)

    # 读数 2：季末 roe0 季度对数变动 vs 沪深 300 同季对数回报
    closes, days = index_quarters()

    def idx_at(day):
        i = bisect.bisect_right(days, day) - 1
        return closes[days[i]] if i >= 0 else None
    swing = {}
    for k in CANDS:
        xs, ys = [], []
        by = defaultdict(dict)
        for r in rows:
            if r['month'][5:] in ('03', '06', '09', '12') and r[f'roe_{k}']:
                by[r['code']][r['month']] = (r['date'], r[f'roe_{k}'])
        for code, m in by.items():
            ks = sorted(m)
            for a, b in zip(ks, ks[1:]):
                ya, ma = map(int, a.split('-')); yb, mb = map(int, b.split('-'))
                if (yb - ya) * 12 + mb - ma != 3:
                    continue
                ia, ib = idx_at(m[a][0]), idx_at(m[b][0])
                if ia and ib and m[b][0] <= days[-1]:
                    xs.append(math.log(ib / ia)); ys.append(math.log(m[b][1] / m[a][1]))
        if len(xs) > 10:
            X = np.column_stack([np.ones(len(xs)), xs]); y = np.array(ys)
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            resid = y - X @ beta
            r2 = 1 - resid.var() / y.var() if y.var() > 0 else None
            swing[k] = dict(pairs=len(xs), slope=float(beta[1]), r2=float(r2) if r2 is not None else None,
                            sd_quarterly=float(np.std(ys)))
    res['readings']['market_swing'] = swing

    # 读数 3：同尺偏差、保险内排序、阶跃（OI-232 analyze 同式）
    ref = a232.load_ref()
    ins = [dict(code=r['code'], month=r['month'], panel=r['panel'] == 'True', f3=r['f3'], f5=r['f5'], rf=r['rf'],
                **{f'pv_{k}': r[f'pv_{k}'] for k in CANDS}, **{f'v_{k}': r[f'v_{k}'] for k in CANDS}) for r in rows]
    rng2 = np.random.default_rng(20260930)
    ruler = {}
    for k in CANDS:
        if not any(r[f'pv_{k}'] for r in ins):
            continue
        sub = [r for r in ins if r[f'pv_{k}'] is not None]
        ruler[k] = dict(same_ruler=a232.same_ruler(ref, sub, k, False, '2007-01', 3, rng2), dynamics=a232.dynamics(sub, k),
                        ranking=a232.ranking(sub, k))
    res['readings']['same_ruler'] = ruler

    # 读数 4：新准则前后季度 TTM 因子偏离
    pre, post = [], []
    for code in INS:
        for r in fund.rows.get(code, ()):
            if r['report'].endswith('12-31') or r['ttm'] is None:
                continue
            (post if r['report'] >= '2023-01-01' else pre).append(abs(r['ttm'] - 1))
    res['readings']['ttm_regime'] = dict(pre_n=len(pre), pre_median_abs_dev=float(np.median(pre)) if pre else None,
                                         post_n=len(post), post_median_abs_dev=float(np.median(post)) if post else None,
                                         pre_p90=float(np.percentile(pre, 90)) if pre else None,
                                         post_p90=float(np.percentile(post, 90)) if post else None)

    # 读数 5：09-30 现值；Ḡ 由生产实时 V（平安）÷ C0 V_DDM 反推，五家同用
    live = {}
    with SCAN.open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            live[r['security_code'].zfill(6)] = (fnum(r['close']), fnum(r['model_intrinsic_value']))
    import build_historical_valuation_bands as bhv
    f_pa, roes_pa = roe_candidates(fund, opat, '601318', SIGNAL)
    g_live = live['601318'][1] / v_ddm(f_pa, roes_pa['C0'], acts.get('601318', []), SIGNAL)
    cur = dict(signal=SIGNAL, g_live=g_live, insurers={})
    for code in INS:
        f, roes = roe_candidates(fund, opat, code, SIGNAL)
        if code in live and live[code][0]:
            price, pday = live[code][0], SIGNAL
        else:
            px = bhv.load_ohlcv(code)
            pday, price = px[-1] if px else (None, None)
        vals = {k: (v_ddm(f, roes[k], acts.get(code, []), SIGNAL) or 0) * g_live or None for k in CANDS}
        cur['insurers'][code] = dict(name=NAMES[code], price=price, price_date=pday, roe0={k: roes[k] for k in CANDS},
                                     v=vals, pv={k: (price / v if price and v else None) for k, v in vals.items()})
    res['current'] = cur
    (EXP / 'readings.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(rows=res['rows'], c0_mismatch=mismatch, opat=res['opat_codes'],
                          accuracy=res['readings']['accuracy_all'], swing=swing,
                          ttm_regime=res['readings']['ttm_regime']), ensure_ascii=False, indent=1))
    for k, v in ruler.items():
        s = v['same_ruler']
        print(k, 'c_ins %.2f [%.2f, %.2f]' % (s['c_ins'] * 100, s['c_ins_ci'][0] * 100, s['c_ins_ci'][1] * 100),
              'rankIC', v['ranking'], 'jump', round(v['dynamics']['jump_share'], 3))
    for code, e in cur['insurers'].items():
        print(code, e['name'], e['price'], {k: (round(x, 4) if x else None) for k, x in e['roe0'].items()},
              {k: (round(x, 3) if x else None) for k, x in e['pv'].items()})


if __name__ == '__main__':
    main()
