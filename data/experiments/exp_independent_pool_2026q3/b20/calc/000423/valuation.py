#!/usr/bin/env python3
"""东阿阿胶（000423）独立估值（OI-291 b20，价格日 2026-10-21）。

方法：核心经营所有者收益 DCF（不含利息与理财收益）+ 经调整净现金 + 非经营资产；
熊／基准／牛三情景概率加权；报 8%／10% 股权成本敏感性、现价隐含回报与反向 DCF。
全部输入写在脚本内，单位：亿元、元/股。运行：python3 valuation.py
"""

PRICE = 47.21
SHARES = 6.39826824          # 亿股，总股本 639,826,824（2026-07-02 注销 415 万股后），含回购专户 385,869 股
SHARES_EX_TREASURY = 6.39440955  # 剔除回购专户股份（2026-08-25 权益分派实施公告）
COE = 0.09
TAX = 0.155                  # 正常化所得税率（2025 实际 15.6%，母公司高新 15%）

# ---------------------------------------------------------------- 报表输入（元 → 亿元）
Y = 1e8
IS = {  # 合并利润表：2025 年报第 74 页、附注第 138-140 页；2026 中报第 41-42、107-109 页
    "2025":   dict(rev=6700474184.47, op=2071304132.45, int_inc=58867519.58, int_exp=6589218.84,
                   wmp=58663993.79, fv=-4109805.03, eq=-9882822.55, lt_disp=1270718.50,
                   asset_disp=12696821.46, credit=2224037.22, impair=-7557836.50, donation=5400095.14),
    "2025H1": dict(rev=3051583802.55, op=975499755.17, int_inc=31613316.78, int_exp=834612.70,
                   wmp=41982658.70, fv=-8962695.33, eq=-4855725.48, lt_disp=0.0,
                   asset_disp=836884.46, credit=4384476.50, impair=3334852.67, donation=1001406.72),
    "2026H1": dict(rev=3155143496.50, op=1016945898.59, int_inc=23372307.74, int_exp=2516077.11,
                   wmp=35728080.24, fv=-8390882.60, eq=-1588067.24, lt_disp=22918704.77,
                   asset_disp=5257163.40, credit=-15216300.79, impair=-35073.57, donation=1723223.40),
}


def core_ebit(d):
    """核心经营利润：营业利润剔除利息净收入、理财收益、公允价值变动、权益法损益、
    长期股权投资处置、资产处置、信用与资产减值（视为一次性），扣除对外捐赠（视为经常性）。"""
    return (d["op"] - (d["int_inc"] - d["int_exp"]) - d["wmp"] - d["fv"] - d["eq"] - d["lt_disp"]
            - d["asset_disp"] - d["credit"] - d["impair"] - d["donation"]) / Y


def net_fin(d):
    return (d["int_inc"] - d["int_exp"] + d["wmp"] + d["fv"]) / Y


CORE = {k: core_ebit(v) for k, v in IS.items()}
REV = {k: v["rev"] / Y for k, v in IS.items()}
REV["2025H2"] = REV["2025"] - REV["2025H1"]
CORE["2025H2"] = CORE["2025"] - CORE["2025H1"]

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，中报第 36-38、77、99-104、112、131 页）
CASH = 5011024977.94 / Y           # 货币资金（含一年内定期存款 18.09 亿、直销保证金 0.20 亿）
TFA = 2966712188.58 / Y            # 交易性金融资产（银行理财与结构性存款）
INTERIM_DIV = 859927251.46 / Y     # 2026 中期股利，8-31 支付（6-30 之后）
RESTRICTED = 20000000.00 / Y       # 直销企业保证金
SHORT_LOAN = 10004166.67 / Y       # 吉林子公司抵押借款
DB_PENSION = 62307742.98 / Y       # 设定受益计划净负债（含一年内到期）
INCENTIVE_FUND = 51000000.00 / Y   # 2018 年度中长期激励基金，未支付
ACQ_PAYABLE = 75769544.45 / Y      # 收购子公司应付代价（东阿阿胶(吉林)药业）
LEASE_LIAB = (47311268.17 + 24737400.15) / Y   # 租赁负债（含一年内到期），只列示不扣
RELATED_DEPOSIT = 193943739.28 / Y  # 广东华润银行存款，单独列示（已含在货币资金内）
RESERVE_MONTHS = 1.5               # 经营备付：1.5 个月现金经营成本
DA_2025 = (115498481.86 + 24356935.02 + 13549232.11 + 6767766.04) / Y
CASH_OPEX_2025 = REV["2025"] - CORE["2025"] - DA_2025
OP_RESERVE = CASH_OPEX_2025 * RESERVE_MONTHS / 12
NET_CASH_ADJ = (CASH + TFA - INTERIM_DIV - RESTRICTED - SHORT_LOAN - DB_PENSION
                - INCENTIVE_FUND - ACQ_PAYABLE - OP_RESERVE)
