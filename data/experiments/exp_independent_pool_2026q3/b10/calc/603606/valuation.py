#!/usr/bin/env python3
"""东方电缆（603606）独立估值：归母所有者收益 DCF，三情景概率加权。

运行：python3 valuation.py
全部输入写在本脚本内（金额单位亿元，股价与每股价值单位元）。
数据出处：2026 中报（2026H1_report）、2025 年报（2025_annual_report）、
2025 年度权益分派与回购公告、数据包快照（腾讯行情 2026-10-20）。
"""

# ---------------------------------------------------------------- 快照
PRICE = 34.14                      # 2026-10-20 收盘，元
SHARES_TOTAL = 8.24808488          # 亿股，含回购专户 224.9766 万股（2026H1_report 第 45 页）
TREASURY = 0.02249766              # 亿股，回购专户，用途为员工持股/股权激励，未公告注销
SHARES_EX_TREASURY = SHARES_TOTAL - TREASURY
MKT_CAP = PRICE * SHARES_TOTAL

# ---------------------------------------------------------------- 资产负债（2026-06-30）
CASH = 26.963                      # 货币资金（2026H1_report 第 50、101 页）
RESTRICTED = 4.552                 # 期货保证金 4.439 + 保函 0.073 + 信用证 0.040（第 25、101 页）
DEBT = {                           # 有息负债（第 140、144-146 页）
    "短期借款": 0.9945,
    "一年内到期长期借款": 4.3879,
    "一年内到期租赁负债": 0.0221,
    "长期借款": 3.8785,
    "租赁负债": 0.0042,
}
DEBT_LIKE = {
    "长期应付职工薪酬（OIMS 奖励基金）": 0.2027,   # 第 146 页
    "关联方房产尚未支付的 50% 购房款": 0.3665,      # 7,329.9 万元的 50%，第 42-43 页
}
TTM_REVENUE = 122.11               # 数据包 TTM 营收
OPERATING_RESERVE_RATE = 0.05      # 经营备付：TTM 营收的 5%
NON_OPERATING = {                  # 非经营资产（第 50 页）
    "其他权益工具投资（Aquora 等）": 0.751,
    "长期股权投资（联营）": 0.613,
    "投资性房地产": 0.130,
}
DERIVATIVE_ASSET = 0.911           # 套期衍生金融资产：对应存货与在手合同的铜价，列经营性，不计入现金

# 经营营运资金（用于判断是否需要正常化调整，单位亿元）
NWC_ROWS = {
    # 期末: (应收账款+票据+应收款项融资, 存货, 合同资产(含非流动), 预付, 应付票据, 应付账款, 合同负债, 营收口径)
    "2024-12-31": (34.77, 18.34, 0.80 + 3.80, 1.23, 14.66, 12.05, 11.48, 90.93),
    "2025-12-31": (36.45, 39.50, 0.65 + 4.74, 2.45, 19.68, 13.51, 23.70, 108.43),
    "2026-06-30": (47.40, 51.21, 0.52 + 6.06, 1.54, 36.58, 17.57, 20.67, 122.11),
}

# ---------------------------------------------------------------- 2026 正常化归母净利（分部毛利模型）
# 分部历史毛利率（f10 主营构成与 2026H1_report 第 157 页）：
#   海底电缆与高压电缆 2025H1 25.0% / 2025H2 38.1% / 2026H1 26.1%（三个半年按收入加权 31.1%）
#   电力工程与装备线缆 2025H1 10.8% / 2025H2 6.8% / 2026H1 10.5%
#   海洋装备与工程运维 2025H1 29.1% / 2025H2 23.4% / 2026H1 37.9%
SCENARIOS = {
    "bear": dict(
        p=0.30,
        rev={"陆缆": 58.0, "海缆与高压": 53.0, "海工": 10.75, "其他": 0.25},
        gm={"陆缆": 0.095, "海缆与高压": 0.265, "海工": 0.28, "其他": 0.70},
        opex=0.065, surtax=0.0055, impair=0.013, other_income=0.45, donation=0.15,
        net_fin=0.03, tax=0.155,
        growth=[0.04, 0.04, 0.03, 0.03, 0.025], g_terminal=0.020, roiic=0.12,
        text="海缆与高压毛利率回落到 26.5%（2025H1/2026H1 水平），高压陆缆价格战延续，"
             "海工 28%，减值率 1.3%；海风招标 2026 年同比腰斩后恢复缓慢，2027-2031 年净利增速 4%→2.5%，"
             "增量回报 12%，终值增长 2.0%",
    ),
    "base": dict(
        p=0.50,
        rev={"陆缆": 59.0, "海缆与高压": 58.0, "海工": 11.0, "其他": 0.25},
        gm={"陆缆": 0.095, "海缆与高压": 0.295, "海工": 0.30, "其他": 0.70},
        opex=0.065, surtax=0.0055, impair=0.012, other_income=0.50, donation=0.15,
        net_fin=0.03, tax=0.155,
        growth=[0.10, 0.09, 0.08, 0.06, 0.04], g_terminal=0.025, roiic=0.17,
        text="海缆与高压毛利率 29.5%（近三个半年加权 31.1% 打折，反映高压陆缆竞价与订单结构），"
             "陆缆 9.5%、海工 30%，期间费用率 6.5%，减值率 1.2%；179 亿元在手订单在 2026H2-2027 "
             "确认，十五五海风逐步兑现，2027-2031 年净利增速 10%/9%/8%/6%/4%，增量回报 17%",
    ),
    "bull": dict(
        p=0.20,
        rev={"陆缆": 60.0, "海缆与高压": 62.0, "海工": 12.0, "其他": 0.25},
        gm={"陆缆": 0.100, "海缆与高压": 0.325, "海工": 0.33, "其他": 0.70},
        opex=0.063, surtax=0.0055, impair=0.010, other_income=0.55, donation=0.15,
        net_fin=0.03, tax=0.155,
        growth=[0.18, 0.15, 0.12, 0.09, 0.06], g_terminal=0.025, roiic=0.22,
        text="深远海柔直与 500kV 项目维持 32.5% 海缆毛利率，十五五年均 15GW 海风与海外订单兑现，"
             "2027-2031 年净利增速 18%/15%/12%/9%/6%，增量回报 22%",
    ),
}

