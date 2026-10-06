"""现行 BASE 长跑的分时段读数与收益来源（描述统计，不进任何判定）。读 run.py 的 runs/ 与在册 summary。

* 长跑锚点 2009-11-01、2011-11-01 与 14 起点的全期 CAGR、最大回撤、滚动 5 年分布（引擎 `rolling_windows` 原函数的逐窗口值）。
* 2009-11 路径逐自然年：收益、沪深 300（价格指数）、年内最大回撤、平均仓位、股债上限受限日占比、逐票盈亏前三与后三；
  另列 14 起点同年收益的中位与范围（只取覆盖整年的起点）。
* 2009-11 路径按净值 30% 反转切分涨跌波段（zigzag，下跌段即全部 ≥ 30% 的回撤），逐段报同期沪深 300、平均仓位、
  逐票与行业盈亏，及同一日历区间在 14 起点路径上的收益中位与范围。
* 「持仓本身」= 同一组持仓的时间加权链式收益（见 `period`），与净资产收益之差 = 仓位高低（融资放大、股债上限减仓、
  闲置现金）与利息费用的合计作用。
* 分期贡献：逐日 `pnl ÷ 前一日净资产`（引擎赢家尺的逐日项；pnl = 市值变动 − 买入 ＋ 卖出与分红）按 Carino 系数
  `[ln(1+r_t)/r_t] ÷ [ln(1+R)/R]` 链接到期间收益 R，各代码之和 ＋「费用、利息与股息税」= R（逐期精确相加，且早晚同一把尺，
  不像「金额 ÷ 期初净资产」那样放大长波段后期）；全期排名报引擎尺 Σ 逐日盈亏 ÷ 前一日净资产（pp）。

    python3 analyze.py      # → report.md、years.csv、legs.csv、codes.csv、windows5.csv、analysis.json
"""
import bisect
import csv
import json
import math
import statistics as st
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
RUNS = EXP / 'runs'
sys.path.insert(0, str(ROOT / 'scripts'))
import sweep_backtest_configs as sw  # noqa: E402

csv.field_size_limit(10 ** 9)
CAPITAL = 3_000_000.0
MAIN, SECOND = '2009-11-01', '2011-11-01'
ZIGZAG = 0.30
STARTS = sw.DEFAULT_STARTS


def tag(start):
    return sw.summary_tag('BASE', start)


def summary(start, ex=False):
    return next(csv.DictReader((ROOT / 'data/backtest' / f'summary_{tag(start)}{"ex5" if ex else ""}.csv').open(encoding='utf-8')))


def load_curve(start):
    out = []
    for r in csv.DictReader((RUNS / f'{tag(start)}_curve.csv').open(encoding='utf-8')):
        e, c, d = float(r['net_equity']), float(r['cash']), float(r['debt'])
        out.append(dict(date=r['date'], eq=e, debt=d, mv=e - c + d, n=int(r['positions'])))
    return out


def load_pnl(start):
    pnl, rel = defaultdict(lambda: defaultdict(float)), defaultdict(float)
    for r in csv.DictReader((RUNS / f'{tag(start)}_daily_pnl.csv').open(encoding='utf-8')):
        p = float(r['pnl'])
        pnl[r['date']][r['security_code']] += p
        rel[r['security_code']] += p / float(r['eq_prev'])
    return pnl, rel


def load_eb(start):
    path = RUNS / 'eb' / f'_{tag(start)}.csv'
    if not path.exists():
        return {}
    return {r['date']: r['cap'] not in ('', 'None', 'nan') for r in csv.DictReader(path.open(encoding='utf-8'))}


def load_names():
    names = {}
    for r in csv.DictReader((ROOT / 'data/raw/a_share_securities.csv').open(encoding='utf-8-sig')):
        names[r['security_code'].zfill(6)] = r['security_name'].replace(' ', '')
    return names


