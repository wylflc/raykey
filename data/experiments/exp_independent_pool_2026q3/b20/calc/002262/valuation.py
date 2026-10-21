#!/usr/bin/env python3
"""恩华药业（002262）独立估值：所有者收益 DCF + 净现金 + 非经营资产，三情景概率加权。

运行：python3 valuation.py
金额单位亿元，每股价值单位元/股。输入全部写在本脚本内，出处见同批 companies/002262_恩华药业.md。
"""

# ---------------------------------------------------------------- 快照
PRICE = 21.90                 # 2026-10-21 收盘，腾讯日线
SHARES = 10.12971423          # 亿股；2026-08-26 回购注销 281.5160 万股限制性股票后（公告 2026-034）
COE = 0.09                    # 股权成本基准
DAYS_ROLL = 113               # 2026-06-30 → 2026-10-21，估值基准日滚动天数

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report）
CASH = 12.2200                # 货币资金（第 86 页）
STRUCT_DEPOSIT = 25.2200      # 交易性金融资产，全部为结构性存款（第 86 页）
RESTRICTED = 0.9214           # 受限保证金（第 25 页）
SHORT_LOAN = 0.4000           # 短期借款
LONG_LOAN = 0.0023            # 长期借款（第 108 页）
LEASE = 0.3181                # 租赁负债（含一年内到期 0.1676）；利润已扣使用权折旧与利息，只列示不扣
RS_BUYBACK_PAID = 0.3026      # 8 月回购注销限制性股票付款 3,026.2970 万元（公告 2026-034）
OPER_RESERVE = 3.0            # 经营备付：约 TTM 营收 61.19 亿的 5%

NET_CASH_ADJ = (CASH + STRUCT_DEPOSIT - RESTRICTED - OPER_RESERVE
                - SHORT_LOAN - LONG_LOAN - RS_BUYBACK_PAID)

# ---------------------------------------------------------------- 非经营资产
# 好欣晴（Good Mood Holdings）：恩华持 2,550 万股；2026-09 增资 2.62 亿元认购 777.4744 万股
GM_SHARES_WAN = 2550.0
GM_ROUND_PRICE = 26200.0 / 777.4744          # 元/股，约 33.70
GM_ROUND_VALUE = GM_SHARES_WAN * GM_ROUND_PRICE / 1e4   # 亿元，约 8.59
GM_BOOK = 1.2772                              # 2026-06-30 权益法账面（第 95 页）
GM_TAX = 0.25                                 # 处置增值所得税


def good_mood(fraction_of_round):
    if fraction_of_round is None:
        return GM_BOOK
    v = GM_ROUND_VALUE * fraction_of_round
    return v - GM_TAX * max(v - GM_BOOK, 0.0)


# Somnivera 许可：首付款 1,050 万美元 + 15% 股权 + 里程碑/特许权使用费风险调整现值（百万美元）
USDCNY = 7.10
SOMN_AFTER_TAX = 0.85


def somnivera(upfront_musd, equity_musd, rnpv_musd):
    return (upfront_musd + equity_musd + rnpv_musd) * USDCNY / 100.0 * SOMN_AFTER_TAX


OTHER_EQUITY_INV = 0.5116     # 其他权益工具投资（三晟医药等），账面
OTHER_ASSOC = 0.1380 + 0.0782 # 中健永泰（合营）+ 南京医药徐州恩华（24%），账面

# ---------------------------------------------------------------- 经营利润口径
# 2026H1 归母 7.4068；剔除税后金融收益（结构性存款 0.2515 + 利息收入 0.0339 - 利息支出 0.0106，税率 15%）
# 与联营/合营投资收益 0.1077
H1_PARENT_NP = 7.4068
H1_FIN_AFTER_TAX = (0.2515 + 0.0339 - 0.0106) * 0.85
H1_ASSOC = 0.1077
H1_OP_NP = H1_PARENT_NP - H1_FIN_AFTER_TAX - H1_ASSOC

