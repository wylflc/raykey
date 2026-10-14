"""按用户 2026-10-14 裁定落地当晚的复核（工作流 §7.3、§9.3.6），并登记 OI-287 规则裁定。

- 沪电股份：研究与模型差距因预告叠加重新入队，结论维持「采用研究数」（研究数 48.80 亿不改），档案记复核与两数。
- 德业股份：成长股预做重点复核，结论按用户裁定写档案（复核日按 v4.252 记证据日），研究数 46.2 亿照特宝生物先例登记
  （差距不足 30%，不采用）；登记行证伪条件按用户裁定改为分产品口径。旧条件的第 6 条核对先由
  `growth_stocks.py --check` 登记。
- OI-287：成长股当晚核对与复核记证据日（v4.252）。

改写档案并向决策日志追加裁定行（按 decision_id 去重）。

    python3 data/experiments/exp_growth_prereview_20261014/apply_rulings.py [--deye 通过|不通过]
"""
import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
REGISTRY = ROOT / "data/processed/a_share_business_attributes.csv"
LOG = ROOT / "data/processed/a_share_workflow_decision_log.csv"
DAY, EVIDENCE_DAY = "2026-10-14", "2026-10-15"
VERSION = "a-share-selection-operation-v4.252"

HUDIAN_NOTE = ("采用研究数（用户 2026-10-14 裁定，§7.3 差距复核，因预告叠加重新入队）：10-14 前三季度预告（归母 54.5～57.0 亿元）"
               "经 §6.4 叠加把每股净资产 ×1.1553，机械每股 NOPAT 1.4511→1.6765，模型锚 27.92→32.26 亿（+15.5%）；"
               "研究数 48.80 亿不改，差距 51.3%；研究口径 V 44.88→42.69（投入资本随账面上升、ROIC0 下降），P/V 2.69。"
               "预告折三季度单季归母 25.27～27.77 亿元（二季度 16.81 亿元），新增产能与价格各占多少要等三季报（10-28）的毛利率与产能数据，届时重估研究数。"
               "研究数证伪条件未触发（综合毛利率 2026Q1 35.63%、Q2 41.28%）。")


DEYE_FALSIFIER = ("新兴市场户储需求连续两年负增长，或储能逆变器毛利率连续两个半年度低于45%，"
                  "或电池包毛利率连续两个半年度低于22% → 复核")
DEYE_REGISTER_PREFIX = (f"{EVIDENCE_DAY} 预做复核：证伪条件由综合毛利率连续两季低于33%改为分产品口径（用户 {DAY} 裁定；"
                        "电池包收入占比升到约一半，结构会把综合毛利率拉向33%）。")
DEYE_FLIPS = ["登记行证伪条件触发（储能逆变器或电池包毛利率连续两个半年度分别低于45%、22%，或新兴市场户储需求连续两年负增长）",
              "电池包毛利超过逆变器毛利（按毛利主导项改判易复制）",
              "InfoLink等口径全球户储年出货量同比转负",
              "欧盟或主要市场把对中国逆变器的限制扩至户用（先按§7.4事件复核）",
              "模型锚升至60.1亿以上（研究数低于模型锚超30%，按§7.3入队并冻结）",
              "三季报（预约10-30）入带后本记录失效，须重做"]


