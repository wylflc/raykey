#!/usr/bin/env python3
"""伊之密（300415）独立估值：OI-291 池内独立审计 b03。

用法：python3 valuation.py
全部输入写在本脚本内（金额单位亿元，每股为元）。同时计算两种口径：
- 共同部分：经营所有者收益 = 无杠杆经营 NOPAT ×（1 − 再投资率），再投资率 = 增速 ÷ 增量回报；
  不含利息、汇兑、联营投资收益与非经常性补助；以 9% 股权成本折现（8%／10% 敏感性），年中折现。
- 无杠杆口径：股权价值 = 经营价值 + 经调整净现金（−21.39 亿，已扣受限资金、经营备付与全部有息负债）+ 非经营资产。
- 有杠杆口径（framework.md「三法互校」第 2 条，经调整净现金为负时为主口径）：有息负债 26.65 亿按现规模滚动、
  不偿还本金；股权价值 = 经营价值 − 有息负债税后利息的现值（利率取实际平均利率，同一折现率）
  + 现金与其他调整项（现金类 − 受限资金 − 经营备付 − 已宣派股利，同无杠杆口径）+ 非经营资产。
- 每股价值用总股本 4.6856 亿股（含回购专户 807.30 万股，用途为股权激励／员工持股，未公告注销）；
  另报剔除回购专户后的对照。
"""

from __future__ import annotations

from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 18.12                     # 2026-10-19 收盘，元/股
SHARES_TOTAL = 4.68562084         # 亿股，2026H1 报告股本 468,562,084 股（含回购专户）
TREASURY = 0.08072978             # 亿股，回购专户 8,072,978 股（2026H1 报告第 46 页）
SHARES_EX_TREASURY = SHARES_TOTAL - TREASURY
VAL_DATE = date(2026, 10, 19)
COE = 0.09

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1 报告第 49–51、86–87、110–115 页）
CASH = 7.39004082                 # 货币资金
STRUCT_DEPOSIT = 1.10             # 交易性金融资产（保本结构性存款）
RESTRICTED = 1.2286269            # 受限货币资金（承兑保证金、大额存单等）
OPER_RESERVE = 2.0                # 经营备付（约 3% 收入；境外子公司受外汇管制现金 1.28 亿）
DEBT = {                          # 有息负债
    'short_loan': 1.57867212,
    'ltloan_current': 5.92841645,
    'long_loan': 18.96670529,
    'lease_liab': 0.11446301 + 0.05856953,
}
DIVIDEND_DECLARED_UNPAID = 0.0    # 2025 年度分红已于 2026-06 实施
NET_CASH_ADJ = CASH + STRUCT_DEPOSIT - RESTRICTED - OPER_RESERVE - sum(DEBT.values()) - DIVIDEND_DECLARED_UNPAID
DEBT_TOTAL = sum(DEBT.values())   # 26.65 亿（2026-06-30）
# 现金与其他调整项（同无杠杆口径，不含有息负债）
FREE_CASH = CASH + STRUCT_DEPOSIT - RESTRICTED - OPER_RESERVE - DIVIDEND_DECLARED_UNPAID

# 有息负债实际平均利率：2026H1 利息支出 32,288,390.19 元（2026H1 报告第 120 页，无资本化利息，第 104 页）
# ÷ 期初期末平均有息负债（2025-12-31 为 20.1972 亿：短借 1.7492 + 长借 15.3314 + 一年内到期 2.9574 + 租赁 0.1592），年化
INTEREST_H1_2026 = 0.3228839019
DEBT_2025YE = 1.7492453398 + 15.3313547581 + 2.9574070205 + 0.1591829329
DEBT_RATE = INTEREST_H1_2026 * 2 / ((DEBT_TOTAL + DEBT_2025YE) / 2)
DEBT_RATE_FY2025 = 0.4903693132 / ((14.62 + DEBT_2025YE) / 2)   # 2025 年利息支出 ÷ 平均有息负债，对照
TAX_INTEREST = 0.15               # 主要借款主体为高新技术企业，利息按 15% 抵税
INTEREST_AFTER_TAX = DEBT_TOTAL * DEBT_RATE * (1 - TAX_INTEREST)
USE_LEVERED = NET_CASH_ADJ < 0    # 规则：经调整净现金为负 → 有杠杆口径为主口径

