#!/usr/bin/env python3
"""神奇公式回测的输入（实验，只读生产数据）：逐公司全部报告期的利润表与资产负债表、证监会行业。

预登记 `data/experiments/exp_magic_formula_csi300_20261012/preregister.md`。
生产侧 `fetch_a_share_financial_statements.py` 只取年报、只覆盖回测宇宙；神奇公式要近四季 EBIT 与
沪深 300 历年成分（949 只），故另取一份到 `data/scratch/`，不写 `data/raw/`。

数据源同为东财 F10 通用报表（`RPT_F10_FINANCE_GINCOME`／`GBALANCE`，无需凭据），一次请求返回该股全部报告期；
`ORG_TYPE` 列区分通用／银行／证券／保险。行业走 `fetch_csrc_industry.fetch`（现行分类）。
可断点续跑：已写入 `done_codes.txt` 的代码跳过。

    python3 scripts/experimental/magic_formula_fetch_inputs.py --out-dir data/scratch/experiments/exp_magic_formula_csi300_20261012
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_a_share_financial_statements import API, HEADERS, secucode  # noqa: E402
from fetch_csrc_industry import fetch as fetch_industry  # noqa: E402

EXP = ROOT / "data/experiments/exp_magic_formula_csi300_20261012"
MEMBERSHIP = EXP / "csi300_membership.csv"
PANEL = ROOT / "data/processed/pit_attention/panel_moat_bank_v6b.csv"

KEYS = ["SECURITY_CODE", "SECURITY_NAME_ABBR", "ORG_TYPE", "REPORT_DATE", "REPORT_TYPE", "NOTICE_DATE", "UPDATE_DATE"]
INCOME = KEYS + [
    "TOTAL_OPERATE_INCOME", "OPERATE_INCOME", "TOTAL_OPERATE_COST", "OPERATE_COST", "OPERATE_TAX_ADD",
    "SALE_EXPENSE", "MANAGE_EXPENSE", "RESEARCH_EXPENSE", "FINANCE_EXPENSE", "FE_INTEREST_EXPENSE",
    "FE_INTEREST_INCOME", "INVEST_INCOME", "FAIRVALUE_CHANGE_INCOME", "ASSET_IMPAIRMENT_LOSS",
    "CREDIT_IMPAIRMENT_LOSS", "ASSET_IMPAIRMENT_INCOME", "CREDIT_IMPAIRMENT_INCOME", "OTHER_INCOME",
    "OPERATE_PROFIT", "NONBUSINESS_INCOME", "NONBUSINESS_EXPENSE", "TOTAL_PROFIT", "INCOME_TAX",
    "NETPROFIT", "PARENT_NETPROFIT", "DEDUCT_PARENT_NETPROFIT", "BASIC_EPS",
]
BALANCE = KEYS + [
    "MONETARYFUNDS", "TRADE_FINASSET", "TRADE_FINASSET_NOTFVTPL", "TOTAL_CURRENT_ASSETS", "FIXED_ASSET", "CIP",
    "USERIGHT_ASSET", "INTANGIBLE_ASSET", "GOODWILL", "TOTAL_NONCURRENT_ASSETS", "TOTAL_ASSETS", "SHORT_LOAN",
    "NONCURRENT_LIAB_1YEAR", "SHORT_BOND_PAYABLE", "TOTAL_CURRENT_LIAB", "LONG_LOAN", "BOND_PAYABLE",
    "LEASE_LIAB", "TOTAL_LIABILITIES", "SHARE_CAPITAL", "OTHER_EQUITY_TOOL", "PREFERRED_SHARES",
    "PERPETUAL_BOND", "TOTAL_PARENT_EQUITY", "MINORITY_EQUITY", "TOTAL_EQUITY",
]
TABLES = {"income": ("RPT_F10_FINANCE_GINCOME", INCOME), "balance": ("RPT_F10_FINANCE_GBALANCE", BALANCE)}
INDUSTRY = ["security_code", "security_name", "csrc_industry", "em2016", "status"]


def fetch_all_periods(report_name: str, code: str, timeout: float, retries: int = 3) -> tuple[list[dict], str | None]:
    query = urllib.parse.urlencode({
        "reportName": report_name, "columns": "ALL", "filter": f'(SECUCODE="{secucode(code)}")',
        "pageNumber": "1", "pageSize": "300", "sortTypes": "-1", "sortColumns": "REPORT_DATE",
        "source": "HSF10", "client": "PC",
    })
    error = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(f"{API}?{query}", headers=HEADERS)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8", "replace"))
            result = payload.get("result") or {}
            if int(result.get("pages") or 1) > 1:
                return [], "multi_page"
            return (result.get("data") or []), None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            error = type(exc).__name__
            time.sleep(2.0 * (attempt + 1))
    return [], error


def universe_codes() -> list[str]:
    codes = set()
    with MEMBERSHIP.open(newline="", encoding="utf-8") as handle:
        codes.update(row["security_code"] for row in csv.DictReader(handle))
    with PANEL.open(newline="", encoding="utf-8") as handle:
        codes.update(row["security_code"] for row in csv.DictReader(handle))
    return sorted(code for code in codes if code.isdigit())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 只（冒烟用）")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument("--workers", type=int, default=4, help="并发线程数（纯网络等待）")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    done_path = args.out_dir / "done_codes.txt"
    done = set(done_path.read_text(encoding="utf-8").split()) if done_path.exists() else set()
    codes = [code for code in universe_codes() if code not in done]
    if args.limit:
        codes = codes[:args.limit]
    print(f"待取 {len(codes)} 只，已完成 {len(done)} 只", flush=True)

    paths = {kind: args.out_dir / f"{kind}_q.csv" for kind in TABLES}
    paths["industry"] = args.out_dir / "industry.csv"
    paths["gaps"] = args.out_dir / "fetch_gaps.csv"
    fields = {"income": INCOME, "balance": BALANCE, "industry": INDUSTRY, "gaps": ["security_code", "kind", "reason"]}
    handles, writers = {}, {}
    for kind, path in paths.items():
        fresh = not path.exists()
        handles[kind] = path.open("a", newline="", encoding="utf-8")
        writers[kind] = csv.DictWriter(handles[kind], fieldnames=fields[kind], extrasaction="ignore")
        if fresh:
            writers[kind].writeheader()

    def work(code: str) -> tuple[str, dict[str, list[dict]], dict, list[tuple[str, str]], bool]:
        tables, gaps, complete = {}, [], True
        for kind, (report_name, _) in TABLES.items():
            rows, error = fetch_all_periods(report_name, code, args.timeout)
            if error:
                complete = False
                gaps.append((kind, error))
            elif not rows:
                gaps.append((kind, "empty"))
            tables[kind] = rows
            time.sleep(args.pause)
        info = fetch_industry(code)
        if str(info.get("status", "")).startswith("error"):
            complete = False
        time.sleep(args.pause)
        return code, tables, info, gaps, complete

    started = time.time()
    with done_path.open("a", encoding="utf-8") as done_handle, ThreadPoolExecutor(max_workers=args.workers) as pool:
        for index, (code, tables, info, gaps, complete) in enumerate(pool.map(work, codes), 1):
            for kind, rows in tables.items():
                for row in rows:
                    row["SECURITY_CODE"] = code
                    writers[kind].writerow(row)
            for kind, reason in gaps:
                writers["gaps"].writerow(dict(security_code=code, kind=kind, reason=reason))
            writers["industry"].writerow(dict(security_code=code, security_name=info.get("security_name", ""),
                                              csrc_industry=info.get("csrc_industry", ""), em2016=info.get("em2016", ""),
                                              status=info.get("status", "")))
            if complete:
                done_handle.write(code + "\n")
                done_handle.flush()
            if index % 50 == 0:
                for handle in handles.values():
                    handle.flush()
                print(f"{index}/{len(codes)}  {time.time() - started:.0f}s", flush=True)
    for handle in handles.values():
        handle.close()
    print(f"完成，用时 {time.time() - started:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
