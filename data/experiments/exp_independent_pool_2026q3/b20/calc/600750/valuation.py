"""华润江中（600750）独立估值：归母所有者收益 DCF（无杠杆口径，经调整净现金为正）。

单位：金额亿元，价格与 V 元/股。价格日 2026-10-21，最新定期报告 2026 中报（三季报 2026-10-24 预约）。
运行：python3 valuation.py
"""

PRICE = 23.13
SHARES = 6.3559          # 亿股，腾讯行情总股本（含 678.8 万股未解锁限制性股票；无回购专户股份）
COE = 0.09
T0 = 71 / 365            # 2026-10-21 至 2026-12-31 的年数
P_BAND = [(0.75, "明显低估"), (0.90, "温和低估"), (1.10, "大致合理")]

# ---------- 1. 经调整净现金（2026-06-30 合并报表，2026H1_report 第 35、76、87、99、103、105、132 页） ----------
CASH_ITEMS = {
    "货币资金": 6.4010,
    "交易性金融资产（银行理财）": 2.4727,
    "一年内到期的定期存款": 10.0580,
    "一年以上到期的定期存款（其他非流动资产）": 10.8941,
}
DEDUCTIONS = {
    "受限货币资金（应付票据质押）": 0.5100,
    "2026 中期股利（2026-09-11 已派，0.5 元/股）": 3.1779,
    "经营备付（约 5% 营收）": 2.0000,
    "控股股东委托贷款（含应计利息，2027-12-23 到期）": 0.5087,
    "长期应付款（应付桑海科技股利及减资款）": 1.5679,
}
LEASE_LIAB = 0.0263               # 只列示不扣：所有者收益以净利润为起点，已扣使用权资产折旧与租赁利息
RELATED_DEPOSIT = 3.2507          # 存放广东华润银行，含在上列存款中，单独列示
MINORITY_SHARE_SUB_CASH = 1.0     # 少数股东应占非全资子公司净金融资产（估计，区间 0～2）
NON_OP = 0.73 * 0.7 + 0.0577 + 0.16 + 0.3406   # 青海银行 1.64%（七折）+产业创新中心+华润成都基金+联营企业

NET_CASH_CONS = sum(CASH_ITEMS.values()) - sum(DEDUCTIONS.values())
NET_CASH_PARENT = NET_CASH_CONS - MINORITY_SHARE_SUB_CASH

# ---------- 2. 2026 正常化归母净利与经营口径 ----------
H1_DEDUCT_NP = 4.6961             # 2026 中报扣非归母净利
H1_INV_REVERSAL_AT = 0.07         # 存货跌价转回 0.132 亿的归母税后影响（剔除）
H1_NORM = H1_DEDUCT_NP - H1_INV_REVERSAL_AT
H1_NET_INT_AT = (0.28871 - 0.00726) * 0.85          # 上半年税后净利息
H2_NET_INT_AT = (0.26 - 0.008) * 0.85               # 下半年税后净利息（估计）
NET_INT_AT_2026 = H1_NET_INT_AT + H2_NET_INT_AT
NP_OP_H1 = H1_NORM - H1_NET_INT_AT                  # 上半年经营口径（不含利息）归母净利
R_2026H2 = 0.15                                     # 下半年再投资率（金匠产业园等资本开支高于折旧）

SCEN = {
    "bear": dict(p=0.30, np26=7.70, g=[-0.10, -0.06, -0.03, -0.02, -0.01], r=[0.05] * 5, gT=0.0, roiic=None,
                 note="集采价格外溢压低健胃消食片价格与销量，OTC 继续下滑，费用无再压空间"),
    "base": dict(p=0.50, np26=8.00, g=[-0.03, -0.01, 0.01, 0.02, 0.02], r=[0.12] * 5, gT=0.02, roiic=0.15,
                 note="2027 年受集采外溢与处方药下滑再降，2028 企稳，此后新品与提价带来低增长"),
    "bull": dict(p=0.20, np26=8.30, g=[0.01, 0.04, 0.05, 0.04, 0.04], r=[0.20] * 5, gT=0.025, roiic=0.20,
                 note="OTC 2027 企稳，贝飞达扩产、经典名方与特医放量，并购回报约 20%"),
}


