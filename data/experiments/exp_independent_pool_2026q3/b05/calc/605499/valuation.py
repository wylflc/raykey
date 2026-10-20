#!/usr/bin/env python3
"""东鹏饮料（605499）独立估值（OI-291 b05，价格日 2026-10-19）。

方法：归母所有者收益 DCF（熊／基准／牛三情景，股权成本 9%，敏感性 8%／10%），
加经调整净现金与非经营资产；另算反向 DCF 与现价隐含回报。
金额单位亿元，每股为元/股。输入全部写在脚本内，运行：python3 valuation.py

出处（页码为 PDF 物理页）：
- 2026H1_report 第 6、30、32-35、64-73、110、123-124、137-143、149-156 页；
- 2025_annual_report 第 11-13、34-36、43-44、116-117 页；
- 2026Q1_report 第 4-5 页；buyback_20261010_272449；dividend_20260918_527668；
- 回购报告书（2026-05-07，H2_AN202605061821992974_1.pdf）：不低于 90% 的回购股份用于注销。
"""

from __future__ import annotations

PRICE = 113.04            # 2026-10-19 A 股收盘（brief.md）
SHARES_TOTAL = 7.3420     # 亿股，A+H 全部股份，含回购专户（brief.md；中报第 58-59 页 734,199,310 股）
TREASURY = 0.07122551     # 亿股，A 股回购专户（buyback_20261010_272449）
CANCEL_SHARE = 0.90       # 回购报告书：不低于 90% 用于注销
SHARES = SHARES_TOTAL - TREASURY * CANCEL_SHARE      # 扣除拟注销部分后的每股口径
SHARES_EX_TREASURY = SHARES_TOTAL - TREASURY         # 对照：剔除全部回购专户股份

COE = 0.09
TAX = 0.21                # 2025 年 20.96%、2026H1 20.9%（年报第 116 页、中报第 69 页）

# ---------------- 经调整净现金（2026-06-30，亿元；中报第 64-65、110、123-124、137-143 页） ----------------
CASH = 144.7470           # 货币资金（含应收利息 1.5041、回购专户资金 1.6116）
RESTRICTED = 0.0847       # 银行保证金等受限资金
TFA = 64.5385             # 交易性金融资产（理财产品）
CD_IN_OCA = 4.9134        # 其他流动资产中的大额存单
NCA_DUE_1Y = 17.9453      # 一年内到期的债权投资（大额存单、定期存款）
DEBT_INV = 1.0513         # 债权投资
ONCFA_WEALTH = 1.2265     # 其他非流动金融资产中的理财产品
PE_FUND = 6.5343          # 其他非流动金融资产中的私募股权基金（招赢朗曜）
PE_HAIRCUT = 0.25         # 流动性与估值折扣
ST_LOANS = 56.4870        # 短期借款（贴现借款 54.80 + 信用借款 1.69，利率 0.55%-2.08%）
LEASE = 0.1904 + 3.9130   # 一年内到期租赁负债 + 租赁负债
DIVIDEND_DECLARED = 21.8123   # 2026 年中期分红，8-31 股东会通过、9-24 除息（dividend_20260918_527668）
OP_RESERVE = 14.0         # 经营备付：约 1 个月现金经营成本（2026E 营收约 232 − EBITDA 约 66）/12

FIN_ASSETS = CASH - RESTRICTED + TFA + CD_IN_OCA + NCA_DUE_1Y + DEBT_INV + ONCFA_WEALTH
DEBT = ST_LOANS + LEASE
NET_CASH_SIMPLE = FIN_ASSETS - DEBT
NET_CASH_ADJ = NET_CASH_SIMPLE - DIVIDEND_DECLARED - OP_RESERVE
NON_OP = PE_FUND * (1 - PE_HAIRCUT)

# 正常化净利息（税前，年化）：金融资产约 212 亿（扣 9 月分红后）× 约 1.9% − 贴现借款与租赁利息约 1.0 亿
NET_INTEREST_PRETAX = 3.0
NET_INTEREST_AT = NET_INTEREST_PRETAX * (1 - TAX)

