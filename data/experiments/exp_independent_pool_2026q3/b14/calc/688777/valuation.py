# -*- coding: utf-8 -*-
"""688777 中控技术 独立估值（OI-291 b14，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在本脚本内，出处见注释
（2026H1 = 2026 年半年报，2025AR = 2025 年年报，页码为 PDF 物理页）。
"""

# ---------------------------------------------------------------- 快照
PRICE = 72.74                    # 2026-10-20 收盘（brief）
SHARES = 7.9119                  # 总股本亿股（含回购专户；含 GDR 对应 A 股基础股票）
TREASURY_SH = (4876209 + 8867191) / 1e8
# 6-30 回购专户 11,233,509 股（2026H1 第 164 页）= 旧方案 4,876,209 股 + 现方案 6,357,300 股
# （现方案 8-31 累计 635.73 万股；5-8 月股价高于 68.53 元上限，未成交）；
# 现方案 10-19 累计 8,867,191 股（buyback_20261020 第 2 页）。用途：股权激励/员工持股，不注销。
MCAP = PRICE * SHARES

# ---------------------------------------------------------------- 经调整净现金（6-30 资产负债表 + 期后已知现金流）
CASH = 28.6045                   # 货币资金（2026H1 第 120 页），其中境外 20.16（多为 GDR 募集资金）
TFA = 16.0000                    # 交易性金融资产 = 银行理财（2026H1 第 121 页）
RESTRICTED = 0.5821              # 保函/票据保证金与涉诉冻结（2026H1 第 121 页）
OPER_RESERVE = 5.0               # 经营备付：约 3 周付现成本；6-30 已是季节性低点
INTERIM_DIV = 0.7800             # 2026 中期 10 派 1 元，9-15 股东会通过（dividend_20260829）
BUYBACK_AFTER_0630 = 5.0001 - 3.236  # 现方案累计 5.0001 亿，6-30 时约 3.236 亿（9-30 3.374 亿减 9-30 当日约 0.138 亿）
DEBT = 8.9995 + 0.0706 + 0.1501  # 短期借款 + 一年内到期租赁 + 租赁负债（2026H1 第 83、157 页）；无长期借款、无预计负债
NET_CASH = CASH + TFA - RESTRICTED - OPER_RESERVE - INTERIM_DIV - BUYBACK_AFTER_0630 - DEBT

# ---------------------------------------------------------------- 非经营资产（权益法收益不进经营 DCF）
LTEI = {  # 长期股权投资账面值（2026H1 第 141-143 页）, 折算系数
    "石化盈科（权益法，盈利并分红）": (7.1132, 1.0),
    "浙江人形机器人创新中心（无盈利）": (4.3443, 0.7),
    "北京达美盛（亏损）": (1.5879, 0.7),
    "浙江中控西子（盈利）": (1.0736, 1.0),
    "其余 18 家联营与创投合伙": (17.5945 - 7.1132 - 4.3443 - 1.5879 - 1.0736, 0.7),
}
FUNDS = (6.6912, 0.9)            # 其他非流动金融资产 = 基金，公允价值（2026H1 第 146 页）
OEI = (0.3964, 0.8)              # 其他权益工具投资
NON_OP = sum(v * k for v, k in LTEI.values()) + FUNDS[0] * FUNDS[1] + OEI[0] * OEI[1]
NON_OP_BOOK = 17.5945 + FUNDS[0] + OEI[0]

# ---------------------------------------------------------------- 2026E 报表口径估计（参考，非 V 输入）
REV_2026E = 77.0                 # H1 36.35 + H2 40.65（H2 2025 42.42 × 0.958）
# TTM（2025H2 + 2026H1）经营EBIT：毛利 24.42 − 税金及附加 0.61 − 三费 23.61 + 其他收益 2.74 − 减值 1.73
EBIT_TTM = 24.42 - 0.61 - 23.61 + 2.74 - 1.73


def pnl_2026(rev, gm, opex, oi, imp, assoc, wealth, fin, tax_rate, mi=0.02):
    ebit_op = rev * gm - 0.008 * rev - opex + oi - imp
    ebt = ebit_op + assoc + wealth + fin
    return ebit_op, ebt * (1 - tax_rate) * (1 - mi)


