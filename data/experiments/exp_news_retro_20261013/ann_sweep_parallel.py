"""池成员某一时间段的全部交易所公告标题（东财公告列表，按代码并行），写 JSONL 供本地筛关键词。

    python3 -I data/experiments/exp_news_retro_20261013/ann_sweep_parallel.py <分层表> <输出 jsonl> <起始日> <截止日> [线程数]
"""
import csv, json, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp_oi286_20261013"))
from ann_probe import page  # noqa: E402

tiers, out, begin, end = sys.argv[1:5]
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 8
codes = [(r["security_code"].zfill(6), r["security_name"]) for r in csv.DictReader(open(tiers, encoding="utf-8-sig"))
         if r["attention_class"] == "worth_attention"]


def one(item):
    code, name = item
    idx, got, total, rows_out = 1, 0, None, []
    while True:
        for attempt in range(4):
            try:
                d = (page(code, begin, end, idx).get("data") or {})
                break
            except Exception:   # noqa: BLE001
                if attempt == 3:
                    return code, name, rows_out, f"取数失败（第 {idx} 页）"
                time.sleep(2 * (attempt + 1))
        rows = d.get("list") or []
        total = d.get("total_hits") if total is None else total
        rows_out += [dict(code=code, name=name, date=a["notice_date"][:10], art=a["art_code"],
                          cols=[c["column_name"] for c in a.get("columns") or []], title=a["title"]) for a in rows]
        got += len(rows)
        if not rows or got >= (total or 0):
            break
        idx += 1
    return code, name, rows_out, "" if got == (total or 0) else f"取到 {got}，接口报 {total}"


n = 0
with ThreadPoolExecutor(workers) as pool, open(out, "w", encoding="utf-8") as fh:
    for code, name, rows, warn in pool.map(one, codes):
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += len(rows)
        if warn:
            print("WARN", code, name, warn, flush=True)
print("codes", len(codes), "rows", n)
