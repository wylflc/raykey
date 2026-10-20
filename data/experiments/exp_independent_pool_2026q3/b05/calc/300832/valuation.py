#!/usr/bin/env python3
"""300832 新产业：OI-291 池内独立审计（b05，深度版）估值计算。

口径：所有者收益 DCF（归母，无杠杆；经调整净现金为正，全额扣除有息负债即租赁负债）。
金额单位亿元，每股价值元/股。价格日 2026-10-19，最新定期报告 2026 中报（三季报预约 2026-10-28）。
运行：python3 valuation.py
"""

# ---------------------------------------------------------------- 快照
PRICE = 53.32                 # 2026-10-19 收盘，元
SHARES = 7.8572               # 亿股，行情口径总股本（含回购专户股份）
TREASURY = 0.04147588         # 亿股，回购专户 4,147,588 股（buyback_20260825 第 4 页），用于股权激励、不注销
COE = 0.09
COE_LOW, COE_HIGH = 0.08, 0.10
YEAR_ELAPSED_AT_VAL = 0.80    # 2026-10-19 约为全年的 80%

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report 第 47-49、107-117 页）
CASH = 14.5409                # 货币资金，受限 0（期初 0.014 为验资户）
TRADING_FA = 6.7859           # 交易性金融资产：银行理财 6.7657 + 外汇衍生 0.0202
CD_CURRENT = 10.6188          # 一年内到期的债权投资（大额存单）
ONCFA_CURRENT = 2.1548        # 一年内到期的其他非流动金融资产（债务工具）
DEBT_INV = 9.0087             # 债权投资：大额存单 8.8546 + 政府专项债 0.1542
ONCFA_DEBT = 1.0191           # 其他非流动金融资产中的债务工具投资
LEASE_DEBT = 0.0198 + 0.0132  # 一年内到期的非流动负债（租赁）+ 租赁负债；无借款
OPER_RESERVE = 5.0            # 经营备付：约 2 个月付现成本
BUYBACK_AFTER_PERIOD = 1.0006 # 2026-07-07～08-25 回购 2,250,400 股（buyback_20260825 第 2 页），期后现金流出
DECLARED_UNPAID_DIV = 0.0     # 2025 年末期股利 2026-05-27 已除息支付；2026 中期不分配
FIN_DTL = 0.1390 + 0.0127     # 大额存单未到期应收利息、交易性金融资产公允价值变动的递延所得税负债（2026H1_report 第 122 页）

GROSS_FIN = CASH + TRADING_FA + CD_CURRENT + ONCFA_CURRENT + DEBT_INV + ONCFA_DEBT
NET_CASH_ADJ = GROSS_FIN - LEASE_DEBT - OPER_RESERVE - BUYBACK_AFTER_PERIOD - DECLARED_UNPAID_DIV - FIN_DTL

# 非经营资产：其他权益工具投资（卡本医疗 0.9555、艾迪康 0.2310）+ 其他非流动金融资产中的权益工具 0.5700，扣公允价值增值递延税
EQUITY_INV = 1.1865 + 0.5700
EQUITY_INV_DTL = 0.1090 + 0.0366
NON_OPER_ASSETS = EQUITY_INV - EQUITY_INV_DTL
# 激励对象归属时按 35 元/股交回的款项：414.30 万股 × 35 元，按 90% 归属、约 1.6 年折现
INCENTIVE_CASH_PV = 0.04143 * 35.0 * 0.90 / (1 + COE) ** 1.6
OTHER_ADJ = INCENTIVE_CASH_PV

# ---------------------------------------------------------------- 经营基数
REV_2025 = 45.768
REV_H1_2025, REV_H2_2025 = 21.848, 45.768 - 21.848
REV_H1_2026 = 24.203
EBIT_H1_2026 = 9.975          # 剔除汇兑与金融收益（利息、理财、公允价值）的营业利润；含其他收益与信用减值
NONOP_ANNUAL = 0.10           # 捐赠等营业外净支出，按经常性小额处理
NORM_INTEREST_AT = 44.1 * 0.020 * (1 - 0.15)   # 2026 正常化净利息（税后），仅用于正常化归母净利，不进入 DCF

