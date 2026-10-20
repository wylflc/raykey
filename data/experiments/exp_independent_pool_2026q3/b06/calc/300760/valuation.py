#!/usr/bin/env python3
"""迈瑞医疗（300760）独立估值：所有者收益 DCF（迈瑞除惠泰）+ 惠泰股权按市值折价 + 经调整净现金。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。价格日 2026-10-20，现价 169.76，总股本 12.11799431 亿股（A 股，
无 H 股；回购专户库存股 641,963 股已于 2026-08-07 注销，现无库存股）。
输入出处见各行注释（2026H1_report 页码为 PDF 物理页）。
"""
from datetime import date

PRICE = 169.76
SHARES = 12.11799431          # 亿股，2026H1_report 第 2 页分红基数 1,211,799,431 股
VAL_DATE = date(2026, 10, 20)
PROBS = {"bear": 0.25, "base": 0.50, "bull": 0.25}
COE = 0.09

# ---------------- 2026 上半年实际（2026H1_report 第 128、208-210 页） ----------------
REV_H1 = 177.46969604
COGS_H1 = 69.50862309
TAXSUR_H1 = 1.97717792
SELL_H1 = 25.16220938
ADMIN_H1 = 6.96325373
RD_H1 = 15.69511152
CORE_EBIT_H1 = REV_H1 - COGS_H1 - TAXSUR_H1 - SELL_H1 - ADMIN_H1 - RD_H1   # 58.16
OTHER_INC_H1 = 1.94188774      # 软件退税 1.4670 + 加计抵减 0.1287 + 补助 0.3462（第 208 页）
RECUR_OTHER_H1 = 1.46699674 + 0.12867031
INVEST_H1 = 0.19984846
FV_H1 = 0.00587825
CREDIT_IMP_H1 = -0.05251257
ASSET_IMP_H1 = -0.67535273
DISPOSAL_H1 = -0.09022964
NONOP_IN_H1, NONOP_OUT_H1 = 0.30783463, 0.40951927
FIN_EXP_H1 = 3.83021821        # 含汇兑损失 5.7369、利息收入 -2.4602（第 208 页）
FX_LOSS_H1 = 5.73688595
INT_INC_H1 = 2.46018611
LEASE_INT_H1 = 0.11460070
PBT_H1 = 55.56093706
TAX_H1 = 5.09187626
PARENT_NP_H1 = 47.967918
MINORITY_H1 = 2.50114280

# 惠泰医疗（2026H1_report 第 225-226 页；合并口径含购买价分摊调整）
HT_STAKE = 0.2688
HT_NP_H1_CONSOL = 3.41881381
HT_MKT_CAP = 357.13468739      # 东财 F10 公司规模（2026-10-20 抓取，raw/300760/f10.json peers.gsgm_zsz）
HT_CASH_EST = 10.5             # 惠泰自有现金估计（无一手数据，见正文）

# ---------------- 资产负债表（2026-06-30，第 125-127、169、200 页）与期后事项 ----------------
CASH = 186.99272786
TRADING_FA = 0.75587825
RESTRICTED = 0.53157307
OPER_RESERVE = 20.0            # 经营备付：约 0.8 个月经营性现金流出（上半年月均 151.3/6≈25.2，第 132 页），含海外外汇管制现金 1.32
DIV_DECLARED = 16.11693243     # 2026 第二次中期分红，2026-09-08 除息（dividend_20260831_816590）
DEBT = 0.00231201 + 0.00530911 + 3.10318121   # 短借+长借（含一年内）+租赁负债（含一年内）
DIASYS_PUT = 3.91842888        # 收购 DiaSys 少数股权义务（第 200 页）
FX_REVAL_Q3 = 1.6              # 6-30→9-30 美元中间价 6.8109→6.7351（-1.11%），美元净货币资产约 24 亿美元
NONOP_OTHER = 1.79829765 + 0.34016256   # 其他权益工具投资 + 高性能医疗器械研究院（惠泰的联营投资不计）

