#!/usr/bin/env python3
"""顺络电子（002138）独立估值：所有者收益 DCF。

经调整净现金为负，按框架以有杠杆口径为准（经调整净负债按现规模滚动、不还本，扣其税后利息现值），
另列全额扣除口径作对照。金额单位亿元，每股价值元/股。输入全部写在脚本内：
    python3 valuation.py
数据出处：2026 半年报（资产负债表第 57～59 页、利润表第 62～63 页、长期借款第 166 页、
购买少数股东权益第 178 页、重要非全资子公司第 189 页）、2025 年报、数据包；假设见正文第五节。
"""

# ---------------------------------------------------------------- 快照
PRICE = 39.75            # 2026-10-20 收盘（腾讯日线）
SHARES = 8.0632          # 亿股，总股本（含回购专户股份）
TREASURY = 0.0772948     # 亿股，回购专户 7,729,480 股，用途为股权激励/员工持股，未公告注销
COE = 0.09
DAYS_TO_YE = 72          # 2026-10-20 至 2026-12-31

# ---------------------------------------------------------------- 资产负债（2026-06-30）
CASH = 4.3616            # 货币资金
RESTRICTED = 0.0003      # 保证金（受限）
REV_TTM = 73.80
OP_CASH = 0.02 * REV_TTM # 经营备付：TTM 营收的 2%
DECLARED_DIV = 0.0       # 6-30 无已宣派未付股利（2025 年度股利已于 4 月支付）
DEBT = 7.1202 + 26.5923 + 6.7001 + 0.0709   # 短期借款+长期借款+一年内到期非流动负债（含租赁）+租赁负债
NET_CASH_ADJ = CASH - RESTRICTED - OP_CASH - DECLARED_DIV - DEBT   # 无杠杆口径经调整净现金（负数）
NONOP_BOOK = 2.8148 + 1.5100   # 长期股权投资（联营与基金）+ 其他权益工具投资（基金）
NONOP = NONOP_BOOK * 0.8       # 基金份额流动性与费用折价 20%
R_DEBT = 0.025           # 实际平均利率：TTM 利息 0.878 / 五个季末平均有息负债 36.4 = 2.4%；H1 年化 2.55%；长借 2.29%～2.9%
TAX_SHIELD = 0.15        # 高新技术企业税率
AT_INT = -NET_CASH_ADJ * R_DEBT * (1 - TAX_SHIELD)   # 经调整净负债的税后利息（亿元/年）

# ---------------------------------------------------------------- 情景
# np26：2026 正常化归母净利（含净利息；剔除补助等非经常、银价周期与股份支付超常摊销）
# g：2027～2031 经营所有者收益（归母，加回税后利息）增速；2032～2036 线性收敛到 g_term
# roic：增量资本回报，再投资率 = 次年增速 / roic；roic_term：终值期增量回报
# leak：子公司员工持股回购的净现金成本（2027 年值，随收益增长），少数股东损益之外的隐性激励成本
SCEN = {
    'bear': dict(p=0.25, np26=9.6, g=[0.05, 0.06, 0.06, 0.05, 0.05], g_term=0.020,
                 roic=0.12, roic_term=0.10, leak=1.0),
    'base': dict(p=0.50, np26=11.0, g=[0.14, 0.13, 0.12, 0.11, 0.10], g_term=0.025,
                 roic=0.18, roic_term=0.12, leak=0.6),
    'bull': dict(p=0.25, np26=12.0, g=[0.22, 0.20, 0.17, 0.14, 0.12], g_term=0.025,
                 roic=0.25, roic_term=0.15, leak=0.4),
}
YEARS = list(range(2027, 2037))
OFF = DAYS_TO_YE / 365


def growth_path(s, flat=None):
    if flat is not None:
        return [flat] * 10
    g5 = list(s['g'])
    return g5 + [g5[-1] + (s['g_term'] - g5[-1]) * k / 5 for k in range(1, 6)]


