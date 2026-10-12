"""不设单票上限（CNONE）对现行 BASE：两个长跑锚点的逐代码对照（runs/ 的逐日逐代码盈亏、净值曲线与成交流水）。

    python3 analyze.py     # → anchor_compare.json，并打印摘要
"""
import collections
import csv
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
RUNS = EXP / 'runs'
CAP = 0.60
with (ROOT / 'data/raw/financials/2026-06-30.csv').open(encoding='utf-8-sig') as fh:      # 成交流水里部分代码无名称
    PANEL_NAMES = {r['security_code'].zfill(6): r['security_name'] for r in csv.DictReader(fh)}


def load(tag):
    pnl = list(csv.DictReader((RUNS / f'{tag}_daily_pnl.csv').open(encoding='utf-8')))
    curve = list(csv.DictReader((RUNS / f'{tag}_curve.csv').open(encoding='utf-8')))
    trades = list(csv.DictReader((RUNS / f'{tag}_tradelog.csv').open(encoding='utf-8')))
    return pnl, curve, trades


def profile(tag):
    pnl, curve, trades = load(tag)
    eq = {r['date']: float(r['net_equity']) for r in curve}
    names = {t['security_code']: t['security_name'] or PANEL_NAMES.get(t['security_code'], t['security_code']) for t in trades}
    contrib, maxw, over_days, last = collections.Counter(), {}, collections.Counter(), {}
    weight = {}
    for r in pnl:
        code, day = r['security_code'], r['date']
        e_prev, mv = float(r['eq_prev']), float(r['mv'])
        contrib[code] += float(r['pnl']) / e_prev if e_prev else 0.0
        w = mv / eq[day] if eq.get(day) else 0.0
        weight[(code, day)] = w
        if w > maxw.get(code, (0, ''))[0]:
            maxw[code] = (w, day)
        if w >= CAP:
            over_days[code] += 1
        last[code] = (day, w)
    days = [r['date'] for r in curve]
    prev_day = {d: days[i - 1] for i, d in enumerate(days) if i}
    over_buys = collections.defaultdict(lambda: [0, 0.0, '', ''])     # 买入前一日权重已 ≥ 60% 的加仓：笔数、金额、首日、末日
    for t in trades:
        if t['action'] != '买入':
            continue
        w0 = weight.get((t['security_code'], prev_day.get(t['date'], '')), 0.0)
        if w0 >= CAP:
            b = over_buys[t['security_code']]
            b[0] += 1
            b[1] += float(t['amount'])
            b[2] = b[2] or t['date']
            b[3] = t['date']
    end_day = days[-1]
    recent = set(days[-20:])     # 当日盈亏为 0 的代码不落行（部分代码行情止于 2026-08-07），期末持仓取最近 20 个净值日内的末条记录
    end = {c: round(w, 4) for c, (d, w) in last.items() if d in recent and w > 0.001}
    top1 = [float(r['top1_weight']) for r in curve if float(r['top1_weight']) > 0]
    return dict(tag=tag, final_equity=eq[end_day], names=names, contrib=dict(contrib), maxw=maxw, over_days=dict(over_days),
                over_buys={c: v for c, v in over_buys.items()}, end=end, end_day=end_day,
                top1_days_over={str(x): sum(w >= x for w in top1) / len(top1) for x in (0.6, 0.8, 1.0, 1.2)},
                min_margin=min((float(r['margin_ratio']), r['date']) for r in curve if float(r['debt']) > 0),
                buys=sum(t['action'] == '买入' for t in trades), sells=sum(t['action'] != '买入' for t in trades))


out = {}
for start in ('20111101', '20091101'):
    b, c = profile('BASE' + start), profile('CNONE' + start)
    names = {**b['names'], **c['names']}
    codes = sorted(set(b['contrib']) | set(c['contrib']), key=lambda k: c['contrib'].get(k, 0) - b['contrib'].get(k, 0))
    rows = [dict(code=k, name=names.get(k, ''), base=round(100 * b['contrib'].get(k, 0), 1), cnone=round(100 * c['contrib'].get(k, 0), 1),
                 diff=round(100 * (c['contrib'].get(k, 0) - b['contrib'].get(k, 0)), 1),
                 base_maxw=round(100 * b['maxw'].get(k, (0, ''))[0], 1), cnone_maxw=round(100 * c['maxw'].get(k, (0, ''))[0], 1),
                 cnone_maxw_day=c['maxw'].get(k, (0, ''))[1], cnone_over_days=c['over_days'].get(k, 0), base_over_days=b['over_days'].get(k, 0),
                 cnone_over_buys=c['over_buys'].get(k, [0, 0, '', ''])) for k in codes]
    out[start] = dict(base={k: b[k] for k in ('final_equity', 'end', 'end_day', 'top1_days_over', 'min_margin', 'buys', 'sells')},
                      cnone={k: c[k] for k in ('final_equity', 'end', 'end_day', 'top1_days_over', 'min_margin', 'buys', 'sells')},
                      base_over_buys=b['over_buys'], codes=rows, names=names)
    print(f"=== 起点 {start}：期末净资产 BASE {b['final_equity'] / 1e8:.2f} 亿／CNONE {c['final_equity'] / 1e8:.2f} 亿；"
          f"买入笔数 {b['buys']}／{c['buys']}；最低担保比例 {b['min_margin']}／{c['min_margin']}")
    print('  最大单票权重超线天数占比 BASE', b['top1_days_over'], 'CNONE', c['top1_days_over'])
    print('  BASE 越线后买入（应为空）', b['over_buys'])
    print('  期末持仓 BASE', {names.get(k, k): v for k, v in sorted(b['end'].items(), key=lambda x: -x[1])})
    print('  期末持仓 CNONE', {names.get(k, k): v for k, v in sorted(c['end'].items(), key=lambda x: -x[1])})
    print('  CNONE 权重 ≥60% 之后的加仓：')
    for r in sorted(rows, key=lambda r: -r['cnone_over_buys'][1]):
        n, amt, d0, d1 = r['cnone_over_buys']
        if n:
            print(f"    {r['code']} {r['name']}: {n} 笔 {amt / 1e8:.2f} 亿 {d0}～{d1}｜最大权重 BASE {r['base_maxw']}% → CNONE {r['cnone_maxw']}%（{r['cnone_maxw_day']}）"
                  f"｜贡献 {r['base']} → {r['cnone']}（{r['diff']:+}）")
    print('  贡献差最大的十只（累计「盈亏÷前一日净资产」，pp）：')
    for r in rows[:5] + rows[-5:]:
        print(f"    {r['code']} {r['name']}: BASE {r['base']} → CNONE {r['cnone']}（{r['diff']:+}）｜最大权重 {r['base_maxw']}% → {r['cnone_maxw']}%")
(EXP / 'anchor_compare.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
