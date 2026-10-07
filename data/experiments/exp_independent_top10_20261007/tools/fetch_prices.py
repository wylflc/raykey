#!/usr/bin/env python3
"""Tencent monthly kline (unadjusted + hfq) and spot quote for codes; merges into raw/<code>.json."""
import json, sys, time, urllib.request
from pathlib import Path
OUT = Path(sys.argv[1]); CODES = sys.argv[2].split(',')
H = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}
def sym(c):
    if c.startswith('92'): return 'bj' + c
    return ('sh' if c[0] in '69' else 'sz') + c
def get(url, enc='utf-8'):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30) as r:
                return r.read().decode(enc, 'ignore')
        except Exception as e:
            time.sleep(2)
    return ''
for c in CODES:
    f = OUT / f"{c}.json"; d = json.loads(f.read_text())
    s = sym(c)
    for fq, key in (("", "month"), ("hfq", "hfqmonth")):
        t = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={s},month,2010-01-01,2026-09-30,400,{fq}")
        try:
            data = json.loads(t)["data"][s]
            d[f"tx_{key}"] = data.get(key) or data.get("month") or []
        except Exception as e:
            d[f"tx_{key}"] = []
    t = get(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={s},day,2026-01-01,2026-09-30,400,")
    try:
        data = json.loads(t)["data"][s]; d["tx_day"] = data.get("day") or []
    except Exception:
        d["tx_day"] = []
    q = get(f"https://qt.gtimg.cn/q={s}", 'gbk')
    d["tx_quote"] = q.split('"')[1].split('~') if '"' in q else []
    f.write_text(json.dumps(d, ensure_ascii=False))
    print(c, len(d["tx_month"]), len(d["tx_hfqmonth"]), len(d["tx_day"]), d["tx_quote"][3:4], d["tx_quote"][30:31], d["tx_quote"][44:47])
