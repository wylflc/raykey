"""小商品城（600415）OI-291 独立估值脚本。

运行：python3 valuation.py
单位：亿元（每股为元）。价格日 2026-10-21，现价 10.94 元（含 2026 中期 0.10 元股息，登记日 10-21、除息 10-22）。
口径：所有者收益只取经常性核心盈利（剔除全球数贸中心选位/入驻一次性确认、配套房产销售、公允价值变动、联营投资收益），
联营与金融资产单列为非经营资产；数贸中心一次性预收款的回转（税）与季节性营运资金单列为一次性调整。
经调整净现金为负，按 framework 有杠杆口径：净负债按现规模滚动，扣其税后利息现值；同时打印无杠杆口径对照。
"""

PRICE = 10.94
SHARES = 54.8356            # 亿股，含全部 A 股；无库存股、无拟注销回购
COE = 0.09
TAX = 0.25

# ---------------- 资产负债（2026-09-30，三季报第 5-6 页；H1 附注） ----------------
CASH = 34.28                 # 货币资金（含定期存单、受限 0.35）
WMP = 4.00                   # 交易性金融资产中的银行理财/结构性存款（母公司 4.00）
MUXI = 6.85 - WMP            # 交易性金融资产其余部分：沐曦股份限售股（H1 4.75，Q3 公允价值 -1.89）
RESTRICTED = 0.35            # 受限货币资金（H1 附注 31）
OP_RESERVE = 5.0             # 经营备付（约 2-3 周现金成本）
DEBT = 27.99 + 2.84 + 0.59   # 应付债券 + 长期借款 + 一年内到期（不含租赁）
LEASE = 1.45                 # 租赁负债（含一年内到期）：净利润已扣使用权折旧与利息，只列示不扣
DIV_PAY_CTRL = 10.4          # 2025 年末股利中控股股东等自行发放部分 15.47，Q3 估计已付 ~5.06，余额估计
RD = 0.0205                  # 有息负债实际平均利率（债券票息 1.89%-2.10%，长借 2.1%-2.4%）

NET_CASH_ADJ = CASH + WMP - RESTRICTED - OP_RESERVE - DEBT - DIV_PAY_CTRL

# ---------------- 非经营资产（账面 -> 折价） ----------------
# (名称, 账面, 熊折价, 基准折价, 牛折价)
LTEI = [
    ("商城房产（49%，控股股东控制，2025 亏 2.69 亿）", 30.05, 0.70, 0.50, 0.35),
    ("弘义股权投资基金（49.98%）", 9.07, 0.30, 0.20, 0.10),
    ("稠州金融租赁（26%，2025 净利 4.50 亿）", 6.92, 0.20, 0.00, 0.00),
    ("义乌商旅（49% 合营）", 5.20, 0.25, 0.10, 0.00),
    ("浦江绿谷置业（49%）", 4.18, 0.50, 0.30, 0.20),
    ("智捷元港（23.23%）", 1.49, 0.40, 0.20, 0.00),
    ("惠商紫荆二期", 1.33, 0.30, 0.20, 0.10),
    ("国深商博置业（49%）", 1.08, 0.20, 0.10, 0.00),
    ("阜兴母基金（司法冻结）", 1.03, 1.00, 1.00, 0.70),
    ("惠商小贷", 0.81, 0.50, 0.30, 0.20),
    ("融商置业", 0.66, 0.50, 0.30, 0.20),
    ("其他联营合营（H1）", 2.28, 0.50, 0.30, 0.20),
    ("三季度新增（66.86-64.10）", 2.76, 0.20, 0.10, 0.00),
]
OTHER_FIN = [
    ("商阜创智基金（湖北资管股权被上海二中院冻结）", 6.64, 0.80, 0.60, 0.40),
    ("其他私募基金", 6.67, 0.30, 0.20, 0.10),
    ("非上市股权", 1.95, 0.50, 0.30, 0.20),
    ("天图投资（新三板）", 0.37, 0.20, 0.00, 0.00),
    ("申万宏源 A 股（其他权益工具，市值）", 5.49, 0.00, 0.00, 0.00),
    ("沐曦股份限售股（交易性，市值）", MUXI, 0.25, 0.10, 0.00),
    ("委托贷款（一年内到期非流动资产）", 0.48, 0.20, 0.00, 0.00),
]
PROPERTY_BLOCK = {"bear": 2.0, "base": 5.0, "bull": 7.0}   # T1/T2 及杭州飞地待售部分的剩余税后利润（扣预收房款与续建成本）

