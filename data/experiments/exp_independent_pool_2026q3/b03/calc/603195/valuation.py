# -*- coding: utf-8 -*-
"""公牛集团（603195）独立估值：经营所有者收益 DCF + 经调整净现金。

OI-291 池内独立审计 b03。金额单位亿元，每股价值元/股。输入全部写在脚本内，
出处见 b03/companies/603195_公牛集团.md 第九节「来源」。运行：python3 valuation.py

口径：
- 核心经营利润 = 营业收入 - 营业成本 - 税金及附加 - 销售/管理/研发费用 + 资产与信用减值；
  不含利息收入、理财收益、套保平仓损益、政府补助、营业外收支与资产处置。
- 现金类资产按面值计入（扣受限资金、有息负债、经营备付、理财计损、6/30 后回购与并购付现），
  所以经营 DCF 不再计理财与利息收益，避免重复。
- 2026 年正常化归母净利 = 正常化核心经营利润（税后）+ 经常性其他收益 + 正常化净利息（税后）- 少数股东。
"""
from datetime import date

# ---------------------------------------------------------------- 快照（brief.md）
PRICE = 39.28                      # 2026-10-19 收盘
SHARES = 18.0345                   # 亿股，腾讯行情总股本，含回购专户股份（7/9 注销后 1,803,446,009 股）
TREASURY = 0.062571                # 亿股，2026 回购方案累计 625.71 万股，用途为员工持股/股权激励，不注销（上限口径）
VAL_DATE = date(2026, 10, 19)
T0 = (date(2026, 12, 31) - VAL_DATE).days / 365.0   # 2026 年末距价格日的年数
COE = 0.09

# ---------------------------------------------------------------- 资产负债（2026-06-30，2026H1_report 第 38-40、86、130 页）
CASH_MONETARY = 45.385             # 货币资金（含定期存款 31.773、应收定期存款利息 2.117）
TFA_BANK, TFA_TRUST, TFA_BROKER = 3.130, 10.240, 92.010   # 交易性金融资产：银行理财、信托、资管计划
RESTRICTED = 0.801 + 0.109 + 0.500  # 期货保证金、保函保证金、票据保证金（不属于现金等价物）
DEBT = 6.985 + 2.251 + 0.095 + 0.085 + 0.305   # 短借、长借、一年内到期租赁、租赁负债、衍生金融负债
OP_RESERVE = 10.0                  # 经营备付：约 1 个月付现成本（全年付现成本约 118 亿）
POST_H1_BUYBACK = 0.13             # 7/1~10/19 回购付现：累计 24,698 万 - 6/30 前 23,416 万
ACQUISITION = 3.0                  # 2026-09 收购艾伏新能源付现：未披露（低于信披门槛 16.8 亿），按 3 亿估计

# ---------------------------------------------------------------- 经营基数
REV_2025 = 160.263
REV_H1_2026 = 83.938
REV_H2_2025 = 78.591               # 2025Q3 40.298 + Q4 38.293
CORE_H1_2026 = 22.35               # 2026H1 核心经营利润（26.6%）
CORE_2025 = 41.99                  # 2025 核心经营利润（26.2%）
CORE_TTM, REV_TTM = 43.01, 162.53  # 2025Q3~2026Q2
VAT_CREDIT = 0.30                  # 增值税加计抵减等经常性其他收益（先进制造业加计抵减政策至 2027 年末）
TAX = 0.168                        # 核心经营所得有效税率（2025 年 16.9%，2026H1 17.0%）
FIN_TAX = 0.20                     # 理财与利息收入混合税率
GROSS_CASH_AVG = 145.0             # 年内平均现金类资产（分红前后在 140~175 之间）
INT_EXP = 0.15                     # 有息负债年利息
MINORITY = 0.08                    # 少数股东损益（2025 年 0.06，2026H1 0.04）
NP_TTM, NP_2025, DEDUCT_2025 = 41.62, 40.71, 36.25
EQUITY_PARENT = 151.93
DPS_2025 = 1.90

