#!/usr/bin/env python3
"""爱美客（300896）独立估值：所有者收益 DCF（归母口径）+ 经调整净现金 + 非经营资产 − 或有负债。

金额单位：亿元；每股：元。价格日 2026-10-19，现价 95.30 元。
最新定期报告：2026 年中报（2026-06-30）；三季报预约 2026-10-29。
运行：python3 valuation.py
"""

PRICE = 95.30
SHARES_TOTAL = 3.02592061      # 亿股，含回购专户 1,165,874 股（2026H1_report 第 37、44 页）
TREASURY = 0.01165874          # 回购专户股份，拟全部过户给 2026 年员工持股计划，不注销
ESOP_PRICE = 48.29             # 受让价 49.29 元（incentive_20260821_217471 第 4 页）按 1.00 元派息调整的推算值
COE = 0.09
YEARS = [2027, 2028, 2029, 2030, 2031]
T_H2_2026 = 0.20               # 2026H2 所有者收益按 2026-12-31 计，距价格日约 0.2 年
T_FIRST = 0.70                 # 2027 年现金流按年中计，距价格日 0.70 年
TAX = 0.145                    # 有效税率（2025 年 13.9%，2026H1 13.9%，取略高值）
MINORITY = 0.025               # 少数股东占税后经营利润的比例（爱美客国际 30% 外方股东等，2026H1 实际 1.1%）

# ---------- 资产负债表（2026-06-30，2026H1_report 第 50～52、116、130～136、151～153 页）----------
CASH = 19.6364                 # 货币资金（其中境外 1.52）
STRUCT_DEP = 19.2130           # 交易性金融资产中的结构性存款
STOCKS = 0.2251                # 交易性金融资产中的股票
CD_CURRENT = 2.6736            # 一年内到期的债权投资（大额存单）；保函保证金 0.1729 为受限资金，未计入
CD_NONCURRENT = 6.2571         # 债权投资（大额存单）
CASH_LIKE = CASH + STRUCT_DEP + STOCKS + CD_CURRENT + CD_NONCURRENT

DIV_PAID_SEP = 3.0143          # 2026 年中期分红，2026-09-03 除息（dividend_20260826_411109 第 1 页）
REGEN_PAYABLE = 2.1789         # 一年内到期的长期应付款：REGEN 第二阶段股权对价（美元），由持股 70% 的爱美客国际承担
REGEN_PAYABLE_PARENT = REGEN_PAYABLE * 0.70
LEASES = 0.2266 + 0.0726       # 一年内到期的租赁负债 + 租赁负债
OP_RESERVE = 4.5               # 经营备付：约 3 个月经营现金流出（2026H1 经营现金流出 9.12 亿）
ESOP_CASH = TREASURY * ESOP_PRICE   # 员工持股计划受让回购股份的缴款


def net_cash(with_esop=True):
    v = CASH_LIKE - DIV_PAID_SEP - REGEN_PAYABLE_PARENT - LEASES - OP_RESERVE
    return v + (ESOP_CASH if with_esop else 0.0)


# ---------- 2026H1 实际 ----------
H1_REV = 12.1574
H1_CORE_EBIT = 6.3770          # 营收 − 营业成本 − 税金及附加 − 销售 − 管理 − 研发（不含利息、投资收益、公允价值变动、补助）
GM = {"legacy": 0.94, "fd": 0.875, "botox": 0.55, "new": 0.60}   # 分产品毛利率假设

