#!/usr/bin/env python3
"""300015 爱尔眼科 独立估值（OI-291 b10，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。全部输入写在本脚本内，来源见同目录外的
companies/300015_爱尔眼科.md 第 9 节。

主口径：租赁视为经营成本（归母净利已扣使用权资产折旧与租赁利息，近似房租），
租赁负债不计入有息负债；经调整净现金为正，按无杠杆口径全额扣除银行借款。
另一口径：租赁负债计入有息负债，经调整净现金为负，按框架的有杠杆口径计算。
"""

PRICE = 7.94
SHARES = 92.81000213          # 亿股，2026-10-19 注销 1,856.4521 万股后总股本（含回购专户）
TREASURY = 0.12798657         # 回购专户剩余 12,798,657 股（2024-10 完成回购，用途为股权激励/员工持股）
SHARES_EX = SHARES - TREASURY
COE = 0.09
MCAP = PRICE * SHARES

# ---------- 1. 2026 正常化归母净利 ----------
H1_REPORTED = 13.570          # 2026H1 归母净利（2026H1_report 第 18 页）
ADJ_TAX_SELFCHECK = 3.48 + 2.32   # 自查补缴往期税款 + 调增 2025 年所得税汇算清缴额（第 70 页）
ADJ_LATE_FEE = 1.76           # 滞纳金，计入营业外支出（第 32、70 页）
ADJ_SBP_REVERSAL = -1.075     # 2021 年限制性股票未达考核、股份支付费用冲回（第 18、32 页推算）
ADJ_FX = 0.53 * 0.85          # 财务费用中汇兑损失约 0.53 亿，按税后 85% 加回（第 84 页推算）
H1_NORM = H1_REPORTED + ADJ_TAX_SELFCHECK + ADJ_LATE_FEE + ADJ_SBP_REVERSAL + ADJ_FX

Q3_2025_NP, Q4_2025_NP = 10.638, 1.255          # 2025 单季归母净利（2025_annual_report 第 21 页）
Q3_2025_REV, Q4_2025_REV = 59.767, 48.687
H1_2026_REV = 119.457

# ---------- 2. 经调整净现金与非经营资产（2026-06-30 时点，扣日后已知流出） ----------
CASH = 55.598                 # 货币资金
TFA = 11.586                  # 交易性金融资产（银行理财 5.51 + 资管计划 6.08）
OTHER_DEBT_INV = 3.215        # 其他债权投资（CB 基金投资，类现金）
RESTRICTED = 0.160            # 冻结资金
OPER_RESERVE = 8.0            # 经营备付：约 1 个月职工薪酬现金支出
DIV_DECLARED = 9.268          # 2025 年度分红 9.27 亿，2026-07-17 派发，6-30 未入负债
FUND_COMMIT = 2.0             # 2026-07-31 认缴共青城坚持盛启专项基金
BRAZIL = 6.96                 # 巴西增资 5.30 亿雷亚尔，待交割
BANK_DEBT = 21.717 + 1.807 + 0.257   # 短期借款 + 长期借款 + 一年内到期长期借款
CONTINGENT = 0.795            # 其他非流动负债：或有对价
LEASE_LIAB = 44.172 + 8.755   # 租赁负债 + 一年内到期租赁负债（主口径不计入）

NET_CASH_ADJ = (CASH + TFA + OTHER_DEBT_INV - RESTRICTED - OPER_RESERVE - DIV_DECLARED
                - FUND_COMMIT - BRAZIL - BANK_DEBT - CONTINGENT)

OTHER_NC_FIN = 7.935          # 其他非流动金融资产（亮视系基金 LP 份额等），打 8 折
LT_EQUITY = 1.035 + 0.366     # 长期股权投资 + 其他权益工具投资，打 8 折
HAIRCUT = 0.8
NONOP_EX_BRAZIL = (OTHER_NC_FIN + LT_EQUITY + FUND_COMMIT) * HAIRCUT
BRAZIL_VALUE = {"bear": BRAZIL * 0.7, "base": BRAZIL, "bull": BRAZIL}   # 按成本计（熊市打 7 折）