YEARS = [2027, 2028, 2029, 2030, 2031]

SCEN = {
    "bear": dict(p=0.25, h2_growth=0.00, h2_margin=0.233, m2027=0.235, margin=0.235,
                 growth=[-0.01, 0.00, 0.01, 0.01, 0.01], g_term=0.010, ronic=0.30,
                 wm_haircut=0.03, fin_yield=0.020,
                 text="竣工继续两位数下滑、转换器被低价品牌侵蚀、铜价高位而提价受限：核心经营利润率 23.5%（2021-2022 铜价冲击期水平），营收 2027-2031 年 -1%~+1%，终值增长 1%，增量回报 30%，信托与资管计划按 3% 计损"),
    "base": dict(p=0.50, h2_growth=0.03, h2_margin=0.246, m2027=0.253, margin=0.258,
                 growth=[0.03, 0.035, 0.035, 0.03, 0.03], g_term=0.020, ronic=0.50,
                 wm_haircut=0.01, fin_yield=0.027,
                 text="传统品类份额稳中有升、地产拖累持续但被存量翻新部分抵消、新业务小幅贡献；2026 下半年铜价压毛利，2027 年起逐步提价修复：核心经营利润率 2026H2 24.6%、2027 年 25.3%、其后 25.8%（2019-2025 年均值 25.3%，TTM 26.5%），营收 3%~3.5%，终值增长 2%，增量回报 50%，理财按 1% 计损"),
    "bull": dict(p=0.25, h2_growth=0.05, h2_margin=0.256, m2027=0.263, margin=0.268,
                 growth=[0.06, 0.07, 0.07, 0.06, 0.05], g_term=0.025, ronic=0.60,
                 wm_haircut=0.00, fin_yield=0.032,
                 text="海外（外销 +20%）、数据中心配电、重卡超充与欧洲家储放量，提价与结构升级抵消铜价：核心经营利润率 2027 年 26.3%、其后 26.8%，营收 5%~7%，终值增长 2.5%，增量回报 60%"),
}


def net_cash(s, extra=0.0):
    cash_like = CASH_MONETARY + TFA_BANK + TFA_TRUST + TFA_BROKER
    haircut = s["wm_haircut"] * (TFA_TRUST + TFA_BROKER)
    return cash_like - RESTRICTED - DEBT - OP_RESERVE - POST_H1_BUYBACK - ACQUISITION - haircut - extra


def path(s):
    """返回 ([(期间, t, 营收, NOPAT, 再投资率, 所有者收益)], 2026E 营收)，第一行为 2026H2。"""
    rows = []
    rev_h2 = REV_H2_2025 * (1 + s["h2_growth"])
    rev_2026 = REV_H1_2026 + rev_h2
    g_2026 = rev_2026 / REV_2025 - 1
    nopat_h2 = (rev_h2 * s["h2_margin"] + VAT_CREDIT / 2) * (1 - TAX)
    rr = max(g_2026, 0.0) / s["ronic"]
    rows.append(("2026H2", T0, rev_h2, nopat_h2, rr, nopat_h2 * (1 - rr)))
    rev = rev_2026
    for i, y in enumerate(YEARS):
        g = s["growth"][i]
        rev *= 1 + g
        m = s["m2027"] if y == 2027 else s["margin"]
        vat = VAT_CREDIT if y <= 2027 else 0.0
        nopat = (rev * m + vat) * (1 - TAX)
        rr = max(g, 0.0) / s["ronic"]
        rows.append((y, T0 + (y - 2026), rev, nopat, rr, nopat * (1 - rr)))
    return rows, rev_2026


def value(s, coe=COE, shares=SHARES, extra_cash_cut=0.0):
    rows, _ = path(s)
    pv = sum(oe / (1 + coe) ** t for (_, t, _, _, _, oe) in rows)
    t_last, nopat_last = rows[-1][1], rows[-1][3]
    g = s["g_term"]
    oe_term = nopat_last * (1 + g) * (1 - g / s["ronic"])
    tv = oe_term / (coe - g)
    pv_tv = tv / (1 + coe) ** t_last
    nc = net_cash(s, extra_cash_cut)
    eq = pv + pv_tv + nc
    return dict(v=eq / shares, eq=eq, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / eq, nc=nc)


