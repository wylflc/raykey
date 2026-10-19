"""OI-291：把独立审计的正常化盈利折成模型口径，登记为档案研究数（工作流 §6.5.2.2），并写决策日志。

输入 `research/<代码>.json`：
    {"security_code", "security_name", "parent_yi": {"bear", "base", "bull"}（2026 年正常化归母净利，亿元，含净利息）,
     "evidence_date", "falsifier", "source"（报告与全文路径）, "review_id"（§6.9 登记表行）}

折算（§6.5.2.2，唯一实现 `build_report_update_queue.research_nopat_from_parent`）：
    研究数 = 归母 ÷ (1 − 生产带 minority_share) + (最新年报模型口径 NOPAT − 合并净利)
最新年报 NOPAT 按生产口径（非经营现金、notes_wc 受限现金、投入资本下限 0.1、研发资本化）由 `roic_inputs` 现算。
只写研究数四列，不写差距复核结论（采用与否由用户逐家裁定，§7.3）。
档案已「采用研究数」的行，新研究数会直接改生产带（§6.5.2.2），所以不覆盖、退出码 2，待用户裁定后加 --replace-adopted。
档案已有研究数（未采用）的，出处注明被替换的旧数与证据日。

    python3 register_research.py research/002415.json [--dry-run] [--replace-adopted]
"""
import argparse
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import roic_inputs as ri  # noqa: E402
from build_report_update_queue import research_nopat_from_parent  # noqa: E402
from workflow_decision_log import WORKFLOW_VERSION, append_decision_log  # noqa: E402

DOSSIERS = ROOT / 'data/processed/a_share_valuation_dossiers.csv'
BANDS = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
LOG = ROOT / 'data/processed/a_share_workflow_decision_log.csv'


def read_table(path: Path) -> tuple[list[list[str]], str]:
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    rows = list(csv.reader(io.StringIO(text, newline='')))
    if dump(rows, newline) != raw:
        raise ValueError(f'无法逐字节往返：{path}')
    return rows, newline


def dump(rows: list[list[str]], newline: str) -> bytes:
    out = io.StringIO(newline='')
    csv.writer(out, lineterminator=newline).writerows(rows)
    return out.getvalue().encode('utf-8')


