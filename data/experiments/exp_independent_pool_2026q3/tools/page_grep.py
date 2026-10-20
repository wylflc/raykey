#!/usr/bin/env python3
"""OI-291 主会话抽查：在批次公告的逐页文本里按正则找原文，打印页码与上下文。

    python3 -I tools/page_grep.py b07 300750 2026Q3_report '回购专用证券账户' [页码,页码|-] [上下文字数] [条数]

文件名是 raw/<代码>/txt/ 下去掉 .txt 的部分（对照 raw/<代码>/INDEX.tsv）；缺省上下文 90 字、只打印 1 条。
"""
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
SCRATCH = ROOT / 'data/scratch/experiments/exp_independent_pool_2026q3'


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    batch, code, stem, pattern = sys.argv[1:5]
    pages = {int(x) for x in sys.argv[5].split(',')} if len(sys.argv) > 5 and sys.argv[5] not in ('', '-') else None
    ctx = int(sys.argv[6]) if len(sys.argv) > 6 else 90
    limit = int(sys.argv[7]) if len(sys.argv) > 7 else 1
    text = (SCRATCH / batch / 'raw' / code / 'txt' / f'{stem}.txt').read_text(encoding='utf-8')
    parts = re.split(r'(?:^|\n)=== 第 (\d+) 页 ===\n', text)
    found = 0
    for i in range(1, len(parts) - 1, 2):
        page, body = int(parts[i]), parts[i + 1].replace('\n', ' ')
        if pages and page not in pages:
            continue
        for m in re.finditer(pattern, body):
            print(f'[{code} {stem} 第 {page} 页]', body[max(0, m.start() - ctx):m.end() + ctx])
            found += 1
            if found >= limit:
                return
    if not found:
        print(f'[{code} {stem}] 未找到：{pattern}')


if __name__ == '__main__':
    main()