# ---------------- 文商旅综合体（五区南 78.63 + 地块一 17.60 = 96.23） ----------------
PROJ_TOTAL = 96.23
PROJ_CAPEX = {2026: 3.0, 2027: 15.0, 2028: 18.0, 2029: 15.0, 2030: 5.0}   # 剩余约 56（土地 37.5 已付）
PROJ_END = 2065              # 土地 40 年

# ---------------- 情景 ----------------
SCEN = {
    "bear": dict(p=0.25, E0=24.0, g1=0.01, roic=0.15, gT=0.015, roicT=0.12, uplift=0.0,
                 proj_r=0.035, proj_capex_mult=1.15, float_adj=-22.5, extra_npv=-10.0),
    "base": dict(p=0.50, E0=26.5, g1=0.04, roic=0.25, gT=0.025, roicT=0.20, uplift=1.5,
                 proj_r=0.050, proj_capex_mult=1.00, float_adj=-5.0, extra_npv=0.0),
    "bull": dict(p=0.25, E0=29.5, g1=0.07, roic=0.40, gT=0.025, roicT=0.30, uplift=4.0,
                 proj_r=0.060, proj_capex_mult=1.00, float_adj=7.5, extra_npv=0.0),
}
JV_NORMAL = 1.5              # 正常化联营投资收益（9M-26 1.82，Q4-25 -0.71）
Q4_SHARE = 0.22              # 四季度占全年经常性利润比例（2024 年 23.5%）
T_STUB = 0.10                # 2026Q4 现金流折现年限（10-21 起算的季度中点）
T_FIRST = 0.69               # 2027 年中点距 10-21 的年数


def nonop(case):
    k = {"bear": 2, "base": 3, "bull": 4}[case]
    s = sum(r[1] * (1 - r[k]) for r in LTEI) + sum(r[1] * (1 - r[k]) for r in OTHER_FIN)
    return s + PROPERTY_BLOCK[case]


def path(sc):
    """返回 [(年, g, E, 再投资, OE)]，2027-2036。"""
    rows, E = [], sc["E0"]
    for y in range(2027, 2037):
        if y <= 2031:
            g, roic = sc["g1"], sc["roic"]
        else:
            w = (y - 2031) / 5
            g = sc["g1"] + (sc["gT"] - sc["g1"]) * w
            roic = sc["roic"] + (sc["roicT"] - sc["roic"]) * w
        E = E * (1 + g) + (sc["uplift"] if y == 2029 else 0.0)
        re = g / roic * E
        rows.append((y, g, E, re, E - re))
    return rows


def df(t, r):
    return (1 + r) ** -t


def project_pv(sc, r):
    pv = 0.0
    for y, c in PROJ_CAPEX.items():
        t = T_STUB if y == 2026 else T_FIRST + (y - 2027)
        pv -= c * sc["proj_capex_mult"] * df(t, r)
    inc = sc["proj_r"] * PROJ_TOTAL
    for y in range(2030, PROJ_END + 1):
        lvl = 0.5 if y == 2030 else 1.0
        cf = inc * lvl * 1.02 ** max(0, y - 2031)
        pv += cf * df(T_FIRST + (y - 2027), r)
    return pv


def value(case, r=COE, levered=True, detail=False):
    sc = SCEN[case]
    rows = path(sc)
    stub = sc["E0"] * Q4_SHARE * (1 - sc["g1"] / sc["roic"])
    pv_oe = stub * df(T_STUB, r) + sum(oe * df(T_FIRST + (y - 2027), r) for y, g, E, re, oe in rows)
    E36 = rows[-1][2]
    oe37 = E36 * (1 + sc["gT"]) * (1 - sc["gT"] / sc["roicT"])
    pv_tv = oe37 / (r - sc["gT"]) * df(T_FIRST + 9, r)
    pv_proj = project_pv(sc, r)
    na = nonop(case)
    fl = sc["float_adj"] * df(T_FIRST, r)
    if NET_CASH_ADJ < 0 and levered:
        nd = -NET_CASH_ADJ * RD * (1 - TAX) / r       # 净负债滚动，扣税后利息现值
    else:
        nd = -NET_CASH_ADJ                             # 无杠杆：全额扣除（为正即加回）
    eq = pv_oe + pv_tv + pv_proj + na + fl + sc["extra_npv"] - nd
    if detail:
        return dict(pv_oe=pv_oe, pv_tv=pv_tv, pv_proj=pv_proj, nonop=na, float_adj=fl,
                    extra=sc["extra_npv"], net_debt_charge=nd, equity=eq, v=eq / SHARES,
                    tv_share=pv_tv / (pv_oe + pv_tv), rows=rows, stub=stub)
    return eq / SHARES


