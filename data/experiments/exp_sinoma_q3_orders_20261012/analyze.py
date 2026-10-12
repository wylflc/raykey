"""中材国际 2026Q3 经营数据公告的独立核对：分项勾稽、同比复算、一次性大单拆分、在手合同滚动与汇率折算、V 情景。

orders.csv：各季「主要经营数据公告」原表（万元；公告原文 https://pdf.dfcfw.com/pdf/H2_<art_code>_1.pdf），
revenue_yi 取 data/raw/financials 单季营业收入（亿元），usdcnh_quarter_end 为季末美元兑离岸人民币收盘。

    python3 analyze.py     # → results.json，并打印
"""
import csv
import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_forecast_band_overlay as ov  # noqa: E402
from apply_forecast_band_overlay import num, equity_from_ev  # noqa: E402

CLOSE = 7.89                      # 2026-10-12 收盘
OVERSEAS_BACKLOG_0630 = 531.52    # 2026 半年报 p.12 境外未完合同额（亿元）；06-30 合计 716.52
OVERSEAS_BACKLOG_SHARE_2025 = 0.70  # 2025-09-30 境外占比的估计（2025-06-30 为 67.2%、2026-06-30 为 74.2%）
DANGOTE_USD_YI, DANGOTE_RATE = 4.76, 6.758   # 临 2026-042：设备供货合同 4.76 亿美元，签署即生效；08-03 美元兑离岸人民币

rows = list(csv.DictReader((EXP / 'orders.csv').open(encoding='utf-8')))
Q = {r['quarter']: {k: (float(v) / 1e4 if k not in ('revenue_yi', 'usdcnh_quarter_end') else float(v)) if v else None
                    for k, v in r.items() if k not in ('quarter', 'notice_date', 'art_code')} for r in rows}
names = [r['quarter'] for r in rows]
out = {}

# 1. 分项勾稽
for q, d in Q.items():
    assert abs(d['engineering'] + d['equipment'] + d['operations'] + d['other'] - d['total']) < 1e-6, q
    assert abs(d['domestic'] + d['overseas'] - d['total']) < 1e-6, q
    d['ops_other'] = d['operations'] - d['cement_om'] - d['mining_om']       # 生产运营服务里未列明的部分

# 2. 同比复算（2026Q3 对 2025Q3）
cur, prev = Q['2026Q3'], Q['2025Q3']
yoy = {k: round(100 * (cur[k] / prev[k] - 1), 1) for k in ('total', 'engineering', 'equipment', 'operations', 'cement_om', 'mining_om',
                                                           'other', 'domestic', 'overseas', 'overseas_operations', 'ops_other')}
out['yoy_2026Q3'] = yoy
ytd = lambda y, k: sum(Q[f'{y}Q{i}'][k] for i in (1, 2, 3))
out['ytd'] = {k: [round(ytd(2026, k), 2), round(100 * (ytd(2026, k) / ytd(2025, k) - 1), 1)] for k in ('total', 'engineering', 'equipment', 'operations', 'ops_other')}

# 3. 一次性大单：生产运营服务未列明部分超出上年同期的金额
lump = cur['ops_other'] - prev['ops_other']
out['ops_other_by_quarter'] = {q: round(Q[q]['ops_other'], 2) for q in names}
out['overseas_operations_by_quarter'] = {q: round(Q[q]['overseas_operations'], 2) for q in names}
out['ex_lump'] = dict(lump_yi=round(lump, 2), q3_total_ex=round(cur['total'] - lump, 2), q3_yoy_ex=round(100 * ((cur['total'] - lump) / prev['total'] - 1), 1),
                      ytd_total_ex=round(ytd(2026, 'total') - lump, 2), ytd_yoy_ex=round(100 * ((ytd(2026, 'total') - lump) / ytd(2025, 'total') - 1), 1))
dangote = DANGOTE_USD_YI * DANGOTE_RATE
out['dangote'] = dict(cny_yi=round(dangote, 2), overseas_engineering_q3=65.89, cement_engineering_q3=42.31, cement_engineering_ex=round(42.31 - dangote, 2))

# 4. 滚动四季新签
ttm = lambda i, k: sum(Q[names[j]][k] for j in range(i - 3, i + 1))
i3 = names.index('2026Q3')
out['ttm'] = {k: [round(ttm(i3, k), 2), round(100 * (ttm(i3, k) / ttm(i3 - 4, k) - 1), 1)] for k in ('total', 'engineering', 'equipment', 'operations', 'other')}
om = lambda i: ttm(i, 'cement_om') + ttm(i, 'mining_om')
out['ttm']['cement_mining_om'] = [round(om(i3), 2), round(100 * (om(i3) / om(i3 - 4) - 1), 1)]

# 5. 在手合同滚动：期初 + 新签 − 期末 = 当季消耗（收入、未生效、取消、折算等合计）
roll = {}
for a, b in zip(names, names[1:]):
    burn = Q[a]['backlog'] + Q[b]['total'] - Q[b]['backlog']
    roll[b] = dict(backlog=round(Q[b]['backlog'], 2), qoq=round(100 * (Q[b]['backlog'] / Q[a]['backlog'] - 1), 2), new=round(Q[b]['total'], 2),
                   burn=round(burn, 2), revenue=Q[b]['revenue_yi'], gap=None if Q[b]['revenue_yi'] is None else round(burn - Q[b]['revenue_yi'], 2))
