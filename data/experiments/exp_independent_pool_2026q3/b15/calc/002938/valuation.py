#!/usr/bin/env python3
"""鹏鼎控股（002938）独立估值（OI-291 b15，价格日 2026-10-20）。

运行：python3 valuation.py
输入全部写在脚本内（单位：亿元；每股价值与价格为元/股）。
口径：
- 所有者收益 OE = 正常化归母净利 + 折旧摊销 − 资本开支 − 营运资本增量；
  2026H2–2028 扩产期 OE 为负，按 9% 股权成本折现（等同按公允价补充权益资金），
  定增现金另计流入、新股计入股本（"定增后"口径，为主口径）。
- 两段业务：存量（通讯 + 消费电子及计算机 + 其他，A 客户为主）与
  算力/汽车（汽车/服务器用板：AI 服务器、高速光模块、汽车）。
- 正常化：剔除公允价值变动、处置、非经常性补助，汇兑损益归零（长期期望为零）。
- 经调整净现金为负（−1.92 亿）→ 按框架用有杠杆口径（净负债滚动、扣税后利息现值），
  并列无杠杆口径对照。
"""

PRICE = 73.85
SHARES = 23.1754          # 亿股，腾讯行情口径（无回购专户股份，新回购用于股权激励、不注销）
COE = 0.09
T0 = 2026.80              # 估值日 2026-10-20

# ---------- 资产负债表（2026-06-30，2026H1_report 第 82–83、104–105 页）----------
CASH = 106.68
RESTRICTED = 0.08          # 银行保函保证金 0.0695 + 海关保证金 0.009
OP_RESERVE = 20.0          # 经营备付：约 5% TTM 营收（399.89），约 3 周现金成本
DEBT = 68.95 + 16.62 + 0.59 + 0.75   # 短借 + 长借 + 一年内到期 + 租赁负债 = 86.91
SHENGXIN_PAYABLE = 1.6087  # 收购晟新 23.53% 股权价款，2026-08-04 尚未支付
NET_CASH_ADJ = CASH - RESTRICTED - OP_RESERVE - DEBT - SHENGXIN_PAYABLE
DEBT_RATE = 0.0245         # H1 借款利息 0.80 亿 ÷ 平均有息负债 65.3 亿 × 2
TAX_ON_INTEREST = 0.15

# 非经营资产：其他权益工具投资 33.80（礼鼎半导体 18.22 为主）×0.75；
# 其他非流动金融资产 7.91（基金）×0.80；长期股权投资 0.19
NONOP = 33.80 * 0.75 + 7.91 * 0.80 + 0.19

# ---------- 定增（募集说明书 第 3–4、72–73 页）----------
PLACE_GROSS = 96.0
PLACE_FEE = 0.5
PLACE_PRICE_RATIO = 0.82   # 发行价 ≥ 发行期首日前 20 日均价 80%，取现价 × 0.82
PLACE_T = 2027.20          # 预计到账（2027 年一季度）
PLACE_CAP = 2.317537       # 上限：发行前总股本 10%


def placement(price_issue=None):
    p = price_issue if price_issue else PRICE * PLACE_PRICE_RATIO
    net = PLACE_GROSS - PLACE_FEE
    n = min(PLACE_GROSS / p, PLACE_CAP)
    if n == PLACE_CAP:
        net = PLACE_CAP * p - PLACE_FEE
    return net, n, p


# ---------- 2026 已知部分 ----------
H1_NORM_NP = 8.92 + 4.48 * (1 - 0.15)   # 扣非 8.92 + 汇兑损失 4.48 税后加回 = 12.73
H2_2025_NORM_NP = 23.86 + 1.77 * 0.87    # 扣非 23.86 + H2 汇兑损失税后加回
REV_2025 = 391.47
REV_H1_LEG = 100.48 + 47.42 + 1.61       # 存量业务 H1 2026
REV_H1_AI = 22.67
NET_INT_2026 = 0.92                       # 2026 净利息收入税后（H1 0.86 税前，H2 约 0.2）
DA_H2_2026 = 19.1                         # H1 17.42
ROIC_DEN = 0.70                           # 终值期投入资本 ≈ 0.70 × 收入（固定资产 0.60 + 营运资本 0.10）
NWC_RATE = 0.10                           # 营运资本增量 = 10% × 收入增量

