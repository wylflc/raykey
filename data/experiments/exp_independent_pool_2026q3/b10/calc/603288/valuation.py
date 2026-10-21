#!/usr/bin/env python3
"""603288 海天味业 独立估值（OI-291 b10，价格日 2026-10-20）。

运行：python3 valuation.py
金额单位：亿元；股本：亿股；每股价值：元/股。
方法：核心经营所有者收益 DCF（不含现金收益与汇兑）+ 经调整净现金。
时间：估值日 2026-10-20；2026 下半年所有者收益记在 2026-12-31（t=0.2），
2027—2031 年按年中（t=0.70…4.70），终值在 t=4.70 用 Gordon 公式。
全部输入写在本文件内，来源见同目录外的正文
companies/603288_海天味业.md。
"""

PRICE = 34.09                     # A 股收盘，2026-10-20
PRICE_DATE = "2026-10-20"
H_PRICE_HKD = 26.18               # 03288.HK 收盘，2026-10-20（腾讯行情）
HKD_CNY = 0.85294                 # 2026-10-20 汇率（open.er-api.com）

# ---------------------------------------------------------------- 股本
SHARES_A = 55.59820644            # 5,560,600,544 − 779,900（2026-08-06 注销）
SHARES_H = 2.84152800             # 291,224,400 − 7,071,600（9 月回购后注销）
SHARES_TOTAL = SHARES_A + SHARES_H          # 58.43973444，与腾讯行情一致
A_BUYBACK_2026 = 0.22035253       # 2026 A 股回购，截至 9-30（10-09 进展公告）
CANCEL_RATIO = 0.70               # 回购方案：70% 以上用于注销
SHARES = SHARES_TOTAL - A_BUYBACK_2026 * CANCEL_RATIO        # 主口径
REPO_ACCOUNT = 0.05289491 + A_BUYBACK_2026  # 回购专户（旧回购余股 + 2026 回购）
SHARES_EX_REPO = SHARES_TOTAL - REPO_ACCOUNT                  # 对照口径

# ---------------------------------------------------------------- 经调整净现金（2026-06-30 + 期后事项）
CASH_ITEMS = {
    "货币资金（含大额存单与应计利息）": 189.3907,
    "交易性金融资产（债务工具）": 108.1434,
    "衍生金融资产": 0.2251,
    "其他非流动资产：定期存款及大额存单": 62.4260,
}
DEDUCTIONS = {
    "受限资金": 0.1385,
    "短期借款": 3.2935,
    "一年内到期的非流动负债": 0.5816,
    "租赁负债": 0.5142,
    "其他非流动负债": 0.0600,
    "衍生金融负债": 0.0209,
    "应付票据（票据贴现融资，列筹资活动）": 20.9166,
    "经营备付（约 5% 营收）": 15.0,
    "期后：A 股回购至 9-30": 7.5469,
    "期后：H 股回购 9 月（约 1.97 亿港元）": 1.70,
    "期后：收购淘大（对价未披露，按 2 亿美元 × 6.69 估）": 13.4,
}
NET_CASH_ADJ = sum(CASH_ITEMS.values()) - sum(DEDUCTIONS.values())
NON_OPERATING = 0.0

# ---------------------------------------------------------------- 经营假设
REV_H1_2026 = 161.4627            # 2026 中报营收
REV_H2_2025 = 136.4193            # 2025Q3 63.99 + Q4 72.43
TAX = 0.160                       # 经营所得税率：2024 15.4%、2025 剔除研发加计扣除调整 16.5%、2026H1 15.4%（含现金收益的综合税率）
MINORITY = 0.05                   # 少数股东损益
TAODA_NOPAT_FULL = 0.67           # 淘大：假设营收 10 亿、EBIT 率 8%
TAODA_NOPAT_2026 = 0.20           # 2026-09-10 起并表
H2_SHARE = 0.45                   # 核心利润下半年占比（2025：45.4%）
FIN_INCOME_2026_PRETAX = 13.0     # 2026E 利息+理财收益−利息支出（H1 实际 7.05）
FIN_TAX = 0.20

SCEN = {
    "bear": dict(p=0.25, h2_growth=0.02, margin=0.250,
                 growth=[0.020, 0.020, 0.020, 0.020, 0.020], rr=0.12,
                 g_term=0.020, rr_term=0.10),
    "base": dict(p=0.50, h2_growth=0.04, margin=0.270,
                 growth=[0.045, 0.045, 0.040, 0.040, 0.035], rr=0.15,
                 g_term=0.025, rr_term=0.10),
    "bull": dict(p=0.25, h2_growth=0.05, margin=0.285,
                 growth=[0.080, 0.075, 0.070, 0.060, 0.050], rr=0.20,
                 g_term=0.025, rr_term=0.08),
}
YEARS = [2027, 2028, 2029, 2030, 2031]
T_H2 = 0.20
T_YEARS = [0.70, 1.70, 2.70, 3.70, 4.70]


def nopat_2026(s, margin=None, tax=TAX):
    m = s["margin"] if margin is None else margin
    rev = REV_H1_2026 + REV_H2_2025 * (1 + s["h2_growth"])
    organic = rev * m * (1 - tax) - MINORITY
    return rev, organic


