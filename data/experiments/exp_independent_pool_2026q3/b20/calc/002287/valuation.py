# -*- coding: utf-8 -*-
"""奇正藏药（002287）独立估值（OI-291 b20，价格日 2026-10-21）。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在脚本内，来源见正文「来源」一节。
口径：无杠杆所有者收益 DCF（核心经营利润，不含金融收益）+ 经调整净现金 + 非经营资产 ± 情景调整项。
经调整净现金为正，按框架全额扣除有息负债；奇正转债已于 2025-09 全部转股/赎回并摘牌，无可转债取低。
"""

PRICE = 19.23
SHARES = 5.7212              # 总股本（含回购专户股份），亿股
TREASURY = 0.05239895        # 回购专户 5,239,895 股，用途为股权激励/员工持股，未公告注销
SHARES_EX = SHARES - TREASURY
COE = 0.09
T_H2 = 0.10                  # 2026H2 所有者收益折现年数（估值日 2026-10-21）
T_2027 = 0.69                # 2027 年中点距估值日的年数；以后每年 +1

# ---------------- 经调整净现金（2026-06-30，2026H1 报告附注） ----------------
CASH = 2.9367339             # 货币资金（p98）
RESTRICTED = 0.1183429 + 0.0030304   # 员工持股计划处置款（2026-08 已清算发放）+ 保函保证金（p131）
CD = 25.5517200              # 交易性金融资产 = 可转让大额存单（p98）
TD_CUR = 0.9356856           # 其他流动资产中的定期存款及利息（p114）
TD_NONCUR = 2.0163909        # 其他非流动资产中的定期存款及利息（p131）
PF = 4.1589425               # 其他非流动金融资产-理财产品：单一委托人私募证券基金（债权类，2053 到期）（p119；年报 p70）
PF_HAIRCUT = 0.10            # 流动性与信用折扣
DEBT = 8.7967412 + 0.25 + 0.0500938 + 0.026   # 短期借款 + 长期借款 + 一年内到期长期借款 + 长期应付款
DIV_AFTER = 0.23 * 5.66878308                 # 2026 中期分红（2026-09-23 发放），按剔除回购股后的股本
OP_RESERVE = 1.0                              # 经营备付：约 1 个月付现成本
LEASE = 0.0278457 + 0.0466196                 # 租赁负债（含一年内到期）：只列示不扣
CASH_LIKE = CASH - RESTRICTED + CD + TD_CUR + TD_NONCUR + PF * (1 - PF_HAIRCUT)
NET_CASH_ADJ = CASH_LIKE - DEBT - DIV_AFTER - OP_RESERVE
NON_OP = 0.4400071 + 0.4928173 * 0.5          # 权益工具投资按账面；联营企业（权益法连年亏损）按 50%
LHASA_REMAIN = 5.0 * (1 - 0.5775)             # 拉萨宇妥德堂林家园：预算 5 亿，投入进度 57.75%，剩余预算
NET_FIN_2026 = 0.60          # 2026 年税前净金融收益（大额存单/理财公允价值变动 + 利息收入 − 借款利息 − 贴现息）

# ---------------- 2026H1 实际与 2025H2 基数 ----------------
H1 = dict(rev=9.7797, cogs=1.7527, tax_add=0.1685, sale=3.3102, mgmt=0.7874, rnd=0.3292, imp=-0.0461)
H1_CORE = H1['rev'] - H1['cogs'] - H1['tax_add'] - H1['sale'] - H1['mgmt'] - H1['rnd'] + H1['imp']
H2_2025 = dict(rev=12.4096, sale=6.2994, mgmt=1.0156, rnd=0.4889)
CORE_2025 = 24.1601 - 4.0947 - 0.3980 - 10.9562 - 1.8936 - 0.8103 - 0.0110
CORE_H1_2025 = 11.7506 - 2.0924 - 0.2301 - 4.6568 - 0.8780 - 0.3213 + 0.0075
CORE_TTM = CORE_2025 - CORE_H1_2025 + H1_CORE
PROJECT_CAPEX = {'2026H2': 0.30, 2027: 0.35}   # 甘肃车间改造、提取纯化、藏药集团基地等剩余投入

