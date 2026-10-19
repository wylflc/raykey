#!/usr/bin/env python3
"""阳光电源（300274）独立估值（OI-291 池内独立审计 b02，价格日 2026-10-19）。

运行：python3 valuation.py
打印：2026 正常化归母净利三档、增长路径、三情景 V、加权 V、P/V、8%/10% 下的 V、
现价隐含回报、反向 DCF、交叉验证与证伪条件触发后的 V。
金额单位：亿元；每股：元。全部输入写在本脚本内，出处见正文第 9 节。
"""

PRICE = 77.68            # 2026-10-19 收盘，A 股未复权（数据包快照）
SHARES = 20.7321         # 总股本 2,073,211,424 股（含回购专户 1,572.7 万股，留作员工持股），无 H 股
COE = 0.09
PROBS = {"bear": 0.30, "base": 0.50, "bull": 0.20}

# ---------------------------------------------------------------- 经调整净现金
# 2026H1 合并资产负债表（2026H1_report 第 86-88 页）及附注
CASH_LIKE = {
    "货币资金": 315.23,
    "减：受限货币资金（冻结、保证金，附注26）": -6.63,
    "理财产品（交易性金融资产内）": 26.13,
    "远期结售汇（交易性金融资产内）": 0.30,
    "衍生金融资产": 0.24,
    "一年内到期的大额存单": 2.01,
}
DEBT_LIKE = {
    "短期借款": 25.42,
    "长期借款（含一年内到期及利息）": 38.37,
    "租赁负债（含一年内到期）": 3.97,
    "长期应付款（融资租赁、附回购条款投资款、非金融机构借款，含一年内到期）": 18.92,
    "交易性金融负债": 1.40,
    "衍生金融负债（商品期货）": 2.40,
}
POST_BS = {
    "2026 中期股利（2026-09-21 除息派发）": 13.17,
    "回购支出（截至 2026-09-30）": 3.25,
}
TTM_REVENUE = 765.63
OPERATING_RESERVE_RATE = 0.05   # 经营备付：TTM 营收的 5%
NON_OPERATING = {
    "权益工具投资（交易性金融资产内）": 14.03,
    "其他非流动金融资产": 14.16,
    "长期股权投资": 7.69,
}
NON_OP_HAIRCUT = 0.20            # 非上市股权与基金份额折价 20%


def net_cash_adjusted():
    cash = sum(CASH_LIKE.values())
    debt = sum(DEBT_LIKE.values())
    post = sum(POST_BS.values())
    reserve = OPERATING_RESERVE_RATE * TTM_REVENUE
    net = cash - debt - post - reserve
    nonop = sum(NON_OPERATING.values()) * (1 - NON_OP_HAIRCUT)
    return {"cash": cash, "debt": debt, "post": post, "reserve": reserve,
            "net_cash_adj": net, "non_op": nonop, "total": net + nonop}


