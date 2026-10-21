# -*- coding: utf-8 -*-
"""振华股份（603067）独立估值：所有者收益 DCF（有杠杆口径）+ 可转债逐情景取低 + 反向 DCF。

运行：python3 valuation.py
金额单位亿元，股本亿股，每股价值元/股。估值基准日 2026-06-30（最新定期报告资产负债表），
现金流从 2026H2 起折现（年中惯例），再按股权成本滚动到价格日 2026-10-20。
输入全部写在本脚本内，出处见同目录正文 companies/603067_振华股份.md。
"""

PRICE = 34.20                 # 2026-10-20 收盘，元/股
SHARES = 7.55525404           # 总股本，亿股（2026H1 报告第 39 页；无回购专户股份）
COE = 0.09                    # 股权成本基准
ROLL_YEARS = 112 / 365        # 2026-06-30 → 2026-10-20
TAX = 0.15                    # 高新技术企业 15%（2026H1 实际所得税率约 10%）

# ---------- 资产负债表（2026-06-30，2026H1_report 第 44-46、86-121 页） ----------
CASH = 3.0852                 # 货币资金
RESTRICTED = 0.3949           # 其他货币资金：票据保证金 0.172、预售监管 0.217、植被保证金 0.006
TRADING_FA = 0.0002
OP_RESERVE = 1.5              # 经营备付（约 3% 营收；公司口径最低现金保有量 3.54 亿，见问询回复第 50 页）
IBD = 5.6307 + 4.8515 + 1.0841 + 0.0074   # 短借 + 长借 + 一年内到期 + 租赁负债 = 11.57
DIV_PAYABLE = 1.2088          # 应付股利（2026-07-15 派发）
ACQ_PAYABLE = 0.5156          # 应付股权购买款（新疆沈宏重整投资尾款）
PERSONAL_LOANS = 0.2328       # 向其他单位和个人借款（广东首能）
PROVISIONS = 0.1453           # 预计负债：职工安置 + 环境修复
MINORITY = 0.1455             # 少数股东权益（账面）
DEBT_RATE = 0.030             # 有息负债实际平均利率（2025 年利息 0.43 亿含可转债计提；银行贷款约 2.8%-3.2%）

# 非经营资产（打折计入）
PE_FUNDS = 0.6414 * 0.9       # 其他非流动金融资产（私募基金份额）
LT_EQUITY = 0.0400
REAL_ESTATE = 2.4020 * 0.75 + 0.2167   # 住宅开发成本（已计提跌价）七五折 + 预售监管资金
NON_OP = PE_FUNDS + LT_EQUITY + REAL_ESTATE

# 可转债（振26转债，financing_20260813 第 23-27 页；不下修公告 2026-09-10）
CB_FACE = 8.78
CB_NET_PROCEEDS = 8.6854      # 2026-08-05 到账净额（invest_20260811 第 1 页）
CB_CONV_PRICE = 40.33
CB_SHARES = CB_FACE / CB_CONV_PRICE        # 0.2177 亿股
CB_COUPONS = [0.001, 0.003, 0.006, 0.010, 0.015]   # 第 1-5 年；第 6 年到期按 110% 赎回（含最后一期利息）


def net_cash_adj():
    """无杠杆口径经调整净现金（不含可转债及其募集资金）。"""
    return (CASH - RESTRICTED - OP_RESERVE + TRADING_FA
            - IBD - DIV_PAYABLE - ACQ_PAYABLE - PERSONAL_LOANS - PROVISIONS)


def cb_bond_floor(y=0.035):
    pv = sum(c / (1 + y) ** (i + 1) for i, c in enumerate(CB_COUPONS))
    pv += 1.10 / (1 + y) ** 6
    return CB_FACE * pv


YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
T_MID = [0.25, 1.0, 2.0, 3.0, 4.0, 5.0]     # 2026 为下半年；其余年中，距 2026-06-30
T_END = 5.5                                 # 2031 年末

