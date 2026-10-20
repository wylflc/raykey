#!/usr/bin/env python3
"""顺丰控股（002352）独立估值：OI-291 b09 深度版。

金额单位：亿元人民币（另注明者除外）；每股价值单位：元/股。
价格日 2026-10-20（北京时间收盘），估值基准日同日。
所有输入写在脚本内，出处见同目录正文
data/experiments/exp_independent_pool_2026q3/b09/companies/002352_顺丰控股.md。

口径要点：
- 归母口径；租赁视为经营成本（所有者收益已扣使用权资产折旧、租赁利息，并另扣租赁现金支付高出
  损益费用的差额），因此租赁负债不计入净负债，避免重复扣除。
- 经调整净现金（不含租赁）为负 → 按框架用有杠杆口径：
  股权价值 = 经营所有者收益现值 − 经调整净负债税后利息的现值（按现规模永续滚动、9% 折现）+ 非经营资产。
- 经营所有者收益 = 经营归母净利（剔除全部借款利息、现金及结构性存款收益、极兔与其他计入
  非经营资产的联营企业投资收益）×（1 − 再投资率）。
- 年度现金流按年中折现；2026 下半年现金流放在 t = 0.1 年。
- 可转债：2025-07 发行的 29.5 亿港元 H 股可转债已于 2026-07-08 按 100.5% 全额赎回，无未转股余额，
  不做转股情景。
"""

from __future__ import annotations

# ----------------------------------------------------------------------------
# 1. 股本与价格
# ----------------------------------------------------------------------------
PRICE_A = 31.49                      # A 股 2026-10-20 收盘（元）
PRICE_H_HKD = 29.20                  # H 股 2026-10-20 收盘（港元）
HKD_CNY = 0.8526                     # 2026-10-20 港元兑人民币
SHARES_A = 46.39270409               # 亿股，2026-09-18 注销 1.6016 亿股回购 A 股后
SHARES_H = 4.65877669                # 亿股，含 2026-06-09 向极兔发行的 2.25877669 亿股
SHARES_TOTAL = SHARES_A + SHARES_H   # 51.05148078 亿股 = brief 总股本 51.0515
H_TREASURY = 0.143712                # 亿股，H 股回购作库存股持有（7-31 前 716.36 万股 + 8-31~9-11 约 720.76 万股）
SHARES_EX_TREASURY = SHARES_TOTAL - H_TREASURY

# ----------------------------------------------------------------------------
# 2. 经调整净现金（2026-06-30 资产负债表 + 期后已发生的资本分配）
# ----------------------------------------------------------------------------
CASH = 263.4978                 # 货币资金
TRADING_FA = 210.1719           # 交易性金融资产（结构性存款 208.2960 + 基金及其他 1.8759）
FIXED_INCOME_CERT = 0.50        # 其他流动资产中的固定收益凭证
RESTRICTED = 13.8369            # 受限货币资金（法定存款准备金 10.0359 + 其他 3.8010）
TTM_REVENUE = 3168.75
OPER_RESERVE = 0.02 * TTM_REVENUE   # 经营备付：TTM 营收的 2%
COD_NET_PAYABLE = 12.3802 - 5.9727  # 应付代收货款 − 应收代收货款（客户资金）
DIV_INTERIM_2026 = 24.95        # 2026 中期 0.49 元/股（A 股 9-17 除息、H 股 10-16 派发）
BUYBACK_A_POST = 59.99593 - 58.80256   # 7-1~7-21 回购 353.8 万股 A 股
BUYBACK_H_POST = (4.497 - 0.3844) * 0.87  # 6-30 后 H 股回购约 4.11 亿港元
CB_REDEMPTION_PREMIUM = 0.12    # 可转债按 100.5% 赎回高于账面的部分
FENGCHAO_INJECTION = 3.05       # 8 月丰巢增资上限（现金转为其他权益工具）
FIN_DEBT = 430.1616             # 有息负债（不含租赁）：银行借款 227.9078 + 债券及可转债 195.1364 + 供应链金融 1.6503 + 其他 5.4671
TRADING_FL = 1.0447             # 交易性金融负债
LEASE_LIAB = 154.0452           # 租赁负债（含一年内到期 57.2250），不计入净负债，仅对照

