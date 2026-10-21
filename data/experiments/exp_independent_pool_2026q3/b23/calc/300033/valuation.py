"""同花顺（300033）独立估值：所有者收益 DCF（归母、无杠杆口径，净现金为正）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。价格日 2026-10-21（北京时间），股权成本基准 9%。
输入出处：2026H1_report（下称 H1）、2025_annual_report（下称 AR）页码为 PDF 物理页；
网络事实见正文「来源」。三季报 2026-10-23 披露前，2026 下半年为估计值。
"""
import math

PRICE = 195.85
SHARES = 7.5264              # 亿股，腾讯行情口径；无回购专户、无拟注销股份（H1 第 30、39 页）
COE = 0.09
T0 = 71 / 365                # 2026-10-21 → 2026-12-31

# ---------------- 2026-06-30 资产负债（H1 第 38-39、85-88、95-96 页） ----------------
CASH_0630 = 124.488          # 货币资金
AGENCY_CASH_0630 = 27.176    # 基金销售、其他代理业务结算资金和保证金（对应其他应付款中代理买卖基金款 26.885）
INTERIM_DIV = 1.505          # 2026 中期每 10 股派 2 元，9-23 除息，已在价格日前流出
RESERVE = 6.0                # 经营备付：约 2 个月现金成本（2026E 成本基数约 35.9 亿）
NONOP = 0.066 + 0.057        # 其他权益工具投资 + 长期股权投资
DEBT = 0.0                   # 无有息负债、无租赁负债（H1 第 39 页）
CL_0630 = 33.534 + 1.183     # 合同负债 + 其他非流动负债中的预收服务费（H1 第 86、88 页）
TAXPAY_0630, PAYROLL_0630 = 1.424, 1.279
TAXPAY_YE, PAYROLL_YE = 4.0, 2.6   # 年末应交税费、应付职工薪酬（AR：3.88、2.32，按规模上调）
CL_RATIO = 0.32              # 年末（合同负债+长期预收）/当年营收：2021-2025 为 0.32/0.30/0.34/0.38/0.31
DA_H2, CAPEX_H2 = 0.40, 1.20

# ---------------- 2026 年估计（H1 实际 + 下半年估计） ----------------
H1_REV, H1_NI, H1_ONEOFF_AT = 26.457, 9.523, 0.179     # H1 第 7-8、42-43 页
H2_REV_2025 = 42.502         # 2025 全年 60.290 − 上半年 17.788（AR 第 7 页）
H2_COST = 18.70              # 下半年成本基数（营业成本+税金+四项费用）：H1 17.16 × 1.09（2023-2025 下半年/上半年 1.09-1.13）
H2_REC_OTHER = 0.15          # 经常性其他收益（软件增值税退税、个税手续费返还）
H2_FIN = 0.70                # 下半年利息净收入
H2_ONEOFF = 0.50             # 下半年政府补助等一次性税前收益（2025 下半年约 1.4）
H2_TAX = 0.10                # 2019-2025 年度实际税率 5%-11%，2025 为 11.1%（含上年汇算 0.42 亿）
YIELD_AT = 0.0126            # 自有现金税后收益率：税前约 1.4%（2026H1 利息 0.81 亿/自有现金约 100 亿，年化 1.6%，存款利率下行）


def project_2026(h2_growth):
    h2_rev = H2_REV_2025 * (1 + h2_growth)
    pretax = h2_rev - H2_COST + H2_REC_OTHER + H2_FIN + H2_ONEOFF + 0.03
    h2_ni = pretax * (1 - H2_TAX)
    ni = H1_NI + h2_ni
    return {'rev': H1_REV + h2_rev, 'h2_rev': h2_rev, 'h2_ni': h2_ni, 'ni': ni,
            'ni_rec': ni - H1_ONEOFF_AT - H2_ONEOFF * (1 - H2_TAX)}


def cash_ye2026(p26):
    """2026 年末自有现金：6-30 自有现金 − 中期股利 + 下半年自由现金流（合同负债季节性回落已扣）。"""
    dwc_h2 = (CL_RATIO * p26['rev'] - CL_0630) + (TAXPAY_YE - TAXPAY_0630) + (PAYROLL_YE - PAYROLL_0630)
    return CASH_0630 - AGENCY_CASH_0630 - INTERIM_DIV + p26['h2_ni'] + DA_H2 - CAPEX_H2 + dwc_h2, dwc_h2