def load_industry():
    ind = {}
    for r in csv.DictReader((ROOT / 'data/processed/a_share_company_analysis_index.csv').open(encoding='utf-8-sig')):
        ind[r['security_code'].zfill(6)] = (r.get('industry') or '').split(' ')[-1] or '未分类'
    for r in csv.DictReader((ROOT / 'data/reference/a_share_csrc_industry.csv').open(encoding='utf-8')):
        parts = (r.get('em2016') or '').split('-')
        if len(parts) >= 2 and parts[1]:
            ind[r['security_code'].zfill(6)] = parts[1]
    return ind


def load_index():
    rows = [(r['date'], float(r['close'])) for r in csv.DictReader((ROOT / 'data/raw/ohlcv/INDEX_000300.csv').open(encoding='utf-8')) if r['close']]
    return [d for d, _ in rows], [v for _, v in rows]


IDX_D, IDX_V = load_index()


def index_at(day):
    k = bisect.bisect_right(IDX_D, day) - 1
    return (IDX_D[k], IDX_V[k]) if k >= 0 else (None, None)


def index_ret(d0, d1):
    a, va = index_at(d0)
    b, vb = index_at(d1)
    if a is None or b is None or b <= d0:
        return None, b
    return vb / va - 1, b


def mdd(values):
    peak, worst = -1.0, 0.0
    for v in values:
        peak = max(peak, v)
        worst = max(worst, 1 - v / peak)
    return worst