NON_OP = (71192270.56 + 35641917.01) / Y   # 长期股权投资 + 其他非流动金融资产

# 2026 年净财务收益（含净利息，用于报表口径正常化归母净利）：上半年实际 + 下半年估计
FIN_2026H2 = 0.41
FIN_2026 = net_fin(IS["2026H1"]) + FIN_2026H2

# 健康消费品产业园：总投资 14.85 亿（固定资产 14.21 + 铺底流动资金 0.64），6-30 前已付约 1.5 亿
PARK = {"2026H2": 1.50, 2027: 6.00, 2028: 5.85}

YEARS = [2027, 2028, 2029, 2030, 2031]
T = {"2026H2": 0.0, 2027: 0.69, 2028: 1.69, 2029: 2.69, 2030: 3.69, 2031: 4.69}  # 距 2026-10-21 的年数（年中流量）

SCEN = {
    "bear": dict(p=0.30, h2_growth=-0.03, h2_margin=0.275,
                 growth=[-0.12, 0.02, 0.02, 0.02, 0.02], margin=[0.245, 0.255, 0.255, 0.255, 0.255],
                 ma=[1.5, 1.5, 1.5, 1.5, 1.5], one_off={}, g=0.015, roic=0.10,
                 text="授信年末未清零、渠道去库存：2026H2 收入 -3%（核心利润率 27.5%），2027 收入 -12%"
                      "（利润率 24.5%），2028-2031 +2%/年、利润率 25.5%；产业园与每年 1.5 亿并购照常投入；"
                      "永续 1.5%、增量回报 10%"),
    "base": dict(p=0.50, h2_growth=0.025, h2_margin=0.289,
                 growth=[0.03, 0.04, 0.04, 0.04, 0.035], margin=[0.290, 0.2875, 0.285, 0.2825, 0.280],
                 ma=[1.5, 1.5, 1.5, 1.5, 1.5], one_off={}, g=0.025, roic=0.15,
                 text="授信年末基本清零，阿胶块与复方阿胶浆持平微增、健康消费品与男科贡献增量：2026H2 +2.5%"
                      "（利润率 28.9%），2027-2031 收入 +3%/+4%/+4%/+4%/+3.5%，研发加码与毛利率回落使核心利润率"
                      "由 29.0% 逐年降至 28.0%；永续 2.5%、增量回报 15%"),
    "bull": dict(p=0.20, h2_growth=0.05, h2_margin=0.295,
                 growth=[0.06, 0.07, 0.07, 0.06, 0.05], margin=[0.295] * 5,
                 ma=[1.5, 1.5, 1.5, 1.5, 1.5], one_off={}, g=0.025, roic=0.20,
                 text="第二、三曲线兑现、产业园投产放量：2026H2 +5%，2027-2031 收入 +6%/+7%/+7%/+6%/+5%，"
                      "核心利润率 29.5%；永续 2.5%、增量回报 20%"),
}


