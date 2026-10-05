"""OI-253 中创智领（601717）分部穿越周期正常化（只读仓库数据，写本目录 segment_history.csv）。

口径：煤机广义 = 煤机板块 + 工业智能板块（恒达智控，2025 年前一直在煤机板块内）+ 总部一般费用，
即 2017-2024 年报两分部表的「煤机板块」口径；2012-2016 年公司只有煤机业务，取模型口径合并 NOPAT（未做研发资本化）。
分部 NOPAT 近似 = 分部净利 − 0.85 ×（非权益法投资收益 + 公允价值变动 − 财务费用净额），与模型 EBIT 剔除金融收益同向。
收入剔除金属材料贸易（毛利率 2%-4% 的过手业务），贸易利润留在 NOPAT 内（约 0.3-0.5 亿/年）。
金额为亿元；出处写在各行注释与 601717_中创智领.md 来源节。
"""
import csv, sys
from pathlib import Path

ROOT = Path('/gpfs/scratch1/shared/zwang/mm_quant/RayKey')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import roic_inputs as ri

years = ri.load_statements({'601717'}, ic_floor=0.1, caliber='nonop', restricted_cash='notes_wc')['601717']
model_raw = {int(p[:4]): years[p].nopat / 1e8 for p in years if p.endswith('12-31') and years[p].nopat is not None}

# 年报主营「贸易」行收入（AR2012-AR2025 分行业表，元→亿）
TRADE = {2012: 15.7323, 2013: 20.4117, 2014: 15.3094, 2015: 8.3530, 2016: 7.3105, 2017: 7.2529, 2018: 15.5089,
         2019: 16.8558, 2020: 21.8490, 2021: 29.9200, 2022: 33.7022, 2023: 28.9505, 2024: 26.8549, 2025: 28.3515}
# 2012-2016 合并营收（data/raw/financials/<年>-12-31.csv）
CONSOL_REV = {2012: 102.1285, 2013: 80.5531, 2014: 61.2446, 2015: 45.1086, 2016: 36.2853}
# 煤机广义分部：(营收, 净利, 需剔除的税前金融收益, 出处)
SEG = {
    2017: (47.5214, 3.3328, -0.237, 'AR2017 分板块表；财务费用 0.757、非权益法投资收益约 0.52'),
    2018: (82.6678, 8.9331, 0.16, 'AR2019 上年列；财务费用 0.08、非权益法投资收益约 0.24（近似）'),
    2019: (95.5159, 16.6233, 0.30, 'AR2019；财务费用 −0.04、理财收益约 0.3（近似）；含坏账冲回 1.86'),
    2020: (114.9497, 25.2530, 0.423, 'AR2020/AR2021；投资收益 0.955 − 权益法约 0.25 + 公允 0.28 − 财务费用 0.562'),
    2021: (130.8309, 21.4180, 1.57, 'AR2021；理财投资收益 2.272 − 权益法约 0.3 − 公允 0.1 − 财务费用约 0.3'),
    2022: (167.5731, 25.4922, 1.149, 'AR2022/AR2023；投资收益 1.028 − 权益法约 0.2 + 公允 0.321'),
    2023: (188.5380, 31.9278, 0.685, 'AR2023；投资收益 2.073 − 权益法约 0.4 + 公允 −0.988'),
    2024: (194.6962, 41.6472, 2.83, 'AR2024 两分部；投资收益 1.376 − 权益法约 0.5 + 公允 2.200 − 财务费用约 0.25'),
    2025: (213.3735, 39.7504, 2.89, 'AR2025 三分部合并：煤机 31.04+工业智能 9.39+抵销 0.09−总部 0.77；营收 191.82+33.31−11.75；'
                                  '投资收益 0.458 − 权益法约 0.4 + 公允 3.729（含信托追回 1.99）− 财务费用 0.897'),
}
TAX = 0.15  # 煤机主体高新技术企业税率

rows = []
for y in range(2012, 2026):
    if y <= 2016:
        rev, nopat, basis = CONSOL_REV[y], model_raw[y], '合并＝煤机（模型口径 NOPAT，未研发资本化）'
    else:
        rev, np_, fin, basis = SEG[y]
        nopat = np_ - (1 - TAX) * fin
    rev_x = rev - TRADE[y]
    rows.append(dict(year=y, seg_revenue=rev, trade_revenue=TRADE[y], revenue_ex_trade=rev_x, nopat=nopat,
                     margin_ex_trade=nopat / rev_x, basis=basis))

# 峰到峰趋势：2012 与 2025 两个剔贸易收入峰连线，作「当期规模」
p0, p1 = rows[0]['revenue_ex_trade'], rows[-1]['revenue_ex_trade']
g_peak = (p1 / p0) ** (1 / 13) - 1
for r in rows:
    r['peak_trend'] = p0 * (1 + g_peak) ** (r['year'] - 2012)
    r['utilization'] = r['revenue_ex_trade'] / r['peak_trend']
    r['nopat_over_trend'] = r['nopat'] / r['peak_trend']

with open(HERE / 'segment_history.csv', 'w', newline='', encoding='utf-8') as fh:
    cols = ['year', 'seg_revenue', 'trade_revenue', 'revenue_ex_trade', 'nopat', 'margin_ex_trade', 'peak_trend',
            'utilization', 'nopat_over_trend', 'model_nopat_raw_consolidated', 'basis']
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for r in rows:
        r['model_nopat_raw_consolidated'] = model_raw[r['year']]
        w.writerow({k: (f"{r[k]:.4f}" if isinstance(r[k], float) else r[k]) for k in cols})