def q(xs, p):
    xs = sorted(xs)
    pos = (len(xs) - 1) * p
    lo, hi = int(pos), min(int(pos) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def period(curve, pnl, eb, i0, i1, first=False):
    """(i0, i1] 区间：i0 = 基准日下标（first 时基准为初始资本、含第 0 日）。

    `codes`／`resid`：逐日 pnl ÷ 前一日净资产（费用利息股息税同除）按 Carino 系数链接，合计 = 期间收益 `ret`。
    `unlev` = 持仓本身的链式收益 Π(1 + 当日各代码盈亏之和 ÷ 前一日持仓市值) − 1，与 `ret` 之差即仓位高低
    （融资放大、股债上限减仓、闲置现金）与利息费用的合计作用。"""
    base = CAPITAL if first else curve[i0]['eq']
    k0 = i0 if first else i0 + 1
    days = curve[k0:i1 + 1]
    ret = curve[i1]['eq'] / base - 1
    link = math.log1p(ret) / ret if ret else 1.0
    by, resid, unlev, prev_eq = defaultdict(float), 0.0, 1.0, base
    for k in range(k0, i1 + 1):
        eq = curve[k]['eq']
        r = eq / prev_eq - 1
        kt = (math.log1p(r) / r if r else 1.0) / link
        day_pnl = pnl.get(curve[k]['date'], {})
        total = sum(day_pnl.values())
        for code, p in day_pnl.items():
            by[code] += p / prev_eq * kt
        resid += (eq - prev_eq - total) / prev_eq * kt
        prev_mv = curve[k - 1]['mv'] if k > 0 else 0.0
        if prev_mv > 0:
            unlev *= 1 + total / prev_mv
        prev_eq = eq
    assert abs(sum(by.values()) + resid - ret) < 1e-9 * max(1.0, abs(ret)), (curve[i0]['date'], curve[i1]['date'])
    seg = [base] + [r['eq'] for r in days]
    return dict(start=curve[i0]['date'], end=curve[i1]['date'], days=len(days), ret=ret, resid=resid, mdd=mdd(seg),
                unlev=unlev - 1,
                exposure=st.fmean(r['mv'] / r['eq'] for r in days), lev=st.fmean(r['debt'] / r['eq'] for r in days),
                npos=st.median(r['n'] for r in days), eb=st.fmean(eb.get(r['date'], False) for r in days) if eb else 0.0,
                codes=dict(by))


def eb_episodes(eb):
    """股债总仓位上限受限的连续区间 [(首日, 末日, 交易日数)]。"""
    out, cur = [], None
    for day in sorted(eb):
        if eb[day]:
            cur = [day, day, 1] if cur is None else [cur[0], day, cur[2] + 1]
        elif cur:
            out.append(tuple(cur)); cur = None
    return out + ([tuple(cur)] if cur else [])


def cross_leg(curves, d0, d1):
    """同一日历区间在各起点路径上的收益（只取 d0 时已在跑的起点）。"""
    out = []
    for c in curves.values():
        dates = [r['date'] for r in c]
        if dates[0] > d0:
            continue
        a, b = bisect.bisect_right(dates, d0) - 1, bisect.bisect_right(dates, d1) - 1
        out.append(c[b]['eq'] / c[a]['eq'] - 1)
    return dict(n=len(out), median=st.median(out), lo=min(out), hi=max(out)) if out else None


def zigzag(values, thr):
    piv, d, ext, hi, lo = [0], 0, 0, 0, 0
    for i in range(1, len(values)):
        v = values[i]
        if d == 0:
            hi = i if v > values[hi] else hi
            lo = i if v < values[lo] else lo
            if v <= values[hi] * (1 - thr):
                piv += [hi] if hi else []
                d, ext = -1, i
            elif v >= values[lo] * (1 + thr):
                piv += [lo] if lo else []
                d, ext = 1, i
        elif d == 1:
            if v > values[ext]:
                ext = i
            elif v <= values[ext] * (1 - thr):
                piv.append(ext); d, ext = -1, i
        else:
            if v < values[ext]:
                ext = i
            elif v >= values[ext] * (1 + thr):
                piv.append(ext); d, ext = 1, i
    for k in (ext, len(values) - 1):
        if k != piv[-1]:
            piv.append(k)
    return piv


def years_of(curve):
    """逐自然年 (年, 基准下标, 末下标, 是否首段)。"""
    ends = [i for i in range(len(curve)) if i == len(curve) - 1 or curve[i]['date'][:4] != curve[i + 1]['date'][:4]]
    out, prev = [], 0
    for k, i in enumerate(ends):
        out.append((curve[i]['date'][:4], prev, i, k == 0))
        prev = i
    return out


def fmt_codes(codes, names, n=3, sign=1):
    items = sorted(((v, c) for c, v in codes.items() if v * sign > 0), reverse=(sign > 0))[:n]
    return '、'.join(f"{names.get(c, c)} {v * 100:+.1f}%" for v, c in items) or '—'


def by_industry(codes, ind):
    out = defaultdict(float)
    for c, v in codes.items():
        out[ind.get(c, '未分类')] += v
    return out


def pct(v, nd=1, last=None, end=None):
    """指数行情止于区间末日之前时标 *（只算到指数末日）。"""
    return '—' if v is None else f'{v * 100:+.{nd}f}%' + ('*' if last and end and last < end else '')


def main():
    names, ind = load_names(), load_industry()
    reg = {s: summary(s) for s in STARTS}
    regx = {s: summary(s, ex=True) for s in STARTS}
    curves = {s: load_curve(s) for s in STARTS}
    res, md = {}, []

    # ---- 一、长跑锚点与 14 起点 ----
    anchors = {}
    for s in (MAIN, SECOND):
        r, x, c = reg[s], regx[s], curves[s]
        anchors[s] = dict(first=r['首个净值日'], last=r['末次净值日'], multiple=float(r['期末资产']) / CAPITAL, cagr=float(r['年化']),
                          mdd=float(r['最大回撤']), mdd_range=r['回撤区间'], calmar=float(r['Calmar']), sharpe=float(r['Sharpe']),
                          vol=float(r['年化波动']), exposure=float(r['平均仓位']), min_margin=float(r['最低担保比例']),
                          min_margin_day=r['最低担保比例日'], top5=r['前五赢家'], top5_share=float(r['前五赢家占正贡献']),
                          ex5_cagr=float(x['年化']), ex5_mdd=float(x['最大回撤']), ex5_mdd_range=x['回撤区间'],
                          check_cagr=(c[-1]['eq'] / CAPITAL) ** (365.25 / (date.fromisoformat(c[-1]['date']) - date.fromisoformat(c[0]['date'])).days) - 1,
                          check_mdd=mdd([CAPITAL] + [row['eq'] for row in c]))
    cross = {k: dict(median=st.median(float(reg[s][k]) for s in STARTS), lo=min(float(reg[s][k]) for s in STARTS),
                     hi=max(float(reg[s][k]) for s in STARTS),
                     ex5_median=st.median(float(regx[s][k]) for s in STARTS))
             for k in ('年化', '最大回撤', '滚动5年年化中位', '滚动5年年化P25', '滚动5年年化最差', '滚动5年回撤中位', '互不重叠5年块中位')}
    res['anchors'], res['cross'] = anchors, cross

    # ---- 二、滚动 5 年 ----
    win = {s: json.loads((RUNS / f'{tag(s)}_windows.json').read_text(encoding='utf-8'))['5'] for s in STARTS}
    for s in STARTS:      # 与在册 summary 逐窗口核对
        regwin = sw.parse_window_series(reg[s][sw.WIN5_KEY])
        mine = {w['end'][:7]: w['cagr'] for w in win[s]}
        assert set(regwin) == set(mine) and all(abs(regwin[k] - mine[k]) < 1e-8 for k in mine), s
    w0 = win[MAIN]
    with (EXP / 'windows5.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['start', 'window_start', 'window_end', 'cagr', 'mdd', 'calmar', 'sharpe'])
        for s in STARTS:
            for x in win[s]:
                w.writerow([s, x['start'], x['end'], f"{x['cagr']:.6f}", f"{x['mdd']:.6f}", f"{x['calmar']:.4f}", f"{x['sharpe']:.4f}"])
    dist = lambda xs: dict(min=min(xs), p10=q(xs, .1), p25=q(xs, .25), median=q(xs, .5), p75=q(xs, .75), max=max(xs))
    roll = dict(n=len(w0), first_end=w0[0]['end'], last_end=w0[-1]['end'], cagr=dist([x['cagr'] for x in w0]),
                mdd=dist([x['mdd'] for x in w0]),
                worst=sorted(w0, key=lambda x: x['cagr'])[:3], best=sorted(w0, key=lambda x: -x['cagr'])[:3],
                deepest=sorted(w0, key=lambda x: -x['mdd'])[:1],
                share_mdd_ge_35=sum(x['mdd'] >= .35 for x in w0) / len(w0),
                share_cagr_lt_20=sum(x['cagr'] < .20 for x in w0) / len(w0),
                december={x['end'][:4]: (x['cagr'], x['mdd']) for x in w0 if x['end'][5:7] == '12'},
                latest=(w0[-1]['end'], w0[-1]['cagr'], w0[-1]['mdd']),
                per_start_mdd_median=st.median(st.median(x['mdd'] for x in win[s]) for s in STARTS),
                per_start_mdd_worst=max((max(x['mdd'] for x in win[s]), s) for s in STARTS),
                pooled_min=min((x['cagr'], s, x['end']) for s in STARTS for x in win[s]))
    res['rolling5'] = roll

    # ---- 三、逐年（2009-11 路径）与 14 起点同年 ----
    pnl0, rel0 = load_pnl(MAIN)
    eb0 = load_eb(MAIN)
    c0 = curves[MAIN]
    year_rets = defaultdict(dict)
    for s in STARTS:
        c = curves[s]
        for y, i0, i1, first in years_of(c):
            full_year = not first and c[i1]['date'][5:] >= '12-25'
            if full_year:
                year_rets[y][s] = c[i1]['eq'] / c[i0]['eq'] - 1
    years = []
    for y, i0, i1, first in years_of(c0):
        p = period(c0, pnl0, eb0, i0, i1, first)
        p['year'], (p['index'], p['index_end']) = y, index_ret(p['start'] if not first else c0[0]['date'], p['end'])
        xs = list(year_rets.get(y, {}).values())
        p['cross'] = dict(n=len(xs), median=st.median(xs), lo=min(xs), hi=max(xs), pos=sum(v > 0 for v in xs)) if xs else None
        years.append(p)
    with (EXP / 'years.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['year', 'start', 'end', 'return', 'holdings_unlevered', 'csi300', 'mdd_in_year', 'avg_exposure', 'avg_debt_ratio',
                    'eb_cap_days', 'cost_resid', 'cross_n', 'cross_median', 'cross_min', 'cross_max', 'top_contrib', 'top_detract'])
        for p in years:
            cr = p['cross'] or {}
            w.writerow([p['year'], p['start'], p['end'], f"{p['ret']:.6f}", f"{p['unlev']:.6f}", '' if p['index'] is None else f"{p['index']:.6f}",
                        f"{p['mdd']:.6f}", f"{p['exposure']:.4f}", f"{p['lev']:.4f}", f"{p['eb']:.4f}", f"{p['resid']:.6f}",
                        cr.get('n', ''), *(f"{cr[k]:.6f}" if cr else '' for k in ('median', 'lo', 'hi')),
                        fmt_codes(p['codes'], names), fmt_codes(p['codes'], names, sign=-1)])

    # ---- 四、涨跌波段（2009-11 路径，净值 ZIGZAG 反转）----
    values = [CAPITAL] + [r['eq'] for r in c0]
    piv = [max(0, k - 1) for k in zigzag(values, ZIGZAG)]   # values 比 curve 多一个初始资本点
    legs = []
    for a, b in zip(piv, piv[1:]):
        if b <= a:
            continue
        p = period(c0, pnl0, eb0, a, b, first=(a == 0))
        p['index'], p['index_end'] = index_ret(p['start'], p['end'])
        p['dir'] = '上涨' if p['ret'] >= ZIGZAG else '下跌' if p['ret'] <= -ZIGZAG else ('当前未完' if b == len(c0) - 1 else '起步震荡')
        p['industry'] = by_industry(p['codes'], ind)
        p['cross'] = cross_leg(curves, p['start'], p['end'])
        legs.append(p)
    with (EXP / 'legs.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['start', 'end', 'trading_days', 'direction', 'return', 'mdd_in_leg', 'holdings_unlevered', 'csi300', 'csi300_last_date',
                    'avg_exposure', 'avg_debt_ratio', 'eb_cap_days', 'cost_resid', 'cross_n', 'cross_median', 'cross_min', 'cross_max',
                    'top_contrib', 'top_detract', 'top_industries'])
        for p in legs:
            inds = sorted(p['industry'].items(), key=lambda kv: -abs(kv[1]))[:4]
            cr = p['cross'] or {}
            w.writerow([p['start'], p['end'], p['days'], p['dir'], f"{p['ret']:.6f}", f"{p['mdd']:.6f}", f"{p['unlev']:.6f}",
                        '' if p['index'] is None else f"{p['index']:.6f}",
                        p['index_end'], f"{p['exposure']:.4f}", f"{p['lev']:.4f}", f"{p['eb']:.4f}", f"{p['resid']:.6f}",
                        cr.get('n', ''), *(f"{cr[k]:.6f}" if cr else '' for k in ('median', 'lo', 'hi')),
                        fmt_codes(p['codes'], names, 5), fmt_codes(p['codes'], names, 5, -1),
                        '、'.join(f'{k} {v * 100:+.1f}%' for k, v in inds)])

    # ---- 四之二：≥ ZIGZAG 回撤的修复时间；股债上限各受限区间的净资产、持仓本身与沪深 300 ----
    drawdowns = []
    for p in legs:
        if p['dir'] == '下跌':
            i0 = next(i for i, r in enumerate(c0) if r['date'] == p['start'])
            i1 = next(i for i, r in enumerate(c0) if r['date'] == p['end'])
            rec = next((r['date'] for r in c0[i1:] if r['eq'] >= c0[i0]['eq']), None)
            gap = lambda a, b: (date.fromisoformat(b) - date.fromisoformat(a)).days if b else None
            drawdowns.append(dict(peak=p['start'], trough=p['end'], depth=-p['ret'], recovered=rec,
                                  days_from_peak=gap(p['start'], rec), days_from_trough=gap(p['end'], rec)))
    dates0 = [r['date'] for r in c0]
    eb_reads = []
    for a, b, n in eb_episodes(eb0):
        i0, i1 = max(0, bisect.bisect_left(dates0, a) - 1), bisect.bisect_right(dates0, b) - 1
        p = period(c0, pnl0, eb0, i0, i1, first=(i0 == 0))
        eb_reads.append(dict(start=a, end=b, days=n, ret=p['ret'], unlev=p['unlev'], index=index_ret(p['start'], p['end'])[0],
                             exposure=p['exposure']))
    res['drawdowns'], res['eb_reads'] = drawdowns, eb_reads

    # ---- 五、全期来源（2009-11 路径）----
    whole = period(c0, pnl0, eb0, 0, len(c0) - 1, first=True)
    money = whole['codes']
    pos_total = sum(v for v in rel0.values() if v > 0)
    top5_reg = reg[MAIN]['前五赢家'].split('/')
    top5_mine = [c for c, _v in sorted(rel0.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
    assert top5_mine == top5_reg, (top5_mine, top5_reg)
    with (EXP / 'codes.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['security_code', 'security_name', 'industry', 'contrib_rel', 'share_of_positive', 'pnl_over_capital'])
        for c, v in sorted(rel0.items(), key=lambda kv: -kv[1]):
            w.writerow([c, names.get(c, ''), ind.get(c, '未分类'), f'{v:.6f}', f'{v / pos_total:.6f}', f'{money.get(c, 0.0):.6f}'])
    ind_rel = by_industry(rel0, ind)
    span = (date.fromisoformat(c0[-1]['date']) - date.fromisoformat(c0[0]['date'])).days / 365.25
    prev, cost_rel = CAPITAL, 0.0          # 费用、利息与股息税的引擎尺（Σ 逐日 ÷ 前一日净资产），与逐票 pp 同单位
    for row in c0:
        cost_rel += (row['eq'] - prev - sum(pnl0.get(row['date'], {}).values())) / prev
        prev = row['eq']
    res['whole'] = dict(unlev_cagr=(1 + whole['unlev']) ** (1 / span) - 1, cost_rel=cost_rel, years=span, exposure=whole['exposure'],
                        eb_episodes=eb_episodes(eb0),
                        index_cagr=(lambda r, d: (1 + r) ** (365.25 / (date.fromisoformat(d) - date.fromisoformat(c0[0]['date'])).days) - 1)(
                            *index_ret(c0[0]['date'], c0[-1]['date'])),codes=len(rel0), winners=sum(v > 0 for v in rel0.values()), losers=sum(v < 0 for v in rel0.values()),
                        pos_total=pos_total, neg_total=sum(v for v in rel0.values() if v < 0),
                        top=[(c, names.get(c, ''), v, v / pos_total) for c, v in sorted(rel0.items(), key=lambda kv: -kv[1])[:15]],
                        bottom=[(c, names.get(c, ''), v) for c, v in sorted(rel0.items(), key=lambda kv: kv[1])[:10]],
                        industry=sorted(ind_rel.items(), key=lambda kv: -kv[1]))
    res['years'] = [{k: v for k, v in p.items() if k != 'codes'} | dict(top=fmt_codes(p['codes'], names), bottom=fmt_codes(p['codes'], names, sign=-1))
                    for p in years]
    res['legs'] = [{k: v for k, v in p.items() if k not in ('codes', 'industry')} | dict(top=fmt_codes(p['codes'], names, 5),
                   bottom=fmt_codes(p['codes'], names, 5, -1),
                   industry=sorted(p['industry'].items(), key=lambda kv: -abs(kv[1]))[:5]) for p in legs]
    (EXP / 'analysis.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')

    # ---- 报告 ----
    A, B = anchors[MAIN], anchors[SECOND]
    md += ['# 现行 BASE 长跑的分时段读数与收益来源（v4.235 在册 BASE，描述统计）', '',
           f"路径 {A['first']}～{A['last']}（14 个标准起点 summary 与在册逐字段一致，见 `reproduce.json`）；沪深 300 为价格指数，行情止于 {IDX_D[-1]}（* 表示只算到该日）。"
           '收益率读数只描述已过历史（§12.1），不作未来预期。', '',
           '## 一、长跑复利与回撤', '',
           '| 起点 | 期末倍数 | 全期 CAGR | 最大回撤（区间） | Calmar | Sharpe | 平均仓位 | 最低担保比例 | 剔除集 A：CAGR／最大回撤 |',
           '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for s, a in ((MAIN, A), (SECOND, B)):
        md.append(f"| {s} | {a['multiple']:.0f} 倍 | {a['cagr']:.2%} | {a['mdd']:.2%}（{a['mdd_range']}） | {a['calmar']:.2f} | {a['sharpe']:.2f} | "
                  f"{a['exposure']:.0%} | {a['min_margin']:.2f}（{a['min_margin_day']}） | {a['ex5_cagr']:.2%}／{a['ex5_mdd']:.2%}（{a['ex5_mdd_range']}） |")
    cx = cross
    md += ['', f"14 起点：全期 CAGR 中位 {cx['年化']['median']:.2%}（{cx['年化']['lo']:.2%}～{cx['年化']['hi']:.2%}），"
           f"最大回撤中位 {cx['最大回撤']['median']:.2%}（{cx['最大回撤']['lo']:.2%}～{cx['最大回撤']['hi']:.2%}）；"
           f"剔除集 A 后 CAGR 中位 {cx['年化']['ex5_median']:.2%}、最大回撤中位 {cx['最大回撤']['ex5_median']:.2%}。", '',
           '## 二、滚动 5 年（月末锚定）', '',
           f"2009-11 路径 {roll['n']} 个窗口（末日 {roll['first_end']}～{roll['last_end']}）：",
           '', '| 读数 | 最差 | P10 | P25 | 中位 | P75 | 最好 |', '| --- | --- | --- | --- | --- | --- | --- |',
           '| 窗口年化 | ' + ' | '.join(f"{roll['cagr'][k]:.1%}" for k in ('min', 'p10', 'p25', 'median', 'p75', 'max')) + ' |',
           '| 窗口内最大回撤 | ' + ' | '.join(f"{roll['mdd'][k]:.1%}" for k in ('min', 'p10', 'p25', 'median', 'p75', 'max')) + ' |', '',
           f"最差窗口 {roll['worst'][0]['start']}～{roll['worst'][0]['end']} 年化 {roll['worst'][0]['cagr']:.1%}；年化 < 20% 的窗口占 {roll['share_cagr_lt_20']:.0%}，"
           f"窗口回撤 ≥ 35% 的占 {roll['share_mdd_ge_35']:.0%}；无负收益窗口。14 起点（起点内取值后跨起点中位）：滚 5 中位 {cx['滚动5年年化中位']['median']:.2%}、"
           f"P25 {cx['滚动5年年化P25']['median']:.2%}、最差 {cx['滚动5年年化最差']['median']:.2%}、滚 5 回撤中位 {cx['滚动5年回撤中位']['median']:.2%}；"
           f"剔除集 A 后分别为 {cx['滚动5年年化中位']['ex5_median']:.2%}、{cx['滚动5年年化P25']['ex5_median']:.2%}、{cx['滚动5年年化最差']['ex5_median']:.2%}、"
           f"{cx['滚动5年回撤中位']['ex5_median']:.2%}。互不重叠 5 年块中位 {cx['互不重叠5年块中位']['median']:.2%}。", '',
           '## 三、逐年（2009-11 路径）', '',
           '| 年 | 策略 | 持仓本身 | 沪深300 | 年内回撤 | 平均仓位 | 股债受限日 | 14 起点同年中位［范围］ | 主要盈利 | 主要亏损 |',
           '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for p in years:
        cr = p['cross']
        crs = f"{cr['median']:+.1%}［{cr['lo']:+.1%}，{cr['hi']:+.1%}］{cr['pos']}/{cr['n']} 正" if cr else '—'
        md.append(f"| {p['year']} | {p['ret']:+.1%} | {p['unlev']:+.1%} | {pct(p['index'], last=p['index_end'], end=p['end'])} | {p['mdd']:.1%} | {p['exposure']:.0%} | {p['eb']:.0%} | {crs} | "
                  f"{fmt_codes(p['codes'], names)} | {fmt_codes(p['codes'], names, sign=-1)} |")
    md += ['', '「持仓本身」= 同一组持仓的时间加权收益；与「策略」之差 = 仓位高低（融资放大、股债上限减仓、闲置现金）与利息费用。'
           '主要盈利／亏损为逐日相对贡献按 Carino 链接到当年收益（各票合计 ＋ 费用利息 = 当年收益）。']
    md += ['', f'## 四、涨跌波段（2009-11 路径，净值 {ZIGZAG:.0%} 反转切分，下跌段即全部 ≥ {ZIGZAG:.0%} 的回撤）', '',
           '| 区间 | 方向 | 策略（段内最大回撤） | 持仓本身 | 沪深300 | 平均仓位 | 股债受限日 | 14 起点同区间中位［范围］ | 主要来源（链接贡献） | 主要拖累 | 行业 |',
           '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for p in legs:
        inds = sorted(p['industry'].items(), key=lambda kv: -abs(kv[1]))[:3]
        cr = p['cross']
        crs = f"{cr['median']:+.1%}［{cr['lo']:+.1%}，{cr['hi']:+.1%}］n={cr['n']}" if cr else '—'
        dd = f"（{p['mdd']:.1%}）" if p['mdd'] > abs(min(p['ret'], 0)) + 1e-9 else ''
        md.append(f"| {p['start']}～{p['end']} | {p['dir']} | {p['ret']:+.1%}{dd} | {p['unlev']:+.1%} | {pct(p['index'], last=p['index_end'], end=p['end'])} | "
                  f"{p['exposure']:.0%} | {p['eb']:.0%} | {crs} | "
                  f"{fmt_codes(p['codes'], names, 4)} | {fmt_codes(p['codes'], names, 3, -1)} | {'、'.join(f'{k} {v * 100:+.0f}%' for k, v in inds)} |")
    md += ['', f'≥ {ZIGZAG:.0%} 回撤的修复（净资产回到前高）：' + '；'.join(
        f"{d['peak']} 高点 −{d['depth']:.1%}（谷 {d['trough']}）→ {d['recovered'] or '未修复'}"
        + (f"，距高点 {d['days_from_peak']} 天、距谷 {d['days_from_trough']} 天" if d['recovered'] else '') for d in drawdowns) + '。',
           '', '股债总仓位上限受限区间（上限 30%）：' + '；'.join(
        f"{e['start']}～{e['end']}（{e['days']} 日）净资产 {e['ret']:+.1%}、持仓本身 {e['unlev']:+.1%}、沪深300 {pct(e['index'])}、平均仓位 {e['exposure']:.0%}"
        for e in eb_reads) + '。']
    W = res['whole']
    md += ['', '## 五、全期来源（2009-11 路径，引擎赢家尺：Σ 逐日盈亏 ÷ 前一日净资产）', '',
           f"交易过 {W['codes']} 只，{W['winners']} 只净贡献为正、{W['losers']} 只为负；正贡献合计 {W['pos_total'] * 100:.0f}pp，负贡献合计 {W['neg_total'] * 100:.0f}pp。", '',
           '| 排名 | 股票 | 贡献 | 占正贡献 |', '| --- | --- | --- | --- |']
    md += [f"| {k} | {n}（{c}） | {v * 100:+.0f}pp | {sh:.1%} |" for k, (c, n, v, sh) in enumerate(W['top'], 1)]
    md += ['', '最大拖累：' + '、'.join(f"{n} {v * 100:+.1f}pp" for c, n, v in W['bottom']), '',
           f"杠杆与成本：全期平均仓位 {W['exposure']:.0%}；同一组持仓不计杠杆的链式年化 {W['unlev_cagr']:.2%}（净资产 {A['cagr']:.2%}），"
           f"同期沪深 300 价格指数年化 {W['index_cagr']:.2%}（至 {IDX_D[-1]}）；费用、融资利息与股息税合计 {W['cost_rel'] * 100:.0f}pp（同一尺，约每年 {W['cost_rel'] / W['years'] * 100:.1f}pp）。", '',

           '行业：' + '、'.join(f'{k} {v * 100:+.0f}pp' for k, v in W['industry'][:10]) + '；最弱 '
           + '、'.join(f'{k} {v * 100:+.0f}pp' for k, v in W['industry'][-5:]), '']
    (EXP / 'report.md').write_text('\n'.join(md), encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
