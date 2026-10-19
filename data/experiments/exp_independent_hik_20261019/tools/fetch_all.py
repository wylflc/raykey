#!/usr/bin/env python3
"""Fetch all-period statements, main-business composition, dividends and price history for a code list."""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
CODES = sys.argv[2].split(',')
API = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
API2 = "https://datacenter-web.eastmoney.com/api/data/v1/get"
H = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}

def secu(c):
    if c.startswith('92'): return c + '.BJ'
    if c[0] in '69': return c + '.SH'
    return c + '.SZ'

def get(url, params):
    q = urllib.parse.urlencode(params)
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{url}?{q}", headers=H), timeout=30) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:
            err = e; time.sleep(2)
    return {"error": str(err)}

for c in CODES:
    d = {}
    for kind, rpt in (("income", "RPT_F10_FINANCE_GINCOME"), ("balance", "RPT_F10_FINANCE_GBALANCE"), ("cashflow", "RPT_F10_FINANCE_GCASHFLOW")):
        p = get(API, {"reportName": rpt, "columns": "ALL", "filter": f'(SECUCODE="{secu(c)}")',
                      "pageNumber": "1", "pageSize": "200", "sortTypes": "-1", "sortColumns": "REPORT_DATE",
                      "source": "HSF10", "client": "PC"})
        d[kind] = ((p.get("result") or {}).get("data")) or []
        time.sleep(0.3)
    p = get(API, {"reportName": "RPT_F10_FN_MAINOP", "columns": "ALL", "filter": f'(SECUCODE="{secu(c)}")',
                  "pageNumber": "1", "pageSize": "500", "sortTypes": "-1", "sortColumns": "REPORT_DATE",
                  "source": "HSF10", "client": "PC"})
    d["mainop"] = ((p.get("result") or {}).get("data")) or []
    p = get(API2, {"reportName": "RPT_SHAREBONUS_DET", "columns": "ALL", "filter": f'(SECURITY_CODE="{c}")',
                   "pageNumber": "1", "pageSize": "100", "sortTypes": "-1", "sortColumns": "PLAN_NOTICE_DATE",
                   "source": "WEB", "client": "WEB"})
    d["dividends"] = ((p.get("result") or {}).get("data")) or []
    # price history, unadjusted daily and forward-adjusted monthly
    mk = '0' if c[0] in '03' else ('1' if c[0] in '69' else '0')
    for fqt, klt, key in (("0", "101", "kline_daily_raw"), ("1", "103", "kline_monthly_qfq")):
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        p = get(url, {"secid": f"{mk}.{c}", "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                      "klt": klt, "fqt": fqt, "beg": "20150101", "end": "20261231", "lmt": "5000"})
        d[key] = ((p.get("data") or {}).get("klines")) or []
    (OUT / f"{c}.json").write_text(json.dumps(d, ensure_ascii=False))
    print(c, {k: len(v) for k, v in d.items()}, flush=True)
