"""马应龙（600993）独立估值：所有者收益 DCF、反向 DCF、隐含回报、交叉验证与证伪情景。

运行：python3 valuation.py
金额单位亿元，每股价值单位元/股。输入全部写在脚本内，出处见同批
companies/600993_马应龙.md「来源」一节（页码为 PDF 物理页）。
"""

PRICE = 24.91            # 2026-10-19 收盘，A 股未复权（brief.md）
SHARES = 4.3105          # 亿股，腾讯行情口径；2026H1_report 第 34 页股本 431,053,891 股
TREASURY = 0.0           # 无库存股、无回购专户股份（2026H1_report 第 34 页「减：库存股」为空）
VAL_DATE = 2026 + 291 / 365   # 2026-10-19
TAX = 0.15               # 母公司高新技术企业税率，利息与理财收益集中在母公司
COE = 0.09

# ---------------------------------------------------------------- 1 核心经营利润
# 核心经营利润 = 扣非归母 −（存款类利息收入 − 利息费用）×(1−15%)。
# 理财公允价值与处置收益已被公司列为非经常性损益，不在扣非内；
# 银行存款、定期存单与大额存单利息在扣非内，这里剔除，净现金另行加回。
def core_np(deduct_np, deposit_interest, interest_expense):
    return deduct_np - (deposit_interest - interest_expense) * (1 - TAX)

# 2025：扣非 5.637；财务费用利息收入 0.404、大额存单持有收益 0.067、债权利息 0.0045；利息费用 0.074
CORE_2025 = core_np(5.637, 0.404 + 0.067 + 0.0045, 0.074)
# 2025H1：扣非 3.216；利息收入 0.232；利息费用 0.035
CORE_H1_2025 = core_np(3.216, 0.232, 0.035)
# 2026H1：扣非 3.424；利息收入 0.083、大额存单持有收益 0.069、债权利息 0.0006；利息费用 0.021
CORE_H1_2026 = core_np(3.424, 0.083 + 0.069 + 0.0006, 0.021)
CORE_H2_2025 = CORE_2025 - CORE_H1_2025
REVENUE_2025, REVENUE_TTM = 38.67, 39.29
CORE_TTM = CORE_H2_2025 + CORE_H1_2026
# 历史中枢（东财 F10 年度：营收、扣非、财务费用利息收入、利息费用；只扣财务费用口径利息）
HIST = {2019: (27.05, 3.208, 0.169, 0.051), 2020: (27.92, 3.271, 0.304, 0.070),
        2021: (33.85, 4.317, 0.466, 0.102), 2022: (35.32, 4.613, 0.586, 0.117),
        2023: (31.37, 3.524, 0.610, 0.169), 2024: (37.28, 5.109, 0.652, 0.074)}
HIST_MARGIN = {y: core_np(d, i, e) / rev for y, (rev, d, i, e) in HIST.items()}
CENTRE = sum(HIST_MARGIN.values()) / len(HIST_MARGIN)

# ---------------------------------------------------------------- 2 经调整净现金（2026-06-30）
CASH = 6.312             # 货币资金
WMP = 18.458             # 交易性金融资产：券商理财 16.534、银行理财 1.924
CD_CURRENT = 0.300       # 其他流动资产中的一年内到期大额存单
CD_NONCURRENT = 8.670    # 其他非流动资产中的银行大额存单
GROSS_FIN = CASH + WMP + CD_CURRENT + CD_NONCURRENT
RESTRICTED = 0.189       # 受限货币资金（承兑保证金、电商平台保证金）
DEBT = 0.110 + 0.215 + 0.610   # 短期借款 + 一年内到期租赁负债 + 租赁负债
DIV_PAYABLE = 3.039      # 应付股利；2025 年度 0.70 元/股共 3.017 亿已于 2026-08-05 发放
RESERVE = 4.0            # 经营备付：约 10% 年收入、1.5 个月付现成本
NET_CASH_ADJ = GROSS_FIN - RESTRICTED - DEBT - DIV_PAYABLE - RESERVE
LT_EQUITY_INV = 1.362    # 长期股权投资账面（宝利通 0.931、疌泉建龙基金 0.335 等）
NON_OP = round(LT_EQUITY_INV * 0.7, 3)   # 打七折计入
INTEREST_BASE = 30.0     # 2026 年计息金融资产净额均值（扣有息负债与已宣派股利）

