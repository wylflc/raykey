# -*- coding: utf-8 -*-
"""铂科新材（300811）独立估值：分部收入 × 净利率 → 归母净利；所有者收益 = 归母净利 − k × 收入增量。

金额单位亿元，每股为元。运行：python3 valuation.py
输入均写在本脚本内，来源见 companies/300811_铂科新材.md。
"""

PRICE = 68.11                 # 2026-10-20 收盘
SHARES_TOTAL = 4.0783         # 亿股，腾讯行情口径（含回购专户股份）
BUYBACK_CANCEL = 0.01232      # 截至 2026-09-30 回购 123.20 万股，用途为注销
SHARES = SHARES_TOTAL - BUYBACK_CANCEL

COE = 0.09
G_TERM = 0.025
RONIC_TERM = 0.15             # 终值期新增投入回报，再投资率 = g / RONIC
T0 = 72 / 365                 # 2026-10-20 → 2026-12-31

# ---- 资产负债（2026-06-30 中报，及期后回购付现） ----
CASH = 3.2764
TRADING_FA = 0.3015
TTM_REV = 21.25
OP_RESERVE = 0.05 * TTM_REV           # 经营备付：TTM 营收 5%
BUYBACK_PAID = 0.9581                 # 7-1 后回购付现（截至 9-30，不含费用）
BANK_DEBT = 0.7600 + 0.5964 + 0.1373 + 0.0015   # 短借 + 长借 + 一年内到期长借 + 其他流动负债
LEASE = 3.7576 + 0.1957               # 租赁负债 + 一年内到期租赁负债
NET_CASH_ADJ = CASH + TRADING_FA - OP_RESERVE - BUYBACK_PAID - BANK_DEBT - LEASE
NON_OP = 0.8017 + 0.0800              # 长期股权投资 + 其他非流动金融资产（账面）
R_DEBT = 0.035                        # 有息负债（含租赁）实际平均利率
TAX_INT = 0.15

# ---- 2025 年基数（年报 + 2026-04 投资者关系记录：粉芯约 72%、粉末约 3%、电感约 25%） ----
REV25_IND = 4.50
REV25_TRAD = 18.02 - REV25_IND
NI_H1_NORM = 2.343            # 2026H1 归母 2.26 − 非经常 0.023 + 汇兑损失税后 0.110

YEARS = list(range(2027, 2037))

SCEN = {
    "bear": dict(p=0.25, ni26=4.95, trad26=14.6, ind26=9.9,
                 g_trad=[0.06, 0.06, 0.05, 0.05, 0.04],
                 ind=[12.0, 13.0, 13.5, 14.0, 14.5],
                 m_trad=0.195, m_ind=0.15, k=1.15),
    "base": dict(p=0.50, ni26=5.30, trad26=15.0, ind26=10.5,
                 g_trad=[0.10, 0.09, 0.08, 0.07, 0.06],
                 ind=[16.0, 20.5, 24.0, 27.0, 29.0],
                 m_trad=0.215, m_ind=0.20, k=1.00),
    "bull": dict(p=0.25, ni26=5.60, trad26=15.3, ind26=11.2,
                 g_trad=[0.12, 0.11, 0.10, 0.09, 0.08],
                 ind=[20.0, 28.0, 35.0, 41.0, 46.0],
                 m_trad=0.225, m_ind=0.24, k=0.85),
}


