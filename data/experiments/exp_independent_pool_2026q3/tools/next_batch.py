#!/usr/bin/env python3
"""OI-291：按 README「范围与顺序」列出下一批候选，认领与释放正在分析的公司（README「认领」）。

列出候选只读；加 --refresh 时先刷新 queue.csv 的三季报日期。认领与释放改 queue.csv 的 batch、claimed_by、claimed_at。
模型 `P/V` = 最近一次扫描的估值价（池 CSV 的 valuation_price）÷ 模型带中值（intrinsic_value），只供主会话排序。
账户标签：环境变量 CLAUDE_CONFIG_DIR 未设置的会话为 A，已设置的为 B；判断不对时用 --by 指定。

    python3 tools/next_batch.py [--refresh] [--n 8]
    python3 tools/next_batch.py --claim 600660,600415 --batch b08   # 认领；三季报后更新（done_pre_q3）不改批次号
    python3 tools/next_batch.py --claim 600660 --takeover           # 用户同意后，把另一账户认领的公司转到本账户
    python3 tools/next_batch.py --release 600660,600415             # 登记后清除认领；放弃时加 --abandon，未审公司退回候选
"""
import argparse
import csv
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
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
OPEN = ('pending', 'recheck_after_q3')


def account() -> str:
    return 'B' if os.environ.get('CLAUDE_CONFIG_DIR') else 'A'


def codes_of(text: str) -> list[str]:
    return [c.strip().zfill(6) for c in re.split(r'[,+]', text) if c.strip()]


def busy(r: dict) -> bool:
    """正在分析：已认领，或未审公司已填批次号（派出时未认领）。"""
    return bool(r['claimed_by']) or (r['status'] in OPEN and bool(r['batch']))


def free_batch(queue: list[dict]) -> str:
    names = [r['batch'] for r in queue] + [p.name for p in EXP.iterdir() if p.is_dir()]
    last = max((int(n[1:]) for n in names if re.fullmatch(r'b\d+', n)), default=0)
    return f'b{last + 1:02d}'


def claim(codes: list[str], batch: str, by: str, takeover: bool) -> None:
    queue = write_brief.load_queue()
    rows = {r['security_code']: r for r in queue}
    errors = [f'队列里没有 {c}' for c in codes if c not in rows]
    codes = [c for c in codes if c in rows]
    for c in codes:
        r, name = rows[c], f"{c} {rows[c]['security_name']}"
        if r['claimed_by'] and not (takeover and r['claimed_by'] != by):
            errors.append(f"{name} 已由账户 {r['claimed_by']} 于 {r['claimed_at']} 认领（{r['batch']}）"
                          + ('' if r['claimed_by'] == by else '；用户同意接手时加 --takeover'))
        elif takeover and not r['claimed_by']:
            errors.append(f'{name} 未被认领，不用 --takeover')
        elif not takeover and r['status'] == 'done':
            errors.append(f"{name} 已完成（{r['current_review_id']}）")
        elif not takeover and r['status'] in OPEN and (not batch or r['batch'] not in ('', batch)):
            errors.append(f"{name} 是新审计，--batch 须给出" + (f"且与已填的 {r['batch']} 一致" if r['batch'] else ''))
    if batch and not takeover:
        used = [r for r in queue if r['batch'] == batch and r['security_code'] not in codes and r['claimed_by'] != by]
        if used:
            names = '、'.join(r['security_code'] + ' ' + r['security_name'] for r in used[:3]) + ('等' if len(used) > 3 else '')
            errors.append(f'批次号 {batch} 已被 {names} 使用；空闲批次号 {free_batch(queue)}')
    if errors:
        raise SystemExit('未认领：\n' + '\n'.join(errors))
    now = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    for c in codes:
        r = rows[c]
        if r['status'] in OPEN and not takeover:
            r['batch'] = batch
        r['claimed_by'], r['claimed_at'] = by, now
    write_brief.save_queue(queue)
    print(f"账户 {by} {'接手' if takeover else '认领'}（{now}）：" + '、'.join(f"{c} {rows[c]['security_name']}（{rows[c]['batch']}）" for c in codes))
    print('立即只提交 queue.csv：git commit -m <信息> -- data/experiments/exp_independent_pool_2026q3/queue.csv')


