#!/usr/bin/env python3
"""伟星股份（002003）独立估值（OI-291 b08，价格日 2026-10-20）。

方法：归母所有者收益 DCF（10 年显性期：前 5 年逐年给定，后 5 年线性降到终值增速），
所有者收益 = 归母经营净利 × (1 − g / 增量回报)；年中折现。
经调整净现金为负，按框架用有杠杆口径：经营价值 − 经调整净负债税后利息永续现值 + 非经营资产。
另报无杠杆口径对照、8%／10% 敏感性、反向 DCF、现价隐含回报、交叉验证与证伪触发后的 V。

运行：python3 valuation.py   （只用标准库，输入全部写在脚本内）
金额单位：亿元；每股：元。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 11.97                    # 2026-10-20 收盘，A 股未复权（brief）
SHARES = 11.8889                 # 亿股，总股本；无回购专户股份（库存股为限制性股票回购义务）
PRICE_DATE = date(2026, 10, 20)
COE = 0.09
COE_SENS = (0.08, 0.10)
PROBS = {"bear": 0.25, "base": 0.50, "bull": 0.25}
RESERVE_GRANT_SHARES = 0.03      # 第六期预留授予上限 300 万股（2025 年报第 50 页），10-09 董事会已审议，尚未登记

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report）
CASH = 12.1549                   # 货币资金，第 45、87 页
RESTRICTED_CASH = 0.0928         # 履约保函保证金，第 18、105 页
TTM_REVENUE = 51.22              # 数据包 TTM
OP_RESERVE = round(0.02 * TTM_REVENUE, 3)   # 经营备付按 TTM 营收 2%
DECLARED_UNPAID_DIV = 0.0        # 中报不分配，2025 年度股利已于 5 月派发
ST_LOAN = 13.1964                # 短期借款，第 46、106 页
LEASE_CURRENT = 0.1313           # 一年内到期的租赁负债，第 109 页
LEASE_LT = 0.1714                # 租赁负债，第 47、109 页
DEBT = ST_LOAN + LEASE_CURRENT + LEASE_LT
NON_OPERATING = 1.0327           # 长期股权投资（伟星光学、融汇环境，权益法），按账面，第 98 页
DEBT_RATE = 0.024                # 2026H1 利息费用 0.1386 亿年化 ÷ 平均借款约 11.7 亿
TAX_SHIELD = 0.16
NET_CASH_ADJ = CASH - RESTRICTED_CASH - OP_RESERVE - DECLARED_UNPAID_DIV - DEBT

# ---------------------------------------------------------------- 2026 正常化归母净利（三档）
# 结构：营收 × 核心经营利润率（毛利 − 税金及附加 − 销售 − 管理 − 研发，含股份支付）
#      + 经常性其他收益 − 信用减值常态 − 营业外常态 − 银行手续费 − 结构性汇兑拖累 − 净利息
#      → × (1 − 税率) + 联营投资收益 → × (1 − 少数股东占比)
# 2025 核对：核心经营利润 7.85（16.35%），其他收益 0.51，财务费用 0.66（含汇兑损失 0.354），利润总额 7.80。
NORM = {
    #        营收   核心利润率 其他收益 信用减值 营业外 手续费 汇兑拖累 净利息 联营  税率  少数
    "bear": dict(rev=52.8, m=0.153, oi=0.30, cl=0.10, no=0.02, fee=0.15, fx=0.35, ni=0.22, assoc=0.15, tax=0.16, mi=0.012),
    "base": dict(rev=53.7, m=0.166, oi=0.33, cl=0.05, no=0.02, fee=0.15, fx=0.15, ni=0.19, assoc=0.17, tax=0.16, mi=0.012),
    "bull": dict(rev=54.5, m=0.173, oi=0.35, cl=0.04, no=0.02, fee=0.15, fx=0.00, ni=0.17, assoc=0.18, tax=0.16, mi=0.012),
}


def normalized_np(p):
    pretax_ex_assoc = p["rev"] * p["m"] + p["oi"] - p["cl"] - p["no"] - p["fee"] - p["fx"] - p["ni"]
    np_total = pretax_ex_assoc * (1 - p["tax"]) + p["assoc"]
    parent = np_total * (1 - p["mi"])
    # DCF 用经营口径：加回税后净利息（净负债另行扣减），剔除联营收益（联营按账面列非经营资产）
    operating = parent + p["ni"] * (1 - p["tax"]) * (1 - p["mi"]) - p["assoc"] * (1 - p["mi"])
    return parent, operating


# 依据：2026H1 核心经营利润率 19.6%（上年同期 19.2%），2025 全年 16.35%，2021-2025 平均约 16.0%；
# 汇兑：2025 损失 0.354、2026H1 损失 0.372（人民币 1-9 月升值约 4.1%，三季度约 1.2%）；
# 原材料约占营业成本 52%（2025 年报第 17 页），LME 铜 2026-07-30 约 13,800 美元/吨、9 月创新高。

# ---------------------------------------------------------------- 增长与再投资
# 增量回报依据：2016-2025 约 14%、2021-2025 约 12%（重投入期，FA 周转 2.17→1.44）；
# 产能利用率 68.62%（境外 49.53%）、2026H1 资本开支同比 −39%，基准取 18%，熊 13%（≈历史），牛 24%。
SCEN = {
    # g5：2027-2031 归母经营净利增速；之后 5 年线性降到 gT；roiic：显性期增量回报；roiic_t：终值期
    "bear": dict(g5=[0.05, 0.05, 0.045, 0.04, 0.035], gT=0.020, roiic=0.13, roiic_t=0.12),
    "base": dict(g5=[0.09, 0.085, 0.08, 0.07, 0.06], gT=0.025, roiic=0.18, roiic_t=0.15),
    "bull": dict(g5=[0.11, 0.10, 0.09, 0.08, 0.07], gT=0.025, roiic=0.24, roiic_t=0.18),
}
FIRST_YEAR = 2027
STUB_YEARS = (date(2026, 12, 31) - PRICE_DATE).days / 365.0     # 价格日至年末的 2026 尾段


def growth_path(g5, gT):
    last = g5[-1]
    fade = [last + (gT - last) * (i + 1) / 5 for i in range(5)]
    return list(g5) + fade                                   # 10 年


def t_mid(year):
    return (date(year, 7, 1) - PRICE_DATE).days / 365.0


def dcf_operating(np0, s, r):
    """返回经营价值（价格日现值）与逐年明细。年中折现；终值 = 第 11 年所有者收益 / (r − gT)，
    以年中惯例折到最后一个显性年的年中时点。"""
    path = growth_path(s["g5"], s["gT"])
    rows, pv, np_t = [], 0.0, np0
    rr1 = path[0] / s["roiic"]
    stub = np0 * (1 - rr1) * STUB_YEARS                     # 2026 尾段所有者收益
    pv += stub / (1 + r) ** (STUB_YEARS / 2)
    for i, g in enumerate(path):
        y = FIRST_YEAR + i
        np_t *= 1 + g
        rr = g / s["roiic"]
        oe = np_t * (1 - rr)
        df = (1 + r) ** -t_mid(y)
        pv += oe * df
        rows.append((y, g, np_t, rr, oe, oe * df))
    np_T = np_t * (1 + s["gT"])
    oe_T = np_T * (1 - s["gT"] / s["roiic_t"])
    tv = oe_T / (r - s["gT"])
    pv_tv = tv * (1 + r) ** -t_mid(FIRST_YEAR + len(path) - 1)
    return pv + pv_tv, rows, tv, pv_tv, stub


def pv_debt_interest(r):
    """有杠杆口径：经调整净负债按现规模滚动、不还本，税后利息永续现值。"""
    if NET_CASH_ADJ >= 0:
        return 0.0
    return (-NET_CASH_ADJ) * DEBT_RATE * (1 - TAX_SHIELD) / r


def equity_value(op_value, r, levered=True):
    if levered and NET_CASH_ADJ < 0:
        return op_value - pv_debt_interest(r) + NON_OPERATING
    return op_value + NET_CASH_ADJ + NON_OPERATING


def per_share(eq, shares=SHARES):
    return eq / shares


def scenario_value(name, r=COE, levered=True, np_override=None, s_override=None):
    _, op_np = normalized_np(NORM[name])
    if np_override is not None:
        op_np = np_override
    s = dict(SCEN[name])
    if s_override:
        s.update(s_override)
    op_val, rows, tv, pv_tv, stub = dcf_operating(op_np, s, r)
    eq = equity_value(op_val, r, levered)
    return per_share(eq), dict(op_np=op_np, op_val=op_val, rows=rows, tv=tv, pv_tv=pv_tv, eq=eq, stub=stub)


def weighted(vals, probs=PROBS):
    return sum(vals[k] * probs[k] for k in probs)


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


def main():
    print("=" * 78)
    print("伟星股份 002003 独立估值  价格日 2026-10-20  现价 %.2f  总股本 %.4f 亿股  市值 %.2f 亿"
          % (PRICE, SHARES, PRICE * SHARES))
    print("=" * 78)

    print("\n[1] 经调整净现金（2026-06-30）")
    print("  货币资金 %.3f − 受限 %.3f − 经营备付 %.3f − 已宣派未付股利 %.3f − 有息负债 %.3f"
          % (CASH, RESTRICTED_CASH, OP_RESERVE, DECLARED_UNPAID_DIV, DEBT))
    print("  = 经调整净现金 %.3f 亿（为负 → 有杠杆口径）；非经营资产（联营账面）%.3f 亿" % (NET_CASH_ADJ, NON_OPERATING))
    print("  净负债税后利息 %.4f 亿/年，9%% 永续现值 %.3f 亿" % (-NET_CASH_ADJ * DEBT_RATE * (1 - TAX_SHIELD), pv_debt_interest(COE)))

    print("\n[2] 2026 正常化归母净利（含净利息、剔除一次性与周期性汇兑）")
    norm = {}
    for k in ("bear", "base", "bull"):
        parent, op = normalized_np(NORM[k])
        norm[k] = parent
        p = NORM[k]
        print("  %-4s 营收 %.1f  核心利润率 %.1f%%  汇兑拖累 %.2f  → 归母 %.2f 亿（净利率 %.1f%%）；经营口径 %.2f"
              % (k, p["rev"], p["m"] * 100, p["fx"], parent, parent / p["rev"] * 100, op))

    print("\n[3] 三情景（股权成本 9%，有杠杆口径）")
    vals, det = {}, {}
    for k in ("bear", "base", "bull"):
        v, d = scenario_value(k)
        vals[k], det[k] = v, d
        s = SCEN[k]
        print("  %-4s V = %.2f 元  (概率 %.0f%%)  经营价值 %.1f  终值现值 %.1f（占 %.0f%%）  ROIIC %.0f%%  gT %.1f%%"
              % (k, v, PROBS[k] * 100, d["op_val"], d["pv_tv"], d["pv_tv"] / d["op_val"] * 100,
                 s["roiic"] * 100, s["gT"] * 100))
    vw = weighted(vals)
    pv_ratio = PRICE / vw
    tier = ("明显低估" if pv_ratio <= 0.75 else "温和低估" if pv_ratio <= 0.90
            else "大致合理" if pv_ratio <= 1.10 else "偏贵或价值陷阱风险高")
    print("  加权 V = %.2f 元   P/V = %.3f → %s" % (vw, pv_ratio, tier))
    print("  V 不变时各档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    print("\n[4] 基准情景逐年（归母经营净利、再投资率、所有者收益）")
    print("  年份  增速    净利    再投资率  所有者收益  现值")
    d = det["base"]
    print("  2026尾段（%.2f 年）所有者收益 %.2f" % (STUB_YEARS, d["stub"]))
    for (y, g, npt, rr, oe, pv) in d["rows"]:
        print("  %d  %5.1f%%  %6.2f   %5.1f%%    %6.2f    %6.2f" % (y, g * 100, npt, rr * 100, oe, pv))
    print("  终值（2036 末）%.1f，现值 %.1f" % (d["tv"], d["pv_tv"]))
    rr5 = sum(r[3] for r in d["rows"][:5]) / 5
    print("  基准前 5 年平均再投资率 %.1f%%，增量回报 %.0f%%" % (rr5 * 100, SCEN["base"]["roiic"] * 100))

    print("\n[5] 口径对照与股本对照")
    unlev = {k: scenario_value(k, levered=False)[0] for k in vals}
    print("  无杠杆口径（全额扣经调整净负债）：熊 %.2f 基 %.2f 牛 %.2f 加权 %.2f，P/V %.3f"
          % (unlev["bear"], unlev["base"], unlev["bull"], weighted(unlev), PRICE / weighted(unlev)))
    print("  有杠杆口径（采用）：加权 %.2f，P/V %.3f" % (vw, pv_ratio))
    post = {k: scenario_value(k)[1]["eq"] for k in vals}
    vw_post = weighted({k: (post[k] + RESERVE_GRANT_SHARES * 4.72) / (SHARES + RESERVE_GRANT_SHARES) for k in post})
    print("  无回购专户股份，无需剔除；若预留 300 万股按 4.72 元登记：加权 V %.2f，P/V %.3f" % (vw_post, PRICE / vw_post))

    print("\n[6] 股权成本敏感性")
    sens = {}
    for r in COE_SENS:
        vs = {k: scenario_value(k, r=r)[0] for k in vals}
        sens[r] = weighted(vs)
        print("  r = %.0f%%：熊 %.2f 基 %.2f 牛 %.2f  加权 %.2f  P/V %.3f"
              % (r * 100, vs["bear"], vs["base"], vs["bull"], sens[r], PRICE / sens[r]))

    print("\n[7] 现价隐含回报（基准情景流，含终值与净负债利息流）")
    irr = solve(lambda r: scenario_value("base", r=r)[0], 0.05, 0.15, PRICE)
    print("  隐含折现率 = %.2f%%" % (irr * 100))

    print("\n[8] 反向 DCF（基准起点与增量回报）")
    base_s = SCEN["base"]

    def v_const10(g):
        s = dict(g5=[g] * 5, gT=0.025, roiic=base_s["roiic"], roiic_t=base_s["roiic_t"])
        _, op_np = normalized_np(NORM["base"])
        path_override = [g] * 10
        # 10 年恒定增速：直接把后 5 年也设为 g
        pv, np_t, r = 0.0, op_np, COE
        pv += op_np * (1 - g / s["roiic"]) * STUB_YEARS / (1 + r) ** (STUB_YEARS / 2)
        for i, gi in enumerate(path_override):
            np_t *= 1 + gi
            pv += np_t * (1 - gi / s["roiic"]) * (1 + r) ** -t_mid(FIRST_YEAR + i)
        oe_T = np_t * 1.025 * (1 - 0.025 / s["roiic_t"])
        pv += oe_T / (r - 0.025) * (1 + r) ** -t_mid(FIRST_YEAR + 9)
        return per_share(equity_value(pv, r))
    g10 = solve(v_const10, 0.0, 0.30, PRICE)
    print("  现价隐含 2027-2036 年归母净利（所有者收益同速）恒定增速 %.1f%%，之后 2.5%%（ROIIC 18%%/终值 15%%）" % (g10 * 100))

    def v_perp(g):
        _, op_np = normalized_np(NORM["base"])
        oe1 = op_np * (1 + g) * (1 - g / base_s["roiic_t"])
        return per_share(equity_value(oe1 / (COE - g), COE))
    gp = solve(v_perp, 0.0, 0.085, PRICE)
    print("  现价隐含永续增速 %.2f%%（自 2027 起单阶段，ROIIC 15%%）" % (gp * 100))

    print("\n[9] 交叉验证")
    mcap = PRICE * SHARES
    print("  市值/2026 基准正常化归母 = %.1f×；市值/TTM 归母 6.88 = %.1f×；PB 3.14" % (mcap / norm["base"], mcap / 6.88))
    nd_0630 = DEBT - CASH
    ebit26 = NORM["base"]["rev"] * NORM["base"]["m"] + 0.48 - 0.08
    print("  EV = 市值 + 账面净负债 %.2f − 联营 %.2f = %.1f；EV/2026E EBIT(%.2f) = %.1f×"
          % (nd_0630, NON_OPERATING, mcap + nd_0630 - NON_OPERATING, ebit26, (mcap + nd_0630 - NON_OPERATING) / ebit26))
    print("  过去 12 个月每股现金分红 0.50 元，股息率 %.2f%%；无回购（股权激励净增发 2,000 万股）" % (0.50 / PRICE * 100))
    print("  2016-2025 年末 PE 13.4～23.7（中位约 21）；PB 1.9～3.8")

    print("\n[10] 证伪触发后的独立 V（9%，有杠杆口径）")
    f = {}
    # F1：2026Q3 单季营收 < 13.60 亿或单季扣非 < 2.11 亿 → 上半年动能证伪，概率改为 40/50/10
    f["F1"] = weighted(vals, {"bear": 0.40, "base": 0.50, "bull": 0.10})
    # F2：2026 全年毛利率 < 40.5% 或 2027H1 < 41.0%（成本加成传导失效）→ 各情景核心利润率 −1.5pp
    vs = {}
    for k in vals:
        p = dict(NORM[k]); p["m"] -= 0.015
        _, op = normalized_np(p)
        vs[k] = scenario_value(k, np_override=op)[0]
    f["F2"] = weighted(vs)
    # F3：2026 营收 < 51.0 亿或 2027 营收增速 < 4% → 前 5 年增速各 −3pp
    vs = {}
    for k in vals:
        g5 = [max(g - 0.03, 0.0) for g in SCEN[k]["g5"]]
        vs[k] = scenario_value(k, s_override=dict(g5=g5))[0]
    f["F3"] = weighted(vs)
    # F4：2027 资本开支 > 9 亿且营收增速 < 10%（重资本扩张延续）→ 增量回报降 5pp
    vs = {}
    for k in vals:
        vs[k] = scenario_value(k, s_override=dict(roiic=SCEN[k]["roiic"] - 0.05,
                                                   roiic_t=SCEN[k]["roiic_t"] - 0.02))[0]
    f["F4"] = weighted(vs)
    # F5（反向，证伪「偏贵」）：2027 资本开支 ≤ 6.0 亿且营收增速 ≥ 10%、扣非增速 ≥ 12%
    #     → 增量回报各 +6pp（终值 +3pp），概率改为 15/50/35
    vs = {}
    for k in vals:
        vs[k] = scenario_value(k, s_override=dict(roiic=SCEN[k]["roiic"] + 0.06,
                                                   roiic_t=SCEN[k]["roiic_t"] + 0.03))[0]
    f["F5"] = weighted(vs, {"bear": 0.15, "base": 0.50, "bull": 0.35})
    for k, v in f.items():
        print("  %s：V = %.2f 元，P/V = %.3f" % (k, v, PRICE / v))

    print("\n[11] 2026 报告口径估计（三季报核对用，非估值输入）")
    # 单季核心经营利润 = 营收 − 营业成本 − 税金及附加 − 销售 − 管理 − 研发
    # 2025Q3：营收 12.948，核心 2.645（20.4%）；2025Q4：营收 11.678，核心 0.714（6.1%）
    # 2026Q3E：营收 +11%、毛利率 44.5%（2025Q3 45.2%，铜价创新高）、费用 3.48；汇兑损失约 0.14
    #   （人民币 7-9 月升值约 1.1%-1.2%；2026H1 升值约 2.7% 对应汇兑损失 0.372）
    q3_rev = 12.948 * 1.11
    q3_core = q3_rev * 0.445 - 3.48
    q3_pretax = q3_core + 0.12 + 0.05 - 0.01 - (0.08 - 0.02 + 0.04) - 0.14
    q3_parent = q3_pretax * (1 - 0.15) * (1 - 0.012)
    q4_rev = 11.678 * 1.09
    q4_core = q4_rev * 0.072
    q4_pretax = q4_core + 0.15 + 0.04 - 0.03 - 0.10
    q4_parent = q4_pretax * (1 - 0.16) * (1 - 0.012)
    fy_rev = 26.593 + q3_rev + q4_rev
    fy_parent = 4.131 + q3_parent + q4_parent
    print("  2026Q3E 营收 %.2f（+11%%）归母 %.2f（2025Q3 2.14）；Q4E 营收 %.2f 归母 %.2f"
          % (q3_rev, q3_parent, q4_rev, q4_parent))
    print("  2026E 营收 %.2f，归母 %.2f（券商 9 月预测 7.19～7.21），扣非约 %.2f；"
          "前三季度归母约 %.2f、扣非约 %.2f" % (fy_rev, fy_parent, fy_parent - 0.17,
                                            4.131 + q3_parent, 4.047 + q3_parent - 0.04))

    print("\n[汇总]")
    print("  熊 %.2f / 基 %.2f / 牛 %.2f（25/50/25）  加权 V %.2f  P/V %.3f  %s"
          % (vals["bear"], vals["base"], vals["bull"], vw, pv_ratio, tier))
    print("  V@8%% %.2f  V@10%% %.2f  隐含回报 %.2f%%  正常化归母 2026：%.2f / %.2f / %.2f"
          % (sens[0.08], sens[0.10], irr * 100, norm["bear"], norm["base"], norm["bull"]))


if __name__ == "__main__":
    main()
