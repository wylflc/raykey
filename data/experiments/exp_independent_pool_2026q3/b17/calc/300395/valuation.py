# -*- coding: utf-8 -*-
"""菲利华（300395）独立估值：归母所有者收益 DCF（OI-291 b17）。

运行：python3 valuation.py
金额单位：亿元；每股价值：元/股。所有输入写在本脚本内，出处见注释。
"""

PRICE = 78.83                 # 2026-10-21 收盘（brief.md）
SHARES = 5.2573               # 总股本，亿股（腾讯行情，含回购专户股份）
REPO_SHARES = 0.0027605       # 回购专户 276,050 股（2026H1_report 第 24 页），未公告注销
COE = 0.09
G_TERM = 0.025
VAL_T = 2026 + 294 / 365      # 估值日 2026-10-21 的年内位置

# ---------------- 一、2026 年正常化归母净利 ----------------
# 前三季度预告（forecast_20261015 第 1 页）：归母 4.50～5.20，扣非 4.23～4.93；
# 中报（2026H1_report 第 8 页）：归母 2.948，扣非 2.737。
H1_DEDUCT = 2.737
NINE_M_DEDUCT = {"bear": 4.23, "base": 4.58, "bull": 4.93}
Q4_DEDUCT = {"bear": 1.45, "base": 1.82, "bull": 2.20}   # 四季度扣非：约等于三季度单季（1.49～2.19，中值 1.84）
ADJ = {
    "wmp_interest": 0.14,   # 理财收益（扣非时剔除，经济上是现金利息），税后归母
    "fx_addback": 0.13,     # 2026 年汇兑损失回加（H1 财务费用 0.131 中约 0.12 为汇兑及手续费），税后归母
    "impair_norm": -0.10,   # 存货减值正常化（2026H1 资产减值仅 0.003，2025 年 0.358），税后归母
}
CYCLICAL_HAIRCUT = {"bear": -0.25, "base": 0.0, "bull": 0.0}  # 熊市：测试期石英布高价（250～300 元/米）回落的周期剔除

def normalized_np_2026(s):
    return NINE_M_DEDUCT[s] + Q4_DEDUCT[s] + sum(ADJ.values()) + CYCLICAL_HAIRCUT[s]

NP26 = {s: round(normalized_np_2026(s), 2) for s in ("bear", "base", "bull")}
H1_NORM = H1_DEDUCT + 0.5 * sum(ADJ.values())   # 上半年正常化（用于估算 2026 下半年所有者收益）

# ---------------- 二、经调整净现金（2026-06-30，2026H1_report 第 39～41 页） ----------------
CASH = 12.538          # 货币资金
TFA = 5.048            # 交易性金融资产（银行理财）
ONCFA = 1.710          # 其他非流动金融资产（一年以上理财）
RESTRICTED = 2.030     # 票据保证金（第 133 页），对应应付票据，不可自由支配
DEBT = 1.201 + 0.287 + 1.522   # 短期借款 + 长期借款 + 一年内到期非流动负债（含少量租赁）
DIV_PAYABLE = 0.118    # 应付股利（普通股股利）
DIV_INTERIM = 0.893    # 2026 中期分红 0.17 元/股 × 525,451,032 股，09-22 除息（dividend_20260821）
OP_RESERVE = 1.45      # 经营备付：2026E 营收约 29 亿的 5%
NET_CASH_GROUP = CASH + TFA + ONCFA - RESTRICTED - DEBT - DIV_PAYABLE - DIV_INTERIM - OP_RESERVE
PARENT_EQ, MINORITY_EQ = 52.376, 12.205
NET_CASH_ATTR = NET_CASH_GROUP * PARENT_EQ / (PARENT_EQ + MINORITY_EQ)   # 按归母权益占比折算
NON_OP = 0.108         # 长期股权投资（联营）账面；未计 1.85 亿未执行的诉讼赔偿（再审审查中）
# 租赁负债 0.010 与专项应付款 0.100 只列示不扣（所有者收益以净利润为起点，已含使用权资产折旧与租赁利息）