# ---------------------------------------------------------------- 情景参数
# 2026N = 2026 年正常化（中枢毛利率、剔除公允价值变动收益与汇兑等一次性项目，含净利息）
# 美国占比：2025 年美国阳光营收 172.47 亿（经审计，约占总营收 19%；担保额度公告 2026-04-01 第 4 页），公司 2025-04 口径
# 美国占总收入一到二成；2026N 假设美国占储能收入 25%、逆变器收入 12%，美国毛利率高 5/4 个百分点。
SCEN = {
    "base": dict(
        st_rev=375.0, st_gm=0.28, inv_rev=265.0, inv_gm=0.375,
        oth_rev=96.0, oth_gp=17.8, opex=103.0, imp_rate=0.019,
        oth_inc=[3.5, 3.5, 2.0, 2.0, 2.0, 2.0], net_int=5.5, inv_inc=2.0, tax=0.175, minority=-0.3,
        us_st=0.25, us_inv=0.12, us_prem_st=0.05, us_prem_inv=0.04,
        us_path=[1.00, 0.90, 0.35, 0.15, 0.10],           # 2027-2031 美国规模相对 2026N
        st_vol_nonus=[0.18, 0.15, 0.12, 0.10, 0.08],      # 非美储能出货量增速
        st_asp=[0.00, -0.03, -0.03, -0.03, -0.03],        # 储能单价变化
        st_gm_path=[0.26, 0.26, 0.26, 0.26, 0.26],        # 混合储能毛利率中枢（2027 起电池出口退税取消、锂电消费税）
        inv_g_nonus=[0.03, 0.03, 0.03, 0.03, 0.03],
        aidc_rev=[5.0, 20.0, 40.0, 60.0, 80.0], aidc_gm=0.30, aidc_opex=0.10,
        oth_g=0.02, opex_g=0.03,
        intensity=0.30, release=0.5, g_term=0.025, ronic_term=0.15,
        note="储能毛利率中枢 28%（2027 起 26%），逆变器 37.5%；美国 2029 年起安全港结束降至 35%/15%/10%；"
             "非美储能量增 18%→8%；AIDC 2031 年营收 80 亿",
    ),
    "bear": dict(
        st_rev=350.0, st_gm=0.23, inv_rev=255.0, inv_gm=0.34,
        oth_rev=89.0, oth_gp=15.0, opex=100.0, imp_rate=0.023,
        oth_inc=[3.0, 3.0, 1.5, 1.5, 1.5, 1.5], net_int=5.0, inv_inc=1.5, tax=0.18, minority=-0.3,
        us_st=0.25, us_inv=0.12, us_prem_st=0.05, us_prem_inv=0.04,
        us_path=[0.80, 0.50, 0.15, 0.05, 0.05],
        st_vol_nonus=[0.10, 0.08, 0.07, 0.06, 0.05],
        st_asp=[-0.03, -0.03, -0.03, -0.03, -0.03],
        st_gm_path=[0.21, 0.21, 0.21, 0.21, 0.21],
        inv_g_nonus=[-0.03, 0.00, 0.00, 0.01, 0.01],      # 欧盟高风险供应商限制扩大
        aidc_rev=[2.0, 5.0, 10.0, 15.0, 20.0], aidc_gm=0.25, aidc_opex=0.12,
        oth_g=-0.03, opex_g=-0.01,
        intensity=0.32, release=0.5, g_term=0.010, ronic_term=0.10,
        note="储能沦为大宗集成（毛利率 23%→21%），逆变器 34%；美国 2029 年后只剩 5%；"
             "欧盟限制扩至非公共资金项目；费用每年压降 1%；AIDC 只到 20 亿",
    ),
    "bull": dict(
        st_rev=395.0, st_gm=0.31, inv_rev=275.0, inv_gm=0.40,
        oth_rev=101.0, oth_gp=20.0, opex=106.0, imp_rate=0.015,
        oth_inc=[4.0, 4.0, 2.5, 2.5, 2.5, 2.5], net_int=6.0, inv_inc=2.5, tax=0.17, minority=-0.3,
        us_st=0.25, us_inv=0.12, us_prem_st=0.05, us_prem_inv=0.04,
        us_path=[1.00, 1.00, 0.60, 0.45, 0.40],
        st_vol_nonus=[0.25, 0.20, 0.15, 0.12, 0.10],
        st_asp=[0.02, -0.02, -0.02, -0.02, -0.02],
        st_gm_path=[0.30, 0.30, 0.30, 0.30, 0.30],
        inv_g_nonus=[0.05, 0.05, 0.05, 0.05, 0.05],
        aidc_rev=[8.0, 35.0, 70.0, 110.0, 150.0], aidc_gm=0.32, aidc_opex=0.09,
        oth_g=0.05, opex_g=0.05,
        intensity=0.28, release=0.5, g_term=0.025, ronic_term=0.20,
        note="储能溢价守住（毛利率 31%→30%），逆变器 40%；美国经合作保留四成；"
             "非美储能量增 25%→10%；AIDC 2031 年营收 150 亿",
    ),
}
YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
FADE_YEARS = [2032, 2033, 2034, 2035, 2036]

# 2026 上半年实际（2026H1_report 第 34-35、91 页）：上半年利润已在 6 月末净资产内，估值只计下半年。
# 下半年正常化利润 = 全年 2026N − 上半年按同一情景毛利率中枢重算的正常化利润（上半年营收低、费用均摊，
# 不能简单取全年的一半）。
H1 = dict(st_rev=154.56, inv_rev=123.88, oth_rev=30.68, oth_gp=7.99, surcharge=1.28, opex=49.75)


