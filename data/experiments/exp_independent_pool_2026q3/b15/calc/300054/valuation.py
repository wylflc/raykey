#!/usr/bin/env python3
"""鼎龙股份（300054）独立估值：所有者收益 DCF（有杠杆口径）+ 可转债逐情景取低 + 反向 DCF。

价格日 2026-10-20，现价 58.09 元；最新定期报告 2026 中报（三季报预约 2026-10-28）。
金额单位亿元，每股价值元/股。全部输入写在本脚本内，出处见正文「来源」。
运行：python3 valuation.py
"""

PRICE = 58.09
SHARES = 9.5473              # 腾讯行情总股本（亿股），含第五期回购专户股份
TREASURY = 0.01385620        # 截至 2026-09-30 回购专户 1,385,620 股（用于维护公司价值，未公告注销）
CB_FACE = 9.095484           # 鼎龙转债 2026-09-30 剩余面值（financing_20261009 第 3 页）
CB_CONV_PRICE = 28.38        # 最新转股价（同上第 1 页）
CB_SHARES = CB_FACE / CB_CONV_PRICE   # 全部转股新增股数（亿股）
TAX = 0.15                   # 主要经营主体高新技术企业 15%（2026H1 实际税率 13.6%）
COE = 0.09
G_TERM = 0.025
VAL_TO_YE = 72 / 365         # 2026-10-20 至 2026-12-31

# ---------- 经调整净现金（2026-06-30，并扣三季度已发生的现金用途） ----------
cash = 13.69                 # 货币资金
trading_fa = 0.72            # 交易性金融资产
cds = 4.7646                 # 其他非流动金融资产中的大额存单（2026H1 附注十一「其他」，第 151 页附近）
restricted = 0.1841          # 受限货币资金（附注二十一）
op_reserve = 2.0             # 经营备付：约 1 个月付现成本
div_payable = 0.0108         # 应付股利
bank_debt = 0.85 + 9.3462 + 4.3659 + 0.4800 + 0.1032   # 短借（剔除已贴现未终止确认票据 1.16）+长借+一年内到期长借+租赁负债
haofei_payable = 6.30 - 4.94 # 皓飞新材股权款未付部分（含 1 亿元业绩条件尾款）
q3_buyback = 0.9697          # 第五期回购截至 9-30 已付（buyback_20261009）
q3_dinghui = 0.2943          # 2026-08 购买鼎汇微电子 0.6538% 少数股权
net_cash_adj = (cash + trading_fa + cds - restricted - op_reserve - div_payable
                - bank_debt - haofei_payable - q3_buyback - q3_dinghui)
DEBT_RATE = 0.023            # 银行借款实际平均利率（2026H1 银行与租赁利息约 0.12 亿/半年，含资本化后按 2.3% 取）

# 非经营资产：其他非流动金融资产中的权益工具 0.69 + 长期股权投资 6.60 按 0.8 折
non_op = 0.6946 + 6.5953 * 0.8

# ---------- 正常化归母净利（报表口径，含净利息、剔除非经常） ----------
NORM_2026 = {"bear": 9.3, "base": 11.0, "bull": 12.2}
# 由报表口径换到经营口径：+ 转债利息（票息+摊销）税后，− 权益法投资收益（投资另作非经营资产）
CB_INT_AT = 0.26 * (1 - TAX)         # 2026H1 转债利息费用 0.13 亿（票息 0.014 + 摊销 0.116）×2
EQ_INCOME = 0.30                     # 权益法投资收益年化（H1 0.14，4 月起含打印终端两家参股）
BANK_INT_NET_AT = (bank_debt * DEBT_RATE - (cash + cds) * 0.012) * (1 - TAX)  # 银行净利息税后（基本为零）

SCEN = {
    # 2027-2031 归母经营净利增速；ROIIC = 增量投入资本回报；p = 概率
    "bear": {"p": 0.25, "g": [0.06, 0.06, 0.05, 0.05, 0.04], "roiic": 0.20},
    "base": {"p": 0.50, "g": [0.22, 0.16, 0.12, 0.10, 0.08], "roiic": 0.35},
    "bull": {"p": 0.25, "g": [0.28, 0.24, 0.19, 0.15, 0.12], "roiic": 0.45},
}
YEARS = [2027, 2028, 2029, 2030, 2031]
FADE_YEARS = 5               # 2032-2036 增速线性降到终值增速


def op_np_2026(name):
    return NORM_2026[name] + CB_INT_AT - EQ_INCOME + BANK_INT_NET_AT


def path(name):
    """返回 [(年份, 经营净利, 增速, 再投资率, 所有者收益)]，含 2032-2036 衰减期。"""
    s = SCEN[name]
    gs = list(s["g"])
    g_last = gs[-1]
    for k in range(1, FADE_YEARS + 1):
        gs.append(g_last + (G_TERM - g_last) * k / FADE_YEARS)
    rows = []
    np_ = op_np_2026(name)
    for i, g in enumerate(gs):
        np_ = np_ * (1 + g)
        g_next = gs[i + 1] if i + 1 < len(gs) else G_TERM
        rr = min(max(g_next / s["roiic"], 0.0), 0.9)
        rows.append((2027 + i, np_, g, rr, np_ * (1 - rr)))
    return rows


