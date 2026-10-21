#!/usr/bin/env python3
"""中材国际（600970）独立估值：所有者收益 DCF（有杠杆口径为准，另列无杠杆对照）、三情景、
股权成本敏感性、现价隐含回报、反向 DCF、交叉验证与证伪条件触发后的 V。

用法：python3 valuation.py
金额单位亿元，每股价值单位元/股。全部输入写在脚本内，出处见 companies/600970_中材国际.md 第 9 节。
"""
import copy

# ============================================================ 快照（brief.md）
PRICE = 7.79                 # 2026-10-21 收盘，A 股未复权
SHARES = 26.2181             # 亿股；2026-09-30 股本 2,621,812,924 股，库存股 0（2026Q3_report 第 8 页）
COE = 0.09
STUB_YEARS = 0.19            # 2026-10-21 至 2026-12-31
MKT_CAP = PRICE * SHARES

# ============================================================ 2026-09-30 资产负债表（2026Q3_report 第 6-8、12 页；2026H1_report 附注）
CASH = 76.107                # 货币资金
TRADING_FA = 0.627           # 交易性金融资产（主要为权益工具，含中材节能股票）
CASH_EQUIV = 71.410          # 期末现金及现金等价物（第 12 页）；差额为受限资金
DEBT_REPORTED = 72.96        # 短借 36.24 + 长借 11.32 + 应付债券 14.00 + 一年内到期非流动负债 10.84 + 租赁 0.55 + 交易性金融负债 0.01
LEASE_TOTAL = 0.55 + 0.25    # 租赁负债 + 一年内到期租赁负债（中报第 161 页 0.25）；以净利润为起点，只列示不扣
GROUP_LOANS = 4.583          # 其他应付款—资金拆借（中国建材集团等，中报第 160 页；公司年报把它列为债权融资）
EQUITY_TRANSFER_PAY = 0.824  # 其他应付款—应付股权转让款（中报第 161 页）
SUPPLY_CHAIN_FIN = 0.480     # 其他流动负债—供应链融资（中报第 161 页）
LONG_PAYABLE = 4.447         # 长期应付款（采矿权价款为主，中报第 166 页 3.86；三季报余额 4.45）
LT_EMPLOYEE = 2.380          # 长期应付职工薪酬（设定受益计划净负债 2.25 为主）
DIV_PAYABLE = 1.279          # 应付股利（已宣派，主要为子公司少数股东）
OP_RESERVE_RATE = 0.03       # 经营备付：TTM 营收的 3%（含奈拉、比尔等兑换受限币种的境外存款）
TTM_REVENUE = 485.42
FINCO_DEPOSIT_H1 = 22.977    # 存放中国建材集团财务有限公司存款（中报第 37、111 页），只列示
LTEI = 27.862                # 长期股权投资（中材水泥 40% 中报账面 19.77）
HELD_FOR_SALE = 0.431        # 持有待售资产（公允价值 0.65）
DEBT_RATE = 0.026            # 有息负债实际平均利率：前三季度利息费用 1.378 年化 ÷ 平均有息负债约 72
PARENT_EQUITY = 229.355      # 2026-09-30 归母权益

restricted = CASH - CASH_EQUIV
op_reserve = OP_RESERVE_RATE * TTM_REVENUE
debt_ex_lease = DEBT_REPORTED - LEASE_TOTAL
debt_like = GROUP_LOANS + EQUITY_TRANSFER_PAY + SUPPLY_CHAIN_FIN + LONG_PAYABLE + LT_EMPLOYEE + DIV_PAYABLE
NET_CASH_ADJ = CASH + TRADING_FA - restricted - op_reserve - debt_ex_lease - debt_like

# ============================================================ 2026 年估计（前三季度实际 + 四季度假设）
NP_9M, DNP_9M, EXFX_9M = 12.877, 12.991, 14.90   # 归母、扣非、扣非扣汇兑（2026Q3_report 第 1、6 页）
ASSOC_9M = 1.211
REV_9M = 319.410
Q4 = dict(rev=155.0, gm=0.208, opex=18.6, imp=4.8, other=0.45, assoc=0.45, derecog=-0.15,
          net_int=0.45, fees=-0.12, fx=-0.30, nonop=0.10, tax=0.17, minority=0.06)
