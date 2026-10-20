# -*- coding: utf-8 -*-
"""300750 宁德时代 独立估值（OI-291 b07，价格日 2026-10-20；2026-10-21 修订：计入出口退税取消）

运行：python3 valuation.py
金额单位：亿元；每股：元。输入全部写在本脚本内，出处见注释与正文
（2026Q3_report、2026H1_report、2025_annual_report 页码；网络事实见正文「来源」）。

方法：归母核心经营所有者收益 DCF（剔除联营投资收益、净利息、补助、公允价值、汇兑）
      + 归母经调整净现金 + 归母非经营资产（洛阳钼业按 10-20 市值，其余按账面）。
经调整净现金为正，按无杠杆口径全额扣除有息负债；无可转债。
核心 EBIT = 营业收入 − 营业成本 − 税金及附加 − 销售/管理/研发费用 − 资产与信用减值
（减值每年都有，按经常性成本保留）。单位核心 EBIT = 核心 EBIT ÷ 锂电池销量（元/Wh）。
两项税负单列、按情景自担比例从单位核心 EBIT 中扣除：锂电池消费税（只对境内销量）与
电池出口退税下调及取消（只对从中国出口的销量，按相对标定期的增量计）。
"""
import copy

# ---------------------------------------------------------------- 市场与股本
PRICE = 259.08                      # A 股 2026-10-20 收盘（腾讯行情）
SHARES_TOTAL = 46.2725              # 亿股，A+H 全部股份，含回购专户（2026Q3_report 第 8 页股本 4,627,250 千元）
BUYBACK_CANCEL = 0.10945162         # 亿股，2026 年 A 股回购用于注销，截至 9-30（2026Q3_report 第 5 页）
TREASURY_ALL = 0.39264206           # 亿股，回购专户合计；其余 0.28319044 亿股用于股权激励/员工持股（2026Q3_report 第 4 页）
SHARES_MAIN = SHARES_TOTAL - BUYBACK_CANCEL          # 主口径：扣拟注销股份
SHARES_EX_TREASURY = SHARES_TOTAL - TREASURY_ALL     # 对照：剔除全部回购专户
H_PRICE_HKD = 411.80                # H 股 2026-10-20 收盘（腾讯行情），仅作参考
HKD_CNY = 0.86616                   # 2026-07-23 人民银行中间价（dividend_20260725_324646 第 2 页），近似
H_SHARES = 2.183003                 # 亿股 H 股：IPO 1.559153 + 2026-04-30 配售 0.62385（2026H1_report 第 149 页）

# ---------------------------------------------------------------- 资产负债（2026-09-30，2026Q3_report 第 5-8 页）
CASH = 3698.14
TRADING_FA = 627.80                 # 银行理财与结构性存款为主（2026H1_report 第 123 页）
LT_TIME_DEPOSIT = 26.69             # 其他非流动资产中的定期存单（2026H1_report 第 141 页，6-30 数）
DERIV_ASSET, DERIV_LIAB = 6.29, 16.46
RESTRICTED = 93.35                  # 保证金 85.81 + 质押定期存款 7.54（2026H1_report 第 123/142 页，6-30 数；三季报未披露）
DEBT = dict(short_loan=398.98, ncl_1yr=168.71, long_loan=763.55, bonds=527.38, lease=40.65)
LT_PAYABLE = 16.32                  # 长期应付款：国开基金、应付合作投资款等（2026H1_report 第 148 页）
EQUITY_TOTAL, MINORITY_EQUITY = 4232.17, 363.36

# 经营性营运资金：判断现金中有多少由负营运资金（浮存）支撑
OP_ASSETS = dict(note_rece=4.64, ar=1129.12, fin_rece=257.84, prepay=264.60, other_rece=23.42,
                 inventory=1447.70, contract_asset=3.24, other_ca=206.31, long_rece=4.10)
OP_LIABS = dict(note_pay=1529.30, ap=1804.42, contract_liab=406.69, other_ncl_prepay=41.72,
                staff=245.12, tax=115.74, other_pay=109.03, other_cl=97.35, provisions=1041.11)
DEFER_INCOME = 271.74               # 政府补助递延收益，非现金偿付义务，不计入浮存

# 经营备付：1 个月付现经营成本（TTM 营业成本+税金及附加+销售+管理+研发 − 折旧摊销约 322）
TTM_CASH_COSTS = 4426.51 + 45.28 + 46.98 + 127.50 + 255.96 - 322.0

# ---------------------------------------------------------------- 非经营资产
CMOC_SHARES = 0.2491 * 213.94310176   # 亿股：持股 24.91%（2025_annual_report 第 208 页）× 总股本 21,394,310,176（腾讯行情）
CMOC_PRICE = 14.35                     # 洛阳钼业 A 2026-10-20 收盘（腾讯行情）
CMOC_PARENT_SHARE = 0.792              # 经四川时代（公司持股 79.20%，2025_annual_report 第 207 页）旗下原洛矿集团持有
CMOC_BOOK_EST = 350.0                  # 估计账面（权益法），公司未单列；±60 亿影响每股约 ±1.2 元
LT_EQUITY_INV = 728.41                 # 长期股权投资合计（9-30）
OTHER_EQUITY_INST = 131.49             # 其他权益工具投资（公允价值计量）
OTHER_NC_FIN = 118.25                  # 其他非流动金融资产（基金等）

