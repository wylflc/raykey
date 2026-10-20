#!/usr/bin/env python3
"""同仁堂（600085）独立估值，OI-291 b08，价格日 2026-10-20。

运行：python3 valuation.py
口径：归母、金额亿元、每股元；股权成本 9%（敏感性 8%／10%）。
输入全部写在本脚本内，来源见正文「来源」一节（2026H1_report 页码等）。
"""

PRICE = 24.97
SHARES = 13.7147          # 亿股，无回购专户、无拟注销股份
MKT_CAP = PRICE * SHARES
COE = 0.09
PROB = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# ---------------------------------------------------------------------------
# 1. 归母穿透的经调整净现金（2026-06-30）
# ---------------------------------------------------------------------------
CONS_CASH = 102.7602           # 货币资金，2026H1_report 第 32、76 页
CONS_TFA = 7.5026              # 交易性金融资产，其中结构性存款 7.50，第 77 页
RESTRICTED = 0.7355            # 受限货币资金（保证金等），第 16、77 页
CONS_DEBT = 1.2902 + 11.0893 + 6.2246 + 0.6797
#   短期借款 + 长期借款 + 一年内到期长期借款 + 少数股东借款（其他应付款内），第 33、110、111 页
DIV_PAYABLE_MIN = 1.6527       # 子公司应付其他股东股利，第 110 页
LEASE_LIAB = 15.6263           # 租赁负债（含一年内到期），租金已计入利润，不再扣除，第 112 页
RELATED_DEPOSIT = 0.0          # 集团财务公司存款：无（第 27、76 页「存放财务公司存款」为空）

PARENT_CASH = 32.1078 + 4.50   # 母公司货币资金 + 交易性金融资产，第 34 页
PARENT_DEBT = 0.433            # 集团委托贷款（2026-11-15 到期），第 111 页
GM_EQ, MIN_EQ = 136.2325, 75.3508          # 归母权益、少数股东权益，第 33 页
PARENT_EQ, PARENT_LTEI = 83.8180, 12.5663  # 母公司净资产、对子公司长期股权投资，第 34-35 页
SHANGYE_REDUCTION = 2.4576     # 商业公司定向减资对价，2026-09-30 公告 2026-025
SHANGYE_STAKE_AFTER = 0.575033
OP_RESERVE = 6.5               # 经营备付：归母穿透约 1 个月付现成本

# 母公司在子公司合计中的经济权益比例（按权益穿透）
S_SUB = (GM_EQ - PARENT_EQ + PARENT_LTEI) / (GM_EQ + MIN_EQ - PARENT_EQ + PARENT_LTEI)
CONS_NET_CASH = CONS_CASH + CONS_TFA - RESTRICTED - CONS_DEBT - DIV_PAYABLE_MIN
SUB_NET_CASH = (CONS_CASH + CONS_TFA - PARENT_CASH) - RESTRICTED \
    - (CONS_DEBT - PARENT_DEBT) - DIV_PAYABLE_MIN
PARENT_NET_CASH = PARENT_CASH - PARENT_DEBT
ATTR_NET_CASH_GROSS = PARENT_NET_CASH + S_SUB * SUB_NET_CASH
NET_CASH_ADJ = ATTR_NET_CASH_GROSS - SHANGYE_REDUCTION * SHANGYE_STAKE_AFTER \
    - OP_RESERVE + RELATED_DEPOSIT
NON_OPERATING = 0.0            # 联营合营与其他权益投资收益已在利润中，不另计

