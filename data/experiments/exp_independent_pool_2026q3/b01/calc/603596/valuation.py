#!/usr/bin/env python3
"""伯特利（603596）OI-291 独立估值：归母所有者收益 DCF（熊/基准/牛）、反向 DCF、隐含回报与交叉验证。

运行：python3 valuation.py
金额单位亿元；每股价值为元/股，按 2026 中报 10 转 4.2 实施前的股本（8.9764 亿股）计，
转增实施后每股数字除以 1.42。输入出处见 companies/603596_伯特利.md「来源」一节。
"""
from datetime import date

# ---------------------------------------------------------------- 市场、股本与转债
PRICE = 26.40                 # 2026-10-19 收盘（brief.md）
T0 = date(2026, 10, 19)
SHARES = 8.97641828           # 亿股，腾讯行情 897,641,828 股（含回购专户 371.17 万股）
TRANSFER_RATIO = 1.42         # 2026 中报每 10 股转增 4.2 股：2026-09-15 股东会通过，未实施
CB_FACE = 28.018              # 伯25转债未转股面值：28.02 亿发行，截至 6/30 转股面值 20.1 万元（2026H1 第 181 页）
CB_CONV = 35.16               # 当前转股价（dividend_20260430_757565 第 1、3 页）
CB_SHARES = CB_FACE / CB_CONV  # 全部转股新增股数（亿股）
COE = 0.09

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，2026H1 第 48-50、135、153、174-183 页）
CASH = 31.712                 # 货币资金
BILL_MARGIN = 5.352           # 票据保证金：对应应付票据 31.28，归入营运资本
GUARANTEE_MARGIN = 0.421      # 保函保证金
FROZEN = 0.006                # 涉诉冻结
TRADING_FA = 22.891           # 交易性金融资产（银行理财/基金 18.36、收益凭证 2.02、结构性存款 2.52）
CD_CURRENT = 3.947            # 其他流动资产中的大额存单
CD_NONCURRENT = 3.257         # 债权投资（大额存单）
LIQUID = CASH - BILL_MARGIN - GUARANTEE_MARGIN - FROZEN + TRADING_FA + CD_CURRENT + CD_NONCURRENT

DEBT_EX_CB = (4.069           # 短期借款
              + 2.022         # 一年内到期非流动负债（长期借款 1.50、其他非流动负债 0.46、租赁 0.06）
              + 8.596         # 长期借款
              + 0.110         # 租赁负债
              + 0.723         # 其他非流动负债（产线扶持、借转补资金，按类债务）
              + 0.600)        # 其他应付款中的借款
BUYBACK_Q3 = 1.001            # 7-9 月回购付现（buyback_20261009_210099 第 1 页）
OP_RESERVE = 5.0              # 经营备付，约 2026E 年化收入的 3%
MINORITY_YUBEI_CASH = 0.7     # 豫北转向 49% 少数股东应占其自由净现金（估计，见正文 2.4）
NET_CASH_ADJ = LIQUID - DEBT_EX_CB - CB_FACE - BUYBACK_Q3 - OP_RESERVE - MINORITY_YUBEI_CASH
NON_OP = 2.526 * 0.7 + 0.856  # 其他非流动金融资产按 70%、其他权益工具投资按账面

# ---------------------------------------------------------------- 2026 正常化归母净利（含净利息，剔除一次性）
TAX = 0.15
H1_KF = 5.8009                # 2026H1 扣非归母（2026H1 第 6 页）
H1_FX = (75.617 - 55.407) / 100 * (1 - TAX)   # 2026H1 汇兑净损失 0.202 亿，税后加回（第 195 页）
H1_FIN = 0.4215 * (1 - TAX)   # 理财、存单收益（非经常性 65.91m 扣除其他权益工具股利 23.76m，第 7、195-196 页）
H2_2025_KF = 3.5056 + 3.6072  # 2025Q3+Q4 扣非（2025 年报第 9 页）
H2_2025_FX = (86.674 - 71.086 + 4.142) / 100 * (1 - TAX)  # 2025 全年汇兑净损失 15.59m 加上半年净收益 4.14m = 下半年净损失 0.197 亿
H2_BASE = H2_2025_KF + H2_2025_FX   # 剔除汇兑的 2025 下半年扣非基数（2025 年报第 197 页；2025H1 汇兑见 2026H1 第 195 页上期数）
YUBEI_ONEOFF = 0.10           # 豫北存货评估增值 25.08m 转销的税后归母部分，一次性加回（第 209 页）
ACQ_FIN_H2 = 0.12             # 新增借款约 9-12 亿（借款由年初 0.8 亿增至 14.2 亿，含豫北并入约 4 亿）、利率约 2.4% 的下半年税后利息，取高值


