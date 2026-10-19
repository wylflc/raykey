#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
000408 藏格矿业 —— OI-291 b01 池内独立估值（深度版）

运行：python3 valuation.py
单位：金额亿元；每股价值元；商品价格为 2026 年不变价，名义值按每年 2% 通胀（价格与成本同步）。

方法：分部加总（SOTP）。每个分部按归母口径的所有者收益逐年折现（股权成本 9%，另报 8%／10%）。
  1. 巨龙铜业 30.78%：二期 30～36 万吨/年铜（二期 2024-02 核准、服务期最长约 36 年，按 28/32/34 年），
     单吨净利由 2025 年与 2026 年前三季度实际数反推的成本结构计算；
     三期（约 60 万吨/年）未获批，按概率 × NPV 计期权价值，扣除按股比承担的资本开支。
  2. 察尔汗钾肥：保有 KCl 资源量 2,309.66 万吨、设计 120 万吨/年，采矿权有效期至 2029-12-01，
     按资源寿命逐年递减，2030 年起乘续期概率并加计出让收益。
  3. 察尔汗碳酸锂：原料为钾肥老卤，产量随钾肥同比例变化，寿命相同。
  4. 麻米错盐湖 26.95%（经江苏藏青基金穿透）：一期 5 万吨/年，按可采资源量耗竭；二期按概率计。
  5. 国能矿业 14.74%（扩募后穿透）、老挝钾盐 70%、Kanga 69%、其他权益投资：按账面倍数。
  6. 经调整净现金（2026-09-30），扣除 Kanga 应付对价。
