"""分众传媒（002027）独立估值：所有者收益 DCF（OI-291 b10，价格日 2026-10-20）。

单位：金额亿元，股本亿股，每股价值元/股。运行：python3 valuation.py
主结论口径：收购新潮传媒 90.02% 股份「交易完成」（每股 = 合并后权益 ÷ 159.7674 亿股，
现行每一股对应合并后一股）；「交易未完成」（现行股本 144.4220 亿股）作对照。
租赁负债主口径不计入有息负债（媒体租金已在所有者收益中按使用权资产折旧 + 租赁利息全额扣除），
另给出把租赁负债全额扣除的保守口径。
"""

PRICE = 5.18                    # 2026-10-20 收盘（brief）
SHARES = 144.4220               # 现行总股本，无回购专户、无拟注销股份（2026H1_report 第 44-45 页）
NEW_SHARES = 15.34540509        # 新潮交易发行股份，发行价 5.06 元（dividend_20260828_556724 第 3-5 页）
COE = 0.09
P_DEAL = 0.85                   # 交易完成概率（市场监管总局已附条件批准；尚需深交所审核、证监会注册）

# ---- 2026-06-30 资产负债表（2026H1_report 第 48-49 页及附注）----
CASH = 40.2819                  # 货币资金
WMP = 67.8170                   # 交易性金融资产（理财产品）
TD = 4.6959 + 0.9180 + 4.3590   # 定期存款及利息：其他流动资产 / 一年内到期非流动资产 / 其他非流动资产（第 107、111 页）
RESTRICTED = 1.0343             # 受限资金（第 20 页）
DIV_PAYABLE = 27.4994           # 应付股利：2025 年度 0.19 元/股（7-09 付）+ 少数股东旧欠 0.06
INTERIM_DIV = 7.2211            # 2026 中期 0.05 元/股（9-04 除息）
BORROW = 1.9473 + 0.1405 + 0.4610   # 短期借款 + 一年内到期长期借款 + 长期借款（第 123-124 页）
OP_RESERVE = 10.0               # 经营备付（约 1.7 个月现金成本，含境外子公司 7.54 亿存款）
LEASE = 17.7531 + 7.4475        # 一年内到期租赁负债 + 租赁负债（第 123-124 页）
OTHER_NCFA = 19.4913            # 其他非流动金融资产（股权基金 18.98 + 影视 0.51，第 110 页）
OTHER_EQ = 6.6227               # 其他权益工具投资（VSPN 4.18 等非上市股权，第 108 页）
LTEI = 0.8686                   # 长期股权投资（第 109 页）
SHUHE_RECV = 1.9392             # 数禾退出尚未收回款（第 18 页）

# ---- 正常化经营参数 ----
LEASE_INT = 0.95                # 租赁负债利息（TTM 0.94：2025 1.04 − 2025H1 0.55 + 2026H1 0.46）
CREDIT = 0.004                  # 正常信用损失 / 收入
MINORITY = 0.20                 # 少数股东分担的境外亏损（TTM 少数股东损益 −0.21）
FIN_YIELD_AT = 1.2              # 2026 税后理财与利息收入（只用于正常化归母净利，不进所有者收益）

