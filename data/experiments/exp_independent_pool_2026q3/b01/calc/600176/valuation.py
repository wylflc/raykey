#!/usr/bin/env python3
"""中国巨石（600176）独立估值：OI-291 池内独立审计 b01（深度版）。

运行：python3 valuation.py        打印三情景 V、加权 V、P/V、8%/10% 敏感性、隐含回报与反向 DCF
      python3 valuation.py --json 额外打印 JSON 摘要（供登记文件核对）

金额单位亿元，每股元。价格日 2026-10-19，现价 33.72 元，总股本 40.0314 亿股（全部为 A 股）。
所有输入写在本脚本内，出处见同批 companies/600176_中国巨石.md 的「来源」。

方法：所有者收益 DCF（归母口径）。所有者收益 = 归母净利 + 税后净利息 + 折旧摊销
      − 资本开支（维护 + 已公告扩产）− 营运资本增量；显式期 2026Q4–2031，
      终值 = 2032 年正常化所有者收益 /(k − g)，其中再投资率 = g / 增量回报。
      权益价值 = 现值 + 调整后净现金（净负债为负）。
利润引擎：粗纱及制品「吨净利」× 销量 + 电子布「单米净利」×（电子布销量 + 0.15 × 外售电子纱万吨）+ 其他。
      单米净利 = (实现价/1.13 − 单米全成本 2.40) × (1 − 15%)，实现价为 7628 当量含税价。
"""
import json
import sys

PRICE = 33.72
SHARES = 40.0314
MKT_CAP = PRICE * SHARES
COE = 0.09

# ---------------------------------------------------------------- 1. 调整后净现金（2026-09-30）
CASH = 35.80              # 货币资金（2026Q3_report 第5页）；其中存放中国建材集团财务公司 6.50（2026H1_report 第86页，6月末）
OP_RESERVE = 10.0         # 经营备付，约 4% 年收入
DIV_PAID_OCT = 13.20      # 2026 年中期分红 13.20 亿元，2026-10-16 发放（dividend_20260821 第1页；三季报应付股利 13.36）
DEBT = {
    "短期借款": 45.30,
    "长期借款": 41.79,
    "应付债券": 14.99,
    "一年内到期的非流动负债": 15.99,
    "超短期融资券（其他流动负债 32.47 内，扣已背书票据约 6.5、预收增值税约 0.45，估）": 25.50,
    "租赁负债": 0.16,
    "长期应付款（中国建材集团资金拆借）": 2.95,
    "衍生金融负债（贵金属期权）": 0.26,
}
PROVISION = 0.61          # 预计负债：中复连众风险保障补偿（2026H1_report 第114-115页）
NET_CASH_ADJ = CASH - OP_RESERVE - DIV_PAID_OCT - sum(DEBT.values()) - PROVISION
NON_OPERATING = 0.0       # 联营（中材叶片 20.01% 等，账面 17.35）收益已含在利润「其他」中，不另加
INT_AT = 1.9              # 税后净利息/年：2026 前三季度利息支出 1.97 − 利息收入 0.33，年化 ×(1−15%)

# ---------------------------------------------------------------- 2. 单位经济（校准见第 3 节）
TAX = 0.15
C_E = 2.40                # 电子布单米全成本（不含税，含期间费用与利息分摊），元/米
YARN_K = 0.15             # 外售电子纱 1 万吨的利润 ≈ 0.15 亿米电子布的利润
ROV_ASP0, ROV_PI0 = 4720.0, 990.0   # 2026H1 粗纱及制品不含税均价（元/吨）与对应吨净利，用于收入估算
YARN_COST = 6300.0        # 电子纱不含税全成本（元/吨），用于收入估算
OTHER_REV = 6.0           # 风电与其他业务收入/年
NWC_RATE = 0.22           # 营运资本 / 年化收入


def pi_e(r):
    """电子布单米净利（元/米）；r 为巨石实现价（7628 当量，含税，元/米）。"""
    return (r / 1.13 - C_E) * (1 - TAX)


