"""华鲁恒升（600426）独立估值（OI-291 b04，价格日 2026-10-19）。

运行：python3 valuation.py
口径：金额亿元，每股元。最新定期报告 2026 中报（2026-06-30 资产负债表）；三季报预约 2026-10-30。
方法：合并口径无杠杆所有者收益（经营）DCF。经调整净现金为负，按框架「三法互校」第 2 条取有杠杆口径：
      股权 = 经营所有者收益现值 − 经调整净负债税后利息现值（规模不变滚动）；现金已在净负债里抵减，不另加
      （r2，2026-10-20 用户裁定；r1 曾滚动全部有息负债 110.72 亿、现金调整项 17.15 亿另加）；
      另列无杠杆口径（全额扣有息负债）作对照。合并股权按少数股东净利占比折归母。
"""

PRICE = 19.40            # 2026-10-19 收盘
SHARES = 27.49943015     # 亿股，2026-07-10 十转三后总股本；回购 784.5881 万股已于 2026-05-06 注销，无回购专户股份
R = 0.09                 # 股权成本基准
TAX = 0.155              # 有效税率（母公司与荆州恒升均为高新技术企业 15%，2024–2026H1 实际 14.2%–16.7%）
VAL_DATE_OFFSET = 0.30   # 2026-10-19 → 2027-01-01 约 0.20 年；年中法下 2027 年现金流距估值日 0.70 年

# ---------- 资产负债表调整项（2026-06-30，2026H1_report 第 25–27、78、97–102 页）----------
cash = 31.708            # 货币资金
struct_dep = 1.002       # 交易性金融资产（结构性存款）
restricted = 0.271       # 信用证保证金 + ETC 保证金
op_reserve = 10.0        # 经营备付，约营收 3%
div_payable = 5.288      # 应付股利：2025 年末期 0.25 元/股，已于 2026-07-10 付出
cash_adj = cash + struct_dep - restricted - op_reserve - div_payable
# 2026 中期股息 0.26 元/股（7.15 亿，10-22 登记、10-23 除息）归现价持有人，现价含权，不扣
debt = 5.670 + 80.171 + 24.310 + 0.060 + 0.419 + 0.088  # 短借+长借+一年内到期长借+其应付利息+租赁负债
net_cash_adj_unlev = cash_adj - debt
# r2：只滚动经调整净负债；被现金抵减的那部分有息负债按本金扣除，所以有杠杆口径的现金调整项为 0
net_debt_rolled = max(0.0, -net_cash_adj_unlev)
levered_cash_adj = cash_adj - debt + net_debt_rolled

# 实际平均利率：2026H1 费用化利息 1.488 + 资本化 0.087 = 1.575 亿，年化 3.15 ÷ 平均有息负债 ≈2.87%；
# 另加控股股东担保费（年化 0.3%，2026 年上限 0.36 亿，担保借款约 91.6 亿）折合约 0.25 个百分点
RATE = 0.0287 + 0.0025
interest_after_tax = net_debt_rolled * RATE * (1 - TAX)

# ---------- 正常化（2026 年产能，长期价差）----------
# AGP = 毛利 − 研发费用（研发材料费与生产成本存在归类迁移，合并看更可比）
# 实际：2023 51.1｜2024 57.4｜2025 50.5｜TTM 60.1｜2026H1 年化 69.0
BRIDGE = -6.2   # 税金及附加 −2.4、销售 −0.95、管理 −3.2、其他收益 +0.8、票据贴现等投资收益 −0.2、减值 −0.35、营业外 +0.1
NET_INTEREST = debt * RATE - 0.13   # 含担保费，扣利息收入
DA = 37.0       # 2027 年折旧摊销（2026H1 年化 35.2，加气化平台 30.4 亿转固）

SCEN = {
    #        概率   AGP   维持资本开支 少数股东占比 再投资率 增量回报 终值增长
    "bear": dict(p=0.25, agp=50.0, maint=30.0, m=0.093, b=0.25, roic=0.060, gT=0.010,
                 note="2025 年谷底价差延续：新能源新材料 ~555 元/吨毛利、化肥 ~410、醋酸 ~640、有机胺 ~570；"
                      "山西优混 5500 大卡长期 ~950、尿素 ~1750；增量回报 6%"),
    "base": dict(p=0.50, agp=60.0, maint=28.0, m=0.085, b=0.25, roic=0.085, gT=0.020,
                 note="中枢价差：新能源新材料 ~770 元/吨、化肥 ~440、醋酸 ~720、有机胺 ~650，研发 3% 营收；"
                      "山西优混 ~850、尿素 ~1900；增量回报 8.5%"),
    "bull": dict(p=0.25, agp=72.0, maint=26.0, m=0.075, b=0.30, roic=0.110, gT=0.025,
                 note="2026H1 油煤价差与反内卷延续：新能源新材料 ~1000 元/吨、化肥 ~480、醋酸 ~900；"
                      "山西优混 ~780、尿素 ~2050；增量回报 11%"),
}

