#!/usr/bin/env python3
"""工商银行（601398）独立估值：股利折现（DDM）与剩余收益（RI，P/B-ROE）互校。

OI-291 池内独立审计 b03。价格日 2026-10-19，A 股 8.60 元（含 2026 年中期股息 0.1511 元，除息日 2026-10-21）。
内部单位：人民币百万元；输出：亿元、元/股。运行：python3 valuation.py

口径
- 每股价值按全部普通股（A 股 269,612,212,539 股 + H 股 86,794,044,550 股 = 356,406,257,089 股）计算。
  2026-09-06 董事会通过的向特定对象发行 A 股（不超过 1,000 亿元，财政部 700 亿元，其余由中国烟草系认购）
  按 1,000 亿元、发行价 8.40 元于 2026-12-31 完成计入，新增约 119.05 亿股、合计约 3,683.11 亿股。
  新资本按银行平均 ROE 投放：2027 年起普通股东净利、股利、账面同比例放大 (1 + 1,000 亿 / 2026 年末普通股权益)，
  再除以扩大后股本；2026 年中期股息只归现有股本，2026 年末期股息按扩大后股本分配。
- 归母净利扣除对优先股、永续债的分配后才归普通股东；账面值为扣除其他权益工具后的普通股权益。
- 银行不做净现金调整（存款、现金是经营负债与经营资产），净现金调整与非经营资产均为 0。
- 2026 年用上半年实际 + 下半年预测（报告口径，三情景共用）；情景分歧自 2027 年开始，驱动项为生息资产增速、
  净息差、手续费增速、其他非息净收入/生息资产、成本增速、信用成本（全部减值 / 平均贷款）、税率、分红率。
- 终值：2031 年后永续增长 2.5%；2032 年普通股东净利 = 2031 年 × 1.025（资本水平停在 2031 年末），
  终值 ROE = E_2032 / B_2031，终值分红率 = 1 - g / ROE_T。
- 拨备覆盖率高于监管线的部分只讨论、不计入价值。
"""
from datetime import date

# ----------------------------------------------------------------------------------------------
# 一、实际数（2026H1_report 第 13-15、18-24、69-73、81、92、99、119-122 页；2025_annual_report 第 14-17、26-32、165、207-212 页）
# ----------------------------------------------------------------------------------------------
PRICE = 8.60                      # A 股 2026-10-19 收盘（腾讯行情），含 0.1511 元中期股息
VAL_DATE = date(2026, 10, 19)
SHARES_A = 269_612.212539         # 百万股
SHARES_H = 86_794.044550
SHARES0 = SHARES_A + SHARES_H     # 356,406.257089 百万股 = 3,564.0626 亿股
INTERIM_DPS_2026 = 0.1511         # 元/股（dividend_20261015_463887），A 股 2026-10-21 派发
INTERIM_POOL_2026 = 53_853        # 百万元（2026H1 第 99 页）

PLACEMENT_AMT = 100_000           # 百万元（holders_20260907_079153 第 2 页）
PLACEMENT_PRICE = 8.40            # 假设：不低于发行期首日前 20 个交易日均价（2026-10-19 前 20 日收盘均价 8.26）
PLACEMENT_DATE = date(2026, 12, 31)
NEW_SHARES = PLACEMENT_AMT / PLACEMENT_PRICE
SHARES1 = SHARES0 + NEW_SHARES

PARENT_EQ_0630 = 4_326_994
OTHER_EQ_0630 = 364_666           # 优先股 114,927 + 永续债 249,739（2026H1 第 119 页）
ORD_EQ_0630 = PARENT_EQ_0630 - OTHER_EQ_0630   # 3,962,328 → 每股 11.12 元
ORD_EQ_2025 = 4_244_259 - 384_657              # 2025 年末普通股权益 3,859,602
FINAL_POOL_2025 = 60_197                       # 2025 末期股息，2026 上半年扣减（2026H1 第 122 页）
CET1_0630 = 3_940_780
RWA_0630 = 29_832_780
NPL_0630 = 411_818
ALLOW_0630 = 896_048
LOANS_0630 = 31_992_126

H1_26 = dict(nii=341_237, fee=69_235, oth=55_387, othcost=17_173, opex=105_754, sur=5_620,
             imp=127_018 + 738, pbt=210_010, tax=33_535, parent=173_682, dist=4_414,
             iea=53_422_255, loans=31_433_884)
