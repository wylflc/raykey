#!/usr/bin/env python3
"""沪电股份（002463）独立估值（OI-291 b13，深度版）。

所有者收益 DCF（归母口径，股权成本 9%，8%/10% 敏感性），有杠杆口径（经调整净现金为负），
三情景概率加权、反向 DCF、现价隐含回报、证伪情景与交叉验证。
输入全部写在脚本内，出处见 companies/002463_沪电股份.md。金额单位亿元，每股价值元/股。
运行：python3 valuation.py
"""

# ---------------------------------------------------------------- 快照
PRICE = 111.01            # 2026-10-20 收盘（brief.md）
SHARES = 19.2436          # 总股本（亿股，腾讯行情口径 = 2026H1 资产负债表股本 1,924,363,537 股；无回购专户）
MCAP = PRICE * SHARES
COE = 0.09
TAX = 0.15                # 高新技术企业税率（有息负债利息抵税用）

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report）
CASH = 45.538             # 货币资金；受限仅 3,000 元 ETC 保证金（第 18 页）
DEP_1Y = 21.116           # 一年内到期的非流动资产 = 一年内到期定期存款 19.627 + 应计利息 1.489（第 94 页）
DEP_LT = 9.800 + 0.352    # 其他非流动资产中定期存款 9.80 + 应计利息 0.352；另 24.06 为购置资产预付款，属经营性（第 108 页）
DEBT = 83.146             # 银行借款含一年内到期 8,314,563,153 元（筹资活动负债变动表，第 123 页）
DEBT_YE2025 = 45.482      # 同表上年年末余额
REV_TTM = 241.41          # TTM 营收（数据包）
OP_RESERVE = 0.04 * REV_TTM   # 经营备付：TTM 营收 4%（约 2 周付现成本）
DECLARED_DIV = 0.0        # 6-30 无已宣派未付股利（2025 年度股利 2026-05-08 已付）
NET_CASH_ADJ = CASH + DEP_1Y + DEP_LT - DEBT - OP_RESERVE - DECLARED_DIV

INT_EXP_H1 = 0.7558       # 2026H1 利息支出（第 121 页 财务费用附注）
INT_INC_H1 = 0.7422       # 2026H1 利息收入
RATE = INT_EXP_H1 * 2 / ((DEBT_YE2025 + DEBT) / 2)   # 有息负债实际平均利率（年化）

# 非经营资产：Meiko、CMK 股票（其他权益工具投资，公允价值 6-30），扣未实现收益递延税；其他非流动金融资产、长期股权投资
MEIKO_CMK_FV = 12.709 + 0.030
MEIKO_CMK_COST = 0.909 + 0.023
GAIN_TAX = 0.165          # 持有主体沪士国际（香港），按递延所得税负债增加额与公允价值变动之比约 16.5%
OTHER_NONOP = 0.850 + 0.257
NON_OP = MEIKO_CMK_FV - (MEIKO_CMK_FV - MEIKO_CMK_COST) * GAIN_TAX + OTHER_NONOP

# ---------------------------------------------------------------- 2026 年报告口径估计（三季度用预告）
NP_H1 = 29.234            # 2026H1 归母
NP_9M_LOW, NP_9M_HIGH = 54.5, 57.0      # 前三季度预告（forecast_20261015_459992）
NP_Q3_MID = (NP_9M_LOW + NP_9M_HIGH) / 2 - NP_H1
NP_Q4_EST = 27.5          # 估计：Q4 与 Q3 大体持平（产能约束、汇率中性）
NP_2026E = (NP_9M_LOW + NP_9M_HIGH) / 2 + NP_Q4_EST
REV_H1 = 136.894
REV_Q3_EST = 95.0         # 估计：Q3 归母约 26.5 亿、净利率约 28%
REV_Q4_EST = 98.0
REV_2026E = REV_H1 + REV_Q3_EST + REV_Q4_EST
FX_LOSS_H1 = 2.756        # 2026H1 汇兑损失 2.76 亿（IR_20260923；Q1 1.48、Q2 约 1.28）
# 三季度人民币即期升值约 1.18%（网络：东方财富 2026-10-01）；上半年即期升值约 2.9% 对应损失 2.76 亿，
# 敏感度约 0.95 亿/1%，估三季度汇兑损失约 1.1 亿（估计值，三季报核对）
FX_LOSS_Q3_EST = 1.1
NONREC_9M = (NP_9M_LOW + NP_9M_HIGH) / 2 - (53.6 + 55.5) / 2   # 前三季度非经常性损益（预告中值差）
NP_2026E_CORE = NP_2026E + (FX_LOSS_H1 + FX_LOSS_Q3_EST) * (1 - TAX) - NONREC_9M

