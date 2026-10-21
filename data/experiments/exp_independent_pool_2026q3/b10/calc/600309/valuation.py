#!/usr/bin/env python3
"""万华化学（600309）独立估值：OI-291 池内独立审计 b10。

运行：python3 valuation.py
输入全部写在脚本内（金额单位亿元，价格元/股）。来源见正文
companies/600309_万华化学.md 的「来源」一节；页码为 PDF 物理页。

口径要点
- 价格日 2026-10-20，现价 66.90 元，总股本 31.3047 亿股（无回购专户股份，
  2025 年回购的 927.5 万股已于 2025-07-14 注销）。
- 最新定期报告：2026 年中报（三季报预约 2026-10-27）。
- 有息负债按筹资活动负债变动表（2026H1_report 第 135～136 页）重建：
  应付票据 431.76 亿中 408.40 亿列入筹资活动（开票贴现现金计入「取得借款收到的现金」），
  按有息负债处理；另加其他流动负债中的短融 19.11 亿与长期应付款（售后租回等）。
- 经调整净现金为负，按框架用有杠杆口径（净负债按现规模滚动、扣税后利息现值），
  并给出无杠杆（全额扣除）口径与「租赁不计入有息负债」口径作对照。
- 现金流按年中折现：2027 年现金流距价格日 0.696 年；2026 年下半年现金流按 t=0。
"""

import math

PRICE = 66.90
SHARES = 31.3047          # 亿股
MCAP = PRICE * SHARES     # 亿元
COE = 0.09
T0 = 0.696                # 2026-10-20 至 2027-07-01（年）

# ---------------------------------------------------------------- 资产负债表（2026-06-30）
DEBT = {                                  # 亿元
    "短期借款": 604.8696,
    "长期借款（含一年内到期 127.21）": 432.0821 + 127.2143,
    "应付债券（含一年内到期利息 0.87）": 99.50 + 0.8702,
    "短期及超短期融资券（其他流动负债）": 19.1061,
    "租赁负债（含一年内到期 14.08）": 101.5521 + 14.0809,
    "长期应付款（售后租回、专项债、股权收购款，含一年内到期）": 18.1960 + 1.5618 + 0.0022,
    "融资性应付票据（筹资活动负债变动表）": 408.4023,
}
LEASES = 101.5521 + 14.0809
CASH = 444.0563 + 20.0834                 # 货币资金 + 结构性存款（交易性金融资产）
RESTRICTED = 35.9937                      # 受限货币资金（承兑汇票保证金 33.40 等）
TTM_REVENUE = 2316.49
OP_RESERVE = 0.02 * TTM_REVENUE           # 经营备付：TTM 营收的 2%
DIV_PAID_AFTER_BS = 25.3568               # 2026 中期分红 0.81 元/股，9-11 已付
DIV_PAYABLE = 1.0282                      # 应付股利（少数股东）
AVG_RATE = 0.022                          # 有息负债实际平均利率：2025 年 34.14/1544；2026H1 年化 37.2/1713
NONOP_BOOK = 122.3227 + 7.2691            # 长期股权投资 + 其他权益工具投资
NONOP_PARENT_SHARE = 0.95                 # 归母份额（部分联营由非全资子公司持有）
NONOP_PARENT = NONOP_BOOK * NONOP_PARENT_SHARE
LEASE_RATE = 0.035                        # 租赁负债隐含利率（估计）
NET_INT_PL_2026 = 25.0                    # 2026 年损益表净利息（含手续费，估计）
H2_NET_INT = 12.5                         # 2026 年下半年净利息
DA_H2 = 96.0                              # 2026 年下半年折旧摊销
DA_PATH = {2027: 198, 2028: 205, 2029: 211, 2030: 215, 2031: 218}
CIP = 334.6046                            # 在建工程（含工程物资）
WC_RATE = 0.14                            # 经营营运资本 / 营收


def total_debt(include_leases=True):
    d = sum(DEBT.values())
    return d if include_leases else d - LEASES