q4_pbt = (Q4['rev'] * Q4['gm'] - Q4['opex'] - Q4['imp'] + Q4['other'] + Q4['assoc'] + Q4['derecog']
          + Q4['net_int'] + Q4['fees'] + Q4['fx'] + Q4['nonop'])
Q4_NP = q4_pbt * (1 - Q4['tax']) * (1 - Q4['minority'])
REV_2026E = REV_9M + Q4['rev']
NP_2026E = NP_9M + Q4_NP
EXFX_2026E = EXFX_9M + Q4_NP - (Q4['fx'] + Q4['nonop']) * (1 - Q4['tax']) * (1 - Q4['minority'])
FIN_INT = 0.15               # 财务性净利息（存款利息 − 借款利息），税前；其余利息收入来自分期收款项目，属经营
RUNRATE_OP = EXFX_2026E - (ASSOC_9M + Q4['assoc']) - FIN_INT * (1 - 0.165) * (1 - 0.065)

# ============================================================ 情景
YEARS = [2027, 2028, 2029, 2030, 2031]
SCEN = {
    'bear': dict(p=0.30, gm=0.170, opex=0.109, imp=0.020, other=0.8, derecog=-0.6, net_int=1.5, fees=-0.45,
                 tax=0.18, minority=0.06, assoc=1.0,
                 g=[-0.03, -0.01, 0.01, 0.01, 0.01], g_term=0.010,
                 nwc_inc=0.22, capex_inc=0.05, creep=[0.010, 0.008, 0.006, 0.004, 0.002],
                 stub_fcf=10.0, ltei_mult=0.5, specific=6.0,
                 note='境内继续收缩、境外毛利受中东与人民币升值压制，减值维持 2.0%，两金占比再升 3 个百分点；'
                      '锦象回收 40%、清峰损失 20%'),
    'base': dict(p=0.50, gm=0.178, opex=0.106, imp=0.015, other=1.0, derecog=-0.4, net_int=1.8, fees=-0.45,
                 tax=0.165, minority=0.065, assoc=1.5,
                 g=[0.02, 0.03, 0.03, 0.03, 0.025], g_term=0.020,
                 nwc_inc=0.22, capex_inc=0.05, creep=[0.005, 0.003, 0.0, 0.0, 0.0],
                 stub_fcf=18.0, ltei_mult=0.7, specific=1.64,
                 note='毛利率 17.8%（略低于 2017-2025 中枢 17.9%），减值率从 2026E 的 2.0% 回落到 1.5%，'
                      '境外与矿业订单支撑 2-3% 增长，两金占比再升 0.8 个百分点后企稳；锦象回收 70%'),
    'bull': dict(p=0.20, gm=0.185, opex=0.103, imp=0.011, other=1.2, derecog=-0.3, net_int=2.0, fees=-0.45,
                 tax=0.16, minority=0.07, assoc=2.0,
                 g=[0.04, 0.05, 0.05, 0.04, 0.035], g_term=0.025,
                 nwc_inc=0.20, capex_inc=0.05, creep=[-0.003, -0.003, 0.0, 0.0, 0.0],
                 stub_fcf=24.0, ltei_mult=0.9, specific=0.27,
                 note='汇率与中东扰动消退，减值回到 2020-2025 年均 1.1%，境外运维与矿业放量，两金压降见效；锦象回收 90%'),
}


def ebit_items(s, rev):
    return rev * (s['gm'] - s['opex'] - s['imp']) + s['other'] + s['derecog'] + s['fees']


def normalized_np(s, rev=None):
    """2026 年正常化归母净利：(报表口径，含净利息与联营收益), (经营口径，不含联营与财务性净利息)。"""
    rev = REV_2026E if rev is None else rev
    keep = (1 - s['tax']) * (1 - s['minority'])
    pbt = ebit_items(s, rev) + s['net_int']
    reported = pbt * keep + s['assoc']
    operating = (pbt - FIN_INT) * keep
    return reported, operating


