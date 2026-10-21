#!/usr/bin/env python3
"""长江电力（600900）独立估值：OI-291 b15 深度版。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。价格日 2026-10-20，资产负债表取 2026-06-30（2026 中报）。
口径：所有者收益 DCF（归母、无杠杆经营口径，参股公司与金融资产作非经营资产单列，权益法收益不进经营流），
经调整净负债为正，按框架有杠杆口径：股权 = 经营所有者收益现值 − 净负债税后利息永续现值 + 非经营资产 − 类债务；
另列无杠杆口径（全额扣净负债）作对照。
"""
from datetime import date

PRICE = 29.69
SHARES = 244.6822          # 亿股，腾讯行情 = 资产负债表股本；无回购专户、无拟注销股份
COE = 0.09
VAL_DATE = date(2026, 10, 20)

# ---------- 1. 历史数据（公告原文） ----------
# 2025 年报：利润表第 84-85 页；电量电价第 18 页；发电量第 13 页；现金流补充资料第 193 页
G_2025 = 3071.94                    # 境内六站发电量，亿千瓦时
HYDRO_REV_2025 = 756.62             # 境内水电收入（不含税）
P_2025 = HYDRO_REV_2025 / G_2025    # 元/千瓦时（发电量口径，不含税）
EBIT_2025 = (417.40 + 93.71 - 49.59 - 16.77 + 0.26 + 15.05 - 0.20 + 0.005)
# = 利润总额 + 财务费用 − 投资收益 − 公允价值变动 + 信用/资产减值 − 其他收益 + 资产处置损失；营业外收支留在经营口径
DA_2025 = 190.89 + 1.14 + 3.05 + 0.22

# 2026 中报：利润表第 50-51 页；税金及附加第 154 页；现金流补充资料第 160-161 页
EBIT_H1_26 = 181.09 + 42.01 - 24.76 - 6.38 + 0.105 + 0.0025 - 0.08 + 0.03
EBIT_H1_25 = 155.56 + 48.63 - 25.89 + 0.15 + 0.043 - 0.069 + 0.012
EBIT_H2_25 = EBIT_2025 - EBIT_H1_25
DA_H1_26 = 92.32 + 0.59 + 1.57 + 0.10
WATER_TAX_H1_26 = 9.0036
VAT_SURCH_H1_26 = 2.3578 + 1.2322 + 0.8209   # 城建税 + 教育费附加 + 地方教育附加

# 发电量（2026-10-12 三季度发电量公告；2025 年报）
G_H1_26 = 1327.44
G_9M_26 = 2250.58
G_9M_25 = G_9M_26 / (1 - 0.0428)
G_Q3_26 = 923.14
G_Q3_25 = G_Q3_26 / (1 - 0.1489)
G_H1_25 = G_9M_25 - G_Q3_25
G_Q4_25 = G_2025 - G_9M_25
G_Q4_26E = 700.0                    # 假设：介于常年四季度与 2025 秋汛偏丰之间
G_2026E = G_9M_26 + G_Q4_26E
G_H2_25 = G_2025 - G_H1_25
G_H2_26E = G_Q3_26 + G_Q4_26E

# 变动成本：水资源税 + 增值税附加（中报实际）+ 库区基金等其他按电量计提的规费（假设 0.006）
V_COST = (WATER_TAX_H1_26 + VAT_SURCH_H1_26) / G_H1_26 + 0.006
MARGIN_KWH = P_2025 - V_COST

TAX = 0.19            # 经营税前利润有效税率：2025 18.3%、2026H1 19.4%（扣除免税的权益法收益后）
MINORITY = 0.016      # 少数股东损益占比：2025 1.3%、2026H1 1.8%

# ---------- 2. 2026 年估计与三季度推算 ----------
TARIFF_H2_26 = -0.01  # 上半年电价与上年基本持平（业绩会），下半年按 −1% 估
EBIT_H2_26E = (EBIT_H2_25 - (G_H2_25 - G_H2_26E) * MARGIN_KWH
               + G_H2_26E * P_2025 * TARIFF_H2_26 + 1.5)   # +1.5：折旧同比减少
