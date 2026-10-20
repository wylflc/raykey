#!/usr/bin/env python3
"""福耀玻璃（600660）独立估值：OI-291 池内独立审计 b08，价格日 2026-10-20。

运行：python3 valuation.py
打印：经调整净现金、2026 正常化归母净利三档、三情景 V（有杠杆口径与无杠杆口径对照）、
加权 V、P/V、8%／10% 股权成本下的 V、现价隐含回报、反向 DCF、交叉验证、
回撤对照、证伪触发后的 V。
金额单位：亿元；每股数据：元/股。输入全部写在脚本内，出处见注释。
"""

# ---------------------------------------------------------------------------
# 0. 快照
# ---------------------------------------------------------------------------
PRICE = 55.25                 # A 股 2026-10-20 收盘（腾讯日线）
A_SHARES = 20.02986332        # 亿股，dividend_20260917 第 2 页
H_SHARES = 6.06757200         # 亿股，总股本 26.09743532 − A 股；腾讯港股行情同
SHARES = 26.0974              # brief 口径总股本（A+H，无回购专户、无库存股）
H_PRICE_HKD = 55.35           # H 股 03606 2026-10-20 收盘（腾讯港股行情，联网查询）
USDCNY_1020 = 6.6781          # 2026-10-20（腾讯外汇行情，联网查询）
USDHKD = 7.80                 # 联系汇率区间 7.75–7.85 中值附近，仅用于 H 股参考价折算
COE = 0.09
T_Q4 = 0.11                   # 2026Q4 现金流取 2026-11-30，距价格日约 0.11 年
T_2027 = 0.70                 # 2027 年现金流取年中 2027-07-01，距价格日约 0.70 年

# ---------------------------------------------------------------------------
# 1. 2026-09-30 资产负债（2026Q3_report 第 4–7、10 页）与经调整净现金
# ---------------------------------------------------------------------------
CASH = 215.2031               # 货币资金
CASH_EQ = 214.8712            # 期末现金及现金等价物；差额 0.33 视为受限或三个月以上定期
TRADING_FA = 10.0954          # 交易性金融资产：保本结构性存款约 10.0 + 债务重组所得股票
DEBT = {
    "短期借款": 98.4875,
    "长期借款": 50.8124,
    "应付债券 MTN001-004 (3+5+4+3)": 14.9976,
    "一年内到期的非流动负债": 37.0981,
    "租赁负债": 2.9792,
    # 超短融不在东财「有息负债」口径里，列在其他流动负债 20.84 内：
    # SCP001 5.5 + SCP002 3 + SCP003 5（2026H1_report 第 35–36 页）+ SCP004 6.5（推算：
    # 前三季度「收到其他与筹资活动有关的现金」35.0 − 上半年 16.5 − 三季度 MTN003 4、MTN004 3、SCP003 5）
    "超短期融资券（其他流动负债内）": 20.0,
    "衍生金融负债": 0.0461,
}
DIV_PAYABLE = 6.8966          # 应付股利（H 股中期股利等，已宣派未付；第 6 页）
OP_RESERVE = 15.0             # 经营备付：约 TTM 营收 466 亿的 3%
RELATED_PARTY_DEPOSIT = 0.0   # 无关联财务公司，无关联方存款
NON_OP_ASSETS = 3.9093 + 0.8834   # 长期股权投资 + 其他权益工具投资
DEBT_RATE = 0.0167            # 有息负债实际平均利率：2026H1 利息支出 1.58 + 租赁利息 0.07（含资本化 0.36），
                              # 年化 3.30 ÷ 平均有息负债约 198（2026H1_report 第 110、14–15 页）
TAX_SHIELD = 0.15             # 母公司与主要境内子公司高新技术企业税率

cash_like = CASH_EQ + TRADING_FA
gross_debt = sum(DEBT.values())
net_cash_reported = CASH + TRADING_FA - gross_debt
net_cash_adj = cash_like - gross_debt - DIV_PAYABLE - OP_RESERVE   # 无杠杆口径经调整净现金
adj_net_debt = max(0.0, -net_cash_adj)