# 2026 下半年（三季报未披露，估计值，三情景共用）：归母 Q3 9.5、Q4 9.0
H2_PARENT_NP = 18.5
H2_M = 0.085
H2_INTEREST = NET_INTEREST / 2
H2_DA, H2_MAINT, H2_GROWTH_CAPEX = 18.5, 14.0, 2.0   # 维持性开支取基准年 28 的一半


def normalized(s):
    ebit = s["agp"] + BRIDGE
    np_total = (ebit - NET_INTEREST) * (1 - TAX)
    np_parent = np_total * (1 - s["m"])
    oe_gross = ebit * (1 - TAX) + (DA - s["maint"])     # 无杠杆所有者收益（再投资前）
    return ebit, np_total, np_parent, oe_gross


def h2_2026_oe():
    np_total = H2_PARENT_NP / (1 - H2_M)
    ebit = np_total / (1 - TAX) + H2_INTEREST
    return ebit * (1 - TAX) + H2_DA - H2_MAINT - H2_GROWTH_CAPEX


def value(s, r=R, levered=True, detail=False):
    ebit, np_total, np_parent, oe0 = normalized(s)
    g = s["b"] * s["roic"]                  # 前 5 年增长 = 再投资率 × 增量回报
    pv, rows = h2_2026_oe(), []
    oe = oe0
    for i, y in enumerate(range(2027, 2032)):
        oe *= 1 + g
        cf = oe * (1 - s["b"])
        t = (y - 2026) - VAL_DATE_OFFSET
        pv += cf / (1 + r) ** t
        rows.append((y, g, oe, cf, t))
    # 终值：2032 起永续；折旧回落到维持性资本开支，税盾差额消失
    oe_2032 = oe * (1 + s["gT"]) - TAX * (DA - s["maint"]) * (1 + g) ** 6
    cf_2032 = oe_2032 * (1 - s["gT"] / s["roic"])
    tv = cf_2032 / (r - s["gT"])
    pv_tv = tv / (1 + r) ** (2031 - 2026 - VAL_DATE_OFFSET)
    v_ops = pv + pv_tv
    if levered:
        pv_int = interest_after_tax / 2 + interest_after_tax / (1 + r) ** (1 - VAL_DATE_OFFSET) * (1 + r) / r
        eq = v_ops - pv_int + levered_cash_adj
    else:
        pv_int = debt
        eq = v_ops - debt + cash_adj
    v_parent = eq * (1 - s["m"])
    out = v_parent / SHARES
    if detail:
        return dict(ebit=ebit, np_total=np_total, np_parent=np_parent, oe0=oe0, g=g, rows=rows,
                    cf_2032=cf_2032, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / v_ops, v_ops=v_ops,
                    deduct=pv_int, eq=eq, v_parent=v_parent, v=out)
    return out


