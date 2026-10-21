# -*- coding: utf-8 -*-
"""澜起科技（688008）独立估值：所有者收益 DCF（归母、无杠杆口径，经调整净现金为正）。

运行：python3 valuation.py
输入全部写在本脚本内；单位：亿元（金额）、亿股（股本）、元/股（价格与 V）。
来源页码见同目录上级 companies/688008_澜起科技.md 第九节。
"""

# ---------------------------------------------------------------- 快照
PRICE = 169.27                      # 2026-10-20 A 股收盘（含 0.20 元中期股息，10-23 除息）
SHARES = 12.20538021                # 总股本：A 11.44764521 + H 0.757735（dividend_20261017 第2页）
TREASURY = 0.12101362               # A 股回购专户（2026-10-16），用途为股权激励/维护价值，无拟注销
SHARES_EX_TREASURY = SHARES - TREASURY
COE = 0.09
COE_LOW, COE_HIGH = 0.08, 0.10
T0 = 0.197                          # 2026-10-20 至 2026-12-31 的年数（年中折现以此为起点）
HKD_CNY = 0.89                      # 港元兑人民币近似值，仅用于 H 股参考价换算
H_PRICE_HKD_REF = 289.60            # 第三方页面显示的前收（日期未标明，未经一手核实）

# ------------------------------------------- 2026E 产品级利润模型（报表口径，经常性）
# 互连类芯片收入：Q1 14.17、Q2 16.94（2026H1_report 第42页、2026Q1_report 第2页）、
# Q3 20.47（forecast_20261021 第2页）、Q4 估计 21.90（公司称四季度需求进一步提升，取环比 +7%）
IC_Q = [14.17, 16.94, 20.47, 21.90]
IC_GM_Q = [0.715, 0.674, 0.6825, 0.685]   # Q1 71.5%、Q2 67.4%、Q3 预告 68.0~68.5% 取中、Q4 估计
NEW_Q = [2.69, 2.69, 2.90, 3.10]          # 四款新品（MRCD/MDB、PCIe Retimer、CKD、MXC）；Q3/Q4 为估计
JINDAI_REV, JINDAI_GM = 3.05, 0.10        # 津逮：Q1 0.42、Q2 1.81、Q3 0.32（20.79-20.47）、Q4 估 0.50
OPEX_2026 = 16.90   # 销售 1.25 + 管理 6.00（含股份支付约 3.9）+ 研发 9.60 + 税金及附加 0.05
OTHER_INC = 0.20    # 经常性其他收益
IMPAIR = -0.30      # 正常化存货/信用减值
EQUITY_METHOD = -0.20  # 联营企业权益法亏损（扣非口径内）
MINORITY_ADD = 1.10    # 横琴子公司（持股 44.88%）亏损由少数股东承担部分，归母口径加回
INTEREST_PRETAX_2026 = 4.05  # 利息收入：H1 2.05（2026H1_report 第162页）+ Q3/Q4 各约 1.0

IC_REV = sum(IC_Q)
NEW_REV = sum(NEW_Q)
CORE_REV = IC_REV - NEW_REV                      # DDR5 RCD/DB 与模组配套芯片
IC_GP = sum(r * g for r, g in zip(IC_Q, IC_GM_Q))
IC_GM = IC_GP / IC_REV


def op_np(core, new, gm, etr):
    """归母经营净利（不含利息、汇兑与一次性项目）。"""
    gp = (core + new) * gm + JINDAI_REV * JINDAI_GM
    ebit = gp - OPEX_2026 + OTHER_INC + IMPAIR + EQUITY_METHOD
    return ebit, ebit * (1 - etr) + MINORITY_ADD


EBIT_2026, OPNP_2026 = op_np(CORE_REV, NEW_REV, IC_GM, 0.08)   # 2026E 实际经常性（ETR 8%）
INT_AT_2026 = INTEREST_PRETAX_2026 * (1 - 0.08)
RECURRING_NP_2026 = OPNP_2026 + INT_AT_2026

