#!/usr/bin/env python3
"""工作流程 §6.10 第 7 条港股烟蒂池粗筛：港股 A／B／C／D 四类烟蒂价值、港股通标注，补登候选并写决策日志汇总。

报表取东财 HK F10 按标准报告期的全市场接口：资产负债表与利润表取报表币原值（`RPT_HKF10_FN_BALANCE`／`_INCOME`，
带 `CURRENCY_CODE`），现金流量表只有折人民币版（`RPT_HKF10_FN_CASHFLOW_PC`），主要指标 `RPT_HKF10_FN_MAININDICATOR`
（机构类型、股数、每股净资产、ROE），分红 `RPT_HKF10_INFO_DIVIDEND`；科目名沿用 `fetch_overseas_statements.HK_ITEMS`。
逐家取信号日已披露的最新定期报告。行情取腾讯（总市值 = 全部普通股 × 港股价），汇率取欧洲央行信号日参考价，
港股通取上交所、深交所当日公布的港股通标的证券名单。A+H 公司按东财机构代码对应 A 股：A 股在关注池或 `garbage`
的不入；A+H 银行沿用 A 股粗筛的烟蒂价值（`data/interim/cigar_butt_screen.csv`）。
缓存在 `data/raw/financials_market_hk/`（不入库，`--reuse-raw` 复用）。写 `data/interim/cigar_butt_screen_hk.csv`，
并按 A 股同一状态规则更新 `data/processed/cigar_butt_pool_hk.csv`。
"""
from __future__ import annotations

import argparse
import json
import re
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
import screen_cigar_butts as cb  # noqa: E402
from fetch_overseas_statements import HK_API, HK_DPS_RE, HK_INTERMEDIATION_KEYS, HK_ITEMS, CCY_NAME, hk_debt_keys  # noqa: E402

RAW = ROOT / "data/raw/financials_market_hk"
SCREEN = ROOT / "data/interim/cigar_butt_screen_hk.csv"
POOL = ROOT / "data/processed/cigar_butt_pool_hk.csv"
WATCHLIST = ROOT / "data/processed/overseas_watchlist_valuation.csv"
TRIAGE = ROOT / "data/processed/a_share_attention_triage.csv"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}
SSE_LIST = ("http://query.sse.com.cn/commonQuery.do?sqlId=COMMON_SSE_JYFW_HGT_XXPL_BDZQQD_L"
            "&isPagination=true&pageHelp.pageSize=5000&pageHelp.pageNo=1")
SZSE_LIST = "https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=SGT_GGTBDQD&TABKEY=tab1&PAGENO={page}"
FX_API = "https://api.frankfurter.dev/v1/{day}?base=USD"

# §6.10 第 7 条口径（数值只在工作流程定义一次，此处为实现）
DELIST_MCAP_HKD = 5e8
HK_BANK_COE = 11.0                      # 香港及外资银行；内地银行同第 1 条分档
H_JOINT_STOCK_BANKS = {"09668"}         # 只在港股上市的股份行（渤海银行）
HKD_PER_MOP = 1 / 1.03                  # 澳门元按联系汇率折港元（欧洲央行无澳门元）
SECURITY_TYPES = {"H股", "红筹股", "非H股"}
BANK_NAMES = ("银行", "农商")
BANK_EXTRA = {"00005", "02888"}         # 汇丰控股、渣打集团

CASH = ("现金及等价物", "短期存款", "受限制存款及现金")
TRADING = ("短期投资", "指定以公允价值记账之金融资产(流动)", "交易性金融资产(流动)", "其他金融资产(流动)")
NOTES = ("应收票据",)
RECEIVABLES = ("应收帐款",)
INVENTORY = ("存货", "发展中及待售物业")
CONTRACT = ("合同资产",)
NON_COMMON = ("少数股东权益", "非控股股东权益", "永久资本证券", "其他权益工具", "优先股", "其他权益")
DEBT_EXTRA = ("银行贷款及透支", "长期银行贷款", "借款", "其他贷款(流动)", "其他贷款(非流动)", "已发行债券",
              "可转换票据及债券(流动)")
DEPOSITS_NC = ("中长期存款", "现金及等价物(非流动)")
INVESTMENTS = ("联营公司权益", "合营公司权益", "于合营公司投资", "证券投资", "其他证券投资", "其他投资", "长期投资",
               "可供出售投资", "持有至到期投资", "指定以公允价值记账之金融资产", "其他金融资产(非流动)")
