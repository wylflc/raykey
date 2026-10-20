#!/usr/bin/env python3
"""春风动力（603129）独立估值：OI-291 b08 深度版。

运行：python3 valuation.py
金额单位亿元，每股价值单位元/股。输入全部写在脚本内，出处见注释
（文件名指 raw/603129/txt 下的公告逐页文本，页码为 PDF 物理页）。

方法：归母所有者收益 DCF（股权成本 9%，终值增长 2.5%），再投资率 = 次年增长 / 增量回报；
经调整净现金为正，用无杠杆口径；可转债逐情景取低（按面值全额扣除 vs 全部转股）；
已授予未行权的期权与限制性股票按库存股法计入摊薄。
"""

import math

# ---------------------------------------------------------------- 快照
PRICE = 275.90                 # 2026-10-20 收盘（brief.md）
SHARES = 1.53482763            # 亿股，2026-09-30 股本 153,482,763 股（2026Q3_report 第 8 页），无库存股
COE = 0.09
G_TERM = 0.025

# ---------------------------------------------------------------- 2026 前三季度实际（2026Q3_report 第 1-3、8-9 页）
REV_YTD = 209.4221
PBT_YTD = 25.8110
REFUND_PRETAX = 6.2394          # 美国 IEEPA 关税退税及利息，计入非经常性损益（第 3 页）
NR_PRETAX_YTD = -0.0287 + 0.2882 + 0.0143 + 0.0287 + REFUND_PRETAX   # 非经常性损益税前合计
FIN_EXP_YTD = 1.2698
INT_EXP_YTD = 0.3456
INT_INC_YTD = 2.6589
OTHER_FEES_YTD = 0.053          # 银行手续费，按 2026H1_report 第 132 页「其他」0.0352 年化
FX_LOSS_YTD = FIN_EXP_YTD - INT_EXP_YTD + INT_INC_YTD - OTHER_FEES_YTD   # 汇兑损失约 3.53
EBIT_YTD = PBT_YTD - NR_PRETAX_YTD + FX_LOSS_YTD - INT_INC_YTD + INT_EXP_YTD  # 剔除退税、其他非经常、汇兑与利息
# 历史可比 EBIT（利润总额 − 非经常性损益税前 + 汇兑损失 − 利息收入 + 利息费用）
# 2024/2025：2025_annual_report 第 5、90 页（利润总额）、第 7-8 页（非经常性损益）、第 158 页（财务费用）
EBIT_2025 = 18.7879 - (-0.0039 + 0.5483 + 0.0018 + 0.6109 + 0.1452) + 1.1920 - 3.0596 + 0.2767
EBIT_2024 = 16.2884 - (-0.0098 + 0.3417 + 0.0002 + 0.0240 + 0.0113 - 0.0045) - 1.3268 - 1.9735 + 0.1562
REV_2025, REV_2024 = 197.4558, 150.3806
# 2026H1：2026H1_report 第 5、58 页（利润总额 13.0260）、第 6-7 页（非经常性损益）、第 132 页（财务费用）
EBIT_H1_26 = 13.0260 - (-0.0302 + 0.1490 + 0.0114 + 0.0425) + 2.5632 - 1.4717 + 0.1752
REV_H1_26 = 133.8608
PARENT_NP_YTD = 20.2086
DEDUCT_NP_YTD = 15.5950
REFUND_AFTER_TAX = 4.3987       # 退税进展公告（2026-09-08）：累计 9,264.03 万美元，税后约 4.40 亿

# 四季度假设（季节性弱季；2025Q4 营收 48.49、EBIT 率约 2.5%，2024Q4 约 5.9%）
Q4_INT_INC = 1.10
Q4_INT_EXP = 0.18

# ---------------------------------------------------------------- 资产负债表 2026-09-30（2026Q3_report 第 6-8、12 页）
CASH = 142.6928
CCE_END = 141.8866              # 现金及现金等价物，差额为受限或非现金等价物
RESTRICTED = CASH - CCE_END
LEASE = 2.8329 + 0.4197         # 租赁负债 + 一年内到期的非流动负债（无银行借款）
TRADE_WC = (22.9349 + 2.8407 + 40.4701 + 2.2158) - (66.4388 + 65.9595 + 5.1836)  # 应收+应收款项融资+存货+预付 − 应付票据−应付账款−合同负债
NON_OP_ASSETS = 1.6512          # 其他权益工具投资（公允价值计量）；联营合营投资收益留在经营利润内
CB_FACE = 21.78763              # 春风转债面值（financing_20260703_664398 第 3 页）
CB_CONV_PRICE = 241.70          # 初始转股价，截至中报未调整（2026H1_report 第 52 页）
CB_SHARES = CB_FACE / CB_CONV_PRICE   # 亿股，约 901.4 万股
CB_BOOK = 21.7143               # 应付债券账面（负债成分）