def rov_asp(pi_r):
    return ROV_ASP0 + (pi_r - ROV_PI0) / (1 - TAX)


def yarn_asp(pe):
    return YARN_COST + 1500.0 * pe / (1 - TAX)


def seg_np(rov_wt, pi_r, cloth_ym, yarn_wt, r, other):
    """归母净利（亿元）。rov_wt 万吨，pi_r 元/吨，cloth_ym 亿米，yarn_wt 万吨。"""
    return rov_wt * pi_r / 1e4 + (cloth_ym + YARN_K * yarn_wt) * pi_e(r) + other


def revenue(rov_wt, pi_r, cloth_ym, yarn_wt, r, other_rev):
    return (rov_wt * rov_asp(pi_r) / 1e4 + cloth_ym * r / 1.13
            + yarn_wt * yarn_asp(pi_e(r)) / 1e4 + other_rev)


# ---------------------------------------------------------------- 3. 校准：2026 年前三季度
# 季度，扣非归母，粗纱万吨，电子布亿米，外售电子纱万吨，市场 7628 季均价（含税），假设粗纱吨净利
CAL = [
    ("2026Q1", 12.76, 81.0, 2.80, 0.0, 5.15, 988),    # 申万一季报点评：粗纱约 81 万吨、吨净利约 988 元；电子布约 2.8 亿米
    ("2026Q2", 16.32, 89.04, 2.64, 1.0, 6.73, 950),   # 上半年粗纱 170.04 万吨、电子布 5.44 亿米（2026H1_report 第10页）
    ("2026Q3", 24.06, 88.0, 3.00, 2.5, 10.10, 950),   # 三季度量为估计；7628 三季度均价约 10.1（东财 2026-09-01 等）
]
OTHER_Q = 0.3             # 风电、联营等/季


def calibration():
    rows = []
    for q, np_, rov, cloth, yarn, mkt, pr in CAL:
        e_np = np_ - OTHER_Q - rov * pr / 1e4
        pe = e_np / (cloth + YARN_K * yarn)
        r = (pe / (1 - TAX) + C_E) * 1.13
        rows.append((q, np_, rov * pr / 1e4, e_np, pe, r, r / mkt))
    return rows


# ---------------------------------------------------------------- 4. 2026Q4 与情景
NP_9M = 53.46             # 2026 年前三季度归母净利（2026Q3_report 第1页）
REV_9M, REV_Q3 = 180.78, 69.19
Q4 = dict(rov=87.0, pr=900, cloth=3.15, yarn=2.5, other=0.3, accrual=-1.5,   # 四季度年终考核与研发计提
          da=7.0, growth=9.0)
YEARS = [2027, 2028, 2029, 2030, 2031]
T = {2027: 0.70, 2028: 1.70, 2029: 2.70, 2030: 3.70, 2031: 4.70}   # 距 2026-10-19 的年中折现时点
T_Q4, T_TV = 0.15, 5.20
DA = {2027: 30.0, 2028: 33.0, 2029: 35.0, 2030: 35.5, 2031: 36.0}
MAINT_RATIO = 0.8         # 显式期维护性资本开支 = 0.8 × 折旧摊销；终值期按再投资率处理
VOL_BASE = dict(rov={2027: 360, 2028: 375, 2029: 385, 2030: 393, 2031: 400},
                cloth={2027: 12.5, 2028: 16.0, 2029: 18.5, 2030: 19.0, 2031: 19.5},
                yarn={2027: 9, 2028: 7, 2029: 5, 2030: 5, 2031: 5})
VOL_BEAR = dict(rov={2027: 360, 2028: 370, 2029: 378, 2030: 384, 2031: 390},
                cloth={2027: 12.5, 2028: 15.0, 2029: 17.0, 2030: 17.5, 2031: 18.0},
                yarn={2027: 9, 2028: 7, 2029: 5, 2030: 5, 2031: 5})
