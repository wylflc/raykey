"""OI-255: build candidate rd_expense supplement rows for Tencent (00700) from HKEX annual reports.

Downloads missing PDFs into raw/ (not committed), extracts text with pypdf, locates the
"Expenses by nature" footnote that states the full-year R&D expense, checks that the next
annual report's comparative matches (no restatement), and writes rd_supplements.csv.
Pop Mart (09992), Haidilao (06862) and OOIL (00316) disclose no R&D total; see rd_supplements.md.

Usage: python3 build_rd_supplements.py   (run from any directory)
"""
import csv
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
TXT = RAW / "txt"
HKEX = "https://www1.hkexnews.hk/listedco/listconews/sehk/"

# fiscal year -> (annual report path, HKEX publication date); annual results announcement likewise
ANNUAL_REPORTS = {
    2017: ("2018/0410/ltn20180410929.pdf", "2018-04-10"),
    2018: ("2019/0401/ltn201904012133.pdf", "2019-04-01"),
    2019: ("2020/0402/2020040201883.pdf", "2020-04-02"),
    2020: ("2021/0408/2021040802045.pdf", "2021-04-08"),
    2021: ("2022/0407/2022040701694.pdf", "2022-04-07"),
    2022: ("2023/0406/2023040601848.pdf", "2023-04-06"),
    2023: ("2024/0408/2024040801822.pdf", "2024-04-08"),
    2024: ("2025/0408/2025040800667.pdf", "2025-04-08"),
    2025: ("2026/0409/2026040901231.pdf", "2026-04-09"),
}
RESULTS_ANNOUNCEMENTS = {
    2017: ("2018/0321/ltn20180321452.pdf", "2018-03-21"),
    2018: ("2019/0321/ltn20190321255.pdf", "2019-03-21"),
    2019: ("2020/0318/2020031800856.pdf", "2020-03-18"),
    2020: ("2021/0324/2021032400488.pdf", "2021-03-24"),
    2021: ("2022/0323/2022032300430.pdf", "2022-03-23"),
    2022: ("2023/0322/2023032200281.pdf", "2023-03-22"),
    2023: ("2024/0320/2024032000508.pdf", "2024-03-20"),
    2024: ("2025/0319/2025031900336.pdf", "2025-03-19"),
    2025: ("2026/0318/2026031800388.pdf", "2026-03-18"),
}
COLUMNS = ["market", "security_code", "security_name", "period", "period_kind", "field", "value", "unit",
           "original_value", "original_unit", "fx_to_report", "evidence_date", "source_url", "source_ref", "note"]

FOOTNOTE = re.compile(
    r"\((?P<letter>[a-z])\) (?P<sentence>During the year ended 31 December (?P<fy>\d{4}), the Group (?:had )?incurred "
    r"expenses for the purpose of (?:research and development|R&D) of approximately RMB(?P<amt>[\d,]+) million "
    r"\((?P<py>\d{4}): RMB(?P<prior>[\d,]+) million\), which (?:mainly )?comprised employee benefits expenses of "
    r"(?:approximately )?RMB(?P<emp>[\d,]+) million \(\d{4}: RMB[\d,]+ million\)\.)")


def pages_text(kind: str, fy: int, rel: str, date: str) -> list[str]:
    stem = f"00700_{kind}{fy}_{date.replace('-', '')}"
    pdf, cache = RAW / f"{stem}.pdf", TXT / f"{stem}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    TXT.mkdir(parents=True, exist_ok=True)
    if not pdf.exists():
        subprocess.run(["curl", "-s", "-L", "--max-time", "300", "-A", "Mozilla/5.0", "-o", str(pdf), HKEX + rel],
                       check=True)
    pages = [p.extract_text() or "" for p in PdfReader(str(pdf)).pages]
    cache.write_text(json.dumps(pages, ensure_ascii=False))
    return pages


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def printed_page(text: str, pdf_page: int) -> str | None:
    """Printed folio from the first/last lines; spreads may carry two numbers, keep the one nearest pdf_page - 1."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    nums = [int(n) for ln in lines[:3] + lines[-3:] if re.fullmatch(r"\d{1,3}(?: \d{1,3})?", ln) for n in ln.split()]
    return str(min(nums, key=lambda n: abs(n - (pdf_page - 1)))) if nums else None


def find_footnote(fy: int) -> dict:
    rel, date = ANNUAL_REPORTS[fy]
    pages = pages_text("AR", fy, rel, date)
    for i, text in enumerate(pages, 1):
        m = FOOTNOTE.search(flat(text))
        if m and int(m.group("fy")) == fy:
            note = None
            for j in (i, i - 1):  # heading sits on the same page or the page before ("continued")
                h = re.search(r"\b(\d{1,2}) EXPENSES BY NATURE", flat(pages[j - 1]))
                if h:
                    note = h.group(1)
                    break
            return {"fy": fy, "page": i, "printed": printed_page(text, i), "note": note, "letter": m.group("letter"),
                    "sentence": m.group("sentence"), "amt": int(m.group("amt").replace(",", "")),
                    "prior": int(m.group("prior").replace(",", "")), "emp": int(m.group("emp").replace(",", "")),
                    "url": HKEX + rel, "date": date}
    raise SystemExit(f"FY{fy}: R&D footnote not found")


def find_in_results(fy: int, amt: int) -> int | None:
    rel, date = RESULTS_ANNOUNCEMENTS[fy]
    key = re.compile(r"purposeof(?:researchanddevelopment|R&D)ofapproximatelyRMB" + f"{amt:,}" + "million")
    for i, text in enumerate(pages_text("RA", fy, rel, date), 1):
        if key.search(re.sub(r"\s+", "", text)):
            return i
    return None


def main() -> None:
    found = {fy: find_footnote(fy) for fy in ANNUAL_REPORTS}
    rows = []
    for fy, f in found.items():
        nxt = found.get(fy + 1)
        if nxt and nxt["prior"] != f["amt"]:
            raise SystemExit(f"FY{fy} restated in FY{fy + 1} report: {f['amt']} -> {nxt['prior']}")
        restate = (f"Not restated: AR{fy + 1} comparative RMB{nxt['prior']:,}m" if nxt
                   else "Latest year, no later report to check restatement")
        ra_page = find_in_results(fy, f["amt"])
        if ra_page is None:
            raise SystemExit(f"FY{fy}: footnote not found in results announcement")
        ra_date = RESULTS_ANNOUNCEMENTS[fy][1]
        value = f["amt"] * 1_000_000
        printed = f" (printed p.{f['printed']})" if f["printed"] else ""
        rows.append({
            "market": "HK", "security_code": "00700", "security_name": "腾讯控股", "period": f"{fy}-12-31",
            "period_kind": "annual", "field": "rd_expense", "value": str(value), "unit": "CNY",
            "original_value": str(value), "original_unit": "CNY", "fx_to_report": "1",
            "evidence_date": f["date"], "source_url": f["url"],
            "source_ref": f"PDF p.{f['page']}{printed} note {f['note']} Expenses by nature, Note ({f['letter']})",
            "note": (f"'{f['sentence']}' No significant development expenses capitalised. Employee benefits "
                     f"{f['emp'] / f['amt']:.0%} of R&D; MD&A cites R&D as the driver of G&A growth. {restate}. Same footnote "
                     f"first published in annual results announcement {ra_date} PDF p.{ra_page}"),
        })
    out = HERE / "rd_supplements.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(r["period"], r["value"], r["evidence_date"], r["source_ref"])
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
