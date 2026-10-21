# -*- coding: utf-8 -*-
"""688120 华海清科 独立估值（OI-291 b16）。

金额单位亿元，每股价值元/股。输入全部写在脚本内，`python3 valuation.py` 复现正文与 json 的全部数字。
口径：所有者收益 = 核心经营 NOPAT − 营运资本增加 − 净资本开支（资本开支 − 折旧摊销）。
核心经营利润 = 营收 − 成本 − 税金 − 销售/管理/研发 + 经常性其他收益（软件退税、增值税加计抵减）+ 减值；
不含理财收益、公允价值变动、利息与非经常性政府补助（这些对应的现金已计入净现金或按一次性剔除）。
股份支付按营收 1.5% 的常态水平计入费用（2026 年激励计划的会计摊销另列，不再另做摊薄）。
"""

PRICE = 218.51
SHARES = 5.12361946          # 上市公告书第 7 页：发行后总股本 512,361,946 股（含回购专户股份）
TREASURY = 0.00954151        # 回购专户 954,151 股，用途为股权激励/员工持股/转债，未公告注销
COE = 0.09
G = 0.025
T_VAL = 2026.80              # 估值日 2026-10-20（按年小数）

# ---------- 经调整净现金：2026-06-30 资产负债表 + 6-30 之后的资本事件 ----------
CASH = 23.6592               # 货币资金，含定期存款及应收利息 6.0020（2026H1 第 113、163 页）
TFA = 19.6643                # 交易性金融资产，均为债务工具（2026H1 第 113 页）
MARGIN_DEP = 0.7864          # 保证金，受限（2026H1 第 163 页）
DEBT = 1.7399 + 1.2055 + 0.7939 + 0.1103   # 长期借款、一年内到期长期借款(含息)、租赁负债、一年内到期租赁负债（第 148-150 页）
ACQ_PAYABLE = 1.3060         # 其他应付款-购买股权款（第 148 页）
OP_FLOAT = 3.0               # 经营备付，约 2026E 营收的 5%
PLACEMENT_NET = 37.7312      # 定增募资净额，2026-09-24 到账（上市公告书第 2、15 页）
VEST_CASH = 1550311 * 30.611 / 1e8   # 2023 年激励首次授予第二个归属期 7-27 归属 1,550,311 股 × 30.611 元
RELATED_FIN_CO_DEPOSIT = 0.0 # 关联财务公司（天府清源控股集团财务公司）存款：2025 年末、2026-06-30 均为 0
NET_CASH_ADJ = (CASH + TFA - MARGIN_DEP - DEBT - ACQ_PAYABLE - OP_FLOAT
                + PLACEMENT_NET + VEST_CASH)
NON_OP_BOOK = 3.4124 + 0.8686 + 0.0217      # 长期股权投资、其他非流动金融资产、其他权益工具投资
NON_OP = 0.8 * NON_OP_BOOK                   # 产业基金与参股按账面八折

# ---------- 2026 上半年实际（核心经营口径） ----------
EBIT_H1 = 6.112              # 26.432-15.069-0.179-1.108-1.720-2.750+(1.143-0.275)+(-0.226-0.136)
TAX_H1 = 0.155               # 上半年实际税率（研发加计扣除在年末汇算）
NWC_0630 = 16.85             # 经营性营运资本 2026-06-30
FIN_INCOME_2026_AT = 0.64    # 2026 年净利息与理财收益（税后）：上半年 0.27 税前 + 下半年约 0.48 税前，按 15% 税
REV_2025 = 46.482
YEARS = list(range(2027, 2036))

