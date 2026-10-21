#!/usr/bin/env python3
"""紫金矿业（601899）独立估值：分矿种价格正常化 + 归母所有者收益 DCF（有杠杆口径）+ 可转债逐券取低。

运行：python3 valuation.py
金额单位：亿元人民币；每股价值：元/股。全部输入写在脚本内，出处见正文「来源」。
价格日 2026-10-21；最新定期报告 2026 中报（三季报预约 2026-10-24）。
"""
from __future__ import annotations

OZ = 31.1035  # 克/盎司

# ---------------------------------------------------------------------------
# 0. 快照（brief.md；腾讯行情 2026-10-21；新浪外汇 2026-10-21 夜盘）
# ---------------------------------------------------------------------------
PRICE_A = 28.87
PRICE_H_HKD = 30.70
HKD_CNY = 0.8508
USD_CNY = 6.676
SHARES = 265.9080          # 亿股，A 206.0179 + H 59.8901（含回购专户 0.7747 亿股）
TREASURY = 0.77474592      # 回购专户 A 股，用于 2026 年员工持股计划（受让价 18.56 元），不注销
ESOP_PRICE = 18.56
COE = 0.09
T_FIRST = 0.69             # 2026-10-21 至 2027 年年中的年数（年中折现）

# ---------------------------------------------------------------------------
# 1. 2026 上半年分产品单位经济（2026H1_report 第 13-14 页，不含非控股企业）
#    (销量, 不含税单价, 单位销售成本)；金、银以克计，其余以吨计
# ---------------------------------------------------------------------------
H1 = {
    "金锭": ("au", 27424e3, 1034.09, 347.30),
    "金精矿": ("au", 16756e3, 961.30, 199.15),
    "铜精矿": ("cu", 353831, 82624, 24480),
    "电积铜": ("cu", 46845, 90734, 36620),
    "电解铜": ("cu", 59120, 90524, 38513),
    "锂盐": ("li", 22021, 130778, 49912),
    "锂精矿": ("li", 14265, 76974, 16307),
    "矿山锌": ("zn", 171897, 17539, 9692),
    "矿山银": ("ag", 225232e3, 13.95, 2.28),
    "铁精矿": ("fe", 52e4, 636, 413.90),
}
# 2026H1 市场均价（2026H1_report 第 7 页）：伦金、伦银（美元/盎司），伦铜、伦锌（美元/吨），国内碳酸锂（元/吨，含税）
MKT_H1 = dict(au=4693.0, ag=79.0, cu=13083.0, zn=3351.0, li=163427.0)
FX_H1 = 1033.0 * OZ / 4693.0   # 国内金价 1,033 元/克 反推的上半年汇率 ≈ 6.846
GP_H1_TOTAL = 1941.785 - 1208.815          # 合并毛利 732.97（第 45 页）
SMELT_H1 = 7.59 + 1.22 - 1.54 + 0.16       # 精炼金、冶炼铜锌、冶炼碳酸锂毛利（第 13-14 页推算）
S_LINK = 0.055      # 营业成本中随价格变动的部分（权益金、矿权出让收益等），由 2025H2→2026H1 单位成本变动反推
TAX_FIXED, TAX_RATE_REV = 10.0, 0.058      # 税金及附加 ≈ 10 + 5.8% × 矿产品收入（2026H1 59.86、2025H1 35.74 校准）
OTHER_OP = 6.5 - 5.0 - 8.0 - 2.6           # 其他收益、减值、营业外净额、手续费（经常性部分）
TAX_ETR = 0.225     # 扣除联营合营收益后的有效税率（2025：22.5%；2026H1：22.6%）
ASSOC_MINORITY = 0.05


def unit_market(metal: str, usd_or_cny: float, fx: float) -> float:
    """市场价折人民币不含税口径：金银为元/克，铜锌为元/吨，锂为元/吨（不含税）。"""
    if metal in ("au", "ag"):
        return usd_or_cny * fx / OZ
    if metal == "li":
        return usd_or_cny / 1.13
    return usd_or_cny * fx


