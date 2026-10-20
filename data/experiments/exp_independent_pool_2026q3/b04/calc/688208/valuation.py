"""道通科技（688208）独立估值：所有者收益 DCF（OI-291 b04，价格日 2026-10-19）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在本脚本内，出处见正文「来源」与 688208.json 的 spot_checks。

口径要点（framework.md「三法互校」第 2、3 条）
- 经营股权价值 = 经营所有者收益现值 + 超额现金 + 非经营资产。
- 主口径「转债逐情景取低」：每个情景分别算两种每股价值，取较低者。
  · 债务：全额扣除道通转债债底现值（2027 年 1.8% 票息 + 2028-07 按面值 115% 赎回，4% 折现），除以总股本；
  · 全部转股：股本加转股股数 12.7967 ÷ 20.99 = 0.6097 亿股，不扣转债。
  可转债不计入经调整净现金，也不参与有杠杆口径的判断与滚动。剔除转债后经调整净现金
  = 超额现金 − 租赁负债 = +9.28 亿，为正，转债以外的有息负债（租赁）按无杠杆口径全额扣除本金。
  三情景 V 与加权 V 取此口径。
- 对照列：
  · 取低 + 租赁有杠杆：转债同主口径，租赁按现规模滚动只扣税后利息现值；
  · 有杠杆（转债与租赁都滚动，只扣税后利息现值）；
  · 无杠杆（全额扣除可转债账面与租赁负债，不考虑转股）。
- 正常化归母净利含净利息（含可转债利息），剔除汇兑重估损益、上半年关税退税一次性收益与非经常性损益；
  经营所有者收益另加回有息负债税后利息、扣除超额现金税后利息收入，避免与现金重复计算。
"""

PRICE = 23.49            # 元/股，2026-10-19 收盘
N = 6.7019               # 亿股，brief 总股本（含回购专户股份）
TREASURY = 0.07043456    # 亿股，回购专户 7,043,456 股（2026-09-21，用于股权激励，不注销）
N_EX = N - TREASURY      # 剔除回购专户后的股本（对照）

# ---- 资产负债（2026-06-30 中报，期后事项调整）----
CASH = 16.8569           # 货币资金
TFA = 2.0020             # 交易性金融资产（结构性存款及外汇产品）
RESTRICTED = 1.4452      # 受限：冻结 0.2700、海关保证金 0.5007、票据保证金 0.6292、保函 0.0424、App Store 0.0028、押金
OP_RESERVE = 2.5         # 经营备付，约 TTM 营收 51.47 的 5%
DIV_PAID = 3.3157        # 2026 中期分红，2026-09-30 除息派发
BUYBACK_PAID = 0.8996    # 2026-07～08 回购付现（3,391,839 股）
LEASE = 0.4099 + 1.0123  # 一年内到期租赁负债 + 租赁负债
CB_BOOK = 12.2073 + 0.1840   # 应付债券 + 一年内到期应付债券（应计利息）
DEBT = CB_BOOK + LEASE

EXCESS_CASH = CASH + TFA - RESTRICTED - OP_RESERVE - DIV_PAID - BUYBACK_PAID
NET_CASH_ADJ = EXCESS_CASH - LEASE       # framework 定义的经调整净现金：不计可转债（+9.28）
NET_CASH_ADJ_WITH_CB = EXCESS_CASH - DEBT    # 含可转债账面（−3.12），只作说明

# 非经营资产：其他非流动金融资产（量旋科技等）0.336 + 长投 0.005 + 关联方股权转让应收款 0.639 打八折
RELATED_RECEIVABLE = 0.6392
NON_OP = 0.3363 + 0.0050 + RELATED_RECEIVABLE * 0.8

