# -*- coding: utf-8 -*-
"""乐鑫科技（688018）独立估值，OI-291 b21，价格日 2026-10-21。

运行：python3 valuation.py
单位：金额亿元，每股价值元/股。全部输入写在本脚本内，行尾注明出处或「估计」。
方法：归母所有者收益 DCF。经营利润剔除金融资产收益（存款利息、结构性存款与大额存单收益）、
政府补助等一次性项目与汇兑损益；现金类资产与非经营资产另加。显式期 2027-2036，终值增长 2.5%，
终值再投资率 = g / RONIC；现金流年中折现，2026 年第四季度单列。股权成本 9%，报 8%/10% 敏感性。
租赁：净利润已扣使用权资产折旧与租赁利息，租赁负债只列示、不扣。
股份支付：按报表计入费用（不加回），已授予未归属的限制性股票不再另扣摊薄。
"""
from datetime import date

# ============================================================ 快照
PRICE = 145.86                    # 2026-10-21 收盘（brief.md）
SHARES_TOTAL = 2.34384311         # 亿股，234,384,311 股，含回购专户（buyback_20260911 第 2-3 页）
TREASURY = 0.02729203             # 回购专户 2,729,203 股，用于员工持股/股权激励，未公告注销（同上第 3 页）
SHARES_EX = SHARES_TOTAL - TREASURY
MKT_CAP = PRICE * SHARES_TOTAL
VAL_DATE = date(2026, 10, 21)
COE = 0.09
G_TERM = 0.025
MINORITY = 0.003                  # 少数股东损益占净利润：2026H1 0.0105/3.3528（2026H1_report 第 79 页）

# ============================================================ 资产负债（2026-06-30）
CASH = 10.4643496134              # 货币资金，含未到期应收利息 0.1128；无受限资产（2026H1_report 第 115、143、164 页）
TFA = 9.5922342580                # 交易性金融资产：混合工具投资，即结构性存款（第 115、161-162 页）
CD_OCA = 7.188777                 # 其他流动资产中的大额存单（第 130 页；其余 0.4395 为待退税、预缴税与留抵，归经营）
CD_DEBT = 2.273313                # 债权投资：大额存单（第 131 页）
OEI = 0.4203606993                # 其他权益工具投资（第 73 页）
ONCFA = 0.4193741558              # 其他非流动金融资产：两只私募基金（第 38、73 页）
LEASE_LIAB = 0.0823404649 + 0.2559093506   # 一年内到期的租赁负债 + 租赁负债（第 74、163 页），只列示
BORROWINGS = 0.0                  # 6-30 无银行借款（第 74 页）
DTL_OVERSEAS_RE = 1.1519807273    # 境外留存收益递延所得税负债（第 142 页），已计入历年所得税费用，只列示
CASH_LIKE_0630 = CASH + TFA + CD_OCA + CD_DEBT
NON_OP = OEI + ONCFA
# 经营营运资本 = 应收票据 + 应收账款 + 预付 + 其他应收 + 存货 + 其他流动资产中非存单部分 − 应付账款 − 合同负债 − 应付职工薪酬 − 应交税费 − 其他应付 − 其他流动负债
NWC_0630 = (0.6526001282 + 4.0262250080 + 0.3514563439 + 0.1272975787 + 8.4184145653 + (7.6283154098 - CD_OCA)
            - 2.0879954594 - 0.3954011172 - 1.0145194674 - 0.1436851060 - 0.1299978745 - 0.0285039465)   # 2026H1_report 第 73-74、130 页
NWC_1231 = (0.6553450723 + 2.9810602993 + 0.1942710005 + 0.1143996254 + 6.2763751272 + (10.1193789821 - 9.468269)
            - 1.8752876183 - 0.2338105500 - 1.5761902425 - 0.0258179136 - 0.3730374736 - 0.0117341758)   # 同上期初数

