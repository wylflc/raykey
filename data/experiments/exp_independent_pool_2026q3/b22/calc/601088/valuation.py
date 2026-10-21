#!/usr/bin/env python3
"""中国神华（601088）独立估值（OI-291 b22，价格日 2026-10-21）。

金额单位亿元（另注明者除外）；价格与 V 为元/股。运行：python3 valuation.py
口径：中国企业会计准则归母；每股价值按全部 A+H 股 216.8943 亿股；现价 49.27 元含 10-26 除息的
中期股息 0.98 元，净现金不扣这笔股息，与含息价比较。经调整净现金为负，按 framework 用有杠杆口径。
"""

# ---------------- 1. 快照 ----------------
PRICE = 49.27                 # A 股 2026-10-21 收盘（腾讯行情）
SHARES = 216.8943             # 亿股，A 183.11952304 + H 33.77482（2026-10-16 权益分派实施公告）
H_PRICE_HKD = 40.22           # H 股 2026-10-21 收盘（腾讯行情）
HKDCNY = 0.8504               # 腾讯行情 2026-10-21
INTERIM_DPS = 0.98            # 2026 中期股息，A 股 10-26 除息
VAL_TO_PRICE_DATE = 113 / 365  # 2026-06-30 → 2026-10-21

# ---------------- 2. 资产负债（2026-06-30，2026H1_report 第 76-77、138-139、161-163、193 页） ----------------
CASH = 1355.92                # 货币资金，其中存放财务公司 702.00
FIN_CO_DEPOSIT = 702.00       # 关联方存款（国家能源集团财务公司），单独列示，不打折
STRUCT_DEPOSIT = 67.01        # 交易性金融资产（结构性存款）
RESTRICTED = 181.97           # 限制用途资金
OPER_RESERVE = 200.0          # 经营备付：约 0.9 个月付现成本（年付现成本约 2,700 亿）
DIV_PAYABLE = 240.23          # 应付股利（含 2025 末期股息 223.40，7-8 月已付）
ST_LOAN = 675.49              # 短期借款（主要为并购贷款）
LT_LOAN = 900.79              # 长期借款 749.23 + 一年内到期 151.56
FACTORING = 96.27             # 其他流动负债：未终止确认的应收保理款（类债务）
LT_PAYABLE_FIN = 286.03       # 长期应付款中的金融负债（含应付采矿权价款现值 180.80，含一年内到期）
MINING_RIGHT_ADV = 36.26      # 其他应付款：代垫矿权转让款（应付关联方，类债务）
LEASE = 12.13                 # 租赁负债，只列示不扣（所有者收益以净利润为起点）
NON_OP = 70.0                 # 其他权益工具投资 72.11 + 其他非流动金融资产 1.23，扣浮盈所得税约 3

net_cash_adj = (CASH + STRUCT_DEPOSIT - RESTRICTED - OPER_RESERVE - DIV_PAYABLE
                - ST_LOAN - LT_LOAN - FACTORING - LT_PAYABLE_FIN - MINING_RIGHT_ADV)
DEBT_RATE = 0.027             # 有息负债实际平均利率：H1 利息费用 24.21×2 ÷ 平均有息负债约 1,730～1,850
TAX = 0.22                    # 有效税率（H1 2026：9,974/45,494=21.9%）

# ---------------- 3. 2026 年报表口径估计 ----------------
H1_PARENT_NP = 287.15         # 2026H1 归母（含 11 家标的 1-3 月合并日前利润，过渡期损益归上市公司）
H1_ONEOFF_ADDBACK = 2.4       # 非经常性中除同一控制项外的净损失（营业外支出滞纳金等 -5.06 等）税后少数后
SPOT_H1, SPOT_Q3, SPOT_Q4 = 772.0, 865.0, 970.0   # 秦皇岛 5500 大卡成交均价（含税）；Q3、Q4 为估计
H2_REALIZATION = 0.8          # 价格上涨传导到 H2 利润的比例（长协按月滞后、外购煤顺价）
H2_CHEM_DELTA = -3.0          # H2 煤化工较 H1 回落（税后归母）
H2_INTEREST_DELTA = -3.0      # 2025 末期股息付出、并购贷款全期计息（税后归母）
H2_ONEOFF = -2.0              # H2 报表非经常性估计（捐赠、滞纳金等）
Q3_SHARE_OF_H2 = 0.54          # Q3 占 H2 经常性利润（Q4 有年末成本计提，历年 Q4 扣非低于 Q3）