SCEN = {
    "bear": dict(p=0.25, rq4=11.0, vol=VOL_BEAR,
                 R={2027: 9.8, 2028: 5.2, 2029: 3.9, 2030: 3.9, 2031: 3.9},
                 pr={2027: 750, 2028: 550, 2029: 600, 2030: 600, 2031: 600},
                 growth={2027: 45, 2028: 20, 2029: 8, 2030: 8, 2031: 8},
                 other=1.0, g=0.015, roic=0.07, r_mid=3.9, pr_mid=600),
    "base": dict(p=0.50, rq4=11.5, vol=VOL_BASE,
                 R={2027: 12.0, 2028: 8.5, 2029: 5.8, 2030: 4.6, 2031: 4.6},
                 pr={2027: 930, 2028: 900, 2029: 900, 2030: 900, 2031: 900},
                 growth={2027: 58, 2028: 30, 2029: 12, 2030: 12, 2031: 12},
                 other=1.2, g=0.020, roic=0.09, r_mid=4.6, pr_mid=900),
    "bull": dict(p=0.25, rq4=12.0, vol=VOL_BASE,
                 R={2027: 14.0, 2028: 13.0, 2029: 10.0, 2030: 7.0, 2031: 5.6},
                 pr={2027: 1100, 2028: 1250, 2029: 1250, 2030: 1250, 2031: 1250},
                 growth={2027: 58, 2028: 30, 2029: 12, 2030: 12, 2031: 12},
                 other=1.4, g=0.025, roic=0.12, r_mid=5.6, pr_mid=1250),
}
VOL_2026 = dict(rov=170.04 + 88.0 + 87.0, cloth=5.44 + 3.00 + 3.15, yarn=6.0)


def normalized_2026(s):
    """2026 年正常化归母净利：2026 年销量 × 周期中枢单位利润（含净利息，剔除汇兑与一次性项目）。"""
    return seg_np(VOL_2026["rov"], s["pr_mid"], VOL_2026["cloth"], VOL_2026["yarn"], s["r_mid"], s["other"])


def normalized_path(s):
    """逐年正常化归母净利（周期中枢单位利润 × 当年销量），用于增长路径与再投资核算。"""
    vol = s["vol"]
    path = {2026: normalized_2026(s)}
    for y in YEARS:
        path[y] = seg_np(vol["rov"][y], s["pr_mid"], vol["cloth"][y], vol["yarn"][y], s["r_mid"], s["other"])
    growth = {y: path[y] / path[y - 1] - 1 for y in YEARS}
    capex_growth = Q4["growth"] + sum(s["growth"][y] for y in YEARS)
    reinvest = capex_growth / sum(path[y] for y in YEARS)
    inc_return = (path[2031] - path[2026]) / capex_growth
    return dict(path=path, growth=growth, reinvest=reinvest, inc_return=inc_return)


def project(s):
    """返回逐年明细与现金流（不折现）。"""
    out = {}
    np_q4 = seg_np(Q4["rov"], Q4["pr"], Q4["cloth"], Q4["yarn"], s["rq4"], Q4["other"]) + Q4["accrual"]
    rev_q4 = revenue(Q4["rov"], Q4["pr"], Q4["cloth"], Q4["yarn"], s["rq4"], OTHER_REV / 4)
    nwc_prev = NWC_RATE * 4 * REV_Q3
    nwc_q4 = NWC_RATE * 4 * rev_q4
    capex_q4 = MAINT_RATIO * Q4["da"] + Q4["growth"]
    oe_q4 = np_q4 + INT_AT / 4 + Q4["da"] - capex_q4 - (nwc_q4 - nwc_prev)
    out["2026Q4"] = dict(np=np_q4, rev=rev_q4, da=Q4["da"], capex=capex_q4, dnwc=nwc_q4 - nwc_prev, oe=oe_q4)
    out["np_2026"] = NP_9M + np_q4
    nwc_prev = nwc_q4
    vol = s["vol"]
    for y in YEARS:
        npy = seg_np(vol["rov"][y], s["pr"][y], vol["cloth"][y], vol["yarn"][y], s["R"][y], s["other"])
        rev = revenue(vol["rov"][y], s["pr"][y], vol["cloth"][y], vol["yarn"][y], s["R"][y], OTHER_REV)
        nwc = NWC_RATE * rev
        capex = MAINT_RATIO * DA[y] + s["growth"][y]
        oe = npy + INT_AT + DA[y] - capex - (nwc - nwc_prev)
        out[y] = dict(np=npy, rev=rev, da=DA[y], capex=capex, dnwc=nwc - nwc_prev, oe=oe,
                      pi_e=pi_e(s["R"][y]), pi_r=s["pr"][y])
        nwc_prev = nwc
    np_t = out[2031]["np"] * (1 + s["g"]) + INT_AT
    out["oe_terminal"] = np_t * (1 - s["g"] / s["roic"])
    return out


