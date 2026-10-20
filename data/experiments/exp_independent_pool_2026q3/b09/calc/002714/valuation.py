#!/usr/bin/env python3
"""牧原股份（002714）独立估值：有杠杆口径所有者收益 DCF（OI-291 b09，价格日 2026-10-20）。

运行：python3 valuation.py   （仅用标准库，输入全部写在本脚本内）

口径要点
- 单位：金额亿元，股数亿股，价格与 V 元/股，猪价与成本元/公斤（活重）。
- 资产负债表取 2026 中报（2026-06-30）；2026H2 用 7-9 月销售简报与预测估计，作为估值起点的短期现金流。
- 正常化：周期平均“全口径税前利息前利润/公斤”（含屠宰、仔猪、补助、营业外与减值，按历史折旧水平）
  × 正常化出栏重量；所有者收益 = (利润/公斤 + 已含在利润里的固定资产折旧/公斤 1.50) × 公斤数
  − 维持与扩张资本开支 − 营运资本 − 历史工程设备欠款的超额偿付。
- 框架规定：经调整净现金为负 → 有杠杆口径（净负债按现规模滚动，扣其利息的永续现值）为主，
  无杠杆口径（全额扣净负债）并列；可转债逐情景按“债务全额扣除”与“全部转股”取低。
"""
from datetime import date

# ---------------------------------------------------------------- 市场与股本
VAL_DATE = date(2026, 10, 20)
PRICE_A = 40.78                      # A 股收盘（腾讯日线，brief.md）
PRICE_H_HKD = 35.90                  # H 股 02714 收盘（Yahoo 图表接口 2026-10-20）
HKDCNY = 0.8526                      # 港元兑人民币（Yahoo HKDCNY=X，2026-10-20）
SHARES_A = 54.62773044               # A 股 5,462,773,044 股（2026Q3 转股公告第 6 页）
SHARES_H = 3.10223100                # H 股 310,223,100 股（同上）
SHARES = 57.7300                     # 总股本（brief：含回购专户股份）
TREASURY_A = 0.69586523              # A 股回购专户 69,586,523 股（拟用于持股计划，非注销）

# ---------------------------------------------------------------- 可转债（牧原转债 127045）
CB_FACE = 95.429474                  # 2026-09-30 剩余面值（2026Q3 转股公告第 5 页）
CB_CONV_PRICE = 43.32                # 现行转股价（2026-05-27 起）
CB_CARRYING = 99.345                 # 2026-06-30 负债成分摊余成本（含应计利息，中报第 140 页），作敏感性
CB_SHARES = CB_FACE / CB_CONV_PRICE  # 全部转股新增股数

# ---------------------------------------------------------------- 资产负债表（2026-06-30，中报）
CASH = 165.466                       # 货币资金（第 20 页）
TRADING_FA = 10.054                  # 交易性金融资产（券商理财 10 亿，第 43 页）
RESTRICTED = 29.174                  # 受限货币资金（第 116、134 页）
RESERVE = 25.0                       # 经营备付，约 TTM 营收 1,270.9 的 2%
DEBT_ITEMS = {                       # 有息负债与类债务
    "短期借款": 472.523,
    "长期借款": 46.431,
    "一年内到期的非流动负债": 95.800,  # 长期借款 51.98、应付债券 16.68、售后回租 7.22、租赁 19.91（第 138 页）
    "应付债券（含可转债）": 112.968,
    "租赁负债": 20.299,
    "短期应付债券（其他流动负债）": 13.049,   # 第 138 页
    "长期应付款（售后回租）": 3.214,          # 第 141 页
    "反向保理（其他应付款）": 9.376,          # 第 136 页
}
DEBT_EX_CB = sum(DEBT_ITEMS.values()) - CB_CARRYING
NET_CASH_ADJ = CASH + TRADING_FA - RESTRICTED - RESERVE - DEBT_EX_CB   # 无杠杆口径经调整净现金
NONOP = 0.663 + 0.942                # 其他权益工具投资（农信社）+ 投资性房地产；联营公司按经营性不计

