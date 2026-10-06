"""OI-271 读数：各臂信号日池带 V 与 `P/V` 对 CONTROL 的变化；CONTROL 须逐只复现生产池带 V；附 FY2025 客户资金分项（一阶量级）。

    python3 compare.py     # → results.json、readings.md
"""
import csv
import json
import sys

from common import ARMS, BUY_LINE, EXP, POOL_BANDS, QUOTES, ROOT

sys.path.insert(0, str(ROOT / 'scripts'))
import roic_inputs  # noqa: E402

KINDS = ('prepay', 'rebate', 'vat', 'payment', 'unclassified')
LABEL = dict(prepay='预收与监管商品', rebate='返利折让退货', vat='待转销项税', payment='支付往来', unclassified='未归类')


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return {r['security_code'].zfill(6): r for r in csv.DictReader(fh)}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    prod, quotes = read(POOL_BANDS), read(QUOTES)
    arms = {arm: read(EXP / 'arms' / arm / 'pool_adopted.csv') for arm in ARMS}
    control = arms['CONTROL']
    mismatch = [c for c, r in prod.items() if num(r.get('intrinsic_value')) is not None
                and (num(control.get(c, {}).get('intrinsic_value')) is None
                     or abs(num(control[c]['intrinsic_value']) - num(r['intrinsic_value'])) > 1e-4)]
    detail = roic_inputs.load_customer_float(set(prod), detail=True)
    contract = roic_inputs.load_balance_fields(set(prod), roic_inputs.CONTRACT_FLOAT_FIELDS)
    rows = []
    for code, r in prod.items():
        v0 = num(control.get(code, {}).get('intrinsic_value'))
        close = num(quotes.get(code, {}).get('close'))
        if v0 is None or not close:
            continue
        shares = num(r.get('shares_est'))
        fy = detail.get((code, '2025-12-31'), {})
        cl = contract.get((code, '2025-12-31'), {})
        rec = dict(code=code, name=r.get('security_name', ''), path=r.get('roic_path', ''), close=close, V=round(v0, 4), pv=round(close / v0, 4),
                   fy2025_yi={k: round(fy.get(k, 0.0) / 1e8, 2) for k in KINDS},
                   contract_yi=round(sum((cl.get(f) or 0.0) for f in roic_inputs.CONTRACT_FLOAT_FIELDS) / 1e8, 2),
                   shares_yi=round(shares / 1e8, 4) if shares else None)
        for arm in ARMS:
            if arm == 'CONTROL':
                continue
            v = num(arms[arm].get(code, {}).get('intrinsic_value'))
            rec[f'V_{arm}'] = round(v, 4) if v is not None else None
            rec[f'pv_{arm}'] = round(close / v, 4) if v else None
            rec[f'chg_{arm}'] = round((v / v0 - 1) * 100, 3) if v else None
        rows.append(rec)
    zone = lambda key: {r['code'] for r in rows if r.get(key) is not None and r[key] <= BUY_LINE}
    summary = {}
    for arm in ARMS:
        if arm == 'CONTROL':
            continue
        moved = [r for r in rows if r.get(f'chg_{arm}') is not None and abs(r[f'chg_{arm}']) >= 0.005]
        summary[arm] = dict(changed=len(moved), down=sum(r[f'chg_{arm}'] < 0 for r in moved), up=sum(r[f'chg_{arm}'] > 0 for r in moved),
                            entered=sorted(zone(f'pv_{arm}') - zone('pv')), left=sorted(zone('pv') - zone(f'pv_{arm}')),
                            zone=len(zone(f'pv_{arm}')))
    res = dict(control_mismatch=mismatch, pool_rows=len(rows), zone_control=len(zone('pv')), summary=summary, rows=rows)
    (EXP / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    name = {r['code']: r['name'] for r in rows}
    md = ['# OI-271 全池量化读数（信号日 2026-09-30，候选侧池带；研究开关，生产未改）', '',
          f"CONTROL 复现生产池带 V：不一致 {len(mismatch)} 只{'（' + '、'.join(mismatch) + '）' if mismatch else ''}；有 V 的池成员 {len(rows)} 只，"
          f"买入区（P/V ≤ {BUY_LINE}）{res['zone_control']} 只。", '']
    for arm, label in (('C1', 'C1 其他流动负债客户资金类扣超额现金'), ('C2', 'C2 另扣合同负债与预收款项'), ('W', 'W 只计入营运资金')):
        s = summary[arm]
        md.append(f"- {label}：V 变化 {s['changed']} 只（降 {s['down']}、升 {s['up']}）；买入区 {res['zone_control']} → {s['zone']}，"
                  f"进 {'、'.join(name[c] for c in s['entered']) or '无'}，出 {'、'.join(name[c] for c in s['left']) or '无'}。")
    md += ['', '| 代码 | 名称 | 收盘 | V | P/V | C1 | C2 | W | P/V(C1) | P/V(C2) | FY2025 其他流动负债客户资金（亿：' + '／'.join(LABEL[k] for k in KINDS) + '） | 合同负债＋预收（亿） |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|']
    f = lambda v, d=3: '—' if v is None else f'{v:.{d}f}'
    for r in sorted(rows, key=lambda r: (r.get('chg_C2') or 0.0)):
        if all(abs(r.get(f'chg_{a}') or 0.0) < 0.5 for a in ('C1', 'C2', 'W')):
            continue
        md.append(f"| {r['code']} | {r['name']} | {r['close']:.2f} | {r['V']:.2f} | {r['pv']:.3f} | {f(r.get('chg_C1'), 1)}% | {f(r.get('chg_C2'), 1)}% | "
                  f"{f(r.get('chg_W'), 1)}% | {f(r.get('pv_C1'))} | {f(r.get('pv_C2'))} | "
                  + '／'.join(f"{r['fy2025_yi'][k]:.1f}" for k in KINDS) + f" | {r['contract_yi']:.1f} |")
    md += ['', '只列任一臂 |ΔV| ≥ 0.5% 的池成员；百分比为 V 对 CONTROL 的变化。']
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md[:8]))


if __name__ == '__main__':
    main()
