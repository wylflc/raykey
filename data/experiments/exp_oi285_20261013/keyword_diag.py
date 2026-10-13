"""全池逐家对比：简称检索与代码检索第一页（时间排序）的命中数、标题含名称的条数、最新日期。"""
import json, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "scripts"))
import screen_pool_events as ev

members = ev.load_members()
aliases = ev.load_aliases()

def one(kv):
    code, name = kv
    kw = ev.clean_name(name)
    names = [kw] + aliases.get(code, [])
    out = dict(security_code=code, security_name=name)
    for label, q in (("name", kw), ("code", code)):
        for attempt in range(3):
            try:
                rows, total = ev.search_news(q, 1, "time")
                break
            except Exception as e:
                rows, total = [], -1
                time.sleep(2 * (attempt + 1))
        inname = [r for r in rows if any(n in r["title"].replace(" ", "") for n in names)]
        out[label] = dict(total=total, n=len(rows), titled=len(inname),
                          newest=max((r["date"] for r in rows), default=""),
                          oldest=min((r["date"] for r in rows), default=""),
                          newest_titled=max((r["date"] for r in inname), default=""))
        time.sleep(0.2)
    return out

with ThreadPoolExecutor(4) as pool:
    res = list(pool.map(one, sorted(members.items())))
json.dump(res, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
cap = [r for r in res if r["name"]["total"] >= 10000]
print("成员", len(res), "简称命中到上限", len(cap))
for r in cap:
    print("  ", r["security_code"], r["security_name"], "| 简称 titled", r["name"]["titled"], "| 代码 total", r["code"]["total"], "titled", r["code"]["titled"], "newest", r["code"]["newest_titled"])
