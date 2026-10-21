# -*- coding: utf-8 -*-
"""电投能源（002128）独立估值（OI-291 b20，价格日 2026-10-21）。

运行：python3 valuation.py
口径：金额亿元，每股元。资产负债表日 2026-06-30 记为 t=0，现金流按年中折现，
股权价值再按股权成本滚到价格日 2026-10-21（期间无分红除息）。
最新定期报告为 2026 中报：已同一控制下合并白音华煤电并追溯调整（合并日 2026-05-12）。
出处缩写：H1 = 2026H1_report，AR = 2025_annual_report，页码为 PDF 物理页。
"""
from __future__ import annotations

PRICE = 27.57             # 2026-10-21 收盘（腾讯日线）
SHARES = 31.2648          # 亿股：22.4157 + 发行股份购买资产 7.1183 + 配套募资 1.7308（mna_20260715_961802 第5、24页）
COE = 0.09
DAYS_TO_PRICE_DATE = 113  # 2026-06-30 → 2026-10-21
VAT = 1.13

# ---------------- 2026H1 实际锚点（H1 第18、20-21、82-83页） ----------------
H1_PBT = 85.93
H1_PARENT_NP = 52.93
H1_AL_SALES = 71.13                       # 万吨
H1_AL_REV = 150.72                        # 铝业产品收入（亿元），毛利率 39.9%
H1_AL_COST = H1_AL_REV * (1 - 0.399)
H1_AL_PRICE_R = H1_AL_REV / H1_AL_SALES * 1e4          # 不含税实现价 ≈ 21,189 元/吨
H1_SHFE = 24140.0                         # 2026 上半年国内铝现货均价（含税），网络资料
REALIZE_RATIO = H1_AL_PRICE_R * VAT / H1_SHFE          # 实现价/现货 ≈ 0.992（铝液为主）
H1_ALUMINA = 2700.0                       # 2026 上半年氧化铝含税均价（1 月约 2,667、6 月约 2,739），网络资料
ALUMINA_PER_T = 1.92                      # 吨铝氧化铝单耗
H1_NONALUMINA = H1_AL_COST / H1_AL_SALES * 1e4 - ALUMINA_PER_T * H1_ALUMINA / VAT   # ≈ 8,147 元/吨不含税

# 霍煤鸿骏（持股 51%）：H1 净利 22.63 亿（H1 第33页）含补缴 2025 年所得税 2.956 亿（补缴公告 2026-05-29）；
# 2026 年起不在 15% 税率主体之列（H1 第121页，对照 AR 第207页），按 25%。
HMHJ_H1_PBT = (22.63 + 2.956) / 0.75                   # ≈ 34.1
HMHJ_H1_VOL = H1_AL_SALES - 41.65 / 2                  # 扣白音华铝电半年产量 → ≈ 50.3 万吨
HMHJ_H1_PBT_PER_T = HMHJ_H1_PBT / HMHJ_H1_VOL * 1e4   # ≈ 6,782 元/吨
HMHJ_CAP_OUT = 121.0 * 1.04                            # 霍煤鸿骏满产产量（含扎铝二期 35 万吨），万吨/年
HMHJ_COAL_BUY = 850.0                                  # 万吨/年，霍林河集群自备电厂耗煤（H1 第14页）
COAL_PRICE_H1 = 250.0                                  # 褐煤不含税结算价近似（审核问询回复第16页：242-245）

# 煤、电按 H1 年化（H1 约占全年 51-52%）：煤 33.78 → 65.9；火电 5.95 → 11.6；新能源 4.79 → 9.0
COAL_GP_AT_H1 = 65.9
COAL_EXT_REV = 57.04 * 2                  # 外销煤收入年化，用于煤价敏感性（资源税等约 10% 随价联动）

