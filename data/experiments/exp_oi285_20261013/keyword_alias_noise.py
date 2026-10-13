"""近 30 天内，标题只含别名（不含全简称）且命中负面词表的新闻：看别名的误命中有多少。"""
import re, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "scripts"))
import screen_pool_events as ev
members, aliases = ev.load_members(), ev.load_aliases()
START = "2026-09-13"
def one(item):
    code, alias = item
    name = ev.clean_name(members[code]); seen = {}
    for q in (code, name, alias):
        for page in range(1, 11):
            try: rows, total = ev.search_news(q, page, "time")
            except Exception: break
            for r in rows:
                title = re.sub(r"</?em>|\s+", "", r["title"])
                if r["date"] >= START and alias in title and name not in title and ev.news_hit(r["title"], [alias]):
                    seen[r["url"]] = (r["date"], title)
            if len(rows) < 100 or min(x["date"] for x in rows) < START or (page == 1 and total >= 10000 and not any(alias in x["title"] or name in x["title"] for x in rows)): break
            time.sleep(0.2)
    return code, name, alias, sorted(set(seen.values()))
items = [(c, a) for c, al in sorted(aliases.items()) if c in members for a in al]
with ThreadPoolExecutor(4) as pool:
    for code, name, alias, rows in pool.map(one, items):
        print(f"{code} {name}〔{alias}〕 只含别名的负面标题 {len(rows)}")
        for d, t in rows[:6]: print("     ", d, t[:70])
