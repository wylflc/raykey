#!/usr/bin/env python3
"""华明装备（002270）独立估值：分部所有者收益 DCF（有杠杆口径）＋非经营资产。

运行：python3 valuation.py
单位：金额亿元，每股元。输入全部写在脚本内，出处见正文「来源」。
"""

PRICE = 19.00                     # 2026-10-20 收盘
SHARES = 8.96225431               # 总股本（亿股），含回购专户股份；2026H1_report 第 52 页、第 98 页
BUYBACK_SHARES = 0.013283         # 2026-10-16 首次回购 132.83 万股（用于员工持股/股权激励，不注销）
SHARES_EX_BUYBACK = SHARES - BUYBACK_SHARES
COE = 0.09
TAX_SHIELD_RATE = 0.15            # 有息负债利息抵税税率

# ---------- 资产负债表（2026-06-30，2026H1_report 第 58～60、101、138～145、157 页） ----------
CASH = 11.2644                    # 货币资金
RESTRICTED = 1.2838               # 承兑/信用证/保函保证金
DIVIDEND_PAID_OCT = 2.3302        # 2026 中期每 10 股派 2.60 元，10-15 除息，价格日已除息
BUYBACK_CASH = 0.2500             # 10-16 首次回购成交 2,499.81 万元
DEBT = 3.1003 + 1.4991 + 2.9544 + 0.9099   # 短期借款(含国内票据融资2.70)+一年内到期+长期借款+租赁负债
DEBT_LIKE = 0.1095 + 0.0238       # 其他应付款中的股权回购款、应付股利
OP_RESERVE_RATIO = 0.05           # 经营备付：2026E 收入的 5%
REV_2026E = 27.0
OP_RESERVE = OP_RESERVE_RATIO * REV_2026E
NET_CASH_ADJ = CASH - RESTRICTED - OP_RESERVE - DIVIDEND_PAID_OCT - BUYBACK_CASH - DEBT - DEBT_LIKE
DEBT_RATE = 0.022                 # 有息负债实际平均利率：H1 利息费用 0.104 亿×2 ÷ 平均有息负债约 10.3 亿≈2.0%，取 2.2%

# 非经营资产（亿元）：政府土地收储款 1.2881×0.9；汇川农商行股权 0.5541×0.7；联营 0.2695；河南劲风光伏电站（情景值）
NONOP_FIXED = 1.2881 * 0.9 + 0.5541 * 0.7 + 0.2695
PV_PLANT = {"bear": 1.5, "base": 2.2, "bull": 3.2}

MINORITY = 0.012                  # 少数股东损益占比（H1 2026：0.039/3.94）

# ---------- 情景 ----------
# 电力设备：2026E 收入、正常化分部 EBIT 率（未扣股份支付）、增长路径、增量回报
#   分部 EBIT 率推算（未扣股份支付）：2025 年 39.3%，2025H1 40.4%，2025H2 38.5%，2026H1 41.3%，
#   2026H2E 39.4%（2025H2＋0.9 个百分点）→ 2026E 全年约 40.3%，基准取 40%
#   2026E 电力设备收入 23.9 = H1 10.99 + H2E 12.9（出口 H2 2025 4.04 亿×1.35，国内 H2 2025 7.40 亿×1.01）
# 数控及其他：2026E EBIT（未含光伏），增长 2%，增量回报 15%
# 股份支付：正常化每年 0.45 亿（随收入增长），作为经常性成本扣除
SCEN = {
    "bear": dict(p=0.25, pe_rev=23.4, pe_margin=0.36, cnc_ebit=0.15, tax=0.16,
                 growth=[0.04, 0.04, 0.03, 0.03, 0.03], g_term=0.020, ronic=0.30, ronic_term=0.20),
    "base": dict(p=0.50, pe_rev=23.9, pe_margin=0.40, cnc_ebit=0.30, tax=0.155,
                 growth=[0.10, 0.09, 0.08, 0.07, 0.06], g_term=0.025, ronic=0.50, ronic_term=0.30),
    "bull": dict(p=0.25, pe_rev=24.3, pe_margin=0.415, cnc_ebit=0.40, tax=0.15,
                 growth=[0.15, 0.13, 0.12, 0.10, 0.08], g_term=0.025, ronic=0.60, ronic_term=0.35),
}
SBC_NORM = 0.45
CNC_G, CNC_RONIC = 0.02, 0.15
FADE_YEARS = 5                    # 2032～2036 线性衰减到终值增速
T_H2 = 0.10                       # 2026H2 现金流距价格日（已过大半，近似）
T_2027 = 0.70                     # 2027 年中点距 2026-10-20