def flows(s, margin=None, tax=TAX, growth=None):
    """返回 [(t, 所有者收益)] 与终值所需的 2031 年 NOPAT。"""
    g_path = s["growth"] if growth is None else growth
    _, organic = nopat_2026(s, margin, tax)
    out = [(T_H2, (organic * H2_SHARE + TAODA_NOPAT_2026) * (1 - s["rr"]))]
    nop = organic + TAODA_NOPAT_FULL
    for t, g in zip(T_YEARS, g_path):
        nop *= 1 + g
        out.append((t, nop * (1 - s["rr"])))
    return out, nop


def ev(s, r, margin=None, tax=TAX, growth=None):
    fl, nop_last = flows(s, margin, tax, growth)
    pv = sum(cf / (1 + r) ** t for t, cf in fl)
    oe_next = nop_last * (1 + s["g_term"]) * (1 - s["rr_term"])
    tv = oe_next / (r - s["g_term"])
    pv_tv = tv / (1 + r) ** T_YEARS[-1]
    return pv + pv_tv, pv_tv


def value_per_share(s, r, shares=None, margin=None, tax=TAX, growth=None,
                    net_cash=None):
    sh = SHARES if shares is None else shares
    nc = NET_CASH_ADJ if net_cash is None else net_cash
    e, _ = ev(s, r, margin, tax, growth)
    return (e + nc + NON_OPERATING) / sh


def weighted(r, **kw):
    return sum(SCEN[k]["p"] * value_per_share(SCEN[k], r, **kw) for k in SCEN)


def solve(f, lo, hi, target, n=200):
    for _ in range(n):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def implied_irr(s):
    return solve(lambda r: value_per_share(s, r), 0.03, 0.20, PRICE)


def reverse_dcf_10y(r=0.09):
    """现价隐含：2027—2036 所有者收益年增速 g（基准 2026 年化 OE 起步），之后 2.5%。"""
    s = SCEN["base"]
    _, organic = nopat_2026(s)
    h2 = (organic * H2_SHARE + TAODA_NOPAT_2026) * (1 - s["rr"])
    base_oe = (organic + TAODA_NOPAT_FULL) * (1 - s["rr"])
    target_ev = PRICE * SHARES - NET_CASH_ADJ - NON_OPERATING

    def ev_g(g):
        pv = h2 / (1 + r) ** T_H2
        oe = base_oe
        t = 0.70
        for _ in range(10):
            oe *= 1 + g
            pv += oe / (1 + r) ** t
            t += 1
        oe_term = oe / (1 - s["rr"]) * 1.025 * (1 - 0.10)
        pv += oe_term / (r - 0.025) / (1 + r) ** (t - 1)
        return pv
    return solve(ev_g, -0.05, 0.30, target_ev)


def reverse_dcf_perpetual(r=0.09):
    """现价隐含永续增速：EV = OE_2027/(r−g)，OE_2027 取基准情景。"""
    s = SCEN["base"]
    fl, _ = flows(s)
    oe_2027 = fl[1][1]
    target_ev = PRICE * SHARES - NET_CASH_ADJ - NON_OPERATING
    return r - oe_2027 / target_ev


