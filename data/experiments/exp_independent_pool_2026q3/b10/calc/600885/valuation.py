#!/usr/bin/env python3
"""宏发股份（600885）独立估值：归母所有者收益 DCF（熊／基准／牛三情景）。

运行：python3 valuation.py
输入全部写在本脚本内（金额单位亿元，每股为元）。来源：
  2026H1_report 第 7、13、42-47、50-51、106-107、155-157、162-163 页；
  2025_annual_report 第 21-22、202-205 页；2026H1_report 母公司注释（第 19 节）。
估值基准日先取 2026-06-30（最新资产负债表），再按股权成本滚动到价格日 2026-10-20。
"""

PRICE = 29.35          # 2026-10-20 收盘价
SHARES = 15.4759       # 亿股，总股本；无回购专户股份，无拟注销股份
COE = 0.09
ROLL_YEARS = 112 / 365  # 2026-06-30 -> 2026-10-20

# ---- 归母比例与税率 ----
PARENT_SHARE = 0.762   # 归母净利 / 合并净利：2026H1 11.56/15.15=76.3%；上市公司持宏发电声 79.9999%
TAX = 0.125            # 2023-2026H1 有效税率 11.5%-14.5%

# ---- 经调整净现金（2026-06-30，合并口径）----
CASH_LIKE = 26.95 + 2.61 + 0.02          # 货币资金（含大额存单 8.30）+ 交易性金融资产 + 衍生金融资产
DEBT = 8.70 + 1.55 + 0.48 + 0.62 + 0.09  # 短借 + 长借 + 一年内到期 + 租赁负债 + 衍生金融负债
RESTRICTED = 0.0001                      # 受限保证金 1.02 万元
MINORITY_DIV_PAYABLE = 2.04              # 应付股利（子公司已宣派、应付少数股东）
TTM_REVENUE = 198.77
OP_RESERVE = 0.02 * TTM_REVENUE          # 经营备付：TTM 营收 2%
PARENT_CLAIMS = 12.32                    # 母公司对宏发电声的应收股利 4.62 + 往来款 7.70（100% 归母）
NON_OP_GROUP = 0.13                      # 长期股权投资

group_net_cash_adj = CASH_LIKE - RESTRICTED - DEBT - MINORITY_DIV_PAYABLE - OP_RESERVE
# 母公司债权全额归母；其余合并净现金按归母比例分摊（宏发电声对母公司的负债由其全体股东承担）
NET_CASH_PARENT = PARENT_CLAIMS + PARENT_SHARE * (group_net_cash_adj - PARENT_CLAIMS)
NON_OP_PARENT = PARENT_SHARE * NON_OP_GROUP

# 对照：2025-12-31 年末口径（扣 2025 年度已宣派现金分红 5.37 亿）与 6-30 口径的平均，消除上半年季节性占款
YE_CASH_LIKE = 36.24 + 3.01 + 0.31
YE_DEBT = 6.02 + 1.69 + 0.75 + 0.55 + 0.09
YE_MINORITY_DIV = 1.66
YE_PARENT_CLAIMS = 9.82 + 7.81
YE_GROUP_ADJ = YE_CASH_LIKE - YE_DEBT - YE_MINORITY_DIV - 0.02 * 172.02
YE_NET_CASH_PARENT = YE_PARENT_CLAIMS + PARENT_SHARE * (YE_GROUP_ADJ - YE_PARENT_CLAIMS) - 0.347 * SHARES
NET_CASH_SEASONAL_AVG = (NET_CASH_PARENT + YE_NET_CASH_PARENT) / 2

