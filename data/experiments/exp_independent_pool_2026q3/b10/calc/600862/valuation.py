#!/usr/bin/env python3
"""600862 中航高科 独立估值（OI-291 b10，价格日 2026-10-20）。

python3 valuation.py 打印三情景 V、加权 V、P/V、8%/10% 股权成本下的 V、
现价隐含回报与反向 DCF，数字与正文、600862.json 一致。
金额单位：亿元；每股价值：元/股。输入均写在脚本内，出处见注释。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 18.22                    # 2026-10-20 收盘（brief.md）
SHARES_TOTAL = 13.93049107       # 亿股，含回购专户（buyback_20260429_675699 第 2 页）
TREASURY = 0.03895               # 回购专户 389.5 万股，用途为股权激励，未拟注销
SHARES_EX_TREASURY = SHARES_TOTAL - TREASURY
VAL_DATE = date(2026, 10, 20)
COE = 0.09

# ---------------------------------------------------------------- 2026-06-30 资产负债表（2026H1_report 第 41-43、85 页）
CASH = 28.6426                   # 货币资金
FC_DEPOSIT = 27.6704             # 其中存放中航工业集团财务公司（关联方）
DEBT = 0.0213 + 0.3925 + 0.6998  # 短期借款 + 一年内到期非流动负债 + 租赁负债
DEBT_LIKE = 0.0810 + 0.1120      # 应付股利 + 长期应付职工薪酬（辞退福利）
# 经营性营运资本 = 应收账款+应收票据+应收款项融资+存货+预付 − 应付账款−应付票据−合同负债−预收−其他流动负债
NWC_0630 = (35.0509 + 2.5687 + 0.4593 + 15.6580 + 0.6727) - (22.9206 + 0.0075 + 0.3680 + 0.4430 + 0.0956)
REV_2026E = 43.0                 # 中报 23.64 + 下半年约 19.4（全年目标 42.65，2025_annual_report 第 34 页）
NWC_RATIO_YE2026 = 0.80          # 年末营运资本/营收：2023 0.60，2024 0.73，2025 0.77，账龄继续拉长取 0.80
OP_RESERVE = 2.6                 # 经营备付：约 1 个月付现成本
RP_HAIRCUT = 0.20                # 关联方（财务公司）存款折价

# 长期股权投资（2026H1_report 第 104-105 页）：账面值 × 计价系数
LTEI = {
    "长盛（廊坊）科技 18.19%（碳纤维，亏损）": (3.1358, 0.60),
    "北京航为高科 11.15%": (0.5923, 1.00),
    "南通红土创新资本": (0.1334, 1.00),
    "北京优材京航生物 41.33%（借款逾期）": (0.2375, 0.50),
    "北京三元飞机刹车": (0.1391, 1.00),
}

# 2026 年下半年存根（经营口径：剔除净利息、加回联营亏损）
NP_2026E = 7.60                  # 全年归母（中报 4.39 + 下半年约 3.21）
AT_INTEREST = 0.145              # 税后净利息收入（中报利息收入 0.097 亿年化，税率 15%）
ASSOC_LOSS = 0.25                # 联营企业亏损（中报 -0.133 亿年化），另按非经营资产计价
OPNP_H2 = (NP_2026E - 4.3902) - AT_INTEREST / 2 + ASSOC_LOSS / 2
DA_H2 = 1.15                     # 2025 年折旧摊销 2.28 亿的一半
CAPEX_H2 = 2.50                  # 维持 1.15 + 民机构件等项目 1.35
STUB_OE = OPNP_H2 + DA_H2 - CAPEX_H2
T_STUB = 0.2                     # 约在 2026 年末

FIXED_INTENSITY = 0.30           # 固定资本/营收（固定资产+在建+无形 ≈ 13.6+4.4 对营收 46）

SCENARIOS = {
    "bear": dict(
        p=0.25,
        growth=[0.015, 0.025, 0.025, 0.020, 0.020],
        margin=[0.163] * 5,
        nwc_ratio=[0.812, 0.824, 0.836, 0.848, 0.860],
        gcapex=[3.0, 2.5, 1.0, 0.5, 0.5],
        g_term=0.020, haircut=0.30,
        norm_rev=44.0, norm_margin=0.165,
        assumptions="收入 2027-2031 年增 1.5%-2.5%（双流水分走份额、军品降价抵消量增），经营净利率 16.3%，"
                    "营运资本/营收升至 0.86，永续增长 2.0%，财务公司存款折价 30%",
    ),
    "base": dict(
        p=0.50,
        growth=[0.055, 0.060, 0.050, 0.040, 0.035],
        margin=[0.176, 0.178, 0.180, 0.180, 0.180],
        nwc_ratio=[0.80] * 5,
        gcapex=[3.0, 2.5, 1.0, 0.6, 0.6],
        g_term=0.025, haircut=RP_HAIRCUT,
        norm_rev=46.5, norm_margin=0.176,
        assumptions="主机厂交付 2027 年起修复，收入 2027-2031 年增 5.5%/6.0%/5.0%/4.0%/3.5%，经营净利率 17.6%→18.0%"
                    "（低于 2023-2025 年 21.6% 的中枢，含降价与民机低毛利），营运资本/营收 0.80，民机构件等扩产 7.7 亿，永续增长 2.5%",
    ),
    "bull": dict(
        p=0.25,
        growth=[0.105, 0.105, 0.095, 0.080, 0.065],
        margin=[0.185, 0.190, 0.195, 0.195, 0.195],
        nwc_ratio=[0.78, 0.76, 0.74, 0.72, 0.70],
        gcapex=[3.5, 3.0, 2.0, 1.5, 1.2],
        g_term=0.025, haircut=RP_HAIRCUT,
        norm_rev=48.5, norm_margin=0.186,
        assumptions="十五五新机型与无人机放量、C919/商发风扇叶片与 eVTOL 贡献，收入 2027-2031 年增 10.5%→6.5%，"
                    "经营净利率 18.5%→19.5%，回款改善使营运资本/营收降至 0.70，永续增长 2.5%",
    ),
}


def t_mid(year):
    return (date(year, 7, 1) - VAL_DATE).days / 365.25


def adjusted_net_cash():
    nwc_ye = NWC_RATIO_YE2026 * REV_2026E
    seasonal = max(0.0, nwc_ye - NWC_0630)
    nca = CASH - DEBT - DEBT_LIKE - OP_RESERVE - seasonal
    return nca, seasonal, nwc_ye


def valued_cash(haircut):
    nca, _, _ = adjusted_net_cash()
    fc_share = FC_DEPOSIT / CASH
    return nca * (1 - haircut * fc_share)


def non_operating():
    return sum(b * k for b, k in LTEI.values())


def path(s):
    """逐年收入、经营归母净利、营运资本变化、扩产资本开支与所有者收益（2027-2031）。"""
    rev_prev = REV_2026E
    nwc_prev = NWC_RATIO_YE2026 * REV_2026E
    rows = []
    for i, y in enumerate(range(2027, 2032)):
        rev = rev_prev * (1 + s["growth"][i])
        opnp = rev * s["margin"][i]
        nwc = s["nwc_ratio"][i] * rev
        d_nwc = nwc - nwc_prev
        oe = opnp - d_nwc - s["gcapex"][i]   # 维持性资本开支 ≈ 折旧摊销
        rows.append(dict(year=y, rev=rev, opnp=opnp, d_nwc=d_nwc, gcapex=s["gcapex"][i], oe=oe))
        rev_prev, nwc_prev = rev, nwc
    return rows


def ronic(s):
    return s["margin"][-1] / (s["nwc_ratio"][-1] + FIXED_INTENSITY)


def terminal_oe(s, rows):
    np_next = rows[-1]["opnp"] * (1 + s["g_term"])
    rr = s["g_term"] / ronic(s)
    return np_next * (1 - rr), rr


def value(s, r=COE, shares=SHARES_TOTAL, detail=False):
    rows = path(s)
    pv_stub = STUB_OE / (1 + r) ** T_STUB
    pv_exp = sum(x["oe"] / (1 + r) ** t_mid(x["year"]) for x in rows)
    oe_t, rr = terminal_oe(s, rows)
    tv = oe_t / (r - s["g_term"])
    pv_tv = tv / (1 + r) ** t_mid(2031)
    cash = valued_cash(s["haircut"])
    nonop = non_operating()
    equity = pv_stub + pv_exp + pv_tv + cash + nonop
    v = equity / shares
    if detail:
        return dict(v=v, equity=equity, pv_stub=pv_stub, pv_exp=pv_exp, pv_tv=pv_tv, tv=tv,
                    cash=cash, nonop=nonop, rows=rows, rr=rr, oe_t=oe_t)
    return v


def weighted(r=COE, shares=SHARES_TOTAL):
    return sum(s["p"] * value(s, r, shares) for s in SCENARIOS.values())


def solve(f, lo, hi, target, n=200):
    """二分求解 f(x)=target（f 单调）。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    s = SCENARIOS["base"]
    mcap = PRICE * SHARES_TOTAL
    return solve(lambda r: value(s, r) * SHARES_TOTAL, 0.035, 0.20, mcap)