# ============================================================ 6-30 至 9-30 现金变动
BB1_SHARES = 932824 - 17161       # 7-31 回购方案股数：8-19 方案实施前专户 932,824 股（buyback_20260911 第 3 页）减 6-30 专户 17,161 股（2026H1_report 第 64 页）
BB1_PRICE = 109.2                 # 估计：8-3 至 8-17 日线成交量加权均价约 110（f10.json 日线），该方案结果公告未读到
BB1 = BB1_SHARES * BB1_PRICE / 1e8
BB2 = 1.9999883907                # 8-19 回购方案实际金额（buyback_20260911 第 1 页）
OCF_H1 = 0.7244651208             # 2026H1_report 第 81 页
OCF_9M = 3.15                     # 前三季度经营现金流 3.1-3.2 亿取中（forecast_20261014 第 2 页）
CAPEX_Q3 = 0.40                   # 估计：上半年购建长期资产 0.7933 亿（第 81 页）的一半
LEASE_PAY_Q3 = 0.02               # 估计：上半年租赁付现 0.0424 亿（第 163 页）的一半
CASH_LIKE_0930 = CASH_LIKE_0630 - BB1 - BB2 + (OCF_9M - OCF_H1) - CAPEX_Q3 - LEASE_PAY_Q3
OP_RESERVE = 3.0                  # 经营备付：约 1.5 个月现金经营成本（2026E 现金成本约 24 亿/年）
NET_CASH_ADJ = CASH_LIKE_0930 - OP_RESERVE - BORROWINGS

# ============================================================ 2026 年：上半年实际 + 三季度预告 + 四季度估计
REV_2025 = 25.6527543181          # 2025_annual_report 第 11 页
NP_2025 = 4.9784014233
H1_REV = 14.8071129355            # 2026H1_report 第 11、78 页
H1_NP = 3.3422605686
H1_KF = 3.1162342241
H1_PRETAX = 3.4443152906          # 第 78 页
H1_FIN = 0.1110990583 + 0.1683095144 + 0.0153148429   # 利息收入 + 投资收益（存单与结构性存款）+ 公允价值变动（第 157-158 页）
H1_NRI = 0.0513963820 + 0.0206476824 + 0.0065777239 + 0.0001   # 政府补助 + 营业外净额 + 个税手续费返还 + 减值转回（第 13-14 页）
H1_FX = 0.0651141687              # 汇兑损失，加回（第 157 页）
H1_OP = H1_PRETAX - H1_FIN - H1_NRI + H1_FX

Q3_REV, Q3_NP, Q3_KF = 8.90, 2.20, 2.09   # 预告区间中值：营收 8.8-9.0，归母 2.11-2.29，扣非 2.00-2.18（forecast_20261014 第 1 页）
Q_ETR = 0.03                      # 季度实际税率估计（2026H1 为 2.66%，第 78 页）
Q3_FIN, Q3_NRI = 0.14, 0.03       # 估计：现金类约 29 亿 × 年化 1.96%（上半年实际收益率）/4；补助等
Q3_PRETAX = Q3_NP / (1 - MINORITY) / (1 - Q_ETR)
Q3_OP = Q3_PRETAX - Q3_FIN - Q3_NRI

Q4_REV, Q4_OP_MARGIN = 8.70, 0.225   # 估计：Q4 收入环比 -2%（2025 年 Q4 环比 -2.1%），经营利润率略低于 Q3
Q4_FIN, Q4_NRI = 0.13, 0.02
Q4_OP = Q4_REV * Q4_OP_MARGIN
Q4_NP = (Q4_OP + Q4_FIN + Q4_NRI) * (1 - Q_ETR) * (1 - MINORITY)
Q4_CAPEX_NET = 0.20               # 估计：四季度资本开支减折旧摊销
NWC_0930 = NWC_0630 + 0.12        # 估计：三季度经营现金流 2.43 ≈ 归母 2.20 + 折旧摊销约 0.23 + 股份支付约 0.15 − 存单收益等 0.04 − Δ营运资本 0.12
NWC_2026 = 10.0                   # 估计：2026 年末经营营运资本（四季度回款与年终奖计提释放约 0.34；2025 年四季度经营现金流 2.13 而归母 1.21）
Q4_OE = Q4_OP * (1 - Q_ETR) * (1 - MINORITY) - Q4_CAPEX_NET - (NWC_2026 - NWC_0930)

