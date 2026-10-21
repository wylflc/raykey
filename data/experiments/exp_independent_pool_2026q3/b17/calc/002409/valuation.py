#!/usr/bin/env python3
"""雅克科技（002409）独立估值：OI-291 b17，价格日 2026-10-21。

运行：python3 valuation.py
输出：三情景 V、加权 V、P/V、股权成本 8%/10% 下的 V、现价隐含回报、反向 DCF、证伪触发后的 V。
金额单位：亿元；每股价值：元/股。全部输入写在本文件内，来源见同名正文
（b17/companies/002409_雅克科技.md）。
"""

# ---------------------------------------------------------------------------
# 一、快照
# ---------------------------------------------------------------------------
PRICE = 96.80            # 2026-10-21 收盘（腾讯日线）
SHARES = 4.7593          # 总股本（亿股），无回购专户、无库存股（2026H1 第 29、37 页）
MCAP = PRICE * SHARES    # 460.70
COE = 0.09
TG = 0.025               # 终值增长
STUB = 1 - 294 / 365     # 2026-10-21 之后 2026 年剩余比例（约 0.195）

# ---------------------------------------------------------------------------
# 二、经调整净现金（2026-06-30，亿元）
# ---------------------------------------------------------------------------
CASH = 23.358            # 货币资金，期末现金等价物同额，无受限（2026H1 第 36、44 页）
TERM_DEP = 3.127         # 其他流动资产中的定期存款及利息（2026H1 第 88 页）
DEBT_ST = 8.022          # 短期借款
DEBT_LT = 29.107         # 长期借款（信用 2.3%-3.2%，抵押 5.5%-5.8%，2026H1 第 106 页）
DEBT_LT_CUR = 0.405      # 一年内到期的长期借款
LEASE = 0.196 + 0.080    # 租赁负债（含一年内到期），所有者收益以净利润为起点，只列示不扣
REV_TTM = 88.31
OP_RESERVE = 0.03 * REV_TTM   # 经营备付：TTM 营收 3%
DIV_DECLARED = 1.666     # 2026 中期 10 派 3.5 元，2026-09-22 除息，H1 资产负债表后支付
DEBT_RATE = 0.026        # 有息负债实际平均利率（H1 借款利息 0.523 亿×2 ÷ 期初期末平均借款约 41 亿）
TAX = 0.15

CASH_LIKE = CASH + TERM_DEP
DEBT = DEBT_ST + DEBT_LT + DEBT_LT_CUR
NET_CASH_ADJ = CASH_LIKE - OP_RESERVE - DIV_DECLARED - DEBT   # 无杠杆口径，填 json

# 金融资产投资公司等投资人在子公司的权益（按实缴出资全额扣除，相应子公司利润 100% 计入）
AIC_KMT = 9.25           # 成都科美特 22.85%：工融金投 7.25 + 兴银金投 2.00（AN202601041814692062）
AIC_HF = 14.616 - 9.25   # 浙江华飞已到位 5.366（H1 所有者投入 14.616 亿，第 45 页；增资上限 8.498 亿）
AIC_CLAIMS = AIC_KMT + AIC_HF

# 非经营资产（亿元）
NON_OP_ITEMS = {
    "交易性金融资产（华泰瑞联基金）": 0.667,
    "长期股权投资（沈阳亦创 0.858 按五折）": 2.300 - 0.858 * 0.5,
    "其他权益工具（CHEME）+ MTI 基金": 0.128 + 0.061,
    "对参股公司借款（沈阳亦创 0.129、KASUS 0.244）八折": (0.129 + 0.244) * 0.8,
    "为沈阳亦创担保 0.403 按五折计或有损失": -0.403 * 0.5,
}
NON_OP = sum(NON_OP_ITEMS.values())

