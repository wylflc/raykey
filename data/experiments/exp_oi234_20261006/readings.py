"""OI-234 读数（preregister.md 第 1～8 条）：回踩加仓 P（δ 0／3%／6%）、偏离减仓 D（K 1.15／1.25／1.35）、PD（δ 3%＋K 1.25）对 CONTROL（现行 BASE）。

    python3 readings.py     # → readings.json、readings.md、case_<臂>_vs_CONTROL.md
"""
import bisect
import csv
import glob
import json
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts/experimental'))
sys.path.insert(0, str(EXP))
import backtest_valuation_strategy as bt  # noqa: E402
import build_historical_valuation_bands as bhv  # noqa: E402
import opportunity_trap_audit as audit  # noqa: E402
import sweep_backtest_configs as sw  # noqa: E402
from delta_attribution import load_contrib  # noqa: E402
from moat_param_lab import total_return_index  # noqa: E402
from run import A_SET, ARMS, NEW, REF  # noqa: E402

W5 = sw.WIN5_KEY
STARTS = sw.DEFAULT_STARTS
ANCHOR = sw.EX5_ANCHOR_START
STATES = ROOT / 'data/processed/a_share_daily_states_adopted.csv'
DOSE = (('P', ('P0', 'P3', 'P6')), ('D', ('D115', 'D125', 'D135')))
CASE_ARMS = ('PD', 'P3', 'D125')
CLAUSE4 = (('滚动5年年化中位', 0, +1), ('滚动5年年化P25', 0, +1), ('滚动5年年化最差', 0, +1), ('滚动5年回撤中位', 0, -1),
           ('滚动5年Calmar中位', 1, +1), ('滚动5年Sharpe中位', 1, +1), ('滚动5年为负的窗口占比', 0, -1), ('年化', 0, +1),
           ('最大回撤', 0, -1), ('Calmar', 1, +1), ('Sharpe', 1, +1), ('互不重叠5年块中位', 0, +1), ('滚动3年年化中位', 0, +1),
           ('滚动3年回撤中位', 0, -1), ('逐年收益中位', 0, +1), ('逐年最差', 0, +1))
CONC = ('持仓数中位', '单票权重中位', '单票权重P90', '单票权重最大', '前三权重中位', '单票超60%天数占比', '平均仓位')
DEV_TAG = '偏离MA20≥'


def load(path):
    sw.set_market(sw.scan_market(path))
    groups, _orders, failed, *_ = sw.load_scan(path)
    assert not any(failed.values()), (path, failed)
    return groups


FULL = load(EXP / 'sweep_full.txt')['']
EXA = load(EXP / 'sweep_A.txt')[sw.EX5_PREFIX]
EXU = {a: load(EXP / 'u' / f'{a}.txt')[sw.EX5_PREFIX] for a in NEW}


def pm(grp, arm, key, ref=REF):
    return sw._paired_median(grp, arm, key, ref=ref)


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def share(xs, cond):
    xs = [x for x in xs if x is not None]
    return sum(1 for x in xs if cond(x)) / len(xs) if xs else None


def tag(arm, start):
    return sw.summary_tag(arm + 'full', start, '')


def vs_base(arm):
    flag, reasons, _ = sw.reading_flags(FULL, EXA, arm, ref=REF)
    u = EXU[arm]
    clause = {k: pm(u, arm, k) for k, _r, _s in CLAUSE4}
    worst = []
    for k, ratio, sign in CLAUSE4:
        v = sign * clause[k]
        lo, band = (-0.005, -0.033) if ratio else (-0.0015, -0.01)
        worst.append('ok' if v >= lo else 'band' if v >= band else 'bad')
    return dict(flag=flag, reasons=reasons, main=[pm(FULL, arm, W5), pm(EXA, arm, W5), pm(u, arm, W5)],
                cagr=[pm(FULL, arm, '年化'), pm(EXA, arm, '年化'), pm(u, arm, '年化')], mdd=[pm(FULL, arm, '最大回撤'), pm(EXA, arm, '最大回撤')],
                better=sum(FULL[arm][s]['年化'] > FULL[REF][s]['年化'] for s in STARTS), u_clause4=clause,
                u_all_good=worst.count('bad') == 0 and worst.count('band') <= 1,
                conc={k: pm(FULL, arm, k) for k in CONC})


