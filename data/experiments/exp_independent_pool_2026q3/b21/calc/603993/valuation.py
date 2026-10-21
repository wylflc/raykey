#!/usr/bin/env python3
"""洛阳钼业（603993）独立估值：分部正常化 + 有杠杆口径所有者收益 DCF。

运行：python3 valuation.py
金额单位：亿元人民币（另注明者除外）；价格与 V 为元/股。
估值基准日：2026-06-30 资产负债表；现金流按年中→年末计，最后复利滚动到价格日 2026-10-21。
所有输入写在脚本内，来源见同目录外的正文 companies/603993_洛阳钼业.md。
"""

# ---------------------------------------------------------------- 统一快照
PRICE = 14.15                 # A 股收盘，2026-10-21
SHARES = 213.9431             # 亿股，A+H 全部股份（2026H1 报告第 29 页 21,394,310,176 股）
COE = 0.09
FX = 6.80                     # 美元/人民币，2026-06-30 为 6.811（存货质押折算，H1 第 138 页）
LB_PER_T = 2204.62
DAYS_TO_PRICE_DATE = 113      # 2026-06-30 → 2026-10-21
H_PRICE_HKD = 13.65           # H 股 2026-10-21 收盘（腾讯行情）
HKD_CNY = FX / 7.79           # 联系汇率近似

# ---------------------------------------------------------------- 资产负债（2026-06-30，H1 报告附注）
cash = 425.23                 # 货币资金
restricted = 20.87            # 其他货币资金受限：矿山保证金 1.00 + 借款保证金 7.40 + 质押大额存单 11.50 + 其他 0.98
fin_invest = 3.00 + 10.04 + 35.86   # 交易性金融资产中结构性存款、理财、基金（剔除按公允价值计量的贸易应收 101.39 与“其他”10.59）
cd_current = 5.76 - 2.80      # 一年内到期大额存单，扣质押 2.80
op_reserve = 40.0             # 经营备付：矿山端约 1 个月付现成本
cash_like = cash - restricted + fin_invest + cd_current - op_reserve

debt_items = {
    "短期借款（信用 179.10 + 质押 179.51，多为贸易融资）": 358.61,
    "长期借款（含一年内到期 16.09）": 5.98 + 16.09,
    "宁德时代计息预付款（其他非流动负债 105.40 + 合同负债 10.47）": 105.40 + 10.47,
    "金属流合同负债（非流动 62.85 + 流动 2.79）": 62.85 + 2.79,
    "Gécamines 和解金应付（非流动 9.50 + 一年内 7.44）": 9.50 + 7.44,
    "巴西金矿或有对价（交易性金融负债）": 2.70,
    "设定受益计划等长期应付职工薪酬": 6.10,
    "预计负债（复垦 27.94 + 巴西诉讼 4.40）": 32.34,
    "已宣派中期股息 20.32 + 应付股利 0.34": 20.32 + 0.34,
    "应交税费高于 2025 年末的部分（112.25 − 82.35，上半年高价利润的应付税款）": 112.25 - 82.35,
}
debt_like = sum(debt_items.values())
NET_CASH_ADJ = cash_like - debt_like          # 无杠杆口径经调整净现金（不含可转债）
CB_FACE = 12.0 * FX                           # H 股可换股债券面值 12 亿美元，2027-01-24 到期，零息
CB_CONV_SHARES = 3.39554265                   # 亿股，按 27.55 港元悉数转换（H1 第 71 页）
LEASE = 1.05 + 1.62                           # 租赁负债：列示不扣（所有者收益以净利润为起点）
INT_RATE = 0.050                              # 有息负债实际平均利率：2026H1 利息支出 14.72 亿×2 / 平均计息负债约 583 亿
INT_TAX = 0.22                                # 利息抵税的混合税率（IXM/香港低税、刚果（金）30%）

# 非经营资产
other_fin_assets = 33.80 * 0.9 + 1.07         # 其他非流动金融资产（私募基金、资管计划等）打九折 + 其他权益工具投资
COBALT_STOCK_KT = 168.397 - 10.0              # 2026-06-30 钴库存 168,397 吨，扣 1 万吨正常周转

