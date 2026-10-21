#!/usr/bin/env python3
"""嘉立创（001232）独立估值：所有者收益 DCF 三情景、反向 DCF、隐含回报与证伪情景。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。价格日与估值时点 2026-10-20。
输入全部写在本脚本内，出处见注释（文件名与页码指 raw/001232/txt 下的公告逐页文本）。
"""

# ---------------------------------------------------------------- 市场与股本
PRICE = 161.80          # 2026-10-20 收盘，腾讯日线
SHARES = 5.5556         # 亿股，发行后总股本 555,560,000 股（dividend_20260918_514920 第 1 页）；无回购专户
COE = 0.09
G_TERMINAL = 0.025

# ---------------------------------------------------------------- 经调整净现金（无杠杆口径）
CASH = 7.0884           # 货币资金 708,837,547.68 元（2026H1_report 第 35 页）
WMP = 39.9503           # 交易性金融资产，全部为银行理财（2026H1_report 第 35、80 页）
TIME_DEPOSIT = 0.7568   # 其他流动资产中短期定期存款 0.7443 + 应收利息 0.0125（2026H1_report 第 90 页）
IPO_NET = 44.4817       # 首发募集资金净额 4,448,173,848.40 元，2026-07-30 到位（invest_20261017_621609 第 6 页）
DIVIDEND_PAID = 2.7778  # 2026 中期分红 277,780,000 元，2026-09-28 派发（dividend_20260918_514920 第 1 页）
RESTRICTED = 0.2987     # 受限货币资金 29,874,618.41 元（2026H1_report 第 80 页）
OPERATING_RESERVE = 5.0  # 经营备付：约为正常化 2026 年收入的 3.5%（假设，见正文 2.4 节）
BUYBACK_LEASE = 3.9825  # 长期应付款「招商引资-代建租赁回购」，含一年内到期 0.8698（2026H1_report 第 107-108 页）
TEMP_RECEIPT = 0.0850   # 长期应付款「暂收款」（2026H1_report 第 108 页）
LEASE = 0.5260          # 租赁负债 55,584,183.80 − 未确认融资费用 2,986,081.99 元（2026H1_report 第 107-108 页）
DEBT_LIKE = BUYBACK_LEASE + TEMP_RECEIPT + LEASE
NET_CASH_ADJ = (CASH + WMP + TIME_DEPOSIT + IPO_NET - DIVIDEND_PAID
                - RESTRICTED - OPERATING_RESERVE - DEBT_LIKE)
NON_OPERATING = 1.0335  # 其他权益工具投资：半导体初创企业少数股权（2026H1_report 第 36、90-91 页）

# ---------------------------------------------------------------- 2026 年报表口径
NP_H1 = 10.3035         # 2026H1 归母（2026H1_report 第 7 页）
DEDUCT_H1 = 9.9158      # 2026H1 扣非归母（同上）
INT_EXP_H1 = 0.0735     # 2026H1 利息支出：长期应付款未确认融资费用 0.0652 + 租赁 0.0084（第 112 页）
INT_INC_H1 = 0.0234     # 2026H1 利息收入（第 112 页）
TAX = 0.15              # 母公司及主要子公司高新技术企业税率（2026H1_report 第 78-79 页）
NP_9M = {"low": 16.7874, "mid": (16.7874 + 20.5179) / 2, "high": 20.5179}  # forecast_20261017_621578 第 1 页
H2_NONOP = 0.60         # 2026H2 净利息与非经常项目税后合计（估计：净利息约 0.50，补助等约 0.10）

WMP_YIELD = 0.0165      # 2026H1 理财收益 0.331 亿（投资收益+公允价值变动，第 112 页）÷ 约 40 亿 × 2
NET_INTEREST_2026 = (
    40.0 * WMP_YIELD                                 # 首发前理财与定存约 40 亿，全年
    + IPO_NET * WMP_YIELD * 5 / 12                   # 首发资金 7-30 到位，约 5 个月
    - DIVIDEND_PAID * WMP_YIELD * 3 / 12             # 9-28 派息
    + 0.05                                           # 银行存款利息
    - 0.147                                          # 代建回购与租赁利息支出
) * (1 - TAX)
OP_H1_2026 = DEDUCT_H1 + (INT_EXP_H1 - INT_INC_H1) * (1 - TAX)   # 2026H1 经营性利润（不含利息）

