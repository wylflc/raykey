# -*- coding: utf-8 -*-
"""汇川技术（300124）独立估值（OI-291 b05，价格日 2026-10-19）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。全部输入写在本脚本内，出处见
`companies/300124_汇川技术.md`「来源」一节（公告文件与 PDF 物理页码）。

方法：分部所有者收益 DCF（归母口径）。
  分部 A：联合动力以外的全部业务（工业自动化与数字化、智慧电梯、智能机器人、数字能源、其他），
          归母口径；DCF 中剔除税后净利息（现金另行加回）。
  分部 B：联合动力（301656，持股 83.3129%），按归母比例计入。
  所有者收益 = 净利润 ×（1 − 当年增速 / 增量 ROIC）；2027-2031 逐年给定增速，2032-2036 线性
  过渡到终值增速；年中折现（FY2027 现金流距价格日 0.7 年，终值折现 9.7 年）；终值 = 2037 年
  所有者收益 ÷（r − g）。
  股权价值 = 两分部现值 + 2026 下半年所有者收益 + 归母经调整净现金 + 非经营资产（折价后）。
  经调整净现金为正，按无杠杆口径全额扣除有息负债；公司无可转债。
"""

PRICE = 50.79                 # 2026-10-19 收盘，A 股未复权（腾讯日线）
SHARES_TX = 27.0987           # 亿股，腾讯行情总股本（含回购专户股份）
CANCEL = 0.00739967           # 拟注销回购股份 739,967 股（2026-09-22 董事会、10-13 股东会通过，10-13 通知债权人）
TREASURY_KEEP = 0.024762      # 2026 年回购方案已回购 2,476,200 股（截至 2026-09-30，用于员工持股或股权激励）
SHARES = SHARES_TX - CANCEL   # 每股价值股本：含回购专户中不注销的部分
SHARES_EX_TREASURY = SHARES - TREASURY_KEEP
COE = 0.09

# ---------- 资产负债表调整（2026-06-30；2026H1_report 第 29-31、107、116-119、128-134、142 页） ----------
CASH = 56.8666                # 货币资金
TRADING_FA = 39.2029          # 交易性金融资产（理财与结构性存款 39.1071 + 衍生 0.0958）
TD_CURRENT = 36.5525          # 一年内到期的长期定期存款及利息
TD_LONG = 48.2064             # 其他非流动资产中的长期定期存款及利息
RESTRICTED = 1.3952           # 受限货币资金（承兑保证金、短期定期存款、期货与履约保证金）
OP_RESERVE_RATE = 0.05        # 经营备付 = TTM 营收 × 5%（判断）
REV_TTM = 492.71
ST_LOAN = 7.6324              # 短期借款
LT_LOAN_ALL = 19.6034         # 长期借款（含一年内到期与应计利息）
LEASE_ALL = 3.5967            # 租赁负债（含一年内到期）
DISCOUNTED_NOTES = 3.4006     # 其他流动负债：已贴现未到期票据及电子债权凭证（类债务）
BUYBACK_OBLIG = 0.4504        # 其他应付款：限制性股票回购义务
GUARANTEE = 9.2577            # 买方信贷担保余额
GUARANTEE_LOSS = 0.10         # 担保预期损失率（判断）
LPC_SUB_NET_CASH = 38.0       # 联合动力自身净现金（其半年报资产负债表未取到；按其流动资产结构推算，区间 30～50）
LPC_STAKE = 0.833129
MINORITY_LPC = 1 - LPC_STAKE
MINORITY_BOOK = 17.5134       # 合并少数股东权益账面（其中联合动力 15.7382）

LT_EQUITY_INV = 23.5551       # 长期股权投资（前海晶瑞 18.4300 等）
OTHER_NC_FA = 29.4610         # 其他非流动金融资产
OUTSIDE_LP = 13.3061          # 其他合伙人享有份额（非流动 13.2979 + 流动 0.0082），即并表基金外部 LP 的权益
NONOP_HAIRCUT = 0.25