# ---- 利息 ----
TAX_INT = 0.15                         # 母公司高新技术企业税率
CB_RATE, LEASE_RATE = 0.0422, 0.0437   # 问询回复：可转债实际利率 4.22%，租赁 4.37%
DEBT_RATE = (CB_BOOK * CB_RATE + LEASE * LEASE_RATE) / DEBT
AT_INTEREST = DEBT * DEBT_RATE * (1 - TAX_INT)       # 全部有息负债税后利息（每年）
AT_LEASE_INTEREST = LEASE * LEASE_RATE * (1 - TAX_INT)
CASH_YIELD = 0.015
AT_CASH_INCOME = EXCESS_CASH * CASH_YIELD * (1 - TAX_INT)

# ---- 可转债 ----
CB_FACE = 12.79674       # 未转股面值（2026-06-30）
CONV_PRICE = 20.99       # 2026-09-30 起转股价
N_CB = CB_FACE / CONV_PRICE
CB_CREDIT = 0.04         # 债底折现率（AA）
T_COUPON, T_MATURITY = 0.737, 1.737   # 距 2027-07-14 付息、2028-07-14 到期（年）
PV_CB_DEBT = CB_FACE * 0.018 / (1 + CB_CREDIT) ** T_COUPON + CB_FACE * 1.15 / (1 + CB_CREDIT) ** T_MATURITY

# ---- 2026 正常化归母净利拆解 ----
H1_REPORTED = 4.3374         # 中报归母
H1_NONREC = 0.0114           # 中报非经常性损益
H1_FX_AT = 5.02 - 4.3260     # 公司口径：剔除汇兑后扣非 5.02 − 扣非 4.326
NORMALIZATION = {
    # 情景: (上半年关税退税一次性税后估计, 下半年核心归母)
    "bear": (0.60, 3.90),
    "base": (0.35, 4.35),
    "bull": (0.20, 4.70),
}


def ni_2026(s):
    one_off, h2 = NORMALIZATION[s]
    h1_core = H1_REPORTED - H1_NONREC + H1_FX_AT - one_off
    return h1_core + h2