NET_CASH_CONSOL = CASH + TRADING_FA - RESTRICTED - OPER_RESERVE - DIV_DECLARED - DEBT - DIASYS_PUT
NET_CASH_FOR_V = NET_CASH_CONSOL - HT_CASH_EST - FX_REVAL_Q3

# ---------------- 2025 年与历史（数据包第三节，东财 F10 年报口径） ----------------
REV_2025, PARENT_NP_2025 = 332.82, 81.36
DOM_2025, INTL_2025 = 156.32, 176.50
DOM_H1_2025, INTL_H1_2025 = 84.10604047, 167.43003854 - 84.10604047   # 第 239 页
DOM_H1_2026 = 82.75541810

# ---------------- 情景参数 ----------------
SCEN = {
    # rev26: 2026 全年收入；margin: 正常化核心经营利润率（毛利-税金-三费-研发；2017-19 均值 27.5%，
    # 2020-24 均值 33.7%，2025 年 28.3%，2026E 28.7%）；imp: 常态减值（2023-25 年均 -6.1，含无形资产减值）；
    # recur_other: 软件退税+加计抵减；ht_np: 惠泰合并口径（含购买价分摊摊销）净利；tax: 正常化有效税率
    "bear": dict(rev26=352.0, margin=0.275, recur_other=3.0, assoc=0.30, imp=-4.5, tax=0.15,
                 ht_np=7.0, growth=[0.05, 0.05, 0.045, 0.04, 0.035], ronic=0.25,
                 g_t=0.020, ronic_t=0.15, ht_disc=0.40),
    "base": dict(rev26=None, margin=0.295, recur_other=3.2, assoc=0.35, imp=-4.0, tax=0.13,
                 ht_np=7.4, growth=[0.10, 0.095, 0.09, 0.08, 0.07], ronic=0.35,
                 g_t=0.025, ronic_t=0.25, ht_disc=0.25),
    "bull": dict(rev26=358.0, margin=0.310, recur_other=3.3, assoc=0.40, imp=-3.5, tax=0.12,
                 ht_np=7.8, growth=[0.14, 0.13, 0.12, 0.11, 0.10], ronic=0.40,
                 g_t=0.025, ronic_t=0.30, ht_disc=0.15),
}
OTHER_MINORITY = 0.05          # DiaSys 等其他少数股东损益（上半年 0.02）
NORM_YIELD = 0.018             # 净现金正常化收益率（美元存款高息与人民币升值汇损相抵后的人民币等价）
H2_SHARE = 0.43                # 下半年占全年核心经营利润比例（2025 年 H2/H1=0.74，取 0.76）


def h2_2026_revenue():
    """基准：下半年国内 +5%、国际 +10.5%（2025 年下半年国内 72.21、国际 93.18）。"""
    dom_h2_25 = DOM_2025 - DOM_H1_2025
    intl_h2_25 = INTL_2025 - INTL_H1_2025
    return dom_h2_25 * 1.05 + intl_h2_25 * 1.105


REV_2026_BASE = REV_H1 + h2_2026_revenue()
SCEN["base"]["rev26"] = REV_2026_BASE