op_reserve = OP_RESERVE_RATE * REV_TTM
cash_like = CASH + TRADING_FA + TD_CURRENT + TD_LONG
debt_like = ST_LOAN + LT_LOAN_ALL + LEASE_ALL + DISCOUNTED_NOTES + BUYBACK_OBLIG + GUARANTEE * GUARANTEE_LOSS
NET_CASH_CONSOL = cash_like - RESTRICTED - op_reserve - debt_like
NET_CASH_ATTR = NET_CASH_CONSOL - MINORITY_LPC * LPC_SUB_NET_CASH
NONOP = (LT_EQUITY_INV + OTHER_NC_FA - OUTSIDE_LP) * (1 - NONOP_HAIRCUT)

NET_FIN_INCOME_AT = 0.8       # 正常化净利中所含税后净利息（归母，H1 利息收入 1.11 − 利息费用 0.63 年化后税后），DCF 剔除

# ---------- 分部拆分（报告数，供正文复核；非 V 输入） ----------
REPORTED = {
    # 期间: (合并营收, 合并归母, 联合动力营收, 联合动力净利 100%, 联合动力归母份额)
    "2024":   (370.41, 42.8549, 161.7753, 9.3591, 9.3591 * 0.946737),
    "2025":   (451.05, 50.5000, 206.9700, 11.3336, 11.3336 - 1.0978),
    "2025H1": (205.09, 29.6878, 91.4806, 5.4901, 5.4901 * 0.946737),
    "2026H1": (246.75, 28.0992, 95.1235, -0.8809, -0.8809 + 0.1470),
}
KF_2026H1 = 27.5605           # 合并扣非归母 2026H1
LPC_KF_2026H1 = -1.39         # 联合动力 2026H1 扣非归母（东吴证券点评，网络）
# 2026E 实际口径（非 V 输入）：分部 A 扣非 Q3E、Q4E；联合动力下半年归母份额
A_KF_Q3E, A_KF_Q4E, LPC_H2E_ATTR = 11.7, 10.3, 1.2
# 分部 A 经营口径（剔除投资收益、公允价值变动、合营联营损益、外部 LP 份额、非经常性补助等；非 V 输入）
# 2026H1 自下而上：合并利润总额 30.5040、所得税 2.4970；联合动力营业利润 −1.4654（作税前近似）、净利 −0.8809
CORE_H1_26 = dict(pt=30.5040, tax=2.4970, lpc_pt=-1.4654, lpc_np=-0.8809, mino=-0.0923, lpc_mino=-0.1470,
                  inv=0.4062, fv=0.8611, lp=0.6073, grants=0.4562, other=0.0952)
# 2025 与 2025H1 按净利层面近似：分部 A 归母 −（投资收益 + 公允价值 + 分部 A 补助 + 其他非经常 − 外部 LP 份额）× 90%
CORE_FY25_ITEMS = 0.628 - 0.291 + 1.50 - 0.12 - 0.116
CORE_H1_25_ITEMS = 4.121 - 0.701 + 0.50 - 0.182
CORE_H2_GROWTH_E = 0.28       # 2026 下半年分部 A 经营口径同比增速假设（上半年 +31%）

# ---------- 情景 ----------
# A.np0：分部 A 2026 正常化归母净利（含净利息、剔除一次性）；B：联合动力 100% 口径营收 × 净利率
SCEN = {
    "bear": dict(p=0.25,
                 A=dict(np0=40.0, g=[0.06, 0.06, 0.05, 0.05, 0.04], gT=0.020, roic=0.22),
                 B=dict(rev=195.0, margin=0.015, g=[0.03, 0.03, 0.03, 0.03, 0.03], gT=0.020, roic=0.10, ramp=0.5)),
    "base": dict(p=0.50,
                 A=dict(np0=47.0, g=[0.12, 0.11, 0.10, 0.09, 0.08], gT=0.025, roic=0.30),
                 B=dict(rev=210.0, margin=0.035, g=[0.08, 0.08, 0.07, 0.06, 0.05], gT=0.025, roic=0.14, ramp=0.7)),
    "bull": dict(p=0.25,
                 A=dict(np0=52.0, g=[0.15, 0.14, 0.13, 0.11, 0.10], gT=0.025, roic=0.36),
                 B=dict(rev=225.0, margin=0.050, g=[0.12, 0.11, 0.10, 0.08, 0.07], gT=0.025, roic=0.18, ramp=0.9)),
}


def growth_path(g5, gT):
    gs = list(g5)
    last = gs[-1]
    for i in range(1, 6):
        gs.append(last + (gT - last) * i / 5)
    return gs