SCEN = {
    'bear': dict(
        p=0.25,
        h2_leg=219.0, h2_ai=31.0, m26_leg=0.082, m26_ai=0.125, capex_h2=58.0,
        leg_g=[-0.03, -0.03, -0.02, 0.0, 0.0, 0.005, 0.005, 0.005, 0.005],
        ai_rev=[78, 95, 108, 118, 125],          # 2027–2031
        ai_g_late=[0.02, 0.02, 0.02, 0.02],      # 2032–2035
        m_leg=[0.075] * 9,
        m_ai=[0.09, 0.06, 0.06, 0.07, 0.08, 0.08, 0.08, 0.08, 0.08],
        capex=[95, 60, 50, 50, 50], da=[43, 49, 52, 53, 53],
        gT=0.015,
        text='A 客户份额与单价下滑，存量收入 2027–2029 年降 3%/3%/2%、净利率 7.5%；'
             'AI 扩产与同业 800 亿新增产能撞上需求放缓，算力/汽车收入 2031 年仅 125 亿、净利率 2028–2029 年 6%、2030 年 7%、2031 年起 8%；'
             '资本开支 2027 年后压缩；终值增长 1.5%'),
    'base': dict(
        p=0.50,
        h2_leg=221.7, h2_ai=33.0, m26_leg=0.086, m26_ai=0.138, capex_h2=61.0,
        leg_g=[0.03, 0.025, 0.025, 0.025, 0.025, 0.02, 0.02, 0.02, 0.02],
        ai_rev=[105, 165, 220, 260, 290],
        ai_g_late=[0.07, 0.05, 0.04, 0.03],
        m_leg=[0.088] * 9,
        m_ai=[0.12, 0.125, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13],
        capex=[115, 95, 75, 65, 62], da=[44, 52, 58, 61, 62],
        gT=0.025,
        text='存量业务随 A 客户年增 2–3%、净利率 8.8%（2024–2025 剔除利息与汇兑的中枢）；'
             '十余座在建厂房 2027 年起投产，算力/汽车收入 2031 年 290 亿、净利率 13%'
             '（募投测算达产期平均 12.63%）；资本开支 2027–2031 年 412 亿；终值增长 2.5%'),
    'bull': dict(
        p=0.25,
        h2_leg=223.0, h2_ai=35.0, m26_leg=0.090, m26_ai=0.150, capex_h2=64.0,
        leg_g=[0.04, 0.04, 0.04, 0.04, 0.04, 0.025, 0.025, 0.025, 0.025],
        ai_rev=[115, 200, 290, 370, 430],
        ai_g_late=[0.10, 0.08, 0.06, 0.04],
        m_leg=[0.098] * 9,
        m_ai=[0.14, 0.16, 0.17, 0.17, 0.17, 0.17, 0.17, 0.17, 0.17],
        capex=[135, 125, 105, 85, 75], da=[45, 55, 65, 72, 76],
        gT=0.025,
        text='折叠屏与 AI 终端带动存量年增 4%、净利率 9.8%；算力份额与同业相当、价格维持，'
             '算力/汽车收入 2031 年 430 亿、净利率 17%（接近同业景气期）；资本开支 2027–2031 年 525 亿；终值增长 2.5%'),
}


def build(s):
    """返回逐年明细（2026H2、2027–2035）与终值所需量。"""
    rev_leg26 = REV_H1_LEG + s['h2_leg']
    rev_ai26 = REV_H1_AI + s['h2_ai']
    np26 = rev_leg26 * s['m26_leg'] + rev_ai26 * s['m26_ai'] + NET_INT_2026
    rows = []
    rev26 = rev_leg26 + rev_ai26
    oe_h2 = (np26 - H1_NORM_NP) + DA_H2_2026 - s['capex_h2'] - NWC_RATE * (rev26 - REV_2025) * 0.5
    rows.append(dict(year='2026H2', t=0.0, rev_leg=rev_leg26, rev_ai=rev_ai26, rev=rev26,
                     np=np26, np_period=np26 - H1_NORM_NP, da=DA_H2_2026, capex=s['capex_h2'],
                     oe=oe_h2))
    leg, ai, rev_prev = rev_leg26, rev_ai26, rev26
    da_prev = s['da'][-1]
    for i, y in enumerate(range(2027, 2036)):
        leg = leg * (1 + s['leg_g'][i])
        ai = s['ai_rev'][i] if i < 5 else ai * (1 + s['ai_g_late'][i - 5])
        rev = leg + ai
        np_ = leg * s['m_leg'][i] + ai * s['m_ai'][i]
        if i < 5:
            da, capex = s['da'][i], s['capex'][i]
        else:
            da = da_prev * 1.02
            capex = da + 0.60 * (rev - rev_prev)
        da_prev = da
        oe = np_ + da - capex - NWC_RATE * (rev - rev_prev)
        rows.append(dict(year=y, t=(y + 0.5) - T0, rev_leg=leg, rev_ai=ai, rev=rev, np=np_,
                         np_period=np_, da=da, capex=capex, oe=oe))
        rev_prev = rev
    last = rows[-1]
    roic_T = last['np'] / (ROIC_DEN * last['rev'])
    return rows, roic_T, np26


