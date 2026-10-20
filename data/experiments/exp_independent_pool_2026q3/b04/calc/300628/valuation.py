#!/usr/bin/env python3
"""亿联网络（300628）独立估值：经营所有者收益 DCF + 经调整净现金。

运行：python3 valuation.py
金额单位亿元，每股价值元/股。输入全部写在本脚本内，出处见注释与正文「来源」。
口径：经营所有者收益不含理财与利息收益；超额现金按面值单独加回（避免重复计算）。
"""
from datetime import date

# ---------------------------------------------------------------- 快照
PRICE = 36.59            # 2026-10-19 收盘（brief）
SHARES = 12.6692         # 亿股，腾讯行情口径；191 股回购专户股份已于 2026-07-07 注销（buyback_20260707 第 1 页），
                         # 注销后总股本 1,266,918,377 股，回购专户已无股份，剔除前后 V 相同
MCAP = PRICE * SHARES
VAL_DATE = date(2026, 10, 19)
COE = 0.09

# ---------------------------------------------------------------- 资产负债表（2026-06-30，2026H1_report 第 44～46 页）
CASH = 10.1293           # 货币资金；报告期末无受限资产（第 12 页）
TFA = 40.2385            # 交易性金融资产：银行理财 5.38、证券资管 24.80、可转让存单 10.06（第 102 页附注）
ONCFA = 1.0007           # 其他非流动金融资产：预期持有超一年的证券资管产品
LEASE = 0.0350 + 0.0222  # 一年内到期租赁负债 + 租赁负债（无借款）
TRADING_FL = 0.0108      # 交易性金融负债（外汇衍生品）
INTERIM_DIV = 6.3346     # 2026 中期 10 派 5，2026-09-21 除息已付（dividend_20260914 第 1 页）
OP_RESERVE = 6.0         # 经营备付：约 1 个月收入 / 2 个月付现成本
NET_CASH_ADJ = CASH + TFA + ONCFA - LEASE - TRADING_FL - INTERIM_DIV - OP_RESERVE
# 非经营资产（打折计入）：长期股权投资 1.7219（凯泰创投基金等）×0.7；投资性房地产 1.6620×0.8；其他权益工具 0.02
NON_OP = 1.7219 * 0.7 + 1.6620 * 0.8 + 0.02

# ---------------------------------------------------------------- 2026 年报告利润估计与正常化
H1_NP = 15.2425          # 2026H1_report 第 7 页
NINE_M_NP = {"low": 22.3225, "mid": (22.3225 + 23.1058) / 2, "high": 23.1058}  # forecast_20261015 第 1 页
NINE_M_REV = {"low": 49.4309, "mid": (49.4309 + 51.1502) / 2, "high": 51.1502}
Q4_2025_NP, Q4_2025_REV = 6.425, 17.348  # 2025 年报减前三季报（数据包单季表）
NONREC_FY_AT = 1.36      # 2026 全年非经常性损益（税后）：9 月累计约 1.06（预告），四季度约 0.30，主要为理财收益与补助
NONREC_H2_AT = NONREC_FY_AT - 0.7935   # 上半年 0.7935（第 8 页）
FX_LOSS_FY_PRE = 0.95    # 全年汇兑损失估计（税前）：上半年 0.6574（第 142 页）+ 下半年约 0.3（美元兑人民币 6.81→6.72）
TAX = 0.10               # 母公司重点软件企业 10% 税率（2025_annual_report 第 145 页）；上半年实际税率 9.35%

def reported_fy2026(nine_m_key, q4_growth):
    """返回 (2026 营收, 2026 报告归母净利)。"""
    rev = NINE_M_REV[nine_m_key] + Q4_2025_REV * (1 + q4_growth)
    np_ = NINE_M_NP[nine_m_key] + Q4_2025_NP * (1 + q4_growth)
    return rev, np_

