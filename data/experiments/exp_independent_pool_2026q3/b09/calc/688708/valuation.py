#!/usr/bin/env python3
"""佳驰科技（688708）独立估值：无杠杆所有者收益 DCF（经调整净现金为正，照常加回）。

用法：python3 valuation.py
输入全部写在脚本内（金额单位亿元，每股单位元），来源页码见同批 companies/688708_佳驰科技.md。
打印：三情景 V、加权 V、P/V、8%/10% 股权成本下的 V、基准情景现价隐含回报、反向 DCF、
2026 正常化归母净利三档、证伪条件触发后的 V、交叉验证读数。
"""

# ---------------------------------------------------------------- 快照
PRICE = 38.50            # 2026-10-20 收盘，元
SHARES = 4.0048          # 亿股，2026-06-24 归属登记后总股本；无回购专户、无拟注销股份
MCAP = PRICE * SHARES
COE = 0.09

# ---------------------------------------------------------------- 2026-06-30 资产负债表
CASH = 1.995205          # 货币资金（无受限，2026H1 第 111、153 页）
TRADING_FA = 2.134088    # 交易性金融资产：非保本浮动收益理财（第 111 页）
CD_CURRENT = 0.432312    # 一年内到期的非流动资产：可转让大额存单（第 126 页）
CD_NONCURRENT = 10.472769  # 其他非流动资产中的可转让大额存单（第 137 页；预付工程设备款 0.0218 不计）
LEASE = 0.000515         # 租赁负债含一年内到期（第 70、151 页），无借款
OP_RESERVE = 1.0         # 经营备付：约 2 个月付现成本
GROSS_CASH = CASH + TRADING_FA + CD_CURRENT + CD_NONCURRENT
NET_CASH_ADJ = GROSS_CASH - LEASE - OP_RESERVE
NON_OPERATING = 0.0      # 无长期股权投资、无投资性房地产

# 经营性营运资本 = 应收账款 + 应收票据 + 存货 + 预付 − 应付票据 − 应付账款 − 合同负债
WC_YE2025 = 12.823195 + 2.128558 + 2.227177 + 0.024605 - 1.343818 - 2.295859 - 0.269667
WC_MID2026 = 12.500036 + 2.181815 + 3.527553 + 0.181600 - 1.016709 - 2.485633 - 0.530717

# 2026H1 实际：经营 EBIT = 营收 − 营业成本 − 税金及附加 − 销售 − 管理 − 研发 + 增值税加计抵减
#                      + 信用减值 + 资产减值（剔除政府补助、个税手续费、理财收益、利息与营业外）
EBIT_H1 = (2.605340 - 0.860679 - 0.033388 - 0.044076 - 0.360784 - 0.793800
           + 0.019159 - 0.105195 - 0.054653)
DA_H1 = 0.357122 + 0.007364 + 0.000148
CAPEX_H1 = 0.346539

# 交叉验证用：2025 年与 2025H1 经营 EBIT（同一口径）
EBIT_2025 = (11.072768 - 3.689569 - 0.140003 - 0.090741 - 0.652133 - 1.663904
             + 0.037133 - 0.412253 - 0.079421)
EBIT_H1_2025 = (2.786430 - 0.730026 - 0.039145 - 0.048502 - 0.293369 - 0.709723
                + 0.016688 + 0.096637 - 0.030685)

# 利润率三分法用：2024 年与 TTM 的分项（营收、营业成本、研发、管理、减值合计、税金及附加+销售−增值税加计）
P2024 = dict(rev=9.568498, cogs=2.216212, rnd=0.875986, adm=0.414715, imp=0.214835 + 0.038516,
             oth=0.122 + 0.086726 - 0.017861)
PTTM = dict(rev=11.072768 - 2.786430 + 2.605340, cogs=3.689569 - 0.730026 + 0.860679,
            rnd=1.663904 - 0.709723 + 0.793800, adm=0.652133 - 0.293369 + 0.360784,
            imp=(0.412253 + 0.079421) - (-0.096637 + 0.030685) + (0.105195 + 0.054653),
            oth=(0.140003 - 0.039145 + 0.033388) + (0.090741 - 0.048502 + 0.044076)
                - (0.037133 - 0.016688 + 0.019159))
