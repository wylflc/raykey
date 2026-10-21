# -*- coding: utf-8 -*-
"""圣邦股份（300661）独立估值：所有者收益 DCF（经营口径）+ 经调整净现金 + 非经营资产。

金额单位：亿元人民币；每股价值：元/股。输入全部写在脚本内，`python3 valuation.py` 复现正文与 json 的全部 V。
口径：
- 价格日 2026-10-20，A 股收盘 89.47 元；总股本 6.8715 亿股（腾讯行情口径，含 H 股 0.621013 亿股，无回购专户股份）。
- 每股价值按全部股份（A+H）计算；A 股 P/V 用 A 股价，H 股另按港股收盘折人民币计。
- 经营所有者收益不含利息收入、理财与公允价值收益、联营企业收益（这些在净现金与非经营资产里单独计价）。
- 股份支付费用（2026 年约 2 亿元）按报表计入费用，不加回；研发全部费用化（报表资本化研发为 0）。
"""

# ---------------- 市场与股本 ----------------
PRICE_A = 89.47                 # 元，2026-10-20 A 股收盘（腾讯日线）
SHARES = 6.8715                 # 亿股，行情口径总股本（A+H）
H_SHARES = 0.621013             # 亿股，H 股 54,001,200 + 超额配售 8,100,100（2026H1 报告第 30、115 页）
PRICE_H_HKD = 70.65             # 港元，2026-10-20 03661.HK 收盘（Yahoo 日线）
HKDCNY = 0.85258                # 2026-10-20 港元兑人民币（Yahoo HKDCNY=X）

# ---------------- 资产负债（2026-06-30，2026H1 报告） ----------------
cash = 46.297                   # 货币资金（第 70 页）
restricted = 0.440              # 财产保全冻结（第 18、86 页；一审胜诉、判决未生效）
trading_fa = 20.715             # 交易性金融资产：银行理财本金 20.62 + 公允价值变动（第 70 页）
time_dep_current = 2.113        # 一年内到期的定期存款及利息（第 78 页）
large_cd = 2.362                # 其他非流动资产中的大额存单（第 86 页）
overallot_hkd_m = 681.78        # 超额配售所得款项净额（百万港元，7 月到账，第 115 页）
option_cash_post = 1.20         # 6-30 后期权行权与限制性股票归属约 214 万股 × 约 55 元（估计）
hkd_cash_hkd_m = 3866.87        # 6-30 港币货币性资产（百万港元，按 0.8686 折算，第 102-103 页外币货币性项目）
HKDCNY_0630 = 0.8686
debt_interest = 4.524 + 0.349 + 0.690 + 0.169   # 短借、长借、一年内到期非流动负债、租赁负债
long_payable = 1.906            # 长期应付款：收购子公司剩余股权义务 1.458 + 回购义务 0.449（第 91 页），视同债务
dividend_payable = 0.06
operating_cash_reserve = 3.0    # 经营备付：约 2026E 营收 58 亿 × 5%

overallot_rmb = overallot_hkd_m / 100 * HKDCNY
fx_mark = hkd_cash_hkd_m / 100 * (HKDCNY - HKDCNY_0630)   # 港币资金按 10-20 汇率重估（若仍持有港币）
cash_like = cash - restricted + trading_fa + time_dep_current + large_cd
net_cash_adj = (cash_like + overallot_rmb + option_cash_post + fx_mark
                - debt_interest - long_payable - dividend_payable - operating_cash_reserve)

# ---------------- 非经营资产 ----------------
YOUXUN_SHARES = 0.06154974      # 亿股，持有优迅股份（688807）7.69%（新浪财经 2026-06-30 前十大股东）
YOUXUN_PRICE = 234.53           # 元，2026-10-20 收盘（Yahoo 日线）；限售至 2026-12-21
YOUXUN_HAIRCUT = 0.20           # 所得税（收益部分）与解禁前流动性折扣合计
youxun_value = YOUXUN_SHARES * YOUXUN_PRICE * (1 - YOUXUN_HAIRCUT)
yutai_book = 3.286              # 钰泰半导体，权益法账面（未上市，第 79 页）
haigao_book = 0.419             # 海高启航基金，账面
other_fin_assets = 1.425        # 其他非流动金融资产（公允价值，第 80 页）
non_operating = youxun_value + yutai_book + haigao_book + other_fin_assets

