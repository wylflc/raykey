# -*- coding: utf-8 -*-
"""三一重工（600031）独立估值：OI-291 池内独立审计 b09，深度版。

运行：python3 valuation.py
单位：金额亿元，每股价值元/股。所有输入写在本脚本内，出处见正文
（2026H1_report = 2026 年半年度报告，2025_annual_report = 2025 年年度报告，页码为 PDF 物理页）。

方法：分部（国内／国际）正常化经营利润 -> 经营所有者收益（不含理财与存款利息，也不含
全部有息负债的利息）三阶段 DCF（9% 股权成本、年中折现）+ 经调整净现金 + 非经营资产。
经调整净现金为正，按框架全额扣除有息负债，不用有杠杆口径。无可转债。
"""

# ---------------------------------------------------------------- 快照
PRICE = 18.20                 # A 股 2026-10-20 收盘（腾讯日线）
H_PRICE_HKD = 16.67           # H 股 2026-10-20 收盘（腾讯港股行情 r_hk06031）
HKD_CNY = 0.862               # 假设：USD/CNY 约 6.72、USD/HKD 约 7.80（6-30 报表汇率 0.8686）
SHARES_A = 84.74390037        # A 股（含回购专户），2025_annual_report 第 68-69 页
SHARES_H = 7.20614400         # H 股 631,598,800 + 超额配售 89,015,600
SHARES = SHARES_A + SHARES_H  # 91.95004437 亿股，与 brief 总股本一致
# 回购专户（用于员工持股，不注销）：6-30 为 42,987,413 股（2026H1 第 37 页），
# 8-24 过户 22,736,500 股给 2026 年员工持股计划（第 24 页），9-11～9-16 回购 18,368,500 股
TREASURY = (42987413 - 22736500 + 18368500) / 1e8

# ---------------------------------------------------------------- 经调整净现金（2026-06-30）
CASH = 278.65                 # 货币资金（含三湘银行存款 32.71、受限 7.14）
PLACEMENT = 1.78              # 拆出资金（三一汽金同业）
TRADING_FA = 217.15           # 交易性金融资产（债务工具 216.70 + 权益 0.46）
ST_DEBT_INV = 91.10           # 其他流动资产中的短期债权投资（2026H1 第 93 页）
RESTRICTED = 7.14             # 其他货币资金：按揭与承兑保证金（第 109 页）
TTM_REVENUE = 980.03          # 营业收入 TTM = 892.31 + 533.06 - 445.34
OP_RESERVE_RATIO = 0.025      # 经营备付按 TTM 营业收入的 2.5%
DECLARED_DIV = 15.30          # 6-30 应付股利，7-17 已派发（第 112-113 页）
BUYBACK_AFTER = 3.33          # 9 月回购付现（回购进展公告 2026-047）
DEBT = {                      # 有息负债与类债务（第 41、109-114 页）
    "短期借款": 67.31,
    "拆入资金（三一汽金）": 45.95,
    "一年内到期长期借款": 15.00,
    "长期借款": 51.81,
    "租赁负债（含一年内到期）": 10.54,
    "质押式回购借入资金": 15.24,
    "应付资产专项计划及保理转付款": 11.14,
}
RELATED_DEPOSIT = 32.71       # 三湘银行（关联方）存款，第 31 页；含在货币资金内，单独列示

NON_OP = {                    # 非经营资产（账面），收益不计入经营所有者收益
    "华胥产业投资基金（权益法）": 10.84,
    "三湘银行股权（权益法）": 5.97,
    "无锡三一创业投资合伙（权益法）": 1.90,
    "其他权益工具投资": 6.94,
    "其他非流动金融资产": 3.72,
    "投资性房地产": 2.44,
}
MINORITY_SHARE = 11.11 / (920.84 + 11.11)   # 少数股东占合并权益比例，用于分摊净现金与非经营资产


def net_cash_adj():
    gross = CASH + PLACEMENT + TRADING_FA + ST_DEBT_INV
    reserve = OP_RESERVE_RATIO * TTM_REVENUE
    debt = sum(DEBT.values())
    nc = gross - RESTRICTED - reserve - DECLARED_DIV - BUYBACK_AFTER - debt
    return nc, gross, reserve, debt