# 有息负债实际平均利率（剔除可转债）：2026H1 借款债券利息 9.3605 + 租赁及长期应付款利息 0.9429（第 147 页）
# 减可转债当期计息 0.7746 与折价摊销 1.0359（第 140 页），年化后除以期初期末平均有息负债（不含反向保理）
INT_EX_CB_ANNUAL = (9.3605 + 0.9429 - 0.7746 - 1.0359) * 2
DEBT_EX_CB_BEGIN = 411.554 + 77.334 + 74.856 + 116.951 + 21.793 + 3.034 + 6.765 - 97.536   # 2025-12-31
DEBT_EX_CB_END = DEBT_EX_CB - 9.376
RATE = INT_EX_CB_ANNUAL / ((DEBT_EX_CB_BEGIN + DEBT_EX_CB_END) / 2)
ANNUAL_INTEREST = -NET_CASH_ADJ * RATE   # 农业所得免税，税后利息 = 税前利息

# ---------------------------------------------------------------- 2026H2 短期现金流（估计）
# 7-9 月商品猪：销量 666.1/703.0/642.3 万头，收入 88.97/92.54/85.20 亿，均价 10.64/10.30/10.36（9 月销售简报）
Q3_REV = 88.97 + 92.54 + 85.20
Q3_KG = 88.97 / 10.64 + 92.54 / 10.30 + 85.20 / 10.36        # 亿公斤
Q3_PRICE = Q3_REV / Q3_KG
Q4_KG = 2000 * 1.27 / 100                                    # 约 2,000 万头 × 127 公斤 → 亿公斤
OTHER_Q = 3.5                       # 屠宰、仔猪等非商品猪项目（2026Q1/Q2 倒算约 +3.5～3.9 亿/季）
INT_Q = 5.15                        # 季度利息支出（含可转债，2026Q1/Q2 为 5.11/5.20）
DEP_H2 = 75.9                       # 固定资产折旧 H2（H1 实际 75.89，第 128 页）
CAPEX_H2 = 35.0                     # 2026 全年资本开支控制在 100 亿内，H1 已付现 65.2
STUB = {  # (Q3 完全成本, Q4 均价, Q4 完全成本)，完全成本含财务费用
    "bear": (11.50, 9.90, 11.20),
    "base": (11.40, 10.36, 11.10),
    "bull": (11.30, 10.80, 11.00),
}

# ---------------------------------------------------------------- 正常化与情景
DEP_PER_KG = 1.50                   # 历史正常化窗口里已含在利润中的固定资产折旧（元/公斤）
WC = 3.0                            # 名义增长带来的营运资本占用（亿/年）
YEARS = [2027, 2028, 2029, 2030, 2031]
# 终值维持资本开支依据：固定资产原值 1,678 亿（房屋 70.5%、机器 25.4%、其他 4.1%，中报第 128 页）。
# 房屋 20 年、机器 10 年、其他 7 年全额重置 ≈ 112 亿/年（熊 110）；房屋 25 年 ≈ 100 亿，
# 扣除母猪调减后约两成闲置产能不再重置 ≈ 80 亿（牛）；基准 90。管理层口径 60-70 亿为近年刚性维修更新。
SCEN = {
    # spread：周期平均全口径税前利息前利润（元/公斤）；heads 万头；w 公斤/头
    "bear": dict(p=0.25, spread=0.75, heads=7000, w=122, capex=[85, 85, 85, 85, 85], capex_t=110,
                 legacy=[15, 25, 20], g=0.010),
    "base": dict(p=0.50, spread=1.35, heads=7500, w=125, capex=[75, 75, 80, 85, 85], capex_t=90,
                 legacy=[10, 20, 20], g=0.015),
    "bull": dict(p=0.25, spread=1.95, heads=8000, w=125, capex=[70, 70, 75, 80, 80], capex_t=80,
                 legacy=[10, 15, 15], g=0.020),
}
NP_INTEREST_RUN = (10.3034 - 0.456) * 2   # 2026 年化净利息（含可转债计息）≈19.7，用于“正常化归母净利”


