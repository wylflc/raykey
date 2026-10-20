"""002179 中航光电：分部所有者收益 DCF（OI-291 b04 独立审计）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。估值日 2026-10-19（价格日），资产负债表取 2026-06-30（2026H1_report 第 40-42 页）。
口径：合并口径先算净利与再投资，再乘 (1-少数股东占比) 折成归母；净现金按归母权益占比折算。
经调整净现金为正，按框架照常全额扣除有息负债（不触发有杠杆口径）。
"""

PRICE = 32.82            # 2026-10-19 收盘
SHARES = 21.0025         # 总股本（含回购专户 409.867 万股，专户股份用于股权激励，不注销）
TREASURY = 0.0409867     # 回购专户股份（2026H1_report 第 34 页）
COE = 0.09

# ---------- 2025 基期分部（独立估算：防务约 40%，未查到公开口径） ----------
R25 = 213.86             # 2025_annual_report 第 10 页
D25 = 85.0               # 防务收入估算
C25 = R25 - D25          # 民品收入估算
MINOR = 0.075            # 少数股东损益占合并净利（2025 8.0%、2026H1 7.2%）

# ---------- 经调整净现金（2026-06-30，合并） ----------
CASH = 63.887            # 货币资金，其中存放中航工业财务公司 13.326
RESTRICTED = 0.134       # 票据保证金等受限资金
RESERVE = 20.0           # 经营备付：约一个季度的季节性经营流出（2026Q1 经营现金流 -20.61）
DEBT = {"短期借款(含未终止确认票据贴现)": 20.822, "长期借款": 2.958,
        "一年内到期长期借款": 0.901, "租赁负债": 0.932, "一年内到期租赁负债": 0.463}
DIV_PAYABLE = 1.226      # 应付股利（子公司对少数股东）
QUASI_DEBT = 0.306       # 长期应付款-改制预留费
NET_CASH_ADJ = CASH - RESTRICTED - RESERVE - sum(DEBT.values()) - DIV_PAYABLE - QUASI_DEBT
PARENT_SHARE = 1 - 19.831 / 262.502   # 归母权益 / 全部权益
NON_OP = 0.019           # 交易性金融资产（千里科技股票）

# ---------- 三情景 ----------
# D26/C26：2026 防务/民品收入；gD/gC：2027-2031 增速；mD/mC：2026-2031 合并净利率（含净利息、剔除一次性）
# kD/kC：每新增 1 元收入需投入的营运资本+固定资本；X：在建项目超额资本开支；
# vat：2028 年起先进制造业增值税加计抵减到期的税后影响（按到期概率计）；gT/ron：终值增长与终值增量回报
SCEN = {
    "bear": dict(p=0.25, D26=76.0, C26=143.0,
                 gD=[-0.02, 0.02, 0.03, 0.03, 0.03], gC=[0.08, 0.07, 0.06, 0.05, 0.05],
                 mD=[0.153, 0.150, 0.150, 0.150, 0.150, 0.150], mC=[0.055, 0.053, 0.052, 0.052, 0.052, 0.052],
                 kD=1.1, kC=0.7, X={2026: 4.0, 2027: 4.0, 2028: 2.5}, vat=0.9, gT=0.020, ron=0.09),
    "base": dict(p=0.50, D26=77.0, C26=146.4,
                 gD=[0.04, 0.07, 0.07, 0.06, 0.05], gC=[0.12, 0.11, 0.10, 0.08, 0.07],
                 mD=[0.167, 0.175, 0.185, 0.195, 0.200, 0.200], mC=[0.060, 0.064, 0.068, 0.071, 0.073, 0.075],
                 kD=1.0, kC=0.6, X={2026: 4.0, 2027: 3.0, 2028: 1.5}, vat=0.45, gT=0.025, ron=0.12),
    "bull": dict(p=0.25, D26=78.0, C26=149.0,
                 gD=[0.09, 0.10, 0.09, 0.07, 0.05], gC=[0.16, 0.15, 0.13, 0.10, 0.08],
                 mD=[0.183, 0.200, 0.215, 0.225, 0.230, 0.230], mC=[0.064, 0.072, 0.080, 0.085, 0.088, 0.090],
                 kD=0.8, kC=0.5, X={2026: 4.0, 2027: 3.0, 2028: 1.5}, vat=0.0, gT=0.025, ron=0.15),
}
YEARS = list(range(2026, 2037))   # 2026-2031 明确期，2032-2036 增速线性收敛到 gT，2037 起永续


