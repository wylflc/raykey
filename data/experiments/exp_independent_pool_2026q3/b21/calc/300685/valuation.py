#!/usr/bin/env python3
"""艾德生物（300685）独立估值：OI-291 b21 深度版。

运行：python3 valuation.py
输入全部写在脚本内。金额单位亿元，股本亿股，价格与 V 为元/股。
出处写在注释里，页码为 PDF 物理页（txt 中的「=== 第 N 页 ===」）。
"""
from datetime import date

# ---------------------------------------------------------------- 快照与股本
PRICE = 18.75                  # 2026-10-21 收盘（brief.md）
PRICE_DATE = date(2026, 10, 21)
SHARES_TOTAL = 3.90105169      # 股本 390,105,169 股（2026H1_report 第 38 页；brief 3.9011）
BUYBACK_SHARES = 0.09119300    # 回购专户 9,119,300 股，方案为全部注销（buyback_20261009_264735 第 1 页）
TREASURY_0630_SHARES = 0.08554300  # 6-30 库存股 1.6122 亿元对应 8,554,300 股（2026H1_report 第 31-32 页）
SHARES_VAL = SHARES_TOTAL - BUYBACK_SHARES   # 框架：拟注销回购股份扣除

# ---------------------------------------------------------------- 2026-06-30 资产负债（2026H1_report 第 36-38 页）
CASH = 10.52115895             # 货币资金，含定期存单 7.5905（第 20、128 页：计划持有至到期，未质押）
TFA = 1.73831009               # 交易性金融资产：银行 1.55、券商 0.15 中低风险理财（第 19-20 页）
ST_LOAN = 0.04002611           # 短期借款
LT_LOAN = 1.80080000           # 长期借款，均为 36 个月信用借款（第 114 页）
LT_LOAN_CUR = 0.05174151       # 一年内到期的长期借款（第 113 页）
LEASE = 0.01997116 + 0.05476766  # 租赁负债 + 一年内到期租赁负债：只列示不扣（框架第 2 条）
OP_RESERVE = 0.60              # 经营备付：约 1 个月付现成本（2026H1 年化付现成本约 7.1 亿）
BUYBACK_CASH_AFTER_0630 = 1.71127899 - 1.61220892  # 7-9 月回购付现（buyback_20261009 第 1 页 − 6-30 库存股）
DIVIDEND_DECLARED_UNPAID = 0.0  # 2025 年度分红已于 2026-05-18 除息派发（dividend_20260509_073869）
NON_OP = 0.53                  # 其他权益工具投资：赛陆医疗 2.381%（2026H1_report 第 97 页；invest_20251009_937140）
NON_OP_BEAR_HAIRCUT = 0.5      # 熊市情景按五折（标的仍亏损）

# 外币货币资金（2026H1_report 第 128 页）：外币余额（亿外币）与 6-30 折算汇率
USD_CASH, EUR_CASH, HKD_CASH = 1.00946137, 0.17995232, 0.47416956
USD_0630, EUR_0630, HKD_0630 = 6.8109, 7.7671, 0.86855
# 估值日附近汇率：2026-10-16 中间价 USD 6.7220、EUR 7.5228（中国经济网，见正文 web_facts；港币按联系汇率随美元）
USD_NOW, EUR_NOW = 6.7220, 7.5228
HKD_NOW = HKD_0630 * USD_NOW / USD_0630
# 三季度末汇率代理：2026-09-28 中间价 USD 6.7399、EUR 7.6564（同上）
USD_0930, EUR_0930 = 6.7399, 7.6564
FX_AR_USD, FX_AR_EUR = 0.05007122, 0.01078908   # 外币应收账款（亿外币，2026H1_report 第 128 页）

