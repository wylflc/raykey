#!/usr/bin/env python3
"""新奥股份（600803）独立估值：OI-291 池内独立审计 b08。

运行：python3 valuation.py
口径：归母（新奥能源按新能香港 2026-09-03 持股 35.00% 穿透），金额单位亿元，每股价值元。
方法：归母所有者收益 DCF。归母穿透经调整净现金为负，按框架用有杠杆口径（净负债按现规模滚动，
扣其税后利息现值）；无杠杆口径（全额扣净负债）一并列示。估值基准为 2026-06-30 资产负债表，
现金流折现到 2026-06-30 后按股权成本滚动到价格日 2026-10-20。
所有输入写在本文件内，出处见同目录上级的公司全文。
"""

PRICE = 20.07                 # 2026-10-20 收盘（元）
SHARES = 30.9519              # 总股本（亿股，腾讯行情，含回购专户）
REPO_SHARES = 0.01201580      # 回购专户 1,201,580 股（dividend_20261013 第 1 页）
COE = 0.09
TAX = 0.25                    # 法定税率，用于利息税盾
RATE_DEBT = 0.028             # 有息负债实际平均利率：2025 利息费用 8.88/平均借贷 321≈2.77%；2026H1 年化 9.16/320≈2.87%
ROLL_YEARS = 112 / 365        # 2026-06-30 → 2026-10-20

# ---------------------------------------------------------------- 资产负债（2026-06-30）
# 新奥能源层（香港准则中期公告第 5、9-10 页）
ENN_BORROW = 189.44           # 借贷总额（银行及其他贷款 118.96 + 优先票据 70.48）
ENN_CASH = 85.54              # 银行结余及现金（不含受限）
ENN_DIV_PAYABLE = 22.77       # 2025 末期股息，7-31 已付
ENN_OTHER_MIN_DIV = 3.47      # 合并应付股利 47.97 − 新奥股份 29.70 − 新奥能源外部股东 14.80（附属公司少数股东股利，归入新奥能源层）
ENN_BUFFER = 15.0             # 经营备付（约 1.5 周现金成本）
ENN_STAKE = 0.3500            # 396,162,534 / 1,131,839,264（holders_20260905 第 1 页）

# 新奥股份合并（2026H1_report 第 53-55、110-111、155-166 页）
CONS_BORROW = 305.77          # 短期借款 145.74 + 一年内到期非流动负债（扣租赁）83.76 + 长期借款 44.36 + 应付债券 31.28 + 长期应付款 0.63
CONS_CASH = 201.40            # 货币资金 165.98 − 受限 10.70 + 拆出资金 46.11（境内银行）
CONS_TFA = 4.84               # 交易性金融资产（结构性存款 0.84 + 理财 4.00）
CONS_DIV_PAYABLE = 47.97      # 应付股利
ABS_LIAB = 39.06              # 舟山管道资产支持专项计划款，计入其他应付款-股权转让款（第 160、178 页），按类债务
DEPOSITS = 3.99               # 财务公司吸收存款（公司客户；无关联方金融业务，第 40 页）
OWN_DIV_PAYABLE = 29.70       # 新奥股份 2025 末期股息 0.96 元，7-09 已付
OWN_BUFFER = 10.0             # 自有层经营备付（贸易保证金、信用证）
ENN_SHARES_AFTER = 1.2        # 6-30 后增持新奥能源 3,055,900 股的现金
ENN_DIV_RECEIVED = 7.7        # 新能香港收到新奥能源 2025 末期股息（税后约数）
CONS_BUFFER = 25.0            # 合并口径经营备付

NONOP = 0.0                   # 非经营资产：中石化销售 1.13% 股权（公允价 37.6，归母约 13.2）的股利已含在利润里，不另加

# 新奥能源股价（SOTP 交叉验证）
ENN_PRICE_HKD = 49.20         # 2026-10-20 收盘（腾讯行情）
HKDCNY = 0.8505
ENN_TOTAL_SHARES = 11.31839264  # 亿股
XNHK_SHARES = 3.96162534        # 亿股