SCENARIOS = {
    # 2026 正常化归母（报表口径，含净利息，剔除 Somnivera 首付款等一次性）；fin_assoc 为全年税后金融收益+联营收益
    "bear": dict(p=0.25, np2026=11.10, fin_assoc=0.68,
                 growth=[-0.04, 0.00, 0.02, 0.03, 0.03], g_term=0.020, roiic=0.12, ronic=0.11,
                 gm=None, somn=(10.5, 3.0, 0.0)),
    "base": dict(p=0.50, np2026=11.80, fin_assoc=0.68,
                 growth=[0.07, 0.065, 0.06, 0.055, 0.05], g_term=0.025, roiic=0.18, ronic=0.15,
                 gm=0.50, somn=(10.5, 7.0, 25.0)),
    "bull": dict(p=0.25, np2026=12.50, fin_assoc=0.68,
                 growth=[0.11, 0.11, 0.10, 0.09, 0.08], g_term=0.025, roiic=0.25, ronic=0.18,
                 gm=0.80, somn=(10.5, 15.0, 60.0)),
}
FADE_YEARS = 5               # 2032-2036 线性收敛到终值增速
RR_FLOOR = 0.20              # 显性期再投资率下限：资本化研发约 1.6 亿 + 净资本开支约 0.6 亿，对冲集采的防守性投入


def operating_value(s, r, uniform_g=None):
    """返回 2026-06-30 时点经营价值（亿元）与逐年路径。"""
    op2026 = s["np2026"] - s["fin_assoc"]
    growth = list(s["growth"]) if uniform_g is None else [uniform_g] * 5
    g_term = s["g_term"]
    rr_exp = max((sum(growth) / len(growth)) / s["roiic"], RR_FLOOR)   # 显性期再投资率（常数）
    rr_term = g_term / s["ronic"]
    g_last = growth[-1] if uniform_g is None else uniform_g
    fade = [g_last + (g_term - g_last) * k / FADE_YEARS for k in range(1, FADE_YEARS + 1)]
    if uniform_g is not None:
        fade = [uniform_g] * FADE_YEARS
    path = []
    # 2026 下半年
    op_h2 = op2026 - H1_OP_NP
    rr_2026 = max(rr_exp, 0.0)
    pv = op_h2 * (1 - rr_2026) / (1 + r) ** 0.25
    path.append(("2026H2", None, op_h2, op_h2 * (1 - rr_2026)))
    npv = op2026
    t = 0.0
    all_g = growth + fade
    for i, g in enumerate(all_g):
        t += 1.0
        npv *= 1 + g
        if i < len(growth):
            rr = rr_exp
        else:
            k = i - len(growth) + 1
            rr = rr_exp + (rr_term - rr_exp) * k / FADE_YEARS
        rr = max(rr, 0.0)
        oe = npv * (1 - rr)
        pv += oe / (1 + r) ** t
        path.append((2026 + i + 1, g, npv, oe))
    np_next = npv * (1 + g_term)
    oe_next = np_next * (1 - rr_term)
    tv = oe_next / (r - g_term)
    pv_tv = tv / (1 + r) ** t
    return pv, pv_tv, path, rr_exp, rr_term


def non_operating(s):
    gm = good_mood(s["gm"])
    sv = somnivera(*s["somn"])
    return gm + sv + OTHER_EQUITY_INV + OTHER_ASSOC, gm, sv


def per_share(s, r, uniform_g=None):
    pv, pv_tv, path, rr_exp, rr_term = operating_value(s, r, uniform_g)
    nonop, gm, sv = non_operating(s)
    equity_0630 = pv + pv_tv + NET_CASH_ADJ + nonop
    equity_1021 = equity_0630 * (1 + r) ** (DAYS_ROLL / 365.0)
    return dict(v=equity_1021 / SHARES, ev_op=pv + pv_tv, pv=pv, pv_tv=pv_tv, path=path,
                rr_exp=rr_exp, rr_term=rr_term, nonop=nonop, gm=gm, sv=sv,
                tv_share=pv_tv / (pv + pv_tv))