cash_like = CASH + TRADING_FA + FIXED_INCOME_CERT
net_cash_adj = (cash_like - RESTRICTED - OPER_RESERVE - COD_NET_PAYABLE - DIV_INTERIM_2026
                - BUYBACK_A_POST - BUYBACK_H_POST - CB_REDEMPTION_PREMIUM - FENGCHAO_INJECTION
                - FIN_DEBT - TRADING_FL)
net_debt_adj = -net_cash_adj

DEBT_RATE = 0.027   # 借款实际平均利率：2026H1 年化约 3.0%，9 月 100 亿离岸人民币债 1.75%/1.85% 置换后约 2.5~2.6%
TAX = 0.25

# ----------------------------------------------------------------------------
# 3. 非经营资产（各情景折扣不同）
# ----------------------------------------------------------------------------
JT_SHARES_YI = 9.71958328       # 持有极兔 B 类股（亿股），约 10%，交割后 5 年锁定
PRICE_JT_HKD = 9.20             # 极兔 2026-10-20 收盘（港元）
JT_MV = JT_SHARES_YI * PRICE_JT_HKD * HKD_CNY
OTHER_EQUITY_INV = 56.52195 + FENGCHAO_INJECTION  # 其他权益工具投资（主要为丰巢，第三层次公允价值）
OTHER_NC_FA = 9.57014           # 其他非流动金融资产
ASSOC_EX_JT_EX_EZHOU = 51.0     # 长期股权投资 141.77 − 极兔约 71.9 − 湖北国际物流机场合营约 18.9（后者视为经营资产），估算值
PARK_UPLIFT_BULL = 15.0         # 牛市情景：产业园经 REIT 盘活的增值（2025 年处置三家项目公司税后收益 5.9 亿）

NONOP_HAIRCUT = {
    #            极兔   其他权益工具  其他非流动金融资产  联营(除极兔/鄂州)  产业园增值
    "bear": dict(jt=0.65, oei=0.25, ncfa=0.70, assoc=0.50, park=0.0),
    "base": dict(jt=0.80, oei=0.40, ncfa=0.80, assoc=0.70, park=0.0),
    "bull": dict(jt=0.90, oei=0.70, ncfa=0.90, assoc=0.90, park=1.0),
}


def nonop(scn: str) -> float:
    h = NONOP_HAIRCUT[scn]
    return (JT_MV * h["jt"] + OTHER_EQUITY_INV * h["oei"] + OTHER_NC_FA * h["ncfa"]
            + ASSOC_EX_JT_EX_EZHOU * h["assoc"] + PARK_UPLIFT_BULL * h["park"])


# ----------------------------------------------------------------------------
# 4. 2026 正常化归母净利（含净利息，剔除一次性）与经营归母净利
# ----------------------------------------------------------------------------
KF_H1_2026 = 49.7495            # 2026H1 扣非归母
KF_2025 = 92.6379               # 2025 扣非归母
# 三季度：7 月合计收入 +6.12%，8 月 +2.83%，9 月 +6.34% → 三季度物流收入约 +5.1%；
# 速运物流量 8 月 −8.53%、9 月 −7.25%，单票 +7.8%/+7.7%；2025Q3 扣非 22.27、Q4 24.86。
# 布伦特油价 2026Q3 均价约 93 美元（2025Q3 约 67），10-20 为 109 美元 → 下半年燃油成本压力大于二季度。
KF_Q3E = {"bear": 21.8, "base": 23.4, "bull": 25.0}
KF_Q4E = {"bear": 22.5, "base": 25.2, "bull": 26.8}
STRUCT_DEPOSIT_AT = 3.6         # 结构性存款及固定收益凭证收益（税后、归母），2026 全年
OIL_NORM_ADD = {"bear": 0.0, "base": 2.5, "bull": 4.0}   # 周期项：下半年油价高于 75 美元中枢的超额燃油成本（税后）加回
CYCLICAL_ADJ = {"bear": -1.5, "base": 0.0, "bull": 0.0}  # 熊市：国际货代运价正常化
FX_H1_ADJ = -0.62 * (1 - 0.25)   # 2026H1 汇兑收益 0.62 亿（税前）计入扣非，正常化剔除

