# -*- coding: utf-8 -*-
"""
恒瑞医药（600276）独立估值（OI-291 b11，价格日 2026-10-20）

方法：所有者收益 DCF，研发投入（费用化+资本化）全额作为当期费用；股权成本 9%（敏感性 8%/10%），
终值增长 2.5%；经调整净现金为正，按无杠杆口径全额加回；无可转债。
金额单位：亿元人民币；每股价值：元/股（按 A+H 总股本 66.3720 亿股，含回购专户）。
运行：python3 valuation.py（无外部依赖）。

主要出处（页码为 PDF 物理页）：
  2026H1_report 第 20-22 页（创新药 88.09、仿制药 51.39、许可收入 14.22、BMS 首付款预期三季度到账）
  2026H1_report 第 75-81 页（报表）、第 129 页（Kailera 9.30%、Braveheart）、第 138 页（合同负债 17.32）
  2026H1_report 第 143 页（A 股 6,379,002,274 股、H 股 258,197,600 股；库存股）、第 154 页（美元存款、6.8109）
  2026H1_report 第 157 页（研发总投入 46.05、资本化 11.12）
  2025_annual_report 第 19-20、61、203 页（创新药 163.42、许可收入 33.92、研发 87.24/资本化 17.63）
  incentive_20260820_162528 第 3、14 页（受让价 26.21 元、创新药收入考核 192/432/732 亿元）
  2026-09-29 诺和授权公告（3 亿美元首付款、预计 2026Q4 交割）
  网络：KLRA 2026-10-20 收盘 12.89 美元；1276.HK 49.52 港元；2026-10-16 中间价 USD 6.7220、HKD 0.85658
"""
import json

# ---------------------------------------------------------------- 市场与股本
PRICE_A = 47.45
SH_A, SH_H = 63.7900, 2.5820
SHARES = 66.3720                # 总股本（含回购专户）；新回购用途为员工持股计划，无拟注销股份
TREASURY = 0.135                # 回购专户估计约 1,350 万股（员工持股计划受让上限 1,285.5 万股 + 9-10 月回购约 78 万股）
PRICE_H_HKD = 49.52
HKD_CNY = 0.85658
USD_CNY = 6.7220
VAL_T = 2026 + 293 / 365        # 估值日 2026-10-20
COE = 0.09
TG = 0.025

# ---------------------------------------------------------------- 资产负债表调整（2026-06-30）
CASH = 387.343
RESTRICTED = 0.127              # 保函保证金（冻结）
TRADING_FA = 1.075              # 交易性金融资产（新和成、康龙化成、迈瑞医疗等股票）
DEBT = 0.298 + 0.382            # 一年内到期非流动负债 + 租赁负债；期末无银行借款
OP_RESERVE = 20.0               # 经营备付：约 1 个月现金经营支出（2025 年现金经营支出约 241 亿元）
USD_CASH = 28.0858              # 美元存款 28.09 亿美元，期末汇率 6.8109
FX_REVAL = USD_CASH * (USD_CNY - 6.8109)
NET_CASH_ADJ = CASH - RESTRICTED + TRADING_FA - DEBT - OP_RESERVE + FX_REVAL
# 合同负债 17.32（其中其他非流动负债 7.83）为 GSK 首付款递延，现金已在账上，不作债务扣除，其后续确认也不计入所有者收益。

# 非经营资产
KLRA_SHARES_M = 0.0930 * 129.64            # 持股 9.30% × 已发行 1.2964 亿股（百万股）
KLRA_PX = 12.89
KLRA_VAL = KLRA_SHARES_M * KLRA_PX * USD_CNY / 100
KLRA_COST = 3.541
KLRA_NET = KLRA_VAL - 0.15 * (KLRA_VAL - KLRA_COST)   # 扣除浮盈所得税
OTHER_FIN = 23.154 - 17.273                 # Braveheart 2.48 + 医药基金与其他股权 3.40（账面）
LTEI = 8.006 * 0.7                           # 联营企业账面打七折；其投资损失不计入经营所有者收益
MINORITY = 5.233
NON_OP = KLRA_NET + OTHER_FIN + LTEI