# 报表口径 2026E：GM 31.5%，费用 24.4（H1 11.10 + H2 13.3），其他收益 2.55（含非经常补助约 0.5），
# 减值 1.45，联营 0.55，理财 0.55，财务净收益 0.10（含汇兑约 -0.2），税率约 0
REPORTED_2026E = pnl_2026(REV_2026E, 0.315, 24.4, 2.55, 1.45, 0.55, 0.55, 0.10, 0.0)

# 正常化 2026 归母（报表口径：含联营与净利息 = 利息+理财-利息支出-手续费，剔除非经常补助、汇兑、公允价值；
# 收入取中周期水平，减值取常态）
NORMALIZED_2026 = {
    #        收入  毛利率  费用   其他收益(经常)  减值   联营  净利息  税率
    "bear": (79.0, 0.313, 24.48, 0.025 * 79.0, 0.016 * 79.0, 0.50, 0.75, 0.03),
    "base": (84.0, 0.318, 24.73, 0.026 * 84.0, 0.013 * 84.0, 0.60, 0.80, 0.06),
    "bull": (89.0, 0.325, 24.98, 0.027 * 89.0, 0.010 * 89.0, 0.70, 0.85, 0.08),
}

# ---------------------------------------------------------------- 三情景经营 DCF
# 经营 EBIT = 毛利 - 税金及附加 - 三费(含研发、股份支付) + 经常性其他收益(软件退税等) - 常态减值；
# 不含联营收益与利息（现金与非经营资产另加）。所有者收益 = EBIT×(1-税)×(1-少数) - 再投资率×Δ收入。
SCEN = {
    "bear": dict(p=0.25,
                 rev_g=[0.006, 0.038, 0.043, 0.041, 0.040],
                 margin=[0.008, 0.018, 0.028, 0.037, 0.045],
                 fade_g=[0.030, 0.028, 0.026, 0.025, 0.025],
                 fade_m=[0.047, 0.049, 0.050, 0.050, 0.050],
                 tax_e=0.05, tax_t=0.08, reinv=0.33,
                 text="主业随化工资本开支继续低迷（2027 年持平、此后 3-4%），工业AI 2031 年约 16 亿且低毛利，"
                      "管理层压住费用，经营利润率 2031 年 4.5%、终值 5.0%"),
    "base": dict(p=0.50,
                 rev_g=[0.078, 0.084, 0.078, 0.067, 0.058],
                 margin=[0.024, 0.041, 0.058, 0.069, 0.079],
                 fade_g=[0.050, 0.044, 0.038, 0.031, 0.025],
                 fade_m=[0.083, 0.086, 0.088, 0.090, 0.090],
                 tax_e=0.08, tax_t=0.10, reinv=0.30,
                 text="主业 2027 年企稳、此后年增约 3-4%，工业AI 2026 年约 9 亿、2031 年约 28 亿（毛利率升至 45%），"
                      "费用年增 4.5%，经营利润率 2031 年 7.9%、终值 9.0%（低于 2017-2024 年 9-14%）"),
    "bull": dict(p=0.25,
                 rev_g=[0.162, 0.211, 0.156, 0.119, 0.099],
                 margin=[0.060, 0.114, 0.151, 0.175, 0.193],
                 fade_g=[0.100, 0.080, 0.060, 0.040, 0.025],
                 fade_m=[0.195, 0.195, 0.195, 0.195, 0.195],
                 tax_e=0.10, tax_t=0.12, reinv=0.22,
                 text="工业AI 大致按激励触发值放量（2027 年 18 亿、2028 年 32 亿、2031 年 65 亿，毛利率 55%），"
                      "主业回到 90 亿，经营利润率 2031 年 19.3%、终值 19.5%"),
}
YEARS = list(range(2027, 2037))
T0 = 0.70        # 2026-10-20 至 2027 年年中
G_T = 0.025
MI = 0.02        # 少数股东占比（2025 年 3.7%，2026H1 收购少数股权后约 0）


