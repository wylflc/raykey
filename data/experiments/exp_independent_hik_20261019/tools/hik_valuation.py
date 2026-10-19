#!/usr/bin/env python3
"""海康威视（002415）独立估值计算（价格日 2026-10-19）。

全部输入写在本脚本内，不联网。运行：
    cd data/experiments/exp_independent_hik_20261019 && python3 tools/hik_valuation.py

金额单位：亿元人民币（另注明者除外）。正文 companies/002415_海康威视.md 的估值数字均由本脚本输出。
口径：所有者收益 DCF（归母口径，扣少数股东），股权成本 9%（敏感性 8%/10%），终值增长 <= 2.5%。
"""

# ---------------------------------------------------------------------------
# 一、市场与资产负债表输入（来源：数据包 packs/002415、2026 三季报、2026 半年报附注）
# ---------------------------------------------------------------------------
PRICE = 33.19                  # 2026-10-19 收盘，元
SHARES = 91.6487155            # 亿股（三季报：9,164,871,550 股）
MKT_CAP = PRICE * SHARES       # 亿元

BS = {                         # 2026-09-30 合并资产负债表（三季报）
    "cash": 370.84,            # 货币资金
    "deriv_asset": 0.29,       # 衍生金融资产
    "short_loan": 31.12,
    "long_loan": 8.65,
    "ncl_1y": 10.91,           # 一年内到期的非流动负债
    "lease": 3.14,             # 租赁负债
    "deriv_liab": 0.04,
    "div_payable": 0.19,       # 应付股利
    "parent_equity": 842.75,   # 归母权益
    "minority_equity": 92.71,
    "inventory": 333.34,
    "lt_equity_invest": 15.67, # 长期股权投资（含联芸科技账面值）
    "other_nc_finasset": 6.73, # 其他非流动金融资产
}
RESTRICTED_CASH = 4.08         # 半年报附注：受限资金 407,867,779.21 元（三季报未披露，沿用）
CETC_FIN_DEPOSIT = 44.40       # 半年报：存放中国电子科技财务有限公司 4,440,090,336.34 元（2025 末 62.96）
TTM_REVENUE = 1007.94

# 联芸科技（688449）：海康威视 8,075.19 万股 + 杭州海康威视科技 5,382.83 万股，合计 29.26%（2026-06-30）
MAXIO_STAKE = (0.807519 + 0.538283) / 4.60
MAXIO_MKT_CAP = 216.02         # 2026-10-19 腾讯行情，46.96 元 × 4.60 亿股
MAXIO_BOOK = 5.5               # 估计：联营企业“其他”5.62 亿 ≈ 联芸净资产 19.06 亿 × 29.26%
EZVIZ_STAKE = 0.48             # 萤石网络 3.78 亿股 / 7.875 亿股
EZVIZ_MKT_CAP = 224.04         # 2026-10-19，28.45 元
EZVIZ_TTM_NP = 7.60

# ---------------------------------------------------------------------------
# 二、TTM（2025Q4～2026Q3）利润表，由东财 F10 累计数差分得到
# ---------------------------------------------------------------------------
TTM = {
    "revenue": 1007.94, "cogs": 514.37, "surcharge": 8.38,
    "sales": 125.14, "admin": 31.35, "rd": 123.61,
    "fin_exp": 6.20, "int_exp": 1.63, "int_inc": 6.28,
    "other_income": 28.31, "invest_income": 8.77, "assoc_income": 7.55,
    "fv_change": 0.53, "credit_imp": -10.27, "asset_imp": -4.56, "disposal": 0.08,
    "op_profit": 221.75, "total_profit": 222.30, "tax": 23.37,
    "net_profit": 198.93, "minority": 21.06, "parent_np": 177.88, "deducted_np": 174.28,
    "ocf": 188.56, "capex": 27.69,
}
HIST = [  # 年度：营收、毛利率、营业利润率、归母、扣非、经营现金流、购建长期资产（数据包第三节）
    ("2021", 814.20, 44.3, 22.7, 168.00, 164.45, 127.09, 30.98),
    ("2022", 831.66, 42.3, 17.8, 128.38, 123.31, 101.64, 37.56),
    ("2023", 893.41, 44.3, 18.0, 141.08, 136.66, 166.22, 40.48),
    ("2024", 924.96, 43.8, 15.5, 119.77, 118.15, 132.64, 46.66),
    ("2025", 925.08, 45.9, 18.3, 141.95, 137.03, 253.39, 36.22),
]