# 期后现金项目（税后；授权所得按 15%）
T_LIC = 0.15
BMS_UPFRONT = 6.00 * USD_CNY * (1 - T_LIC)
NOVO_UPFRONT = 3.00 * USD_CNY * (1 - T_LIC)
H2_INTEREST = 7.013 / 181 * 112 * (1 - T_LIC)
BUYBACK_SEP_OCT = -0.35
ESOP_INFLOW = 0.12855 * 26.21
POST_ITEMS = BMS_UPFRONT + NOVO_UPFRONT + H2_INTEREST + BUYBACK_SEP_OCT + ESOP_INFLOW
BMS_ANNIV1 = 1.75 * USD_CNY * (1 - T_LIC)    # 2027 年第一笔周年付款
BMS_ANNIV2 = 1.75 * USD_CNY * (1 - T_LIC)    # 2028 年第二笔（有条件），按情景概率计

# ---------------------------------------------------------------- 2026 年：上半年实际 + 下半年估计
# 上半年核心经营利润（研发全额费用化）= 产品及其他收入 140.333 − 成本（不含许可成本）20.911 − 税金及附加 1.409
#   − 销售 43.409 − 管理 12.575 − 研发总投入 46.051 + 加回资本化研发摊销 0.745 + 经常性其他收益 0.364
#   − 减值 0.166 − 营业外支出经常部分 0.68（营业外净支出的一半）；不含许可收入、利息、汇兑、公允价值变动、联营损益
H1_INNOV, H1_GEN = 88.09, 51.39
H1_EBIT = 140.333 - 20.911 - 1.409 - 43.409 - 12.575 - 46.051 + 0.745 + 0.364 - 0.166 - 0.68
INNOV_25, GEN_25 = 163.42, 280.134 - 163.42
H2_INNOV_25 = INNOV_25 - H1_INNOV / 1.1638     # 2025 下半年创新药约 87.73
H2_GEN_25 = GEN_25 - H1_GEN / (1 - 0.1607)     # 2025 下半年仿制药约 55.47

T_CORE = 0.12                    # 核心经营有效税率（2025 年 11.4%，2026H1 9.8%）
NWC_RATE, CAPEX_RATE, CAPEX_FIX = 0.25, 0.04, 1.0   # 再投资 = 1.0 + (4% 净资本开支 + 25% 营运资本) × 产品收入增量
OTHER_2026 = -1.9                # 经常性其他（其他收益、减值、营业外经常部分），每年 +2%

YEARS = list(range(2027, 2037))

