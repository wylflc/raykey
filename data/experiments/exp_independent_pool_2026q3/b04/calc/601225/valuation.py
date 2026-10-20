# -*- coding: utf-8 -*-
"""陕西煤业（601225）独立估值，OI-291 b04，价格日 2026-10-19。

运行：python3 valuation.py
打印三情景 V（有杠杆与无杠杆两种口径）、加权 V、P/V、股权成本 8%/10% 下的 V、隐含回报、反向 DCF 与证伪条件触发后的 V。
单位：金额亿元；价格与 V 元/股；煤价元/吨。自产煤售价为公司披露口径（不含税、不含“一票制”运费）。
页码指 PDF 物理页，见 raw/601225/txt/ 下逐页文本。网络事实见正文“来源”。
"""

# ============ 快照 ============
PRICE = 28.19                 # 2026-10-19 收盘（brief.md）
SHARES = 96.95                # 亿股；无回购专户，无拟注销股份（2026H1_report 第 41-42 页）
COE = 0.09
INT_DISC = 0.09               # 有杠杆口径：有息负债税后利息按 9% 折现（framework 三法互校第 2 条）
P_W = {"bear": 0.25, "base": 0.50, "bull": 0.25}

# ============ 一、煤价映射：秦港 5500 现货（含税）→ 公司自产煤售价 ============
# 2025 秦港 5500 成交均价约 703，同比 -18.4%；自产煤售价 2025 年 443.78、2024 年 532.03
# （2025_annual_report 第 12、19 页）。斜率约 0.56：约四成销量执行长协，长协价随现货只小幅浮动
# （2026 年 10 月秦港 5500 长协 717、年内均值 694，现货已破 1000）。
QHD24, PS24 = 703.0 / (1 - 0.184), 532.03
QHD25, PS25 = 703.0, 443.78
B_MAP = (PS24 - PS25) / (QHD24 - QHD25)
A_MAP = PS25 - B_MAP * QHD25

def p_self(qhd):
    """长期秦港 5500 现货 → 自产煤售价"""
    return A_MAP + B_MAP * qhd

# ============ 二、吨煤模型（以 2025 年报全年为锚，2026H1 回测） ============
T_PRICE = 0.122               # 吨煤相关税费/售价：2025 12.1%、2026H1 12.4%（2025_annual_report 第 16 页；2026H1_report 第 14 页）
TAX = 0.18                    # 煤矿子公司所得税：多数 15%（西部大开发，至 2030 年），张家峁等 25%（2026H1_report 第 89 页）
MINOR = 0.37                  # 增量煤炭利润少数股东占比：红柳林/柠条塔 49%，小保当/张家峁 45%，黄陵二号 46%（2026H1_report 第 177-179 页）
F_AT = (1 - TAX) * (1 - MINOR)
PW_OFFSET = 0.04              # 煤价每涨 1 元/吨，电力归母净利约减 0.04 亿（2026H1 度电售价 -28.01、完全成本 -12.35 元/MWh）
V25 = 1.5984777               # 2025 自产煤销量，亿吨（2025_annual_report 第 19 页）
C0_25 = 288.58 - (6.28 / 0.1046 - 6.28)        # 2025 原选煤完全成本 288.58 扣相关税费 53.76 → 234.82
C0_H125 = (282.84 - 2.84) - 7.24 / 0.1399      # 2025H1 → 228.25（2026H1_report 第 14 页倒推）
C0_H126 = 282.84 - (7.24 / 0.1399 + 7.24)      # 2026H1 → 223.85
KF25 = 153.45                 # 2025 扣非归母（2025_annual_report 第 8-9 页，非经常性损益 141,950.98 万）
# 2025 计入扣非的非经营投资收益：盐湖 4.418、彤程 0.175、金力永磁 0.128、理想晶延 0.017、启创 -0.076、
# 启明 0.621（2025_annual_report 第 153-157 页），交易性金融资产持有收益 0.529、其他权益工具股利 0.247、
# 其他非流动金融资产收益 0.048（第 200 页）
NONOP25 = 4.418 + 0.175 + 0.128 + 0.017 - 0.076 + 0.621 + 0.529 + 0.247 + 0.048
OP25 = KF25 - NONOP25         # 2025 经营口径归母净利（含净利息）

