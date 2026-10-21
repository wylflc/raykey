"""工业富联（601138）独立估值：三情景所有者收益 DCF（有杠杆口径）＋交叉验证。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。所有输入写在本脚本内，来源见正文。
"""

PRICE = 48.77            # 2026-10-20 收盘
SHARES = 198.4409        # 亿股，总股本，含回购专户股份（brief.md）
TREASURY = 0.15833353    # 亿股，2026-09-18 回购完成，拟 12 个月后出售，不注销
BUYBACK_CASH = 10.0005   # 亿元，回购耗资（6-30 之后发生）
COE = 0.09
TAX = 0.15               # 正常化税率（2025 年 13.9%，2026H1 14.6%，支柱二最低税 15%）
TG = 0.025               # 终值增长
MINORITY = 0.0004        # 少数股东占净利比例（2026H1 0.09/237.49）

# ---- 2026-06-30 资产负债表（2026H1_report 第 74～76、117～118、148～154 页）----
CASH = 1004.06           # 货币资金（含存款应收利息 1.51、受限 0.05）
DERIV = 2.25             # 衍生金融资产（外汇远期）
RESTRICTED = 0.05        # 电力保证金
TTM_REV = 10999.88       # TTM 营收（2025 年报 − 2025H1 + 2026H1）
RESERVE_PCT = 0.02       # 经营备付 = TTM 营收 2%
DIV_PAYABLE = 130.52     # 应付股利，2025 年度末期红利 8-03 已派
ST_LOAN = 1023.25        # 短期借款（美元信用借款 949.68 为主，含应付利息 3.59）
LEASE = 55.94            # 租赁负债 39.66 + 一年内到期 16.28
LT_LOAN = 0.04           # 一年内到期长期借款
FACTORING_PAY = 24.33    # 应付保理款（代银行收取的保理回款）
LT_TAX = 11.60           # 长期应交税费（其他非流动负债）
EQ_PURCHASE = 1.69       # 应付股权购买款
NONOP = 43.61 + 6.40 + 2.39   # 长期股权投资 + 其他权益工具投资 + 交易性金融资产（账面）
DEBT_2025 = 1101.84      # 2025-12-31 有息负债（数据包）
INT_H1 = 20.02           # 2026H1 利息费用（2026H1_report 第 161 页）

DEBT = ST_LOAN + LEASE + LT_LOAN
RESERVE = RESERVE_PCT * TTM_REV
NET_CASH_ADJ = (CASH + DERIV - RESTRICTED - RESERVE - DIV_PAYABLE - DEBT
                - FACTORING_PAY - LT_TAX - EQ_PURCHASE)
INT_RATE = 2 * INT_H1 / ((DEBT_2025 + DEBT) / 2)

# ---- 经营口径与情景 ----
H1_REV = 5578.61         # 2026H1 营收
H1_NOPAT = (295.19 - 6.67) * (1 - TAX)   # 2026H1 经营利润（减值后、扣保理成本）税后
NWC_I = 0.13             # 增量营收的营运资金占用（广义营运资本/营收 6-30 为 13.4%）
FIX_I = 0.04             # 增量营收的长期经营资产占用（6-30 为 4.3%）
INTENSITY = NWC_I + FIX_I
YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
T = {2026: 0.0, 2027: 0.70, 2028: 1.70, 2029: 2.70, 2030: 3.70, 2031: 4.70}  # 距 2026-10-20 的年中贴现年数
T_TV = 5.20

