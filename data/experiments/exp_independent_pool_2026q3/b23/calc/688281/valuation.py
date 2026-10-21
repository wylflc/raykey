#!/usr/bin/env python3
"""华秦科技（688281）独立估值：归母所有者收益 DCF（三情景）＋反向 DCF＋隐含回报＋交叉验证。

金额单位亿元，每股价值元/股。价格日 2026-10-21，现价 46.83 元，总股本 3.8160 亿股（无回购专户股份）。
最新定期报告 2026 中报（2026-06-30）；三季报预约 2026-10-23。
运行：python3 valuation.py
"""

PRICE = 46.83
SHARES = 3.8160          # 亿股，腾讯行情口径＝2026H1 资产负债表股本 381,598,945 股
COE = 0.09
VAL_DATE_OFFSET = 113 / 365   # 2026-06-30 → 2026-10-21

# ---------------------------------------------------------------------------
# 1. 经调整净现金（2026-06-30 合并报表，2026H1_report 第 66–68、34、147–152、192 页）
# ---------------------------------------------------------------------------
CASH = 10.5647             # 货币资金
STRUCT_DEPOSIT = 16.7005   # 交易性金融资产＝结构性存款（第 35 页）
RESTRICTED = 0.0027 + 0.0239   # 票据保证金＋项目专户资金（第 34 页）
ST_LOAN = 3.4341           # 短期借款（含票据贴现 0.137、保理 0.011）
LT_LOAN = 3.8842           # 长期借款（保证借款，2.05%–2.85%）
LT_CURRENT = 0.9504        # 一年内到期的长期借款
LINGBI_LOAN = 0.10         # 其他应付款中灵璧县工业投资发展有限公司借款（尚未到期）
DECLARED_DIV = 0.3434      # 2026 半年度分红，2026-09-03 除息，现价已除息
TRANSFER_PROCEEDS = 0.53   # 2026-07-01 交割的子公司少数股权转让款（智造 0.15＋光声 0.05＋瑞华晟 0.33）
OP_RESERVE = 1.50          # 经营备付（约 2026E 营收的 9%；回款集中在四季度）
LEASE = 1.0511 + 0.1051    # 租赁负债（含一年内到期）：所有者收益以净利润为起点、已扣使用权资产折旧与利息，只列示不扣
NON_OPERATING = 0.2190 + 0.0607   # 长期股权投资＋其他权益工具投资（账面）

DEBT = ST_LOAN + LT_LOAN + LT_CURRENT + LINGBI_LOAN
CASH_LIKE = CASH + STRUCT_DEPOSIT
NET_CASH_ADJ = (CASH_LIKE - RESTRICTED - DEBT - DECLARED_DIV
                + TRANSFER_PROCEEDS - OP_RESERVE)

# ---------------------------------------------------------------------------
# 2. 经营假设（本部＝母公司报表；子公司按 2026-07-01 交割后的持股比例计归母）
# ---------------------------------------------------------------------------
TAX = 0.125            # 本部有效税率（2024 13.2%、2025 11.9%、2026H1 11.4%）
SBC_RATE = 0.025       # 常态化股份支付占本部营收（2026 激励计划总费用约 1.5 亿摊 4.6 年；2026 实际约 0.48 亿前置）
OTHER_INC_RATE = 0.004 # 经常性其他收益（先进制造业增值税加计抵减等）占本部营收
WC_RATE_P = 0.55       # 本部增量营运资金／增量营收（合并口径 2021→2025 实测约 0.63，2022→2025 约 0.56）
WC_RATE_S = 0.45       # 子公司增量营运资金／增量营收（华秦智造以来料加工为主，存货占用较低）
SUB_FUND = 0.75        # 子公司再投资由上市公司承担的比例（持股约 50%，但借款与商票承兑超出持股比例）
CAPEX_INT = 0.20       # 2029 年起增长性资本开支（资本开支−折旧摊销）／增量合并营收
NET_CAPEX_EARLY = {2026: 0.80, 2027: 0.50, 2028: 0.40}   # 本部新园区已转固、二期缩至 2 亿；子公司产线收尾
ATTR_CAPEX = 0.85      # 资本开支净额的归母比例
NET_INT_AFTER_TAX = 0.19   # 2026 正常化归母净利含的税后净利息（结构性存款＋利息收入约 0.40，利息支出约 0.19）
H1_2026_FCF_ATTR = (0.6803 - 1.2682) * 0.90   # 2026H1 经营现金流−购建长期资产（归母约九成），已体现在 6-30 现金中

