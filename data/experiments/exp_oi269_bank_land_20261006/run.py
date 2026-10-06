"""银行 BV 年增速封顶落地第二段：现行 BASE 在 CONTROL（须逐字节等于现行正式状态）与 NEW 状态上跑 14 起点，全样本、A、U。
臂：CONTROL（现行 BASE）、NEW（银行 BV 年增速封顶 7% 的状态，拟安装口径）。读数只作参考，NEW 对 CONTROL 给标记；据 NEW 重登在册 BASE。

    python3 run.py        # → summary_rows.csv、sweep_*.txt、readings.json、readings.md
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

ARMS = {'CONTROL': ('CONTROL', 'signal'), 'NEW': ('NEW', 'signal')}
REF = 'CONTROL'
A_SET = sorted('000651/601088/000338/601225/600897'.split('/'))          # 现行 BASE 锚点前五（OI-257 落地 NEW 同）


def base_args(cap: str) -> list[str]:
    args = shlex.split(sw.BASE)
    if '--cap-equity' in args:
        i = args.index('--cap-equity'); del args[i:i + 2]
    return args + ['--cap-equity', cap]


def one(job):
    arm, start, group, excluded = job
    states, cap = ARMS[arm]
    tag = sw.summary_tag(arm + group, start, ','.join(excluded))
    st = EXP / 'states' / states
    cmd = [sys.executable, str(ROOT / 'scripts/backtest_valuation_strategy.py'), *base_args(cap), '--since', start,
           '--label-suffix', '_' + tag, '--out-dir', str(EXP / 'cache'), '--equity-bond-log-dir', str(EXP / 'daily'),
           '--daily-states', str(st / 'a_share_daily_states_adopted.csv'), '--hold-states', str(st / 'a_share_daily_states_hold.csv')]
    if excluded:
        cmd += ['--exclude-codes', ','.join(excluded)]
    with (EXP / 'errors' / f'{tag}.txt').open('w') as f:
        p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=f)
    assert p.returncode == 0, (tag, p.returncode)
    row = next(r for r in csv.DictReader((EXP / 'cache' / f'summary_{tag}.csv').open()) if r['策略'].startswith('trend_'))
    assert row['计量版本'] == sw.METRIC_VERSION and row['负现金日数'] == '0', tag
    return dict(arm=arm, start=start, group=group, tag=tag, **row)


def run_jobs(jobs):
    with ThreadPoolExecutor(max_workers=int(os.environ.get('WORKERS', 14))) as pool:
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


def load(path):
    sw.set_market(sw.scan_market(path))
    groups, _orders, failed, *_ = sw.load_scan(path)
    assert not any(failed.values()), (path, failed)
    return groups


def main():
    for name in ('cache', 'errors', 'daily'):
        (EXP / name).mkdir(exist_ok=True)
    full = run_jobs([(a, s, 'full', []) for a in ARMS for s in sw.DEFAULT_STARTS])
    top5 = {r['arm']: [c for c in r[sw.EX5_FIELD].split('/') if c] for r in full if r['start'] == sw.EX5_ANCHOR_START}
    u_set = sorted(set(A_SET) | set(top5['NEW']))
    rest = run_jobs([(a, s, 'A', A_SET) for a in ARMS for s in sw.DEFAULT_STARTS]
                    + [(a, s, 'U', u_set) for a in ARMS for s in sw.DEFAULT_STARTS])
    write_sweep(EXP / 'sweep_full.txt', full)
    write_sweep(EXP / 'sweep_A.txt', [r for r in rest if r['group'] == 'A'], A_SET)
    write_sweep(EXP / 'sweep_U.txt', [r for r in rest if r['group'] == 'U'], u_set)
    rows = full + rest
    with (EXP / 'summary_rows.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    FULL, EXA, EXU = load(EXP / 'sweep_full.txt')[''], load(EXP / 'sweep_A.txt')[sw.EX5_PREFIX], load(EXP / 'sweep_U.txt')[sw.EX5_PREFIX]
    col = lambda arm, key: sorted(FULL[arm][s][key] for s in sw.DEFAULT_STARTS)
    med = lambda xs: xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2
    res = dict(job=os.getenv('SLURM_JOB_ID'), ref=REF, A=A_SET, U=u_set, top5=top5, arms={})
    for arm in ('NEW',):
        pm = lambda g, key: sw._paired_median(g, arm, key, ref=REF)
        flag, reasons, _ = sw.reading_flags(FULL, EXA, arm, ref=REF)
        res['arms'][arm] = dict(flag=flag, reasons=reasons,
                                main=[pm(FULL, sw.WIN5_KEY), pm(EXA, sw.WIN5_KEY), pm(EXU, sw.WIN5_KEY)],
                                cagr=[pm(FULL, '年化'), pm(EXA, '年化'), pm(EXU, '年化')],
                                mdd=[pm(FULL, '最大回撤'), pm(EXA, '最大回撤')],
                                better_starts=sum(FULL[arm][s]['年化'] > FULL[REF][s]['年化'] for s in sw.DEFAULT_STARTS))
    res['levels'] = {arm: dict(cagr_median=med(col(arm, '年化')), mdd_median=med(col(arm, '最大回撤')),
                               anchor_2009=FULL[arm]['2009-11-01']['年化'], anchor_2011=FULL[arm]['2011-11-01']['年化'])
                     for arm in ARMS}
    (EXP / 'readings.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + '\n')
    pp = lambda v: f'{v * 100:+.2f}'
    md = ['# 银行 BV 年增速封顶落地读数（对 CONTROL＝现行 BASE，14 起点，参考）', '']
    for arm, label in (('NEW', 'NEW（银行 V_DDM 路径 BV 年增速 ≤ 7%，拟安装）'),):
        a = res['arms'][arm]
        md.append(f"- {label}：标记 {a['flag']}；主读数 全／A／U {'／'.join(pp(v) for v in a['main'])}；复利 全／A／U {'／'.join(pp(v) for v in a['cagr'])}；"
                  f"全期回撤 Δ 全／A {'／'.join(pp(v) for v in a['mdd'])}；复利胜出起点 {a['better_starts']}/14。")
    L = res['levels']
    md += ['', f"在册 BASE（NEW）：年化中位 {L['NEW']['cagr_median']:.2%}、最大回撤中位 {L['NEW']['mdd_median']:.2%}；长跑 2009-11 {L['NEW']['anchor_2009']:.2%}、"
           f"2011-11 {L['NEW']['anchor_2011']:.2%}。对照 CONTROL：年化中位 {L['CONTROL']['cagr_median']:.2%}、最大回撤中位 {L['CONTROL']['mdd_median']:.2%}。", '',
           f"A = {'/'.join(A_SET)}；U = {'/'.join(u_set)}；NEW 锚点前五 {'/'.join(top5['NEW'])}。"]
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