# 非经营资产（2026H1 报告第 100–101 页长期股权投资；第 101 页其他非流动金融资产）
HAISHENG_BOOK = 4.44800327        # 海晟金融租赁 9% 股权，权益法账面
JIANGGONG_BOOK = 0.92390007       # 江西江工 34%（供应商，账面）
FUNDS_BOOK = 0.05107670 + 0.06    # 零壹基金 + 美智创投


def non_operating(haisheng_pb: float) -> float:
    return HAISHENG_BOOK * haisheng_pb + JIANGGONG_BOOK + FUNDS_BOOK


# ---------------------------------------------------------------- 情景
# margin 拆分：核心 EBIT（毛利−税金−销售−管理−研发）+ 经常性其他收益（软件退税等；加计抵减 2027 年底到期，取一半）
# − 正常化减值；tax 为对经营利润的有效税率。
SCENARIOS = {
    'bear': dict(
        p=0.25, rev_2026=60.0, core_ebit=0.105, other_income=0.013, impairment=0.010, tax=0.16,
        growth=[0.00, 0.03, 0.03, 0.03, 0.03], g_terminal=0.020, roic_incr=0.10, roic_terminal=0.10,
        haisheng_pb=0.55,
        text='国内价格战延续、人民币升值与墨西哥／印度关税压缩外销、一体化压铸订单停滞：正常化收入 60 亿、'
             '核心 EBIT 率 10.5%，2027–2031 增速 0%/3%/3%/3%/3%，增量回报 10%，永续 2%',
    ),
    'base': dict(
        p=0.50, rev_2026=65.0, core_ebit=0.120, other_income=0.015, impairment=0.008, tax=0.16,
        growth=[0.07, 0.07, 0.06, 0.05, 0.04], g_terminal=0.025, roic_incr=0.15, roic_terminal=0.12,
        haisheng_pb=0.70,
        text='行业平台期、公司靠压铸（半固态镁合金）、海外本地化与南浔产能继续拿份额：正常化收入 65 亿、'
             '核心 EBIT 率 12.0%（2019–2025 均值 12.1%），2027–2031 增速 7%/7%/6%/5%/4%，增量回报 15%，永续 2.5%',
    ),
    'bull': dict(
        p=0.25, rev_2026=67.0, core_ebit=0.130, other_income=0.016, impairment=0.007, tax=0.16,
        growth=[0.11, 0.10, 0.09, 0.08, 0.06], g_terminal=0.025, roic_incr=0.18, roic_terminal=0.14,
        haisheng_pb=0.85,
        text='设备更新与新能源汽车轻量化带动新一轮上行、海外收入占比回到 30% 以上：正常化收入 67 亿、'
             '核心 EBIT 率 13.0%，2027–2031 增速 11%/10%/9%/8%/6%，增量回报 18%，永续 2.5%',
    ),
}

YEARS = [2027, 2028, 2029, 2030, 2031]
# 已承诺产能项目（五沙新地块总投资不低于 3.74 亿、南浔一期与总部大楼尾款）使 2027–2028 再投资率不低于下限
RR_FLOOR = {2027: 0.30, 2028: 0.25}
# 2026 下半年存根：估计的无杠杆自由现金流，与情景无关。2024H2、2025H2 实际约 0.3、0.4
#（经营现金流 + 税后利息 − 资本开支），2026H2 按经营现金流约 2.9 + 税后利息约 0.3 − 资本开支约 2.2 ≈ 1.0，取中 0.6
STUB_2026H2 = 0.6