RATIO = {k: (v[2] / unit_market(v[0], MKT_H1[v[0]], FX_H1) if v[0] != "fe" else 1.0) for k, v in H1.items()}

# 2026 全年合并口径销量（上半年实际 + 下半年估计）÷ 上半年销量
VOL_FY = {"au": 92e6 / 44180e3,        # 金 92 吨（上半年 44.18 吨；计划矿产金 105 吨含联营权益）
          "cu": 960000 / 459796,       # 铜 96 万吨（不含卡莫阿、玉龙权益产量）
          "li": 85000 / 36286,         # 当量碳酸锂 8.5 万吨销量
          "zn": 345000 / 171897,
          "ag": 455e6 / 225232e3,
          "fe": 105e4 / 52e4}
VOL_H1X2 = {m: 2.0 for m in VOL_FY}


def pnl(px: dict, fx: float, li_cny: float, other: float, smelt: float, opex: float,
        assoc: float, minority: float, vol: dict = VOL_FY, scale: float = 1.0, cost_mult: float = 1.0) -> dict:
    """给定价格与销量，推算年化（scale=1）或分期（scale<1）的归母经营净利（不含净利息、不含一次性项目）。"""
    gp_mine, rev_mine, seg = 0.0, 0.0, {}
    for k, (m, q, p, c) in H1.items():
        if m == "fe":
            pn = p
        elif m == "li":
            pn = RATIO[k] * unit_market("li", li_cny, fx)
        else:
            pn = RATIO[k] * unit_market(m, px[m], fx)
        cn = (c - S_LINK * p) * cost_mult + S_LINK * pn
        qq = q * vol[m]
        seg[k] = qq * (pn - cn) / 1e8
        gp_mine += seg[k]
        rev_mine += qq * pn / 1e8
    gp = gp_mine + smelt + other
    taxes = TAX_FIXED * scale + TAX_RATE_REV * rev_mine
    pbt = gp - taxes - opex + OTHER_OP * scale + assoc
    parent = (pbt - assoc) * (1 - TAX_ETR) * (1 - minority) + assoc * (1 - ASSOC_MINORITY)
    return dict(seg=seg, gp_mine=gp_mine, rev_mine=rev_mine, gp=gp, taxes=taxes, pbt=pbt, parent=parent)


NET_INT_2026 = 8.0      # 报表口径 2026 年正常化净利息（税前）：利息费用 34.1 + 折现摊销 4.5 − 利息收入 34.3，计入下半年付息与派现
def reported_np(parent_op: float, minority: float) -> float:
    return parent_op - NET_INT_2026 * (1 - TAX_ETR) * (1 - minority)


# ---------------------------------------------------------------------------
# 2. 情景（长期正常化价格，不取现价；汇率 6.70）
# ---------------------------------------------------------------------------
FX_NORM = 6.70
SCEN = {
    "bear": dict(p=0.25, px=dict(au=2800, cu=9000, ag=30, zn=2400), li=65000, other=110, smelt=12, opex=130,
                 assoc=38, minority=0.210, g=[0.05, 0.04, 0.03, 0.02, 0.015], roic=0.12, g_t=0.010, roic_t=0.10,
                 chifeng_np=8.0),
    "base": dict(p=0.50, px=dict(au=3600, cu=11000, ag=45, zn=2800), li=90000, other=140, smelt=15, opex=140,
                 assoc=55, minority=0.215, g=[0.10, 0.08, 0.06, 0.04, 0.03], roic=0.20, g_t=0.020, roic_t=0.12,
                 chifeng_np=29.0),
    "bull": dict(p=0.25, px=dict(au=4400, cu=13500, ag=65, zn=3300), li=130000, other=170, smelt=18, opex=150,
                 assoc=70, minority=0.220, g=[0.13, 0.11, 0.08, 0.06, 0.04], roic=0.25, g_t=0.025, roic_t=0.14,
                 chifeng_np=46.0),
}

# 2026 下半年（7-12 月）：三季度实际与四季度现价的估计；销量 = 全年 − 上半年
H2 = dict(px=dict(au=4150, cu=14250, ag=58, zn=3600), li=115000, fx=6.71, other=85, smelt=8, opex=72,
          assoc=30, minority=0.224, reinvest=0.45)