# 同口径历史经营税前利润率（税前 − 金融资产收益 − 补助等非经常 + 汇兑损失）：2025_annual_report 第 14-15、135-136、218 页
REV_2024 = 20.0691968657
OP_2025 = 5.0768766726 - (0.2416029280 + 0.1687740207 + 0.0872539830) - (0.2225883353 - 0.0017457240 + 0.0049862684 + 0.0056494634) + 0.0737515261
OP_2024 = 3.3297177920 - (0.1701917905 + 0.2104212439) - (0.1629349249 - 0.0100676748 - 0.0018981745 + 0.0036412751 + 0.0013308590) + 0.0732023485

REV_2026 = H1_REV + Q3_REV + Q4_REV
NP_2026 = H1_NP + Q3_NP + Q4_NP
OP_2026 = H1_OP + Q3_OP + Q4_OP
OP_MARGIN_2026 = OP_2026 / REV_2026
FIN_2026 = H1_FIN + Q3_FIN + Q4_FIN

# 2026 年正常化归母净利（报表口径，含净利息，剔除一次性；正文第二节）
NORM_MARGIN_2026 = {"bear": OP_MARGIN_2026 - 0.030, "base": OP_MARGIN_2026 - 0.010, "bull": OP_MARGIN_2026}
NORM_NP_2026 = {k: (REV_2026 * m + FIN_2026) * (1 - Q_ETR) * (1 - MINORITY) for k, m in NORM_MARGIN_2026.items()}

# ============================================================ 情景
YEARS = list(range(2027, 2037))
CAPEX_INT = 0.08                  # 净资本开支 / 收入增量（不含总部大楼的固定+无形+长摊约占收入 7.5%）
SCEN = {
    "bear": dict(
        p=0.25,
        growth=[0.08, 0.09, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.025],
        margin=[0.195, 0.175, 0.175] + [0.180] * 7,
        etr=[0.04, 0.06, 0.08, 0.10, 0.11] + [0.12] * 5,
        nwc=[0.31] + [0.30] * 9, ronic=0.15,
        text="存储涨价挤压模组毛利、智能家居停滞、国内对手价格战、AI 编程降低迁移成本；2027-2031 年收入增 8%-9%，"
             "2031 年约 48 亿；毛利率回到 46% 左右而研发照常扩张，经营利润率 2028 年起 17.5%-18%"
             "（加计抵减 2027 年底到期），税率升至 12%，营运资本占收入 30%，终值 RONIC 15%"),
    "base": dict(
        p=0.50,
        growth=[0.19, 0.17, 0.15, 0.13, 0.11, 0.09, 0.075, 0.06, 0.045, 0.035],
        margin=[0.220, 0.215, 0.220, 0.225] + [0.230] * 6,
        etr=[0.04, 0.05, 0.06, 0.07, 0.08, 0.09] + [0.10] * 4,
        nwc=[0.285] + [0.27] * 9, ronic=0.30,
        text="Wi-Fi MCU 第一的位置守住，非智能家居、开发者与 AI 交互终端带动 S3/P4/S31、Wi-Fi 6 放量；"
             "2027-2031 年收入增 19%→11%，2029 年约 52 亿（略低于 2026 年激励计划目标 53.2 亿），2031 年约 66 亿；"
             "毛利率回到 48%-48.5%，研发费率降至 19.5%-20.5%，经营利润率 22%（2028 年加计抵减到期降至 21.5%）后升至 23%；"
             "税率 4%→10%，存货回落后营运资本占收入 27%，终值 RONIC 30%"),
    "bull": dict(
        p=0.25,
        growth=[0.25, 0.23, 0.21, 0.18, 0.16, 0.13, 0.10, 0.08, 0.06, 0.04],
        margin=[0.240, 0.245, 0.255, 0.260] + [0.265] * 6,
        etr=[0.04, 0.05, 0.06, 0.07, 0.08, 0.09] + [0.10] * 4,
        nwc=[0.27] + [0.25] * 9, ronic=0.40,
        text="端侧 AI 与开发者生态推高单设备价值量，Wi-Fi 7 终端/路由与 Linux 平台打开新市场；2027-2031 年收入增 25%→16%，"
             "2031 年约 83 亿；毛利率保持 49%-50%，加计抵减延续或被经营杠杆抵消，经营利润率升至 26.5%；终值 RONIC 40%"),
}