def h1_normalized_op(s):
    gp = H1["st_rev"] * s["st_gm"] + H1["inv_rev"] * s["inv_gm"] + H1["oth_gp"]
    rev = H1["st_rev"] + H1["inv_rev"] + H1["oth_rev"]
    pbt_op = gp - H1["surcharge"] - H1["opex"] - s["imp_rate"] * rev + s["oth_inc"][0] / 2
    return pbt_op * (1 - s["tax"]) - s["minority"] / 2


def build(s):
    """逐年计算营收、归母净利（2026N 与 2027-2031）。"""
    rows = []
    # 2026N 拆分美国与非美
    st_us0, inv_us0 = s["st_rev"] * s["us_st"], s["inv_rev"] * s["us_inv"]
    st_nonus0, inv_nonus0 = s["st_rev"] - st_us0, s["inv_rev"] - inv_us0
    gm_st_nonus0 = s["st_gm"] - s["us_st"] * s["us_prem_st"]
    gm_inv_nonus0 = s["inv_gm"] - s["us_inv"] * s["us_prem_inv"]
    st_nonus, inv_nonus, asp = st_nonus0, inv_nonus0, 1.0
    oth_rev, oth_gp, opex = s["oth_rev"], s["oth_gp"], s["opex"]
    for i, y in enumerate(YEARS):
        if i == 0:
            us_mult, gm_st_nonus, aidc = 1.0, gm_st_nonus0, 0.0
            st_rev_y = s["st_rev"]
            st_gp = st_nonus0 * gm_st_nonus0 + st_us0 * (gm_st_nonus0 + s["us_prem_st"])
            inv_rev_y = s["inv_rev"]
            inv_gp = inv_nonus0 * gm_inv_nonus0 + inv_us0 * (gm_inv_nonus0 + s["us_prem_inv"])
        else:
            k = i - 1
            us_mult = s["us_path"][k]
            asp *= 1 + s["st_asp"][k]
            st_nonus *= 1 + s["st_vol_nonus"][k]
            gm_st_nonus = s["st_gm_path"][k] - s["us_st"] * s["us_prem_st"]
            st_nonus_rev = st_nonus * asp
            st_us_rev = st_us0 * us_mult * asp
            st_rev_y = st_nonus_rev + st_us_rev
            st_gp = st_nonus_rev * gm_st_nonus + st_us_rev * (gm_st_nonus + s["us_prem_st"])
            inv_nonus *= 1 + s["inv_g_nonus"][k]
            inv_us_rev = inv_us0 * us_mult
            inv_rev_y = inv_nonus + inv_us_rev
            inv_gp = inv_nonus * gm_inv_nonus0 + inv_us_rev * (gm_inv_nonus0 + s["us_prem_inv"])
            aidc = s["aidc_rev"][k]
            oth_rev *= 1 + s["oth_g"]
            oth_gp *= 1 + s["oth_g"]
            opex *= 1 + s["opex_g"]
        aidc_gp = aidc * s["aidc_gm"]
        aidc_opex = aidc * s["aidc_opex"]
        rev = st_rev_y + inv_rev_y + oth_rev + aidc
        gp = st_gp + inv_gp + oth_gp + aidc_gp
        surcharge = 0.0045 * rev
        imp = s["imp_rate"] * rev
        pbt = gp - surcharge - opex - aidc_opex - imp + s["oth_inc"][i] + s["net_int"] + s["inv_inc"]
        np_cons = pbt * (1 - s["tax"])
        parent = np_cons - s["minority"]
        # 估值用经营利润：扣除税后净利息与投资收益（对应的现金与股权已在净现金、非经营资产中按账面计入，避免重复）
        parent_op = parent - (s["net_int"] + s["inv_inc"]) * (1 - s["tax"])
        rows.append(dict(year=y, rev=rev, st_rev=st_rev_y, st_gm=st_gp / st_rev_y, inv_rev=inv_rev_y,
                         inv_gm=inv_gp / inv_rev_y, aidc=aidc, gp=gp, opex=opex + aidc_opex, imp=imp,
                         pbt=pbt, parent=parent, parent_op=parent_op, us_mult=us_mult))
    return rows