# ---------------------------------------------------------------- 情景
# growth: 2027～2036 营收增速；margin_path: 2027～2036 经营税后净利率（不含理财利息）；nwc_path: 营运资本/营收
DA_RATIO, CAPEX_RATIO = 0.013, 0.015     # 折旧摊销约 0.90/年（2026H1 0.452，第 146 页）；资本开支略高于折旧
NWC_2026 = 24.0                         # 2026 年末营运资本估计（6 月末 24.4，存货 19.01 为战略备货高位）

def linear(a, b, n):
    return [a + (b - a) * (i + 1) / n for i in range(n)]

SCEN = {}
# 基准：9 月累计取预告中值、四季度净利 +5%；正常化剔除非经常与汇兑，再加回超额现金 2.3% 收益
rev26, rep26 = reported_fy2026("mid", 0.05)
op26 = rep26 - NONREC_FY_AT + FX_LOSS_FY_PRE * (1 - TAX)
SCEN["base"] = dict(
    p=0.50, rev2026=rev26, reported2026=rep26, opnp2026=op26,
    interest_yield=0.023, h2_oe=(rep26 - H1_NP) - NONREC_H2_AT,
    growth=[0.06, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025],
    margin_path=linear(op26 / rev26, 0.400, 4) + [0.400] * 6,
    nwc_path=[0.335, 0.32] + [0.31] * 8, g_term=0.020,
    assumptions="2026 营收 68.5、经营净利率 42.3%；会议 +12%、耳机 +20%、话机 +1% 加权，扣汇率约 2%：2027 +6%、2028 +8%、2029 +7%、2030 +6%、2031 +5%，此后降至 2.5%；"
                "净利率因耳机占比上升、研发回升与存储涨价 2030 年降至 40%；营运资本率 35%→31%；终值增长 2.0%",
)
# 熊市：美国限制或关税压缩美洲业务、话机加速萎缩、人民币继续升值与存储涨价；2026 正常化归母 27.0（剔除备货与低价库存的周期性顺风）
rev26b, rep26b = reported_fy2026("low", -0.05)
SCEN["bear"] = dict(
    p=0.30, rev2026=rev26b, reported2026=rep26b, opnp2026=27.0 - 0.75,
    interest_yield=0.018, h2_oe=(rep26b - H1_NP) - NONREC_H2_AT,
    growth=[-0.05, -0.06, -0.03, 0.01, 0.02, 0.02, 0.02, 0.015, 0.015, 0.015],
    margin_path=linear((27.0 - 0.75) / rev26b, 0.350, 3) + [0.350] * 7,
    nwc_path=[0.35] * 10, g_term=0.010,
    assumptions="2026 营收 65.9（预告下限、四季度 -5%）；美国新品认证受限或关税抬升，美洲收入三年内缩减约三成；话机年降 4%～5%；2027 -5%、2028 -6%、2029 -3%、2030 +1%、2031 +2%，此后 1.5%～2%；"
                "经营净利率由 39.8% 降至 35%；营运资本率维持 35%；终值增长 1.0%",
)
# 牛市：会议与耳机持续夺份额、美国无新增限制、存储涨价顺利转嫁
rev26u, rep26u = reported_fy2026("high", 0.12)
op26u = rep26u - NONREC_FY_AT + FX_LOSS_FY_PRE * (1 - TAX)
SCEN["bull"] = dict(
    p=0.20, rev2026=rev26u, reported2026=rep26u, opnp2026=op26u,
    interest_yield=0.026, h2_oe=(rep26u - H1_NP) - NONREC_H2_AT,
    growth=[0.11, 0.11, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.035, 0.03],
    margin_path=linear(op26u / rev26u, 0.420, 5) + [0.420] * 5,
    nwc_path=[0.32, 0.29] + [0.28] * 8, g_term=0.025,
    assumptions="会议与耳机 15%～25% 增长、话机持平：2027 +11%、2028 +11%、2029 +10%、2030 +8%、2031 +7%，此后降至 3%；2026 营收 70.6、经营净利率 42.2% 并大致维持 42%；营运资本率降至 28%；终值增长 2.5%",
)