# ---------------------------------------------------------------- 情景
# np2026：2026 年正常化归母净利（含净利息、剔除一次性）；growth：2027-2031 经营收益增速；
# gT：终值增长；rr：再投资率（占经营收益）；windfall：霍尔木兹扰动下 JKM−HH 价差的税后归母一次性超额（年份偏移: 金额），不资本化
SCEN = {
    'bear': dict(p=0.25, np2026=36.5, growth=[-0.03, -0.02, 0.0, 0.01, 0.01], gT=0.010, rr=0.32, windfall={},
                 note='LNG 2027 年后过剩、长协价差≤0；舟山利用率低；新奥能源归母降至约 54 亿'),
    'base': dict(p=0.50, np2026=44.0, growth=[0.03, 0.03, 0.025, 0.025, 0.02], gT=0.020, rr=0.30,
                 windfall={0.25: 2.5, 1.0: 2.5},
                 note='新奥能源正常化归母约 60 亿×35%=21.0；自有业务约 23.0；切尼尔二期 2027 全量'),
    'bull': dict(p=0.25, np2026=50.5, growth=[0.05, 0.045, 0.04, 0.03, 0.03], gT=0.025, rr=0.30,
                 windfall={0.25: 5.0, 1.0: 8.0},
                 note='扰动延续至 2027、长协中枢价差 4-5 美元；顺价完成；新奥能源约 64 亿'),
}


def scen_override(**kw):
    """复制情景并按 {情景名: {字段: 值}} 覆盖。"""
    out = {}
    for n, s in SCEN.items():
        d = dict(s)
        d.update(kw.get(n, {}))
        out[n] = d
    return out


# 证伪条件触发后的情景改写（触发后 V 由 weighted_from 计算）
FALSIFIERS = [
    ('F1 2027 年 JKM 年均 <9 美元且 Henry Hub ≥3.5 美元，或 2027 年“平台交易气毛利+衍生品已实现结算”<15 亿',
     '2028-03-31', dict(r=COE, scen=scen_override(bear={'p': 0.50}, base={'p': 0.40}, bull={'p': 0.10}))),
    ('F2 2026 年归母经营利润 <48 亿（2025 年 51.91，激励目标 54.45）',
     '2027-03-31', dict(r=COE, scen=scen_override(base={'np2026': 40.5}, bull={'np2026': 46.5}))),
    ('F3 新奥能源 2026 年核心利润 <63 亿或全年股息 <3.00 港元',
     '2027-03-31', dict(r=COE, scen=scen_override(bear={'np2026': 34.75}, base={'np2026': 42.25}, bull={'np2026': 48.75}))),
    ('F4 2026 年末归母穿透净负债（含专项计划）>150 亿，或控股股东质押占其持股 >40%，或出现关联方非经营性占用',
     '2027-04-30', dict(r=0.10, nd=150.0, scen=SCEN)),
    ('F5（反向）2026 年归母经营利润 ≥56 亿且 2027 年中报经营利润同比 ≥+10%',
     '2027-08-31', dict(r=COE, scen=scen_override(bear={'p': 0.10}, base={'p': 0.45}, bull={'p': 0.45}))),
]


def weighted_from(scen, r=COE, nd=None):
    nd = ND if nd is None else nd
    return sum(s['p'] * value(s, r, True, nd)[0] / SHARES for s in scen.values())


def nd_attr():
    """归母穿透经调整净负债（无杠杆口径，正数为净负债）。"""
    enn_nd = ENN_BORROW - ENN_CASH + ENN_DIV_PAYABLE + ENN_OTHER_MIN_DIV + ENN_BUFFER
    own_borrow = CONS_BORROW - ENN_BORROW
    own_cash = CONS_CASH - ENN_CASH
    own_tfa = CONS_TFA - 0.84
    own_nd = (own_borrow + ABS_LIAB + DEPOSITS + OWN_DIV_PAYABLE + OWN_BUFFER + ENN_SHARES_AFTER
              - own_cash - own_tfa - ENN_DIV_RECEIVED)
    return own_nd + ENN_STAKE * enn_nd, own_nd, enn_nd


def cons_net_cash_adj():
    return CONS_CASH + CONS_TFA - CONS_BUFFER - CONS_DIV_PAYABLE - DEPOSITS - CONS_BORROW - ABS_LIAB


ND, OWN_ND, ENN_ND = nd_attr()