# ---------------------------------------------------------------- 3 情景
# core26：2026 核心经营利润；growth：2027-2031 核心经营利润增速；
# roic：增量投入资本回报（再投资率 = max(g/roic, rr_floor)）；
# g_t / roic_t：终值增长与终值期再投资回报；yld：正常化税前现金收益率；p：概率。
SCEN = {
    "bear": dict(core26=5.40, growth=[-0.04, -0.03, -0.02, -0.01, 0.00], roic=0.35, rr_floor=0.03,
                 g_t=0.0, roic_t=0.30, yld=0.017, p=0.25),
    "base": dict(core26=5.55, growth=[0.02, 0.03, 0.035, 0.035, 0.03], roic=0.35, rr_floor=0.03,
                 g_t=0.02, roic_t=0.30, yld=0.020, p=0.50),
    "bull": dict(core26=5.70, growth=[0.06, 0.07, 0.07, 0.06, 0.05], roic=0.35, rr_floor=0.03,
                 g_t=0.025, roic_t=0.30, yld=0.022, p=0.25),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def rr(g, roic, floor):
    return max(g / roic, floor)


def dcf(s, r, cash_mult=1.0, net_cash=None, detail=False):
    """返回每股价值。H2 2026 所有者收益按 t≈0 计；2027-2031 按年中折现；终值接在 2031 年中。"""
    nc = NET_CASH_ADJ if net_cash is None else net_cash
    h2 = s["core26"] - CORE_H1_2026
    pv_h2 = h2 * (1 - rr(s["growth"][0], s["roic"], s["rr_floor"]))
    c, pv_explicit, rows = s["core26"], 0.0, []
    for y, g in zip(YEARS, s["growth"]):
        c *= 1 + g
        oe = c * (1 - rr(g, s["roic"], s["rr_floor"]))
        t = (y + 0.5) - VAL_DATE
        pv_explicit += oe / (1 + r) ** t
        rows.append((y, g, c, oe))
    oe_next = c * (1 + s["g_t"]) * (1 - max(s["g_t"] / s["roic_t"], 0.0))
    t_last = (YEARS[-1] + 0.5) - VAL_DATE
    pv_tv = oe_next / (r - s["g_t"]) / (1 + r) ** t_last
    equity = pv_h2 + pv_explicit + pv_tv + nc * cash_mult + NON_OP
    v = equity / (SHARES - TREASURY)
    if detail:
        return v, dict(pv_h2=pv_h2, pv_explicit=pv_explicit, pv_tv=pv_tv, equity=equity, rows=rows,
                       tv_share_of_operating=pv_tv / (pv_h2 + pv_explicit + pv_tv))
    return v


def weighted(r=COE, probs=None, **kw):
    probs = probs or {k: s["p"] for k, s in SCEN.items()}
    vals = {k: dcf(SCEN[k], r, **kw) for k in SCEN}
    return sum(vals[k] * probs[k] for k in SCEN), vals


def solve(f, lo, hi, target, n=200):
    """二分求解 f(x)=target（f 单调）。"""
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


def normalized_np_2026(s):
    """2026 正常化归母净利：核心经营利润 + 计息资产税后正常化收益（剔除补助与一次性项目）。"""
    return s["core26"] + INTEREST_BASE * s["yld"] * (1 - TAX)


def main():
    print("== 1 核心经营利润（扣非 − 税后存款类利息净额）")
    print(f"2025 {CORE_2025:.3f}（核心利润率 {CORE_2025 / REVENUE_2025:.1%}）；2025H1 {CORE_H1_2025:.3f}；"
          f"2026H1 {CORE_H1_2026:.3f}（同比 {CORE_H1_2026 / CORE_H1_2025 - 1:+.1%}）；2025H2 {CORE_H2_2025:.3f}；"
          f"TTM {CORE_TTM:.3f}（{CORE_TTM / REVENUE_TTM:.1%}）")
    print("历史核心利润率 " + "，".join(f"{y}:{m:.1%}" for y, m in HIST_MARGIN.items())
          + f"；2019-2024 中枢 {CENTRE:.1%}；TTM 高出 {CORE_TTM / REVENUE_TTM - CENTRE:+.1%}"
          f"（≈{(CORE_TTM / REVENUE_TTM - CENTRE) * REVENUE_TTM:.2f} 亿）")

    print("\n== 2 经调整净现金（2026-06-30）")
    print(f"现金与金融资产 {GROSS_FIN:.3f} − 受限 {RESTRICTED} − 有息与租赁负债 {DEBT:.3f} − 已宣派股利 {DIV_PAYABLE}"
          f" − 经营备付 {RESERVE} = {NET_CASH_ADJ:.2f}；长期股权投资七折 {NON_OP:.2f}；"
          f"合计每股 {(NET_CASH_ADJ + NON_OP) / SHARES:.2f} 元")

    print("\n== 3 三情景（股权成本 9%）")
    for k, s in SCEN.items():
        v, d = dcf(s, COE, detail=True)
        path = "，".join(f"{y}:{g:+.1%}/核心{c:.2f}/OE{oe:.2f}" for y, g, c, oe in d["rows"])
        print(f"{k}: V={v:.2f}  概率 {s['p']:.0%}  2026 核心 {s['core26']:.2f}  {path}  终值 g={s['g_t']:.1%}"
              f"  终值占经营价值 {d['tv_share_of_operating']:.0%}  2026 正常化归母净利 {normalized_np_2026(s):.2f}")
    vw, vals = weighted()
    pv = PRICE / vw
    b = SCEN["base"]
    rr_avg = sum(rr(g, b["roic"], b["rr_floor"]) for g in b["growth"]) / len(b["growth"])
    print(f"基准再投资率均值 {rr_avg:.1%}，增量回报 {b['roic']:.0%}；终值期再投资率 {b['g_t'] / b['roic_t']:.1%}")
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.3f} → {verdict(pv)}")
    print(f"剔除回购专户股份后 V 与 P/V：无回购专户股份，同上（{vw:.2f}、{pv:.3f}）")
    print(f"V 不变时进入各档的价格：明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")

    print("\n== 4 股权成本敏感性")
    for r in (0.08, 0.09, 0.10):
        w, vv = weighted(r)
        print(f"r={r:.0%}: 熊 {vv['bear']:.2f} 基 {vv['base']:.2f} 牛 {vv['bull']:.2f} 加权 {w:.2f} P/V {PRICE / w:.3f}")

    print("\n== 5 现价隐含回报与反向 DCF")
    irr_base = solve(lambda r: dcf(SCEN["base"], r), 0.05, 0.20, PRICE)
    irr_w = solve(lambda r: weighted(r)[0], 0.05, 0.20, PRICE)
    print(f"基准情景所有者收益流（含终值与净现金）的隐含回报 = {irr_base:.2%}；三情景加权口径 = {irr_w:.2%}")
    base = SCEN["base"]

    def v_const_growth(g):
        s = dict(base, growth=[g] * 5)
        # 10 年同速：2027-2031 显式期 + 2032-2036 以同速并入终值前的第二段
        r = COE
        h2 = s["core26"] - CORE_H1_2026
        pv_ = h2 * (1 - rr(g, s["roic"], s["rr_floor"]))
        c = s["core26"]
        for i in range(10):
            c *= 1 + g
            pv_ += c * (1 - rr(g, s["roic"], s["rr_floor"])) / (1 + r) ** ((2027 + i + 0.5) - VAL_DATE)
        oe_next = c * 1.02 * (1 - 0.02 / 0.30)
        pv_ += oe_next / (r - 0.02) / (1 + r) ** ((2036 + 0.5) - VAL_DATE)
        return (pv_ + NET_CASH_ADJ + NON_OP) / SHARES
    g10 = solve(v_const_growth, -0.10, 0.15, PRICE)
    ev_implied = PRICE * SHARES - NET_CASH_ADJ - NON_OP

    def ev_perpetual(g):
        # H2 2026 所有者收益 + 自 2027 年中起按 g 永续增长的所有者收益（再投资率 g/30%）
        keep = 1 - max(g / 0.30, 0.0)
        h2 = (base["core26"] - CORE_H1_2026) * keep
        oe27 = base["core26"] * (1 + g) * keep
        return h2 + oe27 / (COE - g) / (1 + COE) ** ((2027 + 0.5) - VAL_DATE)
    g_perp = solve(ev_perpetual, -0.05, 0.08, ev_implied)
    print(f"现价隐含经营价值（市值 − 净现金 − 非经营资产）= {ev_implied:.2f} 亿")
    print(f"反向 DCF：核心经营利润 2027-2036 年均增速 {g10:+.2%} 后接 2% 永续，可使 V = 现价；"
          f"或以 2026 核心 {base['core26']} 为基的永续增速 {g_perp:+.2%}（再投资回报 30%）")

    print("\n== 6 交叉验证")
    dps = 0.70
    eps_26 = 5.98 / SHARES    # 2026E 报告口径归母净利（中报 3.63 + 下半年估 2.35）
    mcap = PRICE * SHARES
    minority_mv = 4.0         # 大健康 51.52% 少数股东权益的估计市值
    core_pbt_26 = base["core26"] / (1 - TAX) / (1 - 0.04)
    ev = mcap - NET_CASH_ADJ - NON_OP + minority_mv
    fcf_ttm = 7.20 - 0.82 - 0.47 - 0.23  # 经营现金流 − 购建长期资产 − 租赁等筹资付现 − 子公司付少数股东股利
    print(f"股息率 {dps / PRICE:.2%}（无回购）；2026E 报告口径 PE {PRICE / eps_26:.1f}×；"
          f"剔现金 PE（经营价值/2026 核心）{ev_implied / base['core26']:.1f}×；PB {mcap / 44.40:.2f}×")
    print(f"EV（含少数股东估值 {minority_mv}）= {ev:.1f} 亿；2026E 核心经营税前利润约 {core_pbt_26:.2f} 亿；EV/EBIT {ev / core_pbt_26:.1f}×")
    print(f"TTM 归母自由现金流约 {fcf_ttm:.2f} 亿：市值收益率 {fcf_ttm / mcap:.1%}，经营价值收益率 {fcf_ttm / ev_implied:.1%}")
    for pe in (18.0, 20.4, 21.3):
        print(f"  2026E 报告口径归母 5.98 × {pe}× = {5.98 * pe / SHARES:.2f} 元/股")
    print(f"  同业 PE(TTM) 中值 17.86× × TTM 归母 6.01 = {17.86 * 6.01 / SHARES:.2f} 元/股")
    print(f"  现金按八折计：加权 V = {weighted(cash_mult=0.8)[0]:.2f}（−{vw - weighted(cash_mult=0.8)[0]:.2f}）")

    print("\n== 7 证伪情景下的独立 V")
    # F1 2026 年报：治痔类毛利率 < 70% 且治痔收入同比 < 0 → 概率移向熊市
    v_f1 = weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})[0]
    # F2 三季报：Q3 单季扣非 < 1.30 亿 → 2026 核心降至 5.40，基准增速各年 −1 个百分点
    f2 = {k: dict(s) for k, s in SCEN.items()}
    f2["base"] = dict(f2["base"], core26=5.40, growth=[g - 0.01 for g in SCEN["base"]["growth"]])
    f2["bull"] = dict(f2["bull"], core26=5.55)
    v_f2 = sum(dcf(f2[k], COE) * SCEN[k]["p"] for k in SCEN)
    # F3 资本配置：2026 年度分红率 < 45% 或单笔动用现金 > 5 亿的低回报并购 → 超额现金七折
    v_f3 = weighted(cash_mult=0.7)[0]
    # F4 集采或降价：麝香痔疮膏纳入集采且降幅 > 30%，或零售价下调 → 熊市 60% / 基准 40%
    v_f4 = weighted(probs={"bear": 0.60, "base": 0.40, "bull": 0.0})[0]
    # F5 回款：2026 年末应收账款 > 4.5 亿且全年经营现金流/净利润 < 0.8 → 1.5 亿营运资金视为长期占用，核心利润 −3%
    f5 = {k: dict(s, core26=s["core26"] * 0.97) for k, s in SCEN.items()}
    v_f5 = sum(dcf(f5[k], COE, net_cash=NET_CASH_ADJ - 1.5) * SCEN[k]["p"] for k in SCEN)
    for name, v in (("F1", v_f1), ("F2", v_f2), ("F3", v_f3), ("F4", v_f4), ("F5", v_f5)):
        print(f"{name}: V={v:.2f}  P/V={PRICE / v:.3f}  {verdict(PRICE / v)}")


if __name__ == "__main__":
    main()