# ---------------------------------------------------------------- 历史利润表（元→亿元）
# 核心经营利润 = 营收 − 营业成本 − 税金及附加 − 销售 − 管理 − 研发 + 经常性减值 + 营业外收支净额 + 股份支付冲回调整
# 经常性减值：应收账款、应收票据、其他应收款与合同资产；剔除艾维克长期应收款坏账与长期股权投资减值。
# 不含：其他收益（政府补助、加计抵减）、利息、汇兑、理财与联营收益、资产处置。
HIST = {
    # 2025_annual_report 第 71-72、154 页；2024 年为同表上年数
    "2024": dict(rev=11.08948700, cogs=1.69145096, tax_s=0.05003158, sell=3.58816273, adm=0.72214299,
                 rnd=2.16114223, credit=-0.30218315, lt_rec=-0.17625000, asset=-0.08150641, lt_eq=-0.08228761,
                 nonop=0.00176975 - 0.03274297, sbc_adj=0.0, np=2.54863445),
    # 2025 年股份支付确认费用 −772.16 万元（冲回，2025_annual_report 第 178 页「本期以权益结算的股份支付确认的费用总额」），正常化时扣回
    "2025": dict(rev=11.97733641, cogs=2.08514046, tax_s=0.13178447, sell=3.34051443, adm=0.72915023,
                 rnd=1.77587377, credit=-0.26123890, lt_rec=-0.18372116, asset=-0.04981503, lt_eq=-0.05021467,
                 nonop=0.00331418 - 0.06837119, sbc_adj=-0.07721560, np=3.61255321),
    # 2026H1_report 第 41 页上年同期栏
    "2025H1": dict(rev=5.79344558, cogs=0.92683801, tax_s=0.06980665, sell=1.49133204, adm=0.43671009,
                   rnd=0.90526231, credit=-0.05726318, lt_rec=0.0, asset=0.00055922, lt_eq=0.0,
                   nonop=0.00203351 - 0.03431681, sbc_adj=0.0, np=1.89037383),
    # 2026H1_report 第 41 页
    "2026H1": dict(rev=5.59346697, cogs=0.92800836, tax_s=0.06620383, sell=1.29365112, adm=0.33107935,
                   rnd=0.91174528, credit=-0.04158750, lt_rec=0.0, asset=0.00030381, lt_eq=0.0,
                   nonop=0.00000279 - 0.03731189, sbc_adj=0.0, np=1.66125205),
}
FX_LOSS = {"2025": 0.06845624, "2026H1": 0.32338666}   # 汇兑损失（2025_annual_report 第 153 页；2026H1_report 第 122 页）
SUBSIDY = {"2025": 0.18327271, "2026H1": 0.05674680}   # 计入其他收益的政府补助（同上）


def core_ebit(h):
    gross_op = h["rev"] - h["cogs"] - h["tax_s"] - h["sell"] - h["adm"] - h["rnd"]
    recurring_imp = (h["credit"] - h["lt_rec"]) + (h["asset"] - h["lt_eq"])
    return gross_op + recurring_imp + h["nonop"] + h["sbc_adj"]


CORE = {k: core_ebit(v) for k, v in HIST.items()}
CORE["2025H2"] = CORE["2025"] - CORE["2025H1"]
REV = {k: v["rev"] for k, v in HIST.items()}
REV["2025H2"] = REV["2025"] - REV["2025H1"]
CORE["TTM"] = CORE["2025H2"] + CORE["2026H1"]
REV["TTM"] = REV["2025H2"] + REV["2026H1"]

# ---------------------------------------------------------------- 正常化参数
TAX = 0.12                     # 有效税率：2024、2025 年 12.1%，2026H1 11.0%（15% 高新 + 研发加计扣除，2025_annual_report 第 155 页）
TAX_SURCHARGE = 0.012          # 税金及附加 / 营收（2025 年 1.10%，2026H1 1.18%；增值税 13% 后）
# 2026 年正常化净财务收益（税前）：利息收入约 0.27（2026H1 0.134，下半年现金回升）− 利息费用约 0.043（2026H1 0.021）
# + 理财收益约 0.055（2026H1 投资收益 + 公允价值变动 0.032）
INT_INC_2026, INT_EXP_2026, WEALTH_2026 = 0.27, 0.043, 0.055
NETFIN_2026_PRETAX = INT_INC_2026 - INT_EXP_2026 + WEALTH_2026
DONATION_2026 = {"bear": 0.037 + 0.035, "base": 0.037 + 0.030, "bull": 0.037 + 0.028}  # 营业外支出（主要为捐赠），扣非口径加回

