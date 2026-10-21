#!/usr/bin/env python3
"""金山办公（688111）独立估值：所有者收益 DCF（归母、无杠杆口径）+ 反向 DCF + 交叉验证。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在脚本内，出处见同目录上级
companies/688111_金山办公.md 第十节「来源」。
"""

# ---------------------------------------------------------------- 快照
PRICE = 233.88                 # 2026-10-20 收盘（brief.md）
SHARES = 4.6401                # 总股本，亿股（含回购专户，brief.md）
TREASURY = 0.00529811          # 截至 2026-10-16 回购 529,811 股（用于激励，不注销）
SHARES_EX_TREASURY = SHARES - TREASURY
COE = 0.09
VAL_YEAR = 2026.80             # 估值日 2026-10-20 的年内位置
SHARE_PRICE_MKT_CAP = PRICE * SHARES

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 55-57、114-115、130-131 页）
CASH = 13.8778                 # 货币资金
RESTRICTED = 0.0259            # 履约保函受限
TRADING_FA = 8.8148            # 交易性金融资产（结构性存款/理财）
DEP_1Y = 67.5454               # 一年内到期的定期存款及应收收益
DEP_OCA = 35.0857              # 其他流动资产中的定期存款及应收收益
DEP_ONCA = 28.3015             # 其他非流动资产中的定期存款及应收收益
PREPAID_CIT = 1.9379           # 所得税预缴（因基金浮盈预缴，汇算时抵减）
LEASE = 0.3396 + 0.3043        # 一年内到期的非流动负债（主要为租赁）+ 租赁负债
DIV_PAYABLE = 3.2960           # 应付股利，2026-07 已付
DTL_INTEREST = 0.4648          # 应收利息对应的递延所得税负债
BUYBACK_AFTER = 1.1498         # 2026-07～10-16 回购付现（buyback_20261017 第 1 页）
OP_RESERVE = 9.0               # 经营备付：约 2 个月付现经营支出
FUNDS_BOOK = 24.6126 + 9.1683  # 顺金顺赢 + 顺赢私募基金（权益法）账面
FUNDS_DTL = 2.1781             # 长期股权投资暂时性差异的递延所得税负债
OTHER_ASSOC = 34.6767 - FUNDS_BOOK   # 其余联营企业账面
OTHER_NC_FA = 0.1124           # 其他非流动金融资产

GROSS_CASH = CASH - RESTRICTED + TRADING_FA + DEP_1Y + DEP_OCA + DEP_ONCA + PREPAID_CIT
NET_CASH_ADJ = GROSS_CASH - LEASE - DIV_PAYABLE - DTL_INTEREST - BUYBACK_AFTER - OP_RESERVE
FUNDS_AFTER_TAX = FUNDS_BOOK - FUNDS_DTL

# ---------------------------------------------------------------- 盈利正常化
TAX_FUND = 0.10                # 基金收益递延税率（DTL 增量 1.7609 / 收益 17.6087）
# 2025：归母 18.3647；两只基金利润影响 1.7585（2025_annual_report 第 44 页）
NP25 = 18.3647
FUND25 = 1.7585
ONEOFF25 = 0.20                # 非经常性损益 0.3395 中剔除理财公允价值后的补助、营业外等（税后）
CORE25 = NP25 - FUND25 * (1 - TAX_FUND)
NORM25 = CORE25 - ONEOFF25
# 2026H1：归母 25.1759；两只基金利润影响 17.6087（2026H1_report 第 33-34 页）
NP26H1 = 25.1759
FUND26H1 = 17.6087
ONEOFF26H1 = 0.21              # 营业外赔偿收入 0.199、补助 0.028 等（税后）
CORE26H1 = NP26H1 - FUND26H1 * (1 - TAX_FUND)
NORM26H1 = CORE26H1 - ONEOFF26H1
# 2025H1：归母 7.4720；经调整 8.4714 = 10.8680/1.2829；股份支付 0.9336
NP25H1 = 7.4720
FUND25H1_AT = NP25H1 + 0.9336 - 10.8680 / 1.2829    # 基金税后影响（负值）
CORE25H1 = NP25H1 - FUND25H1_AT
NORM25H1 = CORE25H1 - 0.12
NORM25H2 = NORM25 - NORM25H1
# 资金收益（定期存款利息 + 理财处置 + 公允价值 + 财务费用利息收入 − 租赁利息）
TREASURY26H1 = 1.4189 + 0.1611 - 0.0547 + 0.0405 - 0.0082
TREASURY26_AT = 2 * TREASURY26H1 * (1 - 0.10)
NPOP26H1 = NORM26H1 - TREASURY26H1 * (1 - 0.10)      # 上半年经营性归母（不含资金收益）

