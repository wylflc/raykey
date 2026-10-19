#!/usr/bin/env python3
"""晶盛机电（300316）独立估值：分部经营路径 + 所有者收益 DCF。

单位：金额亿元，每股元。输入全部写在本脚本内，运行 python3 valuation.py 复现正文与 json 的全部数字。
口径：归母；股权成本基准 9%（敏感性 8%/10%）；终值增长 2.5%；估值日 2026-10-19；
资产负债表取 2026-06-30（2026 半年报），扣除 2026-09-29 已除息的中期股利。
"""

PRICE = 31.87                 # 2026-10-19 收盘（腾讯行情）
SHARES = 13.0953              # 亿股，总股本（行情口径 = 2026-06-30 资产负债表股本）
SHARES_EX_TREASURY = 13.0735981  # 扣回购专户 2,173,984 股，用于计算已付中期股利
COE = 0.09
G_TERM = 0.025
T_FIRST = 0.70                # 2026-10-19 → 2027 年年中
YEARS = ["2026H2", 2027, 2028, 2029, 2030, 2031]

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 92、100-101、110-115 页）
BS = dict(
    cash=40.6686,                # 货币资金
    tfa=2.27,                    # 交易性金融资产（结构性存款）
    debt_inv_current=0.20,       # 一年内到期的债权投资（大额存单）
    debt_inv=3.80,               # 债权投资
    other_debt_inv=4.0022,       # 其他债权投资（大额存单）
    restricted=5.4924,           # 受限货币资金（保证金及部分存款）
    st_loan=4.3729,              # 短期借款（含保理融资 0.75）
    lt_loan_current=4.2337,      # 一年内到期的长期借款
    lt_loan=7.4881,              # 长期借款
    lease=1.2520 + 0.0390,       # 租赁负债（含一年内到期）
    jingrui_put=5.50,            # 长期应付款：晶瑞电子战略投资者股权回购款（类债务）
    buffer=5.0,                  # 经营备付（约一个月付现成本）
)
INTERIM_DPS = 0.06               # 2026 中期每股派息，2026-09-29 除息


def net_cash_adj():
    b = BS
    cash_like = b["cash"] + b["tfa"] + b["debt_inv_current"] + b["debt_inv"] + b["other_debt_inv"]
    debt = b["st_loan"] + b["lt_loan_current"] + b["lt_loan"] + b["lease"]
    div_paid = INTERIM_DPS * SHARES_EX_TREASURY
    nc = cash_like - b["restricted"] - debt - b["jingrui_put"] - div_paid - b["buffer"]
    return nc, dict(cash_like=cash_like, debt=debt, div_paid=div_paid)


# 非经营资产：中环领先（联营，账面 12.4185）与其他联营按账面 8 折；其他非流动金融资产 9 折；投资性房地产按账面
NON_OP = dict(zhonghuan=12.4185 * 0.8, other_assoc=(13.1306 - 12.4185) * 0.8,
              ofa=3.5105 * 0.9, inv_property=0.8331)


def non_op_total():
    return sum(NON_OP.values())


SEGMENTS = ["pv_core", "tesla", "semi_eq", "semi_mat", "pv_mat", "other"]
SEG_CN = dict(pv_core="光伏设备（国内+海外，除特斯拉）", tesla="特斯拉得州订单（约30亿含税，传闻）",
              semi_eq="半导体设备（集成电路+化合物）", semi_mat="半导体材料（碳化硅、蓝宝石、零部件等）",
              pv_mat="光伏耗材（石英坩埚、金刚线等）", other="其他业务")

