#!/usr/bin/env python3
"""天孚通信（300394）独立估值（OI-291 b17，价格日 2026-10-21）。

方法：归母所有者收益 DCF（2026H2 + 2027-2036 显式期 + 2.5% 终值），熊／基准／牛三情景概率加权；
反向 DCF、现价隐含回报、股权成本 8%/10% 敏感性、证伪情景重新加权、H 股摊薄对照、周期性毛利溢价拆分。
输入全部写在脚本内，运行 `python3 valuation.py` 打印正文与 json 的全部数字。
单位：金额亿元，股本亿股，每股元。来源页码见 companies/300394_天孚通信.md。
"""

# ---------------------------------------------------------------- 市场与股本
PRICE = 214.98                 # 2026-10-21 收盘（腾讯日线）
SHARES = 10.90825093           # 总股本（2025 年度 10 转 4 后，dividend_20260605 第 3 页；无回购专户股份）
MKT_CAP = PRICE * SHARES
COE, G_TERM = 0.09, 0.025
T0_2027 = 0.69                 # 2026-10-21 至 2027 年年中（年中折现）
T_TV = 10.19                   # 至 2036-12-31
T_H2 = 0.0                     # 2026H2 所有者收益视同当期

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，2026H1_report 第 56-58、100、129 页）
CASH = 29.05778869             # 货币资金
TFA = 2.72166570               # 交易性金融资产（非固定收益理财）
RESTRICTED = 0.51701573        # 保函保证金 5,170 万元 + 冻结 1,573 元
DIV_SEPT = 5.45412547          # 2026 半年度现金分红，2026-09-17 除息支付（dividend_20260909）
OP_RESERVE = 3.0               # 经营备付：约 2026E 营收 5%
DEBT = 0.0                     # 无银行借款
LEASE = 0.03648173             # 租赁负债（含一年内到期），净利润已扣租赁成本，只列示不扣
NONOP = 0.11917615             # 长期股权投资（联营、合资，含新加坡 SuperX 合资 70 万新币）
NET_CASH_ADJ = CASH + TFA - RESTRICTED - DIV_SEPT - OP_RESERVE - DEBT
INT_AT = round(NET_CASH_ADJ * 0.031 * 0.85, 2)   # 超额现金税后利息：计入正常化净利，不计入 DCF 经营现金流（现金另加）

# ---------------------------------------------------------------- 2025 与 2026H1 报表口径
REV_2025 = 51.6343247
NP_2025, NP_TTM, EQUITY = 20.17266034, 23.22, 62.48576374
REV_H1 = 28.27938748
NP_H1 = 12.04285104
NONREC_H1 = 0.18021623          # 非经常性损益合计（2026H1_report 第 11 页）
FX_LOSS_H1 = 0.85846500         # 汇兑损失（2026H1_report 第 22 页）
TAX_EFF = 0.1255                # 2026H1 实际税率 1.7287/13.7728
REC_H1 = NP_H1 - NONREC_H1 + FX_LOSS_H1 * (1 - TAX_EFF)   # 2026H1 经常性归母净利（剔汇兑、非经常）
REC_H1_OPS = REC_H1 - INT_AT / 2

