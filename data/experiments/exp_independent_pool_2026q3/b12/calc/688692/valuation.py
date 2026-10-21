#!/usr/bin/env python3
"""达梦数据（688692）独立估值：所有者收益 DCF（三情景）、敏感性、隐含回报与反向 DCF。

金额单位亿元，每股价值单位元。输入全部写在脚本内，来源见同批 companies/688692_达梦数据.md。
运行：python3 valuation.py
"""

# ---------------------------------------------------------------- 快照
PRICE = 174.82            # 2026-10-20 收盘，元
SHARES = 1.1324           # 亿股，总股本（无回购专户、无拟注销股份）
COE = 0.09
T_STUB = 72 / 365         # 2026-10-20 → 2026-12-31，年末折现
PROB = {"bear": 0.30, "base": 0.45, "bull": 0.25}

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 122、37 页；第 67 页关联存款）
CASH = 30.1464            # 货币资金（含定期存单 23.305）
RESTRICTED = 0.0235       # 保函保证金
RELATED_DEPOSIT = 1.0091  # 中国电子财务有限责任公司存款（关联方），单独列示
RELATED_HAIRCUT = 0.50    # 关联方存款按 50% 计入可用现金
LEASE_DEBT = 0.1067 + 0.3100   # 一年内到期的非流动负债（租赁）+ 租赁负债；无银行借款
DIV_PAID_AFTER_BS = 0.79268    # 2026 中期每 10 股派 7 元，9-28 除息，已付出
OPERATING_RESERVE = 3.0        # 经营备付：约 3 个月现金性经营支出（上半年经营现金流季节性为零）
NON_OPERATING = 0.1000         # 合肥中湾达梦股权投资基金（长期股权投资，账面）

NET_CASH_ADJ = (CASH - RESTRICTED - RELATED_DEPOSIT * RELATED_HAIRCUT - LEASE_DEBT
                - DIV_PAID_AFTER_BS - OPERATING_RESERVE)

# ---------------------------------------------------------------- 2025 年与 2026 上半年实际（亿元）
REV_2025 = 13.0585
REV_H1_2025 = 5.2308
SBC_2025 = 0.1377         # 2025 年股份支付（计入资本公积累计 1,376.54 万元，2025_annual_report）
OPEX_EXSBC_H2_2025 = (3.9957 + 1.2414 + 2.5345) - (1.7086 + 0.4789 + 1.1175) - SBC_2025
NWC_YE2025 = 0.677        # 经营性营运资本（应收、存货、预付等减应付、合同负债、应付薪酬、应交税费等）
NWC_H1_2026 = 4.329       # 2026-06-30 同口径：季节性占用高点

H1 = dict(rev=7.1281, pretax=2.3493, tax=0.1901, minority=-0.0509, parent=2.2102,
          sbc=0.7115,            # 股份支付费用合计（2026H1_report 第 190 页）
          grants=0.1326,         # 非经常性政府补助（第 11 页）
          other_nonrec=0.0027,   # 资产处置与营业外净额
          interest=0.1907,       # 财务费用净收益（利息收入 0.1968 减手续费等）
          da=0.232, capex=1.170)

# 2026 年报口径的 H2 假设与 2027-2031 路径
SCEN = {
    "bear": dict(
        g_h2=0.05, gm_h2=0.950, opex_g_h2=0.24, sbc_pct=0.06, vat_pct=0.066, credit_pct=0.022,
        growth=[0.06, -0.08, 0.02, 0.03, 0.03], margin=[0.29, 0.25, 0.255, 0.26, 0.26],
        tax=[0.09, 0.09, 0.13, 0.13, 0.13], g_term=0.020, ronic=0.20, net_capex=0.08,
        nwc_extra=0.40,
        text="2026H2 营收 +5%，2027 年 +6%，2028 年信创期限后回落 -8%，之后 2%～3%；"
             "股份支付 6%，营业利润率（扣股份支付、不含利息与补助）29%→25%→26%；2029 年起税率 13%；终值增长 2%"),
    "base": dict(
        g_h2=0.15, gm_h2=0.953, opex_g_h2=0.22, sbc_pct=0.05, vat_pct=0.066, credit_pct=0.017,
        growth=[0.17, 0.12, 0.09, 0.07, 0.05], margin=[0.350, 0.355, 0.360, 0.365, 0.370],
        tax=[0.09] * 5, g_term=0.025, ronic=0.30, net_capex=0.10, nwc_extra=0.0,
        text="2026H2 营收 +15%（全年约 +23%），2027-2031 年 +17%/+12%/+9%/+7%/+5%；"
             "股份支付按收入 5% 常态化，营业利润率 35%→37%；税率 9%；终值增长 2.5%"),
    "bull": dict(
        g_h2=0.25, gm_h2=0.955, opex_g_h2=0.22, sbc_pct=0.04, vat_pct=0.066, credit_pct=0.015,
        growth=[0.25, 0.20, 0.15, 0.12, 0.10], margin=[0.395, 0.405, 0.415, 0.420, 0.425],
        tax=[0.09] * 5, g_term=0.025, ronic=0.30, net_capex=0.15, nwc_extra=0.0,
        text="2026H2 营收 +25%，2027-2031 年 +25%/+20%/+15%/+12%/+10%（洗牌中份额升至约两成、一体机放量）；"
             "股份支付 4%，营业利润率 39.5%→42.5%；终值增长 2.5%"),
}

