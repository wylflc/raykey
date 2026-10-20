"""健帆生物（300529）独立估值：OI-291 b08 深度版。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。所有输入写在本脚本内，来源见正文
companies/300529_健帆生物.md 与 companies/300529.json 的 spot_checks。

方法：经营所有者收益 DCF（股权成本 9%，8%/10% 敏感性）+ 经调整净现金（不含可转债）
+ 非经营资产 − 可转债（逐情景取低：债务法＝扣除 110% 到期赎回额的现值；
全部转股法＝股本加 9.998 亿面值 / 38.15 元的转股数、不扣转债）。
"""

from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 15.24                      # 2026-10-20 收盘，元
SHARES_TOTAL = 7.98605275          # 亿股，含回购专户（腾讯行情口径，2026H1 第 32 页）
TREASURY = 0.24242720              # 亿股，回购专户（2026H1 第 34 页）
SHARES_EX_TREASURY = SHARES_TOTAL - TREASURY   # 7.74362555，2025 年度分红股本基数
VAL_DATE = date(2026, 10, 20)
COE = 0.09

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1 第 42–45、90、121、126–127 页）
CASH = 5.97216620                  # 货币资金
TRADING_FA = 17.85827340           # 交易性金融资产（银行/券商理财，R1–R2）
LT_DEPOSIT = 1.05257778            # 其他非流动资产中一年以上定期存款及应收利息
RESTRICTED = 0.07911823            # 受限货币资金
OP_RESERVE = 1.0                   # 经营备付（约营收 5%）
DEBT = (0.02155243                 # 短期借款
        + 1.70523505 + 0.07867113 + 0.00126674   # 长期借款 + 一年内到期部分 + 应计利息
        + 0.03201815 + 0.01752851)               # 租赁负债（含一年内到期）
AIDUODUO_BUYOUT = 0.17592          # 2026-08 受让爱多多 37.6% 的承诺付款（关联方众焱科技）
DECLARED_DIV = 0.0                 # 6-30 后无已宣派未付股利
# 非经营资产：众惠财产相互保险社 1.0227 + 健福制药（实控人控制）0.2839，均打五折
NON_OP = 0.5 * (1.02270788 + 0.28391623)

NET_CASH_ADJ = (CASH + TRADING_FA + LT_DEPOSIT - RESTRICTED - OP_RESERVE
                - DEBT - AIDUODUO_BUYOUT - DECLARED_DIV)

# ---------------------------------------------------------------- 可转债（健帆转债 123117）
CB_FACE = 9.998292                 # 2026-09-30 剩余面值（2026Q3 转股情况公告）
CB_REDEEM_RATIO = 1.10             # 到期按面值 110%（含最后一期利息）赎回（受托管理事务报告第 8 页）
CB_CONV_PRICE = 38.15              # 2026-06-01 起转股价
CB_REDEEM_DATE = date(2027, 6, 29)  # 2027-06-22 到期后五个交易日内
CB_DEBT_RATE = 0.025               # 债底折现率（AA 短久期）
T_CB = (CB_REDEEM_DATE - VAL_DATE).days / 365.0
CB_PV = CB_FACE * CB_REDEEM_RATIO / (1 + CB_DEBT_RATE) ** T_CB
CB_CONV_SHARES = CB_FACE / CB_CONV_PRICE   # 亿股

# ---------------------------------------------------------------- 2026H1 实际（2026H1 第 48–49 页）
H1 = dict(rev=10.32473665, cogs=2.22436554, tax_sur=0.19162951, sell=1.61863474,
          ga=0.70775982, rd=1.03092779)
H1_ACT_ADJ = 0.12666678 - 0.01576059 - 0.19992056 + 0.00059818 - 0.04981209 - 0.00113196
# 实际：其他收益、信用减值、资产减值、营业外收支、资产处置
NORM_ADJ = 0.016   # 正常化：常态减值 0.8% + 常态捐赠 0.8%（占营收），不计政府补助与理财收益
TAX = 0.165        # 正常化所得税率（高新 15%，2023–2025 实际 18–20%，2026H1 14.3%）

