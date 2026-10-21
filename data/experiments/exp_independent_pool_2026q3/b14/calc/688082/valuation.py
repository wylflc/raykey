# -*- coding: utf-8 -*-
"""盛美上海（688082）独立估值：所有者收益 DCF（经济口径，研发全额费用化），熊/基准/牛三情景。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。价格日 2026-10-20，估值基准日同日。
输入均来自 2026 半年报、2025 年报、公告与数据包，出处见正文 companies/688082_盛美上海.md。
"""
from datetime import date

# ---------------------------------------------------------------- 市场与股本
PRICE = 243.33                 # 2026-10-20 收盘（数据包快照）
SHARES = 4.8527                # 亿股，行情总股本，含回购专户股份（2026-09 限制性股票归属后）
TREASURY = 0.004434            # 回购专户 443,400 股，用途为股权激励，不注销（buyback_20250805 第 1 页）
VAL_DATE = date(2026, 10, 20)

COE = 0.09
G_TERM = 0.025
TAX = 0.135                    # 正常化有效税率（2026H1 合并所得税 1.52/利润总额 11.41 = 13.3%）
CAP_RD_TAX = 0.15              # 资本化研发改为费用化时的税盾（母公司高新技术企业 15%）

# ---------------------------------------------------------------- 资产负债表 2026-06-30（2026H1_report 第 73-75、129-130、142-148 页）
CASH = 46.898                  # 货币资金
RESTRICTED = 0.092 + 1.363     # 韩国退休金专户 + 银行保证金（第 143 页）
DEPOSITS = 24.867              # 其他流动资产中的定期存款/大额存单及应收利息（第 130 页）
DEBT = 7.304 + 13.141 + 2.778 + 0.542   # 短借 + 长借 + 一年内到期长借(含息) + 租赁负债(含一年内)
DEBT_LIKE = 0.092              # 长期应付职工薪酬（韩国退休金）
DIV_PAYABLE = 2.990            # 应付股利，2026-07-31 已派发
RSU_CASH_IN = 0.0267 * 47.88   # 2026-09 归属约 267 万股（公告 2026-09-11 标题）× 估算归属价 47.88 元（48.50 元扣 2025 年度分红）
OP_RESERVE_PCT = 0.05          # 经营备付：2026E 收入的 5%

# 非经营资产：交易性金融资产（华虹公司 6.467、上海合晶 0.692，成本 1.000+0.200）、其他非流动金融资产 1.675（成本约 1.43）
LISTED_EQ, LISTED_COST = 6.467 + 0.692, 1.000 + 0.200
OTHER_FIN, OTHER_FIN_COST = 1.675, 1.430
NONOP = (LISTED_EQ - 0.15 * (LISTED_EQ - LISTED_COST)) + (OTHER_FIN - 0.15 * (OTHER_FIN - OTHER_FIN_COST))
# 长期股权投资 2.98（Ninebell 等）不另加，其投资收益计入正常化利润。

# ---------------------------------------------------------------- 2026 年正常化（报表口径，含资本化研发）
REV_2025 = 67.862
REV_H1_2026 = 37.181
RECUR_NP_H1 = 5.710            # 2026H1 扣非归母（第 9 页）
FX_LOSS_H1 = 1.461             # 2026H1 汇兑损失（第 155 页），正常化时加回（税后）
CAP_RD_H1 = 1.969              # 2026H1 资本化研发（第 28 页）
NORM_NP_H1 = RECUR_NP_H1 + FX_LOSS_H1 * (1 - CAP_RD_TAX)

H2_COMMON = dict(sell=0.078, admin=0.033, sur=0.0026, cap_share=0.30, assoc=0.35, net_int=0.30)  # 含 2026 年限制性股票（8 月授予）摊销

SCEN = {
    # rev: 2026-2031 收入；m: 2027-2031 经济口径归母净利率（研发全额费用化、剔除汇兑与非经常）；k: 增量收入所需增量资本
    "bear": dict(p=0.25, rev2026=81.0, gm_h2=0.445, rd_h2=0.180, imp_h2=0.040,
                 rev=[110.0, 100.0, 95.0, 108.0, 118.0], m=[0.145, 0.115, 0.110, 0.135, 0.150], k=0.80),
    "base": dict(p=0.50, rev2026=85.0, gm_h2=0.460, rd_h2=0.175, imp_h2=0.031,
                 rev=[128.0, 150.0, 160.0, 175.0, 190.0], m=[0.160, 0.170, 0.175, 0.180, 0.180], k=0.70),
    "bull": dict(p=0.25, rev2026=88.0, gm_h2=0.470, rd_h2=0.165, imp_h2=0.028,
                 rev=[145.0, 180.0, 205.0, 235.0, 265.0], m=[0.170, 0.185, 0.195, 0.205, 0.210], k=0.60),
}
EXTRA_CAPEX_H2_2026 = 3.4      # 临港 B 厂房装修与设备（ACMR 指引 2026 年资本开支约 1.75 亿美元，H1 已付 6.69 亿元）
FADE_YEARS = 4                 # 2032-2035 增速线性回落至 2.5%


