"""按用户 2026-10-01 裁定落地五只复核（工作流 §9.3.6、§6.5.2.2、§7.3；个人投资体系第 5.12 节）。

- 中际旭创、新易盛：登记研究数，差距复核结论「采用研究数」。
- 阳光电源：可复制性改判易复制（储能），类别改为可复制成长型；登记研究数并采用。
- 中际联合：需求空间改判存量，类别改为稳定型；登记研究数并采用（g0 照带，用户裁定不改研究增长规则，另立 OI-252）。
- 特宝生物：登记研究数（与模型锚差 2.7%，不入队、不采用）；§9.3.6 重点复核「通过」。

改写登记表与档案，并向决策日志追加裁定行（按 decision_id 去重）。

    python3 apply_reviews.py
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
REGISTRY = ROOT / "data/processed/a_share_business_attributes.csv"
DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
LOG = ROOT / "data/processed/a_share_workflow_decision_log.csv"
BANDS = ROOT / "data/processed/a_share_pool_model_bands_adopted.csv"
DAY = "2026-10-01"
VERSION = "a-share-selection-operation-v4.228"
GROWTH_FIELDS = ["growth_reviewed_at", "growth_review_conclusion", "growth_review_note", "growth_reviewed_pv"]
GUARD = {"可复制成长型": "保留：扩产与竞争会侵蚀回报", "稳定型": "保留：守卫作用多为消化一次性高位"}

REGISTER_UPDATES = {
    "300308": dict(replicability_confidence="中",
                   falsifier="北美云厂资本开支指引下修>15%，或CPO替代可插拔加速，或毛利率<34%",
                   note_prefix="2026-10-01 研究复核：可复制性把握由高降为中（同业两年内可扩产，稀缺溢价约 8pp 已剔入研究数）；毛利率阈值 38%→34% 与研究数中枢一致。"),
    "300274": dict(replicability="易复制", replicability_confidence="中", derived_class="可复制成长型",
                   evidence="需求增长在储能而储能易复制：同业电芯产能2026年底1.2–1.5TWh、比亚迪与宁德储能大增，特斯拉储能毛利30.3%→20.4%，公司储能毛利36.5%→32.4%；逆变器仍为双寡头（2026-09）",
                   evidence_date="2026-09-29", falsifier="储能毛利率连续两个半年度≥34% → 改回难复制（结构成长型）",
                   confidence="中", rejudged_from="结构成长型", rejudged_at=DAY,
                   note_prefix="用户 2026-10-01 裁定改判（§9.3.6 重点复核；原结构成长型、可复制性把握低）。"),
    "605305": dict(demand_runway="存量", replicability_confidence="中", derived_class="稳定型",
                   evidence="GWEC（2026-04）全球风电新增装机2025→2028年复合约5.5%（陆上2.8%、海上29%），中国2026年1–7月并网−12%；增量在海上与后市场，行业量增约等于名义GDP",
                   evidence_date="2026-09-14", falsifier="GWEC或CWEA显示2026–28年全球新增年复合≥8%，或中国2027年新增≥140GW → 改回结构扩张",
                   confidence="中", rejudged_from="结构成长型", rejudged_at=DAY,
                   note_prefix="用户 2026-10-01 裁定改判存量（§9.3.6 重点复核；原结构成长型、把握低）；外销毛利率 56%～60% 未见压价，可复制性维持难复制（把握由低升为中）。"),
}

ADOPT = {
    "300308": "采用研究数（用户 2026-10-01 裁定，§7.3 结构性增长复核）：模型锚 75.61 亿由峰守卫取五年比率中位（w = 1，守卫砍掉每股 NOPAT 78%）；"
              "研究数 195.66 亿按二季度产能与 80% 目标利用率、常态毛利率 38%（二季度 46.4% 中约 8pp 视为 InP 激光器与 DSP 紧缺溢价）；"
              "V 98.33→311.12，P/V 8.22→2.60，股价 ≤ 312.18 才到买入线；区间 148.43～252.65 亿对应 P/V 3.57～1.93。"
              "生产带未含 H 股发行与回购，粗略备考 P/V 约 2.4，待下一期报表进模型。",
    "300502": "采用研究数（用户 2026-10-01 裁定，§7.3 结构性增长复核）：模型锚 57.25 亿由峰守卫取五年比率中位（w = 1，守卫砍掉每股 NOPAT 69%）；"
              "研究数 133.93 亿按现有产能 2,836 万只、利用率 90%、常态毛利率 40%（2023 年 31.0%→2026H1 48.4% 的 17pp 中约 8pp 视为短缺溢价）；"
              "V 68.05→174.01，P/V 5.72→2.24，股价 ≤ 174.60 才到买入线；区间 101.71～175.97 亿对应 P/V 3.05～1.63。",
    "300274": "采用研究数（用户 2026-10-01 裁定，同日可复制性改判易复制、类别改为可复制成长型）：模型锚 175.14 亿 = 三年回报中位 37.0% × 已增约 40% 的经营账面"
              "（λ = 0，TTM 因子 0.816 不进锚），高于 2025 年报 NOPAT 149.40 亿与 TTM 约 119 亿；研究数 106.5 亿按 2026 年量（储能 380 亿 × 30%、逆变器等 260 亿 × 37%）；"
              "V 125.78→77.24，P/V 0.656→1.068，退出买入区；股价 ≤ 77.50 才到买入线。上半年归母 −32% 来自 136 号文后国内装机下降、上年沙特项目高基数与储能毛利下降。",
    "605305": "采用研究数（用户 2026-10-01 裁定，同日需求空间改判存量、类别改为稳定型）：差距 10.5% 未超过 30%，用户要求以研究数作 P/V 依据；研究数 4.68 亿按内销 9.0 亿 × 35%、外销 9.4 亿 × 57% 推算；"
              "g0 仍按生产带 19.68%（研究增长只许本公司已实现资本腿，用户裁定不改规则，g0 偏高另立 OI-252）；V 45.35→41.24，P/V 0.669→0.735。"
              "Q2 归母 −17.7% 主因汇兑与退税，模型口径 EBIT 上半年 +23%。",
}
GROWTH_PASS = {
    "688278": "重点复核通过（用户 2026-10-01 裁定）：研究数 14.25 亿（区间 13.35～15.25，与模型锚 13.87 亿差 2.7%），研究口径 V 61.99、P/V 0.853；"
              "利润放缓来自 2026-01-01 起增值税改一般计税（净收入 −8.85%）与 ACT580 首付款费用化，Q2 归母 +27%；两年内无同类 PEG-IFN 获批，替代威胁为 GSK bepirovirsen（在华约 2027 年后获批）。"
              "可证伪：2026 年报归母（剔除首付款）< 10.9 亿，或 2027 年上半年营收增速 < 10%，或 bepirovirsen 在华获批并进医保。",
}


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    reviews = {c: json.loads((EXP / f"{c}.json").read_text(encoding="utf-8")) for c in ("300308", "300502", "300274", "605305", "688278")}
    bands = {r["security_code"]: r for r in read(BANDS)[0]}
    model_yi = {c: float(bands[c]["nopat_ps"]) * float(bands[c]["shares_est"]) / 1e8 for c in reviews}
    pv_0930 = {r["security_code"]: r["model_pv"] for r in read(ROOT / "data/processed/daily_buy_candidates.csv")[0]
               if r["trade_date"] == "2026-09-30"}      # 复核时的候选侧生产 P/V（09-30 扫描）

    reg_rows, reg_fields = read(REGISTRY)
    for r in reg_rows:
        upd = REGISTER_UPDATES.get(r["security_code"])
        if not upd:
            continue
        upd = dict(upd)
        prefix = upd.pop("note_prefix")
        if not (r.get("note") or "").startswith(prefix):
            r["note"] = (prefix + (r.get("note") or ""))[:300]
        r.update(upd)
        if r["derived_class"] in GUARD:
            r["guard_view"] = GUARD[r["derived_class"]]
    write(REGISTRY, reg_rows, reg_fields)

    doc_rows, doc_fields = read(DOSSIERS)
    doc_fields += [f for f in GROWTH_FIELDS if f not in doc_fields]
    for d in doc_rows:
        code = d["security_code"]
        for f in GROWTH_FIELDS:
            d.setdefault(f, "")
        if code not in reviews:
            continue
        j = reviews[code]
        d.update(research_nopat_yi=f"{j['research_nopat_yi']:.2f}", research_evidence_date=j["research_evidence_date"],
                 research_falsifier=j["research_falsifier"], research_source=j["research_source"])
        if code in ADOPT:
            d.update(divergence_reviewed_at=DAY, divergence_review_conclusion="采用研究数", divergence_review_note=ADOPT[code],
                     divergence_reviewed_model_yi=f"{model_yi[code]:.2f}", divergence_reviewed_research_yi=f"{j['research_nopat_yi']:.2f}")
        if code in GROWTH_PASS:
            d.update(growth_reviewed_at=DAY, growth_review_conclusion="通过", growth_review_note=GROWTH_PASS[code],
                     growth_reviewed_pv=pv_0930[code])
    write(DOSSIERS, doc_rows, doc_fields)

    log_rows, log_fields = read(LOG)
    seen = {r["decision_id"] for r in log_rows}
    now = datetime.now(timezone.utc).isoformat()
    names = {c: reviews[c]["security_name"] for c in reviews}
    new = []

    def add(stage, run_id, code, name, dtype, result, summary, output, decision_id):
        if decision_id in seen:
            return
        new.append(dict(logged_at_utc=now, workflow_stage=stage, run_id=run_id, as_of=DAY, security_code=code, security_name=name,
                        decision_type=dtype, decision_result=result, summary_reason=summary,
                        input_files=f"user_confirmation;data/experiments/exp_growth_reviews_20261001/{code}.json" if code != "ALL" else "user_confirmation",
                        source_urls="", output_file=output, operator_or_script="Claude", workflow_version=VERSION,
                        decision_id=decision_id, supersedes_decision_id=""))

    add("workflow_rule", "v4.228-20261001", "ALL", "", "trading_rule", "adopted",
        "用户2026-10-01裁定成长股模块（v4.228，§9.3.6，独立于回测）：①成长股（业务属性登记为结构成长型）研究数经用户裁定采用后进生产带，候选侧P/V达买入线而无有效重点复核「通过」记录的不进合格集，复核通过后与其他候选同一执行清单；"
        "②成长股持仓市值合计≤净资产20%，只挡买入；③成长股不做涨幅减持、不作换仓卖出源，持仓侧P/V≥2.0每日减一档，复核改判后每日减一档直至清空；④业务属性登记扩到池内全部ROIC路径（173只），可复制性另记把握，把握低的难复制保留并标记、P/V达线时重点复核重判。回测不复现（成文差异）。",
        "docs/000_Ashare_workflow.md;docs/000_personal-investment-system-v1.zh.md;scripts/screen_daily_volume_price_signals.py;scripts/growth_stocks.py",
        "workflow_rule:2026-10-01:ALL:growth_module")
    add("quality_review", "oi250_register_full:2026-10-01", "ALL", "", "business_attributes", "registered",
        "业务属性登记扩到池内全部ROIC路径（用户2026-10-01裁定）：新登记116只（口径v2），合计173只：结构成长型48（复核后46）、可复制成长型14（复核后15）、稳定型82（复核后83）、成本领先周期型24、价格周期型5；可复制性把握低的结构成长型10只标记。",
        "data/processed/a_share_business_attributes.csv", "quality_review:2026-10-01:ALL:business_attributes_full")
    for code, cls in (("300274", "可复制成长型"), ("605305", "稳定型")):
        add("quality_review", "growth_focused_review:2026-10-01", code, names[code], "business_attributes_rejudge", cls,
            REGISTER_UPDATES[code]["note_prefix"] + REGISTER_UPDATES[code]["evidence"],
            "data/processed/a_share_business_attributes.csv", f"quality_review:2026-10-01:{code}:rejudge")
    for code, note in ADOPT.items():
        j = reviews[code]
        add("valuation_review", "oi209_divergence_review:2026-10-01", code, names[code], "research_model_divergence_review", "采用研究数",
            f"研究 {j['research_nopat_yi']:.2f} 亿、模型锚 {model_yi[code]:.2f} 亿；{note}",
            "data/processed/a_share_valuation_dossiers.csv", f"valuation_review:2026-10-01:{code}:research")
    j = reviews["688278"]
    add("valuation_review", "growth_focused_review:2026-10-01", "688278", names["688278"], "growth_focused_review", "通过",
        f"研究 {j['research_nopat_yi']:.2f} 亿登记（与模型锚 {model_yi['688278']:.2f} 亿差 2.7%，不入队、不采用）；{GROWTH_PASS['688278']}",
        "data/processed/a_share_valuation_dossiers.csv", "valuation_review:2026-10-01:688278:growth_review")
    if new:
        with LOG.open("a", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=log_fields).writerows(new)
    res = dict(register_updates=sorted(REGISTER_UPDATES), adopted=sorted(ADOPT), growth_pass=sorted(GROWTH_PASS),
               model_yi={c: round(v, 2) for c, v in model_yi.items()}, log_rows_added=len(new))
    (EXP / "rulings.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
