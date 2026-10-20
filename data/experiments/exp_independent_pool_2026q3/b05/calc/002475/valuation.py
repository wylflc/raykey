#!/usr/bin/env python3
"""立讯精密（002475）独立估值（OI-291 b05，价格日 2026-10-19）。

金额单位亿元，每股价值元/股。输入全部写在脚本内，`python3 valuation.py` 复现正文与 json 的全部 V。

口径：
- 归母所有者收益 DCF（股权成本 9%，敏感性 8%／10%），估值时点按 2026 年末近似，2027 年为第 1 年。
- 分两块：合并口径的自营业务（剔除权益法联营投资收益，扣少数股东）＋权益法联营企业（单列，按无控制、几乎不分红折价）。
- 经调整净现金（不含立讯转债）为正，按无杠杆口径全额扣除有息负债；另打印有杠杆口径作对照（不采用，原因见正文）。
- 立讯转债逐情景取低：债务法扣到期兑付 108 元/张，转股法加 29.80 亿元面值÷55.45 元的股数、不扣转债。
"""

PRICE = 46.20                 # A 股收盘，2026-10-19
SHARES = 77.432209            # 亿股，A 73.472062 + H 3.960147（2026-10-14 公告股本，含回购专户）
BUYBACK = 0.17665380          # 亿股，回购专户（用于股权激励，未公告注销）
CB_FACE = 29.803635           # 亿元，立讯转债 2026-09-30 未转股面值
CB_REDEEM = 1.08              # 到期兑付 108 元/张（含最后一期利息），2026-11-02 到期
CB_CONV_PRICE = 55.45         # 元/股，2026-10-22 起

# ---------- 经调整净现金（2026-06-30 资产负债表 + 期后已发生现金事项）----------
cash_like = {
    "货币资金": 718.12,
    "减：受限保证金": -7.72,
    "交易性金融资产（远汇及理财）": 35.42,
    "衍生金融资产": 0.67,
    "一年内到期的定期存款": 97.67,
    "其他流动资产-大额存单": 293.96,
    "其他非流动资产-大额存单及定期存款": 210.57,
}
debt_like = {
    "短期借款": 935.69,
    "长期借款": 245.43,
    "一年内到期的长期借款": 61.69,
    "一年内到期应付债券中的宣德可转债": 4.21,
    "一年内到期的长期应付款": 0.40,
    "一年内到期的租赁负债": 6.43,
    "应付债券（中票、科创债）": 64.26,
    "其他流动负债-短期应付债券": 80.59,
    "其他流动负债-应付短期票券": 0.23,
    "租赁负债": 22.76,
    "交易性金融负债+衍生金融负债": 1.99,
    "未终止确认的票据": 1.13,
    "设定受益计划净负债及其他长期福利": 7.14,
}
post_bs = {
    "H 股全球发售净额（396,014,700 股×63.28 港元，扣约 2.3% 费用，按 0.868 折人民币）": 212.5,
    "三季度股票期权行权款（约 2,800 万股，估计）": 7.5,
    "减：应付股利（2025 年末期股息，7 月已付）": -10.79,
    "减：2026 年中期股息（10-22 派发）": -8.49,
}
OPER_RESERVE_RATIO = 0.025    # 经营备付：2026 年收入的 2.5%
REV_2026_FOR_RESERVE = 4000.0

cash_total = sum(cash_like.values())
debt_total = sum(debt_like.values())
post_total = sum(post_bs.values())
oper_reserve = OPER_RESERVE_RATIO * REV_2026_FOR_RESERVE
NET_CASH_ADJ = cash_total - debt_total + post_total - oper_reserve

non_operating = {
    "其他权益工具投资+其他非流动金融资产": 8.51,
    "投资性房地产": 0.93,
    "预付股权收购款（含京西等）": 15.19,
    "印度闻泰资产包（仲裁追偿）": 1.39,
}
NON_OP = sum(non_operating.values())