def yfrac(d):
    return (d - VAL_DATE).days / 365.25


def stub_oe(name):
    """2026H2 税前利息前所有者收益（含历史欠款超额偿付第一段）。"""
    c3, p4, c4 = STUB[name]
    np_q3 = Q3_KG * (Q3_PRICE - c3) + OTHER_Q
    np_q4 = Q4_KG * (p4 - c4) + OTHER_Q
    pre_int = np_q3 + np_q4 + 2 * INT_Q - 2 * 0.23   # 加回利息支出、扣利息收入
    oe = pre_int + DEP_H2 - CAPEX_H2 - SCEN[name]["legacy"][0]
    return oe, np_q3, np_q4


def oe_path(s, spread=None, kg_mult=1.0, capex_add=0.0):
    spread = s["spread"] if spread is None else spread
    kg = s["heads"] * s["w"] / 1e4 * kg_mult           # 亿公斤
    margin = (spread + DEP_PER_KG) * kg                # 现金口径经营利润（税前利息前，扣维持资本开支前）
    legacy = s["legacy"][1:] + [0, 0, 0]
    path = []
    for i, y in enumerate(YEARS):
        infl = (1 + s["g"]) ** i                       # 2028 起名义价格与成本同步上涨
        path.append(margin * infl - (s["capex"][i] + capex_add) * infl - WC - legacy[i])
    oe_t = (margin - s["capex_t"] - capex_add) * (1 + s["g"]) ** len(YEARS) - WC
    return path, oe_t, kg, margin


def equity(name, r, spread=None, kg_mult=1.0, capex_add=0.0, g=None, extra_debt=0.0):
    s = SCEN[name]
    g = s["g"] if g is None else g
    path, oe_t, kg, _ = oe_path(s, spread, kg_mult, capex_add)
    pv = stub_oe(name)[0]
    for y, cf in zip(YEARS, path):
        pv += cf / (1 + r) ** yfrac(date(y, 7, 1))
    t32 = yfrac(date(2032, 7, 1))
    pv_tv = oe_t / (r - g) / (1 + r) ** (t32 - 1)
    op_value = pv + pv_tv
    nd = -NET_CASH_ADJ + extra_debt
    lev = op_value - nd * RATE / r + NONOP
    unlev = op_value - nd + NONOP
    return dict(op=op_value, tv=pv_tv, lev=lev, unlev=unlev, path=path, oe_t=oe_t, kg=kg)


def per_share(eq, shares=SHARES, cb_debt=CB_FACE, conv_price=CB_CONV_PRICE):
    v_debt = (eq - cb_debt) / shares
    v_conv = eq / (shares + CB_FACE / conv_price)
    return min(v_debt, v_conv), v_debt, v_conv


def weighted(r, probs=None, spread_shift=0.0, conv_price=CB_CONV_PRICE, **kw):
    """三情景加权 V（有杠杆）；spread_shift 平移三个情景的利润/公斤，其余参数传给 equity()。"""
    probs = probs or {k: SCEN[k]["p"] for k in SCEN}
    out = {}
    for k in SCEN:
        extra = dict(kw)
        if spread_shift:
            extra["spread"] = SCEN[k]["spread"] + spread_shift
        e = equity(k, r, **extra)
        out[k] = per_share(e["lev"], conv_price=conv_price)[0]
    return sum(probs[k] * out[k] for k in SCEN), out


