#!/usr/bin/env python3
"""按工作流程 §6.9 校验独立估值登记表并重出阅读版。

登记表 `data/processed/independent_valuations.csv` 每家公司每次评审一行；阅读版 `docs/independent_valuations.zh.md`
由本脚本生成，不手改。--check 只校验不写。
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/processed/independent_valuations.csv"
READING = ROOT / "docs/independent_valuations.zh.md"
FIELDS = [
    "review_id", "batch_id", "review_date", "reviewer_type", "reviewer", "market", "security_code", "security_name",
    "status", "superseded_by", "price_date", "evidence_cutoff", "currency", "unit", "price", "v_base", "v_bear", "v_bull",
    "pv", "scenarios", "verdict", "confidence", "coe", "method", "implied_irr", "model_v", "model_pv",
    "conclusion", "basis", "risks", "falsifiers", "next_check", "report", "evidence",
]
REQUIRED = ("review_id", "batch_id", "review_date", "reviewer_type", "reviewer", "market", "security_code",
            "security_name", "status", "report")
STATUSES = {"own": {"current", "superseded", "historical"}, "external": {"reference"}}
PV_TOLERANCE = 0.015  # 登记值为舍入后的价格与 V，P/V 复算允许的绝对误差
MARKET_ORDER = {"A": 0, "HK": 1, "US": 2}


def _num(value: str) -> float | None:
    try:
        return float(value) if value not in ("", None) else None
    except ValueError:
        return None


def _iso(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def load(path: Path = REGISTRY) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise SystemExit(f"{path.name} 列与脚本 FIELDS 不一致：{reader.fieldnames}")
        return list(reader)


def validate(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    by_id = {}
    for i, row in enumerate(rows, start=2):
        where = f"第 {i} 行 {row.get('review_id') or '?'}"
        for field in REQUIRED:
            if not row.get(field):
                errors.append(f"{where}：缺 {field}")
        if row["review_id"] in by_id:
            errors.append(f"{where}：review_id 重复")
        by_id[row["review_id"]] = row
        kind, status = row.get("reviewer_type"), row.get("status")
        if status not in STATUSES.get(kind, set()):
            errors.append(f"{where}：reviewer_type {kind} 与 status {status} 不匹配")
        for field in ("review_date", "price_date"):
            if row.get(field) and not _iso(row[field]):
                errors.append(f"{where}：{field} 不是 YYYY-MM-DD")
        for field in ("price", "v_base", "v_bear", "v_bull", "pv", "implied_irr", "model_v", "model_pv"):
            if row.get(field) and _num(row[field]) is None:
                errors.append(f"{where}：{field} 不是数字")
        price, value, pv = _num(row.get("price", "")), _num(row.get("v_base", "")), _num(row.get("pv", ""))
        if kind == "own":
            if not (price and value and pv):
                errors.append(f"{where}：自有评审须有 price、v_base、pv")
            elif abs(price / value - pv) > PV_TOLERANCE:
                errors.append(f"{where}：pv {pv} 与 price ÷ v_base = {price / value:.3f} 不符")
        elif pv is None:
            errors.append(f"{where}：外部意见须有 pv")
        for field in ("report", "evidence"):
            if row.get(field) and not (ROOT / row[field]).exists():
                errors.append(f"{where}：{field} 路径不存在 {row[field]}")
    current = Counter((r["market"], r["security_code"]) for r in rows if r["status"] == "current")
    errors += [f"{m}:{c} 有 {n} 行 current" for (m, c), n in current.items() if n > 1]
    for row in rows:
        target = row.get("superseded_by", "")
        if row["status"] == "superseded":
            later = by_id.get(target)
            if not later:
                errors.append(f"{row['review_id']}：superseded_by 缺失或不存在")
            elif (later["market"], later["security_code"]) != (row["market"], row["security_code"]) \
                    or later["review_date"] < row["review_date"]:
                errors.append(f"{row['review_id']}：superseded_by 须指向同一公司、不早于本行的评审")
        elif target:
            errors.append(f"{row['review_id']}：只有 superseded 行可填 superseded_by")
    return errors


def _link(path: str, label: str) -> str:
    if not path:
        return "—"
    return f"[{label}]({'' if path.startswith('docs/') else '../'}{path.removeprefix('docs/')})"


def _range(row: dict[str, str]) -> str:
    base, bear, bull = row.get("v_base"), row.get("v_bear"), row.get("v_bull")
    return f"{base}（{bear}～{bull}）" if bear and bull else (base or "—")


def _key(row: dict[str, str]) -> tuple:
    return (MARKET_ORDER.get(row["market"], 9), row["security_code"], row["review_date"])


def render(rows: list[dict[str, str]]) -> str:
    current = sorted((r for r in rows if r["status"] == "current"), key=_key)
    older = sorted((r for r in rows if r["status"] in ("superseded", "historical")), key=_key)
    external = sorted((r for r in rows if r["status"] == "reference"), key=_key)
    out = [
        "# 独立估值登记",
        "",
        "> 由 `python3 scripts/build_independent_valuations.py` 从 `data/processed/independent_valuations.csv` 生成，不手改。"
        "复用条件、分档与登记步骤见[工作流程](000_Ashare_workflow.md) §6.9。独立估值只作研究对照，不改模型带、不进执行清单。",
        "",
        "- **独立 V**：概率加权值（较早批次为基准情景）；括号内为熊～牛（或悲观～乐观）情景。",
        "- **独立 P/V**：评审价格日的现价 ÷ 独立 V，是绝对估值口径；复用时按当日价格重算。模型 P/V 是池内相对位置，两者只比方向。",
        "- **判断**：沿用各批原话；2026-10-05 及更早批次的「小幅低估」「高估」大致对应 §6.9 分档的「温和低估」「偏贵」。",
        f"- 登记 {len(rows)} 行：现行 {len(current)}、已取代或历史时点 {len(older)}、外部意见 {len(external)}。",
        "",
        "## 一、现行结论",
        "",
        "| 市场 | 代码 | 名称 | 评审日 | 价格日 | 现价 | 独立 V（熊～牛） | 独立 P/V | 判断 | 置信度 | 证据截止 | 下次核对 | 全文 |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for r in current:
        out.append(f"| {r['market']} | {r['security_code']} | {r['security_name']} | {r['review_date']} | {r['price_date']} | "
                   f"{r['price']} {r['unit']} | {_range(r)} | **{r['pv']}** | {r['verdict']} | {r['confidence'] or '—'} | "
                   f"{r['evidence_cutoff'] or '—'} | {r['next_check'] or '—'} | {_link(r['evidence'] or r['report'], '全文')} |")
    out += ["", "## 二、逐家要点", ""]
    for r in current:
        model = f"{r['model_v']}（P/V {r['model_pv']}）" if r.get("model_v") else "—"
        irr = f"{float(r['implied_irr']):.1%}" if r.get("implied_irr") else "—"
        out += [f"### {r['security_name']}（{r['security_code']}）", "",
                f"- **结论**：{r['conclusion']}",
                f"- **依据**：{r['basis'] or '—'}",
                f"- **情景**：{r['scenarios'] or '—'}",
                f"- **方法与股权成本**：{r['method'] or '—'}｜{r['coe'] or '—'}｜基准隐含 IRR {irr}",
                f"- **主要风险**：{r['risks'] or '—'}",
                f"- **证伪条件**：{r['falsifiers'] or '—'}",
                f"- **评审时模型 V**：{model}｜评审 `{r['review_id']}`｜{_link(r['report'], '汇总报告')}｜{_link(r['evidence'], '全文')}",
                ""]
    out += ["## 三、已被取代与历史时点的评审", "",
            "| 市场 | 代码 | 名称 | 评审日 | 价格日 | 现价 | 独立 V（熊～牛） | 独立 P/V | 判断 | 状态 | 取代者 | 全文 |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |"]
    for r in older:
        out.append(f"| {r['market']} | {r['security_code']} | {r['security_name']} | {r['review_date']} | {r['price_date']} | "
                   f"{r['price']} {r['unit']} | {_range(r)} | {r['pv']} | {r['verdict']} | {r['status']} | "
                   f"{r['superseded_by'] or '—'} | {_link(r['evidence'] or r['report'], '全文')} |")
    out += ["", "## 四、外部意见（只作对照）", "",
            "| 市场 | 代码 | 名称 | 日期 | 来源 | P/V（区间） | 说明 | 报告 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in external:
        out.append(f"| {r['market']} | {r['security_code']} | {r['security_name']} | {r['review_date']} | {r['reviewer']} | "
                   f"{r['pv']}（{r['scenarios'] or '—'}） | {r['conclusion']} | {_link(r['report'], '报告')} |")
    batches: dict[str, dict] = {}
    for r in rows:
        b = batches.setdefault(r["batch_id"], dict(date=r["review_date"], reviewers=[], n=0, report=r["report"]))
        b["n"] += 1
        if r["reviewer"] not in b["reviewers"]:
            b["reviewers"].append(r["reviewer"])
    out += ["", "## 五、评审批次", "", "| 批次 | 评审日 | 执行 | 行数 | 报告 |", "| --- | --- | --- | ---: | --- |"]
    for batch_id, b in sorted(batches.items(), key=lambda kv: (kv[1]["date"], kv[0])):
        out.append(f"| `{batch_id}` | {b['date']} | {'、'.join(b['reviewers'])} | {b['n']} | {_link(b['report'], '报告')} |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="只校验，不写阅读版")
    args = ap.parse_args()
    rows = load()
    errors = validate(rows)
    for error in errors:
        print("ERROR:", error)
    if errors:
        return 1
    text = render(rows)
    if args.check:
        stale = not READING.exists() or READING.read_text(encoding="utf-8") != text
        print(f"{len(rows)} 行通过校验" + ("；阅读版需重出" if stale else "；阅读版一致"))
        return int(stale)
    READING.write_text(text, encoding="utf-8")
    print(f"{len(rows)} 行通过校验，已写 {READING.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
