# -*- coding: utf-8 -*-
"""中际旭创（300308）独立估值：归母所有者收益 DCF、三情景、反向 DCF、隐含回报。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在本脚本内，来源见同批 companies/300308_中际旭创.md。
估值基准日 2026-10-20；资产负债表取 2026-06-30，再计入 7～10 月已发生的 H 股募资、回购与中期分红。
"""

PRICE = 647.90                      # A 股 2026-10-20 收盘（元）
SHARES_QUOTE = 11.7791              # 行情口径总股本（亿股，A 11.1523 + H 0.62675，含回购专户股份）
BUYBACK_TO_CANCEL = 0.05653063      # 回购专户股份 565.3063 万股，2026-10-15 公告拟全部注销
SHARES = SHARES_QUOTE - BUYBACK_TO_CANCEL   # 每股价值所用股本 11.7226 亿股（A+H）

# ---------- 经调整净现金（无杠杆口径，亿元） ----------
CASH_0630 = 63.97                   # 货币资金
RESTRICTED = 0.33                   # 保函保证金
HKD_CNY = 0.8686                    # 2026-06-30 报表折算汇率
H_BASE_GROSS_HKD = 534.10           # 基础发行 5,450 万股 × 980 港元
H_BASE_NET_RATIO = 0.986            # 基础发行费用率估计 1.4%（超额配售部分实际约 0.9%，另加固定上市费用）
H_OVERALLOT_NET_HKD = 79.387        # 超额配售 817.5 万股净额（2026-08-27 公告）
H_NET_CNY = (H_BASE_GROSS_HKD * H_BASE_NET_RATIO + H_OVERALLOT_NET_HKD) * HKD_CNY
BUYBACK_CASH = 49.9725              # 2026-09 回购支付金额
INTERIM_DIV = 1.20 * (SHARES_QUOTE - BUYBACK_TO_CANCEL)   # 2026 中期每股 1.20 元，回购专户股份不参与
DEBT = 3.99 + 4.87 + 7.11 + 0.59 + 1.40   # 短借 + 长借 + 一年内到期长借 + 租赁负债（含一年内到期）
REV_2026E = 928.0
OPER_RESERVE = 0.025 * REV_2026E    # 经营备付：2026E 营收的 2.5%
NET_CASH_ADJ = (CASH_0630 - RESTRICTED + H_NET_CNY - BUYBACK_CASH - INTERIM_DIV
                - DEBT - OPER_RESERVE)

# 非经营资产：交易性权益工具 25.29（上市供应链股权）+ 其他非流动金融资产 9.38，扣浮盈递延税
NON_OP = 25.29 + 9.38 - 0.15 * 5.43
# 2026 正常化归母净利另计 H 股募资净额 8～12 月利息（混合收益率 2.5%，税率 15%）
NORM_INTEREST = H_NET_CNY * 0.025 * 5 / 12 * 0.85
# 长期应付款 50.57 亿元（7.425 亿美元）为 TeraHop 外部投资人退出权的计量，按公允价值以新 H 股或
# 「现金须认购新股」结算，少数股东利润已在归母口径扣除，不另作债务扣除（敏感性见 LTP_SENS）。
LONG_TERM_PAYABLE = 50.57

# ---------- 2026 下半年（7～12 月）归母所有者收益 ----------
Q3_REV, Q4_REV = 245.0, 265.0       # 2026Q2 营收 222.81，按环比 +10%、+8% 估计
H2_MARGIN = 0.335                   # 归母扣非净利率（2026Q2 为 33.1%）
H2_NP = (Q3_REV + Q4_REV) * H2_MARGIN
PARENT_SHARE = 0.92                 # 再投资中归母承担的比例（2026H1 少数股东损益占净利 7.3%）
H2_REINV = PARENT_SHARE * (0.22 * ((Q4_REV - 222.81) * 4) + 50.0)   # 营运资本增量 + 下半年净资本开支
H2_OE = H2_NP - H2_REINV

YEARS = [2027, 2028, 2029, 2030, 2031]

SCEN = {
    # 营收同比、归母净利率（报表口径，含少数股东扣除与税率上升）、终值净利率、终值增长、增量回报
    "bear": dict(p=0.25, g=[0.25, -0.20, -0.15, 0.00, 0.04], m=[0.29, 0.20, 0.16, 0.15, 0.15],
                 m_t=0.15, g_t=0.020, roe_t=0.15),
    "base": dict(p=0.50, g=[0.50, 0.20, -0.15, 0.03, 0.05], m=[0.31, 0.28, 0.225, 0.22, 0.22],
                 m_t=0.22, g_t=0.025, roe_t=0.20),
    "bull": dict(p=0.25, g=[0.70, 0.30, 0.12, 0.06, 0.05], m=[0.33, 0.32, 0.30, 0.285, 0.27],
                 m_t=0.26, g_t=0.025, roe_t=0.25),
}
NWC_UP, NWC_DOWN = 0.22, 0.18       # 营运资本占营收增量；收缩时按 18% 释放（存货减值留余量）
FA_UP = 0.15                        # 固定资产+在建占营收（2026-06-30 为 135/891）
CHURN = 0.01                        # 技术换代带来的超折旧资本开支，占营收


