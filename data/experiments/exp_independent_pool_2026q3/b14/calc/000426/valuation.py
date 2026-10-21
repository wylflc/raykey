#!/usr/bin/env python3
"""兴业银锡（000426）独立估值，OI-291 b14，价格日 2026-10-20。

用法：python3 valuation.py
金额单位亿元，金属量单位吨，价格为美元基准价（白银 COMEX 美元/盎司，其余 LME 美元/吨）。
输入全部写在本脚本内，来源页码见正文《来源》一节。
口径：
- 估值基准日 2026-06-30（最新资产负债表），2026H2 现金流按季度中点折现，
  2027 年起按年中折现，终值落在 2040 年末；结果按 9% 滚动 0.307 年到 2026-10-20。
- 经调整净现金为负，按框架用有杠杆口径（净负债按现规模滚动、不还本，
  扣税后利息现值）；无杠杆口径（全额扣净负债）并列输出。
"""

import copy

OZ_PER_T = 32150.7466
SHARES = 17.7564            # 亿股，brief 总股本，无回购专户股份
PRICE = 28.53               # 元/股，2026-10-20 收盘
COE = 0.09
INFL = 0.02                 # 名义价格与成本的年通胀；情景金属价为 2027 年起实际不变的长期价
ROLL_YEARS = 112 / 365      # 2026-06-30 → 2026-10-20

# ---------------------------------------------------------------- 实现价系数
# 2026H1 分产品收入与销量（2026H1_report 第 23-26 页），基准价为同期 COMEX/LME 均价（第 10-13 页）。
# 系数 = 每 1 美元基准价对应的不含税人民币实现收入，含计价系数、加工费、增值税与汇率。
H1 = {
    "ag": (25.1061906, 166.67 * OZ_PER_T, 78.760),   # 收入亿元，销量（盎司），COMEX 均价
    "sn": (8.0822691, 2650.31, 50287.0),             # LME 三月锡均价
    "zn": (5.1052314, 33832.32, 3369.0),
    "pb": (1.3604370, 11204.91, 1971.0),
    "cu": (0.7850460, 1241.76, 13615.0),
}
K = {m: rev * 1e8 / (qty * px) for m, (rev, qty, px) in H1.items()}
OTHER_REV_H1_ANNUAL = 2 * (0.97106544 + 0.67153506 + 0.53905567 + 0.11442757 + 0.03087265 + 0.05083962)  # 铁金锑铋铟其他

# ---------------------------------------------------------------- 现有矿山（2026 年正常年化口径）
EXIST_VOL = {"ag": 316.0, "sn": 6000.0, "zn": 68500.0, "pb": 19200.0, "cu": 2450.0}  # 2026H1 产量×2；锡介于招股书 5,500 吨指引与 Q2 年化 7,900 吨之间
# 2026H1 现金成本：营业成本 13.38 − 折旧摊销 2.61 − 存货下降 1.15×85% = 9.79；管理 1.49、研发 0.48、销售 0.02 → 11.77/半年
EXIST_CASH_OPEX_2026 = 23.8
SURCHARGE_RATE = 0.0612       # 税金及附加/收入（资源税 4.74% + 其他 1.38%），2026H1
EXIST_DA = 5.85               # 2026H1 折旧摊销 2.91 亿 × 2
EXIST_TAX = 0.19              # 2026H1 扣除双源一次性因素后的实际税负
EXIST_SUST_CAPEX_2026 = 6.0   # 维持性资本开支（2023-2025 购建 6.58/6.63/5.28）
YUBANG_CUR = {"ag": 115.0, "pb": 7000.0, "zn": 9000.0, "other": 0.5,
              "opex": 5.3, "da": 2.0, "sust": 1.0, "tax": 0.25}  # 宇邦现有规模（少数股东 15%）；按 H1 净利 4.33 亿（第 151 页）校准成本
NET_INT_2026 = 3.2            # 2026 正常化净利息：H1 利息费用 1.64 亿，下半年计足 7.4% 美元债全期，减利息收入

