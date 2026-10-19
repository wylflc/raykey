#!/usr/bin/env python3
"""德业股份（605117）独立估值：OI-291 池内独立审计 b02（深度版）。

价格日 2026-10-19，现价 71.35 元，总股本 12.7328 亿股（腾讯行情口径；
2026-08-26 公告总股本 1,273,282,072 股，H 股尚未发行）。
最新定期报告为 2026 中报；三季度用 2026-10-15 前三季度业绩预增公告估计，
三季报预约 2026-10-30 披露。

方法：所有者收益 DCF（归母口径，股权成本 9%，敏感性 8%/10%），
V = 经调整净现金 + 非经营资产 + PV(2026 下半年所有者收益)
    + PV(2027-2036 所有者收益) + PV(终值) - PV(营运资金浮存回吐)。
经营利润口径剔除净利息与理财收益（对应现金已在净现金中计入），避免重复计算。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。
"""

PRICE = 71.35
SHARES = 12.7328          # 亿股，腾讯行情口径
COE = 0.09
T_H2_2026 = 0.10          # 2026 下半年现金流的折现时点（年，自 2026-10-19 起）
T_2027 = 0.70             # 2027 年年中，距价格日约 0.70 年；之后每年 +1

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report）
BS = {
    "货币资金": 60.3774,                 # 第 52、105 页
    "理财产品(交易性金融资产)": 42.2534,   # 第 105 页（另有衍生金融资产 0.6226）
    "一年内到期定期存款及利息": 7.2104,     # 第 123 页
    "其他流动资产-定期存款": 7.0030,       # 第 124 页
    "其他非流动资产-定期存单": 15.1394,    # 第 138 页
}
RESTRICTED = 10.6513 + 0.0026 + 3.0006 + 2.0360   # 质押给应付票据等，第 20、139 页
DEBT = {
    "短期借款(含内部票据/信用证贴现 8.07)": 18.7644,  # 第 140 页
    "长期借款": 0.9860,
    "一年内到期的非流动负债": 0.3351,
    "租赁负债": 0.1207,
}
DERIV_NET = 0.6226 - 0.7330          # 衍生金融资产 - 交易性金融负债（衍生）
DIV_H1_2026 = 20.3725                # 2026 中期分红 1.6 元/股，2026-10-14 已除息并发放（dividend_20260930）
BUYBACK_SPENT = 0.4045               # 2026-10-15 已回购 56.196 万股（buyback_20261016）
OP_RESERVE = 10.0                    # 经营备付：约 2 周营业成本
NON_OPERATING = 1.7278 + 0.50        # 长期股权投资（创投合伙企业）+ 其他非流动金融资产，按账面

# 营运资金（含受限保证金）：应收票据+账款 26.94、应收款项融资 0.65、预付 0.34、其他应收 4.33（主要出口退税）、
# 存货 38.55、合同资产 0.01、其他流动资产中非现金项 2.11、受限资金 15.69；
# 减 应付票据 46.65、应付账款 50.01、合同负债 6.22、职工薪酬 2.26、应交税费 4.18、其他应付与其他流动负债 0.29
NWC_0630 = (26.94 + 0.65 + 0.34 + 4.33 + 38.55 + 0.01 + 2.11 + RESTRICTED) \
    - (46.65 + 50.01 + 6.22 + 2.26 + 4.18 + 0.29)

# ---------------------------------------------------------------- 已披露与预告
H1_2026_PARENT_NP = 27.1750          # 2026H1_report 第 7 页
NINE_M_RANGE = (42.2, 43.2)          # forecast_20261015 第 1 页
Q3_2026_NP = sum(NINE_M_RANGE) / 2 - H1_2026_PARENT_NP   # 15.53，区间 15.03～16.03
FIN_INCOME_AT_H2 = 0.75              # 下半年税后净利息与理财收益（H1 为 0.79），已含在净现金回报中，剔除
NET_CAPEX_H2 = 5.5 - 1.65            # 下半年资本开支约 5.5、折旧摊销约 1.65（H1 分别 4.92、1.53）
FIN_INCOME_2026_AT = 1.5             # 2026 全年税后净财务收益（正常化归母净利"含净利息"时加回）
# 2026E 报告归母 → 核心口径的桥（税后，亿元）
NONREC_2026E = 1.4798 + 1.18 + 0.50  # 非经常性损益：H1 1.48（2026H1_report 第 8 页）+ Q3 约 1.18（预告净利与扣非中值差）+ Q4 估 0.5
FX_ADDBACK_2026E = 2.6               # 汇兑损失加回：H1 2.30（第 153 页）+ H2 估 0.8，税前约 3.1
WMP_READD_2026E = 0.6                # 理财收益随非经常性剔除后重新计入（"含净利息"口径）