# ---------------------------------------------------------------------------
# 2. 2026 正常化（剔除汇兑、非经常性损益、IEEPA 关税退回；税率正常化）
# ---------------------------------------------------------------------------
PRETAX_9M = 71.2497           # 2026Q3_report 第 8 页
FX_LOSS_9M = 10.6698          # 第 2 页：1–9 月汇兑损失 106,698.17 万元
NONREC_PRETAX_9M = (-0.0629 + 1.8263 + 0.2308 - 0.8871)   # 第 2 页非经常性损益税前合计 1.107
IEEPA_H1 = 0.0067 * 219.711   # IR_20260826 第 1 页：美国海关退回 IEEPA 关税贡献上半年毛利率 0.67pp
NET_INT_9M = 6.1636 - 1.9515  # 第 7 页：利息收入 − 利息费用
MINORITY = 0.035              # 少数股东损益（前三季度 0.026）

PRETAX_Q4_25 = 111.6168 - 85.7714   # 2025 年报利润总额 − 2025 前三季度（2026Q3_report 第 8 页上年同期）
FX_GAIN_Q4_25 = 2.9752 - 4.8056     # 2025 汇兑收益 2.98（年报财务费用附注）− 前三季度 4.81 → Q4 损失 1.83
NET_INT_Q4_25 = (8.6884 - 3.2141) - (7.0349 - 2.4891)   # 2025 全年净利息 − 前三季度净利息
NONREC_PRETAX_Q4_25 = 0.07          # 2025 全年非经常 1.476 − 前三季度 1.42（税后）≈0.06，折税前约 0.07

adj_pretax_9m = PRETAX_9M + FX_LOSS_9M - NONREC_PRETAX_9M - IEEPA_H1
op_pretax_9m = adj_pretax_9m - NET_INT_9M
op_pretax_q4_25 = PRETAX_Q4_25 - FX_GAIN_Q4_25 - NONREC_PRETAX_Q4_25 - NET_INT_Q4_25

# 汇兑敞口估算：前三季度美元兑人民币 6.9890→6.7053（−4.06%），欧元 8.2071→7.6175（−7.18%）
# （每日经济新闻 2026-10-20 转引）；损失 10.67 亿 ⇒ 每 1% 美元波动约 2 亿元税前
FX_SENS_PER_PCT = 2.0

SCEN = {
    # q4g：2026Q4 经营性税前利润同比（三季度同口径约 −4.7%）；adj：全年税前额外调整；
    # netint：正常化净利息（税前）；etr：正常化税率；g：2027–2031 经营性归母净利增速；
    # roiic：显性期增量回报（再投资率 = 次年增速 ÷ roiic）；tg / ronic：终值增速与终值增量回报
    "bear": dict(p=0.25, q4g=-0.08, adj=-3.0, netint=4.0, etr=0.170,
                 g=[0.02, 0.04, 0.04, 0.035, 0.03], roiic=0.12, tg=0.020, ronic=0.12,
                 note="纯碱与天然气回升（税前 −3 亿）、出口退税取消与美国关税成本难转嫁、人民币续升；"
                      "增速 2–4%，新产能只赚 12%"),
    "base": dict(p=0.50, q4g=-0.04, adj=0.0, netint=5.4, etr=0.165,
                 g=[0.075, 0.075, 0.065, 0.055, 0.045], roiic=0.20, tg=0.025, ronic=0.18,
                 note="汇兑归零、毛利率维持 2026 前三季度水平；份额与单车价值量驱动 7.5% 增长后逐年回落"),
    "bull": dict(p=0.25, q4g=0.00, adj=1.0, netint=5.4, etr=0.160,
                 g=[0.12, 0.11, 0.10, 0.09, 0.07], roiic=0.28, tg=0.025, ronic=0.22,
                 note="美国二期满产、出口退税逐步转嫁、高附加值占比续升，回到 2017–2025 年 11–14% 的复合增速"),
}
YEARS = [2027, 2028, 2029, 2030, 2031]

# 历史投入资本回报（f10 资产负债表与利润表；经营投入资本 = 固定资产+在建+无形+商誉+使用权+长期待摊
# + 经营营运资本 − 递延收益 − 其他非流动负债；NOPAT = 营业利润 + 财务费用 − 投资与公允价值收益，税率 16.5%）
ROIC_HIST = {2019: (228.7, 28.3), 2021: (222.2, 36.7), 2022: (241.9, 38.9), 2023: (268.6, 51.0),
             2024: (318.9, 70.9), 2025: (358.9, 86.8)}
IC_20260930 = 377.0

