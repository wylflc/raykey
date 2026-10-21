#!/usr/bin/env python3
"""光威复材（300699）OI-291 池内独立估值（深度版）。

运行：python3 valuation.py
口径：金额亿元，每股元；价格日 2026-10-20；最新定期报告 2026 中报（资产负债表 2026-06-30）。
方法：归母所有者收益 DCF（股权成本 9%，终值增长 <= 2.5%），经调整净现金为负，
      按框架有杠杆口径（净负债按现规模滚动，扣其税后利息现值），另列无杠杆口径对照。
所有输入写在本脚本内，出处见同目录上级 companies/300699_光威复材.md「来源」一节。
"""
from datetime import date

# ----------------------------------------------------------------- 快照
PRICE = 23.92                 # 2026-10-20 收盘
SHARES = 8.3135               # 亿股，总股本（含回购专户 635.2 万股）
TREASURY = 0.06352            # 亿股，回购专户（2026H1_report 第 34 页）
VAL_DATE = date(2026, 10, 20)
COE = 0.09
PROB = {"bear": 0.25, "base": 0.50, "bull": 0.25}
MCAP = PRICE * SHARES

# ----------------------------------------------- 资产负债（2026-06-30）
CASH = 11.5368                # 货币资金
RESTRICTED = 1.7176           # 银行承兑汇票保证金（2026H1_report 第 78 页）
OP_RESERVE = 1.50             # 经营备付，约 TTM 营收 5%（约 1 个月付现成本）
ST_LOAN = 13.1265             # 短期借款，其中质押（应收账款保理）3.435（第 106 页）
CUR_NONCUR = 3.3321           # 一年内到期非流动负债（长期借款 3.2727 + 租赁 0.0593）
LT_LOAN = 1.6495
LEASE = 0.0280
RP_LOAN = 1.20                # 控股股东光威集团资金拆借，2027 年到期（第 108、140 页）
NON_OP = 0.4798               # 长期股权投资账面（科泰克、上工飞人），视作非经营资产
DIV_DECLARED = 0.0            # 2025 年度股利已于 2026-06-18 除息

BANK_DEBT = ST_LOAN + CUR_NONCUR + LT_LOAN + LEASE          # 18.14
DEBT = BANK_DEBT + RP_LOAN                                  # 19.34
NET_CASH_ADJ = CASH - RESTRICTED - OP_RESERVE - DIV_DECLARED - DEBT   # 无杠杆口径经调整净现金

# 应付票据浮存：票据净额（应付票据 - 保证金）相对 2024 年末占营业成本比例的超额部分
NOTE_PAY, NOTE_PAY_24, MARGIN_24, COGS_24 = 6.2155, 2.0422, 0.6018, 13.3405
COGS_TTM = 17.2140 - 6.9057 + 7.9742
FLOAT_NOW = NOTE_PAY - RESTRICTED
FLOAT_NORMAL = (NOTE_PAY_24 - MARGIN_24) / COGS_24 * COGS_TTM
FLOAT_EXCESS = FLOAT_NOW - FLOAT_NORMAL

# 有息负债实际平均利率：TTM 利息费用 / 5 个季末银行借款与租赁负债的梯形平均
INT_EXP_TTM = 0.4042 - 0.1821 + 0.1907
BANK_DEBT_Q = [12.514, 14.527, 15.451, 15.400, 18.136]      # 2025-06 至 2026-06（东财 F10 资产负债表）
AVG_BANK_DEBT = (BANK_DEBT_Q[0] / 2 + sum(BANK_DEBT_Q[1:-1]) + BANK_DEBT_Q[-1] / 2) / 4
RATE = INT_EXP_TTM / AVG_BANK_DEBT

# ------------------------------------------- 2026 正常化（分部毛利法）
# 2026H1 实际（2026H1_report 第 17、116、118-120 页）
H1_GP = 3.5581 + 1.2044 + 0.3100 + 0.1225 + 0.0186   # 碳纤维+碳梁+预浸料+制品+其他业务 = 5.2136
H1_OPEX = 0.1698 + 0.0711 + 0.6672 + 1.3234          # 税金及附加+销售+管理+研发
H1_CORE = H1_GP - H1_OPEX
MINORITY_ADD = 0.08           # 光晟科技亏损中少数股东承担部分（2025 年 -0.041，2026H1 -0.045）