def adj_net_cash(include_leases=True):
    return (CASH - RESTRICTED - OP_RESERVE - DIV_PAID_AFTER_BS - DIV_PAYABLE
            - total_debt(include_leases))


# ---------------------------------------------------------------- 情景假设
# GP/t：分部毛利 / 销量（元/吨）；vol：正常化销量（万吨）；GP（亿元）= GP/t × vol / 1e4
SCEN = {
    "bear": dict(
        p=0.25, label="熊",
        pu_gpt=2950, pu_vol=640, pc_gpt=250, pc_vol=680, fc_gpt=1350, fc_vol=290,
        other_gp=18.0, other_biz=2.0, tax_add=13.5, opex=92.0, oth_inc=6.0,
        impair=-10.0, nonop=-5.0, assoc=6.0, tax=0.14, m=0.10, h2_parent=72.0,
        k=0.90, exp_capex=[50, 90, 80, 70, 60, 60], ronic_new=0.05, ronic_cip=0.03,
        pu_dvol=20, g_T=0.020, ronic_T=0.07, rev0=2150.0),
    "base": dict(
        p=0.50, label="基准",
        pu_gpt=3450, pu_vol=655, pc_gpt=600, pc_vol=690, fc_gpt=1850, fc_vol=300,
        other_gp=26.0, other_biz=2.0, tax_add=14.5, opex=94.0, oth_inc=6.5,
        impair=-8.0, nonop=-4.0, assoc=8.5, tax=0.155, m=0.115, h2_parent=86.0,
        k=0.80, exp_capex=[40, 70, 60, 50, 40, 40], ronic_new=0.08, ronic_cip=0.06,
        pu_dvol=40, g_T=0.025, ronic_T=0.09, rev0=2350.0),
    "bull": dict(
        p=0.25, label="牛",
        pu_gpt=4100, pu_vol=670, pc_gpt=900, pc_vol=700, fc_gpt=2400, fc_vol=310,
        other_gp=32.0, other_biz=2.0, tax_add=15.5, opex=96.0, oth_inc=7.5,
        impair=-6.0, nonop=-3.0, assoc=10.5, tax=0.165, m=0.125, h2_parent=98.0,
        k=0.70, exp_capex=[40, 60, 50, 40, 40, 40], ronic_new=0.11, ronic_cip=0.09,
        pu_dvol=50, g_T=0.025, ronic_T=0.11, rev0=2550.0),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
CIP_PHASE = {2027: 0.3, 2028: 0.7, 2029: 1.0, 2030: 1.0, 2031: 1.0}
PU_PHASE = {2027: 0.4, 2028: 0.8, 2029: 1.0, 2030: 1.0, 2031: 1.0}


def seg_gp(s):
    pu = s["pu_gpt"] * s["pu_vol"] / 1e4
    pc = s["pc_gpt"] * s["pc_vol"] / 1e4
    fc = s["fc_gpt"] * s["fc_vol"] / 1e4
    return pu, pc, fc, s["other_gp"]


def ebit_ex_assoc(s):
    gp = sum(seg_gp(s)) + s["other_biz"]
    return gp - s["tax_add"] - s["opex"] + s["oth_inc"] + s["impair"] + s["nonop"]


def normalized_parent_np(s):
    """2026 年正常化归母净利：含净利息，剔除一次性；联营收益不再计税。"""
    e = ebit_ex_assoc(s)
    pbt = e + s["assoc"] - NET_INT_PL_2026
    tax = s["tax"] * (pbt - s["assoc"])
    return (pbt - tax) * (1 - s["m"])


def nopat0(s):
    return ebit_ex_assoc(s) * (1 - s["tax"])


def project(s, scale=1.0, lease_cost=0.0):
    """返回 (H2 2026 OE, [(年, NOPAT, OE)], 2032 年 OE)。均为合并口径、息前、不含联营。"""
    n0 = nopat0(s) * scale
    lease_at = lease_cost * (1 - s["tax"])
    # 2026 年下半年（实际估计）
    nopat_h2 = (s["h2_parent"] / (1 - s["m"]) + H2_NET_INT * (1 - s["tax"]) - s["assoc"] / 2) * scale
    oe_h2 = nopat_h2 - lease_at / 2 + (1 - s["k"]) * DA_H2 - s["exp_capex"][0]
    rows = []
    cum_exp = 0.0
    prev_rev = s["rev0"]
    for i, y in enumerate(YEARS):
        cum_exp += s["exp_capex"][i]          # 上一期（含 2026H2）扩张投资，一年后产生回报
        cip_add = CIP * s["ronic_cip"] * CIP_PHASE[y] * scale
        pu_add = s["pu_dvol"] * s["pu_gpt"] / 1e4 * (1 - s["tax"]) * PU_PHASE[y] * scale
        nopat = n0 + cip_add + pu_add + s["ronic_new"] * cum_exp * scale
        rev = s["rev0"] * nopat / n0
        dwc = WC_RATE * (rev - prev_rev)
        prev_rev = rev
        oe = nopat - lease_at + (1 - s["k"]) * DA_PATH[y] - s["exp_capex"][i + 1] - dwc
        rows.append((y, nopat, oe))
    nopat_2032 = rows[-1][1] * (1 + s["g_T"])
    oe_2032 = nopat_2032 * (1 - s["g_T"] / s["ronic_T"]) - lease_at
    return oe_h2, rows, oe_2032


def pv_oe(s, r=COE, scale=1.0, lease_cost=0.0):
    oe_h2, rows, oe_2032 = project(s, scale, lease_cost)
    pv = oe_h2
    for i, (y, _, oe) in enumerate(rows):
        pv += oe / (1 + r) ** (T0 + i)
    tv = oe_2032 / (r - s["g_T"])
    pv += tv / (1 + r) ** (T0 + len(rows) - 1)
    return pv, tv / (1 + r) ** (T0 + len(rows) - 1)


def pv_interest(net_debt, tax, r=COE, rate=AVG_RATE):
    a = net_debt * rate * (1 - tax)
    return a / 2 + a / r * (1 + r) ** (1 - T0)


def equity_value(s, r=COE, levered=True, include_leases=True, scale=1.0, rate=AVG_RATE,
                 extra_debt=0.0):
    nd = -adj_net_cash(include_leases) + extra_debt
    lease_cost = 0.0 if include_leases else LEASES * LEASE_RATE
    pv, _ = pv_oe(s, r, scale, lease_cost)
    if levered:
        core = pv - pv_interest(nd, s["tax"], r, rate)
    else:
        core = pv - nd
    return core * (1 - s["m"]) + NONOP_PARENT


def per_share(s, **kw):
    return equity_value(s, **kw) / SHARES


def weighted(scen=SCEN, **kw):
    return sum(v["p"] * per_share(v, **kw) for v in scen.values())


def solve(f, lo, hi, it=200):
    flo = f(lo)
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s, levered=True):
    return solve(lambda r: equity_value(s, r=r, levered=levered) - MCAP, s["g_T"] + 0.003, 0.40)