# ---------------- 资产负债（2026-06-30，H1 第77-79、123、147-150页） ----------------
CASH = 104.38
RESTRICTED = 1.42                         # 其他货币资金：保函、履约、复垦、期货保证金
OPER_RESERVE = 15.0                       # 经营备付（约 3% 年收入）
DEBT_ITEMS = {
    "短期借款": 32.95,
    "长期借款（含一年内到期 31.53）": 155.32,
    "长期应付款（采矿权 12.60 + 融资租赁款 4.91，含一年内到期 1.08）": 17.51,
    "其他应付款-股权收购款（白音华现金对价，6-30 未付）": 15.62,
    "应付股利（已宣派）": 1.90,
    "长期应付职工薪酬": 0.66,
}
LEASE_LIAB = 1.27 + 0.50                  # 租赁负债：所有者收益以净利润为起点，列示不扣
DEBT_TOTAL = sum(DEBT_ITEMS.values())
NET_CASH_ADJ = CASH - RESTRICTED - OPER_RESERVE - DEBT_TOTAL        # 无杠杆口径经调整净现金 ≈ −136.0
FINCO_DEPOSIT = 46.96                     # 存放国家电投财务公司 46.71 + 香港财资 0.26（H1 第61-62、123页），单列
RAISED_IN_CASH = 44.55                    # 6-30 募集资金专户余额（H1 第29页），已含在货币资金
RD = 0.022                                # 有息负债实际利率：利息费用 2.04 亿/半年年化 + 资本化利息（资本化率 2.05%）
NON_OP = 12.28 * 0.7 + 1.56 + 0.69 + 0.26   # 长期股权投资七折 + 债权投资 + 其他权益工具 + 投资性房地产

# ---------------- 正常化情景（价格均为含税，沪铝/氧化铝） ----------------
# 吨铝非氧化铝成本（不含税）历史：2023 约 8,650、2024 约 7,630、2025 约 6,900（AR 第43页成本构成）、2026H1 约 8,150；
# 基准取四年均值附近 7,800，熊市 8,400，牛市 7,300。
SCEN = {
    "bear": dict(p=0.25, shfe=18000, alumina=2900, nonal=8400, vol=160.0,
                 coal_px=-0.10, coal_vol=-0.05, thermal=8.5, renew=7.0, other=1.0,
                 surcharge=21.5, tax=0.22, b=0.15, ronic=0.05, drift=-0.010, g_t=-0.010, maint=1.00),
    "base": dict(p=0.50, shfe=20500, alumina=3000, nonal=7800, vol=166.0,
                 coal_px=-0.015, coal_vol=0.0, thermal=11.0, renew=8.5, other=1.1,
                 surcharge=23.5, tax=0.225, b=0.10, ronic=0.07, drift=0.003, g_t=0.005, maint=0.85),
    "bull": dict(p=0.25, shfe=23000, alumina=2800, nonal=7300, vol=168.0,
                 coal_px=0.06, coal_vol=0.0, thermal=12.0, renew=9.2, other=1.2,
                 surcharge=25.0, tax=0.235, b=0.10, ronic=0.08, drift=0.010, g_t=0.015, maint=0.75),
}
SGA = 15.0                 # 销售+管理+研发（2026 调整预算期间费用 19.71 含财务费用约 4.2）
OTHER_ITEMS = -0.6         # 减值、营业外、其他收益净额；联营投资收益不计入（联营按非经营资产）
PARENT_DA = 37.0           # 归母口径折旧摊销（合并约 44.5：H1 固定资产折旧 18.66、无形资产摊销 1.50 等）
OTHER_MINORITY = 0.3       # 扎哈淖尔 2% 等
VOL_2026 = 154.0           # 2026 年铝销量（H1 71.13 + H2 约 83）

# H2 2026：三季度沪铝约 23,600-23,900、10 月约 23,500，氧化铝约 2,690（网络资料）。
# 公司 2026-09-16 调整后预算：全年利润总额 153.45 亿 → H2 隐含 67.52 亿；取 60% 价格模型 + 40% 预算。
H2_BUDGET_PBT = 153.45 - H1_PBT
H2_MODEL_WEIGHT = 0.6
H2 = dict(shfe=23650, alumina=2690, vol=83.0, coal_gp=COAL_GP_AT_H1 * 0.485 * 1.02, thermal=5.7, renew=4.2,
          other=0.5, surcharge=13.9, sga=10.2, other_items=-0.8, tax=0.225, fin=1.95)