EBIT_2026E = EBIT_H1_26 + EBIT_H2_26E
P_2026 = P_2025 * (1 - 0.005)
FIN_2026E = 42.01 + 41.5
EQ_2026E = 22.96 + 22.0
OTHINV_2026E = (24.76 - 22.96) + 1.6
FV_2026E = 6.38
pretax_26 = EBIT_2026E - FIN_2026E + EQ_2026E + OTHINV_2026E + FV_2026E
np_26 = pretax_26 - TAX * (pretax_26 - EQ_2026E)
PARENT_NP_2026E = np_26 * (1 - MINORITY)
PARENT_NP_2026E_RECURRING = PARENT_NP_2026E - FV_2026E * 0.75 * (1 - MINORITY)
Q3_25_PARENT = 151.37
Q3_26E_PARENT = (Q3_25_PARENT
                 - ((G_Q3_25 - G_Q3_26) * MARGIN_KWH + G_Q3_26 * P_2025 * 0.01) * (1 - TAX) * (1 - MINORITY)
                 + 1.6 * (1 - TAX))
NM9_26E_PARENT = 147.56 + Q3_26E_PARENT

# ---------- 3. 资产负债（2026-06-30） ----------
CASH = 93.73
DEBT = 2833.66 + 5.20          # 数据包有息负债 + 其他流动负债中的短期融资券 5.20（中报第 142 页）
DEBT_BEGIN = 2879.86 + 27.65
OP_CASH_RESERVE = 20.0         # 经营备付（约 1 个月付现成本）
DIV_PAYABLE = 193.92           # 应付股利（2025 年末期股利 0.79 元，2026-07-17 除息并发放；价格日已除息，扣一次）
DIV_RECEIVABLE = 18.19         # 应收股利（参股公司已宣告未发放，中报第 46、108 页）
ND_INT = DEBT - CASH + OP_CASH_RESERVE + DIV_PAYABLE - DIV_RECEIVABLE
INT_RATE = (42.29 * 2) / ((DEBT_BEGIN + DEBT) / 2)    # 实际平均融资成本（中报利息费用年化 / 平均有息负债）
CONSTR_PAYABLE = 148.41        # 其他应付款—工程款（中报第 141 页）
CONSTR_NORMAL = 48.0           # 常态工程应付（约 4 个月资本开支）

# 参股公司：持股比例与注册资本（中报第 14-15 页），账面值（中报第 117-121 页），2026-10-20 收盘价（腾讯行情）
LISTED = {
    # 名称: (持股比例, 总股本亿股, 10-20 收盘价, 账面价值)
    "国投电力": (0.1739, 80.0449, 16.09, 153.75),
    "湖北能源": (0.2793, 70.7939, 4.34, 104.55),
    "川投能源": (0.0994, 48.7461, 17.34, 63.98),
    "桂冠电力": (0.1302, 78.8238, 9.85, 66.85),
    "广州发展": (0.1552, 35.0587, 6.37, 45.42),
    "申能股份": (0.1159, 48.9408, 9.10, 41.06),
    "三峡水利": (0.2199, 19.1214, 5.96, 25.98),
    "甘肃能源": (0.1307, 32.4384, 6.79, 24.01),
}
LTEI_TOTAL = 747.54
LISTED_MV = sum(p * s * px for p, s, px, _ in LISTED.values())
LISTED_BOOK = sum(b for *_, b in LISTED.values())
UNLISTED_BOOK = LTEI_TOTAL - LISTED_BOOK      # 含浙江新能 8.65（按账面）
FIN_ASSETS = 43.35 + 39.13                    # 其他权益工具投资 + 其他非流动金融资产（公允价值）

