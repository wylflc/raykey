"""第二批修正落地（用户 2026-10-06 裁定原则采纳）共用路径与参数：OI-261 附注类债务、融资项、税后弃置义务与弃置专户（`--note-debt notes`），
OI-263 受限资产附注新版式（`fetch_restricted_cash_items.py --parser v2` 生成的表）。

各臂同一代码与 v4.232 生产命令（第一批四项开关全开），只差：
- CONTROL：v4.232 生产口径，须逐字节复现安装后的七份正式状态；
- N261：加 `--note-debt notes`，附注类债务与弃置专户表取 `inputs/`；
- R263：受限资产表换 v2；
- ALL2：两项都换（拟安装口径）。
建带用与第一批相同的冻结公司行动与除权价格参数（`exp_oi257_land_20261005/old_inputs/`）。
"""
import importlib.util
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
_spec = importlib.util.spec_from_file_location('batch1_common', ROOT / 'data/experiments/exp_oi260_264_land_20261006/common.py')
_b1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b1)
B2, BUY_LINE, FROZEN_ACTIONS, FROZEN_TERMS, PROC = _b1.B2, _b1.BUY_LINE, _b1.FROZEN_ACTIONS, _b1.FROZEN_TERMS, _b1.PROC
PRODUCTION, REGISTERED_SHARE_PCT, SIGNAL_DATE, STATE_FILES = _b1.PRODUCTION, _b1.REGISTERED_SHARE_PCT, _b1.SIGNAL_DATE, _b1.STATE_FILES
digest, load, read = _b1.digest, _b1.load, _b1.read
BATCH1 = _b1.NEW_FLAGS['ALL']


def save(name: str, value) -> None:
    import json
    (EXP / name).write_text(json.dumps(value, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')


def load(name: str):  # noqa: F811 —— 本目录的 load
    import json
    return json.loads((EXP / name).read_text(encoding='utf-8'))
INPUTS = EXP / 'inputs'
DEBT, FUND = INPUTS / 'debt_note_items.csv', INPUTS / 'decom_fund_items.csv'
RESTRICTED_V1, RESTRICTED_V2 = ROOT / 'data/reference/restricted_cash_items.csv', INPUTS / 'restricted_cash_items_v2.csv'
ARMS = {
    'CONTROL': dict(flags=[], restricted=RESTRICTED_V1),
    'N261': dict(flags=['--note-debt', 'notes'], restricted=RESTRICTED_V1),
    'R263': dict(flags=[], restricted=RESTRICTED_V2),
    'ALL2': dict(flags=['--note-debt', 'notes'], restricted=RESTRICTED_V2),
}
