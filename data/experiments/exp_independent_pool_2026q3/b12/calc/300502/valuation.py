"""新易盛（300502）独立估值：所有者收益 DCF（周期正常化），三情景概率加权。

运行：python3 valuation.py
单位：金额亿元，每股价值元/股。价格日 2026-10-20，估值时点同日。
输入出处见注释；页码为 PDF 物理页（txt 中「=== 第 N 页 ===」）。
"""

PRICE = 298.17          # 2026-10-20 收盘（brief.md）
SHARES = 13.9474        # 亿股，腾讯行情总股本（brief.md）；无回购专户股份、无拟注销股份
COE = 0.09

# ---------- 2026-06-30 资产负债表（2026H1_report 第 36-38 页；附注第 78、98-102 页） ----------
CASH = 72.40                    # 货币资金
RESTRICTED = 0.56               # 受限保证金（第 16、98 页）
LEASE_DEBT = 0.18 + 0.06        # 租赁负债 + 一年内到期租赁负债（无银行借款、无债券）
LT_STAFF_PAY = 12.01            # 长期应付职工薪酬（长期应付薪酬款，递延薪酬，第 102 页）
LT_STAFF_PAY_TAX = 0.15         # 按 15% 税率扣税盾（年报第 133 页：职工薪酬已确认递延所得税资产）
NON_OPERATING = 0.32 + 0.13     # 其他非流动金融资产 + 长期股权投资
OP_CASH_RATIO = 0.02            # 经营备付：2026E 营收的 2%

NWC_0630 = (75.48 + 0.14 + 0.12 + 116.55 + 8.70 + 16.08    # 应收、票据、应收融资、存货、预付、长期预付材料款
            - 71.25 - 22.30 - 2.17)                         # 应付账款、应付票据（商业承兑，经营性）、合同负债
FIXED_0630 = 41.09 + 5.57 + 1.83 + 1.35 + 0.21 + 0.68       # 固定资产、在建、无形、预付设备款、使用权、长期待摊
IC_0630 = NWC_0630 + FIXED_0630
IC_2025 = (44.38 + 0.04 + 0.12 + 72.34 + 0.17 - 37.26 - 15.49 - 0.91) + (33.54 + 3.27 + 1.93 + 0.88 + 0.12 + 0.81)

H1_REV = 209.10                 # 2026H1 营收（第 7 页）
H1_NP = 75.29                   # 2026H1 归母净利（含汇兑损失 7.44 亿，第 106 页）
H1_FX_LOSS_AT = 7.44 * (1 - 0.15)   # 汇兑损失税后，一次性项目
TTM_REV, TTM_NP = 353.14, 131.19
INTEREST_YIELD_AT = 0.025 * 0.85    # 正常化净现金税后利息收益率（2026H1 利息收入 1.02 亿，年化约 2.7%）


def net_cash_adj(rev_2026):
    """无杠杆口径经调整净现金（json 的 net_cash_adj_yi，非经营资产另列）。"""
    return (CASH - RESTRICTED - LEASE_DEBT - LT_STAFF_PAY * (1 - LT_STAFF_PAY_TAX)
            - OP_CASH_RATIO * rev_2026)


