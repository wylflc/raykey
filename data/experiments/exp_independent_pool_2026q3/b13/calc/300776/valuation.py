#!/usr/bin/env python3
"""帝尔激光（300776）独立估值：所有者收益 DCF（经调整净现金为正，无杠杆口径）。

价格日 2026-10-20，最新定期报告 2026 中报（三季报预约 2026-10-28）。
金额单位：亿元；每股价值：元/股。运行：python3 valuation.py
输入全部写在脚本内，出处见同目录上级 companies/300776_帝尔激光.md「来源」。
"""

PRICE = 86.86
SHARES = 2.85234456          # 亿股，含回购专户 1,062,460 股（拟过户给 2026 员工持股计划，不注销）
TREASURY = 0.01062460
COE = 0.09
VAL_TO_MID2027 = 0.70        # 2026-10-20 到 2027 年年中（年中折现）的年数

# ---- 2026-06-30 资产负债表（2026H1_report 第 45-47、95-96、112、130-131 页）----
CASH = 6.35548098            # 货币资金
RESTRICTED = 0.06846902      # 其中履约保证金（受限）
WMP = 2.55457695             # 交易性金融资产：理财产品
EQ_FVTPL = 1.43147464        # 交易性金融资产：权益工具投资（非经营资产）
CD = 19.93317038             # 其他流动资产：银行大额存单
LT_EQ = 0.23832848           # 长期股权投资（非经营资产）
FACTORING = 0.96904632 + 0.81140368  # 应收账款保理款（一年内到期非流动负债 + 长期借款），类债务
LEASE = 0.04789816           # 一年内到期租赁负债
RESERVE = 3.0                # 经营备付：约为基准正常化收入的 15%（约 2.5 个月付现成本）
NONOP_HAIRCUT = 0.75         # 未上市股权类资产按账面 75% 计
CONVERTIBLE_LEFT = 0.0       # 帝尔转债 2026-06-11 摘牌，未转股余额 0（2026H1_report 第 41-42 页）

# 净利息（只用于「正常化归母净利」，DCF 中净现金单列，不重复计息）
YIELD_CASH = 0.016           # 存单/理财/存款综合收益率
COST_FACTORING = 0.030
TAX_INTEREST = 0.15

NET_CASH_ADJ = CASH - RESTRICTED + WMP + CD - FACTORING - LEASE - RESERVE
NON_OP = (EQ_FVTPL + LT_EQ) * NONOP_HAIRCUT

YEARS = [2027, 2028, 2029, 2030, 2031]

# ---- 情景：利润率分项（占收入比例）----
# gm 毛利率；tax_sur 税金及附加；sell/admin/rd 三费；sbc 员工持股计划股份支付；
# soft 软件产品增值税退税；vat 进项加计抵减；imp 信用+资产减值；tax 所得税率；
# nwc 增量营运资本/增量收入；capex_net 资本开支-折旧摊销（亿元/年）；g 终值增长
SCEN = {
    "bear": dict(p=0.30, r2026=16.5, growth=[-0.10, 0.00, 0.04, 0.04, 0.03],
                 gm=0.420, tax_sur=0.008, sell=0.008, admin=0.036, rd=0.125, sbc=0.005,
                 soft=0.020, vat=0.003, imp=0.050, tax=0.12, nwc=0.60, capex_net=0.10, g=0.010,
                 desc="光伏电池端扩产与 BC 改造 2026 年后退潮、TOPCon 改造零散；毛利率 42%、减值 5% 收入；"
                      "2026 正常化收入 16.5 亿，2027 年再降 10%，此后低速恢复；半导体/TGV 无规模收入；终值增长 1%"),
    "base": dict(p=0.50, r2026=19.5, growth=[0.05, 0.07, 0.07, 0.06, 0.05],
                 gm=0.450, tax_sur=0.008, sell=0.008, admin=0.036, rd=0.120, sbc=0.005,
                 soft=0.025, vat=0.005, imp=0.035, tax=0.12, nwc=0.50, capex_net=0.15, g=0.020,
                 desc="2026 正常化收入 19.5 亿（低谷期以 BC/TOPCon 升级支撑，约等于 2024-2026H1 年化均值）；"
                      "2027-2031 年增 5-7%（2027 年能效国标驱动改造、BC 渗透、TGV/PCB 逐步贡献，2031 年收入约 26 亿）；"
                      "毛利率 45%、研发 12%、减值 3.5%；终值增长 2%"),
    "bull": dict(p=0.20, r2026=21.5, growth=[0.12, 0.18, 0.18, 0.15, 0.12],
                 gm=0.460, tax_sur=0.008, sell=0.008, admin=0.036, rd=0.120, sbc=0.005,
                 soft=0.025, vat=0.005, imp=0.025, tax=0.12, nwc=0.45, capex_net=0.20, g=0.025,
                 desc="员工持股计划收入目标基本兑现（2026≥20.5 亿），BC 与组件 LIB/MBI 放量，TGV/PCB 等泛半导体"
                      "2031 年贡献约 15 亿，2031 年收入约 43 亿；毛利率 46%、减值 2.5%；终值增长 2.5%"),
}