H2_SHARE_2026 = 0.57               # 2026 正常化净利中尚未进入 6-30 资产负债表的下半年部分
COE = 0.09
YEARS = [2027, 2028, 2029, 2030, 2031]
T_H2_2026 = 72 / 365               # 2026-10-20 → 2026-12-31
T_MID_2027 = 254 / 365             # 2026-10-20 → 2027-07-01（年度流量按年中折现）


def fmt(x, n=2):
    return f"{x:,.{n}f}"


def normalized_np(s):
    rev = s["rev"]
    total_rev = sum(rev.values())
    gp = sum(rev[k] * s["gm"][k] for k in rev)
    opex = total_rev * s["opex"]
    surtax = total_rev * s["surtax"]
    impair = total_rev * s["impair"]
    ebt = gp - opex - surtax - impair + s["other_income"] - s["donation"] + s["net_fin"]
    np_ = ebt * (1 - s["tax"])
    return dict(revenue=total_rev, gp=gp, gm=gp / total_rev, opex=opex, surtax=surtax,
                impair=impair, ebt=ebt, ebit=ebt - s["net_fin"], np=np_)


def net_cash_adj():
    debt = sum(DEBT.values())
    debt_like = sum(DEBT_LIKE.values())
    reserve = TTM_REVENUE * OPERATING_RESERVE_RATE
    return CASH - RESTRICTED - debt - debt_like - reserve, debt, debt_like, reserve


def flows(s, np2026=None, growth=None, roiic=None, g_terminal=None):
    """返回 [(t, 所有者收益)] 与终值所需的 2032 所有者收益。"""
    np0 = normalized_np(s)["np"] if np2026 is None else np2026
    growth = s["growth"] if growth is None else growth
    roiic = s["roiic"] if roiic is None else roiic
    g_t = s["g_terminal"] if g_terminal is None else g_terminal
    nps = [np0]
    for g in growth:
        nps.append(nps[-1] * (1 + g))
    nxt = list(growth) + [g_t]                 # 每年的再投资率由下一年增速决定
    reinv = [g / roiic for g in nxt]           # 2026..2031
    oe = [n * (1 - r) for n, r in zip(nps, reinv)]
    out = [(T_H2_2026, oe[0] * H2_SHARE_2026)]
    for i in range(1, len(oe)):
        out.append((T_MID_2027 + (i - 1), oe[i]))
    np_term = nps[-1] * (1 + g_t)
    oe_term = np_term * (1 - g_t / roiic)
    return out, oe_term, nps, reinv, oe


def equity_value(s, r, **kw):
    fl, oe_term, *_ = flows(s, **kw)
    g_t = s["g_terminal"] if kw.get("g_terminal") is None else kw["g_terminal"]
    pv = sum(cf / (1 + r) ** t for t, cf in fl)
    t_last = fl[-1][0]
    tv = oe_term / (r - g_t)
    pv_tv = tv / (1 + r) ** t_last
    nca = net_cash_adj()[0]
    nonop = sum(NON_OPERATING.values())
    return pv + pv_tv + nca + nonop, pv, pv_tv, tv


def per_share(s, r, shares=SHARES_TOTAL, **kw):
    return equity_value(s, r, **kw)[0] / shares


