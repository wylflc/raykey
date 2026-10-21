#!/usr/bin/env python3
"""三环集团（300408）独立估值：所有者收益 DCF（三情景）、敏感性、隐含回报与反向 DCF。

金额单位亿元，每股为元。运行：python3 valuation.py
输入均写在脚本内，来源见同批 companies/300408_三环集团.md「来源」一节。
"""

# ---------- 市场与股本 ----------
PRICE_A = 92.25                 # 2026-10-20 A 股收盘（腾讯日线）
SHARES = 19.96718571            # 总股本（A 19.16497371 + H 0.80221200），含回购专户股份
TREASURY = 0.24899761           # 回购专户：10-14 为 22,375,061 股，加 10-15 的 130,600 股与 10-16 的 2,394,100 股
H_SHARES = 0.80221200
H_PRICE_HKD = 93.15             # 06951.HK 2026-10-20 收盘（腾讯行情昨收字段，10-21 取）
HKDCNY = 0.86855                # 2026H1 报告外币货币性项目折算汇率（2026H1_report 第 104 页）

# ---------- 经调整净现金（2026-06-30 报表 + 期后已发生现金事项） ----------
CASH = 38.2554154               # 货币资金（含到期超 3 个月的大额存单及定期存款 7.45）
TFA = 32.5656711                # 交易性金融资产（理财）
LT_DEPOSIT = 56.9313763         # 其他非流动资产中到期日一年以上的定期存款及大额存单
RESTRICTED = 0.0001             # 受限货币资金（黄金交易保证金 1 万元）
DEBT = 7.39864054 + 0.249 + 0.04833198 + 0.21237105   # 短借（含已贴现未到期票据 3.45）、长借、一年内到期、租赁负债
OPER_RESERVE = 8.0              # 经营备付：约 1 个月营业成本与费用
H_NET_HKD = 70.46 + 8.794       # H 股募资净额：基础发行约 70.46 亿港元（媒体引公司公告）+ 超额配售约 8.794 亿港元（公告 2026-50）
BUYBACK_POST = 8.94661561 + 10.00 + 0.12497767 + 2.3315223   # 6-30 之后回购：第一期、第二期（约 10 亿）、第三期至 10-16
ESOP_CASH_IN = 0.05 * 57.58     # 员工持股计划受让 500 万股 × 57.58 元（股份已在总股本内）
NON_OPERATING = 0.5747 + 0.0320 # 投资性房地产、其他权益工具投资

H_NET = H_NET_HKD * HKDCNY
NET_CASH_ADJ = (CASH + TFA + LT_DEPOSIT - RESTRICTED - DEBT - OPER_RESERVE
                + H_NET - BUYBACK_POST + ESOP_CASH_IN)

# ---------- 情景（经营 NOPAT，不含利息收入；扣非口径并剔除汇兑与超常减值） ----------
# n0: 2026 正常化经营 NOPAT；h2: 2026H2 经营 NOPAT 估计（实际数，不正常化）
# cyc: 2027 年高于正常化水平的周期性超额 NOPAT（一次性加回，不进入增长基数）
# g: 2027-2031 逐年增速；ronic: 显性期增量回报；ronic_t: 终值期增量回报
SCEN = {
    "bear": dict(p=0.25, n0=31.0, h2=20.5, cyc=0.0, g=[-0.05, 0.10, 0.10, 0.08, 0.06], ronic=0.18, ronic_t=0.15,
                 assumptions="MLCC 涨价周期 2026 见顶、2027 回落；正常化收入约 125 亿、毛利率 41%；AI 光通信与 SOFC 增速放缓；增量回报 18%"),
    "base": dict(p=0.50, n0=37.5, h2=22.8, cyc=5.0, g=[0.22, 0.17, 0.13, 0.09, 0.06], ronic=0.28, ronic_t=0.20,
                 assumptions="正常化收入约 140 亿、毛利率 42.8%、经营 NOPAT 率 26.8%；2027-2031 增速 22/17/13/9/6%；2028 年员工持股营收目标 260 亿晚约 3 年达成；增量回报 28%"),
    "bull": dict(p=0.25, n0=41.5, h2=24.5, cyc=8.0, g=[0.33, 0.24, 0.15, 0.10, 0.07], ronic=0.32, ronic_t=0.22,
                 assumptions="2026 年运行率即常态（毛利率约 44.5%）；AI 服务器 MLCC 份额突破、光通信与 SOFC 放量，2028 营收约 250 亿接近员工持股目标；增量回报 32%"),
}
TERMINAL_G = 0.025
INTEREST_YIELD = 0.016          # 净现金税前收益率（用于正常化归母净利，不进入 DCF）
TAX = 0.13                      # 2026H1 实际所得税率 13.1%
T_H2 = 0.10                     # 2026H2 现金流折现时点（年）
T_2027 = 0.70                   # 2027 年年中距 2026-10-20 的年数
T_TV = 5.20                     # 2031 年末