def project(s):
    """返回逐年（2026H2 与 2027-2031）收入、核心 EBIT、NOPAT、所有者收益与终值所需量。"""
    rev_h2 = REV["2025H2"] * (1 + s["h2_growth"])
    core_h2 = rev_h2 * s["h2_margin"]
    rev26 = REV["2026H1"] + rev_h2
    core26 = CORE["2026H1"] + core_h2
    rows = []
    # 2026H2：NOPAT − 产业园支出（维护性资本开支 = 不含使用权资产的折旧摊销，相抵）
    nopat_h2 = core_h2 * (1 - TAX)
    rows.append(dict(year="2026H2", rev=rev_h2, core=core_h2, nopat=nopat_h2,
                     oe=nopat_h2 - PARK["2026H2"]))
    rev, nopat_prev = rev26, core26 * (1 - TAX)
    for i, y in enumerate(YEARS):
        rev = rev * (1 + s["growth"][i])
        core = rev * s["margin"][i]
        nopat = core * (1 - TAX)
        oe = nopat - PARK.get(y, 0.0) - s["ma"][i] + s["one_off"].get(y, 0.0) * (1 - TAX)
        rows.append(dict(year=y, rev=rev, core=core, nopat=nopat, oe=oe,
                         g_nopat=nopat / nopat_prev - 1))
        nopat_prev = nopat
    return dict(rows=rows, rev26=rev26, core26=core26,
                np26=(core26 + FIN_2026) * (1 - TAX))


def value(s, r=COE, shares=SHARES, extra_cash=0.0):
    pj = project(s)
    pv = 0.0
    for row in pj["rows"]:
        pv += row["oe"] / (1 + r) ** T[row["year"]]
    last = pj["rows"][-1]
    oe_tv = last["nopat"] * (1 + s["g"]) * (1 - s["g"] / s["roic"])
    tv = oe_tv / (r - s["g"])
    pv_tv = tv / (1 + r) ** T[2031]
    eq = pv + pv_tv + NET_CASH_ADJ + NON_OP + extra_cash
    return dict(v=eq / shares, eq=eq, pv_ops=pv, pv_tv=pv_tv, tv_share=pv_tv / eq, pj=pj)


def weighted(r=COE, shares=SHARES, scen=SCEN):
    return sum(s["p"] * value(s, r, shares)["v"] for s in scen.values())


def implied_irr(s, price=PRICE):
    lo, hi = 0.03, 0.40
    for _ in range(200):
        mid = (lo + hi) / 2
        if mid <= s["g"] + 1e-4:
            lo = mid
            continue
        if value(s, mid)["v"] > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(price=PRICE):
    """(1) 现价隐含的 2027-2036 年 NOPAT 恒定增速（其后 2.5% 永续，增长再投资 = g/15%，
    产业园支出与净现金同基准情景）；(2) 自 2027 年起的永续增速。"""
    b = SCEN["base"]
    pj = project(b)
    nopat26 = pj["core26"] * (1 - TAX)
    oe_h2 = pj["rows"][0]["oe"]
    target = price * SHARES - NET_CASH_ADJ - NON_OP - oe_h2

    def pv_10y(g):
        pv, nopat = 0.0, nopat26
        for k in range(10):
            y = 2027 + k
            nopat *= (1 + g)
            reinv = max(g, 0.0) / b["roic"]
            oe = nopat * (1 - reinv) - PARK.get(y, 0.0)
            pv += oe / (1 + COE) ** (0.69 + k)
        tv = nopat * 1.025 * (1 - 0.025 / b["roic"]) / (COE - 0.025)
        return pv + tv / (1 + COE) ** (0.69 + 9)

    def pv_perp(g):
        oe0 = nopat26 * (1 + g) * (1 - max(g, 0.0) / b["roic"])
        pv_park = sum(PARK[y] / (1 + COE) ** T[y] for y in (2027, 2028))
        return oe0 / (COE - g) * (1 + COE) ** (1 - 0.69) - pv_park

    def solve(f, lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid) > target:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    return solve(pv_10y, -0.15, 0.25), solve(pv_perp, -0.10, 0.08)


