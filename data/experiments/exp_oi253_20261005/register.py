"""OI-253：登记中创智领研究正常化盈利（§6.5.2.2），按 §7.3 入队并冻结新增买入；采用与否待用户裁定。

    python3 register.py                 # 登记研究数（档案 research_* 列）并追加决策日志行
    python3 register.py --adopt         # 用户裁定「采用研究数」后：写差距复核结论并追加裁定行
    python3 register.py --keep          # 用户裁定「维持模型」后：同上，结论为维持模型
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
LOG = ROOT / "data/processed/a_share_workflow_decision_log.csv"
BANDS = ROOT / "data/processed/a_share_pool_model_bands_adopted.csv"
CODE, DAY = "601717", "2026-10-05"
VERSION = "a-share-selection-operation-v4.229"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--adopt", action="store_true")
    group.add_argument("--keep", action="store_true")
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    review = json.loads((EXP / f"{CODE}.json").read_text(encoding="utf-8"))
    band = next(r for r in read(BANDS)[0] if r["security_code"] == CODE)
    model_yi = float(band.get("model_nopat_ps") or band["nopat_ps"]) * float(band["shares_est"]) / 1e8
    research = float(review["research_nopat_yi"])
    rows, fields = read(DOSSIERS)
    d = next(r for r in rows if r["security_code"] == CODE)
    d.update(research_nopat_yi=f"{research:.2f}", research_evidence_date=review["research_evidence_date"],
             research_falsifier=review["research_falsifier"], research_source=review["research_source"])
    conclusion = "采用研究数" if args.adopt else "维持模型" if args.keep else ""
    if conclusion:
        d.update(divergence_reviewed_at=DAY, divergence_review_conclusion=conclusion, divergence_review_note=args.note,
                 divergence_reviewed_model_yi=f"{model_yi:.2f}", divergence_reviewed_research_yi=f"{research:.2f}")
    write(DOSSIERS, rows, fields)
    log_rows, log_fields = read(LOG)
    seen = {r["decision_id"] for r in log_rows}
    now = datetime.now(timezone.utc).isoformat()
    gap = max(research, model_yi) / min(research, model_yi) - 1
    new = []
    base = dict(logged_at_utc=now, workflow_stage="valuation_review", as_of=DAY, security_code=CODE, security_name="中创智领",
                input_files="data/experiments/exp_oi253_20261005/601717.json", source_urls="",
                output_file="data/processed/a_share_valuation_dossiers.csv", operator_or_script="Claude",
                workflow_version=VERSION, supersedes_decision_id="")
    reg_id = f"valuation_review:{DAY}:{CODE}:research_registered"
    if reg_id not in seen:
        new.append(dict(base, run_id="oi253_research:2026-10-05", decision_type="research_normalized_earnings", decision_result="registered",
                        summary_reason=(f"OI-253 研究复核登记研究正常化盈利 {research:.2f} 亿（区间 {review['research_range_yi'][0]:.2f}～"
                                        f"{review['research_range_yi'][1]:.2f}），模型锚 {model_yi:.2f} 亿，差距 {gap:.0%} > 30%，按 §7.3 入队；"
                                        "模型锚较高，冻结新增买入至用户裁定。可证伪：" + review["research_falsifier"]),
                        decision_id=reg_id))
    if conclusion:
        rid = f"valuation_review:{DAY}:{CODE}:research"
        if rid not in seen:
            new.append(dict(base, run_id="oi209_divergence_review:2026-10-05", decision_type="research_model_divergence_review",
                            decision_result=conclusion, input_files="user_confirmation;" + base["input_files"],
                            summary_reason=f"研究 {research:.2f} 亿、模型锚 {model_yi:.2f} 亿；用户 {DAY} 裁定{conclusion}。{args.note}",
                            decision_id=rid))
    if new:
        with LOG.open("a", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=log_fields).writerows(new)
    print(json.dumps(dict(research_yi=research, model_yi=round(model_yi, 2), gap=round(gap, 3), conclusion=conclusion,
                          log_rows_added=len(new)), ensure_ascii=False))


if __name__ == "__main__":
    main()