# ---------------- 情景 ----------------
# rev0：2026 年正常化（剔除周期上行超额）营收；opm0：2026 正常化经营利润率（不含利息、理财、联营、补助一次性）
# g：2027-2031 营收增速，2032-2036 线性收敛到 gT；opm 2026→2031 线性到 opm_2031 后持平；
# k：每 1 元新增营收所需净经营资本（存货约 240 天、应收、掩膜与测试设备，扣应付）；roiic_T：终值期增量回报
# 结构：opm = 毛利率 − 研发 − 销售管理 − 税金附加 − 存货及信用减值 + 经常性其他收益
SCEN = {
    "bear": dict(p=0.25, rev0=48.0, gm=0.495, rd=0.245, sga=0.096, surch=0.0035, impair=0.045, oth=0.001,
                 g=[0.10, 0.09, 0.08, 0.08, 0.07], opm_2031=0.130, tax=0.10, k=0.45, gT=0.020, roiic_T=0.15),
    "base": dict(p=0.50, rev0=54.0, gm=0.510, rd=0.225, sga=0.092, surch=0.0035, impair=0.040, oth=0.003,
                 g=[0.16, 0.15, 0.13, 0.12, 0.10], opm_2031=0.185, tax=0.07, k=0.38, gT=0.025, roiic_T=0.20),
    "bull": dict(p=0.25, rev0=58.0, gm=0.520, rd=0.210, sga=0.088, surch=0.0035, impair=0.035, oth=0.004,
                 g=[0.30, 0.25, 0.20, 0.16, 0.13], opm_2031=0.240, tax=0.05, k=0.33, gT=0.025, roiic_T=0.25),
}
NET_INT_RATE = 0.014            # 现金类税前收益率（理财与存款，2026H1 年化约 1.4%）
DEBT_RATE = 0.025               # 有息负债与长期应付款利率（估计）


def opm0(s):
    return s["gm"] - s["rd"] - s["sga"] - s["surch"] - s["impair"] + s["oth"]


def path(s):
    """返回 2026..2036 年的 (年份, 营收, 经营利润率, 经营归母净利, 再投资, 所有者收益)。"""
    years = list(range(2026, 2037))
    g31 = s["g"][-1]
    growth = s["g"] + [g31 + (s["gT"] - g31) * i / 5 for i in range(1, 6)]   # 2032-2036 线性收敛到终值增长
    m0, m31 = opm0(s), s["opm_2031"]
    rows = []
    rev = s["rev0"]
    for i, y in enumerate(years):
        if i == 0:
            g = None
            opm = m0
        else:
            g = growth[i - 1]
            rev_prev = rev
            rev = rev * (1 + g)
            opm = m0 + (m31 - m0) * min(i, 5) / 5
        np_op = rev * opm * (1 - s["tax"])
        reinv = 0.0 if i == 0 else s["k"] * (rev - rev_prev)
        rows.append((y, rev, opm, np_op, reinv, np_op - reinv, g))
    return rows


def ev_operating(s, r):
    rows = path(s)
    pv = 0.0
    for t, row in enumerate(rows[1:], start=1):        # 2027..2036 折到 2026 年末
        pv += row[5] / (1 + r) ** t
    y, rev, opm, np_op, reinv, oe, g = rows[-1]
    rev_T = rev * (1 + s["gT"])
    np_T = rev_T * opm * (1 - s["tax"])
    oe_T = np_T * (1 - s["gT"] / s["roiic_T"])          # 终值期再投资率 = g / 终值增量回报（保守下调）
    tv = oe_T / (r - s["gT"])
    pv_tv = tv / (1 + r) ** (len(rows) - 1)
    return pv, pv_tv


def value_per_share(s, r, shares=SHARES):
    pv, pv_tv = ev_operating(s, r)
    eq = pv + pv_tv + net_cash_adj + non_operating
    return eq / shares, pv, pv_tv, eq


def weighted(r, shares=SHARES):
    return sum(SCEN[k]["p"] * value_per_share(SCEN[k], r, shares)[0] for k in SCEN)


def irr_for_price(s, price_total):
    lo, hi = 0.03, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        pv, pv_tv = ev_operating(s, mid)
        if pv + pv_tv + net_cash_adj + non_operating > price_total:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_growth(price_total, r=0.09):
    """以基准情景利润率、税率与资本强度为准，求现价隐含的 2027-2031 年营收年增速（之后同样 5 年收敛到 2.5%）。"""
    base = dict(SCEN["base"])
    lo, hi = 0.0, 0.80
    for _ in range(200):
        mid = (lo + hi) / 2
        base["g"] = [mid] * 5
        pv, pv_tv = ev_operating(base, r)
        if pv + pv_tv + net_cash_adj + non_operating > price_total:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def normalized_np_2026(s):
    """2026 年正常化归母净利（含净利息、剔除一次性）：经营归母净利 + 税后净利息（按 IPO 后现金全年化）。"""
    gross_cash = cash_like + overallot_rmb + option_cash_post
    net_int = gross_cash * NET_INT_RATE - (debt_interest + long_payable) * DEBT_RATE
    return path(s)[0][3] + net_int * (1 - s["tax"])