def weighted(r=COE, levered=True):
    return sum(SCEN[c]["p"] * value(c, r, levered) for c in SCEN)


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
    return solve(lambda r: value("base", r), 0.04, 0.20, PRICE)


def reverse_dcf_g10():
    """基准起点 E0、ROIC 25%/20%，求 2027-2036 恒定增速 g（终值 2.5%）使 9% 下 V = 现价。"""
    def f(g):
        saved = dict(SCEN["base"])
        SCEN["base"].update(g1=g, uplift=0.0)
        # 让 2032-36 也保持 g：把 gT 暂设为 g 再在终值处用 2.5%
        rows, E = [], SCEN["base"]["E0"]
        for y in range(2027, 2037):
            E = E * (1 + g)
            rows.append((y, E, E * (1 - g / 0.25)))
        stub = SCEN["base"]["E0"] * Q4_SHARE * (1 - g / 0.25)
        pv = stub * df(T_STUB, COE) + sum(oe * df(T_FIRST + (y - 2027), COE) for y, E, oe in rows)
        oe37 = rows[-1][1] * 1.025 * (1 - 0.025 / 0.20)
        pv += oe37 / (COE - 0.025) * df(T_FIRST + 9, COE)
        sc = SCEN["base"]
        pv += project_pv(sc, COE) + nonop("base") + sc["float_adj"] * df(T_FIRST, COE)
        pv -= -NET_CASH_ADJ * RD * (1 - TAX) / COE
        SCEN["base"].clear(); SCEN["base"].update(saved)
        return pv / SHARES
    return solve(f, -0.05, 0.25, PRICE)


def h_share(v_pre, issue_px, frac=0.10, fee=0.03):
    n = SHARES / (1 - frac) * frac
    proceeds = n * issue_px * (1 - fee)
    return (v_pre * SHARES + proceeds) / (SHARES + n), n


def variant(case, **kw):
    saved = dict(SCEN[case]); SCEN[case].update(kw)
    v = value(case)
    SCEN[case].clear(); SCEN[case].update(saved)
    return v


def weighted_with_base(v_base_variant):
    return SCEN["bear"]["p"] * value("bear") + SCEN["base"]["p"] * v_base_variant + SCEN["bull"]["p"] * value("bull")


