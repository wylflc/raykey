"""按用户 2026-10-15 裁定落地奥特维谷底锚研究数复核（工作流 §7.3 谷底侧复核、§6.5.2.2）。

读同目录 `688516.json`（研究数、证据日、可证伪条件、出处）与 `inputs.json`（模型锚），写档案研究数与差距复核字段，
向决策日志追加研究数登记行与差距复核行（按 decision_id 去重）。之后按 §7.3 当晚以同一信号日生效：
§6.7 第 4～6 步（`scripts/slurm/refresh_pool_from_bands.sbatch`）后重跑当日扫描并重新发布。

    python3 data/experiments/exp_trough_review_20261015/apply_ruling.py --conclusion 采用研究数|维持模型
"""
import argparse
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from workflow_decision_log import WORKFLOW_VERSION, append_decision_log  # noqa: E402

DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
LOG = ROOT / "data/processed/a_share_workflow_decision_log.csv"
DAY = "2026-10-15"
CODE, NAME = "688516", "奥特维"


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
    ap.add_argument("--conclusion", required=True, choices=("采用研究数", "维持模型"))
    args = ap.parse_args()
    review = json.loads((EXP / f"{CODE}.json").read_text(encoding="utf-8"))
    inputs = json.loads((EXP / "inputs.json").read_text(encoding="utf-8"))
    research, model = float(review["research_nopat_yi"]), float(inputs["model_anchor_yi"])
    gap = max(research, model) / min(research, model) - 1
    note = (f"{args.conclusion}（用户 {DAY} 裁定，§7.3 谷底侧复核，买入区内首次入队）：研究数 {research:.2f} 亿，模型锚 {model:.2f} 亿，差距 {gap:.1%}——"
            f"{review['why_anchor_high']}；研究口径 V {review['research_v']:.2f}、`P/V` {review['research_pv']:.3f}（10-15 收盘 {inputs['close_2026_10_15']:.2f}，"
            f"生产带 V {float(inputs['production_band']['intrinsic_value']):.2f}、`P/V` {inputs['candidate_pv']:.4f}）。{review['recommendation_reason']}")

    docs, nl = read_table(DOSSIERS)
    col = {name: i for i, name in enumerate(docs[0])}
    row = next(r for r in docs[1:] if r[col["security_code"]].zfill(6) == CODE)
    for key, value in dict(research_nopat_yi=f"{research:.2f}", research_evidence_date=review["research_evidence_date"],
                           research_falsifier=review["research_falsifier"], research_source=review["research_source"],
                           divergence_reviewed_at=DAY, divergence_review_conclusion=args.conclusion, divergence_review_note=note,
                           divergence_reviewed_model_yi=f"{model:.2f}", divergence_reviewed_research_yi=f"{research:.2f}").items():
        row[col[key]] = value
    DOSSIERS.write_bytes(dump(docs, nl))

    with LOG.open(encoding="utf-8-sig", newline="") as fh:
        seen = {r["decision_id"] for r in csv.DictReader(fh)}
    now, new = datetime.now(timezone.utc).isoformat(), []
    base = dict(logged_at_utc=now, workflow_stage="valuation_review", run_id=f"trough_anchor_review:{DAY}", as_of=DAY, security_code=CODE,
                security_name=NAME, input_files=f"user_confirmation;data/experiments/exp_trough_review_20261015/{CODE}.json",
                source_urls=";".join(s.get("url_or_path", "") for s in review.get("sources", []) if str(s.get("url_or_path", "")).startswith("http"))[:2000],
                output_file="data/processed/a_share_valuation_dossiers.csv", operator_or_script="exp_trough_review_20261015/apply_ruling.py",
                workflow_version=WORKFLOW_VERSION)
    registered_id = f"valuation_review:{DAY}:{CODE}:research_registered"
    if registered_id not in seen:
        new.append(dict(base, decision_type="research_normalized_earnings", decision_result="registered",
                        summary_reason=(f"§7.3 谷底侧复核登记研究数（§6.5.2.2）：{research:.2f} 亿（三档 {'／'.join(f'{x:g}' for x in review['bear_base_bull_yi'])} 亿；"
                                        f"{review['basis']}）；可证伪条件：{review['research_falsifier']}；证据日 {review['research_evidence_date']}。"),
                        decision_id=registered_id, supersedes_decision_id=""))
    review_id = f"valuation_review:{DAY}:{CODE}:divergence_review"
    if review_id not in seen:
        new.append(dict(base, decision_type="research_model_divergence_review", decision_result=args.conclusion, summary_reason=note,
                        decision_id=review_id, supersedes_decision_id=registered_id))
    append_decision_log(LOG, new)
    print(f"档案已写（{NAME} 研究数 {research:.2f} 亿，{args.conclusion}）；决策日志追加 {len(new)} 行")


if __name__ == "__main__":
    main()
