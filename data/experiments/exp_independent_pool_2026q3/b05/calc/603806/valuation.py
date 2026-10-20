"""福斯特（603806）独立估值：分部所有者收益 DCF（OI-291 b05，价格日 2026-10-19）。

运行：python3 valuation.py
金额单位亿元，股本亿股，每股价值元/股。输入全部写在本脚本内，出处见正文「来源」。
"""

# ---------------------------------------------------------------- 快照与股本
PRICE = 13.27                    # 2026-10-19 收盘（brief.md）
SHARES = 26.0875                 # 总股本，含回购专户（brief.md；dividend_20260929 第 2 页 2,608,745,702 股）
TREASURY = 0.027388              # 回购专户 2,738,800 股，未公告注销（dividend_20260929 第 1 页）
COE = 0.09

# 福22转债（2026H1_report 第 53-54、135 页；financing_20260619 第 8-9 页；financing_20261017 第 3 页）
CB_FACE = 30.29742               # 未转股面值
CB_CONV = 14.47                  # 2026-10-14 起转股价
CB_SHARES = CB_FACE / CB_CONV    # 全部转股新增股数
CB_RATE = 0.025                  # 按债务处理时的折现率（≈现金理财收益率，与不计利息收入一致）
# 剩余现金流：2026-11-23 第4年息1.5%、2027-11-22 第5年息1.8%、2028-11-21 按面值110%（含末期息）到期赎回
CB_FLOWS = [(35 / 365, CB_FACE * 0.015), (399 / 365, CB_FACE * 0.018), (763 / 365, CB_FACE * 1.10)]

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 56-58 页）
CASH = 31.0125                   # 货币资金
TFA = 55.1256                    # 交易性金融资产（理财，含私募证券基金 1.44）
RESTRICTED = 0.0357              # 受限保证金（第 19 页）
DIV_DECLARED = 3.1272            # 中期分红 0.12 元，2026-10-14 发放（dividend_20260929 第 2 页）
OP_RESERVE = 7.0                 # 经营备付，约 5% 营收
LEASE = 0.0697                   # 租赁负债（含一年内到期）
NONOP = 1.8557 + 0.04            # 长期股权投资（烟台万旭 24% 等）+ 其他权益工具投资
BOOK_CB = 28.8909                # 应付债券账面值（对照用）
PARENT_EQUITY = 167.5717

# ---------------------------------------------------------------- 正常化共用参数
TAX = 0.145                      # 2025 年 14.8%，2026H1 13.4%
PV_CAP_INTENSITY = 0.70          # 光伏分部经营资本/营收（营运资本约 57 + 长期资产约 33，对 2026E 约 125 营收）
EL_CAP_INTENSITY = 0.80          # 电子材料增量营收所需资本
EL_OWN = 0.8243                  # 电子材料公司持股（第 153、156 页）
YEARS = [2027, 2028, 2029, 2030, 2031]

