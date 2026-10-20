#!/usr/bin/env python3
"""国电南瑞（600406）独立估值：所有者收益 DCF（归母、无杠杆，净现金为正）+ 反向 DCF + 交叉验证。

金额单位亿元，每股价值元/股。价格日 2026-10-20，现价 23.00 元。
最新定期报告 2026 年中报（三季报预约 2026-10-29）。输入全部写在本脚本内，出处见各常量注释
（`2026H1_report`、`2025_annual_report` 为公告逐页文本，页码为 PDF 物理页）。

运行：python3 valuation.py
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------- 市场与股本
PRICE = 23.00                 # 2026-10-20 收盘（腾讯日线）
SHARES = 80.3176              # 亿股，总股本（含回购专户），2026H1_report 第 9 页
TREASURY = (45_157_255 + 5_742_268) / 1e8  # 回购专户：旧方案 45,157,255 股（2026H1 第 55 页）+ 新方案截至 9-30 累计 5,742,268 股（buyback_20261012 第 1 页）；用于股权激励，不注销
COE = 0.09
VAL_DATE_TO_YE2026 = 72 / 365  # 2026-10-20 → 2026-12-31
MARKET_CAP = PRICE * SHARES

# ---------------------------------------------------------------- 已报告数据
REV_2025 = 662.29             # 2025_annual_report 第 26 页
NP_PARENT_2025 = 82.79
NP_PARENT_TTM = 83.99         # 截至 2026-06-30（数据包 TTM）
PARENT_EQUITY_H1 = 520.74     # 2026-06-30 归母权益，2026H1_report 第 61 页
REV_H1_2026 = 277.67          # 2026H1_report 第 22 页
NP_PARENT_H1_2026 = 30.73

# 经营 EBIT（剔除利息收入、理财/存单/结构性存款收益、公允价值变动，保留汇兑与远期合约损益、减值、其他收益）
#   = 营业利润 − (利息收入 − 利息费用) − (投资收益 + 公允价值变动收益)
# 由 f10 利润表逐期计算，见 HIST_EBIT
HIST = {  # 年度：营收, 营业利润, 利息收入, 利息费用, 投资收益, 公允价值变动
    2023: (516.55, 85.44, 5.36, 0.38, 0.07, 0.19),
    2024: (578.29, 91.19, 5.08, 0.29, 0.38, 1.48),
    2025: (662.29, 98.09, 3.03, 0.20, 1.89, 1.62),
    "2025H1": (242.43, 35.45, 1.60, 0.10, 1.07, 0.74),
    "2026H1": (277.67, 37.18, 0.56, 0.07, 1.17, 1.28),
}


def op_ebit(rev, op, ii, ie, inv, fv):
    return op - (ii - ie) - (inv + fv)


HIST_EBIT = {k: op_ebit(*v) for k, v in HIST.items()}
EBIT_H1_2026 = HIST_EBIT["2026H1"]          # 34.24
EBIT_H2_2025 = HIST_EBIT[2025] - HIST_EBIT["2025H1"]
REV_H2_2025 = REV_2025 - HIST["2025H1"][0]

# 财务收益（含结构性存款、大额存单、定期存款收益与利息收入，不含远期外汇合约与权益法收益）
#   2026H1：利息收入 0.556 + 理财 0.173 + 存单定存 0.923 + 结构性存款公允价值 1.128 = 2.78（2026H1 第 178～179 页）
FIN_INCOME_2026 = 5.60        # 全年估计（上半年 2.78 ×2，现金规模与收益率持平）
INT_EXPENSE_2026 = 0.15       # 上半年利息费用 0.072

# ---------------------------------------------------------------- 资产负债（2026-06-30）与期后调整
CASH_ITEMS = {
    "货币资金（扣受限 0.45）": 44.64 - 0.45,      # 2026H1 第 125～126 页；含中国电财存款 1.90
    "交易性金融资产（全部为银行结构性存款）": 145.63,  # 第 126 页
    "一年内到期的大额存单": 29.03,                # 第 144 页（一年内到期的长期应收款 10.75 为经营性，不计）
    "其他流动资产中的定期存款": 19.51,            # 第 145 页（留抵进项税等 16.0 不计）
    "其他非流动资产中的大额存单及定期存款": 32.74,  # 第 161 页；含中国电财定期存款 5.20（第 214 页）
}
RELATED_PARTY_DEPOSIT = 1.90 + 5.20   # 中国电力财务有限公司（国网控股的财务公司），单独列示，已含在上面
DEBT_ITEMS = {
    "短期借款": 4.46,
    "长期借款": 0.07,
    "一年内到期的非流动负债（含租赁）": 0.78,
    "租赁负债": 0.53,
}
DEBT_LIKE = {
    "长期应付款（企业发展专项资金）": 3.39,        # 第 170 页
    "应付股利（主要为南瑞继保自然人股东，分批支付）": 5.71,  # 第 167 页
    "2026 中期分红（9-29 发放，期后）": 12.21,     # dividend_20260922_725101 第 2 页：1,221,357,557 元
    "8～9 月回购已付现金（期后）": 1.31,           # buyback_20261012 第 1 页
    "经营备付（约 3% 营收）": 20.0,
}
MINORITY_EQUITY = 36.48
TOTAL_EQUITY = 557.22
MINORITY_CASH_SHARE = MINORITY_EQUITY / TOTAL_EQUITY   # 少数股东按权益占比分享净现金
NON_OPERATING = 0.39 + 0.50 + 0.68  # 其他权益工具投资（龙芯中科等）+ 长期股权投资 + 投资性房地产，按账面

GROSS_CASH = sum(CASH_ITEMS.values())
DEBT = sum(DEBT_ITEMS.values())
NET_CASH_CONSOL = GROSS_CASH - DEBT - sum(DEBT_LIKE.values())
NET_CASH_PARENT = NET_CASH_CONSOL * (1 - MINORITY_CASH_SHARE)

# ---------------------------------------------------------------- 营运资本与资本开支
# 窄口径营运资本 = 应收（票据+账款+应收款项融资）+ 存货 + 合同资产 − 应付（票据+账款）− 合同负债与预收 − 其他流动负债
NWC_YE2025 = 345.88 + 130.58 + 14.95 - 297.36 - 78.13 - 9.16      # 106.76
NWC_H1_2026 = 315.80 + 151.60 + 14.75 - 266.80 - 70.16 - 8.31     # 136.88（年中季节性高点）
DA_2026, DA_H1_2026 = 11.8, 4.22 + 1.10 + 0.11 + 0.38               # 折旧摊销：上半年 5.81
CAPEX_2026, CAPEX_H1_2026 = 21.0, 7.54   # 2026 计划固定资产投资 18.21（不含募投与租赁，2025_annual_report 第 42 页）+ 募投等约 2.8

# ---------------------------------------------------------------- 情景
SCEN = {
    "bear": dict(
        p=0.25, rev2026=720.0, h2_margin=0.130, tax=0.115, minority=0.065,
        growth=[0.06, 0.05, 0.04, 0.03, 0.03],
        margin=[0.125, 0.122, 0.119, 0.117, 0.115],
        nwc_k=0.18, netcapex=0.010, g=0.020, ronic=0.15,
        text="在手履约义务托住 2027 年营收 +6%，此后电网投资见顶、增速降至 3%；储能电芯涨价与海外 EPC 竞争压低毛利，"
             "经营 EBIT 利润率由 12.7% 降至 11.5%；新增营收的营运资本占用 18%；终值增长 2.0%、新增资本回报 15%",
    ),
    "base": dict(
        p=0.50, rev2026=735.0, h2_margin=0.139, tax=0.105, minority=0.065,
        growth=[0.10, 0.09, 0.08, 0.07, 0.06],
        margin=[0.132, 0.131, 0.130, 0.130, 0.130],
        nwc_k=0.14, netcapex=0.010, g=0.025, ronic=0.20,
        text="十五五电网投资年增约 6%、在手履约义务 592 亿（较年初 +25%）支撑 2027 年营收 +10%，此后逐年降 1 个百分点；"
             "海外与储能占比上升抵消规模效应，经营 EBIT 利润率稳定在 13.0%；营运资本占新增营收 14%；终值 2.5%、新增资本回报 20%",
    ),
    "bull": dict(
        p=0.25, rev2026=750.0, h2_margin=0.144, tax=0.100, minority=0.065,
        growth=[0.12, 0.11, 0.10, 0.09, 0.08],
        margin=[0.136, 0.139, 0.141, 0.142, 0.143],
        nwc_k=0.10, netcapex=0.010, g=0.025, ronic=0.25,
        text="特高压与柔直核准加速、海外年增 20% 以上且毛利回到 18% 以上、IGBT 与固态变压器放量，"
             "经营 EBIT 利润率回升至 14.3%；营运资本占新增营收 10%；终值 2.5%、新增资本回报 25%",
    ),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def normalized_np_2026(s):
    """2026 正常化归母净利（含净利息，剔除一次性项目）。"""
    ebit = EBIT_H1_2026 + (s["rev2026"] - REV_H1_2026) * s["h2_margin"]
    pbt = ebit + FIN_INCOME_2026 - INT_EXPENSE_2026
    return ebit, pbt * (1 - s["tax"]) * (1 - s["minority"])


def scenario_value(s, coe=COE):
    ebit26, np26 = normalized_np_2026(s)
    t, m = s["tax"], s["minority"]
    # 2026 下半年：经营 NOPAT + 折旧 − 资本开支 + 年中营运资本回落（年末营运资本按新增营收占用率外推）
    nwc_ye26 = NWC_YE2025 + s["nwc_k"] * (s["rev2026"] - REV_2025)
    ebit_h2 = ebit26 - EBIT_H1_2026
    fcf_h2 = (ebit_h2 * (1 - t) + (DA_2026 - DA_H1_2026) - (CAPEX_2026 - CAPEX_H1_2026)
              + (NWC_H1_2026 - nwc_ye26)) * (1 - m)
    pv = fcf_h2 / (1 + coe) ** VAL_DATE_TO_YE2026
    rows = []
    rev_prev, rev = s["rev2026"], s["rev2026"]
    nopat_prev = ebit26 * (1 - t)
    oe_list, nopat_list, reinv_list = [], [], []
    for i, yr in enumerate(YEARS):
        rev = rev_prev * (1 + s["growth"][i])
        nopat = rev * s["margin"][i] * (1 - t)
        reinv = s["nwc_k"] * (rev - rev_prev) + s["netcapex"] * rev
        oe = (nopat - reinv) * (1 - m)
        tt = VAL_DATE_TO_YE2026 + 0.5 + i
        pv += oe / (1 + coe) ** tt
        rows.append((yr, rev, s["margin"][i], nopat * (1 - m), reinv * (1 - m), oe))
        oe_list.append(oe); nopat_list.append(nopat); reinv_list.append(reinv)
        rev_prev, nopat_prev = rev, nopat
    nopat_next = nopat_prev * (1 + s["g"])
    tv = nopat_next * (1 - s["g"] / s["ronic"]) * (1 - m) / (coe - s["g"]) * (1 + coe) ** 0.5
    pv_tv = tv / (1 + coe) ** (VAL_DATE_TO_YE2026 + len(YEARS))
    op_value = pv + pv_tv
    equity = op_value + NET_CASH_PARENT + NON_OPERATING
    # 2026 全年所有者收益（年度口径，不含年中季节性营运资本回落），作增长路径起点
    oe26 = (ebit26 * (1 - t) - s["nwc_k"] * (s["rev2026"] - REV_2025) - s["netcapex"] * s["rev2026"]) * (1 - m)
    growth_oe = [oe_list[0] / oe26 - 1] + [oe_list[i] / oe_list[i - 1] - 1 for i in range(1, len(oe_list))]
    out = dict(v=equity / SHARES, v_ex_treasury=equity / (SHARES - TREASURY), equity=equity,
               op_value=op_value, pv_tv=pv_tv, tv_share=pv_tv / op_value, fcf_h2=fcf_h2,
               np26=np26, ebit26=ebit26, rows=rows, oe26=oe26, growth_oe=growth_oe)
    # 再投资率（2027～2031 再投资合计 ÷ NOPAT 合计）与增量回报（2027→2031 NOPAT 增量 ÷ 2027～2030 再投资合计）
    out["reinvest_rate"] = sum(reinv_list) / sum(nopat_list)
    out["incremental_return"] = (nopat_list[-1] - nopat_list[0]) / sum(reinv_list[:-1])
    return out


def weighted(coe=COE):
    return sum(SCEN[k]["p"] * scenario_value(SCEN[k], coe)["v"] for k in SCEN)


def solve(f, lo, hi, tol=1e-7):
    flo, fhi = f(lo), f(hi)
    assert flo * fhi < 0, (flo, fhi)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < tol:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def implied_irr(key="base"):
    """情景所有者收益流（含终值与净现金）现值等于现价的折现率；终值增长须低于折现率。"""
    lo = SCEN[key]["g"] + 0.002
    return solve(lambda r: scenario_value(SCEN[key], r)["v"] - PRICE, lo, 0.20)


def reverse_dcf():
    """现价隐含增长：以基准 2027 年所有者收益为起点，2028～2036 年按常数 g 增长，此后 2.5%（9% 折现）。"""
    b = scenario_value(SCEN["base"])
    oe27 = b["rows"][0][5]
    pv_h2 = b["fcf_h2"] / (1 + COE) ** VAL_DATE_TO_YE2026
    target_op = MARKET_CAP - NET_CASH_PARENT - NON_OPERATING - pv_h2

    def op_val(g):
        pv, oe = 0.0, oe27
        for i in range(10):
            if i > 0:
                oe *= 1 + g
            pv += oe / (1 + COE) ** (VAL_DATE_TO_YE2026 + 0.5 + i)
        tv = oe * (1 + 0.025) / (COE - 0.025) * (1 + COE) ** 0.5
        return pv + tv / (1 + COE) ** (VAL_DATE_TO_YE2026 + 10)

    g10 = solve(lambda g: op_val(g) - target_op, -0.10, 0.30)

    def perp(g):   # 永续口径：2027 所有者收益起永续增长
        return oe27 / (COE - g) * (1 + COE) ** 0.5 / (1 + COE) ** (VAL_DATE_TO_YE2026 + 1) - target_op

    gp = solve(perp, -0.05, 0.085)
    return g10, gp, oe27, target_op


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 历史经营 EBIT（剔除财务收益）与利润率")
    for k, v in HIST_EBIT.items():
        print(f"  {k}: EBIT {v:6.2f}  利润率 {v / HIST[k][0]:.2%}")
    print(f"  2025H2: EBIT {EBIT_H2_2025:.2f} 利润率 {EBIT_H2_2025 / REV_H2_2025:.2%}")
    print("== 经调整净现金（2026-06-30，含期后分红与回购）")
    for k, v in CASH_ITEMS.items():
        print(f"  + {k}: {v:.2f}")
    print(f"  现金类合计 {GROSS_CASH:.2f}（其中中国电财存款 {RELATED_PARTY_DEPOSIT:.2f}，单独列示）")
    for k, v in {**DEBT_ITEMS, **DEBT_LIKE}.items():
        print(f"  − {k}: {v:.2f}")
    print(f"  合并口径经调整净现金 {NET_CASH_CONSOL:.2f}；少数股东分享 {MINORITY_CASH_SHARE:.2%} → 归母 {NET_CASH_PARENT:.2f}；非经营资产 {NON_OPERATING:.2f}")
    print(f"  营运资本：2025 年末 {NWC_YE2025:.2f}，2026 年中 {NWC_H1_2026:.2f}")
    # 2025 年资本回报：经营 NOPAT ÷（总权益 + 有息负债 − 现金类）
    cash_ye25 = 73.23 - 0.71 + 171.70 + 6.13 + 22.01 + 39.88
    ic_ye25 = 526.46 + 38.13 + 5.89 - cash_ye25
    nopat25 = HIST_EBIT[2025] * (1 - 9.61 / 98.19)
    print(f"  2025 经营 NOPAT {nopat25:.1f}；经营投入资本 {ic_ye25:.1f}（现金类 {cash_ye25:.1f} 已扣）→ ROIC {nopat25 / ic_ye25:.1%}")

    print("== 情景")
    res = {}
    for k, s in SCEN.items():
        r = scenario_value(s)
        res[k] = r
        print(f"[{k}] p={s['p']:.2f}  2026 经营 EBIT {r['ebit26']:.2f}（利润率 {r['ebit26'] / s['rev2026']:.2%}）"
              f"  2026 正常化归母净利 {r['np26']:.2f}")
        h2_np = r["np26"] - NP_PARENT_H1_2026
        print(f"  2026 下半年归母净利 {h2_np:.2f}（2025 下半年 {NP_PARENT_2025 - 29.52:.2f}），其中三季度约 {h2_np * 19.03 / 53.27:.2f}"
              f"（按 2025 年三季度占下半年 35.7% 拆分）；2026 下半年归母自由现金流 {r['fcf_h2']:.2f}")
        for yr, rev, mg, nop, rei, oe in r["rows"]:
            print(f"  {yr}: 营收 {rev:7.1f}  EBIT 率 {mg:.1%}  归母 NOPAT {nop:6.2f}  再投资 {rei:5.2f}  所有者收益 {oe:6.2f}")
        print(f"  2026 全年所有者收益（年度口径）{r['oe26']:.2f}；所有者收益增速 2027～2031: "
              f"{', '.join(f'{x:.1%}' for x in r['growth_oe'])}；终值增长 {s['g']:.1%}")
        print(f"  再投资率 {r['reinvest_rate']:.1%}  增量回报 {r['incremental_return']:.1%}  终值占经营价值 {r['tv_share']:.1%}")
        print(f"  经营价值 {r['op_value']:.1f}  股权价值 {r['equity']:.1f}  V = {r['v']:.2f} 元/股"
              f"（剔除回购专户 {r['v_ex_treasury']:.2f}）  P/V {PRICE / r['v']:.3f}")
    vw = weighted()
    vw_ex = sum(SCEN[k]["p"] * res[k]["v_ex_treasury"] for k in SCEN)
    v8, v10 = weighted(0.08), weighted(0.10)
    irr = implied_irr()
    g10, gp, oe27, target = reverse_dcf()
    print("== 汇总")
    print(f"  加权 V = {vw:.2f} 元/股  P/V = {PRICE / vw:.3f}  → {verdict(PRICE / vw)}")
    print(f"  剔除回购专户 {TREASURY:.4f} 亿股：加权 V = {vw_ex:.2f}  P/V = {PRICE / vw_ex:.3f}")
    print(f"  股权成本 8%：加权 V = {v8:.2f}（P/V {PRICE / v8:.3f}）；10%：加权 V = {v10:.2f}（P/V {PRICE / v10:.3f}）")
    for k in SCEN:
        print(f"    {k}: 8% {scenario_value(SCEN[k], 0.08)['v']:.2f}  10% {scenario_value(SCEN[k], 0.10)['v']:.2f}")
    print(f"  现价隐含回报（基准情景）= {irr:.2%}；熊 {implied_irr('bear'):.2%}；牛 {implied_irr('bull'):.2%}")
    print(f"  反向 DCF：现价隐含 2028～2036 所有者收益年增 {g10:.2%}（起点 2027 年 {oe27:.1f}，此后 2.5%）；"
          f"或自 2027 年起永续增长 {gp:.2%}；需由经营资产支撑的市值 {target:.1f}")
    print("  分档价格（V 不变）：明显低估 ≤ {:.2f}；温和低估 ≤ {:.2f}；大致合理 ≤ {:.2f}；偏贵 > {:.2f}".format(
        0.75 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    print("== 交叉验证")
    dps_ttm = 0.475 + 0.153   # 过去 12 个月除息：0.475（6-30）+ 0.153（9-29）
    print(f"  市值 {MARKET_CAP:.1f}；PE(TTM) {MARKET_CAP / NP_PARENT_TTM:.1f}×；PE(2026 基准) {MARKET_CAP / res['base']['np26']:.1f}×；"
          f"PB {MARKET_CAP / PARENT_EQUITY_H1:.2f}×")
    fin_after = (FIN_INCOME_2026 - INT_EXPENSE_2026) * (1 - SCEN["base"]["tax"]) * (1 - SCEN["base"]["minority"])
    ex_cash_pe = (MARKET_CAP - NET_CASH_PARENT) / (res['base']['np26'] - fin_after)
    print(f"  扣净现金 PE(2026 基准经营利润) {ex_cash_pe:.1f}×；股息率(TTM {dps_ttm:.3f} 元) {dps_ttm / PRICE:.2%}")
    ev = MARKET_CAP + MINORITY_EQUITY * 3.0 - NET_CASH_CONSOL
    print(f"  EV（少数股东按 3 倍 PB 计）{ev:.0f}；EV/EBIT(2026 基准) {ev / res['base']['ebit26']:.1f}×")
    m = SCEN["base"]["minority"]
    ebit_parent = res["base"]["ebit26"] * (1 - m)
    mkt_op = MARKET_CAP - NET_CASH_PARENT - NON_OPERATING
    print(f"  归母口径 EV/EBIT(2026 基准)：市场 {mkt_op / ebit_parent:.1f}×（市值 − 归母净现金 − 非经营资产）；"
          f"基准情景经营价值 {res['base']['op_value'] / ebit_parent:.1f}×")

    print("== 证伪情景（触发后的 V）")
    trig = falsifier_values()
    for k, v in trig.items():
        print(f"  {k}: V = {v:.2f}")
    return res, vw


def falsifier_values():
    """证伪条件触发后的独立 V：按条件改写情景概率或参数。"""
    out = {}
    # F1：三季报单季归母 < 18.5 亿或 9 月末经营现金流累计 < 0 → 熊 50% / 基准 40% / 牛 10%
    vb, vs, vu = (scenario_value(SCEN[k])["v"] for k in ("bear", "base", "bull"))
    out["F1 三季报单季归母<18.5亿"] = 0.5 * vb + 0.4 * vs + 0.1 * vu
    # F2：2026 年报归母 < 81 亿或经营 EBIT 利润率 < 12.5% → 熊 70% / 基准 30%
    out["F2 2026 年报归母<81亿"] = 0.7 * vb + 0.3 * vs
    # F3：2026 年报信用减值损失 > 6 亿或经营现金流/归母 < 0.9 → 基准利润率每年再降 0.4 个百分点、营运资本占用 18%
    s = dict(SCEN["base"]); s["margin"] = [m - 0.004 for m in SCEN["base"]["margin"]]; s["nwc_k"] = 0.18
    out["F3 信用减值>6亿或现金流/归母<0.9"] = 0.25 * vb + 0.5 * scenario_value(s)["v"] + 0.25 * vu
    # F4：国网 2027 年计划投资低于 2026 年实际，或 2027-06-30 前新核准特高压直流 < 2 条 → 熊 45% / 基准 45% / 牛 10%
    out["F4 国网2027计划投资<2026实际"] = 0.45 * vb + 0.45 * vs + 0.10 * vu
    # F5（向上）：2026 新签合同 ≥ 900 亿且 2026 归母 ≥ 90 亿 → 熊 15% / 基准 40% / 牛 45%
    out["F5 新签≥900亿且归母≥90亿（向上）"] = 0.15 * vb + 0.4 * vs + 0.45 * vu
    return out


if __name__ == "__main__":
    main()
