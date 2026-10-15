#!/usr/bin/env python3
"""Materialize A-share earnings preannouncements (业绩预告) from Eastmoney.

Feeds the §7.5.1 express-review queue and the pool refresh summary (§7.1).
Re-run every scan day per §9.1 step 0 — disclosures arrive daily, and a stale
file silently closes the §7.4/§7.5.1 event inlet. Raw-first: the full-market
forecast list for one report date is saved with provenance (retrieval time,
source); consumers filter by their own code lists. Field notes (validated
2026-07-17): PREDICT_FINANCE_CODE 004=归母净利, 005=扣非净利, 006=营业收入;
amounts in CNY; PREYEAR_SAME_PERIOD = 去年同期值.

§6.4 预告补录（OI-288）：同批取东财公告「业绩预告」栏目（自报告期末起），预告表与补录表
（`data/reference/forecast_supplements.csv`）都对不上的公告写入 `a_share_forecast_unregistered.csv`，
由队列冻结；补录表 `disposition = 叠加` 的行按预告表字段并入输出（`source = 补录:<公告编号>`）。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data/interim/a_share_earnings_forecasts.csv"
DEFAULT_SUPPLEMENTS = ROOT / "data/reference/forecast_supplements.csv"
DEFAULT_UNREGISTERED = ROOT / "data/interim/a_share_forecast_unregistered.csv"
API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
ANN_URL = "https://np-anotice-stock.eastmoney.com/api/security/ann"
SUPPLEMENT_FIELDS = ["security_code", "security_name", "report_date", "notice_date", "art_code", "disposition",
                     "predict_type", "predict_amt_lower", "predict_amt_upper", "basis", "registered_at", "note"]
DISPOSITIONS = ("叠加", "不叠加")
UNREGISTERED_FIELDS = ["security_code", "security_name", "report_date", "notice_date", "title", "art_code", "url",
                       "retrieved_at_utc"]
MATCH_DAYS = 3   # 栏目公告与预告表、补录表按代码与公告日相差不超过此天数对应
A_SHARE_CODE = re.compile(r"(?:00|30|60|68|92)\d{4}")

FIELDNAMES = [
    "security_code",
    "security_name",
    "report_date",
    "notice_date",
    "predict_finance_code",
    "predict_finance",
    "predict_type",
    "predict_amt_lower",
    "predict_amt_upper",
    "add_amp_lower",
    "add_amp_upper",
    "preyear_same_period",
    "is_latest",
    "source",
    "retrieved_at_utc",
]


def latest_ended_quarter_end(today: date | None = None) -> str:
    """最近一个已结束的季度报告期末（§9.1 步骤 0 缺省口径）。"""
    current = today or datetime.now(timezone.utc).date()
    for month, day in ((9, 30), (6, 30), (3, 31)):
        end = date(current.year, month, day)
        if current > end:
            return end.isoformat()
    return f"{current.year - 1}-12-31"


def fetch_pages(report_date: str, timeout: float, page_size: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {
                "sortColumns": "NOTICE_DATE,SECURITY_CODE",
                "sortTypes": "-1,1",
                "pageSize": page_size,
                "pageNumber": page,
                "reportName": "RPT_PUBLIC_OP_NEWPREDICT",
                "columns": "ALL",
                "filter": f"(REPORT_DATE='{report_date}')",
            }
        )
        request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", "ignore"))
        data = ((payload.get("result") or {}).get("data")) or []
        rows.extend(data)
        pages = int((payload.get("result") or {}).get("pages") or 0)
        if page >= pages or not data:
            return rows
        page += 1


def fetch_preview_announcements(begin: str, end: str, timeout: float) -> list[dict[str, object]]:
    """东财公告「业绩预告」栏目（f_node=1、s_node=5）全市场 [begin, end]；分页不全即报错。"""
    rows: list[dict[str, object]] = []
    page, total = 1, 0
    while page <= 500:
        query = urllib.parse.urlencode(dict(sr=-1, page_size=100, page_index=page, ann_type="A", client_source="web",
                                            f_node=1, s_node=5, begin_time=begin, end_time=end))
        request = urllib.request.Request(f"{ANN_URL}?{query}", headers={"User-Agent": "Mozilla/5.0"})
        for attempt in (1, 2, 3):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    data = json.loads(response.read().decode("utf-8", "ignore")).get("data") or {}
                break
            except (TimeoutError, OSError, ValueError):
                if attempt == 3:
                    raise
        items, total = data.get("list") or [], int(data.get("total_hits") or 0)
        rows.extend(items)
        if not items or len(rows) >= total:
            break
        page += 1
    if len(rows) < total:
        raise RuntimeError(f"「业绩预告」栏目公告分页不全：取到 {len(rows)} 条，接口报 {total} 条")
    return rows


def title_period(title: str) -> str | None:
    """公告标题所指报告期末；识别不出（无年份、1-2 月一类非报告期）返回 None。"""
    match = re.search(r"(20\d{2})\s*年", title)
    if not match:
        return None
    year, rest = match.group(1), title[match.end():].lstrip()
    if re.match(r"(?:前三季度|第三季度|三季度)", rest):
        return f"{year}-09-30"
    if re.match(r"(?:半年|上半年|中期|第二季度|二季度)", rest):
        return f"{year}-06-30"
    if re.match(r"(?:第一季度|一季度)", rest):
        return f"{year}-03-31"
    if re.match(r"(?:度|年度|全年|第四季度|四季度)", rest):
        return f"{year}-12-31"
    return None


def _near(day: str, other: str) -> bool:
    try:
        return abs((date.fromisoformat(day[:10]) - date.fromisoformat(other[:10])).days) <= MATCH_DAYS
    except ValueError:
        return False


def load_supplements(path: Path) -> list[dict[str, str]]:
    """读补录表并校验；`叠加` 行须给报告期累计归母净利上下限（元）。"""
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        code = (row.get("security_code") or "").strip()
        if not re.fullmatch(r"\d{6}", code) or row.get("disposition") not in DISPOSITIONS:
            raise ValueError(f"补录表行无效（代码或处置）：{row}")
        date.fromisoformat((row.get("report_date") or "")[:10])
        date.fromisoformat((row.get("notice_date") or "")[:10])
        if row["disposition"] == "叠加":
            lower, upper = float(row["predict_amt_lower"]), float(row["predict_amt_upper"])
            if lower > upper:
                raise ValueError(f"补录表下限高于上限：{code}")
    return rows


def merge_supplements(table_rows: list[dict[str, object]], supplements: list[dict[str, str]], report_date: str,
                      retrieved_at: str) -> list[dict[str, object]]:
    """本报告期 `叠加` 行并入预告表行。表内已有该代码归母预告（004、is_latest=T）且公告日不早于补录的，
    以表内为准；补录更晚的，表内该代码归母行改 is_latest=F。"""
    latest: dict[str, str] = {}
    for row in table_rows:
        if row.get("predict_finance_code") == "004" and row.get("is_latest") == "T":
            code = str(row["security_code"])
            latest[code] = max(latest.get(code, ""), str(row.get("notice_date") or "")[:10])
    added: list[dict[str, object]] = []
    for sup in supplements:
        code, notice = sup["security_code"].strip(), sup["notice_date"][:10]
        if sup["disposition"] != "叠加" or sup["report_date"][:10] != report_date or latest.get(code, "") >= notice:
            continue
        added.append({
            "security_code": code, "security_name": sup.get("security_name", ""), "report_date": report_date,
            "notice_date": notice, "predict_finance_code": "004", "predict_finance": "归属于上市公司股东的净利润",
            "predict_type": sup.get("predict_type", ""), "predict_amt_lower": sup["predict_amt_lower"],
            "predict_amt_upper": sup["predict_amt_upper"], "add_amp_lower": "", "add_amp_upper": "",
            "preyear_same_period": "", "is_latest": "T", "source": f"补录:{sup.get('art_code', '')}",
            "retrieved_at_utc": retrieved_at,
        })
    superseded = {str(row["security_code"]) for row in added} & set(latest)
    for row in table_rows:
        if str(row["security_code"]) in superseded and row.get("predict_finance_code") == "004":
            row["is_latest"] = "F"
    return table_rows + added


def unregistered_announcements(announcements: list[dict[str, object]], table_rows: list[dict[str, object]],
                               supplements: list[dict[str, str]], report_date: str,
                               retrieved_at: str) -> list[dict[str, str]]:
    """「业绩预告」栏目中标题所指报告期为本期或识别不出、预告表与补录表都对不上的 A 股公告（业绩说明会除外）。"""
    table: dict[str, list[str]] = {}
    for row in table_rows:
        table.setdefault(str(row["security_code"]), []).append(str(row.get("notice_date") or "")[:10])
    registered_arts = {(s.get("art_code") or "").strip() for s in supplements} - {""}
    registered: dict[str, list[str]] = {}
    for sup in supplements:
        registered.setdefault(sup["security_code"].strip(), []).append(sup["notice_date"][:10])
    out: dict[tuple[str, str], dict[str, str]] = {}
    for item in announcements:
        title = re.sub(r"</?em>", "", str(item.get("title") or item.get("title_ch") or ""))
        art = str(item.get("art_code") or "")
        notice = str(item.get("notice_date") or "")[:10]
        if "说明会" in title or title_period(title) not in (None, report_date) or art in registered_arts:
            continue
        for entry in item.get("codes") or []:
            code = str(entry.get("stock_code") or "")
            if not A_SHARE_CODE.fullmatch(code):
                continue
            if any(_near(notice, d) for d in table.get(code, [])) or any(_near(notice, d) for d in registered.get(code, [])):
                continue
            out[(code, art)] = dict(security_code=code, security_name=str(entry.get("short_name") or ""),
                                    report_date=report_date, notice_date=notice, title=title, art_code=art,
                                    url=f"https://pdf.dfcfw.com/pdf/H2_{art}_1.pdf" if art else "",
                                    retrieved_at_utc=retrieved_at)
    return sorted(out.values(), key=lambda r: (r["notice_date"], r["security_code"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-date",
        default=None,
        help="报告期，如 2026-06-30（中报）；缺省自动取最近一个已结束的季度报告期末。",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--signal-date", default=None, help="本次服务的信号日，用于同日证据凭据")
    parser.add_argument("--supplements", type=Path, default=DEFAULT_SUPPLEMENTS, help="§6.4 预告补录表（人工登记）")
    parser.add_argument("--unregistered-output", type=Path, default=DEFAULT_UNREGISTERED,
                        help="§6.4 「业绩预告」栏目中表外且未登记补录表的公告")
    args = parser.parse_args()

    report_date = args.report_date or latest_ended_quarter_end()
    supplements = load_supplements(args.supplements)
    raw = fetch_pages(report_date, args.timeout, args.page_size)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_rows = [
        {
            "security_code": str(item.get("SECURITY_CODE", "")).zfill(6),
            "security_name": item.get("SECURITY_NAME_ABBR", ""),
            "report_date": str(item.get("REPORT_DATE", ""))[:10],
            "notice_date": str(item.get("NOTICE_DATE", ""))[:10],
            "predict_finance_code": item.get("PREDICT_FINANCE_CODE", ""),
            "predict_finance": item.get("PREDICT_FINANCE", ""),
            "predict_type": item.get("PREDICT_TYPE", ""),
            "predict_amt_lower": item.get("PREDICT_AMT_LOWER", ""),
            "predict_amt_upper": item.get("PREDICT_AMT_UPPER", ""),
            "add_amp_lower": item.get("ADD_AMP_LOWER", ""),
            "add_amp_upper": item.get("ADD_AMP_UPPER", ""),
            "preyear_same_period": item.get("PREYEAR_SAME_PERIOD", ""),
            "is_latest": item.get("IS_LATEST", ""),
            "source": "eastmoney:RPT_PUBLIC_OP_NEWPREDICT",
            "retrieved_at_utc": retrieved_at,
        }
        for item in raw
    ]
    if args.signal_date:
        from a_share_signal_dates import evidence_iso_for_signal
        end = evidence_iso_for_signal(args.signal_date)
    else:
        end = (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()
    announcements = fetch_preview_announcements(report_date, end, args.timeout)
    unregistered = unregistered_announcements(announcements, out_rows, supplements, report_date, retrieved_at)
    table_count = len(out_rows)
    out_rows = merge_supplements(out_rows, supplements, report_date, retrieved_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(out_rows)
    args.unregistered_output.parent.mkdir(parents=True, exist_ok=True)
    with args.unregistered_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=UNREGISTERED_FIELDS)
        writer.writeheader()
        writer.writerows(unregistered)
    from daily_execution_guard import stamp
    inputs = (args.supplements,) if args.supplements.exists() else ()
    stamp(args.output, args.signal_date, inputs)
    stamp(args.unregistered_output, args.signal_date, inputs)
    print(f"wrote {len(out_rows)} forecast rows (report_date={report_date}; 预告表 {table_count}、补录 "
          f"{len(out_rows) - table_count}) to {args.output}；「业绩预告」栏目 {len(announcements)} 条，"
          f"表外未登记 {len(unregistered)} 条 → {args.unregistered_output}")


if __name__ == "__main__":
    main()
