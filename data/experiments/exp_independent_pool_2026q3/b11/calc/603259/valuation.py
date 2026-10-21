#!/usr/bin/env python3
"""药明康德（603259）独立估值：所有者收益 DCF 三情景、反向 DCF、隐含回报与交叉验证。

全部输入写在脚本内，来源见注释（文件名指 raw/603259/txt/ 下逐页文本，页码为 PDF 物理页）。
金额单位亿元，股数单位亿股，每股价值单位元。运行：python3 valuation.py；加 --json 另打印数值字段。
"""
import json
import sys
from datetime import date

# ---------------------------------------------------------------- 价格与股本
PRICE_DATE = date(2026, 10, 20)
PRICE_A = 147.66                 # A 股收盘（腾讯日线 2026-10-20）
PRICE_H_HKD = 196.50             # H 股 02359 收盘（腾讯行情 2026-10-20）
HKDCNY = 0.8505                  # 腾讯行情 whHKDCNY，2026-10-21 早盘
A_SHARES = 24.73280246           # FF301 月报表（2026-10-08 H 股公告）截至 2026-09-30：A 股 2,473,280,246
H_SHARES = 5.61623820            # 同上：H 股 561,623,820（6-30 为 510,476,909，增量 51,146,911 为转债转股）
SHARES = A_SHARES + H_SHARES     # 30.3490，与 brief 一致（含 A 股回购专户与 H 股库存股）
A_REPO = 0.09701231              # A 股回购专户 9,701,231 股，用于 2026 年员工持股计划，非注销（buyback_20260627 第 3 页）
H_TREASURY = 0.20148900          # H 股库存股 20,148,900 股（2026H1_report 第 2 页）
SHARES_EX_TREASURY = SHARES - A_REPO - H_TREASURY
SHARES_BS = 29.83757155          # 资产负债表股本 2026-06-30（2026H1_report 第 46、133 页）
CB_FACE = 67.8                   # 2027 年到期美元结算零息可转债本金（2026H1_report 第 45 页）
CB_CONV_SHARES = 0.51146959      # 按 153 港元、HKD1=CNY0.8664 全部转股的股数（同上第 46 页）
# 转债状态：2026-09-21 董事会《关于接受可转换债券转股申请的议案》；FF301 显示 H 股增 51,146,911 股，
# 与全部转股股数只差 48 股（零碎股），判断已全部转股。正文仍列出“按未转股（债务）口径”对照。

# ---------------------------------------------------------------- 经调整净现金（2026-06-30，2026H1_report 第 47-48 页及附注）
CASH = 357.258                   # 货币资金
RESTRICTED = 0.246               # 受限货币资金（保函保证金/保护性冻结，附注七 31）
WMP = 109.143                    # 交易性金融资产（全部为理财产品，附注七 2）
CD_CURRENT = 13.876              # 一年内到期的非流动资产中银行大额存单（附注七 12）
ST_LOAN = 61.818                 # 短期借款（信用借款）
LT_LOAN = 17.988 + 0.006         # 长期借款 + 一年内到期长期借款
LEASE = 3.910 + 1.545            # 租赁负债 + 一年内到期租赁负债
DIV_PAYABLE_MINORITY = 0.546     # 应付少数股东股利
DECLARED_INTERIM_DIV = 15.065    # 2026 中期股利 0.51 元/股 × 29.5391 亿股（6-30 后宣派并支付，2026H1_report 第 27 页）
OPERATING_RESERVE = 23.0         # 经营备付：约 1 个月付现成本（H1 营业成本+税金+三费-折旧摊销-股份支付 ≈137.8/6）
NET_CASH_ADJ = (CASH - RESTRICTED + WMP + CD_CURRENT - ST_LOAN - LT_LOAN - LEASE
                - DIV_PAYABLE_MINORITY - DECLARED_INTERIM_DIV - OPERATING_RESERVE)
# 衍生金融资产 2.69/负债 0.14 为外汇套保，与未来收入对冲，不计入；转债已转股，不扣。