# ---------------------------------------------------------------------------
# 三、情景参数
# ---------------------------------------------------------------------------
def linpath(a, b, n_ramp, n_total):
    """从 a 线性变到 b（n_ramp 年），之后保持 b，共 n_total 年。"""
    out = []
    for i in range(n_total):
        out.append(b if i >= n_ramp - 1 else a + (b - a) * i / (n_ramp - 1))
    return out


SCEN = {
    "熊": dict(
        prob=0.25, R0=1000.0, gm0=0.455, opex0=0.290,
        growth=[0.03, 0.04, 0.04, 0.04, 0.03, 0.03, 0.03, 0.025, 0.025, 0.02],
        margin=[0.165, 0.160] + [0.160] * 8,
        tax=0.125, mi=[0.09] * 10,
        inv_release={2027: 20.0, 2028: 20.0}, inv_loss={2027: 30.0},
        g=0.020, ronic=0.15,
        cetc_haircut=0.30, maxio_factor=0.50, other_lt_factor=0.50,
    ),
    "基准": dict(
        prob=0.50, R0=1015.0, gm0=0.470, opex0=0.285,
        growth=[0.07, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04, 0.04, 0.035, 0.03],
        margin=None,  # 由 gm0/opex0 推出并保持不变
        tax=0.115, mi=linpath(0.095, 0.110, 5, 10),
        inv_release={2027: 30.0, 2028: 30.0}, inv_loss={2027: 10.0},
        g=0.025, ronic=0.20,
        cetc_haircut=0.10, maxio_factor=0.70, other_lt_factor=0.70,
    ),
    "牛": dict(
        prob=0.25, R0=1030.0, gm0=0.485, opex0=0.280,
        growth=[0.10, 0.09, 0.08, 0.07, 0.06, 0.055, 0.05, 0.045, 0.04, 0.035],
        margin=[0.210, 0.2125, 0.215] + [0.215] * 7,
        tax=0.110, mi=linpath(0.100, 0.120, 5, 10),
        inv_release={2027: 35.0, 2028: 35.0}, inv_loss={},
        g=0.025, ronic=0.25,
        cetc_haircut=0.0, maxio_factor=0.80, other_lt_factor=0.80,
    ),
}
# 共同的利润率构成（占收入）：税金及附加、其他收益（增值税即征即退为主）、减值（信用+资产）
SURCHARGE = 0.0085
OTHER_INC = 0.026
IMPAIR = 0.013
REINVEST_OF_DREV = 0.30     # 每增加 1 元收入需投入的营运资本（0.20）与净资本开支（0.10）
OPER_RESERVE_PCT = 0.05     # 经营备付：TTM 营收 × 5%
NET_INTEREST = 4.4          # 正常化净利息收入（税前），仅用于报“正常化归母净利”，DCF 不含
INV_ATTR = 0.90             # 存货释放/损失的归母比例
START_YEAR = 2027
T_FIRST = 0.70              # 2026-10-19 至 2027 年年中
T_STUB = 0.10               # 2026Q4 存根现金流的折现时点
STUB_FRAC = 0.25            # 2026-10-01～12-31 的所有者收益（资产负债表截至 9-30）
RATES = (0.08, 0.09, 0.10)


def base_margin(s):
    return s["gm0"] - SURCHARGE - s["opex0"] + OTHER_INC - IMPAIR