def scen_inputs(s):
    pe_ebit = s["pe_rev"] * s["pe_margin"] - SBC_NORM
    pretax = pe_ebit + s["cnc_ebit"]
    np_parent = pretax * (1 - s["tax"]) * (1 - MINORITY)
    return pe_ebit, pretax, np_parent


def growth_path(s):
    g = list(s["growth"])
    g_last, g_t = g[-1], s["g_term"]
    for k in range(1, FADE_YEARS + 1):
        g.append(g_last + (g_t - g_last) * k / FADE_YEARS)
    return g                         # 2027..2036


def pv_stream(nopat0, growth, g_term, ronic, ronic_term, r):
    """nopat0 = 2026 正常化 NOPAT（归母）。返回 (2026H2..终值) 现值与终值占比。"""
    pv = 0.0
    # 2026H2：半年 NOPAT，再投资按 2027 增速
    oe_h2 = 0.5 * nopat0 * (1 - growth[0] / ronic)
    pv += oe_h2 / (1 + r) ** T_H2
    nopat = nopat0
    for i, g in enumerate(growth):
        nopat *= 1 + g
        g_next = growth[i + 1] if i + 1 < len(growth) else g_term
        rr = ronic if i < 5 else ronic + (ronic_term - ronic) * (i - 4) / FADE_YEARS
        oe = nopat * (1 - g_next / rr)
        pv += oe / (1 + r) ** (T_2027 + i)
    n = len(growth)
    tv = nopat * (1 + g_term) * (1 - g_term / ronic_term) / (r - g_term)
    pv_tv = tv / (1 + r) ** (T_2027 + n - 1)
    return pv + pv_tv, pv_tv / (pv + pv_tv)


def value(name, r=COE, shares=SHARES, levered=True):
    s = SCEN[name]
    pe_ebit, pretax, np_parent = scen_inputs(s)
    k = (1 - s["tax"]) * (1 - MINORITY)
    pv_pe, tv_share = pv_stream(pe_ebit * k, growth_path(s), s["g_term"], s["ronic"], s["ronic_term"], r)
    pv_cnc, _ = pv_stream(s["cnc_ebit"] * k, [CNC_G] * 10, CNC_G, CNC_RONIC, CNC_RONIC, r)
    ops = pv_pe + pv_cnc
    nonop = NONOP_FIXED + PV_PLANT[name]
    net_debt = -NET_CASH_ADJ
    if levered and net_debt > 0:
        pv_int = net_debt * DEBT_RATE * (1 - TAX_SHIELD_RATE) / r
        eq = ops - pv_int + nonop
    else:
        eq = ops + NET_CASH_ADJ + nonop
    return dict(v=eq / shares, eq=eq, ops=ops, pv_pe=pv_pe, pv_cnc=pv_cnc, tv_share=tv_share,
                np_parent=np_parent, pretax=pretax)


def weighted(r=COE, shares=SHARES, levered=True):
    return sum(SCEN[n]["p"] * value(n, r, shares, levered)["v"] for n in SCEN)


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    return solve(lambda r: value("base", r)["v"], 0.03, 0.30, PRICE)


