#!/usr/bin/env python3
"""000933 神火股份 独立估值（OI-291 b06，价格日 2026-10-20）。

运行：python3 valuation.py
输出：三情景正常化归母净利、所有者收益、每股 V、加权 V、P/V、8%/10% 下的 V、
隐含回报、反向 DCF（隐含长期沪铝价、隐含永续增速、隐含 10 年增速）与证伪触发后的 V。

金额单位：亿元；价格：元/吨（含税）；产量：万吨；每股：元。
口径：电解铝分部按“吨铝税前利润 = (沪铝 - 1.93 x 氧化铝)/1.13 - K”计算，
K 为吨铝其他全部成本（电力、阳极、人工、折旧、费用，净额含自备炭素厂利润），
用 2025 年报与 2026 中报子公司、分部数据标定（见正文第二节）。
"""

PRICE = 25.69               # 2026-10-20 收盘，腾讯行情
SHARES = 22.4900            # 亿股，腾讯行情总股本，含回购专户 1,542.036 万股
TREASURY = 0.15420360       # 回购专户股份（buyback_20251203 第2页），拟用于股权激励，不注销
COE = 0.09

VAT = 1.13
ALUMINA_PER_T = 1.93        # 吨铝氧化铝单耗
TAX_X, TAX_Y = 0.25, 0.15   # 新疆煤电/新疆炭素约 25%，云南神火约 15%（2025 年报第34页营业利润与净利倒算）
TAX_COAL, TAX_FOIL, TAX_OTHER = 0.25, 0.15, 0.25
YUNNAN_PARENT = 0.5825      # 云南神火持股（2025 年报第170页），少数股东 41.75%
COAL_PARENT = 0.97          # 兴隆公司 82% 等少数股东
TRADE_PARENT = 0.90         # 上海国贸 64.52%（注销中）
DA_PARENT = 19.0            # 归母口径折旧摊销（2025 合并 21.50，扣云南少数约 2.1、裕中约 0.4）
MAINT_RATIO = 0.90          # 维持性资本开支 = 90% 折旧（2021-2025 年均购建 10.8 亿，低于折旧）
OE_UPLIFT = DA_PARENT * (1 - MAINT_RATIO)
FADE_2027 = 0.20            # 2027 年保留现行超额收益的比例（其余回到正常化水平）

# ---- 2026 年实际（2026Q3_report 第2-4、10-12页；2026Q1_report；2026H1_report） ----
NP_9M_2026 = 74.87          # 前三季度归母净利
IMPAIR_Q3_PARENT = 4.13 * 0.5016   # 崔岗井田减值 4.13 亿（新密超化，集团权益 50.16%）
NP_9M_2026_EX = NP_9M_2026 + IMPAIR_Q3_PARENT

# ---- 资产负债（2026-09-30，2026Q3_report 第7-10页；附注取 2026H1） ----
CASH = 148.52
CD_CURRENT = 4.25           # 一年内到期的非流动资产（定期存单）
PLEDGED_TD = 4.00           # 其他流动资产中的一年期质押定期存款（2026H1 第94、109页，三季度沿用）
FROZEN = 0.40               # 冻结款项（2026H1 第128页 0.39）
RECLAMATION = 12.17 + 0.65  # 预计负债（复垦弃置为主）+ 一年内到期预计负债；矿山环境治理基金约 7.6 已含在货币资金
OPER_RESERVE = 12.0         # 经营备付，约 TTM 营收 2.5%
DIV_PAYABLE = 1.35          # 应付股利（子公司应付少数股东）
DEBT = 93.40 + 16.63 + (11.10 - 0.65) + 0.08   # 短借+长借+一年内到期非流动负债（扣其中预计负债 0.65）+租赁负债
OTHER_DEBT_LIKE = 0.99 + 0.65   # 收购子公司少数股权交易款、整合小煤矿股权转让款（2026H1 第111页、2025 年报第144页）
NET_CASH_ADJ = (CASH + CD_CURRENT + PLEDGED_TD - FROZEN - RECLAMATION - OPER_RESERVE
                - DIV_PAYABLE - DEBT - OTHER_DEBT_LIKE)