# ---- 2026 年正常化归母净利 = 正常化营收 × 正常化核心利润率 × (1-税率) × 归母比例 ----
# 核心利润率 = (营业利润 + 财务费用 - 投资收益 - 公允价值变动 - 非经常性补助等) / 营收，含正常减值，不含汇兑
SCEN = {
    'bear': dict(p=0.25, rev=205.0, margin=0.148,
                 g=[0.03, 0.05, 0.05, 0.05, 0.04], ronic=0.14, gT=0.020, ronicT=0.12,
                 note='2026 景气回落约 8%（储能、高温家电、补贴退坡），铜价高位与高压直流价格战使核心利润率停在 14.8%；'
                      '此后增速 3%-5%，增量回报 14%，终值增长 2%'),
    'base': dict(p=0.50, rev=215.0, margin=0.156,
                 g=[0.11, 0.10, 0.09, 0.08, 0.08], ronic=0.20, gT=0.025, ronicT=0.15,
                 note='剔除约 3% 的一次性需求（高温、储能抢装），核心利润率 15.6%（2026H1 剔除汇兑与异常存货减值 16.05%，'
                      '下半年季节性偏低；2019-2025 剔补助均值约 16.4%）；增速 11% 降到 8%，增量回报 20%，终值 2.5%'),
    'bull': dict(p=0.25, rev=222.0, margin=0.166,
                 g=[0.15, 0.14, 0.13, 0.12, 0.11], ronic=0.25, gT=0.025, ronicT=0.18,
                 note='2026 营收即为新常态，银价自高点回落、提价落地，核心利润率回到 16.6%；数据中心、储能、'
                      '高压直流与新门类维持 11%-15% 增长，增量回报 25%'),
}
YEARS = list(range(2027, 2037))  # 显式期 10 年：前 5 年为情景增速，后 5 年线性衰减到终值增速


def normalized_np(s):
    return s['rev'] * s['margin'] * (1 - TAX) * PARENT_SHARE


def growth_path(s):
    g5 = list(s['g'])
    fade = [g5[-1] + (s['gT'] - g5[-1]) * k / 5 for k in range(1, 6)]
    ron5 = [s['ronic']] * 5
    ronf = [s['ronic'] + (s['ronicT'] - s['ronic']) * k / 5 for k in range(1, 6)]
    return g5 + fade, ron5 + ronf


def dcf(s, r, np26=None, roll=True, detail=False, path=None, net_cash=None):
    """所有者收益 OE_t = NP_t × (1 - g_{t+1}/增量回报)。2026 下半年取半年，年中贴现。"""
    gs, rons = growth_path(s) if path is None else path
    np_t = normalized_np(s) if np26 is None else np26
    nc = NET_CASH_PARENT if net_cash is None else net_cash
    rows = []
    oe26 = np_t * (1 - gs[0] / rons[0])
    pv = 0.5 * oe26 / (1 + r) ** 0.25
    rows.append((2026, np_t, None, 1 - gs[0] / rons[0], 0.5 * oe26))
    for i, yr in enumerate(YEARS):
        np_t *= 1 + gs[i]
        g_next = gs[i + 1] if i + 1 < len(YEARS) else s['gT']
        ron_next = rons[i + 1] if i + 1 < len(YEARS) else s['ronicT']
        payout = 1 - g_next / ron_next
        oe = np_t * payout
        pv += oe / (1 + r) ** (i + 1)
        rows.append((yr, np_t, gs[i], payout, oe))
    np_next = np_t * (1 + s['gT'])
    oe_next = np_next * (1 - s['gT'] / s['ronicT'])
    tv = oe_next / (r - s['gT'])
    pv_tv = tv / (1 + r) ** 10.5
    equity = pv + pv_tv + nc + NON_OP_PARENT
    if roll:
        equity *= (1 + r) ** ROLL_YEARS
    v = equity / SHARES
    if detail:
        return v, dict(pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv), rows=rows)
    return v


