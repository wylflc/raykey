#!/usr/bin/env python3
"""重庆啤酒（600132）独立估值：归母口径所有者收益 DCF，三情景概率加权。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。估值日 2026-10-20（北京时间收盘）。
全部输入写在本文件内；出处见正文「来源」一节（公告文件与 PDF 物理页）。
"""

# ---------------------------------------------------------------- 快照
PRICE = 38.42            # 2026-10-20 收盘，元
SHARES = 4.8397          # 亿股，总股本 483,971,198 股；无回购专户、无拟注销股份
COE = 0.09               # 股权成本基准
T_YE2026 = 72 / 365      # 2026-10-20 → 2026-12-31 的年数

# ---------------------------------------------------------------- 归母比例
# 上市公司持有嘉士伯重庆啤酒有限公司（原重庆嘉酿）51.42%，嘉士伯经广州嘉士伯投资持有 48.58%；全部啤酒业务在该子公司。
# 孙公司少数股东（宁夏西夏嘉酿 30%、嘉士伯安徽 25%、湖南 1.25%、广东 1%）由 2026H1 倒推约占子公司净利 0.9%。
STAKE = 0.5142
SUBSUB_MINORITY = 0.009
ATTR = STAKE * (1 - SUBSUB_MINORITY)


def check_attribution():
    """2026H1：子公司净利 × ATTR − 母公司自身费用 ≈ 归母净利。"""
    sub_np_h1 = 16.1150      # 2026H1_report 第 132 页：嘉士伯重庆啤酒净利 161,149.94 万元
    parent_np_h1 = 7.9592    # 2026H1_report 第 41 页
    parent_cost_h1 = 0.285   # 母公司管理费用（第 42 页）
    return sub_np_h1 * ATTR - parent_cost_h1, parent_np_h1


# ---------------------------------------------------------------- 经调整净现金（合并，2026-06-30）
CASH = 22.813            # 货币资金（2026H1_report 第 34 页）
RESTRICTED = 0.066       # 应计利息 0.041 + 诉讼及其他保证金 0.025（第 12、79 页）
MMF = 5.001              # 交易性金融资产，货币市场基金（第 34、79 页）

# 季节性营运资金：中报时点应付与应交税费处于旺季高位，下半年回吐（2023~2025 年下半年 8 科目分别 -7.4/-13.9/-11.3 亿）。
# 取 8 个科目 2025-12-31 → 2026-06-30 的变动，并加回已识别的非季节流出（嘉威 1 亿结算款支付、其他押金及保证金退还 2.17 亿）。
WC_ITEMS = {  # 科目: (2025-12-31, 2026-06-30, 符号)  +1 经营性负债，-1 经营性资产
    "应付账款": (23.867, 31.474, +1),
    "应交税费": (0.918, 4.430, +1),
    "其他应付款": (25.357, 24.456, +1),
    "合同负债": (17.158, 16.308, +1),
    "应付职工薪酬": (4.577, 3.492, +1),
    "应收账款": (0.874, 4.449, -1),
    "存货": (20.445, 16.914, -1),
    "其他流动资产": (1.579, 0.359, -1),
}
NON_SEASONAL_OUTFLOW = 1.000 + 2.168

LEASE = 0.785 + 0.415     # 租赁负债 + 一年内到期的非流动负债
LT_EMPLOYEE = 1.411       # 长期应付职工薪酬（设定受益计划等）
BAOXIAO_PROV = 1.180      # 预计负债：包销业务相关负债（嘉威 2026~2028 固定包销），按税后扣
TAX = 0.25
DEPOSIT_TREND = 1.786     # 其他押金及保证金：2024 末 9.00 → 2025 末 3.95 → 2026H1 1.79，持续退还，余额按类债务扣
OP_RESERVE = 3.0          # 经营备付（约 1 周现金成本）
PARENT_CASH = 0.227       # 母公司自有现金（第 37 页），100% 归母
PARENT_LT_EMP = 0.530     # 母公司长期应付职工薪酬（第 38 页），由母公司全额承担
OTHER_EQUITY_INV = 0.137  # 其他权益工具投资（非经营资产，按 ATTR 归母）