# ---------------------------------------------------------------- 经营假设
TAX = 0.16                  # 核心应税利润有效税率（TTM 所得税 158.5 ÷（利润总额 1,098.4 − 权益法收益 108.5））
MINO_CORE = 0.063           # 少数股东在核心经营利润中的份额（TTM 少数股东损益 62.9 扣洛钼对应约 15 后 ÷ 经营与利息利润）
MINO_CASH = MINORITY_EQUITY / EQUITY_TOTAL   # 少数股东应占现金与其他投资的近似比例（8.6%）
VOL_2026 = 960.0            # GWh：Q1 约 208 + Q2 约 232（媒体与券商口径）+ Q3 约 260（高盛估计）+ Q4 估 260
REV_2026_EST = 6000.0       # 2026 年营业收入估计（只用于出口额核对）
DOMESTIC_SHARE = 0.65       # 境内销量占比（2026H1 境内收入占 68.5%，2026H1_report 第 16 页）
ASP_2026 = 0.58             # 元/Wh，电池系统平均售价近似（2025 动力 0.585、储能 0.516）
ASP_FADE = 0.03
CTAX_RATE = {2026: 0.0224 * 4 / 12, 2027: 0.0224 * 8 / 12 + 0.0448 * 4 / 12}   # 消费税 2%（2026-09～2027-08）、4%，含 12% 附加
CTAX_FULL = 0.0448
COE = 0.09

# ---------------------------------------------------------------- 出口退税（2026-10-21 修订新增）
# 财政部 税务总局公告 2026 年第 2 号（2026-01-09 公布，主会话核对原文）：2026-04-01～12-31 电池产品增值税出口退税率
# 9%→6%；2027-01-01 起取消；征收消费税的产品出口消费税政策不变（继续退免，故消费税只计境内销量）。
# 免抵退税下不得免征和抵扣税额 = 离岸价 ×（征税率 13% − 退税率），计入成本：退税率 13%/9%/6% 时为离岸价 0/4%/7%
# （背景知识）。取消后按财税〔2012〕39 号第七条视同内销（背景知识）：销项 = 离岸价 ÷ 1.13 × 13% ≈ 11.5%，进项可抵扣；
# 进料加工保税进口料件的扣减忽略不计（简化，略高估税负）。
XTAX_RATE = {2026: 0.13 - 0.06}     # 2026 年单位利润同时决定 2026Q4 现金流与 2026 正常化，全年按 6% 退税率（7%）计
XTAX_FULL = 0.13 / 1.13             # 2027 年起取消退税（约 11.5%）
# 境外工厂电芯产出（GWh，三情景相同；不经中国出口）。德国图林根规划约 14 GWh（背景知识，未核对）按 10→12；
# 匈牙利一期超过 30 GWh（IR_20251021_372304 第 4 页）、2025 年底完成安装（IR_20260310_437622 第 5 页）、
# 2026 年爬坡（IR_20260416_252967 第 4 页）、9-22 电芯试生产（网络），规划 100 GWh；西班牙合资 50 GWh，2025-11 开工、
# 完工说法 2026 年末至 2028-03（网络）；印尼工厂在建（2026H1_report 第 15 页），一期规模按约 7 GWh（背景知识）。
OVERSEAS_PLANTS = {   # 年份: (德国, 匈牙利, 西班牙, 印尼)
    2026: (10, 3, 0, 0), 2027: (12, 15, 2, 3), 2028: (12, 30, 10, 7),
    2029: (12, 40, 25, 7), 2030: (12, 50, 35, 7), 2031: (12, 60, 45, 7),
}
OVERSEAS_PROD = {y: float(sum(v)) for y, v in OVERSEAS_PLANTS.items()}
# 标定期（2024-01～2026-09）从中国出口额与不得免抵税率：基准、牛的单位核心 EBIT 按该区间周期均值标定，
# 起点 = 出口额加权税率。出口额 = 境外收入 − 德国工厂产出（约 10 GWh/年 × 0.6 元/Wh ≈ 60 亿/年，背景知识）。
# 境外收入：2024 年 1,103.36（30.48%）、2025 年 1,296.41（2025_annual_report 第 25 页）；2026H1 871.29（2026H1_report
# 第 16 页，按单季收入 1,291.31/1,477.86 拆成 Q1/Q2）；2026Q3 未披露，按 H1 占比 31.46% × 1,652.21 估；
# 2024-12 按 2024Q4 收入 1,029.68 × 30.48% 的三分之一估。
XTAX_HIST = [  # (期间, 境外收入, 德国工厂产出, 不得免抵税率)
    ("2024-01～11", 1103.36 - 1029.68 * 0.3048 / 3, 55.0, 0.00),
    ("2024-12", 1029.68 * 0.3048 / 3, 5.0, 0.04),
    ("2025", 1296.41, 60.0, 0.04),
    ("2026Q1", 871.29 * 1291.31 / 2769.17, 15.0, 0.04),
    ("2026Q2", 871.29 * 1477.86 / 2769.17, 15.0, 0.07),
    ("2026Q3", 1652.21 * 0.3146, 15.0, 0.07),
]
HIST_VOLUME = 475 + 661 + 208 + 232 + 260   # GWh，2024-01～2026-09（2024、2025 年报数；2026 各季为估计）


def xtax_start_cycle():
    """标定期按从中国出口额加权的不得免抵税率。"""
    w = [(ov - de, r) for _, ov, de, r in XTAX_HIST]
    return sum(x * r for x, r in w) / sum(x for x, _ in w)


X_START_CYCLE = xtax_start_cycle()  # 约 3.75%
X_START_Q3 = 0.13 - 0.06            # 2026Q3 水平（6% 退税率）

