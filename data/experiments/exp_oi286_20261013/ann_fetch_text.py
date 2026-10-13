"""下载东财公告 PDF（各放独立目录）并打印正文前若干字。用法：ann_fetch_text.py <outdir> <chars> <art_code>..."""
import os, re, sys, urllib.request
from pypdf import PdfReader
out, limit = sys.argv[1], int(sys.argv[2])
for art in sys.argv[3:]:
    d = os.path.join(out, art); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "doc.pdf")
    if not os.path.exists(p):
        req = urllib.request.Request(f"https://pdf.dfcfw.com/pdf/H2_{art}_1.pdf", headers={"User-Agent": "Mozilla/5.0"})
        open(p, "wb").write(urllib.request.urlopen(req, timeout=60).read())
    try:
        r = PdfReader(p)
        text = re.sub(r"\s+", "", "".join((pg.extract_text() or "") for pg in r.pages))
        print(f"=== {art} pages={len(r.pages)} chars={len(text)}\n{text[:limit]}\n")
    except Exception as exc:  # noqa: BLE001
        print(f"=== {art} ERROR {exc}")
