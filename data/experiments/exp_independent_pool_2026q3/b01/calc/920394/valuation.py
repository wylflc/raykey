# -*- coding: utf-8 -*-
"""920394 民士达 独立估值（OI-291 b01，深度版）。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。输入全部写在脚本内，出处见注释与正文「来源」。
"""

PRICE = 39.58            # 2026-10-19 收盘（腾讯日线）
SHARES = 1.4625          # 亿股，2026Q3_report 第 7 页
COE = 0.09               # 股权成本基准（框架统一）；本文判断 10% 更贴合风险，见敏感性
COE_LOW, COE_HIGH = 0.08, 0.10

# ---------------------------------------------------------------------------
# 0. 母公司单体逐季毛利率（2026Q1_report 第 14-15 页、2026H1_report 第 36 页、2026Q3_report 第 17 页；元）
# ---------------------------------------------------------------------------
PARENT = {  # 累计营收, 累计营业成本
    "2025H1": (233_454_385.38, 134_724_579.15),
    "2025Q1-3": (336_951_484.74, 196_028_227.35),
    "2026Q1": (108_682_198.32, 61_823_664.30),
    "2026H1": (223_839_246.47, 131_928_154.63),
    "2026Q1-3": (327_689_420.84, 201_706_375.39),
}


def parent_quarters():
    p = PARENT
    q = {
        "2025Q3": (p["2025Q1-3"][0] - p["2025H1"][0], p["2025Q1-3"][1] - p["2025H1"][1]),
        "2026Q1": p["2026Q1"],
        "2026Q2": (p["2026H1"][0] - p["2026Q1"][0], p["2026H1"][1] - p["2026Q1"][1]),
        "2026Q3": (p["2026Q1-3"][0] - p["2026H1"][0], p["2026Q1-3"][1] - p["2026H1"][1]),
    }
    return {k: (rev / 1e8, 1 - cost / rev) for k, (rev, cost) in q.items()}


# ---------------------------------------------------------------------------
# 1. 经调整净现金与非经营资产（2026-09-30，2026Q3_report 第 11-13 页）
# ---------------------------------------------------------------------------
cash = 1.7211                  # 货币资金
restricted = 0.2827            # 受限：票据保证金 0.0808 + 信用证保证金 0.2019（第 11 页）
op_reserve = 0.35              # 经营备付：约 1 个月付现成本（年付现成本约 3.6 亿），兼顾未付工程尾款
subs_cash = cash - 1.5500      # 子公司持有现金 = 合并 1.7211 − 母公司 1.5500（第 11、13 页）
minority_cash = 0.49 * subs_cash   # 先进制造、中菱少数股东均为 49%（2026H1_report 第 115 页）
cd = 0.7109                    # 债权投资：三年期大额存单 7000 万（1.75%，2028-11-10 到期）+ 应计利息
lease = 0.0389 + 0.0073        # 租赁负债 + 一年内到期非流动负债（无银行借款；中菱尾款 3200 万已于 Q3 付清）
net_cash_adj = cash - restricted - op_reserve - minority_cash + cd - lease

reloc_receivable = 0.8447      # 其他应收款：应收烟台黄渤海新区自然资源和规划局搬迁补偿 8628.53 万（已提 255 万）
reloc_haircut = 0.85           # 回收时点未披露、截至 Q3 九个月未回款：按 85% 计
non_operating = reloc_receivable * reloc_haircut

# ---------------------------------------------------------------------------
# 2. 2026 年正常化归母净利（会计口径：含净利息，剔除补助等一次性项目，中菱按全年备考、含购买价分摊摊销）
# ---------------------------------------------------------------------------
KF_9M, KF_Q3 = 0.6827, 0.1745        # 扣非归母（2026Q3_report 第 3 页）
KF_2025 = 1.0826                     # 2025 扣非归母（2025_annual_report 第 8 页）
FX_Q3_AT = (0.004398 - 0.000448 + 0.010207) * 0.85 * 0.9   # Q3 财务费用拆出汇兑与手续费，税后、九成视为汇兑
FX_9M_AT = (0.011310 - 0.001374 + 0.018271) * 0.85 * 0.9   # 前三季度同口径
INV_STEPUP_AT = (0.2543 - 0.2345) * 0.75 * 0.51           # 中菱存货评估增值，Q3 随销售转出（一次性）
DEAL_FEES_AT = 0.010                 # 并购中介费（管理费用，IR_20260824 第 2 页），估计
ZL_H1_PROFORMA = 0.018               # 中菱 H1 未并表：公允口径归母份额估计（承诺 1700 万/年 − 摊销）× 51% ÷ 2
KF_Q4_E = KF_Q3                      # Q4 按 Q3 扣非水平估计

