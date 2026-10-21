"""安琪酵母（600298）独立估值（OI-291 b12，价格日 2026-10-20）。

运行：python3 valuation.py
口径：金额亿元，每股元。所有输入写在本脚本内，出处见正文「来源」。
主口径为有杠杆口径（经调整净现金为负）：
  股权价值 = 归母经营所有者收益现值(9%) − 经调整净负债税后利息现值(按现规模永续滚动) + 非经营资产
另报无杠杆口径：股权价值 = 归母经营所有者收益现值 − 经调整净负债（全额扣除） + 非经营资产
可转债（2026-09-25 预案，35 亿元，未发行）不进主口径，单列发行后对照。
"""

# ---------------------------------------------------------------- 市场与股本
PRICE = 36.86                 # 2026-10-20 收盘（brief）
SHARES = 8.6782               # 亿股，腾讯行情总股本（含限制性股票；无回购专户股份）
MCAP = PRICE * SHARES

# ---------------------------------------------------------------- 2026-06-30 资产负债（2026H1_report 第 43-45、83、97-100、118-126 页）
CASH = 23.18                  # 货币资金
TRADING_FA = 0.60             # 交易性金融资产（结构性存款）
DERIV_FA = 0.02               # 衍生金融资产（远期结售汇）
RESTRICTED = 2.04             # 受限货币资金（保证金，第 14 页）
REVENUE_TTM = 180.16
OPER_RESERVE = round(0.02 * REVENUE_TTM, 2)   # 经营备付：TTM 营收 2%
SHORT_LOAN = 35.89            # 含票据贴现融资 17.07
NCL_1Y = 9.96                 # 一年内到期长期借款 9.53 + 租赁 0.25 + 债券利息 0.18
LONG_LOAN = 23.04
BONDS = 19.95                 # 25安琪K1、26安琪K1 科技创新公司债（普通债，非可转债）
LEASE = 1.09
EARNOUT = 1.74                # 其他非流动负债：晟通糖业业绩对赌保证金（递延收购对价）
DIV_PAYABLE = 0.14            # 应付股利（埃及员工分红）
DEBT = SHORT_LOAN + NCL_1Y + LONG_LOAN + BONDS + LEASE
CASH_LIKE = CASH + TRADING_FA + DERIV_FA
NET_CASH_ADJ = CASH_LIKE - RESTRICTED - OPER_RESERVE - DEBT - EARNOUT - DIV_PAYABLE
NET_DEBT_ADJ = -NET_CASH_ADJ
# 非经营资产：长期股权投资 0.67 + 其他权益工具 0.04 + 其他非流动金融资产 0.14 + 投资性房地产 0.38
NON_OP = 0.67 + 0.04 + 0.14 + 0.38
# 融资租赁应收款（长期应收款 7.36 + 一年内到期 5.03）留在经营口径内，其收益已含在正常化利润中

# 有息负债实际平均利率：TTM 费用化利息 / 五个季末有息负债均值（f10 资产负债表）
INT_EXP_TTM = 1.717 - 0.716 + 0.903          # 2025 全年 − 2025H1 + 2026H1
DEBT_POINTS = [74.01, 80.72, 81.53, 85.35, DEBT]   # 2025-06-30 … 2026-06-30
RATE = INT_EXP_TTM / (sum(DEBT_POINTS) / len(DEBT_POINTS))
TAX = 0.16                    # 有效税率（2025 年 15.1%，2026H1 18.5%）
AT_INTEREST = NET_DEBT_ADJ * RATE * (1 - TAX)  # 经调整净负债税后利息（年）

# 实际净利息（用于从归母净利还原经营利润）：2026H1 年化利息 1.81 − 利息收入 0.17
NET_INT_AT = (0.903 * 2 - 0.085 * 2) * (1 - TAX)

# ---------------------------------------------------------------- 正常化 2026 归母净利（含净利息，剔除一次性）
# 推导（正文第 2 节）：2026E 报告归母约 17.5 → 扣非约 15.6；加回汇兑损失税后约 1.06；
# 加回经常性的资产相关补助摊销约 0.69；扣除糖蜜低价的周期性红利约 1.0；糖业亏损向中枢修复约 +0.3
NORM_NP = {"bear": 15.0, "base": 16.7, "bull": 18.2}