# 正常化归母净利（含净利息与联营收益，剔除汇兑与非经常性补助）所需项
EQUITY_INCOME_2026 = {'bear': 0.45, 'base': 0.55, 'bull': 0.60}   # 海晟金融 ≈0.46 + 江西江工 ≈0.10
NET_INTEREST_AFTER_TAX_2026 = 0.54  # 2026 年利息支出约 0.68、利息收入约 0.05，税后
PARENT_EQUITY = 33.0880383          # 2026-06-30 归母权益（2026H1 报告第 51 页）
HIST_PE_YEAR_END = {2018: 14.9, 2019: 22.0, 2020: 18.6, 2021: 19.3, 2022: 20.5, 2023: 17.3, 2024: 15.5, 2025: 17.2}


def mid_year_t(year: int) -> float:
    return (date(year, 7, 1) - VAL_DATE).days / 365.0


def nopat_2026(s: dict) -> float:
    ebit = s['rev_2026'] * (s['core_ebit'] + s['other_income'] - s['impairment'])
    return ebit * (1 - s['tax'])


def flows(s: dict):
    """返回 NOPAT_2026、[(年份, 增速, NOPAT, 再投资率, 所有者收益)] 与 2026H2 存根。"""
    n0 = nopat_2026(s)
    rows = []
    n = n0
    for y, g in zip(YEARS, s['growth']):
        n = n * (1 + g)
        rr = max(g / s['roic_incr'], RR_FLOOR.get(y, 0.0))
        rows.append((y, g, n, rr, n * (1 - rr)))
    return n0, rows, STUB_2026H2


def operating_value(s: dict, r: float, detail: bool = False):
    n0, rows, stub = flows(s)
    pv = stub
    for y, g, n, rr, oe in rows:
        pv += oe / (1 + r) ** mid_year_t(y)
    n_last = rows[-1][2]
    gT = s['g_terminal']
    oe_T = n_last * (1 + gT) * (1 - gT / s['roic_terminal'])
    tv = oe_T / (r - gT)
    pv_tv = tv / (1 + r) ** mid_year_t(YEARS[-1])
    total = pv + pv_tv
    if detail:
        return dict(n0=n0, rows=rows, stub=stub, pv_explicit=pv, tv=tv, pv_tv=pv_tv,
                    total=total, tv_share=pv_tv / total, oe_T=oe_T)
    return total


def equity_value(s: dict, r: float) -> float:
    return operating_value(s, r) + NET_CASH_ADJ + non_operating(s['haisheng_pb'])


def per_share(s: dict, r: float, shares: float = SHARES_TOTAL) -> float:
    return equity_value(s, r) / shares


def weighted_v(r: float, shares: float = SHARES_TOTAL) -> float:
    return sum(sc['p'] * per_share(sc, r, shares) for sc in SCENARIOS.values())


def pv_interest(r: float) -> float:
    """有息负债按现规模滚动的税后利息现值：2026H2 存根（t = 0，与经营存根一致）+ 2027 年起按年中永续。"""
    t0 = mid_year_t(YEARS[0])
    return 0.5 * INTEREST_AFTER_TAX + INTEREST_AFTER_TAX * (1 + r) / r / (1 + r) ** t0


def equity_value_levered(s: dict, r: float) -> float:
    return operating_value(s, r) - pv_interest(r) + FREE_CASH + non_operating(s['haisheng_pb'])


def per_share_levered(s: dict, r: float, shares: float = SHARES_TOTAL) -> float:
    return equity_value_levered(s, r) / shares


def weighted_v_levered(r: float, shares: float = SHARES_TOTAL) -> float:
    return sum(sc['p'] * per_share_levered(sc, r, shares) for sc in SCENARIOS.values())


def v_primary(s: dict, r: float = 0.09, shares: float = SHARES_TOTAL) -> float:
    return per_share_levered(s, r, shares) if USE_LEVERED else per_share(s, r, shares)