# 回撤对照（腾讯日线；沪深 300 为联网查询）
DRAWDOWN = [("2025-10-09", 71.88, 4709.48), ("2025-10-16", 66.88, 4618.42),
            ("2025-12-31", 64.77, 4629.94), ("2026-03-24", 55.70, 4474.72),
            ("2026-06-25", 48.01, 5020.10), ("2026-09-30", 53.58, 4357.62),
            ("2026-10-20", 55.25, 4152.11)]


def normalize(s):
    """返回 (2026 经营性归母, 2026 正常化归母（含净利息）, 2026Q4 经营性归母, 2026 经营性税前)。"""
    op_pretax = op_pretax_9m + op_pretax_q4_25 * (1 + s["q4g"]) + s["adj"]
    q4_op = op_pretax_q4_25 * (1 + s["q4g"]) + s["adj"] * 0.25
    op_np = op_pretax * (1 - s["etr"]) - MINORITY
    norm_np = (op_pretax + s["netint"]) * (1 - s["etr"]) - MINORITY
    q4_np = q4_op * (1 - s["etr"]) - MINORITY / 4
    return op_np, norm_np, q4_np, op_pretax


def dcf(s, r, detail=False):
    """经营所有者收益现值（不含净利息；现金已在净负债里抵减）。"""
    op_np, _, q4_np, _ = normalize(s)
    g = s["g"]
    rr_q4 = g[0] / s["roiic"]
    pv = q4_np * (1 - rr_q4) / (1 + r) ** T_Q4
    rows = [("2026Q4", q4_np, rr_q4, q4_np * (1 - rr_q4), pv)]
    np_t = op_np
    for i, y in enumerate(YEARS):
        np_t *= (1 + g[i])
        last = i + 1 == len(g)
        rr = s["tg"] / s["ronic"] if last else g[i + 1] / s["roiic"]
        oe = np_t * (1 - rr)
        pv_i = oe / (1 + r) ** (T_2027 + i)
        pv += pv_i
        rows.append((str(y), np_t, rr, oe, pv_i))
    t_last = T_2027 + len(YEARS) - 1
    tv = np_t * (1 + s["tg"]) * (1 - s["tg"] / s["ronic"]) / (r - s["tg"])
    pv_tv = tv / (1 + r) ** t_last
    pv += pv_tv
    if detail:
        return pv, pv_tv, rows, tv
    return pv


def to_equity(pv, r, levered=True):
    if levered:
        # 有杠杆口径：经调整净负债按现规模滚动、不偿还本金，扣其税后利息现值（折现率同 r，基准 9%）
        return (pv - adj_net_debt * DEBT_RATE * (1 - TAX_SHIELD) / r + NON_OP_ASSETS) / SHARES
    return (pv + net_cash_adj + NON_OP_ASSETS) / SHARES


def equity_value(s, r, levered=True):
    return to_equity(dcf(s, r), r, levered)


def weighted(r, levered=True, probs=None):
    probs = probs or {k: v["p"] for k, v in SCEN.items()}
    return sum(probs[k] * equity_value(SCEN[k], r, levered) for k in SCEN)


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


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def reverse_const_growth(g10, base):
    """10 年恒定增速（2027–2036），再投资率 = g ÷ 显性期增量回报，之后按基准终值假设。"""
    op_np, _, q4_np, _ = normalize(base)
    pv = q4_np * (1 - g10 / base["roiic"]) / (1 + COE) ** T_Q4
    np_t = op_np
    for i in range(10):
        np_t *= (1 + g10)
        rr = base["tg"] / base["ronic"] if i == 9 else g10 / base["roiic"]
        pv += np_t * (1 - rr) / (1 + COE) ** (T_2027 + i)
    tv = np_t * (1 + base["tg"]) * (1 - base["tg"] / base["ronic"]) / (COE - base["tg"])
    pv += tv / (1 + COE) ** (T_2027 + 9)
    return to_equity(pv, COE)


def reverse_perpetual(gp, base):
    """永续增速：再投资率 = g ÷ 终值增量回报。"""
    op_np = normalize(base)[0]
    oe1 = op_np * (1 + gp) * (1 - gp / base["ronic"])
    pv = oe1 / (COE - gp) / (1 + COE) ** (T_2027 - 0.5)
    return to_equity(pv, COE)