def seg_pv(np0, g5, gT, roic, r, ramp=1.0, strip=0.0):
    """返回（显性期现值，终值现值，2026 所有者收益，逐年明细[(年, g, 净利, 计入净利, 所有者收益)]）。
    ramp 只作用于 2027 年（联合动力恢复缺口）；strip 为每年剔除的税后净利息。"""
    gs = growth_path(g5, gT)
    npv, rows, pv = np0, [], 0.0
    for k, g in enumerate(gs, start=1):
        npv = npv * (1 + g)
        eff = npv * (ramp if k == 1 else 1.0) - strip
        oe = eff * (1 - g / roic)
        pv += oe / (1 + r) ** (k - 0.3)
        rows.append((2026 + k, g, npv, eff, oe))
    oeT = (npv * (1 + gT) - strip) * (1 - gT / roic)
    pv_tv = oeT / (r - gT) / (1 + r) ** (len(gs) - 0.3)
    oe2026 = (np0 - strip) * (1 - g5[0] / roic)
    return pv, pv_tv, oe2026, rows


def scen_value(s, r, a_override=None, b_override=None):
    A = dict(s["A"]); B = dict(s["B"])
    if a_override:
        A.update(a_override)
    if b_override:
        B.update(b_override)
    pvA, tvA, oeA26, rowsA = seg_pv(A["np0"], A["g"], A["gT"], A["roic"], r, strip=NET_FIN_INCOME_AT)
    npB0 = B["rev"] * B["margin"] * LPC_STAKE
    pvB, tvB, oeB26, rowsB = seg_pv(npB0, B["g"], B["gT"], B["roic"], r, ramp=B["ramp"])
    h2 = 0.5 * (oeA26 + oeB26 * B["ramp"])          # 2026 下半年所有者收益（净现金截至 6-30）
    eq = pvA + tvA + pvB + tvB + h2 + NET_CASH_ATTR + NONOP
    return dict(pvA=pvA, tvA=tvA, pvB=pvB, tvB=tvB, h2=h2, eq=eq, v=eq / SHARES,
                v_ex_treasury=eq / SHARES_EX_TREASURY, npA0=A["np0"], npB0=npB0,
                rowsA=rowsA, rowsB=rowsB, oeA26=oeA26, oeB26=oeB26)


def weighted(r, **kw):
    return sum(s["p"] * scen_value(s, r, **kw)["v"] for s in SCEN.values())


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


