"""第一批修正落地（用户 2026-10-06 裁定原则采纳）共用路径与参数：OI-260 派息率、OI-264 税率异常、OI-262 普通股权益推股数与重述前 BPS、
OI-262／OI-261 分红时点与期后除息补扣；回测引擎 OI-243 单票上限分母在第二段（run.py）。

各臂同一代码，只差建带开关（缺省＝改前口径）：
- CONTROL：不给新开关，须逐字节复现现行七份正式状态（v4.230 安装产物）；
- P260 `--payout-basis fiscal`、T264 `--tax-anomaly median3`、S262 `--share-equity common`、D262 `--dividend-timing post_period`：各单开一项；
- ALL：四项全开（拟安装口径）。
建带用 v4.230 生产建带时的公司行动与除权价格参数（`exp_oi257_land_20261005/old_inputs/`，与 OI-257 落地 NEW 臂相同），
银行保险覆盖与持仓侧合成用现行文件。
"""
import csv
import hashlib
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
PROC = ROOT / 'data/processed'
OLD = ROOT / 'data/experiments/exp_oi257_land_20261005/old_inputs'
FROZEN_ACTIONS = OLD / 'a_share_corporate_actions.csv'
FROZEN_TERMS = OLD / 'a_share_exright_terms.csv'
NEW_FLAGS = {
    'CONTROL': [],
    'P260': ['--payout-basis', 'fiscal'],
    'T264': ['--tax-anomaly', 'median3'],
    'S262': ['--share-equity', 'common'],
    'D262': ['--dividend-timing', 'post_period'],
    'ALL': ['--payout-basis', 'fiscal', '--tax-anomaly', 'median3', '--share-equity', 'common', '--dividend-timing', 'post_period'],
}
ARMS = tuple(NEW_FLAGS)
STATE_FILES = ('roic_bands.csv', 'roic_bands_b2.csv', 'roic_daily_raw.csv', 'roic_daily_raw_b2.csv',
               'a_share_daily_states_adopted.csv', 'a_share_daily_states_b2.csv', 'a_share_daily_states_hold.csv')
# §6.7 第 2 步建带命令（v4.231 生产口径，与 scripts/slurm/rebuild_chain_with_fetch.sbatch 的 COMMON 相同）
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
REGISTERED_SHARE_PCT = 16.916          # v4.224 在册合格面（§12.295；v4.230 容差内保留未改写）


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