def normalized_np_2026(s):
    _, rev_2026 = path(s)
    core = (rev_2026 * s["margin"] + VAT_CREDIT) * (1 - TAX)
    fin = (GROSS_CASH_AVG * s["fin_yield"] - INT_EXP) * (1 - FIN_TAX)
    return core + fin - MINORITY


def weighted(coe=COE, shares=SHARES, probs=None, scen=None):
    scen = scen or SCEN
    probs = probs or {k: scen[k]["p"] for k in scen}
    return sum(probs[k] * value(scen[k], coe, shares)["v"] for k in scen)


def irr_base(price=PRICE):
    lo, hi = 0.03, 0.30
    for _ in range(200):
        mid = (lo + hi) / 2
        if value(SCEN["base"], mid)["v"] > price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(price=PRICE):
    """现价隐含增长：基准利润率 25.8%、增量回报 50%，2026H2 按基准。"""
    s = SCEN["base"]
    target = price * SHARES - net_cash(s)
    rows, rev_2026 = path(s)
    pv_h2 = rows[0][5] / (1 + COE) ** rows[0][1]
    nopat_2026 = rev_2026 * s["margin"] * (1 - TAX)
    # (a) 2027 年起永续增长
    lo, hi = -0.05, 0.085
    for _ in range(200):
        g = (lo + hi) / 2
        oe_2027 = nopat_2026 * (1 + g) * (1 - max(g, 0) / s["ronic"])
        val = pv_h2 + oe_2027 / (COE - g) / (1 + COE) ** T0
        hi, lo = (g, lo) if val > target else (hi, g)
    g_perp = (lo + hi) / 2
    # (b) 10 年所有者收益增速，其后 2% 永续
    lo, hi = -0.10, 0.25
    for _ in range(200):
        g10 = (lo + hi) / 2
        pv, nopat, t = pv_h2, nopat_2026, T0
        for _y in range(10):
            nopat *= 1 + g10
            t += 1
            pv += nopat * (1 - max(g10, 0) / s["ronic"]) / (1 + COE) ** t
        tv = nopat * 1.02 * (1 - 0.02 / s["ronic"]) / (COE - 0.02) / (1 + COE) ** t
        hi, lo = (g10, lo) if pv + tv > target else (hi, g10)
    return g_perp, (lo + hi) / 2


def falsifiers():
    """证伪条件触发后的独立 V（元/股）。"""
    b = SCEN["base"]
    out = []
    # F1 定价权失守：利润率较基准低 1.5 个百分点
    s = dict(b, h2_margin=b["h2_margin"] - 0.015, m2027=b["m2027"] - 0.015, margin=b["margin"] - 0.015)
    out.append(("F1 2026 扣非归母 < 34.5 亿或 2026Q4 毛利率 < 42%", "2027-04-30", value(s)["v"]))
    # F2 收入失速：增长路径降为 0~1.5%，终值 1.5%
    s = dict(b, growth=[0.0, 0.01, 0.015, 0.015, 0.015], g_term=0.015)
    out.append(("F2 2027H1 营收同比 < 0%", "2027-08-31", value(s)["v"]))
    # F3 三季报量价双弱：情景概率改为 0.50/0.40/0.10
    out.append(("F3 2026Q3 毛利率 < 38.5% 且营收同比 < 0%", "2026-10-30",
                weighted(probs={"bear": 0.50, "base": 0.40, "bull": 0.10})))
    # F4 资本配置恶化：净现金少计 20 亿、增量回报降至 30%
    s = dict(b, ronic=0.30)
    out.append(("F4 2026 年度分红+回购 < 归母净利 70% 或单笔新业务并购 > 20 亿元", "2027-04-30",
                value(s, extra_cash_cut=20.0)["v"]))
    # F5 理财信用事件：信托与资管计划按 10% 计损
    s = dict(b, wm_haircut=0.10)
    out.append(("F5 2026 年报理财逾期或减值 >= 2 亿元", "2027-04-30", value(s)["v"]))
    return out