# ---------- 情景 ----------
# rev / margin：2026（全年，H1 实际 + H2 估计）至 2031 营收与归母净利率（经营口径，不含利息收入）
# ic：年末投入资本 / 当年营收（营运资金 + 固定资本）
# fade：2032 起 n 年增速从 g0 线性降到终值增速；ronic：增量回报，决定再投资率 = g / ronic
# lr_margin：长期（中枢）净利率，用于 2026 正常化归母净利
SCEN = {
    "bear": dict(p=0.30, rev=[495, 680, 520, 400, 420, 450], h2_margin=0.36,
                 margin=[None, 0.31, 0.20, 0.14, 0.16, 0.17], ic=[0.40, 0.40, 0.44, 0.44, 0.42, 0.40],
                 fade_n=0, fade_g0=0.02, g=0.02, ronic_fade=0.15, ronic=0.15, lr_margin=0.17,
                 text="2027 营收 680 亿后见顶；2028-2029 资本开支消化、1.6T/800G 降价与新进入者压价，叠加美方限制使北美新代际份额流失，"
                      "营收回落到 400-450 亿，净利率 14%-17%；终值增长 2%，增量回报 15%"),
    "base": dict(p=0.50, rev=[519, 800, 840, 720, 770, 830], h2_margin=0.38,
                 margin=[None, 0.34, 0.29, 0.24, 0.24, 0.24], ic=[0.38, 0.37, 0.37, 0.39, 0.38, 0.37],
                 fade_n=5, fade_g0=0.06, g=0.025, ronic_fade=0.25, ronic=0.20, lr_margin=0.24,
                 text="2027 营收 800 亿（激励目标 900 亿打七折至九折之间），2028 持平略增；2029 消化期回落 14%，2030-2031 恢复到 830 亿，"
                      "份额由约 20% 降到约 15%，净利率回到中枢 24%；2032-2036 增速 6% 递减到 2.5%"),
    "bull": dict(p=0.20, rev=[540, 1000, 1200, 1200, 1300, 1400], h2_margin=0.39,
                 margin=[None, 0.37, 0.33, 0.30, 0.30, 0.30], ic=[0.37, 0.35, 0.35, 0.35, 0.35, 0.35],
                 fade_n=5, fade_g0=0.08, g=0.025, ronic_fade=0.30, ronic=0.25, lr_margin=0.30,
                 text="2027 营收 1000 亿（达成激励目标，接近一致预期 370 亿净利），scale-up 光互联（NPO/CPO 引擎）与 3.2T 接力，"
                      "2028-2031 营收 1200-1400 亿，净利率 30%；2032-2036 增速 8% 递减到 2.5%"),
}

T_H2 = 0.2                      # 2026H2 所有者收益（7-1 起，约半数已发生）
T_2027 = 0.70                   # 2027 年中距估值日（2026-10-20）年数


def run(s, r=COE):
    rev = s["rev"]
    np_ = [H1_NP + (rev[0] - H1_REV) * s["h2_margin"]] + [rev[i] * s["margin"][i] for i in range(1, 6)]
    ic = [rev[i] * s["ic"][i] for i in range(6)]
    oe = [(np_[0] - H1_NP) - (ic[0] - IC_0630)] + [np_[i] - (ic[i] - ic[i - 1]) for i in range(1, 6)]
    t = [T_H2] + [T_2027 + i for i in range(5)]
    pv_explicit = sum(oe[i] / (1 + r) ** t[i] for i in range(6))
    npx, tt, pv_fade, fade_rows = np_[5], t[5], 0.0, []
    for k in range(1, s["fade_n"] + 1):
        g = s["fade_g0"] + (s["g"] - s["fade_g0"]) * (k - 1) / max(s["fade_n"] - 1, 1)
        npx *= 1 + g
        tt += 1
        oe_k = npx * (1 - g / s["ronic_fade"])
        pv_fade += oe_k / (1 + r) ** tt
        fade_rows.append((2031 + k, round(g, 4), round(npx, 1), round(oe_k, 1)))
    tv = npx * (1 + s["g"]) * (1 - s["g"] / s["ronic"]) / (r - s["g"])
    pv_tv = tv / (1 + r) ** tt
    nc = net_cash_adj(rev[0])
    equity = pv_explicit + pv_fade + pv_tv + nc + NON_OPERATING
    oe_2026_full = np_[0] - (ic[0] - IC_2025)
    return dict(np=np_, ic=ic, oe=oe, oe_2026_full=oe_2026_full, pv_explicit=pv_explicit, pv_fade=pv_fade,
                pv_tv=pv_tv, tv_share=pv_tv / (pv_explicit + pv_fade + pv_tv), net_cash=nc,
                equity=equity, v=equity / SHARES, fade=fade_rows)


def weighted(r=COE, probs=None, scen=SCEN):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * run(scen[k], r)["v"] for k in scen)


def with_margin_cut(cut):
    """治理漏出情景：2027 起各年及长期净利率下调 cut（关联采购溢价、子公司层面内部人持股分利）。"""
    out = {}
    for k, s in SCEN.items():
        s2 = dict(s)
        s2["margin"] = [None] + [m - cut for m in s["margin"][1:]]
        out[k] = s2
    return out


def normalized_np_2026(s):
    """2026 正常化归母净利：2026E 营收 × 长期中枢净利率 + 正常化净现金税后利息；剔除汇兑等一次性项目。"""
    return s["rev"][0] * s["lr_margin"] + net_cash_adj(s["rev"][0]) * INTEREST_YIELD_AT


