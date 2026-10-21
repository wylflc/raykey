#!/usr/bin/env python3
"""巨化股份（600160）独立估值：所有者收益 DCF（有杠杆口径）+ 甘肃项目 NPV + 非经营资产分部加总。

运行：python3 valuation.py
金额单位：亿元；价格与 V：元/股；制冷剂量价：万吨、千元/吨（不含税）。
价格日 2026-10-21；最新定期报告 2026 中报（三季报预约 2026-10-24）。

主要输入来源（页码为 PDF 物理页）：
- 2026H1_report：资产负债表 p71-73；制冷剂均价 45,521 元/吨 p22；外销量 155,993.79 吨 p28；
  在建工程 p157-159；长期股权投资 p149-150；联营企业 p198-200；少数股东 p196-197；
  财务公司存贷 p65-66；受限资金 p166；其他流动资产 p144；其他非流动资产 p165-166；借款 p167/p171；
  长期应付款 p173。
- 2025_annual_report：2026 年 HFCs 配额 p67；制冷剂均价 39,490 元/吨 p30-31；外销量 342,980.61 吨 p39；
  2026 年经营计划（固定资产投资用款 93.42 亿、资金净流出 112.1 亿）p100-101。
- 甘肃项目：2025-02-19 临 2025-06 公告 第 10-11 页（总投资 196.25 亿，税后项目 IRR 6.63%）。
- 中巨芯：腾讯行情 2026-10-21 收盘 18.35 元、总市值 271.08 亿；持股 26.40%（2026H1_report p198）。
"""

from __future__ import annotations

# ----------------------------------------------------------------------------
# 0. 快照
# ----------------------------------------------------------------------------
PRICE = 29.72
SHARES = 26.9975          # 亿股，腾讯行情；无回购专户股份、无库存股（2026H1_report p73）
MCAP = PRICE * SHARES
COE = 0.09
PROB = {"bear": 0.25, "base": 0.50, "bull": 0.25}
YEARS = list(range(2027, 2037))       # 显式期 2027-2036；2026H2 单列
T_2026H2 = 0.0                        # 2026 下半年现金流视同估值日（已过大半）
T_2027 = 0.69                         # 2027 年中距 2026-10-21 约 0.69 年

# ----------------------------------------------------------------------------
# 1. 资产负债表（2026-06-30）与经调整净现金
# ----------------------------------------------------------------------------
BS = dict(
    cash=40.74,            # 货币资金
    restricted=6.36,       # 受限货币资金（票据/信用证/保函保证金等）p166
    wmp=3.20,              # 其他流动资产中的理财产品 p144
    trading=0.01,          # 交易性金融资产
    st_loan=15.76,         # 短期借款
    lt_loan=61.13,         # 长期借款
    lt_loan_current=12.87, # 一年内到期的长期借款 p171
    lease=1.52 + 0.20,     # 租赁负债（含一年内到期）
    lt_payable=0.83 + 0.11,# 长期应付款（含向 iGas 借款 0.66 亿、职工安置款）p173
    fc_deposit=21.53,      # 存放巨化集团财务公司（关联方）p65-66，已含在货币资金内
    fc_loan=4.97,          # 向财务公司借款，已含在借款内
)
OP_RESERVE = 8.0          # 经营备付（约营收 3%）
DECLARED_DIV = 5.94       # 2026 年中期分红（8-25 宣派、9-24 实施），资产负债表日后流出
DEBT = BS["st_loan"] + BS["lt_loan"] + BS["lt_loan_current"] + BS["lease"] + BS["lt_payable"]
NET_CASH_ADJ = (BS["cash"] + BS["wmp"] + BS["trading"] - BS["restricted"]
                - OP_RESERVE - DECLARED_DIV - DEBT)
# 有息负债实际平均利率：2026H1 费用化利息 0.62 亿 + 资本化利息 0.316 亿（p158-159），
# 年化 1.87 亿 / 平均有息负债约 76 亿 ≈ 2.46%
R_DEBT = 0.025
TAX_SHIELD = 0.15