# ---------------------------------------------------------------- 三情景
SCEN = {
    "bear": dict(
        p=0.25,
        rev=dict(pv_core=[8.0, 14.0, 18.0, 22.0, 25.0, 27.0],
                 tesla=[3.0, 13.0, 5.0, 0, 0, 0],
                 semi_eq=[16.0, 25.0, 26.0, 27.0, 28.5, 30.0],
                 semi_mat=[7.0, 13.0, 14.0, 15.0, 16.0, 17.0],
                 pv_mat=[6.0, 11.0, 11.0, 11.5, 12.0, 12.0],
                 other=[1.3, 2.5, 2.5, 2.5, 2.5, 2.5]),
        gm=dict(pv_core=[0.31, 0.32, 0.32, 0.32, 0.32, 0.32], tesla=[0.38] * 6, semi_eq=[0.38] * 6,
                semi_mat=[0.15, 0.15, 0.17, 0.18, 0.19, 0.20],
                pv_mat=[0.14, 0.14, 0.15, 0.15, 0.16, 0.16], other=[0.05] * 6),
        rd0=9.3, rd_g=-0.02, adm0=5.8, adm_g=-0.01,
        imp=[0.035, 0.032, 0.028, 0.025, 0.025, 0.025],
        tax=[0.16] * 6, minority=0.02,
        da=[5.6, 11.2, 11.3, 11.4, 11.5, 11.6],
        capex=[3.0, 7.5, 8.0, 8.5, 9.0, 9.5],
        nwc_int=0.45, dnwc_h2=3.0, roic_term=0.09,
        norm=dict(rev=dict(pv_core=28, semi_eq=26, semi_mat=12, pv_mat=12, other=2.5),
                  gm=dict(pv_core=0.32, semi_eq=0.39, semi_mat=0.17, pv_mat=0.15, other=0.08),
                  rd=9.1, adm=5.75, imp=0.025, tax=0.15, minority=0.02),
        note="光伏国内低谷延续到 2028 年后、正常年景仅约 27 亿；半导体设备在手订单消化后停在 30 亿上下且价格竞争；"
             "碳化硅微利；特斯拉订单 2 成落空或延后；研发与管理费用每年压缩 1%～2%，资本开支压到 8～9.5 亿；"
             "减值率 2.5%～3.5%；税率 16%；终值增量回报等于股权成本。",
    ),
    "base": dict(
        p=0.50,
        rev=dict(pv_core=[9.0, 18.0, 27.0, 36.0, 42.0, 44.0],
                 tesla=[6.6, 19.9, 0, 0, 0, 0],
                 semi_eq=[19.0, 30.0, 34.0, 38.0, 42.0, 45.0],
                 semi_mat=[8.0, 16.0, 19.0, 22.0, 25.0, 27.0],
                 pv_mat=[6.5, 13.0, 14.0, 15.0, 15.0, 15.0],
                 other=[1.5, 3.0, 3.0, 3.0, 3.0, 3.0]),
        gm=dict(pv_core=[0.34, 0.35, 0.35, 0.35, 0.35, 0.35], tesla=[0.42] * 6,
                semi_eq=[0.42, 0.42, 0.42, 0.425, 0.43, 0.43],
                semi_mat=[0.21, 0.22, 0.23, 0.24, 0.25, 0.26],
                pv_mat=[0.18, 0.18, 0.19, 0.20, 0.21, 0.21], other=[0.10] * 6),
        rd0=9.3, rd_g=0.05, adm0=5.8, adm_g=0.03,
        imp=[0.035, 0.028, 0.023, 0.02, 0.02, 0.02],
        tax=[0.15, 0.14, 0.14, 0.14, 0.14, 0.14], minority=0.04,
        da=[5.6, 11.3, 11.6, 11.9, 12.2, 12.5],
        capex=[3.5, 10.0, 11.0, 12.0, 12.5, 13.0],
        nwc_int=0.45, dnwc_h2=4.0, roic_term=0.12,
        norm=dict(rev=dict(pv_core=42, semi_eq=27, semi_mat=13, pv_mat=14, other=3),
                  gm=dict(pv_core=0.35, semi_eq=0.42, semi_mat=0.22, pv_mat=0.19, other=0.10),
                  rd=9.3, adm=5.8, imp=0.02, tax=0.14, minority=0.04),
        note="光伏国内 2027 年见底、2028 年起更新改造与海外扩产带动回升，2031 年 44 亿（正常年景 42 亿）；特斯拉订单 26.5 亿（不含税）"
             "2026H2 确认 25%、2027 年 75%；半导体设备由在手订单支撑 2027 年 30 亿、2031 年 45 亿；"
             "碳化硅与蓝宝石等半导体材料 2031 年 27 亿；减值率 2%；税率 14%；终值增量回报 12%。",
    ),
    "bull": dict(
        p=0.25,
        rev=dict(pv_core=[10.0, 22.0, 36.0, 48.0, 55.0, 58.0],
                 tesla=[8.0, 18.5, 15.0, 15.0, 0, 0],
                 semi_eq=[20.0, 34.0, 42.0, 50.0, 57.0, 63.0],
                 semi_mat=[9.0, 19.0, 25.0, 31.0, 37.0, 42.0],
                 pv_mat=[6.5, 14.0, 16.0, 18.0, 18.0, 18.0],
                 other=[1.5, 3.5, 3.5, 3.5, 3.5, 3.5]),
        gm=dict(pv_core=[0.36, 0.37, 0.37, 0.37, 0.37, 0.37], tesla=[0.43] * 6,
                semi_eq=[0.42, 0.43, 0.44, 0.45, 0.455, 0.46],
                semi_mat=[0.23, 0.25, 0.27, 0.29, 0.31, 0.32],
                pv_mat=[0.19, 0.21, 0.23, 0.24, 0.25, 0.25], other=[0.12] * 6),
        rd0=9.3, rd_g=0.07, adm0=5.8, adm_g=0.04,
        imp=[0.03, 0.022, 0.018, 0.018, 0.018, 0.018],
        tax=[0.145] * 6, minority=0.06,
        da=[5.6, 11.4, 12.0, 12.6, 13.2, 13.8],
        capex=[4.0, 12.0, 14.0, 15.0, 16.0, 16.0],
        nwc_int=0.40, dnwc_h2=4.0, roic_term=0.15,
        norm=dict(rev=dict(pv_core=55, semi_eq=30, semi_mat=15, pv_mat=17, other=3.5),
                  gm=dict(pv_core=0.37, semi_eq=0.43, semi_mat=0.26, pv_mat=0.24, other=0.12),
                  rd=9.5, adm=5.9, imp=0.018, tax=0.145, minority=0.06),
        note="光伏更新改造与美国扩产（特斯拉后续两期各 15 亿）推动光伏设备 2031 年 58 亿（正常年景 55 亿）；半导体设备国产替代加速至 63 亿；"
             "碳化硅受 AI 电源与 AR 光学拉动，半导体材料 42 亿、毛利率 32%；减值率 1.8%；终值增量回报 15%。",
    ),
}