# ---------------------------------------------------------------- 资产负债表与非经营项目（2026-06-30）
CASH = 36.06
RESTRICTED = 0.20            # 环境治理保证金 0.19、农民工工资保证金、应计利息（H1 第 27 页）
OPER_RESERVE = 2.5           # 约一个月现金成本与税费
DIV_DECLARED = 1.95 + 1.78   # 应付 2025 年末期股利 + 2026 年中期 10 派 1.00 元（9-14 股东会通过）
DEBT = 11.43 + 17.38 + 13.51 + 1.61 + 0.34 + 3.00   # 短借、长借、美元债、一年内到期、租赁、长期应付款（融资租赁+矿业权出让收益）
BOSHENG_DEBT = 2.91 + 3.11   # 博盛矿业非金融机构借款本金 + 应付利息（H1 第 129-130 页）
NOTES_FIN = 0.33             # 应付票据（按融资性质计）
ARO = 1.70                   # 弃置费用预计负债
POST_BS_MNA = 0.42 + 0.11 + 1.64 + 6.21   # 6-30 后已付：FEG 要约、Tartana、西藏阳光（查拉普金矿）、威领 11.05%
# Atlas Tin 25%（2,311 万美元）计入 Achmmach 项目现金流，不在此重复扣
NET_CASH_ADJ_BS = CASH - RESTRICTED - OPER_RESERVE - DIV_DECLARED - DEBT - BOSHENG_DEBT - NOTES_FIN - ARO
NET_CASH_ADJ = NET_CASH_ADJ_BS - POST_BS_MNA
DEBT_RATE = 0.070            # 实际平均利率：H1 利息费用 1.637 亿×2 ÷ 期初期末平均有息负债（含博盛借款）约 46.9 亿

# 非经营资产公允价值估计（亿元），三情景
NONOP = {
    #                 熊     基准   牛
    "天通矿业(联营)":   (1.0, 1.5, 1.7),
    "FEG 34.57%":     (0.5, 0.9, 1.2),
    "双源有色 40%":     (0.8, 1.2, 1.36),
    "中诚信托股权":     (1.2, 1.5, 1.75),
    "铜都 49% 待收款":  (0.5, 0.8, 1.0),
    "威领 11.05%":     (1.5, 3.5, 6.0),   # 成本 6.21，10-19 市值约 6.67，*ST 退市风险折价
    "Tartana 9.99%":  (0.05, 0.1, 0.15),
    "查拉普金矿":       (1.0, 1.64, 2.5),
    "唐河镍矿(停建)":   (0.0, 1.0, 2.0),
    "博盛金矿重启期权":  (0.0, 2.0, 5.0),
    "威领后续投入负NPV": (-7.0, -4.0, -1.0),  # 18 亿额度余约 11.8 亿
}

