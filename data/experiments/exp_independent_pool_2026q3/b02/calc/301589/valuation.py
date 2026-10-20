#!/usr/bin/env python3
"""诺瓦星云（301589）独立估值（OI-291 b02，价格日 2026-10-19；2026-10-20 按有杠杆口径重算）。

方法：归母所有者收益 DCF（股权成本 9%，敏感性 8%／10%）+ 反向 DCF + 交叉验证。
金额单位亿元，每股单位元。运行：python3 valuation.py

口径
- 每股：总股本 0.92448 亿股（brief 口径，含回购专户 355.81 万股，未公告注销）；另报剔除专户的
  0.88890 亿股口径作对照。
- 先算 2026-12-31 的价值，再按 73 天折回 2026-10-19；年度现金流按年中折现。
- 经营所有者收益 OE = 经营归母净利（正常化归母净利加回税后净利息）− 增量收入 × 增量资本强度 k
  − 深圳科技园剩余投资；维护性资本开支≈折旧摊销（2025 年折旧摊销 0.91 亿，购建长期资产 0.97 亿）。
  科技园建成前后（2027–2032）k 中的固定资产部分（0.17）由科技园替代，不重复计提。
- 两种口径（framework.md「三法互校」第 2 条；经调整净现金 −0.96 亿 < 0，登记取有杠杆口径）：
  有杠杆：有息负债 8.113 亿（含租赁）按现规模滚动、不还本，股权价值 = 经营 OE 现值
          − 税后利息现值（利率取近 12 个月实际平均利率，税率 15%，与经营 OE 同率折现）+ 现金与其他调整项；
  无杠杆：股权价值 = 经营 OE 现值 + 现金与其他调整项 − 有息负债本金。
  两种口径的经营 OE 都不含利息收支，现金按面值计入，避免利息与本金重复扣减。
- 金融投资（其他权益工具投资、交易性金融资产、基金）不进经营利润，按情景折价单列。
出处见《301589_诺瓦星云.md》第九节。
"""

PRICE = 151.00            # 2026-10-19 收盘（腾讯日线）
SHARES = 0.92448          # 亿股，总股本（2026H1_report 第 44 页；2026-07-31 分红基数口径未变）
SHARES_EX_TREASURY = 0.88889911  # 扣回购专户（2026H1_report 第 35 页）
STUB = 73 / 365           # 2026-10-19 → 2026-12-31
PRIMARY = 'levered'

# ---- 资产负债（2026-06-30，2026H1_report 第 50–52、101、119–123 页） ----
CASH = 9.409              # 货币资金
RESTRICTED = 0.006        # 受限货币资金
BANK_DEBT = 2.141 + 5.295 + 0.367   # 短期借款 + 长期借款 + 一年内到期长期借款
LEASE = 0.117 + 0.194     # 租赁负债 + 一年内到期租赁负债
DEBT_IB = BANK_DEBT + LEASE         # 有息负债（含租赁）8.114
OP_BUFFER = 1.0           # 经营备付（约 2.5% 收入）
INTERIM_DIV = 0.604       # 2026 中期分红，2026-09-16 除息（dividend_20260909）
LAND = 0.647              # 深圳龙岗地块竞得价，2026-10（invest_20261009）
PARK_TOTAL = 6.5          # 未来显示湾区科技园投资上限（invest_20260907）
PARK_YEARS = (2027, 2028, 2029)     # 剩余 5.853 亿按 36 个月建设期均摊
PARK_SUBST_YEARS = range(2027, 2033)
K_FIXED = 0.17            # k 中的固定资产部分（固定资产/收入约 0.22，取增量 0.17）