SCEN = {
    "bear": dict(p=0.30, growth=[-0.20, 0.00, 0.03, 0.03, 0.03], gT=0.015, roic=0.20, ronic=0.15),
    "base": dict(p=0.50, growth=[0.07, 0.09, 0.08, 0.07, 0.06], gT=0.025, roic=0.28, ronic=0.20),
    "bull": dict(p=0.20, growth=[0.14, 0.13, 0.12, 0.10, 0.08], gT=0.025, roic=0.35, ronic=0.20),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
T_H2 = 0.20                                  # 2026 下半年现金流（三季度已实现、四季度将实现）
T_YEARS = [0.70, 1.70, 2.70, 3.70, 4.70]     # 年中现金流距 2026-10-19
RR_FLOOR = 0.05


def ni_op_2026(s):
    """经营归母净利：正常化归母 + 有息负债税后利息 − 超额现金税后利息收入。"""
    return ni_2026(s) + AT_INTEREST - AT_CASH_INCOME


def pv_operating(s, r, growth=None, base_ni=None, roic=None, gT=None, ronic=None):
    sc = SCEN[s]
    growth = sc["growth"] if growth is None else growth
    roic = sc["roic"] if roic is None else roic
    gT = sc["gT"] if gT is None else gT
    ronic = sc["ronic"] if ronic is None else ronic
    ni = ni_op_2026(s) if base_ni is None else base_ni
    rr0 = max(growth[0] / roic, RR_FLOOR)
    pv = 0.5 * ni * (1 - rr0) / (1 + r) ** T_H2
    path = []
    for g, t in zip(growth, T_YEARS):
        ni *= 1 + g
        rr = max(g / roic, RR_FLOOR)
        oe = ni * (1 - rr)
        pv += oe / (1 + r) ** t
        path.append((round(ni, 2), round(rr, 3), round(oe, 2)))
    tv = ni * (1 + gT) * (1 - gT / ronic) / (r - gT)
    pv_tv = tv / (1 + r) ** T_YEARS[-1]
    return pv + pv_tv, pv_tv, path


def cb_min(e_op, lease_claim, shares=N):
    """转债逐情景取低：债务（扣债底现值）与全部转股（加转股股数）取较低者。"""
    conv = (e_op - lease_claim) / (shares + N_CB)
    debt = (e_op - lease_claim - PV_CB_DEBT) / shares
    return min(conv, debt), conv, debt


def equity_values(s, r, extra=0.0, **kw):
    """extra：额外扣减的股权价值（如关联交易利益流出现值）。"""
    pv_op, pv_tv, path = pv_operating(s, r, **kw)
    e_op = pv_op + EXCESS_CASH + NON_OP - extra
    main, conv, debt = cb_min(e_op, LEASE)            # 主口径：转债取低，租赁本金全额扣除
    main_ex, _, _ = cb_min(e_op, LEASE, N_EX)
    lease_levered, _, _ = cb_min(e_op, AT_LEASE_INTEREST / r)
    return dict(main=main, conv=conv, debt=debt, main_ex_treasury=main_ex,
                lease_levered=lease_levered,
                levered=(e_op - AT_INTEREST / r) / N,
                unlevered=(e_op - DEBT) / N,
                tv_share=pv_tv / pv_op, path=path, e_op=e_op)


def weighted(r, key="main"):
    return sum(SCEN[s]["p"] * equity_values(s, r)[key] for s in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 输入核对 ==")
    print(f"超额现金 {EXCESS_CASH:.2f}；有息负债 {DEBT:.2f}（可转债 {CB_BOOK:.2f} + 租赁 {LEASE:.2f}）")
    print(f"经调整净现金（不计可转债）{NET_CASH_ADJ:.2f} → "
          f"{'<0：租赁按有杠杆口径' if NET_CASH_ADJ < 0 else '>0：租赁按无杠杆口径全额扣除'}；"
          f"含可转债账面时 {NET_CASH_ADJ_WITH_CB:.2f}；转债按逐情景取低")
    print(f"非经营资产 {NON_OP:.2f}；有息负债实际平均利率 {DEBT_RATE:.4f}；全部税后利息 {AT_INTEREST:.3f}/年"
          f"（租赁 {AT_LEASE_INTEREST:.3f}）；超额现金税后利息 {AT_CASH_INCOME:.3f}/年")
    print(f"可转债：转股股数 {N_CB:.4f} 亿股，债底现值 {PV_CB_DEBT:.2f}，转股价值（现价）{N_CB * PRICE:.2f}")

    print("\n== 2026 正常化归母净利（含净利息，剔除汇兑、关税退税一次性与非经常性）==")
    for s in SCEN:
        one_off, h2 = NORMALIZATION[s]
        print(f"{s}: 上半年核心 {ni_2026(s) - h2:.2f} + 下半年 {h2:.2f} = {ni_2026(s):.2f}；经营归母 {ni_op_2026(s):.2f}")

    r0 = 0.09
    print("\n== 三情景（9%）：主口径 = 转债逐情景取低（租赁本金全额扣除）==")
    for s in SCEN:
        v = equity_values(s, r0)
        print(f"{s}: p={SCEN[s]['p']:.2f} 主口径 V={v['main']:.2f}（债务 {v['debt']:.2f}／转股 {v['conv']:.2f}）  "
              f"对照：取低+租赁有杠杆 {v['lease_levered']:.2f}，有杠杆 {v['levered']:.2f}，无杠杆 {v['unlevered']:.2f}  "
              f"终值占比 {v['tv_share']:.1%}")
        print(f"    路径（经营归母, 再投资率, 所有者收益）{v['path']}")
    vw = weighted(r0)
    pv = PRICE / vw
    print(f"\n加权 V（主口径，转债逐情景取低）= {vw:.2f}，P/V = {pv:.3f}（{band(pv)}）")
    for key, name in (("lease_levered", "转债取低 + 租赁有杠杆"), ("levered", "有杠杆（转债与租赁滚动）"),
                      ("unlevered", "无杠杆（扣可转债账面，不计转股）")):
        vk = weighted(r0, key)
        print(f"对照 加权 V（{name}）= {vk:.2f}，P/V = {PRICE / vk:.3f}（{band(PRICE / vk)}）")
    vw_ex = weighted(r0, "main_ex_treasury")
    print(f"加权 V（主口径，剔除回购专户股本 {N_EX:.4f}）= {vw_ex:.2f}，P/V = {PRICE / vw_ex:.3f}")
    print(f"V 不变时各档价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n== 股权成本敏感性（主口径；债底现值固定按 4% 折现）==")
    for r in (0.08, 0.10):
        print(f"r={r:.0%}: 加权 V={weighted(r):.2f}；" + "，".join(
            f"{s} {equity_values(s, r)['main']:.2f}" for s in SCEN) +
            f"；对照 取低+租赁有杠杆 {weighted(r, 'lease_levered'):.2f}，有杠杆 {weighted(r, 'levered'):.2f}，"
            f"无杠杆 {weighted(r, 'unlevered'):.2f}")

    irr = solve(lambda r: equity_values("base", r)["main"], 0.04, 0.25, PRICE)
    irr_ll = solve(lambda r: equity_values("base", r)["lease_levered"], 0.04, 0.25, PRICE)
    irr_l = solve(lambda r: equity_values("base", r)["levered"], 0.04, 0.25, PRICE)
    irr_u = solve(lambda r: equity_values("base", r)["unlevered"], 0.04, 0.25, PRICE)
    print(f"\n现价隐含回报（基准情景，主口径）= {irr:.2%}；对照 取低+租赁有杠杆 {irr_ll:.2%}，"
          f"有杠杆 {irr_l:.2%}，无杠杆 {irr_u:.2%}")

    # 反向 DCF（主口径）：现价隐含的 10 年经营归母增速（再投资 = g ÷ 28%），之后 2.5% 永续
    def v_const_growth(g, years=10):
        ni = ni_op_2026("base")
        rr0 = max(g / 0.28, RR_FLOOR)
        pv_ = 0.5 * ni * (1 - rr0) / (1 + r0) ** T_H2
        t = 0.70
        for _ in range(years):
            ni *= 1 + g
            pv_ += ni * (1 - max(g / 0.28, RR_FLOOR)) / (1 + r0) ** t
            t += 1
        tv = ni * 1.025 * (1 - 0.025 / 0.20) / (r0 - 0.025)
        pv_ += tv / (1 + r0) ** (t - 1)
        return cb_min(pv_ + EXCESS_CASH + NON_OP, LEASE)[0]
    g10 = solve(v_const_growth, -0.10, 0.30, PRICE)

    def v_perp(g):
        ni = ni_op_2026("base")
        oe1 = ni * (1 + g) * (1 - max(g, 0) / 0.20)
        e_op = (0.5 * ni * (1 - max(g, 0) / 0.20) + oe1 / (r0 - g) / (1 + r0) ** 0.70
                + EXCESS_CASH + NON_OP)
        return cb_min(e_op, LEASE)[0]
    gp = solve(v_perp, -0.05, 0.08, PRICE)
    print(f"反向 DCF（主口径）：现价隐含 10 年经营归母年增速 {g10:.2%}（之后 2.5%）；或自 2027 年起永续增速 {gp:.2%}")

    # ---- 交叉验证 ----
    mcap = PRICE * N
    ev = mcap + DEBT - (CASH + TFA - DIV_PAID - BUYBACK_PAID)
    # 2026E 息税前利润：上半年税前 6.275（报表 5.434 + 汇兑损失 0.841）− 关税退税税前约 0.43；
    # 下半年（核心归母 4.35 − 少数股东分担亏损 0.08）÷（1 − 20%）；加净利息支出约 0.52
    h1_pretax = 5.434 + 0.841 - 0.43
    h2_pretax = (NORMALIZATION["base"][1] - 0.08) / (1 - 0.20)
    ebit_2026 = h1_pretax + h2_pretax + 0.52
    print(f"\n交叉：市值 {mcap:.1f}；PE（2026 基准正常化 {ni_2026('base'):.2f}）{mcap / ni_2026('base'):.1f}×；"
          f"PE（TTM 归母 8.89）{mcap / 8.89:.1f}×；PB（归母权益 39.32）{mcap / 39.32:.2f}×；"
          f"EV {ev:.1f}，EV/EBIT(2026E {ebit_2026:.1f}) {ev / ebit_2026:.1f}×；股息率 {1.00 / PRICE:.2%}，"
          f"回购收益率 {BUYBACK_PAID / mcap:.2%}")

    # ---- 证伪条件触发后的独立 V（主口径，9%；除 F2 外均为三情景重新加权）----
    print("\n== 证伪触发后的独立 V（主口径）==")

    def reweighted(mod):
        return sum(SCEN[s]["p"] * equity_values(s, r0, **mod(s))["main"] for s in SCEN)

    # F1：2026 年报剔除汇兑后扣非归母 < 8.5 亿（基准预期 9.37）：起点按 (8.5 − 0.35) ÷ 9.02 缩放，各年增速 −1pp
    k1 = (8.5 - 0.35) / ni_2026("base")
    f1 = reweighted(lambda s: dict(base_ni=ni_2026(s) * k1 + AT_INTEREST - AT_CASH_INCOME,
                                   growth=[g - 0.01 for g in SCEN[s]["growth"]]))
    # F2：美国对公司诊断/TPMS 产品实施禁售或进口限制，或任一半年北美收入同比降 > 25%：取严重熊市路径
    f2 = equity_values("bear", r0, growth=[-0.45, 0.00, 0.03, 0.03, 0.03], gT=0.01)["main"]
    # F3：软件云服务预收（合同负债 + 其他非流动负债中的软件款）低于门槛，或 AI 及软件收入增速 < 8%
    f3 = reweighted(lambda s: dict(growth=[g - 0.03 for g in SCEN[s]["growth"]],
                                   roic=SCEN[s]["roic"] - 0.06))
    # F4：再现关联方资金占用或向关联方低价转让资产：按每年 0.5 亿利益流出永续现值扣减
    f4 = reweighted(lambda s: dict(extra=0.5 / r0))
    # F5：美元兑人民币中间价 2027 上半年均值 < 6.40：2027 年经营归母较各情景再降 8%
    f5 = reweighted(lambda s: dict(growth=[SCEN[s]["growth"][0] - 0.08] + SCEN[s]["growth"][1:]))
    for name, v in (("F1 核心利润不及", f1), ("F2 美国限制", f2), ("F3 软件预收下降", f3),
                    ("F4 关联交易利益流出", f4), ("F5 人民币升破 6.40", f5)):
        print(f"{name}: V={v:.2f}，P/V={PRICE / v:.2f}")

    # ---- 三季度估计（三季报 2026-10-30 预约披露，作为下次核对点）----
    q3_rev, q3_core, q3_fx = 12.45, 2.15, -0.22
    print(f"\n三季度估计：营收 {q3_rev:.2f}（同比 {q3_rev / 11.51 - 1:+.1%}），核心归母 {q3_core:.2f}，"
          f"汇兑税后 {q3_fx:.2f}，报表归母约 {q3_core + q3_fx:.2f}；前三季度归母约 {H1_REPORTED + q3_core + q3_fx:.2f}")
    print(f"2026 全年报表归母（基准）约 {ni_2026('base') + NORMALIZATION['base'][0] - H1_FX_AT + q3_fx + H1_NONREC:.2f}；"
          f"剔汇扣非约 {ni_2026('base') + NORMALIZATION['base'][0]:.2f}")


if __name__ == "__main__":
    main()
