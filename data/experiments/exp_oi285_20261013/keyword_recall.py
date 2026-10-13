"""已知事件窗口内，按 简称／别名／代码 三种关键词检索各自检出的负面标题数（时间排序翻页到窗口起点）。"""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "scripts"))
import screen_pool_events as ev
members, aliases = ev.load_members(), ev.load_aliases()
CASES = [("000895", "2026-05-14", "2026-06-10"), ("601100", "2026-03-18", "2026-04-20"), ("000858", "2026-02-25", "2026-03-15"),
         ("300832", "2026-07-03", "2026-07-20"), ("600436", "2026-10-01", "2026-10-13"), ("002714", "2026-09-01", "2026-10-13"),
         ("002001", "2026-08-01", "2026-10-13"), ("688208", "2025-12-01", "2025-12-20")]
def pull(q, start, maxpages=40):
    out, total = [], 0
    for page in range(1, maxpages + 1):
        for attempt in range(3):
            try:
                rows, total = ev.search_news(q, page, "time"); break
            except Exception:
                rows = []; time.sleep(2)
        out += rows
        if len(rows) < ev.NEWS_PAGE_SIZE or min(r["date"] for r in rows) < start: break
        time.sleep(0.2)
    return out, total, page
for code, start, end in CASES:
    name = ev.clean_name(members[code]); names = [name] + aliases.get(code, [])
    got = {}
    for q in [name] + aliases.get(code, []) + [code]:
        rows, total, pages = pull(q, start)
        hit = {r["url"]: r for r in rows if start <= r["date"] <= end and ev.news_hit(r["title"], names)}
        got[q] = hit
        print(f"{code} {name} [{start}~{end}] 关键词 {q}: total {total} 翻 {pages} 页 命中 {len(hit)} 最早 {min((r['date'] for r in hit.values()), default='-')}")
    union = set().union(*[set(h) for h in got.values()])
    print("   并集", len(union), "| 各自独有:", {q: len(set(h) - set().union(*[set(x) for k, x in got.items() if k != q])) for q, h in got.items()})
