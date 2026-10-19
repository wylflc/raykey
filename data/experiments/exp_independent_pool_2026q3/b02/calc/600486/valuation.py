#!/usr/bin/env python3
"""扬农化工（600486）独立估值（OI-291 b02，深度版）。

运行：python3 valuation.py
全部输入写在本文件内；金额单位亿元，每股价值单位元/股。
口径：归母；股权成本基准 9%（敏感性 8%/10%）；价格日 2026-10-19（北京时间）。
方法：分部毛利（原药按「毛利/吨」做概率加权的长期价差正常化，不取现价）
→ 2026 正常化经营 NOPAT → 所有者收益 DCF（再投资率 = 增速 / 增量回报）
+ 经调整净现金 + 非经营资产；三情景概率加权。
"""

# ---------------------------------------------------------------- 快照
PRICE = 51.72                     # 元，2026-10-19 收盘（腾讯日线）
SHARES = 4.04111938               # 亿股，2026-06-30 股本 404,111,938 股（2026H1_report 第 30 页），与行情口径 4.0411 一致
COE = 0.09
T0 = 2026 + 291 / 365             # 2026-10-19 折成年份
YEARS = [2027, 2028, 2029, 2030, 2031]

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，2026H1_report）
CASH = 11.5518                    # 货币资金（第 35、72 页），含存放中化财务 6.0621
TD_1Y_NCA = 6.5470                # 一年内到期的非流动资产＝定期存款（第 88 页）
TD_OCA = 3.5515                   # 其他流动资产中一年内到期的定期存款（第 88 页）
TD_ONCA = 16.0248                 # 其他非流动资产中定期存款（第 103 页）
RESTRICTED = 0.6002               # 票据保证金（第 15 页）
DEBT = 2.0012 + 0.0216 + 0.0123   # 短期借款＋一年内到期租赁＋租赁负债（第 36 页）
DEBT_LIKE = 1.9914 + 1.8505       # 长期应付职工薪酬（第 110 页）＋江苏优士厂区土地恢复原状预计负债（第 111 页）
DIV_DECLARED = 0.24 * SHARES      # 2026 中期 0.24 元/股，8-25 宣派、9-30 发放，未进 6-30 报表
OPER_RESERVE = 6.0                # 经营备付：约 5% 收入／三周付现成本（季节性：四季度经营现金流常为负）
RP_DEPOSIT = 29.90                # 中化财务存款本金（contract_20260825_364307 第 3、6 页；2026H1_report 第 28 页）
NON_OP = 0.0675 + 0.1042          # 其他权益工具投资＋投资性房地产

CASH_ALL = CASH + TD_1Y_NCA + TD_OCA + TD_ONCA
NET_CASH_ADJ = CASH_ALL - RESTRICTED - DEBT - DEBT_LIKE - DIV_DECLARED - OPER_RESERVE

# ---------------------------------------------------------------- 2026 正常化：分部毛利
VOL_API = 120_600                 # 吨，2026E 原药销量＝上半年 61,522（2026H1 经营数据公告）＋下半年 59,080（2025H2 56,808×1.04）
REV_FORM = 14.3                   # 制剂收入 2026E（上半年 11.01，下半年按 2025H2 3.27）
REV_TRADE = 28.2                  # 贸易收入 2026E（上半年 12.74，下半年按 2025H2 15.61 略降）
REV_OTHER, GM_OTHER = 2.9, 0.09
OPEX = 2.30 + 4.40 + 4.20         # 销售＋管理＋研发（2025：2.24/4.53/3.93；2026H1：1.05/1.98/1.89）
SURCHARGE = 0.50                  # 税金及附加
OTHER_INCOME = 0.25               # 经常性其他收益（扣除非经常政府补助）
NONOP = 0.03                      # 营业外与资产处置
NET_INT = 0.85                    # 税前净利息：利息收入约 1.0（存款收益率下行）－利息支出约 0.15
TAX = 0.165                       # 2024/2025 有效税率 14.4%/14.9%，2026H1 17.2%
MINORITY = 0.01