PROPERTY = ("投资物业",)
FIXED = ("物业厂房及设备", "固定资产", "在建工程")
INTERMEDIATION = tuple(n for k in HK_INTERMEDIATION_KEYS for n in HK_ITEMS[k][1])
PROFIT, REVALUATION = "股东应占溢利", "重估盈余"
OCF, ACQUISITION = "经营业务现金净额", "收购附属公司"
INDICATOR_COLS = "SECURITY_CODE,DATE_TYPE_CODE,ORG_TYPE,BPS,ROE_AVG,ISSUED_COMMON_SHARES"
HK_EXTRA_FIELDS = ["security_type", "report_currency", "fx_to_hkd", "southbound_sh", "southbound_sz", "southbound_eligible"]
POOL_FIELDS = cb.POOL_FIELDS + HK_EXTRA_FIELDS
AUTO_FIELDS = cb.AUTO_FIELDS + HK_EXTRA_FIELDS
SCREEN_FIELDS = [f for f in POOL_FIELDS if f in AUTO_FIELDS or f == "security_code"]
HKD_EQUIVALENT = re.compile(r"相当于港币([\d.]+)元")
CJK = re.compile(r"[\u4e00-\u9fff]")
INTERIM_PERIODS = ("中期", "特别", "季度", "第一季", "第三季")


def _get(url: str, headers: dict = HEADERS, timeout: int = 40) -> bytes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as resp:
                return resp.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def _json_cache(path: Path, reuse: bool, build):
    if reuse and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    value = build()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return value


def datacenter(report: str, flt: str, columns: str, sort: str = "") -> list[dict]:
    """东财数据中心分页全取（每页 500 行，按 `sort` 稳定排序）。"""
    rows, page = [], 1
    while True:
        params = dict(reportName=report, columns=columns, pageSize=500, pageNumber=page) | (dict(filter=flt) if flt else {})
        if sort:
            params.update(sortColumns=sort, sortTypes=",".join("1" for _ in sort.split(",")))
        data = json.loads(_get(f"{HK_API}?{urllib.parse.urlencode(params)}"))
        if data.get("success") is False and "为空" not in str(data.get("message")):
            raise SystemExit(f"{report} {flt}：{data.get('message')}")
        result = data.get("result") or {}
        rows += result.get("data") or []
        if page >= int(result.get("pages") or 0):
            return rows
        page += 1
        time.sleep(0.2)


def _items_filter(items) -> str:
    return "(ITEM_NAME in (" + ",".join(f'"{i}"' for i in items) + "))"


def statement(report: str, period: str, reuse: bool, items=None) -> dict[str, dict]:
    """按标准报告期取全市场报表，转成 {代码: {科目: 金额, _type, _ccy}}；`_PC` 报表为东财折人民币值。

    东财标准报告期：年报一律记 YYYY-12-31（非 12 月年结记财年所属年，如 2026-03-31 年结记 2025），
    中报记 06-30，一、三季报记 03-31、09-30；分红期次（「2025末期」）用同一年份。"""
    pc = report.endswith("_PC")
    name = "STD_ITEM_NAME" if pc else "ITEM_NAME"
    tag = "_" + "-".join(items) if items else ""

    def build():
        flt = f"(STD_REPORT_DATE='{period} 00:00:00')"
        if items:
            flt += _items_filter(items).replace("ITEM_NAME", name)
        columns = "SECURITY_CODE,DATE_TYPE_CODE,STD_ITEM_CODE,AMOUNT," + name + ("" if pc else ",CURRENCY_CODE")
        out: dict[str, dict] = {}
        for r in datacenter(report, flt, columns, "SECURITY_CODE,STD_ITEM_CODE"):
            row = out.setdefault(r["SECURITY_CODE"], dict(_type=r["DATE_TYPE_CODE"],
                                                          _ccy="CNY" if pc else r.get("CURRENCY_CODE") or ""))
            if r["AMOUNT"] is not None and r[name] not in row:
                row[r[name]] = float(r["AMOUNT"])
        return out
    return _json_cache(RAW / f"{report}_{period}{tag}.json", reuse, build)


def standard_year(end: str) -> int:
    """实际年结日 → 东财标准报告期年份：年结月在 1～6 月的记上一年（2026-03-31 → 2025），其余记当年。"""
    return int(end[:4]) - (1 if int(end[5:7]) <= 6 else 0)