def path(s):
    """逐年经营所有者收益（归母口径）。"""
    _, np_norm = normalized_np(s)
    m_norm = np_norm / REV_2026E
    m_rr = RUNRATE_OP / REV_2026E
    ps = 1 - s['minority']
    rows, rev_prev = [], REV_2026E
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s['g'][i])
        m = 0.5 * (m_rr + m_norm) if i == 0 else m_norm          # 2027 年利润率走一半，2028 年起到正常化水平
        npy = m * rev
        d_rev = rev - rev_prev
        reinv = (s['nwc_inc'] * d_rev + s['creep'][i] * rev + s['capex_inc'] * max(d_rev, 0.0)) * ps
        rows.append(dict(year=y, rev=rev, np=npy, reinv=reinv, oe=npy - reinv))
        rev_prev = rev
    rev_t = rev_prev * (1 + s['g_term'])
    d_rev = rev_t - rev_prev
    reinv_t = (s['nwc_inc'] + s['capex_inc']) * d_rev * ps
    term = dict(year=2032, rev=rev_t, np=m_norm * rev_t, reinv=reinv_t, oe=m_norm * rev_t - reinv_t)
    stub = s['stub_fcf'] * ps
    return dict(np_norm=np_norm, rows=rows, term=term, stub=stub)


def oe_2026_runrate(s):
    """2026 运行水平所有者收益：经营口径运行利润扣按终值增速计的稳态再投资（增长路径的起点）。"""
    return RUNRATE_OP - (s['nwc_inc'] + s['capex_inc']) * REV_2026E * s['g_term'] * (1 - s['minority'])


def value(s, coe=COE, levered=True):
    cf = path(s)
    keep_fin = FIN_INT * (1 - s['tax']) * (1 - s['minority'])        # 无杠杆对照把财务性净利息加回
    pv_stub = cf['stub'] / (1 + coe) ** (STUB_YEARS / 2)
    pv_exp = 0.0
    for k, r in enumerate(cf['rows']):
        oe = r['oe'] + (0.0 if levered else keep_fin)
        pv_exp += oe / (1 + coe) ** (STUB_YEARS + k + 0.5)
    oe_t = cf['term']['oe'] + (0.0 if levered else keep_fin)
    pv_tv = oe_t / (coe - s['g_term']) / (1 + coe) ** (STUB_YEARS + len(YEARS) - 0.5)
    non_op = LTEI * s['ltei_mult'] + HELD_FOR_SALE
    if levered and NET_CASH_ADJ < 0:
        fin = NET_CASH_ADJ * DEBT_RATE * (1 - s['tax']) / coe          # 经调整净负债按现规模滚动，扣税后利息现值
    else:
        fin = NET_CASH_ADJ
    equity = pv_stub + pv_exp + pv_tv + fin + non_op - s['specific']
    op = pv_stub + pv_exp + pv_tv
    return dict(v=equity / SHARES, equity=equity, pv_stub=pv_stub, pv_exp=pv_exp, pv_tv=pv_tv,
                tv_share=pv_tv / op, fin=fin, non_op=non_op, cf=cf)


def weighted(coe=COE, levered=True, scen=None, probs=None):
    scen = scen or SCEN
    probs = probs or {k: v['p'] for k, v in scen.items()}
    return sum(probs[k] * value(scen[k], coe, levered)['v'] for k in scen)


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if fm * flo <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def implied_irr(s):
    return solve(lambda r: value(s, r)['v'], 0.05, 0.40, PRICE)


def fixed_parts(s, coe=COE):
    non_op = LTEI * s['ltei_mult'] + HELD_FOR_SALE
    drag = -NET_CASH_ADJ * DEBT_RATE * (1 - s['tax']) / coe
    pv_stub = path(s)['stub'] / (1 + coe) ** (STUB_YEARS / 2)
    return MKT_CAP + drag + s['specific'] - non_op - pv_stub      # 现价对应的经营所有者收益现值


def reverse_perpetual(s):
    """以基准 2027 年所有者收益为起点，现价隐含的永续增速（9%）。"""
    oe1 = path(s)['rows'][0]['oe']
    target = fixed_parts(s)
    return solve(lambda g: oe1 / (COE - g) / (1 + COE) ** (STUB_YEARS + 0.5), -0.30, 0.085, target)