# ---------------------------------------------------------------- 情景
SCEN = {
    "bear": dict(
        p=0.25, px={"ag": 38.0, "sn": 32000.0, "zn": 2500.0, "pb": 1900.0, "cu": 9500.0}, other_scale=0.75,
        vol_ovr={"ag": 305.0, "sn": 5000.0},
        downtime=0.05, safety_add=0.5, decline=0.025, g=0.005,   # 低价环境下外包与奖金成本回落，抵消部分安全投入
        # 熊市：低价下改为约一半规模的一期（约 400 万吨/年）并推迟一年，资本开支含超支
        yubang=dict(capex={2027: 1.5, 2028: 6.0, 2029: 7.0, 2030: 3.5}, ramp={2031: 0.4, 2032: 0.8, 2033: 1.0},
                    vol={"ag": 130.0, "pb": 12000.0, "zn": 20000.0}, opex=7.5, surcharge=SURCHARGE_RATE,
                    tax=0.25, sust=1.5, own=0.85),
        yinman=dict(capex={2026.5: 0.8, 2027: 3.5, 2028: 4.5, 2029: 3.0, 2030: 1.0}, ramp={2030: 0.3, 2031: 0.7, 2032: 1.0},
                    vol={"ag": 50.0, "sn": 1500.0, "zn": 13000.0, "pb": 3000.0, "cu": 500.0}, opex=5.5,
                    surcharge=SURCHARGE_RATE, tax=0.15, sust=0.8, own=1.0),
        # 熊市：锡价 3.2 万美元下项目现金流为负，按唐河镍矿先例在前期投入后暂停，不产出
        achmmach=dict(capex={2026.5: 1.64, 2027: 3.0, 2028: 2.0}, ramp={},
                      vol={"sn": 3500.0}, opex=5.5, surcharge=0.04, tax=0.30, sust=0.6, own=1.0),
    ),
    "base": dict(
        p=0.50, px={"ag": 52.0, "sn": 40000.0, "zn": 2800.0, "pb": 2000.0, "cu": 11000.0}, other_scale=0.90,
        vol_ovr={"ag": 316.0, "sn": 6000.0},
        downtime=0.04, safety_add=1.0, decline=0.02, g=0.01,
        yubang=dict(capex={2026.5: 0.5, 2027: 6.5, 2028: 10.5, 2029: 8.5}, ramp={2030: 0.4, 2031: 0.8, 2032: 1.0},
                    vol={"ag": 260.0, "pb": 25000.0, "zn": 40000.0}, opex=13.5, surcharge=SURCHARGE_RATE,
                    tax=0.25, sust=1.5, own=0.85),
        yinman=dict(capex={2026.5: 1.0, 2027: 4.0, 2028: 4.0, 2029: 2.0}, ramp={2029: 0.3, 2030: 0.7, 2031: 1.0},
                    vol={"ag": 70.0, "sn": 2200.0, "zn": 18000.0, "pb": 4000.0, "cu": 700.0}, opex=5.5,
                    surcharge=SURCHARGE_RATE, tax=0.15, sust=0.8, own=1.0),
        achmmach=dict(capex={2026.5: 1.64 + 0.5, 2027: 5.0, 2028: 8.0, 2029: 5.0}, ramp={2029: 0.25, 2030: 0.75, 2031: 1.0},
                      vol={"sn": 4500.0}, opex=5.5, surcharge=0.04, tax=0.30, sust=0.6, own=1.0),
    ),
    "bull": dict(
        p=0.25, px={"ag": 68.0, "sn": 50000.0, "zn": 3100.0, "pb": 2100.0, "cu": 13000.0}, other_scale=1.05,
        vol_ovr={"ag": 325.0, "sn": 7000.0},
        downtime=0.02, safety_add=0.5, decline=0.01, g=0.02,
        yubang=dict(capex={2026.5: 1.0, 2027: 8.0, 2028: 9.5, 2029: 6.0}, ramp={2029: 0.4, 2030: 0.8, 2031: 1.0},
                    vol={"ag": 335.0, "pb": 30000.0, "zn": 48000.0}, opex=13.5, surcharge=SURCHARGE_RATE,
                    tax=0.25, sust=1.5, own=0.85),
        yinman=dict(capex={2026.5: 1.0, 2027: 4.5, 2028: 4.5, 2029: 1.0}, ramp={2029: 0.5, 2030: 0.9, 2031: 1.0},
                    vol={"ag": 100.0, "sn": 3000.0, "zn": 20000.0, "pb": 5000.0, "cu": 900.0}, opex=5.8,
                    surcharge=SURCHARGE_RATE, tax=0.15, sust=0.8, own=1.0),
        achmmach=dict(capex={2026.5: 1.64 + 0.8, 2027: 6.0, 2028: 8.0, 2029: 3.0}, ramp={2029: 0.4, 2030: 0.9, 2031: 1.0},
                      vol={"sn": 5500.0}, opex=5.8, surcharge=0.04, tax=0.30, sust=0.6, own=1.0),
    ),
}

YEARS = list(range(2027, 2041))
NONOP_IDX = {"bear": 0, "base": 1, "bull": 2}


def revenue(vol, px):
    """vol 吨，px 美元基准价 → 亿元（不含税）。"""
    r = 0.0
    for m, q in vol.items():
        if m not in K or q == 0:
            continue
        unit = OZ_PER_T if m == "ag" else 1.0
        r += q * unit * px[m] * K[m] / 1e8
    return r


def exist_vol(s):
    v = dict(EXIST_VOL)
    v.update(s.get("vol_ovr", {}))
    return v


def px_at(px0, year):
    f = (1 + INFL) ** max(0, year - 2027)
    return {m: v * f for m, v in px0.items()}


