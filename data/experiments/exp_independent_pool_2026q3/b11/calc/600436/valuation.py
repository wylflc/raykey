# -*- coding: utf-8 -*-
"""片仔癀（600436）独立估值（OI-291 b11，价格日 2026-10-20）。

方法：所有者收益 DCF（医药制造业按“重置成本”毛利率计经济利润，归母口径）
      + 超额存货市值 + 存货账面高于市价部分的税盾 − 在建项目资本开支的价值损失
      + 经调整净现金 + 非经营资产。经调整净现金为正，有息负债全额扣除（无杠杆口径）。
金额单位：亿元；每股价值：元/股。输入全部写在脚本内，来源见注释。
运行：python3 valuation.py
"""

PRICE = 123.41            # 2026-10-20 收盘（brief.md）
SHARES = 6.03317210       # 亿股；总股本 603,317,210 股，无库存股/回购专户（2026H1_report 第 47 页）
COE = 0.09

# ---------------- 资产负债表（2026-06-30，2026H1_report） ----------------
CASH = 21.1416            # 货币资金（第 46 页）
TD_CUR = 15.2965          # 其他流动资产中“一年内银行定期存款及利息”（第 132 页）
TD_NONCUR = 31.4774       # 其他非流动资产中“定期存单”（第 153 页）
RESTRICTED = 0.1623       # 受限货币资金（第 154 页）
DEBT = 8.1698 + 0.5228 + 0.4401 + 1.2052   # 短期借款+长期借款+一年内到期非流动负债+租赁负债（第 47 页）
DIV_PAYABLE = 9.4780      # 应付股利：2025 年度 1.57 元/股，2026-07-31 发放（第 159 页）
LT_STAFF = 0.5292         # 长期应付职工薪酬（设定受益计划，类债务，第 47 页）
INTERIM_DIV = 6.4555      # 2026 年中期 1.07 元/股，2026-10-16 发放（dividend_20261010_270388 第 2 页）
OP_RESERVE = 5.0          # 经营备付：约 1 个月合并现金成本（假设）

NET_CASH_ADJ = (CASH + TD_CUR + TD_NONCUR - RESTRICTED - DEBT - DIV_PAYABLE
                - LT_STAFF - INTERIM_DIV - OP_RESERVE)

# ---------------- 非经营资产（第 136-138 页；对外投资承诺见第 216 页） ----------------
FUNDS_LTEI = 4.7272 + 1.4126 + 0.5968 + 0.5950 + 0.5996 + 0.2000 + 0.2553 + 0.0197
#            圆山大健康  盈科    招盈    高鑫    中金    再生医学  兴证    闽山
FUNDS_ONCFA = 0.3514      # 其他非流动金融资产（丰园群贤、阳明康怡）
ASSOC_OPER = 1.1090 + 0.0909 + 0.0526 + 0.0196 + 0.0351 + 0.0040
#            同春药业  爱之味  麝业   广生合癀  高科   嘉昀达
LISTED = 2.9402 + 0.6052 + 0.1343 + 0.0476   # 兴业证券、兴业银行、华润双鹤、辽宁成大（第 28 页）
OEI_OTHER = 3.8722 - LISTED                   # 其他权益工具投资中非上市部分
UNFUNDED = 6.7865         # 已签约未出资的对外投资承诺
FUND_HAIRCUT = 0.20       # 产业基金流动性与估值折价（假设）
NON_OP = ((FUNDS_LTEI + FUNDS_ONCFA) * (1 - FUND_HAIRCUT) + LISTED + OEI_OTHER + ASSOC_OPER
          - UNFUNDED * FUND_HAIRCUT)

# ---------------- 医药制造业存货（2026-06-30，第 127 页） ----------------
MFG_INV_BOOK = 40.9205 + 5.5995 + 4.4295     # 原材料 + 库存商品 + 在产品及半成品
RESERVE_YEARS = 2.75      # 正常战略储备：约 2.75 年材料耗用（2020-2022 年约 2.3~2.8 年，推算）
MATERIAL_SHARE = 0.96     # 直接材料占营业成本（2025_annual_report 第 26 页：95.47%）