def margins(s):
    return s["margin"] if s["margin"] is not None else [base_margin(s)] * 10


# ---------------------------------------------------------------------------
# 四、经调整净现金与非经营资产
# ---------------------------------------------------------------------------
def adjusted_net_cash(s):
    debt = BS["short_loan"] + BS["long_loan"] + BS["ncl_1y"] + BS["lease"]
    reserve = OPER_RESERVE_PCT * TTM_REVENUE
    cetc_cut = s["cetc_haircut"] * CETC_FIN_DEPOSIT
    items = [
        ("货币资金", BS["cash"]),
        ("衍生金融资产", BS["deriv_asset"]),
        ("减：受限资金（半年报口径）", -RESTRICTED_CASH),
        ("减：经营备付（TTM 营收×%.0f%%）" % (OPER_RESERVE_PCT * 100), -reserve),
        ("减：已宣派未付股利（应付股利）", -BS["div_payable"]),
        ("减：有息负债（短借+长借+一年内到期+租赁）", -debt),
        ("减：衍生金融负债", -BS["deriv_liab"]),
        ("减：财务公司存款折扣（44.40×%.0f%%）" % (s["cetc_haircut"] * 100), -cetc_cut),
    ]
    return sum(v for _, v in items), items


def non_operating(s):
    maxio_mv = MAXIO_STAKE * MAXIO_MKT_CAP
    other_lt = BS["lt_equity_invest"] - MAXIO_BOOK + BS["other_nc_finasset"]
    items = [
        ("联芸科技 %.2f%% × 市值 %.2f × %.0f%%" % (MAXIO_STAKE * 100, MAXIO_MKT_CAP, s["maxio_factor"] * 100),
         maxio_mv * s["maxio_factor"]),
        ("其他长期股权投资与非流动金融资产账面 %.2f × %.0f%%" % (other_lt, s["other_lt_factor"] * 100),
         other_lt * s["other_lt_factor"]),
    ]
    return sum(v for _, v in items), items


# ---------------------------------------------------------------------------
# 五、所有者收益 DCF
# ---------------------------------------------------------------------------
def project(s):
    """返回逐年 (年份, 收入, EBIT, NOPAT, 再投资, 一次性, 归母所有者收益, 少数比例)。"""
    rows = []
    rev_prev = s["R0"]
    m = margins(s)
    for k in range(10):
        yr = START_YEAR + k
        rev = rev_prev * (1 + s["growth"][k])
        ebit = rev * m[k]
        nopat = ebit * (1 - s["tax"])
        reinv = REINVEST_OF_DREV * (rev - rev_prev)
        mi = s["mi"][k]
        one_off = INV_ATTR * (s["inv_release"].get(yr, 0.0) - s["inv_loss"].get(yr, 0.0) * (1 - s["tax"]))
        oe = (nopat - reinv) * (1 - mi) + one_off
        rows.append((yr, rev, ebit, nopat, reinv, one_off, oe, mi))
        rev_prev = rev
    return rows


def normalized_2026(s):
    ebit = s["R0"] * base_margin(s)
    nopat = ebit * (1 - s["tax"])
    attr_nopat = nopat * (1 - s["mi"][0])
    attr_np = (ebit + NET_INTEREST) * (1 - s["tax"]) * (1 - s["mi"][0])
    return ebit, nopat, attr_nopat, attr_np