def band(pv):
    if pv <= 0.75: return "明显低估"
    if pv <= 0.90: return "温和低估"
    if pv <= 1.10: return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print("== 输入核对 ==")
    print(f"经调整净现金（无杠杆口径）= {CASH}+{WMP}-{RESTRICTED}-{OP_RESERVE}-{DEBT:.2f}-{DIV_PAY_CTRL} = {NET_CASH_ADJ:.2f} 亿；租赁负债 {LEASE} 只列示")
    for c in ("bear", "base", "bull"):
        print(f"非经营资产[{c}] = {nonop(c):.2f} 亿（长投账面 66.86、其他非流金融 15.62、其他权益 5.49、沐曦 {MUXI:.2f}、委贷 0.48、房产块 {PROPERTY_BLOCK[c]}）")
    print("TTM 扣非 39.29 = Q4-25 5.01 + 9.45 + 8.78 + 16.05；减配套房产税后约 6.3、联营 1.11、数贸中心入驻/选位一次性约 4.5-8 → 经常性约 24-27.5")

    print("\n== 三情景 ==")
    res = {}
    for c in ("bear", "base", "bull"):
        d = value(c, detail=True); res[c] = d
        sc = SCEN[c]
        print(f"[{c}] p={sc['p']:.2f} E0={sc['E0']} g1={sc['g1']:.1%} ROIC={sc['roic']:.0%} gT={sc['gT']:.1%} 续约提价={sc['uplift']} 项目收益率={sc['proj_r']:.1%}")
        print(f"   PV(经营OE)={d['pv_oe']:.1f} PV(终值)={d['pv_tv']:.1f}（终值占比 {d['tv_share']:.0%}） 文商旅项目NPV={d['pv_proj']:.1f} 非经营={d['nonop']:.1f} 预收回转/营运={d['float_adj']:.1f} 其他={d['extra']:.1f} 净负债利息现值=-{d['net_debt_charge']:.2f}")
        print(f"   股权={d['equity']:.1f} 亿 → V={d['v']:.2f} 元；无杠杆口径 V={value(c, levered=False):.2f} 元")
        print("   年  增速   E(经常性)  再投资   OE")
        print(f"   2026Q4 存根 OE={d['stub']:.2f}")
        for y, g, E, re, oe in d['rows']:
            print(f"   {y} {g:6.2%} {E:9.2f} {re:7.2f} {oe:7.2f}")
    vw = weighted(); vw_u = weighted(levered=False)
    print(f"\n加权 V（有杠杆）= {vw:.2f} 元；P/V = {PRICE / vw:.2f} → {band(PRICE / vw)}")
    print(f"加权 V（无杠杆对照）= {vw_u:.2f} 元；P/V = {PRICE / vw_u:.2f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8% → 加权 V {v8:.2f}；10% → {v10:.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准情景现金流）= {irr:.2%}")
    g10 = reverse_dcf_g10()
    print(f"反向 DCF：现价隐含 2027-2036 经常性盈利年增速 {g10:.2%}（终值 2.5%，ROIC 25%/20%，含净现金与非经营资产）")
    print(f"V 不变时进入各档的价格：明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}；高于 {1.10 * vw:.2f} 为偏贵")

    print("\n== H 股摊薄（未完成，另列） ==")
    for px in (8.2, 7.0, 9.5):
        vpost, n = h_share(vw, px)
        print(f"发行后总股本 10%（新增 {n:.3f} 亿股）、发行价折人民币 {px} 元 → 加权 V {vw:.2f} → {vpost:.2f}")

    print("\n== 证伪触发后的 V（单项改动，其余取基准；加权时按 25/50/25 替换对应情景） ==")
    up = variant("base", E0=29.5, float_adj=7.5)
    print(f"F1 2026 年 OCF ≥ 35 亿且年末合同负债+其他非流动负债 ≥ 105 亿（预收不回转）：基准 V → {up:.2f}，加权 V → {weighted_with_base(up):.2f}")
    dn = variant("base", g1=0.01, E0=25.0, uplift=0.0)
    print(f"F2 2027H1 市场经营分部对外收入 < 26.5 亿（较 25.79 增长 < 3%）：基准 V → {dn:.2f}，加权 V → {weighted_with_base(dn):.2f}")
    pj = variant("base", proj_r=0.035, proj_capex_mult=1.15)
    print(f"F3 文商旅总投资上调 > 10% 或新增拿地 > 20 亿：基准 V → {pj:.2f}，加权 V → {weighted_with_base(pj):.2f}")
    e2 = variant("base", E0=24.0)
    print(f"F4 2026 年报商位使用及经营配套服务收入 < 48 亿或扣非 < 37 亿：基准 V → {e2:.2f}，加权 V → {weighted_with_base(e2):.2f}")
    vpost7, _ = h_share(vw, 7.0)
    print(f"F5 H 股以 < 7 元人民币足额发行 10%：加权 V → {vpost7:.2f}")

    print("\n== 正常化归母净利 2026（含联营 1.5 与净利息，剔除一次性） ==")
    for c in ("bear", "base", "bull"):
        print(f"{c}: {SCEN[c]['E0'] + JV_NORMAL:.1f} 亿")
    print("报告口径 2026E 约 41.6 亿 = 9M 34.61 + Q4E 约 7.0（含配套房产、数贸中心一次性确认）")

    print("\n== 交叉验证 ==")
    mcap = PRICE * SHARES
    print(f"市值 {mcap:.1f} 亿；经常性 PE（含联营）= {mcap / (SCEN['base']['E0'] + JV_NORMAL):.1f}×；报告 TTM PE = {mcap / 42.07:.1f}×；PB = {mcap / 230.15:.2f}×")
    ev = mcap - NET_CASH_ADJ - nonop('base')
    print(f"EV（市值+净负债-非经营资产）= {ev:.1f} 亿；经常性 EBIT 约 {SCEN['base']['E0'] / (1 - TAX):.1f} → EV/EBIT {ev / (SCEN['base']['E0'] / (1 - TAX)):.1f}×")
    print(f"过去 12 个月股息 0.50 元 → 股息率 {0.50 / PRICE:.2%}；按经常性盈利 65% 派息的可持续股息率约 {(SCEN['base']['E0'] + JV_NORMAL) * 0.65 / mcap:.2%}")