def margin_at(P, C0):
    """每吨自产外销煤对归母净利的贡献（元/吨）"""
    return (P * (1 - T_PRICE) - C0) * F_AT

K25 = OP25 - V25 * margin_at(PS25, C0_25)      # 电力、经营性联营、贸易、其他、净利息与未分摊费用（归母）

def np_op(P, V, C0, K):
    """全年经营口径归母净利（含净利息，不含非经营投资收益与一次性项目）"""
    return K + V * margin_at(P, C0) - PW_OFFSET * (P - PS25)

# 2026H1 回测：扣非 97.36 − 盐湖权益法 2.364 − 彤程 1.823 − 持股分红 0.373（2026H1_report 第 7、120-122、160-162 页）
OP_H126 = 97.36 - (2.364 + 1.823 + 0.373)
CHECK_H126 = np_op(477.13, 2 * 0.8342630, C0_H126, K25)
# 2026 全年量：H1 8342.63 万吨；Q3 = 1-8 月 11051 + 9 月 1340 − H1 = 4048.4；Q4 取 2025Q4 4046.5 × 1.03
V26 = (8342.63 + 4048.4 + 4046.5 * 1.03) / 1e4
C0_26 = C0_25 * C0_H126 / C0_H125
SEASONAL_H2 = 7.7             # 2025 下半年扣非较按售价推算少 7.7 亿（年末计提集中），用于半年拆分

# ============ 三、资产负债调整（2026-06-30，归母口径） ============
CASH = 431.5513 - 100.1477    # 货币资金 − 受限 100.15（复垦基金 98.30 等）= 331.40（第 45、90-91 页）
DEBT = 10.5965 + 239.7304 + 14.4055 + 4.3306 + 1.3955   # 短借、长借、一年内到期长借、租赁负债（第 46、150-153 页）
DEBT_LIKE = 49.1576 + 1.2403 + 0.7074 + 0.0998 + 0.1226 # 小保当矿权价款、一年内到期长期应付款、柠条塔搬迁补偿、其他、应付股利（第 148、153 页）
DIV_DECL = 5.6231             # 2026 中期分红，10-22 除息（dividend_20261015_463260 第 2 页）
BUFFER = 40.0                 # 经营备付，约营收 2.5%
# 少数股东对净金融资产的要求权：四大非全资矿净流动资产 × 85% × 少数比例（第 180 页）+ 张家峁、建新、彬长子矿估计
MI_CASH_CLAIM = (0.49 * 0.85 * (150.2558 - 24.8817) + 0.45 * 0.85 * (127.6990 - 27.8352)
                 + 0.49 * 0.85 * (101.8015 - 15.4150) + 0.46 * 0.85 * (65.1596 - 8.8829)
                 + 0.45 * 40.0 + 0.49 * 8.0 + 5.0)
MI_DEBT_SHARE = 55.0 + 0.45 * 7.90625          # 电力项目（51% 控股电厂居多）少数股东分担借款 + 小保当借款 45%
MI_DEBTLIKE_SHARE = 0.45 * 49.1576             # 小保当矿权价款 45%
CASH_P = CASH - MI_CASH_CLAIM
DEBT_P = DEBT - MI_DEBT_SHARE
DEBTLIKE_P = DEBT_LIKE - MI_DEBTLIKE_SHARE
NET_CASH_ADJ = CASH_P - DEBT_P - DEBTLIKE_P - DIV_DECL - BUFFER   # 无杠杆口径经调整净现金（json 填此数）
OTHER_ADJ_LEV = CASH_P - DEBTLIKE_P - DIV_DECL - BUFFER            # 有杠杆口径的“现金与其他调整项”
RATE = 0.029                  # 实际平均利率：2026H1 费用化利息 2.61 + 资本化 1.39 亿，对平均有息负债约 263 亿
TAX_INT = 0.22                # 电力子公司多为 25%，陕西电厂 15%
PV_INT = DEBT_P * RATE * (1 - TAX_INT) / INT_DISC
# 模型净利含净利息；经营所有者收益加回归母税后净利息（2026H1 利息费用 2.6117、利息收入 1.6837，第 50 页）
INT_EXP_P = 2 * 2.6117 * (DEBT_P / DEBT) * (1 - TAX_INT)
INT_INC_P = 2 * 1.6837 * (CASH_P / CASH) * (1 - 0.18)
NET_INT_ADDBACK = INT_EXP_P - INT_INC_P
RP_DEPOSIT = 70.4981          # 存放陕煤集团财务公司（第 35-36、90 页）