NONREC_TTM = dict(subsidy=0.235935 - 0.065 + 0.168555, fin=0.241781 - 0.111 + 0.131953)

# ---------------------------------------------------------------- 税与费用参数
TAX_HT = 0.15            # 高新技术企业 15%（证书 2024-2026，假设 2027 年续期）
RD_DEDUCT = 0.95         # 研发费用 100% 加计扣除，约 95% 可扣
NONDED = 0.005           # 不可抵扣项目与子公司税率差，占 EBIT
SELL = 0.0085            # 销售费用率
SURTAX = 0.0125          # 税金及附加 / 营收
OTHER_REC = 0.0025       # 增值税加计抵减等经常性其他收益 / 营收
YIELD_CASH = 0.017       # 现金类资产税前收益率（2026H1 理财+存单+利息年化约 1.75%）

T_YE2026 = 72 / 365      # 2026-10-20 至 2026-12-31（年）


def tax_of(ebit, rnd):
    return TAX_HT * max(0.0, ebit - RD_DEDUCT * rnd) + NONDED * max(ebit, 0.0)


# ---------------------------------------------------------------- 三情景
# rnd 列表为营收占比；wc 为年末营运资本 / 当年营收（2026…2031）
SCEN = {
    "bear": dict(p=0.25, g_term=0.020, roiic=0.15,
                 rev26=9.0, growth=[0.03, 0.04, 0.04, 0.04, 0.03],
                 gm26=0.640, gm=[0.610] * 5,
                 rnd26=1.80, rnd=[0.185, 0.180, 0.175, 0.170, 0.168],
                 adm26=0.72, adm_g=0.03, imp26=0.030, imp=0.020,
                 da=[0.73, 0.80, 0.83, 0.85, 0.87, 0.89],
                 capex=[0.85, 1.05, 0.85, 0.85, 0.90, 0.90],
                 wc=[1.85, 1.80, 1.75, 1.70, 1.65, 1.65]),
    "base": dict(p=0.50, g_term=0.025, roiic=0.25,
                 rev26=10.0, growth=[0.09, 0.08, 0.07, 0.06, 0.05],
                 gm26=0.655, gm=[0.655] * 5,
                 rnd26=1.80, rnd=[0.160, 0.155, 0.150, 0.145, 0.140],
                 adm26=0.72, adm_g=0.05, imp26=0.020, imp=0.013,
                 da=[0.73, 0.80, 0.84, 0.87, 0.90, 0.93],
                 capex=[0.85, 1.10, 0.90, 0.90, 0.95, 1.00],
                 wc=[1.55, 1.48, 1.42, 1.36, 1.35, 1.35]),
    "bull": dict(p=0.25, g_term=0.025, roiic=0.30,
                 rev26=11.0, growth=[0.15, 0.13, 0.11, 0.09, 0.07],
                 gm26=0.665, gm=[0.680] * 5,
                 rnd26=1.80, rnd=[0.150, 0.140, 0.130, 0.125, 0.120],
                 adm26=0.72, adm_g=0.06, imp26=0.015, imp=0.010,
                 da=[0.73, 0.82, 0.88, 0.94, 1.00, 1.06],
                 capex=[0.85, 1.20, 1.10, 1.10, 1.15, 1.20],
                 wc=[1.45, 1.30, 1.20, 1.15, 1.10, 1.10]),
}

# 2026 正常化归母净利三档（含现金利息、剔除补助与理财以外的一次性项目）
NORM = {"bear": dict(rev=9.5, gm=0.610, rnd=1.70, adm=0.72, imp=0.025),
        "base": dict(rev=10.8, gm=0.655, rnd=1.62, adm=0.72, imp=0.015),
        "bull": dict(rev=12.0, gm=0.685, rnd=1.56, adm=0.74, imp=0.010)}