FY_25 = dict(nii=635_126, fee=111_171, oth=91_973, othcost=33_468, opex=235_173, sur=10_658,
             imp=132_973 + 1_887, pbt=424_435, tax=53_669, parent=368_562, dist=11_764, div=110_593,
             iea=49_730_513, loans=29_873_346)
H1_25 = dict(nii=313_576, fee=67_020, oth=46_496, othcost=15_536, opex=102_922, sur=5_199,
             imp=104_007 + 522, pbt=199_008, tax=30_205, parent=168_103, dist=3_669)
H2_25 = {k: FY_25[k] - H1_25[k] for k in H1_25}
OCI_OTHER_H1_2026 = ORD_EQ_0630 - (ORD_EQ_2025 + H1_26['parent'] - H1_26['dist'] - FINAL_POOL_2025)

# ----------------------------------------------------------------------------------------------
# 二、2026 下半年预测（报告口径，三情景共用）
# ----------------------------------------------------------------------------------------------
H2_IEA_AVG = 55_400_000           # 下半年平均生息资产（上半年 53.42 万亿；年末总资产约 58.5 万亿）
H2_NIM = 0.0127                   # 年化（上半年 1.29%，2025 全年 1.28%）
H2_LOANS_AVG = 32_400_000
H2_CREDIT_COST = 0.0030           # 年化；工行下半年计提历来偏低（2024H2 约 0.18%、2025H2 约 0.20%）
H2_OTH_NET = 24_000               # 其他非息收入减其他业务成本（2025H2 为 27,545，债券收益回落）
H2_TAX = 0.105                    # 2025 下半年实际约 10.4%
H2_MINORITY = 0.012
H2_DIST = 7_500                   # 下半年对优先股、永续债分配（2025 下半年 8,095）
RWA_GROWTH_H2_26 = 0.025


def h2_2026():
    nii = H2_NIM * H2_IEA_AVG * 0.5
    fee = H2_25['fee'] * 1.03
    opex = H2_25['opex'] * 1.025
    sur = H2_25['sur'] * 1.06
    imp = H2_CREDIT_COST * H2_LOANS_AVG * 0.5
    pbt = nii + fee + H2_OTH_NET - opex - sur - imp + 300
    parent = pbt * (1 - H2_TAX) * (1 - H2_MINORITY)
    return dict(nii=nii, fee=fee, oth_net=H2_OTH_NET, opex=opex, sur=sur, imp=imp, pbt=pbt,
                parent=parent, dist=H2_DIST, ord=parent - H2_DIST)


H2 = h2_2026()
FY26 = dict(nii=H1_26['nii'] + H2['nii'], fee=H1_26['fee'] + H2['fee'],
            oth_net=H1_26['oth'] - H1_26['othcost'] + H2['oth_net'],
            opex=H1_26['opex'] + H2['opex'], sur=H1_26['sur'] + H2['sur'], imp=H1_26['imp'] + H2['imp'],
            pbt=H1_26['pbt'] + H2['pbt'], parent=H1_26['parent'] + H2['parent'],
            dist=H1_26['dist'] + H2['dist'])
FY26['ord'] = FY26['parent'] - FY26['dist']
IEA_AVG_26 = (H1_26['iea'] + H2_IEA_AVG) / 2
LOANS_AVG_26 = (H1_26['loans'] + H2_LOANS_AVG) / 2
RWA_2026 = RWA_0630 * (1 + RWA_GROWTH_H2_26)
LOAN_SHARE = H1_26['loans'] / H1_26['iea']          # 平均贷款 / 平均生息资产 ≈ 58.8%
RWA_TO_IEA = RWA_0630 / H1_26['iea']                 # ≈ 0.558
CET1_TO_BOOK = CET1_0630 / ORD_EQ_0630               # 扣减项约 0.5%
SUR_RATE = FY_25['sur'] / (FY_25['nii'] + FY_25['fee'] + FY_25['oth'] - FY_25['othcost'])
DIST_RATE = 0.00035                                  # 其他权益工具分配 / 平均 RWA（2025 年约 0.044%，高息工具已赎回）
PAYOUT_2026 = 0.31                                   # 2026 中期分红率已提至 31%（六大行统一）
DIV_2026 = PAYOUT_2026 * FY26['ord']
FINAL_POOL_2026 = DIV_2026 - INTERIM_POOL_2026
# 申报口径（股利计入所属年度）2026 年末普通股权益，不含定增
B_2026_PRE = ORD_EQ_2025 - FINAL_POOL_2025 + FY26['ord'] - DIV_2026 + OCI_OTHER_H1_2026
SCALE = 1 + PLACEMENT_AMT / B_2026_PRE              # 新资本按平均 ROE 投放的放大系数