def cash_flows(s):
    """归母所有者收益：经营净利（扣净利息与投资收益）− 增长再投资（当年营收增量 × 资本强度；营收下降时按 50% 释放）。"""
    rows = build(s)
    g31 = rows[-1]["parent_op"] / rows[-2]["parent_op"] - 1
    # 2032-2036 增速由 2031 年线性收敛到终值增速
    fade_g = [g31 + (s["g_term"] - g31) * (j + 1) / len(FADE_YEARS) for j in range(len(FADE_YEARS))]
    path = [(r["year"], r["parent_op"], r["rev"]) for r in rows]
    for y, g in zip(FADE_YEARS, fade_g):
        _, p, rv = path[-1]
        path.append((y, p * (1 + g), rv * (1 + g)))
    flows = []
    for i, (y, p, rv) in enumerate(path):
        if i == 0:
            reinv = 0.0   # 2026 下半年：上半年存货与预付已增加 83 亿备货，计入 6 月末净现金，不再另扣
        else:
            d = rv - path[i - 1][2]   # 当年营收增量 × 资本强度；营收下降时按比例释放营运资金
            reinv = s["intensity"] * d if d > 0 else s["intensity"] * d * s["release"]
        flows.append(dict(year=y, parent=p, rev=rv, reinv=reinv, oe=p - reinv))
    np_term = path[-1][1] * (1 + s["g_term"])
    oe_term = np_term * (1 - s["g_term"] / s["ronic_term"])
    return rows, flows, oe_term, fade_g


def times(year):
    """估值日 2026-10-19：2026 下半年现金流按年末（0.2 年）计；以后各年按年中计（2027 年为 0.7 年）。"""
    return 0.2 if year == 2026 else (year - 2027) + 0.7


def value(s, r, net):
    rows, flows, oe_term, _ = cash_flows(s)
    pv = 0.0
    for f in flows:
        cf = (f["oe"] - h1_normalized_op(s)) if f["year"] == 2026 else f["oe"]   # 2026 只计下半年
        pv += cf / (1 + r) ** times(f["year"])
    tv = oe_term / (r - s["g_term"])
    pv_tv = tv / (1 + r) ** times(FADE_YEARS[-1])
    eq = pv + pv_tv + net
    return dict(v=eq / SHARES, pv_flows=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv), equity=eq)