def value(s, k=COE, net_cash=None, oe_override=None):
    net_cash = NET_CASH_ADJ if net_cash is None else net_cash
    pr = project(s) if oe_override is None else oe_override
    pv = pr["2026Q4"]["oe"] / (1 + k) ** T_Q4
    for y in YEARS:
        pv += pr[y]["oe"] / (1 + k) ** T[y]
    tv = pr["oe_terminal"] / (k - s["g"])
    pv_tv = tv / (1 + k) ** T_TV
    eq = pv + pv_tv + net_cash
    return dict(v=eq / SHARES, equity=eq, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / (pv + pv_tv))


def weighted(k=COE, scen=None):
    scen = SCEN if scen is None else scen
    return sum(sc["p"] * value(sc, k)["v"] for sc in scen.values())


def implied_irr(s):
    """基准所有者收益流（含终值与净现金）使现值等于现价的折现率。"""
    lo, hi = s["g"] + 0.002, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if value(s, mid)["equity"] > MKT_CAP:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf():
    """(a) 现价隐含：自 2026 年正常化所有者收益起步，10 年复合增速 g10（之后 2.5% 永续）；
    (b) 保留基准 2026Q4–2031 现金流，隐含 2032 年正常化归母净利。"""
    base = SCEN["base"]
    oe0 = (normalized_2026(base) + INT_AT) * (1 - base["g"] / base["roic"])
    target = MKT_CAP - NET_CASH_ADJ
    lo, hi = -0.10, 0.50
    for _ in range(200):
        g10 = (lo + hi) / 2
        pv, oe = 0.0, oe0
        for t in range(1, 11):
            oe *= 1 + g10
            pv += oe / (1 + COE) ** (t - 0.5)
        pv += oe * 1.025 / (COE - 0.025) / (1 + COE) ** 10
        if pv < target:
            lo = g10
        else:
            hi = g10
    g10 = (lo + hi) / 2
    pr = project(base)
    pv_exp = pr["2026Q4"]["oe"] / (1 + COE) ** T_Q4 + sum(pr[y]["oe"] / (1 + COE) ** T[y] for y in YEARS)
    need_tv = (target - pv_exp) * (1 + COE) ** T_TV
    oe_t = need_tv * (COE - base["g"])
    np_t = oe_t / (1 - base["g"] / base["roic"]) - INT_AT
    base_np_t = pr[2031]["np"] * (1 + base["g"])
    # (c) 稳态隐含：EV = NP×(1−g/ROIC)/(k−g)
    np_steady = target * (COE - base["g"]) / (1 - base["g"] / base["roic"]) - INT_AT
    return dict(oe0=oe0, g10=g10, np_2032_implied=np_t, np_2032_base=base_np_t, np_steady=np_steady)