def norm_2026(s):
    """返回 (报表口径正常化归母净利, 经济口径, 下半年经济口径净利, 全年资本化研发)."""
    rev_h2 = s["rev2026"] - REV_H1_2026
    c = H2_COMMON
    rd_exp = s["rd_h2"] * (1 - c["cap_share"])
    pretax = rev_h2 * (s["gm_h2"] - c["sell"] - c["admin"] - rd_exp - c["sur"] - s["imp_h2"]) + c["assoc"] + c["net_int"]
    np_h2 = pretax * (1 - TAX)
    cap_h2 = rev_h2 * s["rd_h2"] * c["cap_share"]
    reported = NORM_NP_H1 + np_h2
    cap = CAP_RD_H1 + cap_h2
    econ = reported - cap * (1 - CAP_RD_TAX)
    econ_h2 = np_h2 - cap_h2 * (1 - CAP_RD_TAX)
    return reported, econ, econ_h2, cap


def net_cash_adj(rev2026=85.0):
    return (CASH - RESTRICTED + DEPOSITS - DEBT - DEBT_LIKE - DIV_PAYABLE
            - OP_RESERVE_PCT * rev2026 + RSU_CASH_IN)


def t_mid(year):
    """年中现金流距估值日的年数。"""
    return ((date(year, 7, 1) - VAL_DATE).days) / 365.25


def cashflows(s, fade=True):
    """返回 [(年份, 收入, 经济净利, 再投资, 所有者收益, 折现年数)] 与终值输入 (次年所有者收益, 折现年数, 末年收入)。"""
    _, _, econ_h2, _ = norm_2026(s)
    rows = []
    reinv_h2 = 0.5 * s["k"] * (s["rev2026"] - REV_2025) + EXTRA_CAPEX_H2_2026
    rows.append(("2026H2", s["rev2026"], econ_h2, reinv_h2, econ_h2 - reinv_h2, 0.0))
    prev = s["rev2026"]
    for i, y in enumerate(range(2027, 2032)):
        rev = s["rev"][i]
        npv = rev * s["m"][i]
        reinv = s["k"] * (rev - prev)
        rows.append((y, rev, npv, reinv, npv - reinv, t_mid(y)))
        prev = rev
    m_last = s["m"][-1]
    g_last = s["rev"][-1] / s["rev"][-2] - 1
    last_year = 2031
    if fade:
        for j in range(1, FADE_YEARS + 1):
            g = g_last - (g_last - G_TERM) * j / (FADE_YEARS + 1)
            y = 2031 + j
            rev = prev * (1 + g)
            npv = rev * m_last
            reinv = s["k"] * (rev - prev)
            rows.append((y, rev, npv, reinv, npv - reinv, t_mid(y)))
            prev = rev
            last_year = y
    rev_next = prev * (1 + G_TERM)
    oe_next = rev_next * m_last - s["k"] * (rev_next - prev)
    t_tv = t_mid(last_year)        # 年中惯例：次年起的现金流按 Gordon 公式折到末年年中
    return rows, (oe_next, t_tv, prev)


def value(s, r=COE, fade=True, shares=SHARES):
    rows, (oe_next, t_tv, _) = cashflows(s, fade)
    pv_exp = sum(oe / (1 + r) ** t for (_, _, _, _, oe, t) in rows)
    tv = oe_next / (r - G_TERM)
    pv_tv = tv / (1 + r) ** t_tv
    nc = net_cash_adj(s["rev2026"])
    equity = pv_exp + pv_tv + nc + NONOP
    return dict(v=equity / shares, equity=equity, pv_exp=pv_exp, pv_tv=pv_tv, nc=nc, tv_share=pv_tv / (pv_exp + pv_tv))


def weighted(r=COE, fade=True, shares=SHARES, scen=SCEN, probs=None):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * value(scen[k], r, fade, shares)["v"] for k in scen)


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


def implied_irr(s):
    return solve(lambda r: value(s, r)["v"], 0.03, 0.20, PRICE)


