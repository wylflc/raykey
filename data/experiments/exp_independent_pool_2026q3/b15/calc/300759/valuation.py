#!/usr/bin/env python3
"""康龙化成（300759.SZ / 3759.HK）独立估值（OI-291 b15，深度版）。

口径：
- 价格日 2026-10-20；A 股收盘 39.09 元；H 股收盘 27.12 港元，港元兑人民币 0.8507（腾讯行情 2026-10-21 读数）。
- 每股价值按全部股份 18.3728 亿股（A 14.7731 + H 3.5998，含库存 H 股 186.683 万股）计算；另列剔除库存 H 股的对照。
- 金额单位亿元。资产负债表取 2026-06-30（2026 中报），再加 2026-09-02 发行的 21.80 亿元零息可转债募集净额（备考）。
- 经调整净现金为负，按框架用有杠杆口径：经营所有者收益现值 − 净负债税后利息永续现值 + 非经营资产；
  可转债不进净现金与杠杆滚动，逐情景在「按面值全额扣除」与「全部转股」之间取每股价值较低者。
- 所有者收益 = 经营 NOPAT ×（1 − 下一年增速 / 增量 ROIC）；终值增长 ≤ 2.5%。
运行：python3 valuation.py
"""

# ---------------- 输入：行情与股本 ----------------
PRICE_A = 39.09                   # 元/股，2026-10-20 A 股收盘
PRICE_H_HKD = 27.12               # 港元，2026-10-20 H 股收盘（腾讯行情昨收字段）
HKD_CNY = 0.8507                  # 腾讯行情 2026-10-21
USD_CNY = 6.6787                  # 腾讯行情 2026-10-21（一年内高点 7.1332）
SHARES_A = 14.77305741            # 亿股，可转债公告 2026-067 股权结构表
SHARES_H_TOTAL = 3.59977887       # 亿股，含库存 H 股（2026 中报第 49 页）
TREASURY_H = 0.0186683            # 亿股，库存 H 股（可转债公告注 1），未公告注销
SHARES = SHARES_A + SHARES_H_TOTAL  # 18.3728 亿股，与 brief 一致
SHARES_EX_TREASURY = SHARES - TREASURY_H

# ---------------- 输入：2026-06-30 资产负债（中报第 56-58、99-100、106、115-121 页） ----------------
CASH = 15.7613                    # 货币资金
WMP = 8.7620                      # 交易性金融资产（银行理财）
DERIV_ASSET = 0.0145              # 衍生金融资产
REPO = 3.7013                     # 其他流动资产中的国债逆回购
RESTRICTED = 1.1855               # 受限货币资金（保证金等）
DIV_PAYABLE = 3.6496              # 应付股利（2026-07-07 已派）
EQUITY_INV_PAYABLE = 0.4407       # 其他应付款中的应付股权投资款（类债务）
ST_LOAN = 11.3938
LT_LOAN = 19.2050
LT_LOAN_CURRENT = 34.1454         # 一年内到期的长期借款（不含可转债，中报第 119 页）
LEASE_CURRENT = 1.2668
LEASE = 3.5271
DERIV_LIAB = 0.0467
DEBT = ST_LOAN + LT_LOAN + LT_LOAN_CURRENT + LEASE_CURRENT + LEASE + DERIV_LIAB  # 69.585
TTM_REVENUE = 152.50
OPER_RESERVE = 0.05 * TTM_REVENUE  # 经营备付：TTM 收入的 5%
CB_NET_PROCEEDS = 3.272 * 6.722    # 可转债募集净额 3.272 亿美元 × 发行隐含汇率（2,223.6 百万元 / 330.8 百万美元）
NET_CASH_ADJ_H1 = (CASH + WMP + DERIV_ASSET + REPO - RESTRICTED - OPER_RESERVE
                   - DIV_PAYABLE - EQUITY_INV_PAYABLE - DEBT)
NET_CASH_ADJ = NET_CASH_ADJ_H1 + CB_NET_PROCEEDS   # 备考（含可转债现金，不含可转债负债）
NET_DEBT = -NET_CASH_ADJ
INT_RATE = 1.1514 * 2 / ((DEBT + 70.40) / 2)       # 2026H1 利息支出（资本化前）年化 / 平均有息负债
TAX_SHIELD = 0.20

