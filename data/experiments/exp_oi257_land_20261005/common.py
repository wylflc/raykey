"""OI-257 落地（v4.230）共用路径与参数：受限现金附注受限分项与财务公司法定存款准备金。

两臂同一代码（v4.230 `roic_inputs` 与抽取脚本），只换受限资产表：
- CONTROL：v4.229 生产表（冻结副本，无 `fallback_yuan`／`reserve_yuan` 列），须逐行复现现行七份逐日状态；
- NEW：v4.230 抽取（`inputs.py` 生成）。
建带用 2026-09-28 生产建带时的公司行动与除权价格参数（git 681eedb1／1b90aab3，其后只改了 09-29、09-30 的少数行），
银行保险覆盖与持仓侧合成用现行文件（与 v4.225 安装时相同）。
"""
import csv
import hashlib
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
PROC = ROOT / 'data/processed'
ARMS = ('CONTROL', 'NEW')
RESTRICTED = {'CONTROL': EXP / 'inputs/restricted_cash_items_v4229.csv', 'NEW': EXP / 'inputs/restricted_cash_items.csv'}
FROZEN_ACTIONS = EXP / 'old_inputs/a_share_corporate_actions.csv'
FROZEN_TERMS = EXP / 'old_inputs/a_share_exright_terms.csv'
STATE_FILES = ('roic_bands.csv', 'roic_bands_b2.csv', 'roic_daily_raw.csv', 'roic_daily_raw_b2.csv',
               'a_share_daily_states_adopted.csv', 'a_share_daily_states_b2.csv', 'a_share_daily_states_hold.csv')
# §6.7 第 2 步建带命令（v4.229 生产口径，与 scripts/slurm/rebuild_chain_with_fetch.sbatch 的 COMMON 相同）
PRODUCTION = ['--all', '--value-model', 'roic', '--roe-source', 'onesided_max', '--roe-lift', '2.0', '--uniform-tier', 'L2',
              '--since', '2002-01-01', '--roic-nopat-source', 'conditional3', '--roic-growth', 'hybrid',
              '--roic-cycle-guard', 'peak', '--roic-cond-detect', 'graded', '--roic-peak-ramp', '0.3',
              '--ttm-current', 'on', '--growth-damp', 'on', '--thin-equity-max', '0.5', '--roic-trail-weight', '0',
              '--minority-basis', 'earnings', '--wc-aggregation', 'operating', '--cash-caliber', 'nonop',
              '--equity-anchor', 'guarded', '--restricted-cash', 'notes_wc', '--wacc-weights', 'unlevered',
              '--reset-guard', 'both', '--rd-capitalize', 'on', '--fade-shape', 'exponential', '--fade-lambda', '0.12',
              '--fade-horizon', '50', '--roic-ic-floor', '0.1']
B2 = ['--ttm-trust', 'on', '--ttm-trust-delta', '0.02']
SIGNAL_DATE = '2026-09-30'
BUY_LINE = 1.0034
REGISTERED_SHARE_PCT = 16.916          # v4.224 在册合格面（§12.295）


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 24), b''):
            h.update(block)
    return h.hexdigest()


def save(name: str, value) -> None:
    (EXP / name).write_text(json.dumps(value, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')


def load(name: str):
    return json.loads((EXP / name).read_text(encoding='utf-8'))


def read(path: Path) -> list[dict]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))
