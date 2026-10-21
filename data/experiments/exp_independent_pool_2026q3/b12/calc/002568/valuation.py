#!/usr/bin/env python3
"""百润股份（002568）独立估值：OI-291 b12，价格日 2026-10-20。

方法：分部所有者收益 DCF（归母口径，股权成本基准 9%）。
  1. 核心业务（预调鸡尾酒 + 食用香精 + 其他）：2026 年正常化经营利润（归母正常化净利加回烈酒板块税后亏损与税后净利息），
     2027-2031 逐年增长，扣除再投资得所有者收益，2031 年后按戈登公式（终值增长 ≤ 2.5%，终值再投资 = g / 30%）。
  2. 烈酒（威士忌）板块：显式现金流 2027-2040 加终值，含 13.5 亿元桶陈扩能与研发中心资本开支、新酒灌桶现金投入、
     固定营销与管理费用；已在库陈酿原酒视为沉没成本，只在出售时贡献现金边际，账面成本仅用于计税。
  3. 加经调整净现金（无杠杆口径）与非经营资产，扣除 6-30 后已付转债利息。
  4. 可转债逐情景取低：债务口径扣除到期赎回额（面值 110%，含最后一期利息）的现值；转股口径股本加 11.274/20.33 亿股。
  5. 定增（13.05 亿元）另列「发行」口径对照；三情景 V 与加权 V 取「不发行」口径。

所有金额单位亿元，股本亿股，每股价值元。用 python3 valuation.py 运行，不读取任何外部文件。
"""

PRICE = 18.04
SHARES = 10.4080            # 腾讯行情口径总股本（含回购专户股份）
TREASURY = 0.04665468       # 回购专户 4,665,468 股（2026-07-16 简式权益变动报告书注）
T0 = 0.20                   # 2026-10-20 至 2026-12-31 的年数

# ---------------- 资产负债（2026-06-30，2026H1_report 第 21、95、109、112 页）
CASH = 18.6988              # 货币资金
TFA = 2.0075                # 交易性金融资产（结构性存款与银行理财）
RESTRICTED = 0.0115         # 冻结资金
OP_BUFFER = 1.50            # 经营备付，约为收入的 5%
ST_LOAN = 14.9552           # 短期借款（保证借款为主）
LEASE = 0.0681              # 租赁负债 0.0201 + 一年内到期的租赁负债 0.0480
NON_OP = 0.2895             # 投资性房地产（账面）
CB_COUPON_PAID = 0.2029     # 2026-09-29 已付第五年利息（1.8% × 11.274），6-30 之后的现金流出

NET_CASH_ADJ = CASH + TFA - RESTRICTED - OP_BUFFER - ST_LOAN - LEASE

# ---------------- 可转债（financing_20260922_727867、2026H1_report 第 41 页、受托管理事务报告到期赎回条款）
CB_FACE = 11.274134         # 6-30 未转股面值
CONV_PRICE = 20.33          # 2026-06-05 起转股价；10-09 公告限制性股票注销后不调整
CB_REDEEM = CB_FACE * 1.10  # 到期（2027-09-28）后五个交易日内按面值 110%（含最后一期利息）赎回
CB_T = 0.97                 # 至 2027-10 上旬兑付的年数
CB_RD = 0.03                # 债底折现率（AA 主体一年期）
CB_DEBT_PV = CB_REDEEM / (1 + CB_RD) ** CB_T
CB_CONV_SHARES = CB_FACE / CONV_PRICE

# ---------------- 定增对照（financing_20261016_521639 第 3-4 页）
PP_GROSS = 13.05
PP_FEE = 0.015
PP_PRICE = 15.5             # 假设：竞价定价约为发行期首日前 20 日均价的 86%（下限 80%）
PP_SHARES = PP_GROSS / PP_PRICE
PP_NET = PP_GROSS * (1 - PP_FEE)

# ---------------- 核心业务
NET_INT_ADDBACK = 0.15      # 2026 年税后净利息支出（短借利息 + 转债票息与摊销 - 存款利息），加回得经营口径
RONIC = 0.30                # 终值阶段新增投资回报率
CORE = {
    # np26：2026 年归母正常化净利（含净利息、含烈酒亏损，剔除补助等非经常性损益并把 H1 18.1% 的税率正常化）
    "bear": dict(np26=6.85, g=[-0.04, -0.04, -0.02, 0.00, 0.00], reinv=0.03, gT=0.010, h2_oe=0.9),
    "base": dict(np26=7.30, g=[0.07, 0.06, 0.05, 0.04, 0.03], reinv=0.10, gT=0.025, h2_oe=1.2),
    "bull": dict(np26=7.65, g=[0.12, 0.10, 0.08, 0.07, 0.06], reinv=0.15, gT=0.025, h2_oe=1.5),
}
YEARS_CORE = [2027, 2028, 2029, 2030, 2031]