# ---------------------------------------------------------------- 5. 证伪情景（触发后的独立 V）
def falsifier_values():
    b = SCEN["base"]
    res = {}
    # F1 景气延长：2028H1 7628 主流价仍 ≥ 10 元/米 → 2028–2030 实现价按牛市路径，中枢仍取基准
    s = dict(b, R={2027: 13.0, 2028: 12.0, 2029: 9.0, 2030: 6.0, 2031: 4.6})
    res["F1"] = weighted(scen={"bear": dict(SCEN["bear"], p=0.10), "base": dict(s, p=0.55),
                               "bull": dict(SCEN["bull"], p=0.35)})
    # F2 提前回落：2027-06-30 前 7628 主流价跌破 8 元/米或 2027Q2 归母 < 22 亿 → 2027–2028 按熊市路径
    s2 = dict(b, R={2027: 9.0, 2028: 5.2, 2029: 4.6, 2030: 4.6, 2031: 4.6})
    res["F2"] = weighted(scen={"bear": dict(SCEN["bear"], p=0.40), "base": dict(s2, p=0.50),
                               "bull": dict(SCEN["bull"], p=0.10)})
    # F3 粗纱中枢下移：2400tex 缠绕直接纱连续两季 < 3,300 元/吨或粗纱吨净利 < 650 元
    #    → 基准中枢 650 元/吨、牛市中枢 1,000 元/吨，概率 35/45/20
    s3 = dict(b, pr={2027: 800, 2028: 650, 2029: 650, 2030: 650, 2031: 650}, pr_mid=650, p=0.45)
    bull3 = dict(SCEN["bull"], pr={2027: 950, 2028: 1000, 2029: 1000, 2030: 1000, 2031: 1000}, pr_mid=1000, p=0.20)
    res["F3"] = weighted(scen={"bear": dict(SCEN["bear"], p=0.35), "base": s3, "bull": bull3})
    # F4 电子布中枢下移：2029 年 7628 连续两季 ≤ 4.0 元/米 → 基准中枢 3.9、牛市中枢 4.8，概率 35/45/20
    s4 = dict(b, R={2027: 12.0, 2028: 8.5, 2029: 4.4, 2030: 3.9, 2031: 3.9}, r_mid=3.9, p=0.45)
    bull4 = dict(SCEN["bull"], R={2027: 14.0, 2028: 13.0, 2029: 9.0, 2030: 5.5, 2031: 4.8}, r_mid=4.8, p=0.20)
    res["F4"] = weighted(scen={"bear": dict(SCEN["bear"], p=0.35), "base": s4, "bull": bull4})
    # F5 资本配置：2027 年购建长期资产 > 100 亿或新增粗纱扩产 ≥ 40 万吨 → 增量 30 亿资本开支、回报 6%
    s5 = dict(b, growth={2027: 78, 2028: 40, 2029: 12, 2030: 12, 2031: 12}, other=b["other"] + 0.6)
    res["F5"] = weighted(scen={"bear": dict(SCEN["bear"], growth={2027: 65, 2028: 30, 2029: 8, 2030: 8, 2031: 8}),
                               "base": s5, "bull": dict(SCEN["bull"], growth=s5["growth"], other=1.4 + 0.6)})
    return res


# ---------------------------------------------------------------- 6. 交叉验证
NP_TTM, EQ_PARENT = 60.63, 342.93          # TTM 归母（2025Q4 7.17 + 2026 前三季度 53.46）；9 月末归母权益
PRETAX_TTM = 65.33 + (41.50 - 32.32)       # 2026 前三季度利润总额 + 2025Q4 利润总额
NET_INT_TTM = 2.24                         # 2026 前三季度 1.64 + 2025Q4 约 0.6
HIST_PE = [28.4, 28.6, 15.7, 22.1, 14.3, 17.9, 28.9, 12.1, 8.3, 12.9, 18.6, 20.8]   # 2014–2025 年末
HIST_PB = [3.36, 2.89, 2.18, 3.82, 2.38, 2.44, 4.01, 3.23, 1.99, 1.37, 1.52, 2.20]
DPS_TTM = 0.52


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def cross_checks(r):
    ev = MKT_CAP - NET_CASH_ADJ
    ebit_ttm = PRETAX_TTM + NET_INT_TTM
    ebit_norm = (r["base"]["np_norm_2026"] + 1.3) / (1 - 0.16) + NET_INT_TTM   # 加少数股东约 1.3、税率约 16%
    np26 = r["base"]["proj"]["np_2026"]
    return dict(
        pe_ttm=MKT_CAP / NP_TTM, pb=MKT_CAP / EQ_PARENT, pe_2026e=MKT_CAP / np26,
        pe_norm=MKT_CAP / r["base"]["np_norm_2026"],
        pe_range=(min(HIST_PE), median(HIST_PE), max(HIST_PE)), pb_range=(min(HIST_PB), median(HIST_PB), max(HIST_PB)),
        v_pe_median=median(HIST_PE) * r["base"]["np_norm_2026"] / SHARES,
        v_pb_median=median(HIST_PB) * EQ_PARENT / SHARES,
        ev=ev, ev_ebit_ttm=ev / ebit_ttm, ev_ebit_norm=ev / ebit_norm,
        dy_ttm=DPS_TTM / PRICE, dy_2026e=0.45 * np26 / SHARES / PRICE,
    )