# ---------- 4. 情景 ----------
SCEN = {
    "bear": dict(p=0.25, G=2900.0, tariff=-0.04, eq=41.0, maint=70.0, drift=-0.010,
                 oblig={2027: 25, 2028: 25, 2029: 25, 2030: 25}, gc=60.0, ret=0.05, g=0.005,
                 quasi=CONSTR_PAYABLE, assoc="cap"),
    "base": dict(p=0.50, G=3030.0, tariff=-0.005, eq=45.0, maint=55.0, drift=0.0,
                 oblig={2027: 20, 2028: 20, 2029: 20}, gc=65.0, ret=0.065, g=0.01,
                 quasi=CONSTR_PAYABLE - CONSTR_NORMAL, assoc="mv"),
    "bull": dict(p=0.25, G=3110.0, tariff=0.0, eq=47.0, maint=45.0, drift=0.005,
                 oblig={2027: 15, 2028: 15}, gc=65.0, ret=0.095, g=0.015,
                 quasi=50.0, assoc="mv_plus"),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
GC_LAG = 2
OTHINV_NORM = 3.4
FIN_NORM = FIN_2026E
DA_NORM = 189.0


def ebit_norm(s):
    p_s = P_2025 * (1 + s["tariff"])
    return EBIT_2026E + (s["G"] - G_2026E) * (P_2026 - V_COST) + s["G"] * (p_s - P_2026)


def parent_np_norm(s):
    e = ebit_norm(s)
    pretax = e - FIN_NORM + s["eq"] + OTHINV_NORM
    return (pretax - TAX * (pretax - s["eq"])) * (1 - MINORITY)


def assoc_value(s, k=COE):
    if s["assoc"] == "cap":       # 熊市：按 COE 资本化权益法收益（不高于市值）
        return min(s["eq"] / k, LISTED_MV + UNLISTED_BOOK)
    if s["assoc"] == "mv_plus":
        return LISTED_MV + UNLISTED_BOOK * 1.1
    return LISTED_MV + UNLISTED_BOOK


def t_years(d):
    return (d - VAL_DATE).days / 365.25


def oe_path(s):
    """返回 (stub, [(年, OE, OE_pre)], OE_2032, OE_pre_2031)；OE 为归母无杠杆所有者收益。"""
    base_pre = (ebit_norm(s) * (1 - TAX) + DA_NORM - s["maint"]) * (1 - MINORITY)
    stub = (EBIT_H2_26E * (1 - TAX) + DA_H1_26 - 27.5 - 10.0 - 25.0) * (1 - MINORITY)
    rows = []
    gcs = {}
    pre = base_pre
    for i, y in enumerate(YEARS):
        ebit_part = ebit_norm(s) * (1 - TAX) * (1 - MINORITY)
        drift_adj = ebit_part * ((1 + s["drift"]) ** (i + 1) - 1)
        ret = sum(gc * s["ret"] for yy, gc in gcs.items() if y - yy >= GC_LAG)
        gcs[y] = s["gc"]
        pre = base_pre + drift_adj + ret
        oe = pre - s["gc"] - s["oblig"].get(y, 0.0)
        rows.append((y, oe, pre))
    ret_all = sum(gc * s["ret"] for gc in gcs.values())
    pre_2032 = (base_pre + ebit_part * ((1 + s["drift"]) ** len(YEARS) - 1) + ret_all) * (1 + s["g"])
    reinv = s["g"] / s["ret"] if s["g"] > 0 else 0.0
    oe_2032 = pre_2032 * (1 - reinv)
    return stub, rows, oe_2032, base_pre


def value(s, k=COE, levered=True, detail=False):
    stub, rows, oe_2032, base_pre = oe_path(s)
    pv = stub / (1 + k) ** t_years(date(2026, 12, 31))
    for y, oe, _ in rows:
        pv += oe / (1 + k) ** t_years(date(y, 7, 1))
    tv = oe_2032 / (k - s["g"])
    pv_tv = tv / (1 + k) ** t_years(date(2031, 7, 1))
    pv_op = pv + pv_tv
    int_at = ND_INT * INT_RATE * (1 - TAX)
    debt_charge = int_at / k if levered else ND_INT
    nonop = assoc_value(s, k) + FIN_ASSETS
    eq = pv_op - debt_charge + nonop - s["quasi"]
    if detail:
        return dict(pv_explicit=pv, pv_tv=pv_tv, pv_op=pv_op, debt_charge=debt_charge,
                    nonop=nonop, quasi=s["quasi"], equity=eq, per_share=eq / SHARES,
                    tv_share=pv_tv / pv_op, base_pre=base_pre, rows=rows, oe_2032=oe_2032, stub=stub)
    return eq / SHARES


def weighted(k=COE, levered=True):
    return sum(s["p"] * value(s, k, levered) for s in SCEN.values())


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


def implied_irr():
    s = SCEN["base"]
    return solve(lambda k: value(s, k, True), 0.03, 0.15, PRICE)


def reverse_dcf():
    """现价隐含：(a) 2027 年基准所有者收益起永续增长率（不另加再投资）；(b) 10 年增速、其后 2.5%。"""
    s = SCEN["base"]
    stub, rows, _, _ = oe_path(s)
    oe27 = rows[0][1]
    int_at = ND_INT * INT_RATE * (1 - TAX)
    need = PRICE * SHARES + int_at / COE - (assoc_value(s) + FIN_ASSETS) + s["quasi"]
    need -= stub / (1 + COE) ** t_years(date(2026, 12, 31))
    t0 = t_years(date(2027, 7, 1))

    def pv_perp(g):
        return oe27 / (COE - g) * (1 + COE) ** (1 - t0)

    g_perp = solve(pv_perp, -0.05, 0.0899, need)

    def pv_10(g):
        tot, oe = 0.0, oe27
        for i in range(10):
            tot += oe / (1 + COE) ** (t0 + i)
            oe *= 1 + g
        tot += oe / (COE - 0.025) / (1 + COE) ** (t0 + 9)
        return tot

    g10 = solve(pv_10, -0.05, 0.30, need)
    return g_perp, g10


def main():
    global INT_RATE
    print("== 长江电力（600900）独立估值 ==")
    print(f"价格日 {VAL_DATE}  现价 {PRICE}  总股本 {SHARES} 亿股  市值 {PRICE*SHARES:.1f} 亿元")
    print(f"单位电价（不含税，发电量口径）2025: {P_2025:.5f}  变动成本 {V_COST:.5f}  单位边际 EBIT {MARGIN_KWH:.5f} 元/kWh")
    print(f"经营 EBIT：2025 {EBIT_2025:.2f}；2025H1 {EBIT_H1_25:.2f}；2026H1 {EBIT_H1_26:.2f}；2026H2E {EBIT_H2_26E:.2f}；2026E {EBIT_2026E:.2f}")
    print(f"发电量：2025 前三季度 {G_9M_25:.2f}，2025Q3 {G_Q3_25:.2f}，2025H1 {G_H1_25:.2f}，2025Q4 {G_Q4_25:.2f}；2026E {G_2026E:.2f}")
    print(f"2026 三季度归母净利估计 {Q3_26E_PARENT:.1f}（2025Q3 {Q3_25_PARENT}），前三季度 {NM9_26E_PARENT:.1f}（2025 同期 281.94）")
    print(f"2026E 报表归母净利 {PARENT_NP_2026E:.1f}，扣公允价值变动后 {PARENT_NP_2026E_RECURRING:.1f}")
    print(f"经调整净负债（计息口径）{ND_INT:.2f}；实际平均融资成本 {INT_RATE:.4f}；类债务（工程款超常态部分，基准）{CONSTR_PAYABLE-CONSTR_NORMAL:.2f}")
    print(f"无杠杆口径经调整净现金 net_cash_adj = {-(ND_INT + CONSTR_PAYABLE - CONSTR_NORMAL):.2f}")
    print(f"上市参股市值 {LISTED_MV:.2f}（账面 {LISTED_BOOK:.2f}）；非上市参股账面 {UNLISTED_BOOK:.2f}；金融资产 {FIN_ASSETS:.2f}")
    for n, (pc, sh, px, bk) in LISTED.items():
        print(f"   {n}: 持股 {pc*sh:.3f} 亿股 × {px} = {pc*sh*px:.2f}（账面 {bk}）")
    print()
    print("情景 | 正常化 2026 归母净利 | 无杠杆 OE_pre | V(有杠杆) | V(无杠杆) | 概率")
    for name, s in SCEN.items():
        d = value(s, detail=True)
        print(f"{name:5s} | {parent_np_norm(s):7.1f} | {d['base_pre']:7.1f} | {d['per_share']:6.2f} | {value(s, levered=False):6.2f} | {s['p']}")
        print(f"      经营现值 {d['pv_op']:.1f}（显性 {d['pv_explicit']:.1f}，终值 {d['pv_tv']:.1f}，终值占比 {d['tv_share']:.1%}）"
              f" − 利息现值 {d['debt_charge']:.1f} + 非经营 {d['nonop']:.1f} − 类债务 {d['quasi']:.1f} = {d['equity']:.1f}")
        path = ", ".join(f"{y}:{oe:.1f}" for y, oe, _ in d["rows"])
        grow = []
        prev = d["rows"][0][1]
        for y, oe, _ in d["rows"][1:]:
            grow.append(f"{y}:{oe/prev-1:+.1%}")
            prev = oe
        print(f"      OE 路径（2026H2 stub {d['stub']:.1f}）{path}；2032 {d['oe_2032']:.1f}；增速 {', '.join(grow)}")
    int_at = ND_INT * INT_RATE * (1 - TAX)
    d0 = value(SCEN["base"], detail=True)
    print(f"基准 2027 有杠杆所有者收益 = {d0['rows'][0][1]:.1f} − 税后利息 {int_at:.1f} = {d0['rows'][0][1]-int_at:.1f}"
          f"（再投资率 {SCEN['base']['gc']/d0['base_pre']:.1%}，增量回报 {SCEN['base']['ret']:.1%}）")
    vw = weighted()
    vw_u = weighted(levered=False)
    print()
    print(f"加权 V（有杠杆，9%）= {vw:.2f}  P/V = {PRICE/vw:.3f}")
    print(f"加权 V（无杠杆，9%）= {vw_u:.2f}  P/V = {PRICE/vw_u:.3f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"加权 V @8% = {v8:.2f}（P/V {PRICE/v8:.3f}）；@10% = {v10:.2f}（P/V {PRICE/v10:.3f}）")
    print(f"基准情景 V @8% = {value(SCEN['base'], 0.08):.2f}；@10% = {value(SCEN['base'], 0.10):.2f}")
    irr = implied_irr()
    print(f"现价隐含回报（基准情景有杠杆流，含终值与非经营资产）= {irr:.4f}")
    gp, g10 = reverse_dcf()
    print(f"反向 DCF（9%）：2027 起永续增速 {gp:.4f}；或前 10 年增速 {g10:.4f} 后 2.5%")
    print(f"分档价格（V 不变）：≤0.75 → {0.75*vw:.2f}；0.90 → {0.90*vw:.2f}；1.10 → {1.10*vw:.2f}")
    ev = PRICE * SHARES + ND_INT + (CONSTR_PAYABLE - CONSTR_NORMAL) + 119.82 - (LISTED_MV + UNLISTED_BOOK + FIN_ASSETS)
    en = ebit_norm(SCEN["base"])
    print(f"EV {ev:.1f}；EV/正常化EBIT {ev/en:.1f}×；EV/EBITDA {ev/(en+DA_NORM):.1f}×")
    print(f"股息率（近 12 月 1.00 元）{1.00/PRICE:.4f}；2026E 70% 分红对应每股 {0.70*PARENT_NP_2026E/SHARES:.3f}")
    # 证伪触发
    print()
    print("证伪触发后的独立 V（有杠杆，9%，其他按基准）：")
    import copy
    def alt(**kw):
        s = copy.deepcopy(SCEN["base"]); s.update(kw); return value(s)
    print(f"  F1 正常化发电量降至 2,920：{alt(G=2920.0):.2f}")
    print(f"  F2 全口径电价较基准再降 2%（乌白新合同下调约 6%）：{alt(tariff=-0.025):.2f}")
    r0 = INT_RATE; INT_RATE = 0.025; v_f3 = value(SCEN["base"]); INT_RATE = r0
    print(f"  F3 平均融资成本降至 2.5%：{v_f3:.2f}")
    print(f"  F4 扩机获批、增量回报 9.5%：{alt(ret=0.095):.2f}；抽蓄与新能源增量回报仅 4.5%：{alt(ret=0.045):.2f}")
    print(f"  F5 维护+义务性资本开支年均多 30（维护 85）：{alt(maint=85.0):.2f}")
    print(f"  参股公司改按 9% 资本化权益法收益：{alt(assoc='cap'):.2f}")


if __name__ == "__main__":
    main()