SCENARIOS = {
    # h2_growth：2026H2 收入同比；h2_margin：2026H2 经营 EBIT 率
    # growth：2027-2036 收入增速；margin：2027-2036 经营 EBIT 率；k：每新增 1 元收入的净再投资（营运资本 + 资本开支 − 折旧）
    "bear": dict(p=0.25, h2_growth=0.07, h2_margin=0.390, tax=0.14,
                 growth=[0.02, 0.03, 0.04, 0.04, 0.04, 0.035, 0.03, 0.03, 0.025, 0.02],
                 margin=[0.375, 0.355, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35],
                 k=1.00, g_t=0.015, ronic_t=0.12,
                 note="国内第二轮集采与检验收费立项指南落地后试剂单价再降 15%～20%，国内收入 2027 年负增长；海外增速降到 8%～10%；"
                      "经营 EBIT 率降到 35%；营运资本占收入继续上升，每新增 1 元收入净再投资 1.0 元；终值增长 1.5%、新增投资回报 12%"),
    "base": dict(p=0.50, h2_growth=0.127, h2_margin=0.415, tax=0.13,
                 growth=[0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03],
                 margin=[0.41] * 10,
                 k=0.75, g_t=0.025, ronic_t=0.25,
                 note="2026 收入 51.2 亿（+11.9%），国内试剂量增价降、仪器下滑，海外试剂 +25%～30%；2027 起收入增速 12% 逐年降到 3%；"
                      "经营 EBIT 率 41%（2026H1 实际 41.2%，不回到集采前 43%～45%）；营运资本占收入稳定在约 44%，每新增 1 元收入净再投资 0.75 元；终值增长 2.5%、新增投资回报 25%"),
    "bull": dict(p=0.25, h2_growth=0.17, h2_margin=0.425, tax=0.125,
                 growth=[0.15, 0.14, 0.13, 0.12, 0.11, 0.095, 0.08, 0.065, 0.05, 0.035],
                 margin=[0.42, 0.425, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43],
                 k=0.60, g_t=0.025, ronic_t=0.30,
                 note="海外试剂维持 30% 增长（X8/X10、Mini-T8 与小分子夹心法），国内三级医院替代进口；收入增速 15% 逐年降到 3.5%；"
                      "试剂占比提升使经营 EBIT 率升到 43%；每新增 1 元收入净再投资 0.6 元；终值增长 2.5%、新增投资回报 30%"),
}
YEARS = list(range(2027, 2037))


def project(s, r):
    """返回 (经营价值现值, 明细)。"""
    tax = s["tax"]
    rev_h2 = REV_H2_2025 * (1 + s["h2_growth"])
    rev26 = REV_H1_2026 + rev_h2
    ebit_h2 = rev_h2 * s["h2_margin"]
    ebit26 = EBIT_H1_2026 + ebit_h2
    nopat26 = ebit26 * (1 - tax) - NONOP_ANNUAL
    # 2026H2 所有者收益：H2 税后经营利润 − 半年再投资；6-30 后现金流全部计入（10-19 前已实现部分在净现金中未体现）
    nopat_h2 = ebit_h2 * (1 - tax) - NONOP_ANNUAL / 2
    reinv_h2 = s["k"] * (rev26 - REV_2025) * 0.5
    oe_h2 = nopat_h2 - reinv_h2
    pv = oe_h2  # 时点约为 2026-09-30，按 0 年折现
    rows = []
    rev_prev = rev26
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s["growth"][i])
        ebit = rev * s["margin"][i]
        nopat = ebit * (1 - tax) - NONOP_ANNUAL
        reinv = s["k"] * (rev - rev_prev)
        oe = nopat - reinv
        t = (y - 2026) + 0.5 - YEAR_ELAPSED_AT_VAL
        df = (1 + r) ** (-t)
        pv += oe * df
        rows.append(dict(year=y, rev=rev, ebit=ebit, nopat=nopat, reinv=reinv, oe=oe, t=t, df=df))
        rev_prev = rev
    last = rows[-1]
    g_t = s["g_t"]
    oe_t1 = last["nopat"] * (1 + g_t) * (1 - g_t / s["ronic_t"])
    tv = oe_t1 / (r - g_t)
    pv_tv = tv * last["df"]
    pv += pv_tv
    detail = dict(rev26=rev26, ebit26=ebit26, nopat26=nopat26, oe_h2=oe_h2, rows=rows, tv=tv, pv_tv=pv_tv, pv_oper=pv)
    return pv, detail