SCEN = {
    'bear': dict(
        name='熊', p=0.25,
        h2_innov_g=0.05, h2_gen_g=-0.16, h2_cogs=0.143, h2_sell=47.0, h2_ga=15.2, h2_rd=49.5,
        g_innov=[0.12, 0.10, 0.07, 0.05, 0.04, 0.03, 0.03, 0.03, 0.03, 0.03],
        g_gen=[-0.12, -0.09, -0.07, -0.05, -0.04, -0.03, -0.03, -0.03, -0.03, -0.03],
        r2031=dict(cogs=0.148, sell=0.295, ga=0.090, rd=0.285), r2036=dict(cogs=0.150, sell=0.280, ga=0.085, rd=0.250),
        upf=1.00, ms0=0.40, ms31=1.20, lic_g=0.02, anniv2_p=0.3),
    'base': dict(
        name='基准', p=0.50,
        h2_innov_g=0.12, h2_gen_g=-0.14, h2_cogs=0.141, h2_sell=46.5, h2_ga=15.0, h2_rd=49.5,
        g_innov=[0.19, 0.16, 0.13, 0.11, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03],
        g_gen=[-0.10, -0.07, -0.05, -0.04, -0.03, -0.02, -0.02, -0.02, -0.02, -0.02],
        r2031=dict(cogs=0.140, sell=0.270, ga=0.082, rd=0.265), r2036=dict(cogs=0.140, sell=0.255, ga=0.075, rd=0.230),
        upf=2.50, ms0=0.80, ms31=2.50, lic_g=0.03, anniv2_p=0.6),
    'bull': dict(
        name='牛', p=0.25,
        h2_innov_g=0.184, h2_gen_g=-0.12, h2_cogs=0.139, h2_sell=46.5, h2_ga=15.0, h2_rd=49.5,
        g_innov=[0.25, 0.25, 0.18, 0.14, 0.11, 0.09, 0.07, 0.06, 0.05, 0.04],
        g_gen=[-0.08, -0.06, -0.04, -0.03, -0.02, -0.02, -0.02, -0.02, -0.02, -0.02],
        r2031=dict(cogs=0.134, sell=0.255, ga=0.076, rd=0.245), r2036=dict(cogs=0.130, sell=0.240, ga=0.070, rd=0.210),
        upf=4.50, ms0=1.50, ms31=4.50, lic_g=0.05, anniv2_p=0.9),
}
# 授权现金（亿美元/年，税前）：upf = 新交易首付款；ms = 已签与新签交易的里程碑、选择权费与提成，2027→2031 线性爬升，其后按 lic_g 增长。


def year2026(s):
    h2_innov = H2_INNOV_25 * (1 + s['h2_innov_g'])
    h2_gen = H2_GEN_25 * (1 + s['h2_gen_g'])
    h2_rev = h2_innov + h2_gen + 0.9
    h2_ebit = h2_rev - h2_rev * s['h2_cogs'] - 1.5 - s['h2_sell'] - s['h2_ga'] - s['h2_rd'] - 0.95
    innov, gen = H1_INNOV + h2_innov, H1_GEN + h2_gen
    S = innov + gen
    ratios = dict(cogs=(19.60 + h2_rev * s['h2_cogs']) / S, sell=(43.409 + s['h2_sell']) / S,
                  ga=(12.575 + s['h2_ga']) / S, rd=(46.051 + s['h2_rd']) / S)
    return dict(innov=innov, gen=gen, S=S, ebit=H1_EBIT + h2_ebit, h2_ebit=h2_ebit, ratios=ratios,
                rd=46.051 + s['h2_rd'])


def lic_path(s):
    out = []
    for i, y in enumerate(YEARS):
        if y <= 2031:
            ms, upf = s['ms0'] + (s['ms31'] - s['ms0']) * i / 4, s['upf']
        else:
            k = y - 2031
            ms, upf = s['ms31'] * (1 + s['lic_g']) ** k, s['upf'] * (1 + s['lic_g']) ** k
        out.append((upf + ms) * USD_CNY)
    return out


def interp(a, b, i, n):
    return a + (b - a) * i / n


def project(s, override=None):
    s = dict(s)
    if override:
        s.update(override)
    y26 = year2026(s)
    r26 = y26['ratios']
    innov, gen, S_prev = y26['innov'], y26['gen'], y26['S']
    lic = lic_path(s)
    rows = []
    for i, y in enumerate(YEARS):
        innov *= 1 + s['g_innov'][i]
        gen *= 1 + s['g_gen'][i]
        S = innov + gen
        if y <= 2031:
            rr = {k: interp(r26[k], s['r2031'][k], i + 1, 5) for k in r26}
        else:
            rr = {k: interp(s['r2031'][k], s['r2036'][k], y - 2031, 5) for k in r26}
        ebit = S * (1 - rr['cogs'] - rr['sell'] - rr['ga'] - rr['rd'] - 0.010) + OTHER_2026 * 1.02 ** (i + 1)
        nopat = ebit * (1 - T_CORE) + lic[i] * (1 - T_LIC)
        reinv = CAPEX_FIX + (CAPEX_RATE + NWC_RATE) * (S - S_prev)
        rows.append(dict(y=y, innov=innov, gen=gen, S=S, rd=S * rr['rd'], margin=ebit / S, ebit=ebit,
                         lic=lic[i], nopat=nopat, reinv=reinv, oe=nopat - reinv))
        S_prev = S
    return s, y26, rows


