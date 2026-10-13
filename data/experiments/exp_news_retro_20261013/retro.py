"""近 6 个月新闻标题按 §7.4 口径回扫（东财资讯搜索只保留约 6 个月）：代码、简称、别名各检索，时间排序最多 10 页。

    python3 data/experiments/exp_news_retro_20261013/retro.py <输出前缀> [buyline|all] [线程数]

写 `<前缀>_hits.json` 与 `<前缀>_report.txt`。`buyline` 只扫买入线内的池成员与持仓，`all` 扫全部池成员与持仓。
"""
import csv, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import screen_pool_events as ev  # noqa: E402

START, END, LINE = "2025-10-13", "2026-10-13", 1.0034
prefix, scope, workers = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "buyline"), int(sys.argv[3]) if len(sys.argv) > 3 else 4
members, aliases = ev.load_members(), ev.load_aliases()
cand = list(csv.DictReader(open(ROOT / "data/processed/daily_buy_candidates.csv", encoding="utf-8")))
hold = {r["security_code"].zfill(6) for r in csv.DictReader(open(ROOT / "data/processed/a_share_holdings.csv", encoding="utf-8-sig"))}
buyline = {r["security_code"] for r in cand if r["model_pv"] and 0 < float(r["model_pv"]) <= LINE} | hold
codes = sorted(buyline if scope == "buyline" else members)


def one(code):
    name = ev.clean_name(members[code])
    names = [name] + aliases.get(code, [])
    found, reach = {}, {}
    for q in dict.fromkeys([code, *names]):
        oldest, total1 = END, 0
        for page in range(1, 11):
            rows = None
            for attempt in range(3):
                try:
                    rows, total = ev.search_news(q, page, "time")
                    break
                except Exception:   # noqa: BLE001
                    time.sleep(2 * (attempt + 1))
            if rows is None:
                reach[q] = "取数失败"
                break
            if page == 1:
                total1 = total
            for r in rows:
                if START <= r["date"] <= END and ev.news_hit(r["title"], names):
                    found[re.sub(r"\s+", "", r["title"])] = r
            if rows:
                oldest = min(oldest, min(r["date"] for r in rows))
            if len(rows) < ev.NEWS_PAGE_SIZE or oldest < START:
                break
            time.sleep(0.2)
        reach.setdefault(q, f"total {total1}，最早取到 {oldest}")
    return code, members[code], reach, sorted(found.values(), key=lambda r: r["date"])


out, lines = {}, []
with ThreadPoolExecutor(workers) as pool:
    for code, name, reach, rows in pool.map(one, codes):
        out[code] = dict(name=name, in_buy_line=code in buyline, reach=reach, hits=rows)
        lines.append(f"== {code} {name}｜{len(rows)} 条｜" + "；".join(f"{q}: {v}" for q, v in reach.items()))
        lines += [f"    {r['date']} {re.sub(chr(92) + 's+', '', r['title'])[:80]}" for r in rows]
Path(prefix + "_hits.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
Path(prefix + "_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"公司 {len(out)}，有命中 {sum(bool(v['hits']) for v in out.values())}，标题 {sum(len(v['hits']) for v in out.values())}，"
      f"取数失败 {sum('取数失败' in v['reach'].values() for v in out.values())}")