HIST_NPM_2016_2025 = [20.4, 24.8, 23.7, 20.3, 20.7, 30.6, 32.7, 20.5, 15.4, 17.4]   # 归母净利率 %，数据包第三节
FX_LOSS_AT_9M = 1.4       # 2026 前三季度汇兑损失约 1.65 亿（财务费用 3.39 − 利息 1.97 + 利息收入 0.33 − 其他约 0.1）税后
NONREC_9M = 0.32          # 2026 前三季度非经常性损益（2026Q3_report 第2页）


def decomposition():
    """2026E（基准）归母净利 vs 正常化：一次性、周期性与结构性拆分。"""
    b = SCEN["base"]
    pj = project(b)
    cal = calibration()
    rov_act = sum(c[2] for c in cal) + Q4["rov"] * Q4["pr"] / 1e4
    e_act = sum(c[3] for c in cal) + (Q4["cloth"] + YARN_K * Q4["yarn"]) * pi_e(b["rq4"])
    rov_norm = VOL_2026["rov"] * b["pr_mid"] / 1e4
    e_norm = (VOL_2026["cloth"] + YARN_K * VOL_2026["yarn"]) * pi_e(b["r_mid"])
    rev_norm = revenue(VOL_2026["rov"], b["pr_mid"], VOL_2026["cloth"], VOL_2026["yarn"], b["r_mid"], OTHER_REV)
    npm_norm = normalized_2026(b) / rev_norm
    npm_hist = median(HIST_NPM_2016_2025) / 100
    return dict(np_2026e=pj["np_2026"], np_norm=normalized_2026(b), one_off=NONREC_9M - FX_LOSS_AT_9M,
                cyc_e=e_act - e_norm, cyc_rov=rov_act - rov_norm, e_act=e_act, e_norm=e_norm,
                rov_act=rov_act, rov_norm=rov_norm, rev_norm=rev_norm, npm_norm=npm_norm, npm_hist=npm_hist,
                structural=(npm_norm - npm_hist) * rev_norm)


