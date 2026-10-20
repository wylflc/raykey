# -*- coding: utf-8 -*-
"""伊利股份（600887）独立估值：所有者收益 DCF（归母、无杠杆口径）+ 经调整净现金 + 非经营资产。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。价格日 2026-10-20。
基准日：2026-06-30 资产负债表（2026 中报为最新定期报告），经营部分现值按股权成本滚动至 2026-10-20。
所有输入写在本脚本内，出处见注释（文件名 + PDF 物理页；网络事实见正文来源）。
"""
import math

# ---------------------------------------------------------------- 快照
PRICE = 28.07                 # 2026-10-20 收盘（brief）
SHARES = 63.2536              # 亿股，总股本（brief；回购尚未实施，无回购专户股份）
COE = 0.09
ROLL_DAYS = 112               # 2026-06-30 -> 2026-10-20

# ---------------------------------------------------------------- 2026H1 与 2025H2 经营数据（亿元）
# 核心经营利润 = 营业收入 - 营业成本 - 税金及附加 - 销售费用 - 管理费用 - 研发费用（不含利息、投资、补助、减值、营业外）
H1_26 = dict(rev=643.3094, cost=408.9408, tax_add=4.6518, sell=114.3217, admin=24.7090, rnd=3.9745)  # 2026H1_report 第 52 页
FY_25 = dict(rev=1156.3623, cost=756.5384, tax_add=6.7249, sell=215.4458, admin=46.9560, rnd=9.1501)  # 2025_annual_report 第 86 页
H1_25 = dict(rev=617.7675, cost=395.0920, tax_add=4.1216, sell=113.3412, admin=23.3526, rnd=3.8030)   # 2026H1_report 第 52 页（上年同期）


def core_op(d):
    return d['rev'] - d['cost'] - d['tax_add'] - d['sell'] - d['admin'] - d['rnd']


CORE_H1_26 = core_op(H1_26)                     # 86.72
CORE_H2_25 = core_op(FY_25) - core_op(H1_25)    # 43.47
REV_H2_25 = FY_25['rev'] - H1_25['rev']         # 538.59

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，亿元）
DEPOSITS = {
    '货币资金': 166.1674,                        # 第 48、110 页
    '一年内到期的大额存单': 18.2231,              # 第 126 页
    '其他流动资产-大额存单及定期存款': 201.2463,   # 第 127 页
    '其他非流动资产-大额存单及定期存款': 413.1810, # 第 147 页
}
RESTRICTED = {
    '财务公司法定存款准备金': 26.5655,            # 第 111、147 页
    '担保保证金': 0.3552,
    '其他受限资金': 0.0441,
}
TTM_REVENUE = 1184.88                            # 营业总收入 TTM（数据包）
OPERATING_RESERVE_RATE = 0.03                    # 经营备付：TTM 收入的 3%
DEBT = {
    '短期借款（含票据贴现借款 481.41）': 646.7719,  # 第 148 页
    '一年内到期的长期借款': 0.3774,                # 第 153 页
    '一年内到期的租赁负债': 1.6067,
    '长期借款': 1.9771,                            # 第 49 页
    '租赁负债': 2.6949,
    '衍生金融负债净额（扣衍生金融资产 0.02）': 0.9976,  # 第 48-49 页
    '其他非流动负债（远期外汇合约）': 0.0668,
    '财务公司吸收成员单位存款（含优然 11.49）': 13.4235,  # 第 152、198 页
    '应付股利': 3.5266,                            # 第 152 页
    '融资担保准备金（未到期责任+担保赔偿）': 1.6965,  # 第 153 页
}

# ---------------------------------------------------------------- 非经营资产（亿元）
HKD_CNY = 0.86855                     # 2026H1_report 第 175 页期末汇率（10-20 汇率未另查，按此近似）
YOURAN_STAKE = 0.3607                 # 第 185 页
YOURAN_MCAP_HKD = 157.6421            # 腾讯行情 2026-10-20：优然牧业 HK$3.51
AUSNUTRIA_STAKE = 1546.5449 / 2613.7314  # 合并报表商誉减值 / 全部商誉减值（第 144 页）≈ 59.17%
AUSNUTRIA_MCAP_HKD = 18.6705          # 腾讯行情 2026-10-20：澳优 HK$1.05（仅作分部加总交叉验证）
OTHER_ASSOC_BOOK = 2.3269 + 1.1832    # 不重要的合营、联营企业账面（第 186-187 页）
FIN_INVEST = 1.0924 + 20.5151 + 22.3746  # 交易性金融资产 + 其他非流动金融资产 + 其他权益工具投资（第 48 页）
CREDIT_ASSETS_NET = 32.4534 + 28.8603 + 2.7941  # 小贷、保理、代位追偿款净额（第 126-127、146-147、189 页）

