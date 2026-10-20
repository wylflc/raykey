# -*- coding: utf-8 -*-
"""中国国贸（600007）独立估值：所有者收益 DCF（含国贸一、二期土地租期 2038 与三期土地 2052 到期调整）、
反向 DCF、隐含回报、资本化率 NAV 交叉验证。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。输入全部写在本脚本内，来源见同目录公司正文。
"""

PRICE = 20.86            # 2026-10-20 收盘
SHARES = 10.0728         # 亿股，腾讯行情口径；无回购专户股份
VAL_DATE = 2026.80       # 2026-10-20 折年
COE = 0.09
TAX = 0.25

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report 第 15、64、81、83、97 页）
CASH = 29.530            # 货币资金（含应收利息 0.988、受限 1.250）
TENANT_DEPOSIT = 7.010   # 应付租户押金（类债务，全额扣除）
CUSTODIAL = 1.472        # 应付物业管理项目代收款（对应受限资金 1.25，扣负债口径避免重复）
OPER_RESERVE = 2.0       # 经营备付：约 1 个月营运支出与税费
BANK_DEBT = 0.0          # 2026-06 已还清建行借款
LEASE_LIAB = 0.395       # 租赁负债（向国贸有限公司租入），按类债务扣除
DECLARED_DIV = 0.0       # 2025 年度股利已于 2026-06-26 派发
NON_OPER = 0.342         # 长期股权投资（联营企业），其投资收益不进经营现金流
NET_CASH_ADJ = CASH - TENANT_DEPOSIT - CUSTODIAL - OPER_RESERVE - BANK_DEBT - LEASE_LIAB - DECLARED_DIV

# ---------------------------------------------------------------- 2026 年基数（H1 实际 + H2 估计）
# 分业态收入：H1 实际（2026H1_report 第 13 页），H2 = 2025H2 × (1+同比估计)
H2_2025 = {"office": 6.871, "mall": 6.265, "apt": 0.960, "other": 2.143, "hotel": 2.565}
H1_2026 = {"office": 6.608, "mall": 6.388, "apt": 0.913, "other": 1.868, "hotel": 2.383}
H2_YOY = {"office": -0.055, "mall": -0.010, "apt": -0.020, "other": -0.010, "hotel": 0.0}
REV26 = {k: H1_2026[k] + H2_2025[k] * (1 + H2_YOY[k]) for k in H1_2026}

# 租赁分部 EBITDA = 租金类收入×0.874 + 其他收入×0.40 − 固定营运成本
DROP_RENT = 1 - 0.126    # 房产税从租 12% + 附加约 0.6%
DROP_OTHER = 0.40        # 停车、物业管理服务等含外包成本
LEASE_EBITDA_H1 = 9.805  # 分部利润总额 8.514 + 折旧摊销 1.551 − 利息收入 0.260（第 97 页）
LEASE_EBITDA_H2_25 = 19.499 - 10.377   # 2025 全年 − 2025H1（2025 年报第 137 页；2026H1 报告第 98 页）
H2_RENT_DELTA = sum(H2_2025[k] * H2_YOY[k] for k in ("office", "mall", "apt"))
H2_OTHER_DELTA = H2_2025["other"] * H2_YOY["other"]
H2_COST_SAVING = 0.142   # 2025H2 租赁分部付现成本 7.118 × 2%（H1 同比 −2.7%）
LEASE_EBITDA_H2 = LEASE_EBITDA_H2_25 + H2_RENT_DELTA * DROP_RENT + H2_OTHER_DELTA * DROP_OTHER + H2_COST_SAVING
LEASE_EBITDA_26 = LEASE_EBITDA_H1 + LEASE_EBITDA_H2
HOTEL_EBITDA_H1 = 0.378  # 酒店分部利润总额 −0.052 + 折旧摊销 0.430
HOTEL_EBITDA_H2 = 0.440
HOTEL_EBITDA_26 = HOTEL_EBITDA_H1 + HOTEL_EBITDA_H2
RENT26 = REV26["office"] + REV26["mall"] + REV26["apt"]
FIXED26 = RENT26 * DROP_RENT + REV26["other"] * DROP_OTHER - LEASE_EBITDA_26