def reverse_dcf():
    """现价隐含：(a) 10 年所有者收益增速（之后 2.5%）；(b) 永续增速（再投资 = g/RONIC）。"""
    s = SCENARIOS["base"]
    mcap = PRICE * SHARES_TOTAL
    op_target = mcap - valued_cash(s["haircut"]) - non_operating() - STUB_OE / (1 + COE) ** T_STUB
    norm_opnp = s["norm_rev"] * s["norm_margin"]
    rn = ronic(s)
    oe0 = norm_opnp * (1 - 0.025 / rn)

    def pv10(g):
        pv, oe = 0.0, oe0
        for k, y in enumerate(range(2027, 2037)):
            oe = oe * (1 + g)
            pv += oe / (1 + COE) ** t_mid(y)
        tv = oe * 1.025 / (COE - 0.025)
        return pv + tv / (1 + COE) ** t_mid(2036)

    g10 = solve(pv10, -0.05, 0.40, op_target)
    np1 = path(s)[0]["opnp"]
    # 首笔现金流在 2027 年中（t_mid），戈登公式给出前一年同一时点的价值，再折到估值日
    gp = solve(lambda g: np1 * (1 - g / rn) / (COE - g) * (1 + COE) ** (1 - t_mid(2027)), 0.0, 0.085, op_target)
    return g10, gp, oe0, op_target