NWC_RATIO = 0.06          # 增量收入的营运资本占用（2024→2025 年末口径约 6%）
H2_TAX = 0.085
H2_MINORITY = -0.05
H2_INTEREST = 0.15        # 下半年利息净收益（2025 年下半年仅 0.08，上半年 0.19）
H2_DA, H2_CAPEX = 0.24, 0.30
YEARS = [2027, 2028, 2029, 2030, 2031]


def year_2026(s):
    """2026 年：上半年实际 + 下半年假设；返回正常化与报表口径的利润、营业利润率与下半年自由现金流。"""
    rev_h2 = (REV_2025 - REV_H1_2025) * (1 + s["g_h2"])
    rev = H1["rev"] + rev_h2
    # 上半年正常化：加回实际股份支付、扣常态化股份支付，剔除补助与其他非经常
    h1_pretax_n = H1["pretax"] + H1["sbc"] - s["sbc_pct"] * H1["rev"] - H1["grants"] - H1["other_nonrec"]
    h1_parent_n = h1_pretax_n * (1 - H1["tax"] / H1["pretax"]) - H1["minority"]
    # 下半年：毛利 - 税金及附加 - 期间费用（不含股份支付）+ 即征即退 - 信用减值 + 利息 - 常态化股份支付
    vat_h2 = s["vat_pct"] * rev - 0.3609
    credit_h2 = s["credit_pct"] * rev - 0.1249
    op_exsbc_h2 = (rev_h2 * s["gm_h2"] - 0.016 * rev_h2 - OPEX_EXSBC_H2_2025 * (1 + s["opex_g_h2"])
                   + vat_h2 + 0.005 - credit_h2)
    h2_pretax_n = op_exsbc_h2 + H2_INTEREST - s["sbc_pct"] * rev_h2
    h2_parent_n = h2_pretax_n * (1 - H2_TAX) - H2_MINORITY
    parent_n = h1_parent_n + h2_parent_n
    # 报表口径（实际股份支付约 1.43、补助约 0.25）：仅作参考
    sbc_actual = H1["sbc"] + 0.72
    gaap_parent = (H1["parent"] + (op_exsbc_h2 + H2_INTEREST - 0.72 + 0.12) * (1 - H2_TAX) - H2_MINORITY)
    # 加回实际股份支付后的扣非归母（证伪门槛用，与公司「扣除股份支付影响后」口径接近）
    kf_plus_sbc = (gaap_parent - (H1["grants"] + H1["other_nonrec"]) * (1 - 0.081) - 0.12 * (1 - H2_TAX)
                   + sbc_actual * (1 - H2_TAX))
    # 公司披露口径「扣除股份支付影响后的净利润」：合并净利润 + 股份支付×0.988（上半年 2.86 亿的口径）
    company_metric = gaap_parent + H1["minority"] + H2_MINORITY + 0.988 * sbc_actual
    # 经营口径利润率（扣常态化股份支付，不含利息与补助）
    interest_fy = H1["interest"] + H2_INTEREST
    op_margin = (h1_pretax_n + h2_pretax_n - interest_fy) / rev
    # 下半年经济自由现金流：正常化归母 + 折旧 - 资本开支 + 季节性营运资本回落
    nwc_ye = NWC_YE2025 * rev / REV_2025 + s["nwc_extra"]
    stub = h2_parent_n + H2_DA - H2_CAPEX + (NWC_H1_2026 - nwc_ye)
    return dict(rev=rev, rev_h2=rev_h2, parent_n=parent_n, gaap_parent=gaap_parent, op_margin=op_margin,
                stub=stub, nwc_ye=nwc_ye, sbc_actual=sbc_actual, h1_parent_n=h1_parent_n,
                h2_parent_n=h2_parent_n, kf_plus_sbc=kf_plus_sbc, company_metric=company_metric,
                oe=rev * op_margin * (1 - 0.09) - s["net_capex"] - NWC_RATIO * (rev - REV_2025))


