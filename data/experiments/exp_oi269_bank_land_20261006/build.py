"""两臂 × 两侧银行保险覆盖（§6.7 第 3 步）并行重建，再合成持仓侧，产物写 `states/<臂>/`。

    python3 build.py
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from common import ARMS, EXP, PROC, ROOT, SIDES


def bank(job):
    arm, side = job
    out = EXP / 'states' / arm
    out.mkdir(parents=True, exist_ok=True)
    raw, bands, states = SIDES[side]
    with (EXP / 'states' / f'build_{arm}_{side}.log').open('w') as f:
        subprocess.run([sys.executable, 'scripts/rebuild_bank_bands.py', ARMS[arm], str(out / states), str(PROC / raw), str(PROC / bands)],
                       cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
    print('DONE', arm, side, flush=True)


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(bank, [(a, s) for a in ARMS for s in SIDES]))
    for arm in ARMS:
        out = EXP / 'states' / arm
        subprocess.run([sys.executable, 'scripts/build_hold_daily_states.py', '--base', str(out / 'a_share_daily_states_adopted.csv'),
                        '--b2', str(out / 'a_share_daily_states_b2.csv'), '--out', str(out / 'a_share_daily_states_hold.csv')], cwd=ROOT, check=True)
        print('DONE', arm, 'hold', flush=True)


if __name__ == '__main__':
    main()