# ---------------------------------------------------------------- 三情景
# n26_op：2026 正常化经营归母净利（剔除净利息、一次性项目与能源冲击带来的超额需求）
# g27：2027 相对 n26_op 的增速；rev27：2027 收入（用于营运资金与利润率展示）
# growth：2028-2036 逐年增速；rr：再投资率（净资本开支/经营净利），前 5 年与后 5 年
# k_nwc：正常营运资金（含受限保证金）/收入；浮存回吐 = k*rev27 - NWC_0630，计入 2027
SCENARIOS = {
    "bear": dict(p=0.30, q4=11.5, n26_op=31.0, g27=-0.02, rev27=160.0,
                 growth=[0.03, 0.03, 0.02, 0.02, 0.02, 0.02, 0.015, 0.015, 0.015],
                 rr=(0.10, 0.08), g_t=0.015, rr_t=0.075, k_nwc=0.02,
                 text="2027 年重演 2023 年式去库存：伊朗冲突溢价消退、渠道消化库存、价格战与电池出口退税取消，"
                      "收入回落至约 160 亿、经营净利率 19%，经营归母净利约 30 亿；之后年增 2～3%，终值增长 1.5%，"
                      "营运资金浮存回吐约 24 亿"),
    "base": dict(p=0.45, q4=14.0, n26_op=44.0, g27=0.05, rev27=215.0,
                 growth=[0.10, 0.08, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025],
                 rr=(0.15, 0.10), g_t=0.025, rr_t=0.10, k_nwc=-0.03,
                 text="2026 核心经营净利约 20% 属冲击性超额需求，2027 年收入约 215 亿（较 2026E 约 228 亿回落 6%），"
                      "经营净利率 21.5%（电池包占比上升、出口退税取消、竞争），经营归母净利约 46 亿；"
                      "2028-2031 年增 10%→5%，终值增长 2.5%，营运资金浮存回吐约 15 亿"),
    "bull": dict(p=0.25, q4=16.3, n26_op=55.0, g27=0.13, rev27=265.0,
                 growth=[0.12, 0.10, 0.08, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03],
                 rr=(0.18, 0.12), g_t=0.025, rr_t=0.10, k_nwc=-0.06,
                 text="能源价格维持高位、工商储与新兴市场持续放量，2026 年水平基本属结构性；2027 年收入约 265 亿、"
                      "经营净利率 23.5%，经营归母净利约 62 亿；2028-2031 年增 12%→6%，终值增长 2.5%"),
}


def adjusted_net_cash():
    cash = sum(BS.values()) - RESTRICTED
    debt = sum(DEBT.values())
    return cash - debt + DERIV_NET - DIV_H1_2026 - BUYBACK_SPENT - OP_RESERVE


def scenario_flows(s):
    """返回 [(t, 现金流)] 列表、终值现金流参数与逐年经营净利。"""
    flows = []
    # 2026 下半年：Q3 预告中值 + Q4 估计 - 净财务收益 - 净资本开支
    oe_h2 = Q3_2026_NP + s["q4"] - FIN_INCOME_AT_H2 - NET_CAPEX_H2
    flows.append((T_H2_2026, oe_h2, "2026H2"))
    np_op = s["n26_op"] * (1 + s["g27"])
    rev = s["rev27"]
    margin = np_op / rev
    path = []
    years = list(range(2027, 2037))
    for i, y in enumerate(years):
        if i > 0:
            g = s["growth"][i - 1]
            np_op *= 1 + g
            new_rev = rev * (1 + g)
            d_nwc = s["k_nwc"] * (new_rev - rev)
            rev = new_rev
        else:
            # 2027：营运资金由 2026-06-30 的 NWC_0630 回到 k*rev27
            d_nwc = s["k_nwc"] * rev - NWC_0630
        rr = s["rr"][0] if y <= 2031 else s["rr"][1]
        oe = np_op * (1 - rr) - d_nwc
        flows.append((T_2027 + i, oe, str(y)))
        path.append((y, np_op, rev, rr, d_nwc, oe))
    np_t = np_op * (1 + s["g_t"])
    oe_t = np_t * (1 - s["rr_t"])
    return flows, oe_t, path, margin