BASE_YEAR_REV = {"parent_2025": 10.1818, "subs_2025": 12.4376 - 10.1818}

SCENARIOS = {
    "bear": dict(
        p=0.25, rp26=11.6, gp=[0.05, 0.04, 0.03, 0.03, 0.03], m26=0.34, m=0.32,
        subs=[-0.65, -0.55, -0.45, -0.35, -0.25, -0.15], rs26=4.0, gs=0.08, tg=0.020,
        assumptions="本部 2026 营收 11.6 亿（+14%），2027–2031 年增 5%→3%；核心 EBIT 率（未扣股份支付）34%→32%"
                    "（审价降价与竞争）；子公司归母亏损 0.65 亿逐年收窄、2033 年归零；终值增长 2.0%"),
    "base": dict(
        p=0.50, rp26=12.3, gp=[0.14, 0.12, 0.10, 0.08, 0.07], m26=0.375, m=0.37,
        subs=[-0.50, -0.25, 0.00, 0.15, 0.30, 0.40], rs26=4.2, gs=0.20, tg=0.025,
        assumptions="本部 2026 营收 12.3 亿（+21%），2027–2031 年增 14%→7%，2032–2036 线性降至 2.5%；"
                    "核心 EBIT 率 37.5%→37%；子公司归母 −0.50 亿（2026）→2028 年盈亏平衡→2031 年 +0.40 亿"),
    "bull": dict(
        p=0.25, rp26=13.0, gp=[0.20, 0.18, 0.15, 0.12, 0.10], m26=0.40, m=0.42,
        subs=[-0.45, -0.10, 0.25, 0.55, 0.85, 1.10], rs26=4.4, gs=0.30, tg=0.025,
        assumptions="本部 2026 营收 13.0 亿（+28%），2027–2031 年增 20%→10%；核心 EBIT 率回到 2024 年的 40%–42%；"
                    "陶瓷基复材等子公司 2028 年起盈利，2031 年归母 +1.10 亿"),
}

YEARS = list(range(2026, 2037))   # 2026（只取下半年）…2036；2037 起终值


def build(s, const_g=None):
    """逐年生成本部营收、子公司营收、归母经营净利（不含净利息）与归母所有者收益。
    const_g 给定时，本部营收 2027–2036 年按该常数增长（反向 DCF 用）。"""
    rp, rs = {}, {}
    rp[2026], rs[2026] = s["rp26"], s["rs26"]
    g_last = s["gp"][-1]
    gs_last = s["gs"]
    for i, y in enumerate(range(2027, 2037)):
        if y <= 2031:
            g = s["gp"][i]
            g_s = s["gs"]
        else:   # 2032–2036 线性降至终值增长
            k = y - 2031
            g = g_last + (s["tg"] - g_last) * k / 5
            g_s = gs_last + (s["tg"] - gs_last) * k / 5
        if const_g is not None:
            g = const_g
        rp[y] = rp[y - 1] * (1 + g)
        rs[y] = rs[y - 1] * (1 + g_s)
    rows = []
    prev_rp, prev_rs = BASE_YEAR_REV["parent_2025"], BASE_YEAR_REV["subs_2025"]
    subs_path = dict(zip(range(2026, 2032), s["subs"]))
    for y in YEARS:
        m = s["m26"] if y == 2026 else s["m"]
        core = (rp[y] * m - SBC_RATE * rp[y] + OTHER_INC_RATE * rp[y]) * (1 - TAX)
        if y in subs_path:
            sub = subs_path[y]
        else:
            last = subs_path[2031]
            if last >= 0:
                sub = last * (rp[y] / rp[2031])
            else:   # 亏损子公司 2033 年前关停或扭亏
                sub = min(0.0, last * (2033 - y) / 2)
        np_op = core + sub
        d_rp, d_rs = rp[y] - prev_rp, rs[y] - prev_rs
        d_rev = d_rp + d_rs
        if y in NET_CAPEX_EARLY:
            net_capex = NET_CAPEX_EARLY[y]
        else:
            net_capex = CAPEX_INT * d_rev
        reinv = WC_RATE_P * d_rp + SUB_FUND * WC_RATE_S * d_rs + ATTR_CAPEX * net_capex
        oe = np_op - reinv
        rows.append(dict(year=y, rp=rp[y], rs=rs[y], rev=rp[y] + rs[y], core=core, sub=sub,
                         np_op=np_op, reinv=reinv, oe=oe))
        prev_rp, prev_rs = rp[y], rs[y]
    # 终值：2037 年
    last = rows[-1]
    tg = s["tg"]
    np37 = last["np_op"] * (1 + tg)
    reinv37 = (WC_RATE_P * last["rp"] + SUB_FUND * WC_RATE_S * last["rs"]
               + ATTR_CAPEX * CAPEX_INT * last["rev"]) * tg
    oe37 = np37 - reinv37
    return rows, oe37


