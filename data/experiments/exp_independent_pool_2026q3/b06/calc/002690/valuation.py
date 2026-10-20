#!/usr/bin/env python3
"""002690 美亚光电 独立估值（OI-291 b06，价格日 2026-10-20）。

用法：python3 valuation.py
输入全部写在本脚本内（来源见正文 companies/002690_美亚光电.md）。
金额单位：亿元；每股价值：元/股。
方法：归母所有者收益 DCF（无杠杆口径，经调整净现金为正）＋ 经调整净现金 ＋ 非经营资产；
      熊/基准/牛三情景概率加权；8%/10% 股权成本敏感性；现价隐含回报与反向 DCF。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 15.16                    # 2026-10-20 收盘（brief）
SHARES = 8.8223                  # 总股本，亿股（brief；无回购专户、无拟注销股份）
VAL_DATE = date(2026, 10, 20)
COE = 0.09

# ---------------------------------------------------------------- 2026-06-30 资产负债（2026H1_report 第 16、18、37-38 页）
CASH = 17.4040                   # 货币资金；交易性金融资产 0
RESTRICTED = 0.0917              # 承兑保证金 + 履约保证金（第 18 页）
OPER_RESERVE = 2.00              # 经营备付：约 1.4 个月付现成本（年付现成本约 17 亿）
DEBT_LIKE = 0.0050               # 交易性金融负债（远期结售汇浮亏）；无借款、无租赁负债
DECLARED_DIV = 0.0               # 2025 年度股利已于 2026-05-14 付讫；中期不分配
NET_CASH_ADJ = CASH - RESTRICTED - OPER_RESERVE - DEBT_LIKE - DECLARED_DIV

# 非经营资产
COFCO_FV = 1.3503                # 其他权益工具投资：中粮科工，2026-06-30 公允价值（第 38、91 页）
COFCO_UNREAL_GAIN = 0.8542       # 累计计入其他综合收益的利得
TAX_ON_GAIN = 0.15
DENTIFY_REMAIN = 1.98 + 0.0096 - 0.2410   # 登特菲判赔余额（判赔 1.98 亿 + 维权费 − 已执行 2409.85 万）
DENTIFY_RECOVERY = 0.10          # 预期回收率（被执行人为小型 CBCT 企业，回收存疑）
NON_OP = COFCO_FV - TAX_ON_GAIN * COFCO_UNREAL_GAIN + DENTIFY_REMAIN * DENTIFY_RECOVERY * (1 - TAX_ON_GAIN)

# ---------------------------------------------------------------- 报告数（2025_annual_report、2026H1_report）
REV_2025 = 24.0686
NP_2025 = 7.1912
DNP_2025 = 7.0710
NP_TTM = 7.1912 - 3.0276 + 3.1495        # 2025 − 2025H1 + 2026H1
DNP_TTM = 7.0710 - 2.9526 + 2.9326
EQUITY_LATEST = 25.7366
FX_LOSS_TTM_PRETAX = 0.3955 + (0.2392 + 0.0201)   # 2026H1 汇兑损失 + 2025H2（全年损失 0.2392 + 上半年收益 0.0201）
NONREC_TTM_AFTERTAX = (NP_2025 - DNP_2025) - (3.0276 - 2.9526) + (3.1495 - 2.9326)  # 非经常性损益 TTM（税后）
INTEREST_TTM_PRETAX = 0.4965 - 0.2238 + 0.1796     # 利息收入 TTM
TAX_TTM = 0.129                                    # 实际所得税率（2025 12.8%，2026H1 12.9%）
REV_TTM = 24.0686 - 10.2255 + 10.6551
# 历史年末估值（数据包第八节）：PE 2014-2025，PB
HIST_PE = {2014: 47.9, 2015: 94.2, 2016: 46.2, 2017: 35.7, 2018: 32.1, 2019: 48.5, 2020: 68.3,
           2021: 49.7, 2022: 28.9, 2023: 23.3, 2024: 20.1, 2025: 25.2}
HIST_PB = {2014: 7.08, 2015: 14.18, 2016: 7.04, 2017: 5.93, 2018: 6.23, 2019: 11.09, 2020: 13.04,
           2021: 10.14, 2022: 7.96, 2023: 6.28, 2024: 4.69, 2025: 6.20}
# 2025Q3 单季（数据包第五节），用于三季报预估
Q3_2025 = dict(rev=6.7149, gm=0.542, np=2.1610, dnp=2.1390)

# ---------------------------------------------------------------- 情景
# core_margin = 核心 EBIT（不含利息收入、汇兑、投资收益、非经常补助；含软件退税与减值）/ 营收
SCEN = {
    "bear": dict(p=0.25, rev26=24.50, growth=[0.00, 0.01, 0.01, 0.01, 0.01], g_term=0.010,
                 core_margin=0.287, tax=0.150, int_yield=0.014, ronic=0.15),
    "base": dict(p=0.50, rev26=24.90, growth=[0.045, 0.045, 0.040, 0.035, 0.030], g_term=0.020,
                 core_margin=0.3215, tax=0.135, int_yield=0.017, ronic=0.25),
    "bull": dict(p=0.25, rev26=25.10, growth=[0.080, 0.070, 0.060, 0.050, 0.040], g_term=0.025,
                 core_margin=0.338, tax=0.130, int_yield=0.019, ronic=0.40),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
AVG_CASH_2026 = 19.5             # 2026 年平均现金（6 月末 17.4，年末约 21-22）
INCR_CAP_RATIO = 0.20            # 显性期每 1 元新增营收需新增营运资本 0.12 + 其他固定资产 0.08
PROJECT_CAPEX = {2026: 0.55, 2027: 0.75}   # 涂装钣金扩产项目：预算 1.85，6 月末累计 0.54（第 19 页）
H2_SHARE = 0.57                  # 下半年占全年利润比例（2023-2025 年为 54%-58%）
SEASONAL_WC_RELEASE = 0.60       # 上半年季节性占用的营运资本（经营现金流 2.67 vs 净利 3.15 + 折旧 0.17）下半年回流


def yrs(d):
    return (d - VAL_DATE).days / 365.25


def nopat(rev, s):
    return rev * s["core_margin"] * (1 - s["tax"])


def flows(s):
    """返回 [(期间, 距估值日年数, 营收, NOPAT, 再投资, 所有者收益)]。"""
    out = []
    rev26 = s["rev26"]
    n26 = nopat(rev26, s)
    reinv_h2 = PROJECT_CAPEX[2026] + 0.5 * INCR_CAP_RATIO * (rev26 - REV_2025) - SEASONAL_WC_RELEASE
    out.append(("2026H2", yrs(date(2026, 9, 30)), rev26, n26 * H2_SHARE, reinv_h2, n26 * H2_SHARE - reinv_h2))
    rev = rev26
    for y, g in zip(YEARS, s["growth"]):
        new = rev * (1 + g)
        n = nopat(new, s)
        reinv = INCR_CAP_RATIO * (new - rev) + PROJECT_CAPEX.get(y, 0.0)
        out.append((str(y), yrs(date(y, 7, 1)), new, n, reinv, n - reinv))
        rev = new
    return out


def value(s, r=COE, detail=False):
    fl = flows(s)
    pv = sum(oe / (1 + r) ** t for _, t, _, _, _, oe in fl)
    last_rev, last_t = fl[-1][2], fl[-1][1]
    g = s["g_term"]
    n_next = nopat(last_rev * (1 + g), s)
    oe_next = n_next * (1 - g / s["ronic"])
    tv = oe_next / (r - g)                 # 年中惯例：首笔终值现金流在 2032 年中，终值落在 2031 年中
    pv_tv = tv / (1 + r) ** last_t
    equity = pv + pv_tv + NET_CASH_ADJ + NON_OP
    if detail:
        return equity / SHARES, dict(pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv), flows=fl, oe_next=oe_next)
    return equity / SHARES


def norm_np_2026(s):
    """2026 正常化归母净利：核心经营 NOPAT + 税后净利息（剔除汇兑与一次性项目）。"""
    return nopat(s["rev26"], s) + AVG_CASH_2026 * s["int_yield"] * (1 - s["tax"])


def weighted(r=COE):
    return sum(s["p"] * value(s, r) for s in SCEN.values())


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
    base = SCEN["base"]
    return solve(lambda r: value(base, r), 0.04, 0.20, PRICE)


def reverse_perpetual_g():
    """2026H2 按基准，自 2027 年起以基准 2026 年 NOPAT 为基数按永续增速 g 增长（RONIC 25%）：求现价隐含的 g。"""
    b = SCEN["base"]
    h2 = flows(b)[0]
    pv_h2 = h2[5] / (1 + COE) ** h2[1]
    n26 = nopat(b["rev26"], b)
    t1 = yrs(date(2027, 7, 1))
    op_value = PRICE * SHARES - NET_CASH_ADJ - NON_OP

    def v(g):
        oe27 = n26 * (1 + g) * (1 - g / b["ronic"])
        return pv_h2 + oe27 / (COE - g) / (1 + COE) ** (t1 - 1.0)

    return solve(v, -0.05, 0.085, op_value)


def reverse_10y_g():
    """10 年营收复合增速 g（利润率、税率按基准），终值增速 2%：使每股价值 = 现价。"""
    b = dict(SCEN["base"])

    def v(g):
        s = dict(b)
        s["growth"] = [g] * 5
        fl = flows(s)
        # 显性 2027-2031 用 flows，2032-2036 继续 g，之后 2%
        pv = sum(oe / (1 + COE) ** t for _, t, _, _, _, oe in fl)
        rev = fl[-1][2]
        t = fl[-1][1]
        for _ in range(5):
            new = rev * (1 + g)
            n = nopat(new, s)
            oe = n - INCR_CAP_RATIO * (new - rev)
            t += 1
            pv += oe / (1 + COE) ** t
            rev = new
        n_next = nopat(rev * 1.02, s)
        tv = n_next * (1 - 0.02 / s["ronic"]) / (COE - 0.02)
        pv += tv / (1 + COE) ** t
        return (pv + NET_CASH_ADJ + NON_OP) / SHARES

    return solve(v, -0.10, 0.20, PRICE)


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def falsifier_values():
    """证伪触发后的独立 V（元/股）。"""
    b = SCEN["base"]
    out = {}
    # F1：色选机毛利率回落至 51% 以下（核心利润率降 2.2pp），增长不变
    s = dict(b); s["core_margin"] = b["core_margin"] - 0.022
    out["F1_色选机毛利率<51%"] = value(s)
    # F2：2027 年营收增速 ≤ 1%（2026 年营收 < 24.5 亿且 2027 年无增长），按熊市增长、基准利润率
    s = dict(b); s["rev26"] = 24.5; s["growth"] = [0.0, 0.01, 0.01, 0.01, 0.01]; s["g_term"] = 0.01; s["ronic"] = 0.15
    out["F2_营收停滞"] = value(s)
    # F3：高新技术企业资格未续（税率 25%，研发加计扣除仍在：有效约 22%）
    s = dict(b); s["tax"] = 0.22
    out["F3_高新资格未续"] = value(s)
    # F4：口腔未见底（2026 年医疗收入 < 4.0 亿且毛利率 < 47%）：营收基数 −0.5 亿、各年增速 −0.5pp、核心利润率 −0.6pp
    s = dict(b); s["rev26"] = b["rev26"] - 0.5; s["growth"] = [g - 0.005 for g in b["growth"]]
    s["core_margin"] = b["core_margin"] - 0.006
    out["F4_口腔未见底"] = value(s)
    # F5：分红降到 0.60 元/股以下且无对应资本开支，或 >5 亿非主业投资 → 资本配置恶化：经调整净现金按 7 折计
    out["F5_现金7折"] = value(b) - 0.3 * NET_CASH_ADJ / SHARES
    # 参考：熊市情景整体兑现
    out["参考_熊市"] = value(SCEN["bear"])
    return out


def main():
    print("== 002690 美亚光电 独立估值（价格日 2026-10-20，现价 %.2f 元，股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("经调整净现金 %.2f 亿（现金 %.2f − 受限 %.2f − 经营备付 %.2f − 类债务 %.3f）"
          % (NET_CASH_ADJ, CASH, RESTRICTED, OPER_RESERVE, DEBT_LIKE))
    print("非经营资产 %.2f 亿（中粮科工税后 %.2f + 登特菲判赔预期回收 %.2f）"
          % (NON_OP, COFCO_FV - TAX_ON_GAIN * COFCO_UNREAL_GAIN, DENTIFY_REMAIN * DENTIFY_RECOVERY * (1 - TAX_ON_GAIN)))
    print("报告数：2025 营收 %.2f、归母 %.2f、扣非 %.2f；TTM 归母 %.2f、扣非 %.2f；TTM 汇兑损失(税前) %.2f；归母权益 %.2f"
          % (REV_2025, NP_2025, DNP_2025, NP_TTM, DNP_TTM, FX_LOSS_TTM_PRETAX, EQUITY_LATEST))
    print()
    for k, s in SCEN.items():
        v, d = value(s, detail=True)
        print("[%s] p=%.2f  V=%.2f 元/股  P/V=%.3f  2026 正常化归母 %.2f 亿  终值占经营价值 %.0f%%"
              % (k, s["p"], v, PRICE / v, norm_np_2026(s), 100 * d["tv_share"]))
        for name, t, rev, n, reinv, oe in d["flows"]:
            print("    %-6s t=%5.2f 营收 %6.2f NOPAT %5.2f 再投资 %5.2f 所有者收益 %5.2f" % (name, t, rev, n, reinv, oe))
        print("    2032 终值首年所有者收益 %.2f（g=%.1f%%，RONIC=%.0f%%）；显性期现值 %.1f，终值现值 %.1f"
              % (d["oe_next"], 100 * s["g_term"], 100 * s["ronic"], d["pv_explicit"], d["pv_tv"]))
    vw = weighted()
    print()
    print("概率加权 V = %.2f 元/股；P/V = %.3f → %s" % (vw, PRICE / vw, band(PRICE / vw)))
    print("股权成本 8%%：熊 %.2f / 基 %.2f / 牛 %.2f，加权 %.2f"
          % (value(SCEN["bear"], 0.08), value(SCEN["base"], 0.08), value(SCEN["bull"], 0.08), weighted(0.08)))
    print("股权成本 10%%：熊 %.2f / 基 %.2f / 牛 %.2f，加权 %.2f"
          % (value(SCEN["bear"], 0.10), value(SCEN["base"], 0.10), value(SCEN["bull"], 0.10), weighted(0.10)))
    print("现价隐含回报（基准现金流）= %.2f%%" % (100 * implied_irr()))
    print("反向 DCF：现价隐含永续增速 %.2f%%（RONIC 25%%）；隐含 10 年营收复合增速 %.2f%%（之后 2%%）"
          % (100 * reverse_perpetual_g(), 100 * reverse_10y_g()))
    print("V 不变时各档价格：≤%.2f 明显低估；%.2f-%.2f 温和低估；%.2f-%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    print("证伪触发后的 V：")
    for k, v in falsifier_values().items():
        print("    %s: %.2f" % (k, v))
    # 正常化桥：TTM 报告归母 → 剔除一次性与汇兑 → 基准 2026 正常化
    core_ttm = NP_TTM - NONREC_TTM_AFTERTAX + FX_LOSS_TTM_PRETAX * (1 - TAX_TTM)
    core_ttm_ex_int = core_ttm - INTEREST_TTM_PRETAX * (1 - TAX_TTM)
    print()
    print("正常化桥：TTM 归母 %.2f − 非经常 %.2f + 汇兑损失(税后) %.2f = 核心(含利息) %.2f；"
          "剔利息后经营 %.2f（税前核心利润率 %.1f%%）→ 基准 2026 正常化归母 %.2f"
          % (NP_TTM, NONREC_TTM_AFTERTAX, FX_LOSS_TTM_PRETAX * (1 - TAX_TTM), core_ttm, core_ttm_ex_int,
             100 * core_ttm_ex_int / (1 - TAX_TTM) / REV_TTM, norm_np_2026(SCEN["base"])))
    # 三季报预估（2026-10-27 披露）：营收 +4%，毛利率 54.5%，汇兑损失约 0.13 亿（人民币中间价 6.8109→6.7351）
    # 税前：2025Q3 税前 + 毛利增量 − 费用增量（费用约 1.40 亿×4%）− 利息收入减少 0.05 − 汇兑损失增加 0.07 − 其他收益 0.01
    q3_rev = Q3_2025["rev"] * 1.04
    d_fx = 0.07
    q3_pretax = Q3_2025["np"] / 0.87 + (q3_rev * 0.545 - Q3_2025["rev"] * Q3_2025["gm"]) \
        - 0.04 * 1.40 - 0.05 - d_fx - 0.01
    q3_np = q3_pretax * 0.87
    print("2026Q3 预估：营收 %.2f 亿（+4%%），归母约 %.2f 亿（2025Q3 %.2f，%+.1f%%），剔汇兑增量后 %+.1f%%"
          % (q3_rev, q3_np, Q3_2025["np"], 100 * (q3_np / Q3_2025["np"] - 1),
             100 * ((q3_np + d_fx * 0.87) / Q3_2025["np"] - 1)))
    # 交叉验证
    mcap = PRICE * SHARES
    ev = mcap - CASH + DEBT_LIKE - COFCO_FV
    core_ebit_ttm = core_ttm_ex_int / (1 - TAX_TTM)
    pes = sorted(HIST_PE.values())
    print()
    print("交叉验证：市值 %.2f 亿；股息率 %.2f%%（无回购）；市值/基准正常化归母 %.1f×；剔现金 PE %.1f×；"
          "EV %.1f 亿，EV/TTM 核心 EBIT %.1f×；历史年末 PE %.1f-%.1f×（中位 %.1f×），PB %.2f-%.2f×，现 PB %.2f×"
          % (mcap, 100 * 0.70 / PRICE, mcap / norm_np_2026(SCEN["base"]),
             (mcap - NET_CASH_ADJ - NON_OP) / nopat(SCEN["base"]["rev26"], SCEN["base"]),
             ev, ev / core_ebit_ttm, pes[0], pes[-1], (pes[5] + pes[6]) / 2,
             min(HIST_PB.values()), max(HIST_PB.values()), mcap / EQUITY_LATEST))
    b = SCEN["base"]
    fl = flows(b)
    rr = sum(f[4] for f in fl[1:]) / sum(f[3] for f in fl[1:])
    g5 = (fl[-1][3] / nopat(b["rev26"], b)) ** (1 / 5) - 1
    cum_reinv = PROJECT_CAPEX[2026] + sum(f[4] for f in fl[1:])
    incr_ret = (fl[-1][3] - nopat(b["rev26"], b)) / cum_reinv
    oe = [f[5] for f in fl[1:]]
    print("基准再投资率（2027-2031 再投资/NOPAT）%.1f%%；NOPAT 2026→2031 复合增速 %.1f%%；"
          "增量回报（NOPAT 增量 / 2026H2 起累计再投资）%.0f%%；终值期再投资率 %.1f%%（g/RONIC）"
          % (100 * rr, 100 * g5, 100 * incr_ret, 100 * b["g_term"] / b["ronic"]))
    print("基准所有者收益 2027-2031：" + " / ".join("%.2f" % x for x in oe))


if __name__ == "__main__":
    main()