商品价格：长期价按情景（概率 25/50/25）；2026Q4 用近期价，2027 年按 fade 系数向长期价回归，2028 年起取长期价。
"""

PRICE = 73.75            # 2026-10-19 收盘，元
SHARES = 15.6891         # 亿股，总股本（含回购专户 0.0503 亿股）
MKT_CAP = PRICE * SHARES
COE = 0.09
INFL = 0.02
T_OFF = 0.30             # 估值日 2026-10-19 ≈ 2026.80；Y 年年中现金流折现期数 = Y - 2026 - 0.30
Q4_T = 0.30              # 2026Q4 现金流折现期数

# ---------------- 巨龙铜业成本结构（由实际数反推） ----------------
JL_STAKE = 0.3078
JL_ADJ = 0.993           # 投资收益 / (净利润×持股)：47.08 /(153.98×30.78%)
FX = 7.7                 # 沪铜含税价(元/吨) ≈ LME(美元/吨) × 7.7（2026-08/09 沪铜 10.8～11.0 万对 LME 1.43～1.45 万美元）
K_CU = 0.85              # 铜精矿计价：含税价 ÷1.13 × 计价系数约 0.96
TAX_JL = 0.15
JL_2025 = dict(rev=166.63, np=91.41, cu=19.37)    # 2025 年报第 30 页
JL_9M26 = dict(rev=249.58, np=153.98, cu=21.65)   # 2026 三季报第 7 页


def calibrate_julong():
    """解 成本 = F×销量 + r×收入，税前利润 = 净利润/(1-15%)。"""
    c1 = JL_2025["rev"] - JL_2025["np"] / (1 - TAX_JL)
    c2 = JL_9M26["rev"] - JL_9M26["np"] / (1 - TAX_JL)
    # c1 = F*q1 + r*R1 ; c2 = F*q2 + r*R2
    q1, r1, q2, r2 = JL_2025["cu"], JL_2025["rev"], JL_9M26["cu"], JL_9M26["rev"]
    roy = (c2 - c1 * q2 / q1) / (r2 - r1 * q2 / q1)
    fix = (c1 - roy * r1) / q1
    return roy, fix


ROY, F_CAL = calibrate_julong()   # 约 3.7% 与 2.73 万元/吨


def jl_np_t(lme, byp, fix):
    """巨龙单吨铜净利（万元/吨，2026 不变价）。byp=钼银副产品折每吨铜收入（万元）。"""
    rev_t = K_CU * lme * FX / 1e4 + byp
    return (rev_t * (1 - ROY) - fix) * (1 - TAX_JL)


# ---------------- 近期价格（只用于 2026Q4 与 2027 过渡） ----------------
SPOT = dict(lme=14750.0, byp=2.8, kcl=3050.0, li=11.0)
# LME 2026-10-14 现货约 14,751 美元/吨；副产品 2.8 万元/吨铜为 2026Q3 反推值；
# 氯化钾 2026Q3 含税均价 3,041.59 元/吨；碳酸锂 10-09 现货 11.85～12.2 万、10-12 期货 10.47 万，取 11.0 万含税。

# ---------------- 资产负债表（2026-09-30，三季报第 8～9 页） ----------------
NET_CASH_ITEMS = {
    "货币资金": 41.434,
    "减：受限资金（货币资金−现金等价物）": -0.172,
    "应收巨龙已宣告股利": 15.390,
    "交易性金融资产（理财）": 1.400,
    "一年内到期非流动资产（质押存单/债权投资）": 2.404,
    "减：一年内到期非流动负债（借款）": -2.380,
    "减：租赁负债": -0.147,
    "减：预计负债（弃置/恢复治理，类债务）": -3.714,
    "减：经营备付（约一季度付现成本）": -4.000,
}
KANGA_COST = 8.68        # Kanga 92% 收购中公司 75% 份额对价 1.2828 亿美元（2026-09-18 公告第 2 页）
NET_CASH_PRE = sum(NET_CASH_ITEMS.values())
NET_CASH = NET_CASH_PRE - KANGA_COST
ZIJIN_FIN_DEPOSIT_H1 = 15.89   # 紫金财务公司存款（2026 中报第 37 页），含在货币资金内，单列不扣减

GN_BOOK = 19.97          # 国能矿业穿透净值：37.79% × 西藏藏青基金扩募后净值(36.84+16.0)
OTHER_EQ = 1.32          # 其他权益工具投资

SC = {
    "bear": dict(
        p=0.25, lme=9000.0, byp=1.5, fix=2.85, fade=0.3,
        jl_v27=29.0, jl_v=30.0, jl_life=28, ctrl=0.10,
        ph3_p=0.25, ph3_start=2034, ph3_add=27.0, ph3_capex=450.0, ph3_life=28,
        kcl_p=2400.0, kcl_c=1080.0, kcl_v0=95.0, kcl_flat_to=2029, kcl_decl=0.10, kcl_end=2036,
        renew_p=0.70, royal_new=0.03, tax_late=0.25, da_adj=0.0,
        li_p=7.0, li_c=3.9, li_v=1.10,
        mm_v27=3.5, mm_v=4.0, mm_c=4.4, mm_R=100.0, mm_hair=0.30,
        mm2_p=0.0, mm2_start=2031, mm2_capex=55.0,
        gn_mult=0.5, laos=0.0, kanga_mult=0.5,
    ),
    "base": dict(
        p=0.50, lme=11000.0, byp=2.0, fix=F_CAL, fade=0.5,
        jl_v27=31.5, jl_v=33.0, jl_life=32, ctrl=0.05,
        ph3_p=0.50, ph3_start=2032, ph3_add=27.0, ph3_capex=400.0, ph3_life=30,
        kcl_p=2750.0, kcl_c=1000.0, kcl_v0=100.0, kcl_flat_to=2030, kcl_decl=0.06, kcl_end=2040,
        renew_p=0.85, royal_new=0.02, tax_late=0.20, da_adj=1.0,
        li_p=9.5, li_c=3.5, li_v=1.30,
        mm_v27=4.8, mm_v=5.0, mm_c=3.9, mm_R=130.0, mm_hair=0.20,
        mm2_p=0.4, mm2_start=2030, mm2_capex=50.0,
        gn_mult=1.0, laos=3.0, kanga_mult=1.0,
    ),
    "bull": dict(
        p=0.25, lme=13500.0, byp=2.5, fix=2.65, fade=0.6,
        jl_v27=33.0, jl_v=36.0, jl_life=34, ctrl=0.0,
        ph3_p=0.75, ph3_start=2031, ph3_add=28.0, ph3_capex=350.0, ph3_life=30,
        kcl_p=3100.0, kcl_c=980.0, kcl_v0=102.0, kcl_flat_to=2032, kcl_decl=0.04, kcl_end=2045,
        renew_p=0.95, royal_new=0.015, tax_late=0.15, da_adj=1.5,
        li_p=13.0, li_c=3.3, li_v=1.50,
        mm_v27=5.2, mm_v=5.5, mm_c=3.6, mm_R=150.0, mm_hair=0.10,
        mm2_p=0.7, mm2_start=2029, mm2_capex=45.0,
        gn_mult=1.8, laos=15.0, kanga_mult=1.3,
    ),
}

HQ_COST = 0.80           # 母公司及未分摊费用（税前，亿/年）
KCL_SGA = 2.0
LI_SGA = 0.5
LAST_YEAR = 2100         # 永续项（总部费用）截断年


def infl(y):
    return (1 + INFL) ** (y - 2026)


def disc(y, r):
    return (1 + r) ** (-(y - 2026 - T_OFF))


def px(s, key_lt, key_spot, y):
    """y 年商品价格（2026 不变价）：2027 年 = 长期价 + fade×(近期价-长期价)，2028 起长期价。"""
    lt = s[key_lt]
    if y == 2027:
        return lt + s["fade"] * (SPOT[key_spot] - lt)
    return lt


# ---------------- 巨龙 ----------------
def julong_share_np(y, s, vol, use_ctrl=True):
    lme = px(s, "lme", "lme", y)
    byp = px(s, "byp", "byp", y)
    npt = jl_np_t(lme, byp, s["fix"])
    share = JL_STAKE * JL_ADJ * ((1 - s["ctrl"]) if use_ctrl else 1.0)
    return vol * npt * share * infl(y)


def julong_ph2(s, r):
    pv = 0.0
    flows = {}
    for y in range(2027, 2027 + s["jl_life"]):
        v = s["jl_v27"] if y == 2027 else s["jl_v"]
        f = julong_share_np(y, s, v)
        flows[y] = f
        pv += f * disc(y, r)
    return pv, flows


def julong_ph3_npv(s, r):
    """三期增量：投产前 4 年平均投入资本开支（按 30.78% 承担），首年产量 50%。"""
    st = s["ph3_start"]
    pv = 0.0
    flows = {}
    capex_share = s["ph3_capex"] * JL_STAKE * (1 - s["ctrl"])
    for k in range(4):
        y = st - 4 + k
        f = -capex_share / 4 * infl(y)
        flows[y] = flows.get(y, 0) + f
    for k in range(s["ph3_life"]):
        y = st + k
        v = s["ph3_add"] * (0.5 if k == 0 else 1.0)
        flows[y] = flows.get(y, 0) + julong_share_np(y, s, v)
    for y, f in flows.items():
        pv += f * disc(y, r)
    return pv, flows


# ---------------- 察尔汗钾肥与碳酸锂 ----------------
def kcl_vol(y, s):
    if y > s["kcl_end"]:
        return 0.0
    if y <= s["kcl_flat_to"]:
        return s["kcl_v0"]
    return s["kcl_v0"] * (1 - s["kcl_decl"]) ** (y - s["kcl_flat_to"])


def own_ops_oe(y, s, kcl_price=None, li_price=None, tax_override=None, royal=True, renewal=True):
    """钾肥＋碳酸锂所有者收益（亿，名义）。"""
    v = kcl_vol(y, s)
    if v <= 0:
        return 0.0, 0.0
    kp = px(s, "kcl_p", "kcl", y) if kcl_price is None else kcl_price
    lp = px(s, "li_p", "li", y) if li_price is None else li_price
    tax = 0.15 if y <= 2030 else s["tax_late"]
    if tax_override is not None:
        tax = tax_override
    # 钾肥：单位成本 50% 固定、50% 变动（参照 100 万吨）
    rev = v * kp / 1.09 / 1e4
    cost = s["kcl_c"] * (0.5 * 100.0 + 0.5 * v) / 1e4
    roy_new = s["royal_new"] * rev if (royal and y >= 2030) else 0.0
    ebit_k = rev * (1 - 0.08 - 0.01) - cost - roy_new - KCL_SGA
    # 碳酸锂：老卤随钾肥产量同比例
    li_v = s["li_v"] * v / s["kcl_v0"]
    li_rev = li_v * lp / 1.13
    roy_li = s["royal_new"] * li_rev if (royal and y >= 2030) else 0.0
    ebit_l = li_v * (lp / 1.13 - s["li_c"] - 0.30) - roy_li - LI_SGA
    oe_k = max(0.0, ebit_k * (1 - tax) + 0.7 * s["da_adj"])   # 亏损年份视为停产（弃置费已在净现金中扣除）
    oe_l = max(0.0, ebit_l * (1 - tax) + 0.3 * s["da_adj"])
    f = infl(y)
    rp = s["renew_p"] if (renewal and y >= 2030) else 1.0
    return oe_k * f * rp, oe_l * f * rp


def own_ops_pv(s, r):
    pk = pl = 0.0
    fk, fl = {}, {}
    for y in range(2027, s["kcl_end"] + 1):
        k, l = own_ops_oe(y, s)
        fk[y], fl[y] = k, l
        pk += k * disc(y, r)
        pl += l * disc(y, r)
    return pk, pl, fk, fl


# ---------------- 麻米错 ----------------
MM_LOOK = 0.2695


def mm_profile(s, with_ph2):
    rem = s["mm_R"]
    vols = {}
    y = 2027
    while rem > 1e-9 and y < 2090:
        v = s["mm_v27"] if y == 2027 else s["mm_v"]
        if with_ph2 and y >= s["mm2_start"]:
            v += 5.0
        v = min(v, rem)
        vols[y] = v
        rem -= v
        y += 1
    return vols


def mm_flow(y, v, s, li_price=None):
    lp = px(s, "li_p", "li", y) if li_price is None else li_price
    np100 = v * (lp / 1.13 - s["mm_c"]) * 0.85 - (0.5 if y <= 2035 else 0.0)
    return np100 * MM_LOOK * (1 - s["mm_hair"]) * infl(y)


def mm_pv(s, r, with_ph2=False):
    pv = 0.0
    flows = {}
    for y, v in mm_profile(s, with_ph2).items():
        f = mm_flow(y, v, s)
        flows[y] = f
        pv += f * disc(y, r)
    if with_ph2:
        for k in range(2):
            y = s["mm2_start"] - 2 + k
            f = -s["mm2_capex"] * MM_LOOK / 2 * infl(y)
            flows[y] = flows.get(y, 0) + f
            pv += f * disc(y, r)
    return pv, flows


# ---------------- 2026Q4（近期价，三情景相同） ----------------
def q4_2026():
    jl = 8.85 * jl_np_t(SPOT["lme"], SPOT["byp"], F_CAL) * JL_STAKE * JL_ADJ   # 全年指引 30～31 万吨减前三季度 21.65
    kcl = (31.0 * (SPOT["kcl"] / 1.09 * (1 - 0.09) - 1000.0) / 1e4 - 0.5) * 0.85  # 年度销量计划 104 万吨减前三季度 72.94
    li = (0.35 * (SPOT["li"] / 1.13 - 3.5 - 0.30) - 0.125) * 0.85
    mm = 1.5 * (SPOT["li"] / 1.13 - 3.9) * 0.85 * MM_LOOK * 0.8                  # 三季度末库存约 0.86 万吨＋四季度产量；基金层折扣 20%
    hq = -HQ_COST / 4 * 0.85
    tot = jl + kcl + li + mm + hq
    return dict(julong=jl, kcl=kcl, li=li, mamicuo=mm, hq=hq, total=tot)


def hq_pv(r):
    return sum(-HQ_COST * 0.85 * infl(y) * disc(y, r) for y in range(2027, LAST_YEAR + 1))


def value(s, r=COE, detail=False, overrides=None):
    s = dict(s)
    if overrides:
        s.update(overrides)
    q4 = q4_2026()["total"] * (1 + r) ** (-Q4_T)
    jl2, jl2f = julong_ph2(s, r)
    ph3, ph3f = julong_ph3_npv(s, r)
    jl3 = s["ph3_p"] * ph3
    pk, pl, fk, fl = own_ops_pv(s, r)
    mm1, mm1f = mm_pv(s, r, False)
    mm2_full, _ = mm_pv(s, r, True)
    mm2 = s["mm2_p"] * max(0.0, mm2_full - mm1)
    hq = hq_pv(r)
    other = s["gn_mult"] * GN_BOOK + s["laos"] + s["kanga_mult"] * KANGA_COST + OTHER_EQ
    eq = q4 + jl2 + jl3 + pk + pl + mm1 + mm2 + hq + other + NET_CASH
    out = dict(q4=q4, julong_ph2=jl2, julong_ph3=jl3, ph3_npv_full=ph3, kcl=pk, li=pl, mamicuo1=mm1,
               mamicuo2=mm2, hq=hq, other=other, net_cash=NET_CASH, equity=eq, v=eq / SHARES)
    if detail:
        out.update(flows=dict(jl2=jl2f, ph3=ph3f, kcl=fk, li=fl, mm1=mm1f))
    return out


def weighted(r=COE, overrides=None):
    return sum(SC[k]["p"] * value(SC[k], r, overrides=overrides)["v"] for k in SC)


def solve(f, lo, hi, target=0.0, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------- 正常化 2026 归母净利（长期价 × 2026 年量，剔除一次性） ----------------
def normalized_np_2026(s):
    jl = 30.5 * jl_np_t(s["lme"], s["byp"], s["fix"]) * JL_STAKE * JL_ADJ
    v = 103.0                                   # 2026 销量约 103 万吨（前三季度 72.94，全年计划 104）
    rev = v * s["kcl_p"] / 1.09 / 1e4
    cost = s["kcl_c"] * (0.5 * 100 + 0.5 * v) / 1e4
    kcl = (rev * 0.91 - cost - KCL_SGA) * 0.85
    li = (1.27 * (s["li_p"] / 1.13 - s["li_c"] - 0.30) - LI_SGA) * 0.85       # 2026 销量约 1.27 万吨（前三季度 0.921）
    mm = (1.70 * (s["li_p"] / 1.13 - s["mm_c"]) * 0.85 - 0.5) * MM_LOOK        # 麻米错 2026 销量约 1.7 万吨（三季度 0.19＋四季度约 1.5）
    other = -HQ_COST * 0.85 - 0.40 - 0.30 + 0.35  # 总部；基金管理费等（份额）；老挝亏损；净利息税后
    return dict(julong=jl, kcl=kcl, li=li, mamicuo=mm, other=other, total=jl + kcl + li + mm + other)


def base_oe_path(r=COE):
    """基准情景所有者收益（不含三期与麻米错二期期权），名义值。"""
    s = SC["base"]
    _, jlf = julong_ph2(s, r)
    _, _, fk, fl = own_ops_pv(s, r)
    _, mmf = mm_pv(s, r, False)
    hq = {y: -HQ_COST * 0.85 * infl(y) for y in range(2027, LAST_YEAR + 1)}
    path = {}
    for y in range(2027, 2042):
        path[y] = jlf.get(y, 0) + fk.get(y, 0) + fl.get(y, 0) + mmf.get(y, 0) + hq.get(y, 0)
    return path


def normalized_oe_2027_base():
    """2027 年按长期价（不含过渡回归）的基准所有者收益。"""
    s = dict(SC["base"])
    s["fade"] = 0.0
    jl = julong_share_np(2027, s, s["jl_v27"])
    k, l = own_ops_oe(2027, s)
    mm = mm_flow(2027, s["mm_v27"], s)
    return jl + k + l + mm - HQ_COST * 0.85 * infl(2027)


def reverse_dcf(r=COE):
    s = SC["base"]
    x = normalized_oe_2027_base()
    nonop = s["gn_mult"] * GN_BOOK + s["laos"] + s["kanga_mult"] * KANGA_COST + OTHER_EQ
    target = MKT_CAP - NET_CASH - nonop - q4_2026()["total"] * (1 + r) ** (-Q4_T)

    def pv_g(g, gt=0.02):
        pv = 0.0
        f = x
        for t in range(1, 11):
            pv += f * (1 + r) ** (-(t - T_OFF))
            f_last = f
            f *= (1 + g)
        tv = f_last * (1 + gt) / (r - gt)
        return pv + tv * (1 + r) ** (-(10 - T_OFF))

    g10 = solve(pv_g, -0.30, 0.40, target)
    g_perp = r - x * (1 + r) ** T_OFF / target
    return dict(oe2027=x, target=target, g10=g10, g_perp=g_perp)


def main():
    print("=" * 78)
    print("000408 藏格矿业 独立估值（价格日 2026-10-19，现价 %.2f 元，总股本 %.4f 亿股，市值 %.1f 亿）"
          % (PRICE, SHARES, MKT_CAP))
    print("巨龙成本反推：随收入税费比例 r = %.2f%%，单位固定成本 F = %.3f 万元/吨铜" % (ROY * 100, F_CAL))
    for k in SC:
        s = SC[k]
        print("  %-4s 长期 LME %6.0f 美元/吨（沪铜 %.2f 万）→ 巨龙单吨净利 %.2f 万元/吨"
              % (k, s["lme"], s["lme"] * FX / 1e4, jl_np_t(s["lme"], s["byp"], s["fix"])))
    print("  近期 LME %6.0f → 单吨净利 %.2f 万元/吨（2026Q3 实际 61.75 亿/8.30 万吨 = 7.44）"
          % (SPOT["lme"], jl_np_t(SPOT["lme"], SPOT["byp"], F_CAL)))
    print("-" * 78)
    print("经调整净现金（亿）：")
    for k, v in NET_CASH_ITEMS.items():
        print("  %-40s %8.2f" % (k, v))
    print("  %-40s %8.2f" % ("小计", NET_CASH_PRE))
    print("  %-40s %8.2f" % ("减：Kanga 应付对价（公司份额）", -KANGA_COST))
    print("  %-40s %8.2f   （其中紫金财务公司存款 2026-06-30 为 %.2f，单列不扣）" % ("经调整净现金", NET_CASH, ZIJIN_FIN_DEPOSIT_H1))
    q4 = q4_2026()
    print("2026Q4 所有者收益（近期价）：" + "，".join("%s %.2f" % (k, v) for k, v in q4.items()))
    print("-" * 78)
    hdr = "%-6s %6s %8s %8s %8s %7s %7s %7s %7s %7s %7s %8s %7s %7s" % (
        "情景", "概率", "Q4", "巨龙二期", "三期×p", "钾肥", "锂", "麻米一期", "麻米二期", "总部", "其他", "净现金", "合计", "V")
    print(hdr)
    res = {}
    for k in SC:
        o = value(SC[k])
        res[k] = o
        print("%-6s %6.2f %8.1f %8.1f %8.1f %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %8.1f %7.0f %7.2f" % (
            k, SC[k]["p"], o["q4"], o["julong_ph2"], o["julong_ph3"], o["kcl"], o["li"], o["mamicuo1"],
            o["mamicuo2"], o["hq"], o["other"], o["net_cash"], o["equity"], o["v"]))
    vw = weighted()
    print("-" * 78)
    print("概率加权独立 V = %.2f 元/股；P/V = %.3f" % (vw, PRICE / vw))
    pv = PRICE / vw
    band = "明显低估" if pv <= 0.75 else ("温和低估" if pv <= 0.90 else ("大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"))
    print("分档：%s；V 不变时 P/V=0.75/0.90/1.10 对应价格 %.2f / %.2f / %.2f 元" % (band, 0.75 * vw, 0.90 * vw, 1.10 * vw))
    v8, v10 = weighted(0.08), weighted(0.10)
    print("股权成本敏感性：8%% → V %.2f（P/V %.3f）；10%% → V %.2f（P/V %.3f）" % (v8, PRICE / v8, v10, PRICE / v10))
    for k in SC:
        print("  %-4s 8%%: %.2f  9%%: %.2f  10%%: %.2f" % (k, value(SC[k], 0.08)["v"], res[k]["v"], value(SC[k], 0.10)["v"]))
    irr_base = solve(lambda r: value(SC["base"], r)["v"], 0.03, 0.30, PRICE)
    irr_w = solve(lambda r: weighted(r), 0.03, 0.30, PRICE)
    print("现价隐含回报（基准情景现金流）= %.2f%%；（概率加权现金流）= %.2f%%" % (irr_base * 100, irr_w * 100))
    rd = reverse_dcf()
    print("反向 DCF：基准 2027 正常化所有者收益 %.1f 亿；现价对应经营部分 %.0f 亿；"
          % (rd["oe2027"], rd["target"]))
    print("  隐含前 10 年所有者收益年增速 %.2f%%（其后 2%% 永续）；或隐含永续增速 %.2f%%"
          % (rd["g10"] * 100, rd["g_perp"] * 100))
    lme_imp = solve(lambda x: value(SC["base"], overrides=dict(lme=x))["v"], 6000.0, 20000.0, PRICE)
    print("  商品口径：基准其他假设不变，现价隐含长期 LME 铜价 %.0f 美元/吨（2026 不变价，沪铜约 %.2f 万元）"
          % (lme_imp, lme_imp * FX / 1e4))
    print("-" * 78)
    print("2026 正常化归母净利（长期价 × 2026 年量，剔除一次性）：")
    for k in SC:
        n = normalized_np_2026(SC[k])
        print("  %-4s 合计 %.1f 亿（巨龙 %.1f，钾肥 %.1f，锂 %.1f，麻米错 %.1f，其他 %.1f）"
              % (k, n["total"], n["julong"], n["kcl"], n["li"], n["mamicuo"], n["other"]))
    path = base_oe_path()
    nb = normalized_np_2026(SC["base"])["total"]
    prev = nb
    gr = []
    print("基准所有者收益路径（不含期权，名义亿元）：")
    for y in range(2027, 2032):
        g = path[y] / prev - 1
        gr.append(g)
        print("  %d  %.1f  （增速 %+.1f%%）" % (y, path[y], g * 100))
        prev = path[y]
    print("  2036 %.1f；2041 %.1f" % (path[2036], path[2041]))
    # 终值占比：2036 年后现金流现值 / 经营现值（基准）
    o = value(SC["base"], detail=True)
    fl = o["flows"]
    late = early = 0.0
    for key in ("jl2", "kcl", "li", "mm1"):
        for y, f in fl[key].items():
            d = f * disc(y, COE)
            if y > 2036:
                late += d
            else:
                early += d
    ph3_late = sum(f * disc(y, COE) for y, f in fl["ph3"].items() if y > 2036) * SC["base"]["ph3_p"]
    ph3_early = sum(f * disc(y, COE) for y, f in fl["ph3"].items() if y <= 2036) * SC["base"]["ph3_p"]
    late += ph3_late
    early += ph3_early
    print("基准经营现值中 2036 年以后占比 = %.1f%%" % (late / (late + early) * 100))
    # 再投资与增量回报（基准）
    s = SC["base"]
    capex_ph3 = s["ph3_p"] * s["ph3_capex"] * JL_STAKE
    capex_mm2 = s["mm2_p"] * s["mm2_capex"] * MM_LOOK
    oe_sum = sum(path[y] for y in range(2027, 2032))
    reinv_rate = (capex_ph3 + capex_mm2) / oe_sum
    inc_oe = s["ph3_add"] * jl_np_t(s["lme"], s["byp"], s["fix"]) * JL_STAKE * JL_ADJ
    inc_ret = inc_oe / (s["ph3_capex"] * JL_STAKE)
    print("基准再投资率（2027-2031 期望增长性资本开支 / 所有者收益）= %.1f%%；三期增量回报（达产年税后/投入）= %.1f%%"
          % (reinv_rate * 100, inc_ret * 100))
    print("-" * 78)
    print("证伪条件触发后的 V（其余取基准，概率加权口径为单一情景）：")
    fz = {
        "F1 铜长期价落到熊市（LME 9,000 美元，副产品 1.5 万）": value(SC["base"], overrides=dict(lme=9000.0, byp=1.5, fix=2.85))["v"],
        "F2 巨龙三期 2028 年底前未获批（三期概率 0）": value(SC["base"], overrides=dict(ph3_p=0.0))["v"],
        "F3 察尔汗采矿权 2029-12-01 未续期（2030 起钾锂归零）": value(SC["base"], overrides=dict(renew_p=0.0))["v"],
        "F4 碳酸锂长期价 7 万元（含税）且麻米错 2027 年产 <3.5 万吨": value(SC["base"], overrides=dict(li_p=7.0, mm_v27=3.5, mm_v=4.0, mm2_p=0.0))["v"],
        "F5 巨龙分红受限（控制权折价 20%）": value(SC["base"], overrides=dict(ctrl=0.20))["v"],
    }
    for k, v in fz.items():
        print("  %-55s V = %.2f" % (k, v))
    # 铜价敏感性
    print("铜长期价敏感性（基准其他假设）：")
    for lme in (9000, 10000, 10700, 11000, 12000, 13000, 14750):
        print("  LME %5d → V %.2f" % (lme, value(SC["base"], overrides=dict(lme=float(lme)))["v"]))
    print("其他单项敏感性（基准其他假设）：")
    sens = [
        ("F2 变体：三期未获批且巨龙 2027 年 29、此后 30 万吨", dict(jl_v27=29.0, jl_v=30.0, ph3_p=0.0)),
        ("巨龙 2027 年 29、此后 30 万吨（三期仍按 50%）", dict(jl_v27=29.0, jl_v=30.0)),
        ("三期概率 65%", dict(ph3_p=0.65)),
        ("三期获批（概率 100%）", dict(ph3_p=1.0)),
        ("取消控制权折价", dict(ctrl=0.0)),
        ("碳酸锂长期价 7 万元", dict(li_p=7.0)),
        ("碳酸锂长期价 12 万元", dict(li_p=12.0)),
        ("碳酸锂长期价 15 万元", dict(li_p=15.0)),
        ("氯化钾长期价 2,400 元", dict(kcl_p=2400.0)),
        ("氯化钾长期价 3,050 元", dict(kcl_p=3050.0)),
        ("2027 年不做价格回归", dict(fade=0.0)),
    ]
    for name, ov in sens:
        print("  %-46s V = %.2f" % (name, value(SC["base"], overrides=ov)["v"]))
    w_ph3 = sum(SC[k]["p"] * value(SC[k], overrides=dict(ph3_p=1.0))["v"] for k in SC)
    print("  三期获批时概率加权 V = %.2f" % w_ph3)
    print("-" * 78)
    print("交叉验证：")
    b = res["base"]
    print("  基准分部每股：Q4 %.2f｜巨龙二期 %.2f｜三期期望 %.2f｜钾肥 %.2f｜锂 %.2f｜麻米错 %.2f｜总部 %.2f｜其他 %.2f｜净现金 %.2f"
          % tuple(x / SHARES for x in (b["q4"], b["julong_ph2"], b["julong_ph3"], b["kcl"], b["li"],
                                       b["mamicuo1"] + b["mamicuo2"], b["hq"], b["other"], b["net_cash"])))
    spot = value(SC["base"], overrides=dict(lme=SPOT["lme"], byp=SPOT["byp"], kcl_p=SPOT["kcl"], li_p=SPOT["li"]))["v"]
    print("  参考（不采用）：基准量 × 近期价长期不变 → V %.2f 元" % spot)
    ex_jl = b["q4"] + b["kcl"] + b["li"] + b["mamicuo1"] + b["mamicuo2"] + b["hq"] + b["other"] + b["net_cash"]
    implied_jl = (MKT_CAP - ex_jl) / JL_STAKE
    jl_2026e = (JL_9M26["np"] + 8.85 * jl_np_t(SPOT["lme"], SPOT["byp"], F_CAL))
    jl_norm = SC["base"]["jl_v"] * jl_np_t(SC["base"]["lme"], SC["base"]["byp"], SC["base"]["fix"])
    print("  现价隐含巨龙 100%% 股权价值 %.0f 亿：2026E 净利 %.0f 亿 → %.1f 倍；基准正常化净利 %.0f 亿 → %.1f 倍"
          % (implied_jl, jl_2026e, implied_jl / jl_2026e, jl_norm, implied_jl / jl_norm))
    nb = normalized_np_2026(SC["base"])["total"]
    nonop = b["other"]
    print("  （市值−净现金−非经营资产）/基准正常化归母净利 = %.1f 倍；市值/2026E 报表归母（前三季度 61.09＋Q4 %.1f）= %.1f 倍"
          % ((MKT_CAP - NET_CASH - nonop) / nb, q4["total"], MKT_CAP / (61.09 + q4["total"])))
    print("  近 12 个月每股派息 2.50 元 → 股息率 %.2f%%；2026 年回购 4.00 亿元（用于员工持股）→ %.2f%%"
          % (2.50 / PRICE * 100, 4.0 / MKT_CAP * 100))
    return res, vw


if __name__ == "__main__":
    main()