# ---------------- 三、情景 ----------------
SCEN = {
    "bear": dict(p=0.25, roiic=0.12, g=[-0.08, 0.04, 0.08, 0.08, 0.07],
                 note="石英电子布认证与放量受阻或价格战（价格较 250～300 元/米 腰斩），2027 半导体下行；增量回报 12%"),
    "base": dict(p=0.50, roiic=0.18, g=[0.30, 0.20, 0.15, 0.12, 0.10],
                 note="石英电子布 2027 年收入约翻倍、2027H2 起降价；半导体国产替代 +15% 左右；增量回报 18%（募投内部收益率 20.7%）"),
    "bull": dict(p=0.25, roiic=0.25, g=[0.50, 0.32, 0.22, 0.16, 0.13],
                 note="石英电子布进入 AI 服务器主流方案、中益 500 万平方米与鼎益 1,000 吨满产；2028 年归母约 14 亿；增量回报 25%"),
}
YEARS = list(range(2027, 2032))
FADE_YEARS = 5   # 2032～2036 线性降到 2.5%


def growth_path(g5):
    gs = list(g5)
    g_last = g5[-1]
    for k in range(1, FADE_YEARS + 1):
        gs.append(g_last + (G_TERM - g_last) * k / FADE_YEARS)
    return gs   # 2027..2036


B26_FLOOR = 1.0   # 2026 下半年再投资率下限：在建项目已锁定（鼎益电子纱剩余约 3.1 亿建设投资与 1.3 亿铺底流动资金、嘉殷基地剩余约 2.6 亿、电子布基材剩余约 1.0 亿）


def value(s, r=COE, np26=None, g5=None, roiic=None, detail=False):
    sc = SCEN[s]
    np26 = NP26[s] if np26 is None else np26
    g5 = sc["g"] if g5 is None else g5
    roiic = sc["roiic"] if roiic is None else roiic
    gs = growth_path(g5)
    b_floor = G_TERM / roiic          # 任何年份再投资率不低于终值期水平
    # 2026 下半年：归母正常化净利 × (1 − 再投资率)，再投资率 = max(2027 增速 / 增量回报, 100%)
    np_h2 = np26 - H1_NORM
    b26 = max(gs[0] / roiic, B26_FLOOR)
    pv = np_h2 * (1 - b26)            # t≈0（资产负债表日 6-30 至估值日之间）
    rows = [(2026.5, np_h2, b26, np_h2 * (1 - b26), 1.0)]
    np_t = np26
    for i, y in enumerate(range(2027, 2037)):
        np_t = np_t * (1 + gs[i])
        g_next = gs[i + 1] if i + 1 < len(gs) else G_TERM
        b = max(g_next / roiic, b_floor)
        oe = np_t * (1 - b)
        t = (y + 0.5) - VAL_T
        df = (1 + r) ** -t
        pv += oe * df
        rows.append((y, np_t, b, oe, df))
    # 终值：2037 年起所有者收益按 2.5% 永续，置于 2036 年年中
    np_2037 = np_t * (1 + G_TERM)
    oe_2037 = np_2037 * (1 - G_TERM / roiic)
    tv = oe_2037 / (r - G_TERM)
    t_tv = (2036 + 0.5) - VAL_T
    pv_tv = tv * (1 + r) ** -t_tv
    equity = pv + pv_tv + NET_CASH_ATTR + NON_OP
    v = equity / SHARES
    if detail:
        return v, rows, pv, pv_tv, equity
    return v


def weighted(r=COE):
    return sum(SCEN[s]["p"] * value(s, r) for s in SCEN)


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


