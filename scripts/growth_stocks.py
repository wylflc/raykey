"""工作流 §9.3.6 成长股模块：读业务属性登记表（个人投资体系第 5.12 节）与档案的重点复核记录。

成长股 = 登记表 `derived_class = 结构成长型` 的公司；由结构成长型改判为其他类别的记 `rejudged_from`，持仓按
§9.3.1 成长股卖出行逐日减一档。重点复核记录（档案 `growth_reviewed_at`／`growth_review_conclusion`）在生产带此后
吸收新定期报告或预告、或登记行变动时失效。交易阈值只在扫描器 `SEC93_GROWTH_*` 常量（§9.3.1）。
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUSINESS = ROOT / "data/processed/a_share_business_attributes.csv"
DEFAULT_DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
GROWTH_CLASS = "结构成长型"
REVIEW_PASS, REVIEW_FAIL = "通过", "不通过"
REVIEW_FIELDS = ("growth_reviewed_at", "growth_review_conclusion", "growth_review_note", "growth_reviewed_pv")


@dataclass
class GrowthState:
    growth: set[str] = field(default_factory=set)           # 现登记为结构成长型
    exiting: set[str] = field(default_factory=set)          # 由结构成长型改判为其他类别
    low_confidence: set[str] = field(default_factory=set)   # 可复制性把握为低的难复制判定
    reviews: dict[str, tuple[str, str]] = field(default_factory=dict)   # 代码 → (pass／fail／stale／missing, 说明)

    def passed(self, code: str) -> bool:
        return self.reviews.get(code, ("missing", ""))[0] == "pass"

    def gated(self, code: str) -> bool:
        """§10.1 第 4 条：成长股无有效「通过」记录；改判后的清仓期由调用方按持仓另判。"""
        return code in self.growth and not self.passed(code)


def _read(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not Path(path).exists():
        return {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return {(r.get("security_code") or "").strip().zfill(6): r for r in csv.DictReader(handle)}


def review_status(dossier: dict | None, band: dict | None, register_row: dict | None) -> tuple[str, str]:
    """重点复核记录的状态：`pass`／`fail` 有效，`stale` 已失效，`missing` 无记录。"""
    dossier, band, register_row = dossier or {}, band or {}, register_row or {}
    reviewed = (dossier.get("growth_reviewed_at") or "").strip()[:10]
    conclusion = (dossier.get("growth_review_conclusion") or "").strip()
    if not reviewed or conclusion not in (REVIEW_PASS, REVIEW_FAIL):
        return "missing", "无重点复核记录"
    later = [f"{key} {value}" for key, value in (("available_at", (band.get("available_at") or "")[:10]),
                                                  ("forecast_notice_date", (band.get("forecast_notice_date") or "")[:10]),
                                                  ("registered_at", (register_row.get("registered_at") or "")[:10]))
             if value and value > reviewed]
    if later:
        return "stale", f"复核 {reviewed} 之后 {'、'.join(later)}，记录失效"
    return ("pass" if conclusion == REVIEW_PASS else "fail"), f"复核 {reviewed} {conclusion}"


def load_growth_state(business: Path | None = DEFAULT_BUSINESS, dossiers: Path | None = DEFAULT_DOSSIERS,
                      bands: dict[str, dict] | None = None) -> GrowthState:
    """`bands` 为扫描器 `load_model_bands` 读出的候选侧生产带（代码 → 当日可用带行）。"""
    register, docs, bands = _read(business), _read(dossiers), bands or {}
    state = GrowthState()
    for code, row in register.items():
        cls = (row.get("derived_class") or "").strip()
        if cls == GROWTH_CLASS:
            state.growth.add(code)
            if ((row.get("replicability") or "").strip() == "难复制"
                    and (row.get("replicability_confidence") or "").strip() == "低"):
                state.low_confidence.add(code)
            state.reviews[code] = review_status(docs.get(code), bands.get(code), row)
        elif (row.get("rejudged_from") or "").strip() == GROWTH_CLASS:
            state.exiting.add(code)
    return state
