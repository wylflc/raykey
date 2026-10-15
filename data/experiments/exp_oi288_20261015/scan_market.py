"""OI-288 频率核查：全市场近 3 年「业绩预告」「业绩快报」栏目公告（东财公告 f_node=1, s_node=5/6），
对照东财预告表 RPT_PUBLIC_OP_NEWPREDICT 与快报表 RPT_FCI_PERFORMANCEE 是否在公告日 ±3 天内有该公司的行。"""
import csv, json, re, sys, time, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
ANN_URL = "https://np-anotice-stock.eastmoney.com/api/security/ann"
API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
BEGIN, END = "2023-10-15", "2026-10-15"


def get(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return json.loads(urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace"))
        except Exception:
            time.sleep(2 + 2 * i)
    raise RuntimeError(url)


def anns(snode, begin, end):
    out, page, total = [], 1, 0
    while True:
        q = urllib.parse.urlencode(dict(sr=-1, page_size=100, page_index=page, ann_type="A", client_source="web",
                                        f_node=1, s_node=snode, begin_time=begin, end_time=end))
        d = get(ANN_URL + "?" + q).get("data") or {}
        rows, total = d.get("list") or [], int(d.get("total_hits") or 0)
        out.extend(rows)
        if not rows or len(out) >= total or page >= 200:
            return out, total
        page += 1
        time.sleep(0.1)


windows = []
for y in (2023, 2024, 2025, 2026):
    for a, b in (("01-01", "01-31"), ("02-01", "03-31"), ("04-01", "04-30"), ("05-01", "06-30"), ("07-01", "07-31"),
                 ("08-01", "09-30"), ("10-01", "10-31"), ("11-01", "12-31")):
        s, e = f"{y}-{a}", f"{y}-{b}"
        if e < BEGIN or s > END:
            continue
        windows.append((max(s, BEGIN), min(e, END)))

items = []
for snode, kind in ((5, "forecast"), (6, "express")):
    for s, e in windows:
        rows, total = anns(snode, s, e)
        for it in rows:
            t = re.sub(r"</?em>", "", it.get("title") or "")
            for c in it.get("codes") or []:
                code = c.get("stock_code") or ""
                if re.fullmatch(r"\d{6}", code):
                    items.append(dict(kind=kind, code=code, name=c.get("short_name") or "",
                                      notice_date=(it.get("notice_date") or "")[:10],
                                      display_time=(it.get("display_time") or "")[:19], title=t, art=it.get("art_code") or ""))
        print(kind, s, e, len(rows), total, file=sys.stderr, flush=True)


def table(report, rdate):
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({"sortColumns": "NOTICE_DATE,SECURITY_CODE", "sortTypes": "-1,1", "pageSize": 500,
                                    "pageNumber": page, "reportName": report,
                                    "columns": "SECURITY_CODE,NOTICE_DATE,REPORT_DATE", "filter": f"(REPORT_DATE='{rdate}')"})
        p = get(API + "?" + q)
        data = ((p.get("result") or {}).get("data")) or []
        out.extend(data)
        if page >= int((p.get("result") or {}).get("pages") or 0) or not data:
            return out
        page += 1


periods = ["2023-09-30", "2023-12-31", "2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31", "2025-03-31",
           "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30", "2026-09-30"]
fc, ex = {}, {}
for p in periods:
    for r in table("RPT_PUBLIC_OP_NEWPREDICT", p):
        fc.setdefault(r["SECURITY_CODE"], set()).add((p, (r.get("NOTICE_DATE") or "")[:10]))
    for r in table("RPT_FCI_PERFORMANCEE", p):
        ex.setdefault(r["SECURITY_CODE"], set()).add((p, (r.get("NOTICE_DATE") or "")[:10]))
    print("table", p, file=sys.stderr, flush=True)


def near(sets, code, nd):
    d0 = date.fromisoformat(nd)
    return sorted({(p, d) for p, d in sets.get(code, set()) if d and abs((date.fromisoformat(d) - d0).days) <= 3})


pool = {r["security_code"] for r in csv.DictReader(open(ROOT / "data/processed/a_share_core_valuation_pool.csv",
                                                         encoding="utf-8-sig"))}
for it in items:
    hits = near(fc if it["kind"] == "forecast" else ex, it["code"], it["notice_date"])
    it["in_table"] = ";".join(f"{p}@{d}" for p, d in hits)
    it["pool"] = "yes" if it["code"] in pool else ""
with OUT.open("w", encoding="utf-8", newline="") as h:
    w = csv.DictWriter(h, fieldnames=list(items[0].keys()))
    w.writeheader()
    w.writerows(items)
print("done", len(items), file=sys.stderr)