def estimate_2026_reported():
    """2026E 报表口径：H1 实际 + 三、四季度估计（三季报 2026-10-30 披露后核对）。"""
    h1_np, h1_np_kf = 4.2032, 3.5567                   # 2026H1 归母、扣非（2026H1 报告第 8 页）
    q3_rev, q4_rev = 15.8, 16.2                        # 估计：二季度 14.97，7 月称下半年订单高于上半年
    h2_rev = q3_rev + q4_rev
    h2_gp = h2_rev * 0.52
    h2_opex = 6.40 + h2_rev * 0.088 + 0.11             # 研发、销售管理、税金附加
    h2_impair = h2_rev * 0.039
    h2_other = 0.25                                    # 其他收益（含补助）
    h2_inv_fv = 0.30                                   # 理财、公允价值与联营收益
    h2_interest = 0.45                                 # IPO 后净利息
    h2_fx = -0.60                                      # 港币资金若未换汇的汇兑损失（6-30 0.8686 → 10-20 0.8526）
    h2_pbt = h2_gp - h2_opex - h2_impair + h2_other + h2_inv_fv + h2_interest + h2_fx
    h2_np = h2_pbt * (1 - 0.05) - 0.02
    h2_nri = (0.20 + 0.30) * 0.9                       # 补助与理财公允价值收益（税后）
    return dict(rev=25.954 + h2_rev, np=h1_np + h2_np, np_kf=h1_np_kf + h2_np - h2_nri, h2_np=h2_np,
                q3_rev=q3_rev, q3_np=h2_np * q3_rev / h2_rev)


