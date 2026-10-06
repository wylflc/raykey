"""核对：CONTROL 逐字节复现三份正式逐日状态；NEW 对 CONTROL 的银行保险行 V 变化；信号日 2026-09-30 实时口径（§6.5.1 第 4 条
`bank_live_value`，封顶在本进程打开）的银行保险 V 与 `P/V`、买入区进出。

    python3 check.py     # → build_check.json、current_changes.md
"""
import csv
import sys

from common import ARMS, BUY_LINE, EXP, PROC, ROOT, SIGNAL_DATE, STATE_FILES, digest, save

sys.path.insert(0, str(ROOT / 'scripts'))


def bank_rows_changed():
    import itertools
    a = (EXP / 'states/CONTROL/a_share_daily_states_adopted.csv').open(encoding='utf-8', newline='')
    b = (EXP / 'states/NEW/a_share_daily_states_adopted.csv').open(encoding='utf-8', newline='')
    ra, rb = csv.DictReader(a), csv.DictReader(b)
    rows = changed = 0
    codes = set()
    for x, y in itertools.zip_longest(ra, rb):
        assert x and y and (x['security_code'], x['date']) == (y['security_code'], y['date'])
        rows += 1
        if x['intrinsic_value'] != y['intrinsic_value']:
            changed += 1
            codes.add(x['security_code'])
    return dict(rows=rows, changed=changed, codes=len(codes))


def live(cap):
    import bank_valuation
    bank_valuation.BV_GROWTH_CAP = cap
    import screen_daily_volume_price_signals as scan
    scan._bank_h2.cache_clear()
    scan._insurer_g_bar.cache_clear()
    quotes = {r['security_code']: r for r in csv.DictReader((PROC / 'daily_buy_candidates.csv').open(encoding='utf-8'))}
    rf = scan._default_rf(SIGNAL_DATE)
    out = {}
    for code, q in quotes.items():
        if scan.is_bank(q['security_name'], code):
            v = scan.bank_live_value(code, SIGNAL_DATE, rf)[0]
            out[code] = (q['security_name'], float(q['close']), v)
    return out


def main():
    check = dict(reproduction={})
    for name in STATE_FILES:
        cur = digest(PROC / name)
        check['reproduction'][name] = dict(current=cur, **{arm: digest(EXP / 'states' / arm / name) for arm in ARMS})
        check['reproduction'][name]['identical'] = cur == check['reproduction'][name]['CONTROL']
        print(name, 'CONTROL 复现' if check['reproduction'][name]['identical'] else 'CONTROL 不同', flush=True)
    check['bank_rows'] = bank_rows_changed()
    before, after = live(None), live(0.07)
    rows = []
    for code, (name, close, v0) in before.items():
        v1 = after[code][2]
        rows.append(dict(code=code, name=name, close=close, V=v0, V_new=v1, pv=close / v0 if v0 else None, pv_new=close / v1 if v1 else None,
                         chg=(v1 / v0 - 1) * 100 if v0 and v1 else None))
    check['live'] = rows
    zone = lambda key: {r['code'] for r in rows if r[key] is not None and r[key] <= BUY_LINE}
    check['entered'], check['left'] = sorted(zone('pv_new') - zone('pv')), sorted(zone('pv') - zone('pv_new'))
    save('build_check.json', check)
    md = [f'# 银行 BV 年增速封顶 7%：信号日 {SIGNAL_DATE} 池内银行保险（实时口径）', '',
          f"逐日状态银行保险行 {check['bank_rows']['changed']:,}／{check['bank_rows']['rows']:,} 行 V 变化（{check['bank_rows']['codes']} 只）；"
          f"买入区进 {check['entered'] or '无'}、出 {check['left'] or '无'}。", '', '| 代码 | 名称 | V 前 | V 后 | 变化 | P/V 前 | P/V 后 |', '|---|---|---|---|---|---|---|']
    f = lambda v, d=3: '—' if v is None else f'{v:.{d}f}'
    for r in sorted(rows, key=lambda r: r['chg'] or 0):
        md.append(f"| {r['code']} | {r['name']} | {f(r['V'], 2)} | {f(r['V_new'], 2)} | {f(r['chg'], 2)}% | {f(r['pv'])} | {f(r['pv_new'])} |")
    (EXP / 'current_changes.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
