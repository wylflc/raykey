# -*- coding: utf-8 -*-
"""601965 中国汽研 独立估值（OI-291 b02，价格日 2026-10-19；2026-10-20 按框架补有杠杆口径，同日按用户裁定改为只滚动净负债，r2）。

运行：python3 valuation.py
口径：金额亿元，每股元；归母口径；股权成本基准 9%（敏感性 8%／10%）。
方法：归母所有者收益两阶段 DCF（经营利润口径，剔除税后净银行利息）
      + 归母经调整净现金（核心，剔除南方试验场）
      + 南方试验场 35.15% 权益按账面倍数单列
      + 非经营投资。
两种口径：
  无杠杆：有息负债按本金全额扣除（核心经调整净现金 −5.05 亿）。
  有杠杆（framework「三法互校」第 2 条，经调整净现金为负时适用，登记取此口径）：
      经调整净负债（−核心经调整净现金）按现规模滚动、不偿还本金，改扣其税后利息的现值
      （利率取有息负债实际平均利率，折现率取股权成本：基准 9%，敏感性随 8%／10% 同步），
      现金已在净负债里抵减、不另加（r2；r1 曾滚动全部有息负债 14.27 亿、现金按面值另加）。
所有输入写在本脚本内，出处见 b02/companies/601965_中国汽研.md。
"""

PRICE = 14.00            # 2026-10-19 收盘，腾讯行情
SHARES = 10.0265         # 亿股，总股本（= 2026H1 资产负债表 1,002,648,387 股；无回购专户，库存股为限制性股票回购义务）
COE = 0.09
VAL_T = 2026 + 292 / 365  # 估值日 2026-10-19 折成年份
WEIGHTS = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# ---------------- 一、资产负债表（2026-06-30，2026H1_report 第 43-45、99-100、145-147 页） ----------------
BS = dict(
    cash=22.730,             # 货币资金
    restricted=0.340,        # 受限：承兑/保函/信用证保证金、冻结资金
    struct_dep=1.706,        # 结构性存款（交易性金融资产内）
    nanfang_cash=6.40,       # 南方试验场现金估计：其流动资产 6.948 扣应收、预付、待抵扣税约 0.55（估计）
    div_payable=2.464,       # 应付股利（2025 年末期股利 2.406 已于 7-08 支付，另含子公司少数股东股利）
    op_reserve=3.0,          # 经营备付：约 1 个月付现成本（2025 付现成本约 31.7 亿/年）
    grant_advance=1.00,      # 与收益相关递延收益 1.121 × 归母比例约 0.9（课题经费已收、待支出）
    minority_cash=2.0,       # 广东、天平、河南、湖南等非全资子公司现金中少数股东份额（估计）
    bank_debt=13.150 + 0.917 + 0.012,   # 长期借款 + 一年内到期长期借款 + 应计利息
    other_lt_payable=0.173 + 0.029,     # 长期应付款（含一年内到期；2025 年报称非金融机构长期借款）
)
# 租赁负债 5.159 两种口径都不扣：其成本（使用权资产折旧约 0.83 + 租赁利息约 0.19 亿/年）已在归母净利内。


def core_net_cash(bs=BS):
    """无杠杆口径的核心归母经调整净现金（json 的 net_cash_adj_yi）。"""
    c = bs["cash"] - bs["restricted"] + bs["struct_dep"] - bs["nanfang_cash"]
    c -= bs["div_payable"] + bs["op_reserve"] + bs["grant_advance"] + bs["minority_cash"]
    c -= bs["bank_debt"] + bs["other_lt_payable"]
    return c