def reported_2026_estimate():
    """2026 年报口径归母净利估计（含汇兑损失与实际税率），用于与正常化对照和三季报核对。"""
    rev_h2 = h2_2026_revenue()
    core_h2 = CORE_EBIT_H1 * 0.76
    other_h2 = 1.90
    invest_h2 = 0.15
    imp_h2 = -2.30
    # 下半年财务费用（正数为费用）：租赁利息 0.12 + 未确认融资费用 0.17 + 手续费 0.06 + 三季度汇损 1.60 - 利息收入 2.35
    fin_exp_h2 = 0.12 + 0.17 + 0.06 + 1.60 - 2.35
    nonop_h2 = -0.20
    pbt_h2 = core_h2 + other_h2 + invest_h2 + imp_h2 - fin_exp_h2 + nonop_h2
    tax_h2 = pbt_h2 * 0.12
    minority_h2 = 2.75
    parent_h2 = pbt_h2 - tax_h2 - minority_h2
    # 三季度：收入 97.5（国际美元 +15%、人民币约 +11%，国内 +3%～+6%），核心经营利润率 32.5%（2025Q3 33.8%）
    q3_rev = 97.5
    q3_core = q3_rev * 0.325
    q3_fin_exp = 1.60 + 0.25 - 1.20        # 汇损 1.60 + 其他财务费用 0.25 - 利息收入 1.20
    q3_pbt = q3_core + 0.95 + 0.10 - 0.40 - q3_fin_exp   # 其他收益 0.95、投资收益 0.10、减值 -0.40
    q3_parent = q3_pbt * (1 - 0.11) - 1.30                # 有效税率 11%，少数股东 1.30
    return dict(rev=REV_H1 + rev_h2, parent=PARENT_NP_H1 + parent_h2, parent_h2=parent_h2,
                core_margin=(CORE_EBIT_H1 + core_h2) / (REV_H1 + rev_h2), q3_rev=q3_rev, q3_parent=q3_parent)


def normalized_2026(s):
    p = SCEN[s]
    core = p["rev26"] * p["margin"]
    op_pbt = core + p["recur_other"] + p["assoc"] + p["imp"]
    op_np = op_pbt * (1 - p["tax"])                       # 合并经营净利（不含利息）
    ex_ht = op_np - p["ht_np"] - OTHER_MINORITY            # 迈瑞（除惠泰）经营归母净利
    ht_share = HT_STAKE * p["ht_np"]
    net_int = NET_CASH_CONSOL * NORM_YIELD * (1 - p["tax"])
    parent = ex_ht + ht_share + net_int                   # 正常化归母净利（含净利息，剔除一次性）
    return dict(core=core, op_pbt=op_pbt, op_np=op_np, ex_ht=ex_ht, ht_share=ht_share,
                net_int=net_int, parent=parent)


def years_from_val(d):
    return (d - VAL_DATE).days / 365.25


T_H2 = 0.05                    # 7-12 月流量：至价格日约六成已发生，余下按年底到账，折现期取 0.05 年
T_MID = [years_from_val(date(2027 + i, 7, 1)) for i in range(5)]
T_END = years_from_val(date(2031, 12, 31))


def dcf_ops(s, r, growth=None, margin_shift=0.0, tax=None):
    p = dict(SCEN[s])
    if tax is not None:
        p["tax"] = tax
    g_path = growth if growth is not None else p["growth"]
    if margin_shift:
        p["margin"] = p["margin"] + margin_shift
    core = p["rev26"] * p["margin"]
    op_np = (core + p["recur_other"] + p["assoc"] + p["imp"]) * (1 - p["tax"])
    np0 = op_np - p["ht_np"] - OTHER_MINORITY
    pv_h2 = np0 * H2_SHARE * (1 - g_path[0] / p["ronic"]) / (1 + r) ** T_H2
    rows, npv, npt = [], 0.0, np0
    for i, g in enumerate(g_path):
        npt = npt * (1 + g)
        reinv = g / p["ronic"]
        oe = npt * (1 - reinv)
        pv = oe / (1 + r) ** T_MID[i]
        npv += pv
        rows.append((2027 + i, g, npt, reinv, oe, pv))
    np_t1 = npt * (1 + p["g_t"])
    oe_t1 = np_t1 * (1 - p["g_t"] / p["ronic_t"])
    tv = oe_t1 / (r - p["g_t"])
    pv_tv = tv / (1 + r) ** T_END
    ops = pv_h2 + npv + pv_tv
    return dict(np0=np0, pv_h2=pv_h2, pv_explicit=npv, pv_tv=pv_tv, ops=ops, rows=rows,
                tv_share=pv_tv / ops, oe_t1=oe_t1)