# ---------------------------------------------------------------- 三情景
# rev26：2026 全年营收；rec26：2026 全年经常性归母净利（含利息，剔汇兑与非经常）
# g：2027-2036 营收增速；m：2027-2036 经营净利率（不含超额现金利息）
# k_up：每增 1 元营收所需新增资本（固定资产净增 + 营运资本）；营收下降时只回收营运资本 k_down
# ronic：终值期增量资本回报，终值再投资率 = G_TERM / ronic
SCEN = {
    "bear": dict(p=0.25, rev26=60.0, rec26=25.6,
                 g=[0.10, -0.15, 0.05, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03, 0.025],
                 m=[0.375, 0.32, 0.31, 0.305, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30],
                 k_up=0.45, k_down=0.20, ronic=0.15,
                 desc="2027 年 AI 光互连扩产后进入消化期，2028 年营收 -15%；有源光引擎因硅光/CPO 与 200G EML "
                      "供给受限持续丢份额，无源被国内同业扩产与美方含量规则压价；经营净利率由 41.7% 降至 30%（2013-2025 年最低 29.7%）；"
                      "终值 RONIC 15%"),
    "base": dict(p=0.50, rev26=62.5, rec26=27.0,
                 g=[0.41, 0.24, 0.14, 0.08, 0.05, 0.04, 0.035, 0.03, 0.03, 0.025],
                 m=[0.395, 0.385, 0.37, 0.36, 0.35, 0.345, 0.34, 0.34, 0.34, 0.34],
                 k_up=0.40, k_down=0.20, ronic=0.20,
                 desc="2027 年有源随 200G EML 供给恢复 + 1.6T/CPO 放量，营收 +41%（无源 +30%、有源 +55%），2028 年 +24%，此后随行业景气回落降速；"
                      "无源维持全球 FAU 第一与约 11% 光器件份额，有源份额低于 2025 年；经营净利率由 42% 渐降至 34%（2027 年起股份支付 1.8 亿、有源占比回升）；终值 RONIC 20%"),
    "bull": dict(p=0.25, rev26=65.0, rec26=28.2,
                 g=[0.62, 0.50, 0.32, 0.18, 0.10, 0.07, 0.06, 0.05, 0.04, 0.03],
                 m=[0.42, 0.415, 0.41, 0.40, 0.39, 0.385, 0.38, 0.375, 0.37, 0.37],
                 k_up=0.40, k_down=0.20, ronic=0.25,
                 desc="CPO/NPO 与 scale-up 光互连 2027-2029 年放量，FAU/ELS/1.6T 光引擎份额恢复并扩大，"
                      "2027 年归母约 45 亿（达到股权激励触发值 43.5 亿），2029 年约 86 亿（仍低于触发值 130 亿）；经营净利率 2030 年后仍有 37%；终值 RONIC 25%"),
}
YEARS = list(range(2027, 2037))


def build(s):
    rev, np_ops, reinv, oe = [], [], [], []
    prev = s["rev26"]
    for g, m in zip(s["g"], s["m"]):
        r = prev * (1 + g)
        d = r - prev
        ri = s["k_up"] * d if d > 0 else s["k_down"] * d
        n = r * m
        rev.append(r); np_ops.append(n); reinv.append(ri); oe.append(n - ri)
        prev = r
    ops26 = s["rec26"] - INT_AT
    h2_ops = ops26 - REC_H1_OPS
    h2_reinv = s["k_up"] * (s["rev26"] - REV_2025) * 0.5
    return dict(rev=rev, np=np_ops, reinv=reinv, oe=oe, ops26=ops26,
                h2_ops=h2_ops, h2_reinv=h2_reinv, h2_oe=h2_ops - h2_reinv)


def value(s, r=COE, g=G_TERM, detail=False):
    b = build(s)
    pv_h2 = b["h2_oe"] / (1 + r) ** T_H2
    pv_exp = sum(cf / (1 + r) ** (T0_2027 + i) for i, cf in enumerate(b["oe"]))
    oe_tv = b["np"][-1] * (1 + g) * (1 - g / s["ronic"])
    tv = oe_tv / (r - g)
    pv_tv = tv / (1 + r) ** T_TV
    eq = pv_h2 + pv_exp + pv_tv + NET_CASH_ADJ + NONOP
    v = eq / SHARES
    if detail:
        return v, dict(b=b, pv_h2=pv_h2, pv_exp=pv_exp, tv=tv, pv_tv=pv_tv, eq=eq, oe_tv=oe_tv)
    return v