# 2025 年股份支付为 -0.2507（限制性股票业绩条件未达成，冲回以前年度费用；2025_annual_report 第 183 页），
# 其中 2025H1 计提 +0.0485，故 2025H2 费用含 -0.2992 的一次性冲回。2025H2 报告费用 2.2115，剔除后 2.5107。
H2_2025_OPEX_EX_SBC = (0.3560 - 0.1659) + (0.1857 - 0.0799) + (1.4581 - 0.6055) + (2.1952 - 1.1321) + 0.2992

SCEN = {
    # h2: 下半年分部 (收入, 毛利率)；opex: 下半年费用（税金及附加+销售+管理+研发，不含股份支付冲回）；
    # subsidy: 经常性政府补助（约等于现金补助）；impair: 正常化信用+存货减值；
    # net_int: 净利息（不含汇兑）；tax: 有效税率
    # growth: 2027-2031 归母 NOPAT 增速；tg: 终值增长；roic: 增量资本回报；
    # maint: 维护性资本开支/折旧摊销；extra_debt: 额外计入的类债务
    "bear": dict(h2={"cf": (8.4, 0.45), "beam": (5.7, 0.25), "prepreg": (1.2, 0.22), "other": (1.1, 0.15)},
                 opex=2.55, subsidy=0.25, impair=0.55, net_int=-0.10, tax=0.16,
                 growth=[0.02, -0.15, 0.00, 0.02, 0.02], tg=0.015, roic=0.08, maint=1.00,
                 extra_debt=FLOAT_EXCESS),
    "base": dict(h2={"cf": (8.6, 0.485), "beam": (5.9, 0.275), "prepreg": (1.27, 0.24), "other": (1.2, 0.20)},
                 opex=2.48, subsidy=0.40, impair=0.40, net_int=-0.05, tax=0.155,
                 growth=[0.06, -0.04, 0.04, 0.04, 0.03], tg=0.025, roic=0.12, maint=0.90,
                 extra_debt=0.0),
    "bull": dict(h2={"cf": (9.2, 0.51), "beam": (6.1, 0.29), "prepreg": (1.3, 0.26), "other": (1.3, 0.22)},
                 opex=2.45, subsidy=0.50, impair=0.30, net_int=0.0, tax=0.15,
                 growth=[0.12, 0.05, 0.12, 0.10, 0.08], tg=0.025, roic=0.18, maint=0.85,
                 extra_debt=0.0),
}


def normalized_history():
    """2025 年与 TTM 的同口径正常化（剔除汇兑、股份支付冲回，补助与减值取 0.40 常态值）。"""
    gp25, opex25, sbc25 = 28.5952 - 17.2140, 0.3560 + 0.1857 + 1.4581 + 2.1952, -0.2507
    core25 = gp25 - (opex25 - sbc25)
    np25 = (core25 + 0.40 - 0.40 - 0.071) * (1 - 0.155) + 0.041
    gp_ttm = 11.4930
    opex_ttm = (0.3560 - 0.1659 + 0.1698) + (0.1857 - 0.0799 + 0.0711) + (1.4581 - 0.6055 + 0.6672) + (2.1952 - 1.1321 + 1.3234)
    sbc_ttm = -0.2992
    core_ttm = gp_ttm - (opex_ttm - sbc_ttm)
    np_ttm = (core_ttm + 0.40 - 0.40 - 0.023) * (1 - 0.155) + 0.086
    return dict(core25=core25, np25=np25, core_ttm=core_ttm, np_ttm=np_ttm)
DA = 4.5                      # 2026 折旧摊销约 4.4（2026H1 2.20），此后按 4.5
YEARS = [2027, 2028, 2029, 2030, 2031]


def normalize(s):
    h2_rev = sum(r for r, _ in s["h2"].values())
    h2_gp = sum(r * m for r, m in s["h2"].values())
    core = H1_CORE + h2_gp - s["opex"]
    ebit = core + s["subsidy"] - s["impair"]
    nopat = ebit * (1 - s["tax"]) + MINORITY_ADD
    np_parent = (ebit + s["net_int"]) * (1 - s["tax"]) + MINORITY_ADD
    return dict(h2_rev=h2_rev, h2_gp=h2_gp, rev=13.1878 + h2_rev, gp=H1_GP + h2_gp,
                core=core, ebit=ebit, nopat=nopat, np=np_parent)