SELL_RATE = 0.010         # 销售费用率
SURTAX_RATE = 0.007       # 税金及附加 / 收入
OTHER_INCOME = 0.8        # 经常性其他收益（软件退税等），年
NET_INTEREST = 0.18       # 正常化净利息（只进正常化归母净利，不进 DCF，因净现金另计）
REV_2026H1 = 34.5220


def path(s):
    """返回逐年 (收入, 毛利, 费用, 减值, 税前, 归母净利, 折旧, 资本开支, 营运资本增量, 所有者收益)。"""
    out = []
    prev_rev_annual = None
    for i, y in enumerate(YEARS):
        half = (y == "2026H2")
        rev = sum(s["rev"][k][i] for k in SEGMENTS)
        gp = sum(s["rev"][k][i] * s["gm"][k][i] for k in SEGMENTS)
        n = 0 if half else (y - 2026)
        rd = s["rd0"] * (1 + s["rd_g"]) ** n * (0.5 if half else 1.0)
        adm = s["adm0"] * (1 + s["adm_g"]) ** n * (0.5 if half else 1.0)
        opex = rd + adm + (SELL_RATE + SURTAX_RATE) * rev
        imp = s["imp"][i] * rev
        oi = OTHER_INCOME * (0.5 if half else 1.0)
        ebt = gp - opex - imp + oi
        np_parent = ebt * (1 - s["tax"][i]) * (1 - s["minority"])
        rev_annual = REV_2026H1 + rev if half else rev
        if half:
            dnwc = s["dnwc_h2"]
        else:
            dnwc = s["nwc_int"] * (rev_annual - prev_rev_annual)
        prev_rev_annual = rev_annual
        oe = np_parent + s["da"][i] - s["capex"][i] - dnwc
        out.append(dict(year=y, rev=rev, rev_annual=rev_annual, gp=gp, opex=opex, imp=imp, ebt=ebt,
                        np=np_parent, da=s["da"][i], capex=s["capex"][i], dnwc=dnwc, oe=oe))
    return out