if __name__ == "__main__":
    price_total = PRICE_A * SHARES
    price_h_cny = PRICE_H_HKD * HKDCNY
    mcap_ah = (SHARES - H_SHARES) * PRICE_A + H_SHARES * price_h_cny
    print("== 口径 ==")
    print(f"A 股价 × 总股本 = {price_total:.2f} 亿元；A+H 分别计价市值 = {mcap_ah:.2f} 亿元"
          f"（H 股 {PRICE_H_HKD} 港元 ≈ {price_h_cny:.2f} 元，A/H 溢价 {PRICE_A / price_h_cny - 1:.1%}）")
    print(f"现金类 {cash_like:.2f}；超额配售 {overallot_rmb:.2f}；行权款 {option_cash_post:.2f}；港币重估 {fx_mark:.2f}；"
          f"有息负债 {debt_interest:.2f}；长期应付款 {long_payable:.2f}；经营备付 {operating_cash_reserve:.2f}")
    print(f"经调整净现金 net_cash_adj = {net_cash_adj:.2f} 亿元；非经营资产 = {non_operating:.2f} 亿元"
          f"（优迅 {youxun_value:.2f}、钰泰 {yutai_book:.2f}、海高 {haigao_book:.2f}、其他金融资产 {other_fin_assets:.2f}）")
    print()
    for k, s in SCEN.items():
        v, pv, pv_tv, eq = value_per_share(s, 0.09)
        rows = path(s)
        print(f"== {k}（p={s['p']}）2026 正常化：营收 {s['rev0']:.1f}，经营利润率 {opm0(s):.2%}，"
              f"经营归母 {rows[0][3]:.2f}，正常化归母(含净利息) {normalized_np_2026(s):.2f}")
        for y, rev, opm, np_op, reinv, oe, g in rows[1:6]:
            print(f"   {y}: 营收 {rev:7.2f}（{g:+.1%}） 利润率 {opm:.2%} 经营归母 {np_op:6.2f} 再投资 {reinv:5.2f}"
                  f" 所有者收益 {oe:6.2f}（再投资率 {reinv / np_op:.0%}）")
        gnp = [rows[i][3] / rows[i - 1][3] - 1 for i in range(1, 6)]
        print("   经营归母净利增速 2027-2031：" + "、".join(f"{x:.1%}" for x in gnp))
        inc_ret = (rows[5][3] - rows[0][3]) / sum(r[4] for r in rows[1:6])
        print(f"   2027-2031 平均再投资率 {sum(r[4] for r in rows[1:6]) / sum(r[3] for r in rows[1:6]):.0%}，"
              f"增量回报（Δ经营归母/累计再投资）{inc_ret:.0%}；终值增长 {s['gT']:.1%}")
        print(f"   PV(2027-2036) {pv:.1f} + PV(终值) {pv_tv:.1f}（终值占经营价值 {pv_tv / (pv + pv_tv):.0%}）"
              f" + 净现金 {net_cash_adj:.1f} + 非经营 {non_operating:.1f} = {eq:.1f} 亿元 → V = {v:.2f} 元/股")
        print(f"   COE 8% V = {value_per_share(s, 0.08)[0]:.2f}；10% V = {value_per_share(s, 0.10)[0]:.2f}")
    vw = weighted(0.09)
    print()
    print(f"== 概率加权 V = {vw:.2f} 元/股；A 股 P/V = {PRICE_A / vw:.2f}；H 股 P/V = {price_h_cny / vw:.2f}")
    print(f"   COE 8%: V = {weighted(0.08):.2f}（P/V {PRICE_A / weighted(0.08):.2f}）；"
          f"COE 10%: V = {weighted(0.10):.2f}（P/V {PRICE_A / weighted(0.10):.2f}）")
    irr = irr_for_price(SCEN["base"], price_total)
    print(f"   现价隐含回报（基准情景现金流）= {irr:.2%}；牛市情景现金流下 = {irr_for_price(SCEN['bull'], price_total):.2%}")
    rg = reverse_growth(price_total)
    print(f"   反向 DCF（基准利润率路径、9%）：现价隐含 2027-2031 营收年增速 {rg:.1%}")
    # 分档价格
    print(f"   V 不变时分档价格：≤{0.75 * vw:.2f} 明显低估；≤{0.90 * vw:.2f} 温和低估；≤{1.10 * vw:.2f} 大致合理")
    # 稀释对照：估计在外期权约 0.35 亿份、平均行权价约 58 元（库藏股法，按现价）
    opt, k_ex = 0.35, 58.0
    dil = opt * (1 - k_ex / PRICE_A)
    print(f"   稀释对照：估计期权 {opt} 亿份 × (1 − {k_ex}/{PRICE_A}) = {dil:.3f} 亿股 → 加权 V = {weighted(0.09, SHARES + dil):.2f}")
    e = estimate_2026_reported()
    print(f"   2026E 报表口径估计：营收 {e['rev']:.1f}，归母 {e['np']:.2f}，扣非 {e['np_kf']:.2f}"
          f"（三季度营收 {e['q3_rev']:.1f}、归母约 {e['q3_np']:.2f}）；现价/2026E 归母 = {price_total / e['np']:.1f}×")
    ev = price_total - net_cash_adj - non_operating
    ebit_e = 58.0 * opm0(dict(SCEN['bull'], gm=0.52, rd=0.215, sga=0.090, impair=0.038, oth=0.003))
    print(f"   市场 EV（扣经调整净现金与非经营资产）= {ev:.1f} 亿元；EV/2026E 经营利润 {ebit_e:.2f} = {ev / ebit_e:.1f}×；"
          f"EV/基准正常化经营利润 {SCEN['base']['rev0'] * opm0(SCEN['base']):.2f} = {ev / (SCEN['base']['rev0'] * opm0(SCEN['base'])):.1f}×")
    # 证伪情景
    print()
    print("== 证伪触发后的独立 V ==")
    pw = {"bear": 0.40, "base": 0.50, "bull": 0.10}
    v_rew = sum(pw[k] * value_per_share(SCEN[k], 0.09)[0] for k in SCEN)
    print(f"   F0 三季度营收 < 14.0 亿或毛利率 < 49%（概率改为 40/50/10）：V = {v_rew:.2f}")
    f1 = dict(SCEN["bear"]); f1.update(rev0=44.0, gm=0.48)
    print(f"   F1 2027 年营收同比下滑、毛利率 <48%（熊市再下修）：V = {value_per_share(f1, 0.09)[0]:.2f}")
    f2 = dict(SCEN["base"]); f2.update(tax=0.15)
    print(f"   F2 失去重点集成电路设计企业 10% 税率与加计扣除收缩（基准、税率 15%）：V = {value_per_share(f2, 0.09)[0]:.2f}")
    f3 = dict(SCEN["base"]); f3.update(impair=0.06, k=0.50)
    print(f"   F3 存货跌价率 6%、资本强度 0.50（基准）：V = {value_per_share(f3, 0.09)[0]:.2f}")
    f4 = dict(SCEN["bull"])
    print(f"   F4 2026 年营收 ≥ 60 亿且 2027Q2 单季营收 ≥ 18 亿（牛市成立）：V = {value_per_share(f4, 0.09)[0]:.2f}")