def read_table(path: Path) -> tuple[list[list[str]], str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if dump(rows, newline) != raw:
        raise ValueError(f"无法逐字节往返：{path}")
    return rows, newline


def dump(rows: list[list[str]], newline: str) -> bytes:
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator=newline).writerows(rows)
    return out.getvalue().encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deye", choices=("通过", "不通过"), help="德业股份预做重点复核的用户裁定")
    args = ap.parse_args()

    docs, nl = read_table(DOSSIERS)
    head = docs[0]
    col = {name: i for i, name in enumerate(head)}
    rows = {r[col["security_code"]].zfill(6): r for r in docs[1:]}

    hd = rows["002463"]
    for key, value in dict(divergence_reviewed_at=DAY, divergence_review_conclusion="采用研究数", divergence_review_note=HUDIAN_NOTE,
                           divergence_reviewed_model_yi="32.26", divergence_reviewed_research_yi="48.80").items():
        hd[col[key]] = value

    deye = None
    if args.deye:
        review = json.loads((EXP / "605117.json").read_text(encoding="utf-8"))
        inputs = json.loads((EXP / "inputs.json").read_text(encoding="utf-8"))
        deye = rows["605117"]
        note = (f"重点复核{args.deye}（用户 {DAY} 裁定，§9.3.6 第 6 条预做；复核日按 v4.252 记证据日）：" + review["recommendation_reason"]
                + "｜改判条件（任一出现即改不通过并重做）：" + "；".join(DEYE_FLIPS) + "。")
        for key, value in dict(research_nopat_yi=f"{review['research_nopat_yi']:.2f}", research_evidence_date=review["research_evidence_date"],
                               research_falsifier=review["research_falsifier"], research_source=review["research_source"],
                               growth_reviewed_at=EVIDENCE_DAY, growth_review_conclusion=args.deye, growth_review_note=note,
                               growth_reviewed_pv=f"{inputs['candidate_pv']:.4f}").items():
            deye[col[key]] = value
    DOSSIERS.write_bytes(dump(docs, nl))

    if deye is not None:
        reg, reg_nl = read_table(REGISTRY)
        rh = {name: i for i, name in enumerate(reg[0])}
        row = next(r for r in reg[1:] if r[rh["security_code"]].zfill(6) == "605117")
        if row[rh["falsifier"]] != DEYE_FALSIFIER:
            row[rh["falsifier"]] = DEYE_FALSIFIER
            row[rh["registered_at"]] = EVIDENCE_DAY
            if not row[rh["note"]].startswith(DEYE_REGISTER_PREFIX):
                row[rh["note"]] = DEYE_REGISTER_PREFIX + row[rh["note"]]
        REGISTRY.write_bytes(dump(reg, reg_nl))

    with LOG.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        seen = {r["decision_id"] for r in reader}
    now, new = datetime.now(timezone.utc).isoformat(), []

    def add(stage, run_id, as_of, code, name, dtype, result, summary, inputs, output, decision_id):
        if decision_id not in seen:
            new.append(dict(logged_at_utc=now, workflow_stage=stage, run_id=run_id, as_of=as_of, security_code=code, security_name=name,
                            decision_type=dtype, decision_result=result, summary_reason=summary, input_files=inputs, source_urls="",
                            output_file=output, operator_or_script="Claude", workflow_version=VERSION, decision_id=decision_id,
                            supersedes_decision_id=""))

    add("workflow_rule", "v4.252-20261014", DAY, "ALL", "", "trading_rule", "adopted",
        "用户2026-10-14裁定（v4.252，结 OI-287）：§9.3.6 成长股重点复核日与定期报告后核对日都记当晚扫描的证据日（信号日之后的首个工作日），"
        "与生产带吸收的晚间公告日戳同口径；growth_stocks.py 比较式不变。",
        "docs/000_Ashare_workflow.md", "docs/000_Ashare_workflow.md", "workflow_rule:v4.252:oi287")
    add("valuation_review", "divergence_review_2026-10-14", DAY, "002463", "沪电股份", "research_divergence_review", "采用研究数",
        HUDIAN_NOTE, "data/processed/a_share_valuation_dossiers.csv;data/interim/a_share_report_update_queue.csv",
        "data/processed/a_share_valuation_dossiers.csv", "divergence_review:002463:2026-10-14")
    if deye is not None:
        add("valuation_review", "growth_review_2026-10-15", EVIDENCE_DAY, "605117", "德业股份", "growth_key_review", args.deye,
            f"研究 {review['research_nopat_yi']:.2f} 亿登记（与模型锚 {inputs['model_anchor_yi']:.2f} 亿差 14.7%，不入队、不采用）；"
            + deye[col["growth_review_note"]], "user_confirmation;data/experiments/exp_growth_prereview_20261014/605117.json",
            "data/processed/a_share_valuation_dossiers.csv", f"growth_review:605117:{EVIDENCE_DAY}")
        add("quality_review", "growth_review_2026-10-15", EVIDENCE_DAY, "605117", "德业股份", "business_attributes_update",
            "结构成长型（类别不变）", DEYE_REGISTER_PREFIX + "新条件：" + DEYE_FALSIFIER,
            "user_confirmation;data/experiments/exp_growth_prereview_20261014/605117.json",
            "data/processed/a_share_business_attributes.csv", f"quality_review:{EVIDENCE_DAY}:605117:business_attributes_update")
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from workflow_decision_log import append_decision_log
    append_decision_log(LOG, new)
    print(f"档案已写（沪电{'、德业' if deye is not None else ''}）；决策日志追加 {len(new)} 行")


if __name__ == "__main__":
    main()
