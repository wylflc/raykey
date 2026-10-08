#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""晶泰控股（02228.HK）独立估值：分部加总（SOTP）。

口径：价格日 2026-10-08（港股收盘）；资产负债表截至 2026-06-30；
金额默认人民币百万元（RMB m），每股价值以港元计；折现率 10%（名义），
敏感性 9%/11%/12%；平台终值增长 ≤ 2.5%。
只用标准库，不联网、不读文件。运行：python3 xtalpi_valuation.py
出处标注为港交所披露易文件编号（https://www1.hkexnews.hk/listedco/listconews/sehk/年/月日/编号.pdf）。
“假设”“推断”字样表示公司未披露、由本脚本设定或由报表勾稽得到。
"""

# ---------------------------------------------------------------- 1. 快照
PRICE_HKD = 7.14                    # 2026-10-08 收盘（统一快照）
SHARES_BASIC = 4_301_176_179        # 2026-09-30 月报表 2026100601423：已发行股份（不含 29.9 万库存股）
PENDING_CANCEL = 981_000 + 1_897_000 + 2_004_000  # 已回购待注销（2026100502035），未从股数中扣除（保守）
USD_HKD, USD_CNY = 7.8484, 6.7046   # ECB 2026-10-07
CNY_HKD = USD_HKD / USD_CNY         # 1.1706
VAL_FRAC = 280 / 365                # 估值日 2026-10-08 在当年已过比例

# 摊薄工具（2026-09-30 月报表；授予公告 2026040902220 / 2026070203757 / 2026092301885）
RSU_OUT = 11_746_712 + 9_134_712    # 首次公开发售后 RSU + 2026 计划 RSU（视同全部摊薄）
OPTIONS = [(10_505_590, 9.61),      # 首次公开发售后购股权，行使价 HK$9.61
           (34_980_210, 7.48),      # 2026 计划，授予四名执行董事，HK$7.48
           (668_920, 8.385)]        # 2026 计划，HK$8.385
PRE_IPO_OPTIONS = 217_188_943       # 首发前 ESOP：对应股份已发行并含在 SHARES_BASIC 内；行使价约 US$0.0008–0.263，行权款不计（保守）
CB_FACE_HKD = 2_866.0               # 零息可转债面值 HK$m（2026010800041 / 2026012800647）
CB_REDEEM_PCT = 1.0176              # 2027-01-26 到期按 101.76% 赎回（中期报告附注 21）
CB_CONV_PRICE = 13.85
CB_CONV_SHARES = 206_931_407

# ---------------------------------------------------------------- 2. 资产负债表（2026-06-30，中期报告 2026090901145）
CASH = 2_622.881
BANK_DEPOSITS = 3_845.317
RESTRICTED = 5.022                  # 受限资金：不计入
WMP_NOTES = 944.554                 # 结构性票据（含复星 Hani 票据类产品），当期 FVTPL
WMP_MONEY = 1_253.406               # 货币基金，当期 FVTPL
LISTED = 891.370                    # 上市股权（第一层级；含 2026-05 上市的剂泰科技 7666.HK，转入时 2.421 亿）
PE_FUNDS = 877.692                  # 私募股权基金（第三层级）
UNLISTED = 645.181                  # 非上市股权（第三层级，倒推法估值）
CONV_DEBTS = 107.344                # 可转换债务投资（第三层级）
EQUITY_METHOD = 158.826             # 联营及合营（79.6 + 79.2）
BANK_DEBT = 270.5 + 24.9 + 234.7    # 银行借款合计 530.1
LEASES = 90.436 + 37.620            # 租赁负债
NCI = 72.256                        # 少数股东权益（账面）
CB_FACE_RMB = CB_FACE_HKD / CNY_HKD

# ---------------------------------------------------------------- 3. 历史口径（年报 2025040702143 / 2026041701551，业绩公告 2026032501035 / 2026081900919）
HIST = {  # 收入：总额、AI4S 智能化解决方案、药物发现、其中 DoveTree（客户 A）
    "2023": dict(rev=174.420, ai4s=86.692, dds=87.728, dovetree=0.0),
    "2024": dict(rev=266.433, ai4s=162.771, dds=103.662, dovetree=0.0),
    "2025": dict(rev=802.623, ai4s=264.690, dds=537.933, dovetree=365.089),
    "2025H1": dict(rev=517.076, ai4s=81.864, dds=435.212, dovetree=365.089),
    "2026H1": dict(rev=393.627, ai4s=193.518, dds=200.109, dovetree=129.407),
}
COSTS = {  # 营业成本、管理、研发、销售、金融资产减值、其他收入、FVTPL 公允价值变动、股权激励
    "2024": dict(cogs=143.007, ga=417.883, rd=418.238, sm=70.992, imp=1.228, oi=65.914, fv=25.278, sbc=136.678),
    "2025": dict(cogs=243.445, ga=409.894, rd=569.185, sm=81.166, imp=8.627, oi=50.894, fv=514.560, sbc=123.581),
    "2025H1": dict(cogs=81.959, ga=200.333, rd=221.527, sm=40.354, imp=8.523, oi=30.646, fv=34.438, sbc=66.019),
    "2026H1": dict(cogs=167.834, ga=212.142, rd=367.838, sm=48.000, imp=1.061, oi=13.335, fv=154.242, sbc=66.473),
}
NET_PROFIT = {"2024": -1514.869, "2025": 134.579, "2025H1": 75.609, "2026H1": -224.944}
CASHFLOW = {  # 经营现金流、购置物业设备+无形资产
    "2024": dict(ocf=-478.681, capex=58.108 + 3.759),
    "2025": dict(ocf=-165.411, capex=67.648 + 10.091),
    "2025H1": dict(ocf=-238.479, capex=31.686 + 5.162),
    "2026H1": dict(ocf=-399.238, capex=49.787 + 18.659),
}
REV_2025_RECURRING = HIST["2025"]["rev"] - HIST["2025"]["dovetree"]       # 437.5
REV_2026H1_RECURRING = HIST["2026H1"]["rev"] - HIST["2026H1"]["dovetree"]  # 264.2

# ---------------------------------------------------------------- 4. 情景假设（均为本脚本假设）
TAX = 0.15                      # 高新技术企业税率
CAPEX_PCT = {y: (0.02 if y <= 2030 else 0.015) for y in range(2026, 2036)}  # 净资本开支（资本开支 − 折旧）占收入
YEARS = list(range(2027, 2036))

SCEN = {
    "熊": dict(
        prob=0.30, r26h2=324.0, g=0.020,
        growth=[.22, .16, .12, .10, .08, .06, .05, .04, .03],
        margin=[-.04, -.02, .01, .03, .05, .06, .07, .08, .08, .08],   # 2026H2, 2027..2035
        unalloc=[520, 1060, 1000, 860, 720, 600, 500, 400, 320, 250], u_term=0.08,
        bd=[0, 80, 100, 100, 100, 100, 100, 100, 100, 100],
        ronic=0.10, nwc=0.18,
        keep=dict(notes=.95, listed=.70, pe=.55, unlisted=.40, cd=.50, eqm=.50),
        dt_near_prob=0.0, dt_cp=0.4, dt_other=1, lilly_near_prob=0.3, partner_cp=0.6),
    "基准": dict(
        prob=0.50, r26h2=390.0, g=0.025,
        growth=[.45, .35, .28, .22, .17, .13, .10, .07, .05],
        margin=[.00, .03, .06, .09, .11, .13, .14, .15, .15, .15],
        unalloc=[520, 1040, 1000, 940, 870, 790, 710, 620, 530, 450], u_term=0.12,
        bd=[30, 200, 250, 280, 300, 310, 320, 330, 340, 350],
        ronic=0.15, nwc=0.15,
        keep=dict(notes=.98, listed=.85, pe=.70, unlisted=.60, cd=.70, eqm=.70),
        dt_near_prob=0.5, dt_cp=0.7, dt_other=3, lilly_near_prob=0.6, partner_cp=0.8),
    "牛": dict(
        prob=0.20, r26h2=442.0, g=0.025,
        growth=[.60, .50, .40, .35, .30, .25, .20, .15, .10],
        margin=[.03, .08, .12, .16, .19, .21, .23, .25, .25, .25],
        unalloc=[530, 1120, 1180, 1200, 1180, 1120, 1040, 940, 820, 700], u_term=0.10,
        bd=[60, 400, 500, 600, 650, 680, 710, 740, 770, 800],
        ronic=0.20, nwc=0.12,
        keep=dict(notes=1.0, listed=1.0, pe=.90, unlisted=.85, cd=.90, eqm=1.0),
        dt_near_prob=1.0, dt_cp=1.0, dt_other=5, lilly_near_prob=0.9, partner_cp=1.0),
}

# 成功率：BIO/Informa/QLS《Clinical Development Success Rates 2011–2020》（2021）
P_ALL = dict(p1p2=0.520, p2p3=0.289, p3nda=0.578, ndaap=0.906)   # 全部适应症
P_ONC = dict(p1p2=0.488, p2p3=0.246, p3nda=0.477, ndaap=0.920)   # 肿瘤
P_PRE = 0.69          # 临床前→I 期（Paul et al. 2010, Nat Rev Drug Discov 9:203）
P_DISC = 0.75 * 0.85  # 苗头→先导（75%）×先导优化（85%），同上
RAMP = [0.10, 0.30, 0.55, 0.80, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.7, 0.5]  # 上市后销售爬坡（假设）


def t_mid(year):
    """年度现金流取年中，距估值日的年数；2026H2 取 0。"""
    return 0.0 if year == 2026 else year - 2026 + 0.5 - VAL_FRAC


def df(year, r):
    return (1.0 + r) ** (-t_mid(year))


# ---------------------------------------------------------------- 5. 已签约交易与合作临床资产 rNPV（美元百万 → 人民币）
def program_rnpv(chain, miles, r, royalty=0.0, peak=0.0, launch=None, commercial=(), start_prob=1.0, cp=1.0, shift=0):
    """chain: [(事件, 年份, 到达该事件的转换概率)]；miles: {事件: 美元百万}；返回人民币百万 PV。"""
    pv, cum = 0.0, start_prob
    for ev, yr, p in chain:
        cum *= p
        if ev in miles:
            pv += miles[ev] * cum * cp * df(yr + shift, r)
    if launch is not None and peak > 0:
        paid = set()
        for k, f in enumerate(RAMP):
            yr = launch + k + shift
            sales = peak * f
            pv += royalty * sales * cum * cp * df(yr, r)
            for thr, amt in commercial:
                if sales >= thr and thr not in paid:
                    paid.add(thr)
                    pv += amt * cum * cp * df(yr, r)
    return pv * USD_CNY


def chain_from(stage_probs, years, events=("p2", "p3", "nda", "appr")):
    keys = {"p2": "p1p2", "p3": "p2p3", "nda": "p3nda", "appr": "ndaap"}
    return [(e, y, stage_probs[keys[e]]) for e, y in zip(events, years)]


def signed_deals(s, r):
    out = {}
    # DoveTree：剩余约 3,000 万美元（4,900 万 − 已收 1,900 万，是否仍应付未查到）+ 里程碑/分成
    out["DoveTree 剩余近期款"] = 30.0 * s["dt_near_prob"] * df(2027, r) * USD_CNY
    lead_chain = [("p1", 2028, P_PRE)] + chain_from(P_ONC, [2030, 2032, 2034, 2035])
    lead_miles = {"p1": 10, "p2": 20, "p3": 40, "nda": 30, "appr": 77}  # 假设：58.9 亿美元按 10 个项目均摊，开发/注册占 30%
    lead = program_rnpv(lead_chain, lead_miles, r, royalty=0.05, peak=800, launch=2035,
                        commercial=[(500, 100)], cp=s["dt_cp"])
    other = s["dt_other"] * program_rnpv(lead_chain, lead_miles, r, royalty=0.05, peak=800, launch=2035,
                                         commercial=[(500, 100)], start_prob=P_DISC, cp=s["dt_cp"], shift=1)
    out["DoveTree 首个肿瘤资产"] = lead
    out["DoveTree 其他项目"] = other
    # 礼来（Ailux 双抗平台，总额 3.45 亿美元，首付+近期里程碑“数千万美元”，2025110501768）
    disc_chain = [("ind", 2028, P_DISC), ("p1", 2029, P_PRE)] + chain_from(P_ALL, [2031, 2033, 2035, 2036])
    lilly = 15.0 * s["lilly_near_prob"] * df(2027, r) * USD_CNY
    lilly += program_rnpv(disc_chain, {"p1": 20, "p2": 40, "p3": 60, "appr": 180}, r)
    out["礼来双抗平台"] = lilly
    # GPCR 合作（总额 > 4 亿美元，首付未披露，2026060901622）
    out["GPCR 合作"] = program_rnpv(disc_chain, {"ind": 5, "p1": 10, "p2": 20, "p3": 40, "appr": 100}, r,
                                    royalty=0.03, peak=1000, launch=2036, commercial=[(500, 150)])
    # 合作方临床期资产：晶泰经济权益未披露，假设剩余里程碑 1,500 万美元/个 + 1% 分成（推断）
    cp = s["partner_cp"]
    m = {"p2": 5, "p3": 5, "appr": 5}
    pep08 = program_rnpv(chain_from(P_ONC, [2027, 2029, 2031, 2032]), m, r, royalty=0.01, peak=500, launch=2032, cp=cp)
    sig1094 = program_rnpv(chain_from(P_ONC, [2027, 2029, 2031, 2032]), m, r, royalty=0.01, peak=300, launch=2032, cp=cp)
    rtx117 = program_rnpv(chain_from(P_ALL, [2027, 2029, 2031, 2032]), m, r, royalty=0.01, peak=300, launch=2032, cp=cp)
    sig2649 = program_rnpv([("p1", 2027, 0.9)] + chain_from(P_ONC, [2028, 2030, 2032, 2033]), m, r,
                           royalty=0.01, peak=500, launch=2033, cp=cp)
    out["PEP08（智擎，PRMT5，I 期）"] = pep08
    out["SIGX1094（Signet，FAK/SRC，I 期）"] = sig1094
    out["RTX-117（ReviR，eIF2B，I 期）"] = rtx117
    out["SIGX2649（Signet，TEAD，IND 获批）"] = sig2649
    return out


# ---------------------------------------------------------------- 6. 平台/服务 DCF、BD 流、未分摊费用
def revenue_path(s, scale=1.0):
    r26 = REV_2026H1_RECURRING + s["r26h2"]
    rev = {2026: r26}
    prev = r26
    for y, gth in zip(YEARS, s["growth"]):
        prev = prev * (1 + gth)
        rev[y] = prev * scale
    rev[2036] = rev[2035] * (1 + s["g"])
    return rev


def operating(s, r, scale=1.0, detail=False):
    rev = revenue_path(s, scale)
    g = s["g"]
    seg_pv = bd_pv = u_pv = tax_pv = 0.0
    rows = []
    periods = [2026] + YEARS
    for i, y in enumerate(periods):
        m, u, bd = s["margin"][i], s["unalloc"][i], s["bd"][i]
        if y == 2026:
            r_p = s["r26h2"]
            reinv = s["nwc"] * (rev[2026] - REV_2025_RECURRING) / 2 + CAPEX_PCT[2026] * r_p
        else:
            r_p = rev[y]
            reinv = s["nwc"] * (rev[y] - rev[y - 1]) + CAPEX_PCT[y] * r_p
        ebit = m * r_p
        cons = ebit + bd - u
        tax = TAX * max(0.0, cons)
        d = df(y, r)
        seg_pv += (ebit - reinv) * d
        bd_pv += bd * d
        u_pv -= u * d
        tax_pv -= tax * d
        rows.append((("2026H2" if y == 2026 else str(y)), r_p, ebit, bd, u, cons, ebit - reinv + bd - u - tax))
    # 终值（2036 年起，Gordon，年中现金流 → 2035 年中折现）
    rT = rev[2036]
    # 终值期未分摊费用 = 情景比例 × 未放大的 2036 年收入（半固定费用：放大收入时不随之放大）
    u_abs = s.get("u_term_abs")
    u_T_pre = u_abs if u_abs is not None else s["u_term"] * revenue_path(s, 1.0)[2036]
    seg_fcf_T = s["margin"][-1] * rT * (1 - TAX) * (1 - g / s["ronic"])
    bd_T = s["bd"][-1] * (1 + g) * (1 - TAX)
    u_T = u_T_pre * (1 - TAX)
    k = df(2035, r) / (r - g)
    seg_tv, bd_tv, u_tv = seg_fcf_T * k, bd_T * k, -u_T * k
    cons_T = s["margin"][-1] * rT + s["bd"][-1] * (1 + g) - u_T_pre
    res = dict(seg=seg_pv + seg_tv, seg_tv=seg_tv, bd=bd_pv + bd_tv, bd_tv=bd_tv, unalloc=u_pv + u_tv,
               u_tv=u_tv, tax=tax_pv, cons_T=cons_T, rev=rev, rows=rows)
    return res


def net_financial(s):
    k = s["keep"]
    cash_core = CASH + BANK_DEPOSITS + WMP_MONEY + WMP_NOTES * k["notes"] - BANK_DEBT - CB_FACE_RMB - LEASES
    inv = (LISTED * k["listed"] + PE_FUNDS * k["pe"] + UNLISTED * k["unlisted"]
           + CONV_DEBTS * k["cd"] + EQUITY_METHOD * k["eqm"])
    return dict(cash_core=cash_core, inv=inv, nci=-NCI, total=cash_core + inv - NCI)


def per_share(equity_rmb):
    """权益（人民币百万）→ 每股港元；RSU 全额摊薄，期权按库存股法；V > 转股价时视同转股。"""
    eq_hkd = equity_rmb * CNY_HKD
    v = eq_hkd * 1e6 / (SHARES_BASIC + RSU_OUT)
    for _ in range(50):
        opt = sum(n * max(0.0, v - kx) / v for n, kx in OPTIONS) if v > 0 else 0.0
        shares = SHARES_BASIC + RSU_OUT + opt
        v_new = eq_hkd * 1e6 / shares
        if abs(v_new - v) < 1e-9:
            break
        v = v_new
    if v > CB_CONV_PRICE:  # 转股：加回面值、加股数
        eq2 = eq_hkd + CB_FACE_HKD
        v = eq2 * 1e6 / (SHARES_BASIC + RSU_OUT + CB_CONV_SHARES)
    return v


def value(name, r, scale=1.0, override=None):
    s = dict(SCEN[name])
    if override:
        s.update(override)
    op = operating(s, r, scale)
    deals = signed_deals(s, r)
    deals_total = sum(deals.values())
    nf = net_financial(s)
    op_total = op["seg"] + op["bd"] + op["unalloc"] + op["tax"] + deals_total
    equity = op_total + nf["total"]
    return dict(op=op, deals=deals, deals_total=deals_total, nf=nf, op_total=op_total,
                equity=equity, v=per_share(equity))


def weighted(r):
    return sum(SCEN[n]["prob"] * value(n, r)["v"] for n in SCEN)


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def solve(f, lo, hi, target, it=200):
    flo, fhi = f(lo) - target, f(hi) - target
    if flo * fhi > 0:
        return None
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


# ---------------------------------------------------------------- 7. 输出
def fmt(x, nd=1):
    return f"{x:,.{nd}f}"


def main():
    print("=" * 78)
    print("晶泰控股 02228.HK 独立估值（分部加总）  价格日 2026-10-08  单位：人民币百万元，除注明")
    print("=" * 78)
    mcap_hkd = PRICE_HKD * SHARES_BASIC / 1e6
    print(f"现价 HK${PRICE_HKD}；股数 {SHARES_BASIC:,}（待注销回购 {PENDING_CANCEL:,} 未扣）；"
          f"市值 HK${fmt(mcap_hkd)}m = RMB {fmt(mcap_hkd / CNY_HKD)}m；CNY/HKD {CNY_HKD:.4f}")

    print("\n[1] 收入结构（可重复 = 总收入 − DoveTree；药物发现内其他授权/里程碑未单列，按上限看待）")
    for k in ["2023", "2024", "2025", "2025H1", "2026H1"]:
        h = HIST[k]
        rec = h["rev"] - h["dovetree"]
        print(f"  {k:7s} 总 {fmt(h['rev']):>7s}  AI4S {fmt(h['ai4s']):>6s}  药物发现 {fmt(h['dds']):>6s}"
              f"（DoveTree {fmt(h['dovetree'])}）  可重复 {fmt(rec)}  一次性占比 {h['dovetree'] / h['rev']:.1%}")
    h25h2 = {x: HIST["2025"][x] - HIST["2025H1"][x] for x in ("rev", "ai4s", "dds", "dovetree")}
    print(f"  2025H2  总 {fmt(h25h2['rev'])}  AI4S {fmt(h25h2['ai4s'])}  药物发现 {fmt(h25h2['dds'])}（推断）")

    print("\n[2] 核心经营亏损（不含 DoveTree、不含 FVTPL 公允价值变动，含股权激励）与利润拆解")
    for k in ["2024", "2025", "2025H1", "2026H1"]:
        c, h = COSTS[k], HIST[k]
        core = (h["rev"] - h["dovetree"]) - c["cogs"] - c["ga"] - c["rd"] - c["sm"] - c["imp"] + c["oi"]
        print(f"  {k:7s} 核心经营亏损 {fmt(core):>8s}  DoveTree {fmt(h['dovetree']):>6s}  FVTPL 收益 {fmt(c['fv']):>6s}"
              f"  股权激励 {fmt(c['sbc']):>6s}  报表净利 {fmt(NET_PROFIT[k]):>8s}")
    print("  2025 年 FVTPL 收益 514.6 中：第三层级 251.4（非上市 118.8、理财 98.3、基金 29.0、可转债 5.2），"
          "上市股权约 263.2（推断：总额减第三层级）")
    c25, c25h1 = COSTS["2025"], COSTS["2025H1"]
    core = lambda k: ((HIST[k]["rev"] - HIST[k]["dovetree"]) - COSTS[k]["cogs"] - COSTS[k]["ga"] - COSTS[k]["rd"]
                      - COSTS[k]["sm"] - COSTS[k]["imp"] + COSTS[k]["oi"])
    print(f"  2025H2 核心经营亏损 {fmt(core('2025') - core('2025H1'))}（推断：全年减上半年）；"
          f"2026H1 同比 {core('2026H1') / core('2025H1') - 1:+.1%}；可重复收入 2026H1 同比 "
          f"{REV_2026H1_RECURRING / (HIST['2025H1']['rev'] - HIST['2025H1']['dovetree']) - 1:+.1%}")
    gm = {k: 1 - COSTS[k]["cogs"] / (HIST[k]["rev"] - HIST[k]["dovetree"]) for k in ("2024", "2025", "2026H1")}
    print("  毛利率（剔除 DoveTree，成本全归可重复收入，推断）：" + "；".join(f"{k} {v:.1%}" for k, v in gm.items()))

    print("\n[3] 现金消耗与跑道")
    for k in ["2024", "2025", "2026H1"]:
        cf = CASHFLOW[k]
        burn = cf["ocf"] - cf["capex"]
        print(f"  {k:7s} 经营现金流 {fmt(cf['ocf']):>8s}  资本开支 {fmt(cf['capex']):>6s}  消耗 {fmt(burn):>8s}"
              f"  剔除 DoveTree 收款 {fmt(burn - HIST[k]['dovetree']):>8s}")
    ttm_ocf = CASHFLOW["2025"]["ocf"] - CASHFLOW["2025H1"]["ocf"] + CASHFLOW["2026H1"]["ocf"]
    ttm_capex = CASHFLOW["2025"]["capex"] - CASHFLOW["2025H1"]["capex"] + CASHFLOW["2026H1"]["capex"]
    # DoveTree 现金：首付 5,100 万美元收入记在 2025H1、现金于 2025-08 前到账（2025080500993），第二笔 1,900 万美元 2026H1 到账
    ttm_dt = 365.089 + 129.407
    ttm_burn = ttm_ocf - ttm_capex
    print(f"  近 12 个月（2025H2+2026H1）消耗 {fmt(ttm_burn)}；剔除 DoveTree 两笔收款 {fmt(ttm_burn - ttm_dt)}；"
          f"2026H1 年化（剔除 DoveTree）{fmt(2 * (CASHFLOW['2026H1']['ocf'] - CASHFLOW['2026H1']['capex'] - 129.407))}")

    nf = net_financial(SCEN["基准"])
    print("\n[4] 经调整净现金（2026-06-30；基准情景折扣）")
    gross = CASH + BANK_DEPOSITS + WMP_MONEY + WMP_NOTES
    print(f"  现金 {fmt(CASH)} + 定期存款 {fmt(BANK_DEPOSITS)} + 货币基金 {fmt(WMP_MONEY)} + 结构性票据 {fmt(WMP_NOTES)}"
          f" = {fmt(gross)}（另有受限资金 {fmt(RESTRICTED)} 不计）")
    print(f"  − 银行借款 {fmt(BANK_DEBT)} − 可转债面值 {fmt(CB_FACE_RMB)}（HK${fmt(CB_FACE_HKD)}m）− 租赁 {fmt(LEASES)}")
    print(f"  核心净现金（基准，票据按 98%）{fmt(nf['cash_core'])} = HK${fmt(nf['cash_core'] * CNY_HKD)}m"
          f" = HK${nf['cash_core'] * CNY_HKD * 1e6 / (SHARES_BASIC + RSU_OUT):.2f}/股")
    print(f"  可转债到期赎回额 101.76% = HK${fmt(CB_FACE_HKD * CB_REDEEM_PCT)}m，溢价 HK${fmt(CB_FACE_HKD * (CB_REDEEM_PCT - 1))}m"
          f"（HK${CB_FACE_HKD * (CB_REDEEM_PCT - 1) * 1e6 / SHARES_BASIC:.3f}/股，未计入）；转股价 HK${CB_CONV_PRICE}，"
          f"可转 {CB_CONV_SHARES:,} 股（占现股 {CB_CONV_SHARES / SHARES_BASIC:.1%}）")
    inv_book = LISTED + PE_FUNDS + UNLISTED + CONV_DEBTS + EQUITY_METHOD
    print(f"  长期投资账面 {fmt(inv_book)}：上市 {fmt(LISTED)}、基金 {fmt(PE_FUNDS)}、非上市 {fmt(UNLISTED)}、"
          f"可转债权 {fmt(CONV_DEBTS)}、权益法 {fmt(EQUITY_METHOD)}")
    for n in SCEN:
        f = net_financial(SCEN[n])
        print(f"  {n}：核心净现金 {fmt(f['cash_core'])} + 投资可变现 {fmt(f['inv'])} − 少数股东 {fmt(NCI)}"
              f" = {fmt(f['total'])}（HK${fmt(f['total'] * CNY_HKD)}m）"
              f" → HK${f['total'] * CNY_HKD * 1e6 / (SHARES_BASIC + RSU_OUT):.2f}/股")
    # 分部成本口径（推断）：可重复收入 − 营业成本 − 销售 − 10% 管理费用分摊 − 10% 维持性研发
    c, rec = COSTS["2026H1"], REV_2026H1_RECURRING
    seg = rec - c["cogs"] - c["sm"] - 0.2 * rec
    unal = c["ga"] + c["rd"] + c["imp"] - c["oi"] - 0.2 * rec
    print(f"  2026H1 分部 EBIT {fmt(seg)}（{seg / rec:.1%}）；未分摊费用 {fmt(unal)}/半年（年化 {fmt(2 * unal)}）")
    burn_now = -(CASHFLOW["2026H1"]["ocf"] - CASHFLOW["2026H1"]["capex"] - 129.407) * 2
    print(f"  跑道：核心净现金 / 近 12 月剔除一次性消耗 = {nf['cash_core'] / -(ttm_burn - ttm_dt):.1f} 年；"
          f"/ 2026H1 年化 = {nf['cash_core'] / burn_now:.1f} 年；含投资可变现 = "
          f"{nf['total'] / burn_now:.1f} 年")

    print("\n[5] 三情景（折现率 10%）")
    r = 0.10
    results = {}
    for n in SCEN:
        res = value(n, r)
        results[n] = res
        op = res["op"]
        print(f"  —— {n}（概率 {SCEN[n]['prob']:.0%}）")
        print(f"     可重复收入 2026E {fmt(op['rev'][2026])} → 2030E {fmt(op['rev'][2030])} → 2035E {fmt(op['rev'][2035])}")
        print(f"     平台与服务 DCF {fmt(op['seg'])}（其中终值 {fmt(op['seg_tv'])}）")
        print(f"     未签约 BD 流 {fmt(op['bd'])}（终值 {fmt(op['bd_tv'])}）")
        print(f"     已签约交易与合作资产 rNPV {fmt(res['deals_total'])}")
        print(f"     未分摊总部+平台/管线研发 {fmt(op['unalloc'])}（终值 {fmt(op['u_tv'])}）；显性期税 {fmt(op['tax'])}")
        print(f"     经营业务合计 {fmt(res['op_total'])}；+ 金融资产净额 {fmt(res['nf']['total'])}"
              f" = 权益 {fmt(res['equity'])} = HK${fmt(res['equity'] * CNY_HKD)}m → V = HK${res['v']:.2f}/股")
        be = next((row[0] for row in op["rows"] if row[5] > 0), "2035 年后")
        cum, low, low_y = 0.0, 0.0, "-"
        for row in op["rows"]:
            cum += row[6]
            if cum < low:
                low, low_y = cum, row[0]
        print(f"     合并经营利润（分部+BD−未分摊）首次转正：{be}；终值年合并经营利润 {fmt(op['cons_T'])}；"
              f"累计自由现金流最低 {fmt(low)}（{low_y}）")
    print("\n  已签约交易明细（基准，人民币百万）：")
    for k, v in results["基准"]["deals"].items():
        print(f"     {k:28s} {fmt(v)}")

    print("\n  基准情景年度路径（人民币百万）：期间 | 可重复收入 | 分部 EBIT | BD | 未分摊 | 合并经营利润 | 自由现金流")
    for row in results["基准"]["op"]["rows"]:
        print("     " + " | ".join([row[0]] + [fmt(x, 0) for x in row[1:]]))

    vw = weighted(r)
    pv_ratio = PRICE_HKD / vw
    print(f"\n[6] 概率加权独立 V = HK${vw:.2f}/股；P/V = {PRICE_HKD}/{vw:.2f} = {pv_ratio:.2f} → {band(pv_ratio)}")

    print("\n[7] 折现率敏感性（HK$/股）：r | 熊 | 基准 | 牛 | 加权 | P/V")
    for rr in (0.09, 0.10, 0.11, 0.12):
        vs = [value(n, rr)["v"] for n in SCEN]
        w = weighted(rr)
        print(f"     {rr:.0%} | " + " | ".join(f"{x:.2f}" for x in vs) + f" | {w:.2f} | {PRICE_HKD / w:.2f}")
    print("  终值增长敏感性（基准，r=10%）：", end="")
    for gg in (0.015, 0.025):
        print(f" g={gg:.1%} → HK${value('基准', 0.10, override=dict(g=gg))['v']:.2f}", end="；")
    print()
    b = SCEN["基准"]
    tests = [
        ("未分摊费用 ×0.8", dict(unalloc=[x * 0.8 for x in b["unalloc"]], u_term=b["u_term"] * 0.8), 1.0),
        ("未分摊费用 ×1.2", dict(unalloc=[x * 1.2 for x in b["unalloc"]], u_term=b["u_term"] * 1.2), 1.0),
        ("可重复收入 ×1.2", None, 1.2),
        ("可重复收入 ×0.8", None, 0.8),
        ("分部利润率 +3pp", dict(margin=[x + 0.03 for x in b["margin"]]), 1.0),
        ("未签约 BD ×2", dict(bd=[x * 2 for x in b["bd"]]), 1.0),
        ("投资按账面不打折", dict(keep=dict(notes=1, listed=1, pe=1, unlisted=1, cd=1, eqm=1)), 1.0),
    ]
    print("  基准情景单项敏感性（r=10%）：")
    for label, ov, sc in tests:
        print(f"     {label:16s} → HK${value('基准', 0.10, scale=sc, override=ov)['v']:.2f}")

    print("\n[8] 现价隐含回报（IRR：使情景价值等于现价的折现率）")
    for n in ("基准", "牛"):
        gmin = SCEN[n]["g"] + 0.0005
        irr = solve(lambda x: value(n, x)["v"], gmin, 0.40, PRICE_HKD)
        if irr is None:
            vmax = value(n, gmin)["v"]
            print(f"  {n}：在 r ∈ ({gmin:.2%}, 40%) 内无解（r 趋近 g 时 V 仅 HK${vmax:.2f}），即隐含回报 < {gmin:.1%}")
        else:
            print(f"  {n}：IRR = {irr:.2%}")

    print("\n[9] 反向估值")
    nf_b = results["基准"]["nf"]["total"]
    implied_op_rmb = mcap_hkd / CNY_HKD - nf_b
    print(f"  市值 RMB {fmt(mcap_hkd / CNY_HKD)} − 金融资产净额（基准）{fmt(nf_b)} = 隐含经营价值 RMB {fmt(implied_op_rmb)}"
          f"（HK${fmt(implied_op_rmb * CNY_HKD)}m）")
    rec26 = results["基准"]["op"]["rev"][2026]
    ev_hkd = mcap_hkd - nf_b * CNY_HKD
    print(f"  隐含 EV / 2026E 可重复收入 {rec26:.0f} = {implied_op_rmb / rec26:.1f} 倍；/ 近 12 月总收入 "
          f"{(HIST['2025']['rev'] - HIST['2025H1']['rev'] + HIST['2026H1']['rev']):.0f} = "
          f"{implied_op_rmb / (HIST['2025']['rev'] - HIST['2025H1']['rev'] + HIST['2026H1']['rev']):.1f} 倍；EV ≈ US${ev_hkd / USD_HKD:,.0f}m")
    for n in ("基准", "牛"):
        s0 = SCEN[n]
        u_abs = s0["u_term"] * revenue_path(s0)[2036]   # 费用按该情景绝对额固定，只放大收入
        k = solve(lambda x: value(n, 0.10, scale=x, override=dict(u_term_abs=u_abs))["v"], 0.2, 12.0, PRICE_HKD)
        if k:
            rev35 = revenue_path(s0, k)[2035]
            print(f"  按{n}利润率、{n}费用绝对额不变，需把 2027–2035 收入整体放大 {k:.2f} 倍：2035E 可重复收入 RMB {fmt(rev35, 0)}m"
                  f"（2026E→2035E 年复合 {((rev35 / revenue_path(s0)[2026]) ** (1 / 9) - 1):.1%}）")
        else:
            print(f"  按{n}参数：收入放大至 12 倍仍不足以支撑现价")
    pv_m = 1.10 ** (-(2032 - 2026 + 0.5 - VAL_FRAC))
    need_usd = implied_op_rmb / USD_CNY / pv_m
    print(f"  若全部由里程碑兑现：需 2032 年前后确定性收到约 US${need_usd:,.0f}m（现值系数 {pv_m:.2f}），"
          f"相当于 DoveTree 58.9 亿美元里程碑上限的 {need_usd / 5890:.0%}")

    print("\n[10] 交叉验证")
    # 同业（美元百万；市值为股价×股数的推断值，见正文来源）
    rx_mcap, rx_cash = 3.44 * 530, 556.8                      # RXRX 2026-09-03 价 3.44 美元 × 约 5.3 亿股；现金 2026-06-30
    rx_ttm = 74.681 - 33.968 + 14.143                         # FY2025 − 1H25 + 1H26 收入
    sd_lo, sd_hi, sd_cash, sd_rev = 29.23 * 65.6, 29.23 * 74.7, 418.8, 58.9 * 4   # SDGR 2026-09-22 价；Q2 年化收入
    ce_mcap, ce_rev = 1210.0, (367 + 382) / 2                 # CERT 市值约 12.1 亿美元；2026 收入指引中值
    print(f"  Recursion：市值约 {rx_mcap:,.0f}，EV/近 12 月收入 {(rx_mcap - rx_cash) / rx_ttm:.1f} 倍（近 12 月收入 {rx_ttm:.1f}）")
    print(f"  Schrödinger：市值约 {sd_lo:,.0f}–{sd_hi:,.0f}，EV/年化 Q2 收入 {(sd_lo - sd_cash) / sd_rev:.1f}–"
          f"{(sd_hi - sd_cash) / sd_rev:.1f} 倍")
    print(f"  Certara：市值/2026 指引收入 {ce_mcap / ce_rev:.1f} 倍；药明康德 PS（TTM）约 10 倍（外部估算）")
    for mult in (5, 10, 20, 30):
        eq = mult * rec26 + nf_b
        print(f"  {mult:>2d} 倍 × 2026E 可重复收入 + 金融资产净额 → HK${per_share(eq):.2f}/股")
    print("  融资价格：2024-06 IPO HK$5.28；2025-01 配售 HK$4.28；2025-02 配售 HK$6.10；2025-08 配售 HK$9.28；"
          "2026-01 可转债转股价 HK$13.85")
    for p in (5.28, 4.28, 6.10, 9.28, 13.85):
        print(f"     现价 / {p} = {PRICE_HKD / p:.2f}")
    sh0 = 3_413_523_761
    print(f"  股本：2025-01-01 {sh0:,} → 2026-09-30 {SHARES_BASIC:,}（+{SHARES_BASIC / sh0 - 1:.1%}）；"
          f"含可转债全部转股 +{(SHARES_BASIC + CB_CONV_SHARES) / sh0 - 1:.1%}")


if __name__ == "__main__":
    main()
