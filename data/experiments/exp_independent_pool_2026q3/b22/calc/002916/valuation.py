#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深南电路（002916）独立估值（OI-291 b22，深度版）。

运行：python3 valuation.py
单位：金额亿元；每股价值、价格元/股；比率小数。价格日 2026-10-21（北京时间收盘）。

方法：归母所有者收益 DCF（股权成本 9%，敏感性 8%／10%，终值增长 2.5%），三情景概率加权。
- 所有者收益 = 归母净利 + 净负债税后利息（经营口径） − 净再投资；
  净再投资 = 固定资本强度 k_fixed × 收入增量（收入下降时取 0） + 营运资本强度 K_WC × 收入增量（同期口径）。
- 经调整净现金为负 → 按 framework 第 4 条用有杠杆口径：净负债按现规模滚动、不偿还本金，
  股权价值 = 经营所有者收益现值 − 净负债税后利息永续现值 + 非经营资产；同时给出无杠杆口径（全额扣净负债）对照。
- 现金流时点：2026 下半年流量折现 0.1 年；2027 起年中惯例（2027 年流量在 0.695 年，依此类推）；
  终值以 2037 年流量按戈登公式接续。
来源页码见各输入旁注释（PDF 物理页）。
"""

# ---------------------------------------------------------------- 市场与股本
PRICE = 305.60                     # 2026-10-21 收盘，brief.md
SHARES_TOTAL = 6.8117              # 腾讯行情总股本（含第二期限制性股票 1,442.58 万股）
CANCEL = 0.000326                  # 拟回购注销限制性股票：1.8 万股（4-23 董事会、8-14 股东会，2026H1_report 第 26 页）
                                   # + 1.46 万股（8-25 董事会、9-11 股东会，公告 2026-055，pdf.dfcfw.com/pdf/H2_AN202609111829277123_1.pdf）
SHARES = SHARES_TOTAL - CANCEL
RS_SHARES = 0.144258               # 限制性股票 1,442.58 万股（2026H1_report 第 36、148 页）

COE = 0.09
G_TERM = 0.025
TAX = 0.15                         # 母公司、无锡深南、南通深南、广州广芯 15%（2026H1_report 第 97 页）

# ---------------------------------------------------------------- 资产负债表 2026-06-30（2026H1_report）
CASH = 22.0224                     # 货币资金（第 44、99 页）
RESTRICTED = 0.0040                # 土地复垦保证金（第 99 页）
FINCO_DEPOSIT = 11.9003            # 其中存放中航工业集团财务公司（关联方，第 29、99 页）；8-26 披露日余额为 0
OPER_RESERVE = 10.0                # 经营备付（假设：约 2026E 收入的 2.7%，约半个月现金成本）
DIV_PAYABLE = 0.3462               # 应付股利：限制性股票股利（第 46、121 页）
ST_LOAN = 12.2437                  # 短期借款，含信用证福费廷 6.99（第 120 页）
LT_LOAN = 57.1693                  # 长期借款（第 46、124 页）
LT_CURRENT = 9.6549                # 一年内到期的长期借款（第 123 页）
LEASE = 0.9449 + 0.2162            # 租赁负债（含一年内到期），NP 已扣使用权资产折旧与租赁利息 → 列示不扣
RS_OBLIGATION = 16.2031            # 限制性股票回购义务（其他应付款，第 121 页；库存股第 46、125 页）：股份已计入股本 → 列示不扣
NONOP = 0.8419 + 0.0309 + 0.0462   # 其他权益工具投资 + 长期股权投资 + 投资性房地产（第 45 页）

DEBT = ST_LOAN + LT_LOAN + LT_CURRENT
NET_CASH_ADJ = (CASH - RESTRICTED) - OPER_RESERVE - DIV_PAYABLE - DEBT   # 无杠杆口径经调整净现金（负 = 净负债）
NET_DEBT_ADJ = -NET_CASH_ADJ
R_DEBT = 0.021   # 有息负债实际平均利率：2025 利息费用 0.776 / 平均有息负债 34.3 = 2.26%；2026H1 年化 1.12 / 平均 57.0 = 1.97%
ATI = NET_DEBT_ADJ * R_DEBT * (1 - TAX)  # 净负债税后利息（年）

# ---------------------------------------------------------------- 2026 年估计
NP_H1 = 22.5146                    # 2026H1 归母净利（2026H1_report 第 8 页）
REV_H1 = 152.9636                  # 2026H1 营业收入
NP_9M = (40.5, 41.5)               # 前三季度业绩预告（forecast_20261016_531246 第 1 页）
NP_Q3 = sum(NP_9M) / 2 - NP_H1     # 三季度单季归母净利中值（区间 17.99～18.99）
REV_Q3 = 103.0                     # 三季度收入估计（假设：单季净利率约 18%；10-23 三季报核对）
NETINV_H2_2026 = 45.0              # 2026 下半年净再投资：资本开支约 45（6-30 已签约未确认资本承诺 69.36，第 149 页）
                                   # − 折旧摊销约 10.5 + 营运资本约 +10.5（年末营运资本约为全年收入 25%，募集说明书第 66-67 页）
NP_2025, REV_2025 = 32.7574, 236.4698
K_WC = 0.24                        # 营运资本强度：募集说明书测算 25.56%（第 66 页）；2026-06-30 实际 80.6 / 2026E 收入 364 = 22%

# 三情景：Q4 2026 归母净利、Q4 收入；2027-2036 收入增速与归母净利率；固定资本强度
SCENARIOS = {
    "bear": dict(
        p=0.25, np_q4=17.0, rev_q4=100.0,
        growth=[0.05, -0.10, 0.06, 0.05, 0.04, 0.035, 0.03, 0.03, 0.03, 0.025],
        margin=[0.140, 0.095, 0.105, 0.110, 0.110, 0.110, 0.110, 0.110, 0.110, 0.110],
        k_fixed=0.71,
        norm_rev_2026=330.0, norm_margin=0.110,
        text="AI 资本开支 2027-2028 进入消化期，同业新增产能集中释放：2027 收入 +5%、2028 −10%，"
             "净利率 2028 年落至 9.5%，长期 11%（2019-2024 中枢 11.2%）；新增产能单位收入资本 0.95，增量回报约 11.6%（与募投项目税后 IRR 11.12% 相当）"),
    "base": dict(
        p=0.50, np_q4=19.0, rev_q4=108.0,
        growth=[0.22, 0.13, 0.09, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03],
        margin=[0.165, 0.150, 0.140, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135, 0.135],
        k_fixed=0.61,
        norm_rev_2026=355.0, norm_margin=0.135,
        text="AI 需求延续但增速回落：2027 收入 +22%（无锡 AI 项目、南通四期、泰国、广州基板爬坡），2028 +13%，之后 9%→3%；"
             "净利率由 2026 年 16.5% 回落至 13.5%（较 2019-2024 中枢 11.2% 高 2.3 个百分点的结构性部分）；单位收入资本 0.85，增量回报约 16%"),
    "bull": dict(
        p=0.25, np_q4=20.5, rev_q4=114.0,
        growth=[0.30, 0.22, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04],
        margin=[0.170, 0.170, 0.165, 0.160, 0.160, 0.160, 0.160, 0.160, 0.160, 0.160],
        k_fixed=0.51,
        norm_rev_2026=364.0, norm_margin=0.160,
        text="AI 超级周期持续、份额提升（高多层板与 FC-BGA）：2027 收入 +30%、2028 +22%，2026-2031 年复合约 17.6%；"
             "净利率长期 16%；单位收入资本 0.75，增量回报约 21%"),
}

T_H2 = 0.10        # 2026 下半年流量的折现年数
T0 = 0.695         # 2027 年流量（年中）距价格日的年数：71 天/365 + 0.5
YEARS = list(range(2027, 2037))
NEW_ISSUE_GROSS = 43.67352         # 定增募资上限（financing_20261016_531124 第 4、59 页）
ISSUE_FEE = 0.005                  # 发行费用率（假设）


def build(sc, g_override=None):
    """返回逐年路径：收入、归母净利、净再投资、经营所有者收益。"""
    rev26 = REV_H1 + REV_Q3 + sc["rev_q4"]
    np26 = NP_H1 + NP_Q3 + sc["np_q4"]
    growth = [g_override] * 10 if g_override is not None else sc["growth"]
    rev, npat, ni, oe = [rev26], [], [], []
    for i in range(10):
        r_new = rev[-1] * (1 + growth[i])
        d = r_new - rev[-1]
        n_i = sc["k_fixed"] * max(d, 0.0) + K_WC * d
        p = r_new * sc["margin"][i]
        rev.append(r_new)
        npat.append(p)
        ni.append(n_i)
        oe.append(p + ATI - n_i)
    return dict(rev26=rev26, np26=np26, rev=rev[1:], np=npat, ni=ni, oe=oe)


def value(sc, r=COE, g=G_TERM, levered=True, g_override=None, extra_cash=0.0, extra_shares=0.0,
          finco_haircut=False):
    """每股价值（元）。levered=True 为有杠杆口径。"""
    b = build(sc, g_override)
    np_h2 = NP_Q3 + sc["np_q4"]
    oe_h2 = np_h2 + ATI / 2 - NETINV_H2_2026
    pv = oe_h2 / (1 + r) ** T_H2
    for i in range(10):
        pv += b["oe"][i] / (1 + r) ** (T0 + i)
    # 终值：2037 年流量
    m = sc["margin"][-1]
    rev37 = b["rev"][-1] * (1 + g)
    oe37 = rev37 * m + ATI - (sc["k_fixed"] + K_WC) * (rev37 - b["rev"][-1])
    tv_pv = oe37 / (1 + r) ** (T0 + 10) * (1 + r) / (r - g)
    pv_total = pv + tv_pv
    nd = NET_DEBT_ADJ + (FINCO_DEPOSIT if finco_haircut else 0.0)
    if levered:
        # 经营流量已加回净负债税后利息（ATI，剥离归母净利中的利息）；此处扣除净负债税后利息的永续现值
        ati = nd * R_DEBT * (1 - TAX)
        eq = pv_total - ati / r + NONOP
    else:
        eq = pv_total - nd + NONOP
    eq += extra_cash
    return eq / (SHARES + extra_shares), dict(pv_explicit=pv, pv_tv=tv_pv, eq=eq, b=b, oe37=oe37, rev37=rev37)


def weighted(r=COE, levered=True, **kw):
    vs = {k: value(sc, r=r, levered=levered, **kw)[0] for k, sc in SCENARIOS.items()}
    return sum(SCENARIOS[k]["p"] * v for k, v in vs.items()), vs


def solve(f, lo, hi, target, n=200):
    """二分求根：f 单调。"""
    flo = f(lo) - target
    for _ in range(n):
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
    print("=== 深南电路 002916 独立估值（价格日 2026-10-21，现价 %.2f 元，股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("经调整净现金（无杠杆口径）= 现金 %.2f − 受限 %.3f − 经营备付 %.1f − 应付股利 %.2f − 有息负债 %.2f = %.2f 亿元"
          % (CASH, RESTRICTED, OPER_RESERVE, DIV_PAYABLE, DEBT, NET_CASH_ADJ))
    print("  其中关联方财务公司存款 %.2f（单列）；租赁负债 %.2f 列示不扣；限制性股票回购义务 %.2f 列示不扣；非经营资产 %.2f"
          % (FINCO_DEPOSIT, LEASE, RS_OBLIGATION, NONOP))
    print("  净负债税后利息 %.3f 亿/年（利率 %.1f%%），9%% 永续现值 %.2f 亿" % (ATI, R_DEBT * 100, ATI / COE))
    print("2026 三季度单季归母净利（预告推算）%.2f～%.2f，中值 %.2f；扣非单季 %.2f～%.2f"
          % (NP_9M[0] - NP_H1, NP_9M[1] - NP_H1, NP_Q3, 40.18 - 22.3917, 41.18 - 22.3917))
    print()
    res = {}
    for k, sc in SCENARIOS.items():
        v_l, d = value(sc)
        v_u, _ = value(sc, levered=False)
        res[k] = (v_l, v_u)
        b = d["b"]
        tv_share = d["pv_tv"] / (d["pv_explicit"] + d["pv_tv"])
        m_lr = sc["margin"][-1]
        k_tot = sc["k_fixed"] + K_WC
        rr = (k_tot * G_TERM / (1 + G_TERM)) / (m_lr + ATI / d["rev37"])
        print("[%s] p=%.2f  有杠杆 V=%.2f  无杠杆 V=%.2f  终值占比 %.0f%%  终值再投资率 %.1f%%  增量回报 %.1f%%"
              % (k, sc["p"], v_l, v_u, tv_share * 100, rr * 100, m_lr / k_tot * 100))
        print("   2026E 收入 %.1f 归母 %.1f | " % (b["rev26"], b["np26"]) +
              " ".join("%d:%.0f/%.1f/%.1f" % (y, b["rev"][i], b["np"][i], b["oe"][i]) for i, y in enumerate(YEARS[:5]))
              + "  （收入/归母净利/所有者收益）")
        print("   正常化 2026 归母净利 %.1f（正常化收入 %.0f × 净利率 %.1f%%）"
              % (sc["norm_rev_2026"] * sc["norm_margin"], sc["norm_rev_2026"], sc["norm_margin"] * 100))
    # 基准情景增长路径（json growth_path）与 2026 归母净利拆分
    bb = build(SCENARIOS["base"])
    nps = [bb["np26"]] + bb["np"]
    g_np = [nps[i + 1] / nps[i] - 1 for i in range(5)]
    rr5 = sum(bb["ni"][i] / (bb["np"][i] + ATI) for i in range(5)) / 5
    print("基准归母净利增速 2027-2031：" + " ".join("%.1f%%" % (x * 100) for x in g_np)
          + "；2027-2031 平均再投资率 %.0f%%" % (rr5 * 100))
    fx_one_off = -0.949 * (1 - TAX)          # 2026H1 汇兑损失 0.95 亿（2026H1_report 第 128 页），税后
    nonrec = 40.5 - 40.18                    # 前三季度非经常性损益（预告：归母 − 扣非，下限口径）
    np_ex = bb["np26"] - fx_one_off - nonrec
    norm_base = SCENARIOS["base"]["norm_rev_2026"] * SCENARIOS["base"]["norm_margin"]
    print("2026E 归母 %.1f = 结构性（正常化）%.1f + 周期性 %.1f + 一次性 %.1f（汇兑 %.2f、非经常 +%.2f）"
          % (bb["np26"], norm_base, np_ex - norm_base, fx_one_off + nonrec, fx_one_off, nonrec))
    vw, _ = weighted()
    vw_u, _ = weighted(levered=False)
    print()
    print("概率加权 V（有杠杆，登记口径）= %.2f 元，P/V = %.2f → %s" % (vw, PRICE / vw, verdict(PRICE / vw)))
    print("概率加权 V（无杠杆对照）     = %.2f 元，P/V = %.2f" % (vw_u, PRICE / vw_u))
    for r in (0.08, 0.10):
        v_r, vs_r = weighted(r=r)
        print("COE %.0f%%：加权 V = %.2f（熊 %.2f / 基准 %.2f / 牛 %.2f），P/V = %.2f"
              % (r * 100, v_r, vs_r["bear"], vs_r["base"], vs_r["bull"], PRICE / v_r))
    # 隐含回报：基准情景流量使现值 = 现价
    irr = solve(lambda r: value(SCENARIOS["base"], r=r)[0], 0.03, 0.20, PRICE)
    irr_w = solve(lambda r: weighted(r=r)[0], 0.03, 0.20, PRICE)
    print("现价隐含回报（基准情景流量，有杠杆）= %.2f%%；（三情景加权流量）= %.2f%%" % (irr * 100, irr_w * 100))
    # 反向 DCF：基准利润率与资本强度下，2027-2036 统一收入增速
    g_imp = solve(lambda g: value(SCENARIOS["base"], g_override=g)[0], 0.0, 0.40, PRICE)
    b_imp = build(SCENARIOS["base"], g_override=g_imp)
    np36 = b_imp["np"][-1]
    print("反向 DCF：基准利润率（长期 13.5%%）与资本强度下，现价隐含 2027-2036 收入年增 %.1f%%，2036 年收入 %.0f、归母净利 %.0f（2026E 的 %.1f 倍）"
          % (g_imp * 100, b_imp["rev"][-1], np36, np36 / b_imp["np26"]))
    sc_bull = SCENARIOS["bull"]
    g_imp_b = solve(lambda g: value(sc_bull, g_override=g)[0], 0.0, 0.40, PRICE)
    b_imp_b = build(sc_bull, g_override=g_imp_b)
    print("         牛市利润率（16%%）与资本强度下，隐含 2027-2036 收入年增 %.1f%%，2036 年收入 %.0f（2026E 的 %.1f 倍）"
          % (g_imp_b * 100, b_imp_b["rev"][-1], b_imp_b["rev"][-1] / b_imp_b["rev26"]))
    # 定增前后
    print()
    for px in (270.0, 245.0):
        n_new = NEW_ISSUE_GROSS / px
        cash = NEW_ISSUE_GROSS * (1 - ISSUE_FEE)
        vpost, vs_post = weighted(extra_cash=cash, extra_shares=n_new)
        print("定增后（发行价 %.0f 元、新增 %.4f 亿股、净募 %.2f 亿）：加权 V = %.2f（熊 %.2f / 基准 %.2f / 牛 %.2f），P/V = %.2f"
              % (px, n_new, cash, vpost, vs_post["bear"], vs_post["base"], vs_post["bull"], PRICE / vpost))
    # 关联方存款与限制性股票对照
    v_fin, _ = weighted(finco_haircut=True)
    v_fin_u, _ = weighted(levered=False, finco_haircut=True)
    print("对照：剔除财务公司存款 11.90 后，加权 V 有杠杆 %.2f / 无杠杆 %.2f" % (v_fin, v_fin_u))
    eq_w = vw * SHARES
    v_rs = (eq_w - RS_OBLIGATION) / (SHARES - RS_SHARES)
    print("对照：限制性股票按未解锁处理（扣回购义务 16.20、剔除 1,442.58 万股）后加权 V = %.2f" % v_rs)
    # 证伪触发后的 V
    vb, vbase, vbull = res["bear"][0], res["base"][0], res["bull"][0]
    print()
    print("证伪触发后 V：牛 50%%+基准 50%% = %.2f；熊 50%%+基准 50%% = %.2f；熊 100%% = %.2f；"
          "熊 40%%+基准 60%% = %.2f" % (0.5 * vbull + 0.5 * vbase, 0.5 * vb + 0.5 * vbase, vb, 0.4 * vb + 0.6 * vbase))
    base_lowm = dict(SCENARIOS["base"])
    base_lowm["margin"] = [m - 0.01 for m in base_lowm["margin"]]
    v_lowm = value(base_lowm)[0]
    print("基准情景净利率全程 −1 个百分点：V = %.2f；三情景加权 = %.2f"
          % (v_lowm, 0.25 * vb + 0.5 * v_lowm + 0.25 * vbull))
    base_k = dict(SCENARIOS["base"])
    base_k["k_fixed"] = 0.46
    v_k100 = value(dict(SCENARIOS["base"], k_fixed=0.76))[0]
    print("敏感性：基准资本强度 0.70（固定 0.46）时基准 V = %.2f；资本强度 1.00（固定 0.76）时 = %.2f，三情景加权 = %.2f"
          % (value(base_k)[0], v_k100, 0.25 * vb + 0.5 * v_k100 + 0.25 * vbull))
    base_m15 = dict(SCENARIOS["base"])
    base_m15["margin"] = [0.165, 0.155] + [0.15] * 8
    print("敏感性：基准净利率 2027 16.5%%、2028 15.5%%、2029 起长期 15%%时基准 V = %.2f" % value(base_m15)[0])
    # 交叉验证
    print()
    mcap = PRICE * SHARES_TOTAL
    np26b = build(SCENARIOS["base"])["np26"]
    ebit26 = np26b / (1 - 0.115) + R_DEBT * DEBT
    print("交叉：市值 %.1f 亿；PE(TTM 41.67) %.1f；PE(2026E %.1f) %.1f；PB(180.30) %.2f；EV/EBIT(2026E) %.1f；股息率 %.2f%%"
          % (mcap, mcap / 41.67, np26b, mcap / np26b, mcap / 180.30, (mcap + NET_DEBT_ADJ - NONOP) / ebit26, 2.4 / PRICE * 100))
    for lab, pv in (("明显低估", 0.75), ("温和低估", 0.90), ("合理上沿", 1.10)):
        print("V 不变时 %s 价格上限 = %.1f 元" % (lab, vw * pv))


if __name__ == "__main__":
    main()
