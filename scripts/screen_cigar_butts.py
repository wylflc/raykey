#!/usr/bin/env python3
"""工作流程 §6.10 烟蒂池粗筛：算 A／B／C／D 四类烟蒂价值 `V_cb`，补登候选，写决策日志汇总。

报表取东财数据中心按报告期的全市场接口（一般企业三大报表 `RPT_F10_FINANCE_G*`，分红 `RPT_SHAREBONUS_DET`），
缓存在 `data/raw/financials_market/`（不入库，`--reuse-raw` 复用）；银行读 `data/raw/financials/` 逐季面板。
行情取腾讯（总市值按 A 股价计全部股本）。写 `data/interim/cigar_butt_screen.csv`（逐家读数），并更新
`data/processed/cigar_butt_pool.csv` 的候选与读数：复核状态只由人工改，本脚本只补登候选、移出 `P/V_cb > 1.0`
的候选、把 `P/V_cb ≥ 1.0` 的 watch／focus 标 exited。
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from divspread_names import is_bank_name  # noqa: E402
from roic_inputs import FINANCIAL_INTERMEDIATION_FIELDS, FINANCIAL_INTERMEDIATION_MIN  # noqa: E402

RAW = ROOT / "data/raw/financials_market"
SCREEN = ROOT / "data/interim/cigar_butt_screen.csv"
POOL = ROOT / "data/processed/cigar_butt_pool.csv"
F10_API = "https://datacenter.eastmoney.com/securities/api/data/get"
WEB_API = "https://datacenter-web.eastmoney.com/api/data/v1/get"

# §6.10 口径（数值只在工作流程定义一次，此处为实现）
CANDIDATE_MAX = 1.0
FOCUS_MAX = {"A": 0.8, "B": 0.8, "C": 0.7, "D": 0.75}
B_MULTIPLE = 5
EROSION_MAX = -0.10
BURN_YEARS_MIN = 5
CASH_RETURN_MIN = 0.20
DIVIDEND_YEARS_MIN = 2
ACQUISITION_MAX = 0.20
LIQUIDITY_MIN_WAN = 1000
DELIST_MCAP, DELIST_PRICE = 5e8, 1.0
STATE_BANKS = {"601398", "601939", "601288", "601988", "601328", "601658"}
JOINT_STOCK_BANKS = {"600036", "601166", "600000", "601998", "600016", "601818", "600015", "000001", "601916"}
COE = {"state": 10.0, "joint": 11.0, "city": 11.5}
DONE = {"实施分配", "股东大会决议通过"}

BAL_COLS = ["MONETARYFUNDS", "TRADE_FINASSET", "TRADE_FINASSET_NOTFVTPL", "NOTE_RECE", "FINANCE_RECE", "ACCOUNTS_RECE",
            "NOTE_ACCOUNTS_RECE", "INVENTORY", "CONTRACT_ASSET", "TOTAL_CURRENT_ASSETS", "CREDITOR_INVEST",
            "OTHER_CREDITOR_INVEST", "LONG_EQUITY_INVEST", "OTHER_EQUITY_INVEST", "OTHER_NONCURRENT_FINASSET",
            "INVEST_REALESTATE", "FIXED_ASSET", "CIP", "SHORT_LOAN", "LONG_LOAN", "BOND_PAYABLE", "SHORT_BOND_PAYABLE",
            "NONCURRENT_LIAB_1YEAR", "LEASE_LIAB", "TOTAL_LIABILITIES", "MINORITY_EQUITY", "OTHER_EQUITY_TOOL",
            "TOTAL_PARENT_EQUITY", "SHARE_CAPITAL", "CURRENCY", "TOTAL_ASSETS", *FINANCIAL_INTERMEDIATION_FIELDS]
INC_COLS = ["PARENT_NETPROFIT", "DEDUCT_PARENT_NETPROFIT", "OPINION_TYPE"]
CF_COLS = ["NETCASH_OPERATE", "OBTAIN_SUBSIDIARY_OTHER"]
DEBT_COLS = ("SHORT_LOAN", "LONG_LOAN", "BOND_PAYABLE", "SHORT_BOND_PAYABLE", "NONCURRENT_LIAB_1YEAR", "LEASE_LIAB")
POOL_FIELDS = [
    "security_code", "security_name", "cb_type", "status", "status_since", "attention_class", "report_date",
    "evidence_available_at", "price_date", "price", "market_cap_yi", "v_cb_yi", "pv_cb", "pv_a", "pv_b", "pv_c",
    "pv_d", "ncav_yi", "net_cash_yi", "cash_verified", "dividend_yield", "payout_3y", "ocf_3y_yi", "v_cb_cagr_3y",
    "liquidity_60d_wan", "auto_flags", "gates_failed", "catalysts", "falsifiers", "next_check", "buy_eligible",
    "independent_review_id", "dossier_dir", "reviewed_at", "note",
]
AUTO_FIELDS = ["security_name", "cb_type"] + POOL_FIELDS[POOL_FIELDS.index("attention_class"):POOL_FIELDS.index("gates_failed")]
STATUSES = ("candidate", "watch", "focus", "rejected", "exited")


def num(row: dict, key: str) -> float:
    value = row.get(key)
    try:
        return float(value) if value not in (None, "", "None") else 0.0
    except ValueError:
        return 0.0


def _get(url: str) -> bytes:
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def _write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def fetch_statement(report: str, columns: list[str], report_date: str, codes: set[str], reuse: bool) -> dict[str, dict]:
    """一般企业报表：按报告期取全市场，只留 A 股代码；缓存 `<报表>_<报告期>.csv`。"""
    path = RAW / f"{report}_{report_date}.csv"
    fields = ["SECURITY_CODE", "REPORT_DATE", "NOTICE_DATE"] + columns
    if reuse and path.exists():
        with path.open(encoding="utf-8") as handle:
            reuse = set(fields) <= set(next(csv.reader(handle)))   # 缓存缺列即重取
    if not (reuse and path.exists()):
        rows, page, asked = [], 1, list(fields)
        while True:
            query = urllib.parse.urlencode(dict(type=report, sty=",".join(["SECUCODE"] + asked), p=page, ps=500,
                                                filter=f"(REPORT_DATE='{report_date}')", sr=1, st="SECUCODE"))
            data = json.loads(_get(f"{F10_API}?{query}"))
            message = data.get("message") or ""
            if data.get("success") is False and message.endswith("返回字段不存在") and page == 1:
                asked.remove(message[: -len("返回字段不存在")])   # 按报告期接口没有的科目按 0 计
                continue
            if data.get("success") is False:
                raise SystemExit(f"{report} {report_date}：{message}")
            result = data.get("result") or {}
            rows += [r for r in result.get("data") or [] if r["SECURITY_CODE"] in codes]
            if page >= int(result.get("pages") or 0):
                break
            page += 1
        if not rows:
            raise SystemExit(f"{report} {report_date}：没有取到 A 股行")
        _write(path, rows, fields)
    return {r["SECURITY_CODE"]: r for r in _read(path)}


def fetch_dividends(year: int, codes: set[str], reuse: bool) -> list[dict]:
    """某财年（分红所属报告期在该年）的现金分红；缓存 `dividends_<年>.csv`。"""
    path = RAW / f"dividends_{year}.csv"
    fields = ["SECURITY_CODE", "REPORT_DATE", "PRETAX_BONUS_RMB", "TOTAL_SHARES", "ASSIGN_PROGRESS", "EX_DIVIDEND_DATE"]
    if not (reuse and path.exists()):
        rows = []
        for md in ("03-31", "06-30", "09-30", "12-31"):
            page = 1
            while True:
                query = urllib.parse.urlencode(dict(reportName="RPT_SHAREBONUS_DET", columns=",".join(fields), pageNumber=page,
                                                    pageSize=500, filter=f"(REPORT_DATE='{year}-{md}')"))
                result = json.loads(_get(f"{WEB_API}?{query}")).get("result") or {}
                rows += [r for r in result.get("data") or [] if r["SECURITY_CODE"] in codes]
                if page >= int(result.get("pages") or 0):
                    break
                page += 1
        _write(path, rows, fields)
    return _read(path)


def fetch_quotes(universe: list[dict], signal_date: str) -> dict[str, dict]:
    prefix = {"SSE": "sh", "SZSE": "sz", "BSE": "bj"}
    symbols = [prefix[r["exchange"]] + r["security_code"] for r in universe if r["exchange"] in prefix]
    out, raw_rows = {}, []
    for i in range(0, len(symbols), 200):
        text = _get("https://qt.gtimg.cn/q=" + ",".join(symbols[i:i + 200])).decode("gbk", errors="replace")
        for item in text.split(";"):
            f = item.split("~")
            if len(f) <= 46 or not f[3] or float(f[3] or 0) <= 0:
                continue
            day = f"{f[30][:4]}-{f[30][4:6]}-{f[30][6:8]}"
            out[f[2]] = dict(name=f[1].replace(" ", ""), price=float(f[3]), mcap=float(f[45]) * 1e8, date=day)
            raw_rows.append(dict(security_code=f[2], name=out[f[2]]["name"], price=f[3], mcap_yi=f[45], quote_date=day))
    _write(RAW / f"quotes_{signal_date}.csv", raw_rows, ["security_code", "name", "price", "mcap_yi", "quote_date"])
    stale = [c for c, q in out.items() if q["date"] != signal_date]
    if len(stale) > len(out) * 0.2:
        raise SystemExit(f"行情日不是信号日 {signal_date}：{len(stale)}/{len(out)} 只")
    return out


# ---------------------------------------------------------------- 估值口径（§6.10 第 1 条）

def value_a(b: dict) -> tuple[float, float]:
    """A 类保守净营运资金与扣少数股东、其他权益工具后的 NCAV（元）。"""
    cash, tfa = num(b, "MONETARYFUNDS"), num(b, "TRADE_FINASSET") + num(b, "TRADE_FINASSET_NOTFVTPL")
    notes = num(b, "NOTE_RECE") + num(b, "FINANCE_RECE")
    ar = num(b, "ACCOUNTS_RECE") or (0.0 if num(b, "NOTE_RECE") else num(b, "NOTE_ACCOUNTS_RECE"))
    inv, contract = num(b, "INVENTORY"), num(b, "CONTRACT_ASSET")
    other = max(0.0, num(b, "TOTAL_CURRENT_ASSETS") - (cash + tfa + notes + ar + inv + contract))
    claims = num(b, "TOTAL_LIABILITIES") + num(b, "MINORITY_EQUITY") + num(b, "OTHER_EQUITY_TOOL")
    value = cash + 0.9 * tfa + 0.9 * notes + 0.75 * ar + 0.5 * inv + 0.5 * contract + 0.25 * other - claims
    return value, num(b, "TOTAL_CURRENT_ASSETS") - claims


def net_cash(b: dict) -> float:
    return (num(b, "MONETARYFUNDS") + num(b, "TRADE_FINASSET") + num(b, "TRADE_FINASSET_NOTFVTPL")
            - sum(num(b, k) for k in DEBT_COLS) - num(b, "OTHER_EQUITY_TOOL") - num(b, "MINORITY_EQUITY"))


def value_b(b: dict, deducted_years: list[float], deducted_ttm: float | None) -> float | None:
    """B 类：近五个财年扣非归母净利均为正才适用；净现金不超过 A 类的 NCAV（预收款等经营负债占用的现金不计）。"""
    if len(deducted_years) < 5 or min(deducted_years) <= 0 or deducted_ttm is None:
        return None
    earnings = min(statistics.median(deducted_years), deducted_ttm)
    return min(net_cash(b), value_a(b)[1]) + B_MULTIPLE * earnings if earnings > 0 else None


def value_c(b: dict, v_a: float) -> float:
    return (v_a + 0.9 * (num(b, "CREDITOR_INVEST") + num(b, "OTHER_CREDITOR_INVEST"))
            + 0.3 * (num(b, "LONG_EQUITY_INVEST") + num(b, "OTHER_EQUITY_INVEST") + num(b, "OTHER_NONCURRENT_FINASSET"))
            + 0.5 * num(b, "INVEST_REALESTATE") + 0.2 * (num(b, "FIXED_ASSET") + num(b, "CIP")))


def is_intermediary(b: dict) -> bool:
    """§6.5.1 第 3 条口径：金融中介负债 ≥ 总资产 20% 的一般企业按金融企业处理，不入 A、B、C 类。"""
    total = num(b, "TOTAL_ASSETS")
    return total > 0 and sum(num(b, k) for k in FINANCIAL_INTERMEDIATION_FIELDS) >= FINANCIAL_INTERMEDIATION_MIN * total


def bank_coe(code: str) -> float:
    return COE["state"] if code in STATE_BANKS else COE["joint"] if code in JOINT_STOCK_BANKS else COE["city"]


def value_d_ps(bps: float, roes: list[float], coe: float) -> float | None:
    """D 类每股：普通股每股净资产 × min(1, (可持续 ROE − 3%) ÷ (COE − 3%))。"""
    if bps <= 0 or not roes:
        return None
    ratio = min(1.0, (min(roes) - 3.0) / (coe - 3.0))
    return bps * ratio if ratio > 0 else None


def assign_type(pv: dict[str, float | None]) -> str:
    """非金融按 A → B → C 取第一个 P/V_cb ≤ 1.0 的类；银行只有 D。"""
    for kind in ("A", "B", "C", "D"):
        if pv.get(kind) is not None and pv[kind] <= CANDIDATE_MAX:
            return kind
    return ""


def cash_verified(dividends: list[float], profits: list[float]) -> bool:
    """§6.10 第 3 条第 4 项：以三年股东回报验证现金真实性。"""
    years = sum(1 for d in dividends if d > 0)
    if sum(profits) <= 0:
        return years >= DIVIDEND_YEARS_MIN
    return years >= DIVIDEND_YEARS_MIN and sum(dividends) >= CASH_RETURN_MIN * sum(profits)


def cagr_3y(now: float, then: float) -> float | None:
    if then <= 0:
        return None
    return -1.0 if now <= 0 else (now / then) ** (1 / 3) - 1


# ---------------------------------------------------------------- 粗筛

def periods(report_date: str) -> dict:
    d = date.fromisoformat(report_date)
    fy = d.year if (d.month, d.day) == (12, 31) else d.year - 1
    prior = f"{d.year - 1}-{report_date[5:]}"
    return dict(fy=fy, annual=[f"{y}-12-31" for y in range(fy - 4, fy + 1)], prior=prior,
                three_years_ago=f"{d.year - 3}-{report_date[5:]}", ytd=report_date != f"{fy}-12-31")


def dividend_totals(rows: list[dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for r in rows:
        if r["ASSIGN_PROGRESS"] in DONE and num(r, "PRETAX_BONUS_RMB") > 0:
            out[r["SECURITY_CODE"]] = out.get(r["SECURITY_CODE"], 0.0) + num(r, "PRETAX_BONUS_RMB") / 10 * num(r, "TOTAL_SHARES")
    return out


def liquidity(codes: list[tuple[str, str]], signal_date: str) -> dict[str, float]:
    """候选近 60 个交易日日均成交额（万元），取数同 §8 扫描器。"""
    import screen_daily_volume_price_signals as scanner

    def one(item):
        code, exchange = item
        try:
            _, rows = scanner.fetch_daily_rows(code, exchange, signal_date, 20.0, fq="")
            amounts = [float(r["amount"]) for r in rows[-60:] if r.get("amount") not in (None, "")]
            return code, (sum(amounts) / len(amounts) / 1e4 if amounts else None)
        except Exception:
            return code, None
    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(one, codes))


def screen(report_date: str, signal_date: str, reuse: bool) -> list[dict]:
    universe = _read(ROOT / "data/raw/a_share_securities.csv")
    codes = {r["security_code"] for r in universe}
    exchange = {r["security_code"]: {"SSE": "SH", "SZSE": "SZ", "BSE": "BJ"}.get(r["exchange"], "") for r in universe}
    triage = {r["security_code"]: r["attention_class"] for r in _read(ROOT / "data/processed/a_share_attention_triage.csv")}
    p = periods(report_date)
    bal = fetch_statement("RPT_F10_FINANCE_GBALANCE", BAL_COLS, report_date, codes, reuse)
    bal3 = fetch_statement("RPT_F10_FINANCE_GBALANCE", BAL_COLS, p["three_years_ago"], codes, reuse)
    inc = {d: fetch_statement("RPT_F10_FINANCE_GINCOME", INC_COLS, d, codes, reuse) for d in p["annual"]}
    ytd = {d: fetch_statement("RPT_F10_FINANCE_GINCOME", INC_COLS, d, codes, reuse) for d in (report_date, p["prior"])} if p["ytd"] else {}
    cf = {d: fetch_statement("RPT_F10_FINANCE_GCASHFLOW", CF_COLS, d, codes, reuse) for d in p["annual"][-3:]}
    divs = {y: dividend_totals(fetch_dividends(y, codes, reuse)) for y in range(p["fy"] - 2, p["fy"] + 1)}
    quotes = fetch_quotes(universe, signal_date)
    panel = {d: {r["security_code"]: r for r in _read(ROOT / f"data/raw/financials/{d}.csv")}
             for d in [report_date, p["prior"], p["three_years_ago"]] + p["annual"][-3:]}
    out = []
    for u in universe:
        code = u["security_code"]
        q = quotes.get(code)
        klass = triage.get(code, "")
        if not q or klass in ("worth_attention", "garbage"):
            continue
        name = u["security_name"] or q["name"]          # 展示用名单名称；ST 与退市整理按行情名称（当前状态）判
        row = dict(security_code=code, security_name=name, attention_class=klass, price_date=q["date"],
                   price=q["price"], market_cap_yi=round(q["mcap"] / 1e8, 2))
        flags = []
        if "ST" in q["name"].upper() or "退" in q["name"] or "ST" in name.upper():
            continue
        if q["mcap"] < DELIST_MCAP or q["price"] < DELIST_PRICE:
            flags.append("退市风险")
        dividends = [divs[y].get(code, 0.0) for y in range(p["fy"] - 2, p["fy"] + 1)]
        pv: dict[str, float | None] = {}
        if is_bank_name(name) or is_bank_name(u["security_name"]):
            pr = panel[report_date].get(code)
            if not pr:
                continue
            roes = [num(panel[d].get(code, {}), "weightavg_roe") for d in p["annual"][-3:]]
            if p["ytd"]:
                roes.append(roes[-1] + num(pr, "weightavg_roe") - num(panel[p["prior"]].get(code, {}), "weightavg_roe"))
            shares = q["mcap"] / q["price"]
            v_ps = value_d_ps(num(pr, "bps"), roes, bank_coe(code))
            v = v_ps * shares if v_ps else None
            pv["D"] = q["mcap"] / v if v else None
            profits = [num(panel[d].get(code, {}), "parent_netprofit") for d in p["annual"][-3:]]
            bps3 = num(panel[p["three_years_ago"]].get(code, {}), "bps")
            row.update(report_date=report_date, evidence_available_at=(pr.get("notice_date") or "")[:10],
                       v_cb_yi=round(v / 1e8, 2) if v else "", v_cb_cagr_3y=cagr_3y(num(pr, "bps"), bps3))
        else:
            b = bal.get(code)
            if not b or is_intermediary(b):
                continue
            v_a, ncav = value_a(b)
            years = [num(inc[d].get(code, {}), "DEDUCT_PARENT_NETPROFIT") for d in p["annual"] if code in inc[d]]
            ttm = (years[-1] + num(ytd[report_date].get(code, {}), "DEDUCT_PARENT_NETPROFIT")
                   - num(ytd[p["prior"]].get(code, {}), "DEDUCT_PARENT_NETPROFIT")) if p["ytd"] and years else (years[-1] if years else None)
            if p["ytd"] and (code not in ytd[report_date] or code not in ytd[p["prior"]]):
                ttm = None
            v_b = value_b(b, years, ttm)
            v_c = value_c(b, v_a)
            pv = {k: (q["mcap"] / v if v and v > 0 else None) for k, v in (("A", v_a), ("B", v_b), ("C", v_c))}
            kind = assign_type(pv)
            v = {"A": v_a, "B": v_b, "C": v_c}.get(kind)
            shares, shares3 = num(b, "SHARE_CAPITAL"), num(bal3.get(code, {}), "SHARE_CAPITAL")
            b3 = bal3.get(code)
            if kind and b3 and shares > 0 and shares3 > 0:
                now = {"A": v_a, "C": v_c}.get(kind, num(b, "TOTAL_PARENT_EQUITY") - num(b, "OTHER_EQUITY_TOOL"))
                a3, _ = value_a(b3)
                then = {"A": a3, "C": value_c(b3, a3)}.get(kind, num(b3, "TOTAL_PARENT_EQUITY") - num(b3, "OTHER_EQUITY_TOOL"))
                row["v_cb_cagr_3y"] = cagr_3y(now / shares, then / shares3)
            opinions = [inc[d].get(code, {}).get("OPINION_TYPE") or "" for d in p["annual"][-3:]]
            if any(o and o != "标准无保留意见" for o in opinions):
                flags.append("非标审计意见")
            ocf = [num(cf[d].get(code, {}), "NETCASH_OPERATE") for d in p["annual"][-3:]]
            acquisitions = sum(num(cf[d].get(code, {}), "OBTAIN_SUBSIDIARY_OTHER") for d in p["annual"][-3:])
            equity = num(b, "TOTAL_PARENT_EQUITY") - num(b, "OTHER_EQUITY_TOOL")
            if equity > 0 and acquisitions > ACQUISITION_MAX * equity:
                flags.append("收购现金超权益 20%")
            if kind and sum(ocf) < 0 and v and v / (-sum(ocf) / 3) < BURN_YEARS_MIN:
                flags.append("现金消耗")
            profits = [num(inc[d].get(code, {}), "PARENT_NETPROFIT") for d in p["annual"][-3:]]
            row.update(report_date=report_date, evidence_available_at=(b.get("NOTICE_DATE") or "")[:10],
                       v_cb_yi=round(v / 1e8, 2) if v else "", ncav_yi=round(ncav / 1e8, 2),
                       net_cash_yi=round(net_cash(b) / 1e8, 2), ocf_3y_yi=round(sum(ocf) / 1e8, 2))
        kind = assign_type(pv)
        if row.get("v_cb_cagr_3y") is not None and row.get("v_cb_cagr_3y") != "" and row["v_cb_cagr_3y"] < EROSION_MAX:
            flags.append("价值流失")
        row.update(cb_type=kind, pv_cb=round(pv[kind], 3) if kind else "",
                   **{f"pv_{k.lower()}": (round(pv[k], 3) if pv.get(k) else "") for k in "ABCD"},
                   cash_verified="yes" if cash_verified(dividends, profits) else "no",
                   dividend_yield=round(dividends[-1] / q["mcap"], 4) if q["mcap"] else "",
                   payout_3y=round(sum(dividends) / sum(profits), 3) if sum(profits) > 0 else "",
                   auto_flags="；".join(flags))
        if isinstance(row.get("v_cb_cagr_3y"), float):
            row["v_cb_cagr_3y"] = round(row["v_cb_cagr_3y"], 4)
        row["_exchange"] = exchange.get(code, "")
        out.append(row)
    blocked = {"非标审计意见", "价值流失", "现金消耗"}
    candidates = [r for r in out if r["cb_type"] and not blocked & set(filter(None, r["auto_flags"].split("；")))]
    liq = liquidity([(r["security_code"], r["_exchange"]) for r in candidates], signal_date)
    for r in candidates:
        value = liq.get(r["security_code"])
        r["liquidity_60d_wan"] = round(value, 0) if value is not None else ""
        if value is not None and value < LIQUIDITY_MIN_WAN:
            r["auto_flags"] = "；".join(filter(None, [r["auto_flags"], "流动性不足"]))
    return out


def update_pool(rows: list[dict], signal_date: str) -> dict[str, int]:
    pool = {r["security_code"]: r for r in _read(POOL)} if POOL.exists() else {}
    blocked = {"非标审计意见", "价值流失", "现金消耗"}
    seen, stats = set(), dict(added=0, removed=0, exited=0)
    for r in rows:
        code = r["security_code"]
        if not r["cb_type"] and code not in pool:
            continue
        if r["cb_type"]:
            seen.add(code)
        if code not in pool:
            if set(filter(None, r["auto_flags"].split("；"))) & blocked:
                continue
            pool[code] = {f: "" for f in POOL_FIELDS} | dict(security_code=code, status="candidate", status_since=signal_date)
            stats["added"] += 1
        entry = pool[code]
        kind = r["cb_type"] or entry["cb_type"]          # 出区的保留原类，读数按原类重算
        entry.update({f: r.get(f, "") for f in AUTO_FIELDS})
        entry.update(cb_type=kind, pv_cb=r["pv_cb"] if r["cb_type"] else r.get(f"pv_{kind.lower()}", ""))
    for code in [c for c, e in pool.items() if e["status"] == "candidate" and c not in seen]:
        del pool[code]
        stats["removed"] += 1
    for code, entry in pool.items():
        if code not in seen and entry["status"] in ("watch", "focus"):
            entry.update(status="exited", status_since=signal_date, note=f"P/V_cb ≥ 1.0 或不再可估（{signal_date}）")
            stats["exited"] += 1
    _write(POOL, sorted(pool.values(), key=lambda e: (STATUSES.index(e["status"]), e["cb_type"], float(e["pv_cb"] or 9), e["security_code"])),
           POOL_FIELDS)
    return stats


def log_summary(report_date: str, signal_date: str, rows: list[dict], stats: dict[str, int]) -> None:
    from workflow_decision_log import WORKFLOW_VERSION, append_decision_log
    pool = _read(POOL)
    by_type = {k: sum(1 for e in pool if e["cb_type"] == k and e["status"] == "candidate") for k in "ABCD"}
    focus_ready = sum(1 for e in pool if e["pv_cb"] and float(e["pv_cb"]) <= FOCUS_MAX.get(e["cb_type"], 0))
    append_decision_log(ROOT / "data/processed/a_share_workflow_decision_log.csv", [dict(
        logged_at_utc=time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()), workflow_stage="cigar_butt_pool",
        run_id=f"cigar_butt_screen:{report_date}", as_of=signal_date, security_code="POOL", security_name="烟蒂池",
        decision_type="cigar_butt_screen",
        decision_result=f"候选 A {by_type['A']}／B {by_type['B']}／C {by_type['C']}／D {by_type['D']}；达重点级门槛 {focus_ready}",
        summary_reason=f"报告期 {report_date}、价格日 {signal_date}；逐家读数 {len(rows)}；新增 {stats['added']}、移出 {stats['removed']}、标退出 {stats['exited']}",
        input_files=f"data/raw/financials_market/；data/raw/financials/{report_date}.csv", output_file="data/processed/cigar_butt_pool.csv",
        operator_or_script="scripts/screen_cigar_butts.py", workflow_version=WORKFLOW_VERSION)])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report-date", required=True, help="最新定期报告期末 YYYY-MM-DD")
    ap.add_argument("--signal-date", required=True, help="价格日 YYYY-MM-DD")
    ap.add_argument("--reuse-raw", action="store_true", help="复用已缓存的报表与分红，只刷新行情")
    ap.add_argument("--dry-run", action="store_true", help="只写逐家读数，不改池表、不写决策日志")
    args = ap.parse_args()
    rows = screen(args.report_date, args.signal_date, args.reuse_raw)
    fields = [f for f in POOL_FIELDS if f in AUTO_FIELDS or f == "security_code"]
    _write(SCREEN, sorted(rows, key=lambda r: (r["cb_type"] == "", r["cb_type"], float(r["pv_cb"] or 9), r["security_code"])), fields)
    if args.dry_run:
        print(f"逐家读数 {len(rows)}；P/V_cb ≤ 1.0：{ {k: sum(1 for r in rows if r['cb_type'] == k) for k in 'ABCD'} }（试跑，未改池表）")
        return 0
    stats = update_pool(rows, args.signal_date)
    publication = ROOT / "data/processed/daily_execution_publication.json"
    if publication.exists() and json.loads(publication.read_text()).get("status") == "complete":
        print("注意：写决策日志会使当前发布凭据失效，须在每日扫描前运行，或运行后按同一参数重发（仓库清理规则第 3 节）")
    log_summary(args.report_date, args.signal_date, rows, stats)
    kinds = {k: sum(1 for r in rows if r["cb_type"] == k) for k in "ABCD"}
    print(f"逐家读数 {len(rows)}；P/V_cb ≤ 1.0：{kinds}；池表新增 {stats['added']}、移出 {stats['removed']}、标退出 {stats['exited']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