# ---------------------------------------------------------------- 情景假设（2026 年美元价，正常化）
SCN = {
    "bear": dict(p=0.25, cu=9000, cu_cost=4900, co=12.0, co_pay=0.65, co_kt=40, mo=19.0, w=26.0,
                 china_cost=52.0, au=2700, au_cost=2750, nb=40.0, p_gp=4.0, ixm=12.0, eq=3.0,
                 drc_tax=0.33, kfm2_delay=1, odin=(0, 0, 0, 0, 100, 200),
                 stock=dict(px=6.5, start=2031, years=15)),
    "base": dict(p=0.50, cu=11000, cu_cost=4700, co=16.0, co_pay=0.85, co_kt=30, mo=25.0, w=40.0,
                 china_cost=50.0, au=3500, au_cost=2650, nb=45.0, p_gp=8.0, ixm=21.0, eq=7.0,
                 drc_tax=0.30, kfm2_delay=0, odin=(0, 0, 0, 120, 250, 330),
                 stock=dict(px=11.0, start=2029, years=10)),
    "bull": dict(p=0.25, cu=13000, cu_cost=4500, co=21.0, co_pay=0.92, co_kt=33, mo=31.0, w=60.0,
                 china_cost=50.0, au=4300, au_cost=2550, nb=50.0, p_gp=12.0, ixm=30.0, eq=11.0,
                 drc_tax=0.30, kfm2_delay=0, odin=(0, 0, 0, 180, 380, 480),
                 stock=dict(px=16.0, start=2028, years=6)),
}

# 年度（2026 正常化年 + 2027–2031）销量：铜千吨、巴西金千盎司；Odin 千盎司在情景里
YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
CU_KT = {0: [780, 800, 870, 900, 905, 910],          # KFM 二期 2027 年建成、2028 年起贡献约 10 万吨
         1: [780, 790, 830, 880, 900, 905]}          # 熊市：推迟一年
BR_AU_KOZ = 225                                      # 巴西四座金矿年产约 7 吨
CU_REAL = 0.97        # 实现价/LME（2026H1：12,693/13,084）
CU_ROY = 0.04         # 铜矿权益金 3.5% + 其他
CO_ROY = 0.105        # 钴（战略矿产）权益金 10% + 其他
CO_COST = 4.0         # 美元/磅，钴增量与分摊成本（2025 年约 2.8，2026H1 约 6.2）
MO_KT, W_KT = 13.5, 7.0
MO_REV_PER_FEMO = 58.07 / 29.08   # 钼：每吨钼收入（万元）/钼铁价（万元），2026H1 3,932.6 百万元 / 6,772 吨
W_REV_PER_APT = 124.07 / 103.10   # 钨：每吨钨收入/APT 价，2026H1 3,194.8 百万元 / 2,575 吨
CHINA_ROY = 0.09
CHINA_TAX, CHINA_MIN = 0.20, 0.03
NB_KT, NB_COST = 10.5, 25.1       # 铌：吨、美元/公斤（2026H1 销售成本 954.3 百万元 / 5,583 吨）
BR_ROY, BR_TAX = 0.03, 0.25
P_REV = 42.0                      # 磷肥年收入（权益金基数）
ODIN_COST, ODIN_ROY, ODIN_TAX = 1700, 0.05, 0.36
IXM_TAX = 0.18
OVERHEAD = 30.0                   # 管理、研发、销售费用（不含 IXM 自身费用）
OVH_TAX = 0.25
DRC_MIN = 0.16                    # 少数股东占刚果（金）经济净利：2025 年 16.3%、2026H1 14.8%（集团内定价与股东借款使实际低于名义 20%/28.75%）
NET_FIN_2026 = 14.5               # 2026 年净财务费用（利息支出约 29.5 − 利息收入约 18 + 其他约 3，不含汇兑）

# 增长再投资（归母口径，亿元）：KFM 二期剩余约 7 亿美元×71.25%、Odin 金矿约 16 亿美元、其他扩产
GROWTH_CAPEX = {"bear": [12, 55, 50, 40, 25, 20],
                "base": [12, 60, 50, 35, 20, 20],
                "bull": [12, 62, 52, 38, 22, 22]}