# ---------------- 经营假设 ----------------
REV_2025 = 208.75         # 2025 营收（年报第 116 页）
WC_FLOAT = 0.20           # 营收增量带来的营运资本流入比例（合同负债+应付；2023-2025 实际 0.24-0.47）
GC_RATIO = 0.35           # 扩产资本开支 / 营收增量（2023-2025 实际 0.23-0.35）
# 维护性资本开支 = 折旧摊销（两者在所有者收益中相抵）；冰柜与促销已在销售费用中

YEARS = [2027, 2028, 2029, 2030, 2031]
T_FIRST = 0.70            # 2027 年现金流按年中折现：2026-10-19 → 2027-07-01 约 0.70 年
T_TV = T_FIRST + len(YEARS) - 1   # 2032 年起的现金流按年中到账，其 Gordon 值位于 2031 年中（4.70 年）
T_STUB = 0.20             # 2026 下半年自由现金流在 2026-12-31 前到账
CAPEX_GROWTH_2026 = 16.0  # 2026E 资本开支约 22.9（上半年 11.35）− 折旧摊销约 6.6，仅用于 2026 参照行

SCENARIOS = {
    "bear": dict(
        p=0.30,
        rev2026=229.0,
        growth=[0.01, 0.02, 0.025, 0.03, 0.025],
        tg=0.020,
        core_margin=0.196,              # 核心经营利润率（营收−成本−税金−销售−管理−研发）
        pipeline=[10.0, 6.0, 3.0, 2.0, 0.0],   # 已规划基地的扩产开支（超出维护部分）
        wc_shock={2027: -8.0},          # 竞争下经销商预付款回落
        ronic_tv=0.25,
        stub=26.0,                      # 2026 下半年自由现金流（2025 下半年实际 31.8）
        text="能量饮料价格战持续、品类零售额继续下滑，特饮收入两年小幅下降；电解质持平；原料按油价 100 美元重置；"
             "核心经营利润率回到 2021-2023 年的 19.6%；营收 2027-2031 年 +1%/2%/2.5%/3%/2.5%，终值增长 2%；"
             "经销商预付款回落 8 亿；终值增量回报 25%",
    ),
    "base": dict(
        p=0.50,
        rev2026=232.0,
        growth=[0.055, 0.055, 0.05, 0.045, 0.04],
        tg=0.025,
        core_margin=0.235,
        pipeline=[12.0, 9.0, 6.0, 3.0, 0.0],
        wc_shock={},
        ronic_tv=0.40,
        stub=29.0,
        text="特饮低个位数增长、省外渗透延续，茶与咖啡等新品类拉动，营收 2027-2031 年 +5.5%/5.5%/5%/4.5%/4%，终值 2.5%；"
             "PET 与白糖回到周期中位、促销强度高于 2025 年，核心经营利润率 23.5%（2025 年 24.5%，2026E 约 25.5%）；"
             "扩产开支 2027-2030 年 12/9/6/3 亿；终值增量回报 40%",
    ),
    "bull": dict(
        p=0.20,
        rev2026=235.0,
        growth=[0.10, 0.09, 0.08, 0.07, 0.06],
        tg=0.025,
        core_margin=0.253,
        pipeline=[14.0, 12.0, 9.0, 6.0, 0.0],
        wc_shock={},
        ronic_tv=0.50,
        stub=31.0,
        text="特饮恢复中个位数增长并凭东方大鹏提价、电解质企稳、新品类与海外放量，营收 2027-2031 年 +10%/9%/8%/7%/6%，终值 2.5%；"
             "2026 年的核心经营利润率约 25.3% 得以维持；终值增量回报 50%",
    ),
}


def project(s: dict) -> dict:
    """逐年营收、经营归母净利（不含利息）、再投资与所有者收益。"""
    np_margin = s["core_margin"] * (1 - TAX)
    rev_prev = s["rev2026"]
    rows = []
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s["growth"][i])
        d_rev = rev - rev_prev
        np_op = rev * np_margin
        growth_capex = max(s["pipeline"][i], GC_RATIO * max(d_rev, 0.0))
        wc_in = WC_FLOAT * d_rev + s["wc_shock"].get(y, 0.0)
        reinvest = growth_capex - wc_in
        oe = np_op - reinvest
        rows.append(dict(year=y, rev=rev, np_op=np_op, growth_capex=growth_capex, wc_in=wc_in,
                         reinvest=reinvest, oe=oe))
        rev_prev = rev
    rev_tv = rev_prev * (1 + s["tg"])
    np_tv = rev_tv * np_margin
    oe_tv = np_tv * (1 - s["tg"] / s["ronic_tv"])
    np2026_op = s["rev2026"] * np_margin
    oe2026 = np2026_op - (CAPEX_GROWTH_2026 - WC_FLOAT * (s["rev2026"] - REV_2025))
    return dict(rows=rows, oe_tv=oe_tv, np_tv=np_tv, np_margin=np_margin, oe2026=oe2026,
                np2026_op=np2026_op, np2026_norm=np2026_op + NET_INTEREST_AT)


