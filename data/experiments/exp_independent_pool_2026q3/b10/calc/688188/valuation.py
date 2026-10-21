#!/usr/bin/env python3
"""688188 柏楚电子 独立估值（OI-291 b10，价格日 2026-10-20）。

输入全部写在脚本内（金额单位亿元，股本亿股，价格元/股），来源见正文：
  2026H1_report 第 7、20、61-70、146-153 页；2025_annual_report 第 9-11、27-29、57-58 页；
  invest_20260101_042043 第 9-17 页；incentive_20260905_025062 第 20-30 页；
  2026-09-30 首次授予公告（公告编号 2026-040）。
运行：python3 valuation.py   打印三情景 V、加权 V、P/V、8%/10% 下的 V、隐含回报、反向 DCF 与证伪触发后的 V。
"""

PRICE = 97.61            # 2026-10-20 收盘，未复权（已含 2026-06-29 的 10 转 4）
SHARES = 4.0556          # 总股本，无回购专户股份
COE = 0.09
STUB = 72 / 365          # 2026-10-20 → 2026-12-31

# ---------- 1. 经调整净现金（2026-06-30） ----------
CASH = 19.8129           # 货币资金（受限仅 ETC 保证金 4,600 元）
TFA = 33.9051            # 交易性金融资产（结构性存款/理财，含募集资金现金管理 5.45 亿）
DEBT = 0.1307 + 0.0084 + 0.0172   # 短期借款（未终止确认的贴现票据）+ 一年内到期非流动负债 + 租赁负债
DECLARED_DIV = 2.3603    # 2026 中期 0.582 元/股，股东会已通过，截至价格日未除息
OPER_RESERVE = 3.0       # 经营备付：约 2 个月经营现金流出（2026H1 流出 8.70 亿/半年）
# 2026-01 变更后新募投项目中的建设投资与铺底流动资金（研发投入部分走利润表，不在此扣）：
#   新建研发中心二期 1.6720 + 智能产线机器人 (3.6119+0.2375) + 锂电焊接 (2.4926-0.5450) = 7.4690
#   减已投入 0.2400（产线 0.1265 + 锂电 0.1135，2026H1 报告第 48-49 页）
COMMITTED_PROJECT = 7.4690 - 0.2400
NET_CASH_ADJ = CASH + TFA - DEBT - DECLARED_DIV - OPER_RESERVE - COMMITTED_PROJECT
NONOP = 0.5398 + 0.1392  # 其他非流动金融资产（创投基金份额）+ 长期股权投资

# ---------- 2. 核心经营利润（EBIT：剔除利息、理财收益、公允价值变动、非经常政府补助与一次性项目） ----------
def core_ebit(op, fin_exp, inv, fv, subsidy_nr, disposal, impair_oneoff=0.0, sbc_oneoff=0.0):
    return op + fin_exp - inv - fv - subsidy_nr - disposal - impair_oneoff + sbc_oneoff

CORE = {
    '2023': core_ebit(8.2732, -0.4784, 0.3212, 0.1861, 0.1717, 0.0017, -0.0047),
    '2024': core_ebit(10.3624, -0.2626, 0.2301, 0.2369, 0.1929, 0.0000, -0.0004),
    '2025': core_ebit(12.4512, -0.3282, 0.2216, 0.4464, 0.2591, -0.0023, -0.1726, 0.0672),
    '2025H1': core_ebit(7.3486, -0.0968, 0.1370, 0.2130, 0.1564, -0.0019),
    '2026H1': core_ebit(8.8400, -0.7432, 0.1384, 0.3968, 0.3079, 0.0001),
}
REV = {'2023': 14.0711, '2024': 17.3546, '2025': 21.9563, '2025H1': 11.0348, '2026H1': 12.7825}
REV_H2_2025 = REV['2025'] - REV['2025H1']
CORE_H2_2025 = CORE['2025'] - CORE['2025H1']
MARGIN_H2_2025 = CORE_H2_2025 / REV_H2_2025

