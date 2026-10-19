#!/usr/bin/env python3
"""潍柴动力（000338.SZ / 2338.HK）独立估值（OI-291 b02，价格日 2026-10-19）。

口径：归母；每股按 A+H 全部股份 86.4022 亿股（A 66.9718 + H 19.4304，
2026-10-16 中期派息实施公告第 2 页）。金额单位亿元。
方法：分部所有者收益 DCF（发动机拆成传统内燃机／大缸径与发电／新能源三块，
另有整车及零部件、农机、凯傲），分部税后利润按持股比例折算；净利息不进
所有者收益，改为把扣除凯傲后的经调整净现金按归母比例按面值加回；
非经营资产（上市公司股权、财务公司股权等）按市值或账面打折加回。
现价 21.41 元含 2026 中期息 0.517 元（除息日 10-23 晚于价格日），
故 6-30 现金不扣中期息，只扣已在 6-30 入账、8 月已付的 2025 年末期息。
运行：python3 valuation.py
"""

PRICE = 21.41            # A 股 2026-10-19 收盘（腾讯日线）
SHARES = 86.40220621     # 亿股，A+H
COE = 0.09
INTERIM_DPS = 0.517      # 2026 中期息，10-23 除息（现价含息）

# ---------------------------------------------------------------------------
# 一、2026-06-30 资产负债表（2026H1_report 第 43-45、87-88、94、105-111 页）
# ---------------------------------------------------------------------------
cash = 775.43                 # 货币资金，其中存放财务公司 356.70，境外 58.21
cash_restricted = 119.26      # 受限货币资金（保证金、质押）
fin_co_deposit = 356.70       # 存放山东重工集团财务公司（关联方）
struct_deposit = 138.83       # 交易性金融资产：结构性存款
other_debt_inst = 7.17        # 交易性金融资产：其他债务工具
time_dep_onca = 266.94        # 其他非流动资产：定期存款及大额存单
time_dep_pledged = 107.83     # 其中质押
gross_cash = cash + struct_deposit + other_debt_inst + time_dep_onca
restricted = cash_restricted + time_dep_pledged

st_loan = 15.46
lt_loan = 98.05 + 6.13        # 含一年内到期；其中潍柴香港欧元贷款 85.99（11.07 亿欧元）
bonds = 107.33                # 全部为凯傲中票与公司债（含一年内到期 3.18）
cp = 6.03                     # 其他流动负债：短期融资券（凯傲）
lease = 64.63                 # 租赁负债（含一年内到期 13.33）
fin_debt = st_loan + lt_loan + bonds + cp + lease
div_payable = 32.32           # 应付股利：2025 年末期息，2026-08 已付

# 凯傲拆分（假设，见正文）：凯傲现金不超过境外货币资金 58.21
kion_cash = 43.0
kion_debt = bonds + cp + 8.0 + 10.0 + 46.6   # 债券+商票+短借+长借+租赁负债（假设）
exk_gross_cash = gross_cash - kion_cash
exk_unrestricted = exk_gross_cash - restricted
exk_debt = fin_debt - kion_debt
exk_net_cash = exk_unrestricted - exk_debt

EXK_REVENUE_2026 = 1600.0     # 扣凯傲营收 2026E（约 2,520 − 920）
exk_pension_like = 5.0        # 扣凯傲的设定受益、辞退福利等（估）

# 非经营资产（2026-06-30）
fvoci = 64.89                 # 其他权益工具投资：徐工、山推、中力、福田、三一、快仓等
ballard = 8.02                # 交易性金融资产：巴拉德股票（丧失重大影响后转入）
other_ncfa = 4.60             # 其他非流动金融资产
fin_co_equity = 22.25         # 山东重工财务公司 23.44% 权益法账面
other_assoc = 59.56 - 22.25   # 其他联营合营账面

# 凯傲市值（stockanalysis，2026-10-19 收盘 34.09 欧元，13,112 万股）
KION_PX_EUR = 34.09
KION_SHARES_YI = 1.3112
KION_STAKE = 0.4652
EURCNY = 7.767                # 2026-06-30 报表折算率（11.07 亿欧元 = 85.99 亿元）

