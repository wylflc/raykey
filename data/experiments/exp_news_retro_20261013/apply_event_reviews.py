"""按 `reviews.json` 落地新闻回扫检出的存量事件的质量复核（工作流 §7.4、§5.7、§5.8）。

每家：分层表改 Q4／参考分／旗标／理由与证据字段，档案追加复核触发，估值证据追加公告与结论，决策日志追加一行，
负面事件登记表登记并处置：`disposition` 缺省「事件复核」，写「不构成事件」的只处置登记行、不动分层表。
事实取自同目录 `<代码>.json`（取证产物）。重复运行按 decision_id 跳过。

    python3 data/experiments/exp_news_retro_20261013/apply_event_reviews.py [--dry-run]
"""
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import screen_pool_events as ev  # noqa: E402
from workflow_decision_log import WORKFLOW_VERSION, append_decision_log  # noqa: E402

TIERS = ROOT / "data/processed/a_share_watchlist_quality_tiers.csv"
DOSSIERS = ROOT / "data/processed/a_share_valuation_dossiers.csv"
LOG = ROOT / "data/processed/a_share_workflow_decision_log.csv"
EVIDENCE = ROOT / "data/interim/valuation_evidence"
PDFS = ROOT / "data/scratch/experiments/exp_news_retro_20261013/pdf"
DAY = "2026-10-13"
DRY = "--dry-run" in sys.argv


def read_table(path: Path) -> tuple[list[list[str]], str, bytes]:
    """读表并核对能逐字节往返；返回 (行, 行尾, 原字节)。"""
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if dump(rows, newline, bom) != raw:
        raise ValueError(f"无法逐字节往返：{path}")
    return rows, newline, raw


def dump(rows: list[list[str]], newline: str, bom: bool) -> bytes:
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator=newline).writerows(rows)
    return (b"\xef\xbb\xbf" if bom else b"") + out.getvalue().encode("utf-8")


# 参考分 = Q1×0.25 + Q2×0.40 + Q3×0.20 + Q4×0.15 − 报表可信度扣分（§5.7）；本脚本只按变动量改参考分
WEIGHTS = {"q3": ("q3_capital_allocation_score", 0.20, "Q3"), "q4": ("q4_management_score", 0.15, "Q4")}


