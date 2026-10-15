"""工作流 §7.5 用户裁定的临时冻结名单（`data/reference/review_holds.csv`）：定期报告后的复看。

`released_at` 为空的行，在该公司新定期报告公告日晚于 `ruled_at` 与 `rechecked_at` 的较晚者时到期复看，
队列列 `review_hold_recheck_due`。复看结论提请用户裁定保留、解除或改条件，复看本身登记：

    python3 scripts/review_holds.py --recheck <代码> --rechecked-at YYYY-MM-DD --note "..."
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOLDS = ROOT / "data/reference/review_holds.csv"
RECHECK_FIELDS = ("rechecked_at", "recheck_note")


def recheck_due(hold: dict | None, periodic_notice_date: str | None, periodic_label: str = "") -> str | None:
    """§7.5：未解除行的定期报告公告日晚于 `ruled_at` 与 `rechecked_at` 的较晚者时到期，返回说明。"""
    if not hold or (hold.get("released_at") or "").strip():
        return None
    notice = (periodic_notice_date or "").strip()[:10]
    base = max((hold.get("ruled_at") or "").strip()[:10], (hold.get("rechecked_at") or "").strip()[:10])
    if notice and notice > base:
        return f"{periodic_label.strip() or '定期报告'} {notice} 晚于上次复看 {base or '无'}"
    return None


def record_recheck(code: str, rechecked_at: str, note: str, *, holds: Path = DEFAULT_HOLDS,
                   log_path: Path | None = None) -> dict[str, str]:
    """登记一次复看：只写 RECHECK_FIELDS 两列，其余字节不动，并写决策日志。"""
    from datetime import date, datetime, timezone
    from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log
    code = code.zfill(6)
    date.fromisoformat(rechecked_at)
    if not note.strip():
        raise ValueError("复看须写核对的读数与提请裁定的建议")
    raw = Path(holds).read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    check = io.StringIO(newline="")
    csv.writer(check, lineterminator=newline).writerows(rows)
    if check.getvalue().encode("utf-8") != raw:
        raise ValueError("冻结名单无法逐字节往返，先人工核对文件格式")
    header = rows[0]
    for name in RECHECK_FIELDS:
        if name not in header:
            header.append(name)
            for row in rows[1:]:
                row.append("")
    col = {name: header.index(name) for name in header}
    target = next((r for r in rows[1:] if r[col["security_code"]].zfill(6) == code
                   and not r[col["released_at"]].strip()), None)
    if target is None:
        raise ValueError(f"不是未解除的临时冻结：{code}")
    if rechecked_at < target[col["ruled_at"]][:10] or rechecked_at < target[col["rechecked_at"]][:10]:
        raise ValueError("复看日不得早于裁定日或上次复看日")
    target[col["rechecked_at"]], target[col["recheck_note"]] = rechecked_at, note.strip()
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator=newline).writerows(rows)
    Path(holds).write_bytes(out.getvalue().encode("utf-8"))
    name = target[col["security_name"]]
    append_decision_log(log_path or DEFAULT_DECISION_LOG, [{
        "logged_at_utc": datetime.now(timezone.utc).isoformat(), "workflow_stage": "valuation_review",
        "run_id": f"review_hold_recheck_{rechecked_at}", "as_of": rechecked_at, "security_code": code,
        "security_name": name, "decision_type": "user_review_hold", "decision_result": "rechecked",
        "summary_reason": f"§7.5 临时冻结定期报告后复看：解除条件「{target[col['release_condition']]}」｜{note.strip()}",
        "input_files": str(holds), "source_urls": "", "output_file": str(holds),
        "operator_or_script": "review_holds.py", "workflow_version": WORKFLOW_VERSION,
        "decision_id": f"user_review_hold_recheck:{code}:{rechecked_at}", "supersedes_decision_id": ""}])
    return dict(zip(header, target))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recheck", metavar="代码", required=True, help="登记该临时冻结的定期报告后复看")
    parser.add_argument("--rechecked-at", required=True, help="复看日 YYYY-MM-DD（当晚扫描的证据日）")
    parser.add_argument("--note", required=True, help="核对的读数与提请用户裁定的建议")
    args = parser.parse_args()
    row = record_recheck(args.recheck, args.rechecked_at, args.note)
    print(f"已登记复看：{row['security_code']} {row['security_name']} {row['rechecked_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