def equity_per_share(s, r=COE, **kw):
    p = SCEN[s]
    d = dcf_ops(s, r, **kw)
    ht = HT_STAKE * HT_MKT_CAP * (1 - p["ht_disc"])
    eq = d["ops"] + NET_CASH_FOR_V + ht + NONOP_OTHER
    return eq / SHARES, d, ht


def weighted(r=COE, probs=PROBS, **kw):
    return sum(probs[s] * equity_per_share(s, r, **kw)[0] for s in probs)


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
    return solve(lambda r: equity_per_share("base", r)[0], 0.03, 0.20, PRICE)


def reverse_dcf_10y():
    """现价隐含：2027-2036 年所有者收益口径的归母经营净利年增 g（再投资率 g/35%），之后 2.5%。"""
    p = SCEN["base"]
    np0 = dcf_ops("base", COE)["np0"]
    ht = HT_STAKE * HT_MKT_CAP * (1 - p["ht_disc"])

    def v(g):
        pv_h2 = np0 * H2_SHARE * (1 - g / p["ronic"]) / (1 + COE) ** T_H2
        tot, npt = pv_h2, np0
        for i in range(10):
            npt *= 1 + g
            t = years_from_val(date(2027 + i, 7, 1))
            tot += npt * (1 - g / p["ronic"]) / (1 + COE) ** t
        oe = npt * (1 + p["g_t"]) * (1 - p["g_t"] / p["ronic_t"])
        tot += oe / (COE - p["g_t"]) / (1 + COE) ** years_from_val(date(2036, 12, 31))
        return (tot + NET_CASH_FOR_V + ht + NONOP_OTHER) / SHARES
    return solve(v, 0.0, 0.30, PRICE)


def reverse_dcf_5y():
    return solve(lambda g: equity_per_share("base", growth=[g] * 5)[0], 0.0, 0.40, PRICE)


def reverse_perpetual():
    """现价隐含永续增速：以 2027 年所有者收益起算的戈登模型（再投资率 g/25%）。"""
    p = SCEN["base"]
    np27 = dcf_ops("base", COE)["np0"] * 1.10
    ht = HT_STAKE * HT_MKT_CAP * (1 - p["ht_disc"])
    target = PRICE * SHARES - NET_CASH_FOR_V - ht - NONOP_OTHER
    return solve(lambda g: np27 * (1 - g / 0.25) / (COE - g), 0.0, 0.0899, target)


def three_stage_base():
    """参考（不入 V）：基准 2032-2036 年增速由 7% 线性降至 3%，2037 起 2.5%。"""
    p = SCEN["base"]
    d = dcf_ops("base", COE)
    npt = d["rows"][-1][2]
    tot = d["pv_h2"] + d["pv_explicit"]
    fade = [0.062, 0.054, 0.046, 0.038, 0.030]
    for i, g in enumerate(fade):
        npt *= 1 + g
        t = years_from_val(date(2032 + i, 7, 1))
        tot += npt * (1 - g / 0.30) / (1 + COE) ** t
    oe = npt * (1 + p["g_t"]) * (1 - p["g_t"] / p["ronic_t"])
    tot += oe / (COE - p["g_t"]) / (1 + COE) ** years_from_val(date(2036, 12, 31))
    ht = HT_STAKE * HT_MKT_CAP * (1 - p["ht_disc"])
    return (tot + NET_CASH_FOR_V + ht + NONOP_OTHER) / SHARES