def implied_scale(s, levered=True):
    return solve(lambda x: equity_value(s, levered=levered, scale=x) - MCAP, 0.2, 5.0)


def implied_parent_np_from_scale(s, x):
    e = ebit_ex_assoc(s) * x
    pbt = e + s["assoc"] - NET_INT_PL_2026
    return (pbt - s["tax"] * (pbt - s["assoc"])) * (1 - s["m"])


def implied_10y_growth(s, levered=True, g_T=0.025):
    """以基准 2027 年 OE 为起点，2027-2036 年按 g 增长、此后 2.5% 永续，使股权价值等于市值。"""
    _, rows, _ = project(s)
    oe27 = rows[0][2]
    oe_h2, _, _ = project(s)
    nd = -adj_net_cash(True)

    def val(g):
        pv = oe_h2
        oe = oe27
        for i in range(10):
            pv += oe / (1 + COE) ** (T0 + i)
            if i < 9:
                oe *= 1 + g
        tv = oe * (1 + g_T) / (COE - g_T)
        pv += tv / (1 + COE) ** (T0 + 9)
        core = pv - (pv_interest(nd, s["tax"]) if levered else nd)
        return core * (1 - s["m"]) + NONOP_PARENT - MCAP

    return solve(val, -0.20, 0.40)


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def variant(changes_by_scen):
    out = {}
    for k, v in SCEN.items():
        nv = dict(v)
        nv.update(changes_by_scen.get(k, {}))
        out[k] = nv
    return out