SCENARIOS = {
    "bear": dict(p=0.25, rev0=12600, g=[0.05, -0.30, -0.05, 0.05, 0.04],
                 m=[0.0430, 0.0400, 0.0320, 0.0350, 0.0360, 0.0360], tm=0.036,
                 adj={2028: -40.0, 2029: -20.0},
                 text="2027 年云厂商资本开支见顶，2028 年 AI 服务器需求回落 30%，营收回到约 9,300～9,600 亿；"
                      "经营税后利润率 3.2%～3.6%（去杠杆、存货减值、价格竞争）；337 最坏情况 2028～2029 年合计少赚 60 亿"),
    "base": dict(p=0.50, rev0=13000, g=[0.20, 0.02, 0.05, 0.05, 0.04],
                 m=[0.0435, 0.0430, 0.0420, 0.0415, 0.0410, 0.0410], tm=0.041,
                 adj={},
                 text="2026 年营收 13,000 亿（三季度约 3,550、四季度约 3,870）；2027 年 +20%（资本开支预测 +25%～30% 打折并计人民币升值）；"
                      "2028 年消化期 +2%，此后 4%～5%；经营税后利润率由 4.35% 回落到 4.1%（云计算占比上升压低毛利率）"),
    "bull": dict(p=0.25, rev0=13400, g=[0.40, 0.15, 0.10, 0.07, 0.05],
                 m=[0.0440, 0.0450, 0.0460, 0.0460, 0.0460, 0.0460], tm=0.045,
                 adj={},
                 text="AI 基建持续扩张（推理、主权 AI、ASIC 机柜），2027 年 +40%（约等于卖方 2027 年一致预期），2031 年营收约 2.7 万亿；"
                      "液冷、电源、CPO 自供提高利润率到 4.5%～4.6%"),
}


def rev_path(s):
    rev = [s["rev0"]]
    for g in s["g"]:
        rev.append(rev[-1] * (1 + g))
    return rev


def flows(s, nwc_i=NWC_I, margin_shift=0.0):
    rev = rev_path(s)
    out, prev = [], TTM_REV
    for i, y in enumerate(YEARS):
        m = s["m"][i] + (margin_shift if y >= 2027 else 0.0)
        period_rev = rev[i] - H1_REV if y == 2026 else rev[i]   # 2026 年只计 7～12 月
        nopat = period_rev * m + s["adj"].get(y, 0.0)
        d = rev[i] - prev
        reinv = (nwc_i + FIX_I) * d if d > 0 else nwc_i * d     # 收缩时只释放营运资金
        out.append(dict(year=y, rev=rev[i], nopat=nopat, reinv=reinv, oe=nopat - reinv))
        prev = rev[i]
    return out


def value(s, r=COE, levered=True, cash_adj=0.0, shares=SHARES, nwc_i=NWC_I, margin_shift=0.0):
    fl = flows(s, nwc_i, margin_shift)
    pv_exp = sum(f["oe"] / (1 + r) ** T[f["year"]] for f in fl)
    tm = s["tm"] + margin_shift
    ronic = tm / (nwc_i + FIX_I)
    nopat_tv = fl[-1]["rev"] * (1 + TG) * tm
    oe_tv = nopat_tv * (1 - TG / ronic)
    pv_tv = oe_tv / (r - TG) / (1 + r) ** T_TV
    ops = (pv_exp + pv_tv) * (1 - MINORITY)
    nca = NET_CASH_ADJ + cash_adj
    if levered and nca < 0:
        int_pv = (-nca) * INT_RATE * (1 - TAX) / r
        eq = ops - int_pv + NONOP
    else:
        int_pv = 0.0
        eq = ops + nca + NONOP
    return eq / shares, dict(pv_exp=pv_exp, pv_tv=pv_tv, ops=ops, int_pv=int_pv, eq=eq,
                             tv_share=pv_tv / (pv_exp + pv_tv), ronic=ronic, oe_tv=oe_tv)


def weighted(r=COE, probs=None, **kw):
    probs = probs or {k: s["p"] for k, s in SCENARIOS.items()}
    return sum(probs[k] * value(s, r, **kw)[0] for k, s in SCENARIOS.items())