def levels(arm):
    col = lambda key: med([FULL[arm][s][key] for s in STARTS])
    return dict(cagr=col('年化'), mdd=col('最大回撤'), a2009=FULL[arm]['2009-11-01']['年化'], a2011=FULL[arm]['2011-11-01']['年化'],
                mdd2009=FULL[arm]['2009-11-01']['最大回撤'])


def ledger(arm, start):
    with (EXP / 'ledgers' / f'{tag(arm, start)}.csv').open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def trades(arm, start):
    path = next(iter(glob.glob(str(EXP / 'artifacts' / f'*_{tag(arm, start)}_trades.csv'))))
    with open(path, newline='', encoding='utf-8') as f:
        return path, list(csv.DictReader(f))


class Series:
    """含分红再投总回报指数，按交易日前移。"""

    def __init__(self, series):
        self.s = series

    def fwd(self, code, day, k):
        if code not in self.s:
            return None
        days, tr = self.s[code]
        i = bisect.bisect_right(days, day) - 1
        if i < 0 or i + k >= len(days):
            return None
        return tr[days[i + k]] / tr[days[i]] - 1


def accounts(S, closes, mas):
    """加仓账（CONTROL 与 P 臂）与偏离减仓账（D 臂、PD）。"""
    def sig_ratio(code, exe):
        days = closes.get(code)
        if not days:
            return None
        keys = sorted(days)
        i = bisect.bisect_left(keys, exe) - 1
        if i < 0:
            return None
        sig = keys[i]
        m = mas.get(code, {}).get(sig, {}).get(20)
        return days[sig] / m if m else None

    out = {}
    for arm in ARMS:
        adds_n, trims_n, trims_amt = [], [], []
        uniq_add, uniq_trim = {}, {}
        for s in STARTS:
            rows = ledger(arm, s)
            adds = [r for r in rows if r['reason'] == '定投加仓']
            trims = [r for r in rows if r['reason'].startswith(DEV_TAG)]
            adds_n.append(len(adds))
            trims_n.append(len(trims))
            trims_amt.append(sum(float(r['amount']) for r in trims))
            for r in adds:
                k = (r['security_code'].zfill(6), r['date'])
                if k not in uniq_add:
                    uniq_add[k] = sig_ratio(*k)
            for r in trims:
                uniq_trim.setdefault((r['security_code'].zfill(6), r['date']), True)
        ratios = [v for v in uniq_add.values() if v is not None]
        groups = {}
        for name, cond in (('收盘≤MA20×1.03', lambda v: v <= 1.03), ('收盘>MA20×1.03', lambda v: v > 1.03)):
            ks = [k for k, v in uniq_add.items() if v is not None and cond(v)]
            f20 = [S.fwd(c, d, 20) for c, d in ks]
            f60 = [S.fwd(c, d, 60) for c, d in ks]
            groups[name] = dict(n=len(ks), f20=med(f20), f20_neg=share(f20, lambda v: v < 0), f60=med(f60), f60_neg=share(f60, lambda v: v < 0))
        t20 = [S.fwd(c, d, 20) for c, d in uniq_trim]
        t60 = [S.fwd(c, d, 60) for c, d in uniq_trim]
        out[arm] = dict(adds=med(adds_n), add_unique=len(uniq_add),
                        add_over={f'>{x:.2f}': share(ratios, lambda v, x=x: v > x) for x in (1.00, 1.03, 1.06)},
                        add_groups=groups, trims=med(trims_n), trims_amount=med(trims_amt), trim_unique=len(uniq_trim),
                        trim_f20=med(t20), trim_f20_neg=share(t20, lambda v: v < 0), trim_f60=med(t60), trim_f60_neg=share(t60, lambda v: v < 0))
    return out