REV25 = 59.2874
REV25H1 = 26.5712
REV26H1 = 33.1326

# ---------------------------------------------------------------- 情景
SCEN = {
    "bear": dict(p=0.25, h2_growth=0.05, rev26=71.0,
                 g=[0.07, 0.04, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
                 m=[0.215, 0.205, 0.200, 0.195, 0.190, 0.190, 0.190, 0.190, 0.190, 0.190],
                 k=0.25, tg=0.015, fund_haircut=0.50,
                 text="AI 原生产品与大厂免费工具分流付费，国内个人付费增长停滞、信创替换 2027 年后回落；"
                      "收入 2027 年 +7% 后年增 2%～4%，经营净利率降至 19%，营运资本流入系数 0.25，终值增长 1.5%，基金按账面税后 5 折"),
    "base": dict(p=0.50, h2_growth=0.17, rev26=72.2,
                 g=[0.16, 0.14, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04],
                 m=[0.240, 0.245, 0.250, 0.255, 0.260, 0.265, 0.265, 0.265, 0.265, 0.265],
                 k=0.40, tg=0.025, fund_haircut=0.25,
                 text="付费用户与 WPS 365 延续增长、AI 提升转化但单用户收入大体持平；收入 2027 年 +16% 递减至 2031 年 +9%、"
                      "2036 年 +4%，经营净利率 2027 年 24% 逐年升至 2032 年 26.5%，营运资本流入系数 0.40，终值增长 2.5%，基金按账面税后 75 折"),
    "bull": dict(p=0.25, h2_growth=0.25, rev26=73.0,
                 g=[0.22, 0.20, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08, 0.06, 0.04],
                 m=[0.250, 0.260, 0.270, 0.280, 0.290, 0.300, 0.300, 0.300, 0.300, 0.300],
                 k=0.50, tg=0.025, fund_haircut=0.0,
                 text="灵犀/Comate 按“订阅+用量”成功收费、海外与 WPS 365 高增；收入 2027 年 +22% 递减至 2031 年 +14%，"
                      "经营净利率升至 30%，营运资本流入系数 0.50，终值增长 2.5%，基金按账面税后全额"),
}
YEARS = list(range(2027, 2037))


def norm_np_2026(s):
    """2026 正常化归母（含净利息，剔除基金收益与一次性项目）。"""
    return NORM26H1 + NORM25H2 * (1 + s["h2_growth"])


def non_operating(s):
    return FUNDS_AFTER_TAX * (1 - s["fund_haircut"]) + OTHER_ASSOC + OTHER_NC_FA


def project(s):
    """返回 2026 下半年与 2027-2037 的收入、经营归母、营运资本流入与所有者收益。"""
    np26 = norm_np_2026(s)
    npop26 = np26 - TREASURY26_AT
    rev = [s["rev26"]]
    npop = [npop26]
    for gi, mi in zip(s["g"], s["m"]):
        rev.append(rev[-1] * (1 + gi))
        npop.append(rev[-1] * mi)
    # 终值年 2037
    rev.append(rev[-1] * (1 + s["tg"]))
    npop.append(rev[-1] * s["m"][-1])
    oe = [None]
    for i in range(1, len(rev)):
        oe.append(npop[i] + s["k"] * (rev[i] - rev[i - 1]))
    h2_rev_inc = (s["rev26"] - REV26H1) - (REV25 - REV25H1)
    oe_h2_26 = (npop26 - NPOP26H1) + s["k"] * h2_rev_inc
    return dict(rev=rev, npop=npop, oe=oe, oe_h2_26=oe_h2_26, np26=np26, npop26=npop26,
                oe26_full=npop26 + s["k"] * (s["rev26"] - REV25))


def value(s, r, shares=SHARES, detail=False):
    pr = project(s)
    pv_explicit = 0.0
    for i, y in enumerate(YEARS, start=1):
        t = y + 0.5 - VAL_YEAR
        pv_explicit += pr["oe"][i] / (1 + r) ** t
    t_last = YEARS[-1] + 0.5 - VAL_YEAR
    tv = pr["oe"][-1] / (r - s["tg"])
    pv_tv = tv / (1 + r) ** t_last
    ops = pr["oe_h2_26"] + pv_explicit + pv_tv
    eq = ops + NET_CASH_ADJ + non_operating(s)
    v = eq / shares
    if detail:
        return dict(v=v, eq=eq, ops=ops, pv_explicit=pv_explicit, pv_tv=pv_tv,
                    tv_share=pv_tv / eq, h2=pr["oe_h2_26"], proj=pr)
    return v


def weighted(r, probs=None, shares=SHARES, scen=None):
    scen = scen or SCEN
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * value(scen[k], r, shares) for k in scen)


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def reverse_dcf_growth():
    """基准 2026 全年所有者收益起步，2027-2036 年恒定增速 g，之后 2.5%，使每股价值等于现价。"""
    base = SCEN["base"]
    pr = project(base)
    oe0 = pr["oe26_full"]
    fixed = NET_CASH_ADJ + non_operating(base) + pr["oe_h2_26"]

    def v_of(g):
        pv = 0.0
        oe = oe0
        for y in YEARS:
            oe *= 1 + g
            pv += oe / (1 + COE) ** (y + 0.5 - VAL_YEAR)
        tv = oe * 1.025 / (COE - 0.025)
        pv += tv / (1 + COE) ** (YEARS[-1] + 0.5 - VAL_YEAR)
        return (fixed + pv) / SHARES

    return solve(v_of, -0.05, 0.40, PRICE), oe0


