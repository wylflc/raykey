#!/usr/bin/env python3
"""双汇发展（000895）独立估值（OI-291 b09，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在脚本内，出处见各行注释：
  AR25 = 2025_annual_report，H126 = 2026H1_report，Q126 = 2026Q1_report（页码为 PDF 物理页）；
  IR0325 / IR0828 / IR0831 = 2026-03-25、2026-08-28、2026-08-31 投资者调研记录（东财 PDF，AN 编号见正文来源）。
"""

# ---------------------------------------------------------------- 快照
PRICE = 23.94            # 2026-10-20 收盘（brief）
SHARES = 34.6466         # 亿股，腾讯行情口径；无库存股、无拟注销回购（H126 第 65 页股本 3,464,661,213 股）
VAL_DATE = 2026 + 293 / 365   # 2026-10-20 折成年份小数
COE = 0.09

# ---------------------------------------------------------------- 资产负债表 2026-06-30（H126 第 63-65、114、133、152-154、158 页）
CASH = 39.093            # 货币资金
TIME_DEP = 64.066        # 其他流动资产：不可提前支取的银行定期存款
ST_DEBT_INV = 30.923     # 其他流动资产：短期债权投资（大额存单 24.90、质押式报价回购 2.03、同业存单 3.99）
LT_CD = 9.336            # 其他非流动资产：大额存单
LOANS_ADV = 0.428        # 发放贷款和垫款（财务公司、保理公司）
RESTRICTED = 6.722 + 0.25 + 0.20   # 受限货币资金（央行法定准备金 6.30 等）+ 受限大额存单
DEBT = {                 # 有息负债
    "短期借款": 117.803,           # 其中票据贴现质押借款 70.466（0.58%-1.17%），信用借款 47.337（0.8%-2.30%）
    "一年内到期长期借款": 4.014,
    "一年内到期租赁负债": 0.877,
    "长期借款": 0.088,
    "租赁负债": 1.933,
    "吸收存款": 1.133,             # 财务公司吸收存款；其中关联方好烤克 0.006（H126 第 51、206 页）
}
DIV_PAYABLE = 0.055      # 应付股利（H126 第 155 页）
FINES_COMPANY = 0.7250   # 2026-10-10 处罚：公司及望奎双汇罚没合计 7,250.21 万元，6/30 后付现，按类债务扣除
OP_RESERVE = 15.0        # 经营备付：约 11 天付现成本（年付现成本约 506 亿 = 营收 591 − EBITDA 84）
NON_OP = 3.109 + 0.807   # 长期股权投资 + 其他非流动金融资产（按账面）

# 有息负债实际平均利率：2026H1 利息费用 0.764 + 财务公司利息支出 0.0066，年化 ÷ 平均有息负债（期初 104.58、期末 125.85）
AVG_RATE = (0.7644 + 0.0066) * 2 / ((104.58 + 125.848) / 2)
TAX_INT = 0.25

# ---------------------------------------------------------------- 利润公式（用 2025 与 2026H1 校准）
T_MEAT = 0.228           # 肉制品分部有效税率（2025：所得税 15.13 − 金融收益税 0.36 ≈ 14.77 ÷ 64.46）
T_FIN = 0.25             # 金融收益税率；屠宰、养殖利润免税（H126 第 114 页）
MINORITY = 0.0106        # 少数股东占净利润比例（2025：0.554/51.60；2026H1：0.244/23.30）


def parent_np(meat, slaughter, other_ops, fin=0.0, assoc=0.0):
    """归母净利 =（肉制品×(1−税) + 屠宰 + 其他经营 + 金融×(1−25%) + 联营）×(1−少数股东)。"""
    return (meat * (1 - T_MEAT) + slaughter + other_ops + fin * (1 - T_FIN) + assoc) * (1 - MINORITY)


# 校准：2025 分部经营利润 肉制品 64.46、生鲜品 3.30、其他 −0.80（AR25 第 255 页），其他分部含财务公司净利息 1.844
# （AR25 第 108 页：利息收入 1.856 − 利息支出 0.013），故其他经营 = −0.80 − 1.844 = −2.644；
# 金融收益 = 财务公司净利息 1.844 + 财务费用中净利息与其他（0.720 − 1.495 − 0.090）+ 结构性存款等投资收益 0.393 − 公允价值 0.102 = 1.27
CAL_2025 = parent_np(64.46, 3.30, -2.644, 1.270, 0.309)     # 实际 51.05
# 2026H1：肉制品 31.48、生鲜品 1.37、其他 −2.06（H126 第 210 页），其他含财务公司净利息 0.980（第 68 页 0.987 − 0.0066）
# 金融收益 = 0.980 + 0.298 − 0.764 − 0.034 + 0.179 − 0.046 = 0.613；营业外净额 −0.05 计入其他经营
CAL_H126 = parent_np(31.48, 1.37, -3.04 - 0.05, 0.613, 0.184)  # 实际 23.06