# ---------- 情景 ----------
# npt：铬盐链吨所有者经营利润（NOPAT，元/吨，折重铬酸钠当量），长期概率加权价格与毛利率的正常化结果；
#      2024/2025/TTM 实际约 1,950/1,950/1,820 元/吨，2023 约 1,700 元/吨。
# vol：折重铬酸钠产销量（万吨）；2026 公司指引 33 万吨（results_call_20260831 第 2 页）。
# cr：金属铬（SOFC 等）超额税后利润（亿元）；syn：重庆新基地副产物、硫酸自给、铬绿/K3 结构带来的税后增量（亿元）。
# da：折旧摊销（亿元）；超出现有吨折旧强度（940 元/吨）的部分视为新基地增加的折旧，税后计入 NOPAT。
# m：长期维护性资本开支 / 折旧摊销。capex：重庆搬迁及配套项目资本开支（不含维护性）；comp：搬迁补偿款流入。
SCEN = {
    "bear": dict(p=0.30, npt=1500, rev_t=15000,
                 vol=[33.0, 33.5, 34.0, 35.0, 36.0, 36.5],
                 cr=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                 syn=[0.0, 0.0, -0.3, 0.2, 0.4, 0.5],
                 da=[3.1, 3.4, 4.5, 4.8, 4.9, 5.0], m=1.0,
                 capex=[2.0, 10.0, 10.0, 5.0, 2.2, 0.0],
                 comp=[0.0, 2.30, 2.27, 0.75, 0.0, 0.0],
                 wc_release=0.8, wc_ratio=0.27, g=0.015, ronic=0.10,
                 text="吨利润 1,500 元（较 TTM 低约 18%：扩产后以价换量、铬矿涨价或南非出口税、硫酸高位）；"
                      "量 2031 年 36.5 万吨（新厂爬坡慢）；搬迁项目超支 15%、补偿款晚到；金属铬无超额利润；"
                      "维护性资本开支=折旧；永续增长 1.5%、增量回报 10%"),
    "base": dict(p=0.50, npt=1850, rev_t=15700,
                 vol=[33.0, 34.5, 36.0, 37.5, 39.0, 39.5],
                 cr=[0.0, 0.2, 0.4, 0.5, 0.5, 0.5],
                 syn=[0.0, 0.0, 0.0, 0.6, 0.9, 1.0],
                 da=[3.1, 3.4, 4.4, 4.6, 4.7, 4.8], m=0.9,
                 capex=[2.5, 11.0, 8.5, 3.4, 0.0, 0.0],
                 comp=[0.0, 3.05, 2.27, 0.0, 0.0, 0.0],
                 wc_release=1.5, wc_ratio=0.25, g=0.020, ronic=0.12,
                 text="吨利润 1,850 元（TTM 水平，铬矿与产品价差按 2023-2026 中枢、硫酸回落）；"
                      "量 2031 年 39.5 万吨（重庆新厂 20 万吨核定产能 2027Q4 投产、新疆 4 万吨）；"
                      "SOFC 金属铬溢价税后 0.5 亿；搬迁项目按预算 25.4 亿、补偿款 5.32 亿按进度到账；"
                      "维护性资本开支=0.9×折旧；永续增长 2%、增量回报 12%"),
    "bull": dict(p=0.20, npt=2100, rev_t=16500,
                 vol=[33.0, 35.0, 37.0, 40.0, 41.5, 42.5],
                 cr=[0.3, 1.0, 2.5, 4.0, 5.0, 5.5],
                 syn=[0.0, 0.0, 0.3, 1.0, 1.4, 1.5],
                 da=[3.1, 3.4, 4.4, 4.6, 4.8, 5.0], m=0.8,
                 capex=[2.5, 11.0, 10.0, 3.4, 0.0, 0.0],
                 comp=[0.0, 3.05, 2.27, 0.0, 0.0, 0.0],
                 wc_release=2.0, wc_ratio=0.23, g=0.025, ronic=0.14,
                 text="吨利润 2,100 元（2025 年剔除减值的高点）；量 2031 年 42.5 万吨；"
                      "SOFC 放量，金属铬约 5 万吨、超额毛利约 1.3 万元/吨，税后超额利润 2031 年 5.5 亿；"
                      "另投 1.5 亿扩金属铬；维护性资本开支=0.8×折旧；永续增长 2.5%、增量回报 14%"),
}

INT_AT_2026 = 0.45   # 2026 年税后净利息：银行贷款约 0.36 + 可转债 8-12 月实际利率计提约 0.09