def value(s, r=COE, with_detail=False):
    flows, oe_t, path, margin = scenario_flows(s)
    pv_flows = sum(cf / (1 + r) ** t for t, cf, _ in flows)
    t_last = flows[-1][0]
    tv = oe_t / (r - s["g_t"])
    pv_tv = tv / (1 + r) ** t_last
    nc = adjusted_net_cash() + NON_OPERATING
    equity = nc + pv_flows + pv_tv
    if with_detail:
        return equity, dict(pv_flows=pv_flows, pv_tv=pv_tv, net_cash=nc, tv_share=pv_tv / equity,
                            path=path, margin27=margin, flows=flows)
    return equity


def per_share(s, r=COE):
    return value(s, r) / SHARES


def weighted(r=COE, weights=None):
    if weights is None:
        weights = {k: s["p"] for k, s in SCENARIOS.items()}
    return sum(weights[k] * per_share(s, r) for k, s in SCENARIOS.items())


def reinvestment_stats(s):
    """2027-2031 平均再投资率（净资本开支 + 增长带来的营运资金变化，不含 2027 一次性浮存回吐）与增量回报。"""
    _, _, path, _ = scenario_flows(s)
    first5 = path[:5]
    reinv = []
    for i, (y, np_op, rev, rr, d_nwc, oe) in enumerate(first5):
        nwc_growth = 0.0 if i == 0 else d_nwc
        reinv.append(np_op * rr + nwc_growth)
    rate = sum(reinv) / sum(p[1] for p in first5)
    d_np = first5[-1][1] - first5[0][1]
    inc_ret = d_np / sum(reinv[:4])
    return rate, inc_ret


def shocked(name, factor=1.0, **override):
    """情景敏感性：经营净利整体乘以 factor，或覆盖个别参数。"""
    s = dict(SCENARIOS[name])
    s["n26_op"] *= factor
    s.update(override)
    return per_share(s)


def h_share_dilution(v, new_ratio=0.10, issue_price=0.85 * PRICE, fee=0.03):
    """H 股发行敏感性：按现股本 new_ratio 发新股，发行价 issue_price（元/股），费用率 fee。"""
    return (v * SHARES + issue_price * (1 - fee) * SHARES * new_ratio) / (SHARES * (1 + new_ratio))


def solve(f, lo, hi, target, n=200):
    """二分求 f(x)=target，f 单调。"""
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
    """基准情景现金流（含终值与净现金）使现值等于现价的折现率。"""
    return solve(lambda r: per_share(SCENARIOS["base"], r), 0.04, 0.30, PRICE)


def reverse_dcf():
    """(1) 以基准 2027 经营净利为起点，2028-2036 恒定增速 g（再投资率同基准，终值 2.5%）使 V=现价；
    (2) 以基准 2027 经营净利为起点的永续增长率（再投资率 = g/25%）。"""
    base = SCENARIOS["base"]

    def v_const(g):
        s = dict(base)
        s["growth"] = [g] * 9
        return per_share(s)

    g10 = solve(v_const, -0.10, 0.40, PRICE)

    def v_perp(g):
        nc = adjusted_net_cash() + NON_OPERATING
        np27 = base["n26_op"] * (1 + base["g27"])
        oe27 = np27 * (1 - g / 0.25) - (base["k_nwc"] * base["rev27"] - NWC_0630)
        oe_h2 = Q3_2026_NP + base["q4"] - FIN_INCOME_AT_H2 - NET_CAPEX_H2
        pv = oe_h2 / (1 + COE) ** T_H2_2026
        pv += (np27 * (1 - g / 0.25) / (COE - g)) / (1 + COE) ** (T_2027 - 1) \
            - (base["k_nwc"] * base["rev27"] - NWC_0630) / (1 + COE) ** T_2027
        return (nc + pv) / SHARES

    g_perp = solve(v_perp, -0.05, 0.085, PRICE)

    def v_level(x):
        s = dict(base)
        s["n26_op"] = x
        return per_share(s)

    n26_implied = solve(v_level, 10.0, 120.0, PRICE)
    np27_implied = n26_implied * (1 + base["g27"])
    return g10, g_perp, np27_implied