def t_of(d):
    return (d - VAL_DATE).days / 365.25


def project(s, margin_shift=0.0, shift_from=2027, nwc_override=None):
    rows = []
    rev_prev, nwc_prev = REV_2026, NWC_2026
    for i, y in enumerate(YEARS):
        rev = rev_prev * (1 + s["growth"][i])
        m = s["margin"][i] + (margin_shift if y >= shift_from else 0.0)
        op_np = rev * m * (1 - s["etr"][i]) * (1 - MINORITY)
        nwc = rev * (nwc_override if nwc_override is not None else s["nwc"][i])
        d_nwc = nwc - nwc_prev
        capex_net = CAPEX_INT * (rev - rev_prev)
        rows.append(dict(year=y, rev=rev, growth=s["growth"][i], margin=m, etr=s["etr"][i], op_np=op_np,
                         d_nwc=d_nwc, capex_net=capex_net, oe=op_np - d_nwc - capex_net))
        rev_prev, nwc_prev = rev, nwc
    oe_term = rows[-1]["op_np"] * (1 + G_TERM) * (1 - G_TERM / s["ronic"])
    return rows, oe_term


def equity(s, r=COE, extra=0.0, **kw):
    rows, oe_term = project(s, **kw)
    pv_q4 = Q4_OE / (1 + r) ** t_of(date(2026, 11, 25))
    pv_exp = sum(x["oe"] / (1 + r) ** t_of(date(x["year"], 7, 1)) for x in rows)
    pv_tv = oe_term / (r - G_TERM) / (1 + r) ** t_of(date(YEARS[-1], 7, 1))
    ops = pv_q4 + pv_exp + pv_tv
    eq = ops + NET_CASH_ADJ + NON_OP + extra
    return dict(rows=rows, pv_q4=pv_q4, pv_exp=pv_exp, pv_tv=pv_tv, ops=ops, eq=eq,
                v=eq / SHARES_TOTAL, v_ex=eq / SHARES_EX, tv_share=pv_tv / eq)


def weighted(r=COE, weights=None, **kw):
    w = weights or {k: SCEN[k]["p"] for k in SCEN}
    return sum(w[k] * equity(SCEN[k], r, **kw)["v"] for k in SCEN)


def bisect(f, lo, hi, target, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s):
    return bisect(lambda r: equity(s, r)["eq"], 0.03, 0.40, MKT_CAP)


def reverse_uniform(roiic, r=COE):
    """经营归母净利自 2026E 起 10 年等速增长 g，再投资 = g/ROIIC × 净利，之后 2.5% 永续（RONIC 30%）。"""
    op_np0 = OP_2026 * (1 - Q_ETR) * (1 - MINORITY)
    target = MKT_CAP - NET_CASH_ADJ - NON_OP - Q4_OE / (1 + r) ** t_of(date(2026, 11, 25))

    def ops(g):
        pv, x = 0.0, op_np0
        for y in YEARS:
            x *= 1 + g
            pv += x * (1 - min(g / roiic, 0.95)) / (1 + r) ** t_of(date(y, 7, 1))
        tv = x * (1 + G_TERM) * (1 - G_TERM / 0.30) / (r - G_TERM)
        return pv + tv / (1 + r) ** t_of(date(YEARS[-1], 7, 1))

    g = bisect(ops, -0.05, 0.60, target)
    return g, op_np0 * (1 + g) ** 10


