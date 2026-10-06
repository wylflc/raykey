"""决策日志：第二批修正落地行（v4.233，须在重发扫描之前写入；已写的 run_id 不重写）。摘要由 readings.json／current_changes.json 与 user_ruling.json 生成。"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from workflow_decision_log import append_decision_log, DEFAULT_DECISION_LOG, WORKFLOW_VERSION  # noqa: E402

RUN_ID = 'OI-261-263-20261006-land'
REL = 'data/experiments/exp_oi261_263_land_20261006/'


def main():
    ruling = json.loads((EXP / 'user_ruling.json').read_text(encoding='utf-8'))
    done = {r['run_id'] for r in csv.DictReader(open(DEFAULT_DECISION_LOG, encoding='utf-8'))}
    if RUN_ID in done:
        print('decision log row exists', RUN_ID)
        return
    row = dict(logged_at_utc=datetime.now(timezone.utc).isoformat(), workflow_stage='mechanism_repair', run_id=RUN_ID, as_of='2026-09-30',
               security_code='ALL', decision_type='valuation_caliber', decision_result='adopted', summary_reason=ruling['summary'],
               input_files=';'.join(REL + n for n in ('build_check.json', 'current_changes.md', 'align.txt', 'readings.md', 'user_ruling.json',
                                                      'registration.json')) + ';data/experiments/exp_oi261_263_20261006/quantification.md',
               output_file=REL + 'publication.json', operator_or_script='exp_oi261_263_land_20261006/log.py',
               workflow_version=WORKFLOW_VERSION, supersedes_decision_id='workflow_rule:2026-10-06:ALL:batch2_ruled')
    append_decision_log(DEFAULT_DECISION_LOG, [row])
    print('decision log rows appended 1', WORKFLOW_VERSION)


if __name__ == '__main__':
    main()