def scenario(s, r):
    rev_prev, pv, flows = REV_2026E, 0.0, []
    gs, ms = s["rev_g"] + s["fade_g"], s["margin"] + s["fade_m"]
    nopat = 0.0
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + gs[i])
        tax = s["tax_e"] if i < 5 else s["tax_t"]
        ebit = rev * ms[i]
        nopat = ebit * (1 - tax) * (1 - MI)
        oe = nopat - s["reinv"] * (rev - rev_prev)
        pv += oe / (1 + r) ** (T0 + i)
        flows.append((y, rev, ebit, nopat, oe))
        rev_prev = rev
    ronic = ms[-1] * (1 - s["tax_t"]) * (1 - MI) / s["reinv"]
    rr = G_T / ronic
    tv = nopat * (1 + G_T) * (1 - rr) / (r - G_T)
    pv_tv = tv / (1 + r) ** (T0 + 9)
    ev = pv + pv_tv
    return dict(pv=pv, pv_tv=pv_tv, ev=ev, eq=ev + NET_CASH + NON_OP, flows=flows, ronic=ronic, rr=rr)


def value(r, weights=None, shares=SHARES):
    out = {}
    for k, s in SCEN.items():
        out[k] = scenario(s, r)["eq"] / shares
    w = weights or {k: s["p"] for k, s in SCEN.items()}
    return out, sum(w[k] * out[k] for k in out)


def irr_base():
    lo, hi = 0.0, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if mid <= G_T + 1e-6:
            lo = mid
            continue
        if scenario(SCEN["base"], mid)["eq"] > MCAP:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(base_oe, r=0.09, years=10):
    """现价隐含：(a) 永续增速；(b) 10 年所有者收益复合增速（此后 2.5%）。"""
    ev_mkt = MCAP - NET_CASH - NON_OP
    g_perp = (ev_mkt * r - base_oe) / (ev_mkt + base_oe)
    lo, hi = -0.2, 1.0
    for _ in range(200):
        g = (lo + hi) / 2
        pv, oe = 0.0, base_oe
        for t in range(1, years + 1):
            oe *= 1 + g
            pv += oe / (1 + r) ** (t - 0.3)
        pv += oe * (1 + G_T) / (r - G_T) / (1 + r) ** (years - 0.3)
        if pv > ev_mkt:
            hi = g
        else:
            lo = g
    return ev_mkt, g_perp, (lo + hi) / 2


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


