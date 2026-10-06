"""OI-265（用户 2026-10-06 裁定）：买入区 15 只按 OI-259 审查基准档登记研究正常化盈利，五粮液改登记并维持采用研究数，
研究数管不到的 8 只登记 §7.5 临时冻结名单。

研究数按 §6.5.2.2 与模型同口径（税后经营利润、剔金融收益、含少数股东份额、研发资本化）。审查各股基准档口径不一，分三类换算：
- `nopat`：审查给的已是合并税后经营利润（研发费用化）→ 基准 + 最新年报研发资本化加回（资本化 NOPAT − 费用化 NOPAT）；
- `parent_net`：审查给的是归母净利 → `research_nopat_from_parent`（归母 ÷ (1 − 带 minority_share) + 最新年报 NOPAT − 合并净利）；
- `parent_operating`：审查给的是归母经营利润（已剔利息与理财收益）→ 基准 ÷ (1 − minority_share) + 研发资本化加回
  （中材国际另加审查按经营成本扣的汇兑 2 亿 × (1 − 税率)：模型把汇兑随财务费用剔出 EBIT，OI-270）。
三档、可证伪条件与证据日取 `exp_oi259_lowpv_20261005/companies/<代码>_<名称>.json`。

    python3 register.py [--dry-run]
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import roic_inputs  # noqa: E402
from build_report_update_queue import RESEARCH_GAP_MAX, research_nopat_from_parent  # noqa: E402
from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log  # noqa: E402

AUDIT = ROOT / "data/experiments/exp_oi259_lowpv_20261005/companies"
DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
BANDS = ROOT / "data/processed/a_share_pool_model_bands_adopted.csv"
INDUSTRY = ROOT / "data/reference/a_share_csrc_industry.csv"
HOLDS = ROOT / "data/reference/review_holds.csv"
DAY, AUDIT_DAY = "2026-10-06", "2026-10-05"
PERIOD = "2025-12-31"
CALIBER = {   # 代码 → (审查基准档口径, 汇兑税前加回亿元)
    "603279": ("nopat", 0.0), "000858": ("nopat", 0.0), "000596": ("nopat", 0.0), "000568": ("nopat", 0.0),
    "603369": ("nopat", 0.0), "600809": ("nopat", 0.0), "603855": ("nopat", 0.0), "600938": ("nopat", 0.0),
    "300910": ("nopat", 0.0), "002920": ("nopat", 0.0), "920599": ("nopat", 0.0),
    "002001": ("parent_net", 0.0), "002594": ("parent_net", 0.0),
    "000786": ("parent_operating", 0.0), "600970": ("parent_operating", 2.0),
}
WULIANGYE = "000858"
PRIOR_WULIANGYE = "valuation_review:2026-09-24:000858:7d565013"
HOLD = {   # 研究数管不到的 8 只：代码 → (所依 issue, 解除条件, 偏差来源)
    "603855": ("OI-265；OI-262", "OI-262 落地后重评，或逐只复核结束", "股权桥分红时点：已宣派未入账的年度分红按外生权益加回（V 多约 1.00 元）"),
    "600938": ("OI-265；OI-252", "OI-252 裁定，或逐只复核结束", "资本腿 g0 9.7% 外推到存量商品，锚约等于布伦特 83 美元"),
    "002001": ("OI-265；OI-252、OI-270", "OI-252 裁定，或逐只复核结束", "周期高位窗口的 g0 10.5%，研发摊销按医药 10 年"),
    "300910": ("OI-265；OI-252、OI-270", "OI-252 裁定，或逐只复核结束", "低谷起点的 g0 17.7%，权益法基金收益进 EBIT"),
    "600809": ("OI-265；OI-266、OI-268", "OI-266／OI-268 裁定，或逐只复核结束", "白酒下行期锚高于 TTM，独立基准 P/V 1.14"),
    "002920": ("OI-265；OI-267、OI-252", "OI-267／OI-252 裁定，或逐只复核结束", "研发资本化加回外推（不资本化 V −32%），g0 18.6%"),
    "002594": ("OI-265；OI-267、OI-252", "OI-267／OI-252 裁定，或逐只复核结束", "研发加回约 38 元／股外推，g0 20.5%"),
    "920599": ("OI-265；OI-252", "OI-252 裁定，或逐只复核结束", "资本腿增长腿约 9.3 元／股"),
}
HOLD_FIELDS = ["security_code", "security_name", "basis", "ruled_at", "release_condition", "released_at", "note"]


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def audit_items():
    out = {}
    for path in glob.glob(str(AUDIT / "*.json")):
        code = os.path.basename(path)[:6]
        if code not in CALIBER:
            continue
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        prof = d["independent"]["normalized_profit_yi"]
        text = str(d.get("trap_risk", ""))
        m = re.search(r"(可证伪条件|可证伪|陷阱条件)[：:](.+)", text)
        falsifier = m.group(2).strip() if m else ""
        falsifier = re.split(r"[。；]\s*(S15|模型锚要到)", falsifier)[0].strip("。；")
        dates = [s.get("date", "") for s in d.get("sources", []) if isinstance(s, dict)]
        dates = [x for x in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", x or "") and x <= AUDIT_DAY]
        out[code] = dict(name=d["name"], bear=float(prof["bear"]), base=float(prof["base"]), bull=float(prof["bull"]),
                         falsifier=falsifier, evidence_date=max(dates) if dates else AUDIT_DAY,
                         report=f"data/experiments/exp_oi259_lowpv_20261005/companies/{os.path.basename(path)}")
    missing = set(CALIBER) - set(out)
    assert not missing, missing
    return out


def convert(caliber, value, fx_pretax, m, raw, cap):
    addback = (cap.nopat - raw.nopat) / 1e8
    if caliber == "nopat":
        return value + addback
    if caliber == "parent_net":
        return research_nopat_from_parent(value, m, cap.nopat / 1e8, cap.net_profit / 1e8)
    return value / (1.0 - m) + addback + fx_pretax * (1.0 - (cap.tax_rate or 0.25))


def main(dry_run: bool) -> None:
    items = audit_items()
    codes = set(items)
    bands = {r["security_code"]: r for r in read(BANDS)[0]}
    csrc = {r["security_code"]: r["csrc_industry"] for r in read(INDUSTRY)[0]}
    years = roic_inputs.load_statements(codes, ic_floor=0.1, caliber="nonop", restricted_cash="notes_wc")
    rd = roic_inputs.load_rd_expense(codes)
    record = {}
    for code, it in sorted(items.items()):
        b = bands[code]
        raw = years[code][PERIOD]
        capped = roic_inputs.capitalize_rd(years[code], rd.get(code, {}), roic_inputs.rd_life(csrc.get(code)))
        cap = capped[0][PERIOD] if capped else raw
        m = float(b["minority_share"] or 0.0)
        caliber, fx = CALIBER[code]
        conv = {k: round(convert(caliber, it[k], fx, m, raw, cap), 2) for k in ("bear", "base", "bull")}
        adopted = bool((b.get("research_overlay") or "").strip())
        model = float(b["model_nopat_ps"] if adopted else b["nopat_ps"]) * float(b["shares_est"]) / 1e8
        research = conv["base"]
        gap = max(model, research) / min(model, research) - 1
        record[code] = dict(name=it["name"], caliber=caliber, audit_bear_base_bull=[it["bear"], it["base"], it["bull"]],
                            research_bear_base_bull=[conv["bear"], conv["base"], conv["bull"]], research_nopat_yi=research,
                            minority_share=m, rd_addback_yi=round((cap.nopat - raw.nopat) / 1e8, 2),
                            nopat_less_net_profit_yi=round((cap.nopat - cap.net_profit) / 1e8, 2), fx_pretax_yi=fx,
                            tax_rate=cap.tax_rate, model_anchor_yi=round(model, 2), gap=round(gap, 4),
                            triggered=gap > RESEARCH_GAP_MAX + 1e-9, freeze=gap > RESEARCH_GAP_MAX + 1e-9 and (research > model if adopted else research < model),
                            adopted=adopted, evidence_date=it["evidence_date"], falsifier=it["falsifier"], report=it["report"])
    (EXP / "register.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    for code, r in sorted(record.items(), key=lambda kv: -kv[1]["gap"]):
        print(f"{code} {r['name']:6s} {r['caliber']:16s} 审查 {r['audit_bear_base_bull'][1]:>8} → 研究 {r['research_nopat_yi']:>8.2f}"
              f" 模型锚 {r['model_anchor_yi']:>8.2f} 差距 {r['gap']:.1%} {'冻结' if r['freeze'] else ('入队' if r['triggered'] else '')}")
    if dry_run:
        return

    rows, fields = read(DOSSIERS)
    now = datetime.now(timezone.utc).isoformat()
    log = []
    for row in rows:
        code = row["security_code"]
        if code not in record:
            continue
        r = record[code]
        lo, hi = r["research_bear_base_bull"][0], r["research_bear_base_bull"][2]
        conv_note = {"nopat": f"审查基准档为合并税后经营利润（研发费用化）{r['audit_bear_base_bull'][1]:g} 亿，加 2025 年报研发资本化加回 {r['rd_addback_yi']:+.2f} 亿",
                     "parent_net": f"审查基准档为归母净利 {r['audit_bear_base_bull'][1]:g} 亿，÷ (1 − 少数股东份额 {r['minority_share']:.3f}) {r['nopat_less_net_profit_yi']:+.2f} 亿（2025 年报 NOPAT − 合并净利，研发资本化口径）",
                     "parent_operating": f"审查基准档为归母经营利润（已剔利息与理财收益）{r['audit_bear_base_bull'][1]:g} 亿，÷ (1 − 少数股东份额 {r['minority_share']:.3f})，加 2025 年报研发资本化加回 {r['rd_addback_yi']:+.2f} 亿"
                     + (f"，加审查按经营成本扣的汇兑 {r['fx_pretax_yi']:g} 亿 × (1 − {r['tax_rate']:.1%})（模型把汇兑随财务费用剔出 EBIT）" if r["fx_pretax_yi"] else "")}[r["caliber"]]
        row["research_nopat_yi"] = f"{r['research_nopat_yi']:.2f}"
        row["research_evidence_date"] = r["evidence_date"]
        row["research_falsifier"] = (r["falsifier"] + "；" if r["falsifier"] else "") + f"连续两个年报模型口径 NOPAT 落在 {lo:.2f}～{hi:.2f} 亿（审查悲观～乐观档换算）之外"
        row["research_source"] = (f"OI-259 低 P/V 审查（docs/reports/low_pv_audit_2026-10-05.zh.md，{r['report']}）：{conv_note} = {r['research_nopat_yi']:.2f} 亿"
                                  f"（§6.5.2.2 模型同口径；用户 {DAY} 裁定登记，OI-265）")
        summary = (f"OI-265 按 OI-259 审查基准档登记研究正常化盈利 {r['research_nopat_yi']:.2f} 亿（区间 {lo:.2f}～{hi:.2f}），模型锚 {r['model_anchor_yi']:.2f} 亿，"
                   f"差距 {r['gap']:.1%}" + ("，> 30% 按 §7.3 入队；模型锚较高，冻结新增买入至复核结论" if r["freeze"] else "，未超过 30%、不入队")
                   + f"。{conv_note}。可证伪：{row['research_falsifier']}")
        if code == WULIANGYE:
            row["divergence_reviewed_at"] = DAY
            row["divergence_review_conclusion"] = "采用研究数"
            row["divergence_reviewed_model_yi"] = f"{r['model_anchor_yi']:.2f}"
            row["divergence_reviewed_research_yi"] = f"{r['research_nopat_yi']:.2f}"
            row["divergence_review_note"] = (f"采用研究数（用户 {DAY} 裁定改登记，OI-265）：研究数 177.92 → {r['research_nopat_yi']:.2f} 亿，按 OI-259 审查基准档"
                                             f"（合并 NOPAT 150 亿：中报后 7 家一致预期 2026E／27E 归母 155／173 亿折 NOPAT 143／161 亿之间；悲观 110 亿约等于 TTM，乐观 190 亿约等于 2028E）"
                                             f"加研发资本化加回 {r['rd_addback_yi']:+.2f} 亿；模型锚 {r['model_anchor_yi']:.2f} 亿（谷底守卫回归五年中位），差距 {r['gap']:.1%}。"
                                             f"审查：2025 年发货腰斩，监管商品款项 239.7 亿待消化，普五批价低于经销商开票成本，独立基准 P/V 1.18。"
                                             f"前次：用户 2026-09-24 裁定采用研究数 177.92 亿（归母约 190 亿换算）")
            log.append(dict(logged_at_utc=now, workflow_stage="valuation_review", run_id=f"oi209_divergence_review:{DAY}", as_of=DAY,
                            security_code=code, security_name=r["name"], decision_type="research_model_divergence_review",
                            decision_result="采用研究数",
                            summary_reason=f"研究 {r['research_nopat_yi']:.2f} 亿、模型锚 {r['model_anchor_yi']:.2f} 亿、差距 {r['gap']:.1%}；{row['divergence_review_note']}",
                            input_files=f"user_confirmation;{r['report']};data/experiments/exp_oi265_20261006/register.json",
                            output_file="data/processed/a_share_valuation_dossiers.csv", operator_or_script="Claude",
                            workflow_version=WORKFLOW_VERSION, decision_id=f"valuation_review:{DAY}:{code}:oi265_research",
                            supersedes_decision_id=PRIOR_WULIANGYE))
            continue
        log.append(dict(logged_at_utc=now, workflow_stage="valuation_review", run_id=f"oi265_research:{DAY}", as_of=DAY,
                        security_code=code, security_name=r["name"], decision_type="research_normalized_earnings",
                        decision_result="registered", summary_reason=summary,
                        input_files=f"user_confirmation;{r['report']};data/experiments/exp_oi265_20261006/register.json",
                        output_file="data/processed/a_share_valuation_dossiers.csv", operator_or_script="Claude",
                        workflow_version=WORKFLOW_VERSION, decision_id=f"valuation_review:{DAY}:{code}:research_registered"))
    with DOSSIERS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    holds = []
    for code, (basis, release, source) in HOLD.items():
        r = record[code]
        note = (f"{source}；研究数 {r['research_nopat_yi']:.2f} 亿对模型锚 {r['model_anchor_yi']:.2f} 亿差距 {r['gap']:.1%}，"
                f"偏乐观主要在锚之外（OI-259 独立基准 P/V 见审查报告）")
        holds.append(dict(security_code=code, security_name=r["name"], basis=basis, ruled_at=DAY, release_condition=release,
                          released_at="", note=note))
        log.append(dict(logged_at_utc=now, workflow_stage="valuation_review", run_id=f"oi265_hold:{DAY}", as_of=DAY,
                        security_code=code, security_name=r["name"], decision_type="user_review_hold", decision_result="registered",
                        summary_reason=f"用户 {DAY} 裁定登记 §7.5 临时冻结（{basis}），冻结新增买入；解除条件：{release}。{note}",
                        input_files="user_confirmation;docs/reports/low_pv_audit_2026-10-05.zh.md", output_file=str(HOLDS.relative_to(ROOT)),
                        operator_or_script="Claude", workflow_version=WORKFLOW_VERSION,
                        decision_id=f"valuation_review:{DAY}:{code}:user_review_hold"))
    with HOLDS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HOLD_FIELDS)
        writer.writeheader()
        writer.writerows(holds)
    append_decision_log(DEFAULT_DECISION_LOG, log)
    print(f"wrote {DOSSIERS.relative_to(ROOT)} ({len(record)} 只)、{HOLDS.relative_to(ROOT)} ({len(holds)} 只)、决策日志 {len(log)} 行（{WORKFLOW_VERSION}）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    main(ap.parse_args().dry_run)
