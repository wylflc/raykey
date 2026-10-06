"""盐湖股份研究正常化盈利（用户 2026-10-06 裁定：随第一批 OI-264 只纠负税率安装，按 OI-259 审查长期价格基准登记研究数）。

OI-264 只纠负税率后，2025 年按 12% 补税使当期比率下降、谷底守卫权重 0.85 → 1，锚混向含 2021–22 年景气高点的五年中位，V 不降反升
（OI-266 的问题）。商品价格接受者的研究数按 §6.5.2.2 取概率加权长期价格：审查基准合并 NOPAT 91.6 亿（氯化钾 2,830 元／吨、碳酸锂 9.5 万元／吨，
含税；悲观 55.9、乐观 142.1 亿），加 2025 年报研发资本化加回（模型同口径）。差距超过 30% 按 §7.3 入队并冻结新增买入。

    python3 register_salt_lake.py [--dry-run]
"""
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import roic_inputs  # noqa: E402
from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log  # noqa: E402

CODE, NAME, DAY = '000792', '盐湖股份', '2026-10-06'
AUDIT = 'data/experiments/exp_oi259_lowpv_20261005/companies/000792_盐湖股份.json'
BEAR, BASE, BULL = 55.9, 91.6, 142.1          # 审查合并 NOPAT（亿元，长期价格悲观／基准／乐观）
DOSSIERS = ROOT / 'data/processed/a_share_valuation_dossiers.csv'
BANDS = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'


def main(dry_run: bool) -> None:
    years = roic_inputs.load_statements({CODE}, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc', tax_anomaly='median3')[CODE]
    rd = roic_inputs.load_rd_expense({CODE}).get(CODE, {})
    csrc = {r['security_code']: r['csrc_industry'] for r in csv.DictReader(open(ROOT / 'data/reference/a_share_csrc_industry.csv', encoding='utf-8'))}
    raw = years['2025-12-31']
    capped = roic_inputs.capitalize_rd(years, rd, roic_inputs.rd_life(csrc.get(CODE)))
    addback = ((capped[0]['2025-12-31'].nopat if capped else raw.nopat) - raw.nopat) / 1e8
    research, lo, hi = (round(v + addback, 2) for v in (BASE, BEAR, BULL))
    band = next(r for r in csv.DictReader(BANDS.open(encoding='utf-8-sig')) if r['security_code'] == CODE)
    model = float(band['nopat_ps']) * float(band['shares_est']) / 1e8
    gap = max(model, research) / min(model, research) - 1
    print(f'{NAME} 研究 {research:.2f} 亿（研发加回 {addback:+.2f}）模型锚 {model:.2f} 亿 差距 {gap:.1%}')
    if dry_run:
        return
    rows = list(csv.DictReader(DOSSIERS.open(encoding='utf-8-sig')))
    fields = list(rows[0].keys())
    falsifier = ('2027 年碳酸锂均价 < 8 万元／吨且国内氯化钾 < 2,600 元／吨（悲观档成立）；2027 年氯化钾 ≥ 3,200 元／吨且碳酸锂 ≥ 12 万元／吨（含税，乐观档成立）；'
                 f'连续两个年报模型口径 NOPAT 落在 {lo:.2f}～{hi:.2f} 亿之外')
    source = (f'OI-259 低 P/V 审查（{AUDIT}）：商品价格接受者按 §6.5.2.2 取概率加权长期价格，合并 NOPAT 基准 {BASE:g} 亿（氯化钾 2,830 元／吨、碳酸锂 9.5 万元／吨，'
              f'含税；钾 500 万吨、锂 9.3 万吨；所得税 15%），加 2025 年报研发资本化加回 {addback:+.2f} 亿 = {research:.2f} 亿（用户 {DAY} 裁定登记，OI-264／OI-266）')
    for r in rows:
        if r['security_code'] == CODE:
            r.update(research_nopat_yi=f'{research:.2f}', research_evidence_date='2026-09-30', research_falsifier=falsifier, research_source=source)
    with DOSSIERS.open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
    append_decision_log(DEFAULT_DECISION_LOG, [dict(
        logged_at_utc=datetime.now(timezone.utc).isoformat(), workflow_stage='valuation_review', run_id=f'oi264_research:{DAY}', as_of=DAY,
        security_code=CODE, security_name=NAME, decision_type='research_normalized_earnings', decision_result='registered',
        summary_reason=(f'OI-264 只纠负税率后谷底守卫使锚混向含 2021–22 年景气高点的五年中位、V 不降反升（OI-266），用户 {DAY} 裁定按 OI-259 审查长期价格基准登记研究正常化盈利 '
                        f'{research:.2f} 亿（区间 {lo:.2f}～{hi:.2f}），模型锚 {model:.2f} 亿，差距 {gap:.1%}'
                        + ('，> 30% 按 §7.3 入队；模型锚较高，冻结新增买入至复核结论。' if gap > 0.30 else '。') + f'可证伪：{falsifier}'),
        input_files=f'user_confirmation;{AUDIT}', output_file='data/processed/a_share_valuation_dossiers.csv', operator_or_script='Claude',
        workflow_version=WORKFLOW_VERSION, decision_id=f'valuation_review:{DAY}:{CODE}:research_registered')])
    print('registered', WORKFLOW_VERSION)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--dry-run', action='store_true')
    main(ap.parse_args().dry_run)
