"""快手-W（01024）独立估值：分部加总（核心平台所有者收益 DCF + 可灵股权 + 经调整净现金 + 非经营资产）。

运行：python3 kuaishou_valuation.py
金额单位：亿元人民币；每股价值与价格为港元。输入全部写在本脚本内，来源见注释与正文
data/experiments/exp_independent_kuaishou_20261022/companies/01024_快手.md。
页码写法：「中期业绩」= 2026-08-19 业绩公告（港交所 2026081900315_c.pdf）PDF 物理页；
「中报」= 2026 年中期报告（2026090300643_c.pdf）印刷页；「年报」= 2025 年报（2026042401900_c.pdf）印刷页。
"""

# ---------------------------------------------------------------- 快照
PRICE_HKD = 28.04            # 2026-10-21 港股收盘（任务统一快照）
HKD_CNY = 0.8509             # 1 港元 = 0.8509 元人民币（任务统一快照）
SHARES_YI = 43.04151598      # 2026-09 月报表：B 类 3,644,802,646 + A 类 659,348,952，库存股 0
COE_BASE = 0.10

# ---------------------------------------------------------------- 2026 年利润（合并口径）
H1_REV, H1_ADJ_NP, H1_SBC = 692.51, 72.87, 13.11         # 中期业绩第 2、22 页
H2_2025_REV, H2_2025_ADJ_NP = 751.22, 104.49             # 年报第 27 页：Q3 355.54+Q4 395.68；经调整 49.86+54.63
SBC_H2_2026 = 14.0                                       # 假设：2025H2 为 13.20
MINORITY = 0.1
NET_FIN_INCOME_AT = 22.0     # 推断：理财公允价值收益约 33.8 − 财务开支净额约 10.0 + 租赁利息约 4.5，税后（20%）约 22

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，中期业绩第 26–27 页，中报附注 22）
LIQUID = {"现金及现金等价物": 116.96, "短期定期存款": 123.58, "长期定期存款": 142.91,
          "理财产品及其他（非流动）": 271.16, "理财产品及其他（流动）": 556.34}
DEDUCT = {"借款（含应计利息）": 273.62, "应付票据（银行承兑，类债务）": 252.48,
          "可退还客户保证金": 86.57, "客户预付款": 48.42, "应付股息（2026-07 已付）": 25.84,
          "其他应付款经营浮存（雇员福利 37.84+其他税项 8.56+其他 30.75）": 77.15,
          "2026Q3 回购现金（估计，股本已按 9-30 计）": 7.0}
WHT_FACTOR = 0.92            # 境内约八成现金汇出按 10% 预提税
CASH_YIELD_AT = 0.03         # 现金税后收益率（假设）；兑现系数 = ((1+y)/(1+r))**N

# ---------------------------------------------------------------- 非经营资产（中期业绩第 34 页附注 7；资产负债表）
NONOP_GROSS = 25.02 + 7.19 + 1.30   # 非上市实体投资 + 上市实体投资 + 权益法投资

# ---------------------------------------------------------------- 可灵（2026-07-02 与 08-31 公告）
KLING_SUB_RMB = 204.471      # 认购上限人民币 20,447.10 百万元，已全数用完（08-31 公告第 3 页）
KLING_INV_UNITS = 96175864 - (63796656 + 1923517 + 961759 + 2885276 + 432792 + 2404398 + 7742156)
KLING_TOTAL_UNITS = 96175864
KS_STAKE = (63796656 + 1923517) / KLING_TOTAL_UNITS      # Lucky Labs 66.33% + 北京快灵瑞 2.00%
INV_STAKE = KLING_INV_UNITS / KLING_TOTAL_UNITS          # 约 16.67%
ESOP_STAKE = 1 - KS_STAKE - INV_STAKE                    # 约 15%
KLING_ROUND_POST = KLING_SUB_RMB / INV_STAKE             # 投后（全面摊薄）约 1,227 亿元

