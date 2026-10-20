"""600285 羚锐制药 独立估值（OI-291 b04，价格日 2026-10-19）。

用法：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在本脚本内，出处见同目录上级
companies/600285_羚锐制药.md 的「来源」一节（页码为 PDF 物理页）。

口径：
- 所有者收益（OE）= 经营 NOPAT（不含利息与理财收益）× (1 − 增长/增量回报)；
  现金、存单与理财按面值计入净现金，利息收入不进 OE，避免重复。
- 估值基准日 2026-10-19；2027 年起逐年现金流按年中折现，2026 年下半年的经营
  收益按年底计入，再整体折回 0.2 年；终值 = OE_2032 /(r − g) 并做年中调整。
- 经调整净现金为正，按无杠杆口径全额扣除有息负债与类债务；框架新增的有杠杆
  口径（净现金为负时适用）对本公司不适用。
"""

PRICE = 21.29          # 2026-10-19 收盘，腾讯行情
SHARES = 5.6712        # 亿股，总股本 567,115,486 股（含限制性股票 62.5 万股），无回购专户
COE = 0.09

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report 第 37–39、94–121、124–125 页）
CASH_LIKE = {
    "货币资金（无受限，第 93 页）": 7.437,
    "交易性金融资产（理财）": 1.303,
    "一年内到期的非流动资产（定存 1.270 + 大额存单 5.477）": 6.747,
    "其他流动资产中的大额存单": 0.175,
    "其他非流动资产中的大额存单 6.747 + 定期存款 2.084": 8.831,
}
DEBT_LIKE = {
    "短期借款（票据贴现借款）": 3.611,
    "租赁负债（含一年内到期）": 0.055,
    "其他应付款：联营企业信阳悦合房地产借款": 0.572,
    "其他应付款：暂借款": 0.541,
    "其他应付款：限制性股票回购义务": 0.056,
}
OP_RESERVE = 2.5       # 经营备付：约 1 个月付现成本（年付现成本约 29–30 亿）
FLOAT_EXCESS = 1.1     # 年中计提推广费等经营性负债高于全年平均的季节性部分（年中 15.69 vs 年中常态约 14.5）
NONOP = {              # 账面值, 折扣系数
    "其他非流动金融资产（权益工具，含厦门金镒兴私募基金已实缴 0.5）": (1.242, 0.8),
    "其他权益工具投资（中原银行 0.302 等）": (0.427, 0.8),
    "长期股权投资（信阳悦合房地产 40%，房地产开发）": (0.726, 0.5),
}
FUND_UNFUNDED = 2.0    # 私募基金认缴 2.5 亿、已实缴 0.5 亿
FUND_HAIRCUT = 0.2     # 未实缴部分预期折损 20%


def net_cash_adj():
    return sum(CASH_LIKE.values()) - sum(DEBT_LIKE.values()) - OP_RESERVE - FLOAT_EXCESS


def nonop_value():
    return sum(b * h for b, h in NONOP.values()) - FUND_UNFUNDED * FUND_HAIRCUT