norm_np_2026 = {s: KF_H1_2026 + KF_Q3E[s] + KF_Q4E[s] + STRUCT_DEPOSIT_AT + OIL_NORM_ADD[s] + CYCLICAL_ADJ[s] + FX_H1_ADJ
                for s in ("bear", "base", "bull")}
kf_2026e = {s: KF_H1_2026 + KF_Q3E[s] + KF_Q4E[s] for s in ("bear", "base", "bull")}

# 经营归母净利 = 正常化归母净利 − 极兔投资收益 − 其他非经营联营收益 + 税后净融资成本
JT_INCOME_2026 = 1.9            # 2026-06-09 交割后按 10% 确认；极兔 2026H1 利润 2.59 亿美元
JT_INCOME_2027 = 3.8
ASSOC_INCOME = 0.5
NET_FIN_COST_AT_2026 = (10.8 * (1 - TAX)) - (2.0 * (1 - TAX)) - STRUCT_DEPOSIT_AT  # 借款利息 − 存款利息 − 结构性存款收益（税后）

op_np_2026 = {s: norm_np_2026[s] - JT_INCOME_2026 - ASSOC_INCOME + NET_FIN_COST_AT_2026
              for s in norm_np_2026}
JT_INCOME_H2, ASSOC_INCOME_H2, NET_FIN_COST_AT_H2 = 1.7, 0.25, NET_FIN_COST_AT_2026 / 2
# 2026H2 经营归母净利（实际预期，含油价拖累，不加回周期项）
op_np_h2_2026 = {s: KF_Q3E[s] + KF_Q4E[s] + STRUCT_DEPOSIT_AT / 2 - JT_INCOME_H2 - ASSOC_INCOME_H2 + NET_FIN_COST_AT_H2
                 for s in ("bear", "base", "bull")}

# ----------------------------------------------------------------------------
# 5. 情景：经营归母净利增速、再投资率、终值
# ----------------------------------------------------------------------------
YEARS = [2027, 2028, 2029, 2030, 2031]
SCEN = {
    "bear": dict(p=0.25, growth=[-0.04, 0.02, 0.03, 0.03, 0.025], rr_h2=0.30,
                 rr=[0.30, 0.30, 0.28, 0.26, 0.24], g_t=0.020, roic_t=0.10),
    "base": dict(p=0.50, growth=[0.05, 0.07, 0.06, 0.05, 0.04], rr_h2=0.31,
                 rr=[0.29, 0.28, 0.26, 0.23, 0.21], g_t=0.025, roic_t=0.14),
    "bull": dict(p=0.25, growth=[0.10, 0.11, 0.09, 0.07, 0.05], rr_h2=0.31,
                 rr=[0.33, 0.32, 0.30, 0.27, 0.23], g_t=0.025, roic_t=0.16),
}
T_H2 = 0.1                       # 2026H2 现金流折现时点（年）
T_FIRST = 0.7                    # 2027 年中距估值日约 0.7 年


def flows(scn: str):
    """返回 [(t, 所有者收益)]、终值时点与终值、逐年经营归母净利。"""
    c = SCEN[scn]
    np26 = op_np_2026[scn]
    oe = [(T_H2, op_np_h2_2026[scn] * (1 - c["rr_h2"]))]
    np_t = np26
    path = []
    for i, (g, rr) in enumerate(zip(c["growth"], c["rr"])):
        np_t *= 1 + g
        path.append(np_t)
        oe.append((T_FIRST + i, np_t * (1 - rr)))
    rr_t = c["g_t"] / c["roic_t"]
    oe_next = np_t * (1 + c["g_t"]) * (1 - rr_t)
    return oe, (T_FIRST + len(YEARS) - 1, oe_next, c["g_t"]), path, rr_t


