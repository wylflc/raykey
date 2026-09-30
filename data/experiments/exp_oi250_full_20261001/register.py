"""OI-250 登记扩到池内全部 ROIC 路径（v4.228）：合并四份判定，核对口径，与已登记 57 只合并写生产登记表。

- 已登记 57 只补 `replicability_confidence`：差异化定价行取口径 v2 重判（`../exp_oi250_pilot_20261001/replicability_v2.csv`）
  的把握，商品价格接受者行取原整体把握；补空的 `rejudged_from`／`rejudged_at`。
- 新判 116 只（`attributes_part1～4.csv`）按 rubric v2 派生规则核对标签与类别，依据日不晚于 2026-09-30。

    python3 register.py      # → attributes.csv、register.json、生产登记表 data/processed/a_share_business_attributes.csv
"""
import csv
import json
from collections import Counter
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
PILOT = ROOT / "data/experiments/exp_oi250_pilot_20261001"
REGISTRY = ROOT / "data/processed/a_share_business_attributes.csv"
REGISTERED_AT = "2026-10-01"
ALLOWED = dict(pricing_mode={"商品价格接受者", "差异化定价"}, demand_runway={"存量", "结构扩张"}, replicability={"易复制", "难复制"},
               replicability_confidence={"高", "中", "低"}, cost_position={"领先", "一般", "不适用"}, confidence={"高", "中", "低"})
GUARD = {"价格周期型": "保留峰守卫；周期中枢可按概率加权的长期价格经 §6.5.2.2 研究数调整",
         "成本领先周期型": "保留峰守卫；周期中枢可按概率加权的长期价格经 §6.5.2.2 研究数调整",
         "结构成长型": "可个案放宽：经 §6.5.2.2 研究数复核",
         "可复制成长型": "保留：扩产与竞争会侵蚀回报",
         "稳定型": "保留：守卫作用多为消化一次性高位"}
FIELDS = ["security_code", "security_name", "pricing_mode", "demand_runway", "replicability", "replicability_confidence", "cost_position",
          "derived_class", "guard_view", "evidence", "evidence_date", "falsifier", "confidence", "note", "rubric_version", "registered_at",
          "rejudged_from", "rejudged_at"]


def derived(r):
    if r["pricing_mode"] == "商品价格接受者":
        return "成本领先周期型" if r["cost_position"] == "领先" else "价格周期型"
    if r["demand_runway"] == "结构扩张":
        return "结构成长型" if r["replicability"] == "难复制" else "可复制成长型"
    return "稳定型"


def read(path, encoding="utf-8-sig"):
    with path.open(encoding=encoding, newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    issues = []
    existing = {r["security_code"].zfill(6): r for r in read(REGISTRY)}
    rep = {r["security_code"].strip().zfill(6): r for r in read(PILOT / "replicability_v2.csv")}
    for code, r in existing.items():
        if not (r.get("replicability_confidence") or "").strip():
            q = rep.get(code)
            r["replicability_confidence"] = (q.get("confidence") if q and r["pricing_mode"] == "差异化定价" else r.get("confidence")) or ""
        r.setdefault("rejudged_from", "")
        r.setdefault("rejudged_at", "")
    inputs = {r["security_code"].zfill(6): r for r in read(EXP / "inputs.csv")}
    new = []
    for part in sorted(EXP.glob("attributes_part*.csv")):
        new += read(part)
    for r in new:
        r["security_code"] = r["security_code"].strip().zfill(6)
        for k in list(r):
            r[k] = (r[k] or "").strip()
    codes = [r["security_code"] for r in new]
    missing = sorted(set(inputs) - set(codes))
    dupes = sorted(c for c, n in Counter(codes).items() if n > 1)
    extra = sorted(set(codes) - set(inputs))
    if missing or dupes or extra:
        issues.append(f"缺 {missing}，重复 {dupes}，多出 {extra}")
    for r in new:
        for k, allowed in ALLOWED.items():
            if r.get(k, "") not in allowed:
                issues.append(f"{r['security_code']} {k}={r.get(k)!r} 不在口径内")
        if r.get("derived_class") != derived(r):
            issues.append(f"{r['security_code']} 派生类别 {r.get('derived_class')!r} 与规则 {derived(r)!r} 不符")
        if r["pricing_mode"] == "差异化定价" and r["cost_position"] != "不适用":
            issues.append(f"{r['security_code']} 差异化定价却判成本地位 {r['cost_position']}")
        if (r.get("evidence_date") or "") > "2026-09-30":
            issues.append(f"{r['security_code']} 依据日 {r.get('evidence_date')} 晚于判定时点")
        if r["security_code"] in existing:
            issues.append(f"{r['security_code']} 已登记")
        r["guard_view"] = GUARD.get(r.get("derived_class"), "")
        r.update(rubric_version="v2", registered_at=REGISTERED_AT, rejudged_from="", rejudged_at="",
                 security_name=inputs.get(r["security_code"], {}).get("security_name", r.get("security_name", "")))
    if issues:
        print(json.dumps(dict(issues=issues), ensure_ascii=False, indent=1))
        raise SystemExit("核对未通过，未写登记表")
    rows = sorted(list(existing.values()) + new, key=lambda r: r["security_code"])
    for path in (EXP / "attributes.csv", REGISTRY):
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    growth_low = [(r["security_code"], r["security_name"]) for r in rows
                  if r["derived_class"] == "结构成长型" and r["replicability_confidence"] == "低"]
    res = dict(n=len(rows), n_new=len(new), by_class=dict(Counter(r["derived_class"] for r in rows)),
               new_by_class=dict(Counter(r["derived_class"] for r in new)),
               growth_low_confidence=growth_low,
               new_confidence=dict(Counter(r["confidence"] for r in new)))
    (EXP / "register.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