def h2_2026(s):
    """2026H2：现有矿山（含银漫停产损失）+ 维持性开支；项目资本开支在 project_cf 里。"""
    px_h2 = {"ag": 62.0, "sn": 50000.0, "zn": 3000.0, "pb": 1950.0, "cu": 13000.0}  # Q3 约 64、Q4 约 60（网络事实）
    vol_h2 = {m: v / 2 for m, v in EXIST_VOL.items()}
    rev = revenue(vol_h2, px_h2) + OTHER_REV_H1_ANNUAL / 2 * 0.95
    yinman_rev_normal = 18.0
    lost_share = 0.55            # 银漫 7-26 停产，选厂 9-03 复产，采区至 10-20 未见复产公告
    lost_rev = yinman_rev_normal * lost_share
    ebitda = rev - EXIST_CASH_OPEX_2026 / 2 - SURCHARGE_RATE * rev
    lost_contrib = lost_rev * (1 - SURCHARGE_RATE - 0.12)
    ebitda -= lost_contrib + 0.3          # 停工期间费用、罚款等
    tax = EXIST_TAX * (ebitda - EXIST_DA / 2)
    fcf = ebitda - tax - EXIST_SUST_CAPEX_2026 / 2
    ni = (ebitda - EXIST_DA / 2 - (NET_INT_2026 / 2)) * (1 - EXIST_TAX)
    minority = 0.30
    return dict(rev=rev, ebitda=ebitda, fcf=fcf - minority, ni_parent=ni - minority)


def existing_cf(s, year):
    vf = (1 - s["decline"]) ** max(0, year - 2027)
    infl = (1 + INFL) ** (year - 2026)
    px = px_at(s["px"], year)
    vol = {m: v * vf * (1 - s["downtime"]) for m, v in exist_vol(s).items()}
    rev = revenue(vol, px) + OTHER_REV_H1_ANNUAL * s["other_scale"] * vf * (1 - s["downtime"]) * (1 + INFL) ** max(0, year - 2027)
    opex = (EXIST_CASH_OPEX_2026 + s["safety_add"]) * infl * (0.5 + 0.5 * vf)
    ebitda = rev - opex - SURCHARGE_RATE * rev
    tax = max(0.0, EXIST_TAX * (ebitda - EXIST_DA))
    sust = EXIST_SUST_CAPEX_2026 * infl * (0.5 + 0.5 * vf)
    # 宇邦现有规模的少数股东份额
    yb = YUBANG_CUR
    yb_rev = revenue({"ag": yb["ag"] * (1 - s["downtime"]), "pb": yb["pb"], "zn": yb["zn"]}, px) + yb["other"] * infl
    yb_ebitda = yb_rev * (1 - SURCHARGE_RATE) - yb["opex"] * infl
    yb_fcf = yb_ebitda - max(0.0, yb["tax"] * (yb_ebitda - yb["da"])) - yb["sust"] * infl
    minority = 0.15 * yb_fcf
    return dict(rev=rev, ebitda=ebitda, fcf=ebitda - tax - sust - minority, ebit=ebitda - EXIST_DA)


def project_cf(pp, s, year):
    capex = pp["capex"].get(year, 0.0)
    ramp = pp["ramp"].get(year, 1.0 if pp["ramp"] and year > max(pp["ramp"]) else 0.0)
    infl = (1 + INFL) ** (year - 2026)
    if ramp > 0:
        px = px_at(s["px"], year)
        vol = {m: v * ramp * (1 - s["downtime"]) for m, v in pp["vol"].items()}
        rev = revenue(vol, px)
        opex = pp["opex"] * infl * (0.3 + 0.7 * ramp)
        ebitda = rev * (1 - pp["surcharge"]) - opex
        total_capex = sum(pp["capex"].values())
        tax = max(0.0, pp["tax"] * (ebitda - total_capex / 15))
        sust = pp["sust"] * infl * ramp
    else:
        rev = ebitda = tax = sust = 0.0
    fcf = (ebitda - tax - sust - capex) * pp["own"]
    return dict(rev=rev, ebitda=ebitda, fcf=fcf, capex=capex * pp["own"])


