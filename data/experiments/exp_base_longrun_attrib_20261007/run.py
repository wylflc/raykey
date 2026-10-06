"""现行 BASE（v4.235 在册，正式状态）14 个标准起点单跑（engine.py 包装，全样本），落逐日净值、逐日逐代码盈亏、
滚动窗口与成交流水；每个起点的 summary 与在册 `data/backtest/summary_BASE<起点>.csv` 逐字段比对：非数值逐字相等，
数值相对差 ≤ 1e-12（引擎按集合迭代顺序累加 contrib，`前五赢家占正贡献` 可差末位，属进程间哈希顺序），否则失败。

    WORKERS=8 python3 run.py        # → runs/、reproduce.json
    python3 run.py --check-only     # 只比对已有 runs/
"""
import csv
import json
import os
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import sweep_backtest_configs as sw  # noqa: E402

RUNS = EXP / 'runs'


def compare(start):
    tag = sw.summary_tag('BASE', start)
    mine = next(r for r in csv.DictReader((RUNS / f'summary_{tag}.csv').open(encoding='utf-8')) if r['策略'].startswith('trend_'))
    reg = next(csv.DictReader((ROOT / 'data/backtest' / f'summary_{tag}.csv').open(encoding='utf-8')))
    diff, ulp = [], []
    for k in sorted(set(mine) | set(reg)):
        a, b = mine.get(k), reg.get(k)
        if a == b:
            continue
        try:
            close = abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(b)))
        except (TypeError, ValueError):
            close = False
        (ulp if close else diff).append(k)
    return start, tag, diff, ulp


def one(start):
    tag = sw.summary_tag('BASE', start)
    cmd = [sys.executable, str(EXP / 'engine.py'), *shlex.split(sw.BASE), '--artifacts', '--since', start,
           '--label-suffix', '_' + tag, '--out-dir', str(RUNS), '--equity-bond-log-dir', str(RUNS / 'eb'),
           '--trade-log', str(RUNS / f'{tag}_tradelog.csv')]
    with (RUNS / f'{tag}.log').open('w') as log:
        p = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1'))
    assert p.returncode == 0, (tag, p.returncode)
    return compare(start)


def main():
    if '--check-only' in sys.argv:
        done = [compare(s) for s in sw.DEFAULT_STARTS]
    else:
        (RUNS / 'eb').mkdir(parents=True, exist_ok=True)
        (RUNS / 'job.txt').write_text(os.getenv('SLURM_JOB_ID', '') + '\n')
        with ThreadPoolExecutor(max_workers=int(os.environ.get('WORKERS', 8))) as pool:
            done = list(pool.map(one, sw.DEFAULT_STARTS))
    res = {'starts': len(done), 'identical': sum(not d and not u for *_x, d, u in done),
           'diffs': {tag: d for _s, tag, d, _u in done if d}, 'ulp_only': {tag: u for _s, tag, _d, u in done if u},
           'job': (RUNS / 'job.txt').read_text().strip()}
    (EXP / 'reproduce.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False))
    assert not res['diffs'], res['diffs']


if __name__ == '__main__':
    main()
