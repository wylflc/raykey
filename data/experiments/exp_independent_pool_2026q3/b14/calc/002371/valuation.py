# -*- coding: utf-8 -*-
"""北方华创（002371）独立估值（OI-291 b14，价格日 2026-10-20）。

方法：经济口径（研发全额费用化、股份支付计入成本）的归母所有者收益 DCF，三情景概率加权。
- 经营利润率 = (营收 - 营业成本 - 税金及附加 - 销售 - 管理 - 经济口径研发 + 其他收益 + 减值 + 资产处置) / 营收，
  经济口径研发 = 报表研发费用 + 当期资本化研发 - 计入研发费用的已资本化研发摊销。
- 所有者收益 = (税后经营利润 - 增量经营资本) x (1 - 少数股东占比)；增量经营资本 = c x 营收增量（下降时按 rel 释放）。
- 2027-2036 逐年，2037 起永续 2.5%；年中折现，估值日 2026-10-20。
- 经调整净现金为正，按无杠杆口径：股权价值 = 经营价值 + 经调整净现金 + 非经营资产。
- 每股价值：总股本 7.2782 亿股（腾讯行情口径），在外股票期权按行权法（V 高于行权价才计入，行权款计入股权价值）。
运行：python3 valuation.py
"""

PRICE = 566.49           # 元，2026-10-20 收盘
SHARES = 7.2782          # 亿股，腾讯行情总股本（2026-06-30 资产负债表 7.256892 亿股，差额为 7-10 月期权行权）
COE = 0.09
G_T = 0.025
T_FIRST = 0.70           # 2026-10-20 -> 2027-06-30（年中折现）
T_TV = 10.20             # 2026-10-20 -> 2036-12-31

# ---------------------------------------------------------------- 报表数（亿元）
REV_2025 = 393.531       # 2025_annual_report 第 111 页
REV_TTM = 433.733        # 2025 年 - 2025H1 + 2026H1
PARENT_NP_2025 = 55.220
PARENT_NP_TTM = 56.842   # 55.220 - 32.080 + 33.700
PARENT_EQUITY = 405.449  # 2026H1_report 第 49 页

# 利润表（不含财务费用、投资收益、公允价值变动、营业外）；研发：rd 报表研发费用，cap 资本化，
# rd_total 研发支出合计（附注「研发支出」），rd_input 研发投入（管理层讨论口径）；二者之差视为计入研发费用的已资本化研发摊销
IS = {
    '2025':    dict(rev=393.531, cogs=235.710, tax_s=2.370, sell=16.360, adm=34.334, rd=54.354, oth=12.930,
                    cr=-1.632, ai=-1.530, disp=0.111, cap=25.110, rd_total=79.464, rd_input=72.771),
    '2025H1':  dict(rev=161.415, cogs=93.349, tax_s=0.920, sell=4.653, adm=10.570, rd=20.774, oth=3.983,
                    cr=-0.981, ai=-0.022, disp=0.002, cap=11.408, rd_total=32.183, rd_input=29.154),
    '2026H1':  dict(rev=201.614, cogs=120.831, tax_s=1.233, sell=7.606, adm=13.704, rd=26.772, oth=5.108,
                    cr=-0.656, ai=0.168, disp=0.011, cap=14.293, rd_total=41.065, rd_input=37.056),
}


def ebit(p):
    rep = (p['rev'] - p['cogs'] - p['tax_s'] - p['sell'] - p['adm'] - p['rd']
           + p['oth'] + p['cr'] + p['ai'] + p['disp'])
    net_cap = p['cap'] - (p['rd_total'] - p['rd_input'])
    return rep, rep - net_cap, net_cap


def ttm_ebit():
    r = [ebit(IS[k]) for k in ('2025', '2025H1', '2026H1')]
    return tuple(r[0][i] - r[1][i] + r[2][i] for i in range(3))


