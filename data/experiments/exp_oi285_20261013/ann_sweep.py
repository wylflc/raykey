"""一次性回扫：池成员一年内的全部交易所公告（东财公告列表，按代码），写 JSONL 供本地筛关键词。"""
import csv, json, sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from ann_probe import page

tiers, out, begin, end = sys.argv[1:5]
codes = [(r["security_code"].zfill(6), r["security_name"]) for r in csv.DictReader(open(tiers, encoding="utf-8-sig"))
         if r["attention_class"] == "worth_attention"]
n = 0
with open(out, "w", encoding="utf-8") as fh:
    for i, (code, name) in enumerate(codes):
        idx, got, total = 1, 0, None
        while True:
            for attempt in range(4):
                try:
                    d = (page(code, begin, end, idx).get("data") or {})
                    break
                except Exception as exc:                      # noqa: BLE001
                    if attempt == 3:
                        raise
                    time.sleep(2 * (attempt + 1))
            rows = d.get("list") or []
            total = d.get("total_hits") if total is None else total
            for a in rows:
                fh.write(json.dumps(dict(code=code, name=name, date=a["notice_date"][:10], art=a["art_code"],
                                         cols=[c["column_name"] for c in a.get("columns") or []], title=a["title"]),
                                    ensure_ascii=False) + "\n")
            got += len(rows)
            n += len(rows)
            if not rows or got >= (total or 0):
                break
            idx += 1
            time.sleep(0.1)
        if got != (total or 0):
            print(f"WARN {code} {name} got {got} total {total}", flush=True)
        if i % 30 == 0:
            print(i, code, name, got, flush=True)
        time.sleep(0.1)
print("codes", len(codes), "rows", n)
