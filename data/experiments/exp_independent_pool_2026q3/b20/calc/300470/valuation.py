#!/usr/bin/env python3
"""中密控股（300470）独立估值（OI-291 b20，价格日 2026-10-21）。

方法：归母所有者收益 DCF，三情景（熊/基准/牛）概率加权；经营 NOPAT 不含利息与理财收益，
经调整净现金与联营投资另加。另算 8%/10% 股权成本敏感性、反向 DCF 与基准情景隐含回报。
金额单位亿元，每股为元。输入全部写在脚本内，`python3 valuation.py` 复现正文与 json 的全部 V。
"""

# ---------------------------------------------------------------- 价格与股本
PRICE = 26.55                 # 2026-10-21 收盘，未复权（已于 2026-10-13 除息 0.5 元）
SHARES_QUOTE = 2.0793         # 亿股，腾讯行情（= 207,934,737 股，2026-07-13 注销 2.7 万股后）
SHARES_TO_CANCEL = 0.0001     # 1 万股离职激励对象限制性股票，2026-09-15 临时股东会通过回购注销
SHARES = SHARES_QUOTE - SHARES_TO_CANCEL   # 2.0792；无回购专户股份，故不另算剔除口径
COE = 0.09

# ---------------------------------------------------------------- 2026-06-30 资产负债表
# 2026H1_report 第 62-64 页（合并资产负债表）、第 106 页（其他流动资产附注）、第 24 页（受限资产）
CASH = 1.91399825             # 货币资金
TRADING_FA = 4.01731151       # 交易性金融资产（券商/银行理财，自有资金）
OCA_WMP = 5.04008571          # 其他流动资产中“理财产品及应计利息”（结构性存款、大额存单等）
RESTRICTED = 0.08981061       # 银行承兑汇票保证金与履约保证金
DIV_PAID_20261013 = 1.039673685   # 2026 中期 10 派 5 元，股权登记 10-12、除息并派发 10-13（dividend_20260929 第 2 页）
OP_BUFFER = 1.00              # 经营备付：约 1.3 个月经营现金流出（2025 年经营现金流出 9.09 亿）
INTEREST_DEBT = 0.0           # 无短期借款、长期借款、应付债券
LEASE = 0.01146221 + 0.00413526   # 租赁负债（含一年内到期）：净利润已扣使用权资产折旧与租赁利息，只列示不扣
RS_OBLIGATION = 0.647504      # 限制性股票回购义务（其他应付款/库存股），解锁即消失，或有，不扣
CASH_LIKE = CASH + TRADING_FA + OCA_WMP
NET_CASH_ADJ = CASH_LIKE - RESTRICTED - DIV_PAID_20261013 - OP_BUFFER - INTEREST_DEBT
NON_OP = 0.51974095           # 长期股权投资（振兴中密基金 39.99% 份额、川哈院），按账面；其收益不计入 NOPAT

CASH_YIELD = 0.022            # 2026H1 利息收入 289 万 + 理财收益 601 万 + 公允价值变动 295 万，年化约 2.2%
TAX = 0.13                    # 2025 年实际所得税率 13.2%，2026H1 12.1%
INTEREST_AT = NET_CASH_ADJ * CASH_YIELD * (1 - TAX)   # 计入“正常化归母净利”的税后净利息

# ---------------------------------------------------------------- 经营营运资本（剔除限制性股票回购义务）
WC_ASSETS_0630 = 0.15127653 + 7.99669895 + 0.88414511 + 0.11494576 + 0.07359852 + 4.31748351 + 0.60602475
WC_LIABS_0630 = 0.51266611 + 2.42906777 + 0.61047127 + 0.40015392 + 0.26596103 + (0.81732494 - 0.647504) + 0.09950167
WC_0630 = WC_ASSETS_0630 - WC_LIABS_0630
WC_ASSETS_2025 = 0.16862391 + 6.69914411 + 1.55052818 + 0.12618626 + 0.07040794 + 4.68013073 + 0.69107147
WC_LIABS_2025 = 0.77857319 + 2.36169170 + 0.41918590 + 0.77397740 + 0.38754311 + (0.85909159 - 0.67433950) + 0.07949076
WC_2025YE = WC_ASSETS_2025 - WC_LIABS_2025
REV_2025 = 17.6883942
WC_RATIO = 0.51               # 2025 年末经营营运资本/收入 = 50.9%（2023 年约 60%、2024 年约 55%）