def paths(s):
    """返回逐年（2026 及 2027–2036）分部收入、归母净利与所有者收益。"""
    trad, ind = [s["trad26"]], [s["ind26"]]
    for g in s["g_trad"]:
        trad.append(trad[-1] * (1 + g))
    ind += s["ind"]
    # 2032–2036：两分部增速从 2031 年线性降到终值增速
    gt0 = trad[-1] / trad[-2] - 1
    gi0 = ind[-1] / ind[-2] - 1
    for i in range(1, 6):
        trad.append(trad[-1] * (1 + gt0 + (G_TERM - gt0) * i / 5))
        ind.append(ind[-1] * (1 + gi0 + (G_TERM - gi0) * i / 5))
    rev = [a + b for a, b in zip(trad, ind)]
    ni = [s["ni26"]] + [a * s["m_trad"] + b * s["m_ind"] for a, b in zip(trad[1:], ind[1:])]
    rev25 = REV25_TRAD + REV25_IND
    # 2026 下半年：净利 = 全年 − 上半年；再投资按全年收入增量的一半
    oe = [(ni[0] - NI_H1_NORM) - s["k"] * (rev[0] - rev25) * 0.5]
    for i in range(1, len(rev)):
        oe.append(ni[i] - s["k"] * (rev[i] - rev[i - 1]))
    return dict(trad=trad, ind=ind, rev=rev, ni=ni, oe=oe)


def pv_oe(s, coe=COE):
    p = paths(s)
    pv = 0.0
    for i, cf in enumerate(p["oe"]):
        pv += cf / (1 + coe) ** (T0 + i)
    ni_last = p["ni"][-1]
    tv = ni_last * (1 + G_TERM) * (1 - G_TERM / RONIC_TERM) / (coe - G_TERM)
    pv_tv = tv / (1 + coe) ** (T0 + len(p["oe"]) - 1)
    return pv, pv_tv, p


def equity(s, coe=COE, levered=True):
    pv, pv_tv, _ = pv_oe(s, coe)
    # 归母净利已含现有净负债的税后利息：
    # 有杠杆口径 = 经营所有者收益现值（PV + 利息加回现值）− 净负债税后利息现值 + 非经营资产
    int_at = -NET_CASH_ADJ * R_DEBT * (1 - TAX_INT) if NET_CASH_ADJ < 0 else 0.0
    pv_int = int_at / coe
    op_value = pv + pv_tv + pv_int
    if levered:
        return op_value - pv_int + NON_OP
    return op_value + NET_CASH_ADJ + NON_OP


def v_ps(s, coe=COE, levered=True, shares=SHARES):
    return equity(s, coe, levered) / shares


def weighted(coe=COE, levered=True, shares=SHARES):
    return sum(SCEN[k]["p"] * v_ps(SCEN[k], coe, levered, shares) for k in SCEN)


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


def reverse_dcf_cagr(roic=0.21):
    """现价隐含：2026 正常化归母 5.30 起 10 年复合增速 g，再投资 = g / 增量回报，之后同终值规则。"""
    target = PRICE * SHARES - NON_OP

    def val(g):
        ni, pv = 5.30, 0.0
        for i in range(1, 11):
            ni *= 1 + g
            pv += ni * (1 - g / roic) / (1 + COE) ** (T0 + i)
        tv = ni * (1 + G_TERM) * (1 - G_TERM / RONIC_TERM) / (COE - G_TERM)
        return pv + tv / (1 + COE) ** (T0 + 10)
    return solve(val, 0.0, 0.60, target)


def implied_perp_g(roic=0.21):
    """现价隐含永续增速：P = NI27 × (1 − g/roic) / (COE − g)，NI27 = 5.30 × (1+g)。"""
    target = PRICE * SHARES - NON_OP
    return solve(lambda g: 5.30 * (1 + g) * (1 - g / roic) / (COE - g), 0.0, 0.0899, target)