SCENARIOS = {
    # unit：2026-27 年单位核心 EBIT（扣消费税与出口退税增量前，元/Wh）；fade：2028 起年降幅；absorb：消费税自担比例
    # absorb_x：出口退税增量自担比例；x_start：单位核心 EBIT 已含的不得免抵税率（只计相对它的增量）
    # k：每新增 1 GWh 年销量所需净投入（亿元，含配套材料与海外工厂，维持性开支 ≈ 折旧，已在利润中扣除）
    # ronic_t：终值期增量回报；g_t：终值增速
    "bear": dict(p=0.25, unit=0.072, fade=0.03, absorb=0.75, absorb_x=0.80, x_start=X_START_Q3,
                 vol_g=[0.08, 0.06, 0.05, 0.04, 0.03],
                 k=1.8, ronic_t=0.12, g_t=0.020, float_reversal=454.0, cmoc_haircut=0.25,
                 interest_at=45.0, assoc_norm=55.0),
    "base": dict(p=0.50, unit=0.087, fade=0.02, absorb=0.40, absorb_x=0.50, x_start=X_START_CYCLE,
                 vol_g=[0.18, 0.13, 0.10, 0.08, 0.06],
                 k=1.6, ronic_t=0.20, g_t=0.025, float_reversal=0.0, cmoc_haircut=0.0,
                 interest_at=50.0, assoc_norm=74.0),
    "bull": dict(p=0.25, unit=0.094, fade=0.01, absorb=0.15, absorb_x=0.25, x_start=X_START_CYCLE,
                 vol_g=[0.25, 0.18, 0.14, 0.10, 0.08],
                 k=1.4, ronic_t=0.25, g_t=0.025, float_reversal=0.0, cmoc_haircut=0.0,
                 interest_at=55.0, assoc_norm=90.0),
}
YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
T_MID = {2027: 0.70, 2028: 1.70, 2029: 2.70, 2030: 3.70, 2031: 4.70}   # 年中折现（距 2026-10-20）
T_STUB, T_TV = 0.10, 4.70           # 2026Q4 现金流（全年的 1/4）与终值（2031 年中）


def net_cash_block():
    gross = CASH + TRADING_FA + LT_TIME_DEPOSIT
    debt = sum(DEBT.values())
    pre_reserve = gross - RESTRICTED - debt - LT_PAYABLE + DERIV_ASSET - DERIV_LIAB
    reserve = TTM_CASH_COSTS / 12.0
    adj = pre_reserve - reserve
    op_a, op_l = sum(OP_ASSETS.values()), sum(OP_LIABS.values())
    float_total = op_l - op_a
    trade_float = OP_LIABS["note_pay"] + OP_LIABS["ap"] - (OP_ASSETS["note_rece"] + OP_ASSETS["ar"]
                  + OP_ASSETS["fin_rece"] + OP_ASSETS["prepay"] + OP_ASSETS["inventory"])
    return dict(gross=gross, debt=debt, pre_reserve=pre_reserve, reserve=reserve, adj=adj,
                float_total=float_total, trade_float=trade_float, free_strict=pre_reserve - float_total,
                prepay_float=OP_LIABS["contract_liab"] + OP_LIABS["other_ncl_prepay"],
                accrued=OP_LIABS["staff"] + OP_LIABS["tax"] + OP_LIABS["other_pay"] + OP_LIABS["other_cl"])


def non_op_block(cmoc_haircut=0.0):
    cmoc_mv = CMOC_SHARES * CMOC_PRICE * (1 - cmoc_haircut)
    other_ltei = LT_EQUITY_INV - CMOC_BOOK_EST
    group = cmoc_mv + other_ltei + OTHER_EQUITY_INST + OTHER_NC_FIN
    parent = cmoc_mv * CMOC_PARENT_SHARE + (other_ltei + OTHER_EQUITY_INST + OTHER_NC_FIN) * (1 - MINO_CASH)
    return dict(cmoc_mv=cmoc_mv, cmoc_parent=cmoc_mv * CMOC_PARENT_SHARE, other_ltei=other_ltei,
                group=group, parent=parent)


def asp(year):
    return ASP_2026 * (1 - ASP_FADE) ** (year - 2026)


def ctax_absorbed(year, s):
    rate = CTAX_RATE.get(year, CTAX_FULL)
    return s["absorb"] * rate * DOMESTIC_SHARE * asp(year)      # 元/Wh，摊到全部销量


def export_share(year, vol):
    """从中国出口的销量占比 = 1 − 境内占比（与消费税同一口径）− 境外工厂产出占比。"""
    return 1 - DOMESTIC_SHARE - OVERSEAS_PROD[year] / vol


def xtax_detail(year, s, vol):
    rate = XTAX_RATE.get(year, XTAX_FULL)
    share = export_share(year, vol)
    inc = rate - s["x_start"]
    per_wh = s["absorb_x"] * inc * share * asp(year)          # 元/Wh，摊到全部销量
    return dict(rate=rate, share=share, export_rev=share * asp(year) * vol * 10.0, inc=inc,
                per_wh=per_wh, pretax=per_wh * vol * 10.0)


def xtax_absorbed(year, s, vol):
    return xtax_detail(year, s, vol)["per_wh"]