def per_share(pv_oper, shares=SHARES):
    return (pv_oper + NET_CASH_ADJ + NON_OPER_ASSETS + OTHER_ADJ) / shares


def scenario_values(r, shares=SHARES):
    out = {}
    for name, s in SCENARIOS.items():
        pv, det = project(s, r)
        out[name] = (per_share(pv, shares), det)
    return out


def weighted(vals):
    return sum(SCENARIOS[n]["p"] * vals[n][0] for n in SCENARIOS)


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


def implied_irr(name="base"):
    s = SCENARIOS[name]
    return solve(lambda r: per_share(project(s, r)[0]), 0.03, 0.25, PRICE)


def reverse_dcf():
    """现价隐含：(a) 以基准 2027 年所有者收益为起点、10 年恒定增速 + 2.5% 终值；(b) 2027 起永续增速。"""
    base = SCENARIOS["base"]
    _, det = project(base, COE)
    oe27 = det["rows"][0]["oe"]
    oe_h2 = det["oe_h2"]
    target_oper = PRICE * SHARES - NET_CASH_ADJ - NON_OPER_ASSETS - OTHER_ADJ

    def val_10y(g):
        pv, oe = oe_h2, oe27
        for i in range(10):
            t = (i + 1) + 0.5 - YEAR_ELAPSED_AT_VAL
            if i > 0:
                oe *= (1 + g)
            pv += oe * (1 + COE) ** (-t)
        tv = oe * 1.025 / (COE - 0.025)
        return pv + tv * (1 + COE) ** (-(10 + 0.5 - YEAR_ELAPSED_AT_VAL))

    g10 = solve(val_10y, -0.10, 0.25, target_oper)

    def val_perp(g):
        t1 = 1 + 0.5 - YEAR_ELAPSED_AT_VAL
        return oe_h2 + oe27 / (COE - g) * (1 + COE) ** (-t1)

    gp = solve(val_perp, -0.05, 0.085, target_oper)
    return g10, gp, oe27, target_oper


