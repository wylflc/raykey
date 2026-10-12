#!/usr/bin/env python3
"""神奇公式（盈利收益率 + 资本回报率）季度回测：沪深 300 历年成分，并在工作流程回测宇宙上与 `P/V` 排序对照。

实验脚本，只读生产数据，不改任何口径；口径、臂与读数见预登记
`data/experiments/exp_magic_formula_csi300_20261012/preregister.md`，跑完不换。

    python3 scripts/experimental/magic_formula_backtest.py \
        --inputs data/scratch/experiments/exp_magic_formula_csi300_20261012 \
        --out-dir data/experiments/exp_magic_formula_csi300_20261012
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from backtest_valuation_strategy import STAMP_HISTORY, USER_FEES  # noqa: E402
from corporate_actions import event_map, price_terms  # noqa: E402

OHLCV = ROOT / "data/raw/ohlcv"
ACTIONS = ROOT / "data/raw/corporate_actions/a_share_corporate_actions.csv"
INDEX = OHLCV / "INDEX_000300.csv"
PANEL = ROOT / "data/processed/pit_attention/panel_moat_bank_v6b.csv"
STATES = ROOT / "data/processed/a_share_daily_states_adopted.csv"
RISK_FREE = ROOT / "data/reference/cost_of_equity_inputs.csv"
CANDIDATES = ROOT / "data/processed/daily_buy_candidates.csv"
SUMMARY_FINANCIALS = ROOT / "data/raw/financials"      # 逐期业绩报表：每股净资产，用于裁决两种股数口径
CDR_RATIO = {"689009": 10.0}                           # 九号公司：行情按存托凭证报价，1 股 = 10 份

CALENDAR_START = "2005-01-04"
END = "2026-08-07"
FIRST_SIGNAL = "2005-06-30"
STALE_DAYS = 550                       # 最新报告期距信号日超过此数即视为无可用财报
EV_FLOOR = 0.10                        # EV 下限 = 总市值 × 10%
CAPITAL_FLOOR = 0.01                   # 投入有形资本下限 = 总资产 × 1%
DEADLINES = {"03": "{y}-04-30", "06": "{y}-08-31", "09": "{y}-10-31", "12": "{n}-04-30"}
EXCLUDED = ("金融业", "电力、热力、燃气及水生产和供应业")
DEBT_SHORT = ("SHORT_LOAN", "NONCURRENT_LIAB_1YEAR", "SHORT_BOND_PAYABLE")
DEBT_LONG = ("LONG_LOAN", "BOND_PAYABLE", "LEASE_LIAB")
TEXT_COLUMNS = ("SECURITY_CODE", "SECURITY_NAME_ABBR", "ORG_TYPE", "REPORT_DATE", "REPORT_TYPE", "NOTICE_DATE", "UPDATE_DATE")


# ------------------------------------------------------------------ 数据
def load_spans(path: Path) -> dict[str, list[tuple[str, str]]]:
    spans: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["security_code"].isdigit():
                spans[row["security_code"]].append((row["effective_from"], row.get("effective_to") or "9999-12-31"))
    return spans


def members(spans: dict[str, list[tuple[str, str]]], day: str) -> list[str]:
    return sorted(code for code, items in spans.items() if any(a <= day <= b for a, b in items))


def load_calendar() -> tuple[list[str], np.ndarray]:
    frame = pd.read_csv(INDEX, usecols=["date", "close"])
    frame = frame[(frame["date"] >= CALENDAR_START) & (frame["date"] <= END)]
    return frame["date"].tolist(), frame["close"].to_numpy(float)


def exright_affine(days: list[str], events: dict[str, tuple]) -> tuple[np.ndarray, np.ndarray]:
    """每个报价日「当日口径 → 末日口径」的仿射映射 q = A·p + B（与引擎 `exright_affine` 同式，§11.4）。"""
    n = len(days)
    scale, shift = np.ones(n), np.zeros(n)
    event_days = sorted(d for d in events if days[0] < d <= days[-1]) if days else []
    cursor, a, b = len(event_days) - 1, 1.0, 0.0
    for i in range(n - 1, -1, -1):
        while cursor >= 0 and event_days[cursor] > days[i]:
            cash, ratio, rr, rp = price_terms(events[event_days[cursor]])
            a, b = a / (1.0 + ratio + rr), b + a * (rr * rp - cash) / (1.0 + ratio + rr)
            cursor -= 1
        scale[i], shift[i] = a, b
    return scale, shift


class Market:
    """行情矩阵：收盘、是否可成交、含分红日收益乘数、前复权收盘（算均线用）。"""

    def __init__(self, codes: list[str], calendar: list[str]):
        self.codes, self.calendar = codes, calendar
        self.col = {code: j for j, code in enumerate(codes)}
        self.row = {day: i for i, day in enumerate(calendar)}
        n_days, n_codes = len(calendar), len(codes)
        self.close = np.full((n_days, n_codes), np.nan)
        self.adjusted = np.full((n_days, n_codes), np.nan)
        self.tradable = np.zeros((n_days, n_codes), bool)
        self.gross = np.ones((n_days, n_codes))
        self.last_bar = np.full(n_codes, -1)
        self.anomalies = 0
        with ACTIONS.open(newline="", encoding="utf-8") as handle:
            self.events = event_map(csv.DictReader(handle))
        for code in codes:
            path = OHLCV / f"{code}.csv"
            if not path.exists():
                continue
            frame = pd.read_csv(path, usecols=["date", "close", "volume"], dtype={"date": str})
            frame = frame[(frame["date"] >= calendar[0]) & (frame["date"] <= calendar[-1]) & (frame["close"] > 0)]
            frame = frame[frame["date"].isin(self.row)]
            if frame.empty:
                continue
            days = frame["date"].tolist()
            closes = frame["close"].to_numpy(float)
            volume = frame["volume"].to_numpy(float)
            rows = np.fromiter((self.row[d] for d in days), int, len(days))
            scale, shift = exright_affine(days, self.events.get(code, {}))
            j = self.col[code]
            self.close[rows, j] = closes
            self.adjusted[rows, j] = scale * closes + shift
            self.tradable[rows, j] = volume > 0
            self.last_bar[j] = rows[-1]
            if len(days) > 1:
                base = scale[:-1] * closes[:-1] + shift[:-1] - shift[1:]
                gross = np.where(base > 0, closes[1:] * scale[1:] / np.where(base > 0, base, 1.0), 1.0)
                self.anomalies += int((base <= 0).sum())
                self.gross[rows[1:], j] = gross
        self.close_ffill = pd.DataFrame(self.close).ffill().to_numpy()
        adjusted = pd.DataFrame(self.adjusted).ffill()
        self.ma20 = adjusted.rolling(20, min_periods=20).mean().to_numpy()
        self.ma60 = adjusted.rolling(60, min_periods=60).mean().to_numpy()
        self.adjusted_ffill = adjusted.to_numpy()

    def share_factor(self, code: str, after: str, upto: str) -> float:
        factor = 1.0
        for ex_day, event in self.events.get(code, {}).items():
            if after < ex_day <= upto:
                _, ratio, rr, _ = price_terms(event)
                factor *= 1.0 + ratio + rr
        return factor


def available_on(report_date: str, notice: str) -> str:
    year, month = int(report_date[:4]), report_date[5:7]
    deadline = DEADLINES.get(month, "{n}-04-30").format(y=year, n=year + 1)
    notice = (notice or "")[:10]
    # 东财对被重述的历史期给的是重述版公告日（约晚一年），故按法定披露截止日封顶
    return min(notice, deadline) if len(notice) == 10 and notice > report_date else deadline


class Fundamentals:
    def __init__(self, inputs: Path):
        self.income: dict[str, dict[str, dict]] = defaultdict(dict)
        self.balance: dict[str, dict[str, dict]] = defaultdict(dict)
        self.names: dict[str, str] = {}
        self.org_type: dict[str, str] = {}
        for kind, store in (("income", self.income), ("balance", self.balance)):
            frame = pd.read_csv(inputs / f"{kind}_q.csv", dtype={"SECURITY_CODE": str}, low_memory=False)
            frame["SECURITY_CODE"] = frame["SECURITY_CODE"].str.zfill(6)
            for column in frame.columns:
                if column not in TEXT_COLUMNS:
                    frame[column] = pd.to_numeric(frame[column], errors="coerce")
            frame["report"] = frame["REPORT_DATE"].astype(str).str[:10]
            frame["avail"] = [available_on(r, n if isinstance(n, str) else "")
                              for r, n in zip(frame["report"], frame["NOTICE_DATE"])]
            frame = frame.drop_duplicates(["SECURITY_CODE", "report"], keep="first")
            for record in frame.to_dict("records"):
                code = record["SECURITY_CODE"]
                store[code][record["report"]] = record
                if kind == "income":
                    if isinstance(record.get("SECURITY_NAME_ABBR"), str) and code not in self.names:
                        self.names[code] = record["SECURITY_NAME_ABBR"]
                    if isinstance(record.get("ORG_TYPE"), str):
                        self.org_type.setdefault(code, record["ORG_TYPE"])
        self.industry: dict[str, str] = {}
        with (inputs / "industry.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                code = row["security_code"].zfill(6)
                if row.get("csrc_industry"):
                    self.industry[code] = row["csrc_industry"]
                if row.get("security_name") and code not in self.names:
                    self.names[code] = row["security_name"]
        self._income_keys = {c: sorted(v) for c, v in self.income.items()}
        self._balance_keys = {c: sorted(v) for c, v in self.balance.items()}
        self.bps: dict[tuple[str, str], float] = {}
        wanted = set(self.balance) | set(self.income)
        for path in sorted(SUMMARY_FINANCIALS.glob("*.csv")):
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    if row["security_code"] in wanted and row.get("bps"):
                        try:
                            self.bps[row["security_code"], row["report_date"][:10]] = float(row["bps"])
                        except ValueError:
                            pass

    @staticmethod
    def _num(record: dict, key: str) -> float:
        value = record.get(key)
        return float(value) if isinstance(value, (int, float)) and not math.isnan(value) else 0.0

    def _ebit(self, record: dict, mode: str = "total") -> float | None:
        """total：利润总额 + 财务费用（预登记主口径）；core：营业收入减营业成本、税金及附加与销售、管理、研发费用。"""
        if mode == "core":
            revenue = record.get("OPERATE_INCOME")
            if not isinstance(revenue, (int, float)) or math.isnan(revenue):
                return None
            return float(revenue) - sum(self._num(record, k) for k in (
                "OPERATE_COST", "OPERATE_TAX_ADD", "SALE_EXPENSE", "MANAGE_EXPENSE", "RESEARCH_EXPENSE"))
        profit = record.get("TOTAL_PROFIT")
        if not isinstance(profit, (int, float)) or math.isnan(profit):
            return None
        return float(profit) + self._num(record, "FINANCE_EXPENSE")

    def _latest(self, store, keys, code: str, day: str) -> dict | None:
        for report in reversed(keys.get(code, [])):
            record = store[code][report]
            if report < day and record["avail"] <= day:
                return record
        return None

    def ebit_ttm(self, code: str, day: str, mode: str = "total") -> tuple[float, str] | None:
        latest = self._latest(self.income, self._income_keys, code, day)
        if latest is None or (date.fromisoformat(day) - date.fromisoformat(latest["report"])).days > STALE_DAYS:
            return None
        report = latest["report"]
        if report[5:7] != "12":
            year = int(report[:4])
            annual = self.income[code].get(f"{year - 1}-12-31")
            same = self.income[code].get(f"{year - 1}{report[4:]}")
            parts = [self._ebit(latest, mode)] + [self._ebit(r, mode) if r and r["avail"] <= day else None for r in (annual, same)]
            if all(p is not None for p in parts):
                return parts[0] + parts[1] - parts[2], report
            latest = next((self.income[code][r] for r in reversed(self._income_keys[code])
                           if r[5:7] == "12" and r < day and self.income[code][r]["avail"] <= day), None)
            if latest is None or (date.fromisoformat(day) - date.fromisoformat(latest["report"])).days > STALE_DAYS + 190:
                return None
        value = self._ebit(latest, mode)
        return (value, latest["report"]) if value is not None else None

    def eps_shares(self, code: str, day: str) -> tuple[float, str] | None:
        for report in reversed(self._income_keys.get(code, [])):
            record = self.income[code][report]
            if report[5:7] == "12" and report < day and record["avail"] <= day:
                eps, profit = record.get("BASIC_EPS"), record.get("PARENT_NETPROFIT")
                if all(isinstance(v, (int, float)) and not math.isnan(v) for v in (eps, profit)) and abs(eps) >= 0.02:
                    shares = profit / eps
                    return (shares, report) if shares > 0 else None
                return None
        return None

    def shares(self, code: str, day: str, market: Market, sheet: dict | None = None) -> float:
        """信号日总股本。主口径是最近一期资产负债表的股本（按其后的送转配折算）；它与「归母净利 ÷ 基本每股收益」
        相差 25% 以上时（面值不是 1 元、无面值股、借壳上市的合并报表股本），用「归母权益 ÷ 每股净资产」裁决取近者。"""
        sheet = sheet or self._latest(self.balance, self._balance_keys, code, day)
        first = self._num(sheet, "SHARE_CAPITAL") * market.share_factor(code, sheet["report"], day) if sheet else 0.0
        implied = self.eps_shares(code, day)
        if implied:
            second = implied[0] * market.share_factor(code, implied[1], day)
            if first <= 0:
                first = second
            elif not 0.8 <= first / second <= 1.25:
                bps = self.bps.get((code, sheet["report"]), 0.0)
                equity = self._num(sheet, "TOTAL_PARENT_EQUITY") - self._num(sheet, "OTHER_EQUITY_TOOL")
                if bps > 0.05 and equity > 0:
                    third = equity / bps * market.share_factor(code, sheet["report"], day)
                    first = min((first, second), key=lambda v: abs(math.log(v / third)))
                elif not 0.5 <= first / second <= 2.0:
                    first = second
        return first * CDR_RATIO.get(code, 1.0)

    def metrics(self, code: str, day: str, close: float, market: Market, mode: str = "total") -> dict | None:
        ttm = self.ebit_ttm(code, day, mode)
        sheet = self._latest(self.balance, self._balance_keys, code, day)
        if ttm is None or sheet is None or not close or math.isnan(close):
            return None
        num = self._num
        total_assets = num(sheet, "TOTAL_ASSETS")
        shares = self.shares(code, day, market, sheet)
        if shares <= 0 or total_assets <= 0:
            return None
        market_cap = close * shares
        short_debt = sum(num(sheet, k) for k in DEBT_SHORT)
        debt = short_debt + sum(num(sheet, k) for k in DEBT_LONG)
        trading = sheet.get("TRADE_FINASSET_NOTFVTPL")
        trading = float(trading) if isinstance(trading, (int, float)) and not math.isnan(trading) else num(sheet, "TRADE_FINASSET")
        cash = num(sheet, "MONETARYFUNDS") + trading
        ev = market_cap + debt + num(sheet, "MINORITY_EQUITY") + num(sheet, "OTHER_EQUITY_TOOL") - cash
        ev = max(ev, EV_FLOOR * market_cap)
        working = (num(sheet, "TOTAL_CURRENT_ASSETS") - cash) - (num(sheet, "TOTAL_CURRENT_LIAB") - short_debt)
        capital = max(working, 0.0) + num(sheet, "FIXED_ASSET") + num(sheet, "CIP")
        capital = max(capital, CAPITAL_FLOOR * total_assets)
        ebit = ttm[0]
        return dict(ebit=ebit, ev=ev, market_cap=market_cap, capital=capital, ey=ebit / ev, roc=ebit / capital,
                    income_period=ttm[1], balance_period=sheet["report"])

    def eligible(self, code: str, real_estate: bool = True, utilities_ok: bool = False) -> bool:
        if self.org_type.get(code) != "通用":
            return False
        industry = self.industry.get(code, "")
        if industry.startswith("金融业"):
            return False
        if not utilities_ok and industry.startswith(EXCLUDED[1]):
            return False
        return real_estate or not industry.startswith("房地产业")


def load_pv(signal_days: set[str]) -> dict[str, dict[str, float]]:
    """逐日状态里各信号日的 `valuation_ratio`（候选侧 P/V）。2 GB 文件只流式读一遍。"""
    out: dict[str, dict[str, float]] = defaultdict(dict)
    with STATES.open(encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split(",")
        i_code, i_date, i_ratio = header.index("security_code"), header.index("date"), header.index("valuation_ratio")
        for line in handle:
            parts = line.split(",", i_ratio + 1)
            if parts[i_date] in signal_days:
                try:
                    ratio = float(parts[i_ratio])
                except ValueError:
                    continue
                if ratio > 0:
                    out[parts[i_date]][parts[i_code]] = ratio
    return out


# ------------------------------------------------------------------ 排名与组合
def rank_desc(values: dict[str, float]) -> dict[str, int]:
    return {code: i for i, code in enumerate(sorted(values, key=lambda c: -values[c]), 1)}


def magic_order(table: dict[str, dict]) -> list[str]:
    ey, roc = rank_desc({c: m["ey"] for c, m in table.items()}), rank_desc({c: m["roc"] for c, m in table.items()})
    for code, row in table.items():
        row["rank_ey"], row["rank_roc"], row["score"] = ey[code], roc[code], ey[code] + roc[code]
    return sorted(table, key=lambda c: (table[c]["score"], -table[c]["ey"]))


def stamp_rate(day: str, side: str) -> float:
    rate, both = next((r, b) for start, r, b in reversed(STAMP_HISTORY) if start <= day)
    return rate if side == "sell" or both else 0.0


def simulate(market: Market, plans: dict[int, dict], start: int, slippage_bp: float = 0.0) -> dict:
    """plans: {成交日行号: {ranked: [列号…], n: 目标只数} 或 {weights: {列号: 权重}}}；成交日收盘调到目标。"""
    n_days, n_codes = market.gross.shape
    hold, cash = np.zeros(n_codes), 1.0
    nav = np.full(n_days, np.nan)
    turnover, cost_total, counts = [], 0.0, []
    delisted = market.last_bar < n_days - 20
    fee = USER_FEES["commission"] + USER_FEES["transfer"] + slippage_bp / 1e4
    for t in range(start, n_days):
        hold *= market.gross[t]
        plan = plans.get(t)
        if plan is not None:
            day = market.calendar[t]
            dead = (hold > 0) & delisted & (market.last_bar < t)
            cash += hold[dead].sum()
            hold[dead] = 0.0
            tradable = market.tradable[t]
            frozen = (hold > 0) & ~tradable
            before = cash + hold.sum()
            free = before - hold[frozen].sum()
            target = np.zeros(n_codes)
            if "weights" in plan:
                picks = [j for j in plan["weights"] if tradable[j]]
                total = sum(plan["weights"][j] for j in picks)
                for j in picks:
                    target[j] = free * plan["weights"][j] / total if total > 0 else 0.0
            else:
                slots = max(plan["n"] - int(frozen.sum()), 0)
                picks = [j for j in plan["ranked"] if tradable[j]][:slots]
                for j in picks:
                    target[j] = free / len(picks)
            delta = np.where(frozen, 0.0, target - hold)
            sells, buys = -delta[delta < 0].sum(), delta[delta > 0].sum()
            fee_sell, fee_buy = fee + stamp_rate(day, "sell"), fee + stamp_rate(day, "buy")
            available = cash + sells * (1.0 - fee_sell)
            k = min(1.0, available / (buys * (1.0 + fee_buy))) if buys > 0 else 0.0
            hold = np.where(delta < 0, hold + delta, hold + np.where(delta > 0, delta * k, 0.0))
            cash = available - buys * k * (1.0 + fee_buy)
            cost_total += (sells * fee_sell + buys * k * fee_buy) / before
            turnover.append(sells / before)
            counts.append(int((hold > 1e-12).sum()))
        nav[t] = cash + hold.sum()
    return dict(nav=nav, turnover=turnover, cost=cost_total, counts=counts)


# ------------------------------------------------------------------ 读数
def risk_free_daily(calendar: list[str]) -> np.ndarray:
    observed, rates = [], []
    with RISK_FREE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            observed.append(row["observed_on"])
            rates.append(float(row["risk_free_rate"]))
    out = np.zeros(len(calendar))
    for i in range(1, len(calendar)):
        k = bisect_right(observed, calendar[i - 1])
        if k:
            gap = (date.fromisoformat(calendar[i]) - date.fromisoformat(calendar[i - 1])).days
            out[i] = rates[k - 1] * gap / 365.25
    return out


def stats(nav: np.ndarray, calendar: list[str], start: int, rf: np.ndarray, end: int | None = None) -> dict:
    end = len(calendar) - 1 if end is None else end
    series = nav[start:end + 1]
    days = calendar[start:end + 1]
    years = (date.fromisoformat(days[-1]) - date.fromisoformat(days[0])).days / 365.25
    ret = series[1:] / series[:-1] - 1.0
    peak = np.maximum.accumulate(series)
    drawdown = series / peak - 1.0
    trough = int(drawdown.argmin())
    top = int(series[:trough + 1].argmax())
    excess = ret - rf[start + 1:end + 1]
    return dict(start=days[0], end=days[-1], final=float(series[-1] / series[0]),
                cagr=float((series[-1] / series[0]) ** (1.0 / years) - 1.0) if years > 0 else float("nan"),
                vol=float(ret.std(ddof=1) * math.sqrt(244)),
                sharpe=float(excess.mean() / excess.std(ddof=1) * math.sqrt(244)) if excess.std(ddof=1) > 0 else float("nan"),
                max_drawdown=float(-drawdown.min()), drawdown_from=days[top], drawdown_to=days[trough])


def yearly(nav: np.ndarray, calendar: list[str], start: int) -> dict[str, float]:
    out, prev = {}, nav[start]
    for i in range(start + 1, len(calendar)):
        if i == len(calendar) - 1 or calendar[i + 1][:4] != calendar[i][:4]:
            out[calendar[i][:4]] = float(nav[i] / prev - 1.0)
            prev = nav[i]
    return out


def blocks(nav: np.ndarray, calendar: list[str], start: int, months: int = 60) -> list[dict]:
    """自末日往回每 60 个月一块、首尾相接。"""
    out, end = [], len(calendar) - 1
    while True:
        end_day = date.fromisoformat(calendar[end])
        year, month = end_day.year - months // 12, end_day.month
        target = date(year, month, min(end_day.day, 28)).isoformat()
        begin = bisect_right(calendar, target) - 1
        if begin < start:
            break
        years = (end_day - date.fromisoformat(calendar[begin])).days / 365.25
        out.append(dict(start=calendar[begin], end=calendar[end], cagr=float((nav[end] / nav[begin]) ** (1 / years) - 1)))
        end = begin
    return out[::-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--inputs", type=Path, required=True, help="magic_formula_fetch_inputs.py 的输出目录")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    (out_dir / "picks").mkdir(parents=True, exist_ok=True)

    calendar, index_close = load_calendar()
    csi = load_spans(out_dir / "csi300_membership.csv")
    panel = load_spans(PANEL)
    fundamentals = Fundamentals(args.inputs)
    with CANDIDATES.open(newline="", encoding="utf-8") as handle:
        candidates = list(csv.DictReader(handle))
    codes = sorted(set(csi) | set(panel) | {row["security_code"] for row in candidates})
    market = Market(codes, calendar)
    rf = risk_free_daily(calendar)
    print(f"交易日 {len(calendar)}（{calendar[0]}～{calendar[-1]}），代码 {len(codes)}，除权基数异常 {market.anomalies}", flush=True)

    quarter_ends = [calendar[i] for i in range(len(calendar) - 1)
                    if calendar[i][5:7] in ("03", "06", "09", "12") and calendar[i + 1][5:7] != calendar[i][5:7]]
    signals = [d for d in quarter_ends if FIRST_SIGNAL <= d]
    annual = [calendar[i] for i in range(len(calendar) - 1)
              if calendar[i][5:7] == "04" and calendar[i + 1][5:7] == "05" and calendar[i] >= FIRST_SIGNAL]
    pv = load_pv(set(signals))
    print(f"季末信号日 {len(signals)}（{signals[0]}～{signals[-1]}），有 P/V 的信号日 {len(pv)}", flush=True)

    def table_for(universe: list[str], day: str, mode: str = "total", **kwargs) -> dict[str, dict]:
        i = market.row[day]
        out = {}
        for code in universe:
            j = market.col.get(code)
            if j is None or not market.tradable[i, j] or not fundamentals.eligible(code, **kwargs):
                continue
            row = fundamentals.metrics(code, day, market.close[i, j], market, mode)
            if row is not None and math.isfinite(row["ey"]) and math.isfinite(row["roc"]):
                out[code] = row
        return out

    cols = market.col
    plans: dict[str, dict[int, dict]] = defaultdict(dict)
    picks_log: dict[str, list[dict]] = defaultdict(list)
    coverage, overlap, latest = [], [], {}
    w_start = None

    def record(arm: str, day: str, ordered: list[str], n: int, table: dict[str, dict], extra: dict | None = None):
        for position, code in enumerate(ordered[:n], 1):
            row = table.get(code, {})
            picks_log[arm].append(dict(signal_date=day, position=position, security_code=code,
                                       security_name=fundamentals.names.get(code, ""),
                                       ey=row.get("ey"), roc=row.get("roc"), score=row.get("score"),
                                       pv=(extra or {}).get(code)))

    for day in signals + [d for d in annual if d not in signals]:
        i = market.row[day]
        execute = i + 1
        universe = members(csi, day)
        table = table_for(universe, day)
        order = magic_order(table)
        if day in annual:
            plans["MF30_Y"][execute] = dict(ranked=[cols[c] for c in order], n=30)
            record("MF30_Y", day, order, 30, table)
        if day not in signals:
            continue
        for arm, n in (("MF30", 30), ("MF20", 20), ("MF50", 50)):
            plans[arm][execute] = dict(ranked=[cols[c] for c in order], n=n)
            record(arm, day, order, n, table)
        by_ey = sorted(table, key=lambda c: -table[c]["ey"])
        by_roc = sorted(table, key=lambda c: -table[c]["roc"])
        plans["EY30"][execute] = dict(ranked=[cols[c] for c in by_ey], n=30)
        plans["ROC30"][execute] = dict(ranked=[cols[c] for c in by_roc], n=30)
        record("EY30", day, by_ey, 30, table)
        record("ROC30", day, by_roc, 30, table)
        trend = [c for c in order if market.adjusted_ffill[i, cols[c]] > market.ma20[i, cols[c]] > market.ma60[i, cols[c]]]
        plans["MF30_T"][execute] = dict(ranked=[cols[c] for c in trend], n=30)
        record("MF30_T", day, trend, 30, table)
        no_re = {c: dict(m) for c, m in table.items() if fundamentals.eligible(c, real_estate=False)}
        order_re = magic_order(no_re)
        plans["MF30_RE"][execute] = dict(ranked=[cols[c] for c in order_re], n=30)
        record("MF30_RE", day, order_re, 30, no_re)
        core = table_for(universe, day, mode="core")
        order_core = magic_order(core)
        plans["MF30_OP"][execute] = dict(ranked=[cols[c] for c in order_core], n=30)
        record("MF30_OP", day, order_core, 30, core)
        plans["EW_ELIG"][execute] = dict(weights={cols[c]: 1.0 for c in table})
        all_members = [c for c in universe if c in cols and market.tradable[i, cols[c]]]
        caps = {}
        for code in all_members:
            shares = fundamentals.shares(code, day, market)
            if shares > 0:
                caps[code] = shares * market.close[i, cols[code]]
        plans["CW300"][execute] = dict(weights={cols[c]: v for c, v in caps.items()})
        plans["EW300"][execute] = dict(weights={cols[c]: 1.0 for c in all_members})
        coverage.append(dict(signal_date=day, members=len(universe), tradable=len(all_members), with_market_cap=len(caps),
                             non_financial=sum(fundamentals.eligible(c, utilities_ok=True) for c in universe),
                             eligible_ranked=len(table)))
        if day == signals[-1]:
            latest["csi300"] = (day, table, order)

        # 工作流程回测宇宙：同一组合构造下比较 P/V 排序与神奇公式排序
        ratios = pv.get(day, {})
        w_universe = members(panel, day)
        w_table = {c: m for c, m in table_for(w_universe, day, utilities_ok=True).items() if c in ratios}
        if w_start is None and len(w_table) >= 30:
            w_start = execute
        if w_start is not None and w_table:
            n = max(10, round(0.2 * len(w_table)))
            w_order = magic_order(w_table)
            by_pv = sorted(w_table, key=lambda c: ratios[c])
            pos_mf = {c: k for k, c in enumerate(w_order, 1)}
            pos_pv = {c: k for k, c in enumerate(by_pv, 1)}
            both = sorted(w_table, key=lambda c: (pos_mf[c] + pos_pv[c], ratios[c]))
            for arm, ordered in (("W_MF", w_order), ("W_PV", by_pv), ("W_PVMF", both)):
                plans[arm][execute] = dict(ranked=[cols[c] for c in ordered], n=n)
                record(arm, day, ordered, n, w_table, ratios)
            plans["W_EW"][execute] = dict(weights={cols[c]: 1.0 for c in w_table})
            everyone = sorted((c for c in w_universe if c in ratios and c in cols and market.tradable[i, cols[c]]),
                              key=lambda c: ratios[c])
            n_all = max(10, round(0.2 * len(everyone)))
            plans["W_PV_ALL"][execute] = dict(ranked=[cols[c] for c in everyone], n=n_all)
            record("W_PV_ALL", day, everyone, n_all, w_table, ratios)
            overlap.append(dict(signal_date=day, eligible=len(w_table), n=n, universe_with_pv=len(everyone),
                                pv_mf_overlap=len(set(by_pv[:n]) & set(w_order[:n])),
                                rank_corr=float(np.corrcoef([pos_mf[c] for c in w_table], [pos_pv[c] for c in w_table])[0, 1])))
            if day == signals[-1]:
                latest["workflow"] = (day, w_table, w_order, ratios)

    first_exec = market.row[signals[0]] + 1
    plans["MF30_Y"].setdefault(first_exec, plans["MF30"][first_exec])    # 首期与季度臂同日建仓，其后每年 4 月末换一次
    results, navs = {}, {"date": calendar}
    for arm, plan in plans.items():
        start = w_start if arm.startswith("W_") else min(plan)
        sim = simulate(market, plan, start)
        navs[arm] = sim["nav"]
        span_years = (date.fromisoformat(calendar[-1]) - date.fromisoformat(calendar[start])).days / 365.25
        results[arm] = dict(stats(sim["nav"], calendar, start, rf), yearly=yearly(sim["nav"], calendar, start),
                            blocks=blocks(sim["nav"], calendar, start),
                            turnover_per_year=float(sum(sim["turnover"]) / span_years),
                            cost_per_year=float(sim["cost"] / span_years),
                            avg_holdings=float(np.mean(sim["counts"])), rebalances=len(plan))
        if w_start is not None and not arm.startswith("W_"):
            results[arm]["common"] = stats(sim["nav"], calendar, w_start, rf)
    slip = simulate(market, plans["MF30"], first_exec, slippage_bp=20.0)
    results["MF30_slip20"] = dict(stats(slip["nav"], calendar, first_exec, rf), cost_per_year=float(
        slip["cost"] / ((date.fromisoformat(calendar[-1]) - date.fromisoformat(calendar[first_exec])).days / 365.25)))
    navs["MF30_slip20"] = slip["nav"]
    index_nav = np.full(len(calendar), np.nan)
    index_nav[first_exec:] = index_close[first_exec:] / index_close[first_exec]
    navs["INDEX_000300"] = index_nav
    results["INDEX_000300"] = dict(stats(index_nav, calendar, first_exec, rf), yearly=yearly(index_nav, calendar, first_exec),
                                   blocks=blocks(index_nav, calendar, first_exec))
    if w_start is not None:
        results["INDEX_000300"]["common"] = stats(index_close / index_close[w_start], calendar, w_start, rf)
    total_return_path = out_dir / "h00300.csv"          # 中证官网沪深 300 全收益指数（含分红）
    if total_return_path.exists():
        frame = pd.read_csv(total_return_path, dtype={"date": str}).set_index("date")["close"]
        series = frame.reindex(calendar).ffill().to_numpy(float)
        tr_nav = np.full(len(calendar), np.nan)
        tr_nav[first_exec:] = series[first_exec:] / series[first_exec]
        navs["H00300"] = tr_nav
        results["H00300"] = dict(stats(tr_nav, calendar, first_exec, rf), yearly=yearly(tr_nav, calendar, first_exec),
                                 blocks=blocks(tr_nav, calendar, first_exec))
        if w_start is not None:
            results["H00300"]["common"] = stats(series / series[w_start], calendar, w_start, rf)

    def paired(a: str, b: str) -> dict:
        ya, yb = results[a]["yearly"], results[b]["yearly"]
        years = [y for y in ya if y in yb]
        diff = {y: ya[y] - yb[y] for y in years}
        return dict(years=diff, positive=sum(v > 0 for v in diff.values()), n=len(diff),
                    median=float(np.median(list(diff.values()))) if diff else None)

    pairs = {f"{a}-{b}": paired(a, b) for a, b in (
        ("MF30", "H00300"), ("MF30", "CW300"), ("MF30", "EW_ELIG"), ("MF30", "EW300"), ("MF30_T", "MF30"), ("MF30_Y", "MF30"), ("MF30_OP", "MF30"),
        ("W_PV", "W_EW"), ("W_MF", "W_EW"), ("W_PVMF", "W_EW"), ("W_PV", "W_MF"), ("W_PVMF", "W_PV")) if a in results and b in results}

    # 最近一次排名与当前核心池对照（P/V 取 10-12 扫描，财报取最新可得）
    def dump_table(name: str, table: dict[str, dict], order: list[str], ratios: dict | None = None):
        with (out_dir / name).open("w", newline="", encoding="utf-8") as handle:
            fields = ["position", "security_code", "security_name", "industry", "ey", "roc", "rank_ey", "rank_roc", "score",
                      "pv", "ebit_yi", "ev_yi", "market_cap_yi", "capital_yi", "income_period", "balance_period"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for position, code in enumerate(order, 1):
                m = table[code]
                writer.writerow(dict(position=position, security_code=code, security_name=fundamentals.names.get(code, ""),
                                     industry=fundamentals.industry.get(code, ""), ey=round(m["ey"], 4), roc=round(m["roc"], 4),
                                     rank_ey=m["rank_ey"], rank_roc=m["rank_roc"], score=m["score"],
                                     pv=round(ratios[code], 4) if ratios and code in ratios else "",
                                     ebit_yi=round(m["ebit"] / 1e8, 2), ev_yi=round(m["ev"] / 1e8, 2),
                                     market_cap_yi=round(m["market_cap"] / 1e8, 2), capital_yi=round(m["capital"] / 1e8, 2),
                                     income_period=m["income_period"], balance_period=m["balance_period"]))

    if "csi300" in latest:
        dump_table("latest_rank_csi300.csv", latest["csi300"][1], latest["csi300"][2])
    if "workflow" in latest:
        dump_table("latest_rank_workflow.csv", latest["workflow"][1], latest["workflow"][2], latest["workflow"][3])
    scan_day = candidates[0]["trade_date"]
    pool_table, pool_pv = {}, {}
    for row in candidates:
        code = row["security_code"]
        try:
            close, ratio = float(row["close"]), float(row["model_pv"])
        except ValueError:
            continue
        if fundamentals.eligible(code, utilities_ok=True):
            m = fundamentals.metrics(code, scan_day, close, market)
            if m is not None:
                pool_table[code], pool_pv[code] = m, ratio
    if pool_table:
        dump_table("current_pool_crosscheck.csv", pool_table, magic_order(pool_table), pool_pv)

    pd.DataFrame(navs).iloc[first_exec:].to_csv(out_dir / "nav.csv", index=False, float_format="%.6f")
    for arm, rows in picks_log.items():
        pd.DataFrame(rows).to_csv(out_dir / "picks" / f"{arm}.csv", index=False, float_format="%.4f")
    pd.DataFrame(coverage).to_csv(out_dir / "coverage.csv", index=False)
    pd.DataFrame(overlap).to_csv(out_dir / "workflow_overlap.csv", index=False, float_format="%.4f")
    with (out_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(dict(calendar_end=calendar[-1], first_signal=signals[0], last_signal=signals[-1],
                       first_execution=calendar[first_exec], workflow_start=calendar[w_start] if w_start else None,
                       scan_day=scan_day, price_anomalies=market.anomalies, results=results, pairs=pairs),
                  handle, ensure_ascii=False, indent=1)
    rows = []
    for arm, r in results.items():
        rows.append(dict(arm=arm, start=r["start"], end=r["end"], final=round(r["final"], 3), cagr=round(r["cagr"], 4),
                         max_drawdown=round(r["max_drawdown"], 4), drawdown_from=r["drawdown_from"], drawdown_to=r["drawdown_to"],
                         vol=round(r["vol"], 4), sharpe=round(r["sharpe"], 3),
                         turnover_per_year=round(r.get("turnover_per_year", float("nan")), 3),
                         cost_per_year=round(r.get("cost_per_year", float("nan")), 5),
                         avg_holdings=round(r.get("avg_holdings", float("nan")), 1),
                         common_cagr=round(r["common"]["cagr"], 4) if "common" in r else "",
                         common_max_drawdown=round(r["common"]["max_drawdown"], 4) if "common" in r else ""))
    pd.DataFrame(rows).to_csv(out_dir / "summary.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