def equity_value(s: dict, r: float) -> dict:
    pr = project(s)
    pv_rows = sum(row["oe"] / (1 + r) ** (T_FIRST + i) for i, row in enumerate(pr["rows"]))
    tv = pr["oe_tv"] / (r - s["tg"])
    pv_tv = tv / (1 + r) ** T_TV
    pv_stub = s["stub"] / (1 + r) ** T_STUB
    eq = pv_rows + pv_tv + pv_stub + NET_CASH_ADJ + NON_OP
    return dict(pr=pr, pv_rows=pv_rows, tv=tv, pv_tv=pv_tv, pv_stub=pv_stub, equity=eq,
                v=eq / SHARES, v_ex_treasury=eq / SHARES_EX_TREASURY,
                tv_share=pv_tv / eq)


def weighted(r: float) -> float:
    return sum(s["p"] * equity_value(s, r)["v"] for s in SCENARIOS.values())


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


def implied_irr(s: dict) -> float:
    """基准情景现金流（含终值与净现金）现值等于现价时的折现率。"""
    return solve(lambda r: equity_value(s, r)["v"], 0.04, 0.30, target=PRICE)


def reverse_dcf() -> dict:
    """现价隐含增长。基准正常化利润率与终值增量回报 40% 不变。"""
    base = SCENARIOS["base"]
    mcap = PRICE * SHARES
    ev_op = mcap - NET_CASH_ADJ - NON_OP - base["stub"] / (1 + COE) ** T_STUB
    np_margin = base["core_margin"] * (1 - TAX)
    np27 = base["rev2026"] * 1.0 * np_margin   # 以 2026 正常化经营利润为起点

    # (a) 永续增长：2027 年起 OE = NP×(1+g)^k×(1−g/RONIC)，首笔在 0.70 年，Gordon 值位于 −0.30 年
    def gordon(g):
        return np27 * (1 + g) * (1 - g / base["ronic_tv"]) / (COE - g) / (1 + COE) ** (T_FIRST - 1)
    g_perp = solve(gordon, -0.05, 0.085, target=ev_op)

    # (b) 10 年所有者收益增速（再投资率按 g/40%），其后 2.5% 永续
    def ten_year(g):
        v = 0.0
        np_t = np27
        for k in range(10):
            np_t *= (1 + g)
            oe = np_t * (1 - g / base["ronic_tv"]) if g > 0 else np_t
            v += oe / (1 + COE) ** (T_FIRST + k)
        oe_tv = np_t * (1 + 0.025) * (1 - 0.025 / base["ronic_tv"])
        v += oe_tv / (COE - 0.025) / (1 + COE) ** (T_FIRST + 9)
        return v
    g10 = solve(ten_year, -0.10, 0.30, target=ev_op)
    return dict(mcap=mcap, ev_op=ev_op, np27=np27, g_perp=g_perp, g10=g10)


