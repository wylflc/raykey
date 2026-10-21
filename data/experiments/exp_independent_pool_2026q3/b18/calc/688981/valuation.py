#!/usr/bin/env python3
"""中芯国际（688981 / 00981）独立估值 —— OI-291 b18 深度版。

口径
- 经营现金流按国际财务报告准则美元建模（十亿美元，USD bn），按价格日即期汇率折人民币；
  资产负债表项目取 2026-06-30 企业会计准则人民币数（亿元）。
- 每股价值按全部股份（A 股 + H 股）计算，总股本 85.6238 亿股，无库存股、无拟注销回购股。
- 所有者收益 = 经营 EBITDA（经营利润 + 折旧摊销，不含联营与金融资产收益）− 现金税 − 维持性资本开支
  − 扩张性资本开支 − 营运资金增量；归母份额按情景取集团所有者收益的固定比例。
- 经调整净现金为负，用有杠杆口径（净负债按现规模滚动，扣其税后利息现值），另列无杠杆口径对照。

运行：python3 valuation.py
"""

# ---------------------------------------------------------------- 市场与股本
PRICE_DATE = "2026-10-21"
PRICE_A = 100.24            # A 股收盘，元
PRICE_H_HKD = 49.96         # H 股收盘，港元（腾讯行情 16:08:26 收市）
HKD_CNY = 0.8507            # 腾讯行情 2026-10-21
USD_CNY = 6.6779            # 腾讯行情 2026-10-21
PRICE_H = PRICE_H_HKD * HKD_CNY
SHARES = 85.6238            # 亿股，全部股份（行情口径 8,562,381,909 股）
SHARES_H = 60.1461          # 亿股（6,014,605,927 股）
SHARES_A = SHARES - SHARES_H
BVPS = 1714.57 / SHARES     # 2026-06-30 归母权益 / 总股本
USD_BN_TO_YI = USD_CNY * 10  # 1 十亿美元 = 66.78 亿元

# ---------------------------------------------------------------- 资产负债表（2026-06-30，亿元）
CASH = 690.54               # 货币资金（含 3 个月以上定期存款 130.4）
TRADING_FA = 5.81           # 结构性存款 + 货币基金
DEPOSIT_1Y = 175.66         # 一年内到期的非流动资产 = 长期定期存款（A 股中报附注七、12）
DEPOSIT_LT = 72.67          # 其他非流动资产中的 1-3 年定期存款（附注七、30）
DEBT = 955.74               # 短期借款 145.18 + 长期借款 604.55 + 一年内到期 205.98 + 租赁 0.04（不含套期衍生负债）
REV_2026E_USD = 11.734      # 十亿美元，见 base_year()
OP_RESERVE = 0.05 * REV_2026E_USD * 68.175  # 经营备付：2026E 收入 5%，按 6-30 汇率 6.8175 折算
CASH_LIKE = CASH + TRADING_FA + DEPOSIT_1Y + DEPOSIT_LT
NET_CASH_RAW = CASH_LIKE - DEBT
NET_CASH_ADJ = NET_CASH_RAW - OP_RESERVE   # 无受限资金、无已宣派股利、无关联方存款
NCI_BOOK = 866.36           # 少数股东权益
# 非经营资产：长期股权投资 170.54（股权投资基金 130.30、芯鑫融资租赁/中芯宁波/芯联集成 30.64、其他 9.60）
#            + 其他非流动金融资产 92.67（未上市权益工具，第三层次公允价值）
NONOP = 170.54 + 92.67
DEBT_RATE = 2 * 179.273 / ((12587.850 + 14017.712) / 2)   # 上半年财务费用年化 / 平均借款（含套期成本）
TAX_ON_INTEREST = 0.15

