#!/usr/bin/env python3
"""宝丰能源（600989）独立估值：OI-291 b21 深度版。

运行：python3 valuation.py
金额单位亿元，价格与每股价值为元/股，单价为元/吨（不含税）。
输入全部写在脚本内，出处见注释（文件名指 raw/600989/txt/ 下的公告逐页文本，
"opdata" 指公司按化工行业信息披露指引发布的季度/年度主要经营数据公告）。
"""

# ---------------------------------------------------------------- 市场与股本
PRICE = 22.18                 # 2026-10-21 收盘（brief.md）
SHARES = 73.3336              # 总股本，亿股，含回购专户（brief.md；2026Q3_report 第 7 页）
TREASURY = 0.605972           # 回购专户 60,597,200 股，用途员工持股/股权激励，非注销（buyback_20260513 第 2 页）
SHARES_EX = SHARES - TREASURY
MCAP = PRICE * SHARES
K = 0.09                      # 股权成本基准
TAX_INT = 0.155               # 利息抵税税率（与经营税率一致）

# ---------------------------------------------------------------- 2026-09-30 资产负债（2026Q3_report 第 6-7、9 页）
CASH = 36.68                  # 货币资金 3,667,755,987.28
RESTRICTED = 36.68 - 35.57    # 期末现金及现金等价物 3,556,933,916.55，差额为受限（信用证及矿山保证金）
OP_RESERVE = 10.0             # 经营备付：约 2% 收入；公司年末常态现金 13 亿左右
IBD = 5.00 + 184.30 + 30.93 + 35.18   # 短借+长借+一年内到期非流动负债+租赁负债 = 255.41
LT_PAYABLE = 11.26            # 长期应付款：采矿权、取水权分期价款（2026H1_report 第 104 页），类债务
PROVISION = 0.99              # 预计负债：矿山弃置义务
# 已宣派未付股利（控股股东自行发放部分）：H1 末 9.879（2026H1_report 第 102 页）
# + 半年度派息中控股股东部分 5,166,211,270 股 × 0.42 = 21.698
# − Q3 实付控股股东 ≈ Q3「分配股利、利润或偿付利息」24.218 − Q3 借款利息约 2.21 − 中小股东派息 8.848
DIV_PAYABLE = 9.879 + 21.698 - (24.218 - 2.21 - 8.848)
# 季节性营运资金超常部分：Q3 末经营性营运资金 −37.80，前四个季末均值 −28.0，按正常化收入折算的超额约 9.5
WC_EXCESS = 9.5
NET_CASH_ADJ = CASH - RESTRICTED - OP_RESERVE - DIV_PAYABLE - WC_EXCESS - IBD - LT_PAYABLE - PROVISION
ND_ADJ = -NET_CASH_ADJ        # 经调整净负债（有杠杆口径按现规模滚动）

# 有息负债实际平均利率：2026H1 借款利息支出 3.981（含资本化）+ 未确认融资费用摊销 1.262，年化后
# ÷ 期初期末平均有息负债 (300.74 + 267.40)/2（2026H1_report 第 111 页「财务费用」附注；借款利率 2.34%-3.50% 见第 104 页）
RATE = (3.981 + 1.262) * 2 / ((300.74 + 267.40) / 2)

# 非经营资产
FUND_NET = 13.10 - 2.22 - 1.24   # 其他非流动金融资产（北交联合羚跃系列基金，第二层次，按现行市价含限售折扣）
                                 # − 普通合伙人份额（其他非流动负债）− 公允价值增值对应递延所得税负债增量
HDZ_RECV = 10.0                  # 红墩子煤业 40% 股权转让尾款，账龄 1-2 年，H1 已计提 1.0（2026H1_report 第 82-83 页）
EQUITY_INV = 3.43 + 0.20         # 长期股权投资 + 其他权益工具投资
NONOP = {'bear': FUND_NET * 0.5 + HDZ_RECV * 0.4 + EQUITY_INV * 0.8,
         'base': FUND_NET * 0.85 + HDZ_RECV * 0.7 + EQUITY_INV,
         'bull': FUND_NET * 1.0 + HDZ_RECV * 0.9 + EQUITY_INV}

