"""按用户 2026-10-13 裁定落地五只结构性增长复核（工作流 §7.3、§6.5.2.2、§9.3.6 第 2 条）与登记表修订，并登记当日的规则与临时冻结裁定。

- 百济神州、沪电股份、鼎龙股份：登记研究数，差距复核结论「采用研究数」。
- 中微公司、天孚通信：登记研究数，结论「维持模型」。
- 登记表：百济神州、鼎龙股份可复制性把握由高降为中；鼎龙股份证据的毛利率口径与证伪阈值更正；天孚通信备注的大客户更正。类别不变。
- 临时冻结（§7.5、§10.1 第 2 条）：道通科技、景津装备、五粮液、恒立液压、新产业。

改写档案、登记表与临时冻结名单，向决策日志追加裁定行（按 decision_id 去重）。

    python3 data/experiments/exp_growth_reviews_20261013/apply_reviews.py
"""
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
REGISTRY = ROOT / "data/processed/a_share_business_attributes.csv"
DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
HOLDS = ROOT / "data/reference/review_holds.csv"
LOG = ROOT / "data/processed/a_share_workflow_decision_log.csv"
DAY = "2026-10-13"
VERSION = "a-share-selection-operation-v4.250"
HEAD = f"（用户 {DAY} 裁定，§7.3 结构性增长复核）："

NOTES = {
    "688235": ("采用研究数", "模型锚 {model:.2f} 亿由峰守卫取五年比率中位（w = 1，守卫砍掉每股 NOPAT 87%），窗口含 2021～2022 年亏损与 2023 年刚转正的年份；"
                         "研究数 106.40 亿按公司 2026 年指引中值（经营利润 68 亿元）得正常化归母 52.3 亿元，经股权桥加回研发资本化 54.08 亿元，不计在研管线；"
                         "V 37.02→87.35，P/V 6.59→2.79，股价 ≤ 87.65 才到买入线；区间 84.40～137.10 亿对应 P/V 3.34～2.27。"
                         "研究数的 51% 是研发资本化加回，美国药价政策与 BTK 竞争是主要不确定项。"),
    "002463": ("采用研究数", "模型锚 {model:.2f} 亿由峰守卫取五年比率中位（w = 1，守卫砍掉每股 NOPAT 56%）；"
                         "研究数 48.80 亿按二季度年化营收 299 亿元的现有产能、稼动率 99%→90%、数据通讯板毛利率 38%（二季度 46.2% 中约 8pp 视为高阶产能紧缺溢价）；"
                         "V 21.71→44.88，P/V 5.34→2.58，股价 ≤ 45.03 才到买入线；区间 35.90～64.10 亿对应 P/V 3.91～1.89。"
                         "可复制性把握仍为低：2027 年同业产能落地后数据通讯板毛利率低于 34% 即改判易复制。"),
    "300054": ("采用研究数", "模型锚 {model:.2f} 亿（已叠加 2026-10-09 三季度预告）由峰守卫取五年比率中位（w = 1，守卫砍掉每股 NOPAT 43%），窗口含低毛利耗材为主的年份；"
                         "研究数 14.26 亿按抛光垫现有产能 110 万片、利用率 80%、半导体材料毛利率 69%（2024～2025 年水平），光刻胶与先进封装只计费用；"
                         "V 10.07→17.65，P/V 6.20→3.54，股价 ≤ 17.71 才到买入线；区间 11.55～17.00 亿对应 P/V 4.58～2.81。"),
    "688012": ("维持模型", "研究数 24.80 亿低于模型锚 {model:.2f} 亿 30.1%，差距来自研发按稳态 13% 营收扣减的判断（每 1pp 营收约 1.3 亿元）；"
                         "按模型机械摊销为 31.22 亿、与锚差 3%，研究区间 16.26～36.64 亿覆盖模型锚。峰守卫砍掉的 56% 主要是 TTM 因子里的金融收益，不支持放宽。"
                         "研究口径 P/V 6.17（区间 8.45～4.64）。"),
    "300394": ("维持模型", "研究数 20.35 亿较模型锚 {model:.2f} 亿高 24.5%，未过 30%；按无源常态毛利率 64%（上半年 71.9% 中约 8pp 视为紧缺溢价）、"
                         "有源现有产能约 40 亿元 × 85%、毛利率 43%。有源现有产能取 50 亿元或无源常态毛利率取 68% 时差距升到约 40%，三季报后复看。"
                         "研究口径 P/V 8.92（区间 12.72～6.11）。"),
}