def main() -> None:
    reviews = json.loads((EXP / "reviews.json").read_text(encoding="utf-8"))
    logged = LOG.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tier_rows, tier_nl, tier_raw = read_table(TIERS)
    dossier_rows, dossier_nl, dossier_raw = read_table(DOSSIERS)
    th, dh = tier_rows[0], dossier_rows[0]
    tiers = {r[th.index("security_code")].zfill(6): r for r in tier_rows[1:]}
    dossiers = {r[dh.index("security_code")].zfill(6): r for r in dossier_rows[1:]}
    members = ev.load_members()
    register = {(r["security_code"], r["detected_on"]): r for r in ev.load_register()}
    log_rows, done = [], []
    for code, rv in reviews.items():
        decision_id = f"quality_review:{DAY}:{code}:{rv.get('decision_suffix', 'event')}"
        if rv.get("disposition") == "不构成事件":
            if not (register.get((code, DAY)) or {}).get("disposition"):
                if not DRY:
                    ev.dispose(code, DAY, "不构成事件", rv["summary"], DAY)
                print(code, rv["name"], "不构成事件")
            continue
        if decision_id in logged:
            print("已落地，跳过", code, rv["name"])
            continue
        row = tiers[code]
        get = lambda k: row[th.index(k)]                      # noqa: E731

        def put(key: str, value: str) -> None:
            row[th.index(key)] = value

        assert get("security_name") == rv["name"], (code, get("security_name"))
        old_score, tier = get("quality_score"), get("quality_tier")
        change, delta = [], 0.0
        for key, (column, weight, label) in WEIGHTS.items():
            if rv.get(key):
                old, new = rv[key]
                assert float(get(column)) == old, (code, column, get(column))
                if new == old:
                    continue
                put(column, f"{new:g}")
                change.append(f"{label} {old:g}→{new:g}")
                delta += weight * (new - old)
        if rv.get("deduction"):   # 表内扣分记为非正数
            old, new = rv["deduction"]
            assert abs(float(get("credibility_deduction") or 0)) == old, (code, get("credibility_deduction"))
            put("credibility_deduction", f"-{new:g}" if new else "0")
            change.append(f"报表可信度扣分 {old:g}→{new:g}")
            delta -= new - old
        new_score = old_score
        if change:
            new_score = f"{float(old_score) + delta:.1f}"
            put("quality_score", new_score)
            put("score_version", "v" + WORKFLOW_VERSION.rsplit("v", 1)[1])
            put("scored_at", DAY)
            put("score_reason", f"{DAY} 事件复核（{rv['event']}）：{'，'.join(change)}，其余不变 → 参考分 {old_score}→{new_score}；"
                                f"档位 {tier} 不变。｜" + get("score_reason"))
        for key in ("q3_reason", "q4_reason"):
            if rv.get(key):
                put(key, rv[key] + (f"｜此前：{get(key)}" if get(key).strip() else ""))
        if rv.get("flags_add"):
            put("flags", "; ".join(x for x in (rv["flags_add"], get("flags").strip()) if x))
        if rv.get("erosion_add"):
            put("q2_erosion_paths", "；".join(x for x in (get("q2_erosion_paths").strip().rstrip("。；"), rv["erosion_add"]) if x))
        put("evidence_note", rv["evidence_note"] + (" ｜ " + get("evidence_note") if get("evidence_note").strip() else ""))
        put("evidence_sources", "; ".join(x for x in (get("evidence_sources").strip(), f"{DAY} 事件复核：" + rv["sources"]) if x))
        put("decision_log_summary", rv["summary"])
        put("reviewed_at_utc", now)
        put("workflow_version", WORKFLOW_VERSION)
        if rv.get("evidence_available_at", "") > get("evidence_available_at"):
            put("evidence_available_at", rv["evidence_available_at"])
        if rv.get("triggers_add") and code in dossiers:
            d = dossiers[code]
            i = dh.index("review_triggers")
            if rv["triggers_add"] not in d[i]:
                d[i] = "；".join(x for x in (d[i].strip().rstrip("；"), rv["triggers_add"]) if x)
        result = (f"worth_attention、{tier} 维持（" + ("，".join(change) + f"，参考分 {old_score}→{new_score}" if change else "分数不变") + "）")
        log_rows.append({
            "logged_at_utc": now, "workflow_stage": "quality_review", "run_id": f"event_quality_review:{DAY}", "as_of": DAY,
            "security_code": code, "security_name": rv["name"], "decision_type": "quality_tier_review",
            "decision_result": result,
            "summary_reason": f"§7.4 负面事件复核（近 6 个月新闻回扫的存量补核，沿用用户 {DAY} 全部补完的裁定；模型推导，用户可覆盖）。" + rv["evidence_note"],
            "input_files": f"data/experiments/exp_news_retro_20261013/{code}.json", "source_urls": rv["sources"],
            "output_file": "data/processed/a_share_watchlist_quality_tiers.csv", "operator_or_script": "Claude",
            "workflow_version": WORKFLOW_VERSION, "decision_id": decision_id, "supersedes_decision_id": ""})
        done.append((code, rv, result))
        print(code, rv["name"], result)
    if DRY or not done:
        print("dry-run，不写文件" if DRY else "无新增")
        return
    TIERS.write_bytes(dump(tier_rows, tier_nl, tier_raw.startswith(b"\xef\xbb\xbf")))
    DOSSIERS.write_bytes(dump(dossier_rows, dossier_nl, dossier_raw.startswith(b"\xef\xbb\xbf")))
    append_decision_log(LOG, log_rows)
    for code, rv, result in done:
        path = EVIDENCE / f"{code}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            manual = data.setdefault("manual_evidence", [])
            for doc in rv.get("documents", []):
                item = dict(recorded_at=DAY, evidence_type=doc.get("type", "公告"), title=doc["title"],
                            notice_date=doc.get("date", ""), source_url=doc["url"], summary=doc["summary"], use=doc.get("use", "事件事实"))
                pdf = PDFS / doc.get("art", "-") / "doc.pdf"
                if pdf.exists():
                    item["source_sha256"] = hashlib.sha256(pdf.read_bytes()).hexdigest()
                manual.append(item)
            manual.append(dict(recorded_at=DAY, evidence_type="质量复核结论", title=f"{rv['event']}事件复核", summary=rv["summary"],
                               use=f"结构化结论见分层表与决策日志 quality_review:{DAY}:{code}:event"))
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            print("  无估值证据文件，跳过 manual_evidence：", code)
        if (code, DAY) not in register:
            ev.add(code, DAY, rv["headline"], rv["first_event_date"], sources="存量补核", members=members)
        if (register.get((code, DAY)) or {}).get("disposition"):   # 当日已处置的行：补充复核只在说明后追加
            rows = ev.load_register()
            row = next(r for r in rows if (r["security_code"], r["detected_on"]) == (code, DAY))
            row["note"] = row["note"] + "｜补充：" + result + "｜" + rv["summary"]
            ev.write_register(rows)
        else:
            ev.dispose(code, DAY, "事件复核", result + "｜" + rv["summary"], DAY)
    print(f"落地 {len(done)} 家")


if __name__ == "__main__":
    main()