# 下半年实际估计（存根现金流）：三季度 2.45＋四季度 2.30，均不含一次性项目
H2_2026_NI = 2.45 + 2.30
H2_2026_NOPAT = H2_2026_NI - NET_INT / 2 * (1 - TAX)

SCEN = {
    # gp_t：原药毛利（元/吨）。实际：2023 23,069（销量按 73.84 亿/7.65 万元推算）；2024 17,804；2025 17,055；
    # TTM 17,462；2026H1 18,882（旺季）。毛利取东财主营构成（与年报第 16 页一致），销量与均价取年度/半年度经营数据公告
    "bear": dict(p=0.30, gp_t=17_000, gm_form=0.24, gm_trade=0.070, fx=0.20, impair=0.55, extra_opex=0.0,
                 g=[0.03, 0.02, 0.02, 0.02, 0.02], gT=0.015, roic=0.07, cycle=[1, 1, 1, 1, 1], rp_haircut=0.10,
                 text="原药毛利 1.70 万元/吨（≈2025 底部，长期不修复），制剂毛利率 24%，贸易 7%，汇兑拖累 0.2 亿；"
                      "量增 3%→2%，终值 1.5%，增量回报 7%，中化财务存款打九折"),
    "base": dict(p=0.45, gp_t=20_000, gm_form=0.275, gm_trade=0.075, fx=0.0, impair=0.45, extra_opex=0.0,
                 g=[0.05, 0.04, 0.04, 0.035, 0.03], gT=0.025, roic=0.10, cycle=[0.86, 0.94, 0.98, 1, 1], rp_haircut=0.0,
                 text="原药毛利 2.00 万元/吨（2023 与 2024–25 底部的中点，对应均价约 7.1 万元/吨），制剂 27.5%，"
                      "贸易 7.5%；2027–29 修复系数 0.86/0.94/0.98；量增 5%→3%，终值 2.5%，增量回报 10%"),
    "bull": dict(p=0.25, gp_t=23_000, gm_form=0.30, gm_trade=0.080, fx=0.0, impair=0.45, extra_opex=0.30,
                 g=[0.07, 0.06, 0.05, 0.04, 0.04], gT=0.025, roic=0.14, cycle=[0.82, 0.90, 0.96, 1, 1], rp_haircut=0.0,
                 text="原药毛利 2.30 万元/吨（回到 2023 水平），制剂 30%，贸易 8%；修复 0.82/0.90/0.96；"
                      "葫芦岛二期与创制品种带动量增 7%→4%，终值 2.5%，增量回报 14%"),
}


def normalized(s):
    gp = VOL_API * s["gp_t"] / 1e8 + REV_FORM * s["gm_form"] + REV_TRADE * s["gm_trade"] + REV_OTHER * GM_OTHER
    ebit = gp - OPEX - s["extra_opex"] - SURCHARGE + OTHER_INCOME - s["impair"] - NONOP - s["fx"]
    nopat = ebit * (1 - TAX)
    ni = nopat + NET_INT * (1 - TAX) - MINORITY
    return dict(gp=gp, ebit=ebit, nopat=nopat, ni=ni)


def value(s, r=COE, extra=None):
    """返回 (每股价值, 明细)。经营价值＝存根＋2027–2031 所有者收益（年中折现）＋终值；再加经调整净现金与非经营资产。"""
    s = dict(s, **(extra or {}))
    n = normalized(s)
    g, gT, roic = s["g"], s["gT"], s["roic"]
    nxt = g[1:] + [gT]                                   # 第 t 年的再投资支撑第 t+1 年增长
    level, rows, pv = n["nopat"], [], 0.0
    stub = H2_2026_NOPAT * (1 - g[0] / roic)
    pv_stub = stub / (1 + r) ** (2027.0 - T0)
    for i, y in enumerate(YEARS):
        level *= 1 + g[i]
        nopat_t = level * s["cycle"][i]
        rr = nxt[i] / roic
        oe = nopat_t * (1 - rr)
        t = y + 0.5 - T0
        pv += oe / (1 + r) ** t
        rows.append((y, g[i], s["cycle"][i], nopat_t, rr, oe))
    oe_T = level * (1 + gT) * (1 - gT / roic)
    tv = oe_T / (r - gT)
    pv_tv = tv / (1 + r) ** (YEARS[-1] + 0.5 - T0)
    cash = NET_CASH_ADJ - RP_DEPOSIT * s["rp_haircut"]
    eq = pv_stub + pv + pv_tv + cash + NON_OP
    return eq / SHARES, dict(norm=n, rows=rows, pv_stub=pv_stub, pv_oe=pv, pv_tv=pv_tv, cash=cash, eq=eq,
                             tv_share=pv_tv / (pv_stub + pv + pv_tv), rr_T=gT / roic)


