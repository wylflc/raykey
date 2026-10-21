# -*- coding: utf-8 -*-
"""华峰测控（688200）独立估值（OI-291 b15，价格日 2026-10-20）。

金额单位亿元，每股价值元/股。输入全部写在脚本内，来源见正文
`b15/companies/688200_华峰测控.md`。运行：python3 valuation.py
"""

# ---------------- 快照 ----------------
PRICE = 300.00                 # 2026-10-20 收盘（腾讯日线）
SHARES = 2.01117417            # 亿股，2026-09-11 总股本 201,117,417 股（受托管理报告第 5 页）
TREASURY = 0.0                 # 回购专户：06-30 余 110,400 股已于 2026-08 用于 2024 年激励归属（buyback_20260812 第 2-3 页），按 0 计

# ---------------- 可转债（华峰转债 118071） ----------------
CB_FACE = 7.4947               # 未转股面值（2026H1_report 第 55-56 页）
CB_CONV_PRICE = 335.33         # 2026-09 调整后转股价（financing_20260911 第 5 页）
CB_SHARES = CB_FACE / CB_CONV_PRICE   # 全部转股新增股数（亿股）

# ---------------- 经调整净现金（无杠杆口径，不含可转债） ----------------
CASH = 25.71                   # 货币资金（含 7.39 亿可转债募集资金）
RESTRICTED = 0.0052            # 受限保证金（2026H1_report 第 112 页）
CDS = 1.6471 + 0.2184 + 1.7362 # 大额定期存单：其他流动资产 + 一年内到期 + 其他非流动资产（第 112、124 页附注）
LEASE = 0.18 + 0.07            # 租赁负债（含一年内到期）
OP_RESERVE = 2.0               # 经营备付：约两个月付现成本
NET_CASH_ADJ = CASH - RESTRICTED + CDS - LEASE - OP_RESERVE

# ---------------- 非经营资产（税后） ----------------
TAX_GAIN = 0.15                # 公司对公允价值变动按 15% 计递延税（2026H1_report 第 124 页）
# 联讯仪器（688808）：上市前持股约 188.9 万股（上市后总股本 1.84%），2026-09-29 10转4.8 后约 279.6 万股
LX_SHARES = 0.018891 * 1.48    # 亿股
LX_PRICE = 1193.79             # 2026-10-20 收盘（腾讯日线）
LX_COST = 0.30                 # 初始成本（期末 35.26 亿 − 累计计入 OCI 34.96 亿）
LX_DISCOUNT = 0.10             # 限售至约 2027-04-24 与高波动的折扣
lx_mv = LX_SHARES * LX_PRICE
lx_val = lx_mv * (1 - LX_DISCOUNT)
LX_NET = lx_val - TAX_GAIN * (lx_val - LX_COST)
# 其他权益工具投资（韬盛、芯长征、中科四点零、士模微）：账面 1.147，累计利得 0.577
OTHER_EQ_NET = 1.147 - TAX_GAIN * 0.577
# 交易性金融资产（芯联集成股票 + 诺德单一资产计划）：06-30 账面 2.085，成本 1.037；按科创50 06-30→10-20 跌幅折算
STAR50_RATIO = 1342.42 / 2207.86
trading_val = 2.085 * STAR50_RATIO
TRADING_NET = trading_val - TAX_GAIN * max(trading_val - 1.037, 0.0)
# 其他非流动金融资产（私募基金，按净资产份额计量）：账面 2.890，成本 1.568；打八折
fund_val = 2.890 * 0.80
FUND_NET = fund_val - TAX_GAIN * max(fund_val - 1.568, 0.0)
LT_EQUITY = 0.078
NON_OP = LX_NET + OTHER_EQ_NET + TRADING_NET + FUND_NET + LT_EQUITY

# ---------------- 经营假设 ----------------
G_TERM = 0.025
CAP_INT = 0.65                 # 每增加 1 元收入需追加营运资本约 0.55 元 + 固定资产约 0.10 元
FADE_YEARS = 5                 # 2032-2036 线性收敛到终值增长

SCENARIOS = {
    # 正常化收入（2026 周期中位）、核心经营利润率（含股份支付、经常性其他收益，不含利息与公允价值）、税率、2027-2031 收入增速
    "bear": dict(p=0.25, R0=13.5, margin=0.30, tax=0.10, growth=[0.06, 0.06, 0.05, 0.05, 0.04]),
    "base": dict(p=0.50, R0=16.0, margin=0.35, tax=0.09, growth=[0.16, 0.14, 0.12, 0.10, 0.08]),
    "bull": dict(p=0.25, R0=18.0, margin=0.39, tax=0.08, growth=[0.28, 0.25, 0.22, 0.18, 0.15]),
}

# 正常化归母净利（报表口径，含净利息）：利息收入约 0.45 亿 − 可转债实际利率利息约 0.17 亿，税后
NET_INTEREST_AT = (0.45 - 0.17) * (1 - 0.15)