def main():
    print("=== 汇川技术 300124 独立估值（价格日 2026-10-19，现价 %.2f 元）===" % PRICE)
    print("股本：腾讯总股本 %.4f − 拟注销 %.4f = %.4f 亿股；再剔除回购专户留存 %.4f 后 %.4f 亿股"
          % (SHARES_TX, CANCEL, SHARES, TREASURY_KEEP, SHARES_EX_TREASURY))

    print("\n--- 分部拆分（报告数）---")
    for k, (rev, np_, lrev, lnp, lattr) in REPORTED.items():
        print("  %-6s 合并营收 %.2f 归母 %.2f | 联合动力营收 %.2f 净利 %.2f 归母份额 %.2f | 分部 A 营收 %.2f 归母 %.2f（净利率 %.1f%%）"
              % (k, rev, np_, lrev, lnp, lattr, rev - lrev, np_ - lattr, (np_ - lattr) / (rev - lrev) * 100))
    a_kf_h1 = KF_2026H1 - LPC_KF_2026H1 * LPC_STAKE
    a_kf_26e = a_kf_h1 + A_KF_Q3E + A_KF_Q4E
    lpc_26e = REPORTED["2026H1"][4] + LPC_H2E_ATTR
    print("  2026H1 分部 A 扣非 = %.2f + %.2f = %.2f；2026E 分部 A 扣非（激励考核口径）≈ %.1f（目标 49）；联合动力归母份额 2026E ≈ %.1f；合并扣非 2026E ≈ %.1f"
          % (KF_2026H1, -LPC_KF_2026H1 * LPC_STAKE, a_kf_h1, a_kf_26e, lpc_26e, a_kf_26e + lpc_26e))
    c = CORE_H1_26
    a_pt = c["pt"] - c["lpc_pt"]
    a_tax = c["tax"] - (c["lpc_pt"] - c["lpc_np"])
    adj = -c["inv"] - c["fv"] + c["lp"] - c["grants"] - c["other"]
    core_h1_26 = (a_pt + adj) * (1 - a_tax / a_pt) - (c["mino"] - c["lpc_mino"])
    core_fy25 = (REPORTED["2025"][1] - REPORTED["2025"][4]) - CORE_FY25_ITEMS * 0.9
    core_h1_25 = (REPORTED["2025H1"][1] - REPORTED["2025H1"][4]) - CORE_H1_25_ITEMS * 0.9
    core_h2_25 = core_fy25 - core_h1_25
    core_26e = core_h1_26 + core_h2_25 * (1 + CORE_H2_GROWTH_E)
    print("  分部 A 经营口径：2025 ≈ %.1f（净利率 %.1f%%）；2025H1 ≈ %.1f，2025H2 ≈ %.1f；2026H1 = %.2f（税前 %.2f，税率 %.1f%%，同比 %+.0f%%）；2026E ≈ %.1f（净利率 %.1f%%）"
          % (core_fy25, core_fy25 / (451.05 - 206.97) * 100, core_h1_25, core_h2_25, core_h1_26, a_pt + adj,
             a_tax / a_pt * 100, (core_h1_26 / core_h1_25 - 1) * 100, core_26e,
             core_26e / ((246.75 - 95.1235) + (451.05 - 206.97 - 113.61) * 1.22) * 100))

    print("\n--- 经调整净现金与非经营资产（2026-06-30）---")
    print("  现金类 %.2f − 受限 %.2f − 经营备付 %.2f − 有息及类债务 %.2f = 合并经调整净现金 %.2f"
          % (cash_like, RESTRICTED, op_reserve, debt_like, NET_CASH_CONSOL))
    print("  − 联合动力净现金 %.1f 中少数股东份额 %.2f → 归母经调整净现金 %.2f（%.2f 元/股）"
          % (LPC_SUB_NET_CASH, MINORITY_LPC * LPC_SUB_NET_CASH, NET_CASH_ATTR, NET_CASH_ATTR / SHARES))
    print("  非经营资产：(长投 %.2f + 其他非流动金融资产 %.2f − 外部 LP 份额 %.2f) × 75%% = %.2f（%.2f 元/股）"
          % (LT_EQUITY_INV, OTHER_NC_FA, OUTSIDE_LP, NONOP, NONOP / SHARES))

    print("\n--- 三情景（COE 9%）---")
    res = {}
    for name, s in SCEN.items():
        o = scen_value(s, COE)
        res[name] = o
        tv_share = (o["tvA"] + o["tvB"]) / o["eq"]
        print("[%s] p=%.2f  2026 正常化归母：A %.2f + B %.2f = %.2f" % (name, s["p"], o["npA0"], o["npB0"], o["npA0"] + o["npB0"]))
        print("   A 显性 %.1f 终值 %.1f | B 显性 %.1f 终值 %.1f | 2026H2 %.1f | 净现金 %.1f | 非经营 %.1f"
              % (o["pvA"], o["tvA"], o["pvB"], o["tvB"], o["h2"], NET_CASH_ATTR, NONOP))
        print("   股权价值 %.1f 亿元，V = %.2f 元/股（剔除回购专户 %.2f），终值占比 %.0f%%，P/V %.2f"
              % (o["eq"], o["v"], o["v_ex_treasury"], tv_share * 100, PRICE / o["v"]))
    vw = weighted(COE)
    vw_ex = sum(s["p"] * scen_value(s, COE)["v_ex_treasury"] for s in SCEN.values())
    print("\n加权 V = %.2f 元/股，P/V = %.2f（剔除回购专户：V %.2f，P/V %.2f）" % (vw, PRICE / vw, vw_ex, PRICE / vw_ex))
    for r in (0.08, 0.10):
        w = weighted(r)
        print("COE %.0f%%：加权 V %.2f，P/V %.2f；熊/基/牛 %.2f / %.2f / %.2f" %
              (r * 100, w, PRICE / w, *(scen_value(s, r)["v"] for s in SCEN.values())))
    irr = solve(lambda r: scen_value(SCEN["base"], r)["v"], 0.04, 0.20, PRICE)
    print("基准情景隐含回报（现值 = 现价的折现率）= %.2f%%" % (irr * 100))

    # 反向 DCF
    g5 = solve(lambda g: scen_value(SCEN["base"], COE, a_override=dict(g=[g] * 5))["v"], 0.0, 0.40, PRICE)
    print("反向 DCF：分部 A 2027-2031 每年 %.1f%%（其后 5 年线性降至 2.5%%），其余取基准，可支撑现价" % (g5 * 100))

    def v_flat10(g):
        s = SCEN["base"]; A = s["A"]
        pv, npv = 0.0, A["np0"]
        for k in range(1, 11):
            npv *= (1 + g)
            pv += (npv - NET_FIN_INCOME_AT) * (1 - g / A["roic"]) / (1 + COE) ** (k - 0.3)
        oeT = (npv * 1.025 - NET_FIN_INCOME_AT) * (1 - 0.025 / A["roic"])
        pv += oeT / (COE - 0.025) / (1 + COE) ** 9.7
        b = scen_value(s, COE)
        return (pv + b["pvB"] + b["tvB"] + b["h2"] + NET_CASH_ATTR + NONOP) / SHARES
    g10 = solve(v_flat10, 0.0, 0.40, PRICE)
    print("反向 DCF：分部 A 10 年不变增速 %.1f%% 后接 2.5%% 永续，可支撑现价" % (g10 * 100))
    npA = SCEN["base"]["A"]["np0"] - NET_FIN_INCOME_AT
    npB = SCEN["base"]["B"]["rev"] * SCEN["base"]["B"]["margin"] * LPC_STAKE

    def v_perp(g):
        oe = npA * (1 + g) * (1 - g / 0.30) + npB * (1 + g) * (1 - g / 0.14)
        return (oe / (COE - g) + NET_CASH_ATTR + NONOP) / SHARES
    gp = solve(v_perp, 0.0, 0.085, PRICE)
    print("反向 DCF：单段永续增速 %.2f%%（基准正常化起点、ROIC 30%%/14%%）可支撑现价" % (gp * 100))

    # 基准逐年
    print("\n--- 基准情景逐年（亿元）---")
    b = res["base"]
    oe_prev = b["oeA26"] + b["oeB26"] * SCEN["base"]["B"]["ramp"]
    nps, oes = [], []
    for (y, gA, nA, eA, oA), (_, gB, nB, eB, oB) in zip(b["rowsA"], b["rowsB"]):
        print("  %d  A g=%4.1f%% 净利 %5.1f 所有者收益 %5.1f | B g=%4.1f%% 归母净利 %4.1f（计入 %4.1f）所有者收益 %4.1f | 合计所有者收益 %5.1f"
              % (y, gA * 100, nA, oA, gB * 100, nB, eB, oB, oA + oB))
        nps.append(eA + NET_FIN_INCOME_AT + eB); oes.append(oA + oB)
    gro = [oes[0] / oe_prev - 1] + [oes[i] / oes[i - 1] - 1 for i in range(1, 5)]
    print("  合计所有者收益增速 2027-2031：" + ", ".join("%.3f" % x for x in gro))
    rr27 = 1 - oes[0] / (nps[0] - NET_FIN_INCOME_AT)
    roic_blend = (b["rowsA"][0][3] * SCEN["base"]["A"]["roic"] + b["rowsB"][0][3] * SCEN["base"]["B"]["roic"]) / \
                 (b["rowsA"][0][3] + b["rowsB"][0][3])
    print("  2027 再投资率 %.3f，净利加权增量 ROIC %.3f；2026 所有者收益（年化）%.1f" % (rr27, roic_blend, oe_prev))

    # 交叉验证
    print("\n--- 交叉验证 ---")
    mcap = PRICE * SHARES
    np_ttm, np_2025, eq_parent = 48.91, 50.50, 367.84
    norm = SCEN['base']['A']['np0'] + npB
    print("  市值 %.1f 亿元；PE(TTM) %.1f，PE(2025) %.1f，PB %.2f；基准正常化 PE %.1f，剔除净现金与非经营资产后 %.1f"
          % (mcap, mcap / np_ttm, mcap / np_2025, mcap / eq_parent, mcap / norm, (mcap - NET_CASH_ATTR - NONOP) / norm))
    ebit_ttm = 52.88 + 1.81 - 0.96   # TTM 营业利润 + 剔除投资收益与公允价值变动（TTM 合计 −1.81）− 净利息收入（年化 0.96）
    ev = mcap - NET_CASH_CONSOL - NONOP + MINORITY_BOOK
    print("  EV %.1f（市值 − 合并经调整净现金 − 非经营 + 少数股东权益账面），EBIT(TTM) ≈ %.1f，EV/EBIT %.1f" % (ev, ebit_ttm, ev / ebit_ttm))
    print("  股息率 %.2f%%（TTM 每股 0.50 元）；2026 回购已用 1.62 亿元（%.2f%% 市值）；合计 %.2f%%"
          % (0.50 / PRICE * 100, 1.62 / mcap * 100, (0.50 * SHARES + 1.62) / mcap * 100))
    lpc_px, lpc_sh = 13.80, 24.0479   # 联合动力 2026-09-28 收盘（网络），总股本 24.0479 亿股
    lpc_mv = lpc_px * lpc_sh
    parent_net_cash = NET_CASH_ATTR - LPC_STAKE * LPC_SUB_NET_CASH
    a_part = b["pvA"] + b["tvA"] + b["h2"]
    sotp = a_part + parent_net_cash + NONOP + LPC_STAKE * lpc_mv
    sotp80 = a_part + parent_net_cash + NONOP + 0.8 * LPC_STAKE * lpc_mv
    lpc_intr = (b["pvB"] + b["tvB"]) / LPC_STAKE + LPC_SUB_NET_CASH
    print("  分部加总：A 基准（含 2026H2）%.1f + 母公司口径净现金 %.1f + 非经营 %.1f + 联合动力 83.31%% 市值 %.1f = %.1f 亿元 → %.2f 元/股"
          % (a_part, parent_net_cash, NONOP, LPC_STAKE * lpc_mv, sotp, sotp / SHARES))
    print("    联合动力市值打 8 折：%.2f 元/股；联合动力 100%% 基准内在值 ≈ %.1f 亿元（市值 %.1f 亿元，每股 %.2f 元）"
          % (sotp80 / SHARES, lpc_intr, lpc_mv, lpc_intr / lpc_sh))

    # 证伪
    print("\n--- 证伪触发后的独立 V（加权，COE 9%）---")
    f1 = sum(s["p"] * scen_value(s, COE, a_override=dict(np0=s["A"]["np0"] * 0.90))["v"] for s in SCEN.values())
    print("  F1 分部 A 2026 扣非 < 44.1 亿：三档 A 起点 −10%%：V %.2f" % f1)
    f2 = sum(s["p"] * scen_value(s, COE, a_override=dict(np0=s["A"]["np0"] * 1.06,
                                                         g=[x + 0.02 for x in s["A"]["g"]]))["v"] for s in SCEN.values())
    print("  F2 分部 A 2026 扣非 ≥ 52 亿且 2027H1 同比 ≥ 18%%：A 起点 +6%%、前 5 年增速 +2pp：V %.2f" % f2)
    bb = SCEN["bear"]["B"]
    f3 = weighted(COE, b_override=dict(margin=bb["margin"], rev=bb["rev"], g=bb["g"], roic=bb["roic"], ramp=bb["ramp"], gT=bb["gT"]))
    print("  F3 联合动力 2026 归母亏损或 2027H1 净利率 < 1%%：三档 B 取熊市参数：V %.2f" % f3)
    f4 = sum(s["p"] * scen_value(s, COE, a_override=dict(np0=s["A"]["np0"] * 0.88, roic=s["A"]["roic"] * 0.85))["v"]
             for s in SCEN.values())
    print("  F4 工业自动化与数字化毛利率 < 38%%：A 起点 −12%%、ROIC ×0.85：V %.2f" % f4)
    f5 = sum(s["p"] * scen_value(s, COE, a_override=dict(np0=s["A"]["np0"] * 0.95,
                                                         g=[max(x - 0.03, 0.0) for x in s["A"]["g"]]))["v"]
             for s in SCEN.values())
    print("  F5 2027H1 工业自动化与数字化收入同比 < 5%%：A 起点 −5%%、前 5 年增速 −3pp：V %.2f" % f5)

    print("\nV 不变时分档价格：≤ %.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；> %.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
