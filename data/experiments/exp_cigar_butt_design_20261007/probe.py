#!/usr/bin/env python3
"""烟蒂池设计的全市场粗筛（只读探针，不进任何判定）。

资产负债表取东财数据中心 `RPT_DMSK_FN_BALANCE`（按报告期一次取全市场，只有货币资金、应收账款、存货、
负债合计等少数科目），行情取腾讯 `qt.gtimg.cn`（收盘、总市值、市净率）。粗算口径偏保守：交易性金融资产、
应收票据与融资、预付、其他流动资产都不计，少数股东权益与其他权益工具未扣。写 `probe_counts.json` 与
`probe_candidates.csv`（各类粗筛命中名单）。

    python3 probe.py --report-date 2026-06-30 --raw <下载目录>
"""
import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
BAL = ('SECURITY_CODE,SECURITY_NAME_ABBR,INDUSTRY_NAME,NOTICE_DATE,REPORT_DATE,MONETARYFUNDS,ACCOUNTS_RECE,'
       'INVENTORY,TOTAL_ASSETS,TOTAL_LIABILITIES,TOTAL_EQUITY')
FINANCIAL = ('银行', '保险', '证券', '多元金融')
PREFIX = {'SSE': 'sh', 'SZSE': 'sz', 'BSE': 'bj'}


def get(url):
    for attempt in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def balance(report_date, raw):
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode(dict(reportName='RPT_DMSK_FN_BALANCE', columns=BAL, pageNumber=page, pageSize=500,
                                        filter=f"(REPORT_DATE='{report_date}')"))
        data = json.loads(get('https://datacenter-web.eastmoney.com/api/data/v1/get?' + q))
        (raw / f'balance_{report_date}_{page}.json').write_text(json.dumps(data, ensure_ascii=False))
        result = data.get('result') or {}
        rows += result.get('data') or []
        if page >= int(result.get('pages') or 0):
            return rows
        page += 1


def quotes(codes, raw):
    out = {}
    for i in range(0, len(codes), 200):
        text = get('https://qt.gtimg.cn/q=' + ','.join(codes[i:i + 200])).decode('gbk', errors='replace')
        (raw / f'quotes_{i // 200:03d}.txt').write_text(text, encoding='utf-8')
        for item in text.split(';'):
            f = item.split('~')
            if len(f) > 46 and f[3] not in ('', '0.00'):
                try:
                    out[f[2]] = dict(close=float(f[3]), mcap=float(f[45]) * 1e8, pb=float(f[46] or 0), time=f[30][:8])
                except ValueError:
                    pass
    return out


def num(x):
    return float(x) if x not in (None, '') else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report-date', default='2026-06-30')
    ap.add_argument('--raw', type=Path, required=True)
    args = ap.parse_args()
    args.raw.mkdir(parents=True, exist_ok=True)
    secs = list(csv.DictReader(open(ROOT / 'data/raw/a_share_securities.csv', encoding='utf-8-sig')))
    names = {r['security_code']: r['security_name'] for r in secs}
    triage = {r['security_code']: r['attention_class']
              for r in csv.DictReader(open(ROOT / 'data/processed/a_share_attention_triage.csv', encoding='utf-8'))}
    q = quotes([PREFIX[r['exchange']] + r['security_code'] for r in secs if r['exchange'] in PREFIX], args.raw)
    bal = {r['SECURITY_CODE']: r for r in balance(args.report_date, args.raw)}
    hits, counts = [], dict(report_date=args.report_date, balance_rows=len(bal), quotes=len(q))
    rules = {
        'A_nnwc_le_1.0': lambda m, nnwc, nc, pb, fin: not fin and nnwc > 0 and m <= nnwc,
        'A_nnwc_le_0.67': lambda m, nnwc, nc, pb, fin: not fin and nnwc > 0 and m <= 0.67 * nnwc,
        'B_cash_minus_all_liab_ge_mcap': lambda m, nnwc, nc, pb, fin: not fin and nc > 0 and m <= nc,
        'PB_le_0.5_nonfin': lambda m, nnwc, nc, pb, fin: not fin and 0 < pb <= 0.5,
        'PB_le_0.7_nonfin': lambda m, nnwc, nc, pb, fin: not fin and 0 < pb <= 0.7,
        'PB_le_0.5_bank': lambda m, nnwc, nc, pb, fin: fin == '银行' and 0 < pb <= 0.5,
    }
    for rule in rules:
        counts[rule] = 0
    for code, b in bal.items():
        if code not in q:
            continue
        m, pb = q[code]['mcap'], q[code]['pb']
        fin = next((k for k in FINANCIAL if k in (b.get('INDUSTRY_NAME') or '')), '')
        nnwc = num(b['MONETARYFUNDS']) + 0.75 * num(b['ACCOUNTS_RECE']) + 0.5 * num(b['INVENTORY']) - num(b['TOTAL_LIABILITIES'])
        nc = num(b['MONETARYFUNDS']) - num(b['TOTAL_LIABILITIES'])
        for rule, test in rules.items():
            if test(m, nnwc, nc, pb, fin):
                counts[rule] += 1
                hits.append(dict(rule=rule, security_code=code, security_name=names.get(code, b['SECURITY_NAME_ABBR']),
                                 industry=b['INDUSTRY_NAME'], attention_class=triage.get(code, ''),
                                 mcap_yi=round(m / 1e8, 2), pb=pb, nnwc_lite_yi=round(nnwc / 1e8, 2),
                                 cash_minus_liab_yi=round(nc / 1e8, 2), quote_date=q[code]['time']))
    (EXP / 'probe_counts.json').write_text(json.dumps(counts, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    with (EXP / 'probe_candidates.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(hits[0]))
        writer.writeheader()
        writer.writerows(sorted(hits, key=lambda h: (h['rule'], h['security_code'])))
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == '__main__':
    main()