# ---------------------------------------------------------------- 情景
# 正常化经营利润（2026 年规模、周期中位口径），不含：汇兑与套保损益、理财与存款利息、
# 有息负债利息、华胥基金权益法收益、非经常性政府补助与资产处置。
# 客户融资利息（融资租赁、分期、按揭贷款）属经营，计入 cust_fin。
SCEN = {
    "bear": dict(
        p=0.25,
        dom_rev=320.0, dom_gm=0.190,     # 国内：更新需求落空、价格战延续
        intl_rev=560.0, intl_gm=0.285,   # 国际：较 2026E 658 回落 15%，人民币升值与贸易壁垒压毛利
        oth_rev=18.0, oth_gm=0.20,
        opex=0.160, surcharge=0.0055, cust_fin=8.0,
        other_inc=5.0, impair=0.020, eq_inc=0.0, disposal=-1.0,
        tax=0.17, minority=0.01, fin_after_tax=7.0,
        growth=[0.03, 0.03, 0.03, 0.025, 0.025], g_term=0.020,
        roic_inc=0.18, roic_term=0.15,
        one_off=15.0,          # 下行期一次性信用损失（税后）：应收、融资租赁与担保
        rp_haircut=0.30,       # 关联银行存款折价
        nonop_factor=0.70,
    ),
    "base": dict(
        p=0.50,
        dom_rev=370.0, dom_gm=0.220,     # 国内：2026E 约 346，更新周期与 5 月提价带来小幅修复
        intl_rev=640.0, intl_gm=0.305,   # 国际：2026E 约 658、毛利率 32.5%，中位口径下修
        oth_rev=21.0, oth_gm=0.20,
        opex=0.149, surcharge=0.0055, cust_fin=9.0,
        other_inc=6.0, impair=0.014, eq_inc=0.3, disposal=-0.5,
        tax=0.155, minority=0.01, fin_after_tax=9.0,
        growth=[0.06, 0.06, 0.05, 0.04, 0.035], g_term=0.025,
        roic_inc=0.30, roic_term=0.20,
        one_off=0.0, rp_haircut=0.0, nonop_factor=0.90,
    ),
    "bull": dict(
        p=0.25,
        dom_rev=420.0, dom_gm=0.240,     # 国内：更新周期兑现、价格企稳
        intl_rev=680.0, intl_gm=0.315,   # 国际：份额继续提升，毛利率维持高位
        oth_rev=24.0, oth_gm=0.20,
        opex=0.142, surcharge=0.0055, cust_fin=10.0,
        other_inc=7.0, impair=0.011, eq_inc=0.5, disposal=-0.5,
        tax=0.15, minority=0.01, fin_after_tax=11.0,
        growth=[0.08, 0.08, 0.07, 0.06, 0.05], g_term=0.025,
        roic_inc=0.35, roic_term=0.25,
        one_off=0.0, rp_haircut=0.0, nonop_factor=1.00,
    ),
}

YEARS = [2027, 2028, 2029, 2030, 2031]
T0 = 0.696   # 2027 年中点距 2026-10-20 的年数（年中折现）


def normalized(s):
    rev = s["dom_rev"] + s["intl_rev"] + s["oth_rev"]
    gp = s["dom_rev"] * s["dom_gm"] + s["intl_rev"] * s["intl_gm"] + s["oth_rev"] * s["oth_gm"]
    core_ebit = gp - s["opex"] * rev - s["surcharge"] * rev + s["cust_fin"]
    pretax = core_ebit + s["other_inc"] - s["impair"] * rev + s["eq_inc"] + s["disposal"]
    nopat = pretax * (1 - s["tax"]) * (1 - s["minority"])     # 经营口径归母
    np_total = nopat + s["fin_after_tax"]                      # 含净利息的正常化归母净利
    return dict(rev=rev, gp=gp, gm=gp / rev, core_ebit=core_ebit, pretax=pretax,
                nopat=nopat, np_total=np_total)