# ----------------------------------------------------------------------------
# 2. 情景参数
# ----------------------------------------------------------------------------
# 制冷剂：量（万吨，外销）、正常化均价 P 与单位成本 C（千元/吨，不含税）
# 2026H2 过渡价 46.5（Q3 长协 R32 上调 2,800-2,900 元，Q4 再 +500）；2027 取过渡价与正常化价的均值；
# 2029 配额削减 10%（相对基线，CO2 当量）：量 × v29、价 × p29；2035 削减 30%：量 × v35、价 × p35。
SCEN = {
    "bear": dict(
        V=30.5, P=36.0, C=21.0, v29=0.90, p29=1.04, v35=0.78, p35=1.06,
        V_h2=15.5, nonref=[11.0, 12.0, 13.0], nonref_g=0.0,
        opex=20.0, impair=2.5, tax=0.150, mi=0.11, g_term=-0.015,
        # 甘肃项目（100% 口径）
        gs_capex=[30.0, 50.0, 35.0], gs_roic=0.02, gs_startup_loss=4.0, gs_g=-0.01,
        # 非经营资产：中巨芯按基本面（PB 2.5×、扣税），其余折价
        zjx_mode="fundamental", fc_mult=0.6, igas_mult=0.7, other_assoc_mult=0.8, oei_mult=0.7,
        assoc_income=0.9, net_interest=1.2,
    ),
    "base": dict(
        V=32.5, P=43.0, C=21.3, v29=0.92, p29=1.08, v35=0.82, p35=1.12,
        V_h2=16.0, nonref=[16.0, 18.0, 20.0], nonref_g=0.015,
        opex=20.5, impair=1.5, tax=0.145, mi=0.11, g_term=0.0,
        gs_capex=[30.0, 35.0, 20.0], gs_roic=0.04, gs_startup_loss=2.5, gs_g=0.0,
        zjx_mode="market_70", fc_mult=0.8, igas_mult=1.0, other_assoc_mult=1.0, oei_mult=0.9,
        assoc_income=1.3, net_interest=1.0,
    ),
    "bull": dict(
        V=34.0, P=49.0, C=21.8, v29=0.93, p29=1.10, v35=0.84, p35=1.15,
        V_h2=16.5, nonref=[20.0, 23.0, 26.0], nonref_g=0.025,
        opex=21.0, impair=1.0, tax=0.145, mi=0.11, g_term=0.015,
        gs_capex=[30.0, 25.0, 10.0], gs_roic=0.06, gs_startup_loss=1.5, gs_g=0.01,
        zjx_mode="market_90", fc_mult=1.0, igas_mult=1.2, other_assoc_mult=1.0, oei_mult=1.0,
        assoc_income=1.5, net_interest=0.9,
    ),
}
P_H2 = 46.5          # 2026H2 过渡均价
C_H2 = 21.6          # 2026H2 单位成本（2026H1 约 21.6）
OPEX_G = 0.02        # 费用年增 2%
CORE_GROWTH_CAPEX = {"2026H2": 10.0, 2027: 10.0, 2028: 6.0}  # 非甘肃新项目（飞源 R32、含氟化学品等），母公司口径
# 截至 2026-06-30 甘肃化工+风电已投入：化工 196.25×27.99%=54.93（p158，含预付）+ 风电 37.37×69.61%=26.01
# + 土地约 4 → 约 85 亿（100% 口径）
GS_SUNK = 85.0
GS_SHARE = 0.70

# 非经营资产
ZJX_SHARES = 0.2640 * 271.08 / 18.35   # 亿股：持股 26.40% × 总股本（总市值/股价）
ZJX_PRICE = 18.35
ZJX_BOOK = 7.97
ZJX_EQUITY = 30.17                      # 中巨芯归母权益 2026-06-30（p199）
FC_BOOK, IGAS_BOOK = 6.83, 8.99
OTHER_ASSOC_BOOK = 26.99 - 7.97 - 6.83 - 8.99
OEI_BOOK = 10.56                        # 其他权益工具投资（富浙集成电路 10.00 等）
CGT = 0.25