run_rate = 4 * (KF_Q3 + FX_Q3_AT + INV_STEPUP_AT)
pro_forma = KF_9M + KF_Q4_E + FX_9M_AT + INV_STEPUP_AT + DEAL_FEES_AT + ZL_H1_PROFORMA

NORM_NP_2026 = {"bear": 0.70, "base": 0.85, "bull": 1.05}

# 经济口径调整
NET_INTEREST_AT = 0.03   # 税后利息收入（存款与大额存单），净现金另计，避免重复
PPA_ADDBACK = 0.047      # 中菱购买价分摊：专有技术 2062 万、客户关系 3602 万（Q3 摊销约 266 万/季 ≈ 1040 万/年）
                         # + 固定资产增值 2332 万折旧约 200 万/年；税后（25%）× 51% ≈ 0.047 亿；非现金、无需重置


def e0(s, norm=None):
    norm = norm or NORM_NP_2026
    return norm[s] - NET_INTEREST_AT + PPA_ADDBACK


# ---------------------------------------------------------------------------
# 3. 情景
# ---------------------------------------------------------------------------
def fade(start, end, n=5):
    step = (start - end) / n
    return [round(start - step * (i + 1), 6) for i in range(n)]


SCEN = {
    "bear": dict(
        p=0.30,
        g=[0.02, 0.03, 0.03, 0.03, 0.03] + fade(0.03, 0.02),
        roic=[0.10] * 10, g_term=0.02, roic_term=0.09,
        note="国内低端价格内卷常态化、原料成本不回落，母公司毛利率停在 31%～34%；收入年增 3%～5%，增量回报约等于资本成本"),
    "base": dict(
        p=0.50,
        g=[0.10, 0.09, 0.08, 0.07, 0.06] + fade(0.06, 0.025),
        roic=[0.25] * 5 + [0.13] * 5, g_term=0.025, roic_term=0.12,
        note="原料成本回落、新产线利用率爬坡，母公司毛利率回到 36%～38%；收入年增约 8%，"
             "前 5 年借富余产能（约 4500 吨对约 3000 吨销量）、增量回报 25%"),
    "bull": dict(
        p=0.20,
        g=[0.18, 0.15, 0.13, 0.12, 0.10] + fade(0.10, 0.025),
        roic=[0.30] * 5 + [0.15] * 5, g_term=0.025, roic_term=0.15,
        note="杜邦芳纶易主后份额外溢、海外高端与航空蜂窝放量，毛利率回到 40%～42%；收入年增 12%～15%，"
             "2031 年经济口径净利约 2 亿"),
}


def pv_flow(e_start, g, roic, g_term, roic_term, r):
    """所有者收益现值（亿元）：OE_t = E_t × (1 − g_{t+1}/ROIC_t)，年末折现；第 10 年后 Gordon。"""
    e, pv, path = e_start, 0.0, []
    gs = list(g) + [g_term]
    for t in range(1, 11):
        e *= (1 + gs[t - 1])
        oe = e * (1 - gs[t] / roic[t - 1])
        pv += oe / (1 + r) ** t
        path.append((2026 + t, e, oe))
    oe_term = e * (1 + g_term) * (1 - g_term / roic_term)
    pv_tv = oe_term / (r - g_term) / (1 + r) ** 10
    return pv + pv_tv, pv_tv, path


def pv_ops(s, r, norm=None):
    sc = SCEN[s]
    return pv_flow(e0(s, norm), sc["g"], sc["roic"], sc["g_term"], sc["roic_term"], r)


def to_share(ops, with_non_op=True):
    return (ops + net_cash_adj + (non_operating if with_non_op else 0.0)) / SHARES


def v_per_share(s, r, norm=None, with_non_op=True):
    return to_share(pv_ops(s, r, norm)[0], with_non_op)