SCEN = {
    "bear": dict(
        p=0.25,
        h2=dict(legacy=8.25, fd=2.05, botox=0.45, new=0.15, ebit_margin=0.37),
        legacy_g=[-0.14, -0.09, -0.06, -0.04, -0.03],
        fd_g=[0.00, 0.03, 0.03, 0.03, 0.03],
        botox=[1.2, 1.6, 1.8, 2.0, 2.1],
        new=[0.4, 0.5, 0.6, 0.7, 0.8],
        gm_legacy=0.935,
        opex=[0.45, 0.45, 0.45, 0.45, 0.45],
        capex=[2.2, 1.8, 1.3, 1.2, 1.2], h2_capex=1.2,
        g_term=0.010, ronic=0.12,
        nonop=3.4, arbitration=4.0, cash_haircut=0.15,
    ),
    "base": dict(
        p=0.50,
        h2=dict(legacy=8.70, fd=2.25, botox=0.70, new=0.15, ebit_margin=0.415),
        legacy_g=[-0.08, -0.05, -0.03, -0.02, -0.01],
        fd_g=[0.10, 0.10, 0.08, 0.06, 0.05],
        botox=[2.0, 2.8, 3.4, 3.8, 4.1],
        new=[0.6, 0.9, 1.2, 1.4, 1.6],
        gm_legacy=0.94,
        opex=[0.435, 0.425, 0.42, 0.415, 0.415],
        capex=[2.2, 1.8, 1.3, 1.3, 1.3], h2_capex=1.2,
        g_term=0.025, ronic=0.20,
        nonop=5.2, arbitration=1.5, cash_haircut=0.0,
    ),
    "bull": dict(
        p=0.25,
        h2=dict(legacy=9.15, fd=2.45, botox=1.00, new=0.20, ebit_margin=0.44),
        legacy_g=[-0.03, 0.00, 0.01, 0.01, 0.01],
        fd_g=[0.20, 0.16, 0.13, 0.10, 0.08],
        botox=[2.5, 3.8, 4.8, 5.5, 6.0],
        new=[1.0, 1.6, 2.2, 2.7, 3.1],
        gm_legacy=0.94,
        opex=[0.41, 0.39, 0.38, 0.37, 0.37],
        capex=[2.4, 2.0, 1.6, 1.5, 1.5], h2_capex=1.2,
        g_term=0.025, ronic=0.25,
        nonop=7.6, arbitration=0.5, cash_haircut=0.0,
    ),
}

H1_PRODUCTS = dict(legacy=5.9137 + 3.7941 + 0.3600, fd=2.0896, botox=0.0, new=0.0)  # 溶液+凝胶+其他、冻干粉


def da(year):
    return {2026: 0.70, 2027: 0.80, 2028: 0.90, 2029: 1.00, 2030: 1.05, 2031: 1.05}[year]   # 不含使用权资产折旧


def build(s):
    """返回逐年经营数据：营收、分产品、EBIT、归母税后经营利润、所有者收益。"""
    h2 = s["h2"]
    fy = {k: H1_PRODUCTS[k] + h2[k] for k in ("legacy", "fd", "botox", "new")}
    rev26 = sum(fy.values())
    h2_rev = sum(h2[k] for k in ("legacy", "fd", "botox", "new"))
    ebit26 = H1_CORE_EBIT + h2_rev * h2["ebit_margin"]
    nopat26 = ebit26 * (1 - TAX) * (1 - MINORITY)
    h2_nopat = h2_rev * h2["ebit_margin"] * (1 - TAX) * (1 - MINORITY)
    h2_oe = h2_nopat - (s["h2_capex"] - da(2026) / 2) - 0.03 * (rev26 - 24.526) / 2
    rows = [dict(year=2026, rev=rev26, ebit=ebit26, margin=ebit26 / rev26, nopat=nopat26,
                 oe=nopat26 - (2.0 - da(2026)) - 0.03 * (rev26 - 24.526), **fy)]
    legacy, fd = fy["legacy"], fy["fd"]
    prev_rev = rev26
    for i, y in enumerate(YEARS):
        legacy *= 1 + s["legacy_g"][i]
        fd *= 1 + s["fd_g"][i]
        bt, nw = s["botox"][i], s["new"][i]
        rev = legacy + fd + bt + nw
        gp = legacy * s["gm_legacy"] + fd * GM["fd"] + bt * GM["botox"] + nw * GM["new"]
        ebit = gp - rev * s["opex"][i]
        nopat = ebit * (1 - TAX) * (1 - MINORITY)
        reinv = (s["capex"][i] - da(y)) + 0.03 * (rev - prev_rev)
        rows.append(dict(year=y, rev=rev, legacy=legacy, fd=fd, botox=bt, new=nw, gm=gp / rev, ebit=ebit,
                         margin=ebit / rev, nopat=nopat, reinv=reinv, oe=nopat - reinv))
        prev_rev = rev
    return rows, h2_oe


def equity_value(s, r, with_esop=True, haircut_override=None):
    rows, h2_oe = build(s)
    pv = h2_oe / (1 + r) ** T_H2_2026
    for i, row in enumerate(rows[1:]):
        pv += row["oe"] / (1 + r) ** (T_FIRST + i)
    last = rows[-1]
    g, ronic = s["g_term"], s["ronic"]
    tv = last["nopat"] * (1 + g) * (1 - g / ronic) / (r - g)
    pv_tv = tv / (1 + r) ** (T_FIRST + len(YEARS) - 1 + 0.5)
    hc = s["cash_haircut"] if haircut_override is None else haircut_override
    nc = net_cash(with_esop) * (1 - hc)
    eq = pv + pv_tv + nc + s["nonop"] - s["arbitration"]
    return dict(op=pv + pv_tv, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv), net_cash=nc,
                equity=eq, rows=rows, h2_oe=h2_oe)