def pv_ops(s, r):
    rows, roic_T, _ = build(s)
    gT = s['gT']
    pv = sum(x['oe'] / (1 + r) ** x['t'] for x in rows)
    last = rows[-1]
    oe_T1 = last['np'] * (1 + gT) * (1 - gT / roic_T)
    tv = oe_T1 / (r - gT)
    t_tv = 2036.0 - T0
    pv_tv = tv / (1 + r) ** t_tv
    return pv + pv_tv, pv_tv, rows, roic_T


def per_share(s, r=COE, place=True, levered=True, price_issue=None):
    ops, pv_tv, rows, roic_T = pv_ops(s, r)
    if levered and NET_CASH_ADJ < 0:
        netdebt = -NET_CASH_ADJ
        cash_term = -(netdebt * DEBT_RATE * (1 - TAX_ON_INTEREST)) / r   # 净负债滚动，扣税后利息现值
    else:
        cash_term = NET_CASH_ADJ
    eq = ops + cash_term + NONOP
    n_sh = SHARES
    if place:
        net, n, _ = placement(price_issue)
        eq += net / (1 + r) ** (PLACE_T - T0)
        n_sh += n
    return eq / n_sh, dict(ops=ops, pv_tv=pv_tv, cash_term=cash_term, eq=eq, n_sh=n_sh,
                           rows=rows, roic_T=roic_T)


def weighted(r=COE, weights=None, **kw):
    w = weights or {k: v['p'] for k, v in SCEN.items()}
    return sum(w[k] * per_share(SCEN[k], r, **kw)[0] for k in SCEN)