def normalized_np_2026():
    """2026 年正常化归母净利（含税后净利息，含联营亏损常态 -0.20，剔除一次性）。"""
    out = {}
    for k, s in SCENARIOS.items():
        out[k] = s["norm_rev"] * s["norm_margin"] + AT_INTEREST - 0.20
    return out


def variant(base_key="base", **changes):
    s = dict(SCENARIOS[base_key])
    s.update(changes)
    return value(s)


def main():
    nca, seasonal, nwc_ye = adjusted_net_cash()
    print("== 资产负债表调整（2026-06-30）")
    print(f"货币资金 {CASH:.2f}，其中财务公司存款 {FC_DEPOSIT:.2f}（{FC_DEPOSIT / CASH:.1%}）")
    print(f"有息负债含租赁 {DEBT:.2f}，类债务 {DEBT_LIKE:.2f}，经营备付 {OP_RESERVE:.2f}")
    print(f"营运资本 6-30 {NWC_0630:.2f} → 2026 年末预计 {nwc_ye:.2f}，季节性回吐 {seasonal:.2f}")
    print(f"经调整净现金（无杠杆口径）{nca:.2f}；财务公司存款折价 {RP_HAIRCUT:.0%} 后计入 {valued_cash(RP_HAIRCUT):.2f}")
    print(f"非经营资产（长期股权投资计价）{non_operating():.2f}；下半年存根所有者收益 {STUB_OE:.2f}")
    print()
    for k, s in SCENARIOS.items():
        d = value(s, detail=True)
        print(f"== {k}（概率 {s['p']:.2f}）V = {d['v']:.2f} 元/股；8% {value(s, 0.08):.2f}；10% {value(s, 0.10):.2f}")
        for x in d["rows"]:
            print(f"   {x['year']} 收入 {x['rev']:.1f} 经营归母 {x['opnp']:.2f} ΔNWC {x['d_nwc']:.2f} 扩产 {x['gcapex']:.1f} 所有者收益 {x['oe']:.2f}")
        oe_prev = [x['oe'] for x in d['rows']]
        print(f"   终值年所有者收益 {d['oe_t']:.2f}（再投资率 {d['rr']:.1%}，RONIC {ronic(s):.1%}，g {s['g_term']:.1%}）")
        tot_op = d['pv_stub'] + d['pv_exp'] + d['pv_tv']
        print(f"   PV：存根 {d['pv_stub']:.2f} + 显性期 {d['pv_exp']:.2f} + 终值 {d['pv_tv']:.2f}（终值占经营价值 {d['pv_tv'] / tot_op:.0%}）"
              f" + 现金 {d['cash']:.2f} + 非经营 {d['nonop']:.2f} = {d['equity']:.1f} 亿")
        print(f"   剔除回购专户股本 V = {value(s, shares=SHARES_EX_TREASURY):.2f}")
    vw = weighted()
    print()
    print(f"加权 V = {vw:.2f}；P/V = {PRICE / vw:.2f}")
    print(f"剔除回购专户股本：加权 V = {weighted(shares=SHARES_EX_TREASURY):.2f}；P/V = {PRICE / weighted(shares=SHARES_EX_TREASURY):.2f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}；10%：加权 V = {weighted(0.10):.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准情景）= {irr:.2%}")
    g10, gp, oe0, op_target = reverse_dcf()
    print(f"反向 DCF：现价对应经营价值 {op_target:.1f} 亿；以正常化所有者收益 {oe0:.2f} 起算，隐含 10 年增速 {g10:.1%}（之后 2.5%）；"
          f"隐含永续增速 {gp:.1%}（再投资 = g/RONIC）")
    b = SCENARIOS["base"]
    rows = path(b)
    op26 = NP_2026E - AT_INTEREST + ASSOC_LOSS
    prev = op26
    gr = []
    for x in rows:
        gr.append(x["opnp"] / prev - 1)
        prev = x["opnp"]
    reinv = sum(x["d_nwc"] + x["gcapex"] for x in rows)
    rr_exp = reinv / sum(x["opnp"] for x in rows)
    incr = (rows[-1]["opnp"] - op26) / reinv
    print("基准增长路径（经营归母净利，2026E 经营口径 {:.2f}）：".format(op26)
          + "，".join(f"{x['year']} {g:+.1%}" for x, g in zip(rows, gr))
          + f"；所有者收益 " + "，".join(f"{x['oe']:.2f}" for x in rows))
    print(f"显性期再投资率 {rr_exp:.1%}，增量回报 {incr:.1%}；终值再投资率 {terminal_oe(b, rows)[1]:.1%}，RONIC {ronic(b):.1%}")
    nn = normalized_np_2026()
    print("2026 正常化归母净利：" + "，".join(f"{k} {v:.2f}" for k, v in nn.items()))
    print("各档价格（V 不变）：明显低估 ≤ {:.2f}；温和低估 {:.2f}～{:.2f}；大致合理 {:.2f}～{:.2f}；偏贵 > {:.2f}".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    print("== 证伪条件触发后的 V")
    v_f1 = value(SCENARIOS["bear"])
    v_f2 = value(SCENARIOS["bull"])
    v_f3 = variant(nwc_ratio=[0.84, 0.86, 0.88, 0.88, 0.88])
    v_f4 = variant(margin=[0.160, 0.162, 0.165, 0.165, 0.165])
    v_f5 = variant(margin=[m - 0.02 for m in SCENARIOS["base"]["margin"]], haircut=0.35)
    print(f"F1 2026 年归母 < 7.0 亿（熊市情景）V = {v_f1:.2f}")
    print(f"F2 2027 年收入增 ≥ 10% 且归母 ≥ 9.5 亿（牛市情景）V = {v_f2:.2f}")
    print(f"F3 年末应收合计 ≥ 42 亿、营运资本/营收升至 0.88（基准其余不变）V = {v_f3:.2f}")
    print(f"F4 航空新材料毛利率 < 33%、经营净利率 16.0%-16.5%（基准其余不变）V = {v_f4:.2f}")
    print(f"F5 关联方技术许可费 > 1.0 亿或财务公司存款超限未纠正（净利率 -2 个百分点、存款折价 35%）V = {v_f5:.2f}")


if __name__ == "__main__":
    main()