def t_mid(year):
    """年度现金流取年中（7 月 1 日）到估值日的年数。"""
    return (date(year, 7, 1) - VAL_DATE).days / 365.25

def scenario_value(s, r, detail=False):
    rev, nwc_prev = s["rev2026"], NWC_2026
    rows, pv_sum = [], s["h2_oe"]          # 2026 下半年经营现金流（含已实现汇兑，不含理财收益），视为当期
    oe = None
    for i, y in enumerate(range(2027, 2037)):
        rev = rev * (1 + s["growth"][i])
        opnp = rev * s["margin_path"][i]
        nwc = rev * s["nwc_path"][i]
        dnwc = nwc - nwc_prev
        nwc_prev = nwc
        net_capex = rev * (CAPEX_RATIO - DA_RATIO)
        oe = opnp - net_capex - dnwc
        df = (1 + r) ** -t_mid(y)
        pv_sum += oe * df
        rows.append((y, rev, s["margin_path"][i], opnp, dnwc, net_capex, oe, oe * df))
    tv = oe * (1 + s["g_term"]) / (r - s["g_term"])   # 以 2036 年中为基点
    pv_tv = tv * (1 + r) ** -t_mid(2036)
    ev_ops = pv_sum + pv_tv
    equity = ev_ops + NET_CASH_ADJ + NON_OP
    v = equity / SHARES
    if detail:
        return v, dict(rows=rows, pv_tv=pv_tv, ev_ops=ev_ops, equity=equity, tv_share=pv_tv / equity)
    return v

def weighted(r):
    return sum(SCEN[k]["p"] * scenario_value(SCEN[k], r) for k in SCEN)

