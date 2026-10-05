"""OI-254 三臂（C／A1／A2）只为 11 只需求周期型资本品建候选侧带与逐日状态（§6.7 第 2 步生产命令，`--all` 换成 `--codes`）。

非金融公司的逐日状态即 `roic_daily_raw.csv`（`rebuild_bank_bands.py` 对非银行行逐位不动）。

    python3 build.py            # 三臂并行
    python3 build.py <ARM>      # 单臂
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
CODES = [c.strip() for c in (EXP / 'demand_cycle_codes.txt').read_text(encoding='utf-8').splitlines() if c.strip()]
PRODUCTION = ['--value-model', 'roic', '--roe-source', 'onesided_max', '--roe-lift', '2.0', '--uniform-tier', 'L2',
              '--since', '2002-01-01', '--roic-nopat-source', 'conditional3', '--roic-growth', 'hybrid',
              '--roic-cycle-guard', 'peak', '--roic-cond-detect', 'graded', '--roic-peak-ramp', '0.3', '--ttm-current', 'on',
              '--growth-damp', 'on', '--thin-equity-max', '0.5', '--roic-trail-weight', '0', '--minority-basis', 'earnings',
              '--wc-aggregation', 'operating', '--cash-caliber', 'nonop', '--equity-anchor', 'guarded',
              '--restricted-cash', 'notes_wc', '--wacc-weights', 'unlevered', '--reset-guard', 'both', '--rd-capitalize', 'on',
              '--fade-shape', 'exponential', '--fade-lambda', '0.12', '--fade-horizon', '50', '--roic-ic-floor', '0.1']
ARMS = {'C': [], 'A1': ['--demand-cycle-codes', str(EXP / 'demand_cycle_codes.txt')],
        'A2': ['--demand-cycle-codes', str(EXP / 'demand_cycle_codes.txt'), '--demand-cycle-g0', 'zero']}


def run(arm: str) -> str:
    out = EXP / 'states' / arm
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(ROOT / 'scripts/build_historical_valuation_bands.py'), '--codes', ','.join(CODES), *PRODUCTION,
           *ARMS[arm], '--out-bands', str(out / 'roic_bands.csv'), '--out-daily', str(out / 'roic_daily_raw.csv')]
    with (EXP / f'build_{arm}.log').open('w') as log:
        subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True,
                       env={'PYTHONUNBUFFERED': '1', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
                            'PATH': '/usr/bin:/bin', 'HOME': str(Path.home()),
                            'RK_STMT_GAP_LOG': str(out / 'gaps.csv')})
    return arm


if __name__ == '__main__':
    arms = sys.argv[1:] or list(ARMS)
    with ThreadPoolExecutor(max_workers=len(arms)) as pool:
        for done in pool.map(run, arms):
            print('DONE', done, flush=True)