def equity_value(scn: str, r: float, levered: bool = True):
    oe, (t_tv, oe_next, g_t), _, _ = flows(scn)
    pv_oe = sum(cf / (1 + r) ** t for t, cf in oe)
    tv = oe_next / (r - g_t)
    pv_tv = tv / (1 + r) ** t_tv
    if levered:
        pv_debt = net_debt_adj * DEBT_RATE * (1 - TAX) / r
    else:
        pv_debt = net_debt_adj     # 无杠杆口径：全额扣除经调整净负债本金
    eq = pv_oe + pv_tv - pv_debt + nonop(scn)
    return eq, pv_oe, pv_tv, pv_debt


def v_per_share(scn: str, r: float = 0.09, levered: bool = True, shares: float = SHARES_TOTAL) -> float:
    return equity_value(scn, r, levered)[0] / shares


def weighted(r: float = 0.09, levered: bool = True, shares: float = SHARES_TOTAL) -> float:
    return sum(SCEN[s]["p"] * v_per_share(s, r, levered, shares) for s in SCEN)


def solve(fn, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (fn(mid) - target) * (fn(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def verdict(pv: float) -> str:
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


# ----------------------------------------------------------------------------
# 6. 交叉验证输入
# ----------------------------------------------------------------------------
PARENT_EQUITY = 1027.86          # 2026-06-30 归母权益
MINORITY_BOOK = 114.82           # 2026-06-30 少数股东权益（KLN 48.48% 约 102 亿）
KLN_SHARES_YI = 18.0             # 嘉里物流总股本约 18 亿股（近似值，未逐一核实）
PRICE_KLN_HKD = 5.76             # 嘉里物流 0636.HK 2026-10-20 收盘（港元）
KLN_PARENT_NP_2025 = 5.65        # KLN 2025 年对归母净利贡献
# 2025 核心 EBIT = 利润总额 149.18 − 非经常性损益税前合计 24.32 + 借款利息净额 12.52 − 利息收入 2.63
#                 + 汇兑损失 1.04 + 权益法亏损 0.62（剔除联营）
EBIT_CORE_2025 = 149.18 - 24.32 + 12.52 - 2.63 + 1.04 + 0.62
# 2026H1 核心 EBIT = 利润总额 77.75 − 非经常性损益税前合计 8.35 + 借款利息净额 5.405 − 利息收入 1.00
#                   − 汇兑收益 0.62 − 权益法收益 1.71
EBIT_CORE_H1_2026 = 77.75 - 8.35 + 5.405 - 1.00 - 0.62 - 1.71


# ----------------------------------------------------------------------------
# 7. 证伪情景（触发后的独立 V）
# ----------------------------------------------------------------------------
def v_with(overrides: dict) -> float:
    """临时改三情景参数，返回加权 V。"""
    saved = {k: dict(v) for k, v in SCEN.items()}
    saved_np = dict(op_np_2026)
    saved_h2 = dict(op_np_h2_2026)
    try:
        for s in SCEN:
            if "growth_shift" in overrides:
                SCEN[s]["growth"] = [g + overrides["growth_shift"] for g in SCEN[s]["growth"]]
            if "np_mult" in overrides:
                op_np_2026[s] = saved_np[s] * overrides["np_mult"]
                op_np_h2_2026[s] = saved_h2[s] * overrides["np_mult"]
            if "rr_add" in overrides:
                SCEN[s]["rr"] = [x + overrides["rr_add"] for x in SCEN[s]["rr"]]
                SCEN[s]["rr_h2"] += overrides["rr_add"]
            if "roic_t_add" in overrides:
                SCEN[s]["roic_t"] += overrides["roic_t_add"]
        if "prob" in overrides:
            for s, p in overrides["prob"].items():
                SCEN[s]["p"] = p
        return weighted()
    finally:
        for k, v in saved.items():
            SCEN[k] = v
        op_np_2026.clear()
        op_np_2026.update(saved_np)
        op_np_h2_2026.clear()
        op_np_h2_2026.update(saved_h2)


def main():
    print("=== 股本与市值 ===")
    mcap_a_all = PRICE_A * SHARES_TOTAL
    price_h_cny = PRICE_H_HKD * HKD_CNY
    mcap_mixed = PRICE_A * SHARES_A + price_h_cny * SHARES_H
    print(f"总股本 {SHARES_TOTAL:.4f} 亿股（A {SHARES_A:.4f} + H {SHARES_H:.4f}）；H 股库存股约 {H_TREASURY:.4f}；剔除后 {SHARES_EX_TREASURY:.4f}")
    print(f"A 股价×总股本 {mcap_a_all:.1f} 亿；A 按 A 价 + H 按 H 价 {mcap_mixed:.1f} 亿"
          f"（H 股 {PRICE_H_HKD} 港元 = {price_h_cny:.2f} 元，较 A 折价 {1 - price_h_cny / PRICE_A:.1%}）")

    print("\n=== 经调整净现金（不含租赁） ===")
    print(f"现金类 {cash_like:.2f} − 受限 {RESTRICTED:.2f} − 经营备付 {OPER_RESERVE:.2f} − 代收货款净额 {COD_NET_PAYABLE:.2f}"
          f" − 中期股息 {DIV_INTERIM_2026:.2f} − 期后回购 {BUYBACK_A_POST + BUYBACK_H_POST:.2f} − 可转债赎回溢价 {CB_REDEMPTION_PREMIUM:.2f}"
          f" − 丰巢增资 {FENGCHAO_INJECTION:.2f} − 有息负债 {FIN_DEBT:.2f} − 交易性金融负债 {TRADING_FL:.2f}")
    print(f"net_cash_adj = {net_cash_adj:.1f} 亿（为负 → 有杠杆口径）；含租赁负债则为 {net_cash_adj - LEASE_LIAB:.1f} 亿")
    print(f"经调整净负债税后利息 {net_debt_adj * DEBT_RATE * (1 - TAX):.2f} 亿/年（利率 {DEBT_RATE:.1%}），"
          f"9% 永续现值 {net_debt_adj * DEBT_RATE * (1 - TAX) / 0.09:.1f} 亿")

    print("\n=== 非经营资产 ===")
    print(f"极兔 10% 市值 {JT_MV:.1f} 亿（{PRICE_JT_HKD} 港元×{JT_SHARES_YI:.4f} 亿股×{HKD_CNY}）；"
          f"其他权益工具 {OTHER_EQUITY_INV:.1f}；其他非流动金融资产 {OTHER_NC_FA:.1f}；联营（除极兔、鄂州机场）{ASSOC_EX_JT_EX_EZHOU:.1f}")
    for s in ("bear", "base", "bull"):
        print(f"  {s}: 折扣 {NONOP_HAIRCUT[s]} → 非经营资产合计 {nonop(s):.1f} 亿")

    print("\n=== 2026 正常化归母净利（含净利息，剔除一次性） ===")
    for s in ("bear", "base", "bull"):
        print(f"  {s}: 扣非 H1 {KF_H1_2026:.2f} + Q3E {KF_Q3E[s]} + Q4E {KF_Q4E[s]}（扣非全年 {kf_2026e[s]:.1f}，同比 {kf_2026e[s] / KF_2025 - 1:+.1%}）"
              f" + 结构性存款 {STRUCT_DEPOSIT_AT} + 油价周期加回 {OIL_NORM_ADD[s]} + 货代周期 {CYCLICAL_ADJ[s]} + 汇兑剔除 {FX_H1_ADJ:.2f}"
              f" = {norm_np_2026[s]:.1f}；经营归母净利 {op_np_2026[s]:.1f}（2026H2 实际预期 {op_np_h2_2026[s]:.1f}）")
    print(f"  税后净融资成本 2026E {NET_FIN_COST_AT_2026:.2f} 亿；极兔投资收益 2026E {JT_INCOME_2026}、2027E {JT_INCOME_2027}（不进经营收益）")

    print("\n=== 三情景（股权成本 9%，有杠杆口径） ===")
    for s in ("bear", "base", "bull"):
        eq, pv_oe, pv_tv, pv_debt = equity_value(s, 0.09)
        oe, (t_tv, oe_next, g_t), path, rr_t = flows(s)
        v = eq / SHARES_TOTAL
        print(f"[{s}] p={SCEN[s]['p']:.2f}  V = {v:.2f} 元/股；剔除 H 库存股 {eq / SHARES_EX_TREASURY:.2f}")
        print("   增速 2027-2031: " + ", ".join(f"{g:+.1%}" for g in SCEN[s]["growth"]) + f"；终值增速 {g_t:.1%}")
        print("   经营归母净利 2027-2031: " + ", ".join(f"{x:.1f}" for x in path))
        print("   再投资率 2027-2031: " + ", ".join(f"{x:.0%}" for x in SCEN[s]["rr"]) + f"；终值再投资率 {rr_t:.1%}（g/ROIC {SCEN[s]['roic_t']:.0%}）")
        print("   所有者收益: " + ", ".join(f"t={t:.1f}:{cf:.1f}" for t, cf in oe) + f"；终值首年 OE {oe_next:.1f}")
        print(f"   PV(OE) {pv_oe:.1f} + PV(终值) {pv_tv:.1f}（终值占经营价值 {pv_tv / (pv_oe + pv_tv):.0%}）"
              f"− 净负债利息现值 {pv_debt:.1f} + 非经营 {nonop(s):.1f} = 股权 {eq:.1f} 亿")
        rr_avg = sum(SCEN[s]["rr"]) / len(SCEN[s]["rr"])
        g_avg = (path[-1] / op_np_2026[s]) ** (1 / 5) - 1
        print(f"   2027-2031 平均再投资率 {rr_avg:.1%}，经营归母净利 5 年复合 {g_avg:.1%}，隐含增量回报 {g_avg / rr_avg:.1%}")

    vw = weighted()
    pv = PRICE_A / vw
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {pv:.3f} → {verdict(pv)}")
    print(f"剔除 H 股库存股：加权 V = {weighted(shares=SHARES_EX_TREASURY):.2f}，P/V = {PRICE_A / weighted(shares=SHARES_EX_TREASURY):.3f}")
    print(f"无杠杆口径（全额扣经调整净负债 {net_debt_adj:.1f} 亿）：bear {v_per_share('bear', levered=False):.2f} / base {v_per_share('base', levered=False):.2f}"
          f" / bull {v_per_share('bull', levered=False):.2f}，加权 {weighted(levered=False):.2f}，P/V {PRICE_A / weighted(levered=False):.3f}")
    print(f"H 股（{price_h_cny:.2f} 元）对同一 V 的 P/V = {price_h_cny / vw:.3f}")
    print(f"各档价格（V 不变）：≤{0.75 * vw:.2f} 明显低估；{0.75 * vw:.2f}~{0.90 * vw:.2f} 温和低估；"
          f"{0.90 * vw:.2f}~{1.10 * vw:.2f} 大致合理；>{1.10 * vw:.2f} 偏贵")

    print("\n=== 股权成本敏感性 ===")
    for r in (0.08, 0.09, 0.10):
        vs = [v_per_share(s, r) for s in ("bear", "base", "bull")]
        print(f"  r={r:.0%}: bear {vs[0]:.2f} / base {vs[1]:.2f} / bull {vs[2]:.2f}；加权 {weighted(r):.2f}")

    print("\n=== 现价隐含回报（基准情景） ===")
    target = PRICE_A * SHARES_TOTAL
    irr = solve(lambda r: equity_value("base", r)[0], 0.05, 0.20, target)
    print(f"  基准情景现金流（含终值、非经营资产与净负债利息）使现值 = A 股价×总股本 {target:.1f} 亿的折现率：{irr:.2%}")
    irr_mixed = solve(lambda r: equity_value("base", r)[0], 0.05, 0.20, mcap_mixed)
    print(f"  H 股按 H 价计市值 {mcap_mixed:.1f} 亿时：{irr_mixed:.2%}")

    print("\n=== 反向 DCF（9%） ===")
    pv_debt9 = net_debt_adj * DEBT_RATE * (1 - TAX) / 0.09
    eq_needed = target - nonop("base") + pv_debt9
    h2_pv = op_np_h2_2026["base"] * (1 - SCEN["base"]["rr_h2"]) / 1.09 ** T_H2

    def ev_const_growth(g, years=10, g_t=0.025, roic_t=0.14, roic_inc=0.20):
        np_t = op_np_2026["base"]
        pv = h2_pv
        for i in range(years):
            np_t *= 1 + g
            rr = min(max(g / roic_inc, 0.0), 0.6)
            pv += np_t * (1 - rr) / 1.09 ** (T_FIRST + i)
        pv += np_t * (1 + g_t) * (1 - g_t / roic_t) / (0.09 - g_t) / 1.09 ** (T_FIRST + years - 1)
        return pv

    g_impl = solve(ev_const_growth, -0.10, 0.20, eq_needed)
    print(f"  现价隐含：2027-2036 经营归母净利年增 {g_impl:.2%}（再投资率 = g/20%），之后 2.5% 永续（再投资率 = 2.5%/14%）")

    def perp(g):
        oe = op_np_2026["base"] * (1 + g) * (1 - g / 0.14)
        return h2_pv + oe / (0.09 - g) * 1.09 ** (1 - T_FIRST)

    g_perp = solve(perp, -0.05, 0.085, eq_needed)
    print(f"  现价隐含永续增速（2026 经营归母净利起、再投资率 = g/14%）：{g_perp:.2%}")

    print("\n=== 交叉验证 ===")
    np_base = norm_np_2026["base"]
    core_mcap = target - nonop("base") + pv_debt9
    print(f"  PE：A 价×总股本 / 2026 正常化归母 {target / np_base:.1f}×；扣除非经营资产、加净负债利息现值后 / 经营归母 {core_mcap / op_np_2026['base']:.1f}×")
    print(f"  PB：{target / PARENT_EQUITY:.2f}×（历史年末 PB：2023 2.13、2024 2.18、2025 1.94）")
    kln_mv = KLN_SHARES_YI * PRICE_KLN_HKD * HKD_CNY
    minority_mkt = kln_mv * 0.4848 + (MINORITY_BOOK - 102.39)
    ebit_2026e = EBIT_CORE_2025 * (kf_2026e["base"] / KF_2025)
    for label, mino in (("少数股东按账面", MINORITY_BOOK), ("KLN 少数股东按市值", minority_mkt)):
        ev = target + net_debt_adj + mino - nonop("base")
        print(f"  EV（{label}）{ev:.0f} 亿：2025 核心 EBIT {EBIT_CORE_2025:.1f} → {ev / EBIT_CORE_2025:.1f}×；2026E {ebit_2026e:.1f} → {ev / ebit_2026e:.1f}×")
    print(f"  2026H1 核心 EBIT {EBIT_CORE_H1_2026:.1f}（2025 全年 {EBIT_CORE_2025:.1f}）")
    dps_ttm = 0.43 + 0.49
    print(f"  过去 12 个月股息 {dps_ttm:.2f} 元 → 股息率 {dps_ttm / PRICE_A:.2%}；2025-09~2026-09 回购 A 约 60.0 亿 + H 约 4.5 亿港元"
          f" → 回购收益率约 {(59.99 + 4.5 * 0.87) / target:.2%}（A 股方案已实施完毕，H 股方案上限 5 亿港元）")
    sf_kln = kln_mv * 0.5152
    core_ex_kln = op_np_2026["base"] - KLN_PARENT_NP_2025
    for pe in (12, 14, 16):
        v = (core_ex_kln * pe + sf_kln + nonop("base") - pv_debt9) / SHARES_TOTAL
        print(f"  分部加总：除 KLN 外经营归母 {core_ex_kln:.1f} 亿×{pe} + KLN 51.52% 市值 {sf_kln:.0f} 亿 + 非经营 − 净负债利息现值 → {v:.2f} 元/股")

    print("\n=== 证伪条件触发后的 V（加权） ===")
    print(f"  F1 2026 全年扣非 < 94 亿（2026 基数整体 −8%）：{v_with({'np_mult': 0.92}):.2f}")
    print(f"  F2 2027 上半年速运物流收入同比 ≤ 0 且单票收入同比转负（增速路径整体 −3pp）：{v_with({'growth_shift': -0.03}):.2f}")
    print(f"  F3 2026、2027 年资产类资本开支均 > 营收 4.5% 且扣非净利率未升至 3.3%（再投资率 +8pp、终值 ROIC −3pp）："
          f"{v_with({'rr_add': 0.08, 'roic_t_add': -0.03}):.2f}")
    print(f"  F4 布伦特季均 > 100 美元持续至 2027Q1 且 2026Q4、2027Q1 扣非同比均为负（熊市概率 50%）："
          f"{v_with({'prob': {'bear': 0.5, 'base': 0.4, 'bull': 0.1}}):.2f}")
    print(f"  F5 正面：2027 扣非 ≥ 115 亿且速运物流收入增速回到 ≥ 3%（增速路径整体 +3pp）：{v_with({'growth_shift': 0.03}):.2f}")
    f12 = v_with({'np_mult': 0.92, 'growth_shift': -0.03})
    f124 = v_with({'np_mult': 0.92, 'growth_shift': -0.03, 'prob': {'bear': 0.5, 'base': 0.4, 'bull': 0.1}})
    print(f"  F1+F2 同时触发：{f12:.2f}（P/V {PRICE_A / f12:.2f}）；F1+F2+F4：{f124:.2f}（P/V {PRICE_A / f124:.2f}）")


def sensitivity():
    """正文第五节"主要判断的敏感性"表。"""
    global T_H2, T_FIRST, net_debt_adj, JT_MV
    print("\n=== 主要判断的敏感性（加权 V） ===")
    print(f"  基准 {weighted():.2f}")
    print(f"  增速 +1pp / −1pp：{v_with({'growth_shift': 0.01}):.2f} / {v_with({'growth_shift': -0.01}):.2f}")
    saved = {k: dict(x) for k, x in SCEN.items()}
    out = []
    for d in (0.005, -0.005):
        for k in SCEN:
            SCEN[k]["g_t"] = saved[k]["g_t"] + d
        out.append(weighted())
        for k in SCEN:
            SCEN[k] = dict(saved[k])
    print(f"  终值增速 +0.5pp / −0.5pp：{out[0]:.2f} / {out[1]:.2f}")
    print(f"  终值 ROIC +3pp / −3pp：{v_with({'roic_t_add': 0.03}):.2f} / {v_with({'roic_t_add': -0.03}):.2f}")
    print(f"  再投资率 +5pp / −5pp：{v_with({'rr_add': 0.05}):.2f} / {v_with({'rr_add': -0.05}):.2f}")
    T_H2, T_FIRST = 0.2, 1.2
    print(f"  改为年末折现：{weighted():.2f}")
    T_H2, T_FIRST = 0.1, 0.7
    nd0 = net_debt_adj
    net_debt_adj = nd0 - OPER_RESERVE
    print(f"  不设经营备付：{weighted():.2f}")
    net_debt_adj = nd0
    saved_h = {k: dict(x) for k, x in NONOP_HAIRCUT.items()}
    for k in NONOP_HAIRCUT:
        NONOP_HAIRCUT[k] = dict(jt=1, oei=1, ncfa=1, assoc=1, park=NONOP_HAIRCUT[k]["park"])
    print(f"  非经营资产不打折：{weighted():.2f}")
    for k in saved_h:
        NONOP_HAIRCUT[k] = saved_h[k]
    jt0 = JT_MV
    vals = []
    for px in (7.54, 12.2):
        JT_MV = JT_SHARES_YI * px * HKD_CNY
        vals.append(weighted())
    JT_MV = jt0
    print(f"  极兔取 52 周低点 7.54 / 高点 12.2 港元：{vals[0]:.2f} / {vals[1]:.2f}")
    print(f"  三情景等权：{v_with({'prob': {'bear': 1 / 3, 'base': 1 / 3, 'bull': 1 / 3}}):.2f}")
    net_debt_adj = nd0 + LEASE_LIAB
    print(f"  若误把租赁负债也作净负债扣除：有杠杆 {weighted():.2f} / 无杠杆 {weighted(levered=False):.2f}")
    net_debt_adj = nd0


if __name__ == "__main__":
    main()
    sensitivity()