def path(growth):
    last = growth[-1]
    fade = [last + (G_TERM - last) * (i + 1) / FADE_YEARS for i in range(FADE_YEARS)]
    return list(growth) + fade


def operating_value(R0, margin, tax, growth, coe, detail=False):
    nm = margin * (1 - tax)
    gs = path(growth)
    # 2026 下半年存根（06-30 资产负债表之后、2027 之前）：半年正常化所有者收益
    oe_2026 = R0 * nm - CAP_INT * (R0 - R0 / (1 + gs[0]))
    stub = 0.5 * oe_2026
    R, pv, rows = R0, 0.0, []
    for t, g in enumerate(gs, 1):
        Rn = R * (1 + g)
        nopat = Rn * nm
        reinv = CAP_INT * (Rn - R)
        oe = nopat - reinv
        pv += oe / (1 + coe) ** t
        rows.append((2026 + t, g, Rn, nopat, reinv, oe))
        R = Rn
    Rt = R * (1 + G_TERM)
    oe_t = Rt * nm - CAP_INT * (Rt - R)
    tv = oe_t / (coe - G_TERM)
    pv_tv = tv / (1 + coe) ** len(gs)
    ev = stub + pv + pv_tv
    if detail:
        return ev, pv_tv / ev, rows, stub, oe_t
    return ev


def per_share(equity):
    v_debt = (equity - CB_FACE) / (SHARES - TREASURY)
    v_conv = equity / (SHARES - TREASURY + CB_SHARES)
    return min(v_debt, v_conv), v_debt, v_conv


def scenario_values(coe):
    out = {}
    for k, s in SCENARIOS.items():
        ev = operating_value(s["R0"], s["margin"], s["tax"], s["growth"], coe)
        eq = ev + NET_CASH_ADJ + NON_OP
        out[k] = per_share(eq) + (ev, eq)
    return out


def weighted(coe):
    vals = scenario_values(coe)
    return sum(SCENARIOS[k]["p"] * vals[k][0] for k in SCENARIOS), vals


def solve(f, lo, hi, it=200):
    flo = f(lo)
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    s = SCENARIOS["base"]
    target = PRICE * (SHARES - TREASURY) + CB_FACE   # 债务法：市值 + 可转债面值 = 经营价值 + 净现金 + 非经营资产
    f = lambda r: operating_value(s["R0"], s["margin"], s["tax"], s["growth"], r) + NET_CASH_ADJ + NON_OP - target
    return solve(f, 0.026, 0.30)


def reverse_dcf():
    s = SCENARIOS["base"]
    target_ev = PRICE * (SHARES - TREASURY) + CB_FACE - NET_CASH_ADJ - NON_OP
    # (1) 10 年恒定收入增速（利润率、再投资强度同基准），之后 2.5% 永续
    def ev10(g):
        nm = s["margin"] * (1 - s["tax"])
        R, pv = s["R0"], 0.5 * (s["R0"] * nm - CAP_INT * (s["R0"] - s["R0"] / (1 + g)))
        for t in range(1, 11):
            Rn = R * (1 + g)
            pv += (Rn * nm - CAP_INT * (Rn - R)) / 1.09 ** t
            R = Rn
        Rt = R * (1 + G_TERM)
        pv += (Rt * nm - CAP_INT * (Rt - R)) / (0.09 - G_TERM) / 1.09 ** 10
        return pv
    g10 = solve(lambda g: ev10(g) - target_ev, 0.0, 0.80)
    # (2) 永续增速：EV = NOPAT1 ×(1 − g/ROIC)/(9% − g)，ROIC = 增量回报
    nopat0 = s["R0"] * s["margin"] * (1 - s["tax"])
    roic = s["margin"] * (1 - s["tax"]) / CAP_INT
    gp = solve(lambda g: nopat0 * (1 + g) * (1 - g / roic) / (0.09 - g) - target_ev, 0.0, 0.0899)
    return g10, gp, target_ev