SCEN = {
    'bear': dict(p=0.25,
        rev={2026: 56.0, 2027: 66.0, 2028: 57.0, 2029: 60.0, 2030: 66.0, 2031: 71.0, 2032: 75.0, 2033: 78.0, 2034: 80.0, 2035: 82.0},
        m={2026: 0.215, 2027: 0.195, 2028: 0.150, 2029: 0.155, 'lr': 0.165},
        tax={2026: 0.105, 2027: 0.12, 'lr': 0.14},
        nwc_end26=0.30, nwc_inc=0.28,
        capex={'H2': 1.8, 2027: 9.0, 2028: 6.0, 2029: 2.0, 2030: 1.0}, fcap=0.25, ronic=0.12,
        norm_m26=0.180),
    'base': dict(p=0.50,
        rev={2026: 58.0, 2027: 74.0, 2028: 85.0, 2029: 93.0, 2030: 99.5, 2031: 105.0, 2032: 110.0, 2033: 114.0, 2034: 117.5, 2035: 120.5},
        m={2026: 0.220, 2027: 0.225, 2028: 0.210, 'lr': 0.210},
        tax={2026: 0.105, 2027: 0.11, 'lr': 0.125},
        nwc_end26=0.27, nwc_inc=0.25,
        capex={'H2': 1.8, 2027: 10.3, 2028: 9.9, 2029: 3.9, 2030: 2.0}, fcap=0.25, ronic=0.20,
        norm_m26=0.215),
    'bull': dict(p=0.25,
        rev={2026: 60.5, 2027: 82.0, 2028: 100.0, 2029: 116.0, 2030: 130.0, 2031: 142.0, 2032: 152.0, 2033: 160.0, 2034: 166.0, 2035: 170.0},
        m={2026: 0.225, 2027: 0.240, 2028: 0.235, 2029: 0.240, 'lr': 0.245},
        tax={2026: 0.105, 2027: 0.11, 'lr': 0.115},
        nwc_end26=0.25, nwc_inc=0.23,
        capex={'H2': 2.0, 2027: 11.0, 2028: 11.0, 2029: 6.0, 2030: 4.0}, fcap=0.25, ronic=0.25,
        norm_m26=0.235),
}


def get(d, y):
    return d[y] if y in d else d['lr']


def run(s, r=COE, verbose=False):
    rev = s['rev']
    ebit26 = rev[2026] * get(s['m'], 2026)
    nopat26 = ebit26 * (1 - get(s['tax'], 2026))
    nopat_h2 = nopat26 - EBIT_H1 * (1 - TAX_H1)
    nwc26 = s['nwc_end26'] * rev[2026]
    dnwc_h2 = nwc26 - NWC_0630
    oe_h2 = nopat_h2 - dnwc_h2 - s['capex']['H2']
    flows = [(0.0, oe_h2)]
    rows = [('2026H2', rev[2026], nopat26, nopat_h2, dnwc_h2, s['capex']['H2'], oe_h2)]
    prev_rev = rev[2026]
    nopats = {2026: nopat26}
    reinv = {}
    for y in YEARS:
        rv = rev[y]
        nopat = rv * get(s['m'], y) * (1 - get(s['tax'], y))
        dnwc = s['nwc_inc'] * (rv - prev_rev)
        ncx = s['capex'][y] if y in s['capex'] else s['fcap'] * (rv - prev_rev)
        oe = nopat - dnwc - ncx
        flows.append(((y + 0.5) - T_VAL, oe))
        rows.append((str(y), rv, nopat, nopat, dnwc, ncx, oe))
        nopats[y] = nopat
        reinv[y] = dnwc + ncx
        prev_rev = rv
    nopat_T = rev[2035] * (1 + G) * s['m']['lr'] * (1 - s['tax']['lr'])
    oe_T = nopat_T * (1 - G / s['ronic'])
    tv = oe_T / (r - G)
    pv_flows = sum(cf / (1 + r) ** t for t, cf in flows)
    pv_tv = tv / (1 + r) ** ((2035 + 0.5) - T_VAL)
    eq = NET_CASH_ADJ + NON_OP + pv_flows + pv_tv
    yrs5 = range(2027, 2032)
    out = dict(eq=eq, v=eq / SHARES, v_ex=eq / (SHARES - TREASURY), pv_flows=pv_flows, pv_tv=pv_tv,
               tv_share=pv_tv / (pv_flows + pv_tv), rows=rows, nopat_T=nopat_T, oe_T=oe_T, nopats=nopats,
               reinv_rate=sum(reinv[y] for y in yrs5) / sum(nopats[y] for y in yrs5),
               inc_ret=(nopats[2031] - nopats[2026]) / sum(reinv[y] for y in yrs5),
               growth=[nopats[y] / nopats[y - 1] - 1 for y in yrs5])
    if verbose:
        print("  期间     营收   全年NOPAT  期内NOPAT   ΔNWC  净资本开支  所有者收益")
        for lab, rv, nf, n, dn, cx, oe in rows:
            print(f"  {lab:<7} {rv:6.1f} {nf:9.2f} {n:9.2f} {dn:7.2f} {cx:9.2f} {oe:10.2f}")
        print(f"  终值：2036 NOPAT {nopat_T:.2f}，再投资率 {G / s['ronic']:.1%}（RONIC {s['ronic']:.0%}），所有者收益 {oe_T:.2f}")
    return out