def project(s):
    gD, gC = list(s["gD"]), list(s["gC"])
    for j in range(1, 6):
        gD.append(s["gD"][-1] + (s["gT"] - s["gD"][-1]) * j / 6)
        gC.append(s["gC"][-1] + (s["gT"] - s["gC"][-1]) * j / 6)
    D, C = [s["D26"]], [s["C26"]]
    for a, b in zip(gD, gC):
        D.append(D[-1] * (1 + a))
        C.append(C[-1] * (1 + b))
    mD = s["mD"] + [s["mD"][-1]] * (len(YEARS) - len(s["mD"]))
    mC = s["mC"] + [s["mC"][-1]] * (len(YEARS) - len(s["mC"]))
    rows, dp, cp = [], D25, C25
    for i, y in enumerate(YEARS):
        ni = D[i] * mD[i] + C[i] * mC[i] - (s["vat"] if y >= 2028 else 0.0)
        reinv = s["kD"] * max(0.0, D[i] - dp) + s["kC"] * max(0.0, C[i] - cp) + s["X"].get(y, 0.0)
        rows.append(dict(y=y, D=D[i], C=C[i], R=D[i] + C[i], ni=ni, nip=ni * (1 - MINOR),
                         reinv=reinv, oe=(ni - reinv) * (1 - MINOR)))
        dp, cp = D[i], C[i]
    return rows


def equity_value(s, r, rows=None):
    rows = rows or project(s)
    pv = 0.5 * rows[0]["oe"] / (1 + r) ** 0.2          # 2026 下半年所有者收益（6-30 资产负债表之后）
    for row in rows[1:]:
        pv += row["oe"] / (1 + r) ** (row["y"] - 2026 - 0.3)   # 年中折现，2027 年中距估值日 0.7 年
    oe37 = rows[-1]["nip"] * (1 + s["gT"]) * (1 - s["gT"] / s["ron"])
    tv = oe37 / (r - s["gT"]) / (1 + r) ** 9.7
    cash = NET_CASH_ADJ * PARENT_SHARE + NON_OP
    return pv + tv + cash, pv, tv, cash


def per_share(s, r=COE, shares=SHARES):
    return equity_value(s, r)[0] / shares


def weighted(r=COE, probs=None, scen=SCEN, shares=SHARES):
    probs = probs or {k: v["p"] for k, v in scen.items()}
    return sum(probs[k] * equity_value(scen[k], r)[0] for k in scen) / shares


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s):
    mcap = PRICE * SHARES
    return solve(lambda r: equity_value(s, r)[0], 0.03, 0.20, mcap)


def reverse_perpetual(ni_start, ron):
    """现价 = NI × (1 - g/ron)/(r - g) + 现金，解 g。"""
    ev = PRICE * SHARES - NET_CASH_ADJ * PARENT_SHARE - NON_OP
    return solve(lambda g: ni_start * (1 - g / ron) / (COE - g), -0.05, 0.0899, ev)


def pv_10y(ni0, g, ron=None, gT=0.025, ron_T=0.12):
    """2026 正常化归母净利 ni0 起，10 年复合增速 g，之后 gT 永续（终值增量回报 ron_T）。
    ron=None：增长不需额外资本，所有者收益恒为净利 × (1 - gT/ron_T)；否则增长期再投资率 = g/ron。"""
    tot, ni = 0.0, ni0
    conv = (1 - gT / ron_T) if ron is None else (1 - g / ron)
    for t in range(1, 11):
        ni *= 1 + g
        tot += ni * conv / (1 + COE) ** (t - 0.3)
    tot += ni * (1 + gT) * (1 - gT / ron_T) / (COE - gT) / (1 + COE) ** 9.7
    return tot


def reverse_10y_free(ni0):
    ev = PRICE * SHARES - NET_CASH_ADJ * PARENT_SHARE - NON_OP
    return solve(lambda g: pv_10y(ni0, g), 0.0, 0.40, ev)