def dcf(s, r, nopat0=None, growth=None, g_term=None, detail=False):
    n = normalized(s)
    nopat0 = n["nopat"] if nopat0 is None else nopat0
    growth = s["growth"] if growth is None else growth
    g_term = s["g_term"] if g_term is None else g_term
    gs = list(growth)
    # 再投资率 = 下一年增速 / 增量回报
    nop = [nopat0]
    for g in gs:
        nop.append(nop[-1] * (1 + g))
    rr = [gs[i] / s["roic_inc"] for i in range(len(gs))] + [g_term / s["roic_term"]]
    oe = [nop[i] * (1 - rr[i]) for i in range(len(nop))]       # 2026 … 最后一个显性年
    pv = 0.5 * oe[0]                                           # 2026 下半年，t≈0
    rows = [(2026, nop[0], rr[0], 0.5 * oe[0], 0.0, 0.5 * oe[0])]
    for i in range(1, len(nop)):
        t = T0 + (i - 1)
        d = oe[i] / (1 + r) ** t
        pv += d
        rows.append((2026 + i, nop[i], rr[i], oe[i], t, d))
    nop_next = nop[-1] * (1 + g_term)
    oe_next = nop_next * (1 - g_term / s["roic_term"])
    t_last = T0 + (len(nop) - 2)
    tv = oe_next / (r - g_term)
    pv_tv = tv / (1 + r) ** t_last
    nc = net_cash_adj()[0]
    nonop = sum(NON_OP.values()) * s["nonop_factor"]
    m = MINORITY_SHARE
    equity = (pv + pv_tv + (nc + nonop) * (1 - m) - s["one_off"]
              - s["rp_haircut"] * RELATED_DEPOSIT * (1 - m))
    v = equity / SHARES
    if detail:
        return dict(v=v, v_ex_treasury=equity / (SHARES - TREASURY), equity=equity,
                    pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / equity, rows=rows,
                    nc=nc, nonop=nonop, oe_next=oe_next)
    return v


def weighted(r):
    return sum(SCEN[k]["p"] * dcf(SCEN[k], r) for k in SCEN)


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


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def variant(base_key="base", **kw):
    s = dict(SCEN[base_key])
    s.update(kw)
    return s


# ---------------------------------------------------------------- TTM 拆分（报表原值，亿元）
# 2025：2025_annual_report 第 89-90、172-174 页；H1：2026H1_report 第 44-45、121-123 页（含上年同期列）
PERIODS = {
    "2025": dict(rev=892.31, cost=646.60, fin_int_inc=4.68, fin_fee=0.06, sur=5.18, sell=64.15, adm=25.89,
                 rnd=50.33, int_exp=5.69, int_inc=11.49, fx=2.12, bank_fee=0.56, finsub_int_exp=1.64,
                 other_inc=6.82, inv_inc=4.27, eq_inc=0.45, fv=-3.58, fv_deriv=-3.22, fv_tfl=-1.15,
                 credit=-11.80, asset=-1.38, disposal=-1.23, nonop=1.45 - 1.74, pretax=99.07, tax=14.20,
                 minority=0.80, parent=84.08),
    "2026H1": dict(rev=533.06, cost=384.96, fin_int_inc=2.01, fin_fee=0.004, sur=3.24, sell=34.97, adm=12.99,
                   rnd=23.40, int_exp=2.09, int_inc=6.69, fx=21.04, bank_fee=0.07, finsub_int_exp=0.60,
                   other_inc=5.11, inv_inc=5.80, eq_inc=1.12, fv=4.85, fv_deriv=4.69, fv_tfl=-0.45,
                   credit=-7.14, asset=-0.39, disposal=-0.02, nonop=0.55 - 0.52, pretax=66.64, tax=9.40,
                   minority=0.34, parent=56.90),
    "2025H1": dict(rev=445.34, cost=323.15, fin_int_inc=2.47, fin_fee=0.02, sur=2.77, sell=29.28, adm=12.57,
                   rnd=21.62, int_exp=2.88, int_inc=5.08, fx=-6.69, bank_fee=0.31, finsub_int_exp=0.87,
                   other_inc=3.45, inv_inc=2.46, eq_inc=-0.26, fv=-6.77, fv_deriv=-2.95, fv_tfl=-4.60,
                   credit=-3.83, asset=-0.59, disposal=0.14, nonop=0.48 - 0.66, pretax=60.77, tax=7.92,
                   minority=0.71, parent=52.14),
}
CUSTFIN_SHARE_OF_INT_INC = 0.37   # 财务费用中利息收入属于融资租赁／分期收款的估计比例（其余为存款利息）