def weighted(r=COE, w=None):
    w = w or {k: s['p'] for k, s in SCEN.items()}
    return sum(w[k] * run(SCEN[k], r)['v'] for k in SCEN)


def implied_irr():
    mcap = PRICE * SHARES
    lo, hi = 0.026, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if run(SCEN['base'], mid)['eq'] > mcap:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(roic_inc=0.25, ronic_T=0.20):
    """现价隐含的 2027-2036 年 NOPAT 年增速：起点为基准 2026 年 NOPAT，再投资率 = g/增量回报(25%)，之后 2.5% 永续。"""
    mcap = PRICE * SHARES
    s = SCEN['base']
    base26 = s['rev'][2026] * s['m'][2026] * (1 - s['tax'][2026])

    def eqv(g):
        pv, n = 0.0, base26
        for k in range(1, 11):
            n *= (1 + g)
            pv += n * (1 - min(g / roic_inc, 0.95)) / (1 + COE) ** (k - 0.3)
        pv += n * (1 + G) * (1 - G / ronic_T) / (COE - G) / (1 + COE) ** (10 - 0.3)
        return pv + NET_CASH_ADJ + NON_OP
    lo, hi = 0.0, 0.8
    for _ in range(200):
        mid = (lo + hi) / 2
        if eqv(mid) < mcap:
            lo = mid
        else:
            hi = mid
    g = (lo + hi) / 2
    return g, base26, base26 * (1 + g) ** 10


def norm_np_2026(s):
    """2026 正常化归母净利（报表口径）：2026E 营收 × 跨周期核心利润率 ×（1−税率）+ 税后净利息；
    剔除非经常性补助与公允价值波动，股份支付按营收 1.5% 计。"""
    return s['rev'][2026] * s['norm_m26'] * (1 - s['tax'][2026]) + FIN_INCOME_2026_AT


