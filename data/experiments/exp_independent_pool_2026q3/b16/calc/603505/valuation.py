# -*- coding: utf-8 -*-
"""金石资源（603505）独立估值（OI-291 b16，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位亿元，价格与每股价值元/股。输入全部写在脚本内，来源见正文《603505_金石资源.md》。

方法：分部正常化 2026 年归母净利（含净利息，剔除停产等一次性影响）
-> 加回归母口径税后利息得经营所有者收益（剔除诺亚权益法收益，诺亚按非经营资产另计）
-> 2027-2031 逐年增长、按再投资率扣除再投资 -> 终值（增长 ≤2.5%）
-> 有杠杆口径（经调整净现金为负）：减去归母口径净负债税后利息的永续现值，加非经营资产与过渡期调整。
同时给出无杠杆口径（全额扣净负债）与“按合并口径净负债”两种对照。
"""

PRICE = 12.65                 # 2026-10-20 收盘
SHARES = 8.4167               # 亿股，总股本（含回购专户 2,136,799 股）
TREASURY = 0.02136799         # 亿股，回购专户（2024 年回购，未公告注销）
COE = 0.09
SCEN_P = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# ---------------- 资产负债表（2026-06-30，2026H1_report 第 35-37、17、94-99 页） ----------------
CASH = 6.56                   # 货币资金
RESTRICTED = 1.45             # 受限货币资金：票据保证金 1.27、环境治理基金 0.16、冻结 0.02
OPER_RESERVE = 1.00           # 经营备付（约营收 2.5%）
DIV_PAYABLE = 0.42            # 应付股利（2025 年度分红，7-16 已付）
DEBT = 38.42                  # 短借 17.94 + 长借 11.15 + 一年内到期 9.27 + 租赁 0.06
DEBT_LIKE = 0.20              # 预计负债
NET_CASH_ADJ = CASH - RESTRICTED - OPER_RESERVE - DIV_PAYABLE - DEBT - DEBT_LIKE   # 合并口径 = -34.93
MINORITY_ND = 5.40            # 金鄂博（少数股东 49%）净负债约 11 亿 x 49%（估计，见正文）
ND_ATTR = -NET_CASH_ADJ - MINORITY_ND                 # 归母口径经调整净负债 = 29.53
RATE = 0.030                  # 有息负债实际平均利率：2025 利息 0.964/平均负债 31.2；H1'26 年化 1.107/36.7
SHIELD = 0.15                 # 利息税盾（母公司应税所得少，金鄂博 15% 税率）
INT_AT = ND_ATTR * RATE * (1 - SHIELD)                # 归母口径税后利息 ≈ 0.753

# ---------------- 非经营资产 ----------------
NOAH_BV = 2.64 + 0.088        # 诺亚液冷：6-30 账面 2.64 + 8 月受让 45 万股（按入股成本 19.6 元/股估）
OTHER_FIN = 0.12              # 其他权益工具投资 0.06 + 其他非流动金融资产 0.06
POWDER_COST = 1491.6          # 包钢金石→金鄂博 萤石粉暂定单价（元/吨，不含税）
EXCESS_POWDER_6M30 = 32 - 8   # 金鄂博库存萤石粉 32 万吨，正常周转约 8 万吨
H2_BUILD = 20                 # 2026H2 金鄂博停产期间净增库存（万吨，估计）
EXCESS_INV_ATTR = EXCESS_POWDER_6M30 * POWDER_COST / 1e4 * 0.51   # 1.83 亿
H2_BUILD_ATTR = H2_BUILD * POWDER_COST / 1e4 * 0.51               # 1.52 亿

# ---------------- 分部参数（2026 正常化，熊/基准/牛） ----------------
REAL = 0.81        # 公司萤石精矿不含税实现价 / 97% 酸级精粉含税市场均价（2025: 2767/3426=0.808；2024: 2807/3440=0.816）
RES_TAX = 0.04     # 资源税及附加占矿山收入
FIX_OH = 1.45      # 单一矿山固定费用（2025 实际 1.395 = 期间费用及税金 1.857 - 资源税等 0.462）
MINE_INT = 0.62    # 单一矿山分部分摊利息（2025 为 0.58，《提质增效2.0》表 1-2）
MINE_TAX = 0.20    # 所得税 + 少数股东（2025 实际 (2.546-2.037)/2.546 = 20%）
TRADE_NP_T = 450   # 金鄂博外销包钢金石萤石粉每吨归母净利（H1'25 7.8 万吨 ↔ 约 3,500 万元）

