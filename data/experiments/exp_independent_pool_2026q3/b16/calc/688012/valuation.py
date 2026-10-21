# -*- coding: utf-8 -*-
"""中微公司（688012）独立估值（OI-291 池内独立审计 b16）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在脚本内，来源见同目录正文
companies/688012_中微公司.md 的「来源」一节。

方法：经济口径（研发全额费用化、股份支付计入成本）的所有者收益 DCF，
2026H2 + 2027-2031 显性期 + 2032-2036 线性衰减期 + 2.5% 永续；
股权价值 = 经营现金流现值 + 经调整净现金 + 非经营资产 − 少数股东权益。
经调整净现金为正，按无杠杆口径全额扣除有息负债。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 278.50                # 2026-10-20 收盘
SHARES = 9.57842348           # 亿股；含 2026-06-18 登记的购买资产发行 10,488,545 股与
                              # 2026-07-02 登记的配套募资 5,156,765 股；6-30 库存股为 0
VAL_DATE = date(2026, 10, 20)
COE = 0.09
G_T = 0.025                   # 永续增长

# ---------------------------------------------------------------- 报表输入
REV_2025 = 123.846            # 2025 营业收入
REV_H1_2026 = 66.913
# H1 2026 报表口径经常性核心 EBIT（营收−成本−税金附加−销售−管理−研发
# +经常性其他收益 0.573−信用与资产减值），2026H1_report 第 90-91 页、第 8 页
CORE_EBIT_H1_2026 = 66.913 - 40.321 - 0.382 - 2.585 - 2.626 - 13.096 + 0.573 - 0.330 - 0.103
CAP_RD_H1_2026 = 6.888        # 资本化研发投入（第 27-28 页）
AMORT_DEV_H1_2026 = 1.199     # 内部开发技术摊销（第 152 页）
ECON_EBIT_H1_2026 = CORE_EBIT_H1_2026 - CAP_RD_H1_2026 + AMORT_DEV_H1_2026

# 2025 年经济口径（2025_annual_report 第 57、204、221 页；非经常性政府补助 0.387）
CORE_EBIT_2025 = 123.846 - 75.341 - 0.683 - 4.985 - 4.779 - 24.754 + (2.574 - 0.387) - 0.266 - 0.960
ECON_EBIT_2025 = CORE_EBIT_2025 - 10.452 + 1.751

# 资产负债表 2026-06-30（第 86-88、129、157-160 页）
CASH = 97.682
RESTRICTED = 0.243
STRUCT = 6.712
DEBT = 1.39 + 2.5444 + 4.817 + 0.1549 + 0.1385   # 短借+一年内到期长借+长借+租赁
NWC_0630 = (1.690 + 30.578 + 0.893 + 0.872 + 76.660 + 0.096 + 8.000) \
    - (24.574 + 27.723 + 3.201 + 1.198 + 4.639 + 2.073)
RESERVE_RATE = 0.05           # 经营备付：5% 年收入


def net_cash_adj(rev2026=166.0):
    return CASH - RESTRICTED + STRUCT - DEBT - RESERVE_RATE * rev2026


# ---------------------------------------------------------------- 非经营资产
TJ_SHARES0 = 20516305                                  # 出售股票资产公告（2026-006）
TJ_SOLD_FRAC = 69887875.59 / 501985662.38              # H1 减少投资 / 期初账面（第 145 页）
TJ_SHARES = TJ_SHARES0 * (1 - TJ_SOLD_FRAC)            # 约 1,766 万股
TJ_PRICE = 546.00                                      # 拓荆科技 2026-10-20 收盘
TJ_BASIS_PS = 1.45e8 / TJ_SHARES0                      # 最初投资成本 1.45 亿（第 38 页）
TJ_DISC = 0.05                                         # 大额减持折价
TAX_GAIN = 0.15                                        # 高新技术企业税率


def tuojing_value(price=TJ_PRICE):
    p = price * (1 - TJ_DISC)
    return TJ_SHARES * (p - TAX_GAIN * (p - TJ_BASIS_PS)) / 1e8


OTHER_ASSOC_BOOK = 21.893 - 7.810      # 长投中拓荆以外的联营（智微攀峰 7.48 等）
NCFA_LISTED = 15.99                    # 其他非流动金融资产中上市公司股权（第 38-39 页）
NCFA_LISTED_COST = 5.20
NCFA_LISTED_MARK = 0.65                # 6-30 后科创 50 回落约 39%，按 −35% 计
NCFA_UNLISTED = 32.051 - 15.99
PREPAID_INV = 3.00                     # 其他非流动资产中预付投资款（第 157 页）
FUND_FEE_DRAG = 1.0                    # 智微系关联基金管理费拖累（承诺 7.35+14.7 亿）


def non_operating():
    listed = NCFA_LISTED * NCFA_LISTED_MARK
    listed_net = listed - TAX_GAIN * max(listed - NCFA_LISTED_COST, 0.0)
    return {
        "拓荆科技 1,766 万股（10-20 价×95%，扣 15% 税）": tuojing_value(),
        "其他联营企业（账面×0.85）": OTHER_ASSOC_BOOK * 0.85,
        "上市公司股权类金融资产（×0.65，扣税）": listed_net,
        "非上市股权类金融资产（×0.80）": NCFA_UNLISTED * 0.80,
        "预付投资款": PREPAID_INV,
        "关联基金管理费拖累": -FUND_FEE_DRAG,
    }


MINORITY = 0.2327 * 24.3649 + 0.10    # 众硅 23.27% 按交易作价 + 其他子公司少数股东

# ---------------------------------------------------------------- 情景
# g: 2027-2031 收入增速；m: 2027-2031 经济口径 EBIT 率；2032-2036 线性过渡到 g_T / mT
# t: 有效税率 2026 t26 → 2031 tT 线性；nwc/fix: 每增加 1 元收入的营运资本/净固定资本
# nwc_ye: 2026 年末营运资本/收入（含众硅）；ronic: 永续期增量资本回报
SCEN = {
    "bear": dict(p=0.25, rev26=160.0, g=[0.06, 0.03, 0.12, 0.12, 0.10],
                 m26=0.045, m=[0.040, 0.045, 0.070, 0.090, 0.105], mT=0.14,
                 t26=0.03, tT=0.12, nwc=0.35, fix=0.12, nwc_ye=0.37, ronic=0.15,
                 desc="2027-2028 大陆扩产消化，收入 2027/2028 仅 +6%/+3%，2031 年约 241 亿；"
                      "竞争与客户折扣压毛利，研发占比下降慢，终值经济口径 EBIT 率 14%，税率 12%，"
                      "新增收入的再投资 47%，永续增量回报 15%"),
    "base": dict(p=0.50, rev26=166.0, g=[0.27, 0.22, 0.18, 0.15, 0.12],
                 m26=0.055, m=[0.085, 0.110, 0.130, 0.150, 0.165], mT=0.20,
                 t26=0.03, tT=0.10, nwc=0.28, fix=0.12, nwc_ye=0.34, ronic=0.20,
                 desc="2026 收入 166 亿（+34%），2027-2031 增速 27/22/18/15/12%，2031 年约 391 亿、2036 年约 530 亿；"
                      "研发占比由 28% 降到约 15%，毛利率回到 41-42%，终值经济口径 EBIT 率 20%，税率 10%；"
                      "新增收入的再投资 40%，永续增量回报 20%"),
    "bull": dict(p=0.25, rev26=171.0, g=[0.33, 0.27, 0.22, 0.18, 0.15],
                 m26=0.062, m=[0.100, 0.135, 0.165, 0.190, 0.210], mT=0.25,
                 t26=0.03, tT=0.08, nwc=0.22, fix=0.10, nwc_ye=0.32, ronic=0.25,
                 desc="国产替代加平台化（薄膜、CMP、量检测）持续放量，2027-2031 增速 33/27/22/18/15%，"
                      "2031 年约 478 亿、2036 年约 685 亿（约 95 亿美元）；终值经济口径 EBIT 率 25%（接近 Lam），"
                      "税率 8%，新增收入的再投资 32%，永续增量回报 25%"),
}
EXTRA_CAPEX = {2026: 2.0, 2027: 4.0, 2028: 3.0}   # 临港二期（固定资产 17 亿）、广州、成都基地先行投入


def paths(s, g_override=None, mT_override=None, m_shift=0.0):
    years = list(range(2026, 2037))
    g5list = list(g_override) if g_override is not None else list(s["g"])
    mT = (s["mT"] if mT_override is None else mT_override) + m_shift
    g = [s["rev26"] / REV_2025 - 1] + g5list
    g5 = g5list[-1]
    for k in range(1, 6):
        g.append(g5 + (G_T - g5) * k / 5)
    m = [s["m26"]] + [x + m_shift for x in s["m"]]
    m5 = s["m"][-1] + m_shift
    for k in range(1, 6):
        m.append(m5 + (mT - m5) * k / 5)
    t = [s["t26"] + (s["tT"] - s["t26"]) * min(i, 5) / 5 for i in range(len(years))]
    rev, r = [], REV_2025
    for gi in g:
        r *= 1 + gi
        rev.append(r)
    return years, g, m, t, rev, mT


def yearfrac(d):
    return (d - VAL_DATE).days / 365.25


def value(s, r=COE, detail=False, g_override=None, mT_override=None, tj_price=TJ_PRICE, m_shift=0.0):
    years, g, m, t, rev, mT = paths(s, g_override, mT_override, m_shift)
    k = s["nwc"] + s["fix"]
    pv, rows, prev = 0.0, [], REV_2025
    for i, y in enumerate(years):
        ebit = rev[i] * m[i]
        if y == 2026:
            nopat = (ebit - ECON_EBIT_H1_2026) * (1 - t[i])           # 只计 H2
            reinv = (s["nwc_ye"] * rev[i] - NWC_0630) + 0.5 * s["fix"] * (rev[i] - prev) \
                + EXTRA_CAPEX.get(y, 0.0)
            tt = yearfrac(date(2026, 10, 1))
        else:
            nopat = ebit * (1 - t[i])
            reinv = k * (rev[i] - prev) + EXTRA_CAPEX.get(y, 0.0)
            tt = yearfrac(date(y, 7, 1))
        oe = nopat - reinv
        df = (1 + r) ** (-tt)
        pv += oe * df
        rows.append(dict(year=y, rev=rev[i], g=g[i], m=m[i], t=t[i], nopat=nopat, reinv=reinv, oe=oe, df=df))
        prev = rev[i]
    nopat_T = rev[-1] * (1 + G_T) * mT * (1 - s["tT"])
    reinv_rate_T = G_T / s["ronic"]
    tv = nopat_T * (1 - reinv_rate_T) / (r - G_T)
    pv_tv = tv * (1 + r) ** (-yearfrac(date(2036, 12, 31)))
    nca = net_cash_adj(s["rev26"])
    nop_parts = non_operating()
    nop = sum(nop_parts.values()) - tuojing_value() + tuojing_value(tj_price)
    eq = pv + pv_tv + nca + nop - MINORITY
    v = eq / SHARES
    if detail:
        return dict(rows=rows, pv_explicit=pv, tv=tv, pv_tv=pv_tv, nca=nca, nop=nop, eq=eq, v=v,
                    tv_share=pv_tv / (pv + pv_tv), ops=pv + pv_tv)
    return v


def weighted(r=COE, probs=None, **kw):
    probs = probs or {k: SCEN[k]["p"] for k in SCEN}
    return sum(probs[k] * value(SCEN[k], r, **kw) for k in SCEN)


def bisect(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) > 0) == (flo > 0):
            lo, flo = mid, f(mid)
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    return bisect(lambda r: value(SCEN["base"], r) - PRICE, 0.03, 0.09)


def reverse_growth(scen="base"):
    """2027-2031 统一增速 x（其余假设不变）使 V = 现价。"""
    s = SCEN[scen]
    return bisect(lambda x: value(s, g_override=[x] * 5) - PRICE, 0.0, 0.80)


def reverse_margin():
    """基准增长下，终值经济口径 EBIT 率需达到多少才使 V = 现价。"""
    s = SCEN["base"]
    return bisect(lambda mt: value(s, mT_override=mt) - PRICE, 0.10, 0.90)


def normalized_np_2026():
    """2026 正常化归母净利（报表口径，研发按公司资本化照计）。
    核心 EBIT（报表口径）+ 权益法投资收益 + 净利息与结构性存款收益，按 5% 正常化税率，
    加回少数股东分担的亏损。"""
    out = {}
    spec = {  # 报表口径核心 EBIT、权益法收益、净利息、少数股东分担
        "bear": (18.6, 1.4, 0.9, 0.4),
        "base": (21.5, 1.6, 0.9, 0.5),
        "bull": (24.3, 1.8, 0.9, 0.5),
    }
    for k, (ebit, eq_inc, interest, mi) in spec.items():
        pre = ebit + eq_inc + interest
        out[k] = pre * (1 - 0.05) + mi
    return out


def econ_np_2026_base():
    """经济口径（资本化研发全额费用化）2026 归母净利：报表口径减（资本化 15.0 − 摊销 2.6）×（1−5%）。"""
    return normalized_np_2026()["base"] - (15.0 - 2.6) * 0.95


# (条件, 时点, 触发后情景概率, 触发后 2027 年起各情景经济口径 EBIT 率平移)
FALSIFIERS = [
    ("2026 年收入 < 155 亿元，或 2027Q1 收入同比 < 10%（大陆扩产消化提前）", "2027-04-30",
     {"bear": 0.50, "base": 0.40, "bull": 0.10}, 0.0),
    ("2026 年报经济口径营业利润率（报表核心 EBIT − 资本化研发 + 开发技术摊销）/收入 < 3%，"
     "或研发资本化比例 > 40%", "2027-04-30", None, -0.02),
    ("2026 年或 2027H1 综合毛利率 < 37%（客户折扣与国产竞争压价）", "2027-08-31", None, -0.03),
    ("中微被美国商务部列入实体清单或核心进口零部件断供（任何时点）", "2027-12-31",
     {"bear": 0.60, "base": 0.35, "bull": 0.05}, 0.0),
    ("（向上）2027 年收入 ≥ 230 亿元且经济口径营业利润率 ≥ 12%", "2028-04-30",
     {"bear": 0.10, "base": 0.40, "bull": 0.50}, 0.0),
]


def main():
    print("== 输入核对 ==")
    print(f"H1 2026 报表核心 EBIT {CORE_EBIT_H1_2026:.2f}，经济口径 {ECON_EBIT_H1_2026:.2f}"
          f"（{ECON_EBIT_H1_2026 / REV_H1_2026:.1%}）；2025 报表核心 {CORE_EBIT_2025:.2f}，"
          f"经济口径 {ECON_EBIT_2025:.2f}（{ECON_EBIT_2025 / REV_2025:.1%}）")
    print(f"6-30 营运资本 {NWC_0630:.2f}；有息负债 {DEBT:.2f}；经调整净现金（基准）{net_cash_adj():.2f}")
    nop = non_operating()
    for k, v in nop.items():
        print(f"  非经营资产 {k}: {v:.2f}")
    print(f"  合计 {sum(nop.values()):.2f}；拓荆剩余股数 {TJ_SHARES / 1e4:.0f} 万股；少数股东 {MINORITY:.2f}")
    print()
    res = {}
    for k, s in SCEN.items():
        d = value(s, detail=True)
        res[k] = d
        print(f"== {k}（p={s['p']}）V = {d['v']:.2f} 元/股；经营价值 {d['ops']:.1f}（显性 {d['pv_explicit']:.1f}，"
              f"终值现值 {d['pv_tv']:.1f}，终值占 {d['tv_share']:.0%}）+ 净现金 {d['nca']:.1f} + 非经营 {d['nop']:.1f}"
              f" − 少数 {MINORITY:.1f} = 股权 {d['eq']:.1f} 亿")
        for row in d["rows"]:
            tag = "（仅 H2）" if row["year"] == 2026 else ""
            print(f"  {row['year']}{tag} 收入 {row['rev']:6.1f} 增速 {row['g']:6.1%} 经济EBIT率 {row['m']:5.1%} "
                  f"税 {row['t']:4.1%} NOPAT {row['nopat']:6.1f} 再投资 {row['reinv']:6.1f} 所有者收益 {row['oe']:6.1f}")
    vw = weighted()
    pv = PRICE / vw
    band = "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"
    print()
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.2f}（{band}）")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}；10%：加权 V = {weighted(0.10):.2f}")
    for k in SCEN:
        print(f"  {k}: 8% {value(SCEN[k], 0.08):.2f} / 9% {value(SCEN[k]):.2f} / 10% {value(SCEN[k], 0.10):.2f}")
    print(f"现价隐含回报（基准情景现金流）= {implied_irr():.2%}")
    gb = reverse_growth("base")
    gbu = reverse_growth("bull")
    rb = paths(SCEN["base"], g_override=[gb] * 5)[4]
    rbu = paths(SCEN["bull"], g_override=[gbu] * 5)[4]
    print(f"反向 DCF：基准利润率下需 2027-2031 年收入年增 {gb:.1%}（2031 年收入约 {rb[5]:.0f} 亿，"
          f"2036 年约 {rb[-1]:.0f} 亿）；牛市利润率下需 {gbu:.1%}（2031 年约 {rbu[5]:.0f} 亿，2036 年约 {rbu[-1]:.0f} 亿）")
    print(f"反向 DCF：基准增长下需终值经济口径 EBIT 率 {reverse_margin():.1%}")
    print(f"拓荆股价 ±30% 对加权 V 的影响：{weighted(tj_price=TJ_PRICE * 0.7):.2f} / {weighted(tj_price=TJ_PRICE * 1.3):.2f}")
    print()
    nn = normalized_np_2026()
    print("2026 正常化归母净利（报表口径）：" + "，".join(f"{k} {v:.1f}" for k, v in nn.items())
          + f"；经济口径基准 {econ_np_2026_base():.1f}")
    print(f"市值 {PRICE * SHARES:.1f} 亿；市值/2026 基准正常化归母净利 {PRICE * SHARES / nn['base']:.0f} 倍；"
          f"/经济口径 {PRICE * SHARES / econ_np_2026_base():.0f} 倍")
    bd = res["base"]["rows"]
    reinv = sum(r_["reinv"] for r_ in bd if 2027 <= r_["year"] <= 2031)
    nopat = sum(r_["nopat"] for r_ in bd if 2027 <= r_["year"] <= 2031)
    nopat26_full = SCEN["base"]["rev26"] * SCEN["base"]["m26"] * (1 - SCEN["base"]["t26"])
    d_nopat = bd[5]["nopat"] - nopat26_full
    print(f"基准 2027-2031 再投资率 {reinv / nopat:.0%}，增量回报（ΔNOPAT/累计再投资）{d_nopat / reinv:.0%}；"
          f"永续再投资率 {G_T / SCEN['base']['ronic']:.1%}，增量回报 {SCEN['base']['ronic']:.0%}")
    print()
    print("证伪条件触发后的独立 V：")
    for cond, ddl, probs, shift in FALSIFIERS:
        print(f"  [{ddl}] {cond} → V = {weighted(probs=probs, m_shift=shift):.2f}")
    print()
    for x in (0.75, 0.90, 1.10):
        print(f"P/V = {x:.2f} 对应价格 {x * vw:.1f}")


if __name__ == "__main__":
    main()
