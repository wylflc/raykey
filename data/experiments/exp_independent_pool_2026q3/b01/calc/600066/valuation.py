# -*- coding: utf-8 -*-
"""600066 宇通客车 独立估值（OI-291 b01，价格日 2026-10-19）。

运行：python3 valuation.py
单位：金额亿元，每股元。输入全部写在本脚本内，出处见注释
（「Q3」= 2026Q3_report，「H1」= 2026H1_report，「AR」= 2025_annual_report，后接 PDF 物理页）。
方法：所有者收益 DCF（归母、经营口径，股权成本 9%），加经调整净现金与非经营资产；
三情景概率加权；另做反向 DCF、隐含回报、历史 PE/PB、股息率、EV/EBIT 互校。
"""

PRICE = 29.08                 # 2026-10-19 收盘，A 股未复权（数据包快照）
SHARES = 22.1394              # 亿股，总股本（Q3 第 6 页 2,213,939,223 股）
MKT_CAP = PRICE * SHARES      # 643.81
COE = 0.09
STUB_T = 0.2                  # 2026-10-19 → 2026-12-31 约 0.2 年
PROB = {'bear': 0.25, 'base': 0.50, 'bull': 0.25}

# ---------------------------------------------------------------------------
# 1. 2026 正常化归母净利（含净利息，剔除一次性）
# ---------------------------------------------------------------------------
# 9M2026 核心经营利润 = 营收 - 营业成本 - 税金及附加 - 销售 - 管理 - 研发（Q3 第 7 页，元）
REV_9M26 = 25815871584.91 / 1e8
CORE_9M26 = (25815871584.91 - 19293205663.45 - 253812533.66 - 855631228.89
             - 583167619.32 - 1306293526.54) / 1e8                      # 35.24，利润率 13.65%
# 参照：2025Q4 营收 150.60、核心利润 23.51（15.61%）；2026Q3 营收 90.97、核心利润 14.61（16.06%）

SCEN = {
    # q4_rev/q4_margin：2026Q4 营收与核心利润率
    # oth：经常性其他收益（增值税/税金减免约 0.8～1.0 + 政府补助的一部分）
    # cash_yield：理财、存款、大额存单收益（约 1.4%～1.8% × 130～145 亿）
    # factoring：保理与票据贴现损失（AR 第 111 页 2025 年 -1.00；Q3 9M -0.90）
    # fees：手续费；impair：资产+信用减值的周期正常值（2023～2025 年 -8.9/-5.2/-0.8）
    # assoc：联营合营收益与股利；nonop：营业外净额；tax：有效税率；mi：少数股东占比
    'bear': dict(q4_rev=125.0, q4_margin=0.135, oth=1.0, cash_yield=1.9, factoring=-1.3, fees=-0.5,
                 impair=-3.5, assoc=0.3, nonop=0.2, tax=0.150, mi=0.01),
    'base': dict(q4_rev=140.0, q4_margin=0.155, oth=1.5, cash_yield=2.2, factoring=-1.1, fees=-0.5,
                 impair=-2.5, assoc=0.4, nonop=0.3, tax=0.135, mi=0.01),
    'bull': dict(q4_rev=150.0, q4_margin=0.165, oth=2.0, cash_yield=2.5, factoring=-0.9, fees=-0.5,
                 impair=-2.0, assoc=0.5, nonop=0.4, tax=0.125, mi=0.01),
}


def normalized_2026(s):
    core = CORE_9M26 + s['q4_rev'] * s['q4_margin']
    other = (s['oth'] + s['cash_yield'] + s['factoring'] + s['fees'] + s['impair']
             + s['assoc'] + s['nonop'])
    pbt = core + other
    keep = (1 - s['tax']) * (1 - s['mi'])
    np_parent = pbt * keep                               # 含净利息的正常化归母净利
    np_op = (pbt - s['cash_yield']) * keep               # 经营口径（DCF 用，净现金另加）
    q4_op = (s['q4_rev'] * s['q4_margin'] + (other - s['cash_yield']) / 4.0) * keep
    return dict(rev=REV_9M26 + s['q4_rev'], core=core, pbt=pbt, np=np_parent, np_op=np_op, q4_op=q4_op)