# ---------- 情景 ----------
SCEN = {
    "bear": dict(p=0.25, rev=3850.0, core_margin=0.034, subsidy=0.001, tax=0.15, minority=0.115,
                 net_fin=-3.0, growth=[0.04, 0.04, 0.035, 0.03, 0.03], g_t=0.02, ronic=0.10,
                 assoc=35.0, assoc_g=0.02, assoc_roe=0.25, assoc_disc=0.40),
    "base": dict(p=0.50, rev=4000.0, core_margin=0.039, subsidy=0.002, tax=0.13, minority=0.115,
                 net_fin=0.0, growth=[0.10, 0.09, 0.08, 0.07, 0.06], g_t=0.025, ronic=0.15,
                 assoc=50.0, assoc_g=0.025, assoc_roe=0.30, assoc_disc=0.30),
    "bull": dict(p=0.25, rev=4100.0, core_margin=0.044, subsidy=0.0025, tax=0.12, minority=0.115,
                 net_fin=3.0, growth=[0.15, 0.13, 0.11, 0.09, 0.08], g_t=0.025, ronic=0.20,
                 assoc=62.0, assoc_g=0.03, assoc_roe=0.35, assoc_disc=0.20),
}


def core_parent_np(s):
    """2026 正常化自营归母净利（不含联营、不含净财务项）。"""
    op = s["rev"] * (s["core_margin"] + s["subsidy"])
    return op * (1 - s["tax"]) * (1 - s["minority"])


def normalized_np(s):
    """2026 正常化归母净利：自营 + 联营 + 正常化净财务（税后、扣少数）。"""
    fin = s["net_fin"] * (1 - s["tax"]) * (1 - s["minority"])
    return core_parent_np(s) + s["assoc"] + fin


def growth_path(s):
    """2027-2036 逐年增速：前 5 年按情景，后 5 年线性降到终值增速。"""
    g = list(s["growth"])
    g5, gt = g[-1], s["g_t"]
    for k in range(1, 6):
        g.append(g5 + (gt - g5) * k / 5)
    return g  # 10 个


def pv_core(s, r, growth=None):
    g = growth if growth is not None else growth_path(s)
    npv, pv = core_parent_np(s), 0.0
    nxt = g[1:] + [s["g_t"]]
    rows = []
    for k in range(10):
        npv *= 1 + g[k]
        rr = nxt[k] / s["ronic"]
        oe = npv * (1 - rr)
        pv += oe / (1 + r) ** (k + 1)
        rows.append((2027 + k, g[k], npv, rr, oe))
    gt = s["g_t"]
    tv = npv * (1 + gt) * (1 - gt / s["ronic"]) / (r - gt)
    pv_tv = tv / (1 + r) ** 10
    return pv + pv_tv, pv_tv, rows


def v_assoc(s, r):
    a, g = s["assoc"], s["assoc_g"]
    return a * (1 + g) * (1 - g / s["assoc_roe"]) / (r - g) * (1 - s["assoc_disc"])


def equity_pre_cb(s, r, growth=None):
    core, pv_tv, _ = pv_core(s, r, growth)
    return core + v_assoc(s, r) + NET_CASH_ADJ + NON_OP, core, pv_tv


def per_share(eq, shares=SHARES):
    v_debt = (eq - CB_FACE * CB_REDEEM) / shares
    v_conv = eq / (shares + CB_FACE / CB_CONV_PRICE)
    return min(v_debt, v_conv), v_debt, v_conv


def v_scen(s, r, growth=None, shares=SHARES):
    eq, _, _ = equity_pre_cb(s, r, growth)
    return per_share(eq, shares)[0]


def weighted(r, shares=SHARES):
    return sum(s["p"] * v_scen(s, r, shares=shares) for s in SCEN.values())


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


def levered_reference(s, r, rate=0.0185):
    """有杠杆口径对照（不采用）：有息负债按现规模滚动只付税后利息，现金等调整项同无杠杆口径。"""
    core, _, _ = pv_core(s, r)
    pv_int = debt_total * rate * (1 - s["tax"]) / r
    eq = core + v_assoc(s, r) - pv_int + (cash_total + post_total - oper_reserve) + NON_OP
    return per_share(eq)[0]