def main():
    pbt_check = (CORE_EBIT_H1 + OTHER_INC_H1 + INVEST_H1 + FV_H1 + CREDIT_IMP_H1 + ASSET_IMP_H1
                 + DISPOSAL_H1 - FIN_EXP_H1 + NONOP_IN_H1 - NONOP_OUT_H1)
    print(f"核对：上半年利润总额分项合计 {pbt_check:.4f} 对报表 {PBT_H1:.4f}；"
          f"净利 {PBT_H1-TAX_H1:.2f} = 归母 {PARENT_NP_H1:.2f} + 少数 {MINORITY_H1:.2f}")
    rep = reported_2026_estimate()
    print("== 2026 年报口径估计（含汇兑、实际税率；非正常化）==")
    print(f"收入 {rep['rev']:.1f}  核心经营利润率 {rep['core_margin']:.1%}  归母净利 {rep['parent']:.1f}"
          f"（下半年 {rep['parent_h2']:.1f}）  三季度：收入 {rep['q3_rev']:.1f} 归母 {rep['q3_parent']:.1f}")
    print(f"上半年核心经营利润 {CORE_EBIT_H1:.2f}（{CORE_EBIT_H1/REV_H1:.1%}），汇兑损失 {FX_LOSS_H1:.2f}")
    print()
    print("== 经调整净现金 ==")
    print(f"合并口径 {NET_CASH_CONSOL:.2f} = 现金 {CASH:.2f} + 理财 {TRADING_FA:.2f} - 受限 {RESTRICTED:.2f}"
          f" - 经营备付 {OPER_RESERVE:.0f} - 已宣派股利 {DIV_DECLARED:.2f} - 有息负债 {DEBT:.2f} - DiaSys 回购义务 {DIASYS_PUT:.2f}")
    print(f"入 V 口径 {NET_CASH_FOR_V:.2f}（再扣惠泰自有现金 {HT_CASH_EST} 与三季度美元折算损失 {FX_REVAL_Q3}）")
    print(f"惠泰 26.88% 市值 {HT_STAKE*HT_MKT_CAP:.2f}；其他非经营资产 {NONOP_OTHER:.2f}")
    print()
    print("== 2026 正常化 ==")
    for s in ("bear", "base", "bull"):
        n = normalized_2026(s)
        p = SCEN[s]
        print(f"{s}: 收入 {p['rev26']:.1f} 核心利润率 {p['margin']:.1%} 税率 {p['tax']:.0%} → 合并经营净利 {n['op_np']:.1f}；"
              f"除惠泰经营归母 {n['ex_ht']:.1f} + 惠泰 26.88% {n['ht_share']:.2f} + 正常化净利息 {n['net_int']:.2f}"
              f" = 正常化归母净利 {n['parent']:.1f}")
    print()
    vals = {}
    for s in ("bear", "base", "bull"):
        v, d, ht = equity_per_share(s)
        vals[s] = v
        print(f"== {s}（概率 {PROBS[s]:.0%}）V = {v:.2f} 元/股 ==")
        print(f"  起点（2026 正常化，除惠泰经营归母）{d['np0']:.2f}；7-12 月所有者收益现值 {d['pv_h2']:.2f}")
        for (y, g, npt, reinv, oe, pv) in d["rows"]:
            print(f"  {y}: 增速 {g:.1%} 净利 {npt:.1f} 再投资率 {reinv:.1%} 所有者收益 {oe:.1f} 现值 {pv:.1f}")
        print(f"  终值增长 {SCEN[s]['g_t']:.1%}、终值再投资率 {SCEN[s]['g_t']/SCEN[s]['ronic_t']:.1%}，2032 所有者收益 {d['oe_t1']:.1f}"
              f"，终值现值 {d['pv_tv']:.1f}（占经营价值 {d['tv_share']:.0%}）")
        print(f"  经营价值 {d['ops']:.1f} + 净现金 {NET_CASH_FOR_V:.1f} + 惠泰（折价 {SCEN[s]['ht_disc']:.0%}）{ht:.1f}"
              f" + 其他 {NONOP_OTHER:.1f} = {d['ops']+NET_CASH_FOR_V+ht+NONOP_OTHER:.1f} 亿")
    vw = weighted()
    print()
    print(f"加权 V = {vw:.2f}；P/V = {PRICE/vw:.3f}")
    band = ("明显低估" if PRICE / vw <= 0.75 else "温和低估" if PRICE / vw <= 0.90
            else "大致合理" if PRICE / vw <= 1.10 else "偏贵或价值陷阱风险高")
    print(f"分档：{band}；V 不变时各档价格：≤{0.75*vw:.1f} 明显低估，{0.75*vw:.1f}～{0.90*vw:.1f} 温和低估，"
          f"{0.90*vw:.1f}～{1.10*vw:.1f} 大致合理，>{1.10*vw:.1f} 偏贵")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：加权 V = {v8:.2f}（P/V {PRICE/v8:.3f}）；10%：加权 V = {v10:.2f}（P/V {PRICE/v10:.3f}）")
    for s in ("bear", "base", "bull"):
        print(f"   {s}: 8% {equity_per_share(s, 0.08)[0]:.2f}  10% {equity_per_share(s, 0.10)[0]:.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准情景所有者收益流使现值=现价的折现率）= {irr:.2%}")
    print(f"反向 DCF：现价隐含 2027-2036 年增速 {reverse_dcf_10y():.2%}（之后 2.5%）；"
          f"或 2027-2031 年增速 {reverse_dcf_5y():.2%}（之后 2.5%）；或自 2027 年起永续增速 {reverse_perpetual():.2%}")
    print(f"参考（不入 V）：基准三阶段（2032-2036 由 6.2% 降至 3%）V = {three_stage_base():.2f}")
    for ronic in (0.25, 0.50):
        saved = SCEN["base"]["ronic"]
        SCEN["base"]["ronic"] = ronic
        print(f"参考：基准增量回报 {ronic:.0%} 时基准 V = {equity_per_share('base')[0]:.2f}")
        SCEN["base"]["ronic"] = saved
    print(f"股本口径：总股本 {SHARES:.4f} 亿股，无库存股（641,963 股已于 2026-08-07 注销），剔除口径 V 相同")
    pe_rep = PRICE * SHARES / reported_2026_estimate()["parent"]
    pe_norm = PRICE * SHARES / normalized_2026("base")["parent"]
    ex_ops = PRICE * SHARES - NET_CASH_FOR_V - HT_STAKE * HT_MKT_CAP - NONOP_OTHER
    print(f"交叉：现价/2026E 报表归母 {pe_rep:.1f}x，/正常化归母 {pe_norm:.1f}x；"
          f"扣净现金与惠泰市值后/除惠泰经营归母 {ex_ops/normalized_2026('base')['ex_ht']:.1f}x")
    print()
    print("== 证伪条件触发后的 V ==")
    base_g = SCEN["base"]["growth"]
    f1 = weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    print(f"F1 国内复苏落空（权重 50/40/10）：{f1:.2f}")
    f2_probs = {"bear": 0.40, "base": 0.50, "bull": 0.10}
    f2 = (f2_probs["bear"] * equity_per_share("bear")[0]
          + f2_probs["base"] * equity_per_share("base", growth=[g - 0.03 for g in base_g])[0]
          + f2_probs["bull"] * equity_per_share("bull")[0])
    print(f"F2 国际增长失速（基准增速各年 -3pp，权重 40/50/10）：{f2:.2f}")
    f3 = sum(PROBS[s] * equity_per_share(s, margin_shift=-0.015)[0] for s in PROBS)
    print(f"F3 毛利率结构性下滑（各情景核心利润率 -1.5pp）：{f3:.2f}")
    f4 = sum(PROBS[s] * equity_per_share(s, tax=max(SCEN[s]['tax'], 0.15))[0] for s in PROBS)
    print(f"F4 有效税率升至 15%：{f4:.2f}")
    f5 = weighted(probs={"bear": 0.10, "base": 0.40, "bull": 0.50})
    print(f"F5（上行）2027 年收入增 ≥13% 且毛利率 ≥61%（权重 10/40/50）：{f5:.2f}")
    ht_drop = HT_STAKE * (HT_MKT_CAP - 290.0) * (1 - SCEN['base']['ht_disc']) / SHARES
    print(f"参考：惠泰市值跌至 290 亿（商誉减值临界附近）对基准 V 的影响：-{ht_drop:.2f}")


if __name__ == "__main__":
    main()