def equity_value(s0, r, override=None):
    s, y26, rows = project(s0, override)
    pv = sum(row['oe'] / (1 + r) ** (row['y'] + 0.5 - VAL_T) for row in rows)
    last = rows[-1]
    oe_tv = last['nopat'] * (1 + TG) - (CAPEX_FIX + (CAPEX_RATE + NWC_RATE) * TG * last['S'])
    pv_tv = oe_tv / (r - TG) / (1 + r) ** (last['y'] + 0.5 - VAL_T)
    stub = y26['h2_ebit'] * (1 - T_CORE) - 3.0                       # 2026 下半年核心经营所有者收益
    anniv = BMS_ANNIV1 / (1 + r) ** (2027.5 - VAL_T) + s['anniv2_p'] * BMS_ANNIV2 / (1 + r) ** (2028.5 - VAL_T)
    fixed = NET_CASH_ADJ + NON_OP - MINORITY + POST_ITEMS + stub + anniv
    total = pv + pv_tv + fixed
    return dict(total=total, ps=total / SHARES, pv=pv, pv_tv=pv_tv, fixed=fixed, stub=stub, anniv=anniv,
                tv_share=pv_tv / (pv + pv_tv), y26=y26, rows=rows)


NORM_INTEREST = 0.024 * 420 * (1 - T_LIC)   # 正常化利息：约 420 亿元可用现金 × 2.4%，税后


def norm_np_2026(s):
    """2026 正常化归母净利（研发全额费用化口径）：核心经营 + 可持续授权（取 2027 年水平）+ 正常化利息；少数股东约 0。"""
    y26 = year2026(s)
    return y26['ebit'] * (1 - T_CORE) + lic_path(s)[0] * (1 - T_LIC) + NORM_INTEREST


CAP_NET_2026 = (22.6 - 1.6) * (1 - T_CORE)   # 报表口径加回：2026E 资本化研发约 22.6 − 已资本化项目摊销约 1.6，税后


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


def weighted(r, weights=None):
    w = weights or {k: SCEN[k]['p'] for k in SCEN}
    return sum(w[k] * equity_value(SCEN[k], r)['ps'] for k in SCEN)


