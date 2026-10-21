#!/usr/bin/env python3
"""华测导航（300627）独立估值：所有者收益 DCF + 三情景 + 反向 DCF + 交叉验证 + 证伪情形。

金额单位亿元，每股价值元/股。全部输入写在脚本内，出处见
companies/300627_华测导航.md 的页码引用（2025_annual_report、2026H1_report 等逐页文本的物理页）。
运行：python3 valuation.py
"""

PRICE = 26.01            # 2026-10-21 收盘，元（brief.md）
SHARES = 7.9397          # 亿股，腾讯行情口径 = 2026-07-24 总股本 793,970,662 股（holders_20260727 第 1 页），无回购专户股份
COE = 0.09
T_YEAREND = 0.19         # 2026-10-21 → 2026-12-31（年）
T_MID2027 = 0.69         # 2026-10-21 → 2027-06-30（年）；2027 年起年中折现

# ------------------------------------------------ 资产负债（2026-06-30；2026H1_report 第 59–61、104–105、120–121、138–139 页）
cash = 9.82999733            # 货币资金
restricted = 0.28841731      # 其中保证金受限（第 23 页）
wealth = 4.99724197          # 交易性金融资产-理财产品
fx_fwd_asset = 0.04517990    # 交易性金融资产-远期外汇合约
fx_fwd_liab = 0.00712961     # 交易性金融负债（远期外汇）
oca_debt_inv = 5.26684790    # 其他流动资产-债权投资（摊余成本的定期/收益凭证类）
cd_total = 4.65670831        # 大额存单：一年内到期 1.77177722 + 债权投资 2.88493110
short_loan = 1.15006481
long_loan = 0.34450000
lease_liab = 0.01885468 + 0.02288686   # 一年内到期租赁负债 + 租赁负债：以净利润为起点，只列示不扣
guarantee_bal = 1.5954444    # 供应链融资（为非关联下游客户银行贷款提供连带责任担保）余额，第 47 页
guarantee_loss = 0.10        # 预期损失率；账面已计预计负债 0.0799（约 5%，第 145 页）
REV_2025 = 36.99152108
H1_26_REV = 19.28755092
H1_25_REV = 18.33371047
TTM_REV = REV_2025 + H1_26_REV - H1_25_REV
op_reserve_ratio = 0.10      # 经营备付 = TTM 营收 10%（一、三季度经营现金流为负，5 月派息约 3.5 亿）
lt_equity = 0.74912510       # 长期股权投资：方广熙禾基金 0.6225 + 隽梦 0.1267（第 126 页）
other_ncfa = 0.59130901      # 其他非流动金融资产（权益工具，公允价值，第 127 页）
parent_equity = 43.66558862

gross_fin = cash + wealth + fx_fwd_asset - fx_fwd_liab + oca_debt_inv + cd_total
debt = short_loan + long_loan
op_reserve = op_reserve_ratio * TTM_REV
guar_adj = guarantee_bal * guarantee_loss
NET_CASH_ADJ = gross_fin - restricted - op_reserve - debt - guar_adj
NON_OP = lt_equity + other_ncfa


# ------------------------------------------------ TTM 桥（2025 年报 + 2026H1 − 2025H1）
def ttm(fy25, h126, h125):
    return fy25 + h126 - h125


TTM = {
    "归母净利": ttm(6.85420584, 3.33157564, 3.26468108),
    "扣非归母": ttm(6.05007542, 2.71945706, 2.99059491),
    "经营现金流": ttm(6.98680737, 0.51910848, 1.33757437),
    "汇兑损失": ttm(-0.29580829, 0.50691849, -0.33209172),
    "股份支付": ttm(0.43656160, 0.78616167, 0.22201435),
    "信用减值": ttm(1.12035604, 0.08823639, 0.28245303),
    "资产减值": ttm(0.24942712, 0.04479805, -0.00123942),
    "非经常补助": ttm(0.59881206, 0.49832799, 0.17795592),
    "理财存单收益": ttm(0.28773874, 0.19922080, 0.13862900),
    "银行利息收入": ttm(0.12506350, 0.05183356, 0.06036307),
    "利息支出": ttm(0.05334198, 0.02443797, 0.02059162),
    "利润总额": ttm(7.84894154, 3.58615768, 3.68001211),
    "所得税": ttm(1.01287560, 0.20718029, 0.24962439),
}
TTM["非经常合计(税后)"] = TTM["归母净利"] - TTM["扣非归母"]