def ebit_margin(s):
    return (s["gm"] - s["tax_sur"] - s["sell"] - s["admin"] - s["rd"] - s["sbc"]
            + s["soft"] + s["vat"] - s["imp"])


def path(s):
    """返回逐年收入、NOPAT、再投资与所有者收益（2026 为正常化基年）。"""
    m = ebit_margin(s)
    rev = {2026: s["r2026"]}
    for y, gr in zip(YEARS, s["growth"]):
        rev[y] = rev[y - 1] * (1 + gr)
    rows = {}
    for y in [2026] + YEARS:
        nopat = rev[y] * m * (1 - s["tax"])
        d_nwc = 0.0 if y == 2026 else s["nwc"] * (rev[y] - rev[y - 1])
        reinv = s["capex_net"] + d_nwc
        rows[y] = dict(rev=rev[y], nopat=nopat, reinv=reinv, oe=nopat - reinv)
    return rows


def equity_value(s, r, detail=False):
    rows = path(s)
    g = s["g"]
    last = rows[YEARS[-1]]
    oe_t1 = last["nopat"] * (1 + g) - s["capex_net"] * (1 + g) - s["nwc"] * last["rev"] * g
    tv = oe_t1 / (r - g)
    pv_oe = 0.0
    for i, y in enumerate(YEARS):
        pv_oe += rows[y]["oe"] / (1 + r) ** (i + VAL_TO_MID2027)
    df_last = (1 + r) ** (len(YEARS) - 1 + VAL_TO_MID2027)
    pv_tv = tv / df_last
    h2_2026 = 0.5 * (rows[2026]["nopat"] - s["capex_net"])   # 2026 下半年所有者收益（中报后至年末）
    eq = pv_oe + pv_tv + h2_2026 + NET_CASH_ADJ + NON_OP
    if detail:
        return dict(eq=eq, pv_oe=pv_oe, pv_tv=pv_tv, h2=h2_2026, tv=tv,
                    tv_share=pv_tv / (pv_oe + pv_tv + h2_2026), rows=rows)
    return eq


def per_share(eq, shares=SHARES):
    return eq / shares


def weighted(r, scen=SCEN, probs=None):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * per_share(equity_value(scen[k], r)) for k in scen)


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
    mcap = PRICE * SHARES
    return solve(lambda r: equity_value(s, r), s["g"] + 0.0005, 0.40, mcap)


def reverse_dcf(s):
    """现价隐含增长：(a) 基年所有者收益 10 年恒定增速（此后 2.5% 永续）；(b) 从 2027 起的永续增速。"""
    rows = path(s)
    oe0 = rows[2026]["nopat"] - s["capex_net"]
    target_ev = PRICE * SHARES - NET_CASH_ADJ - NON_OP - 0.5 * oe0

    def ev10(g10, r=COE, gt=0.025):
        pv = 0.0
        oe = oe0
        for i in range(10):
            oe *= 1 + g10
            pv += oe / (1 + r) ** (i + VAL_TO_MID2027)
        pv += oe * (1 + gt) / (r - gt) / (1 + r) ** (9 + VAL_TO_MID2027)
        return pv

    g10 = solve(ev10, -0.20, 0.60, target_ev)
    oe2027 = rows[2027]["oe"]
    g_perp = COE - oe2027 / target_ev
    return g10, g_perp, oe0


def falsifier_values():
    out = {}
    out["F1"] = weighted(COE, probs={"bear": 0.50, "base": 0.45, "bull": 0.05})
    out["F2"] = weighted(COE, probs={"bear": 0.55, "base": 0.45, "bull": 0.00})
    sc = {k: dict(v) for k, v in SCEN.items()}
    for k in ("base", "bull"):
        sc[k]["imp"] += 0.015
    out["F3"] = weighted(COE, scen=sc)
    sc = {k: dict(v) for k, v in SCEN.items()}
    for k in ("base", "bull"):
        sc[k]["gm"] -= 0.03
    out["F4"] = weighted(COE, scen=sc)
    out["F5"] = weighted(COE, probs={"bear": 0.10, "base": 0.40, "bull": 0.50})
    return out


