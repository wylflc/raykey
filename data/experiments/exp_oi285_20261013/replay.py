"""OI-285 回放：用生产词表（screen_pool_events）重判一年公告清单与双汇 5 月新闻标题，核对能否在首日检出。

    python3 data/experiments/exp_oi285_20261013/replay.py <全年公告 JSONL>
"""
import collections
import csv
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP.parents[2] / "scripts"))
import screen_pool_events as ev  # noqa: E402

rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
hits = [r for r in rows if ev.announcement_hit(r["title"], r["cols"])]
days = {(r["code"], r["date"]) for r in hits}
print(f"公告 {len(rows)} 条、{len({r['code'] for r in rows})} 家（{min(r['date'] for r in rows)}～{max(r['date'] for r in rows)}）："
      f"命中 {len(hits)} 条、{len({r['code'] for r in hits})} 家、{len(days)} 个公司日、{len({d for _, d in days})} 个日")
listed = list(csv.DictReader(open(EXP / "pool_event_announcements.csv", encoding="utf-8")))
missed = [r for r in listed if not ev.announcement_hit(r["title"], r["columns"].split("|"))]
print(f"首轮回扫清单 {len(listed)} 条：生产词表检出 {len(listed) - len(missed)} 条，漏 {len(missed)} 条")
for r in missed:
    print("  漏：", r["security_name"], r["notice_date"], r["title"][:60])
extra = collections.Counter(r["name"] for r in hits if (r["code"], r["date"], r["title"]) not in
                            {(x["security_code"], x["notice_date"], x["title"]) for x in listed})
print("清单以外新增命中（家：条）：", dict(extra.most_common(12)))
names = ["双汇发展"] + ev.load_aliases().get("000895", [])
first = {}
for line in open(EXP / "shuanghui_may_news.txt", encoding="utf-8"):
    parts = [p.strip() for p in line.split("|")]
    if len(parts) == 3 and ev.news_hit(parts[2], names):
        first.setdefault(parts[0], parts[2])
day = min(first)
print(f"双汇 5 月新闻：{len(first)} 个日有命中，最早 {day}｜{first[day]}")
