"""OI-251 全池量化：峰守卫生效的池带（结构性复核表 `data/interim/structural_growth_review.csv`，信号日 2026-09-30）中，
一次性收益（扣非与归母差距）与扭亏（十年窗口内有亏损年）各涉及几只、守卫对 V 的削减与关守卫的上界 `P/V` 是否进买入区。

    python3 quantify.py     # → quantify.json、quantify.md
"""
import csv
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
LINE, ONE_OFF, YEARS = 1.0034, 0.20, 10


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    guard = [r for r in csv.DictReader((ROOT / 'data/interim/structural_growth_review.csv').open(encoding='utf-8'))
             if (num(r['peak_weight']) or 0) > 0]
    codes = {r['security_code'] for r in guard}
    quotes = {r['security_code']: r for r in csv.DictReader((ROOT / 'data/processed/daily_buy_candidates.csv').open(encoding='utf-8'))}
    annual = {}
    with (ROOT / 'data/raw/financials_statements/income.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            c = (r.get('security_code') or '').zfill(6)
            p = (r.get('REPORT_DATE') or '')[:10]
            if c in codes and p.endswith('-12-31'):
                annual.setdefault(c, {})[p[:4]] = (num(r.get('PARENT_NETPROFIT')), num(r.get('DEDUCT_PARENT_NETPROFIT')))
    half = {}
    with (ROOT / 'data/raw/financials/2026-06-30.csv').open(encoding='utf-8-sig', newline='') as fh:
        for r in csv.DictReader(fh):
            c = (r.get('security_code') or '').zfill(6)
            if c in codes:
                half[c] = (num(r.get('basic_eps')), num(r.get('deduct_basic_eps')))
    rows = []
    for g in guard:
        c = g['security_code']
        years = annual.get(c, {})
        last = max(years) if years else None
        pn, dn = years.get(last, (None, None)) if last else (None, None)
        one_off_fy = (pn - dn) / abs(pn) if pn and dn is not None else None
        be, de = half.get(c, (None, None))
        one_off_h1 = (be - de) / abs(be) if be and de is not None else None
        window = [y for y in sorted(years) if last and int(y) > int(last) - YEARS]
        losses = [y for y in window if years[y][0] is not None and years[y][0] <= 0]
        close = num(quotes.get(c, {}).get('close'))
        vg, vu = num(g['v_guarded']), num(g['v_unguarded'])
        rows.append(dict(code=c, name=g['security_name'], w=num(g['peak_weight']), cut=num(g['cut']), business=g['business_class'],
                         one_off_fy=one_off_fy, fy=last, one_off_h1=one_off_h1, loss_years=losses,
                         pv_guarded=close / vg if close and vg else None, pv_unguarded=close / vu if close and vu else None, vg=vg, vu=vu))
    flag = lambda r: ((r['one_off_fy'] or 0) >= ONE_OFF or (r['one_off_h1'] or 0) >= ONE_OFF, bool(r['loss_years']))
    hit = [r for r in rows if any(flag(r))]
    zone_up = [r for r in hit if r['pv_unguarded'] is not None and r['pv_unguarded'] <= LINE and (r['pv_guarded'] or 9) > LINE]
    out = dict(guarded=len(rows), one_off=sum(flag(r)[0] for r in rows), turnaround=sum(flag(r)[1] for r in rows),
               flagged=len(hit), would_enter_zone_if_unguarded=[r['name'] for r in zone_up], rows=rows)
    (EXP / 'quantify.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8')
    f = lambda v, d=3: '—' if v is None else f'{v:.{d}f}'
    md = ['# OI-251 峰守卫一次性收益与扭亏的全池量化（信号日 2026-09-30）', '',
          f"峰守卫生效（w > 0）的池带 {out['guarded']} 只；一次性收益（最新年报或 2026 上半年「(归母 − 扣非) ÷ |归母|」≥ {ONE_OFF:.0%}）{out['one_off']} 只，"
          f"扭亏（近 {YEARS} 个年报内有亏损年）{out['turnaround']} 只，合计 {out['flagged']} 只；关守卫（上界）后进买入区的："
          f"{'、'.join(out['would_enter_zone_if_unguarded']) or '无'}。", '',
          '| 代码 | 名称 | w | 守卫削减 | 一次性 FY／H1 | 亏损年 | P/V（守卫） | P/V（关守卫上界） |', '|---|---|---|---|---|---|---|---|']
    for r in sorted(hit, key=lambda r: -(r['cut'] or 0)):
        md.append(f"| {r['code']} | {r['name']} | {f(r['w'])} | {f(r['cut'])} | {f(r['one_off_fy'])}（{r['fy']}）／{f(r['one_off_h1'])} | "
                  f"{'、'.join(r['loss_years']) or '—'} | {f(r['pv_guarded'])} | {f(r['pv_unguarded'])} |")
    (EXP / 'quantify.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