def annual_cashflow(since: str, reuse: bool) -> dict[str, dict[str, dict]]:
    """现金流量表只有折人民币版且没有标准报告期列：取 `since` 起的年报行，按 `standard_year` 归到 YYYY-12-31。"""
    def build():
        flt = (f'(DATE_TYPE_CODE="001")(REPORT_DATE>=\'{since} 00:00:00\')'
               + _items_filter((OCF, ACQUISITION)).replace("ITEM_NAME", "STD_ITEM_NAME"))
        out: dict[str, dict[str, dict]] = {}
        for r in datacenter("RPT_HKF10_FN_CASHFLOW_PC", flt, "SECURITY_CODE,REPORT_DATE,STD_ITEM_NAME,AMOUNT",
                            "SECURITY_CODE,REPORT_DATE"):
            if r["AMOUNT"] is not None:
                period = f"{standard_year(r['REPORT_DATE'][:10])}-12-31"
                out.setdefault(period, {}).setdefault(r["SECURITY_CODE"], {})[r["STD_ITEM_NAME"]] = float(r["AMOUNT"])
        return out
    return _json_cache(RAW / f"RPT_HKF10_FN_CASHFLOW_PC_annual_{since}.json", reuse, build)


def indicators(period: str, reuse: bool) -> dict[str, dict]:
    def build():
        rows = datacenter("RPT_HKF10_FN_MAININDICATOR", f"(STD_REPORT_DATE='{period} 00:00:00')", INDICATOR_COLS, "SECURITY_CODE")
        return {r["SECURITY_CODE"]: r for r in rows}
    return _json_cache(RAW / f"RPT_HKF10_FN_MAININDICATOR_{period}.json", reuse, build)


def securities(signal_date: str, reuse: bool) -> dict[str, dict]:
    def build():
        rows = datacenter("RPT_HKF10_INFO_SECURITYINFO", "",
                          "SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,SECURITY_TYPE,BOARD", "SECURITY_CODE")
        return {r["SECURITY_CODE"]: r for r in rows}
    return _json_cache(RAW / f"securities_{signal_date}.json", reuse, build)


def a_share_org_codes(signal_date: str, reuse: bool) -> dict[str, str]:
    """东财机构代码 → A 股代码（A+H 对应用）。"""
    def build():
        rows = datacenter("RPT_F10_BASIC_ORGINFO", "", "SECUCODE,ORG_CODE", "SECUCODE")
        return {r["ORG_CODE"]: r["SECUCODE"].split(".")[0] for r in rows
                if r.get("ORG_CODE") and r["SECUCODE"].endswith((".SH", ".SZ", ".BJ"))}
    return _json_cache(RAW / f"a_share_org_{signal_date}.json", reuse, build)


def dividend_events(since: str, signal_date: str, reuse: bool) -> dict[str, list[dict]]:
    def build():
        rows = datacenter("RPT_HKF10_INFO_DIVIDEND", f"(NOTICE_DATE>='{since}')",
                          "SECURITY_CODE,NOTICE_DATE,ASSIGN_PERIOD,PLAN_EXPLAIN,ASSIGN_PROGRESS", "SECURITY_CODE,NOTICE_DATE")
        out: dict[str, list[dict]] = {}
        for r in rows:
            out.setdefault(r["SECURITY_CODE"], []).append(r)
        return out
    return _json_cache(RAW / f"dividends_{since}_{signal_date}.json", reuse, build)


def southbound(signal_date: str, reuse: bool) -> dict:
    """上交所、深交所当日公布的港股通标的证券名单。"""
    def build():
        sse = json.loads(_get(SSE_LIST, {"User-Agent": "Mozilla/5.0", "Referer": "http://www.sse.com.cn/"}))["pageHelp"]["data"]
        szse, page, pages, szse_day = [], 1, 1, ""
        while page <= pages:
            data = json.loads(_get(SZSE_LIST.format(page=page), {
                "User-Agent": "Mozilla/5.0", "Referer": "https://www.szse.cn/szhk/hkbussiness/underlylist/index.html"}))[0]
            pages, szse_day = int(data["metadata"]["pagecount"]), data["metadata"]["subname"]
            szse += [r["zqdm"] for r in data["data"]]
            page += 1
            time.sleep(0.2)
        return dict(sh=sorted(r["SECURITY_CODE"] for r in sse), sh_date=max(r["UPDATE_DATE"] for r in sse),
                    sz=sorted(szse), sz_date=szse_day)
    return _json_cache(RAW / f"southbound_{signal_date}.json", reuse, build)