def falsifier_values():
    """证伪条件触发后的独立 V（元/股）。"""
    out = {}
    # F1：授信未清零（2026 年末应收账款 > 3.0 亿或全年经营现金流 < 13 亿）→ 熊 60%／基准 40%
    out["F1_credit_not_cleared"] = 0.6 * value(SCEN["bear"])["v"] + 0.4 * value(SCEN["base"])["v"]
    # F2：2027H1 收入同比 < -5% → 熊情景
    out["F2_revenue_decline"] = value(SCEN["bear"])["v"]
    # F3：毛利率连续两季 < 70%（驴皮成本）→ 基准情景核心利润率 -3pct
    b = dict(SCEN["base"]); b["margin"] = [m - 0.03 for m in b["margin"]]; b["h2_margin"] -= 0.015
    out["F3_margin_squeeze"] = (SCEN["bear"]["p"] * value(SCEN["bear"])["v"] + SCEN["base"]["p"] * value(b)["v"]
                                 + SCEN["bull"]["p"] * value(SCEN["bull"])["v"])
    # F4：新增并购或产业园超支合计 > 20 亿且增量回报 < 5%：价值损失 = 20 ×(1 − 5%/9%)
    out["F4_capital_misallocation"] = weighted() - 20 * (1 - 0.05 / COE) / SHARES
    # F5：研发投入按 30% 复合增长而收入增速 < 5%（2027 年研发投入 > 5.7 亿）→ 基准利润率逐年 -1.5pct 至 -6pct
    b5 = dict(SCEN["base"]); b5["margin"] = [m - x for m, x in zip(SCEN["base"]["margin"], (0.015, 0.03, 0.045, 0.06, 0.06))]
    out["F5_rd_ramp"] = (SCEN["bear"]["p"] * value(SCEN["bear"])["v"] + SCEN["base"]["p"] * value(b5)["v"]
                          + SCEN["bull"]["p"] * value(SCEN["bull"])["v"])
    return out