# 有息负债实际平均利率：近 12 个月利息支出 ÷ 季均有息负债（含租赁）
INT_TTM = (0.1470 - 0.0711) + 0.0844   # 2025 年利息支出 − 2025H1 + 2026H1（2025_annual_report 第 186 页附注；2026H1_report 第 128 页）
DEBT_QEND = [6.342, 7.137, 5.769, 8.212, 8.113]  # 2025-06-30 … 2026-06-30 季末（短借 + 长借 + 一年内到期 + 租赁，f10）
DEBT_AVG = sum((a + b) / 2 for a, b in zip(DEBT_QEND, DEBT_QEND[1:])) / 4
R_D = INT_TTM / DEBT_AVG
TAX_INT = 0.15            # 利息抵税按高新技术企业法定税率

# 金融投资（2026H1_report 第 25–26、101、110–112、118、139 页）
TRADING_FA = 1.295                  # 交易性金融资产（股票，明细未披露）
TAIJIN_0630, TAIJIN_PX = 1.977, 105.69 / 210.00   # 泰金新能 688813：6/30 收 210.00 → 10/19 收 105.69
YUTAI_0630, YUTAI_PX = 0.871, 107.13 / 248.76     # 裕太微 688515：6/30 收 248.76 → 10/19 收 107.13
LISTED_OCI_NOW = TAIJIN_0630 * TAIJIN_PX + YUTAI_0630 * YUTAI_PX
UNLISTED = 6.926 + 0.350            # 其余 12 项未上市股权 + 西高投鲲鹏基金（长期股权投资）
DTL_FV = 0.495 + 0.087              # 6/30 公允价值变动形成的递延所得税负债
TAX_FV = 0.15

# ---- 2026H1 实际（2026H1_report 第 55–59、124、127–129 页） ----
H1 = dict(rev=17.648, gp=17.648 - 7.723, tax_sur=0.145, opex=2.953 + 0.939 + 2.772,
          oth_recurring=0.438 - 0.042, net_int=-(0.0844 - 0.0741))
H1_SBC = 0.379            # 股份支付费用
H1_FCF = 2.182 - 0.442    # 经营现金流 − 购建长期资产
REV_2025 = 35.103


def h1_normalized(imp_rate=0.014, etr=0.125):
    """2026H1 正常化归母净利（含净利息）：剔除公允价值变动 0.585、汇兑损失 0.249、非经常性补助 0.042；减值按常态。"""
    pre = (H1['gp'] - H1['tax_sur'] - H1['opex'] + H1['oth_recurring']
           - imp_rate * H1['rev'] + H1['net_int'])
    return pre * (1 - etr)


# ---- 情景（margin 为含净利息的长期归母净利率） ----
SCEN = {
    'bear': dict(
        p=0.25, rev26=37.6, gm=0.550, tax_sur=0.010, opex=0.355, sbc26=0.57, oth=0.021,
        imp=0.020, net_int=-0.06, etr=0.13,
        growth=[0.04, 0.04, 0.035, 0.03, 0.03, 0.03, 0.025, 0.025, 0.02, 0.02], margin=0.145,
        k=0.80, tg=0.020, troic=0.14, unlisted_haircut=0.50, trading_haircut=0.50),
    'base': dict(
        p=0.50, rev26=39.0, gm=0.557, tax_sur=0.010, opex=0.346, sbc26=0.57, oth=0.022,
        imp=0.014, net_int=-0.05, etr=0.125,
        growth=[0.085, 0.08, 0.07, 0.06, 0.055, 0.05, 0.045, 0.04, 0.03, 0.025], margin=0.175,
        k=0.65, tg=0.025, troic=0.20, unlisted_haircut=0.30, trading_haircut=0.30),
    'bull': dict(
        p=0.25, rev26=40.0, gm=0.568, tax_sur=0.010, opex=0.338, sbc26=0.57, oth=0.022,
        imp=0.010, net_int=-0.04, etr=0.125,
        growth=[0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03], margin=0.195,
        k=0.55, tg=0.025, troic=0.25, unlisted_haircut=0.0, trading_haircut=0.0),
}


def np2026(s):
    """2026 年正常化归母净利（含净利息；剔除公允价值变动、汇兑、非经常性补助；减值按常态）。"""
    pre = (s['rev26'] * (s['gm'] - s['tax_sur'] - s['opex'] + s['oth'] - s['imp'])
           - s['sbc26'] + s['net_int'])
    return pre * (1 - s['etr'])