def upside_case():
    """反向：三季报显示提价落地（毛利率 >= 41%、营收 >= +4%）时，基准利润率 +1 个百分点、增长 +0.5 个百分点。"""
    b = SCEN["base"]
    s = dict(b, h2_margin=b["h2_margin"] + 0.01, m2027=b["m2027"] + 0.01, margin=b["margin"] + 0.01,
             growth=[g + 0.005 for g in b["growth"]])
    sc = dict(SCEN)
    sc["base"] = s
    return value(s)["v"], weighted(scen=sc)


def cross_checks():
    mcap = PRICE * SHARES
    nc = net_cash(SCEN["base"])
    fin_ttm_after_tax = (4.27 + 0.94 - 0.14) * (1 - FIN_TAX)   # TTM 理财 4.27 + 利息 0.94 - 利息支出
    ex_cash_np = NP_TTM - fin_ttm_after_tax
    return {
        "市值": mcap,
        "股息率(2025 年每股 1.90)": DPS_2025 / PRICE,
        "回购收益率(2026 方案已付 2.47 亿)": 2.4698 / mcap,
        "PE(TTM 归母)": mcap / NP_TTM,
        "剔除净现金 PE(TTM 剔除税后理财利息)": (mcap - nc) / ex_cash_np,
        "EV/核心 EBIT(TTM)": (mcap - nc) / CORE_TTM,
        "PB": mcap / EQUITY_PARENT,
        "长江证券 2026E 42.3 亿对应 PE": mcap / 42.3,
    }


def oe_full_2026(s):
    """2026 全年所有者收益：上半年按实际核心经营利润，下半年按情景。"""
    rows, rev_2026 = path(s)
    g_2026 = rev_2026 / REV_2025 - 1
    rr = max(g_2026, 0.0) / s["ronic"]
    oe_h1 = (CORE_H1_2026 + VAT_CREDIT / 2) * (1 - TAX) * (1 - rr)
    return oe_h1 + rows[0][5]


def oe_growth(s):
    rows, _ = path(s)
    prev = oe_full_2026(s)
    out = []
    for r in rows[1:]:
        out.append(r[5] / prev - 1)
        prev = r[5]
    return out


def reported_2026(s):
    """2026E 报表口径：扣非归母（含存款利息与增值税加计抵减）与归母（再加理财、补助等非经常性）。"""
    rev_h2 = REV_H2_2025 * (1 + s["h2_growth"])
    deduct_h2 = (rev_h2 * s["h2_margin"] + VAT_CREDIT / 2 + 0.42 - 0.07) * (1 - TAX)
    nonrec_h2 = (2.2 + 0.8 - 0.3) * (1 - FIN_TAX)       # 理财约 2.2、补助约 0.8、营业外与处置约 -0.3
    return 19.00 + deduct_h2, 21.51 + deduct_h2 + nonrec_h2


def q3_estimate():
    """2026Q3 基准估计：营收 +2.5%，毛利率约 39.3%（铜价同比约 +35%，无提价），管理费率继续下降。"""
    rev = 40.298 * 1.025
    core = rev * 0.232
    deduct = (core + 0.20 - 0.03) * (1 - TAX)          # 扣非含存款利息
    parent = deduct + 0.90 * (1 - FIN_TAX) + 0.20 * (1 - TAX) - 0.05
    return rev, core, deduct, parent