# 2026H2 情景（营收、毛利率、费用；other = 经常性减值 + 营业外收支）
H2_2026 = {
    "bear": dict(rev=5.95, gm=0.81, sell=1.80, adm=0.32, rnd=0.92, other=-0.08),
    "base": dict(rev=6.15, gm=0.82, sell=1.75, adm=0.30, rnd=0.90, other=-0.07),
    "bull": dict(rev=6.35, gm=0.83, sell=1.72, adm=0.29, rnd=0.88, other=-0.06),
}


def h2_core(s):
    p = H2_2026[s]
    return p["rev"] * (p["gm"] - TAX_SURCHARGE) - p["sell"] - p["adm"] - p["rnd"] + p["other"]


# ---------------------------------------------------------------- DCF 情景（2027-2036 逐年；终值）
K_REINV = 0.55   # 每增加 1 元营收的再投资：营运资本 0.45（应收约占营收 52%，扣应付与薪酬税费）+ 增长性资本开支 0.10
SCEN = {
    "bear": dict(p=0.25,
                 growth=[-0.08, -0.03, 0.02, 0.03, 0.03, 0.03, 0.03, 0.025, 0.025, 0.025],
                 margin=[0.29, 0.27, 0.27, 0.27, 0.27, 0.27, 0.27, 0.27, 0.27, 0.27],
                 g_term=0.02, ronic=0.20,
                 text="2027 年起肿瘤基因检测试剂或检测服务纳入省级／联盟带量采购，或病理收费目录大幅压价；"
                      "营收 2027 −8%、2028 −3%，之后 2-3%；核心利润率 29%→27%；终值增长 2%、RONIC 20%；赛陆五折"),
    "base": dict(p=0.50,
                 growth=[0.04, 0.06, 0.06, 0.05, 0.05, 0.045, 0.04, 0.035, 0.03, 0.03],
                 margin=[0.325, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32],
                 g_term=0.025, ronic=0.30,
                 text="病理收费目录落地后的重新议价在 2027 年基本完成，院内合规检测回流与新标志物带动量增；"
                      "国际及药企业务中高个位数增长；营收 2027 +4%、2028-2029 +6%、2030-2031 +5%，之后降到 3%；"
                      "核心利润率 32.5%→32%（研发费率回到约 16.5%）；终值增长 2.5%、RONIC 30%"),
    "bull": dict(p=0.25,
                 growth=[0.08, 0.10, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.035],
                 margin=[0.345, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35],
                 g_term=0.025, ronic=0.40,
                 text="国药渠道与合规出清提升院内份额，HRD、MRD、大 Panel、甲状腺 panel 与海外伴随诊断放量；"
                      "营收 2027-2031 年增 8-10%；核心利润率 34.5%→35%；终值增长 2.5%、RONIC 40%"),
}
COE = 0.09
STUB = (date(2026, 12, 31) - PRICE_DATE).days / 365.0   # 估值日到 2026 年末的年数


def fx_reval():
    return (USD_CASH * (USD_NOW - USD_0630) + EUR_CASH * (EUR_NOW - EUR_0630)
            + HKD_CASH * (HKD_NOW - HKD_0630))


def net_cash_adj():
    debt = ST_LOAN + LT_LOAN + LT_LOAN_CUR
    return (CASH + TFA - debt - OP_RESERVE - BUYBACK_CASH_AFTER_0630 - DIVIDEND_DECLARED_UNPAID
            + fx_reval())


def rev_2026(s):
    return HIST["2026H1"]["rev"] + H2_2026[s]["rev"]


def core_2026(s):
    return CORE["2026H1"] + h2_core(s)


def norm_np_2026(s):
    return core_2026(s) * (1 - TAX) + NETFIN_2026_PRETAX * (1 - TAX)


def kf_plus_fx_2026(s):
    """F1 口径：扣非归母净利 + 税后汇兑损失 ≈（核心经营利润 + 捐赠等营业外支出 + 利息收入 − 利息费用）×（1 − 税率）。"""
    return (core_2026(s) + DONATION_2026[s] + INT_INC_2026 - INT_EXP_2026) * (1 - TAX)


# 2026Q3 估计（三季报 2026-10-23 预约，下次核对点）
Q3_2026 = dict(rev=2.90, core_margin=0.30, other_income=0.03, int_net=0.06, wealth=0.012, tax=0.11)
Q3_2025 = dict(rev=2.86288423, np=0.73468556, dnp=0.65619530)   # 2025_annual_report 第 7 页