# ---------------------------------------------------------------- 已承诺资本开支（2026H1_report 第 109-110 页）
HQ_REMAIN = 2.50 - 1.3821937395       # 总部综合体：预算 2.5 亿，已投 1.38 亿；非生产性，全额作现金流出
RJ4_REMAIN = 1.737195 - 0.5129717153  # 日机密封四期（机械密封、特种泵产业化）：预算 1.74 亿，已投 0.51 亿
HQ_SCHED = {"2026H2": 0.40, 2027: HQ_REMAIN - 0.40}
RJ4_SCHED = {"2026H2": 0.30, 2027: 0.50, 2028: RJ4_REMAIN - 0.80}
CAPEX_RATIO = 0.25            # 2029 年后增长性资本开支/新增收入（固定资产+在建 ≈ 收入 30%）；维护性资本开支 ≈ 折旧摊销

# ---------------------------------------------------------------- 时间
VAL_DATE = 2026 + 293 / 365   # 2026-10-21
T_STUB = 0.10                 # 2026H2 剩余现金流（10-21 至 12-31）的平均折现期
YEARS = [2027, 2028, 2029, 2030, 2031]

# ---------------------------------------------------------------- 2026 年经营核心归母净利（不含利息、补助、汇兑、联营）
H1_2026_CORE = 1.210          # 2026H1 利润总额 1.537 亿剔除净利息理财 0.115、补助 0.054、汇兑损失 -0.046、联营 0.035 等后 ×(1-12.1%)
H1_2025_CORE = 1.653
FY2025_CORE = 3.511           # 2025 年同口径（利润总额 4.444 亿剔除净利息理财 0.188、补助 0.152、汇兑收益 0.027、联营 0.042 等）×(1-13.2%)
H1_2026_REPORTED = 1.34859163 # 2026H1 归母净利（报表）
H2_ONEOFF_AT = 0.07           # 2026H2 补助（税后约 0.05）与联营（约 0.02）；汇兑按 0
Q3_SHARE_OF_H2 = 0.45         # 2025 年 Q3 归母占下半年 45.9%（0.908/1.979），扣非口径 44.4%
HIST_MARGIN = 0.23            # 2023-2024 年经营核心 NOPAT/收入中枢（2024 年约 23.3%）
SBC_2026_AT = 0.30            # 2024 年限制性股票激励摊销税后：2025 年 0.300，2026H1 0.150
SBC_NORMAL_AT = 0.15          # 长期股权激励费用税后假设（预期 2028 年后另有新计划）

SCEN = {
    # h2_nopat：2026H2 经营核心归母净利；rev_g/margin：2027-2031 收入增速与 NOPAT/收入
    "bear": dict(p=0.25, h2_nopat=1.39, rev2026=16.85,
                 rev_g=[-0.010, 0.015, 0.020, 0.020, 0.020],
                 margin=[0.154, 0.156, 0.156, 0.156, 0.156],
                 g_T=0.015, ronic_T=0.15, norm_rev=16.9, norm_margin=0.153,
                 note="增量价格战持续、增量毛利率约 20%，老旧装置出清侵蚀存量，国际业务低迷；收入 2027 年 -1%、其后 +2%，"
                      "NOPAT 率约 15.5%，终值增长 1.5%、新增资本回报 15%"),
    "base": dict(p=0.50, h2_nopat=1.48, rev2026=17.00,
                 rev_g=[0.035, 0.040, 0.049, 0.047, 0.045],
                 margin=[0.164, 0.168, 0.169, 0.170, 0.170],
                 g_T=0.025, ronic_T=0.20, norm_rev=17.4, norm_margin=0.176,
                 note="增量毛利率自约 20% 修复到 25% 上下，存量随装机基数与国产化年增 4%～6%，股份支付 2027-2028 年回落；"
                      "收入年增 3.5%～5%，NOPAT 率 16.4%→17.0%，终值增长 2.5%、新增资本回报 20%"),
    "bull": dict(p=0.25, h2_nopat=1.58, rev2026=17.15,
                 rev_g=[0.070, 0.070, 0.070, 0.060, 0.060],
                 margin=[0.172, 0.178, 0.182, 0.185, 0.186],
                 g_T=0.025, ronic_T=0.25, norm_rev=17.6, norm_margin=0.198,
                 note="乙烯与煤化工项目重启、中东重建带动增量量价回升，增量毛利率回到约 30%，国际恢复增长；"
                      "收入年增 6%～7%，NOPAT 率回到 2025 年水平以上（18.6%），终值增长 2.5%、新增资本回报 25%"),
}