def build(s):
    """返回逐年 NOPAT、所有者收益（FCFF）与辅助列。"""
    rows = []
    prev_rev = None
    for i, y in enumerate(YEARS):
        vol = s["vol"][i]
        da = s["da"][i]
        extra_da_at = max(da - 0.094 * vol, 0.0) * (1 - TAX)
        nopat = vol * s["npt"] / 1e4 + s["cr"][i] + s["syn"][i] - extra_da_at
        rev = vol * s["rev_t"] / 1e4
        if i == 0:
            dwc = -s["wc_release"]
            frac = 0.5          # 2026 只计下半年
        else:
            dwc = s["wc_ratio"] * (rev - prev_rev)
            frac = 1.0
        prev_rev = rev
        maint_gap = (1 - s["m"]) * da
        fcff = frac * (nopat + maint_gap) - s["capex"][i] + s["comp"][i] - dwc
        rows.append(dict(year=y, vol=vol, rev=rev, nopat=nopat, da=da, extra_da_at=extra_da_at,
                         capex=s["capex"][i], comp=s["comp"][i], dwc=dwc, fcff=fcff))
    return rows


def terminal_oe(s, rows):
    last = rows[-1]
    nopat_next = (last["nopat"]) * (1 + s["g"])
    oe_next = nopat_next * (1 - s["g"] / s["ronic"]) + (1 - s["m"]) * last["da"] * (1 + s["g"])
    return oe_next


def equity_value(s, r=COE, levered=True, npt=None):
    s2 = dict(s)
    if npt is not None:
        s2["npt"] = npt
    rows = build(s2)
    pv_explicit = sum(row["fcff"] / (1 + r) ** t for row, t in zip(rows, T_MID))
    oe_next = terminal_oe(s2, rows)
    tv = oe_next / (r - s2["g"])
    pv_tv = tv / (1 + r) ** T_END
    op_value = pv_explicit + pv_tv
    nc = net_cash_adj()
    if levered:
        pv_int = (-nc) * DEBT_RATE * (1 - TAX) / r
        eq = op_value - pv_int + NON_OP - MINORITY
    else:
        eq = op_value + nc + NON_OP - MINORITY
    roll = (1 + r) ** ROLL_YEARS
    return dict(rows=rows, pv_explicit=pv_explicit, pv_tv=pv_tv, tv_share=pv_tv / op_value,
                op_value=op_value, eq_6m=eq, eq=eq * roll, oe_next=oe_next)


def per_share(eq):
    """可转债逐情景取低：债务（面值全额扣除、募集资金计入现金） vs 全部转股。"""
    v_debt = (eq + CB_NET_PROCEEDS - CB_FACE) / SHARES
    v_conv = (eq + CB_NET_PROCEEDS) / (SHARES + CB_SHARES)
    return min(v_debt, v_conv), v_debt, v_conv


def scenario_values(r=COE, levered=True):
    out = {}
    for k, s in SCEN.items():
        ev = equity_value(s, r=r, levered=levered)
        v, vd, vc = per_share(ev["eq"])
        out[k] = dict(v=v, v_debt=vd, v_conv=vc, **ev)
    return out


def weighted(vals):
    return sum(SCEN[k]["p"] * vals[k]["v"] for k in SCEN)


def norm_np_2026(s):
    rows = build(s)
    return rows[0]["nopat"] - INT_AT_2026


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s):
    def f(r):
        return per_share(equity_value(s, r=r)["eq"])[0]
    return solve(f, s["g"] + 0.002, 0.30, PRICE)


def implied_npt(s):
    def f(n):
        return per_share(equity_value(s, npt=n)["eq"])[0]
    return solve(f, 500, 20000, PRICE)