# ---------------- 原料成本模型：由历史毛利率标定，推导重置成本毛利率 ----------------
GM_MFG_2021 = 0.784       # 医药制造业毛利率 2021（东财主营构成：39.72 收入、8.59 成本）
GM_MFG_2025 = 0.5929      # 2025_annual_report 第 23 页
GM_MFG_2024 = 0.647       # 东财主营构成 2024（56.63 收入、20.02 成本），用于验证
PRICE_UPLIFT = 1.40       # 2023-05 提价：国内供应价约 +170 元/粒、境外约 +35 美元/粒（网络来源），折合出厂均价约 1.4 倍
SH_MUSK = 0.30            # 2021 年耗用成本中天然麝香占比（假设）
# 各年耗用口径单价（万元/kg）：(天然牛黄, 天然麝香, 其他材料与制造费用倍数)；2021 年为基期
BASIS = {2021: (37.5, 30.0, 1.00), 2024: (118.0, 48.0, 1.15), 2025: (140.0, 55.0, 1.20)}


def _mult(year_or_prices, a, b):
    nh, mu, ot = year_or_prices
    nh0, mu0, _ = BASIS[2021]
    return a * nh / nh0 + b * mu / mu0 + (1 - a - b) * ot


def calibrate_share_niuhuang():
    """由 2025 年毛利率反解 2021 年耗用成本中天然牛黄占比 a。"""
    target = (1 - GM_MFG_2025) * PRICE_UPLIFT / (1 - GM_MFG_2021)
    nh, mu, ot = BASIS[2025]
    nh0, mu0, _ = BASIS[2021]
    b = SH_MUSK
    # target = a*nh/nh0 + b*mu/mu0 + (1-a-b)*ot
    return (target - b * mu / mu0 - (1 - b) * ot) / (nh / nh0 - ot)


SH_NIUHUANG = calibrate_share_niuhuang()
SH_OTHER = 1 - SH_NIUHUANG - SH_MUSK


def gm_from_prices(prices, mix_drag=0.0, price_cut=0.0, uplift=PRICE_UPLIFT):
    cost_ratio = (1 - GM_MFG_2021) * _mult(prices, SH_NIUHUANG, SH_MUSK) / uplift / (1 - price_cut)
    return 1 - cost_ratio - mix_drag


def inv_market_to_book(niuhuang, musk, other_mb=0.8):
    """存货按 2025 年耗用口径单价计账面；市价/账面按各原料账面价值占比加权。"""
    nh, mu, ot = BASIS[2025]
    nh0, mu0, _ = BASIS[2021]
    w_nh = SH_NIUHUANG * nh / nh0
    w_mu = SH_MUSK * mu / mu0
    w_ot = SH_OTHER * ot
    tot = w_nh + w_mu + w_ot
    return (w_nh * niuhuang / nh + w_mu * musk / mu + w_ot * other_mb) / tot


# ---------------- 情景 ----------------
H1_2026_MFG = 24.5176     # 2026H1 医药制造业收入（2026H1_report 第 22 页）
SCEN = {
    "bear": dict(p=0.30, h2_mfg=13.3, growth=[-0.08, -0.03, 0.00, 0.01, 0.015], g_term=0.015,
                 niuhuang=100.0, musk=70.0, other_mult=1.2, mix_drag=0.015, price_cut=0.03,
                 selling=0.050, rd=0.060, admin=1.20, tax=0.175, other_seg=-0.10,
                 project_capex=22.0, project_recovery=0.3, gm_book_h2=0.605),
    "base": dict(p=0.50, h2_mfg=14.8, growth=[0.01, 0.04, 0.05, 0.05, 0.04], g_term=0.025,
                 niuhuang=70.0, musk=65.0, other_mult=1.2, mix_drag=0.010, price_cut=0.0,
                 selling=0.040, rd=0.055, admin=1.15, tax=0.155, other_seg=0.20,
                 project_capex=18.0, project_recovery=0.5, gm_book_h2=0.615),
    "bull": dict(p=0.20, h2_mfg=16.3, growth=[0.07, 0.08, 0.07, 0.06, 0.05], g_term=0.025,
                 niuhuang=52.0, musk=60.0, other_mult=1.2, mix_drag=0.005, price_cut=0.0,
                 selling=0.035, rd=0.050, admin=1.10, tax=0.150, other_seg=0.45,
                 project_capex=14.0, project_recovery=0.7, gm_book_h2=0.625),
}
SURCHARGE = 0.010         # 税金及附加 / 收入
OTHER_SEG_GROWTH = 0.025  # 流通、化妆品等其他板块归母利润增速
ADMIN_GROWTH = 0.03
T_H2 = 0.1                # 2026H2 余下现金流（距价格日，年）
T_YEARS = [0.7, 1.7, 2.7, 3.7, 4.7]   # 2027-2031 年中
T_TV = 5.2                # 2031 年末
PROJ_W = [0.15, 0.35, 0.30, 0.20]      # 项目开支在 2026H2-2029 的分布
PROJ_T = [0.1, 0.7, 1.7, 2.7]
# 净利息（计入正常化归母净利，不计入经营所有者收益）：存款利息约 0.85、借款利息约 0.27、上市股票股利 0.12
NET_INTEREST_AFTER_TAX = (0.85 - 0.27) * (1 - 0.155) + 0.12
H1_2026_PARENT_NP = 10.9297   # 2026H1 归母净利（第 51 页）
H2_NET_INTEREST = 0.30        # 2026H2 报表口径净利息与投资收益（税后，估计）