# ---------------------------------------------------------------- 经调整净现金（2026-06-30）
CASH = 189.803                    # 货币资金，2026H1_report 第 47 页
RESTRICTED = 0.355                # 保证金，第 23 页
OP_RESERVE = 0.05 * REV_TTM       # 经营备付：TTM 营收 5%
DIV_PAYABLE = 7.745               # 应付股利（含 2025 年度现金红利 5.52 亿，7-03 除息），第 49 页
DEBT = 2.990 + 121.480 + 11.700 + 0.769 + 0.712 + 1.820   # 短借、长借、一年内到期长借/租赁/其他长期负债、租赁负债（第 49、121 页）
DEBT_LIKE = 3.031 + 0.240 + 0.447                         # 票据融资款、委托贷款（第 121 页）、长期应付款
POST_BS = -4.046 + 2.47           # 诺合键维对价 4.05 亿（自有资金）；7-01 后期权行权约 213 万股 x 约 116 元
NET_CASH_ADJ = CASH - RESTRICTED - OP_RESERVE - DIV_PAYABLE - DEBT - DEBT_LIKE + POST_BS
NON_OP = 4.611 + 4.721 + 1.513 + 0.504   # 长期股权投资、其他非流动金融资产、其他权益工具投资、投资性房地产

# ---------------------------------------------------------------- 在外股票期权（亿份，行权价 元/份）
OPTIONS = [
    (0.028, 116.0),    # 2022 年计划首次授予第三期与预留授予剩余（估计）
    (0.1181, 139.63),  # 2024 年计划：注销 501,279 份后约 1,181 万份（第一期可行权 2,952,170 份，2026-10-16 公告）
    (0.1039, 234.98),  # 2025 年计划：10,403,050 份，扣离职 8,000 份
]

# ---------------------------------------------------------------- 情景
# g：2027-2036 营收增速；m：2027-2036 经济口径经营利润率；tax：经营利润税率；mino：少数股东占比；
# c：每 1 元营收增量所需经营资本（营运资本约 0.45 + 固定资产约 0.10）；rel：营收下降时释放比例
SCEN = {
    'bear': dict(p=0.25, rev26=470.0, m26=0.100,
                 g=[-0.05, -0.08, 0.06, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025],
                 m=[0.080, 0.065, 0.085, 0.100, 0.105, 0.110, 0.110, 0.110, 0.110, 0.110],
                 tax=0.12, mino=0.03, c=0.60, rel=0.30,
                 desc='大陆设备开支 2027-2028 回落、国内同业与新进入者价格战，营收 2031 年约 485 亿元（与 2026 年持平），'
                      '经济口径经营利润率由 10% 降至 6.5% 后回到 11%，税率 12%'),
    'base': dict(p=0.50, rev26=480.0, m26=0.110,
                 g=[0.20, 0.16, 0.11, 0.07, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025],
                 m=[0.125, 0.140, 0.155, 0.165, 0.170, 0.175, 0.175, 0.175, 0.175, 0.175],
                 tax=0.10, mino=0.03, c=0.55, rel=0.30,
                 desc='大陆设备开支约 500 亿美元高位持平、国产化率 2031 年约五成、公司占国产份额四成以上，'
                      '营收 2031 年约 833 亿元，研发强度由 18.6% 降至约 15%，经济口径经营利润率升至 17.5%，税率 10%'),
    'bull': dict(p=0.25, rev26=490.0, m26=0.120,
                 g=[0.28, 0.24, 0.18, 0.13, 0.10, 0.09, 0.075, 0.06, 0.045, 0.03],
                 m=[0.145, 0.165, 0.185, 0.200, 0.210, 0.220, 0.220, 0.220, 0.220, 0.220],
                 tax=0.09, mino=0.03, c=0.50, rel=0.30,
                 desc='国产化率 2031 年约六成、先进制程与键合等新品放量并出海，营收 2031 年约 1,141 亿元、2036 年约 1,525 亿元，'
                      '经济口径经营利润率 22%，税率 9%'),
}

# 2026 年正常化归母净利（报表口径，研发资本化照报表）：(营收 x 经济口径利润率 + 净资本化 - 净利息) x (1 - 有效税率) + 少数股东亏损回加
NORM26 = {
    'bear': dict(rev=430.0, m=0.100, net_cap=17.0, net_int=3.0, tax=0.09, mino_addback=2.0),
    'base': dict(rev=480.0, m=0.110, net_cap=21.0, net_int=2.9, tax=0.09, mino_addback=2.5),
    'bull': dict(rev=495.0, m=0.120, net_cap=23.0, net_int=2.8, tax=0.09, mino_addback=2.5),
}


