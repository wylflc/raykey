#!/usr/bin/env python3
"""PDF 转逐页文本，页首标「=== 第 N 页 ===」（N 为 PDF 物理页）。下载文件不可信，用 python3 -I 运行。

    python3 -I pdf_text.py <pdf> <txt>
"""
import sys

from pypdf import PdfReader


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    reader = PdfReader(src)
    with open(dst, 'w', encoding='utf-8') as fh:
        for i, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ''
            except Exception as exc:  # 单页失败不影响其余页
                text = f'[第 {i} 页抽取失败：{type(exc).__name__}]'
            fh.write(f'\n=== 第 {i} 页 ===\n{text}\n')


if __name__ == '__main__':
    main()