SBC_NORMAL = 0.65        # 正常化股份支付（2023-2025 年 1.10/0.69/0.54 亿；2026 计划首次授予总费用 1.52 亿）
SBC_ACCT_2026 = 0.0905 + 0.08 + 0.2217   # H1 实际 + H2 旧计划估计 + 2026 计划当年摊销
FIN_BASE = 52.0          # 2026 年平均生息金融资产

SCEN = {
    'bear': dict(p=0.25, h2_g=0.06, h2_dm=-0.05, tax=0.12, mr=0.010, fin_y=0.015,
                 growth=[-0.08, 0.04, 0.05, 0.04, 0.04], gt=0.020, roiic=0.75,
                 note='2027 年激光设备周期回落叠加切割头价格战，核心经营利润先降 8% 后低速修复；'
                      '母公司失去 10% 重点软件企业税率（税率 12%）；新业务拖累，增量回报 75%'),
    'base': dict(p=0.50, h2_g=0.12, h2_dm=-0.03, tax=0.105, mr=0.010, fin_y=0.018,
                 growth=[0.10, 0.09, 0.08, 0.07, 0.06], gt=0.025, roiic=1.50,
                 note='平面低个位数、管材/三维约 10%、焊接与产线等其他业务 25-50% 增长，'
                      '收入 11-12%/年，毛利率每年降约 1 个百分点，所有者收益 10%→6%，2032-36 线性降到 2.5%'),
    'bull': dict(p=0.25, h2_g=0.17, h2_dm=-0.01, tax=0.10, mr=0.010, fin_y=0.020,
                 growth=[0.20, 0.18, 0.15, 0.12, 0.10], gt=0.025, roiic=2.00,
                 note='高功率与出口带动平面恢复两位数，焊接/产线成第二曲线，2028 年收入较 2025 年 +70% 以上'
                      '（接近激励目标 B），所有者收益 20%→10%'),
}


def normalize_2026(s):
    core_h2 = REV_H2_2025 * (1 + s['h2_g']) * (MARGIN_H2_2025 + s['h2_dm'])
    core_26 = CORE['2026H1'] + core_h2
    sbc_adj = SBC_NORMAL - SBC_ACCT_2026
    oe_26 = (core_26 - sbc_adj) * (1 - s['tax']) * (1 - s['mr'])
    oe_h1 = (CORE['2026H1'] - (SBC_NORMAL / 2 - 0.0905)) * (1 - s['tax']) * (1 - s['mr'])
    fin_after_tax = s['fin_y'] * FIN_BASE * (1 - s['tax'])
    return dict(core_h2=core_h2, core_26=core_26, oe_26=oe_26, oe_h2=oe_26 - oe_h1,
                fin_after_tax=fin_after_tax, np_norm=oe_26 + fin_after_tax)


def dcf(s, r=COE, growth=None, fade_years=5):
    n = normalize_2026(s)
    g = list(growth if growth is not None else s['growth'])
    gt, roiic = s['gt'], s['roiic']
    g5 = g[-1]
    path = g + [g5 + (gt - g5) * k / fade_years for k in range(1, fade_years + 1)]
    reinv = lambda oe, gg: max(gg, 0.0) / roiic * oe
    # 2026H2 存根：所有者收益减去为 2027 年增长所做的再投资（半年）
    pv = (n['oe_h2'] - 0.5 * reinv(n['oe_26'], path[0])) / (1 + r) ** (STUB / 2)
    oe = n['oe_26']
    rows = []
    for i, gg in enumerate(path):
        oe *= 1 + gg
        nxt = path[i + 1] if i + 1 < len(path) else gt
        fcf = oe - reinv(oe, nxt)
        t = STUB + i + 0.5
        pv += fcf / (1 + r) ** t
        rows.append((2027 + i, gg, oe, fcf))
    oe_t = oe * (1 + gt)
    fcf_t = oe_t * (1 - gt / roiic)
    pv_tv = fcf_t / (r - gt) / (1 + r) ** (STUB + len(path) - 0.5)
    ev = pv + pv_tv
    v = (ev + NET_CASH_ADJ + NONOP) / SHARES
    return dict(v=v, ev=ev, tv_share=pv_tv / ev, rows=rows, norm=n)