# 现价（2026-10 中旬）满产运行率，用于 2027、2028 年周期超额的衰减
SPOT = dict(shfe=23500, alumina=2680, nonal=H1_NONALUMINA, vol=166.0, coal_px=0.03, thermal=11.6,
            renew=9.0, other=1.1, surcharge=25.0, tax=0.235)
FADE = {1: 0.30, 2: 0.10}   # 2027 年保留现价超额的 30%，2028 年 10%，此后为正常化水平


def al_gp_per_t(shfe, alumina, nonal):
    """合并口径吨铝毛利（不含税，元/吨）。"""
    return shfe * REALIZE_RATIO / VAT - nonal - ALUMINA_PER_T * alumina / VAT


def hmhj_pbt_per_t(shfe, alumina, nonal, coal_px):
    """霍煤鸿骏吨铝利润总额：以 H1 实际为锚按价差调整；其外购褐煤随煤价变动。"""
    d_price = shfe * REALIZE_RATIO / VAT - H1_AL_PRICE_R
    d_alumina = -ALUMINA_PER_T * (alumina - H1_ALUMINA) / VAT
    d_nonal = H1_NONALUMINA - nonal
    d_coal = -coal_px * COAL_PRICE_H1 * HMHJ_COAL_BUY / HMHJ_CAP_OUT
    return HMHJ_H1_PBT_PER_T + d_price + d_alumina + d_nonal + d_coal


def normalized(s, vol=None):
    """正常化 EBIT、少数股东与归母经营利润（未扣利息）。"""
    vol = s["vol"] if vol is None else vol
    al = al_gp_per_t(s["shfe"], s["alumina"], s["nonal"]) * vol / 1e4
    coal = (COAL_GP_AT_H1 + s["coal_px"] * COAL_EXT_REV * 0.9) * (1 + s["coal_vol"])
    gp = al + coal + s["thermal"] + s["renew"] + s["other"]
    ebit = gp - s["surcharge"] - SGA + OTHER_ITEMS
    nopat = ebit * (1 - s["tax"])
    hm_vol = min(vol - 41.6, HMHJ_CAP_OUT) if vol > 41.6 else 0.0
    hm_pbt = hmhj_pbt_per_t(s["shfe"], s["alumina"], s["nonal"], s["coal_px"]) * hm_vol / 1e4
    minority = 0.49 * hm_pbt * 0.75 + OTHER_MINORITY
    return dict(al_gp=al, coal_gp=coal, gp=gp, ebit=ebit, nopat=nopat, hm_pbt=hm_pbt,
                minority=minority, np_op=nopat - minority)


def h2_2026():
    s = H2
    al = al_gp_per_t(s["shfe"], s["alumina"], H1_NONALUMINA) * s["vol"] / 1e4
    gp = al + s["coal_gp"] + s["thermal"] + s["renew"] + s["other"]
    ebit = gp - s["surcharge"] - s["sga"] + s["other_items"]
    pbt = ebit - s["fin"]
    hm_pbt = hmhj_pbt_per_t(s["shfe"], s["alumina"], H1_NONALUMINA, 0.02) * (HMHJ_CAP_OUT / 2) / 1e4
    minority_model = 0.49 * hm_pbt * 0.75 + OTHER_MINORITY / 2
    pbt_used = H2_MODEL_WEIGHT * pbt + (1 - H2_MODEL_WEIGHT) * H2_BUDGET_PBT
    minority = minority_model * pbt_used / pbt
    np_parent = pbt_used * (1 - s["tax"]) - minority
    np_op = (pbt_used + s["fin"]) * (1 - s["tax"]) - minority
    return dict(pbt_model=pbt, pbt=pbt_used, minority=minority, np_parent=np_parent, np_op=np_op)