if __name__ == "__main__":
    print("== 输入 ==")
    print(f"现价 {PRICE:.2f} 元；总股本 {SHARES:.4f} 亿股；市值 {PRICE*SHARES:.1f} 亿")
    print(f"经调整净现金（无杠杆，不含可转债）{NET_CASH_ADJ:.2f} 亿：现金 {CASH} + 存单 {CDS:.2f} − 受限 {RESTRICTED} − 租赁 {LEASE:.2f} − 备付 {OP_RESERVE}")
    print(f"联讯仪器：{LX_SHARES*1e4:.1f} 万股 × {LX_PRICE} = 市值 {lx_mv:.2f} 亿；折扣后 {lx_val:.2f}；税后 {LX_NET:.2f} 亿")
    print(f"其他权益工具 {OTHER_EQ_NET:.2f}；交易性金融资产 {TRADING_NET:.2f}；私募基金 {FUND_NET:.2f}；长投 {LT_EQUITY:.2f}")
    print(f"非经营资产合计（税后）{NON_OP:.2f} 亿")
    print(f"可转债：面值 {CB_FACE} 亿，转股价 {CB_CONV_PRICE}，转股数 {CB_SHARES*1e4:.1f} 万股")
    print()
    for coe in (0.09,):
        vw, vals = weighted(coe)
        for k, s in SCENARIOS.items():
            ev, tvshare, rows, stub, oe_t = operating_value(s["R0"], s["margin"], s["tax"], s["growth"], coe, detail=True)
            v, vd, vc, ev_, eq = vals[k]
            nopat0 = s["R0"] * s["margin"] * (1 - s["tax"])
            print(f"== {k}（p={s['p']}）==")
            print(f"  正常化 2026：收入 {s['R0']:.1f}，核心经营利润率 {s['margin']:.0%}，税率 {s['tax']:.0%}，经营净利 {nopat0:.2f}，"
                  f"含净利息归母 {nopat0 + NET_INTEREST_AT:.2f}")
            for (yr, g, Rn, nopat, reinv, oe) in rows[:5]:
                print(f"  {yr}: 收入增速 {g:.1%} 收入 {Rn:.2f} 经营净利 {nopat:.2f} 再投资 {reinv:.2f} 所有者收益 {oe:.2f} 再投资率 {reinv/nopat:.0%}")
            oes = [2 * stub] + [r[5] for r in rows[:5]]
            print(f"  所有者收益增速 2027-2031：{', '.join(f'{oes[i+1]/oes[i]-1:.1%}' for i in range(5))}"
                  f"（2026 正常化所有者收益 {oes[0]:.2f}）；2027-2031 平均再投资率 "
                  f"{sum(r[4] for r in rows[:5])/sum(r[3] for r in rows[:5]):.0%}")
            print(f"  2032-2036 增速 {', '.join(f'{r[1]:.1%}' for r in rows[5:])}；终值年所有者收益 {oe_t:.2f}")
            print(f"  经营价值 {ev:.1f}（含 2026H2 存根 {stub:.2f}，终值占 {tvshare:.0%}）；股权价值 {eq:.1f}")
            print(f"  每股：债务法 {vd:.2f}，全部转股法 {vc:.2f} → 取低 {v:.2f}")
        print()
        print(f"加权 V（9%）= {vw:.2f} 元；P/V = {PRICE/vw:.2f}")
    v8, _ = weighted(0.08)
    v10, _ = weighted(0.10)
    print(f"股权成本 8%：加权 V = {v8:.2f}（P/V {PRICE/v8:.2f}）；10%：加权 V = {v10:.2f}（P/V {PRICE/v10:.2f}）")
    irr = implied_irr()
    print(f"现价隐含回报（基准情景所有者收益流）= {irr:.2%}")
    g10, gp, tev = reverse_dcf()
    print(f"反向 DCF：现价隐含经营价值 {tev:.1f} 亿；隐含 10 年收入（≈所有者收益）复合增速 {g10:.1%} 后转 2.5% 永续；"
          f"或隐含永续增速 {gp:.2%}")
    nm = SCENARIOS['base']
    print(f"基准增量回报 = {nm['margin']*(1-nm['tax'])/CAP_INT:.0%}；再投资率 = 再投资/经营净利（见逐年行）")
    print()
    print("== 证伪触发后的 V（9%）==")
    # F1：2026 年报收入 < 16 亿或扣非 < 5.3 亿 → 基准降为熊市概率加大（熊 0.5/基 0.4/牛 0.1）
    vals = scenario_values(0.09)
    f1 = 0.5 * vals['bear'][0] + 0.4 * vals['base'][0] + 0.1 * vals['bull'][0]
    print(f"F1 收入/扣非不达标：{f1:.2f}")
    # F2：联讯仪器跌破 800 元（折后税后价值按比例下降）
    lx_net_800 = (LX_SHARES * 800 * 0.9) - TAX_GAIN * (LX_SHARES * 800 * 0.9 - LX_COST)
    f2 = vw - (LX_NET - lx_net_800) / SHARES
    print(f"F2 联讯仪器 ≤ 800 元：{f2:.2f}")
    # F3：SoC 放量（上行证伪）→ 牛市成为基准（熊 0.1/基 0.4/牛 0.5）
    f3 = 0.1 * vals['bear'][0] + 0.4 * vals['base'][0] + 0.5 * vals['bull'][0]
    print(f"F3 SoC 放量、2027 收入 ≥ 30 亿且核心利润率 ≥ 38%：{f3:.2f}")
    # F4：毛利率连续两季 < 70%（价格竞争）→ 熊 0.5/基 0.5/牛 0
    f4 = 0.5 * vals['bear'][0] + 0.5 * vals['base'][0]
    print(f"F4 毛利率连续两季 < 70%：{f4:.2f}")