def scenario_value(name, r=COE, detail=False, gm_shift=0.0, rev_scale=1.0):
    s = SCEN[name]
    gm = gm_from_prices((s["niuhuang"], s["musk"], s["other_mult"]),
                        s["mix_drag"], s["price_cut"]) + gm_shift
    h2 = s["h2_mfg"] * rev_scale
    r2026 = H1_2026_MFG * rev_scale + h2
    wci = RESERVE_YEARS * (1 - gm) * MATERIAL_SHARE + 0.02

    def nopat(rev, admin):
        return (rev * (gm - SURCHARGE - s["selling"] - s["rd"]) - admin) * (1 - s["tax"])

    admin = s["admin"]
    other = s["other_seg"]
    nopat26 = nopat(r2026, admin)
    oe26 = nopat26 + other
    ebit_h2 = h2 * (gm - SURCHARGE - s["selling"]) - 0.5 * (admin + s["rd"] * r2026)
    oe_h2 = ebit_h2 * (1 - s["tax"]) + 0.5 * other
    pv = oe_h2 / (1 + r) ** T_H2

    rev, rows = r2026, []
    for i, g in enumerate(s["growth"]):
        new_rev = rev * (1 + g)
        admin *= 1 + ADMIN_GROWTH
        other *= 1 + OTHER_SEG_GROWTH
        np_ = nopat(new_rev, admin) + other
        reinv = wci * (new_rev - rev)
        oe = np_ - reinv
        pv += oe / (1 + r) ** T_YEARS[i]
        rows.append((2027 + i, new_rev, np_, reinv, oe))
        rev = new_rev
    g = s["g_term"]
    rev32 = rev * (1 + g)
    np32 = nopat(rev32, admin * (1 + ADMIN_GROWTH)) + other * (1 + g)
    oe32 = np32 - wci * (rev32 - rev)
    tv = oe32 / (r - g) * (1 + r) ** 0.5
    pv_tv = tv / (1 + r) ** T_TV
    pv_ops = pv + pv_tv

    mb = inv_market_to_book(s["niuhuang"], s["musk"])
    consumption = r2026 * (1 - gm) * MATERIAL_SHARE
    excess = max(0.0, MFG_INV_BOOK * mb - RESERVE_YEARS * consumption)
    pv_excess = excess / (1 + r) ** 1.2
    tax_shield = s["tax"] * MFG_INV_BOOK * (1 - mb) / (1 + r) ** 1.5
    pv_proj = sum(s["project_capex"] * w / (1 + r) ** t for w, t in zip(PROJ_W, PROJ_T))
    proj_loss = (1 - s["project_recovery"]) * pv_proj

    equity = pv_ops + pv_excess + tax_shield - proj_loss + NET_CASH_ADJ + NON_OP
    v = equity / SHARES
    if not detail:
        return v
    # 2026 报表口径归母净利估计（下半年仍按高价存货的账面毛利率）
    ebit_h2_book = h2 * (s["gm_book_h2"] - SURCHARGE - s["selling"]) - 0.5 * (s["admin"] + s["rd"] * r2026)
    np2026_reported = (H1_2026_PARENT_NP + ebit_h2_book * (1 - s["tax"]) + 0.5 * s["other_seg"]
                       + H2_NET_INTEREST)
    np_list = [oe26] + [x[2] for x in rows]
    reinv_sum = sum(x[3] for x in rows)
    nopat_sum = sum(x[2] for x in rows)
    incr_ret = (rows[-1][2] - oe26) / reinv_sum if reinv_sum > 0 else float("nan")
    return dict(v=v, gm=gm, r2026=r2026, wci=wci, oe26=oe26, oe_h2=oe_h2, rows=rows,
                oe32=oe32, pv_ops=pv_ops, pv_tv=pv_tv, tv_share=pv_tv / equity, excess=excess,
                pv_excess=pv_excess, tax_shield=tax_shield, proj_loss=proj_loss, mb=mb,
                equity=equity, np2026_norm=oe26 + NET_INTEREST_AFTER_TAX,
                np2026_reported=np2026_reported, reinv_rate=reinv_sum / nopat_sum,
                incr_ret=incr_ret,
                oe_growth=[rows[0][4] / oe26 - 1] + [rows[i][4] / rows[i - 1][4] - 1 for i in range(1, 5)],
                np_list=np_list)


