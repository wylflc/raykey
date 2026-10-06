"""OI-270 读数：各臂信号日池带 V 与 `P/V` 对 CONTROL 的变化（CONTROL 须逐只复现生产池带 V），超过 V 的 3% 且涉及买入区的列出；
另列权益法投资收益占利润总额的一阶清单（权益法创投基金收益进 EBIT，OI-270 第 3 项）。

    python3 compare.py     # → results.json、readings.md
"""
import csv
import json

from common import ARMS, BUY_LINE, EXP, POOL_BANDS, QUOTES, ROOT

MATERIAL = 3.0          # OI-270 完成条件：超过 V 的 3% 且涉及买入区


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return {r['security_code'].zfill(6): r for r in csv.DictReader(fh)}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def equity_method(codes):
    out = {}
    with (ROOT / 'data/raw/financials_statements/income.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            c = (r.get('security_code') or '').zfill(6)
            if c in codes and (r.get('REPORT_DATE') or '').startswith('2025-12-31'):
                joint, tp = num(r.get('INVEST_JOINT_INCOME')), num(r.get('TOTAL_PROFIT'))
                if joint is not None and tp and tp > 0:
                    out[c] = (joint / 1e8, joint / tp)
    return out


def main():
    prod, quotes = read(POOL_BANDS), read(QUOTES)
    arms = {arm: read(EXP / 'arms' / arm / 'pool_adopted.csv') for arm in ARMS}
    control = arms['CONTROL']
    mismatch = [c for c, r in prod.items() if num(r.get('intrinsic_value')) is not None
                and (num(control.get(c, {}).get('intrinsic_value')) is None
                     or abs(num(control[c]['intrinsic_value']) - num(r['intrinsic_value'])) > 1e-4)]
    rows = []
    for code, r in prod.items():
        v0, close = num(control.get(code, {}).get('intrinsic_value')), num(quotes.get(code, {}).get('close'))
        if v0 is None or not close:
            continue
        rec = dict(code=code, name=r.get('security_name', ''), close=close, V=round(v0, 4), pv=round(close / v0, 4))
        for arm in ARMS:
            if arm == 'CONTROL':
                continue
            v = num(arms[arm].get(code, {}).get('intrinsic_value'))
            rec[f'chg_{arm}'] = round((v / v0 - 1) * 100, 3) if v else None
            rec[f'pv_{arm}'] = round(close / v, 4) if v else None
        rows.append(rec)
    summary = {}
    for arm in ARMS:
        if arm == 'CONTROL':
            continue
        moved = [r for r in rows if r.get(f'chg_{arm}') is not None and abs(r[f'chg_{arm}']) >= 0.005]
        material = [r for r in moved if abs(r[f'chg_{arm}']) >= MATERIAL
                    and (r['pv'] <= BUY_LINE or (r.get(f'pv_{arm}') or 9) <= BUY_LINE)]
        summary[arm] = dict(changed=len(moved), down=sum(r[f'chg_{arm}'] < 0 for r in moved), up=sum(r[f'chg_{arm}'] > 0 for r in moved),
                            over3=sum(abs(r[f'chg_{arm}']) >= MATERIAL for r in moved),
                            material_zone=[dict(code=r['code'], name=r['name'], chg=r[f'chg_{arm}'], pv=r['pv'], pv_arm=r.get(f'pv_{arm}'))
                                           for r in material],
                            entered=[r['name'] for r in rows if r['pv'] > BUY_LINE and (r.get(f'pv_{arm}') or 9) <= BUY_LINE],
                            left=[r['name'] for r in rows if r['pv'] <= BUY_LINE and (r.get(f'pv_{arm}') or 0) > BUY_LINE])
    em = equity_method(set(prod))
    em_list = sorted(((c, *v) for c, v in em.items() if abs(v[1]) >= 0.10), key=lambda x: -abs(x[2]))
    res = dict(control_mismatch=mismatch, pool_rows=len(rows), summary=summary,
               equity_method=[dict(code=c, name=prod[c].get('security_name', ''), joint_yi=round(j, 2), share=round(s, 4),
                                   pv=next((r['pv'] for r in rows if r['code'] == c), None)) for c, j, s in em_list], rows=rows)
    (EXP / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    f = lambda v, d=3: '—' if v is None else f'{v:.{d}f}'
    md = ['# OI-270 估值细项全池量化（信号日 2026-09-30，候选侧池带；研究开关，生产未改）', '',
          f"CONTROL 复现生产池带 V：不一致 {len(mismatch)} 只；有 V 的池成员 {len(rows)} 只。完成条件：超过 V 的 {MATERIAL:g}% 且涉及买入区的项另拟修正并预登记检验，其余结案。", '']
    label = dict(FX='FX 汇兑等留在 EBIT', M0='M0 少数股东份额各年夹 ≥ 0', ML='ML 少数股东份额取最新年度', RD5='RD5 研发摊销一律 5 年')
    for arm, s in summary.items():
        mz = '、'.join(f"{x['name']} {x['chg']:+.1f}%（P/V {f(x['pv'])}→{f(x['pv_arm'])}）" for x in s['material_zone']) or '无'
        md.append(f"- {label[arm]}：V 变化 {s['changed']} 只（降 {s['down']}、升 {s['up']}），超过 3% 的 {s['over3']} 只；"
                  f"超过 3% 且涉及买入区：{mz}；买入区进 {'、'.join(s['entered']) or '无'}、出 {'、'.join(s['left']) or '无'}。")
    md += ['', '## 权益法投资收益占 2025 年利润总额 ≥ 10% 的池成员（一阶清单，未区分创投基金与合营联营）', '',
           '| 代码 | 名称 | 权益法收益（亿） | 占利润总额 | 当前 P/V |', '|---|---|---|---|---|']
    for x in res['equity_method']:
        md.append(f"| {x['code']} | {x['name']} | {x['joint_yi']:.2f} | {x['share']:.1%} | {f(x['pv'])} |")
    md += ['', '## 各臂 |ΔV| ≥ 1% 的池成员', '', '| 代码 | 名称 | P/V | FX | M0 | ML | RD5 |', '|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: min(r.get(f'chg_{a}') or 0.0 for a in ('FX', 'M0', 'ML', 'RD5'))):
        if all(abs(r.get(f'chg_{a}') or 0.0) < 1.0 for a in ('FX', 'M0', 'ML', 'RD5')):
            continue
        md.append(f"| {r['code']} | {r['name']} | {r['pv']:.3f} | " + ' | '.join(f"{f(r.get(f'chg_{a}'), 1)}%" for a in ('FX', 'M0', 'ML', 'RD5')) + ' |')
    (EXP / 'readings.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md[:12]))


if __name__ == '__main__':
    main()