def solve(fn, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (fn(mid) - target) * (fn(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def weighted(r, net, probs=PROBS, scen=SCEN):
    return sum(probs[k] * value(scen[k], r, net)["v"] for k in probs)


def implied_irr(s, net):
    """使现值等于现价的折现率；区间内无解时返回 None（现价高于该情景在任何合理折现率下的价值）。"""
    lo, hi = s["g_term"] + 0.005, 0.30
    f = lambda r: value(s, r, net)["v"] - PRICE
    if f(lo) * f(hi) > 0:
        return None
    return solve(lambda r: value(s, r, net)["v"], lo, hi, PRICE)


def reverse_dcf(net):
    """现价隐含：(1) 基准 2026N 利润的永续增速；(2) 10 年不变增速 + 2.5% 终值。"""
    base = SCEN["base"]
    np0 = build(base)[0]["parent_op"]      # 经营口径（扣税后净利息与投资收益），与扣净现金后的经营价值对应
    ev_price = PRICE * SHARES - net
    ronic = base["ronic_term"]

    def gordon(g):
        return np0 * (1 + g) * (1 - g / ronic) / (COE - g)
    g_perp = solve(gordon, -0.10, 0.085, ev_price)

    def ten_year(g):
        pv, p = 0.0, np0
        for t in range(1, 11):
            p *= 1 + g
            pv += p * (1 - max(g, 0) / 0.30) / (1 + COE) ** (t - 0.3)
        tv = p * 1.025 * (1 - 0.025 / ronic) / (COE - 0.025)
        return pv + tv / (1 + COE) ** (10 - 0.3)
    g10 = solve(ten_year, -0.15, 0.30, ev_price)
    return np0, ev_price, g_perp, g10


def main():
    nc = net_cash_adjusted()
    net = nc["total"]
    print("=== 经调整净现金（亿元） ===")
    print(f"现金类 {nc['cash']:.2f} − 有息及类债务 {nc['debt']:.2f} − 期后股利与回购 {nc['post']:.2f} "
          f"− 经营备付 {nc['reserve']:.2f} = {nc['net_cash_adj']:.2f}；非经营资产（折价后）{nc['non_op']:.2f}；"
          f"合计 {net:.2f}（每股 {net / SHARES:.2f} 元）")

    print("\n=== 2026 正常化归母净利与增长路径（亿元） ===")
    for k in ("bear", "base", "bull"):
        rows, flows, oe_term, fade_g = cash_flows(SCEN[k])
        r0 = rows[0]
        print(f"[{k}] 2026N 营收 {r0['rev']:.0f}，储能 {r0['st_rev']:.0f}（毛利率 {r0['st_gm']:.1%}），"
              f"逆变器等 {r0['inv_rev']:.0f}（{r0['inv_gm']:.1%}），税前 {r0['pbt']:.1f}，归母 {r0['parent']:.1f}")
        line = []
        for a, b in zip(rows[:-1], rows[1:]):
            line.append(f"{b['year']} {b['parent']:.1f}（{b['parent'] / a['parent'] - 1:+.1%}，储能毛利率 {b['st_gm']:.1%}，"
                        f"美国 {b['us_mult']:.0%}，AIDC {b['aidc']:.0f}）")
        print("   " + "；".join(line))
        tot_np = sum(f["parent"] for f in flows[1:6])
        tot_re = sum(f["reinv"] for f in flows[1:6])
        dnp = rows[-1]["parent_op"] - rows[0]["parent_op"]
        inc_txt = f"{dnp / tot_re:.0%}" if tot_re > 0 and dnp > 0 else "为负（美国退出与价格冲击压过再投资）"
        oe = [f["oe"] for f in flows]
        print(f"   2026 上半年正常化经营归母 {h1_normalized_op(SCEN[k]):.1f}，下半年计入估值 {rows[0]['parent_op'] - h1_normalized_op(SCEN[k]):.1f}")
        print(f"   估值用经营归母（扣税后净利息与投资收益）2026N {rows[0]['parent_op']:.1f}；"
              f"所有者收益 2027-31：{', '.join(f'{x:.1f}' for x in oe[1:6])}；2036 年 {oe[-1]:.1f}；终值首年 {oe_term:.1f}")
        print(f"   2032-36 净利增速 {', '.join(f'{g:.1%}' for g in fade_g)}；终值增速 {SCEN[k]['g_term']:.1%}；"
              f"2027-31 再投资率 {tot_re / tot_np:.1%}，增量回报 {inc_txt}；终值 RONIC {SCEN[k]['ronic_term']:.0%}")

    print("\n=== 三情景 V（股权成本 9%） ===")
    vals = {}
    for k in ("bear", "base", "bull"):
        res = value(SCEN[k], COE, net)
        vals[k] = res["v"]
        print(f"{k}: V = {res['v']:.2f} 元/股（概率 {PROBS[k]:.0%}；终值占比 {res['tv_share']:.0%}）  {SCEN[k]['note']}")
    vw = weighted(COE, net)
    pv = PRICE / vw
    band = "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.3f}（{band}）")
    print(f"V 不变时各档价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n=== 股权成本敏感性 ===")
    for r in (0.08, 0.10):
        parts = "，".join(f"{k} {value(SCEN[k], r, net)['v']:.2f}" for k in ("bear", "base", "bull"))
        print(f"{r:.0%}：加权 V = {weighted(r, net):.2f}（{parts}）")

    irr = implied_irr(SCEN["base"], net)
    print(f"\n=== 现价隐含回报（基准情景所有者收益流 + 终值 + 净现金） === {irr:.2%}")
    for k in ("bear", "bull"):
        x = implied_irr(SCEN[k], net)
        txt = f"{x:.2%}" if x is not None else f"低于 {SCEN[k]['g_term'] + 0.005:.1%}（无解）"
        print(f"   参考：{k} 情景下现价隐含回报 {txt}")

    np0, ev_price, g_perp, g10 = reverse_dcf(net)
    print(f"\n=== 反向 DCF === 现价扣净现金后经营价值 {ev_price:.0f} 亿；以基准 2026N 经营归母 {np0:.1f} 亿为起点："
          f"隐含永续增速 {g_perp:.2%}；或未来 10 年年均增速 {g10:.2%} 后接 2.5% 终值")

    print("\n=== 交叉验证 ===")
    mcap = PRICE * SHARES
    base_rows = build(SCEN["base"])
    ebit_n = base_rows[0]["pbt"] - SCEN["base"]["net_int"] - SCEN["base"]["inv_inc"]
    np_n = base_rows[0]["parent"]
    print(f"市值 {mcap:.1f} 亿；EV {mcap - net:.1f} 亿；EV/正常化 EBIT {(mcap - net) / ebit_n:.1f}×；"
          f"PE（基准 2026N 归母 {np_n:.1f}）{mcap / np_n:.1f}×；EV/经营归母 {(mcap - net) / np0:.1f}×")
    print(f"PE(TTM 归母 109.85) {mcap / 109.85:.1f}×；PE(TTM 扣非 96.09) {mcap / 96.09:.1f}×；PB(归母权益 501.40) {mcap / 501.40:.2f}×")
    print(f"股息率（过去 12 个月每股 2.28 元）{2.28 / PRICE:.2%}；回购 3.25 亿占市值 {3.25 / mcap:.2%}")

    print("\n=== 敏感性（股权成本 9%） ===")
    import copy
    sa = copy.deepcopy(SCEN)
    for k in sa:
        sa[k]["us_st"], sa[k]["us_inv"] = 0.15, 0.08
    print(f"美国占比改为储能 15%、逆变器 8%：加权 V = {weighted(COE, net, PROBS, sa):.2f}")
    sb = copy.deepcopy(SCEN)
    sb["base"]["us_path"] = [1.0, 1.0, 0.7, 0.55, 0.5]
    print(f"基准美国 2031 年保留五成：基准 V = {value(sb['base'], COE, net)['v']:.2f}，加权 V = {weighted(COE, net, PROBS, sb):.2f}")
    sc = copy.deepcopy(SCEN)
    for k in sc:
        sc[k]["us_prem_st"], sc[k]["us_prem_inv"] = 0.0, 0.0
    print(f"美国毛利率不设溢价：加权 V = {weighted(COE, net, PROBS, sc):.2f}")
    print(f"概率改为 25/50/25：加权 V = {weighted(COE, net, {'bear': 0.25, 'base': 0.50, 'bull': 0.25}):.2f}")

    print("\n=== 证伪条件触发后的 V（股权成本 9%） ===")
    # F1 储能毛利率：2026 年报储能系统毛利率 < 28%，或 2027 中报 < 25% → 基准与牛市储能毛利率中枢各降 3 个百分点
    s1 = copy.deepcopy(SCEN)
    for k in ("base", "bull"):
        s1[k]["st_gm"] -= 0.03
        s1[k]["st_gm_path"] = [x - 0.03 for x in s1[k]["st_gm_path"]]
    print(f"F1 储能毛利率中枢降 3pp：加权 V = {weighted(COE, net, PROBS, s1):.2f}")
    # F2 储能出货：2026 全年储能发货 < 50GWh 或储能收入 < 330 亿（2027-04-30 年报）→ 概率 45/45/10
    p2 = {"bear": 0.45, "base": 0.45, "bull": 0.10}
    print(f"F2 储能出货不及 50GWh：加权 V = {weighted(COE, net, p2):.2f}")
    # F3 欧盟：高风险供应商限制扩大到非欧盟资金的光伏与储能项目（2027-12-31 前立法通过）→ 基准非美增速减半、概率 45/45/10
    s3 = copy.deepcopy(SCEN)
    s3["base"]["st_vol_nonus"] = [x / 2 for x in s3["base"]["st_vol_nonus"]]
    s3["base"]["inv_g_nonus"] = [-0.02, -0.02, 0.0, 0.01, 0.01]
    p3 = {"bear": 0.45, "base": 0.45, "bull": 0.10}
    print(f"F3 欧盟限制扩大：加权 V = {weighted(COE, net, p3, s3):.2f}")
    # F4 美国提前关闭：已获授权型号被撤销/禁售，或 2027 年美国收入 < 2026 年的一半（2028-04-30 年报）
    s4 = copy.deepcopy(SCEN)
    s4["base"]["us_path"] = [0.40, 0.15, 0.05, 0.0, 0.0]
    s4["bear"]["us_path"] = [0.20, 0.0, 0.0, 0.0, 0.0]
    s4["bull"]["us_path"] = [0.70, 0.50, 0.35, 0.30, 0.30]
    print(f"F4 美国提前关闭：加权 V = {weighted(COE, net, PROBS, s4):.2f}")
    # F5 向上：2026Q3 扣非归母 ≥ 30 亿且 2026 全年储能毛利率 ≥ 31%，并有 AIDC（SST/HVDC）批量订单公告（2027-06-30 前）→ 概率 20/50/30
    p5 = {"bear": 0.20, "base": 0.50, "bull": 0.30}
    print(f"F5 向上验证：加权 V = {weighted(COE, net, p5):.2f}")


if __name__ == "__main__":
    main()