# 经营备付：贸易营运资本浮存回到营收的 −18%（2020-2025 年末均值约 −20%，打折），另留 2% 营收的最低经营现金
FLOAT_NORMAL_RATIO = -0.18
MIN_CASH_RATIO = 0.02

# ---------------------------------------------------------------- 股权激励（incentive_20260919_624237 第 1-2、28、43 页；2026H1_report 第 127 页）
OPTIONS = [
    # (亿股, 行权或授予价)
    (0.023573, 97.95),   # 2024 年期权计划未行权部分：326.24 万份 − 已行权 90.51 万份；行权价 102.15 扣 2025 年每股派息 4.20
    (0.033215, 233.45),  # 2026 年计划首次授予期权 332.15 万份（10-20 授予）
    (0.004800, 145.91),  # 2026 年计划首次授予限制性股票 48 万股
]

# ---------------------------------------------------------------- 情景
SCEN = {
    "bear": dict(
        p=0.25, q4_rev=60.0, margin26=0.076, tax=0.15, minority=0.060,
        growth=[0.03, -0.02, 0.06, 0.06, 0.05, 0.05, 0.04, 0.035, 0.03, 0.025],
        margin=[0.070, 0.065, 0.068, 0.070, 0.072, 0.072, 0.072, 0.072, 0.072, 0.072],
        ronic=0.18, ronic_term=0.12,
        text="337 调查裁定侵权、UFORCE/ZFORCE 输美受阻一至两年；中国产品输美关税维持 25%+12.5%；"
             "极核电自停售、亏损延续；人民币继续升值。2027 年营收 +3%、2028 年 −2%，EBIT 率 6.5%～7.2%，"
             "增量回报 18%。"),
    "base": dict(
        p=0.50, q4_rev=63.0, margin26=None, tax=0.135, minority=0.055,
        growth=[0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.025],
        margin=[0.081, 0.082, 0.083, 0.083, 0.083, 0.083, 0.083, 0.083, 0.083, 0.083],
        ronic=0.30, ronic_term=0.15,
        text="营收 2027 年 +15% 后逐年放缓至 2.5%；EBIT 率 8.1%～8.3%，略低于 2024～2026 年正常化中枢 8.2%～8.5%"
             "（汇兑与退税剔除，现行关税已含，扣新增股份支付约 1 亿）；税率 13.5%，少数股东 5.5%；增量回报 30%。"),
    "bull": dict(
        p=0.25, q4_rev=66.0, margin26=0.089, tax=0.125, minority=0.050,
        growth=[0.22, 0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.04, 0.03],
        margin=[0.088, 0.092, 0.095, 0.095, 0.095, 0.095, 0.095, 0.095, 0.095, 0.095],
        ronic=0.40, ronic_term=0.18,
        text="北美与欧洲继续夺份额、337 和解或规避设计、关税回落、极核扭亏；营收 2027 年 +22% 后放缓，"
             "EBIT 率升至 9.5%，增量回报 40%。"),
}
YEARS = list(range(2027, 2037))


def normalized_2026(s):
    """返回 2026 正常化：营收、EBIT、经营 NOPAT（归母、不含利息）与正常化归母净利（含净利息）。"""
    rev = REV_YTD + s["q4_rev"]
    if s["margin26"] is None:            # 基准：前三季度实际 + 四季度 EBIT 率 4%
        ebit = EBIT_YTD + s["q4_rev"] * 0.04
    else:
        ebit = rev * s["margin26"]
    nopat = ebit * (1 - s["tax"]) * (1 - s["minority"])
    net_int = (INT_INC_YTD + Q4_INT_INC) - (INT_EXP_YTD + Q4_INT_EXP)
    np_norm = nopat + net_int * (1 - s["tax"])
    return rev, ebit, nopat, np_norm


REV26_BASE = REV_YTD + 63.0     # 经营备付按基准 2026E 营收计，三情景共用同一张资产负债表