TERM_G = 0.020
TERM_ROIC = 0.12


def segments(s, year_idx):
    """返回某年分部税后利润（归母前、含少数股东）与少数股东损益，及分部明细。"""
    cu_kt = CU_KT[s["kfm2_delay"]][year_idx]
    cu_rev_usd = cu_kt * 1e3 * s["cu"] * CU_REAL
    cu_pt = cu_rev_usd - cu_kt * 1e3 * s["cu_cost"] - CU_ROY * cu_rev_usd
    co_lb = s["co_kt"] * 1e3 * LB_PER_T
    co_rev_usd = co_lb * s["co"] * s["co_pay"]
    co_pt = co_rev_usd - co_lb * CO_COST - CO_ROY * co_rev_usd
    drc_pt = (cu_pt + co_pt) * FX / 1e8
    drc_np = drc_pt * (1 - s["drc_tax"])
    drc_min = drc_np * DRC_MIN

    china_rev = MO_KT * 1e3 * MO_REV_PER_FEMO * s["mo"] / 1e4 + W_KT * 1e3 * W_REV_PER_APT * s["w"] / 1e4
    china_pt = china_rev * (1 - CHINA_ROY) - s["china_cost"]
    china_np = china_pt * (1 - CHINA_TAX)
    china_min = china_np * CHINA_MIN

    nb_rev = NB_KT * 1e3 * s["nb"] * 1e3 * FX / 1e8
    nb_gp = NB_KT * 1e3 * (s["nb"] - NB_COST) * 1e3 * FX / 1e8
    au_rev = BR_AU_KOZ * 1e3 * s["au"] * FX / 1e8
    au_gp = BR_AU_KOZ * 1e3 * (s["au"] - s["au_cost"]) * FX / 1e8
    br_pt = nb_gp + s["p_gp"] + au_gp - BR_ROY * (nb_rev + P_REV) - 0.015 * au_rev
    br_np = br_pt * (1 - BR_TAX)

    odin_koz = s["odin"][year_idx]
    odin_rev = odin_koz * 1e3 * s["au"] * FX / 1e8
    odin_np = (odin_koz * 1e3 * (s["au"] - ODIN_COST) * FX / 1e8 - ODIN_ROY * odin_rev) * (1 - ODIN_TAX)

    ixm_np = s["ixm"] * (1 - IXM_TAX)       # 息前
    eq = s["eq"]
    ovh = -OVERHEAD * (1 - OVH_TAX)
    nopat = drc_np + china_np + br_np + odin_np + ixm_np + eq + ovh
    minority = drc_min + china_min
    detail = dict(cu_kt=cu_kt, drc_pt=drc_pt, drc_np=drc_np, china_rev=china_rev, china_pt=china_pt,
                  br_pt=br_pt, odin_np=odin_np, ixm_np=ixm_np, eq=eq, ovh=ovh, minority=minority)
    return nopat - minority, detail          # 归母经营所有者收益（息前）


def stockpile_value(s, coe=COE):
    st = s["stock"]
    lbs_total = COBALT_STOCK_KT * 1e3 * LB_PER_T
    lbs_y = lbs_total / st["years"]
    book = 3.4                                # 美元/磅，库存账面成本（已付现，计税成本）
    pv = 0.0
    for k in range(st["years"]):
        year = st["start"] + k
        t = (year - 2026) + 0.0               # 年中销售，距 2026-06-30 整年数
        net = lbs_y * (st["px"] * (1 - CO_ROY) - 0.5)
        tax = max(0.0, lbs_y * (st["px"] * (1 - CO_ROY) - 0.5 - book)) * 0.30
        cash_ = (net - tax) * (1 - DRC_MIN - 0.03)   # 库存在 TFM/KFM，少数股东比例略高于利润口径
        pv += cash_ * FX / 1e8 / (1 + coe) ** t
    return pv