def zjx_value(mode: str) -> float:
    mv = ZJX_SHARES * ZJX_PRICE
    after_tax = mv - CGT * (mv - ZJX_BOOK)
    if mode == "fundamental":
        fv = 2.5 * ZJX_EQUITY * 0.2640
        return fv - CGT * max(fv - ZJX_BOOK, 0.0)
    if mode == "market_70":
        return after_tax * 0.70
    if mode == "market_90":
        return after_tax * 0.90
    raise ValueError(mode)


def nonop(s: dict) -> dict:
    d = dict(
        zjx=zjx_value(s["zjx_mode"]),
        fc=FC_BOOK * s["fc_mult"],
        igas=IGAS_BOOK * s["igas_mult"],
        other_assoc=OTHER_ASSOC_BOOK * s["other_assoc_mult"],
        oei=OEI_BOOK * s["oei_mult"],
    )
    d["total"] = sum(d.values())
    return d


# ----------------------------------------------------------------------------
# 3. 核心业务（不含甘肃项目与联营收益）
# ----------------------------------------------------------------------------
def ref_gp(V: float, P: float, C: float) -> float:
    return V * (P - C) / 10.0     # 万吨 × 千元/吨 / 10 = 亿元


def core_path(s: dict) -> dict:
    """返回各年合并 EBIT、归母 NOPAT、归母所有者收益（扣增长性资本开支）。"""
    out = {}
    # 2026 正常化（登记用）
    gp26 = ref_gp(s["V"], s["P"], s["C"])
    ebit26 = gp26 + s["nonref"][0] - s["opex"] - s["impair"]
    out["norm2026"] = dict(ref_gp=gp26, ebit=ebit26,
                           nopat_parent=ebit26 * (1 - s["tax"]) * (1 - s["mi"]))
    # 2026H2 过渡期（半年）
    gp_h2 = ref_gp(s["V_h2"], P_H2, C_H2)
    ebit_h2 = gp_h2 + s["nonref"][0] / 2 - s["opex"] / 2 - s["impair"] / 2
    nopat_h2 = ebit_h2 * (1 - s["tax"]) * (1 - s["mi"])
    out["2026H2"] = dict(ebit=ebit_h2, nopat_parent=nopat_h2,
                         oe=nopat_h2 - CORE_GROWTH_CAPEX["2026H2"])
    for i, y in enumerate(YEARS):
        V, P, C = s["V"], s["P"], s["C"]
        if y == 2027:
            P = (P_H2 + s["P"]) / 2
        if y >= 2029:          # 配额削减 10%：量、价相对 2027-2028 水平
            V, P = V * s["v29"], P * s["p29"]
        if y >= 2035:          # 配额削减 30%：量、价再相对 2029-2034 水平
            V, P = V * s["v35"], P * s["p35"]
        gp = ref_gp(V, P, C)
        if y == 2027:
            nonref = s["nonref"][1]
        elif y == 2028:
            nonref = s["nonref"][2]
        else:
            nonref = s["nonref"][2] * (1 + s["nonref_g"]) ** (y - 2028)
        opex = s["opex"] * (1 + OPEX_G) ** (y - 2026)
        ebit = gp + nonref - opex - s["impair"]
        nopat = ebit * (1 - s["tax"]) * (1 - s["mi"])
        capex = CORE_GROWTH_CAPEX.get(y, 0.0)
        out[y] = dict(V=V, P=P, ref_gp=gp, nonref=nonref, ebit=ebit,
                      nopat_parent=nopat, oe=nopat - capex)
    return out


# ----------------------------------------------------------------------------
# 4. 甘肃项目（化工一体化 + 1GW 风电），母公司 70%
# ----------------------------------------------------------------------------
def gansu_path(s: dict) -> dict:
    capex_h2, capex27, capex28 = s["gs_capex"]
    K = GS_SUNK + capex_h2 + capex27 + capex28
    nopat_ss = K * s["gs_roic"]
    ramp = {2027: 0.30, 2028: 0.60, 2029: 0.85}
    out = {"K": K, "nopat_ss": nopat_ss,
           "2026H2": dict(nopat=0.0, capex=capex_h2, oe_parent=-GS_SHARE * capex_h2)}
    for y in YEARS:
        f = ramp.get(y, 1.0)
        nopat = nopat_ss * f - (s["gs_startup_loss"] if y == 2027 else 0.0)
        if y > 2030:
            nopat = nopat_ss * (1 + s["gs_g"]) ** (y - 2030)
        capex = {2027: capex27, 2028: capex28}.get(y, 0.0)
        out[y] = dict(nopat=nopat, capex=capex, oe_parent=GS_SHARE * (nopat - capex))
    return out