TAX_NORM = 0.10          # 2024 年 7.7%、2025 年 12.9%（含以前年度调整与未确认递延 3.6pp）、TTM 12.5%
SBC_NORM_BASE = 1.10     # 常态股份支付（税前）：2024 0.51、2025 0.44、2026 公司预计约 1.6，跨期均值约 1.0–1.2


def ttm_normalized_op():
    fx_add = TTM["汇兑损失"] * (1 - TAX_NORM)
    sbc_adj = -(SBC_NORM_BASE - TTM["股份支付"]) * (1 - TAX_NORM)
    int_net = -(TTM["银行利息收入"] - TTM["利息支出"]) * (1 - TAX_NORM)
    return TTM["扣非归母"] + fx_add + sbc_adj + int_net, fx_add, sbc_adj, int_net


# ------------------------------------------------ 情景
H2_25_REV = REV_2025 - H1_25_REV
INT_YIELD = 0.018        # 金融资产税前收益率（TTM 约 1.9%，2.6% 大额存单陆续到期后下行）
INT_ASSETS = gross_fin - restricted

SCEN = {
    "bear": dict(p=0.25, h2_growth=0.03, gm=0.595, sell=0.185, ga=0.060, rd=0.158, surtax=0.006,
                 oth=0.018, imp=0.035, sbc=1.30, minority=0.03,
                 rev_g=[0.04, 0.04, 0.03, 0.03, 0.03], np_g=[0.04, 0.04, 0.03, 0.03, 0.03],
                 g_term=0.020, k=0.45, ronic_term=0.15),
    "base": dict(p=0.50, h2_growth=0.08, gm=0.608, sell=0.180, ga=0.058, rd=0.153, surtax=0.006,
                 oth=0.019, imp=0.030, sbc=1.10, minority=0.03,
                 rev_g=[0.085, 0.085, 0.08, 0.08, 0.075], np_g=[0.115, 0.115, 0.105, 0.10, 0.09],
                 g_term=0.025, k=0.40, ronic_term=0.20),
    "bull": dict(p=0.25, h2_growth=0.13, gm=0.615, sell=0.178, ga=0.057, rd=0.152, surtax=0.006,
                 oth=0.020, imp=0.026, sbc=1.00, minority=0.03,
                 rev_g=[0.12, 0.12, 0.11, 0.10, 0.10], np_g=[0.17, 0.16, 0.15, 0.13, 0.12],
                 g_term=0.025, k=0.38, ronic_term=0.25),
}
FADE_YEARS = 5


def norm_np_2026(s):
    rev = H1_26_REV + H2_25_REV * (1 + s["h2_growth"])
    ebit_pre_sbc = rev * (s["gm"] - s["sell"] - s["ga"] - s["rd"] - s["surtax"] + s["oth"] - s["imp"])
    ebit = ebit_pre_sbc - s["sbc"]
    np_op = ebit * (1 - TAX_NORM) - s["minority"]
    net_int = (INT_ASSETS * INT_YIELD - TTM["利息支出"]) * (1 - TAX_NORM)
    return rev, ebit, np_op, net_int


def paths(s, np_g=None, rev_g=None, np0=None):
    rev0, _, np_op0, _ = norm_np_2026(s)
    if np0 is not None:
        np_op0 = np0
    np_g = np_g or s["np_g"]
    rev_g = rev_g or s["rev_g"]
    gt = s["g_term"]
    fade_np = [np_g[-1] + (gt - np_g[-1]) * (i + 1) / FADE_YEARS for i in range(FADE_YEARS)]
    fade_rev = [rev_g[-1] + (gt - rev_g[-1]) * (i + 1) / FADE_YEARS for i in range(FADE_YEARS)]
    g_np, g_rev = list(np_g) + fade_np, list(rev_g) + fade_rev
    years = list(range(2027, 2027 + len(g_np)))
    nps, revs, oes, reinv = [], [], [], []
    n, r = np_op0, rev0
    for gn, gr in zip(g_np, g_rev):
        n_new, r_new = n * (1 + gn), r * (1 + gr)
        ri = s["k"] * (r_new - r)
        nps.append(n_new); revs.append(r_new); reinv.append(ri); oes.append(n_new - ri)
        n, r = n_new, r_new
    oe_2026 = np_op0 - s["k"] * (rev0 - REV_2025)
    return dict(years=years, g_np=g_np, g_rev=g_rev, nps=nps, revs=revs, oes=oes, reinv=reinv,
                oe_2026=oe_2026, oe_h2=0.5 * oe_2026, np0=np_op0, rev0=rev0)


