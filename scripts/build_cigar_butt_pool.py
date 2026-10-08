#!/usr/bin/env python3
"""按工作流程 §6.10 校验烟蒂池池表并重出阅读版 `docs/000_cigar_butt_pool.md`（不手改）；--check 只校验不写。"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from screen_cigar_butts import CANDIDATE_MAX, FOCUS_MAX, POOL, POOL_FIELDS, SCREEN, STATUSES  # noqa: E402

READING = ROOT / "docs/000_cigar_butt_pool.md"
REGISTRY = ROOT / "data/processed/independent_valuations.csv"
BUY_PV_MAX = 0.90       # §6.10 第 5 条：§6.9 独立 P/V
NEAR_TOP = 10
TYPE_NAME = {"A": "净流动资产型", "B": "净现金加盈利型", "C": "资产折价型", "D": "低市净率金融型"}


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str) -> float | None:
    try:
        return float(value) if value not in ("", None) else None
    except ValueError:
        return None


def validate(rows: list[dict], registry: dict[str, dict]) -> list[str]:
    errors, seen = [], set()
    for i, r in enumerate(rows, start=2):
        where = f"第 {i} 行 {r.get('security_code') or '?'}"
        if r["security_code"] in seen:
            errors.append(f"{where}：代码重复")
        seen.add(r["security_code"])
        if r["status"] not in STATUSES:
            errors.append(f"{where}：status {r['status']} 不在 {STATUSES}")
        if r["cb_type"] not in FOCUS_MAX:
            errors.append(f"{where}：cb_type {r['cb_type']} 不在 A／B／C／D")
        for field in ("price", "market_cap_yi", "v_cb_yi", "pv_cb", "pv_a", "pv_b", "pv_c", "pv_d", "dividend_yield",
                      "v_cb_reviewed_yi", "pv_cb_reviewed"):
            if r.get(field) and fnum(r[field]) is None:
                errors.append(f"{where}：{field} 不是数字")
        pv = fnum(r["pv_cb"])
        if r["status"] == "candidate" and (pv is None or pv > CANDIDATE_MAX):
            errors.append(f"{where}：候选须 P/V_cb ≤ {CANDIDATE_MAX}")
        if r["status"] in ("watch", "focus", "rejected") and not r["reviewed_at"]:
            errors.append(f"{where}：{r['status']} 须填 reviewed_at")
        if r["status"] == "rejected" and not r["gates_failed"]:
            errors.append(f"{where}：rejected 须写 gates_failed")
        if r["status"] in ("watch", "focus") and r["cb_type"] in ("C", "D") and not r["v_cb_reviewed_yi"]:
            errors.append(f"{where}：C、D 类复核后须填 v_cb_reviewed_yi")
        if r["status"] == "focus":
            review = registry.get(r["independent_review_id"])
            pv = fnum(r["pv_cb_reviewed"]) if r["v_cb_reviewed_yi"] else pv
            if pv is None or pv > FOCUS_MAX.get(r["cb_type"], 0):
                errors.append(f"{where}：重点级须 P/V_cb ≤ {FOCUS_MAX.get(r['cb_type'])}")
            if r["cash_verified"] != "yes":
                errors.append(f"{where}：重点级须通过股东回报验证")
            if not r["catalysts"]:
                errors.append(f"{where}：重点级须写兑现路径 catalysts")
            if not review or review["status"] != "current":
                errors.append(f"{where}：重点级须有 §6.9 现行独立估值（independent_review_id）")
        if r["buy_eligible"] not in ("", "yes", "no"):
            errors.append(f"{where}：buy_eligible 只能为 yes／no／空")
        if r["buy_eligible"] == "yes":
            review = registry.get(r["independent_review_id"])
            if r["status"] != "focus" or not review or (fnum(review["pv"]) or 9) > BUY_PV_MAX:
                errors.append(f"{where}：可买须为重点级且 §6.9 独立 P/V ≤ {BUY_PV_MAX}")
    return errors


def _pct(value: str) -> str:
    v = fnum(value)
    return f"{v * 100:.1f}%" if v is not None else "—"


def _cell(value: str) -> str:
    return value if value not in ("", None) else "—"


def _wan(value: str) -> str:
    v = fnum(value)
    return f"{v:,.0f}" if v is not None else "—"


def _pvs(r: dict) -> str:
    return "／".join(_cell(r.get(f"pv_{k}", "")) for k in "abcd")


def render(rows: list[dict], screen: list[dict], registry: dict[str, dict]) -> str:
    by_status = {s: [r for r in rows if r["status"] == s] for s in STATUSES}
    latest = max(rows, key=lambda r: r["price_date"], default={})
    out = [
        "# 烟蒂池",
        "",
        "> 由 `python3 scripts/build_cigar_butt_pool.py` 从 `data/processed/cigar_butt_pool.csv` 生成，不手改。口径、门槛、闸门与状态见"
        "[工作流程](000_Ashare_workflow.md) §6.10；逐家粗筛读数在 `data/interim/cigar_butt_screen.csv`。烟蒂池不做回测，"
        "不设系统买卖规则，买卖由用户决定，不进执行清单。",
        "",
        f"- 报告期 {latest.get('report_date', '—')}，价格日 {latest.get('price_date', '—')}。"
        f"重点级 {len(by_status['focus'])}、观察级 {len(by_status['watch'])}、候选 {len(by_status['candidate'])}、"
        f"已退回 {len(by_status['rejected'])}、已退出 {len(by_status['exited'])}。",
        "- `P/V_cb` = 总市值 ÷ 烟蒂价值；四列依次为 A／B／C／D 类读数，— 表示该类不适用或烟蒂价值不为正。重点级门槛："
        + "、".join(f"{k} {v}" for k, v in FOCUS_MAX.items()) + f"；候选门槛 {CANDIDATE_MAX}。",
        "- 股东回报：近三个财年现金分红合计不低于同期归母净利 20%、且至少两年有分红为「是」（§6.10 第 3 条第 4 项），回购暂未计入。",
        "- 粗筛旗标：退市风险、非标审计意见、价值流失、现金消耗、收购现金超权益 20%、流动性不足；复核结论写「闸门」。",
        "",
    ]
    head = "| 代码 | 名称 | 类 | P/V_cb | A／B／C／D | V_cb（亿） | 市值（亿） | 股息率 | 三年分红率 | 股东回报 | 每股价值三年年化 | 日均成交（万） | 旗标 |"
    rule = "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |"
    reviewed_head = ("| 代码 | 名称 | 类 | 复核 P/V_cb | 粗筛 P/V_cb | 复核 V_cb（亿） | 市值（亿） | 股息率 | 股东回报 | 日均成交（万） | 独立 P/V | 可买 |")
    reviewed_rule = "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |"

    def line(r: dict) -> str:
        return (f"| {r['security_code']} | {r['security_name']} | {r['cb_type']} | **{_cell(r['pv_cb'])}** | {_pvs(r)} | "
                f"{_cell(r['v_cb_yi'])} | {_cell(r['market_cap_yi'])} | {_pct(r['dividend_yield'])} | {_pct(r['payout_3y'])} | "
                f"{'是' if r['cash_verified'] == 'yes' else '否'} | {_pct(r['v_cb_cagr_3y'])} | {_wan(r['liquidity_60d_wan'])} | "
                f"{_cell(r['auto_flags'])} |")

    for title, status, extra in (("一、重点级", "focus", "兑现路径"), ("二、观察级", "watch", "复核结论")):
        out += [f"## {title}", ""]
        if not by_status[status]:
            out += ["无。", ""]
            continue
        out += [reviewed_head + f" {extra} | 下次核对 |", reviewed_rule + " --- | --- |"]
        group = sorted(by_status[status], key=lambda r: fnum(r["pv_cb_reviewed"] or r["pv_cb"]) or 9)
        for r in group:
            review = registry.get(r["independent_review_id"], {})
            detail = r["catalysts"] if status == "focus" else (r["gates_failed"] or r["note"])
            out.append(f"| {r['security_code']} | {r['security_name']} | {r['cb_type']} | **{_cell(r['pv_cb_reviewed'] or r['pv_cb'])}** | "
                       f"{_cell(r['pv_cb'])} | {_cell(r['v_cb_reviewed_yi'] or r['v_cb_yi'])} | {_cell(r['market_cap_yi'])} | "
                       f"{_pct(r['dividend_yield'])} | {'是' if r['cash_verified'] == 'yes' else '否'} | {_wan(r['liquidity_60d_wan'])} | "
                       f"{_cell(review.get('pv', ''))} | {'是' if r['buy_eligible'] == 'yes' else '—'} | {_cell(detail)} | {_cell(r['next_check'])} |")
        out.append("")
    out += ["## 三、候选（待复核）", ""]
    for kind in "ABCD":
        group = sorted((r for r in by_status["candidate"] if r["cb_type"] == kind), key=lambda r: fnum(r["pv_cb"]) or 9)
        out += [f"### {kind} {TYPE_NAME[kind]}（{len(group)} 家；重点级门槛 {FOCUS_MAX[kind]}）", ""]
        out += ([head, rule] + [line(r) for r in group] if group else ["无。"]) + [""]
    out += ["## 四、已退回与已退出", ""]
    gone = by_status["rejected"] + by_status["exited"]
    if gone:
        out += ["| 代码 | 名称 | 类 | 状态 | 日期 | 原因 |", "| --- | --- | --- | --- | --- | --- |"]
        out += [f"| {r['security_code']} | {r['security_name']} | {r['cb_type']} | {r['status']} | {r['status_since']} | "
                f"{_cell(r['gates_failed'] or r['note'])} |" for r in gone]
    else:
        out.append("无。")
    out += ["", f"## 五、各类最接近门槛的 {NEAR_TOP} 家（粗筛读数，未入池时只作参数对照）", "",
            "按各类 `P/V_cb` 升序，含已入池者；非金融公司三类各自排序，银行只有 D 类。", ""]
    for kind in "ABCD":
        key = f"pv_{kind.lower()}"
        near = sorted((r for r in screen if fnum(r.get(key, ""))), key=lambda r: fnum(r[key]))[:NEAR_TOP]
        out += [f"### {kind} {TYPE_NAME[kind]}", "",
                "| 代码 | 名称 | 该类 P/V_cb | A／B／C／D | 市值（亿） | NCAV（亿） | 净现金（亿） | 股东回报 | 旗标 | 名单 |",
                "| --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | --- |"]
        out += [f"| {r['security_code']} | {r['security_name']} | {r[key]} | {_pvs(r)} | {_cell(r['market_cap_yi'])} | "
                f"{_cell(r['ncav_yi'])} | {_cell(r['net_cash_yi'])} | {'是' if r['cash_verified'] == 'yes' else '否'} | "
                f"{_cell(r['auto_flags'])} | {_cell(r['attention_class'])} |" for r in near]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="只校验，不写阅读版")
    args = ap.parse_args()
    rows = read(POOL)
    if rows and list(rows[0]) != POOL_FIELDS:
        print(f"ERROR: 池表列与 POOL_FIELDS 不一致：{list(rows[0])}")
        return 1
    registry = {r["review_id"]: r for r in read(REGISTRY)}
    errors = validate(rows, registry)
    for error in errors:
        print("ERROR:", error)
    if errors:
        return 1
    text = render(rows, read(SCREEN) if SCREEN.exists() else [], registry)
    if args.check:
        stale = not READING.exists() or READING.read_text(encoding="utf-8") != text
        print(f"{len(rows)} 行通过校验" + ("；阅读版需重出" if stale else "；阅读版一致"))
        return int(stale)
    READING.write_text(text, encoding="utf-8")
    print(f"{len(rows)} 行通过校验，已写 {READING.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
