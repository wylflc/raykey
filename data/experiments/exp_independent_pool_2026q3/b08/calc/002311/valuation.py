#!/usr/bin/env python3
"""海大集团（002311）独立估值：所有者收益 DCF（有杠杆口径，归母）、反向 DCF、隐含回报与交叉验证。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。价格日 2026-10-20，现价 43.18 元。
输入全部写在本脚本内，出处见注释（文件名指 raw/002311/txt/ 下的公告逐页文本，页码为 PDF 物理页）。
"""

# ---------------------------------------------------------------- 快照与股本
PRICE = 43.18                      # 2026-10-20 收盘，腾讯行情
SHARES_QUOTE = 16.5701             # 亿股，行情口径 = 2026-09-16 登记日总股本 1,657,010,297 股（dividend_20260911_232976 第 1 页）
BUYBACK_TO_CANCEL = 0.00075557     # 亿股，回购专户 75,557 股，2026-08-21 股东会通过注销（buyback_20260822_276187 第 1 页）
SHARES = SHARES_QUOTE - BUYBACK_TO_CANCEL   # 16.5693 亿股：估值股本（拟注销股份扣除后；专户全部注销，故与"剔除专户"口径相同）
# 对照：2026-06-30 资产负债表股本 16.4538 亿股 = 4 月注销 18,367,936 股后的 1,645,382,034 股（buyback_20260424_504814 第 2 页）；
# 7 月起 2024 年期权第二期自主行权新增 11,628,263 股（行权价 27.06→26.91 元），至 9-16 为 1,657,010,297 股。
OPTION_SHARES_EXERCISED = 0.11628263          # 亿股，6-30 之后行权新增
OPTION_PROCEEDS = OPTION_SHARES_EXERCISED * 27.0   # ≈3.14 亿元行权款，资产负债表日后流入，与行权后股本配套加回
OPTIONS_REMAINING = 0.0308                    # 亿股，第二期 14,711,706 份中尚未行权约 308 万份（2026H1_report 第 31、194 页推算），只在正文作稀释对照

# ---------------------------------------------------------------- 2026-06-30 资产负债表（2026H1_report 第 57-59、125-154 页）
CASH = 34.25                # 货币资金
WMP = 31.83                 # 交易性金融资产中的银行理财（第 126 页：理财产品 31.83；衍生金融资产 0.68 与衍生金融负债 1.63 属套保头寸，不计）
RESTRICTED = 2.90           # 受限货币资金（第 149 页：土地复垦/担保保证金、期货账户资金）
ST_LOAN = 36.01             # 短期借款（第 150 页）
LT_LOAN_CURRENT = 0.71      # 一年内到期的长期借款（第 153 页）
LT_LOAN = 1.12              # 长期借款
LEASE = 4.10 + 22.30        # 租赁负债（一年内到期 4.10 + 非流动 22.30）
INTERIM_DIV = 2.49          # 2026 中期分红 2.4854 亿元，2026-09-17 派发（dividend_20260911_232976 第 1 页）
OP_RESERVE = 15.0           # 经营备付：约为 TTM 营收 1,338.8 亿的 1.1%（约 4 天现金成本）
SEASONAL_NWC = 9.1          # 季节性营运资金：6-30 净营运资金 18.7 亿，低于近四个季末均值 27.8 亿，差额视为旺季暂时多出的现金
NON_OPERATING = 2.45        # 其他非流动金融资产（股权投资，收益不在正常化利润中）
DEBT_RATE = 0.040           # 有息负债（含租赁）实际平均利率：2025 年 3.4%，2026H1 年化 4.5%，取 4.0%
TAX_ON_INTEREST = 0.15      # 利息抵税按综合税率约 15%（2025 年 12.3%，2026H1 16.1%）
INT_ADDBACK = 1.3           # 正常化归母净利中含的税后净财务费用（年），用于还原经营口径

GROSS_DEBT = ST_LOAN + LT_LOAN_CURRENT + LT_LOAN + LEASE
NET_CASH_ADJ = (CASH + WMP - RESTRICTED - OP_RESERVE - INTERIM_DIV + OPTION_PROCEEDS
                - SEASONAL_NWC - GROSS_DEBT)

# ---------------------------------------------------------------- 正常化归母净利（2026 年口径，含净利息，剔除一次性）
# 2025 年分部净利（含少数股东，2025_annual_report 第 254 页）：饲料 43.21 + 动保 1.61 + 贸易 0.69 + 其他 8.03 + 抵消 -18.60 = 34.94（非养殖合计）；养殖 10.51
FEED_2025 = 43.2055 + 1.6109 + 0.6873 + 8.0346 - 18.5974
MINORITY_SHARE = 0.06       # 少数股东损益占净利：2025 年 5.8%，2026H1 6.7%