def solve(fn, target, lo, hi, n=200):
    flo = fn(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = fn(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    base = SCENARIOS["base"]
    return solve(lambda r: value(base, r)[0], PRICE, 0.04, 0.20)


def reverse_dcf_10y(r=COE):
    """2026 年基准经营税后利润按常数 g 增长 10 年（2027～2036），再以 2.5% 永续；再投资 = 增量利润 / RONIC。"""
    base = SCENARIOS["base"]
    nopat26 = H1_NOPAT + (base["rev0"] - H1_REV) * base["m"][0]
    ronic = base["tm"] / INTENSITY
    nca_pv = -(-NET_CASH_ADJ) * INT_RATE * (1 - TAX) / r

    def v(g):
        pv, prev = 0.0, nopat26
        for k in range(1, 11):
            n = nopat26 * (1 + g) ** k
            oe = n - (n - prev) / ronic
            pv += oe / (1 + r) ** (k - 0.3)
            prev = n
        oe_tv = prev * (1 + TG) * (1 - TG / ronic)
        pv += oe_tv / (r - TG) / (1 + r) ** 9.7
        return (pv * (1 - MINORITY) + nca_pv + NONOP) / SHARES
    return solve(v, PRICE, -0.05, 0.40), nopat26


def implied_perpetual(r=COE):
    """单阶段：以 2027 年基准经营税后利润为起点，现价隐含的永续增速。"""
    base = SCENARIOS["base"]
    n27 = base["rev0"] * (1 + base["g"][0]) * base["m"][1]
    ronic = base["tm"] / INTENSITY
    ops_mkt = PRICE * SHARES / (1 - MINORITY) + (-NET_CASH_ADJ) * INT_RATE * (1 - TAX) / r - NONOP
    return solve(lambda g: n27 * (1 - g / ronic) / (r - g), ops_mkt, -0.05, 0.085), n27


def main():
    print(f"经调整净现金（无杠杆口径）{NET_CASH_ADJ:.2f} 亿：现金 {CASH + DERIV:.2f} − 受限 {RESTRICTED} − 经营备付 {RESERVE:.2f} "
          f"− 应付股利 {DIV_PAYABLE} − 有息负债 {DEBT:.2f} − 类债务 {FACTORING_PAY + LT_TAX + EQ_PURCHASE:.2f}")
    print(f"有息负债实际平均利率 {INT_RATE:.4f}；净负债税后利息现值 {-NET_CASH_ADJ * INT_RATE * (1 - TAX) / COE:.1f} 亿；非经营资产 {NONOP:.2f} 亿")
    print(f"2026H1 经营税后利润 {H1_NOPAT:.1f} 亿（营收 {H1_REV}，利润率 {H1_NOPAT / H1_REV:.4f}）")
    res = {}
    for k, s in SCENARIOS.items():
        v, info = value(s)
        vu, _ = value(s, levered=False)
        vx, _ = value(s, cash_adj=-BUYBACK_CASH, shares=SHARES - TREASURY)
        res[k] = v
        print(f"\n[{k}] p={s['p']}  V(有杠杆)={v:.2f}  V(无杠杆)={vu:.2f}  V(剔除回购专户)={vx:.2f}  "
              f"终值占比 {info['tv_share']:.1%}  RONIC {info['ronic']:.1%}")
        for f in flows(s):
            print(f"   {f['year']}  营收 {f['rev']:9.1f}  经营税后利润 {f['nopat']:7.1f}  再投资 {f['reinv']:7.1f}  所有者收益 {f['oe']:7.1f}")
        rev = rev_path(s)
        gr = [rev[i + 1] / rev[i] - 1 for i in range(len(rev) - 1)]
        print("   营收增速 2027-2031:", [round(x, 3) for x in gr])
    vw = weighted()
    vw_u = weighted(levered=False)
    vw_x = sum(s["p"] * value(s, cash_adj=-BUYBACK_CASH, shares=SHARES - TREASURY)[0] for s in SCENARIOS.values())
    print(f"\n加权 V（有杠杆）= {vw:.2f}   P/V = {PRICE / vw:.3f}")
    print(f"加权 V（无杠杆）= {vw_u:.2f}   P/V = {PRICE / vw_u:.3f}")
    print(f"加权 V（剔除回购专户股份、扣回购现金）= {vw_x:.2f}   P/V = {PRICE / vw_x:.3f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：V = {v8:.2f}（P/V {PRICE / v8:.3f}）；10%：V = {v10:.2f}（P/V {PRICE / v10:.3f}）")
    irr = implied_irr()
    print(f"现价隐含回报（基准情景流，有杠杆口径）= {irr:.4f}")
    g10, n26 = reverse_dcf_10y()
    gp, n27 = implied_perpetual()
    print(f"反向 DCF：2026 基准经营税后利润 {n26:.1f} 亿，现价隐含 10 年增速 {g10:.4f}；以 2027 年 {n27:.1f} 亿起算的隐含永续增速 {gp:.4f}")

    # 正常化归母净利 2026（含净利息、剔除一次性）：情景营收 × 情景中枢利润率 − 税后净利息；熊市营收取 2026～2031 平均
    net_int_after_tax = (40.30 - 13.11) * (1 - TAX)   # TTM 利息费用 − 利息收入
    norm = {}
    for k, s in SCENARIOS.items():
        rev = rev_path(s)
        r_mid = sum(rev) / len(rev) if k == "bear" else s["rev0"]
        norm[k] = (r_mid * s["tm"]) * (1 - MINORITY) - net_int_after_tax
    print("2026 正常化归母净利（亿）：", {k: round(v, 1) for k, v in norm.items()}, f"税后净利息 {net_int_after_tax:.1f}")

    # 基准增长路径（经营税后利润），再投资率与增量回报
    fl = flows(SCENARIOS["base"])
    n26_full = H1_NOPAT + fl[0]["nopat"]
    seq = [n26_full] + [f["nopat"] for f in fl[1:]]
    growth = [seq[i + 1] / seq[i] - 1 for i in range(len(seq) - 1)]
    reinv_rate = sum(f["reinv"] for f in fl[1:]) / sum(f["nopat"] for f in fl[1:])
    ronic_b = SCENARIOS["base"]["tm"] / INTENSITY
    print(f"\n基准经营税后利润增速 2027-2031：{[round(g, 3) for g in growth]}；2027-2031 平均再投资率 {reinv_rate:.3f}；"
          f"增量回报 {ronic_b:.3f}；终值再投资率 {TG / ronic_b:.3f}")
    vb, ib = value(SCENARIOS["base"])
    print(f"基准：显性期现值 {ib['pv_exp']:.0f}、终值现值 {ib['pv_tv']:.0f}（占 {ib['tv_share']:.1%}）、净负债利息现值 {ib['int_pv']:.0f}")

    # 交叉验证
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NONOP
    ebit_ttm = 578.61 - 14.46
    base = SCENARIOS["base"]
    ebit_26 = (H1_NOPAT + (base["rev0"] - H1_REV) * base["m"][0]) / (1 - TAX)
    print(f"\n市值 {mcap:.1f}；EV {ev:.1f}；EV/EBIT(TTM {ebit_ttm:.1f}) {ev / ebit_ttm:.1f}x；EV/EBIT(2026E 基准 {ebit_26:.1f}) {ev / ebit_26:.1f}x")
    np26_base = H1_NOPAT + (base["rev0"] - H1_REV) * base["m"][0] - net_int_after_tax
    for pe in (11.0, 14.95, 18.0):
        print(f"   PE {pe}x × 2026E 基准经常性净利 {np26_base:.1f} = 每股 {pe * np26_base / SHARES:.2f}")
    print(f"   PB 历史中位 2.71x × 归母权益 1757.53 = 每股 {2.71 * 1757.53 / SHARES:.2f}")
    print(f"   股息率 {0.98 / PRICE:.4f}；回购 10 亿占市值 {BUYBACK_CASH / mcap:.4f}（拟出售，不计入长期回报）")

    # 337 最坏情况单独作用于基准情景
    s337 = dict(base, adj={2028: -40.0, 2029: -20.0})
    print(f"\n337 最坏情况作用于基准：V {value(base)[0]:.2f} → {value(s337)[0]:.2f}")

    # 证伪触发后的 V
    f1 = weighted(margin_shift=-0.003)
    f2 = weighted(nwc_i=0.18)
    f3 = weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    f4 = 0.25 * value(SCENARIOS["bear"])[0] + 0.50 * value(s337)[0] + 0.25 * value(dict(SCENARIOS["bull"], adj={2028: -40.0, 2029: -20.0}))[0]
    f5 = weighted(probs={"bear": 0.15, "base": 0.45, "bull": 0.40})
    print(f"证伪 1（利润率中枢 −0.3pp）V = {f1:.2f}")
    print(f"证伪 2（增量营运资金占用 18%）V = {f2:.2f}")
    print(f"证伪 3（概率改为 50/40/10）V = {f3:.2f}")
    print(f"证伪 4（337 排除令，三情景都计 60 亿损失）V = {f4:.2f}")
    print(f"证伪 5（上行：概率改为 15/45/40）V = {f5:.2f}")
    for band, x in (("0.75", 0.75), ("0.90", 0.90), ("1.10", 1.10)):
        print(f"V 不变时 P/V = {band} 对应价格 {vw * x:.2f}")


if __name__ == "__main__":
    main()