def norm26(k, economic=False):
    s = NORM26[k]
    nc = 0.0 if economic else s['net_cap']
    return (s['rev'] * s['m'] + nc - s['net_int']) * (1 - s['tax']) + s['mino_addback']


def flows(s, g_shift=0.0):
    rev_prev = s['rev26']
    out = []
    for i in range(10):
        rev = rev_prev * (1 + s['g'][i] + g_shift)
        nopat = rev * s['m'][i] * (1 - s['tax'])
        d = rev - rev_prev
        reinv = s['c'] * d if d > 0 else s['rel'] * d
        oe = (nopat - reinv) * (1 - s['mino'])
        out.append(dict(year=2027 + i, rev=rev, nopat=nopat, reinv=reinv, oe=oe))
        rev_prev = rev
    rev_t = rev_prev * (1 + G_T)
    nopat_t = rev_t * s['m'][-1] * (1 - s['tax'])
    reinv_t = s['c'] * (rev_t - rev_prev)
    oe_t = (nopat_t - reinv_t) * (1 - s['mino'])
    return out, dict(rev=rev_t, nopat=nopat_t, reinv=reinv_t, oe=oe_t)


def h2_2026(s):
    nopat = s['rev26'] * s['m26'] * (1 - s['tax'])
    reinv = s['c'] * (s['rev26'] - REV_2025)
    return 0.5 * (nopat - reinv) * (1 - s['mino'])


def equity(s, r, g_shift=0.0):
    fl, term = flows(s, g_shift)
    pv = sum(f['oe'] / (1 + r) ** (T_FIRST + i) for i, f in enumerate(fl))
    pv_tv = term['oe'] / (r - G_T) / (1 + r) ** T_TV
    eq = pv + pv_tv + h2_2026(s) + NET_CASH_ADJ + NON_OP
    return eq, pv, pv_tv


def per_share(eq, options=True):
    v = eq / SHARES
    if not options:
        return v
    for _ in range(100):
        n = sum(q for q, k in OPTIONS if k < v)
        cash = sum(q * k for q, k in OPTIONS if k < v)
        v_new = (eq + cash) / (SHARES + n)
        if abs(v_new - v) < 1e-9:
            break
        v = v_new
    return v


def v_scen(k, r=COE, options=True, g_shift=0.0):
    return per_share(equity(SCEN[k], r, g_shift)[0], options)


def v_weighted(r=COE, weights=None, options=True, scen=None):
    w = weights or {k: SCEN[k]['p'] for k in SCEN}
    total = 0.0
    for k in SCEN:
        s = scen[k] if scen and k in scen else SCEN[k]
        total += w[k] * per_share(equity(s, r)[0], options)
    return total


