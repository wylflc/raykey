#!/usr/bin/env python3
"""美的集团（000333）独立估值：所有者收益 DCF + 经调整净现金 + 非经营资产。

金额单位亿元，每股价值与价格单位元/股。所有输入写在本脚本内，出处见
`b02/companies/000333_美的集团.md` 第 9 节「来源」。运行：python3 valuation.py
口径：A+H 全部股份扣库存股（回购专户），按 2026-06-30 资产负债表，并计入 7-1 至 10-16
的回购、已宣派股息与期权行权；价格日 2026-10-19，A 股收盘 86.54 元。
"""

PRICE = 86.54          # A 股 2026-10-19 收盘（腾讯日线）
COE = 0.09             # 股权成本基准
TAX = 0.165            # 有效税率（2025 年 16.1%，2026H1 16.5%）
MINORITY = 0.01        # 少数股东损益占净利比例（2024-2026H1 0.5%-1.3%）

# ---------------------------------------------------------------- 股本
SHARES_TOTAL = 76.3016          # 亿股，腾讯行情总股本（A+H；2026-08-28 公告口径 76.2880）
TREASURY_CANCEL = 1.32517507    # 2026 年回购方案（用于注销），截至 10-16，buyback_20261017 第 1 页
TREASURY_ESOP = 0.80412541 - 0.16312221  # 激励用库存股 8,041 万股减 2026 持股计划过户 1,631 万股
OPTIONS_LEFT = 0.1213           # 第九期第三个行权期尚未行权期权（亿份），行权价 41.44 元
STRIKE = 41.44


def diluted_shares(v_ps):
    """库存股扣除后的流通股，加库存股法下的期权摊薄（以估值本身作股价）。"""
    base = SHARES_TOTAL - TREASURY_CANCEL - TREASURY_ESOP
    return base + OPTIONS_LEFT * max(0.0, 1 - STRIKE / max(v_ps, STRIKE))


# ---------------------------------------------------------------- 核心经营利润（EBIT）
# 口径：毛利 − 税金及附加 − 销售 − 管理 − 研发 + 其他收益 − 经营性减值（存货、合同资产、信用等）
#       + 联营投资收益；不含利息、汇兑、公允价值变动、处置收益、商誉与长投减值、营业外收支。
CORE_H1_26 = (2600.42 - 1943.67) - 11.81 - 215.46 - 76.15 - 84.67 + 14.83 \
    - (4.42 + 0.28 + 0.21 + 6.06) + 5.10          # = 277.62，2026H1_report 第 98-99、173-174 页
CORE_H1_25 = (2511.24 - 1867.86) - 11.46 - 230.53 - 72.57 - 87.67 + 13.96 \
    - (3.56 + 0.10 + 3.46) + 4.69                  # = 252.68
CORE_2025 = (4564.52 - 3359.90) - 22.17 - 428.91 - 160.92 - 177.88 + 26.64 \
    - 11.46 + 5.89                                 # = 435.81（经营性减值 11.46 不含长投减值 3.67）
REV_Q3_25, CORE_Q3_25 = 1119.33, 123.95            # 2025Q3 单季（三季报累计减中报）
REV_Q4_25, CORE_Q4_25 = 933.95, 59.18
REV_H1_26 = 2600.42
NET_INT_2025 = 84.44 - 22.11 + 20.50               # 2025 年净利息 82.83（财务收入附注 + 金融业务利息）
NET_INT_H1_26 = 37.25 - 8.63 + 10.10               # 2026H1 38.72
LOAN_INT = 11.3        # 金融业务发放贷款利息（年化，H1 5.63），属经营性
IMPAIR_ALLOW = 4.0     # 商誉/长投减值的常态化年均计提（税前），代替一次性剔除