out['backlog_roll'] = roll
fx_q = Q['2026Q3']['usdcnh_quarter_end'] / Q['2026Q2']['usdcnh_quarter_end'] - 1
fx_y = Q['2026Q3']['usdcnh_quarter_end'] / Q['2025Q3']['usdcnh_quarter_end'] - 1
tr_q = OVERSEAS_BACKLOG_0630 * fx_q
tr_y = Q['2025Q3']['backlog'] * OVERSEAS_BACKLOG_SHARE_2025 * fx_y
out['fx'] = dict(usdcnh_qoq_pct=round(100 * fx_q, 2), usdcnh_yoy_pct=round(100 * fx_y, 2), translation_qoq_yi=round(tr_q, 2),
                 backlog_change_qoq_yi=round(cur['backlog'] - Q['2026Q2']['backlog'], 2),
                 backlog_qoq_ex_fx_pct=round(100 * ((cur['backlog'] - tr_q) / Q['2026Q2']['backlog'] - 1), 2),
                 backlog_yoy_pct=round(100 * (cur['backlog'] / prev['backlog'] - 1), 2),
                 backlog_yoy_ex_fx_pct=round(100 * ((cur['backlog'] - tr_y) / prev['backlog'] - 1), 2),
                 note='假设境外在手合同均按美元计价并按期末汇率折算（公告未说明折算口径），为上限估计')
out['coverage'] = dict(backlog_over_2025_revenue=round(cur['backlog'] / 495.99, 2))

# 6. V 情景：生产池带行（已套研究数）同一引擎与股权桥
band = next(r for r in csv.DictReader((ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv').open(encoding='utf-8-sig')) if r['security_code'] == '600970')
assert not (band.get('exright_note') or '').strip()
nopat, roic0, wacc, g0, g_t = (num(band[k]) for k in ('nopat_ps', 'roic0', 'wacc', 'g0', 'g_terminal'))
iv, ev_ps, nd, shares = num(band['intrinsic_value']), num(band['ev_ps']), num(band['net_debt_ps']), num(band['shares_est'])
base_yi = nopat * shares / 1e8


def ev(k, g):
    r0 = roic0 * k
    return ov.intrinsic_value(nopat * k, r0, g, wacc, roe_terminal=min(wacc + ov.TERMINAL_EXCESS, r0), g_terminal=g_t, **ov.FADE).intrinsic_value


def value(nopat_yi, g):
    return equity_from_ev(band, ev_ps * ev(nopat_yi / base_yi, g) / ev(1.0, g0), nd)


# 订单→毛利的示意换算：2025 年报分部毛利（亿元）× 滚动四季新签同比；运营按运维年费口径，或按 2026H1 实际（收入未随订单增长）取 0
gp = dict(engineering=41.83, equipment=14.44, operations=30.11, other=3.69)
g_orders = dict(engineering=out['ttm']['engineering'][1] / 100, equipment=out['ttm']['equipment'][1] / 100,
                operations=out['ttm']['cement_mining_om'][1] / 100, other=out['ttm']['other'][1] / 100)
d_hi = sum(gp[k] * g_orders[k] for k in gp)
d_lo = sum(gp[k] * (0.0 if k == 'operations' else g_orders[k]) for k in gp)
tax = num(band['tax_rate'])
out['order_bridge'] = dict(gross_profit_2025=gp, ttm_order_growth=g_orders, gp_change_yi=[round(d_lo, 2), round(d_hi, 2)],
                           nopat_change_yi=[round(d_lo * (1 - tax), 2), round(d_hi * (1 - tax), 2)],
                           note='费用不随收入变动、税率取带上 15.47%；只作量级示意，不是预测')
scen = [('生产现值（研究数 32.30 亿，g0 1.93%）', base_yi, g0),
        ('订单换算下沿（运营收入不随订单增长）', base_yi + d_lo * (1 - tax), g0),
        ('订单换算上沿（运营按运维年费增长）', base_yi + d_hi * (1 - tax), g0),
        ('研究悲观档 27.38 亿', 27.38, g0), ('研究乐观档 36.13 亿', 36.13, g0),
        ('研究数不变、g0 取 0', base_yi, 0.0), ('研究数不变、g0 取 3%', base_yi, 0.03),
        ('研究悲观档且 g0 取 0', 27.38, 0.0)]
out['scenarios'] = [dict(name=n, nopat_yi=round(y, 2), g0=round(g, 4), V=round(value(y, g), 4), pv=round(CLOSE / value(y, g), 4),
                         dV_pct=round(100 * (value(y, g) / iv - 1), 2)) for n, y, g in scen]
out['independent_oi259'] = {k: dict(V=v, pv=round(CLOSE / v, 4)) for k, v in (('bear', 7.44), ('base', 9.51), ('bull', 11.23))}
out['buy_line_price'] = round(1.0034 * iv, 2)
(EXP / 'results.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(out, ensure_ascii=False, indent=1))