def solve(f, lo, hi, it=200):
    flo = f(lo)
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def verdict(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


if __name__ == '__main__':
    print('== 经营利润（亿元）：报表口径 / 经济口径（研发全额费用化） / 净资本化')
    for k in IS:
        rep, eco, nc = ebit(IS[k])
        print('  %-7s 报表 %6.2f (%4.1f%%)  经济 %6.2f (%4.1f%%)  净资本化 %5.2f' % (
            k, rep, 100 * rep / IS[k]['rev'], eco, 100 * eco / IS[k]['rev'], nc))
    rep_t, eco_t, nc_t = ttm_ebit()
    print('  TTM     报表 %6.2f (%4.1f%%)  经济 %6.2f (%4.1f%%)  净资本化 %5.2f' % (
        rep_t, 100 * rep_t / REV_TTM, eco_t, 100 * eco_t / REV_TTM, nc_t))

    print('\n== 经调整净现金（亿元）')
    print('  现金 %.2f - 受限 %.2f - 经营备付 %.2f - 应付股利 %.2f - 有息负债 %.2f - 类债务 %.2f + 期后 %.2f = %.2f' % (
        CASH, RESTRICTED, OP_RESERVE, DIV_PAYABLE, DEBT, DEBT_LIKE, POST_BS, NET_CASH_ADJ))
    print('  非经营资产 %.2f；经调整净现金为正，采用无杠杆口径' % NON_OP)

    print('\n== 2026 年正常化归母净利（亿元）：报表口径 / 经济口径')
    for k in ('bear', 'base', 'bull'):
        print('  %-4s 报表 %.1f  经济 %.1f' % (k, norm26(k), norm26(k, economic=True)))

    print('\n== 情景（股权成本 9%，终值增长 2.5%）')
    res = {}
    for k in ('bear', 'base', 'bull'):
        s = SCEN[k]
        eq, pv, pv_tv = equity(s, COE)
        fl, term = flows(s)
        v_opt = per_share(eq)
        v_basic = per_share(eq, options=False)
        res[k] = v_opt
        print('  %-4s p=%.2f 股权价值 %.0f 亿（显性期 %.0f + 终值 %.0f，终值占经营价值 %.0f%%）V=%.1f 元（不计期权 %.1f）' % (
            k, s['p'], eq, pv, pv_tv, 100 * pv_tv / (pv + pv_tv), v_opt, v_basic))
        nopat26 = s['rev26'] * s['m26'] * (1 - s['tax'])
        prev_rev, prev_n = s['rev26'], nopat26 * (1 - s['mino'])
        print('      2026E 营收 %7.1f  归母NOPAT %6.1f  下半年所有者收益 %5.1f' % (s['rev26'], prev_n, h2_2026(s)))
        for i, f in enumerate(fl):
            n = f['nopat'] * (1 - s['mino'])
            if i < 5 or i == 9:
                print('      %d 营收 %7.1f 增速 %5.1f%%  归母NOPAT %6.1f (%+5.1f%%) 再投资 %6.1f 所有者收益 %6.1f 现值 %6.1f' % (
                    f['year'], f['rev'], 100 * (f['rev'] / prev_rev - 1), n, 100 * (n / prev_n - 1),
                    f['reinv'], f['oe'], f['oe'] / (1 + COE) ** (T_FIRST + i)))
            prev_rev, prev_n = f['rev'], n
        sum_re = sum(f['reinv'] for f in fl[:5])
        sum_np = sum(f['nopat'] for f in fl[:5])
        d_np = fl[4]['nopat'] - nopat26
        print('      2027-2031 再投资率 %.1f%%，增量回报（NOPAT 增量 / 累计再投资）%.1f%%' % (
            100 * sum_re / sum_np, 100 * d_np / sum_re))
        print('      终值：2037 营收 %.1f NOPAT %.1f 所有者收益 %.1f，再投资率 %.1f%%，增量回报 %.1f%%' % (
            term['rev'], term['nopat'], term['oe'], 100 * term['reinv'] / term['nopat'],
            100 * s['m'][-1] * (1 - s['tax']) / s['c']))

    vw = sum(SCEN[k]['p'] * res[k] for k in res)
    vw_basic = v_weighted(options=False)
    pv_ratio = PRICE / vw
    print('\n== 结论')
    print('  加权 V = %.1f 元/股（不计期权 %.1f）；P/V = %.2f → %s' % (vw, vw_basic, pv_ratio, verdict(pv_ratio)))
    print('  V 不变时各档价格：明显低估 ≤ %.0f；温和低估 %.0f～%.0f；大致合理 %.0f～%.0f；偏贵 > %.0f' % (
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    v8, v10 = v_weighted(0.08), v_weighted(0.10)
    print('  股权成本 8%%：V = %.1f（P/V %.2f）；10%%：V = %.1f（P/V %.2f）' % (v8, PRICE / v8, v10, PRICE / v10))
    for r in (0.08, 0.10):
        print('    %.0f%% 分情景：' % (100 * r) + '  '.join('%s %.1f' % (k, v_scen(k, r)) for k in ('bear', 'base', 'bull')))

    irr = solve(lambda r: v_scen('base', r) - PRICE, 0.03, 0.12)
    print('  现价隐含回报（基准情景现金流）= %.2f%%' % (100 * irr))
    irr_bull = solve(lambda r: v_scen('bull', r) - PRICE, 0.03, 0.12)
    print('  （参考：牛市情景现金流的隐含回报 = %.2f%%）' % (100 * irr_bull))

    # 反向 DCF（9%）
    dg = solve(lambda d: v_scen('base', COE, g_shift=d) - PRICE, 0.0, 0.30)
    fl_rev, _ = flows(SCEN['base'], dg)
    cagr = (fl_rev[-1]['rev'] / SCEN['base']['rev26']) ** (1 / 10) - 1
    print('  反向 DCF①：沿用基准利润率与资本强度，现价要求 2027-2036 每年增速比基准高 %.1f 个百分点，'
          '即 2036 年营收 %.0f 亿元（2026-2036 年复合 %.1f%%），基准为 %.0f 亿元' % (
              100 * dg, fl_rev[-1]['rev'], 100 * cagr, flows(SCEN['base'])[0][-1]['rev']))
    s = SCEN['base']
    oe0 = s['rev26'] * s['m26'] * (1 - s['tax']) * (1 - s['mino'])

    def eq_needed():
        # 现价对应的股权价值：全部期权行权（现价高于全部行权价）
        n = sum(q for q, k in OPTIONS)
        cash = sum(q * k for q, k in OPTIONS)
        return PRICE * (SHARES + n) - cash
    target_op = eq_needed() - NET_CASH_ADJ - NON_OP

    def pv_const(g):
        pv = sum(oe0 * (1 + g) ** (i + 1) / (1 + COE) ** (T_FIRST + i) for i in range(10))
        oe11 = oe0 * (1 + g) ** 10 * (1 + G_T)
        return pv + oe11 / (COE - G_T) / (1 + COE) ** T_TV
    g_imp = solve(lambda g: pv_const(g) - target_op, 0.0, 0.6)
    print('  反向 DCF②：以 2026E 经济口径归母 NOPAT %.1f 亿元为起点（不扣再投资），现价隐含 10 年年增 %.1f%%，之后 2.5%%' % (
        oe0, 100 * g_imp))

    # 交叉验证
    mcap = PRICE * SHARES
    print('\n== 交叉验证')
    print('  市值 %.0f 亿；市值/TTM 归母 %.1f 倍；市值/2026E 正常化归母（基准 %.1f）%.1f 倍；市值/2026E 经济口径 %.1f 倍' % (
        mcap, mcap / PARENT_NP_TTM, norm26('base'), mcap / norm26('base'), mcap / norm26('base', True)))
    print('  V 对应：2026E 报表口径市盈率 %.1f 倍；市净率 %.2f 倍' % (vw * SHARES / norm26('base'), vw * SHARES / PARENT_EQUITY))
    ev = mcap + 61.729 - NET_CASH_ADJ - NON_OP
    print('  EV（含少数股东权益账面 61.73）%.0f 亿；EV/TTM 报表经营利润 %.1f 倍；EV/TTM 经济口径经营利润 %.1f 倍' % (
        ev, ev / rep_t, ev / eco_t))
    print('  股息率 %.2f%%（2025 年度每股 0.762 元），无回购' % (100 * 0.762 / PRICE))
    stake = 0.1784 * 554.75 * 275.45 / 274.49
    print('  分部加总：芯源微 17.84%% 持股市值约 %.0f 亿（%.1f 元/股）；DCF 内其归母经济收益现值估计不足 5 亿，'
          '按市值替换后 V 约 +%.1f 元' % (stake, stake / SHARES, (stake - 5) / SHARES))

    print('\n== 证伪条件触发后的 V')
    f1 = v_weighted(weights={'bear': 0.40, 'base': 0.50, 'bull': 0.10})
    weak = dict(SCEN['base'])
    weak['m'] = [x - 0.02 for x in SCEN['base']['m']]
    f2 = v_weighted(weights={'bear': 0.35, 'base': 0.50, 'bull': 0.15}, scen={'base': weak})
    f3 = v_weighted(weights={'bear': 0.50, 'base': 0.40, 'bull': 0.10})
    f4 = v_weighted(weights={'bear': 0.10, 'base': 0.50, 'bull': 0.40})
    print('  F1 三季报走弱（熊 40/基 50/牛 10）：V = %.1f' % f1)
    print('  F2 2026 年报利润与毛利不达标（基准利润率 -2pp，熊 35/基 50/牛 15）：V = %.1f' % f2)
    print('  F3 大陆设备开支转跌（熊 50/基 40/牛 10）：V = %.1f' % f3)
    print('  F4 上行：2027H1 高增且经济利润率达标（熊 10/基 50/牛 40）：V = %.1f' % f4)