def paths(s):
    vol, unit_pre, unit, ebit, nopat, ctax, xtax = {}, {}, {}, {}, {}, {}, {}
    vol[2026] = VOL_2026
    for i, y in enumerate(YEARS[1:]):
        vol[y] = vol[y - 1] * (1 + s["vol_g"][i])
    for y in YEARS:
        unit_pre[y] = s["unit"] * (1 - s["fade"]) ** max(0, y - 2027)
        ctax[y] = ctax_absorbed(y, s)
        xtax[y] = xtax_absorbed(y, s, vol[y])
        unit[y] = unit_pre[y] - ctax[y] - xtax[y]
        ebit[y] = vol[y] * unit[y] * 10.0               # 亿元（1 GWh × 1 元/Wh = 10 亿元）
        nopat[y] = ebit[y] * (1 - TAX) * (1 - MINO_CORE)
    nopat_next = nopat[2031] * (1 + s["g_t"])
    reinv, oe = {}, {}
    for y in YEARS:
        if y < 2031:   # 当年投入支撑下一年销量增长
            reinv[y] = (vol[y + 1] - vol[y]) * s["k"] * (1 - MINO_CORE)
        else:          # 进入终值期：再投资率 = g / RONIC_T
            reinv[y] = nopat[y] * s["g_t"] / s["ronic_t"]
        oe[y] = nopat[y] - reinv[y]
    oe_next = nopat_next * (1 - s["g_t"] / s["ronic_t"])
    inc_ret = (nopat[2031] - nopat[2026]) / sum(reinv[y] for y in YEARS[:-1])
    return dict(vol=vol, unit_pre=unit_pre, unit=unit, ctax=ctax, xtax=xtax, ebit=ebit, nopat=nopat,
                reinv=reinv, oe=oe, nopat_next=nopat_next, oe_next=oe_next, inc_ret=inc_ret)


def ops_value(s, r):
    p = paths(s)
    stub = 0.25 * p["oe"][2026] / (1 + r) ** T_STUB
    explicit = sum(p["oe"][y] / (1 + r) ** T_MID[y] for y in YEARS[1:])
    pv_tv = p["oe_next"] / (r - s["g_t"]) / (1 + r) ** T_TV
    return dict(stub=stub, explicit=explicit, tv=pv_tv, total=stub + explicit + pv_tv)


def scenario_value(s, r=COE, shares=SHARES_MAIN):
    nc = net_cash_block()
    no = non_op_block(s["cmoc_haircut"])
    ov = ops_value(s, r)
    cash_parent = (nc["adj"] - s["float_reversal"]) * (1 - MINO_CASH)
    equity = ov["total"] + cash_parent + no["parent"]
    return dict(v=equity / shares, equity=equity, ops=ov, cash_parent=cash_parent, non_op_parent=no["parent"])


def weighted(r=COE, shares=SHARES_MAIN, scen=None):
    sc = scen or SCENARIOS
    return sum(sc[k]["p"] * scenario_value(sc[k], r, shares)["v"] for k in sc)