# ---------------------------------------------------------------- 三情景
# n0：2026 年正常化归母净利（含净利息，剔除一次性；2026H1 利息收支相抵，净利息约 0）
# g：2027-2031 年正常化归母净利增速；roic：增量回报；再投资率 RR_t = g_{t+1}/roic（当年再投资支撑次年增长），
#    第 5 年取终值再投资率 gT/roicT；熊市给定承诺资本开支下的再投资率
# cyc：2027-2031 年报告利润相对正常化水平的周期偏离（税后，计作当年所有者收益）
SCEN = {
    "bear": dict(p=0.25, n0=46.0, g=[0.00, 0.03, 0.04, 0.04, 0.03],
                 rr=[0.40, 0.30, 0.30, 0.25, None], roic=None, gT=0.020, roicT=0.10,
                 cyc=[8.0, -15.0, -10.0, 0.0, 0.0]),
    "base": dict(p=0.50, n0=65.0, g=[0.12, 0.10, 0.08, 0.06, 0.05],
                 rr=None, roic=0.18, gT=0.025, roicT=0.15,
                 cyc=[18.0, 3.0, -12.0, -8.0, 0.0]),
    "bull": dict(p=0.25, n0=80.0, g=[0.22, 0.16, 0.12, 0.09, 0.06],
                 rr=None, roic=0.28, gT=0.025, roicT=0.20,
                 cyc=[20.0, 12.0, 0.0, 0.0, 0.0]),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def reinvest_rates(s):
    if s["rr"] is not None:
        rr = list(s["rr"])
        rr[-1] = s["gT"] / s["roicT"]
        return rr
    g = s["g"]
    return [g[i + 1] / s["roic"] for i in range(4)] + [s["gT"] / s["roicT"]]


def path(s):
    np_, out = s["n0"], []
    for g, rr in zip(s["g"], reinvest_rates(s)):
        np_ = np_ * (1 + g)
        out.append((np_, rr, np_ * (1 - rr)))
    return out


def interest_pv(r):
    nd = max(-NET_CASH_ADJ, 0.0)
    return nd * RATE * (1 - TAX) / r


def equity_value(s, r, levered=True, cycle=True):
    pv, rows = 0.0, path(s)
    for t, (np_, rr, oe) in enumerate(rows, start=1):
        cf = oe + (s["cyc"][t - 1] if cycle else 0.0)
        pv += cf / (1 + r) ** t
    np_T = rows[-1][0] * (1 + s["gT"])
    tv = np_T * (1 - s["gT"] / s["roicT"]) / (r - s["gT"])
    pv_tv = tv / (1 + r) ** len(rows)
    ops = pv + pv_tv
    if levered and NET_CASH_ADJ < 0:
        eq = ops - interest_pv(r) + NON_OP
    else:
        eq = ops + NET_CASH_ADJ + NON_OP
    return eq, ops, pv_tv


def per_share(s, r, **kw):
    return equity_value(s, r, **kw)[0] / SHARES


def weighted(r, scen=SCEN, probs=None, **kw):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * per_share(scen[k], r, **kw) for k in scen)


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


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


# ---------------------------------------------------------------- 反向 DCF（10 年恒定增速 + 终值）
def ev_const_growth(n0, g, roic, gT, roicT, r, years=10):
    pv, np_ = 0.0, n0
    for t in range(1, years + 1):
        np_ *= 1 + g
        rr = g / roic if t < years else gT / roicT
        pv += np_ * (1 - rr) / (1 + r) ** t
    tv = np_ * (1 + gT) * (1 - gT / roicT) / (r - gT)
    return pv + tv / (1 + r) ** years - interest_pv(r) + NON_OP