# ============ 四、非经营资产（价格取 2026-10-19 收盘，腾讯行情） ============
NONOP = {
    "盐湖股份约1.483亿股×23.00": 1.4828 * 23.00,   # 2025 末 5.03%（2.66 亿股）；H1 账面减少 24.92/56.25 → 出售约 44%（推算，待核）
    "彤程新材（账面）": 8.3389,
    "长江电力约0.4015亿股×29.54": 0.4015 * 29.54,   # 账面 10.58 亿（第 18 页）倒推股数
    "南网储能（账面）": 5.8156,
    "天玛智控（账面）": 0.2112,
    "货币基金": 0.1820,
    "扬州启创/启明、理想晶延、上海擎昆×0.8": 0.8 * (14.0635 + 4.4995 + 3.7673 + 0.2791),
    "其他非流动金融资产×0.8": 0.8 * 11.2833,
    "其他权益工具投资×0.7": 0.7 * 16.3535,
}
NONOP_TOTAL = sum(NONOP.values())

# ============ 五、2026 下半年（已过约 3.6 个月）的实际估计 ============
QHD_Q3, QHD_Q4 = 870.0, 970.0   # 现货 7/24 826、8/10 854、10/10 1003、10/13 1013；华泰判断 Q4 中枢 >900
LAG = 15.0                      # 月度定价滞后约半月
P_Q3 = p_self(QHD_Q3) - LAG
P_Q4 = p_self(QHD_Q4) - LAG
P_H2_26 = 0.5 * (P_Q3 + P_Q4)
P_NOW = P_Q4                    # 当前（2026Q4）售价水平，用于 2027-2028 余温

def h2_2026(P):
    return np_op(P, V26, C0_26, K25) / 2 - SEASONAL_H2 / 2