def weighted_primary(r: float = 0.09, shares: float = SHARES_TOTAL) -> float:
    return weighted_v_levered(r, shares) if USE_LEVERED else weighted_v(r, shares)


def bisect(f, lo: float, hi: float, tol: float = 1e-7) -> float:
    flo = f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def implied_irr(s: dict) -> float:
    """无杠杆口径：经营所有者收益流 + 终值 + 经调整净现金 + 非经营资产 = 现价。"""
    target = PRICE * SHARES_TOTAL
    return bisect(lambda r: equity_value(s, r) - target, s['g_terminal'] + 0.005, 0.40)


def implied_irr_levered(s: dict) -> float:
    """有杠杆口径：（经营所有者收益 − 税后利息）流 + 终值 + 现金与其他调整项 + 非经营资产 = 现价。"""
    target = PRICE * SHARES_TOTAL
    return bisect(lambda r: equity_value_levered(s, r) - target, s['g_terminal'] + 0.005, 0.40)


def _operating_target(s: dict, levered: bool) -> float:
    """现价对应的经营价值：无杠杆加回经调整净负债；有杠杆加回税后利息现值、扣现金与其他调整项。"""
    cap = PRICE * SHARES_TOTAL - non_operating(s['haisheng_pb'])
    if levered:
        return cap - FREE_CASH + pv_interest(COE)
    return cap - NET_CASH_ADJ


def reverse_dcf_10y(s: dict, levered: bool = False) -> float:
    """现价隐含的 2027–2036 年 NOPAT 统一增速（再投资率 = g/增量回报 15%，之后 2.5% 永续、终值回报 12%）。"""
    target = _operating_target(s, levered)
    n0 = nopat_2026(s)

    def val(g):
        pv = STUB_2026H2
        n = n0
        for i in range(10):
            n *= (1 + g)
            rr = max(g / s['roic_incr'], RR_FLOOR.get(2027 + i, 0.0))
            pv += n * (1 - rr) / (1 + COE) ** mid_year_t(2027 + i)
        gT = 0.025
        oe_T = n * (1 + gT) * (1 - gT / 0.12)
        pv += oe_T / (COE - gT) / (1 + COE) ** mid_year_t(2036)
        return pv - target

    return bisect(val, -0.10, 0.30)


def reverse_perpetual(s: dict, levered: bool = False) -> float:
    """现价隐含的永续增速：经营价值 = NOPAT_2027 ×（1 − g/12%）/（9% − g）。"""
    target = _operating_target(s, levered)
    n0 = nopat_2026(s)
    return bisect(lambda g: n0 * (1 + g) * (1 - g / 0.12) / (COE - g) - target, -0.05, 0.085)


def pb_roe_crosscheck(np_norm: float, g: float = 0.025, r: float = COE) -> float:
    """对照：P/B =（ROE − g）/（r − g），ROE = 正常化归母净利 ÷ 最新归母权益。"""
    roe = np_norm / PARENT_EQUITY
    return PARENT_EQUITY * (roe - g) / (r - g) / SHARES_TOTAL


def q3_2026_estimate():
    """三季度估计（不进入 V，只用于下次核对）：单季营收、核心 EBIT 率与汇兑假设。"""
    rev = 17.3                    # 2025Q3 15.59；合同负债 2026-06-30 同比 +55%，取 +11%（区间 16.8–17.8）
    core = 0.135                  # 2025Q3 15.7%，2026Q2 12.3%
    other_income, eq_inc, imp, net_int = 0.28, 0.14, -0.10, -0.17
    fx = -0.10                    # 美元兑人民币 6.8109→6.7351（−1.1%），美元净敞口约 0.83 亿美元、欧元约 0.25 亿欧元
    pretax = rev * core + other_income + eq_inc + imp + net_int + fx
    tax = 0.155 * (pretax - eq_inc)
    parent = pretax - tax
    return rev, core, fx, parent, 3.20303153 + parent


