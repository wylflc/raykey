# -*- coding: utf-8 -*-
"""拓荆科技（688072）独立估值：所有者收益 DCF（归母口径）、反向 DCF、隐含回报与重组备考对照。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。估值日 2026-10-21（北京时间收盘）。
输入均写在本脚本内，出处见 companies/688072_拓荆科技.md「来源」。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 533.00                      # 2026-10-21 收盘，腾讯日线
SHARES = 2.92173270                 # 亿股，总股本（含回购专户 702,102 股），2026-09-09 公告 2026-061
TREASURY = 0.00702102               # 亿股，回购专户（用途为股权激励，未公告注销）
SHARES_EX_TREASURY = SHARES - TREASURY
VAL_DATE = date(2026, 10, 21)

# ---------------------------------------------------------------- 经调整净现金（2026-06-30 中报 + 期后已发生现金事项）
cash = 75.2219                      # 货币资金（中报第 61 页）
restricted = 1.0849                 # 其他货币资金：保函/承兑保证金等受限（中报第 63、153 页）
struct_dep = 10.60                  # 交易性金融资产中的结构性存款（中报第 153 页），视同现金
loans = 12.0363 + 3.9980            # 一年内到期长期借款 + 长期借款（中报第 184-185 页）
lt_payable = 0.2648                 # 长期应付款＝应付股权融资款，类债务（中报第 186 页）
lease = 0.0402 + 0.0591             # 租赁负债（含一年内到期）：净利润已扣折旧与利息，只列示不扣
div_declared = 1.0201               # 2026 半年度现金红利，10-12 发放（公告 2026-061/067）
vest_cash_in = 1.9069               # 7-8 月限制性股票归属款（股本已含该部分股份，中报第 102 页）
op_reserve = 8.0                    # 经营备付：约 1.4 个月 2026E 付现成本
NET_CASH_ADJ = (cash - restricted + struct_dep - loans - lt_payable
                - div_declared + vest_cash_in - op_reserve)
INTEREST_RATE = 0.022               # 有息负债实际平均利率（H1 利息 0.248 亿 / 平均借款约 22 亿 ×2）

# ---------------------------------------------------------------- 非经营资产（对外股权投资）
# 交易性金融资产中的上市股权（中报第 64-65 页，6-30 账面，万元→亿元）
listed_equity_book = {"恒运昌688785": 10.552996, "先锋精科688605": 0.907396, "托伦斯301583": 0.199605}
# 期后市值调整系数（价格日收盘 / 6-30 收盘）：恒运昌 293.90 / 484.03（腾讯行情，2026-10-21 查）；
# 先锋精科、托伦斯 6-30 价格未查，按账面（合计 1.1 亿，影响 <0.4 元/股）
HYC_PX_0630, HYC_PX_NOW = 484.03, 293.90
listed_mtm_factor = {"恒运昌688785": HYC_PX_NOW / HYC_PX_0630, "先锋精科688605": 1.00, "托伦斯301583": 1.00}
# 期后新增：长鑫科技（688825）IPO 战略配售 18,244,803 股 @8.66 元（约 1.58 亿，单一媒体来源），按 10-21 收盘 40.97 元计
CXMT_SHARES, CXMT_PX_NOW, CXMT_COST = 0.18244803, 40.97, 1.58
cxmt_mtm = CXMT_SHARES * CXMT_PX_NOW
other_nc_fin = 7.8728               # 其他非流动金融资产（未上市股权，含芯丰精密 2.70 亿成本等；中报第 171 页）
lt_equity = 3.6768 - 2.0960         # 长期股权投资扣除已出售的稷以科技（6-30 账面 2.096 亿，中报第 170 页）
fund_commit = 5.00 + 0.30           # 长智瀚海 5.0 亿（08-21 公告 2026-053）+ 海望合纵 0.3 亿（07-08 公告 2026-037），按认缴额计
NONOP_HAIRCUT = 0.15                # 未实现收益税负、限售期与基金流动性折扣
listed_mtm = sum(v * listed_mtm_factor[k] for k, v in listed_equity_book.items())
NONOP_GROSS = listed_mtm + cxmt_mtm + other_nc_fin + lt_equity + fund_commit
NONOP = NONOP_GROSS * (1 - NONOP_HAIRCUT)
# 期后现金事项：稷以科技 8.4478% 全部转让款 2.7231 亿（07-08 公告 2026-038，8-31 前收齐）；长鑫配售款 1.58 亿；基金认缴 5.3 亿
POST_CASH = 2.7231 - CXMT_COST - fund_commit
NET_CASH_ADJ += POST_CASH
MINORITY = 4.8392                   # 少数股东权益（6-30），主要为拓荆键科 46.4% 外部与员工平台股东；对合并现金的索取权，扣除
# ---------------------------------------------------------------- 报表与正常化读数
REV_2025 = 65.19
NP_2025 = 9.27
NP_TTM = 21.75
EQUITY_LATEST = 127.16
REV_TTM = 74.78
H1_2026_NP_RECUR = 3.67             # 2026H1 扣非归母

YEARS = list(range(2027, 2037))     # 显式期 10 年，2037 起永续

SCEN = {
    # rev26: 2026E 营收；g: 2027-2036 营收增速；m26: 2026E 正常化净利率；m: 2027-2036 净利率；
    # k: 每 1 元新增营收所需新增经营资本（含资本开支净额与营运资本）；gT: 永续增速
    "bear": dict(p=0.25, rev26=82.0, m26=0.138,
                 g=[0.10, -0.10, 0.10, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03],
                 m=[0.130, 0.100, 0.120, 0.130, 0.130, 0.130, 0.130, 0.130, 0.130, 0.130],
                 k=0.85, gT=0.020),
    "base": dict(p=0.50, rev26=88.0, m26=0.163,
                 g=[0.25, 0.20, 0.17, 0.14, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04],
                 m=[0.175, 0.180, 0.185, 0.190, 0.190, 0.190, 0.190, 0.190, 0.190, 0.190],
                 k=0.65, gT=0.025),
    "bull": dict(p=0.25, rev26=95.0, m26=0.190,
                 g=[0.35, 0.30, 0.25, 0.20, 0.17, 0.14, 0.12, 0.10, 0.08, 0.06],
                 m=[0.205, 0.215, 0.225, 0.230, 0.230, 0.230, 0.230, 0.230, 0.230, 0.230],
                 k=0.50, gT=0.025),
}


def yearfrac(d1, d2):
    return (d2 - d1).days / 365.25


T_H2 = 0.10                                          # 2026H2 剩余所有者收益的近似折现时点
T_MID = {y: yearfrac(VAL_DATE, date(y, 7, 1)) for y in YEARS}


def project(s):
    """返回逐年 (年, 营收, 净利, 再投资, 所有者收益)，以及 2026H2 所有者收益。"""
    rev = [s["rev26"]]
    for g in s["g"]:
        rev.append(rev[-1] * (1 + g))
    rows = []
    peak = max(rev[0], REV_TTM)            # 已投入经营资本对应的营收峰值：下行年不回收、复苏到前高之前不重复投入
    for i, y in enumerate(YEARS):
        r = rev[i + 1]
        np_ = r * s["m"][i]
        reinv = s["k"] * max(r - peak, 0.0)
        peak = max(peak, r)
        rows.append((y, r, np_, reinv, np_ - reinv))
    np26 = s["rev26"] * s["m26"]
    oe_h2 = (np26 - H1_2026_NP_RECUR) - s["k"] * max(s["rev26"] - REV_TTM, 0.0)
    return rows, np26, oe_h2


def operating_value(s, r):
    rows, np26, oe_h2 = project(s)
    pv = oe_h2 / (1 + r) ** T_H2
    for (y, rev, np_, reinv, oe) in rows:
        pv += oe / (1 + r) ** T_MID[y]
    roiic = s["m"][-1] / s["k"]
    np_T = rows[-1][2] * (1 + s["gT"])
    oe_T = np_T * (1 - s["gT"] / roiic)
    tv = oe_T / (r - s["gT"])
    pv_tv = tv / (1 + r) ** T_MID[YEARS[-1]]
    return pv + pv_tv, pv_tv


def equity_value(s, r, extra=0.0):
    ov, pv_tv = operating_value(s, r)
    return ov + NET_CASH_ADJ + NONOP - MINORITY + extra, pv_tv, ov


def per_share(eq, shares=SHARES):
    return eq / shares


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


def weighted(r):
    return sum(SCEN[k]["p"] * per_share(equity_value(SCEN[k], r)[0]) for k in SCEN)


def main():
    COE = 0.09
    print("== 拓荆科技 688072 独立估值（估值日 2026-10-21，价格 %.2f 元）==" % PRICE)
    print("经调整净现金 %.2f 亿（含期后现金事项 %.2f 亿）；非经营资产 毛额 %.2f 亿 → 折后 %.2f 亿"
          "（恒运昌等上市股权按市值 %.2f 亿，长鑫科技配售股 %.2f 亿）；少数股东权益 %.2f 亿扣除"
          % (NET_CASH_ADJ, POST_CASH, NONOP_GROSS, NONOP, listed_mtm, cxmt_mtm, MINORITY))
    print("租赁负债 %.2f 亿只列示不扣；有息负债 %.2f 亿已全额扣除" % (lease, loans + lt_payable))
    res = {}
    for k, s in SCEN.items():
        eq, pv_tv, ov = equity_value(s, COE)
        v = per_share(eq)
        res[k] = v
        rows, np26, oe_h2 = project(s)
        roiic = s["m"][-1] / s["k"]
        print("\n[%s] p=%.2f  2026E 营收 %.1f 正常化归母净利 %.2f（净利率 %.1f%%）  2026H2 所有者收益 %.2f"
              % (k, s["p"], s["rev26"], np26, np26 / s["rev26"] * 100, oe_h2))
        for (y, rev, np_, reinv, oe) in rows:
            print("  %d 营收 %7.1f  净利 %6.2f  再投资 %6.2f  所有者收益 %6.2f  再投资率 %5.1f%%"
                  % (y, rev, np_, reinv, oe, reinv / np_ * 100 if np_ else 0))
        print("  增量回报 ROIIC %.1f%%；永续增速 %.1f%%，永续再投资率 %.1f%%" %
              (roiic * 100, s["gT"] * 100, s["gT"] / roiic * 100))
        print("  经营价值 %.1f 亿（终值现值 %.1f 亿，占经营价值 %.0f%%）；股权价值 %.1f 亿；V = %.2f 元；剔除回购专户 V = %.2f 元"
              % (ov, pv_tv, pv_tv / ov * 100, eq, v, eq / SHARES_EX_TREASURY))
    vw = sum(SCEN[k]["p"] * res[k] for k in SCEN)
    pv_ratio = PRICE / vw
    print("\n加权 V = %.2f 元；P/V = %.2f" % (vw, pv_ratio))
    eq_w = vw * SHARES
    print("剔除回购专户股份：加权 V = %.2f 元，P/V = %.2f" % (eq_w / SHARES_EX_TREASURY, PRICE / (eq_w / SHARES_EX_TREASURY)))
    v8, v10 = weighted(0.08), weighted(0.10)
    print("股权成本 8%%：加权 V = %.2f 元（P/V %.2f）；10%%：加权 V = %.2f 元（P/V %.2f）"
          % (v8, PRICE / v8, v10, PRICE / v10))
    for k in SCEN:
        print("  %s：8%% V=%.2f，10%% V=%.2f" % (k, per_share(equity_value(SCEN[k], 0.08)[0]),
                                            per_share(equity_value(SCEN[k], 0.10)[0])))

    # 现价隐含回报：基准情景所有者收益流（含终值、净现金与非经营资产）现值 = 现价
    base = SCEN["base"]
    irr = solve(lambda r: per_share(equity_value(base, r)[0]), base["gT"] + 0.002, 0.30, PRICE)
    print("\n现价隐含回报（基准情景现金流）= %.2f%%" % (irr * 100))

    # 反向 DCF ①：保持基准净利率与 k，2027-2036 营收统一增速 g，使 V = 现价
    def v_uniform_g(g):
        s = dict(base)
        s["g"] = [g] * 10
        return per_share(equity_value(s, COE)[0])
    g_imp = solve(v_uniform_g, 0.0, 0.60, PRICE)
    s_imp = dict(base); s_imp["g"] = [g_imp] * 10
    rev36 = project(s_imp)[0][-1][1]
    print("反向 DCF①：基准利润率与再投资强度下，现价隐含 2027-2036 营收年增 %.1f%%（2036 年营收 %.0f 亿，净利 %.0f 亿）"
          % (g_imp * 100, rev36, rev36 * base["m"][-1]))

    # 反向 DCF ①b：改用牛市利润率与再投资强度（23%、k=0.50）
    bull = SCEN["bull"]

    def v_uniform_g_bull(g):
        s = dict(bull)
        s["g"] = [g] * 10
        return per_share(equity_value(s, COE)[0])
    g_imp_b = solve(v_uniform_g_bull, 0.0, 0.60, PRICE)
    s_b = dict(bull); s_b["g"] = [g_imp_b] * 10
    rev36_b = project(s_b)[0][-1][1]
    print("反向 DCF①b：牛市利润率（23%%）与 k=0.50 下，现价隐含 2027-2036 营收年增 %.1f%%（2036 年营收 %.0f 亿）"
          % (g_imp_b * 100, rev36_b))

    # 反向 DCF ②：以 2026E 基准正常化净利 15.0 亿为起点，10 年净利年增 g（再投资率 g/ROIIC），之后 2.5% 永续
    np0 = base["rev26"] * base["m26"]
    roiic = base["m"][-1] / base["k"]

    def v_np_growth(g):
        pv = 0.0
        np_ = np0
        for y in YEARS:
            np_ *= (1 + g)
            oe = np_ * (1 - min(g / roiic, 1.0))
            pv += oe / (1 + COE) ** T_MID[y]
        oe_T = np_ * (1 + base["gT"]) * (1 - base["gT"] / roiic)
        pv += oe_T / (COE - base["gT"]) / (1 + COE) ** T_MID[YEARS[-1]]
        return (pv + NET_CASH_ADJ + NONOP - MINORITY) / SHARES
    g2 = solve(v_np_growth, 0.0, 0.80, PRICE)
    print("反向 DCF②：以 2026E 正常化净利 %.1f 亿起步，现价隐含未来 10 年净利年增 %.1f%%（2036 年净利 %.0f 亿），之后 2.5%% 永续"
          % (np0, g2 * 100, np0 * (1 + g2) ** 10))

    # 交叉验证
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NONOP + MINORITY
    print("\n交叉验证：市值 %.1f 亿；EV（扣经调整净现金与折后非经营资产、加少数股东权益）%.1f 亿" % (mcap, ev))
    for k in SCEN:
        np26 = SCEN[k]["rev26"] * SCEN[k]["m26"]
        print("  %s：市值/2026E 正常化净利 = %.0f×；EV/2026E 营收 = %.1f×" % (k, mcap / np26, ev / SCEN[k]["rev26"]))
    print("  市值/2025 归母 = %.0f×；市值/TTM 归母 = %.1f×；PB = %.2f×；股息率 0.13%%"
          % (mcap / NP_2025, mcap / NP_TTM, mcap / EQUITY_LATEST))

    # 重组备考（交易未完成，仅作对照）：25 亿收购无锡尚积 100%（股份 18.2752 亿＝4,768,850 股 @383.22；现金 6.7248 亿）
    # 配套募资 18.2 亿，假设按 80% × 现价发行；无锡尚积独立价值按三档 10/18/28 亿（含其自身净现金约 3.2 亿）
    new_sh_consid = 0.04768850
    cash_consid = 6.7248
    pipe = 18.20
    pipe_px = 0.80 * PRICE
    pipe_sh = pipe / pipe_px
    fees = 0.40
    print("\n重组备考（未完成，仅对照）：配套募资按 %.1f 元/股发行 %.4f 亿股" % (pipe_px, pipe_sh))
    sj = {"bear": 10.0, "base": 18.0, "bull": 28.0}
    vw_pf = 0.0
    for k in SCEN:
        eq = equity_value(SCEN[k], COE)[0]
        eq_pf = eq + sj[k] - cash_consid + pipe - fees
        v_pf = eq_pf / (SHARES + new_sh_consid + pipe_sh)
        vw_pf += SCEN[k]["p"] * v_pf
        print("  %s：备考 V = %.2f 元（独立口径 %.2f）" % (k, v_pf, res[k]))
    print("  备考加权 V = %.2f 元；P/V = %.2f" % (vw_pf, PRICE / vw_pf))

    # 证伪情景
    print("\n证伪触发后的 V（股权成本 9%）：")
    fz = {}
    s = dict(SCEN["bear"]); fz["F1 2026 年报营收<80 亿或（扣非归母+股份支付）<16 亿 → 熊市情景"] = per_share(equity_value(s, COE)[0])
    s = dict(SCEN["base"]); s["m"] = [min(x, 0.15) for x in s["m"]]
    fz["F2 连续两季毛利率<38%：长期净利率 15%（基准增长）"] = per_share(equity_value(s, COE)[0])
    s = dict(SCEN["base"]); s["g"] = [0.05, -0.15, 0.05] + s["g"][3:]
    fz["F3 合同负债<40 亿或 2027H1 营收同比为负：2027 +5%、2028 -15%、2029 +5%"] = per_share(equity_value(s, COE)[0])
    s = dict(SCEN["bull"]); fz["F4 反向：2027 营收≥128 亿且（扣非归母+股份支付）净利率≥24% → 牛市情景"] = per_share(equity_value(s, COE)[0])
    for k, v in fz.items():
        print("  %s：V = %.2f 元，P/V = %.2f" % (k, v, PRICE / v))

    # 分档价格（V 不变）
    print("\n分档价格（V=%.2f 不变）：≤%.0f 明显低估；%.0f-%.0f 温和低估；%.0f-%.0f 大致合理；>%.0f 偏贵"
          % (vw, 0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