def results():
    out = {"net_cash_adj": NET_CASH_ADJ, "debt": sum(DEBT.values())}
    for name, s in SCEN.items():
        v = value(s)
        out[name] = dict(v=v["v"], p=s["p"], tv_share=v["tv_share"], np_norm_2026=normalized_2026(s),
                         v8=value(s, 0.08)["v"], v10=value(s, 0.10)["v"], proj=project(s))
    out["v_w"] = weighted()
    out["pv"] = PRICE / out["v_w"]
    out["v8"] = weighted(0.08)
    out["v10"] = weighted(0.10)
    out["irr"] = implied_irr(SCEN["base"])
    out["rev"] = reverse_dcf()
    out["fals"] = falsifier_values()
    return out


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    r = results()
    print("== 中国巨石 600176 独立估值（价格日 2026-10-19，现价 %.2f，股本 %.4f 亿股，市值 %.1f 亿）==" % (PRICE, SHARES, MKT_CAP))
    print("\n[1] 调整后净现金：现金 %.2f − 经营备付 %.1f − 10月已付中期分红 %.2f − 有息负债 %.2f − 预计负债 %.2f = %.2f 亿元（%.2f 元/股）"
          % (CASH, OP_RESERVE, DIV_PAID_OCT, r["debt"], PROVISION, NET_CASH_ADJ, NET_CASH_ADJ / SHARES))
    print("\n[2] 校准（电子布单米全成本 %.2f 元/米）：" % C_E)
    for q, np_, rov, e_np, pe, rr, lam in calibration():
        print("  %s 扣非 %.2f = 粗纱 %.2f + 电子布/纱 %.2f；隐含单米净利 %.2f 元，隐含实现价 %.2f 元/米（为市场均价的 %.0f%%）"
              % (q, np_, rov, e_np, pe, rr, lam * 100))
    print("\n[3] 2026 正常化归母净利（2026 年销量 × 周期中枢）：熊 %.1f / 基准 %.1f / 牛 %.1f 亿元"
          % (r["bear"]["np_norm_2026"], r["base"]["np_norm_2026"], r["bull"]["np_norm_2026"]))
    for name in ("bear", "base", "bull"):
        s = SCEN[name]
        print("    %s 中枢：7628 %.1f 元/米（单米净利 %.2f），粗纱吨净利 %d 元" % (name, s["r_mid"], pi_e(s["r_mid"]), s["pr_mid"]))
    d = decomposition()
    print("    拆分（基准）：2026E 归母 %.1f vs 正常化 %.1f；一次性 %+.1f（非经常 %+.2f、汇兑税后 −%.1f）；"
          "周期性 %+.1f（电子布/纱 %.1f→%.1f，粗纱 %.1f→%.1f）；结构性 %+.1f（正常化净利率 %.1f%% vs 2016–2025 中位 %.1f%%，正常化收入 %.0f）"
          % (d["np_2026e"], d["np_norm"], d["one_off"], NONREC_9M, FX_LOSS_AT_9M, d["cyc_e"] + d["cyc_rov"],
             d["e_act"], d["e_norm"], d["rov_act"], d["rov_norm"], d["structural"], d["npm_norm"] * 100,
             d["npm_hist"] * 100, d["rev_norm"]))
    print("\n[4] 情景明细（归母净利 / 所有者收益，亿元）：")
    for name in ("bear", "base", "bull"):
        pj = r[name]["proj"]
        line = "  %-4s 2026E 归母 %.1f（Q4 %.1f）" % (name, pj["np_2026"], pj["2026Q4"]["np"])
        for y in YEARS:
            line += " | %d 归母 %.1f OE %.1f" % (y, pj[y]["np"], pj[y]["oe"])
        line += " | 终值 OE %.1f" % pj["oe_terminal"]
        print(line)
    pjb = r["base"]["proj"]
    nb = normalized_path(SCEN["base"])
    print("  基准正常化归母净利（中枢价 × 当年销量）：" + "，".join("%d %.1f" % (y, nb["path"][y]) for y in [2026] + YEARS)
          + "；增速 " + "，".join("%d %+.1f%%" % (y, nb["growth"][y] * 100) for y in YEARS)
          + "；2026Q4–2031 扩产资本开支 / 正常化净利 = %.0f%%，增量回报 %.1f%%；终值期再投资率 %.0f%%（g %.1f%% ÷ 增量回报 %.0f%%）"
          % (nb["reinvest"] * 100, nb["inc_return"] * 100, SCEN["base"]["g"] / SCEN["base"]["roic"] * 100,
             SCEN["base"]["g"] * 100, SCEN["base"]["roic"] * 100))
    print("  基准逐年：收入 " + "，".join("%d %.0f" % (y, pjb[y]["rev"]) for y in YEARS)
          + "；资本开支 " + "，".join("%d %.0f" % (y, pjb[y]["capex"]) for y in YEARS)
          + "；营运资本增量 " + "，".join("%d %.1f" % (y, pjb[y]["dnwc"]) for y in YEARS))
    print("\n[5] 独立 V（股权成本 9%）：")
    for name in ("bear", "base", "bull"):
        print("  %-4s V = %.2f 元/股（概率 %.0f%%，终值占比 %.0f%%；8%% → %.2f，10%% → %.2f）"
              % (name, r[name]["v"], r[name]["p"] * 100, r[name]["tv_share"] * 100, r[name]["v8"], r[name]["v10"]))
    print("  加权 V = %.2f 元/股；P/V = %.2f → %s" % (r["v_w"], r["pv"], band(r["pv"])))
    print("  股权成本敏感性：8%% → 加权 V %.2f（P/V %.2f）；10%% → 加权 V %.2f（P/V %.2f）"
          % (r["v8"], PRICE / r["v8"], r["v10"], PRICE / r["v10"]))
    print("  V 不变时进入各档的价格：明显低估 ≤ %.2f；温和低估 %.2f–%.2f；大致合理 %.2f–%.2f；偏贵 > %.2f"
          % (0.75 * r["v_w"], 0.75 * r["v_w"], 0.90 * r["v_w"], 0.90 * r["v_w"], 1.10 * r["v_w"], 1.10 * r["v_w"]))
    print("\n[6] 现价隐含回报（基准现金流含终值与净现金）：%.2f%%" % (r["irr"] * 100))
    rv = r["rev"]
    print("[7] 反向 DCF：自 2026 正常化所有者收益 %.1f 亿起步，现价隐含 10 年复合增速 %.1f%%（之后 2.5%%）；"
          % (rv["oe0"], rv["g10"] * 100))
    print("    保留基准 2026Q4–2031 现金流，现价隐含 2032 年正常化归母净利 %.0f 亿元（基准 %.0f 亿元）；稳态口径隐含归母净利 %.0f 亿元"
          % (rv["np_2032_implied"], rv["np_2032_base"], rv["np_steady"]))
    print("\n[8] 证伪触发后的加权 V：" + "；".join("%s %.2f" % (k_, v_) for k_, v_ in r["fals"].items()))
    c = cross_checks(r)
    print("\n[9] 交叉验证：PE(TTM) %.1f，PB %.2f，PE(2026E 基准 %.1f 亿) %.1f，PE(2026 正常化) %.1f；"
          % (c["pe_ttm"], c["pb"], r["base"]["proj"]["np_2026"], c["pe_2026e"], c["pe_norm"]))
    print("    历史年末 PE %.1f–%.1f（中位 %.1f），PB %.2f–%.2f（中位 %.2f）；中位 PE × 正常化净利 → %.2f 元，中位 PB × 归母权益 → %.2f 元"
          % (c["pe_range"][0], c["pe_range"][2], c["pe_range"][1], c["pb_range"][0], c["pb_range"][2], c["pb_range"][1],
             c["v_pe_median"], c["v_pb_median"]))
    print("    EV %.0f 亿：EV/EBIT(TTM) %.1f，EV/EBIT(正常化) %.1f；股息率 TTM %.2f%%，2026E（45%% 派息）%.2f%%；无回购"
          % (c["ev"], c["ev_ebit_ttm"], c["ev_ebit_norm"], c["dy_ttm"] * 100, c["dy_2026e"] * 100))
    if "--json" in sys.argv:
        print(json.dumps({
            "v_bear": round(r["bear"]["v"], 2), "v_base": round(r["base"]["v"], 2), "v_bull": round(r["bull"]["v"], 2),
            "v_weighted": round(r["v_w"], 2), "pv": round(r["pv"], 2),
            "v_at_coe_8": round(r["v8"], 2), "v_at_coe_10": round(r["v10"], 2), "implied_irr": round(r["irr"], 4),
            "np_norm_2026": {k_: round(r[k_]["np_norm_2026"], 1) for k_ in ("bear", "base", "bull")},
            "net_cash_adj_yi": round(NET_CASH_ADJ, 2),
            "falsifiers": {k_: round(v_, 2) for k_, v_ in r["fals"].items()},
        }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