def value(s, r, detail=False):
    rows = project(s)
    ebit0, nopat0, attr_nopat0, _ = normalized_2026(s)
    # 2026Q4 存根：归母 NOPAT 的 1/4，扣除按首年增速计算的再投资占比
    reinvest_share = REINVEST_OF_DREV * s["growth"][0] * s["R0"] / nopat0
    stub = STUB_FRAC * attr_nopat0 * (1 - reinvest_share)
    pv_stub = stub / (1 + r) ** T_STUB
    pv_exp = 0.0
    for k, row in enumerate(rows):
        t = T_FIRST + k
        pv_exp += row[6] / (1 + r) ** t
    yr10 = rows[-1]
    rev11 = yr10[1] * (1 + s["g"])
    nopat11 = rev11 * margins(s)[-1] * (1 - s["tax"])
    oe11 = nopat11 * (1 - s["g"] / s["ronic"]) * (1 - yr10[7])
    t10 = T_FIRST + 9
    tv = oe11 / (r - s["g"])
    pv_tv = tv / (1 + r) ** t10
    nc, _ = adjusted_net_cash(s)
    no, _ = non_operating(s)
    equity = pv_stub + pv_exp + pv_tv + nc + no
    if detail:
        return dict(stub=pv_stub, explicit=pv_exp, tv=pv_tv, tv_undisc=tv, oe11=oe11,
                    net_cash=nc, nonop=no, equity=equity, per_share=equity / SHARES)
    return equity / SHARES


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