def weighted(r=COE):
    return sum(SCEN[k]["p"] * scenario_value(k, r) for k in SCEN)


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if fm * flo <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def _fixed_items(d, r):
    return (d["pv_excess"] + d["tax_shield"] - d["proj_loss"] + NET_CASH_ADJ + NON_OP
            + d["oe_h2"] / (1 + r) ** T_H2)


def reverse_dcf_growth10(r=COE, g_term=0.025):
    """现价隐含：以基准情景 2027 年所有者收益为起点，2028-2036 年复合增速 x，之后 2.5% 永续。"""
    d = scenario_value("base", r, detail=True)
    oe27 = d["rows"][0][4]
    fixed = _fixed_items(d, r)

    def val(x):
        pv, oe = 0.0, oe27
        for i in range(10):
            if i > 0:
                oe *= 1 + x
            pv += oe / (1 + r) ** (0.7 + i)
        tv = oe * (1 + g_term) / (r - g_term) * (1 + r) ** 0.5 / (1 + r) ** 10.2
        return (pv + tv + fixed) / SHARES
    return solve(val, -0.2, 0.5, PRICE), oe27


def reverse_dcf_perpetual(r=COE):
    """现价隐含：以基准情景 2027 年所有者收益为起点的永续增速。"""
    d = scenario_value("base", r, detail=True)
    oe27 = d["rows"][0][4]
    fixed = _fixed_items(d, r)
    return solve(lambda g: (oe27 / (r - g) * (1 + r) ** 0.3 + fixed) / SHARES, -0.05, r - 0.001, PRICE)


def variant_value(r=COE, **overrides):
    """基准情景参数替换部分假设后的 V（用于证伪条件触发后的独立 V）。"""
    saved = dict(SCEN["base"])
    try:
        SCEN["base"].update(overrides)
        return scenario_value("base", r)
    finally:
        SCEN["base"].clear()
        SCEN["base"].update(saved)