DA26 = 1.980 + 1.950     # H1 实际 1.980（第 93 页）
INT_INC26 = 0.261 + 0.230
INT_EXP26 = 0.036 + 0.008
OTHER26 = 0.108 + 0.0    # 其他收益、联营收益、信用减值转回、营业外净额
PBT26 = LEASE_EBITDA_26 + HOTEL_EBITDA_26 - DA26 + INT_INC26 - INT_EXP26 + OTHER26
NP26 = PBT26 * (1 - 0.2505) - 0.008
PBT_H1 = 8.457
CAPEX_H2_26 = 0.53       # 2026 计划 0.8（2025 年报第 29 页）− H1 0.27
OE_H2_26 = (LEASE_EBITDA_H2 + HOTEL_EBITDA_H2) - CAPEX_H2_26 - TAX * (LEASE_EBITDA_H2 + HOTEL_EBITDA_H2 - 1.950)

# ---------------------------------------------------------------- 税务折旧路径（装修、电子设备 2028 年前基本摊完；一、二期建筑 2038 年摊完）
def tax_da(year, capex):
    if year <= 2026:
        return DA26
    table = {2027: 3.60, 2028: 3.30, 2029: 3.10}
    if year in table:
        return table[year]
    if year <= 2038:
        return 3.00
    if year <= 2052:
        return max(2.60, capex)
    return capex

YEARS5 = [2027, 2028, 2029, 2030, 2031]

SCEN = {
    "bear": dict(
        p=0.25,
        g={"office": [-0.12, -0.08, -0.03, 0.00, 0.01], "mall": [-0.05, -0.04, -0.01, 0.01, 0.01],
           "apt": [-0.05, -0.03, 0.00, 0.01, 0.01], "other": [-0.03, -0.02, 0.00, 0.01, 0.01],
           "fixed": [-0.02, -0.01, 0.01, 0.02, 0.02]},
        hotel=[0.60, 0.55, 0.55, 0.56, 0.57],
        capex=[2.0, 2.5, 2.55, 2.60, 2.65], g_term=0.010, cap_growth=0.02,
        s12=0.45, r12=0.70, s3_r=0.70, norm=dict(office=11.0, mall=11.6, apt=1.65, other=3.85, hotel=0.55,
                                                 cost_cut=0.30, int_inc=0.30),
        text="写字楼在租租金 2029 年降至约 490 元、出租率约 85%（收入较 2026E −21%），商城 −10%；"
             "维持性资本开支 2.5 亿；一、二期 2038 年、三期 2052 年续期各付出其后价值的 70%；永续增长 1.0%"),
    "base": dict(
        p=0.50,
        g={"office": [-0.06, -0.03, 0.00, 0.02, 0.02], "mall": [-0.02, -0.01, 0.01, 0.02, 0.02],
           "apt": [-0.03, 0.00, 0.01, 0.02, 0.02], "other": [-0.01, 0.00, 0.01, 0.02, 0.02],
           "fixed": [-0.01, 0.00, 0.015, 0.02, 0.02]},
        hotel=[0.80, 0.82, 0.84, 0.86, 0.88],
        capex=[1.5, 1.8, 1.84, 1.87, 1.91], g_term=0.015, cap_growth=0.02,
        s12=0.40, r12=0.40, s3_r=0.40, norm=dict(office=12.4, mall=12.4, apt=1.80, other=3.95, hotel=0.80,
                                                 cost_cut=0.0, int_inc=0.40),
        text="写字楼收入 2027 −6%、2028 −3% 后企稳（在租租金约 540 元、出租率约 89%），商城小幅回落后随通胀；"
             "维持性资本开支 1.8 亿（现约 0.8 亿）；一、二期 2038 年续期付出其后价值的 40%，三期 2052 年同 40%；永续增长 1.5%"),
    "bull": dict(
        p=0.25,
        g={"office": [-0.02, 0.01, 0.03, 0.03, 0.03], "mall": [0.00, 0.01, 0.025, 0.03, 0.03],
           "apt": [0.00, 0.01, 0.02, 0.025, 0.025], "other": [0.00, 0.01, 0.02, 0.025, 0.025],
           "fixed": [-0.01, 0.005, 0.02, 0.025, 0.025]},
        hotel=[0.85, 0.90, 0.95, 1.00, 1.05],
        capex=[1.2, 1.3, 1.33, 1.35, 1.38], g_term=0.020, cap_growth=0.02,
        s12=0.35, r12=0.20, s3_r=0.20, norm=dict(office=13.1, mall=12.6, apt=1.85, other=4.00, hotel=0.95,
                                                 cost_cut=0.0, int_inc=0.45),
        text="写字楼 2027 年 −2% 后随 CBD 供应高峰过去回升 3%/年，商城稳中有升；维持性资本开支 1.3 亿；"
             "一、二期与三期续期各付出其后价值的 20%；永续增长 2.0%"),
}