def reverse_dcf_growth():
    """现价隐含：基准 2026 正常化 NOPAT 起，2027～2036 恒定增速 g、之后 2.5%，基准增量回报。"""
    s = SCEN["base"]
    pe_ebit, _, _ = scen_inputs(s)
    k = (1 - s["tax"]) * (1 - MINORITY)
    pv_cnc, _ = pv_stream(s["cnc_ebit"] * k, [CNC_G] * 10, CNC_G, CNC_RONIC, CNC_RONIC, COE)
    nonop = NONOP_FIXED + PV_PLANT["base"]
    pv_int = -NET_CASH_ADJ * DEBT_RATE * (1 - TAX_SHIELD_RATE) / COE
    target_ops = PRICE * SHARES - nonop + pv_int - pv_cnc

    def f(g):
        return pv_stream(pe_ebit * k, [g] * 10, 0.025, s["ronic"], s["ronic_term"], COE)[0]
    return solve(f, -0.10, 0.30, target_ops)


def reverse_perpetual():
    """现价隐含永续增速：2026 正常化归母所有者收益（基准）按 Gordon 公式。"""
    s = SCEN["base"]
    _, pretax, np_parent = scen_inputs(s)
    nonop = NONOP_FIXED + PV_PLANT["base"]
    pv_int = -NET_CASH_ADJ * DEBT_RATE * (1 - TAX_SHIELD_RATE) / COE
    target = PRICE * SHARES - nonop + pv_int

    def f(g):
        oe = np_parent * (1 + g) * (1 - g / s["ronic_term"])
        return oe / (COE - g)
    return solve(f, -0.05, 0.085, target)


def falsifier_values():
    """证伪条件触发后的独立 V（加权口径不再适用，直接给触发后的单一情景 V）。"""
    out = {}
    base = dict(SCEN["base"])

    def v_with(**kw):
        old = dict(SCEN["base"])
        SCEN["base"].update(kw)
        v = value("base")["v"]
        SCEN["base"].clear(); SCEN["base"].update(old)
        return v
    # F1 海外失速：2026 年报直接+间接出口增速 < 25% 且 2027H1 < 10% → 增速降到 5/5/4/4/3，增量回报 40%
    out["F1_overseas_stall"] = v_with(growth=[0.05, 0.05, 0.04, 0.04, 0.03], ronic=0.40)
    # F2 毛利率下台阶：电力设备毛利率 < 57%（约等于分部 EBIT 率 36.5%），增速不变
    out["F2_margin_step_down"] = v_with(pe_margin=0.365)
    # F3 三季度走弱：2026Q3 单季扣非归母 < 1.9 亿 → 2026E 电力收入 23.3、EBIT 率 39%，2027 增速 7%
    out["F3_q3_weak"] = v_with(pe_rev=23.3, pe_margin=0.39, growth=[0.07, 0.08, 0.07, 0.06, 0.05])
    # F4 折价增发：H 股或定增以 13 元（约 0.75×V）发行 10% 股本，募资净额 97%
    vw = weighted()
    new_sh = 0.10 * SHARES
    out["F4_dilutive_issue"] = (vw * SHARES + new_sh * 13.0 * 0.97) / (SHARES + new_sh)
    return out


def print_path(name="base"):
    """逐年列出电力设备分部归母 NOPAT 与所有者收益（数控另列为常数增长 2%）。"""
    s = SCEN[name]
    pe_ebit, _, _ = scen_inputs(s)
    k = (1 - s["tax"]) * (1 - MINORITY)
    g = growth_path(s)
    nopat = pe_ebit * k
    cnc = s["cnc_ebit"] * k
    print(f"{name} 路径：2026 电力 NOPAT {nopat:.2f}，数控及其他 NOPAT {cnc:.2f}")
    for i, gi in enumerate(g[:5]):
        nopat *= 1 + gi
        cnc *= 1 + CNC_G
        g_next = g[i + 1]
        oe = nopat * (1 - g_next / s["ronic"])
        print(f"  {2027 + i}: 增速 {gi:.1%}，电力 NOPAT {nopat:.2f}，再投资率 {g_next / s['ronic']:.1%}，"
              f"电力所有者收益 {oe:.2f}，数控 NOPAT {cnc:.2f}")
    print(f"  2032～2036 增速由 {g[5]:.1%} 线性降至 {g[9]:.1%}；终值增速 {s['g_term']:.1%}，终值再投资率 {s['g_term'] / s['ronic_term']:.1%}")