def implied_irr(s):
    lo, hi = 0.03, 0.30
    target = PRICE * SHARES
    for _ in range(100):
        mid = (lo + hi) / 2
        if run(s, mid)["equity"] > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(np0, years=10, g_term=0.025, ronic=0.20, reinvest=0.20, r=COE):
    """以 np0 为起点、前 10 年再投资率 reinvest，求使现值 = 市值 - 经调整净现金 - 非经营资产的年增速。"""
    target = PRICE * SHARES - net_cash_adj(SCEN["base"]["rev"][0]) - NON_OPERATING

    def pv(g):
        tot, npx = 0.0, np0
        for t in range(1, years + 1):
            npx *= 1 + g
            tot += npx * (1 - reinvest) / (1 + r) ** t
        tv = npx * (1 + g_term) * (1 - g_term / ronic) / (r - g_term)
        return tot + tv / (1 + r) ** years

    lo, hi = -0.3, 0.6
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def perpetual_growth_implied(np0, ronic=0.20, r=COE):
    target = PRICE * SHARES - net_cash_adj(SCEN["base"]["rev"][0]) - NON_OPERATING
    lo, hi = -0.05, 0.085
    for _ in range(200):
        g = (lo + hi) / 2
        val = np0 * (1 + g) * (1 - g / ronic) / (r - g)
        if val < target:
            lo = g
        else:
            hi = g
    return (lo + hi) / 2