# ---------------------------------------------------------------- 三情景
# q3：2026 三季度单季归母取预告低／中／高，四季度按三季度水平
# cyc：2026 年报表口径经营利润中的周期超额占比（元器件涨价与备货、PCB 景气量、废料铜价、经营杠杆）
# g：2027-2031 年正常化经营利润增速；2032-2036 线性降向 2.5%，2037 起永续 2.5%
# roic：增量资本回报（再投资率 = 下一年增速 ÷ roic，终值同）
# f27、f28：2027、2028 年周期超额 = 系数 × 2026H2 超额年化值（熊市为负：去库存与跌价）
SCENARIOS = {
    "bear": {"p": 0.25, "q3": "low", "cyc": 0.32, "g": [0.10, 0.10, 0.09, 0.08, 0.08],
             "roic": 0.20, "f27": -0.37, "f28": -0.19},
    "base": {"p": 0.50, "q3": "mid", "cyc": 0.27, "g": [0.20, 0.17, 0.15, 0.13, 0.11],
             "roic": 0.30, "f27": 0.35, "f28": 0.00},
    "bull": {"p": 0.25, "q3": "high", "cyc": 0.22, "g": [0.26, 0.22, 0.18, 0.15, 0.13],
             "roic": 0.40, "f27": 0.40, "f28": 0.15},
}
H2_SHARE = 0.55          # 下半年占全年正常化利润比重（2025 年 H2 占 54.5%）
T_STUB = 0.2             # 2026H2 现金流折现时点（年）
T_2027 = 0.70            # 2027 年年中距估值时点（年）


def h2_op_reported(s):
    return 2 * (NP_9M[s["q3"]] - NP_H1) - H2_NONOP


def op_2026_reported(s):
    return OP_H1_2026 + h2_op_reported(s)


def derive(s):
    """由情景参数推出正常化基数、下半年占比与周期超额序列。"""
    if s.get("reported_start"):            # 反向 DCF：以报表口径为起点，不计周期超额
        np26 = op_2026_reported(s)
        return np26, h2_op_reported(s) / np26, []
    np26 = op_2026_reported(s) * (1 - s["cyc"])
    h2ex = h2_op_reported(s) - np26 * H2_SHARE
    ex = [(2026, h2ex), (2027, s["f27"] * 2 * h2ex), (2028, s["f28"] * 2 * h2ex)]
    return np26, H2_SHARE, ex


def growth_path(s):
    """2027-2037 年增速（11 个）。"""
    g5 = list(s["g"])
    last = g5[-1]
    fade = [last - (last - G_TERMINAL) * i / 6 for i in range(1, 6)]   # 2032-2036
    return g5 + fade + [G_TERMINAL]


def value(s, k=COE, detail=False):
    np26, h2_share, ex = derive(s)
    g = growth_path(s)                       # g[0]=2027 ... g[10]=2037
    roic = s["roic"]
    np_ = [np26]
    for gi in g:
        np_.append(np_[-1] * (1 + gi))       # np_[0]=2026 ... np_[11]=2037
    stub = np26 * h2_share * (1 - g[0] / roic)          # 2026H2 正常化所有者收益
    pv_stub = stub / (1 + k) ** T_STUB
    oe, pv_oe = [], 0.0
    for i in range(10):                      # 2027-2036
        o = np_[i + 1] * (1 - g[i + 1] / roic)
        oe.append(o)
        pv_oe += o / (1 + k) ** (T_2027 + i)
    oe_2037 = np_[11] * (1 - G_TERMINAL / roic)
    pv_tv = oe_2037 / (k - G_TERMINAL) / (1 + k) ** (T_2027 + 9)
    pv_ex = sum(a / (1 + k) ** (T_STUB if y == 2026 else T_2027 + (y - 2027)) for y, a in ex)
    equity = pv_stub + pv_oe + pv_tv + pv_ex + NET_CASH_ADJ + NON_OPERATING
    v = equity / SHARES
    if not detail:
        return v
    return {"v": v, "equity": equity, "pv_stub": pv_stub, "pv_oe": pv_oe, "pv_tv": pv_tv,
            "pv_ex": pv_ex, "np": np_, "oe": oe, "oe_2037": oe_2037, "g": g, "excess": ex,
            "tv_share": pv_tv / (pv_stub + pv_oe + pv_tv)}


def weighted(k=COE, scen=None, weights=None):
    scen = scen or SCENARIOS
    w = weights or {n: s["p"] for n, s in scen.items()}
    return sum(w[n] * value(s, k) for n, s in scen.items())