def value(s, r, pth=None):
    pth = pth or paths(s)
    pv = pth["oe_h2"] / (1 + r) ** T_YEAREND
    for i, oe in enumerate(pth["oes"]):
        pv += oe / (1 + r) ** (T_MID2027 + i)
    gt = s["g_term"]
    oe_next = pth["nps"][-1] * (1 + gt) * (1 - gt / s["ronic_term"])
    pv_tv = oe_next / (r - gt) / (1 + r) ** (T_MID2027 + len(pth["oes"]) - 1)
    eq = pv + pv_tv + NET_CASH_ADJ + NON_OP
    return dict(v=eq / SHARES, eq=eq, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv))


def solve_rate(s, target_eq, pth=None, lo=0.03, hi=0.25):
    pth = pth or paths(s)
    for _ in range(200):
        mid = (lo + hi) / 2
        if value(s, mid, pth)["eq"] > target_eq:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def reverse_dcf_growth(target_eq, r=COE):
    """现价隐含：2027–36 年利润恒定增速 g（再投资率 = g/50%，即基准增量回报），之后 2.5%。"""
    _, _, np0, _ = norm_np_2026(SCEN["base"])

    def eq_at(g):
        pv = 0.5 * np0 * (1 - g / 0.5) / (1 + r) ** T_YEAREND
        n = np0
        for i in range(10):
            n *= (1 + g)
            pv += n * (1 - g / 0.5) / (1 + r) ** (T_MID2027 + i)
        pv += n * 1.025 * (1 - 0.025 / 0.20) / (r - 0.025) / (1 + r) ** (T_MID2027 + 9)
        return pv + NET_CASH_ADJ + NON_OP

    lo, hi = 0.0, 0.40
    for _ in range(200):
        mid = (lo + hi) / 2
        if eq_at(mid) < target_eq:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_perpetual_g(target_eq, r=COE):
    pth = paths(SCEN["base"])
    return r - pth["oes"][0] / (target_eq - NET_CASH_ADJ - NON_OP)


def falsifier_values():
    b = SCEN["base"]
    out = {}
    # F1 增长：2026 营收同比 < 5% 或海外收入同比 < 12% → 营收增速各年 −3pp、利润增速 −4pp
    p = paths(b, np_g=[g - 0.04 for g in b["np_g"]], rev_g=[g - 0.03 for g in b["rev_g"]])
    out["F1"] = value(b, COE, p)["v"]
    # F2 毛利：2026Q4 或 2027 任一季度毛利率 < 58.5%（存储涨价、价格战）→ 正常化毛利率 −2pp、利润增速 −1pp
    b2 = dict(b, gm=b["gm"] - 0.02)
    out["F2"] = value(b2, COE, paths(b2, np_g=[g - 0.01 for g in b["np_g"]]))["v"]
    # F3 回款：2026 年末应收账款净额 > 15.5 亿或全年信用+资产减值 > 1.6 亿 → 减值率 4%、再投资系数 0.50
    b3 = dict(b, imp=0.040, k=0.50)
    out["F3"] = value(b3, COE)["v"]
    # F4 海外限制：列入实体清单/欧美限制中国高精度定位设备，或海外收入同比下降 → 熊市情景
    out["F4"] = value(SCEN["bear"], COE)["v"]
    # F5 上行：2026「扣除股份支付影响后的净利润」≥ 8.5 亿且 2027H1 海外同比 ≥ 25% → 基准与牛市各半
    out["F5"] = 0.5 * value(b, COE)["v"] + 0.5 * value(SCEN["bull"], COE)["v"]
    return out