def main():
    print("== 输入与调整 ==")
    print(f"市值 {MCAP:,.2f} 亿；现金 {CASH:.2f} + 定存 {DEP_1Y + DEP_LT:.2f} − 有息负债 {DEBT:.2f} − 经营备付 {OP_RESERVE:.2f}"
          f" = 经调整净现金 {NET_CASH_ADJ:.2f} 亿（为负，用有杠杆口径）")
    print(f"有息负债实际平均利率 {RATE:.2%}；经调整净负债税后利息现值（9%）{interest_pv(COE):.2f} 亿")
    print(f"非经营资产（Meiko/CMK 税后 + 其他）{NON_OP:.2f} 亿")
    print(f"2026Q3 单季归母（预告中值）{NP_Q3_MID:.2f}；2026E 归母 {NP_2026E:.2f}；核心（加回前三季度汇兑损失、扣非经常）{NP_2026E_CORE:.2f}")
    print(f"2026E 营收（Q3/Q4 估计）{REV_2026E:.1f}；正常化基准净利率 {SCEN['base']['n0'] / (REV_2026E * 0.95):.1%}（按营收 95% 计）")

    print("\n== 三情景（9%）==")
    vs = {}
    for k, s in SCEN.items():
        eq, ops, pv_tv = equity_value(s, COE)
        v = eq / SHARES
        vs[k] = v
        rows = path(s)
        print(f"[{k}] p={s['p']:.2f} n0={s['n0']:.1f} 终值增长 {s['gT']:.1%} 终值ROIC {s['roicT']:.0%}")
        for y, (np_, rr, oe), c in zip(YEARS, rows, s["cyc"]):
            print(f"   {y}: 正常化归母 {np_:7.2f} 再投资率 {rr:5.1%} 所有者收益 {oe:6.2f} 周期偏离 {c:+6.1f}")
        print(f"   经营价值 {ops:,.1f}（终值占 {pv_tv / ops:.0%}） 股权价值 {eq:,.1f} 亿  V = {v:.2f} 元"
              f"  （无杠杆口径 {per_share(s, COE, levered=False):.2f}；不含周期偏离 {per_share(s, COE, cycle=False):.2f}）")
    vw = weighted(COE)
    vw_unlev = weighted(COE, levered=False)
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元  P/V = {pv:.2f} → {verdict(pv)}")
    print(f"无杠杆口径加权 V = {vw_unlev:.2f} 元  P/V = {PRICE / vw_unlev:.2f}")
    for r in (0.08, 0.10):
        print(f"股权成本 {r:.0%}: 熊 {per_share(SCEN['bear'], r):.2f} 基 {per_share(SCEN['base'], r):.2f} "
              f"牛 {per_share(SCEN['bull'], r):.2f} 加权 {weighted(r):.2f} P/V {PRICE / weighted(r):.2f}")
    print(f"V 不变时各档价格：≤{vw * 0.75:.2f} 明显低估；{vw * 0.75:.2f}～{vw * 0.90:.2f} 温和低估；"
          f"{vw * 0.90:.2f}～{vw * 1.10:.2f} 大致合理；>{vw * 1.10:.2f} 偏贵")

    # 现价隐含回报（基准情景所有者收益流含终值与净现金调整）
    irr = solve(lambda r: equity_value(SCEN["base"], r)[0], 0.035, 0.20, MCAP)
    print(f"\n现价隐含回报（基准情景）= {irr:.2%}")
    irr_bull = solve(lambda r: equity_value(SCEN["bull"], r)[0], 0.035, 0.20, MCAP)
    print(f"现价隐含回报（牛市情景）= {irr_bull:.2%}")

    # 反向 DCF
    b = SCEN["base"]
    g10 = solve(lambda g: ev_const_growth(b["n0"], g, b["roic"], b["gT"], b["roicT"], COE), 0.0, 0.40, MCAP)
    g10_core = solve(lambda g: ev_const_growth(NP_2026E_CORE, g, 0.28, 0.025, 0.20, COE), 0.0, 0.40, MCAP)
    print(f"反向 DCF：自正常化 {b['n0']:.0f} 亿、增量 ROIC 18%：2027-2036 年需年增 {g10:.1%}，2036 年归母 {b['n0'] * (1 + g10) ** 10:.0f} 亿")
    print(f"反向 DCF：自 2026E 核心 {NP_2026E_CORE:.1f} 亿、增量 ROIC 28%：需年增 {g10_core:.1%}，2036 年归母 {NP_2026E_CORE * (1 + g10_core) ** 10:.0f} 亿")
    gperp = solve(lambda g: b["n0"] * (1 + g) * (1 - g / b["roic"]) / (COE - g) - interest_pv(COE) + NON_OP, 0.0, 0.0899, MCAP)
    print(f"反向 DCF：自正常化 {b['n0']:.0f} 亿、ROIC 18% 的永续增速 = {gperp:.2%}")

    # 证伪情景
    print("\n== 证伪触发后的 V ==")
    s_f1 = dict(SCEN); s_f1["base"] = dict(SCEN["base"], n0=60.0)
    print(f"F1 三季报单季扣非 <25 亿或毛利率 <40%（基准 n0 降至 60）：V = {weighted(COE, scen=s_f1):.2f}")
    print(f"F2 2027 年任一单季营收同比下降或单季毛利率 <35%（权重 0.5/0.4/0.1）：V = "
          f"{weighted(COE, probs={'bear': 0.5, 'base': 0.4, 'bull': 0.1}):.2f}")
    print(f"F3 2027 年归母 ≥115 亿、毛利率 ≥42%、经营现金流 ≥0.8×归母（权重 0.1/0.4/0.5）：V = "
          f"{weighted(COE, probs={'bear': 0.1, 'base': 0.4, 'bull': 0.5}):.2f}")
    s_f4 = dict(SCEN); s_f4["base"] = dict(SCEN["base"], roic=0.14, roicT=0.12); s_f4["bull"] = dict(SCEN["bull"], roic=0.20, roicT=0.16)
    print(f"F4 2027 年资本开支 >110 亿且经营现金流 <0.6×归母（基准/牛市增量 ROIC 降至 14%/20%）：V = {weighted(COE, scen=s_f4):.2f}")
    # H 股发行敏感性：发行 2.0 亿股、净募资按 80 元/股折人民币
    eq_w = vw * SHARES
    for px in (60.0, 80.0, 100.0):
        print(f"H 股发行 2.0 亿股、净价 {px:.0f} 元：V = {(eq_w + 2.0 * px) / (SHARES + 2.0):.2f}")

    # 交叉验证
    print("\n== 交叉验证 ==")
    div_2026 = 22.0
    print(f"2026 年分红下限 22 亿 → 股息率 {div_2026 / MCAP:.2%}")
    print(f"PE：TTM {MCAP / 50.63:.1f}x；2026E {MCAP / NP_2026E:.1f}x；Q3 年化 {MCAP / (NP_Q3_MID * 4):.1f}x；正常化基准 {MCAP / b['n0']:.1f}x")
    print(f"PB：{MCAP / 179.89:.2f}x（2015-2025 年末区间 2.38～9.30x）")
    ev = MCAP - (CASH + DEP_1Y + DEP_LT) + DEBT - NON_OP
    ebit_26e = NP_2026E_CORE / (1 - 0.13)
    ebit_norm = b["n0"] / (1 - 0.13)
    print(f"EV {ev:,.1f} 亿；EV/EBIT 2026E 核心 {ev / ebit_26e:.1f}x；正常化 {ev / ebit_norm:.1f}x")
    print(f"历史年末 PE（2019-2025）中位约 29.4x：×正常化基准 {29.4 * b['n0'] / SHARES:.1f} 元；×2026E {29.4 * NP_2026E / SHARES:.1f} 元")
    opt = 0.14761750
    print(f"期权（第一个行权期 1,476.18 万份，行权价 19.22）库存股法稀释：V × {1 / (1 + opt * (1 - 19.22 / vw) / SHARES):.4f}")


if __name__ == "__main__":
    main()