# 非经营资产：其他非流动金融资产（非上市基金与股权，公允价值）全额 + 长期股权投资按 70%（联营企业 2025 年权益法亏损 1.36 亿）
OTHER_NC_FA = 6.9747
LT_EQUITY_INV = 7.9079
NON_OP = OTHER_NC_FA + 0.70 * LT_EQUITY_INV

# 可转债：人民币 21.80 亿元、零息、2027-08-31 前后到期、到期按本金美元等值赎回；初始转换价 36.08 港元，约 7,047.86 万股 H 股
CB_FACE = 21.80
CB_SHARES = 0.70478579

# ---------------- 正常化利润 ----------------
# 2026H1 正常化归母净利 = 报告 7.502 + 汇兑相关亏损 1.04×(1−15%) − 金融资产公允价值收益 0.520×(1−20%) − 权益法收益 0.203 + 架构调整一次性支出 0.34
NP_H1_2026_REPORTED = 7.5019
NP_H1_2026_NORM = NP_H1_2026_REPORTED + 1.04 * 0.85 - 0.5198 * 0.80 - 0.2032 + 0.34
# 2025H2 正常化 = 报告 9.625 − 汇兑收益 0.346×85% + 权益法亏损 1.029 − 公允价值收益 0.473×80%
NP_H2_2025_NORM = (16.6390 - 7.0140) - 0.346 * 0.85 + 1.029 - 0.473 * 0.80
NET_INTEREST_AT = 1.20             # 2026 税后净利息（净利息约占收入 1.0%，扣税 20%）

COE = 0.09
STUB = 72 / 365                    # 2026-10-20 至 2026-12-31

SCENARIOS = {
    "bear": dict(p=0.25, h2_growth=0.06,
                 g=[0.03, 0.06, 0.06, 0.05, 0.05, 0.04, 0.04, 0.035, 0.03, 0.025],
                 roic_inc=0.09, g_t=0.020, roic_t=0.09,
                 note="人民币续升与生物科技融资回落、美国生物安全法清单风险；2027 年 NOPAT 仅 +3%，增量 ROIC 9%（≈股权成本）"),
    "base": dict(p=0.50, h2_growth=0.15,
                 g=[0.16, 0.14, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04],
                 roic_inc=0.15, g_t=0.025, roic_t=0.12,
                 note="新签订单 +30% 兑现，收入 2027 年约 +15%，CDMO 毛利率回升、大分子与 CGT 亏损收窄；增量 ROIC 15%"),
    "bull": dict(p=0.25, h2_growth=0.22,
                 g=[0.20, 0.18, 0.16, 0.14, 0.12, 0.10, 0.09, 0.07, 0.06, 0.045],
                 roic_inc=0.20, g_t=0.025, roic_t=0.15,
                 note="CDMO 商业化放量、利润率回到 2021 年附近；增量 ROIC 20%"),
}


def norm_np_2026(s):
    return NP_H1_2026_NORM + NP_H2_2025_NORM * (1 + s["h2_growth"])


def dcf(s, coe=COE, np2026=None, nopat_shock=0.0):
    """返回经营所有者收益现值等中间量（亿元）。nopat_shock：2027 年起 NOPAT 一次性下调比例（证伪情景用）。"""
    np26 = norm_np_2026(s) if np2026 is None else np2026
    nopat = np26 + NET_INTEREST_AT
    g = s["g"]
    path, oe, pv = [], [], 0.0
    n = nopat
    for i, gi in enumerate(g):
        n = n * (1 + gi) * ((1 - nopat_shock) if i == 0 else 1.0)
        g_next = g[i + 1] if i + 1 < len(g) else s["g_t"]
        roic = s["roic_inc"] if i + 1 < len(g) else s["roic_t"]
        o = n * (1 - g_next / roic)
        t = i + 1 + STUB  # 年末现金流：2027 年末距价格日 1.197 年
        pv += o / (1 + coe) ** t
        path.append(n)
        oe.append(o)
    n_t1 = path[-1] * (1 + s["g_t"])
    tv = n_t1 * (1 - s["g_t"] / s["roic_t"]) / (coe - s["g_t"])
    t_last = len(g) + STUB
    pv_tv = tv / (1 + coe) ** t_last
    pv_total = pv + pv_tv
    lev_interest_pv = NET_DEBT * INT_RATE * (1 - TAX_SHIELD) / coe
    eq_lev = pv_total - lev_interest_pv + NON_OP
    eq_unlev = pv_total - NET_DEBT + NON_OP
    return dict(np26=np26, nopat26=nopat, path=path, oe=oe, pv_oe=pv, pv_tv=pv_tv,
                pv_total=pv_total, tv_share=pv_tv / pv_total, lev_interest_pv=lev_interest_pv,
                eq_lev=eq_lev, eq_unlev=eq_unlev)