def seasonal_wc():
    raw = sum(sign * (h1 - ye) for ye, h1, sign in WC_ITEMS.values())
    return raw, raw + NON_SEASONAL_OUTFLOW


def net_cash():
    wc_raw, wc_seasonal = seasonal_wc()
    cash_like = CASH - RESTRICTED + MMF
    debt_like = LEASE + LT_EMPLOYEE + BAOXIAO_PROV * (1 - TAX) + DEPOSIT_TREND
    consolidated = cash_like - wc_seasonal - debt_like - OP_RESERVE
    attributable = ATTR * (consolidated - PARENT_CASH + PARENT_LT_EMP) + PARENT_CASH - PARENT_LT_EMP
    non_operating = ATTR * OTHER_EQUITY_INV
    return dict(cash_like=cash_like, wc_raw=wc_raw, wc_seasonal=wc_seasonal, debt_like=debt_like,
                consolidated=consolidated, attributable=attributable, non_operating=non_operating)


# ---------------------------------------------------------------- 再投资
# 增长期：再投资率 = g / RONIC（RONIC 取 50%，含负营运资金对增长的自融资）。
# 收缩期：负营运资金（经营性负债净额约为收入的 33%）随收入收缩而流出，流出 = FLOAT_RATIO × |g| × 归母净利。
RONIC = 0.50
NOL_TO_REVENUE = 0.33       # 2025 末 8 科目经营性负债净额 49.0 亿 ÷ 收入 147.2 亿
REV_TO_NI_CONS = 142.4 / 22.2   # 2026E 合并收入 ÷ 合并净利
FLOAT_RATIO = NOL_TO_REVENUE * REV_TO_NI_CONS   # 约 2.1


def reinvestment(g, ni):
    if g >= 0:
        return g / RONIC * ni
    return FLOAT_RATIO * (-g) * ni


# ---------------------------------------------------------------- 情景
# ni26：2026 正常化归母净利（含净利息，剔除一次性项目）；h2_oe：2026 年下半年归母所有者收益（三、四季度估计）
# growth：2027~2031 归母净利增速；g_term：2032 起永续增速
# baoxiao：2029 起嘉威包销到期的净影响（归母税后，亿元/年）；capex_gap：资本开支低于折旧的阶段性差额（归母）
SCENARIOS = {
    "bear": dict(p=0.25, ni26=10.4, h2_oe=2.85,
                 growth=[-0.03, -0.02, -0.01, 0.00, 0.00], g_term=0.000,
                 baoxiao=-0.2, capex_gap=[0.3, 0.3, 0.0, 0.0, 0.0],
                 note="三季度归母约 3.1 亿（同比 -18%）；核心市场份额继续流失，2027~2029 年归母累计 -6%，之后零增长；"
                      "嘉威到期后自立品牌竞争、联营收益消失（-0.2 亿/年）；收缩期负营运资金流出"),
    "base": dict(p=0.50, ni26=11.2, h2_oe=3.30,
                 growth=[0.005, 0.015, 0.015, 0.015, 0.015], g_term=0.015,
                 baoxiao=0.3, capex_gap=[0.6, 0.6, 0.0, 0.0, 0.0],
                 note="三季度归母约 3.4 亿（同比 -10%）；销量年降约 1%、吨价与结构年增约 2%，利润率持平；"
                      "2027 年铝价抬升抵消部分增长；2029 年起包销到期回收 0.3 亿/年"),
    "bull": dict(p=0.25, ni26=12.0, h2_oe=3.70,
                 growth=[0.04, 0.04, 0.03, 0.03, 0.03], g_term=0.025,
                 baoxiao=0.6, capex_gap=[0.6, 0.6, 0.0, 0.0, 0.0],
                 note="三季度归母约 3.65 亿（同比 -3%）；天气与现饮恢复，嘉士伯、乐堡延续增长，乌苏止跌，"
                      "净利率回到 2025 年水平；包销到期回收 0.6 亿/年"),
}
YEARS = [2027, 2028, 2029, 2030, 2031]