# ----------------------------------------------------------------------------------------------
# 三、情景驱动（2027-2031）
# ----------------------------------------------------------------------------------------------
YEARS = [2027, 2028, 2029, 2030, 2031]
G_TERM = 0.025
INTERIM_SHARE = 0.47              # 中期股息占全年（2025 年 45.6%，2026 年约 47%）
MINORITY = 0.008
SCENARIOS = {
    'bear': dict(p=0.25, iea_g=[0.060, 0.050, 0.045, 0.040, 0.040],
                 nim=[0.0123, 0.0118, 0.0113, 0.0113, 0.0113], fee_g=0.0, oth=0.00075, opex_g=0.03,
                 cc=[0.0070, 0.0080, 0.0072, 0.0072, 0.0072], tax=0.12, payout=0.30,
                 desc='净息差 2027 年 1.23%、2029 年起 1.13%（LPR 再降、活期存款利率触底），信用成本 0.70%→0.80%→0.72%'
                      '（零售与地产不良继续上升），手续费零增长，分红率 30%'),
    'base': dict(p=0.50, iea_g=[0.070, 0.060, 0.055, 0.050, 0.045],
                 nim=[0.0126, 0.0125, 0.0124, 0.0124, 0.0124], fee_g=0.03, oth=0.00095, opex_g=0.03,
                 cc=[0.0060] * 5, tax=0.13, payout=0.31,
                 desc='净息差 1.26%→1.24% 企稳（定期存款重定价对冲贷款收益率下行），信用成本 0.60%'
                      '（维持覆盖率所需水平），手续费 +3%、成本 +3%，分红率 31%'),
    'bull': dict(p=0.25, iea_g=[0.075, 0.065, 0.060, 0.055, 0.050],
                 nim=[0.0129, 0.0130, 0.0131, 0.0131, 0.0131], fee_g=0.04, oth=0.00110, opex_g=0.03,
                 cc=[0.0050] * 5, tax=0.135, payout=0.33,
                 desc='净息差回升至 1.31%（负债成本继续下行、监管护息差），信用成本 0.50%（2024-2025 实际水平），'
                      '手续费 +4%，分红率提至 33%（战略投资协议目标含合理提升分红比例）'),
}


def project(s, payout=None, cc_shift=0.0, nim_shift=0.0):
    """不含定增的逐年预测（申报口径账面）；定增效应在估值时以 SCALE 放大。"""
    b_prev = B_2026_PRE if payout is None else B_2026_PRE + (PAYOUT_2026 - payout) * FY26['ord']
    payout = s['payout'] if payout is None else payout
    rows, iea, fee, opex, rwa = [], IEA_AVG_26, FY26['fee'], FY26['opex'], RWA_2026
    for i, y in enumerate(YEARS):
        iea *= 1 + s['iea_g'][i]
        rwa *= 1 + s['iea_g'][i]
        loans = LOAN_SHARE * iea
        nim = s['nim'][i] + nim_shift
        nii = nim * iea
        fee *= 1 + s['fee_g']
        oth = s['oth'] * iea
        opex *= 1 + s['opex_g']
        opinc = nii + fee + oth
        imp = (s['cc'][i] + cc_shift) * loans
        pbt = opinc - opex - SUR_RATE * opinc - imp
        parent = pbt * (1 - s['tax']) * (1 - MINORITY)
        dist = DIST_RATE * RWA_TO_IEA * iea
        ordnp = parent - dist
        div = payout * ordnp
        b = b_prev + ordnp - div
        rows.append(dict(year=y, iea=iea, nim=nim, nii=nii, fee=fee, oth=oth, opex=opex, imp=imp, pbt=pbt,
                         parent=parent, dist=dist, ordnp=ordnp, div=div, b_open=b_prev, b=b,
                         roe=ordnp / ((b_prev + b) / 2), roe_open=ordnp / b_prev, ci=opex / opinc,
                         cet1=CET1_TO_BOOK * (b + (1 - INTERIM_SHARE) * div) / rwa))
        b_prev = b
    return rows


