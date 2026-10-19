# -*- coding: utf-8 -*-
"""601965 中国汽研 独立估值（OI-291 b02，价格日 2026-10-19）。

运行：python3 valuation.py
口径：金额亿元，每股元；归母口径；股权成本基准 9%（敏感性 8%／10%）。
方法：归母所有者收益两阶段 DCF（经营利润口径，剔除税后净银行利息）
      + 归母经调整净现金（核心，剔除南方试验场）
      + 南方试验场 35.15% 权益按账面倍数单列
      + 非经营投资。
所有输入写在本脚本内，出处见 b02/companies/601965_中国汽研.md。
"""

PRICE = 14.00            # 2026-10-19 收盘，腾讯行情
SHARES = 10.0265         # 亿股，总股本（= 2026H1 资产负债表 1,002,648,387 股）
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
    other_lt_payable=0.173 + 0.029,     # 长期应付款（含一年内到期）
)
# 租赁负债 5.159 不扣：其成本（使用权资产折旧约 0.83 + 租赁利息约 0.19 亿/年）已在归母净利内。


def core_net_cash(bs=BS):
    c = bs["cash"] - bs["restricted"] + bs["struct_dep"] - bs["nanfang_cash"]
    c -= bs["div_payable"] + bs["op_reserve"] + bs["grant_advance"] + bs["minority_cash"]
    c -= bs["bank_debt"] + bs["other_lt_payable"]
    return c


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


def scenario_value(name, r=COE):
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
    eq = op_value + core_net_cash() + nf + NON_OP + s["manuf_option"]
    out = dict(v=eq / SHARES, equity=eq, op_value=op_value, pv_explicit=pv - oe_h2, oe_h2=oe_h2,
               pv_tv=pv_tv, tv_share=pv_tv / eq, nanfang=nf, rows=rows, rr_t=rr_t,
               tv_pe=(1 - rr_t) / (r - s["g_t"]))
    return out


def weighted_v(r=COE, w=WEIGHTS):
    return sum(w[k] * scenario_value(k, r)["v"] for k in w)


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
    """基准情景所有者收益流（含终值、净现金、南方与非经营资产）现值等于现价的折现率。"""
    return bisect(lambda r: scenario_value("base", r)["v"] - PRICE, 0.04, 0.20)


def reverse_dcf():
    """现价隐含：(a) 10 年归母经营利润年增速 g（再投资率 = g/14%，下限 25%），之后 2.5% 永续（增量回报 12%）；
    (b) 单阶段永续增速（增量回报 14%）。"""
    s = SCEN["base"]
    other = core_net_cash() + PARENT_PCT * NANFANG_EQUITY * s["nanfang_pb"] + NON_OP
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
    return g10, gp, target


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


