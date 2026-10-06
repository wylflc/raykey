"""OI-269＋OI-231 银行检验（preregister.md）：月末银行 V 在 C／R／B／K／RBK 五臂下重算（G 逐臂按截面同式），
估值准确性（包含检验、月度截面排序）与买入区识别力（S1 低派息、S2 资本宽松度下三分之一、S3 摊薄）。

    python3 bank_test.py     # → observations.json、results.json、readings.md
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
from scipy.stats import rankdata

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
import backtest_valuation_strategy as bt  # noqa: E402
import bank_valuation as bv  # noqa: E402
import build_historical_valuation_bands as bhv  # noqa: E402
import caliber_fairness as cf  # noqa: E402
import opportunity_trap_audit as audit  # noqa: E402
import screen_daily_volume_price_signals as scan  # noqa: E402
from build_historical_valuation_bands import exright_adjust  # noqa: E402
from moat_param_lab import forward_annualized, total_return_index  # noqa: E402

LINE = 1.0034
START = '2010-01-01'
ARMS = ('R', 'B', 'K', 'RBK')
COE, COE_TIGHT, BV_CAP = 0.10, 0.11, 0.07
PAYOUT_LOW, DILUTION_MIN = 0.20, 0.05
PERIODS = (('2010-01', '2016-12'), ('2017-01', '2023-08'))
CASES = ('600036', '002142', '601838', '601318')
INSURER = '601318'
BOOT, SEED = 1000, 20261006


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def ddm(bps, roe0, payout, coe=COE, cap=None):
    """`bank_valuation.ddm_value` 同式（可持续终值派息率），另可把 BV 年增速封顶（B 臂）。"""
    b = 1.0 - (payout if payout is not None else bv.DEFAULT_PAYOUT)
    b = min(max(b, 0.0), 1.0)
    roe_t_end = min(roe0, coe + bv.TERMINAL_EXCESS)
    g_t = min(bv.G_CAP, roe_t_end * b)
    if coe - g_t < 0.02:
        return None
    pay, value, book = 1.0 - b, 0.0, bps
    for t in range(1, bv.FADE_YEARS + 1):
        roe_t = roe0 + (roe_t_end - roe0) * t / bv.FADE_YEARS
        value += roe_t * book * pay / (1.0 + coe) ** t
        growth = roe_t * b
        book *= 1.0 + (min(growth, cap) if cap is not None else growth)
    return value + roe_t_end * book * (1.0 - g_t / roe_t_end) / (coe - g_t) / (1.0 + coe) ** bv.FADE_YEARS


def load_fundamentals(codes):
    seq = defaultdict(list)
    with (ROOT / 'data/processed/roic_bands.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            c = r['security_code'].zfill(6)
            av = r.get('available_at') or ''
            if c in codes and len(av) == 10:
                seq[c].append(dict(av=av, rd=r.get('report_date') or '', bps=num(r.get('bps')), roe0=num(r.get('roe0')),
                                   roe_ttm=num(r.get('roe_ttm')), payout=num(r.get('payout')), basis=r.get('bps_basis_date') or av))
    return {c: sorted(v, key=lambda x: x['av']) for c, v in seq.items()}


def fund_at(rows, day):
    keys = [r['av'] for r in rows]
    i = bisect.bisect_right(keys, day) - 1
    return (rows[i], rows[:i + 1]) if i >= 0 else (None, [])


def roe_r(row, history):
    """R 臂：min(可得年报 ROE 最近三年中位, 当期 TTM ROE)；缺失退 roe0。"""
    annual = {}
    for h in history:
        if h['rd'].endswith('-12-31') and h['roe_ttm'] is not None:
            annual[h['rd']] = h['roe_ttm']
    last = [annual[k] for k in sorted(annual)[-3:]]
    if not last or row['roe_ttm'] is None:
        return row['roe0']
    return min(statistics.median(last), row['roe_ttm'])


def load_balance(codes):
    """年报：(公告日, 报告期, 普通股权益 ÷ 总资产, 股本)。"""
    out = defaultdict(list)
    with (ROOT / 'data/raw/financials_statements/balance.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            c = (r.get('security_code') or '').zfill(6)
            rd = (r.get('REPORT_DATE') or '')[:10]
            if c not in codes or not rd.endswith('-12-31'):
                continue
            ta, pe = num(r.get('TOTAL_ASSETS')), num(r.get('TOTAL_PARENT_EQUITY'))
            oet = num(r.get('OTHER_EQUITY_TOOL')) or 0.0
            out[c].append(((r.get('NOTICE_DATE') or '')[:10], rd, (pe - oet) / ta if ta and pe else None, num(r.get('SHARE_CAPITAL'))))
    return {c: sorted(v, key=lambda x: x[1]) for c, v in out.items()}


def equity_ratio(bal, day):
    rows = [x for x in bal if x[0] and x[0] <= day and x[2] is not None]
    return rows[-1][2] if rows else None


def dilution(bal, actions, day):
    """最近两个可得年报间隔两年的股本增长，扣除其间送转（公司行动 share_ratio）。"""
    rows = [x for x in bal if x[0] and x[0] <= day and x[3]]
    if len(rows) < 3:
        return None
    (_, rd1, _, s1), (_, rd0, _, s0) = rows[-1], rows[-3]
    bonus = 1.0
    for a in actions:
        ex = a.get('ex_dividend_date') or ''
        if rd0 < ex <= rd1:
            bonus *= 1.0 + (bhv._num(a.get('share_ratio')) or 0.0)
    return s1 / (s0 * bonus) - 1.0


def month_end_days(prices):
    days = sorted({d for p in prices.values() for d in p if d >= START})
    last = {}
    for d in days:
        last[d[:7]] = d
    return sorted(last.values())


def production_bank_v(codes, days):
    want = set(days)
    out = {}
    with (ROOT / 'data/processed/a_share_daily_states_adopted.csv').open(encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            c = r['security_code']
            if c in codes and r['date'] in want:
                out[(c, r['date'])] = num(r['intrinsic_value'])
    return out


def panel_members():
    spans = defaultdict(list)
    with (ROOT / 'data/processed/pit_attention/panel_moat_bank_v6b.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            spans[r['security_code'].zfill(6)].append((r['effective_from'], r['effective_to']))
    return spans


def build(banks, names, members):
    """`members[day]`：生产逐日状态当日有行的银行——与 `rebuild_bank_bands.py h2` 同一截面（停牌或尚无带的银行不进当日 G）。"""
    fund = load_fundamentals(banks | {INSURER})
    bal = load_balance(banks)
    acts = bhv.load_actions()
    prices = bt.load_prices(banks | {INSURER})
    days = month_end_days({c: prices[c] for c in banks if c in prices})
    tr = {}
    for c in banks:
        p = bhv.load_ohlcv(c)
        if p:
            tr[c] = ([d for d, _ in p], total_return_index(p, acts.get(c, [])))
    spans = panel_members()
    rows, gs = [], {a: {} for a in ('C', *ARMS)}
    for day in days:
        rf = scan._default_rf(day)
        ratios = {c: equity_ratio(bal.get(c, []), day) for c in banks}
        known = sorted(v for v in ratios.values() if v is not None)
        cut = known[len(known) // 3] if len(known) >= 6 else None
        per = {}
        for c in sorted(members.get(day, set())):
            row, hist = fund_at(fund.get(c, []), day)
            if not row or not row['bps'] or row['bps'] <= 0 or not row['roe0'] or row['roe0'] <= 0:
                continue
            tight = cut is not None and ratios[c] is not None and ratios[c] < cut
            r_roe = roe_r(row, hist)
            spec = dict(C=(row['roe0'], COE, None), R=(r_roe, COE, None), B=(row['roe0'], COE, BV_CAP),
                        K=(row['roe0'], COE_TIGHT if tight else COE, None), RBK=(r_roe, COE_TIGHT if tight else COE, BV_CAP))
            vdd = {}
            for arm, (roe, coe, cap) in spec.items():
                v = ddm(row['bps'], roe, row['payout'], coe, cap) if roe and roe > 0 else None
                if v and v > 0:
                    (adj,), _f, _c = exright_adjust(acts.get(c, []), row['av'], day, (v,), split_since=row['basis'])
                    vdd[arm] = adj if adj > 0 else None
            d0 = scan.bank_dividend_intrinsic(c, day, rf) if rf is not None else None
            per[c] = dict(d0=d0, vdd=vdd, payout=row['payout'], tight=tight, ratio=ratios[c],
                          dil=dilution(bal.get(c, []), acts.get(c, []), day))
        values = {}
        for arm in ('C', *ARMS):
            g = bv.h2_scale((x['d0'], x['vdd'].get(arm)) for x in per.values())
            gs[arm][day] = g
            for c, x in per.items():
                if g is not None and x['vdd'].get(arm):
                    values[(c, arm)] = x['vdd'][arm] * g * bv.BANK_SCALE
                elif g is None and x['d0']:
                    values[(c, arm)] = x['d0'] * bv.BANK_SCALE
        for c, x in per.items():
            close = prices.get(c, {}).get(day)
            if not close or (c, 'C') not in values:
                continue
            days_c, tr_c = tr.get(c, ([], {}))
            f3 = forward_annualized(tr_c, days_c, day, 3) if day in tr_c else None
            f5 = forward_annualized(tr_c, days_c, day, 5) if day in tr_c else None
            rec = dict(code=c, name=names.get(c, ''), date=day, month=day[:7], industry='bank', f3=f3, f5=f5,
                       payout=x['payout'], tight=x['tight'], ratio=x['ratio'], dil=x['dil'], V_C=values[(c, 'C')],
                       panel=any(a <= day <= b for a, b in spans.get(c, [])))
            for arm in ('C', *ARMS):
                v = values.get((c, arm))
                rec[f'pv_{arm}'] = close / v if v else None
            rec['groups'] = {}
            rows.append(rec)
    return rows, gs, days, fund, acts


def now_values(banks, fund, acts, gs, day='2026-09-30'):
    """信号日现值（与实盘 `live_h2` 同截面：全部有带的银行）：各臂银行 V 与平安 `V_DDM × Ḡ`（Ḡ 取该臂前 36 个月末 G 的中位，
    月末 G 用本检验的月末截面）。收盘取 `daily_buy_candidates.csv`。"""
    rf = scan._default_rf(day)
    bal = load_balance(banks)
    ratios = {c: equity_ratio(bal.get(c, []), day) for c in banks}
    known = sorted(v for v in ratios.values() if v is not None)
    cut = known[len(known) // 3] if len(known) >= 6 else None
    vdd, d0 = defaultdict(dict), {}
    for c in sorted(banks | {INSURER}):
        row, hist = fund_at(fund.get(c, []), day)
        if not row or not row['bps'] or row['bps'] <= 0 or not row['roe0'] or row['roe0'] <= 0:
            continue
        tight = c != INSURER and cut is not None and ratios.get(c) is not None and ratios[c] < cut
        r_roe = roe_r(row, hist)
        spec = dict(C=(row['roe0'], COE, None), R=(r_roe, COE, None), B=(row['roe0'], COE, BV_CAP),
                    K=(row['roe0'], COE_TIGHT if tight else COE, None), RBK=(r_roe, COE_TIGHT if tight else COE, BV_CAP))
        for arm, (roe, coe, cap) in spec.items():
            v = ddm(row['bps'], roe, row['payout'], coe, cap) if roe and roe > 0 else None
            if v and v > 0:
                (adj,), _f, _c = exright_adjust(acts.get(c, []), row['av'], day, (v,), split_since=row['basis'])
                if adj > 0:
                    vdd[c][arm] = adj
        if c != INSURER:
            d0[c] = scan.bank_dividend_intrinsic(c, day, rf) if rf is not None else None
    quotes = {r['security_code']: r for r in csv.DictReader((ROOT / 'data/processed/daily_buy_candidates.csv').open(encoding='utf-8'))}
    out = {}
    for arm in ('C', *ARMS):
        g = bv.h2_scale((d0.get(c), vdd[c].get(arm)) for c in sorted(banks))
        ends = bv.month_ends_before(day)
        hist_g = [gs[arm].get(max([d for d in gs[arm] if d <= e], default='')) for e in ends]
        hist_g = [x for x in hist_g if x]
        g_bar = statistics.median(hist_g) if len(hist_g) >= bv.INSURER_G_MIN else None
        for c in CASES:
            v = vdd[c].get(arm)
            val = (v * g_bar if g_bar else None) if c == INSURER else (v * g * bv.BANK_SCALE if v and g else None)
            close = num(quotes.get(c, {}).get('close'))
            out.setdefault(c, {})[arm] = dict(V=val, pv=close / val if close and val else None,
                                              production=num(quotes.get(c, {}).get('model_intrinsic_value')))
    return out


def rank(rows, arm, horizon, min_banks=8):
    by = defaultdict(list)
    for r in rows:
        if r.get(f'pv_{arm}') and r[f'f{horizon}'] is not None and cf.PV_RANGE[0] <= r['pv_C'] <= cf.PV_RANGE[1]:
            by[r['month']].append(r)
    diffs, cs, ars = [], [], []
    for m in sorted(by):
        rs = by[m]
        if len(rs) < min_banks:
            continue
        ry = rankdata([r[f'f{horizon}'] for r in rs])
        rc = float(np.corrcoef(rankdata([r['pv_C'] for r in rs]), ry)[0, 1])
        ra = float(np.corrcoef(rankdata([r[f'pv_{arm}'] for r in rs]), ry)[0, 1])
        if math.isfinite(rc) and math.isfinite(ra):
            cs.append(rc); ars.append(ra); diffs.append(ra - rc)
    return dict(months=len(diffs), C=float(np.mean(cs)) if cs else None, arm=float(np.mean(ars)) if ars else None,
                diff=float(np.mean(diffs)) if diffs else None, diff_t=cf.newey_west_t(diffs, 12 * horizon) if diffs else None)


def verdict(ci):
    lo, hi = ci
    if lo is None:
        return '不可估'
    has0, has1 = lo <= 0 <= hi, lo <= 1 <= hi
    return '支持' if (not has0 and has1) else '不支持' if (has0 and not has1) else '不能区分' if (has0 and has1) else '0 与 1 都不含'


def identify(rows, labels, rng):
    zone = [r for r in rows if r['pv_C'] is not None and r['pv_C'] <= LINE and r['f3'] is not None]
    tests = dict(S1=lambda r: r['payout'] is not None and r['payout'] < PAYOUT_LOW, S2=lambda r: r['tight'],
                 S3=lambda r: r['dil'] is not None and r['dil'] > DILUTION_MIN)
    out = {}
    for name, cond in tests.items():
        res = {}
        for lo, hi in (('2010-01', '2023-08'), *PERIODS):
            sub = [r for r in zone if lo <= r['month'] <= hi]
            codes = sorted({r['code'] for r in sub})
            idx = {c: i for i, c in enumerate(codes)}

            def stat(w):
                g = [(r, w[idx[r['code']]]) for r in sub if cond(r)]
                o = [(r, w[idx[r['code']]]) for r in sub if not cond(r)]
                if sum(x for _, x in g) == 0 or sum(x for _, x in o) == 0:
                    return None
                wm = lambda xs: float(np.average([r['f3'] for r, _ in xs], weights=[x for _, x in xs]))
                lab = lambda xs, t: float(np.average([labels.get((r['code'], r['month'])) == t for r, _ in xs], weights=[x for _, x in xs]))
                return (wm(g) - wm(o), lab(g, '机会') - lab(o, '机会'), lab(g, '陷阱') - lab(o, '陷阱'))
            point = stat(np.ones(len(codes)))
            draws = [stat(np.bincount(rng.integers(0, len(codes), len(codes)), minlength=len(codes)).astype(float)) for _ in range(BOOT)]
            draws = [d for d in draws if d is not None]
            res[f'{lo}～{hi}'] = dict(n_group=sum(1 for r in sub if cond(r)), n_rest=sum(1 for r in sub if not cond(r)), banks=len(codes),
                                     ret_diff=point[0] if point else None, ret_ci=cf.interval([d[0] for d in draws]),
                                     opp_diff=point[1] if point else None, opp_ci=cf.interval([d[1] for d in draws]),
                                     trap_diff=point[2] if point else None, trap_ci=cf.interval([d[2] for d in draws]))
        out[name] = res
    return out


def main():
    banks = bv.bank_codes(ROOT / 'data/raw/a_share_securities.csv')
    names = {}
    with (ROOT / 'data/raw/a_share_securities.csv').open(encoding='utf-8-sig', newline='') as fh:
        names = {r['security_code'].zfill(6): r.get('security_name', '') for r in csv.DictReader(fh)}
    prices = bt.load_prices(banks)
    days_all = month_end_days({c: prices[c] for c in banks if c in prices})
    prod = production_bank_v(banks, days_all)
    members = defaultdict(set)
    for (c, d) in prod:
        members[d].add(c)
    rows, gs, days, fund, acts = build(banks, names, members)
    rel = [abs(r['V_C'] / prod[(r['code'], r['date'])] - 1) for r in rows if prod.get((r['code'], r['date']))]
    repro = dict(compared=len(rel), within_1e6=sum(1 for x in rel if x <= 1e-6), max_rel=max(rel) if rel else None,
                 share_within=sum(1 for x in rel if x <= 1e-6) / len(rel) if rel else None)
    (EXP / 'observations.json').write_text(json.dumps(dict(rows=rows, reproduction=repro), ensure_ascii=False, default=float) + '\n', encoding='utf-8')
    rng = np.random.default_rng(SEED)
    answer, _eps = audit.load_answer_key(audit.LABELS)
    labels = {(r['code'], r['month']): r['label'] for r in answer}
    res = dict(reproduction=repro, months=len(days), banks=len(banks), arms={})
    for arm in ARMS:
        entry = {}
        for pop in ('panel', 'all'):
            sub = [r for r in rows if pop == 'all' or r['panel']]
            for h in (3, 5):
                s = cf.Sample(sub, arm, h)
                enc = cf.readout_encompass(s, rng, BOOT)
                entry[f'{pop}|{h}y'] = dict(encompass=enc, verdict=verdict(enc.get('lam_ci', [None, None])), rank=rank(sub, arm, h))
        entry['disagreement'] = cf.readout_disagreement(rows, arm)
        res['arms'][arm] = entry
    res['identify'] = identify(rows, labels, rng)
    res['now'] = dict(day='2026-09-30', values=now_values(banks, fund, acts, gs))
    (EXP / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')
    write_md(res)


def write_md(res):
    f = lambda v, d=3: '—' if v is None else f'{v:.{d}f}'
    ci = lambda c: '—' if not c or c[0] is None else f'[{c[0]:.2f}, {c[1]:.2f}]'
    md = ['# OI-269＋OI-231 银行检验读数（月末，候选只改 V_DDM 输入、G 逐臂重算）', '',
          f"复现：C 臂月末 V 对生产逐日状态同日比较 {res['reproduction']['compared']} 个，相对差 ≤ 1e-6 占 {f(res['reproduction']['share_within'], 4)}，"
          f"最大 {f(res['reproduction']['max_rel'], 6)}；月末 {res['months']} 个、银行 {res['banks']} 家。", '',
          '## 1. 估值候选（包含检验 λ 与 90% 区间；月度截面 Spearman 配对差与 NW t）', '',
          '| 臂 | 面板 3 年 | 面板 5 年 | 全部 3 年 | 全部 5 年 | 分歧 |d|≥0.10 占比 |', '|---|---|---|---|---|---|']
    for arm, e in res['arms'].items():
        cells = []
        for key in ('panel|3y', 'panel|5y', 'all|3y', 'all|5y'):
            x = e[key]
            enc, rk = x['encompass'], x['rank']
            cells.append(f"λ {f(enc.get('lam'), 2)} {ci(enc.get('lam_ci'))} {x['verdict']}；排序 {f(rk['diff'], 3)}（t {f(rk['diff_t'], 2)}）")
        md.append(f"| {arm} | " + ' | '.join(cells) + f" | {f(e['disagreement'].get('share_abs_ge_010'), 3)} |")
    md += ['', '## 2. 识别力（买入区银行月份；组内 − 其余：其后 3 年年化回报、机会占比、陷阱占比，90% 区间）', '']
    for name, per in res['identify'].items():
        md.append(f"- {name}：" + '；'.join(
            f"{k} n={v['n_group']}/{v['n_rest']}（{v['banks']} 家）回报 {f(v['ret_diff'], 3)} {ci(v['ret_ci'])}、机会 {f(v['opp_diff'], 3)} {ci(v['opp_ci'])}、"
            f"陷阱 {f(v['trap_diff'], 3)} {ci(v['trap_ci'])}" for k, v in per.items()))
    md += ['', f"## 3. 现值（{res['now']['day']}，各臂 V／P/V；括号内为生产 V）", '']
    for c, v in res['now']['values'].items():
        md.append(f"- {c}（生产 {f(v['C']['production'], 2)}）：" + '、'.join(f"{a} {f(x['V'], 2)}／{f(x['pv'])}" for a, x in v.items()))
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