def fx_to_hkd(signal_date: str, reuse: bool) -> tuple[dict[str, float], str]:
    """欧洲央行信号日参考价（无当日价取此前最近一日）：{币种: 港元每单位}。"""
    data = _json_cache(RAW / f"fx_{signal_date}.json", reuse,
                       lambda: json.loads(_get(FX_API.format(day=signal_date), {"User-Agent": "Mozilla/5.0"})))
    hkd = data["rates"]["HKD"]
    rates = {ccy: hkd / value for ccy, value in data["rates"].items()} | {"USD": hkd, "HKD": 1.0, "MOP": HKD_PER_MOP}
    return rates, data["date"]


def quotes(codes: list[str], signal_date: str, reuse: bool) -> dict[str, dict]:
    """腾讯港股行情：收盘、行情日、全部普通股、总市值（港元）、当日成交额。"""
    def build():
        out = {}
        for i in range(0, len(codes), 60):
            text = _get("https://qt.gtimg.cn/q=" + ",".join("hk" + c for c in codes[i:i + 60]),
                        {"User-Agent": "Mozilla/5.0"}).decode("gbk", errors="replace")
            for item in text.split(";"):
                f = item.split("~")
                if len(f) <= 70 or not f[3] or float(f[3] or 0) <= 0:
                    continue
                price, shares = float(f[3]), float(f[69] or 0)
                mcap = float(f[45] or 0) * 1e8 or price * shares
                if mcap > 0 and shares > 0:
                    out[f[2]] = dict(name=f[1].replace(" ", ""), price=price, date=f[30][:10].replace("/", "-"),
                                     shares=shares, mcap=mcap)
            time.sleep(0.1)
        return out
    out = _json_cache(RAW / f"quotes_{signal_date}.json", reuse, build)
    fresh = {c: q for c, q in out.items() if q["date"] == signal_date}
    if len(fresh) < len(out) * 0.8:
        raise SystemExit(f"行情日不是信号日 {signal_date}：{len(out) - len(fresh)}/{len(out)} 只")
    return fresh


def liquidity(codes: list[str], signal_date: str, cny_to_hkd: float) -> dict[str, float | None]:
    """近 60 个交易日日均成交额，折人民币万元（腾讯日线末列为万港元）。"""
    def one(code):
        try:
            url = f"https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get?param=hk{code},day,,{signal_date},60,qfq"
            rows = json.loads(_get(url, {"User-Agent": "Mozilla/5.0"}))["data"]["hk" + code]
            rows = [r for r in rows.get("qfqday") or rows.get("day") or [] if r[0] <= signal_date][-60:]
            amounts = [float(r[8]) for r in rows if len(r) > 8 and r[8] not in ("", None)]
            return code, (sum(amounts) / len(amounts) / cny_to_hkd if amounts else None)
        except Exception:
            return code, None
    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(one, codes))


def balance_3y(code: str, period: str, cache: dict) -> dict:
    """候选的三年前同期资产负债表（逐家取，缓存）。"""
    key = f"{code}:{period}"
    if key not in cache:
        rows = datacenter("RPT_HKF10_FN_BALANCE", f'(SECUCODE="{code}.HK")(STD_REPORT_DATE=\'{period} 00:00:00\')',
                          "ITEM_NAME,AMOUNT,CURRENCY_CODE")
        b = {"_ccy": rows[0]["CURRENCY_CODE"]} if rows else {}
        for r in rows:
            if r["AMOUNT"] is not None and r["ITEM_NAME"] not in b:
                b[r["ITEM_NAME"]] = float(r["AMOUNT"])
        cache[key] = b
    return cache[key]


# ---------------------------------------------------------------- 估值口径（§6.10 第 1、7 条）

def total(b: dict, names) -> float:
    return sum(b.get(n) or 0.0 for n in names)


def debt_names(code: str) -> tuple[str, ...]:
    return tuple(n for k in hk_debt_keys(code) for n in HK_ITEMS[k][1]) + DEBT_EXTRA