# ---------------- 有杠杆口径：有息负债按现规模滚动 ----------------
# 滚动本金 = 长期借款 13.150 + 一年内到期长期借款 0.917 + 长期应付款 0.202（应计利息 0.012 仍按面值扣除）
DEBT_ROLLED = 13.150 + 0.917 + 0.173 + 0.029
# 实际平均利率 = 2026H1 借款利息（费用化 利息费用 0.23369 − 租赁利息 0.09397，加资本化 0.03310）× 2
#                ÷ 平均有息负债（2025 年末 11.221+0.607+0.173+0.029 = 12.030；2026-06-30 14.269）
#   （2026H1_report 第 155 页财务费用、第 131-133 页在建工程利息资本化；资本化率 2.24%／2.44% 作旁证）
H1_INT_EXPENSED = 0.233689 - 0.093971
H1_INT_CAPITALIZED = 0.033103
DEBT_BEGIN, DEBT_END = 11.221 + 0.607 + 0.173 + 0.029, DEBT_ROLLED
DEBT_RATE = (H1_INT_EXPENSED + H1_INT_CAPITALIZED) * 2 / ((DEBT_BEGIN + DEBT_END) / 2)
TAX_SHIELD = 0.15        # 高新技术企业 15%
# r2：只滚动经调整净负债，现金已在净负债里抵减；有息负债本金只用于测算实际平均利率
NET_DEBT_ROLLED = max(0.0, -core_net_cash())
AT_INTEREST = NET_DEBT_ROLLED * DEBT_RATE * (1 - TAX_SHIELD)   # 年税后利息


def pv_after_tax_interest(r=COE):
    return AT_INTEREST / r


def leverage_uplift(r=COE):
    """有杠杆口径相对无杠杆口径的股权价值差：加回滚动本金，改扣税后利息现值。"""
    return NET_DEBT_ROLLED - pv_after_tax_interest(r)


# 南方试验场（35.15% 持股并表，少数股东 64.85%；2026H1_report 第 169-175 页）
NANFANG_EQUITY = 21.149 - 0.936      # 资产合计 − 负债合计 = 20.213
PARENT_PCT = 0.3515
# 非经营投资：长期股权投资 0.552（主要为中汽院浙江合营）+ 金融资产 1.145 按 8 折
NON_OP = 0.552 + (0.156 + 0.989) * 0.8

# ---------------- 二、2026 年正常化归母净利（含净利息，剔除一次性） ----------------
# 2026E 扣非归母 = H1 4.08 + Q3E 2.40 + Q4E 3.70 = 10.18 ≈ 10.2；
# 加回：H1 以前年度所得税调整 0.10、测试装备低谷 0.10；减：价格压力 0.10 → 基准 10.3。
NORM_NP_2026 = {"bear": 9.3, "base": 10.3, "bull": 10.9}
AT_NET_INTEREST = 0.20   # 税后净银行利息（归母）：2026H1 银行利息 0.140 − 利息收入 0.043，全年约 0.25 税前

SCEN = {
    "bear": dict(g=[0.00, 0.01, 0.02, 0.02, 0.02], ronic=0.07, rr_floor=0.25,
                 g_t=0.015, ronic_t=0.07, h2_wc=0.0, nanfang_pb=0.45, manuf_option=0.0,
                 note="国内车市收缩与车企整合压价、检测机构价格战；新产能利用率低，增量回报 7%"),
    "base": dict(g=[0.07, 0.06, 0.05, 0.045, 0.04], ronic=0.14, rr_floor=0.25,
                 g_t=0.025, ronic_t=0.12, h2_wc=1.5, nanfang_pb=0.70, manuf_option=0.0,
                 note="GB 47955 与新版准入审查要求 2027-01-01 施行、出口认证拉动，价格温和承压；华东、南方逐步爬坡，增量回报 14%"),
    "bull": dict(g=[0.10, 0.09, 0.08, 0.07, 0.06], ronic=0.18, rr_floor=0.25,
                 g_t=0.025, ronic_t=0.15, h2_wc=2.0, nanfang_pb=1.00, manuf_option=1.5,
                 note="强标落地带来认证潮、份额提升、出海认证放量；制造业务按账面处置变现"),
}
# 2026 下半年归母核心自由现金流（6-30 为季节性现金低点：2025 年 H1 FCF −4.91、H2 +7.46）
# = 半年经营归母 + 核心折旧摊销 3.0 − 核心资本开支 3.5 + 季节性营运资金回收（情景值），× 0.95（扣除非全资子公司的少数股东份额）
H2_DA, H2_CAPEX, H2_MINORITY = 3.0, 3.5, 0.95
YEARS = [2027, 2028, 2029, 2030, 2031]