def weighted(r, probs=None, norm=None, with_non_op=True):
    probs = probs or {k: SCEN[k]["p"] for k in SCEN}
    return sum(probs[k] * v_per_share(k, r, norm, with_non_op) for k in SCEN)


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


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 920394 民士达 独立估值（价格日 2026-10-19，现价 %.2f 元，股本 %.4f 亿股，市值 %.2f 亿元）=="
          % (PRICE, SHARES, PRICE * SHARES))
    pq = parent_quarters()
    print("母公司单体毛利率：" + "；".join("%s %.1f%%（营收 %.3f 亿）" % (k, 100 * gm, rev)
                                   for k, (rev, gm) in pq.items()))
    print("经调整净现金 %.3f 亿（现金 %.4f − 受限 %.4f − 经营备付 %.2f − 少数股东应占子公司现金 %.4f + 大额存单 %.4f − 租赁 %.4f）"
          % (net_cash_adj, cash, restricted, op_reserve, minority_cash, cd, lease))
    print("非经营资产 %.3f 亿（搬迁补偿应收 %.4f × %.2f）；合计 %.3f 亿 = %.2f 元/股"
          % (non_operating, reloc_receivable, reloc_haircut, net_cash_adj + non_operating,
             (net_cash_adj + non_operating) / SHARES))
    print()
    print("正常化参照：Q3 年化 %.3f 亿（扣非 %.4f + 汇兑还原 %.4f + 存货增值 %.4f，×4）；"
          "全年备考 %.3f 亿；2025 扣非 %.4f 亿" % (run_rate, KF_Q3, FX_Q3_AT, INV_STEPUP_AT, pro_forma, KF_2025))
    print("2026 正常化归母净利（会计口径，含净利息）：熊 %.2f／基准 %.2f／牛 %.2f 亿"
          % (NORM_NP_2026["bear"], NORM_NP_2026["base"], NORM_NP_2026["bull"]))
    print("经济口径 E0（− 税后利息 %.3f + 购买价分摊加回 %.3f）：熊 %.3f／基准 %.3f／牛 %.3f 亿"
          % (NET_INTEREST_AT, PPA_ADDBACK, e0("bear"), e0("base"), e0("bull")))
    print()
    for s in ("bear", "base", "bull"):
        ops, pv_tv, path = pv_ops(s, COE)
        v = to_share(ops)
        sc = SCEN[s]
        print("[%s] p=%.2f  V=%.2f 元/股  经营价值 %.2f 亿（终值占 %.0f%%）  P/V=%.2f"
              % (s, sc["p"], v, ops, 100 * pv_tv / ops, PRICE / v))
        print("    增速 2027-2031：%s；2032-2036：%s；终值 g=%.3f、终值 ROIC=%.2f；前 5 年增量回报 %.2f"
              % ([round(x, 3) for x in sc["g"][:5]], [round(x, 3) for x in sc["g"][5:]],
                 sc["g_term"], sc["roic_term"], sc["roic"][0]))
        print("    逐年（年份: 经济口径利润 E / 所有者收益 OE）：" +
              "; ".join("%d:%.3f/%.3f" % (y, e, oe) for y, e, oe in path[:5]) + " …… " +
              "%d:%.3f/%.3f" % path[-1])
        print("    " + sc["note"])
    vw = weighted(COE)
    pv = PRICE / vw
    print()
    print("加权 V = %.2f 元/股；P/V = %.2f → %s" % (vw, pv, band(pv)))
    v8, v10, v11 = weighted(COE_LOW), weighted(COE_HIGH), weighted(0.11)
    print("股权成本敏感性：8%% → %.2f；9%% → %.2f；10%% → %.2f；11%% → %.2f 元/股" % (v8, vw, v10, v11))
    print("  三情景 @8%%：%s；@10%%：%s" % (
        "/".join("%.2f" % v_per_share(k, COE_LOW) for k in ("bear", "base", "bull")),
        "/".join("%.2f" % v_per_share(k, COE_HIGH) for k in ("bear", "base", "bull"))))
    print("北交所流动性折价单列：V×0.90 = %.2f；V×0.85 = %.2f（不计入独立 V）" % (0.90 * vw, 0.85 * vw))

    irr = solve(lambda r: v_per_share("base", r), 0.0255, 0.40, PRICE)
    irr_bull = solve(lambda r: v_per_share("bull", r), 0.0255, 0.40, PRICE)
    print("现价隐含回报（基准情景所有者收益流）= %.2f%%；（牛市情景）= %.2f%%" % (100 * irr, 100 * irr_bull))

    # 反向 DCF
    ops_needed = PRICE * SHARES - net_cash_adj - non_operating
    E0 = e0("base")

    def v_const_growth(g):  # 10 年所有者收益按 g 增长且增长免再投资（最宽松），之后 2.5%、ROIC 12%
        pv_, oe = 0.0, E0
        for t in range(1, 11):
            oe *= (1 + g)
            pv_ += oe / (1 + COE) ** t
        tv = oe * 1.025 * (1 - 0.025 / 0.12) / (COE - 0.025)
        return pv_ + tv / (1 + COE) ** 10

    g10 = solve(v_const_growth, 0.0, 0.60, ops_needed)

    def v_gordon(g, roic=0.15):
        return E0 * (1 + g) * (1 - g / roic) / (COE - g)

    g_perp = solve(v_gordon, 0.0, 0.0899, ops_needed)
    print("反向 DCF：现价对应经营价值 %.2f 亿 = %.1f 倍基准 E0；需 10 年所有者收益年增 %.1f%%"
          "（增长免再投资、之后 2.5%%），或永续增长 %.2f%%（ROIC 15%%、再投资率 g/ROIC）"
          % (ops_needed, ops_needed / E0, 100 * g10, 100 * g_perp))
    print("  即 2036 年经济口径归母利润约 %.1f 亿（2025 年扣非 %.2f 亿）" % (E0 * (1 + g10) ** 10, KF_2025))

    # 交叉验证
    ttm_np, ttm_kf, equity = 1.1452, 0.8930, 8.6164
    mcap = PRICE * SHARES
    minority = 0.8562
    ev = mcap - net_cash_adj - non_operating + minority
    ebit_norm = 1.12   # 2026 基准正常化合并 EBIT（扣非税前、不含利息与补助，含中菱全年）
    rev_pf = 4.85      # 2026 备考营收（前三季度 3.574 + Q4 约 1.25 + 中菱上半年约 0.35，扣内部交易）
    print()
    print("交叉验证：PE(TTM) %.1f、PE(TTM 扣非) %.1f、PB %.2f、股息率 %.2f%%、EV %.1f 亿、"
          "EV/正常化 EBIT %.0f 倍、EV/备考营收 %.1f 倍（杜邦芳纶出售约 1.4 倍营收）"
          % (mcap / ttm_np, mcap / ttm_kf, mcap / equity, 100 * 0.20 / PRICE, ev, ev / ebit_norm, ev / rev_pf))
    vb = v_per_share("base", COE)
    print("  基准 V 对应 2026 正常化 PE %.1f 倍、PB %.2f 倍；加权 V 对应 PE %.1f 倍"
          % ((vb * SHARES - net_cash_adj - non_operating) / NORM_NP_2026["base"], vb * SHARES / equity,
             (vw * SHARES - net_cash_adj - non_operating) / NORM_NP_2026["base"]))
    print("V 不变时各档价格：≤%.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    # 压力测试：利润回到 0.50 亿、十年零增长
    st_ops = pv_flow(0.50, [0.0] * 10, [0.09] * 10, 0.01, 0.09, COE)[0]
    print("压力测试（E0 0.50 亿、零增长、终值 1%%）：V = %.2f" % to_share(st_ops))

    # 证伪条件触发后的 V
    print()
    w_down = {"bear": 0.55, "base": 0.40, "bull": 0.05}
    w_up = {"bear": 0.10, "base": 0.50, "bull": 0.40}
    f1 = weighted(COE, w_down)
    f2 = weighted(COE, w_down, norm={k: v - 0.12 for k, v in NORM_NP_2026.items()})
    f3 = weighted(COE, with_non_op=False)
    f4 = weighted(COE, w_up)
    sb = SCEN["bull"]
    f5_ops = pv_flow(e0("bull"), [0.37, 0.37, 0.20, 0.15, 0.12] + fade(0.12, 0.025),
                     sb["roic"], sb["g_term"], sb["roic_term"], COE)[0]
    f5 = to_share(f5_ops)
    print("证伪触发后的 V：F1 2026 扣非 <0.82 亿或 Q4 毛利率 <32%% → %.2f；"
          "F2 2027H1 母公司毛利率 <31%% → %.2f；F3 搬迁款至 2027-06-30 未回 → %.2f；"
          "F4 2027H1 母公司营收 ≥+15%% 且毛利率 ≥40%% → %.2f；F5 2028 扣非 ≥2.0 亿（重估）→ %.2f"
          % (f1, f2, f3, f4, f5))


if __name__ == "__main__":
    main()