def terminal_oe(s, rows):
    np_next = rows[-1]["np"] * (1 + G_TERM)
    rr = G_TERM / s["roic_term"]
    return np_next * (1 - rr), rr


def dcf_equity(s, r, rows=None):
    rows = rows or path(s)
    pv = 0.0
    for i, row in enumerate(rows):
        t = 0.0 if row["year"] == "2026H2" else T_FIRST + (row["year"] - 2027)
        pv += row["oe"] / (1 + r) ** t
    oe_t, _ = terminal_oe(s, rows)
    tv_end = oe_t / (r - G_TERM) * (1 + r) ** 0.5     # 2032 年年中起的永续流折到 2031 年末
    t_end = T_FIRST + 4.5                              # 2031 年末
    pv_tv = tv_end / (1 + r) ** t_end
    nc, _ = net_cash_adj()
    equity = pv + pv_tv + nc + non_op_total()
    return dict(equity=equity, v=equity / SHARES, pv_explicit=pv, pv_tv=pv_tv,
                tv_share=pv_tv / (pv + pv_tv))


def normalized_np_2026(s):
    nm = s["norm"]
    rev = sum(nm["rev"].values())
    gp = sum(nm["rev"][k] * nm["gm"][k] for k in nm["rev"])
    opex = nm["rd"] + nm["adm"] + (SELL_RATE + SURTAX_RATE) * rev
    ebt = gp - opex - nm["imp"] * rev + OTHER_INCOME + NET_INTEREST
    return ebt * (1 - nm["tax"]) * (1 - nm["minority"]), rev


def weighted(r, weights=None, scen=None):
    scen = scen or SCEN
    weights = weights or {k: v["p"] for k, v in scen.items()}
    vs = {k: dcf_equity(scen[k], r)["v"] for k in scen}
    return sum(weights[k] * vs[k] for k in scen), vs


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    s = SCEN["base"]
    rows = path(s)
    return solve(lambda r: dcf_equity(s, r, rows)["v"], 0.03, 0.20, PRICE)


def reverse_dcf(rr_growth=0.30):
    """现价隐含：以基准正常化归母净利（不含净利息）为起点，10 年增速 g、增长期再投资率固定 30%
    （与基准路径 2027-31 年 28% 相当），之后 2.5%、终值再投资率 2.5%/12%。另给隐含永续增速。"""
    s = SCEN["base"]
    np0, _ = normalized_np_2026(s)
    nm = s["norm"]
    np0 -= NET_INTEREST * (1 - nm["tax"]) * (1 - nm["minority"])
    nc = net_cash_adj()[0] + non_op_total()
    target_ev = PRICE * SHARES - nc

    def ev10(g):
        pv, npx = 0.0, np0
        for t in range(1, 11):
            npx *= (1 + g)
            pv += npx * (1 - rr_growth) / (1 + COE) ** (t - 0.3)
        oe_t = npx * (1 + G_TERM) * (1 - G_TERM / 0.12)
        pv += oe_t / (COE - G_TERM) / (1 + COE) ** (10 - 0.3)
        return pv

    g10 = solve(ev10, 0.0, 0.40, target_ev)
    np10 = np0 * (1 + g10) ** 10

    def ev_perp(g):
        return np0 * (1 + g) * (1 - g / 0.12) / (COE - g)

    gp = solve(ev_perp, 0.0, 0.0899, target_ev)
    return g10, gp, np0, target_ev, np10


def q3_estimate():
    """2026Q3 基准估计（三季报 2026-10-30 披露前）：半导体验收开始放量、特斯拉验收放在 Q4。"""
    rev = dict(pv_core=4.5, tesla=0.0, semi_eq=7.5, semi_mat=3.8, pv_mat=3.2, other=0.7)
    gm = dict(pv_core=0.34, tesla=0.42, semi_eq=0.41, semi_mat=0.21, pv_mat=0.18, other=0.10)
    r = sum(rev.values())
    gp = sum(rev[k] * gm[k] for k in rev)
    opex = 9.3 / 4 + 5.8 / 4 + (SELL_RATE + SURTAX_RATE) * r
    ebt = gp - opex - 0.025 * r + OTHER_INCOME / 4
    npq = ebt * (1 - 0.15)
    return r, gp / r, npq, 2.3224 + npq