def op_margin(s, margin=None):
    """经营归母净利率 = 含净利息的净利率 + 2026 年税后净利息占收入比（加回）。"""
    m = s['margin'] if margin is None else margin
    return m + (-s['net_int']) * (1 - s['etr']) / s['rev26']


def cash_ex_debt():
    """现金与其他调整项：货币资金 − 受限 − 经营备付 − 已付中期分红 − 10 月土地款（两种口径相同）。"""
    return CASH - RESTRICTED - OP_BUFFER - INTERIM_DIV - LAND


def adj_net_cash():
    """无杠杆口径经调整净现金（json 的 net_cash_adj_yi）。"""
    return cash_ex_debt() - DEBT_IB


def interest_after_tax():
    return DEBT_IB * R_D * (1 - TAX_INT)


def non_operating(s, detail=False):
    """金融投资：两只已上市股权按 10/19 收盘重估；交易性股票明细未披露，按情景折价；
    未上市股权按情景折价；递延所得税负债随估值下调相应冲减（15%）。"""
    trading = TRADING_FA * (1 - s['trading_haircut'])
    drop = (TAIJIN_0630 + YUTAI_0630 - LISTED_OCI_NOW) + (TRADING_FA - trading)
    dtl = DTL_FV - TAX_FV * drop
    total = LISTED_OCI_NOW + trading + UNLISTED * (1 - s['unlisted_haircut']) - dtl
    if detail:
        return dict(listed_oci=LISTED_OCI_NOW, trading=trading,
                    unlisted=UNLISTED * (1 - s['unlisted_haircut']), dtl=dtl, total=total)
    return total


def h1_reinvest(s):
    """2026H1 实际再投资 = 正常化净利 + 股份支付（非现金）− 自由现金流。"""
    return h1_normalized(s['imp'], s['etr']) + H1_SBC - H1_FCF


def h2_2026_oe(s):
    """2026H2 经营所有者收益：H2 正常化净利 − 全年应有再投资中 H1 未完成的部分，再加回 H2 税后净利息。"""
    np_h2 = np2026(s) - h1_normalized(s['imp'], s['etr'])
    need = (s['rev26'] - REV_2025) * s['k']
    h2_net_int = s['net_int'] - H1['net_int']
    return np_h2 - max(0.0, need - h1_reinvest(s)) - h2_net_int * (1 - s['etr'])


def paths(s, growth=None, margin=None):
    g = s['growth'] if growth is None else growth
    m = s['margin'] if margin is None else margin
    mo = op_margin(s, m)
    rev, rows = s['rev26'], []
    park_each = (PARK_TOTAL - LAND) / len(PARK_YEARS)
    for i, gi in enumerate(g):
        year = 2027 + i
        new = rev * (1 + gi)
        k = s['k'] - (K_FIXED if year in PARK_SUBST_YEARS else 0.0)
        reinv = (new - rev) * k + (park_each if year in PARK_YEARS else 0.0)
        rows.append(dict(year=year, g=gi, rev=new, np=new * m, np_op=new * mo, reinv=reinv,
                         oe=new * mo - reinv))
        rev = new
    return rows


def debt_charge(r, caliber):
    """2026-12-31 时点的债务扣减：有杠杆 = H2 税后利息 + 2027 年起永续税后利息现值（年中）；无杠杆 = 本金。"""
    if caliber == 'levered':
        ia = interest_after_tax()
        return ia / 2 + ia / r * (1 + r) ** 0.5
    return DEBT_IB