SCEN = {
    'bear': dict(p=0.30,
                 h2=dict(rev_g=-0.17, gm=0.820, sale_g=-0.15, mgmt_g=-0.03, imp=-0.06),
                 g=[-0.05, -0.03, -0.01, 0.00, 0.01], margin=0.24, tg=0.005, ronic_t=0.12,
                 tax_early=0.115, tax_late=0.165, subsidy_cash=0.0, subsidy_pl=0.25,
                 donation=0.15, extra_capex=0.20, wc_ratio=0.40, lhasa_recovery=0.0, pf_extra=0.20),
    'base': dict(p=0.50,
                 h2=dict(rev_g=-0.10, gm=0.830, sale_g=-0.22, mgmt_g=-0.07, imp=-0.04),
                 g=[0.02, 0.03, 0.03, 0.03, 0.025], margin=0.285, tg=0.02, ronic_t=0.20,
                 tax_early=0.115, tax_late=0.135, subsidy_cash=0.30, subsidy_pl=0.55,
                 donation=0.10, extra_capex=0.15, wc_ratio=0.40, lhasa_recovery=0.5, pf_extra=0.0),
    'bull': dict(p=0.20,
                 h2=dict(rev_g=-0.05, gm=0.835, sale_g=-0.27, mgmt_g=-0.08, imp=-0.03),
                 g=[0.06, 0.06, 0.05, 0.05, 0.04], margin=0.31, tg=0.025, ronic_t=0.25,
                 tax_early=0.115, tax_late=0.115, subsidy_cash=0.60, subsidy_pl=0.85,
                 donation=0.05, extra_capex=0.10, wc_ratio=0.40, lhasa_recovery=1.0, pf_extra=-0.10),
}
TAX_ADD_RATIO = 0.014        # 税金及附加 / 营收（2025H2 为 1.35%）


def h2_2026(s):
    h = s['h2']
    rev = H2_2025['rev'] * (1 + h['rev_g'])
    core = rev * h['gm'] - H2_2025['sale'] * (1 + h['sale_g']) - H2_2025['mgmt'] * (1 + h['mgmt_g']) \
        - H2_2025['rnd'] - rev * TAX_ADD_RATIO + h['imp']
    return rev, core


def run(s, coe=COE, margin=None, growth=None, tax_late=None, detail=False):
    margin = s['margin'] if margin is None else margin
    growth = s['g'] if growth is None else growth
    t1 = s['tax_early']
    t2 = s['tax_late'] if tax_late is None else tax_late
    h2_rev, h2_core = h2_2026(s)
    rev26, core26 = H1['rev'] + h2_rev, H1_CORE + h2_core
    oe_h2 = h2_core * (1 - t1) + s['subsidy_cash'] / 2 * (1 - t1) - s['donation'] / 2 \
        - s['extra_capex'] / 2 - PROJECT_CAPEX['2026H2']
    pv = oe_h2 / (1 + coe) ** T_H2
    rows, rev_prev = [], rev26
    for i, g in enumerate(growth):
        yr = 2027 + i
        rev = rev_prev * (1 + g)
        tax = t1 if yr <= 2027 else t2
        nopat = rev * margin * (1 - tax)
        reinv = max(0.0, (rev - rev_prev) * s['wc_ratio'])
        oe = nopat + s['subsidy_cash'] * (1 - tax) - s['donation'] - s['extra_capex'] - reinv \
            - PROJECT_CAPEX.get(yr, 0.0)
        pv += oe / (1 + coe) ** (T_2027 + i)
        rows.append(dict(yr=yr, rev=rev, ebit=rev * margin, nopat=nopat, reinv=reinv, oe=oe))
        rev_prev = rev
    tg = s['tg']
    nopat_t = rev_prev * (1 + tg) * margin * (1 - t2)
    oe_t = nopat_t * (1 - tg / s['ronic_t']) + s['subsidy_cash'] * (1 - t2) - s['donation'] - s['extra_capex']
    pv_tv = oe_t / (coe - tg) / (1 + coe) ** (T_2027 + len(growth) - 1)
    adj = -LHASA_REMAIN * (1 - s['lhasa_recovery']) - PF * s['pf_extra']
    equity = pv + pv_tv + NET_CASH_ADJ + NON_OP + adj
    v = equity / SHARES
    if not detail:
        return v
    return dict(v=v, v_ex=equity / SHARES_EX, equity=equity, pv_explicit=pv, pv_tv=pv_tv,
                tv_share=pv_tv / (pv + pv_tv), rev26=rev26, core26=core26, h2_rev=h2_rev, h2_core=h2_core,
                oe_h2=oe_h2, rows=rows, oe_t=oe_t, adj=adj)


