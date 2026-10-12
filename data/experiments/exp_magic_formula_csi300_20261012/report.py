#!/usr/bin/env python3
"""把 `magic_formula_backtest.py` 的产物排成读数表（只读 results.json 与同目录 CSV，不重算）。

    python3 data/experiments/exp_magic_formula_csi300_20261012/report.py > data/experiments/exp_magic_formula_csi300_20261012/report.txt
"""
import csv
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
R = json.loads((EXP / "results.json").read_text(encoding="utf-8"))
res, pairs = R["results"], R["pairs"]
pct = lambda v: "" if v is None or v != v else f"{100 * v:.1f}%"

print(f"数据末端 {R['calendar_end']}；首个信号日 {R['first_signal']}，首个成交日 {R['first_execution']}，末次信号日 {R['last_signal']}；"
      f"工作流程宇宙各臂起点 {R['workflow_start']}；除权基数异常 {R['price_anomalies']}\n")

print("【全期】臂 | 起 | 期末净值 | 年化 | 最大回撤（区间） | 波动 | Sharpe | 年均单边换手 | 年费用 | 平均持仓")
for arm, r in res.items():
    print(f"{arm:13s} {r['start']} {r['final']:8.2f} {pct(r['cagr']):>7s} {pct(r['max_drawdown']):>7s} "
          f"({r['drawdown_from']}～{r['drawdown_to']}) {pct(r['vol']):>6s} {r['sharpe']:5.2f} "
          f"{r.get('turnover_per_year', float('nan')):5.2f} {pct(r.get('cost_per_year')):>6s} {r.get('avg_holdings', float('nan')):6.1f}")

print(f"\n【共同区间 {R['workflow_start']} 起】臂 | 年化 | 最大回撤")
for arm, r in res.items():
    c = r.get("common") or (r if arm.startswith("W_") else None)
    if c:
        print(f"{arm:13s} {pct(c['cagr']):>7s} {pct(c['max_drawdown']):>7s}")

arms = [a for a in ("MF30", "H00300", "INDEX_000300", "CW300", "EW300", "EW_ELIG", "MF30_Y", "MF30_T", "EY30", "ROC30") if a in res]
years = sorted(res["MF30"]["yearly"])
print("\n【逐年收益】" + " | ".join(["年"] + arms))
for y in years:
    print(y + " " + " ".join(f"{pct(res[a]['yearly'].get(y)):>8s}" for a in arms))

w_arms = [a for a in ("W_PV", "W_MF", "W_PVMF", "W_EW", "W_PV_ALL", "MF30", "H00300") if a in res]
w_years = sorted(res["W_EW"]["yearly"]) if "W_EW" in res else []
print("\n【逐年收益·工作流程宇宙】" + " | ".join(["年"] + w_arms))
for y in w_years:
    print(y + " " + " ".join(f"{pct(res[a]['yearly'].get(y)):>8s}" for a in w_arms))

print("\n【互不重叠 5 年块年化】")
for arm in ("MF30", "H00300", "CW300", "EW_ELIG", "W_PV", "W_MF", "W_PVMF", "W_EW"):
    if arm in res:
        print(f"{arm:8s} " + "  ".join(f"{b['start'][:7]}～{b['end'][:7]} {pct(b['cagr'])}" for b in res[arm]["blocks"]))

print("\n【逐年配对差】对 | 为正年数／年数 | 中位")
for name, p in pairs.items():
    print(f"{name:16s} {p['positive']:2d}/{p['n']:2d}  {pct(p['median'])}")

overlap = list(csv.DictReader((EXP / "workflow_overlap.csv").open(encoding="utf-8")))
if overlap:
    share = [int(r["pv_mf_overlap"]) / int(r["n"]) for r in overlap]
    corr = [float(r["rank_corr"]) for r in overlap]
    print(f"\n【P/V 与神奇公式的重合】{len(overlap)} 个季末：入选名单重合占比均值 {pct(sum(share) / len(share))}"
          f"（最低 {pct(min(share))}，最高 {pct(max(share))}）；全体名次相关均值 {sum(corr) / len(corr):.2f}；"
          f"合资格只数 {overlap[0]['eligible']}→{overlap[-1]['eligible']}，每期持有 {overlap[0]['n']}→{overlap[-1]['n']} 只")


def show(name, codes=None, top=30):
    path = EXP / name
    if not path.exists():
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    print(f"\n【{name}】共 {len(rows)} 只；名次 | 代码 | 名称 | 盈利收益率 | 资本回报率 | 两项名次 | P/V | EBIT 亿 | EV 亿")
    for r in rows:
        if (codes and r["security_code"] in codes) or (not codes and int(r["position"]) <= top):
            print(f"{int(r['position']):4d} {r['security_code']} {r['security_name']:8s} {pct(float(r['ey'])):>7s} {pct(float(r['roc'])):>8s} "
                  f"{r['rank_ey']:>4s}+{r['rank_roc']:<4s} {r['pv']:>7s} {float(r['ebit_yi']):9.1f} {float(r['ev_yi']):10.1f}")


FOCUS = {"000651", "603529", "600970", "920599", "834599", "601717", "600690", "600600", "601009", "601838", "603279", "600036"}
show("latest_rank_csi300.csv")
show("latest_rank_csi300.csv", FOCUS)
show("latest_rank_workflow.csv", top=25)
show("current_pool_crosscheck.csv", top=25)
show("current_pool_crosscheck.csv", FOCUS)