def release(codes: list[str], by: str, abandon: bool) -> None:
    queue = write_brief.load_queue()
    rows = {r['security_code']: r for r in queue}
    errors = [f'队列里没有 {c}' for c in codes if c not in rows]
    codes = [c for c in codes if c in rows]
    for c in codes:
        r = rows[c]
        if not r['claimed_by']:
            errors.append(f"{c} {r['security_name']} 未被认领")
        elif r['claimed_by'] != by:
            errors.append(f"{c} {r['security_name']} 由账户 {r['claimed_by']} 认领，不能释放；用户同意接手时先 --takeover")
        elif r['status'] in OPEN and not abandon:
            errors.append(f"{c} {r['security_name']} 仍为 {r['status']}：登记后先改 status 再释放，放弃时加 --abandon")
    if errors:
        raise SystemExit('未释放：\n' + '\n'.join(errors))
    for c in codes:
        r = rows[c]
        if r['status'] in OPEN:
            r['batch'] = ''
        r['claimed_by'] = r['claimed_at'] = ''
    write_brief.save_queue(queue)
    print(f"账户 {by} 释放：" + '、'.join(f"{c} {rows[c]['security_name']}（{rows[c]['status']}）" for c in codes))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true', help='先按东财预约披露表刷新 queue.csv 的三季报日期（联网）')
    ap.add_argument('--n', type=int, default=8, help='每组列出的家数')
    ap.add_argument('--claim', default='', help='认领的代码，逗号或加号分隔')
    ap.add_argument('--batch', default='', help='认领未审公司时的批次号')
    ap.add_argument('--takeover', action='store_true', help='把另一账户认领的公司转到本账户（须经用户同意）')
    ap.add_argument('--release', default='', help='释放认领的代码')
    ap.add_argument('--abandon', action='store_true', help='放弃未登记的公司，退回候选')
    ap.add_argument('--by', default='', help='账户标签，缺省按 CLAUDE_CONFIG_DIR 判断')
    args = ap.parse_args()
    by = args.by or account()
    if args.claim:
        return claim(codes_of(args.claim), args.batch, by, args.takeover)
    if args.release:
        return release(codes_of(args.release), by, args.abandon)
    if args.refresh:
        codes = [r['security_code'] for r in write_brief.load_queue()]
        write_brief.refresh_queue(write_brief.q3_schedule(codes))
    queue = write_brief.load_queue()
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

    print(f'本会话账户 {by}；空闲批次号 {free_batch(queue)}')
    for r in filter(busy, queue):
        owner = (f"账户 {r['claimed_by']}{'（本账户）' if r['claimed_by'] == by else ''}，{r['claimed_at']} 认领"
                 if r['claimed_by'] else '未认领，先补认领或完成该批')
        print(f"进行中：{r['security_code']} {r['security_name']}（{r['batch']}，{r['status']}，{owner}）")
    disclosed = [r for r in queue if r['q3_notice_date'].endswith('已披露')]
    open_rows = [r for r in queue if r['status'] in OPEN and not busy(r) and FINANCIAL not in r['valuation_path']]
    show('1. 三季报已披露、未审计或待复核', [r for r in open_rows if r in disclosed], args.n)
    show(f'2. 未审计、三季报预约 {LATE} 及以后（按模型 P/V 升序）',
         [r for r in open_rows if r['status'] == 'pending' and r not in disclosed and r['q3_notice_date'][:10] >= LATE], args.n)
    waiting = [r for r in open_rows if r not in disclosed and not (r['status'] == 'pending' and r['q3_notice_date'][:10] >= LATE)]
    print(f'等三季报披露后归入第 1 组：{len(waiting)} 家')
    show('3. 银行与保险（单独成批）', [r for r in queue if r['status'] in OPEN and not busy(r)
                                       and FINANCIAL in r['valuation_path']], args.n)
    show('三季报后更新（done_pre_q3，三季报已披露）',
         [r for r in queue if r['status'] == 'done_pre_q3' and r in disclosed and not busy(r)], 50)


if __name__ == '__main__':
    main()
