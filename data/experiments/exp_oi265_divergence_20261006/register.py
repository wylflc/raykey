"""§7.3 研究与模型差距复核（OI-265 登记研究数后入队冻结的 7 只）：用户 2026-10-06 裁定均采用研究数（g0 照带）并解冻。

逐只读生产池带（信号日 2026-09-30）与队列的两数，按 §6.5.2.2 算采用研究数后的 V（泸州老窖池带已除权归一化：按原始带套用后减同额
归一化差），写 `review.json`、档案复核字段与决策日志（复核行接 OI-265 研究数登记行）；之后按 §7.3 当晚以同一信号日生效：
§6.7 第 4～6 步后重跑 09-30 扫描并重新发布。

    python3 register.py [--dry-run]
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_forecast_band_overlay as ov  # noqa: E402
from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log  # noqa: E402

DAY = '2026-10-06'
RUN_ID = f'oi209_divergence_review:{DAY}'
DOSSIERS = ROOT / 'data/processed/a_share_valuation_dossiers.csv'
POOL = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
RAW = ROOT / 'data/processed/roic_bands.csv'
QUEUE = ROOT / 'data/interim/a_share_report_update_queue.csv'
QUOTES = ROOT / 'data/processed/daily_buy_candidates.csv'
AUDIT = ROOT / 'data/experiments/exp_oi259_lowpv_20261005/summary_table.json'
# 模型锚偏高的来历（OI-259 审查拆解，`exp_oi259_lowpv_20261005/decomposition.md`）
WHY = {
    '000786': '锚取 2023–24 年比率（λ=0 三年中位）× 经营账面、谷底守卫 v=0.79，比 TTM NOPAT 高 74%；竣工面积仍在下滑',
    '600970': '锚取 λ=0 中位比率 × 账面，高于 2024–25 年与 TTM 归母（29.8／28.6／23.7 亿）',
    '603279': '谷底守卫回归中位，锚 11.3 亿对 2024／2025／TTM 归母 8.5／5.2／4.1 亿',
    '000568': 'λ=0 中位锚、谷底守卫 v=0.75，锚 129.6 亿对 TTM 归母 75.1 亿',
    '603369': '三年中位锚 36.2 亿对 2025／TTM 归母 26.0／24.6 亿',
    '000596': '谷底守卫回归中位，锚 45.6 亿对 2025／TTM 归母 35.5／20.5 亿',
    '000792': '补税后谷底守卫使锚混向含 2021–22 年景气高点的五年中位（OI-264、OI-266），研究数按审查长期价格',
}


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def research_v(band: dict, dossier: dict) -> float:
    res = ov.apply_research_overlay(dict(band), {'research_nopat_yi': dossier['research_nopat_yi'], 'divergence_reviewed_at': DAY})
    if isinstance(res, tuple):
        return res[1]
    raw = next(r for r in read(RAW) if r['security_code'] == band['security_code'] and r['report_date'] == band['report_date']
               and r['available_at'] == band['available_at'])
    res = ov.apply_research_overlay(dict(raw), {'research_nopat_yi': dossier['research_nopat_yi'], 'divergence_reviewed_at': DAY})
    return res[1] - (float(raw['intrinsic_value']) - float(band['intrinsic_value']))


def main(dry_run: bool) -> None:
    pool = {r['security_code']: r for r in read(POOL)}
    queue = {r['security_code']: r for r in read(QUEUE)}
    quotes = {r['security_code']: r for r in read(QUOTES)}
    audit = {r['code']: r for r in json.loads(AUDIT.read_text(encoding='utf-8'))}
    dossiers = read(DOSSIERS)
    by_code = {r['security_code']: r for r in dossiers}
    review = []
    for code in WHY:
        band, dossier, q = pool[code], by_code[code], queue[code]
        assert q['queue_reasons'] == 'research_model_divergence' and not dossier['divergence_reviewed_at'], code
        close = float(quotes[code]['close'])
        v0, v1 = float(band['intrinsic_value']), research_v(band, dossier)
        a = audit[code]
        review.append(dict(code=code, name=band['security_name'], close=close, model_yi=float(q['model_nopat_yi']),
                           research_yi=float(q['research_nopat_yi']), gap=float(q['research_model_gap']), model_V=round(v0, 2),
                           research_V=round(v1, 2), model_pv=round(close / v0, 3), research_pv=round(close / v1, 3),
                           independent_pv=a['indep_base'], independent_range=[a['indep_bull'], a['indep_bear']], why=WHY[code]))
    (EXP / 'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    notes = {r['code']: (f"采用研究数（用户 {DAY} 裁定，§7.3 差距复核，OI-265 登记后入队冻结）：研究数 {r['research_yi']:.2f} 亿，模型锚 {r['model_yi']:.2f} 亿，"
                         f"差距 {r['gap']:.1%}——{r['why']}；V {r['model_V']:.2f}→{r['research_V']:.2f}，`P/V` {r['model_pv']:.3f}→{r['research_pv']:.3f}"
                         f"（09-30 收盘 {r['close']:.2f}），OI-259 独立基准 `P/V` {r['independent_pv']}（{r['independent_range'][0]}～{r['independent_range'][1]}）。"
                         f"g0 照带，不登记研究增长。") for r in review}
    for r in review:
        print(r['code'], r['name'], f"P/V {r['model_pv']}→{r['research_pv']}（独立 {r['independent_pv']}）")
    if dry_run:
        return
    for r in review:
        by_code[r['code']].update(divergence_reviewed_at=DAY, divergence_review_conclusion='采用研究数', divergence_review_note=notes[r['code']],
                                  divergence_reviewed_model_yi=f"{r['model_yi']:.2f}", divergence_reviewed_research_yi=f"{r['research_yi']:.2f}")
    tmp = DOSSIERS.with_name('.' + DOSSIERS.name + '.tmp')
    with tmp.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(dossiers[0].keys()))
        writer.writeheader()
        writer.writerows(dossiers)
    tmp.replace(DOSSIERS)
    now = datetime.now(timezone.utc).isoformat()
    append_decision_log(DEFAULT_DECISION_LOG, [dict(
        logged_at_utc=now, workflow_stage='valuation_review', run_id=RUN_ID, as_of=DAY, security_code=r['code'], security_name=r['name'],
        decision_type='research_model_divergence_review', decision_result='采用研究数', summary_reason=notes[r['code']],
        input_files='user_confirmation;data/experiments/exp_oi265_divergence_20261006/review.json', source_urls='',
        output_file='data/processed/a_share_valuation_dossiers.csv', operator_or_script='exp_oi265_divergence_20261006/register.py',
        workflow_version=WORKFLOW_VERSION, decision_id=f"valuation_review:{DAY}:{r['code']}:divergence_review",
        supersedes_decision_id=f"valuation_review:{DAY}:{r['code']}:research_registered") for r in review])
    print('registered', len(review), 'divergence reviews', WORKFLOW_VERSION)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    main(ap.parse_args().dry_run)