def main():
    print("== 正常化核心经营利润（亿元）==")
    for k in ("2025", "2025H1", "2025H2", "2026H1"):
        print(f"  {k}: 收入 {REV[k]:.2f}  核心EBIT {CORE[k]:.2f}  利润率 {CORE[k] / REV[k]:.2%}")
    print(f"  2026H1 净财务收益 {net_fin(IS['2026H1']):.3f}；2025 净财务收益 {net_fin(IS['2025']):.3f}")
    print("\n== 经调整净现金（2026-06-30，亿元）==")
    print(f"  现金类 {CASH + TFA:.2f} − 中期股利 {INTERIM_DIV:.2f} − 受限 {RESTRICTED:.2f} − 借款 {SHORT_LOAN:.2f}"
          f" − 设定受益 {DB_PENSION:.2f} − 激励基金 {INCENTIVE_FUND:.2f} − 收购应付 {ACQ_PAYABLE:.2f}"
          f" − 经营备付 {OP_RESERVE:.2f} = {NET_CASH_ADJ:.2f}")
    print(f"  非经营资产 {NON_OP:.2f}；租赁负债（只列示）{LEASE_LIAB:.2f}；华润银行存款（单独列示）{RELATED_DEPOSIT:.2f}")
    print(f"  每股经调整净现金 {NET_CASH_ADJ / SHARES:.2f} 元")

    print("\n== 三情景（股权成本 9%）==")
    for name, s in SCEN.items():
        res = value(s)
        pj = res["pj"]
        print(f"  {name}: p={s['p']:.2f}  V={res['v']:.2f}  2026 正常化归母净利 {pj['np26']:.2f}"
              f"  2026 收入 {pj['rev26']:.2f} 核心EBIT {pj['core26']:.2f}  终值占比 {res['tv_share']:.0%}")
        for row in pj["rows"]:
            gtxt = f" NOPAT增速 {row['g_nopat']:+.1%}" if "g_nopat" in row else ""
            print(f"     {row['year']}: 收入 {row['rev']:.2f} 核心EBIT {row['core']:.2f} NOPAT {row['nopat']:.2f}"
                  f" 所有者收益 {row['oe']:.2f}{gtxt}")
        reinv = PARK["2026H2"] + sum(PARK.get(y, 0.0) for y in YEARS) + sum(s["ma"])
        nopat_sum = sum(r["nopat"] for r in pj["rows"][1:])
        d_nopat = pj["rows"][-1]["nopat"] - pj["core26"] * (1 - TAX)
        print(f"     2026H2-2031 再投资（产业园+并购）{reinv:.2f}，占 2027-2031 NOPAT {reinv / nopat_sum:.1%}；"
              f"NOPAT 增量 {d_nopat:+.2f}，增量回报 {d_nopat / reinv:.1%}；终值期再投资率 {s['g'] / s['roic']:.1%}")
    vw = weighted()
    print(f"\n  加权 V = {vw:.2f}  P/V = {PRICE / vw:.3f}")
    vw_ex = weighted(shares=SHARES_EX_TREASURY)
    print(f"  剔除回购专户股份：加权 V = {vw_ex:.2f}  P/V = {PRICE / vw_ex:.3f}")
    print("\n== 股权成本敏感性 ==")
    for r in (0.08, 0.10):
        vals = {n: value(s, r)["v"] for n, s in SCEN.items()}
        print(f"  r={r:.0%}: 熊 {vals['bear']:.2f} 基准 {vals['base']:.2f} 牛 {vals['bull']:.2f}"
              f"  加权 {weighted(r):.2f}")
    irr = implied_irr(SCEN["base"])
    print(f"\n== 现价隐含回报（基准情景）== {irr:.2%}"
          f"（熊 {implied_irr(SCEN['bear']):.2%}，牛 {implied_irr(SCEN['bull']):.2%}）")
    g10, gp = reverse_dcf()
    print(f"== 反向 DCF == 2027-2036 年 NOPAT 隐含年增速 {g10:+.2%}（其后 2.5%）；自 2027 年永续隐含增速 {gp:+.2%}")
    print("\n== 交叉验证 ==")
    b = value(SCEN["base"])["pj"]
    mcap = PRICE * SHARES
    ev = mcap - NET_CASH_ADJ - NON_OP
    print(f"  市值 {mcap:.2f}；EV {ev:.2f}；EV/2026 核心EBIT {ev / b['core26']:.1f}x；"
          f"（市值−净现金）/2026 核心NOPAT {ev / (b['core26'] * (1 - TAX)):.1f}x；PE(2026 正常化) {mcap / b['np26']:.1f}x")
    print(f"  过去 12 个月每股分红 2.7803 元，股息率 {2.7803 / PRICE:.2%}；2026H1 回购 1.20 亿，回购收益率 {1.2 / mcap:.2%}")
    print("\n== 证伪触发后的 V ==")
    for k, v in falsifier_values().items():
        print(f"  {k}: {v:.2f}")
    # 2026Q3 基准估计：按 2025 年 Q3 占下半年的比重（收入 17.157/36.499、归母 4.561/9.210）拆分
    pj_b = value(SCEN["base"])["pj"]
    h2_np = (pj_b["rows"][0]["core"] + FIN_2026H2) * (1 - TAX)
    print(f"\n== 2026Q3 基准估计 == 收入 {pj_b['rows'][0]['rev'] * 17.157 / 36.499:.2f} 亿（2025Q3 17.16）；"
          f"归母净利 {h2_np * 4.561 / 9.210:.2f} 亿（2025Q3 4.56）")
    print("\n== 进入各档的价格（V 不变）==")
    print(f"  明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")


if __name__ == "__main__":
    main()