# 少数股东应占云南神火净现金：H1 净流动资产 32.60（2026H1 第133页）+ Q3 净利约 17 + 折旧 1.2 - 购建 0.3，
# 扣经营营运资金约 3，三季度末约 47（估计，三季报无子公司数据）
YUNNAN_NET_CASH = 47.0
MINORITY_CASH_CLAIM = (1 - YUNNAN_PARENT) * YUNNAN_NET_CASH

OTHER_EQUITY_INV = 6.67 * 0.8   # 其他权益工具投资（开曼铝业三门峡 1.875% 等）打八折
# 裕中煤业（51%）按隔离处理：经营不计，母公司债权 29.69 亿（已计提 11.16）按回收额计
YUZHONG_RECOVERY = {"bear": 0.0, "base": 5.0, "bull": 9.0}
CONTINGENT = {"bear": -5.0, "base": 0.0, "bull": 0.0}   # 熊市：裕中诉讼外溢、担保或补资

SCEN = {
    "bear": dict(p=0.30, al=19500, alumina=3300, kx=8000, ky=8900, vx=80, vy=81,
                 coal_vol=680, coal_price=740, coal_cost=725, foil=0.3, trade=0.5, hq=-3.0,
                 assoc=2.0, net_int=-1.0, g=0.005, roic=0.10, q4=21.0),
    "base": dict(p=0.50, al=21500, alumina=3000, kx=7500, ky=8300, vx=80, vy=89.5,
                 coal_vol=690, coal_price=860, coal_cost=718, foil=2.0, trade=1.0, hq=-2.5,
                 assoc=2.5, net_int=-0.8, g=0.015, roic=0.15, q4=24.5),
    "bull": dict(p=0.20, al=23500, alumina=2750, kx=7300, ky=8000, vx=80, vy=90,
                 coal_vol=700, coal_price=980, coal_cost=730, foil=3.5, trade=1.5, hq=-2.0,
                 assoc=3.0, net_int=-0.5, g=0.020, roic=0.18, q4=27.0),
}
ORDER = ("bear", "base", "bull")
T_Q4 = 0.2                              # 2026Q4 现金流距价格日约 0.2 年
T_YEARS = [1.2, 2.2, 3.2, 4.2, 5.2]     # 2027-2031 年末
YEARS = [2027, 2028, 2029, 2030, 2031]


def spread_ex_vat(al, alumina):
    return (al - ALUMINA_PER_T * alumina) / VAT


def normalized(s):
    """正常化（以今日资产规模、长期价格计）的归母净利分解。"""
    sp = spread_ex_vat(s["al"], s["alumina"])
    x_pre = (sp - s["kx"]) * s["vx"] / 1e4          # 亿元
    y_pre = (sp - s["ky"]) * s["vy"] / 1e4
    x_np = x_pre * (1 - TAX_X)
    y_np = y_pre * (1 - TAX_Y)
    al_parent = x_np + y_np * YUNNAN_PARENT
    coal_pre = (s["coal_price"] - s["coal_cost"]) * s["coal_vol"] / 1e4
    coal = coal_pre * (1 - TAX_COAL) * COAL_PARENT
    foil = s["foil"] * (1 - TAX_FOIL)
    trade = s["trade"] * (1 - TAX_OTHER) * TRADE_PARENT
    hq = s["hq"] * (1 - TAX_OTHER)
    op_np = al_parent + coal + foil + trade + hq + s["assoc"]
    ni = s["net_int"] * (1 - TAX_OTHER)
    return dict(spread=sp, x_pre=x_pre, y_pre=y_pre, al_parent=al_parent, y_minority=y_np * (1 - YUNNAN_PARENT),
                coal_pre=coal_pre, coal=coal, foil=foil, trade=trade, hq=hq, assoc=s["assoc"],
                op_np=op_np, net_int=ni, np=op_np + ni)


def oe_norm(s):
    return normalized(s)["op_np"] + OE_UPLIFT


def oe_runrate(s):
    """2026E 归母净利（前三季度剔除减值 + 情景 Q4）换算的所有者收益。"""
    np26 = NP_9M_2026_EX + s["q4"]
    return np26 - normalized(s)["net_int"] + OE_UPLIFT


def oe_path(s, oe0=None, g=None):
    oe0 = oe_norm(s) if oe0 is None else oe0
    g = s["g"] if g is None else g
    first = oe0 + FADE_2027 * (oe_runrate(s) - oe0)
    path = [first] + [oe0 * (1 + g) ** k for k in range(1, 5)]
    return path