def value(s, r, const_g=None):
    rows, oe37 = build(s, const_g)
    pv = 0.0
    for row in rows:
        y = row["year"]
        if y == 2026:
            h2 = row["oe"] - H1_2026_FCF_ATTR        # 全年模型所有者收益扣除上半年已实现部分
            pv += h2 / (1 + r) ** 0.25
        else:
            pv += row["oe"] / (1 + r) ** (y - 2026)   # 年中折现（以 2026-06-30 为 0 点）
    tv = oe37 / (r - s["tg"])
    pv_tv = tv / (1 + r) ** (2036 - 2026)
    equity_0630 = pv + pv_tv + NET_CASH_ADJ + NON_OPERATING
    equity_now = equity_0630 * (1 + r) ** VAL_DATE_OFFSET
    return dict(v=equity_now / SHARES, pv_oe=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv),
                equity=equity_now, rows=rows, oe37=oe37)


def weighted(r):
    return sum(SCENARIOS[k]["p"] * value(SCENARIOS[k], r)["v"] for k in SCENARIOS)


def bisect(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def implied_irr():
    s = SCENARIOS["base"]
    return bisect(lambda r: value(s, r)["v"] - PRICE, s["tg"] + 0.005, 0.30)


def reverse_dcf():
    """以基准 2027E 所有者收益为起点，求现价隐含的 2027–2036 年所有者收益年增速（终值 2.5%，9% 折现）。"""
    s = SCENARIOS["base"]
    rows, _ = build(s)
    oe27 = [x for x in rows if x["year"] == 2027][0]["oe"]
    h2 = rows[0]["oe"] - H1_2026_FCF_ATTR
    target = PRICE * SHARES / (1 + COE) ** VAL_DATE_OFFSET - NET_CASH_ADJ - NON_OPERATING - h2 / (1 + COE) ** 0.25

    def pv_g(g):
        pv, oe = 0.0, oe27
        for t in range(1, 11):          # 2027…2036
            if t > 1:
                oe *= (1 + g)
            pv += oe / (1 + COE) ** t
        tv = oe * (1 + 0.025) / (COE - 0.025)
        return pv + tv / (1 + COE) ** 10 - target

    g10 = bisect(pv_g, -0.5, 1.0)
    g_perp = COE - oe27 / (target * (1 + COE) ** 1)   # 2027E 所有者收益直接永续
    # 营收口径：基准利润率、子公司与再投资不变，求本部营收 2027–2036 年的常数增速
    g_rev = bisect(lambda g: value(s, COE, const_g=g)["v"] - PRICE, 0.0, 0.6)
    rows_g, _ = build(s, const_g=g_rev)
    np36 = rows_g[-1]["np_op"]
    rp36 = rows_g[-1]["rp"]
    return oe27, g10, g_perp, target, g_rev, rp36, np36


def sotp_subsidiaries():
    """子公司按 2026-04 关联交易定价（以注册资本 1 元/元或评估价）× 交割后持股，汉正按 2025 年增资价。"""
    marks = {
        "华秦智造": (2.40, 0.6175),    # 6.25% 作价 1,500 万 → 100% 2.4 亿；净资产 1.886 亿
        "华秦光声": (1.00, 0.50),      # 5% 作价 500 万 → 1.0 亿；净资产 0.073 亿
        "上海瑞华晟": (6.00, 0.46),    # 5.5% 作价 3,300 万 → 6.0 亿；净资产 3.169 亿
        "安徽汉正": (2.4497 / 0.475728, 0.475728),  # 2025 年 2.45 亿增资取得 47.57%
    }
    return {k: v[0] * v[1] for k, v in marks.items()}


def main():
    print("== 华秦科技 688281 独立估值（价格日 2026-10-21，现价 %.2f 元，总股本 %.4f 亿股）==" % (PRICE, SHARES))
    print("现金类 %.3f（货币资金 %.3f＋结构性存款 %.3f）；受限 %.3f；有息负债 %.3f；已宣派股利 %.3f；"
          "股权转让款 +%.3f；经营备付 %.2f" % (CASH_LIKE, CASH, STRUCT_DEPOSIT, RESTRICTED, DEBT,
                                         DECLARED_DIV, TRANSFER_PROCEEDS, OP_RESERVE))
    print("经调整净现金 %.3f 亿（%.2f 元/股）；租赁负债 %.3f 亿只列示；非经营资产 %.3f 亿" %
          (NET_CASH_ADJ, NET_CASH_ADJ / SHARES, LEASE, NON_OPERATING))
    print()
    res = {}
    for k, s in SCENARIOS.items():
        v = value(s, COE)
        res[k] = v
        rows = v["rows"]
        print("-- %s（概率 %.2f）V = %.2f 元/股；所有者收益现值 %.2f、终值现值 %.2f（终值占经营价值 %.0f%%）" %
              (k, s["p"], v["v"], v["pv_oe"], v["pv_tv"], 100 * v["tv_share"]))
        print("   年份  本部营收  子公司营收  合并营收  本部核心税后  子公司归母  归母经营净利  归母再投资  所有者收益")
        for x in rows[:6]:
            print("   %d  %7.2f  %8.2f  %8.2f  %10.2f  %9.2f  %10.2f  %9.2f  %9.2f" %
                  (x["year"], x["rp"], x["rs"], x["rev"], x["core"], x["sub"], x["np_op"], x["reinv"], x["oe"]))
        x = rows[-1]
        print("   %d  %7.2f  %8.2f  %8.2f  %10.2f  %9.2f  %10.2f  %9.2f  %9.2f" %
              (x["year"], x["rp"], x["rs"], x["rev"], x["core"], x["sub"], x["np_op"], x["reinv"], x["oe"]))
        print("   2037 终值所有者收益 %.2f，终值增长 %.1f%%" % (v["oe37"], 100 * s["tg"]))
        np26 = rows[0]["np_op"] + NET_INT_AFTER_TAX
        print("   2026 正常化归母净利（含税后净利息 %.2f，常态化股份支付）= %.2f 亿" % (NET_INT_AFTER_TAX, np26))
        oe_growth = [(rows[i]["oe"] / rows[i - 1]["oe"] - 1) if rows[i - 1]["oe"] > 0 else float("nan")
                     for i in range(2, 7)]
        reinv_rate = sum(x["reinv"] for x in rows[1:6]) / sum(x["np_op"] for x in rows[1:6])
        print("   2028–2031 所有者收益同比：%s；2027–2031 再投资率 %.0f%%" %
              (", ".join("%.1f%%" % (100 * g) for g in oe_growth[:4]), 100 * reinv_rate))
        # 增量回报：2026→2031 归母经营净利增量 ÷ 2027–2031 累计归母再投资
        inc_ret = (rows[5]["np_op"] - rows[0]["np_op"]) / sum(x["reinv"] for x in rows[1:6])
        print("   增量回报（2026→2031 归母经营净利增量 ÷ 2027–2031 累计再投资）%.0f%%" % (100 * inc_ret))
        print()
    vw = weighted(COE)
    print("加权 V = %.2f 元/股；P/V = %.3f" % (vw, PRICE / vw))
    for r in (0.08, 0.10):
        print("股权成本 %.0f%%：bear %.2f / base %.2f / bull %.2f；加权 V = %.2f；P/V = %.3f" %
              (100 * r, value(SCENARIOS["bear"], r)["v"], value(SCENARIOS["base"], r)["v"],
               value(SCENARIOS["bull"], r)["v"], weighted(r), PRICE / weighted(r)))
    irr = implied_irr()
    print("现价隐含回报（基准情景所有者收益流＋终值＋净现金，使现值＝现价的折现率）= %.2f%%" % (100 * irr))
    oe27, g10, g_perp, target, g_rev, rp36, np36 = reverse_dcf()
    print("反向 DCF：现价对应经营价值 %.1f 亿；以基准 2027E 所有者收益 %.2f 亿为起点，隐含 2027–2036 年增 %.1f%%（其后 2.5%%）；"
          "若直接永续，隐含永续增速 %.1f%%" % (target, oe27, 100 * g10, 100 * g_perp))
    print("反向 DCF（营收口径）：基准利润率与子公司路径不变，现价隐含本部营收 2027–2036 年均增 %.1f%%，"
          "2036 年本部营收 %.1f 亿、归母经营净利 %.1f 亿" % (100 * g_rev, rp36, np36))
    # 营运资金占用敏感性
    global WC_RATE_P
    keep = WC_RATE_P
    for w in (0.40, 0.70):
        WC_RATE_P = w
        print("敏感性：本部增量营运资金率 %.2f（原 0.55）→ 加权 V = %.2f（其中基准情景 %.2f）" %
              (w, weighted(COE), value(SCENARIOS["base"], COE)["v"]))
    WC_RATE_P = keep
    print()
    # 分档价格（V 不变）
    print("V 不变时各档价格：≤0.75 → ≤%.2f 元；0.75–0.90 → %.2f–%.2f 元；0.90–1.10 → %.2f–%.2f 元；>1.10 → >%.2f 元" %
          (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    # 交叉验证
    print()
    print("== 交叉验证 ==")
    mcap = PRICE * SHARES
    print("市值 %.1f 亿；股息率（过去 12 个月 0.31 元）%.2f%%；无回购" % (mcap, 100 * 0.31 / PRICE))
    ev = mcap - NET_CASH_ADJ - NON_OPERATING + 2.1596
    ebit_ttm = 2.245 - 1.094 + 1.349   # 合并：营业利润−投资收益−公允价值变动＋财务费用−其他收益，2025 全年−2025H1＋2026H1
    print("EV（市值−经调整净现金−非经营资产＋少数股东权益 2.16）%.1f 亿；TTM 经营 EBIT（剔除投资收益与其他收益）%.2f 亿；EV/EBIT %.0f×" %
          (ev, ebit_ttm, ev / ebit_ttm))
    np_base26 = res["base"]["rows"][0]["np_op"] + NET_INT_AFTER_TAX
    print("PE：TTM 归母 3.33 亿 → %.1f×；基准 2026 正常化 %.2f 亿 → %.1f×；历史年末 PE 43.8–79.8×、PB 3.96–6.99×（2022–2025）" %
          (mcap / 3.33, np_base26, mcap / np_base26))
    sub = sotp_subsidiaries()
    pv_sub = sum(x["sub"] / (1 + COE) ** (x["year"] - 2026) for x in res["base"]["rows"][1:])
    print("子公司按关联交易作价×持股合计 %.2f 亿（%s）；基准情景子公司归母净利（2027–2036，未扣再投资、未计终值）现值 %.2f 亿" %
          (sum(sub.values()), "、".join("%s %.2f" % (k, v) for k, v in sub.items()), pv_sub))
    # 情景触发后的 V（证伪条件用）
    print()
    print("== 证伪触发后的 V（重新加权或替换情景）==")
    vb, vbase, vu = (res[k]["v"] for k in ("bear", "base", "bull"))
    print("营收不达激励触发值（权重 0.55/0.40/0.05）：%.2f" % (0.55 * vb + 0.40 * vbase + 0.05 * vu))
    print("本部毛利率跌破 50%%（按熊市情景）：%.2f" % vb)
    s_alt = dict(SCENARIOS["base"]); s_alt["subs"] = SCENARIOS["bear"]["subs"]
    v_alt = value(s_alt, COE)["v"]
    print("子公司亏损不收窄（基准本部＋熊市子公司，重新加权 0.25/0.50/0.25）：%.2f" %
          (0.25 * vb + 0.50 * v_alt + 0.25 * vu))
    print("框架协议执行率低于 60%%（权重 0.45/0.45/0.10）：%.2f" % (0.45 * vb + 0.45 * vbase + 0.10 * vu))
    print("上行：2026 本部营收≥13.0 亿且核心 EBIT 率≥40%%（权重 0.10/0.40/0.50）：%.2f" %
          (0.10 * vb + 0.40 * vbase + 0.50 * vu))
    # 增长路径（基准，json growth_path 用）
    rows = res["base"]["rows"]
    g = [rows[i]["np_op"] / rows[i - 1]["np_op"] - 1 for i in range(1, 6)]
    reinv_rate = sum(x["reinv"] for x in rows[1:6]) / sum(x["np_op"] for x in rows[1:6])
    inc_ret = (rows[5]["np_op"] - rows[0]["np_op"]) / sum(x["reinv"] for x in rows[1:6])
    print()
    print("基准增长路径（归母经营净利，不含净利息）2027–2031：%s；再投资率 %.2f；增量回报 %.2f；"
          "所有者收益 2026–2031：%s" % (", ".join("%.3f" % x for x in g), reinv_rate, inc_ret,
                                    ", ".join("%.2f" % x["oe"] for x in rows[:6])))


if __name__ == "__main__":
    main()