def split(p):
    custfin = CUSTFIN_SHARE_OF_INT_INC * p["int_inc"]
    core = (p["rev"] - p["cost"] + p["fin_int_inc"] - p["fin_fee"] + custfin
            - p["sur"] - p["sell"] - p["adm"] - p["rnd"])
    operating = core + p["other_inc"] + p["eq_inc"] + p["credit"] + p["asset"] + p["disposal"] + p["nonop"]
    fx = -p["fx"] + p["fv_deriv"] + p["fv_tfl"]
    financial = ((1 - CUSTFIN_SHARE_OF_INT_INC) * p["int_inc"] + (p["inv_inc"] - p["eq_inc"])
                 + (p["fv"] - p["fv_deriv"] - p["fv_tfl"]) - p["int_exp"] - p["finsub_int_exp"] - p["bank_fee"])
    return dict(core=core, operating=operating, financial=financial, fx=fx,
                check=operating + financial + fx - p["pretax"])


def ttm_bridge(show=True):
    a, b, c = (split(PERIODS[k]) for k in ("2025", "2026H1", "2025H1"))
    ttm = {k: a[k] + b[k] - c[k] for k in ("core", "operating", "financial", "fx")}
    rev = PERIODS["2025"]["rev"] + PERIODS["2026H1"]["rev"] - PERIODS["2025H1"]["rev"]
    if not show:
        return ttm
    print("== TTM 拆分（2025 + 2026H1 - 2025H1，税前，亿元）")
    for name, d in (("2025", a), ("2026H1", b), ("2025H1", c)):
        print(f"  {name}: 核心 EBIT {d['core']:.1f}，经营税前 {d['operating']:.1f}，金融净收益 {d['financial']:.1f}，"
              f"汇兑与套保 {d['fx']:.1f}，与利润总额差 {d['check']:+.2f}")
    print(f"  TTM: 营业收入 {rev:.1f}，核心 EBIT {ttm['core']:.1f}（{ttm['core'] / rev:.1%}），经营税前 {ttm['operating']:.1f}，"
          f"金融净收益 {ttm['financial']:.1f}，汇兑与套保 {ttm['fx']:.1f}")
    op_np = ttm["operating"] * (1 - 0.15) * 0.99
    fin_np = ttm["financial"] * (1 - 0.15)
    print(f"  TTM 剔除汇兑后的归母约 {op_np + fin_np:.1f}（经营 {op_np:.1f} + 金融 {fin_np:.1f}，税率 15%）；报告 TTM 归母 88.84")
    return ttm


def q3_estimate():
    # 2026Q3：营收按同比 +15%（区间 +11%～+18%）；剔汇兑税前利润率 13%；汇兑与套保 -4 亿
    # （9 月末中间价 6.7351，较 6 月末 6.8109 升值 1.1%，按 2026H1 第 143 页敏感性推算）
    q3_2025_rev, q3_2025_np = 213.24, 19.21
    out = []
    for g in (0.11, 0.15, 0.18):
        rev = q3_2025_rev * (1 + g)
        pretax = rev * 0.13 - 4.0
        npar = pretax * (1 - 0.145) * 0.99
        out.append((g, rev, npar))
    print("== 2026Q3 估计（三季报 2026-10-30 披露）")
    for g, rev, npar in out:
        print(f"  营收同比 {g:+.0%}：营业总收入 {rev:.1f}，归母约 {npar:.1f}（2025Q3 为 {q3_2025_np}）")


