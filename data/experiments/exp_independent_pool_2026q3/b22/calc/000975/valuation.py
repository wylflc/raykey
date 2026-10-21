#!/usr/bin/env python3
"""000975 山金国际：OI-291 b22 独立估值（价格日 2026-10-21）。

运行：python3 valuation.py
单位：金额亿元；每股价值元/股；金价美元/盎司（USD）或元/克；产量吨。
最新定期报告为 2026 中报（三季报预约 2026-10-24）。全部输入写在本文件内，来源见正文。

结构（归母、所有者收益口径，股权成本 9%）：
  V = [国内矿山与贸易 2026H2–2031 所有者收益现值 + 2031 年终值（Gordon）
       + Osino 双子山逐年现金流现值（有限寿命，折现率 = 股权成本 + 1.5% 国别溢价）
       + 合并口径经调整净现金 − 少数股东应占子公司净金融资产
       + 华盛金矿期权价值 + 其他权益工具投资] / 总股本
商品价格：长期正常化金价（2026 年实际美元）按 2% 名义上涨；2027、2028 年由现货 4,180 美元
线性收敛（2027 取 2/3 现货 + 1/3 长期，2028 取 1/3 现货 + 2/3 长期），2029 年起取长期价。
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------- 快照与常数
PRICE = 24.31            # 2026-10-21 收盘
SHARES = 27.7253         # 亿股；2026-05-20 注销回购 4,194,829 股后 2,772,527,436 股，回购专户余 0
COE = 0.09
OSINO_PREM = 0.015       # 纳米比亚项目国别与执行风险溢价
FX = 6.85                # 长期 USD/CNY（2026-06-30 折算汇率 6.8109）
FX_NOW = 6.80
OZ = 31.1035             # 克/盎司
GOLD_SPOT = 4180.0       # 2026-10 中旬伦敦现货约 4,170–4,200 美元
AG_SPOT = 57.0           # 2026-10-15 约 56.7 美元
AG_NET_RATIO = 0.76      # 精矿含银净实现价 ÷ 国际银价折人民币（2025：7.03 元/克 对 约 40 美元×7.18）
T0 = 2026.8              # 估值时点 2026-10-21

# 2026H2 已大部分实现的价格（各情景相同）
H2_GOLD_CNY = 920.0      # 元/克：Q3 约 925（4,200–4,300 美元×6.80），Q4 约 910
H2_AG_NET = 58.0 * FX_NOW / OZ * AG_NET_RATIO   # ≈9.6 元/克
H2_PB, H2_ZN = 15000.0, 15500.0                  # 元/吨（金属量，扣加工费不含税）

# ---------------------------------------------------------------- 2026-06-30 资产负债（中报第 45–46、75、85、91–92、101 页）
CASH = 55.0379           # 货币资金
CD = 27.1365             # 其他流动资产中大额存单（计划持有至到期）
RESTRICTED = 19.1827     # 受限货币资金：银行承兑汇票保证金 18.5320、复垦保证金 0.6505 等
DEBT = 0.20 + 19.0885 + 1.4650 + 0.0071 + 0.2030   # 短借、长借、一年内到期长借及利息、租赁负债（含一年内）
LT_PAYABLE = 4.0642      # 矿业权出让金（长期应付款 3.7489 + 一年内到期 0.3153），按类债务扣除
OP_RESERVE = 4.0         # 经营备付：约一个月矿山现金成本、管理费与贸易周转
TAX_BACKPAY = 2.8722     # 2026-10-16 公告 2026-051：吉林板庙子补缴 2023–2025 所得税及滞纳金，已缴清（期后现金流出）
OTHER_EQUITY_INV = 0.2082
# 少数股东应占子公司净金融资产：(流动资产-流动负债-非流动负债)×少数股权比例（中报第 105 页）
SUBS = {  # 流动资产, 流动负债, 非流动负债, 少数比例
    "吉林板庙子": (16.2738, 1.6082, 1.1866, 0.05),
    "青海大柴旦": (11.5213, 2.0101, 4.7226, 0.10),
    "玉龙矿业": (9.1709, 2.9329, 1.4282, 0.2333),
}


def net_cash_adj() -> float:
    return CASH + CD - RESTRICTED - DEBT - LT_PAYABLE - OP_RESERVE - TAX_BACKPAY


def minority_nfa() -> float:
    return sum((ca - cl - ncl) * m for ca, cl, ncl, m in SUBS.values())


def cny_g(usd: float, fx: float = FX) -> float:
    return usd * fx / OZ


# ---------------------------------------------------------------- 情景
YEARS = [2027, 2028, 2029, 2030, 2031]
SCEN = {
    "bear": dict(
        p=0.25, gold_lr=2900.0, ag_ratio=78.0, pb=13000.0, zn=13000.0,
        au_dom=[6.1, 5.8, 5.6, 5.4, 5.3], cc_steps=(0.12, 0.06), cc_esc=0.04,
        capex_au=[9.0, 9.0, 8.5, 8.0, 7.5],
        yl_ag=[135, 135, 135, 135, 135], yl_pb=[10.5] * 5, yl_zn=[20.0] * 5,
        yl_cc_add=[0, 0, 0, 0, 0], yl_cc_esc=0.04, yl_capex=[2.5, 2.5, 2.5, 2.2, 2.2], yl_tax_2031=0.25,
        trade=0.2, corp=(-2.5, -2.0), g_dom=0.0,
        os_capex={2026: 9.0, 2027: 15.0, 2028: 3.0},
        os_prod={2027: 0.8, 2028: 3.6, **{y: 4.5 for y in range(2029, 2040)}, 2040: 2.5},
        os_ext=(0, 0, 0.0), os_aisc=1400.0, huasheng=0.0,
    ),
    "base": dict(
        p=0.50, gold_lr=3750.0, ag_ratio=75.0, pb=14500.0, zn=15000.0,
        au_dom=[6.4, 6.3, 6.3, 6.3, 6.3], cc_steps=(0.07, 0.04), cc_esc=0.03,
        capex_au=[8.5, 8.5, 8.0, 7.5, 7.0],
        yl_ag=[145] * 5, yl_pb=[11.0] * 5, yl_zn=[21.0] * 5,
        yl_cc_add=[0, 0, 0, 0, 0], yl_cc_esc=0.03, yl_capex=[2.5, 2.5, 2.5, 2.2, 2.2], yl_tax_2031=0.15,
        trade=0.5, corp=(-2.2, -1.6), g_dom=0.01,
        os_capex={2026: 9.0, 2027: 13.0},
        os_prod={2027: 1.5, 2028: 4.6, **{y: 4.9 for y in range(2029, 2040)}, 2040: 3.0},
        os_ext=(2041, 2048, 4.0 * 0.5), os_aisc=1200.0, huasheng=5.0,
    ),
    "bull": dict(
        p=0.25, gold_lr=4800.0, ag_ratio=72.0, pb=16000.0, zn=16500.0,
        au_dom=[6.6, 6.9, 7.1, 7.2, 7.3], cc_steps=(0.04, 0.025), cc_esc=0.025,
        capex_au=[9.0, 9.0, 8.5, 8.0, 7.5],
        yl_ag=[145, 145, 170, 170, 170], yl_pb=[11.0, 11.0, 13.0, 13.0, 13.0], yl_zn=[21.0, 21.0, 25.0, 25.0, 25.0],
        yl_cc_add=[0, 0, 1.0, 1.0, 1.0], yl_cc_esc=0.025, yl_capex=[4.5, 4.5, 2.8, 2.5, 2.5], yl_tax_2031=0.15,
        trade=0.8, corp=(-2.0, -1.4), g_dom=0.02,
        os_capex={2026: 8.0, 2027: 11.0},
        os_prod={2027: 2.0, 2028: 5.0, **{y: 5.2 for y in range(2029, 2041)}},
        os_ext=(2041, 2050, 4.5 * 0.8), os_aisc=1100.0, huasheng=10.0,
    ),
}

# ---------------------------------------------------------------- 经营参数（2026 中报、2025 年报、IR 记录）
AU_TAX = 0.25            # 黑河洛克、青海大柴旦、吉林板庙子（2026 起不再享受 15%）
AU_TS = 0.053            # 税金及附加/采选收入（2026H1：2.71/51.31）
AU_MINORITY = 0.05       # 大柴旦 10%×约 30–39% 利润 + 板庙子 5%×约 23–29% 利润（2026H1、2025 子公司净利）
AU_BYP_AG = 18.0         # 金矿副产银 吨/年（洛克 2025 年 17.23 吨）
AU_CC_2026 = 150.0       # 元/克，现金成本（不含折旧摊销，含矿山管理研发）。2026H1 按子公司营业利润倒推约 136，下半年管理研发偏重，全年取 150；2025 年约 129
YL_TAX = 0.15            # 玉龙矿业西部大开发 15%
YL_TS = 0.06
YL_CC_2026 = 7.0         # 亿元/年，玉龙现金成本（不含折旧，含管理）
YL_SHARE = 0.7667
OS_TAX = 0.375           # Osino Gold Exploration and Mining (Pty) Ltd. 所得税率
OS_LEAK = 0.05           # 股息预提等汇回损耗
OS_BUDGET = 35.5234      # 双子山预算（2025 年报第 113 页）
OS_SPENT = 11.8528       # 截至 2026-06-30 累计投入（中报第 20 页）
OS_AISC_ESC = 0.025


def gold_usd(year: int, lr: float) -> float:
    lr_nom = lr * 1.02 ** (year - 2026)
    if year == 2027:
        return GOLD_SPOT * 2 / 3 + lr_nom / 3
    if year == 2028:
        return GOLD_SPOT / 3 + lr_nom * 2 / 3
    return lr_nom


def ag_usd(year: int, s: dict) -> float:
    lr_nom = s["gold_lr"] / s["ag_ratio"] * 1.02 ** (year - 2026)
    if year == 2027:
        return AG_SPOT * 2 / 3 + lr_nom / 3
    if year == 2028:
        return AG_SPOT / 3 + lr_nom * 2 / 3
    return lr_nom


def au_cash_cost(year: int, s: dict) -> float:
    c = AU_CC_2026
    for y in range(2027, year + 1):
        if y == 2027:
            c *= 1 + s["cc_steps"][0]
        elif y == 2028:
            c *= 1 + s["cc_steps"][1]
        else:
            c *= 1 + s["cc_esc"]
    return c


def domestic_year(year: int, s: dict) -> dict:
    """国内金矿 + 玉龙 + 贸易 + 总部，归母所有者收益（亿元）。"""
    if year == 2026:  # 2026H2
        au_t, p, ag, cc = 3.30, H2_GOLD_CNY, H2_AG_NET, 152.0
        byp, capex_au, dep_au = AU_BYP_AG / 2, 3.75, 1.0
        yl = dict(ag=88.0, pb=6.5, zn=13.0, pbp=H2_PB, znp=H2_ZN, cc=3.6, capex=1.25, dep=0.6, tax=YL_TAX)
        trade, corp = s["trade"] / 2, s["corp"][0] / 2
    else:
        i = YEARS.index(year) if year in YEARS else len(YEARS) - 1
        au_t = s["au_dom"][i]
        p = cny_g(gold_usd(year, s["gold_lr"]))
        ag = cny_g(ag_usd(year, s)) * AG_NET_RATIO
        cc = au_cash_cost(year, s)
        byp, capex_au = AU_BYP_AG, s["capex_au"][i]
        dep_au = min(capex_au, 2.0 + 0.6 * (year - 2026))
        infl = 1.02 ** (year - 2026)
        yl_cc = YL_CC_2026 * (1 + s["yl_cc_esc"]) ** (year - 2026) + s["yl_cc_add"][i]
        yl = dict(ag=s["yl_ag"][i], pb=s["yl_pb"][i], zn=s["yl_zn"][i], pbp=s["pb"] * infl, znp=s["zn"] * infl,
                  cc=yl_cc, capex=s["yl_capex"][i], dep=min(s["yl_capex"][i], 1.2 + 0.1 * (year - 2026)),
                  tax=s["yl_tax_2031"] if year >= 2031 else YL_TAX)
        trade = s["trade"] * infl
        corp = (s["corp"][0] if year <= 2027 else s["corp"][1]) * (1.02 ** max(0, year - 2028))
    # 金矿（100%）
    rev = au_t * p / 100 + byp * ag / 100
    cash_cost = au_t * cc / 100
    ts = AU_TS * rev
    tax = AU_TAX * max(rev - cash_cost - ts - dep_au, 0)
    oe_au = (rev - cash_cost - ts - tax - capex_au) * (1 - AU_MINORITY)
    # 玉龙（100% 后乘 76.67%）
    rev_y = yl["ag"] * ag / 100 + yl["pb"] * 1000 * yl["pbp"] / 1e8 + yl["zn"] * 1000 * yl["znp"] / 1e8
    ts_y = YL_TS * rev_y
    tax_y = yl["tax"] * max(rev_y - yl["cc"] - ts_y - yl["dep"], 0)
    oe_y = (rev_y - yl["cc"] - ts_y - tax_y - yl["capex"]) * YL_SHARE
    oe = oe_au + oe_y + trade + corp
    return dict(year=year, au_t=au_t, p=p, ag=ag, cc=cc, rev_au=rev, oe_au=oe_au, rev_y=rev_y, oe_y=oe_y,
                trade=trade, corp=corp, oe=oe)


def osino_flows(s: dict) -> list[tuple[int, float, float]]:
    """返回 (年份, 产量, 归母现金流)；2026 指 2026H2。"""
    total_capex = OS_SPENT + sum(s["os_capex"].values())
    dep = total_capex / 12.0
    prod = dict(s["os_prod"])
    a, b, t_ext = s["os_ext"]
    if a:
        for y in range(a, b + 1):
            prod[y] = prod.get(y, 0) + t_ext
    out = []
    for y in range(2026, 2051):
        t = prod.get(y, 0.0)
        p = cny_g(gold_usd(y, s["gold_lr"])) if y >= 2027 else H2_GOLD_CNY
        aisc = cny_g(s["os_aisc"] * (1 + OS_AISC_ESC) ** (y - 2026))
        rev = t * p / 100
        cost = t * aisc / 100
        d = dep if 2028 <= y <= 2039 else 0.0
        tax = OS_TAX * max(rev - cost - d, 0)
        cf = rev - cost - tax - s["os_capex"].get(y, 0.0)
        if cf > 0:
            cf *= 1 - OS_LEAK
        out.append((y, t, cf))
    return out


def tfrac(year: int) -> float:
    return 0.0 if year == 2026 else (year + 0.5) - T0


def value(s: dict, r: float = COE, g_override: float | None = None) -> dict:
    g = s["g_dom"] if g_override is None else g_override
    rows = [domestic_year(y, s) for y in [2026] + YEARS]
    pv_dom = sum(row["oe"] / (1 + r) ** tfrac(row["year"]) for row in rows)
    oe_2031 = rows[-1]["oe"]
    tv = oe_2031 * (1 + g) / (r - g)
    pv_tv = tv / (1 + r) ** tfrac(2031)
    ro = r + OSINO_PREM
    os_rows = osino_flows(s)
    pv_os = sum(cf / (1 + ro) ** tfrac(y) for y, _, cf in os_rows)
    nc = net_cash_adj() - minority_nfa()
    eq = pv_dom + pv_tv + pv_os + nc + s["huasheng"] + OTHER_EQUITY_INV
    return dict(v=eq / SHARES, eq=eq, pv_dom=pv_dom, pv_tv=pv_tv, pv_os=pv_os, nc=nc, rows=rows,
                os_rows=os_rows, tv=tv, tv_share=pv_tv / eq)


def weighted(r: float = COE) -> float:
    return sum(s["p"] * value(s, r)["v"] for s in SCEN.values())


def solve(f, lo: float, hi: float, target: float, n: int = 200) -> float:
    flo = f(lo) - target
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def with_gold(s: dict, lr: float) -> dict:
    t = dict(s)
    t["gold_lr"] = lr
    return t


# ---------------------------------------------------------------- 2026 正常化归母净利（报表口径）
def normalized_np_2026(s: dict) -> dict:
    p = cny_g(s["gold_lr"])
    ag = cny_g(s["gold_lr"] / s["ag_ratio"]) * AG_NET_RATIO
    rev = 6.6 * p / 100 + AU_BYP_AG * ag / 100
    pbt = rev - 6.6 * AU_CC_2026 / 100 - AU_TS * rev - (2.0 + 1.2)   # 折旧摊销 2.0 + 合并评估增值摊销 1.2
    np_au = pbt * (1 - AU_TAX) * (1 - AU_MINORITY)
    rev_y = 140 * ag / 100 + 11.0 * 1000 * s["pb"] / 1e8 + 21.0 * 1000 * s["zn"] / 1e8
    pbt_y = rev_y - YL_CC_2026 - YL_TS * rev_y - (1.2 + 1.33)
    np_y = pbt_y * (1 - YL_TAX) * YL_SHARE
    net_int = -0.27                                                   # 2026H1 利息净支出 0.17×2×(1-25%)
    total = np_au + np_y + s["trade"] + s["corp"][0] + net_int
    return dict(total=total, au=np_au, yl=np_y, p=p, ag=ag)


def reserves_only_floor(s: dict, r: float = COE) -> float:
    """仅按 2025 年末储量开采、不续期的地板值（基准成本，金价按情景）。"""
    mines = {"黑河洛克": (6.168 * 0.93, 2.2), "吉林板庙子": (9.657 * 0.90, 1.45), "青海大柴旦": (42.092 * 0.88, 2.85)}
    pv = 0.0
    for rec_t, rate in mines.values():
        left, y = rec_t, 2027
        while left > 1e-9:
            t = min(rate, left)
            p = cny_g(gold_usd(y, s["gold_lr"]))
            cc = au_cash_cost(y, s)
            rev = t * p / 100
            cf = (rev - t * cc / 100 - AU_TS * rev) * (1 - AU_TAX) - t * 60 / 100   # 维持性资本开支约 60 元/克
            pv += cf * (1 - AU_MINORITY) / (1 + r) ** tfrac(y)
            left -= t
            y += 1
    yl_years = 2701.5 / 145
    yl = sum(domestic_year(min(y, 2031), s)["oe_y"] / (1 + r) ** tfrac(y) for y in range(2027, 2027 + int(yl_years)))
    os_pv = sum(cf / (1 + r + OSINO_PREM) ** tfrac(y) for y, _, cf in osino_flows({**s, "os_ext": (0, 0, 0.0)}))
    return (pv + yl + os_pv + net_cash_adj() - minority_nfa()) / SHARES


def main() -> None:
    print("== 000975 山金国际 独立估值（价格日 2026-10-21，现价 %.2f 元，总股本 %.4f 亿股）==" % (PRICE, SHARES))
    nc, mn = net_cash_adj(), minority_nfa()
    print("\n[经调整净现金，2026-06-30]")
    print("  货币资金 %.2f + 大额存单 %.2f − 受限资金 %.2f − 有息负债(含租赁) %.2f − 矿业权出让金 %.2f"
          " − 经营备付 %.2f − 期后补税 %.2f = %.2f 亿" % (CASH, CD, RESTRICTED, DEBT, LT_PAYABLE, OP_RESERVE,
                                                       TAX_BACKPAY, nc))
    print("  少数股东应占子公司净金融资产 %.2f → 归母口径 %.2f 亿；华盛期权与其他权益投资另列" % (mn, nc - mn))

    print("\n[2026 正常化归母净利（报表口径，剔除补税等一次性项目）]")
    norm = {}
    for k, s in SCEN.items():
        n = normalized_np_2026(s)
        norm[k] = n["total"]
        print("  %-4s 金价 %5.0f 美元（%.0f 元/克），银净价 %.2f 元/克：金矿归母 %.2f + 玉龙归母 %.2f + 贸易 %.2f"
              " + 总部 %.2f + 净利息 -0.27 = %.2f 亿"
              % (k, s["gold_lr"], n["p"], n["ag"], n["au"], n["yl"], s["trade"], s["corp"][0], n["total"]))
    # 2026 板庙子税率由 15% 升至 25% 对正常化利润的影响（基准）
    s = SCEN["base"]
    p = cny_g(s["gold_lr"])
    bmz_pbt = 1.45 * (p - 200) / 100 - AU_TS * 1.45 * p / 100
    print("  吉林板庙子按 25%% 而非 15%%：基准年化税前约 %.2f 亿，归母净利减少约 %.2f 亿/年"
          % (bmz_pbt, bmz_pbt * 0.10 * 0.95))

    print("\n[情景估值，股权成本 9%]")
    res = {}
    for k, s in SCEN.items():
        v = value(s)
        res[k] = v
        print("  %-4s p=%.2f  国内显性 %.1f + 国内终值 %.1f（g=%.1f%%，终值占比 %.0f%%） + Osino %.1f + 净现金 %.1f"
              " + 华盛 %.1f + 其他 %.2f = %.1f 亿 → V = %.2f 元"
              % (k, s["p"], v["pv_dom"], v["pv_tv"], s["g_dom"] * 100, v["tv_share"] * 100, v["pv_os"], v["nc"],
                 s["huasheng"], OTHER_EQUITY_INV, v["eq"], v["v"]))
    vw = weighted()
    print("  加权 V = %.2f 元；P/V = %.2f" % (vw, PRICE / vw))
    print("  每股拆分（基准）：国内 %.2f + Osino %.2f + 净现金 %.2f + 华盛与其他 %.2f 元"
          % ((res["base"]["pv_dom"] + res["base"]["pv_tv"]) / SHARES, res["base"]["pv_os"] / SHARES,
             res["base"]["nc"] / SHARES, (SCEN["base"]["huasheng"] + OTHER_EQUITY_INV) / SHARES))
    print("  分档价格（V 不变）：明显低估 ≤ %.2f；温和低估 %.2f–%.2f；大致合理 %.2f–%.2f；偏贵 > %.2f 元"
          % (0.75 * vw, 0.75 * vw, 0.90 * vw, 0.90 * vw, 1.10 * vw, 1.10 * vw))

    print("\n[逐年所有者收益（归母，亿元；2026 为下半年）]")
    for k in SCEN:
        line = []
        os_map = {y: cf for y, _, cf in res[k]["os_rows"]}
        for row in res[k]["rows"]:
            tot = row["oe"] + os_map[row["year"]]
            line.append("%d: 国内 %.1f / Osino %.1f / 合计 %.1f" % (row["year"], row["oe"], os_map[row["year"]], tot))
        print("  %-4s " % k + "；".join(line))
        r = res[k]["rows"]
        print("        金价（元/克）" + " ".join("%d:%.0f" % (x["year"], x["p"]) for x in r)
              + "；国内金产量（吨）" + " ".join("%d:%.2f" % (x["year"], x["au_t"]) for x in r)
              + "；现金成本（元/克）" + " ".join("%d:%.0f" % (x["year"], x["cc"]) for x in r))

    print("\n[股权成本敏感性]")
    for r in (0.08, 0.09, 0.10):
        vs = {k: value(s, r)["v"] for k, s in SCEN.items()}
        print("  r=%.0f%%：熊 %.2f / 基准 %.2f / 牛 %.2f → 加权 %.2f 元，P/V %.2f"
              % (r * 100, vs["bear"], vs["base"], vs["bull"], weighted(r), PRICE / weighted(r)))

    base = SCEN["base"]
    irr = solve(lambda r: value(base, r)["v"], 0.03, 0.30, PRICE)
    irr_w = solve(lambda r: weighted(r), 0.03, 0.30, PRICE)
    print("\n[现价隐含回报] 基准情景现金流（含终值与净现金）使现值等于现价的折现率 = %.2f%%（加权情景 %.2f%%）"
          % (irr * 100, irr_w * 100))

    print("\n[反向 DCF，9%]")
    g_imp = solve(lambda g: value(base, COE, g)["v"], -0.05, 0.085, PRICE)
    print("  基准其余假设不变，国内永续增速需 %.2f%%（上限 2.5%%）" % (g_imp * 100))
    lr_imp = solve(lambda lr: value(with_gold(base, lr))["v"], 2000, 8000, PRICE)
    print("  基准结构下现价隐含长期金价 %.0f 美元/盎司（%.0f 元/克，2026 年实际值）" % (lr_imp, cny_g(lr_imp)))
    # 10 年增速：以基准 2028 年合计所有者收益为起点，10 年后转 1.5% 永续
    os_map = {y: cf for y, _, cf in res["base"]["os_rows"]}
    oe28 = res["base"]["rows"][2]["oe"] + os_map[2028]
    target = PRICE * SHARES - res["base"]["nc"] - base["huasheng"] - OTHER_EQUITY_INV

    def pv_growth(x: float) -> float:
        pv, oe = 0.0, oe28
        for i in range(10):
            pv += oe / (1 + COE) ** tfrac(2028 + i)
            oe *= 1 + x
        return pv + oe * 1.015 / (COE - 0.015) / (1 + COE) ** tfrac(2037)

    x_imp = solve(pv_growth, -0.10, 0.20, target)
    print("  以基准 2028 年合计所有者收益 %.1f 亿为起点，现价隐含 2028–2037 年增速 %.1f%%，其后 1.5%% 永续"
          % (oe28, x_imp * 100))

    print("\n[金价敏感性：基准结构，只改长期金价（2026 年实际美元）]")
    for lr in (2800, 3200, 3500, 3750, 4000, 4180, 4500, 4800, 5200):
        print("  %5d 美元（%4.0f 元/克）→ V %.2f 元" % (lr, cny_g(lr), value(with_gold(base, lr))["v"]))

    print("\n[交叉验证]")
    print("  储量地板值（不续期、无勘探转化，基准金价）%.2f 元；牛市金价 %.2f 元"
          % (reserves_only_floor(base), reserves_only_floor(SCEN["bull"])))
    os_capex_cum = OS_SPENT + sum(base["os_capex"].values())
    os_ss = [cf for y, _, cf in res["base"]["os_rows"] if y == 2030][0]
    print("  Osino：基准累计投资 %.1f 亿，2030 年税后现金流 %.1f 亿 → 增量现金回报 %.0f%%；Osino 现值 %.1f 亿（%.2f 元/股）"
          % (os_capex_cum, os_ss, os_ss / os_capex_cum * 100, res["base"]["pv_os"], res["base"]["pv_os"] / SHARES))
    mcap = PRICE * SHARES
    print("  市值 %.1f 亿；对基准 2026 正常化归母净利 %.1f 亿 PE %.1f 倍；TTM PE 17.8、PB 4.23"
          % (mcap, norm["base"], mcap / norm["base"]))
    alt = (25.73 - 18.532) / SHARES
    print("  应付票据 25.73 亿改作债务、承兑保证金 18.53 亿计入现金：加权 V %.2f 元（%.2f）" % (vw - alt, -alt))
    ev = mcap - nc + 20.18
    print("  EV（市值−经调整净现金+少数股东权益账面 20.18）%.1f 亿；TTM 营业利润约 55.6 亿 → EV/EBIT %.1f 倍"
          % (ev, ev / 55.64))

    # 证伪与触发后 V
    print("\n[证伪触发后的独立 V（9%，其余按基准）]")
    trig = {
        "金价长期 4,600 美元（2027 年均价不低于 4,600 且央行购金未退潮）": value(with_gold(base, 4600))["v"],
        "金价长期 3,200 美元（2027 年均价不高于 3,200）": value(with_gold(base, 3200))["v"],
    }
    s = dict(base)
    s["au_dom"] = [6.0, 5.8, 5.6, 5.5, 5.4]
    trig["国内矿产金 2027 年不高于 6.0 吨并继续下滑"] = value(s)["v"]
    s = dict(base)
    s["os_capex"] = {2026: 9.0, 2027: 13.0, 2028: 8.0}
    s["os_prod"] = {2028: 2.5, 2029: 4.6, **{y: 4.9 for y in range(2030, 2041)}}
    trig["Osino 首金推迟至 2028 年且投资超预算 8 亿"] = value(s)["v"]
    s = dict(base)
    s["cc_steps"] = (0.15, 0.06)
    trig["2027 年克金现金成本较 2026 年上升 15% 以上"] = value(s)["v"]
    for kk, vv in trig.items():
        print("  %s → V %.2f 元" % (kk, vv))

    print("\n[增长路径与再投资（基准）]")
    # 2026H1 实际归母所有者收益：归母净利 24.16 + 折旧摊销 3.07×0.92 − 购建长期资产 11.11（扣少数应占国内部分 0.46）
    oe_h1 = 24.1647 + 3.066 * 0.92 - (11.1101 - 0.46)
    osm = {y: cf for y, _, cf in res["base"]["os_rows"]}
    tot = {row["year"]: row["oe"] + osm[row["year"]] for row in res["base"]["rows"]}
    tot[2026] += oe_h1
    gr = [tot[y] / tot[y - 1] - 1 for y in YEARS]
    print("  2026 全年所有者收益约 %.1f 亿（上半年实际约 %.1f）；2027–2031 合计所有者收益 %s"
          % (tot[2026], oe_h1, " ".join("%d:%.1f" % (y, tot[y]) for y in YEARS)))
    print("  增速 " + " ".join("%d:%+.1f%%" % (y, g * 100) for y, g in zip(YEARS, gr)))
    capex = {}
    for y in YEARS:
        i = YEARS.index(y)
        capex[y] = (base["capex_au"][i] * (1 - AU_MINORITY) + base["yl_capex"][i] * YL_SHARE
                    + base["os_capex"].get(y, 0.0))
    reinv = sum(capex.values()) / sum(tot[y] + capex[y] for y in YEARS)
    print("  2027–2031 资本开支（归母）%.1f 亿，占扣资本开支前现金收益 %.0f%%（再投资率）"
          % (sum(capex.values()), reinv * 100))

    print("\n[H 股摊薄敏感性：发行后总股本 15%（含绿鞋），发行费 3%]")
    n_new = SHARES / 0.85 - SHARES
    for ph in (17.0, 19.0, 24.31):
        vv = (vw * SHARES + ph * n_new * 0.97) / (SHARES + n_new)
        print("  发行价折人民币 %.2f 元 → 加权 V %.2f 元（%+.1f%%）" % (ph, vv, (vv / vw - 1) * 100))

    print("\n[2026 年报表口径估计（含一次性补税）与 Q3 估计]")
    h2 = domestic_year(2026, base)
    print("  2026H2 国内金矿收入 %.1f 亿、玉龙收入 %.1f 亿；三季度归母净利估计约 8.5–10.5 亿（金价约 925 元/克、矿产金约 1.65 吨）"
          % (h2["rev_au"], h2["rev_y"]))


if __name__ == "__main__":
    main()