# ---------------------------------------------------------------------------
# 三、2026 年正常化归母净利（报表口径，含净利息，剔除一次性）
# ---------------------------------------------------------------------------
H1_KF = 5.299            # 2026H1 扣非归母（第 7 页）
H1_TAX_PRIOR = 35.37 / 100 * 0.90   # 调整以前期间所得税 -3,537 万（第 116 页），按 90% 归母
H1_CREDIT_REV = 15.98 / 100 * 0.85  # 信用减值转回 1,598 万（第 115 页），税后
H1_FX = 8.39 / 100 * 0.85           # 汇兑收益 839 万（第 113 页），税后
H1_ASSOC = 0.05                     # 半年报未确认的权益法亏损估计（沈阳亦创等）
H1_CORE = H1_KF - H1_TAX_PRIOR - H1_CREDIT_REV - H1_FX - H1_ASSOC
H2_CORE = {"bear": 3.876, "base": 4.976, "bull": 5.976}
NORM_NP_2026 = {k: round(H1_CORE + v, 2) for k, v in H2_CORE.items()}

# 估值口径调整：加回税后净利息（2026E 净利息约 0.75 亿），
# 加回科美特 22.85%、华飞 34.92% 的少数股东损益（投资人权益已按出资额全额扣除）
NET_INT_AT = 0.75 * (1 - TAX)
AIC_MINORITY = {
    "bear": 0.2285 * 1.50 + 0.3492 * 0.15,
    "base": 0.2285 * 1.76 + 0.3492 * 0.30,
    "bull": 0.2285 * 2.00 + 0.3492 * 0.45,
}

SCEN = {
    # g: 2027-2031 经营所有者收益（NOPAT）增速；rr: 再投资率；roic_t: 终值期资本回报
    "bear": dict(p=0.25, g=[0.03, -0.08, 0.02, 0.05, 0.03], rr=0.38, roic_t=0.10,
                 extra=-4.8,  # 2027 年底前现金收购江苏先科 66.93%，对价高于内在价值约三成
                 note="存储 2028 年转入下行、硅基前驱体国内价格战；LNG 订单 2028 年后回落且板材毛利率停在 22% 左右；"
                      "光刻胶低开工；江苏先科少数股权现金高价收回"),
    "base": dict(p=0.50, g=[0.11, 0.14, 0.11, 0.09, 0.07], rr=0.48, roic_t=0.13, extra=0.0,
                 note="UP 三厂 2026 年底投产、中韩新增产能 2027 年底建成，2028 年前驱体放量；江苏先科爬坡；"
                      "LNG 板材与安装持平；电子特气内蒙古新产能、硅微粉温和增长"),
    "bull": dict(p=0.25, g=[0.20, 0.24, 0.18, 0.13, 0.10], rr=0.52, roic_t=0.18, extra=0.0,
                 note="AI 存储超级周期延续到 2030 年、主要客户产能翻倍且份额提升，钼前驱体与 HBM 放量；"
                      "LNG 订单维持高位、板材毛利率回到 27%；半导体光刻胶通过验证"),
}


def nopat_2026(k):
    return NORM_NP_2026[k] + NET_INT_AT + AIC_MINORITY[k]


def nopat_path(base, gs):
    out, x = [], base
    for g in gs:
        x *= 1 + g
        out.append(x)
    return out


def ops_value(k, r, gs=None, rr=None, roic_t=None):
    s = SCEN[k]
    gs = s["g"] if gs is None else gs
    rr = s["rr"] if rr is None else rr
    roic_t = s["roic_t"] if roic_t is None else roic_t
    n0 = nopat_2026(k)
    path = nopat_path(n0, gs)
    pv = n0 * (1 - rr) * STUB / (1 + r) ** (STUB / 2)          # 2026 年剩余期
    for i, n in enumerate(path, start=1):
        t = i - 0.5 + STUB                                       # 年中折现
        pv += n * (1 - rr) / (1 + r) ** t
    t_last = len(path) - 0.5 + STUB
    oe_next = path[-1] * (1 + TG) * (1 - TG / roic_t)
    tv = oe_next / (r - TG)
    pv_tv = tv / (1 + r) ** t_last
    return pv + pv_tv, pv_tv, path