# ---------------- 烈酒（威士忌）板块
W_REV_PER_CASE_2026 = 1552.0   # 元/箱（9 升），由 2025 年约 1.15 亿元收入 / 7.48 万箱推算并上调单一麦芽占比
W_CASES_2026 = 12.5            # 万箱：H1 3.76 万箱 + H2 估计（公司预计单一麦芽全年 9 万箱）
W_CONTRIB = 0.53               # 现金边际：1 - 灌装包材人工 17% - 消费税及附加 20% - 变动销售费用 10%
W_BOOK_SPIRIT = 0.105          # 在库原酒账面成本（非现金，可抵税）；与 17% 合计使毛利率约 72.5%
W_TAX = 0.25
W_F2026 = 1.65                 # 烈酒板块固定现金费用（营销团队、体验中心、崃州吧、管理）
W_MAINT = 0.50                 # 蒸馏厂、陈酿库与体验中心维持性资本开支
PROJECT = {2027: 4.5, 2028: 4.5, 2029: 4.5}   # 桶陈扩能 11.77 + 研发检测中心 1.73（不含铺底流动资金）
PROJECT_DEP_YEARS = 10         # 橡木桶按 10 年折旧，近似为税盾
W_YEARS = list(range(2027, 2041))

WHISKY = {
    "bear": dict(
        cases={2027: 15, 2028: 17, 2029: 19, 2030: 20, 2031: 21}, g_after=0.03, price_g=0.00,
        F={2027: 1.70, 2028: 1.70, 2029: 1.50, 2030: 1.30}, F_g=0.02,
        newmake={2027: 1.2, 2028: 1.2, 2029: 1.2}, newmake_late=0.3, repl_T=0.00,
        extra_capex_pct=0.0, gT=0.010),
    "base": dict(
        cases={2027: 16, 2028: 21, 2029: 27, 2030: 33, 2031: 39, 2032: 44, 2033: 48, 2034: 52, 2035: 55},
        g_after=0.03, price_g=0.01,
        F=None, F_g=0.06, F_g_late=0.04,
        newmake={2027: 1.2, 2028: 1.2, 2029: 1.2, 2030: 1.2, 2031: 1.2}, newmake_late=0.4, repl_T=0.05,
        extra_capex_pct=0.0, gT=0.025),
    "bull": dict(
        cases={2027: 24, 2028: 38, 2029: 56, 2030: 76, 2031: 96, 2032: 114, 2033: 130, 2034: 142, 2035: 150},
        g_after=0.03, price_g=0.03,
        F=None, F_g=0.10, F_g_late=0.04,
        newmake={2027: 1.2, 2028: 1.2, 2029: 1.2, 2030: 1.2, 2031: 1.2}, newmake_late_pct=0.06, repl_T=0.10,
        extra_capex_pct=0.02, gT=0.025),
}

PROB = {"bear": 0.25, "base": 0.50, "bull": 0.25}


def disc(t, r):
    return 1.0 / (1.0 + r) ** t


def t_mid(year):
    """年度现金流按年中折现：2027 年 → 0.70 年。"""
    return T0 + (year - 2027) + 0.5


def whisky_2026_after_tax():
    rev = W_CASES_2026 * W_REV_PER_CASE_2026 / 1e4
    ebit = rev * (W_CONTRIB - W_BOOK_SPIRIT) - W_F2026
    return rev, ebit, ebit * (1 - W_TAX)


W_REV_2026, W_EBIT_2026, W_NI_2026 = whisky_2026_after_tax()


def core_nopat26(s):
    return CORE[s]["np26"] - W_NI_2026 + NET_INT_ADDBACK


def core_value(s, r, g_override=None, years=None, reinv_override=None):
    c = CORE[s]
    nopat = core_nopat26(s)
    gs = g_override if g_override is not None else c["g"]
    yrs = years if years is not None else YEARS_CORE
    reinv = c["reinv"] if reinv_override is None else reinv_override
    pv, path = 0.0, []
    for y, g in zip(yrs, gs):
        nopat *= 1 + g
        oe = nopat * (1 - reinv)
        path.append((y, nopat, oe))
        pv += oe * disc(t_mid(y), r)
    gT = c["gT"]
    oe_next = nopat * (1 + gT) * (1 - gT / RONIC)
    tv = oe_next / (r - gT) * (1 + r) ** 0.5   # 年中折现口径：终值首笔现金流在终值时点后 0.5 年
    t_tv = T0 + (yrs[-1] - 2026)
    pv_tv = tv * disc(t_tv, r)
    return pv + pv_tv, pv, pv_tv, path