def project(s):
    rev = [s["rev26"]]
    for g in s["growth"]:
        rev.append(rev[-1] * (1 + g))
    rows, adm, wc_prev = [], s["adm26"], WC_YE2025
    for i, year in enumerate(range(2026, 2032)):
        r = rev[i]
        gm = s["gm26"] if i == 0 else s["gm"][i - 1]
        if i == 0:
            rnd = s["rnd26"]
        else:
            rnd = r * s["rnd"][i - 1]
            adm *= 1 + s["adm_g"]
        imp = s["imp26"] if i == 0 else s["imp"]
        ebit = r * (gm - SURTAX - SELL - imp + OTHER_REC) - adm - rnd
        nopat = ebit - tax_of(ebit, rnd)
        wc = s["wc"][i] * r
        dwc = wc - wc_prev
        oe = nopat + s["da"][i] - s["capex"][i] - dwc
        rows.append(dict(year=year, rev=r, gm=gm, rnd=rnd, adm=adm, ebit=ebit, nopat=nopat,
                         da=s["da"][i], capex=s["capex"][i], wc=wc, dwc=dwc, oe=oe))
        wc_prev = wc
    return rows


def value(s, r=COE):
    rows = project(s)
    y26 = rows[0]
    nopat_h2 = y26["nopat"] - EBIT_H1 * (1 - NONDED)
    oe_h2 = (nopat_h2 + (y26["da"] - DA_H1) - (y26["capex"] - CAPEX_H1)
             - (y26["wc"] - WC_MID2026))
    pv = oe_h2 / (1 + r) ** T_YE2026
    for k, row in enumerate(rows[1:]):                 # 2027…2031，年中折现
        pv += row["oe"] / (1 + r) ** (T_YE2026 + 0.5 + k)
    g = s["g_term"]
    nopat_next = rows[-1]["nopat"] * (1 + g)
    oe_next = nopat_next * (1 - g / s["roiic"])
    tv = oe_next / (r - g)
    pv_tv = tv / (1 + r) ** (T_YE2026 + 0.5 + len(rows) - 2)
    equity = pv + pv_tv + NET_CASH_ADJ + NON_OPERATING
    return dict(rows=rows, oe_h2=oe_h2, pv_explicit=pv, pv_tv=pv_tv, equity=equity,
                v=equity / SHARES, tv_share=pv_tv / (pv + pv_tv), oe_next=oe_next)


def weighted(scen, r=COE, weights=None):
    w = weights or {k: v["p"] for k, v in scen.items()}
    return sum(w[k] * value(scen[k], r)["v"] for k in scen)


def solve(f, lo, hi, target, n=200):
    """f 单调递减时求 f(x)=target。"""
    for _ in range(n):
        mid = (lo + hi) / 2
        if f(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s):
    return solve(lambda r: value(s, r)["equity"], s["g_term"] + 0.002, 0.40, MCAP)


def norm_np(rev, gm, rnd, adm, imp):
    ebit = rev * (gm - SURTAX - SELL - imp + OTHER_REC) - adm - rnd
    nopat = ebit - tax_of(ebit, rnd)
    interest_after_tax = GROSS_CASH * YIELD_CASH * (1 - TAX_HT)
    return ebit, nopat, nopat + interest_after_tax


def reverse_dcf(nopat0, r=COE, g_term=0.025, roiic=0.25):
    ev_op = MCAP - NET_CASH_ADJ
    # (a) 永续增速：EV = NOPAT×(1−g/ROIIC)/(r−g)
    g_perp = solve(lambda g: -(nopat0 * (1 - g / roiic) / (r - g)), 0.0, r - 0.001, -ev_op)
    # (b) 10 年增速：OE0 = NOPAT×(1−g_term/ROIIC)，前 10 年按 g 增长（未扣增长所需的额外再投资，属下限），之后 g_term
    oe0 = nopat0 * (1 - g_term / roiic)

    def pv_of(g):
        pv, oe = 0.0, oe0
        for t in range(1, 11):
            oe *= 1 + g
            pv += oe / (1 + r) ** (T_YE2026 + t - 0.5)
        tv = oe * (1 + g_term) / (r - g_term)
        return pv + tv / (1 + r) ** (T_YE2026 + 9.5)

    g10 = solve(lambda g: -pv_of(g), -0.10, 0.60, -ev_op)
    return ev_op, g_perp, oe0, g10


