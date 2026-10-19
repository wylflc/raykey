"""OI-290 读数 6（§12.1 第 13 款）与读数 8 的扫描配置（preregister.md）。

1. 各臂按 §12.1 对齐买入线（在册合格面 16.687%，容差 0.2pp，原线 1.0034）→ align.json；
2. 第 13 款机会／陷阱读数（四臂并列，各按其买入线）→ opportunity_trap.md／.json；
3. 写回测扫描配置 sweep_arms.txt（相对 BASE 只换逐日状态与 --width）。

    python3 post.py
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
SCRATCH = Path(os.environ.get('OI290_DIR', ROOT / 'data/scratch/experiments/exp_oi290_20261019')) / 'states'
OUT = Path(os.environ.get('OI290_OUT', EXP))
ARMS = ('C', 'F3', 'F5', 'FR')
LINE, SHARE, TOL = 1.0034, 16.687, 0.2


def states(arm: str, side: str = 'adopted') -> Path:
    return SCRATCH / arm / f'a_share_daily_states_{side}.csv'


def align(arm: str) -> dict:
    out = subprocess.run([sys.executable, str(ROOT / 'scripts/experimental/align_buy_line.py'), str(states('C')), str(states(arm)),
                          '--base-line', f'{LINE}', '--registered-share', f'{SHARE}', '--tolerance-pp', f'{TOL}'],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    arm_part = out.split('\n\n', 1)[-1]
    lines = re.findall(r'(?:保留原线 |买入线 \*\*)([0-9]+\.[0-9]{4})', arm_part)
    shares = re.findall(r'下侧合格面 ([0-9.]+)%', arm_part)
    return dict(line=float(lines[-1]), kept='保留原线' in arm_part, original_line_share=float(shares[0]) if shares else None,
                log=out)


def main() -> None:
    aligned = {arm: align(arm) for arm in ARMS}
    (OUT / 'align.json').write_text(json.dumps(aligned, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for arm, a in aligned.items():
        print(arm, '买入线', a['line'], '保留原线' if a['kept'] else '重解', '原线合格面', a['original_line_share'])
    cmd = [sys.executable, str(ROOT / 'scripts/experimental/opportunity_trap_audit.py'),
           '--states', *[f'{arm}={states(arm)}' for arm in ARMS],
           '--buy-line', *[f"{arm}={aligned[arm]['line']:.4f}" for arm in ARMS],
           '--out', str(OUT / 'opportunity_trap.md')]
    subprocess.run(cmd, cwd=ROOT, check=True)
    rows = ['BASE|']
    for arm in ARMS:
        width = 1 - aligned[arm]['line']
        rows.append(f"{arm}|--daily-states {states(arm)} --hold-states {states(arm, 'hold')} --width {width:.4f}")
    (OUT / 'sweep_arms.txt').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    print('写出', OUT / 'sweep_arms.txt')


if __name__ == '__main__':
    main()