def q3_fx_loss():
    """按 6-30 外币余额与 9-28 中间价估算的三季度汇兑损失（税前）。"""
    return (USD_CASH * (USD_0630 - USD_0930) + EUR_CASH * (EUR_0630 - EUR_0930)
            + HKD_CASH * HKD_0630 * (1 - USD_0930 / USD_0630)
            + FX_AR_USD * (USD_0630 - USD_0930) + FX_AR_EUR * (EUR_0630 - EUR_0930))


def q3_estimate():
    q = Q3_2026
    core = q["rev"] * q["core_margin"]
    pbt = core + q["other_income"] + q["int_net"] + q["wealth"] - q3_fx_loss()
    return dict(rev=q["rev"], core=core, fx=q3_fx_loss(), np=pbt * (1 - q["tax"]))


def pv_flat_perpetuity(c, r=COE):
    """2027 年起每年 c（年中到账、不增长）的现值。"""
    return c * (1 + r) ** (0.5 - STUB) / r


def path(s, overrides=None):
    """返回逐年表：(年度, 营收, 增速, 利润率, NOPAT, 再投资, 所有者收益)。"""
    sc = dict(SCEN[s])
    if overrides:
        sc.update(overrides)
    rows = []
    rev = rev_2026(s)
    for i, y in enumerate(range(2027, 2037)):
        g = sc["growth"][i]
        new = rev * (1 + g)
        nopat = new * sc["margin"][i] * (1 - TAX)
        reinv = max(0.0, sc.get("k", K_REINV) * (new - rev))   # 收入下降年份不计营运资本释放（保守）
        rows.append((y, new, g, sc["margin"][i], nopat, reinv, nopat - reinv))
        rev = new
    return rows, sc


def equity_value(s, r=COE, overrides=None, net_cash=None, non_op=None):
    rows, sc = path(s, overrides)
    pv_explicit = sum(oe / (1 + r) ** ((y - 2026) - 0.5 + STUB) for (y, _, _, _, _, _, oe) in rows)
    nopat_last = rows[-1][4]
    g = sc["g_term"]
    oe_t1 = nopat_last * (1 + g) * (1 - g / sc["ronic"])
    tv = oe_t1 * (1 + r) ** 0.5 / (r - g)            # 年中现金流口径，终值落在 2036 年末
    pv_tv = tv / (1 + r) ** (10 + STUB)
    oe_h2 = h2_core(s) * (1 - TAX)                     # 2026H2 经营所有者收益：年内到账，不折现
    nc = net_cash_adj() if net_cash is None else net_cash
    if non_op is None:
        non_op = NON_OP * (NON_OP_BEAR_HAIRCUT if s == "bear" else 1.0)
    eq = pv_explicit + pv_tv + oe_h2 + nc + non_op
    return dict(eq=eq, pv_explicit=pv_explicit, pv_tv=pv_tv, oe_h2=oe_h2, net_cash=nc, non_op=non_op,
                rows=rows, tv_share=pv_tv / (pv_explicit + pv_tv), sc=sc)


def v_per_share(s, r=COE, shares=SHARES_VAL, **kw):
    return equity_value(s, r, **kw)["eq"] / shares


def weighted(r=COE, shares=SHARES_VAL, probs=None, **kw):
    probs = probs or {k: SCEN[k]["p"] for k in SCEN}
    return sum(probs[k] * v_per_share(k, r, shares, **kw) for k in SCEN)


def solve(f, lo, hi, target=0.0, n=200):
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def implied_irr(s="base"):
    return solve(lambda r: v_per_share(s, r), 0.03, 0.30, PRICE)


def implied_irr_weighted():
    return solve(lambda r: weighted(r), 0.03, 0.30, PRICE)


def reverse_dcf_growth():
    """维持基准利润率 32%、再投资系数与终值 2.5%，现价隐含 2027-2036 年营收与所有者收益的均匀年增速。"""
    def f(g):
        ov = dict(growth=[g] * 10, margin=[0.32] * 10)
        return v_per_share("base", COE, overrides=ov)
    return solve(f, -0.10, 0.25, PRICE)