# ---------------------------------------------------------------- 情景
# rev26：2026 年营收（H1 实际 21.48 + H2 估计）；h2_rev/h2_m：2026H2 营收与核心经营利润率
# m_path：2027–2031 核心经营利润率（营收−营业成本−税金及附加−销售−管理−研发，不含投资收益）
# m_norm：穿越周期的正常化核心利润率，用于 2026 正常化归母净利
# other：信用减值+其他收益+营业外收支占营收比例（负为净损失）
SCEN = {
    "bear": dict(p=0.25, rev26=37.97, h2_rev=16.49, h2_m=0.155, m_norm=0.175,
                 m_path=[0.195, 0.175, 0.175, 0.175, 0.175],
                 g=[-0.04, -0.02, 0.00, 0.01, 0.01], gT=0.010, ronic=0.25,
                 tax=0.150, minority=0.007, other=-0.0030, net_int=0.40),
    "base": dict(p=0.50, rev26=38.85, h2_rev=17.37, h2_m=0.175, m_norm=0.205,
                 m_path=[0.215, 0.210, 0.205, 0.205, 0.205],
                 g=[0.015, 0.025, 0.030, 0.030, 0.025], gT=0.020, ronic=0.40,
                 tax=0.135, minority=0.007, other=-0.0015, net_int=0.45),
    "bull": dict(p=0.25, rev26=39.72, h2_rev=18.24, h2_m=0.185, m_norm=0.225,
                 m_path=[0.225, 0.225, 0.225, 0.225, 0.225],
                 g=[0.06, 0.06, 0.05, 0.05, 0.04], gT=0.025, ronic=0.50,
                 tax=0.135, minority=0.008, other=-0.0005, net_int=0.45),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def nopat(rev, m, s):
    pre = rev * m + rev * s["other"]
    return pre * (1 - s["tax"]) * (1 - s["minority"])


def norm_np_2026(s):
    """2026 正常化归母净利：穿越周期利润率，含净利息（税后），剔除一次性项目。"""
    return nopat(s["rev26"], s["m_norm"], s) + s["net_int"] * (1 - s["tax"])


# 2026H1 实际经营 NOPAT（不含利息与理财）：2026H1_report 第 41–42 页合并利润表
H1_REV, H1_COGS, H1_TAXADD, H1_SALES, H1_ADMIN, H1_RD = 21.480, 4.532, 0.272, 9.855, 0.774, 0.527
H1_OTHER = -0.118 - 0.003 + 0.077 + 0.002 - 0.017   # 信用减值、资产减值、其他收益、营业外收支


def reinv_rate(s):
    """显性期再投资率 = 显性期平均营收增速 / 增量回报（负增长取 0，维持性资本开支≈折旧已含在 NOPAT）。"""
    return max(sum(s["g"]) / len(s["g"]), 0.0) / s["ronic"]


def nopat26_expected(s):
    """2026 年预期经营 NOPAT = H1 实际 + H2 情景估计，作增长路径的基年。"""
    h1_pre = H1_REV - H1_COGS - H1_TAXADD - H1_SALES - H1_ADMIN - H1_RD + H1_OTHER
    h1 = h1_pre * (1 - s["tax"]) * (1 - s["minority"])
    return h1 + nopat(s["h2_rev"], s["h2_m"], s)


def path(s):
    rows, rev, prev = [], s["rev26"], nopat26_expected(s)
    k = reinv_rate(s)
    for y, g, m in zip(YEARS, s["g"], s["m_path"]):
        rev *= 1 + g
        n = nopat(rev, m, s)
        rows.append(dict(year=y, rev=rev, m=m, nopat=n, growth=n / prev - 1, reinv=k, oe=n * (1 - k)))
        prev = n
    return rows


def value(s, r=COE, nc=None, nonop=None):
    nc = net_cash_adj() if nc is None else nc
    nonop = nonop_value() if nonop is None else nonop
    h2 = nopat(s["h2_rev"], s["h2_m"], s)
    rows = path(s)
    pv = sum(row["oe"] / (1 + r) ** (i + 0.5) for i, row in enumerate(rows))
    gT = s["gT"]
    oeT = rows[-1]["nopat"] * (1 + gT) * (1 - gT / s["ronic"])
    tv = oeT / (r - gT) * (1 + r) ** 0.5 / (1 + r) ** len(rows)
    ops = (h2 + pv + tv) / (1 + r) ** 0.2
    eq = nc + nonop + ops
    return dict(v=eq / SHARES, eq=eq, ops=ops, tv_share=tv / (h2 + pv + tv), h2=h2, rows=rows)


def weighted(r=COE, scen=None, probs=None, **kw):
    scen = scen or SCEN
    probs = probs or {k: s["p"] for k, s in scen.items()}
    return sum(probs[k] * value(s, r, **kw)["v"] for k, s in scen.items())


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


def implied_irr():
    """基准情景所有者收益流（含终值、净现金）使现值等于现价的折现率。"""
    return solve(lambda r: value(SCEN["base"], r)["v"], 0.03, 0.30, PRICE)


def reverse_perpetual():
    """以基准正常化 2026 NOPAT 为起点，现价隐含的永续增速（增量回报 40%）。"""
    s = SCEN["base"]
    n0 = nopat(s["rev26"], s["m_norm"], s)
    nc, no = net_cash_adj(), nonop_value()
    h2 = nopat(s["h2_rev"], s["h2_m"], s)

    def v(g):
        oe1 = n0 * (1 + g) * (1 - max(g, 0) / s["ronic"])
        return (nc + no + (h2 + oe1 / (COE - g) * (1 + COE) ** 0.5) / (1 + COE) ** 0.2) / SHARES
    return solve(v, -0.05, 0.08, PRICE)


def reverse_10y(gT=0.02):
    """以基准正常化 2026 NOPAT 为起点，2027–2036 年恒定增速 g、此后 2% 永续，现价隐含的 g。"""
    s = SCEN["base"]
    n0 = nopat(s["rev26"], s["m_norm"], s)
    nc, no = net_cash_adj(), nonop_value()
    h2 = nopat(s["h2_rev"], s["h2_m"], s)

    def v(g):
        n, pv = n0, 0.0
        for i in range(10):
            n *= 1 + g
            pv += n * (1 - max(g, 0) / s["ronic"]) / (1 + COE) ** (i + 0.5)
        tv = n * (1 + gT) * (1 - gT / s["ronic"]) / (COE - gT) * (1 + COE) ** 0.5 / (1 + COE) ** 10
        return (nc + no + (h2 + pv + tv) / (1 + COE) ** 0.2) / SHARES
    return solve(v, -0.08, 0.15, PRICE)


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def falsifiers():
    """各证伪条件触发后的独立 V（9%）。"""
    out = {}
    # F1 三季报/全年转弱：三情景概率改为 熊 0.45／基准 0.45／牛 0.10
    out["F1_业绩转弱"] = weighted(probs={"bear": 0.45, "base": 0.45, "bull": 0.10})
    # F2 毛利率连续两季 < 76%：三情景正常化利润率各降 1.5 个百分点（路径同步下移）
    sc = {}
    for k, s in SCEN.items():
        t = dict(s)
        t["m_path"] = [m - 0.015 for m in s["m_path"]]
        t["m_norm"] = s["m_norm"] - 0.015
        sc[k] = t
    out["F2_毛利率回落"] = weighted(scen=sc)
    # F3 通络祛痛膏独家性被打破或进入集采降价 ≥ 30%：熊 0.60／基准 0.40／牛 0
    out["F3_独家性丧失"] = weighted(probs={"bear": 0.60, "base": 0.40, "bull": 0.0})
    # F4 2026 年度分红率 < 60% 或 > 10 亿、> 20 倍 PE 的并购：经调整净现金按七折计
    out["F4_资本配置"] = weighted(nc=net_cash_adj() * 0.7)
    # F5 母公司高新技术企业复审未通过：合并有效税率 +8.5 个百分点
    sc = {}
    for k, s in SCEN.items():
        t = dict(s)
        t["tax"] = s["tax"] + 0.085
        sc[k] = t
    out["F5_高新复审失败"] = weighted(scen=sc)
    return out


def main():
    nc, no = net_cash_adj(), nonop_value()
    print("== 经调整净现金（2026-06-30）")
    print(f"  现金类合计 {sum(CASH_LIKE.values()):.2f}  有息及类债务 {sum(DEBT_LIKE.values()):.2f}  "
          f"经营备付 {OP_RESERVE:.2f}  季节性浮存 {FLOAT_EXCESS:.2f}  → 经调整净现金 {nc:.2f}")
    print(f"  非经营资产（折扣后，扣基金未实缴折损）{no:.2f}；合计 {nc + no:.2f}（{(nc + no) / SHARES:.2f} 元/股）")
    print("  经调整净现金为正：无杠杆口径全额扣除有息负债，框架的有杠杆口径不适用")
    print("== 情景（股权成本 9%）")
    res = {}
    for k, s in SCEN.items():
        v = value(s)
        res[k] = v
        print(f"  {k}: p={s['p']:.2f}  V={v['v']:.2f}  经营价值 {v['ops']:.1f}  终值占经营价值 {v['tv_share']:.0%}  "
              f"2026H2 经营 NOPAT {v['h2']:.2f}  正常化 2026 归母 {norm_np_2026(s):.2f}")
        print(f"     2026E 经营 NOPAT {nopat26_expected(s):.2f}（H1 实际 + H2 估计），显性期再投资率 {reinv_rate(s):.1%}")
        for row in v["rows"]:
            print(f"     {row['year']} 营收 {row['rev']:.2f}  核心利润率 {row['m']:.1%}  NOPAT {row['nopat']:.2f}  "
                  f"OE 增速 {row['growth']:+.1%}  OE {row['oe']:.2f}")
        print(f"     终值增长 {s['gT']:.1%}  终值再投资率 {s['gT'] / s['ronic']:.1%}  增量回报 {s['ronic']:.0%}")
    vw = weighted()
    pv = PRICE / vw
    print(f"== 加权 V = {vw:.2f}  P/V = {pv:.3f}  分档：{verdict(pv)}")
    for r in (0.08, 0.10):
        print(f"  r={r:.0%}: " + "  ".join(f"{k} {value(s, r)['v']:.2f}" for k, s in SCEN.items())
              + f"  加权 {weighted(r):.2f}  P/V {PRICE / weighted(r):.3f}")
    print(f"== 隐含回报（基准情景）{implied_irr():.2%}")
    print(f"== 反向 DCF：永续增速 {reverse_perpetual():.2%}；10 年增速（其后 2%）{reverse_10y():.2%}")
    print("== 进入各档的价格（V 不变）：明显低估 ≤ {:.2f}；温和低估 ≤ {:.2f}；大致合理 ≤ {:.2f}；偏贵 > {:.2f}".format(
        0.75 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    # 交叉验证
    mcap = PRICE * SHARES
    ev = mcap - nc - no
    ttm_np, ttm_core_ebit, dps = 7.80, 8.56, 1.10
    base = SCEN["base"]
    print("== 交叉验证")
    print(f"  市值 {mcap:.1f}  EV {ev:.1f}  PE(TTM) {mcap / ttm_np:.1f}  剔除现金 PE {ev / (ttm_np - 0.45 * 0.865):.1f}  "
          f"EV/核心EBIT(TTM) {ev / ttm_core_ebit:.1f}  EV/正常化核心EBIT {ev / (base['rev26'] * base['m_norm']):.1f}  股息率 {dps / PRICE:.2%}")
    print("== 证伪条件触发后的 V（9%）")
    for k, v in falsifiers().items():
        print(f"  {k}: {v:.2f}")
    print(f"  正面方向（三季报营收转正且毛利率 ≥ 79%，概率 15/50/35）: "
          f"{weighted(probs={'bear': 0.15, 'base': 0.50, 'bull': 0.35}):.2f}")
    b = value(SCEN["base"])
    print(f"== 基准每股拆分：净现金+非经营 {(nc + no) / SHARES:.2f}  经营价值 {b['ops']:.1f} 亿（{b['ops'] / SHARES:.2f} 元）")
    print("== 敏感性（基准，9%）：核心利润率 ±1pp、终值增长 1.5%/2.5%")
    for dm in (-0.01, 0.01):
        t = dict(SCEN["base"])
        t["m_path"] = [m + dm for m in SCEN["base"]["m_path"]]
        print(f"  利润率 {dm:+.0%}: V {value(t)['v']:.2f}")
    for g in (0.015, 0.025):
        t = dict(SCEN["base"])
        t["gT"] = g
        print(f"  终值增长 {g:.1%}: V {value(t)['v']:.2f}")
    print(f"== 2026E 报告口径归母（基准）≈ H1 4.95 + H2 经营 NOPAT + H2 税后净利息 0.19 = "
          f"{4.951 + nopat(SCEN['base']['h2_rev'], SCEN['base']['h2_m'], SCEN['base']) + 0.22 * (1 - SCEN['base']['tax']):.2f}")
    print("== 正常化 2026 归母净利（含净利息）：" + "  ".join(f"{k} {norm_np_2026(s):.2f}" for k, s in SCEN.items()))


if __name__ == "__main__":
    main()
