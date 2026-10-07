#!/usr/bin/env python3
"""按工作流程 §6.10 把逐家复核结果写回烟蒂池：复核烟蒂价值、闸门、状态，并登记 §6.9 独立估值。

输入：本目录 `data/<代码>_<名称>.json`（分析代理按 brief.md 摘录），平安银行取 `exp_independent_pab_20261007` 的评审；
池表与粗筛读数取 `data/processed/cigar_butt_pool.csv`、`data/interim/cigar_butt_screen.csv`。
输出：`review_results.csv`（逐家计算），`--apply` 时改池表、追加独立估值登记与决策日志。
治理清单只列出、不自动判：`--governance-fail <代码,...>` 指定复核判为不过的公司。
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
import time
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from screen_cigar_butts import CANDIDATE_MAX, FOCUS_MAX, POOL, POOL_FIELDS, SCREEN, bank_coe  # noqa: E402

TODAY = "2026-10-07"
BATCH = "iv20261007_cigar"
REPORT = "docs/reports/cigar_butt_review_2026-10-07.zh.md"
NORMAL_RATES = dict(normal_corporate_yi=0.0035, normal_mortgage_yi=0.0015, normal_credit_card_yi=0.05, normal_other_retail_yi=0.025)
PINGAN = dict(  # exp_independent_pab_20261007：2026 年半年报，页码见该评审全文
    code="000001", name="平安银行", price=11.57, common_bvps=23.88, shares_yi=194.06, cet1_pct=9.32, cet1_req_pct=7.75,
    npl_yi=362.7, special_mention_yi=631.8, restructured_yi=419.7, restructured_normal_yi=139.9, reserve_yi=795.63,
    coverage_pct=219.58, provision_to_loans_pct=2.30, loans_yi=362.7 / 0.0105, normal_corporate_yi=1941.2 + 14238.7,
    normal_mortgage_yi=3628.3, normal_credit_card_yi=3936.1, normal_other_retail_yi=4551.9 + 4941.0,
    roe_2016_2025=[None] * 7 + [11.38, 10.08, 9.15], roe_h1_2026_annualized=10.44, one_off_roe_pp_2025=1.1,
    governance=[], review_id="iv20261007_pab:000001", pv="0.803", verdict="温和低估",
    falsifiers=["2026 年归母净利 < 426.3 亿或加权 ROE < 8.5%", "单季净息差 < 1.72%", "逾期 90 天以上占比 > 0.85% 或关注率 > 2.0%"],
    next_check="2026 三季报（10 月下旬）")


def f(value) -> float | None:
    try:
        return float(value) if value not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def bank_review(d: dict, pool_row: dict) -> dict:
    out = dict(kind="D", notes=[])
    bvps, shares, price = f(d.get("common_bvps")), f(d.get("shares_yi")), f(d.get("price")) or f(pool_row["price"])
    parts = [f(d.get(k)) for k in ("npl_yi", "special_mention_yi", "reserve_yi")]
    normals = {k: f(d.get(k)) for k in NORMAL_RATES}
    if normals["normal_credit_card_yi"] is None and None not in [v for k, v in normals.items() if k != "normal_credit_card_yi"]:
        normals["normal_credit_card_yi"] = 0.0                  # 未单列的信用卡含在其他零售里，按其他零售损失率计
        out["notes"].append("信用卡未单列，含在其他零售")
    restructured_normal = f(d.get("restructured_normal_yi"))
    if restructured_normal is None and f(d.get("restructured_yi")) is not None:
        restructured_normal = f(d.get("restructured_yi")) / 3
        out["notes"].append("仍列正常类的重组贷款按三分之一假设")
    if None in parts or None in normals.values() or not bvps or not shares:
        stressed = f(d.get("stress_bvps_prudent"))
        out["notes"].append("分项不全，压力后每股净资产取代理审慎档")
        loss = shortfall = None
    else:
        npl, sm, reserve = parts
        loss = npl * 0.60 + sm * 0.25 + (restructured_normal or 0.0) * 0.10 + sum(v * NORMAL_RATES[k] for k, v in normals.items())
        shortfall = max(0.0, loss - reserve)
        stressed = bvps - shortfall * 0.75 / shares
    roes = [f(x) for x in (d.get("roe_2016_2025") or [])][-3:]
    one_off = f(d.get("one_off_roe_pp_2025")) or 0.0
    if len(roes) == 3 and None not in roes:
        roes[-1] -= one_off
    candidates = [r for r in roes + [f(d.get("roe_h1_2026_annualized"))] if r is not None]
    roe_s = min(candidates) if candidates else None
    coe = bank_coe(d["code"])
    if stressed and roe_s is not None:
        ratio = min(1.0, (roe_s - 3.0) / (coe - 3.0))
        v_ps = stressed * ratio if ratio > 0 else None
    else:
        v_ps = None
    gates = []
    cet1, req = f(d.get("cet1_pct")), f(d.get("cet1_req_pct"))
    if cet1 is not None and req is not None and cet1 < req + 1.5:
        gates.append(f"核心一级 {cet1}% 低于要求 {req}% + 1.5pp")
    coverage, ptl = f(d.get("coverage_pct")), f(d.get("provision_to_loans_pct"))
    if (coverage is not None and coverage < 150) or (ptl is not None and ptl < 2):
        gates.append(f"拨备覆盖率 {coverage}%／拨贷比 {ptl}% 未达 150%／2%")
    loans = f(d.get("loans_yi"))
    if loans and None not in parts[:2] and (parts[0] + parts[1]) / loans > 0.05:
        gates.append(f"不良加关注占贷款 {(parts[0] + parts[1]) / loans:.1%} 超过 5%")
    raw3 = [f(x) for x in (d.get("roe_2016_2025") or [])][-3:]
    if raw3 and None not in raw3 and min(raw3) < 6:
        gates.append(f"近三年 ROE 最低 {min(raw3)}% 低于 6%")
    actual_shares = f(pool_row["market_cap_yi"]) / f(pool_row["price"])   # 公司口径按实际股本，与池表市值同基（常熟按转股摊薄填股数）
    out.update(price=price, bvps=bvps, shares=shares, loss=loss, shortfall=shortfall, stressed=stressed, roe_s=roe_s, coe=coe,
               v_ps=v_ps, v_yi=v_ps * actual_shares if v_ps else None, pv=price / v_ps if v_ps else None, gates=gates)
    return out


def nonfin_review(d: dict, screen_row: dict, pool_row: dict) -> dict:
    out = dict(kind="B", notes=[])
    ncav, net_cash, v_screen = f(screen_row.get("ncav_yi")), f(screen_row.get("net_cash_yi")), f(screen_row.get("v_cb_yi"))
    earnings5 = v_screen - min(net_cash, ncav)                 # 粗筛 B 类的 5 × 盈利部分
    restricted = f(d.get("restricted_cash_yi")) or 0.0
    related = f(d.get("deposits_related_finance_yi")) or 0.0
    haircut = restricted + 0.5 * related                        # §6.10：受限资金不计，关联财务公司存款按 50%
    v = min(net_cash - haircut, ncav - haircut) + earnings5
    mcap = f(pool_row["market_cap_yi"])
    out.update(price=f(pool_row["price"]), ncav=ncav, net_cash=net_cash, haircut=haircut, earnings5=earnings5, v_yi=v,
               pv=mcap / v if v and v > 0 else None, gates=[])
    if restricted or related:
        out["notes"].append(f"扣受限资金 {restricted:.2f} 亿、关联财务公司存款 50%（{related:.2f} 亿）")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--governance-fail", default="", help="复核判治理不过的代码，逗号分隔")
    args = ap.parse_args()
    governance_fail = set(filter(None, args.governance_fail.split(",")))
    pool = {r["security_code"]: r for r in read(POOL)}
    screen = {r["security_code"]: r for r in read(SCREEN)}
    data = [json.loads(Path(p).read_text(encoding="utf-8")) for p in sorted(glob.glob(str(EXP / "data/*.json")))]
    data.append(PINGAN)
    results = []
    for d in data:
        code = str(d["code"]).zfill(6)
        d["code"] = code
        row = pool.get(code)
        if not row or row["status"] != "candidate":
            print("跳过（不在候选）：", code, d.get("name"))
            continue
        r = bank_review(d, row) if row["cb_type"] == "D" else nonfin_review(d, screen[code], row)
        if code in governance_fail:
            r["gates"].append("治理（复核判定，见全文）")
        flags = set(filter(None, row["auto_flags"].split("；")))
        catalysts = []
        dy, payout = f(row["dividend_yield"]), f(row["payout_3y"])
        if dy and dy >= 0.04:
            catalysts.append(f"股息率 {dy:.1%}")
        if payout and payout >= 0.30:
            catalysts.append(f"三年分红率 {payout:.0%}")
        if r["gates"]:
            status = "rejected"
        elif r["pv"] is None or r["pv"] > CANDIDATE_MAX:
            status, r["gates"] = "rejected", [f"复核 P/V_cb {r['pv']:.3f} 高于 1.0" if r["pv"] else "复核烟蒂价值不为正"]
        elif (r["pv"] <= FOCUS_MAX[row["cb_type"]] and row["cash_verified"] == "yes" and "流动性不足" not in flags and catalysts):
            status = "focus"
        else:
            status = "watch"
        review_id = d.get("review_id") or f"{BATCH}:{code}"
        results.append(dict(security_code=code, security_name=row["security_name"], cb_type=row["cb_type"], status=status,
                            pv_screen=row["pv_cb"], pv_reviewed=round(r["pv"], 3) if r["pv"] else "",
                            v_reviewed_yi=round(r["v_yi"], 2) if r.get("v_yi") else "",
                            stressed_bvps=round(r["stressed"], 2) if r.get("stressed") else "",
                            roe_s=round(r["roe_s"], 2) if r.get("roe_s") is not None else "", coe=r.get("coe", ""),
                            gates="；".join(r["gates"]), catalysts="；".join(catalysts), notes="；".join(r["notes"]),
                            independent_pv=d.get("pv", ""), verdict=d.get("verdict", ""),
                            governance=json.dumps(d.get("governance") or [], ensure_ascii=False),
                            review_id=review_id, falsifiers="；".join(d.get("falsifiers") or []), next_check=d.get("next_check", "")))
    fields = list(results[0])
    with (EXP / "review_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    for r in sorted(results, key=lambda r: (r["status"], f(r["pv_reviewed"]) or 9)):
        print(r["security_code"], r["security_name"], r["cb_type"], r["status"], "粗筛", r["pv_screen"], "复核", r["pv_reviewed"],
              "独立", r["independent_pv"], r["verdict"], "|", r["gates"] or "-", "|", r["notes"] or "-")
    if args.apply:
        apply(results, data, pool)
    return 0


def apply(results: list[dict], data: list[dict], pool: dict) -> None:
    from workflow_decision_log import WORKFLOW_VERSION, append_decision_log
    by_code = {str(d["code"]).zfill(6): d for d in data}
    for r in results:
        entry = pool[r["security_code"]]
        entry.update(status=r["status"], status_since=TODAY, v_cb_reviewed_yi=r["v_reviewed_yi"], pv_cb_reviewed=r["pv_reviewed"],
                     gates_failed=r["gates"], catalysts=r["catalysts"], falsifiers=r["falsifiers"], next_check=r["next_check"],
                     independent_review_id=r["review_id"], reviewed_at=TODAY, note=r["notes"])
    rows = sorted(pool.values(), key=lambda e: (("candidate", "watch", "focus", "rejected", "exited").index(e["status"]),
                                                e["cb_type"], f(e["pv_cb_reviewed"] or e["pv_cb"]) or 9))
    with POOL.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=POOL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    registry_path = ROOT / "data/processed/independent_valuations.csv"
    import build_independent_valuations as registry
    existing = registry.load(registry_path)
    current = {(e["market"], e["security_code"]): e for e in existing if e["status"] == "current"}
    new_rows = []
    for r in results:
        d = by_code[r["security_code"]]
        if d.get("review_id"):
            continue                                            # 平安银行已登记
        old = current.get(("A", r["security_code"]))
        if old:
            old.update(status="superseded", superseded_by=r["review_id"])
        price, v = f(d.get("price")), f(d.get("v_weighted"))
        model_v = model_pv = ""
        if r["cb_type"] == "D":
            import screen_daily_volume_price_signals as scanner
            value, _ = scanner.bank_live_value(r["security_code"], "2026-09-30", scanner._default_rf("2026-09-30"))
            if value:
                model_v, model_pv = f"{value:.2f}", f"{price / value:.3f}"
        probs = [f(d.get(k)) for k in ("p_bear", "p_base", "p_bull")]
        probs = [f"{p * 100:.0f}%" if p is not None and p <= 1 else (f"{p:.0f}%" if p is not None else "?") for p in probs]
        irr = f(d.get("implied_irr"))
        irr = irr / 100 if irr is not None and irr > 1 else irr     # 代理按百分数填写的折成小数
        coe = f(d.get("coe"))
        new_rows.append({k: "" for k in registry.FIELDS} | dict(
            review_id=r["review_id"], batch_id=BATCH, review_date=TODAY, reviewer_type="own", reviewer="独立代理（不读仓库，七组）",
            market="A", security_code=r["security_code"], security_name=r["security_name"], status="current",
            price_date="2026-09-30", evidence_cutoff="2026 中报及 09-30 前公告", currency="CNY", unit="元/股",
            price=f"{price}", v_base=f"{v:.2f}", v_bear=f"{f(d.get('v_bear')):.2f}" if f(d.get("v_bear")) else "",
            v_bull=f"{f(d.get('v_bull')):.2f}" if f(d.get("v_bull")) else "", pv=f"{price / v:.3f}",
            scenarios=f"熊 {d.get('v_bear')}（{probs[0]}）／基准 {d.get('v_base')}（{probs[1]}）／牛 {d.get('v_bull')}（{probs[2]}）",
            verdict=d.get("verdict", ""), confidence=d.get("confidence", ""),
            coe=f"{coe:g}%" if coe is not None else str(d.get("coe", "")), method=d.get("method", ""),
            implied_irr=f"{irr:.3f}" if irr is not None else "",
            model_v=model_v, model_pv=model_pv,
            conclusion=f"{d.get('verdict', '')}：独立 V {v:.2f}、P/V {price / v:.3f}；烟蒂池复核 {r['status']}（复核 P/V_cb {r['pv_reviewed']}）",
            basis=(d.get("notes") or "")[:600], risks="见全文", falsifiers=r["falsifiers"], next_check=r["next_check"],
            report=REPORT, evidence=f"data/experiments/exp_cigar_review_20261007/companies/{r['security_code']}_{r['security_name']}.md"))
    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=registry.FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing + new_rows)
    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    append_decision_log(ROOT / "data/processed/a_share_workflow_decision_log.csv", [dict(
        logged_at_utc=now, workflow_stage="cigar_butt_pool", run_id=f"cigar_butt_review:{TODAY}", as_of=TODAY,
        security_code=r["security_code"], security_name=r["security_name"], decision_type="cigar_butt_review",
        decision_result=f"candidate→{r['status']}",
        summary_reason=(f"{r['cb_type']} 类：粗筛 P/V_cb {r['pv_screen']}，复核 {r['pv_reviewed'] or '—'}"
                        + (f"；闸门：{r['gates']}" if r["gates"] else "") + (f"；兑现路径：{r['catalysts']}" if r["catalysts"] else "")
                        + f"；独立 P/V {r['independent_pv']}（{r['verdict']}）"),
        input_files="data/experiments/exp_cigar_review_20261007/", output_file="data/processed/cigar_butt_pool.csv",
        operator_or_script="data/experiments/exp_cigar_review_20261007/tools/apply_review.py", workflow_version=WORKFLOW_VERSION,
        decision_id=f"cigar_butt_pool:{TODAY}:{r['security_code']}:review") for r in results])
    print("已写池表、独立估值登记与决策日志", len(results))


if __name__ == "__main__":
    sys.exit(main())