def reverse_perpetual():
    """以基准 2027 年 NOPAT 为起点、RONIC 30%，现价隐含的永续增速（不含显性期）。"""
    rows, sc = path("base")
    nopat27 = rows[0][4]
    ops_needed = PRICE * SHARES_VAL - (h2_core("base") * (1 - TAX) + net_cash_adj() + NON_OP)

    def f(g):
        return nopat27 * (1 - g / sc["ronic"]) / (COE - g) * (1 + COE) ** (0.5 - STUB)
    return solve(f, -0.05, 0.085, ops_needed)


def fmt(x, nd=2):
    return f"{x:.{nd}f}"


def band_prices(v):
    return dict(obvious=0.75 * v, mild=0.90 * v, fair=1.10 * v)


def verdict(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print("== 股本与经调整净现金 ==")
    print(f"估值股本 {SHARES_VAL:.4f} 亿股（总股本 {SHARES_TOTAL:.4f} − 拟注销回购 {BUYBACK_SHARES:.4f}；"
          f"其中 6-30 库存股 {TREASURY_0630_SHARES:.4f}）")
    debt = ST_LOAN + LT_LOAN + LT_LOAN_CUR
    print(f"现金类 {CASH + TFA:.3f}（货币资金 {CASH:.3f} + 理财 {TFA:.3f}）；有息负债 {debt:.3f}；"
          f"租赁负债 {LEASE:.3f}（只列示）；经营备付 {OP_RESERVE:.2f}；6-30 后回购付现 {BUYBACK_CASH_AFTER_0630:.3f}；"
          f"外币资金重估 {fx_reval():+.3f}（USD {USD_0630}→{USD_NOW}，EUR {EUR_0630}→{EUR_NOW}）")
    print(f"经调整净现金 {net_cash_adj():.3f}；非经营资产 {NON_OP:.2f}（熊市五折）")

    print("\n== 核心经营利润（口径见脚本注释）==")
    for k in ["2024", "2025", "2025H1", "2025H2", "2026H1", "TTM"]:
        print(f"{k:>7}: 营收 {REV[k]:6.3f}  核心经营利润 {CORE[k]:6.3f}  利润率 {CORE[k] / REV[k]:6.1%}")
    h = HIST["2025"]
    one_off_2025 = -(h["lt_rec"] + h["lt_eq"])
    print(f"2025 报表归母 {h['np']:.3f}；一次性：艾维克长期应收款坏账 {-h['lt_rec']:.3f}、长期股权投资减值 {-h['lt_eq']:.3f}、"
          f"股份支付冲回 {-h['sbc_adj']:.3f}、汇兑损失 {FX_LOSS['2025']:.3f}、政府补助 {SUBSIDY['2025']:.3f}")
    print(f"2026H1 报表归母 {HIST['2026H1']['np']:.3f}；汇兑损失 {FX_LOSS['2026H1']:.3f}；政府补助 {SUBSIDY['2026H1']:.3f}")
    _ = one_off_2025

    print("\n== 2026 年（中报实际 + 下半年情景）==")
    for s in ["bear", "base", "bull"]:
        print(f"{s}: 2026H2 营收 {H2_2026[s]['rev']:.2f}，核心经营利润 {h2_core(s):.3f}（{h2_core(s) / H2_2026[s]['rev']:.1%}）；"
              f"全年营收 {rev_2026(s):.2f}，核心经营利润 {core_2026(s):.3f}（{core_2026(s) / rev_2026(s):.1%}），"
              f"正常化归母净利 {norm_np_2026(s):.2f}（含税后净财务收益 {NETFIN_2026_PRETAX * (1 - TAX):.3f}）")

    print("F1 口径（扣非归母 + 税后汇兑损失）2026E：" + "，".join(f"{s} {kf_plus_fx_2026(s):.2f}" for s in SCEN))
    q3 = q3_estimate()
    print(f"2026Q3 估计：营收 {q3['rev']:.2f}（同比 {q3['rev'] / Q3_2025['rev'] - 1:+.1%}），核心经营利润 {q3['core']:.2f}，"
          f"汇兑损失约 {q3['fx']:.3f}，归母净利约 {q3['np']:.2f}（2025Q3 {Q3_2025['np']:.3f}，含艾维克坏账 0.182）")

    print("\n== 情景路径与价值（股权成本 9%）==")
    res = {}
    for s in ["bear", "base", "bull"]:
        e = equity_value(s)
        res[s] = e
        sc = e["sc"]
        print(f"-- {s}（p={sc['p']}）：{sc['text']}")
        oe26 = core_2026(s) * (1 - TAX)
        prev = oe26
        gs = []
        for (y, rv, g, m, nopat, reinv, oe) in e["rows"][:5]:
            gs.append(oe / prev - 1)
            print(f"   {y}: 营收 {rv:6.2f}（{g:+.1%}） 利润率 {m:.1%} NOPAT {nopat:5.2f} 再投资 {reinv:4.2f} 所有者收益 {oe:5.2f}（{oe / prev - 1:+.1%}）")
            prev = oe
        reinv5 = sum(r[5] for r in e["rows"][:5])
        nopat5 = sum(r[4] for r in e["rows"][:5])
        d_nopat = e["rows"][4][4] - oe26
        inc_ret = d_nopat / reinv5 if reinv5 > 0 else float("nan")
        print(f"   2026 经营所有者收益 {oe26:.2f}；2027-2031 再投资率 {reinv5 / nopat5:.1%}，增量回报 "
              f"{inc_ret:.0%}（NOPAT 增量 {d_nopat:.2f} ÷ 累计再投资 {reinv5:.2f}）；"
              f"终值增长 {sc['g_term']:.1%}，终值再投资率 {sc['g_term'] / sc['ronic']:.1%}（RONIC {sc['ronic']:.0%}）")
        print(f"   显性期现值 {e['pv_explicit']:.2f} + 终值现值 {e['pv_tv']:.2f} + 2026H2 所有者收益 {e['oe_h2']:.2f} "
              f"+ 净现金 {e['net_cash']:.2f} + 非经营 {e['non_op']:.2f} = 股权 {e['eq']:.2f}；终值占经营价值 {e['tv_share']:.0%}")
        print(f"   V = {e['eq'] / SHARES_VAL:.2f}（按总股本 {SHARES_TOTAL:.4f}：{e['eq'] / SHARES_TOTAL:.2f}）；"
              f"8%：{v_per_share(s, 0.08):.2f}；10%：{v_per_share(s, 0.10):.2f}")
        res[s]["growth5"] = gs

    vw = weighted()
    vw8, vw10 = weighted(0.08), weighted(0.10)
    vw_total = weighted(shares=SHARES_TOTAL)
    pv = PRICE / vw
    print("\n== 加权 ==")
    print(f"加权 V = {vw:.2f}；P/V = {pv:.3f}（{verdict(pv)}）；8%：{vw8:.2f}；10%：{vw10:.2f}")
    print(f"对照：按总股本 {SHARES_TOTAL:.4f} 亿股（不扣回购专户股份）加权 V = {vw_total:.2f}，P/V = {PRICE / vw_total:.3f}")
    b = band_prices(vw)
    print(f"V 不变时各档价格：明显低估 ≤ {b['obvious']:.2f}；温和低估 ≤ {b['mild']:.2f}；大致合理 ≤ {b['fair']:.2f}；偏贵 > {b['fair']:.2f}")
    irr_b = implied_irr("base")
    irr_w = implied_irr_weighted()
    print(f"现价隐含回报：基准情景 {irr_b:.2%}；三情景加权 {irr_w:.2%}")
    g10 = reverse_dcf_growth()
    gp = reverse_perpetual()
    print(f"反向 DCF：现价隐含 2027-2036 营收与所有者收益年增 {g10:.2%}（利润率 32%，终值 2.5%）；"
          f"隐含永续增速 {gp:.2%}（2027 NOPAT {path('base')[0][0][4]:.2f}，RONIC 30%）")

    print("\n== 交叉验证 ==")
    mcap = PRICE * SHARES_VAL
    nc = net_cash_adj()
    ev = mcap - nc - NON_OP
    print(f"市值（估值股本）{mcap:.2f}；EV {ev:.2f}；EV/2026E 核心经营利润 {ev / core_2026('base'):.1f}x；"
          f"EV/2026E NOPAT {ev / (core_2026('base') * (1 - TAX)):.1f}x；P/2026E 正常化归母 {mcap / norm_np_2026('base'):.1f}x")
    div_yield = 0.45 / PRICE
    bb_yield = 1.71127899 / (PRICE * SHARES_TOTAL)
    print(f"股息率 {div_yield:.2%}；2025-11～2026-09 回购 1.71 亿 / 市值 {bb_yield:.2%}；合计 {div_yield + bb_yield:.2%}")
    print(f"控制权转让价 21.20 元对应股权价值 {21.20 * SHARES_VAL:.1f} 亿，为加权 V 的 {21.20 / vw:.2f} 倍；回购均价 "
          f"{1.71127899e8 / 9119300:.2f} 元")

    print("\n== 敏感性（基准情景，9%）==")
    vb = v_per_share("base")
    sub = pv_flat_perpetuity(0.15 * (1 - TAX)) / SHARES_VAL + 0.09 * (1 - TAX) / SHARES_VAL
    print(f"基准 V {vb:.2f}；保留政府补助（每年税前 0.15，不增长）+{sub:.2f}")
    for lab, ov in [("利润率 +1pp", dict(margin=[m + 0.01 for m in SCEN['base']['margin']])),
                    ("利润率 −1pp", dict(margin=[m - 0.01 for m in SCEN['base']['margin']])),
                    ("再投资系数 0.45", dict(k=0.45)), ("再投资系数 0.65", dict(k=0.65)),
                    ("终值增长 2.0%", dict(g_term=0.02)), ("终值增长 3.0%", dict(g_term=0.03)),
                    ("终值 RONIC 20%", dict(ronic=0.20)), ("终值 RONIC 50%", dict(ronic=0.50))]:
        print(f"   {lab}: V {v_per_share('base', overrides=ov):.2f}")
    print(f"   不扣经营备付：+{OP_RESERVE / SHARES_VAL:.2f}；外币资金按 6-30 汇率：+{-fx_reval() / SHARES_VAL:.2f}")

    print("\n== 证伪触发后的 V ==")
    f1 = weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})
    f2 = v_per_share("bear")
    f3 = v_per_share("base", overrides=dict(growth=[0.02] * 5 + [0.025] * 5, margin=[0.29] * 10))
    f4 = v_per_share("base", overrides=dict(margin=[0.28] * 10))
    f5 = weighted(net_cash=net_cash_adj() * 0.7)
    print(f"F1 2026 营收 < 11.40 或扣非归母 + 税后汇兑损失 < 3.50：概率改为熊 50%／基 40%／牛 10%，V = {f1:.2f}")
    print(f"F2 肿瘤基因检测试剂或服务纳入带量采购并执行、主力产品降价 ≥ 30%：取熊市情景 V = {f2:.2f}")
    print(f"F3 2027H1 国内销售同比 ≤ −5%：基准增速降到 2%、利润率 29%，V = {f3:.2f}")
    print(f"F4 2027 核心经营利润率 < 29%：基准利润率降到 28%，V = {f4:.2f}")
    print(f"F5 交割后现金过半存放集团财务公司或分红回购 < 归母 40%：净现金打七折，V = {f5:.2f}")

    print("\n== 登记用数字 ==")
    out = dict(
        v={s: round(v_per_share(s), 2) for s in SCEN}, v_weighted=round(vw, 2), pv=round(pv, 3),
        v8=round(vw8, 2), v10=round(vw10, 2), irr_base=round(irr_b, 4), irr_weighted=round(irr_w, 4),
        norm_np_2026={s: round(norm_np_2026(s), 2) for s in SCEN}, net_cash_adj=round(nc, 2),
        growth_base=[round(x, 3) for x in res["base"]["growth5"]],
        reinv_rate_base=round(sum(r[5] for r in res["base"]["rows"][:5]) / sum(r[4] for r in res["base"]["rows"][:5]), 3),
        incr_ret_base=round((res["base"]["rows"][4][4] - core_2026("base") * (1 - TAX))
                            / sum(r[5] for r in res["base"]["rows"][:5]), 3),
        tv_share_base=round(res["base"]["tv_share"], 3),
        v_total_shares=round(vw_total, 2), falsifiers=[round(x, 2) for x in (f1, f2, f3, f4, f5)],
        reverse_g10=round(g10, 4), reverse_perp=round(gp, 4),
    )
    print(out)


if __name__ == "__main__":
    main()
