#!/usr/bin/env python3
"""OI-291：按用户裁定写档案的差距复核结论（工作流 §7.3、§6.5.2.2），每家追加一行决策日志。

输入 JSON（列表）：[{"security_code", "conclusion": "采用研究数|维持模型", "reason"}]。研究数取档案现值（register_batch.py 已登记），
模型锚按 §6.5.2.2 现算，研究口径 V 用生产叠加的同一实现 `apply_forecast_band_overlay.apply_research_overlay`。
档案在发布凭据的输入摘要内：当日清单已发布、尚未到下一次收盘时拒绝写入（§7.3 发布后改动须当晚重跑，见 README）。

    python3 tools/apply_rulings.py rulings.json --day 2026-10-20 --review-batch b01 [--dry-run]
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / 'scripts'))
import register_batch  # noqa: E402
import register_research as rr  # noqa: E402
from apply_forecast_band_overlay import apply_research_overlay  # noqa: E402
from workflow_decision_log import WORKFLOW_VERSION, append_decision_log  # noqa: E402

BANDS = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
REGISTRY = ROOT / 'data/processed/independent_valuations.csv'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('rulings', type=Path)
    ap.add_argument('--day', required=True, help='裁定日（北京时间）')
    ap.add_argument('--review-batch', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    ok, msg = register_batch.research_window()
    print(msg)
    if not ok and not args.dry_run:
        raise SystemExit('清单已发布、尚未到下一次收盘：裁定留待下一次扫描之前登记')
    bands = {r['security_code'].zfill(6): r for r in csv.DictReader(BANDS.open(encoding='utf-8'))}
    reviews = {r['security_code']: r for r in csv.DictReader(REGISTRY.open(encoding='utf-8'))
               if r['market'] == 'A' and r['status'] == 'current'}
    docs, nl = rr.read_table(rr.DOSSIERS)
    col = {name: i for i, name in enumerate(docs[0])}
    with rr.LOG.open(encoding='utf-8-sig', newline='') as fh:
        seen = {r['decision_id']: r for r in csv.DictReader(fh)}
    log_rows = []
    for item in json.loads(args.rulings.read_text(encoding='utf-8')):
        code, conclusion = item['security_code'].zfill(6), item['conclusion']
        if conclusion not in ('采用研究数', '维持模型'):
            raise SystemExit(f'{code} 结论只能是采用研究数或维持模型：{conclusion}')
        row = next(r for r in docs[1:] if r[col['security_code']].zfill(6) == code)
        name = row[col['security_name']]
        spec = json.loads((EXP / 'research' / f'{code}.json').read_text(encoding='utf-8'))
        research = float(row[col['research_nopat_yi']])
        if abs(research - float(f"{rr.compute(spec)['conv']['base']:.2f}")) > 0.005:
            raise SystemExit(f'{code} 档案研究数 {research} 与 research/{code}.json 折算值不一致，先重新登记')
        model = rr.compute(spec)['model_yi']
        gap = max(research, model) / min(research, model) - 1
        band = dict(bands[code])
        approx = bool((band.get('exright_note') or '').strip())
        band['exright_note'] = ''
        dossier = {name_: row[i] for name_, i in col.items()}
        res = apply_research_overlay(band, dossier)
        rev = reviews[code]
        price, iv = float(rev['price']), float(bands[code]['intrinsic_value'])
        research_part = ''
        if not isinstance(res, str):
            research_part = (f"研究口径 V {res[1]:.2f}、`P/V` {price / res[1]:.3f}" + ('（未计除权归一化，近似）' if approx else '') + '，')
        note = (f"{conclusion}（用户 {args.day} 裁定，OI-291 池内独立审计 {args.review_batch}，§7.3 差距复核）：研究数 {research:.2f} 亿，"
                f"模型锚 {model:.2f} 亿，差距 {gap:.1%}；{research_part}生产带 V {iv:.2f}、`P/V` {price / iv:.3f}"
                f"（{rev['price_date']} 收盘 {price:.2f}）；独立评审 `{rev['review_id']}`：独立 V {float(rev['v_base']):.2f}、`P/V` {float(rev['pv']):.3f}。"
                f"{item['reason']}")
        print(f"{code} {name}：{note}")
        for key, value in dict(divergence_reviewed_at=args.day, divergence_review_conclusion=conclusion, divergence_review_note=note,
                               divergence_reviewed_model_yi=f"{model:.2f}", divergence_reviewed_research_yi=f"{research:.2f}").items():
            row[col[key]] = value
        decision_id = f"valuation_review:{args.day}:{code}:oi291_divergence_review"
        registered = f"valuation_review:{spec['evidence_date']}:{code}:oi291_research_registered"
        if decision_id not in seen:
            log_rows.append(dict(
                logged_at_utc=datetime.now(timezone.utc).isoformat(), workflow_stage='valuation_review', run_id=f'oi291:{args.day}',
                as_of=args.day, security_code=code, security_name=name, decision_type='research_model_divergence_review',
                decision_result=conclusion, summary_reason=note,
                input_files=f"user_confirmation;{args.rulings.relative_to(ROOT) if args.rulings.is_absolute() else args.rulings}",
                source_urls='', output_file='data/processed/a_share_valuation_dossiers.csv',
                operator_or_script='exp_independent_pool_2026q3/tools/apply_rulings.py', workflow_version=WORKFLOW_VERSION,
                decision_id=decision_id, supersedes_decision_id=registered if registered in seen else ''))
    if args.dry_run:
        return
    rr.DOSSIERS.write_bytes(rr.dump(docs, nl))
    append_decision_log(rr.LOG, log_rows)
    print(f'档案已写差距复核结论；决策日志追加 {len(log_rows)} 行')


if __name__ == '__main__':
    main()