SCEN = {
    # h2: (Q3 营收同比, Q4 营收同比, Q3 核心利润率, Q4 核心利润率)；norm_margin 给定时按中枢利润率正常化
    "bear": dict(h2=(-0.02, -0.02, 0.100, 0.050), norm_margin=0.090, norm_rev=4650.0, net_int=72.0,
                 cash_yield=0.023, rr=0.15, growth=[-0.04, 0.00, 0.02, 0.02, 0.02], g_t=0.015, rr_t=0.15,
                 cash_adj=-100.0, nonop_mult=0.8, extra=0.0, p=0.25,
                 text="内需在补贴退坡后再跌、铜价与人民币升值压利润率回到十年中枢 9.0%，2027 年所有者收益 -4%，"
                      "此后 2% 增长，终值 1.5%；再投资率 15% 但回报低（并购与 ToB）；浮存金收缩 100 亿元"),
    "base": dict(h2=(0.03, 0.03, 0.108, 0.060), norm_margin=None, norm_rev=None, net_int=74.3,
                 cash_yield=0.0256, rr=0.12, growth=[0.015, 0.04, 0.045, 0.04, 0.035], g_t=0.025, rr_t=0.10,
                 cash_adj=0.0, nonop_mult=1.0, extra=0.0, p=0.50,
                 text="下半年营收 +3%、核心利润率同比降约 0.3 个点（铜价、价格战），2026 核心利润率 9.75%；"
                      "2027 年补贴退坡只增 1.5%，2028-2031 年 3.5%-4.5%；再投资率 12%（增量回报约 29%），终值 2.5%"),
    "bull": dict(h2=(0.04, 0.05, 0.111, 0.065), norm_margin=None, norm_rev=None, net_int=74.3,
                 cash_yield=0.026, rr=0.15, growth=[0.06, 0.07, 0.07, 0.06, 0.05], g_t=0.025, rr_t=0.10,
                 cash_adj=0.0, nonop_mult=1.0, extra=100.0, p=0.25,
                 text="海外自有品牌与楼宇科技（数据中心液冷）、机器人加速，利润率守住 9.9%，2027-2031 年所有者收益"
                      " 5%-7%，再投资率 15%（增量回报约 41%），终值 2.5%；另计长鑫科技持股上市增值 100 亿元（税后）"),
}

# ---------------------------------------------------------------- 经调整净现金（2026-06-30 起算）
GROSS_LIQUID = {
    "货币资金": 906.43,
    "交易性金融资产（不含权益工具 1.10）": 31.56 - 1.10,
    "衍生金融资产净额（47.80-9.15）": 47.80 - 9.15,
    "固定收益类产品（一年内到期 1,583.11 + 一年以上 690.06，含美国国债 150.35）": 2273.17,
    "其他流动资产中的固定收益类产品": 4.26,
}
RESTRICTED = {
    "其他货币资金（保证金等）": 58.01,
    "存放央行法定准备金": 21.73,
    "质押的固定收益类产品": 197.40,
}
DEBT = {
    "短期借款": 473.05,
    "长期借款（含一年内到期 5.75）": 154.17 + 5.75,
    "美元债（一年内到期）": 30.95,
    "H 股可转债面值 172.48 亿港元×0.8584（中期股息 0.50 元=0.58249 港元）": 172.48 * 0.8584,
    "租赁负债（含一年内到期 13.93）": 19.19 + 13.93,
    "吸收存款及同业存放": 1.02,
    "交易性金融负债": 5.65,
    "长期应付职工薪酬（设定受益等）": 12.26,
}
AFTER_PERIOD = {
    "H 股 2025 年末期股息（6-30 未付，6.508 亿股×3.80）": -24.73,
    "2026 中期股息（已获股东会通过，0.50 元×7.43 亿股）": -37.17,
    "7-1 至 10-16 A 股回购（107.31-54.76）": -52.55,
    "9 月 H 股回购（约 6,200 万港元）": -0.55,
    "6-30 后期权行权收款（约 1,670 万股×41.44）": 6.90,
    "百胜医疗（Esaote）控股权收购（对价未披露，估计）": -18.0,
}
REV_2026E_FOR_RESERVE = 4715.0
OPER_RESERVE_RATE = 0.05          # 经营备付：营收 5%
SEASONAL_FLOAT = 170.3            # 6-30 经营性营运资本 -1,732.9 较年末 -1,562.6 的季节性高位（应付票据扩张）
OPER_CASH = sum(RESTRICTED.values()) + OPER_RESERVE_RATE * REV_2026E_FOR_RESERVE + SEASONAL_FLOAT

NONOP_BOOK = 72.70 + 1.10 + 0.30  # 其他非流动金融资产 + 交易性权益工具 + 其他权益工具投资
NONOP_TAX_HAIRCUT = 0.15


def net_cash_adj():
    gross = sum(GROSS_LIQUID.values())
    restricted = sum(RESTRICTED.values())
    debt = sum(DEBT.values())
    after = sum(AFTER_PERIOD.values())
    reserve = OPER_RESERVE_RATE * REV_2026E_FOR_RESERVE
    pre_min = gross - restricted - debt + after - reserve - SEASONAL_FLOAT
    return dict(gross=gross, restricted=restricted, debt=debt, after=after, reserve=reserve,
                seasonal=SEASONAL_FLOAT, pre_minority=pre_min, value=pre_min * (1 - MINORITY))