SCEN = {
    # vol: 2026E 饲料外销量 / 2025（2,986 万吨）；margin: 吨利润相对 2025 年的系数；
    # nonhog: 种苗、对虾等非生猪养殖净利；hog: 生猪按长期价格正常化后的净利；
    # h2_np: 2026H2 实际归母净利估计；short27: 2027 年相对正常化路径的周期缺口（鱼粉、猪价）
    "bear": dict(p=0.25, vol=1.050, margin=0.85, nonhog=2.5, hog=-1.0,
                 growth=[0.040, 0.040, 0.035, 0.030, 0.030], g_t=0.020, ronic=0.15,
                 h2_np=12.5, short27=6.0),
    "base": dict(p=0.50, vol=1.068, margin=0.95, nonhog=4.0, hog=3.5,
                 growth=[0.080, 0.075, 0.065, 0.055, 0.045], g_t=0.025, ronic=0.22,
                 h2_np=15.5, short27=4.5),
    "bull": dict(p=0.25, vol=1.080, margin=1.02, nonhog=5.0, hog=7.0,
                 growth=[0.110, 0.100, 0.090, 0.080, 0.070], g_t=0.025, ronic=0.28,
                 h2_np=17.5, short27=1.5),
}
H2_REINVEST = 5.0           # 2026H2 再投资（资本开支超出折旧约 4.5 亿 + 海外营运资金）
YEARS = [2027, 2028, 2029, 2030, 2031]
T_H2 = 0.10                 # 2026H2 现金流折现年数（估值日 2026-10-20）


def normalized_np(s):
    total = FEED_2025 * s["vol"] * s["margin"] + s["nonhog"] + s["hog"]
    return total * (1 - MINORITY_SHARE)


def pv_operating(s, r, growth=None, g_t=None, ronic=None, np0=None):
    """经营口径所有者收益现值（未扣利息、未加非经营资产）。"""
    growth = s["growth"] if growth is None else growth
    g_t = s["g_t"] if g_t is None else g_t
    ronic = s["ronic"] if ronic is None else ronic
    np0 = normalized_np(s) if np0 is None else np0
    nopat = np0 + INT_ADDBACK
    n = len(growth)
    t_mid = [0.70 + k for k in range(n)]   # 年中折现：2027 年距估值日 0.7 年，此后逐年加 1
    path, oe = [], []
    for k, g in enumerate(growth):
        nopat *= 1 + g
        path.append(nopat)
    for k in range(n):
        g_next = growth[k + 1] if k + 1 < n else g_t
        oe.append(path[k] * (1 - g_next / ronic))
    oe[0] -= s["short27"]
    pv = sum(c / (1 + r) ** t for c, t in zip(oe, t_mid))
    oe_tv = path[-1] * (1 + g_t) * (1 - g_t / ronic)
    tv = oe_tv / (r - g_t)
    pv_tv = tv / (1 + r) ** t_mid[-1]
    h2 = (s["h2_np"] + INT_ADDBACK / 2 - H2_REINVEST) / (1 + r) ** T_H2
    return dict(pv=pv + pv_tv + h2, pv_explicit=pv, pv_tv=pv_tv, pv_h2=h2,
                path=path, oe=oe, oe_tv=oe_tv, np0=np0)


def equity_levered(s, r, **kw):
    op = pv_operating(s, r, **kw)
    nd = -NET_CASH_ADJ
    interest_pv = nd * DEBT_RATE * (1 - TAX_ON_INTEREST) / r if nd > 0 else 0.0
    return op["pv"] - interest_pv + NON_OPERATING + (NET_CASH_ADJ if nd <= 0 else 0.0), op


def equity_unlevered(s, r, **kw):
    op = pv_operating(s, r, **kw)
    return op["pv"] + NET_CASH_ADJ + NON_OPERATING, op


