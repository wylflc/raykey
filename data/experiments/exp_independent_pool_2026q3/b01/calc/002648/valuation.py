# -*- coding: utf-8 -*-
"""卫星化学（002648）OI-291 独立估值：归母所有者收益 DCF，熊／基准／牛三情景概率加权。

运行：python3 valuation.py
单位：金额亿元，每股价值元/股。价格日 2026-10-19，最新定期报告 2026 年三季报（2026-10-17 披露）。
输入全部写在本脚本内，出处见 ../../companies/002648_卫星化学.md 的「来源」一节与各行注释。
"""

PRICE = 25.41
SHARES = 33.6865          # 亿股，行情口径总股本（= 2026-09-30 资产负债表股本）
COE = 0.09
T_Q4 = 0.2                # 2026Q4 现金流按季末计，距价格日约 0.2 年
T_FIRST = 0.7             # 2027 年现金流按年中计，距价格日约 0.7 年；之后逐年 +1
YEARS = [2027, 2028, 2029, 2030, 2031]

# ---------------- 经调整净现金（2026-09-30，三季报第 9-12、18 页） ----------------
CASH = 142.15             # 货币资金
TRADING_FA = 9.12         # 交易性金融资产（结构性存款等）
CD_NONCURRENT = 8.98      # 其他非流动资产 9.01 中的可转让大额存单（三季报第 4 页；构成见 2026H1 第 128 页）
NCA_DUE_1Y = 0.70         # 一年内到期的非流动资产（存单）
DERIV_NET = 1.07 - 0.66   # 衍生金融资产 − 衍生金融负债
RESTRICTED = 142.15 - 128.12   # 货币资金 − 期末现金及现金等价物（三季报第 18 页），全部按受限扣除
PLEDGED_TD = 10.20        # 其中质押定期存款 10.2 亿（2025 年报第 103 页、2026H1 第 107 页），对应白银租借/票据负债已全额扣除，故加回
OP_BUFFER = 20.0          # 经营备付（约两周付现成本）
BANK_LOANS = 17.46        # 长期借款；一年内到期部分按现金流推算≈0（年初 58.2 + 借 9.7 − 还 50.4 ≈ 17.5）
NOTES_FIN = 51.25         # 应付票据，票据贴现融资（2026H1 第 142 页：贴现所得计入筹资流入）
SILVER = (30.30 - 1.00) + 1.92  # 其他流动负债中的白银租借合约（扣待转销项税约 1.0）+ 其他非流动负债（长期租借合约）
LEASE_TOTAL = 185.67 + 17.89    # 租赁负债 + 一年内到期非流动负债（几乎全为租赁）：船舶租赁成本已在净利润中，只列示不扣

NET_CASH_ADJ = (CASH + TRADING_FA + CD_NONCURRENT + NCA_DUE_1Y + DERIV_NET
                - RESTRICTED + PLEDGED_TD - OP_BUFFER - BANK_LOANS - NOTES_FIN - SILVER)
NON_OPERATING = 0.0       # 长期股权投资 23.08（Orbit 乙烷码头等）收益已含在归母净利中，不另加

# ---------------- 三情景 ----------------
# oe0：2026 年正常化归母净利（=所有者收益，维护性资本开支≈非租赁折旧摊销；租赁成本已在净利中）
# q4：2026Q4 预计归母净利；q4_capex：Q4 在建项目投入；excess27：2027 年高于正常化水平的战时超额利润
# g：2027-2031 所有者收益增速；rr：再投资率；gT/roicT：终值增长与终值增量回报
SCEN = {
    "bear": dict(p=0.25, oe0=46.0, q4=20.0, q4_capex=7.0, excess27=5.0,
                 g=[0.010, 0.025, 0.020, 0.015, 0.015], rr=[0.45, 0.40, 0.35, 0.25, 0.20],
                 gT=0.010, roicT=0.07),
    "base": dict(p=0.50, oe0=68.0, q4=24.0, q4_capex=7.0, excess27=18.0,
                 g=[0.020, 0.050, 0.040, 0.030, 0.025], rr=[0.40, 0.35, 0.30, 0.25, 0.22],
                 gT=0.020, roicT=0.10),
    "bull": dict(p=0.25, oe0=90.0, q4=27.0, q4_capex=7.0, excess27=25.0,
                 g=[0.040, 0.070, 0.070, 0.050, 0.040], rr=[0.45, 0.45, 0.40, 0.35, 0.30],
                 gT=0.025, roicT=0.12),
}