# 正常化：按产品线与 AI 服务器内存周期折算（不用单季外推）
#   核心内存接口（量价）系数、新品系数、互连类毛利率、税率
NORM = {
    "bear": dict(core=0.78, new=0.85, gm=0.635, etr=0.10),
    "base": dict(core=0.90, new=1.00, gm=0.665, etr=0.09),
    "bull": dict(core=1.00, new=1.10, gm=0.685, etr=0.08),
}
NORM_OPNP, NORM_NP = {}, {}
for k, a in NORM.items():
    _, v = op_np(CORE_REV * a["core"], NEW_REV * a["new"], a["gm"], a["etr"])
    NORM_OPNP[k] = v
    NORM_NP[k] = v + INTEREST_PRETAX_2026 * (1 - a["etr"])

# ------------------------------------------------------ 经调整净现金与非经营资产
CASH = 151.10            # 货币资金（2026H1_report 第92页）
STRUCT_DEP = 25.25       # 交易性金融资产中的结构性存款（第127页）
RESTRICTED = 0.30        # 保函保证金受限（第62页）
DEBT = 1.07 + 0.21 + 0.15  # 长期借款 + 一年内到期非流动负债 + 租赁负债
DIV_PAYABLE = 4.72       # 2025 年末期股利，6-30 挂应付、7-29 已付
DIV_INTERIM = 2.42       # 2026 中期 0.20 元/股（A 2.265 + H 0.152），10-23 发放
BUYBACK_POST = 4.10      # 7-29 至 9-30 集中竞价回购支付（buyback_20261001 第1页）
OP_RESERVE = 10.0        # 经营备付：约一个季度现金经营支出（H1 经营现金流出 17.86）
NET_CASH_ADJ = (CASH + STRUCT_DEP - RESTRICTED - DEBT - DIV_PAYABLE - DIV_INTERIM
                - BUYBACK_POST - OP_RESERVE)
NONOP_BOOK = 3.92 + 3.73 + 0.25 + 2.63 + 3.71  # 权益类交易性资产、其他非流动金融资产、其他权益工具、联营、投资性房地产
NONOP = 0.85 * NONOP_BOOK                       # 扣 15%（处置税负与流动性）

# 2026 下半年经营净利：Q3 扣非中值 10.0 扣税后利息约 0.95；Q4 估 10.8 扣利息 0.95
H2_OPNP = (10.0 - 0.95) + (10.8 - 0.95)

# -------------------------------------------------------------- 三情景
SCEN = {
    "bear": dict(p=0.25, growth=[-0.28, 0.03, 0.10, 0.08, 0.07],
                 fade=[0.06, 0.05, 0.04, 0.03, 0.025], reinv=0.08, legal=40.0,
                 text="2027 年内存模组去库存叠加反垄断调查坐实、三家供应商转向价格竞争："
                      "经营净利较 2026E 降 28%，互连类毛利率回到约 63%；之后年增 7%~10%；"
                      "罚款与赔偿 40 亿元"),
    "base": dict(p=0.50, growth=[0.22, -0.10, 0.15, 0.13, 0.11],
                 fade=[0.10, 0.08, 0.06, 0.045, 0.03], reinv=0.12, legal=15.0,
                 text="2027 年新平台（16 通道、MRDIMM 二代、PCIe 6 Retimer）与服务器增长使经营净利"
                      "大致持平 2026Q4 年化水平（+22%），2028 年去库存 -10%，2029~2031 年 11%~15%；"
                      "互连类毛利率中枢 66%~67%；调查预期成本 15 亿元"),
    "bull": dict(p=0.25, growth=[0.30, 0.08, 0.22, 0.20, 0.18],
                 fade=[0.15, 0.12, 0.09, 0.06, 0.035], reinv=0.15, legal=5.0,
                 text="AI 推理带动服务器 CPU 与内存通道数持续上行，MRDIMM、DDR6、PCIe/CXL 放量："
                      "2027 年 +30%，2028 年仅小幅放缓，2029~2031 年 18%~22%；份额与毛利率维持；"
                      "调查无实质处罚"),
}
TERM_G = 0.025
RONIC = 0.25            # 终值期增量回报，终值再投资率 = g / RONIC = 10%
LEGAL_T = 1.70          # 罚款/赔偿现金流出时点（年，距估值日）


def paths(s, np0=None):
    x = OPNP_2026 if np0 is None else np0
    out = []
    for g in s["growth"] + s["fade"]:
        x *= 1 + g
        out.append(x)
    return out