# 2026 净利息（税前）：H1 实际 利息收入 0.0946 + 理财 0.0598 + 0.1882 − 利息费用净额 0.2478；H2 估计 0.04
NET_INTEREST_2026 = (0.09460290 + 0.05978577 + 0.18816274 - (0.26919931 - 0.02139406)) + 0.04

# 时点（年，距 2026-10-20）
T_H2_2026 = 0.1
YEARS = [2027, 2028, 2029, 2030, 2031]
T_MID = {y: (date(y, 7, 1) - VAL_DATE).days / 365.0 for y in YEARS}

SCENARIOS = {
    "bear": dict(
        p=0.25,
        h2=dict(rev=7.90, gm=0.76, tax_sur=0.16, sell=1.75, ga=0.68, rd=1.05),
        growth=[-0.03, -0.28, 0.02, 0.03, 0.03],      # 2028 年灌流器纳入联盟带量采购：价 −50%、量 +20%
        margin=[0.35, 0.30, 0.30, 0.30, 0.30],
        da=[1.42, 1.50, 1.60, 1.62, 1.64], capex=[2.90, 2.00, 1.60, 1.60, 1.65],
        g_term=0.010, ronic=0.12,
        assumptions="2026H2 营收 −10%；2027 −3%；2028 灌流器纳入省际联盟带量采购（价 −50%、量 +20%，营收 −28%），"
                    "经营利润率 35%→30%；此后 +2～3%，终值增长 1%。"),
    "base": dict(
        p=0.50,
        h2=dict(rev=8.40, gm=0.77, tax_sur=0.17, sell=1.65, ga=0.68, rd=1.05),
        growth=[0.02, 0.03, 0.03, 0.03, 0.03],
        margin=[0.38, 0.38, 0.38, 0.38, 0.38],
        da=[1.42, 1.50, 1.60, 1.63, 1.66], capex=[2.90, 2.30, 1.70, 1.75, 1.80],
        g_term=0.020, ronic=0.20,
        assumptions="2026H2 营收 −4%、销售费用维持上半年水平；2027 +2%（KHA 替代 HA130 的降价效应走完），"
                    "2028–2031 +3%（透析人数 +8～10% 抵消单价下行）；未纳入集采；经营利润率 38%；终值增长 2%。"),
    "bull": dict(
        p=0.25,
        h2=dict(rev=8.80, gm=0.78, tax_sur=0.18, sell=1.60, ga=0.68, rd=1.05),
        growth=[0.08, 0.09, 0.08, 0.06, 0.05],
        margin=[0.40, 0.40, 0.40, 0.40, 0.40],
        da=[1.42, 1.52, 1.65, 1.72, 1.80], capex=[3.00, 2.50, 2.00, 2.10, 2.20],
        g_term=0.025, ronic=0.25,
        assumptions="血液透析灌流单独收费与 HAHD 共识推动肾科渗透、海外 +20%：2027–2031 营收 +8/9/8/6/5%，"
                    "经营利润率 40%；不纳入集采；终值增长 2.5%。"),
}
NWC_RATE = 0.06    # 营运资本占营收增量比例
H2_DA, H2_CAPEX = 0.70, 1.05


def ebit_core(rev, cogs, tax_sur, sell, ga, rd):
    return rev - cogs - tax_sur - sell - ga - rd


def h1_norm_operating():
    e = ebit_core(**H1)
    return e - NORM_ADJ * H1["rev"]


def h2_norm_operating(h2):
    cogs = h2["rev"] * (1 - h2["gm"])
    e = ebit_core(h2["rev"], cogs, h2["tax_sur"], h2["sell"], h2["ga"], h2["rd"])
    return e - NORM_ADJ * h2["rev"]