SCENARIOS = {
    "bear": dict(
        p=0.25,
        vol26=23.5, vg=0.0, gp=0.60, asp=5.0, oth=0.6, opex=6.3, opex_g=0.01, imp=0.012, oi=0.40,
        tg=0.01, roic_t=0.07,
        el_rev26=10.0, el_m26=0.065, el_g=[0.12] * 5, el_m=[0.070, 0.075, 0.080, 0.080, 0.080], el_tg=0.02, el_roic_t=0.10,
        oth26=-0.77, oth_path=[-0.70, -0.60, -0.50, -0.40, -0.30], oth_t=0.0,
        extra={2027: -2.55},     # 逾期应收再损失约 3 亿（税后 2.55）
        note="胶膜单位毛利 0.60 元/平、销量 23.5 亿平且不增长，减值 1.2% 营收，华创 PET 膜持续亏损，2027 年再损失逾期应收 3 亿",
    ),
    "base": dict(
        p=0.50,
        vol26=25.0, vg=0.025, gp=0.82, asp=5.3, oth=0.9, opex=6.3, opex_g=0.02, imp=0.008, oi=0.45,
        tg=0.02, roic_t=0.12,
        el_rev26=10.0, el_m26=0.070, el_g=[0.22, 0.20, 0.17, 0.15, 0.12], el_m=[0.085, 0.10, 0.11, 0.12, 0.125], el_tg=0.025, el_roic_t=0.14,
        oth26=-0.77, oth_path=[-0.45, -0.20, 0.0, 0.10, 0.15], oth_t=0.10,
        extra={},
        note="胶膜单位毛利 0.82 元/平（2024-2026H1 均值 0.74 与 2022-2026E 全周期推算均值约 0.96 之间）、销量 25 亿平后年增 2.5%，电子材料 2031 年营收约 22 亿、净利率 12.5%",
    ),
    "bull": dict(
        p=0.25,
        vol26=26.5, vg=0.04, gp=1.02, asp=5.6, oth=1.1, opex=6.4, opex_g=0.02, imp=0.005, oi=0.55,
        tg=0.025, roic_t=0.16,
        el_rev26=10.0, el_m26=0.080, el_g=[0.28, 0.25, 0.22, 0.18, 0.15], el_m=[0.09, 0.11, 0.13, 0.14, 0.15], el_tg=0.025, el_roic_t=0.18,
        oth26=-0.60, oth_path=[-0.30, 0.0, 0.20, 0.35, 0.50], oth_t=0.45,
        extra={},
        note="二线胶膜厂退出后单位毛利回到 1.02 元/平（≈2024 年）、销量 26.5 亿平后年增 4%，干膜高端替代使电子材料 2031 年营收约 26 亿、净利率 15%",
    ),
}

# 2026 正常化归母净利的财务项（含净利息）：理财与存款收益 ≈ 80 亿 × 1.9%，转债利息费用约 1.0 亿，联营收益约 0.05 亿
FIN_INCOME_PRE = 80.0 * 0.019
CB_INTEREST_PL = 1.0
EQUITY_METHOD = 0.05
ESOP_COST_AFTER_TAX = 0.43       # 第五期员工持股计划公司奖励基金 0.5 亿（税前），一次性


def pv_nopat(sc, vol, years_from_2026, oi):
    """光伏材料分部税后经营利润（不含利息收支与投资收益）。"""
    rev = vol * sc["asp"] + 4.0                     # 胶膜之外的背板、电站与其他业务收入约 4 亿
    ebit = vol * sc["gp"] + sc["oth"] - sc["opex"] * (1 + sc["opex_g"]) ** years_from_2026 - sc["imp"] * rev + oi
    return ebit * (1 - TAX), rev, ebit


def build(sc):
    """返回 2026 正常化与 2027-2031 逐年分部税后利润、所有者收益及终值输入。"""
    n26, rev26, ebit26 = pv_nopat(sc, sc["vol26"], 0, sc["oi"] + 0.05)
    el26 = sc["el_rev26"] * sc["el_m26"] * EL_OWN
    rows = []
    prev_rev, prev_el = rev26, sc["el_rev26"]
    vol = sc["vol26"]
    for i, y in enumerate(YEARS):
        vol = vol * (1 + sc["vg"])
        n, rev, ebit = pv_nopat(sc, vol, i + 1, sc["oi"])
        pv_reinv = PV_CAP_INTENSITY * (rev - prev_rev)
        el_rev = prev_el * (1 + sc["el_g"][i])
        el_n = el_rev * sc["el_m"][i] * EL_OWN
        el_reinv = EL_CAP_INTENSITY * (el_rev - prev_el) * EL_OWN
        o_n = sc["oth_path"][i]
        extra = sc["extra"].get(y, 0.0)
        oe = (n - pv_reinv) + (el_n - el_reinv) + o_n + extra
        rows.append(dict(year=y, vol=vol, pv_n=n, pv_reinv=pv_reinv, el_rev=el_rev, el_n=el_n, el_reinv=el_reinv,
                         oth=o_n, extra=extra, nopat=n + el_n + o_n, oe=oe, ebit=ebit))
        prev_rev, prev_el = rev, el_rev
    nopat26 = n26 + el26 + sc["oth26"]
    # 2026 正常化所有者收益：扣除按情景增速的常态再投资（光伏按 vg，电子材料按 2026 年约 22% 的实际增速）
    oe26 = (n26 - PV_CAP_INTENSITY * sc["vg"] * rev26) + (el26 - EL_CAP_INTENSITY * 0.22 / 1.22 * sc["el_rev26"] * EL_OWN) + sc["oth26"]
    return dict(n26=n26, el26=el26, nopat26=nopat26, oe26=oe26, ebit26=ebit26, rev26=rev26, rows=rows)