def yfrac(d):
    return (d - VAL_DATE).days / 365.25


def value(name, coe=COE, growth=None, nopat0=None, extra_debt=None, roic=None, levered=True, detail=False):
    s = SCEN[name]
    n = normalize(s)
    g = s["growth"] if growth is None else growth
    nop = [n["nopat"] if nopat0 is None else nopat0]
    for x in g:
        nop.append(nop[-1] * (1 + x))
    roic_i = s["roic"] if roic is None else roic
    cagr = (nop[-1] / nop[0]) ** (1 / len(g)) - 1
    rr = max(cagr, s["tg"]) / roic_i          # 显性期再投资率（增长须由再投资 x 增量回报支撑）
    rr_t = s["tg"] / roic_i                   # 终值期再投资率
    gap = DA * (1 - s["maint"])               # 折旧高于维护性资本开支的部分（显性期）
    oe = [x * (1 - rr) + gap for x in nop]    # nop[0] 为 2026 年
    # 2026 下半年（资产负债表日之后）的所有者收益，按半年计入，时点约为估值日
    pv = 0.5 * oe[0]
    rows = []
    for i, yr in enumerate(YEARS, start=1):
        t = yfrac(date(yr, 7, 1))
        d = (1 + coe) ** t
        pv += oe[i] / d
        rows.append((yr, nop[i], oe[i], t, oe[i] / d))
    oe_t = nop[-1] * (1 + s["tg"]) * (1 - rr_t)
    tv = oe_t / (coe - s["tg"])
    t_end = yfrac(date(2031, 12, 31))
    pv_tv = tv / (1 + coe) ** t_end
    ops = pv + pv_tv
    nd = -NET_CASH_ADJ + (s["extra_debt"] if extra_debt is None else extra_debt)
    int_pv = nd * RATE * (1 - s["tax"]) / coe
    eq_lev = ops - int_pv + NON_OP
    eq_unlev = ops - nd + NON_OP
    eq = eq_lev if levered else eq_unlev
    out = dict(name=name, norm=n, nop=nop, oe=oe, rr=rr, rr_t=rr_t, gap=gap, cagr=cagr, rows=rows,
               tv=tv, pv_tv=pv_tv, ops=ops, nd=nd, int_pv=int_pv, eq_lev=eq_lev, eq_unlev=eq_unlev,
               v=eq / SHARES, v_lev=eq_lev / SHARES, v_unlev=eq_unlev / SHARES,
               v_ex_treasury=eq_lev / (SHARES - TREASURY), tv_share=pv_tv / ops, oe_t=oe_t)
    return out


def weighted(coe=COE, levered=True):
    return sum(PROB[k] * value(k, coe=coe, levered=levered)["v"] for k in PROB)