print(f"峰到峰趋势年增 {g_peak:.2%}")
print('year  rev_x   NOPAT  margin  trend   u     NOPAT/trend  model_raw')
for r in rows:
    print(f"{r['year']} {r['revenue_ex_trade']:7.2f} {r['nopat']:6.2f} {r['margin_ex_trade']:6.1%} {r['peak_trend']:7.2f} {r['utilization']:5.2f} {r['nopat_over_trend']:8.4f}   {model_raw[r['year']]:6.2f}")

scale = rows[-1]['peak_trend']
up = [r for r in rows if r['year'] >= 2019]; dn = [r for r in rows if 2013 <= r['year'] <= 2018]
ku = sum(r['nopat_over_trend'] for r in up) / len(up); kd = sum(r['nopat_over_trend'] for r in dn) / len(dn)
uu = sum(r['utilization'] for r in up) / len(up); ud = sum(r['utilization'] for r in dn) / len(dn)
print(f"上行段 2019-2025：u {uu:.3f}、NOPAT/趋势 {ku:.4f}；下行段 2013-2018：u {ud:.3f}、NOPAT/趋势 {kd:.4f}")

def scen(n_bust, k_bust, u_bust, n_good):
    k = (n_bust * k_bust + n_good * ku) / (n_bust + n_good)
    u = (n_bust * u_bust + n_good * uu) / (n_bust + n_good)
    return k, u

full_k = sum(r['nopat_over_trend'] for r in rows) / len(rows)
full_u = sum(r['utilization'] for r in rows) / len(rows)
scenarios = {
    '复刻 2012-2025 全周期（深度下行 6 年）': (full_k, full_u),
    '温和下行（4 年，u≈0.55、利润率≈11%）': scen(4, 0.06, 0.55, 8),
    '轻度下行（3 年，u≈0.60、利润率≈12%）': scen(3, 0.07, 0.60, 7),
}
print(f"\n煤机广义正常化（2025 规模 {scale:.1f} 亿，剔贸易）：")
for name, (k, u) in scenarios.items():
    print(f"  {name}: 收入 {u * scale:6.1f} × 利润率 {k / u:5.1%} = {k * scale:5.2f} 亿")
kc = (scenarios['复刻 2012-2025 全周期（深度下行 6 年）'][0] + scenarios['温和下行（4 年，u≈0.55、利润率≈11%）'][0]) / 2
uc = (scenarios['复刻 2012-2025 全周期（深度下行 6 年）'][1] + scenarios['温和下行（4 年，u≈0.55、利润率≈11%）'][1]) / 2
coal = {'low': full_k * scale, 'mid': kc * scale, 'high': scenarios['轻度下行（3 年，u≈0.60、利润率≈12%）'][0] * scale}
print(f"  中值＝复刻与温和各半: 收入 {uc * scale:.1f} × 利润率 {kc / uc:.1%} = {coal['mid']:.2f} 亿")

# 汽车零部件：模型口径 NOPAT ≈ 分部净利 +（财务费用 − 投资收益 − 公允价值）× 0.8；与「合并模型 NOPAT − 煤机广义 − 总部特殊项」互验
AUTO = {2023: (2.7630, -0.811, 0.423, 1.40, 0.44), 2024: (2.5697, 0.110, -0.723, 1.219, 0.0), 2025: (3.8195, 0.266, 0.667, 1.781, 0.8828)}
HQ_SPECIAL = {2023: 0.0, 2024: -2.0210, 2025: 0.0}
print('\n汽车零部件（亿）：年  直接法  残差法  剔商誉减值')
coal_by_year = {r['year']: r['nopat'] for r in rows}
for y, (np_, inv, fv, fe, gw) in AUTO.items():
    direct = np_ - 0.8 * (inv + fv - fe)
    resid = model_raw[y] - coal_by_year[y] - HQ_SPECIAL[y]
    print(f"  {y}  {direct:5.2f}  {resid:5.2f}  {direct + gw:5.2f}/{resid + gw:5.2f}")
# TTM（2025H2 + 2026H1）剔一次性：2025H2 净利 3.82−2.95=0.87，加回双环商誉减值 0.88；2026H1 净利 4.22，
# 扣双环土地收储处置收益 1.265×0.85≈1.08（问询回复 2.1：汽零 H1 增利主要来自此项）；金融项按 2025 全年 +0.68 计
ttm_auto = (3.8195 - 2.9484 + 0.8828) + (4.2175 - 1.265 * 0.85) + 0.678
print(f"  TTM 剔一次性 ≈ {ttm_auto:.2f}")
auto = {'low': 4.0, 'mid': 5.3, 'high': round(ttm_auto, 1)}
rd = {'low': 0.5, 'mid': 1.0, 'high': 1.5}
print('\n合计（模型口径，研发资本化后）：')
shares = 17.85399930
for k in ('low', 'mid', 'high'):
    tot = coal[k] + auto[k] + rd[k]
    parent = (tot - (43.44 - 43.57)) * (1 - 0.0562)
    print(f"  {k:4s}: 煤机广义 {coal[k]:5.2f} + 汽零 {auto[k]:.1f} + 研发资本化 {rd[k]:.1f} = {tot:5.2f} 亿（每股 {tot / shares:.3f} 元；股权桥反推归母约 {parent:.1f} 亿）")