def build(sc):
    rev26 = H1["rev"] + sc["h2"]["rev"]
    op26 = h1_norm_operating() + h2_norm_operating(sc["h2"])
    nopat26 = op26 * (1 - TAX)
    np26 = nopat26 + NET_INTEREST_2026 * (1 - TAX)
    oe_h2 = h2_norm_operating(sc["h2"]) * (1 - TAX) + H2_DA - H2_CAPEX
    rows, rev_prev = [], rev26
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + sc["growth"][i])
        nopat = rev * sc["margin"][i] * (1 - TAX)
        dnwc = NWC_RATE * (rev - rev_prev)
        oe = nopat + sc["da"][i] - sc["capex"][i] - dnwc
        rows.append(dict(year=y, rev=rev, nopat=nopat, oe=oe,
                         reinv=sc["capex"][i] - sc["da"][i] + dnwc))
        rev_prev = rev
    return dict(rev26=rev26, op26=op26, nopat26=nopat26, np26=np26, oe_h2=oe_h2, rows=rows)


def pv_operating(sc, r, m=None):
    m = m or build(sc)
    pv = m["oe_h2"] / (1 + r) ** T_H2_2026
    for row in m["rows"]:
        pv += row["oe"] / (1 + r) ** T_MID[row["year"]]
    last = m["rows"][-1]
    g = sc["g_term"]
    oe_next = last["nopat"] * (1 + g) * (1 - g / sc["ronic"])
    tv = oe_next / (r - g)
    pv_tv = tv / (1 + r) ** T_MID[last["year"]]
    return pv + pv_tv, pv_tv


def per_share(sc, r=COE, shares=SHARES_TOTAL):
    op, pv_tv = pv_operating(sc, r)
    eq_debt = op + NET_CASH_ADJ + NON_OP - CB_PV
    v_debt = eq_debt / shares
    v_conv = (op + NET_CASH_ADJ + NON_OP) / (shares + CB_CONV_SHARES)
    return dict(v=min(v_debt, v_conv), v_debt=v_debt, v_conv=v_conv, op=op,
                tv_share=pv_tv / op, eq=eq_debt)


def weighted(r=COE, shares=SHARES_TOTAL, scen=SCENARIOS):
    return sum(sc["p"] * per_share(sc, r, shares)["v"] for sc in scen.values())