def weighted(r, weights=None, shares=SHARES_TOTAL):
    weights = weights or {k: v["p"] for k, v in SCENARIOS.items()}
    return sum(weights[k] * per_share(SCENARIOS[k], r, shares) for k in SCENARIOS)


def solve(fn, lo, hi, target, it=200):
    flo = fn(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = fn(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("=== 东方电缆（603606）独立估值 ===")
    print(f"价格 {PRICE} 元，总股本 {SHARES_TOTAL:.4f} 亿股（含回购专户 {TREASURY*1e4:.2f} 万股），"
          f"市值 {fmt(MKT_CAP)} 亿元")

    nca, debt, debt_like, reserve = net_cash_adj()
    nonop = sum(NON_OPERATING.values())
    print("\n--- 经调整净现金（2026-06-30）---")
    print(f"货币资金 {fmt(CASH)} − 受限 {fmt(RESTRICTED)} − 有息负债 {fmt(debt)} − 类债务 {fmt(debt_like)}"
          f" − 经营备付（TTM 营收 5%）{fmt(reserve)} = {fmt(nca)}")
    print(f"非经营资产 {fmt(nonop)}；套期衍生资产 {fmt(DERIVATIVE_ASSET)} 列经营性，不计入")
    print("经营营运资金（应收+存货+合同资产+预付−应付票据−应付账款−合同负债）：")
    for d, (ar, inv, ca, pre, npay, ap, cl, rev) in NWC_ROWS.items():
        nwc = ar + inv + ca + pre - npay - ap - cl
        print(f"  {d}: {fmt(nwc)} 亿元，占营收 {nwc/rev:.1%}；应付票据/营收 {npay/rev:.1%}")

    print("\n--- 2026 正常化归母净利 ---")
    for k, s in SCENARIOS.items():
        n = normalized_np(s)
        print(f"{k}: 营收 {fmt(n['revenue'])}，毛利 {fmt(n['gp'])}（{n['gm']:.1%}），"
              f"费用 {fmt(n['opex'])}，减值 {fmt(n['impair'])}，税前 {fmt(n['ebt'])}，归母净利 {fmt(n['np'])}"
              f"（净利率 {n['np']/n['revenue']:.1%}）")

    print("\n--- 三情景 DCF（股权成本 9%）---")
    res = {}
    for k, s in SCENARIOS.items():
        fl, oe_term, nps, reinv, oe = flows(s)
        ev, pv, pv_tv, tv = equity_value(s, COE)
        v = ev / SHARES_TOTAL
        v_ex = ev / SHARES_EX_TREASURY
        res[k] = v
        print(f"[{k}] p={s['p']:.2f}  V = {v:.2f} 元（剔除回购专户 {v_ex:.2f} 元）")
        print("   净利 2026-2031:", " / ".join(fmt(x) for x in nps))
        print("   再投资率 2026-2031:", " / ".join(f"{x:.0%}" for x in reinv))
        print("   所有者收益 2026-2031:", " / ".join(fmt(x) for x in oe),
              f"；2026 下半年计入 {fmt(oe[0]*H2_SHARE_2026)}")
        print(f"   显性期现值 {fmt(pv)}，终值 {fmt(tv)}（现值 {fmt(pv_tv)}，占经营价值 {pv_tv/(pv+pv_tv):.0%}），"
              f"股权价值 {fmt(ev)}，隐含 2026 正常化 PE {ev/normalized_np(s)['np']:.1f}x")

    vw = weighted(COE)
    vw_ex = weighted(COE, shares=SHARES_EX_TREASURY)
    pv_ratio = PRICE / vw
    print(f"\n加权 V = {vw:.2f} 元；P/V = {pv_ratio:.2f}（{band(pv_ratio)}）")
    print(f"剔除回购专户：V = {vw_ex:.2f} 元，P/V = {PRICE/vw_ex:.2f}")

    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：加权 V = {v8:.2f} 元（P/V {PRICE/v8:.2f}）；"
          f"10%：加权 V = {v10:.2f} 元（P/V {PRICE/v10:.2f}）")
    for r in (0.08, 0.10):
        print(f"   {int(r*100)}% 分情景：" + "，".join(
            f"{k} {per_share(SCENARIOS[k], r):.2f}" for k in SCENARIOS))

    base = SCENARIOS["base"]
    irr = solve(lambda r: equity_value(base, r)[0], 0.03, 0.30, MKT_CAP)
    print(f"现价隐含回报（基准情景流量）= {irr:.2%}")

    # 反向 DCF
    np_base = normalized_np(base)["np"]

    def val_uniform(g):
        gs10 = [g] * 10
        # 10 年同一增速，第 11 年起 2.5%
        nps = [np_base]
        for x in gs10:
            nps.append(nps[-1] * (1 + x))
        nxt = gs10 + [0.025]
        oe = [n * (1 - x / base["roiic"]) for n, x in zip(nps, nxt)]
        pv = oe[0] * H2_SHARE_2026 / (1 + COE) ** T_H2_2026
        for i in range(1, len(oe)):
            pv += oe[i] / (1 + COE) ** (T_MID_2027 + i - 1)
        oe_t = nps[-1] * 1.025 * (1 - 0.025 / base["roiic"])
        pv += oe_t / (COE - 0.025) / (1 + COE) ** (T_MID_2027 + 9)
        return pv + nca + nonop

    g10 = solve(val_uniform, 0.0, 0.40, MKT_CAP)

    def val_gordon(g):
        oe1 = np_base * (1 + g) * (1 - g / base["roiic"])
        return oe1 / (COE - g) / (1 + COE) ** (T_MID_2027 - 1) + nca + nonop

    gp_ = solve(val_gordon, 0.0, 0.0899, MKT_CAP)
    print(f"反向 DCF：以基准 2026 正常化净利 {np_base:.2f} 亿元、增量回报 17%，"
          f"现价隐含 2027-2036 年净利年增 {g10:.1%} 后转 2.5%；或永续增速 {gp_:.2%}")

    # 交叉验证
    ebit = normalized_np(base)["ebit"]
    ev_ = MKT_CAP - nca - nonop
    print("\n--- 交叉验证 ---")
    print(f"市值/TTM 归母 {MKT_CAP/13.63:.1f}x；市值/2026 基准正常化 {MKT_CAP/np_base:.1f}x；"
          f"EV/基准正常化 EBIT {ev_/ebit:.1f}x（EV {fmt(ev_)}）；PB {MKT_CAP/84.57:.2f}x")
    div_total = 3.8386
    print(f"2025 年度现金分红 {div_total:.2f} 亿元 + 2025 年回购 0.18 亿元，股息加回购收益率 "
          f"{(div_total+0.18)/MKT_CAP:.2%}")

    # 证伪触发后的 V
    print("\n--- 证伪触发后的 V（9%）---")
    bear = SCENARIOS["bear"]
    # F1：三季报确收未兑现 → 熊/基准各半
    f1 = weighted(COE, {"bear": 0.5, "base": 0.5, "bull": 0.0})
    # F2：海缆毛利率中枢下移到熊市水平，增长路径仍按基准
    f2 = per_share(base, COE, np2026=normalized_np(bear)["np"])
    # F3：新订单不能补充在手订单 → 基准增速降为 5/5/4/3/2.5%，与熊市各半
    f3 = 0.5 * per_share(base, COE, growth=[0.05, 0.05, 0.04, 0.03, 0.025]) + 0.5 * per_share(bear, COE)
    # F4：营运资金恶化，经调整净现金再减 8 亿元、减值率 +0.4pct
    f4_scen = {k: dict(v, impair=v["impair"] + 0.004) for k, v in SCENARIOS.items()}
    f4 = sum(f4_scen[k]["p"] * per_share(f4_scen[k], COE) for k in f4_scen) - 8.0 / SHARES_TOTAL
    # F5（上行）：权重移向牛市
    f5 = weighted(COE, {"bear": 0.15, "base": 0.45, "bull": 0.40})
    print(f"F1 2026-10-29 三季报单季毛利率<18% 且前三季度扣非<9.0 亿元：熊/基准各半 → V = {f1:.2f}")
    print(f"F2 2026 年报海底电缆与高压电缆全年毛利率<27%：正常化净利取熊市 {normalized_np(bear)['np']:.2f} 亿元、增长按基准 → V = {f2:.2f}")
    print(f"F3 2027-04-30 前披露的在手订单<150 亿元且海缆与高压<70 亿元：基准增速降为 5/5/4/3/2.5% 与熊市各半 → V = {f3:.2f}")
    print(f"F4 2026 年经营现金流<5 亿元或年末应收+合同资产（含非流动）>55 亿元：净现金 −8 亿元、减值率 +0.4pct → V = {f4:.2f}")
    print(f"F5（上行）2026 年归母≥16 亿元、海缆与高压毛利率≥32%、在手订单≥200 亿元：权重 0.15/0.45/0.40 → V = {f5:.2f}")

    print("\n--- 分档价格（V 不变）---")
    print(f"明显低估 ≤ {0.75*vw:.2f}；温和低估 {0.75*vw:.2f}～{0.90*vw:.2f}；"
          f"大致合理 {0.90*vw:.2f}～{1.10*vw:.2f}；偏贵 > {1.10*vw:.2f}")


if __name__ == "__main__":
    main()