def scenario_value(name, coe=COE, levered=True, detail=False):
    s = SCEN[name]
    h2 = h2_2026(s)
    pv = 0.0
    rows = []
    # 2026H2：现有矿山 + 项目在 2026.5 的资本开支，季度中点 0.25 年
    proj_h2 = sum(project_cf(s[k], s, 2026.5)["fcf"] for k in ("yubang", "yinman", "achmmach"))
    cf_h2 = h2["fcf"] + proj_h2
    pv += cf_h2 / (1 + coe) ** 0.25
    rows.append((2026.5, cf_h2, h2["fcf"], proj_h2))
    last = None
    for y in YEARS:
        ex = existing_cf(s, y)
        pr = {k: project_cf(s[k], s, y) for k in ("yubang", "yinman", "achmmach")}
        cf = ex["fcf"] + sum(v["fcf"] for v in pr.values())
        t = y - 2026            # 年中折现，距 2026-06-30 的年数
        pv += cf / (1 + coe) ** t
        rows.append((y, cf, ex["fcf"], sum(v["fcf"] for v in pr.values())))
        last = cf
    tv = last * (1 + s["g"]) / (coe - s["g"])
    pv_tv = tv / (1 + coe) ** (2040.5 - 2026.0)
    pv_ops = pv + pv_tv
    nd = -NET_CASH_ADJ
    if levered:
        claim = nd * DEBT_RATE * (1 - EXIST_TAX) / coe
    else:
        claim = nd
    nonop = sum(v[NONOP_IDX[name]] for v in NONOP.values())
    equity = (pv_ops - claim) * (1 + coe) ** ROLL_YEARS + nonop
    v = equity / SHARES
    if detail:
        return dict(v=v, pv_ops=pv_ops, pv_tv=pv_tv, claim=claim, nonop=nonop, rows=rows, tv_share=pv_tv / pv_ops)
    return v


def normalized_np_2026(name):
    """2026 年正常化归母净利：现有矿山 2026 正常年化量 × 情景价（2026 年口径），含净利息与少数股东，剔除一次性。"""
    s = SCEN[name]
    px = s["px"]
    vol = {m: v * (1 - s["downtime"]) for m, v in exist_vol(s).items()}
    rev = revenue(vol, px) + OTHER_REV_H1_ANNUAL * s["other_scale"] * (1 - s["downtime"])
    ebit = rev * (1 - SURCHARGE_RATE) - (EXIST_CASH_OPEX_2026 + s["safety_add"]) - EXIST_DA
    ni = (ebit - NET_INT_2026) * (1 - EXIST_TAX)
    yb = YUBANG_CUR
    yb_rev = revenue({"ag": yb["ag"] * (1 - s["downtime"]), "pb": yb["pb"], "zn": yb["zn"]}, px) + yb["other"]
    yb_ni = (yb_rev * (1 - SURCHARGE_RATE) - yb["opex"] - yb["da"]) * (1 - yb["tax"])
    minority = 0.15 * yb_ni - 0.05    # 博盛 30% 少数股东承担的亏损
    return dict(rev=rev, ebit=ebit, ni_parent=ni - minority)


def weighted(coe=COE, levered=True):
    return sum(SCEN[n]["p"] * scenario_value(n, coe, levered) for n in SCEN)


def implied_irr(name="base", levered=True):
    lo, hi = 0.03, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if scenario_value(name, mid, levered) > PRICE:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_silver(levered=True):
    """反向 DCF：其余假设取基准情景，求使基准情景 V = 现价的长期银价。"""
    base_ag = SCEN["base"]["px"]["ag"]
    lo, hi = 20.0, 150.0
    for _ in range(200):
        mid = (lo + hi) / 2
        SCEN["base"]["px"]["ag"] = mid
        v = scenario_value("base", COE, levered)
        if v > PRICE:
            hi = mid
        else:
            lo = mid
    SCEN["base"]["px"]["ag"] = base_ag
    return (lo + hi) / 2


def implied_growth_existing():
    """反向 DCF：只看现有矿山（不含扩建），2027 年基准所有者收益需以多高的 10 年增速（之后 2.5%）才能支撑现价。"""
    s = SCEN["base"]
    oe0 = existing_cf(s, 2027)["fcf"]
    target = PRICE * SHARES / (1 + COE) ** ROLL_YEARS + (-NET_CASH_ADJ) * DEBT_RATE * (1 - EXIST_TAX) / COE \
        - sum(v[1] for v in NONOP.values()) / (1 + COE) ** ROLL_YEARS
    lo, hi = -0.2, 0.5
    for _ in range(200):
        g = (lo + hi) / 2
        pv, cf = 0.0, oe0
        for i in range(10):
            pv += cf / (1 + COE) ** (i + 1)
            cf *= (1 + g)
        pv += cf * 1.025 / (COE - 0.025) / (1 + COE) ** 10
        if pv > target:
            hi = g
        else:
            lo = g
    return oe0, (lo + hi) / 2


