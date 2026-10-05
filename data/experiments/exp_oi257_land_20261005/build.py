"""CONTROL／NEW 两臂全市场重建（§6.7 第 2、2b、3 步与持仓侧合成），产物写 `states/<臂>/`。

    python3 build.py                      # 编排：四个建带进程并行 → 银行保险覆盖 → 持仓侧逐日状态
    python3 build.py <ARM> <side> bands   # 单个建带进程（side = base | b2）
    python3 build.py <ARM> <side> bank    # 该臂该侧的银行保险股利折现覆盖（§6.7 第 3 步，h2:0.02:0.10）
"""
import os
import runpy
import subprocess
import sys
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import ARMS, B2, EXP, FROZEN_ACTIONS, FROZEN_TERMS, PRODUCTION, RESTRICTED, ROOT

sys.path.insert(0, str(ROOT / 'scripts'))


def folder(arm: str) -> Path:
    path = EXP / 'states' / arm
    path.mkdir(parents=True, exist_ok=True)
    return path


def child(arm: str, side: str, task: str) -> None:
    suffix = '_b2' if side == 'b2' else ''
    out = folder(arm)
    raw, bands = out / f'roic_daily_raw{suffix}.csv', out / f'roic_bands{suffix}.csv'
    if task == 'bands':
        import corporate_actions
        import roic_inputs
        roic_inputs.RESTRICTED_CASH_FILE = RESTRICTED[arm]
        corporate_actions.PRICE_TERMS_PATH = FROZEN_TERMS          # 2026-09-28 生产建带时的除权价格参数
        path = ROOT / 'scripts/build_historical_valuation_bands.py'
        module = types.ModuleType('exp_build')
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), module.__dict__)
        module.ACTIONS = FROZEN_ACTIONS                              # 2026-09-28 生产建带时的公司行动
        module.STMT_GAP_LOG = out / f'gaps{suffix}.csv'
        sys.argv = ['build', *PRODUCTION, *(B2 if suffix else []), '--out-bands', str(bands), '--out-daily', str(raw)]
        raise SystemExit(module.main())
    if task == 'bank':                                               # 现行公司行动（与 v4.225 安装时相同）
        output = out / ('a_share_daily_states_b2.csv' if suffix else 'a_share_daily_states_adopted.csv')
        sys.argv = ['rebuild_bank_bands.py', 'h2:0.02:0.10', str(output), str(raw), str(bands)]
        runpy.run_path(str(ROOT / 'scripts/rebuild_bank_bands.py'), run_name='__main__')


def run(arm: str, side: str, task: str) -> str:
    log = EXP / f'build_{arm}_{side}_{task}.log'
    with log.open('w') as f:
        subprocess.run([sys.executable, __file__, arm, side, task], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True,
                       env=dict(os.environ, PYTHONUNBUFFERED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
    print('DONE', arm, side, task, flush=True)
    return log.name


def orchestrate() -> None:
    arms = [a for a in os.environ.get('EXP_ARMS', '+'.join(ARMS)).split('+') if a]
    jobs = [(a, s) for a in arms for s in ('base', 'b2')]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(lambda j: run(*j, 'bands'), jobs))
        list(pool.map(lambda j: run(*j, 'bank'), jobs))
    for arm in arms:
        out = folder(arm)
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_hold_daily_states.py'),
                        '--base', str(out / 'a_share_daily_states_adopted.csv'), '--b2', str(out / 'a_share_daily_states_b2.csv'),
                        '--out', str(out / 'a_share_daily_states_hold.csv')], cwd=ROOT, check=True)
        print('DONE', arm, 'hold', flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        child(*sys.argv[1:4])
    else:
        orchestrate()