def ebitda_path(s):
    """返回 {year: (ebitda, capex)}，2027-2031 显式，之后按永续增长。"""
    rev = {k: REV26[k] for k in ("office", "mall", "apt", "other")}
    fixed = FIXED26
    out = {}
    for i, y in enumerate(YEARS5):
        for k in rev:
            rev[k] *= 1 + s["g"][k][i]
        fixed *= 1 + s["g"]["fixed"][i]
        rent = rev["office"] + rev["mall"] + rev["apt"]
        lease = rent * DROP_RENT + rev["other"] * DROP_OTHER - fixed
        out[y] = (lease + s["hotel"][i], s["capex"][i], dict(rev), lease)
    return out


def tenure_factor(y, s):
    """国贸一、二期土地使用权租赁至 2038-08-29（2026H1_report 第 24-25 页）；三期土地使用权约 2052 年到期。"""
    f = 1.0
    if y == 2038:
        f -= s["s12"] * s["r12"] * (4 / 12)
    elif y > 2038:
        f -= s["s12"] * s["r12"]
    if y > 2052:
        f -= (1 - s["s12"]) * s["s3_r"]
    return f


def owner_earnings(s):
    path = ebitda_path(s)
    flows = {}
    e31, c31 = path[2031][0], path[2031][1]
    for y in range(2027, 2127):
        if y in path:
            e, c = path[y][0], path[y][1]
        else:
            n = y - 2031
            e = e31 * (1 + s["g_term"]) ** n
            c = c31 * (1 + s["cap_growth"]) ** n
            c = min(c, e * 0.20)
        da = tax_da(y, c)
        oe = e - c - TAX * max(e - da, 0.0)
        flows[y] = oe * tenure_factor(y, s)
    return flows


def pv(flows, r, oe_h2=OE_H2_26):
    v = oe_h2  # 2026H2 所有者收益，按估值日近似不折现
    for y, f in flows.items():
        t = y + 0.5 - VAL_DATE
        v += f / (1 + r) ** t
    return v


def value_per_share(s, r=COE):
    flows = owner_earnings(s)
    op = pv(flows, r)
    eq = op + NET_CASH_ADJ + NON_OPER
    return eq / SHARES, op, flows


def tv_share(s, r=COE):
    flows = owner_earnings(s)
    total = pv(flows, r)
    late = sum(f / (1 + r) ** (y + 0.5 - VAL_DATE) for y, f in flows.items() if y > 2031)
    return late / total


def norm_np(s):
    n = s["norm"]
    lease = (n["office"] + n["mall"] + n["apt"]) * DROP_RENT + n["other"] * DROP_OTHER - FIXED26 + n["cost_cut"]
    pbt = lease + n["hotel"] - DA26 + n["int_inc"] - 0.02 + 0.05
    return pbt * (1 - TAX) - 0.008