def band(pv_ratio):
    if pv_ratio <= 0.75:
        return "明显低估"
    if pv_ratio <= 0.90:
        return "温和低估"
    if pv_ratio <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def falsifier_values():
    """证伪触发后的独立 V（每股）：在基准上改变关键假设后重算三情景并按调整后的概率加权。"""
    import copy
    out = {}
    # F1：2026 年营收 < 50.35 亿（激励触发值，+10%），或 2027 年中报营收同比 < 6%——概率改为 熊 0.45 / 基 0.45 / 牛 0.10
    p_alt = {"bear": 0.45, "base": 0.45, "bull": 0.10}
    vals = scenario_values(COE)
    out["F1_growth_miss_weighted"] = sum(p_alt[n] * vals[n][0] for n in vals)
    # F2：2026 年经营 EBIT 率（剔除汇兑与金融收益）< 39%，或 2027 年中报 < 38%——基准利润率改为 37%，概率 熊 0.35 / 基 0.50 / 牛 0.15
    saved = copy.deepcopy(SCENARIOS["base"])
    SCENARIOS["base"]["margin"] = [0.37] * 10
    vals2 = scenario_values(COE)
    out["F2_margin_37_base_only"] = vals2["base"][0]
    out["F2_margin_weighted"] = sum({"bear": 0.35, "base": 0.50, "bull": 0.15}[n] * vals2[n][0] for n in vals2)
    SCENARIOS["base"] = saved
    # F3：海外主营 2026 年增速 < 12%，或 2027 年中报同比 < 10%——基准增速前 5 年各降 4 个百分点、其后降 2 个百分点，概率 熊 0.30 / 基 0.55 / 牛 0.15
    saved = copy.deepcopy(SCENARIOS["base"])
    SCENARIOS["base"]["growth"] = [g - 0.04 if i < 5 else g - 0.02 for i, g in enumerate(saved["growth"])]
    vals3 = scenario_values(COE)
    out["F3_overseas_base_only"] = vals3["base"][0]
    out["F3_overseas_weighted"] = sum({"bear": 0.30, "base": 0.55, "bull": 0.15}[n] * vals3[n][0] for n in vals3)
    SCENARIOS["base"] = saved
    # F4：治理——公司本身被立案调查，或披露资金占用、违规担保，或董事、高管因实控人案件被采取措施：按熊情景 V
    out["F4_governance_bear"] = scenario_values(COE)["bear"][0]
    # F5：经营现金流/归母净利 2026 年 < 0.75 且 2027 年中报 < 0.6，或应收+长期应收增速高于收入增速 10 个百分点——三情景 k 各加 0.3
    saved = {n: SCENARIOS[n]["k"] for n in SCENARIOS}
    for n in SCENARIOS:
        SCENARIOS[n]["k"] = saved[n] + 0.3
    vals5 = scenario_values(COE)
    out["F5_cash_conversion_weighted"] = weighted(vals5)
    for n in SCENARIOS:
        SCENARIOS[n]["k"] = saved[n]
    return out


