"""OI-271 全池量化共用参数：其他流动负债中的客户资金类项目（研究开关，缺省 off）。

臂（候选侧、池成员，信号日 2026-09-30；其余参数为 v4.233 §6.7 第 2 步生产命令，建带用与第二批落地相同的冻结公司行动与除权价格参数）：
- CONTROL：生产口径，须逐行复现生产池带 `a_share_pool_model_bands_adopted.csv` 的 V；
- C1 `--customer-float ocl`：其他流动负债附注中的客户资金类项目（预收与监管商品款项、销售返利／折让／应付退货、待转销项税、支付业务往来与
  待清算资金、未到期责任准备金）从超额现金扣除（同 OI-200 客户资金：现金与负债在投入资本中相抵）；
- C2 `--customer-float ocl_contract`：C1 再扣资产负债表合同负债与预收款项（客户预付全部不计超额现金）；
- W `--ocl-wc customer`：C1 的同一批项目只计入营运资金（投入资本按融资侧计、已含这些负债，只影响再投资率）。
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
ARMS = {'CONTROL': [], 'C1': ['--customer-float', 'ocl'], 'C2': ['--customer-float', 'ocl_contract'], 'W': ['--ocl-wc', 'customer']}
POOL_BANDS = ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv'
QUOTES = ROOT / 'data/processed/daily_buy_candidates.csv'