def reported_2026_estimate():
    """基准下 2026 年报表口径估计：以 2025 下半年实际为起点逐项调整（含实际股份支付约 1.6 亿与汇兑）。"""
    h2_25_rev = REV_2025 - H1_25_REV
    h2_25_gp = h2_25_rev - (14.43567852 - 7.67550402)                       # 2025 下半年毛利（毛利率约 63.8%）
    h2_26_rev = h2_25_rev * 1.08
    d_gp = h2_26_rev * 0.620 - h2_25_gp                                       # 下半年毛利率 62.0%
    h2_25_opex = (6.78585825 - 3.74722157) + ((2.59680913 - 0.38841104) - (1.15777450 - 0.22201435)) + (5.57996822 - 2.66870680)
    d_opex = -h2_25_opex * 0.06                                               # 销售+管理(不含股份支付)+研发 +6%
    d_sbc = -((1.60 - 0.78616167) - (0.38841104 - 0.22201435))                # 2026 全年约 1.6 亿（IR_20260522 第 5 页）
    d_imp = (1.12035604 - 0.28245303) + (0.24942712 + 0.00123942) - 0.85     # 下半年减值 0.85 亿
    d_oth = 0.40 - ((1.19060372 - 0.59881206) - (0.45844768 - 0.17795592))    # 经常性其他收益 0.40 亿
    d_fx = -(0.30 - (-0.29580829 + 0.33209172))                              # 下半年汇兑损失 0.30 亿
    d_surtax = -(0.12 - (0.19820329 - 0.08757416))
    h2_25_rec_pretax = (7.84894154 - 3.68001211) - (0.92369397 - 0.32)       # 扣除非经常税前（上半年约 0.32 亿）
    h2_26_rec_pretax = h2_25_rec_pretax + d_gp + d_opex + d_sbc + d_imp + d_oth + d_fx + d_surtax
    kf_h2 = h2_26_rec_pretax * (1 - 0.09) - 0.02
    kf_fy = 2.71945706 + kf_h2
    gm_fy = (H1_26_REV - 7.59604857 + h2_26_rev * 0.620) / (H1_26_REV + h2_26_rev)
    np_fy = 3.33157564 + kf_h2 + 0.49 * (1 - 0.15)                            # 下半年补助+理财等非经常约 0.49 亿
    reversal = 2.81 * 0.40 * 11.15 / 15 * (1 - 0.09)                          # 首期 40% 未达标时冲回（总成本约 2.81 亿推算）
    ex_sbc = np_fy + 1.60 * 0.85                                              # 公司口径「扣除股份支付影响后的净利润」
    return dict(kf_fy=kf_fy, np_fy=np_fy, gm_fy=gm_fy, rev_fy=H1_26_REV + h2_26_rev,
                kf_rev=kf_fy + reversal, np_rev=np_fy + reversal, ex_sbc=ex_sbc)


def q3_2026_estimate():
    """三季报（2026-10-23）核对点：基准下单季区间（与正常化无关，含汇兑与实际股份支付）。"""
    usd_net = 35.937 + 47.056 + 8.230 + 58.103 - 12.233 - 7.897     # 百万美元，2026-06-30 美元货币性净资产（第 159–160 页）
    eur_net = 15.645 + 22.629 + 0.523 + 19.104 - 10.742 - 0.084     # 百万欧元
    fx_usd = usd_net * (6.9170 - 6.7351) / 100                      # 亿元；中间价 6.9170（6-30）→ 6.7351（9-30）
    rev_q3_25 = 7.84906043
    lo, hi = rev_q3_25 * 1.04, rev_q3_25 * 1.12
    return usd_net, eur_net, fx_usd, lo, hi