def value(s, r=COE, levered=True, nd=ND, growth=None, gT=None, years=None):
    """股权价值（亿元，价格日）。growth/gT 可覆盖情景设置（反向 DCF 用）。"""
    growth = s['growth'] if growth is None else growth
    gT = s['gT'] if gT is None else gT
    I = nd * RATE_DEBT * (1 - TAX)              # 归母税后净利息（按现规模滚动）
    np_op = s['np2026'] + I                     # 经营收益（加回税后利息）
    flows = [(0.25, 0.5 * np_op * (1 - s['rr']))]   # 2026 下半年
    x = np_op
    for k, g in enumerate(growth, start=1):
        x *= (1 + g)
        flows.append((float(k), x * (1 - s['rr'])))
    n = len(growth)
    tv = flows[-1][1] * (1 + gT) / (r - gT)
    pv_op = sum(cf / (1 + r) ** t for t, cf in flows) + tv / (1 + r) ** n
    pv_wf = sum(a / (1 + r) ** t for t, a in s['windfall'].items())
    if levered:
        pv_int = 0.5 * I / (1 + r) ** 0.25 + sum(I / (1 + r) ** k for k in range(1, n + 1)) + (I / r) / (1 + r) ** n
        eq0 = pv_op + pv_wf - pv_int + NONOP
    else:
        eq0 = pv_op + pv_wf - nd + NONOP
    return eq0 * (1 + r) ** ROLL_YEARS, dict(I=I, np_op=np_op, pv_op=pv_op, tv=tv, pv_tv=tv / (1 + r) ** n,
                                             pv_wf=pv_wf, flows=flows)


def per_share(eq, shares=SHARES):
    return eq / shares


def weighted(r=COE, levered=True, shares=SHARES):
    return sum(s['p'] * per_share(value(s, r, levered)[0], shares) for s in SCEN.values())


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