def main():
    print("== 2026 年正常化归母净利（亿元） ==")
    for s in SCEN:
        print(f"  {s}: {NP26[s]:.2f}")
    print(f"  上半年正常化 {H1_NORM:.2f}；调整项合计 {sum(ADJ.values()):+.2f}")
    print("== 经调整净现金（亿元） ==")
    print(f"  集团口径 {NET_CASH_GROUP:.2f}；归母口径（×{PARENT_EQ/(PARENT_EQ+MINORITY_EQ):.3f}）{NET_CASH_ATTR:.2f}；非经营资产 {NON_OP:.2f}")
    print("== 三情景（股权成本 9%） ==")
    for s, sc in SCEN.items():
        v, rows, pv, pv_tv, eq = value(s, detail=True)
        gs = growth_path(sc["g"])
        print(f"  {s}: V={v:.2f} 元/股  p={sc['p']}  增量回报={sc['roiic']:.0%}  股权价值={eq:.1f} 亿  终值现值占比={pv_tv/(pv+pv_tv):.0%}")
        print("     增速 2027-2031: " + " ".join(f"{g:+.0%}" for g in sc["g"]) + "；2032-2036: " + " ".join(f"{g:.1%}" for g in gs[5:]))
        print("     年份    归母净利  再投资率  所有者收益  现值")
        for y, npv, b, oe, df in rows:
            print(f"     {y}  {npv:7.2f}  {b:7.0%}  {oe:8.2f}  {oe*df:7.2f}")
        print(f"     终值现值 {pv_tv:.1f} 亿；显性期现值 {pv:.1f} 亿；2031 归母净利 {rows[5][1]:.2f}，2036 归母净利 {rows[-1][1]:.2f}")
    vw = weighted()
    print(f"== 加权 V = {vw:.2f} 元/股；P/V = {PRICE/vw:.2f} ==")
    v_ex = vw * SHARES / (SHARES - REPO_SHARES)
    print(f"  剔除回购专户股份：V = {v_ex:.2f}，P/V = {PRICE/v_ex:.2f}")
    print("== 股权成本敏感性（加权 V） ==")
    for r in (0.08, 0.09, 0.10):
        print(f"  r={r:.0%}: V={weighted(r):.2f}  （熊 {value('bear', r):.2f} / 基 {value('base', r):.2f} / 牛 {value('bull', r):.2f}）")
    irr = solve(lambda r: value("base", r), 0.03, 0.12, PRICE)
    print(f"== 现价隐含回报（基准情景现金流） = {irr:.2%} ==")
    irr_bull = solve(lambda r: value("bull", r), 0.03, 0.15, PRICE)
    print(f"  （牛市情景现金流下的隐含回报 = {irr_bull:.2%}）")
    # 反向 DCF：2027-2036 恒定增速（从 2026 基准正常化净利出发），2037 起 2.5%
    def v_const(g, roiic):
        np26 = NP26["base"]
        np_h2 = np26 - H1_NORM
        pv = np_h2 * (1 - max(g / roiic, B26_FLOOR))
        np_t = np26
        for y in range(2027, 2037):
            np_t *= 1 + g
            g_next = g if y < 2036 else G_TERM
            oe = np_t * (1 - g_next / roiic)
            pv += oe * (1 + COE) ** -((y + 0.5) - VAL_T)
        tv = np_t * (1 + G_TERM) * (1 - G_TERM / roiic) / (COE - G_TERM)
        pv += tv * (1 + COE) ** -((2036 + 0.5) - VAL_T)
        return (pv + NET_CASH_ATTR + NON_OP) / SHARES
    for roiic in (0.18, 0.25):
        g_impl = solve(lambda g: v_const(g, roiic), 0.0, 0.45, PRICE)
        np_2036 = NP26["base"] * (1 + g_impl) ** 10
        print(f"== 反向 DCF（增量回报 {roiic:.0%}）：现价隐含 2027-2036 归母净利年增 {g_impl:.1%}，2036 年归母净利约 {np_2036:.0f} 亿 ==")
    # 永续口径：基准正常化净利、增量回报 18% 下的隐含永续增速
    target = PRICE * SHARES - NET_CASH_ATTR - NON_OP
    f_perp = lambda g: NP26["base"] * (1 - g / 0.18) * (1 + g) / (COE - g)
    g_perp = solve(f_perp, 0.0, 0.0899, target)
    print(f"  现价隐含永续增速 = {g_perp:.2%}（增量回报 18%，起点为 2026 基准正常化归母净利）")
    # 交叉验证
    mcap = PRICE * SHARES
    print("== 交叉验证 ==")
    print(f"  市值 {mcap:.1f} 亿；2026E 正常化 PE {mcap/NP26['base']:.1f}×；基准 2027E PE {mcap/(NP26['base']*1.30):.1f}×")
    print(f"  加权 V 对应 2026E 正常化 PE {vw*SHARES/NP26['base']:.1f}×，对应 PB {vw*SHARES/PARENT_EQ:.2f}×（现价 PB {mcap/PARENT_EQ:.2f}×）")
    ebit26 = 8.1   # 2026E 集团 EBIT：税前约 8.35（集团净利约 7.1/0.85）− 投资与公允价值收益约 0.2 − 非经常补助约 0.25 + 汇兑与利息净额约 0.2
    ev = mcap + MINORITY_EQ - NET_CASH_GROUP
    print(f"  EV/EBIT(2026E) ≈ {ev/ebit26:.0f}×（EV {ev:.0f} 亿，少数股东权益按账面 {MINORITY_EQ} 亿计）")
    print(f"  股息率 0.22%（过去 12 个月 0.17 元/股），无回购；实控人、董事长及高管 2026 年合计减持约 1.1% 股本（约 6.7 亿元）")
    # 分部拆解：现价留给石英电子布的归母价值
    core_np, core_pe = 5.3, 27.5          # 2026 核心业务（石英材料与制品、航空航天纤维等）归母净利估计与倍数
    q_attr_share = 0.60                    # 石英电子布增量利润归母比例（鼎益纱 100%＋中益布 48.11%）
    resid = mcap - core_np * core_pe - NET_CASH_ATTR - NON_OP
    term_pe = (1 - G_TERM / 0.25) * (1 + G_TERM) / (COE - G_TERM)
    disc5 = (1 + COE) ** -5
    need_attr = resid / (term_pe * disc5)
    print(f"  分部：核心业务 {core_np}×{core_pe} = {core_np*core_pe:.0f} 亿；现价留给石英电子布的归母价值 {resid:.0f} 亿")
    print(f"        按 2031 年成熟、终值倍数 {term_pe:.1f}×、5 年折现 {disc5:.2f}，需成熟期归母净利 {need_attr:.0f} 亿，即集团口径 {need_attr/q_attr_share:.0f} 亿")
    print("== 分档价格（V 不变） ==")
    print(f"  明显低估 ≤ {0.75*vw:.1f}；温和低估 {0.75*vw:.1f}～{0.90*vw:.1f}；大致合理 {0.90*vw:.1f}～{1.10*vw:.1f}；偏贵 > {1.10*vw:.1f}")
    # 证伪情景
    print("== 证伪触发后的 V ==")
    cut = 0.6   # 三季报低于预告下限：2026 正常化三档各下调约 0.6 亿
    f1 = sum(SCEN[s]["p"] * value(s, np26=NP26[s] - cut) for s in SCEN)
    f2 = 0.5 * value("bear") + 0.5 * value("base")
    f3 = value("bear")
    f4 = value("bull")
    f5 = 0.95 * vw
    print(f"  F1 三季报单季归母 < 1.55 亿或前三季度经营现金流 < 2.5 亿（2026 正常化下调约 0.6 亿）：{f1:.2f}")
    print(f"  F2 2027 中报石英电子布半年收入 < 2.5 亿或中益半年净利 < 0.8 亿（概率移向熊市 50/50/0）：{f2:.2f}")
    print(f"  F3 2027 年报营收同比 < +10% 且毛利率 < 44%（熊市路径）：{f3:.2f}")
    print(f"  F4 2027 年报石英电子布收入 ≥ 15 亿且归母扣非 ≥ 11 亿（牛市路径）：{f4:.2f}")
    print(f"  F5 子公司再次向董监高或持股平台低价增资、上市公司放弃认缴：{f5:.2f}")


if __name__ == "__main__":
    main()