def weighted(r, probs=None):
    probs = probs or {k: SCEN[k]['p'] for k in SCEN}
    return sum(probs[k] * dcf(SCEN[k], r) for k in SCEN)


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def tier(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def main():
    print('== 宏发股份 600885 独立估值（价格日 2026-10-20，现价 %.2f 元，总股本 %.4f 亿股）==' % (PRICE, SHARES))
    print('合并经调整净现金 %.2f 亿；归母经调整净现金 %.2f 亿（含母公司对宏发电声债权 %.2f 亿）；非经营资产 %.2f 亿'
          % (group_net_cash_adj, NET_CASH_PARENT, PARENT_CLAIMS, NON_OP_PARENT))
    print('经调整净现金为正：按无杠杆口径全额扣除有息负债；无在外可转债（宏发转债 2025-12-12 赎回完毕）；无回购专户股份')
    print()
    for k, s in SCEN.items():
        v, d = dcf(s, COE, detail=True)
        print('[%s] 概率 %.2f  2026 正常化营收 %.1f  核心利润率 %.1f%%  正常化归母净利 %.2f 亿'
              % (k, s['p'], s['rev'], s['margin'] * 100, normalized_np(s)))
        print('    V = %.2f 元  P/V = %.3f  显式期现值 %.1f 亿  终值现值 %.1f 亿  终值占比 %.0f%%'
              % (v, PRICE / v, d['pv_explicit'], d['pv_tv'], d['tv_share'] * 100))
        for yr, np_t, g, payout, oe in d['rows'][:6]:
            gtxt = '  —  ' if g is None else '%5.1f%%' % (g * 100)
            print('    %d  归母净利 %6.2f  增速 %s  所有者收益/净利 %4.0f%%  所有者收益 %6.2f%s'
                  % (yr, np_t, gtxt, payout * 100, oe, '（下半年）' if yr == 2026 else ''))
    _, d = dcf(SCEN['base'], COE, detail=True)
    rows = d['rows']
    np26 = rows[0][1]
    cagr5 = (rows[5][1] / np26) ** (1 / 5) - 1
    cagr10 = (rows[10][1] / np26) ** (1 / 10) - 1
    rr = sum(1 - r[3] for r in rows[:6]) / 6
    print('基准情景归母净利复合增速：5 年 %.1f%%，10 年 %.1f%%；2026-2031 年平均再投资率 %.0f%%'
          % (cagr5 * 100, cagr10 * 100, rr * 100))
    # 历史再投资与增量回报（数据包年度表，合并口径）
    np_hist = {2013: 3.28 + 1.44, 2019: 7.04 + 2.60, 2025: 17.58 + 5.81}
    np_sum_14_25 = 156.82
    ocf_14_25, capex_14_25 = 159.43, 103.55
    fcf = ocf_14_25 - capex_14_25
    reinv = np_sum_14_25 - fcf
    print('2014-2025：累计合并净利 %.1f、自由现金流 %.1f、再投资率 %.0f%%、增量回报 %.1f%%'
          % (np_sum_14_25, fcf, reinv / np_sum_14_25 * 100, (np_hist[2025] - np_hist[2013]) / reinv * 100))
    vw = weighted(COE)
    pv = PRICE / vw
    print()
    print('概率加权 V = %.2f 元；P/V = %.3f（%s）' % (vw, pv, tier(pv)))
    print('V 不变时的分档价格：≤ %.2f 明显低估；%.2f-%.2f 温和低估；%.2f-%.2f 大致合理；> %.2f 偏贵'
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    for r in (0.08, 0.10):
        print('股权成本 %.0f%%：加权 V = %.2f 元（熊 %.2f／基准 %.2f／牛 %.2f）'
              % (r * 100, weighted(r), dcf(SCEN['bear'], r), dcf(SCEN['base'], r), dcf(SCEN['bull'], r)))

    vw_seasonal = sum(SCEN[k]['p'] * dcf(SCEN[k], COE, net_cash=NET_CASH_SEASONAL_AVG) for k in SCEN)
    print('对照：归母净现金取 6-30 与年末（扣分红）平均 %.2f 亿时，加权 V = %.2f 元，P/V = %.3f'
          % (NET_CASH_SEASONAL_AVG, vw_seasonal, PRICE / vw_seasonal))
    vw_nores = sum(SCEN[k]['p'] * dcf(SCEN[k], COE, net_cash=NET_CASH_PARENT + PARENT_SHARE * OP_RESERVE) for k in SCEN)
    print('对照：不扣经营备付时，加权 V = %.2f 元，P/V = %.3f' % (vw_nores, PRICE / vw_nores))

    # 现价隐含回报：基准情景现金流（含终值与净现金）使现值等于现价的折现率
    irr = solve(lambda r: dcf(SCEN['base'], r), 0.05, 0.20, PRICE)
    print('现价隐含回报（基准情景）= %.2f%%' % (irr * 100))

    # 反向 DCF 1：基准正常化净利与增量回报不变，10 年恒定增速 g（随后终值 2.5%）
    base = SCEN['base']

    def v_const_growth(g):
        return dcf(base, COE, path=([g] * 10, [base['ronic']] * 10))
    g10 = solve(v_const_growth, 0.0, 0.30, PRICE)
    print('反向 DCF：现价隐含 2027-2036 年归母净利恒定增速 %.1f%%（增量回报 20%%，终值 2.5%%）' % (g10 * 100))

    # 反向 DCF 2：永续增长（OE = NP×(1+g)×(1-g/ROE)，ROE 取 20%）
    np26 = normalized_np(base)
    eq_now = PRICE * SHARES / (1 + COE) ** ROLL_YEARS - NET_CASH_PARENT - NON_OP_PARENT

    def v_perp(g):
        return np26 * (1 + g) * (1 - g / base['ronic']) / (COE - g)
    gp = solve(v_perp, 0.0, 0.085, eq_now)
    print('反向 DCF：现价隐含永续增速 %.2f%%（增量回报 20%%）' % (gp * 100))

    # 交叉验证
    mcap = PRICE * SHARES
    print()
    print('市值 %.1f 亿；市值/正常化归母（基准）%.1f 倍；基准 V 对应 %.1f 倍；市值/TTM 归母 19.49 = %.1f 倍'
          % (mcap, mcap / np26, dcf(base, COE) * SHARES / np26, mcap / 19.49))
    minority_mkt = mcap * (1 - PARENT_SHARE) / PARENT_SHARE
    ev = mcap + minority_mkt + DEBT - CASH_LIKE
    ebit_ttm = 12.66 + 18.01  # 2025H2 + 2026H1 核心 EBIT（营业利润+财务费用-投资收益-公允价值变动）
    ebit_26 = 222.0 * 0.1535 + 1.3  # 2026E：核心利润率 15.35% + 补助
    print('EV（含少数股东按同倍数估值）%.0f 亿；EV/TTM 核心 EBIT %.1f 倍；EV/2026E EBIT %.1f 倍' % (ev, ev / ebit_ttm, ev / ebit_26))
    print('股息率 %.2f%%（0.347 元，近 12 个月无回购）；PB %.2f 倍（归母权益 132.12 亿）'
          % (0.347 / PRICE * 100, mcap / 132.12))

    # 证伪条件触发后的 V
    print()
    f_margin = weighted(COE, {'bear': 0.45, 'base': 0.45, 'bull': 0.10})
    f_cash = weighted(COE, {'bear': 0.50, 'base': 0.40, 'bull': 0.10})
    f_bust = dcf(SCEN['bear'], COE)
    f_gov = 0.9 * vw
    f_bull = weighted(COE, {'bear': 0.10, 'base': 0.50, 'bull': 0.40})
    print('证伪 1（三季度单季毛利率 < 32.0%% 且单季归母 < 5.5 亿）触发后 V = %.2f' % f_margin)
    print('证伪 2（2026 扣非归母 < 20.0 亿或经营现金流 < 19 亿）触发后 V = %.2f' % f_cash)
    print('证伪 3（2027H1 营收同比 < 5%% 且毛利率 < 32.5%%）触发后 V = %.2f（熊情景）' % f_bust)
    print('证伪 4（宏发电声 20%% 股权落入关联方或公司以 > 25 倍市盈率高价收购，或 2026 少数股东损益占比 > 27%%）触发后 V = %.2f' % f_gov)
    print('反向核对（2026 扣非归母 ≥ 23 亿且毛利率 ≥ 34%%）V = %.2f' % f_bull)


if __name__ == '__main__':
    main()