def explicit_flows(s):
    """返回 [(t, 所有者收益, 明细)]：2026H2 存根 + 2027-2031；以及 2031 年 NOPAT。"""
    rows = []
    wc_release = WC_0630 - WC_RATIO * s["rev2026"]          # 6-30 季节性高点回落到年末 51% 收入
    oe_stub = s["h2_nopat"] + wc_release - HQ_SCHED["2026H2"] - RJ4_SCHED["2026H2"]
    rows.append((T_STUB, oe_stub, dict(year="2026H2", rev=s["rev2026"], nopat=s["h2_nopat"],
                                       dwc=-wc_release, gcap=RJ4_SCHED["2026H2"], hq=HQ_SCHED["2026H2"])))
    rev_prev = s["rev2026"]
    nopat = None
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s["rev_g"][i])
        nopat = rev * s["margin"][i]
        dwc = WC_RATIO * (rev - rev_prev)
        gcap = RJ4_SCHED.get(y, 0.0) if y <= 2028 else CAPEX_RATIO * (rev - rev_prev)
        hq = HQ_SCHED.get(y, 0.0)
        oe = nopat - dwc - gcap - hq
        rows.append((y + 0.5 - VAL_DATE, oe, dict(year=y, rev=rev, nopat=nopat, dwc=dwc, gcap=gcap, hq=hq)))
        rev_prev = rev
    return rows, nopat


def value(s, r):
    rows, nopat_2031 = explicit_flows(s)
    pv_exp = sum(oe / (1 + r) ** t for t, oe, _ in rows)
    nopat_2032 = nopat_2031 * (1 + s["g_T"])
    oe_2032 = nopat_2032 * (1 - s["g_T"] / s["ronic_T"])
    t_2032 = 2032.5 - VAL_DATE
    pv_tv = oe_2032 / (r - s["g_T"]) / (1 + r) ** (t_2032 - 1)
    equity = pv_exp + pv_tv + NET_CASH_ADJ + NON_OP
    return dict(v=equity / SHARES, equity=equity, pv_exp=pv_exp, pv_tv=pv_tv, rows=rows,
                tv_share_op=pv_tv / (pv_exp + pv_tv), tv_share_total=pv_tv / equity)


def weighted(r, weights=None):
    w = weights or {k: s["p"] for k, s in SCEN.items()}
    return sum(w[k] * value(SCEN[k], r)["v"] for k in SCEN)


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


def reverse_dcf_10y(g, r=COE, ronic=0.20, g_T=0.025):
    """现价隐含：2026 年经营核心 NOPAT 起，2027-2036 年按 g 增长、再投资 = g/RONIC，其后 2.5%。"""
    base = SCEN["base"]
    nopat0 = H1_2026_CORE + base["h2_nopat"]
    stub_oe = explicit_flows(base)[0][0][1]
    pv = stub_oe / (1 + r) ** T_STUB
    pv -= HQ_SCHED[2027] / (1 + r) ** (2027.5 - VAL_DATE)      # 非生产性总部支出单列
    nopat = nopat0
    for y in range(2027, 2037):
        nopat *= (1 + g)
        oe = nopat * (1 - g / ronic)
        pv += oe / (1 + r) ** (y + 0.5 - VAL_DATE)
    oe_T = nopat * (1 + g_T) * (1 - g_T / ronic)
    pv += oe_T / (r - g_T) / (1 + r) ** (2037.5 - VAL_DATE - 1)
    return (pv + NET_CASH_ADJ + NON_OP) / SHARES


