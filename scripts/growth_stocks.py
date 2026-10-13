"""工作流 §9.3.6 成长股模块：读业务属性登记表（个人投资体系第 5.12 节）与档案的重点复核记录。

成长股 = 登记表 `derived_class = 结构成长型` 的公司；由结构成长型改判为其他类别的记 `rejudged_from`，持仓按
§9.3.1 成长股卖出行逐日减一档。重点复核记录（档案 `growth_reviewed_at`／`growth_review_conclusion`）在生产带此后
吸收新定期报告或预告、或登记行变动时失效。交易阈值只在扫描器 `SEC93_GROWTH_*` 常量（§9.3.1）。

§9.3.6 第 6 条：生产带吸收成长股新定期报告后，逐只核对登记行的可证伪条件并登记：

    python3 scripts/growth_stocks.py --check <代码> --checked-at YYYY-MM-DD --note "..."
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUSINESS = ROOT / "data/processed/a_share_business_attributes.csv"
DEFAULT_DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
GROWTH_CLASS = "结构成长型"
REVIEW_PASS, REVIEW_FAIL = "通过", "不通过"
REVIEW_FIELDS = ("growth_reviewed_at", "growth_review_conclusion", "growth_review_note", "growth_reviewed_pv")
CHECK_FIELDS = ("falsifier_checked_at", "falsifier_check_note")
PREREVIEW_PV_MULTIPLE = 1.2   # §9.3.6 第 6 条：定期报告后预做重点复核的 P/V 上限 = 买入线 × 此值


@dataclass
class GrowthState:
    growth: set[str] = field(default_factory=set)           # 现登记为结构成长型
    exiting: set[str] = field(default_factory=set)          # 由结构成长型改判为其他类别
    low_confidence: set[str] = field(default_factory=set)   # 可复制性把握为低的难复制判定
    reviews: dict[str, tuple[str, str]] = field(default_factory=dict)   # 代码 → (pass／fail／stale／missing, 说明)
    report_checks: dict[str, str] = field(default_factory=dict)        # 代码 → 定期报告后待核对的说明（§9.3.6 第 6 条）

    def passed(self, code: str) -> bool:
        return self.reviews.get(code, ("missing", ""))[0] == "pass"

    def gated(self, code: str) -> bool:
        """§10.1 第 4 条：成长股无有效「通过」记录；改判后的清仓期由调用方按持仓另判。"""
        return code in self.growth and not self.passed(code)


def _read(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not Path(path).exists():
        return {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return {(r.get("security_code") or "").strip().zfill(6): r for r in csv.DictReader(handle)}


def review_status(dossier: dict | None, band: dict | None, register_row: dict | None) -> tuple[str, str]:
    """重点复核记录的状态：`pass`／`fail` 有效，`stale` 已失效，`missing` 无记录。"""
    dossier, band, register_row = dossier or {}, band or {}, register_row or {}
    reviewed = (dossier.get("growth_reviewed_at") or "").strip()[:10]
    conclusion = (dossier.get("growth_review_conclusion") or "").strip()
    if not reviewed or conclusion not in (REVIEW_PASS, REVIEW_FAIL):
        return "missing", "无重点复核记录"
    later = [f"{key} {value}" for key, value in (("available_at", (band.get("available_at") or "")[:10]),
                                                  ("forecast_notice_date", (band.get("forecast_notice_date") or "")[:10]),
                                                  ("registered_at", (register_row.get("registered_at") or "")[:10]))
             if value and value > reviewed]
    if later:
        return "stale", f"复核 {reviewed} 之后 {'、'.join(later)}，记录失效"
    return ("pass" if conclusion == REVIEW_PASS else "fail"), f"复核 {reviewed} {conclusion}"


def report_check_due(register_row: dict | None, band: dict | None) -> str | None:
    """§9.3.6 第 6 条：生产带吸收的定期报告晚于登记日与上次核对日的较晚者时待核对，返回说明。"""
    register_row, band = register_row or {}, band or {}
    available = (band.get("available_at") or "").strip()[:10]
    base = max((register_row.get("registered_at") or "").strip()[:10],
               (register_row.get("falsifier_checked_at") or "").strip()[:10])
    if available and available > base:
        return f"带 available_at {available} 晚于上次核对 {base or '无'}"
    return None


def prereview_needed(state: "GrowthState", code: str, pv: float | None, buy_line: float) -> bool:
    """§9.3.6 第 6 条：待核对的成长股候选侧 P/V 不高于买入线 × PREREVIEW_PV_MULTIPLE 且无有效「通过」记录。"""
    return (code in state.report_checks and pv is not None and pv <= buy_line * PREREVIEW_PV_MULTIPLE
            and not state.passed(code))


def record_check(code: str, checked_at: str, note: str, *, business: Path = DEFAULT_BUSINESS,
                 log_path: Path | None = None) -> dict[str, str]:
    """登记一次定期报告后的可证伪条件核对：只写 CHECK_FIELDS 两列，其余字节不动，并写决策日志。"""
    import io
    from datetime import date, datetime, timezone
    from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log
    code = code.zfill(6)
    date.fromisoformat(checked_at)
    if not note.strip():
        raise ValueError("核对须写读数与结论")
    raw = Path(business).read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    check = io.StringIO(newline="")
    csv.writer(check, lineterminator=newline).writerows(rows)
    if check.getvalue().encode("utf-8") != raw:
        raise ValueError("登记表无法逐字节往返，先人工核对文件格式")
    header = rows[0]
    for name in CHECK_FIELDS:
        if name not in header:
            header.append(name)
            for row in rows[1:]:
                row.append("")
    col = {name: header.index(name) for name in header}
    target = next((r for r in rows[1:] if r[col["security_code"]].zfill(6) == code), None)
    if target is None or target[col["derived_class"]] != GROWTH_CLASS:
        raise ValueError(f"不是登记在册的成长股：{code}")
    if checked_at < (target[col["registered_at"]] or "")[:10] or checked_at < (target[col["falsifier_checked_at"]] or "")[:10]:
        raise ValueError("核对日不得早于登记日或上次核对日")
    target[col["falsifier_checked_at"]], target[col["falsifier_check_note"]] = checked_at, note.strip()
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator=newline).writerows(rows)
    Path(business).write_bytes(out.getvalue().encode("utf-8"))
    name = target[col["security_name"]]
    append_decision_log(log_path or DEFAULT_DECISION_LOG, [{
        "logged_at_utc": datetime.now(timezone.utc).isoformat(), "workflow_stage": "valuation_review",
        "run_id": f"growth_report_check_{checked_at}", "as_of": checked_at, "security_code": code, "security_name": name,
        "decision_type": "growth_falsifier_check", "decision_result": "已核对",
        "summary_reason": f"§9.3.6 第 6 条 定期报告后核对可证伪条件：{target[col['falsifier']]}｜{note.strip()}",
        "input_files": str(business), "source_urls": "", "output_file": str(business),
        "operator_or_script": "growth_stocks.py", "workflow_version": WORKFLOW_VERSION,
        "decision_id": f"growth_falsifier_check:{code}:{checked_at}", "supersedes_decision_id": ""}])
    return dict(zip(header, target))


def load_growth_state(business: Path | None = DEFAULT_BUSINESS, dossiers: Path | None = DEFAULT_DOSSIERS,
                      bands: dict[str, dict] | None = None) -> GrowthState:
    """`bands` 为扫描器 `load_model_bands` 读出的候选侧生产带（代码 → 当日可用带行）。"""
    register, docs, bands = _read(business), _read(dossiers), bands or {}
    state = GrowthState()
    for code, row in register.items():
        cls = (row.get("derived_class") or "").strip()
        if cls == GROWTH_CLASS:
            state.growth.add(code)
            if ((row.get("replicability") or "").strip() == "难复制"
                    and (row.get("replicability_confidence") or "").strip() == "低"):
                state.low_confidence.add(code)
            state.reviews[code] = review_status(docs.get(code), bands.get(code), row)
            due = report_check_due(row, bands.get(code))
            if due:
                state.report_checks[code] = due
        elif (row.get("rejudged_from") or "").strip() == GROWTH_CLASS:
            state.exiting.add(code)
    return state


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", metavar="代码", required=True, help="登记该成长股定期报告后的可证伪条件核对")
    parser.add_argument("--checked-at", required=True, help="核对日 YYYY-MM-DD")
    parser.add_argument("--note", required=True, help="按新报告的读数与结论")
    args = parser.parse_args()
    row = record_check(args.check, args.checked_at, args.note)
    print(f"已登记核对：{row['security_code']} {row['security_name']} {row['falsifier_checked_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
