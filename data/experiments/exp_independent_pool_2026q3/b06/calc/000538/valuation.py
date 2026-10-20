# -*- coding: utf-8 -*-
"""云南白药（000538）独立估值：OI-291 b06 深度版。

口径：金额单位亿元，每股价值元/股；价格日 2026-10-20，现价 53.38 元，总股本 17.8426 亿股（无回购专户股份）。
方法：核心经营（工业 + 医药流通）所有者收益 DCF（归母、无杠杆，净现金为正）
      + 上海医药 17.95% 股权（市值折价，权益法收益资本化互校）
      + 经调整净现金 + 其他非经营金融资产。
输入全部写在脚本内，出处见同名正文。运行：python3 valuation.py
"""
from __future__ import annotations

PRICE = 53.38
SHARES = 17.8426            # 亿股，资产负债表 1,784,262,603 股；无库存股、无拟注销股份
MKT_CAP = PRICE * SHARES
VAL_DATE_TO_YE2026 = 72 / 365   # 2026-10-20 → 2026-12-31

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 59-62、117、126-128、142-147 页）
CASH = 95.70                 # 货币资金
TRADING_FA = 47.51           # 交易性金融资产（银行理财 14.2 + 券商理财 33.0，第 49 页）
TERM_DEP_OCA = 3.03          # 其他流动资产中的定期存款等理财产品（第 126 页）
RESTRICTED = 0.2953 + 0.0266 + 5.3666   # 保证金、房改维修金、改制专户（第 142 页；改制专户与长期应付款 5.36 对应，只扣一次）
DEBT = 0.2511 + 1.6485 + 0.0210 + 1.3310  # 短借 + 一年内到期非流动负债 + 长借 + 租赁负债
DIV_RECEIVABLE = 2.3297      # 应收上海医药 2025 年末期股利（第 127 页）
SPECIAL_DIV_PAID = 18.5206   # 2026 特别分红 10 派 10.38，2026-09-24 派发（dividend_20260917_465224）
JYT_DEFERRED = 1.32          # 聚药堂股权尾款（其他应付款-股权转让款，第 144 页）
TTM_REVENUE = 418.14
OPER_RESERVE_RATIO = 0.03    # 经营备付：TTM 营收 3%

gross_cash = CASH + TRADING_FA + TERM_DEP_OCA
oper_reserve = OPER_RESERVE_RATIO * TTM_REVENUE
NET_CASH_ADJ = (gross_cash - RESTRICTED - DEBT + DIV_RECEIVABLE
                - SPECIAL_DIV_PAID - JYT_DEFERRED - oper_reserve)

# ---------------------------------------------------------------- 非经营资产
SPH_SHARES = 6.65626796      # 亿股，上海医药 A 股（2025_annual_report 第 217 页公允价值 139.78 亿 ÷ 21.00 元反推，持股 17.95%）
SPH_PRICE = 16.45            # 元，2026-10-20 收盘（腾讯行情 qt.gtimg.cn）
SPH_MKT = SPH_SHARES * SPH_PRICE
SPH_BOOK = 131.48            # 2026-06-30 长期股权投资账面
OTHER_NCFA = 3.124           # 其他非流动金融资产（FVTPL）
OTHER_EQ = 0.717             # 其他权益工具投资（ImmuneSensor）
TCM_FUND = 5.005             # 云南中医药大健康创新股权投资基金（联营，权益法）

# 上海医药权益法收益正常化：其 2026H1 剔除一次性特殊损益后归母 28.28 亿（中信建投 2026-09-06 研报，格隆汇转载），
# H2 参照 2025H2 的 12.67 亿（2025 全年 57.25 − 2025H1 44.58）至券商预测隐含约 17 亿，取 bear 10 / base 14 / bull 17
SPH_NORM_NP = {"bear": 38.0, "base": 42.0, "bull": 45.0}
SPH_STAKE = 0.1795
SPH_ADJ = -0.40              # 公允价值调整摊销等（2026H1 账面确认 6.08 vs 17.95%×35.04=6.29）


def non_operating(scn: str) -> dict:
    disc = {"bear": 0.30, "base": 0.15, "bull": 0.0}[scn]
    hair = {"bear": 0.6, "base": 0.8, "bull": 1.0}[scn]
    hair_eq = {"bear": 0.3, "base": 0.5, "bull": 0.8}[scn]   # 未上市美国生物科技公司，折价更大
    sph = SPH_MKT * (1 - disc)
    other = OTHER_NCFA * hair + OTHER_EQ * hair_eq + TCM_FUND * hair
    return {"sph": sph, "other": other, "total": sph + other}