def scenario_flows(s, years=5):
    """返回 [(t, 所有者收益)]、终值所在年份末的经营归母净利、终值再投资率。"""
    npop = s["np26"] - NET_INT_AT_2026
    flows = [(0.0, (npop - NP_OP_H1) * (1 - R_2026H2))]
    for k in range(1, years + 1):
        g, r = s["g"][k - 1], s["r"][k - 1]
        npop *= 1 + g
        flows.append((T0 + k - 0.5, npop * (1 - r)))
    if "rT" in s:
        rT = s["rT"]
    else:
        rT = s["gT"] / s["roiic"] if s["roiic"] else 0.0
    return flows, npop, rT, T0 + years


def value(s, coe=COE, detail=False):
    flows, np_last, rT, t_tv = scenario_flows(s, len(s["g"]))
    pv_ops = sum(cf / (1 + coe) ** t for t, cf in flows)
    tv = np_last * (1 + s["gT"]) * (1 - rT) / (coe - s["gT"])
    pv_tv = tv / (1 + coe) ** t_tv
    equity = pv_ops + pv_tv + NET_CASH_PARENT + NON_OP
    v = equity / SHARES
    if detail:
        return v, dict(pv_explicit=pv_ops, pv_tv=pv_tv, tv_share=pv_tv / (pv_ops + pv_tv), equity=equity, flows=flows, tv=tv)
    return v


def weighted(coe=COE, scen=SCEN):
    return sum(s["p"] * value(s, coe) for s in scen.values())