def latest_annual(code: str, before: str) -> tuple[str, float, float]:
    """(年报期, 模型口径 NOPAT, 合并净利)，亿元；取可得日不晚于 `before` 的最新年报（按期末判，年报次年 4/30 前已披露）。"""
    years = ri.load_statements({code}, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc').get(code, {})
    rd = ri.load_rd_expense({code}).get(code, {})
    industry = {r['security_code']: r.get('csrc_industry') or r.get('industry') or ''
                for r in csv.DictReader((ROOT / 'data/reference/a_share_csrc_industry.csv').open(encoding='utf-8'))}
    cap = ri.capitalize_rd(years, rd, ri.rd_life(industry.get(code)))
    adj = cap[0] if cap else years
    annual = [p for p in sorted(adj) if p.endswith('12-31') and f'{int(p[:4]) + 1}-04-30' <= before]
    period = annual[-1]
    y = adj[period]
    return period, y.nopat / 1e8, y.net_profit / 1e8


def compute(spec: dict) -> dict:
    """研究数三档、模型锚与差距（亿元）；register_batch.py 预演出对照表也用它。"""
    code = spec['security_code'].zfill(6)
    band = next(r for r in csv.DictReader(BANDS.open(encoding='utf-8')) if r['security_code'].zfill(6) == code)
    minority = float(band['minority_share'] or 0.0)
    nopat_ps = float(band['model_nopat_ps'] if (band.get('research_overlay') or '').strip() else band['nopat_ps'])
    model_yi = nopat_ps * float(band['shares_est']) / 1e8
    period, nopat_yi, net_yi = latest_annual(code, spec['evidence_date'])
    conv = {k: research_nopat_from_parent(float(v), minority, nopat_yi, net_yi) for k, v in spec['parent_yi'].items()}
    gap = max(conv['base'], model_yi) / min(conv['base'], model_yi) - 1
    return dict(minority=minority, model_yi=model_yi, period=period, nopat_yi=nopat_yi, net_yi=net_yi, conv=conv, gap=gap)


def dossier_state(code: str) -> dict:
    """档案现有研究数与差距复核结论。"""
    docs, _ = read_table(DOSSIERS)
    col = {name: i for i, name in enumerate(docs[0])}
    row = next(r for r in docs[1:] if r[col['security_code']].zfill(6) == code.zfill(6))
    return dict(research=row[col['research_nopat_yi']].strip(), date=row[col['research_evidence_date']].strip(),
                conclusion=row[col['divergence_review_conclusion']].strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('json', type=Path)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--replace-adopted', action='store_true', help='用户已裁定改用新研究数时才用')
    args = ap.parse_args()
    spec = json.loads(args.json.read_text(encoding='utf-8'))
    code = spec['security_code'].zfill(6)
    res = compute(spec)
    minority, model_yi, period, nopat_yi, net_yi, conv, gap = (res[k] for k in
                                                               ('minority', 'model_yi', 'period', 'nopat_yi', 'net_yi', 'conv', 'gap'))
    source = (f"{spec['source']}：基准情景正常化归母净利 {spec['parent_yi']['base']:.2f} 亿 ÷ (1 − 生产带 minority_share {minority:.4f})"
              f" + ({period[:4]} 年报模型口径 NOPAT {nopat_yi:.2f} − 合并净利 {net_yi:.2f}) = {conv['base']:.2f} 亿"
              f"（§6.5.2.2 模型同口径；悲观／乐观 {conv['bear']:.2f}／{conv['bull']:.2f} 亿；用户 2026-10-19 裁定登记，OI-291）")
    falsifier = (f"{spec['falsifier']}；连续两个年报模型口径 NOPAT 落在 {conv['bear']:.2f}～{conv['bull']:.2f} 亿"
                 f"（悲观～乐观档换算）之外")
    print(f"{code} {spec['security_name']}：研究数 {conv['base']:.2f} 亿（{conv['bear']:.2f}～{conv['bull']:.2f}），"
          f"模型锚 {model_yi:.2f} 亿，差距 {gap:.1%}{'（超过 30%，§7.3 入队）' if gap > 0.30 + 1e-9 else ''}")
    docs, nl = read_table(DOSSIERS)
    col = {name: i for i, name in enumerate(docs[0])}
    row = next(r for r in docs[1:] if r[col['security_code']].zfill(6) == code)
    old, old_date = row[col['research_nopat_yi']].strip(), row[col['research_evidence_date']].strip()
    if row[col['divergence_review_conclusion']].strip() == '采用研究数' and not args.replace_adopted:
        print(f"{code} {spec['security_name']}：档案已采用研究数 {old} 亿（{old_date}），新研究数 {conv['base']:.2f} 亿未覆盖，待用户裁定")
        sys.exit(2)
    if old:
        source += f"；替换 {old_date} 登记的 {old} 亿"
    if args.dry_run:
        return
    for key, value in dict(research_nopat_yi=f"{conv['base']:.2f}", research_evidence_date=spec['evidence_date'],
                           research_falsifier=falsifier, research_source=source).items():
        row[col[key]] = value
    DOSSIERS.write_bytes(dump(docs, nl))
    decision_id = f"valuation_review:{spec['evidence_date']}:{code}:oi291_research_registered"
    with LOG.open(encoding='utf-8-sig', newline='') as fh:
        seen = {r['decision_id'] for r in csv.DictReader(fh)}
    if decision_id not in seen:
        append_decision_log(LOG, [dict(
            logged_at_utc=datetime.now(timezone.utc).isoformat(), workflow_stage='valuation_review',
            run_id=f"oi291:{spec['evidence_date']}", as_of=spec['evidence_date'], security_code=code, security_name=spec['security_name'],
            decision_type='research_normalized_earnings', decision_result='registered',
            summary_reason=(f"OI-291 池内独立审计登记研究数（§6.5.2.2）：{conv['base']:.2f} 亿（{conv['bear']:.2f}～{conv['bull']:.2f}），"
                            f"模型锚 {model_yi:.2f} 亿，差距 {gap:.1%}；独立评审 {spec['review_id']}。"),
            input_files=f"user_confirmation;{args.json.relative_to(ROOT) if args.json.is_absolute() else args.json}",
            source_urls='', output_file='data/processed/a_share_valuation_dossiers.csv',
            operator_or_script='exp_independent_pool_2026q3/tools/register_research.py', workflow_version=WORKFLOW_VERSION,
            decision_id=decision_id, supersedes_decision_id='')])
    print('已登记档案研究数与决策日志')


if __name__ == '__main__':
    main()