VOL_H2 = {m: VOL_FY[m] - 1.0 for m in VOL_FY}
Q3 = dict(px=dict(au=4150, cu=14250, ag=60, zn=3500), li=135000, fx=6.75, other=42, smelt=4, opex=36,
          assoc=15, minority=0.224)
VOL_Q3 = {m: VOL_H2[m] / 2 for m in VOL_FY}
NP_H1_REPORTED = 391.698   # 2026H1 归母净利（第 45 页）
NP_Q2_REPORTED = 190.90

# ---------------------------------------------------------------------------
# 3. 资产负债调整（2026-06-30，2026H1_report 附注五）
# ---------------------------------------------------------------------------
CASH = 913.179
RESTRICTED = 4.626 + 20.555 + 1.515 + 0.185          # 闭矿保证金、财务公司法定准备金、保证金、冻结（第 99 页）
TFA_CASHLIKE = 14.433 + 25.979                       # 基金、银行理财及结构性存款（第 100 页）
OCA_CASHLIKE = 58.383 + 21.450 + 1.132               # 大额存单及国债逆回购、期货账户流动资金、基金账户资金（第 116 页）
DEBT_INV_FREE = 4.174 - 3.122                        # 债权投资扣除质押（第 117 页）
CASH_LIKE = CASH - RESTRICTED + TFA_CASHLIKE + OCA_CASHLIKE + DEBT_INV_FREE
OP_RESERVE = 100.0                                   # 经营备付（约 15 天营业成本）
DIV_PAYABLE = 30.260                                 # 6 月末应付股利（H 股 2025 末期息 22.76 等，第 158 页）
INTERIM_DIV = 111.356                                # 2026 中期息 0.42 元，8-21 除息，现价已除息
ALLIED_COST = 19.9                                   # 7-30 公告认购联合黄金 9.2%：4.166 亿加元 ≈ 2.95 亿美元，期后已交割

DEBT = {
    "短期借款（含黄金租赁 93.75、票据贴现 73.78）": 331.285,
    "衍生金融负债中的黄金租赁": 9.725,
    "长期借款（含一年内到期 244.88、黄金租赁 77.81）": 693.161,
    "应付债券（公司债、中票、可交换债，不含可转债）": 154.949 + 249.281 + 6.367,
    "应付债券利息": 3.457,
    "长期应付款（含一年内到期）": 39.019,
    "财务公司吸收存款": 3.560,
    "预计负债（矿山环境恢复 87.33 等）": 89.585,
    "金属流合同负债": 6.874,
    "或有对价": 3.071,
    "购电协议衍生负债": 2.004,
    "长期应付职工薪酬": 0.785,
    "其他衍生负债净额（负债 21.03 − 衍生资产 12.95）": 31.109 - 9.725 - 0.361 - 12.952,
}
LEASE = 2.777        # 租赁负债：净利润已扣折旧与利息，只列示不扣
DEBT_TOTAL = sum(DEBT.values())
NET_CASH_ADJ = CASH_LIKE - OP_RESERVE - DIV_PAYABLE - INTERIM_DIV - ALLIED_COST - DEBT_TOTAL
DEBT_RATE = 0.025    # 有息负债实际平均利率（不含可转债，含资本化利息）：2026H1 利息支出 22.03 − 可转债 3.32，年化 ÷ 平均余额
TAX_SHIELD = 0.25

# 非经营资产（扣折价）：其他权益工具投资、交易性权益投资、对合营联营企业借款等
NON_OP = {
    "艾芬豪（6-30 公允价值 92.19，美元市值按不变、汇率调至 6.676）×0.85": 92.193 * USD_CNY / 6.8109 * 0.85,
    "其他上市其他权益工具投资（四川黄金 12.25 等）×0.85": 20.020 * 0.85,
    "非上市其他权益工具投资 ×0.70": 13.973 * 0.70,
    "交易性权益工具投资（含其他非流动金融资产 11.37）×0.85": 106.136 * 0.85,
    "联合黄金 9.2%（1,280 万股 × 20.32 美元）×0.85": 0.128 * 20.32 * USD_CNY * 0.85,
    "对卡莫阿等合营联营企业借款本息 ×0.80": 115.220 * 0.80,
    "投资性房地产": 5.135,
}
NON_OP_TOTAL = sum(NON_OP.values())