S = {
    "bear": dict(
        p_fl=3000, vol=37.0, cogs=1700,           # 萤石含税均价、单一矿山销量（万吨）、单位成本（元/吨）
        bg_vol=68, bg_np_t=380,                    # 包钢金石销量（万吨）与每吨净利（元）
        ahf_vol=21.0, ahf_np_t=80,                 # 金鄂博 AHF 销量（万吨）与每吨净利（不含外销萤石粉）
        trade=0.0, elim=-0.10,                     # 外销萤石粉（万吨/年）与未实现利润抵销拖累
        lith=-0.41, hunan=-0.06, mongo=-0.10, noah=0.08, hq=-0.30,
        g=[0.03, 0.03, 0.02, 0.02, 0.02], rr=[0.30, 0.30, 0.30, 0.30, 0.30], gT=0.015, roicT=0.08,
        inv_f=0.2, noah_mult=0.8,
        q3=-0.45, q4_short=-1.06, y27_short=-1.10),
    "base": dict(
        p_fl=3400, vol=40.0, cogs=1640,
        bg_vol=74, bg_np_t=430,
        ahf_vol=23.0, ahf_np_t=250,
        trade=4.0, elim=-0.05,
        lith=-0.17, hunan=-0.04, mongo=-0.05, noah=0.14, hq=-0.25,
        g=[0.06, 0.06, 0.05, 0.04, 0.03], rr=[0.35, 0.35, 0.35, 0.30, 0.30], gT=0.02, roicT=0.10,
        inv_f=0.5, noah_mult=1.0,
        q3=-0.30, q4_short=-0.78, y27_short=-0.43),
    "bull": dict(
        p_fl=3800, vol=43.0, cogs=1600,
        bg_vol=78, bg_np_t=465,
        ahf_vol=24.5, ahf_np_t=450,
        trade=12.0, elim=0.0,
        lith=0.04, hunan=-0.01, mongo=0.0, noah=0.20, hq=-0.22,
        g=[0.10, 0.09, 0.07, 0.05, 0.04], rr=[0.40, 0.40, 0.40, 0.35, 0.35], gT=0.025, roicT=0.15,
        inv_f=1.0, noah_mult=1.5,
        q3=-0.15, q4_short=-0.45, y27_short=-0.25),
}


def segments(c):
    """2026 正常化归母净利（含净利息、含诺亚权益法收益，剔除停产等一次性影响）。"""
    real = c["p_fl"] * REAL
    rev = c["vol"] * real / 1e4
    gp = c["vol"] * (real - c["cogs"]) / 1e4
    ebit_mine = gp - RES_TAX * rev - FIX_OH
    mine = (ebit_mine - MINE_INT) * (1 - MINE_TAX)
    bg = 0.43 * c["bg_vol"] * c["bg_np_t"] / 1e4
    jeb = 0.51 * c["ahf_vol"] * c["ahf_np_t"] / 1e4
    trade = c["trade"] * TRADE_NP_T / 1e4
    chain = bg + jeb + trade + c["elim"]
    other = c["lith"] + c["hunan"] + c["mongo"] + c["noah"] + c["hq"]
    np_ = mine + chain + other
    return dict(real=real, rev_mine=rev, ebit_mine=ebit_mine, mine=mine, bg=bg, jeb=jeb, trade=trade,
                chain=chain, other=other, np=np_)


def transition(c):
    """过渡期调整：三季度实际（估）+ 四季度与 2027H1 相对正常化的缺口 + 2026H2 萤石粉增库存的折价损失。"""
    return c["q3"] + c["q4_short"] + c["y27_short"] - H2_BUILD_ATTR * (1 - c["inv_f"])


def nonop(c):
    return NOAH_BV * c["noah_mult"] + OTHER_FIN + EXCESS_INV_ATTR * c["inv_f"]


def value(c, k=COE, mode="lev", nd=None):
    """mode: lev = 有杠杆口径（框架）；unlev = 全额扣除净负债。nd: 覆盖归母净负债。"""
    nd = ND_ATTR if nd is None else nd
    int_at = nd * RATE * (1 - SHIELD)
    seg = segments(c)
    ebiat = seg["np"] - c["noah"] + INT_AT          # 经营（税后、息前、归母）收益
    flows = []
    oe26 = ebiat * (1 - c["rr"][0])
    pv = 0.25 * oe26                                 # 2026Q4 按 t=0 计入
    e = ebiat
    for t in range(5):                               # 2027..2031，年末折现
        e *= 1 + c["g"][t]
        oe = e * (1 - c["rr"][t])
        flows.append((2027 + t, e, oe))
        pv += oe / (1 + k) ** (t + 1)
    rT = c["gT"] / c["roicT"]
    tv = e * (1 + c["gT"]) * (1 - rT) / (k - c["gT"])
    tv_pv = tv / (1 + k) ** 5
    pv_ops = pv + tv_pv
    debt = int_at / k if mode == "lev" else nd
    eq = pv_ops + nonop(c) + transition(c) - debt
    return dict(v=eq / SHARES, v_ex_treasury=eq / (SHARES - TREASURY), eq=eq, pv_ops=pv_ops, tv_pv=tv_pv,
                tv_share=tv_pv / pv_ops, debt=debt, ebiat=ebiat, oe26=oe26, flows=flows, seg=seg)