def q3_estimate(s):
    """2026Q3 单季（三季报核对用）：2025Q3 实际为营收 3.071、期间费用 1.887、其他收益 0.300、
    信用减值 -0.068、利息 0.049、营业利润 1.302、归母 1.250。"""
    rev = 3.0713 * (1 + s["g_h2"])
    op = (rev * s["gm_h2"] - 0.016 * rev - 1.8874 * (1 + s["opex_g_h2"]) - 0.36   # 实际股份支付约 0.36/季
          + 0.2997 * rev / 3.0713 * 0.95 + 0.07 - s["credit_pct"] * rev)
    return rev, op * (1 - H2_TAX) + 0.025


def flows(s):
    y26 = year_2026(s)
    rev_prev, rows = y26["rev"], []
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s["growth"][i])
        nopat = rev * s["margin"][i] * (1 - s["tax"][i])
        oe = nopat - NWC_RATIO * (rev - rev_prev) - s["net_capex"]
        rows.append(dict(year=y, rev=rev, nopat=nopat, oe=oe))
        rev_prev = rev
    last = rows[-1]
    g = s["g_term"]
    oe_term = last["nopat"] * (1 + g) * (1 - g / s["ronic"])
    return y26, rows, oe_term


def value(s, r=COE):
    y26, rows, oe_term = flows(s)
    g = s["g_term"]
    pv_stub = y26["stub"] / (1 + r) ** T_STUB
    pv_oe = sum(row["oe"] / (1 + r) ** (T_STUB + k + 1) for k, row in enumerate(rows))
    tv = oe_term / (r - g)
    pv_tv = tv / (1 + r) ** (T_STUB + len(rows))
    total = NET_CASH_ADJ + NON_OPERATING + pv_stub + pv_oe + pv_tv
    return dict(total=total, v=total / SHARES, pv_stub=pv_stub, pv_oe=pv_oe, pv_tv=pv_tv, tv=tv,
                tv_share=pv_tv / total, y26=y26, rows=rows, oe_term=oe_term)


def weighted(r=COE):
    return sum(PROB[k] * value(SCEN[k], r)["v"] for k in SCEN)


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr():
    """基准情景所有者收益流（含终值与净现金）使现值等于现价的折现率。"""
    return solve(lambda r: value(SCEN["base"], r)["v"], 0.03, 0.30, PRICE)


def reverse_dcf():
    """以基准 2026 年正常化经营所有者收益为起点：(a) 10 年匀速增长、其后 2.5%；(b) 永续增速。"""
    base = SCEN["base"]
    y26 = year_2026(base)
    oe0 = y26["oe"]   # 2026 年经营所有者收益（不含利息，扣常态股份支付、营运资本与净资本开支）
    cash_like = NET_CASH_ADJ + NON_OPERATING + y26["stub"] / (1 + COE) ** T_STUB
    target = PRICE * SHARES

    def pv10(g10):
        pv, oe = cash_like, oe0
        for k in range(1, 11):
            oe *= 1 + g10
            pv += oe / (1 + COE) ** (T_STUB + k)
        pv += oe * 1.025 * (1 - 0.025 / 0.30) / (COE - 0.025) / (1 + COE) ** (T_STUB + 10)
        return pv

    def pv_perp(g):
        return cash_like + oe0 * (1 + g) / (COE - g) / (1 + COE) ** T_STUB

    return oe0, solve(pv10, -0.10, 0.40, target), solve(pv_perp, -0.05, 0.0899, target)