def ops_value(sc, coe, b=None):
    """经营价值：2026H2 存根 + 2027-2031 显性期（年中折现）+ 分部终值。估值日 2026-10-19。"""
    b = b or build(sc)
    last = b["rows"][-1]
    pv_term = last["pv_n"] * (1 + sc["tg"]) * (1 - sc["tg"] / sc["roic_t"]) / (coe - sc["tg"])
    el_term = last["el_n"] * (1 + sc["el_tg"]) * (1 - sc["el_tg"] / sc["el_roic_t"]) / (coe - sc["el_tg"])
    oth_term = sc["oth_t"] / (coe - 0.02)
    tv = pv_term + el_term + oth_term
    stub = 0.5 * b["oe26"] - ESOP_COST_AFTER_TAX
    pv_explicit = stub / (1 + coe) ** 0.2
    for i, r in enumerate(b["rows"]):
        pv_explicit += r["oe"] / (1 + coe) ** (0.7 + i)
    pv_tv = tv / (1 + coe) ** 4.7
    return pv_explicit + pv_tv, pv_explicit, pv_tv, b


def segment_values(sc, coe=COE):
    """分部经营价值（存根按分部税后利润占比拆分，ESOP 成本计入光伏）。"""
    b = build(sc)
    last = b["rows"][-1]
    d = 1 + coe
    pv = {"光伏材料": 0.0, "电子材料": 0.0, "其他新材料": 0.0}
    pv["光伏材料"] += (0.5 * (b["n26"] - PV_CAP_INTENSITY * sc["vg"] * b["rev26"]) - ESOP_COST_AFTER_TAX) / d ** 0.2
    pv["电子材料"] += 0.5 * (b["el26"] - EL_CAP_INTENSITY * 0.22 / 1.22 * sc["el_rev26"] * EL_OWN) / d ** 0.2
    pv["其他新材料"] += 0.5 * sc["oth26"] / d ** 0.2
    for i, r in enumerate(b["rows"]):
        f = d ** (0.7 + i)
        pv["光伏材料"] += (r["pv_n"] - r["pv_reinv"] + r["extra"]) / f
        pv["电子材料"] += (r["el_n"] - r["el_reinv"]) / f
        pv["其他新材料"] += r["oth"] / f
    pv["光伏材料"] += last["pv_n"] * (1 + sc["tg"]) * (1 - sc["tg"] / sc["roic_t"]) / (coe - sc["tg"]) / d ** 4.7
    pv["电子材料"] += last["el_n"] * (1 + sc["el_tg"]) * (1 - sc["el_tg"] / sc["el_roic_t"]) / (coe - sc["el_tg"]) / d ** 4.7
    pv["其他新材料"] += sc["oth_t"] / (coe - 0.02) / d ** 4.7
    return pv


def cb_debt_value(rate=CB_RATE):
    return sum(cf / (1 + rate) ** t for t, cf in CB_FLOWS)


