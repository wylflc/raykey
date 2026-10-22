"""按用户 2026-10-22 裁定落地 10-22 扫描后的复核（工作流 §7.3、§9.3.6）。

- 宁德时代：成长股预做重点复核，结论与证据见 `300750.json`；复核日记证据日 10-23（§9.3.6 第 3 条）。
- 生益科技、宝丰能源、海光信息：三季报或预告进带后研究与模型差距重新入队，按裁定写档案复核与复核时两数。

改写档案并向决策日志追加裁定行（按 decision_id 去重）。档案是发布输入：落地后按 §7.3 跑
`scripts/slurm/refresh_pool_from_bands.sbatch`，再重跑当日扫描并重新发布。

    python3 data/experiments/exp_growth_prereview_20261022/apply_rulings.py
"""
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
DAY, EVIDENCE_DAY = "2026-10-22", "2026-10-23"

DIVERGENCE = [
    dict(code="600183", conclusion="采用研究数", model="34.31", research="54.59",
         supersedes="valuation_review:2026-10-22:600183:oi291_divergence_review",
         note="继续采用研究数（用户 2026-10-22 裁定，§7.3 差距复核，三季度预告进带后重新入队）：研究数 54.59 亿，模型锚 34.31 亿"
              "（复核时 28.46 亿，+20.6%），差距 59.1%；生产带（研究口径）V 23.45、`P/V` 4.703，模型口径 V 14.78、`P/V` 7.460"
              "（2026-10-22 收盘 110.26）；独立评审 `iv20261021_pool_b17:600183`：独立 V 39.50。模型锚仍低于研究数熊市档 37.86 亿；"
              "研究数已含前三季度预增（归母 64.6～68.7 亿）。两种做法下都远离买入区。"),
    dict(code="600989", conclusion="采用研究数", model="105.57", research="148.77",
         supersedes="valuation_review:2026-10-22:600989:oi291_research_registered",
         note="采用研究数（用户 2026-10-22 裁定，§7.3 差距复核，三季报进带后首次入队）：研究数 148.77 亿，模型锚 105.57 亿"
              "（研究数登记时 123.23 亿），差距 40.9%；研究口径 V 18.34、`P/V` 1.108，生产带 V 12.18、`P/V` 1.668"
              "（2026-10-22 收盘 20.31）；独立评审 `iv20261021_pool_b21:600989`：独立 V 26.89。模型锚经周期守卫削 50.8%，"
              "约等于研究数熊市档 105.63 亿（同巨化股份先例）；研究数按三季报、现有约 595 万吨烯烃销量与 2024—2025 年价差正常化，"
              "已剔除油价冲高带来的约 36 亿周期性利润。研究口径仍在买入线外。"),
    dict(code="688041", conclusion="维持模型", model="45.95", research="72.05",
         supersedes="valuation_review:2026-10-20:688041:oi291_divergence_review",
         note="维持模型（用户 2026-10-22 裁定，§7.3 差距复核，三季报进带后重新入队）：研究数 72.05 亿，模型锚 45.95 亿"
              "（复核时 52.19 亿，−12.0%；峰值守卫削 49.1%），差距 56.8%；研究口径 V 42.79、`P/V` 4.464，生产带 V 25.23、"
              "`P/V` 7.571（2026-10-22 收盘 191.02）；独立评审 `iv20261019_pool_b01:688041`：独立 V 73.60。理由同 10-20："
              "模型按 g0 = 25% 计增长，研究数取 2026 年运行率作锚，采用会重复计增长；2026 年报后再议。研究数高于模型锚，不冻结。"),
]


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
    docs, nl = read_table(DOSSIERS)
    col = {name: i for i, name in enumerate(docs[0])}
    rows = {r[col["security_code"]].zfill(6): r for r in docs[1:]}

    review = json.loads((EXP / "300750.json").read_text(encoding="utf-8"))
    conclusion = review["user_ruling"]["conclusion"]
    catl = rows["300750"]
    note = (f"重点复核{conclusion}（用户 {DAY} 裁定，§9.3.6 第 6 条预做；复核日记证据日）：" + review["recommendation_reason"]
            + "｜改判条件（任一出现即改不通过并重做）：" + "；".join(review["flip_conditions"]) + "。")
    for key, value in dict(growth_reviewed_at=EVIDENCE_DAY, growth_review_conclusion=conclusion, growth_review_note=note,
                           growth_reviewed_pv=f"{review['inputs']['candidate_pv']:.4f}").items():
        catl[col[key]] = value
    for item in DIVERGENCE:
        row = rows[item["code"]]
        if row[col["research_nopat_yi"]] != item["research"]:
            raise SystemExit(f"{item['code']} 档案研究数 {row[col['research_nopat_yi']]} 与裁定时 {item['research']} 不一致")
        for key, value in dict(divergence_reviewed_at=DAY, divergence_review_conclusion=item["conclusion"],
                               divergence_review_note=item["note"], divergence_reviewed_model_yi=item["model"],
                               divergence_reviewed_research_yi=item["research"]).items():
            row[col[key]] = value
    DOSSIERS.write_bytes(dump(docs, nl))

    with LOG.open(encoding="utf-8-sig", newline="") as fh:
        seen = {r["decision_id"] for r in csv.DictReader(fh)}
    now, new = datetime.now(timezone.utc).isoformat(), []

    def add(run_id, as_of, code, name, dtype, result, summary, inputs, decision_id, supersedes=""):
        if decision_id not in seen:
            new.append(dict(logged_at_utc=now, workflow_stage="valuation_review", run_id=run_id, as_of=as_of, security_code=code,
                            security_name=name, decision_type=dtype, decision_result=result, summary_reason=summary,
                            input_files=inputs, source_urls="", output_file="data/processed/a_share_valuation_dossiers.csv",
                            operator_or_script="Claude", workflow_version=WORKFLOW_VERSION, decision_id=decision_id,
                            supersedes_decision_id=supersedes if supersedes in seen else ""))

    add(f"growth_review_{EVIDENCE_DAY}", EVIDENCE_DAY, "300750", "宁德时代", "growth_key_review", conclusion,
        catl[col["growth_review_note"]], "user_confirmation;data/experiments/exp_growth_prereview_20261022/300750.json",
        f"growth_review:300750:{EVIDENCE_DAY}")
    for item in DIVERGENCE:
        row = rows[item["code"]]
        add(f"divergence_review_{DAY}", DAY, item["code"], row[col["security_name"]], "research_model_divergence_review",
            item["conclusion"], item["note"],
            "user_confirmation;data/interim/a_share_report_update_queue.csv;data/processed/a_share_pool_model_bands_adopted.csv",
            f"divergence_review:{item['code']}:{DAY}", item["supersedes"])
    append_decision_log(LOG, new)
    print(f"档案已写（宁德时代重点复核{conclusion}；生益科技、宝丰能源、海光信息差距复核）；决策日志追加 {len(new)} 行")


if __name__ == "__main__":
    main()