# 赤峰黄金控制权（3-23 公告；9-29 补充协议延至 11-30）：增量 25.00% 股权，A 股 100.06 亿 + H 股 93.86 亿港元
CHIFENG_COST = 100.06 + 93.86 * HKD_CNY
CHIFENG_CASH_IN = 93.86 * HKD_CNY
CHIFENG_STAKE = 0.25
CHIFENG_PE = 13.0
CHIFENG_P_CLOSE = 0.85


def chifeng_npv(np_norm: float) -> float:
    return CHIFENG_P_CLOSE * (CHIFENG_STAKE * (CHIFENG_PE * np_norm + CHIFENG_CASH_IN) - CHIFENG_COST)


# ---------------------------------------------------------------------------
# 4. 可转债（第 36-37 页；financing_20260130 第 9-12 页）
# ---------------------------------------------------------------------------
CB24_USD, CB24_FIX, CB24_CP = 1999.8, 7.8101, 18.75   # 百万美元；6-30 转换价 18.97 港元，按 8 月中期息估算下调
CB26_USD, CB26_FIX, CB26_CP = 1500.0, 7.8027, 62.00   # 6-30 转换价 62.65 港元，同上；2029-02-05 可按面值回售
N24 = CB24_USD * CB24_FIX / CB24_CP / 100
N26 = CB26_USD * CB26_FIX / CB26_CP / 100
D24 = CB24_USD * USD_CNY / 100
D26 = CB26_USD * USD_CNY / 100


def per_share(equity: float, shares: float = SHARES) -> dict:
    combos = {
        "全部按债务": (equity - D24 - D26) / shares,
        "全部转股": equity / (shares + N24 + N26),
        "24 券转股、26 券按债务": (equity - D26) / (shares + N24),
        "24 券按债务、26 券转股": (equity - D24) / (shares + N26),
    }
    key = min(combos, key=combos.get)
    return dict(v=combos[key], pick=key, combos=combos)


# ---------------------------------------------------------------------------
# 5. DCF
# ---------------------------------------------------------------------------
def scenario(name: str, coe: float = COE, levered: bool = True, override: dict | None = None,
             shares: float = SHARES) -> dict:
    s = dict(SCEN[name])
    if override:
        s.update(override)
    r = pnl(s["px"], FX_NORM, s["li"], s["other"], s["smelt"], s["opex"], s["assoc"], s["minority"],
            cost_mult=s.get("cost_mult", 1.0))
    np0 = r["parent"]
    flows, npt = [], np0
    for i, gi in enumerate(s["g"]):
        npt *= 1 + gi
        b = gi / s["roic"]
        flows.append((2027 + i, npt, b, npt * (1 - b)))
    pv = sum(f[3] / (1 + coe) ** (T_FIRST + i) for i, f in enumerate(flows))
    b_t = s["g_t"] / s["roic_t"]
    oe_t = flows[-1][1] * (1 + s["g_t"]) * (1 - b_t)
    tv = oe_t / (coe - s["g_t"])
    pv_tv = tv / (1 + coe) ** (T_FIRST + len(flows) - 1)
    h2 = pnl(H2["px"], H2["fx"], H2["li"], H2["other"], H2["smelt"], H2["opex"], H2["assoc"], H2["minority"],
             vol=VOL_H2, scale=0.5)
    h2_oe = h2["parent"] * (1 - H2["reinvest"])
    debt_pv = -NET_CASH_ADJ * DEBT_RATE * (1 - TAX_SHIELD) / coe if NET_CASH_ADJ < 0 else 0.0
    cf = chifeng_npv(s["chifeng_np"])
    if levered and NET_CASH_ADJ < 0:
        equity = pv + pv_tv + h2_oe - debt_pv + NON_OP_TOTAL + cf
    else:
        equity = pv + pv_tv + h2_oe + NET_CASH_ADJ + NON_OP_TOTAL + cf
    ps = per_share(equity, shares)
    return dict(s=s, pnl=r, np0=np0, np_rep=reported_np(np0, s["minority"]), flows=flows, pv=pv, pv_tv=pv_tv,
                tv_share=pv_tv / (pv + pv_tv), b_t=b_t, h2=h2["parent"], h2_oe=h2_oe, debt_pv=debt_pv, chifeng=cf,
                equity=equity, **ps)