def with_override(scen, name, **kw):
    out = {k: dict(v) for k, v in scen.items()}
    out[name].update(kw)
    return out


if __name__ == "__main__":
    print(f"现价 {PRICE:.2f} 元 × 股本 {SHARES:.4f} 亿股 = 市值 {MCAP:.2f} 亿元")
    print(f"现金类合计 {GROSS_CASH:.3f}；有息负债 {LEASE:.4f}；经营备付 {OP_RESERVE:.1f}；"
          f"经调整净现金 {NET_CASH_ADJ:.2f} 亿元（{NET_CASH_ADJ / SHARES:.2f} 元/股）")
    print(f"营运资本 2025 年末 {WC_YE2025:.2f}、2026-06-30 {WC_MID2026:.2f} 亿元；"
          f"2026H1 经营 EBIT {EBIT_H1:.3f}")
    ttm_ebit = EBIT_2025 - EBIT_H1_2025 + EBIT_H1
    ev = MCAP - GROSS_CASH + LEASE
    print(f"经营 EBIT：2025 {EBIT_2025:.2f}，TTM {ttm_ebit:.2f}；EV {ev:.2f}，EV/EBIT(TTM) {ev / ttm_ebit:.1f}×")

    def ratios(d):
        r = d["rev"]
        gm = 1 - d["cogs"] / r
        return dict(gm=gm, rnd=d["rnd"] / r, adm=d["adm"] / r, imp=d["imp"] / r, oth=d["oth"] / r,
                    ebit=gm - (d["rnd"] + d["adm"] + d["imp"] + d["oth"]) / r)
    a, b = ratios(P2024), ratios(PTTM)
    nb = NORM["base"]
    n = dict(gm=nb["gm"], rnd=nb["rnd"] / nb["rev"], adm=nb["adm"] / nb["rev"], imp=nb["imp"],
             oth=SURTAX + SELL - OTHER_REC)
    n["ebit"] = n["gm"] - n["rnd"] - n["adm"] - n["imp"] - n["oth"]
    print("经营 EBIT 率三分法（2024 → TTM → 基准正常化）：")
    for k, lab in (("gm", "毛利率"), ("rnd", "研发费率"), ("adm", "管理费率"), ("imp", "减值/营收"),
                   ("oth", "税金+销售−加计"), ("ebit", "经营EBIT率")):
        print(f"  {lab}: {a[k]:.2%} → {b[k]:.2%} → {n[k]:.2%}")
    struct = (n["gm"] - a["gm"]) - (n["rnd"] - a["rnd"]) - (n["adm"] - a["adm"])
    cyc = n["ebit"] - b["ebit"]
    print(f"  结构性（正常化保留）{struct:.2%}，约 {struct * nb['rev']:.2f} 亿元；"
          f"周期性（正常化回补）{cyc:.2%}，约 {cyc * PTTM['rev']:.2f} 亿元；"
          f"一次性（TTM 补助 {NONREC_TTM['subsidy']:.2f}、理财与存单 {NONREC_TTM['fin']:.2f} 亿元，不计入经营利润）")

    res = {}
    for name, s in SCEN.items():
        out = value(s)
        res[name] = out
        print(f"\n== {name}（概率 {s['p']:.2f}，终值增速 {s['g_term']:.1%}，终值增量回报 {s['roiic']:.0%}，"
              f"终值再投资率 {s['g_term'] / s['roiic']:.1%}）")
        print("  年份  营收  毛利率  研发  经营EBIT  NOPAT  折旧  资本开支  营运资本  ΔWC  所有者收益")
        for row in out["rows"]:
            print("  {year} {rev:6.2f} {gm:6.1%} {rnd:5.2f} {ebit:7.2f} {nopat:6.2f} {da:5.2f} {capex:6.2f}"
                  " {wc:8.2f} {dwc:5.2f} {oe:7.2f}".format(**row))
        nopats = [r_["nopat"] for r_ in out["rows"]]
        gr = [nopats[i] / nopats[i - 1] - 1 for i in range(1, len(nopats))]
        print("  NOPAT 增速 2027-2031：" + "、".join(f"{x:.1%}" for x in gr))
        print(f"  2026H2 所有者收益 {out['oe_h2']:.2f}；显性期现值 {out['pv_explicit']:.2f}；终值现值 {out['pv_tv']:.2f}"
              f"（占经营价值 {out['tv_share']:.0%}）；股权价值 {out['equity']:.2f}；V = {out['v']:.2f} 元")
        for r in (0.08, 0.10):
            print(f"  股权成本 {r:.0%}：V = {value(s, r)['v']:.2f} 元")
        print(f"  现价隐含回报（IRR）{implied_irr(s):.2%}")

    vw = weighted(SCEN)
    print(f"\n概率加权 V = {vw:.2f} 元；P/V = {PRICE / vw:.2f}")
    for r in (0.08, 0.10):
        v_r = weighted(SCEN, r)
        print(f"股权成本 {r:.0%}：加权 V = {v_r:.2f} 元，P/V = {PRICE / v_r:.2f}")
    print(f"基准情景现价隐含回报 {implied_irr(SCEN['base']):.2%}")
    print("V 不变时各档价格：≤{:.2f} 明显低估；{:.2f}～{:.2f} 温和低估；{:.2f}～{:.2f} 大致合理；>{:.2f} 偏贵".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    print("\n2026 正常化归母净利（含税后现金利息，剔除补助等一次性项目）：")
    norm = {}
    for k, a in NORM.items():
        e, n, npi = norm_np(**a)
        norm[k] = npi
        print(f"  {k}: 营收 {a['rev']:.1f} 毛利率 {a['gm']:.1%} 研发 {a['rnd']:.2f} → 经营EBIT {e:.2f}，"
              f"NOPAT {n:.2f}，归母净利 {npi:.2f}；市值/正常化净利 {MCAP / npi:.1f}×")

    ev_op, g_perp, oe0, g10 = reverse_dcf(norm_np(**NORM["base"])[1])
    print(f"\n反向 DCF：经营价值 {ev_op:.2f} 亿元；按基准正常化 NOPAT、增量回报 25% 的永续增速 {g_perp:.2%}；"
          f"所有者收益 {oe0:.2f} 亿元起算的 10 年年增速 {g10:.2%}（之后 2.5%）")

    print("\n证伪条件触发后的独立 V：")
    s1 = with_override(SCEN, "bull", growth=[14.1 / 11.0 - 1] + SCEN["bull"]["growth"][1:])
    f1 = value(s1["bull"])["v"]
    print(f"  F1 2027 年营收 ≥ 14.1 亿元（激励计划 2027 触发值）且毛利率 ≥ 66%"
          f"（牛市参数、2027 年营收 14.1 亿元，全权重）：V = {f1:.2f}，P/V = {PRICE / f1:.2f}")
    f2 = weighted(SCEN, weights={"bear": 0.10, "base": 0.45, "bull": 0.45})
    print(f"  F2 2026 年营收 ≥ 11.5 亿元且全年毛利率 ≥ 66%（权重 0.10/0.45/0.45）：V = {f2:.2f}")
    s3 = {k: dict(v) for k, v in SCEN.items()}
    s3["base"]["wc"] = SCEN["bear"]["wc"]
    s3["bull"]["wc"] = SCEN["base"]["wc"]
    f3 = weighted(s3, weights={"bear": 0.40, "base": 0.45, "bull": 0.15})
    print(f"  F3 2026 年末应收票据及账款 ≥ 18 亿元且全年经营现金流 < 0"
          f"（基准与牛市改用低一档营运资本路径，权重 0.40/0.45/0.15）：V = {f3:.2f}")
    f4 = weighted(SCEN, weights={"bear": 0.55, "base": 0.40, "bull": 0.05})
    print(f"  F4 披露审价价差调减收入，或任一单季毛利率 < 60%（权重 0.55/0.40/0.05）：V = {f4:.2f}")
    f5 = value(SCEN["bear"])["v"]
    print(f"  F5 2027 年营收 < 9.5 亿元（熊市情景全权重）：V = {f5:.2f}")
    print(f"\n股息率（过去 12 个月每股 0.50 元）{0.50 / PRICE:.2%}；无回购")