def whisky_flows(s, with_project=True):
    w = WHISKY[s]
    cases = W_CASES_2026
    price = W_REV_PER_CASE_2026
    F = W_F2026
    rows = []
    proj = PROJECT if with_project else {}
    for y in W_YEARS:
        cases = w["cases"][y] if y in w["cases"] else cases * (1 + w["g_after"])
        price *= 1 + w["price_g"]
        rev = cases * price / 1e4
        if w["F"] is not None and y in w["F"]:
            F = w["F"][y]
        else:
            g_f = w["F_g"]
            if y > 2035 and "F_g_late" in w:
                g_f = w["F_g_late"]
            F *= 1 + g_f
        ebit = rev * (W_CONTRIB - W_BOOK_SPIRIT) - F
        shield = sum(v / PROJECT_DEP_YEARS for py, v in proj.items() if py < y <= py + PROJECT_DEP_YEARS)
        tax = W_TAX * (ebit - shield)
        if y in w["newmake"]:
            newmake = w["newmake"][y]
        elif "newmake_late_pct" in w:
            newmake = rev * w["newmake_late_pct"]
        else:
            newmake = w["newmake_late"]
        capex = proj.get(y, 0.0) + W_MAINT + (rev * w["extra_capex_pct"] if y >= 2030 else 0.0)
        cf = rev * W_CONTRIB - F - tax - newmake - capex
        rows.append(dict(y=y, cases=cases, price=price, rev=rev, F=F, ebit=ebit, tax=tax,
                         newmake=newmake, capex=capex, cf=cf))
    return rows


def whisky_value(s, r, with_project=True):
    w = WHISKY[s]
    rows = whisky_flows(s, with_project)
    pv = sum(row["cf"] * disc(t_mid(row["y"]), r) for row in rows)
    last = rows[-1]
    gT = w["gT"]
    rev_n = last["rev"] * (1 + gT)
    F_n = last["F"] * (1 + gT)
    ebit_n = rev_n * (W_CONTRIB - W_BOOK_SPIRIT) - F_n
    cf_n = rev_n * W_CONTRIB - F_n - W_TAX * ebit_n - rev_n * w["repl_T"] - W_MAINT * (1 + gT) \
        - rev_n * w["extra_capex_pct"]
    tv = cf_n / (r - gT) * (1 + r) ** 0.5
    pv_tv = tv * disc(T0 + (W_YEARS[-1] - 2026), r)
    return pv + pv_tv, pv, pv_tv, rows


def per_share(E, extra_shares=0.0, extra_cash=0.0):
    """可转债逐情景取低：返回 (V_debt, V_conv, V_min)。"""
    v_debt = (E + extra_cash - CB_DEBT_PV) / (SHARES + extra_shares)
    v_conv = (E + extra_cash) / (SHARES + CB_CONV_SHARES + extra_shares)
    return v_debt, v_conv, min(v_debt, v_conv)


def equity_pre_cb(core_s, whisky_s, r, with_project=True, core_g=None, core_years=None):
    cv = core_value(core_s, r, g_override=core_g, years=core_years)[0]
    wv = whisky_value(whisky_s, r, with_project)[0]
    h2 = CORE[core_s]["h2_oe"] * disc(T0, r)
    return cv + wv + h2 + NET_CASH_ADJ + NON_OP - CB_COUPON_PAID


def scenario(s, r):
    E = equity_pre_cb(s, s, r)
    vd, vc, v = per_share(E)
    vd_pp, vc_pp, v_pp = per_share(E, PP_SHARES, PP_NET)
    v_ex_treasury = min((E - CB_DEBT_PV) / (SHARES - TREASURY),
                        E / (SHARES - TREASURY + CB_CONV_SHARES))
    return dict(E=E, v_debt=vd, v_conv=vc, v=v, v_pp=v_pp, v_ex_treasury=v_ex_treasury)


def weighted(r):
    res = {s: scenario(s, r) for s in PROB}
    vw = sum(PROB[s] * res[s]["v"] for s in PROB)
    return vw, res


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
    """基准情景所有者收益流（含终值、净现金与转债兑付）使现值等于现价市值的折现率。"""
    target = PRICE * SHARES

    def pv_at(r):
        return equity_pre_cb("base", "base", r) - CB_REDEEM * disc(CB_T, r) - target
    return bisect(pv_at, 0.035, 0.20)


