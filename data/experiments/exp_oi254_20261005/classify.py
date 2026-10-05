"""OI-254 历史检验用的需求周期型资本品名单（客观口径，preregister.md「样本」）。

ROIC 路径（`roic_bands.csv` 有 ok 的 growth／zero_growth 带）的非金融公司中，同时满足：
1. 证监会大类属资本品：专用设备、通用设备、汽车制造、铁路船舶航空航天和其他运输设备、土木工程建筑；
2. 2008–2025 年任一年报营收较此前三个年报内的最高值回落 ≥ 30%；
3. 不在业务属性登记的商品价格接受者（另有周期口径）与结构成长型、可复制成长型（§9.3.6 成长股模块）之列。

    python3 classify.py      # → demand_cycle_codes.txt、classification.csv
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from divspread_names import is_divspread_financial  # noqa: E402

CAPITAL_GOODS = ('专用设备制造业', '通用设备制造业', '汽车制造业', '铁路、船舶、航空航天和其他运输设备制造业', '土木工程建筑业')
DRAWDOWN, WINDOW = 0.30, 3
GROWTH = {'结构成长型', '可复制成长型'}


def main():
    industry = {}
    with (ROOT / 'data/reference/a_share_csrc_industry.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            industry[r['security_code'].zfill(6)] = (r.get('csrc_industry') or '', r.get('security_name') or '')
    register = {}
    with (ROOT / 'data/processed/a_share_business_attributes.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            register[r['security_code'].zfill(6)] = r
    roic = set()
    with (ROOT / 'data/processed/roic_bands.csv').open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['status'] == 'ok' and r['roic_path'] in ('growth', 'zero_growth'):
                roic.add(r['security_code'])
    revenue = defaultdict(dict)
    with (ROOT / 'data/raw/financials_statements/income.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            code, period = (r.get('security_code') or '').zfill(6), (r.get('REPORT_DATE') or '')[:10]
            if code in roic and period.endswith('12-31'):
                try:
                    revenue[code][int(period[:4])] = float(r.get('TOTAL_OPERATE_INCOME') or r.get('OPERATE_INCOME'))
                except (TypeError, ValueError):
                    pass
    rows, codes = [], []
    for code in sorted(roic):
        label, name = industry.get(code, ('', ''))
        major = label.split('-')[-1]
        if is_divspread_financial(code, name) or not any(k in major for k in CAPITAL_GOODS):
            continue
        rev = revenue.get(code, {})
        worst, when = 0.0, None
        for year in sorted(rev):
            if year < 2008:
                continue
            prior = [rev[y] for y in range(year - WINDOW, year) if y in rev and rev[y] > 0]
            if prior and rev[year] > 0:
                drop = 1 - rev[year] / max(prior)
                if drop > worst:
                    worst, when = drop, year
        reg = register.get(code, {})
        excluded = ('商品价格接受者' if reg.get('pricing_mode') == '商品价格接受者'
                    else reg.get('derived_class') if reg.get('derived_class') in GROWTH else '')
        flagged = worst >= DRAWDOWN and not excluded
        rows.append(dict(code=code, name=name or reg.get('security_name', ''), industry=major, worst_drawdown=round(worst, 3),
                         drawdown_year=when, register_class=reg.get('derived_class', ''), excluded=excluded, flagged=int(flagged)))
        if flagged:
            codes.append(code)
    with (EXP / 'classification.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    (EXP / 'demand_cycle_codes.txt').write_text('\n'.join(codes) + '\n', encoding='utf-8')
    print(f'资本品 ROIC 路径 {len(rows)} 只，标记 {len(codes)} 只')
    for r in rows:
        if r['flagged'] or r['register_class']:
            print(r['code'], r['name'], r['industry'][:10], r['worst_drawdown'], r['drawdown_year'], r['register_class'], r['excluded'], 'FLAG' if r['flagged'] else '')


if __name__ == '__main__':
    main()