def value(name, coe=COE, levered=True, cb_mode="debt"):
    s = SCN[name]
    oe = [segments(s, i)[0] for i in range(len(YEARS))]
    capex = GROWTH_CAPEX[name]
    pv = 0.0
    flows = []
    # 2026H2：半年正常化所有者收益减半年增长开支，t=0.5
    f = 0.5 * oe[0] - capex[0]
    flows.append((0.5, f))
    for i, y in enumerate(YEARS[1:], start=1):
        t = i + 0.5                            # 2027 年现金流在 2027 年末，距 2026-06-30 1.5 年
        flows.append((t, oe[i] - capex[i]))
    rr = TERM_G / TERM_ROIC
    tv = oe[-1] * (1 + TERM_G) * (1 - rr) / (coe - TERM_G)
    flows.append((YEARS[-1] - 2026 + 0.5, tv))
    pv_ops = sum(fl / (1 + coe) ** t for t, fl in flows)
    nd = -NET_CASH_ADJ
    if levered and nd > 0:
        debt_cost = nd * INT_RATE * (1 - INT_TAX) / coe     # 净负债按现规模滚动，税后利息的现值
        fin = -debt_cost
    else:
        fin = NET_CASH_ADJ
    stock = stockpile_value(s, coe)
    nonop = other_fin_assets + stock
    equity = pv_ops + fin + nonop
    roll = (1 + coe) ** (DAYS_TO_PRICE_DATE / 365)
    v_debt = (equity - CB_FACE) * roll / SHARES
    v_conv = equity * roll / (SHARES + CB_CONV_SHARES)
    v = min(v_debt, v_conv) if cb_mode == "min" else (v_debt if cb_mode == "debt" else v_conv)
    term_share = tv / (1 + coe) ** flows[-1][0] / pv_ops
    return dict(v=v, v_debt=v_debt, v_conv=v_conv, pv_ops=pv_ops, fin=fin, nonop=nonop,
                stock=stock, oe=oe, term_share=term_share, equity=equity, flows=flows)


def normalized_np_2026(name):
    """2026 年正常化归母净利（含净利息、剔除汇兑与一次性）。"""
    s = SCN[name]
    oe0, d = segments(s, 0)
    return oe0 - NET_FIN_2026 * (1 - INT_TAX)


def weighted(coe=COE, levered=True, cb_mode="min"):
    return sum(SCN[n]["p"] * value(n, coe, levered, cb_mode)["v"] for n in SCN)


def implied_irr():
    """基准情景现金流（含终值、净负债与非经营资产）使现值等于现价的折现率。"""
    lo, hi = 0.03, 0.30
    target = PRICE
    for _ in range(100):
        mid = (lo + hi) / 2
        v = value("base", coe=mid, levered=True, cb_mode="min")["v"]
        if v > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf():
    """现价隐含：以基准 2026 正常化归母经营所有者收益为起点，10 年增速 g10（之后 2%），9% 折现。"""
    base0 = segments(SCN["base"], 0)[0]
    nd = -NET_CASH_ADJ
    fin = -nd * INT_RATE * (1 - INT_TAX) / COE
    nonop = other_fin_assets + stockpile_value(SCN["base"])
    roll = (1 + COE) ** (DAYS_TO_PRICE_DATE / 365)
    target_ops = PRICE * SHARES / roll + CB_FACE - fin - nonop

    def pv_for(g):
        pv, oe = 0.0, base0
        rr10 = min(0.9, g / 0.20) if g > 0 else 0.0     # 增长需要再投资：按增量回报 20% 计
        for k in range(1, 11):
            oe *= 1 + g
            pv += oe * (1 - rr10) / (1 + COE) ** (k + 0.5)
        tv = oe * (1 + TERM_G) * (1 - TERM_G / TERM_ROIC) / (COE - TERM_G)
        return pv + tv / (1 + COE) ** 10.5
    lo, hi = -0.2, 0.3
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv_for(mid) < target_ops:
            lo = mid
        else:
            hi = mid
    g10 = (lo + hi) / 2
    # 永续增速口径：起点所有者收益×(1−g/ROIC)/(r−g) = 目标
    lo, hi = -0.10, 0.085
    for _ in range(200):
        mid = (lo + hi) / 2
        pv = base0 * (1 + mid) * (1 - max(mid, 0) / TERM_ROIC) / (COE - mid) / (1 + COE) ** 0.5
        if pv < target_ops:
            lo = mid
        else:
            hi = mid
    return g10, (lo + hi) / 2, base0, target_ops