def tier(pv: float) -> str:
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main() -> None:
    print("=== 东鹏饮料 605499 独立估值（价格日 2026-10-19，现价 %.2f 元）===" % PRICE)
    print(f"股本：全部 {SHARES_TOTAL:.4f} 亿股；扣拟注销回购（{TREASURY:.5f}×90%）后 {SHARES:.4f}；"
          f"剔除全部回购专户 {SHARES_EX_TREASURY:.4f}")
    print(f"金融资产 {FIN_ASSETS:.2f} − 有息负债 {DEBT:.2f}（短借 {ST_LOANS:.2f} + 租赁 {LEASE:.2f}）"
          f" = {NET_CASH_SIMPLE:.2f}；− 已宣派中期股利 {DIVIDEND_DECLARED:.2f} − 经营备付 {OP_RESERVE:.1f}"
          f" → 经调整净现金 {NET_CASH_ADJ:.2f}；非经营资产（私募基金 ×75%）{NON_OP:.2f}")
    print(f"正常化净利息（税后）{NET_INTEREST_AT:.2f}；税率 {TAX:.0%}")
    print()
    results = {}
    for name, s in SCENARIOS.items():
        ev = equity_value(s, COE)
        results[name] = ev
        pr = ev["pr"]
        print(f"[{name}] p={s['p']:.2f} 核心经营利润率 {s['core_margin']:.1%} → 经营归母净利率 {pr['np_margin']:.2%}")
        print(f"  2026 营收 {s['rev2026']:.1f}；2026 正常化归母净利（含净利息）{pr['np2026_norm']:.2f}"
              f"（经营 {pr['np2026_op']:.2f} + 利息 {NET_INTEREST_AT:.2f}）")
        print("  年份   营收    经营净利  扩产开支  营运资本流入  再投资  所有者收益  增速")
        print(f"  2026  {s['rev2026']:7.1f}  {pr['np2026_op']:7.2f}  {CAPEX_GROWTH_2026:7.2f}"
              f"  {WC_FLOAT * (s['rev2026'] - REV_2025):9.2f}  {CAPEX_GROWTH_2026 - WC_FLOAT * (s['rev2026'] - REV_2025):7.2f}"
              f"  {pr['oe2026']:8.2f}   （参照行，不计入现值）")
        prev_oe = pr["oe2026"]
        for row in pr["rows"]:
            g = "" if prev_oe is None else f"{row['oe'] / prev_oe - 1:+.1%}"
            print(f"  {row['year']}  {row['rev']:7.1f}  {row['np_op']:7.2f}  {row['growth_capex']:7.2f}"
                  f"  {row['wc_in']:9.2f}  {row['reinvest']:7.2f}  {row['oe']:8.2f}   {g}")
            prev_oe = row["oe"]
        sum_np = sum(r_["np_op"] for r_ in pr["rows"])
        sum_re = sum(r_["reinvest"] for r_ in pr["rows"])
        d_np = pr["rows"][-1]["np_op"] - pr["np2026_op"]
        print(f"  经营净利增速 2027-2031：" + " ".join(f"{pr['rows'][i]['np_op'] / (pr['rows'][i-1]['np_op'] if i else pr['np2026_op']) - 1:+.1%}" for i in range(5)))
        print(f"  终值：2032 经营净利 {pr['np_tv']:.2f}，所有者收益 {pr['oe_tv']:.2f}（再投资率 {s['tg'] / s['ronic_tv']:.2%}），"
              f"g={s['tg']:.1%}")
        print(f"  显性期再投资率 {sum_re / sum_np:.1%}，增量回报 {d_np / sum_re if sum_re > 0 else float('nan'):.0%}")
        print(f"  PV：2026H2 现金流 {ev['pv_stub']:.1f} + 2027-31 {ev['pv_rows']:.1f} + 终值 {ev['pv_tv']:.1f}"
              f"（终值 {ev['tv']:.1f}，占股权价值 {ev['tv_share']:.0%}）+ 净现金 {NET_CASH_ADJ:.1f} + 非经营 {NON_OP:.1f}"
              f" = {ev['equity']:.1f} 亿")
        print(f"  V = {ev['v']:.2f} 元/股（剔除全部回购专户 {ev['v_ex_treasury']:.2f}）")
        print()
    vw = sum(SCENARIOS[n]["p"] * results[n]["v"] for n in SCENARIOS)
    vw_ex = sum(SCENARIOS[n]["p"] * results[n]["v_ex_treasury"] for n in SCENARIOS)
    pv = PRICE / vw
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.3f}（{tier(pv)}）")
    print(f"剔除全部回购专户：加权 V = {vw_ex:.2f}，P/V = {PRICE / vw_ex:.3f}")
    eq_w = sum(SCENARIOS[n]["p"] * results[n]["equity"] for n in SCENARIOS)
    print(f"不扣任何回购股份（{SHARES_TOTAL:.4f} 亿股）：加权 V = {eq_w / SHARES_TOTAL:.2f}，P/V = {PRICE * SHARES_TOTAL / eq_w:.3f}")
    v_sym = 0.25 * results["bear"]["v"] + 0.50 * results["base"]["v"] + 0.25 * results["bull"]["v"]
    print(f"对照：概率取 25/50/25 时加权 V = {v_sym:.2f}，P/V = {PRICE / v_sym:.3f}")
    print(f"对照：计划外海外或并购投资 30 亿使每股价值减少 {30 / SHARES:.2f} 元")
    for r in (0.08, 0.10):
        vals = {n: equity_value(s, r)["v"] for n, s in SCENARIOS.items()}
        w = sum(SCENARIOS[n]["p"] * vals[n] for n in SCENARIOS)
        print(f"股权成本 {r:.0%}：熊 {vals['bear']:.2f} / 基准 {vals['base']:.2f} / 牛 {vals['bull']:.2f}；"
              f"加权 {w:.2f}，P/V {PRICE / w:.3f}")
    irr = implied_irr(SCENARIOS["base"])
    print(f"现价隐含回报（基准情景现金流）：{irr:.2%}")
    rd = reverse_dcf()
    print(f"反向 DCF：市值 {rd['mcap']:.1f}（{SHARES:.4f} 亿股）− 净现金与非经营资产与 2026H2 现金流 → 经营价值 {rd['ev_op']:.1f}；"
          f"以 2026 正常化经营净利 {rd['np27']:.2f} 为起点")
    print(f"  隐含永续增长 {rd['g_perp']:.2%}（再投资率 g/40%）；隐含 10 年所有者收益年增速 {rd['g10']:.2%}（其后 2.5%）")
    print()
    print("各档价格（V 不变）：明显低估 ≤ %.2f；温和低估 ≤ %.2f；大致合理 ≤ %.2f；偏贵 > %.2f"
          % (0.75 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    # 证伪情景
    print()
    print("=== 证伪触发后的 V（股权成本 9%）===")
    for label, prob in [("熊情景 100%", {"bear": 1.0, "base": 0.0, "bull": 0.0}),
                        ("熊 60% / 基准 40%", {"bear": 0.6, "base": 0.4, "bull": 0.0}),
                        ("熊 50% / 基准 50%", {"bear": 0.5, "base": 0.5, "bull": 0.0}),
                        ("基准 50% / 牛 50%", {"bear": 0.0, "base": 0.5, "bull": 0.5})]:
        v = sum(prob[n] * results[n]["v"] for n in SCENARIOS)
        print(f"  {label}: V = {v:.2f}，P/V = {PRICE / v:.3f}")
    # 交叉验证
    print()
    mcap = PRICE * SHARES
    print("=== 交叉验证 ===")
    np_base = results["base"]["pr"]["np2026_norm"]
    print(f"市值（{SHARES:.4f} 亿股）{mcap:.1f}；基准正常化归母净利 {np_base:.2f} → PE {mcap / np_base:.1f}x；"
          f"扣净现金与非经营后 {(mcap - NET_CASH_ADJ - NON_OP) / results['base']['pr']['np2026_op']:.1f}x")
    ev_mkt = mcap - NET_CASH_ADJ - NON_OP
    core_2026e = 59.0
    core_norm = SCENARIOS["base"]["rev2026"] * SCENARIOS["base"]["core_margin"]
    print(f"EV（市值−经调整净现金−非经营）{ev_mkt:.1f}；EV/2026E 核心经营利润 {core_2026e:.1f} = {ev_mkt / core_2026e:.1f}x；"
          f"EV/正常化 {core_norm:.1f} = {ev_mkt / core_norm:.1f}x")
    cash_2026 = 14.12 + 21.81 + 10.39
    print(f"2026 年度内现金回报：2025 年末期息 14.12 + 中期息 21.81 + A 股回购 10.39 = {cash_2026:.2f} → {cash_2026 / mcap:.1%}")
    print(f"分红规划（不低于归母净利 80%，回购计入）× 基准正常化净利：{0.8 * np_base:.1f} → {0.8 * np_base / mcap:.1%}")


if __name__ == "__main__":
    main()