def implied_irr():
    return solve(lambda r: v_ps(SCEN["base"], r), 0.04, 0.20, PRICE)


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print(f"股本（扣拟注销回购）{SHARES:.4f} 亿股；经调整净现金 {NET_CASH_ADJ:.2f} 亿元（为负，主值取有杠杆口径）；"
          f"非经营资产 {NON_OP:.2f}")
    print(f"  明细：现金类 {CASH + TRADING_FA:.2f} − 经营备付 {OP_RESERVE:.2f} − 期后回购 {BUYBACK_PAID:.2f} "
          f"− 银行借款 {BANK_DEBT:.2f} − 租赁 {LEASE:.2f}")
    for k, s in SCEN.items():
        pv, pv_tv, p = pv_oe(s)
        print(f"\n[{k}] p={s['p']:.2f}  V={v_ps(s):.2f}（无杠杆 {v_ps(s, levered=False):.2f}；"
              f"含回购专户股份 {v_ps(s, shares=SHARES_TOTAL):.2f}）  "
              f"显性期现值 {pv:.1f}  终值现值 {pv_tv:.1f}  终值占比 {pv_tv / (pv + pv_tv):.0%}")
        print("  年份     " + " ".join(f"{y:>6}" for y in [2026] + YEARS))
        print("  传统收入 " + " ".join(f"{x:6.1f}" for x in p["trad"]))
        print("  电感收入 " + " ".join(f"{x:6.1f}" for x in p["ind"]))
        print("  归母净利 " + " ".join(f"{x:6.2f}" for x in p["ni"]))
        print("  所有者收益" + " ".join(f"{x:6.2f}" for x in p["oe"]) + "  （2026 列为下半年）")
        g5 = [p["ni"][i] / p["ni"][i - 1] - 1 for i in range(1, 6)]
        rr = sum(s["k"] * (p["rev"][i] - p["rev"][i - 1]) for i in range(1, 6)) / sum(p["ni"][1:6])
        print("  2027–2031 归母增速 " + " ".join(f"{x:.1%}" for x in g5)
              + f"；再投资率 {rr:.0%}；增量回报（净利率/k）{(p['ni'][5] / p['rev'][5]) / s['k']:.1%}")
    vw = weighted()
    print(f"\n加权 V = {vw:.2f}  P/V = {PRICE / vw:.2f}（{band(PRICE / vw)}）")
    print(f"无杠杆口径加权 V = {weighted(levered=False):.2f}  P/V = {PRICE / weighted(levered=False):.2f}")
    print(f"含回购专户股份（4.0783 亿股）加权 V = {weighted(shares=SHARES_TOTAL):.2f}")
    for c in (0.08, 0.10):
        print(f"股权成本 {c:.0%}：加权 V = {weighted(c):.2f}；基准 V = {v_ps(SCEN['base'], c):.2f}")
    print(f"现价隐含回报（基准情景）= {implied_irr():.2%}")
    print(f"反向 DCF：现价隐含 10 年归母复合增速 = {reverse_dcf_cagr():.1%}（增量回报 21%）；"
          f"隐含永续增速 = {implied_perp_g():.2%}")
    print("进入各档的价格（V 不变）：≤0.75 → {:.2f}；0.90 → {:.2f}；1.10 → {:.2f}".format(
        0.75 * vw, 0.90 * vw, 1.10 * vw))
    # 证伪触发后的 V
    vb, vm, vu = (v_ps(SCEN[k]) for k in ("bear", "base", "bull"))
    print(f"证伪 1（三季报偏弱）V = 0.5熊 + 0.5基准 = {0.5 * vb + 0.5 * vm:.2f}")
    print(f"证伪 2/3（电感增速或毛利率失守）V = 熊 = {vb:.2f}")
    print(f"证伪 4（2027 达牛市轨迹）V = 0.4基准 + 0.6牛 = {0.4 * vm + 0.6 * vu:.2f}")
    s_k = dict(SCEN["base"], k=1.15)
    print(f"证伪 5（应收与存货占用升至熊情景 k=1.15）基准 V = {v_ps(s_k):.2f}")

    # 现价需要的芯片电感规模：按牛市情景的利润率与 k，把 2027–2031 电感收入路径同比放大
    def v_scaled(f):
        s = dict(SCEN["bull"], ind=[x * f for x in SCEN["bull"]["ind"]])
        return v_ps(s)
    f = solve(v_scaled, 1.0, 6.0, PRICE)
    print(f"现价需要：牛市利润率与 k 下，2031 年芯片电感收入约 {46.0 * f:.0f} 亿元（牛市路径 × {f:.2f}）")
