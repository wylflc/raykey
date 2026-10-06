"""OI-271 各臂只建池成员的候选侧带（§6.7 第 2 步，`--codes`），再按 §6.7 第 4 步建信号日池带并叠加（预告／研究数／除权归一化）。

    python3 build.py                 # 编排：各臂并行建带 → 池带 → 叠加，写 arms/<臂>/
    python3 build.py <ARM> bands     # 单个建带进程
"""
import csv
import os
import subprocess
import sys
import types
from concurrent.futures import ThreadPoolExecutor

from common import ARMS, EXP, FROZEN_ACTIONS, FROZEN_TERMS, POOL_BANDS, PRODUCTION, ROOT, SIGNAL_DATE, V4233

sys.path.insert(0, str(ROOT / 'scripts'))


def codes() -> list[str]:
    pool = {r['security_code'].zfill(6) for r in csv.DictReader((ROOT / 'data/processed/a_share_core_valuation_pool.csv').open(encoding='utf-8-sig'))}
    pool |= {r['security_code'].zfill(6) for r in csv.DictReader(POOL_BANDS.open(encoding='utf-8-sig'))}
    return sorted(pool)


def folder(arm: str):
    path = EXP / 'arms' / arm
    path.mkdir(parents=True, exist_ok=True)
    return path


def child(arm: str) -> None:
    import corporate_actions
    corporate_actions.PRICE_TERMS_PATH = FROZEN_TERMS
    path = ROOT / 'scripts/build_historical_valuation_bands.py'
    module = types.ModuleType('exp_build')
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), module.__dict__)
    module.ACTIONS = FROZEN_ACTIONS
    out = folder(arm)
    module.STMT_GAP_LOG = out / 'gaps.csv'
    base = list(PRODUCTION)
    base[base.index('--all')] = '--codes'
    base.insert(base.index('--codes') + 1, ','.join(codes()))
    sys.argv = ['build', *base, *V4233, *ARMS[arm], '--out-bands', str(out / 'roic_bands.csv'), '--out-daily', str(out / 'roic_daily_raw.csv')]
    raise SystemExit(module.main())


def run(arm: str) -> str:
    out = folder(arm)
    with (out / 'build.log').open('w') as f:
        subprocess.run([sys.executable, __file__, arm, 'bands'], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True,
                       env=dict(os.environ, PYTHONUNBUFFERED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
    pool = out / 'pool_adopted.csv'
    subprocess.run([sys.executable, 'scripts/build_pool_model_bands.py', '--signal-date', SIGNAL_DATE, '--bands', str(out / 'roic_bands.csv'),
                    '--states', str(ROOT / 'data/processed/a_share_daily_states_adopted.csv'), '--out', str(pool)],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, 'scripts/apply_forecast_band_overlay.py', '--signal-date', SIGNAL_DATE, '--bands', str(pool)],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print('DONE', arm, flush=True)
    return arm


if __name__ == '__main__':
    if len(sys.argv) > 2:
        child(sys.argv[1])
    else:
        arms = [a for a in os.environ.get('EXP_ARMS', '+'.join(ARMS)).split('+') if a]
        with ThreadPoolExecutor(max_workers=len(arms)) as pool:
            list(pool.map(run, arms))