# ---------------------------------------------------------------- 再投资与时间轴
DA = 16.0                                  # 折旧摊销（2025 16.30；2026H1 EBITDA 39.4 − 利润总额 30.6 − 利息 0.76 ≈ 8.0）
CAPEX = [14.0, 14.0, 15.0, 15.0, 16.0]     # 2027-2031；2026 计划约 13 亿（AR25 第 42 页），屠宰产能充足暂不扩产（IR0831）
DWC = 0.3                                  # 每年营运资本小幅占用
YEARS = [2027, 2028, 2029, 2030, 2031]

SCEN = {
    # 正常化 2026：肉制品销量（万吨）× 吨均经营利润（元/吨）；屠宰、其他经营、金融、联营（亿元）
    "bear": dict(p=0.25, vol=137.0, ton=4150.0, slaughter=1.5, other=-3.5, fin=0.9, assoc=0.25,
                 growth=[0.005, 0.005, 0.010, 0.010, 0.010], g_t=0.010, roic_inc=0.10,
                 h2_op_np=23.1, h2_wc=2.0,
                 text="食品安全事件伤及品牌、费用换量失效，肉制品 137 万吨 × 4,150 元/吨（接近 2026Q2 的约 4,070 元）；"
                      "屠宰头均约 10 元、利润 1.5 亿；养猪与禽长期亏损，其他经营 −3.5 亿；增长 0.5%-1%，永续 1%，增量回报 10%"),
    "base": dict(p=0.50, vol=143.0, ton=4450.0, slaughter=4.0, other=-2.0, fin=1.2, assoc=0.35,
                 growth=[0.025, 0.025, 0.020, 0.020, 0.020], g_t=0.020, roic_inc=0.15,
                 h2_op_np=25.8, h2_wc=5.0,   # 2026H2 经营口径归母 = Q3+Q4 估计 25.76 − 金融 0.45 − 联营 0.16 + 罚没 0.64
                 text="肉制品 143 万吨 × 4,450 元/吨 = 63.6 亿（2025 年 4,736、2026H1 4,503）；屠宰 1,550 万头 × 约 26 元 = 4.0 亿；"
                      "其他经营 −2.0 亿（猪价回到 14 元/kg 左右）；增长 2%-2.5%，永续 2%，增量回报 15%"),
    "bull": dict(p=0.25, vol=147.0, ton=4650.0, slaughter=6.0, other=-0.8, fin=1.4, assoc=0.45,
                 growth=[0.035, 0.035, 0.030, 0.030, 0.025], g_t=0.025, roic_inc=0.20,
                 h2_op_np=27.1, h2_wc=7.0,
                 text="新渠道带动肉制品 147 万吨、吨利 4,650 元；屠宰 2,000 万头 × 30 元 = 6.0 亿；猪价回升、冻品增值，其他经营 −0.8 亿；"
                      "增长 2.5%-3.5%，永续 2.5%，增量回报 20%"),
}


def net_cash_adj():
    gross = CASH + TIME_DEP + ST_DEBT_INV + LT_CD + LOANS_ADV
    return gross - RESTRICTED - OP_RESERVE - sum(DEBT.values()) - DIV_PAYABLE - FINES_COMPANY


def norm_2026(s):
    meat = s["vol"] * s["ton"] / 1e4
    np_norm = parent_np(meat, s["slaughter"], s["other"], s["fin"], s["assoc"])
    np_op = parent_np(meat, s["slaughter"], s["other"])
    return meat, np_norm, np_op