def scenario_value(name, r=COE, levered=True):
    s = SCEN[name]
    np_op = NORM_NP_2026[name] + AT_NET_INTEREST          # 经营口径（剔除税后净利息）
    oe_h2 = (0.5 * np_op + H2_DA - H2_CAPEX + s["h2_wc"]) * H2_MINORITY   # 2026 下半年，t≈0
    pv, rows, npt = oe_h2, [], np_op
    for y, g in zip(YEARS, s["g"]):
        npt *= 1 + g
        rr = max(s["rr_floor"], g / s["ronic"])
        oe = npt * (1 - rr)
        t = y + 0.5 - VAL_T
        df = (1 + r) ** -t
        pv += oe * df
        rows.append((y, g, npt, rr, oe, df))
    rr_t = s["g_t"] / s["ronic_t"]
    oe_next = npt * (1 + s["g_t"]) * (1 - rr_t)
    tv = oe_next / (r - s["g_t"])
    pv_tv = tv * rows[-1][5]
    op_value = pv + pv_tv
    nf = PARENT_PCT * NANFANG_EQUITY * s["nanfang_pb"]
    adj = core_net_cash() + (leverage_uplift(r) if levered else 0.0)
    eq = op_value + adj + nf + NON_OP + s["manuf_option"]
    return dict(v=eq / SHARES, equity=eq, op_value=op_value, pv_explicit=pv - oe_h2, oe_h2=oe_h2,
                pv_tv=pv_tv, tv_share=pv_tv / eq, nanfang=nf, adj=adj, rows=rows, rr_t=rr_t,
                tv_pe=(1 - rr_t) / (r - s["g_t"]))


def weighted_v(r=COE, w=WEIGHTS, levered=True):
    return sum(w[k] * scenario_value(k, r, levered)["v"] for k in w)


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


def implied_irr(levered=True):
    """基准情景所有者收益流（含终值、净现金或税后利息现值、南方与非经营资产）现值等于现价的折现率。"""
    return bisect(lambda r: scenario_value("base", r, levered)["v"] - PRICE, 0.04, 0.20)


def reverse_dcf(levered=True):
    """现价隐含：(a) 10 年归母经营利润年增速 g（再投资率 = g/14%，下限 25%），之后 2.5% 永续（增量回报 12%）；
    (b) 单阶段永续增速（增量回报 14%）。"""
    s = SCEN["base"]
    adj = core_net_cash() + (leverage_uplift(COE) if levered else 0.0)
    other = adj + PARENT_PCT * NANFANG_EQUITY * s["nanfang_pb"] + NON_OP
    target = PRICE * SHARES - other
    np0 = NORM_NP_2026["base"] + AT_NET_INTEREST

    def op_value_10y(g):
        pv = (0.5 * np0 + H2_DA - H2_CAPEX + s["h2_wc"]) * H2_MINORITY
        npt = np0
        for i in range(10):
            npt *= 1 + g
            rr = max(0.25, g / s["ronic"])
            pv += npt * (1 - rr) * (1 + COE) ** -(2027 + i + 0.5 - VAL_T)
        rr_t = 0.025 / s["ronic_t"]
        tv = npt * 1.025 * (1 - rr_t) / (COE - 0.025)
        pv += tv * (1 + COE) ** -(2036 + 0.5 - VAL_T)
        return pv

    g10 = bisect(lambda g: op_value_10y(g) - target, -0.05, 0.20)

    def op_value_perp(g):
        return np0 * (1 + g) * (1 - g / s["ronic"]) / (COE - g)

    gp = bisect(lambda g: op_value_perp(g) - target, -0.05, 0.085)
    return g10, gp, target, adj


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


FALSIFIERS = [
    ("2026 三季报（10-27）前三季度扣非归母 < 6.20 亿（Q3 单季 < 2.12 亿，同比 −6%）", "2026-10-31",
     {"bear": 0.40, "base": 0.50, "bull": 0.10}),
    ("2026 年报扣非归母 < 9.6 亿或技术服务收入同比 < 0", "2027-04-30",
     {"bear": 0.55, "base": 0.40, "bull": 0.05}),
    ("2026 年末应收（账款+票据+合同资产）/收入 > 65% 或全年信用减值 > 1.5 亿", "2027-04-30",
     {"bear": 0.50, "base": 0.45, "bull": 0.05}),
    ("工信部准入允许车企自检替代第三方法规检测（大范围试点或正式规章）", "2027-12-31",
     {"bear": 1.00, "base": 0.00, "bull": 0.00}),
    ("2027 年新能源及智能网联开发和测评收入增速 < 15%（L2 强标实施首年）", "2028-04-30",
     {"bear": 0.30, "base": 0.60, "bull": 0.10}),
]