def weighted(r):
    return sum(s["p"] * per_share(s, r)["v"] for s in SCENARIOS.values())


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    print("恩华药业 002262 独立估值（价格日 2026-10-21，现价 %.2f 元，股本 %.4f 亿股）" % (PRICE, SHARES))
    print("经调整净现金 %.2f 亿元 = 货币资金 %.2f + 结构性存款 %.2f - 受限 %.2f - 经营备付 %.2f - 借款 %.2f - 8 月回购付款 %.2f"
          % (NET_CASH_ADJ, CASH, STRUCT_DEPOSIT, RESTRICTED, OPER_RESERVE, SHORT_LOAN + LONG_LOAN, RS_BUYBACK_PAID))
    print("租赁负债 %.2f 亿元只列示不扣；好欣晴按增资价全额价值 %.2f 亿元（每股 %.2f 元），账面 %.2f"
          % (LEASE, GM_ROUND_VALUE, GM_ROUND_PRICE, GM_BOOK))
    print("2026H1 经营口径归母（剔除税后金融收益与联营收益）%.2f 亿元" % H1_OP_NP)
    print()
    res = {}
    for name, s in SCENARIOS.items():
        x = per_share(s, COE)
        res[name] = x
        print("[%s] p=%.2f  2026 正常化归母 %.2f，经营口径 %.2f；显性期再投资率 %.1f%%，终值再投资率 %.1f%%"
              % (name, s["p"], s["np2026"], s["np2026"] - s["fin_assoc"], x["rr_exp"] * 100, x["rr_term"] * 100))
        print("    经营价值 %.1f 亿（显性+收敛期 %.1f，终值 %.1f，终值占比 %.0f%%）；非经营 %.2f 亿（好欣晴 %.2f，Somnivera %.2f）"
              % (x["ev_op"], x["pv"], x["pv_tv"], x["tv_share"] * 100, x["nonop"], x["gm"], x["sv"]))
        line = "    路径："
        for (yr, g, npv, oe) in x["path"][:6]:
            line += " %s %s 归母%.2f/OE%.2f;" % (yr, "" if g is None else "%+.1f%%" % (g * 100), npv, oe)
        print(line)
        print("    V = %.2f 元/股" % x["v"])
    vw = weighted(COE)
    pv_ratio = PRICE / vw
    print()
    print("加权 V = %.2f 元/股；P/V = %.2f" % (vw, pv_ratio))
    for r in (0.08, 0.10):
        print("股权成本 %.0f%%：加权 V = %.2f；基准 V = %.2f" % (r * 100, weighted(r), per_share(SCENARIOS["base"], r)["v"]))
    irr = solve(lambda r: per_share(SCENARIOS["base"], r)["v"], 0.03, 0.30, PRICE)
    print("现价隐含回报（基准情景现金流）= %.2f%%" % (irr * 100))
    g10 = solve(lambda g: per_share(SCENARIOS["base"], COE, uniform_g=g)["v"], -0.10, 0.30, PRICE)
    print("反向 DCF：基准再投资回报下，现价隐含 2027-2036 年经营归母年增速 %.2f%%（其后 2.5%%）" % (g10 * 100))
    # 永续增速：单阶段 Gordon，OE = 经营归母 × (1 - g/RONIC)
    s = SCENARIOS["base"]
    op2026 = s["np2026"] - s["fin_assoc"]
    nonop = non_operating(s)[0]
    target_ev = PRICE * SHARES / (1 + COE) ** (DAYS_ROLL / 365.0) - NET_CASH_ADJ - nonop
    gp = solve(lambda g: op2026 * (1 + g) * (1 - g / s["ronic"]) / (COE - g), -0.10, 0.085, target_ev)
    print("反向 DCF：单阶段永续增速 %.2f%%（再投资回报 %.0f%%）" % (gp * 100, s["ronic"] * 100))
    for lo, hi, tag in ((0, 0.75, "明显低估"), (0.75, 0.90, "温和低估"), (0.90, 1.10, "大致合理")):
        print("V 不变时进入「%s」的价格区间：%.2f ～ %.2f 元" % (tag, vw * lo, vw * hi))
    print("价格高于 %.2f 元为「偏贵」" % (vw * 1.10))
    # 证伪情景
    print()
    print("证伪触发后的 V：")
    print("  熊市情景 V = %.2f" % res["bear"]["v"])
    trig = dict(SCENARIOS["base"])
    trig.update(growth=[0.03, 0.03, 0.03, 0.03, 0.03], np2026=11.10)
    print("  2026 归母 ≤ 11.1 且其后增速 3%%：V = %.2f" % per_share(trig, COE)["v"])
    trig2 = dict(SCENARIOS["base"])
    trig2.update(growth=[0.0, 0.02, 0.04, 0.05, 0.05])
    print("  NH600001 2027 年底前未获批、2027 年经营归母不增长：V = %.2f" % per_share(trig2, COE)["v"])
    trig3 = dict(SCENARIOS["base"])
    trig3.update(roiic=0.12, ronic=0.12)
    print("  再投资回报降至 12%%（应收与开发支出继续膨胀）：V = %.2f" % per_share(trig3, COE)["v"])
    trig4 = dict(SCENARIOS["base"])
    trig4.update(growth=[-0.08, 0.0, 0.03, 0.04, 0.04], np2026=11.10)
    print("  依托咪酯/咪达唑仑进入全国或大范围联盟集采：V = %.2f" % per_share(trig4, COE)["v"])


if __name__ == "__main__":
    main()