# 归母净利对秦皇岛 5500 现货的敏感度（每 100 元/吨，按 2026 年业务量自下而上）
VOL_MKT_OWN = 0.65            # 亿吨/年 自产动力煤市场价部分（H1 32.3 百万吨×2）
VOL_LT_OWN = 4.14             # 亿吨/年 电煤中长协（H1 206.9×2）
VOL_COKING = 0.10             # 亿吨/年 自产炼焦煤
VOL_POWER_EXT = 0.30          # 亿吨/年 发电分部外购煤（总耗煤 1.25 亿吨×23.5%）
EL_MKT, EL_LT, EL_COKING, EL_POWER = 0.75, 0.08, 0.50, 0.45   # 不含税实现价/成本 每变动 1 元现货的变动
RES_TAX = 0.08                # 资源税等从价税费
PARENT_SHARE = 0.81           # 归母占净利（H1 2026：28,715/35,520）
sens_pretax = ((VOL_MKT_OWN * EL_MKT + VOL_LT_OWN * EL_LT + VOL_COKING * EL_COKING) * 100 * (1 - RES_TAX)
               - VOL_POWER_EXT * EL_POWER * 100)
SENS = sens_pretax * (1 - TAX) * PARENT_SHARE            # 亿元归母 / 100 元/吨

spot_h2 = (SPOT_Q3 + SPOT_Q4) / 2
h1_recurring = H1_PARENT_NP + H1_ONEOFF_ADDBACK
h2_uplift = (spot_h2 - SPOT_H1) / 100 * SENS * 0.5 * H2_REALIZATION
h2_recurring = h1_recurring + h2_uplift + H2_CHEM_DELTA + H2_INTEREST_DELTA
np_2026_reported = H1_PARENT_NP + h2_recurring + H2_ONEOFF
np_2026_recurring = h1_recurring + h2_recurring
spot_2026_effective = SPOT_H1 + (spot_h2 - SPOT_H1) * H2_REALIZATION * 0.5   # 2026E 利润所含的有效现货价

# 正常化的其他项目（税后归母）
PURCHASED_VOL = 1.15          # 亿吨/年 外购煤
PURCHASED_MARGIN_2026 = 30.0  # 元/吨（H1 30.6）
CHEM_EBT_2026 = 39.6          # 煤化工分部利润总额 2026E（H1 21.32）
CHEM_TAXSHARE = 0.776         # 税后×归母（化工公司全资，部分 15% 税率）
PURCH_TAXSHARE = (1 - TAX) * 0.95