def per_share(eq):
    """可转债逐情景取低：债务口径（面值全额扣除，股本不变）与转股口径（股本加转股数，不扣转债）。"""
    v_debt = (eq - CB_FACE) / SHARES
    v_conv = eq / (SHARES + CB_SHARES)
    return min(v_debt, v_conv), v_debt, v_conv


def scenario_values(coe=COE):
    out = {}
    for k, s in SCENARIOS.items():
        r = dcf(s, coe)
        v, vd, vc = per_share(r["eq_lev"])
        vu, vud, vuc = per_share(r["eq_unlev"])
        out[k] = dict(r, v=v, v_debt=vd, v_conv=vc, v_unlev=vu, v_unlev_debt=vud, v_unlev_conv=vuc)
    return out


def weighted(vals, key="v"):
    return sum(SCENARIOS[k]["p"] * vals[k][key] for k in vals)


def implied_irr(s):
    """基准情景所有者收益流（含终值、净负债利息、非经营资产与可转债债务口径）现值等于 A 股市值的折现率。"""
    target = PRICE_A * SHARES
    lo, hi = 0.03, 0.20
    for _ in range(200):
        mid = (lo + hi) / 2
        r = dcf(s, mid)
        eq = r["eq_lev"] - CB_FACE
        if eq > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf():
    """现价隐含：10 年 NOPAT 恒定增速 g（增量 ROIC 15%，再投资率 g/15%），之后 2.5% 永续（ROIC 12%）。"""
    target = PRICE_A * SHARES + CB_FACE
    base = SCENARIOS["base"]
    lo, hi = 0.0, 0.40
    for _ in range(200):
        mid = (lo + hi) / 2
        s = dict(base, g=[mid] * 10)
        r = dcf(s)
        if r["eq_lev"] > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def segment_sotp():
    """分部交叉验证：2026E 分部收入 × 正常化毛利率 − 分部费用强度（实验室 23%、CDMO 15%、临床 8%，
    合计约等于集团期间费用、税金及附加扣其他收益后的 18.9%）→ 正常化 EBIT，各自用两段式所有者收益模型（股权成本 9%）。"""
    segs = {
        # 名称: (2026E 收入, 正常化毛利率, 费用强度, 10 年 NOPAT 增速, 增量 ROIC)
        "实验室服务": (97.3, 0.420, 0.23, 0.09, 0.18),
        "CDMO 服务": (46.8, 0.300, 0.15, 0.14, 0.12),
        "临床研究服务": (22.3, 0.130, 0.08, 0.07, 0.10),
    }
    res = {}
    for name, (rev, gm, opex, g, roic) in segs.items():
        ebit = rev * (gm - opex)
        nopat = ebit * (1 - TAX_SHIELD)
        s = dict(g=[g] * 10, roic_inc=roic, g_t=0.025, roic_t=min(roic, 0.12), h2_growth=0.0)
        r = dcf(s, COE, np2026=nopat - NET_INTEREST_AT)
        res[name] = dict(rev=rev, gm=gm, opex=opex, ebit=ebit, nopat=nopat, value=r["pv_total"])
    total = sum(v["value"] for v in res.values())
    eq_lev = total - NET_DEBT * INT_RATE * (1 - TAX_SHIELD) / COE + NON_OP
    return res, total, per_share(eq_lev)[0]