def per_share(eq, shares=SHARES):
    return eq / shares


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


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    mcap = PRICE * SHARES
    print("== 股本与资产负债调整 ==")
    print(f"估值股本 {SHARES:.4f} 亿股（行情 {SHARES_QUOTE:.4f} − 拟注销回购 {BUYBACK_TO_CANCEL:.5f}）；市值 {mcap:.1f} 亿元")
    print(f"现金类 {CASH + WMP:.2f}（货币资金 {CASH} + 理财 {WMP}）；有息负债 {GROSS_DEBT:.2f}（银行借款 {ST_LOAN + LT_LOAN_CURRENT + LT_LOAN:.2f} + 租赁 {LEASE:.2f}）")
    print(f"扣：受限 {RESTRICTED}、经营备付 {OP_RESERVE}、已宣派中期股利 {INTERIM_DIV}、季节性营运资金 {SEASONAL_NWC}；加：期权行权款 {OPTION_PROCEEDS:.2f}")
    print(f"经调整净现金（无杠杆口径）net_cash_adj = {NET_CASH_ADJ:.2f} 亿元（为负 → 有杠杆口径）")
    nd = -NET_CASH_ADJ
    print(f"有杠杆口径：净负债 {nd:.2f} × {DEBT_RATE:.1%} × (1−{TAX_ON_INTEREST:.0%}) = 税后利息 {nd * DEBT_RATE * (1 - TAX_ON_INTEREST):.3f} 亿/年，9% 现值 {nd * DEBT_RATE * (1 - TAX_ON_INTEREST) / 0.09:.2f}")
    print()

    print("== 2026 正常化归母净利（亿元）==")
    print(f"2025 非养殖分部净利（含少数股东）{FEED_2025:.2f}；少数股东占比 {MINORITY_SHARE:.0%}")
    for k, s in SCEN.items():
        feed = FEED_2025 * s["vol"] * s["margin"]
        print(f"{k:5s}: 饲料等 {feed:.2f} + 非生猪养殖 {s['nonhog']:.1f} + 生猪 {s['hog']:+.1f} → 归母 {normalized_np(s):.2f}")
    print()

    print("== 三情景 V（9%，有杠杆口径）==")
    res = {}
    for k, s in SCEN.items():
        eq, op = equity_levered(s, 0.09)
        eu, _ = equity_unlevered(s, 0.09)
        v, vu = per_share(eq), per_share(eu)
        res[k] = (v, vu, eq, op)
        tv_share = op["pv_tv"] / op["pv"]
        print(f"{k:5s} p={s['p']:.2f}  V={v:6.2f}  （无杠杆口径 {vu:6.2f}）  股权 {eq:7.1f} 亿  终值占经营现值 {tv_share:.0%}")
        print(f"       正常化归母 {op['np0']:.2f}；经营 NOPAT 路径 " + ", ".join(f"{y}:{x:.1f}" for y, x in zip(YEARS, op['path'])))
        print(f"       所有者收益 " + ", ".join(f"{y}:{x:.1f}" for y, x in zip(YEARS, op['oe'])) + f"；2032 起 {op['oe_tv']:.1f}，2026H2 现值 {op['pv_h2']:.1f}")
        reinv = [(s['growth'][i + 1] if i + 1 < 5 else s['g_t']) / s['ronic'] for i in range(5)]
        print(f"       增长 {s['growth']}，终值增长 {s['g_t']:.1%}，增量回报 {s['ronic']:.0%}，再投资率 2027-2031 " + "/".join(f"{x:.0%}" for x in reinv) + f"（均值 {sum(reinv) / 5:.0%}），终值 {s['g_t'] / s['ronic']:.0%}")
    vw = sum(SCEN[k]["p"] * res[k][0] for k in SCEN)
    vwu = sum(SCEN[k]["p"] * res[k][1] for k in SCEN)
    pv = PRICE / vw
    print(f"加权 V = {vw:.2f} 元（无杠杆口径 {vwu:.2f}）；P/V = {pv:.3f}（无杠杆口径 {PRICE / vwu:.3f}）→ {tier(pv)}")
    print(f"回购专户剔除口径：专户 75,557 股全部拟注销，估值股本已扣除，V 与 P/V 相同")
    dil = (vw * SHARES + OPTIONS_REMAINING * 26.91) / (SHARES + OPTIONS_REMAINING)
    print(f"对照：剩余约 308 万份期权按 26.91 元全部行权，加权 V 变为 {dil:.2f} 元")
    print()

    print("== 股权成本敏感性（加权，有杠杆口径）==")
    for r in (0.08, 0.10):
        v = sum(SCEN[k]["p"] * per_share(equity_levered(SCEN[k], r)[0]) for k in SCEN)
        vb = per_share(equity_levered(SCEN["base"], r)[0])
        print(f"r={r:.0%}: 加权 V = {v:.2f}（基准 {vb:.2f}），P/V = {PRICE / v:.3f}")
    print()

    base = SCEN["base"]
    irr = solve(lambda r: equity_levered(base, r)[0], 0.04, 0.20, mcap)
    print(f"== 现价隐含回报（基准情景现金流，有杠杆口径）== {irr:.2%}")

    # 反向 DCF：10 年等速增长（2027-2036），之后 2.5%，基准正常化利润与增量回报
    def eq_g10(g):
        return equity_levered(base, 0.09, growth=[g] * 10, g_t=0.025)[0]
    g10 = solve(eq_g10, -0.05, 0.25, mcap)
    def eq_perp(g):
        return equity_levered(base, 0.09, growth=[g], g_t=g)[0]
    gp = solve(eq_perp, -0.02, 0.085, mcap)
    print(f"== 反向 DCF == 现价隐含 2027-2036 年所有者收益年增速 {g10:.2%}（之后 2.5%）；或 2027 年起永续增速 {gp:.2%}")
    print()

    print("== 交叉验证 ==")
    ttm_div = 1.10 + 0.15
    bb_2026 = 2.82
    print(f"近 12 个月股息 {ttm_div:.2f} 元 → 股息率 {ttm_div / PRICE:.2%}；加 2026 年回购 {bb_2026} 亿 → 股东回报率 {(ttm_div * SHARES + bb_2026) / mcap:.2%}")
    np_b = normalized_np(base)
    print(f"市值/基准正常化归母 = {mcap / np_b:.1f} 倍；市值/2026E 实际归母（H1 16.11 + H2 {base['h2_np']}）= {mcap / (16.11 + base['h2_np']):.1f} 倍；PB 3.01")
    ev = mcap + (-NET_CASH_ADJ) + 13.55 * 2.0 - NON_OPERATING
    ebit = (np_b / (1 - MINORITY_SHARE)) / (1 - 0.15) + 1.6
    print(f"EV（市值 + 经调整净负债 + 少数股东权益按 2 倍账面 − 非经营资产）= {ev:.0f} 亿；正常化 EBIT ≈ {ebit:.1f} 亿 → EV/EBIT ≈ {ev / ebit:.1f}")
    # 分部加总：海外（海大控股口径）与国内分开
    overseas_np = 12.0
    domestic_np = np_b - overseas_np * (1 - MINORITY_SHARE)
    for pe_o, pe_d in ((15, 14), (20, 16), (25, 18)):
        eq = overseas_np * (1 - MINORITY_SHARE) * pe_o + domestic_np * pe_d + NET_CASH_ADJ + NON_OPERATING
        print(f"分部加总：海外 {overseas_np:.0f} 亿×{pe_o} 倍 + 国内及养殖 {domestic_np:.1f} 亿×{pe_d} 倍 + 净现金 → {eq:.0f} 亿，{eq / SHARES:.1f} 元/股")
    print()

    print("== V 不变时进入各档的价格（加权 V）==")
    print(f"≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")
    print()

    print("== 证伪条件触发后的 V（加权，有杠杆口径）==")
    def weighted_with(mod):
        tot = 0.0
        for k, s in SCEN.items():
            s2 = dict(s)
            s2.update(mod(k, s))
            tot += s["p"] * per_share(equity_levered(s2, 0.09)[0])
        return tot
    f1 = weighted_with(lambda k, s: dict(hog=s["hog"] - 3.5, short27=s["short27"] + 3.0))
    f2 = weighted_with(lambda k, s: dict(short27=s["short27"] + 4.0, margin=s["margin"] - 0.03))
    f3 = weighted_with(lambda k, s: dict(margin=s["margin"] - 0.08))
    f4 = weighted_with(lambda k, s: dict(growth=[g - 0.03 for g in s["growth"]]))
    f5 = weighted_with(lambda k, s: dict(h2_np=s["h2_np"] - 4.0, margin=s["margin"] - 0.04))
    print(f"F1 2027 年 1-9 月全国外三元生猪均价 <12.0 元/kg（生猪正常化 −3.5 亿、2027 缺口 +3 亿）：{f1:.2f}")
    print(f"F2 2027 年 4-6 月秘鲁超级蒸汽鱼粉国内现货仍 >18,000 元/吨（2027 缺口 +4 亿、吨利润 −3%）：{f2:.2f}")
    print(f"F3 2027H1 非养殖分部净利 <14.5 亿或 2026 年末应收 >40 亿且信用减值 >3 亿（吨利润再降 8%）：{f3:.2f}")
    print(f"F4 2027H1 饲料外销量 <1,550 万吨或境外收入增速 <15%（各年增速 −3 个百分点）：{f4:.2f}")
    print(f"F5 2026Q3 单季归母 <8.0 亿（H2 −4 亿、吨利润 −4%）：{f5:.2f}")


if __name__ == "__main__":
    main()