def weighted_with(mod, coe=COE):
    """在情景副本上施加修改 mod(scen, nonop)，返回加权 V（有杠杆）。"""
    global SCEN, NONOP
    saved_s, saved_n = SCEN, NONOP
    SCEN, NONOP = copy.deepcopy(saved_s), copy.deepcopy(saved_n)
    try:
        mod(SCEN, NONOP)
        return sum(SCEN[n]["p"] * scenario_value(n, coe) for n in SCEN)
    finally:
        SCEN, NONOP = saved_s, saved_n


def _f_price_down(sc, no):
    sc["bear"]["p"], sc["base"]["p"], sc["bull"]["p"] = 0.5, 0.5, 0.0


def _f_price_up(sc, no):
    sc["base"]["px"] = {"ag": 60.0, "sn": 48000.0, "zn": 2900.0, "pb": 2000.0, "cu": 12000.0}
    sc["bull"]["px"] = {"ag": 75.0, "sn": 55000.0, "zn": 3200.0, "pb": 2150.0, "cu": 13500.0}
    sc["bear"]["px"] = {"ag": 45.0, "sn": 38000.0, "zn": 2600.0, "pb": 1900.0, "cu": 10000.0}


def _f_safety(sc, no):
    for n, extra in (("bear", 0.03), ("base", 0.03), ("bull", 0.02)):
        sc[n]["downtime"] += extra
        sc[n]["safety_add"] += 0.5


def _shift(d, k):
    return {(y + k if y != 2026.5 else 2027 + (k - 1)): v for y, v in d.items()}


def _f_yubang_delay(sc, no):
    for n in ("base", "bull"):
        yb = sc[n]["yubang"]
        yb["capex"] = _shift(yb["capex"], 2)
        yb["ramp"] = {y + 2: v for y, v in yb["ramp"].items()}


def _f_tin_low(sc, no):
    for n, sn in (("bear", 4200.0), ("base", 4800.0), ("bull", 5800.0)):
        sc[n]["vol_ovr"]["sn"] = sn


def _f_capital(sc, no):
    no["威领 11.05%"] = (0.5, 1.5, 3.0)
    no["威领后续投入负NPV"] = (-10.0, -8.0, -5.0)


FALSIFIERS = [
    ("COMEX 白银 2027 年均价 < 42 美元/盎司且 LME 锡 2027 年均价 < 36,000 美元/吨（熊市价格兑现，权重改为熊 0.5、基准 0.5）", _f_price_down),
    ("COMEX 白银 2027 年均价 ≥ 65 美元/盎司且 LME 锡 ≥ 48,000 美元/吨（高价持续，正常化价格上移：熊 45/3.8 万、基准 60/4.8 万、牛 75/5.5 万）", _f_price_up),
    ("银漫采区 2026-12-31 前仍未复产，或 2027 年内主力矿山再发生停产 ≥ 30 天的事故（停产折损各情景 +2～3 个百分点、安全成本 +0.5 亿/年）", _f_safety),
    ("宇邦 825 万吨/年项目 2027-06-30 前仍未取得开工许可（基准与牛市进度推迟两年）", _f_yubang_delay),
    ("2026 年报锡产量 < 4,800 吨，或 2027 年锡产量年化 < 4,800 吨（现有锡产量下调约 1,000 吨）", _f_tin_low),
    ("威领投入超出 18 亿元额度、为威领债务担保，或再宣布单笔 ≥ 10 亿元非银锡主业并购（威领持股与后续投入减值）", _f_capital),
]


def sotp(name, coe=COE):
    """分部现值（2026-06-30，亿元）：现有矿山、三个扩建项目；终值按各自 2040 年现金流与情景 g 计。"""
    s = SCEN[name]
    parts = {"现有矿山": 0.0, "宇邦825": 0.0, "银漫二期": 0.0, "Achmmach": 0.0}
    keys = {"宇邦825": "yubang", "银漫二期": "yinman", "Achmmach": "achmmach"}
    parts["现有矿山"] += h2_2026(s)["fcf"] / (1 + coe) ** 0.25
    for nm, k in keys.items():
        parts[nm] += project_cf(s[k], s, 2026.5)["fcf"] / (1 + coe) ** 0.25
    last = {}
    for y in YEARS:
        t = y - 2026
        ex = existing_cf(s, y)["fcf"]
        parts["现有矿山"] += ex / (1 + coe) ** t
        last["现有矿山"] = ex
        for nm, k in keys.items():
            cf = project_cf(s[k], s, y)["fcf"]
            parts[nm] += cf / (1 + coe) ** t
            last[nm] = cf
    for nm in parts:
        parts[nm] += last[nm] * (1 + s["g"]) / (coe - s["g"]) / (1 + coe) ** (2040.5 - 2026.0)
    return parts


