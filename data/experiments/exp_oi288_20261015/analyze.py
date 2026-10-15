"""汇总 OI-288 频率核查：池成员与全市场的预告／快报栏目公告中，东财表未收录的比例与形态。"""
import csv, re, sys, collections

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
# 同一公告可能挂多个代码（A+H 等），按 (kind, code, art) 去重
seen, uniq = set(), []
for r in rows:
    k = (r["kind"], r["code"], r["art"])
    if k not in seen:
        seen.add(k)
        uniq.append(r)
rows = uniq

def shape(t):
    if re.search("更正|补充|修正|取消", t):
        return "更正/补充"
    if re.search("第[一二三四]季度|[一二三四]季度(?!报)|单季", t) and not re.search("前三季度|半年度|年度", t.replace("第三季度", "")):
        return "单季"
    if "自愿" in t:
        return "自愿·累计"
    return "常规"

def season(nd):
    y, m = int(nd[:4]), int(nd[5:7])
    if m in (1, 2, 3, 4):
        return f"{y - 1}年报/{y}Q1"
    if m in (5, 6, 7, 8, 9):
        return f"{y}H1"
    return f"{y}Q3"

for scope in ("pool", "market"):
    sub = [r for r in rows if scope == "market" or r["pool"] == "yes"]
    for kind in ("forecast", "express"):
        s = [r for r in sub if r["kind"] == kind]
        miss = [r for r in s if not r["in_table"]]
        print(f"== {scope} {kind}: 公告 {len(s)}，表内无对应行 {len(miss)}（{len(miss) / max(len(s), 1):.1%}）")
        c = collections.Counter(shape(r["title"]) for r in miss)
        print("   未收录形态：", dict(c))
        c2 = collections.Counter(shape(r["title"]) for r in s)
        print("   全部形态：", dict(c2))
        if scope == "pool":
            for r in sorted(miss, key=lambda r: r["notice_date"]):
                print("   ", r["notice_date"], r["code"], r["name"], r["title"][:70])
            bys = collections.Counter(season(r["notice_date"]) for r in miss if shape(r["title"]) != "更正/补充")
            print("   按季（不含更正补充）：", dict(sorted(bys.items())))