# ---------------------------------------------------------------------------
# 二、分部税后归母系数（税率 × 持股）
# ---------------------------------------------------------------------------
F = {
    "ice": (1 - 0.14) * 0.98,   # 传统内燃机及其他发动机（母公司、扬州、重庆等）
    "pg": (1 - 0.15) * 0.88,    # 大缸径与发电（含 PSI，持股 45.99%）
    "ne": (1 - 0.14) * 0.95,    # 新能源动力（电池、电机电控、燃料电池、SOFC）
    "elim": (1 - 0.14) * 0.80,  # 分部间抵销（主要是发动机配套陕重汽）
    "veh": (1 - 0.15) * 0.60,   # 整车及零部件：陕重汽 51%、法士特 51%、汉德 97%、火炬 70%
    "ag": (1 - 0.15) * 0.611,   # 潍柴雷沃 61.10%
}
ELIM_RATE = -0.09               # 分部间抵销 ≈ 发动机分部税前利润 × −9%

YEARS = [2026, 2027, 2028, 2029, 2030, 2031]


def path(level, growth):
    out = [level]
    for g in growth:
        out.append(out[-1] * (1 + g))
    return out


SCEN = {
    "bear": dict(
        p=0.25,
        ice=path(60.0, [-0.10] * 5),
        pg=path(28.0, [0.05, -0.15, -0.15, 0.0, 0.0]),
        ne=[-9.0, -9.0, -8.0, -6.0, -5.0, -4.0],
        veh=path(6.0, [0.0] * 5),
        ag=path(5.0, [0.0] * 5),
        kion=path(9.0, [0.0] * 5),
        reinv=0.20, reinv_k=0.20, g_term=0.005,
        net_int_pre=12.0, inv_inc=1.5,
        reserve=0.06, finco_haircut=0.10, attrib_cash=0.75,
        h_fvoci=0.20, h_assoc=0.50,
    ),
    "base": dict(
        p=0.50,
        ice=path(66.0, [-0.06] * 5),
        pg=path(40.0, [0.10, 0.08, 0.05, 0.03, 0.03]),
        ne=[-8.0, -6.0, -4.0, -2.0, 0.0, 1.0],
        veh=path(14.0, [0.02] * 5),
        ag=path(8.0, [0.02] * 5),
        kion=path(14.0, [0.02] * 5),
        reinv=0.15, reinv_k=0.15, g_term=0.015,
        net_int_pre=18.0, inv_inc=2.2,
        reserve=0.03, finco_haircut=0.0, attrib_cash=0.80,
        h_fvoci=0.10, h_assoc=0.30,
    ),
    "bull": dict(
        p=0.25,
        ice=path(72.0, [-0.03] * 5),
        pg=path(52.0, [0.15, 0.12, 0.08, 0.05, 0.03]),
        ne=[-6.0, -2.0, 2.0, 4.0, 6.0, 8.0],
        veh=path(20.0, [0.03] * 5),
        ag=path(10.0, [0.03] * 5),
        kion=path(18.0, [0.03] * 5),
        reinv=0.20, reinv_k=0.15, g_term=0.025,
        net_int_pre=20.0, inv_inc=2.5,
        reserve=0.02, finco_haircut=0.0, attrib_cash=0.82,
        h_fvoci=0.10, h_assoc=0.30,
    ),
}


def op_attrib(s, i):
    """第 i 年（0=2026）扣凯傲经营性归母税后利润与凯傲归母利润。"""
    eng = s["ice"][i] + s["pg"][i] + s["ne"][i]
    elim = ELIM_RATE * eng
    core = (s["ice"][i] * F["ice"] + s["pg"][i] * F["pg"] + s["ne"][i] * F["ne"]
            + elim * F["elim"] + s["veh"][i] * F["veh"] + s["ag"][i] * F["ag"])
    pretax = eng + elim + s["veh"][i] + s["ag"][i]
    return core, s["kion"][i], pretax


def owner_earnings(s, i):
    core, kion, _ = op_attrib(s, i)
    return core * (1 - s["reinv"]) + kion * (1 - s["reinv_k"])


def adj_net_cash(s):
    reserve = s["reserve"] * EXK_REVENUE_2026
    haircut = s["finco_haircut"] * fin_co_deposit
    pre = exk_net_cash - div_payable - reserve - exk_pension_like - haircut
    return pre * s["attrib_cash"], pre