def band(pv: float) -> str:
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


FALSIFIER_INPUTS = {
    # F1 竞争：2026 年报核心 EBIT 率 < 11.5%（2025 年 12.8%，2026H1 12.2%）→ 正常化核心 EBIT 率 11.0%
    'F1': dict(core_ebit=0.110),
    # F2 周期：2027 年中报合同负债同比降幅 > 15%（< 7.10 亿）且上半年营收同比下降 → 正常化收入 60 亿、增速 0/3/4/4/3
    'F2': dict(rev_2026=60.0, growth=[0.00, 0.03, 0.04, 0.04, 0.03]),
    # F3 海外：2026 年外销收入 < 17.2 亿（同比 −5%，2025 年 18.08 亿）→ 增速各年 −2 个百分点、增量回报 12%
    'F3': dict(growth=[g - 0.02 for g in SCENARIOS['base']['growth']], roic_incr=0.12),
    # F4 资本配置：2027 年中报有息负债 > 32 亿且 TTM 经营现金流 < 3 亿 → 增量回报 11%、终值回报 10%
    'F4': dict(roic_incr=0.11, roic_terminal=0.10),
    # F5 上行：2026 年报核心 EBIT 率 ≥ 13.0% 且外销收入 ≥ 19.9 亿（+10%）→ 核心 EBIT 13%、增速 9/8/7/6/5、增量回报 16%
    'F5_up': dict(core_ebit=0.130, growth=[0.09, 0.08, 0.07, 0.06, 0.05], roic_incr=0.16),
    # 陷阱检查门槛（不列入证伪）：1 年以上账龄应收占比 > 20% 或减值合计 > 营收 1.5% → 减值率 1.5%
    'T_credit': dict(impairment=0.015),
}


def falsifier_values(levered: bool = USE_LEVERED):
    """证伪条件触发后的独立 V（元/股，9%）：在基准情景上改关键输入，其余不变。"""
    base = SCENARIOS['base']
    f = per_share_levered if levered else per_share
    return {k: f(dict(base, **mod), COE) for k, mod in FALSIFIER_INPUTS.items()}


def bands(vw: float) -> str:
    return (f'≤{0.75*vw:.2f} 明显低估；{0.75*vw:.2f}–{0.90*vw:.2f} 温和低估；'
            f'{0.90*vw:.2f}–{1.10*vw:.2f} 大致合理；>{1.10*vw:.2f} 偏贵')