def main():
    print("=" * 78)
    print("万华化学（600309）独立估值  价格日 2026-10-20  现价 %.2f 元  股本 %.4f 亿股  市值 %.1f 亿元"
          % (PRICE, SHARES, MCAP))
    print("=" * 78)

    print("\n[1] 有息负债重建（2026-06-30，亿元）")
    for k, v in DEBT.items():
        print("   %-46s %9.2f" % (k, v))
    print("   %-46s %9.2f" % ("合计（含租赁）", total_debt(True)))
    print("   %-46s %9.2f" % ("合计（不含租赁）", total_debt(False)))
    print("   现金类 %.2f − 受限 %.2f − 经营备付 %.2f − 9-11 已付中期分红 %.2f − 应付股利 %.2f"
          % (CASH, RESTRICTED, OP_RESERVE, DIV_PAID_AFTER_BS, DIV_PAYABLE))
    print("   经调整净现金（含租赁）= %.2f ；（租赁不计入）= %.2f" % (adj_net_cash(True), adj_net_cash(False)))
    print("   非经营资产（长投 + 其他权益工具，账面）%.2f，归母按 %.0f%% 计 %.2f"
          % (NONOP_BOOK, NONOP_PARENT_SHARE * 100, NONOP_PARENT))

    print("\n[2] 2026 年正常化损益（亿元）")
    hdr = "   %-6s %7s %7s %7s %7s %8s %8s %9s %8s %8s" % (
        "情景", "聚氨酯GP", "石化GP", "精细GP", "其他GP", "EBIT", "NOPAT0", "归母净利", "ROE", "PE")
    print(hdr)
    for k, s in SCEN.items():
        pu, pc, fc, ot = seg_gp(s)
        npn = normalized_parent_np(s)
        print("   %-6s %7.1f %7.1f %7.1f %7.1f %8.1f %8.1f %9.1f %7.1f%% %7.1fx" % (
            s["label"], pu, pc, fc, ot, ebit_ex_assoc(s), nopat0(s), npn,
            npn / 1135.9622 * 100, MCAP / npn))

    print("\n[3] 所有者收益路径（合并口径、息前、不含联营；亿元）")
    for k, s in SCEN.items():
        oe_h2, rows, oe32 = project(s)
        n0 = nopat0(s)
        path = "  ".join("%d:NOPAT %.1f/OE %.1f" % (y, n, o) for y, n, o in rows)
        print("   %s  2026H2 OE %.1f | %s | 2032 OE %.1f" % (s["label"], oe_h2, path, oe32))
        gs = []
        prev = n0
        for y, n, _ in rows:
            gs.append(n / prev - 1)
            prev = n
        print("        NOPAT 增速 " + " ".join("%d:%.1f%%" % (y, g * 100) for (y, _, _), g in zip(rows, gs))
              + "  终值 g=%.1f%% 增量回报 %.0f%% 终值再投资率 %.1f%%"
              % (s["g_T"] * 100, s["ronic_T"] * 100, s["g_T"] / s["ronic_T"] * 100))
        reinv = [1 - o / n for (_, n, o) in rows]
        print("        再投资率（1−OE/NOPAT）" + " ".join("%d:%.0f%%" % (y, r * 100) for (y, _, _), r in zip(rows, reinv)))

    print("\n[4] 情景估值（元/股）")
    nd_l = -adj_net_cash(True)
    for k, s in SCEN.items():
        pv, pvtv = pv_oe(s)
        pvi = pv_interest(nd_l, s["tax"])
        v_lev = per_share(s)
        v_unl = per_share(s, levered=False)
        v_lev_xl = per_share(s, include_leases=False)
        v_unl_xl = per_share(s, levered=False, include_leases=False)
        print("   %s(p=%.2f)  PV(OE) %.1f（终值占 %.0f%%）  PV(税后利息) %.1f  "
              "有杠杆 V=%.2f  无杠杆 V=%.2f  | 租赁不计入：有杠杆 %.2f 无杠杆 %.2f"
              % (s["label"], s["p"], pv, pvtv / pv * 100, pvi, v_lev, v_unl, v_lev_xl, v_unl_xl))
    vw = weighted()
    vw_unl = weighted(levered=False)
    vw_xl = weighted(include_leases=False)
    vw_unl_xl = weighted(levered=False, include_leases=False)
    print("   加权 V（有杠杆，含租赁，主口径）= %.2f  P/V = %.3f  → %s" % (vw, PRICE / vw, band(PRICE / vw)))
    print("   加权 V（无杠杆全额扣除，含租赁）= %.2f  P/V = %.3f  → %s" % (vw_unl, PRICE / vw_unl, band(PRICE / vw_unl)))
    print("   加权 V（有杠杆，租赁不计入）  = %.2f  P/V = %.3f" % (vw_xl, PRICE / vw_xl))
    print("   加权 V（无杠杆，租赁不计入）  = %.2f  P/V = %.3f" % (vw_unl_xl, PRICE / vw_unl_xl))
    print("   注：无回购专户股份，剔除后口径与上同。")

    print("\n[5] 股权成本敏感性（加权 V，有杠杆）")
    v8 = weighted(r=0.08)
    v10 = weighted(r=0.10)
    print("   8%%: %.2f (P/V %.3f)   9%%: %.2f   10%%: %.2f (P/V %.3f)" % (v8, PRICE / v8, vw, v10, PRICE / v10))
    print("   无杠杆口径：8%%: %.2f   10%%: %.2f" % (weighted(r=0.08, levered=False), weighted(r=0.10, levered=False)))
    print("   利率敏感（基准情景，有杠杆）：3.0%%: %.2f  3.5%%: %.2f"
          % (per_share(SCEN["base"], rate=0.030), per_share(SCEN["base"], rate=0.035)))

    print("\n[6] 隐含回报与反向 DCF")
    irr_l = implied_irr(SCEN["base"])
    irr_u = implied_irr(SCEN["base"], levered=False)
    print("   现价隐含回报（基准情景所有者收益流，有杠杆）= %.2f%%；无杠杆口径 = %.2f%%" % (irr_l * 100, irr_u * 100))
    xs = implied_scale(SCEN["base"])
    xu = implied_scale(SCEN["base"], levered=False)
    print("   现价隐含正常化经营利润倍数：有杠杆 %.3f×（相当于 2026 正常化归母净利 %.1f 亿）；"
          "无杠杆 %.3f×（%.1f 亿）" % (xs, implied_parent_np_from_scale(SCEN["base"], xs),
                                   xu, implied_parent_np_from_scale(SCEN["base"], xu)))
    g10 = implied_10y_growth(SCEN["base"])
    g10u = implied_10y_growth(SCEN["base"], levered=False)
    print("   以基准 2027 年 OE 起算，现价隐含 2027-2036 年 OE 年增速：有杠杆 %.2f%%，无杠杆 %.2f%%（此后 2.5%%）"
          % (g10 * 100, g10u * 100))

    print("\n[7] 交叉验证")
    bvps = 1135.9622 / SHARES
    for k, s in SCEN.items():
        roe = normalized_parent_np(s) / 1135.9622
        pb = (roe - s["g_T"]) / (COE - s["g_T"])
        print("   %s：正常化 ROE %.1f%%，合理 PB=(ROE−g)/(r−g)=%.2f → %.2f 元" % (s["label"], roe * 100, pb, pb * bvps))
    ev = MCAP + (-adj_net_cash(True)) + 129.3309 * PRICE / bvps - NONOP_BOOK
    base = SCEN["base"]
    ebit_b = ebit_ex_assoc(base)
    ttm_ebit_ex = 256.2 - 9.4      # TTM 利润总额 227.08 + 财务费用 29.07 ≈ 256.2；减 TTM 联营收益 9.4
    print("   EV（市值 + 经调整净负债 + 少数股东按 PB 计 − 非经营资产）≈ %.0f 亿；"
          "EV/正常化 EBIT（基准，不含联营）%.1fx；EV/TTM EBIT %.1fx；EV/EBITDA（基准，D&A 190）%.1fx"
          % (ev, ev / ebit_b, ev / ttm_ebit_ex, ev / (ebit_b + 190)))
    print("   股息率（近 12 个月 2.06 元）%.2f%%；近 12 个月无回购" % (2.06 / PRICE * 100))

    print("\n[7b] 稳健性（基准情景单项变动，有杠杆，元/股）")
    b = SCEN["base"]
    checks = [
        ("维持性资本开支 = 折旧（k=1.0）", dict(b, k=1.0)),
        ("在建工程不产生回报（ronic_cip=0）", dict(b, ronic_cip=0.0)),
        ("聚氨酯毛利/吨 3,300", dict(b, pu_gpt=3300)),
        ("扩张投资回报 6%", dict(b, ronic_new=0.06)),
        ("少数股东占比 13%", dict(b, m=0.13)),
    ]
    print("   基准 V = %.2f" % per_share(b))
    for name, sc in checks:
        print("   %-34s V=%.2f" % (name, per_share(sc)))
    print("   应付票据全部按经营性负债（不计入有息负债）：有杠杆 %.2f，无杠杆 %.2f"
          % (per_share(b, extra_debt=-DEBT["融资性应付票据（筹资活动负债变动表）"]),
             per_share(b, levered=False, extra_debt=-DEBT["融资性应付票据（筹资活动负债变动表）"])))

    print("\n[8] 证伪条件触发后的加权 V（有杠杆）")
    fals = [
        ("聚氨酯毛利/吨 < 3,000 元（2027 年报）", variant({
            "base": {"pu_gpt": 3000}, "bull": {"pu_gpt": 3450}})),
        ("石化毛利/吨 < 300 元（2027 年报）", variant({
            "base": {"pc_gpt": 300}, "bull": {"pc_gpt": 600}})),
        ("扩张投资不减：2027 购建长期资产 > 300 亿且回报 ≤ 4%", variant({
            k: {"exp_capex": [v["exp_capex"][0]] + [c + 100 for c in v["exp_capex"][1:]],
                "ronic_new": min(v["ronic_new"], 0.04)} for k, v in SCEN.items()})),
    ]
    for name, sc in fals:
        v = weighted(sc)
        print("   %-44s V=%.2f  P/V=%.3f" % (name, v, PRICE / v))
    v_rate = weighted(rate=0.030)
    print("   %-44s V=%.2f  P/V=%.3f" % ("有息负债平均利率 ≥ 3.0%（2027 年报）", v_rate, PRICE / v_rate))
    v_nd = weighted(extra_debt=1700 + adj_net_cash(True))
    print("   %-44s V=%.2f  P/V=%.3f" % ("经调整净负债升至 1,700 亿（2027 年报）", v_nd, PRICE / v_nd))

    print("\n[9] 汇总")
    print("   熊/基准/牛 V = %.2f / %.2f / %.2f（概率 25/50/25）"
          % tuple(per_share(SCEN[k]) for k in ("bear", "base", "bull")))
    print("   加权 V = %.2f  P/V = %.3f  分档：%s" % (vw, PRICE / vw, band(PRICE / vw)))
    print("   2026 正常化归母净利 熊/基准/牛 = %.1f / %.1f / %.1f 亿"
          % tuple(normalized_parent_np(SCEN[k]) for k in ("bear", "base", "bull")))
    print("   8%%/10%% 股权成本 V = %.2f / %.2f；隐含回报 %.2f%%" % (v8, v10, irr_l * 100))
    print("   V 不变时各档价格：≤%.2f 明显低估；≤%.2f 温和低估；≤%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