if __name__ == '__main__':
    mcap = PRICE * SHARES
    print(f"市值 {mcap:.1f} 亿元（{PRICE} 元 × {SHARES:.4f} 亿股）")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f} 亿元 = 货币资金 {CASH} + 交易性金融资产 {TFA} − 保证金 {MARGIN_DEP} − 有息负债 {DEBT:.2f}"
          f" − 购买股权尾款 {ACQ_PAYABLE} − 经营备付 {OP_FLOAT} + 定增净额 {PLACEMENT_NET} + 归属认购款 {VEST_CASH:.2f}")
    print(f"关联财务公司存款 {RELATED_FIN_CO_DEPOSIT:.2f}；非经营资产 {NON_OP:.2f}（账面 {NON_OP_BOOK:.2f} 八折）")
    res = {}
    for k, s in SCEN.items():
        print(f"\n[{k}] 概率 {s['p']:.0%}")
        o = run(s, verbose=True)
        res[k] = o
        print(f"  经营现值 {o['pv_flows']:.1f}，终值现值 {o['pv_tv']:.1f}（终值占经营价值 {o['tv_share']:.0%}）")
        print(f"  股权价值 {o['eq']:.1f} 亿元 → V = {o['v']:.2f} 元/股（剔除回购专户 {o['v_ex']:.2f}）")
        print(f"  2027-2031 NOPAT 增速 {', '.join(f'{x:.1%}' for x in o['growth'])}；再投资率 {o['reinv_rate']:.0%}；增量回报 {o['inc_ret']:.0%}")
        print(f"  2026 正常化归母净利 {norm_np_2026(s):.2f} 亿元")
    vw = weighted()
    vw_ex = sum(SCEN[k]['p'] * res[k]['v_ex'] for k in SCEN)
    print(f"\n加权 V = {vw:.2f} 元/股，P/V = {PRICE / vw:.2f}；剔除回购专户 V = {vw_ex:.2f}，P/V = {PRICE / vw_ex:.2f}")
    print(f"股权成本 8%：V = {weighted(0.08):.2f}（P/V {PRICE / weighted(0.08):.2f}）；10%：V = {weighted(0.10):.2f}（P/V {PRICE / weighted(0.10):.2f}）")
    for k in SCEN:
        print(f"  {k}: 8% {run(SCEN[k], 0.08)['v']:.2f}，10% {run(SCEN[k], 0.10)['v']:.2f}")
    print(f"基准情景现价隐含回报 {implied_irr():.2%}")
    g, b26, n36 = reverse_dcf()
    print(f"反向 DCF：自 2026E NOPAT {b26:.2f} 亿元起，现价隐含 2027-2036 年 NOPAT 年增速 {g:.1%}（2036 年 NOPAT {n36:.0f} 亿元）")
    print("分档价格（V 不变）：明显低估 ≤ {:.1f}；温和低估 {:.1f}～{:.1f}；大致合理 {:.1f}～{:.1f}；偏贵 > {:.1f}".format(
        0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    # ---------- 交叉验证 ----------
    ttm_core_ebit = 10.333 - 4.920 + EBIT_H1
    ev = mcap - NET_CASH_ADJ - NON_OP
    base = SCEN['base']
    ebit27 = base['rev'][2027] * base['m'][2027]
    print(f"\n交叉验证：EV {ev:.0f} 亿元；EV/TTM 核心 EBIT {ev / ttm_core_ebit:.0f} 倍（TTM 核心 EBIT {ttm_core_ebit:.2f}）；"
          f"EV/2027E 基准 EBIT {ev / ebit27:.0f} 倍")
    print(f"PE(TTM 归母 11.42) {mcap / 11.42:.0f} 倍；PB（6-30 归母权益 79.11 + 定增 37.73）{mcap / (79.11 + 37.73):.1f} 倍；"
          f"股息率 {0.40 / PRICE:.2%}；回购（新提议上限 1 亿元）收益率 {1.0 / mcap:.2%}")
    sbc_plan = {2026: 1.4658, 2027: 8.7949, 2028: 8.2029, 2029: 4.7921, 2030: 2.1142}
    pv_gap = sum((sbc_plan[y] - 0.015 * base['rev'][y]) * (1 - 0.12) / (1 + COE) ** max(0.0, (y + 0.5) - T_VAL)
                 for y in sbc_plan if y > 2026)
    print(f"敏感性：若 2027-2030 股份支付按 2026 激励计划会计摊销（而非营收 1.5%），基准 V 降 {pv_gap / SHARES:.1f} 元/股")

    # ---------- 2026 年报表口径预估（基准） ----------
    rev26 = base['rev'][2026]
    ebit26 = rev26 * base['m'][2026]
    nopat26 = ebit26 * (1 - base['tax'][2026])
    nonrec_at = 0.47             # 非经常性补助等，税后（上半年 0.27 税前，全年约 0.55 税前）
    sbc23_2026 = 0.62            # 2023 年计划 2026 年摊销（上半年 0.309 × 2）
    reported26 = (nopat26 + FIN_INCOME_2026_AT + nonrec_at
                  - sbc_plan[2026] * (1 - 0.12) + (0.015 * rev26 - sbc23_2026) * (1 - 0.12))
    print(f"\n2026 基准：营收 {rev26:.1f}（下半年 {rev26 - 26.432:.2f}），核心 EBIT {ebit26:.2f}（下半年 {ebit26 - EBIT_H1:.2f}，"
          f"利润率 {(ebit26 - EBIT_H1) / (rev26 - 26.432):.1%}），扣 2026 计划四季度摊销后报表归母净利约 {reported26:.2f} 亿元")

    # ---------- 证伪条件触发后的 V ----------
    f1 = weighted(w={'bear': 0.55, 'base': 0.40, 'bull': 0.05})
    f2 = weighted(w={'bear': 0.70, 'base': 0.30, 'bull': 0.00})
    f3 = weighted(w={'bear': 0.45, 'base': 0.50, 'bull': 0.05})
    f4 = weighted(w={'bear': 0.05, 'base': 0.45, 'bull': 0.50})
    print(f"\n证伪触发后 V：F1 营收/订单不及 {f1:.1f}；F2 利润率失守 {f2:.1f}；F3 芯嵛未达承诺并减值 {f3:.1f}；F4 上行证伪 {f4:.1f}")