def equity_value(name, coe=COE):
    """经营所有者收益现值 − 经调整净负债税后利息现值 + 非经营资产（转债另算）。"""
    s = SCEN[name]
    rows = path(name)
    # 2026 下半年所有者收益（资产负债表日之后、价格日前后发生），按 2027 年再投资率折算
    oe_h2 = 0.5 * op_np_2026(name) * (1 - rows[0][2] / s["roiic"])
    pv = oe_h2 / (1 + coe) ** 0.1
    for i, (y, np_, g, rr, oe) in enumerate(rows):
        t = VAL_TO_YE + i + 0.5
        pv += oe / (1 + coe) ** t
    y, np_, g, rr, oe = rows[-1]
    oe_t1 = np_ * (1 + G_TERM) * (1 - G_TERM / s["roiic"])
    tv = oe_t1 / (coe - G_TERM)
    t_tv = VAL_TO_YE + len(rows)
    pv_tv = tv / (1 + coe) ** t_tv
    pv += pv_tv
    if net_cash_adj < 0:      # 有杠杆口径：净负债按现规模滚动，扣其税后利息现值
        lev = -net_cash_adj * DEBT_RATE * (1 - TAX) / coe
        eq = pv - lev + non_op
    else:
        eq = pv + net_cash_adj + non_op
    return eq, pv_tv, pv


def per_share(name, coe=COE, shares=SHARES):
    eq, pv_tv, pv_op = equity_value(name, coe)
    v_debt = (eq - CB_FACE) / shares                  # 转债按未转股面值全额扣除
    v_conv = eq / (shares + CB_SHARES)                # 全部转股，不扣转债
    return min(v_debt, v_conv), v_debt, v_conv, eq, pv_tv / pv_op


def weighted(coe=COE, shares=SHARES):
    return sum(SCEN[n]["p"] * per_share(n, coe, shares)[0] for n in SCEN)


def unlevered_weighted(coe=COE):
    """无杠杆口径对照：经营所有者收益现值 + 经调整净现金（负值直接扣）+ 非经营资产。"""
    tot = 0.0
    for n in SCEN:
        eq, _, pv = equity_value(n, coe)
        if net_cash_adj < 0:
            eq = pv + net_cash_adj + non_op
        v = min((eq - CB_FACE) / SHARES, eq / (SHARES + CB_SHARES))
        tot += SCEN[n]["p"] * v
    return tot


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    """基准情景所有者收益流（含终值、净负债与非经营资产、转债取低）使现值等于现价的折现率。"""
    return solve(lambda r: per_share("base", r)[0], 0.03, 0.20, PRICE)