# ---------------------------------------------------------------------------
# 2. 经调整净现金与非经营资产（2026-09-30，Q3 第 5～6 页）
# ---------------------------------------------------------------------------
CASH = 76.5302                 # 货币资金（其中存放宇通集团财务公司 15.19，H1 第 64 页；集团财务公司存款合计 28.22，H1 第 20 页）
TRADING_FA = 51.7380           # 交易性金融资产（银行理财为主，H1 第 64 页）
DEBT_INV = 1.1922              # 债权投资（大额存单）
NCA_1Y_DEPOSITS = 3.9807 - 1.40   # 一年内到期非流动资产，扣估计的一年内到期长期应收款 1.40（H1 第 71 页为 1.53）
ONCA_DEPOSITS = 11.0592 - 0.40    # 其他非流动资产，扣估计的预付设备款 0.40（H1 第 78 页定期存款 13.16、预付 0.36）
TREASURY = CASH + TRADING_FA + DEBT_INV + NCA_1Y_DEPOSITS + ONCA_DEPOSITS   # 142.70

DEBT = 1.2819 + 0.4880 + 1.6353 + 0.2028 + 0.0055   # 短借、一年内到期非流动负债、租赁负债、长期应付款、交易性金融负债
RESTRICTED = 0.45              # 在途资金（H1 第 64 页 0.45）
OPER_RESERVE = 20.0            # 经营备付，约营收 5%
EUR_CNY, USD_CNY = 7.7671, 6.8109   # H1 第 88 页期末汇率
ARBITRATION = 2.69 * EUR_CNY   # China Motor Limited 仲裁请求 2.69 亿欧元（H1 第 100 页）≈ 20.89
REPURCHASE_NET = 54.91 - 42.09  # 回购责任 54.91，其中安驰按揭 42.09 由宇通集团承诺兜底（H1 第 100 页）
FUND_COMMIT = 1.0 * USD_CNY    # 子公司认购 1 亿美元境外碳中和私募基金（2026-09-15 公告，标题见数据包）
FINCO_DEPOSIT = 28.22          # 存放宇通集团财务公司（关联方）

ADJ = {
    'bear': dict(p_arb=0.35, loss_rep=0.08, fund_hc=0.40, wc_unwind=15.0, finco_hc=0.20, nonop_hc=0.40),
    'base': dict(p_arb=0.15, loss_rep=0.03, fund_hc=0.25, wc_unwind=0.0, finco_hc=0.00, nonop_hc=0.25),
    'bull': dict(p_arb=0.05, loss_rep=0.01, fund_hc=0.10, wc_unwind=0.0, finco_hc=0.00, nonop_hc=0.10),
}

# 非经营资产：其他权益工具投资 9.39 + 其他非流动金融资产 13.58 + 长期股权投资 8.08 扣经营性合营 1.29（AR 第 97 页）
NONOP_BOOK = 9.3924 + 13.5829 + (8.0776 - 1.2942)


def net_cash_adj(a):
    contingent = ARBITRATION * a['p_arb'] + REPURCHASE_NET * a['loss_rep']
    return (TREASURY - DEBT - RESTRICTED - OPER_RESERVE - contingent - FUND_COMMIT * a['fund_hc']
            - a['wc_unwind'] - FINCO_DEPOSIT * a['finco_hc'])


def nonop_value(a):
    return NONOP_BOOK * (1 - a['nonop_hc'])