def path(s):
    """返回逐年 (年份, 所有者收益, 超额, 股东可得现金) 与终值首年现金。"""
    oe, rows = s["oe0"], []
    for i, y in enumerate(YEARS):
        oe *= 1 + s["g"][i]
        ex = s["excess27"] if y == 2027 else 0.0
        rows.append((y, oe, ex, oe * (1 - s["rr"][i]) + ex))
    fcf_t1 = oe * (1 + s["gT"]) * (1 - s["gT"] / s["roicT"])
    return rows, fcf_t1


def value(s, k=COE, net_cash=None):
    nc = NET_CASH_ADJ + NON_OPERATING if net_cash is None else net_cash
    rows, fcf_t1 = path(s)
    pv_q4 = (s["q4"] - s["q4_capex"]) / (1 + k) ** T_Q4
    pv_exp = sum(f / (1 + k) ** (T_FIRST + i) for i, (_, _, _, f) in enumerate(rows))
    pv_tv = fcf_t1 / (k - s["gT"]) / (1 + k) ** (T_FIRST + len(YEARS) - 1)
    eq = pv_q4 + pv_exp + pv_tv + nc
    return eq / SHARES, dict(pv_q4=pv_q4, pv_exp=pv_exp, pv_tv=pv_tv, nc=nc,
                             tv_share=pv_tv / (pv_q4 + pv_exp + pv_tv))


def weighted(k=COE, scen=SCEN):
    return sum(s["p"] * value(s, k)[0] for s in scen.values())