# ---------------------------------------------------------------------------
# 2. 2026 年归母净利：报表估计与正常化三档（含净利息、剔除一次性）
# ---------------------------------------------------------------------------
H1_2026 = 7.2619               # 2026H1_report 第 6 页
Q3_2026E = 2.3206 * 0.85       # 2025Q3 归母 2.32 × (1-15%)
Q4_2026E = 0.60                # 2025Q4 仅 0.12（减值与年末费用），2024Q4 1.76
NP_2026E = H1_2026 + Q3_2026E + Q4_2026E
NONREC_2026E = 0.20            # 上半年非经常 0.129，全年按 0.20
EXCESS_INT_2026 = 0.35         # 2026 母公司利息收入偏高（上半年 0.93 亿），超出正常化部分
NP_2026E_CORE = NP_2026E - NONREC_2026E - EXCESS_INT_2026
NORM_ADJ = {
    "bear": -0.80,   # 安宫降价与竞品（牛黄跌价后双天然厂家增至 5 家）、兴安保健全年停产
    "base": +1.00,   # 渠道去库存（提货低于动销）一半回补
    "bull": +2.70,   # 去库存全部回补 + 低价牛黄入成本后毛利修复与费用压降延续
}
NORM_NP_2026 = {k: round(NP_2026E_CORE + v, 1) for k, v in NORM_ADJ.items()}
NET_INT = 0.80                 # 正常化归母税后净利息：母公司 36.2 亿 × 2.0% × 85% + 子公司穿透

# ---------------------------------------------------------------------------
# 3. 情景：经营性归母利润增长、再投资与存货释放
# ---------------------------------------------------------------------------
YEARS = [2027, 2028, 2029, 2030, 2031]
SCEN = {
    "bear": dict(growth=[-0.02, 0.01, 0.02, 0.02, 0.02], g_term=0.015, r_inc=0.10,
                 h2_2026=1.45, one_off={2027: -2.0}, release=[0.0, 0.0, 0.0]),
    "base": dict(growth=[0.06, 0.06, 0.05, 0.04, 0.035], g_term=0.025, r_inc=0.14,
                 h2_2026=2.05, one_off={}, release=[2.0, 2.5, 2.5]),
    "bull": dict(growth=[0.12, 0.10, 0.08, 0.06, 0.05], g_term=0.025, r_inc=0.20,
                 h2_2026=2.35, one_off={}, release=[3.0, 3.5, 3.4]),
}
# 时点（年，自 2026-10-20 起）：2026 下半年 0.1；各年年中；终值在 2031 年末
T_H2, T_YEAR, T_TV = 0.1, [0.7, 1.7, 2.7, 3.7, 4.7], 5.2
T_RELEASE = [0.1, 0.7, 1.7]


def scenario_value(name, coe=COE, norm_np=None, extra_one_off=None, detail=False):
    s = SCEN[name]
    np0 = (norm_np if norm_np is not None else NORM_NP_2026[name]) - NET_INT
    one_off = dict(s["one_off"])
    if extra_one_off:
        for y, v in extra_one_off.items():
            one_off[y] = one_off.get(y, 0.0) + v
    pv, npo, rows = 0.0, np0, []
    for y, g, t in zip(YEARS, s["growth"], T_YEAR):
        npo *= 1 + g
        reinv = max(g, 0.0) / s["r_inc"]
        oe = npo * (1 - reinv) + one_off.get(y, 0.0)
        pv += oe / (1 + coe) ** t
        rows.append((y, g, npo, reinv, oe))
    g_t = s["g_term"]
    oe_t = npo * (1 + g_t) * (1 - g_t / s["r_inc"])
    tv = oe_t / (coe - g_t)
    pv_tv = tv / (1 + coe) ** T_TV
    pv_h2 = s["h2_2026"] / (1 + coe) ** T_H2
    pv_rel = sum(r / (1 + coe) ** t for r, t in zip(s["release"], T_RELEASE))
    equity = pv + pv_tv + pv_h2 + pv_rel + NET_CASH_ADJ + NON_OPERATING
    out = dict(v=equity / SHARES, equity=equity, pv_ops=pv, pv_tv=pv_tv, pv_h2=pv_h2,
               pv_rel=pv_rel, tv_share=pv_tv / equity, rows=rows, oe_t=oe_t, tv=tv)
    if detail:
        return out
    return out["v"]


def weighted(coe=COE):
    return sum(PROB[k] * scenario_value(k, coe) for k in PROB)