def oe_path(s, growth=None, g_t=None):
    """返回 [(时点, 所有者收益)]，以及终值（2031 年末）。所有者收益为经营口径归母（不含金融收益与联营）。"""
    growth = s["growth"] if growth is None else growth
    g_t = s["g_t"] if g_t is None else g_t
    _, _, np_op = norm_2026(s)
    flows = [(2026.0 + 1.0 - VAL_DATE, s["h2_op_np"] + (8.0 - 6.5) + s["h2_wc"])]   # 2026H2：D&A 8.0 − 资本开支 6.5 + 冻品去化
    npv = np_op
    nps = []
    for i, yr in enumerate(YEARS):
        npv *= 1 + growth[i]
        nps.append(npv)
        oe = npv + (DA - CAPEX[i]) - DWC
        flows.append((yr + 1.0 - VAL_DATE, oe))
    reinvest = g_t / s["roic_inc"]
    oe_t = nps[-1] * (1 + g_t) * (1 - reinvest)
    return flows, oe_t, nps


def value(s, r=COE, levered=True, growth=None, g_t=None):
    flows, oe_t, _ = oe_path(s, growth, g_t)
    g = s["g_t"] if g_t is None else g_t
    pv = sum(cf / (1 + r) ** t for t, cf in flows)
    t_last = flows[-1][0]
    tv = oe_t / (r - g)
    pv_tv = tv / (1 + r) ** t_last
    nca = net_cash_adj()
    if levered and nca < 0:
        # 有杠杆口径：净负债按现规模滚动，扣税后利息现值（9% 折现，不随 r 变化以外的假设）
        fin_adj = -(-nca) * AVG_RATE * (1 - TAX_INT) / r
    else:
        fin_adj = nca
    eq = pv + pv_tv + fin_adj + NON_OP
    return eq / SHARES, dict(pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv), fin_adj=fin_adj, equity=eq)


def weighted(r=COE, levered=True, probs=None):
    probs = probs or {k: v["p"] for k, v in SCEN.items()}
    return sum(probs[k] * value(SCEN[k], r, levered)[0] for k in SCEN)


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