SCEN = {
    #        概率  正常化现货  外购煤吨毛利  煤化工利润总额  发电调整  显性期再投资率  显性期增速(2027-31)        终值增速  终值再投资率
    "bear": dict(p=0.25, spot=640, purch_m=6.0, chem=5.0, power=-15.0, rr=0.25,
                 growth=[0.000, 0.010, 0.010, 0.005, 0.005], g_t=0.005, rr_t=0.125),
    "base": dict(p=0.50, spot=750, purch_m=12.0, chem=20.0, power=0.0, rr=0.30,
                 growth=[0.010, 0.020, 0.025, 0.020, 0.020], g_t=0.020, rr_t=0.25),
    "bull": dict(p=0.25, spot=880, purch_m=20.0, chem=32.0, power=5.0, rr=0.30,
                 growth=[0.025, 0.030, 0.030, 0.025, 0.025], g_t=0.025, rr_t=0.25),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
INTEREST_AT = 25.0            # 报表税后净利息（归母，2026 年化 13.39×2×1.2×0.78），算经营所有者收益时加回


def normalized_np(s):
    d_price = (s["spot"] - spot_2026_effective) / 100 * SENS
    d_purch = (s["purch_m"] - PURCHASED_MARGIN_2026) * PURCHASED_VOL * PURCH_TAXSHARE
    d_chem = (s["chem"] - CHEM_EBT_2026) * CHEM_TAXSHARE
    return np_2026_recurring + d_price + d_purch + d_chem + s["power"]


def equity_value(s, r, levered=True):
    """2026-06-30 估值、滚动到价格日；返回每股 V 与分项。"""
    np_norm = normalized_np(s)
    pv = 0.0
    # 2026H2：报表口径估计 + 税后净利息，扣再投资，t=0.5
    oe_h2 = (h2_recurring + INTEREST_AT / 2) * (1 - s["rr"])
    pv += oe_h2 / (1 + r) ** 0.5
    np_op = np_norm + INTEREST_AT
    rows = []
    for i, g in enumerate(s["growth"]):
        np_op *= (1 + g)
        oe = np_op * (1 - s["rr"])
        t = 1.5 + i
        pv += oe / (1 + r) ** t
        rows.append((YEARS[i], g, np_op, oe))
    oe_t = np_op * (1 + s["g_t"]) * (1 - s["rr_t"])
    tv = oe_t / (r - s["g_t"])
    pv_tv = tv / (1 + r) ** 5.5
    pv += pv_tv
    debt_net = -net_cash_adj
    if levered:
        debt_cost = debt_net * DEBT_RATE * (1 - TAX) / r
        eq = pv - debt_cost + NON_OP
    else:
        debt_cost = None
        eq = pv + net_cash_adj + NON_OP
    eq_price_date = eq * (1 + r) ** VAL_TO_PRICE_DATE
    return dict(v=eq_price_date / SHARES, eq=eq_price_date, pv_oe=pv, pv_tv=pv_tv,
                tv_share=pv_tv / pv, debt_cost=debt_cost, np_norm=np_norm, rows=rows, oe_h2=oe_h2)


def weighted(r, levered=True):
    return sum(s["p"] * equity_value(s, r, levered)["v"] for s in SCEN.values())


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    print("== 输入与中间量 ==")
    print(f"经调整净现金（无杠杆口径）: {net_cash_adj:,.2f} 亿元；其中财务公司存款 {FIN_CO_DEPOSIT:.2f}；租赁负债 {LEASE:.2f} 只列示")
    print(f"有杠杆口径：净负债 {-net_cash_adj:,.2f} × {DEBT_RATE:.1%} × (1-{TAX:.0%}) = 年税后利息 "
          f"{-net_cash_adj * DEBT_RATE * (1 - TAX):.2f}")
    print(f"现货敏感度：税前 {sens_pretax:.1f} 亿/100 元/吨，归母 {SENS:.1f} 亿/100 元/吨")
    print(f"2026E：H1 经常性 {h1_recurring:.1f}，H2 经常性 {h2_recurring:.1f}（现货抬升贡献 {h2_uplift:.1f}），"
          f"全年报表 {np_2026_reported:.1f}，经常性 {np_2026_recurring:.1f}，所含有效现货 {spot_2026_effective:.0f}")
    q3 = h2_recurring * Q3_SHARE_OF_H2
    print(f"三季度归母估计 {q3:.1f}（前三季度 {H1_PARENT_NP + q3:.1f}），四季度 {h2_recurring - q3 + H2_ONEOFF:.1f}")
    print()
    print("== 情景（股权成本 9%，有杠杆口径） ==")
    res = {}
    for k, s in SCEN.items():
        e = equity_value(s, 0.09, True)
        u = equity_value(s, 0.09, False)
        res[k] = e
        print(f"{k}: p={s['p']:.2f} 正常化现货 {s['spot']} → 2026 正常化归母 {e['np_norm']:.1f}；"
              f"V={e['v']:.2f}（无杠杆 {u['v']:.2f}）；终值占比 {e['tv_share']:.1%}；"
              f"净负债税后利息现值 {e['debt_cost']:.1f}；2026H2 所有者收益 {e['oe_h2']:.1f}")
        print("   年份  增速   经营归母净利  所有者收益")
        for y, g, npop, oe in e["rows"]:
            print(f"   {y}  {g:5.1%}  {npop:9.1f}  {oe:9.1f}")
        print(f"   终值增速 {s['g_t']:.1%}，终值再投资率 {s['rr_t']:.0%}，显性期再投资率 {s['rr']:.0%}，"
              f"增量回报约 {sum(s['growth']) / 5 / s['rr']:.1%}")
    vw = weighted(0.09, True)
    vw_u = weighted(0.09, False)
    pv_ratio = PRICE / vw
    print()
    print(f"加权 V（有杠杆）= {vw:.2f} 元；P/V = {PRICE} / {vw:.2f} = {pv_ratio:.2f}")
    print(f"加权 V（无杠杆，全额扣净负债）= {vw_u:.2f} 元；P/V = {PRICE / vw_u:.2f}")
    print(f"扣除中期股息口径：除息价 {PRICE - INTERIM_DPS:.2f} 对 V {vw - INTERIM_DPS:.2f}，"
          f"P/V = {(PRICE - INTERIM_DPS) / (vw - INTERIM_DPS):.2f}")
    h_rmb = H_PRICE_HKD * HKDCNY
    print(f"H 股 {H_PRICE_HKD} 港元 = {h_rmb:.2f} 元，较 A 股折价 {1 - h_rmb / PRICE:.1%}；H 股 P/V = {h_rmb / vw:.2f}")
    mcap_a = PRICE * SHARES
    mcap_mixed = PRICE * 183.11952304 + h_rmb * 33.77482
    print(f"市值：A 股价×总股本 {mcap_a:,.1f}；A、H 各按本市场价 {mcap_mixed:,.1f}")
    print()
    print("== 股权成本敏感性（加权，有杠杆） ==")
    v8, v10 = weighted(0.08, True), weighted(0.10, True)
    print(f"8%: V={v8:.2f}（P/V {PRICE / v8:.2f}）  10%: V={v10:.2f}（P/V {PRICE / v10:.2f}）")
    irr = solve(lambda r: equity_value(SCEN['base'], r, True)["v"], 0.03, 0.12, PRICE)
    print(f"现价隐含回报（基准情景所有者收益流使现值等于现价的折现率）: {irr:.2%}")
    irr_u = solve(lambda r: equity_value(SCEN['base'], r, False)["v"], 0.03, 0.12, PRICE)
    print(f"  无杠杆口径隐含回报: {irr_u:.2%}")
    print()
    print("== 反向 DCF（9%，基准再投资率） ==")
    base = SCEN["base"]

    def v_perp(g):
        s = dict(base, growth=[g] * 5, g_t=g)
        return equity_value(s, 0.09, True)["v"]
    g_perp = solve(v_perp, 0.0, 0.085, PRICE)
    print(f"现价隐含永续增速（2027 起、再投资率 30%/25%）: {g_perp:.2%}")

    def v_10y(g):
        # 10 年增速 g（2027-2036），之后 2% 永续；再投资率 30%
        np_op = normalized_np(base) + INTEREST_AT
        r = 0.09
        pv = (h2_recurring + INTEREST_AT / 2) * (1 - base["rr"]) / (1 + r) ** 0.5
        for i in range(10):
            np_op *= (1 + g)
            pv += np_op * (1 - base["rr"]) / (1 + r) ** (1.5 + i)
        oe_t = np_op * 1.02 * (1 - 0.25)
        pv += oe_t / (r - 0.02) / (1 + r) ** 10.5
        eq = pv - (-net_cash_adj) * DEBT_RATE * (1 - TAX) / r + NON_OP
        return eq * (1 + r) ** VAL_TO_PRICE_DATE / SHARES
    g10 = solve(v_10y, -0.05, 0.25, PRICE)
    print(f"现价隐含 10 年经营归母净利（所有者收益）年增速（之后 2%）: {g10:.2%}")
    # 现价隐含的正常化归母（其余不变，按比例放大经营所有者收益）
    e_b = equity_value(base, 0.09, True)
    scale = (PRICE * SHARES / (1.09 ** VAL_TO_PRICE_DATE) + e_b["debt_cost"] - NON_OP) / e_b["pv_oe"]
    print(f"现价隐含 2026 正常化经营归母约 {(normalized_np(base) + INTEREST_AT) * scale:.0f}（基准 "
          f"{normalized_np(base) + INTEREST_AT:.0f}，×{scale:.2f}）")
    print()
    print("== 分档价格（V 不变） ==")
    print(f"明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}；高于则偏贵")
    print()
    print("== 交叉验证 ==")
    dps_ttm = 2.01
    print(f"过去 12 个月股息 {dps_ttm} 元，股息率 {dps_ttm / PRICE:.2%}；2026E 每股收益 {np_2026_reported / SHARES:.2f}，"
          f"现价/2026E = {PRICE * SHARES / np_2026_reported:.1f}×；现价/正常化基准 = "
          f"{PRICE * SHARES / normalized_np(base):.1f}×")
    print(f"按正常化基准派息 75%：每股 {normalized_np(base) * 0.75 / SHARES:.2f} 元，9%-2% 股利折现 "
          f"{normalized_np(base) * 0.75 / SHARES * 1.02 / 0.07:.2f} 元")
    roe = normalized_np(base) / 4509.33
    print(f"正常化 ROE {roe:.1%}；剩余收益法 P/B=(ROE-g)/(r-g)={(roe - 0.02) / 0.07:.2f}× → "
          f"{(roe - 0.02) / 0.07 * 4509.33 / SHARES:.2f} 元（假设增量也赚 ROE，偏乐观）")
    ev = PRICE * SHARES - net_cash_adj + 990.98 - NON_OP
    ebit_2026 = 455 + 480 + 32 - 33
    print(f"EV（A 股价市值+经调整净负债+少数股东权益账面-非经营）≈ {ev:,.0f}；2026E EBIT 约 {ebit_2026}，"
          f"EV/EBIT ≈ {ev / ebit_2026:.1f}×")
    print()
    print("== 证伪触发后的 V（加权口径的单因素替换） ==")
    trig = {
        "2027 年秦皇岛 5500 均价≥900 且长协 NCEI≥720：基准现货改 850": dict(spot=850),
        "电煤长协基准价下调（2027 NCEI 年均<660）：基准现货改 650": dict(spot=650),
        "2027 资本开支>650 亿或派息率<65%：基准再投资率改 40%": dict(rr=0.40),
        "2027 商品煤产量<4.9 亿吨：基准增速前两年改 0": dict(growth=[0.0, 0.0, 0.025, 0.020, 0.020]),
        "三季报 Q3 归母<150 亿（10-24）：正常化基数下调 30 亿": dict(spot=750 - 30 / SENS * 100),
    }
    for name, chg in trig.items():
        s = dict(SCEN["base"], **chg)
        vb = equity_value(s, 0.09, True)["v"]
        vw_t = 0.25 * equity_value(SCEN["bear"], 0.09, True)["v"] + 0.5 * vb + \
            0.25 * equity_value(SCEN["bull"], 0.09, True)["v"]
        print(f"{name}: 基准 V {vb:.2f}，加权 V {vw_t:.2f}")


if __name__ == "__main__":
    main()