# ---------------------------------------------------------------- 情景假设
# m_h2：2026H2 核心经营利润率（2025H2 为 8.07%）；m_norm：2028 年起的周期中枢核心经营利润率
# sub：政府补助/收入；imp：常规资产减值/收入；nonop：营业外净支出/收入；minority：少数股东损益（亿元，2026 口径）
# net_int、assoc：只用于“正常化归母净利”（含净利息、联营），不进 DCF（现金与优然已在资产端单列）
SCEN = {
    'bear': dict(p=0.25, g_h2=0.01, m_h2=0.076, m_norm=0.0875,
                 rev_g=[0.015, 0.015, 0.015, 0.015, 0.010], g_term=0.010,
                 sub=0.006, imp=0.005, nonop=0.0035, tax=0.17, tax_term=0.19,
                 minority=0.0, ronic=0.15,
                 youran_hc=0.80, fin_hc=0.70, credit_hc=0.75, net_int=6.0, assoc=1.0),
    'base': dict(p=0.50, g_h2=0.04, m_h2=0.085, m_norm=0.100,
                 rev_g=[0.035, 0.035, 0.030, 0.030, 0.025], g_term=0.020,
                 sub=0.008, imp=0.004, nonop=0.0025, tax=0.155, tax_term=0.155,
                 minority=0.6, ronic=0.25,
                 youran_hc=1.00, fin_hc=0.80, credit_hc=0.85, net_int=9.0, assoc=2.5),
    'bull': dict(p=0.25, g_h2=0.06, m_h2=0.089, m_norm=0.1125,
                 rev_g=[0.055, 0.050, 0.045, 0.040, 0.035], g_term=0.025,
                 sub=0.009, imp=0.003, nonop=0.0020, tax=0.145, tax_term=0.145,
                 minority=1.0, ronic=0.35,
                 youran_hc=1.00, fin_hc=0.90, credit_hc=0.95, net_int=11.0, assoc=4.0),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def net_cash_adj():
    dep = sum(DEPOSITS.values())
    res = sum(RESTRICTED.values())
    reserve = OPERATING_RESERVE_RATE * TTM_REVENUE
    debt = sum(DEBT.values())
    return dict(deposits=dep, restricted=res, reserve=reserve, debt=debt,
                net=dep - res - reserve - debt)


def non_operating(s):
    youran = YOURAN_STAKE * YOURAN_MCAP_HKD * HKD_CNY
    parts = dict(youran=youran * s['youran_hc'], other_assoc=OTHER_ASSOC_BOOK,
                 fin_invest=FIN_INVEST * s['fin_hc'], credit=CREDIT_ASSETS_NET * s['credit_hc'])
    parts['total'] = sum(parts.values())
    return parts


def path(s):
    """返回 2026 全年、2026H2 与 2027-2032 的收入、利润率、归母经营 NOPAT、所有者收益。"""
    rev_h2 = REV_H2_25 * (1 + s['g_h2'])
    rev26 = H1_26['rev'] + rev_h2
    m26 = (CORE_H1_26 + rev_h2 * s['m_h2']) / rev26
    other = s['sub'] - s['imp'] - s['nonop']
    out = dict(rev26=rev26, m26=m26, rev_h2=rev_h2)
    out['nopat26'] = rev26 * (m26 + other) * (1 - s['tax']) - s['minority']
    out['nopat26_norm'] = rev26 * (s['m_norm'] + other) * (1 - s['tax']) - s['minority']
    g_next = s['rev_g'][0]
    out['oe26'] = out['nopat26'] * (1 - g_next / s['ronic'])
    nopat_h2 = rev_h2 * (s['m_h2'] + other) * (1 - s['tax']) - s['minority'] / 2
    out['oe_h2'] = nopat_h2 * (1 - g_next / s['ronic'])
    rows = []
    rev = rev26
    for i, y in enumerate(YEARS):
        g = s['rev_g'][i]
        rev *= 1 + g
        m = (m26 + s['m_norm']) / 2 if y == 2027 else s['m_norm']
        minority = s['minority'] * rev / rev26
        nopat = rev * (m + other) * (1 - s['tax']) - minority
        g_next = s['rev_g'][i + 1] if i + 1 < len(YEARS) else s['g_term']
        rr = g_next / s['ronic']
        rows.append(dict(year=y, rev=rev, margin=m, nopat=nopat, rr=rr, oe=nopat * (1 - rr)))
    rev32 = rev * (1 + s['g_term'])
    nopat32 = rev32 * (s['m_norm'] + other) * (1 - s['tax_term']) - s['minority'] * rev32 / rev26
    out['oe32'] = nopat32 * (1 - s['g_term'] / s['ronic'])
    out['rows'] = rows
    return out


def value(s, r=COE, g_term=None, detail=False):
    g_term = s['g_term'] if g_term is None else g_term
    p = path(dict(s, g_term=g_term))
    pv = p['oe_h2'] / (1 + r) ** 0.25
    for k, row in enumerate(p['rows'], start=1):
        pv += row['oe'] / (1 + r) ** k
    tv = p['oe32'] / (r - g_term)
    pv_tv = tv / (1 + r) ** 5
    op_0630 = pv + pv_tv
    op_1020 = op_0630 * (1 + r) ** (ROLL_DAYS / 365)
    nc = net_cash_adj()['net']
    no = non_operating(s)['total']
    eq = op_1020 + nc + no
    v = eq / SHARES
    if detail:
        return dict(v=v, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / op_0630, op_1020=op_1020,
                    net_cash=nc, nonop=no, equity=eq, path=p)
    return v


def weighted(r=COE, mod=None):
    tot = 0.0
    for k, s in SCEN.items():
        s2 = dict(s, **(mod(k, s) if mod else {}))
        tot += s['p'] * value(s2, r)
    return tot


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


def reverse_dcf_cagr():
    """现价隐含：以基准 2026 年中枢所有者收益为起点，10 年年增速 x，之后永续 2%，9% 折现。"""
    s = SCEN['base']
    p = path(s)
    oe0 = p['nopat26_norm'] * (1 - 0.03 / s['ronic'])
    nc = net_cash_adj()['net']
    no = non_operating(s)['total']
    target_op_1020 = PRICE * SHARES - nc - no
    target_op_0630 = target_op_1020 / (1 + COE) ** (ROLL_DAYS / 365)

    def pv(x):
        tot = 0.5 * oe0 / (1 + COE) ** 0.25
        oe = oe0
        for k in range(1, 11):
            oe *= 1 + x
            tot += oe / (1 + COE) ** k
        tv = oe * 1.02 * (1 - 0.02 / s['ronic']) / (1 - 0.03 / s['ronic']) / (COE - 0.02)
        return tot + tv / (1 + COE) ** 10
    return oe0, solve(pv, -0.10, 0.20, target_op_0630)


def normalized_np_2026(s):
    p = path(s)
    return p['nopat26_norm'] + s['net_int'] * (1 - s['tax']) + s['assoc']


def main():
    nc = net_cash_adj()
    print('=== 经调整净现金（2026-06-30，亿元）===')
    print(f"存款类合计 {nc['deposits']:.2f} - 受限 {nc['restricted']:.2f} - 经营备付 {nc['reserve']:.2f}"
          f" - 有息及类债务 {nc['debt']:.2f} = {nc['net']:.2f}")
    print('（为正，按框架照常全额扣除有息负债，不用有杠杆口径）')
    print(f"核心经营利润：2026H1 {CORE_H1_26:.2f}（{CORE_H1_26 / H1_26['rev']:.2%}），"
          f"2025H1 {core_op(H1_25):.2f}（{core_op(H1_25) / H1_25['rev']:.2%}），"
          f"2025 {core_op(FY_25):.2f}（{core_op(FY_25) / FY_25['rev']:.2%}），2025H2 {CORE_H2_25:.2f}（{CORE_H2_25 / REV_H2_25:.2%}）")
    print()
    res = {}
    for k, s in SCEN.items():
        d = value(s, detail=True)
        res[k] = d
        no = non_operating(s)
        p = d['path']
        print(f"=== {k}（概率 {s['p']:.0%}）===")
        print(f"2026 收入 {p['rev26']:.1f}，核心经营利润率 {p['m26']:.2%}，中枢 {s['m_norm']:.2%}；"
              f"2026 经营 NOPAT（当年）{p['nopat26']:.1f}，按中枢 {p['nopat26_norm']:.1f}")
        print(f"2026H2 所有者收益 {p['oe_h2']:.1f}")
        for row in p['rows']:
            print(f"  {row['year']} 收入 {row['rev']:.1f} 利润率 {row['margin']:.2%} NOPAT {row['nopat']:.1f}"
                  f" 再投资率 {row['rr']:.1%} 所有者收益 {row['oe']:.1f}")
        print(f"  2032 所有者收益 {p['oe32']:.1f}（终值增长 {s['g_term']:.1%}）")
        print(f"显性期现值 {d['pv_explicit']:.1f}，终值现值 {d['pv_tv']:.1f}（终值占经营现值 {d['tv_share']:.1%}）；"
              f"经营部分滚动至 10-20 {d['op_1020']:.1f}")
        print(f"非经营资产 {no['total']:.1f}（优然 {no['youran']:.1f}、其他联营 {no['other_assoc']:.1f}、"
              f"金融投资 {no['fin_invest']:.1f}、小贷保理 {no['credit']:.1f}）；净现金 {d['net_cash']:.1f}")
        print(f"股权价值 {d['equity']:.1f} 亿元，每股 V = {d['v']:.2f} 元；8% 下 {value(s, 0.08):.2f}，10% 下 {value(s, 0.10):.2f}")
        print(f"2026 正常化归母净利（含净利息、联营，剔除一次性）{normalized_np_2026(s):.1f}")
        print()
    vw = sum(SCEN[k]['p'] * res[k]['v'] for k in SCEN)
    v8, v10 = weighted(0.08), weighted(0.10)
    pv_ratio = PRICE / vw
    band = ('明显低估' if pv_ratio <= 0.75 else '温和低估' if pv_ratio <= 0.90
            else '大致合理' if pv_ratio <= 1.10 else '偏贵或价值陷阱风险高')
    print('=== 汇总 ===')
    print(f"三情景 V：熊 {res['bear']['v']:.2f} / 基准 {res['base']['v']:.2f} / 牛 {res['bull']['v']:.2f}")
    print(f"加权 V = {vw:.2f} 元；P/V = {pv_ratio:.3f}（{band}）")
    print(f"股权成本 8%：加权 V {v8:.2f}（P/V {PRICE / v8:.3f}）；10%：加权 V {v10:.2f}（P/V {PRICE / v10:.3f}）")
    irr = solve(lambda r: value(SCEN['base'], r), 0.05, 0.20, PRICE)
    print(f"现价隐含回报（基准现金流）= {irr:.2%}")
    g_imp = solve(lambda g: value(SCEN['base'], COE, g_term=g), -0.05, 0.06, PRICE)
    oe0, x = reverse_dcf_cagr()
    print(f"反向 DCF：基准显性期不变时现价隐含永续增长 {g_imp:.2%}；"
          f"以 2026 中枢所有者收益 {oe0:.1f} 亿为起点，现价隐含 10 年年增速 {x:.2%}（其后 2%）")
    print(f"各档价格（V 不变）：明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}~{0.90 * vw:.2f}；"
          f"大致合理 {0.90 * vw:.2f}~{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}")
    print()

    print('=== 交叉验证 ===')
    mcap = PRICE * SHARES
    nc_v = net_cash_adj()['net']
    no_b = non_operating(SCEN['base'])['total']
    ev = mcap - nc_v - no_b
    pb = path(SCEN['base'])
    other_b = SCEN['base']['sub'] - SCEN['base']['imp'] - SCEN['base']['nonop']
    ebit_run = pb['rev26'] * (pb['m26'] + other_b)
    ebit_norm = pb['rev26'] * (SCEN['base']['m_norm'] + other_b)
    print(f"市值 {mcap:.1f}；剔除净现金与非经营资产后的经营 EV {ev:.1f}；"
          f"EV/2026 经营 EBIT（当年 {ebit_run:.1f}）{ev / ebit_run:.1f}x，（中枢 {ebit_norm:.1f}）{ev / ebit_norm:.1f}x")
    nn = normalized_np_2026(SCEN['base'])
    sb = SCEN['base']
    np_run = pb['nopat26'] + sb['net_int'] * (1 - sb['tax']) + sb['assoc']
    print(f"市值 / 基准 2026 正常化归母净利 {nn:.1f} = {mcap / nn:.1f}x；市值 / 2025 归母 115.65 = {mcap / 115.65:.1f}x；"
          f"2026 当年利润率口径（不做周期正常化）归母约 {np_run:.1f}")
    print(f"股息率：近 12 个月每股 1.38 元 -> {1.38 / PRICE:.2%}；分红底线每股 1.22 元 -> {1.22 / PRICE:.2%}；"
          f"回购 10~20 亿 -> {10 / mcap:.2%}~{20 / mcap:.2%}")
    youran = YOURAN_STAKE * YOURAN_MCAP_HKD * HKD_CNY
    ausn = AUSNUTRIA_STAKE * AUSNUTRIA_MCAP_HKD * HKD_CNY
    print(f"分部加总：优然 36.07% 市值 {youran:.1f}（6-30 公允价值 38.98，账面 49.52）；"
          f"澳优 {AUSNUTRIA_STAKE:.2%} 市值 {ausn:.1f}；合计 {(youran + ausn) / SHARES:.2f} 元/股")
    core_implied = mcap - nc_v - no_b - ausn
    print(f"现价隐含伊利本部（扣澳优市值）经营价值 {core_implied:.1f}，"
          f"对基准 2026 中枢经营 NOPAT {pb['nopat26_norm']:.1f} 为 {core_implied / pb['nopat26_norm']:.1f}x")
    print()

    print('=== 基准增长路径（登记用）===')
    rows = pb['rows']
    oe_prev = pb['oe26']
    growth = []
    for row in rows:
        growth.append(row['oe'] / oe_prev - 1)
        oe_prev = row['oe']
    print(f"2026 全年所有者收益（当年利润率）{pb['oe26']:.1f}；2027-2031 所有者收益增速 "
          + ', '.join(f"{g:.1%}" for g in growth)
          + f"；平均再投资率 {sum(r['rr'] for r in rows) / len(rows):.1%}；增量回报 {SCEN['base']['ronic']:.0%}")
    # 三季度估计（2025 前三季度数据取东财 F10 原始数据 f10.json；2025Q3 营业收入 285.64、归母净利 32.26 与 2025_annual_report 第 8 页一致）
    q3_rev25 = 903.4055 - H1_25['rev']
    q3_core25 = 903.4055 - 584.2961 - 4.9670 - 165.5296 - 34.7409 - 6.2768 - core_op(H1_25)
    q3_rev26 = q3_rev25 * 1.03
    q3_core26 = q3_rev26 * (q3_core25 / q3_rev25 + 0.004)
    q3_pretax = q3_core26 + q3_rev26 * (SCEN['base']['sub'] - SCEN['base']['imp'] - SCEN['base']['nonop']) + 3.0 + 0.8
    print(f"2026Q3 估计（基准）：营业收入 {q3_rev26:.1f}（2025Q3 {q3_rev25:.1f}），核心经营利润 {q3_core26:.1f}"
          f"（2025Q3 {q3_core25:.1f}），归母净利约 {q3_pretax * (1 - SCEN['base']['tax']):.1f}（2025Q3 32.26）")
    print()

    print('=== 证伪触发后的加权 V ===')
    falsifiers = [
        ('F1 2027H1 核心经营利润率 < 12.0%（2026H1 13.48%；中枢下移 0.75 个百分点、2026H2 利润率 -1 个百分点）',
         lambda k, s: dict(m_norm=s['m_norm'] - 0.0075, m_h2=s['m_h2'] - 0.01)),
        ('F2 2026 营业总收入 < 1,180 亿或 2027H1 收入同比 < 0（增速全线下调 1.5 个百分点）',
         lambda k, s: dict(g_h2=s['g_h2'] - 0.03, rev_g=[g - 0.015 for g in s['rev_g']], g_term=s['g_term'] - 0.005)),
        ('F3 十省生鲜乳均价连续一季 ≥ 3.60 元/公斤且季度毛利率同比降 ≥ 1.5 个百分点（中枢下移 1.25 个百分点）',
         lambda k, s: dict(m_norm=s['m_norm'] - 0.0125)),
        ('F4 2026 实际税率（剔除商誉减值与以前年度调整）≥ 18%（税率全线 +2.5 个百分点）',
         lambda k, s: dict(tax=s['tax'] + 0.025, tax_term=s['tax_term'] + 0.025)),
        ('F5 澳优 2026H2 未扭亏或再计提商誉/无形资产减值 ≥ 10 亿（增量回报 -10 个百分点、减值率 +0.1 个百分点）',
         lambda k, s: dict(ronic=max(s['ronic'] - 0.10, 0.08), imp=s['imp'] + 0.001)),
    ]
    for name, mod in falsifiers:
        print(f"{name}：{weighted(COE, mod):.2f}")


if __name__ == '__main__':
    main()