def implied_10y_growth():
    """以基准 2026 年稳态所有者收益为起点，现价隐含的 10 年增速（第 11 年起 2.5% 永续，增量回报 12%）。"""
    s = SCEN["base"]
    nopat0 = build(s)[0]["nopat"]
    oe0 = nopat0 * (1 - s["g"] / s["ronic"]) + (1 - s["m"]) * s["da"][0]
    nc = net_cash_adj()
    pv_int = (-nc) * DEBT_RATE * (1 - TAX) / COE
    target_eq_6m = (PRICE * SHARES - (CB_NET_PROCEEDS - CB_FACE)) / (1 + COE) ** ROLL_YEARS \
        + pv_int - NON_OP + MINORITY

    def f(g):
        pv, oe = 0.0, oe0
        for t in range(1, 11):
            oe *= (1 + g)
            pv += oe / (1 + COE) ** (t - 0.5)
        gt = 0.025
        nopat10 = oe / (1 - g / s["ronic"]) if g < s["ronic"] else oe
        oe11 = nopat10 * (1 + gt) * (1 - gt / s["ronic"])
        pv += oe11 / (COE - gt) / (1 + COE) ** 9.5
        return pv
    return solve(f, -0.05, 0.40, target_eq_6m), oe0


def implied_perp_growth():
    """基准 2031 年 NOPAT 不变、增量回报 12% 时现价隐含的永续增速。"""
    s = SCEN["base"]

    def f(g):
        s2 = dict(s, g=g)
        return per_share(equity_value(s2)["eq"])[0]
    hi = COE - 1e-4
    if f(hi) < PRICE:
        return None
    return solve(f, 0.0, hi, PRICE)


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    nc = net_cash_adj()
    print("=== 输入 ===")
    print(f"价格 {PRICE:.2f} 元；总股本 {SHARES:.4f} 亿股；市值 {PRICE * SHARES:.2f} 亿元")
    print(f"无杠杆经调整净现金 {nc:.2f} 亿元（有息负债 {IBD:.2f}，应付股利 {DIV_PAYABLE:.2f}，"
          f"重整尾款 {ACQ_PAYABLE:.2f}，个人借款 {PERSONAL_LOANS:.2f}，预计负债 {PROVISIONS:.2f}，"
          f"经营备付 {OP_RESERVE:.2f}，受限资金 {RESTRICTED:.2f}）")
    pv_int = (-nc) * DEBT_RATE * (1 - TAX) / COE
    print(f"有杠杆口径：净负债 {-nc:.2f} × {DEBT_RATE:.1%} × (1-{TAX:.0%}) / {COE:.0%} = 税后利息现值 {pv_int:.2f} 亿元")
    print(f"非经营资产 {NON_OP:.2f} 亿元；少数股东权益 {MINORITY:.2f}")
    print(f"可转债面值 {CB_FACE:.2f}、募集净额 {CB_NET_PROCEEDS:.2f}、转股数 {CB_SHARES:.4f} 亿股、"
          f"债底（3.5%）{cb_bond_floor():.2f}")

    vals = scenario_values()
    vals_unlev = scenario_values(levered=False)
    print("\n=== 情景（有杠杆口径，股权成本 9%） ===")
    for k, s in SCEN.items():
        v = vals[k]
        print(f"\n[{k}] p={s['p']:.2f}  {s['text']}")
        print("  年份  量(万吨) 营收  NOPAT  折旧  新增折旧税后  搬迁资本开支  补偿款  营运资本增加  所有者收益")
        for row in v["rows"]:
            print(f"  {row['year']}  {row['vol']:6.1f} {row['rev']:6.1f} {row['nopat']:6.2f} {row['da']:5.2f}"
                  f" {row['extra_da_at']:8.2f} {row['capex']:10.2f} {row['comp']:8.2f} {row['dwc']:9.2f}"
                  f" {row['fcff']:10.2f}")
        g_path = []
        nop = [r_["nopat"] for r_ in v["rows"]]
        for i in range(1, 6):
            g_path.append(nop[i] / nop[i - 1] - 1)
        print("  NOPAT 增速 2027-2031：" + ", ".join(f"{x:+.1%}" for x in g_path))
        print(f"  2032 所有者收益 {v['oe_next']:.2f}；显性期现值 {v['pv_explicit']:.2f}；终值现值 {v['pv_tv']:.2f}"
              f"（终值占经营价值 {v['tv_share']:.0%}）；经营价值 {v['op_value']:.2f}")
        print(f"  股权价值（10-20）{v['eq']:.2f} 亿；每股：按债务 {v['v_debt']:.2f}、按转股 {v['v_conv']:.2f}"
              f" → 取低 {v['v']:.2f} 元；无杠杆口径取低 {vals_unlev[k]['v']:.2f} 元")
        print(f"  2026 正常化归母净利 {norm_np_2026(s):.2f} 亿元")

    vw = weighted(vals)
    vw_unlev = weighted(vals_unlev)
    pv = PRICE / vw
    print("\n=== 结论 ===")
    print("三情景 V：" + "，".join(f"{k} {vals[k]['v']:.2f}" for k in SCEN))
    print(f"加权 V（有杠杆口径）{vw:.2f} 元；P/V {pv:.2f} → {band(pv)}")
    print(f"对照：无杠杆口径加权 V {vw_unlev:.2f} 元，P/V {PRICE / vw_unlev:.2f}")
    for r in (0.08, 0.10):
        vr = weighted(scenario_values(r=r))
        print(f"股权成本 {r:.0%}：加权 V {vr:.2f} 元，P/V {PRICE / vr:.2f}")
    irr = implied_irr(SCEN["base"])
    print(f"现价隐含回报（基准情景现金流）：{irr:.2%}")
    print(f"反向：基准其他假设不变，现价隐含吨利润 {implied_npt(SCEN['base']):,.0f} 元/吨（基准 1,850）")
    g10, oe0 = implied_10y_growth()
    print(f"反向：以 2026 稳态所有者收益 {oe0:.2f} 亿起，现价隐含 10 年增速 {g10:.1%}（其后 2.5% 永续）")
    gp = implied_perp_growth()
    print("反向：基准路径下现价隐含永续增速 " + (f"{gp:.2%}" if gp is not None else "高于股权成本，无解"))
    print(f"V 不变时各档价格：P/V=0.75 {0.75 * vw:.2f}，0.90 {0.90 * vw:.2f}，1.10 {1.10 * vw:.2f}")

    print("\n=== 增长路径与再投资（基准） ===")
    rows = vals["base"]["rows"]
    nop = [r_["nopat"] for r_ in rows]
    reinv = [(0.5 if i == 0 else 1.0) * (rows[i]["nopat"]) - rows[i]["fcff"] for i in range(6)]
    nop_sum = 0.5 * nop[0] + sum(nop[1:])
    print("NOPAT：" + "，".join(f"{r_['year']} {r_['nopat']:.2f}" for r_ in rows))
    print(f"2026H2-2031 累计净再投资 {sum(reinv):.2f} 亿，累计 NOPAT {nop_sum:.2f} 亿，再投资率 {sum(reinv) / nop_sum:.0%}")
    print(f"增量回报（2031 vs 2026 NOPAT 增量 / 累计净再投资）{(nop[-1] - nop[0]) / sum(reinv):.1%}")
    s = SCEN["base"]
    print(f"终值期再投资率 {s['g'] / s['ronic']:.1%}（g {s['g']:.1%} / 增量回报 {s['ronic']:.0%}）")

    print("\n=== 证伪情形下的加权 V ===")
    def wv(probs=None, base_over=None):
        vv = {}
        for k, sc in SCEN.items():
            sc2 = dict(sc)
            if k == "base" and base_over:
                sc2.update(base_over)
            vv[k] = per_share(equity_value(sc2)["eq"])[0]
        pr = probs or {k: SCEN[k]["p"] for k in SCEN}
        return sum(pr[k] * vv[k] for k in SCEN)
    f1 = wv(probs={"bear": 0.50, "base": 0.45, "bull": 0.05})
    f2 = wv(base_over=dict(npt=1600))
    f3 = wv(probs={"bear": 0.10, "base": 0.40, "bull": 0.50})
    f4 = wv(base_over=dict(capex=SCEN["bear"]["capex"], comp=SCEN["bear"]["comp"]))
    print(f"F1 2026 扣非归母<5.0 亿 → 概率 0.50/0.45/0.05：V {f1:.2f}")
    print(f"F2 铬的氧化物均价<19,500 且铬矿>2,900（基准吨利润降至 1,600）：V {f2:.2f}")
    print(f"F3 金属铬放量（概率 0.10/0.40/0.50）：V {f3:.2f}")
    print(f"F4 重庆新基地延期或超支（基准改用熊市资本开支与补偿款节奏）：V {f4:.2f}")


if __name__ == "__main__":
    main()
