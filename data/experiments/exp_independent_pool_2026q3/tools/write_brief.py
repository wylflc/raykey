#!/usr/bin/env python3
"""OI-291：写批次快照 `<批次>/brief.md`，并刷新 `queue.csv` 的三季报日期（东财预约披露，已披露的记实际日）。

读 build_kit.py 写出的 kit_summary.json（价格、股本、市值、最新报告期）。

    python3 tools/write_brief.py b01 --price-date 2026-10-19
"""
import argparse
import csv
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
SCRATCH = ROOT / 'data/scratch/experiments/exp_independent_pool_2026q3'
QUEUE = EXP / 'queue.csv'


def q3_schedule(codes: list[str]) -> dict[str, str]:
    """代码 → 三季报日期：已披露写「YYYY-MM-DD 已披露」，否则写最新预约日。"""
    out = {}
    for i in range(0, len(codes), 50):
        chunk = codes[i:i + 50]
        flt = "(REPORT_DATE='2026-09-30')(SECURITY_CODE in (" + ",".join(f'"{c}"' for c in chunk) + "))"
        params = dict(reportName='RPT_PUBLIC_BS_APPOIN', columns='SECURITY_CODE,FIRST_APPOINT_DATE,FIRST_CHANGE_DATE,'
                      'SECOND_CHANGE_DATE,THIRD_CHANGE_DATE,ACTUAL_PUBLISH_DATE', filter=flt, pageNumber=1, pageSize=100,
                      source='WEB', client='WEB')
        url = 'https://datacenter-web.eastmoney.com/api/data/v1/get?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read())
        for r in (data.get('result') or {}).get('data') or []:
            if r.get('ACTUAL_PUBLISH_DATE'):
                out[r['SECURITY_CODE']] = f"{r['ACTUAL_PUBLISH_DATE'][:10]} 已披露"
            else:
                appoint = r['THIRD_CHANGE_DATE'] or r['SECOND_CHANGE_DATE'] or r['FIRST_CHANGE_DATE'] or r['FIRST_APPOINT_DATE']
                out[r['SECURITY_CODE']] = f"{(appoint or '')[:10]} 预约"
    return out


def refresh_queue(schedule: dict[str, str]) -> None:
    raw = QUEUE.read_bytes().decode('utf-8')
    rows = list(csv.DictReader(io.StringIO(raw)))
    fields = list(rows[0].keys())
    for r in rows:
        if r['security_code'] in schedule:
            r['q3_notice_date'] = schedule[r['security_code']]
    out = io.StringIO(newline='')
    w = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    QUEUE.write_text(out.getvalue(), encoding='utf-8')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('batch')
    ap.add_argument('--price-date', required=True)
    args = ap.parse_args()
    summary = json.loads((SCRATCH / args.batch / 'kit_summary.json').read_text(encoding='utf-8'))
    queue_codes = [r['security_code'] for r in csv.DictReader(QUEUE.open(encoding='utf-8'))]
    schedule = q3_schedule(queue_codes)
    refresh_queue(schedule)
    raw_rel = (SCRATCH / args.batch / 'raw').relative_to(ROOT)
    work_rel = (SCRATCH / args.batch / 'work').relative_to(ROOT)
    L = [f"# 池内独立审计 {args.batch}：任务说明与快照（价格日 {args.price_date}）\n",
         "OI-291 池内逐家独立审计（深度版）。框架、独立性约束与交付字段见 [`framework.md`](../framework.md)，本文件只给本批快照。\n",
         "## 统一快照\n",
         f"- 价格日：{args.price_date} 收盘（北京时间），A 股未复权；股权成本基准 9%（敏感性 8%／10%）。",
         "- 证据截止：本批取数时已公告的定期报告与公告（三季报已披露的含三季报）；网络事实写明查证日。",
         f"- 原始数据：`{raw_rel}/<代码>/`；草稿与辅助脚本：`{work_rel}/<代码>/`。",
         f"- 交付：`{args.batch}/companies/<代码>_<名称>.md`、`{args.batch}/companies/<代码>.json`、`{args.batch}/calc/<代码>/valuation.py`。\n",
         "| 代码 | 名称 | 收盘价（元） | 总股本（亿股） | A 股价×总股本（亿元） | PE(TTM) | PB | 最新定期报告 | 三季报 | 数据包 |",
         "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |"]
    for s in summary:
        latest = {'09-30': '2026 三季报', '06-30': '2026 中报', '03-31': '2026 一季报', '12-31': '2025 年报'}.get(s['latest'][5:], s['latest'])
        pe = f"{s['pe_ttm']:.1f}" if s.get('pe_ttm') else '—'
        pb = f"{s['pb']:.2f}" if s.get('pb') else '—'
        L.append(f"| {s['code']} | {s['name']} | {s['price']:.2f} | {s['shares_yi']:.4f} | {s['mcap_yi']:,.1f} | {pe} | {pb} | {latest} | "
                 f"{schedule.get(s['code'], '未查到')} | [`packs/{s['code']}_{s['name']}.md`](packs/{s['code']}_{s['name']}.md) |")
    L.append("\n总股本取腾讯行情；有 H 股或其他类别股份的，市值与每股价值按全部股份计算，并写明口径。")
    (EXP / args.batch / 'brief.md').write_text("\n".join(L) + "\n", encoding='utf-8')
    print('写出', EXP / args.batch / 'brief.md')


if __name__ == '__main__':
    main()