# ----------------------------------------------------------------------------
# 5. 估值
# ----------------------------------------------------------------------------
def disc(t: float, r: float) -> float:
    return (1 + r) ** (-t)


def value_scenario(name: str, r: float = COE, detail: bool = False) -> dict:
    s = SCEN[name]
    core = core_path(s)
    gs = gansu_path(s)
    no = nonop(s)
    # 核心业务
    pv_core = core["2026H2"]["oe"] * disc(T_2026H2, r)
    for k, y in enumerate(YEARS):
        pv_core += core[y]["oe"] * disc(T_2027 + k, r)
    oe_2037 = core[2036]["nopat_parent"] * (1 + s["g_term"])
    tv_core = oe_2037 / (r - s["g_term"])
    t_tv = T_2027 + len(YEARS) - 1      # 终值置于 2036 年中点（下一笔现金流前一期）
    pv_tv_core = tv_core * disc(t_tv, r)
    # 甘肃项目
    pv_gs = gs["2026H2"]["oe_parent"] * disc(T_2026H2, r)
    for k, y in enumerate(YEARS):
        pv_gs += gs[y]["oe_parent"] * disc(T_2027 + k, r)
    tv_gs = GS_SHARE * gs[2036]["nopat"] * (1 + s["gs_g"]) / (r - s["gs_g"])
    pv_tv_gs = tv_gs * disc(t_tv, r)
    pv_gansu = pv_gs + pv_tv_gs
    # 净负债两种口径
    net_debt = -NET_CASH_ADJ
    pv_interest = net_debt * R_DEBT * (1 - TAX_SHIELD) / r
    op_value = pv_core + pv_tv_core + pv_gansu
    eq_levered = op_value + no["total"] - pv_interest
    eq_unlevered = op_value + no["total"] - net_debt
    res = dict(
        name=name, r=r,
        pv_core_explicit=pv_core, pv_core_tv=pv_tv_core, pv_gansu=pv_gansu,
        nonop=no, pv_interest=pv_interest, net_debt=net_debt,
        eq_levered=eq_levered, eq_unlevered=eq_unlevered,
        v_levered=eq_levered / SHARES, v_unlevered=eq_unlevered / SHARES,
        tv_share=(pv_tv_core + pv_tv_gs) / op_value if op_value else float("nan"),
        core=core, gansu=gs,
    )
    return res


def weighted(r: float = COE, key: str = "v_levered") -> float:
    return sum(PROB[n] * value_scenario(n, r)[key] for n in PROB)


def normalized_np_2026(name: str) -> float:
    """2026 正常化归母净利（报表口径，含净利息与联营收益，剔除一次性项目，不含甘肃试车损益）。"""
    s = SCEN[name]
    c = core_path(s)["norm2026"]
    return (c["ebit"] - s["net_interest"]) * (1 - s["tax"]) * (1 - s["mi"]) + s["assoc_income"]


def solve(f, lo: float, hi: float, target: float, it: int = 200) -> float:
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr_base() -> float:
    """基准情景现金流（有杠杆口径）使现值等于市值的折现率。"""
    return solve(lambda r: value_scenario("base", r)["eq_levered"], 0.03, 0.20, MCAP)