NET_CASH_EX_CB = CASH + TFA - RESTRICTED - DIV_DECLARED - OP_RESERVE - LEASE
CB_DEBT = cb_debt_value()
NET_CASH_ADJ = NET_CASH_EX_CB - CB_DEBT          # 无杠杆口径经调整净现金（为正，照常全额扣除有息负债）


def per_share(ops, shares=SHARES):
    """可转债逐情景取低：按债务（债底现值全额扣除）与全部转股（股本加转股数、不扣转债）各算一次，取较低者。"""
    v_debt = (ops + NET_CASH_ADJ + NONOP) / shares
    v_conv = (ops + NET_CASH_EX_CB + NONOP) / (shares + CB_SHARES)
    if v_conv < v_debt:
        return v_conv, "转股", v_debt, v_conv
    return v_debt, "债务", v_debt, v_conv


def scenario_values(coe=COE, scen=SCENARIOS, shares=SHARES):
    out = {}
    for k, sc in scen.items():
        ops, pe, ptv, b = ops_value(sc, coe)
        v, mode, vd, vc = per_share(ops, shares)
        out[k] = dict(v=v, mode=mode, v_debt=vd, v_conv=vc, ops=ops, pv_explicit=pe, pv_tv=ptv, b=b)
    return out


def weighted(vals, scen=SCENARIOS):
    return sum(scen[k]["p"] * vals[k]["v"] for k in vals)


def normalized_np_2026(sc):
    b = build(sc)
    fin = (FIN_INCOME_PRE - CB_INTEREST_PL) * (1 - 0.15)
    return b["n26"] + b["el26"] + sc["oth26"] + fin + EQUITY_METHOD