def cross_checks():
    mcap = PRICE * SHARES
    print(f"市值 {mcap:.2f} 亿；TTM 归母 7.31 → PE {mcap / 7.31:.1f}×；扣非 6.76 → {mcap / 6.76:.1f}×；PB {mcap / 33.68:.2f}×")
    # 历史 PE（正确股本 8.9623 亿股，2022-03 起；数据包第八节按 2.2725 亿股计算有误）
    for y, close, np_, eq in [(2022, 7.70, 3.59, 33.34), (2023, 14.12, 5.42, 33.50), (2024, 16.89, 6.14, 31.66), (2025, 25.04, 7.10, 31.42)]:
        m = close * SHARES
        print(f"  {y} 年末：市值 {m:.1f} 亿，PE {m / np_:.1f}×，PB {m / eq:.2f}×")
    nonop = NONOP_FIXED + PV_PLANT["base"]
    ev = mcap - NET_CASH_ADJ - nonop
    ebit_ttm = 8.198 - 4.061 + 4.284     # 核心 EBIT（含股份支付）：2025 − 2025H1 + 2026H1
    ebit_norm = SCEN["base"]["pe_rev"] * SCEN["base"]["pe_margin"] - SBC_NORM + SCEN["base"]["cnc_ebit"]
    print(f"EV {ev:.1f} 亿；EV/TTM 核心 EBIT {ev / ebit_ttm:.1f}×；EV/2026 正常化 EBIT {ev / ebit_norm:.1f}×")
    dps = 0.20 + 0.21 + 0.26
    print(f"近 12 个月每股现金分红 {dps:.2f} 元，股息率 {dps / PRICE:.2%}；回购 1.5～2.5 亿/年 → {1.5 / mcap:.2%}～{2.5 / mcap:.2%}（用于员工持股，非注销）")


if __name__ == "__main__":
    print(f"经调整净现金（无杠杆口径）: {NET_CASH_ADJ:.3f} 亿元；经营备付 {OP_RESERVE:.2f}；有息负债 {DEBT:.3f}")
    print(f"非经营资产（固定部分）: {NONOP_FIXED:.3f} 亿元；光伏电站 {PV_PLANT}")
    for n in SCEN:
        d = value(n)
        du = value(n, levered=False)
        print(f"{n:4s} p={SCEN[n]['p']:.2f} 2026 正常化归母 {d['np_parent']:.2f} 亿 | 经营现值 {d['ops']:.1f}"
              f"（电力 {d['pv_pe']:.1f}，数控 {d['pv_cnc']:.1f}，终值占比 {d['tv_share']:.0%}） | "
              f"V(有杠杆) {d['v']:.2f} | V(无杠杆) {du['v']:.2f}")
    vw = weighted()
    print(f"加权 V（有杠杆）: {vw:.2f} 元；P/V = {PRICE / vw:.4f}（分档界 1.10：≤1.10 大致合理）")
    print(f"加权 V（无杠杆）: {weighted(levered=False):.2f} 元；P/V = {PRICE / weighted(levered=False):.3f}")
    vx = weighted(shares=SHARES_EX_BUYBACK)
    print(f"剔除回购专户股份后加权 V: {vx:.2f} 元；P/V = {PRICE / vx:.3f}")
    print(f"股权成本 8%: 加权 V {weighted(0.08):.2f}；10%: 加权 V {weighted(0.10):.2f}")
    print(f"基准情景 V：8% {value('base', 0.08)['v']:.2f}；10% {value('base', 0.10)['v']:.2f}")
    print(f"现价隐含回报（基准现金流）: {implied_irr():.2%}")
    print(f"反向 DCF：现价隐含 2027～2036 年恒定增速 {reverse_dcf_growth():.2%}（之后 2.5%）")
    print(f"反向 DCF：现价隐含永续增速 {reverse_perpetual():.2%}")
    for name, p in [("明显低估上限 0.75", 0.75), ("温和低估上限 0.90", 0.90), ("大致合理上限 1.10", 1.10)]:
        print(f"V 不变时 {name} 对应价格: {vw * p:.2f}")
    print("证伪触发后的 V：", {k: round(v, 2) for k, v in falsifier_values().items()})
    for n in SCEN:
        print_path(n)
    cross_checks()