def per_share(s, r, shares=SHARES_TOTAL, with_esop=True):
    return equity_value(s, r, with_esop)["equity"] / shares


def weighted(r, shares=SHARES_TOTAL, with_esop=True):
    return sum(SCEN[k]["p"] * per_share(SCEN[k], r, shares, with_esop) for k in SCEN)


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
    s = SCEN["base"]
    return solve(lambda r: per_share(s, r), 0.03, 0.30, PRICE)


def reverse_dcf():
    """现价隐含：(1) 以基准 2026 年所有者收益为起点，2027-2036 年不变增速 g10，之后永续 2.5%（终值按所有者收益）；
    (2) 2027 年基准所有者收益起永续增速（Gordon）。均按 9%，经营价值目标 = 市值 − 经调整净现金 − 非经营资产 + 仲裁或有。"""
    s = SCEN["base"]
    rows, h2_oe = build(s)
    oe0 = rows[0]["oe"]
    target_op = PRICE * SHARES_TOTAL - net_cash() - s["nonop"] + s["arbitration"]
    pv_h2 = h2_oe / (1 + COE) ** T_H2_2026

    def op_value(g10, r=COE, gt=0.025):
        pv, oe = pv_h2, oe0
        for t in range(10):
            oe *= 1 + g10
            pv += oe / (1 + r) ** (T_FIRST + t)
        return pv + oe * (1 + gt) / (r - gt) / (1 + r) ** (T_FIRST + 9.5)

    g10 = solve(op_value, -0.05, 0.30, target_op)
    oe27 = rows[1]["oe"]
    g_perp = solve(lambda g: pv_h2 + oe27 / (COE - g) / (1 + COE) ** (T_FIRST - 0.5), -0.05, 0.0899, target_op)
    return g10, g_perp, target_op, oe0


def fmt_rows(rows):
    out = []
    for r_ in rows:
        out.append("  %d 营收 %6.2f（存量 %5.2f 冻干粉 %4.2f 肉毒 %4.2f 新品 %4.2f）EBIT %5.2f（%4.1f%%）归母经营利润 %5.2f 所有者收益 %5.2f"
                   % (r_["year"], r_["rev"], r_["legacy"], r_["fd"], r_["botox"], r_["new"], r_["ebit"],
                      100 * r_["margin"], r_["nopat"], r_["oe"]))
    return "\n".join(out)


def normalized_np_2026(key):
    """2026 年正常化归母净利：经营利润 + 税后净利息（现金类约 46 亿 × 1.0% × 85%）− 联营亏损 0.10 − 员工持股费用 0.09。"""
    rows, _ = build(SCEN[key])
    return rows[0]["nopat"] + 46.0 * 0.010 * 0.85 - 0.10 - 0.09


def falsifiers():
    """证伪条件触发后的独立 V（9% 股权成本、重新加权）。"""
    out = {}
    # F1：2026Q3 营收 < 5.4 亿或扣非归母 < 2.0 亿（2026-10-29），或 2026 年营收 < 23.0 亿（2027-04-30）：熊 45%/基 45%/牛 10%
    p = {"bear": 0.45, "base": 0.45, "bull": 0.10}
    out["F1"] = sum(p[k] * per_share(SCEN[k], COE) for k in SCEN)
    # F2：仲裁裁决 REGEN 赔偿 ≥ 8 亿（归母按 70% 承担 5.6 亿）：各情景或有负债取 max(原值, 5.6)
    v = 0.0
    for k in SCEN:
        s = dict(SCEN[k]); s["arbitration"] = max(s["arbitration"], 8.0 * 0.70)
        v += SCEN[k]["p"] * per_share(s, COE)
    out["F2"] = v
    # F3：2027 年存量产品（溶液+凝胶+其他）营收同比降幅 ≥ 10%（2028-04-30 年报）：熊 50%/基 40%/牛 10%
    p = {"bear": 0.50, "base": 0.40, "bull": 0.10}
    out["F3"] = sum(p[k] * per_share(SCEN[k], COE) for k in SCEN)
    # F4（向上）：2027 年营收 ≥ 27.25 亿（员工持股计划触发值隐含）且核心 EBIT 率 ≥ 47%（2028-04-30）：熊 10%/基 40%/牛 50%
    p = {"bear": 0.10, "base": 0.40, "bull": 0.50}
    out["F4"] = sum(p[k] * per_share(SCEN[k], COE) for k in SCEN)
    # F5：2027-10-31 前宣布对价 ≥ 15 亿且标的 PE > 30 倍的并购：各情景超额现金折价取 max(原值, 30%)
    v = 0.0
    for k in SCEN:
        s = dict(SCEN[k]); s["cash_haircut"] = max(s["cash_haircut"], 0.30)
        v += SCEN[k]["p"] * per_share(s, COE)
    out["F5"] = v
    return out