# 情景：前 5 年（2027-2031）NOPAT 增速、之后线性收敛到终值增速（至 2036）、增量资本回报
SCEN = {
    "bear": dict(p=0.25, g5=[0.050, 0.050, 0.045, 0.035, 0.030], gT=0.020, roic=0.065),
    "base": dict(p=0.50, g5=[0.080, 0.080, 0.075, 0.060, 0.050], gT=0.025, roic=0.100),
    "bull": dict(p=0.25, g5=[0.120, 0.120, 0.110, 0.090, 0.075], gT=0.025, roic=0.140),
}
YEARS = list(range(2027, 2037))          # 显性期 10 年
T0 = 2026.8                               # 估值日 2026-10-20


def growth_path(s):
    g5, gT = s["g5"], s["gT"]
    path = list(g5)
    last = g5[-1]
    for i in range(1, 6):                 # 2032-2036 线性收敛到 gT
        path.append(last + (gT - last) * i / 5)
    return path                           # 长度 10，对应 YEARS


def scenario_flows(name):
    s = SCEN[name]
    nopat0 = NORM_NP[name] + NET_INT_AT   # 2026 正常化归母经营利润（加回税后净利息）
    gp = growth_path(s)
    nopat = [nopat0]
    for g in gp:
        nopat.append(nopat[-1] * (1 + g))
    # 再投资 = 下一年 NOPAT 增量 / 增量资本回报；所有者收益 = NOPAT − 再投资
    g_next = gp + [s["gT"]]
    oe = [nopat[i] - nopat[i] * g_next[i] / s["roic"] for i in range(len(nopat))]
    return nopat, oe, gp


def op_value(name, k):
    s = SCEN[name]
    nopat, oe, gp = scenario_flows(name)
    pv = 0.5 * oe[0]                      # 2026H2 所有者收益（资产负债表日 6-30 之后），t≈0
    for i, y in enumerate(YEARS, start=1):
        t = (y + 0.5) - T0
        pv += oe[i] / (1 + k) ** t
    oe_next = nopat[-1] * (1 + s["gT"]) * (1 - s["gT"] / s["roic"])
    tv = oe_next / (k - s["gT"])
    t_last = (YEARS[-1] + 0.5) - T0
    pv_tv = tv / (1 + k) ** t_last
    return pv + pv_tv, pv_tv


def equity_value(name, k, levered=True, net_debt=None, extra=0.0):
    nd = NET_DEBT_ADJ if net_debt is None else net_debt
    v_op, _ = op_value(name, k)
    debt_claim = nd * RATE * (1 - TAX) / k if levered else nd
    return v_op - debt_claim + NON_OP + extra


def per_share(name, k=0.09, levered=True, shares=SHARES, **kw):
    return equity_value(name, k, levered, **kw) / shares