# ---------------------------------------------------------------- 情景
# core_rev_2026：剔除可灵（约 38 亿元）后的 2026E 收入；da_core_2026：剔除可灵后的 2026E 折旧摊销（集团约 103 − 可灵约 10）
SCEN = {
    "bear": dict(p=0.30, h2_rev_g=-0.02, h2_adj_np=70.0, kling_addback=10.0, da_ss=0.100,
                 growth=[-0.06, -0.03, 0.00, 0.00, 0.01], g_t=0.000, roiic=0.08,
                 excess_capex=[(0.0, 60.0), (1.0, 40.0)], cash_years=9.0, nonop_disc=0.50,
                 kling_equity=300.0, kling_pref_weight=1.0, kling_disc=0.30),
    "base": dict(p=0.50, h2_rev_g=0.02, h2_adj_np=80.0, kling_addback=18.0, da_ss=0.085,
                 growth=[0.02, 0.04, 0.05, 0.04, 0.03], g_t=0.020, roiic=0.15,
                 excess_capex=[(0.0, 20.0)], cash_years=4.5, nonop_disc=0.30,
                 kling_equity=600.0, kling_pref_weight=0.5, kling_disc=0.25),
    "bull": dict(p=0.20, h2_rev_g=0.05, h2_adj_np=88.0, kling_addback=22.0, da_ss=0.075,
                 growth=[0.08, 0.08, 0.07, 0.06, 0.05], g_t=0.025, roiic=0.20,
                 excess_capex=[], cash_years=1.6, nonop_disc=0.15,
                 kling_equity=KLING_ROUND_POST, kling_pref_weight=0.0, kling_disc=0.15),
}
KLING_REV_2026 = 38.0
DA_GROUP_2026 = 103.1         # 物业及设备折旧约 69 + 使用权资产约 33.5 + 无形资产约 0.6（推断）
DA_KLING_2026 = 10.0          # 假设
TAX_NORM = 0.125              # 折旧正常化的税盾（假设）
YEARS = [2027, 2028, 2029, 2030, 2031]


def adjusted_net_cash():
    gross = sum(LIQUID.values()) - sum(DEDUCT.values())
    return gross, gross * WHT_FACTOR


def normalized_np_2026(s):
    adj = H1_ADJ_NP + s["h2_adj_np"]
    return adj - (H1_SBC + SBC_H2_2026) - MINORITY


def revenue_2026(s):
    return H1_REV + H2_2025_REV * (1 + s["h2_rev_g"])


def core_oe_2026(s):
    """剔除净利息、加回可灵亏损、折旧摊销按稳态资本开支正常化后的核心所有者收益。"""
    core_rev = revenue_2026(s) - KLING_REV_2026
    da_gap = s["da_ss"] * core_rev - (DA_GROUP_2026 - DA_KLING_2026)
    da_norm_at = max(da_gap, 0.0) * (1 - TAX_NORM)
    oe = normalized_np_2026(s) - NET_FIN_INCOME_AT + s["kling_addback"] - da_norm_at
    return oe, da_norm_at, core_rev


def core_value(s, r):
    oe0, _, _ = core_oe_2026(s)
    g_list = s["growth"] + [s["g_t"]]
    oe, pv, rows = oe0, 0.0, []
    for i, year in enumerate(YEARS):
        oe = oe * (1 + g_list[i])
        rr = max(g_list[i + 1], 0.0) / s["roiic"]
        fcf = oe * (1 - rr)
        disc = (1 + r) ** (i + 1)
        pv += fcf / disc
        rows.append((year, g_list[i], oe, rr, fcf, fcf / disc))
    oe_next = oe * (1 + s["g_t"])
    tv = oe_next * (1 - max(s["g_t"], 0.0) / s["roiic"]) / (r - s["g_t"])
    pv_tv = tv / (1 + r) ** len(YEARS)
    # 2026 下半年：半年核心所有者收益（扣为 2027 年增长的再投资）减超额资本开支
    rr0 = max(g_list[0], 0.0) / s["roiic"]
    h2 = 0.5 * oe0 * (1 - rr0)
    excess = sum(amt / (1 + r) ** t for t, amt in s["excess_capex"])
    return pv + pv_tv + h2 - excess, dict(rows=rows, tv=tv, pv_tv=pv_tv, pv_explicit=pv, h2=h2, excess=excess)


def cash_value(s, r):
    _, net = adjusted_net_cash()
    factor = ((1 + CASH_YIELD_AT) / (1 + r)) ** s["cash_years"]
    return net * factor, factor


def kling_value(s):
    eq = s["kling_equity"]
    pro_rata = INV_STAKE * eq
    claim = s["kling_pref_weight"] * max(pro_rata, KLING_SUB_RMB) + (1 - s["kling_pref_weight"]) * pro_rata
    ks_share = KS_STAKE / (KS_STAKE + ESOP_STAKE)
    gross = max(eq - claim, 0.0) * ks_share
    return gross * (1 - s["kling_disc"]), gross


def nonop_value(s):
    return NONOP_GROSS * (1 - s["nonop_disc"])


def equity_value(s, r, kling_override=None, cash_years=None, extra_cash=0.0, excess_extra=0.0):
    core, _ = core_value(s, r)
    s2 = dict(s)
    if cash_years is not None:
        s2["cash_years"] = cash_years
    cash, _ = cash_value(s2, r)
    kling = kling_value(s)[0] if kling_override is None else kling_override
    total = core - excess_extra + cash + extra_cash + kling + nonop_value(s)
    return total


def per_share_hkd(total_yi):
    return total_yi / HKD_CNY / SHARES_YI


def v(s, r, **kw):
    return per_share_hkd(equity_value(s, r, **kw))