def main():
    print("=== 601965 中国汽研 独立估值（价格日 2026-10-19，现价 %.2f，总股本 %.4f 亿股）===" % (PRICE, SHARES))
    ncc = core_net_cash()
    print("核心归母经调整净现金（剔除南方）: %.2f 亿（%.2f 元/股）" % (ncc, ncc / SHARES))
    print("南方试验场账面净资产 %.3f 亿 × 35.15%% = %.2f 亿；非经营投资 %.2f 亿" %
          (NANFANG_EQUITY, PARENT_PCT * NANFANG_EQUITY, NON_OP))
    for k in ("bear", "base", "bull"):
        o = scenario_value(k)
        print("\n[%s] p=%.2f  2026 正常化归母 %.2f（经营口径 %.2f）  %s" %
              (k, WEIGHTS[k], NORM_NP_2026[k], NORM_NP_2026[k] + AT_NET_INTEREST, SCEN[k]["note"]))
        for (y, g, npt, rr, oe, df) in o["rows"]:
            print("  %d  增速 %5.1f%%  经营归母 %6.2f  再投资率 %4.1f%%  所有者收益 %5.2f  折现因子 %.4f" %
                  (y, g * 100, npt, rr * 100, oe, df))
        print("  终值增速 %.1f%%  终值再投资率 %.1f%%  终值倍数(次年经营归母) %.1fx" %
              (SCEN[k]["g_t"] * 100, o["rr_t"] * 100, o["tv_pe"]))
        print("  2026H2 所有者收益 %.2f + 显性期现值 %.2f + 终值现值 %.2f = 经营价值 %.2f" %
              (o["oe_h2"], o["pv_explicit"], o["pv_tv"], o["op_value"]))
        print("  + 核心净现金 %.2f + 南方 %.2f + 非经营 %.2f + 制造处置期权 %.2f = 股权 %.2f 亿；终值占比 %.0f%%" %
              (ncc, o["nanfang"], NON_OP, SCEN[k]["manuf_option"], o["equity"], o["tv_share"] * 100))
        print("  V = %.2f 元/股" % o["v"])
    vw = weighted_v()
    pv = PRICE / vw
    print("\n加权 V = %.2f 元/股；P/V = %.3f → %s" % (vw, pv, verdict(pv)))
    print("股权成本 8%%: 加权 V = %.2f；10%%: 加权 V = %.2f" % (weighted_v(0.08), weighted_v(0.10)))
    for r in (0.08, 0.10):
        print("  r=%.0f%%  熊/基/牛 = %.2f / %.2f / %.2f" % (r * 100, *(scenario_value(k, r)["v"] for k in ("bear", "base", "bull"))))
    irr = implied_irr()
    print("现价隐含回报（基准情景）: %.2f%%" % (irr * 100))
    g10, gp, target = reverse_dcf()
    print("反向 DCF: 现价隐含经营价值 %.1f 亿；10 年经营归母增速 %.2f%%（再投资率=g/14%%，下限25%%）；单阶段永续增速 %.2f%%（增量回报 14%%）" %
          (target, g10 * 100, gp * 100))
    print("V 不变时各档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵" %
          (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print("\n证伪条件触发后的独立 V：")
    for cond, ddl, w in FALSIFIERS:
        print("  [%s] %s → V = %.2f" % (ddl, cond, weighted_v(COE, w)))
    # 基准情景增量回报敏感性（显性期与终值同时变动）
    keep = dict(SCEN["base"])
    for ro, rot in ((0.10, 0.09), (0.12, 0.11), (0.18, 0.15)):
        SCEN["base"]["ronic"], SCEN["base"]["ronic_t"] = ro, rot
        print("基准增量回报 %.0f%%/终值 %.0f%%: 基准 V = %.2f" % (ro * 100, rot * 100, scenario_value("base")["v"]))
    SCEN["base"].update(keep)
    # 再投资率交叉核对（基准）：显式资本开支与营运资金
    print("基准再投资交叉核对（核心，亿元）：")
    da = [5.9, 6.1, 6.3, 6.5, 6.7]
    capex = [7.5, 7.5, 7.8, 8.0, 8.2]
    nwc_ratio = 0.40
    rev = 53.0
    o = scenario_value("base")
    alt_pv = 0.0
    for (y, g, npt, rr, oe, df), d, c in zip(o["rows"], da, capex):
        drev = rev * g
        rev += drev
        reinv = c - d + nwc_ratio * drev
        print("  %d 资本开支 %.1f − 折旧摊销 %.1f + 营运资金 %.2f = 净再投资 %.2f → 再投资率 %.0f%%（模型 %.0f%%）" %
              (y, c, d, nwc_ratio * drev, reinv, reinv / npt * 100, rr * 100))
        alt_pv += (npt - reinv) * df
    alt_eq = o["oe_h2"] + alt_pv + o["pv_tv"] + core_net_cash() + o["nanfang"] + NON_OP
    print("  若资本开支按上表回落（再投资率约 19%%～27%%），基准 V = %.2f（模型取更保守的 g/增量回报）" % (alt_eq / SHARES))
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