def np_2026(h2_org_growth, yubei_h2):
    """2026 正常化归母净利 = 上半年扣非 + 汇兑加回 + 上半年理财收益 + 下半年内生扣非（剔除汇兑的基数 × 增速）
    + 豫北下半年归母 − 收购利息 + 下半年理财收益 + 一次性加回。"""
    return (H1_KF + H1_FX + H1_FIN + H2_BASE * (1 + h2_org_growth) + yubei_h2
            - ACQ_FIN_H2 + H1_FIN + YUBEI_ONEOFF)


H1_NORM = H1_KF + H1_FX + H1_FIN + YUBEI_ONEOFF   # 上半年正常化部分（其现金已在 6/30 资产负债表内）

SCENARIOS = {
    # growth：2027-2036 归母净利增速；annualize：2027 年豫北全年并表带来的增速（不需再投资）
    'bear': dict(p=0.25, h2=-0.05, yubei=0.26, annualize=0.015,
                 growth=[-0.02, 0.03, 0.03, 0.03, 0.03, 0.025, 0.025, 0.02, 0.02, 0.02],
                 ronic=0.10, g_t=0.02, ronic_t=0.09,
                 text='国内价格战与年降加深、奇瑞内销继续下滑、墨西哥受关税拖累：下半年内生扣非 -5%，'
                      '2027 归母 -2%（内生 -3.5%），此后 3% 并降至 2%；增量回报 10%，终值回报 9%'),
    'base': dict(p=0.50, h2=0.08, yubei=0.34, annualize=0.015,
                 growth=[0.105, 0.09, 0.08, 0.07, 0.065, 0.055, 0.045, 0.035, 0.03, 0.025],
                 ronic=0.15, g_t=0.025, ronic_t=0.12,
                 text='下半年内生扣非 +8%（内销 -25%、出口 +67%、奇瑞 +4%，管理层称“平稳增长”），'
                      '2027 归母 +10.5%（含豫北全年并表 1.5 个百分点），2028-2031 为 9/8/7/6.5%，'
                      '之后五年降到 2.5%；增量回报 15%，终值回报 12%'),
    'bull': dict(p=0.25, h2=0.18, yubei=0.40, annualize=0.015,
                 growth=[0.19, 0.17, 0.15, 0.13, 0.11, 0.09, 0.07, 0.05, 0.04, 0.03],
                 ronic=0.18, g_t=0.025, ronic_t=0.15,
                 text='EMB 放量、线控制动份额从 8.6% 继续提升、欧洲与北美定点落地、转向协同兑现：'
                      '下半年内生扣非 +18%，2027-2031 归母 19/17/15/13/11%；增量回报 18%，终值回报 15%'),
}


def yrs(y):
    return (date(y, 12, 31) - T0).days / 365.25


