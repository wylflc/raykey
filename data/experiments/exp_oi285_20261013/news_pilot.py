"""试跑：全池新闻标题负面词筛查（东财资讯搜索，按公司简称，时间倒序取第一页 100 条）。"""
import csv, json, re, sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from news_probe import search
tiers, out, lo = sys.argv[1:4]
NEG = re.compile("处罚|罚款|罚没|被罚|立案|留置|被查|调查|警示函|监管函|监管措施|问询函|通报|超标|不合格|召回|致歉|道歉|事故|爆炸|起火|火灾|停产|造假|违规|违法|诉讼|仲裁|索赔|制裁|禁令|黑榜|曝光|维权|暴雷|爆雷|失信|冻结|退市|做空|质疑|举报|涉嫌|被执行|裁员|欠薪|中毒|污染")
rows = [(r["security_code"].zfill(6), r["security_name"]) for r in csv.DictReader(open(tiers, encoding="utf-8-sig")) if r["attention_class"] == "worth_attention"]
hits, fails = [], 0
for i, (code, name) in enumerate(rows):
    try:
        res = (search(name, 1, 100).get("result") or {}).get("cmsArticleWebOld") or []
    except Exception as exc:  # noqa: BLE001
        fails += 1; print("FAIL", code, name, exc, flush=True); time.sleep(2); continue
    seen = set()
    for a in res:
        d, t = a.get("date", "")[:10], a.get("title", "")
        if d >= lo and name in t and NEG.search(t) and t not in seen:
            seen.add(t); hits.append(dict(code=code, name=name, date=d, media=a.get("mediaName", ""), title=t, url=a.get("url", "")))
    time.sleep(0.25)
json.dump(hits, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("codes", len(rows), "fails", fails, "hits", len(hits), "companies", len({h["code"] for h in hits}))
import collections
for (code, name), n in collections.Counter((h["code"], h["name"]) for h in hits).most_common():
    print(code, name, n, "|", "；".join(sorted({h["date"][5:] + " " + h["title"][:34] for h in hits if h["code"] == code})[:3]))