def value(s, r=COE, at_int=None, net_cash=None, leak=None, flat=None, detail=False):
    """返回经营价值与两种口径的每股 V。利息现值与经营现金流用同一折现率 r。"""
    at_int = AT_INT if at_int is None else at_int
    net_cash = NET_CASH_ADJ if net_cash is None else net_cash
    leak = s['leak'] if leak is None else leak
    gs = growth_path(s, flat)
    e26 = s['np26'] + AT_INT                      # 经营所有者收益基数
    es, e = [], e26
    for g in gs:
        e *= 1 + g
        es.append(e)
    e27 = es[0]
    nxt = gs[1:] + [s['g_term']]
    rr = [nxt[i] / s['roic'] for i in range(9)] + [s['g_term'] / s['roic_term']]
    # 2026 下半年（6-30 资产负债表之后）所有者收益，视作现值日附近
    pv = 0.5 * e26 * (1 - gs[0] / s['roic']) - 0.5 * leak * e26 / e27
    rows = []
    for i, y in enumerate(YEARS):
        oe = es[i] * (1 - rr[i]) - leak * es[i] / e27
        d = (1 + r) ** ((y - 2027) + 0.5 + OFF)
        pv += oe / d
        rows.append((y, gs[i], es[i], rr[i], oe, oe / d))
    e37 = es[-1] * (1 + s['g_term'])
    oe37 = e37 * (1 - s['g_term'] / s['roic_term']) - leak * e37 / e27
    pv_tv = oe37 / (r - s['g_term']) / (1 + r) ** (9.5 + OFF)
    pv_op = pv + pv_tv
    eq_lev = pv_op - at_int / r + NONOP
    eq_full = pv_op + net_cash + NONOP
    out = dict(e26=e26, pv_op=pv_op, pv_tv=pv_tv, tv_share=pv_tv / pv_op,
               eq_lev=eq_lev, eq_full=eq_full, v_lev=eq_lev / SHARES, v_full=eq_full / SHARES,
               v_lev_ex=eq_lev / (SHARES - TREASURY), rr_avg=sum(rr[:5]) / 5)
    if detail:
        out['rows'] = rows
    return out


