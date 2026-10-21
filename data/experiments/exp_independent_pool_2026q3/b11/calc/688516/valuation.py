# -*- coding: utf-8 -*-
"""奥特维（688516）独立估值：所有者收益 DCF（有杠杆口径）+ 可转债逐情景取低 + 反向 DCF。

运行：python3 valuation.py
金额单位：亿元；每股：元。价格日 2026-10-20。最新定期报告 2026 中报（2026-06-30）。
输入全部写在本脚本内，来源见同批 companies/688516_奥特维.md 第 8 节与来源表。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 38.15                  # 2026-10-20 收盘
SHARES = 3.1476                # 亿股，2026-07-01 注销限制性股票后 314,760,458 股；无回购专户股份
VAL_DATE = date(2026, 10, 20)
TAX = 0.15                     # 正常化有效税率（高新 15%，加计扣除抵消子公司亏损不可抵）

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report 第 144-193 页）
CASH = 21.704                  # 货币资金
RESTRICTED = 0.857             # 其他货币资金（保证金、存出投资款，报告列为受限）
TRADING_FA = 0.446             # 交易性金融资产（理财 0.37 + 中利集团股票 0.08）
OPER_RESERVE = 3.0             # 经营备付，约正常化营收的 5%
DIV_AFTER_BS = 0.30 * SHARES   # 2026 中期分红 0.30 元/股，2026-09-24 发放，期后扣除
ST_LOAN = 12.854               # 短期借款
DISCOUNTED_NOTES = 3.904       # 其中：未终止确认的应收款项融资（贴现票据），与应收款项融资对冲，不计有息负债
LT_LOAN = 9.064
LT_LOAN_CURRENT = 2.583        # 一年内到期的长期借款
LEASE = 0.165 + 0.113          # 租赁负债（含一年内到期）
FACTORING = 0.569              # 其他非流动负债：保理融资款（类债务）
BANK_RATE = 0.022              # 有息负债实际平均利率：H1 利息（费用化 0.225 + 资本化 0.358 − 转债 0.339）×2 / 平均银行借款 22.1

# 非经营资产：其他非流动金融资产 4.289（上市股权 1.164、非上市股权 2.883、债务工具 0.242）+ 长投 0.020
LISTED_EQ, UNLISTED_EQ, DEBT_INSTR, LT_EQ_INV = 1.164, 2.883, 0.242, 0.020

# ---------------------------------------------------------------- 可转债（奥维转债 118042）
CB_FACE = 11.3992              # 未转股面值（11,399,180 张 × 100 元）
CONV_PRICE = 83.39             # 2026-09-24 起转股价
CB_CF = [(date(2027, 8, 10), 0.015), (date(2028, 8, 10), 0.020), (date(2029, 8, 9), 1.15)]  # 第4年1.5%、第5年2.0%、到期按面值115%（含最后一期利息）赎回
CB_DISC = 0.03                 # 债底折现率（AA- 主体、剩余约 2.8 年）


def yrs(d):
    return (d - VAL_DATE).days / 365.25


def cb_floor(rate=CB_DISC):
    return sum(CB_FACE * c / (1 + rate) ** yrs(d) for d, c in CB_CF)


def bank_debt():
    return ST_LOAN - DISCOUNTED_NOTES + LT_LOAN + LT_LOAN_CURRENT + LEASE + FACTORING


def net_cash_adj():
    """无杠杆口径经调整净现金（不含可转债）。"""
    cash_like = CASH - RESTRICTED + TRADING_FA
    return cash_like - OPER_RESERVE - DIV_AFTER_BS - bank_debt()


def non_operating(haircut_unlisted):
    return LISTED_EQ + (UNLISTED_EQ + DEBT_INSTR + LT_EQ_INV) * (1 - haircut_unlisted)


# ---------------------------------------------------------------- 情景
# rev：2026E-2031E 营收；m：经营性归母净利率（税后、未计净利息与转债利息、剔除一次性项目、少数股东不再分担亏损、含股份支付）
# k_nwc：增量营收所需净营运资金；release：营收下降时营运资金可回收比例；capex_g：增量营收所需净资本开支
# netcapex_2027：两大在建项目收尾（剩余预算约 6.4 亿，2026H2 约 3.0、2027 约 3.4）减折旧后的净额
SCEN = {
    "bear": dict(p=0.25, rev=[57.0, 50.0, 50.0, 52.0, 54.0, 55.0],
                 m=[0.045, 0.030, 0.050, 0.063, 0.063, 0.063],
                 k_nwc=0.30, release=0.5, capex_g=0.15, netcapex_2027=1.2,
                 g_term=0.015, roic_term=0.10, haircut=0.50, mid_rev=52.0, mid_m=0.060),
    "base": dict(p=0.50, rev=[60.0, 67.0, 71.0, 73.5, 75.5, 77.0],
                 m=[0.062, 0.090, 0.100, 0.105, 0.105, 0.105],
                 k_nwc=0.25, release=0.5, capex_g=0.15, netcapex_2027=1.2,
                 g_term=0.025, roic_term=0.15, haircut=0.25, mid_rev=64.0, mid_m=0.097),
    "bull": dict(p=0.25, rev=[61.0, 74.0, 84.0, 90.0, 94.0, 97.0],
                 m=[0.070, 0.105, 0.120, 0.130, 0.130, 0.130],
                 k_nwc=0.20, release=0.5, capex_g=0.15, netcapex_2027=1.2,
                 g_term=0.025, roic_term=0.18, haircut=0.25, mid_rev=74.0, mid_m=0.115),
}
REV_2025 = 63.97
REV_2026H1 = 27.19
NETCAPEX_2026H2 = 2.1          # 2026H2 项目付款约 3.0 − 折旧约 0.9
INT_INCOME = 0.137             # 年利息收入（H1 0.068 × 2）
# 登记口径净利息：银行借款 21.44 × 2.2% − 利息收入；转债按债底 × 3% 计息（介于票息 0.2 亿与会计实际利率摊销约 0.67 亿之间）
YEARS = [2026, 2027, 2028, 2029, 2030, 2031]

# 中枢经营净利率的自下而上拆分（亿元）：综合毛利 =（毛利率 − 存货与信用减值率）× 营收，
# 因存货跌价转销会抬高确认收入当期的毛利率（2026H1 转销 1.47 亿），按“毛利率 − 减值”合并口径正常化。
BUILD = {
    # 营收, 毛利率, 减值率, 销售, 管理(不含股份支付), 研发, 税金附加, 股份支付, 其他收益(经常性), 新厂折旧增量, 盈利子公司少数股东
    "bear 2029E": (54.0, 0.315, 0.055, 1.50, 3.40, 3.90, 0.45, 0.50, 0.45, 0.60, 0.10),
    "base 2026 正常化": (64.0, 0.330, 0.045, 1.66, 3.60, 4.30, 0.50, 0.60, 0.50, 0.60, 0.19),
    "base 2029E": (73.5, 0.330, 0.045, 1.91, 3.80, 4.70, 0.60, 0.60, 0.60, 0.60, 0.25),
    "bull 2029E": (90.0, 0.345, 0.040, 2.16, 4.30, 5.40, 0.75, 0.70, 0.75, 0.60, 0.35),
}


def margin_build(rev, gm, imp, sell, adm, rd, taxadd, sbc, oth, dep_up, mino):
    ebit = rev * (gm - imp) - sell - adm - rd - taxadd - sbc + oth - dep_up
    np_op = ebit * (1 - TAX) - mino
    return ebit, np_op, np_op / rev


# TTM（2025H2 + 2026H1）桥接：扣非 2.90；减值 6.89（2025 全年 5.73 − 2025H1 1.56 + 2026H1 2.71）；
# 少数股东分担亏损 0.70；营收 57.36；综合毛利率（毛利率 36.1% − 减值率 12.0%）= 24.1%；P&L 净利息约 0.30（税前）
TTM = dict(rev=57.36, kf=2.90, imp=6.889, gm=0.361, mino_absorb=0.705, net_int=0.30)


def owner_earnings(s):
    """返回 [(年份, 营收, 经营净利, 营运资金增加, 净资本开支, 所有者收益)]，2026 行只含下半年。"""
    rows = []
    prev = REV_2025
    for i, y in enumerate(YEARS):
        r, m = s["rev"][i], s["m"][i]
        np_op = r * m
        if y == 2026:
            h2_rev = r - REV_2026H1
            np_h2 = h2_rev * m
            rows.append((y, r, np_h2, 0.0, NETCAPEX_2026H2, np_h2 - NETCAPEX_2026H2))
            prev = r
            continue
        d = r - prev
        dnwc = s["k_nwc"] * d if d >= 0 else s["k_nwc"] * d * s["release"]
        ncx = s["capex_g"] * max(d, 0.0) + (s["netcapex_2027"] if y == 2027 else 0.0)
        rows.append((y, r, np_op, dnwc, ncx, np_op - dnwc - ncx))
        prev = r
    return rows


def t_mid(y):
    """2026H2 现金流按 2026-11-30 计；以后各年按年中。"""
    if y == 2026:
        return yrs(date(2026, 11, 30))
    return yrs(date(y, 7, 1))


def dcf(s, r):
    rows = owner_earnings(s)
    pv = sum(oe / (1 + r) ** t_mid(y) for y, _, _, _, _, oe in rows)
    np_last = rows[-1][2]
    g = s["g_term"]
    oe_t = np_last * (1 + g) * (1 - g / s["roic_term"])
    tv = oe_t / (r - g)                            # 位于 2031 年中（下一笔在 2032 年中）
    pv_tv = tv / (1 + r) ** t_mid(2031)
    return pv, pv_tv, rows, oe_t


def equity_value(s, r, levered=True):
    pv, pv_tv, rows, oe_t = dcf(s, r)
    nc = net_cash_adj()
    if levered and nc < 0:
        int_after_tax = -nc * BANK_RATE * (1 - TAX)
        debt_adj = -int_after_tax / r              # 净负债按现规模滚动、不还本
    else:
        debt_adj = nc
    eq = pv + pv_tv + debt_adj + non_operating(s["haircut"])
    return eq, pv, pv_tv, debt_adj


def per_share(s, r, levered=True):
    eq = equity_value(s, r, levered)[0]
    v_debt = (eq - cb_floor()) / SHARES
    v_conv = eq / (SHARES + CB_FACE / CONV_PRICE)
    return min(v_debt, v_conv), v_debt, v_conv


def weighted(r, levered=True, probs=None):
    probs = probs or {k: v["p"] for k, v in SCEN.items()}
    return sum(probs[k] * per_share(SCEN[k], r, levered)[0] for k in SCEN)


def implied_irr(s):
    """基准所有者收益流（含终值与净现金调整）使现值等于现价的折现率。"""
    lo, hi = 0.03, 0.20
    for _ in range(200):
        mid = (lo + hi) / 2
        if per_share(s, mid)[0] > PRICE:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def target_operating_value(r=0.09):
    """现价对应的经营价值：市值 + 转债债底 − 净负债利息调整 − 非经营资产。"""
    s = SCEN["base"]
    return PRICE * SHARES + cb_floor() - equity_value(s, r)[3] - non_operating(s["haircut"])


def reverse_dcf_10y(r=0.09, g_term=0.025, roic=0.15):
    """现价隐含：以基准正常化所有者收益（64 亿 × 10% ×（1 − 2.5%/15%））为 2026 年起点，
    2027-2036 年所有者收益年均增速 g，之后 2.5% 永续。"""
    s = SCEN["base"]
    target = target_operating_value(r)
    oe0 = s["mid_rev"] * s["mid_m"] * (1 - g_term / roic)

    def pv_for(g):
        pv, oe = 0.0, oe0
        for y in range(2027, 2037):
            oe *= (1 + g)
            pv += oe / (1 + r) ** t_mid(y)
        pv += oe * (1 + g_term) / (r - g_term) / (1 + r) ** t_mid(2036)
        return pv

    lo, hi = -0.10, 0.40
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv_for(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2, target, oe0


def reverse_perpetual(r=0.09, roic=0.15):
    """现价隐含：以基准正常化归母经营净利（64 亿 × 10%）为起点的永续增长率。"""
    s = SCEN["base"]
    target = target_operating_value(r)
    np0 = s["mid_rev"] * s["mid_m"]
    lo, hi = -0.05, 0.085
    for _ in range(200):
        g = (lo + hi) / 2
        v = np0 * (1 + g) * (1 - g / roic) / (r - g)
        if v < target:
            lo = g
        else:
            hi = g
    return (lo + hi) / 2


def net_interest_after_tax():
    bank = bank_debt() * BANK_RATE - INT_INCOME
    cb = cb_floor() * CB_DISC
    return (bank + cb) * (1 - TAX)


def normalized_np_2026(s):
    """登记口径：正常化营收 × 中枢经营净利率 − 税后净利息（银行净利息 + 转债按债底计息）。"""
    return s["mid_rev"] * s["mid_m"] - net_interest_after_tax()


def ttm_bridge(norm_combined=0.285, contrib_after_tax=0.217, norm_rev=64.0, dep_up_after_tax=0.51):
    t = TTM
    combined = t["gm"] - t["imp"] / t["rev"]
    cyc = (norm_combined - combined) * t["rev"] * (1 - TAX)      # 综合毛利回到中枢
    op_ttm = t["kf"] + cyc - t["mino_absorb"] + t["net_int"] * (1 - TAX)
    scale = (norm_rev - t["rev"]) * contrib_after_tax           # 营收回到正常化水平的经营杠杆
    return combined, cyc, op_ttm, scale, op_ttm + scale - dep_up_after_tax


def main():
    print("=== 奥特维 688516 独立估值（价格日 2026-10-20，现价 %.2f 元，总股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("中枢经营净利率自下而上：")
    for k, args in BUILD.items():
        ebit, npo, mm = margin_build(*args)
        print("  %s：营收 %.1f，EBIT %.2f，经营净利 %.2f，经营净利率 %.1f%%" % (k, args[0], ebit, npo, mm * 100))
    comb, cyc, op_ttm, scale, op_norm = ttm_bridge()
    print("TTM 桥接：综合毛利率 %.1f%%（中枢 28.5%%）→ 周期性加回 %.2f；TTM 经营净利 %.2f；营收回到 64 亿 +%.2f；"
          "扣新厂折旧 → 正常化 %.2f 亿元" % (comb * 100, cyc, op_ttm, scale, op_norm))
    nc = net_cash_adj()
    print("银行有息负债（不含转债、不含贴现票据）%.2f；经调整净现金（无杠杆口径）%.2f 亿元" % (bank_debt(), nc))
    print("可转债：面值 %.2f，债底现值（3%%）%.2f，全部转股增加 %.4f 亿股（转股价 %.2f）"
          % (CB_FACE, cb_floor(), CB_FACE / CONV_PRICE, CONV_PRICE))
    print()
    for k, s in SCEN.items():
        print("--- %s（概率 %.2f）---" % (k, s["p"]))
        print("年份  营收  经营净利  营运资金+  净资本开支  所有者收益")
        for y, rv, npo, dn, cx, oe in owner_earnings(s):
            tag = "H2" if y == 2026 else "  "
            print("%d%s %6.1f %8.2f %9.2f %10.2f %10.2f" % (y, tag, rv, npo, dn, cx, oe))
        for r in (0.08, 0.09, 0.10):
            eq, pv, pvtv, dadj = equity_value(s, r)
            v, vd, vc = per_share(s, r)
            v_unlev = per_share(s, r, levered=False)[0]
            print("r=%.0f%%：经营 PV %.1f + 终值 PV %.1f（占 %.0f%%）+ 净负债调整 %.2f + 非经营 %.2f = %.1f；"
                  "债务法 %.2f / 转股法 %.2f → 取低 %.2f；无杠杆口径 %.2f"
                  % (r * 100, pv, pvtv, pvtv / (pv + pvtv) * 100, dadj, non_operating(s["haircut"]), eq, vd, vc, v, v_unlev))
        print("2026 正常化归母净利（登记口径）%.2f 亿元" % normalized_np_2026(s))
        print()
    vw = weighted(0.09)
    print("加权 V（9%%，有杠杆口径）= %.2f 元；P/V = %.2f" % (vw, PRICE / vw))
    print("加权 V（9%%，无杠杆口径）= %.2f 元；P/V = %.2f" % (weighted(0.09, levered=False), PRICE / weighted(0.09, levered=False)))
    print("加权 V（8%%）= %.2f；加权 V（10%%）= %.2f" % (weighted(0.08), weighted(0.10)))
    cb_face_accrued = CB_FACE * (1 + 0.015 * (VAL_DATE - date(2026, 8, 10)).days / 365.25)
    face_adj = (cb_floor() - cb_face_accrued) / SHARES
    print("对照：转债按面值加应计利息 %.2f 亿元扣除（而非债底 %.2f），加权 V 高 %.2f 元 = %.2f"
          % (cb_face_accrued, cb_floor(), face_adj, vw + face_adj))
    print("分档价格（V 不变）：明显低估 ≤ %.2f；温和低估 %.2f～%.2f；大致合理 %.2f～%.2f；偏贵 > %.2f"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    irr = implied_irr(SCEN["base"])
    print("现价隐含回报（基准情景）= %.2f%%" % (irr * 100))
    g10, tgt, oe0 = reverse_dcf_10y()
    print("反向 DCF：现价对应的经营价值 %.1f 亿元；以正常化所有者收益 %.2f 亿元为起点，2027-2036 年均增速 %.1f%%（之后 2.5%%）"
          % (tgt, oe0, g10 * 100))
    print("反向 DCF：以基准正常化经营净利 %.2f 亿元为起点的隐含永续增速 %.2f%%"
          % (SCEN["base"]["mid_rev"] * SCEN["base"]["mid_m"], reverse_perpetual() * 100))
    # 交叉验证
    mcap = PRICE * SHARES
    ev = mcap + cb_floor() - nc - non_operating(0.25)
    np_norm_base = normalized_np_2026(SCEN["base"])
    ebit_norm = SCEN["base"]["mid_rev"] * SCEN["base"]["mid_m"] / (1 - TAX)
    print("交叉：市值 %.1f；EV（含转债债底、净负债，扣非经营）%.1f；EV/正常化 EBIT %.1f×；市值/基准正常化净利 %.1f×；"
          "PB %.2f；TTM 股息率 %.2f%%" % (mcap, ev, ev / ebit_norm, mcap / np_norm_base, mcap / 37.94, 1.10 / PRICE * 100))
    print("交叉：加权 V 对应 PB %.2f（每股净资产 %.2f）；对应正常化基准 PE %.1f×"
          % (vw / (37.94 / SHARES), 37.94 / SHARES, vw * SHARES / np_norm_base))
    print("登记口径税后净利息 %.2f 亿元/年" % net_interest_after_tax())
    # 证伪触发后的 V（概率重配或改基准）
    f1 = weighted(0.09, probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    f3 = weighted(0.09, probs={"bear": 0.40, "base": 0.45, "bull": 0.15})
    slow = dict(SCEN["base"], rev=[60.0, 65.0, 66.0, 67.5, 69.0, 70.0])
    v_slow = per_share(slow, 0.09)[0]
    probs = {k: v["p"] for k, v in SCEN.items()}
    f4 = probs["bear"] * per_share(SCEN["bear"], 0.09)[0] + probs["base"] * v_slow + probs["bull"] * per_share(SCEN["bull"], 0.09)[0]
    print("证伪：利润兑现不及（0.40/0.45/0.15）V = %.2f；新业务放缓（基准营收 2031E 70 亿）基准 V = %.2f，加权 V = %.2f"
          % (f3, v_slow, f4))
    f2 = weighted(0.09, probs={"bear": 0.10, "base": 0.50, "bull": 0.40})
    print("证伪：概率移向熊（0.5/0.4/0.1）V = %.2f；移向牛（0.1/0.5/0.4）V = %.2f" % (f1, f2))
    bear_v = per_share(SCEN["bear"], 0.09)[0]
    print("证伪：熊市情景单独成立时 V = %.2f" % bear_v)
    print("汇总：熊 %.2f / 基准 %.2f / 牛 %.2f；加权 %.2f；P/V %.2f；8%% %.2f；10%% %.2f；隐含回报 %.4f；"
          "经调整净现金 %.2f；非经营资产 %.2f"
          % (per_share(SCEN["bear"], 0.09)[0], per_share(SCEN["base"], 0.09)[0], per_share(SCEN["bull"], 0.09)[0],
             vw, PRICE / vw, weighted(0.08), weighted(0.10), irr, nc, non_operating(SCEN["base"]["haircut"])))
    base_conv_low = (equity_value(SCEN["base"], 0.09)[0]) / (SHARES + CB_FACE / 40.0)
    print("对照：若转股价下修至 40 元，基准情景转股法 V = %.2f（债务法 %.2f）"
          % (base_conv_low, per_share(SCEN["base"], 0.09)[1]))


if __name__ == "__main__":
    main()