def main():
    out = {}
    mcap_a = PRICE_A * SHARES
    price_h_cny = PRICE_H_HKD * HKD_CNY
    mcap_ah = PRICE_A * SH_A + price_h_cny * SH_H
    print('== 股本与市值 ==')
    print('A 股价×总股本 %.1f 亿元；A、H 分别计价 %.1f 亿元（H 股 %.2f 港元 ≈ %.2f 元，较 A 股折价 %.1f%%）'
          % (mcap_a, mcap_ah, PRICE_H_HKD, price_h_cny, (1 - price_h_cny / PRICE_A) * 100))
    print('\n== 净现金、非经营资产与期后现金 ==')
    print('经调整净现金 %.2f（美元存款按 10 月中间价重估 %.2f）' % (NET_CASH_ADJ, FX_REVAL))
    print('非经营资产 %.2f（Kailera 市值 %.2f、扣浮盈税后 %.2f；其他非流动金融资产 %.2f；联营七折 %.2f）；少数股东权益 %.2f'
          % (NON_OP, KLRA_VAL, KLRA_NET, OTHER_FIN, LTEI, MINORITY))
    print('期后现金（税后）%.2f：BMS 首付 %.2f、诺和首付 %.2f、7-10 月利息 %.2f、回购 %.2f、员工持股认购 %.2f'
          % (POST_ITEMS, BMS_UPFRONT, NOVO_UPFRONT, H2_INTEREST, BUYBACK_SEP_OCT, ESOP_INFLOW))
    print('2026 上半年核心经营利润（研发费用化）%.2f' % H1_EBIT)

    res = {}
    for k, s in SCEN.items():
        d9, d8, d10 = equity_value(s, COE), equity_value(s, 0.08), equity_value(s, 0.10)
        res[k] = dict(v9=d9['ps'], v8=d8['ps'], v10=d10['ps'], d=d9)
        y26 = d9['y26']
        print('\n== %s情景（概率 %.2f）==' % (s['name'], s['p']))
        print('2026E 创新药 %.1f（%+.1f%%）、仿制药 %.1f、产品收入 %.1f；研发总投入 %.1f；核心经营利润（费用化）%.1f（下半年 %.1f）'
              % (y26['innov'], (y26['innov'] / INNOV_25 - 1) * 100, y26['gen'], y26['S'], y26['rd'], y26['ebit'], y26['h2_ebit']))
        print('   2026 费用率（占产品收入）：成本 %.1f%%、销售 %.1f%%、管理 %.1f%%、研发总投入 %.1f%%'
              % tuple(y26['ratios'][x] * 100 for x in ('cogs', 'sell', 'ga', 'rd')))
        print('   2026 正常化归母净利：费用化口径 %.1f；报表（资本化）口径约 %.1f' % (norm_np_2026(s), norm_np_2026(s) + CAP_NET_2026))
        oe26_s = y26['ebit'] * (1 - T_CORE) + lic_path(s)[0] * (1 - T_LIC) - (CAPEX_FIX + 0.29 * 0.10 * y26['S'])
        print('   2026 正常化所有者收益（可持续授权、按 10%% 收入增长的正常再投资）%.1f；费用化核心利润率 %.1f%%'
              % (oe26_s, y26['ebit'] / y26['S'] * 100))
        prev = None
        for row in d9['rows']:
            g = '' if prev is None else '  OE %+.1f%%' % ((row['oe'] / prev - 1) * 100)
            print('   %d 创新药 %6.1f 仿制药 %5.1f 产品 %6.1f 研发 %5.1f 核心利润率 %5.1f%% 授权 %5.1f NOPAT %6.1f 再投资 %4.1f OE %6.1f%s'
                  % (row['y'], row['innov'], row['gen'], row['S'], row['rd'], row['margin'] * 100, row['lic'],
                     row['nopat'], row['reinv'], row['oe'], g))
            prev = row['oe']
        print('   V(9%%) %.2f  V(8%%) %.2f  V(10%%) %.2f | 显性期 %.0f 终值 %.0f（终值占经营价值 %.0f%%）固定项 %.0f（下半年 %.1f、BMS 周年款 %.1f）'
              % (d9['ps'], d8['ps'], d10['ps'], d9['pv'], d9['pv_tv'], d9['tv_share'] * 100, d9['fixed'], d9['stub'], d9['anniv']))

    vw, vw8, vw10 = weighted(COE), weighted(0.08), weighted(0.10)
    print('\n== 加权 ==')
    print('加权 V %.2f，P/V %.3f；8%% 加权 V %.2f（P/V %.2f）；10%% 加权 V %.2f（P/V %.2f）'
          % (vw, PRICE_A / vw, vw8, PRICE_A / vw8, vw10, PRICE_A / vw10))
    v_ex = (vw * SHARES - ESOP_INFLOW) / (SHARES - TREASURY)
    print('剔除回购专户 %.3f 亿股（同时剔除其员工持股认购款）后 V %.2f，P/V %.3f' % (TREASURY, v_ex, PRICE_A / v_ex))
    print('V 不变时进入各档的价格：≤ %.2f 明显低估；%.2f～%.2f 温和低估；%.2f～%.2f 大致合理；> %.2f 偏贵'
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    base = SCEN['base']
    irr = solve(lambda r: equity_value(base, r)['ps'], 0.03, 0.20, PRICE_A)
    irr_w = solve(lambda r: weighted(r), 0.03, 0.20, PRICE_A)
    print('现价隐含回报：基准情景 %.2f%%；三情景加权 %.2f%%' % (irr * 100, irr_w * 100))

    y26 = year2026(base)
    oe26 = y26['ebit'] * (1 - T_CORE) + lic_path(base)[0] * (1 - T_LIC) - (CAPEX_FIX + 0.29 * 0.10 * y26['S'])
    fixed_b = equity_value(base, COE)['fixed']

    def v_of_g(g):
        pv, oe = 0.0, oe26
        for n in range(1, 11):
            oe *= 1 + g
            pv += oe / (1 + COE) ** (2026 + n + 0.5 - VAL_T)
        return (pv + oe * (1 + TG) / (COE - TG) / (1 + COE) ** (2036.5 - VAL_T) + fixed_b) / SHARES

    g_impl = solve(v_of_g, -0.2, 0.6, PRICE_A)
    oe27 = equity_value(base, COE)['rows'][0]['oe']
    g_perp = solve(lambda g: (oe27 / (COE - g) / (1 + COE) ** (2027.5 - VAL_T) + fixed_b) / SHARES, -0.05, 0.0899, PRICE_A)
    print('反向 DCF：以 2026 正常化所有者收益 %.1f 亿元起，现价隐含 2027-2036 年均增长 %.1f%%（其后 2.5%%）；'
          '以 2027 年基准所有者收益 %.1f 亿元计隐含永续增长 %.2f%%' % (oe26, g_impl * 100, oe27, g_perp * 100))

    rows = res['base']['d']['rows']
    gr = [rows[0]['oe'] / oe26 - 1] + [rows[i]['oe'] / rows[i - 1]['oe'] - 1 for i in range(1, 5)]
    reinv5 = sum(r['reinv'] for r in rows[:5])
    nopat5 = sum(r['nopat'] for r in rows[:5])
    nopat26 = y26['ebit'] * (1 - T_CORE) + lic_path(base)[0] * (1 - T_LIC)
    d_nopat = rows[4]['nopat'] - nopat26
    growth_rd = sum((r['rd'] - 0.20 * r['S']) * (1 - T_CORE) for r in rows[:5])
    econ_rr = (reinv5 + growth_rd) / (nopat5 + growth_rd)
    econ_roi = d_nopat / (reinv5 + growth_rd)
    print('基准所有者收益增速 2027-2031：' + '、'.join('%.1f%%' % (x * 100) for x in gr))
    print('有形再投资率 %.1f%%，有形增量回报 %.0f%%；计入超出 20%% 维持水平的增长性研发（税后 %.0f 亿元）后经济再投资率 %.0f%%、增量回报 %.0f%%'
          % (reinv5 / nopat5 * 100, d_nopat / reinv5 * 100, growth_rd, econ_rr * 100, econ_roi * 100))

    print('\n== 证伪触发后的 V（9%）==')
    bear = SCEN['bear']
    f1 = equity_value(base, COE, dict(h2_innov_g=bear['h2_innov_g'], g_innov=bear['g_innov'],
                                      h2_gen_g=bear['h2_gen_g'], g_gen=bear['g_gen']))['ps']
    f2 = equity_value(base, COE, dict(upf=bear['upf'], ms0=bear['ms0'], ms31=bear['ms31'],
                                      lic_g=bear['lic_g'], anniv2_p=0.3))['ps']
    f3 = equity_value(base, COE, dict(r2031=bear['r2031'], r2036=bear['r2036']))['ps']
    f4 = res['bull']['v9']
    f5 = weighted(COE, dict(bear=0.45, base=0.45, bull=0.10))
    print('F1 创新药按熊情景增长（授权、费用率仍按基准）%.2f' % f1)
    print('F2 授权按熊情景（产品按基准）%.2f' % f2)
    print('F3 费用率按熊情景（增长按基准）%.2f' % f3)
    print('F4 员工持股考核目标兑现（牛情景）%.2f' % f4)
    print('F5 前三季度创新药增速 <10%%，权重改为 45/45/10：%.2f' % f5)

    print('\n== 驱动因素敏感性（9%）==')
    bull = SCEN['bull']
    lic_keys = ('upf', 'ms0', 'ms31', 'lic_g', 'anniv2_p')
    prod_keys = ('h2_innov_g', 'h2_gen_g', 'g_innov', 'g_gen', 'h2_cogs', 'r2031', 'r2036')
    s_a = equity_value(base, COE, dict((k, bull[k]) for k in lic_keys))['ps']
    s_b = equity_value(base, COE, dict((k, bull[k]) for k in prod_keys))['ps']
    s_c = equity_value(base, COE, dict(r2036=dict(base['r2036'], rd=0.20)))['ps']
    print('基准产品 + 牛情景授权 %.2f；牛情景产品 + 基准授权 %.2f；基准但 2036 年研发率 20%%（原 23%%）%.2f' % (s_a, s_b, s_c))

    print('\n== 交叉验证 ==')
    ev = mcap_a - NET_CASH_ADJ - POST_ITEMS - NON_OP + MINORITY
    ebit25_rep = 28.72 + (17.627 - 0.867) + 33.924
    ebit26_fx = y26['ebit'] + lic_path(base)[0]
    print('EV（A 股价口径）%.0f 亿元；EV/2025 报表口径经营利润（含许可收入 33.92）%.0f = %.1f×；EV/2026 基准费用化经营利润+可持续授权 %.1f = %.1f×'
          % (ev, ebit25_rep, ev / ebit25_rep, ebit26_fx, ev / ebit26_fx))
    print('市值/2026 基准正常化归母：费用化口径 %.1f×，报表口径 %.1f×；股息率 %.2f%%'
          % (mcap_a / norm_np_2026(base), mcap_a / (norm_np_2026(base) + CAP_NET_2026), 0.20 / PRICE_A * 100))

    out = dict(v_bear=round(res['bear']['v9'], 2), v_base=round(res['base']['v9'], 2), v_bull=round(res['bull']['v9'], 2),
               v_weighted=round(vw, 2), pv=round(PRICE_A / vw, 3), v_at_coe_8=round(vw8, 2), v_at_coe_10=round(vw10, 2),
               implied_irr=round(irr, 4), implied_irr_weighted=round(irr_w, 4), v_ex_treasury=round(v_ex, 2),
               norm_np_2026=dict((k, round(norm_np_2026(SCEN[k]), 1)) for k in SCEN),
               norm_np_2026_reported_basis=dict((k, round(norm_np_2026(SCEN[k]) + CAP_NET_2026, 1)) for k in SCEN),
               net_cash_adj=round(NET_CASH_ADJ, 1), non_operating_assets=round(NON_OP, 1), post_items=round(POST_ITEMS, 1),
               growth_2027_2031=[round(x, 3) for x in gr], econ_reinvestment_rate=round(econ_rr, 2),
               econ_incremental_return=round(econ_roi, 2), implied_g10=round(g_impl, 3), implied_g_perp=round(g_perp, 4),
               falsifiers=dict(F1=round(f1, 2), F2=round(f2, 2), F3=round(f3, 2), F4=round(f4, 2), F5=round(f5, 2)),
               mcap_a=round(mcap_a, 1), mcap_ah=round(mcap_ah, 1))
    print('\n== 摘要 ==')
    print(json.dumps(out, ensure_ascii=False))
    return out


if __name__ == '__main__':
    main()
