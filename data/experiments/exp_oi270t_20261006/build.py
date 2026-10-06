"""OI-270 检验各臂全市场候选侧建带（v4.234 §6.7 第 2 步生产命令 + 研究开关），产物写 `states/<臂>/`（只建 base 侧，ROIC 路径检验不需要银行覆盖）。

    python3 build.py                  # 编排：各臂并行（EXP_ARMS=A+B 只跑部分臂）
    python3 build.py <ARM>            # 单个建带进程
建带用与第二批落地相同的冻结公司行动与除权价格参数（`exp_oi257_land_20261005/old_inputs/`），C 须逐字节复现生产候选侧带与逐日状态。
"""
import os
import subprocess
import sys
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data/experiments/exp_oi260_264_land_20261006'))
from common import FROZEN_ACTIONS, FROZEN_TERMS, NEW_FLAGS, PRODUCTION  # noqa: E402

BATCH1 = NEW_FLAGS['ALL'] + ['--note-debt', 'notes']   # v4.233 起生产口径（第一批四项 + 第二批附注类债务；受限资产 v2 表已是生产表）
ARMS = {
    'C': [],
    'FX': ['--fx-in-ebit', 'on'],
    'RD5': ['--rd-life', 'uniform5'],
    'FR': ['--fx-in-ebit', 'on', '--rd-life', 'uniform5'],
}


def child(arm: str) -> None:
    out = EXP / 'states' / arm
    out.mkdir(parents=True, exist_ok=True)
    import corporate_actions
    corporate_actions.PRICE_TERMS_PATH = FROZEN_TERMS
    path = ROOT / 'scripts/build_historical_valuation_bands.py'
    module = types.ModuleType('exp_build')
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), module.__dict__)
    module.ACTIONS = FROZEN_ACTIONS
    module.STMT_GAP_LOG = out / 'gaps.csv'
    sys.argv = ['build', *PRODUCTION, *BATCH1, *ARMS[arm], '--out-bands', str(out / 'roic_bands.csv'), '--out-daily', str(out / 'roic_daily_raw.csv')]
    raise SystemExit(module.main())


def run(arm: str) -> None:
    (EXP / 'states').mkdir(exist_ok=True)
    with (EXP / 'states' / f'build_{arm}.log').open('w') as f:
        subprocess.run([sys.executable, __file__, arm], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True,
                       env=dict(os.environ, PYTHONUNBUFFERED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
    print('DONE', arm, flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        child(sys.argv[1])
    else:
        arms = [a for a in os.environ.get('EXP_ARMS', '+'.join(ARMS)).split('+') if a]
        with ThreadPoolExecutor(max_workers=len(arms)) as pool:
            list(pool.map(run, arms))