def reverse_dcf() -> dict:
    """现价隐含：(a) 基准 2026 正常化归母 NOPAT 的永续增速；(b) 10 年增速（终值 2.5%）。"""
    b = value_scenario("base")
    implied_core = MCAP - b["nonop"]["total"] - b["pv_gansu"] + b["pv_interest"]
    oe0 = core_path(SCEN["base"])["norm2026"]["nopat_parent"]
    g_perp = solve(lambda g: oe0 * (1 + g) / (COE - g), -0.05, 0.085, implied_core)

    def pv_10y(g: float) -> float:
        pv, oe = 0.0, oe0
        for k in range(10):
            oe *= (1 + g)
            pv += oe * disc(T_2027 + k, COE)
        tv = oe * 1.025 / (COE - 0.025)
        return pv + tv * disc(T_2027 + 9, COE)

    g10 = solve(pv_10y, -0.10, 0.30, implied_core)
    return dict(implied_core=implied_core, oe0=oe0, g_perp=g_perp, g10=g10)


def fmt(x: float) -> str:
    return f"{x:,.2f}"


def with_overrides(overrides: dict[str, dict], r: float = COE, probs: dict | None = None) -> float:
    """临时改参数后的加权 V（有杠杆口径），用于证伪条件触发后的 V。"""
    saved = {n: dict(SCEN[n]) for n in SCEN}
    try:
        for n, ov in overrides.items():
            SCEN[n].update(ov)
        p = probs or PROB
        return sum(p[n] * value_scenario(n, r)["v_levered"] for n in p)
    finally:
        for n in SCEN:
            SCEN[n].clear()
            SCEN[n].update(saved[n])


def base_v_at_price(p_norm: float) -> float:
    saved = dict(SCEN["base"])
    try:
        SCEN["base"]["P"] = p_norm
        return value_scenario("base")["v_levered"]
    finally:
        SCEN["base"].clear()
        SCEN["base"].update(saved)


def q3_2026_estimate(V=8.0, P=46.8, C=21.7, nonref=4.0, opex=5.2, impair=0.4,
                     net_interest=0.25, assoc=0.35, tax=0.145, mi=0.11) -> float:
    """2026Q3 归母净利粗估（2026Q2 实际 14.77 亿，Q2 外销 8.54 万吨、均价约 46.35 千元）。"""
    ebit = V * (P - C) / 10 + nonref - opex - impair
    return (ebit - net_interest) * (1 - tax) * (1 - mi) + assoc