if __name__ == "__main__":
    print("== 经调整净现金（无杠杆口径，2026-06-30，不含可转债）")
    print(f"  现金类 {cash - restricted + fin_invest + cd_current:.2f}（货币资金 {cash} − 受限 {restricted} + 理财/基金 {fin_invest:.2f} + 存单 {cd_current:.2f}），经营备付 −{op_reserve}")
    for k, v in debt_items.items():
        print(f"  − {k}: {v:.2f}")
    print(f"  类债务合计 {debt_like:.2f}；net_cash_adj = {NET_CASH_ADJ:.2f}；可转债面值 {CB_FACE:.2f}（另扣）；租赁负债 {LEASE:.2f}（列示不扣）")
    nd = -NET_CASH_ADJ
    print(f"  有杠杆口径：净负债 {nd:.2f} × {INT_RATE:.1%} × (1−{INT_TAX:.0%}) / 9% = 税后利息现值 {nd*INT_RATE*(1-INT_TAX)/COE:.2f}")
    print(f"  非经营资产：其他金融资产 {other_fin_assets:.2f}；钴库存超额价值 熊/基/牛 = "
          + " / ".join(f"{stockpile_value(SCN[n]):.1f}" for n in SCN))
    print()
    for n in SCN:
        s = SCN[n]
        _, d = segments(s, 0)
        print(f"== {n}（p={s['p']}）2026 正常化分部（亿元）：刚果（金）税前 {d['drc_pt']:.1f}、税后 {d['drc_np']:.1f}；"
              f"中国钼钨收入 {d['china_rev']:.1f}、税前 {d['china_pt']:.1f}；巴西税前 {d['br_pt']:.1f}；IXM 税后息前 {d['ixm_np']:.1f}；"
              f"联合营 {d['eq']:.1f}；费用税后 {d['ovh']:.1f}；少数股东 −{d['minority']:.1f}")
        r = value(n, cb_mode="min")
        print(f"  归母经营所有者收益 2026–2031: " + ", ".join(f"{x:.1f}" for x in r["oe"]))
        g = [r["oe"][i] / r["oe"][i - 1] - 1 for i in range(2, len(r["oe"]))]
        print(f"  增速 2028–2031: " + ", ".join(f"{x:.1%}" for x in g)
              + f"；2027 较 2026 {r['oe'][1]/r['oe'][0]-1:.1%}")
        print(f"  经营现值 {r['pv_ops']:.1f}（终值占 {r['term_share']:.0%}）+ 财务项 {r['fin']:.1f} + 非经营 {r['nonop']:.1f}"
              f" = 股权 {r['equity']:.1f}；V(扣可转债) {r['v_debt']:.2f}，V(全部转股) {r['v_conv']:.2f} → 取低 {r['v']:.2f}")
        print(f"  2026 正常化归母净利（含净利息）{normalized_np_2026(n):.1f}")
        unlev = value(n, levered=False, cb_mode="min")["v"]
        print(f"  无杠杆口径（全额扣经调整净负债）V = {unlev:.2f}")
        print()
    vw = weighted()
    print(f"== 加权 V（有杠杆口径，可转债取低）= {vw:.2f}，P/V = {PRICE / vw:.3f}")
    vw_unlev = weighted(levered=False)
    print(f"   无杠杆口径加权 V = {vw_unlev:.2f}，P/V = {PRICE / vw_unlev:.3f}")
    v8, v10 = weighted(coe=0.08), weighted(coe=0.10)
    print(f"   股权成本 8%：V = {v8:.2f}；10%：V = {v10:.2f}")
    print(f"   现价隐含回报（基准情景）= {implied_irr():.2%}")
    g10, gperp, base0, tgt = reverse_dcf()
    print(f"   反向 DCF：起点归母经营所有者收益 {base0:.1f} 亿，现价需经营现值 {tgt:.1f} 亿 → 10 年增速 {g10:.2%}（之后 2%），或永续增速 {gperp:.2%}")
    print(f"   分档价格（V 不变）：≤0.75 → {0.75*vw:.2f}；0.90 → {0.90*vw:.2f}；1.10 → {1.10*vw:.2f}")
    h_cny = H_PRICE_HKD * HKD_CNY
    print(f"   H 股 {H_PRICE_HKD} 港元 ≈ {h_cny:.2f} 元，较 A 股折价 {1 - h_cny / PRICE:.1%}；按 H 股价 P/V = {h_cny / vw:.3f}")
    print(f"   无回购专户股份，剔除口径 V 相同。")

    # ------------------------------------------------------------ 校准：模型机制套用实际价量能否复现报表利润
    print()
    print("== 校准（亿元）")
    def calib(cu_kt, cu_real, cu_cogs, fx, co_gp, co_rev, china_gp, china_rev, br_gp, br_rev_nbp, au_rev,
              ixm_ebit, eq, ovh, net_int, fx_gain, unreal, actual, label):
        cu_pt = cu_kt * 1e3 * (cu_real - cu_cogs - CU_ROY * cu_real) * fx / 1e8
        drc_pt = cu_pt + co_gp - CO_ROY * co_rev
        drc_np = drc_pt * 0.70
        china_np = (china_gp - CHINA_ROY * china_rev) * (1 - CHINA_TAX)
        br_np = (br_gp - BR_ROY * br_rev_nbp - 0.015 * au_rev) * (1 - BR_TAX)
        ixm_np = (ixm_ebit) * (1 - IXM_TAX)
        other = (ovh - net_int + fx_gain) * (1 - 0.22) + unreal * 0.70
        np_total = drc_np + china_np + br_np + ixm_np + eq + other
        mino = drc_np * DRC_MIN + china_np * CHINA_MIN
        print(f"  {label}: 模型归母 {np_total - mino:.1f} vs 报表 {actual:.2f}（刚果（金）税前 {drc_pt:.1f}，少数股东 {mino:.1f}，"
              f"汇兑 {fx_gain:+.2f}，分部间未实现利润 {unreal:+.2f}）")
    # 2026H1：铜 376,164 吨，铜收入 325.18 亿、成本 120.71 亿；IXM 期现合并毛利 29.87−1.51，扣自身费用约 5
    calib(376.164, 325.18e8 / 376164 / 6.811, 120.71e8 / 376164 / 6.811, 6.811, 26.26, 31.58, 43.12, 71.27,
          21.79, 15.55 + 21.91, 30.17, 29.87 - 1.51 - 5.0, 6.87, -(19.91 - 5.0), 14.72 - 9.02 + 0.79, -10.49, -15.67,
          161.52, "2026H1")
    # 2025：铜 730,176 吨，收入 550.96 亿、毛利率 55.2%；钴毛利 61.71×63.6%；IXM 国际准则毛利率 2.11%；分部间抵销毛利 −33.3
    calib(730.176, 550.96e8 / 730176 / 7.18, 550.96e8 * (1 - 0.552) / 730176 / 7.18, 7.18, 61.71 * 0.636, 61.71,
          41.19, 87.53, 26.38, 36.25 + 40.68, 0.0, 0.0211 * 1800.79 - 10.0, 7.5, -(34.0 - 10.0),
          26.31 - 16.44 + 4.40, 9.14, -33.3, 203.39, "2025")

    # ------------------------------------------------------------ 交叉验证
    print()
    print("== 交叉验证")
    mcap = PRICE * SHARES
    _, d = segments(SCN["base"], 0)
    ebit_cons = d["drc_pt"] + d["china_pt"] + d["br_pt"] + SCN["base"]["ixm"] + SCN["base"]["eq"] - OVERHEAD
    ebit_attr = ebit_cons - d["drc_pt"] * DRC_MIN - d["china_pt"] * CHINA_MIN
    ev_attr = mcap - NET_CASH_ADJ + CB_FACE - (other_fin_assets + stockpile_value(SCN["base"]))
    print(f"  市值 {mcap:.1f}；归母口径 EV {ev_attr:.1f}；基准正常化 EBIT 合并 {ebit_cons:.1f}、归母 {ebit_attr:.1f} → EV/EBIT {ev_attr/ebit_attr:.1f}×")
    print(f"  市值/基准 2026 正常化归母净利 {mcap / normalized_np_2026('base'):.1f}×；市值/TTM 归母 278.20 = {mcap/278.20:.1f}×；PB {mcap/899.63:.2f}×")
    hist = {2017: (6.88, 43.1985, 27.28, 381.57), 2018: (3.76, 43.1985, 46.36, 409.49), 2019: (4.36, 43.1985, 18.57, 408.03),
            2020: (6.25, 43.1985, 23.29, 388.92), 2021: (5.58, 43.1985, 51.06, 398.45), 2022: (4.55, 43.1985, 60.67, 516.99),
            2023: (5.20, 43.1985, 82.50, 595.40), 2024: (6.65, 43.1985, 135.32, 710.23), 2025: (20.00, 42.7886, 203.39, 824.35)}
    row = []
    for y, (px, cap_yi_yuan, npy, eqy) in hist.items():
        mc = px * cap_yi_yuan / 0.2          # 资产负债表股本（亿元）÷ 每股面值 0.2 元 = 股数（亿股）
        row.append(f"{y}: PE {mc/npy:.1f} PB {mc/eqy:.2f}")
    print("  历史（年末未复权收盘×股数，股数=股本/0.2）：" + "；".join(row))
    print(f"  股息率（近 12 个月 0.381 元）{0.381/PRICE:.2%}；按基准正常化归母净利 35% 分红 {0.35*normalized_np_2026('base')/mcap:.2%}")

    # ------------------------------------------------------------ 敏感性（加权 V）
    print()
    print("== 敏感性（加权 V，元/股）")
    import copy
    base_scn = copy.deepcopy(SCN)
    def wv_with(mod):
        global SCN
        SCN = copy.deepcopy(base_scn)
        for n in SCN:
            mod(SCN[n])
        v = weighted()
        SCN = copy.deepcopy(base_scn)
        return v
    print(f"  铜价各情景 −1,000 美元：{wv_with(lambda s: s.update(cu=s['cu'] - 1000)):.2f}；+1,000：{wv_with(lambda s: s.update(cu=s['cu'] + 1000)):.2f}")
    print(f"  钴价各情景 −5 美元/磅：{wv_with(lambda s: s.update(co=s['co'] - 5)):.2f}；+5：{wv_with(lambda s: s.update(co=s['co'] + 5)):.2f}")
    print(f"  铜单位成本各情景 +500 美元：{wv_with(lambda s: s.update(cu_cost=s['cu_cost'] + 500)):.2f}")
    print(f"  刚果（金）所得税率各情景 +5 个百分点：{wv_with(lambda s: s.update(drc_tax=s['drc_tax'] + 0.05)):.2f}")
    print(f"  钴库存不计价值：{wv_with(lambda s: s['stock'].update(px=0.5/(1-CO_ROY))):.2f}")

    # ------------------------------------------------------------ 增长路径（基准）
    print()
    r = value("base", cb_mode="min")
    oe, cap = r["oe"], GROWTH_CAPEX["base"]
    growth = [oe[i] / oe[i - 1] - 1 for i in range(1, len(oe))]
    rr = sum(cap[1:]) / sum(oe[1:])
    inc = (oe[-1] - oe[0]) / sum(cap)
    print("== 基准增长路径：2027–2031 所有者收益增速 " + ", ".join(f"{g:.1%}" for g in growth)
          + f"；终值增速 {TERM_G:.1%}（再投资率 {TERM_G/TERM_ROIC:.1%}，增量回报 {TERM_ROIC:.0%}）")
    print(f"   2027–2031 增长开支合计 {sum(cap[1:]):.0f} 亿，占同期所有者收益 {rr:.1%}；2026H2–2031 增量所有者收益 {oe[-1]-oe[0]:.1f} 亿 / 增长开支 {sum(cap):.0f} 亿 = 增量回报 {inc:.1%}")

    # ------------------------------------------------------------ 现价隐含铜价（各情景同步平移，其余不变）
    lo, hi = -4000.0, 4000.0
    for _ in range(80):
        mid = (lo + hi) / 2
        v = wv_with(lambda s, m=mid: s.update(cu=s["cu"] + m))
        if v > PRICE:
            hi = mid
        else:
            lo = mid
    shift = (lo + hi) / 2
    w_cu = sum(SCN[n]["p"] * SCN[n]["cu"] for n in SCN)
    print()
    print(f"== 现价隐含：各情景铜价同步平移 {shift:+.0f} 美元/吨，概率加权铜价 {w_cu + shift:,.0f}（基准加权 {w_cu:,.0f}）")

    # ------------------------------------------------------------ 证伪条件触发后的 V
    print()
    print("== 证伪条件触发后的独立 V（元/股）")
    def v_weights(pb, pm, pu, **kw):
        vals = {n: value(n, cb_mode="min")["v"] for n in SCN}
        return pb * vals["bear"] + pm * vals["base"] + pu * vals["bull"]
    f1 = v_weights(0.5, 0.5, 0.0)
    print(f"  F1 铜：2027 年 LME 均价 < 9,500 → 情景权重改为 熊 0.5／基 0.5／牛 0：{f1:.2f}")
    def f2mod(s):
        s.update(co_kt=max(15, s["co_kt"] - 10), co=s["co"] - 3)
        s["stock"].update(px=max(3.0, s["stock"]["px"] - 3), start=s["stock"]["start"] + 2)
    f2 = wv_with(f2mod)
    print(f"  F2 钴：年销量各情景 −1 万吨、钴价 −3 美元/磅、库存变现推迟 2 年且 −3 美元/磅：{f2:.2f}")
    def f3mod(s):
        s.update(kfm2_delay=1, odin=tuple(int(x * 0.5) for x in s["odin"]))
    f3 = wv_with(f3mod)
    print(f"  F3 增量：KFM 二期推迟一年、Odin 产量减半：{f3:.2f}")
    f4 = wv_with(lambda s: s.update(cu_cost=s["cu_cost"] + 500))
    print(f"  F4 成本：铜单位销售成本各情景 +500 美元/吨：{f4:.2f}")
    f5 = wv_with(lambda s: s.update(drc_tax=s["drc_tax"] + 0.05))
    print(f"  F5 刚果（金）财税：实际税负 +5 个百分点：{f5:.2f}")

    # ------------------------------------------------------------ 2026H2 现价超额利润（不计入 V，三季报后核对）
    win_cu = 3000 * CU_REAL * (1 - CU_ROY) * 395e3 * (1 - 0.30) * (1 - DRC_MIN) * FX / 1e8
    win_w = 20 * W_REV_PER_APT * 3.5e3 / 1e4 * (1 - CHINA_ROY) * (1 - CHINA_TAX)
    win_mo = 8 * MO_REV_PER_FEMO * 6.75e3 / 1e4 * (1 - CHINA_ROY) * (1 - CHINA_TAX)
    win_au = 500 * 112e3 * FX / 1e8 * (1 - BR_TAX)
    print()
    print(f"== 2026H2 现价相对基准正常化的超额归母利润（估计，不计入 V）：铜 {win_cu:.1f} + 钨 {win_w:.1f} + 钼 {win_mo:.1f} + 金 {win_au:.1f}"
          f" = {win_cu + win_w + win_mo + win_au:.1f} 亿，约 {(win_cu + win_w + win_mo + win_au) / SHARES:.2f} 元/股")

    # ------------------------------------------------------------ 汇总（与 json 一致）
    print()
    vals = {n: value(n, cb_mode="min")["v"] for n in SCN}
    print("== 汇总")
    print("  V 熊/基/牛 = " + " / ".join(f"{vals[n]:.2f}" for n in SCN) + f"；加权 {weighted():.2f}；P/V {PRICE/weighted():.3f}")
    print("  2026 正常化归母净利 熊/基/牛 = " + " / ".join(f"{normalized_np_2026(n):.1f}" for n in SCN))
    print(f"  net_cash_adj_yi = {NET_CASH_ADJ:.2f}；non_operating_assets_yi（基准）= {other_fin_assets + stockpile_value(SCN['base']):.2f}")
    print(f"  V@8% {weighted(coe=0.08):.2f}；V@10% {weighted(coe=0.10):.2f}；隐含回报 {implied_irr():.4f}")