if __name__ == "__main__":
    print(f"现价 {PRICE}，总股本 {SHARES} 亿股，市值 {PRICE * SHARES:.1f} 亿")
    print(f"6-30 投入资本 {IC_0630:.2f}（营运资金 {NWC_0630:.2f} + 固定资本 {FIXED_0630:.2f}）；2025 末 {IC_2025:.2f}")
    res = {k: run(s) for k, s in SCEN.items()}
    for k, s in SCEN.items():
        x = res[k]
        print(f"\n[{k}] p={s['p']:.2f}  V={x['v']:.1f}  股权价值={x['equity']:.0f}"
              f"（显性期 {x['pv_explicit']:.0f} + 递减期 {x['pv_fade']:.0f} + 终值 {x['pv_tv']:.0f}"
              f" + 经调整净现金 {x['net_cash']:.1f} + 非经营 {NON_OPERATING:.2f}；终值占比 {x['tv_share']:.0%}）")
        print("  年份      2026   2027   2028   2029   2030   2031")
        print("  营收   " + " ".join(f"{v:6.0f}" for v in s["rev"]))
        print("  归母   " + " ".join(f"{v:6.1f}" for v in x["np"]))
        print("  投入资本" + " ".join(f"{v:6.0f}" for v in x["ic"]))
        oe_full = [x["oe_2026_full"]] + x["oe"][1:]
        print("  所有者收益(2026 全年口径)" + " ".join(f"{v:6.1f}" for v in oe_full))
        print("  所有者收益增速 2027-2031：" + ", ".join(f"{oe_full[i] / oe_full[i - 1] - 1:+.1%}" for i in range(1, 6)))
        if x["fade"]:
            print("  递减期（年, 增速, 归母, 所有者收益）：", x["fade"])
        print(f"  2026 正常化归母净利 {normalized_np_2026(s):.1f}（长期净利率 {s['lr_margin']:.0%}）")
    w = weighted()
    print(f"\n加权 V = {w:.1f}，P/V = {PRICE / w:.2f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.1f}（P/V {PRICE / weighted(0.08):.2f}）；"
          f"10%：加权 V = {weighted(0.10):.1f}（P/V {PRICE / weighted(0.10):.2f}）")
    w_alt = weighted(probs={"bear": 0.25, "base": 0.50, "bull": 0.25})
    print(f"概率改为 0.25/0.50/0.25：加权 V = {w_alt:.1f}（P/V {PRICE / w_alt:.2f}）")
    for k in SCEN:
        print(f"  {k}: 8% {run(SCEN[k], 0.08)['v']:.1f} / 10% {run(SCEN[k], 0.10)['v']:.1f}")
    print(f"现价隐含回报（基准情景现金流）= {implied_irr(SCEN['base']):.2%}")
    print(f"经调整净现金（基准 2026E 营收口径）= {net_cash_adj(SCEN['base']['rev'][0]):.2f} 亿；非经营资产 {NON_OPERATING:.2f} 亿")
    nb = normalized_np_2026(SCEN["base"])
    np26_exfx = res["base"]["np"][0] + H1_FX_LOSS_AT
    print(f"反向 DCF：以基准正常化归母 {nb:.1f} 亿起步（前 10 年再投资率 20%），隐含 10 年年增 {reverse_dcf(nb):.1%}；"
          f"以 2026E 剔除汇兑 {np26_exfx:.1f} 亿起步，隐含 {reverse_dcf(np26_exfx):.1%}")
    print(f"反向 DCF（永续）：以基准正常化归母起步，隐含永续增速 {perpetual_growth_implied(nb):.2%}（增量回报 20%）")
    # 证伪触发后的 V
    trig = {
        "Q3/Q4 环比转负或毛利率<44%：概率改为 0.45/0.45/0.10": weighted(probs={"bear": 0.45, "base": 0.45, "bull": 0.10}),
        "美方限制覆盖新易盛新代际产品：取熊市": res["bear"]["v"],
        "2027 营收<650 亿或净利率<28%：概率改为 0.60/0.40/0": weighted(probs={"bear": 0.60, "base": 0.40, "bull": 0.0}),
        "2027 营收≥900 亿且净利率≥36%：概率改为 0.15/0.50/0.35": weighted(probs={"bear": 0.15, "base": 0.50, "bull": 0.35}),
        "关联采购或子公司层面内部人分利扩大：各情景净利率下调 1 个百分点": weighted(scen=with_margin_cut(0.01)),
    }
    for k, v in trig.items():
        print(f"证伪/验证：{k} → V = {v:.1f}")
    # 交叉验证（数据包与定期报告数字）
    mcap = PRICE * SHARES
    ev = mcap - net_cash_adj(SCEN["base"]["rev"][0]) - NON_OPERATING
    ebit_ttm = 108.59 + 86.82 - 44.43            # 营业利润：2025 + 2026H1 - 2025H1（年报第 73 页、半年报第 41 页）
    fx_ttm = -2.44 + 1.93 + 7.44                 # TTM 汇兑损失（税前）：2025 收益 2.44、2025H1 收益 1.93、2026H1 损失 7.44
    ebit_27 = res["base"]["np"][1] / (1 - 0.13)  # 2027E 基准，按有效税率 13% 还原
    print(f"交叉：PE(TTM) {mcap / TTM_NP:.1f}x；PE(2026E 基准) {mcap / res['base']['np'][0]:.1f}x；PB(6-30) {mcap / 242.97:.1f}x；"
          f"EV/EBIT(TTM) {ev / ebit_ttm:.1f}x，剔除汇兑 {ev / (ebit_ttm + fx_ttm):.1f}x；EV/EBIT(2027E 基准) {ev / ebit_27:.1f}x")
    eq_w = w * SHARES
    print(f"加权 V 对应：PE(TTM) {eq_w / TTM_NP:.1f}x，PE(2027E 基准) {eq_w / res['base']['np'][1]:.1f}x，"
          f"正常化归母 {eq_w / nb:.1f}x，PB(6-30) {eq_w / 242.97:.1f}x")
    div_ttm = 1.0 * 9.95897632                    # 2025 年度每 10 股派 10 元，股本 9.9590 亿股（6-11 除息）
    print(f"股东回报：过去 12 个月现金分红 {div_ttm:.2f} 亿（{div_ttm / mcap:.2%}），提议回购 8-10 亿（{8 / mcap:.2%}-{10 / mcap:.2%}）")
    # H 股：不超过发行后总股本 8%，另加 15% 超额配售；按 270 元（较现价折让约 10%）、费用 3% 示意
    n_h = SHARES * 0.08 / 0.92 * 1.15
    v_h = (w * SHARES + 270 * n_h * 0.97) / (SHARES + n_h)
    print(f"H 股示意：新增 {n_h:.3f} 亿股、发行价 270 元，加权 V 由 {w:.1f} 变为 {v_h:.1f}（发行价高于 V 时增厚）")
    print("V 不变时分档价格：≤{:.1f} 明显低估；{:.1f}-{:.1f} 温和低估；{:.1f}-{:.1f} 大致合理；>{:.1f} 偏贵".format(
        0.75 * w, 0.75 * w, 0.90 * w, 0.90 * w, 1.10 * w, 1.10 * w))
    print(f"参照：TTM 营收 {TTM_REV}、归母 {TTM_NP}；2026E（基准）归母 {res['base']['np'][0]:.1f}，剔除汇兑 {np26_exfx:.1f}；"
          f"市值/2027E 基准归母 = {PRICE * SHARES / res['base']['np'][1]:.1f}x")