def spot_np_op():
    s = SPOT
    al = al_gp_per_t(s["shfe"], s["alumina"], s["nonal"]) * s["vol"] / 1e4
    coal = COAL_GP_AT_H1 + s["coal_px"] * COAL_EXT_REV * 0.9
    ebit = al + coal + s["thermal"] + s["renew"] + s["other"] - s["surcharge"] - SGA + OTHER_ITEMS
    hm_pbt = hmhj_pbt_per_t(s["shfe"], s["alumina"], s["nonal"], s["coal_px"]) * HMHJ_CAP_OUT / 1e4
    minority = 0.49 * hm_pbt * 0.75 + OTHER_MINORITY
    return ebit * (1 - s["tax"]) - minority


def oe_stream(s, n0, h2_op, spot_op, fade=True):
    """所有者收益 OE = 归母经营利润 ×（1 − 再投资率）+（1 − 维持性资本开支/折旧）× 归母折旧 + 周期超额衰减。"""
    ma = (1 - s["maint"]) * PARENT_DA
    g = s["b"] * s["ronic"] + s["drift"]
    excess = spot_op - n0
    flows = [(0.25, h2_op * (1 - s["b"]) + ma / 2)]           # 2026 下半年
    np_t = n0
    for k in range(1, 6):                                       # 2027-2031，t = 1..5
        if k > 1:
            np_t *= (1 + g)
        extra = excess * FADE.get(k, 0.0) if fade else 0.0
        flows.append((float(k), np_t * (1 - s["b"]) + ma + extra))
    b_t = max(0.0, (s["g_t"] - s["drift"]) / s["ronic"])
    oe_term = np_t * (1 + s["g_t"]) * (1 - b_t) + ma
    return flows, oe_term, g


def value(s, r=COE, leveraged=True, fade=True, n0=None, g_override=None, h2_op=None):
    n0 = normalized(s)["np_op"] if n0 is None else n0
    h2_op = h2_2026()["np_op"] if h2_op is None else h2_op
    ss = dict(s)
    if g_override is not None:
        ss["drift"] = g_override - ss["b"] * ss["ronic"]
        ss["g_t"] = g_override
    flows, oe_term, _ = oe_stream(ss, n0, h2_op, spot_np_op(), fade)
    pv = sum(cf / (1 + r) ** t for t, cf in flows) + oe_term / (r - ss["g_t"]) / (1 + r) ** 5
    nd = -NET_CASH_ADJ
    claim = nd * RD * (1 - s["tax"]) / r if leveraged else nd   # 有杠杆：净负债按现规模滚动，扣税后利息现值
    eq = (pv - claim + NON_OP) * (1 + r) ** (DAYS_TO_PRICE_DATE / 365)
    return eq / SHARES


def weighted(r=COE, leveraged=True, fade=True, scen=None, probs=None, **kw):
    scen = SCEN if scen is None else scen
    probs = {k: s["p"] for k, s in scen.items()} if probs is None else probs
    return sum(probs[k] * value(s, r, leveraged, fade, **kw) for k, s in scen.items())


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