def weighted(k=0.09, levered=True, probs=None, **kw):
    probs = probs or {n: SCEN[n]["p"] for n in SCEN}
    return sum(probs[n] * per_share(n, k, levered, **kw) for n in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    # 基准情景所有者收益流（含终值），有杠杆口径，使现值 = 市值的折现率
    return solve(lambda k: equity_value("base", k, True), 0.04, 0.20, MCAP)


def reverse_dcf_growth(roic):
    # 现价隐含：基准正常化起点、给定增量回报下，2027-2036 统一 NOPAT 增速 g，之后 2.5%
    def val(g):
        SCEN["tmp"] = dict(p=0, g5=[g] * 5, gT=0.025, roic=roic)
        NORM_NP["tmp"] = NORM_NP["base"]
        return equity_value("tmp", 0.09, True)

    global growth_path
    orig = growth_path

    def gp_flat(s):
        return list(s["g5"]) * 2 if s is SCEN.get("tmp") else orig(s)

    growth_path = gp_flat
    try:
        if val(0.40) < MCAP:
            g = float("nan")             # 该回报下任何增速都撑不起现价
        else:
            g = solve(val, 0.0, 0.40, MCAP)
    finally:
        growth_path = orig
        SCEN.pop("tmp", None)
        NORM_NP.pop("tmp", None)
    return g


def reverse_perpetual_growth(roic=0.10, k=0.09):
    # 现价隐含永续增速（戈登，再投资按 g/ROIC 扣除，不设 2.5% 上限）
    need = MCAP + NET_DEBT_ADJ * RATE * (1 - TAX) / k - NON_OP
    n0 = NORM_NP["base"] + NET_INT_AT
    return solve(lambda g: n0 * (1 + g) * (1 - g / roic) / (k - g), 0.0, k - 1e-4, need)


def reverse_roic_needed():
    # 维持基准增速路径，现价要求的增量资本回报
    orig = SCEN["base"]["roic"]

    def val(r):
        SCEN["base"]["roic"] = r
        return equity_value("base", 0.09, True)

    try:
        r = solve(val, 0.095, 2.0, MCAP)
    finally:
        SCEN["base"]["roic"] = orig
    return r


def cb_pro_forma(conv_price, k=0.09):
    """35 亿可转债发行后对照（未计入主口径）。
    债务算法：现金 +35、负债 +35（面值全额扣除），资本开支已在所有者收益中扣除 → 每股价值不变；
    转股算法：股本 + 35/转股价，不扣转债，股权价值 +35。逐情景取低。"""
    out = {}
    for n in SCEN:
        e = equity_value(n, k, True)
        v_debt = e / SHARES
        v_conv = (e + 35.0) / (SHARES + 35.0 / conv_price)
        out[n] = (v_debt, v_conv, min(v_debt, v_conv))
    return out


def main():
    print("== 输入 ==")
    print(f"市值 {MCAP:.2f} 亿；现金类 {CASH_LIKE:.2f}；受限 {RESTRICTED:.2f}；经营备付 {OPER_RESERVE:.2f}")
    print(f"有息负债 {DEBT:.2f}；类债务 {EARNOUT + DIV_PAYABLE:.2f}；经调整净现金 {NET_CASH_ADJ:.2f}")
    print(f"有息负债实际平均利率 {RATE:.4f}；经调整净负债税后利息 {AT_INTEREST:.3f}/年；非经营资产 {NON_OP:.2f}")
    print(f"实际税后净利息（还原经营利润用）{NET_INT_AT:.3f}")
    print()
    print("== 情景（股权成本 9%）==")
    for n in SCEN:
        nopat, oe, gp = scenario_flows(n)
        v_op, pv_tv = op_value(n, 0.09)
        vl = per_share(n)
        vu = per_share(n, levered=False)
        rr = gp[0] / SCEN[n]["roic"]
        print(f"{n}: 正常化归母 {NORM_NP[n]:.1f}  NOPAT2026 {nopat[0]:.2f}  "
              f"增速 2027-31 {[round(x, 3) for x in gp[:5]]}  终值 {SCEN[n]['gT']:.3f}  ROIC {SCEN[n]['roic']:.3f}  再投资率(2027) {rr:.2f}")
        print(f"    NOPAT 2027-2031 {[round(x, 2) for x in nopat[1:6]]}  所有者收益 2027-2031 {[round(x, 2) for x in oe[1:6]]}")
        print(f"    经营价值 {v_op:.1f}（终值现值 {pv_tv:.1f}，占 {pv_tv / v_op:.0%}）  "
              f"V 有杠杆 {vl:.2f}  V 无杠杆 {vu:.2f}  概率 {SCEN[n]['p']:.2f}")
    vw = weighted()
    vwu = weighted(levered=False)
    print()
    print(f"加权 V（有杠杆，主口径）{vw:.2f}  P/V {PRICE / vw:.2f}")
    print(f"加权 V（无杠杆）{vwu:.2f}  P/V {PRICE / vwu:.2f}")
    print(f"股权成本 8%：加权 V {weighted(0.08):.2f}（无杠杆 {weighted(0.08, False):.2f}）")
    print(f"股权成本 10%：加权 V {weighted(0.10):.2f}（无杠杆 {weighted(0.10, False):.2f}）")
    print(f"现价隐含回报（基准情景、有杠杆）{implied_irr():.4f}")
    for r in (0.10, 0.14, 0.20):
        print(f"反向 DCF：增量回报 {r:.0%} 时，现价隐含 2027-2036 每年 NOPAT 增速（之后 2.5%）{reverse_dcf_growth(r):.4f}")
    print(f"反向 DCF：增量回报 10% 时现价隐含永续增速 {reverse_perpetual_growth(0.10):.4f}")
    print(f"反向 DCF：维持基准增速路径时，现价要求的增量资本回报 {reverse_roic_needed():.3f}")
    print()
    print("== 交叉验证 ==")
    np_ttm, np_2026e, np_2025 = 16.26, 17.5, 15.44
    equity_parent, minority = 124.49, 8.74
    print(f"PE(TTM) {MCAP / np_ttm:.1f}；PE(2026E 报告口径 {np_2026e}) {MCAP / np_2026e:.1f}；"
          f"PE(2026 正常化基准) {MCAP / NORM_NP['base']:.1f}；PB {MCAP / equity_parent:.2f}")
    print(f"股息率 {0.55 / PRICE:.2%}（近 12 个月每股 0.55 元，无注销式回购）")
    ev = MCAP + (DEBT - CASH_LIKE) + EARNOUT + minority
    ebit = (NORM_NP["base"] + 0.5) / (1 - TAX) + (0.903 * 2 - 0.085 * 2)
    print(f"EV {ev:.1f}；正常化 EBIT {ebit:.1f}；EV/EBIT {ev / ebit:.1f}；税后 EBIT 收益率 {ebit * (1 - TAX) / ev:.2%}")
    v_base = per_share("base")
    print(f"基准 V 对应：PE(正常化) {v_base * SHARES / NORM_NP['base']:.1f}；PB {v_base * SHARES / equity_parent:.2f}")
    # 正常化 TTM：扣非 14.11 + 汇兑损失税后 + 资产相关补助摊销税后
    fx_ttm = 0.419 + 0.856
    norm_ttm = 14.11 + fx_ttm * (1 - TAX) * 0.97 + 0.85 * (1 - TAX) * 0.97
    print(f"TTM 汇兑损失 {fx_ttm:.3f}（税前）；TTM 正常化归母 {norm_ttm:.2f}")
    # 2026E 正常化基准分解
    fx_26 = 0.856 + 0.20 + 0.25
    parts = dict(扣非2026E=15.7, 汇兑加回=fx_26 * (1 - TAX) * 0.97, 资产相关补助摊销=0.85 * (1 - TAX) * 0.97,
                 糖蜜周期红利=-1.0, 糖业向中枢修复=0.3)
    print("2026E 正常化基准分解：" + "，".join(f"{k} {x:+.2f}" for k, x in parts.items())
          + f" → {sum(parts.values()):.2f}")
    print()
    print("== 分档价格（V 不变）==")
    print(f"明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}～{0.90 * vw:.2f}；"
          f"大致合理 {0.90 * vw:.2f}～{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")
    print()
    print("== 可转债发行后对照（35 亿，未计入主口径）==")
    for cp in (37.0, 41.0):
        res = cb_pro_forma(cp)
        w = sum(SCEN[n]["p"] * res[n][2] for n in SCEN)
        wc = sum(SCEN[n]["p"] * res[n][1] for n in SCEN)
        print(f"转股价 {cp:.0f}：新增股 {35 / cp:.3f} 亿股（{35 / cp / SHARES:.1%}）；"
              + "；".join(f"{n} 债务 {res[n][0]:.2f}/转股 {res[n][1]:.2f}" for n in SCEN)
              + f"；逐情景取低加权 {w:.2f}，全部转股加权 {wc:.2f}")
    print()
    print("== 证伪触发后的 V ==")
    # F1 毛利率不改善：情景概率改为 熊 0.5 / 基 0.5 / 牛 0
    print(f"F1 熊 0.5/基 0.5：{weighted(probs={'bear': 0.5, 'base': 0.5, 'bull': 0.0}):.2f}")
    # F2 业绩超预期：熊 0 / 基 0.5 / 牛 0.5
    print(f"F2 基 0.5/牛 0.5：{weighted(probs={'bear': 0.0, 'base': 0.5, 'bull': 0.5}):.2f}")
    # F3 新项目回报落空：所有情景增量回报 −2 个百分点
    saved = {n: SCEN[n]["roic"] for n in SCEN}
    for n in SCEN:
        SCEN[n]["roic"] = saved[n] - 0.02
    f3 = weighted()
    for n in SCEN:
        SCEN[n]["roic"] = saved[n]
    print(f"F3 增量回报各降 2 个百分点：{f3:.2f}")
    # F4 人民币继续升值：正常化归母各降 1.2 亿（出口毛利与汇兑）
    saved_np = dict(NORM_NP)
    for n in SCEN:
        NORM_NP[n] = saved_np[n] - 1.2
    f4 = weighted()
    NORM_NP.update(saved_np)
    print(f"F4 正常化归母各降 1.2 亿：{f4:.2f}")
    print()
    print("== 其他对照 ==")
    print(f"现价隐含回报（基准情景、无杠杆）{solve(lambda k: equity_value('base', k, False), 0.03, 0.20, MCAP):.4f}")
    for d in (-1.0, 1.0):
        NORM_NP.update({n: saved_np[n] + d for n in SCEN})
        print(f"正常化归母各情景 {d:+.0f} 亿：加权 V {weighted():.2f}")
    NORM_NP.update(saved_np)
    for n in SCEN:
        nopat, _, _ = scenario_flows(n)
        print(f"{n} 正常化归母（扣利息后）2027-2031 {[round(x - AT_INTEREST, 2) for x in nopat[1:6]]}")


if __name__ == "__main__":
    main()