def solve(f, lo, hi, target, n=200):
    """二分求解 f(x) = target（f 单调）。"""
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def variant(**changes):
    out = {}
    for n, s in SCENARIOS.items():
        t = dict(s)
        for key, fn in changes.items():
            t[key] = fn(t[key])
        out[n] = t
    return out


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def main():
    mcap = PRICE * SHARES
    print("=== 嘉立创（001232）独立估值  价格日 2026-10-20  现价 %.2f 元  总股本 %.4f 亿股  市值 %.2f 亿 ==="
          % (PRICE, SHARES, mcap))

    print("\n[经调整净现金]")
    print("  货币资金 %.4f + 理财 %.4f + 定存 %.4f + 首发净额 %.4f − 中期分红 %.4f − 受限 %.4f"
          " − 经营备付 %.1f − 类债务 %.4f = %.2f 亿（每股 %.2f 元）"
          % (CASH, WMP, TIME_DEPOSIT, IPO_NET, DIVIDEND_PAID, RESTRICTED, OPERATING_RESERVE,
             DEBT_LIKE, NET_CASH_ADJ, NET_CASH_ADJ / SHARES))
    print("  类债务 = 代建租赁回购 %.4f + 暂收款 %.4f + 租赁负债 %.4f；非经营资产 %.4f"
          % (BUYBACK_LEASE, TEMP_RECEIPT, LEASE, NON_OPERATING))

    print("\n[2026 年报表口径估计与正常化]")
    print("  2026H1 经营性利润（扣非加回税后净利息支出）%.2f；2026 年净利息（税后）%.2f" % (OP_H1_2026, NET_INTEREST_2026))
    for n in ("bear", "base", "bull"):
        s = SCENARIOS[n]
        np26, _, ex = derive(s)
        q3 = NP_9M[s["q3"]] - NP_H1
        print("  %-4s 三季度单季 %.2f → 2026 报表归母约 %.2f、经营利润 %.2f；周期占比 %.0f%% → 正常化经营利润 %.2f；"
              "正常化归母（含净利息）%.2f；周期超额 2026H2 %.2f / 2027 %.2f / 2028 %.2f"
              % (n, q3, NP_H1 + 2 * q3, op_2026_reported(s), s["cyc"] * 100, np26,
                 np26 + NET_INTEREST_2026, ex[0][1], ex[1][1], ex[2][1]))

    print("\n[三情景 DCF，股权成本 %.0f%%，终值增速 %.1f%%]" % (COE * 100, G_TERMINAL * 100))
    for n in ("bear", "base", "bull"):
        s = SCENARIOS[n]
        d = value(s, COE, detail=True)
        print("  %-4s p=%.2f  V=%.2f 元  股权价值 %.1f 亿 = 2026H2 %.1f + 2027-36 所有者收益 %.1f + 终值 %.1f"
              " + 周期超额 %.1f + 净现金 %.1f + 非经营 %.1f；终值占经营价值 %.0f%%"
              % (n, s["p"], d["v"], d["equity"], d["pv_stub"], d["pv_oe"], d["pv_tv"], d["pv_ex"],
                 NET_CASH_ADJ, NON_OPERATING, d["tv_share"] * 100))
        print("       经营利润 " + "  ".join("%d:%.1f" % (2026 + i, d["np"][i]) for i in range(6))
              + "  2036:%.1f" % d["np"][10])
        print("       增速 " + "  ".join("%d:%.0f%%" % (2027 + i, d["g"][i] * 100) for i in range(5))
              + "  2032-36:%.1f%%→%.1f%%  永续 %.1f%%" % (d["g"][5] * 100, d["g"][9] * 100, G_TERMINAL * 100))
        print("       所有者收益 " + "  ".join("%d:%.1f" % (2027 + i, d["oe"][i]) for i in range(5))
              + "  2037:%.1f；2027 再投资率 %.0f%%，增量回报 %.0f%%"
              % (d["oe_2037"], d["g"][1] / s["roic"] * 100, s["roic"] * 100))
    vw = weighted()
    pv = PRICE / vw
    print("\n[加权] V = %.2f 元；P/V = %.2f（%s）" % (vw, pv, band(pv)))
    print("  V 不变时各档价格：明显低估 ≤ %.1f；温和低估 %.1f～%.1f；大致合理 %.1f～%.1f；偏贵 > %.1f 元"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    v8, v10 = weighted(0.08), weighted(0.10)
    print("\n[股权成本敏感性] 8%%：加权 V = %.2f 元（P/V %.2f）；10%%：加权 V = %.2f 元（P/V %.2f）"
          % (v8, PRICE / v8, v10, PRICE / v10))
    for n in ("bear", "base", "bull"):
        print("  %-4s 8%%: %.2f  9%%: %.2f  10%%: %.2f"
              % (n, value(SCENARIOS[n], 0.08), value(SCENARIOS[n], 0.09), value(SCENARIOS[n], 0.10)))

    base = SCENARIOS["base"]
    irr = solve(lambda k: value(base, k), 0.03, 0.30, PRICE)
    irr_w = solve(lambda k: weighted(k), 0.03, 0.30, PRICE)
    print("\n[现价隐含回报] 基准情景所有者收益流（含终值、周期超额与净现金）现值等于现价的折现率 = %.2f%%"
          "（三情景加权现金流约 %.2f%%）" % (irr * 100, irr_w * 100))

    print("\n[反向 DCF]")
    np26_base = derive(base)[0]

    def v_g5(g5):
        s = dict(base)
        s["g"] = [g5] * 5
        return value(s)

    def v_rep(g5):
        s = dict(base)
        s["g"] = [g5] * 5
        s["reported_start"] = True
        return value(s)

    def v_perp(g):
        oe = np26_base * (1 + g) * (1 - g / base["roic"])
        return (oe / (COE - g) + NET_CASH_ADJ + NON_OPERATING) / SHARES

    print("  以正常化经营利润 %.1f 亿为起点、增量回报 30%%：现价隐含 2027-2031 年经营利润年增速 %.1f%%"
          "（之后 5 年线性降至 2.5%%）" % (np26_base, solve(v_g5, 0.0, 0.80, PRICE) * 100))
    print("  以 2026 年报表口径经营利润 %.1f 亿为起点（视同全部可持续）：隐含 2027-2031 年增速 %.1f%%"
          % (op_2026_reported(base), solve(v_rep, 0.0, 0.80, PRICE) * 100))
    print("  若无高增长期（正常化基数直接永续、增量回报 30%%）：现价隐含永续增速 %.2f%%"
          % (solve(v_perp, 0.0, 0.0899, PRICE) * 100))

    print("\n[交叉验证]")
    ttm_np, ttm_deduct = 17.43, 16.73
    rep_2026 = NP_H1 + 2 * (NP_9M["mid"] - NP_H1)
    ttm_ebit = (15.419 - 6.994 + 12.268) - 0.623 + 0.15 - 0.05   # TTM 利润总额 − 理财收益 + 利息支出 − 利息收入
    ev = mcap - NET_CASH_ADJ - NON_OPERATING
    print("  现价：PE(TTM 归母 %.2f) %.1f×；PE(TTM 扣非 %.2f) %.1f×；PE(2026 报表口径估计 %.1f) %.1f×；"
          "EV %.0f 亿 ÷ TTM EBIT %.2f = %.1f×" % (ttm_np, mcap / ttm_np, ttm_deduct, mcap / ttm_deduct, rep_2026,
                                               mcap / rep_2026, ev, ttm_ebit, ev / ttm_ebit))
    eq_w = vw * SHARES
    op_val = eq_w - NET_CASH_ADJ - NON_OPERATING
    print("  加权 V：股权 %.0f 亿，经营价值 %.0f 亿 = 基准正常化经营利润 %.1f 的 %.1f×、2026 报表经营利润 %.1f 的 %.1f×"
          % (eq_w, op_val, np26_base, op_val / np26_base, op_2026_reported(base), op_val / op_2026_reported(base)))
    print("  股息率 %.2f%%（过去 12 个月每股 0.50 元），无回购；首发价 84.46 元对应市值 %.1f 亿；2022-08 增资投后 375 亿"
          % (0.50 / PRICE * 100, 84.46 * SHARES))

    new_sh = SHARES * 0.10 / 0.90
    v_h = (vw * SHARES + new_sh * 130 * 0.97) / (SHARES + new_sh)
    print("\n[H 股情景，未计入主口径] 发行占扩大后股本 10%%、发行价 130 元、费用 3%%：新增 %.4f 亿股，"
          "募资净额 %.1f 亿，加权 V %.2f → %.2f 元" % (new_sh, new_sh * 130 * 0.97, vw, v_h))

    print("\n[证伪情景 V]")
    f1 = weighted(weights={"bear": 0.45, "base": 0.45, "bull": 0.10})
    f2 = weighted(weights={"bear": 0.60, "base": 0.40, "bull": 0.00})
    f3 = weighted(scen=variant(cyc=lambda c: c + 0.06, roic=lambda r: r - 0.05))
    f4 = weighted(weights={"bear": 0.10, "base": 0.40, "bull": 0.50})
    f5 = weighted(scen=variant(roic=lambda r: max(r - 0.10, 0.12)))
    print("  F1 三季度单季扣非 < 6.0 亿（概率改为 45/45/10）：V = %.2f" % f1)
    print("  F2 2026 年 PCB 毛利率 < 26%%（周期占比 +6pp、增量回报 −5pp）：V = %.2f" % f3)
    print("  F3 2027H1 元器件收入同比 < +5%% 或综合毛利率 < 26%%（概率 60/40/0）：V = %.2f" % f2)
    print("  F4（上行）2027H1 扣非同比 ≥ +35%% 且元器件单笔订单金额同比 ≤ +10%%（概率 10/40/50）：V = %.2f" % f4)
    print("  F5 2027 年末固定资产+在建工程 > 75 亿而 2027 年扣非 < 24 亿（增量回报 −10pp）：V = %.2f" % f5)


if __name__ == "__main__":
    main()
