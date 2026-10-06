"""OI-270 全池量化共用参数：估值细项研究开关（缺省关）。

臂（候选侧、池成员，信号日 2026-09-30；其余参数为 v4.234 §6.7 第 2 步生产命令，建带用与第二批落地相同的冻结公司行动与除权价格参数）：
- CONTROL：生产口径，须逐行复现生产池带 `a_share_pool_model_bands_adopted.csv` 的 V；
- FX `--fx-in-ebit on`：财务费用中利息净额之外的部分（汇兑损益、手续费等）留在 EBIT；
- M0 `--minority-share floor0`：少数股东份额各年先夹到 ≥ 0 再取中位（亏损子公司的负少数损益不再拉低份额）；
- ML `--minority-share latest`：少数股东份额取最新年度（并购后不滞后）；
- RD5 `--rd-life uniform5`：研发摊销年限一律 5 年（不按证监会大类取 3／10 年）。
"""
import importlib.util
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
_spec = importlib.util.spec_from_file_location('batch2_common', ROOT / 'data/experiments/exp_oi261_263_land_20261006/common.py')
_b2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b2)
FROZEN_ACTIONS, FROZEN_TERMS, PRODUCTION, BATCH1, SIGNAL_DATE, BUY_LINE = (_b2.FROZEN_ACTIONS, _b2.FROZEN_TERMS, _b2.PRODUCTION, _b2.BATCH1,
                                                                         _b2.SIGNAL_DATE, _b2.BUY_LINE)
V4233 = [*BATCH1, '--note-debt', 'notes']
ARMS = {'CONTROL': [], 'FX': ['--fx-in-ebit', 'on'], 'M0': ['--minority-share', 'floor0'], 'ML': ['--minority-share', 'latest'],
        'RD5': ['--rd-life', 'uniform5']}
POOL_BANDS = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
QUOTES = ROOT / 'data/processed/daily_buy_candidates.csv'
