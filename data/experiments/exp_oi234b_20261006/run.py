"""OI-234 第二轮偏离减仓（preregister.md）：7 臂 × 14 起点，全样本（带逐周期产物与成交流水）、剔除集 A、逐新臂 U；0bp。
CONTROL 须逐字段复现在册 BASE（v4.233 重登，`data/backtest/scan_summaries.csv`）全样本与 A 的 28 条路径，锚点前五须等于 A。

    python3 run.py        # → summary_rows.csv、sweep_*.txt、u/*.txt、reproduction.json、run_manifest.json
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

REF = 'CONTROL'
A_SET = sorted('000651/601088/000338/601225/600897'.split('/'))
ARMS = {'CONTROL': [], 'D130': ['--dev-trim', '1.30'], 'D140': ['--dev-trim', '1.40'], 'D150': ['--dev-trim', '1.50'],
        'E130': ['--dev-trim', '1.30', '--dev-trim-ma', '60'], 'E145': ['--dev-trim', '1.45', '--dev-trim-ma', '60'],
        'E160': ['--dev-trim', '1.60', '--dev-trim-ma', '60']}
NEW = [a for a in ARMS if a != REF]


def one(job):
    arm, start, group, excluded = job
    tag = sw.summary_tag(arm + group, start, ','.join(excluded))
    base = shlex.split(sw.BASE)
    out = EXP / ('artifacts' if group == 'full' else 'cache')
    if group == 'full':
        base.remove('--no-artifacts')
    cmd = [sys.executable, str(ROOT / 'scripts/backtest_valuation_strategy.py'), *base, *ARMS[arm], '--since', start,
           '--label-suffix', '_' + tag, '--out-dir', str(out), '--equity-bond-log-dir', str(EXP / 'daily')]
    if excluded:
        cmd += ['--exclude-codes', ','.join(excluded)]
    if group == 'full':
        cmd += ['--trade-log', str(EXP / 'ledgers' / f'{tag}.csv')]
    with (EXP / 'errors' / f'{tag}.txt').open('w') as f:
        p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=f)
    assert p.returncode == 0, (tag, p.returncode)
    row = next(r for r in csv.DictReader((out / f'summary_{tag}.csv').open()) if r['策略'].startswith('trend_'))
    assert row['计量版本'] == sw.METRIC_VERSION and row['负现金日数'] == '0', tag
    return dict(arm=arm, start=start, group=group, tag=tag, **row)


def run_jobs(jobs):
    with ThreadPoolExecutor(max_workers=int(os.environ.get('WORKERS', int(os.environ.get('SLURM_CPUS_PER_TASK', 16)) - 2))) as pool:
        return list(pool.map(one, jobs))


def write_sweep(path, rows, excluded=None):
    with path.open('w') as f:
        f.write(sw.metric_header() + '\n#MARKET|a\n')
        if excluded:
            f.write('#EX5|fixed|' + ','.join(excluded) + '\n')
        for r in rows:
            label = ('EX5:' if excluded else '') + r['arm']
            f.write('|'.join([label, r['start']] + [f'{sw._field_value(r, k):.6f}' for k in sw.FIELDS]) + '\n')
            f.write(f"#WIN5|{label}|{r['start']}|{r[sw.WIN5_KEY]}\n")


def reproduce(rows):
    """CONTROL 全样本与 A 对在册 BASE（按策略名逐字段，数值容差 1e-9 相对）。"""
    ledger = {(r['扫描标签'], r['策略'], r['计量版本']): r for r in csv.DictReader((ROOT / 'data/backtest/scan_summaries.csv').open())}
    fields = [k for k in rows[0] if k not in ('group', 'arm', 'start', 'tag', '策略', '扫描标签')]

    def close(a, b):
        try:
            return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)))
        except ValueError:
            return a == b
    diffs, checked = {}, 0
    for r in rows:
        if r['arm'] != REF or r['group'] not in ('full', 'A'):
            continue
        tag = sw.summary_tag('BASE', r['start'], ','.join(A_SET) if r['group'] == 'A' else '')
        reg = ledger.get((tag, r['策略'][:-len('_' + r['tag'])] + '_' + tag, r['计量版本']))
        checked += 1
        if reg is None:
            diffs[f"{r['group']}|{r['start']}"] = 'missing'
            continue
        d = {k: [reg[k], r[k]] for k in fields if k in reg and not close(reg[k], r[k])}
        if d:
            diffs[f"{r['group']}|{r['start']}"] = d
    return checked, diffs


def main():
    for name in ('cache', 'artifacts', 'errors', 'daily', 'ledgers', 'u'):
        (EXP / name).mkdir(exist_ok=True)
    full = run_jobs([(a, s, 'full', []) for a in ARMS for s in sw.DEFAULT_STARTS])
    top5 = {r['arm']: [c for c in r[sw.EX5_FIELD].split('/') if c] for r in full if r['start'] == sw.EX5_ANCHOR_START}
    assert sorted(top5[REF]) == A_SET, (top5[REF], A_SET)
    u_sets = {a: sorted(set(A_SET) | set(top5[a])) for a in NEW}
    u_id = {u: f'U{i:02d}' for i, u in enumerate(sorted({tuple(u) for u in u_sets.values()}), 1)}
    rest = run_jobs([(a, s, 'A', A_SET) for a in ARMS for s in sw.DEFAULT_STARTS]
                    + [(a, s, 'U', u_sets[a]) for a in NEW for s in sw.DEFAULT_STARTS]
                    + [(REF, s, gid, list(u)) for u, gid in u_id.items() for s in sw.DEFAULT_STARTS])
    rows = full + rest
    checked, diffs = reproduce(rows)
    (EXP / 'reproduction.json').write_text(json.dumps(dict(paths=checked, differences=diffs, ref_top5=top5[REF], A=A_SET),
                                                      ensure_ascii=False, indent=1) + '\n')
    write_sweep(EXP / 'sweep_full.txt', full)
    write_sweep(EXP / 'sweep_A.txt', [r for r in rest if r['group'] == 'A'], A_SET)
    for a, u in u_sets.items():
        gid = u_id[tuple(u)]
        write_sweep(EXP / 'u' / f'{a}.txt', [r for r in rest if (r['arm'] == a and r['group'] == 'U') or (r['arm'] == REF and r['group'] == gid)], u)
    with (EXP / 'summary_rows.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (EXP / 'run_manifest.json').write_text(json.dumps(dict(job_id=os.getenv('SLURM_JOB_ID'), base=sw.BASE, ref=REF, arms=ARMS, A=A_SET,
                                                          top5=top5, U=u_sets, U_groups={g: list(u) for u, g in u_id.items()},
                                                          starts=sw.DEFAULT_STARTS), ensure_ascii=False, indent=1) + '\n')
    assert not diffs, diffs
    print('DONE runs', len(rows), 'reproduction ok', checked)


if __name__ == '__main__':
    main()