def dcf(s, r, np26=None):
    """返回 (经营价值, 终值现值, 逐年归母净利, 逐年所有者收益)。现金流按年末计，2026 只计下半年。"""
    n26 = np_2026(s['h2'], s['yubei']) if np26 is None else np26
    growth = s['growth']
    org = [growth[0] - s['annualize']] + list(growth[1:])     # 内生增速（决定再投资）
    nps = [n26]
    for g in growth:
        nps.append(nps[-1] * (1 + g))
    flows = []
    oe_h2 = (n26 - H1_NORM) - 0.5 * n26 * max(org[0], 0.0) / s['ronic']
    flows.append((yrs(2026), oe_h2))
    for k in range(1, len(nps)):
        if k < len(org):
            g_next, rr = org[k], s['ronic']
        else:
            g_next, rr = s['g_t'], s['ronic_t']
        flows.append((yrs(2026 + k), nps[k] * (1 - max(g_next, 0.0) / rr)))
    tv = nps[-1] * (1 + s['g_t']) * (1 - s['g_t'] / s['ronic_t']) / (r - s['g_t'])
    pv = sum(cf / (1 + r) ** t for t, cf in flows)
    pv_tv = tv / (1 + r) ** flows[-1][0]
    return pv, pv_tv, nps, flows


def per_share(ops_value, conv=CB_CONV):
    """不摊薄：转债按面值作债务；完全摊薄：转债全部转股、加回面值。按持有人选择取对股东不利者。"""
    eq = ops_value + NET_CASH_ADJ + NON_OP
    v_basic = eq / SHARES
    v_dil = (eq + CB_FACE) / (SHARES + CB_FACE / conv)
    return min(v_basic, v_dil), v_basic, v_dil


def scenario_values(r=COE, conv=CB_CONV):
    out = {}
    for k, s in SCENARIOS.items():
        pv, pv_tv, nps, flows = dcf(s, r)
        v, vb, vd = per_share(pv + pv_tv, conv)
        out[k] = dict(v=v, v_basic=vb, v_dil=vd, pv=pv, pv_tv=pv_tv, nps=nps, flows=flows,
                      tv_share=pv_tv / (pv + pv_tv))
    return out


def weighted(vals):
    return sum(SCENARIOS[k]['p'] * vals[k]['v'] for k in SCENARIOS)