# 三情景：成交额中枢 T*（沪深两市日均，万亿元，2026 年口径）决定 2026 正常化归母净利（含净利息、剔除一次性）
SCEN = {
    'bear': dict(p=0.25, tstar=1.15, h2_growth=0.12, norm_ni=16.0, norm_rev=46.0, g5=0.03, gT=0.020, pers=0.30, capex=0.05),
    'base': dict(p=0.50, tstar=1.45, h2_growth=0.24, norm_ni=24.0, norm_rev=57.0, g5=0.06, gT=0.025, pers=0.45, capex=0.04),
    'bull': dict(p=0.25, tstar=1.85, h2_growth=0.32, norm_ni=33.0, norm_rev=71.6, g5=0.10, gT=0.025, pers=0.60, capex=0.04),
}


def run(sc, coe=COE, oe_override=None):
    """返回每股价值与明细。oe_override=(oe0, g10) 用于反向 DCF：从 oe0 起 10 年匀速 g10、终值 2.5%。"""
    p26 = project_2026(sc['h2_growth'])
    cash, dwc_h2 = cash_ye2026(p26)
    interest = YIELD_AT * cash
    pv_cash = (cash - RESERVE + NONOP - DEBT) / (1 + coe) ** T0
    op_norm = sc['norm_ni'] - interest
    excess_ni = p26['ni_rec'] - sc['norm_ni']
    excess_rev = p26['rev'] - sc['norm_rev']
    rows, pv_oe = [], 0.0
    op_base, rev_base, rev_prev = op_norm, sc['norm_rev'], p26['rev']
    g5, gT = sc['g5'], sc['gT']
    for k in range(1, 11):
        gk = g5 if k <= 5 else g5 + (gT - g5) * (k - 5) / 5
        op_base *= 1 + gk
        rev_base *= 1 + gk
        pers = sc['pers'] if k == 1 else (sc['pers'] / 3 if k == 2 else 0.0)
        op = op_base + pers * excess_ni
        rev = rev_base + pers * excess_rev
        oe = op * (1 - sc['capex']) + CL_RATIO * (rev - rev_prev)
        if oe_override:
            oe0, g10 = oe_override
            oe = oe0 * (1 + g10) ** (k - 1)
        pv = oe / (1 + coe) ** (T0 + k - 0.5)
        pv_oe += pv
        rows.append(dict(year=2026 + k, g=gk, ni=op + interest, rev=rev, oe=oe, pv=pv))
        rev_prev = rev
    if oe_override:
        oe11 = rows[-1]['oe'] * 1.025
        gT_used = 0.025
    else:
        oe11 = op_base * (1 + gT) * (1 - sc['capex']) + CL_RATIO * rev_base * gT
        gT_used = gT
    tv = oe11 / (coe - gT_used)
    pv_tv = tv / (1 + coe) ** (T0 + 9.5)
    equity = pv_cash + pv_oe + pv_tv
    return dict(vps=equity / SHARES, equity=equity, pv_cash=pv_cash, pv_oe=pv_oe, pv_tv=pv_tv,
                tv_share=pv_tv / equity, cash=cash, dwc_h2=dwc_h2, interest=interest, p26=p26, rows=rows)