def flows(s, growth=None, g_term=None):
    growth = s["growth"] if growth is None else growth
    g_term = s["g_term"] if g_term is None else g_term
    out = [(T_YE2026, s["h2_oe"])]
    ni = s["ni26"]
    nis, oes = [], []
    for i, (y, g) in enumerate(zip(YEARS, growth)):
        ni = ni * (1 + g)
        ni_y = ni + (s["baoxiao"] if y >= 2029 else 0.0)
        oe = ni_y - reinvestment(g, ni_y) + s["capex_gap"][i]
        nis.append(ni_y)
        oes.append(oe)
        out.append((T_YE2026 + (y - 2026), oe))   # 年末计（接近中期与年度分红的平均到账时点）
    ni_term = nis[-1] * (1 + g_term)
    oe_term = ni_term - reinvestment(g_term, ni_term)
    return out, oe_term, nis, oes


def value(s, r, mid_year=False):
    nc = net_cash()
    cf, oe_term, _, _ = flows(s)
    shift = 0.5 if mid_year else 0.0
    pv = s["h2_oe"] / (1 + r) ** T_YE2026 + sum(c / (1 + r) ** (t - shift) for t, c in cf[1:])
    t_last = cf[-1][0]
    tv = oe_term / (r - s["g_term"])
    pv_tv = tv / (1 + r) ** (t_last - shift)
    equity = pv + pv_tv + nc["attributable"] + nc["non_operating"]
    return dict(v=equity / SHARES, pv_explicit=pv, pv_tv=pv_tv, tv_share=pv_tv / equity, equity=equity)


def weighted(r, mid_year=False):
    return sum(SCENARIOS[k]["p"] * value(SCENARIOS[k], r, mid_year)["v"] for k in SCENARIOS)


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


def implied_irr(s):
    return solve(lambda r: value(s, r)["v"], 0.03, 0.20, PRICE)


def reverse_perpetual_g():
    """现价隐含永续增速：基准 2026 正常化 11.2 亿为起点，2027 年起恒定增速，不计包销回收与资本开支差额。"""
    b = SCENARIOS["base"]

    def v_of_g(g):
        s = dict(b, growth=[g] * 5, g_term=g, baoxiao=0.0, capex_gap=[0.0] * 5)
        return value(s, COE)["v"]
    return solve(v_of_g, -0.03, 0.065, PRICE)


def reverse_10y_growth(g_term=0.015):
    """现价隐含的 10 年归母净利复合增速（第 11 年起永续 g_term，9% 折现）。"""
    b = SCENARIOS["base"]
    nc = net_cash()

    def v_of_g(g):
        pv = b["h2_oe"] / (1 + COE) ** T_YE2026
        ni = b["ni26"]
        for k in range(1, 11):
            ni *= 1 + g
            pv += (ni - reinvestment(g, ni)) / (1 + COE) ** (T_YE2026 + k)
        ni_t = ni * (1 + g_term)
        pv += (ni_t - reinvestment(g_term, ni_t)) / (COE - g_term) / (1 + COE) ** (T_YE2026 + 10)
        return (pv + nc["attributable"] + nc["non_operating"]) / SHARES
    return solve(v_of_g, -0.05, 0.12, PRICE)


def weighted_with(probs=None, mods=None, r=COE):
    """在给定概率或情景改动下重算加权 V（证伪触发后的 V）。"""
    probs = probs or {k: SCENARIOS[k]["p"] for k in SCENARIOS}
    mods = mods or {}
    total = 0.0
    for k, s in SCENARIOS.items():
        s2 = dict(s, **mods.get(k, {}))
        total += probs[k] * value(s2, r)["v"]
    return total