# ---------------------------------------------------------------- 核心经营（剔除上海医药、理财、利息）
NWC_RATIO = 0.137            # 经营性净营运资本 / 营收（2026-06-30 约 57.4 亿 / 418）
NET_CAPEX_2026 = 0.8         # 购建长期资产约 5 亿 − 折旧摊销约 4.2 亿
CORE_TAX = 0.165             # 15%（西部大开发）与 25%（省医药等）加权；2025 剔除权益法收益后 16.9%，TTM 16.1%
MINORITY = 0.2

SCN = {
    # rev2026: 正常化营收；margin: 核心 EBIT 率（含补助、正常化减值）；h2_ebit: 2026H2 核心 EBIT 估计
    "bear": dict(p=0.25, rev2026=416.0, margin=0.103, h2_ebit=13.0,
                 growth=[0.000, 0.005, 0.010, 0.015, 0.015], tg=0.015),
    "base": dict(p=0.50, rev2026=420.0, margin=0.117, h2_ebit=14.5,
                 growth=[0.020, 0.030, 0.030, 0.030, 0.025], tg=0.025),
    "bull": dict(p=0.25, rev2026=424.0, margin=0.126, h2_ebit=15.5,
                 growth=[0.045, 0.050, 0.050, 0.045, 0.040], tg=0.025),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
FIN_INCOME_AT = {"bear": 0.8, "base": 0.9, "bull": 1.0}   # 理财+利息税后（含净利息），正常化归母口径用


def core_nopat_2026(s: dict) -> float:
    return s["rev2026"] * s["margin"] * (1 - CORE_TAX) - MINORITY


def core_flows(s: dict):
    """返回 [(t, OE)] 及终值所需参数。mid-year：2027 年现金流在 2027-07-01。"""
    flows = []
    # 2026H2：现金已从 6/30 起产生，按 2026-11 中计（t≈0.1）
    h2_oe = (s["h2_ebit"] * (1 - CORE_TAX) - MINORITY / 2) * 0.92
    flows.append((0.10, h2_oe))
    nopat = core_nopat_2026(s)
    rev = s["rev2026"]
    rows = []
    for i, (y, g) in enumerate(zip(YEARS, s["growth"])):
        nopat_y = nopat * (1 + g)
        rev_y = rev * (1 + g)
        reinv = NET_CAPEX_2026 * rev_y / s["rev2026"] + NWC_RATIO * (rev_y - rev)
        oe = nopat_y - reinv
        t = VAL_DATE_TO_YE2026 + i + 0.5
        flows.append((t, oe))
        rows.append((y, g, nopat_y, reinv, oe))
        nopat, rev = nopat_y, rev_y
    g = s["tg"]
    nopat_T = nopat * (1 + g)
    rev_T = rev * (1 + g)
    reinv_T = NET_CAPEX_2026 * rev_T / s["rev2026"] + NWC_RATIO * (rev_T - rev)
    oe_T = nopat_T - reinv_T
    t_T = VAL_DATE_TO_YE2026 + len(YEARS) + 0.5
    return flows, (t_T, oe_T, g), rows


def pv_core(s: dict, r: float):
    flows, (t_T, oe_T, g), rows = core_flows(s)
    pv_exp = sum(cf / (1 + r) ** t for t, cf in flows)
    pv_tv = oe_T * (1 + r) / (r - g) / (1 + r) ** t_T
    return pv_exp, pv_tv, rows


def scenario_value(name: str, r: float = 0.09):
    s = SCN[name]
    pv_exp, pv_tv, rows = pv_core(s, r)
    nonop = non_operating(name)
    eq = pv_exp + pv_tv + NET_CASH_ADJ + nonop["total"]
    return {"v": eq / SHARES, "equity": eq, "pv_exp": pv_exp, "pv_tv": pv_tv,
            "tv_share": pv_tv / (pv_exp + pv_tv), "nonop": nonop, "rows": rows}


def weighted(r: float = 0.09):
    return sum(SCN[k]["p"] * scenario_value(k, r)["v"] for k in SCN)


def solve(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def implied_irr():
    return solve(lambda r: scenario_value("base", r)["equity"] - MKT_CAP, 0.04, 0.20)


def reverse_dcf_10y(r=0.09, tg=0.025):
    """现价隐含：2027-2036 年所有者收益恒定增速 g（再投资随增速联动），之后 2.5%。"""
    s = SCN["base"]
    nonop = non_operating("base")["total"]
    target = MKT_CAP - NET_CASH_ADJ - nonop

    def value(g):
        nopat = core_nopat_2026(s)
        rev = s["rev2026"]
        pv = (s["h2_ebit"] * (1 - CORE_TAX) - MINORITY / 2) * 0.92 / (1 + r) ** 0.10
        for i in range(10):
            nopat *= (1 + g)
            rev_n = rev * (1 + g)
            reinv = NET_CAPEX_2026 * rev_n / s["rev2026"] + NWC_RATIO * (rev_n - rev)
            pv += (nopat - reinv) / (1 + r) ** (VAL_DATE_TO_YE2026 + i + 0.5)
            rev = rev_n
        nopat_T = nopat * (1 + tg)
        rev_T = rev * (1 + tg)
        oe_T = nopat_T - NET_CAPEX_2026 * rev_T / s["rev2026"] - NWC_RATIO * (rev_T - rev)
        pv += oe_T * (1 + r) / (r - tg) / (1 + r) ** (VAL_DATE_TO_YE2026 + 10.5)
        return pv - target

    return solve(value, -0.05, 0.20)


def reverse_dcf_perpetual(r=0.09):
    s = SCN["base"]
    nonop = non_operating("base")["total"]
    target = MKT_CAP - NET_CASH_ADJ - nonop
    nopat = core_nopat_2026(s)

    h2 = (s["h2_ebit"] * (1 - CORE_TAX) - MINORITY / 2) * 0.92 / (1 + r) ** 0.10

    def value(g):
        oe = nopat * (1 + g) - NET_CAPEX_2026 - NWC_RATIO * s["rev2026"] * g
        return h2 + oe * (1 + r) / (r - g) / (1 + r) ** (VAL_DATE_TO_YE2026 + 0.5) - target

    return solve(value, -0.05, 0.085)


def normalized_parent_np():
    out = {}
    for k, s in SCN.items():
        core = core_nopat_2026(s)
        sph = SPH_NORM_NP[k] * SPH_STAKE + SPH_ADJ
        out[k] = core + sph + FIN_INCOME_AT[k]
    return out


def sotp_base():
    """分部加总（基准）：2026E 分部 NOPAT × 倍数。"""
    seg = {  # name: (EBIT, tax, multiple)
        "健康品（牙膏、养元青）": (23.1, 0.15, 16.0),
        "药品（白药系列等）": (12.5, 0.15, 20.0),
        "中药资源及其他": (4.0, 0.15, 10.0),
        "医药流通（省医药）": (10.2, 0.25, 9.0),
        "总部、抵销与正常化减值": (-0.7, 0.17, 12.0),
    }
    total = 0.0
    lines = []
    for n, (ebit, tax, mult) in seg.items():
        nopat = ebit * (1 - tax)
        val = nopat * mult
        total += val
        lines.append((n, ebit, nopat, mult, val))
    nonop = non_operating("base")["total"]
    eq = total - MINORITY * 12 + nonop + NET_CASH_ADJ
    return lines, total, eq / SHARES


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print(f"现价 {PRICE:.2f} 元 × 总股本 {SHARES:.4f} 亿股 = 市值 {MKT_CAP:.1f} 亿元")
    print(f"现金类合计 {gross_cash:.2f}；受限 {RESTRICTED:.2f}；有息负债 {DEBT:.2f}；应收股利 {DIV_RECEIVABLE:.2f}；"
          f"已派特别分红 {SPECIAL_DIV_PAID:.2f}；聚药堂尾款 {JYT_DEFERRED:.2f}；经营备付 {oper_reserve:.2f}")
    print(f"经调整净现金 net_cash_adj = {NET_CASH_ADJ:.2f} 亿元（为正，按无杠杆口径）")
    print(f"上海医药持股市值 {SPH_MKT:.2f} 亿元（账面 {SPH_BOOK:.2f}，市值/账面 {SPH_MKT / SPH_BOOK:.2f}）")
    for k in SCN:
        sph_inc = SPH_NORM_NP[k] * SPH_STAKE + SPH_ADJ
        print(f"  {k}: 权益法正常化收益 {sph_inc:.2f} 亿元；市值折价后 {non_operating(k)['sph']:.2f}；"
              f"权益法收益×12 = {sph_inc * 12:.2f}")
    print()
    for k in SCN:
        s = SCN[k]
        res = scenario_value(k)
        print(f"[{k}] p={s['p']:.2f} 2026 正常化营收 {s['rev2026']:.0f}，核心 EBIT 率 {s['margin']:.1%}，"
              f"核心归母 NOPAT {core_nopat_2026(s):.2f}，终值增速 {s['tg']:.1%}")
        for y, g, nopat, reinv, oe in res["rows"]:
            print(f"    {y}: 增速 {g:+.1%} NOPAT {nopat:6.2f} 再投资 {reinv:5.2f} 所有者收益 {oe:6.2f}")
        print(f"    核心 PV：显性 {res['pv_exp']:.1f} + 终值 {res['pv_tv']:.1f}（终值占比 {res['tv_share']:.1%}）；"
              f"非经营 {res['nonop']['total']:.1f}；净现金 {NET_CASH_ADJ:.1f} → 股权 {res['equity']:.1f} 亿元")
        print(f"    V = {res['v']:.2f} 元/股，P/V = {PRICE / res['v']:.3f}")
    vw = weighted(0.09)
    pv = PRICE / vw
    print()
    print(f"加权 V（9%）= {vw:.2f} 元/股；P/V = {pv:.3f} → {band(pv)}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：加权 V = {v8:.2f}（P/V {PRICE / v8:.3f}）；10%：加权 V = {v10:.2f}（P/V {PRICE / v10:.3f}）")
    for r in (0.08, 0.10):
        print(f"   {r:.0%} 下三情景：" + "，".join(f"{k} {scenario_value(k, r)['v']:.2f}" for k in SCN))
    irr = implied_irr()
    print(f"现价隐含回报（基准现金流）= {irr:.2%}")
    g10 = reverse_dcf_10y()
    gp = reverse_dcf_perpetual()
    print(f"反向 DCF：9% 下现价隐含 2027-2036 所有者收益年增 {g10:.2%}（之后 2.5%）；或单阶段永续增速 {gp:.2%}")
    print()
    npn = normalized_parent_np()
    print("2026 正常化归母净利（核心 + 上海医药正常化 + 理财利息税后）：" +
          "，".join(f"{k} {v:.2f}" for k, v in npn.items()))
    lines, core_total, v_sotp = sotp_base()
    print("分部加总（基准倍数）：")
    for n, ebit, nopat, mult, val in lines:
        print(f"    {n}: EBIT {ebit:5.1f} NOPAT {nopat:5.2f} × {mult:4.1f} = {val:6.1f}")
    print(f"    核心合计 {core_total:.1f}（扣少数股东 {MINORITY * 12:.1f}）+ 非经营 {non_operating('base')['total']:.1f}"
          f" + 净现金 {NET_CASH_ADJ:.1f} → {v_sotp:.2f} 元/股")
    ev = MKT_CAP - NET_CASH_ADJ - non_operating("base")["total"]
    base_ebit = SCN["base"]["rev2026"] * SCN["base"]["margin"]
    ttm_ebit = core_history()["TTM(2025H2+2026H1)"][1]
    print(f"EV（扣净现金与非经营）= {ev:.1f}；EV/正常化核心 EBIT = {ev / base_ebit:.1f}×；"
          f"EV/TTM 核心 EBIT {ttm_ebit:.2f} = {ev / ttm_ebit:.1f}×；EV/核心 NOPAT = {ev / core_nopat_2026(SCN['base']):.1f}×")
    dps_ttm = 1.583 + 1.038
    print(f"近 12 个月每股现金分红 {dps_ttm:.3f} 元（2026-04-30 除息 1.583 + 2026-09-24 除息 1.038），股息率 {dps_ttm / PRICE:.2%}；"
          f"无回购")
    print(f"分档价格（V 不变）：明显低估 ≤ {0.75 * vw:.2f}；温和低估 ≤ {0.90 * vw:.2f}；大致合理 ≤ {1.10 * vw:.2f}")
    # 证伪触发后的 V（见正文第 8 节）
    print()
    print("证伪触发后的独立 V（9%）：")
    v_f1 = mix({"bear": 0.5, "base": 0.4, "bull": 0.1})
    print(f"    F1 前三季度归母 < 47 亿或 2026 药品销售+健康日化收入 < 145 亿 → 概率改为 50/40/10：V = {v_f1:.2f}")
    v_f2 = value_custom("base", margin=0.108)
    print(f"    F2 2026 药品销售+健康日化合计毛利率 < 67.0%（基准核心 EBIT 率降至 10.8%）→ V = {v_f2:.2f}")
    d_f3 = 19.64 * 0.10 * 15.0 / SHARES   # 健康品 NOPAT −10%，按 15 倍
    print(f"    F3 2027H1 健康产品公司不含品牌费利润 < 11.5 亿 → V = {vw - d_f3:.2f}（−{d_f3:.2f}）")
    d_f4 = (SPH_PRICE - 13.0) * SPH_SHARES * 0.85 / SHARES
    print(f"    F4 上海医药 A 股连续 20 日 < 13 元 → V = {vw - d_f4:.2f}（−{d_f4:.2f}）")
    v_f5 = mix({"bear": 0.1, "base": 0.4, "bull": 0.5})
    print(f"    F5（上行）2026 扣非归母 ≥ 52 亿且 2027H1 药品销售+健康日化收入同比 ≥ +5% → 概率改为 10/40/50：V = {v_f5:.2f}")
    # 增长路径字段
    s = SCN["base"]
    rows = scenario_value("base")["rows"]
    reinv_rate = sum(r[3] for r in rows) / sum(r[2] for r in rows)
    inc_ret = (rows[-1][2] - core_nopat_2026(s)) / sum(r[3] for r in rows)
    print()
    print(f"基准增长路径（NOPAT）{[r[1] for r in rows]}，终值 {s['tg']}；再投资率 {reinv_rate:.3f}；增量回报 {inc_ret:.2f}")
    print(f"非经营资产（基准）{non_operating('base')['total']:.2f} 亿元，其中上海医药 {non_operating('base')['sph']:.2f}")
    print()
    print("历史核心 EBIT（毛利 − 税金及附加 − 三费 − 研发 + 其他收益 + 减值 + 资产处置 + 营业外净额）：")
    for k, (rev, e, exi) in core_history().items():
        print(f"    {k}: 营收 {rev:7.2f} 核心 EBIT {e:6.2f}（{e / rev:.2%}），剔除减值 {exi:6.2f}（{exi / rev:.2%}）")


def value_custom(name, margin=None, r=0.09):
    s = dict(SCN[name])
    if margin is not None:
        s["margin"] = margin
    pv_exp, pv_tv, _ = pv_core(s, r)
    eq = pv_exp + pv_tv + NET_CASH_ADJ + non_operating(name)["total"]
    return eq / SHARES


def mix(probs, r=0.09):
    return sum(probs[k] * scenario_value(k, r)["v"] for k in probs)


HIST = {  # 营收, 营业成本, 税金及附加, 销售, 管理, 研发, 其他收益, 信用减值, 资产减值, 资产处置, 营业外净额
    "2024": (400.333, 288.648, 2.431, 48.795, 10.376, 3.374, 1.020, -0.399, -0.912, 0.005, 0.155 - 0.424),
    "2025": (411.870, 290.329, 2.341, 56.195, 10.201, 3.505, 1.008, 0.581, -2.584, 0.082, 0.250 - 0.206),
    "2025H1": (212.571, 146.979, 1.258, 25.164, 3.635, 1.559, 0.274, -0.984, -0.417, 0.026, 0.175 - 0.060),
    "2026H1": (218.841, 153.059, 1.310, 24.504, 3.276, 1.896, 0.635, 0.410, -0.241, 0.011, 0.131 - 0.047),
}


def core_history():
    out = {}
    for k, (rev, cost, ta, se, ad, rd, oi, ci, ai, di, no) in HIST.items():
        e = rev - cost - ta - se - ad - rd + oi + ci + ai + di + no
        out[k] = (rev, e, e - ci - ai)
    h2 = tuple(a - b for a, b in zip(out["2025"], out["2025H1"]))
    out["2025H2"] = h2
    out["TTM(2025H2+2026H1)"] = tuple(a + b for a, b in zip(h2, out["2026H1"]))
    return out


if __name__ == "__main__":
    main()