def equity(k, r=COE, levered=True, **kw):
    ops, pv_tv, _ = ops_value(k, r, **kw)
    nd = -NET_CASH_ADJ
    debt_charge = nd * DEBT_RATE * (1 - TAX) / r if levered else nd
    return ops - debt_charge - AIC_CLAIMS + NON_OP + SCEN[k]["extra"]


def per_share(x):
    return x / SHARES


def weighted(r=COE, levered=True, probs=None):
    probs = probs or {k: SCEN[k]["p"] for k in SCEN}
    return sum(probs[k] * per_share(equity(k, r, levered)) for k in SCEN)


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 经调整净现金（亿元）==")
    print(f"现金类 {CASH_LIKE:.2f}（货币资金 {CASH:.2f} + 定期存款 {TERM_DEP:.2f}）；有息负债（不含租赁）{DEBT:.2f}；"
          f"租赁负债 {LEASE:.2f}（只列示）")
    print(f"经营备付 {OP_RESERVE:.2f}；已宣派中期股利 {DIV_DECLARED:.2f}")
    print(f"net_cash_adj（无杠杆口径）= {NET_CASH_ADJ:.2f}；投资人权益（科美特 {AIC_KMT:.2f} + 华飞 {AIC_HF:.2f}）= {AIC_CLAIMS:.2f}")
    print(f"非经营资产合计 {NON_OP:.2f}：" + "；".join(f"{k} {v:.2f}" for k, v in NON_OP_ITEMS.items()))
    nd = -NET_CASH_ADJ
    print(f"有杠杆口径：经调整净负债 {nd:.2f} × {DEBT_RATE:.1%} × (1-{TAX:.0%}) ÷ 9% = {nd*DEBT_RATE*(1-TAX)/COE:.2f}")

    print("\n== 2026 正常化归母净利（报表口径）==")
    print(f"H1 核心 = 扣非 {H1_KF:.3f} - 以前年度所得税调整 {H1_TAX_PRIOR:.3f} - 信用减值转回 {H1_CREDIT_REV:.3f}"
          f" - 汇兑 {H1_FX:.3f} - 权益法 {H1_ASSOC:.3f} = {H1_CORE:.3f}")
    for k in ("bear", "base", "bull"):
        print(f"{k}: H2 {H2_CORE[k]:.3f} → 2026 正常化归母 {NORM_NP_2026[k]:.2f}；估值起点 NOPAT {nopat_2026(k):.2f}"
              f"（+税后净利息 {NET_INT_AT:.2f} + 投资人少数损益 {AIC_MINORITY[k]:.2f}）")

    print("\n== 三情景（股权成本 9%，有杠杆口径）==")
    res = {}
    for k in ("bear", "base", "bull"):
        s = SCEN[k]
        ops, pv_tv, path = ops_value(k, COE)
        eq = equity(k)
        eq_u = equity(k, levered=False)
        res[k] = per_share(eq)
        avg_g = (path[-1] / nopat_2026(k)) ** (1 / 5) - 1
        print(f"{k}: p={s['p']:.2f} 增速 {[f'{g:.0%}' for g in s['g']]} 再投资率 {s['rr']:.0%} 终值 ROIC {s['roic_t']:.0%}")
        print(f"   NOPAT 2027-2031 {[round(x, 2) for x in path]}；5 年复合 {avg_g:.1%}；增量回报≈{avg_g/s['rr']:.0%}")
        print(f"   经营价值 {ops:.1f}（终值现值 {pv_tv:.1f}，占 {pv_tv/ops:.0%}）；股权 {eq:.1f} → V = {per_share(eq):.2f} 元"
              f"；无杠杆口径 V = {per_share(eq_u):.2f} 元；另计 {s['extra']:.1f}")
    vw = weighted()
    vw_u = weighted(levered=False)
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元（无杠杆口径 {vw_u:.2f} 元）；P/V = {pv:.2f} → {tier(pv)}")
    print(f"V 不变时各档价格：明显低估 ≤ {0.75*vw:.1f}；温和低估 {0.75*vw:.1f}–{0.90*vw:.1f}；"
          f"大致合理 {0.90*vw:.1f}–{1.10*vw:.1f}；偏贵 > {1.10*vw:.1f}")

    print("\n== 股权成本敏感性 ==")
    for r in (0.08, 0.10):
        parts = {k: per_share(equity(k, r)) for k in SCEN}
        print(f"COE {r:.0%}: 熊 {parts['bear']:.2f} / 基准 {parts['base']:.2f} / 牛 {parts['bull']:.2f} → 加权 {weighted(r):.2f}")

    irr = solve(lambda r: equity("base", r), 0.03, 0.30, MCAP)
    irr_w = solve(lambda r: sum(SCEN[k]["p"] * equity(k, r) for k in SCEN), 0.03, 0.30, MCAP)
    print(f"\n现价隐含回报（基准情景）= {irr:.2%}；按三情景加权现金流 = {irr_w:.2%}")

    # 反向 DCF：基准再投资率与终值 ROIC 不变，2027-2036 年 NOPAT 等速增长
    def eq_const_g(g):
        return equity("base", COE, gs=[g] * 10)
    g10 = solve(eq_const_g, -0.05, 0.60, MCAP)
    # Gordon：给定基准 2027 年所有者收益，现价隐含的永续增速
    need_ops = MCAP + (-NET_CASH_ADJ) * DEBT_RATE * (1 - TAX) / COE + AIC_CLAIMS - NON_OP
    oe27 = nopat_2026("base") * (1 + SCEN["base"]["g"][0]) * (1 - SCEN["base"]["rr"])
    g_perp = COE - oe27 / need_ops
    print(f"反向 DCF：现价需 2027-2036 年 NOPAT 年均增长 {g10:.1%}（再投资率 48%、此后 2.5%）；"
          f"或以基准 2027 年所有者收益 {oe27:.2f} 亿计的永续增速 {g_perp:.2%}")
    print(f"现价对应 PE：TTM 归母 10.38 亿 {MCAP/10.38:.1f} 倍；2026 正常化基准 {MCAP/NORM_NP_2026['base']:.1f} 倍")

    print("\n== 证伪触发后的 V（元/股）==")
    f1 = weighted(probs={"bear": 0.5, "base": 0.4, "bull": 0.1})
    f2 = weighted(probs={"bear": 0.1, "base": 0.5, "bull": 0.4})
    # LNG：2026 年报化工行业毛利率 < 20% 且合同负债 < 2 亿 → LNG 正常化利润再降 0.8 亿（各情景同减）
    saved = {k: NORM_NP_2026[k] for k in SCEN}
    for k in SCEN:
        NORM_NP_2026[k] = saved[k] - 0.8
    f3 = weighted()
    for k in SCEN:
        NORM_NP_2026[k] = saved[k]
    # 江苏先科 66.93% 以现金收购、对价 > 30 亿：内在价值约 1.6 亿×15 倍×66.93% ≈ 16.1 亿，超付 13.9 亿
    f4 = vw - 13.9 / SHARES
    print(f"F1 2026 年扣非归母 < 9.0 亿（2027-04-30）→ 权重 0.5/0.4/0.1：V = {f1:.2f}")
    print(f"F2 2027 年中报归母 ≥ 7.0 亿且半导体材料收入同比 ≥ 30%（2027-08-31）→ 权重 0.1/0.5/0.4：V = {f2:.2f}")
    print(f"F3 2026 年报化工行业毛利率 < 20% 且合同负债 < 2.0 亿（2027-04-30）→ LNG 正常化 -0.8 亿：V = {f3:.2f}")
    print(f"F4 2027-12-31 前以现金收购江苏先科 66.93%、对价 > 30 亿 → V = {f4:.2f}")
    f5 = weighted(probs={"bear": 0.6, "base": 0.3, "bull": 0.1})
    print(f"F5 TrendForce DRAM 合约价 2027 年任一季度环比跌 ≥ 10%（2027-12-31）→ 权重 0.6/0.3/0.1：V = {f5:.2f}")

    print("\n== 交叉验证 ==")
    # 历史 PE/PB（数据包第八节，年末收盘×年末股本÷当年归母、÷年末归母权益，2018-2025）
    pe_hist = [48.3, 36.7, 67.3, 115.4, 45.7, 45.8, 31.6, 35.3]
    pb_hist = [1.54, 2.43, 5.90, 6.45, 3.69, 3.84, 3.83, 4.48]
    med = lambda xs: sorted(xs)[len(xs) // 2 - 1: len(xs) // 2 + 1]
    pe_m, pb_m = sum(med(pe_hist)) / 2, sum(med(pb_hist)) / 2
    print(f"历史 PE 中位 {pe_m:.1f} 倍（区间 {min(pe_hist)}–{max(pe_hist)}）；PB 中位 {pb_m:.2f} 倍；"
          f"现价 PE(TTM) {MCAP/10.38:.1f}、PB {MCAP/80.00:.2f}")
    print(f"基准 V 对应 PE（2026 正常化）{vw*SHARES/NORM_NP_2026['base']:.1f} 倍、PB {vw*SHARES/80.00:.2f} 倍")
    # 分部加总（宽松口径）：子公司增资交易估值 + 前驱体与 LNG 给较高倍数
    sotp = {
        "成都科美特集团 77.15%×投后 40.48": 0.7715 * 40.48,
        "浙江华飞 65.08%×投后 15.37": 0.6508 * 15.37,
        "江苏先科 33.07%×2022 投后 24.6": 0.3307 * 24.6,
        "UP Chemical（韩国先科）3.4 亿×25 倍": 3.4 * 25,
        "LNG 板材与阻燃剂（母公司）3.4 亿×14 倍": 3.4 * 14,
        "雅克天然气 50%×0.5 亿×10 倍": 0.5 * 0.5 * 10,
        "雅克福瑞 82.5%×0.7 亿×20 倍": 0.825 * 0.7 * 20,
        "雅克南通 48.84%×0.38 亿×20 倍": 0.4884 * 0.38 * 20,
        "广州科美等 0.1 亿×15 倍": 0.1 * 15,
        "江苏雅睿 100%×账面 0.81": 0.81,
    }
    sotp_eq = sum(sotp.values()) - (-NET_CASH_ADJ) + NON_OP
    print("分部加总：" + "；".join(f"{k} {v:.1f}" for k, v in sotp.items()))
    print(f"分部合计 {sum(sotp.values()):.1f} - 经调整净负债 {-NET_CASH_ADJ:.1f} + 非经营 {NON_OP:.1f} = {sotp_eq:.1f} 亿 → {per_share(sotp_eq):.1f} 元/股")
    ev = MCAP + (DEBT - CASH_LIKE) + 33.85
    ebit_ttm = 12.71 - 7.10 + 7.554 + 0.355 - 0.20
    print(f"EV/EBIT：EV {ev:.1f}（市值+有息负债-现金类+少数股东权益账面 33.85）÷ TTM EBIT {ebit_ttm:.1f} = {ev/ebit_ttm:.1f} 倍")
    print(f"股息率（近 12 个月每股 0.66 元）{0.66/PRICE:.2%}；无回购")

    print("\n== 汇总 ==")
    print({k: round(v, 2) for k, v in res.items()}, "加权", round(vw, 2), "P/V", round(pv, 2),
          "COE8", round(weighted(0.08), 2), "COE10", round(weighted(0.10), 2), "IRR", round(irr, 4))


if __name__ == "__main__":
    main()