def stub_base_2026(name):
    """2026 年所有者收益参照基数（正常化利润、全年资本开支付现 100），只用于计算 2027 增速。"""
    s = SCEN[name]
    kg = s["heads"] * s["w"] / 1e4
    return (s["spread"] + DEP_PER_KG) * kg - 100.0 - WC


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main():
    r = 0.09
    print("== 股本、负债与利率 ==")
    mcap_a = PRICE_A * SHARES
    mcap_mix = PRICE_A * SHARES_A + PRICE_H_HKD * HKDCNY * SHARES_H
    print(f"A 价×总股本 {mcap_a:,.1f}；A、H 各按本地价 {mcap_mix:,.1f}（H 股 {PRICE_H_HKD} 港元 ≈ {PRICE_H_HKD*HKDCNY:.2f} 元，"
          f"较 A 股折价 {1-PRICE_H_HKD*HKDCNY/PRICE_A:.1%}）")
    print(f"有息负债与类债务（剔除可转债）{DEBT_EX_CB:.2f}；经调整净现金 {NET_CASH_ADJ:.2f}；"
          f"实际平均利率 {RATE:.2%}；年利息 {ANNUAL_INTEREST:.2f}；利息永续现值 {ANNUAL_INTEREST/r:.1f}")
    print(f"可转债面值 {CB_FACE:.2f}，转股价 {CB_CONV_PRICE}，转股股数 {CB_SHARES:.4f} 亿股")

    print("\n== 2026H2 估计 ==")
    print(f"Q3 商品猪 {Q3_KG:.2f} 亿公斤，均价 {Q3_PRICE:.2f} 元/公斤")
    for k in SCEN:
        oe, q3, q4 = stub_oe(k)
        print(f"{k}: Q3 归母净利 {q3:.1f}，Q4 {q4:.1f}，2026 全年 {-60.78+q3+q4:.1f}；H2 所有者收益（利息前）{oe:.1f}")

    print("\n== 情景（9%，有杠杆口径为主）==")
    res = {}
    for k, s in SCEN.items():
        e = equity(k, r)
        v, vd, vc = per_share(e["lev"])
        vu, vud, vuc = per_share(e["unlev"])
        v_ex = per_share(e["lev"], shares=SHARES - TREASURY_A)[0]
        res[k] = dict(v=v, vu=vu, v_ex=v_ex, e=e)
        np_norm = s["spread"] * e["kg"] - NP_INTEREST_RUN
        g_path = [e["path"][0] / stub_base_2026(k) - 1] + [e["path"][i] / e["path"][i-1] - 1 for i in range(1, 5)]
        print(f"{k}: p={s['p']:.2f} 利润 {s['spread']:.2f} 元/kg × {e['kg']:.2f} 亿kg；"
              f"2026 正常化归母净利 {np_norm:.1f}；OE 2027-31 " + "/".join(f"{x:.1f}" for x in e["path"]) +
              f"，终值年 {e['oe_t']:.1f}，g={s['g']:.1%}；终值占经营价值 {e['tv']/e['op']:.0%}")
        print(f"     OE 增速 2027-31: " + "/".join(f"{x:+.1%}" for x in g_path))
        print(f"     有杠杆：股权 {e['lev']:,.1f} → 债务法 {vd:.2f}、转股法 {vc:.2f} → V {v:.2f}；"
              f"剔除回购专户 {v_ex:.2f}")
        print(f"     无杠杆：股权 {e['unlev']:,.1f} → 债务法 {vud:.2f}、转股法 {vuc:.2f} → V {vu:.2f}")
    vw = sum(SCEN[k]["p"] * res[k]["v"] for k in SCEN)
    vwu = sum(SCEN[k]["p"] * res[k]["vu"] for k in SCEN)
    vwx = sum(SCEN[k]["p"] * res[k]["v_ex"] for k in SCEN)
    print(f"\n加权 V（有杠杆）{vw:.2f}，P/V {PRICE_A/vw:.3f}；剔除回购专户 V {vwx:.2f}，P/V {PRICE_A/vwx:.3f}")
    print(f"加权 V（无杠杆）{vwu:.2f}，P/V {PRICE_A/vwu:.3f}")
    for lab, pv_ in [("≤0.75 明显低估", 0.75), ("0.90 温和低估上沿", 0.90), ("1.10 大致合理上沿", 1.10)]:
        print(f"  V 不变时 {lab} 对应价格 {vw*pv_:.2f}")

    print("\n== 股权成本敏感性（有杠杆，利息永续现值同用该折现率）==")
    for rr in (0.08, 0.10):
        v_rr, parts = weighted(rr)
        print(f"r={rr:.0%}: 加权 V {v_rr:.2f}（熊 {parts['bear']:.2f} / 基 {parts['base']:.2f} / 牛 {parts['bull']:.2f}）")

    print("\n== 隐含回报与反向 DCF（基准情景，有杠杆）==")
    irr = solve(lambda x: per_share(equity("base", x)["lev"])[0], 0.03, 0.30, PRICE_A)
    print(f"现价隐含回报（基准现金流，含终值与净负债利息）{irr:.2%}")
    g_imp = solve(lambda x: per_share(equity("base", r, g=x)["lev"])[0], -0.05, 0.085, PRICE_A)
    s_imp = solve(lambda x: per_share(equity("base", r, spread=x)["lev"])[0], 0.0, 4.0, PRICE_A)
    print(f"9% 下现价隐含终值增速 {g_imp:.2%}；隐含周期平均全口径利润 {s_imp:.2f} 元/公斤（基准 1.35）")
    s_imp_u = solve(lambda x: per_share(equity("base", r, spread=x)["unlev"])[0], 0.0, 4.0, PRICE_A)
    print(f"无杠杆口径隐含周期平均利润 {s_imp_u:.2f} 元/公斤")

    v_cb_carry = sum(SCEN[k]["p"] * per_share(res[k]["e"]["lev"], cb_debt=CB_CARRYING)[0] for k in SCEN)
    print(f"可转债债务法改用 6/30 摊余成本 {CB_CARRYING}（隐含到期赎回溢价）时加权 V {v_cb_carry:.2f}")

    print("\n== 交叉验证 ==")
    dps_ttm = 0.4270
    print(f"过去 12 个月股息率 {dps_ttm/PRICE_A:.2%}；2025 年 A 股回购 30.01 亿（2024-10～2025-08）约占现市值 "
          f"{30.01/mcap_a:.1%}；H 股回购方案 3-5 亿港元约 {3*HKDCNY/mcap_a:.2%}～{5*HKDCNY/mcap_a:.2%}")
    e_b = res["base"]["e"]
    print(f"PB {mcap_a/801.87:.2f}（归母权益 801.87）；基准正常化归母净利对应 PE "
          f"{mcap_a/(1.35*e_b['kg']-NP_INTEREST_RUN):.1f}；基准 2027 OE（扣利息）收益率 "
          f"{(e_b['path'][0]-ANNUAL_INTEREST)/mcap_a:.1%}")
    ev = mcap_a - NET_CASH_ADJ + CB_FACE
    print(f"EV {ev:,.0f}；EV/正常化 EBIT {ev/(1.35*e_b['kg']):.1f}；EV/2028 年所有者收益 {ev/e_b['path'][1]:.1f}；"
          f"EV/2027 年出栏 {ev/7500*1e4:,.0f} 元/头")

    print("\n== 证伪条件触发后的加权 V ==")
    f = {
        "F1 2027H1 完全成本未降到 11.3 以下（利润 −0.25 元/kg）": weighted(r, spread_shift=-0.25),
        "F2 2027 商品猪均价 <12.0 且能繁 >3,750 万（概率改 0.5/0.4/0.1）": weighted(r, probs={"bear": .5, "base": .4, "bull": .1}),
        "F3 2027 出栏 <7,000 万头（公斤数 −7%）": weighted(r, kg_mult=0.93),
        "F4 2027 资本开支 >110 亿（每年及终值 +20）": weighted(r, capex_add=20.0),
        "F5 经调整净负债升至 650 亿": weighted(r, extra_debt=650 + NET_CASH_ADJ),
        "陷阱检查：转股价下修至 35 元": weighted(r, conv_price=35.0),
    }
    for k, (v_f, _) in f.items():
        print(f"{k}: {v_f:.2f}")


if __name__ == "__main__":
    main()