# ---------------------------------------------------------------------------
# 3. 增长路径（经营口径所有者收益，2027～2031）与再投资
# ---------------------------------------------------------------------------
PATH = {
    'bear': dict(g=[-0.15, -0.12, -0.05, 0.02, 0.02], gT=0.015, ronic=0.15),
    'base': dict(g=[0.00, 0.03, 0.03, 0.03, 0.03], gT=0.025, ronic=0.25),
    'bull': dict(g=[0.06, 0.07, 0.06, 0.05, 0.04], gT=0.025, ronic=0.30),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def dcf(name, r=COE, path=None, e0_mult=1.0, detail=False):
    """返回每股价值与明细。FCF = E × (1 - max(g,0)/RONIC)；负增长不释放资本（净营运资本为负）。"""
    s, a = SCEN[name], ADJ[name]
    p = path or PATH[name]
    n = normalized_2026(s)
    e = n['np_op'] * e0_mult
    pv_stub = n['q4_op'] / (1 + r) ** STUB_T            # 2026Q4 存根不受 e0_mult 压力影响
    pv, rows = pv_stub, []
    for i, g in enumerate(p['g']):
        e = e * (1 + g)
        fcf = e * (1 - max(g, 0.0) / p['ronic'])
        t = STUB_T + i + 1
        pv_i = fcf / (1 + r) ** t
        pv += pv_i
        rows.append((YEARS[i], g, e, fcf, pv_i))
    gT = p['gT']
    fcf_T = e * (1 + gT) * (1 - max(gT, 0.0) / p['ronic'])
    tv = fcf_T / (r - gT)
    pv_tv = tv / (1 + r) ** (STUB_T + len(p['g']))
    ops = pv + pv_tv
    nc, no = net_cash_adj(a), nonop_value(a)
    equity = ops + nc + no
    out = dict(v=equity / SHARES, equity=equity, ops=ops, pv_tv=pv_tv, tv_share=pv_tv / equity,
               nc=nc, nonop=no, rows=rows, e0=n['np_op'] * e0_mult, stub=pv_stub)
    return out


def weighted(r=COE, probs=PROB, e0_mult=None):
    e0_mult = e0_mult or {}
    return sum(probs[k] * dcf(k, r=r, e0_mult=e0_mult.get(k, 1.0))['v'] for k in probs)


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
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


def main():
    print('=== 1. 2026 正常化归母净利（亿元） ===')
    for k in ('bear', 'base', 'bull'):
        n = normalized_2026(SCEN[k])
        print(f"{k:4s} 营收 {n['rev']:.1f}  核心利润 {n['core']:.2f}  税前 {n['pbt']:.2f}  "
              f"归母(含净利息) {n['np']:.2f}  经营口径 {n['np_op']:.2f}  Q4存根 {n['q4_op']:.2f}")

    print('\n=== 2. 经调整净现金与非经营资产（亿元） ===')
    print(f'金融资产合计 {TREASURY:.2f}  有息及类债务 {DEBT:.2f}  受限 {RESTRICTED:.2f}  经营备付 {OPER_RESERVE:.1f}')
    print(f'仲裁请求 {ARBITRATION:.2f}  非集团兜底回购责任 {REPURCHASE_NET:.2f}  基金承诺 {FUND_COMMIT:.2f}  '
          f'关联财务公司存款 {FINCO_DEPOSIT:.2f}（单列）  非经营资产账面 {NONOP_BOOK:.2f}')
    for k in ('bear', 'base', 'bull'):
        print(f'{k:4s} 经调整净现金 {net_cash_adj(ADJ[k]):.2f}  非经营资产 {nonop_value(ADJ[k]):.2f}')

    print('\n=== 3. 三情景 DCF（股权成本 9%） ===')
    res = {}
    for k in ('bear', 'base', 'bull'):
        d = dcf(k)
        res[k] = d
        p = PATH[k]
        print(f"{k:4s} V = {d['v']:.2f} 元/股  经营价值 {d['ops']:.1f}  终值现值 {d['pv_tv']:.1f}"
              f"（占股权价值 {d['tv_share']:.0%}）  净现金 {d['nc']:.1f}  非经营 {d['nonop']:.1f}  "
              f"终值增长 {p['gT']:.1%}  增量回报 {p['ronic']:.0%}")
        print('     ' + '  '.join(f'{y}: g={g:+.0%} E={e:.1f} FCF={f:.1f}' for y, g, e, f, _ in d['rows']))
    vw = weighted()
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元/股（熊 {PROB['bear']:.2f} / 基 {PROB['base']:.2f} / 牛 {PROB['bull']:.2f}）"
          f"  P/V = {pv:.3f}  → {verdict(pv)}")
    print(f'V 不变时各档价格：≤ {0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；'
          f'{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；> {1.10 * vw:.2f} 偏贵')

    print('\n=== 4. 股权成本敏感性 ===')
    for r in (0.08, 0.10):
        print(f'COE {r:.0%}: 熊 {dcf("bear", r=r)["v"]:.2f}  基 {dcf("base", r=r)["v"]:.2f}  '
              f'牛 {dcf("bull", r=r)["v"]:.2f}  加权 {weighted(r=r):.2f}')

    print('\n=== 5. 现价隐含回报（基准情景现金流＝现价的折现率） ===')
    irr = solve(lambda r: dcf('base', r=r)['equity'], 0.05, 0.20, MKT_CAP)
    print(f'隐含回报 = {irr:.2%}')

    print('\n=== 6. 反向 DCF（基准净现金/非经营资产/增量回报 25%，COE 9%） ===')
    base_e0 = normalized_2026(SCEN['base'])['np_op']

    def eq_single(g):
        p = dict(g=[g] * 5, gT=g, ronic=0.25)
        return dcf('base', path=p)['equity']

    def eq_10y(g):
        p = dict(g=[g] * 10, gT=0.025, ronic=0.25)
        return dcf_years(p)

    def dcf_years(p, r=COE):
        s, a = SCEN['base'], ADJ['base']
        n = normalized_2026(s)
        e, pv = n['np_op'], n['q4_op'] / (1 + r) ** STUB_T
        for i, g in enumerate(p['g']):
            e *= (1 + g)
            pv += e * (1 - max(g, 0) / p['ronic']) / (1 + r) ** (STUB_T + i + 1)
        gT = p['gT']
        pv += e * (1 + gT) * (1 - max(gT, 0) / p['ronic']) / (r - gT) / (1 + r) ** (STUB_T + len(p['g']))
        return pv + net_cash_adj(a) + nonop_value(a)

    g_perp = solve(eq_single, -0.10, 0.08, MKT_CAP)
    g_10 = solve(eq_10y, -0.15, 0.15, MKT_CAP)
    print(f'基准经营口径 2026 所有者收益 {base_e0:.1f} 亿；现价隐含永续增速 {g_perp:+.2%}；'
          f'隐含 2027～2036 年增速 {g_10:+.2%}（之后 2.5%）')
    # 等价的零增长所有者收益
    e_flat = (MKT_CAP - net_cash_adj(ADJ['base']) - nonop_value(ADJ['base'])) * COE
    print(f'现价对应零增长经营所有者收益约 {e_flat:.1f} 亿/年（简化：经营价值 × 9%）')

    print('\n=== 7. 交叉验证 ===')
    nb = normalized_2026(SCEN['base'])
    ev = MKT_CAP - net_cash_adj(ADJ['base']) - nonop_value(ADJ['base'])
    ebit = nb['pbt'] - SCEN['base']['cash_yield']
    print(f"市值 {MKT_CAP:.1f}；PE(TTM 归母 54.46) {MKT_CAP / 54.46:.1f}×；PE(正常化基准 {nb['np']:.1f}) {MKT_CAP / nb['np']:.1f}×；"
          f'PB(归母权益 142.84) {MKT_CAP / 142.84:.2f}×')
    print(f'EV(扣经调整净现金与非经营资产) {ev:.1f}；正常化 EBIT {ebit:.1f}；EV/EBIT {ev / ebit:.1f}×')
    print(f'股息率：过去 12 个月 2.00 元 → {2.00 / PRICE:.1%}；2025 年度合计 2.50 元 → {2.50 / PRICE:.1%}；'
          f"按基准正常化利润 90% 派息 → {0.9 * nb['np'] / SHARES / PRICE:.1%}")
    hist_pe = [12.6, 14.1, 10.7, 17.0, 11.4, 16.2, 16.1, 14.2, 13.0]   # 2014～2019、2023～2025 年末 PE（剔除 2020～2022 低谷年）
    hist_pe.sort()
    med = hist_pe[len(hist_pe) // 2]
    print(f'历史年末 PE（剔除 2020～2022）区间 {hist_pe[0]}～{hist_pe[-1]}×，中位 {med}× → '
          f"按基准正常化利润 {med * nb['np'] / SHARES:.2f} 元/股；区间 {hist_pe[0] * nb['np'] / SHARES:.2f}～"
          f"{hist_pe[-1] * nb['np'] / SHARES:.2f}")
    print('历史年末 PB 1.15～4.64×（2022 低点、2025 高点）；现 4.51×，高位因 ROE 约 35% 与近 100% 派息')

    print('\n=== 8. 证伪条件触发后的独立 V ===')
    f1 = weighted(probs={'bear': 0.5, 'base': 0.4, 'bull': 0.1})
    f2 = dcf('bear')['v']
    f3 = weighted(e0_mult={'bear': 0.90, 'base': 0.90, 'bull': 0.90})
    f4 = weighted(probs={'bear': 0.4, 'base': 0.45, 'bull': 0.15})
    f5 = vw - (2.69 * EUR_CNY * (1 - 0.15)) / SHARES
    print(f'F1 2026 年报海外毛利率 < 26% 或海外收入同比下降 → V = {f1:.2f}')
    print(f'F2 2027 年中报扣非归母 < 15 亿 → 取熊市情景 V = {f2:.2f}')
    print(f'F3 欧洲出现针对中国客车的有约束力采购限制 → 各情景经营收益 -10%，V = {f3:.2f}')
    print(f'F4 2026Q4 单季扣非归母 < 15 亿 → V = {f4:.2f}')
    print(f'F5 仲裁裁决全额支持 2.69 亿欧元 → V = {f5:.2f}')


if __name__ == '__main__':
    main()