def main():
    nc, gross, reserve, debt = net_cash_adj()
    print("== 经调整净现金（2026-06-30，亿元）")
    print(f"  现金类合计 {gross:.2f}（货币资金 {CASH} + 拆出 {PLACEMENT} + 交易性 {TRADING_FA} + 短期债权投资 {ST_DEBT_INV}）")
    print(f"  减：受限 {RESTRICTED}，经营备付 {reserve:.2f}，已宣派股利 {DECLARED_DIV}，9 月回购 {BUYBACK_AFTER}，有息负债与类债务 {debt:.2f}")
    print(f"  经调整净现金 = {nc:.2f}；其中三湘银行（关联方）存款 {RELATED_DEPOSIT}")
    print(f"  非经营资产（账面）= {sum(NON_OP.values()):.2f}；少数股东分摊比例 {MINORITY_SHARE:.4f}")
    mcap_a_all = PRICE * SHARES
    mcap_mixed = PRICE * SHARES_A + H_PRICE_HKD * HKD_CNY * SHARES_H
    print(f"  市值：A 股价×全部股份 {mcap_a_all:.1f}；A 股价×A 股 + H 股价×H 股（人民币）{mcap_mixed:.1f}；"
          f"H 股折人民币 {H_PRICE_HKD * HKD_CNY:.2f} 元，A/H 溢价 {PRICE / (H_PRICE_HKD * HKD_CNY) - 1:.1%}")

    print("\n== 正常化（2026 年规模）")
    res = {}
    for k, s in SCEN.items():
        n = normalized(s)
        d = dcf(s, 0.09, detail=True)
        res[k] = (n, d)
        print(f"  {k}: 收入 {n['rev']:.0f}，毛利率 {n['gm']:.1%}，核心 EBIT {n['core_ebit']:.1f}，经营税前 {n['pretax']:.1f}，"
              f"经营归母 {n['nopat']:.1f}，含净利息正常化归母 {n['np_total']:.1f}")

    print("\n== DCF（股权成本 9%，年中折现）")
    for k, (n, d) in res.items():
        print(f"  {k}: V = {d['v']:.2f} 元/股（剔除回购专户 {d['v_ex_treasury']:.2f}），股权价值 {d['equity']:.1f}，"
              f"显性期现值 {d['pv_explicit']:.1f}，终值现值 {d['pv_tv']:.1f}，终值占比 {d['tv_share']:.1%}")
        for (y, nop, rr, oe, t, dv) in d["rows"]:
            print(f"      {y}: 经营归母 {nop:.1f}，再投资率 {rr:.1%}，所有者收益 {oe:.1f}，t={t:.2f}，现值 {dv:.1f}")
        print(f"      终值年所有者收益 {d['oe_next']:.1f}，永续增速 {SCEN[k]['g_term']:.1%}，增量回报 {SCEN[k]['roic_term']:.0%}")

    vw = weighted(0.09)
    pv_ratio = PRICE / vw
    v_ex = sum(SCEN[k]["p"] * res[k][1]["v_ex_treasury"] for k in SCEN)
    print(f"\n== 加权 V = {vw:.2f} 元/股；P/V = {pv_ratio:.3f}（{tier(pv_ratio)}）")
    print(f"   剔除回购专户（{TREASURY:.4f} 亿股）后加权 V = {v_ex:.2f}，P/V = {PRICE / v_ex:.3f}")
    print(f"   进入各档的价格（V 不变）：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n== 股权成本敏感性")
    for r in (0.08, 0.09, 0.10):
        vs = {k: dcf(SCEN[k], r) for k in SCEN}
        print(f"  r={r:.0%}: 熊 {vs['bear']:.2f}，基 {vs['base']:.2f}，牛 {vs['bull']:.2f}，加权 {weighted(r):.2f}")

    irr = solve(lambda r: dcf(SCEN["base"], r), 0.04, 0.30, PRICE)
    irr_w = solve(lambda r: weighted(r), 0.04, 0.30, PRICE)
    print(f"\n== 现价隐含回报：基准情景 IRR = {irr:.2%}；按三情景加权 V 曲线 = {irr_w:.2%}")

    # 反向 DCF
    b = SCEN["base"]
    nb = normalized(b)["nopat"]
    g10 = solve(lambda g: dcf(b, 0.09, growth=[g] * 10, g_term=0.025), -0.10, 0.15, PRICE)
    nopat_imp = solve(lambda x: dcf(b, 0.09, nopat0=x), 10, 300, PRICE)
    g_perp = solve(lambda g: dcf(b, 0.09, growth=[g] * 5, g_term=g), -0.05, 0.06, PRICE)
    print("== 反向 DCF（基准正常化经营归母 %.1f、增量回报 30%%/20%%）" % nb)
    print(f"  10 年恒定增速（之后 2.5%）= {g10:.2%}")
    print(f"  单一永续增速 = {g_perp:.2%}")
    print(f"  按基准增长路径，现价隐含 2026 正常化经营归母 = {nopat_imp:.1f}（含净利息约 {nopat_imp + b['fin_after_tax']:.1f}）")

    # 交叉验证
    eq = 920.84
    print("\n== 交叉验证")
    print(f"  现价 PB = {mcap_a_all / eq:.2f}；基准 V 对应 PB = {res['base'][1]['v'] * SHARES / eq:.2f}")
    for k in SCEN:
        print(f"  {k}: 市值/正常化归母 = {mcap_a_all / res[k][0]['np_total']:.1f}×；V/正常化归母每股 = "
              f"{res[k][1]['v'] * SHARES / res[k][0]['np_total']:.1f}×")
    ev = mcap_mixed - nc - sum(NON_OP.values())
    ttm_op = ttm_bridge(show=False)["operating"]
    print(f"  EV（混合市值 - 经调整净现金 - 非经营资产）= {ev:.1f}；EV/基准经营税前 = {ev / res['base'][0]['pretax']:.1f}×；"
          f"EV/TTM 经营税前（剔汇兑与金融收益）{ttm_op:.1f} = {ev / ttm_op:.1f}×")
    print(f"  股息率（2025 年度 0.31+0.18 元）= {(0.31 + 0.18) / PRICE:.2%}；2026 回购 4～8 亿用于员工持股，不计净回报")

    # 证伪条件触发后的 V
    print("\n== 证伪条件触发后的独立 V（股权成本 9%）")
    f0 = variant(dom_rev=345.0, dom_gm=0.210, intl_rev=620.0, intl_gm=0.300)
    f1 = variant(intl_gm=0.290)
    f2 = variant(dom_rev=320.0, dom_gm=0.200, growth=[0.04, 0.04, 0.04, 0.035, 0.03])
    f3 = variant(impair=0.020, one_off=15.0)
    f4 = variant(intl_gm=0.290, intl_rev=615.0, one_off=13.0)
    fs = {"F0 三季度动能转弱": f0, "F1 海外毛利率正常化至 29%": f1, "F2 国内复苏失败": f2,
          "F3 信用损失上升": f3, "F4 人民币继续大幅升值": f4}
    vb, vu = dcf(SCEN["bear"], 0.09), dcf(SCEN["bull"], 0.09)
    print("  触发后：基准换成对应变体，权重改为熊 35%／变体 50%／牛 15%")
    for name, s in fs.items():
        vv = dcf(s, 0.09)
        vt = 0.35 * vb + 0.50 * vv + 0.15 * vu
        print(f"  {name}: 变体 V = {vv:.2f}（经营归母 {normalized(s)['nopat']:.1f}），触发后独立 V = {vt:.2f}，P/V = {PRICE / vt:.2f}")

    # 增长路径（json 用）
    print("\n== 基准增长路径（经营归母增速；所有者收益 = 经营归母 ×（1 - 再投资率））")
    rows = res["base"][1]["rows"]
    rrs = [r_[2] for r_ in rows[1:]]
    print(f"  增速 {b['growth']}，永续 {b['g_term']}；显性期平均再投资率 {sum(rrs) / len(rrs):.1%}；"
          f"增量回报 {b['roic_inc']:.0%}（终值 {b['roic_term']:.0%}）")
    oe = [2 * rows[0][3]] + [r_[3] for r_ in rows[1:]]
    print("  所有者收益（2026 全年口径起）：" + "，".join(f"{2026 + i}: {x:.1f}" for i, x in enumerate(oe)))

    print()
    ttm_bridge()
    print()
    q3_estimate()


if __name__ == "__main__":
    main()
