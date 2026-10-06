"""OI-234 偏离减仓 K 1.30 在现行 BASE 上的落地读数（用户 2026-10-07 裁定重测，预登记 `preregister.md`）：v4.235 正式逐日状态上，
CONTROL＝现行 BASE、NEW＝BASE ＋ `--dev-trim 1.30`（冷却 10、MA20 缺省；引擎当日偏离减仓的持仓不作换仓卖出源），14 起点，全样本、A、U。
同法见 `../exp_oi234_land_20261006/`（K 1.35，作业 27680415）。剔除集按 §12.1 第 3 款现算：A = CONTROL 2011-11-01 起点前五，
U = A ∪ NEW 同起点前五；另跑 R = NEW 自身锚点前五（若裁定安装，重登 BASE 的剔除集 A 行）。CONTROL 全样本与 A 须逐字段复现在册 BASE。

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

ARMS = {'CONTROL': [], 'NEW': ['--dev-trim', '1.30']}
REF = 'CONTROL'
CLAUSE4 = (('滚动5年年化中位', 0, +1), ('滚动5年年化P25', 0, +1), ('滚动5年年化最差', 0, +1), ('滚动5年回撤中位', 0, -1),
           ('滚动5年Calmar中位', 1, +1), ('滚动5年Sharpe中位', 1, +1), ('滚动5年为负的窗口占比', 0, -1), ('年化', 0, +1),
           ('最大回撤', 0, -1), ('Calmar', 1, +1), ('Sharpe', 1, +1), ('互不重叠5年块中位', 0, +1), ('滚动3年年化中位', 0, +1),
           ('滚动3年回撤中位', 0, -1), ('逐年收益中位', 0, +1), ('逐年最差', 0, +1))


def base_args(extra: list[str]) -> list[str]:
    args = shlex.split(sw.BASE)
    if '--dev-trim' in args:                          # 落地后 BASE 已含偏离减仓：CONTROL 去掉它以复现改前
        i = args.index('--dev-trim'); del args[i:i + 2]
    return args + extra


def one(job):
    arm, start, group, excluded = job
    tag = sw.summary_tag(arm + group, start, ','.join(excluded))
    cmd = [sys.executable, str(ROOT / 'scripts/backtest_valuation_strategy.py'), *base_args(ARMS[arm]), '--since', start,
           '--label-suffix', '_' + tag, '--out-dir', str(EXP / 'cache'), '--equity-bond-log-dir', str(EXP / 'daily')]
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


def _close(a, b):
    try:
        return abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(a)))
    except (TypeError, ValueError):
        return False


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
    a_set, r_set = sorted(top5[REF]), sorted(top5['NEW'])
    u_set = sorted(set(a_set) | set(r_set))
    jobs = ([(a, s, 'A', a_set) for a in ARMS for s in sw.DEFAULT_STARTS] + [(a, s, 'U', u_set) for a in ARMS for s in sw.DEFAULT_STARTS]
            + [('NEW', s, 'R', r_set) for s in sw.DEFAULT_STARTS])
    rest = run_jobs(jobs)
    write_sweep(EXP / 'sweep_full.txt', full)
    write_sweep(EXP / 'sweep_A.txt', [r for r in rest if r['group'] == 'A'], a_set)
    write_sweep(EXP / 'sweep_U.txt', [r for r in rest if r['group'] == 'U'], u_set)
    rows = full + rest
    with (EXP / 'summary_rows.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    FULL, EXA, EXU = load(EXP / 'sweep_full.txt')[''], load(EXP / 'sweep_A.txt')[sw.EX5_PREFIX], load(EXP / 'sweep_U.txt')[sw.EX5_PREFIX]
    col = lambda arm, key: sorted(FULL[arm][s][key] for s in sw.DEFAULT_STARTS)
    med = lambda xs: xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2
    reproduced, mismatched = 0, []
    for r in rows:
        if r['arm'] != REF or r['group'] not in ('full', 'A'):
            continue
        reg = next(csv.DictReader((sw.OUT_DIR / f"summary_{sw.summary_tag('BASE', r['start'], 'x' if r['group'] == 'A' else '')}.csv").open()))
        bad = [k for k in reg if k != '策略' and reg[k] != r.get(k) and not _close(reg[k], r.get(k))]
        reproduced += not bad
        if bad:
            mismatched.append((r['group'], r['start'], bad[:3]))
    res = dict(job=os.getenv('SLURM_JOB_ID'), ref=REF, A=a_set, U=u_set, R=r_set, top5=top5, arms={},
               control_reproduction=dict(matched=reproduced, of=28, mismatched=mismatched))
    for arm in ('NEW',):
        pm = lambda g, key: sw._paired_median(g, arm, key, ref=REF)
        flag, reasons, _ = sw.reading_flags(FULL, EXA, arm, ref=REF)
        clause = {k: pm(EXU, k) for k, _r, _s in CLAUSE4}
        grade = ['ok' if sign * clause[k] >= lo else 'band' if sign * clause[k] >= band else 'bad'
                 for k, ratio, sign in CLAUSE4 for lo, band in [(-0.005, -0.033) if ratio else (-0.0015, -0.01)]]
        res['arms'][arm] = dict(flag=flag, reasons=reasons, u_clause4=clause, u_all_good=grade.count('bad') == 0 and grade.count('band') <= 1,
                                main=[pm(FULL, sw.WIN5_KEY), pm(EXA, sw.WIN5_KEY), pm(EXU, sw.WIN5_KEY)],
                                cagr=[pm(FULL, '年化'), pm(EXA, '年化'), pm(EXU, '年化')],
                                mdd=[pm(FULL, '最大回撤'), pm(EXA, '最大回撤')],
                                better_starts=sum(FULL[arm][s]['年化'] > FULL[REF][s]['年化'] for s in sw.DEFAULT_STARTS))
    res['levels'] = {arm: dict(cagr_median=med(col(arm, '年化')), mdd_median=med(col(arm, '最大回撤')),
                               anchor_2009=FULL[arm]['2009-11-01']['年化'], anchor_2011=FULL[arm]['2011-11-01']['年化'])
                     for arm in ARMS}
    (EXP / 'readings.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + '\n')
    pp = lambda v: f'{v * 100:+.2f}'
    cr = res['control_reproduction']
    md = ['# OI-234 偏离减仓 K 1.30 落地读数（对 CONTROL＝现行 BASE，14 起点，参考）', '',
          f"CONTROL 复现在册 BASE 全样本与 A：{cr['matched']}/{cr['of']}（数值字段容差 1e-12）。", '']
    for arm, label in (('NEW', 'NEW（BASE ＋ 收盘 ≥ MA20 × 1.30 减一档）'),):
        a = res['arms'][arm]
        md.append(f"- {label}：标记 {a['flag']}{'（' + '；'.join(a['reasons']) + '）' if a['reasons'] else ''}；"
                  f"主读数 全／A／U {'／'.join(pp(v) for v in a['main'])}；复利 全／A／U {'／'.join(pp(v) for v in a['cagr'])}；"
                  f"全期回撤 Δ 全／A {'／'.join(pp(v) for v in a['mdd'])}；复利胜出起点 {a['better_starts']}/14；"
                  f"U 第 4 款 {'去赢家全面优秀' if a['u_all_good'] else '不满足'}。")
    L = res['levels']
    md += ['', f"在册 BASE（NEW）：年化中位 {L['NEW']['cagr_median']:.2%}、最大回撤中位 {L['NEW']['mdd_median']:.2%}；长跑 2009-11 {L['NEW']['anchor_2009']:.2%}、"
           f"2011-11 {L['NEW']['anchor_2011']:.2%}。对照 CONTROL：年化中位 {L['CONTROL']['cagr_median']:.2%}、最大回撤中位 {L['CONTROL']['mdd_median']:.2%}。", '',
           f"A（CONTROL 锚点前五）= {'/'.join(a_set)}；U = {'/'.join(u_set)}；R（NEW 锚点前五，重登用）= {'/'.join(r_set)}。"]
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
