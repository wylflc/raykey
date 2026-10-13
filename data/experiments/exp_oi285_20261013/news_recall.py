import sys, time, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from news_probe import search
kw, name, lo, hi, maxpages = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
seen, hits, pages = set(), [], 0
for p in range(1, maxpages + 1):
    r = search(kw, p, 100)
    res = (r.get("result") or {}).get("cmsArticleWebOld") or []
    pages = p
    if not res:
        break
    for a in res:
        d, t = a.get("date", "")[:10], a.get("title", "")
        if name in t and (d, t) not in seen:
            seen.add((d, t)); hits.append((d, a.get("mediaName", ""), t))
    last = res[-1].get("date", "")[:10]
    if last < lo:
        break
    time.sleep(0.2)
print("pages", pages, "hitsTotal", r.get("hitsTotal"), "last date", last, "titles with name", len(hits))
by = collections.Counter(d[:7] for d, _, _ in hits)
print(sorted(by.items()))
for d, m, t in sorted(hits):
    if lo <= d <= hi:
        print(d, "|", m, "|", t[:56])