def main():
    mcap = PRICE * SHARES
    print('=== 新奥股份（600803）独立估值 ===')
    print(f'价格日 2026-10-20  现价 {PRICE:.2f} 元  总股本 {SHARES:.4f} 亿股  A 股市值 {mcap:.1f} 亿元')
    print(f'归母穿透经调整净负债 {ND:.1f} 亿（自有层 {OWN_ND:.1f} + 新奥能源层 {ENN_ND:.1f}×{ENN_STAKE:.2%}）'
          f' → net_cash_adj（归母）{-ND:.1f}；合并口径经调整净现金 {cons_net_cash_adj():.1f}')
    I = ND * RATE_DEBT * (1 - TAX)
    pv_int = 0.5 * I / (1 + COE) ** 0.25 + sum(I / (1 + COE) ** k for k in range(1, 6)) + (I / COE) / (1 + COE) ** 5
    print(f'税后利息 {I:.2f} 亿/年（利率 {RATE_DEBT:.1%}，税率 {TAX:.0%}）；利息现值（含 2026H2，9%）{pv_int:.1f} 亿'
          f'（简单永续 I/r {I / COE:.1f} 亿）')
    print()
    print('情景      概率   2026正常化归母  V有杠杆(元)  V无杠杆(元)  P/V(有杠杆)  终值占比')
    for name, s in SCEN.items():
        eq, d = value(s)
        equ, _ = value(s, levered=False)
        share_tv = d['pv_tv'] / (d['pv_op'])
        print(f'{name:6s}  {s["p"]:.2f}   {s["np2026"]:>8.1f}       {per_share(eq):>7.2f}      {per_share(equ):>7.2f}'
              f'      {PRICE / per_share(eq):>5.2f}      {share_tv:.0%}')
    for name, s in SCEN.items():
        eq, d = value(s)
        print(f'  {name}: 经营现值 {d["pv_op"]:.1f}（终值现值 {d["pv_tv"]:.1f}）+ 价差超额 {d["pv_wf"]:.1f} − 利息现值 {pv_int:.1f}'
              f' = {eq / (1 + COE) ** ROLL_YEARS:.1f}（6-30）→ ×{(1 + COE) ** ROLL_YEARS:.4f} = {eq:.1f} 亿（10-20）')
    vw = weighted()
    vwu = weighted(levered=False)
    print(f'加权 V（有杠杆，9%）= {vw:.2f} 元；P/V = {PRICE / vw:.2f}')
    print(f'加权 V（无杠杆，9%）= {vwu:.2f} 元；P/V = {PRICE / vwu:.2f}')
    vw_ex = weighted(shares=SHARES - REPO_SHARES)
    print(f'剔除回购专户股份（{SHARES - REPO_SHARES:.4f} 亿股）加权 V = {vw_ex:.2f} 元；P/V = {PRICE / vw_ex:.2f}')
    print()
    for r in (0.08, 0.10):
        parts = '  '.join(f'{n} {per_share(value(s, r)[0]):.2f}' for n, s in SCEN.items())
        print(f'股权成本 {r:.0%}: 加权 V = {weighted(r):.2f} 元（{parts}）；无杠杆加权 {weighted(r, False):.2f}')
    print()
    base = SCEN['base']
    irr = solve(lambda r: value(base, r)[0], 0.035, 0.30, mcap)
    print(f'现价隐含回报（基准情景所有者收益流含终值与净负债，使现值=现价的折现率）= {irr:.2%}')
    # 反向 DCF
    g_perp = solve(lambda g: value(base, COE, growth=[g] * 5, gT=g)[0], -0.05, 0.085, mcap)
    g10 = solve(lambda g: value(base, COE, growth=[g] * 10, gT=0.02)[0], -0.10, 0.30, mcap)
    print(f'反向 DCF：基准起点（2026 经营收益 {base["np2026"] + I:.1f} 亿、再投资率 {base["rr"]:.0%}）下，'
          f'现价隐含永续增速 {g_perp:.2%}；或 2027-2036 年 10 年增速 {g10:.2%}、此后 2%')
    print()
    # 交叉验证
    enn_mv = XNHK_SHARES * ENN_PRICE_HKD * HKDCNY
    enn_mcap = ENN_TOTAL_SHARES * ENN_PRICE_HKD * HKDCNY
    print(f'新奥能源市值 {enn_mcap:.1f} 亿元；新能香港所持 35.00% 市值 {enn_mv:.1f} 亿元（{enn_mv / SHARES:.2f} 元/股）')
    implied_own = mcap - enn_mv
    own_np = 23.0
    print(f'现价隐含自有业务（含自有层净负债）价值 {implied_own:.1f} 亿，对应自有业务正常化归母 {own_np:.1f} 亿的 {implied_own / own_np:.1f} 倍')
    # 自有业务内在：归母 23.0、转化 85%、增长 2.5%（利润已含利息，按有杠杆口径）
    own_v = own_np * 0.85 * 1.025 / (COE - 0.025)
    enn_np_norm = 60.0
    enn_v = enn_np_norm * 0.55 * 1.015 / (COE - 0.015)
    for label, own_val in (('自有业务 DCF（转化 85%、增长 2.5%）', own_v), ('自有业务 12 倍 PE', own_np * 12), ('自有业务 15 倍 PE', own_np * 15)):
        sotp = enn_mv + own_val
        print(f'SOTP（新奥能源按市值 + {label} {own_val:.1f}）= {sotp:.1f} 亿 → {sotp / SHARES:.2f} 元/股')
    sotp_i = ENN_STAKE * enn_v + own_v
    print(f'SOTP（新奥能源内在 {enn_v:.1f}×35% + 自有业务 DCF）= {sotp_i:.1f} 亿 → {sotp_i / SHARES:.2f} 元/股')
    print(f'新奥能源按 2026 正常化归母 {enn_np_norm:.0f} 亿的 PE = {enn_mcap / enn_np_norm:.1f} 倍；股息率 {3.00 / ENN_PRICE_HKD:.1%}')
    # EV/EBIT（合并，2025）
    ebit_2025 = 117.11 + 8.88 - 3.56
    minority_mkt = (1 - ENN_STAKE) * enn_mcap + 63.12 + (392.04 - 0.6527 * 480.97 - 63.12)
    ev = mcap + minority_mkt - cons_net_cash_adj()
    print(f'合并 EV ≈ {ev:.0f} 亿（含少数股东按新奥能源市值），2025 EBIT {ebit_2025:.1f} 亿 → EV/EBIT {ev / ebit_2025:.1f} 倍')
    print(f'PE：现价/2026 正常化归母（基准）{mcap / base["np2026"]:.1f} 倍；2018-2025 年末 PE 中位约 10.3 倍；'
          f'PB {mcap / 234.48:.2f} 倍')
    print(f'股息率：过去 12 个月 0.96 元 → {0.96 / PRICE:.2%}；2026 预计 0.25+约 0.65 元 → {0.90 / PRICE:.2%}；无在实施回购')
    print()
    for n, s in SCEN.items():
        _, d = value(s)
        path = [round(cf / (1 - s['rr']), 1) for _, cf in d['flows'][1:]]
        oe = [round(cf, 1) for _, cf in d['flows']]
        print(f'{n} 经营收益 2027-2031 {path}；所有者收益（2026H2 起）{oe}；终值（2031 末）{d["tv"]:.0f}')
    print()
    print(f'V 不变时各档价格：明显低估 ≤{0.75 * vw:.2f}；温和低估 {0.75 * vw:.2f}～{0.90 * vw:.2f}；'
          f'大致合理 {0.90 * vw:.2f}～{1.10 * vw:.2f}；偏贵 >{1.10 * vw:.2f}')
    print()
    print('证伪条件触发后的独立 V（有杠杆口径）：')
    for text, deadline, kw in FALSIFIERS:
        v = weighted_from(kw['scen'], kw.get('r', COE), kw.get('nd'))
        print(f'  {text}｜{deadline}｜V={v:.2f} 元（P/V {PRICE / v:.2f}）')


if __name__ == '__main__':
    main()