def net_cash_adj(rev26=REV26_BASE):
    float_excess = TRADE_WC - FLOAT_NORMAL_RATIO * rev26     # 负数越小浮存越多；超出正常浮存部分视为经营备付
    reserve = max(0.0, -float_excess) + MIN_CASH_RATIO * rev26
    return CASH - RESTRICTED - reserve - LEASE, reserve, -float_excess


def project(s, overrides=None):
    s = dict(s, **(overrides or {}))
    rev26, ebit26, nopat26, np26 = normalized_2026(s)
    rev, rows = rev26, []
    nopat_prev = nopat26
    for i, y in enumerate(YEARS):
        rev = rev * (1 + s["growth"][i])
        ebit = rev * s["margin"][i]
        nopat = ebit * (1 - s["tax"]) * (1 - s["minority"])
        g_next = s["growth"][i + 1] if i + 1 < len(YEARS) else G_TERM
        # 增量回报在显性期后五年线性回落到终值水平
        w = min(1.0, max(0.0, (i - 4) / 5))
        ronic = s["ronic"] * (1 - w) + s["ronic_term"] * w
        rr = max(0.0, g_next) / ronic
        oe = nopat * (1 - rr)
        rows.append(dict(year=y, rev=rev, ebit=ebit, nopat=nopat, g=nopat / nopat_prev - 1, rr=rr, ronic=ronic, oe=oe))
        nopat_prev = nopat
    return dict(rev26=rev26, ebit26=ebit26, nopat26=nopat26, np26=np26, rows=rows, s=s)


def ops_value(proj, r):
    rows = proj["rows"]
    pv = sum(row["oe"] / (1 + r) ** (k + 1) for k, row in enumerate(rows))
    last = rows[-1]
    rr_term = G_TERM / proj["s"]["ronic_term"]
    oe_term = last["nopat"] * (1 + G_TERM) * (1 - rr_term)
    tv = oe_term / (r - G_TERM)
    pv_tv = tv / (1 + r) ** len(rows)
    return pv + pv_tv, pv_tv


def dilution(v):
    return sum(n * max(0.0, 1 - k / v) for n, k in OPTIONS)


def per_share(equity_pre_cb):
    """可转债逐情景取低：债务口径（面值全额扣除）与全部转股口径（加股不扣债），期权按库存股法迭代。"""
    def solve(eq, base_shares):
        v = eq / base_shares
        for _ in range(60):
            v = eq / (base_shares + dilution(v))
        return v
    v_debt = solve(equity_pre_cb - CB_FACE, SHARES)
    v_conv = solve(equity_pre_cb, SHARES + CB_SHARES)
    return min(v_debt, v_conv), v_debt, v_conv


def value(proj, r):
    ops, pv_tv = ops_value(proj, r)
    nca, reserve, _ = net_cash_adj()
    eq = ops + nca + NON_OP_ASSETS
    v, v_debt, v_conv = per_share(eq)
    return dict(ops=ops, pv_tv=pv_tv, nca=nca, reserve=reserve, eq=eq, v=v, v_debt=v_debt, v_conv=v_conv)