def growth_stats(s):
    rows = path(s)
    full = [r for r in rows if r["year"] != "2026H2"]
    np_norm, _ = normalized_np_2026(s)
    reinvest = sum(r["capex"] - r["da"] + r["dnwc"] for r in full)
    rr = reinvest / sum(r["np"] for r in full)
    inc_ret = (full[-1]["np"] - np_norm) / reinvest if reinvest > 0 else float("nan")
    np2026 = 2.3224 + rows[0]["np"]
    g = []
    prev = np2026
    for r in full:
        g.append(r["np"] / prev - 1)
        prev = r["np"]
    return dict(rr=rr, inc_ret=inc_ret, growth=g, np2026=np2026, reinvest=reinvest)


def falsifier_values():
    out = {}
    # F1 半导体放缓：2026 年半导体收入 < 36 亿且年末半导体在手订单 < 40 亿含税 → 权重偏熊
    out["F1"] = weighted(COE, dict(bear=0.50, base=0.40, bull=0.10))[0]
    # F2 特斯拉订单落空：三情景都去掉特斯拉收入
    import copy
    sc = copy.deepcopy(SCEN)
    for k in sc:
        sc[k]["rev"]["tesla"] = [0.0] * 6
    out["F2"] = weighted(COE, scen=sc)[0]
    # F3 减值失控：2026 年资产+信用减值 > 6 亿 → 三情景减值率各 +1pp
    sc = copy.deepcopy(SCEN)
    for k in sc:
        sc[k]["imp"] = [x + 0.01 for x in sc[k]["imp"]]
    out["F3"] = weighted(COE, scen=sc)[0]
    # F4 三季报偏弱：前三季度归母净利 < 3.3 亿（Q3 < 1.0 亿）→ 权重偏熊
    out["F4"] = weighted(COE, dict(bear=0.40, base=0.45, bull=0.15))[0]
    # F5 美国禁令：Linton 案获初步/永久禁令 → 牛市去掉特斯拉后续订单，权重 0.30/0.55/0.15
    sc = copy.deepcopy(SCEN)
    sc["bull"]["rev"]["tesla"] = [8.0, 18.5, 0, 0, 0, 0]
    out["F5"] = weighted(COE, dict(bear=0.30, base=0.55, bull=0.15), scen=sc)[0]
    # F6 向上证伪：2027 年扣非归母 ≥ 18 亿且半导体在手订单 ≥ 70 亿含税 → 权重偏牛
    out["F6"] = weighted(COE, dict(bear=0.10, base=0.40, bull=0.50))[0]
    return out