def solve(f, lo, hi, target=0.0, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    s = SCEN['base']
    return solve(lambda r: per_share(s, r)[0], 0.03, 0.20, target=PRICE)


def reverse_dcf():
    """现价隐含：以 2026 正常化归母净利（基准，含净利息）为起点所有者收益，
    10 年增速 g 后按 2.5% 永续，求 g；另求恒定永续增速。均用定增前股本、无杠杆净现金口径。"""
    oe0 = build(SCEN['base'])[2]
    target = PRICE * SHARES - NET_CASH_ADJ - NONOP

    def val(g):
        pv = 0.0
        oe = oe0
        for t in range(1, 11):
            oe *= (1 + g)
            pv += oe / (1 + COE) ** t
        tv = oe * 1.025 / (COE - 0.025) / (1 + COE) ** 10
        return pv + tv
    g10 = solve(val, -0.10, 0.60, target=target)
    g_perp = COE - oe0 / target   # 恒定增长：EV = OE1/(r-g)，OE1≈OE0
    return g10, g_perp, oe0, target


def main():
    net, n, p_issue = placement()
    print('=== 鹏鼎控股 002938 独立估值（价格日 2026-10-20，现价 %.2f）===' % PRICE)
    print('经调整净现金（无杠杆口径） = %.2f 亿；非经营资产 = %.2f 亿' % (NET_CASH_ADJ, NONOP))
    print('定增：净额 %.1f 亿，假设发行价 %.2f 元，新增 %.4f 亿股（%.1f%%）' % (net, p_issue, n, 100 * n / SHARES))
    print('2026H1 正常化归母净利 %.2f；2025H2 %.2f；TTM 正常化 %.2f' % (H1_NORM_NP, H2_2025_NORM_NP, H1_NORM_NP + H2_2025_NORM_NP))
    print()
    res = {}
    for k, s in SCEN.items():
        v, d = per_share(s)
        v_unlev, _ = per_share(s, levered=False)
        v_noplace, _ = per_share(s, place=False)
        v_np_unlev, _ = per_share(s, place=False, levered=False)
        rows, roic_T, np26 = build(s)
        res[k] = v
        print('--- %s（概率 %.2f）---' % (k, s['p']))
        print('2026 正常化归母净利 %.2f 亿；终值期 ROIC %.1f%%' % (np26, 100 * roic_T))
        print('年度    存量收入  算力收入  总收入   归母净利   D&A   资本开支   所有者收益')
        for x in rows:
            print('%-7s %8.1f %8.1f %8.1f %9.2f %6.1f %8.1f %10.2f' % (
                x['year'], x['rev_leg'], x['rev_ai'], x['rev'], x['np_period'], x['da'], x['capex'], x['oe']))
        print('经营价值 PV = %.1f（其中终值 PV %.1f，占 %.0f%%）；净负债项 %.2f；非经营 %.1f；股本 %.4f' % (
            d['ops'], d['pv_tv'], 100 * d['pv_tv'] / d['ops'], d['cash_term'], NONOP, d['n_sh']))
        print('V（定增后，有杠杆）= %.2f；无杠杆 = %.2f；不计定增（有杠杆）= %.2f；不计定增无杠杆 = %.2f' % (
            v, v_unlev, v_noplace, v_np_unlev))
        print()
    vw = weighted()
    vw_unlev = weighted(levered=False)
    vw_noplace = weighted(place=False)
    print('加权 V（定增后，有杠杆，主口径）= %.2f 元；P/V = %.3f' % (vw, PRICE / vw))
    print('加权 V 无杠杆口径 = %.2f（P/V %.3f）；不计定增 = %.2f（P/V %.3f）' % (
        vw_unlev, PRICE / vw_unlev, vw_noplace, PRICE / vw_noplace))
    v8, v10 = weighted(0.08), weighted(0.10)
    print('股权成本 8%%：加权 V = %.2f（P/V %.3f）；10%%：加权 V = %.2f（P/V %.3f）' % (v8, PRICE / v8, v10, PRICE / v10))
    for k in SCEN:
        print('  %s：8%% %.2f／10%% %.2f' % (k, per_share(SCEN[k], 0.08)[0], per_share(SCEN[k], 0.10)[0]))
    irr = implied_irr()
    print('现价隐含回报（基准情景所有者收益流）= %.2f%%' % (100 * irr))
    g10, g_perp, oe0, target = reverse_dcf()
    print('反向 DCF：以 %.1f 亿为起点，现价（经营部分 %.0f 亿）隐含 10 年所有者收益年增 %.1f%% 后 2.5%% 永续；'
          '恒定永续增速 %.1f%%（>股权成本区间上限，不可持续）' % (oe0, target, 100 * g10, 100 * g_perp))
    print('分档价格（V 不变）：≤%.2f 明显低估；%.2f–%.2f 温和低估；%.2f–%.2f 大致合理；>%.2f 偏贵' % (
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    # 证伪条件触发后的 V（改权重或改输入）
    print()
    print('证伪条件触发后的 V：')
    f0 = weighted(weights={'bear': 0.40, 'base': 0.50, 'bull': 0.10})
    f1 = weighted(weights={'bear': 0.10, 'base': 0.45, 'bull': 0.45})
    f2 = weighted(weights={'bear': 0.50, 'base': 0.40, 'bull': 0.10})
    f3 = weighted(weights={'bear': 0.45, 'base': 0.45, 'bull': 0.10})
    f4 = weighted(weights={'bear': 0.05, 'base': 0.35, 'bull': 0.60})
    f5 = weighted(price_issue=45.0)
    print('F0 2026Q3 单季正常化归母净利<10 亿或 2026 全年<37 亿：%.2f' % f0)
    print('F1 算力/汽车 2027 年收入≥150 亿且毛利率≥30%%：%.2f' % f1)
    print('F2 算力/汽车半年度毛利率<25%% 或 HDI 产能利用率<75%%：%.2f' % f2)
    print('F3 存量收入 2027 年同比降>5%%（A 客户份额流失）：%.2f' % f3)
    print('F4 2027 年正常化归母净利≥65 亿：%.2f' % f4)
    print('F5 定增发行价低于 45 元（新增约 2.13 亿股，敏感性）：%.2f' % f5)
    # 基准情景再投资率与增量回报（2026H2–2031）
    rows, _, np26 = build(SCEN['base'])
    sub = [x for x in rows if x['year'] == '2026H2' or (isinstance(x['year'], int) and x['year'] <= 2031)]
    reinv = sum(x['capex'] - x['da'] for x in sub)
    nwc = NWC_RATE * (sub[-1]['rev'] - (REV_2025 + (sub[0]['rev'] - REV_2025) * 0.5))
    reinv_total = reinv + nwc
    np_sum = sum(x['np_period'] for x in sub)
    d_np = sub[-1]['np'] - np26
    print()
    print('基准：2026H2–2031 净再投资 %.1f 亿（资本开支−折旧 %.1f + 营运资本 %.1f），同期归母净利合计 %.1f 亿，'
          '再投资率 %.0f%%；2031 较 2026 归母净利增 %.1f 亿，增量回报 %.1f%%' % (
              reinv_total, reinv, nwc, np_sum, 100 * reinv_total / np_sum, d_np, 100 * d_np / reinv_total))
    g = [rows[i + 1]['np'] / (rows[i]['np'] if i else np26) - 1 for i in range(5)]
    print('基准归母净利增速 2027–2031：' + '、'.join('%.1f%%' % (100 * x) for x in g))
    return res, vw


if __name__ == '__main__':
    main()