REGISTER_UPDATES = {
    "688235": dict(replicability_confidence="中",
                   note_prefix=f"{DAY} 研究复核：可复制性把握由高降为中（礼来匹妥布替尼 2026-10-02 获 FDA 批准一线 CLL，阿可替尼联合维奈克拉固定疗程 02-20 获批）。"),
    "300054": dict(replicability_confidence="中",
                   evidence="CMP抛光垫国产约九成+抛光液、清洗液延伸，YPI/PSPI显示材料国产独家批量；半导体材料毛利率69.6%（2025年，公司综合50.85%）、为利润主体；"
                            "需求随大陆晶圆扩产与国产替代扩张（仓库2026-08）",
                   falsifier="CMP抛光垫收入年增<15%，或半导体材料毛利率连续两季<66%→改判",
                   note_prefix=f"{DAY} 研究复核：可复制性把握由高降为中（Qnity 仍占中国抛光垫约五成，彤程新材硬垫已过头部客户验证）；毛利率更正为半导体材料口径，"
                               "证伪阈值 48%→66%；硒鼓墨盒 2026-04 出表、皓飞新材 2026-03 并表。"),
    "300394": dict(note="已入§7.3队列（量驱动、守卫砍41%），与业务判断一致；第一大客户 Fabrinet 2025 年占 63.3%（前五大 89.7%），CPO重构器件形态",
                   note_prefix=f"{DAY} 研究复核：更正大客户。"),
}

HOLD_NOTES = {
    "688208": "深圳证监局〔2025〕234 号认定实控人关联方占用上市公司资金 2,442 万元未披露，实控人仍兼董事长、总经理；Q4 70→56",
    "603279": "实控人兼董事长、总经理 2025-06 被留置并立案调查、11 月解除，事由与结论未披露；候选侧 P/V 0.96 在买入区内；Q4 72→62",
    "000858": "董事长 2026-02 被立案留置并于 06 月免职，2025 年三份季报收入确认更正（前三季度营收调减 303 亿元）；Q4 72→60",
    "601100": "实控人、董事长 2026-03 被江苏省监察委员会立案留置，24 天后恢复履职，立案结论未披露；Q4 78→66",
    "300832": "实控人 2026-07 被监察机关留置，机关与事由未披露、未见解除；控股股东质押约五成；Q4 74→66",
}
HOLD_BASIS = "§10.1 第 2 条；OI-286"
HOLD_RELEASE = "涉案或整改结论披露，或用户另行裁定"


def read_table(path: Path) -> tuple[list[list[str]], str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if dump(rows, newline) != raw:
        raise ValueError(f"无法逐字节往返：{path}")
    return rows, newline


def dump(rows: list[list[str]], newline: str) -> bytes:
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator=newline).writerows(rows)
    return out.getvalue().encode("utf-8")