# ---------------------------------------------------------------- 2026 正常化
def normalize_2026(s):
    q3g, q4g, m3, m4 = s["h2"]
    rev = REV_H1_26 + REV_Q3_25 * (1 + q3g) + REV_Q4_25 * (1 + q4g)
    core_h2 = REV_Q3_25 * (1 + q3g) * m3 + REV_Q4_25 * (1 + q4g) * m4
    core = CORE_H1_26 + core_h2
    if s["norm_margin"] is not None:      # 熊市情景：按十年中枢利润率正常化
        rev = s["norm_rev"]
        core = s["norm_margin"] * rev
    keep = (1 - TAX) * (1 - MINORITY)
    core_nopat = core * keep - IMPAIR_ALLOW * keep
    loan_int = LOAN_INT * keep
    oper_cash_int = OPER_CASH * s["cash_yield"] * keep
    cash_int_total = (s["net_int"] - LOAN_INT) * keep        # 现金与有息负债的税后净利息
    excess_int = cash_int_total - oper_cash_int               # 超额净现金的利息，估值时由净现金面值代表
    npn = core_nopat + loan_int + cash_int_total               # 正常化归母净利（含净利息）
    oe0 = (core_nopat + loan_int) * (1 - s["rr"]) + oper_cash_int
    return dict(rev=rev, core=core, margin=core / rev, npn=npn, core_nopat=core_nopat,
                loan_int=loan_int, oper_cash_int=oper_cash_int, excess_int=excess_int, oe0=oe0,
                core_h2=core_h2 if s["norm_margin"] is None else None)


def scenario_value(name, r=COE, override=None):
    s = dict(SCEN[name])
    if override:
        s.update(override)
    n = normalize_2026(s)
    if override and "npn_shift" in override:      # 证伪检验用：正常化净利平移（全部落在经营部分）
        shift = override["npn_shift"]
        n["core_nopat"] += shift
        n["npn"] += shift
        n["oe0"] += shift * (1 - s["rr"])
    oe0, rr, rr_t = n["oe0"], s["rr"], s["rr_t"]
    # 2026H2 价值：下半年经营所有者收益（约占全年 42%）+ 超额现金下半年利息，按 0.2 年折现
    h2 = (0.42 * oe0 + 0.5 * n["excess_int"]) / (1 + r) ** 0.2
    # 2027-2031 年中现金流：t = 0.7, 1.7, ..., 4.7（自 2026-10-19 起算）
    oe, pv_flows, path = oe0, 0.0, []
    for i, g in enumerate(s["growth"]):
        oe *= 1 + g
        path.append(oe)
        pv_flows += oe / (1 + r) ** (0.7 + i)
    # 终值：再投资率由 rr 过渡到 rr_t（经营部分），首年现金流 2032 年中
    oper_share = 1 - n["oper_cash_int"] / oe0
    adj = 1 + oper_share * ((1 - rr_t) / (1 - rr) - 1)
    oe_t = path[-1] * (1 + s["g_t"]) * adj
    pv_tv = oe_t / (r - s["g_t"]) / (1 + r) ** 4.7
    nc = net_cash_adj()["value"] + s["cash_adj"]
    nonop = NONOP_BOOK * (1 - NONOP_TAX_HAIRCUT) * s["nonop_mult"] + s["extra"]
    equity = h2 + pv_flows + pv_tv + nc + nonop
    v = equity / diluted_shares(PRICE)
    for _ in range(20):                              # 期权摊薄以估值本身作股价迭代
        v = equity / diluted_shares(v)
    return dict(v=v, equity=equity, h2=h2, pv_flows=pv_flows, pv_tv=pv_tv, nc=nc, nonop=nonop,
                tv_share=pv_tv / equity, path=path, norm=n, s=s)