def bisect(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    # 基准情景所有者收益流（含终值与有杠杆口径净负债）使股权价值等于现价市值的折现率
    return bisect(lambda r: value("base", coe=r)["eq_lev"] - MCAP, 0.0301, 0.20)


def reverse_dcf():
    b = value("base")
    target_ops = MCAP + b["int_pv"] - NON_OP          # 现价对应的经营价值
    oe26 = b["oe"][0]
    # (a) 以 2026 年正常化所有者收益为起点，2027-2036 年复合增速 X，此后永续 2.5%
    def ops_at(x):
        pv = 0.5 * oe26
        oe = oe26
        for k in range(10):
            yr = 2027 + k
            oe *= (1 + x)
            pv += oe / (1 + COE) ** yfrac(date(yr, 7, 1))
        tv = oe * 1.025 / (COE - 0.025)
        return pv + tv / (1 + COE) ** yfrac(date(2036, 12, 31))
    x10 = bisect(lambda x: ops_at(x) - target_ops, -0.05, 0.60)
    # (b) 永续增速：以 2027 年基准所有者收益为首年现金流
    oe27 = b["oe"][1]
    t27 = yfrac(date(2027, 7, 1))
    gp = COE - oe27 / ((target_ops - 0.5 * oe26) * (1 + COE) ** t27)
    return dict(target_ops=target_ops, x10=x10, g_perp=gp, oe26=oe26, oe27=oe27)


def variants():
    b = SCEN["base"]["growth"]
    out = {}
    out["F1_业绩证伪(=熊)"] = value("bear")["v"]
    out["F2_新合同降价15%"] = value("base", growth=[b[0], -0.15, b[2], b[3], b[4]])["v"]
    out["F3_包头不减亏"] = value("base", growth=[0.01, b[1], b[2], b[3], b[4]])["v"]
    out["F4_营运资本沉淀4亿且增量回报10%"] = value("base", extra_debt=4.0, roic=0.10)["v"]
    n = normalize(SCEN["base"])
    out["F5_碳梁毛利率降至24%"] = value("base", nopat0=n["nopat"] - 0.40 * (1 - 0.155))["v"]
    out["U1_合同放量且包头盈亏平衡(=牛)"] = value("bull")["v"]
    return out


def main():
    print("== 光威复材 300699 独立估值（价格日 2026-10-20，现价 %.2f，总股本 %.4f 亿股，市值 %.2f 亿）==" % (PRICE, SHARES, MCAP))
    print("\n[净现金] 现金 %.2f - 受限 %.2f - 经营备付 %.2f - 银行借款及租赁 %.2f - 关联方拆借 %.2f = 经调整净现金 %.2f"
          % (CASH, RESTRICTED, OP_RESERVE, BANK_DEBT, RP_LOAN, NET_CASH_ADJ))
    print("        票据浮存 %.2f（正常 %.2f，超额 %.2f，仅熊情景计入）；有息负债实际平均利率 %.2f%%（TTM 利息 %.3f / 平均借款 %.2f）"
          % (FLOAT_NOW, FLOAT_NORMAL, FLOAT_EXCESS, RATE * 100, INT_EXP_TTM, AVG_BANK_DEBT))
    nh = normalized_history()
    print("\n[历史同口径正常化] 2025 核心经营利润（剔除股份支付冲回）%.2f → 正常化归母净利 %.2f（报告 6.03）；"
          "TTM 核心 %.2f → 正常化归母净利 %.2f（报告 5.33）；2025H2 费用剔除冲回后 %.2f"
          % (nh["core25"], nh["np25"], nh["core_ttm"], nh["np_ttm"], H2_2025_OPEX_EX_SBC))
    print("[2026 正常化] H1 实际核心经营利润 %.3f（毛利 %.3f - 费用 %.3f）" % (H1_CORE, H1_GP, H1_OPEX))
    for k in ("bear", "base", "bull"):
        n = normalize(SCEN[k])
        print("  %-4s 营收 %.2f 毛利 %.2f(%.1f%%) 核心 %.2f EBIT %.2f NOPAT %.2f 正常化归母净利 %.2f"
              % (k, n["rev"], n["gp"], n["gp"] / n["rev"] * 100, n["core"], n["ebit"], n["nopat"], n["np"]))
    print("\n[DCF] 9%，显性期 2027-2031，年中折现；有杠杆口径 = 经营价值 - 净负债税后利息现值 + 非经营资产")
    res = {}
    for k in ("bear", "base", "bull"):
        r = value(k)
        res[k] = r
        print("  %-4s 再投资率 %.1f%%（终值 %.1f%%）增量回报 %.0f%% 折旧-维护差 %.2f NOPAT CAGR %.1f%%"
              % (k, r["rr"] * 100, r["rr_t"] * 100, SCEN[k]["roic"] * 100, r["gap"], r["cagr"] * 100))
        print("       2026 NOPAT %.2f OE %.2f | " % (r["nop"][0], r["oe"][0])
              + " ".join("%d:%.2f/%.2f" % (y, a, b) for y, a, b, _, _ in r["rows"]))
        print("       经营价值 %.1f（终值现值 %.1f，占 %.0f%%）净负债 %.2f 利息现值 %.2f 非经营 %.2f"
              % (r["ops"], r["pv_tv"], r["tv_share"] * 100, r["nd"], r["int_pv"], NON_OP))
        print("       V 有杠杆 %.2f 元 | 无杠杆 %.2f 元 | 剔除回购专户 %.2f 元" % (r["v_lev"], r["v_unlev"], r["v_ex_treasury"]))
    vw = weighted()
    vw_u = weighted(levered=False)
    print("\n[加权] 熊 %.2f x%.2f + 基准 %.2f x%.2f + 牛 %.2f x%.2f = %.2f 元；P/V = %.2f"
          % (res["bear"]["v"], PROB["bear"], res["base"]["v"], PROB["base"], res["bull"]["v"], PROB["bull"], vw, PRICE / vw))
    vw_ex = sum(PROB[k] * res[k]["v_ex_treasury"] for k in PROB)
    print("       剔除回购专户：V %.2f，P/V %.2f；无杠杆口径：V %.2f，P/V %.2f" % (vw_ex, PRICE / vw_ex, vw_u, PRICE / vw_u))
    v8, v10 = weighted(0.08), weighted(0.10)
    b8, b10 = value("base", coe=0.08)["v"], value("base", coe=0.10)["v"]
    print("[敏感性] 加权 V：8%% %.2f / 9%% %.2f / 10%% %.2f；基准 V：8%% %.2f / 10%% %.2f" % (v8, vw, v10, b8, b10))
    irr = implied_irr()
    print("[隐含回报] 基准情景现金流使现值=市值的折现率 %.2f%%" % (irr * 100))
    rd = reverse_dcf()
    print("[反向 DCF] 需经营价值 %.1f；以 2026 正常化 OE %.2f 为起点，10 年复合增速 %.1f%% 后永续 2.5%%；或以 2027 OE %.2f 计永续增速 %.2f%%"
          % (rd["target_ops"], rd["oe26"], rd["x10"] * 100, rd["oe27"], rd["g_perp"] * 100))
    nb = normalize(SCEN["base"])
    ev = MCAP - NET_CASH_ADJ
    roe = nb["np"] / 54.675
    pb_fair = (roe - 0.025) / (COE - 0.025)
    print("[交叉] PE(TTM 5.33) %.1f；PE(2026 正常化 %.2f) %.1f；PB(54.68) %.2f；EV/正常化 EBIT %.1f；股息率 %.2f%%"
          % (MCAP / 5.328, nb["np"], MCAP / nb["np"], MCAP / 54.675, ev / nb["ebit"], 0.50 / PRICE * 100))
    print("       正常化 ROE %.1f%% 对应合理 PB %.2f → %.2f 元；股利 0.50 元按 2.5%% 永续增长的 DDM %.2f 元"
          % (roe * 100, pb_fair, pb_fair * 54.675 / SHARES, 0.50 * 1.025 / (COE - 0.025)))
    print("[分档价格] V 不变时：明显低估 <= %.2f；温和低估 %.2f-%.2f；大致合理 %.2f-%.2f；偏贵 > %.2f"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    b = res["base"]
    oe_g = [b["oe"][i] / b["oe"][i - 1] - 1 for i in range(1, 6)]
    print("[基准所有者收益路径] 2026 %.2f → " % b["oe"][0] + " ".join("%d:%.2f(%+.1f%%)" % (y, b["oe"][i + 1], oe_g[i] * 100) for i, y in enumerate(YEARS))
          + "；终值首年 %.2f" % b["oe_t"])
    # 三季度汇兑估计：6-30 外币净敞口按 9-30 中间价重估（USD 6.8109→6.7351，EUR 7.7671→7.6215）
    usd_net = 101.2163 + 29.6272 - 2.1335          # 百万美元：货币资金 + 应收 - 应付（2026H1_report 第 125 页）
    fx_q3 = (usd_net * (6.8109 - 6.7351) + 3.8043 * (7.7671 - 7.6215)) / 100
    print("[三季度汇兑估计] 美元净敞口 %.1f 百万美元，按 9-30 中间价重估约 -%.3f 亿元（未计三季度敞口变化）" % (usd_net, fx_q3))
    print("[证伪情景 V]")
    for k, v in variants().items():
        print("  %s：%.2f 元" % (k, v))


if __name__ == "__main__":
    main()