def main():
    print(f"现价 {PRICE:.2f} 元；总股本 {SHARES:.4f} 亿股；市值 {PRICE * SHARES:.2f} 亿元")
    print(f"经调整净现金（6-30，扣已付中期股利、租赁负债、受限、经营备付、关联存款半数）：{NET_CASH_ADJ:.2f} 亿元；"
          f"其中关联存款 {RELATED_DEPOSIT:.2f}，按 {RELATED_HAIRCUT:.0%} 计入；非经营资产 {NON_OPERATING:.2f}")
    print()
    res = {}
    for k in ("bear", "base", "bull"):
        s = SCEN[k]
        v = value(s)
        res[k] = v
        y = v["y26"]
        print(f"[{k}] p={PROB[k]:.2f}  V = {v['v']:.1f} 元/股  （总值 {v['total']:.1f} 亿元）")
        print(f"   2026：营收 {y['rev']:.2f}；正常化归母 {y['parent_n']:.2f}（上半年 {y['h1_parent_n']:.2f}、"
              f"下半年 {y['h2_parent_n']:.2f}）；报表口径估 {y['gaap_parent']:.2f}；"
              f"经营利润率（扣常态股份支付）{y['op_margin']:.1%}")
        print(f"   下半年经济自由现金流 {y['stub']:.2f}（年末营运资本 {y['nwc_ye']:.2f}）")
        print("   年份  营收   NOPAT  所有者收益  增速")
        prev = y["rev"]
        for row in v["rows"]:
            print(f"   {row['year']}  {row['rev']:6.2f} {row['nopat']:6.2f} {row['oe']:8.2f}   "
                  f"{row['rev'] / prev - 1:+.1%}")
            prev = row["rev"]
        print(f"   终值 {v['tv']:.1f}（现值 {v['pv_tv']:.1f}，占总值 {v['tv_share']:.0%}）；"
              f"显性期现值 {v['pv_oe']:.1f}；下半年现值 {v['pv_stub']:.1f}")
        print()
    vw = weighted()
    print(f"加权 V = {vw:.1f} 元/股；P/V = {PRICE / vw:.2f}")
    for r in (0.08, 0.10):
        vs = {k: value(SCEN[k], r)["v"] for k in SCEN}
        print(f"股权成本 {r:.0%}：熊 {vs['bear']:.1f} / 基准 {vs['base']:.1f} / 牛 {vs['bull']:.1f}；"
              f"加权 {weighted(r):.1f}；P/V {PRICE / weighted(r):.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准现金流）：{irr:.2%}")
    oe0, g10, gp = reverse_dcf()
    print(f"反向 DCF：以 2026 经营所有者收益 {oe0:.2f} 亿为起点，现价隐含 10 年增速 {g10:.1%}（其后 2.5%），"
          f"或永续增速 {gp:.2%}")
    # 情景内的正常化归母 2026（json 用）
    print("2026 正常化归母净利：" + "，".join(f"{k} {res[k]['y26']['parent_n']:.2f}" for k in ("bear", "base", "bull")))
    # 各档价格（V 不变时）
    print(f"分档价格（V 不变）：≤{0.75 * vw:.0f} 明显低估；{0.75 * vw:.0f}～{0.90 * vw:.0f} 温和低估；"
          f"{0.90 * vw:.0f}～{1.10 * vw:.0f} 大致合理；>{1.10 * vw:.0f} 偏贵")
    print("2026 加回股份支付后的扣非归母（估）：" + "，".join(
        f"{k} {res[k]['y26']['kf_plus_sbc']:.2f}" for k in ("bear", "base", "bull")))
    print("2026 公司口径「扣除股份支付影响后的净利润」（估）：" + "，".join(
        f"{k} {res[k]['y26']['company_metric']:.2f}" for k in ("bear", "base", "bull")))
    print("2026Q3 单季（估，营收/归母）：" + "，".join(
        f"{k} {q3_estimate(SCEN[k])[0]:.2f}/{q3_estimate(SCEN[k])[1]:.2f}" for k in ("bear", "base", "bull")))
    # 基准增长路径：所有者收益增速、再投资率与有形增量回报
    b = res["base"]
    oes = [b["y26"]["oe"]] + [row["oe"] for row in b["rows"]]
    print("基准所有者收益增速 2027-2031：" + "，".join(f"{oes[i + 1] / oes[i] - 1:+.1%}" for i in range(5)))
    reinv = sum(row["nopat"] - row["oe"] for row in b["rows"])
    nopat_sum = sum(row["nopat"] for row in b["rows"])
    nopat26 = b["y26"]["rev"] * b["y26"]["op_margin"] * (1 - 0.09)
    print(f"基准再投资率（营运资本+净资本开支）/NOPAT = {reinv / nopat_sum:.1%}；"
          f"有形增量回报 ΔNOPAT/累计再投资 = {(b['rows'][-1]['nopat'] - nopat26) / reinv:.1f} 倍；"
          f"终值 RONIC 取 {SCEN['base']['ronic']:.0%}")
    # 交叉验证
    ev = PRICE * SHARES - (CASH - DIV_PAID_AFTER_BS - LEASE_DEBT)
    ebit_ttm = (5.837 - 2.193 + 2.349) - (0.268 - 0.189 + 0.191)
    ebit26 = b["y26"]["rev"] * b["y26"]["op_margin"]
    print(f"交叉验证：EV {ev:.1f} 亿；EV/EBIT(TTM, 报表) {ev / ebit_ttm:.1f}×；"
          f"EV/EBIT(2026 基准正常化) {ev / ebit26:.1f}×；股息率 {1.7 / PRICE:.2%}；无回购")
    # 其他敏感性与参照数
    vb = {k: res[k]["v"] for k in res}
    print(f"概率 0.25/0.50/0.25 时加权 V = {0.25 * vb['bear'] + 0.5 * vb['base'] + 0.25 * vb['bull']:.1f}")
    grants_pv = 0.25 * (1 - 0.09) / (COE - 0.025) / (1 + COE) ** T_STUB / SHARES
    print(f"非经常补助按每年 0.25 亿常态计入：V 约 +{grants_pv:.1f} 元")
    print(f"关联存款升至 5 亿（超出部分同样折半）：V 约 -{(5 - RELATED_DEPOSIT) * RELATED_HAIRCUT / SHARES:.1f} 元")
    irr_bull = solve(lambda r: value(SCEN["bull"], r)["v"], 0.03, 0.30, PRICE)
    print(f"牛市情景现金流下的隐含回报：{irr_bull:.2%}")
    n2025 = ((5.568 + SBC_2025 - 0.05 * REV_2025 - 0.348 + 0.270 - 0.002) * (1 - 0.417 / 5.568) + 0.016)
    print(f"2025 正常化归母（报表 5.17）：{n2025:.2f}")
    print(f"2027 基准正常化归母（NOPAT + 税后利息约 0.30）：{b['rows'][0]['nopat'] + 0.33 * 0.91:.2f}")
    # 证伪触发后的 V
    trig = falsifier_values()
    for name, val in trig.items():
        print(f"证伪触发 {name}：V = {val:.1f}")


