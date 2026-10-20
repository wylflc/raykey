#!/usr/bin/env python3
"""OI-291：按 README「范围与顺序」列出下一批候选。只读；加 --refresh 时先刷新 queue.csv 的三季报日期。

模型 `P/V` = 最近一次扫描的估值价（池 CSV 的 valuation_price）÷ 模型带中值（intrinsic_value），只供主会话排序。

    python3 tools/next_batch.py [--refresh] [--n 8]
"""
import argparse
import csv
import math
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(TOOLS))
import write_brief  # noqa: E402

POOL = ROOT / 'data/processed/a_share_core_valuation_pool.csv'
BANDS = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
LATE = '2026-10-27'
FINANCIAL = '银行/保险'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true', help='先按东财预约披露表刷新 queue.csv 的三季报日期（联网）')
    ap.add_argument('--n', type=int, default=8, help='每组列出的家数')
    args = ap.parse_args()
    if args.refresh:
        codes = [r['security_code'] for r in csv.DictReader(write_brief.QUEUE.open(encoding='utf-8'))]
        write_brief.refresh_queue(write_brief.q3_schedule(codes))
    queue = list(csv.DictReader(write_brief.QUEUE.open(encoding='utf-8')))
    pool = {r['security_code'].zfill(6): r for r in csv.DictReader(POOL.open(encoding='utf-8'))}
    bands = {r['security_code'].zfill(6): r for r in csv.DictReader(BANDS.open(encoding='utf-8'))}

    def pv(code: str) -> float:
        try:
            return float(pool[code]['valuation_price']) / float(bands[code]['intrinsic_value'])
        except (KeyError, ValueError, ZeroDivisionError):
            return math.nan

    def key(r: dict) -> tuple:
        x = pv(r['security_code'])
        return (math.isnan(x), x)

    def show(title: str, rows: list[dict], n: int) -> None:
        print(f'{title}：{len(rows)} 家')
        for r in sorted(rows, key=key)[:n]:
            print(f"  {pv(r['security_code']):.3f}  {r['security_code']} {r['security_name']}  {r['status']}  "
                  f"{r['q3_notice_date']}  {r['valuation_path']}")

    disclosed = [r for r in queue if r['q3_notice_date'].endswith('已披露')]
    dispatched = [r for r in queue if r['status'] in ('pending', 'recheck_after_q3') and r['batch']]
    for r in dispatched:
        print(f"已派出、未登记：{r['security_code']} {r['security_name']}（{r['batch']}）——先完成该批")
    open_rows = [r for r in queue if r['status'] in ('pending', 'recheck_after_q3') and not r['batch']
                 and FINANCIAL not in r['valuation_path']]
    show('1. 三季报已披露、未审计或待复核', [r for r in open_rows if r in disclosed], args.n)
    show(f'2. 未审计、三季报预约 {LATE} 及以后（按模型 P/V 升序）',
         [r for r in open_rows if r['status'] == 'pending' and r not in disclosed and r['q3_notice_date'][:10] >= LATE], args.n)
    waiting = [r for r in open_rows if r not in disclosed and not (r['status'] == 'pending' and r['q3_notice_date'][:10] >= LATE)]
    print(f'等三季报披露后归入第 1 组：{len(waiting)} 家')
    show('3. 银行与保险（单独成批）', [r for r in queue if r['status'] in ('pending', 'recheck_after_q3') and not r['batch']
                                       and FINANCIAL in r['valuation_path']], args.n)
    show('三季报后更新（done_pre_q3，三季报已披露）', [r for r in queue if r['status'] == 'done_pre_q3' and r in disclosed], 50)


if __name__ == '__main__':
    main()