def solve(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(sc):
    def f(r):
        return per_share(sc, r)["v"] - PRICE
    return solve(f, 0.03, 0.20)


def reverse_dcf():
    """现价隐含增长：以基准 2027 正常化所有者收益（经营税后利润 × 90%）为起点，
    (a) 10 年复合增速、其后 2.5% 永续；(b) 永续增速。"""
    base = SCENARIOS["base"]
    mb = build(base)
    ev_implied = PRICE * SHARES_TOTAL - (NET_CASH_ADJ + NON_OP - CB_PV)
    pv_h2 = mb["oe_h2"] / (1 + COE) ** T_H2_2026
    oe27 = mb["rows"][0]["nopat"] * 0.90
    t0 = T_MID[2027]

    def pv10(g):
        pv, oe = pv_h2, oe27
        for k in range(10):
            pv += oe / (1 + COE) ** (t0 + k)
            if k < 9:
                oe *= 1 + g
        gt = 0.025
        tv = oe * (1 + gt) / (COE - gt)
        return pv + tv / (1 + COE) ** (t0 + 9)

    def pv_perp(g):
        return pv_h2 + oe27 / (COE - g) * (1 + COE) ** (1 - t0)

    g10 = solve(lambda g: pv10(g) - ev_implied, -0.05, 0.20)
    gp = solve(lambda g: pv_perp(g) - ev_implied, -0.05, 0.085)
    return ev_implied, oe27, g10, gp


def variant(base_key, **over):
    sc = dict(SCENARIOS[base_key])
    sc.update(over)
    return sc


# 证伪条件触发后的独立 V（单一情景口径）
FALSIFIERS = {
    "F1 三季报：Q3 营收 <3.8 亿或 Q3 扣非 <0.9 亿": variant(
        "base", h2=dict(rev=7.90, gm=0.76, tax_sur=0.16, sell=1.75, ga=0.68, rd=1.05),
        growth=[-0.02, 0.02, 0.02, 0.02, 0.02], margin=[0.36] * 5, g_term=0.015, ronic=0.15),
    "F2 灌流器纳入带量采购或价格治理降价 ≥30%": SCENARIOS["bear"],
    "F3 2026 年报：销售费用率 ≥22% 且营收 <19 亿": variant(
        "base", margin=[0.34] * 5, growth=[0.0, 0.02, 0.02, 0.02, 0.02], g_term=0.015, ronic=0.15),
    "F4 上行：2027H1 营收同比 ≥+10% 且经营利润率 ≥42%": SCENARIOS["bull"],
}


def main():
    print("== 健帆生物 300529 独立估值（价格日 2026-10-20，现价 %.2f）==" % PRICE)
    print("经调整净现金（不含可转债）%.2f 亿；非经营资产 %.2f 亿；可转债债务法扣除 %.2f 亿（面值 %.4f × 110%%，%.2f 年后支付，%.1f%% 折现）"
          % (NET_CASH_ADJ, NON_OP, CB_PV, CB_FACE, T_CB, CB_DEBT_RATE * 100))
    print("全部转股法新增股数 %.4f 亿股（转股价 %.2f）；每股价值低于 %.2f 元时债务法较低"
          % (CB_CONV_SHARES, CB_CONV_PRICE, CB_PV / CB_CONV_SHARES))
    print("扣除可转债后每股净现金（含非经营资产）%.2f 元" % ((NET_CASH_ADJ + NON_OP - CB_PV) / SHARES_TOTAL))
    print()
    res = {}
    for k, sc in SCENARIOS.items():
        m = build(sc)
        ps = per_share(sc)
        res[k] = ps
        print("[%s] p=%.2f  2026营收 %.2f  正常化经营税前 %.2f  NOPAT %.2f  正常化归母净利 %.2f  H2-2026 所有者收益 %.2f"
              % (k, sc["p"], m["rev26"], m["op26"], m["nopat26"], m["np26"], m["oe_h2"]))
        for row in m["rows"]:
            print("   %d 营收 %6.2f  NOPAT %5.2f  净再投资 %5.2f  所有者收益 %5.2f"
                  % (row["year"], row["rev"], row["nopat"], row["reinv"], row["oe"]))
        print("   经营价值 %.2f 亿（终值占 %.0f%%）  股权（债务法）%.2f 亿" % (ps["op"], ps["tv_share"] * 100, ps["eq"]))
        print("   V_债务法 %.2f  V_全部转股 %.2f  → 取低 V = %.2f 元/股；剔除回购专户股本 V = %.2f"
              % (ps["v_debt"], ps["v_conv"], ps["v"], per_share(sc, shares=SHARES_EX_TREASURY)["v"]))
        print("   8%% 下 V %.2f；10%% 下 V %.2f；隐含回报 %.2f%%"
              % (per_share(sc, 0.08)["v"], per_share(sc, 0.10)["v"], implied_irr(sc) * 100))
    vw = weighted()
    vw_ex = weighted(shares=SHARES_EX_TREASURY)
    print()
    print("加权 V = %.2f 元/股；P/V = %.2f" % (vw, PRICE / vw))
    print("剔除回购专户股本：加权 V = %.2f；P/V = %.2f" % (vw_ex, PRICE / vw_ex))
    print("股权成本 8%%：加权 V = %.2f；10%%：加权 V = %.2f" % (weighted(0.08), weighted(0.10)))
    print("基准情景隐含回报（现价）= %.2f%%" % (implied_irr(SCENARIOS["base"]) * 100))
    ev, oe27, g10, gp = reverse_dcf()
    print("反向 DCF：现价隐含经营价值 %.2f 亿；以 2027 正常化所有者收益 %.2f 亿为起点，10 年复合 %.2f%%（其后 2.5%%），或永续增速 %.2f%%"
          % (ev, oe27, g10 * 100, gp * 100))
    print("分档价格（V 不变）：≤%.2f 明显低估；%.2f–%.2f 温和低估；%.2f–%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    b = build(SCENARIOS["base"])
    reinv = sum(r_["reinv"] for r_ in b["rows"])
    nop = sum(r_["nopat"] for r_ in b["rows"])
    d_nopat = b["rows"][-1]["nopat"] - b["nopat26"]
    print("基准再投资率 %.1f%%（2027–2031 净再投资 %.2f / NOPAT %.2f）；增量回报 %.0f%%（NOPAT 增量 %.2f / 净再投资）"
          % (reinv / nop * 100, reinv, nop, d_nopat / reinv * 100, d_nopat))
    g_path = [b["rows"][0]["nopat"] / b["nopat26"] - 1] + [
        b["rows"][i]["nopat"] / b["rows"][i - 1]["nopat"] - 1 for i in range(1, 5)]
    print("基准经营税后利润增长 2027–2031：" + "、".join("%.1f%%" % (g * 100) for g in g_path))
    print()
    # 假设：2026-11-27 后下修转股价至约现价 15.30 元并全部转股（回购专户 0.2424 亿股先用，其余新增）
    op_b = per_share(SCENARIOS["base"])["op"]
    new_sh = CB_FACE / 15.30 - TREASURY
    print("下修假设（转股价 15.30、全部转股、新增 %.4f 亿股）：基准 V = %.2f（对照债务法 %.2f）"
          % (new_sh, (op_b + NET_CASH_ADJ + NON_OP) / (SHARES_TOTAL + new_sh),
             per_share(SCENARIOS["base"])["v"]))
    print()
    print("证伪触发后的独立 V：")
    for k, sc in FALSIFIERS.items():
        print("   %s → V = %.2f" % (k, per_share(sc)["v"]))
    # F5：资本配置——新增非主业或关联方收购/投资 ≥3 亿元，按价值损失一半从加权 V 中扣除
    print("   F5 新增非主业或关联方收购/投资 ≥3 亿元 → V = %.2f" % (vw - 0.5 * 3.0 / SHARES_TOTAL))
    dps26 = b["np26"] * 0.75 / SHARES_EX_TREASURY
    ddm = [dps26 * (1 + g) / (COE - g) for g in (0.03, 0.035)]
    print()
    print("交叉验证：TTM 股息率 %.2f%%；2026E 每股股利（75%% 派息）%.2f 元，股息率 %.2f%%；"
          "股利折现（g 3%%～3.5%%，不另加现金）%.2f～%.2f 元" % (0.52 / PRICE * 100, dps26, dps26 / PRICE * 100,
                                                         ddm[0], ddm[1]))
    TTM_OPERATING_EBIT = 6.36   # TTM 核心经营利润 7.07 + 其他收益 0.24 − 减值 0.78 − 营业外净支出 0.16
    print("EV（市值 − 净现金 − 非经营资产 + 可转债现值）%.2f 亿；EV/正常化经营利润 2026E %.1f 倍；EV/TTM 经营利润 %.1f 倍"
          % (ev, ev / b["op26"], ev / TTM_OPERATING_EBIT))
    PARENT_EQUITY = 34.59
    print("加权 V 对应 2026E 正常化 PE %.1f 倍、PB %.1f 倍" % (vw * SHARES_TOTAL / b["np26"], vw * SHARES_TOTAL / PARENT_EQUITY))
    # 三季度估计（基准）：营收 4.10、毛利率 77%、税金 0.08、销售 0.82、管理 0.33、研发 0.50、
    # 其他收益 0.05、减值与营业外 −0.06、净财务收益 +0.025、所得税 15%
    q3_pre = 4.10 * 0.77 - 0.08 - 0.82 - 0.33 - 0.50 + 0.05 - 0.06 + 0.025
    print("2026Q3 估计（基准）：营收 4.10 亿（2025Q3 4.22），归母净利 %.2f 亿（2025Q3 0.64）" % (q3_pre * 0.85))


if __name__ == "__main__":
    main()