def path(s):
    rev, out = REV_2026E, []
    for g, m in zip(s["g"], s["m"]):
        new = rev * (1 + g)
        d = new - rev
        nwc = NWC_UP * d if d > 0 else NWC_DOWN * d
        capex_net = FA_UP * max(d, 0) + CHURN * new
        np_ = new * m
        oe = np_ - PARENT_SHARE * (nwc + capex_net)
        out.append(dict(rev=new, np=np_, oe=oe, reinv=np_ - oe))
        rev = new
    return out


def value(s, coe=0.09, extra_cash=0.0):
    rows = path(s)
    pv = H2_OE / (1 + coe) ** 0.1
    for i, r in enumerate(rows):
        pv += r["oe"] / (1 + coe) ** (0.7 + i)          # 年中折现，2027 年中距基准日约 0.7 年
    rev_t = rows[-1]["rev"] * (1 + s["g_t"])
    np_t = rev_t * s["m_t"]
    reinv_rate = s["g_t"] / s["roe_t"]
    tv = np_t * (1 - reinv_rate) / (coe - s["g_t"])
    pv_tv = tv / (1 + coe) ** 5.2                        # 2031 年末距基准日约 5.2 年
    equity = pv + pv_tv + NET_CASH_ADJ + NON_OP + extra_cash
    return dict(v=equity / SHARES, equity=equity, pv_explicit=pv, pv_tv=pv_tv,
                tv_share=pv_tv / (pv + pv_tv), rows=rows, np_t=np_t, reinv_rate=reinv_rate)