def terminal_earnings(rows, roe_t=None):
    """终值首年（2032）普通股东净利：默认 = 2031 年 × (1 + g)（资产与利润按 g 增长，资本水平停在 2031 年）；
    给定 roe_t 时 = roe_t × 2031 年末普通股权益。返回 (E_2032, B_2031)。"""
    b31 = rows[-1]['b']
    e32 = rows[-1]['ordnp'] * (1 + G_TERM) if roe_t is None else roe_t * b31
    return e32, b31


def yf(d):
    return (d - VAL_DATE).days / 365.0


def ddm(s, r=0.09, roe_t=None, placement=True, **kw):
    """股利折现：中期股息当年 10-31、末期次年 06-30 派发；终值按 2.5% 永续增长、分红率 = 1 - g/ROE_T。
    placement=False 时不计定增（放大系数 1、股本不变），用于测算定增对每股价值的影响。"""
    scale, shares1 = (SCALE, SHARES1) if placement else (1.0, SHARES0)
    rows = project(s, **kw)
    payout26 = kw.get('payout') if kw.get('payout') is not None else PAYOUT_2026
    final26 = payout26 * FY26['ord'] - INTERIM_POOL_2026
    pv = INTERIM_DPS_2026 / (1 + r) ** yf(date(2026, 10, 21))
    pv += final26 / shares1 / (1 + r) ** yf(date(2027, 6, 30))
    for row in rows:
        y = row['year']
        d = scale * row['div'] / shares1
        pv += INTERIM_SHARE * d / (1 + r) ** yf(date(y, 10, 31))
        pv += (1 - INTERIM_SHARE) * d / (1 + r) ** yf(date(y + 1, 6, 30))
    e32, b31 = terminal_earnings(rows, roe_t)
    d32 = (e32 - G_TERM * b31) * scale / shares1                    # 终值分红率 = 1 - g × B_2031 / E_2032
    timing = INTERIM_SHARE * (1 + r) ** (-304 / 365) + (1 - INTERIM_SHARE) * (1 + r) ** (-547 / 365)
    pv_tv = d32 * timing * (1 + r) / (r - G_TERM) / (1 + r) ** yf(date(2031, 12, 31))
    return pv + pv_tv, pv_tv / (pv + pv_tv), rows


def ri(s, r=0.09):
    """剩余收益（年末折现惯例）：V_2026末 = 末期股息现值 + SCALE×[B_2026 + ΣPV(RI) + PV(终值)]，再除以扩大后股本。"""
    rows = project(s)
    core = B_2026_PRE
    for k, row in enumerate(rows, start=1):
        core += (row['ordnp'] - r * row['b_open']) / (1 + r) ** k
    e32, b31 = terminal_earnings(rows)
    core += (e32 - r * b31) / (r - G_TERM) / (1 + r) ** len(rows)
    v1231 = (FINAL_POOL_2026 / (1 + r) ** 0.5 + SCALE * core) / SHARES1
    return INTERIM_DPS_2026 / (1 + r) ** yf(date(2026, 10, 21)) + v1231 / (1 + r) ** yf(PLACEMENT_DATE)


def pb_roe_single(s, r=0.09):
    """单阶段 P/B-ROE：可持续 ROE 取 (a) 2027-2031 期初权益 ROE 均值、(b) 终值 ROE，P/B = (ROE - g)/(r - g)，乘 2026 年末每股账面（含定增）。"""
    rows = project(s)
    roe_s = sum(row['roe_open'] for row in rows) / len(rows)
    e32, b31 = terminal_earnings(rows)
    out = []
    for roe in (roe_s, e32 / b31):
        pb = (roe - G_TERM) / (r - G_TERM)
        bvps = B_2026_PRE * SCALE / SHARES1
        v = INTERIM_DPS_2026 + (pb * bvps + FINAL_POOL_2026 / SHARES1) / (1 + r) ** yf(PLACEMENT_DATE)
        out.append((v, roe, pb))
    return out, bvps