FALSIFIERS = [
    dict(key="F1", condition="2026 三季报：三季度单季归母净利 < 3.1 亿元（同比降幅 > 18%），或前三季度销量同比降幅 > 4%",
         deadline="2026-10-30",
         probs={"bear": 0.45, "base": 0.45, "bull": 0.10},
         mods={"base": {"ni26": 10.9, "h2_oe": 3.0}, "bear": {"h2_oe": 2.6}}),
    dict(key="F2", condition="2026 年报：2026 扣非归母净利 < 10.3 亿元，或 2026 年度每股现金分红合计 < 2.00 元",
         deadline="2027-04-30",
         probs={"bear": 0.50, "base": 0.40, "bull": 0.10},
         mods={"base": {"ni26": 10.8}}),
    dict(key="F3", condition="2027 中报：上半年销量 < 170 万千升（较 2026H1 再降 > 2.8%）且高档收入同比下降",
         deadline="2027-08-31",
         probs=None,
         mods={"base": {"growth": [-0.005, 0.005, 0.005, 0.005, 0.005], "g_term": 0.005, "baoxiao": 0.1},
               "bull": {"growth": [0.02, 0.02, 0.02, 0.02, 0.02], "g_term": 0.015, "baoxiao": 0.3}}),
    dict(key="F4", condition="（上行）2027 中报：上半年归母净利 ≥ 8.65 亿元（回到 2025H1 水平，同比约 +9%）且销量 ≥ 178 万千升",
         deadline="2027-08-31",
         probs={"bear": 0.15, "base": 0.45, "bull": 0.40},
         mods={"base": {"ni26": 11.7}}),
    dict(key="F5", condition="2027 年度日常关联交易预计或年报显示对嘉士伯的许可费、服务费年化新增 ≥ 1 亿元（2026 预计授权许可 2.42 亿元）",
         deadline="2027-04-30",
         probs=None,
         mods={k: {"ni26": SCENARIOS[k]["ni26"] - 1.0 * 0.75 * ATTR} for k in ("bear", "base", "bull")}),
]


def band(pv):
    if pv <= 0.75:
        return "明显低估"
    if pv <= 0.90:
        return "温和低估"
    if pv <= 1.10:
        return "大致合理"
    return "偏贵或价值陷阱风险高"


def cross_checks():
    """交叉验证读数（只作参考，不进入 V）。"""
    mcap = PRICE * SHARES
    ni_parent_ttm, ni_cons_ttm = 11.62, 23.36          # TTM 截至 2026-06-30
    ni_parent_26e = 7.959 + 3.40 - 0.30               # 2026E 归母（基准）
    ebit_ttm = 30.62 + 0.069 - 0.163                  # 营业利润 TTM − 投资收益 TTM − 净利息收入 TTM
    nc = net_cash()
    ev_cons = mcap * ni_cons_ttm / ni_parent_ttm - nc["consolidated"]
    return dict(mcap=mcap, pe_ttm=mcap / ni_parent_ttm, pe_26e=mcap / ni_parent_26e, ni26e=ni_parent_26e,
                ev_cons=ev_cons, ev_ebit=ev_cons / ebit_ttm, dy_ttm=2.50 / PRICE,
                dy_fwd=ni_parent_26e / SHARES / PRICE, oe_yield=SCENARIOS["base"]["ni26"] / mcap)