def weighted(coe=0.09, probs=None, extra_cash=0.0):
    probs = probs or {k: s["p"] for k, s in SCEN.items()}
    return sum(probs[k] * value(SCEN[k], coe, extra_cash)["v"] for k in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    """基准情景所有者收益流（含终值与净现金）现值等于现价的折现率。"""
    return solve(lambda r: value(SCEN["base"], r)["v"], 0.03, 0.30, PRICE)


def reverse_dcf_growth():
    """现价隐含：2026E 正常化所有者收益起步，前 10 年复合增速 g，其后 2.5% 永续，9% 折现。"""
    oe0 = 302.0 * (1 - 0.25)        # 2026E 归母扣非约 302 亿元，再投资率按 25%
    def v(g):
        pv, oe = 0.0, oe0
        for t in range(1, 11):
            oe *= (1 + g)
            pv += oe / 1.09 ** (t - 0.3)
        tv = oe * 1.025 / (0.09 - 0.025) / 1.09 ** 9.7
        return (pv + tv + NET_CASH_ADJ + NON_OP) / SHARES
    return solve(v, -0.20, 0.40, PRICE)


FALSIFIERS = {
    # 触发后改用的概率（bear, base, bull）
    "F1 2026Q3 归母扣非 < 70 亿元或毛利率 < 43%": dict(bear=0.45, base=0.45, bull=0.10),
    "F2 2027H1 营收同比 < 20%": dict(bear=0.60, base=0.35, bull=0.05),
    "F3 美国立法或行政令禁止中国企业光模块进入商用数据中心": dict(bear=0.80, base=0.20, bull=0.00),
    "F4 2026 年经营现金流 < 120 亿元": dict(bear=0.40, base=0.50, bull=0.10),
    "F5 北美四大云厂商 2027 资本开支指引增速 < 10%": dict(bear=0.55, base=0.40, bull=0.05),
}


def main():
    print(f"每股价值股本 {SHARES:.4f} 亿股（A {SHARES_QUOTE - 0.62675 - BUYBACK_TO_CANCEL:.4f} + H 0.62675）")
    print(f"H 股募资净额 {H_NET_CNY:.1f} 亿元；中期分红 {INTERIM_DIV:.2f}；有息负债 {DEBT:.2f}；经营备付 {OPER_RESERVE:.1f}")
    print(f"经调整净现金 {NET_CASH_ADJ:.1f} 亿元；非经营资产 {NON_OP:.1f} 亿元")
    print(f"2026 下半年：归母净利 {H2_NP:.1f}，再投资 {H2_REINV:.1f}，所有者收益 {H2_OE:.1f}")
    print(f"2026E 营收 {REV_2026E:.0f}；归母扣非 {130.92 + H2_NP:.1f}（上半年 130.92 + 下半年 {H2_NP:.1f}）")
    for k, s in SCEN.items():
        r = value(s)
        print(f"\n[{k}] p={s['p']:.2f}  V={r['v']:.1f} 元/股  股权价值 {r['equity']:.0f} 亿元"
              f"  显性期现值 {r['pv_explicit']:.0f}  终值现值 {r['pv_tv']:.0f}  终值占经营价值 {r['tv_share']:.0%}")
        print("  年份  营收  营收增速  归母净利  所有者收益  再投资率")
        prev = REV_2026E
        for y, row in zip(YEARS, r["rows"]):
            print(f"  {y} {row['rev']:7.0f} {row['rev'] / prev - 1:8.0%} {row['np']:8.0f} {row['oe']:9.0f} "
                  f"{row['reinv'] / row['np']:8.0%}")
            prev = row["rev"]
        print(f"  终值：营收增速 {s['g_t']:.1%}，净利率 {s['m_t']:.1%}，归母净利 {r['np_t']:.0f}，再投资率 {r['reinv_rate']:.1%}")
        oe = [H2_OE * 2] + [row["oe"] for row in r["rows"]]
        gr = [oe[i + 1] / oe[i] - 1 for i in range(len(oe) - 1)]
        print("  所有者收益增速（2027～2031，2026 以下半年×2 为基）：" + "、".join(f"{x:.1%}" for x in gr))
    vw = weighted()
    print(f"\n加权 V = {vw:.1f} 元/股；P/V = {PRICE / vw:.2f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：V = {v8:.1f}（P/V {PRICE / v8:.2f}）；10%：V = {v10:.1f}（P/V {PRICE / v10:.2f}）")
    for k in SCEN:
        print(f"  {k}: 8% {value(SCEN[k], 0.08)['v']:.1f} / 9% {value(SCEN[k])['v']:.1f} / 10% {value(SCEN[k], 0.10)['v']:.1f}")
    print(f"基准情景隐含回报（现值=现价的折现率）：{implied_irr():.2%}")
    print(f"反向 DCF：现价隐含 10 年所有者收益复合增速 {reverse_dcf_growth():.1%}（其后 2.5%，9% 折现）")
    vq = vw * SHARES / SHARES_QUOTE
    print(f"对照：按行情口径 11.7791 亿股（不扣回购股份）V = {vq:.1f}，P/V = {PRICE / vq:.2f}")
    vl = weighted(extra_cash=-LONG_TERM_PAYABLE)
    print(f"敏感性：长期应付款 50.57 亿元按现金债务扣除 V = {vl:.1f}（P/V {PRICE / vl:.2f}）")
    for name, pr in FALSIFIERS.items():
        print(f"证伪 {name}：V = {weighted(probs=pr):.1f}")
    print("V 不变时各档价格：≤0.75 明显低估 {:.1f}；0.90 温和低估上沿 {:.1f}；1.10 大致合理上沿 {:.1f}".format(
        0.75 * vw, 0.90 * vw, 1.10 * vw))
    # 2026 正常化归母净利：2026E 营收 × 各情景 2027～2031 平均归母净利率（周期中枢）
    norm = {k: REV_2026E * sum(s["m"]) / len(s["m"]) + NORM_INTEREST for k, s in SCEN.items()}
    print(f"2026 正常化归母净利（报表口径，含 H 股资金 8～12 月税后利息 {NORM_INTEREST:.1f}）：" + "、".join(f"{k} {v:.0f}" for k, v in norm.items()))
    b = value(SCEN["base"])
    reinv = H2_REINV + sum(r["reinv"] for r in b["rows"])
    np_sum = H2_NP + sum(r["np"] for r in b["rows"])
    inc_ret = (b["rows"][-1]["np"] - (norm["base"] - NORM_INTEREST)) / reinv
    print(f"基准情景 2026H2～2031 再投资率 {reinv / np_sum:.1%}；增量回报（2031 归母净利较 2026 正常化值之增量 ÷ 累计再投资）{inc_ret:.1%}")
    # 交叉验证（TTM = 2025 年报 − 2025 中报 + 2026 中报）
    pbt_ttm = 136.00 - 48.81 + 172.31
    fin_gain_ttm = (3.79 + 0.14) - (0.66 - 0.01) + (1.90 + 5.37)
    net_int_ttm = (2.44 - 1.11 + 1.55) - (0.63 - 0.34 + 0.32)
    ebit_ttm = pbt_ttm - fin_gain_ttm - net_int_ttm
    mi_share = (7.82 - 2.47 + 10.82) / (115.80 - 42.42 + 147.33)
    mcap_all = PRICE * SHARES
    ev = mcap_all * (1 + mi_share / (1 - mi_share)) - NET_CASH_ADJ - NON_OP
    ebit_26 = (130.92 + H2_NP) / (1 - mi_share) / (1 - 0.145)
    print(f"交叉验证：A 价×全部股本 {mcap_all:.0f} 亿元；PE(TTM 归母 204.53) {mcap_all / 204.53:.1f}×；"
          f"PE(2026E 归母扣非 {130.92 + H2_NP:.0f}) {mcap_all / (130.92 + H2_NP):.1f}×；PE(2026 正常化基准) {mcap_all / norm['base']:.1f}×")
    print(f"  EBIT(TTM) {ebit_ttm:.1f}，少数股东占净利 {mi_share:.1%}，EV {ev:.0f}，EV/EBIT(TTM) {ev / ebit_ttm:.1f}×，"
          f"EV/EBIT(2026E {ebit_26:.0f}) {ev / ebit_26:.1f}×")
    div_yield = 2.20 / PRICE
    bb_yield = BUYBACK_CASH / mcap_all
    print(f"  近 12 个月股息率 {div_yield:.2%}，回购（拟注销）收益率 {bb_yield:.2%}，合计 {div_yield + bb_yield:.2%}")


if __name__ == "__main__":
    main()