def implied_perpetual_growth():
    """单阶段：现价 = 净现金 + 非经营资产 + 2027 所有者收益 / (r − g)。"""
    base = SCEN["base"]
    pr = project(base)
    ops_mkt = PRICE * SHARES - NET_CASH_ADJ - non_operating(base) - pr["oe_h2_26"]
    oe27 = pr["oe"][1]
    return COE - oe27 / ops_mkt


def main():
    print("== 金山办公 688111 独立估值（价格日 2026-10-20，现价 %.2f 元，总股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("市值 %.1f 亿元" % SHARE_PRICE_MKT_CAP)
    print("\n[净现金与非经营资产，亿元]")
    print("  现金类毛额（货币资金扣受限 + 理财 + 三处定期存款 + 预缴所得税）= %.2f" % GROSS_CASH)
    print("  经调整净现金（再扣租赁、应付股利、应收利息递延税、6/30 后回购付现、经营备付 %.1f）= %.2f"
          % (OP_RESERVE, NET_CASH_ADJ))
    print("  两只基金账面 %.2f − 递延税 %.2f = 税后 %.2f；其余联营 %.2f；其他非流动金融资产 %.2f"
          % (FUNDS_BOOK, FUNDS_DTL, FUNDS_AFTER_TAX, OTHER_ASSOC, OTHER_NC_FA))
    print("\n[盈利正常化，亿元]")
    print("  2025 归母 %.2f − 基金收益税后 %.2f = %.2f；再剔一次性 → 正常化 %.2f" % (NP25, FUND25 * 0.9, CORE25, NORM25))
    print("  2025H1 剔基金后 %.2f，正常化 %.2f；2025H2 正常化 %.2f" % (CORE25H1, NORM25H1, NORM25H2))
    print("  2026H1 归母 %.2f − 基金收益税后 %.2f = %.2f；正常化 %.2f（同比 %+.1f%%）"
          % (NP26H1, FUND26H1 * 0.9, CORE26H1, NORM26H1, (NORM26H1 / NORM25H1 - 1) * 100))
    print("  2026H1 资金收益税前 %.2f；全年税后约 %.2f；上半年经营性归母 %.2f" % (TREASURY26H1, TREASURY26_AT, NPOP26H1))
    print("  2026 正常化归母：熊 %.2f / 基准 %.2f / 牛 %.2f"
          % tuple(norm_np_2026(SCEN[k]) for k in ("bear", "base", "bull")))

    print("\n[三情景，股权成本 9%]")
    res = {}
    for k in ("bear", "base", "bull"):
        d = value(SCEN[k], COE, detail=True)
        res[k] = d
        pr = d["proj"]
        gr = [pr["oe"][i + 1] / pr["oe"][i] - 1 if i > 0 else pr["oe"][1] / pr["oe26_full"] - 1 for i in range(5)]
        print("  %s：V = %.2f 元（经营部分 %.1f 亿 = 2026H2 %.1f + 明确期现值 %.1f + 终值现值 %.1f；终值占股权价值 %.0f%%）"
              % (k, d["v"], d["ops"], d["h2"], d["pv_explicit"], d["pv_tv"], d["tv_share"] * 100))
        print("     2026 全年所有者收益 %.2f；2027-2031 所有者收益 %s；增速 %s"
              % (pr["oe26_full"], " ".join("%.1f" % x for x in pr["oe"][1:6]),
                 " ".join("%+.1f%%" % (x * 100) for x in gr)))
        print("     收入 2026→2031：%s" % " ".join("%.1f" % x for x in pr["rev"][:6]))
    vw = weighted(COE)
    pv = PRICE / vw
    print("  加权 V = %.2f 元；P/V = %.3f → %s" % (vw, pv, verdict(pv)))
    vw_ex = weighted(COE, shares=SHARES_EX_TREASURY)
    print("  剔除回购专户（%.4f 亿股）：加权 V = %.2f 元，P/V = %.3f" % (SHARES_EX_TREASURY, vw_ex, PRICE / vw_ex))

    v8, v10 = weighted(0.08), weighted(0.10)
    print("\n[股权成本敏感性] 8%%：V = %.2f（P/V %.3f）；10%%：V = %.2f（P/V %.3f）" % (v8, PRICE / v8, v10, PRICE / v10))
    for k in ("bear", "base", "bull"):
        print("  %s：8%% %.2f / 9%% %.2f / 10%% %.2f" % (k, value(SCEN[k], 0.08), value(SCEN[k], 0.09), value(SCEN[k], 0.10)))

    irr = solve(lambda r: value(SCEN["base"], r), 0.03, 0.20, PRICE)
    print("\n[现价隐含回报] 基准情景所有者收益流（含终值与净现金）使现值等于现价的折现率 = %.2f%%" % (irr * 100))
    g10, oe0 = reverse_dcf_growth()
    gp = implied_perpetual_growth()
    print("[反向 DCF] 2026 所有者收益 %.2f 起步：2027-2036 年需年增 %.1f%%（之后 2.5%%）；或单阶段永续增速 %.2f%%"
          % (oe0, g10 * 100, gp * 100))

    print("\n[交叉验证]")
    ev = SHARE_PRICE_MKT_CAP - NET_CASH_ADJ - non_operating(SCEN["base"])
    npop26 = project(SCEN["base"])["npop26"]
    ebit26 = npop26 / (1 - 0.07)
    print("  EV（市值 − 经调整净现金 − 基准非经营资产）= %.1f 亿；EV/2026 经营归母 %.1f×；EV/EBIT（税率 7%%）%.1f×"
          % (ev, ev / npop26, ev / ebit26))
    print("  市值/2026 基准正常化归母 = %.1f×；市值/TTM 报告归母 36.07 = %.1f×" % (SHARE_PRICE_MKT_CAP / norm_np_2026(SCEN["base"]),
                                                                    SHARE_PRICE_MKT_CAP / 36.07))
    div_yield = 1.25 / PRICE
    bb_yield = (2.5 + 5.0) / 2 / SHARE_PRICE_MKT_CAP
    print("  股息率 %.2f%% + 回购（方案中值 3.75 亿/年，用于激励）%.2f%% = %.2f%%" % (div_yield * 100, bb_yield * 100,
                                                                     (div_yield + bb_yield) * 100))
    print("  PB = %.2f（归母权益 150.77）" % (SHARE_PRICE_MKT_CAP / 150.7674))

    print("\n[证伪条件触发后的 V]")
    fal = falsifiers()
    for name, v in fal:
        print("  %s → V = %.2f 元（P/V %.3f）" % (name, v, PRICE / v))

    print("\n[进入各档的价格（V 不变）] ≤0.75×V = %.1f；≤0.90×V = %.1f；≤1.10×V = %.1f" % (0.75 * vw, 0.90 * vw, 1.10 * vw))

    print("\n[2026Q3 估计] 收入 %.1f 亿（15.21×1.20，区间 17.8–18.8）；剔基金归母约 %.1f 亿（2025Q3 约 4.35×1.15）；"
          "公司口径经调整归母约 %.1f 亿（加回股份支付约 0.8）" % (15.21 * 1.20, 4.35 * 1.15, 4.35 * 1.15 + 0.8))

    # 再投资率与增量回报（经济口径：研发费用率 35% 中超出维持水平 25% 的部分视为增长性再投资）
    b = project(SCEN["base"])
    growth_rd = 0.10 * SCEN["base"]["rev26"] * (1 - 0.07)
    rr = growth_rd / (b["oe26_full"] + growth_rd)
    g5 = (b["oe"][5] / b["oe26_full"]) ** (1 / 5) - 1
    print("[再投资] 增长性研发（税后）%.2f 亿；再投资率 %.1f%%；2026→2031 所有者收益年复合 %.1f%%；增量回报 %.1f%%"
          % (growth_rd, rr * 100, g5 * 100, g5 / rr * 100))

    # 分部核对：智谱穿透（199.7 万股，HKD/RMB 按 0.92 假设）
    zp_shares = 521.14 * (0.3332 * 0.999986 + 0.0849 * 0.588235) / 1e4   # 亿股
    for px, tag in ((693.5, "2026-03-31 收盘"), (641.5, "约 2026-10-09 行情页")):
        print("  智谱穿透 %.4f 亿股 × %.1f 港元（%s）× 0.92 = %.1f 亿元" % (zp_shares, px, tag, zp_shares * px * 0.92))
    return vw


def falsifiers():
    out = []
    # F1：AI 分流个人付费（2026 年报）
    out.append(("F1 国内年度付费个人用户 <5,000 万且国内个人收入增速 <8%（2026 年报）：概率改为 熊0.50/基准0.40/牛0.10",
                weighted(COE, probs={"bear": 0.50, "base": 0.40, "bull": 0.10})))
    # F2：毛利率压缩（AI 推理成本）——基准与牛市经营净利率各降 2 个百分点
    scen2 = {k: dict(v) for k, v in SCEN.items()}
    for k in ("base", "bull"):
        scen2[k]["m"] = [x - 0.02 for x in scen2[k]["m"]]
    out.append(("F2 2026 全年毛利率 <82.5% 或 2027Q1 毛利率 <82%：基准/牛市利率各 −2pp", weighted(COE, scen=scen2)))
    # F3：WPS 365 低于激励触发值或 WPS 软件收入下滑
    out.append(("F3 2026 年 WPS 365 收入 <9.0 亿（激励触发值）或 WPS 软件收入同比下滑：概率 熊0.35/基准0.55/牛0.10",
                weighted(COE, probs={"bear": 0.35, "base": 0.55, "bull": 0.10})))
    # F4：基金账面大幅减记（三季报/年报两只基金合计 <15 亿）
    scen4 = {k: dict(v) for k, v in SCEN.items()}
    for k in scen4:
        scen4[k]["fund_haircut"] = 1 - (15.0 - 0.3) / FUNDS_AFTER_TAX   # 账面 15 亿、递延税约 0.3 亿
    out.append(("F4 两只基金账面合计 <15 亿（2026 三季报/年报）：基金按 15 亿税后计", weighted(COE, scen=scen4)))
    # F5（向上）：2026 正常化归母 ≥21 亿且 2027H1 收入增速 ≥20%
    out.append(("F5 向上：2026 正常化归母 ≥21 亿且 2027H1 收入增速 ≥20%：概率 熊0.10/基准0.45/牛0.45",
                weighted(COE, probs={"bear": 0.10, "base": 0.45, "bull": 0.45})))
    return out


if __name__ == "__main__":
    main()