def main():
    est, act = check_attribution()
    print(f"归母比例核对：子公司净利 × {ATTR:.4f} − 母公司费用 = {est:.2f} 亿；实际 2026H1 归母 {act:.2f} 亿")
    nc = net_cash()
    print(f"季节性营运资金：8 科目上半年净流入 {nc['wc_raw']:.2f}，加回非季节流出后按 {nc['wc_seasonal']:.2f} 回吐")
    print(f"现金类 {nc['cash_like']:.2f} − 季节回吐 {nc['wc_seasonal']:.2f} − 类债务 {nc['debt_like']:.2f} − 经营备付 {OP_RESERVE:.1f}"
          f" = 合并经调整净现金 {nc['consolidated']:.2f} 亿；归母 {nc['attributable']:.2f} 亿（{nc['attributable']/SHARES:.2f} 元/股）；"
          f"非经营资产归母 {nc['non_operating']:.2f} 亿")
    print()
    for k, s in SCENARIOS.items():
        cf, oe_term, nis, oes = flows(s)
        r9, r8, r10 = value(s, COE), value(s, 0.08), value(s, 0.10)
        print(f"[{k}] p={s['p']:.2f}  2026 正常化归母 {s['ni26']:.1f}  2026 下半年所有者收益 {s['h2_oe']:.2f}")
        print("   增速   " + " ".join(f"{y}:{g:+.1%}" for y, g in zip(YEARS, s["growth"])) + f"  永续 {s['g_term']:.1%}")
        print("   归母净利 " + " ".join(f"{y}:{n:.2f}" for y, n in zip(YEARS, nis)))
        print("   所有者收益 " + " ".join(f"{y}:{o:.2f}" for y, o in zip(YEARS, oes)) + f"  终值首年 {oe_term:.2f}")
        print(f"   V(9%)={r9['v']:.2f}  终值占比 {r9['tv_share']:.1%}  V(8%)={r8['v']:.2f}  V(10%)={r10['v']:.2f}"
              f"  现价隐含回报 {implied_irr(s):.2%}")
    vw = weighted(COE)
    pv = PRICE / vw
    print()
    print(f"加权 V = {vw:.2f} 元/股；P/V = {pv:.3f}（{band(pv)}）")
    print(f"8% 下加权 V = {weighted(0.08):.2f}；10% 下加权 V = {weighted(0.10):.2f}")
    print(f"基准情景现价隐含回报（IRR）= {implied_irr(SCENARIOS['base']):.2%}")
    print(f"反向 DCF：现价隐含永续增速 {reverse_perpetual_g():.2%}；隐含 10 年复合增速 {reverse_10y_growth():.2%}（第 11 年起 1.5%）")
    print(f"V 不变时分档价格：≤{0.75*vw:.2f} 明显低估；≤{0.90*vw:.2f} 温和低估；≤{1.10*vw:.2f} 大致合理；>{1.10*vw:.2f} 偏贵")
    print(f"参考（非登记口径）：年中折现约定下加权 V = {weighted(COE, mid_year=True):.2f}")
    cc = cross_checks()
    print(f"交叉验证：市值 {cc['mcap']:.1f} 亿；PE(TTM) {cc['pe_ttm']:.1f}x；PE(2026E 归母 {cc['ni26e']:.2f}) {cc['pe_26e']:.1f}x；"
          f"合并口径 EV {cc['ev_cons']:.0f} 亿、EV/EBIT(TTM) {cc['ev_ebit']:.1f}x；股息率 TTM {cc['dy_ttm']:.2%}、"
          f"按 2026E 全额派息 {cc['dy_fwd']:.2%}；正常化收益率 {cc['oe_yield']:.2%}")
    print()
    print("证伪条件触发后的独立 V（9%）：")
    for f in FALSIFIERS:
        v = weighted_with(f["probs"], f["mods"])
        print(f"   {f['key']} [{f['deadline']}] V={v:.2f}  P/V={PRICE / v:.3f}  {f['condition']}")
    print()
    b = SCENARIOS["base"]
    _, _, nis, oes = flows(b)
    prev = b["ni26"]
    gr = []
    for n in nis:
        gr.append(n / prev - 1)
        prev = n
    print("基准归母净利增速（含包销回收）: " + ", ".join(f"{g:.4f}" for g in gr))


if __name__ == "__main__":
    main()
