#!/usr/bin/env python3
"""云路股份（688190）独立估值：所有者收益 DCF，三情景概率加权。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。所有输入写在本脚本内，出处见正文
`b04/companies/688190_云路股份.md`。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 63.14                 # 2026-10-19 收盘（brief.md）
SHARES = 1.2000               # 亿股，总股本；无回购专户（2026H1_report 第 55 页）
VAL_DATE = date(2026, 10, 19)
COE = 0.09
MKT_CAP = PRICE * SHARES      # 75.77 亿元

# ---------------------------------------------------------------- 经调整净现金（2026-06-30）
CASH = 1.2316                 # 货币资金，期末无受限（2026H1 第 59、129 页）
TRADING_FA = 1.5030           # 交易性金融资产（银行理财，第 59 页）
CD_CURRENT = 8.4077           # 其他流动资产中一年内到期的大额存单（第 117 页）
CD_NONCURRENT = 0.8076        # 其他非流动资产中的大额存单（第 129 页）
RESTRICTED = 0.0              # 期末受限货币资金为 0（第 129 页）
DIV_PAID_AFTER = 0.30         # 2026 中期分红 0.25 元/股，2026-10-16 已除息发放
LEASE_DEBT = 0.0951 + 0.6382  # 一年内到期的租赁负债 + 租赁负债（第 60 页）；无银行借款
OP_RESERVE = 1.50             # 经营备付：约 1 个月付现成本
RELATED_DEPOSITS = 0.0        # 无财务公司或关联方存款
NON_OPERATING = 0.0           # 无长期股权投资等非经营资产

GROSS_CASH = CASH + TRADING_FA + CD_CURRENT + CD_NONCURRENT
NET_CASH_ADJ = GROSS_CASH - RESTRICTED - DIV_PAID_AFTER - LEASE_DEBT - OP_RESERVE

# ---------------------------------------------------------------- 2026 上半年正常化（实际数）
H1_REV = 9.9838
H1_NP = 1.2573                # 归母净利
H1_NP_DEDUCT = 1.1569         # 扣非归母（含理财与大额存单收益，第 6–8 页）
H1_FX_LOSS = 0.05471          # 汇兑损失，周期项，税后加回（第 139 页）
TAX_H1 = 0.13
# 经常性净金融收益（税前）：投资收益 11.08 + 公允价值 0.25 − 列入非经常的 1.45
# + 利息收入 0.32 − 利息支出（租赁）1.38，单位百万元（第 139–140 页）
H1_FIN_PRETAX = (11.0795 + 0.2494 - 1.4505 + 0.3218 - 1.3762) / 100
H1_NORM_NP = H1_NP_DEDUCT + H1_FX_LOSS * (1 - TAX_H1)          # 含净利息
H1_OP_NP = H1_NORM_NP - H1_FIN_PRETAX * (1 - TAX_H1)            # 剔除金融收益
TAX = 0.125                   # 高新 15% 叠加研发加计扣除，2025 年 13.1%、2026H1 11.5%

# ---------------------------------------------------------------- 情景
# h2: 2026 下半年假设（收入、毛利率、四项费用含税金及附加、经常性其他收益、
#     减值、净金融收益税前）
# rev/margin: 2027–2031 收入与经营净利率（扣除金融收益后的归母净利 / 收入）
# capex_g: 增长性资本开支（2026H2, 2027..2031），维护性资本开支取等于折旧摊销
# nwc_pct: 新增营运资本占新增收入比例；nwc_release: 营运资本强度改善释放额
SCENARIOS = {
    "bear": dict(
        p=0.25,
        h2=dict(rev=9.10, gm=0.218, opex=0.97, other=0.025, impair=-0.13, fin=0.07),
        rev=[18.00, 18.60, 19.90, 20.90, 21.70],
        margin=[0.090, 0.090, 0.092, 0.094, 0.095],
        capex_g=[0.40, 1.50, 1.30, 0.30, 0.30, 0.30],
        nwc_pct=0.45, nwc_release=[0, 0, 0, 0, 0],
        g=0.020, roic=0.09,
        text="印度对华非晶金属征税（参照同案 CRNO 每吨 224–415 美元），2027 年印度收入少约 1.6 亿；"
             "国内价格战延续，毛利率约 22%；纳米晶与粉末维持低毛利；终值增长 2%、增量回报 9%",
    ),
    "base": dict(
        p=0.50,
        h2=dict(rev=9.40, gm=0.233, opex=0.98, other=0.025, impair=-0.11, fin=0.07),
        rev=[19.90, 20.90, 22.60, 24.00, 25.20],
        margin=[0.108, 0.110, 0.113, 0.116, 0.118],
        capex_g=[0.40, 1.50, 1.30, 0.30, 0.30, 0.30],
        nwc_pct=0.40, nwc_release=[0, 0, 0, 0, 0],
        g=0.025, roic=0.12,
        text="毛利率停在 23%–24%（非晶约 31%–32%，纳米晶与粉末低个位数），2028-08 新增 4.8 万吨后"
             "2029–2031 年利用率爬到约 70%；印度按概率计入部分损失；终值增长 2.5%、增量回报 12%",
    ),
    "bull": dict(
        p=0.25,
        h2=dict(rev=9.60, gm=0.245, opex=0.99, other=0.025, impair=-0.09, fin=0.07),
        rev=[21.30, 23.40, 26.20, 28.80, 31.10],
        margin=[0.123, 0.129, 0.134, 0.138, 0.140],
        capex_g=[0.40, 1.70, 1.60, 0.80, 0.80, 0.60],
        nwc_pct=0.35, nwc_release=[0.30, 0.30, 0, 0, 0],
        g=0.025, roic=0.15,
        text="印度裁定排除非晶金属；国内价格企稳、一级能效与数据中心拉动非晶份额；纳米晶与粉末在"
             "AIDC、光储、车载起量，毛利率回到约 26.5%；营运资本强度改善；终值增长 2.5%、增量回报 15%",
    ),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def t_years(d):
    return (d - VAL_DATE).days / 365.25


T_H2 = 0.0                                       # 2026 下半年现金流（中点在价格日前后）
T_MID = [t_years(date(y, 7, 1)) for y in YEARS]  # 年中折现
T_TV = T_MID[-1]                                 # 终值：2032 年起现金流折到 2031 年中


def h2_numbers(s):
    h = s["h2"]
    pbt = h["rev"] * h["gm"] - h["opex"] + h["other"] + h["impair"] + h["fin"]
    np_h2 = pbt * (1 - TAX)
    op_np_h2 = (pbt - h["fin"]) * (1 - TAX)
    return np_h2, op_np_h2


def build(s):
    np_h2, op_np_h2 = h2_numbers(s)
    norm_np_2026 = H1_NORM_NP + np_h2
    op_np_2026 = H1_OP_NP + op_np_h2
    rev_2026 = H1_REV + s["h2"]["rev"]
    op_np = [r * m for r, m in zip(s["rev"], s["margin"])]
    revs = [rev_2026] + s["rev"]
    d_nwc = [s["nwc_pct"] * (revs[i + 1] - revs[i]) - s["nwc_release"][i] for i in range(5)]
    oe_h2 = op_np_h2 - s["capex_g"][0]
    oe = [op_np[i] - s["capex_g"][i + 1] - d_nwc[i] for i in range(5)]
    oe_2032 = op_np[-1] * (1 + s["g"]) * (1 - s["g"] / s["roic"])
    return dict(norm_np_2026=norm_np_2026, op_np_2026=op_np_2026, rev_2026=rev_2026,
                op_np=op_np, d_nwc=d_nwc, oe_h2=oe_h2, oe=oe, oe_2032=oe_2032)


def equity_value(s, r):
    b = build(s)
    pv = b["oe_h2"] / (1 + r) ** T_H2
    pv += sum(cf / (1 + r) ** t for cf, t in zip(b["oe"], T_MID))
    tv = b["oe_2032"] / (r - s["g"])
    pv_tv = tv / (1 + r) ** T_TV
    eq = pv + pv_tv + NET_CASH_ADJ + NON_OPERATING
    return eq, pv_tv


def per_share(s, r):
    return equity_value(s, r)[0] / SHARES


def weighted(r, scen=SCENARIOS, probs=None):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * per_share(scen[k], r) for k in scen)


def solve(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def variant(name, **changes):
    s = {k: (list(v) if isinstance(v, list) else (dict(v) if isinstance(v, dict) else v))
         for k, v in SCENARIOS[name].items()}
    s.update(changes)
    return s


def main():
    print("=== 云路股份 688190 独立估值（价格日 2026-10-19，股权成本 9%）===")
    print(f"现价 {PRICE:.2f} 元；总股本 {SHARES:.4f} 亿股；市值 {MKT_CAP:.2f} 亿元")
    print(f"现金类合计 {GROSS_CASH:.2f}（货币 {CASH:.2f} + 理财 {TRADING_FA:.2f} + 大额存单 "
          f"{CD_CURRENT + CD_NONCURRENT:.2f}）− 已发中期分红 {DIV_PAID_AFTER:.2f} − 租赁负债 "
          f"{LEASE_DEBT:.2f} − 经营备付 {OP_RESERVE:.2f} = 经调整净现金 {NET_CASH_ADJ:.2f} 亿元"
          f"（{NET_CASH_ADJ / SHARES:.2f} 元/股）；为正，按无杠杆口径全额扣除有息负债")
    print(f"2026H1 正常化归母净利 {H1_NORM_NP:.3f}（扣非 {H1_NP_DEDUCT:.4f} + 税后汇兑损失加回），"
          f"其中经营部分 {H1_OP_NP:.3f}")
    print()
    results = {}
    for k in ("bear", "base", "bull"):
        s = SCENARIOS[k]
        b = build(s)
        eq, pv_tv = equity_value(s, COE)
        v = eq / SHARES
        results[k] = v
        growth = [b["op_np"][0] / b["op_np_2026"] - 1] + [
            b["op_np"][i] / b["op_np"][i - 1] - 1 for i in range(1, 5)]
        reinv = sum(s["capex_g"][1:]) + sum(b["d_nwc"])
        rr = reinv / sum(b["op_np"])
        inc_ret = (b["op_np"][-1] - b["op_np_2026"]) / reinv
        print(f"[{k}] p={s['p']:.2f}  2026 正常化归母净利 {b['norm_np_2026']:.2f}（经营 {b['op_np_2026']:.2f}，"
              f"收入 {b['rev_2026']:.2f}）")
        print("   经营净利 2027–2031: " + " ".join(f"{x:.2f}" for x in b["op_np"])
              + "；增速 " + " ".join(f"{g:+.1%}" for g in growth))
        print(f"   所有者收益 2026H2 {b['oe_h2']:.2f}；2027–2031: " + " ".join(f"{x:.2f}" for x in b["oe"])
              + f"；2032 {b['oe_2032']:.2f}")
        print(f"   2027–2031 再投资率 {rr:.1%}，增量回报 {inc_ret:.1%}；终值增长 {s['g']:.1%}，"
              f"终值期增量回报 {s['roic']:.0%}；终值现值占股权价值 {pv_tv / eq:.0%}")
        print(f"   V = {v:.2f} 元/股（8%: {per_share(s, 0.08):.2f}；10%: {per_share(s, 0.10):.2f}）")
    vw = weighted(COE)
    pv_ratio = PRICE / vw
    print()
    print(f"概率加权 V = {vw:.2f} 元/股；P/V = {pv_ratio:.2f} → {band(pv_ratio)}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：加权 V {v8:.2f}（P/V {PRICE / v8:.2f}）；10%：加权 V {v10:.2f}（P/V {PRICE / v10:.2f}）")
    irr = solve(lambda r: equity_value(SCENARIOS["base"], r)[0] - MKT_CAP,
                SCENARIOS["base"]["g"] + 0.001, 0.30)
    print(f"现价隐含回报（基准情景所有者收益流 + 终值 + 净现金）：{irr:.2%}")
    print(f"V 不变时的分档价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}–{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}–{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    # ------------------------------------------------------------ 反向 DCF
    ev_mkt = MKT_CAP - NET_CASH_ADJ
    op0 = build(SCENARIOS["base"])["op_np_2026"]
    roic_now = 0.13
    g_perp = solve(lambda g: op0 * (1 + g) * (1 - g / roic_now) / (COE - g) - ev_mkt, 0.0, 0.0899)

    def pv_10y(g, roic=None):
        """前 10 年经营净利年增 g，再投资率 g/roic（roic=None 表示增长不需再投资），之后 2.5%。"""
        total, npv = 0.0, op0
        for i in range(1, 11):
            npv *= (1 + g)
            oe = npv * (1 - (g / roic if roic else 0.0))
            total += oe / (1 + COE) ** (i - 0.5)
        tv = npv * 1.025 * (1 - 0.025 / 0.12) / (COE - 0.025)
        return total + tv / (1 + COE) ** 9.5

    max_pv_13 = max(pv_10y(i / 1000, roic_now) for i in range(0, 130))
    g10_free = solve(lambda g: pv_10y(g) - ev_mkt, 0.0, 0.40)
    g10_r20 = solve(lambda g: pv_10y(g, 0.20) - ev_mkt, 0.0, 0.199)
    print()
    print(f"反向 DCF：现价减经调整净现金 = 经营价值 {ev_mkt:.2f} 亿元，为 2026 经营净利 {op0:.2f} 的 "
          f"{ev_mkt / op0:.1f} 倍")
    print(f"   永续口径（增量回报 13%）隐含永续增长 {g_perp:.2%}，高于 2.5% 上限")
    print(f"   10 年口径（之后 2.5%）：增长不需再投资时隐含经营净利年增 {g10_free:.2%}；增量回报 20% 时"
          f"隐含年增 {g10_r20:.2%}；增量回报 13% 时任何增速的现值最高只有 {max_pv_13:.1f} 亿，到不了现价")
    ebit_2026 = op0 / (1 - TAX)
    print(f"   EV/经营税前利润（2026 正常化）= {ev_mkt / ebit_2026:.1f} 倍")

    # ------------------------------------------------------------ 证伪条件触发后的 V
    print()
    print("证伪条件触发后的独立 V：")
    # F1 印度对华非晶金属征税：基准情景下 2027 起每年再少 1.1 亿收入、经营净利率下降 2.4 个百分点
    base = SCENARIOS["base"]
    f1 = variant("base", rev=[r - 1.1 for r in base["rev"]],
                 margin=[m - 0.024 for m in base["margin"]])
    v_f1 = weighted(COE, scen={"bear": SCENARIOS["bear"], "base": f1, "bull": SCENARIOS["bear"]},
                    probs={"bear": 0.40, "base": 0.60, "bull": 0.0})
    print(f"   F1 印度对华非晶金属征收反倾销税：V ≈ {v_f1:.2f}")
    v_f1b = weighted(COE, probs={"bear": 0.15, "base": 0.50, "bull": 0.35})
    print(f"   F1 反向：印度终裁排除非晶金属（熊市权重移 10 个百分点到牛市）：V ≈ {v_f1b:.2f}")
    # F2 毛利率跌破 21%：熊市情景权重升到 60%
    v_f2 = weighted(COE, probs={"bear": 0.60, "base": 0.35, "bull": 0.05})
    print(f"   F2 单季毛利率 < 21% 或 2026 年非晶单价 < 12,300 元/吨：V ≈ {v_f2:.2f}")
    # F3 现金转化恶化：基准情景新增营运资本率 55%，2027 年再吸收 1.0 亿
    f3 = variant("base", nwc_pct=0.55, nwc_release=[-1.0, 0, 0, 0, 0])
    v_f3 = weighted(COE, scen={"bear": SCENARIOS["bear"], "base": f3, "bull": SCENARIOS["bull"]})
    print(f"   F3 2026 年经营现金流 < 1.0 亿或年末应收合计 > 11.5 亿：V ≈ {v_f3:.2f}")
    # F4 关联方应收失控：一半关联方应收（1.3 亿）税后核销，熊市权重升到 40%
    v_f4 = weighted(COE, probs={"bear": 0.40, "base": 0.45, "bull": 0.15}) - 0.65 * (1 - 0.15) / SHARES
    print(f"   F4 关联方应收 > 1.8 亿或出现逾期减值：V ≈ {v_f4:.2f}")
    # F5 上行：纳米晶与粉末毛利率回到 15% 以上且 2027H1 毛利率 ≥ 26%
    v_f5 = weighted(COE, probs={"bear": 0.10, "base": 0.45, "bull": 0.45})
    print(f"   F5（上行）新品类毛利率 ≥ 15% 且 2027H1 毛利率 ≥ 26%：V ≈ {v_f5:.2f}")


if __name__ == "__main__":
    main()