def main() -> None:
    print(f"市值 {fmt(MCAP)} 亿元（{PRICE} 元 × {SHARES} 亿股）")
    print(f"有息负债 {fmt(DEBT)}；经调整净现金（无杠杆口径）{fmt(NET_CASH_ADJ)} 亿元；"
          f"其中财务公司存款 {BS['fc_deposit']}、贷款 {BS['fc_loan']}（关联方，单列）")
    print(f"净负债税后利息现值（9%）{fmt(-NET_CASH_ADJ * R_DEBT * (1 - TAX_SHIELD) / COE)} 亿元")
    print(f"中巨芯持股 {ZJX_SHARES:.3f} 亿股，市值 {fmt(ZJX_SHARES * ZJX_PRICE)} 亿元，账面 {ZJX_BOOK}")
    print()
    rows = {}
    for n in ("bear", "base", "bull"):
        res = value_scenario(n)
        rows[n] = res
        no = res["nonop"]
        c = res["core"]
        g = res["gansu"]
        print(f"[{n}] 概率 {PROB[n]:.2f}")
        print(f"  2026 正常化：制冷剂毛利 {fmt(c['norm2026']['ref_gp'])}，核心 EBIT {fmt(c['norm2026']['ebit'])}，"
              f"归母 NOPAT {fmt(c['norm2026']['nopat_parent'])}，归母净利（报表口径）{fmt(normalized_np_2026(n))}")
        print(f"  2026H2 核心所有者收益 {fmt(c['2026H2']['oe'])}；甘肃 2026H2 {fmt(g['2026H2']['oe_parent'])}")
        print("  年份  核心归母NOPAT  核心OE  甘肃NOPAT(100%)  甘肃OE(母)  合计OE")
        for y in YEARS:
            tot = c[y]["oe"] + g[y]["oe_parent"]
            print(f"  {y}  {c[y]['nopat_parent']:12.2f}  {c[y]['oe']:7.2f}  {g[y]['nopat']:14.2f}  "
                  f"{g[y]['oe_parent']:10.2f}  {tot:7.2f}")
        print(f"  甘肃总投入 K={fmt(g['K'])}，稳态 NOPAT {fmt(g['nopat_ss'])}（100%）")
        print(f"  PV 核心显式 {fmt(res['pv_core_explicit'])} + 核心终值 {fmt(res['pv_core_tv'])} "
              f"+ 甘肃 {fmt(res['pv_gansu'])} + 非经营 {fmt(no['total'])} "
              f"(中巨芯 {fmt(no['zjx'])}, 财务公司 {fmt(no['fc'])}, iGas {fmt(no['igas'])}, "
              f"其他联营 {fmt(no['other_assoc'])}, 其他权益工具 {fmt(no['oei'])})")
        print(f"  有杠杆：− 利息现值 {fmt(res['pv_interest'])} → 股权 {fmt(res['eq_levered'])} 亿，"
              f"V = {res['v_levered']:.2f} 元；无杠杆：− 净负债 {fmt(res['net_debt'])} → "
              f"V = {res['v_unlevered']:.2f} 元；终值占经营价值 {res['tv_share']:.1%}")
        print()
    vw = weighted()
    vw_u = weighted(key="v_unlevered")
    print(f"加权 V（有杠杆口径）= {vw:.2f} 元；P/V = {PRICE / vw:.2f}")
    print(f"加权 V（无杠杆口径）= {vw_u:.2f} 元；P/V = {PRICE / vw_u:.2f}")
    for r in (0.08, 0.10):
        print(f"股权成本 {r:.0%}：加权 V = {weighted(r):.2f} 元（无杠杆 {weighted(r, 'v_unlevered'):.2f}）；"
              + "；".join(f"{n} {value_scenario(n, r)['v_levered']:.2f}" for n in ('bear', 'base', 'bull')))
    irr = implied_irr_base()
    print(f"现价隐含回报（基准情景、有杠杆口径）= {irr:.2%}")
    rd = reverse_dcf()
    print(f"反向 DCF：现价隐含核心价值 {fmt(rd['implied_core'])} 亿；以基准 2026 正常化归母 NOPAT "
          f"{fmt(rd['oe0'])} 亿为起点，隐含永续增速 {rd['g_perp']:.2%}；"
          f"或 10 年增速 {rd['g10']:.2%}（终值 2.5%）")
    print()
    for n in ("bear", "base", "bull"):
        print(f"正常化 2026 归母净利 {n}: {normalized_np_2026(n):.2f} 亿")
    # 进入各档的价格（V 不变）
    print(f"分档价格（V={vw:.2f}）：≤{0.75 * vw:.2f} 明显低估；≤{0.90 * vw:.2f} 温和低估；"
          f"≤{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")
    # 增长路径（基准，归母经营所有者收益 = 核心 NOPAT + 甘肃 NOPAT×70%，未扣增长性资本开支）
    b = rows["base"]
    base_np = [b["core"]["norm2026"]["nopat_parent"]] + [
        b["core"][y]["nopat_parent"] + GS_SHARE * b["gansu"][y]["nopat"] for y in range(2027, 2032)]
    growth = [base_np[i + 1] / base_np[i] - 1 for i in range(5)]
    print("基准增长路径（归母经营 NOPAT，2027-2031）：" + "，".join(f"{g:.1%}" for g in growth))
    reinv = (CORE_GROWTH_CAPEX["2026H2"] + CORE_GROWTH_CAPEX[2027] + CORE_GROWTH_CAPEX[2028]
             + GS_SHARE * sum(SCEN["base"]["gs_capex"]))
    cum_np = sum(base_np[1:])
    print(f"再投资（2026H2-2028 增长性资本开支，母公司口径）{fmt(reinv)} 亿；2027-2031 累计归母 NOPAT "
          f"{fmt(cum_np)} 亿；再投资率 {reinv / cum_np:.1%}；"
          f"增量回报（2031 相对 2026 正常化 NOPAT 增量 ÷ 再投资）{(base_np[5] - base_np[0]) / reinv:.1%}")
    gs_b = b["gansu"]
    print(f"甘肃项目（基准）：剩余资本开支母公司口径 {fmt(GS_SHARE * sum(SCEN['base']['gs_capex']))} 亿，"
          f"稳态 NOPAT 母公司口径 {fmt(GS_SHARE * gs_b['nopat_ss'])} 亿，对剩余投入的回报 "
          f"{GS_SHARE * gs_b['nopat_ss'] / (GS_SHARE * sum(SCEN['base']['gs_capex'])):.1%}")
    print()
    # 现价隐含的基准正常化制冷剂均价（其他参数不变）
    p_imp = solve(base_v_at_price, 30.0, 70.0, PRICE)
    print(f"现价隐含的基准正常化制冷剂均价：{p_imp * 1000:,.0f} 元/吨（不含税；2026H1 实际 45,521）")
    for p in (38.0, 40.0, 41.0, 45.0):
        print(f"  基准均价 {p * 1000:,.0f} 元/吨 → 基准 V {base_v_at_price(p):.2f} 元")
    # 证伪条件触发后的 V
    f1 = with_overrides({"base": {"P": 38.0}, "bull": {"P": 43.0}})
    f2 = with_overrides({"base": {"P": 41.0}, "bull": {"P": 46.0}, "bear": {"P": 34.5}})
    f3 = with_overrides({n: {"gs_capex": SCEN["bear"]["gs_capex"], "gs_roic": 0.02,
                             "gs_startup_loss": 4.0, "gs_g": -0.01} for n in SCEN})
    f4 = with_overrides({"base": {"P": 41.0, "V": 31.0}})
    f5 = with_overrides({n: {"zjx_mode": "fundamental"} for n in SCEN})
    f0 = with_overrides({"bear": {"P": 39.0}, "base": {"P": 47.0}, "bull": {"P": 52.0}})
    print(f"证伪触发后 V：F0 价格上行（熊/基/牛均价 39k/47k/52k）{f0:.2f}；"
          f"F1 价格下行（基准 38k、牛市 43k）{f1:.2f}；F2 配额放量（各情景均价 −2k）{f2:.2f}；"
          f"F3 甘肃按熊市参数 {f3:.2f}；F4 年报低于门槛（基准 41k、31 万吨）{f4:.2f}；"
          f"F5 中巨芯按基本面 {f5:.2f}")
    print(f"2026Q3 归母净利粗估（中值）{q3_2026_estimate():.2f} 亿；区间 "
          f"{q3_2026_estimate(V=7.6, P=46.3):.2f}～{q3_2026_estimate(V=8.6, P=47.3):.2f} 亿")
    h2 = b["core"]["2026H2"]
    np_2026e = 26.50 + (h2["ebit"] - 0.5) * (1 - SCEN["base"]["tax"]) * (1 - SCEN["base"]["mi"]) + 0.65
    print(f"2026E 报表归母净利（H1 实际 26.50 + 基准 H2 过渡期）约 {np_2026e:.1f} 亿")
    # 交叉验证
    ttm_np, eq_parent, div_ttm = 43.83, 220.59, 0.78
    cash_free = BS["cash"] + BS["wmp"] + BS["trading"] - BS["restricted"]
    ev = MCAP + DEBT - cash_free + 33.53 - (26.99 + 10.56)
    ebit_ttm = 59.19 + 1.62 - 1.42 - 0.04      # TTM 利润总额 + 财务费用 − 投资收益 − 公允价值变动
    print(f"交叉验证：PE(TTM) {MCAP / ttm_np:.1f}×；PE(2026 基准正常化) {MCAP / normalized_np_2026('base'):.1f}×；"
          f"PB {MCAP / eq_parent:.2f}×；股息率(TTM) {div_ttm / PRICE:.2%}；EV {fmt(ev)} 亿，EV/EBIT(TTM) "
          f"{ev / ebit_ttm:.1f}×，EV/EBIT(基准正常化) {ev / core_path(SCEN['base'])['norm2026']['ebit']:.1f}×")


if __name__ == "__main__":
    main()
