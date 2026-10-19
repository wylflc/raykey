#!/usr/bin/env python3
"""PDF 转逐页文本，页首标「=== 第 N 页 ===」（N 为 PDF 物理页）。下载文件不可信，用 python3 -I 运行。

先用 pypdf；正文汉字占比低于 20% 的（字体编码乱码，如部分银行年报）改用集群 poppler 模块的 pdftotext 重提，取汉字占比高的一份。

    python3 -I pdf_text.py <pdf> <txt>
"""
import os
import re
import subprocess
import sys

from pypdf import PdfReader

POPPLER = 'module purge >/dev/null 2>&1; module load 2025 poppler/25.09.1-GCC-14.2.0 >/dev/null 2>&1; exec pdftotext -enc UTF-8 "$1" -'
GARBLED = 0.20


def cjk_ratio(pages: list[str]) -> tuple[float, int]:
    body = re.sub(r'\s', '', ''.join(pages))
    return (len(re.findall(r'[一-鿿]', body)) / len(body) if body else 0.0), len(body)


def pypdf_pages(src: str) -> list[str]:
    out = []
    for i, page in enumerate(PdfReader(src).pages, 1):
        try:
            out.append(page.extract_text() or '')
        except Exception as exc:  # 单页失败不影响其余页
            out.append(f'[第 {i} 页抽取失败：{type(exc).__name__}]')
    return out


def poppler_pages(src: str) -> list[str]:
    res = subprocess.run(['bash', '-lc', POPPLER, 'bash', src], capture_output=True, timeout=600)
    if res.returncode != 0:
        return []
    pages = res.stdout.decode('utf-8', errors='replace').split('\f')
    return pages[:-1] if pages and not pages[-1].strip() else pages


def main() -> None:
    src, dst = sys.argv[1], sys.argv[2]
    pages = pypdf_pages(src)
    ratio, size = cjk_ratio(pages)
    if size >= 2000 and ratio < GARBLED:
        alt = poppler_pages(src)
        if alt and cjk_ratio(alt)[0] > ratio:
            pages = alt
    tmp = dst + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        for i, text in enumerate(pages, 1):
            fh.write(f'\n=== 第 {i} 页 ===\n{text}\n')
    os.replace(tmp, dst)


if __name__ == '__main__':
    main()
