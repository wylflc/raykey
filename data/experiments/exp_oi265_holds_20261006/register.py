"""§7.5 临时冻结 8 只逐只复核结束（用户 2026-10-06 裁定：8 只均采用研究数、g0 照带不登记研究增长，并解除临时冻结）。

依据 `review.json`（v4.233 生产池带，信号日 2026-09-30）。写档案复核字段（§7.3：结论、复核日、复核时两数与理由）、临时冻结名单
`released_at`（行不删）与决策日志（复核结论行接 OI-265 研究数登记行，解除行接冻结修订行）。写完按 §7.3 当晚以同一信号日生效：
§6.7 第 4～6 步（`scripts/slurm/refresh_pool_from_bands.sbatch`）后重跑 09-30 扫描并重新发布。

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
from workflow_decision_log import DEFAULT_DECISION_LOG, WORKFLOW_VERSION, append_decision_log  # noqa: E402

DOSSIERS = ROOT / 'data/processed/a_share_valuation_dossiers.csv'
HOLDS = ROOT / 'data/reference/review_holds.csv'
DAY = '2026-10-06'
RUN_ID = f'oi265_hold_review:{DAY}'
# 逐只的偏差来源与裁定说明（数值取 review.json）
NOTES = {
    '603855': '股权桥分红时点已随 v4.232 修正（V 17.27→16.27）；差距超过 30%，按 §7.3 结论采用研究数后不再冻结',
    '600938': 'v4.233 弃置义务税后计入股权桥（模型 V 40.12→36.35）；g0 6.65% 照带（2021 年起点是油价恢复，窗口内无结构性变化）',
    '002001': 'g0 10.46% 照带（毛利率随维生素周期波动，窗口内无结构性变化）',
    '300910': 'g0 17.70% 照带：2021 年起点在毛利率下探期，起点移到 2022 年为 7.00%（P/V 1.235），但 2021–22 年是下探后恢复、不是台阶，'
              '不登记研究增长；用户未取「冻结延至 2026 年报」，OI-252 检验未支持改 g0；2026 年报入带后窗口起点移出 2021 年、预计 V 下调，'
              '届时按 §7.3 新年报重新入队',
    '600809': 'g0 2.82% 照带（再投资率 7%，增长腿小），偏差主要在下行期锚',
    '002920': 'g0 18.57% 照带（2015 年以来各起点增量 ROIC × 再投资率都在 16–22%）；研发加回外推未获 OI-267 检验支持削减；'
              '独立基准分歧记为风险',
    '002594': 'g0 20.09% 照带：2021 年起点在毛利率下探期，起点移到 2022 年为 12.62%（P/V 1.009），但 2021 年是下探后恢复、不是台阶，'
              '不登记研究增长；用户未取「冻结延至 2026 年报」，OI-252、OI-267 检验未支持改 g0 与研发加回；2026 年报入带后研发摊销追上、'
              '窗口起点移出 2021 年，预计 V 下调，届时按 §7.3 新年报重新入队',
    '920599': 'g0 14.56% 照带（各起点 15–16%，无结构性变化）；三种口径都在买入区内',
}


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def write(path, rows):
    tmp = path.with_name('.' + path.name + '.tmp')
    with tmp.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def main(dry_run: bool) -> None:
    review = {r['code']: r for r in json.loads((EXP / 'review.json').read_text(encoding='utf-8'))['rows']}
    assert set(review) == set(NOTES), set(review) ^ set(NOTES)
    dossiers, holds = read(DOSSIERS), read(HOLDS)
    notes = {}
    for code, r in review.items():
        notes[code] = (f"采用研究数（用户 {DAY} 裁定，OI-265 §7.5 临时冻结逐只复核）：研究数 {r['research_yi']:.2f} 亿（OI-259 审查基准档，OI-265 已登记），"
                       f"模型锚 {r['model_yi']:.2f} 亿，差距 {r['gap']:.1%}；V {r['model_V']:.2f}→{r['research_V']:.2f}，`P/V` {r['model_pv']:.3f}→{r['research_pv']:.3f}"
                       f"（09-30 收盘 {r['close']:.2f}）；独立基准 V {r['independent_V']}（`P/V` {r['independent_pv']}）。{NOTES[code]}。解除 §7.5 临时冻结。")
        print(code, r['name'], notes[code][:120])
    if dry_run:
        return
    for row in dossiers:
        code = row['security_code']
        if code in review:
            r = review[code]
            assert abs(float(row['research_nopat_yi']) - r['research_yi']) < 0.005 and not row['divergence_reviewed_at'], code
            row.update(divergence_reviewed_at=DAY, divergence_review_conclusion='采用研究数', divergence_review_note=notes[code],
                       divergence_reviewed_model_yi=f"{r['model_yi']:.2f}", divergence_reviewed_research_yi=f"{r['research_yi']:.2f}")
    for row in holds:
        if row['security_code'] in review:
            assert not row['released_at'], row['security_code']
            row['released_at'] = DAY
    write(DOSSIERS, dossiers)
    write(HOLDS, holds)
    now = datetime.now(timezone.utc).isoformat()
    log = []
    for code, r in review.items():
        common = dict(logged_at_utc=now, workflow_stage='valuation_review', run_id=RUN_ID, as_of=DAY, security_code=code, security_name=r['name'],
                      source_urls='', operator_or_script='exp_oi265_holds_20261006/register.py', workflow_version=WORKFLOW_VERSION)
        log.append(dict(common, decision_type='research_model_divergence_review', decision_result='采用研究数', summary_reason=notes[code],
                        input_files='user_confirmation;data/experiments/exp_oi265_holds_20261006/review.json',
                        output_file='data/processed/a_share_valuation_dossiers.csv', decision_id=f'valuation_review:{DAY}:{code}:hold_review',
                        supersedes_decision_id=f'valuation_review:{DAY}:{code}:research_registered'))
        log.append(dict(common, decision_type='user_review_hold', decision_result='released',
                        summary_reason=f'§7.5 临时冻结解除：逐只复核结束，采用研究数（用户 {DAY} 裁定）',
                        input_files='user_confirmation;data/experiments/exp_oi265_holds_20261006/review.json', output_file='data/reference/review_holds.csv',
                        decision_id=f'valuation_review:{DAY}:{code}:user_review_hold_released',
                        supersedes_decision_id=f'valuation_review:{DAY}:{code}:user_review_hold_amended'))
    append_decision_log(DEFAULT_DECISION_LOG, log)
    print('registered', len(review), 'reviews;', len(log), 'decision log rows', WORKFLOW_VERSION)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    main(ap.parse_args().dry_run)