def reverse_10y(s, g_term=0.02):
    """以 2026 正常化所有者收益（按终值增速扣再投资）为起点，现价隐含的 10 年复合增速，其后 2% 永续。"""
    _, np_norm = normalized_np(s)
    oe0 = np_norm - (s['nwc_inc'] + s['capex_inc']) * REV_2026E * g_term * (1 - s['minority'])
    target = fixed_parts(s)

    def f(x):
        pv, oe = 0.0, oe0
        for k in range(10):
            oe *= 1 + x
            pv += oe / (1 + COE) ** (STUB_YEARS + k + 0.5)
        return pv + oe * (1 + g_term) / (COE - g_term) / (1 + COE) ** (STUB_YEARS + 9.5)
    return solve(f, -0.30, 0.30, target), oe0


def band(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def variant(**changes):
    sc = copy.deepcopy(SCEN)
    for key, upd in changes.items():
        sc[key].update(upd)
    return sc


if __name__ == '__main__':
    print('== 经调整净现金（2026-09-30，亿元，无杠杆口径定义）==')
    print(f'现金类 {CASH + TRADING_FA:.2f} − 受限 {restricted:.2f} − 经营备付 {op_reserve:.2f} − 有息负债(不含租赁) {debt_ex_lease:.2f} '
          f'− 类债务 {debt_like:.2f} = {NET_CASH_ADJ:.2f}')
    print(f'  类债务：资金拆借 {GROUP_LOANS:.2f}、应付股权转让款 {EQUITY_TRANSFER_PAY:.2f}、供应链融资 {SUPPLY_CHAIN_FIN:.2f}、长期应付款 {LONG_PAYABLE:.2f}、'
          f'长期应付职工薪酬 {LT_EMPLOYEE:.2f}、应付股利 {DIV_PAYABLE:.2f}；租赁 {LEASE_TOTAL:.2f} 只列示；财务公司存款 {FINCO_DEPOSIT_H1:.2f}（中报）单独列示')
    print(f'  为负 → 有杠杆口径：经调整净负债 {-NET_CASH_ADJ:.2f} 按 {DEBT_RATE:.1%} 滚动、不偿还本金')
    print()
    print('== 2026 年估计 ==')
    print(f'四季度：营收 {Q4["rev"]:.0f}、毛利率 {Q4["gm"]:.1%}、减值 {Q4["imp"]:.1f} → 归母 {Q4_NP:.2f}')
    print(f'2026E 营收 {REV_2026E:.1f}，归母 {NP_2026E:.2f}，扣非扣汇兑 {EXFX_2026E:.2f}；'
          f'经营口径运行水平（扣联营与财务性净利息）{RUNRATE_OP:.2f}；2026E 市盈率 {MKT_CAP / NP_2026E:.1f}×')
    print()
    GP_26 = (REV_9M - 265.015) + Q4['rev'] * Q4['gm']
    OPEX_26 = 32.664 + Q4['opex']
    IMP_26 = 4.865 + Q4['imp']
    b = SCEN['base']
    k_b = (1 - b['tax']) * (1 - b['minority'])
    d_imp = (IMP_26 - b['imp'] * REV_2026E) * k_b
    d_gm = (b['gm'] * REV_2026E - GP_26) * k_b
    d_opex = (OPEX_26 - b['opex'] * REV_2026E) * k_b
    base_rep = normalized_np(b)[0]
    other = base_rep - EXFX_2026E - d_imp - d_gm - d_opex
    print(f'2026E 毛利率 {GP_26 / REV_2026E:.2%}、费用率 {OPEX_26 / REV_2026E:.2%}、减值 {IMP_26:.2f}（{IMP_26 / REV_2026E:.2%}）')
    print(f'正常化桥（基准）：2026E 归母 {NP_2026E:.2f} → 加回汇兑与非经常 {EXFX_2026E:.2f} → 减值率回到 {b["imp"]:.1%} {d_imp:+.2f} '
          f'→ 毛利率 {b["gm"]:.1%} {d_gm:+.2f} → 费用率 {b["opex"]:.1%} {d_opex:+.2f} → 保理折价、税率、少数股东、联营等 {other:+.2f} = {base_rep:.2f}')
    print()
    print('== 2026 正常化归母净利（亿元）==')
    for k, s in SCEN.items():
        rep, op = normalized_np(s)
        print(f'{k:5s} 报表口径（含净利息 {s["net_int"]:.1f}、联营 {s["assoc"]:.1f}）{rep:6.2f}  经营口径 {op:6.2f}  '
              f'毛利率 {s["gm"]:.1%} 费用率 {s["opex"]:.1%} 减值率 {s["imp"]:.1%} 税率 {s["tax"]:.1%} 少数股东 {s["minority"]:.1%}')
    print()
    print('== 三情景（9%）==')
    for k, s in SCEN.items():
        r = value(s)
        u = value(s, levered=False)
        cf = r['cf']
        oes = [x['oe'] for x in cf['rows']]
        gro = [oes[0] / oe_2026_runrate(s) - 1] + [oes[i] / oes[i - 1] - 1 for i in range(1, 5)]
        rr = sum(x['reinv'] for x in cf['rows']) / sum(x['np'] for x in cf['rows'])
        inc_ret = (normalized_np(s)[1] / REV_2026E) / ((s['nwc_inc'] + s['capex_inc']) * (1 - s['minority']))
        print(f"{k:5s} p={s['p']:.2f} V(有杠杆)={r['v']:.2f}  V(无杠杆对照)={u['v']:.2f}  四季度现金 {r['pv_stub']:.1f} 明确期 {r['pv_exp']:.1f} "
              f"终值 {r['pv_tv']:.1f}（占经营价值 {r['tv_share']:.0%}） 融资调整 {r['fin']:.1f} 非经营 {r['non_op']:.1f} 专项损失 −{s['specific']:.2f}")
        revs = ' '.join('%.0f' % x['rev'] for x in cf['rows'])
        nps = ' '.join('%.2f' % x['np'] for x in cf['rows'])
        oes_s = ' '.join('%.2f' % x for x in oes)
        gro_s = ' '.join('%+.1f%%' % (100 * x) for x in gro)
        print(f"      营收 {revs}；归母经营利润 {nps}")
        print(f"      所有者收益 {oes_s}；2032 {cf['term']['oe']:.2f}；增速 {gro_s}；终值增长 {s['g_term']:.1%}")
        print(f"      再投资率（2027-31 再投资 ÷ 经营利润）{rr:.1%}；稳态增量回报（正常化经营利润率 ÷ 每元新增营收的再投资）{inc_ret:.1%}")
    vw = weighted()
    vu = weighted(levered=False)
    print()
    print(f'加权 V（有杠杆）= {vw:.2f}  P/V = {PRICE / vw:.3f}  分档：{band(PRICE / vw)}')
    print(f'加权 V（无杠杆对照）= {vu:.2f}  P/V = {PRICE / vu:.3f}')
    print(f'股权成本 8%：加权 V = {weighted(0.08):.2f}；10%：加权 V = {weighted(0.10):.2f}')
    irr = implied_irr(SCEN['base'])
    print(f'现价隐含回报（基准情景流，有杠杆）= {irr:.2%}；熊市情景流 = {implied_irr(SCEN["bear"]):.2%}')
    g_perp = reverse_perpetual(SCEN['base'])
    g10, oe0 = reverse_10y(SCEN['base'])
    print(f'反向 DCF：以基准 2027 年所有者收益为起点的隐含永续增速 {g_perp:+.2%}；'
          f'以 2026 正常化所有者收益 {oe0:.2f} 为起点的隐含 10 年复合增速 {g10:+.2%}（其后 2%）')
    print(f'V 不变时各档价格：≤{0.75 * vw:.2f} 明显低估；≤{0.90 * vw:.2f} 温和低估；≤{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵')
    print('无回购专户股份（库存股 0），剔除口径与上同。')

    print()
    print('== 交叉验证 ==')
    pe_hist = [7.0, 7.6, 7.9, 14.0, 7.6, 8.5, 8.4, 9.5]          # 2018-2025 年末 PE（数据包第八节）
    pb_hist = [1.09, 1.19, 0.92, 1.91, 1.11, 1.29, 1.19, 1.19]
    med = lambda xs: (sorted(xs)[len(xs) // 2 - 1] + sorted(xs)[len(xs) // 2]) / 2
    base_rep = normalized_np(SCEN['base'])[0]
    w_rep = sum(s['p'] * normalized_np(s)[0] for s in SCEN.values())
    bvps = PARENT_EQUITY / SHARES
    print(f'历史 PE 中位 {med(pe_hist):.2f}× × 基准正常化 {base_rep:.2f} = {med(pe_hist) * base_rep / SHARES:.2f} 元；× 加权正常化 {w_rep:.2f} = {med(pe_hist) * w_rep / SHARES:.2f} 元')
    print(f'历史 PB 中位 {med(pb_hist):.2f}× × 每股归母权益 {bvps:.2f} = {med(pb_hist) * bvps:.2f} 元；现价 PB {PRICE / bvps:.2f}×')
    roe = base_rep / PARENT_EQUITY
    for g in (0.02, 0.025):
        print(f'剩余收益校验：ROE {roe:.1%}、g {g:.1%}、9% → 合理 PB {(roe - g) / (COE - g):.2f}× → {(roe - g) / (COE - g) * bvps:.2f} 元')
    dps26 = 0.5324 * (DNP_9M + Q4_NP) / SHARES
    print(f'股息：过去 12 个月 0.48 元（{0.48 / PRICE:.2%}）；2026 年承诺不低于可供分配利润 53.24%（2025 年实付 = 48.4% × 扣非），'
          f'按 2026E 扣非 {DNP_9M + Q4_NP:.2f} 估 DPS {dps26:.2f} 元（{dps26 / PRICE:.2%}）；无回购')
    b = SCEN['base']
    ebit_b = ebit_items(b, REV_2026E)
    ev = MKT_CAP - NET_CASH_ADJ - (LTEI + HELD_FOR_SALE)
    print(f'EV/EBIT：EV {ev:.1f}（市值 {MKT_CAP:.1f} + 经调整净负债 {-NET_CASH_ADJ:.1f} − 长投与待售账面 {LTEI + HELD_FOR_SALE:.1f}）÷ 基准正常化 EBIT {ebit_b:.1f} = {ev / ebit_b:.1f}×')

    print()
    print('== 证伪条件触发后的 V ==')
    f1 = weighted(probs={'bear': 0.60, 'base': 0.35, 'bull': 0.05})
    print(f'F1 2026 年扣非扣汇兑归母 < 19.5 亿或 2027H1 扣非 < 9.0 亿 → 权重 60/35/5：V = {f1:.2f}')
    f2 = weighted(scen=variant(base=dict(imp=0.020), bull=dict(imp=0.015)))
    print(f'F2 2026 年减值合计 > 12 亿或 2027 年 > 10 亿 → 基准减值率 2.0%、乐观 1.5%：V = {f2:.2f}')
    f3 = weighted(scen=variant(base=dict(creep=[0.010, 0.008, 0.006, 0.004, 0.002], stub_fcf=10.0),
                               bull=dict(creep=[0.005, 0.003, 0.0, 0.0, 0.0])))
    print(f'F3 2026 年经营现金流 < 15 亿或年末两金/营收 > 23.5% → 基准改走悲观两金路径：V = {f3:.2f}')
    f4 = weighted(scen=variant(base=dict(g=[-0.01, 0.0, 0.01, 0.01, 0.01], g_term=0.015),
                               bull=dict(g=[0.02, 0.03, 0.03, 0.03, 0.025])))
    print(f'F4 2026 年末未完合同 < 650 亿或 2027H1 新签同比 < −10% → 基准增长 −1%～1%：V = {f4:.2f}')
    f5 = weighted(scen=variant(base=dict(specific=6.0), bull=dict(specific=1.64)))
    print(f'F5 锦象执行回收 < 50% 或清峰绿能单项计提 > 3 亿 → 基准专项损失按悲观 6.0：V = {f5:.2f}')
    f123 = weighted(scen=variant(base=dict(imp=0.020, creep=[0.010, 0.008, 0.006, 0.004, 0.002], stub_fcf=10.0),
                                 bull=dict(imp=0.015, creep=[0.005, 0.003, 0.0, 0.0, 0.0])),
                    probs={'bear': 0.60, 'base': 0.35, 'bull': 0.05})
    print(f'F1+F2+F3 同时触发：V = {f123:.2f}（P/V {PRICE / f123:.3f}）')