def weighted(k=COE, mode="lev", probs=None, scen=None, nd=None):
    probs = probs or SCEN_P
    scen = scen or S
    return sum(probs[s] * value(scen[s], k, mode, nd)["v"] for s in scen)


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
    """基准情景：使有杠杆口径每股价值等于现价的折现率（终值与利息永续现值同步按该率计算）。"""
    return solve(lambda k: value(S["base"], k)["v"], 0.03, 0.20, PRICE)


def reverse_dcf(rr=0.35, gT=0.025, k=COE):
    """现价隐含（10 年）：基准 2026 正常化经营收益起，2027-2036 年增速 g、再投资率固定 35%，
    之后 2.5% 永续（再投资率 2.5%/10%）；有杠杆口径，非经营资产与过渡调整同基准。"""
    c = S["base"]
    seg = segments(c)
    ebiat0 = seg["np"] - c["noah"] + INT_AT

    def v(g):
        pv = 0.25 * ebiat0 * (1 - rr)
        e = ebiat0
        for t in range(10):
            e *= 1 + g
            pv += e * (1 - rr) / (1 + k) ** (t + 1)
        tv = e * (1 + gT) * (1 - gT / 0.10) / (k - gT)
        pv += tv / (1 + k) ** 10
        eq = pv + nonop(c) + transition(c) - INT_AT / k
        return eq / SHARES
    g10 = solve(v, -0.05, 0.40, PRICE)
    ebiat_2036 = ebiat0 * (1 + g10) ** 10
    return g10, ebiat0, ebiat_2036


def reverse_perpetual(roic=0.12, k=COE):
    """现价隐含永续增速：EBIAT 从 2026 正常化水平起永续增长 g，再投资率 = g/ROIC（12%）。"""
    c = S["base"]
    seg = segments(c)
    ebiat0 = seg["np"] - c["noah"] + INT_AT

    def v(g):
        eq = ebiat0 * (1 + g) * (1 - g / roic) / (k - g) + nonop(c) + transition(c) - INT_AT / k
        return eq / SHARES
    return solve(v, 0.0, k - 1e-4, PRICE)


def incremental_return(name="base"):
    c = S[name]
    r = value(c)
    reinv = sum(e * c["rr"][i] for i, (_, e, _) in enumerate(r["flows"]))
    d_ebiat = r["flows"][-1][1] - r["ebiat"]
    avg_rr = sum(c["rr"]) / len(c["rr"])
    return d_ebiat / reinv, avg_rr


def override(name, **kw):
    c = dict(S[name])
    c.update(kw)
    return c