# ---------------------------------------------------------------- 价差口径与校准
# 聚烯烃单吨毛利 = P + B − 4.2×Cg − 0.85×Cp − F
#   P：PE/PP/EVA 加权不含税售价；B：烯烃板块副产品收入/吨（板块收入 − PE/PP/EVA 收入）
#   Cg：气化原料煤不含税采购价；Cp：动力煤不含税采购价；4.2、0.85 为吨聚烯烃耗煤（2025 年报原材料成本 2,048 元/吨反推，
#   并与 2026Q3 环比成本增量互校）；F：非煤单位成本（折旧、人工、能耗辅料、维修等）。2026H1 反推 F=2,045（无非计划停车），
#   基准取 2,100 以计入周期性大修，熊 2,200（≈2025 年 2,226 的爬坡期水平），牛 2,050；四期新装置 F 高 300 元/吨（折旧）
COAL_G, COAL_P = 4.2, 0.85
HIST = {  # 名称: (P, B, Cg, Cp, 烯烃板块毛利/吨 或 None)
    '2024':    (6999, 848, 562.63, 414.22, 2683),   # opdata FY2025 表中 2024 列；板块毛利 65.87/245.5 万吨
    '2025':    (6418, 782, 462.08, 335.69, 2748),   # opdata FY2025；2025_annual_report 第 23-24 页板块 143.50/522.27
    '2026H1':  (7040, 1098, 491.01, 350.83, 3733),  # opdata 2026H1；板块收入 241.08、成本 130.48（2026H1_report 第 109 页）
    '2026Q3':  (7552, 1199, 628.2, 472.1, None),    # opdata 9M−H1 推算；Q3 煤价按 9M、H1 均价反推（季度采购量近似）
    '2026_9M': (7212, 1132, 536.74, 391.24, None),  # opdata 2026 前三季度
}

V_EXIST = 595.0      # 万吨/年：2026 前三季度 PE+PP+EVA 销量 446.11 万吨年化（opdata 9M）
INFL = 0.015         # 名义价格与成本年漂移
OPEX = 35.0          # 税金及附加约 1.2% 收入 6.6 + 销售 1.3 + 管理 13.2 + 研发 14.0 + 小额减值与营业外 0.6 − 其他收益 1.0（2026 年价）
FIN_2026 = 9.3       # 2026 前三季度财务费用 6.95 年化（报表口径正常化净利用）
DON_2026 = 7.0       # 2026 年向燕宝慈善基金会捐赠上限 6+1 亿（dividend_20260313 第 2 页；10-21 董事会决议）
DON_9M = 5.6         # 2026Q3_report 第 2 页「捐赠支出」
DON_G = 0.03
DA = {2026: 37.6, 2027: 39.5, 2028: 43.0}   # 2025 年 33.04；2026H1 18.78 年化；四期投产后增加
T_TV = 4.70         # 年中折现：2027 年现金流在 t=0.70，2032 年起的终值折到 t=4.70（=首笔终值流 5.70 前一年）

SC = {
    'bear': dict(p=0.25, P=6250, B=760, Cg=530, Cp=380, F=2200, Fn=2500, coke=20.0, fine=6.0, oth=1.0,
                 Sq4=4700, tax=0.155, tax_late=0.20, maint=1.00, iv={2027: 20, 2028: 52},
                 gcap={'q4': 20.0, 2027: 36.0, 2028: 10.0}, g_mid=0.005, rr_mid=0.05, g_T=0.01, rr_T=0.10,
                 carbon=8.0, comp=False),
    'base': dict(p=0.50, P=6700, B=830, Cg=515, Cp=372, F=2100, Fn=2400, coke=27.0, fine=9.0, oth=1.0,
                 Sq4=5100, tax=0.155, tax_late=0.17, maint=0.80, iv={2027: 25, 2028: 52},
                 gcap={'q4': 18.0, 2027: 32.0, 2028: 8.0}, g_mid=0.025, rr_mid=0.20, g_T=0.02, rr_T=0.20,
                 carbon=3.0, comp=True),
    'bull': dict(p=0.25, P=7150, B=950, Cg=505, Cp=362, F=2050, Fn=2350, coke=34.0, fine=12.0, oth=1.5,
                 Sq4=5450, tax=0.155, tax_late=0.155, maint=0.65, iv={2027: 30, 2028: 52},
                 gcap={'q4': 16.0, 2027: 24.0, 2028: 4.0}, g_mid=0.05, rr_mid=0.40, g_T=0.025, rr_T=0.25,
                 carbon=0.0, comp=True),
}
for _n, _s in SC.items():
    _s['nonop'] = NONOP[_n]