def pv_midcycle_sensitivity():
    """光伏设备中枢取 2019-2026 年中位数约 58 亿（含 2021-24 扩产超级周期）时的基准 V 与正常化归母。"""
    import copy
    sc = copy.deepcopy(SCEN)
    sc["base"]["rev"]["pv_core"] = [9.0, 18.0, 30.0, 45.0, 55.0, 58.0]
    sc["base"]["norm"]["rev"]["pv_core"] = 58
    v_base = dcf_equity(sc["base"], COE)["v"]
    np_n, _ = normalized_np_2026(sc["base"])
    vw, _ = weighted(COE, scen=sc)
    return v_base, np_n, vw


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    nc, parts = net_cash_adj()
    print("== 资产负债表调整（亿元，2026-06-30，扣已付中期股利）")
    print(f"现金类 {parts['cash_like']:.2f}  受限 -{BS['restricted']:.2f}  有息负债 -{parts['debt']:.2f}  "
          f"晶瑞回购款 -{BS['jingrui_put']:.2f}  中期股利 -{parts['div_paid']:.2f}  经营备付 -{BS['buffer']:.2f}")
    print(f"经调整净现金 {nc:.2f}；非经营资产 {non_op_total():.2f}（中环领先 {NON_OP['zhonghuan']:.2f}）")
    print()
    for k, s in SCEN.items():
        rows = path(s)
        print(f"== {k}  p={s['p']}")
        print("年度    收入   毛利   费用   减值   税前   归母   折旧   资本开支 营运资本 所有者收益")
        for r in rows:
            print(f"{str(r['year']):7s}{r['rev']:6.1f} {r['gp']:6.2f} {r['opex']:6.2f} {r['imp']:5.2f} "
                  f"{r['ebt']:6.2f} {r['np']:6.2f} {r['da']:6.2f} {r['capex']:7.2f} {r['dnwc']:7.2f} {r['oe']:8.2f}")
        res = dcf_equity(s, COE, rows)
        oe_t, rr_t = terminal_oe(s, rows)
        np_n, rev_n = normalized_np_2026(s)
        gs = growth_stats(s)
        print(f"终值首年所有者收益 {oe_t:.2f}（终值再投资率 {rr_t:.1%}）；显性期现值 {res['pv_explicit']:.1f}，"
              f"终值现值 {res['pv_tv']:.1f}，终值占经营价值 {res['tv_share']:.0%}")
        print(f"2026 正常化归母净利 {np_n:.2f}（正常化收入 {rev_n:.1f}）；2026 估计归母 {gs['np2026']:.2f}")
        print(f"2027-31 归母同比 " + ", ".join(f"{x:+.1%}" for x in gs["growth"]) +
              f"；再投资率 {gs['rr']:.1%}，增量回报 {gs['inc_ret']:.1%}")
        print(f"V(9%) = {res['v']:.2f} 元/股；股权价值 {res['equity']:.1f} 亿元")
        print()
    vw, vs = weighted(COE)
    v8, vs8 = weighted(0.08)
    v10, vs10 = weighted(0.10)
    pv = PRICE / vw
    print("== 汇总")
    print("三情景 V(9%): " + ", ".join(f"{k} {v:.2f}" for k, v in vs.items()))
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.2f} → {verdict(pv)}")
    print("V(8%): " + ", ".join(f"{k} {v:.2f}" for k, v in vs8.items()) + f"；加权 {v8:.2f}")
    print("V(10%): " + ", ".join(f"{k} {v:.2f}" for k, v in vs10.items()) + f"；加权 {v10:.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准所有者收益流）= {irr:.2%}")
    g10, gperp, np0, ev, np10 = reverse_dcf()
    print(f"反向 DCF：现价对应经营价值 {ev:.1f} 亿；以基准正常化归母 {np0:.2f} 亿为起点，隐含 10 年增速 {g10:.1%}"
          f"（2036 年归母 {np10:.1f} 亿，之后 2.5%）；或隐含永续增速 {gperp:.1%}")
    print(f"分档价格（V 不变）：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")
    sv, snp, svw = pv_midcycle_sensitivity()
    print(f"敏感性：光伏设备中枢取 2019-26 年中位数 58 亿 → 基准 V {sv:.2f}、正常化归母 {snp:.2f}、加权 V {svw:.2f}、P/V {PRICE / svw:.2f}")
    fv = falsifier_values()
    print("证伪触发后的 V: " + ", ".join(f"{k} {v:.2f}" for k, v in fv.items()))
    mcap = PRICE * SHARES
    ev_mkt = mcap - nc - non_op_total()
    print(f"市值 {mcap:.2f} 亿；EV(扣净现金与非经营资产) {ev_mkt:.1f} 亿")
    for k in SCEN:
        npn, _ = normalized_np_2026(SCEN[k])
        nm = SCEN[k]["norm"]
        ebit = npn / (1 - nm["tax"]) / (1 - nm["minority"]) - NET_INTEREST
        print(f"  {k}: 现价/正常化归母 {mcap / npn:.1f}x；EV/正常化 EBIT {ev_mkt / ebit:.1f}x")
    bvps = 171.5383 / SHARES
    print(f"每股归母净资产 {bvps:.2f}；现价 PB {PRICE / bvps:.2f}x；加权 V 对应 PB {vw / bvps:.2f}x")
    print(f"近 12 个月股息 0.21 元/股，股息率 {0.21 / PRICE:.2%}；2026 年无回购")
    qr, qgm, qnp, q9 = q3_estimate()
    print(f"2026Q3 基准估计：营收 {qr:.1f} 亿，毛利率 {qgm:.1%}，归母（不含非经常）{qnp:.2f} 亿，前三季度归母约 {q9:.2f} 亿")


if __name__ == "__main__":
    main()
