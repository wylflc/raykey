#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""京东方Ａ（000725）独立估值，OI-291 b18 深度版。

运行：python3 valuation.py
金额单位亿元，股本亿股，每股元。输入全部写在本脚本内，出处见正文「来源」。
口径：所有者收益 DCF（9% 股权成本，归母经济份额），经调整净现金为负，按框架用有杠杆口径：
股权价值 = 归母份额 ×（经营所有者收益现值 − 经调整净负债税后利息现值）+ 归母非经营资产。
"""

# ---------------------------------------------------------------- 快照与股本
PRICE_DATE = "2026-10-21"
PRICE_A = 5.05                       # A 股收盘
PRICE_B_HKD = 4.82                   # B 股收盘（港元）
HKD_CNY = 0.8507
PRICE_B = PRICE_B_HKD * HKD_CNY      # 折人民币
SHARES_TOTAL = 370.4433              # 总股本，含回购专户（2026H1 第 40 页：37,044,328,064 股）
CANCEL_A = 0.943926                  # 注销式回购 A 股，截至 9-30（buyback_20261008_185202 第 2 页）
CANCEL_B = 0.88686743                # 注销式回购 B 股，截至 9-30（同上）
RESERVE_TREASURY = 0.3000008         # 激励回购余股 1,005,011,580 − 975,011,500，留作预留授予，不注销
SHARES = SHARES_TOTAL - CANCEL_A - CANCEL_B          # 每股价值股本（拟注销股份扣除）
SHARES_EX_TREASURY = SHARES - RESERVE_TREASURY       # 对照：再剔除专户余股
COE = 0.09
TAX_INT = 0.25                       # 利息税盾税率

# ---------------------------------------------------------------- 2026-06-30 资产负债（2026H1 第 50～52、93～94、130～141 页）
CASH = 723.02                        # 货币资金
RESTRICTED = 17.53                   # 受限货币资金（第 15 页）
WMP = 9.95                           # 交易性金融资产中的结构性存款及理财（第 94 页）
CD_TERM = 143.24                     # 其他非流动资产中的大额存单及定期存款（第 130 页）
REV_TTM = 2064.44
OP_RESERVE = 0.025 * REV_TTM         # 经营备付：TTM 营收 2.5%
DEBT_IB = 1425.47                    # 短借 46.84 + 长借 936.49 + 债券 129.67 + 一年内到期 305.78 + 租赁 6.70
LT_PAYABLE = 22.49                   # 长期应付款（2025 年报列入金融负债到期分析，保守按类债务）
REDEEMABLE_MI = 20.80                # 附赎回条款的少数股东出资（福州京东方，摊余成本金融负债）
CEC_FUNDING = 33.10                  # 其他应付款—资金往来：南京显示、成都显示科技欠原控股股东款项
DIV_PAYABLE = 0.79
# 6-30 之后的已知现金事项
B9_REDUCTION = 64.5 * 1.023          # 合肥显示技术 7 月定向减资：注册资本 240→175.5 亿；金额未披露，按武汉 2025 年 51.14 亿/50 亿单价推算
BUYBACK_AFTER_H1 = 5.4993066 + (4.1071891 - 3.8198160) * HKD_CNY   # A 股 5.50 亿元 + B 股 0.287 亿港元
INT_RATE = 35.01 / ((1466.34 + 1435.58) / 2)   # 2025 利息支出 ÷ 平均有息负债

cash_like = CASH - RESTRICTED - OP_RESERVE + WMP + CD_TERM
debt_like = DEBT_IB + LT_PAYABLE + REDEEMABLE_MI + CEC_FUNDING + DIV_PAYABLE
NET_CASH_ADJ = cash_like - debt_like - B9_REDUCTION - BUYBACK_AFTER_H1   # 无杠杆口径经调整净现金（负值＝净负债）
NET_DEBT = -NET_CASH_ADJ

# ---------------------------------------------------------------- 非经营资产（合并口径，再乘归母比例）
HKC_BOOK_0630, HKC_COST = 29.1775, 6.0690           # 惠科股份（2026H1 第 17 页）
HKC_PX_0630, HKC_PX_1021 = 38.18, 17.38             # 腾讯日线
OTHER_LISTED_0630, OTHER_LISTED_COST = 47.1430 - 29.1775, 8.96   # 交易性金融资产中其余权益工具
CSI300_0630, CSI300_1021 = 4979.43, 4111.93         # 其余上市股权缺 10 月行情，按沪深 300 同期涨跌代理
OCI_EQUITY = 4.29                                   # 其他权益工具投资（含重庆银行）
OTHER_NC_FIN = 13.98                                # 其他非流动金融资产（未上市股权）
LTEI_TOTAL, VUSION_BOOK, TJXZL_BOOK = 195.53, 42.03, 24.54   # 长期股权投资合计、VusionGroup、天津显智链（第 115 页）
VUSION_MKT = 50.0                                   # 约 25% × 2026-06 市值约 28 亿美元，未核到 10 月价格
NONOP_PARENT = 0.95                                 # 非经营资产归母比例

hkc_mkt = HKC_BOOK_0630 * HKC_PX_1021 / HKC_PX_0630
other_listed_mkt = OTHER_LISTED_0630 * CSI300_1021 / CSI300_0630
listed_tax = 0.25 * max(0.0, hkc_mkt - HKC_COST) + 0.25 * max(0.0, other_listed_mkt - OTHER_LISTED_COST)
LTEI_OTHER = LTEI_TOTAL - VUSION_BOOK - TJXZL_BOOK


def nonop(s):
    ltei = s["vusion"] + TJXZL_BOOK * s["tj_mult"] + LTEI_OTHER * s["ltei_mult"]
    total = hkc_mkt + other_listed_mkt - listed_tax + OCI_EQUITY + OTHER_NC_FIN + ltei
    return total, total * NONOP_PARENT


# ---------------------------------------------------------------- 2026 上半年实际（2026H1 第 55～58、123、146～147 页）
REV_2025 = 2045.90
REV_H1 = 1031.32
CAPEX_H1 = 145.66
DA_H1 = 179.94                        # 固定资产折旧 171.13 + 使用权 0.95 + 无形 7.05 + 长期待摊 0.81
# EBITDA（扣非经常性补助）= 营业利润 − 投资收益 − 公允价值变动 + 财务费用 + 折旧摊销 − 计入非经常性损益的政府补助
EBITDA_H1 = 72.63 - 17.31 - 23.10 + 16.95 + DA_H1 - 8.01
EBITDA_H2_2025 = (67.83 - 41.00) - (6.54 - 4.37) - (4.32 - 0.70) + (18.37 - 7.13) + (386.69 - 194.25) - (11.57 - 6.97)
EBITDA_TTM = EBITDA_H1 + EBITDA_H2_2025
DA_TTM = DA_H1 + (386.69 - 194.25)
MI_BOOK_POST = 745.72 - B9_REDUCTION  # 少数股东权益账面（6-30）扣合肥减资
T0 = 71 / 365.0                       # 2026-10-21 → 2026-12-31

# ---------------------------------------------------------------- 三情景
# m：EBITDA 率口径＝营业利润 − 投资收益 − 公允价值变动 + 财务费用 + 折旧摊销 − 非经常性政府补助（含存货跌价与股份支付）
# grants：每年计入的准经常性政府补助（税前）；share：归母经济份额（经营现金流与净负债同比例）
SCEN = {
    "bear": dict(p=0.25, rev_h2=1005.0, g_rev=0.00, m_h2=0.195, m=0.185, grants=0.0,
                 da=[362, 350, 336, 322, 308, 295], capex=[295, 290, 285, 280, 280, 280],
                 tax=0.27, gT=0.010, ronic=0.08, share=0.66,
                 vusion=VUSION_BOOK, tj_mult=0.5, ltei_mult=0.60,
                 np26=dict(m=0.185, net_int=16.5, tax=0.30, tax_floor=8.0, mi=-20.0, assoc=1.0)),
    "base": dict(p=0.50, rev_h2=1040.0, g_rev=0.02, m_h2=0.205, m=0.210, grants=5.5,
                 da=[360, 342, 320, 298, 278, 262], capex=[292, 262, 248, 242, 240, 245],
                 tax=0.25, gT=0.015, ronic=0.10, share=0.72,
                 vusion=VUSION_MKT, tj_mult=0.7, ltei_mult=0.75,
                 np26=dict(m=0.210, net_int=16.0, tax=0.28, tax_floor=8.0, mi=-10.0, assoc=2.0)),
    "bull": dict(p=0.25, rev_h2=1065.0, g_rev=0.03, m_h2=0.215, m=0.235, grants=11.0,
                 da=[358, 338, 312, 288, 268, 250], capex=[288, 238, 222, 215, 215, 220],
                 tax=0.23, gT=0.025, ronic=0.12, share=0.80,
                 vusion=55.0, tj_mult=0.85, ltei_mult=0.90,
                 np26=dict(m=0.235, net_int=15.5, tax=0.25, tax_floor=8.0, mi=8.0, assoc=3.0)),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def flows(s):
    """合并口径经营所有者收益（未扣利息）：2026 下半年 + 2027～2031 + 2032 终值年。"""
    rev26 = REV_H1 + s["rev_h2"]
    e_h2 = s["rev_h2"] * s["m_h2"] + s["grants"] / 2
    ebit_h2 = e_h2 - (s["da"][0] - DA_H1)
    oe_h2 = e_h2 - max(0.0, ebit_h2) * s["tax"] - (s["capex"][0] - CAPEX_H1)
    rows, rev_prev = [], rev26
    for i, y in enumerate(YEARS, start=1):
        rev = rev26 * (1 + s["g_rev"]) ** i
        e = rev * s["m"] + s["grants"]
        ebit = e - s["da"][i]
        tax = max(0.0, ebit) * s["tax"]
        dwc = 0.10 * (rev - rev_prev)
        oe = e - tax - s["capex"][i] - dwc
        rows.append(dict(year=y, rev=rev, ebitda=e, da=s["da"][i], ebit=ebit, tax=tax,
                         capex=s["capex"][i], dwc=dwc, oe=oe))
        rev_prev = rev
    rev_t = rev_prev * (1 + s["gT"])
    e_t = rev_t * s["m"] + s["grants"]
    maint = s["capex"][-1] * (1 + s["gT"])
    nopat_t = (e_t - maint) * (1 - s["tax"])
    oe_t = nopat_t * (1 - s["gT"] / s["ronic"])
    return dict(rev26=rev26, oe_h2=oe_h2, rows=rows, rev_t=rev_t, ebitda_t=e_t, maint_t=maint,
                nopat_t=nopat_t, oe_t=oe_t)


def value(s, r=COE):
    f = flows(s)
    pv_h2 = f["oe_h2"] / (1 + r) ** T0
    pv_exp = sum(row["oe"] / (1 + r) ** (T0 + i) for i, row in enumerate(f["rows"], start=1))
    tv = f["oe_t"] / (r - s["gT"])
    pv_tv = tv / (1 + r) ** (T0 + len(YEARS))
    op_pv = pv_h2 + pv_exp + pv_tv
    int_at = NET_DEBT * INT_RATE * (1 - TAX_INT)       # 合并口径净负债税后利息（按现规模滚动）
    pv_int = int_at / r
    _, nonop_p = nonop(s)
    eq_lev = s["share"] * (op_pv - pv_int) + nonop_p
    eq_unlev = s["share"] * (op_pv - NET_DEBT) + nonop_p
    return dict(f=f, pv_h2=pv_h2, pv_exp=pv_exp, pv_tv=pv_tv, op_pv=op_pv, tv_share=pv_tv / op_pv,
                pv_int=pv_int, int_at=int_at, nonop_p=nonop_p, eq_lev=eq_lev, eq_unlev=eq_unlev,
                v=eq_lev / SHARES, v_unlev=eq_unlev / SHARES, v_ex_treasury=eq_lev / SHARES_EX_TREASURY)


def weighted(r=COE, key="v"):
    return sum(SCEN[k]["p"] * value(SCEN[k], r)[key] for k in SCEN)


def solve(fn, lo, hi, target, n=200):
    flo = fn(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = fn(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def normalized_np_2026(s):
    """2026 年正常化归母净利（报表口径：含净利息，剔除公允价值、基金重估、汇兑、非经常性补助）。"""
    n = s["np26"]
    rev26 = REV_H1 + s["rev_h2"]
    ebt = rev26 * n["m"] - s["da"][0] - n["net_int"]
    tax = max(n["tax"] * ebt, n["tax_floor"])           # 亏损子公司不能抵税，盈利子公司照常纳税
    np_cons = ebt - tax
    return np_cons - n["mi"] + n["assoc"]               # 减少数股东损益（负值即少数股东分担亏损），加联营企业常态收益


def implied_irr():
    target = PRICE_A * SHARES
    return solve(lambda r: value(SCEN["base"], r)["eq_lev"], 0.04, 0.20, target)


def reverse_growth():
    """现价隐含：以基准 2027 年归母经营所有者收益为起点，10 年匀速增长后按 1.5% 永续。"""
    s = SCEN["base"]
    v0 = value(s)
    oe27 = v0["f"]["rows"][0]["oe"]
    target = PRICE_A * SHARES - v0["nonop_p"] + s["share"] * v0["pv_int"]

    def eq(x):
        pv, oe = 0.0, oe27
        for i in range(1, 11):
            if i > 1:
                oe *= 1 + x
            pv += s["share"] * oe / (1 + COE) ** (T0 + i)
        tv = s["share"] * oe * 1.015 / (COE - 0.015)
        return pv + tv / (1 + COE) ** (T0 + 10)
    return solve(eq, -0.10, 0.20, target)


def reverse_margin():
    s = dict(SCEN["base"])
    target = PRICE_A * SHARES

    def eq(m):
        t = dict(s, m=m, m_h2=m)
        return value(t)["eq_lev"]
    return solve(eq, 0.15, 0.35, target)


def falsifier_v(overrides, probs=None):
    """overrides：{情景: {参数: 新值}}；probs：(熊, 基准, 牛) 新概率，None 表示不变。"""
    tot = 0.0
    for k, s in SCEN.items():
        t = dict(s, **overrides.get(k, {}))
        p = s["p"] if probs is None else dict(zip(("bear", "base", "bull"), probs))[k]
        tot += p * value(t)["v"]
    return tot


B_CAPEX = SCEN["base"]["capex"]
U_CAPEX = SCEN["bull"]["capex"]
FALSIFIERS = [
    ("F1 2027 年 EBITDA 率（本文口径）< 19.5%：基准率降到 19.5%、牛市降到 22%",
     {"base": dict(m=0.195, m_h2=0.195), "bull": dict(m=0.22)}, None),
    ("F2 2027 年资本开支 > 300 亿：基准 2027～2031 每年 +40 亿、牛市 +25 亿",
     {"base": dict(capex=B_CAPEX[:1] + [c + 40 for c in B_CAPEX[1:]]),
      "bull": dict(capex=U_CAPEX[:1] + [c + 25 for c in U_CAPEX[1:]])}, None),
    ("F3 少数股东分走更多现金流：归母份额熊 0.60／基准 0.62／牛 0.72",
     {"bear": dict(share=0.60), "base": dict(share=0.62), "bull": dict(share=0.72)}, None),
    ("F4 65 吋 TV 面板连续 3 个月 ≤ 160 美元：概率改为 50/40/10", {}, (0.5, 0.4, 0.1)),
    ("F5（向上）2027 年资本开支 ≤ 220 亿且 EBITDA 率 ≥ 23%：概率改为 10/40/50", {}, (0.1, 0.4, 0.5)),
]


def fmt(x, d=2):
    return f"{x:,.{d}f}"


def main():
    print(f"京东方Ａ 000725  价格日 {PRICE_DATE}  A 股 {PRICE_A}  B 股 {PRICE_B_HKD} 港元 = {PRICE_B:.2f} 元")
    print(f"股本：总股本 {SHARES_TOTAL} − 注销式回购 A {CANCEL_A:.4f} − B {CANCEL_B:.4f} = {SHARES:.4f} 亿股；"
          f"再剔除专户余股 {RESERVE_TREASURY:.4f} = {SHARES_EX_TREASURY:.4f}")
    print(f"市值（A 股价 × 每股价值股本）{fmt(PRICE_A * SHARES, 1)} 亿")
    print()
    print("经调整净现金（无杠杆口径）")
    print(f"  现金类 {fmt(cash_like, 1)} = 货币资金 {CASH} − 受限 {RESTRICTED} − 经营备付 {OP_RESERVE:.1f} + 理财 {WMP} + 大额存单 {CD_TERM}")
    print(f"  有息及类债务 {fmt(debt_like, 1)} = 有息负债 {DEBT_IB} + 长期应付 {LT_PAYABLE} + 可赎回少数股东出资 {REDEEMABLE_MI}"
          f" + 资金往来 {CEC_FUNDING} + 应付股利 {DIV_PAYABLE}")
    print(f"  6-30 后：合肥 10.5 代线减资 −{B9_REDUCTION:.1f}，回购 −{BUYBACK_AFTER_H1:.2f}")
    print(f"  net_cash_adj = {fmt(NET_CASH_ADJ, 1)}；有息负债平均利率 {INT_RATE:.3%}；合并口径税后利息 {NET_DEBT * INT_RATE * (1 - TAX_INT):.2f}/年")
    print(f"  惠科股份按 10-21 价 {hkc_mkt:.2f}（6-30 账面 {HKC_BOOK_0630}），其余上市股权 {other_listed_mkt:.2f}，未实现收益税 {listed_tax:.2f}")
    print()
    res = {k: value(SCEN[k]) for k in SCEN}
    for k, s in SCEN.items():
        v = res[k]
        f = v["f"]
        nt, npar = nonop(s)
        print(f"[{k}] 概率 {s['p']:.0%}  归母份额 {s['share']:.2f}  EBITDA 率 {s['m']:.1%}  营收增速 {s['g_rev']:.0%}"
              f"  终值 g {s['gT']:.1%} / RONIC {s['ronic']:.0%}")
        print(f"  2026 营收 {f['rev26']:.0f}，下半年合并所有者收益 {f['oe_h2']:.1f}")
        for row in f["rows"]:
            print(f"  {row['year']}: 营收 {row['rev']:.0f} EBITDA {row['ebitda']:.1f} 折旧 {row['da']} 税 {row['tax']:.1f}"
                  f" 资本开支 {row['capex']} 营运资本 {row['dwc']:.1f} → 合并 {row['oe']:.1f}，归母 {s['share'] * row['oe']:.1f}"
                  f"，扣利息后 {s['share'] * (row['oe'] - v['int_at']):.1f}")
        print(f"  终值年：EBITDA {f['ebitda_t']:.1f} 维持性开支 {f['maint_t']:.1f} NOPAT {f['nopat_t']:.1f}"
              f" 再投资率 {s['gT'] / s['ronic']:.0%} → 所有者收益 {f['oe_t']:.1f}（归母 {s['share'] * f['oe_t']:.1f}）")
        print(f"  现值：下半年 {v['pv_h2']:.1f} + 2027～2031 {v['pv_exp']:.1f} + 终值 {v['pv_tv']:.1f} = {v['op_pv']:.1f}"
              f"（终值占 {v['tv_share']:.0%}）；利息现值 {v['pv_int']:.1f}；非经营资产 {nt:.1f}（归母 {npar:.1f}）")
        print(f"  有杠杆口径 V = {v['v']:.2f}（股权 {v['eq_lev']:.0f}）；无杠杆口径 V = {v['v_unlev']:.2f}；"
              f"剔除专户余股 V = {v['v_ex_treasury']:.2f}")
        print(f"  2026 正常化归母净利 {normalized_np_2026(s):.1f}")
        print()
    vw = weighted()
    vw_u = weighted(key="v_unlev")
    vw_x = weighted(key="v_ex_treasury")
    print(f"加权 V（有杠杆口径）= {vw:.2f}  P/V(A) = {PRICE_A / vw:.2f}  P/V(B) = {PRICE_B / vw:.2f}")
    print(f"加权 V（无杠杆口径）= {vw_u:.2f}  P/V(A) = {PRICE_A / vw_u:.2f}")
    print(f"剔除专户余股：加权 V = {vw_x:.2f}  P/V(A) = {PRICE_A / vw_x:.2f}")
    for r in (0.08, 0.10):
        print(f"股权成本 {r:.0%}：熊 {value(SCEN['bear'], r)['v']:.2f} 基准 {value(SCEN['base'], r)['v']:.2f}"
              f" 牛 {value(SCEN['bull'], r)['v']:.2f} 加权 {weighted(r):.2f}")
    print(f"现价隐含回报（基准情景）= {implied_irr():.2%}")
    print(f"反向 DCF：基准 2027 年归母经营所有者收益之后 10 年隐含年增速 {reverse_growth():.2%}（其后 1.5%）")
    print(f"反向 DCF：其余按基准，现价隐含全周期 EBITDA 率 {reverse_margin():.2%}")
    print("V 不变时各档价格：≤{:.2f} 明显低估；≤{:.2f} 温和低估；≤{:.2f} 大致合理".format(0.75 * vw, 0.90 * vw, 1.10 * vw))
    print()
    print("归母份额敏感性（基准情景其余不变）：")
    for sh in (0.62, 0.66, 0.72, 0.80, 0.85):
        print(f"  share {sh:.2f} → V {value(dict(SCEN['base'], share=sh))['v']:.2f}")
    print("基准 EBITDA 率敏感性：")
    for m in (0.19, 0.20, 0.21, 0.22, 0.23):
        print(f"  {m:.0%} → V {value(dict(SCEN['base'], m=m, m_h2=min(m, 0.205)))['v']:.2f}")

    # ---------------- 基准增长路径（归母所有者收益，扣税后利息）
    print()
    b = SCEN["base"]
    vb = res["base"]
    oe_h1 = EBITDA_H1 - max(0.0, EBITDA_H1 - DA_H1) * b["tax"] - CAPEX_H1
    oe26 = oe_h1 + vb["f"]["oe_h2"]
    path = [b["share"] * (oe26 - vb["int_at"])] + [b["share"] * (row["oe"] - vb["int_at"]) for row in vb["f"]["rows"]]
    print(f"基准 2026 全年合并所有者收益 {oe26:.1f}（上半年实际 {oe_h1:.1f}），归母扣利息 {path[0]:.1f}")
    print("基准增长路径：" + "，".join(f"{y} {path[i + 1]:.1f}（{path[i + 1] / path[i] - 1:+.1%}）" for i, y in enumerate(YEARS))
          + f"；终值 g {b['gT']:.1%}，再投资率 {b['gT'] / b['ronic']:.0%}，增量回报 {b['ronic']:.0%}")

    # ---------------- 交叉验证
    print()
    mc = PRICE_A * SHARES
    ev = mc + NET_DEBT + MI_BOOK_POST - nonop(SCEN["base"])[0]   # 少数股东权益按减资后账面
    ebit_ttm = EBITDA_TTM - DA_TTM
    print(f"TTM EBITDA（扣非经常性补助）= 下半年 2025 {EBITDA_H2_2025:.1f} + 上半年 2026 {EBITDA_H1:.1f} = {EBITDA_TTM:.1f}，"
          f"占营收 {EBITDA_TTM / REV_TTM:.1%}；TTM 折旧摊销 {DA_TTM:.1f}；EBIT {ebit_ttm:.1f}")
    print(f"交叉：EV/EBITDA(TTM, 少数股东按账面) = {ev / EBITDA_TTM:.1f}x；EV/EBIT(TTM) = {ev / ebit_ttm:.0f}x；"
          f"PB = {mc / 1331.36:.2f}x；PE(TTM 归母 78.58) = {mc / 78.58:.1f}x；PE(TTM 扣非 49.56) = {mc / 49.56:.1f}x")
    print(f"交叉：股息率 {0.056 / PRICE_A:.2%}；每年注销式回购不低于 15 亿元 ≈ {15 / mc:.2%}")
    cons_eq = vb["op_pv"] - vb["pv_int"] + nonop(b)[0]
    mi_val = (1 - b["share"]) * (vb["op_pv"] - vb["pv_int"]) + (1 - NONOP_PARENT) * nonop(b)[0]
    print(f"交叉：基准合并股权价值 {cons_eq:.0f}（合并账面约 {1331.36 + MI_BOOK_POST:.0f}）；"
          f"隐含少数股东价值 {mi_val:.0f}，为其账面 {MI_BOOK_POST:.0f} 的 {mi_val / MI_BOOK_POST:.2f} 倍")

    # ---------------- 证伪触发后的 V（按触发事实改写相关情景参数或概率后的加权 V）
    print()
    print("证伪触发后的 V：")
    for name, ov, probs in FALSIFIERS:
        print(f"  {name}：加权 V {falsifier_v(ov, probs):.2f}")


if __name__ == "__main__":
    main()
