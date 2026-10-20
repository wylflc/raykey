#!/usr/bin/env python3
"""贵州茅台（600519）独立估值：所有者收益 DCF（三情景）+ 反向 DCF + 交叉验证 + 证伪情景。

金额单位：亿元；每股价值：元/股。价格日 2026-10-20，最新定期报告 2026 中报（2026-06-30）。
全部输入写在本脚本内，出处见 b06/companies/600519_贵州茅台.md 的「来源」一节。
运行：python3 valuation.py
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 1331.88                      # 2026-10-20 收盘（腾讯日线）
SHARES = 12.5008                     # 亿股；2026-05-28 注销 2,188,614 股后 1,250,081,601 股，无回购专户股份
VAL_DATE = date(2026, 10, 20)
COE = 0.09

# ---------------------------------------------------------------- 资产负债（2026H1_report 第 25～28 页、第 53、69 页）
FIN_ASSETS = {                       # 现金与金融类资产（合并口径）
    "货币资金": 535.19,
    "拆出资金（存放同业 1,408.16 + 拆出 3.01 − 减值 0.33）": 1410.84,
    "买入返售金融资产": 4.06,
    "一年内到期的非流动资产（财务公司债权投资）": 17.98,
    "发放贷款和垫款（财务公司）": 4.16,
    "债权投资": 11.07,
    "其他债权投资": 24.15,
}
RESTRICTED = 83.59                   # 存放中央银行法定存款准备金（第 69 页）
GROUP_DEPOSITS = 254.26              # 吸收存款及同业存放 = 茅台集团成员单位在财务公司的存款（关联方，类债务，第 19 页）
LEASE_DEBT = 1.87 + 0.57             # 租赁负债 + 一年内到期的非流动负债（无银行借款）
OPERATING_RESERVE = 100.0            # 经营备付：约两个月不含所得税的付现成本
MINORITY_EQUITY = 108.43             # 少数股东权益：销售公司 5% 44.23 + 财务公司 49% 等 64.20（第 27、87 页）
NON_OPERATING = 39.18 + 1.47 + 0.03  # 其他非流动金融资产（私募基金）+ 长期股权投资 + 投资性房地产

GUIZHOU_BANK_DEPOSIT = 88.06         # 关联方存款：公司在贵州银行（控股股东之联营企业）的存款，已含在货币资金内（第 17 页）

# ---------------------------------------------------------------- 利息与少数股东
NET_INTEREST_PRETAX_2026 = 33.9      # 2026E 净利息（H1 实际 17.44 = 15.75 − 0.77 + 2.67 − 0.21；H2 约 16.5）
TAX_RATE = 0.25
PARENT_SHARE_OF_INTEREST = 0.80      # 财务公司 49% 少数股权与销售公司 5% 分走约两成
H1_2026_PARENT_NP = 445.17           # 2026H1_report 第 5 页

# ---------------------------------------------------------------- 三情景
# np26：2026 年正常化归母净利（含净利息，剔除一次性项目）；h2_26：2026H2 归母净利估计（实际现金流用）
# g：2027～2031 年经营所有者收益增速；gT：终值增速；rr：显性期再投资率（净资本开支 + 基酒存货 + 营运资本，占经营归母净利）
# ronic_T：终值期增量回报，终值再投资率 = gT / ronic_T
SCENARIOS = {
    "bear": dict(p=0.25, np26=730.0, h2_26=360.0, g=[-0.03, 0.00, 0.01, 0.02, 0.02], gT=0.020, rr=0.08, ronic_T=0.25,
                 text="批价跌破 1,500，自营价与合同价回吐至 1,499／1,269，茅台酒量价双降约 10%，系列酒再降 15%，毛利率再降 2 个百分点"),
    "base": dict(p=0.50, np26=830.0, h2_26=385.0, g=[0.04, 0.04, 0.04, 0.035, 0.03], gT=0.025, rr=0.08, ronic_T=0.35,
                 text="批价稳在 1,650～1,800，合同价 1,369／i茅台 1,639 维持；2027 年吃满两次提价、投放收紧量略降；之后年提价约 2% 加量 1%～2%"),
    "bull": dict(p=0.25, np26=870.0, h2_26=400.0, g=[0.08, 0.08, 0.06, 0.05, 0.04], gT=0.025, rr=0.09, ronic_T=0.40,
                 text="需求修复、批价回到 1,900 以上，2027～2028 年合同价再上调至约 1,500、i茅台价随批价上移，量年增约 3%"),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def t_years(d):
    return (d - VAL_DATE).days / 365.25


def interest_parent_annual():
    return NET_INTEREST_PRETAX_2026 * (1 - TAX_RATE) * PARENT_SHARE_OF_INTEREST


def net_cash_adj():
    return sum(FIN_ASSETS.values()) - RESTRICTED - GROUP_DEPOSITS - LEASE_DEBT - OPERATING_RESERVE - MINORITY_EQUITY


def scenario_value(s, r=COE, detail=False):
    ip = interest_parent_annual()
    op26 = s["np26"] - ip                                   # 2026 正常化经营归母净利（不含利息）
    oe_h2 = (s["h2_26"] - ip / 2) * (1 - s["rr"])          # 2026H2 所有者收益，按 2026-12-31 折现
    pv = oe_h2 / (1 + r) ** t_years(date(2026, 12, 31))
    op = op26
    rows = []
    for y, g in zip(YEARS, s["g"]):
        op *= 1 + g
        oe = op * (1 - s["rr"])
        df = (1 + r) ** -t_years(date(y, 7, 1))
        pv += oe * df
        rows.append((y, g, op, oe, oe * df))
    oe_T = op * (1 + s["gT"]) * (1 - s["gT"] / s["ronic_T"])
    tv = oe_T / (r - s["gT"])
    pv_tv = tv * (1 + r) ** -t_years(date(YEARS[-1], 7, 1))
    eq = pv + pv_tv + net_cash_adj() + NON_OPERATING
    v = eq / SHARES
    if detail:
        return v, dict(op26=op26, oe26=op26 * (1 - s["rr"]), oe_h2=oe_h2, rows=rows, oe_T=oe_T, tv=tv, pv_tv=pv_tv,
                       pv_explicit=pv, eq=eq, tv_share=pv_tv / eq)
    return v


def weighted(r=COE, probs=None, scen=SCENARIOS):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * scenario_value(scen[k], r) for k in scen)


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
    # 基准情景所有者收益流（含终值、净现金与非经营资产）现值等于现价的折现率
    return solve(lambda r: scenario_value(SCENARIOS["base"], r), 0.05, 0.12, PRICE)


def reverse_dcf():
    s = SCENARIOS["base"]
    ip = interest_parent_annual()
    oe26 = (s["np26"] - ip) * (1 - s["rr"])
    oe_h2 = (s["h2_26"] - ip / 2) * (1 - s["rr"])
    ev_mkt = PRICE * SHARES - net_cash_adj() - NON_OPERATING - oe_h2 / (1 + COE) ** t_years(date(2026, 12, 31))
    t27 = t_years(date(2027, 7, 1))

    def pv_perp(g):   # 从 2027 年起以 OE_2026 × (1+g) 为首年、永续增长 g
        return oe26 * (1 + g) * (1 + COE) ** (1 - t27) / (COE - g)

    g_perp = solve(pv_perp, -0.05, 0.085, ev_mkt)

    def pv_10y(g):    # 2027～2036 年增速 g，之后 2.5% 永续（终值再投资率 2.5%/35%）
        pv, oe = 0.0, oe26
        for k, y in enumerate(range(2027, 2037)):
            oe *= 1 + g
            pv += oe * (1 + COE) ** -t_years(date(y, 7, 1))
        op_T = oe / (1 - s["rr"]) * 1.025 * (1 - 0.025 / 0.35)
        pv += op_T / (COE - 0.025) * (1 + COE) ** -t_years(date(2036, 7, 1))
        return pv

    g10 = solve(pv_10y, -0.05, 0.20, ev_mkt)
    return g_perp, g10, ev_mkt


def cross_checks():
    mcap = PRICE * SHARES
    ttm_parent = 814.34
    ttm_op_parent = ttm_parent - interest_parent_annual()
    fin = sum(FIN_ASSETS.values())
    ev = mcap + MINORITY_EQUITY + GROUP_DEPOSITS + LEASE_DEBT - fin - NON_OPERATING
    ebit_ttm = 1109.55 - 606.67 + 596.67    # 2025 全年 − 2025H1 + 2026H1（利润总额扣净利息与营业外）
    div_ttm = 51.9812                         # 过去 12 个月除息每股现金（数据包）
    buyback_ttm = 30.0                        # 第二轮回购 2025-12-31～2026-05-27 合计 30.00 亿元
    return dict(
        pe_ttm=mcap / ttm_parent,
        pe_ex_cash=(mcap - net_cash_adj() - NON_OPERATING) / ttm_op_parent,
        ev=ev, ev_ebit=ev / ebit_ttm, ebit_ttm=ebit_ttm,
        div_yield=div_ttm / PRICE, buyback_yield=buyback_ttm / mcap,
        pb=mcap / 2512.54,
    )


def falsifier_values():
    out = {}
    # F1：三季报单季归母 < 180 亿（同比 −6%）→ 概率改为 40/50/10
    out["F1"] = weighted(probs={"bear": 0.40, "base": 0.50, "bull": 0.10})
    # F2：飞天原箱批价连续 4 周 < 1,500，或自营价 < 1,539、合同价 < 1,269 → 熊市情景
    out["F2"] = scenario_value(SCENARIOS["bear"])
    # F3：2026 年报归母 < 800 亿 → 基准正常化下调至 790、熊 700、牛 840，概率不变
    scen3 = {k: dict(v) for k, v in SCENARIOS.items()}
    scen3["bear"].update(np26=700.0, h2_26=350.0)
    scen3["base"].update(np26=790.0, h2_26=350.0)
    scen3["bull"].update(np26=840.0, h2_26=350.0)
    out["F3"] = weighted(scen=scen3)
    # F4：再有董事、高管被留置，或披露关联方非经营性占用／财务公司对集团放款 > 50 亿 → 股权成本 10%
    out["F4"] = weighted(r=0.10)
    # F5（上行）：2027H1 归母 ≥ 500 亿（同比约 +12%）且批价 ≥ 1,850 → 基准正常化上调至 860，概率 10/50/40
    scen5 = {k: dict(v) for k, v in SCENARIOS.items()}
    scen5["base"].update(np26=860.0)
    out["F5"] = weighted(scen=scen5, probs={"bear": 0.10, "base": 0.50, "bull": 0.40})
    return out


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 贵州茅台 600519 独立估值（价格日 2026-10-20，现价 %.2f，股本 %.4f 亿股）==" % (PRICE, SHARES))
    fin = sum(FIN_ASSETS.values())
    print("\n[经调整净现金，亿元]")
    for k, v in FIN_ASSETS.items():
        print("  + %-44s %9.2f" % (k, v))
    print("  = 现金与金融类资产合计 %33.2f" % fin)
    for k, v in [("法定存款准备金（受限）", RESTRICTED), ("集团成员单位在财务公司存款（关联方，类债务）", GROUP_DEPOSITS),
                 ("租赁负债", LEASE_DEBT), ("经营备付", OPERATING_RESERVE), ("少数股东权益", MINORITY_EQUITY)]:
        print("  − %-44s %9.2f" % (k, v))
    print("  = 经调整净现金 %41.2f（%.1f 元/股）" % (net_cash_adj(), net_cash_adj() / SHARES))
    print("  非经营资产 %44.2f（%.1f 元/股）" % (NON_OPERATING, NON_OPERATING / SHARES))
    print("  关联方存款单列：贵州银行存款 %.2f（已含在货币资金）；集团在财务公司存款 %.2f（已全额扣除）" % (GUIZHOU_BANK_DEPOSIT, GROUP_DEPOSITS))
    print("  归母税后净利息 2026E %.2f 亿（税前 %.1f × 0.75 × %.2f）" % (interest_parent_annual(), NET_INTEREST_PRETAX_2026, PARENT_SHARE_OF_INTEREST))

    print("\n[三情景，股权成本 9%]")
    vs = {}
    for k, s in SCENARIOS.items():
        v, d = scenario_value(s, detail=True)
        vs[k] = v
        print("  %s  p=%.2f  2026 正常化归母 %.0f（经营 %.1f，OE %.1f）  V = %.0f 元/股  终值占权益 %.0f%%"
              % (k, s["p"], s["np26"], d["op26"], d["oe26"], v, d["tv_share"] * 100))
        print("      假设：" + s["text"])
        print("      2026H2 OE %.1f；" % d["oe_h2"] + "；".join("%d: g %+.1f%% 经营归母 %.1f OE %.1f" % (y, g * 100, op, oe)
                                                         for y, g, op, oe, _ in d["rows"]))
        print("      终值：gT %.1f%%，终值再投资率 %.1f%%，OE_2032 %.1f，TV %.0f，TV 现值 %.0f；显性期现值 %.0f；权益 %.0f"
              % (s["gT"] * 100, s["gT"] / s["ronic_T"] * 100, d["oe_T"], d["tv"], d["pv_tv"], d["pv_explicit"], d["eq"]))
    vw = weighted()
    pv_ratio = PRICE / vw
    print("\n  加权 V = %.0f 元/股；P/V = %.3f → %s" % (vw, pv_ratio, band(pv_ratio)))
    print("  V 不变时各档价格：≤ %.0f 明显低估；%.0f～%.0f 温和低估；%.0f～%.0f 大致合理；> %.0f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print("  无回购专户股份，剔除口径 V 与上同。")

    print("\n[股权成本敏感性]")
    for r in (0.08, 0.09, 0.10):
        print("  r = %.0f%%：熊 %.0f／基 %.0f／牛 %.0f；加权 %.0f；P/V %.3f"
              % (r * 100, scenario_value(SCENARIOS["bear"], r), scenario_value(SCENARIOS["base"], r),
                 scenario_value(SCENARIOS["bull"], r), weighted(r), PRICE / weighted(r)))

    irr = implied_irr()
    g_perp, g10, ev_mkt = reverse_dcf()
    print("\n[现价隐含回报与反向 DCF]")
    print("  基准情景现金流下现价隐含回报（IRR）= %.2f%%" % (irr * 100))
    print("  现价对应经营价值 %.0f 亿；9%% 折现下隐含永续增速 %.2f%%；隐含 2027～2036 年所有者收益年增 %.2f%%（之后 2.5%%）"
          % (ev_mkt, g_perp * 100, g10 * 100))

    c = cross_checks()
    print("\n[交叉验证]")
    print("  PE(TTM) %.1f×；扣净现金与非经营资产后经营 PE %.1f×；PB %.2f×" % (c["pe_ttm"], c["pe_ex_cash"], c["pb"]))
    print("  EV %.0f 亿；TTM EBIT %.1f 亿；EV/EBIT %.1f×" % (c["ev"], c["ebit_ttm"], c["ev_ebit"]))
    print("  股息率 %.2f%% + 回购收益率 %.2f%% = %.2f%%" % (c["div_yield"] * 100, c["buyback_yield"] * 100,
                                                     (c["div_yield"] + c["buyback_yield"]) * 100))

    print("\n[证伪情景 V]")
    for k, v in falsifier_values().items():
        print("  %s：V = %.0f 元/股，P/V = %.3f" % (k, v, PRICE / v))


if __name__ == "__main__":
    main()