def main():
    mcap = PRICE * SHARES
    print("=== 华测导航 300627 独立估值（价格日 2026-10-21，现价 %.2f 元，总股本 %.4f 亿股，市值 %.2f 亿）===" % (PRICE, SHARES, mcap))

    print("\n[1] TTM（2025 年报 + 2026H1 − 2025H1，亿元）")
    for k_, v_ in TTM.items():
        print("  %-14s %8.3f" % (k_, v_))
    print("  有效税率 %.1f%%；经营现金流/归母 %.2f" % (TTM["所得税"] / TTM["利润总额"] * 100, TTM["经营现金流"] / TTM["归母净利"]))
    nop, fx_add, sbc_adj, int_net = ttm_normalized_op()
    print("  TTM 扣非 %.3f + 汇兑归零 %.3f + 股份支付换常态 1.1 亿 %.3f + 剔除银行净利息 %.3f = 经营口径 %.3f（TTM 营收 %.2f，净利率 %.1f%%）"
          % (TTM["扣非归母"], fx_add, sbc_adj, int_net, nop, TTM_REV, nop / TTM_REV * 100))
    kf = {2021: (2.30, 19.03), 2022: (2.84, 22.36), 2023: (3.72, 26.78), 2024: (5.04, 32.51), 2025: (6.05, 36.99)}
    print("  扣非净利率 " + " ".join("%d:%.1f%%" % (y, a / b * 100) for y, (a, b) in kf.items())
          + "；2021–25 中枢 %.1f%%，TTM %.1f%%" % (sum(a / b for a, b in kf.values()) / 5 * 100, TTM["扣非归母"] / TTM_REV * 100))

    print("\n[2] 经调整净现金（2026-06-30，亿元）")
    print("  货币资金 %.3f + 理财 %.3f + 远期净额 %.3f + 其他流动资产债权投资 %.3f + 大额存单 %.3f = 金融资产 %.3f"
          % (cash, wealth, fx_fwd_asset - fx_fwd_liab, oca_debt_inv, cd_total, gross_fin))
    print("  − 受限 %.3f − 经营备付 %.3f − 有息负债 %.3f − 担保预期损失 %.3f = 经调整净现金 %.3f（%.2f 元/股）"
          % (restricted, op_reserve, debt, guar_adj, NET_CASH_ADJ, NET_CASH_ADJ / SHARES))
    print("  租赁负债 %.3f 只列示不扣；非经营资产 %.3f；担保余额全额按债务扣时 V 再 −%.2f 元/股"
          % (lease_liab, NON_OP, guarantee_bal * (1 - guarantee_loss) / SHARES))

    print("\n[3] 2026 正常化（报表口径：研发全额费用化、股份支付按常态、汇兑归零、剔除补助/理财/处置）")
    norm = {}
    for name, s in SCEN.items():
        rev, ebit, np_op, net_int = norm_np_2026(s)
        norm[name] = np_op + net_int
        print("  %-4s 营收 %.2f  EBIT %.2f  经营净利 %.2f（%.1f%%）+ 税后净利息 %.2f = 正常化归母 %.2f"
              % (name, rev, ebit, np_op, np_op / rev * 100, net_int, np_op + net_int))

    print("\n[4] 三情景 DCF（股权成本 9%，8%/10% 敏感性）")
    res = {}
    for name, s in SCEN.items():
        pth = paths(s)
        v9, v8, v10 = value(s, 0.09, pth), value(s, 0.08, pth), value(s, 0.10, pth)
        res[name] = (v9, v8, v10, pth)
        rr = sum(pth["reinv"][:5]) / sum(pth["nps"][:5])
        inc_ret = (pth["nps"][4] - pth["np0"]) / sum(pth["reinv"][:5])
        print("  %-4s p=%.2f  V9=%.2f  V8=%.2f  V10=%.2f  终值占比 %.0f%%  2027–31 再投资率 %.0f%%  增量回报 %.0f%%"
              % (name, s["p"], v9["v"], v8["v"], v10["v"], v9["tv_share"] * 100, rr * 100, inc_ret * 100))
        print("        利润增速 " + " ".join("%d:%.1f%%" % (y, g * 100) for y, g in zip(pth["years"], pth["g_np"]))
              + "  终值 %.1f%%" % (s["g_term"] * 100))
        oe_list = [pth["oe_2026"]] + pth["oes"][:5]
        oe_g = [oe_list[i + 1] / oe_list[i] - 1 for i in range(5)]
        print("        所有者收益 2026:%.2f " % pth["oe_2026"]
              + " ".join("%d:%.2f" % (y, o) for y, o in zip(pth["years"][:5], pth["oes"][:5]))
              + "  增速 " + " ".join("%.1f%%" % (g * 100) for g in oe_g)
              + "  2031 营收 %.1f 经营净利 %.2f（%.1f%%）" % (pth["revs"][4], pth["nps"][4], pth["nps"][4] / pth["revs"][4] * 100))
    vw = sum(SCEN[n]["p"] * res[n][0]["v"] for n in SCEN)
    vw8 = sum(SCEN[n]["p"] * res[n][1]["v"] for n in SCEN)
    vw10 = sum(SCEN[n]["p"] * res[n][2]["v"] for n in SCEN)
    pv = PRICE / vw
    print("\n  加权 V = %.2f 元；P/V = %.2f → %s" % (vw, pv, verdict(pv)))
    print("  加权 V(8%%) = %.2f 元（P/V %.2f）；加权 V(10%%) = %.2f 元（P/V %.2f）" % (vw8, PRICE / vw8, vw10, PRICE / vw10))
    print("  V 不变时各档价格：≤%.2f 明显低估；%.2f–%.2f 温和低估；%.2f–%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print("  无回购专户股份，剔除口径 V 相同；正常化归母三档（含净利息）bear/base/bull = %.2f/%.2f/%.2f"
          % (norm["bear"], norm["base"], norm["bull"]))

    print("\n[5] 现价隐含回报与反向 DCF")
    r_imp = solve_rate(SCEN["base"], mcap)
    print("  基准所有者收益流（含终值与净现金）使现值 = 市值的折现率：%.2f%%" % (r_imp * 100))
    print("  反向 DCF：2027–36 年利润恒定增速 %.1f%%（9%% 折现，之后 2.5%%）" % (reverse_dcf_growth(mcap) * 100))
    print("  反向 DCF：以 2027 基准所有者收益计的永续增速 %.2f%%" % (implied_perpetual_g(mcap) * 100))

    print("\n[6] 交叉验证")
    ev = mcap - NET_CASH_ADJ - NON_OP
    _, ebit_b, np_b, _ = norm_np_2026(SCEN["base"])
    print("  EV（扣经调整净现金与非经营资产）%.1f 亿；EV/2026 正常化 EBIT %.1f×；EV/经营净利 %.1f×" % (ev, ev / ebit_b, ev / np_b))
    print("  市值/TTM 归母 %.1f×；市值/TTM 扣非 %.1f×；PB %.2f×" % (mcap / TTM["归母净利"], mcap / TTM["扣非归母"], mcap / parent_equity))
    hist_pe = [40.4, 38.1, 39.4, 59.2, 41.2, 37.6, 39.3, 40.1]
    hist_pb = [4.91, 5.34, 7.15, 7.96, 5.87, 5.61, 6.53, 6.54]
    print("  2018–25 年末 PE %.1f–%.1f×（中位 %.1f×），PB %.2f–%.2f×；按基准正常化归母 × 历史最低 PE = %.1f 元"
          % (min(hist_pe), max(hist_pe), sorted(hist_pe)[3:5][0] / 2 + sorted(hist_pe)[3:5][1] / 2, min(hist_pb), max(hist_pb),
             norm["base"] * min(hist_pe) / SHARES))
    div_yield = 0.45 / PRICE
    dilution = (7.9397 - 7.8644) / 7.8644
    print("  股息率 %.2f%%；2026 年以来股本 +%.2f%%（限制性股票归属），股息减稀释约 %.2f%%"
          % (div_yield * 100, dilution * 100, (div_yield - dilution) * 100))

    print("\n[7] 2026 报表口径估计与三季报核对（2026-10-23）")
    rep = reported_2026_estimate()
    print("  基准报表口径：2026 营收 %.2f 亿、毛利率 %.1f%%、扣非 %.2f 亿、归母 %.2f 亿、扣除股份支付影响后净利 %.2f 亿"
          % (rep["rev_fy"], rep["gm_fy"] * 100, rep["kf_fy"], rep["np_fy"], rep["ex_sbc"]))
    print("  第三期激励首期（2026 扣非 ≥ 6.655 亿）若判定不达标并冲回已摊销费用：扣非 %.2f 亿、归母 %.2f 亿（非现金，不进估值）"
          % (rep["kf_rev"], rep["np_rev"]))
    usd_net, eur_net, fx_usd, lo, hi = q3_2026_estimate()
    print("  6-30 美元货币性净资产 %.1f 百万美元、欧元 %.1f 百万欧元；美元中间价 6.9170→6.7351 对应三季度汇兑损失约 %.2f 亿（未计远期对冲与欧元）"
          % (usd_net, eur_net, fx_usd))
    print("  基准下三季度营收 %.2f–%.2f 亿（同比 +4%%～+12%%）；去年同期毛利率 65.7%% 为高点，单季归母同比下降不改变本估值" % (lo, hi))

    print("\n[8] 证伪条件触发后的 V（9%）")
    fv = falsifier_values()
    labels = {"F1": "营收<5%或海外<12%", "F2": "单季毛利率<58.5%", "F3": "应收/减值恶化",
              "F4": "海外限制(熊市)", "F5": "上行:扣股份支付净利≥8.5亿且海外≥25%"}
    for k_, v_ in fv.items():
        print("  %s %-28s V = %.2f 元（P/V %.2f）" % (k_, labels[k_], v_, PRICE / v_))

    return dict(vw=vw, pv=pv, vw8=vw8, vw10=vw10, r_imp=r_imp, res=res, norm=norm, fv=fv)


if __name__ == "__main__":
    main()