def tier(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("=== 校准 ===")
    print(f"2025 公式归母 {CAL_2025:.2f}（实际 51.05）；2026H1 公式归母 {CAL_H126:.2f}（实际 23.06）")

    nca = net_cash_adj()
    gross = CASH + TIME_DEP + ST_DEBT_INV + LT_CD + LOANS_ADV
    print("\n=== 资金（2026-06-30）===")
    print(f"现金类合计 {gross:.2f}（货币资金 {CASH} + 定期存款 {TIME_DEP} + 短期债权投资 {ST_DEBT_INV} + 长期大额存单 {LT_CD} + 贷款垫款 {LOANS_ADV}）")
    print(f"有息负债 {sum(DEBT.values()):.2f}；账面净现金 {gross - sum(DEBT.values()):.2f}")
    print(f"扣受限 {RESTRICTED:.2f}、经营备付 {OP_RESERVE}、应付股利 {DIV_PAYABLE}、待缴罚没 {FINES_COMPANY} 后，经调整净现金 {nca:.2f}")
    print(f"有息负债平均利率 {AVG_RATE:.2%}；净负债税后利息现值 {(-nca) * AVG_RATE * (1 - TAX_INT) / COE:.2f}；非经营资产 {NON_OP:.2f}")
    h1_int_inc = 0.987 + 0.298 + 0.179
    h1_int_exp = 0.7644 + 0.0066
    print(f"利差：2026H1 利息类收入 {h1_int_inc:.3f}（财务公司 0.987 + 财务费用利息收入 0.298 + 结构性存款等 0.179），"
          f"利息支出 {h1_int_exp:.3f}，年化净额 {2 * (h1_int_inc - h1_int_exp):.2f}；"
          f"生息资产收益率约 {2 * h1_int_inc / ((137.66 + gross) / 2):.2%}，负债成本 {AVG_RATE:.2%}")

    print("\n=== 正常化 2026 与三情景 ===")
    res = {}
    for k, s in SCEN.items():
        meat, np_norm, np_op = norm_2026(s)
        v_lev, d = value(s, COE, True)
        v_unl, _ = value(s, COE, False)
        flows, oe_t, nps = oe_path(s)
        res[k] = (v_lev, v_unl, np_norm, np_op, d, flows, oe_t, nps)
        print(f"[{k}] p={s['p']:.2f} 肉制品 {meat:.2f} 屠宰 {s['slaughter']} 其他经营 {s['other']} 金融 {s['fin']} 联营 {s['assoc']}")
        print(f"    正常化归母 2026 {np_norm:.2f}；经营口径归母 {np_op:.2f}")
        print("    所有者收益：" + "，".join(f"t={t:.2f}:{cf:.2f}" for t, cf in flows) + f"；终值年所有者收益 {oe_t:.2f}")
        print(f"    再投资率（终值）{s['g_t'] / s['roic_inc']:.1%}，增量回报 {s['roic_inc']:.0%}，永续增长 {s['g_t']:.1%}；终值占比 {d['tv_share']:.1%}")
        print(f"    V（有杠杆口径）{v_lev:.2f}；V（无杠杆口径）{v_unl:.2f}")

    vw = weighted()
    vw_unl = weighted(levered=False)
    pv = PRICE / vw
    print("\n=== 加权 ===")
    print(f"加权 V（有杠杆，采用）{vw:.2f}，P/V {pv:.3f} → {tier(pv)}")
    print(f"加权 V（无杠杆，对照）{vw_unl:.2f}，P/V {PRICE / vw_unl:.3f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：V {v8:.2f}（P/V {PRICE / v8:.3f}）；10%：V {v10:.2f}（P/V {PRICE / v10:.3f}）")

    base = SCEN["base"]
    irr = solve(lambda r: value(base, r, True)[0], 0.05, 0.15, PRICE)
    print(f"现价隐含回报（基准所有者收益流）{irr:.2%}")

    # 反向 DCF（9%）：(a) 永续增速：显性期与终值同一增速，再投资率 = g / 15%
    def v_const_g(g):
        return value(base, COE, True, growth=[g] * 5, g_t=g)[0]
    g_impl = solve(v_const_g, 0.0, 0.06, PRICE)
    # (b) 10 年增速：2027-2036 同一增速，之后 2% 永续（再投资 13.3%）
    def v_10y(g):
        _, _, np_op = norm_2026(base)
        flows = [(2027.0 - VAL_DATE, base["h2_op_np"] + 1.5 + base["h2_wc"])]
        npv = np_op
        capex = CAPEX + [16.0] * 5
        for i in range(10):
            npv *= 1 + g
            flows.append((2028.0 + i - VAL_DATE, npv + DA - capex[i] - DWC))
        oe_t = npv * 1.02 * (1 - 0.02 / 0.15)
        pv_ = sum(cf / 1.09 ** t for t, cf in flows) + oe_t / 0.07 / 1.09 ** flows[-1][0]
        nca_ = net_cash_adj()
        return (pv_ - (-nca_) * AVG_RATE * 0.75 / 0.09 + NON_OP) / SHARES
    g10 = solve(v_10y, -0.02, 0.10, PRICE)
    print(f"反向 DCF：现价隐含永续增速 {g_impl:.2%}（再投资率 {g_impl / 0.15:.1%}）；或 2027-2036 年所有者收益年增 {g10:.2%}、此后 2% 永续")

    print("\n=== 2026 年下半年估计（基准，供三季报核对）===")
    q3 = parent_np(40.5 * 4700 / 1e4, 0.9, -1.1, 0.30, 0.08)          # 肉制品 40.5 万吨（+3.6%）× 4,700 元/吨
    q4 = parent_np(34.0 * 4450 / 1e4, 1.1, -1.2, 0.30, 0.08) - 0.638  # 罚没对归母影响 0.638（公告）
    fy26 = 23.06 + q3 + q4
    print(f"Q3 归母 {q3:.2f}（2025Q3 16.36）；Q4 归母 {q4:.2f}（2025Q4 11.46）；2026E 归母 {fy26:.2f}（2025 年 51.05）")

    print("\n=== 交叉验证 ===")
    mcap = PRICE * SHARES
    ttm_seg = 66.96 - 30.9 + 30.80   # 2025 全年 − 2025H1（IR0828：1.8 + 29.8 − 0.7）+ 2026H1
    ev = mcap - nca - NON_OP
    print(f"市值 {mcap:.1f}；EV {ev:.1f}；TTM 分部经营利润 {ttm_seg:.1f} → EV/EBIT {ev / ttm_seg:.1f}×")
    print(f"股息率：过去 12 个月 0.80 元 → {0.80 / PRICE:.2%}；2025 年度合计 1.45 元 → {1.45 / PRICE:.2%}；"
          f"2026E 按归母 {fy26:.1f} 亿 × 85%-100% → 每股 {fy26 * 0.85 / SHARES:.2f}-{fy26 / SHARES:.2f} 元，股息率 "
          f"{fy26 * 0.85 / SHARES / PRICE:.2%}-{fy26 / SHARES / PRICE:.2%}；无回购")
    print(f"PE（TTM 归母 50.87）{mcap / 50.87:.1f}×；对正常化基准 {mcap / res['base'][2]:.1f}×；PB {mcap / 209.00:.2f}×")
    # 分部估值（基准，9%）：肉制品税后利润按 g=2%、再投资 13.3%；屠宰、其他按零增长
    meat = base["vol"] * base["ton"] / 1e4
    ev_meat = meat * (1 - T_MEAT) * (1 - MINORITY) * (1 - 0.02 / 0.15) / (0.09 - 0.02)
    ev_sl = base["slaughter"] * (1 - MINORITY) / 0.09
    ev_ot = base["other"] * (1 - MINORITY) / 0.09
    sotp = (ev_meat + ev_sl + ev_ot + (-(-nca) * AVG_RATE * 0.75 / 0.09) + NON_OP) / SHARES
    print(f"分部加总（基准、9%、不含显性期折旧差额）：肉制品 {ev_meat:.0f} + 屠宰 {ev_sl:.0f} + 其他 {ev_ot:.0f} → 每股 {sotp:.2f}")

    print("\n=== 证伪触发后的独立 V（9%）===")
    # F1：三季报（2026-10-28）单季归母 < 13.5 亿或肉制品单季销量同比下滑 → 熊市权重上升
    f1 = weighted(probs={"bear": 0.45, "base": 0.45, "bull": 0.10})
    # F2：2026 年报肉制品吨均经营利润 < 4,200 元且销量 < 140 万吨 → 基准改为 140 × 4,200
    import copy
    b2 = copy.deepcopy(SCEN)
    b2["base"]["vol"], b2["base"]["ton"] = 140.0, 4200.0
    b2["bull"]["vol"], b2["bull"]["ton"] = 144.0, 4450.0
    f2 = sum(b2[k]["p"] * value(b2[k])[0] for k in b2)
    # F3：2027 年报其他分部（不含财务公司）亏损 > 4 亿且屠宰头均 < 15 元 → 基准其他 −4.0、屠宰 2.0
    b3 = copy.deepcopy(SCEN)
    b3["base"]["other"], b3["base"]["slaughter"] = -4.0, 2.0
    f3 = sum(b3[k]["p"] * value(b3[k])[0] for k in b3)
    # F4：资本配置——2026 年度合计分红 < 1.00 元/股且资本开支 > 20 亿（养殖、并购）→ 增量回报降一档
    b4 = copy.deepcopy(SCEN)
    for k, rr in (("bear", 0.08), ("base", 0.10), ("bull", 0.15)):
        b4[k]["roic_inc"] = rr
    f4 = sum(b4[k]["p"] * value(b4[k])[0] for k in b4)
    # F5（向上）：2027 年肉制品销量 ≥ 150 万吨且吨利 ≥ 4,600 元 → 牛市权重上升
    f5 = weighted(probs={"bear": 0.15, "base": 0.50, "bull": 0.35})
    for name, v in (("F1 三季报走弱", f1), ("F2 吨利与销量双降", f2), ("F3 屠宰与其他分部恶化", f3),
                    ("F4 留存资金低回报", f4), ("F5 向上：量利齐升", f5)):
        print(f"{name}：V {v:.2f}，P/V {PRICE / v:.3f}")

    # 现价落入「大致合理」（P/V = 1.10）所需的增速：三情景显性期与永续增速同加 dg
    target = PRICE / 1.10
    def wv_dg(dg):
        return sum(SCEN[k]["p"] * value(SCEN[k], growth=[x + dg for x in SCEN[k]["growth"]],
                                         g_t=SCEN[k]["g_t"] + dg)[0] for k in SCEN)
    dg = solve(wv_dg, 0.0, 0.03, target)
    print(f"P/V = 1.10 需 V ≥ {target:.2f}：三情景增速同加 {dg:.2%}（基准永续 {0.02 + dg:.2%}）")

    print("\n=== 进入各档的价格（V 不变）===")
    print(f"≤0.75 明显低估：≤ {0.75 * vw:.2f}；0.75-0.90 温和低估：{0.75 * vw:.2f}-{0.90 * vw:.2f}；"
          f"0.90-1.10 大致合理：{0.90 * vw:.2f}-{1.10 * vw:.2f}；>1.10：> {1.10 * vw:.2f}")


if __name__ == "__main__":
    main()