def reverse_dcf_perp(g, r=COE, ronic=0.20):
    """现价隐含永续增长：以基准正常化经营 NOPAT 为 2027 年起点，永续增长 g、再投资 = g/RONIC。"""
    base = SCEN["base"]
    nopat_norm = base["norm_rev"] * base["norm_margin"]
    stub_oe = explicit_flows(base)[0][0][1]
    pv = stub_oe / (1 + r) ** T_STUB - HQ_SCHED[2027] / (1 + r) ** (2027.5 - VAL_DATE)
    oe = nopat_norm * (1 - g / ronic)
    pv += oe / (r - g) / (1 + r) ** (2027.5 - VAL_DATE - 1)
    return (pv + NET_CASH_ADJ + NON_OP) / SHARES


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 输入核对 ==")
    print(f"股本 {SHARES:.4f} 亿股（行情 {SHARES_QUOTE} − 拟注销 {SHARES_TO_CANCEL}）")
    print(f"现金类 {CASH_LIKE:.4f} = 货币资金 {CASH:.4f} + 交易性金融资产 {TRADING_FA:.4f} + 其他流动资产理财 {OCA_WMP:.4f}")
    print(f"经调整净现金 {NET_CASH_ADJ:.4f}（扣受限 {RESTRICTED:.4f}、10-13 已派股利 {DIV_PAID_20261013:.4f}、经营备付 {OP_BUFFER:.2f}；"
          f"有息负债 {INTEREST_DEBT:.2f}；租赁 {LEASE:.4f} 与限制性股票回购义务 {RS_OBLIGATION:.4f} 只列示）")
    print(f"非经营资产（联营）{NON_OP:.4f}；税后净利息 {INTEREST_AT:.4f}")
    print(f"经营营运资本 6-30 {WC_0630:.4f}，2025 年末 {WC_2025YE:.4f}（占 2025 收入 {WC_2025YE / REV_2025:.1%}）")
    print(f"已承诺资本开支：总部剩余 {HQ_REMAIN:.4f}，日机四期剩余 {RJ4_REMAIN:.4f}")
    print(f"经营核心归母净利：2025 {FY2025_CORE:.3f}；2025H1 {H1_2025_CORE:.3f} → 2026H1 {H1_2026_CORE:.3f}"
          f"（{H1_2026_CORE / H1_2025_CORE - 1:+.1%}）")

    print("\n== 2026 正常化归母净利（含税后净利息，剔除一次性；不含联营）==")
    norm = {}
    for k, s in SCEN.items():
        op = s["norm_rev"] * s["norm_margin"]
        norm[k] = op + INTEREST_AT
        print(f"{k}: 正常化收入 {s['norm_rev']:.2f} × NOPAT 率 {s['norm_margin']:.1%} = {op:.3f} + 利息 {INTEREST_AT:.3f}"
              f" = {norm[k]:.2f}；2026 年预计（报表口径前）经营核心 {H1_2026_CORE + s['h2_nopat']:.3f}")

    print("\n== 2026 年预计与正常化拆解 ==")
    for k, s in SCEN.items():
        h2_rep = s["h2_nopat"] + INTEREST_AT / 2 + H2_ONEOFF_AT
        print(f"{k}: 2026E 归母（报表）{H1_2026_REPORTED + h2_rep:.2f}（H1 {H1_2026_REPORTED:.3f} + H2 {h2_rep:.3f}）；"
              f"Q3E {Q3_SHARE_OF_H2 * h2_rep:.2f}、Q4E {(1 - Q3_SHARE_OF_H2) * h2_rep:.2f}；"
              f"2026H2 经营核心同比 {s['h2_nopat'] / (FY2025_CORE - H1_2025_CORE) - 1:+.1%}")
    b = SCEN["base"]
    core26 = H1_2026_CORE + b["h2_nopat"]
    norm_op = b["norm_rev"] * b["norm_margin"]
    hist = HIST_MARGIN * b["norm_rev"]
    print(f"基准：2026E 经营核心 {core26:.2f} → 正常化 {norm_op:.2f}：周期性缺口 {norm_op - core26:.2f}"
          f"（其中股份支付高于常态 {SBC_2026_AT - SBC_NORMAL_AT:.2f}，增量毛利与国际量价 {norm_op - core26 - (SBC_2026_AT - SBC_NORMAL_AT):.2f}）；"
          f"相对 2023-2024 中枢（{HIST_MARGIN:.0%}×{b['norm_rev']:.1f}={hist:.2f}）的结构性缺口 {hist - norm_op:.2f}"
          f"（含常态股权激励 {SBC_NORMAL_AT:.2f}）")

    print("\n== 三情景 DCF（股权成本 9%）==")
    res = {}
    for k, s in SCEN.items():
        out = value(s, COE)
        res[k] = out
        print(f"[{k}] p={s['p']:.2f}  V={out['v']:.2f} 元/股  股权价值 {out['equity']:.2f} 亿"
              f"（显性期 {out['pv_exp']:.2f} + 终值 {out['pv_tv']:.2f} + 净现金 {NET_CASH_ADJ:.2f} + 联营 {NON_OP:.2f}）"
              f"  终值占经营价值 {out['tv_share_op']:.0%}、占股权价值 {out['tv_share_total']:.0%}")
        prev_nopat = H1_2026_CORE + s["h2_nopat"]
        reinv_sum = nopat_sum = 0.0
        for t, oe, d in out["rows"]:
            if d["year"] == "2026H2":
                print(f"   2026H2: NOPAT {d['nopat']:.3f}  营运资本回落 {-d['dwc']:+.3f}  日机四期 -{d['gcap']:.3f}"
                      f"  总部 -{d['hq']:.3f}  → OE {oe:.3f}  (t={t:.2f})")
                continue
            g_n = d["nopat"] / prev_nopat - 1
            prev_nopat = d["nopat"]
            reinv_sum += d["dwc"] + d["gcap"]
            nopat_sum += d["nopat"]
            print(f"   {d['year']}: 收入 {d['rev']:.2f}  NOPAT {d['nopat']:.3f}（{g_n:+.1%}）  ΔWC {d['dwc']:.3f}"
                  f"  增长资本开支 {d['gcap']:.3f}  总部 {d['hq']:.3f}  → OE {oe:.3f}  (t={t:.2f})")
        nopat_2026 = H1_2026_CORE + s["h2_nopat"]
        last = out["rows"][-1][2]["nopat"]
        print(f"   2027-2031 生产性再投资率 {reinv_sum / nopat_sum:.1%}；增量回报（NOPAT 增量/累计生产性再投资）"
              f"{(last - nopat_2026) / (reinv_sum + RJ4_SCHED['2026H2']):.1%}；终值再投资率 {s['g_T'] / s['ronic_T']:.1%}")

    vw = weighted(COE)
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {PRICE:.2f}/{vw:.2f} = {pv:.3f} → {verdict(pv)}")
    print(f"V 不变时进入各档的价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n== 股权成本敏感性 ==")
    for r in (0.08, 0.09, 0.10):
        parts = "  ".join(f"{k} {value(SCEN[k], r)['v']:.2f}" for k in SCEN)
        print(f"r={r:.0%}: {parts}  加权 {weighted(r):.2f}")

    irr_base = solve(lambda r: value(SCEN["base"], r)["v"], 0.05, 0.20, PRICE)
    irr_w = solve(lambda r: weighted(r), 0.05, 0.20, PRICE)
    print(f"\n现价隐含回报（基准情景现金流 = 现价的折现率）：{irr_base:.2%}；（概率加权现金流）{irr_w:.2%}")

    g10 = solve(lambda g: reverse_dcf_10y(g), -0.10, 0.20, PRICE)
    gp = solve(lambda g: reverse_dcf_perp(g), -0.05, 0.08, PRICE)
    print(f"反向 DCF：以 2026 年经营核心 NOPAT {H1_2026_CORE + SCEN['base']['h2_nopat']:.2f} 亿为起点，现价隐含 2027-2036 年"
          f" NOPAT 年增 {g10:.2%}（再投资 = g/20%，其后 2.5%）；以基准正常化 NOPAT "
          f"{SCEN['base']['norm_rev'] * SCEN['base']['norm_margin']:.2f} 亿为 2027 年起点，隐含永续增长 {gp:.2%}")

    print("\n== 交叉验证 ==")
    mcap = PRICE * SHARES_QUOTE
    ev = mcap - NET_CASH_ADJ - NON_OP
    core_2026 = H1_2026_CORE + SCEN["base"]["h2_nopat"]
    print(f"市值 {mcap:.2f} 亿；EV（扣经调整净现金与联营）{ev:.2f} 亿；EV/2026 经营核心 NOPAT {ev / core_2026:.1f}×；"
          f"EV/基准正常化 NOPAT {ev / (SCEN['base']['norm_rev'] * SCEN['base']['norm_margin']):.1f}×")
    print(f"EV/EBIT（2026E 经营核心税前 {core_2026 / (1 - TAX):.2f}）{ev / (core_2026 / (1 - TAX)):.1f}×；"
          f"股息率 {1.00 / PRICE:.2%}（过去 12 个月每股 1.00 元），无回购")
    for k, w in {"F1 三季报走弱": dict(bear=0.45, base=0.45, bull=0.10),
                 "F2 年报扣非与存量走弱": dict(bear=0.60, base=0.40, bull=0.0),
                 "F3 增量与国际持续塌陷": dict(bear=1.0, base=0.0, bull=0.0),
                 "F4 修复确认（上行证伪）": dict(bear=0.10, base=0.50, bull=0.40)}.items():
        print(f"证伪触发 {k}: 权重 {w} → V {weighted(COE, w):.2f}")
    m_and_a_loss = 5.0 - 0.2 / COE
    print(f"证伪触发 F5 高价并购 5 亿（25 倍 PE）：V {vw - m_and_a_loss / SHARES:.2f}（价值损失 {m_and_a_loss:.2f} 亿）")


if __name__ == "__main__":
    main()