def reverse_dcf():
    """(1) 现价隐含 2027-2036 十年统一增速（终值 2.5%，ROIIC 取基准 35%）；(2) 隐含永续增速。"""
    base_np = op_np_2026("base")
    roiic = SCEN["base"]["roiic"]

    def v_uniform(g):
        pv = 0.0
        np_ = base_np
        for i in range(10):
            np_ *= (1 + g)
            g_next = g if i < 9 else G_TERM
            oe = np_ * (1 - min(g_next / roiic, 0.9))
            pv += oe / (1 + COE) ** (VAL_TO_YE + i + 0.5)
        tv = np_ * (1 + G_TERM) * (1 - G_TERM / roiic) / (COE - G_TERM)
        pv += tv / (1 + COE) ** (VAL_TO_YE + 10)
        eq = pv - (-net_cash_adj) * DEBT_RATE * (1 - TAX) / COE + non_op
        return eq / (SHARES + CB_SHARES)

    g10 = solve(v_uniform, 0.0, 0.40, PRICE)

    def v_perp(g):
        oe = base_np * (1 + g) * (1 - min(g / roiic, 0.9))
        eq = oe / (COE - g) - (-net_cash_adj) * DEBT_RATE * (1 - TAX) / COE + non_op
        return eq / (SHARES + CB_SHARES)

    gp = solve(v_perp, 0.0, 0.0899, PRICE)
    return g10, gp


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print(f"经调整净现金（无杠杆口径）= {net_cash_adj:.2f} 亿元；非经营资产 = {non_op:.2f} 亿元")
    print(f"银行有息负债（不含转债）= {bank_debt:.2f}；转债面值 = {CB_FACE:.3f}，全部转股新增 {CB_SHARES:.4f} 亿股")
    print(f"经营口径 2026 归母净利：" + "，".join(f"{n} {op_np_2026(n):.2f}" for n in SCEN))
    print()
    for n in SCEN:
        print(f"[{n}] p={SCEN[n]['p']:.2f} ROIIC={SCEN[n]['roiic']:.0%}")
        for (y, np_, g, rr, oe) in path(n)[:5]:
            print(f"   {y}: 经营净利 {np_:6.2f}  增速 {g:5.1%}  再投资率 {rr:5.1%}  所有者收益 {oe:6.2f}")
        v, vd, vc, eq, tvshare = per_share(n)
        print(f"   股权价值（转债前）{eq:7.1f} 亿；债务法 {vd:6.2f} 元，转股法 {vc:6.2f} 元 → 取低 {v:6.2f} 元；终值占比 {tvshare:.0%}")
    vw = weighted()
    print()
    print(f"概率加权 V = {vw:.2f} 元/股；P/V = {PRICE / vw:.2f}（{band(PRICE / vw)}）")
    vw_ex = weighted(shares=SHARES - TREASURY)
    print(f"剔除回购专户股份后 V = {vw_ex:.2f} 元/股；P/V = {PRICE / vw_ex:.2f}")
    print(f"无杠杆口径对照 V = {unlevered_weighted():.2f} 元/股；P/V = {PRICE / unlevered_weighted():.2f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8% → V = {v8:.2f}；10% → V = {v10:.2f}")
    print(f"现价隐含回报（基准情景）= {implied_irr():.2%}")
    g10, gp = reverse_dcf()
    print(f"反向 DCF：现价隐含 2027-2036 年所有者收益基数的年均增速 {g10:.1%}（之后 2.5%），或隐含永续增速 {gp:.2%}")
    print()
    # 交叉验证
    mcap = PRICE * SHARES
    print(f"市值 {mcap:.1f} 亿；2026E 报表归母 11.7 亿 → PE {mcap / 11.7:.1f}×；正常化基准 {NORM_2026['base']} 亿 → PE {mcap / NORM_2026['base']:.1f}×")
    ebit_2026 = 11.0 / (1 - TAX) + 0.6     # 粗算：归母/（1−税率）+ 少数股东与净利息
    ev = mcap + CB_FACE - net_cash_adj - non_op + 2.70
    print(f"EV ≈ {ev:.1f} 亿；EV/EBIT(2026E≈{ebit_2026:.1f}) ≈ {ev / ebit_2026:.1f}×；PB(归母 56.40) = {mcap / 56.40:.2f}×")
    print(f"股息+回购收益率：0.95 亿股息 + 第五期回购 1～2 亿 → {(0.95 + 1.0) / mcap:.2%}～{(0.95 + 2.0) / mcap:.2%}")
    print()
    print("各档价格（V 不变）：明显低估 ≤ {:.2f}；温和低估 ≤ {:.2f}；大致合理 ≤ {:.2f}".format(0.75 * vw, 0.90 * vw, 1.10 * vw))
    # 证伪触发后的 V：情景 V 不变，按触发后的情景概率重新加权
    vb = {n: per_share(n)[0] for n in SCEN}
    print("情景 V：" + "，".join(f"{n} {vb[n]:.2f}" for n in SCEN))
    FALSIFIERS = {
        "F1 三季报单季扣非归母 < 2.8 亿（2026-10-28）": (0.35, 0.50, 0.15),
        "F2 抛光垫单季收入同比连续两季 < 10% 或半导体材料毛利率 < 65%（2027-08-31 前）": (0.50, 0.40, 0.10),
        "F3 2027 年扣非归母 ≥ 15.5 亿且半导体材料毛利率 ≥ 70%（2028-04-30）": (0.10, 0.45, 0.45),
        "F4 2027 年高端晶圆光刻胶收入 ≥ 3 亿元（2028-04-30）": (0.15, 0.35, 0.50),
        "F5 2027 年扣非归母 < 11 亿（2028-04-30）": (0.60, 0.35, 0.05),
    }
    for k, (pb, pm, pu) in FALSIFIERS.items():
        v = pb * vb["bear"] + pm * vb["base"] + pu * vb["bull"]
        print(f"{k} → V = {v:.2f}，P/V = {PRICE / v:.2f}")
    print()
    # 正文引用的补充敏感性
    print(f"牛情景隐含回报 = {solve(lambda r: per_share('bull', r)[0], 0.03, 0.20, PRICE):.2%}")
    print(f"使加权 V = 现价/1.10 的股权成本 = {solve(lambda r: weighted(r), 0.04, 0.12, PRICE / 1.10):.2%}")
    for roi in (0.30, 0.45, 0.60):
        old = SCEN["base"]["roiic"]
        SCEN["base"]["roiic"] = roi
        print(f"基准 ROIIC = {roi:.0%} 时：基准 V = {per_share('base')[0]:.2f}，加权 V = {weighted():.2f}")
        SCEN["base"]["roiic"] = old
    g0 = list(SCEN["base"]["g"])

    def _vb(k):
        SCEN["base"]["g"] = [x * k for x in g0]
        return per_share("base")[0]

    k = solve(_vb, 1.0, 4.0, PRICE / 1.10)
    SCEN["base"]["g"] = [x * k for x in g0]
    r31 = path("base")[4][1]
    print(f"基准 V 达到现价/1.10 所需增速放大倍数 = {k:.2f}（2027-2031 增速 " +
          "、".join(f"{x * k:.0%}" for x in g0) + f"，2031 年归母经营净利 {r31:.1f} 亿）")
    SCEN["base"]["g"] = g0