def k_index(P, Cg, Cp):
    """证伪用价差指标 K（不含副产品）：P − 4.2×Cg − 0.85×Cp。"""
    return P - COAL_G * Cg - COAL_P * Cp


def spread(s):
    return s['P'] + s['B'] - COAL_G * s['Cg'] - COAL_P * s['Cp']


def gross_profit(s, S, vol_iv, year):
    f = (1 + INFL) ** max(0, year - 2026)
    g = (V_EXIST * (S - s['F']) + vol_iv * (S - s['Fn'])) / 1e4 + s['coke'] + s['fine'] + s['oth']
    return g * f


def norm_np_2026(s, with_donation=True):
    """2026 正常化归母净利（报表口径：含净利息，捐赠按经常性费用计；剔除公允价值、坏账等一次性项目）。"""
    g = gross_profit(s, spread(s), 0, 2026)
    don = DON_2026 if with_donation else 0.0
    return (g - OPEX - FIN_2026 - don) * (1 - s['tax'])


def flows(s):
    """返回 [(t 年, 经营所有者收益, 经营税后净利, 未扣增长性资本开支的所有者收益)] 与终值年所有者收益。
    经营口径：不含利息（有杠杆口径另扣利息现值）；comp=True 时加回大股东补偿给中小股东的税后捐赠。"""
    out = []
    S = spread(s)
    # 2026Q4 存根：现货附近价差，非正常化
    g_q4 = gross_profit(s, s['Sq4'], 0, 2026) / 4
    don = DON_2026 - DON_9M
    npop = (g_q4 - OPEX / 4 - don) * (1 - s['tax'])
    addb = don * (1 - s['tax']) if s['comp'] else 0.0
    pre = npop + addb + DA[2026] / 4 * (1 - s['maint'])
    out.append((0.10, pre - s['gcap']['q4'], npop, pre))
    np_prev = da_prev = None
    for i, yr in enumerate(range(2027, 2032)):
        t = 0.70 + i
        f = (1 + INFL) ** (yr - 2026)
        tax = s['tax'] if yr <= 2030 else s['tax_late']
        don = DON_2026 * (1 + DON_G) ** (yr - 2026)
        carbon = s['carbon'] * f if yr >= 2030 else 0.0
        addb = don * (1 - tax) if s['comp'] else 0.0
        if yr <= 2028:
            g_ = gross_profit(s, S, s['iv'][yr], yr)
            npop = (g_ - OPEX * f - carbon - don) * (1 - tax)
            da = DA[yr]
            pre = npop + addb + da * (1 - s['maint'])
            oe = pre - s['gcap'][yr]
        else:
            g_ = gross_profit(s, S, s['iv'][2028], yr)
            lvl = (g_ - OPEX * f - carbon - don) * (1 - tax)
            npop = lvl * ((1 + s['g_mid']) / (1 + INFL)) ** (yr - 2028)
            da = da_prev * (1 + s['g_mid'])
            pre = npop + addb + da * (1 - s['maint'])
            oe = pre - s['rr_mid'] * npop
        out.append((t, oe, npop, pre))
        np_prev, da_prev = npop, da
    tax = s['tax_late']
    don = DON_2026 * (1 + DON_G) ** 6
    addb = don * (1 - tax) if s['comp'] else 0.0
    np_T = np_prev * (1 + s['g_T'])
    oe_T = np_T * (1 - s['rr_T']) + addb + da_prev * (1 + s['g_T']) * (1 - s['maint'])
    return out, oe_T