if __name__ == "__main__":
    print("== 快照 ==")
    print(f"现价 {PRICE:.2f} 元 × 总股本 {SHARES:.4f} 亿股 = 市值 {MCAP:.1f} 亿；回购专户 {TREASURY_SH*1e4:.1f} 万股（{TREASURY_SH/SHARES:.2%}）")
    print(f"经调整净现金 {NET_CASH:.2f} 亿（现金 {CASH:.2f} + 理财 {TFA:.2f} - 受限 {RESTRICTED:.2f} - 备付 {OPER_RESERVE:.1f}"
          f" - 中期股利 {INTERIM_DIV:.2f} - 6-30 后回购 {BUYBACK_AFTER_0630:.2f} - 有息负债 {DEBT:.2f}）")
    print(f"非经营资产 {NON_OP:.2f} 亿（账面 {NON_OP_BOOK:.2f}）；合计 {NET_CASH+NON_OP:.2f} 亿 = {(NET_CASH+NON_OP)/SHARES:.2f} 元/股")

    print("\n== 2026 年利润 ==")
    eb, np_ = REPORTED_2026E
    print(f"报表口径 2026E：经营EBIT {eb:.2f}，归母约 {np_:.2f} 亿（H1 实际 1.55；TTM 2.42）")
    norm = {}
    for k, v in NORMALIZED_2026.items():
        rev, gm, opex, oi, imp, assoc, ni, tx = v
        e, n = pnl_2026(rev, gm, opex, oi, imp, assoc, ni, 0.0, tx)
        norm[k] = n
        print(f"正常化 {k}: 收入 {rev:.0f}，经营EBIT {e:.2f}（{e/rev:.1%}），归母 {n:.2f} 亿")

    print("\n== 三情景（股权成本 9%） ==")
    for k, s in SCEN.items():
        res = scenario(s, 0.09)
        print(f"[{k}] p={s['p']:.2f} V={res['eq']/SHARES:.2f} 元；经营价值 {res['ev']:.1f}（明确期 {res['pv']:.1f}，终值 {res['pv_tv']:.1f}，"
              f"终值占比 {res['pv_tv']/res['ev']:.0%}）；RONIC {res['ronic']:.1%}，终值再投资率 {res['rr']:.1%}")
        for y, rev, ebit, nopat, oe in res["flows"][:5]:
            print(f"    {y}: 收入 {rev:6.1f} 经营EBIT {ebit:5.2f}（{ebit/rev:5.1%}） NOPAT {nopat:5.2f} 所有者收益 {oe:5.2f}")
        y, rev, ebit, nopat, oe = res["flows"][-1]
        print(f"    {y}: 收入 {rev:6.1f} 经营EBIT {ebit:5.2f}（{ebit/rev:5.1%}） NOPAT {nopat:5.2f} 所有者收益 {oe:5.2f}  → 终值增长 2.5%")

    vs, vw = value(0.09)
    pv = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元；P/V = {pv:.2f}（{tier(pv)}）")
    vs_ex, vw_ex = value(0.09, shares=SHARES - TREASURY_SH)
    print(f"剔除回购专户股份（{SHARES-TREASURY_SH:.4f} 亿股）：加权 V = {vw_ex:.2f}，P/V = {PRICE/vw_ex:.2f}")
    for r in (0.08, 0.10):
        v_r, w_r = value(r)
        print(f"股权成本 {r:.0%}：熊 {v_r['bear']:.2f} / 基 {v_r['base']:.2f} / 牛 {v_r['bull']:.2f}，加权 {w_r:.2f}，P/V {PRICE/w_r:.2f}")
    irr = irr_base()
    print(f"现价隐含回报（基准情景现金流）：{irr:.2%}")

    base_oe_norm = 2.16   # 正常化 2026 基准经营 NOPAT：EBIT 2.40 ×(1-6%)×(1-2%)
    ev_mkt, g_perp, g10 = reverse_dcf(base_oe_norm)
    print(f"反向 DCF：市场隐含经营价值 {ev_mkt:.1f} 亿；以正常化经营收益 {base_oe_norm:.2f} 亿为起点，永续增速 {g_perp:.2%}，"
          f"或 10 年复合 {g10:.1%} 后转 2.5%")
    peak_nopat = 9.29 * 0.96 * 0.97
    ev_mkt, g_perp2, g10b = reverse_dcf(peak_nopat)
    print(f"          以 2024 年高点经营收益 {peak_nopat:.2f} 亿为起点：永续 {g_perp2:.2%}，或 10 年复合 {g10b:.1%}")

    print("\n== 交叉验证 ==")
    ev_mkt = MCAP - NET_CASH - NON_OP
    print(f"EV（市值-净现金-非经营资产）{ev_mkt:.0f} 亿；EV/TTM 经营EBIT（{EBIT_TTM:.2f}）{ev_mkt/EBIT_TTM:.0f}×；EV/2024 经营EBIT（9.29）{ev_mkt/9.29:.0f}×")
    print(f"PE(TTM 2.42) {MCAP/2.42:.0f}×；PE(正常化基准 {norm['base']:.2f}) {MCAP/norm['base']:.0f}×；PB {MCAP/98.55:.2f}（2023-2025 年末 3.65-3.90）")
    print(f"PB 回到 3.8 倍：{98.55*3.8/SHARES:.1f} 元；2024 年归母 11.17 亿 × 35 倍（2024 年末 PE）：{11.17*35/SHARES:.1f} 元")
    print(f"股息率（近 12 月每股 0.28 + 中期 0.10）{0.38/PRICE:.2%}；回购 5.0 亿用于激励，不计股东回报")
    core_val = 6.0 * 13.0
    print(f"分部粗算：主业按 2024 年水平经营 NOPAT 约 6 亿 × 13 倍 = {core_val:.0f} 亿 → 市场隐含工业AI 价值 {ev_mkt-core_val:.0f} 亿，"
          f"约 2026E 工业AI 收入 9 亿的 {(ev_mkt-core_val)/9:.0f} 倍")

    print("\n== 激励考核路径对照（现价隐含什么） ==")
    paths = {
        "目标值路径（营收 2027 年 145、2028 年 200 亿，经营利润率 20%）":
            dict(p=0, rev_g=[145 / REV_2026E - 1, 200 / 145 - 1, 0.12, 0.10, 0.08], margin=[0.08, 0.14, 0.18, 0.20, 0.20],
                 fade_g=[0.07, 0.06, 0.05, 0.04, 0.025], fade_m=[0.20] * 5, tax_e=0.10, tax_t=0.12, reinv=0.22),
        "触发值路径（营收 2027 年 110、2028 年 135 亿，经营利润率 19.5%）":
            dict(p=0, rev_g=[110 / REV_2026E - 1, 135 / 110 - 1, 0.12, 0.10, 0.08], margin=[0.06, 0.12, 0.16, 0.18, 0.19],
                 fade_g=[0.07, 0.06, 0.05, 0.04, 0.025], fade_m=[0.195] * 5, tax_e=0.10, tax_t=0.12, reinv=0.22),
    }
    for name, s in paths.items():
        print(f"{name}：V(9%) = {scenario(s, 0.09)['eq']/SHARES:.1f}，V(8%) = {scenario(s, 0.08)['eq']/SHARES:.1f}")

    print("\n== 经营利润拆分（经营EBIT，亿元） ==")
    ebit_2024 = 30.95 - 0.59 - 21.84 + 2.69 - 1.92          # 2025AR 第 145-146 页（2024 列）
    ebit_ttm = EBIT_TTM
    one_off = 0.62 / 2 + 0.28                                # 非经常政府补助：2025 全年 0.62 折半 + 2026H1 0.28
    e_norm = pnl_2026(*NORMALIZED_2026["base"][:7], 0.0, 0.0)[0]
    print(f"2024 年 {ebit_2024:.2f}（{ebit_2024/91.39:.1%}）→ TTM {ebit_ttm:.2f}（{ebit_ttm/78.77:.1%}）；"
          f"一次性（非经常补助）{one_off:.2f}；扣除后经常性 {ebit_ttm-one_off:.2f}")
    print(f"周期性（收入回到中周期 84 亿、减值回到常态，扣 2026 年费用增长）+{e_norm-(ebit_ttm-one_off):.2f} → 正常化 {e_norm:.2f}")
    opex_step = 24.73 - 21.84
    gm_step = (0.339 - 0.318) * 84.0
    print(f"结构性（相对 2024 年）{ebit_2024-e_norm:.2f}：费用抬升 {opex_step:.2f}、毛利率下移 {gm_step:.2f}、"
          f"收入中枢下移及其他 {ebit_2024-e_norm-opex_step-gm_step:.2f}")

    print("\n== 证伪触发后的 V（重设情景权重，9%） ==")
    fals = {
        "F1 2026 年工业AI收入<8亿或营收<74亿": {"bear": 0.45, "base": 0.45, "bull": 0.10},
        "F2 三季报 Q3 单季营收<16.4亿（同比-10%）或单季归母亏损": {"bear": 0.40, "base": 0.50, "bull": 0.10},
        "F3 2026 年末一年以上应收>17亿或全年减值>2.5亿": {"bear": 0.50, "base": 0.45, "bull": 0.05},
        "F4 2027 年工业AI收入≥20亿且扣非归母≥8亿（上行）": {"bear": 0.05, "base": 0.35, "bull": 0.60},
        "F5 2027H1 化工投资转正且营收同比≥10%（上行）": {"bear": 0.15, "base": 0.55, "bull": 0.30},
    }
    for name, w in fals.items():
        _, v_f = value(0.09, weights=w)
        extra = 2.0 / SHARES if name.startswith("F3") else 0.0
        print(f"{name}: V = {v_f - extra:.2f}（P/V {PRICE/(v_f-extra):.2f}）")

    print("\n== 现价进入各档的价格（V 不变） ==")
    print(f"明显低估 ≤ {0.75*vw:.1f}；温和低估 {0.75*vw:.1f}-{0.90*vw:.1f}；大致合理 {0.90*vw:.1f}-{1.10*vw:.1f}；偏贵 > {1.10*vw:.1f}")