def weighted(weights=None, r=COE):
    w = weights or {k: SCEN[k]["p"] for k in SCEN}
    return sum(w[k] * value(SCEN[k], r) for k in SCEN)


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


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def reverse_dcf_10y():
    """现价隐含：2027-2036 经营净利按同一增速 g 增长（再投资 = 净利 × g / 50% 增量回报），之后 2.5%、RONIC 20%。"""
    base_np = SCEN["base"]["rec26"] - INT_AT

    def eq(gr):
        pv, n = 0.0, base_np
        for i in range(10):
            n *= (1 + gr)
            pv += n * (1 - gr / 0.50) / (1 + COE) ** (T0_2027 + i)
        tv = n * (1 + G_TERM) * (1 - G_TERM / 0.20) / (COE - G_TERM)
        pv += tv / (1 + COE) ** T_TV
        return pv + NET_CASH_ADJ + NONOP
    return solve(eq, 0.0, 0.49, MKT_CAP)


def implied_irr(key="base"):
    return solve(lambda r: value(SCEN[key], r) * SHARES, 0.03, 0.30, MKT_CAP)


def main():
    print("=== 天孚通信 300394 独立估值（价格日 2026-10-21）===")
    print(f"现价 {PRICE:.2f} 元 × 总股本 {SHARES:.4f} 亿股 = 市值 {MKT_CAP:.1f} 亿元")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} = 货币资金 {CASH:.2f} + 交易性金融资产 {TFA:.2f} - 受限 {RESTRICTED:.2f} "
          f"- 9 月已付中期分红 {DIV_SEPT:.2f} - 经营备付 {OP_RESERVE:.1f} - 有息负债 {DEBT:.1f}；租赁负债 {LEASE:.3f} 只列示")
    print(f"非经营资产 {NONOP:.2f}；超额现金税后利息 {INT_AT:.2f}/年（计入正常化净利，DCF 经营流不含）")
    print(f"2026H1 经常性归母 {REC_H1:.2f} = {NP_H1:.2f} - 非经常 {NONREC_H1:.2f} + 汇兑损失税后 {FX_LOSS_H1*(1-TAX_EFF):.2f}")

    # 周期性毛利溢价（2026E 毛利率 vs 2023-2025 分部毛利率中枢按 2026 结构加权）
    gm_mid = 0.53 * 0.638 + 0.45 * 0.456 + 0.02 * 0.70
    gm_26 = 0.602
    prem = (gm_26 - gm_mid) * SCEN["base"]["rev26"] * (1 - 0.13)
    norm = {"bear": SCEN["bear"]["rec26"] - prem, "base": SCEN["base"]["rec26"] - prem / 2, "bull": SCEN["bull"]["rec26"]}
    print(f"\n毛利率中枢 {gm_mid:.1%}（无源 63.8%、有源 45.6%、其他 70% 按 53/45/2 加权）vs 2026E {gm_26:.1%}："
          f"周期性毛利溢价税后 {prem:.2f} 亿")
    print("2026 经常性归母（剔汇兑、非经常，含利息）：" + "，".join(f"{k} {SCEN[k]['rec26']:.1f}" for k in SCEN))
    print("2026 正常化归母（熊扣全部溢价、基准扣一半、牛不扣）：" + "，".join(f"{k} {norm[k]:.1f}" for k in norm))

    res = {}
    for k, s in SCEN.items():
        v, d = value(s, detail=True)
        res[k] = (v, d)
        b = d["b"]
        print(f"\n--- {k}（p={s['p']:.2f}）V = {v:.2f} 元 ---  {s['desc']}")
        print(f"2026：营收 {s['rev26']:.1f}，经常性归母 {s['rec26']:.1f}，经营净利 {b['ops26']:.2f}，"
              f"H2 经营净利 {b['h2_ops']:.2f} - 再投资 {b['h2_reinv']:.2f} = H2 所有者收益 {b['h2_oe']:.2f}")
        print("年份  营收    增速    经营净利  净利率  再投资   所有者收益")
        for i, y in enumerate(YEARS):
            print(f"{y}  {b['rev'][i]:7.1f}  {s['g'][i]:+6.1%}  {b['np'][i]:7.1f}  {s['m'][i]:6.1%}  {b['reinv'][i]:6.1f}  {b['oe'][i]:7.1f}")
        print(f"PV(2026H2) {d['pv_h2']:.1f} + PV(2027-36) {d['pv_exp']:.1f} + PV(终值) {d['pv_tv']:.1f}"
              f"（终值 {d['tv']:.0f}，2037 所有者收益 {d['oe_tv']:.1f}，再投资率 {G_TERM/s['ronic']:.1%}）"
              f" + 净现金 {NET_CASH_ADJ:.1f} + 非经营 {NONOP:.2f} = {d['eq']:.0f} 亿；终值占比 {d['pv_tv']/d['eq']:.0%}")
        print(f"  8%: {value(s, 0.08):.2f}   10%: {value(s, 0.10):.2f}")

    vw = weighted()
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元；P/V = {pv:.2f}（{tier(pv)}）")
    print(f"股权成本 8%：V = {weighted(r=0.08):.2f}（P/V {PRICE/weighted(r=0.08):.2f}）；10%：V = {weighted(r=0.10):.2f}（P/V {PRICE/weighted(r=0.10):.2f}）")
    print(f"V 不变时各档价格：明显低估 ≤ {0.75*vw:.1f}；温和低估 {0.75*vw:.1f}-{0.90*vw:.1f}；大致合理 {0.90*vw:.1f}-{1.10*vw:.1f}；偏贵 > {1.10*vw:.1f}")

    irr = implied_irr("base")
    irr_bull = implied_irr("bull")
    print(f"\n现价隐含回报（基准情景现金流）：{irr:.2%}；按牛市情景现金流：{irr_bull:.2%}")
    g10 = reverse_dcf_10y()
    b = build(SCEN["base"])
    oe27 = b["oe"][0]
    g_perp = COE - oe27 / (MKT_CAP - NET_CASH_ADJ - NONOP)
    print(f"反向 DCF：2027-2036 经营净利年增 {g10:.1%}（2036 年约 {(SCEN['base']['rec26']-INT_AT)*(1+g10)**10:.0f} 亿，再投资按 50% 增量回报）；"
          f"或以 2027 基准所有者收益 {oe27:.1f} 亿起永续增长 {g_perp:.1%}")
    print(f"现价 / 2026 经常性归母 = {MKT_CAP/SCEN['base']['rec26']:.0f}×；/ TTM 归母 = {MKT_CAP/NP_TTM:.0f}×；/ 归母权益 = {MKT_CAP/EQUITY:.1f}×")
    print(f"V / 2026 基准正常化每股 = {vw/(norm['base']/SHARES):.1f}×")

    # 显式期再投资与增量回报（基准 2027-2031）
    bb = build(SCEN["base"])
    rr = sum(bb["reinv"][:5]) / sum(bb["np"][:5])
    inc = (bb["np"][4] - bb["ops26"]) / sum(bb["reinv"][:5])
    oe_g = [bb["oe"][0] / bb["h2_oe"] / 2 - 1] + [bb["oe"][i] / bb["oe"][i - 1] - 1 for i in range(1, 5)]
    np_g = [bb["np"][0] / bb["ops26"] - 1] + [bb["np"][i] / bb["np"][i - 1] - 1 for i in range(1, 5)]
    print(f"\n基准 2027-2031：再投资率 {rr:.1%}，增量回报 {inc:.0%}；经营净利增速 " + "，".join(f"{x:.1%}" for x in np_g))
    oe26_full = bb['ops26'] - SCEN['base']['k_up'] * (SCEN['base']['rev26'] - REV_2025)
    print("基准 2027-2031 所有者收益：" + "，".join(f"{x:.1f}" for x in bb["oe"][:5]) +
          f"（2026 全年口径 {oe26_full:.1f}）")
    oe_path = [oe26_full] + bb["oe"][:5]
    print("基准 2027-2031 所有者收益增速（json growth_path）：" +
          "，".join(f"{oe_path[i] / oe_path[i - 1] - 1:.3f}" for i in range(1, 6)))

    # 证伪情景（重新加权）
    falsifiers = {
        "F1 2026Q3 单季营收 < 15.5 亿或扣非归母 < 6.3 亿（10-29 三季报）": {"bear": 0.45, "base": 0.45, "bull": 0.10},
        "F2 2026 年扣非归母加回汇兑损失 < 25 亿或全年有源营收 < 25.6 亿（2027-04-30 前年报）": {"bear": 0.55, "base": 0.40, "bull": 0.05},
        "F3 2027H1 营收同比 < 15% 或毛利率 < 54%（2027-08-31 前中报）": {"bear": 0.65, "base": 0.30, "bull": 0.05},
        "F4 美方正式发布限制中国产光模块/光器件进入美国的生效规则（含原产地或美国含量门槛，2027-12-31 前）": {"bear": 0.60, "base": 0.35, "bull": 0.05},
        "F5 上行：2027 年扣非归母（不扣股份支付）≥ 43.5 亿（激励触发值，2028-04-30 前）": {"bear": 0.05, "base": 0.45, "bull": 0.50},
    }
    print("\n证伪情景重新加权后的独立 V：")
    for name, w in falsifiers.items():
        print(f"  {name}: V = {weighted(w):.2f}（P/V {PRICE/weighted(w):.2f}）")

    # H 股摊薄对照（未完成，按现有股本估值；以下为假设发行）
    print("\nH 股摊薄对照（未完成，V 按现有股本；假设 H 股发行价折合 A 股价 70%，募资净额 97%）：")
    cases = [("扩大后股本 5%", SHARES * 0.05 / 0.95),
             ("上限：扩大后股本 10%（超额配售前）", SHARES * 0.10 / 0.90),
             ("上限 + 15% 超额配售", SHARES * 0.10 / 0.90 * 1.15)]
    for name, n_h in cases:
        proceeds = n_h * PRICE * 0.70 * 0.97
        v_d = (vw * SHARES + proceeds) / (SHARES + n_h)
        print(f"  {name}：新增 {n_h:.3f} 亿股（占发行后 {n_h/(SHARES+n_h):.1%}），募资净额 {proceeds:.0f} 亿，每股 V {vw:.2f} → {v_d:.2f}（P/V {PRICE/v_d:.2f}）")
    print("  2026 年限制性股票 227.69 万股（授予价 119.5 元，第二类，2027-2029 年归属）：股份支付 2026-2030 年 0.44/1.76/0.86/0.37/0.03 亿，已含在经营净利率内，不另摊薄")

    # 交叉验证
    dps_ttm = 0.70 / 1.4 + 0.50
    ebit_ttm = 23.51934738 + 13.80532835 - 10.31612096 - (0.81248918 + 0.50201858 - 0.32757613) + (0.47523154 + 0.85846500 - 0.06)  # 2025H1 汇兑约 0.06 亿损失（财务费用倒推）
    print(f"\n交叉验证：TTM 每股现金分红（转增调整）{dps_ttm:.2f} 元，股息率 {dps_ttm/PRICE:.2%}；"
          f"拟回购 1-1.5 亿元占市值 {1.0/MKT_CAP:.2%}-{1.5/MKT_CAP:.2%}")
    print(f"EV {MKT_CAP-NET_CASH_ADJ:.0f} 亿 / TTM EBIT（剔利息收入、加回汇兑损失约 {ebit_ttm:.1f}）= {(MKT_CAP-NET_CASH_ADJ)/ebit_ttm:.0f}×")
    print(f"独立 V 对应 2026 基准正常化 PE {vw*SHARES/norm['base']:.0f}×、对应 2027 基准经营净利 PE {vw*SHARES/(bb['np'][0]+INT_AT):.0f}×")


if __name__ == "__main__":
    main()