def weighted(r=R, levered=True, scen=SCEN, probs=None):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * value(scen[k], r, levered) for k in scen)


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print(f"经调整现金项 {cash_adj:.2f}；有息负债 {debt:.2f}；无杠杆经调整净现金 {net_cash_adj_unlev:.2f} 亿")
    print(f"有杠杆（r2）滚动经调整净负债 {net_debt_rolled:.2f} 亿；有息负债实际利率（含担保费）{RATE:.2%}；税后利息 {interest_after_tax:.2f} 亿/年；"
          f"2026H2 无杠杆所有者收益估计 {h2_2026_oe():.2f} 亿")
    print()
    print("情景   概率  AGP   EBIT   合并净利 归母净利 OE(再投资前) g前5年  终值g  终值占比  V有杠杆  V无杠杆")
    for k, s in SCEN.items():
        d = value(s, detail=True)
        vu = value(s, levered=False)
        print(f"{k:5s} {s['p']:.2f} {s['agp']:5.1f} {d['ebit']:6.2f} {d['np_total']:7.2f} {d['np_parent']:7.2f}"
              f" {d['oe0']:9.2f}   {d['g']:.3%} {s['gT']:.2%}  {d['tv_share']:.1%}   {d['v']:6.2f}  {vu:6.2f}")
    vw = weighted()
    vw_u = weighted(levered=False)
    print()
    print(f"加权 V（有杠杆）{vw:.2f} 元；P/V {PRICE / vw:.3f}（{band(PRICE / vw)}）")
    print(f"加权 V（无杠杆）{vw_u:.2f} 元；P/V {PRICE / vw_u:.3f}（{band(PRICE / vw_u)}）")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8% 加权 V {v8:.2f}；10% 加权 V {v10:.2f}（有杠杆；利息现值同率折现）")
    print(f"股权成本 8%/10% 基准 V {value(SCEN['base'], 0.08):.2f} / {value(SCEN['base'], 0.10):.2f}")
    irr = solve(lambda r: value(SCEN["base"], r), 0.04, 0.20, PRICE)
    irr_u = solve(lambda r: value(SCEN["base"], r, levered=False), 0.04, 0.20, PRICE)
    print(f"现价隐含回报（基准情景，有杠杆）{irr:.2%}；无杠杆口径 {irr_u:.2%}")

    # 反向 DCF ①：基准 2026 正常化 OE 全部可分配，现价隐含永续增速
    base = SCEN["base"]
    _, _, _, oe0 = normalized(base)
    pv_int = interest_after_tax / 2 + interest_after_tax / (1 + R) ** (1 - VAL_DATE_OFFSET) * (1 + R) / R
    target_eq = PRICE * SHARES / (1 - base["m"]) - levered_cash_adj + pv_int - h2_2026_oe()
    g_imp = solve(lambda g: oe0 * (1 + g) / (1 + R) ** (1 - VAL_DATE_OFFSET) * (1 + R) / (R - g), -0.10, 0.085, target_eq)
    print(f"反向 DCF①：基准 OE {oe0:.1f} 亿全部可分配，现价隐含永续增速 {g_imp:.2%}")
    # 反向 DCF ②：保持基准增长与回报假设，现价对应的正常化 AGP 与归母净利
    def v_for_agp(a):
        s = dict(base, agp=a)
        return value(s)
    agp_imp = solve(v_for_agp, 30.0, 90.0, PRICE)
    np_imp = normalized(dict(base, agp=agp_imp))[2]
    print(f"反向 DCF②：现价对应正常化 AGP {agp_imp:.1f} 亿、归母净利 {np_imp:.1f} 亿（基准 {normalized(base)[2]:.1f}）")
    # 反向 DCF ③：10 年所有者收益增速（2027–2036 可分配 OE 增速 g10，之后 2%）
    def v_g10(g10):
        pv = h2_2026_oe()
        cf = oe0 * (1 - base["b"])
        for i in range(10):
            cf *= 1 + g10
            pv += cf / (1 + R) ** (i + 1 - VAL_DATE_OFFSET)
        tv = cf * (1 + 0.02) / (R - 0.02) / (1 + R) ** (10 - VAL_DATE_OFFSET)
        return ((pv + tv - pv_int + levered_cash_adj) * (1 - base["m"])) / SHARES
    g10 = solve(v_g10, -0.10, 0.20, PRICE)
    print(f"反向 DCF③：以基准可分配 OE {oe0 * (1 - base['b']):.1f} 亿起步、之后 2% 永续，现价隐含 10 年增速 {g10:.2%}")

    print()
    print("逐年路径（年份、增速、所有者收益再投资前、可分配、折现年数；合并口径亿元）：")
    for k, s in SCEN.items():
        d = value(s, detail=True)
        print(f"  [{k}] 2026 正常化 OE {d['oe0']:.2f}；终值首年（2032）可分配 {d['cf_2032']:.2f}，"
              f"显式期现值 {d['pv_explicit']:.1f}（含 2026H2），终值现值 {d['pv_tv']:.1f}，扣减项 {d['deduct']:.1f}")
        for y, g, oe, cf, t in d["rows"]:
            print(f"    {y} {g:.3%} {oe:7.2f} {cf:7.2f} {t:.2f}")

    # ---------- 证伪触发后的 V ----------
    print()
    tilt = {"bear": 0.50, "base": 0.40, "bull": 0.10}
    print(f"F1 2026Q4–2027Q3 四季合计 AGP < 50 亿或归母净利 < 31 亿 → 权重 50/40/10：加权 V {weighted(probs=tilt):.2f}")
    print(f"F2 山西优混 5500 季均连续四季 > 950 且尿素季均 < 1850 → 权重 50/40/10：加权 V {weighted(probs=tilt):.2f}")
    # 价差较基准 965 低约 315 元/吨；公司实际弹性约为市场价差的 0.6 倍、柔性联产切换有缓冲，取 AGP −6 亿
    s3 = {k: dict(v, agp=v["agp"] - 6.0) for k, v in SCEN.items()}
    print(f"F3 2027 年 尿素 − 1.1×山西优混 年均 < 650 元/吨 → 三情景 AGP 各 −6 亿：加权 V {weighted(scen=s3):.2f}")
    s4 = {k: dict(v, roic={"bear": 0.05, "base": 0.065, "bull": 0.10}[k]) for k, v in SCEN.items()}
    print(f"F4 新建项目 >100 亿投向低开工品种或 2026 年分红率 < 30% → 增量回报 5%/6.5%/10%：加权 V {weighted(scen=s4):.2f}")
    s5 = {k: dict(v, agp=v["agp"] + 4.0) for k, v in SCEN.items()}
    print(f"对照：三情景 AGP 各 +4 亿（油煤价差维持 2026 年高位）：加权 V {weighted(scen=s5):.2f}")
    s6 = {k: dict(v, maint=DA) for k, v in SCEN.items()}
    print(f"对照：维持性资本开支等于折旧（37 亿）：加权 V {weighted(scen=s6):.2f}，无杠杆 {weighted(scen=s6, levered=False):.2f}")
    print()
    print("V 不变时各档价格：明显低估 ≤ {:.2f}；温和低估 {:.2f}–{:.2f}；大致合理 {:.2f}–{:.2f}；偏贵 > {:.2f}".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