def equity(s, k=K, levered=True, comp=None, scale=1.0):
    s2 = dict(s)
    if comp is not None:
        s2['comp'] = comp
    out, oe_T = flows(s2)
    pv = sum(oe * scale / (1 + k) ** t for t, oe, _, _ in out)
    pv_tv = oe_T * scale / (k - s2['g_T']) / (1 + k) ** T_TV
    pv_op = pv + pv_tv
    debt = ND_ADJ * RATE * (1 - TAX_INT) / k if levered else ND_ADJ
    return dict(eq=pv_op - debt + s2['nonop'], pv_op=pv_op, pv_tv=pv_tv, debt=debt)


def v(s, k=K, levered=True, comp=None, shares=SHARES):
    return equity(s, k, levered, comp)['eq'] / shares


def weighted(k=K, levered=True, shares=SHARES):
    return sum(s['p'] * v(s, k, levered, None, shares) for s in SC.values())


def solve(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def verdict(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def variant(name, **kw):
    s = dict(SC[name])
    s.update(kw)
    return s


def main():
    print('== 价差校准（元/吨，不含税） ==')
    for n, (P, B, Cg, Cp, gpt) in HIST.items():
        S = P + B - COAL_G * Cg - COAL_P * Cp
        F = f"{S - gpt:6.0f}" if gpt else '   —  '
        print(f"{n:8s} P={P:5.0f} B={B:5.0f} Cg={Cg:6.1f} Cp={Cp:6.1f}  K={k_index(P, Cg, Cp):5.0f}  S={S:5.0f}  隐含F={F}")
    print()
    print('== 经调整净现金（无杠杆口径） ==')
    print(f"现金 {CASH:.2f} − 受限 {RESTRICTED:.2f} − 经营备付 {OP_RESERVE:.2f} − 已宣派未付股利 {DIV_PAYABLE:.2f}"
          f" − 营运资金超常 {WC_EXCESS:.2f} − 有息负债 {IBD:.2f} − 长期应付款 {LT_PAYABLE:.2f} − 预计负债 {PROVISION:.2f}")
    print(f"net_cash_adj = {NET_CASH_ADJ:.2f}；有息负债实际平均利率 {RATE:.4f}；"
          f"有杠杆口径税后利息 {ND_ADJ * RATE * (1 - TAX_INT):.2f}/年，9% 现值 {ND_ADJ * RATE * (1 - TAX_INT) / K:.2f}")
    print('非经营资产：' + '，'.join(f"{n} {x:.2f}" for n, x in NONOP.items()))
    print()
    print('== 情景 ==')
    for n, s in SC.items():
        S = spread(s)
        e = equity(s)
        print(f"[{n}] p={s['p']:.2f} K={k_index(s['P'], s['Cg'], s['Cp']):.0f} S={S:.0f} 单吨毛利={S - s['F']:.0f}"
              f"  2026正常化归母(含捐赠)={norm_np_2026(s):.1f}（不含捐赠 {norm_np_2026(s, False):.1f}）")
        out, oe_T = flows(s)
        np26 = (gross_profit(s, S, 0, 2026) - OPEX - DON_2026) * (1 - s['tax'])
        pre26 = np26 + (DON_2026 * (1 - s['tax']) if s['comp'] else 0.0) + DA[2026] * (1 - s['maint'])
        print(f"   2026 正常化基年：经营税后净利={np26:7.2f} 所有者收益(未扣增长capex)={pre26:7.2f}")
        prev = None
        for (t, oe, npop, pre), yr in zip(out, ['2026Q4', 2027, 2028, 2029, 2030, 2031]):
            if yr == 2027:
                prev = pre26
            gr = '' if prev is None else f" 增速{pre / prev - 1:+.1%}"
            print(f"   {yr}: t={t:.2f} 经营税后净利={npop:7.2f} 所有者收益(未扣增长capex)={pre:7.2f}{gr} 所有者收益={oe:7.2f}")
            prev = pre
        print(f"   终值年所有者收益={oe_T:.2f}，g_T={s['g_T']:.3f}，终值现值占比={e['pv_tv'] / e['pv_op']:.1%}")
        print(f"   V(有杠杆,9%)={v(s):.2f}  V8={v(s, 0.08):.2f}  V10={v(s, 0.10):.2f}  "
              f"V(无杠杆)={v(s, levered=False):.2f}  V(剔除回购专户)={v(s, shares=SHARES_EX):.2f}  "
              f"V(捐赠不补偿)={v(s, comp=False):.2f}")
    print()
    vw, vw8, vw10 = weighted(), weighted(0.08), weighted(0.10)
    vwu = weighted(levered=False)
    vwx = weighted(shares=SHARES_EX)
    pv = PRICE / vw
    print('== 加权 ==')
    print(f"加权 V（有杠杆，9%）= {vw:.2f}，P/V = {pv:.3f} → {verdict(pv)}")
    print(f"8% → {vw8:.2f}（P/V {PRICE / vw8:.3f}）；10% → {vw10:.2f}（P/V {PRICE / vw10:.3f}）")
    print(f"无杠杆口径加权 V = {vwu:.2f}，P/V = {PRICE / vwu:.3f}")
    print(f"剔除回购专户股本（{SHARES_EX:.4f} 亿股）加权 V = {vwx:.2f}，P/V = {PRICE / vwx:.3f}")
    print(f"V 不变时各档价格：明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}")
    nn = {n: norm_np_2026(s) for n, s in SC.items()}
    print('2026 正常化归母（报表口径）：' + '，'.join(f"{n} {x:.1f}" for n, x in nn.items()) +
          f"；加权 {sum(SC[n]['p'] * x for n, x in nn.items()):.1f}")
    print()
    base = SC['base']
    irr = solve(lambda r: equity(base, r)['eq'] - MCAP, 0.05, 0.25)
    irr_w = solve(lambda r: sum(s['p'] * equity(s, r)['eq'] for s in SC.values()) - MCAP, 0.05, 0.25)
    print('== 现价隐含回报与反向 DCF ==')
    print(f"现价隐含回报（基准情景流，有杠杆）= {irr:.4f}；概率加权流 = {irr_w:.4f}")
    x = solve(lambda sc: (sum(oe * sc / (1 + K) ** t for t, oe, _, _ in flows(base)[0])
                          + flows(base)[1] * sc / (K - base['g_T']) / (1 + K) ** T_TV
                          - ND_ADJ * RATE * (1 - TAX_INT) / K + base['nonop']) - MCAP, 0.2, 2.0)
    print(f"现价隐含：基准所有者收益整体 × {x:.3f}，约合 2026 正常化归母 {norm_np_2026(base) * x:.1f} 亿")
    out, _ = flows(base)
    pre27 = out[1][3]
    stub = out[0][1] / (1 + K) ** out[0][0]
    need = MCAP + ND_ADJ * RATE * (1 - TAX_INT) / K - base['nonop'] - stub
    g_impl = K - pre27 * (1 + K) ** (1 - 0.70) / need
    print(f"现价隐含永续增速（以 2027 基准所有者收益 {pre27:.1f}、未扣增长性资本开支为起点，不再投资，9%）= {g_impl:.4f}")
    print()
    print('== 证伪触发后的 V（有杠杆，9%） ==')
    f_k = variant('base', P=6250, B=760, Cg=530, Cp=380, coke=20.0, fine=6.0)
    f_coal = variant('base', Cg=600, Cp=430)
    f_cost = variant('base', F=2500, Fn=2800)
    f_iv = variant('base', iv={2027: 0, 2028: 30}, gcap={'q4': 18.0, 2027: 40.0, 2028: 22.0})
    print(f"F1 全年 K<3,900（熊市价差 K={k_index(6250, 530, 380):.0f}、其余按基准）：{v(f_k):.2f}")
    print(f"F2 气化煤 ≥600、动力煤 ≥430、PE/PP/EVA ≤6,700（K={k_index(6700, 600, 430):.0f}，副产品按基准）：{v(f_coal):.2f}")
    # F3 门槛：K=4,300、B=830 时按基准成本测算 2027 上半年扣非（不含捐赠、公允价值），F 高 400 元/吨时的读数
    def h1_kf(F):
        S = 4300 + 830
        g_ = ((V_EXIST / 2) * (S - F) + 5 * (S - 2350)) / 1e4 + (27.0 + 9.0 + 1.0) / 2
        return (g_ * (1 + INFL) - OPEX / 2 * (1 + INFL) - FIN_2026 / 2) * (1 - 0.155)
    print(f"F3 非煤单位成本较假设高 400 元/吨：{v(f_cost):.2f}；K=4,300 时 2027H1 扣非：基准成本 {h1_kf(2100):.1f}，"
          f"成本高 400 元/吨 {h1_kf(2500):.1f}")
    print(f"F4 大股东停止捐赠补偿：{v(base, comp=False):.2f}")
    print(f"F5 四期延至 2027H2 后、投资超支至约 120 亿：{v(f_iv):.2f}")
    print()
    print('== 交叉验证 ==')
    nb = norm_np_2026(base)
    ebit_b = gross_profit(base, spread(base), 0, 2026) - OPEX - DON_2026
    ev = MCAP + ND_ADJ - NONOP['base']
    print(f"市值 {MCAP:.1f}；基准正常化 PE {MCAP / nb:.1f}x；TTM PE {MCAP / 167.17:.1f}x；PB {MCAP / 567.41:.2f}x")
    print(f"EV {ev:.1f}；EV/正常化 EBIT {ev / ebit_b:.1f}x；近 12 个月股息率 {0.84 / PRICE:.2%}；"
          f"回购 10.0 亿（2025-05~2026-05）占市值 {10.0 / MCAP:.2%}")
    # 基准正常化收入与利润率（焦炭 689 万吨 × 1,100 元/吨 + 焦化其他 4 + 精细化工 24 + 其他业务 2.5）
    rev_b = V_EXIST * (base['P'] + base['B']) / 1e4 + 689 * 1100 / 1e4 + 4 + 24 + 2.5
    g_b = gross_profit(base, spread(base), 0, 2026)
    print(f"基准正常化收入约 {rev_b:.0f}；毛利 {g_b:.1f}（毛利率 {g_b / rev_b:.1%}）；捐赠前 EBIT {g_b - OPEX:.1f}"
          f"（{(g_b - OPEX) / rev_b:.1%}）；归母净利率 {nb / rev_b:.1%}")
    # 2026 前三季度归母 143.17 拆分：正常化（基准 × 3/4）+ 一次性（税后）+ 周期性（余项）
    one_off = (8.28 - 1.18 - 0.35 - 0.30 - 0.35) * (1 - 0.15)
    norm9 = nb * 0.75
    print(f"2026 前三季度归母 143.17 = 正常化 {norm9:.1f} + 一次性 {one_off:.1f}（公允价值 +8.28、红墩子应收款减值 −1.18、"
          f"资产处置与营业外 −0.65、投资损失 −0.35，税后）+ 周期性 {143.17 - norm9 - one_off:.1f}")
    q4 = flows(base)[0][0][2] - FIN_2026 / 4 * (1 - base['tax'])
    print(f"2026 全年归母估计（前三季度 + 基准 Q4 存根）≈ {143.17 + q4:.1f}")
    print(f"基准情景终值现值占比 {equity(base)['pv_tv'] / equity(base)['pv_op']:.1%}；四期 50 万吨基准增量 ROIC ≈ "
          f"{(52 * (spread(base) - base['Fn']) / 1e4 - 1.0) * (1 - 0.155) / 105.48:.1%}（投资 105.48 亿）")


if __name__ == '__main__':
    main()
