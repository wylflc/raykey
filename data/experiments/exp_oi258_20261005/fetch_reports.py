#!/usr/bin/env python3
"""OI-258 取数：在巨潮定位五家保险的年报／半年报原文并下载到 raw/（不入库）。

用法：python3 fetch_reports.py locate   # 串行查询，写 raw/reports_index.csv
      python3 fetch_reports.py download # 按索引下载 PDF（已存在则跳过）
"""
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
INDEX = RAW / "reports_index.csv"
CODES = {"601318": "中国平安", "601601": "中国太保", "601628": "中国人寿", "601336": "新华保险", "601319": "中国人保"}
CATS = {"FY": "category_ndbg_szsh", "H1": "category_bndbg_szsh"}
UA = {"User-Agent": "Mozilla/5.0"}


def http(url, data=None, tries=4, timeout=60):
    for attempt in range(tries):
        try:
            headers = dict(UA)
            if data is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout).read()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def org_id(code):
    data = urllib.parse.urlencode(dict(keyWord=code, maxNum=5)).encode()
    hits = json.loads(http("http://www.cninfo.com.cn/new/information/topSearch/query", data))
    return next(h["orgId"] for h in hits if h.get("code") == code)


def query(code, org, cat, year):
    out, page = [], 1
    while True:
        data = urllib.parse.urlencode(dict(pageNum=page, pageSize=30, column="sse", tabName="fulltext", plate="",
                                           stock=f"{code},{org}", searchkey="", secid="", category=cat, trade="",
                                           seDate=f"{year}-01-01~{year}-12-31", sortName="", sortType="",
                                           isHLtitle="true")).encode()
        js = json.loads(http("http://www.cninfo.com.cn/new/hisAnnouncement/query", data))
        rows = js.get("announcements") or []
        out += rows
        total = js.get("totalAnnouncement") or 0
        time.sleep(0.4)
        if page * 30 >= total or not rows:
            return out
        page += 1


def locate():
    RAW.mkdir(exist_ok=True)
    recs = []
    for code, name in CODES.items():
        org = org_id(code)
        for ptype, cat in CATS.items():
            for year in range(2014, 2027):
                for a in query(code, org, cat, year):
                    title = re.sub(r"</?em>", "", a.get("announcementTitle") or "")
                    url = a.get("adjunctUrl") or ""
                    m = re.search(r"(\d{4}-\d{2}-\d{2})", url)
                    recs.append(dict(code=code, name=name, ptype=ptype, pub_date=m.group(1) if m else "", title=title,
                                     url="http://static.cninfo.com.cn/" + url, size_kb=a.get("adjunctSize") or ""))
        print(code, name, len([r for r in recs if r["code"] == code]), flush=True)
    seen, uniq = set(), []
    for r in recs:
        if r["url"] not in seen:
            seen.add(r["url"])
            uniq.append(r)
    with INDEX.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(uniq[0]))
        w.writeheader()
        w.writerows(sorted(uniq, key=lambda r: (r["code"], r["ptype"], r["pub_date"])))
    print("index rows", len(uniq))


def main_reports():
    """每期一份原文：标题含「年度报告」或「半年度报告」，排除摘要、英文、提示性公告。"""
    rows = list(csv.DictReader(INDEX.open(encoding="utf-8")))
    keep = []
    for r in rows:
        t = r["title"]
        if re.search(r"摘要|英文|English|提示|公告$|问询|说明|意见", t):
            continue
        m = re.search(r"(20\d\d)\s*年?\s*(半年度报告|中期报告|年度报告|年报|半年报)", t)
        if not m:
            continue
        year = int(m.group(1))
        is_h1 = "半年" in m.group(2) or "中期" in m.group(2)
        ptype = "H1" if is_h1 else "FY"
        if ptype != r["ptype"]:
            continue
        r["year"] = year
        if (ptype == "FY" and 2014 <= year <= 2025) or (ptype == "H1" and 2015 <= year <= 2026):
            keep.append(r)
    best = {}
    for r in keep:      # 同期多份（如人保 2021 半年报摘要误题）取体量最大者
        key = (r["code"], r["ptype"], r["year"])
        if key not in best or float(r["size_kb"] or 0) > float(best[key]["size_kb"] or 0):
            best[key] = r
    return [best[k] for k in sorted(best)]


def download():
    for r in main_reports():
        fn = RAW / r["code"] / f"{r['year']}{r['ptype']}_{r['pub_date']}_{Path(r['url']).stem}.pdf"
        fn.parent.mkdir(exist_ok=True)
        if fn.exists() and fn.stat().st_size > 10000:
            continue
        fn.write_bytes(http(r["url"], timeout=300))
        print("got", fn.name, r["title"], flush=True)
        time.sleep(0.3)


def pages_text(pdf, first=1, last=150):
    """逐页文本缓存（raw/<code>/<stem>.pages.json.gz，键为 PDF 物理页码，从 1 起）。"""
    import gzip
    from pypdf import PdfReader
    cache = pdf.with_suffix(".pages.json.gz")
    try:
        pages = json.loads(gzip.decompress(cache.read_bytes())) if cache.exists() else {}
    except Exception:
        pages = {}
    reader = None
    for i in range(first, last + 1):
        if str(i) in pages:
            continue
        reader = reader or PdfReader(str(pdf))
        if i > len(reader.pages):
            break
        try:
            pages[str(i)] = reader.pages[i - 1].extract_text() or ""
        except Exception as exc:  # 个别页解析失败，记空串
            pages[str(i)] = f"<<extract error {exc}>>"
    if reader is not None:
        import os
        tmp = cache.with_name(cache.name + f".tmp{os.getpid()}")
        tmp.write_bytes(gzip.compress(json.dumps(pages, ensure_ascii=False).encode("utf-8")))
        os.replace(tmp, cache)  # 原子替换，避免并发读到半截文件
    return pages


def text():
    pdfs = sorted(RAW.glob("*/*.pdf"), key=lambda p: ("FY" not in p.name, p.name))
    for pdf in pdfs:
        t = time.time()
        pages_text(pdf, 1, int(sys.argv[2]) if len(sys.argv) > 2 else 150)
        print(f"{pdf.parent.name}/{pdf.name} {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__":
    {"locate": locate, "download": download, "text": text}[sys.argv[1]]()