def value_a(b: dict) -> tuple[float, float]:
    """A 类保守净营运资金与扣少数股东、永续债等非普通股权益后的 NCAV（报表币）。"""
    cash, tfa, notes, ar = total(b, CASH), total(b, TRADING), total(b, NOTES), total(b, RECEIVABLES)
    inv, contract = total(b, INVENTORY), total(b, CONTRACT)
    current = b.get("流动资产合计") or 0.0
    other = max(0.0, current - (cash + tfa + notes + ar + inv + contract))
    claims = (b.get("总负债") or 0.0) + total(b, NON_COMMON)
    value = cash + 0.9 * tfa + 0.9 * notes + 0.75 * ar + 0.5 * inv + 0.5 * contract + 0.25 * other - claims
    return value, current - claims


def net_cash(b: dict, code: str) -> float:
    return total(b, CASH) + total(b, TRADING) - total(b, debt_names(code)) - total(b, NON_COMMON)


def value_b(b: dict, code: str, years: list[float], ttm: float | None) -> float | None:
    if len(years) < 5 or min(years) <= 0 or ttm is None:
        return None
    earnings = min(statistics.median(years), ttm)
    return min(net_cash(b, code), value_a(b)[1]) + cb.B_MULTIPLE * earnings if earnings > 0 else None


def value_c(b: dict, v_a: float) -> float:
    return (v_a + 0.9 * total(b, DEPOSITS_NC) + 0.3 * total(b, INVESTMENTS) + 0.5 * total(b, PROPERTY)
            + 0.2 * total(b, FIXED))


def common_equity(b: dict) -> float:
    equity = b.get("总权益") or b.get("股东权益合计") or (
        (b.get("归属于母公司股东权益") or b.get("股东权益") or 0.0) + total(b, ("少数股东权益", "非控股股东权益")))
    return equity - total(b, NON_COMMON)


def complete(b: dict) -> bool:
    """可用的定期报告：有总资产、总负债，且有流动资产合计（一般企业）或母公司股东权益（银行）。"""
    return bool(b.get("总资产")) and b.get("总负债") is not None and bool(
        b.get("流动资产合计") or b.get("归属于母公司股东权益") or b.get("客户存款"))


def is_intermediary(b: dict) -> bool:
    assets = b.get("总资产") or 0.0
    return assets > 0 and total(b, INTERMEDIATION) >= cb.FINANCIAL_INTERMEDIATION_MIN * assets


def is_bank(code: str, name: str) -> bool:
    return code in BANK_EXTRA or any(k in name for k in BANK_NAMES)


def bank_coe(code: str, security_type: str, name: str) -> float:
    if security_type != "H股":
        return HK_BANK_COE
    if any(n in name for n in ("工商银行", "建设银行", "农业银行", "中国银行", "交通银行", "邮储银行")):
        return cb.COE["state"]
    if code in H_JOINT_STOCK_BANKS:
        return cb.COE["joint"]
    return cb.COE["city"]


def adjusted_profit(row: dict | None) -> float | None:
    """港股扣非替代：股东应占溢利减重估盈余。"""
    if not row or row.get(PROFIT) is None:
        return None
    return row[PROFIT] - (row.get(REVALUATION) or 0.0)


def shift_years(day: str, years: int) -> str:
    d = date.fromisoformat(day)
    try:
        return d.replace(year=d.year + years).isoformat()
    except ValueError:
        return d.replace(year=d.year + years, day=28).isoformat()


def fiscal_end(latest: str, fy: str) -> str:
    """不晚于 `latest` 的最近一个财年末；`fy` 形如 `12-31`。"""
    current = f"{latest[:4]}-{fy}"
    return current if current <= latest else f"{int(latest[:4]) - 1}-{fy}"


def recent_periods(signal_date: str, count: int = 5) -> list[str]:
    """不晚于信号日的最近 `count` 个季末（标准报告期），新到旧。"""
    y, out = int(signal_date[:4]), []
    while len(out) < count:
        for md in ("12-31", "09-30", "06-30", "03-31"):
            if f"{y}-{md}" <= signal_date and len(out) < count:
                out.append(f"{y}-{md}")
        y -= 1
    return out


def dividend_hkd(event: dict, fx: dict[str, float]) -> float:
    """每股现金分红折港元：优先取公告的港币等值，否则按报表所列币种折算；送转与未获批准的末期股息记 0。"""
    plan, progress, period = event.get("PLAN_EXPLAIN") or "", event.get("ASSIGN_PROGRESS") or "", event.get("ASSIGN_PERIOD") or ""
    if progress not in cb.DONE and not (progress == "董事会决议通过" and any(k in period for k in INTERIM_PERIODS)):
        return 0.0
    match = HKD_EQUIVALENT.search(plan)
    if match:
        return float(match[1])
    match = HK_DPS_RE.search(plan)
    if not match:
        return 0.0
    rate = fx.get(CCY_NAME[match[1]])
    return float(match[2]) * rate if rate else 0.0