def main():
    mcap = PRICE * SHARES
    hkdcny = USDCNY_1020 / USDHKD
    h_rmb = H_PRICE_HKD * hkdcny
    print("=" * 78)
    print("福耀玻璃 600660  价格日 2026-10-20  A 股 %.2f 元  总股本 %.4f 亿股（A %.4f + H %.4f）"
          % (PRICE, SHARES, A_SHARES, H_SHARES))
    print("市值口径：A 股价 × 全部股份 = %.1f 亿元（登记口径）" % mcap)
    print("  H 股参考：%.2f 港元 × %.4f = %.2f 元，较 A 股折价 %.1f%%（A/H 溢价 %.1f%%）；"
          "按两地实价合计市值 %.1f 亿元"
          % (H_PRICE_HKD, hkdcny, h_rmb, (1 - h_rmb / PRICE) * 100, (PRICE / h_rmb - 1) * 100,
             A_SHARES * PRICE + H_SHARES * h_rmb))

    print("\n[1] 2026-09-30 经调整净现金")
    print("  现金类：货币资金 %.2f + 交易性金融资产 %.2f = %.2f；受限/定期差额 %.2f"
          % (CASH, TRADING_FA, CASH + TRADING_FA, CASH - CASH_EQ))
    for k, v in DEBT.items():
        print("    有息负债 %-32s %7.2f" % (k, v))
    print("  有息负债合计 %.2f（数据包东财口径 204.42 未含超短融 20.0）" % gross_debt)
    print("  现金类 − 有息负债 = %.2f；扣应付股利 %.2f、经营备付 %.1f、受限 %.2f"
          % (net_cash_reported, DIV_PAYABLE, OP_RESERVE, CASH - CASH_EQ))
    print("  经调整净现金 net_cash_adj = %.2f 亿元（为负，按框架用有杠杆口径）；关联方存款 %.1f"
          % (net_cash_adj, RELATED_PARTY_DEPOSIT))
    print("  有杠杆口径扣除：%.2f × %.2f%% × (1−%.0f%%) ÷ 9%% = %.2f 亿元；非经营资产 %.2f"
          % (adj_net_debt, DEBT_RATE * 100, TAX_SHIELD * 100,
             adj_net_debt * DEBT_RATE * (1 - TAX_SHIELD) / COE, NON_OP_ASSETS))

    print("\n[2] 2026 正常化")
    print("  前三季度：利润总额 %.2f + 汇兑损失 %.2f − 非经常 %.2f − IEEPA 关税退回 %.2f = %.2f；"
          "减净利息 %.2f → 经营性税前 %.2f"
          % (PRETAX_9M, FX_LOSS_9M, NONREC_PRETAX_9M, IEEPA_H1, adj_pretax_9m, NET_INT_9M, op_pretax_9m))
    print("  2025Q4 经营性税前 %.2f（利润总额 %.2f，汇兑 %.2f，净利息 %.2f）"
          % (op_pretax_q4_25, PRETAX_Q4_25, FX_GAIN_Q4_25, NET_INT_Q4_25))
    norm = {}
    for k, s in SCEN.items():
        op_np, norm_np, q4_np, op_pretax = normalize(s)
        norm[k] = (op_np, norm_np, op_pretax)
        print("  %-4s 经营性税前 %.2f → 经营性归母 %.2f；正常化归母（含净利息 %.1f）%.2f；2026Q4 经营性归母 %.2f"
              % (k, op_pretax, op_np, s["netint"], norm_np, q4_np))
    q4_rep = normalize(SCEN["base"])[2] + (5.4 - NET_INT_9M) * 0.835 \
        - FX_SENS_PER_PCT * (1 - USDCNY_1020 / 6.7053) * 100 * 0.85 + 0.3
    print("  2026 年报归母预估（基准，Q4 计入 9-30 至 10-20 的汇兑损失约 %.1f 亿）：%.1f 亿元"
          % (FX_SENS_PER_PCT * (1 - USDCNY_1020 / 6.7053) * 100, 60.0648 + q4_rep))
    print("  汇兑敞口：前三季度美元 −4.06%%、欧元 −7.18%% 对应损失 %.2f 亿 → 每 1%% 美元波动约 %.1f 亿税前"
          % (FX_LOSS_9M, FX_SENS_PER_PCT))

    print("\n[3] 三情景所有者收益 DCF（股权成本 9%，经营性归母口径）")
    res = {}
    for k, s in SCEN.items():
        pv, pv_tv, rows, tv = dcf(s, COE, detail=True)
        v_lev, v_unlev = to_equity(pv, COE, True), to_equity(pv, COE, False)
        res[k] = (v_lev, v_unlev, pv_tv / pv)
        print("  %s（概率 %.2f）：%s" % (k, s["p"], s["note"]))
        print("    年份     归母净利  再投资率  所有者收益   现值")
        for y, npv, rr, oe, pvi in rows:
            print("    %-7s %8.2f   %5.1f%%   %8.2f   %7.2f" % (y, npv, rr * 100, oe, pvi))
        print("    终值 %.1f（g=%.1f%%，终值再投资率 %.1f%%），终值现值 %.1f，占经营现值 %.1f%%"
              % (tv, s["tg"] * 100, s["tg"] / s["ronic"] * 100, pv_tv, pv_tv / pv * 100))
        print("    增速 %s；显性期增量回报 %.0f%%，终值增量回报 %.0f%%"
              % ("/".join("%.1f%%" % (x * 100) for x in s["g"]), s["roiic"] * 100, s["ronic"] * 100))
        print("    V 有杠杆 = %.2f 元（P/V %.3f）；V 无杠杆 = %.2f 元（P/V %.3f）"
              % (v_lev, PRICE / v_lev, v_unlev, PRICE / v_unlev))

    vw = weighted(COE, True)
    vw_u = weighted(COE, False)
    v8, v10 = weighted(0.08, True), weighted(0.10, True)
    print("\n[4] 加权与敏感性")
    print("  加权 V（有杠杆口径，登记用）= %.2f 元；P/V = %.3f → %s" % (vw, PRICE / vw, band(PRICE / vw)))
    print("  加权 V（无杠杆口径对照）   = %.2f 元；P/V = %.3f" % (vw_u, PRICE / vw_u))
    print("  H 股参考价 %.2f 元 ÷ 加权 V = %.3f" % (h_rmb, h_rmb / vw))
    print("  剔除回购专户：无回购专户股份，V 不变")
    print("  股权成本 8%%：加权 V = %.2f（熊 %.2f／基 %.2f／牛 %.2f）"
          % (v8, *(equity_value(SCEN[k], 0.08) for k in SCEN)))
    print("  股权成本 10%%：加权 V = %.2f（熊 %.2f／基 %.2f／牛 %.2f）"
          % (v10, *(equity_value(SCEN[k], 0.10) for k in SCEN)))
    irr = solve(lambda r: equity_value(SCEN["base"], r, True), 0.06, 0.14, PRICE)
    irr_w = solve(lambda r: weighted(r, True), 0.06, 0.14, PRICE)
    print("  现价隐含回报（基准情景所有者收益流）= %.2f%%；（三情景加权）= %.2f%%" % (irr * 100, irr_w * 100))

    base = SCEN["base"]
    g10 = solve(lambda g: reverse_const_growth(g, base), -0.05, 0.20, PRICE)
    gp = solve(lambda g: reverse_perpetual(g, base), -0.02, 0.085, PRICE)
    print("\n[5] 反向 DCF（9%%，起点 2026 经营性归母 %.2f，显性期增量回报 %.0f%%，终值 2.5%%／18%%）"
          % (norm["base"][0], base["roiic"] * 100))
    print("  现价隐含 2027–2036 经营性归母年增速 %.2f%%；或隐含永续增速 %.2f%%（再投资率 = g ÷ 18%%）"
          % (g10 * 100, gp * 100))

    print("\n[6] 交叉验证")
    print("  市值/2026 正常化归母（含净利息，基准 %.2f）= %.1f×；市值/经营性归母 %.2f = %.1f×"
          % (norm["base"][1], mcap / norm["base"][1], norm["base"][0], mcap / norm["base"][0]))
    ev = mcap - net_cash_adj
    print("  EV %.1f（市值 + 经调整净负债）÷ 2026 正常化 EBIT %.2f = %.1f×"
          % (ev, norm["base"][2], ev / norm["base"][2]))
    print("  股息率：过去 12 个月每股 2.20 元 → %.2f%%；无回购" % (2.20 / PRICE * 100))
    print("  PB %.2f×（归母权益 374.71）；2014–2025 年末 PB 2.3–5.6×，PE 11.0–46.3×（中位约 19×）"
          % (mcap / 374.71))
    for pe in (14, 16, 18, 20):
        print("    基准 2027 正常化归母（含净利息）%.1f × %d 倍 = %.2f 元"
              % (norm["base"][1] * 1.075, pe, norm["base"][1] * 1.075 * pe / SHARES))
    print("  ROIC（年末经营投入资本）：" + "；".join(
        "%d %.1f%%" % (y, n / ic * 100) for y, (ic, n) in ROIC_HIST.items()))
    d_nopat = ROIC_HIST[2025][1] - ROIC_HIST[2022][1]
    d_ic = ROIC_HIST[2025][0] - ROIC_HIST[2022][0]
    nopat26 = norm["base"][2] * (1 - 0.165)
    print("  2022→2025 增量 ROIC %.0f%%；2026 正常化 NOPAT %.1f ÷ 9-30 投入资本 %.0f = %.1f%%"
          % (d_nopat / d_ic * 100, nopat26, IC_20260930, nopat26 / IC_20260930 * 100))

    print("\n[7] 回撤对照（未复权，未含分红）")
    p0, i0 = DRAWDOWN[0][1], DRAWDOWN[0][2]
    for d, p, i in DRAWDOWN:
        print("  %s  福耀 %.2f（%+.1f%%）  沪深300 %.2f（%+.1f%%）" % (d, p, (p / p0 - 1) * 100, i, (i / i0 - 1) * 100))

    print("\n[8] V 不变时进入各档的价格（加权 V %.2f）" % vw)
    print("  明显低估 ≤ %.2f；温和低估 %.2f–%.2f；大致合理 %.2f–%.2f；偏贵 > %.2f"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    print("\n[9] 证伪触发后的独立 V（9%，有杠杆口径）")
    f1 = weighted(COE, True, {"bear": 0.5, "base": 0.4, "bull": 0.1})
    print("  F1 2026 年报经调整归母（扣非 + 汇兑税后 − IEEPA）< 84 亿：概率改 0.5/0.4/0.1 → V = %.2f" % f1)
    f1u = weighted(COE, True, {"bear": 0.1, "base": 0.5, "bull": 0.4})
    print("     反向：2027 年经调整归母 ≥ 100 亿（同比 ≥ 12%%）：概率改 0.1/0.5/0.4 → V = %.2f" % f1u)
    f2 = equity_value(SCEN["bear"], COE, True)
    print("  F2 2027 中报毛利率 < 36%%（2026H1 剔除 IEEPA 约 38.2%%）：取熊市情景 → V = %.2f" % f2)
    s3 = dict(SCEN["base"], g=[0.03, 0.035, 0.035, 0.03, 0.03], roiic=0.10)
    f3 = 0.5 * equity_value(s3, COE) + 0.25 * equity_value(SCEN["bear"], COE) + 0.25 * equity_value(SCEN["bull"], COE)
    print("  F3 2027 营收增速 < 4%% 且资本开支 ≥ 70 亿：基准改增速 3–3.5%%、增量回报 10%% → V = %.2f" % f3)
    us_np = 9.0                                   # 福耀美国 2025 年净利 8.84（年报第 33 页）
    us_cut = us_np * 0.5 * (vw * SHARES / norm["base"][1]) / SHARES
    print("  F4 美国对中资汽车零部件工厂设限或福耀美国 2027 净利 < 4.5 亿：扣美国业务一半价值 %.2f → V = %.2f"
          % (us_cut, vw - us_cut))
    one_off = FX_SENS_PER_PCT * 4 * 0.85 / SHARES            # 再升值 4% 的一次性汇兑损失（税后）
    structural = vw * 0.45 * 0.04                            # 海外约 45% 利润按 4% 折算缩水
    print("  F5 2027-06-30 美元兑人民币 < 6.40 且美元存款未压降：一次性 %.2f + 海外利润折算 %.2f → V = %.2f"
          % (one_off, structural, vw - one_off - structural))

    print("\n[10] json 字段")
    print("  normalized_parent_np_2026_yi: bear %.2f / base %.2f / bull %.2f"
          % (norm["bear"][1], norm["base"][1], norm["bull"][1]))
    print("  scenarios V: bear %.2f / base %.2f / bull %.2f；v_weighted %.2f；pv %.3f"
          % (res["bear"][0], res["base"][0], res["bull"][0], vw, PRICE / vw))
    print("  v_at_coe_8 %.2f；v_at_coe_10 %.2f；implied_irr %.4f；net_cash_adj %.2f；non_op %.2f；终值占比（基准）%.1f%%"
          % (v8, v10, irr, net_cash_adj, NON_OP_ASSETS, res["base"][2] * 100))


if __name__ == "__main__":
    main()
