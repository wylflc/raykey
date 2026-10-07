#!/usr/bin/env python3
"""实盘 09-30 持仓与现行 BASE 长跑期末持仓对照（描述统计，只读）。

长跑读 `exp_base_longrun_attrib_20261007/runs/` 的 14 起点逐日盈亏、净值与成交流水（不入库，重跑见该目录 README）；
实盘读 2026-09-30 发布批次的持仓跟踪、候选 P/V、名单分类、账户快照与独立估值登记。写 `end_holdings.csv`、
`compare.csv`、`risk.json`。

期末持仓：各代码最后一条逐日盈亏记录（包装只记非零盈亏）市值 > 0，且其后成交流水无卖出（按前收价清空的
那天盈亏为零、不留记录）；只数须与净值表期末 `positions` 相同。
"""
import csv
import glob
import json
import statistics
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
RUNS = ROOT / 'data/experiments/exp_base_longrun_attrib_20261007/runs'
AS_OF = '2026-09-30'
SINCE = '2012-01-01'   # 风险分布避开 2009-11 起步建仓期
CREDIT = 0.666         # 工作流程 §10.2 授信比例
MIN_WEIGHT = 0.005     # 对照表只列实盘权重或 14 起点中位权重 ≥ 0.5% 的代码


def read(path):
    with open(path, encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def quantile(values, p):
    values = sorted(values)
    k = (len(values) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def end_state(tag):
    curve = read(RUNS / f'{tag}_curve.csv')
    last = {}
    for row in read(RUNS / f'{tag}_daily_pnl.csv'):
        last[row['security_code']] = (row['date'], float(row['mv']))
    sells, names = {}, {}
    for row in read(RUNS / f'{tag}_tradelog.csv'):
        if row['security_name']:
            names[row['security_code']] = row['security_name']
        if row['action'] == '卖出':
            sells[row['security_code']] = max(sells.get(row['security_code'], ''), row['date'])
    held = {code: (day, mv) for code, (day, mv) in last.items() if mv > 0 and sells.get(code, '') <= day}
    end = curve[-1]
    assert len(held) == int(end['positions']), (tag, len(held), end['positions'])
    return end, held, names, curve


def risk(curve):
    rows = [r for r in curve if r['date'] >= SINCE]
    nav = [float(r['net_equity']) for r in rows]
    top1 = [float(r['top1_weight']) for r in rows]
    gross = [(n + float(r['debt']) - float(r['cash'])) / n for r, n in zip(rows, nav)]
    debt = [float(r['debt']) / n for r, n in zip(rows, nav)]
    margin = [float(r['margin_ratio']) for r in rows if r['margin_ratio'] != 'inf']
    share = lambda xs, t: round(sum(x >= t for x in xs) / len(xs), 4)
    return dict(days=len(rows),
                top1=dict(median=round(statistics.median(top1), 4), p90=round(quantile(top1, .9), 4),
                          max=round(max(top1), 4), share_ge_60=share(top1, .6), share_ge_70=share(top1, .7),
                          share_ge_76=share(top1, .76)),
                gross=dict(median=round(statistics.median(gross), 4), p90=round(quantile(gross, .9), 4),
                           max=round(max(gross), 4)),
                debt_over_credit_share=share(debt, CREDIT + 1e-9),
                margin_ratio=dict(min=round(min(margin), 3), p10=round(quantile(margin, .1), 3),
                                  median=round(statistics.median(margin), 3)))


def main():
    tags = sorted(Path(p).name.split('_')[0] for p in glob.glob(str(RUNS / '*_curve.csv')))
    assert len(tags) == 14, tags
    weights, names, risks, ends, held_rows = {}, {}, {}, {}, []
    for tag in tags:
        end, held, run_names, curve = end_state(tag)
        names.update(run_names)
        nav = float(end['net_equity'])
        ends[tag] = dict(end_date=end['date'], positions=int(end['positions']),
                         gross=round((nav + float(end['debt']) - float(end['cash'])) / nav, 4),
                         debt_over_nav=round(float(end['debt']) / nav, 4), top1=float(end['top1_weight']))
        risks[tag] = risk(curve)
        for code, (day, mv) in sorted(held.items(), key=lambda kv: -kv[1][1]):
            weights.setdefault(code, {})[tag] = mv / nav
            held_rows.append((tag, end['date'], code, mv / nav, day))

    snap = next(r for r in read(ROOT / 'data/processed/portfolio_account_snapshot.csv') if r['as_of'] == AS_OF)
    nav = float(snap['net_assets_cny'])
    live = {}
    for row in read(ROOT / 'data/processed/daily_holdings_tracking.csv'):
        assert row['as_of'] == AS_OF, row['as_of']
        live[row['security_code']] = int(row['current_shares']) * float(row['close']) / nav
        names[row['security_code']] = row['security_name']
    cands = {r['security_code']: r for r in read(ROOT / 'data/processed/daily_buy_candidates.csv')}
    assert {r['trade_date'] for r in cands.values()} == {AS_OF}
    triage = {}
    for r in read(ROOT / 'data/processed/a_share_attention_triage.csv'):
        triage[r['security_code']] = r['attention_class']
        names[r['security_code']] = names.get(r['security_code']) or r['security_name']
    indep = {r['security_code']: r for r in read(ROOT / 'data/processed/independent_valuations.csv')
             if r['market'] == 'A' and r['status'] == 'current'}

    with (EXP / 'end_holdings.csv').open('w', newline='', encoding='utf-8') as handle:
        out = csv.writer(handle)
        out.writerow(['start', 'end_date', 'security_code', 'security_name', 'weight_of_nav', 'last_mark_date'])
        out.writerows((tag, day_end, code, names.get(code, ''), f'{w:.4f}', day) for tag, day_end, code, w, day in held_rows)

    base = 'BASE20091101'
    series = {code: [weights.get(code, {}).get(t, 0.0) for t in tags] for code in set(weights) | set(live)}
    table = []
    for code, w in series.items():
        if live.get(code, 0.0) < MIN_WEIGHT and statistics.median(w) < MIN_WEIGHT:
            continue
        c = cands.get(code, {})
        table.append(dict(security_code=code, security_name=names.get(code, ''),
                          live_weight=round(live.get(code, 0.0), 4),
                          longrun_2009_weight=round(weights.get(code, {}).get(base, 0.0), 4),
                          longrun_median=round(statistics.median(w), 4), longrun_min=round(min(w), 4),
                          longrun_max=round(max(w), 4), longrun_starts_held=sum(x > 0 for x in w),
                          attention_class=triage.get(code, ''), model_pv=c.get('model_pv', ''), hold_pv=c.get('hold_pv', ''),
                          independent_pv=indep.get(code, {}).get('pv', ''),
                          independent_verdict=indep.get(code, {}).get('verdict', '')))
    table.sort(key=lambda r: -(r['live_weight'] + r['longrun_median']))
    with (EXP / 'compare.csv').open('w', newline='', encoding='utf-8') as handle:
        out = csv.DictWriter(handle, fieldnames=list(table[0]))
        out.writeheader()
        out.writerows(table)

    live_state = dict(as_of=AS_OF, positions=int(snap['position_count']),
                      gross=round(float(snap['holdings_market_value_cny']) / nav, 4),
                      debt_over_nav=round(float(snap['margin_debt_cny']) / nav, 4),
                      guarantee_ratio=round(float(snap['guarantee_ratio_pct']) / 100, 3),
                      top1=round(float(snap['top_position_weight_pct']) / 100, 4))
    (EXP / 'risk.json').write_text(json.dumps(dict(since=SINCE, credit_ratio=CREDIT, live=live_state, longrun_end=ends,
                                                   longrun_daily=risks), ensure_ascii=False, indent=1) + '\n',
                                   encoding='utf-8')
    for r in table:
        print(r)
    print(json.dumps(dict(live=live_state, end_2009=ends[base], daily_2009=risks[base]), ensure_ascii=False))


if __name__ == '__main__':
    main()