SC = {
    "bear": dict(p=0.25, rev=110.0, m=0.420, tax=0.18, sub=2.0, capex=2.0, fin=1.0,
                 g=[-0.05, -0.02, 0.00, 0.01, 0.01], gt=0.010, h=(0.6, 0.5, 0.7),
                 note="阿里投放回落至年 12-15 亿、日消等阿里以外收入再降、刊例受压"),
    "base": dict(p=0.50, rev=117.0, m=0.440, tax=0.17, sub=2.5, capex=1.5, fin=1.2,
                 g=[-0.03, 0.02, 0.03, 0.03, 0.03], gt=0.020, h=(0.7, 0.6, 0.8),
                 note="2026 收入约 117 亿（阿里约 24 亿）、2027 回落后恢复 2-3% 增长"),
    "bull": dict(p=0.25, rev=124.0, m=0.460, tax=0.16, sub=3.0, capex=1.0, fin=1.4,
                 g=[0.02, 0.04, 0.04, 0.04, 0.04], gt=0.025, h=(0.8, 0.7, 0.9),
                 note="AI 与互联网广告主接力、日消回暖、成本继续优化"),
}
# 交易完成的增减项：限制性条件（城市成交价封顶、放弃独家与自动续约）对分众原有业务的削减、
# 新潮 90.02% 的现金类资产与协同后所有者收益、竞争缓和带来的折扣收窄
DEAL = {
    "bear": dict(oe_cut=0.030, g_cut=0.010, xc_cash=14.0, xc_oe=0.8, relief=0.0),
    "base": dict(oe_cut=0.015, g_cut=0.0075, xc_cash=17.0, xc_oe=2.4, relief=1.0),
    "bull": dict(oe_cut=0.005, g_cut=0.005, xc_cash=19.0, xc_oe=4.0, relief=2.5),
}
DEAL_COST = 2.3                 # 现金对价 0.30 + 中介与整合费用约 2.0
YEARS = [2027, 2028, 2029, 2030, 2031]


def liquid_net_cash():
    return CASH + WMP + TD - RESTRICTED - DIV_PAYABLE - INTERIM_DIV - BORROW - OP_RESERVE


def other_nonop(h):
    return OTHER_NCFA * h[0] + OTHER_EQ * h[1] + LTEI * h[2] + SHUHE_RECV


def np_operating(s):
    """2026 正常化经营归母净利（不含理财利息）。"""
    pre = s["rev"] * s["m"] - LEASE_INT - s["rev"] * CREDIT
    return pre * (1 - s["tax"]) + MINORITY + s["sub"] * 0.85


def oe2026(s):
    return np_operating(s) - s["capex"]


def op_value(s, r=COE, d=None, g_override=None, gt_override=None):
    """经营价值：2026H2 所有者收益（t=0.2）+ 2027-2031（年中，t=0.7…4.7）+ 终值（t=4.7）。"""
    g = g_override if g_override is not None else s["g"]
    gt = gt_override if gt_override is not None else s["gt"]
    oe0 = oe2026(s)
    pv = 0.5 * oe0 / (1 + r) ** 0.2
    oe, last = oe0, oe0
    add = (d["xc_oe"] + d["relief"]) if d else 0.0
    for i, gi in enumerate(g):
        oe *= 1 + gi - (d["g_cut"] if (d and i >= 1) else 0.0)
        extra = add * (0.5 if i == 0 else (1 + gt) ** (i - 1))
        last = oe * (1 - (d["oe_cut"] if d else 0.0)) + extra
        pv += last / (1 + r) ** (i + 0.7)
    tv = last * (1 + gt) / (r - gt)
    return pv + tv / (1 + r) ** 4.7, tv / (1 + r) ** 4.7


def v_standalone(k, r=COE, nonop_cut=1.0):
    s = SC[k]
    nonop = liquid_net_cash() * nonop_cut + other_nonop(s["h"])
    return (op_value(s, r)[0] + nonop) / SHARES


def v_deal(k, r=COE, nonop_cut=1.0):
    s, d = SC[k], DEAL[k]
    nonop = liquid_net_cash() * nonop_cut + other_nonop(s["h"]) + d["xc_cash"] - DEAL_COST
    return (op_value(s, r, d)[0] + nonop) / (SHARES + NEW_SHARES)