def weighted(r, scen=SCEN, probs=None, **kw):
    probs = probs or {k: x["p"] for k, x in scen.items()}
    return sum(probs[k] * v(scen[k], r, **kw) for k in scen)


def solve(f, lo, hi, target, iters=200):
    flo = f(lo) - target
    for _ in range(iters):
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


def main():
    mcap_hkd = PRICE_HKD * SHARES_YI
    mcap_rmb = mcap_hkd * HKD_CNY
    gross_cash, net_cash = adjusted_net_cash()
    print("== 快照")
    print(f"价格 {PRICE_HKD:.2f} 港元，股本 {SHARES_YI:.4f} 亿股，市值 {mcap_hkd:.1f} 亿港元 = {mcap_rmb:.1f} 亿元")
    print(f"经调整净现金（扣预提税前）{gross_cash:.2f}，扣预提税后 {net_cash:.2f}（net_cash_adj_yi）")
    print(f"可灵：投资者 {INV_STAKE:.4%}，快手 {KS_STAKE:.4%}，激励 {ESOP_STAKE:.4%}；本轮投后 {KLING_ROUND_POST:.1f} 亿元")
    print(f"非经营资产账面 {NONOP_GROSS:.2f}")

    print("\n== 情景（股权成本 10%）")
    results = {}
    for k, s in SCEN.items():
        oe0, da_norm, core_rev = core_oe_2026(s)
        core, det = core_value(s, COE_BASE)
        cash, fac = cash_value(s, COE_BASE)
        kling, kling_gross = kling_value(s)
        nonop = nonop_value(s)
        total = core + cash + kling + nonop
        vs = per_share_hkd(total)
        results[k] = vs
        print(f"-- {k}：2026E 收入 {revenue_2026(s):.1f}，正常化归母净利 {normalized_np_2026(s):.1f}，"
              f"核心收入 {core_rev:.1f}，折旧正常化（税后）{da_norm:.1f}，核心所有者收益 {oe0:.1f}")
        for (year, g, oe, rr, fcf, pvf) in det["rows"]:
            print(f"   {year}: 增速 {g:+.1%} 所有者收益 {oe:.1f} 再投资率 {rr:.1%} 可分配 {fcf:.1f} 现值 {pvf:.1f}")
        print(f"   终值 {det['tv']:.1f}（现值 {det['pv_tv']:.1f}，占核心 {det['pv_tv'] / core:.0%}）；2026H2 {det['h2']:.1f}；超额资本开支现值 −{det['excess']:.1f}")
        print(f"   核心 {core:.1f} + 净现金 {cash:.1f}（兑现系数 {fac:.3f}）+ 可灵 {kling:.1f}（折价前 {kling_gross:.1f}）+ 非经营 {nonop:.1f}"
              f" = {total:.1f} 亿元 → V = {vs:.2f} 港元")
        print(f"   每股拆分（港元）：核心 {per_share_hkd(core):.2f}，净现金 {per_share_hkd(cash):.2f}，"
              f"可灵 {per_share_hkd(kling):.2f}，非经营 {per_share_hkd(nonop):.2f}")

    vw = sum(SCEN[k]["p"] * results[k] for k in SCEN)
    pv = PRICE_HKD / vw
    print(f"\n加权 V = {vw:.2f} 港元；P/V = {pv:.3f}（{verdict(pv)}）；10-22 盘中 26.82 港元时 P/V {26.82 / vw:.3f}")
    vw_sym = 0.25 * results["bear"] + 0.5 * results["base"] + 0.25 * results["bull"]
    print(f"对照：概率 25/50/25 时加权 V = {vw_sym:.2f}，P/V = {PRICE_HKD / vw_sym:.3f}")
    print("进入各档的价格（V 不变）：≤0.75 → ≤{:.2f}；0.90 → {:.2f}；1.10 → {:.2f}".format(0.75 * vw, 0.90 * vw, 1.10 * vw))

    print("\n== 股权成本敏感性（V，港元）")
    for r in (0.08, 0.09, 0.10, 0.11, 0.12):
        line = "  ".join(f"{k} {v(SCEN[k], r):.2f}" for k in SCEN)
        print(f"r={r:.0%}: {line}  加权 {weighted(r):.2f}  P/V {PRICE_HKD / weighted(r):.3f}")

    irr = solve(lambda r: v(SCEN["base"], r), 0.05, 0.60, PRICE_HKD)
    irr_w = solve(lambda r: weighted(r), 0.05, 0.60, PRICE_HKD)
    irr_bear = solve(lambda r: v(SCEN["bear"], r), 0.03, 0.60, PRICE_HKD)
    print(f"\n现价隐含回报：基准情景 {irr:.1%}；加权 {irr_w:.1%}；熊市情景 {irr_bear:.1%}")

    # 反向 DCF：核心所有者收益永续增速（基准非核心项不变；可灵另记 0）
    b = SCEN["base"]
    oe0 = core_oe_2026(b)[0]
    noncore = cash_value(b, COE_BASE)[0] + kling_value(b)[0] + nonop_value(b)
    core_implied = mcap_rmb - noncore
    core_implied_k0 = mcap_rmb - cash_value(b, COE_BASE)[0] - nonop_value(b)

    def gordon(g, r=COE_BASE, roiic=b["roiic"]):
        return oe0 * (1 + g) * (1 - max(g, 0.0) / roiic) / (r - g)

    g1 = solve(gordon, -0.60, 0.05, core_implied)
    g2 = solve(gordon, -0.60, 0.05, core_implied_k0)

    def ten_year(g, r=COE_BASE, gt=0.02, roiic=b["roiic"]):
        oe, pvs = oe0, 0.0
        for t in range(1, 11):
            oe *= (1 + g)
            pvs += oe * (1 - max(g, 0.0) / roiic) / (1 + r) ** t
        return pvs + oe * (1 + gt) * (1 - gt / roiic) / (r - gt) / (1 + r) ** 10

    g3 = solve(ten_year, -0.60, 0.20, core_implied_k0)
    print(f"现价隐含核心价值 {core_implied:.1f} 亿元（可灵按基准）/ {core_implied_k0:.1f}（可灵记 0）；基准核心所有者收益 {oe0:.1f}")
    print(f"反向 DCF：核心所有者收益永续增速 {g1:.1%}（可灵按基准）/ {g2:.1%}（可灵记 0）；"
          f"可灵记 0 时前 10 年年增速 {g3:.1%} 后转 2%")

    print("\n== 交叉验证")
    np_base = normalized_np_2026(b)
    print(f"市值/2026E 正常化归母净利（基准 {np_base:.1f}）= {mcap_rmb / np_base:.1f} 倍；"
          f"市值/TTM 归母净利 157.66 = {mcap_rmb / 157.66:.1f} 倍；市值/2026E 经调整净利 {H1_ADJ_NP + b['h2_adj_np']:.1f} = "
          f"{mcap_rmb / (H1_ADJ_NP + b['h2_adj_np']):.1f} 倍")
    ev = mcap_rmb - net_cash - NONOP_GROSS
    ebit = (np_base - NET_FIN_INCOME_AT) / (1 - 0.12)
    print(f"EV（市值 − 扣税后净现金 − 非经营资产账面）{ev:.1f}；2026E EBIT 约 {ebit:.1f}；EV/EBIT {ev / ebit:.1f} 倍")
    div_hkd = 0.69 * SHARES_YI
    print(f"股息 0.69 港元/股 = {div_hkd:.2f} 亿港元，股息率 {0.69 / PRICE_HKD:.1%}；2026-01～07 回购 19.69 亿港元")
    print(f"可灵按本轮价的快手权益 {KS_STAKE * KLING_ROUND_POST:.1f} 亿元 = {per_share_hkd(KS_STAKE * KLING_ROUND_POST):.2f} 港元/股")
    fcf = {"2025": 267.16 - 149.42 - 38.0, "2026H1": 90.44 - 179.41 - 19.19}
    print("自由现金流（经营现金流 − 资本开支 − 租赁付款）：" + "；".join(f"{k} {x:.1f}" for k, x in fcf.items()))

    print("\n== 证伪触发后的独立 V（港元，股权成本 10%）")
    f1 = weighted(COE_BASE, probs={"bear": 0.5, "base": 0.45, "bull": 0.05})
    print(f"F1 三季报收入同比 <0 且经调整净利 <33 亿元 → 概率改为 50/45/5：{f1:.2f}")
    f2 = weighted(COE_BASE, cash_years=9.0, excess_extra=60.0)
    print(f"F2 2026 年资本开支付款 >350 亿元或 2027 年指引不低于 2026 年 → 净现金兑现期 9 年、另扣超额资本开支 60 亿元：{f2:.2f}")
    kb = kling_value(SCEN["bear"])[0]
    f3 = weighted(COE_BASE, kling_override=kb)
    print(f"F3 可灵出现低于本轮价的融资或转让，或 2027Q2 单季收入 <12 亿元 → 可灵各情景按熊市值：{f3:.2f}")
    f4 = 0.6 * results["bear"] + 0.4 * results["base"]
    print(f"F4 快手应用日活连续两个季度同比下降 → 熊 60%、基准 40%：{f4:.2f}")
    f5 = weighted(COE_BASE, extra_cash=-125.0)
    print(f"F5 2026-12-31 借款加应付票据 >650 亿元（较 6-30 多约 125 亿元）→ 净现金再扣 125 亿元：{f5:.2f}")


if __name__ == "__main__":
    main()