def solve(fn, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (fn(mid) - target) * (fn(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main():
    print("== 输入核对 ==")
    print(f"2026E 分业态收入: " + ", ".join(f"{k} {v:.3f}" for k, v in REV26.items()) + f"; 合计 {sum(REV26.values()):.2f}")
    print(f"租赁分部 EBITDA 2026E {LEASE_EBITDA_26:.3f}（H2 {LEASE_EBITDA_H2:.3f}）；酒店 {HOTEL_EBITDA_26:.3f}；固定付现成本 {FIXED26:.3f}")
    print(f"2026E 利润总额 {PBT26:.2f}（H2 {PBT26 - PBT_H1:.2f}），归母净利 {NP26:.2f}；2026H2 所有者收益 {OE_H2_26:.2f}")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} = 货币资金 {CASH} − 押金 {TENANT_DEPOSIT} − 代收款 {CUSTODIAL} − 备付 {OPER_RESERVE} − 租赁负债 {LEASE_LIAB}")
    print()
    res = {}
    for k, s in SCEN.items():
        v, op, flows = value_per_share(s)
        v8 = value_per_share(s, 0.08)[0]
        v10 = value_per_share(s, 0.10)[0]
        res[k] = (v, v8, v10)
        path = ebitda_path(s)
        oe5 = [flows[y] for y in YEARS5]
        gr = [oe5[0] / OE_REF_2026(s) - 1] + [oe5[i] / oe5[i - 1] - 1 for i in range(1, 5)]
        print(f"== {k} (p={s['p']}) ==")
        print("  EBITDA " + ", ".join(f"{y}:{path[y][0]:.2f}" for y in YEARS5) +
              " | 资本开支 " + ", ".join(f"{path[y][1]:.2f}" for y in YEARS5))
        print("  写字楼收入 " + ", ".join(f"{y}:{path[y][2]['office']:.2f}" for y in YEARS5))
        print("  所有者收益 " + ", ".join(f"{y}:{flows[y]:.2f}" for y in YEARS5) +
              f" | 2032:{flows[2032]:.2f} 2039:{flows[2039]:.2f} 2053:{flows[2053]:.2f}")
        print("  所有者收益增速 " + ", ".join(f"{x:+.1%}" for x in gr) + f" | 永续 {s['g_term']:.1%}")
        print(f"  经营价值 {op:.1f} 亿；V = {v:.2f} 元（8%: {v8:.2f}，10%: {v10:.2f}）；终值占比 {tv_share(s):.0%}")
        print(f"  2026 正常化归母净利 {norm_np(s):.2f} 亿")
    vw = sum(SCEN[k]["p"] * res[k][0] for k in SCEN)
    vw8 = sum(SCEN[k]["p"] * res[k][1] for k in SCEN)
    vw10 = sum(SCEN[k]["p"] * res[k][2] for k in SCEN)
    print()
    print(f"加权 V = {vw:.2f} 元；P/V = {PRICE / vw:.3f}；8%: {vw8:.2f}，10%: {vw10:.2f}")

    # 隐含回报：基准情景所有者收益流 + 净现金 = 现价
    base = SCEN["base"]
    irr = solve(lambda r: value_per_share(base, r)[0], 0.04, 0.20, PRICE)
    print(f"现价隐含回报（基准现金流）= {irr:.2%}")

    # 反向 DCF ①：基准 2027 所有者收益起，2028 年起恒定增速（含土地租期调整）
    flows_b = owner_earnings(base)
    oe27 = flows_b[2027]

    def v_const_g(g):
        v = OE_H2_26
        for y in range(2027, 2127):
            f = oe27 * (1 + g) ** (y - 2027) * tenure_factor(y, base)
            v += f / (1 + COE) ** (y + 0.5 - VAL_DATE)
        return (v + NET_CASH_ADJ + NON_OPER) / SHARES

    g_imp = solve(v_const_g, -0.05, 0.08, PRICE)
    print(f"反向 DCF：基准 2027 所有者收益 {oe27:.2f} 亿起永续增速 {g_imp:.2%}（9%，含土地租期调整）")

    # 反向 DCF ②：10 年复合增速，之后 1.5%
    def v_10y(g):
        v = OE_H2_26
        f = oe27
        for y in range(2027, 2127):
            if y > 2027:
                f *= (1 + g) if y <= 2036 else (1 + base["g_term"])
            v += f * tenure_factor(y, base) / (1 + COE) ** (y + 0.5 - VAL_DATE)
        return (v + NET_CASH_ADJ + NON_OPER) / SHARES

    g10 = solve(v_10y, -0.05, 0.15, PRICE)
    print(f"反向 DCF：2028-2036 年所有者收益复合增速 {g10:.2%}，之后 1.5%")

    # 不做土地租期调整的基准 V（对照）
    nt = dict(base, s12=0.0, r12=0.0, s3_r=0.0)
    print(f"对照：基准不做土地到期调整 V = {value_per_share(nt)[0]:.2f}；资本开支维持 0.8 亿 V = "
          f"{value_per_share(dict(base, capex=[0.8, 0.82, 0.84, 0.86, 0.88]))[0]:.2f}；押金不扣 V = "
          f"{value_per_share(base)[0] + TENANT_DEPOSIT / SHARES:.2f}")

    # 交叉验证
    div = 1.07
    print()
    print("== 交叉验证 ==")
    print(f"股息率 {div / PRICE:.2%}；市值 {PRICE * SHARES:.1f}；PE(2026E) {PRICE * SHARES / NP26:.1f}；"
          f"EV {PRICE * SHARES - NET_CASH_ADJ:.1f}，EV/EBIT(2026E) {(PRICE * SHARES - NET_CASH_ADJ) / (LEASE_EBITDA_26 + HOTEL_EBITDA_26 - DA26):.1f}；"
          f"PB {PRICE * SHARES / 93.03:.2f}")
    # 资本化率 NAV：正常化（基准）EBITDA − 维持性资本开支，按私募市场资本化率；土地租期按同一隐含折现率调整
    noi_lease = norm_lease_ebitda(base) - 1.6
    noi_hotel = base["norm"]["hotel"] - 0.2
    for cap_off, cap_hot in ((0.045, 0.065), (0.050, 0.070), (0.055, 0.075)):
        gross = noi_lease / cap_off + noi_hotel / cap_hot
        r_imp = cap_off + 0.015
        sh12 = ((1.015) / (1 + r_imp)) ** 12
        sh3 = ((1.015) / (1 + r_imp)) ** 26
        hair = base["s12"] * sh12 * base["r12"] + (1 - base["s12"]) * sh3 * base["s3_r"]
        net = gross * (1 - hair)
        book = 55.94 + 12.87 + 4.10
        tax_gain = max(net - book, 0) * TAX
        print(f"  资本化率 写字楼/商城 {cap_off:.1%}、酒店 {cap_hot:.1%}：物业毛值 {gross:.0f}，土地到期折减 {hair:.0%} → {net:.0f}；"
              f"NAV {(net + NET_CASH_ADJ) / SHARES:.2f} 元；扣 25% 增值所得税 {(net - tax_gain + NET_CASH_ADJ) / SHARES:.2f} 元")
    # 股利折现对照：每股 1.07 元，增长 1.5%，加经调整净现金
    print(f"  股利折现对照（1.07 元、增长 1.5%、9%）：{div * 1.015 / (COE - 0.015) + NET_CASH_ADJ / SHARES:.2f} 元")

    # 三季度估计（按 2025 年 Q3/Q4 结构拆分 H2）
    h2_rev = sum(H2_2025[k] * (1 + H2_YOY[k]) for k in H2_2025)
    q3_rev = h2_rev * 9.313 / 18.804
    q3_pbt = (PBT26 - PBT_H1) * 4.109 / 7.612
    print()
    print(f"== 2026Q3 估计 == 营收 {q3_rev:.2f} 亿（2025Q3 9.31），利润总额 {q3_pbt:.2f}，归母净利 {q3_pbt * 0.75:.2f}（2025Q3 3.08）")

    # 证伪条件触发后的加权 V：熊市情景不变，基准与牛市情景按触发事实下移（F5 为上行，改概率）
    print()
    print("== 证伪触发后的加权 V ==")
    bear, bull = SCEN["bear"], SCEN["bull"]

    def wv(b, u, d=bear, w=(0.25, 0.50, 0.25)):
        return w[0] * value_per_share(d)[0] + w[1] * value_per_share(b)[0] + w[2] * value_per_share(u)[0]

    f1b = dict(base, g=dict(base["g"], office=[-0.10, -0.06, -0.02, 0.01, 0.02]))
    f1u = dict(bull, g=dict(bull["g"], office=base["g"]["office"]))
    f2b = dict(base, g=dict(base["g"], mall=[-0.06, -0.04, -0.01, 0.015, 0.02]))
    f2u = dict(bull, g=dict(bull["g"], mall=base["g"]["mall"]))
    f3b = dict(base, capex=[2.5, 2.5, 2.55, 2.60, 2.65])
    f3u = dict(bull, capex=[2.0, 2.0, 2.04, 2.08, 2.12])
    f4b = dict(base, r12=0.70)
    f4u = dict(bull, r12=0.70)
    print(f"  F1 写字楼（基准改为 2027 −10%/2028 −6%，牛市改为原基准路径）：V = {wv(f1b, f1u):.2f}；单看基准 {value_per_share(f1b)[0]:.2f}")
    print(f"  F2 商城（基准改为 2027 −6%/2028 −4%，牛市改为原基准路径）：V = {wv(f2b, f2u):.2f}；单看基准 {value_per_share(f2b)[0]:.2f}")
    print(f"  F3 维持性资本开支（基准 2.5 亿、牛市 2.0 亿）：V = {wv(f3b, f3u):.2f}；单看基准 {value_per_share(f3b)[0]:.2f}")
    print(f"  F4 一、二期续期付出 70%（基准、牛市同改）：V = {wv(f4b, f4u):.2f}；单看基准 {value_per_share(f4b)[0]:.2f}")
    v5 = wv(base, bull, w=(0.10, 0.45, 0.45))
    print(f"  F5 上行（写字楼企稳，概率改为 0.10/0.45/0.45）：V = {v5:.2f}")
    # V 不变时进入各档的价格
    print(f"  分档价格（V={vw:.2f}）：≤0.75 → {0.75 * vw:.2f}；0.90 → {0.90 * vw:.2f}；1.10 → {1.10 * vw:.2f}")


def norm_lease_ebitda(s):
    n = s["norm"]
    return (n["office"] + n["mall"] + n["apt"]) * DROP_RENT + n["other"] * DROP_OTHER - FIXED26 + n["cost_cut"]


def OE_REF_2026(s):
    """2026 全年所有者收益（同口径：维持性资本开支取 2026 计划 0.8 亿）。"""
    e = LEASE_EBITDA_26 + HOTEL_EBITDA_26
    return e - 0.8 - TAX * (e - DA26)


if __name__ == "__main__":
    main()