def main():
    print("帝尔激光 300776 独立估值（亿元；元/股）  价格日 2026-10-20  现价 %.2f  总股本 %.4f 亿股" % (PRICE, SHARES))
    print("经调整净现金(无杠杆) = 货币资金 %.2f - 受限 %.2f + 理财 %.2f + 大额存单 %.2f - 保理款 %.2f - 租赁 %.2f - 经营备付 %.2f = %.2f"
          % (CASH, RESTRICTED, WMP, CD, FACTORING, LEASE, RESERVE, NET_CASH_ADJ))
    print("非经营资产(权益工具 %.2f + 长期股权 %.2f) x %.0f%% = %.2f；可转债未转股余额 %.2f（债务法=转股法）"
          % (EQ_FVTPL, LT_EQ, NONOP_HAIRCUT * 100, NON_OP, CONVERTIBLE_LEFT))
    net_int = ((CASH - RESTRICTED + WMP + CD) * YIELD_CASH - FACTORING * COST_FACTORING) * (1 - TAX_INTEREST)
    print("税后净利息（计入正常化归母净利） %.2f" % net_int)
    print()
    res = {}
    for k, s in SCEN.items():
        d = equity_value(s, COE, detail=True)
        rows = d["rows"]
        m = ebit_margin(s)
        v = per_share(d["eq"])
        v8 = per_share(equity_value(s, 0.08))
        v10 = per_share(equity_value(s, 0.10))
        np_norm = rows[2026]["nopat"] + net_int
        reinv5 = sum(rows[y]["reinv"] for y in YEARS)
        nopat5 = sum(rows[y]["nopat"] for y in YEARS)
        inc_ret = (rows[2031]["nopat"] - rows[2026]["nopat"]) / reinv5 if reinv5 > 0 else float("nan")
        oe_g = [rows[y]["oe"] / rows[y - 1]["oe"] - 1 if y > 2027 else rows[2027]["oe"] / (rows[2026]["nopat"] - s["capex_net"]) - 1
                for y in YEARS]
        res[k] = dict(v=v, v8=v8, v10=v10, np=np_norm)
        print("[%s] p=%.2f  EBIT率 %.1f%%  税后经营利润率 %.1f%%" % (k, s["p"], m * 100, m * (1 - s["tax"]) * 100))
        print("  收入   " + "  ".join("%d:%.2f" % (y, rows[y]["rev"]) for y in [2026] + YEARS))
        print("  NOPAT  " + "  ".join("%d:%.2f" % (y, rows[y]["nopat"]) for y in [2026] + YEARS))
        print("  所有者收益 " + "  ".join("%d:%.2f" % (y, rows[y]["oe"]) for y in YEARS)
              + "  增速 " + " ".join("%.1f%%" % (x * 100) for x in oe_g))
        print("  2026 正常化归母净利(含净利息) %.2f；再投资率(2027-31) %.1f%%；增量回报 %.1f%%；终值增长 %.1f%%"
              % (np_norm, reinv5 / nopat5 * 100, inc_ret * 100, s["g"] * 100))
        print("  股权价值 %.1f = 显性期现值 %.1f + 终值现值 %.1f + 2026H2 %.1f + 净现金 %.1f + 非经营 %.1f；终值占经营价值 %.0f%%"
              % (d["eq"], d["pv_oe"], d["pv_tv"], d["h2"], NET_CASH_ADJ, NON_OP, d["tv_share"] * 100))
        print("  V = %.2f 元/股（剔除回购专户股份 %.2f）  8%%: %.2f  10%%: %.2f" %
              (v, per_share(d["eq"], SHARES - TREASURY), v8, v10))
    vw = weighted(COE)
    vw8 = weighted(0.08)
    vw10 = weighted(0.10)
    eq_w = vw * SHARES
    print()
    print("加权 V = %.2f 元/股（剔除回购专户 %.2f）  P/V = %.2f" % (vw, eq_w / (SHARES - TREASURY), PRICE / vw))
    print("股权成本 8%%: V=%.2f (P/V %.2f)   10%%: V=%.2f (P/V %.2f)" % (vw8, PRICE / vw8, vw10, PRICE / vw10))
    irr = implied_irr(SCEN["base"])
    print("现价隐含回报（基准情景所有者收益流+净现金=市值的折现率）= %.2f%%" % (irr * 100))
    g10, gp, oe0 = reverse_dcf(SCEN["base"])
    print("反向 DCF：基年所有者收益 %.2f 亿，现价隐含 10 年年增 %.1f%%（此后 2.5%%）；或自 2027 年起永续增长 %.1f%%（上限 2.5%%）"
          % (oe0, g10 * 100, gp * 100))
    ev = PRICE * SHARES - NET_CASH_ADJ - NON_OP
    base_rows = path(SCEN["base"])
    ebit26 = base_rows[2026]["rev"] * ebit_margin(SCEN["base"])
    print("交叉：EV %.1f 亿；EV/正常化 EBIT(基准 2026) %.1fx；市值/正常化归母(基准) %.1fx"
          % (ev, ev / ebit26, PRICE * SHARES / res["base"]["np"]))
    fv = falsifier_values()
    print("证伪触发后 V：" + "  ".join("%s=%.2f" % (k, v) for k, v in fv.items()))
    print("V 不变时各档价格：明显低估 ≤ %.2f；温和低估 %.2f～%.2f；大致合理 %.2f～%.2f；偏贵 > %.2f"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