if __name__ == "__main__":
    print(f"经调整净现金（合并，无杠杆口径）net_cash_adj = {NET_CASH_ADJ:.2f} 亿；归母口径净负债 = {ND_ATTR:.2f} 亿；"
          f"税后利息 = {INT_AT:.3f} 亿/年，永续现值 = {INT_AT / COE:.2f} 亿")
    print(f"非经营资产（基准）= {nonop(S['base']):.2f} 亿（诺亚 {NOAH_BV:.2f}、其他金融资产 {OTHER_FIN:.2f}、"
          f"超额萤石粉库存归母成本 {EXCESS_INV_ATTR:.2f} x 0.5）")
    print()
    for s in S:
        r = value(S[s])
        g = r["seg"]
        print(f"[{s}] 2026 正常化归母净利 {g['np']:.2f} 亿 = 单一矿山 {g['mine']:.2f}（实现价 {g['real']:.0f} 元/吨，"
              f"EBIT {g['ebit_mine']:.2f}）+ 选化一体 {g['chain']:.2f}（包钢金石 {g['bg']:.2f}、金鄂博 {g['jeb']:.2f}、"
              f"外销 {g['trade']:.2f}）+ 其他 {g['other']:.2f}")
        print(f"      经营收益 EBIAT {r['ebiat']:.2f}；经营价值 {r['pv_ops']:.2f}（终值占 {r['tv_share']:.0%}）；"
              f"非经营 {nonop(S[s]):.2f}；过渡 {transition(S[s]):.2f}；利息现值 {r['debt']:.2f}")
        print(f"      逐年：" + "，".join(f"{y} EBIAT {e:.2f}/OE {o:.2f}" for y, e, o in r["flows"]))
        ru = value(S[s], mode="unlev")
        rc = value(S[s], nd=-NET_CASH_ADJ)
        print(f"      V（有杠杆）= {r['v']:.2f} 元；剔除回购专户 {r['v_ex_treasury']:.2f}；"
              f"V（无杠杆）= {ru['v']:.2f}；V（有杠杆、合并口径净负债）= {rc['v']:.2f}")
    vw = weighted()
    vwu = weighted(mode="unlev")
    vwc = weighted(nd=-NET_CASH_ADJ)
    vw_ex = sum(SCEN_P[s] * value(S[s])["v_ex_treasury"] for s in S)
    print()
    print(f"概率加权 V（有杠杆，采用）= {vw:.2f} 元，P/V = {PRICE / vw:.2f}；剔除回购专户 V = {vw_ex:.2f}，P/V = {PRICE / vw_ex:.2f}")
    print(f"概率加权 V（无杠杆）= {vwu:.2f} 元，P/V = {PRICE / vwu:.2f}；按合并口径净负债的有杠杆 V = {vwc:.2f}")
    print(f"股权成本 8% 加权 V = {weighted(0.08):.2f}；10% 加权 V = {weighted(0.10):.2f}")
    for k in (0.08, 0.10):
        print(f"  COE {k:.0%}：" + "，".join(f"{s} {value(S[s], k)['v']:.2f}" for s in S))
    print(f"基准情景隐含回报（有杠杆）= {implied_irr():.2%}")
    g10, e0, e36 = reverse_dcf()
    print(f"反向 DCF：现价隐含 2027-2036 年经营收益年增 {g10:.2%}（再投资率固定 35%），"
          f"即 EBIAT 由 {e0:.2f} 亿升至 2036 年 {e36:.2f} 亿，其后 2.5% 永续；"
          f"或自 2026 正常化水平起永续增长 {reverse_perpetual():.2%}（再投资率 = g/12%）")
    ir, arr = incremental_return()
    print(f"基准增长路径：平均再投资率 {arr:.0%}，增量回报（2031 较 2026 EBIAT 增量 / 累计再投资）{ir:.1%}")
    for p in (3200, 3400, 3600):
        sc = {s: override(s, p_fl=S[s]["p_fl"] + (p - 3400)) for s in S}
        print(f"  萤石三情景价格整体平移至基准 {p} 元/吨：加权 V = {weighted(scen=sc):.2f}")
    print(f"分档价格（V 不变）：明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}-{0.90 * vw:.2f}；"
          f"大致合理 {0.90 * vw:.2f}-{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")
    norm = {s: segments(S[s])["np"] for s in S}
    print("normalized_parent_np_2026_yi:", {s: round(v, 2) for s, v in norm.items()},
          "加权", round(sum(SCEN_P[s] * norm[s] for s in S), 2))
    # 2026 年报口径估计（基准）：H1 实际 0.897 + Q3 估计 + Q4（正常化季度 - 缺口）
    est26 = 0.897 + S["base"]["q3"] + (norm["base"] / 4 + S["base"]["q4_short"])
    print(f"2026 年报归母净利估计（基准）≈ {est26:.2f} 亿；三季度单季估计 {S['base']['q3']:.2f} 亿")
    print()
    # ---------------- 证伪条件触发后的 V ----------------
    f1 = weighted(probs={"bear": 0.5, "base": 0.5, "bull": 0.0})
    f2 = weighted(scen={"bear": S["bear"], "bull": S["bull"],
                        "base": override("base", vol=35.0, cogs=1700, q4_short=-1.0, y27_short=-1.2)})
    chain_bear = dict(bg_vol=S["bear"]["bg_vol"], bg_np_t=S["bear"]["bg_np_t"], ahf_vol=S["bear"]["ahf_vol"],
                      ahf_np_t=S["bear"]["ahf_np_t"], trade=0.0, elim=-0.10, inv_f=0.2)
    f3 = weighted(scen={"bear": S["bear"], "bull": override("bull", trade=0.0, inv_f=0.5),
                        "base": override("base", **chain_bear)})
    f4 = weighted(probs={"bear": 0.10, "base": 0.40, "bull": 0.50})
    f5 = weighted(scen={"bear": S["bear"], "bull": S["bull"],
                        "base": override("base", q3=-0.60, q4_short=-1.06, y27_short=-0.80)})
    print(f"F1 萤石 2027 年含税均价 < 3,100：V = {f1:.2f}")
    print(f"F2 浙江矿山复产不及预期（2027 销量 < 35 万吨）：V = {f2:.2f}")
    print(f"F3 选化一体条款不利变化/外销禁令延续：V = {f3:.2f}")
    print(f"F4 上行：2027 扣非归母 ≥ 5 亿且萤石均价 ≥ 3,800：V = {f4:.2f}")
    print(f"F5 三季报前三季度归母 < 0.5 亿（停产拖累更深）：V = {f5:.2f}")