def band(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def solve(f, lo, hi, target, it=200):
    """二分求解 f(x) = target（f 单调）。"""
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(key='base'):
    s = SCENARIOS[key]
    return solve(lambda r: per_share(sum(dcf(s, r)[:2]))[0], 0.04, 0.20, PRICE)


def reverse_dcf_growth():
    """基准结构（增量回报 15%、终值 2.5%/12%）下，2027-2036 统一增速 g 使 V = 现价。"""
    base = SCENARIOS['base']
    n26 = np_2026(base['h2'], base['yubei'])

    def v_of(g):
        s = dict(base, growth=[g] * 10, annualize=0.0)
        return per_share(sum(dcf(s, COE, n26)[:2]))[0]
    return solve(v_of, -0.05, 0.25, PRICE)


def reverse_perpetual_growth():
    """单阶段：现价经营价值 = NP26 ×(1+g)×(1−g/15%)/(9%−g)，求 g。"""
    base = SCENARIOS['base']
    n26 = np_2026(base['h2'], base['yubei'])
    ops = PRICE * SHARES - NET_CASH_ADJ - NON_OP
    return solve(lambda g: n26 * (1 + g) * (1 - g / 0.15) / (COE - g), -0.05, 0.085, ops)


def cross_checks():
    base = SCENARIOS['base']
    n26 = np_2026(base['h2'], base['yubei'])
    mcap = PRICE * SHARES
    minority_book = 13.276                           # 2026-06-30 少数股东权益（第 50 页）
    debt_all = DEBT_EX_CB + CB_FACE
    ev = mcap + debt_all - LIQUID + minority_book - NON_OP
    ebit_26 = (n26 + 0.45) / (1 - 0.13)             # 归母 + 少数股东约 0.45，有效税率约 13%，净利息约为零
    return dict(mcap=mcap, pe_ttm=mcap / 14.29, pe_26=mcap / n26, pb=mcap / 84.23,
                ev=ev, ev_ebit=ev / ebit_26, div_yield=0.38 / PRICE,
                shareholder_yield=(0.38 * SHARES + 1.5) / mcap)


def h_share_dilution(v, frac, issue_price):
    """以 issue_price 增发占原股本 frac 的 H 股后每股价值。"""
    return (v + frac * issue_price) / (1 + frac)


def base_sensitivity(ronic=None, shift=0.0):
    """基准情景：改增量回报，或把 2027-2031 增速整体平移 shift。"""
    s = dict(SCENARIOS['base'])
    if ronic is not None:
        s['ronic'] = ronic
    s['growth'] = [g + (shift if i < 5 else 0.0) for i, g in enumerate(s['growth'])]
    return per_share(sum(dcf(s, COE)[:2]))[0]


FALSIFIERS = [
    # (编号, 条件, 期限, 触发后的情景权重 熊/基准/牛)
    ('F1', '2026 三季报：单季扣非归母 < 3.45 亿（不高于 2025Q3，豫北整季并表后仍零增长）或单季毛利率 < 17.5%',
     '2026-10-30', (0.45, 0.45, 0.10)),
    ('F2', '2026 年报：扣非归母 < 13.0 亿（基准约 13.9 亿），或经营现金流/归母净利 < 0.6',
     '2027-04-30', (0.60, 0.35, 0.05)),
    ('F3', '2027 中报：剔除豫北的内生营收同比 < 3% 且扣非归母同比为负',
     '2027-08-31', (1.00, 0.00, 0.00)),
    ('F4', '2026 年报：奇瑞系关联销售占比 < 30% 且金额同比降 > 10%，或奇瑞科技再减持 ≥ 3%',
     '2027-04-30', (0.40, 0.50, 0.10)),
    ('F5', '上行证伪：2027 中报扣非归母同比 ≥ +20% 且毛利率 ≥ 20%',
     '2027-08-31', (0.15, 0.45, 0.40)),
]


def falsifier_values(vals=None):
    vals = scenario_values() if vals is None else vals
    out = []
    for code, cond, deadline, w in FALSIFIERS:
        v = w[0] * vals['bear']['v'] + w[1] * vals['base']['v'] + w[2] * vals['bull']['v']
        out.append((code, cond, deadline, v))
    return out


def q3_2026_expectation():
    """三季报核对基准：内生收入 +9%、内生扣非 +8%，豫北整季收入约 8.3 亿、归母约 0.17 亿，收购利息约 0.06 亿。"""
    rev = 31.935 * 1.09 + 8.3
    kf = 3.5056 * 1.08 + 0.17 - 0.06
    return rev, kf


if __name__ == '__main__':
    print('伯特利 603596 独立估值（价格日 2026-10-19，现价 %.2f 元，总股本 %.4f 亿股）' % (PRICE, SHARES))
    print('经调整净现金 %.2f 亿（流动资产 %.2f − 有息负债 %.2f − 转债面值 %.2f − 回购 %.2f − 备付 %.1f − 豫北少数 %.1f）；非经营资产 %.2f 亿'
          % (NET_CASH_ADJ, LIQUID, DEBT_EX_CB, CB_FACE, BUYBACK_Q3, OP_RESERVE, MINORITY_YUBEI_CASH, NON_OP))
    print('转债：面值 %.3f 亿，转股价 %.2f，全部转股新增 %.4f 亿股（%.1f%%）' % (CB_FACE, CB_CONV, CB_SHARES, CB_SHARES / SHARES * 100))
    print()
    print('2026 正常化归母净利（亿元）：' + '，'.join('%s %.2f' % (k, np_2026(s['h2'], s['yubei'])) for k, s in SCENARIOS.items()))
    vals = scenario_values()
    for k, x in vals.items():
        s = SCENARIOS[k]
        print('%-4s p=%.2f  V=%.2f（不摊薄 %.2f／完全摊薄 %.2f） 经营价值 %.1f 亿（显性 %.1f + 终值 %.1f，终值占 %.0f%%） 2031 归母 %.2f 亿'
              % (k, s['p'], x['v'], x['v_basic'], x['v_dil'], x['pv'] + x['pv_tv'], x['pv'], x['pv_tv'],
                 x['tv_share'] * 100, x['nps'][5]))
    vw = weighted(vals)
    print('加权 V = %.2f 元/股，P/V = %.3f（%s）' % (vw, PRICE / vw, band(PRICE / vw)))
    vw_basic = sum(SCENARIOS[k]['p'] * vals[k]['v_basic'] for k in SCENARIOS)
    vw_dil = sum(SCENARIOS[k]['p'] * vals[k]['v_dil'] for k in SCENARIOS)
    print('口径核对：全按不摊薄 %.2f，全按完全摊薄 %.2f；选定口径为逐情景取低（V 低于转股价按债务，高于转股价按转股）' % (vw_basic, vw_dil))
    print('转增 10 转 4.2 实施后：加权 V %.2f 元/股，现价对应 %.2f 元，转股价 %.2f 元' % (vw / TRANSFER_RATIO, PRICE / TRANSFER_RATIO, CB_CONV / TRANSFER_RATIO))
    print()
    for r in (0.08, 0.10):
        vr = scenario_values(r)
        print('股权成本 %.0f%%：熊 %.2f／基准 %.2f／牛 %.2f，加权 V %.2f，P/V %.3f'
              % (r * 100, vr['bear']['v'], vr['base']['v'], vr['bull']['v'], weighted(vr), PRICE / weighted(vr)))
    print('现价隐含回报（基准现金流）：%.2f%%' % (implied_irr() * 100))
    print('反向 DCF：2027-2036 归母所有者收益统一增速 %.2f%%（增量回报 15%%，终值 2.5%%）；单阶段永续增速 %.2f%%'
          % (reverse_dcf_growth() * 100, reverse_perpetual_growth() * 100))
    print()
    b = vals['base']
    print('基准逐年（亿元）：')
    for (t, oe), y, n in zip(b['flows'], range(2026, 2037), b['nps']):
        print('  %d 归母 %.2f  所有者收益 %.2f%s' % (y, n, oe, '（仅下半年）' if y == 2026 else ''))
    cc = cross_checks()
    print()
    print('交叉验证：市值 %.1f 亿，PE(TTM) %.1f，PE(2026 基准) %.1f，PB %.2f，EV %.1f 亿，EV/EBIT(2026) %.1f，股息率 %.2f%%，股息+回购 %.2f%%'
          % (cc['mcap'], cc['pe_ttm'], cc['pe_26'], cc['pb'], cc['ev'], cc['ev_ebit'], cc['div_yield'] * 100, cc['shareholder_yield'] * 100))
    vd = scenario_values(conv=26.40)
    print('若 2026-12-30 后转股价下修至 26.40：熊 %.2f／基准 %.2f／牛 %.2f，加权 %.2f' % (vd['bear']['v'], vd['base']['v'], vd['bull']['v'], weighted(vd)))
    print('若按 22.4 元（较现价折让约 15%%）增发原股本 10%%／20%% 的 H 股：加权 V %.2f／%.2f'
          % (h_share_dilution(vw, 0.10, 22.4), h_share_dilution(vw, 0.20, 22.4)))
    print('基准敏感性：增量回报 13%%／17%% 时 V %.2f／%.2f；2027-2031 增速 −2／+2 个百分点时 V %.2f／%.2f'
          % (base_sensitivity(ronic=0.13), base_sensitivity(ronic=0.17), base_sensitivity(shift=-0.02), base_sensitivity(shift=0.02)))
    q3r, q3k = q3_2026_expectation()
    print('2026Q3 基准核对值：营收约 %.1f 亿，扣非归母约 %.2f 亿（2025Q3 为 31.94 亿、3.51 亿）' % (q3r, q3k))
    print('V 不变时各档价格：≤%.2f 明显低估；%.2f–%.2f 温和低估；%.2f–%.2f 大致合理；>%.2f 偏贵'
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    print()
    print('证伪条件触发后的独立 V：')
    for code, cond, deadline, v in falsifier_values(vals):
        print('  %s（%s）%s → V %.2f，P/V %.2f' % (code, deadline, cond, v, PRICE / v))
