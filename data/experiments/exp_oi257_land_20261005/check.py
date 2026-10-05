"""两臂核对：CONTROL 逐字节复现现行七份逐日状态；NEW 对 CONTROL 的带值变化（逐代码最新带）；
信号日 2026-09-30 池带（§6.7 第 4 步同命令、写本目录 `pool/`）的 V、`P/V` 与买入区进出。

    python3 check.py      # → build_check.json、current_changes.json、current_changes.md
"""
import csv
import subprocess
import sys

from common import ARMS, BUY_LINE, EXP, PROC, ROOT, SIGNAL_DATE, STATE_FILES, digest, read, save


def latest_bands(path):
    """逐代码最新一条带（按可得日、报告期）：V、净负债、路径。"""
    out = {}
    with path.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            k = r['security_code']
            if k not in out or (r.get('available_at', ''), r.get('report_date', '')) >= (out[k].get('available_at', ''), out[k].get('report_date', '')):
                out[k] = r
    return out


def band_diff(name):
    """同一 (代码, 报告期, 可得日) 的带值差异计数与最新带变化。"""
    key = lambda r: (r['security_code'], r.get('report_date', ''), r.get('available_at', ''))
    a = {key(r): r for r in read(EXP / 'states/CONTROL' / name)}
    b = {key(r): r for r in read(EXP / 'states/NEW' / name)}
    changed = [k for k in a.keys() & b.keys() if a[k].get('intrinsic_value') != b[k].get('intrinsic_value')]
    return dict(rows=len(a), only_control=len(a.keys() - b.keys()), only_new=len(b.keys() - a.keys()),
                value_changed=len(changed), codes_changed=len({k[0] for k in changed}))


def pool(arm):
    """该臂信号日池带：候选侧与 B2 各按 §6.7 第 4 步建、叠加（预告／研究数／除权归一化），持仓侧取较高 V。"""
    out = EXP / 'pool'
    out.mkdir(exist_ok=True)
    states = EXP / 'states' / arm
    for side, bands, st in (('adopted', 'roic_bands.csv', 'a_share_daily_states_adopted.csv'),
                            ('b2', 'roic_bands_b2.csv', 'a_share_daily_states_b2.csv')):
        target = out / f'{arm}_{side}.csv'
        subprocess.run([sys.executable, 'scripts/build_pool_model_bands.py', '--signal-date', SIGNAL_DATE, '--bands', str(states / bands),
                        '--states', str(states / st), '--out', str(target)], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, 'scripts/apply_forecast_band_overlay.py', '--signal-date', SIGNAL_DATE, '--bands', str(target)],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    a = {r['security_code']: r for r in read(out / f'{arm}_adopted.csv')}
    b = {r['security_code']: r for r in read(out / f'{arm}_b2.csv')}
    return a, b


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    check = dict(reproduction={}, band_diff={})
    for name in STATE_FILES:
        cur, rep, new = digest(PROC / name), digest(EXP / 'states/CONTROL' / name), digest(EXP / 'states/NEW' / name)
        check['reproduction'][name] = dict(current=cur, control=rep, new=new, identical=cur == rep)
        print(name, 'CONTROL 复现' if cur == rep else 'CONTROL 不同', flush=True)
    for name in ('roic_bands.csv', 'roic_bands_b2.csv'):
        check['band_diff'][name] = band_diff(name)
    save('build_check.json', check)
    quotes = {r['security_code']: r for r in read(PROC / 'daily_buy_candidates.csv')}
    pools = {arm: pool(arm) for arm in ARMS}
    rows = []
    for code, q in quotes.items():
        price = num(q.get('close'))
        rec = dict(code=code, name=q['security_name'], close=price)
        for arm in ARMS:
            a, b = pools[arm][0].get(code, {}), pools[arm][1].get(code, {})
            va, vb = num(a.get('intrinsic_value')), num(b.get('intrinsic_value'))
            hold = max(v for v in (va, vb) if v is not None) if (va or vb) else None
            rec[f'V_{arm}'] = va
            rec[f'pv_{arm}'] = price / va if price and va else None
            rec[f'hold_pv_{arm}'] = price / hold if price and hold else None
            rec[f'net_debt_ps_{arm}'] = num(a.get('net_debt_ps'))
            rec[f'status_{arm}'] = a.get('status')
        if rec['V_CONTROL'] and rec['V_NEW']:
            rec['v_change_pct'] = (rec['V_NEW'] / rec['V_CONTROL'] - 1) * 100
        rows.append(rec)
    production = {r['security_code']: num(r.get('model_intrinsic_value')) for r in quotes.values()}
    control_matches = sum(1 for r in rows if r['V_CONTROL'] is not None and production.get(r['code']) is not None
                          and abs(r['V_CONTROL'] - production[r['code']]) <= 0.005)
    moved = sorted((r for r in rows if r.get('v_change_pct') is not None and abs(r['v_change_pct']) >= 0.005),
                   key=lambda r: r['v_change_pct'])
    zone = lambda arm: {r['code'] for r in rows if r.get(f'pv_{arm}') is not None and r[f'pv_{arm}'] <= BUY_LINE}
    entered, left = sorted(zone('NEW') - zone('CONTROL')), sorted(zone('CONTROL') - zone('NEW'))
    unval = lambda arm: {r['code'] for r in rows if r.get(f'V_{arm}') is None}
    res = dict(signal_date=SIGNAL_DATE, pool=len(rows), control_matches_production=control_matches,
               production_with_v=sum(v is not None for v in production.values()), v_changed=len(moved),
               buy_zone_control=len(zone('CONTROL')), buy_zone_new=len(zone('NEW')), entered=entered, left=left,
               unvaluable_in=sorted(unval('NEW') - unval('CONTROL')), unvaluable_out=sorted(unval('CONTROL') - unval('NEW')),
               rows=moved)
    save('current_changes.json', res)
    md = [f'# OI-257 落地：信号日 {SIGNAL_DATE} 池带变化（NEW 对 CONTROL，候选侧）', '',
          f"池 {res['pool']} 只；CONTROL 与生产候选侧 V 相同 {control_matches}/{res['production_with_v']} 只；V 变化 {len(moved)} 只；"
          f"买入区（P/V ≤ {BUY_LINE}）{res['buy_zone_control']} → {res['buy_zone_new']} 只，进 {entered or '无'}，出 {left or '无'}；"
          f"无法估值进 {res['unvaluable_in'] or '无'}、出 {res['unvaluable_out'] or '无'}。", '',
          '| 代码 | 名称 | V 前 | V 后 | 变化 | P/V 前 | P/V 后 | 持仓侧 P/V 前 | 后 |', '|---|---|---|---|---|---|---|---|---|']
    f = lambda v, d=3: '—' if v is None else f'{v:.{d}f}'
    for r in moved:
        md.append(f"| {r['code']} | {r['name']} | {f(r['V_CONTROL'], 2)} | {f(r['V_NEW'], 2)} | {r['v_change_pct']:+.2f}% | "
                  f"{f(r['pv_CONTROL'])} | {f(r['pv_NEW'])} | {f(r['hold_pv_CONTROL'])} | {f(r['hold_pv_NEW'])} |")
    (EXP / 'current_changes.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md[:4]))


if __name__ == '__main__':
    main()