def weighted(r=COE, key='v_lev', probs=None, scen=None, **kw):
    scen = scen or SCEN
    probs = probs or {k: v['p'] for k, v in scen.items()}
    return sum(probs[k] * value(s, r=r, **kw)[key] for k, s in scen.items())


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
    print(f"现价 {PRICE}，总股本 {SHARES} 亿股（剔除回购专户 {SHARES - TREASURY:.4f}），股权成本 {COE:.0%}")
    print(f"经调整净现金（无杠杆口径）= {CASH} - {RESTRICTED} - 经营备付 {OP_CASH:.3f} - 有息负债 {DEBT:.3f} = {NET_CASH_ADJ:.2f} 亿")
    print(f"非经营资产 = 账面 {NONOP_BOOK:.2f} × 0.8 = {NONOP:.2f} 亿；经调整净负债税后利息 {AT_INT:.3f} 亿/年，"
          f"9% 永续现值 {AT_INT / COE:.2f} 亿")
    print()
    res = {}
    for k, s in SCEN.items():
        v = value(s, detail=True)
        res[k] = v
        print(f"[{k}] 概率 {s['p']:.2f}；2026 正常化归母 {s['np26']:.1f} 亿，经营所有者收益基数 {v['e26']:.2f} 亿；"
              f"增量回报 {s['roic']:.0%}，2027-31 平均再投资率 {v['rr_avg']:.0%}；员工股权净成本 {s['leak']:.1f} 亿/年；终值增速 {s['g_term']:.1%}")
        print("   年份   增速   经营收益  再投资率  所有者收益   现值")
        for y, g, e, rr, oe, pv in v['rows']:
            print(f"   {y}  {g:5.1%}  {e:8.2f}  {rr:6.0%}  {oe:9.2f}  {pv:7.2f}")
        print(f"   经营价值 {v['pv_op']:.1f} 亿（终值现值占 {v['tv_share']:.0%}）")
        print(f"   有杠杆：股权 {v['eq_lev']:.1f} 亿 → V = {v['v_lev']:.2f} 元（剔除回购专户 {v['v_lev_ex']:.2f}）；"
              f"全额扣除：股权 {v['eq_full']:.1f} 亿 → V = {v['v_full']:.2f} 元")
    print()
    vw = weighted()
    vw_full = weighted(key='v_full')
    vw_ex = weighted(key='v_lev_ex')
    print(f"三情景 V（有杠杆）：熊 {res['bear']['v_lev']:.2f} / 基准 {res['base']['v_lev']:.2f} / 牛 {res['bull']['v_lev']:.2f}")
    print(f"三情景 V（全额扣除）：熊 {res['bear']['v_full']:.2f} / 基准 {res['base']['v_full']:.2f} / 牛 {res['bull']['v_full']:.2f}")
    print(f"加权 V（有杠杆，采用）= {vw:.2f} 元，P/V = {PRICE / vw:.2f}")
    print(f"加权 V（剔除回购专户）= {vw_ex:.2f} 元，P/V = {PRICE / vw_ex:.2f}")
    print(f"加权 V（全额扣除净负债）= {vw_full:.2f} 元，P/V = {PRICE / vw_full:.2f}")
    for r in (0.08, 0.10):
        print(f"股权成本 {r:.0%}：加权 V（有杠杆）= {weighted(r=r):.2f}（P/V {PRICE / weighted(r=r):.2f}）；"
              f"基准 {value(SCEN['base'], r=r)['v_lev']:.2f}；全额扣除加权 {weighted(r=r, key='v_full'):.2f}")
    base = SCEN['base']
    irr = solve(lambda r: value(base, r=r)['v_lev'], 0.03, 0.15, PRICE)
    irr_full = solve(lambda r: value(base, r=r)['v_full'], 0.03, 0.15, PRICE)
    print(f"现价隐含回报（基准现金流）：有杠杆 {irr:.2%}；全额扣除 {irr_full:.2%}")
    g10 = solve(lambda g: value(base, flat=g)['v_lev'], 0.0, 0.5, PRICE)
    g5 = solve(lambda g: value(dict(base, g=[g] * 5))['v_lev'], 0.0, 0.6, PRICE)

    def v_perp(g):
        e27 = (base['np26'] + AT_INT) * (1 + g)
        return ((e27 * (1 - g / base['roic_term'])) / (COE - g) - AT_INT / COE + NONOP) / SHARES
    gp = solve(v_perp, 0.0, 0.0899, PRICE)
    print(f"反向 DCF：现价隐含 2027～2036 年经营所有者收益每年 {g10:.1%}（增量回报 18%，其后 2.5%）；"
          f"或 2027～2031 年每年 {g5:.1%} 后五年收敛；或自 2027 年永续 {gp:.2%}（增量回报 12%）")
    print()
    mcap = PRICE * SHARES
    ebit_ttm = 11.926 + 0.878
    ev = mcap - NET_CASH_ADJ + 6.02 - NONOP_BOOK
    print(f"交叉验证：市值 {mcap:.1f} 亿；EV（加经调整净负债与少数股东权益账面 6.02，减非经营资产账面）{ev:.1f} 亿，"
          f"EV/EBIT(TTM {ebit_ttm:.2f}) = {ev / ebit_ttm:.1f}x")
    print(f"股息率 {0.80 / PRICE:.2%}；2025 年分红 6.39 + 回购 1.00 = 7.39 亿，占市值 {7.39 / mcap:.2%}")
    print(f"PE(TTM 归母 9.82) {mcap / 9.82:.1f}x；PE(基准正常化 11.0) {mcap / 11.0:.1f}x；PB(归母权益 65.65) {mcap / 65.65:.2f}x")
    print(f"V 不变时各档价格：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}～{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}～{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")
    print()
    at_hi = 45.0 * 0.035 * (1 - TAX_SHIELD)
    fals = [
        ("证伪 1：三季报单季毛利率<33.5% 或单季归母<2.6 亿（2026-10-30）", weighted(probs={'bear': 0.45, 'base': 0.45, 'bull': 0.10})),
        ("证伪 2：2026 扣非归母<9.3 亿 或 经营现金流<12 亿（2027-04-30）", weighted(probs={'bear': 0.60, 'base': 0.40, 'bull': 0.0})),
        ("证伪 3：2027 中报营收同比<8% 且毛利率<34%（2027-08-31）", weighted(probs={'bear': 0.80, 'base': 0.20, 'bull': 0.0})),
        ("证伪 4：经调整净负债>45 亿 且实际利率>3.5%（2027-08-31）", weighted(at_int=at_hi)),
        ("证伪 5：子公司员工股权回购现金>3 亿/年 或核心业务新设员工持股>10%（2027-12-31）",
         weighted(scen={k: dict(s, leak=2 * s['leak']) for k, s in SCEN.items()})),
        ("上行：2027 中报营收同比>25% 且毛利率≥36.5%（2027-08-31）", weighted(probs={'bear': 0.10, 'base': 0.50, 'bull': 0.40})),
    ]
    for name, v in fals:
        print(f"{name} → V = {v:.2f}（P/V {PRICE / v:.2f}）")


if __name__ == '__main__':
    main()