def weighted(coe=COE):
    return sum(s['p'] * run(s, coe)['vps'] for s in SCEN.values())


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main():
    print('=== 同花顺 300033 独立估值（价格日 2026-10-21，现价 %.2f，总股本 %.4f 亿股）===' % (PRICE, SHARES))
    own_cash_0630 = CASH_0630 - AGENCY_CASH_0630
    net_cash_adj = own_cash_0630 - INTERIM_DIV - RESERVE - DEBT
    print('6-30 自有现金 %.2f；经调整净现金（扣代客资金、中期股利、经营备付）%.2f 亿' % (own_cash_0630, net_cash_adj))
    res = {}
    for name, sc in SCEN.items():
        r = run(sc)
        res[name] = r
        p = r['p26']
        print('\n[%s] p=%.2f  T*=%.2f  2026E 营收 %.1f、归母 %.1f（经常性 %.1f）；下半年营收 %.1f、归母 %.1f'
              % (name, sc['p'], sc['tstar'], p['rev'], p['ni'], p['ni_rec'], p['h2_rev'], p['h2_ni']))
        print('    2026 正常化归母净利 %.1f（营收 %.1f）；年末自有现金 %.1f（下半年营运资本 %.1f）；税后利息 %.2f'
              % (sc['norm_ni'], sc['norm_rev'], r['cash'], r['dwc_h2'], r['interest']))
        for row in r['rows'][:5]:
            print('    %d  增速 %.3f  归母 %.1f  营收 %.1f  所有者收益 %.1f' % (row['year'], row['g'], row['ni'], row['rev'], row['oe']))
        print('    现值：现金 %.1f + 10 年收益 %.1f + 终值 %.1f = %.1f 亿；终值占比 %.1f%%；V = %.2f 元/股'
              % (r['pv_cash'], r['pv_oe'], r['pv_tv'], r['equity'], r['tv_share'] * 100, r['vps']))
    vw = weighted()
    pv = PRICE / vw
    tier = '明显低估' if pv <= 0.75 else '温和低估' if pv <= 0.90 else '大致合理' if pv <= 1.10 else '偏贵或价值陷阱风险高'
    print('\n加权 V = %.2f 元/股；P/V = %.3f（%s）' % (vw, pv, tier))
    print('V 不变时进入各档的价格：≤%.1f 明显低估；≤%.1f 温和低估；≤%.1f 大致合理' % (0.75 * vw, 0.90 * vw, 1.10 * vw))
    for c in (0.08, 0.10):
        parts = {n: run(s, c)['vps'] for n, s in SCEN.items()}
        print('股权成本 %.0f%%：熊 %.2f / 基准 %.2f / 牛 %.2f；加权 %.2f；P/V %.3f'
              % (c * 100, parts['bear'], parts['base'], parts['bull'], weighted(c), PRICE / weighted(c)))
    # 现价隐含回报：基准情景现金流折现等于现价的折现率
    irr_base = solve(lambda r: run(SCEN['base'], r)['vps'], SCEN['base']['gT'] + 1e-4, 0.09, PRICE)
    irr_bull = solve(lambda r: run(SCEN['bull'], r)['vps'], SCEN['bull']['gT'] + 1e-4, 0.09, PRICE)
    print('现价隐含回报：基准情景 %.2f%%；牛市情景 %.2f%%' % (irr_base * 100, irr_bull * 100))
    # 反向 DCF
    b = SCEN['base']
    rb = res['base']
    oe0_norm = (b['norm_ni'] - rb['interest']) * (1 + b['g5']) * (1 - b['capex'])
    oe0_boom = (rb['p26']['ni_rec'] - rb['interest']) * (1 - b['capex'])
    g_norm = solve(lambda g: run(b, COE, (oe0_norm, g))['vps'], -0.05, 0.40, PRICE)
    g_boom = solve(lambda g: run(b, COE, (oe0_boom, g))['vps'], -0.05, 0.40, PRICE)
    ev = PRICE * SHARES - (rb['cash'] - RESERVE + NONOP)
    g_perp = COE - oe0_boom * 1.0 / ev
    print('反向 DCF（9%%，终值 2.5%%）：从正常化起点 %.1f 亿起需 10 年年增 %.1f%%；从 2026E 经常性起点 %.1f 亿起需 %.1f%%；'
          '把 2026E 当永续起点隐含永续增速 %.2f%%' % (oe0_norm, g_norm * 100, oe0_boom, g_boom * 100, g_perp * 100))
    # 交叉验证
    ttm_div_ps = (27.4176 + 1.50528) / SHARES
    print('交叉验证：近 12 个月现金分红 28.92 亿、每股 %.3f 元（按现股本），股息率 %.2f%%；无回购' % (ttm_div_ps, ttm_div_ps / PRICE * 100))
    mcap = PRICE * SHARES
    ev0 = mcap - net_cash_adj
    # TTM 经营 EBIT = TTM 利润总额 − 财务净收益 − 投资收益 − 一次性税前项目（AR 第 7-8、68-69 页；H1 第 7-8、42-43 页）
    ttm_pretax = (36.037 - 5.774) + 10.393
    ttm_fin = 1.248 - 0.719 + 0.760
    ttm_inv = 0.081 - 0.006 + 0.017
    ttm_oneoff = 1.581 - 0.19 + 0.216
    ttm_ebit = ttm_pretax - ttm_fin - ttm_inv - ttm_oneoff
    norm_ebit = (b['norm_ni'] - rb['interest']) / (1 - 0.10)
    print('市值 %.1f 亿；EV（扣 6-30 经调整净现金）%.1f 亿；EV/TTM 经营 EBIT %.1f = %.1fx；EV/正常化经营 EBIT %.1f = %.1fx'
          % (mcap, ev0, ttm_ebit, ev0 / ttm_ebit, norm_ebit, ev0 / norm_ebit))
    print('PE：TTM %.1fx；2026E 经常性 %.1fx；正常化（基准）%.1fx；历史年末 PE 2016-2025 中位数约 39.7x（区间 30.5-84.8x）'
          % (mcap / 36.56, mcap / rb['p26']['ni_rec'], mcap / b['norm_ni']))
    q3_rev, q3_ni = 19.0, 9.1
    print('三季度估计（基准）：营收约 %.1f（同比 %+.0f%%）、归母约 %.1f（同比 %+.0f%%）；四季度 = 下半年 − 三季度：营收 %.1f、归母 %.1f'
          % (q3_rev, (q3_rev / 14.815 - 1) * 100, q3_ni, (q3_ni / 7.043 - 1) * 100,
             rb['p26']['h2_rev'] - q3_rev, rb['p26']['h2_ni'] - q3_ni))
    print('回购专户股份：无（剔除后 V 与 P/V 相同）')
    # 增长路径（基准）
    rows = rb['rows']
    # 2026E 所有者收益：经常性经营利润 × (1 − 资本开支) + 年末预收增量（2025 年末合同负债 17.69 + 长期预收 1.00）
    oe26 = (rb['p26']['ni_rec'] - rb['interest']) * (1 - b['capex']) + (CL_RATIO * rb['p26']['rev'] - (17.69 + 1.00))
    prev = oe26
    gp = []
    for row in rows[:5]:
        gp.append(row['oe'] / prev - 1)
        prev = row['oe']
    print('基准所有者收益：2026E %.1f；2027-2031 增速 %s' % (oe26, ', '.join('%.3f' % g for g in gp)))
    ni_2031_struct = b['norm_ni'] * (1 + b['g5']) ** 5
    capex_sum = sum(b['capex'] * (r['ni'] - rb['interest']) for r in rows[:5])
    print('基准再投资率（净资本开支/经营所有者收益）%.2f；增量回报（2026-2031 正常化利润增量 / 同期净资本开支）%.2f'
          % (b['capex'], (ni_2031_struct - b['norm_ni']) / capex_sum))
    # 证伪触发后的 V（把对应情景设为 100%）
    print('证伪触发后 V：成交额中枢上移（牛市参数）%.2f；监管与回落（熊市参数）%.2f' % (res['bull']['vps'], res['bear']['vps']))
    hi_tax = dict(SCEN['base'])
    hi_tax['norm_ni'] = SCEN['base']['norm_ni'] * (1 - 0.06)
    print('高新资质未续期（基准正常化利润 −6%%）V %.2f' % run(hi_tax)['vps'])
    reg = dict(SCEN['base'])
    reg['norm_ni'], reg['norm_rev'] = 20.0, 52.6
    print('券商导流按新规改为固定计费、广告收入结构性下降约 20%%（基准正常化 20.0）V %.2f' % run(reg)['vps'])
    inelastic = dict(SCEN['base'])
    inelastic['norm_ni'], inelastic['norm_rev'] = 30.0, 66.0
    print('利润对成交额弹性低于假设（基准正常化上调至 30.0）V %.2f' % run(inelastic)['vps'])
    weak_q = dict(SCEN['base'])
    weak_q['h2_growth'], weak_q['pers'] = 0.12, 0.30
    print('三季报偏弱（下半年营收 +12%%、2027 延续 30%%）V %.2f' % run(weak_q)['vps'])
    strong_q = dict(SCEN['base'])
    strong_q['h2_growth'], strong_q['pers'] = 0.32, 0.60
    print('三季报偏强（下半年营收 +32%%、2027 延续 60%%）V %.2f' % run(strong_q)['vps'])
    print('\n--- json 摘要 ---')
    print({'v': {n: round(res[n]['vps'], 2) for n in res}, 'v_weighted': round(vw, 2), 'pv': round(pv, 3),
           'v8': round(weighted(0.08), 2), 'v10': round(weighted(0.10), 2), 'irr': round(irr_base, 4),
           'net_cash_adj': round(net_cash_adj, 2), 'tv_share_base': round(rb['tv_share'], 3),
           'ni2026E_rec': {n: round(res[n]['p26']['ni_rec'], 1) for n in res},
           'oe_growth_base': [round(g, 3) for g in gp]})


if __name__ == '__main__':
    main()