def main() -> None:
    reviews = {c: json.loads((EXP / f"{c}.json").read_text(encoding="utf-8")) for c in NOTES}
    model_yi = json.loads((EXP / "inputs.json").read_text(encoding="utf-8"))
    model_yi = {c: float(model_yi[c]["model_anchor_yi"]) for c in NOTES}

    reg, reg_nl = read_table(REGISTRY)
    rh = reg[0]
    for row in reg[1:]:
        upd = REGISTER_UPDATES.get(row[rh.index("security_code")].zfill(6))
        if not upd:
            continue
        upd = dict(upd)
        prefix = upd.pop("note_prefix")
        for key, value in upd.items():
            row[rh.index(key)] = value
        note = row[rh.index("note")]
        if not note.startswith(prefix):
            row[rh.index("note")] = (prefix + note)[:300]
        row[rh.index("registered_at")] = DAY
    REGISTRY.write_bytes(dump(reg, reg_nl))

    docs, doc_nl = read_table(DOSSIERS)
    dh = docs[0]
    for row in docs[1:]:
        code = row[dh.index("security_code")].zfill(6)
        if code not in reviews:
            continue
        j, (conclusion, note) = reviews[code], NOTES[code]
        values = dict(research_nopat_yi=f"{j['research_nopat_yi']:.2f}", research_evidence_date=j["research_evidence_date"],
                      research_falsifier=j["research_falsifier"], research_source=j["research_source"],
                      divergence_reviewed_at=DAY, divergence_review_conclusion=conclusion,
                      divergence_review_note=conclusion + HEAD + note.format(model=model_yi[code]),
                      divergence_reviewed_model_yi=f"{model_yi[code]:.2f}",
                      divergence_reviewed_research_yi=f"{j['research_nopat_yi']:.2f}")
        for key, value in values.items():
            row[dh.index(key)] = value
    DOSSIERS.write_bytes(dump(docs, doc_nl))

    holds, hold_nl = read_table(HOLDS)
    hh = holds[0]
    active = {r[hh.index("security_code")].zfill(6) for r in holds[1:] if not r[hh.index("released_at")].strip()}
    names = {r[rh.index("security_code")].zfill(6): r[rh.index("security_name")] for r in reg[1:]}
    names["000858"] = "五粮液"
    for code, note in HOLD_NOTES.items():
        if code not in active:
            holds.append([dict(security_code=code, security_name=names[code], basis=HOLD_BASIS, ruled_at=DAY,
                               release_condition=HOLD_RELEASE, released_at="", note=note)[k] for k in hh])
    HOLDS.write_bytes(dump(holds, hold_nl))

    with LOG.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields, seen = list(reader.fieldnames or []), {r["decision_id"] for r in reader}
    now, new = datetime.now(timezone.utc).isoformat(), []

    def add(stage, run_id, code, name, dtype, result, summary, inputs, output, decision_id):
        if decision_id not in seen:
            new.append(dict(logged_at_utc=now, workflow_stage=stage, run_id=run_id, as_of=DAY, security_code=code, security_name=name,
                            decision_type=dtype, decision_result=result, summary_reason=summary, input_files=inputs, source_urls="",
                            output_file=output, operator_or_script="Claude", workflow_version=VERSION, decision_id=decision_id,
                            supersedes_decision_id=""))

    add("workflow_rule", "v4.250-20261013", "ALL", "", "trading_rule", "adopted",
        "用户2026-10-13裁定（v4.250）：①§7.4 负面事件——全部池成员与持仓每晚筛查交易所公告与东财资讯新闻标题，命中即登记待复核行、当晚处置，处置前冻结新增买入；"
        "事件按首次公开时已知事实复核，不等监管结论（结 OI-285）；②OI-286 存量事件现在全部补核；③§9.3.6 第 6 条——成长股定期报告吸收后核对可证伪条件，"
        "候选侧P/V不高于买入线1.2倍且无有效通过记录的同晚预做重点复核；④§7.5——按§10.1第2条裁定暂停买入的个股登记临时冻结名单。",
        "user_confirmation;data/experiments/exp_oi285_20261013/replay_report.txt",
        "docs/000_Ashare_workflow.md;scripts/screen_pool_events.py;scripts/growth_stocks.py;scripts/build_report_update_queue.py",
        "workflow_rule:2026-10-13:ALL:negative_event_screen")
    for code, (conclusion, note) in NOTES.items():
        j = reviews[code]
        add("valuation_review", f"structural_growth_review:{DAY}", code, j["security_name"], "research_model_divergence_review", conclusion,
            f"研究 {j['research_nopat_yi']:.2f} 亿、模型锚 {model_yi[code]:.2f} 亿；{conclusion}{HEAD}{note.format(model=model_yi[code])}",
            f"user_confirmation;data/experiments/exp_growth_reviews_20261013/{code}.json",
            "data/processed/a_share_valuation_dossiers.csv", f"valuation_review:{DAY}:{code}:research")
    for code, upd in REGISTER_UPDATES.items():
        add("quality_review", f"structural_growth_review:{DAY}", code, reviews[code]["security_name"], "business_attributes_update", "结构成长型（类别不变）",
            upd["note_prefix"], f"user_confirmation;data/experiments/exp_growth_reviews_20261013/{code}.json",
            "data/processed/a_share_business_attributes.csv", f"quality_review:{DAY}:{code}:business_attributes_update")
    for code, note in HOLD_NOTES.items():
        add("valuation_review", f"governance_hold:{DAY}", code, names[code], "user_review_hold", "registered",
            f"§7.5 临时冻结登记（用户 {DAY} 裁定，§10.1 第 2 条）：{note}；解除条件：{HOLD_RELEASE}",
            f"user_confirmation;data/experiments/exp_oi286_20261013/{code}.json", "data/reference/review_holds.csv",
            f"valuation_review:{DAY}:{code}:user_review_hold_registered")
    if new:
        with LOG.open("a", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=fields).writerows(new)
    result = dict(adopted=[c for c, (k, _) in NOTES.items() if k == "采用研究数"], maintained=[c for c, (k, _) in NOTES.items() if k == "维持模型"],
                  register_updates=sorted(REGISTER_UPDATES), holds=sorted(HOLD_NOTES), model_yi=model_yi, log_rows_added=len(new))
    (EXP / "rulings.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