def weighted(r=COE):
    return sum(SCEN[k]["p"] * scenario_value(k, r)["v"] for k in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    """基准情景现金流（含终值与净现金）现值等于现价的折现率。"""
    return solve(lambda r: scenario_value("base", r)["v"], 0.06, 0.20, PRICE)


def reverse_dcf():
    """9% 下，2027 年起所有者收益永续不变增速（再投资率 12%）使价值等于现价。"""
    def v_perp(g):
        return scenario_value("base", COE, dict(growth=[g] * 5, g_t=g, rr_t=0.12))["v"]
    g_perp = solve(v_perp, -0.05, 0.08, PRICE)

    def v_10y(g):   # 前 10 年增速 g，之后终值 2.5%：用 5 年路径 + 5 年同速近似为 growth 两段
        s = dict(SCEN["base"])
        r = COE
        n = normalize_2026(s)
        oe, pv = n["oe0"], 0.0
        for i in range(10):
            oe *= 1 + g
            pv += oe / (1 + r) ** (0.7 + i)
        adj = 1 + (1 - n["oper_cash_int"] / n["oe0"]) * ((1 - 0.10) / (1 - 0.12) - 1)
        pv += oe * 1.025 * adj / (r - 0.025) / (1 + r) ** 9.7
        h2 = (0.42 * n["oe0"] + 0.5 * n["excess_int"]) / (1 + r) ** 0.2
        eq = pv + h2 + net_cash_adj()["value"] + NONOP_BOOK * (1 - NONOP_TAX_HAIRCUT)
        return eq / diluted_shares(PRICE)
    g_10 = solve(v_10y, -0.10, 0.10, PRICE)
    return g_perp, g_10


def weighted_custom(overrides, probs, r=COE):
    """证伪触发后：按触发情形改写各情景并重设概率，返回加权 V。"""
    return sum(probs[k] * scenario_value(k, r, overrides.get(k))["v"] for k in SCEN)


def falsifier_values():
    base = SCEN["base"]
    nc = net_cash_adj()["value"]
    bear_npn = normalize_2026(SCEN["bear"])["npn"]
    base_npn = normalize_2026(base)["npn"]
    out = {}
    # F1 2026 年报核心经营利润率 < 9.0%（基准 9.75%）：基准正常化净利降到熊市口径，概率 40/50/10
    out["F1"] = weighted_custom({"base": dict(npn_shift=bear_npn - base_npn)},
                                {"bear": 0.40, "base": 0.50, "bull": 0.10})
    # F2 2026Q3 营收同比 < -3% 且单季核心经营利润率 < 10.0%（2025Q3 为 11.07%）：基准净利 -20 亿、2027 年零增长，概率 35/50/15
    out["F2"] = weighted_custom({"base": dict(npn_shift=-20.0, growth=[0.0] + base["growth"][1:])},
                                {"bear": 0.35, "base": 0.50, "bull": 0.15})
    # F3 2027H1 国内收入同比 < -5%：基准 2027-2028 年改为 -4%、0%，概率 35/50/15
    out["F3"] = weighted_custom({"base": dict(growth=[-0.04, 0.0, 0.045, 0.04, 0.035])},
                                {"bear": 0.35, "base": 0.50, "bull": 0.15})
    # F4 资本配置恶化（2026 年分红+回购 < 归母净利 70%，或单笔现金并购 > 300 亿元）：三情景超额现金打七折，基准再投资率 18%
    hair = dict(cash_adj=-0.3 * nc)
    out["F4"] = weighted_custom({"bear": dict(cash_adj=SCEN["bear"]["cash_adj"] - 0.3 * nc),
                                 "base": dict(hair, rr=0.18, rr_t=0.15), "bull": hair},
                                {"bear": 0.35, "base": 0.50, "bull": 0.15})
    # F5 美元兑人民币中间价 < 6.40 连续两个季度且海外毛利率同比降 > 1.5 个点：三情景正常化净利 -25 亿，概率 30/50/20
    sh = dict(npn_shift=-25.0)
    out["F5"] = weighted_custom({"bear": sh, "base": sh, "bull": sh},
                                {"bear": 0.30, "base": 0.50, "bull": 0.20})
    return out


def falsifier_combos():
    """两条证伪同时触发时的加权 V（F1 为基础，叠加 F2／F3／F4）。"""
    base = SCEN["base"]
    nc = net_cash_adj()["value"]
    shift = normalize_2026(SCEN["bear"])["npn"] - normalize_2026(base)["npn"]
    probs = {"bear": 0.40, "base": 0.50, "bull": 0.10}
    return {
        "F1+F2": weighted_custom({"base": dict(npn_shift=shift - 20.0, growth=[0.0] + base["growth"][1:])}, probs),
        "F1+F3": weighted_custom({"base": dict(npn_shift=shift, growth=[-0.04, 0.0, 0.045, 0.04, 0.035])}, probs),
        "F1+F4": weighted_custom({"bear": dict(cash_adj=SCEN["bear"]["cash_adj"] - 0.3 * nc),
                                  "base": dict(npn_shift=shift, cash_adj=-0.3 * nc, rr=0.18, rr_t=0.15),
                                  "bull": dict(cash_adj=-0.3 * nc)}, probs),
    }


def implied_irr_cash80():
    """超额净现金只按八成计时，基准现金流的隐含回报。"""
    nc = net_cash_adj()["value"]
    return solve(lambda r: scenario_value("base", r, dict(cash_adj=-0.2 * nc))["v"], 0.06, 0.20, PRICE)


def sensitivities():
    nc = net_cash_adj()["value"]
    out = {}
    out["终值增速降至 2.0%（熊市 1.0%）"] = weighted_custom(
        {"bear": dict(g_t=0.010), "base": dict(g_t=0.020), "bull": dict(g_t=0.020)}, {k: SCEN[k]["p"] for k in SCEN})
    out["超额净现金只按八成计"] = weighted_custom(
        {"bear": dict(cash_adj=SCEN["bear"]["cash_adj"] - 0.2 * nc), "base": dict(cash_adj=-0.2 * nc),
         "bull": dict(cash_adj=-0.2 * nc)}, {k: SCEN[k]["p"] for k in SCEN})
    out["再投资率各加 5 个点"] = weighted_custom(
        {k: dict(rr=SCEN[k]["rr"] + 0.05, rr_t=SCEN[k]["rr_t"] + 0.05) for k in SCEN}, {k: SCEN[k]["p"] for k in SCEN})
    out["不计长鑫增值（牛市 extra=0）"] = weighted_custom({"bull": dict(extra=0.0)}, {k: SCEN[k]["p"] for k in SCEN})
    out["概率改为 35/45/20"] = weighted_custom({}, {"bear": 0.35, "base": 0.45, "bull": 0.20})
    return out


def cross_checks():
    nc = net_cash_adj()["value"]
    nonop = NONOP_BOOK * (1 - NONOP_TAX_HAIRCUT)
    sh = diluted_shares(PRICE)
    mcap = PRICE * sh
    nb = normalize_2026(SCEN["base"])
    ev = mcap - nc - nonop
    oper_ebit = nb["core"] + LOAN_INT + OPER_CASH * SCEN["base"]["cash_yield"]
    # 分部加总（2025 分部利润扣按比例分摊的财务收入 59.04/494.26，税后乘数）
    fin_share = 59.04 / 494.26
    seg = {"智能家居": (371.30, 12.0), "楼宇科技": (45.04, 16.0), "工业技术": (50.88, 13.0)}
    sotp = sum(p * (1 - fin_share) * (1 - TAX) * m for p, m in seg.values())
    kuka = 310.11 * 1.0               # 机器人与自动化按 1.0 倍营收
    others = (622.42 - 310.11) * 0.5  # 安得、能源、医疗等其他对外收入按 0.5 倍营收
    sotp_v = (sotp + kuka + others + nc + nonop) / sh
    hist_pe = [11.0, 11.0, 12.4, 21.0, 12.1, 16.8, 25.4, 18.0, 12.3, 11.4, 14.9, 13.5]
    pe_med = sorted(hist_pe)[len(hist_pe) // 2 - 1: len(hist_pe) // 2 + 1]
    pe_med = sum(pe_med) / 2
    return dict(mcap=mcap, ev=ev, ev_ebit=ev / oper_ebit, pe_norm=mcap / nb["npn"],
                pe_ex_cash=ev / (nb["npn"] - nb["excess_int"]),
                v_pe_median=pe_med * nb["npn"] / sh, pe_median=pe_med,
                v_pe_15=15 * nb["npn"] / sh, sotp_v=sotp_v,
                div_yield=4.30 / PRICE, buyback_yield=137.0 / mcap)


def main():
    nc = net_cash_adj()
    print("=== 美的集团（000333）独立估值，价格日 2026-10-19，A 股 86.54 元 ===")
    print(f"流通股（扣库存股 {TREASURY_CANCEL + TREASURY_ESOP:.4f} 亿股，含期权摊薄）: {diluted_shares(PRICE):.4f} 亿股")
    print(f"核心经营利润：2025 {CORE_2025:.2f}，2025H1 {CORE_H1_25:.2f}，2026H1 {CORE_H1_26:.2f}"
          f"（同比 {CORE_H1_26 / CORE_H1_25 - 1:+.1%}）；净利息 2025 {NET_INT_2025:.2f}，2026H1 {NET_INT_H1_26:.2f}")
    print(f"经调整净现金：毛流动金融资产 {nc['gross']:.1f} − 受限 {nc['restricted']:.1f} − 有息及类债务 {nc['debt']:.1f}"
          f" + 期后事项 {nc['after']:.1f} − 经营备付 {nc['reserve']:.1f} − 季节性浮存 {nc['seasonal']:.1f}"
          f" = {nc['pre_minority']:.1f}，扣少数股东 1% 后 {nc['value']:.1f}")
    print(f"非经营资产（税后）: {NONOP_BOOK * (1 - NONOP_TAX_HAIRCUT):.1f}")
    print()
    res = {k: scenario_value(k) for k in SCEN}
    for k, r in res.items():
        n = r["norm"]
        print(f"[{k}] p={SCEN[k]['p']:.2f}  V={r['v']:.2f} 元/股  P/V={PRICE / r['v']:.3f}")
        print(f"   2026 正常化：营收 {n['rev']:.1f}，核心经营利润 {n['core']:.1f}（{n['margin']:.2%}），"
              f"正常化归母净利 {n['npn']:.1f}（其中超额现金利息 {n['excess_int']:.1f}），所有者收益基数 {n['oe0']:.1f}")
        print("   所有者收益 2027-2031: " + ", ".join(f"{x:.1f}" for x in r["path"])
              + f"；增速 {SCEN[k]['growth']}，终值 g={SCEN[k]['g_t']}")
        print(f"   构成：下半年 {r['h2']:.1f} + 2027-31 现值 {r['pv_flows']:.1f} + 终值现值 {r['pv_tv']:.1f}"
              f"（占 {r['tv_share']:.1%}）+ 净现金 {r['nc']:.1f} + 非经营 {r['nonop']:.1f} = {r['equity']:.1f}")
    vw = weighted()
    pv = PRICE / vw
    band = "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"
    print()
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.3f}（{band}）")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：加权 V = {v8:.2f}（基准 {scenario_value('base', 0.08)['v']:.2f}）；"
          f"10%：加权 V = {v10:.2f}（基准 {scenario_value('base', 0.10)['v']:.2f}）")
    irr = implied_irr()
    print(f"现价隐含回报（基准现金流）: {irr:.2%}")
    g_perp, g_10 = reverse_dcf()
    print(f"反向 DCF：9% 下现价隐含 2027 年起所有者收益永续增速 {g_perp:.2%}（再投资率 12%）；"
          f"或前 10 年 {g_10:.2%}、之后 2.5%")
    print("V 不变时分档价格：明显低估 ≤ {:.2f}；温和低估 {:.2f}～{:.2f}；大致合理 {:.2f}～{:.2f}；偏贵 > {:.2f}".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    fv = falsifier_values()
    for k, v in fv.items():
        print(f"证伪 {k} 触发后的加权 V：{v:.2f}（P/V {PRICE / v:.3f}）")
    for k, v in falsifier_combos().items():
        print(f"证伪 {k} 同时触发的加权 V：{v:.2f}（P/V {PRICE / v:.3f}）")
    print(f"超额净现金只按八成计时的隐含回报: {implied_irr_cash80():.2%}")
    print()
    for k, v in sensitivities().items():
        print(f"敏感性｜{k}：加权 V {v:.2f}（P/V {PRICE / v:.3f}）")
    print()
    c = cross_checks()
    print(f"交叉验证：市值（扣库存股）{c['mcap']:.0f}，经营 EV {c['ev']:.0f}，EV/经营 EBIT {c['ev_ebit']:.1f}x；"
          f"市值/正常化净利 {c['pe_norm']:.1f}x，剔现金后 {c['pe_ex_cash']:.1f}x")
    print(f"   历史 PE 中位 {c['pe_median']:.2f}x → {c['v_pe_median']:.2f} 元；15x → {c['v_pe_15']:.2f} 元；"
          f"分部加总 → {c['sotp_v']:.2f} 元")
    print(f"   股息率 {c['div_yield']:.2%}（近 12 个月 4.30 元）+ 回购收益率约 {c['buyback_yield']:.2%}（近 12 个月约 137 亿元）")


if __name__ == "__main__":
    main()