def multiples():
    base = SCENARIOS["base"]
    np26_rep = H1_2026_PARENT_NP + Q3_2026_NP + base["q4"]
    mcap = PRICE * SHARES
    ttm_q3 = 8.2383 + 11.8789 + 15.2961 + Q3_2026_NP   # 2025Q4 + 2026Q1 + 2026Q2 + 2026Q3E
    ev = mcap - adjusted_net_cash() - NON_OPERATING
    ebit26 = np26_rep / (1 - 0.127) - FIN_INCOME_AT_H2 * 2 / 0.85
    return dict(np26_rep=np26_rep, mcap=mcap, pe26=mcap / np26_rep, pe_ttm=mcap / ttm_q3, ttm_q3=ttm_q3,
                ev=ev, ev_ebit26=ev / ebit26, pb=mcap / 114.8576,
                div_yield_ttm=(10.06 + 16.37 + 20.37) / mcap)


def normalized_np_2026():
    """2026 正常化归母净利（含净利息，剔除一次性项目）= 经营口径 n26_op + 税后净财务收益。"""
    return {k: s["n26_op"] + FIN_INCOME_2026_AT for k, s in SCENARIOS.items()}


def bridge_2026():
    """2026E 报告归母（基准 Q4）→ 剔除一次性后的核心归母 → 各情景周期性超额。"""
    rep = H1_2026_PARENT_NP + Q3_2026_NP + SCENARIOS["base"]["q4"]
    core = rep - NONREC_2026E + FX_ADDBACK_2026E + WMP_READD_2026E
    core_op = core - FIN_INCOME_2026_AT
    excess = {k: core_op - s["n26_op"] for k, s in SCENARIOS.items()}
    return rep, core, core_op, excess


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    nc = adjusted_net_cash()
    print("=== 德业股份 605117 独立估值（价格日 2026-10-19，现价 %.2f 元，股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("现金类合计 %.2f；受限 %.2f；有息负债 %.2f；衍生净额 %.2f；已付中期分红 %.2f；回购 %.2f；经营备付 %.1f"
          % (sum(BS.values()), RESTRICTED, sum(DEBT.values()), DERIV_NET, DIV_H1_2026, BUYBACK_SPENT, OP_RESERVE))
    print("经调整净现金 %.2f 亿（%.2f 元/股）；非经营资产 %.2f 亿；2026-06-30 营运资金（含受限保证金）%.2f 亿"
          % (nc, nc / SHARES, NON_OPERATING, NWC_0630))
    print("三季度归母净利估计 %.2f 亿（预告区间 %.2f～%.2f）"
          % (Q3_2026_NP, NINE_M_RANGE[0] - H1_2026_PARENT_NP, NINE_M_RANGE[1] - H1_2026_PARENT_NP))
    print()
    for name, s in SCENARIOS.items():
        eq, d = value(s, with_detail=True)
        np27 = d["path"][0][1]
        print("[%s] p=%.2f  V=%.2f 元/股（股权价值 %.1f 亿；终值现值占比 %.0f%%）"
              % (name, s["p"], eq / SHARES, eq, d["tv_share"] * 100))
        print("   2026Q4 归母 %.1f；2026 正常化经营净利 %.1f；2027 经营净利 %.1f（收入 %.0f，净利率 %.1f%%）；"
              "浮存回吐 %.1f 亿" % (s["q4"], s["n26_op"], np27, s["rev27"], d["margin27"] * 100,
                               d["path"][0][4]))
        print("   增长路径 2028-2036：" + "，".join("%.1f%%" % (g * 100) for g in s["growth"])
              + "；终值增长 %.1f%%" % (s["g_t"] * 100))
        print("   逐年经营净利：" + "，".join("%d:%.1f" % (y, n) for y, n, *_ in d["path"][:5]) + " …")
        print("   V@8%%=%.2f  V@10%%=%.2f" % (per_share(s, 0.08), per_share(s, 0.10)))
    vw = weighted()
    pv = PRICE / vw
    print()
    print("概率加权 V = %.2f 元/股；P/V = %.3f → %s" % (vw, pv, verdict(pv)))
    print("加权 V @8%% = %.2f；@10%% = %.2f" % (weighted(0.08), weighted(0.10)))
    print("现价隐含回报（基准情景 IRR）= %.2f%%" % (implied_irr() * 100))
    g10, gp, np27_imp = reverse_dcf()
    print("反向 DCF：以基准 2027 经营净利 %.1f 亿为起点，2028-2036 年需年增 %.1f%%（终值 2.5%%）；"
          "或自 2027 起永续增长 %.2f%%；按基准增长路径，现价隐含 2027 经营净利 %.1f 亿"
          % (SCENARIOS["base"]["n26_op"] * (1 + SCENARIOS["base"]["g27"]), g10 * 100, gp * 100, np27_imp))
    m = multiples()
    print("交叉：2026E 归母（基准）%.1f 亿，PE %.1f×；TTM（至 2026Q3E）%.1f 亿，PE %.1f×；PB %.2f×；"
          "EV %.0f 亿，EV/EBIT(2026E) %.1f×；过去 12 个月现金分红收益率 %.1f%%"
          % (m["np26_rep"], m["pe26"], m["ttm_q3"], m["pe_ttm"], m["pb"], m["ev"], m["ev_ebit26"],
             m["div_yield_ttm"] * 100))
    nn = normalized_np_2026()
    rep, core, core_op, excess = bridge_2026()
    print("2026E 归母 %.2f - 非经常性 %.2f + 汇兑损失加回 %.2f + 理财收益 %.2f = 核心 %.2f（经营口径 %.2f）"
          % (rep, NONREC_2026E, FX_ADDBACK_2026E, WMP_READD_2026E, core, core_op))
    print("周期性超额（核心经营 - 正常化经营）：熊 %.1f（%.0f%%）／基准 %.1f（%.0f%%）／牛 %.1f（%.0f%%）"
          % (excess["bear"], excess["bear"] / core_op * 100, excess["base"], excess["base"] / core_op * 100,
             excess["bull"], excess["bull"] / core_op * 100))
    print("2026 正常化归母净利（含净利息，剔除一次性）：熊 %.1f／基准 %.1f／牛 %.1f 亿"
          % (nn["bear"], nn["base"], nn["bull"]))
    for name, s in SCENARIOS.items():
        rate, inc = reinvestment_stats(s)
        print("   %s：2027-2031 平均再投资率 %.1f%%，增量回报 %.0f%%；终值再投资率 %.1f%%（对应 ROIC %.0f%%）"
              % (name, rate * 100, inc * 100, s["rr_t"] * 100, s["g_t"] / s["rr_t"] * 100))
    print("V 不变时分档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    print("--- 证伪触发后的独立 V（元/股）---")
    w_q3 = {"bear": 0.45, "base": 0.40, "bull": 0.15}
    w_bust = {"bear": 0.70, "base": 0.30, "bull": 0.00}
    w_up = {"bear": 0.15, "base": 0.50, "bull": 0.35}
    print("F1/F2 三季报或年报落在熊市路径（权重 0.45/0.40/0.15）：%.2f" % weighted(weights=w_q3))
    print("F3 2027 中报归母 < 17 亿（权重 0.70/0.30/0）：%.2f" % weighted(weights=w_bust))
    m_base = SCENARIOS["base"]["n26_op"] * (1 + SCENARIOS["base"]["g27"]) / SCENARIOS["base"]["rev27"]
    m_bull = SCENARIOS["bull"]["n26_op"] * (1 + SCENARIOS["bull"]["g27"]) / SCENARIOS["bull"]["rev27"]
    v_margin = 0.30 * per_share(SCENARIOS["bear"]) + 0.45 * shocked("base", 0.18 / m_base) \
        + 0.25 * shocked("bull", 0.20 / m_bull)
    print("F4 2027 上半年毛利率 < 30%%（基准净利率 %.1f%%→18%%、牛市 %.1f%%→20%%）：%.2f"
          % (m_base * 100, m_bull * 100, v_margin))
    v_eu = 0.30 * shocked("bear", 0.85) + 0.45 * shocked("base", 0.85) + 0.25 * shocked("bull", 0.85)
    print("F5 欧盟或德国限制中国逆变器接入户用（经营净利 -15%%）：%.2f" % v_eu)
    print("反向证伪 2027 中报归母 ≥ 28 亿（权重 0.15/0.50/0.35）：%.2f" % weighted(weights=w_up))
    print()
    print("--- 其他敏感性 ---")
    print("H 股按现股本 10%% 增发、发行价为 A 股现价 85%%：加权 V %.2f" % h_share_dilution(vw))
    v_tax = 0.30 * shocked("bear", 1 - 1.5 / 30.4) + 0.45 * shocked("base", 1 - 2.0 / 46.2) \
        + 0.25 * shocked("bull", 1 - 2.4 / 62.1)
    print("德业储能高新技术企业资格未续（税率 15%%→25%%，经营净利约 -1.5～-2.4 亿/年）：加权 V %.2f" % v_tax)
    w_sym = {"bear": 0.25, "base": 0.50, "bull": 0.25}
    print("对称权重 0.25/0.50/0.25：加权 V %.2f，P/V %.3f" % (weighted(weights=w_sym),
                                                     PRICE / weighted(weights=w_sym)))


if __name__ == "__main__":
    main()