def growth_path():
    """所有者收益（现有矿山 FCF + 项目经营 FCF，不扣扩建资本开支），基准情景。"""
    s = SCEN["base"]
    out = []
    for y in [2026] + list(range(2027, 2033)):
        if y == 2026:
            oe = existing_cf(s, 2027)["fcf"] / (1 + INFL)
            growth_capex = 0.0
        else:
            ex = existing_cf(s, y)["fcf"]
            pr = [project_cf(s[k], s, y) for k in ("yubang", "yinman", "achmmach")]
            oe = ex + sum(p["fcf"] + p["capex"] for p in pr)
            growth_capex = sum(p["capex"] for p in pr)
        out.append((y, oe, growth_capex))
    return out


def main():
    print(f"实现价系数（元/美元基准）：" + "，".join(f"{m} {k:.3f}" for m, k in K.items()))
    print(f"经调整净现金（资产负债表日）{NET_CASH_ADJ_BS:.2f} 亿；扣 6-30 后并购付款 {POST_BS_MNA:.2f} 后 {NET_CASH_ADJ:.2f} 亿")
    print(f"有杠杆口径扣减：净负债 {-NET_CASH_ADJ:.2f} × {DEBT_RATE:.1%} ×(1-{EXIST_TAX:.0%}) ÷ 9% = "
          f"{-NET_CASH_ADJ * DEBT_RATE * (1 - EXIST_TAX) / COE:.2f} 亿")
    print()
    for n in SCEN:
        d = scenario_value(n, detail=True)
        du = scenario_value(n, levered=False)
        npn = normalized_np_2026(n)
        print(f"[{n}] p={SCEN[n]['p']:.2f}  V(有杠杆)={d['v']:.2f}  V(无杠杆)={du:.2f}  "
              f"经营现值={d['pv_ops']:.1f} 终值占比={d['tv_share']:.0%} 非经营={d['nonop']:.1f}  "
              f"2026 正常化归母={npn['ni_parent']:.2f}（收入 {npn['rev']:.1f}，EBIT {npn['ebit']:.1f}）")
        print("   年度 FCF（合计/现有/项目）：" + "；".join(
            f"{r[0] if r[0] != 2026.5 else '26H2'}:{r[1]:.1f}/{r[2]:.1f}/{r[3]:.1f}" for r in d["rows"][:8]))
    vw = weighted()
    vwu = weighted(levered=False)
    print()
    print(f"加权 V（有杠杆）= {vw:.2f} 元，P/V = {PRICE / vw:.2f}；无杠杆加权 V = {vwu:.2f}，P/V = {PRICE / vwu:.2f}")
    print(f"股权成本 8%：V = {weighted(0.08):.2f}；10%：V = {weighted(0.10):.2f}")
    print(f"现价隐含回报（基准情景，有杠杆）= {implied_irr():.2%}；无杠杆 = {implied_irr(levered=False):.2%}")
    print(f"反向：基准其余不变，现价隐含长期银价 = {implied_silver():.1f} 美元/盎司")
    oe0, g = implied_growth_existing()
    print(f"反向：仅现有矿山，2027 所有者收益 {oe0:.1f} 亿，现价隐含前 10 年增速 {g:.1%}（之后 2.5%）")
    spot = {"ag": 60.0, "sn": 50000.0, "zn": 3000.0, "pb": 1950.0, "cu": 13000.0}
    base_px = dict(SCEN["base"]["px"])
    SCEN["base"]["px"] = spot
    v_spot = scenario_value("base")
    SCEN["base"]["px"] = dict(base_px, ag=base_px["ag"] + 5)
    v_ag5 = scenario_value("base")
    SCEN["base"]["px"] = dict(base_px, sn=base_px["sn"] + 5000)
    v_sn5 = scenario_value("base")
    SCEN["base"]["px"] = base_px
    print(f"参照：基准量与执行、现货价（银 60、锡 50,000）下 V = {v_spot:.2f}；银 +5 美元 V +{v_ag5 - scenario_value('base'):.2f}；"
          f"锡 +5,000 美元 V +{v_sn5 - scenario_value('base'):.2f}")
    SCEN["base"]["px"] = dict(base_px, ag=38.0, sn=32000.0)
    v_bearpx = scenario_value("base")
    proj_bearpx = sum(v for k, v in sotp("base").items() if k != "现有矿山") * (1 + COE) ** ROLL_YEARS / SHARES
    SCEN["base"]["px"] = base_px
    print(f"参照：基准执行、仅银锡降到熊市价（银 38、锡 32,000）下 V = {v_bearpx:.2f}，三个扩建项目合计 {proj_bearpx:.2f} 元/股")
    print()
    for n in SCEN:
        pt = sotp(n)
        print(f"分部现值[{n}]（亿元，6-30）：" + "，".join(f"{k} {v:.1f}" for k, v in pt.items())
              + f"；合计 {sum(pt.values()):.1f}；每股 " + "，".join(f"{k} {v * (1 + COE) ** ROLL_YEARS / SHARES:.2f}" for k, v in pt.items()))
    print()
    print("证伪条件触发后的加权 V：")
    for desc, f in FALSIFIERS:
        print(f"  {weighted_with(f):6.2f}  {desc}")
    print()
    gp = growth_path()
    print("基准所有者收益路径（亿元，扩建资本开支另列）：" + "；".join(f"{y}:{oe:.1f}/{gc:.1f}" for y, oe, gc in gp))
    gr = [gp[i][1] / gp[i - 1][1] - 1 for i in range(1, 6)]
    print("2027-2031 增速：" + "，".join(f"{g:.1%}" for g in gr))
    tot_gc = sum(sum(SCEN["base"][k]["capex"].values()) * SCEN["base"][k]["own"] for k in ("yubang", "yinman", "achmmach"))
    oe_sum = sum(oe for y, oe, gc in gp if 2027 <= y <= 2029) + existing_cf(SCEN["base"], 2027)["fcf"] / 2
    steady = sum(project_cf(SCEN["base"][k], SCEN["base"], 2032)["fcf"] for k in ("yubang", "yinman", "achmmach")) / (1 + INFL) ** 6
    print(f"扩建资本开支合计（归母）{tot_gc:.1f} 亿；2026H2-2029 所有者收益约 {oe_sum:.1f} 亿，再投资率约 {tot_gc / oe_sum:.0%}；"
          f"达产后项目年 FCF（2026 年价）约 {steady:.1f} 亿，增量回报约 {steady / tot_gc:.0%}")
    q3_px = {"ag": 64.0, "sn": 51000.0, "zn": 3050.0, "pb": 1950.0, "cu": 13300.0}
    q3_rev = revenue({m: v / 4 for m, v in EXIST_VOL.items()}, q3_px) + OTHER_REV_H1_ANNUAL / 4 * 0.95
    q3_lost = 9.2 * 0.53 * (1 - SURCHARGE_RATE - 0.12)
    q3_ebitda = q3_rev * (1 - SURCHARGE_RATE) - EXIST_CASH_OPEX_2026 / 4 - q3_lost - 0.15
    q3_np = (q3_ebitda - EXIST_DA / 4 - NET_INT_2026 / 4) * (1 - EXIST_TAX) - 0.15
    print(f"2026Q3 估计：正常收入 {q3_rev:.1f} 亿，银漫当季产出约 47%，归母约 {q3_np:.1f} 亿（核对区间 2.5～5.5 亿）")
    h2 = h2_2026(SCEN["base"])
    print(f"2026H2 估计：收入 {h2['rev']:.1f}，归母约 {h2['ni_parent']:.1f}；全年归母约 {22.63 + h2['ni_parent']:.1f}，"
          f"扣非约 {18.16 + h2['ni_parent'] + 0.3:.1f}")
    for p in (0.75, 0.90, 1.10):
        print(f"V 不变时 P/V = {p:.2f} 对应价格 {vw * p:.2f}")


if __name__ == "__main__":
    main()