def non_op(s):
    v = ((fvoci + ballard) * (1 - s["h_fvoci"]) + other_ncfa * 0.8
         + fin_co_equity + other_assoc * (1 - s["h_assoc"]))
    return v * 0.90          # 约一成由非全资子公司持有


def pv_operating(s, r, g_term=None):
    g_term = s["g_term"] if g_term is None else g_term
    pv = 0.5 * owner_earnings(s, 0)                    # 2026 下半年，t≈0
    for k in range(1, 6):                              # 2027-2031，年中折现
        pv += owner_earnings(s, k) / (1 + r) ** (k - 0.3)
    tv = owner_earnings(s, 5) * (1 + g_term) / (r - g_term)
    pv_tv = tv / (1 + r) ** 4.7
    return pv + pv_tv, pv_tv


def value(s, r=COE, g_term=None):
    op, pv_tv = pv_operating(s, r, g_term)
    cash_attr, _ = adj_net_cash(s)
    total = op + cash_attr + non_op(s)
    return total / SHARES, dict(op=op, tv=pv_tv, cash=cash_attr, nonop=non_op(s), total=total)


def norm_np(s):
    core, kion, _ = op_attrib(s, 0)
    interest = s["net_int_pre"] * 0.85 * s["attrib_cash"]
    return core + kion + interest + s["inv_inc"]


def weighted(r=COE):
    return sum(SCEN[k]["p"] * value(SCEN[k], r)[0] for k in SCEN)


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