def falsifier_values():
    """证伪条件触发后的独立 V：按触发后的情景权重或情景值重算。"""
    vb = {k: value(SCEN[k])["v"] for k in SCEN}
    out = {}
    # F1：2026Q3 单季营收同比转负（< 3.07 亿）→ 熊 0.5 / 基准 0.4 / 牛 0.1
    out["F1 三季报转负"] = 0.5 * vb["bear"] + 0.4 * vb["base"] + 0.1 * vb["bull"]
    # F2：2026 年营收 < 15.3 亿或公司口径「扣除股份支付影响后的净利润」< 6.0 亿 → 熊 0.6 / 基准 0.4
    out["F2 年报低于熊市线"] = 0.6 * vb["bear"] + 0.4 * vb["base"]
    # F3：2027 年上半年营收同比 < 0（信创需求断档提前）→ 熊情景
    out["F3 2027H1 负增长"] = vb["bear"]
    # F4：管理层案件延伸至公司（单位行贿立案、采购禁入或补助追缴 > 1 亿）→ 熊情景再扣 15%
    out["F4 公司层面处罚"] = vb["bear"] * 0.85
    # F5（向上）：2026 年营收 ≥ 17.0 亿且 2027H1 营收同比 ≥ 25%、加回股份支付后营业利润率 ≥ 42% → 基准 0.5 / 牛 0.5
    out["F5 向上证伪"] = 0.5 * vb["base"] + 0.5 * vb["bull"]
    return out


if __name__ == "__main__":
    main()
