"""OI-250 登记扩到池内全部 ROIC 路径（用户 2026-10-01 裁定）：为尚未登记的池成员汇总仓库研究记录与毛利率、营收走势，
供按口径 v2（`../exp_oi250_pilot_20261001/rubric.md`）判定业务属性。

    python3 build_inputs.py      # → inputs.csv
"""
import csv
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
PERIODS = [f"{y}-12-31" for y in range(2019, 2026)] + ["2026-06-30", "2025-06-30"]


def read(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as fh:
        return {r["security_code"].zfill(6): r for r in csv.DictReader(fh)}


def panel():
    out = {}
    for p in PERIODS:
        path = ROOT / "data/raw/financials" / f"{p}.csv"
        if path.exists():
            for r in csv.DictReader(path.open(encoding="utf-8-sig")):
                out.setdefault(r["security_code"].zfill(6), {})[p] = r
    return out


def fmt(v, scale=1.0, digits=1):
    try:
        return f"{float(v) / scale:.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def main():
    bands = read("data/processed/a_share_pool_model_bands_adopted.csv")
    registered = read("data/processed/a_share_business_attributes.csv")
    tiers = read("data/processed/a_share_watchlist_quality_tiers.csv")
    triage = read("data/processed/a_share_attention_triage.csv")
    dossiers = read("data/processed/a_share_valuation_dossiers.csv")
    industry = read("data/reference/a_share_csrc_industry.csv")
    fin = panel()
    rows = []
    for code, b in sorted(bands.items()):
        if b.get("roic_path") not in ("growth", "zero_growth") or code in registered:
            continue
        t, a, d, i, f = tiers.get(code, {}), triage.get(code, {}), dossiers.get(code, {}), industry.get(code, {}), fin.get(code, {})
        years = [p for p in PERIODS[:7] if p in f]
        gm = "；".join(f"{p[:4]} {fmt(f[p].get('gross_margin'))}%" for p in years)
        if "2026-06-30" in f:
            gm += f"；2026H1 {fmt(f['2026-06-30'].get('gross_margin'))}%"
        rev = "；".join(f"{p[:4]} {fmt(f[p].get('total_operate_income'), 1e8)}亿" for p in years)
        if "2026-06-30" in f:
            rev += (f"；2026H1 {fmt(f['2026-06-30'].get('total_operate_income'), 1e8)}亿（同比 {fmt(f['2026-06-30'].get('revenue_yoy'))}%），"
                    f"归母 {fmt(f['2026-06-30'].get('parent_netprofit'), 1e8, 2)}亿（同比 {fmt(f['2026-06-30'].get('netprofit_yoy'))}%）")
        rows.append(dict(
            security_code=code, security_name=b.get("security_name", ""), em2016=i.get("em2016", ""), csrc=i.get("csrc_industry", ""),
            quality_tier=t.get("quality_tier", ""), strategy_tag=t.get("primary_strategy_tag", ""), roic_path=b.get("roic_path", ""),
            peak_weight=b.get("peak_weight", ""), moat_summary=t.get("moat_summary", ""), capital_replicability=t.get("capital_replicability", ""),
            moat_type=t.get("q2_moat_type", ""), erosion_paths=t.get("q2_erosion_paths", ""), q1_reason=t.get("q1_reason", ""),
            peer_comparison=t.get("peer_comparison", ""), attention_reason=a.get("attention_reason", ""),
            implied_growth=d.get("implied_growth_years", ""), review_triggers=d.get("review_triggers", ""), key_metrics=d.get("key_metrics", ""),
            gross_margin_trend=gm, revenue_trend=rev, tier_reviewed_at=(t.get("reviewed_at_utc") or "")[:10],
            evidence_available_at=t.get("evidence_available_at", "")))
    fields = list(rows[0].keys())
    with (EXP / "inputs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows →", EXP / "inputs.csv")


if __name__ == "__main__":
    main()