def reverse_perpetual(roic=0.15):
    """现价隐含永续增速：2026 正常化 NOPAT × (1 − g/ROIC) / (9% − g) = A 股市值 + 可转债 + 净负债利息现值 − 非经营资产。"""
    r = dcf(SCENARIOS["base"])
    target = PRICE_A * SHARES + CB_FACE + r["lev_interest_pv"] - NON_OP
    n = r["nopat26"]
    lo, hi = 0.0, 0.0899
    for _ in range(200):
        g = (lo + hi) / 2
        v = n * (1 - g / roic) / (COE - g)
        if v > target:
            hi = g
        else:
            lo = g
    return (lo + hi) / 2


def main():
    vals = scenario_values()
    vw = weighted(vals)
    print("=== 康龙化成（300759）独立估值 ===")
    print(f"股本 {SHARES:.4f} 亿股（A {SHARES_A:.4f} + H {SHARES_H_TOTAL:.4f}，含库存 H 股 {TREASURY_H*1e4:.2f} 万股）")
    print(f"H 股价 {PRICE_H_HKD} 港元 = {PRICE_H_HKD*HKD_CNY:.2f} 元；A/H 溢价 {PRICE_A/(PRICE_H_HKD*HKD_CNY):.2f} 倍")
    print(f"A 股价×全部股本 {PRICE_A*SHARES:.2f} 亿；A、H 各按本地价 {PRICE_A*SHARES_A + PRICE_H_HKD*HKD_CNY*SHARES_H_TOTAL:.2f} 亿")
    print(f"有息负债 {DEBT:.2f}；2026-06-30 经调整净现金 {NET_CASH_ADJ_H1:.2f}；加可转债募集净额 {CB_NET_PROCEEDS:.2f} 后（备考）{NET_CASH_ADJ:.2f}")
    print(f"有息负债实际平均利率 {INT_RATE:.4f}；非经营资产 {NON_OP:.2f}；经营备付 {OPER_RESERVE:.2f}")
    print(f"2026H1 正常化归母净利 {NP_H1_2026_NORM:.3f}；2025H2 正常化 {NP_H2_2025_NORM:.3f}")
    for k in ("bear", "base", "bull"):
        r = vals[k]
        s = SCENARIOS[k]
        print(f"\n[{k}] p={s['p']}  2026 正常化归母净利 {r['np26']:.2f}，NOPAT {r['nopat26']:.2f}")
        print("  NOPAT 增速 2027-2036:", ", ".join(f"{x:.1%}" for x in s["g"]), f"；终值 {s['g_t']:.1%}")
        print("  NOPAT:", ", ".join(f"{x:.1f}" for x in r["path"]))
        print("  所有者收益:", ", ".join(f"{x:.1f}" for x in r["oe"]))
        print(f"  再投资率 2027={s['g'][1]/s['roic_inc']:.0%}，增量 ROIC {s['roic_inc']:.0%}，终值再投资率 {s['g_t']/s['roic_t']:.0%}")
        print(f"  PV(10年) {r['pv_oe']:.1f} + PV(终值) {r['pv_tv']:.1f} = {r['pv_total']:.1f}，终值占比 {r['tv_share']:.1%}")
        print(f"  有杠杆：− 净负债税后利息现值 {r['lev_interest_pv']:.1f} + 非经营 {NON_OP:.1f} → 股权 {r['eq_lev']:.1f}")
        print(f"  每股：债务口径 {r['v_debt']:.2f}，转股口径 {r['v_conv']:.2f} → 取低 V={r['v']:.2f}")
        print(f"  无杠杆对照（全额扣净负债 {NET_DEBT:.1f}）：V={r['v_unlev']:.2f}")
    print(f"\n加权 V（有杠杆，取低）= {vw:.2f}；P/V(A) = {PRICE_A/vw:.3f}；P/V(H) = {PRICE_H_HKD*HKD_CNY/vw:.3f}")
    vwu = weighted(vals, "v_unlev")
    print(f"加权 V（无杠杆对照）= {vwu:.2f}；P/V(A) = {PRICE_A/vwu:.3f}")
    # 剔除库存 H 股的对照
    vx = sum(SCENARIOS[k]["p"] * min((vals[k]["eq_lev"] - CB_FACE) / SHARES_EX_TREASURY,
                                     vals[k]["eq_lev"] / (SHARES_EX_TREASURY + CB_SHARES)) for k in vals)
    print(f"剔除库存 H 股（{SHARES_EX_TREASURY:.4f} 亿股）加权 V = {vx:.2f}；P/V = {PRICE_A/vx:.3f}")
    for c in (0.08, 0.10):
        vc = scenario_values(c)
        print(f"股权成本 {c:.0%}：bear {vc['bear']['v']:.2f} / base {vc['base']['v']:.2f} / bull {vc['bull']['v']:.2f}；加权 {weighted(vc):.2f}")
    irr = implied_irr(SCENARIOS["base"])
    print(f"现价隐含回报（基准情景）= {irr:.2%}")
    g_imp = reverse_dcf()
    print(f"反向 DCF：现价隐含 10 年 NOPAT 年增速 {g_imp:.1%}（增量 ROIC 15%，之后 2.5% 永续）")
    print(f"反向 DCF：现价隐含永续增速 {reverse_perpetual(0.15):.2%}（增量 ROIC 15%）；{reverse_perpetual(0.25):.2%}（增量 ROIC 25%）")
    # 分档价格
    print(f"V 不变时：≤0.75 明显低估 价格 ≤ {0.75*vw:.2f}；0.90 → {0.90*vw:.2f}；1.10 → {1.10*vw:.2f}")
    # 交叉验证
    base = vals["base"]
    ev_a = PRICE_A * SHARES + NET_DEBT + CB_FACE - NON_OP
    ebit26 = base["nopat26"] / (1 - TAX_SHIELD)
    print(f"\n交叉验证：EV(A 价) {ev_a:.1f}，2026E 正常化 EBIT {ebit26:.1f}，EV/EBIT {ev_a/ebit26:.1f}x；"
          f"市值/2026 正常化归母 {PRICE_A*SHARES/base['np26']:.1f}x；股息率 {0.20/PRICE_A:.2%}")
    res, total, v_sotp = segment_sotp()
    for name, d in res.items():
        print(f"  分部 {name}: 收入 {d['rev']:.1f}，毛利率 {d['gm']:.1%}，费用强度 {d['opex']:.0%}，EBIT {d['ebit']:.1f}，NOPAT {d['nopat']:.1f}，经营价值 {d['value']:.1f}")
    print(f"  分部合计经营价值 {total:.1f} → 每股 {v_sotp:.2f}")
    # 证伪触发后的 V
    print("\n证伪条件触发后的 V：")
    f1 = dcf(SCENARIOS["base"], np2026=18.0)
    print(f"  F1 2026 全年正常化归母净利 < 18.0（基准其余不变）：V={per_share(f1['eq_lev'])[0]:.2f}")
    f2 = dcf(SCENARIOS["bear"], nopat_shock=0.20)
    print(f"  F2 被列入美国「受关注生物技术公司」：熊市路径且 2027 NOPAT 再降 20%：V={per_share(f2['eq_lev'])[0]:.2f}")
    s3 = dict(SCENARIOS["base"], roic_inc=0.11)
    f3 = dcf(s3)
    print(f"  F3 CDMO 毛利率未回升、增量 ROIC 降至 11%（增速不变）：V={per_share(f3['eq_lev'])[0]:.2f}")
    s4 = dict(SCENARIOS["base"], g=[0.08, 0.08, 0.07, 0.07, 0.06, 0.05, 0.05, 0.04, 0.035, 0.03])
    f4 = dcf(s4)
    print(f"  F4 2027 年新签订单增速 < 10%，基准增速减半：V={per_share(f4['eq_lev'])[0]:.2f}")
    s5 = SCENARIOS["bull"]
    f5 = dcf(s5)
    print(f"  F5（向上）2027 年正常化归母净利 ≥ 26：按牛市情景 V={per_share(f5['eq_lev'])[0]:.2f}")


if __name__ == "__main__":
    main()