def dividends_by_year(events: list[dict], fx: dict[str, float]) -> dict[int, float]:
    out: dict[int, float] = {}
    for e in events:
        label = (e.get("ASSIGN_PERIOD") or "")[:4]
        if label.isdigit():
            out[int(label)] = out.get(int(label), 0.0) + dividend_hkd(e, fx)
    return out


# ---------------------------------------------------------------- 粗筛

def screen(signal_date: str, reuse: bool) -> list[dict]:
    fx, fx_day = fx_to_hkd(signal_date, reuse)
    cny = fx["CNY"]
    secs = securities(signal_date, reuse)
    south = southbound(signal_date, reuse)
    sh, sz = set(south["sh"]), set(south["sz"])
    universe = sorted(c for c, s in secs.items() if s.get("SECURITY_TYPE") in SECURITY_TYPES)
    quote = quotes(universe, signal_date, reuse)
    watch = {r["security_code"]: r.get("attention_class", "") for r in cb._read(WATCHLIST)
             if (r.get("market_type") or "").upper() == "HK"}
    triage = {r["security_code"]: r["attention_class"] for r in cb._read(TRIAGE)}
    a_org = a_share_org_codes(signal_date, reuse)
    a_screen = {r["security_code"]: r for r in cb._read(cb.SCREEN)} if cb.SCREEN.exists() else {}
    three_cache_path = RAW / "balance_3y.json"
    three_cache = json.loads(three_cache_path.read_text(encoding="utf-8")) if three_cache_path.exists() else {}

    periods = recent_periods(signal_date)
    balances = {p: statement("RPT_HKF10_FN_BALANCE", p, reuse) for p in periods}
    latest: dict[str, tuple[str, dict]] = {}
    for p in periods:                                  # 新到旧：逐家取最新的定期报告
        for code, b in balances[p].items():
            if code not in latest and complete(b):
                latest[code] = (p, b)
    plan: dict[str, dict] = {}
    for code, (period, b) in latest.items():
        fy_end = fiscal_end(period, "12-31")              # 标准报告期下的最近年报
        plan[code] = dict(period=period, fy_end=fy_end, annual=[shift_years(fy_end, -k) for k in range(4, -1, -1)],
                          ytd=[] if period == fy_end else [period, shift_years(period, -1)], three=shift_years(period, -3))
    income_periods = sorted({d for p in plan.values() for d in p["annual"] + p["ytd"]})
    income = {d: statement("RPT_HKF10_FN_INCOME", d, reuse, (PROFIT, REVALUATION)) for d in income_periods}
    cash_since = shift_years(min(p["annual"][-3] for p in plan.values()), -1)
    cash_all = annual_cashflow(cash_since, reuse)
    cashflow = {d: cash_all.get(d, {}) for p in plan.values() for d in p["annual"][-3:]}
    ind_periods = sorted({d for p in plan.values() for d in p["annual"][-3:] + p["ytd"] + [p["period"], p["three"]]})
    ind = {d: indicators(d, reuse) for d in ind_periods}
    since = min(f"{int(p['annual'][-3][:4]) - 1}-01-01" for p in plan.values())
    events = dividend_events(since, signal_date, reuse)

    out = []
    for code in universe:
        q, s = quote.get(code), secs[code]
        if not q or code not in latest:
            continue
        a_code = a_org.get(s.get("ORG_CODE") or "", "")
        klass = watch.get(code) or triage.get(a_code, "")
        if klass in ("worth_attention", "garbage"):
            continue
        p = plan[code]
        b = latest[code][1]
        ccy = b["_ccy"]
        rate = fx.get(ccy)
        name = s.get("SECURITY_NAME_ABBR") or q["name"]
        if not CJK.search(name) and CJK.search(q["name"]):
            name = q["name"]                            # 证券信息表只有英文简称时取行情中文名
        org_type = (ind[p["period"]].get(code) or {}).get("ORG_TYPE") or ""
        if org_type in ("保险", "证券") or not rate:
            continue
        mcap = q["mcap"]
        row = dict(security_code=code, security_name=name, security_type=s.get("SECURITY_TYPE", ""), attention_class=klass,
                   report_currency=ccy, fx_to_hkd=round(rate, 6), southbound_sh="yes" if code in sh else "no",
                   southbound_sz="yes" if code in sz else "no",
                   southbound_eligible="yes" if code in sh or code in sz else "no",
                   report_date=p["period"], evidence_available_at="", price_date=q["date"], price=q["price"],
                   market_cap_yi=round(mcap / 1e8, 2))
        flags = ["退市风险"] if mcap < DELIST_MCAP_HKD else []
        profits = [(income[d].get(code) or {}).get(PROFIT) for d in p["annual"][-3:]]
        profits_hkd = [x * rate for x in profits if x is not None]
        dividends = dividends_by_year(events.get(code, []), fx)
        label = int(p["fy_end"][:4])
        divs_hkd = [dividends.get(y, 0.0) * q["shares"] for y in range(label - 2, label + 1)]
        pv: dict[str, float | None] = {}
        v = None
        if org_type == "银行" or b.get("客户存款") is not None:
            if not is_bank(code, name):
                continue                                # 金融控股：不入 A、B、C 类，也不按银行估
            a_row = a_screen.get(a_code)
            if a_row and a_row.get("v_cb_yi"):
                v = float(a_row["v_cb_yi"]) * 1e8 * cny
                row.update(report_date=a_row.get("report_date", ""), evidence_available_at=a_row.get("evidence_available_at", ""),
                           v_cb_cagr_3y=a_row.get("v_cb_cagr_3y", ""))
            else:
                shares_l = float((ind[p["period"]].get(code) or {}).get("ISSUED_COMMON_SHARES") or 0)
                roes = [(ind[d].get(code) or {}).get("ROE_AVG") for d in p["annual"][-3:]]
                roes = [float(x) for x in roes if x is not None]
                if p["ytd"] and roes:
                    now, prior = ((ind[d].get(code) or {}).get("ROE_AVG") for d in p["ytd"])
                    roes.append(roes[-1] + float(now) - float(prior) if now is not None and prior is not None else roes[-1])
                v_ps = cb.value_d_ps(common_equity(b) / shares_l, roes, bank_coe(code, row["security_type"], name)) \
                    if shares_l > 0 else None
                v = v_ps * rate * q["shares"] if v_ps else None
                bps = [(ind[d].get(code) or {}).get("BPS") for d in (p["period"], p["three"])]
                if all(x is not None for x in bps):
                    row["v_cb_cagr_3y"] = cb.cagr_3y(float(bps[0]), float(bps[1]))
            pv["D"] = mcap / v if v and v > 0 else None
        else:
            if is_intermediary(b):
                continue
            v_a, ncav = value_a(b)
            years = [adjusted_profit(income[d].get(code)) for d in p["annual"]]
            years = [x for x in years if x is not None]
            ttm = years[-1] if years and not p["ytd"] else None
            if p["ytd"] and years:
                now, prior = (adjusted_profit(income[d].get(code)) for d in p["ytd"])
                ttm = years[-1] + now - prior if now is not None and prior is not None else None
            values = {"A": v_a, "B": value_b(b, code, years, ttm), "C": value_c(b, v_a)}
            pv = {k: (mcap / (x * rate) if x and x > 0 else None) for k, x in values.items()}
            kind = cb.assign_type(pv)
            v = values[kind] * rate if kind else None
            ocf = [(cashflow[d].get(code) or {}).get(OCF) or 0.0 for d in p["annual"][-3:]]
            acquisitions = sum(abs((cashflow[d].get(code) or {}).get(ACQUISITION) or 0.0) for d in p["annual"][-3:])
            equity = common_equity(b)
            if equity > 0 and acquisitions * cny > cb.ACQUISITION_MAX * equity * rate:
                flags.append("收购现金超权益 20%")
            if kind and sum(ocf) < 0 and v and v / (-sum(ocf) * cny / 3) < cb.BURN_YEARS_MIN:
                flags.append("现金消耗")
            row.update(ncav_yi=round(ncav * rate / 1e8, 2), net_cash_yi=round(net_cash(b, code) * rate / 1e8, 2),
                       ocf_3y_yi=round(sum(ocf) * cny / 1e8, 2))
            if kind:
                b3 = balance_3y(code, p["three"], three_cache)
                shares_now = float((ind[p["period"]].get(code) or {}).get("ISSUED_COMMON_SHARES") or 0)
                shares_then = float((ind[p["three"]].get(code) or {}).get("ISSUED_COMMON_SHARES") or 0)
                if b3.get("总资产") and shares_now > 0 and shares_then > 0:
                    a3, _ = value_a(b3)
                    now = {"A": v_a, "C": values["C"]}.get(kind, equity)
                    then = {"A": a3, "C": value_c(b3, a3)}.get(kind, common_equity(b3))
                    row["v_cb_cagr_3y"] = cb.cagr_3y(now / shares_now, then / shares_then)
        kind = cb.assign_type(pv)
        if row.get("v_cb_cagr_3y") not in (None, "") and float(row["v_cb_cagr_3y"]) < cb.EROSION_MAX:
            flags.append("价值流失")
        row.update(cb_type=kind, pv_cb=round(pv[kind], 3) if kind else "",
                   **{f"pv_{k.lower()}": (round(pv[k], 3) if pv.get(k) else "") for k in "ABCD"},
                   v_cb_yi=round(v / 1e8, 2) if v else "",
                   cash_verified="yes" if len(profits_hkd) == 3 and cb.cash_verified(divs_hkd, profits_hkd) else "no",
                   dividend_yield=round(divs_hkd[-1] / mcap, 4) if mcap else "",
                   payout_3y=round(sum(divs_hkd) / sum(profits_hkd), 3) if profits_hkd and sum(profits_hkd) > 0 else "",
                   auto_flags="；".join(flags))
        if isinstance(row.get("v_cb_cagr_3y"), float):
            row["v_cb_cagr_3y"] = round(row["v_cb_cagr_3y"], 4)
        out.append(row)
    three_cache_path.write_text(json.dumps(three_cache, ensure_ascii=False), encoding="utf-8")
    blocked = {"价值流失", "现金消耗"}
    candidates = [r for r in out if r["cb_type"] and not blocked & set(filter(None, r["auto_flags"].split("；")))]
    liq = liquidity([r["security_code"] for r in candidates], signal_date, cny)
    for r in candidates:
        value = liq.get(r["security_code"])
        r["liquidity_60d_wan"] = round(value, 0) if value is not None else ""
        if value is not None and value < cb.LIQUIDITY_MIN_WAN:
            r["auto_flags"] = "；".join(filter(None, [r["auto_flags"], "流动性不足"]))
    print(f"汇率日 {fx_day}（1 人民币 = {cny:.4f} 港元）；港股通名单 沪 {len(sh)}（{south['sh_date']}）、深 {len(sz)}（{south['sz_date']}）")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--signal-date", required=True, help="港股价格日 YYYY-MM-DD（港股交易日）")
    ap.add_argument("--reuse-raw", action="store_true", help="复用已缓存的报表、名单与行情")
    ap.add_argument("--dry-run", action="store_true", help="只写逐家读数，不改池表、不写决策日志")
    args = ap.parse_args()
    rows = screen(args.signal_date, args.reuse_raw)
    cb._write(SCREEN, sorted(rows, key=lambda r: (r["cb_type"] == "", r["cb_type"], float(r["pv_cb"] or 9), r["security_code"])),
              SCREEN_FIELDS)
    kinds = {k: sum(1 for r in rows if r["cb_type"] == k) for k in "ABCD"}
    if args.dry_run:
        print(f"逐家读数 {len(rows)}；P/V_cb ≤ 1.0：{kinds}（试跑，未改池表）")
        return 0
    stats = cb.update_pool(rows, args.signal_date, path=POOL, fields=POOL_FIELDS, auto_fields=AUTO_FIELDS)
    cb.pool_summary_log(POOL, f"cigar_butt_screen_hk:{args.signal_date}", args.signal_date, "POOL_HK", "港股烟蒂池",
                        f"港股各家最新定期报告、价格日 {args.signal_date}；逐家读数 {len(rows)}；新增 {stats['added']}、"
                        f"移出 {stats['removed']}、标退出 {stats['exited']}",
                        "data/raw/financials_market_hk/", "scripts/screen_cigar_butts_hk.py")
    print(f"逐家读数 {len(rows)}；P/V_cb ≤ 1.0：{kinds}；池表新增 {stats['added']}、移出 {stats['removed']}、标退出 {stats['exited']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