def path(s):
    n = [s["n0"]]
    for g in s["g"]:
        n.append(n[-1] * (1 + g))
    return n                     # [2026, 2027, ..., 2031]


def flows(s):
    """返回 (2026H2 所有者收益, [2027..2031] 所有者收益, 2032 所有者收益, NOPAT 路径)。"""
    n = path(s)
    n2032 = n[-1] * (1 + TERMINAL_G)
    reinv_2026 = max(n[1] - n[0], 0.0) / s["ronic"]
    oe_h2 = s["h2"] - 0.5 * reinv_2026
    oe = []
    for i in range(1, 6):                       # 2027..2031
        nxt = n[i + 1] if i + 1 < len(n) else n2032
        r = s["ronic"] if i + 1 < len(n) else s["ronic_t"]
        oe.append(n[i] - max(nxt - n[i], 0.0) / r)
    oe[0] += s.get("cyc", 0.0)
    oe_2032 = n2032 * (1 - TERMINAL_G / s["ronic_t"])
    return oe_h2, oe, oe_2032, n


def equity_value(s, r, shares=SHARES):
    oe_h2, oe, oe_2032, _ = flows(s)
    pv = oe_h2 / (1 + r) ** T_H2
    pv += sum(x / (1 + r) ** (T_2027 + i) for i, x in enumerate(oe))
    tv = oe_2032 / (r - TERMINAL_G)
    pv_tv = tv / (1 + r) ** T_TV
    eq = pv + pv_tv + NET_CASH_ADJ + NON_OPERATING
    return eq / shares, pv_tv / (pv + pv_tv)