def weighted(r=0.09):
    return sum(sc['p'] * ddm(sc, r=r)[0] for sc in SCENARIOS.values())


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


def normalized_2026(cc, oth_ratio, nim, tax):
    """2026 正常化归母净利：全年平均生息资产与实际手续费、成本，按正常化的息差、信用成本、其他非息净收入、税率重算。"""
    nii = nim * IEA_AVG_26
    opinc = nii + FY26['fee'] + oth_ratio * IEA_AVG_26
    pbt = opinc - FY26['opex'] - SUR_RATE * opinc - cc * LOANS_AVG_26
    return pbt * (1 - tax) * (1 - MINORITY)


NIM_2026 = FY26['nii'] / IEA_AVG_26                    # 2026 全年净息差（≈1.28%），正常化不改息差
NORMALIZED_2026 = dict(bear=normalized_2026(0.0075, 0.00075, NIM_2026, 0.12),
                       base=normalized_2026(0.0060, 0.00095, NIM_2026, 0.13),
                       bull=normalized_2026(0.0050, 0.00110, NIM_2026, 0.135))


def decomposition():
    """ROE 拆解：各项 / 平均生息资产，× 杠杆（平均生息资产 / 平均普通股权益）= 普通股 ROE。"""
    ord_2024 = 3_969_841 - 324_340                       # 2024 年末归母权益 - 其他权益工具（2025 年报第 14 页；F10）
    out = []
    eq25 = (ord_2024 + ORD_EQ_2025) / 2
    oth25 = FY_25['oth'] - FY_25['othcost']
    out.append(('2025A', FY_25['iea'], FY_25['nii'], FY_25['fee'], oth25, FY_25['opex'] + FY_25['sur'], FY_25['imp'],
                FY_25['tax'], FY_25['parent'] - FY_25['dist'], eq25))
    eqh1 = (ORD_EQ_2025 + ORD_EQ_0630) / 2
    out.append(('2026H1A(年化)', H1_26['iea'], 2 * H1_26['nii'], 2 * H1_26['fee'], 2 * (H1_26['oth'] - H1_26['othcost']),
                2 * (H1_26['opex'] + H1_26['sur']), 2 * H1_26['imp'], 2 * H1_26['tax'],
                2 * (H1_26['parent'] - H1_26['dist']), eqh1))
    eq26 = (ORD_EQ_2025 + B_2026_PRE) / 2
    tax26 = H1_26['tax'] + H2['pbt'] * H2_TAX
    out.append(('2026E', IEA_AVG_26, FY26['nii'], FY26['fee'], FY26['oth_net'], FY26['opex'] + FY26['sur'], FY26['imp'],
                tax26, FY26['ord'], eq26))
    rows = project(SCENARIOS['base'])
    for row in (rows[0], rows[-1]):
        opinc = row['nii'] + row['fee'] + row['oth']
        out.append((f"{row['year']}E 基准", row['iea'], row['nii'], row['fee'], row['oth'], row['opex'] + SUR_RATE * opinc,
                    row['imp'], row['pbt'] * SCENARIOS['base']['tax'], row['ordnp'], (row['b_open'] + row['b']) / 2))
    return out


def incremental_return(s):
    rows = project(s)
    return (rows[-1]['ordnp'] - FY26['ord']) / (rows[-1]['b'] - B_2026_PRE)