def weighted(r=COE, probs=None, extra=None):
    probs = probs or {k: v["p"] for k, v in SCEN.items()}
    vals = {k: value(SCEN[k], r, (extra or {}).get(k))[0] for k in SCEN}
    return sum(probs[k] * vals[k] for k in SCEN), vals


def solve(f, lo, hi, target, n=200):
    """二分：f 单调，求 f(x)=target。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf_10y(nopat0=12.70, rr=0.25, gT=0.025, r=COE):
    """现价隐含：以 TTM 核心经营利润 12.70 亿（TTM 归母；净利息 +0.83 与汇兑损失 -0.83 亿税前大致相抵）为起点，
    再投资率固定 25%（基准终值口径），2027–2036 年所有者收益恒定增速 g，之后 2.5% 永续。"""
    oe0 = nopat0 * (1 - rr)
    def v(gg):
        lvl, pv = oe0, 0.0
        for i in range(10):
            lvl *= 1 + gg
            pv += lvl / (1 + r) ** (2027 + i + 0.5 - T0)
        pv += lvl * (1 + gT) / (r - gT) / (1 + r) ** (2036 + 0.5 - T0)
        return (pv + NET_CASH_ADJ + NON_OP) / SHARES
    return solve(v, -0.05, 0.25, PRICE)


def reverse_perpetual(rr=0.25, r=COE):
    """以基准正常化 NOPAT 为起点、无修复期、再投资率固定 25% 的永续增速。"""
    oe = normalized(SCEN["base"])["nopat"] * (1 - rr)
    def v(gg):
        return (oe * (1 + gg) / (r - gg) / (1 + r) ** (2027.5 - T0) + NET_CASH_ADJ + NON_OP) / SHARES
    return solve(v, -0.08, 0.085, PRICE)


def implied_gp_t():
    """基准情景其余假设不变，现价隐含的原药正常化毛利（元/吨）。"""
    return solve(lambda x: value(SCEN["base"], extra=dict(gp_t=x))[0], 10_000, 30_000, PRICE)


def implied_irr():
    return solve(lambda rr: value(SCEN["base"], rr)[0], 0.03, 0.30, PRICE)


def falsifiers():
    out = []
    # F1：2026 年报原药毛利/吨 < 16,500 元 → 底部加深，熊情景毛利降到 16,500，概率 0.60/0.35/0.05
    v1, _ = weighted(probs=dict(bear=0.60, base=0.35, bull=0.05), extra=dict(bear=dict(gp_t=16_500)))
    out.append(("F1 2026 年报原药毛利/吨 < 16,500 元", "2027-04-30", v1))
    # F2：2027 上半年市场均价功夫菊酯 < 10.0、联苯菊酯 < 12.0、草甘膦 < 2.40 万元/吨 → 纯熊情景
    out.append(("F2 2027H1 功夫<10.0、联苯<12.0、草甘膦<2.40 万元/吨", "2027-07-31", value(SCEN["bear"])[0]))
    # F3：三季报单季归母 < 2.0 亿元（1–9 月 < 9.9 亿）→ 概率 0.40/0.45/0.15
    v3, _ = weighted(probs=dict(bear=0.40, base=0.45, bull=0.15))
    out.append(("F3 2026Q3 单季归母 < 2.0 亿元", "2026-10-31", v3))
    # F4：辽宁优创 2026 年净利 < 0.9 亿元，或二期预算 > 40 亿元且无回报测算 → 增量回报 6%/8%/11%
    v4, _ = weighted(extra=dict(bear=dict(roic=0.06), base=dict(roic=0.08), bull=dict(roic=0.11)))
    out.append(("F4 优创 2026 净利<0.9 亿或二期预算>40 亿无回报测算", "2027-04-30", v4))
    # F5：中化财务存款 > 35 亿元或占现金类 > 90%，且 2026 年分红率 < 30% → 关联存款各情景打八折
    v5, _ = weighted(extra={k: dict(rp_haircut=0.20) for k in SCEN})
    out.append(("F5 中化财务存款>35 亿或占比>90%，且 2026 分红率<30%", "2027-04-30", v5))
    return out


# ---------------------------------------------------------------- TTM（2025H2+2026H1）→ 2026 基准正常化的利润桥
TTM_NI = 12.70                       # 归母：12.86 + 7.898 − 8.059
TTM_NONREC = 0.140 + 0.0229 - 0.0998 # 非经常性损益（2025_annual_report 第 9 页；2026H1_report 第 7 页）
TTM_FX_LOSS = 0.2736 + 0.0373 + 0.5212   # 2025 汇兑损失 0.274；2025H1 汇兑收益 0.037；2026H1 汇兑损失 0.521（税前）
TTM_API_GP = 19.3529 + 11.6163 - 10.3117 # 原药毛利（主营构成）
TTM_API_T = 113_475 + 61_522 - 56_700    # 原药销量（2025 年报第 17 页；2026H1 经营数据；2025H1 按同比 +8.5% 倒推）
TTM_OTHER_GP = (4.4415 + 2.3986 - 3.1245) + (2.0704 + 1.0692 - 1.0521) + (0.2408 + 0.1182 - 0.2455)  # 制剂＋贸易＋其他


def bridge():
    b = normalized(SCEN["base"])
    k = 1 - TAX
    gp_t_ttm = TTM_API_GP * 1e8 / TTM_API_T
    items = [
        ("剔除非经常性损益（一次性）", -TTM_NONREC),
        ("汇兑损失归零（周期/噪声）", TTM_FX_LOSS * k),
        ("原药毛利/吨 {:,.0f}→{:,.0f}（周期）".format(gp_t_ttm, SCEN["base"]["gp_t"]),
         (SCEN["base"]["gp_t"] - gp_t_ttm) * TTM_API_T / 1e8 * k),
        ("原药销量 {:,}→{:,} 吨（结构：优创爬坡）".format(TTM_API_T, VOL_API),
         (VOL_API - TTM_API_T) * SCEN["base"]["gp_t"] / 1e8 * k),
        ("制剂/贸易/其他毛利回到中枢（周期）",
         (REV_FORM * SCEN["base"]["gm_form"] + REV_TRADE * SCEN["base"]["gm_trade"] + REV_OTHER * GM_OTHER - TTM_OTHER_GP) * k),
    ]
    resid = b["ni"] - TTM_NI - sum(v for _, v in items)
    items.append(("费用、减值、税率与净利息差异（结构）", resid))
    return gp_t_ttm, items, b["ni"]


def band(v):
    return dict(明显低估=0.75 * v, 温和低估上沿=0.90 * v, 大致合理上沿=1.10 * v)


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 经调整净现金（亿元）")
    print(f"现金类合计 {CASH_ALL:.2f}（货币资金 {CASH:.2f}＋定期存款 {TD_1Y_NCA + TD_OCA + TD_ONCA:.2f}）")
    print(f"－受限 {RESTRICTED:.2f} －有息负债 {DEBT:.2f} －类债务 {DEBT_LIKE:.2f} －已宣派股利 {DIV_DECLARED:.2f} "
          f"－经营备付 {OPER_RESERVE:.2f} ＝ {NET_CASH_ADJ:.2f}；其中中化财务存款 {RP_DEPOSIT:.2f}（占 {RP_DEPOSIT / CASH_ALL:.0%}）")
    print(f"非经营资产 {NON_OP:.2f}")
    print("\n== 2026 正常化（亿元）")
    for k, s in SCEN.items():
        n = normalized(s)
        print(f"{k:4s} 毛利 {n['gp']:.2f}  EBIT {n['ebit']:.2f}  NOPAT {n['nopat']:.2f}  归母净利(含净利息) {n['ni']:.2f}"
              f"  EPS {n['ni'] / SHARES:.2f}")
    print(f"存根：2026 下半年归母估计 {H2_2026_NI:.2f}，经营 NOPAT {H2_2026_NOPAT:.2f}")
    gp_t_ttm, items, ni_b = bridge()
    print(f"\n== 利润桥：TTM 归母 {TTM_NI:.2f} → 基准正常化 {ni_b:.2f}（税后，亿元）")
    for name, v in items:
        print(f"  {name}: {v:+.2f}")
    print("\n== 三情景（9%）")
    for k, s in SCEN.items():
        v, d = value(s)
        print(f"{k:4s} p={s['p']:.2f}  V={v:.2f} 元/股  经营价值 {d['eq'] - d['cash'] - NON_OP:.1f}  终值占比 {d['tv_share']:.0%}"
              f"  净现金 {d['cash']:.2f}")
        for y, g, c, nopat_t, rr, oe in d["rows"]:
            print(f"     {y} 增速 {g:.1%} 修复 {c:.2f} NOPAT {nopat_t:.2f} 再投资率 {rr:.1%} 所有者收益 {oe:.2f}")
        print(f"     终值增速 {s['gT']:.1%} 终值再投资率 {d['rr_T']:.1%} 增量回报 {s['roic']:.0%}")
    vw, vals = weighted()
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {pv:.3f}（{verdict(pv)}）")
    v8, vals8 = weighted(0.08)
    v10, vals10 = weighted(0.10)
    print(f"股权成本 8%：V = {v8:.2f}（熊 {vals8['bear']:.2f} 基 {vals8['base']:.2f} 牛 {vals8['bull']:.2f}）")
    print(f"股权成本 10%：V = {v10:.2f}（熊 {vals10['bear']:.2f} 基 {vals10['base']:.2f} 牛 {vals10['bull']:.2f}）")
    irr = implied_irr()
    print(f"现价隐含回报（基准现金流）= {irr:.2%}")
    print(f"反向 DCF：自 TTM 12.70 亿起 10 年所有者收益增速 = {reverse_dcf_10y():.2%}（再投资率 25%，之后 2.5%）；"
          f"以基准正常化利润为起点的永续增速 = {reverse_perpetual():.2%}；"
          f"基准路径下现价隐含原药毛利 = {implied_gp_t():,.0f} 元/吨")
    print("\n== 交叉验证")
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NON_OP
    ebit_ttm = 15.121 - 1.192 + 0.368 + 0.832   # TTM 利润总额－利息收入＋利息支出＋汇兑损失
    nb = normalized(SCEN["base"])
    print(f"市值 {mcap:.1f}；EV {ev:.1f}；EV/EBIT(TTM {ebit_ttm:.2f}) {ev / ebit_ttm:.1f}x；EV/基准正常化 EBIT {ev / nb['ebit']:.1f}x")
    print(f"PE(TTM 12.70) {mcap / 12.70:.1f}x；PE(基准正常化 {nb['ni']:.2f}) {mcap / nb['ni']:.1f}x；PB {mcap / 119.60:.2f}x；"
          f"股息率(近 12 月 0.954 元) {0.954 / PRICE:.2%}")
    b = band(vw)
    print("\nV 不变时分档价格：明显低估 ≤ {:.2f}；温和低估 {:.2f}–{:.2f}；大致合理 {:.2f}–{:.2f}；偏贵 > {:.2f}".format(
        b["明显低估"], b["明显低估"], b["温和低估上沿"], b["温和低估上沿"], b["大致合理上沿"], b["大致合理上沿"]))
    print("\n== 证伪条件触发后的 V")
    for name, dl, v in falsifiers():
        print(f"{name}（{dl}）→ V = {v:.2f}")
    vu, _ = weighted(probs=dict(bear=0.15, base=0.45, bull=0.40))
    print(f"反向：2027H1 功夫>14、联苯>16、草甘膦>3.2 万元/吨 → 概率 0.15/0.45/0.40，V = {vu:.2f}")


if __name__ == "__main__":
    main()