def main():
    print("公牛集团 603195 独立估值（价格日 2026-10-19，现价 %.2f 元，总股本 %.4f 亿股）" % (PRICE, SHARES))
    print("T0（2026 年末距价格日）= %.3f 年；股权成本 %.0f%%" % (T0, COE * 100))
    res = {}
    for k, s in SCEN.items():
        rows, rev_2026 = path(s)
        r = value(s)
        res[k] = r
        print("\n[%s] p=%.2f  2026E 营收 %.2f；%s" % (k, s["p"], rev_2026, s["text"]))
        print("  期间    t     营收    NOPAT  再投资率  所有者收益  增速")
        prev = None
        for (y, t, rev, nopat, rr, oe) in rows:
            gr = "" if prev is None else "%5.1f%%" % ((oe / prev - 1) * 100) if y != 2027 else ""
            print("  %-6s %5.2f %8.2f %8.2f %7.1f%% %9.2f %s" % (y, t, rev, nopat, rr * 100, oe, gr))
            prev = oe
        print("  经调整净现金 %.2f；显性期现值 %.2f；终值现值 %.2f（占股权价值 %.0f%%）"
              % (r["nc"], r["pv_explicit"], r["pv_tv"], r["tv_share"] * 100))
        print("  股权价值 %.1f 亿元；V = %.2f 元/股；P/V = %.2f" % (r["eq"], r["v"], PRICE / r["v"]))
        print("  2026 正常化归母净利 %.2f 亿元" % normalized_np_2026(s))
    vw = weighted()
    print("\n概率加权 V = %.2f 元/股；P/V = %.3f" % (vw, PRICE / vw))
    vw_ex = weighted(shares=SHARES - TREASURY)
    print("剔除回购专户（%.4f 亿股）后 V = %.2f；P/V = %.3f" % (TREASURY, vw_ex, PRICE / vw_ex))
    print("股权成本 8%%：加权 V = %.2f；10%%：加权 V = %.2f" % (weighted(0.08), weighted(0.10)))
    for k in SCEN:
        print("  %s：8%% V=%.2f  10%% V=%.2f" % (k, value(SCEN[k], 0.08)["v"], value(SCEN[k], 0.10)["v"]))
    print("现价隐含回报（基准情景现金流）= %.2f%%" % (irr_base() * 100))
    gp, g10 = reverse_dcf()
    print("反向 DCF：2027 年起永续增长 %.2f%%；或 10 年所有者收益增速 %.2f%%（其后 2%%）" % (gp * 100, g10 * 100))
    for lim, name in [(0.75, "明显低估（P/V<=0.75）"), (0.90, "温和低估（P/V<=0.90）"), (1.10, "大致合理上限（P/V<=1.10）")]:
        print("  V 不变时 %s 价格 = %.2f" % (name, vw * lim))
    print("\n证伪条件触发后的独立 V：")
    for cond, dl, v in falsifiers():
        print("  %s（%s）→ V = %.2f" % (cond, dl, v))
    vb, vw_up = upside_case()
    print("  反向：2026Q3 毛利率 >= 41%% 且营收 >= +4%% → 基准 V = %.2f，加权 V = %.2f，P/V = %.3f" % (vb, vw_up, PRICE / vw_up))
    print("\n交叉验证：")
    for k, v in cross_checks().items():
        print("  %s = %s" % (k, ("%.2f%%" % (v * 100)) if v < 1 else ("%.1f" % v)))
    for k in SCEN:
        d, n = reported_2026(SCEN[k])
        print("2026E 报表口径（%s）：扣非归母 %.2f（2025 年 36.25）、归母 %.2f（2025 年 40.71）；全年所有者收益 %.2f；2027-2031 所有者收益增速 %s"
              % (k, d, n, oe_full_2026(SCEN[k]), ", ".join("%.1f%%" % (x * 100) for x in oe_growth(SCEN[k]))))
    rev, core, deduct, parent = q3_estimate()
    print("\n2026Q3 基准估计：营收 %.2f（+2.5%%）、核心经营利润 %.2f、扣非归母 %.2f（2025Q3 8.59）、归母 %.2f（2025Q3 9.19）"
          % (rev, core, deduct, parent))


if __name__ == "__main__":
    main()