# ---------------------------------------------------------------- 2026 基年（十亿美元）
def base_year():
    h1_rev, h1_op, h1_da = 5.511075, 0.781971, 2.299860
    q3_rev = 3.006 * 1.03            # 指引环比 +2%~+4% 取中值
    q4_rev = q3_rev * 1.01
    gm = 0.27                         # 指引 26%~28% 取中值，四季度持平
    net_opex = 0.235                  # 二季度 0.2265、一季度 0.2555（毛利 − 经营利润）
    da_q = (5.0 - h1_da) / 2          # 全年折旧“接近 50 亿美元”
    q3_op = q3_rev * gm - net_opex
    q4_op = q4_rev * gm - net_opex
    rev = h1_rev + q3_rev + q4_rev
    op_ebitda = h1_op + h1_da + q3_op + q4_op + 2 * da_q
    h2_ebitda = q3_op + q4_op + 2 * da_q
    # 下半年集团经常性净利：经营利润 − 净财务费用 0.033/季 − 税 10%
    h2_np = sum((op - 0.033) * 0.90 for op in (q3_op, q4_op))
    return dict(rev=rev, op_ebitda=op_ebitda, h2_ebitda=h2_ebitda, h2_np=h2_np,
                q3_rev=q3_rev, q4_rev=q4_rev, h2_rev=q3_rev + q4_rev)

BY = base_year()
H2_CAPEX = 4.6            # 全年约 80 亿美元，上半年 34 亿
H2_TAX = 0.06
H2_DNWC = 0.15