# ---------------------------------------------------------------- 非经营资产
# 药明合联（2268.HK）：2025-10-09 持股 21.42%（holders_20251011 第 22 页）；2025-10-08 出售 3,030 万股约占其总股本 2.47%
# （临 2025-066）→ 当时总股本约 12.267 亿股 → 持股约 2.628 亿股；2026-08-26 再售 5,352.4 万股、约 39.20 亿港元、
# 税前收益约 31.43 亿元（临 2026-038）。6-30 账面 21.02 亿元、对应公允价值 115.06 亿元（2026H1_report 第 107 页）。
XDC_PRICE_HKD = 75.85            # 腾讯行情 2026-10-20
XDC_HELD_PRE = 0.2142 * (0.303 / 0.0247)   # ≈2.628 亿股（出售前）
XDC_SOLD = 0.53524
XDC_REMAIN = XDC_HELD_PRE - XDC_SOLD
XDC_BOOK_PS = 21.019 / XDC_HELD_PRE        # 6-30 每股账面（元）
XDC_TAX = 0.165                  # 2025 年出售药明合联：税前 52.08 亿、税后 43.51 亿 → 约 16.5%（2025_annual_report 第 27 页；临 2025-066）
BLOCK_DISCOUNT = 0.07            # 大宗出售折价
xdc_sale_proceeds = 39.20 * 0.865                      # 8 月所得现金（港元按当时约 0.865 折算）
xdc_sale_after_tax = xdc_sale_proceeds - 31.43 * XDC_TAX
xdc_remain_mv = XDC_REMAIN * XDC_PRICE_HKD * HKDCNY
xdc_remain_net = xdc_remain_mv * (1 - BLOCK_DISCOUNT)
xdc_remain_after_tax = xdc_remain_net - (xdc_remain_net - XDC_REMAIN * XDC_BOOK_PS) * XDC_TAX
XDC_VALUE = xdc_sale_after_tax + xdc_remain_after_tax
# 其他非流动金融资产 84.13（附注七 19）：上市股份 20.61、非上市基金 18.70、非上市股份 43.03、或有对价 1.79
NCFA = {"上市股份": (20.611, 0.90), "非上市基金": (18.704, 0.80),
        "非上市股份": (43.030, 0.75), "剥离业务或有对价": (1.789, 0.50)}
NCFA_VALUE = sum(v * h for v, h in NCFA.values())
LP_VALUE = 1.623 * 0.80          # WuXi Healthcare Ventures II（权益法，附注七 17）
DIVEST_RECEIVABLE = 3.474 * 0.95  # 一年内到期的处置子公司股权转让款（附注七 12）
NON_OP = XDC_VALUE + NCFA_VALUE + LP_VALUE + DIVEST_RECEIVABLE

# ---------------------------------------------------------------- 2026 年正常化（H1 实际 + H2 估计）
TAX_N = 0.17                     # 正常化税率（H1 实际 17.7%）
H1_REV = 288.975                 # 2026H1 营业收入
H1_DEDUCT = 105.722              # 2026H1 扣非归母
H1_FX_LOSS = 6.294               # 财务费用中汇兑损失（附注七 66）
H1_HEDGE_GAIN = 2.210            # 到期交割套保对税前利润影响（2026H1_report 第 21 页）
H1_BIO_FV = 2.648                # 生物资产公允价值变动收益（附注七 70，属扣非内的周期性项）
H1_WMP = 0.634 + 0.483           # 理财产品处置收益+公允价值变动（列入非经常，视同利息）
H1_INT_INC, H1_INT_EXP, H1_LEASE_INT = 5.274, 0.897, 0.114
H1_EQUITY_INC = 1.474            # 权益法投资收益（药明合联 1.53、基金 -0.05）
H1_SBC = 3.416                   # 股份支付费用（附注十五 4）
h1_norm = (H1_DEDUCT + (H1_FX_LOSS - H1_HEDGE_GAIN) * (1 - TAX_N)
           - H1_BIO_FV * 0.85 + H1_WMP * (1 - TAX_N))