def equity_value(s, r, np0=None, growth_override=None):
    ss = dict(s)
    if growth_override is not None:
        ss["growth"], ss["fade"] = growth_override[:5], growth_override[5:]
    nps = paths(ss, np0)
    pv = 0.0
    for k, n in enumerate(nps, start=1):
        pv += n * (1 - ss["reinv"]) / (1 + r) ** (T0 + k - 0.5)
    oe_next = nps[-1] * (1 + TERM_G) * (1 - TERM_G / RONIC)
    pv_tv = oe_next / (r - TERM_G) / (1 + r) ** (T0 + len(nps) - 0.5)
    h2 = H2_OPNP * (1 - ss["reinv"]) / (1 + r) ** 0.1
    legal = ss["legal"] / (1 + r) ** LEGAL_T
    eq = pv + pv_tv + NET_CASH_ADJ + NONOP + h2 - legal
    return dict(eq=eq, pv=pv, pv_tv=pv_tv, h2=h2, legal=legal, nps=nps)


def v_per_share(s, r, shares=SHARES):
    return equity_value(s, r)["eq"] / shares


def weighted(r, weights=None, shares=SHARES, legal_override=None):
    tot = 0.0
    for k, s in SCEN.items():
        ss = dict(s)
        if legal_override is not None:
            ss["legal"] = legal_override
        w = s["p"] if weights is None else weights[k]
        tot += w * equity_value(ss, r)["eq"] / shares
    return tot


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print("== 2026E 产品级经常性利润（报表口径）==")
    print(f"互连类收入 {IC_REV:.2f}（核心内存接口 {CORE_REV:.2f}，新品 {NEW_REV:.2f}），"
          f"综合毛利率 {IC_GM:.2%}；津逮 {JINDAI_REV:.2f}；营收约 {IC_REV + JINDAI_REV + 0.10:.1f}")
    print(f"经营 EBIT {EBIT_2026:.2f}；归母经营净利 {OPNP_2026:.2f}；税后利息 {INT_AT_2026:.2f}；"
          f"经常性归母净利 {RECURRING_NP_2026:.2f}")
    print("正常化 2026 归母净利（含净利息，剔除一次性）："
          + "，".join(f"{k} {NORM_NP[k]:.2f}（经营 {NORM_OPNP[k]:.2f}）" for k in ("bear", "base", "bull")))

    print("\n== 净现金与非经营资产 ==")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f}；非经营资产（账面 {NONOP_BOOK:.2f} 折 85%）{NONOP:.2f}；"
          f"2026H2 经营净利 {H2_OPNP:.2f}")

    print("\n== 三情景（股权成本 9%）==")
    res = {}
    for k, s in SCEN.items():
        e = equity_value(s, COE)
        res[k] = e
        v = e["eq"] / SHARES
        n = e["nps"]
        print(f"{k}: p={s['p']:.2f} V={v:.2f} 元/股；经营现值 {e['pv']:.1f} 终值现值 {e['pv_tv']:.1f}"
              f"（终值占经营价值 {e['pv_tv'] / (e['pv'] + e['pv_tv']):.0%}）；"
              f"经营净利 2027~2031 = {', '.join(f'{x:.1f}' for x in n[:5])}；2036 = {n[-1]:.1f}；"
              f"调查成本现值 {e['legal']:.1f}")
    vw = weighted(COE)
    pv_ratio = PRICE / vw
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv_ratio:.2f}（{band(pv_ratio)}）")
    vw_ex = weighted(COE, shares=SHARES_EX_TREASURY)
    print(f"剔除回购专户股份（{SHARES_EX_TREASURY:.4f} 亿股）：V = {vw_ex:.2f}，P/V = {PRICE / vw_ex:.2f}")
    print(f"价格含 0.20 元中期股息：除息口径 P/V = {(PRICE - 0.20) / vw:.2f}")

    print("\n== 股权成本敏感性 ==")
    for r in (COE_LOW, COE, COE_HIGH):
        print(f"r={r:.0%}: " + "，".join(f"{k} {v_per_share(s, r):.2f}" for k, s in SCEN.items())
              + f"；加权 {weighted(r):.2f}；P/V {PRICE / weighted(r):.2f}")

    # 现价隐含回报：基准情景现金流（含终值、净现金）使股权价值 = 市值
    mcap = PRICE * SHARES
    irr = solve(lambda r: equity_value(SCEN["base"], r)["eq"], 0.03, 0.30, mcap)
    print(f"\n现价隐含回报（基准情景）= {irr:.2%}")

    # 反向 DCF：2027~2036 十年恒定增速（再投资 12%，终值 2.5%）使 9% 下股权价值 = 市值
    g10 = solve(lambda g: equity_value(SCEN["base"], COE, growth_override=[g] * 10)["eq"],
                0.0, 0.60, mcap)
    np2036 = OPNP_2026 * (1 + g10) ** 10
    # 永续口径：以 2027E 基准经营所有者收益直接用戈登公式求永续增速
    oe27 = OPNP_2026 * 1.22 * (1 - 0.12)
    ev_ops = mcap - NET_CASH_ADJ - NONOP - H2_OPNP * 0.88 + SCEN["base"]["legal"] / (1 + COE) ** LEGAL_T
    g_perp = COE - oe27 / ev_ops
    print(f"反向 DCF：十年恒定增速 {g10:.1%}（2036 年经营净利约 {np2036:.0f} 亿元，"
          f"为 2026E 的 {np2036 / OPNP_2026:.1f} 倍）；永续增速口径 {g_perp:.2%}；"
          f"现价对应经营价值 {ev_ops:.0f} 亿元")

    # 再投资与增量回报（基准）
    b = res["base"]["nps"]
    cum_reinv = sum(x * SCEN["base"]["reinv"] for x in b[:5])
    inc_ret = (b[4] - OPNP_2026) / cum_reinv
    print(f"基准再投资率 {SCEN['base']['reinv']:.0%}，2027~2031 累计再投资 {cum_reinv:.1f}，"
          f"增量经营净利 {b[4] - OPNP_2026:.1f}，增量回报 {inc_ret:.0%}；终值再投资率 {TERM_G / RONIC:.0%}")

    print("\n== 交叉验证 ==")
    print(f"市值 {mcap:.0f}；EV（扣净现金、非经营资产）{mcap - NET_CASH_ADJ - NONOP:.0f}；"
          f"EV/2026E EBIT {(mcap - NET_CASH_ADJ - NONOP) / EBIT_2026:.1f}x；"
          f"市值/2026E 经常性归母 {mcap / RECURRING_NP_2026:.1f}x")
    print(f"股息率（过去 12 个月 0.59 元）{0.59 / PRICE:.2%}；回购收益率（过去 12 个月约 6.3 亿）"
          f"{6.3 / mcap:.2%}")
    h_cny = H_PRICE_HKD_REF * HKD_CNY
    print(f"H 股参考价 HK${H_PRICE_HKD_REF:.2f} ≈ {h_cny:.1f} 元，较 A 股溢价 {h_cny / PRICE - 1:.0%}，"
          f"按 H 股价 P/V = {h_cny / vw:.2f}")

    print("\n== 证伪条件触发后的 V（9%）==")
    f1 = weighted(COE, weights=dict(bear=0.60, base=0.40, bull=0.0))
    f2 = weighted(COE, weights=dict(bear=0.10, base=0.45, bull=0.45))
    f3 = weighted(COE, weights=dict(bear=0.40, base=0.50, bull=0.10), legal_override=40.0)
    f4 = weighted(COE, weights=dict(bear=0.50, base=0.50, bull=0.0))
    f5 = weighted(COE, legal_override=0.0)
    print(f"F1 2027H1 扣非 < 15 亿：V = {f1:.2f}")
    print(f"F2 2027H1 扣非 ≥ 24 亿且互连类毛利率 ≥ 67%：V = {f2:.2f}")
    print(f"F3 韩国或美国对公司提起指控/处罚：V = {f3:.2f}")
    print(f"F4 互连类毛利率连续两季 < 63%：V = {f4:.2f}")
    print(f"F5 调查结案且无处罚：V = {f5:.2f}")
    f25 = weighted(COE, weights=dict(bear=0.10, base=0.45, bull=0.45), legal_override=0.0)
    print(f"F2 与 F5 同时触发：V = {f25:.2f}")

    print("\n== V 不变时各档价格 ==")
    print(f"明显低估 ≤ {0.75 * vw:.1f}；温和低估 {0.75 * vw:.1f}~{0.90 * vw:.1f}；"
          f"大致合理 {0.90 * vw:.1f}~{1.10 * vw:.1f}；偏贵 > {1.10 * vw:.1f}")