def main():
    h2 = h2_2026()
    sp = spot_np_op()
    np26 = H1_PARENT_NP + h2["np_parent"]
    print("== 输入核对 ==")
    print(f"H1 不含税实现铝价 {H1_AL_PRICE_R:,.0f} 元/吨；实现/现货 {REALIZE_RATIO:.4f}；吨铝非氧化铝成本 {H1_NONALUMINA:,.0f}")
    print(f"霍煤鸿骏 H1 利润总额（剔补缴税）{HMHJ_H1_PBT:.2f} 亿，吨铝 {HMHJ_H1_PBT_PER_T:,.0f} 元")
    print(f"有息及类债务 {DEBT_TOTAL:.2f}；经调整净现金（无杠杆）{NET_CASH_ADJ:.2f}；财务公司存款 {FINCO_DEPOSIT}；"
          f"租赁负债 {LEASE_LIAB:.2f}（列示不扣）；非经营资产 {NON_OP:.2f}")
    print(f"净负债税后利息现值（9%、基准税率）{-NET_CASH_ADJ * RD * (1 - 0.225) / COE:.2f}")
    print(f"H2 2026：模型利润总额 {h2['pbt_model']:.1f}，预算隐含 {H2_BUDGET_PBT:.1f}，采用 {h2['pbt']:.1f}；"
          f"少数股东 {h2['minority']:.1f}；归母 {h2['np_parent']:.1f}；归母经营 {h2['np_op']:.1f}")
    print(f"2026E 报表归母净利 ≈ {np26:.1f} 亿（含补缴税 −1.51），EPS {np26 / SHARES:.2f}；现价满产运行率归母经营利润 {sp:.1f}")

    print("\n== 正常化（2027 满产）==")
    norm26 = {}
    for k, s in SCEN.items():
        n = normalized(s)
        n26 = normalized(s, vol=VOL_2026)
        int_nd = -NET_CASH_ADJ * RD * (1 - s["tax"])
        norm26[k] = n26["np_op"] - (2 * 2.04 - 0.25) * (1 - s["tax"])
        print(f"{k}: 吨铝毛利 {al_gp_per_t(s['shfe'], s['alumina'], s['nonal']):,.0f}；铝毛利 {n['al_gp']:.1f}；煤毛利 {n['coal_gp']:.1f}；"
              f"EBIT {n['ebit']:.1f}；少数股东 {n['minority']:.1f}；归母经营 {n['np_op']:.1f}；扣净负债利息 {n['np_op'] - int_nd:.1f}；"
              f"2026 正常化归母（154 万吨、实际净利息）{norm26[k]:.1f}")

    print("\n== 三情景 V（元/股）==")
    vs = {}
    for k, s in SCEN.items():
        n = normalized(s)
        flows, term, g = oe_stream(s, n["np_op"], h2["np_op"], sp)
        vs[k] = value(s)
        print(f"{k}: p={s['p']:.2f}；2028-31 增速 {g:.4f}，终值 {s['g_t']:.3f}，再投资率 {s['b']:.2f}，增量回报 {s['ronic']:.2f}；"
              f"OE: " + "、".join(f"{cf:.1f}" for _, cf in flows) + f"，终值年 {term:.1f}；"
              f"V有杠杆 {vs[k]:.2f}；V无杠杆 {value(s, leveraged=False):.2f}；V不含衰减 {value(s, fade=False):.2f}")
    vw = weighted()
    vw_u = weighted(leveraged=False)
    print(f"加权 V（有杠杆）{vw:.2f}，P/V {PRICE / vw:.3f}；加权 V（无杠杆）{vw_u:.2f}，P/V {PRICE / vw_u:.3f}")
    print(f"股权成本 8%：{weighted(0.08):.2f}；10%：{weighted(0.10):.2f}（无杠杆 8%：{weighted(0.08, False):.2f}；10%：{weighted(0.10, False):.2f}）")

    base = SCEN["base"]
    nb0 = normalized(base)
    flows, term, _ = oe_stream(base, nb0["np_op"], h2["np_op"], sp)
    pv_h2 = flows[0][1] / (1 + COE) ** flows[0][0]
    pv_exp = sum(cf / (1 + COE) ** t for t, cf in flows[1:])
    pv_term = term / (COE - base["g_t"]) / (1 + COE) ** 5
    claim = -NET_CASH_ADJ * RD * (1 - base["tax"]) / COE
    tot = pv_h2 + pv_exp + pv_term
    print(f"基准拆分（6-30 现值，亿元）：2026H2 {pv_h2:.1f}；2027-31 {pv_exp:.1f}；终值 {pv_term:.1f}（占经营现值 {pv_term / tot:.1%}）；"
          f"净负债税后利息现值 −{claim:.1f}；非经营资产 +{NON_OP:.1f}")
    print(f"现价隐含回报：基准 {solve(lambda r: value(base, r), 0.05, 0.30, PRICE):.4f}；"
          f"三情景加权 {solve(lambda r: weighted(r), 0.05, 0.30, PRICE):.4f}")
    g_imp = solve(lambda g: value(base, g_override=g, fade=False), -0.10, 0.08, PRICE)
    n_imp = solve(lambda x: value(base, n0=x), 10.0, 200.0, PRICE)
    print(f"反向 DCF：基准起点下现价隐含永续增速 {g_imp:.4f}；基准增长结构下现价隐含正常化归母经营利润 {n_imp:.1f} 亿（基准 {normalized(base)['np_op']:.1f}）")
    print(f"敏感性：留存 40% 全部再投资、增量回报 6% → 基准 V {value(dict(base, b=0.40, ronic=0.06)):.2f}")

    print("\n== 证伪触发后的 V（元/股）==")
    f1 = dict(SCEN, base=dict(base, shfe=19000, alumina=3000))
    print(f"F1 沪铝 2027H1 均价 < 19,000 且氧化铝 ≥ 2,800：基准改 19,000，权重 40/50/10 → "
          f"{weighted(scen=f1, probs=dict(bear=0.4, base=0.5, bull=0.1)):.2f}")
    f2 = dict(bear=SCEN['bear'], base=dict(base, b=0.40, ronic=0.06), bull=dict(SCEN['bull'], b=0.40, ronic=0.06))
    print(f"F2 大额新能源基地（留存全部再投资、增量回报 6%）或 2026 年度分红 < 55% → {weighted(scen=f2):.2f}")
    f3 = dict(SCEN, base=dict(base, coal_px=-0.10, coal_vol=-0.05))
    print(f"F3 褐煤结算价较 2026H1 下调 ≥10% 或 2027 年煤炭销量 < 5,900 万吨 → {weighted(scen=f3):.2f}")
    f4 = dict(SCEN, base=dict(base, nonal=8400), bull=dict(SCEN['bull'], nonal=7900))
    print(f"F4 2026 年报吨铝非氧化铝成本 ≥ 8,300（基准改 8,400、牛市 7,900）→ {weighted(scen=f4):.2f}")
    h2_low = (H2_BUDGET_PBT - 6.0 + H2["fin"]) * (1 - H2["tax"]) - h2["minority"] * 0.8
    print(f"F5 三季报前三季度归母 < 72 亿（H2 按预算再减 6 亿）且非氧化铝成本维持 8,400 → "
          f"{weighted(scen=f4, h2_op=h2_low):.2f}")
    print(f"分档价格（V 不变）：明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}")

    print("\n== 交叉验证 ==")
    mcap = PRICE * SHARES
    nb = normalized(base)
    np_b = nb["np_op"] + NET_CASH_ADJ * RD * (1 - base["tax"])
    print(f"市值 {mcap:.1f}；市值/2026E 归母 {mcap / np26:.2f}；市值/基准正常化归母 {mcap / np_b:.2f}；PB {mcap / 528.45:.2f}")
    print(f"基准正常化 ROE {np_b / 528.45:.3f}；理论 PB (ROE−g)/(r−g) {(np_b / 528.45 - base['g_t']) / (COE - base['g_t']):.2f}")
    minority_val = nb["minority"] * 11.0
    ev = mcap - NET_CASH_ADJ + minority_val - NON_OP
    print(f"EV（少数股东按 11 倍盈利 {minority_val:.0f}）{ev:.0f}；EV/基准正常化 EBIT {ev / nb['ebit']:.2f}")
    print(f"股息：2026E 按 60% 派息 {0.6 * np26 / SHARES:.2f} 元/股，股息率 {0.6 * np26 / mcap:.3f}；"
          f"基准正常化 60% 派息 {0.6 * np_b / mcap:.3f}")


if __name__ == "__main__":
    main()