def clause13(rows, cases, last_month):
    out = {}
    for arm in ARMS:
        per = {}
        for s in STARTS:
            _p, cyc = trades(arm, s)
            per[s] = [dict(code=c['security_code'].zfill(6), entry=c['entry_date'], exit=c['exit_date'], invested=float(c['invested'] or 0),
                           contrib=float(c['contrib'] or 0)) for c in cyc]
        res = audit.strategy_readings(per, rows, cases, last_month)
        out[arm] = dict(by_label=res['by_label'], cases=res['cases'])
    return out


def top3_share(arm):
    base, _ = load_contrib(Path(trades(REF, ANCHOR)[0]))
    cand, _ = load_contrib(Path(trades(arm, ANCHOR)[0]))
    diff = {c: cand.get(c, 0.0) - base.get(c, 0.0) for c in set(base) | set(cand)}
    total = sum(diff.values())
    top = sorted(diff.items(), key=lambda kv: -abs(kv[1]))[:3]
    return dict(total=total, top3=[(c, v) for c, v in top], share=(sum(v for _, v in top) / total) if total else None)


def main():
    rows, eps = audit.load_answer_key(audit.LABELS)
    cases = audit.load_cases(audit.CASES, eps)
    last_month = max(r['month'] for r in rows)
    codes = set()
    for arm in ARMS:
        for s in STARTS:
            codes |= {r['security_code'].zfill(6) for r in ledger(arm, s)}
    actions = bhv.load_actions()
    series = {}
    for code in codes:
        prices = bhv.load_ohlcv(code)
        if prices:
            series[code] = ([d for d, _ in prices], total_return_index(prices, actions.get(code, [])))
    closes = bt.load_prices(codes)
    ev = bt.load_actions()
    mas = {c: bt.adjusted_moving_averages(closes[c], ev.get(c, {}), (20,)) for c in codes if c in closes}
    res = dict(ref=REF, A=A_SET, levels={a: levels(a) for a in ARMS}, vs_base={a: vs_base(a) for a in NEW},
               dose={k: {a: dict(main=pm(FULL, a, W5), cagr=pm(FULL, a, '年化'), main_a=pm(EXA, a, W5), cagr_a=pm(EXA, a, '年化')) for a in arms}
                     for k, arms in DOSE},
               accounts=accounts(Series(series), closes, mas), clause13=clause13(rows, cases, last_month), cases={},
               family=dict(new=len(NEW), related='§12.148 加仓闸门、archive §12.40 偏离停投、§12.290 让位换仓源'))
    for arm in CASE_ARMS:
        out = EXP / f'case_{arm}_vs_{REF}.md'
        subprocess.run([sys.executable, str(ROOT / 'scripts/experimental/case_attribution.py'),
                        '--base', f'{REF}={trades(REF, ANCHOR)[0]}', '--arm', f'{arm}={trades(arm, ANCHOR)[0]}',
                        '--base-states', str(STATES), '--arm-states', str(STATES), '--out', str(out)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        table = [ln for ln in out.read_text(encoding='utf-8').splitlines() if ln.startswith('| ') and 'pp |' in ln][:10]
        res['cases'][arm] = dict(top3=top3_share(arm), table=table)
    (EXP / 'readings.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')
    write_md(res)


def pp(v):
    return '—' if v is None else f'{v * 100:+.2f}'


def pct(v):
    return '—' if v is None else f'{v:.1%}'


def write_md(res):
    L = res['levels']
    md = ['# OI-234 回踩加仓与偏离减仓读数（对 CONTROL＝现行 BASE，14 起点，参考）', '',
          f"CONTROL 年化中位 {L[REF]['cagr']:.2%}、最大回撤中位 {L[REF]['mdd']:.2%}；长跑 2009-11 {L[REF]['a2009']:.2%}、2011-11 {L[REF]['a2011']:.2%}。", '',
          '## 1. 参考读数（pp；全样本／A／U）', '',
          '| 臂 | 标记 | 主读数 | 复利 | 全期回撤 Δ 全／A | 复利胜出起点 | U 第 4 款 | 年化中位 | 回撤中位 |', '|---|---|---|---|---|---|---|---|---|']
    for a in NEW:
        v = res['vs_base'][a]
        md.append(f"| {a} | {v['flag']} | {'／'.join(pp(x) for x in v['main'])} | {'／'.join(pp(x) for x in v['cagr'])} | "
                  f"{'／'.join(pp(x) for x in v['mdd'])} | {v['better']}/14 | {'去赢家全面优秀' if v['u_all_good'] else '—'} | "
                  f"{L[a]['cagr']:.2%} | {L[a]['mdd']:.2%} |")
    md += ['', '## 2. 剂量（全样本主读数／复利；A 主读数／复利）', '']
    for k, arms in DOSE:
        md.append(f"- {k}：" + '；'.join(f"{a} {pp(d['main'])}／{pp(d['cagr'])}（A {pp(d['main_a'])}／{pp(d['cagr_a'])}）" for a, d in res['dose'][k].items()))
    acc = res['accounts']
    md += ['', '## 3. 加仓账（逐起点中位；逐笔按（代码, 成交日）去重）', '',
           '| 臂 | 加仓笔数 | 信号日收盘 >MA20×1.00／1.03／1.06 的占比 | ≤1.03 组 20／60 日回报（为负占比） | >1.03 组 20／60 日回报（为负占比） |', '|---|---|---|---|---|']
    for a in ('CONTROL', 'P0', 'P3', 'P6', 'PD'):
        x = acc[a]
        g1, g2 = x['add_groups']['收盘≤MA20×1.03'], x['add_groups']['收盘>MA20×1.03']
        md.append(f"| {a} | {x['adds']:.0f} | {'／'.join(pct(v) for v in x['add_over'].values())} | "
                  f"{pct(g1['f20'])}／{pct(g1['f60'])}（{pct(g1['f20_neg'])}／{pct(g1['f60_neg'])}，n={g1['n']}） | "
                  f"{pct(g2['f20'])}／{pct(g2['f60'])}（{pct(g2['f20_neg'])}／{pct(g2['f60_neg'])}，n={g2['n']}） |")
    md += ['', '## 4. 偏离减仓账', '', '| 臂 | 减仓笔数（中位） | 金额中位（万） | 去重笔数 | 其后 20／60 日回报中位 | 为负占比 20／60 |', '|---|---|---|---|---|---|']
    for a in ('D115', 'D125', 'D135', 'PD'):
        x = acc[a]
        md.append(f"| {a} | {x['trims']:.0f} | {x['trims_amount'] / 1e4:.0f} | {x['trim_unique']} | {pct(x['trim_f20'])}／{pct(x['trim_f60'])} | "
                  f"{pct(x['trim_f20_neg'])}／{pct(x['trim_f60_neg'])} |")
    md += ['', '## 5. 集中度（全样本配对差中位）', '']
    for a in NEW:
        md.append(f"- {a}：" + '；'.join(f"{k} {res['vs_base'][a]['conc'][k]:+.4f}" for k in CONC))
    md += ['', '## 6. 第 13 款（建仓月标签：周期数／投入占比／贡献，逐起点中位）', '']
    for a in ARMS:
        bl = res['clause13'][a]['by_label']
        md.append(f"- {a}：" + '；'.join(f"{k} {v['cycles']:.0f}／{v['invested_share']:.1%}／{v['contrib']:+.3f}" for k, v in sorted(bl.items())))
    md += ['', '## 7. 第 11 款（锚点 2011-11-01）', '']
    for a, c in res['cases'].items():
        t = c['top3']
        md.append(f"- {a} 对 CONTROL：贡献差合计 {t['total']:+.3f}，前三 " + '、'.join(f"{code} {v:+.3f}" for code, v in t['top3'])
                  + (f"，占比 {t['share']:.0%}" if t['share'] is not None else '') + f"；明细 `case_{a}_vs_CONTROL.md`")
    md += ['', f"## 8. 第 12 款：本批新增 {res['family']['new']} 臂；同族旧实验 {res['family']['related']}。"]
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
