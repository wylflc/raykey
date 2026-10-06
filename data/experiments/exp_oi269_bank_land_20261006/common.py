"""OI-269 银行 BV 年增速封顶 7% 的落地实验（用户 2026-10-06 裁定 B 走落地，R、K 不采纳）共用参数。

§6.7 第 3 步银行保险覆盖两臂：CONTROL `h2:0.02:0.10`（现行，须逐字节复现正式逐日状态）、NEW `h2:0.02:0.10:1:bv7`（银行 V_DDM 路径
BV 年增速 ≤ 7%，保险不封顶）。输入为现行正式的建带产物（候选侧与 B2 两侧的 roic_bands 与 roic_daily_raw），持仓侧按 §6.7 合成。
"""
import hashlib
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
PROC = ROOT / 'data/processed'
ARMS = {'CONTROL': 'h2:0.02:0.10', 'NEW': 'h2:0.02:0.10:1:bv7'}
SIDES = {'adopted': ('roic_daily_raw.csv', 'roic_bands.csv', 'a_share_daily_states_adopted.csv'),
         'b2': ('roic_daily_raw_b2.csv', 'roic_bands_b2.csv', 'a_share_daily_states_b2.csv')}
STATE_FILES = ('a_share_daily_states_adopted.csv', 'a_share_daily_states_b2.csv', 'a_share_daily_states_hold.csv')
SIGNAL_DATE, BUY_LINE, REGISTERED_SHARE_PCT = '2026-09-30', 1.0034, 16.916


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(name, value):
    (EXP / name).write_text(json.dumps(value, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')


def load(name):
    return json.loads((EXP / name).read_text(encoding='utf-8'))