def value(s, r, growth=None, margin=None, tg=None, caliber=PRIMARY, detail=False):
    tg = s['tg'] if tg is None else tg
    rows = paths(s, growth, margin)
    pv = sum(row['oe'] / (1 + r) ** (i + 0.5) for i, row in enumerate(rows))
    np_t1 = rows[-1]['np_op'] * (1 + tg)
    oe_t1 = np_t1 * (1 - tg / s['troic'])
    tv = oe_t1 / (r - tg)                       # 第 10 年末价值（次年起现金流按年中计）
    pv_tv = tv * (1 + r) ** 0.5 / (1 + r) ** len(rows)
    op_1231 = pv + pv_tv
    dc = debt_charge(r, caliber)
    eq_1231 = op_1231 + h2_2026_oe(s) + cash_ex_debt() - dc
    eq_now = eq_1231 / (1 + r) ** STUB + non_operating(s)
    if detail:
        return dict(v=eq_now / SHARES, eq=eq_now, op=op_1231, pv_explicit=pv, pv_tv=pv_tv,
                    tv_share=pv_tv / op_1231, rows=rows, oe_t1=oe_t1, debt_charge=dc)
    return eq_now / SHARES


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


def band(pv):
    return ('明显低估' if pv <= 0.75 else '温和低估' if pv <= 0.90 else
            '大致合理' if pv <= 1.10 else '偏贵或价值陷阱风险高')


def weighted(r=0.09, caliber=PRIMARY):
    return sum(SCEN[k]['p'] * value(SCEN[k], r, caliber=caliber) for k in SCEN)


def reweight(pb, pm, pu, base_over=None, caliber=PRIMARY):
    b = dict(SCEN['base'], **(base_over or {}))
    return (pb * value(SCEN['bear'], 0.09, caliber=caliber) + pm * value(b, 0.09, caliber=caliber)
            + pu * value(SCEN['bull'], 0.09, caliber=caliber))


FALSIFIERS = [
    ('F1 2026Q3 单季营收 ≤ 8.82 亿（同比不增）或 2026 全年营收 < 37.0 亿', (0.50, 0.40, 0.10, None)),
    ('F2 2026 全年毛利率 < 54.5% 或 2027H1 毛利率 < 54.0%', (0.40, 0.50, 0.10, dict(margin=0.155))),
    ('F3 2026 扣非归母净利 < 5.6 亿（不高于 2025 年 5.58 亿）', (0.50, 0.50, 0.00, None)),
    ('F4 2026 境外收入增速 < 15% 或 2027H1 境外收入同比 < 10%', (0.35, 0.60, 0.05, None)),
    ('F5 2026 年末存货 > 18 亿或全年资产+信用减值 > 1.0 亿', (0.35, 0.50, 0.15, dict(k=0.80))),
]


