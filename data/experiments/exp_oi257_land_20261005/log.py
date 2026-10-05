"""决策日志：OI-257 落地行（v4.230，须在重发扫描之前写入）。"""
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_decision_log import append_decision_log, DEFAULT_DECISION_LOG, WORKFLOW_VERSION  # noqa: E402

ROWS = [
    ('OI-257-20261005-land', 'mechanism_repair', 'valuation_caliber', 'adopted',
     'OI-257（v4.230）落地：§6.5.1 第 3 条——受限资产表货币资金类行原因笼统时改读货币资金附注与「现金和现金等价物」附注的受限分项，'
     '票据、信用证、保函保证金按 OI-219 计入（格力 2016–2025 年借款质押保证金余额按筹资活动累计人工核定、先减）；财务公司法定存款准备金'
     '不计超额现金、不进营运资金、利息回 EBIT；抽取范围另加有财务公司迹象的年报。全池抽取：受限分项补计 171 行（59 家）1,821.6 亿，'
     '准备金 107 行（12 家）1,606.7 亿。两臂重建（作业 27608743）：CONTROL 逐字节复现七份正式状态；信号日 09-30 池内 29 只 V 变化'
     '（格力 74.86→73.72、P/V 0.511→0.519；茅台 −2.0%；伊利 +6.9%，因准备金入投入资本使 2020→2025 年 ΔIC 由非正转为微正、资本腿 g0 0→4.75%），'
     '买入区 28 只无进出、无法估值名单不变。原线合格面 16.903%（在册 16.916%），容差内保留 1.0034、在册合格面不改写。'
     'BASE 14 起点（参考）未见劣化：主读数全／A／U +0.21／+0.11／+0.11，复利 +0.16／+0.38／+0.38，BASE 按 NEW 重登。',
     'data/experiments/exp_oi257_20261005/000651_restricted_cash.md;data/experiments/exp_oi257_land_20261005/inputs_summary.json;'
     'data/experiments/exp_oi257_land_20261005/current_changes.md;data/experiments/exp_oi257_land_20261005/align.txt;'
     'data/experiments/exp_oi257_land_20261005/readings.md'),
]


def main():
    done = {r['run_id'] for r in csv.DictReader(open(DEFAULT_DECISION_LOG, encoding='utf-8'))}
    rows = [dict(logged_at_utc=datetime.now(timezone.utc).isoformat(), workflow_stage=stage, run_id=run_id, as_of='2026-09-30',
                 security_code='ALL', decision_type=kind, decision_result=result, summary_reason=reason, input_files=inputs,
                 output_file='data/experiments/exp_oi257_land_20261005/publication.json', operator_or_script='exp_oi257_land_20261005/log.py',
                 workflow_version=WORKFLOW_VERSION, supersedes_decision_id='workflow_rule:2026-10-05:ALL:oi257_adopted')
            for run_id, stage, kind, result, reason, inputs in ROWS if run_id not in done]
    if rows:
        append_decision_log(DEFAULT_DECISION_LOG, rows)
    print('decision log rows appended', len(rows), WORKFLOW_VERSION)


if __name__ == '__main__':
    main()