def explicit_capex_check(levered=True, verbose=False):
    """再投资率交叉核对（基准）：若资本开支回落到折旧约 1.25 倍、营运资金按增量收入 40%。"""
    da = [5.9, 6.1, 6.3, 6.5, 6.7]
    capex = [7.5, 7.5, 7.8, 8.0, 8.2]
    nwc_ratio, rev = 0.40, 53.0
    o = scenario_value("base", COE, levered)
    alt_pv = 0.0
    for (y, g, npt, rr, oe, df), d, c in zip(o["rows"], da, capex):
        drev = rev * g
        rev += drev
        reinv = c - d + nwc_ratio * drev
        if verbose:
            print("  %d 资本开支 %.1f − 折旧摊销 %.1f + 营运资金 %.2f = 净再投资 %.2f → 再投资率 %.0f%%（模型 %.0f%%）" %
                  (y, c, d, nwc_ratio * drev, reinv, reinv / npt * 100, rr * 100))
        alt_pv += (npt - reinv) * df
    alt_eq = o["oe_h2"] + alt_pv + o["pv_tv"] + o["adj"] + o["nanfang"] + NON_OP
    return alt_eq / SHARES


def main():
    print("=== 601965 中国汽研 独立估值（价格日 2026-10-19，现价 %.2f，总股本 %.4f 亿股）===" % (PRICE, SHARES))
    ncc = core_net_cash()
    print("无杠杆口径：核心归母经调整净现金（剔除南方）%.2f 亿（%.2f 元/股）" % (ncc, ncc / SHARES))
    print("有杠杆口径（r2）：滚动经调整净负债 %.3f 亿，实际平均利率 %.2f%%（2026H1 借款利息 %.4f + 资本化 %.4f，年化 ÷ 平均负债 %.3f），"
          "税率 %.0f%%，年税后利息 %.3f 亿，9%% 折现现值 %.2f 亿" %
          (NET_DEBT_ROLLED, DEBT_RATE * 100, H1_INT_EXPENSED, H1_INT_CAPITALIZED, (DEBT_BEGIN + DEBT_END) / 2,
           TAX_SHIELD * 100, AT_INTEREST, pv_after_tax_interest()))
    print("  → 有杠杆核心调整项 = %.2f + %.3f − %.2f = %.2f 亿（较无杠杆多 %.2f 元/股）" %
          (ncc, NET_DEBT_ROLLED, pv_after_tax_interest(), ncc + leverage_uplift(), leverage_uplift() / SHARES))
    print("南方试验场账面净资产 %.3f 亿 × 35.15%% = %.2f 亿；非经营投资 %.2f 亿" %
          (NANFANG_EQUITY, PARENT_PCT * NANFANG_EQUITY, NON_OP))
    for k in ("bear", "base", "bull"):
        o = scenario_value(k)
        ou = scenario_value(k, levered=False)
        print("\n[%s] p=%.2f  2026 正常化归母 %.2f（经营口径 %.2f）  %s" %
              (k, WEIGHTS[k], NORM_NP_2026[k], NORM_NP_2026[k] + AT_NET_INTEREST, SCEN[k]["note"]))
        for (y, g, npt, rr, oe, df) in o["rows"]:
            print("  %d  增速 %5.1f%%  经营归母 %6.2f  再投资率 %4.1f%%  所有者收益 %5.2f  折现因子 %.4f" %
                  (y, g * 100, npt, rr * 100, oe, df))
        print("  终值增速 %.1f%%  终值再投资率 %.1f%%  终值倍数(次年经营归母) %.1fx" %
              (SCEN[k]["g_t"] * 100, o["rr_t"] * 100, o["tv_pe"]))
        print("  2026H2 所有者收益 %.2f + 显性期现值 %.2f + 终值现值 %.2f = 经营价值 %.2f" %
              (o["oe_h2"], o["pv_explicit"], o["pv_tv"], o["op_value"]))
        print("  有杠杆：+ 核心调整 %.2f + 南方 %.2f + 非经营 %.2f + 制造处置期权 %.2f = 股权 %.2f 亿；终值占比 %.0f%%  V = %.2f 元/股" %
              (o["adj"], o["nanfang"], NON_OP, SCEN[k]["manuf_option"], o["equity"], o["tv_share"] * 100, o["v"]))
        print("  无杠杆：+ 核心净现金 %.2f → 股权 %.2f 亿；终值占比 %.0f%%  V = %.2f 元/股" %
              (ou["adj"], ou["equity"], ou["tv_share"] * 100, ou["v"]))
    for lev, label in ((True, "有杠杆口径（登记）"), (False, "无杠杆口径（对照）")):
        vw = weighted_v(levered=lev)
        pv = PRICE / vw
        print("\n== %s ==" % label)
        print("三情景 V 熊/基/牛 = %.2f / %.2f / %.2f；加权 V = %.2f 元/股；P/V = %.3f → %s" %
              (*(scenario_value(k, COE, lev)["v"] for k in ("bear", "base", "bull")), vw, pv, verdict(pv)))
        print("股权成本 8%%: 加权 V = %.2f；10%%: 加权 V = %.2f" % (weighted_v(0.08, levered=lev), weighted_v(0.10, levered=lev)))
        for r in (0.08, 0.10):
            print("  r=%.0f%%  熊/基/牛 = %.2f / %.2f / %.2f" % (r * 100, *(scenario_value(k, r, lev)["v"] for k in ("bear", "base", "bull"))))
        print("现价隐含回报（基准情景）: %.2f%%" % (implied_irr(lev) * 100))
        g10, gp, target, adj = reverse_dcf(lev)
        print("反向 DCF: 现价隐含经营价值 %.1f 亿（核心调整项 %.2f）；10 年经营归母增速 %.2f%%（再投资率=g/14%%，下限25%%）；单阶段永续增速 %.2f%%（增量回报 14%%）" %
              (target, adj, g10 * 100, gp * 100))
        print("V 不变时各档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵" %
              (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
        print("证伪条件触发后的独立 V：")
        for cond, ddl, w in FALSIFIERS:
            print("  [%s] %s → V = %.2f" % (ddl, cond, weighted_v(COE, w, lev)))
        keep = dict(SCEN["base"])
        for ro, rot in ((0.10, 0.09), (0.12, 0.11), (0.18, 0.15)):
            SCEN["base"]["ronic"], SCEN["base"]["ronic_t"] = ro, rot
            print("基准增量回报 %.0f%%/终值 %.0f%%: 基准 V = %.2f" % (ro * 100, rot * 100, scenario_value("base", COE, lev)["v"]))
        SCEN["base"].update(keep)
        print("若资本开支 2027 年后回落到折旧约 1.25 倍（再投资率约 19%%～27%%），基准 V = %.2f" % explicit_capex_check(lev))
    print("\n基准再投资交叉核对（核心，亿元）：")
    explicit_capex_check(True, verbose=True)
    # 交叉验证
    mcap = PRICE * SHARES
    print("\n交叉验证：市值 %.2f 亿；TTM 归母 10.76 → PE %.1fx；2026 基准正常化 → PE %.1fx；PB(80.27) %.2fx；"
          "股息率(0.34 元) %.2f%%" % (mcap, mcap / 10.76, mcap / NORM_NP_2026["base"], mcap / 80.27, 0.34 / PRICE * 100))
    ev = mcap + BS["bank_debt"] + BS["other_lt_payable"] + 5.159 + BS["div_payable"] + 18.344 \
        - (BS["cash"] - BS["restricted"] + BS["struct_dep"]) - NON_OP
    ebit_ttm = 13.61 + 0.34   # TTM 营业利润 + 财务费用（2025 13.44+0.18；H1 26 5.44+0.19；H1 25 5.27+0.03）
    print("EV（含少数股东权益账面 18.34、租赁 5.16）%.1f 亿；TTM EBIT 约 %.1f 亿 → EV/EBIT %.1fx" % (ev, ebit_ttm, ev / ebit_ttm))


if __name__ == "__main__":
    main()
