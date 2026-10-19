"""OI-290 四臂（C／F3／F5／FR）全市场重建：§6.7 第 2、2b、3 步的 v4.254 生产命令加 `--g0-none-fill`（preregister.md）。

    python3 build.py                        # 编排：8 个建带进程并行 → 银行与保险覆盖 → 持仓侧逐日状态
    python3 build.py <ARM> <side> bands     # 单个建带进程（side = base | b2）
    python3 build.py <ARM> <side> bank      # 该臂该侧的银行与保险股利折现覆盖

产物写 `data/scratch/experiments/exp_oi290_20261019/states/<ARM>/`（可再生）；日志写本目录 `logs/`。
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
SCRATCH = ROOT / 'data/scratch/experiments/exp_oi290_20261019/states'
ARMS = ('C', 'F3', 'F5', 'FR')
FLAGS = {'C': [], 'F3': ['--g0-none-fill', 'f3'], 'F5': ['--g0-none-fill', 'f5'], 'FR': ['--g0-none-fill', 'fr']}
# §6.7 第 2 步命令（v4.254，与 scripts/slurm/rebuild_chain_with_fetch.sbatch 的 COMMON 相同）
PRODUCTION = ['--all', '--value-model', 'roic', '--roe-source', 'onesided_max', '--roe-lift', '2.0', '--uniform-tier', 'L2',
              '--since', '2002-01-01', '--roic-nopat-source', 'conditional3', '--roic-growth', 'hybrid',
              '--roic-cycle-guard', 'peak', '--roic-cond-detect', 'graded', '--roic-peak-ramp', '0.3',
              '--ttm-current', 'on', '--growth-damp', 'on', '--thin-equity-max', '0.5', '--roic-trail-weight', '0',
              '--minority-basis', 'earnings', '--wc-aggregation', 'operating', '--cash-caliber', 'nonop',
              '--equity-anchor', 'guarded', '--restricted-cash', 'notes_wc', '--wacc-weights', 'unlevered',
              '--reset-guard', 'both', '--rd-capitalize', 'on', '--payout-basis', 'fiscal', '--tax-anomaly', 'median3',
              '--share-equity', 'common', '--dividend-timing', 'post_period', '--note-debt', 'notes',
              '--fade-shape', 'exponential', '--fade-lambda', '0.12', '--fade-horizon', '50', '--roic-ic-floor', '0.1']
B2 = ['--ttm-trust', 'on', '--ttm-trust-delta', '0.02']
BANK_MODE = 'h2:0.02:0.10'


def folder(arm: str) -> Path:
    path = SCRATCH / arm
    path.mkdir(parents=True, exist_ok=True)
    return path


def env(extra: dict | None = None) -> dict:
    return dict(os.environ, PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                OPENBLAS_NUM_THREADS='1', **(extra or {}))


def child(arm: str, side: str, task: str) -> None:
    suffix = '_b2' if side == 'b2' else ''
    out = folder(arm)
    raw, bands = out / f'roic_daily_raw{suffix}.csv', out / f'roic_bands{suffix}.csv'
    if task == 'bands':
        cmd = [sys.executable, str(ROOT / 'scripts/build_historical_valuation_bands.py'), *PRODUCTION, *FLAGS[arm],
               *(B2 if suffix else []), '--out-bands', str(bands), '--out-daily', str(raw)]
        subprocess.run(cmd, cwd=ROOT, check=True, env=env({'RK_STMT_GAP_LOG': str(out / f'gaps{suffix}.csv')}))
    elif task == 'bank':
        states = out / ('a_share_daily_states_b2.csv' if suffix else 'a_share_daily_states_adopted.csv')
        subprocess.run([sys.executable, str(ROOT / 'scripts/rebuild_bank_bands.py'), BANK_MODE, str(states), str(raw), str(bands)],
                       cwd=ROOT, check=True, env=env())
    else:
        raise SystemExit(f'unknown task {task}')


def run(arm: str, side: str, task: str) -> str:
    logs = EXP / 'logs'
    logs.mkdir(exist_ok=True)
    log = logs / f'build_{arm}_{side}_{task}.log'
    with log.open('w') as f:
        subprocess.run([sys.executable, __file__, arm, side, task], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                       env=env(), check=True)
    print(datetime.now(timezone.utc).isoformat(timespec='seconds'), 'DONE', arm, side, task, flush=True)
    return log.name


def orchestrate() -> None:
    arms = [a for a in os.environ.get('EXP_ARMS', '+'.join(ARMS)).split('+') if a]
    rev = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    (EXP / 'run_manifest.json').write_text(json.dumps(dict(
        revision=rev, started_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'), arms=arms,
        production=PRODUCTION, flags={a: FLAGS[a] for a in arms}, b2=B2, bank_mode=BANK_MODE,
        slurm_job=os.environ.get('SLURM_JOB_ID', '')), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    jobs = [(a, s) for a in arms for s in ('base', 'b2')]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(lambda j: run(*j, 'bands'), jobs))
        list(pool.map(lambda j: run(*j, 'bank'), jobs))
    for arm in arms:
        out = folder(arm)
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_hold_daily_states.py'),
                        '--base', str(out / 'a_share_daily_states_adopted.csv'), '--b2', str(out / 'a_share_daily_states_b2.csv'),
                        '--out', str(out / 'a_share_daily_states_hold.csv')], cwd=ROOT, check=True, env=env())
        print(datetime.now(timezone.utc).isoformat(timespec='seconds'), 'DONE', arm, 'hold', flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        child(*sys.argv[1:4])
    else:
        orchestrate()