def solve(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr():
    return solve(lambda r: scenario_value(SCENARIOS["base"], r)["v"], 0.03, 0.30, PRICE)


def reverse_dcf(ronic=0.25):
    """现价隐含增长：以基准 2026 归母核心 NOPAT 为起点，
    (a) 2027-2036 年 NOPAT 恒定增速 g，之后 2.5%；(b) 2027 年起永续增速 g。
    再投资 = 增量 NOPAT ÷ RONIC（显性期 25%，终值期 20%），9% 折现，净现金与非经营资产按基准。"""
    base_nopat = paths(SCENARIOS["base"])["nopat"][2026]
    nc, no = net_cash_block(), non_op_block()
    target_ops = PRICE * SHARES_MAIN - nc["adj"] * (1 - MINO_CASH) - no["parent"]

    def ops10(g):
        n = {2026: base_nopat}
        for y in range(2027, 2037):
            n[y] = n[y - 1] * (1 + g)
        n_next = n[2036] * 1.025
        pv = 0.25 * (n[2026] - (n[2027] - n[2026]) / ronic) / (1 + COE) ** T_STUB
        for y in range(2027, 2037):
            nxt = n[y + 1] if y < 2036 else n_next
            ro = ronic if y < 2036 else 0.20
            pv += (n[y] - (nxt - n[y]) / ro) / (1 + COE) ** (y - 2026 - 0.30)
        pv += n_next * (1 - 0.025 / 0.20) / (COE - 0.025) / (1 + COE) ** (2036 - 2026 - 0.30)
        return pv

    def perp(g):
        return base_nopat * (1 + g) * (1 - g / 0.20) / (COE - g)
    return solve(ops10, -0.10, 0.30, target_ops), solve(perp, -0.05, 0.085, target_ops), target_ops, base_nopat


def normalized_parent_np_2026():
    return {k: paths(s)["nopat"][2026] + s["interest_at"] + s["assoc_norm"] for k, s in SCENARIOS.items()}


def variant(changes):
    """证伪触发：触发假设代入基准与牛情景；熊情景逐项取原值与触发值中较差者
    （unit、x_start 成对替换：触发的单位核心 EBIT 更低时，连同其标定的出口退税起点一起替换）；
    权重改为熊 25%、基准 60%、牛 15%。"""
    sc = copy.deepcopy(SCENARIOS)
    for k in ("base", "bull"):
        sc[k].update(changes)
    bear = sc["bear"]
    for key, val in changes.items():
        if key in ("k", "absorb", "absorb_x", "fade", "float_reversal"):
            bear[key] = max(bear[key], val)
        elif key == "unit" and val < bear["unit"]:
            bear["unit"] = val
            bear["x_start"] = changes.get("x_start", bear["x_start"])
        elif key == "vol_g":
            bear[key] = [min(a, b) for a, b in zip(bear[key], val)]
    sc["base"]["p"], sc["bull"]["p"] = 0.60, 0.15
    return weighted(scen=sc)


FALSIFIERS = {
    # 0.068 是按 2026Q4（6% 退税率）观察值 0.065 加回消费税后的水平，出口退税起点随之取 7%
    "单位核心 EBIT 2026Q4 与 2027Q1 均 < 0.065 元/Wh": dict(unit=0.068, fade=0.03, x_start=X_START_Q3),
    "2027 年锂电池销量 < 1,040 GWh（较 2026 增 < 8%）": dict(vol_g=[0.08, 0.08, 0.07, 0.06, 0.05]),
    "税负自担：2027 年中报境外毛利率 ≤ 28.2%，或 2027Q4 起税金及附加/收入 ≥ 2.5% 且毛利率较 2027Q2 降 ≥ 1.5pct（锂价不升）":
        dict(absorb=0.75, absorb_x=0.80),
    "经营性浮存（负营运资金，口径同 OP_LIABS − OP_ASSETS）在 2027 年任一季末 < 1,600 亿": dict(float_reversal=450.0),
    "匈牙利工厂 2027-06-30 前未量产，或美国 UFLPA/欧盟强制合资等限制落地，海外放量受阻": dict(
        vol_g=[0.15, 0.10, 0.08, 0.06, 0.05], unit=0.084),
}

# 证伪条件 3 的出口退税门槛：2027H1 境外毛利率相对 2026H1 的变化（其他因素不变）。
# 视同内销下收入按离岸价 ÷ 1.13 确认、不再有进项转出，所以报表毛利率降幅小于税负占离岸价的比例。
GM_OVS_H1_2026 = 0.2997             # 2026H1 境外毛利率（2026H1_report 第 16 页）
OVS_LOCAL_H1 = 0.04                 # 境外收入中境外工厂产出的占比（2026H1 约 30/871，2027H1 匈牙利爬坡后略高，按 4%）


def overseas_gm_2027h1(a):
    """自担比例 a 时 2027H1 境外毛利率：出口部分收入 = E ×（1 − r0 − a(r1 − r0)），毛利减少 a(r1 − r0)E。"""
    q1, q2 = XTAX_HIST[3][1], XTAX_HIST[4][1]
    r0 = (q1 * 0.04 + q2 * 0.07) / (q1 + q2)        # 2026H1 出口额加权不得免抵税率（约 5.6%）
    e = 1 - OVS_LOCAL_H1
    gp = GM_OVS_H1_2026 - a * (XTAX_FULL - r0) * e
    rev = 1 - e * (r0 + a * (XTAX_FULL - r0))
    return gp / rev, r0


# TTM（2025Q4～2026Q3）利润构成，税前，合并口径（由 2025 年报、2025/2026 三季报、2026 中报推算）
TTM = dict(core_ebit=836.8, net_interest=68.7, fx_fee=-45.0, other_income=92.9, equity_income=108.45,
           other_inv=9.55, fv=25.9, disposal=1.66, non_op=-0.57, parent_np=876.97, nonrec_after=89.34,
           cmoc_equity_income=74.7, volume=906.0)


def bridge():
    """TTM 归母净利 → 基准 2026 正常化归母净利 的拆分（一次性 / 周期 / 结构 / 口径差）。"""
    core = TTM["core_ebit"] * (1 - TAX) * (1 - MINO_CORE)
    interest = TTM["net_interest"] * (1 - TAX) * (1 - MINO_CASH)
    fx = TTM["fx_fee"] * (1 - TAX) * (1 - MINO_CORE)
    assoc = TTM["cmoc_equity_income"] * CMOC_PARENT_SHARE + (TTM["equity_income"] - TTM["cmoc_equity_income"]) * (1 - MINO_CASH)
    resid = TTM["parent_np"] - (core + interest + fx + TTM["nonrec_after"] + assoc)
    b = SCENARIOS["base"]
    p = paths(b)
    n26 = p["nopat"][2026]
    d_xtax = -p["xtax"][2026] * p["vol"][2026] * 10.0 * (1 - TAX) * (1 - MINO_CORE)
    return dict(core=core, interest=interest, fx=fx, assoc=assoc, nonrec=TTM["nonrec_after"], resid=resid,
                d_assoc=b["assoc_norm"] - assoc, d_interest=b["interest_at"] - interest,
                d_core=n26 - d_xtax - core, d_xtax=d_xtax,
                unit_ttm=TTM["core_ebit"] / TTM["volume"] / 10.0)


def sensitivity():
    """基准情景单项敏感性（其余假设不变）。"""
    out = []
    for key, vals in [("unit", [0.084, 0.090]), ("fade", [0.01, 0.03]), ("absorb", [0.20, 0.60]),
                      ("absorb_x", [0.25, 0.75]), ("x_start", [X_START_Q3]),
                      ("k", [1.3, 2.0]), ("ronic_t", [0.15, 0.25]), ("g_t", [0.020])]:
        for v in vals:
            s = copy.deepcopy(SCENARIOS["base"])
            s[key] = v
            out.append((key, v, scenario_value(s)["v"]))
    for label, vg in [("vol_low", [0.12, 0.10, 0.08, 0.06, 0.04]), ("vol_high", [0.22, 0.16, 0.12, 0.10, 0.08])]:
        s = copy.deepcopy(SCENARIOS["base"])
        s["vol_g"] = vg
        out.append((label, vg[0], scenario_value(s)["v"]))
    return out


def overseas_prod_sensitivity(scale):
    """境外工厂产出整体乘以 scale（三情景同时变化）时的加权 V。"""
    global OVERSEAS_PROD
    saved = OVERSEAS_PROD
    OVERSEAS_PROD = {y: v * scale for y, v in saved.items()}
    try:
        return weighted()
    finally:
        OVERSEAS_PROD = saved


def weighted_with(**changes):
    """按情景改参数后的加权 V，例如 weighted_with(base=dict(absorb_x=0.6))。"""
    sc = copy.deepcopy(SCENARIOS)
    for k, d in changes.items():
        sc[k].update(d)
    return weighted(scen=sc)


def xtax_robustness():
    """出口退税新假设的稳健性：起点口径、基准起点取 7%、境外工厂产出、P/V = 0.90 时的基准自担比例。"""
    hist_cost = sum((ov - de) * r for _, ov, de, r in XTAX_HIST)
    p = paths(SCENARIOS["base"])
    ei_2027 = export_share(2027, p["vol"][2027]) * asp(2027)              # 基准 2027 年每 Wh 出口额（元）
    start_per_wh = hist_cost / HIST_VOLUME / 10.0 / ei_2027               # 按每 Wh 口径折算的起点
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if PRICE / weighted_with(base=dict(absorb_x=mid)) < 0.90:
            lo = mid
        else:
            hi = mid
    # 2026 年出口额核对：H1 境外收入 + 下半年收入（全年约 6,000 − H1 2,769.17）× 31.46% − 境外工厂产出
    export_2026_check = 871.29 + (REV_2026_EST - 2769.17) * 0.3146 - OVERSEAS_PROD[2026] * ASP_2026 * 10.0
    no_x = {k: dict(absorb_x=0.0) for k in SCENARIOS}
    return dict(ei_2027=ei_2027, start_per_wh=start_per_wh,
                v_start_per_wh=weighted_with(base=dict(x_start=start_per_wh), bull=dict(x_start=start_per_wh)),
                v_base_start7=weighted_with(base=dict(x_start=X_START_Q3)),
                v_prod0=overseas_prod_sensitivity(0.0), v_prod05=overseas_prod_sensitivity(0.5),
                v_prod15=overseas_prod_sensitivity(1.5), absorb_x_pv090=lo,
                export_2026_check=export_2026_check, v_no_xtax=weighted_with(**no_x))


def main():
    nc, no = net_cash_block(), non_op_block()
    print("== 股本 ==")
    print(f"主口径股本 {SHARES_MAIN:.4f} 亿股（总股本 {SHARES_TOTAL} − 拟注销 {BUYBACK_CANCEL:.4f}）；"
          f"剔除全部回购专户 {SHARES_EX_TREASURY:.4f} 亿股")
    h_cny = H_PRICE_HKD * HKD_CNY
    mcap_mix = (SHARES_TOTAL - H_SHARES) * PRICE + H_SHARES * h_cny
    print(f"A 价×全部股份 {PRICE * SHARES_TOTAL:,.1f}；H 股 {H_PRICE_HKD} 港元≈{h_cny:.1f} 元（较 A 溢价 {h_cny / PRICE - 1:.1%}），"
          f"A/H 各按本价市值 {mcap_mix:,.1f}")
    print("== 现金与浮存（合并口径）==")
    print(f"现金类 {nc['gross']:,.1f}；有息负债 {nc['debt']:,.1f}；受限 {RESTRICTED}；长期应付款 {LT_PAYABLE}；"
          f"衍生净额 {DERIV_ASSET - DERIV_LIAB:.2f}；未扣备付净现金 {nc['pre_reserve']:,.1f}")
    print(f"经营备付（1 个月付现成本）{nc['reserve']:,.1f}；经调整净现金 {nc['adj']:,.1f}（>0，无杠杆口径）；"
          f"归母份额 {nc['adj'] * (1 - MINO_CASH):,.1f}（少数股东 {MINO_CASH:.1%}）")
    print(f"经营性浮存 {nc['float_total']:,.1f} = 贸易浮存 {nc['trade_float']:,.1f} + 客户预收 {nc['prepay_float']:,.1f}"
          f" + 预计负债 {OP_LIABS['provisions']:,.1f} + 应计 {nc['accrued']:,.1f} − 其他经营资产 "
          f"{OP_ASSETS['other_rece'] + OP_ASSETS['contract_asset'] + OP_ASSETS['other_ca'] + OP_ASSETS['long_rece']:,.1f}；"
          f"严格自由现金（未扣备付净现金 − 浮存）{nc['free_strict']:,.1f}")
    print(f"非经营资产：洛钼市值 {no['cmoc_mv']:,.1f}（归母 {no['cmoc_parent']:,.1f}）；其他长投账面 {no['other_ltei']:,.1f}"
          f"（归母 {no['other_ltei'] * (1 - MINO_CASH):,.1f}）；其他权益工具 {OTHER_EQUITY_INST}（归母 {OTHER_EQUITY_INST * (1 - MINO_CASH):,.1f}）；"
          f"其他非流动金融资产 {OTHER_NC_FIN}（归母 {OTHER_NC_FIN * (1 - MINO_CASH):,.1f}）；合并 {no['group']:,.1f}；归母 {no['parent']:,.1f}")
    print(f"归母净现金与非经营资产合计每股 {(nc['adj'] * (1 - MINO_CASH) + no['parent']) / SHARES_MAIN:.1f} 元")
    print("== 出口退税（财政部 税务总局公告 2026 年第 2 号）==")
    hist_cost = sum((ov - de) * r for _, ov, de, r in XTAX_HIST)
    print("标定期从中国出口额（境外收入 − 德国产出）与不得免抵税率：" + "；".join(
        f"{n} {ov - de:,.1f}×{r:.0%}" for n, ov, de, r in XTAX_HIST))
    print(f"起点（基准、牛）= 出口额加权 {X_START_CYCLE:.2%}；标定期合计出口 {sum(ov - de for _, ov, de, _ in XTAX_HIST):,.1f}、"
          f"不得免抵税额 {hist_cost:.1f}，摊到 {HIST_VOLUME} GWh 为 {hist_cost / HIST_VOLUME / 10:.4f} 元/Wh；起点（熊）= {X_START_Q3:.0%}")
    print("境外工厂产出 GWh（德国/匈牙利/西班牙/印尼=合计）：" + "；".join(
        f"{y} {'/'.join(str(x) for x in v)}={OVERSEAS_PROD[y]:.0f}" for y, v in OVERSEAS_PLANTS.items()))
    for k in ["bear", "base", "bull"]:
        s = SCENARIOS[k]
        p = paths(s)
        print(f"[{k}] 起点 {s['x_start']:.2%}，自担 {s['absorb_x']:.0%}")
        for y in YEARS:
            d = xtax_detail(y, s, p["vol"][y])
            print(f"   {y}: 出口占比 {d['share']:.1%} 出口收入 {d['export_rev']:,.0f} 税率 {d['rate']:.2%} 增量 {d['inc']:+.2%}"
                  f" 每 Wh 自担 {d['per_wh']:.4f} 税前 {d['pretax']:,.1f}（消费税每 Wh {p['ctax'][y]:.4f}）")
    bp0 = paths(SCENARIOS["base"])
    d27 = xtax_detail(2027, SCENARIOS["base"], bp0["vol"][2027])
    print(f"基准 2027 年全额自担：较 6% 退税率多税前 {d27['export_rev'] * (XTAX_FULL - XTAX_RATE[2026]):.1f} 亿，"
          f"较标定期起点多 {d27['export_rev'] * d27['inc']:.1f} 亿；自担 {SCENARIOS['base']['absorb_x']:.0%} 后 {d27['pretax']:.1f} 亿")
    y = 2028
    both = bp0["ctax"][y] + bp0["xtax"][y]
    print(f"两税满额（{y} 年，基准）：消费税 {bp0['ctax'][y]:.4f} + 出口退税 {bp0['xtax'][y]:.4f} = {both:.4f} 元/Wh，"
          f"占扣税前单位核心 EBIT {both / bp0['unit_pre'][y]:.1%}；归母 NOPAT 减少 {both * bp0['vol'][y] * 10 * (1 - TAX) * (1 - MINO_CORE):,.0f} 亿"
          f"（其中出口退税 {bp0['xtax'][y] * bp0['vol'][y] * 10 * (1 - TAX) * (1 - MINO_CORE):,.0f}）")
    for a in (0.25, 0.50, 0.80, 1.00):
        gm, r0 = overseas_gm_2027h1(a)
        print(f"出口退税自担 {a:.0%} 时 2027H1 境外毛利率 {gm:.2%}（较 2026H1 {gm - GM_OVS_H1_2026:+.2%}；2026H1 出口加权税率 {r0:.2%}）")
    rb = xtax_robustness()
    print(f"稳健性：按每 Wh 口径的起点 {rb['start_per_wh']:.2%}（÷ 基准 2027 年每 Wh 出口额 {rb['ei_2027']:.3f} 元）→ 加权 V {rb['v_start_per_wh']:.2f}；"
          f"基准起点取 7% → 加权 V {rb['v_base_start7']:.2f}（P/V {PRICE / rb['v_base_start7']:.3f}）；"
          f"境外工厂产出 ×0 / ×0.5 / ×1.5 → 加权 V {rb['v_prod0']:.2f} / {rb['v_prod05']:.2f} / {rb['v_prod15']:.2f}；"
          f"基准出口退税自担 {rb['absorb_x_pv090']:.1%} 时 P/V = 0.90")
    bx = paths(SCENARIOS["base"])
    print(f"核对：2026 年从中国出口额按报表估 {rb['export_2026_check']:,.0f}，模型 {xtax_detail(2026, SCENARIOS['base'], VOL_2026)['export_rev']:,.0f}；"
          f"不计出口退税的加权 V {rb['v_no_xtax']:.2f}（出口退税一项 {weighted() - rb['v_no_xtax']:+.2f}）；"
          f"基准每 Wh 两税扣减 2026 {bx['ctax'][2026] + bx['xtax'][2026]:.4f}、2027 {bx['ctax'][2027] + bx['xtax'][2027]:.4f}")
    print("== 三情景（股权成本 9%）==")
    for k in ["bear", "base", "bull"]:
        s = SCENARIOS[k]
        p = paths(s)
        sv = scenario_value(s)
        print(f"[{k}] p={s['p']} V={sv['v']:.2f} 元/股 | 经营 {sv['ops']['total']:,.0f}"
              f"（终值占 {sv['ops']['tv'] / sv['ops']['total']:.0%}）+ 现金 {sv['cash_parent']:,.0f}"
              f" + 非经营 {sv['non_op_parent']:,.0f}；显性期增量回报 {p['inc_ret']:.0%}")
        for y in YEARS:
            g = "" if y == 2026 else f" g={p['nopat'][y] / p['nopat'][y - 1] - 1:+.1%}"
            print(f"   {y}: 销量 {p['vol'][y]:,.0f} GWh 单位 {p['unit'][y]:.4f}（扣税前 {p['unit_pre'][y]:.4f}）"
                  f" EBIT {p['ebit'][y]:,.0f} NOPAT {p['nopat'][y]:,.0f}{g} 再投资 {p['reinv'][y]:,.0f}"
                  f"（{p['reinv'][y] / p['nopat'][y]:.0%}） OE {p['oe'][y]:,.0f}")
        print(f"   终值：2032 NOPAT {p['nopat_next']:,.0f} OE {p['oe_next']:,.0f} g={s['g_t']:.1%} RONIC_T={s['ronic_t']:.0%}")
    vw = weighted()
    print(f"加权 V = {vw:.2f}；P/V = {PRICE / vw:.3f}")
    vw_ex = weighted(shares=SHARES_EX_TREASURY)
    print(f"对照：剔除全部回购专户股本 加权 V = {vw_ex:.2f}；P/V = {PRICE / vw_ex:.3f}")
    print(f"股权成本 8%：加权 V = {weighted(0.08):.2f}（基准 {scenario_value(SCENARIOS['base'], 0.08)['v']:.2f}）；"
          f"10%：加权 V = {weighted(0.10):.2f}（基准 {scenario_value(SCENARIOS['base'], 0.10)['v']:.2f}）")
    print(f"现价隐含回报（基准现金流）= {implied_irr():.2%}")
    g10, gp, tgt, bn = reverse_dcf()
    print(f"反向 DCF：现价对应归母经营价值 {tgt:,.0f}；以 2026 归母核心 NOPAT {bn:,.0f} 起算，"
          f"隐含 2027-2036 年 NOPAT 年增 {g10:.2%}（之后 2.5%）；或永续增速 {gp:.2%}")
    print("基准单项敏感性：" + "；".join(f"{k}={v:.4g} → {vv:.1f}" for k, v, vv in sensitivity()))
    print(f"H 股价折人民币 {H_PRICE_HKD * HKD_CNY:.1f} 元对应 P/V {H_PRICE_HKD * HKD_CNY / vw:.3f}（仅参考）")
    bp = paths(SCENARIOS["base"])
    oe_g = [bp["oe"][y] / bp["oe"][y - 1] - 1 for y in YEARS[1:]]
    rr = sum(bp["reinv"][y] for y in YEARS[1:]) / sum(bp["nopat"][y] for y in YEARS[1:])
    print("基准所有者收益增速 2027-2031：" + "，".join(f"{g:+.1%}" for g in oe_g) +
          f"；2027-2031 平均再投资率 {rr:.1%}；显性期增量回报 {bp['inc_ret']:.1%}")
    br = bridge()
    print(f"TTM 拆分（归母税后）：核心 {br['core']:.1f} + 净利息 {br['interest']:.1f} + 汇兑与手续费 {br['fx']:.1f}"
          f" + 一次性（公司口径非经常）{br['nonrec']:.1f} + 联营 {br['assoc']:.1f} + 口径差 {br['resid']:.1f} = {TTM['parent_np']:.1f}；"
          f"TTM 单位核心 EBIT {br['unit_ttm']:.4f} 元/Wh")
    print(f"桥：TTM {TTM['parent_np']:.1f} − 一次性 {br['nonrec']:.1f} + 加回汇兑 {-br['fx']:.1f} + 联营正常化 {br['d_assoc']:.1f}"
          f" + 利息正常化 {br['d_interest']:.1f} + 核心正常化（单位与消费税）{br['d_core']:.1f} + 出口退税增量 {br['d_xtax']:.1f}"
          f" − 口径差 {br['resid']:.1f} = {TTM['parent_np'] - br['nonrec'] - br['fx'] + br['d_assoc'] + br['d_interest'] + br['d_core'] + br['d_xtax'] - br['resid']:.1f}")
    nn = normalized_parent_np_2026()
    print("2026 正常化归母净利（核心 NOPAT + 税后净利息 + 正常化联营）：" +
          "，".join(f"{k} {v:,.1f}" for k, v in nn.items()))
    for name, ch in FALSIFIERS.items():
        print(f"证伪：{name} → 触发后加权 V {variant(ch):.2f}")
    print(f"   税负自担拆开：仅出口退税自担 80% → {variant(dict(absorb_x=0.80)):.2f}；仅消费税自担 75% → {variant(dict(absorb=0.75)):.2f}")
    print("分档价格（V 不变）：≤{:.1f} 明显低估；{:.1f}～{:.1f} 温和低估；{:.1f}～{:.1f} 大致合理；>{:.1f} 偏贵"
          .format(0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))
    mcap = PRICE * SHARES_TOTAL
    ev = mcap - nc["pre_reserve"] - no["group"] + MINORITY_EQUITY
    print(f"EV（A 价市值 − 未扣备付净现金 − 非经营资产 + 少数股东权益）{ev:,.0f}；EV/TTM 核心 EBIT 836.8 = {ev / 836.8:.1f}×；"
          f"EV/基准 2026 正常化核心 EBIT {bp['ebit'][2026]:,.0f} = {ev / bp['ebit'][2026]:.1f}×")
    sb = scenario_value(SCENARIOS["base"])
    print(f"分部加总（基准）：核心电池 {sb['ops']['total']:,.0f} + 洛钼归母 {no['cmoc_parent']:,.1f} + 其他投资归母 "
          f"{no['parent'] - no['cmoc_parent']:,.1f} + 归母净现金 {nc['adj'] * (1 - MINO_CASH):,.1f} = {sb['equity']:,.1f} → 每股 {sb['v']:.1f}")
    print(f"股息率（TTM 每股 8.368）{8.368 / PRICE:.2%}；回购 200～400 亿占 A 价市值 {200 / mcap:.2%}～{400 / mcap:.2%}")


if __name__ == "__main__":
    main()