def weighted(coe: float = COE, levered: bool = True, probs: dict | None = None, override: dict | None = None,
             shares: float = SHARES) -> tuple[dict, float]:
    vs = {k: scenario(k, coe, levered, override.get(k) if override else None, shares)["v"] for k in SCEN}
    pr = probs or {k: SCEN[k]["p"] for k in SCEN}
    return vs, sum(vs[k] * pr[k] for k in SCEN)


def solve(f, lo: float, hi: float, target: float, n: int = 200) -> float:
    """f 单调；求 f(x) = target。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr() -> float:
    return solve(lambda c: scenario("base", coe=c)["v"], 0.04, 0.30, PRICE_A)


def reverse_dcf() -> tuple[float, float]:
    base = scenario("base")
    np0, rest = base["np0"], base["h2_oe"] + NON_OP_TOTAL + base["chifeng"] - base["debt_pv"]

    def v10(g: float) -> float:
        pv, npt = 0.0, np0
        for i in range(10):
            npt *= 1 + g
            pv += npt * (1 - g / 0.20) / (1 + COE) ** (T_FIRST + i)
        tv = npt * 1.02 * (1 - 0.02 / 0.12) / (COE - 0.02) / (1 + COE) ** (T_FIRST + 9)
        return per_share(pv + tv + rest)["v"]

    def vperp(g: float) -> float:
        oe1 = np0 * (1 + g) * (1 - g / 0.12)
        return per_share(oe1 / (COE - g) / (1 + COE) ** (T_FIRST - 1) + rest)["v"]

    return solve(v10, -0.10, 0.20, PRICE_A), solve(vperp, -0.05, 0.085, PRICE_A)


# ---------------------------------------------------------------------------
# 6. 分部加总对照（上市部分按 2026-10-21 市值；其余按基准正常化归母经营净利 × 12 倍）
# ---------------------------------------------------------------------------
LISTED = {
    "紫金黄金国际 85%（市值 3,564.88 亿港元）": 3564.8839 * 0.85 * HKD_CNY,
    "藏格矿业 26.20%（市值 1,109.22 亿）": 1109.22 * 0.262,
    "紫金龙净 25%（3.175 亿股 × 16.26）": 12.70046293 * 0.25 * 16.26,
    "招金矿业 18.2%（市值 622.75 亿港元）": 622.7527 * 0.182 * HKD_CNY,
    "江南化工、万国黄金、嘉友国际、赛恩斯（账面）": 32.420 + 12.789 + 11.752 + 3.204,
    "龙高股份 20%（市值 37.81 亿）": 37.81 * 0.20,
    "艾芬豪与其他上市其他权益工具投资（不折价）": 92.193 * USD_CNY / 6.8109 + 20.020,
}
LOOK_THROUGH_BASE = {"紫金黄金国际": 0.85 * 1.744 * FX_NORM * 10,   # 正常化归母约 17.4 亿美元（金价 3,600）
                     "藏格矿业": 0.262 * 48.5, "紫金龙净": 0.25 * 11.1, "上市联营企业投资收益": 12.2}
REMAIN_PE = 12.0


def sotp() -> dict:
    base = scenario("base")
    remain_np = base["np0"] - sum(LOOK_THROUGH_BASE.values())
    other_nonop = (13.973 * 0.70 + 106.136 * 0.85 + 115.220 * 0.80 + 5.135 + 0.128 * 20.32 * USD_CNY * 0.85)
    equity = (sum(LISTED.values()) + remain_np * REMAIN_PE + other_nonop + NET_CASH_ADJ + base["chifeng"])
    return dict(listed=sum(LISTED.values()), remain_np=remain_np, equity=equity, **per_share(equity))


# ---------------------------------------------------------------------------
# 7. 输出
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== 紫金矿业 601899 独立估值（亿元；元/股）===")
    ph = PRICE_H_HKD * HKD_CNY
    print(f"A 股 {PRICE_A:.2f}；H 股 {PRICE_H_HKD:.2f} 港元 = {ph:.2f} 元（较 A 股 {ph / PRICE_A - 1:+.1%}）；"
          f"总股本 {SHARES:.4f} 亿股（回购专户 {TREASURY:.4f}）；A 股价 × 总股本 = {PRICE_A * SHARES:,.1f}")
    print("上半年实现价/市场价：" + "，".join(f"{k} {v:.3f}" for k, v in RATIO.items() if H1[k][0] != "fe"))
    cal = pnl(MKT_H1, FX_H1, MKT_H1["li"], GP_H1_TOTAL * 2 - (sum(q * (p - c) / 1e8 for _, q, p, c in H1.values()) + SMELT_H1) * 2,
              SMELT_H1 * 2, 143.4, 56.97, 0.224, vol=VOL_H1X2)
    print(f"校准：按 2026H1 价格与销量年化，毛利 {cal['gp']:.1f}（实际 {GP_H1_TOTAL * 2:.1f}）、税金及附加 "
          f"{cal['taxes']:.1f}（实际 119.7）、归母经营净利 {cal['parent']:.1f}（实际归母 783.4、扣非 760.7）")
    print(f"现金类 {CASH_LIKE:.2f} − 备付 {OP_RESERVE:.0f} − 应付股利 {DIV_PAYABLE:.2f} − 中期息 {INTERIM_DIV:.2f} − "
          f"联合黄金认购 {ALLIED_COST:.1f} − 有息及类债务 {DEBT_TOTAL:.2f} = 经调整净现金 {NET_CASH_ADJ:.2f}（不含可转债）")
    print(f"有杠杆口径：净负债税后利息现值（{DEBT_RATE:.1%}，9%） {-NET_CASH_ADJ * DEBT_RATE * (1 - TAX_SHIELD) / COE:.1f}；"
          f"租赁负债 {LEASE:.2f} 只列示")
    print(f"非经营资产合计 {NON_OP_TOTAL:.1f}：" + "；".join(f"{k} {v:.1f}" for k, v in NON_OP.items()))
    print(f"可转债：24 券面值 {D24:.1f} / 转股 {N24:.3f} 亿股（折人民币转换价 {D24 / N24:.2f}）；"
          f"26 券面值 {D26:.1f} / 转股 {N26:.3f} 亿股（{D26 / N26:.2f}）")
    print(f"赤峰黄金：增量对价 {CHIFENG_COST:.1f}（其中 H 股增资 {CHIFENG_CASH_IN:.1f} 留在赤峰），交割概率 {CHIFENG_P_CLOSE:.0%}")
    print()
    res = {}
    for k in SCEN:
        r = scenario(k)
        res[k] = r
        s, p = r["s"], r["pnl"]
        print(f"[{k}] 概率 {s['p']:.2f}；金 {s['px']['au']} 铜 {s['px']['cu']} 银 {s['px']['ag']} 锌 {s['px']['zn']} "
              f"碳酸锂 {s['li']}；汇率 {FX_NORM}")
        print("  2026 正常化矿山毛利：" + "，".join(f"{kk} {vv:.1f}" for kk, vv in p["seg"].items())
              + f"；合计 {p['gp_mine']:.1f}；冶炼 {s['smelt']}；其他 {s['other']}；税金及附加 {p['taxes']:.1f}")
        print(f"  经营税前 {p['pbt']:.1f}（含联营合营 {s['assoc']}）；归母经营净利 {r['np0']:.1f}；"
              f"报表口径正常化归母（含净利息） {r['np_rep']:.1f}")
        print("  增长路径：" + "；".join(f"{y} 净利 {n:.1f} 再投资率 {b:.0%} 所有者收益 {o:.1f}" for y, n, b, o in r["flows"]))
        print(f"  终值增速 {s['g_t']:.1%}、终值再投资率 {r['b_t']:.1%}、终值占比 {r['tv_share']:.1%}；"
              f"经营现值 {r['pv'] + r['pv_tv']:.1f}；2026 下半年归母 {r['h2']:.1f}→所有者收益 {r['h2_oe']:.1f}；"
              f"赤峰净现值 {r['chifeng']:.1f}")
        print(f"  有杠杆股权价值 {r['equity']:.1f}；" + "；".join(f"{kk} {vv:.2f}" for kk, vv in r["combos"].items())
              + f" → V {r['v']:.2f}（{r['pick']}）")
        ru = scenario(k, levered=False)
        rx = scenario(k, shares=SHARES - TREASURY)
        print(f"  对照：无杠杆口径 V {ru['v']:.2f}；剔除回购专户股份 V {rx['v']:.2f}；"
              f"专户股份按 {ESOP_PRICE} 元转让员工 V {per_share(r['equity'] + TREASURY * ESOP_PRICE)['v']:.2f}")
    vs, vw = weighted()
    print()
    print("三情景 V：" + "，".join(f"{k} {v:.2f}" for k, v in vs.items()) + f"；概率加权 V {vw:.2f}")
    print(f"P/V（A 股） {PRICE_A / vw:.3f}；P/V（H 股折人民币 {ph:.2f}） {ph / vw:.3f}")
    vu, vwu = weighted(levered=False)
    vx, vwx = weighted(shares=SHARES - TREASURY)
    print("无杠杆口径：" + "，".join(f"{k} {v:.2f}" for k, v in vu.items()) + f"；加权 {vwu:.2f}；P/V {PRICE_A / vwu:.3f}")
    print("剔除回购专户：" + "，".join(f"{k} {v:.2f}" for k, v in vx.items()) + f"；加权 {vwx:.2f}；P/V {PRICE_A / vwx:.3f}")
    for c in (0.08, 0.10):
        v_c, w_c = weighted(coe=c)
        print(f"股权成本 {c:.0%}：" + "，".join(f"{k} {v:.2f}" for k, v in v_c.items()) + f"；加权 {w_c:.2f}")
    irr = implied_irr()
    g10, gp = reverse_dcf()
    print(f"现价隐含回报（基准情景） {irr:.4f}")
    print(f"反向 DCF：基准 2026 正常化归母 {res['base']['np0']:.1f} 起，10 年净利复合增速 {g10:.4f}（再投资按 20% 增量回报，"
          f"终值 2%）；或直接永续增速 {gp:.4f}（增量回报 12%）")
    print(f"正常化归母（含净利息）三档：" + "，".join(f"{k} {res[k]['np_rep']:.1f}" for k in SCEN)
          + f"；概率加权 {sum(res[k]['np_rep'] * SCEN[k]['p'] for k in SCEN):.1f}")
    # 下半年与三季度
    h2 = res["base"]["h2"]
    q3 = pnl(Q3["px"], Q3["fx"], Q3["li"], Q3["other"], Q3["smelt"], Q3["opex"], Q3["assoc"], Q3["minority"],
             vol=VOL_Q3, scale=0.25)
    q3_rep = q3["parent"] - 2.0 * (1 - TAX_ETR) * (1 - 0.224)
    h2_rep = h2 - 4.0 * (1 - TAX_ETR) * (1 - 0.224)
    print(f"三季度估计：归母约 {q3_rep:.1f}（二季度实际 {NP_Q2_REPORTED}）；下半年归母约 {h2_rep:.1f}；"
          f"2026 全年报表归母约 {NP_H1_REPORTED + h2_rep:.1f}")
    # 敏感性
    b = res["base"]
    for lab, ov in (("金价 ±100 美元", dict(px=dict(b["s"]["px"], au=b["s"]["px"]["au"] + 100))),
                    ("铜价 ±1,000 美元", dict(px=dict(b["s"]["px"], cu=b["s"]["px"]["cu"] + 1000))),
                    ("碳酸锂 ±1 万元", dict(li=b["s"]["li"] + 10000))):
        r2 = scenario("base", override=ov)
        print(f"敏感性（基准）{lab}：归母经营净利 {r2['np0'] - b['np0']:+.1f}，V {r2['v'] - b['v']:+.2f}")
    # 证伪条件触发后的 V
    f1 = weighted(probs=dict(bear=0.5, base=0.4, bull=0.1))[1]
    f2 = weighted(override={k: dict(g=SCEN["bear"]["g"], roic=SCEN["bear"]["roic"]) for k in SCEN})[1]
    f3 = weighted(override={k: dict(cost_mult=1.10) for k in SCEN})[1]
    f4 = vw - 150 / (SHARES + N24)
    f5 = weighted(override={k: dict(assoc=SCEN[k]["assoc"] - 15) for k in SCEN})[1]
    print(f"证伪触发后的 V：F1 金铜同跌（概率 0.5/0.4/0.1） {f1:.2f}；F2 产量与增长不及（各情景改用熊市增长） {f2:.2f}；"
          f"F3 价格联动以外的矿山单位成本 +10% {f3:.2f}；F4 现价并购 500 亿、毁损 30% {f4:.2f}；"
          f"附：卡莫阿 2027 年产量 < 38 万吨（联营收益 −15） {f5:.2f}")
    ev = PRICE_A * SHARES + PRICE_A * N24 - NET_CASH_ADJ + D26 + 672.207 - NON_OP_TOTAL - 557.146
    ebit = b["pnl"]["pbt"] - b["s"]["assoc"]
    print(f"EV/EBIT（基准正常化）：EV {ev:,.1f}（A 股价计全部股份与 24 券转股、经调整净负债、26 券面值、少数股东权益账面，"
          f"减非经营资产与长期股权投资账面）÷ EBIT {ebit:.1f} = {ev / ebit:.1f} 倍；"
          f"市值 ÷ 基准正常化归母 = {PRICE_A * SHARES / b['np_rep']:.1f} 倍")
    sp = sotp()
    print(f"分部加总对照：上市部分（紫金权益）{sp['listed']:.1f}；其余归母经营净利 {sp['remain_np']:.1f} × {REMAIN_PE:.0f} 倍；"
          f"无杠杆净负债 {NET_CASH_ADJ:.1f}；股权 {sp['equity']:.1f} → 每股 {sp['v']:.2f}（{sp['pick']}）")
    zgi_np = LOOK_THROUGH_BASE["紫金黄金国际"]
    zgi_mv = LISTED["紫金黄金国际 85%（市值 3,564.88 亿港元）"]
    print(f"  紫金黄金国际：紫金权益市值 {zgi_mv:.1f} ÷ 正常化归母权益 {zgi_np:.1f} = {zgi_mv / zgi_np:.1f} 倍；"
          f"若按 15 倍计每股 {per_share(sp['equity'] - zgi_mv + zgi_np * 15)['v']:.2f}；"
          f"其余部分按 14 倍计每股 {per_share(sp['equity'] + sp['remain_np'] * 2)['v']:.2f}")
    rest = b["h2_oe"] + NON_OP_TOTAL + b["chifeng"] - b["debt_pv"]

    def vperp_from(np0: float, g: float) -> float:
        return per_share(np0 * (1 + g) * (1 - g / 0.12) / (COE - g) / (1 + COE) ** (T_FIRST - 1) + rest)["v"]

    g781 = solve(lambda g: vperp_from(781.0, g), -0.10, 0.085, PRICE_A)
    n0 = solve(lambda n: vperp_from(n, 0.0), 100, 1500, PRICE_A)
    print(f"反向 DCF 补充：以 2026E 报表口径 781 为起点的隐含永续增速 {g781:.4f}；零增长永续对应归母 {n0:.1f}")
    print("V 不变时各档价格：≤0.75 → {:.2f}；0.90 → {:.2f}；1.10 → {:.2f}".format(0.75 * vw, 0.90 * vw, 1.10 * vw))


if __name__ == "__main__":
    main()