def main():
    r = 0.09
    print('诺瓦星云 301589 独立估值（价格日 2026-10-19，现价 %.2f 元，总股本 %.5f 亿股，市值 %.2f 亿）'
          % (PRICE, SHARES, PRICE * SHARES))
    print('经调整净现金（无杠杆口径）%.2f 亿 = 现金与其他调整项 %.2f − 有息负债 %.3f（含租赁 %.3f）'
          % (adj_net_cash(), cash_ex_debt(), DEBT_IB, LEASE))
    print('有息负债实际平均利率 %.2f%%（近 12 个月利息支出 %.4f ÷ 季均有息负债 %.3f）；税后年利息 %.3f 亿；'
          '9%% 永续现值 %.2f 亿' % (R_D * 100, INT_TTM, DEBT_AVG, interest_after_tax(), interest_after_tax() / r))
    print('2026H1 正常化归母净利 %.2f 亿（报表归母 3.32、扣非 2.75）' % h1_normalized())

    res = {}
    for name, s in SCEN.items():
        d = value(s, r, detail=True)
        du = value(s, r, caliber='unlevered', detail=True)
        res[name] = (d, du)
        rr = d['rows']
        print('\n[%s] 概率 %.2f  2026 正常化归母净利 %.2f 亿（收入 %.1f，净利率 %.1f%%）；经营净利率 %.2f%%'
              % (name, s['p'], np2026(s), s['rev26'], np2026(s) / s['rev26'] * 100, op_margin(s) * 100))
        print('  2026H2 经营所有者收益 %.2f 亿；非经营资产 %.2f 亿（%.2f 元/股）'
              % (h2_2026_oe(s), non_operating(s), non_operating(s) / SHARES))
        for i, row in enumerate(rr[:5]):
            prev = rr[i - 1]['np'] if i else np2026(s)
            print('  %d 收入 %.2f（增 %.1f%%）归母净利 %.2f（增 %.1f%%）再投资 %.2f 经营所有者收益 %.2f'
                  % (row['year'], row['rev'], row['g'] * 100, row['np'], (row['np'] / prev - 1) * 100,
                     row['reinv'], row['oe']))
        reinv_rate = sum(x['reinv'] for x in rr[:5]) / sum(x['np_op'] for x in rr[:5])
        incr = (rr[4]['np'] - np2026(s)) / sum(x['reinv'] for x in rr[:5])
        print('  2027–31 再投资率 %.1f%%，增量回报（净利增量/累计再投资）%.1f%%；终值增长 %.1f%%、终值 ROIC %.0f%%'
              % (reinv_rate * 100, incr * 100, s['tg'] * 100, s['troic'] * 100))
        print('  经营价值(2026-12-31) %.1f 亿，其中终值 %.1f%%；债务扣减：有杠杆 %.2f 亿，无杠杆 %.2f 亿'
              % (d['op'], d['tv_share'] * 100, d['debt_charge'], du['debt_charge']))
        print('  有杠杆 V = %.2f（8%%：%.2f；10%%：%.2f；剔除回购专户 %.2f）'
              % (d['v'], value(s, 0.08), value(s, 0.10), d['eq'] / SHARES_EX_TREASURY))
        print('  无杠杆 V = %.2f（8%%：%.2f；10%%：%.2f；剔除回购专户 %.2f）'
              % (du['v'], value(s, 0.08, caliber='unlevered'), value(s, 0.10, caliber='unlevered'),
                 du['eq'] / SHARES_EX_TREASURY))

    for cal, label in (('levered', '有杠杆口径（登记）'), ('unlevered', '无杠杆口径（对照）')):
        vw = weighted(r, cal)
        v8, v10 = weighted(0.08, cal), weighted(0.10, cal)
        idx = 0 if cal == 'levered' else 1
        vw_ex = sum(SCEN[k]['p'] * res[k][idx]['eq'] for k in SCEN) / SHARES_EX_TREASURY
        print('\n%s：三情景 V %.2f / %.2f / %.2f；加权 V = %.2f 元/股；P/V = %.3f（%s）'
              % (label, res['bear'][idx]['v'], res['base'][idx]['v'], res['bull'][idx]['v'],
                 vw, PRICE / vw, band(PRICE / vw)))
        print('  剔除回购专户：加权 V %.2f，P/V %.3f（%s）' % (vw_ex, PRICE / vw_ex, band(PRICE / vw_ex)))
        print('  股权成本 8%% → %.2f（P/V %.3f）；10%% → %.2f（P/V %.3f）' % (v8, PRICE / v8, v10, PRICE / v10))
        print('  V 不变时各档价格：≤%.2f 明显低估；%.2f–%.2f 温和低估；%.2f–%.2f 大致合理；>%.2f 偏贵'
              % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
        irr = solve(lambda x: value(SCEN['base'], x, caliber=cal), 0.04, 0.30, PRICE)
        print('  现价隐含回报（基准情景流，含终值与现金调整）：%.2f%%' % (irr * 100))

    base = SCEN['base']
    g10 = solve(lambda x: value(base, 0.09, growth=[x] * 10), -0.05, 0.40, PRICE)
    print('\n反向 DCF（有杠杆）①：基准净利率 17.5%%、资本强度与科技园不变，现价隐含 2027–36 年收入与净利统一增速 %.2f%%'
          % (g10 * 100))
    rev36 = base['rev26'] * (1 + g10) ** 10
    print('   对应 2036 年归母净利 %.2f 亿（基准路径 %.2f 亿）' % (rev36 * base['margin'], paths(base)[-1]['np']))
    m_imp = solve(lambda x: value(base, 0.09, margin=x), 0.05, 0.40, PRICE)
    print('反向 DCF（有杠杆）②：基准增长路径不变，现价隐含长期归母净利率 %.2f%%' % (m_imp * 100))
    eq_op = ((PRICE * SHARES - non_operating(base)) * (1 + 0.09) ** STUB
             - h2_2026_oe(base) - cash_ex_debt() + debt_charge(0.09, PRIMARY))
    np27 = paths(base)[0]['np_op']
    gperp = solve(lambda g: np27 * (1 - g / base['troic']) / (0.09 - g) * 1.09 ** 0.5, 0.0, 0.085, eq_op)
    print('反向 DCF（有杠杆）③：以 2027 基准经营净利 %.2f 亿起算、ROIC 20%%，现价隐含永续增长 %.2f%%'
          % (np27, gperp * 100))

    print('\n基准情景敏感性（有杠杆，元/股；利息与经营收益同率折现）：')
    for rr_ in (0.08, 0.09, 0.10):
        print('  股权成本 %.0f%%：' % (rr_ * 100) + '  '.join(
            '终值增长 %.1f%% → %.1f' % (tg * 100, value(base, rr_, tg=tg)) for tg in (0.015, 0.02, 0.025)))
    print('  ' + '  '.join('净利率 %.1f%% → %.1f' % (m * 100, value(base, 0.09, margin=m))
                          for m in (0.155, 0.165, 0.175, 0.185)))

    mcap = PRICE * SHARES
    npb = np2026(base)
    ebit = npb / (1 - base['etr']) - base['net_int']
    ev = mcap - non_operating(base) - (CASH - RESTRICTED - DEBT_IB)
    print('\n交叉验证：PE(2026 正常化) %.1f×，扣金融投资后 %.1f×；PE(TTM 报表) 22.3×；PB %.2f×；EV/EBIT %.1f×'
          % (mcap / npb, (mcap - non_operating(base)) / npb, mcap / 40.862, ev / ebit))
    div_ttm = 1.58 * SHARES_EX_TREASURY
    buyback_ttm = 1.50 + 1.00
    print('近 12 个月分红 %.2f 亿（%.2f%%）＋回购 %.2f 亿（%.2f%%，用于激励而非注销）'
          % (div_ttm, div_ttm / mcap * 100, buyback_ttm, buyback_ttm / mcap * 100))
    nd = non_operating(base, detail=True)
    print('基准非经营资产：已上市两只（10/19 市值）%.2f + 交易性股票（七折）%.2f + 未上市（七折）%.2f − 递延税 %.2f = %.2f 亿'
          % (nd['listed_oci'], nd['trading'], nd['unlisted'], nd['dtl'], nd['total']))

    print('\n证伪条件触发后的独立 V（有杠杆；括号内为无杠杆）：')
    for name, (pb, pm, pu, over) in FALSIFIERS:
        v = reweight(pb, pm, pu, over)
        vu = reweight(pb, pm, pu, over, caliber='unlevered')
        print('  %s → V = %.2f（P/V %.2f）（%.2f）' % (name, v, PRICE / v, vu))

    print('\n2026 正常化归母净利三档：bear %.2f / base %.2f / bull %.2f 亿'
          % tuple(np2026(SCEN[k]) for k in ('bear', 'base', 'bull')))
    vw, vwu = weighted(r), weighted(r, 'unlevered')
    print('登记（有杠杆）：bear %.2f / base %.2f / bull %.2f；加权 %.2f；P/V %.3f（%s）'
          % (res['bear'][0]['v'], res['base'][0]['v'], res['bull'][0]['v'], vw, PRICE / vw, band(PRICE / vw)))
    print('对照（无杠杆）：bear %.2f / base %.2f / bull %.2f；加权 %.2f；P/V %.3f（%s）'
          % (res['bear'][1]['v'], res['base'][1]['v'], res['bull'][1]['v'], vwu, PRICE / vwu, band(PRICE / vwu)))


if __name__ == '__main__':
    main()