def main():
    print("爱美客 300896 独立估值（价格日 2026-10-19，现价 %.2f 元，总股本 %.4f 亿股含回购专户）" % (PRICE, SHARES_TOTAL))
    print("现金类 %.2f；经调整净现金 %.2f（扣已派中期股利 %.2f、REGEN 第二阶段对价归母 70%% %.2f、租赁 %.2f、经营备付 %.2f，加员工持股缴款 %.2f）"
          % (CASH_LIKE, net_cash(), DIV_PAID_SEP, REGEN_PAYABLE_PARENT, LEASES, OP_RESERVE, ESOP_CASH))
    print()
    vs = {}
    for k in ("bear", "base", "bull"):
        s = SCEN[k]
        ev = equity_value(s, COE)
        vs[k] = ev["equity"] / SHARES_TOTAL
        print("[%s] p=%.2f  V=%.2f 元/股  经营价值 %.1f（显性 %.1f + 终值 %.1f，终值占比 %.0f%%）净现金 %.1f 非经营资产 %.1f 仲裁或有 -%.1f 2026H2 所有者收益 %.2f"
              % (k, s["p"], vs[k], ev["op"], ev["pv_explicit"], ev["pv_tv"], 100 * ev["tv_share"], ev["net_cash"],
                 s["nonop"], s["arbitration"], ev["h2_oe"]))
        print(fmt_rows(ev["rows"]))
        print("  终值增长 %.1f%%，RONIC %.0f%%，终值再投资率 %.1f%%" % (100 * s["g_term"], 100 * s["ronic"], 100 * s["g_term"] / s["ronic"]))
    vw = weighted(COE)
    pv = PRICE / vw
    tier = "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"
    print()
    print("加权 V = %.2f 元/股；P/V = %.2f（%s）" % (vw, pv, tier))
    print("股权成本 8%%：V = %.2f；10%%：V = %.2f" % (weighted(0.08), weighted(0.10)))
    print("基准情景隐含回报（现价）= %.2f%%" % (100 * implied_irr()))
    g10, gp, target_op, oe0 = reverse_dcf()
    print("反向 DCF：现价对应经营价值 %.1f 亿；以 2026 年所有者收益 %.2f 亿起算，需 2027-2036 年每年增 %.1f%%（其后 2.5%%）；或 2027 年所有者收益起永续增 %.2f%%"
          % (target_op, oe0, 100 * g10, 100 * gp))
    sh_ex = SHARES_TOTAL - TREASURY
    vw_ex = weighted(COE, shares=sh_ex, with_esop=False)
    print("对照：剔除回购专户股份（%.4f 亿股、不计员工持股缴款）加权 V = %.2f，P/V = %.2f" % (sh_ex, vw_ex, PRICE / vw_ex))
    print("V 不变时分档价格：≤%.1f 明显低估；%.1f～%.1f 温和低估；%.1f～%.1f 大致合理；>%.1f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print("2026 正常化归母净利（含净利息，剔一次性）：熊 %.2f 基 %.2f 牛 %.2f 亿元"
          % tuple(normalized_np_2026(k) for k in ("bear", "base", "bull")))
    print("证伪触发后 V：" + "；".join("%s %.2f" % (k, v) for k, v in falsifiers().items()))
    base_rows, _ = build(SCEN["base"])
    oe = [r_["oe"] for r_ in base_rows]
    print("基准所有者收益增速 2027-2031：" + " ".join("%.1f%%" % (100 * (oe[i + 1] / oe[i] - 1)) for i in range(5)))
    reinv = sum(r_["reinv"] for r_ in base_rows[1:])
    dn = base_rows[-1]["nopat"] - base_rows[0]["nopat"]
    print("基准 2027-2031 累计再投资 %.2f 亿，占累计归母经营利润 %.1f%%；增量回报（2031 较 2026 经营利润增量 / 累计再投资）%.0f%%"
          % (reinv, 100 * reinv / sum(r_["nopat"] for r_ in base_rows[1:]), 100 * dn / reinv))


if __name__ == "__main__":
    main()