FALSIFIERS = {
    "F1 需求：2026 年医药制造业收入 < 37.8 亿（下半年 < 13.3 亿），收入路径转熊":
        dict(h2_mfg=13.3, growth=SCEN["bear"]["growth"], g_term=0.015),
    "F2 毛利：2027 年肝病用药毛利率 < 63.5%（降价原料未带来修复或出厂价让利）":
        dict(niuhuang=100.0, musk=70.0, mix_drag=0.015, price_cut=0.03),
    "F3 原料：天然牛黄市价连续两个季度 ≥ 100 万元/kg（2027 年内）":
        dict(niuhuang=100.0),
    "F4 税率：高新技术企业复审未通过，所得税率 25%":
        dict(tax=0.25),
    "F5 上行：2027 年医药制造业收入 ≥ 46 亿且肝病用药毛利率 ≥ 70%":
        dict(h2_mfg=16.3, growth=SCEN["bull"]["growth"], niuhuang=52.0, musk=60.0, mix_drag=0.005),
}


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print(f"成本标定：2021 年耗用成本中天然牛黄 {SH_NIUHUANG:.1%}、麝香 {SH_MUSK:.0%}、其他 {SH_OTHER:.1%}；"
          f"验证 2024 年毛利率 {gm_from_prices(BASIS[2024]):.1%}（实际 {GM_MFG_2024:.1%}）")
    print(f"现价牛黄 52 万/kg、麝香 60 万/kg 时重置成本毛利率 {gm_from_prices((52.0, 60.0, 1.2)):.1%}")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} 亿；非经营资产 {NON_OP:.2f} 亿；制造业存货账面 {MFG_INV_BOOK:.2f} 亿")
    for k in SCEN:
        d = scenario_value(k, detail=True)
        print(f"\n[{k}] p={SCEN[k]['p']:.2f}  V = {d['v']:.2f} 元/股  重置成本毛利率 {d['gm']:.1%}  2026 制造业收入 {d['r2026']:.2f}")
        print(f"  2026 正常化归母净利（经济口径，含净利息）{d['np2026_norm']:.2f} 亿；2026 报表口径估计 {d['np2026_reported']:.2f} 亿；"
              f"2026H2 所有者收益 {d['oe_h2']:.2f}")
        print(f"  2026 经营所有者收益（不含利息）{d['oe26']:.2f}")
        for y, rev, np_, reinv, oe in d["rows"]:
            print(f"  {y}: 制造业收入 {rev:.2f}  归母经营利润 {np_:.2f}  再投资 {reinv:.2f}  所有者收益 {oe:.2f}")
        print("  所有者收益增速 2027-2031: " + ", ".join(f"{x:.1%}" for x in d["oe_growth"])
              + f"；终值增速 {SCEN[k]['g_term']:.1%}")
        print(f"  再投资率 {d['reinv_rate']:.1%}；增量回报 {d['incr_ret']:.0%}；营运资本强度 {d['wci']:.2f}")
        print(f"  2032 所有者收益 {d['oe32']:.2f}；经营现值 {d['pv_ops']:.1f}（终值现值 {d['pv_tv']:.1f}，占股权价值 {d['tv_share']:.0%}）")
        print(f"  存货市价/账面 {d['mb']:.2f}；超额存货 {d['excess']:.2f}（现值 {d['pv_excess']:.2f}）；"
              f"税盾 {d['tax_shield']:.2f}；项目开支价值损失 {d['proj_loss']:.2f}；股权价值 {d['equity']:.1f} 亿")
    vw = weighted()
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {PRICE / vw:.2f}（{band(PRICE / vw)}）")
    for r in (0.08, 0.10):
        print(f"股权成本 {r:.0%}：熊 {scenario_value('bear', r):.2f} / 基 {scenario_value('base', r):.2f} / "
              f"牛 {scenario_value('bull', r):.2f}；加权 {weighted(r):.2f}；P/V {PRICE / weighted(r):.2f}")
    irr = solve(lambda r: scenario_value("base", r), 0.03, 0.20, PRICE)
    print(f"现价隐含回报（基准情景所有者收益流，含终值与净现金）= {irr:.2%}")
    g10, oe27 = reverse_dcf_growth10()
    print(f"反向 DCF：以基准 2027 年所有者收益 {oe27:.2f} 亿为起点，现价隐含 2028-2036 年复合增速 {g10:.1%}（之后 2.5%）")
    print(f"反向 DCF：现价隐含永续增速 {reverse_dcf_perpetual():.2%}")
    print("基准情景敏感性：毛利率 ±3pp → "
          f"{scenario_value('base', gm_shift=-0.03):.2f} / {scenario_value('base', gm_shift=0.03):.2f}；"
          f"收入 ±10% → {scenario_value('base', rev_scale=0.9):.2f} / {scenario_value('base', rev_scale=1.1):.2f}")
    for name, pv in (("0.75", 0.75), ("0.90", 0.90), ("1.10", 1.10)):
        print(f"V 不变时 P/V = {name} 对应价格 {vw * pv:.2f} 元")
    print("\n证伪条件触发后的独立 V（基准情景替换相应假设，9%）：")
    for label, ov in FALSIFIERS.items():
        v = variant_value(**ov)
        print(f"  {label}：V = {v:.2f} 元，P/V = {PRICE / v:.2f}")
    print("\n股本口径：总股本 6.0332 亿股，无库存股与回购专户股份，剔除口径的 V 与 P/V 与上相同")