def normalized_np_2026(s):
    _, organic = nopat_2026(s)
    return organic + TAODA_NOPAT_2026 + FIN_INCOME_2026_PRETAX * (1 - FIN_TAX)


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    print(f"海天味业 603288  价格日 {PRICE_DATE}  现价 {PRICE:.2f}")
    print(f"股本：行情总股本 {SHARES_TOTAL:.4f}；扣拟注销 {A_BUYBACK_2026*CANCEL_RATIO:.4f}"
          f" → 主口径 {SHARES:.4f}；剔除回购专户 {SHARES_EX_REPO:.4f}")
    print(f"经调整净现金 {NET_CASH_ADJ:.2f}（现金类 {sum(CASH_ITEMS.values()):.2f}"
          f" − 扣减 {sum(DEDUCTIONS.values()):.2f}），每股 {NET_CASH_ADJ/SHARES:.2f}")
    print()
    print("情景   概率  2026营收  核心NOPAT  正常化归母  EV(9%)  终值占EV  V(9%)   V(8%)   V(10%)  IRR")
    res = {}
    for k, s in SCEN.items():
        rev, organic = nopat_2026(s)
        e9, tv9 = ev(s, 0.09)
        v9 = value_per_share(s, 0.09)
        v8 = value_per_share(s, 0.08)
        v10 = value_per_share(s, 0.10)
        irr = implied_irr(s)
        nnp = normalized_np_2026(s)
        res[k] = dict(v9=v9, v8=v8, v10=v10, irr=irr, nnp=nnp)
        print(f"{k:5s} {s['p']:.2f}  {rev:7.1f}  {organic:8.2f}  {nnp:9.2f}  {e9:7.1f}"
              f"  {tv9/e9:6.1%}  {v9:6.2f}  {v8:6.2f}  {v10:6.2f}  {irr:.2%}")
    vw = weighted(0.09)
    vw8 = weighted(0.08)
    vw10 = weighted(0.10)
    vw_ex = weighted(0.09, shares=SHARES_EX_REPO)
    print()
    print(f"加权 V(9%) = {vw:.2f}   P/V = {PRICE/vw:.3f}   分档：{band(PRICE/vw)}")
    print(f"加权 V(8%) = {vw8:.2f}   加权 V(10%) = {vw10:.2f}")
    print(f"剔除回购专户股份：加权 V = {vw_ex:.2f}，P/V = {PRICE/vw_ex:.3f}")
    print(f"基准情景现价隐含回报（IRR）= {res['base']['irr']:.2%}")
    print(f"反向 DCF：10 年所有者收益增速 = {reverse_dcf_10y():.2%}；永续增速 = {reverse_dcf_perpetual():.2%}")
    h_rmb = H_PRICE_HKD * HKD_CNY
    print(f"H 股参考：{H_PRICE_HKD:.2f} 港元 × {HKD_CNY} = {h_rmb:.2f} 元，H 股 P/V = {h_rmb/vw:.3f}；"
          f"A/H 溢价 {PRICE/h_rmb-1:.1%}")
    print(f"分档价格（V 不变）：≤0.75 → ≤{0.75*vw:.2f}；0.90 → {0.90*vw:.2f}；1.10 → {1.10*vw:.2f}")
    print()
    print("证伪触发后的独立 V（9%，其余按三情景加权）：")
    fz = {
        "F1 各情景核心营业利润率统一降至 25.5%":
            sum(SCEN[k]["p"] * value_per_share(SCEN[k], 0.09, margin=0.255) for k in SCEN),
        "F2 增长停滞：各情景 2027—2031 增速改用熊市路径（2%）":
            sum(SCEN[k]["p"] * value_per_share(SCEN[k], 0.09, growth=SCEN["bear"]["growth"]) for k in SCEN),
        "F3 主要子公司失去高新资格：经营税率升至 21%":
            sum(SCEN[k]["p"] * value_per_share(SCEN[k], 0.09, tax=0.21) for k in SCEN),
        "F4 现金回报打折：净现金按 85% 计（大额并购/滞留海外汇兑损失）":
            sum(SCEN[k]["p"] * value_per_share(SCEN[k], 0.09, net_cash=NET_CASH_ADJ * 0.85) for k in SCEN),
        "F5 上行：各情景利润率 28.5% 且增速改用牛市路径":
            sum(SCEN[k]["p"] * value_per_share(SCEN[k], 0.09, margin=0.285, growth=SCEN["bull"]["growth"]) for k in SCEN),
    }
    for name, v in fz.items():
        print(f"  {name}: V = {v:.2f}，P/V = {PRICE/v:.3f}")
    print()
    print("基准情景逐年（核心 NOPAT 增速与所有者收益）：")
    fl, _ = flows(SCEN["base"])
    print(f"  2026H2 OE {fl[0][1]:.2f}")
    for y, (t, cf), g in zip(YEARS, fl[1:], SCEN["base"]["growth"]):
        print(f"  {y} 增速 {g:.1%}  OE {cf:.2f}")
    print()
    print("交叉验证：")
    mcap = PRICE * SHARES_TOTAL
    eq = PRICE * SHARES
    ev_mkt = eq - NET_CASH_ADJ - NON_OPERATING
    core_ebit_ttm = 83.61              # 2025 核心 EBIT 79.73 + 2026H1 47.43 − 2025H1 43.55
    rev_b, org_b = nopat_2026(SCEN["base"])
    core_ebit_norm = rev_b * SCEN["base"]["margin"]
    print(f"  市值（A 股价 × 全部股份）{mcap:.1f}；主口径股权 {eq:.1f}；EV {ev_mkt:.1f}")
    print(f"  EV/核心 EBIT：TTM {ev_mkt/core_ebit_ttm:.1f}×；2026 正常化（基准）{ev_mkt/core_ebit_norm:.1f}×")
    print(f"  EV/核心 NOPAT（基准 2026 含淘大全年）{ev_mkt/(org_b+TAODA_NOPAT_FULL):.1f}×；"
          f"市值/TTM 归母 {mcap/73.17:.1f}×；市值/基准正常化归母 {mcap/normalized_np_2026(SCEN['base']):.1f}×")
    div_2025 = 79.4999                 # 2025 年度现金分红合计（含特别分红 17.54）
    print(f"  2025 年度分红收益率 {div_2025/mcap:.2%}（不含特别分红 {(div_2025-17.5396)/mcap:.2%}）；"
          f"按 80% 派息与基准正常化归母 {0.8*normalized_np_2026(SCEN['base'])/mcap:.2%}")
    print()
    print("JSON 摘要：")
    print({k: round(res[k]["v9"], 2) for k in res}, "v_weighted", round(vw, 2), "pv", round(PRICE / vw, 3),
          "v8", round(vw8, 2), "v10", round(vw10, 2), "irr", round(res["base"]["irr"], 4),
          "nnp", {k: round(res[k]["nnp"], 2) for k in res}, "net_cash", round(NET_CASH_ADJ, 2))


if __name__ == "__main__":
    main()