def solve(f, lo, hi, target, n=200):
    """二分法：f 单调，求 f(x)=target。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    return solve(lambda r: value(SCEN["base"], r), 0.04, 0.15, PRICE)


R_BASE = 0.12   # 反向 DCF 固定再投资率（基准），直接对所有者收益求增速


def constant_growth_scenario(g, years, gT):
    """所有者收益按固定再投资率 R_BASE 换算，经营口径归母净利 2027 起按 g 增长 years 年，之后按 gT 永续。"""
    return dict(np26=SCEN["base"]["np26"], g=[g] * years, r=[R_BASE] * years, gT=gT, roiic=None, rT=R_BASE)


def implied_perpetual_growth():
    return solve(lambda g: value(constant_growth_scenario(g, 5, g)), -0.05, 0.06, PRICE)


def implied_10y_cagr():
    return solve(lambda g: value(constant_growth_scenario(g, 10, 0.025)), -0.10, 0.20, PRICE)


def falsifier_values():
    vb, vbase, vbull = (value(SCEN[k]) for k in ("bear", "base", "bull"))
    cost_up = dict(SCEN["base"], g=[-0.08, -0.01, 0.01, 0.02, 0.02])
    return {
        "F1 2026 年报扣非归母 < 7.8 亿": 0.6 * vb + 0.4 * vbase,
        "F2 2027 中报 OTC 收入同比 ≤ -8% 或 OTC 毛利率 < 74%": vb,
        "F3 2027 中报销售费用率 > 32% 且营收同比为负": value(cost_up),
        "F4 2027 中报营收同比 ≥ +3% 且扣非归母同比 ≥ +5%（上行）": vbull,
        "F5 单笔并购对价 ≥ 10 亿且标的市盈率 ≥ 20 倍": weighted() - 2.9 / SHARES,
    }


def cross_checks():
    mcap = PRICE * SHARES
    np_ttm, np_norm = 8.76, SCEN["base"]["np26"]
    ebit_2026 = 5.533 + 4.15 + 0.18 - 0.13           # 合并口径，不含利息，含经常性补助
    ev = mcap + 7.32 - NET_CASH_CONS - NON_OP          # 少数股东权益按账面
    return {
        "市值": mcap,
        "PE(TTM)": mcap / np_ttm,
        "PE(2026 正常化)": mcap / np_norm,
        "剔现金 PE（经营口径）": (mcap - NET_CASH_PARENT - NON_OP) / (np_norm - NET_INT_AT_2026),
        "EV/EBIT(2026E)": ev / ebit_2026,
        "股息率(TTM 1.38 元)": 1.38 / PRICE,
        "可持续每股派现（OE+税后利息）": (value(SCEN["base"], detail=True)[1]["flows"][1][1] + 0.40) / SHARES,
        "历史 PE 中位数 18.05 倍对应每股": 18.05 * np_norm / SHARES,
        "同业 PE(TTM) 中值 17.42 倍对应每股": 17.42 * np_norm / SHARES,
    }


def band(pv):
    for cut, name in P_BAND:
        if pv <= cut:
            return name
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print("== 经调整净现金 ==")
    print("现金与存款合计 %.2f；扣除 %.2f；合并口径 %.2f；扣少数股东应占子公司净金融资产 %.1f 后归母 %.2f；非经营资产 %.2f"
          % (sum(CASH_ITEMS.values()), sum(DEDUCTIONS.values()), NET_CASH_CONS, MINORITY_SHARE_SUB_CASH, NET_CASH_PARENT, NON_OP))
    print("列示不扣：租赁负债 %.3f；关联方（广东华润银行）存款 %.2f" % (LEASE_LIAB, RELATED_DEPOSIT))
    print("H1 正常化归母 %.2f；2026 税后净利息 %.2f；H1 经营口径 %.2f" % (H1_NORM, NET_INT_AT_2026, NP_OP_H1))
    print()
    print("== 三情景（股权成本 9%） ==")
    for k, s in SCEN.items():
        v, d = value(s, detail=True)
        npop = s["np26"] - NET_INT_AT_2026
        path = []
        for g in s["g"]:
            npop *= 1 + g
            path.append(round(npop, 2))
        print("%-4s p=%.2f V=%.2f  P/V=%.2f  正常化2026归母 %.2f  经营口径路径2027-31 %s  g_T=%.1f%%  终值占比 %.0f%%  V@8%%=%.2f V@10%%=%.2f"
              % (k, s["p"], v, PRICE / v, s["np26"], path, s["gT"] * 100, d["tv_share"] * 100,
                 value(s, 0.08), value(s, 0.10)))
    vw = weighted()
    print()
    print("加权 V = %.2f；P/V = %.2f（%s）" % (vw, PRICE / vw, band(PRICE / vw)))
    print("加权 V@8%% = %.2f（P/V %.2f）；加权 V@10%% = %.2f（P/V %.2f）"
          % (weighted(0.08), PRICE / weighted(0.08), weighted(0.10), PRICE / weighted(0.10)))
    print("基准情景隐含回报（现价=基准 V 的折现率）= %.2f%%" % (implied_irr() * 100))
    print("反向 DCF：隐含永续增速 %.2f%%；隐含 10 年所有者收益 CAGR（终值 2.5%%）%.2f%%"
          % (implied_perpetual_growth() * 100, implied_10y_cagr() * 100))
    base_flows = value(SCEN["base"], detail=True)[1]["flows"]
    oe = [cf for _, cf in base_flows[1:]]
    print("基准所有者收益 2027-31：%s；同比 %s" % ([round(x, 2) for x in oe],
          [round(oe[i] / oe[i - 1] - 1, 4) if i else None for i in range(len(oe))]))
    oe26 = (SCEN["base"]["np26"] - NET_INT_AT_2026) * (1 - R_BASE)
    print("基准 2026 全年所有者收益（经营口径×(1-12%%)）%.2f；2027 同比 %.4f" % (oe26, oe[0] / oe26 - 1))
    print()
    print("== 证伪触发后的 V ==")
    for k, v in falsifier_values().items():
        print("%s：V=%.2f（P/V %.2f）" % (k, v, PRICE / v))
    print()
    print("== V 不变时各档价格 ==")
    print("≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    print("== 交叉验证 ==")
    for k, v in cross_checks().items():
        print("%s：%.3f" % (k, v))
    alt = (weighted() * SHARES - 0.9300) / (SHARES - 0.06788)
    print("对照：剔除未解锁限制性股票 678.8 万股并扣回购义务 0.93 亿后加权 V = %.2f（P/V %.2f）" % (alt, PRICE / alt))