def main():
    print("=== 资产负债与净现金（亿元） ===")
    print(f"现金类合计 {gross_cash:.2f}，受限 {restricted:.2f}，金融负债 {fin_debt:.2f}")
    print(f"扣凯傲：现金类 {exk_gross_cash:.2f}，非受限 {exk_unrestricted:.2f}，"
          f"金融负债 {exk_debt:.2f}，净现金 {exk_net_cash:.2f}")
    for k, s in SCEN.items():
        a, pre = adj_net_cash(s)
        print(f"  {k}: 经调整净现金（扣末期息、经营备付、类债务、财务公司折扣）{pre:.2f}"
              f" → 归母 {a:.2f}（{a / SHARES:.2f} 元/股）；非经营资产 {non_op(s):.2f}")
    print(f"关联方存款（财务公司）{fin_co_deposit:.2f}，占非受限现金类 "
          f"{fin_co_deposit / (gross_cash - restricted):.1%}")

    print("\n=== 2026 正常化（亿元） ===")
    for k, s in SCEN.items():
        core, kion, pretax = op_attrib(s, 0)
        print(f"  {k}: 扣凯傲税前 {pretax:.1f}，扣凯傲经营归母 {core:.1f}，凯傲归母 {kion:.1f}，"
              f"正常化归母净利（含净利息） {norm_np(s):.1f}")

    print("\n=== 分部税前经常性利润路径（亿元，扣凯傲；凯傲为归母净利） ===")
    for k, s in SCEN.items():
        print(f"  [{k}]")
        for i, y in enumerate(YEARS):
            core, kion, pretax = op_attrib(s, i)
            eng = s["ice"][i] + s["pg"][i] + s["ne"][i]
            print(f"   {y}: 内燃机 {s['ice'][i]:.1f} 发电 {s['pg'][i]:.1f} 新能源 {s['ne'][i]:.1f} "
                  f"抵销 {ELIM_RATE * eng:.1f} 整车 {s['veh'][i]:.1f} 农机 {s['ag'][i]:.1f} "
                  f"| 税前 {pretax:.1f} → 经营归母 {core:.1f} + 凯傲 {kion:.1f} = {core + kion:.1f}")

    print("\n=== 所有者收益路径（亿元） ===")
    for k, s in SCEN.items():
        oe = [owner_earnings(s, i) for i in range(6)]
        gr = [oe[i] / oe[i - 1] - 1 for i in range(1, 6)]
        print(f"  {k}: " + "  ".join(f"{y}:{v:.1f}" for y, v in zip(YEARS, oe)))
        print(f"       增速 2027-2031: " + " ".join(f"{g:+.1%}" for g in gr)
              + f"；终值增长 {s['g_term']:.1%}；再投资率 {s['reinv']:.0%}")

    print("\n=== 三情景 V（元/股，COE 9%） ===")
    for k, s in SCEN.items():
        v, d = value(s)
        print(f"  {k}: V={v:.2f}  p={s['p']:.2f}  经营 {d['op']:.0f}（终值 {d['tv']:.0f}，"
              f"占经营 {d['tv'] / d['op']:.0%}）+ 净现金 {d['cash']:.0f} + 非经营 {d['nonop']:.0f}"
              f" = {d['total']:.0f}")
    vw = weighted()
    print(f"加权 V = {vw:.2f}；P/V = {PRICE / vw:.3f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"COE 8%: 加权 V = {v8:.2f}；COE 10%: 加权 V = {v10:.2f}")
    for k in SCEN:
        print(f"  {k}: 8% {value(SCEN[k], 0.08)[0]:.2f} / 10% {value(SCEN[k], 0.10)[0]:.2f}")

    base = SCEN["base"]
    irr = solve(lambda r: value(base, r)[0], 0.04, 0.20, PRICE)
    print(f"\n现价隐含回报（基准情景，含终值与净现金）= {irr:.2%}")
    # 反向 DCF：基准 2026 所有者收益起步，按单一永续增速 g 使 V=现价
    base_v = value(base)[1]
    target_op = PRICE * SHARES - base_v["cash"] - base_v["nonop"]
    oe0 = owner_earnings(base, 0)

    def pv_const(g):
        pv = 0.5 * oe0
        for k in range(1, 6):
            pv += oe0 * (1 + g) ** k / (1 + COE) ** (k - 0.3)
        tv = oe0 * (1 + g) ** 6 / (COE - g)
        return pv + tv / (1 + COE) ** 4.7
    g_impl = solve(pv_const, -0.05, 0.08, target_op)
    print(f"反向 DCF：现价扣净现金与非经营后经营部分 {target_op:.0f} 亿，"
          f"以 2026 基准所有者收益 {oe0:.1f} 起步，隐含永续增速 {g_impl:.2%}")

    # 十年增速版本：10 年增速 g10、之后 1.5% 永续
    def pv_10(g10):
        pv = 0.5 * oe0
        oe = oe0
        for k in range(1, 11):
            oe *= 1 + g10
            pv += oe / (1 + COE) ** (k - 0.3)
        tv = oe * 1.015 / (COE - 0.015)
        return pv + tv / (1 + COE) ** 9.7
    g10 = solve(pv_10, -0.08, 0.10, target_op)
    print(f"反向 DCF（10 年后 1.5% 永续）：隐含 10 年所有者收益年增速 {g10:.2%}")

    # 增量回报：2026→2031 经营归母利润增量 ÷ 累计再投资
    c0 = sum(op_attrib(base, 0)[:2])
    c5 = sum(op_attrib(base, 5)[:2])
    reinv_sum = sum(op_attrib(base, i)[0] * base["reinv"] + op_attrib(base, i)[1] * base["reinv_k"]
                    for i in range(5))
    print(f"基准增量回报 ≈ (2031 经营归母 {c5:.1f} − 2026 {c0:.1f}) ÷ 累计再投资 {reinv_sum:.1f}"
          f" = {(c5 - c0) / reinv_sum:.1%}")

    print("\n=== 交叉验证 ===")
    kion_mkt = KION_PX_EUR * KION_SHARES_YI * KION_STAKE * EURCNY
    rk = 1 - SCEN['base']['reinv_k']
    kion_fund = sum((SCEN['base']['kion'][k] * rk) / (1 + COE) ** (k - 0.3) for k in range(1, 6)) \
        + 0.5 * SCEN['base']['kion'][0] * rk \
        + SCEN['base']['kion'][5] * rk * (1 + 0.015) / (COE - 0.015) / (1 + COE) ** 4.7
    print(f"凯傲 46.52% 市值 {kion_mkt:.1f} 亿（{kion_mkt / SHARES:.2f} 元/股）；"
          f"基准 DCF {kion_fund:.1f} 亿（{kion_fund / SHARES:.2f} 元/股）")
    core, kion, _ = op_attrib(base, 0)
    ice_ne = SCEN['base']['ice'][0] * F['ice'] + SCEN['base']['ne'][0] * F['ne']
    pg = SCEN['base']['pg'][0] * F['pg']
    elim = ELIM_RATE * (SCEN['base']['ice'][0] + SCEN['base']['pg'][0] + SCEN['base']['ne'][0]) * F['elim']
    veh = SCEN['base']['veh'][0] * F['veh']
    ag = SCEN['base']['ag'][0] * F['ag']
    cash_b, nonop_b = adj_net_cash(base)[0], non_op(base)
    sotp = {
        "传统内燃机+新能源 ×9": (ice_ne + elim) * 9,
        "大缸径与发电 ×15": pg * 15,
        "整车及零部件 ×9": veh * 9,
        "农机 ×10": ag * 10,
        "凯傲（市值）": kion_mkt,
        "经调整净现金（归母）": cash_b,
        "非经营资产": nonop_b,
    }
    tot = sum(sotp.values())
    for k, v in sotp.items():
        print(f"  {k}: {v:.1f}")
    print(f"分部加总 = {tot:.0f} 亿 → {tot / SHARES:.2f} 元/股")
    nn = norm_np(base)
    pe_med, pb_med = 13.65, 1.59   # 2014-2025 年末 PE、PB 中位数（数据包第八节）
    print(f"历史 PE 中位 {pe_med} × 基准正常化归母 {nn:.1f} = {pe_med * nn / SHARES:.2f} 元/股；"
          f"PB 中位 {pb_med} × 归母权益 961.02 = {pb_med * 961.02 / SHARES:.2f} 元/股")
    mcap = PRICE * SHARES
    print(f"市值 {mcap:.1f} 亿；市值/正常化归母 {mcap / nn:.1f}×；"
          f"（市值−归母净现金−非经营）/经营归母 {(mcap - cash_b - nonop_b) / (core + kion):.1f}×")
    dps_ttm = 0.358 + 0.374
    print(f"股息率：过去 12 个月 {dps_ttm / PRICE:.2%}；2026 中期 0.517 + 末期假设 0.40 → "
          f"{(0.517 + 0.40) / PRICE:.2%}")
    ev = mcap + 388.99 + fin_debt - (gross_cash - restricted) - (fvoci + ballard + other_ncfa + 59.56)
    ebit = 108.0 + 59.2
    print(f"EV/EBIT（少数股东权益按账面，EBIT=近 12 月扣凯傲经常性分部利润 108.0+凯傲分部 59.2）"
          f" ≈ {ev:.0f}/{ebit:.0f} = {ev / ebit:.1f}×")

    print("\n=== 分档价格（V 不变） ===")
    print(f"≤0.75 明显低估：≤{0.75 * vw:.2f}；0.75-0.90：{0.75 * vw:.2f}-{0.90 * vw:.2f}；"
          f"0.90-1.10：{0.90 * vw:.2f}-{1.10 * vw:.2f}；>1.10：>{1.10 * vw:.2f}")

    print("\n=== 证伪情形（触发后的加权 V） ===")
    import copy

    def reweighted(mod):
        saved = copy.deepcopy(SCEN)
        mod(SCEN)
        v = weighted()
        SCEN.clear()
        SCEN.update(saved)
        return v

    def f1(S):  # 内燃机侵蚀更快：三情景传统内燃机起点 −10%、年降幅再加 4 个百分点
        for k in S:
            g0 = S[k]["ice"][1] / S[k]["ice"][0] - 1
            S[k]["ice"] = path(S[k]["ice"][0] * 0.9, [g0 - 0.04] * 5)

    def f2(S):  # 数据中心周期见顶：发电板块 2027 起三年各 −10%
        for k in S:
            S[k]["pg"] = path(S[k]["pg"][0], [-0.10, -0.10, -0.10, 0.0, 0.0])

    def f3(S):  # 财务公司存款折价 30%
        for k in S:
            S[k]["finco_haircut"] = 0.30

    def f4(S):  # 凯傲归母利润三情景下调 30%
        for k in S:
            S[k]["kion"] = [x * 0.7 for x in S[k]["kion"]]

    def f5(S):  # 熊情景概率升到 50%（牛 10%、基准 40%）
        S["bear"]["p"], S["base"]["p"], S["bull"]["p"] = 0.50, 0.40, 0.10

    for name, fn in [("F1 内燃机侵蚀加速", f1), ("F2 数据中心发电周期见顶", f2),
                     ("F3 财务公司存款折价 30%", f3), ("F4 凯傲归母利润 −30%", f4),
                     ("F5 熊情景概率 50%", f5)]:
        print(f"  {name}: 加权 V = {reweighted(fn):.2f}")


if __name__ == "__main__":
    main()