def value_total(s, key, r=COE, oe0=None, g=None, extra=0.0):
    g = s["g"] if g is None else g
    oe0 = oe_norm(s) if oe0 is None else oe0
    reinv = g / s["roic"] if g > 0 else 0.0
    path = oe_path(s, oe0, g)
    pv_exp = sum(oe * (1 - reinv) / (1 + r) ** t for oe, t in zip(path, T_YEARS))
    tv = oe0 * (1 + g) ** 5 * (1 - reinv) / (r - g)
    pv_tv = tv / (1 + r) ** T_YEARS[-1]
    pv_q4 = s["q4"] / (1 + r) ** T_Q4
    non_op = OTHER_EQUITY_INV + YUZHONG_RECOVERY[key] + CONTINGENT[key]
    total = pv_q4 + pv_exp + pv_tv + NET_CASH_ADJ - MINORITY_CASH_CLAIM + non_op + extra
    return dict(total=total, ps=total / SHARES, pv_q4=pv_q4, pv_exp=pv_exp, pv_tv=pv_tv,
                non_op=non_op, path=path, reinv=reinv)


def weighted(vals, weights=None):
    w = weights or {k: SCEN[k]["p"] for k in ORDER}
    return sum(w[k] * vals[k] for k in ORDER)


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
    print("=== 000933 神火股份 独立估值（价格日 2026-10-20，现价 %.2f，股本 %.4f 亿股）===" % (PRICE, SHARES))
    print("经调整净现金（合并口径）: %.2f 亿；少数股东应占云南神火净现金: -%.2f 亿；其他非经营资产: %.2f 亿"
          % (NET_CASH_ADJ, MINORITY_CASH_CLAIM, OTHER_EQUITY_INV))
    print("  明细: 货币资金 %.2f + 定期存单 %.2f + 质押定存 %.2f - 冻结 %.2f - 复垦预计负债 %.2f - 经营备付 %.2f"
          " - 应付股利 %.2f - 有息负债 %.2f - 类债务 %.2f"
          % (CASH, CD_CURRENT, PLEDGED_TD, FROZEN, RECLAMATION, OPER_RESERVE, DIV_PAYABLE, DEBT, OTHER_DEBT_LIKE))
    print("2026 前三季度归母净利 %.2f，剔除崔岗井田减值归母影响后 %.2f" % (NP_9M_2026, NP_9M_2026_EX))
    print()
    vals, nps, res = {}, {}, {}
    for k in ORDER:
        s = SCEN[k]
        n = normalized(s)
        v = value_total(s, k)
        vals[k], nps[k], res[k] = v["ps"], n["np"], v
        print("[%s] p=%.2f 沪铝 %d 氧化铝 %d 吨铝价差(不含税) %.0f；K 新疆 %d 云南 %d；产量 %.1f+%.1f 万吨"
              % (k, s["p"], s["al"], s["alumina"], n["spread"], s["kx"], s["ky"], s["vx"], s["vy"]))
        print("   税前：新疆 %.2f 云南 %.2f 煤炭 %.2f 铝箔 %.2f 贸易 %.2f 总部 %.2f"
              % (n["x_pre"], n["y_pre"], n["coal_pre"], s["foil"], s["trade"], s["hq"]))
        print("   归母：电解铝 %.2f（云南少数股东 %.2f）煤炭 %.2f 铝箔 %.2f 贸易 %.2f 总部 %.2f 联营 %.2f 净利息 %.2f"
              % (n["al_parent"], n["y_minority"], n["coal"], n["foil"], n["trade"], n["hq"], n["assoc"], n["net_int"]))
        print("   正常化归母净利 %.2f；所有者收益 %.2f；2026E 归母（剔除减值）%.2f；再投资率 %.1f%%，增量回报 %.0f%%，g=%.1f%%"
              % (n["np"], oe_norm(s), NP_9M_2026_EX + s["q4"], v["reinv"] * 100, s["roic"] * 100, s["g"] * 100))
        print("   所有者收益路径 " + " ".join("%d:%.2f" % (y, o) for y, o in zip(YEARS, v["path"]))
              + "；终值增长 %.1f%%" % (s["g"] * 100))
        print("   PV：2026Q4 %.2f + 2027-31 %.2f + 终值 %.2f（终值占经营价值 %.0f%%）+ 净现金 %.2f - 少数现金 %.2f + 非经营 %.2f"
              % (v["pv_q4"], v["pv_exp"], v["pv_tv"], 100 * v["pv_tv"] / (v["pv_q4"] + v["pv_exp"] + v["pv_tv"]),
                 NET_CASH_ADJ, MINORITY_CASH_CLAIM, v["non_op"]))
        print("   V = %.2f 亿 = %.2f 元/股（剔除回购专户 %.2f 元/股）；P/V = %.3f"
              % (v["total"], v["ps"], v["total"] / (SHARES - TREASURY), PRICE / v["ps"]))
        print()
    vw = weighted(vals)
    pv = PRICE / vw
    tier = "明显低估" if pv <= 0.75 else "温和低估" if pv <= 0.90 else "大致合理" if pv <= 1.10 else "偏贵或价值陷阱风险高"
    vw_tot = weighted({k: res[k]["total"] for k in ORDER})
    print("加权 V = %.2f 元/股（剔除回购专户 %.2f）；P/V = %.3f → %s" % (vw, vw_tot / (SHARES - TREASURY), pv, tier))
    print("加权正常化归母净利 = %.2f 亿" % weighted(nps))
    v8 = weighted({k: value_total(SCEN[k], k, r=0.08)["ps"] for k in ORDER})
    v10 = weighted({k: value_total(SCEN[k], k, r=0.10)["ps"] for k in ORDER})
    print("股权成本 8%%: V = %.2f；10%%: V = %.2f" % (v8, v10))
    for k in ORDER:
        print("   %s 8%%: %.2f  10%%: %.2f" % (k, value_total(SCEN[k], k, r=0.08)["ps"], value_total(SCEN[k], k, r=0.10)["ps"]))

    # 隐含回报：基准情景现金流使现值等于现价
    base = SCEN["base"]
    irr = solve(lambda r: value_total(base, "base", r=r)["ps"], 0.05, 0.40, PRICE)
    print("现价隐含回报（基准现金流）= %.2f%%" % (irr * 100))

    # 反向 DCF
    def v_al(al):
        s = dict(base, al=al)
        return value_total(s, "base")["ps"]
    al_imp = solve(v_al, 14000, 26000, PRICE)
    print("反向 DCF：其他假设取基准，现价隐含长期沪铝 = %.0f 元/吨（氧化铝 %d，吨铝价差不含税 %.0f）"
          % (al_imp, base["alumina"], spread_ex_vat(al_imp, base["alumina"])))
    g_imp = solve(lambda g: value_total(base, "base", g=g)["ps"], -0.30, 0.05, PRICE)
    print("反向 DCF：基准所有者收益 %.2f 下现价隐含永续增速 = %.2f%%" % (oe_norm(base), g_imp * 100))

    def v_10y(x):
        oe0 = oe_norm(base)
        path = [oe0 + FADE_2027 * (oe_runrate(base) - oe0)] + [oe0 * (1 + x) ** k for k in range(1, 10)]
        reinv = base["g"] / base["roic"]
        pv = sum(o * (1 - reinv) / (1 + COE) ** (1.2 + i) for i, o in enumerate(path))
        tv = path[-1] * (1 + base["g"]) * (1 - reinv) / (COE - base["g"]) / (1 + COE) ** (1.2 + 9)
        tot = pv + tv + SCEN["base"]["q4"] / (1 + COE) ** T_Q4 + NET_CASH_ADJ - MINORITY_CASH_CLAIM \
            + OTHER_EQUITY_INV + YUZHONG_RECOVERY["base"]
        return tot / SHARES
    x_imp = solve(v_10y, -0.30, 0.10, PRICE)
    print("反向 DCF：自 2027 年基准起点，现价隐含 2028-2036 年所有者收益年增速 = %.2f%%（其后 1.5%%）" % (x_imp * 100))

    # 基准情景敏感性
    print()
    print("基准情景敏感性（元/股）：")
    for lab, kw in (("沪铝 -1000", dict(al=base["al"] - 1000)), ("沪铝 +1000", dict(al=base["al"] + 1000)),
                    ("氧化铝 +300", dict(alumina=base["alumina"] + 300)), ("氧化铝 -300", dict(alumina=base["alumina"] - 300)),
                    ("K 新疆与云南各 +300", dict(kx=base["kx"] + 300, ky=base["ky"] + 300)),
                    ("煤价 -100", dict(coal_price=base["coal_price"] - 100)),
                    ("终值增长 0.5%", dict(g=0.005)), ("终值增长 2.5%", dict(g=0.025))):
        s = dict(base, **kw)
        print("   %-18s V = %.2f（正常化归母 %.2f）" % (lab, value_total(s, "base")["ps"], normalized(s)["np"]))
    oe_b = oe_norm(base)
    path_b = value_total(base, "base")["path"]
    gr = [path_b[0] / oe_runrate(base) - 1] + [path_b[i] / path_b[i - 1] - 1 for i in range(1, 5)]
    print("基准所有者收益增速（相对 2026E %.2f）：" % oe_runrate(base) + " ".join("%d:%.1f%%" % (y, g * 100) for y, g in zip(YEARS, gr)))

    # 交叉验证
    mcap = PRICE * SHARES
    print()
    print("市值 %.1f 亿；市值/基准正常化归母 %.1fx；市值/加权正常化 %.1fx；市值/2026E 归母（剔除减值）%.1fx"
          % (mcap, mcap / nps["base"], mcap / weighted(nps), mcap / (NP_9M_2026_EX + base["q4"])))
    print("2025 年报现金分红 17.87 亿 + 回购 2.55 亿 → 股息+回购收益率 %.2f%%" % ((17.87 + 2.55) / mcap * 100))
    print("2026E 若分红率 30%%/45%% → 股息率 %.1f%% / %.1f%%"
          % (0.30 * (NP_9M_2026_EX + base["q4"]) / mcap * 100, 0.45 * (NP_9M_2026_EX + base["q4"]) / mcap * 100))
    n = normalized(base)
    ebit_norm = n["x_pre"] + n["y_pre"] + n["coal_pre"] + base["foil"] + base["trade"] + base["hq"] + base["assoc"]
    ev_book = mcap + 50.57 - NET_CASH_ADJ
    print("EV（少数股东权益按账面 50.57）= %.1f 亿；基准正常化 EBIT %.1f 亿 → EV/EBIT %.1fx" % (ev_book, ebit_norm, ev_book / ebit_norm))
    print("PB（现价/每股归母净资产 303.40/22.49）= %.2fx；基准正常化 ROE = %.1f%%" % (mcap / 303.40, n["np"] / 303.40 * 100))

    # 证伪触发后的 V
    print()
    f1 = weighted(vals, {"bear": 0.6, "base": 0.4, "bull": 0.0})
    print("F1 2027 年任意连续两季沪铝季均价 < 20,500：权重改为 0.6/0.4/0 → V = %.2f" % f1)
    alt = {}
    for k, a in (("bear", 3700), ("base", 3400), ("bull", 3200)):
        alt[k] = value_total(dict(SCEN[k], alumina=a), k)["ps"]
    f2 = weighted(alt)
    print("F2 氧化铝季度均价 > 3,500 持续：三情景氧化铝 3700/3400/3200 → V = %.2f" % f2)
    alt = {k: value_total(dict(SCEN[k], ky=SCEN[k]["ky"] + 500, vy=SCEN[k]["vy"] - 9), k)["ps"] for k in ORDER}
    f3 = weighted(alt)
    print("F3 云南电价上调或枯水限产：K 云南 +500、产量 -9 万吨 → V = %.2f" % f3)
    f4 = vw - 40 / SHARES
    print("F4 资本配置失当（主业外或高价并购 >50 亿、分红率 <35%%）：扣 40 亿 → V = %.2f" % f4)
    alt = {k: value_total(dict(SCEN[k], coal_price=SCEN[k]["coal_price"] - 80), k, extra=-20.0)["ps"] for k in ORDER}
    f5 = weighted(alt)
    print("F5 裕中/煤炭外溢：母公司补资或承担担保 20 亿、三情景煤价各 -80 → V = %.2f" % f5)
    print()
    for lab, thr in (("明显低估 ≤0.75", 0.75), ("温和低估 0.90", 0.90), ("大致合理上沿 1.10", 1.10)):
        print("V 不变时 %s 对应价格 %.2f" % (lab, vw * thr))


if __name__ == "__main__":
    main()