def main():
    print("=== 经调整净现金（亿元）===")
    print(f"现金类 {cash_total:.2f}；有息负债及类债务（不含立讯转债）{debt_total:.2f}；期后现金事项 {post_total:.2f}；"
          f"经营备付 {oper_reserve:.2f}")
    print(f"net_cash_adj = {NET_CASH_ADJ:.2f}；非经营资产 {NON_OP:.2f}；立讯转债兑付 {CB_FACE * CB_REDEEM:.2f}；"
          f"转股新增 {CB_FACE / CB_CONV_PRICE:.4f} 亿股")
    print()
    for name, s in SCEN.items():
        eq, core, pv_tv = equity_pre_cb(s, 0.09)
        v, vd, vc = per_share(eq)
        va = v_assoc(s, 0.09)
        print(f"=== {name}（p={s['p']}）===")
        print(f"2026 正常化：自营归母 {core_parent_np(s):.2f} + 联营 {s['assoc']:.2f} + 净财务 "
              f"{s['net_fin'] * (1 - s['tax']) * (1 - s['minority']):.2f} = 归母 {normalized_np(s):.2f}")
        _, _, rows = pv_core(s, 0.09)
        for y, g, npv, rr, oe in rows[:5]:
            print(f"  {y}: 增速 {g:.3f} 自营归母 {npv:.2f} 再投资率 {rr:.3f} 所有者收益 {oe:.2f}")
        print(f"  2032-2036 增速 {[round(x, 4) for x in growth_path(s)[5:]]}，终值增速 {s['g_t']}，增量回报 {s['ronic']}")
        print(f"  自营现值 {core:.1f}（终值现值 {pv_tv:.1f}，占自营 {pv_tv / core:.1%}）；联营 {va:.1f}；"
              f"净现金 {NET_CASH_ADJ:.1f}；非经营 {NON_OP:.1f}；股权（转债前）{eq:.1f}")
        print(f"  每股：债务法 {vd:.2f}，转股法 {vc:.2f}，取低 V = {v:.2f}；"
              f"剔除回购专户 {v_scen(s, 0.09, shares=SHARES - BUYBACK):.2f}")
        print(f"  有杠杆口径对照（不采用）{levered_reference(s, 0.09):.2f}")
        print()
    vw = weighted(0.09)
    print(f"加权 V = {vw:.2f}；P/V = {PRICE / vw:.3f}")
    vw_ex = weighted(0.09, shares=SHARES - BUYBACK)
    print(f"剔除回购专户股份：加权 V = {vw_ex:.2f}；P/V = {PRICE / vw_ex:.3f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}（P/V {PRICE / weighted(0.08):.3f}）；"
          f"10%：加权 V = {weighted(0.10):.2f}（P/V {PRICE / weighted(0.10):.3f}）")
    for name in SCEN:
        print(f"  {name}: 8% {v_scen(SCEN[name], 0.08):.2f}  9% {v_scen(SCEN[name], 0.09):.2f}  10% {v_scen(SCEN[name], 0.10):.2f}")

    base = SCEN["base"]
    irr = solve(lambda r: v_scen(base, r), 0.04, 0.12, PRICE)
    print(f"现价隐含回报（基准情景现金流）= {irr:.4f}")

    # 反向 DCF：基准其他假设不变，自营归母 2027-2036 统一增速 g，使 V = 现价
    g10 = solve(lambda g: v_scen(base, 0.09, growth=[g] * 10), -0.05, 0.40, PRICE)
    print(f"反向 DCF：自营 10 年统一增速 {g10:.4f}（增量回报 15%、终值 2.5% 不变）")
    # 再加：若增量回报提高到 25%，需要的 10 年增速
    hi = dict(base, ronic=0.25)
    g10b = solve(lambda g: v_scen(hi, 0.09, growth=[g] * 10), -0.05, 0.40, PRICE)
    print(f"反向 DCF：增量回报 25% 时 10 年统一增速 {g10b:.4f}")
    # 单阶段：整体归母（含联营，不折价）按增量回报 15% 的永续增速
    tot = normalized_np(base)
    adj = NET_CASH_ADJ + NON_OP - CB_FACE * CB_REDEEM
    target_eq = PRICE * SHARES - adj
    gp = solve(lambda g: tot * (1 + g) * (1 - g / 0.15) / (0.09 - g), 0.0, 0.0899, target_eq)
    print(f"反向 DCF：单阶段永续增速 {gp:.4f}（2026 正常化归母 {tot:.1f}，增量回报 15%，联营不折价）")

    # 证伪情景（正文与 json falsifiers 用）：替换基准情景后的加权 V
    fz = {
        "上行：自营利润率 4.3%+补助 0.2%，增速 14/12/10/8/7%": dict(base, core_margin=0.043,
                                                         growth=[0.14, 0.12, 0.10, 0.08, 0.07]),
        "联营投资收益正常化降至 30 亿": dict(base, assoc=30.0),
        "自营利润率 3.4%+补助 0.1%": dict(base, core_margin=0.034, subsidy=0.001),
        "增量回报只有 10%": dict(base, ronic=0.10),
        "增速前 5 年 4/4/3.5/3/3%": dict(base, growth=[0.04, 0.04, 0.035, 0.03, 0.03]),
        "联营折价升到 50%": dict(base, assoc_disc=0.50),
    }
    print()
    for k, s in fz.items():
        vb = v_scen(s, 0.09)
        vw2 = 0.25 * v_scen(SCEN["bear"], 0.09) + 0.5 * vb + 0.25 * v_scen(SCEN["bull"], 0.09)
        print(f"证伪 {k}：基准 V → {vb:.2f}；加权 V（替换基准）→ {vw2:.2f}")
    # 情景加权：熊情景概率升到 50%
    vw_bear = 0.5 * v_scen(SCEN["bear"], 0.09) + 0.4 * v_scen(base, 0.09) + 0.1 * v_scen(SCEN["bull"], 0.09)
    print(f"证伪 熊 50%/基 40%/牛 10%：加权 V → {vw_bear:.2f}")
    print()

    # 交叉验证
    mcap = PRICE * SHARES
    eq_base, core_b, _ = equity_pre_cb(base, 0.09)
    eq_base_after_cb = eq_base - CB_FACE * CB_REDEEM
    book_post_h = 936.07 + 212.5 + 7.5 - 8.49
    ev_core = mcap + CB_FACE * CB_REDEEM - NET_CASH_ADJ - NON_OP - v_assoc(base, 0.09)
    ebit_core = base["rev"] * (base["core_margin"] + base["subsidy"])
    print("=== 交叉验证 ===")
    print(f"市值 {mcap:.1f}；股息率 {0.2990 / PRICE:.2%}，近 12 个月回购 10.0 亿占市值 {10.0 / mcap:.2%}")
    print(f"基准 V 对应 PE（正常化归母 {normalized_np(base):.1f}）{eq_base_after_cb / normalized_np(base):.1f}×；"
          f"现价 PE {mcap / normalized_np(base):.1f}×（正常化）、{mcap / 177.98:.1f}×（TTM 177.98）")
    print(f"H 股后归母权益约 {book_post_h:.1f}：现价 PB {mcap / book_post_h:.2f}×，基准 V 对应 PB {eq_base_after_cb / book_post_h:.2f}×")
    print(f"自营 EV（扣转债、净现金、非经营、联营基准价值）{ev_core:.1f}；自营 EBIT {ebit_core:.1f}；EV/EBIT {ev_core / ebit_core:.1f}×")
    hj = 0.618 * 427.73 * 0.865
    print(f"分部：汇聚科技 61.8% 权益按 9-10 市值 427.73 亿港元×0.865 = {hj:.1f} 亿元，合 {hj / SHARES:.2f} 元/股（上限式加回）；"
          f"全额加回后加权 V ≈ {vw + hj / SHARES:.2f}，P/V {PRICE / (vw + hj / SHARES):.3f}")
    print(f"基准每股拆分：自营 {core_b / SHARES:.2f}，联营 {v_assoc(base, 0.09) / SHARES:.2f}，净现金 {NET_CASH_ADJ / SHARES:.2f}，"
          f"非经营 {NON_OP / SHARES:.2f}，转债 {-CB_FACE * CB_REDEEM / SHARES:.2f}")
    print()
    print("V 不变时各档价格：≤0.75 明显低估 ≤ {:.2f}；0.75–0.90 温和低估 {:.2f}–{:.2f}；0.90–1.10 大致合理 {:.2f}–{:.2f}；"
          ">1.10 偏贵 > {:.2f}".format(0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