def reverse_perpetual(r=COE):
    """一阶段：以基准 2027 年经营归母净利为起点，再投资率 g/30%，求现价对应的永续增长。"""
    np27 = project(SCEN["base"])[0][0]["op_np"]
    target = MKT_CAP - NET_CASH_ADJ - NON_OP
    return bisect(lambda g: np27 * (1 - g / 0.30) / (r - g), 0.0, r - 1e-4, target)


def band(pv):
    return "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"


def main():
    print("=== 乐鑫科技（688018）独立估值，价格日 2026-10-21 ===")
    print(f"现价 {PRICE:.2f} 元；总股本 {SHARES_TOTAL:.4f} 亿股（含回购专户 {TREASURY:.4f}）；市值 {MKT_CAP:.2f} 亿元")
    print(f"现金类 6-30：{CASH_LIKE_0630:.2f} = 货币资金 {CASH:.2f} + 结构性存款 {TFA:.2f} + 大额存单 {CD_OCA:.2f} + {CD_DEBT:.2f}")
    print(f"6-30 后：回购 -{BB1:.2f}（7-31 方案 {BB1_SHARES:,} 股，估计）-{BB2:.2f}（8-19 方案）；"
          f"三季度经营现金流 +{OCF_9M - OCF_H1:.2f}；资本开支 -{CAPEX_Q3:.2f}；租赁 -{LEASE_PAY_Q3:.2f}")
    print(f"9-30 现金类（估计）{CASH_LIKE_0930:.2f}；经营备付 -{OP_RESERVE:.2f}；有息负债 {BORROWINGS:.2f} → "
          f"经调整净现金 {NET_CASH_ADJ:.2f}（每股 {NET_CASH_ADJ / SHARES_TOTAL:.2f}）；非经营资产 {NON_OP:.2f}；"
          f"租赁负债 {LEASE_LIAB:.2f}、境外留存收益递延税负债 {DTL_OVERSEAS_RE:.2f}（均只列示）")
    print(f"同口径经营税前利润率：2024 {OP_2024 / REV_2024:.1%}；2025 {OP_2025 / REV_2025:.1%}；"
          f"2026 上半年 {H1_OP:.3f}（{H1_OP / H1_REV:.1%}）；三季度 {Q3_OP:.3f}（{Q3_OP / Q3_REV:.1%}）；"
          f"四季度估计 {Q4_OP:.3f}（{Q4_OP_MARGIN:.1%}），归母约 {Q4_NP:.2f}")
    print(f"2026E：收入 {REV_2026:.2f}（{REV_2026 / REV_2025 - 1:+.1%}），归母 {NP_2026:.2f}（{NP_2026 / NP_2025 - 1:+.1%}），"
          f"经营税前 {OP_2026:.2f}（{OP_MARGIN_2026:.1%}），金融资产收益 {FIN_2026:.2f}")
    print("2026 正常化归母净利（报表口径）：" + "／".join(f"{k} {v:.2f}（经营利润率 {NORM_MARGIN_2026[k]:.1%}）" for k, v in NORM_NP_2026.items()))
    ttm_np = 5.7134 - 1.1550053805 + Q3_NP     # 数据包 TTM(6-30) 归母 5.71 − 2025Q3 1.155（forecast_20261014 第 1 页）+ 2026Q3 预告中值
    ev = MKT_CAP - NET_CASH_ADJ - NON_OP
    print(f"PE(三季度后 TTM {ttm_np:.2f}) {MKT_CAP / ttm_np:.1f}×；PE(2026E) {MKT_CAP / NP_2026:.1f}×；"
          f"EV {ev:.1f}；EV/经营税前利润(2026E) {ev / OP_2026:.1f}×")
    print(f"经营营运资本：2025 年末 {NWC_1231:.2f}（占 2025 收入 {NWC_1231 / REV_2025:.1%}）；6-30 {NWC_0630:.2f}"
          f"（占上半年年化收入 {NWC_0630 / (2 * H1_REV):.1%}）；9-30 估计 {NWC_0930:.2f}；2026 年末估计 {NWC_2026:.2f}（{NWC_2026 / REV_2026:.1%}）")
    cash_like_1231 = 10.2479283999 + 8.7600960822 + 9.468269 + 2.104304   # 2025 年末：货币资金 + 交易性 + 存单（2026H1_report 第 73、130-131 页期初数）
    print(f"上半年金融资产年化收益率 {2 * H1_FIN / ((cash_like_1231 + CASH_LIKE_0630) / 2):.2%}（现金类 2025 年末 {cash_like_1231:.2f}）")
    buyback_12m = 0.99 + BB1 + BB2    # 2026 上半年回购付现约 0.99（第 81-82、163 页筹资其他支出 1.031 含租赁 0.042）+ 7-31 方案 + 8-19 方案
    div_total = 0.8370255350      # 2025 年度现金分红 83,702,553.50 元（每 10 股派 5 元，按转增前股本，2026H1_report 第 64 页）
    print(f"股息率 {div_total / MKT_CAP:.2%}（按分红总额÷市值；按转增前每股 0.5 元÷现价会高估为 {0.5 / PRICE:.2%}）；"
          f"近 12 个月回购约 {buyback_12m:.2f} 亿（{buyback_12m / MKT_CAP:.2%}，用于股权激励、非注销）；合计 {(div_total + buyback_12m) / MKT_CAP:.2%}")
    ic_0630 = NWC_0630 + 5.6534279752 + 0.2456632356 + 0.7465402370 + 0.3181780298 + 0.3535594935   # + 固定资产 + 无形 + 商誉 + 使用权 + 长摊（第 74 页）
    print(f"经营投入资本 6-30 约 {ic_0630:.2f}，2026E 经营税后利润 {OP_2026 * (1 - Q_ETR):.2f}，ROIC 约 {OP_2026 * (1 - Q_ETR) / ic_0630:.0%}")
    print()

    res = {}
    for k, s in SCEN.items():
        res[k] = e = equity(s)
        print(f"--- {k}（概率 {s['p']:.2f}）---")
        print("年份  收入    增速   经营利润率 税率  经营归母净利 Δ营运资本 净资本开支 所有者收益")
        for x in e["rows"]:
            print(f"{x['year']} {x['rev']:7.2f} {x['growth']:6.1%} {x['margin']:8.1%} {x['etr']:6.1%} "
                  f"{x['op_np']:9.2f} {x['d_nwc']:9.2f} {x['capex_net']:8.2f} {x['oe']:9.2f}")
        r5 = e["rows"][:5]
        reinv = sum(x["d_nwc"] + x["capex_net"] for x in r5)
        np_sum = sum(x["op_np"] for x in r5)
        op_np_2026 = OP_2026 * (1 - Q_ETR) * (1 - MINORITY)
        s["reinv_rate"] = reinv / np_sum
        s["inc_ret"] = (r5[-1]["op_np"] - op_np_2026) / reinv
        s["oe_growth"] = [r5[0]["oe"] / Q4_OE / 4 - 1] + [r5[i]["oe"] / r5[i - 1]["oe"] - 1 for i in range(1, 5)]
        s["np_growth"] = [r5[0]["op_np"] / op_np_2026 - 1] + [r5[i]["op_np"] / r5[i - 1]["op_np"] - 1 for i in range(1, 5)]
        print(f"PV：2026Q4 {e['pv_q4']:.2f} + 显式期 {e['pv_exp']:.2f} + 终值 {e['pv_tv']:.2f} = 经营 {e['ops']:.2f}；"
              f"+ 净现金 {NET_CASH_ADJ:.2f} + 非经营 {NON_OP:.2f} = 股权 {e['eq']:.2f}")
        print(f"V = {e['v']:.2f} 元（剔除回购专户 {e['v_ex']:.2f}）；终值占股权价值 {e['tv_share']:.1%}；"
              f"2027-2031 再投资率 {s['reinv_rate']:.1%}，增量回报 {s['inc_ret']:.1%}；V 对应 2026E 归母 PE {e['eq'] / NP_2026:.1f}×")
        print("经营归母净利增速 2027-2031：" + "、".join(f"{g:.1%}" for g in s["np_growth"]))
        print()

    vw = sum(SCEN[k]["p"] * res[k]["v"] for k in SCEN)
    vw_ex = sum(SCEN[k]["p"] * res[k]["v_ex"] for k in SCEN)
    pv = PRICE / vw
    print(f"加权 V = {vw:.2f} 元；P/V = {pv:.3f}（{band(pv)}）")
    print(f"剔除回购专户股份：加权 V = {vw_ex:.2f} 元，P/V = {PRICE / vw_ex:.3f}")
    print(f"V 不变时各档价格：≤{0.75 * vw:.1f} 明显低估；{0.75 * vw:.1f}-{0.90 * vw:.1f} 温和低估；"
          f"{0.90 * vw:.1f}-{1.10 * vw:.1f} 大致合理；>{1.10 * vw:.1f} 偏贵")
    for r in (0.08, 0.10):
        parts = "／".join(f"{k} {equity(SCEN[k], r)['v']:.2f}" for k in SCEN)
        print(f"股权成本 {r:.0%}：加权 V = {weighted(r):.2f}（{parts}）")
    irr = {k: implied_irr(SCEN[k]) for k in SCEN}
    print(f"现价隐含回报（基准情景现金流）= {irr['base']:.2%}；熊 {irr['bear']:.2%}；牛 {irr['bull']:.2%}")
    g10, np36 = reverse_uniform(SCEN["base"]["inc_ret"])
    gp = reverse_perpetual()
    print(f"反向 DCF：经营归母净利 2027-2036 年均需增 {g10:.1%}（再投资率 g/{SCEN['base']['inc_ret']:.0%}），"
          f"2036 年约 {np36:.1f} 亿（约为 2026E 的 {np36 / (OP_2026 * (1 - Q_ETR) * (1 - MINORITY)):.1f} 倍；"
          f"按 23% 经营利润率、10% 税率需收入约 {np36 / (0.23 * 0.90 * (1 - MINORITY)):.0f} 亿）；一阶段永续增长 {gp:.2%}")
    print()

    print("--- 证伪条件触发后的加权 V ---")
    f1 = weighted(margin_shift=-0.02)
    f2 = weighted(weights={"bear": 0.5, "base": 0.4, "bull": 0.1})
    f3 = sum(SCEN[k]["p"] * equity(SCEN[k], margin_shift=-0.01, nwc_override=0.31)["v"] for k in SCEN)
    f4 = weighted(weights={"bear": 0.1, "base": 0.5, "bull": 0.4})
    f5 = sum(SCEN[k]["p"] * equity(SCEN[k], margin_shift=(0.012 if k != "bull" else 0.0), shift_from=2028)["v"] for k in SCEN)
    print(f"F1 毛利率连续两季 <46%（各情景经营利润率 -2pp）：V = {f1:.2f}")
    print(f"F2 2027 年收入 <35.5 亿，或 2027 年前三季度收入同比 <+10%（权重改为熊 0.5／基准 0.4／牛 0.1）：V = {f2:.2f}")
    print(f"F3 2026 年末存货 ≥10 亿且全年资产减值 ≥0.5 亿，或 2026 年经营现金流 <5.0 亿（营运资本 31%、利润率 -1pp）：V = {f3:.2f}")
    f45 = sum({"bear": 0.1, "base": 0.5, "bull": 0.4}[k] * equity(SCEN[k], margin_shift=(0.012 if k != "bull" else 0.0), shift_from=2028)["v"] for k in SCEN)
    print(f"F4 与 F5 同时触发：V = {f45:.2f}（P/V {PRICE / f45:.2f}）；只按牛市情景：P/V {PRICE / equity(SCEN['bull'])['v']:.2f}")
    print(f"F4 2027 年收入 ≥40 亿且扣非 ≥9.5 亿（权重改为熊 0.1／基准 0.5／牛 0.4）：V = {f4:.2f}")
    print(f"F5 集成电路增值税加计抵减 2027 年底前获延续（熊、基准 2028 年起利润率 +1.2pp）：V = {f5:.2f}")


if __name__ == "__main__":
    main()
