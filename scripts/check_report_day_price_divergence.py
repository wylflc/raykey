#!/usr/bin/env python3
"""A 股财报日「价格与带背离 → 强制复带」检出（§7.5.2，结 OI-026）。

登记的不对称
------------
v2.10 给 §6.8 加了第 ③ 条：海外标的财报后首个价格相对披露前收盘 |Δ| ≥ 7% 且被推出带时，
T+1 内必须复带，不得只让价格改档。**该触发的成因与市场无关**——财报日是唯一一个「带与
价格从同一个事件更新」的日子：价格瞬时、完整地吸收它，而带走的是归一化、拆增速、定倍数
这条慢路径。两者一旦差出这个量级，现有机制只有「市场错了，等它回来」一个读法，**没有
任何机制把这个缺口当成对带的反证**。

而 A 股侧的 §7.3/§7.5.1 express 复核只由**披露事件**触发、同样不看价格反应，故同一盲区
在 261 家上原样存在——且 A 股的暴露面比海外大得多：海外 21 家一律不可买，A 股的带
直接决定 §9.3 的买入资格。

用户 2026-08-07 裁定：**只对「持仓 + 当日可买」子集生效**（三个方向中的第②个）。

口径
----
* **子集**：全部持仓 ∪ 当日合格集（§9.3.2 第 1～2 步，与扫描器同一判定 `eligible_rows`；用户 2026-10-13 裁定，
  OI-279）。理由是决策后果——持仓的卖出侧无冻结保护，可买股票的 `P/V` 直接决定当天能不能下单；其余 200 余家
  逐日判定既不可执行，也没有对应的当日决策。
* **阈值 |Δ| ≥ 7%**：沿用 §6.8 第 ③ 条的海外初始校准值，**明标为未校准值**。A 股有
  10%/20% 涨跌停制度，7% 在此可能偏敏感；本脚本每次运行打印实际触发家数，跑一个
  披露季后按实测频次重定（改阈值先改 §7.5.1 正文）。
* **第二个条件不可省**：该价格必须把标的**推出当前带**（涨破带顶或跌穿带底）。只有
  |Δ| 大而仍在带内的，说明带本来就容得下这次重定价，不构成对带的反证。
* **结论是「带待复核」，不是改带**：命中即在当日报告标注并按 §7.4 express 口径在 T+1
  内完成一次带复核。复核结论可以是「带不变」，但必须显式做过。
* **复带登记**（OI-283，用户 2026-10-13 裁定）：结论按（代码, 公告日）登记
  `data/reference/report_divergence_reviews.csv` 并写决策日志；复核日不早于反应日的登记行使该披露
  不再拦截发布，报告照列。
* **披露后首个交易日**（OI-284，用户 2026-10-13 裁定）：公告日当天或之后的第一根 K 线。预告表与披露表记官方
  公告日，盘后发布的公告已记为下一日。

用法::

    python3 scripts/check_report_day_price_divergence.py --as-of 2026-08-07
    python3 scripts/check_report_day_price_divergence.py --as-of 2026-08-07 --lookback 15
    python3 scripts/check_report_day_price_divergence.py --as-of 2026-08-07 --register 600519 \
        --notice-date 2026-08-07 --conclusion 带不变 --note "复带依据"
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import screen_daily_volume_price_signals as S  # noqa: E402

DEFAULT_POOL = ROOT / "data/processed/a_share_core_valuation_pool.csv"
DEFAULT_HOLDINGS = ROOT / "data/processed/a_share_holdings.csv"
DEFAULT_DISCLOSURES = ROOT / "data/interim/a_share_report_disclosures.csv"
DEFAULT_FORECASTS = ROOT / "data/interim/a_share_earnings_forecasts.csv"
DEFAULT_REVIEWS = ROOT / "data/reference/report_divergence_reviews.csv"
REVIEW_FIELDS = ["security_code", "security_name", "notice_date", "reviewed_at", "conclusion", "note"]
REVIEW_CONCLUSIONS = ("带不变", "已复带")

# §6.8 第 ③ 条的初始校准值。**A 股侧未校准**——见模块 docstring。
DIVERGENCE_THRESHOLD_PCT = 7.0


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def latest_notice_dates(as_of: date, lookback_days: int) -> dict[str, tuple[str, str]]:
    """{代码: (公告日, 披露类型)}，只取回溯窗口内最近的一次披露。

    三档披露一律计入（预告/快报/定期报告），与 §7.3 同口径——「是否大幅超预期」是复核的
    结论，不是入队的门槛。
    """
    floor = (as_of - timedelta(days=lookback_days)).isoformat()
    latest: dict[str, tuple[str, str]] = {}
    for path, label in ((DEFAULT_DISCLOSURES, "定期报告/快报"), (DEFAULT_FORECASTS, "业绩预告")):
        for row in load_csv(path):
            code = (row.get("security_code") or "").zfill(6)
            notice = (row.get("notice_date") or "")[:10]
            if not code or not notice or notice < floor or notice > as_of.isoformat():
                continue
            kind = row.get("disclosure_type") or label
            if code not in latest or notice > latest[code][0]:
                latest[code] = (notice, str(kind))
    return latest


def divergence_for(code: str, exchange: str, notice: str, as_of: date,
                   low: float, high: float, timeout: float, strict: bool = False) -> dict[str, object] | None:
    """返回该票披露前收盘 → 披露后首个收盘的背离读数；不满足条件返回 None。"""
    try:
        _, rows = S.fetch_daily_rows(code, exchange, as_of.isoformat(), timeout)
    except Exception:                                          # noqa: BLE001
        if strict:
            raise
        return None
    if len(rows) < 2:
        if strict:
            raise ValueError(f"背离检查行情不足：{code}")
        return None

    # 披露后首个交易日 = 公告日当天或之后的第一根。`notice` 是官方公告日：盘后发布的公告记为下一日，
    # 盘前、盘中发布的记当天，两种情形当天那根都已吸收披露（2026 年中报回看见回测日志 §12.335）。
    after_idx = next((i for i, r in enumerate(rows) if str(r.get("date", "")) >= notice), None)
    if after_idx is None or after_idx == 0:
        return None
    before_close = to_float(rows[after_idx - 1].get("close"))
    after_close = to_float(rows[after_idx].get("close"))
    if not before_close or not after_close:
        return None

    delta_pct = (after_close / before_close - 1) * 100
    if abs(delta_pct) < DIVERGENCE_THRESHOLD_PCT:
        return None
    if low <= after_close <= high:
        return None                                            # 仍在带内 = 带容得下这次重定价

    # 「**推出**带」是一个位移，不是一个位置——必须是这次财报把价格推得**离带更远**。
    # 首轮全池校准（2026-08-07，45 日窗）实测：只判"收在带外"会把 14 只里的 12 只判成命中，
    # 而其中绝大多数是**早已远在带上方**的 `trim_alert` 行，财报当天反而是**向带收敛**——
    # 判例江丰电子 282.14 → 240（−14.9%），带 42.29-52.25，跌了 15% 仍在带顶之上 4.6 倍。
    # 那不是对带的反证，恰恰是对带的佐证。故判据取「到带的距离扩大」：
    #   d(p) = max(0, low − p, p − high)，要求 d(after) > d(before)。
    # 该定义同时覆盖两种真信号：①原在带内被推出（d 由 0 变正，即 §6.8 微软/Meta 判例）；
    # ②原已在带外、财报把缺口进一步拉大。
    def gap(price: float) -> float:
        return max(0.0, low - price, price - high)

    if gap(after_close) <= gap(before_close):
        return None

    return {
        "notice_date": notice,
        "before_close": before_close,
        "after_date": str(rows[after_idx].get("date", "")),
        "after_close": after_close,
        "delta_pct": delta_pct,
        "band": (low, high),
        "pushed": ("涨破带顶" if gap(before_close) == 0 else "上方缺口扩大") if after_close > high
                  else ("跌穿带底" if gap(before_close) == 0 else "下方缺口扩大"),
    }


def load_reviews(path: Path = DEFAULT_REVIEWS) -> dict[tuple[str, str], dict[str, str]]:
    """§7.5.2 复带登记 {(代码, 公告日): 登记行}；键或结论无效、重复即报错。"""
    reviews: dict[tuple[str, str], dict[str, str]] = {}
    for row in load_csv(path):
        key = (row.get("security_code") or "").zfill(6), (row.get("notice_date") or "")[:10]
        if (len(key[1]) != 10 or len((row.get("reviewed_at") or "")) != 10 or key in reviews
                or row.get("conclusion") not in REVIEW_CONCLUSIONS):
            raise ValueError(f"背离复带登记无效或重复：{key}")
        reviews[key] = row
    return reviews


def register_review(code: str, notice: str, reviewed_at: str, conclusion: str, note: str, *,
                    reviews_path: Path = DEFAULT_REVIEWS, pool_path: Path = DEFAULT_POOL, log_path: Path | None = None) -> dict:
    """登记一次复带结论并写决策日志；同一（代码, 公告日）只登记一次。"""
    from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log
    code = code.zfill(6)
    name = next((r.get("security_name", "") for r in load_csv(pool_path) if r["security_code"].zfill(6) == code), None)
    date.fromisoformat(notice), date.fromisoformat(reviewed_at)
    if name is None or conclusion not in REVIEW_CONCLUSIONS or not note.strip() or reviewed_at < notice:
        raise ValueError("复带登记须给池内代码、有效结论与说明，复核日不早于公告日")
    if (code, notice) in load_reviews(reviews_path):
        raise ValueError(f"该披露已登记复带：{code} {notice}")
    row = dict(zip(REVIEW_FIELDS, (code, name, notice, reviewed_at, conclusion, note.strip())))
    new_file = not reviews_path.exists() or reviews_path.stat().st_size == 0
    with reviews_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    append_decision_log(log_path or DEFAULT_DECISION_LOG, [{
        "logged_at_utc": datetime.now(timezone.utc).isoformat(), "workflow_stage": "valuation_review",
        "run_id": f"report_divergence_review_{reviewed_at}", "as_of": reviewed_at, "security_code": code,
        "security_name": name, "decision_type": "report_divergence_review", "decision_result": conclusion,
        "summary_reason": f"§7.5.2 财报日价格背离复带：公告日 {notice}｜{note.strip()}",
        "input_files": str(pool_path), "source_urls": "", "output_file": str(reviews_path),
        "operator_or_script": "check_report_day_price_divergence.py", "workflow_version": WORKFLOW_VERSION,
        "decision_id": f"report_divergence_review:{code}:{notice}", "supersedes_decision_id": ""}])
    return row


def run(as_of: date, lookback: int, timeout: float, universe: str = "subset", *, candidate_rows=None,
        pool_path=DEFAULT_POOL, holdings_path=DEFAULT_HOLDINGS, members=None, tactical=None,
        blocked=None, growth=None, reviews_path=DEFAULT_REVIEWS, strict=False) -> list[dict[str, object]]:
    pool = {row["security_code"].zfill(6): row for row in load_csv(pool_path)}
    holdings = {row["security_code"].zfill(6) for row in load_csv(holdings_path)
                if (to_float(row.get("current_shares")) or 0) > 0}
    # 「当日可买」= 扫描器的当日合格集（`S.eligible_rows`）：扫描内调用传本次行情行与同一组排除集，
    # 单独运行时读最近一次扫描落盘的候选表（§8.2 产物）、队列冻结列、分层表与成长股登记。
    cand_rows = (load_csv(ROOT / "data/processed/daily_buy_candidates.csv")
                 if candidate_rows is None else candidate_rows)
    members = S.load_worth_attention_codes() if members is None else members
    tactical = S.load_tactical_gate_codes() if tactical is None else tactical
    if members is None:
        raise ValueError('背离复核缺三类表')
    scan_day = max((r.get("trade_date", "") for r in cand_rows), default="")
    day_rows = [r for r in cand_rows if r.get("trade_date") == as_of.isoformat()]
    if blocked is None:
        blocked = {str(r.get("security_code", "")).zfill(6) for r in day_rows
                   if str(r.get("review_frozen", "")).lower() == "true"}
    if growth is None:
        with contextlib.redirect_stdout(io.StringIO()):
            bands = S.load_model_bands(S.DEFAULT_MODEL_BANDS, S.evidence_iso_for_signal(as_of.isoformat()))
        growth = S.load_growth_state(bands=bands)
    buyable = {str(r["security_code"]).zfill(6)
               for r in S.eligible_rows(day_rows, holdings, blocked, tactical, growth, members)}
    if scan_day:
        print(f"  当日合格集取自最近一次扫描（trade_date={scan_day}，{len(buyable)} 只）")
    # `--universe pool` 只用于**阈值校准**（测全池触发频次），不是生效范围。
    # 生效范围由用户 2026-08-07 裁定为「持仓 + 当日可买」，见模块 docstring。
    subset = sorted(pool) if universe == "pool" else sorted(holdings | buyable)

    notices = latest_notice_dates(as_of, lookback)
    checked = 0
    hits: list[dict[str, object]] = []
    for code in subset:
        row = pool.get(code)
        if row is None:
            continue                                           # 持仓但已出池：无带可比
        notice = notices.get(code)
        low, high = to_float(row.get("fair_price_low")), to_float(row.get("fair_price_high"))
        if not notice or low is None or high is None:
            continue
        checked += 1
        result = divergence_for(code, row.get("exchange", ""), notice[0], as_of, low, high, timeout, strict=strict)
        if result:
            result.update({
                "security_code": code,
                "security_name": row.get("security_name", ""),
                "disclosure_kind": notice[1],
                "in_holdings": code in holdings,
                "buyable": code in buyable,
            })
            hits.append(result)

    # 已登记复带的披露（复核日不早于反应日）不再拦截，报告照列。
    reviews = load_reviews(reviews_path) if hits else {}
    for hit in hits:
        review = reviews.get((str(hit["security_code"]), str(hit["notice_date"])))
        hit["review"] = review if review and review["reviewed_at"] >= str(hit["after_date"]) else None
    pending = [hit for hit in hits if not hit["review"]]

    scope = (f"全池 {len(subset)} 只（**校准口径，非生效范围**）" if universe == "pool"
             else f"子集 {len(subset)} 只（持仓 {len(holdings)} + 当日合格集 {len(buyable)}，去重后）")
    print(f"§7.5.2 财报日价格背离检出（{as_of}，OI-026）｜{scope}"
          f"｜其中 {lookback} 日内有披露且有带的 {checked} 只")
    if not hits:
        print(f"  无命中（阈值 |Δ| ≥ {DIVERGENCE_THRESHOLD_PCT:g}% 且被推出带）")
        return pending

    def line(hit: dict[str, object]) -> str:
        low, high = hit["band"]                                # type: ignore[misc]
        tag = "持仓" if hit["in_holdings"] else ("可买" if hit.get("buyable") else "池内")
        return (f"    - {hit['security_name']}（{hit['security_code']}，{tag}）"
                f"{hit['disclosure_kind']} 公告日 {hit['notice_date']}："
                f"{hit['before_close']:g} → {hit['after_close']:g}（{hit['after_date']}）"
                f"**{float(hit['delta_pct']):+.2f}%**，{hit['pushed']}（带 {low:g}-{high:g}）")

    by_move = sorted(hits, key=lambda h: -abs(float(h["delta_pct"])))
    if pending:
        print(f"  **带待复核 {len(pending)} 只**（T+1 内按 §7.4 express 口径复带并登记，不得只让价格改档）：")
        for hit in by_move:
            if not hit["review"]:
                print(line(hit))
    if len(pending) < len(hits):
        print(f"  已登记复带 {len(hits) - len(pending)} 只（不拦截）：")
        for hit in by_move:
            if hit["review"]:
                review = hit["review"]                         # type: ignore[assignment]
                print(line(hit) + f"｜{review['conclusion']}（复核 {review['reviewed_at']}）：{review['note']}")
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description="A 股财报日价格背离强制复带检出（§7.5.2，OI-026）")
    parser.add_argument("--as-of", required=True, help="交易日 YYYY-MM-DD")
    parser.add_argument("--lookback", type=int, default=10, help="披露回溯窗口（自然日，缺省 10）")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--universe", choices=("subset", "pool"), default="subset",
                        help="subset=生效范围（持仓+当日合格集）；pool=全池，仅供阈值校准")
    parser.add_argument("--register", metavar="代码", help="登记该代码的复带结论（复核日取 --as-of），不做检出")
    parser.add_argument("--notice-date", help="--register：被复核披露的公告日 YYYY-MM-DD")
    parser.add_argument("--conclusion", choices=REVIEW_CONCLUSIONS, help="--register：复带结论")
    parser.add_argument("--note", default="", help="--register：复带依据")
    args = parser.parse_args()
    if args.register:
        if not args.notice_date or not args.conclusion:
            parser.error("--register 须同时给 --notice-date 与 --conclusion")
        row = register_review(args.register, args.notice_date, args.as_of, args.conclusion, args.note)
        print(f"已登记复带：{row['security_name']}（{row['security_code']}）公告日 {row['notice_date']}，{row['conclusion']}")
        return 0
    hits = run(date.fromisoformat(args.as_of), args.lookback, args.timeout, args.universe, strict=True)
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