def verdict(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def main():
    yi = lambda x: x / 100.0  # 百万元 → 亿元
    bvps0 = ORD_EQ_0630 / SHARES0
    print('=== 工商银行（601398）独立估值  价格日 2026-10-19  A 股 8.60 元（含 0.1511 元中期股息） ===')
    print(f'股本：A {SHARES_A/100:,.2f} + H {SHARES_H/100:,.2f} = {SHARES0/100:,.4f} 亿股；定增 {PLACEMENT_AMT/100:,.0f} 亿元 / '
          f'{PLACEMENT_PRICE:.2f} 元 = {NEW_SHARES/100:,.2f} 亿股 → {SHARES1/100:,.2f} 亿股；放大系数 {SCALE:.4f}')
    print(f'2026-06-30 普通股权益 {yi(ORD_EQ_0630):,.0f} 亿，每股 {bvps0:.3f} 元，P/B（含息）{PRICE/bvps0:.3f}，'
          f'P/B（除息价/扣中期股息后账面）{(PRICE-INTERIM_DPS_2026)/(bvps0-INTERIM_POOL_2026/SHARES0):.3f}')
    print(f'CET1 {CET1_0630/RWA_0630:.2%}（下限 9.0%，G-SIB 第三组自 2027-01-01 起 9.5%）；定增未投放时 +{PLACEMENT_AMT*CET1_TO_BOOK/RWA_0630:.2%}')
    print(f'不良率 {NPL_0630/LOANS_0630:.2%}，覆盖率 {ALLOW_0630/NPL_0630:.2%}，贷款拨备率 {ALLOW_0630/LOANS_0630:.2%}；'
          f'高于 150% 覆盖率部分 {yi(ALLOW_0630-1.5*NPL_0630):,.0f} 亿，高于 2.5% 拨备率部分 {yi(ALLOW_0630-0.025*LOANS_0630):,.0f} 亿（税前，只讨论）')
    print()
    print('--- 2026 报告口径（H1 实际 + H2 预测，亿元） ---')
    print(f"H2：利息净收入 {yi(H2['nii']):,.0f}，手续费 {yi(H2['fee']):,.0f}，其他非息净额 {yi(H2['oth_net']):,.0f}，"
          f"业务及管理费 {yi(H2['opex']):,.0f}，减值 {yi(H2['imp']):,.0f}，税前 {yi(H2['pbt']):,.0f}，归母 {yi(H2['parent']):,.0f}")
    print(f"全年：利息净收入 {yi(FY26['nii']):,.0f}（{FY26['nii']/FY_25['nii']-1:+.1%}），减值 {yi(FY26['imp']):,.0f}"
          f"（/平均贷款 {FY26['imp']/LOANS_AVG_26:.2%}），归母净利 {yi(FY26['parent']):,.0f}（{FY26['parent']/FY_25['parent']-1:+.1%}），"
          f"其他权益工具分配 {yi(FY26['dist']):,.0f}，归属普通股东 {yi(FY26['ord']):,.0f}")
    print(f"2026 股利（分红率 31%）{yi(DIV_2026):,.0f} 亿 = 中期 {yi(INTERIM_POOL_2026):,.0f} + 末期 {yi(FINAL_POOL_2026):,.0f}"
          f"（扩大后股本每股 {FINAL_POOL_2026/SHARES1:.4f} 元）；现有股全年合计 {INTERIM_DPS_2026+FINAL_POOL_2026/SHARES1:.4f} 元，"
          f"按现价股息率 {(INTERIM_DPS_2026+FINAL_POOL_2026/SHARES1)/PRICE:.2%}")
    print(f'2026 年末普通股权益（申报口径）不含定增 {yi(B_2026_PRE):,.0f} 亿，含定增 {yi(B_2026_PRE+PLACEMENT_AMT):,.0f} 亿，'
          f'每股 {(B_2026_PRE+PLACEMENT_AMT)/SHARES1:.3f} 元；2026 ROE（报告口径）{FY26["ord"]/((ORD_EQ_2025+B_2026_PRE)/2):.2%}')
    print()
    print('--- 2026 正常化归母净利（亿元） ---')
    print('  '.join(f'{k} {yi(v):,.0f}' for k, v in NORMALIZED_2026.items()))
    print()
    res = {}
    for name, sc in SCENARIOS.items():
        v, tv_share, rows = ddm(sc)
        v_ri = ri(sc)
        pbs, bvps = pb_roe_single(sc)
        e32, b31 = terminal_earnings(rows)
        res[name] = v
        print(f'--- 情景 {name}（概率 {sc["p"]:.0%}）：{sc["desc"]}')
        print('年份  生息资产 净息差 利息净收入 手续费 减值   税前   归母  普通股东  股利  年末普通股权益 ROE(平均) CET1(定增资本投放后) 成本收入比')
        for row in rows:
            print(f"{row['year']}  {row['iea']/1e6:6.2f}万亿 {row['nim']:.2%} {yi(row['nii']):8,.0f} {yi(row['fee']):6,.0f} {yi(row['imp']):6,.0f} "
                  f"{yi(row['pbt']):6,.0f} {yi(row['parent']):6,.0f} {yi(row['ordnp']):7,.0f} {yi(row['div']):6,.0f} {yi(row['b']):9,.0f} "
                  f"{row['roe']:.2%} {row['cet1']:.2%} {row['ci']:.1%}")
        gr = [rows[0]['ordnp'] / FY26['ord'] - 1] + [rows[i]['ordnp'] / rows[i - 1]['ordnp'] - 1 for i in range(1, 5)]
        print('归属普通股东净利增速 2027-2031：' + ' '.join(f'{g:+.1%}' for g in gr))
        print('每股股利（扩大后股本）2027-2031：' + ' '.join(f"{SCALE*row['div']/SHARES1:.3f}" for row in rows))
        print('期初权益 ROE 2027-2031：' + ' '.join(f"{row['roe_open']:.2%}" for row in rows))
        print(f"终值：2032 年普通股东净利 {yi(e32):,.0f} 亿（2031 × 1.025），终值 ROE = E_2032 / B_2031 = {e32/b31:.2%}，"
              f"终值分红率 {1-G_TERM*b31/e32:.1%}，终值占 DDM 价值 {tv_share:.1%}")
        print(f'DDM V = {v:.2f}；RI V = {v_ri:.2f}（年末折现惯例，差异来自股利时点）')
        print(f'单阶段 P/B-ROE（× 2026 年末每股账面 {bvps:.2f}）：5 年均值 ROE {pbs[0][1]:.2%} → P/B {pbs[0][2]:.3f}、V {pbs[0][0]:.2f}；'
              f'终值 ROE {pbs[1][1]:.2%} → P/B {pbs[1][2]:.3f}、V {pbs[1][0]:.2f}')
        print()
    vw = sum(SCENARIOS[k]['p'] * res[k] for k in SCENARIOS)
    pv = PRICE / vw
    print(f"=== 三情景 V：熊 {res['bear']:.2f} / 基准 {res['base']:.2f} / 牛 {res['bull']:.2f}（25%/50%/25%）；"
          f"加权 V = {vw:.2f} 元；P/V = {pv:.3f} → {verdict(pv)}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f'股权成本敏感性（加权 V）：8% → {v8:.2f}；9% → {vw:.2f}；10% → {v10:.2f}')
    for name, sc in SCENARIOS.items():
        print(f"  {name}: 8% {ddm(sc, r=0.08)[0]:.2f} / 9% {res[name]:.2f} / 10% {ddm(sc, r=0.10)[0]:.2f}")
    irr = solve(lambda r: ddm(SCENARIOS['base'], r=r)[0], 0.07, 0.20, PRICE)
    print(f'现价隐含回报（基准股利流含终值，现值 = 8.60 的折现率）：{irr:.2%}')
    roe_imp = solve(lambda x: ddm(SCENARIOS['base'], roe_t=x)[0], 0.03, 0.15, PRICE)
    bv_ex = (ORD_EQ_0630 - INTERIM_POOL_2026) / SHARES0
    roe_single = G_TERM + (PRICE - INTERIM_DPS_2026) / bv_ex * (0.09 - G_TERM)
    print(f'反向：保留基准 2027-2031 路径，现价隐含终值 ROE（E_2032/B_2031）{roe_imp:.2%}；单阶段（除息价 ÷ 扣中期股息后 6 月末每股账面 {bv_ex:.2f}）'
          f'隐含长期 ROE {roe_single:.2%}（股权成本 9%、永续增速 2.5%）')
    print(f'V 不变时各档价格：≤ {0.75*vw:.2f} 明显低估；{0.75*vw:.2f}～{0.90*vw:.2f} 温和低估；{0.90*vw:.2f}～{1.10*vw:.2f} 大致合理；> {1.10*vw:.2f} 偏贵')
    print()
    print('--- 证伪条件触发后的独立 V（基准情景改动） ---')
    base = SCENARIOS['base']
    f1 = ddm(base, nim_shift=-0.0006)[0]
    f2 = ddm(base, cc_shift=+0.0015)[0]
    f3 = ddm(base, payout=0.25)[0]
    f4 = ddm(base, nim_shift=-0.0006, cc_shift=+0.0015)[0]
    f1r = project(base, nim_shift=-0.0006)
    f2r = project(base, cc_shift=+0.0015)
    f4r = project(base, nim_shift=-0.0006, cc_shift=+0.0015)
    f5 = ddm(base, cc_shift=+0.0010, nim_shift=-0.0002)[0]
    print(f"F1 净息差较基准低 6bp（2027 年 1.20%）：V = {f1:.2f}（2027 ROE {f1r[0]['roe']:.2%}）")
    print(f"F2 信用成本较基准高 15bp（0.75%）：V = {f2:.2f}（2027 ROE {f2r[0]['roe']:.2%}）")
    print(f'F3 分红率降至 25%：V = {f3:.2f}')
    print(f"F1+F2 同时触发：V = {f4:.2f}（2027 ROE {f4r[0]['roe']:.2%}）")
    print(f"F4 2027 年报 ROE < 7.5%（按 F1+F2 路径）：V = {f4:.2f}")
    print(f'F5 三季报预警（信用成本 +10bp、净息差 -2bp）：V = {f5:.2f}')
    print()
    # 定增对每股价值的影响：不定增（SCALE=1、股本不变）对比
    v_nop = {k: ddm(sc, placement=False)[0] for k, sc in SCENARIOS.items()}
    vw_nop = sum(SCENARIOS[k]['p'] * v_nop[k] for k in SCENARIOS)
    print('不计定增的 V：' + ' / '.join(f'{k} {v:.2f}' for k, v in v_nop.items()) + f'；加权 {vw_nop:.2f}（定增影响 {vw-vw_nop:+.2f} 元/股）')
    # TLAC 粗算（不含持有扣减）：总资本 + TLAC 非资本债 1,100 亿 + 存款保险基金可计入部分
    tlac_bonds = 110_000
    tlac = (5_539_090 + tlac_bonds) / RWA_0630
    print(f'TLAC 粗算：资本 + TLAC 债 = {tlac:.2%}；+ 存保 2.5% = {tlac+0.025:.2%}（2025-2027 要求 16%+缓冲 4.0%/4.5%）；'
          f'2028 起 + 存保 3.5% = {tlac+0.035:.2%}（要求 18%+缓冲 4.5% = 22.5%）')
    print()
    print('--- ROE 拆解（占平均生息资产 %；杠杆 = 平均生息资产 / 平均普通股权益） ---')
    print('期间            净息差  手续费  其他非息净额  成本(含税金附加)  减值   所得税  其他权益工具及少数股东  普通股东净利  杠杆   ROE')
    for (lab, iea, nii, fee, oth, cost, imp, tax, ordnp, eq) in decomposition():
        pre = (nii + fee + oth - cost - imp - tax)
        other = pre - ordnp
        print(f'{lab:14s} {nii/iea:6.3%} {fee/iea:6.3%} {oth/iea:8.3%} {-cost/iea:12.3%} {-imp/iea:7.3%} {-tax/iea:7.3%} '
              f'{-other/iea:14.3%} {ordnp/iea:12.3%} {iea/eq:6.2f}x {ordnp/eq:6.2%}')
    for name, sc in SCENARIOS.items():
        print(f"{name}: 再投资率（1 - 分红率）{1-sc['payout']:.0%}，2026→2031 增量回报 ΔE/ΔB = {incremental_return(sc):.2%}")
    print()
    for g in (0.05, 0.06, 0.07, 0.08):
        print(f'RWA 增速 {g:.0%}、ROE 8.5% 时维持 CET1 比率不变的最高分红率 = {1-g/0.085:.1%}')
    # 历史年末 P/B：年末 A 股收盘（f10 tx_month）÷ 年末每股普通股净资产（f10 dividends.BVPS）
    hist = {2014: (4.87, 4.33), 2015: (4.58, 4.80), 2016: (4.41, 5.29), 2017: (6.20, 5.73), 2018: (5.29, 6.30),
            2019: (5.88, 6.93), 2020: (4.99, 7.48), 2021: (4.63, 8.15), 2022: (4.34, 8.81), 2023: (4.78, 9.55),
            2024: (6.92, 10.23), 2025: (7.93, 10.83)}
    print('历史年末 P/B：' + ' '.join(f'{k}:{p/b:.2f}' for k, (p, b) in hist.items()))


if __name__ == '__main__':
    main()