# ============ 六、情景 ============
SCEN = {
    "bear": dict(qhd=640, fade=(0.25, 0.0), price_g=0.000, cost_g=0.020,
                 vol_g=(0.0, -0.01, -0.01, -0.01, -0.01), dK=(3.5, 3.5, 3.5, 0, 0),
                 reinv=(0.15, 0.15, 0.15, 0.05, 0.05), g_t=-0.015, roic_t=0.10,
                 tax_hit_2031=0.094, nonop_mult=0.85, rp_haircut=0.10),
    "base": dict(qhd=760, fade=(0.40, 0.15), price_g=0.015, cost_g=0.015,
                 vol_g=(0.01, 0.005, 0.0, 0.0, 0.0), dK=(2.8, 2.8, 2.8, 0, 0),
                 reinv=(0.18, 0.18, 0.18, 0.08, 0.08), g_t=0.000, roic_t=0.12,
                 tax_hit_2031=0.047, nonop_mult=1.00, rp_haircut=0.0),
    "bull": dict(qhd=880, fade=(0.50, 0.25), price_g=0.015, cost_g=0.015,
                 vol_g=(0.02, 0.015, 0.01, 0.01, 0.005), dK=(2.0, 2.0, 2.0, 0, 0),
                 reinv=(0.20, 0.20, 0.20, 0.10, 0.10), g_t=0.015, roic_t=0.15,
                 tax_hit_2031=0.0, nonop_mult=1.05, rp_haircut=0.0),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
T_YRS = [0.70 + i for i in range(5)]     # 2026-10-19 至各年年中

def path(s, qhd=None, c0_shift=0.0, vol_shift=0.0, reinv_add=0.0, fade=True, tax_hit=None):
    sc = SCEN[s]
    q = sc["qhd"] if qhd is None else qhd
    P_norm = p_self(q)
    np26 = np_op(P_norm, V26, C0_26 + c0_shift, K25)
    rows = []
    V, C0, K, Pn = V26 * (1 + vol_shift), C0_26 + c0_shift, K25, P_norm
    th = sc["tax_hit_2031"] if tax_hit is None else tax_hit
    for i, y in enumerate(YEARS):
        Pn *= 1 + sc["price_g"]
        C0 *= 1 + sc["cost_g"]
        V *= 1 + sc["vol_g"][i]
        K += sc["dK"][i]
        f = (sc["fade"][0] if i == 0 else sc["fade"][1] if i == 1 else 0.0) if fade else 0.0
        P = Pn + f * max(P_NOW - P_norm, 0.0)
        npy = np_op(P, V, C0, K)
        if y == 2031:
            npy *= 1 - th
        pre = npy + NET_INT_ADDBACK
        r = sc["reinv"][i] + reinv_add
        rows.append(dict(year=y, P=P, V=V, C0=C0, K=K, np=npy, pre=pre, oe=pre * (1 - r), reinv=r))
    return np26, P_norm, rows

def value(s, k=COE, levered=True, qhd=None, c0_shift=0.0, vol_shift=0.0, reinv_add=0.0, g_t=None,
          fade=True, tax_hit=None, reinv_t_add=0.0):
    sc = SCEN[s]
    np26, P_norm, rows = path(s, qhd, c0_shift, vol_shift, reinv_add, fade, tax_hit)
    g = sc["g_t"] if g_t is None else g_t
    pv_rows = sum(r["oe"] / (1 + k) ** t for r, t in zip(rows, T_YRS))
    reinv_t = max(g, 0.0) / sc["roic_t"] + reinv_t_add
    oe_t = rows[-1]["pre"] * (1 + g) * (1 - reinv_t)
    pv_tv = oe_t / (k - g) / (1 + k) ** T_YRS[-1]
    h2_norm = h2_2026(P_norm) + NET_INT_ADDBACK / 2
    h2_excess = h2_2026(P_H2_26) - h2_2026(P_norm)
    pv_h2 = h2_norm * (1 - sc["reinv"][0] - reinv_add) + h2_excess
    ev_op = pv_rows + pv_tv + pv_h2
    nonop = NONOP_TOTAL * sc["nonop_mult"]
    hair = sc["rp_haircut"] * RP_DEPOSIT * CASH_P / CASH
    fin = (OTHER_ADJ_LEV - PV_INT) if levered else NET_CASH_ADJ
    eq = ev_op + fin + nonop - hair
    return dict(v=eq / SHARES, eq=eq, ev_op=ev_op, pv_tv=pv_tv, tv_share=pv_tv / ev_op, np26=np26,
                P_norm=P_norm, rows=rows, h2_excess=h2_excess, pv_h2=pv_h2, fin=fin, nonop=nonop)

def weighted(weights=None, **kw):
    w = P_W if weights is None else weights
    return sum(w[s] * value(s, **kw)["v"] for s in w)

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

def implied_10y_growth(k=COE, reinv=0.10, g_t=0.0):
    """反向 DCF：自 2026 正常化（基准）经营口径归母起，10 年复合增速（再投资率固定 10%，增长主要来自价格），其后零增长；有杠杆口径"""
    base26 = value("base")["np26"] + NET_INT_ADDBACK
    def v_of(g):
        pv, x = 0.0, base26
        for i in range(10):
            x *= 1 + g
            pv += x * (1 - reinv) / (1 + k) ** (0.70 + i)
        tv = x * (1 + g_t) / (k - g_t) / (1 + k) ** 9.70
        h2 = h2_2026(P_H2_26) + NET_INT_ADDBACK / 2
        eq = pv + tv + h2 + OTHER_ADJ_LEV - PV_INT + NONOP_TOTAL
        return eq / SHARES
    return solve(v_of, -0.05, 0.15, PRICE)

def implied_perpetual_growth(k=COE):
    """反向 DCF：基准路径不变，现价隐含的永续增速（再投资 = g/12%）"""
    return solve(lambda g: value("base", k=k, g_t=g)["v"], -0.05, 0.085, PRICE)

FALSIFIERS = {
    "F1 2027 秦港5500现货年均<700且自产煤售价<450（2028-04-30）": dict(weights={"bear": 0.5, "base": 0.4, "bull": 0.1}),
    "F2 2027 秦港5500现货年均>=880且自产煤售价>=540（2028-04-30）": dict(weights={"bear": 0.1, "base": 0.4, "bull": 0.5}),
    "F3 2026或2027原选煤完全成本>305元/吨（2025年288.58）": dict(c0_shift=15.0),
    "F4 2026年度分红<归母50%或以PB>2收购控股股东资产>100亿（2027-04-30）": dict(reinv_add=0.10, reinv_t_add=0.05),
    "F5 2027 自产煤销量<1.58亿吨（2026E 1.656）": dict(vol_shift=-0.05),
}

def falsifier_v(kw):
    kw = dict(kw)
    w = kw.pop("weights", None)
    return weighted(weights=w, **kw)

def quarter_estimate(P, vol_yi_t):
    """单季经营归母估计（不含季节性计提）：按全年公式折季"""
    return np_op(P, 4 * vol_yi_t, C0_26, K25) / 4

if __name__ == "__main__":
    print("== 校准 ==")
    print(f"映射：自产煤售价 = {A_MAP:.1f} + {B_MAP:.3f} × 秦港5500")
    print(f"2025 经营归母 {OP25:.2f}；其他板块合计 K25 {K25:.2f}；不含税费完全成本 2025 {C0_25:.2f}、2026E {C0_26:.2f}；2026E 自产煤销量 {V26:.4f} 亿吨")
    print(f"2026H1 回测（年化）：实际 {2*OP_H126:.1f}，模型 {CHECK_H126:.1f}")
    print(f"2026 下半年：Q3 售价 {P_Q3:.1f}、Q4 {P_Q4:.1f}；H2 经营归母 {h2_2026(P_H2_26):.1f}；"
          f"Q3 经营归母约 {quarter_estimate(P_Q3, 0.40484):.1f}（另非经营投资收益约 1）")
    fy26 = 112.72 + h2_2026(P_H2_26) + 2.3
    print(f"2026E 归母约 {fy26:.1f}（含 H1 盐湖处置约 15.4）；扣非约 {97.36 + h2_2026(P_H2_26) + 2.3:.1f}")
    print("== 资产负债（归母） ==")
    print(f"现金 {CASH:.2f}；有息负债 {DEBT:.2f}；类债务 {DEBT_LIKE:.2f}；少数股东要求权：现金 {MI_CASH_CLAIM:.1f}、有息 {MI_DEBT_SHARE:.1f}、类债务 {MI_DEBTLIKE_SHARE:.1f}")
    print(f"归母现金 {CASH_P:.1f}、有息 {DEBT_P:.1f}、类债务 {DEBTLIKE_P:.1f}；无杠杆经调整净现金 {NET_CASH_ADJ:.1f}")
    print(f"有杠杆：现金与其他调整 {OTHER_ADJ_LEV:.1f}；税后利息现值 {PV_INT:.1f}（{DEBT_P:.1f}×{RATE:.3f}×{1-TAX_INT:.2f}/{INT_DISC}）；净利息加回 {NET_INT_ADDBACK:.2f}")
    print(f"非经营资产合计 {NONOP_TOTAL:.1f}：" + "；".join(f"{k} {v:.1f}" for k, v in NONOP.items()))
    print("== 情景（V 为有杠杆口径，括号内为无杠杆） ==")
    for s in ("bear", "base", "bull"):
        rl, ru = value(s), value(s, levered=False)
        print(f"{s} p={P_W[s]}: 长期秦港5500 {SCEN[s]['qhd']} → 自产煤 {rl['P_norm']:.1f}；2026 正常化归母 {rl['np26']:.1f}；"
              f"V {rl['v']:.2f}（{ru['v']:.2f}）；终值占经营价值 {rl['tv_share']:.0%}；H2 超额 {rl['h2_excess']:.1f}")
        prev = rl["np26"] + NET_INT_ADDBACK
        prev_oe = prev * (1 - SCEN[s]["reinv"][0])
        for r in rl["rows"]:
            print(f"   {r['year']} 售价 {r['P']:.1f} 量 {r['V']:.3f} C0 {r['C0']:.1f} K {r['K']:.1f} 归母 {r['np']:.1f} "
                  f"经营口径 {r['pre']:.1f} 再投资 {r['reinv']:.0%} OE {r['oe']:.1f}（OE 同比 {r['oe']/prev_oe-1:+.1%}）")
            prev_oe = r["oe"]
    vw, vwu = weighted(), weighted(levered=False)
    print(f"加权 V（有杠杆）{vw:.2f}，P/V {PRICE/vw:.3f}；加权 V（无杠杆）{vwu:.2f}，P/V {PRICE/vwu:.3f}")
    v8, v10 = weighted(k=0.08), weighted(k=0.10)
    print(f"COE 8%：{v8:.2f}（P/V {PRICE/v8:.3f}）；COE 10%：{v10:.2f}（P/V {PRICE/v10:.3f}）；税后利息现值固定按 9%")
    irr = solve(lambda k: value("base", k=k)["v"], 0.03, 0.20, PRICE)
    print(f"现价隐含回报（基准，有杠杆）{irr:.4f}；无杠杆 {solve(lambda k: value('base', k=k, levered=False)['v'], 0.03, 0.20, PRICE):.4f}")
    q_imp = solve(lambda q: value("base", qhd=q)["v"], 500, 1400, PRICE)
    print(f"反向 DCF：现价隐含长期秦港5500 {q_imp:.0f}（自产煤 {p_self(q_imp):.0f}）；"
          f"隐含永续增速 {implied_perpetual_growth():.4f}；隐含 10 年复合增速（其后 0%）{implied_10y_growth():.4f}")
    print(f"敏感性：无 2027-28 余温 {weighted(fade=False):.2f}；基准终值增速 +1% → 基准 V {value('base', g_t=0.01)['v']:.2f}；"
          f"西部大开发不延续（基准）{value('base', tax_hit=0.094)['v']:.2f}")
    alt = (CASH * 0.68 - CASH_P) / SHARES
    print(f"敏感性：少数股东现金要求权改按权益比例（归母现金 68%）→ V +{alt:.2f}")
    print("== 交叉验证 ==")
    mcap = PRICE * SHARES
    fy26 = 112.72 + h2_2026(P_H2_26) + 2.3
    dps26 = 0.55 * fy26 / SHARES
    print(f"市值 {mcap:.1f}；过去 12 个月股息 0.967 元，股息率 {0.967/PRICE:.2%}；2026E 每股分红约 {dps26:.2f}（按归母 55%），股息率 {dps26/PRICE:.2%}；无回购")
    print(f"PE：2026E {mcap/fy26:.1f}×；基准正常化 {mcap/value('base')['np26']:.1f}×；TTM 13.4×；PB 2.70（历史 1.2-2.5）")
    ev_p = mcap - NONOP_TOTAL - NET_CASH_ADJ
    ebit_n = (value('base')['np26'] + NET_INT_ADDBACK) / (1 - TAX)
    ebit_26 = (97.36 + h2_2026(P_H2_26) + 2.3 - 4.56 - 2.3 + NET_INT_ADDBACK) / (1 - TAX)
    print(f"归母 EV {ev_p:.1f}；EV/EBIT（基准正常化）{ev_p/ebit_n:.1f}×，（2026E）{ev_p/ebit_26:.1f}×")
    print("== 证伪条件触发后的加权 V（有杠杆） ==")
    for name, kw in FALSIFIERS.items():
        print(f"{name}: {falsifier_v(kw):.2f}")
    print("== 分档价格（V 不变） ==")
    print(f"<= {0.75*vw:.2f} 明显低估；{0.75*vw:.2f}-{0.90*vw:.2f} 温和低估；{0.90*vw:.2f}-{1.10*vw:.2f} 大致合理；> {1.10*vw:.2f} 偏贵")