def solve(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    """基准情景所有者收益流（含终值、存货释放与净现金）现值等于市值的折现率。"""
    return solve(lambda r: scenario_value("base", r) * SHARES - MKT_CAP, 0.03, 0.20)


def reverse_dcf_10y(r_inc=0.14, coe=COE, g_term=0.025):
    """现价隐含：2027-2036 年经营性归母利润恒定增速 g（再投资 = g/r_inc），之后 2.5%。"""
    target = MKT_CAP - NET_CASH_ADJ - SCEN["base"]["h2_2026"] / (1 + coe) ** T_H2 \
        - sum(r / (1 + coe) ** t for r, t in zip(SCEN["base"]["release"], T_RELEASE))
    np0 = NORM_NP_2026["base"] - NET_INT

    def pv_ops(g):
        npo, pv = np0, 0.0
        for i in range(10):
            npo *= 1 + g
            pv += npo * (1 - g / r_inc) / (1 + coe) ** (0.7 + i)
        oe_t = npo * (1 + g_term) * (1 - g_term / r_inc)
        return pv + oe_t / (coe - g_term) / (1 + coe) ** 10.2

    best = max((pv_ops(g / 1000), g / 1000) for g in range(0, int(r_inc * 1000)))
    if best[0] < target:
        return None, best
    return solve(lambda g: pv_ops(g) - target, 0.0, best[1]), best


def reverse_oe_10y(coe=COE, g_term=0.025):
    """常规反向 DCF：所有者收益自基准稳态水平（经营性归母 × (1-2.5%/14%)）起，
    2027-2036 年恒定增速 g，之后 2.5% 永续；加净现金、2026H2 与存货释放后等于市值。"""
    target = MKT_CAP - NET_CASH_ADJ - SCEN["base"]["h2_2026"] / (1 + coe) ** T_H2 \
        - sum(r / (1 + coe) ** t for r, t in zip(SCEN["base"]["release"], T_RELEASE))
    oe0 = (NORM_NP_2026["base"] - NET_INT) * (1 - g_term / SCEN["base"]["r_inc"])

    def pv(g):
        oe, tot = oe0, 0.0
        for i in range(10):
            oe *= 1 + g
            tot += oe / (1 + coe) ** (0.7 + i)
        return tot + oe * (1 + g_term) / (coe - g_term) / (1 + coe) ** 10.2

    return solve(lambda g: pv(g) - target, -0.05, 0.40), oe0


def reverse_perpetual(coe=COE):
    """不计再投资的永续增速：经营价值 = OE_2027 / (coe - g)。"""
    target = MKT_CAP - NET_CASH_ADJ
    oe0 = NORM_NP_2026["base"] - NET_INT
    return (target * coe - oe0) / (target + oe0)


def weighted_variant(coe=COE, release_scale=1.0, extra_one_off=None):
    """证伪用：三情景同时改存货释放与一次性损失后的加权 V。"""
    saved = {k: list(SCEN[k]["release"]) for k in SCEN}
    try:
        for k in SCEN:
            SCEN[k]["release"] = [r * release_scale for r in saved[k]]
        return sum(PROB[k] * scenario_value(k, coe, extra_one_off=extra_one_off) for k in PROB)
    finally:
        for k in SCEN:
            SCEN[k]["release"] = saved[k]


# ---------------------------------------------------------------------------
# 4. 交叉验证
# ---------------------------------------------------------------------------
HKD_CNY = 0.8686                       # 2026H1_report 第 129 页外币折算汇率（6-30）
KJ_MCAP_HKD = 1280.784e6 * 3.105 / 1e8  # 同仁堂科技 01666，2026-10-20 收盘 3.105 港元
GY_MCAP_HKD = 837.1e6 * 5.775 / 1e8     # 同仁堂国药 03613，2026-10-20 收盘 5.775 港元
SY_APPRAISAL = 25.5902                  # 商业公司归母权益收益法评估值（2025-12-31）
OTHER_SUBS_BOOK = 17.0487 - 4.9517      # 「其他」分部净资产，第 156 页
PARENT_OPS_NP = {"2024": 13.9331 - 3.7395 - 0.4240 * 0.85,
                 "2025": 11.2587 - 2.8609 - 1.1872 * 0.85,
                 "2026E": (7.5438 - 2.5172 - 0.9296 * 0.85) + 1.20}
PARENT_OPS_NORM = 6.3                   # 母公司本部经营（不含股利、利息）正常化税后利润
HIST_PE = [38.5, 69.9, 46.1, 43.5, 33.3, 39.2, 31.8, 50.3, 42.9, 44.1, 36.5, 37.2]
PEER_MEDIAN_PE_TTM = 17.57
NP_TTM, NP_TTM_KF = 9.70, 9.18
DPS = 0.50


def sotp():
    kj = 0.4685 * KJ_MCAP_HKD * HKD_CNY
    gy = 0.3362 * GY_MCAP_HKD * HKD_CNY
    sy = SHANGYE_STAKE_AFTER * (SY_APPRAISAL - SHANGYE_REDUCTION)
    oth = 0.60 * OTHER_SUBS_BOOK
    cash = PARENT_NET_CASH - 3.0
    base_ops = scenario_value("base", detail=True)
    mult = (base_ops["pv_ops"] + base_ops["pv_tv"] + base_ops["pv_h2"]) / \
        (NORM_NP_2026["base"] - NET_INT)
    ops = PARENT_OPS_NORM * mult
    total = kj + gy + sy + oth + cash + ops
    implied_parent_ops = MKT_CAP - (kj + gy + sy + oth + cash)
    return dict(kj=kj, gy=gy, sy=sy, oth=oth, cash=cash, ops=ops, mult=mult,
                total=total, v=total / SHARES, implied_parent_ops=implied_parent_ops)


def main():
    print("=== 同仁堂 600085 独立估值（价格日 2026-10-20，现价 %.2f，总股本 %.4f 亿股，市值 %.2f 亿）==="
          % (PRICE, SHARES, MKT_CAP))
    print("\n[1] 经调整净现金")
    print("  合并：现金类 %.2f − 受限 %.2f − 有息负债 %.2f − 应付少数股东股利 %.2f = %.2f 亿（租赁负债 %.2f 不扣）"
          % (CONS_CASH + CONS_TFA, RESTRICTED, CONS_DEBT, DIV_PAYABLE_MIN, CONS_NET_CASH, LEASE_LIAB))
    print("  母公司本部净现金 %.2f；子公司合计净现金 %.2f × 穿透比例 %.4f = %.2f"
          % (PARENT_NET_CASH, SUB_NET_CASH, S_SUB, S_SUB * SUB_NET_CASH))
    print("  归母穿透 %.2f − 商业公司减资 %.2f − 经营备付 %.2f + 关联方存款 %.2f = 经调整净现金 %.2f 亿（%.2f 元/股）"
          % (ATTR_NET_CASH_GROSS, SHANGYE_REDUCTION * SHANGYE_STAKE_AFTER, OP_RESERVE,
             RELATED_DEPOSIT, NET_CASH_ADJ, NET_CASH_ADJ / SHARES))
    print("\n[2] 2026 归母净利")
    print("  报表估计：H1 %.2f + Q3E %.2f + Q4E %.2f = %.2f；剔除非经常 %.2f、超额利息 %.2f → 核心 %.2f"
          % (H1_2026, Q3_2026E, Q4_2026E, NP_2026E, NONREC_2026E, EXCESS_INT_2026, NP_2026E_CORE))
    for k in ("bear", "base", "bull"):
        print("  正常化 %-4s %.1f 亿（其中税后净利息 %.2f，经营性 %.2f）" % (
            k, NORM_NP_2026[k], NET_INT, NORM_NP_2026[k] - NET_INT))
    print("\n[3] 三情景（股权成本 %.0f%%）" % (COE * 100))
    for k in ("bear", "base", "bull"):
        d = scenario_value(k, detail=True)
        s = SCEN[k]
        print("  %s：V = %.2f 元/股（股权 %.1f 亿：经营现值 %.1f + 终值现值 %.1f + 2026H2 %.1f + 存货释放 %.1f + 净现金 %.1f；终值占比 %.0f%%）"
              % (k, d["v"], d["equity"], d["pv_ops"], d["pv_tv"], d["pv_h2"], d["pv_rel"],
                 NET_CASH_ADJ, d["tv_share"] * 100))
        for y, g, npo, reinv, oe in d["rows"]:
            print("     %d 增速 %+5.1f%% 经营性归母 %.2f 再投资率 %4.1f%% 所有者收益 %.2f"
                  % (y, g * 100, npo, reinv * 100, oe))
        print("     终值：g=%.1f%%，增量回报 %.0f%%，再投资率 %.1f%%，OE_2032 %.2f，TV %.1f"
              % (s["g_term"] * 100, s["r_inc"] * 100, s["g_term"] / s["r_inc"] * 100, d["oe_t"], d["tv"]))
    vw = weighted()
    print("\n  概率加权 V = %.2f 元/股（熊 %.0f%% / 基 %.0f%% / 牛 %.0f%%）；P/V = %.2f"
          % (vw, PROB["bear"] * 100, PROB["base"] * 100, PROB["bull"] * 100, PRICE / vw))
    print("  分档价格（V 不变）：≤%.2f 明显低估；%.2f–%.2f 温和低估；%.2f–%.2f 大致合理；>%.2f 偏贵"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print("\n[4] 敏感性与隐含回报")
    for c in (0.08, 0.10):
        print("  股权成本 %.0f%%：熊 %.2f / 基 %.2f / 牛 %.2f → 加权 %.2f（P/V %.2f）"
              % (c * 100, scenario_value("bear", c), scenario_value("base", c),
                 scenario_value("bull", c), weighted(c), PRICE / weighted(c)))
    irr = implied_irr()
    print("  现价隐含回报（基准情景现金流）= %.2f%%" % (irr * 100))
    g_oe, oe0 = reverse_oe_10y()
    print("  反向 DCF（常规）：所有者收益自 %.2f 亿起，现价隐含 2027-2036 年增 %.1f%%，之后 2.5%%"
          % (oe0, g_oe * 100))
    g10, best = reverse_dcf_10y()
    if g10 is None:
        print("  反向 DCF（增量回报 14%%）：无解，最高可达经营现值 %.1f 亿（g=%.1f%%）" % (best[0], best[1] * 100))
    else:
        print("  反向 DCF：现价隐含 2027-2036 经营性归母利润年增 %.1f%%（再投资 = g/14%%，之后 2.5%%）" % (g10 * 100))
    g10b, _ = reverse_dcf_10y(r_inc=0.30)
    if g10b is not None:
        print("  反向 DCF（增量回报 30%%）：现价隐含 10 年年增 %.1f%%" % (g10b * 100))
    print("  反向 DCF（不计再投资的永续增速）：%.2f%%" % (reverse_perpetual() * 100))
    print("\n[5] 交叉验证")
    so = sotp()
    print("  分部加总：科技 46.85%% 市值 %.1f + 国药直接 33.62%% 市值 %.1f + 商业 57.50%% 评估 %.1f + 其他子公司 %.1f + 母公司净现金(扣备付3) %.1f + 母公司本部经营 %.1f×%.1f=%.1f"
          % (so["kj"], so["gy"], so["sy"], so["oth"], so["cash"], PARENT_OPS_NORM, so["mult"], so["ops"]))
    print("    合计 %.1f 亿 = %.2f 元/股；现价隐含母公司本部经营价值 %.1f 亿 = 本部正常化利润 %.1f 倍、2026E %.1f 倍"
          % (so["total"], so["v"], so["implied_parent_ops"], so["implied_parent_ops"] / PARENT_OPS_NORM,
             so["implied_parent_ops"] / PARENT_OPS_NP["2026E"]))
    print("    母公司本部经营利润（不含子公司股利与利息，税后）：2024 %.2f，2025 %.2f，2026E %.2f"
          % (PARENT_OPS_NP["2024"], PARENT_OPS_NP["2025"], PARENT_OPS_NP["2026E"]))
    hp = sorted(HIST_PE)
    med = (hp[5] + hp[6]) / 2
    print("  历史 PE（2014-2025 年末）区间 %.1f–%.1f，中位 %.1f；按基准正常化 %.1f 亿：%.2f–%.2f 元/股；现价对应 TTM %.1f 倍、正常化 %.1f 倍"
          % (hp[0], hp[-1], med, NORM_NP_2026["base"], hp[0] * NORM_NP_2026["base"] / SHARES,
             med * NORM_NP_2026["base"] / SHARES, MKT_CAP / NP_TTM, MKT_CAP / NORM_NP_2026["base"]))
    op_eq = GM_EQ - NET_CASH_ADJ
    op_roe = (NORM_NP_2026["base"] - NET_INT) / op_eq
    pb_just = (op_roe - 0.03) / (COE - 0.03)
    print("  PB：现价 %.2f 倍；经营性 ROE %.1f%%（经营权益 %.1f 亿），9%%/3%% 下合理经营 PB %.2f → %.2f 元/股"
          % (MKT_CAP / GM_EQ, op_roe * 100, op_eq, pb_just, (pb_just * op_eq + NET_CASH_ADJ) / SHARES))
    print("  同业：东财行业中值 PE(TTM) %.1f 倍 × TTM 归母 %.2f = %.2f 元/股"
          % (PEER_MEDIAN_PE_TTM, NP_TTM, PEER_MEDIAN_PE_TTM * NP_TTM / SHARES))
    ev = MKT_CAP - NET_CASH_ADJ
    ebit_norm = (NORM_NP_2026["base"] - NET_INT) / 0.80
    print("  归母口径 EV %.1f 亿 / 正常化经营 EBIT %.1f 亿 = %.1f 倍" % (ev, ebit_norm, ev / ebit_norm))
    print("  股息率 %.2f%%（每股 %.2f 元，无回购）" % (DPS / PRICE * 100, DPS))
    print("\n[6] 证伪条件触发后的 V")
    f1 = scenario_value("bear")
    f2 = scenario_value("bear", norm_np=8.0, extra_one_off={2027: -1.0})
    f3 = 0.5 * scenario_value("bear") + 0.5 * scenario_value("base")
    f4 = scenario_value("bull")
    f5 = weighted_variant(release_scale=0.0, extra_one_off={2027: -1.5})
    print("  F1 2026 年扣非归母 < 8.5 亿 → 熊市 V %.2f" % f1)
    print("  F2 同仁堂双天然安宫建议零售价下调 ≥20%% → V %.2f" % f2)
    print("  F3 前三季度归母 < 8.8 亿（Q3 < 1.55 亿）→ 熊/基各半 V %.2f" % f3)
    print("  F4 2027 年归母 ≥ 13.5 亿且心脑血管类收入转正 → 牛市 V %.2f" % f4)
    print("  F5 2026 年末存货 ≥ 90 亿或全年资产减值 ≥ 2 亿 → 不计存货释放、再减 1.5 亿 V %.2f" % f5)
    print("\n[汇总] 熊 %.2f / 基 %.2f / 牛 %.2f；加权 V %.2f；P/V %.2f；8%% %.2f；10%% %.2f；隐含回报 %.2f%%"
          % (scenario_value("bear"), scenario_value("base"), scenario_value("bull"), vw, PRICE / vw,
             weighted(0.08), weighted(0.10), irr * 100))
    print("  V 对应估值：加权 V 的 PE（正常化基准）%.1f 倍、PB %.2f 倍；现价隐含 TTM PE %.1f 倍"
          % (vw * SHARES / NORM_NP_2026["base"], vw * SHARES / GM_EQ, MKT_CAP / NP_TTM))


if __name__ == "__main__":
    main()