# ---------------------------------------------------------------------------
# 六、输出
# ---------------------------------------------------------------------------
def main():
    print("=" * 78)
    print("海康威视（002415）独立估值  价格日 2026-10-19  单位：亿元（每股为元）")
    print("=" * 78)
    print(f"收盘价 {PRICE:.2f} 元；总股本 {SHARES:.4f} 亿股；总市值 {MKT_CAP:.2f}")
    pe_ttm = MKT_CAP / TTM["parent_np"]
    pb = MKT_CAP / BS["parent_equity"]
    dps_ttm = 0.75 + 0.55
    print(f"TTM PE {pe_ttm:.2f}×；扣非 PE {MKT_CAP / TTM['deducted_np']:.2f}×；PB {pb:.2f}×；"
          f"TTM 每股现金分红 {dps_ttm:.2f} 元，股息率 {dps_ttm / PRICE * 100:.2f}%")

    print("\n[1] 历史与 TTM（亿元）")
    print("年度   营收     毛利率  营业利润率  归母    扣非    经营现金流  购建长期资产")
    for h in HIST:
        print(f"{h[0]}  {h[1]:8.2f}  {h[2]:5.1f}%  {h[3]:6.1f}%   {h[4]:7.2f} {h[5]:7.2f}  {h[6]:8.2f}   {h[7]:7.2f}")
    gm_ttm = 1 - TTM["cogs"] / TTM["revenue"]
    opm_ttm = TTM["op_profit"] / TTM["revenue"]
    print(f"TTM   {TTM['revenue']:8.2f}  {gm_ttm * 100:5.2f}%  {opm_ttm * 100:6.2f}%   {TTM['parent_np']:7.2f} "
          f"{TTM['deducted_np']:7.2f}  {TTM['ocf']:8.2f}   {TTM['capex']:7.2f}")

    # EBIT 口径（剔除财务费用、投资收益与公允价值变动）
    ebit_ttm = TTM["op_profit"] + TTM["fin_exp"] - TTM["invest_income"] - TTM["fv_change"]
    fx_other = TTM["fin_exp"] - TTM["int_exp"] + TTM["int_inc"]
    opex_ttm = (TTM["sales"] + TTM["admin"] + TTM["rd"]) / TTM["revenue"]
    imp_ttm = -(TTM["credit_imp"] + TTM["asset_imp"]) / TTM["revenue"]
    oth_ttm = TTM["other_income"] / TTM["revenue"]
    sur_ttm = TTM["surcharge"] / TTM["revenue"]
    print(f"\nTTM 经营 EBIT（剔除财务费用、投资收益、公允价值变动）{ebit_ttm:.2f}，率 {ebit_ttm / TTM['revenue'] * 100:.2f}%")
    print(f"TTM 财务费用中“利息以外部分”（汇兑损失+手续费）{fx_other:.2f}；联营合营投资收益 {TTM['assoc_income']:.2f}")
    print(f"TTM 三项费用率 {opex_ttm * 100:.2f}%；减值率 {imp_ttm * 100:.2f}%；其他收益率 {oth_ttm * 100:.2f}%；税金及附加率 {sur_ttm * 100:.2f}%")
    print(f"TTM 有效税率 {TTM['tax'] / TTM['total_profit'] * 100:.2f}%；少数股东损益占净利 {TTM['minority'] / TTM['net_profit'] * 100:.2f}%")

    # 毛利率拆解（判断性分配；前三季度同比，百分点）
    gm9_26 = 1 - 372.96 / 740.44   # 2026 前三季度营业成本/营收（三季报）
    gm9_25 = 1 - 359.26 / 657.58   # 2025 前三季度
    decomp = [
        ("低价库存转收入（移动加权平均成本滞后，一次性）", 1.8),
        ("提价与缺货溢价（周期性，供给恢复后回吐）", 0.5),
        ("海康存储等存储类产品景气（周期性）", 0.4),
        ("2025 年调整的全年化（以 2025Q3 45.67% 为起点的差额）", 0.3),
        ("产品结构、AI 产品与产品线梳理（结构性）", 0.9),
        ("创新业务规模效应与提效（结构性）", 0.5),
        ("反内卷价格纪律中可持续部分（结构性）", 0.2),
        ("创新业务占比上升的稀释", -0.4),
    ]
    print(f"\n[1b] 毛利率拆解：2026 前三季度 {gm9_26 * 100:.2f}% vs 2025 前三季度 {gm9_25 * 100:.2f}%，"
          f"同比 {(gm9_26 - gm9_25) * 100:+.2f}pp（分配为判断）")
    for k, v in decomp:
        print(f"  {k:<44s} {v:+.1f}pp ≈ {v / 100 * 740.44:+.1f} 亿毛利")
    resid = (gm9_26 - gm9_25) * 100 - sum(v for _, v in decomp)
    print(f"  未分配残差 {resid:+.2f}pp")
    keep = gm9_25 * 100 + 0.3 + 0.9 + 0.5 + 0.2 - 0.4
    print(f"  正常化毛利率 ≈ 2025 前三季度 {gm9_25 * 100:.2f}% + 全年化 0.3 + 结构性 1.6 − 稀释 0.4 = {keep:.2f}%"
          f"（基准取 47.0%，熊 45.5%，牛 48.5%）")

    print("\n[2] 正常化（2026 年口径）")
    b = SCEN["基准"]
    for name, s in SCEN.items():
        ebit, nopat, attr_nopat, attr_np = normalized_2026(s)
        print(f"{name}: 收入 {s['R0']:.0f}，毛利率 {s['gm0'] * 100:.1f}%，三项费用率 {s['opex0'] * 100:.1f}%，"
              f"EBIT 率 {base_margin(s) * 100:.2f}%，EBIT {ebit:.2f}，NOPAT {nopat:.2f}，"
              f"归母 NOPAT {attr_nopat:.2f}，正常化归母净利（含净利息）{attr_np:.2f}，EPS {attr_np / SHARES:.3f}")
    # 基准桥：TTM EBIT -> 正常化 EBIT
    R = TTM["revenue"]
    bridge = [
        ("TTM 经营 EBIT", ebit_ttm),
        ("毛利率 %.2f%%→%.1f%%" % (gm_ttm * 100, b["gm0"] * 100), -(gm_ttm - b["gm0"]) * R),
        ("三项费用率 %.2f%%→%.1f%%" % (opex_ttm * 100, b["opex0"] * 100), -(b["opex0"] - opex_ttm) * R),
        ("其他收益率 %.2f%%→%.1f%%" % (oth_ttm * 100, OTHER_INC * 100), -(oth_ttm - OTHER_INC) * R),
        ("减值率 %.2f%%→%.1f%%" % (imp_ttm * 100, IMPAIR * 100), (imp_ttm - IMPAIR) * R),
        ("税金及附加率 %.2f%%→%.2f%%" % (sur_ttm * 100, SURCHARGE * 100), -(SURCHARGE - sur_ttm) * R),
        ("收入基数 %.2f→%.0f（按正常化利润率）" % (R, b["R0"]), (b["R0"] - R) * base_margin(b)),
    ]
    tot = 0.0
    for k, v in bridge:
        tot += v
        print(f"  {k:<40s} {v:+8.2f}")
    print(f"  = 正常化 EBIT（基准） {tot:.2f}（直接计算 {normalized_2026(b)[0]:.2f}）")
    ttm_bridge_np = TTM["parent_np"]
    print(f"  对照：TTM 归母 {ttm_bridge_np:.2f} → 基准正常化归母 {normalized_2026(b)[3]:.2f}"
          f"（{(normalized_2026(b)[3] / ttm_bridge_np - 1) * 100:+.1f}%）")

    print("\n[3] 经调整净现金与非经营资产（按情景）")
    for name, s in SCEN.items():
        nc, items = adjusted_net_cash(s)
        no, items2 = non_operating(s)
        print(f"-- {name}情景")
        for k, v in items:
            print(f"   {k:<44s} {v:+9.2f}")
        print(f"   经调整净现金 {nc:.2f}（每股 {nc / SHARES:.3f} 元）")
        for k, v in items2:
            print(f"   {k:<44s} {v:+9.2f}")
        print(f"   非经营资产合计 {no:.2f}（每股 {no / SHARES:.3f} 元）")
    print(f"   单独列示：财务公司存款 {CETC_FIN_DEPOSIT:.2f}（2026-06-30），占货币资金 {CETC_FIN_DEPOSIT / BS['cash'] * 100:.1f}%；"
          f"联芸科技持股市值 {MAXIO_STAKE * MAXIO_MKT_CAP:.2f}（持股 {MAXIO_STAKE * 100:.2f}%）")

    print("\n[4] 基准情景逐年（归母所有者收益）")
    print("年份  收入      EBIT    NOPAT   再投资  一次性   少数比例  归母OE")
    for row in project(b):
        print(f"{row[0]}  {row[1]:8.2f}  {row[2]:7.2f}  {row[3]:7.2f}  {row[4]:6.2f}  {row[5]:+6.2f}   {row[7] * 100:5.2f}%   {row[6]:7.2f}")
    d = value(b, 0.09, detail=True)
    print(f"9% 下：存根 {d['stub']:.2f} + 显性期 {d['explicit']:.2f} + 终值现值 {d['tv']:.2f}"
          f"（终值 {d['tv_undisc']:.2f}，首年 OE {d['oe11']:.2f}）+ 净现金 {d['net_cash']:.2f} + 非经营 {d['nonop']:.2f}"
          f" = {d['equity']:.2f} → {d['per_share']:.2f} 元/股；终值占比 {d['tv'] / (d['equity']) * 100:.1f}%")

    print("\n[5] 情景 × 股权成本（元/股）")
    print("情景   概率   8%      9%      10%")
    wv = {r: 0.0 for r in RATES}
    for name, s in SCEN.items():
        vals = [value(s, r) for r in RATES]
        for r, v in zip(RATES, vals):
            wv[r] += s["prob"] * v
        print(f"{name:<4s}  {s['prob']:.2f}  {vals[0]:6.2f}  {vals[1]:6.2f}  {vals[2]:6.2f}")
    print(f"加权  1.00  {wv[0.08]:6.2f}  {wv[0.09]:6.2f}  {wv[0.10]:6.2f}")
    for r in RATES:
        pv = PRICE / wv[r]
        tier = ("明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高")
        print(f"股权成本 {r * 100:.0f}%：独立 V {wv[r]:.2f} 元，P/V {pv:.3f}（{tier}）")

    print("\n[6] 现价隐含回报（基准情景 IRR）")
    for name, s in SCEN.items():
        irr = solve(lambda r: value(s, r), 0.03 if s["g"] < 0.03 else 0.035, 0.30, PRICE)
        print(f"{name}情景使现值=现价的折现率：{irr * 100:.2f}%")
    irr_w = solve(lambda r: sum(s["prob"] * value(s, r) for s in SCEN.values()), 0.035, 0.30, PRICE)
    print(f"三情景概率加权价值=现价的折现率：{irr_w * 100:.2f}%")

    print("\n[7] 反向 DCF（9%）")
    nc_b, _ = adjusted_net_cash(b)
    no_b, _ = non_operating(b)
    target = MKT_CAP - nc_b - no_b
    attr_nopat0 = normalized_2026(b)[2]
    oe0 = attr_nopat0 * (1 - 0.125)
    print(f"现价对应经营价值 = 市值 {MKT_CAP:.2f} − 净现金 {nc_b:.2f} − 非经营 {no_b:.2f} = {target:.2f}")

    def pv_growth(g, oe_start, r=0.09, gt=0.025):
        pv = STUB_FRAC * oe_start / (1 + r) ** T_STUB
        oe = oe_start
        for k in range(10):
            oe *= (1 + g)
            pv += oe / (1 + r) ** (T_FIRST + k)
        return pv + oe * (1 + gt) / (r - gt) / (1 + r) ** (T_FIRST + 9)
    g10 = solve(lambda g: pv_growth(g, oe0), -0.10, 0.30, target)
    print(f"(a) 以正常化归母所有者收益 {oe0:.2f}（归母 NOPAT {attr_nopat0:.2f} × 87.5%）起算、终值 2.5%：隐含 10 年增速 {g10 * 100:.2f}%")
    oe_ttm = (TTM["deducted_np"] - NET_INTEREST * (1 - 0.115) * 0.905 - TTM["assoc_income"] * 0.885) * (1 - 0.125)
    g10b = solve(lambda g: pv_growth(g, oe_ttm), -0.10, 0.30, target)
    print(f"(b) 若以 TTM 扣非（剔利息与联营）口径所有者收益 {oe_ttm:.2f} 起算：隐含 10 年增速 {g10b * 100:.2f}%")
    for ron in (0.20, 0.30):
        # V = NOPAT1 (1 - g/RONIC)/(r - g)，NOPAT1 = attr_nopat0 (1+g)
        gp = solve(lambda g: attr_nopat0 * (1 + g) * (1 - g / ron) / (0.09 - g), -0.05, 0.0899, target)
        print(f"(c) 永续增长口径（RONIC {ron * 100:.0f}%）：隐含永续增速 {gp * 100:.2f}%")
    vb = value(b, 0.09)
    print(f"对照：基准情景 10 年归母 OE 年化增速约 "
          f"{((project(b)[-1][6] / project(b)[0][6]) ** (1 / 9) - 1) * 100:.2f}%（2027→2036，含 2027 一次性项），基准 V {vb:.2f}")

    print("\n[8] 交叉验证")
    eps_n = normalized_2026(b)[3] / SHARES
    bvps = BS["parent_equity"] / SHARES
    pe_hist = [19.5, 23.8, 19.6, 38.2, 20.9, 24.6, 33.9, 29.1, 25.5, 23.0, 23.7, 19.3]
    pb_hist = [6.13, 7.27, 5.98, 11.86, 6.32, 6.81, 8.43, 7.70, 4.78, 4.24, 3.51, 3.28]
    srt = sorted(pe_hist)
    pe_med = (srt[5] + srt[6]) / 2
    rows = []
    rows.append(("所有者收益 DCF（基准，9%）", "见情景表", vb))
    rows.append(("概率加权 DCF（9%）", "熊/基准/牛 25/50/25", wv[0.09]))
    # 股东收益率：股息 + 回购
    yield_total = dps_ttm / PRICE
    ddm = 0.75 * eps_n * 1.045 / (0.09 - 0.045)
    rows.append(("股息+回购收益率", f"TTM 股息率 {yield_total * 100:.2f}% + 回购 0%；派息 75%×正常化 EPS，g=4.5%", ddm))
    rows.append(("历史 PE 下限", f"2014-2025 年末 PE 最低 {min(pe_hist):.1f}× × 正常化 EPS {eps_n:.3f}", min(pe_hist) * eps_n))
    rows.append(("历史 PE 中位", f"中位 {pe_med:.1f}× × 正常化 EPS（历史增速高，仅作上沿）", pe_med * eps_n))
    rows.append(("历史 PB 近三年", f"2023-2025 年末 PB 均值 {sum(pb_hist[-3:]) / 3:.2f}× × BVPS {bvps:.2f}", sum(pb_hist[-3:]) / 3 * bvps))
    dahua_pe_ded = 16.82
    rows.append(("同业：大华扣非 PE", f"{dahua_pe_ded:.2f}× × 正常化 EPS（大华 ROE 约 10%，海康更优，偏下沿）", dahua_pe_ded * eps_n))
    # EV/EBIT
    mi_value = 20.0 * b["mi"][0] * normalized_2026(b)[1]
    ev = MKT_CAP + mi_value - nc_b - no_b
    ebit_n = normalized_2026(b)[0]
    ev_ebit_mult = 15.0
    eq_ev = ev_ebit_mult * ebit_n - mi_value + nc_b + no_b
    rows.append(("EV/EBIT", f"15× 正常化 EBIT {ebit_n:.1f}；少数股东按 20×其盈利 {mi_value:.0f} 扣除", eq_ev / SHARES))
    # SOTP
    innov_attr = 22.0
    main_attr = normalized_2026(b)[2] - innov_attr
    ezviz_v = EZVIZ_STAKE * EZVIZ_MKT_CAP
    other_innov_attr = innov_attr - EZVIZ_STAKE * EZVIZ_TTM_NP
    other_innov_v = other_innov_attr * 25.0 * 0.8
    main_v = main_attr * 15.5
    sotp = main_v + ezviz_v + other_innov_v + nc_b + no_b
    rows.append(("分部加总", f"主业 {main_attr:.1f}×15.5 + 萤石市值×48% + 其他创新 {other_innov_attr:.1f}×25×0.8 + 净现金/非经营", sotp / SHARES))
    print("方法｜关键假设｜每股价值｜P/V")
    for m_, k_, v_ in rows:
        print(f"{m_}｜{k_}｜{v_:.2f}｜{PRICE / v_:.2f}")
    print(f"当前 EV/EBIT：正常化 {ev / ebit_n:.2f}×，TTM {ev / ebit_ttm:.2f}×（EV {ev:.2f}，含少数股东估值 {mi_value:.2f}）")
    print(f"分部明细：主业 {main_v:.1f}；萤石 {ezviz_v:.1f}；其他创新 {other_innov_v:.1f}；净现金 {nc_b:.1f}；非经营 {no_b:.1f}；合计 {sotp:.1f}")
    print(f"PB-ROE：海康正常化 ROE {normalized_2026(b)[3] / BS['parent_equity'] * 100:.1f}%，PB {pb:.2f}；大华 PB 1.27、TTM ROE 约 9.6%")

    print("\n[9] 基准敏感性（9%，元/股）")
    for dgm in (-0.02, -0.01, 0.0, 0.01, 0.02):
        s = dict(b)
        s["gm0"] = b["gm0"] + dgm
        print(f"  正常化毛利率 {s['gm0'] * 100:.1f}% → V {value(s, 0.09):.2f}")
    for dg in (-0.01, 0.01):
        s = dict(b)
        s["growth"] = [x + dg for x in b["growth"]]
        print(f"  10 年增速逐年 {dg * 100:+.0f}pp → V {value(s, 0.09):.2f}")
    for gt in (0.015, 0.020):
        s = dict(b)
        s["g"] = gt
        print(f"  终值增长 {gt * 100:.1f}% → V {value(s, 0.09):.2f}")


if __name__ == "__main__":
    main()