def solve(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def implied_irr(sc):
    target = PRICE * SHARES - NET_CASH_ADJ - NONOP
    return solve(lambda r: ops_value(sc, r)[0] - target, 0.03, 0.20)


def reverse_dcf(sc):
    """现价隐含：(1) 以基准 2027 所有者收益为起点的永续增速；(2) 10 年所有者收益复合增速（之后 2% 永续）。"""
    target = PRICE * SHARES - NET_CASH_ADJ - NONOP
    b = build(sc)
    oe27 = b["rows"][0]["oe"]
    stub = (0.5 * b["oe26"] - ESOP_COST_AFTER_TAX) / (1 + COE) ** 0.2
    g_perp = solve(lambda g: stub + oe27 / (COE - g) * (1 + COE) ** 0.3 - target, -0.05, 0.085)

    def pv10(x):
        tot, oe = stub, oe27
        for i in range(10):
            tot += oe / (1 + COE) ** (0.7 + i)
            if i < 9:
                oe *= 1 + x
        tot += oe * 1.02 / (COE - 0.02) / (1 + COE) ** 9.7
        return tot - target
    g10 = solve(pv10, -0.10, 0.40)
    return g_perp, g10, oe27


def falsifier_values():
    """各证伪条件触发后的加权 V（只改基准情景或概率，其余不变）。"""
    out = {}
    def wv(mod_base=None, probs=None, delta=0.0):
        scen = {k: dict(v) for k, v in SCENARIOS.items()}
        if mod_base:
            scen["base"].update(mod_base)
        if probs:
            for k, p in probs.items():
                scen[k]["p"] = p
        vals = scenario_values(scen=scen)
        return weighted(vals, scen) + delta
    out["F1_gp"] = wv(mod_base=dict(gp=0.66))
    out["F2_vol"] = wv(mod_base=dict(vol26=23.0, vg=0.01))
    out["F3_credit"] = wv(delta=-3.7 / SHARES)
    out["F4_el"] = wv(mod_base=dict(el_g=[0.10] * 5, el_m=[0.08, 0.085, 0.09, 0.09, 0.09]))
    out["F5_q3"] = wv(probs=dict(bear=0.35, base=0.50, bull=0.15))
    out["U1_up"] = wv(mod_base=dict(gp=0.95, vol26=26.0, vg=0.03))
    out["U2_bull_as_base"] = wv(mod_base=dict(gp=1.00, vol26=26.5, vg=0.035, asp=5.5, oth=1.0, imp=0.006))
    return out


def growth_metrics(sc):
    """基准 2027-2031：所有者收益逐年增速、再投资率（再投资/税后利润）与增量回报（税后利润增量/累计再投资）。"""
    b = build(sc)
    prev = b["oe26"]
    growth = []
    for r in b["rows"]:
        growth.append(r["oe"] / prev - 1)
        prev = r["oe"]
    reinv = sum(r["pv_reinv"] + r["el_reinv"] for r in b["rows"])
    nop = sum(r["nopat"] for r in b["rows"])
    d_nopat = b["rows"][-1]["nopat"] - b["nopat26"]
    d_nopat_ex_oth = d_nopat - (b["rows"][-1]["oth"] - sc["oth26"])
    return growth, reinv / nop, d_nopat / reinv, d_nopat_ex_oth / reinv


# 历史核心经营利润拆解（亿元；2025_annual_report 第 10、70-74 页，2026H1_report 第 60-61、143-145 页）
HIST = {
    # pbt, 信用+资产减值净额, 营收, 利息收入, 理财+公允价值+处置金融资产, 利息支出, 汇兑收益(损失为负), 权益法及处置长投,
    # 资产处置+营业外净额, 非经常性政府补助, 所得税, 少数股东损益
    "2024": dict(pbt=14.7881, imp=-3.1724, rev=191.474, ii=1.0775, wm=0.1564 - 0.0197, ie=0.5706, fx=-0.2574, eq=-0.0716,
                 nonop=0.0005 - 0.3705, grants=0.3738, tax=1.8965, mi=-0.1840),
    "2025": dict(pbt=8.7346, imp=-0.6719, rev=154.908, ii=0.5233, wm=0.6423 + 0.2528, ie=0.4322, fx=-0.2752, eq=-0.3746,
                 nonop=0.0058 - 0.1940, grants=0.4463, tax=1.2957, mi=-0.2578),
    "2026H1": dict(pbt=9.7026, imp=0.9661, rev=69.877, ii=0.1070, wm=0.5258 + 0.1849, ie=0.4193, fx=0.2909, eq=0.1074 + 0.0149,
                   nonop=-0.0371 - 0.0115, grants=0.3381, tax=1.2966, mi=-0.0162),
}
Q2_INVENTORY_GAIN = 1.70   # 2026Q2 低价库存结转估计：营收 36.15 ×（毛利率 20.05% − 无库存效应约 15.3%）


def core_decomposition(h, norm_imp=0.008):
    """税前利润 = 核心经营 + (实际减值 − 常态减值) + 净利息与理财 + 汇兑 + 权益法 + 处置与营业外 + 一半政府补助。"""
    fin = h["ii"] + h["wm"] - h["ie"]
    core_pbt = (h["pbt"] - (h["imp"] + norm_imp * h["rev"]) - fin - h["fx"] - h["eq"] - h["nonop"] - 0.5 * h["grants"])
    t = h["tax"] / h["pbt"]
    return dict(core_pbt=core_pbt, tax_rate=t, core_nopat=core_pbt * (1 - t), core_parent=core_pbt * (1 - t) - h["mi"],
                imp_excess=(h["imp"] + norm_imp * h["rev"]) * (1 - t), fin=fin * (1 - t), fx=h["fx"] * (1 - t),
                eq=h["eq"] * (1 - t), other=(h["nonop"] + 0.5 * h["grants"]) * (1 - t))


def q3_2026_estimate():
    """2026Q3 单季估计（三季报 2026-10-27 披露前）：销量 6.2 亿平、单位毛利 0.74 元/平（7 月光伏级 EVA 约 9,800 元/吨企稳，无低价库存结转）。"""
    film_gp = 6.2 * 0.74
    gp = film_gp + 0.22 + 2.6 * 0.25 - 0.05      # 其他光伏、电子材料（营收约 2.6 亿、毛利率 25%）、华创等
    opex = 8.6 / 4
    other_income = 0.12
    impairment = -0.008 * 34.0
    fin = 0.40 - 0.25                               # 理财与利息收入、转债利息费用
    equity_method = 0.02
    pbt = gp - opex + other_income + impairment + fin + equity_method
    np_parent = pbt * (1 - 0.14) + 0.02             # 少数股东分担华创、电子材料子公司亏损/利润的净额
    np_deducted = np_parent - (0.32 + 0.06) * 0.86  # 扣除理财收益与政府补助
    return film_gp, gp, pbt, np_parent, np_deducted


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    vals = scenario_values()
    vw = weighted(vals)
    pv_ratio = PRICE / vw
    print("== 福斯特 603806 独立估值（价格日 2026-10-19，现价 %.2f，总股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("净现金（不含转债）%.2f；转债按债务现值 %.2f（账面 %.2f）；经调整净现金 %.2f；非经营资产 %.2f"
          % (NET_CASH_EX_CB, CB_DEBT, BOOK_CB, NET_CASH_ADJ, NONOP))
    for k in ("bear", "base", "bull"):
        r = vals[k]
        b = r["b"]
        print("\n[%s] p=%.2f  V=%.2f 元（转债按%s；债务口径 %.2f／转股口径 %.2f）  经营价值 %.1f（显性 %.1f + 终值 %.1f，终值占 %.0f%%）"
              % (k, SCENARIOS[k]["p"], r["v"], r["mode"], r["v_debt"], r["v_conv"], r["ops"], r["pv_explicit"], r["pv_tv"],
                 100 * r["pv_tv"] / r["ops"]))
        print("  2026 正常化：光伏税后 %.2f，电子材料归母 %.2f，其他 %.2f，合计税后 %.2f，所有者收益 %.2f"
              % (b["n26"], b["el26"], SCENARIOS[k]["oth26"], b["nopat26"], b["oe26"]))
        sv = segment_values(SCENARIOS[k])
        print("  分部经营价值：" + "，".join("%s %.1f 亿（%.2f 元/股）" % (n, v, v / SHARES) for n, v in sv.items()))
        prev = b["oe26"]
        for row in b["rows"]:
            print("  %d 销量 %.1f 亿平 光伏税后 %.2f 再投资 %.2f | 电子营收 %.1f 归母 %.2f 再投资 %.2f | 其他 %.2f 一次性 %.2f | 合计税后 %.2f 所有者收益 %.2f（%+.1f%%）"
                  % (row["year"], row["vol"], row["pv_n"], row["pv_reinv"], row["el_rev"], row["el_n"], row["el_reinv"], row["oth"],
                     row["extra"], row["nopat"], row["oe"], 100 * (row["oe"] / prev - 1)))
            prev = row["oe"]
    print("\n加权 V = %.2f 元；P/V = %.2f → %s" % (vw, pv_ratio, verdict(pv_ratio)))
    v_ex_t = weighted(scenario_values(shares=SHARES - TREASURY))
    print("剔除回购专户股份后：加权 V = %.2f，P/V = %.2f" % (v_ex_t, PRICE / v_ex_t))
    for c in (0.08, 0.10):
        vv = scenario_values(coe=c)
        print("股权成本 %.0f%%：熊 %.2f／基准 %.2f／牛 %.2f，加权 %.2f，P/V %.2f"
              % (100 * c, vv["bear"]["v"], vv["base"]["v"], vv["bull"]["v"], weighted(vv), PRICE / weighted(vv)))
    irr = implied_irr(SCENARIOS["base"])
    print("现价隐含回报（基准情景所有者收益流+净现金）：%.2f%%" % (100 * irr))
    g_perp, g10, oe27 = reverse_dcf(SCENARIOS["base"])
    print("反向 DCF：以基准 2027 所有者收益 %.2f 亿为起点，现价隐含永续增速 %.2f%%；或 10 年复合增速 %.1f%%（其后 2%%）"
          % (oe27, 100 * g_perp, 100 * g10))
    print("\n2026 正常化归母净利（含净利息、剔除一次性）：熊 %.2f／基准 %.2f／牛 %.2f 亿"
          % tuple(normalized_np_2026(SCENARIOS[k]) for k in ("bear", "base", "bull")))
    b = vals["base"]["b"]
    ebit26 = b["ebit26"] + b["el26"] / EL_OWN / (1 - TAX) + SCENARIOS["base"]["oth26"] / 0.9085 / (1 - TAX)
    ev = PRICE * SHARES - NET_CASH_ADJ - NONOP
    print("交叉验证：EV %.1f 亿；基准 2026 正常化 EBIT %.2f → EV/EBIT %.1f×；市值/基准正常化归母 %.1f×；PB %.2f"
          % (ev, ebit26, ev / ebit26, PRICE * SHARES / normalized_np_2026(SCENARIOS["base"]), PRICE * SHARES / PARENT_EQUITY))
    print("\n各档价格（V 不变）：明显低估 ≤ %.2f；温和低估 %.2f～%.2f；大致合理 %.2f～%.2f；偏贵 > %.2f"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print("\n证伪条件触发后加权 V：")
    for k, v in falsifier_values().items():
        print("  %s: %.2f" % (k, v))
    g, rr, inc, inc_ex = growth_metrics(SCENARIOS["base"])
    print("\n基准增长路径（所有者收益同比）：" + "，".join("%d %+.1f%%" % (y, 100 * x) for y, x in zip(YEARS, g)))
    print("基准 2027-2031 再投资率 %.1f%%；增量回报 %.1f%%（剔除华创减亏 %.1f%%）；终值增长 光伏 %.1f%%、电子材料 %.1f%%"
          % (100 * rr, 100 * inc, 100 * inc_ex, 100 * SCENARIOS["base"]["tg"], 100 * SCENARIOS["base"]["el_tg"]))
    alt = (vals["base"]["ops"] + NET_CASH_EX_CB - CB_FACE + NONOP) / SHARES
    print("对照：转债按未转股面值 %.2f 亿扣除时基准 V = %.2f（债底现值口径 %.2f）" % (CB_FACE, alt, vals["base"]["v"]))
    print("\n核心经营利润拆解（常态减值 0.8% 营收，一半政府补助视为经常性）：")
    for k, h in HIST.items():
        d = core_decomposition(h)
        print("  %s：核心税前 %.2f，税率 %.1f%%，核心税后归母 %.2f；减值偏离常态 %+.2f，净利息与理财 %+.2f，汇兑 %+.2f，权益法 %+.2f，处置/营业外/补助 %+.2f（税后）"
              % (k, d["core_pbt"], 100 * d["tax_rate"], d["core_parent"], d["imp_excess"], d["fin"], d["fx"], d["eq"], d["other"]))
    d = core_decomposition(HIST["2026H1"])
    clean = (d["core_pbt"] - Q2_INVENTORY_GAIN) * (1 - d["tax_rate"]) - HIST["2026H1"]["mi"]
    print("  2026H1 剔除二季度低价库存结转约 %.2f 亿（税后 %.2f）后核心税后归母 %.2f，年化 %.1f；胶膜单位毛利剔除后约 %.2f 元/平"
          % (Q2_INVENTORY_GAIN, Q2_INVENTORY_GAIN * (1 - d["tax_rate"]), clean, 2 * clean, (10.40 - 0.95 * Q2_INVENTORY_GAIN) / 12.20))
    fg, gp, pbt, npp, npd = q3_2026_estimate()
    print("2026Q3 估计：胶膜毛利 %.2f，毛利 %.2f，利润总额 %.2f，归母 %.2f，扣非 %.2f 亿" % (fg, gp, pbt, npp, npd))


if __name__ == "__main__":
    main()