h1_net_int = (H1_INT_INC + H1_WMP - H1_INT_EXP - H1_LEASE_INT) * (1 - TAX_N)
h1_op = h1_norm - h1_net_int - H1_EQUITY_INC
H1_OP_MARGIN = h1_op / H1_REV
# H2 股份支付：2026-06 授出 2025 年 H 股奖励 31.96 亿元（四批 25%，2026-12 至 2029-12 归属，分批摊销）
# H2 约 13.4 亿 + 2024 年计划约 2.6 亿 + 员工持股计划约 1.7 亿 + 其他 → 约 18.1 亿，较 H1 多 14.7 亿（税后约 12.5 亿）
H2_SBC = 18.1
SBC_STEPUP_AT = (H2_SBC - H1_SBC) * 0.85
H2_NET_INT = 4.5                 # H2 税后净利息（含理财）
H2_EQUITY_INC = 1.2              # H2 权益法（药明合联持股减少约两成）
RR_2026 = 0.45                   # 2026 年再投资率：资本开支 75-85 亿、应收存货大增（H1 营运资本占用约 34 亿）

# ---------------------------------------------------------------- 情景
SCEN = {
    "bear": dict(p=0.25, h2_rev=301.0, h2_margin=0.340,
                 growth=[0.03, -0.06, -0.08, -0.06, -0.03], margin=[0.300, 0.280, 0.265, 0.255, 0.250],
                 rr=[0.15, 0.08, 0.05, 0.05, 0.06], g_t=0.015, roiic_t=0.20,
                 note="1260H 认定经上诉或重新认定恢复、2027 年进入 BCC 名单；美国客户转移新项目，大客户自建产能；2027-2031 收入累计约 -19%，经营净利率回到 25%"),
    "base": dict(p=0.50, h2_rev=311.0, h2_margin=0.350,
                 growth=[0.15, 0.10, 0.07, 0.05, 0.04], margin=[0.325, 0.320, 0.315, 0.310, 0.305],
                 rr=[0.30, 0.26, 0.22, 0.18, 0.14], g_t=0.025, roiic_t=0.25,
                 note="2026 收入约 600 亿（指引 585-605 上沿）；在手订单 +25% 支撑 2027 年 +15%，此后逐年放缓至 4%；股份支付升至约 4% 收入，经营净利率由 33.0% 缓降至 30.5%"),
    "bull": dict(p=0.25, h2_rev=323.0, h2_margin=0.355,
                 growth=[0.22, 0.16, 0.12, 0.09, 0.07], margin=[0.335, 0.335, 0.330, 0.330, 0.325],
                 rr=[0.33, 0.30, 0.26, 0.22, 0.18], g_t=0.025, roiic_t=0.25,
                 note="诉讼胜诉、OMB 名单未纳入；GLP-1 等商业化分子放量延续，2027 年 +22%、2031 年仍 +7%；经营净利率维持 32.5%-33.5%"),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def t_mid(year):
    """年中现金流距价格日的年数。"""
    return (date(year, 7, 1) - PRICE_DATE).days / 365.25


def build(s):
    """返回情景的逐年收入、经营净利、所有者收益（经营口径，不含利息与权益法收益）。"""
    h2_op = s["h2_rev"] * s["h2_margin"] - SBC_STEPUP_AT
    rev26 = H1_REV + s["h2_rev"]
    op26 = h1_op + h2_op
    norm26 = op26 + h1_net_int + H1_EQUITY_INC + H2_NET_INT + H2_EQUITY_INC
    oe_h2 = h2_op * (1 - RR_2026)
    rev, op, oe = [], [], []
    r_prev = rev26
    for g, m, rr in zip(s["growth"], s["margin"], s["rr"]):
        r_prev *= 1 + g
        rev.append(r_prev)
        op.append(r_prev * m)
        oe.append(r_prev * m * (1 - rr))
    rr_t = s["g_t"] / s["roiic_t"]
    oe_t1 = op[-1] * (1 + s["g_t"]) * (1 - rr_t)   # 2032 年所有者收益
    return dict(rev26=rev26, op26=op26, norm26=norm26, h2_op=h2_op, oe_h2=oe_h2,
                rev=rev, op=op, oe=oe, rr_t=rr_t, oe_t1=oe_t1)


def value(s, r, extra_cash=0.0):
    b = build(s)
    pv_exp = sum(cf / (1 + r) ** t_mid(y) for cf, y in zip(b["oe"], YEARS))
    tv = b["oe_t1"] / (r - s["g_t"])
    pv_tv = tv / (1 + r) ** t_mid(2031)
    op_value = b["oe_h2"] + pv_exp + pv_tv
    equity = op_value + NET_CASH_ADJ + NON_OP + extra_cash
    return dict(b=b, pv_exp=pv_exp, tv=tv, pv_tv=pv_tv, op_value=op_value, equity=equity,
                v=equity / SHARES, v_ex=equity / SHARES_EX_TREASURY,
                v_cb_debt=(equity - CB_FACE) / SHARES_BS, tv_share=pv_tv / op_value)


def weighted(r, probs=None, margin_shift=0.0):
    tot = 0.0
    for k, s in SCEN.items():
        s2 = dict(s)
        if margin_shift:
            s2["margin"] = [m + margin_shift for m in s["margin"]]
        p = probs[k] if probs else s["p"]
        tot += p * value(s2, r)["v"]
    return tot


def bisect(f, lo, hi, n=200):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def bridge_2025():
    """2025 年报告归母 → 扣非 → 正常化（2025_annual_report 第 9、187-188 页；附注七 66、68、70）。"""
    reported, deduct = 191.506, 132.406
    items = {  # 非经常性损益（税前，亿元）
        "非流动资产处置（药明合联股权 52.08 + 处置子公司 21.70 + 其他）": 73.131,
        "政府补助（非经常部分）": 1.750,
        "金融资产公允价值变动及处置": 3.421,
        "终止经营一次性费用": -1.603,
        "其他营业外收支": -0.168,
        "股东捐赠用于人才激励的费用": -0.500,
        "所得税影响": -16.458,
        "少数股东影响": -0.472,
    }
    inv_fv = {  # 投资收益 85.88 + 公允价值变动 -1.37 = 84.51 的构成
        "出售药明合联股权": 52.084, "处置子公司": 21.699, "处置其他非流动金融资产": 7.243,
        "权益法收益": 4.526, "生物资产公允价值": 2.780, "理财（处置+公允价值）": 0.820,
        "股权投资公允价值变动": -4.566, "衍生工具": -0.211, "金融资产持有收益及其他": 0.136,
    }
    fx_loss, bio, wmp = 10.137, 2.780, 0.820
    norm = deduct + fx_loss * (1 - TAX_N) - bio * 0.85 + wmp * (1 - TAX_N)
    return reported, deduct, items, inv_fv, norm


def main():
    rep25, ded25, items25, invfv25, norm25 = bridge_2025()
    print("== 2025 年利润桥（亿元）")
    print(f"报告归母 {rep25} − 非经常性损益合计 {sum(items25.values()):.2f} = 扣非 {ded25}")
    for k, v in items25.items():
        print(f"   {k} {v:+.2f}")
    print(f"投资收益+公允价值变动合计 {sum(invfv25.values()):.2f}：" + "；".join(f"{k} {v:+.2f}" for k, v in invfv25.items()))
    print(f"正常化（扣非 + 汇兑损失税后 − 生物资产公允价值 + 理财）{norm25:.1f}；另含股份支付 6.45、权益法 4.53")

    mcap_a_all = PRICE_A * SHARES
    price_h_cny = PRICE_H_HKD * HKDCNY
    mcap_mixed = PRICE_A * A_SHARES + price_h_cny * H_SHARES
    print("== 股本与市值")
    print(f"总股本 {SHARES:.4f} 亿股（A {A_SHARES:.4f} + H {H_SHARES:.4f}）；剔除回购专户与 H 股库存股 {SHARES_EX_TREASURY:.4f}")
    print(f"A 股价×总股本 {mcap_a_all:,.1f}；A、H 各按本市价格 {mcap_mixed:,.1f}（H 股 {PRICE_H_HKD} 港元 = {price_h_cny:.2f} 元，较 A 股溢价 {price_h_cny / PRICE_A - 1:.1%}）")

    print("\n== 经调整净现金与非经营资产（亿元）")
    print(f"经调整净现金 {NET_CASH_ADJ:.1f}（现金 {CASH} − 受限 {RESTRICTED} + 理财 {WMP} + 大额存单 {CD_CURRENT} − 借款 {ST_LOAN + LT_LOAN:.2f} − 租赁 {LEASE:.2f} − 应付少数股利 {DIV_PAYABLE_MINORITY} − 中期股利 {DECLARED_INTERIM_DIV} − 经营备付 {OPERATING_RESERVE}）")
    print(f"药明合联：出售前约 {XDC_HELD_PRE:.3f} 亿股，8 月售出 {XDC_SOLD:.4f}，余 {XDC_REMAIN:.3f} 亿股 × {XDC_PRICE_HKD} 港元 = {xdc_remain_mv:.1f}；折价、税后 {xdc_remain_after_tax:.1f}；8 月出售所得税后 {xdc_sale_after_tax:.1f} → 合计 {XDC_VALUE:.1f}")
    print(f"其他非流动金融资产折算 {NCFA_VALUE:.1f}；基金联营 {LP_VALUE:.1f}；处置应收 {DIVEST_RECEIVABLE:.1f} → 非经营资产合计 {NON_OP:.1f}")
    print(f"净现金+非经营资产 {NET_CASH_ADJ + NON_OP:.1f}，每股 {(NET_CASH_ADJ + NON_OP) / SHARES:.2f} 元")

    print("\n== 2026 年正常化（亿元）")
    print(f"H1：扣非 {H1_DEDUCT} + 汇兑净损失税后 {(H1_FX_LOSS - H1_HEDGE_GAIN) * (1 - TAX_N):.2f} − 生物资产公允价值 {H1_BIO_FV * 0.85:.2f} + 理财收益 {H1_WMP * (1 - TAX_N):.2f} = 正常化 {h1_norm:.2f}")
    print(f"H1：其中税后净利息 {h1_net_int:.2f}、权益法 {H1_EQUITY_INC}；经营净利 {h1_op:.2f}（经营净利率 {H1_OP_MARGIN:.2%}）；H2 股份支付增量税后 {SBC_STEPUP_AT:.2f}")
    for k, s in SCEN.items():
        b = build(s)
        print(f"{k}: 2026 收入 {b['rev26']:.1f}；H2 经营净利 {b['h2_op']:.1f}；全年经营净利 {b['op26']:.1f}；全年正常化归母（含净利息与权益法） {b['norm26']:.1f}")

    print("\n== 三情景（股权成本 9%，年中折现，价格日 2026-10-20）")
    res = {}
    for k, s in SCEN.items():
        v = value(s, 0.09)
        res[k] = v
        b = v["b"]
        print(f"[{k}] p={s['p']:.2f}  {s['note']}")
        print("   年份  收入  增速  经营净利率  经营净利  再投资率  所有者收益  OE增速")
        oe_prev = b["op26"] * (1 - RR_2026)
        for i, y in enumerate(YEARS):
            print(f"   {y}  {b['rev'][i]:7.1f}  {s['growth'][i]:+.0%}  {s['margin'][i]:.1%}  {b['op'][i]:6.1f}  {s['rr'][i]:.0%}  {b['oe'][i]:6.1f}  {b['oe'][i] / oe_prev - 1:+.1%}")
            oe_prev = b["oe"][i]
        print(f"   终值：增长 {s['g_t']:.1%}，再投资率 {b['rr_t']:.1%}（增量回报 {s['roiic_t']:.0%}），2032 年所有者收益 {b['oe_t1']:.1f}")
        print(f"   H2-2026 所有者收益 {b['oe_h2']:.1f} + 显性期现值 {v['pv_exp']:.1f} + 终值现值 {v['pv_tv']:.1f}（终值占经营价值 {v['tv_share']:.0%}）= 经营价值 {v['op_value']:.1f}")
        print(f"   股权价值 {v['equity']:.1f} → 每股 V = {v['v']:.2f}；剔除库存股 {v['v_ex']:.2f}；按未转股债务口径 {v['v_cb_debt']:.2f}（取低 {min(v['v'], v['v_cb_debt']):.2f}）")
    vw = weighted(0.09)
    vw_ex = sum(SCEN[k]["p"] * res[k]["v_ex"] for k in SCEN)
    print(f"\n加权 V = {vw:.2f} 元；P/V = {PRICE_A / vw:.3f}；剔除库存股 V = {vw_ex:.2f}，P/V = {PRICE_A / vw_ex:.3f}；H 股价折人民币 P/V = {price_h_cny / vw:.3f}")
    alt = weighted(0.09, probs=dict(bear=0.20, base=0.50, bull=0.30))
    print(f"概率敏感性：熊 20%/基 50%/牛 30% 时 V {alt:.2f}，P/V {PRICE_A / alt:.3f}")
    cb_low = sum(SCEN[k]["p"] * min(res[k]["v"], res[k]["v_cb_debt"]) for k in SCEN)
    print(f"转债逐情景取低（若视同未转股）加权 V {cb_low:.2f}；转债已转股，正式口径用总股本 {SHARES:.4f}")
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f"股权成本 8%：加权 V {v8:.2f}（熊 {value(SCEN['bear'], 0.08)['v']:.2f}/基 {value(SCEN['base'], 0.08)['v']:.2f}/牛 {value(SCEN['bull'], 0.08)['v']:.2f}）")
    print(f"股权成本 10%：加权 V {v10:.2f}（熊 {value(SCEN['bear'], 0.10)['v']:.2f}/基 {value(SCEN['base'], 0.10)['v']:.2f}/牛 {value(SCEN['bull'], 0.10)['v']:.2f}）")
    bands = (0.75 * vw, 0.90 * vw, 1.10 * vw)
    print(f"V 不变时：≤{bands[0]:.1f} 明显低估；{bands[0]:.1f}-{bands[1]:.1f} 温和低估；{bands[1]:.1f}-{bands[2]:.1f} 大致合理；>{bands[2]:.1f} 偏贵")

    # 隐含回报：基准情景现金流使现值等于 A 股价×总股本
    target = mcap_a_all
    irr = bisect(lambda r: value(SCEN["base"], r)["equity"] - target, 0.03, 0.20)
    irr_w = bisect(lambda r: weighted(r) * SHARES - target, 0.03, 0.20)
    print(f"\n现价隐含回报（基准情景）：{irr:.2%}；按概率加权现金流：{irr_w:.2%}")

    # 反向 DCF
    base_b = build(SCEN["base"])
    oe_norm26 = base_b["op26"] * (1 - 0.30)   # 2026 经营净利按 30% 常态再投资率折成所有者收益
    need = target - NET_CASH_ADJ - NON_OP - base_b["oe_h2"]

    def pv_const(g):
        pv, cf = 0.0, oe_norm26
        for i in range(10):
            cf *= 1 + g
            pv += cf / 1.09 ** t_mid(2027 + i)
        tv = cf * 1.025 / (0.09 - 0.025)
        return pv + tv / 1.09 ** t_mid(2036)
    g10 = bisect(lambda g: pv_const(g) - need, -0.10, 0.30)
    oe27 = oe_norm26
    g_perp = bisect(lambda g: oe27 * (1 + g) / (0.09 - g) / 1.09 ** t_mid(2026) - need, -0.05, 0.085)
    print(f"反向 DCF：2026 常态所有者收益 {oe_norm26:.1f}；现价隐含 2027-2036 年所有者收益年增 {g10:.2%}（之后 2.5%）；或隐含永续增速 {g_perp:.2%}")

    # 交叉验证
    norm26 = base_b["norm26"]
    ev = target - NET_CASH_ADJ - NON_OP
    ebit = base_b["op26"] / (1 - TAX_N)
    print("\n== 交叉验证")
    print(f"市值/2026 正常化归母 {target / norm26:.1f}×；经营市值/2026 经营净利 {ev / base_b['op26']:.1f}×；EV/EBIT {ev / ebit:.1f}×（EBIT≈{ebit:.0f}）")
    print(f"A、H 各按本市价：市值/正常化归母 {mcap_mixed / norm26:.1f}×；EV/EBIT {(mcap_mixed - NET_CASH_ADJ - NON_OP) / ebit:.1f}×")
    print(f"市值/TTM 扣非 {target / 182.31:.1f}×；PB {target / 833.34:.2f}×；正常化 ROE {norm26 / ((797.12 + 833.34) / 2):.1%}")
    print(f"过去 12 个月股息 2.0893 元/股 → 股息率 {2.0893 / PRICE_A:.2%}；12 个月内无注销式回购（2026 年回购 31.6 亿均用于员工激励）")
    hist = {2022: (2398.03, 83.45), 2023: (2160.13, 97.48), 2024: (1589.55, 99.88), 2025: (2704.48, 132.41)}
    print("历史 年末市值/扣非：" + "；".join(f"{y} {m / d:.1f}×" for y, (m, d) in hist.items()))

    # 证伪触发后的 V
    falsifiers = {
        "F1 三季报弱": dict(bear=0.35, base=0.50, bull=0.15),
        "F2 认定恢复或列入 BCC": dict(bear=0.50, base=0.40, bull=0.10),
        "F3 2027 指引 <10%": dict(bear=0.35, base=0.55, bull=0.10),
        "F5 诉讼终局胜诉且指引 ≥20%": dict(bear=0.10, base=0.50, bull=0.40),
    }
    print("\n== 证伪触发后的独立 V（9%）")
    fv = {}
    for name, pr in falsifiers.items():
        fv[name] = weighted(0.09, probs=pr)
        print(f"{name}: V {fv[name]:.2f}，P/V {PRICE_A / fv[name]:.3f}")
    fv["F4 化学毛利率跌破 50%"] = weighted(0.09, margin_shift=-0.02)
    print(f"F4 化学毛利率跌破 50%（各情景经营净利率 -2pp）: V {fv['F4 化学毛利率跌破 50%']:.2f}")

    # 三季报核对点（基准估计）：H2 收入按 Q3 49%/Q4 51% 拆分；Q3 股份支付增量税后约为 H2 增量一半；汇兑损失估 2 亿
    q3_rev = SCEN["base"]["h2_rev"] * 0.49
    q3_wmp_at = H1_WMP * (1 - TAX_N) / 2      # 理财收益列入非经常，扣非不含
    q3_fx_at = 2.0 * (1 - TAX_N)              # Q3 人民币续升值的汇兑损失（估）
    q3_deduct = (q3_rev * SCEN["base"]["h2_margin"] - SBC_STEPUP_AT / 2 + H2_NET_INT / 2 - q3_wmp_at
                 + H2_EQUITY_INC / 2 - q3_fx_at)
    q3_reported = q3_deduct + 31.43 * (1 - XDC_TAX)
    q3 = dict(rev=q3_rev, deduct=q3_deduct, reported=q3_reported)
    print(f"\n三季报基准估计：Q3 收入约 {q3_rev:.0f} 亿；扣非归母约 {q3_deduct:.0f} 亿（含汇兑损失、不含理财）；报告归母约 {q3_reported:.0f} 亿（含出售药明合联税后约 {31.43 * (1 - XDC_TAX):.0f} 亿）")

    out = dict(
        shares=SHARES, shares_ex_treasury=SHARES_EX_TREASURY, net_cash_adj=NET_CASH_ADJ, non_op=NON_OP,
        xdc_value=XDC_VALUE, v={k: res[k]["v"] for k in res}, v_ex={k: res[k]["v_ex"] for k in res},
        v_cb_debt={k: res[k]["v_cb_debt"] for k in res}, v_weighted=vw, pv=PRICE_A / vw,
        v_weighted_ex=vw_ex, v8=v8, v10=v10, irr_base=irr, irr_weighted=irr_w, g10=g10, g_perp=g_perp,
        norm26={k: build(SCEN[k])["norm26"] for k in SCEN}, op26={k: build(SCEN[k])["op26"] for k in SCEN},
        oe_norm26=oe_norm26,
        oe_growth_base=[res["base"]["b"]["oe"][0] / oe_norm26 - 1]
        + [res["base"]["b"]["oe"][i] / res["base"]["b"]["oe"][i - 1] - 1 for i in range(1, 5)],
        v_alt_probs=alt, v_cb_low=cb_low, q3=q3, norm25=norm25,
        tv_share={k: res[k]["tv_share"] for k in res}, falsifier_v=fv, bands=bands,
        mcap_a_all=mcap_a_all, mcap_mixed=mcap_mixed, price_h_cny=price_h_cny)
    if "--json" in sys.argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