def weighted(r, shares=SHARES, probs=None):
    probs = probs or {k: v["p"] for k, v in SCEN.items()}
    return sum(probs[k] * equity_value(SCEN[k], r, shares)[0] for k in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    s = SCEN["base"]
    return solve(lambda r: equity_value(s, r)[0], 0.03, 0.20, PRICE_A)


def reverse_dcf_10y():
    """现价隐含：2027-2036 年经营 NOPAT 恒定增速 g（自基准 n0、增量回报 28%），其后 2.5% 永续、增量回报 20%。"""
    s = SCEN["base"]

    def v(g):
        r = 0.09
        n = [s["n0"] * (1 + g) ** k for k in range(0, 12)]   # 2026..2037
        pv = (s["h2"] - 0.5 * (n[1] - n[0]) / s["ronic"]) / (1 + r) ** T_H2
        for i in range(1, 11):                               # 2027..2036
            ro = s["ronic"] if i < 10 else s["ronic_t"]
            nxt = n[i + 1] if i < 10 else n[i] * (1 + TERMINAL_G)
            pv += (n[i] - (nxt - n[i]) / ro) / (1 + r) ** (T_2027 + i - 1)
        oe_t = n[10] * (1 + TERMINAL_G) * (1 - TERMINAL_G / s["ronic_t"])
        pv += oe_t / (r - TERMINAL_G) / (1 + r) ** (T_TV + 5)
        return (pv + NET_CASH_ADJ + NON_OPERATING) / SHARES
    return solve(v, 0.0, 0.6, PRICE_A)


def reverse_dcf_perp():
    """现价隐含永续增速：以基准 2027 经营 NOPAT 为起点、增量回报 20%，EV = NOPAT×(1-g/20%)/(9%-g)。"""
    s = SCEN["base"]
    n27 = path(s)[1]
    ev = PRICE_A * SHARES - NET_CASH_ADJ - NON_OPERATING
    return solve(lambda g: n27 * (1 - g / s["ronic_t"]) / (0.09 - g), 0.0, 0.0899, ev)


def normalized_np_2026(k):
    return SCEN[k]["n0"] + NET_CASH_ADJ * INTEREST_YIELD * (1 - TAX)


def main():
    print(f"H 股募资净额 {H_NET:.2f} 亿元；6-30 后回购 {BUYBACK_POST:.2f} 亿元")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} 亿元（每股 {NET_CASH_ADJ / SHARES:.2f} 元）；非经营资产 {NON_OPERATING:.2f}")
    res = {}
    for k, s in SCEN.items():
        v, tvshare = equity_value(s, 0.09)
        oe_h2, oe, oe_2032, n = flows(s)
        res[k] = v
        print(f"[{k}] p={s['p']:.2f} V={v:.2f} 元  终值占比 {tvshare:.1%}  "
              f"NOPAT 2026-2031: {', '.join(f'{x:.1f}' for x in n)}  "
              f"所有者收益 2026H2={oe_h2:.1f}; 2027-2031: {', '.join(f'{x:.1f}' for x in oe)}; 2032={oe_2032:.1f}  "
              f"再投资率(2027)={1 - oe[0] / n[1]:.0%}")
    vw = weighted(0.09)
    print(f"加权 V = {vw:.2f} 元；P/V = {PRICE_A / vw:.2f}")
    vw_ex = weighted(0.09, SHARES - TREASURY)
    print(f"剔除回购专户股份（{SHARES - TREASURY:.4f} 亿股）：加权 V = {vw_ex:.2f} 元；P/V = {PRICE_A / vw_ex:.2f}")
    h_cny = H_PRICE_HKD * HKDCNY
    print(f"H 股 {H_PRICE_HKD} 港元 ≈ {h_cny:.2f} 元；H 股 P/V = {h_cny / vw:.2f}；A/H 溢价 {PRICE_A / h_cny - 1:.1%}")
    print(f"市值（A 价×A 股 + H 价×H 股）= {PRICE_A * (SHARES - H_SHARES) + h_cny * H_SHARES:.1f} 亿元；A 价×总股本 = {PRICE_A * SHARES:.1f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}；10%：{weighted(0.10):.2f}")
    for k in SCEN:
        print(f"   {k}: 8% {equity_value(SCEN[k], 0.08)[0]:.2f} / 10% {equity_value(SCEN[k], 0.10)[0]:.2f}")
    print(f"现价隐含回报（基准情景）= {implied_irr():.2%}")
    hi = dict(SCEN["bull"], ronic=0.45, ronic_t=0.30)
    print(f"高回报敏感性（牛市增速、增量回报 45%／终值 30%）V = {equity_value(hi, 0.09)[0]:.2f}")
    print(f"反向 DCF：10 年经营 NOPAT 恒定增速 {reverse_dcf_10y():.1%}；或永续增速 {reverse_dcf_perp():.2%}")
    for k in SCEN:
        print(f"2026 正常化归母净利（含净利息）[{k}] = {normalized_np_2026(k):.1f} 亿元")
    print("分档价格（V 不变）：≤{:.2f} 明显低估；{:.2f}～{:.2f} 温和低估；{:.2f}～{:.2f} 大致合理；>{:.2f} 偏贵".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    # 证伪触发后的 V
    f1 = weighted(0.09, probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    f2 = res["bear"]
    f3 = weighted(0.09, probs={"bear": 0.05, "base": 0.35, "bull": 0.60})
    f4 = weighted(0.09, probs={"bear": 0.40, "base": 0.50, "bull": 0.10})
    print(f"证伪 1（三季报营收<35 亿或毛利率<42%）V = {f1:.2f}")
    print(f"证伪 2（2027H1 营收同比<5% 且毛利率<41%）V = {f2:.2f}")
    print(f"证伪 3（2027 扣非≥60 亿且营收≥200 亿、经营现金流/净利≥0.8）V = {f3:.2f}")
    print(f"证伪 4（2026 年报扣非<38 亿或经营现金流/净利<0.6）V = {f4:.2f}")


if __name__ == "__main__":
    main()