# ---------------------------------------------------------------- 情景
YEARS = list(range(2027, 2037))
SCEN = {
    "bear": dict(
        p=0.25,
        vol=[0.04, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.025, 0.02, 0.015],
        price=[-0.05, -0.03, -0.01, 0.0, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005],
        margin=[0.53, 0.49, 0.48, 0.47, 0.47, 0.47, 0.47, 0.47, 0.47, 0.47],
        term_margin=0.46, maint=0.14, kappa=6.0, ronic=0.07, parent=0.68, nonop_haircut=0.80,
        np_margin=0.52, grant_haircut=0.50,
        text="成熟制程 2027 年起价格回落（−5%/−3%），EBITDA 利润率 53%→47%（终值 46%）；"
             "每 1 美元新增年收入需 6 美元资本开支，维持性资本开支占收入 14%，终值增量回报 7%；"
             "出口管制收紧拖累先进制程；归母份额 68%；非经营资产按账面八折"),
    "base": dict(
        p=0.50,
        vol=[0.08, 0.07, 0.06, 0.05, 0.04, 0.035, 0.03, 0.025, 0.02, 0.015],
        price=[0.025, 0.0, -0.01, 0.0, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
        margin=[0.58, 0.565, 0.55, 0.54, 0.53, 0.52, 0.52, 0.52, 0.52, 0.52],
        term_margin=0.51, maint=0.12, kappa=5.0, ronic=0.10, parent=0.65, nonop_haircut=1.00,
        np_margin=0.55, grant_haircut=0.30,
        text="2026 年涨价延续到 2027 年（+2.5%）后持平略降，销量年增 8%→1.5%；EBITDA 利润率 58%→52%"
             "（2021-2026E 均值 52.7%，终值 51%）；每 1 美元新增年收入需 5 美元资本开支，维持性资本开支占收入 12%，"
             "终值增量回报 10%；归母份额 65%"),
    "bull": dict(
        p=0.25,
        vol=[0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.035, 0.03],
        price=[0.05, 0.03, 0.02, 0.015, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
        margin=[0.62, 0.61, 0.60, 0.59, 0.58, 0.57, 0.57, 0.57, 0.57, 0.57],
        term_margin=0.56, maint=0.10, kappa=4.0, ronic=0.12, parent=0.62, nonop_haircut=1.00,
        np_margin=0.575, grant_haircut=0.0,
        text="AI 配套与国产算力先进制程持续供不应求，收入 2027-2031 年复合约 12%，EBITDA 利润率 62%→57%（终值 56%）；"
             "每 1 美元新增年收入需 4 美元资本开支，维持性资本开支占收入 10%，终值增量回报 12%；"
             "增长偏向持股 40.9% 的中芯南方，归母份额 62%"),
}
# 折旧：机器设备 5-10 年直线法（2025 年报 A 股版第 141 页），近似为“滞后 2 年、5 年平均资本开支 × 0.8”，
# 用 2019-2026 年资本开支（十亿美元，业绩说明会口径）校准到 2026 年折旧约 50 亿美元。
CAPEX_HIST = {2019: 1.9, 2020: 5.7, 2021: 4.5, 2022: 6.35, 2023: 7.5, 2024: 7.3, 2025: 8.1, 2026: 8.0}
TAX_RATE = 0.13           # 经营利润口径实际税率：2026H1 所得税 1.013 亿美元 / 经营利润 7.82 亿美元
NWC_RATE = 0.15
G_TERM = 0.025
G_REAL_TERM = 0.015
T_TV = 10.2                                   # 2036 年末距价格日的年数

def _variant(**kw):
    sc = dict(SCEN["base"])
    sc.update(kw)
    return sc

FALSIFIERS = [
    ("F1 2027 年 EBITDA 利润率 ≤52%（毛利率回到 20% 以下）", _variant(
        margin=[0.52, 0.51, 0.50, 0.49, 0.48, 0.48, 0.48, 0.48, 0.48, 0.48], term_margin=0.47)),
    ("F2 2027 年资本开支 ≥75 亿美元而月产能增幅 <6%（κ≈6.5，终值增量回报 7%）", _variant(kappa=6.5, ronic=0.07)),
    ("F3 2026 年少数股东占经常性净利 >40%（归母份额 58%）", _variant(parent=0.58)),
    ("F4 出口管制收紧：维持性资本开支 15%、销量增速下调", _variant(
        maint=0.15, vol=[0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.025, 0.02, 0.02, 0.015])),
    ("U1 上修：2027 年 EBITDA 利润率 ≥60% 且 κ≤4", _variant(
        margin=[0.60, 0.59, 0.58, 0.57, 0.56, 0.55, 0.55, 0.55, 0.55, 0.55], term_margin=0.54, kappa=4.0, ronic=0.12)),
]

# ---------------------------------------------------------------- 2026 正常化归母净利（亿元，企业会计准则口径）
H1_DEDUCT_PARENT = 29.94     # 2026H1 扣非归母净利（A 股中报）
H1_BEIFANG_MINORITY = 3.74   # 少数股东损益 19.71 − 四家非全资子公司 15.97 = 中芯北方 49% 在 1-6/12 的份额
PARENT_SHARE_H2 = 0.555      # 二季度经常性净利中归母份额（剔除北方 49% 后，见正文）
GRANTS_RECURRING = 2 * 9.13  # 上半年列入经常性的政府补助 10.52 − 1.39，年化

def normalized_np(s):
    h2_parent = BY["h2_np"] * USD_BN_TO_YI * PARENT_SHARE_H2
    reported_like = H1_DEDUCT_PARENT + h2_parent + H1_BEIFANG_MINORITY
    cyc = (BY["op_ebitda"] - s["np_margin"] * BY["rev"]) * 0.90 * PARENT_SHARE_H2 * USD_BN_TO_YI
    grant = GRANTS_RECURRING * s["grant_haircut"] * 0.90 * 0.65
    return dict(reported_like=reported_like, h2_parent=h2_parent, cyc=cyc, grant=grant,
                normalized=reported_like - cyc - grant)

# ---------------------------------------------------------------- DCF
def dcf(s, coe=0.09, margin_shift=0.0):
    rev = BY["rev"]
    rows = []
    pv_explicit = 0.0
    h2_fcf = BY["h2_ebitda"] - H2_CAPEX - H2_TAX - H2_DNWC
    pv_explicit += h2_fcf                                          # t ≈ 0
    capex = dict(CAPEX_HIST)
    for i, y in enumerate(YEARS):
        prev = rev
        rev = prev * (1 + s["vol"][i]) * (1 + s["price"][i])
        m = s["margin"][i] + margin_shift
        ebitda = rev * m
        maint = rev * s["maint"]
        vol_next = s["vol"][i + 1] if i + 1 < len(YEARS) else G_REAL_TERM
        gcap = s["kappa"] * rev * vol_next
        capex[y] = maint + gcap
        da = 0.16 * sum(capex[y - k] for k in range(2, 7))
        tax = TAX_RATE * max(ebitda - da, 0.0)
        dnwc = NWC_RATE * (rev - prev)
        oe = ebitda - tax - maint                                   # 扣扩张性投入前的所有者收益
        fcf = oe - gcap - dnwc
        t = (y - 2026) - 0.3
        pv = fcf / (1 + coe) ** t
        pv_explicit += pv
        rows.append(dict(year=y, rev=rev, margin=m, ebitda=ebitda, da=da, tax=tax, maint=maint, gcap=gcap,
                         dnwc=dnwc, oe=oe, fcf=fcf, pv=pv))
    rev_t = rev * (1 + G_TERM)
    ebitda_t = rev_t * (s["term_margin"] + margin_shift)
    da_t = rev_t * (s["maint"] + s["kappa"] * G_REAL_TERM)         # 稳态折旧≈稳态资本开支
    tax_t = TAX_RATE * max(ebitda_t - da_t, 0.0)
    oe_t = ebitda_t - tax_t - rev_t * s["maint"]
    fcf_t = oe_t * (1 - G_TERM / s["ronic"])
    tv = fcf_t / (coe - G_TERM)
    pv_tv = tv / (1 + coe) ** T_TV
    group_ops = pv_explicit + pv_tv                                # 十亿美元
    parent_ops = s["parent"] * group_ops * USD_BN_TO_YI            # 亿元
    and_ = -NET_CASH_ADJ                                           # 经调整净负债（集团）
    int_pv = and_ * DEBT_RATE * (1 - TAX_ON_INTEREST) / coe * s["parent"]
    nonop = NONOP * s["nonop_haircut"]
    eq_lev = parent_ops - int_pv + nonop
    eq_unlev = parent_ops - and_ * s["parent"] + nonop
    return dict(rows=rows, h2_fcf=h2_fcf, pv_explicit=pv_explicit, pv_tv=pv_tv, tv_share=pv_tv / group_ops,
                group_ops=group_ops, parent_ops=parent_ops, int_pv=int_pv, nonop=nonop,
                eq_lev=eq_lev, eq_unlev=eq_unlev, v=eq_lev / SHARES, v_unlev=eq_unlev / SHARES,
                oe_t=oe_t, fcf_t=fcf_t)

def weighted(coe=0.09):
    return sum(SCEN[k]["p"] * dcf(SCEN[k], coe)["v"] for k in SCEN)

def solve(f, target, lo, hi, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2

def implied_irr(price, key="base"):
    return solve(lambda r: dcf(SCEN[key], r)["v"], price, 0.026, 0.40)

# ---------------------------------------------------------------- 输出
def main():
    print(f"中芯国际 688981/00981 独立估值  价格日 {PRICE_DATE}")
    print(f"A 股 {PRICE_A:.2f} 元；H 股 {PRICE_H_HKD:.2f} 港元 × {HKD_CNY} = {PRICE_H:.2f} 元；A/H 溢价 {PRICE_A / PRICE_H - 1:.1%}")
    print(f"总股本 {SHARES:.4f} 亿股（A {SHARES_A:.4f} + H {SHARES_H:.4f}）；美元兑人民币 {USD_CNY}")
    print(f"A 股价×全部股本 = {PRICE_A * SHARES:,.1f} 亿元；H 股价×全部股本 = {PRICE_H * SHARES:,.1f} 亿元；每股净资产 {BVPS:.2f} 元")
    print()
    print("[基年 2026E，十亿美元] 收入 %.3f（下半年 %.3f）；经营 EBITDA %.3f（利润率 %.1f%%）；下半年集团经常性净利 %.3f"
          % (BY["rev"], BY["h2_rev"], BY["op_ebitda"], BY["op_ebitda"] / BY["rev"] * 100, BY["h2_np"]))
    print()
    print("[经调整净现金，亿元，2026-06-30] 现金类 %.2f − 有息负债 %.2f = %.2f；减经营备付 %.2f → %.2f"
          % (CASH_LIKE, DEBT, NET_CASH_RAW, OP_RESERVE, NET_CASH_ADJ))
    print("  非经营资产 %.2f 亿元；少数股东权益 %.2f 亿元；有息负债实际平均利率 %.2f%%" % (NONOP, NCI_BOOK, DEBT_RATE * 100))
    print()
    print("[2026 正常化归母净利，亿元]")
    for k in ("bear", "base", "bull"):
        n = normalized_np(SCEN[k])
        print("  %-4s 报表口径估计 %.1f（上半年扣非 %.2f + 下半年 %.1f + 北方备考 %.2f）− 周期超额 %.1f − 补助折扣 %.1f = %.1f"
              % (k, n["reported_like"], H1_DEDUCT_PARENT, n["h2_parent"], H1_BEIFANG_MINORITY, n["cyc"], n["grant"], n["normalized"]))
    print()
    res = {k: dcf(SCEN[k]) for k in SCEN}
    for k in ("bear", "base", "bull"):
        r = res[k]
        print(f"[{k}] 概率 {SCEN[k]['p']:.0%}  归母份额 {SCEN[k]['parent']:.0%}  κ={SCEN[k]['kappa']}  维持性资本开支 {SCEN[k]['maint']:.0%}")
        print("   年份  收入   利润率  EBITDA  折旧   现金税  维持   扩张   营运资金 所有者收益(前) FCF")
        for row in r["rows"]:
            print("   %d %6.2f  %5.1f%% %6.2f  %5.2f  %5.2f  %5.2f  %5.2f  %5.2f   %6.2f  %6.2f"
                  % (row["year"], row["rev"], row["margin"] * 100, row["ebitda"], row["da"], row["tax"], row["maint"],
                     row["gcap"], row["dnwc"], row["oe"], row["fcf"]))
        print("   2026H2 FCF %.2f；显性期现值 %.2f；终值现值 %.2f（占 %.0f%%）；集团经营价值 %.2f 十亿美元"
              % (r["h2_fcf"], r["pv_explicit"], r["pv_tv"], r["tv_share"] * 100, r["group_ops"]))
        print("   归母经营价值 %.1f − 净负债利息现值 %.1f + 非经营资产 %.1f = %.1f 亿元 → V = %.2f 元/股（无杠杆口径 %.2f）"
              % (r["parent_ops"], r["int_pv"], r["nonop"], r["eq_lev"], r["v"], r["v_unlev"]))
        print()
    vw = weighted()
    v8, v10 = weighted(0.08), weighted(0.10)
    vw_unlev = sum(SCEN[k]["p"] * res[k]["v_unlev"] for k in SCEN)
    print("[结论] 三情景 V：熊 %.2f / 基准 %.2f / 牛 %.2f；加权 V = %.2f 元/股（无杠杆口径 %.2f）"
          % (res["bear"]["v"], res["base"]["v"], res["bull"]["v"], vw, vw_unlev))
    print("  P/V（A 股）= %.2f；P/V（H 股折人民币）= %.2f" % (PRICE_A / vw, PRICE_H / vw))
    print("  股权成本 8%%：V = %.2f（熊 %.2f / 基 %.2f / 牛 %.2f）；10%%：V = %.2f（熊 %.2f / 基 %.2f / 牛 %.2f）"
          % (v8, dcf(SCEN["bear"], 0.08)["v"], dcf(SCEN["base"], 0.08)["v"], dcf(SCEN["bull"], 0.08)["v"],
             v10, dcf(SCEN["bear"], 0.10)["v"], dcf(SCEN["base"], 0.10)["v"], dcf(SCEN["bull"], 0.10)["v"]))
    irr_a, irr_h = implied_irr(PRICE_A), implied_irr(PRICE_H)
    print("  现价隐含回报（基准现金流）：A 股 %.2f%%；H 股 %.2f%%" % (irr_a * 100, irr_h * 100))
    print("  分档价格（V 不变）：≤%.2f 明显低估；%.2f~%.2f 温和低估；%.2f~%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    # 反向 DCF
    target_eq = PRICE_A * SHARES
    b = SCEN["base"]
    shift = solve(lambda d: dcf(b, 0.09, d)["v"], PRICE_A, 0.0, 0.40)
    oe27 = b["parent"] * res["base"]["rows"][0]["oe"] * USD_BN_TO_YI
    ops_target = target_eq + res["base"]["int_pv"] - res["base"]["nonop"]
    def pv_growth(g10):
        pv, oe = 0.0, oe27
        for i in range(10):
            if i > 0:
                oe *= 1 + g10
            pv += oe / 1.09 ** (0.7 + i)
        tv = oe * (1 + G_TERM) * (1 - G_TERM / b["ronic"]) / (0.09 - G_TERM)
        return pv + tv / 1.09 ** T_TV
    g10 = solve(pv_growth, ops_target, -0.5, 1.0)
    g_perp = 0.09 - oe27 / ops_target
    print("[反向 DCF，A 股 %.2f 元]" % PRICE_A)
    print("  基准路径各年 EBITDA 利润率需整体上移 %.1f 个百分点（2027 年需 %.0f%%，终值 %.0f%%）" %
          (shift * 100, (b["margin"][0] + shift) * 100, (b["term_margin"] + shift) * 100))
    print("  以 2027 年基准归母所有者收益 %.0f 亿元为起点、不计扩张投入：10 年复合增速需 %.1f%%（其后 2.5%%）；永续增速需 %.1f%%"
          % (oe27, g10 * 100, g_perp * 100))
    shift_h = solve(lambda d: dcf(b, 0.09, d)["v"], PRICE_H, -0.2, 0.40)
    print("  H 股 %.2f 元：利润率需上移 %.1f 个百分点" % (PRICE_H, shift_h * 100))
    print()
    # 交叉验证
    ebitda26 = BY["op_ebitda"] * USD_BN_TO_YI
    ebitda26n = 0.55 * BY["rev"] * USD_BN_TO_YI
    def ev(mcap):
        return mcap + NCI_BOOK - NET_CASH_RAW - NONOP
    print("[交叉验证]")
    for name, px in (("A 股", PRICE_A), ("H 股", PRICE_H), ("加权 V", vw)):
        e = ev(px * SHARES)
        print("  %s：EV %.0f 亿元；EV/2026E EBITDA %.1f×（正常化 %.1f×）；P/B %.2f×；P/正常化 EPS %.0f×"
              % (name, e, e / ebitda26, e / ebitda26n, px / BVPS, px / (normalized_np(SCEN['base'])['normalized'] / SHARES)))
    print("  中芯北方 49% 交易：EV/EBITDA 12.33×、P/B 1.98×（市场法，已剔除 A 股流动性溢价 39.26%）")
    print()
    # 增长路径（归母所有者收益，扣扩张投入前）
    oe26 = b["parent"] * (BY["rev"] * b["np_margin"] * (1 - 0.03) - BY["rev"] * b["maint"]) * USD_BN_TO_YI
    path = [b["parent"] * r["oe"] * USD_BN_TO_YI for r in res["base"]["rows"][:5]]
    growth = [path[0] / oe26 - 1] + [path[i] / path[i - 1] - 1 for i in range(1, 5)]
    reinv = sum(r["gcap"] + r["dnwc"] for r in res["base"]["rows"][:5]) / sum(r["oe"] for r in res["base"]["rows"][:5])
    inv = sum(r["gcap"] + r["dnwc"] for r in res["base"]["rows"][:4]) + (H2_CAPEX - 0.5 * b["maint"] * BY["rev"])
    inc_ret = (res["base"]["rows"][4]["oe"] - oe26 / b["parent"] / USD_BN_TO_YI) / inv
    print("[基准增长路径] 2026 正常化归母所有者收益 %.0f 亿元；2027-2031：%s" %
          (oe26, " ".join("%.0f" % x for x in path)))
    print("  同比：%s；再投资率 %.0f%%；显性期增量回报 %.1f%%；终值增量回报 %.0f%%"
          % (" ".join("%.1f%%" % (g * 100) for g in growth), reinv * 100, inc_ret * 100, b["ronic"] * 100))
    print()
    # 证伪情景
    print("[证伪与上修条件触发后的 V（其余按基准）]")
    for name, sc in FALSIFIERS:
        print("  %s：V = %.2f" % (name, dcf(sc)["v"]))
    # 牛市经济性下，A 股价格需要的销量增速倍数
    bull = SCEN["bull"]
    def v_scaled(f):
        sc = dict(bull); sc["vol"] = [x * f for x in bull["vol"]]
        return dcf(sc)["v"]
    f_need = solve(v_scaled, PRICE_A, 1.0, 12.0)
    print("  牛市经济性（κ=4、利润率 57%%-62%%）下，A 股价格需销量增速为牛市路径的 %.1f 倍（2027 年销量 +%.0f%%）"
          % (f_need, bull["vol"][0] * f_need * 100))

if __name__ == "__main__":
    main()