def main():
    print('=== 伊之密（300415）独立估值，价格日 2026-10-19 ===')
    print(f'现价 {PRICE:.2f} 元；总股本 {SHARES_TOTAL:.4f} 亿股（含回购专户 {TREASURY:.4f}）；市值 {PRICE*SHARES_TOTAL:.2f} 亿')
    print(f'经调整净现金（无杠杆口径）= {CASH:.2f}+{STRUCT_DEPOSIT:.2f}−{RESTRICTED:.2f}−{OPER_RESERVE:.2f}−{DEBT_TOTAL:.2f} = {NET_CASH_ADJ:.2f} 亿')
    print(f'主口径：{"有杠杆" if USE_LEVERED else "无杠杆"}（经调整净现金 {"< 0" if USE_LEVERED else "≥ 0"}）')
    print(f'有杠杆口径：有息负债 {DEBT_TOTAL:.2f} 亿，实际平均利率 {DEBT_RATE*100:.2f}%'
          f'（2026H1 利息 {INTEREST_H1_2026:.4f} 亿×2 ÷ 平均有息负债 {(DEBT_TOTAL+DEBT_2025YE)/2:.2f} 亿；2025 年对照 {DEBT_RATE_FY2025*100:.2f}%），'
          f'税后利息 {INTEREST_AFTER_TAX:.4f} 亿/年，现值（9%）{pv_interest(COE):.2f} 亿；现金与其他调整项 {FREE_CASH:.2f} 亿')
    for k, sc in SCENARIOS.items():
        print(f'非经营资产（{k}，海晟 {sc["haisheng_pb"]:.2f}×账面）= {non_operating(sc["haisheng_pb"]):.2f} 亿')
    print()
    for k, sc in SCENARIOS.items():
        det = operating_value(sc, COE, detail=True)
        m = sc['core_ebit'] + sc['other_income'] - sc['impairment']
        print(f'--- {k}（p={sc["p"]:.2f}）---')
        print(f'  正常化 2026：收入 {sc["rev_2026"]:.1f}，经营利润率 {m*100:.1f}%，EBIT {sc["rev_2026"]*m:.2f}，NOPAT {det["n0"]:.2f}')
        print(f'  2026H2 存根所有者收益 {det["stub"]:.2f}')
        for y, g, n, rr, oe in det['rows']:
            print(f'  {y}: 增速 {g*100:4.1f}%  NOPAT {n:6.2f}  再投资率 {rr*100:5.1f}%  所有者收益 {oe:6.2f}')
        print(f'  终值：OE_2032 {det["oe_T"]:.2f}，TV {det["tv"]:.2f}，PV(TV) {det["pv_tv"]:.2f}，显性期 PV {det["pv_explicit"]:.2f}，终值占比 {det["tv_share"]*100:.1f}%')
        print(f'  经营价值 {det["total"]:.2f}')
        print(f'  [有杠杆] 股权价值 {equity_value_levered(sc, COE):.2f} 亿 = {det["total"]:.2f} − 利息现值 {pv_interest(COE):.2f}'
              f' + 现金调整 {FREE_CASH:.2f} + 非经营 {non_operating(sc["haisheng_pb"]):.2f}；每股 V {per_share_levered(sc, COE):.2f} 元'
              f'（剔除回购专户 {per_share_levered(sc, COE, SHARES_EX_TREASURY):.2f}）；8% {per_share_levered(sc, 0.08):.2f}；'
              f'10% {per_share_levered(sc, 0.10):.2f}；隐含回报 {implied_irr_levered(sc)*100:.2f}%')
        print(f'  [无杠杆] 股权价值 {equity_value(sc, COE):.2f} 亿；每股 V {per_share(sc, COE):.2f} 元'
              f'（剔除回购专户 {per_share(sc, COE, SHARES_EX_TREASURY):.2f}）；8% {per_share(sc, 0.08):.2f}；'
              f'10% {per_share(sc, 0.10):.2f}；隐含回报 {implied_irr(sc)*100:.2f}%')
    print()
    base = SCENARIOS['base']
    for label, lev in (('有杠杆', True), ('无杠杆', False)):
        wv = weighted_v_levered if lev else weighted_v
        vw = wv(COE)
        pv = PRICE / vw
        irr = implied_irr_levered(base) if lev else implied_irr(base)
        tag = '（主口径）' if lev == USE_LEVERED else '（对照）'
        print(f'[{label}{tag}] 加权 V（9%）= {vw:.2f} 元；P/V = {pv:.3f}（{band(pv)}）；'
              f'剔除回购专户 V = {wv(COE, SHARES_EX_TREASURY):.2f}、P/V = {PRICE/wv(COE, SHARES_EX_TREASURY):.3f}')
        print(f'    加权 V（8%）= {wv(0.08):.2f}；加权 V（10%）= {wv(0.10):.2f}；基准隐含回报 = {irr*100:.2f}%')
        print(f'    反向 DCF：现价隐含 2027–2036 NOPAT 年增速 {reverse_dcf_10y(base, lev)*100:.2f}%（之后 2.5%）；'
              f'隐含永续增速 {reverse_perpetual(base, lev)*100:.2f}%')
        print(f'    V 不变时各档价格：{bands(vw)}')
    print()
    print('正常化 2026 归母净利（含净利息与联营收益）：')
    for k, sc in SCENARIOS.items():
        npn = nopat_2026(sc) + EQUITY_INCOME_2026[k] - NET_INTEREST_AFTER_TAX_2026
        print(f'  {k}: NOPAT {nopat_2026(sc):.2f} + 联营 {EQUITY_INCOME_2026[k]:.2f} − 税后净利息 {NET_INTEREST_AFTER_TAX_2026:.2f} = {npn:.2f} 亿')
    print()
    print('敏感性（主口径，9%）：')
    vs = {k: v_primary(sc) for k, sc in SCENARIOS.items()}
    print(f'  概率 30/50/20 → {0.3*vs["bear"]+0.5*vs["base"]+0.2*vs["bull"]:.2f}；20/50/30 → {0.2*vs["bear"]+0.5*vs["base"]+0.3*vs["bull"]:.2f}')
    print(f'  基准收入 67.5 亿 → {v_primary(dict(base, rev_2026=67.5)):.2f}；基准永续 2% → {v_primary(dict(base, g_terminal=0.02)):.2f}')
    print(f'  不扣经营备付 → 每股 +{OPER_RESERVE/SHARES_TOTAL:.2f}')
    print()
    print('交叉验证：')
    np_base = nopat_2026(base) + EQUITY_INCOME_2026['base'] - NET_INTEREST_AFTER_TAX_2026
    print(f'  现价 / 基准正常化归母净利 = {PRICE*SHARES_TOTAL/np_base:.1f}×；V_base（主口径）/ 正常化归母净利 = {v_primary(base)*SHARES_TOTAL/np_base:.1f}×')
    ev = PRICE * SHARES_TOTAL - NET_CASH_ADJ - non_operating(base['haisheng_pb'])
    ebit_base = base['rev_2026'] * (base['core_ebit'] + base['other_income'] - base['impairment'])
    print(f'  现价 EV（扣非经营资产）= {ev:.2f} 亿；EV / 正常化 EBIT = {ev/ebit_base:.1f}×；EV / TTM EBIT（剔汇兑 8.55）= {ev/8.55:.1f}×')
    print(f'  股息率 {0.60/PRICE*100:.2f}%（2025 年度 0.60 元/股）')
    pes = sorted(HIST_PE_YEAR_END.values())
    med = (pes[3] + pes[4]) / 2
    print(f'  历史年末 PE 2018–2025：{min(pes):.1f}–{max(pes):.1f}×，中位 {med:.1f}×；'
          f'按 {min(pes):.1f}× 正常化归母净利 → {min(pes)*np_base/SHARES_TOTAL:.2f} 元；按 12× → {12*np_base/SHARES_TOTAL:.2f} 元')
    print(f'  P/B-ROE（ROE {np_base/PARENT_EQUITY*100:.1f}%，g 2.5%）→ {pb_roe_crosscheck(np_base):.2f} 元；'
          f'现价 PB {PRICE*SHARES_TOTAL/PARENT_EQUITY:.2f}×')
    rev, core, fx, q3, m9 = q3_2026_estimate()
    print(f'  2026Q3 估计：营收 {rev:.1f} 亿、核心 EBIT 率 {core*100:.1f}%、汇兑 {fx:.2f} → 归母净利约 {q3:.2f} 亿'
          f'（2025Q3 2.20），前三季度约 {m9:.2f} 亿（2025 年同期 5.64）')
    print()
    for label, lev in (('有杠杆', True), ('无杠杆', False)):
        tag = '主口径' if lev == USE_LEVERED else '对照'
        print(f'证伪触发后的独立 V（{label}，{tag}，基准情景改输入，9%）：')
        for k, val in falsifier_values(lev).items():
            print(f'  {k}: {val:.2f} 元（P/V {PRICE/val:.2f}）')


if __name__ == '__main__':
    main()