def weighted(coe=COE, probs=None):
    probs = probs or {k: s['p'] for k, s in SCEN.items()}
    return sum(probs[k] * run(SCEN[k], coe) for k in SCEN)


def solve(f, lo, hi, target, n=200):
    """二分：f 单调，返回 f(x)=target 的 x。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def norm_np_2026(s):
    """2026 正常化归母净利（报表口径，含净利息，剔除一次性；补助按情景保留可持续部分；少数股东承担亏损约 +0.02）。"""
    core26 = run(s, detail=True)['core26']
    return (core26 + s['subsidy_pl'] - s['donation'] + NET_FIN_2026) * (1 - s['tax_early']) + 0.02


def growth_path(s):
    """所有者收益（不含一次性项目投入）的逐年增速：2026 全年为基数。"""
    d = run(s, detail=True)
    t1 = s['tax_early']
    oe26 = d['core26'] * (1 - t1) + s['subsidy_cash'] * (1 - t1) - s['donation'] - s['extra_capex']
    seq = [oe26] + [r['oe'] + PROJECT_CAPEX.get(r['yr'], 0.0) for r in d['rows']]
    g = [seq[i + 1] / seq[i] - 1 for i in range(len(seq) - 1)]
    reinv = sum(r['reinv'] for r in d['rows']) / sum(r['nopat'] for r in d['rows'])
    return oe26, seq[1:], g, reinv


def reverse_dcf():
    b = SCEN['base']
    d = run(b, detail=True)
    nopat27 = d['rows'][0]['nopat']
    fixed = NET_CASH_ADJ + NON_OP + d['adj'] + d['oe_h2'] / (1 + COE) ** T_H2 \
        - PROJECT_CAPEX[2027] / (1 + COE) ** T_2027
    extra = b['subsidy_cash'] * (1 - b['tax_late']) - b['donation'] - b['extra_capex']

    def v_perp(g):   # 2027 年起所有者收益永续增长 g，再投资率 g/20%
        x = nopat27 * (1 - g / 0.20) + extra
        return (fixed + x * (1 + COE) ** (1 - T_2027) / (COE - g)) / SHARES

    def v_10y(x):    # 2027 NOPAT 起 10 年年增 x，再投资率 x/20%；之后 2.5% 永续
        tot, n = 0.0, nopat27
        for k in range(10):
            if k > 0:
                n *= 1 + x
            tot += (n * (1 - max(x, 0) / 0.20) + extra) / (1 + COE) ** (T_2027 + k)
        n_t = n * 1.025
        tot += (n_t * (1 - 0.025 / 0.20) + extra) / (COE - 0.025) / (1 + COE) ** (T_2027 + 9)
        return (fixed + tot) / SHARES

    return solve(v_perp, -0.05, 0.085, PRICE), solve(v_10y, -0.10, 0.20, PRICE)


def verdict(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


if __name__ == '__main__':
    print('== 经调整净现金（亿元，2026-06-30）')
    print(f'  现金类 {CASH_LIKE:.2f}（货币资金 {CASH:.2f} − 受限 {RESTRICTED:.2f} + 大额存单 {CD:.2f} + 定期存款 {TD_CUR + TD_NONCUR:.2f}'
          f' + 私募基金 {PF:.2f}×{1 - PF_HAIRCUT:.0%}）')
    print(f'  − 有息负债 {DEBT:.2f} − 已宣派股利 {DIV_AFTER:.2f} − 经营备付 {OP_RESERVE:.2f} = 经调整净现金 {NET_CASH_ADJ:.2f}'
          f'（每股 {NET_CASH_ADJ / SHARES:.2f}）；租赁负债 {LEASE:.3f} 只列示')
    print(f'  非经营资产 {NON_OP:.2f}；拉萨项目剩余预算 {LHASA_REMAIN:.2f}')
    print(f'== 核心 EBIT（营收−成本−税金附加−销售−管理−研发±减值，不含补助与金融收益）：2025 {CORE_2025:.2f}，'
          f'2025H1 {CORE_H1_2025:.2f}，2026H1 {H1_CORE:.2f}，TTM {CORE_TTM:.2f}')
    res = {}
    for k, s in SCEN.items():
        d = run(s, detail=True)
        res[k] = d
        print(f"== {k}（p={s['p']:.2f}）V={d['v']:.2f}（剔除回购股 {d['v_ex']:.2f}） 股权 {d['equity']:.1f}："
              f"显性期 PV {d['pv_explicit']:.1f} + 终值 PV {d['pv_tv']:.1f}（终值占 {d['tv_share']:.0%}）"
              f" + 净现金 {NET_CASH_ADJ:.1f} + 非经营 {NON_OP:.2f} + 调整 {d['adj']:.2f}")
        print(f"   2026E 营收 {d['rev26']:.2f}（H2 {d['h2_rev']:.2f}），核心 EBIT {d['core26']:.2f}（H2 {d['h2_core']:.2f}），"
              f"利润率 {d['core26'] / d['rev26']:.1%}；2026H2 所有者收益 {d['oe_h2']:.2f}")
        for r in d['rows']:
            print(f"   {r['yr']} 营收 {r['rev']:.2f} EBIT {r['ebit']:.2f} NOPAT {r['nopat']:.2f} 再投资 {r['reinv']:.2f} 所有者收益 {r['oe']:.2f}")
        print(f"   终值首年所有者收益 {d['oe_t']:.2f}，g={s['tg']:.1%}，终值再投资率 {s['tg'] / s['ronic_t']:.1%}")
        print(f"   2026 正常化归母净利 {norm_np_2026(s):.2f}")
    vw = weighted()
    pv_ratio = PRICE / vw
    vw_ex = vw * SHARES / SHARES_EX
    print(f'== 加权 V {vw:.2f}，P/V {pv_ratio:.3f}（{verdict(pv_ratio)}）；剔除回购股 V {vw_ex:.2f}，P/V {PRICE / vw_ex:.3f}')
    print(f'   股权成本 8%：V {weighted(0.08):.2f}；10%：V {weighted(0.10):.2f}')
    irr = solve(lambda r: run(SCEN["base"], r), 0.03, 0.30, PRICE)
    irr_w = solve(lambda r: weighted(r), 0.03, 0.30, PRICE)
    print(f'   现价隐含回报（基准情景）{irr:.2%}；按三情景加权 {irr_w:.2%}')
    g_perp, g_10 = reverse_dcf()
    print(f'   反向 DCF：基准利润率与税率下，2027 年起所有者收益永续增速 {g_perp:.2%}；或 NOPAT 10 年年增 {g_10:.2%} 后接 2.5% 永续')
    # 交叉验证
    ev = PRICE * SHARES - NET_CASH_ADJ - NON_OP
    core_nopat_ttm = CORE_TTM * (1 - 0.115)
    print(f'== 交叉验证：市值 {PRICE * SHARES:.1f}，经营 EV {ev:.1f}；EV/核心 EBIT(TTM {CORE_TTM:.2f}) {ev / CORE_TTM:.1f}x；'
          f'EV/2026E 基准核心 EBIT {ev / res["base"]["core26"]:.1f}x；剔除净现金 P/E（核心 NOPAT TTM {core_nopat_ttm:.2f}）{ev / core_nopat_ttm:.1f}x')
    print(f'   近 12 个月每股分红 0.64，股息率 {0.64 / PRICE:.2%}；2025 年回购 1.37 亿（市值的 {1.37 / (PRICE * SHARES):.2%}，非常态）')
    # 证伪条件触发后的 V
    f1 = weighted(probs={'bear': 0.5, 'base': 0.5, 'bull': 0.0})
    f2 = weighted(probs={'bear': 0.7, 'base': 0.3, 'bull': 0.0})
    f3 = run(SCEN['bear'])
    f4 = weighted(probs={'bear': 0.0, 'base': 0.5, 'bull': 0.5})
    f5 = (SCEN['bear']['p'] * run(SCEN['bear']) + SCEN['base']['p'] * run(SCEN['base'], tax_late=0.165)
          + SCEN['bull']['p'] * run(SCEN['bull'], tax_late=0.165))
    print('== 证伪条件触发后的 V')
    print(f'   F1 三季报 Q3 单季营收 < 3.0 亿，或前三季度销售费用率 ≥ 40%（基准约 38%）：V {f1:.2f}')
    print(f'   F2 2026 年营收 < 20.3 亿且核心 EBIT < 5.3 亿：V {f2:.2f}')
    print(f'   F3 消痛贴膏纳入国家或省际联盟集采、院内降价 ≥ 30%：V {f3:.2f}')
    print(f'   F4（向上）2027H1 营收 ≥ 10.8 亿且销售费用率 ≤ 36%：V {f4:.2f}')
    print(f'   F5 西藏地方分享部分免征 2027 年后不延续（税率 16.5%）：V {f5:.2f}')
    for k in ('bear', 'base', 'bull'):
        oe26, oes, gp, reinv = growth_path(SCEN[k])
        print(f'== {k} 所有者收益（不含一次性项目投入）：2026 {oe26:.2f}；2027-2031 ' + ', '.join(f'{x:.2f}' for x in oes)
              + '；增速 ' + ', '.join(f'{x:+.1%}' for x in gp) + f'；显性期再投资率 {reinv:.1%}')
    # 基准 Q3 估计（2026H2 按 Q3:Q4 拆分）
    q3_rev = 3.4789 * 0.965
    q3_sale = 2.198 * (1 + SCEN['base']['h2']['sale_g'])
    q3_core = q3_rev * 0.825 - q3_sale - 0.4435 * 0.93 - 0.1752 - q3_rev * TAX_ADD_RATIO - 0.02
    q3_np = (q3_core + 0.25 + 0.15 - 0.03) * (1 - 0.115) + 0.005
    print(f'== 基准三季度估计：营收 {q3_rev:.2f}，销售费用 {q3_sale:.2f}，核心 EBIT {q3_core:.2f}，归母净利约 {q3_np:.2f}；'
          f'前三季度营收 {9.7797 + q3_rev:.2f}、归母净利约 {3.7129 + q3_np:.2f}、销售费用率 {(3.3102 + q3_sale) / (9.7797 + q3_rev):.1%}')
    print('== V 不变时进入各档的价格：'
          f'明显低估 ≤ {0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}～{0.90 * vw:.2f}；大致合理 {0.90 * vw:.2f}～{1.10 * vw:.2f}；偏贵 > {1.10 * vw:.2f}')