def reverse_dcf():
    """现价隐含：核心所有者收益 2027-2036 年均增速（烈酒取基准，10 年后 2.5%）。"""
    yrs = list(range(2027, 2037))

    def f(g):
        E = equity_pre_cb("base", "base", 0.09, core_g=[g] * 10, core_years=yrs)
        return per_share(E)[2] - PRICE
    g10 = bisect(f, -0.05, 0.40)

    def f2(g):
        # 单阶段：2027 年起核心所有者收益以永续增速 g 增长（再投资 = g / 30%）
        nopat = core_nopat26("base")
        oe = nopat * (1 + g) * (1 - g / RONIC)
        cv = oe / (0.09 - g) * (1 + 0.09) ** (1 - t_mid(2027))
        wv = whisky_value("base", 0.09)[0]
        E = cv + wv + CORE["base"]["h2_oe"] * disc(T0, 0.09) + NET_CASH_ADJ + NON_OP - CB_COUPON_PAID
        return per_share(E)[2] - PRICE
    gp = bisect(f2, -0.02, 0.0899)
    return g10, gp


def cross(core_s, whisky_s, with_project=True, r=0.09):
    E = equity_pre_cb(core_s, whisky_s, r, with_project)
    return per_share(E)[2]


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("=== 百润股份 002568 独立估值（价格日 2026-10-20，现价 %.2f 元，股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("经调整净现金（无杠杆口径，不含转债）: %.2f 亿元" % NET_CASH_ADJ)
    print("  = 货币资金 %.2f + 交易性金融资产 %.2f - 冻结 %.3f - 经营备付 %.2f - 短期借款 %.2f - 租赁 %.3f"
          % (CASH, TFA, RESTRICTED, OP_BUFFER, ST_LOAN, LEASE))
    print("非经营资产: %.2f；6-30 后已付转债利息: %.2f" % (NON_OP, CB_COUPON_PAID))
    print("可转债: 面值 %.3f，到期赎回额 %.3f，债务口径现值 %.2f；转股口径新增 %.4f 亿股"
          % (CB_FACE, CB_REDEEM, CB_DEBT_PV, CB_CONV_SHARES))
    print("定增对照: 募资 %.2f（净 %.2f），假设发行价 %.2f，新增 %.4f 亿股" % (PP_GROSS, PP_NET, PP_PRICE, PP_SHARES))
    print("烈酒板块 2026E: 收入 %.2f，税前 %.2f，税后 %.2f（加回核心）" % (W_REV_2026, W_EBIT_2026, W_NI_2026))
    print()
    for s in ["bear", "base", "bull"]:
        cv, cpv, ctv, path = core_value(s, 0.09)
        wv, wpv, wtv, rows = whisky_value(s, 0.09)
        print("--- 情景 %s（概率 %.2f）---" % (s, PROB[s]))
        print("  2026 归母正常化净利 %.2f；核心经营利润 2026 %.2f" % (CORE[s]["np26"], core_nopat26(s)))
        for y, nopat, oe in path:
            print("    核心 %d: 经营利润 %.2f, 所有者收益 %.2f" % (y, nopat, oe))
        print("  核心价值 %.1f（显式 %.1f + 终值 %.1f，终值占比 %.0f%%）" % (cv, cpv, ctv, 100 * ctv / cv))
        for row in rows:
            if row["y"] in (2027, 2028, 2029, 2030, 2031, 2035, 2040):
                print("    烈酒 %d: 销量 %.1f 万箱, 收入 %.2f, 固定费用 %.2f, 税前 %.2f, 新酒 %.2f, 资本开支 %.2f, 现金流 %.2f"
                      % (row["y"], row["cases"], row["rev"], row["F"], row["ebit"], row["newmake"], row["capex"],
                         row["cf"]))
        print("  烈酒板块价值 %.1f（显式 %.1f + 终值 %.1f）" % (wv, wpv, wtv))
        sc = scenario(s, 0.09)
        print("  转债前股权价值 %.1f；V 债务口径 %.2f，V 转股口径 %.2f → 取低 %.2f；剔除回购专户 %.2f；定增发行口径 %.2f"
              % (sc["E"], sc["v_debt"], sc["v_conv"], sc["v"], sc["v_ex_treasury"], sc["v_pp"]))
        print()
    vw, res = weighted(0.09)
    pv = PRICE / vw
    vw_pp = sum(PROB[s] * res[s]["v_pp"] for s in PROB)
    vw_ext = sum(PROB[s] * res[s]["v_ex_treasury"] for s in PROB)
    print("加权 V（9%%）: %.2f 元；P/V = %.2f → %s" % (vw, pv, band(pv)))
    print("  剔除回购专户股份的加权 V: %.2f（P/V %.2f）；定增发行口径加权 V: %.2f（P/V %.2f）"
          % (vw_ext, PRICE / vw_ext, vw_pp, PRICE / vw_pp))
    v8, _ = weighted(0.08)
    v10, _ = weighted(0.10)
    print("股权成本敏感性: 8%% → %.2f 元（P/V %.2f）；10%% → %.2f 元（P/V %.2f）" % (v8, PRICE / v8, v10, PRICE / v10))
    irr = implied_irr()
    print("现价隐含回报（基准情景现金流）: %.2f%%" % (100 * irr))
    g10, gp = reverse_dcf()
    print("反向 DCF: 核心所有者收益 2027-2036 年均增速 %.1f%%（烈酒取基准）；单阶段永续增速 %.2f%%" % (100 * g10, 100 * gp))
    print()
    print("V 不变时进入各档的价格: ≤%.2f 明显低估；≤%.2f 温和低估；≤%.2f 大致合理" % (0.75 * vw, 0.90 * vw, 1.10 * vw))
    print()
    print("交叉情景（9%，不发行，取低）:")
    for cs in ["bear", "base", "bull"]:
        line = "  核心 %s: " % cs
        for ws in ["bear", "base", "bull"]:
            line += "烈酒 %s %.2f  " % (ws, cross(cs, ws))
        print(line)
    print("  核心基准 + 烈酒基准但取消 20 万桶扩能与研发中心: %.2f" % cross("base", "base", with_project=False))
    print()
    print("证伪触发后的独立 V（9%）:")
    print("  F1 核心转入熊市路径: %.2f" % cross("bear", "base"))
    print("  F2 威士忌转入熊市路径: %.2f" % cross("base", "bear"))
    print("  F3 威士忌达到牛市路径: %.2f" % cross("base", "bull"))
    print("  F4 取消扩能项目: %.2f" % cross("base", "base", with_project=False))
    print("  F5 核心达到牛市路径: %.2f" % cross("bull", "base"))
    print()
    print("正常化归母净利 2026（亿元）: 熊 %.2f / 基准 %.2f / 牛 %.2f" % tuple(CORE[s]["np26"] for s in ["bear", "base", "bull"]))
    print()
    # 基准情景核心再投资与增量回报
    c = CORE["base"]
    _, _, _, path = core_value("base", 0.09)
    reinv_sum = sum(oe / (1 - c["reinv"]) * c["reinv"] for _, _, oe in path)
    d_nopat = path[-1][1] - core_nopat26("base")
    print("基准核心: 2027-2031 再投资合计 %.2f，经营利润增量 %.2f，增量回报 %.0f%%；终值再投资率 %.1f%%"
          % (reinv_sum, d_nopat, 100 * d_nopat / reinv_sum, 100 * c["gT"] / RONIC))
    wrows = whisky_flows("base")
    w_inv = sum(r_["capex"] + r_["newmake"] for r_ in wrows if r_["y"] <= 2031)
    print("基准烈酒: 2027-2031 资本开支与新酒投入合计 %.2f 亿元" % w_inv)
    # 交叉验证读数
    mcap = PRICE * SHARES
    ev = mcap + CB_DEBT_PV + ST_LOAN + LEASE - CASH - TFA
    pretax_ttm = 5.8491 + (8.1130 - 5.3218)          # H1 2026 + (2025 - H1 2025) 利润总额
    net_int_ttm = (0.6595 - 0.4565) - (0.3376 - 0.2308) + (0.3145 - 0.2142)
    ebit_ttm = pretax_ttm + net_int_ttm - 0.33       # 扣除税前非经常性损益约 0.33
    print("交叉验证: 市值 %.1f，EV %.1f，TTM 调整 EBIT %.2f，EV/EBIT %.1f 倍；股息率 %.2f%%（过去 12 个月无回购）"
          % (mcap, ev, ebit_ttm, ev / ebit_ttm, 100 * 0.30 / PRICE))
    print("  现价对 2026 基准正常化净利 %.1f 倍；对基准核心经营利润 %.1f 倍" % (mcap / CORE["base"]["np26"],
                                                                     mcap / core_nopat26("base")))


if __name__ == "__main__":
    main()
