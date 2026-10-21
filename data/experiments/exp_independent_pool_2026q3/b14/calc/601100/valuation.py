#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恒立液压（601100）独立估值 —— OI-291 池内独立审计 b14，价格日 2026-10-20。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。全部输入写在本脚本内，出处见
b14/companies/601100_恒立液压.md（公告文件与 PDF 物理页）。
方法：归母所有者收益 DCF（经营 NOPAT − 再投资，再投资率 = 增速 ÷ 增量回报），
     5 年显性期 + 5 年线性衰减期 + 永续；年中折现；经调整净现金为正，按无杠杆口径全额加回。
"""

PRICE = 83.78            # 2026-10-20 收盘（已于 10-16 除息 0.30 元）
SHARES = 13.4082         # 亿股，总股本；公司无回购专户股份、无可转债
COE = 0.09
T0 = 2026 + 293 / 365    # 估值日 2026-10-20

# ---------------------------------------------------------------------------
# 1. 经调整净现金（2026-06-30；2026H1_report 第 28–30、74–75、94、96 页）
# ---------------------------------------------------------------------------
CASH = 102.6076          # 货币资金
TFA = 2.3701             # 交易性金融资产：外汇掉期公允价值 1.6170 + 理财 0.4517 + 结构性存款 0.3014
RESTRICTED = 11.1257     # 其他货币资金：外汇掉期保证金及利息 11.0804 + 信用证保证金 0.0453（使用权受限）
TTM_REV = 126.0237       # 2025H2 + 2026H1 营业收入
OP_RESERVE = 0.05 * TTM_REV   # 经营备付：TTM 营收 5%
DIV_PAYABLE = 20.4401    # 应付股利：主要应付控股股东恒立控股，未约定支付时间（第 96 页）
DIV_INTERIM = 4.0225     # 2026 中期 0.30 元/股：8-22 董事会决议，10-16 除息并发放（价格已除息）
DEBT = 6.9029 + 0.3002 + 0.0268 + 0.0957   # 短期借款 + 长期借款 + 一年内到期租赁负债 + 租赁负债
NONOP = 0.1103 + 0.0500  # 长期股权投资 + 其他非流动金融资产

NET_CASH_RAW = CASH + TFA - DEBT
NET_CASH_ADJ = CASH + TFA - RESTRICTED - OP_RESERVE - DIV_PAYABLE - DIV_INTERIM - DEBT

# ---------------------------------------------------------------------------
# 2. 核心经营利润（营业利润剔除财务费用、投资收益、公允价值变动；减值、其他收益、资产处置保留）
#    2025_annual_report 第 68–69 页；2026H1_report 第 33 页（含上年同期）
# ---------------------------------------------------------------------------
def core_ebit(rev, cogs, tax_sur, sell, admin, rd, other_inc, credit_imp, asset_imp, disposal):
    return rev - cogs - tax_sur - sell - admin - rd + other_inc + credit_imp + asset_imp + disposal

FY2025 = dict(rev=109.4103, cogs=63.9198, tax_sur=1.0894, sell=2.5450, admin=6.4931, rd=7.0500,
              other_inc=0.8896, credit_imp=-0.3297, asset_imp=-1.0657, disposal=0.0008)
H1_2025 = dict(rev=51.7119, cogs=30.0711, tax_sur=0.5244, sell=1.0395, admin=2.9572, rd=3.5644,
               other_inc=0.3937, credit_imp=-0.0647, asset_imp=-0.1724, disposal=0.0013)
H1_2026 = dict(rev=68.3253, cogs=41.4931, tax_sur=0.6001, sell=1.4625, admin=3.3773, rd=3.6029,
               other_inc=0.3724, credit_imp=-0.2392, asset_imp=-0.6079, disposal=0.0122)
# 财务类项目（财务费用取负 + 投资收益（不含权益法）+ 公允价值变动）
FIN_ITEMS = {"2024": 3.32, "2025": 2.61, "2026H1": -1.44}   # 不含权益法投资收益；仅作说明

CORE_2025 = core_ebit(**FY2025)
CORE_H1_2025 = core_ebit(**H1_2025)
CORE_H1_2026 = core_ebit(**H1_2026)
CORE_TTM = CORE_2025 - CORE_H1_2025 + CORE_H1_2026

# 2026 下半年估计（三季报 10-27 待核）：Q3 营收按 2025Q3 26.1867 × 1.20（1–9 月挖机 +23.1%，Q3 约 +16%），
# Q4 按 2025Q4 31.5117 × 1.15；核心经营利润率 Q3 25.0%、Q4 24.0%（2025Q3 26.2%、Q4 23.0%）
Q3E_REV, Q4E_REV = 26.1867 * 1.20, 31.5117 * 1.15
Q3E_CORE, Q4E_CORE = Q3E_REV * 0.250, Q4E_REV * 0.240
REV_2026E = H1_2026["rev"] + Q3E_REV + Q4E_REV
CORE_2026E = CORE_H1_2026 + Q3E_CORE + Q4E_CORE
MINORITY = 0.06          # 少数股东损益（2025 年 0.056）

# 周期正常化：挖机相关收入约占 55%（估计）；2026 年挖机总销量估 28.2 万台（1–9 月 214,274 台）
EXC_SHARE, EXC_2026E, CONTRIB = 0.55, 282.0, 0.38   # 千台；周期性收入的边际贡献率
SCEN = {
    # mid: 挖机周期中枢（千台）；ramp: 新工厂爬坡损失加回；struct: 结构性利润率侵蚀（占正常化收入）
    "bear": dict(p=0.25, mid=245.0, ramp=0.0, struct=-0.015, fin=1.0, tax=0.12,
                 growth=[0.02, 0.03, 0.04, 0.04, 0.04], roic=0.15, roic_fade=0.13, g_t=0.020, ronic=0.12),
    "base": dict(p=0.50, mid=260.0, ramp=1.0, struct=0.0, fin=1.3, tax=0.105,
                 growth=[0.10, 0.09, 0.08, 0.07, 0.06], roic=0.25, roic_fade=0.20, g_t=0.025, ronic=0.15),
    "bull": dict(p=0.25, mid=282.0, ramp=1.0, struct=0.0, fin=1.6, tax=0.10,
                 growth=[0.15, 0.14, 0.13, 0.11, 0.10], roic=0.30, roic_fade=0.25, g_t=0.025, ronic=0.25),
}


def normalize(s):
    exc_rev = EXC_SHARE * REV_2026E
    excess_rev = exc_rev * (1 - s["mid"] / EXC_2026E)
    rev_norm = REV_2026E - excess_rev
    core = CORE_2026E - excess_rev * CONTRIB + s["ramp"] + s["struct"] * rev_norm
    nopat = core * (1 - s["tax"]) - MINORITY                 # 经营口径（不含利息），DCF 起点
    parent_np = (core + s["fin"]) * (1 - s["tax"]) - MINORITY  # 研究数口径（含正常化净利息）
    return dict(rev_norm=rev_norm, core=core, nopat=nopat, parent_np=parent_np)


def fade(g_last, g_t, n=5):
    return [g_last + (g_t - g_last) * (i + 1) / n for i in range(n)]


# 2026 下半年所有者收益（各情景相同）：H2 核心经营利润 × (1 − 10.5%) × (1 − 30% 再投资) − 少数股东
H2_OE = (Q3E_CORE + Q4E_CORE) * (1 - 0.105) * (1 - 0.30) - MINORITY / 2


def dcf(s, r=COE, n0_mult=1.0, g_add=0.0, detail=False):
    n0 = normalize(s)["nopat"] * n0_mult
    g5 = [g + g_add for g in s["growth"]]
    gs = g5 + fade(g5[-1], s["g_t"])
    roics = [s["roic"]] * 5 + [s["roic_fade"]] * 5
    pv, nopat, rows = H2_OE / (1 + r) ** (2027.0 - T0), n0, []
    for i, (g, ro) in enumerate(zip(gs, roics)):
        year = 2027 + i
        nopat *= 1 + g
        rr = max(g, 0.0) / ro
        oe = nopat * (1 - rr)
        t = year + 0.5 - T0
        pv += oe / (1 + r) ** t
        rows.append((year, g, rr, nopat, oe, t))
    g_t = s["g_t"]
    oe_next = nopat * (1 + g_t) * (1 - g_t / s["ronic"])
    tv = oe_next / (r - g_t)
    t_tv = 2036 + 0.5 - T0
    pv_tv = tv / (1 + r) ** t_tv
    equity = pv + pv_tv + NET_CASH_ADJ + NONOP
    out = dict(v=equity / SHARES, equity=equity, pv_ops=pv + pv_tv, pv_tv=pv_tv,
               tv_share=pv_tv / (pv + pv_tv + NET_CASH_ADJ + NONOP), rows=rows, n0=n0)
    return out if detail else out["v"]


def weighted(r=COE, weights=None, **kw):
    w = weights or {k: SCEN[k]["p"] for k in SCEN}
    return sum(w[k] * dcf(SCEN[k], r, **kw) for k in SCEN)


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


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 经调整净现金（2026-06-30）==")
    print(f"现金类 {CASH + TFA:.2f} − 受限 {RESTRICTED:.2f} − 经营备付 {OP_RESERVE:.2f} − 应付股利 {DIV_PAYABLE:.2f}"
          f" − 2026 中期股利 {DIV_INTERIM:.2f} − 有息负债 {DEBT:.2f} = {NET_CASH_ADJ:.2f}"
          f"（未调整的现金类−有息负债 {NET_CASH_RAW:.2f}；每股 {NET_CASH_ADJ / SHARES:.2f} 元）")
    print(f"非经营资产 {NONOP:.2f}")

    print("\n== 核心经营利润 ==")
    print(f"2025 {CORE_2025:.2f}（利润率 {CORE_2025 / FY2025['rev']:.1%}）；2026H1 {CORE_H1_2026:.2f}"
          f"（{CORE_H1_2026 / H1_2026['rev']:.1%}）；TTM {CORE_TTM:.2f}（{CORE_TTM / TTM_REV:.1%}）")
    print(f"2026E 营收 {REV_2026E:.2f}，核心经营利润 {CORE_2026E:.2f}（Q3E {Q3E_REV:.2f}/{Q3E_CORE:.2f}，"
          f"Q4E {Q4E_REV:.2f}/{Q4E_CORE:.2f}）；H2 所有者收益 {H2_OE:.2f}")

    print("\n== 2026 正常化（研究数含正常化净利息；DCF 起点为经营 NOPAT）==")
    for k, s in SCEN.items():
        n = normalize(s)
        print(f"{k}: 正常化营收 {n['rev_norm']:.2f}，核心经营利润 {n['core']:.2f}（{n['core'] / n['rev_norm']:.1%}），"
              f"经营 NOPAT {n['nopat']:.2f}，正常化归母净利 {n['parent_np']:.2f}")

    print("\n== 三情景 DCF（9%）==")
    vals = {}
    for k, s in SCEN.items():
        d = dcf(s, detail=True)
        vals[k] = d["v"]
        g5 = s["growth"]
        print(f"{k}: V {d['v']:.2f} 元/股（p={s['p']}），经营现值 {d['pv_ops']:.1f}，终值占股权价值 {d['tv_share']:.0%}；"
              f"增长 {[f'{g:.0%}' for g in g5]} → 衰减至 {s['g_t']:.1%}；增量回报 {s['roic']:.0%}/{s['roic_fade']:.0%}，永续 RONIC {s['ronic']:.0%}")
        for (year, g, rr, nopat, oe, t) in d["rows"]:
            print(f"   {year}: g {g:5.1%} 再投资率 {rr:5.1%} NOPAT {nopat:6.2f} 所有者收益 {oe:6.2f}")
    d = dcf(SCEN["base"], detail=True)
    r = COE
    pv_h2 = H2_OE / (1 + r) ** (2027.0 - T0)
    pv_exp = sum(oe / (1 + r) ** t for (y, g, rr, n, oe, t) in d["rows"][:5])
    pv_fade = sum(oe / (1 + r) ** t for (y, g, rr, n, oe, t) in d["rows"][5:])
    print(f"基准分解（每股）：2026H2 {pv_h2 / SHARES:.2f} + 2027–31 {pv_exp / SHARES:.2f} + 2032–36 {pv_fade / SHARES:.2f}"
          f" + 终值 {d['pv_tv'] / SHARES:.2f} + 净现金与非经营 {(NET_CASH_ADJ + NONOP) / SHARES:.2f} = {d['v']:.2f}")
    ev_ = PRICE * SHARES - NET_CASH_ADJ - NONOP
    print(f"现价 EV / 基准正常化经营 NOPAT = {ev_ / normalize(SCEN['base'])['nopat']:.1f}×；"
          f"基准 10 年 NOPAT 复合增速 {(d['rows'][-1][3] / d['n0']) ** 0.1 - 1:.1%}；"
          f"牛市 {(dcf(SCEN['bull'], detail=True)['rows'][-1][3] / normalize(SCEN['bull'])['nopat']) ** 0.1 - 1:.1%}")
    vw = weighted()
    pv_ratio = PRICE / vw
    print(f"加权 V {vw:.2f} 元/股；P/V {pv_ratio:.2f} → {verdict(pv_ratio)}")
    print(f"无回购专户股份，剔除口径 V 相同；受限资金与经营备付不扣时加权 V {vw + (RESTRICTED + OP_RESERVE) / SHARES:.2f}")

    print("\n== 股权成本敏感性 ==")
    for r in (0.08, 0.09, 0.10):
        print(f"r={r:.0%}: 熊 {dcf(SCEN['bear'], r):.2f} 基 {dcf(SCEN['base'], r):.2f} 牛 {dcf(SCEN['bull'], r):.2f}"
              f" 加权 {weighted(r):.2f}，P/V {PRICE / weighted(r):.2f}")

    irr = solve(lambda r: dcf(SCEN["base"], r), 0.035, 0.20, PRICE)
    print(f"\n现价隐含回报（基准情景现金流含终值与净现金）：{irr:.2%}")

    # 反向 DCF ①：10 年恒定 NOPAT 增速（再投资率 = g/25%），之后 2.5% 永续（RONIC 15%）
    def dcf_const(g, r=COE):
        n0 = normalize(SCEN["base"])["nopat"]
        pv, nopat = H2_OE / (1 + r) ** (2027.0 - T0), n0
        for i in range(10):
            nopat *= 1 + g
            pv += nopat * (1 - g / 0.25) / (1 + r) ** (2027 + i + 0.5 - T0)
        tv = nopat * 1.025 * (1 - 0.025 / 0.15) / (r - 0.025)
        return (pv + tv / (1 + r) ** (2036.5 - T0) + NET_CASH_ADJ + NONOP) / SHARES
    g10 = solve(dcf_const, 0.0, 0.24, PRICE)
    # 反向 DCF ②：从 2027 年起永续增长（增量回报 25%）
    n0 = normalize(SCEN["base"])["nopat"]
    def v_perp(g):
        oe = n0 * (1 + g) * (1 - g / 0.25)
        return (H2_OE + oe / (COE - g) + NET_CASH_ADJ + NONOP) / SHARES
    gp = solve(v_perp, 0.0, 0.085, PRICE)
    print(f"反向 DCF：10 年 NOPAT 年增 {g10:.1%}（再投资率 {g10 / 0.25:.0%}）后 2.5% 永续；或自 2027 年永续增长 {gp:.2%}（增量回报 25%）")

    print("\n== 交叉验证 ==")
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NONOP
    print(f"市值 {mcap:.1f}；EV（扣经调整净现金）{ev:.1f}；EV/TTM 核心经营利润 {ev / CORE_TTM:.1f}×，EV/2026E {ev / CORE_2026E:.1f}×")
    print(f"PE：TTM 归母 27.41 → {mcap / 27.41:.1f}×；基准正常化归母 {normalize(SCEN['base'])['parent_np']:.2f} → {mcap / normalize(SCEN['base'])['parent_np']:.1f}×；"
          f"基准 V 对应 {vals['base'] * SHARES / normalize(SCEN['base'])['parent_np']:.1f}×")
    print(f"PB {mcap / 179.1255:.2f}×；近 12 个月每股分红 1.16 元，股息率 {1.16 / PRICE:.2%}；无回购")

    print("\n== 证伪条件触发后的 V ==")
    fz = {
        "F1 2026 年报核心经营利润 ≥ 37 亿且毛利率 ≥ 40.5%": dict(weights={"bear": 0.15, "base": 0.45, "bull": 0.40}, n0_mult=1.05),
        "F2 2026Q3 单季营收 < 28.8 亿或单季毛利率 < 37.0%": dict(weights={"bear": 0.40, "base": 0.45, "bull": 0.15}, n0_mult=0.95),
        "F3 2027H1 挖机销量同比 ≤ −15% 且公司营收同比为负": dict(weights={"bear": 0.50, "base": 0.40, "bull": 0.10}),
        "F4 实控人案移送起诉或公司涉案受罚": dict(weights={"bear": 0.35, "base": 0.50, "bull": 0.15}, haircut=0.90),
        "F5 线性驱动年收入 ≥ 15 亿且毛利率 ≥ 30%": dict(weights={"bear": 0.10, "base": 0.45, "bull": 0.45}, g_add=0.02),
    }
    for name, kw in fz.items():
        hc = kw.pop("haircut", 1.0)
        v = weighted(**kw) * hc
        print(f"{name}: V {v:.2f}，P/V {PRICE / v:.2f}")

    print("\n== V 不变时各档价格 ==")
    print(f"≤ {0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}–{0.90 * vw:.2f} 温和低估；{0.90 * vw:.2f}–{1.10 * vw:.2f} 大致合理；> {1.10 * vw:.2f} 偏贵")


if __name__ == "__main__":
    main()