def reverse_rev_cagr():
    """基准利润率路径与 k 不变，2027-2031 收入匀速增长率 x（其后照常回落至 2.5%）使 V = 现价。"""
    b = SCEN["base"]

    def f(x):
        s = dict(b)
        s["rev"] = [b["rev2026"] * (1 + x) ** n for n in range(1, 6)]
        return value(s)["v"]
    return solve(f, 0.0, 0.80, PRICE)


def reverse_oe_growth():
    """以 2026 年经济口径净利扣除 2.5% 稳态增长所需再投资为起点，10 年所有者收益匀速增长率 y 使 V = 现价。"""
    b = SCEN["base"]
    _, econ, _, _ = norm_2026(b)
    oe0 = econ * (1 - G_TERM * b["k"] / b["m"][-1])
    nc = net_cash_adj(b["rev2026"]) + NONOP

    def f(y):
        pv = 0.0
        oe = oe0
        for n in range(1, 11):
            oe *= (1 + y)
            pv += oe / (1 + COE) ** (t_mid(2026 + n))
        tv = oe * (1 + G_TERM) / (COE - G_TERM)
        pv += tv / (1 + COE) ** t_mid(2036)
        return (pv + nc) / SHARES
    return oe0, solve(f, -0.10, 0.60, PRICE)


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("=== 盛美上海 688082 独立估值（价格日 2026-10-20，现价 %.2f 元，总股本 %.4f 亿股）===" % (PRICE, SHARES))
    nc = net_cash_adj(85.0)
    print("经调整净现金（基准，扣经营备付 %.2f）：%.2f 亿元；非经营资产（税后）：%.2f 亿元" % (OP_RESERVE_PCT * 85, nc, NONOP))
    print()
    print("2026 正常化归母净利（报表口径 | 经济口径 | 全年资本化研发）：")
    for k, s in SCEN.items():
        rep, econ, _, cap = norm_2026(s)
        print("  %-4s 收入 %.1f：报表 %.2f（%.1f%%） | 经济 %.2f（%.1f%%） | 资本化研发 %.2f"
              % (k, s["rev2026"], rep, rep / s["rev2026"] * 100, econ, econ / s["rev2026"] * 100, cap))
    print()
    res = {}
    for k, s in SCEN.items():
        r = value(s)
        res[k] = r
        print("[%s] p=%.2f  V=%.2f 元  股权价值 %.1f = 显性期现值 %.1f + 终值现值 %.1f + 净现金 %.1f + 非经营 %.1f；终值占经营价值 %.0f%%"
              % (k, s["p"], r["v"], r["equity"], r["pv_exp"], r["pv_tv"], r["nc"], NONOP, r["tv_share"] * 100))
        rows, (oe_next, t_tv, rev_last) = cashflows(s)
        for (y, rev, npv, reinv, oe, t) in rows:
            print("    %-6s 收入 %6.1f  经济净利 %5.1f  再投资 %5.1f  所有者收益 %6.1f  t=%.2f" % (y, rev, npv, reinv, oe, t))
        print("    终值：次年所有者收益 %.1f，末年收入 %.1f，t=%.2f" % (oe_next, rev_last, t_tv))
    vw = weighted()
    pv = PRICE / vw
    print()
    print("加权 V = %.2f 元；P/V = %.2f → %s" % (vw, pv, tier(pv)))
    v8, v10 = weighted(0.08), weighted(0.10)
    print("股权成本 8%%：V = %.2f（P/V %.2f）；10%%：V = %.2f（P/V %.2f）" % (v8, PRICE / v8, v10, PRICE / v10))
    for k in SCEN:
        print("  %s：8%% %.2f / 9%% %.2f / 10%% %.2f" % (k, value(SCEN[k], 0.08)["v"], res[k]["v"], value(SCEN[k], 0.10)["v"]))
    vstrict = weighted(fade=False)
    print("对照：不设 2032-2035 回落期、2031 年后直接 2.5%% 永续：加权 V = %.2f（P/V %.2f）" % (vstrict, PRICE / vstrict))
    vx = weighted(shares=SHARES - TREASURY)
    print("对照：剔除回购专户 44.34 万股：加权 V = %.2f（P/V %.2f）" % (vx, PRICE / vx))
    irr = implied_irr(SCEN["base"])
    print("现价隐含回报（基准情景所有者收益流+终值+净现金）：%.2f%%" % (irr * 100))
    print("  各情景隐含回报：熊 %.2f%% / 基准 %.2f%% / 牛 %.2f%%"
          % tuple(implied_irr(SCEN[k]) * 100 for k in ("bear", "base", "bull")))
    x = reverse_rev_cagr()
    rev2031 = 85 * (1 + x) ** 5
    print("反向 DCF ①：基准利润率与 k 不变，2027-2031 收入年均增长 %.1f%%（2031 年收入 %.0f 亿元，约 %.1f 倍 2026E）才能支撑现价"
          % (x * 100, rev2031, rev2031 / 85))
    oe0, y = reverse_oe_growth()
    print("反向 DCF ②：所有者收益自 2026 年稳态起点 %.1f 亿元起，10 年年均增长 %.1f%%（第 10 年 %.0f 亿元），其后 2.5%%"
          % (oe0, y * 100, oe0 * (1 + y) ** 10))
    # 证伪触发后的独立 V
    print()
    print("证伪条件触发后的 V：")
    f1 = weighted(probs={"bear": 0.4, "base": 0.6, "bull": 0.0})
    print("  F1 2026 年营收 < 80 亿元（熊 0.4／基准 0.6／牛 0）：%.2f" % f1)
    print("  F2 2027-09 在手订单 < 150 亿元或 2027 年营收 < 110 亿元（熊情景）：%.2f" % res["bear"]["v"])
    low_m = {k: dict(v, m=[x - 0.025 for x in v["m"]]) for k, v in SCEN.items()}
    f3 = weighted(scen=low_m)
    print("  F3 2027 年扣非归母（加回税后汇兑损益）/营收 < 15%%（各情景利润率 -2.5pp）：%.2f" % f3)
    f4 = weighted(probs={"bear": 0.5, "base": 0.5, "bull": 0.0})
    print("  F4 关联方规则恢复且公告断供或海外订单取消 > 在手订单 5%%（熊 0.5／基准 0.5）：%.2f" % f4)
    print("  F5 上行：2027 年营收 ≥ 145 亿元且 2027-09 在手订单 ≥ 220 亿元（牛情景）：%.2f" % res["bull"]["v"])
    hi_k = {k: dict(v, k=v["k"] + 0.20) for k, v in SCEN.items()}
    print("  敏感性：增量资本强度 k 各情景 +0.20：%.2f；-0.20：%.2f"
          % (weighted(scen=hi_k), weighted(scen={k: dict(v, k=v["k"] - 0.20) for k, v in SCEN.items()})))
    # 报表口径对照：经济口径利润率加回资本化研发净额（逐年收窄）
    rep_m = {k: dict(v, m=[x + d for x, d in zip(v["m"], [0.025, 0.020, 0.015, 0.010, 0.005])]) for k, v in SCEN.items()}
    print("对照：报表口径（不扣资本化研发净额）加权 V = %.2f" % weighted(scen=rep_m))
    # 交叉验证
    print()
    rep_b, econ_b, _, _ = norm_2026(SCEN["base"])
    mcap = PRICE * SHARES
    ev = mcap - nc - NONOP
    ebit26 = rep_b / (1 - TAX) - H2_COMMON["net_int"] - 0.38 - 0.63 - H2_COMMON["assoc"]
    b = SCEN["base"]
    rep27 = b["rev"][0] * (b["m"][0] + 0.025)
    print("交叉验证：市值 %.1f 亿元；EV（扣净现金与非经营资产）%.1f 亿元" % (mcap, ev))
    print("  现价 P/E：2026E 正常化（基准报表口径 %.2f）%.1f 倍；2027E 报表口径约 %.1f 亿元 → %.1f 倍"
          % (rep_b, mcap / rep_b, rep27, mcap / rep27))
    print("  EV/EBIT 2026E（EBIT 约 %.1f）：%.1f 倍；EV/EBIT 2027E（EBIT 约 %.1f）：%.1f 倍"
          % (ebit26, ev / ebit26, rep27 / (1 - TAX) - 2.0, ev / (rep27 / (1 - TAX) - 2.0)))
    eq_v = vw * SHARES
    print("  V 对应：2026E 正常化 P/E %.1f 倍，2027E %.1f 倍；P/B %.2f 倍（6-30 归母权益 146.07 亿元）"
          % (eq_v / rep_b, eq_v / rep27, eq_v / 146.07))
    print("  股息率 %.2f%%（每股 0.6202 元）；2025 年回购 0.50 亿元，占市值 %.2f%%" % (0.6202 / PRICE * 100, 0.50 / mcap * 100))
    new_sh, new_px = 0.10 * SHARES, 200.0
    print("  H 股示意：按 %.0f 元等值新发 10%% 股份，每股 V 由 %.2f 变为 %.2f" % (new_px, vw, (eq_v + new_sh * new_px) / (SHARES + new_sh)))
    print()
    print("分档价格（V 不变）：≤%.1f 明显低估；%.1f～%.1f 温和低估；%.1f～%.1f 大致合理；>%.1f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