def weighted(r=COE, weights=None, growth_shift=0.0, years_shift=5):
    tot = 0.0
    for k, s in SCEN.items():
        w = s['p'] if weights is None else weights[k]
        g = [x + (growth_shift if i < years_shift else 0.0) for i, x in enumerate(s['growth'])]
        tot += w * dcf(s, r, g)['v']
    return tot


def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


if __name__ == '__main__':
    print('== 核心经营利润（亿元）与利润率 ==')
    for k in ['2023', '2024', '2025', '2025H1', '2026H1']:
        print(f'  {k}: {CORE[k]:.3f}  利润率 {CORE[k] / REV[k]:.1%}')
    print(f'  2025H2: {CORE_H2_2025:.3f}  利润率 {MARGIN_H2_2025:.1%}；2026H1 同比 {CORE["2026H1"] / CORE["2025H1"] - 1:+.1%}')
    print(f'== 经调整净现金 {NET_CASH_ADJ:.2f} 亿；非经营资产 {NONOP:.2f} 亿；每股 {(NET_CASH_ADJ + NONOP) / SHARES:.2f} 元 ==')

    res = {k: dcf(s) for k, s in SCEN.items()}
    print('== 2026 正常化（亿元） ==')
    for k, x in res.items():
        n = x['norm']
        print(f'  {k}: 核心EBIT {n["core_26"]:.2f}（H2 {n["core_h2"]:.2f}） 经营所有者收益 {n["oe_26"]:.2f} '
              f'税后财务收益 {n["fin_after_tax"]:.2f} 正常化归母净利 {n["np_norm"]:.2f}')
    print('== 三情景（股权成本 9%） ==')
    for k, x in res.items():
        path = ', '.join(f'{y}:{g:+.0%}/{oe:.1f}' for y, g, oe, _ in x['rows'][:5])
        print(f'  {k}: V={x["v"]:.2f} 元  经营价值 {x["ev"]:.1f} 亿  终值占比 {x["tv_share"]:.0%}  p={SCEN[k]["p"]}  [{path}]')
    vw = sum(SCEN[k]['p'] * res[k]['v'] for k in SCEN)
    pv = PRICE / vw
    band = '明显低估' if pv <= 0.75 else '温和低估' if pv <= 0.90 else '大致合理' if pv <= 1.10 else '偏贵或价值陷阱风险高'
    print(f'  加权 V = {vw:.2f} 元；P/V = {pv:.2f}（{band}）')
    print(f'  分档价格：≤{0.75 * vw:.2f} 明显低估；≤{0.90 * vw:.2f} 温和低估；≤{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵')
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f'== 敏感性：加权 V @8% = {v8:.2f}；@10% = {v10:.2f}；基准情景 @8% = {dcf(SCEN["base"], 0.08)["v"]:.2f}，@10% = {dcf(SCEN["base"], 0.10)["v"]:.2f}')

    irr = solve(lambda r: dcf(SCEN['base'], r)['v'], 0.03, 0.30, PRICE)
    print(f'== 现价隐含回报（基准情景现金流 + 净现金）：{irr:.2%}')

    base = SCEN['base']
    target_ev = PRICE * SHARES - NET_CASH_ADJ - NONOP

    def ev_const(g):
        s = dict(base)
        n = normalize_2026(s)
        pv = (n['oe_h2'] - 0.5 * max(g, 0) / s['roiic'] * n['oe_26']) / (1 + COE) ** (STUB / 2)
        oe = n['oe_26']
        for i in range(10):
            oe *= 1 + g
            nxt = g if i < 9 else s['gt']
            pv += (oe - max(nxt, 0) / s['roiic'] * oe) / (1 + COE) ** (STUB + i + 0.5)
        oe_t = oe * (1 + s['gt'])
        pv += oe_t * (1 - s['gt'] / s['roiic']) / (COE - s['gt']) / (1 + COE) ** (STUB + 10 - 0.5)
        return pv
    g10 = solve(ev_const, -0.2, 0.6, target_ev)

    def ev_perp(g):
        n = normalize_2026(base)
        oe27 = n['oe_26'] * (1 + g)
        return (n['oe_h2'] * (1 - g / base['roiic'])) / (1 + COE) ** (STUB / 2) + \
            oe27 * (1 - g / base['roiic']) / (COE - g) / (1 + COE) ** (STUB - 0.5)
    gp = solve(ev_perp, 0.0, 0.0899, target_ev)
    n0 = normalize_2026(base)
    print(f'== 反向 DCF：现价对应经营价值 {target_ev:.1f} 亿 = 2026 正常化经营所有者收益 {n0["oe_26"]:.2f} 亿的 '
          f'{target_ev / n0["oe_26"]:.1f} 倍；隐含 2027-36 年所有者收益增速 {g10:.1%}（之后 2.5%），或自 2027 起永续增速 {gp:.1%}')

    ebit_n = n0['core_26'] - (SBC_NORMAL - SBC_ACCT_2026)
    print(f'== 交叉：EV/正常化 EBIT = {target_ev / ebit_n:.1f}x；市值/2026 正常化归母 = {PRICE * SHARES / n0["np_norm"]:.1f}x；'
          f'市值/TTM 归母 12.60 = {PRICE * SHARES / 12.60:.1f}x')

    print('== 证伪触发后的独立 V ==')
    f1 = weighted(weights={'bear': 0.15, 'base': 0.45, 'bull': 0.40})
    f2 = weighted(growth_shift=0.03, years_shift=5)
    f3 = weighted(weights={'bear': 0.50, 'base': 0.40, 'bull': 0.10})
    f4 = weighted(growth_shift=-0.03, years_shift=5)
    print(f'  F1 2026 核心 EBIT ≥ 13.0 亿且 Q4 营收同比 ≥ 18%（权重 15/45/40）：{f1:.2f}')
    print(f'  F2 2027H1 平面收入同比 ≥ 15% 且毛利率 ≥ 74%（前 5 年增速 +3pp）：{f2:.2f}')
    print(f'  F3 Q3 单季营收同比 < 8% 或 2026 核心 EBIT < 11.6 亿（权重 50/40/10）：{f3:.2f}')
    print(f'  F4 2026 年毛利率 < 72% 或平面毛利率 < 78%（前 5 年增速 −3pp）：{f4:.2f}')
    # 已授予未归属：2026 计划 435 万（含预留）+ 2024 计划 145.16 万 + 2022 计划预留第三期约 30 万，加权行权价约 48 元
    diluted = SHARES + 0.0610 * (PRICE - 48.0) / PRICE
    print(f'== 对照：已授予未归属约 610 万股按库藏股法摊薄 {diluted / SHARES - 1:.2%}，摊薄后加权 V = {vw * SHARES / diluted:.2f}'
          '（正文不采用，费用已在正常化股份支付中扣除）')
    n_b = normalize_2026(SCEN['base'])
    h2_np = (n_b['core_h2'] + 0.50 + 0.10) * (1 - 0.105) * (1 - 0.010)
    print(f'== 参考：基准情景报表口径 2026E 归母 ≈ 7.87 + {h2_np:.2f} = {7.8715 + h2_np:.2f} 亿'
          '（H2 财务收益 0.50、非经常补助 0.10 为假设）')