def main():
    vals = scenario_values(COE)
    vw = weighted(vals)
    vals_ex = scenario_values(COE, SHARES - TREASURY)
    vw_ex = sum(SCENARIOS[n]["p"] * vals_ex[n][0] for n in SCENARIOS)
    print("=== 300832 新产业 独立估值（价格日 2026-10-19，现价 %.2f 元，总股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("金融资产合计 %.2f；租赁负债 %.3f；经营备付 %.1f；期后回购 %.2f；金融资产递延税 %.2f → 经调整净现金 %.2f 亿元" % (
        GROSS_FIN, LEASE_DEBT, OPER_RESERVE, BUYBACK_AFTER_PERIOD, FIN_DTL, NET_CASH_ADJ))
    print("非经营资产（权益投资扣递延税）%.2f；激励回款现值 %.2f；合计 %.2f 亿元 = %.2f 元/股" % (
        NON_OPER_ASSETS, OTHER_ADJ, NET_CASH_ADJ + NON_OPER_ASSETS + OTHER_ADJ,
        (NET_CASH_ADJ + NON_OPER_ASSETS + OTHER_ADJ) / SHARES))
    print()
    for n in ("bear", "base", "bull"):
        v, det = vals[n]
        s = SCENARIOS[n]
        oper = det["pv_oper"]
        print("[%s] p=%.2f  V=%.2f 元/股  经营价值 %.1f 亿（终值现值 %.1f，占 %.0f%%）" % (
            n, s["p"], v, oper, det["pv_tv"], 100 * det["pv_tv"] / oper))
        print("   2026E 收入 %.2f（%+.1f%%） 经营 EBIT %.2f（%.1f%%） 税后经营利润 %.2f；2026H2 所有者收益 %.2f" % (
            det["rev26"], 100 * (det["rev26"] / REV_2025 - 1), det["ebit26"], 100 * det["ebit26"] / det["rev26"],
            det["nopat26"], det["oe_h2"]))
        print("   年份  收入    经营EBIT  税后经营  再投资  所有者收益  OE增速")
        prev_oe = None
        for row in det["rows"]:
            g = "" if prev_oe is None else "%+.1f%%" % (100 * (row["oe"] / prev_oe - 1))
            print("   %d %7.2f %8.2f %8.2f %7.2f %9.2f  %s" % (
                row["year"], row["rev"], row["ebit"], row["nopat"], row["reinv"], row["oe"], g))
            prev_oe = row["oe"]
        print("   终值：增长 %.1f%%，新增投资回报 %.0f%%，终值 %.1f 亿" % (100 * s["g_t"], 100 * s["ronic_t"], det["tv"]))
        print()
    print("加权独立 V = %.2f 元/股；P/V = %.3f（%s）" % (vw, PRICE / vw, band(PRICE / vw)))
    print("剔除回购专户股份（%.4f 亿股）对照：加权 V = %.2f，P/V = %.3f" % (SHARES - TREASURY, vw_ex, PRICE / vw_ex))
    for r in (COE_LOW, COE_HIGH):
        vr = scenario_values(r)
        print("股权成本 %.0f%%：熊 %.2f / 基 %.2f / 牛 %.2f，加权 V = %.2f，P/V = %.3f" % (
            100 * r, vr["bear"][0], vr["base"][0], vr["bull"][0], weighted(vr), PRICE / weighted(vr)))
    irr = implied_irr()
    print("现价隐含回报（基准现金流含终值与净现金）= %.2f%%" % (100 * irr))
    g10, gp, oe27, target_oper = reverse_dcf()
    print("反向 DCF：现价对应经营价值 %.1f 亿；以基准 2027 所有者收益 %.2f 亿为起点，隐含 10 年增速 %.2f%%（其后 2.5%%）；或 2027 起永续增速 %.2f%%" % (
        target_oper, oe27, 100 * g10, 100 * gp))
    # 正常化归母净利（2026，含净利息，剔除汇兑与理财公允价值等一次性项目）
    print()
    print("2026 正常化归母净利（税后经营利润 + 正常化净利息 %.2f）：" % NORM_INTEREST_AT)
    for n in ("bear", "base", "bull"):
        det = vals[n][1]
        print("   %s：%.2f 亿元（EPS %.2f 元；现价对应 PE %.1f）" % (
            n, det["nopat26"] + NORM_INTEREST_AT, (det["nopat26"] + NORM_INTEREST_AT) / SHARES,
            PRICE * SHARES / (det["nopat26"] + NORM_INTEREST_AT)))
    # 交叉验证
    base_det = vals["base"][1]
    ev = PRICE * SHARES - NET_CASH_ADJ - NON_OPER_ASSETS - OTHER_ADJ
    ebit_ttm = 17.870 - 8.171 + EBIT_H1_2026
    print()
    print("交叉验证：EV = %.1f 亿；EV/经营EBIT(TTM %.2f) = %.1f×；EV/经营EBIT(2026E 基准 %.2f) = %.1f×" % (
        ev, ebit_ttm, ev / ebit_ttm, base_det["ebit26"], ev / base_det["ebit26"]))
    norm_base = base_det["nopat26"] + NORM_INTEREST_AT
    print("加权 V 对应 2026 基准正常化 PE = %.1f×；PB（归母权益 89.69）= %.2f×" % (vw * SHARES / norm_base, vw * SHARES / 89.69))
    print("股息+回购收益率：股息 1.20/%.2f = %.2f%%；2026 年两次回购 2.0 亿 / 市值 %.1f = %.2f%%" % (
        PRICE, 100 * 1.2 / PRICE, PRICE * SHARES, 100 * 2.0 / (PRICE * SHARES)))
    print()
    fv = falsifier_values()
    print("证伪触发后的独立 V：")
    for k, v in fv.items():
        print("   %s = %.2f" % (k, v))
    print()
    print("V 不变时各档价格：明显低估 ≤ %.2f；温和低估 ≤ %.2f；大致合理 ≤ %.2f；偏贵 > %.2f" % (
        0.75 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    # 增长路径摘要（基准 2027-2031 所有者收益增速、再投资率与增量回报）
    rows = base_det["rows"]
    oe_g = [rows[i]["oe"] / (rows[i - 1]["oe"] if i > 0 else None or 1) - 1 for i in range(1, 6)]
    oe26_full = base_det["nopat26"] - SCENARIOS["base"]["k"] * (base_det["rev26"] - REV_2025)
    g27 = rows[0]["oe"] / oe26_full - 1
    reinv_rate = sum(r_["reinv"] for r_ in rows[:5]) / sum(r_["nopat"] for r_ in rows[:5])
    incr_ret = (rows[4]["nopat"] - base_det["nopat26"]) / sum(r_["reinv"] for r_ in rows[:5])
    print("基准所有者收益增速 2027-2031：%s（2027 相对 2026 全年口径 %.1f%%）" % (
        ", ".join("%.1f%%" % (100 * x) for x in [g27] + oe_g[:4]), 100 * g27))
    print("基准 2027-2031 再投资率 %.1f%%，增量税后经营利润/累计再投资 = %.1f%%" % (100 * reinv_rate, 100 * incr_ret))
    print("2026 全年口径所有者收益（税后经营利润 − k × 2026 收入增量）：" + "；".join(
        "%s %.2f" % (n, vals[n][1]["nopat26"] - SCENARIOS[n]["k"] * (vals[n][1]["rev26"] - REV_2025))
        for n in ("bear", "base", "bull")))
    print("各情景现金流对应的现价隐含回报：熊 %.2f%%；基 %.2f%%；牛 %.2f%%" % (
        100 * implied_irr("bear"), 100 * implied_irr("base"), 100 * implied_irr("bull")))
    # 高新技术企业资格未续期：2027 年起税率 25%（基准）
    import copy
    saved = copy.deepcopy(SCENARIOS["base"])
    SCENARIOS["base"]["tax"] = 0.25
    v_tax = scenario_values(COE)["base"][0]
    SCENARIOS["base"] = saved
    print("敏感性：基准税率 13%%→25%%（高新资格未续期，含 2026H2）基准 V = %.2f（较 %.2f 低 %.2f）" % (
        v_tax, vals["base"][0], vals["base"][0] - v_tax))
    q3_estimate()


# ---------------------------------------------------------------- 三季度估计（三季报 2026-10-28 核对）
Q3_2025 = dict(rev=12.428, np=4.337, ebit=12.823 - 8.171)   # 单季，2025 三季报累计减中报
FX_EXPOSURE_USD = (1.0700 + 0.6746)   # 亿美元：货币资金 + 应收账款（2026H1_report 第 133-134 页）
FX_EXPOSURE_EUR = (0.4951 + 0.0629)   # 亿欧元
USD_0630, USD_0930 = 6.8109, 6.7351   # 6-30 折算汇率（第 133 页）；9-30 中间价（新华网）


def q3_estimate():
    fx_loss = FX_EXPOSURE_USD * (USD_0630 - USD_0930) + FX_EXPOSURE_EUR * 7.7671 * (1 - USD_0930 / USD_0630)
    print()
    print("2026Q3 估计（欧元按对美元不变近似；未计套保）：汇兑损失约 %.2f 亿" % fx_loss)
    for name, g, m in (("bear", 0.07, 0.38), ("base", 0.12, 0.40), ("bull", 0.17, 0.42)):
        rev = Q3_2025["rev"] * (1 + g)
        ebit = rev * m
        fin = 0.28      # 利息、理财与公允价值收益（单季，税前）
        pre = ebit + fin - fx_loss - 0.03
        np_ = pre * (1 - 0.13)
        print("   %s：收入 %.2f 亿（%+.0f%%），经营 EBIT %.2f，归母净利约 %.2f 亿（%+.0f%%）" % (
            name, rev, 100 * g, ebit, np_, 100 * (np_ / Q3_2025["np"] - 1)))


if __name__ == "__main__":
    main()