def solve(f, lo, hi, target, n=200):
    """二分求 f(x)=target，f 单调。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s=SCEN["base"]):
    return solve(lambda k: value(s, k)[0], 0.03, 0.40, PRICE)


def reverse_perpetual_growth(base=SCEN["base"], roic=0.10, k=COE):
    """扣除净现金、2026Q4 与 2027 超额后，现价对正常化所有者收益（2027 起 = oe0×(1+g)）隐含的永续增速，再投资率 = g/ROIC。"""
    ops = (PRICE * SHARES - NET_CASH_ADJ
           - (base["q4"] - base["q4_capex"]) / (1 + k) ** T_Q4
           - base["excess27"] / (1 + k) ** T_FIRST)

    def v(g):  # Gordon 值在首笔现金前一期（t = T_FIRST − 1），折到价格日
        return base["oe0"] * (1 + g) * (1 - g / roic) / (k - g) * (1 + k) ** (1 - T_FIRST)
    return solve(v, -0.05, 0.085, ops), ops


def reverse_from_ttm(oe_ttm=110.76, gT=0.02, roicT=0.10, k=COE):
    """以 TTM 扣非 110.76 亿为起点、不再投资，求现价隐含的 2027-2036 年均变化率（之后按终值 2%）。"""
    def v(g):
        oe, pv = oe_ttm, 0.0
        for i in range(10):
            oe *= 1 + g
            pv += oe / (1 + k) ** (T_FIRST + i)
        tv = oe * (1 + gT) * (1 - gT / roicT) / (k - gT) / (1 + k) ** (T_FIRST + 9)
        return (pv + tv + NET_CASH_ADJ) / SHARES
    return solve(v, -0.30, 0.08, PRICE)


def reverse_oe0(base=SCEN["base"]):
    """沿用基准增长路径与近端超额，求现价隐含的 2026 正常化归母净利。"""
    def v(x):
        s = dict(base, oe0=x)
        return value(s)[0]
    return solve(v, 10.0, 200.0, PRICE)


def falsifier_values():
    b, bear = SCEN["base"], SCEN["bear"]
    out = {}
    out["F1 价差塌缩→熊"] = value(bear)[0]
    out["F2 美国乙烷断供≥60天"] = value(dict(bear, excess27=-35.0))[0]
    out["F3 大额扩张且不提分红"] = value(dict(b, rr=[r + 0.15 for r in b["rr"][:4]] + [b["rr"][4]], roicT=0.08))[0]
    out["F4 战时超额提前消退"] = value(dict(b, q4=15.0, excess27=0.0))[0]
    out["F5 高油价退潮后盈利仍强→牛"] = value(SCEN["bull"])[0]
    return out


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print("== 经调整净现金（2026-09-30）==")
    gross = CASH + TRADING_FA + CD_NONCURRENT + NCA_DUE_1Y + DERIV_NET
    print(f"现金类合计 {gross:.2f}；扣受限 {RESTRICTED:.2f}，加回质押定存 {PLEDGED_TD:.2f}；扣经营备付 {OP_BUFFER:.1f}")
    print(f"扣银行借款 {BANK_LOANS:.2f}、票据融资 {NOTES_FIN:.2f}、白银租借 {SILVER:.2f}")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} 亿（{NET_CASH_ADJ / SHARES:.2f} 元/股）；"
          f"租赁负债 {LEASE_TOTAL:.2f} 只列示，含租赁口径净负债 {NET_CASH_ADJ - LEASE_TOTAL:.2f}")
    print()
    print("== 三情景（股权成本 9%）==")
    for name, s in SCEN.items():
        v, d = value(s)
        rows, f1 = path(s)
        print(f"{name}: p={s['p']:.2f} 正常化归母 {s['oe0']:.0f} 亿  V={v:.2f}  "
              f"V@8%={value(s, 0.08)[0]:.2f}  V@10%={value(s, 0.10)[0]:.2f}  终值占比 {d['tv_share']:.1%}")
        print("   逐年所有者收益/股东现金:",
              "; ".join(f"{y} {oe:.1f}/{fcf:.1f}" for y, oe, _, fcf in rows),
              f"; 终值首年现金 {f1:.1f}")
        print(f"   PV: 2026Q4 {d['pv_q4']:.1f} + 2027-31 {d['pv_exp']:.1f} + 终值 {d['pv_tv']:.1f} + 净现金 {d['nc']:.1f}")
    vw = weighted()
    pv = PRICE / vw
    print()
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.3f}（{verdict(pv)}）")
    print(f"加权 V @8% = {weighted(0.08):.2f}；@10% = {weighted(0.10):.2f}")
    print(f"基准情景现价隐含回报（IRR）= {implied_irr():.2%}；参考：熊情景 {implied_irr(SCEN['bear']):.2%}，"
          f"牛情景 {implied_irr(SCEN['bull']):.2%}")
    g_imp, ops = reverse_perpetual_growth()
    print(f"反向 DCF：扣净现金与近端超额后经营价值 {ops:.1f} 亿，对正常化 68 亿隐含永续增速 {g_imp:.2%}（增量回报 10%）；"
          f"沿用基准路径时隐含 2026 正常化归母 {reverse_oe0():.1f} 亿；"
          f"以 TTM 扣非 110.76 亿为起点则隐含 2027-2036 年均 {reverse_from_ttm():.2%}")
    print(f"进入各档的价格（V 不变）：≤{0.75 * vw:.2f} 明显低估；≤{0.90 * vw:.2f} 温和低估；"
          f"≤{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")
    print()
    print("== 证伪触发后的独立 V ==")
    for k_, v in falsifier_values().items():
        print(f"{k_}: {v:.2f}")
    print()
    norm_w = sum(s["p"] * s["oe0"] for s in SCEN.values())
    mcap = PRICE * SHARES
    print("== 交叉验证 ==")
    print(f"市值 {mcap:.2f} 亿；PE(TTM 归母 106.14) {mcap / 106.14:.2f}；PB(归母权益 407.75) {mcap / 407.75:.2f}")
    print(f"正常化归母概率加权 {norm_w:.1f} 亿；(市值−净现金)/正常化归母 = {(mcap - NET_CASH_ADJ) / norm_w:.1f} 倍")
    ev = mcap - NET_CASH_ADJ + LEASE_TOTAL
    ebit_norm = 68.0 / (1 - 0.13) + 7.3        # 正常化税前 + 正常化净利息（租赁利息约 8、银行与票据约 1.6、利息收入约 −2.3）
    ebit_ttm = (60.66 - 43.61 + 103.94) + (8.74 - 6.78 + 5.74)  # TTM 利润总额 + TTM 财务费用
    print(f"EV(含租赁) {ev:.1f} 亿；EV/EBIT 正常化 {ev / ebit_norm:.1f}×（EBIT≈{ebit_norm:.1f}），TTM {ev / ebit_ttm:.1f}×（EBIT≈{ebit_ttm:.1f}）")
    print(f"股息率 {0.50 / PRICE:.2%}；2025 年回购 2.18 亿占市值 {2.18 / mcap:.2%}")
    for name, s in SCEN.items():
        rows, _ = path(s)
        reinv = s["q4_capex"] + sum(oe * r for (_, oe, _, _), r in zip(rows[:4], s["rr"][:4]))
        print(f"{name}：2026Q4-2030 累计再投资 {reinv:.1f} 亿，2031 所有者收益较 2026 正常化增加 {rows[-1][1] - s['oe0']:.1f} 亿，"
              f"增量回报 ≈ {(rows[-1][1] - s['oe0']) / reinv:.1%}；2027-2031 平均再投资率 {sum(s['rr']) / 5:.1%}；"
              f"2027 归母合计 {rows[0][1] + rows[0][2]:.1f} 亿；2026 全年归母 {90.59 + s['q4']:.1f} 亿")