def solve(f, lo, hi, target, it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if (f(mid) - target) * (f(lo) - target) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2

def normalized_np(s):
    excess_cash_avg = NET_CASH_ADJ + INTERIM_DIV / 2   # 2026 年平均超额现金（年中付中期股息）
    return s["opnp2026"] + excess_cash_avg * s["interest_yield"] * (1 - TAX)

def main():
    print(f"市值 {MCAP:.2f} 亿；经调整净现金 {NET_CASH_ADJ:.2f}；非经营资产 {NON_OP:.2f}")
    print("2026 正常化归母净利（含超额现金利息，剔除非经常与汇兑）：")
    for k in ("bear", "base", "bull"):
        s = SCEN[k]
        print(f"  {k}: 报告估计 {s['reported2026']:.2f}，营收 {s['rev2026']:.2f}，经营净利 {s['opnp2026']:.2f}，正常化归母 {normalized_np(s):.2f}")
    vals = {}
    for k in ("bear", "base", "bull"):
        v, d = scenario_value(SCEN[k], COE, detail=True)
        vals[k] = v
        print(f"\n[{k}] p={SCEN[k]['p']:.2f}  V={v:.2f} 元/股  经营 EV {d['ev_ops']:.1f}  股权 {d['equity']:.1f}  终值占股权 {d['tv_share']:.1%}")
        print("  年份  营收   净利率  经营净利  ΔNWC  净资本开支  所有者收益  现值")
        for y, rev, m, opnp, dnwc, ncx, oe, pv in d["rows"][:6]:
            print(f"  {y}  {rev:6.2f}  {m:.3f}  {opnp:6.2f}  {dnwc:5.2f}  {ncx:5.2f}  {oe:6.2f}  {pv:6.2f}")
    # 基准增长路径、再投资率与增量回报
    b = SCEN["base"]
    _, d = scenario_value(b, COE, detail=True)
    oe26 = b["opnp2026"] - b["rev2026"] * (CAPEX_RATIO - DA_RATIO)
    oes = [oe26] + [r_[6] for r_ in d["rows"][:5]]
    gpath = [oes[i + 1] / oes[i] - 1 for i in range(5)]
    reinv = sum(r_[4] + r_[5] for r_ in d["rows"][:5])
    opnp_sum = sum(r_[3] for r_ in d["rows"][:5])
    inc_ret = (d["rows"][4][3] - b["opnp2026"]) / reinv
    rd_at = 0.085 * (1 - TAX)   # 研发约占营收 8.5%（2025 年 8.78%），税后视同再投资
    reinv_rd = (reinv + sum(r_[1] * rd_at for r_ in d["rows"][:5])) / opnp_sum
    print(f"\n基准所有者收益增速 2027～2031：{[round(x, 3) for x in gpath]}；有形再投资率 {reinv/opnp_sum:.1%}，"
          f"增量有形资本回报 {inc_ret:.0%}；研发计作再投资后再投资率 {reinv_rd:.1%}，对应增量回报约 {(d['rows'][4][3]/b['opnp2026'])**(1/5)-1:.1%}/{reinv_rd:.1%}={((d['rows'][4][3]/b['opnp2026'])**(1/5)-1)/reinv_rd:.0%}")
    q3_rev = [NINE_M_REV[k] - 33.4929 for k in ("low", "mid", "high")]
    q3_np = [NINE_M_NP[k] - H1_NP for k in ("low", "mid", "high")]
    print(f"三季度单季推算：营收 {q3_rev[0]:.2f}～{q3_rev[2]:.2f}（中值 {q3_rev[1]:.2f}，同比 {q3_rev[1]/16.485-1:+.1%}）；"
          f"归母 {q3_np[0]:.2f}～{q3_np[2]:.2f}（中值 {q3_np[1]:.2f}，同比 {q3_np[1]/7.181-1:+.1%}）")
    vw = weighted(COE)
    pv_ratio = PRICE / vw
    band = "明显低估" if pv_ratio <= 0.75 else "温和低估" if pv_ratio <= 0.90 else "大致合理" if pv_ratio <= 1.10 else "偏贵或价值陷阱风险高"
    print(f"\n加权 V = {vw:.2f} 元/股；P/V = {pv_ratio:.3f}（{band}）")
    print(f"股权成本 8%：加权 V {weighted(0.08):.2f}（基准 {scenario_value(SCEN['base'], 0.08):.2f}）；"
          f"10%：加权 V {weighted(0.10):.2f}（基准 {scenario_value(SCEN['base'], 0.10):.2f}）")
    irr = solve(lambda r: scenario_value(SCEN["base"], r), 0.04, 0.30, PRICE)
    print(f"现价隐含回报（基准现金流）：{irr:.2%}")
    irr_w = solve(weighted, 0.05, 0.20, PRICE)
    irr_bear = solve(lambda r: scenario_value(SCEN["bear"], r), 0.02, 0.30, PRICE)
    irr_bull = solve(lambda r: scenario_value(SCEN["bull"], r), 0.04, 0.30, PRICE)
    print(f"  对照：使加权 V 等于现价的折现率 {irr_w:.2%}；熊市 {irr_bear:.2%}；牛市 {irr_bull:.2%}")
    # 反向 DCF 1：2027～2036 所有者收益统一增速 g，终值 2.0%，起点为基准 2026 经营净利×（1-0.2% 净资本开支率）
    base = SCEN["base"]
    oe0 = base["opnp2026"] - base["rev2026"] * (CAPEX_RATIO - DA_RATIO)
    def v_const(g, gt=0.02, r=COE):
        pv, oe = base["h2_oe"], oe0
        for y in range(2027, 2037):
            oe *= 1 + g
            pv += oe * (1 + r) ** -t_mid(y)
        pv += oe * (1 + gt) / (r - gt) * (1 + r) ** -t_mid(2036)
        return (pv + NET_CASH_ADJ + NON_OP) / SHARES
    g10 = solve(v_const, -0.10, 0.20, PRICE)
    # 反向 DCF 2：从 2027 年起永续增长
    def v_perp(g, r=COE):
        oe1 = oe0 * (1 + g)
        return (base["h2_oe"] + oe1 / (r - g) * (1 + r) ** -t_mid(2027) + NET_CASH_ADJ + NON_OP) / SHARES
    gp = solve(v_perp, -0.10, 0.08, PRICE)
    print(f"反向 DCF：现价隐含 2027～2036 所有者收益年增 {g10:.2%}（终值 2.0%）；或自 2027 年起永续增长 {gp:.2%}（起点 2026 经营所有者收益 {oe0:.2f}）")
    # 交叉验证
    ttm_np = 28.85
    ev = MCAP - NET_CASH_ADJ - NON_OP
    core_ebit_ttm = 7.642 + 6.422 + 6.846 + 9.690   # 2025Q3～2026Q2 单季：毛利-税金-三费-研发（f10）
    print(f"交叉：TTM PE {MCAP/ttm_np:.1f}×；剔除超额现金 PE {(ev)/(ttm_np-0.9):.1f}×；EV/核心 EBIT(TTM) {ev/core_ebit_ttm:.1f}×；"
          f"过去 12 个月股息率 {1.80/PRICE:.2%}；2026 预计股息 2.0 元 → {2.0/PRICE:.2%}")
    print(f"分档价格（V 不变）：≤{0.75*vw:.2f} 明显低估；{0.75*vw:.2f}～{0.90*vw:.2f} 温和低估；{0.90*vw:.2f}～{1.10*vw:.2f} 大致合理；>{1.10*vw:.2f} 偏贵")
    # 证伪触发后的 V
    print("\n证伪触发后的独立 V：")
    s1 = dict(SCEN["base"]); s1["margin_path"] = [m - 0.02 for m in SCEN["base"]["margin_path"]]
    f1 = 0.35 * vals["bear"] + 0.50 * scenario_value(s1, COE) + 0.15 * vals["bull"]
    print(f"  F1 三季报（2026-10-27）单季毛利率 <61% 或 9 月末存货 >21 亿：基准净利率下移 2 个百分点、权重 0.35/0.50/0.15 → {f1:.2f}")
    s = dict(SCEN["base"]); s["growth"] = [0.02, 0.04, 0.04, 0.04, 0.03, 0.03, 0.03, 0.025, 0.025, 0.02]
    f2_base = scenario_value(s, COE)
    f2 = 0.40 * vals["bear"] + 0.50 * f2_base + 0.10 * vals["bull"]
    print(f"  F2 2026 年扣非 <27.5 亿或会议产品全年增速 <10%（2027-04-30）：基准增速降为 2%～4%（V {f2_base:.2f}），权重 0.40/0.50/0.10 → {f2:.2f}")
    s3 = dict(SCEN["bear"]); s3["growth"] = [-0.08, -0.12, -0.08, 0.0, 0.02, 0.02, 0.02, 0.015, 0.015, 0.015]
    s3["margin_path"] = linear((27.0 - 0.75) / rev26b, 0.33, 3) + [0.33] * 7
    f3 = scenario_value(s3, COE)
    print(f"  F3 FCC 把企业通信终端/会议设备列入 Covered List 或点名亿联（2027-12-31 前）：美国收入三年内基本退出 → {f3:.2f}")
    ops_share = (vw * SHARES - NET_CASH_ADJ - NON_OP) / (vw * SHARES)
    f4 = vw * (1 - ops_share) + vw * ops_share * (1 - 0.15) / (1 - TAX)
    print(f"  F4 失去重点软件企业 10% 税率（适用 15%）：经营价值 ×0.944 → {f4:.2f}")
    s5 = dict(SCEN["base"]); s5["margin_path"] = [0.37] * 10
    f5 = 0.30 * vals["bear"] + 0.50 * scenario_value(s5, COE) + 0.20 * vals["bull"]
    print(f"  F5 2027 年中报毛利率 <60%（存储涨价或价格战）：基准净利率降至 37% → {f5:.2f}")
    return vals, vw

if __name__ == "__main__":
    main()