def max_pv_10y(ni0, ron):
    """增长需按增量回报 ron 投入资本时，任意 10 年增速所能达到的最大经营价值。"""
    return max((pv_10y(ni0, g / 1000, ron), g / 1000) for g in range(0, int(ron * 1000)))


def stats(s):
    rows = project(s)
    r5 = rows[1:6]
    reinv = sum(x["reinv"] for x in r5)
    ni = sum(x["ni"] for x in r5)
    inc_ret = (rows[5]["ni"] - rows[0]["ni"]) / reinv
    oe = [x["oe"] for x in rows[:6]]
    g_oe = [oe[i] / oe[i - 1] - 1 for i in range(1, 6)]
    g_ni = [rows[i]["nip"] / rows[i - 1]["nip"] - 1 for i in range(1, 6)]
    return rows, reinv / ni, inc_ret, g_oe, g_ni


def variant(name, **kw):
    s = {k: (dict(v) if isinstance(v, dict) else (list(v) if isinstance(v, list) else v))
         for k, v in SCEN[name].items()}
    s.update(kw)
    return s


if __name__ == "__main__":
    print("== 中航光电 002179 独立估值（亿元；元/股）==")
    print(f"经调整净现金(合并) {NET_CASH_ADJ:.2f}；归母份额 {NET_CASH_ADJ * PARENT_SHARE:.2f}（>0，不触发有杠杆口径）")
    print(f"  现金 {CASH:.2f} − 受限 {RESTRICTED:.2f} − 经营备付 {RESERVE:.1f} − 有息负债 {sum(DEBT.values()):.2f}"
          f" − 应付股利 {DIV_PAYABLE:.2f} − 类债务 {QUASI_DEBT:.2f}；财务公司存款 13.33 单列（计入现金）")
    for k, s in SCEN.items():
        eq, pv, tv, cash = equity_value(s, COE)
        rows, rr, ir, g_oe, g_ni = stats(s)
        print(f"\n[{k}] p={s['p']:.2f}  V={eq / SHARES:.2f}  股权价值 {eq:.1f}（明确期 {pv:.1f} + 终值 {tv:.1f}"
              f" + 现金 {cash:.1f}；终值占比 {tv / eq:.0%}）  8%: {per_share(s, 0.08):.2f}  10%: {per_share(s, 0.10):.2f}")
        print(f"  2026 正常化归母净利 {rows[0]['nip']:.2f}；2031 {rows[5]['nip']:.2f}；2031 收入 {rows[5]['R']:.1f}"
              f"（防务 {rows[5]['D']:.1f}/民品 {rows[5]['C']:.1f}）；再投资率(2027-31) {rr:.0%}；增量回报 {ir:.0%}")
        print("  年份   收入   归母净利  再投资  归母所有者收益")
        for x in rows[:6]:
            print(f"  {x['y']}  {x['R']:6.1f}  {x['nip']:6.2f}  {x['reinv']:6.2f}  {x['oe']:6.2f}")
        print("  所有者收益增速 2027-31:", [round(g, 3) for g in g_oe], " 归母净利增速:", [round(g, 3) for g in g_ni])
    vw = weighted()
    print(f"\n加权 V = {vw:.2f}；P/V = {PRICE / vw:.2f}")
    print(f"剔除回购专户后 V = {weighted(shares=SHARES - TREASURY):.2f}；P/V = {PRICE / weighted(shares=SHARES - TREASURY):.2f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}（P/V {PRICE / weighted(0.08):.2f}）；"
          f"10%：加权 V = {weighted(0.10):.2f}（P/V {PRICE / weighted(0.10):.2f}）")
    print(f"基准情景隐含回报（现价）= {implied_irr(SCEN['base']):.2%}；牛情景隐含回报 = {implied_irr(SCEN['bull']):.2%}")
    base_rows = project(SCEN["base"])
    print(f"反向 DCF：以基准 2027 归母净利 {base_rows[1]['nip']:.2f}、增量回报 12% 计，隐含永续增速 "
          f"{reverse_perpetual(base_rows[1]['nip'], 0.12):.2%}；增量回报 15% 时 {reverse_perpetual(base_rows[1]['nip'], 0.15):.2%}")
    ni0 = base_rows[0]["nip"]
    ev_needed = PRICE * SHARES - NET_CASH_ADJ * PARENT_SHARE - NON_OP
    print(f"反向 DCF：现价对应归母经营价值 {ev_needed:.1f}。以 2026 正常化归母净利 {ni0:.2f} 起，若增长不需额外资本"
          f"（所有者收益恒为净利 79%），隐含 10 年复合增速 {reverse_10y_free(ni0):.2%}"
          f"（2036 年归母约 {ni0 * (1 + reverse_10y_free(ni0)) ** 10:.0f}）")
    for ron in (0.12, 0.15, 0.20):
        mx, g_at = max_pv_10y(ni0, ron)
        print(f"  增长按增量回报 {ron:.0%} 投入资本：任意 10 年增速的最大经营价值 {mx:.1f}（g≈{g_at:.1%}），"
              f"{'不足以' if mx < ev_needed else '可以'}支撑现价")
    print(f"档位价格（V 不变）：明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}～{0.90 * vw:.2f}；"
          f"大致合理 {0.90 * vw:.2f}～{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")

    print("\n== 证伪条件触发后的独立 V ==")
    f1 = weighted(probs={"bear": 0.40, "base": 0.50, "bull": 0.10})
    f2 = weighted(probs={"bear": 0.60, "base": 0.35, "bull": 0.05})
    f3 = weighted(probs={"bear": 0.10, "base": 0.45, "bull": 0.45})
    sc4 = dict(SCEN)
    sc4["base"] = variant("base", kD=1.2, kC=0.8)
    sc4["bull"] = variant("bull", kD=1.0, kC=0.65)
    f4 = weighted(scen=sc4)
    sc5 = {k: variant(k, mD=[m * 0.94 for m in SCEN[k]["mD"]], mC=[m * 0.94 for m in SCEN[k]["mC"]]) for k in SCEN}
    f5 = weighted(scen=sc5)
    print(f"F1 三季报单季归母<3.0亿或毛利率<27%：概率改 40/50/10 → V {f1:.2f}")
    print(f"F2 2026 年报正常化归母<18亿且经营现金流<12亿：概率改 60/35/5 → V {f2:.2f}")
    print(f"F3 2027 中报收入同比≥12%且毛利率≥31%：概率改 10/45/45 → V {f3:.2f}")
    print(f"F4 2026 年末应收票据+账款+融资≥190亿或经营现金流<10亿：再投资强度上调 → V {f4:.2f}")
    print(f"F5 高新技术企业复审失败或有效税率持续≥15%：净利率×0.94 → V {f5:.2f}")
    fsd_mkt = 0.4664 * 47.4
    fsd_dcf = 0.4664 * 0.88 * (vw * SHARES / ni0)
    print(f"\n交叉验证（分部加总）：富士达 46.64% 按 2026-08-28 市值约 47.4 亿计 {fsd_mkt:.1f} 亿；"
          f"DCF 内含其利润贡献 {0.4664 * 0.88:.2f} 亿/年 × {vw * SHARES / ni0:.1f} 倍 ≈ {fsd_dcf:.1f} 亿；"
          f"按市值重估 +{(fsd_mkt - fsd_dcf) / SHARES:.2f} 元/股，不改变结论")
    ev_mkt = PRICE * SHARES + 19.831 - (CASH - sum(DEBT.values()))
    ev_v = vw * SHARES + 19.831 - (CASH - sum(DEBT.values()))
    print(f"EV/EBIT(TTM 23.55)：现价 {ev_mkt / 23.55:.1f} 倍；独立 V 对应 {ev_v / 23.55:.1f} 倍；"
          f"现价 / 2026 正常化归母 = {PRICE * SHARES / ni0:.1f} 倍；V 对应 {vw * SHARES / ni0:.1f} 倍")
    print(f"PB：现价 2.84 倍隐含可持续 ROE ≈ {2.84 * (COE - 0.025) + 0.025:.1%}"
          f"（2026 正常化 ROE {ni0 / 242.67:.1%} 对应合理 PB {(ni0 / 242.67 - 0.025) / (COE - 0.025):.2f}）")