def bisect(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def bond_floor(rate=0.03):
    # 付息日 6 月 10 日；距价格日 2026-10-20 的年数；第六年到期按面值 108%（含最后一期利息）赎回
    t0 = 0.64
    flows = [(t0 + i, c) for i, c in enumerate([0.10, 0.30, 0.60, 1.50, 1.80])] + [(t0 + 5, 108.0)]
    return CB_FACE * sum(c / (1 + rate) ** t for t, c in flows) / 100


def main():
    print("== 春风动力 603129 独立估值（价格日 2026-10-20，现价 %.2f，总股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("前三季度：营收 %.2f，EBIT（剔除退税、其他非经常、汇兑 %.2f、利息）%.2f，EBIT 率 %.2f%%"
          % (REV_YTD, FX_LOSS_YTD, EBIT_YTD, EBIT_YTD / REV_YTD * 100))
    print("可比 EBIT 率：2024 年 %.2f%%，2025 年 %.2f%%，2026H1 %.2f%%，2026 前三季度 %.2f%%，2026Q3 %.2f%%"
          % (EBIT_2024 / REV_2024 * 100, EBIT_2025 / REV_2025 * 100, EBIT_H1_26 / REV_H1_26 * 100,
             EBIT_YTD / REV_YTD * 100, (EBIT_YTD - EBIT_H1_26) / (REV_YTD - REV_H1_26) * 100))
    print("前三季度扣非归母 %.2f；加回税后汇兑损失约 %.2f 后 %.2f；报告归母 %.2f，其中退税税后 %.2f"
          % (DEDUCT_NP_YTD, FX_LOSS_YTD * 0.85, DEDUCT_NP_YTD + FX_LOSS_YTD * 0.85, PARENT_NP_YTD, REFUND_AFTER_TAX))

    projs = {k: project(s) for k, s in SCEN.items()}
    nca, reserve, float_excess = net_cash_adj()
    print("\n-- 经调整净现金（无杠杆口径，不含可转债）--")
    print("货币资金 %.2f − 受限 %.2f − 经营备付 %.2f（超额浮存 %.2f + 最低经营现金 %.2f）− 租赁负债 %.2f = %.2f"
          % (CASH, RESTRICTED, reserve, float_excess, MIN_CASH_RATIO * projs["base"]["rev26"], LEASE, nca))
    print("贸易营运资本 %.2f（营收 %.2f 的 %.1f%%）；正常浮存按 %.0f%% 计 %.2f；非经营资产 %.2f"
          % (TRADE_WC, projs["base"]["rev26"], TRADE_WC / projs["base"]["rev26"] * 100,
             FLOAT_NORMAL_RATIO * 100, FLOAT_NORMAL_RATIO * projs["base"]["rev26"], NON_OP_ASSETS))
    print("可转债：面值 %.2f，账面 %.2f，3%% 折现债底 %.2f，转股 %.4f 亿股（转股价 %.2f）"
          % (CB_FACE, CB_BOOK, bond_floor(), CB_SHARES, CB_CONV_PRICE))

    print("\n-- 2026 正常化（含净利息、剔除一次性）--")
    for k, p in projs.items():
        print("%-4s 营收 %.1f  EBIT %.2f（%.2f%%）  经营 NOPAT 归母 %.2f  正常化归母净利 %.2f"
              % (k, p["rev26"], p["ebit26"], p["ebit26"] / p["rev26"] * 100, p["nopat26"], p["np26"]))

    print("\n-- 增长路径（经营 NOPAT 归母，亿元）--")
    for k, p in projs.items():
        line = " ".join("%d:%.1f(%+.0f%%,RR%.0f%%)" % (r["year"], r["nopat"], r["g"] * 100, r["rr"] * 100) for r in p["rows"][:5])
        print(k, line)

    res = {}
    print("\n-- 三情景 V（股权成本 9%）--")
    for k, p in projs.items():
        v = value(p, COE)
        res[k] = v
        print("%-4s 经营价值 %.1f（终值现值 %.1f，占 %.0f%%）+ 净现金 %.1f + 非经营 %.2f = %.1f；"
              "债务口径 %.2f，转股口径 %.2f → 取低 %.2f"
              % (k, v["ops"], v["pv_tv"], v["pv_tv"] / v["ops"] * 100, v["nca"], NON_OP_ASSETS, v["eq"],
                 v["v_debt"], v["v_conv"], v["v"]))
    vw = sum(SCEN[k]["p"] * res[k]["v"] for k in SCEN)
    pv = PRICE / vw
    tier = "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"
    print("加权 V = %.2f；P/V = %.3f（%s）" % (vw, pv, tier))
    print("V 不变时进入各档的价格：≤%.1f 明显低估；≤%.1f 温和低估；≤%.1f 大致合理"
          % (0.75 * vw, 0.90 * vw, 1.10 * vw))

    sens = {}
    for r in (0.08, 0.10):
        sens[r] = sum(SCEN[k]["p"] * value(projs[k], r)["v"] for k in SCEN)
        per = {k: value(projs[k], r)["v"] for k in SCEN}
        print("股权成本 %.0f%%：加权 V %.2f（熊 %.2f／基 %.2f／牛 %.2f）"
              % (r * 100, sens[r], per["bear"], per["base"], per["bull"]))

    irr = bisect(lambda r: value(projs["base"], r)["v"] - PRICE, 0.05, 0.20)
    print("现价隐含回报（基准所有者收益流，含终值与净现金）：%.2f%%" % (irr * 100))

    # 反向 DCF：基准利润率与再投资不变，2027-2036 统一增速
    def v_uniform(g):
        gs = [g] * 10
        return value(project(SCEN["base"], dict(growth=gs)), COE)["v"]
    g_imp = bisect(lambda g: v_uniform(g) - PRICE, -0.10, 0.30)
    print("反向 DCF：现价隐含 2027-2036 年营收与经营利润统一增速 %.2f%%（其后 2.5%%）" % (g_imp * 100))
    # 反向 DCF：2027 年基准所有者收益起永续增长
    b27 = projs["base"]["rows"][0]
    eq_px = PRICE * (SHARES + CB_SHARES + dilution(PRICE))
    ops_px = eq_px - nca - NON_OP_ASSETS
    nopat27 = b27["nopat"]
    g_perp = bisect(lambda g: nopat27 * (1 - g / SCEN["base"]["ronic_term"]) / (COE - g) - ops_px, -0.05, 0.085)
    print("反向 DCF：以 2027 年经营 NOPAT %.2f、增量回报 15%% 计，现价隐含永续增速 %.2f%%" % (nopat27, g_perp * 100))

    # 交叉验证
    mcap = PRICE * SHARES
    base26 = projs["base"]
    ev = mcap + CB_FACE - nca - NON_OP_ASSETS
    print("\n-- 交叉验证 --")
    print("市值 %.1f；EV（市值 + 转债面值 − 经调整净现金 − 非经营资产）%.1f；EV/2026E EBIT %.1f×；"
          "市值/2026 正常化归母 %.1f×；股息率 %.2f%%"
          % (mcap, ev, ev / base26["ebit26"], mcap / base26["np26"], 4.20 / PRICE * 100))
    ev_full = mcap + CB_FACE + LEASE - CASH
    print("全部现金视为富余时 EV %.1f，EV/EBIT %.1f×" % (ev_full, ev_full / base26["ebit26"]))

    # 证伪触发后的 V（基准情景改写，其余不变）
    h1_26 = EBIT_H1_26 / REV_H1_26
    print("\n-- 证伪触发后的 V（基准路径改写，股权成本 9%%；参照 2026H1 EBIT 率 %.1f%%）--" % (h1_26 * 100))
    trig = {
        "F1 337 裁定侵权且无有效规避": dict(growth=[0.12, -0.05, 0.08, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.025],
                                  margin=[0.080, 0.070, 0.076, 0.081, 0.082, 0.082, 0.082, 0.082, 0.082, 0.082], ronic=0.25),
        "F2 2027H1 营收同比<5%": dict(growth=[0.04, 0.06, 0.06, 0.05, 0.05, 0.04, 0.04, 0.035, 0.03, 0.025]),
        "F3 2027H1 EBIT 率<9.0%（全年约 7%）": dict(margin=[0.072] * 10),
        "F5 极核电自停售且和信亏损>3 亿": dict(margin=[m - 0.006 for m in SCEN["base"]["margin"]]),
    }
    out_trig = {}
    for name, ov in trig.items():
        v = value(project(SCEN["base"], ov), COE)["v"]
        out_trig[name] = v
        print("%s：%.2f" % (name, v))
    # F4：浮存回落到营收 −10%，经营备付再增加
    p = projs["base"]
    ops, _ = ops_value(p, COE)
    for ratio in (-0.10, -0.15, -0.20, None):
        if ratio is None:
            extra = -(TRADE_WC - FLOAT_NORMAL_RATIO * REV26_BASE)   # 全部浮存视为长期：经营备付只留最低现金
            label = "全部浮存视为长期（经营备付只留最低现金）"
            extra = -extra
        else:
            extra = (FLOAT_NORMAL_RATIO - ratio) * REV26_BASE * -1
            label = "正常浮存按营收 %.0f%%" % (ratio * 100)
        v4, _, _ = per_share(ops + nca - extra + NON_OP_ASSETS)
        print("浮存敏感性（基准）：%s，经营备付变动 %+.1f 亿 → V %.2f" % (label, extra, v4))

    b = projs["base"]["rows"][:5]
    print("\n-- json 用数 --")
    print("base growth 2027-2031: " + ", ".join("%.4f" % r["g"] for r in b)
          + "；平均再投资率 %.4f；营收 2031 %.1f；经营 NOPAT 2031 %.2f" % (sum(r["rr"] for r in b) / 5, b[-1]["rev"], b[-1]["nopat"]))
    print("v_bear %.2f v_base %.2f v_bull %.2f v_weighted %.2f pv %.4f v8 %.2f v10 %.2f irr %.4f"
          % (res["bear"]["v"], res["base"]["v"], res["bull"]["v"], vw, pv, sens[0.08], sens[0.10], irr))
    print("np26 bear %.2f base %.2f bull %.2f；net_cash_adj %.2f"
          % (projs["bear"]["np26"], projs["base"]["np26"], projs["bull"]["np26"], nca))


if __name__ == "__main__":
    main()