def weighted(fn, r=COE, w=None, **kw):
    w = w or {k: SC[k]["p"] for k in SC}
    return sum(w[k] * fn(k, r, **kw) for k in SC)


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def band(pv):
    return "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    lnc = liquid_net_cash()
    print("== 非经营项目（2026-06-30，扣已宣派股利）==")
    print(f"经调整净现金（无杠杆口径，租赁负债不扣） {lnc:.2f} 亿；其他金融资产折算 "
          + " / ".join(f"{k} {other_nonop(SC[k]['h']):.2f}" for k in SC) + " 亿；租赁负债 {:.2f} 亿".format(LEASE))

    print("\n== 2026 正常化归母净利（含税后理财利息，剔除一次性）==")
    for k, s in SC.items():
        print(f"{k}: 收入 {s['rev']:.0f}  核心 EBIT {s['rev'] * s['m']:.2f}  经营归母 {np_operating(s):.2f}  "
              f"正常化归母 {np_operating(s) + s['fin']:.2f}  所有者收益 {oe2026(s):.2f}")

    print("\n== 所有者收益路径（基准，交易未完成）==")
    oe = oe2026(SC["base"])
    path = []
    for y, gi in zip(YEARS, SC["base"]["g"]):
        oe *= 1 + gi
        path.append(f"{y} {oe:.2f}")
    print("2026 {:.2f} | ".format(oe2026(SC["base"])) + " | ".join(path) + f" | 终值增长 {SC['base']['gt']:.1%}")
    opv, tvpv = op_value(SC["base"])
    print(f"基准经营价值 {opv:.1f} 亿，其中终值现值 {tvpv:.1f}（占 {tvpv / opv:.0%}）")

    print("\n== 三情景每股价值（股权成本 9%）==")
    for k in SC:
        print(f"{k} (p={SC[k]['p']:.2f})  交易完成 {v_deal(k):.2f}  交易未完成 {v_standalone(k):.2f}")
    vw_d, vw_s = weighted(v_deal), weighted(v_standalone)
    vw_p = P_DEAL * vw_d + (1 - P_DEAL) * vw_s
    print(f"加权 V：交易完成（主口径） {vw_d:.2f}，P/V {PRICE / vw_d:.3f}（{band(PRICE / vw_d)}）")
    print(f"        交易未完成 {vw_s:.2f}，P/V {PRICE / vw_s:.3f}（{band(PRICE / vw_s)}）")
    print(f"        按完成概率 {P_DEAL:.0%} 加权 {vw_p:.2f}，P/V {PRICE / vw_p:.3f}")
    print("无回购专户股份，无需另算剔除口径。")

    print("\n== 股权成本敏感性（加权 V）==")
    for r in (0.08, 0.10):
        print(f"r={r:.0%}: 交易完成 {weighted(v_deal, r):.2f}  交易未完成 {weighted(v_standalone, r):.2f}")

    lease_ps_d = LEASE / (SHARES + NEW_SHARES)
    lease_ps_s = LEASE / SHARES
    print("\n== 租赁负债计入有息负债的保守口径（全额扣除 25.20 亿，所有者收益不调，属重复扣除）==")
    print(f"交易完成 {vw_d - lease_ps_d:.2f}（P/V {PRICE / (vw_d - lease_ps_d):.3f}）；"
          f"交易未完成 {vw_s - lease_ps_s:.2f}（P/V {PRICE / (vw_s - lease_ps_s):.3f}）")

    print("\n== 现价隐含回报（基准情景现金流 + 非经营资产 = 现价的折现率）==")
    irr_d = solve(lambda r: v_deal("base", r), 0.05, 0.20, PRICE)
    irr_s = solve(lambda r: v_standalone("base", r), 0.05, 0.20, PRICE)
    print(f"交易完成 {irr_d:.2%}；交易未完成 {irr_s:.2%}")

    print("\n== 反向 DCF（交易未完成，基准 2026 所有者收益 {:.2f}）==".format(oe2026(SC["base"])))
    s = SC["base"]
    target = PRICE * SHARES - lnc - other_nonop(s["h"])

    def perp(g):
        return op_value(s, gt_override=g, g_override=[g] * 5)[0]

    g_perp = solve(perp, -0.05, 0.08, target)

    def ten(g):
        oe0 = oe2026(s)
        pv = 0.5 * oe0 / 1.09 ** 0.2
        o = oe0
        for i in range(10):
            o *= 1 + g
            pv += o / 1.09 ** (i + 0.7)
        return pv + o * 1.02 / 0.07 / 1.09 ** 9.7

    g_ten = solve(ten, -0.05, 0.10, target)
    print(f"现价对应经营价值 {target:.1f} 亿：隐含 2027 起永续增速 {g_perp:.2%}；或 10 年增速 {g_ten:.2%} 后 2% 永续")
    d = DEAL["base"]
    target_d = PRICE * (SHARES + NEW_SHARES) - lnc - other_nonop(s["h"]) - d["xc_cash"] + DEAL_COST
    g_perp_d = solve(lambda g: op_value(s, d=d, gt_override=g, g_override=[g] * 5)[0], -0.05, 0.08, target_d)
    print(f"交易完成口径（含新潮与限制性条件削减）：分众原有业务需 2027 起永续增速 {g_perp_d:.2%}")

    print("\n== 交叉验证 ==")
    ev = PRICE * SHARES - lnc - other_nonop(SC["base"]["h"])
    print(f"EV（不含租赁）{ev:.1f} 亿；EV/TTM 核心 EBIT 58.62 = {ev / 58.62:.1f}x；EV/2026 基准核心 EBIT "
          f"{SC['base']['rev'] * SC['base']['m']:.1f} = {ev / (SC['base']['rev'] * SC['base']['m']):.1f}x")
    print(f"市值/2026 基准正常化归母 {PRICE * SHARES / (np_operating(SC['base']) + SC['base']['fin']):.1f}x；"
          f"TTM 每股现金分红 0.29 元，股息率 {0.29 / PRICE:.1%}")
    hist = {2018: (5.24, 146.78, 58.23, 142.01), 2019: (6.26, 146.78, 18.75, 137.78),
            2020: (9.87, 146.78, 40.04, 170.17), 2021: (8.19, 144.42, 60.63, 183.79),
            2022: (6.68, 144.42, 27.90, 169.49), 2023: (6.32, 144.42, 48.27, 176.93),
            2024: (7.03, 144.42, 51.55, 170.27), 2025: (7.37, 144.42, 29.46, 142.49)}
    print("历史 PE/PB（年末收盘 × 实际总股本）：" + "；".join(
        f"{y} {c * n / npf:.1f}x/{c * n / bv:.1f}x" for y, (c, n, npf, bv) in hist.items()))

    print("\n== 证伪条件触发后的 V（交易完成口径）==")
    f1 = weighted(v_deal, w={"bear": 0.45, "base": 0.45, "bull": 0.10})
    f2 = weighted(v_deal, w={"bear": 0.60, "base": 0.40, "bull": 0.0})
    f3 = vw_s
    f4 = weighted(v_deal, nonop_cut=0.7)
    f5 = weighted(v_deal, w={"bear": 0.40, "base": 0.50, "bull": 0.10}) - 5.0 / (SHARES + NEW_SHARES)
    f0 = weighted(v_deal, w={"bear": 0.15, "base": 0.55, "bull": 0.30})
    for name, v in (("F1 三季报收入/扣非低于门槛", f1), ("F2 2026 阿里与阿里以外收入双弱", f2),
                    ("F3 交易终止（回到现行股本）", f3), ("F4 分红低于承诺、现金转作他用", f4),
                    ("F5 反垄断判决或调查", f5), ("反向信号：三季报营收≥32.5 亿且扣非≥13 亿", f0)):
        print(f"{name}: V {v:.2f}，P/V {PRICE / v:.3f}")

    print("\n== 新潮对分众的价值拆分（交易完成口径，亿元）==")
    for k in SC:
        s, d = SC[k], DEAL[k]
        base_v = op_value(s)[0]
        cut_only = op_value(s, d=dict(d, xc_oe=0.0, relief=0.0))[0]
        full = op_value(s, d=d)[0]
        print(f"{k}: 限制性条件削减 {cut_only - base_v:.1f}；协同与竞争缓和现值 {full - cut_only:.1f}；"
              f"新潮现金 {d['xc_cash']:.1f}；费用 {-DEAL_COST:.1f}；合计 {full - base_v + d['xc_cash'] - DEAL_COST:.1f}"
              f"（股份对价 {NEW_SHARES * 5.06:.2f}）")

    print("\n== V 不变时进入各档的价格（主口径 V {:.2f}）==".format(vw_d))
    print(f"明显低估 ≤ {vw_d * 0.75:.2f}；温和低估 ≤ {vw_d * 0.90:.2f}；大致合理 ≤ {vw_d * 1.10:.2f}；偏贵 > {vw_d * 1.10:.2f}")
