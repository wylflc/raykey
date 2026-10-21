# -*- coding: utf-8 -*-
"""苏泊尔（002032）独立估值：归母所有者收益 DCF + 经调整净现金，三情景概率加权。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。输入全部写在脚本内，出处见注释与正文。
页码为 PDF 物理页（txt 中「=== 第 N 页 ===」）。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 42.37                 # 2026-10-21 收盘，brief.md
SHARES = 7.9696               # 亿股，腾讯行情 796,964,626 股；9-24 已注销 300 万回购股，回购专户已无持股
MKT_CAP = PRICE * SHARES
T0 = date(2026, 10, 21)
COE = 0.09

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report）
CASH = 14.4476                # 货币资金，第 35、76 页
TRADING_FA = 1.5002           # 交易性金融资产（银行理财），第 35 页
CD_CURRENT = 18.2372          # 一年内到期的其他债权投资＝可转让大额存单，第 85-86 页
CD_NONCURRENT = 9.6747        # 其他债权投资＝一年以上可转让大额存单，第 87 页
GROSS_FIN = CASH + TRADING_FA + CD_CURRENT + CD_NONCURRENT

ST_BORROW = 11.8676           # 短期借款＝银行承兑汇票贴现，第 94 页（期初为 0）
SEB_LOAN = 0.1786             # 其他应付款-关联方资金拆借（SEB S.A.），第 107、122 页
LT_EMPLOYEE = 0.6033          # 长期应付职工薪酬（其他长期福利），第 97 页，按类债务扣
# 受限且服务经营性票据/经销商融资的资金：承兑汇票保证金 2.5644 + 预付款融资风险缓释金 0.58 + 电商平台保证金 0.0237（第 76、93 页）
RESTRICTED_OPER = 2.5644 + 0.5800 + 0.0237
# 质押的定期存单 0.9891 与大额存单 7.70（第 93 页）：上半年新增，与新增的票据贴现借款 11.87 同时出现，
# 视为贴现借款的担保物；借款已全额扣除，担保物按现金计。另列「全部受限都扣」的对照。
PLEDGED_FOR_DISCOUNT = 0.9891 + 7.70
OPER_RESERVE_RATE = 0.02      # 经营备付：年营收的 2%
REV_2025 = 227.7175           # 2025_annual_report 第 12 页
OPER_RESERVE = OPER_RESERVE_RATE * REV_2025
LEASE_LIAB = 2.1676 + 0.3733  # 租赁负债（含一年内到期），第 97 页：只列示、不扣（所有者收益已扣租赁利息与使用权折旧）
DECLARED_DIV = 0.0            # 6-30 无已宣派未付股利（2025 年度股利 20.96 亿已于 5-28 除息派发）

NET_CASH_ADJ = (GROSS_FIN - ST_BORROW - SEB_LOAN - LT_EMPLOYEE
                - RESTRICTED_OPER - OPER_RESERVE - DECLARED_DIV)
NET_CASH_ALL_RESTRICTED = NET_CASH_ADJ - PLEDGED_FOR_DISCOUNT
NONOP_ASSETS = 0.5984         # 长期股权投资（联营武汉安在厨具），第 36 页，按账面计

# ---------------------------------------------------------------- 已披露经营数据（东财 F10，与原文核对）
# 核心经营利润＝营收-营业成本-税金及附加-销售-管理-研发（不含其他收益、投资收益、财务费用、减值）
CORE_2025 = 227.7175 - 171.0915 - 1.3897 - 24.0900 - 3.9994 - 4.7592        # 22.3877
CORE_H1_2025 = 114.7750 - 87.6810 - 0.6483 - 11.5207 - 1.9880 - 2.1037       # 10.8333
CORE_H1_2026 = 114.0977 - 86.4417 - 0.5843 - 12.4518 - 1.8062 - 2.1385       # 10.6752
H1_2026 = dict(rev=114.0977, core=CORE_H1_2026, parent_np=8.6755)          # 2026H1_report 第 41-42 页
H2_2025 = dict(rev=227.7175 - 114.7750, core=CORE_2025 - CORE_H1_2025)
GOV_AWARDS_RUNRATE = 1.90     # 计入非经常性损益的政府补助：2023-2025 年 1.96/1.96/1.92（2025_annual_report 第 8 页）
RECUR_OTHER_RATE = 0.0030     # 增值税即征即退等经常性其他收益/营收（2025 年 0.41%，2026H1 0.28%，加计抵减减少）
IMPAIR_RATE = -0.0010         # 信用+资产减值/营收（2023-2026H1 均值约 -0.1%）
LEASE_INTEREST = 0.06         # 租赁利息/年（2025 年 0.107，2026H1 0.030），计入经营口径
NET_FIN_INCOME = 0.65         # 现金类资产净收益（存款利息+大额存单+理财-贴现利息-手续费），2026H1 年化约 0.73，利率下行取 0.65
H2_RECUR_OTHER_2026 = 0.38    # 2026H2 经常性其他收益

# ---------------------------------------------------------------- 情景
SCEN = {
    'bear': dict(
        p=0.25,
        h2_rev_g=-0.035, h2_core=0.0905, awards_2026=1.20, h2_tax=0.195,
        norm_core=0.088, awards_haircut=0.40, tax=0.205,
        rev_g=[-0.03, 0.00, 0.01, 0.01, 0.01], core=[0.088, 0.088, 0.088, 0.088, 0.088],
        g_t=0.010, rr=0.05,
        text='SEB 订单 2027 年再降约一成、出口毛利停在 15% 左右；内销费用率继续上行，核心经营利润率 8.8%；'
             '地方奖励只按 40% 计；营收 2027 年 -3%，此后 0～1%，永续 1%'),
    'base': dict(
        p=0.50,
        h2_rev_g=-0.015, h2_core=0.0985, awards_2026=1.70, h2_tax=0.185,
        norm_core=0.098, awards_haircut=0.75, tax=0.195,
        rev_g=[0.020, 0.025, 0.025, 0.025, 0.025], core=[0.098, 0.098, 0.098, 0.098, 0.098],
        g_t=0.020, rr=0.05,
        text='内销份额稳住、销售费用率不再上行，原材料涨价 2027 年基本消化，核心经营利润率 9.8%（2015-2025 均值 10.4%）；'
             'SEB 去库存结束、外销持平略增；地方奖励按 75% 计；营收 2027 年 +2%、此后 +2.5%，永续 2%'),
    'bull': dict(
        p=0.25,
        h2_rev_g=0.005, h2_core=0.1030, awards_2026=1.90, h2_tax=0.180,
        norm_core=0.102, awards_haircut=1.00, tax=0.190,
        rev_g=[0.040, 0.040, 0.035, 0.035, 0.030], core=[0.100, 0.104, 0.104, 0.104, 0.104],
        g_t=0.025, rr=0.08,
        text='SEB 继续向苏泊尔转移订单、外销恢复增长，钛材等新品带动内销份额提升，核心经营利润率回到历史均值 10.4%；'
             '奖励全额计；营收 2027-2028 年 +4%、此后 3～3.5%，永续 2.5%'),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def yearfrac(d):
    return (d - T0).days / 365.25


T_H2_2026 = 0.0               # 2026H2 现金流与 6-30 净现金一并按估值日计（H2 已过半）
T_MID = [yearfrac(date(y, 7, 1)) for y in YEARS]   # 年中折现


def scenario_flows(s):
    """2026E 报表口径归母、2026 正常化归母（含净利息）、2026H2 所有者收益、2027-2031 所有者收益。"""
    h2_rev = H2_2025['rev'] * (1 + s['h2_rev_g'])
    rev26 = H1_2026['rev'] + h2_rev
    h2_pre = (h2_rev * s['h2_core'] + H2_RECUR_OTHER_2026 + s['awards_2026']
              + IMPAIR_RATE * h2_rev - LEASE_INTEREST / 2 + NET_FIN_INCOME / 2)
    np26_reported = H1_2026['parent_np'] + h2_pre * (1 - s['h2_tax'])
    oe_h2 = (h2_pre - NET_FIN_INCOME / 2) * (1 - s['h2_tax']) * (1 - s['rr'])
    ebit26n = (rev26 * s['norm_core'] + RECUR_OTHER_RATE * rev26 + GOV_AWARDS_RUNRATE * s['awards_haircut']
               + IMPAIR_RATE * rev26 - LEASE_INTEREST)
    np26_norm = (ebit26n + NET_FIN_INCOME) * (1 - s['tax'])
    rev, oe = rev26, []
    for g, m in zip(s['rev_g'], s['core']):
        rev *= (1 + g)
        ebit = rev * m + RECUR_OTHER_RATE * rev + GOV_AWARDS_RUNRATE * s['awards_haircut'] + IMPAIR_RATE * rev - LEASE_INTEREST
        oe.append(ebit * (1 - s['tax']) * (1 - s['rr']))
    return dict(rev26=rev26, h2_rev=h2_rev, np26_reported=np26_reported, np26_norm=np26_norm,
                nopat26n=ebit26n * (1 - s['tax']), oe_h2=oe_h2, oe=oe)


def equity_value(f, s, r, net_cash=None):
    nc = NET_CASH_ADJ if net_cash is None else net_cash
    pv = f['oe_h2'] / (1 + r) ** T_H2_2026
    for cf, t in zip(f['oe'], T_MID):
        pv += cf / (1 + r) ** t
    tv = f['oe'][-1] * (1 + s['g_t']) / (r - s['g_t'])   # 2032 起的永续流，按 2031 年中折现
    pv_tv = tv / (1 + r) ** T_MID[-1]
    return pv + pv_tv + nc + NONOP_ASSETS, pv_tv


def solve(fun, lo, hi, target, it=200):
    flo = fun(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = fun(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    print('苏泊尔 002032 独立估值（价格日 2026-10-21，股权成本 9%）')
    print(f'现价 {PRICE:.2f} 元 × 总股本 {SHARES:.4f} 亿股 = 市值 {MKT_CAP:.2f} 亿元')
    print(f'现金类 {GROSS_FIN:.2f} = 货币资金 {CASH:.2f} + 理财 {TRADING_FA:.2f} + 大额存单 {CD_CURRENT + CD_NONCURRENT:.2f}')
    print(f'减：票据贴现借款 {ST_BORROW:.2f}、SEB 拆借 {SEB_LOAN:.2f}、长期应付职工薪酬 {LT_EMPLOYEE:.2f}、'
          f'经营性受限资金 {RESTRICTED_OPER:.2f}、经营备付 {OPER_RESERVE:.2f}')
    print(f'经调整净现金 {NET_CASH_ADJ:.2f} 亿（对照：质押存单 {PLEDGED_FOR_DISCOUNT:.2f} 也扣 → {NET_CASH_ALL_RESTRICTED:.2f}）；'
          f'租赁负债 {LEASE_LIAB:.2f} 只列示；非经营资产 {NONOP_ASSETS:.2f}')
    print(f'核心经营利润率：2025 {CORE_2025 / 227.7175 * 100:.2f}%，H1 2025 {CORE_H1_2025 / 114.7750 * 100:.2f}%，'
          f'H2 2025 {H2_2025["core"] / H2_2025["rev"] * 100:.2f}%，H1 2026 {CORE_H1_2026 / 114.0977 * 100:.2f}%')
    print()
    res = {}
    for k, s in SCEN.items():
        f = scenario_flows(s)
        v, pv_tv = equity_value(f, s, COE)
        v8, _ = equity_value(f, s, 0.08)
        v10, _ = equity_value(f, s, 0.10)
        v_allr, _ = equity_value(f, s, COE, net_cash=NET_CASH_ALL_RESTRICTED)
        g_oe = [f['oe'][0] / (f['nopat26n'] * (1 - s['rr'])) - 1] + [f['oe'][i] / f['oe'][i - 1] - 1 for i in range(1, 5)]
        res[k] = dict(f=f, v=v / SHARES, v8=v8 / SHARES, v10=v10 / SHARES, v_allr=v_allr / SHARES,
                      tv_share=pv_tv / v, eq=v, g_oe=g_oe)
        print(f"[{k}] p={s['p']:.2f}：{s['text']}")
        print(f"  2026E 营收 {f['rev26']:.2f}（H2 {f['h2_rev']:.2f}）；2026E 报表口径归母 {f['np26_reported']:.2f}；"
              f"2026 正常化归母（含净利息）{f['np26_norm']:.2f}")
        print(f"  所有者收益：2026H2 {f['oe_h2']:.2f}；2027-2031 " + ' / '.join(f'{x:.2f}' for x in f['oe'])
              + '；增速 ' + ' / '.join(f'{x * 100:.1f}%' for x in g_oe)
              + f"；永续 {s['g_t'] * 100:.1f}%，再投资率 {s['rr'] * 100:.0f}%")
        print(f"  股权价值 {v:.1f} 亿 → V = {v / SHARES:.2f} 元（8%：{v8 / SHARES:.2f}；10%：{v10 / SHARES:.2f}）；"
              f"终值占比 {pv_tv / v * 100:.0f}%；质押存单也扣时 V = {v_allr / SHARES:.2f}")
    w = {k: SCEN[k]['p'] for k in SCEN}
    vw = sum(w[k] * res[k]['v'] for k in SCEN)
    vw8 = sum(w[k] * res[k]['v8'] for k in SCEN)
    vw10 = sum(w[k] * res[k]['v10'] for k in SCEN)
    vw_allr = sum(w[k] * res[k]['v_allr'] for k in SCEN)
    print()
    print(f'概率加权 V = {vw:.2f} 元；P/V = {PRICE / vw:.3f}')
    print(f'  8% 下 V = {vw8:.2f}（P/V {PRICE / vw8:.3f}）；10% 下 V = {vw10:.2f}（P/V {PRICE / vw10:.3f}）；'
          f'质押存单也扣 V = {vw_allr:.2f}（P/V {PRICE / vw_allr:.3f}）')
    for lab, thr in [('明显低估', 0.75), ('温和低估', 0.90), ('大致合理', 1.10)]:
        print(f'  V 不变时进入「{lab}」的价格上限：{vw * thr:.2f} 元')

    sb, fb = SCEN['base'], res['base']['f']
    irr = solve(lambda r: equity_value(fb, sb, r)[0], 0.03, 0.30, MKT_CAP)
    irr_w = solve(lambda r: sum(w[k] * equity_value(res[k]['f'], SCEN[k], r)[0] for k in SCEN), 0.03, 0.30, MKT_CAP)
    print(f'现价隐含回报：基准情景 {irr * 100:.2f}%；三情景加权现金流 {irr_w * 100:.2f}%')

    # 反向 DCF：以 2026 正常化所有者收益为起点
    oe_start = fb['nopat26n'] * (1 - sb['rr'])

    def v_growth(g, n_years, g_term):
        pv, cf = fb['oe_h2'], oe_start
        ts = [yearfrac(date(y, 7, 1)) for y in range(2027, 2027 + n_years)]
        for t in ts:
            cf *= (1 + g)
            pv += cf / (1 + COE) ** t
        gt = g if g_term is None else g_term
        return pv + cf * (1 + gt) / (COE - gt) / (1 + COE) ** ts[-1] + NET_CASH_ADJ + NONOP_ASSETS

    g_perp = solve(lambda g: v_growth(g, 5, None), -0.05, 0.085, MKT_CAP)
    g10 = solve(lambda g: v_growth(g, 10, 0.025), -0.05, 0.20, MKT_CAP)
    print(f'反向 DCF（9%，起点 2026 正常化所有者收益 {oe_start:.2f} 亿）：现价隐含永续增速 {g_perp * 100:.2f}%；'
          f'或前 10 年 {g10 * 100:.2f}% 后接 2.5% 永续')

    # 交叉验证
    ev = MKT_CAP - NET_CASH_ADJ - NONOP_ASSETS
    ebit25 = CORE_2025 + 2.8509 - 0.0703 - 0.1066        # + 其他收益 - 减值 - 租赁利息
    print(f'交叉：EV {ev:.1f} 亿；EV/EBIT(2025，含奖励) {ev / ebit25:.1f}x，(不含奖励 1.92) {ev / (ebit25 - 1.9216):.1f}x；'
          f'PE：TTM {MKT_CAP / 20.24:.1f}x，2026E 基准 {MKT_CAP / fb["np26_reported"]:.1f}x；'
          f'股息率：TTM {2.63 / PRICE * 100:.2f}%，2026E（全额派息）{fb["np26_reported"] / SHARES / PRICE * 100:.2f}%')
    # 内外销利润拆分（2025）：外销 74.38 亿、毛利率 17.19%，外销分摊费用按营收 2.5% 假设
    exp_rev, exp_gm, exp_opex = 74.3796, 0.1719, 0.025
    exp_ebit = exp_rev * (exp_gm - exp_opex)
    print(f'2025 内外销拆分（假设外销费用率 2.5%）：外销核心利润 {exp_ebit:.2f}（{exp_ebit / CORE_2025 * 100:.0f}%），'
          f'内销 {CORE_2025 - exp_ebit:.2f}；外销毛利率每 1pp ≈ 税前 {exp_rev * 0.01:.2f} 亿')
    # 期权摊薄（库存股法）：在有效期内期权 415.378 万份（含 2026 年 104.30 万份、行权价 31.21）
    opt, k_avg = 0.0415378, 33.0
    dil = opt * max(PRICE - k_avg, 0) / PRICE
    print(f'期权摊薄（库存股法，平均行权价按 {k_avg} 元估）：约 {dil * 1e4:.0f} 万股，占 {dil / SHARES * 100:.2f}%，忽略')

    # 基准情景敏感性：核心经营利润率 × 永续增速（9%）
    print('基准情景 V 敏感性（行：核心经营利润率；列：永续增速）：')
    print('          ' + ''.join(f'{gt * 100:>8.1f}%' for gt in (0.015, 0.020, 0.025)))
    for m in (0.093, 0.098, 0.103):
        row = []
        for gt in (0.015, 0.020, 0.025):
            s2 = dict(sb, core=[m] * 5, norm_core=m, g_t=gt)
            f2 = scenario_flows(s2)
            row.append(equity_value(f2, s2, COE)[0] / SHARES)
        print(f'  {m * 100:5.1f}%  ' + ''.join(f'{x:>9.2f}' for x in row))

    # 口径对照：经营备付取 0；基准地方奖励全额计入
    v_no_reserve = vw + OPER_RESERVE / SHARES
    s3 = dict(sb, awards_haircut=1.00)
    v_base_full_awards = equity_value(scenario_flows(s3), s3, COE)[0] / SHARES
    print(f'口径对照：经营备付取 0 时加权 V = {v_no_reserve:.2f}（+{OPER_RESERVE / SHARES:.2f}）；'
          f'基准地方奖励全额计入时基准 V = {v_base_full_awards:.2f}（+{v_base_full_awards - res["base"]["v"]:.2f}）')

    print()
    print('证伪条件（触发后独立 V，9%）：')
    v_f1 = 0.5 * res['bear']['v'] + 0.4 * res['base']['v'] + 0.1 * res['bull']['v']
    v_f2 = 0.45 * res['bear']['v'] + 0.45 * res['base']['v'] + 0.10 * res['bull']['v']
    # F3：出口代工毛利率较 2025 年少 2.2pp 并长期化：税前约 -1.54 亿/年
    loss_f3 = 70.0 * 0.022 * (1 - sb['tax']) * (1 - sb['rr'])
    v_f3 = vw - loss_f3 / (COE - sb['g_t']) / SHARES
    v_f4 = res['bear']['v']
    v_f5 = 0.10 * res['bear']['v'] + 0.45 * res['base']['v'] + 0.45 * res['bull']['v']
    fals = [
        ('F1 2026 年归母净利 < 18.0 亿（2027-04-30 前年报）→ 熊/基/牛 0.5/0.4/0.1', v_f1),
        ('F2 2026 年 SEB 关联销售 < 62 亿，或 2027 年关联交易预计 < 65 亿（2027-04-30 前）→ 0.45/0.45/0.10', v_f2),
        ('F3 2026 年出口代工毛利率 < 15.0%（2025 年 17.19%）且 2027H1 未回到 16% → 定价条款实质下调', v_f3),
        ('F4 2027H1 核心经营利润率 < 8.5% 或销售费用率 > 11.5%（2027-08-31）→ 熊情景', v_f4),
        ('F5（向上）2027H1 归母 ≥ 9.5 亿且外销同比转正（2027-08-31）→ 0.10/0.45/0.45', v_f5),
    ]
    for lab, v in fals:
        print(f'  {lab}：V = {v:.2f}，P/V = {PRICE / v:.2f}')

    print()
    print('汇总')
    print('  三情景 V：' + '，'.join(f"{k} {res[k]['v']:.2f}（p={SCEN[k]['p']:.2f}）" for k in SCEN))
    print(f'  加权 V {vw:.2f}；P/V {PRICE / vw:.3f}；V@8% {vw8:.2f}；V@10% {vw10:.2f}；隐含回报 {irr * 100:.2f}%')
    print('  2026 正常化归母净利：' + '，'.join(f"{k} {res[k]['f']['np26_norm']:.2f}" for k in SCEN))
    print('  2026E 报表口径归母净利：' + '，'.join(f"{k} {res[k]['f']['np26_reported']:.2f}" for k in SCEN))
    print('  基准所有者收益增速 2027-2031：' + ' / '.join(f'{x * 100:.2f}%' for x in res['base']['g_oe'])
          + f"；基准终值占股权价值 {res['base']['tv_share'] * 100:.1f}%")
    return res, vw


if __name__ == '__main__':
    main()