# 另一口径（租赁计入有息负债）所需利率
INT_EXP_ANNUAL = 1.295 * 2    # 2026H1 利息费用年化（含租赁利息）
INT_INC_ANNUAL = 0.203 * 2    # 2026H1 利息收入年化
AVG_IB_DEBT = ((15.275 + 1.396 + 0.182 + 47.155 + 8.164) + (BANK_DEBT + LEASE_LIAB)) / 2
R_DEBT = INT_EXP_ANNUAL / AVG_IB_DEBT
TAX_RATE = 0.20

# ---------- 3. 情景 ----------
SCEN = {
    "bear": dict(p=0.30, q3=-0.10, q4_np=0.60, q3_rev=-0.01, q4_rev=0.00, struct_tax=-2.32,
                 rev_g=[0.035, 0.035, 0.035, 0.030, 0.030],
                 margin=[0.124, 0.123, 0.122, 0.121, 0.120],
                 intensity=1.2, g_t=0.020, roiic_t=0.09),
    "base": dict(p=0.50, q3=-0.02, q4_np=1.30, q3_rev=0.025, q4_rev=0.03, struct_tax=-0.45,
                 rev_g=[0.060, 0.060, 0.055, 0.050, 0.045],
                 margin=[0.139, 0.142, 0.144, 0.146, 0.147],
                 intensity=1.0, g_t=0.025, roiic_t=0.12),
    "bull": dict(p=0.20, q3=0.03, q4_np=1.80, q3_rev=0.05, q4_rev=0.05, struct_tax=0.0,
                 rev_g=[0.080, 0.080, 0.075, 0.070, 0.060],
                 margin=[0.148, 0.154, 0.158, 0.161, 0.163],
                 intensity=0.8, g_t=0.025, roiic_t=0.15),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def normalized_2026(s):
    np26 = H1_NORM + Q3_2025_NP * (1 + s["q3"]) + s["q4_np"] + s["struct_tax"]
    rev26 = H1_2026_REV + Q3_2025_REV * (1 + s["q3_rev"]) + Q4_2025_REV * (1 + s["q4_rev"])
    return np26, rev26


def project(s, margin_shift=0.0, intensity=None):
    """逐年收入、归母净利、净再投资与所有者收益。"""
    inten = s["intensity"] if intensity is None else intensity
    np26, rev26 = normalized_2026(s)
    revs = [rev26]
    for g in s["rev_g"]:
        revs.append(revs[-1] * (1 + g))
    rev_next = revs[-1] * (1 + s["g_t"])
    nps = [r * (m + margin_shift) for r, m in zip(revs[1:], s["margin"])]
    # 2027～2030：为下一年收入增量所需的净再投资（资本强度 × 收入增量）；
    # 2031：与终值一致，再投资率 = 终值增速 ÷ 终值增量回报
    reinv = [(revs[i + 2] - revs[i + 1]) * inten for i in range(4)]
    reinv.append(nps[-1] * s["g_t"] / s["roiic_t"])
    oe = [n - r for n, r in zip(nps, reinv)]
    # 2026 下半年存根：正常化下半年净利 − 半年再投资
    stub = (np26 - H1_NORM) - 0.5 * (revs[1] - revs[0]) * inten
    return dict(np26=np26, rev26=rev26, revs=revs, nps=nps, reinv=reinv, oe=oe, stub=stub)


def equity_value(s, k=COE, margin_shift=0.0, intensity=None, lease_as_debt=False, scen_name="base"):
    pj = project(s, margin_shift, intensity)
    pv_oe = sum(o / (1 + k) ** (i + 1) for i, o in enumerate(pj["oe"]))
    rr_t = s["g_t"] / s["roiic_t"]
    oe_t1 = pj["nps"][-1] * (1 + s["g_t"]) * (1 - rr_t)
    tv = oe_t1 / (k - s["g_t"]) / (1 + k) ** 5
    nonop = NONOP_EX_BRAZIL + BRAZIL_VALUE[scen_name]
    if not lease_as_debt:
        eq = pv_oe + tv + pj["stub"] + NET_CASH_ADJ + nonop
    else:
        # 有杠杆口径：经营所有者收益加回税后净财务费用，再扣经调整净负债税后利息现值（规模不变、不还本）
        net_debt = LEASE_LIAB - NET_CASH_ADJ
        fin_cost_at = (INT_EXP_ANNUAL - INT_INC_ANNUAL) * (1 - TAX_RATE)
        pv_fin_addback = fin_cost_at / k
        pv_int = net_debt * R_DEBT * (1 - TAX_RATE) / k
        eq = pv_oe + tv + pj["stub"] + pv_fin_addback - pv_int + nonop
    return eq, pv_oe, tv, pj


def per_share(eq, shares=SHARES):
    return eq / shares


def weighted(values, weights):
    return sum(values[n] * weights[n] for n in values)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    W = {n: s["p"] for n, s in SCEN.items()}
    print("== 正常化 ==")
    print(f"2026H1 归母正常化 {H1_NORM:.2f}（报告 {H1_REPORTED:.2f}）")
    for n, s in SCEN.items():
        np26, rev26 = normalized_2026(s)
        print(f"{n}: 2026 正常化归母 {np26:.2f}  收入 {rev26:.1f}  净利率 {np26 / rev26:.2%}")
    print(f"经调整净现金（主口径，含已承诺流出） {NET_CASH_ADJ:.2f}；非经营资产（基准，含巴西按成本） "
          f"{NONOP_EX_BRAZIL + BRAZIL:.2f}；租赁负债 {LEASE_LIAB:.2f}；有息负债平均利率 {R_DEBT:.2%}")

    print("\n== 三情景（股权成本 9%，主口径） ==")
    V = {}
    for n, s in SCEN.items():
        eq, pv_oe, tv, pj = equity_value(s, scen_name=n)
        V[n] = per_share(eq)
        tv_share = tv / (pv_oe + tv)
        rr = [r / x for r, x in zip(pj["reinv"], pj["nps"])]
        reinv_26 = (pj["revs"][1] - pj["revs"][0]) * s["intensity"]
        incr = (pj["nps"][-1] - pj["np26"]) / (reinv_26 + sum(pj["reinv"][:4]))
        g_np = [pj["nps"][0] / pj["np26"] - 1] + [pj["nps"][i] / pj["nps"][i - 1] - 1 for i in range(1, 5)]
        print(f"{n}: V={V[n]:.2f} 元  股权 {eq:.1f} 亿  终值占比 {tv_share:.0%}  p={s['p']}")
        print("   收入 " + " ".join(f"{y}:{x:.1f}" for y, x in zip([2026] + YEARS, pj["revs"])))
        print("   归母净利 " + " ".join(f"{y}:{x:.1f}" for y, x in zip(YEARS, pj["nps"])))
        print("   净利增速 " + " ".join(f"{x:.1%}" for x in g_np))
        print("   所有者收益 " + " ".join(f"{x:.1f}" for x in pj["oe"]) + f"  存根(2026H2) {pj['stub']:.1f}")
        print("   再投资率 " + " ".join(f"{x:.0%}" for x in rr) + f"  平均 {sum(rr) / 5:.0%}"
              f"  终值再投资率 {s['g_t'] / s['roiic_t']:.0%}")
        print(f"   增量回报：五年（含利润率变化）{incr:.1%}；不含利润率变化 {s['margin'][-1] / s['intensity']:.1%}；"
              f"终值 {s['roiic_t']:.0%}")
    vw = weighted(V, W)
    pv_ratio = PRICE / vw
    print(f"加权 V = {vw:.2f} 元；P/V = {pv_ratio:.2f}（{tier(pv_ratio)}）")
    print(f"V 不变时各档价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n== 股权成本敏感性（加权） ==")
    for k in (0.08, 0.10):
        vk = {n: per_share(equity_value(s, k=k, scen_name=n)[0]) for n, s in SCEN.items()}
        print(f"COE {k:.0%}: " + " ".join(f"{n} {vk[n]:.2f}" for n in vk) + f"  加权 {weighted(vk, W):.2f}")

    print("\n== 现价隐含回报（基准情景现金流） ==")
    irr = solve(lambda k: equity_value(SCEN["base"], k=k, scen_name="base")[0], 0.04, 0.12, MCAP)
    print(f"隐含回报率 {irr:.2%}")

    print("\n== 反向 DCF ==")
    base = SCEN["base"]
    np26_b, _ = normalized_2026(base)
    stub_b = project(base)["stub"]
    other = stub_b + NET_CASH_ADJ + NONOP_EX_BRAZIL + BRAZIL

    def v_g10(g, roiic=0.15):
        npv, v, n = np26_b, 0.0, 0
        for t in range(1, 11):
            npv *= 1 + g
            v += npv * (1 - min(g / roiic, 0.9)) / (1 + COE) ** t
        oe_t = npv * (1 + 0.025) * (1 - 0.025 / 0.12)
        v += oe_t / (COE - 0.025) / (1 + COE) ** 10
        return v + other

    g10 = solve(v_g10, 0.0, 0.25, MCAP)
    gperp = solve(lambda g: np26_b * (1 + g) * (1 - g / 0.12) / (COE - g) + other, 0.0, 0.085, MCAP)
    print(f"10 年归母净利年增速（再投资回报 15%，之后 2.5%）需 {g10:.1%}；"
          f"永续增速（再投资回报 12%）需 {gperp:.2%}")
    print(f"现价对应 2026 正常化归母 PE {MCAP / np26_b:.1f}x；加权 V 对应 {weighted(V, W) * SHARES / np26_b:.1f}x；"
          f"基准 V 对应 {V['base'] * SHARES / np26_b:.1f}x")

    print("\n== 交叉验证 ==")
    div_ttm = 0.08 + 0.10                     # 2026-01-15 与 2026-07-17 除息
    print(f"近 12 个月股息 {div_ttm:.2f} 元，股息率 {div_ttm / PRICE:.2%}；近 12 个月无新增回购")
    ebit_n = (np26_b + 2.4) / (1 - 0.215) + 0.6 - 0.4   # 正常化归母 + 少数股东 → 税前，再加回银行净利息
    ev = MCAP + 14.21 - NET_CASH_ADJ - (NONOP_EX_BRAZIL + BRAZIL)
    print(f"正常化 EBIT（租赁按经营成本）约 {ebit_n:.1f} 亿；EV（不含租赁，少数股东按账面）{ev:.1f} 亿；EV/EBIT {ev / ebit_n:.1f}x")
    print(f"PB {MCAP / 230.199:.2f}x（6-30 归母权益 230.20）；TTM 报告口径 PE {MCAP / 25.46:.1f}x")

    print("\n== 另一口径：租赁负债计入有息负债（有杠杆口径） ==")
    VL = {n: per_share(equity_value(s, lease_as_debt=True, scen_name=n)[0]) for n, s in SCEN.items()}
    vlw = weighted(VL, W)
    print(" ".join(f"{n} {VL[n]:.2f}" for n in VL) + f"  加权 {vlw:.2f}  P/V {PRICE / vlw:.2f}"
          f"  经调整净负债 {LEASE_LIAB - NET_CASH_ADJ:.2f}")

    print("\n== 剔除回购专户股份 ==")
    vx = {n: equity_value(s, scen_name=n)[0] / SHARES_EX for n, s in SCEN.items()}
    print(" ".join(f"{n} {vx[n]:.2f}" for n in vx) + f"  加权 {weighted(vx, W):.3f}  P/V {PRICE / weighted(vx, W):.3f}")

    print("\n== H 股发行敏感性（不超过发行后总股本 10%，未含超额配售） ==")
    h = SHARES / 9
    eq_w = vw * SHARES
    for ph in (7.0, 6.0, 5.0):
        v_post = (eq_w + h * ph * 0.97) / (SHARES + h)
        print(f"按 {ph:.1f} 元（人民币计，净费 3%）发行 {h:.2f} 亿股：加权 V {vw:.2f} → {v_post:.2f}")

    print("\n== 证伪触发后的 V ==")
    f1 = weighted(V, {"bear": 0.5, "base": 0.4, "bull": 0.1})
    v_tax = per_share(equity_value(SCEN["base"], margin_shift=-0.010, scen_name="base")[0])
    f2 = weighted({"bear": V["bear"], "base": v_tax, "bull": V["bull"]}, W)
    f3 = V["bear"]
    f4 = per_share(equity_value(SCEN["bear"], intensity=1.5, scen_name="bear")[0])
    f5 = weighted(V, {"bear": 0.1, "base": 0.5, "bull": 0.4})
    print(f"F1 三季报低于门槛（权重 0.5/0.4/0.1）：{f1:.2f}")
    print(f"F2 税负结构性上升（基准净利率 −1.0pp）：基准 {v_tax:.2f}，加权 {f2:.2f}")
    print(f"F3 2027H1 扣非不增长（熊市）：{f3:.2f}")
    print(f"F4 并购回报失败（熊市、资本强度 1.5）：{f4:.2f}")
    print(f"F5 上行：2027H1 显著回升（权重 0.1/0.5/0.4）：{f5:.2f}")


if __name__ == "__main__":
    main()
