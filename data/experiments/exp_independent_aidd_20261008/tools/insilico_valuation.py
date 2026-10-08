#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英矽智能（03696.HK）独立估值脚本。

方法：分部加总 = 自有临床资产 rNPV + 已授权临床资产应得款 + 合作框架剩余对价（概率化）
      + 自有临床前组合（打包、低值）+ 平台与服务 DCF（只用可重复收入）
      − 未分摊总部费用现值 ± 持续发现引擎净现值（基准设为 0）
      + 经调整净现金（可转债按面值扣除）+ 期权行权款；熊/基准/牛概率加权。
约束：只用标准库；输入写死并注明出处与期间；不联网、不读文件。
运行：python3 insilico_valuation.py
单位：百万美元（US$M）；每股价值以港元表示。标"推断"者为勾稽或假设，公司未明说。
"""

# ---------------------------------------------------------------------------
# 0. 统一快照（2026-10-08）
# ---------------------------------------------------------------------------
PRICE_HKD = 48.24          # 2026-10-08 港股收盘（统一快照）
USD_HKD = 7.8484           # ECB 2026-10-07
USD_CNY = 6.7046           # ECB 2026-10-07
VAL_YEAR = 2026 + 280 / 365  # 2026-10-08 为当年第 281 天
Q4_FRAC = (2027 - VAL_YEAR)  # 2026 年剩余比例（约 0.23）
R_BASE = 0.10
PROB = {"bear": 0.30, "base": 0.50, "bull": 0.20}

# ---------------------------------------------------------------------------
# 1. 股本与摊薄（百万股）
# ---------------------------------------------------------------------------
SHARES_BASIC = 585.120194   # 2026-09-30 月报表（2026-10-07 披露）
OPTIONS = 17.776905         # 同上，Pre-IPO 期权余额
OPT_STRIKE_USD = 0.88       # 2026 中报附注 22.1：2026-06-30 加权平均行权价
# RSU 未归属 = 中报 Pre-IPO 2,632,553 + Post-IPO 3,706,886 − 7~9 月月报表归属
# (1,654,180+47,264+47,225 及 418,591)，忽略失效（推断）
RSU_UNVESTED = (2.632553 - 1.654180 - 0.047264 - 0.047225) + (3.706886 - 0.418591)
DIL_SHARES = SHARES_BASIC + OPTIONS + RSU_UNVESTED
OPT_PROCEEDS = OPTIONS * OPT_STRIKE_USD
SHARES_LISTING = 557.4185   # 2025-12-30 上市日（中报附注 20）
SHARES_PRE_IPO = 462.728    # 上市前股份（超额配股公告 2026-01-16）
CB_FACE = 305.0             # 零息可转债面值，2027-09-01 前后到期（2026-08-28 定价公告）
CB_CONV_HKD = 58.07         # 初始转股价
CB_SHARES = 41.174737       # 全部转股股数（固定汇率 7.8394）

# ---------------------------------------------------------------------------
# 2. 经调整净现金（2026-06-30 中报 + 7~9 月已披露事项，US$M）
# ---------------------------------------------------------------------------
CASH = 357.617              # 银行结余及现金
TERM_DEP = 108.950          # 原始期限 >3 个月定期存款
MMF = 108.338               # 货币基金（T+3 内可赎回，Level 2）
LISTED_EQ = 10.606          # 上市股权投资（流动 9.913 + 非流动 0.693，Level 1）
UNLISTED_EQ = 4.404         # 非上市股权（不计入）
BORROW = 14.682             # 人民币银行借款（1 年内到期）
LEASE = 1.390 + 3.584       # 租赁负债
CONTRACT_LIAB = 29.184      # 合同负债（预收履约义务，不作债务扣除，单列）
CB_NET = 301.6              # 可转债净募资（2026-09-03 完成公告）
Q3_OPT_HKD = 32.671407 + 0.198340 + 11.017639  # 7/8/9 月月报表期权行权款（百万港元）
Q3_OCF = 0.0                # 2026Q3 经营现金流未披露，设为 0（推断）
NET_CASH = (CASH + TERM_DEP + MMF + LISTED_EQ + CB_NET + Q3_OPT_HKD / USD_HKD + Q3_OCF
            - BORROW - LEASE - CB_FACE)
GROSS_LIQ = NET_CASH + CB_FACE   # 若可转债转股则不需偿还

# 历史现金消耗（经营现金流 + 资本开支，US$M；招股书/年报/中报现金流量表）
BURN = {"2023": -29.576 - 2.562 - 0.411, "2024": -57.401 - 0.844 - 0.081,
        "2025": -76.766 - 2.856 - 0.119, "2026H1": 78.985 - 0.932}
# 前瞻（无新首付款）：2026H1 现金经营费用（剔除股权激励）年化
# = 2*(销售成本10.338 + 销售6.365-2.270 + 研发49.328-8.453 + 管理12.577-4.967)；
# + 资本开支 3 + 可转债所列 200 名研发扩编约 40/年 − 可重复收入约 40 − 利息约 20（推断）
CASH_OPEX_RUN = 2 * (10.338 + (6.365 - 2.270) + (49.328 - 8.453) + (12.577 - 4.967))
FWD_BURN = CASH_OPEX_RUN + 3 + 40 - 40 - 20

# 收入结构（US$M）：招股书附录一附注 6、2025 年报 MD&A、2026 中报附注 3
# 可重复 = 药物发现合作 + 软件 + 非医药发现；一次性 = 管线授权（首付分摊、里程碑等）
REV = {
    "2023": dict(total=51.180, rep=8.796 + 3.362, one=39.022, top5=0.941, top1=0.762),
    "2024": dict(total=85.834, rep=3.144 + 3.970 + 2.131, one=76.589, top5=0.944, top1=0.606),
    "2025": dict(total=56.239, rep=24.952 + 4.913 + 2.489, one=23.885, top5=0.742, top1=0.420),
    # 2026H1 未拆分发现/管线：美国客户收入 95.913，扣除其他美国客户约 8 → 礼来相关一次性约 88（推断）
    "2026H1": dict(total=106.303, rep=106.303 - 88.0, one=88.0, top5=None, top1=None),
}
UPFRONT = {"2024": 58.0, "2025": 15.3}   # 年报披露的管线首付款收入
# 经济利润 = 净利润 + 公允价值变动损失 + 上市开支（股权激励保留为费用）
PROFIT = {"2023": (-211.640, 126.133, 7.355, 10.791), "2024": (-17.096, -9.004, 0.176, 3.259),
          "2025": (-352.316, 296.701, 5.274, 6.507), "2026H1": (35.537, 0.0, 0.0, 15.690)}

# ---------------------------------------------------------------------------
# 3. 通用函数
# ---------------------------------------------------------------------------
def disc(y, r):
    t = Q4_FRAC / 2 if y == 2026 else (y + 0.5 - VAL_YEAR)
    return 1.0 / (1.0 + r) ** t


def pv(cfs, r):
    return sum(v * disc(y, r) for y, v in cfs.items())


def add(cfs, y, v):
    cfs[y] = cfs.get(y, 0.0) + v


def tax(y):
    return 0.05 if y <= 2028 else 0.15   # 早期有亏损抵扣，仅预提税；之后 15%（推断）


def sales_curve(launch, peak, ramp, loe, end=2045, tail=0.3):
    s = {}
    for y in range(launch, end + 1):
        if y < loe:
            s[y] = peak * min(1.0, (y - launch + 1) / ramp)
        else:
            s[y] = peak * tail * (0.7 ** (y - loe))
    return s


def asset_cfs(costs=(), receipts=(), streams=()):
    """costs/receipts: (年, 金额, 概率)；streams: (上市年, 峰值销售, 爬坡年, 失去独占年, 经济分成率, 概率)。"""
    cfs = {}
    for y, amt, p in costs:
        add(cfs, y, -amt * p)
    for y, amt, p in receipts:
        add(cfs, y, amt * p * (1 - tax(y)))
    for launch, peak, ramp, loe, rate, p in streams:
        for y, s in sales_curve(launch, peak, ramp, loe).items():
            add(cfs, y, s * rate * p * (1 - tax(y)))
    return cfs


# ---------------------------------------------------------------------------
# 4. 资产参数
# 成功率基准：BIO/Informa/QLS《Clinical Development Success Rates 2011-2020》
#   呼吸 Ph3→批准 61.6%、Ph2→批准 13.5%、Ph1→批准 7.5%、Ph1→Ph2 55.9%；
#   肿瘤 Ph1→批准 5.3%、Ph1→Ph2 48.8%；神经 Ph1→批准 5.9%；自免 Ph2→批准 19.3%；
#   全部适应症 Ph1→批准 7.9%。
# ---------------------------------------------------------------------------
# Rentosertib 中国峰值销售两来源（取低）：
#   A 观研报告网 2023-05：中国 IPF 药物市场 2022 年 8 亿元、2025E 15 亿元；按 8%/年外推至 2034
#   B 头豹研究院 2024-01：2023 年 50.4 亿元、2028E 90.3 亿元；按 5%/年外推至 2034
#   各乘 25% 峰值份额（推断）
PEAK_SRC_A = 1.5e9 * 1.08 ** 9 * 0.25 / USD_CNY / 1e6
PEAK_SRC_B = 9.03e9 * 1.05 ** 6 * 0.25 / USD_CNY / 1e6
CN_PEAK_BASE = min(PEAK_SRC_A, PEAK_SRC_B)
# 海外：F&S（招股书）全球 IPF 药物 2030E 71 亿美元；AI CERTs 引分析师 2030 >50 亿美元；取低 × 10% 份额
EX_PEAK_BASE = min(7.1e3, 5.0e3) * 0.10

RENTO = {
    "bear": dict(pos=0.15, cn_peak=70, cn_launch=2032, cn_rate=0.30, p_partner=0.5,
                 upfront=50, p_glob=0.45, miles=100, roy=0.10, ex_peak=300, ex_launch=2035),
    "base": dict(pos=0.25, cn_peak=round(CN_PEAK_BASE, -1), cn_launch=2031, cn_rate=0.35,
                 p_partner=0.7, upfront=80, p_glob=0.55, miles=200, roy=0.12,
                 ex_peak=EX_PEAK_BASE, ex_launch=2034),
    "bull": dict(pos=0.40, cn_peak=250, cn_launch=2030, cn_rate=0.40, p_partner=0.9,
                 upfront=200, p_glob=0.65, miles=400, roy=0.15, ex_peak=2000, ex_launch=2033),
}


def rentosertib_oral(sc, pos=None):
    p = dict(RENTO[sc])
    if pos is not None:
        p["pos"] = pos
    # 中国 III 期剩余投入：中报未动用募资 HK$381.45m ≈ US$48.6m，2026Q4-2029 摊（推断）
    costs = [(2026, 3, 1), (2027, 18, 1), (2028, 17, 1), (2029, 11, 1),
             (p["cn_launch"] - 1, 6, p["pos"])]
    pp = p["pos"] * p["p_partner"]
    receipts = [(p["cn_launch"] - 1, p["upfront"], pp),
                (p["ex_launch"], p["miles"], pp * p["p_glob"])]
    streams = [(p["cn_launch"], p["cn_peak"], 5, 2041, p["cn_rate"], p["pos"]),
               (p["ex_launch"], p["ex_peak"], 5, 2042, p["roy"], pp * p["p_glob"])]
    return asset_cfs(costs, receipts, streams)


def scen(bear, base, bull):
    return {"bear": bear, "base": base, "bull": bull}


C3 = [(2026, 1, 1), (2027, 4, 1), (2028, 3, 1)]
ASSETS = {
    # 吸入剂型：2026-04 获 CDE IND，I 期；I 期后授权（推断）
    "Rentosertib 吸入（I 期）": scen(
        dict(costs=C3, receipts=[(2029, 10, 0.559 * 0.5)], streams=[(2035, 200, 5, 2044, 0.10, 0.05)]),
        dict(costs=C3, receipts=[(2029, 20, 0.559 * 0.5)], streams=[(2034, 300, 5, 2044, 0.10, 0.075)]),
        dict(costs=C3, receipts=[(2029, 40, 0.559 * 0.6)], streams=[(2033, 600, 5, 2044, 0.12, 0.10)])),
    # ISM5411：中国 IIa 期（UC），2027 顶线；同机制 GB004 曾在 UC II 期失败，成功率下调
    "Garutadustat ISM5411（IIa）": scen(
        dict(costs=[(2026, 2, 1), (2027, 5, 1)], receipts=[(2028, 30, 0.16), (2034, 150, 0.08)],
             streams=[(2034, 300, 5, 2042, 0.12, 0.08)]),
        dict(costs=[(2026, 2, 1), (2027, 5, 1)], receipts=[(2028, 50, 0.20), (2033, 150, 0.12)],
             streams=[(2033, 600, 5, 2042, 0.12, 0.12)]),
        dict(costs=[(2026, 2, 1), (2027, 5, 1)], receipts=[(2028, 100, 0.28), (2033, 200, 0.152)],
             streams=[(2033, 1200, 5, 2042, 0.12, 0.152)])),
    # ISM6331 pan-TEAD：I 期，FDA 快速通道；ESMO 2026-10-25 口头报告
    "ISM6331 pan-TEAD（I 期）": scen(
        dict(costs=[(2026, 2, 1), (2027, 8, 1), (2028, 6, 0.488)], receipts=[(2029, 20, 0.20), (2034, 60, 0.04)],
             streams=[(2034, 300, 5, 2042, 0.10, 0.04)]),
        dict(costs=[(2026, 2, 1), (2027, 8, 1), (2028, 6, 0.488)], receipts=[(2029, 40, 0.30), (2033, 100, 0.053)],
             streams=[(2033, 500, 5, 2042, 0.12, 0.053)]),
        dict(costs=[(2026, 2, 1), (2027, 8, 1), (2028, 6, 0.488)], receipts=[(2028, 100, 0.40), (2032, 150, 0.08)],
             streams=[(2032, 1000, 5, 2042, 0.14, 0.08)])),
    # ISM3412 MAT2A：I 期；MTA 协同 PRMT5 抑制剂竞争，成功率打 6 折
    "ISM3412 MAT2A（I 期）": scen(
        dict(costs=[(2026, 1.5, 1), (2027, 4, 1)], receipts=[(2028, 5, 0.15)],
             streams=[(2034, 200, 5, 2042, 0.10, 0.02)]),
        dict(costs=[(2026, 1.5, 1), (2027, 4, 1)], receipts=[(2028, 15, 0.25)],
             streams=[(2033, 300, 5, 2042, 0.10, 0.032)]),
        dict(costs=[(2026, 1.5, 1), (2027, 4, 1)], receipts=[(2028, 30, 0.35)],
             streams=[(2033, 600, 5, 2042, 0.12, 0.05)])),
    # ISM8969 脑渗透 NLRP3：与衡泰各 50%；衡泰剩余里程碑最高 5,600 万美元
    "ISM8969 NLRP3 50%（I 期）": scen(
        dict(costs=[(2026, 0.5, 1), (2027, 3, 1), (2028, 4, 0.5), (2030, 15, 0.10), (2031, 15, 0.10)],
             receipts=[(2028, 10, 0.4), (2031, 20, 0.10)], streams=[(2034, 400, 5, 2042, 0.10, 0.04)]),
        dict(costs=[(2026, 0.5, 1), (2027, 3, 1), (2028, 4, 0.5), (2030, 15, 0.15), (2031, 15, 0.15)],
             receipts=[(2028, 16, 0.5), (2031, 30, 0.15)], streams=[(2033, 800, 5, 2042, 0.125, 0.059)]),
        dict(costs=[(2026, 0.5, 1), (2027, 3, 1), (2028, 4, 0.5), (2030, 15, 0.20), (2031, 15, 0.20)],
             receipts=[(2028, 16, 0.6), (2031, 40, 0.20)], streams=[(2032, 1500, 5, 2042, 0.15, 0.08)])),
    # ISM8207 QPCTL：与复星 50/50 共担，I 期（中国）
    "ISM8207 QPCTL 50%（I 期）": scen(
        dict(costs=[(2026, 0.3, 1), (2027, 1, 1)], streams=[(2034, 200, 5, 2042, 0.10, 0.015)]),
        dict(costs=[(2026, 0.3, 1), (2027, 1, 1)], streams=[(2033, 300, 5, 2042, 0.10, 0.027)]),
        dict(costs=[(2026, 0.3, 1), (2027, 1, 1)], streams=[(2033, 500, 5, 2042, 0.10, 0.04)])),
    # ISM4808：大中华区授权太景（"双位数百万美元"），海外权益自留
    "ISM4808 PHD（太景大中华+海外）": scen(
        dict(receipts=[(2028, 1, 0.5)], streams=[(2035, 100, 5, 2042, 0.10, 0.03)]),
        dict(receipts=[(2028, 3, 0.5)], streams=[(2034, 150, 5, 2042, 0.10, 0.04)]),
        dict(receipts=[(2028, 5, 0.5)], streams=[(2033, 300, 5, 2042, 0.10, 0.06)])),
    # 已授权：XL309/ISM3091（Exelixis，2023 首付 8,000 万，已收首个 1,000 万里程碑；
    # 剩余研发里程碑 9,000 万、销售里程碑 7.75 亿、个位数中段至十几% 分成）
    "XL309 USP1（Exelixis）": scen(
        dict(receipts=[(2028, 20, 0.40), (2031, 30, 0.08), (2034, 40, 0.04), (2037, 80, 0.02)],
             streams=[(2034, 500, 5, 2042, 0.08, 0.04)]),
        dict(receipts=[(2028, 20, 0.488), (2030, 30, 0.12), (2033, 40, 0.053), (2036, 100, 0.026)],
             streams=[(2033, 800, 5, 2042, 0.10, 0.053)]),
        dict(receipts=[(2028, 20, 0.55), (2030, 30, 0.18), (2032, 40, 0.08), (2035, 150, 0.04)],
             streams=[(2032, 1500, 5, 2042, 0.12, 0.08)])),
    # MEN2312/ISM5043（Stemline/Menarini，KAT6；研发与注册里程碑 1.5 亿、销售 3.44 亿）
    "MEN2312 KAT6（Menarini）": scen(
        dict(receipts=[(2029, 20, 0.35), (2031, 40, 0.08), (2034, 90, 0.035), (2037, 60, 0.015)],
             streams=[(2034, 400, 5, 2042, 0.08, 0.035)]),
        dict(receipts=[(2028, 20, 0.45), (2030, 40, 0.11), (2033, 90, 0.05), (2036, 80, 0.025)],
             streams=[(2033, 600, 5, 2042, 0.10, 0.05)]),
        dict(receipts=[(2028, 20, 0.55), (2030, 40, 0.16), (2032, 90, 0.08), (2035, 150, 0.04)],
             streams=[(2032, 1200, 5, 2042, 0.12, 0.08)])),
    # MEN2501/ISM9682（Stemline/Menarini，KIF18A；总额 >5.5 亿，已收首付 2,000 万及首例给药里程碑）
    "MEN2501 KIF18A（Menarini）": scen(
        dict(receipts=[(2029, 15, 0.40), (2031, 35, 0.08), (2034, 50, 0.04), (2037, 60, 0.02)],
             streams=[(2034, 400, 5, 2042, 0.08, 0.04)]),
        dict(receipts=[(2028, 15, 0.488), (2030, 35, 0.12), (2033, 50, 0.053), (2036, 80, 0.026)],
             streams=[(2033, 600, 5, 2042, 0.10, 0.053)]),
        dict(receipts=[(2028, 15, 0.55), (2030, 35, 0.18), (2032, 50, 0.08), (2035, 120, 0.04)],
             streams=[(2032, 1200, 5, 2042, 0.12, 0.08)])),
}

# 合作框架剩余对价（总额 − 已知首付/近期款，US$M；均来自公司公告）
LILLY_REMAIN = 2750 - 115
OTHER_REMAIN = {
    "施维雅": 888 - 32, "武田": 600 - 60, "SK 生物制药": 2500 - 18,
    "齐鲁": 931 / USD_HKD, "康哲（2026-07）": 1200 / USD_CNY, "Tenacia 扩展": 94.75,
    "赛诺菲（已指定 3 个靶点）": 3 * 200.5,
}
OTHER_REMAIN_SUM = sum(OTHER_REMAIN.values())
FRAC_LILLY = scen(0.02, 0.04, 0.07)     # 名义兑现比例（推断）
FRAC_OTHER = scen(0.015, 0.03, 0.05)


def headline_cfs(remaining, frac):
    cfs = {}
    for y in range(2027, 2030):
        add(cfs, y, remaining * frac * 0.25 / 3 * (1 - tax(y)))
    for y in range(2030, 2034):
        add(cfs, y, remaining * frac * 0.35 / 4 * (1 - tax(y)))
    for y in range(2034, 2041):
        add(cfs, y, remaining * frac * 0.40 / 7 * (1 - tax(y)))
    return cfs


# 自有临床前组合：截至 2026-09-30 共提名 34 个 PCC，扣除已进临床/已授权约 14 个，余约 20 个
N_PCC = 20
PER_PCC = scen(4, 8, 16)   # 每个 PCC 名义净值（授权概率 × 首付+近期款 − 推进成本，推断）


def preclinical_cfs(sc):
    return {y: N_PCC * PER_PCC[sc] / 4 * (1 - tax(y)) for y in range(2027, 2031)}


# 平台与服务（可重复收入：药物发现合作研究费、软件/MMAI Gym、非医药发现）
PLAT_REV = {
    "bear": {2026: 30, 2027: 35, 2028: 38, 2029: 41, 2030: 44, 2031: 47},
    "base": {2026: 36, 2027: 50, 2028: 60, 2029: 70, 2030: 80, 2031: 90},
    "bull": {2026: 40, 2027: 65, 2028: 85, 2029: 105, 2030: 125, 2031: 145},
}
PLAT_MARGIN = scen(0.10, 0.20, 0.30)   # 成熟 EBIT 利润率，2029 年达到；2026 年为 0
PLAT_G = scen(0.020, 0.025, 0.025)


def platform_cfs(sc, r):
    m = PLAT_MARGIN[sc]
    path = {2026: 0.0, 2027: m / 3, 2028: 2 * m / 3, 2029: m, 2030: m, 2031: m}
    cfs = {}
    for y, rev in PLAT_REV[sc].items():
        f = Q4_FRAC if y == 2026 else 1.0
        cfs[y] = rev * path[y] * (1 - 0.15) * f
    g = PLAT_G[sc]
    cfs[2031] += cfs[2031] * (1 + g) / (r - g)
    return cfs


# 未分摊总部费用：2026H1 管理费用现金部分年化 15.2 + 管理费用股权激励年化 9.9 = 25.1；
# 2024/2025 管理费用（含股权激励）17.5/17.4（年报）→ 熊按现运行率、基准按正常化、牛再收缩
UNALLOC = scen(25, 20, 15)


def unalloc_cfs(sc, r):
    c = UNALLOC[sc]
    cfs = {2026: -c * Q4_FRAC}
    for y in range(2027, 2032):
        cfs[y] = -c
    cfs[2031] += -c / r
    return cfs


# 持续发现引擎（未来新 PCC）：发现研发投入路径（含可转债所列研发扩编），
# 净现值 = (回报倍数 − 1) × 投入现值；基准 1.0（不赋值也不扣费）
ENGINE_SPEND = {2027: 70, 2028: 80}
ENGINE_SPEND.update({y: 75 for y in range(2029, 2037)})
ENGINE_MULT = scen(0.6, 1.0, 1.5)


def engine_cfs(sc):
    return {y: (ENGINE_MULT[sc] - 1) * s for y, s in ENGINE_SPEND.items()}


# ---------------------------------------------------------------------------
# 5. 汇总
# ---------------------------------------------------------------------------
def components(sc, r):
    comp = {"Rentosertib 口服（中国 III 期+海外期权）": rentosertib_oral(sc)}
    for name, d in ASSETS.items():
        comp[name] = asset_cfs(**d[sc])
    comp["礼来剩余对价（概率化）"] = headline_cfs(LILLY_REMAIN, FRAC_LILLY[sc])
    comp["其他合作剩余对价（概率化）"] = headline_cfs(OTHER_REMAIN_SUM, FRAC_OTHER[sc])
    comp["自有临床前组合（约 20 个 PCC）"] = preclinical_cfs(sc)
    comp["平台与服务 DCF"] = platform_cfs(sc, r)
    comp["未分摊总部费用"] = unalloc_cfs(sc, r)
    comp["持续发现引擎净现值"] = engine_cfs(sc)
    return comp


def equity_value(sc, r):
    comp = components(sc, r)
    vals = {k: pv(v, r) for k, v in comp.items()}
    ev = sum(vals.values())
    eq = ev + NET_CASH + OPT_PROCEEDS
    v_debt = eq / DIL_SHARES * USD_HKD
    v_conv = (eq + CB_FACE) / (DIL_SHARES + CB_SHARES) * USD_HKD
    converted = v_conv > CB_CONV_HKD
    return vals, ev, eq, (v_conv if converted else v_debt), converted


def weighted_v(r):
    return sum(PROB[s] * equity_value(s, r)[3] for s in PROB)


def mkt_equity_usd():
    return PRICE_HKD * DIL_SHARES / USD_HKD


def irr_base():
    target = mkt_equity_usd()

    def f(r):
        comp = components("base", r)
        return sum(pv(v, r) for v in comp.values()) + NET_CASH + OPT_PROCEEDS - target

    lo, hi = PLAT_G["base"] + 0.005, 0.60
    if f(lo) < 0:
        return None, f(lo)
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2, None


def main():
    hk = lambda usd_m: usd_m * USD_HKD / DIL_SHARES   # 每股港元
    print("=== 英矽智能 03696.HK 独立估值（2026-10-08 收盘 48.24 港元）===")
    print(f"基本股数 {SHARES_BASIC:.2f}m；期权 {OPTIONS:.2f}m（行权款 US${OPT_PROCEEDS:.1f}m）；"
          f"未归属 RSU {RSU_UNVESTED:.2f}m（推断）；完全摊薄（不含可转债）{DIL_SHARES:.2f}m")
    print(f"可转债：面值 US${CB_FACE:.0f}m，转股价 HK${CB_CONV_HKD}，转股 {CB_SHARES:.2f}m 股"
          f"（占现股本 {CB_SHARES / SHARES_BASIC:.1%}）；含转股完全摊薄 {DIL_SHARES + CB_SHARES:.2f}m")
    print(f"上市以来股本：上市日 {SHARES_LISTING:.2f}m → 2026-09-30 {SHARES_BASIC:.2f}m（+{SHARES_BASIC / SHARES_LISTING - 1:.1%}）；"
          f"对上市前股份 {SHARES_PRE_IPO:.1f}m +{SHARES_BASIC / SHARES_PRE_IPO - 1:.1%}；"
          f"含期权/RSU/可转债潜在 {DIL_SHARES + CB_SHARES:.1f}m（较现股本 +{(DIL_SHARES + CB_SHARES) / SHARES_BASIC - 1:.1%}）")
    print(f"市值（基本股）HK${PRICE_HKD * SHARES_BASIC / 1000:.2f}bn = US${PRICE_HKD * SHARES_BASIC / USD_HKD:.0f}m；"
          f"完全摊薄 US${mkt_equity_usd():.0f}m")
    print()
    print("--- 收入质量（US$M）---")
    for k, d in REV.items():
        t5 = f"前五 {d['top5']:.1%} / 第一 {d['top1']:.1%}" if d["top5"] else "前五未披露（美国客户 90.2%）"
        print(f"{k}: 总收入 {d['total']:.1f}；可重复 {d['rep']:.1f}（{d['rep'] / d['total']:.0%}）；"
              f"一次性 {d['one']:.1f}（{d['one'] / d['total']:.0%}）；{t5}")
    for k, (ni, fv, lst, sbc) in PROFIT.items():
        econ = ni + fv + lst
        print(f"{k}: 净利润 {ni:+.1f}；公允价值变动 {fv:+.1f}；上市开支 {lst:.1f}；股权激励 {sbc:.1f}；"
              f"公司口径经调整 {ni + fv + lst + sbc:+.1f}；经济利润（保留股权激励）{econ:+.1f}")
    ex_one = PROFIT["2026H1"][0] - REV["2026H1"]["one"] * 0.95
    print(f"2026H1 剔除一次性收入（按 95% 落到利润）后的经营结果约 {ex_one:+.1f}，年化 {2 * ex_one:+.0f}（推断）")
    print()
    print("--- 经调整净现金（2026-06-30 + 7~9 月已披露事项，US$M）---")
    print(f"现金 {CASH:.1f} + 定存 {TERM_DEP:.1f} + 货基 {MMF:.1f} + 上市股权 {LISTED_EQ:.1f} + 可转债净募资 {CB_NET:.1f}"
          f" + Q3 期权行权 {Q3_OPT_HKD / USD_HKD:.1f} + Q3 经营现金流 {Q3_OCF:.1f}（推断）"
          f" − 借款 {BORROW:.1f} − 租赁 {LEASE:.1f} − 可转债面值 {CB_FACE:.1f}")
    print(f"经调整净现金 = US${NET_CASH:.1f}m = HK${NET_CASH * USD_HKD:.0f}m = 每股 HK${NET_CASH * USD_HKD / SHARES_BASIC:.2f}（基本股）"
          f"；毛流动性（可转债转股情形）US${GROSS_LIQ:.1f}m；未计：非上市股权 {UNLISTED_EQ:.1f}、合同负债 {CONTRACT_LIAB:.1f}")
    print("现金消耗（经营现金流+资本开支，US$M）：" + "；".join(f"{k} {v:+.1f}" for k, v in BURN.items()))
    print(f"2026H1 现金经营费用年化 {CASH_OPEX_RUN:.1f}；前瞻无新首付款年消耗约 {FWD_BURN:.0f}（推断）")
    print(f"现金跑道：按 2025 年消耗 {NET_CASH / -BURN['2025']:.1f} 年；按前瞻消耗 {NET_CASH / FWD_BURN:.1f} 年；"
          f"若可转债转股按前瞻 {GROSS_LIQ / FWD_BURN:.1f} 年")
    print()
    print(f"Rentosertib 中国峰值两来源：A（观研外推）US${PEAK_SRC_A:.0f}m；B（头豹外推）US${PEAK_SRC_B:.0f}m；取低 → {CN_PEAK_BASE:.0f}m"
          f"；海外峰值（取低市场 × 10%）US${EX_PEAK_BASE:.0f}m")
    print(f"合作剩余对价：礼来 US${LILLY_REMAIN:.0f}m；其他 US${OTHER_REMAIN_SUM:.0f}m（" +
          "、".join(f"{k} {v:.0f}" for k, v in OTHER_REMAIN.items()) + "）")
    print()

    res = {}
    names = None
    for s in ("bear", "base", "bull"):
        vals, ev, eq, v, conv = equity_value(s, R_BASE)
        res[s] = (vals, ev, eq, v, conv)
        names = list(vals.keys())
    print("--- 分部加总（折现率 10%，US$M；括号内为每股港元，按完全摊薄 {:.1f}m 股）---".format(DIL_SHARES))
    print(f"{'分部':<34}{'熊':>16}{'基准':>16}{'牛':>16}")
    for n in names:
        row = "".join(f"{res[s][0][n]:>9.1f}({hk(res[s][0][n]):>5.2f})" for s in ("bear", "base", "bull"))
        print(f"{n:<34}{row}")
    print(f"{'经营资产合计 EV':<34}" + "".join(f"{res[s][1]:>9.1f}({hk(res[s][1]):>5.2f})" for s in ("bear", "base", "bull")))
    print(f"{'+ 经调整净现金 + 期权行权款':<34}" + "".join(
        f"{NET_CASH + OPT_PROCEEDS:>9.1f}({hk(NET_CASH + OPT_PROCEEDS):>5.2f})" for _ in range(3)))
    print(f"{'股权价值':<34}" + "".join(f"{res[s][2]:>9.1f}({hk(res[s][2]):>5.2f})" for s in ("bear", "base", "bull")))
    groups = {
        "其他自有临床合计": ["Rentosertib 吸入（I 期）", "Garutadustat ISM5411（IIa）", "ISM6331 pan-TEAD（I 期）",
                      "ISM3412 MAT2A（I 期）", "ISM8969 NLRP3 50%（I 期）", "ISM8207 QPCTL 50%（I 期）",
                      "ISM4808 PHD（太景大中华+海外）"],
        "已授权临床合计": ["XL309 USP1（Exelixis）", "MEN2312 KAT6（Menarini）", "MEN2501 KIF18A（Menarini）"],
        "合作剩余对价合计": ["礼来剩余对价（概率化）", "其他合作剩余对价（概率化）"],
    }
    for g, keys in groups.items():
        print(f"{'  小计：' + g:<34}" + "".join(
            f"{sum(res[s][0][k] for k in keys):>9.1f}({hk(sum(res[s][0][k] for k in keys)):>5.2f})"
            for s in ("bear", "base", "bull")))
    print("每股价值 V（港元）：" + "；".join(
        f"{s} {res[s][3]:.2f}{'（按转股）' if res[s][4] else '（可转债按债务）'}" for s in ("bear", "base", "bull")))
    vw = weighted_v(R_BASE)
    print(f"情景概率：熊 {PROB['bear']:.0%} / 基准 {PROB['base']:.0%} / 牛 {PROB['bull']:.0%} → 概率加权独立 V = HK${vw:.2f}")
    pv_ratio = PRICE_HKD / vw
    band = ("明显低估" if pv_ratio <= 0.75 else "温和低估" if pv_ratio <= 0.90 else
            "大致合理" if pv_ratio <= 1.10 else "偏贵或价值陷阱风险高")
    print(f"独立 P/V = {PRICE_HKD} / {vw:.2f} = {pv_ratio:.2f} → {band}")
    print()
    print("--- 敏感性（概率加权 V，港元）---")
    for r in (0.09, 0.10, 0.11, 0.12):
        print(f"r={r:.0%}: V={weighted_v(r):.2f}  P/V={PRICE_HKD / weighted_v(r):.2f}  "
              f"（熊 {equity_value('bear', r)[3]:.2f} / 基准 {equity_value('base', r)[3]:.2f} / 牛 {equity_value('bull', r)[3]:.2f}）")
    print()
    print("--- 现价隐含回报与反向估值 ---")
    irr, gap_at_lo = irr_base()
    if irr is None:
        print(f"基准 IRR 不可算：折现率降至 {PLAT_G['base'] + 0.005:.1%}（终值公式下限）时现值仍比现价低 US${-gap_at_lo:.0f}m")
    else:
        print(f"基准情景隐含 IRR = {irr:.1%}")
    mkt = mkt_equity_usd()
    implied_ev = mkt - NET_CASH - OPT_PROCEEDS
    base_ev = res["base"][1]
    gap = implied_ev - base_ev
    pv_spend = pv({y: s for y, s in ENGINE_SPEND.items()}, R_BASE)
    print(f"现价隐含经营资产 EV = US${implied_ev:.0f}m；基准分部 EV = US${base_ev:.0f}m；缺口 US${gap:.0f}m")
    print(f"缺口折算：发现引擎回报倍数需 {1 + gap / pv_spend:.1f}x（基准 1.0x；未来 10 年发现投入现值 US${pv_spend:.0f}m）；"
          f"或自 2027 年起每年税后净交易现金流 US${gap * (R_BASE - 0.025) * (1 + R_BASE) ** (2027.5 - VAL_YEAR):.0f}m（永续、g=2.5%）")
    print(f"发现引擎倍数每 +1.0x ≈ 股权 +US${pv_spend:.0f}m ≈ 每股 +HK${pv_spend * USD_HKD / DIL_SHARES:.2f}")
    r100 = pv(rentosertib_oral("base", pos=1.0), R_BASE)
    r100b = pv(rentosertib_oral("bull", pos=1.0), R_BASE)
    rb = res["base"][0]["Rentosertib 口服（中国 III 期+海外期权）"]
    print(f"Rentosertib 口服：基准 PoS 25% 价值 US${rb:.0f}m；PoS=100%（基准销售）US${r100:.0f}m；"
          f"PoS=100%（牛市销售与条款）US${r100b:.0f}m —— 单靠该资产无法填补缺口")
    plat_b = res["base"][0]["平台与服务 DCF"]
    print(f"平台 DCF 交叉：基准 US${plat_b:.0f}m = 2026E 可重复收入 {PLAT_REV['base'][2026]} 的 {plat_b / PLAT_REV['base'][2026]:.1f} 倍；"
          f"现价隐含 EV / 2026E 可重复收入 = {implied_ev / PLAT_REV['base'][2026]:.0f} 倍；"
          f"/ 2026H1 年化总收入 212.6 = {implied_ev / 212.6:.1f} 倍；/ 2025 收入 56.2 = {implied_ev / 56.239:.0f} 倍")
    print(f"参照：IPO 价 HK$24.05（上市日市值 HK${24.05 * SHARES_LISTING / 1000:.1f}bn）；可转债转股价 HK${CB_CONV_HKD}"
          f"（现价折让 {PRICE_HKD / CB_CONV_HKD - 1:.1%}）")
    print()
    print("--- 正文引用的其他数字 ---")
    mcap_usd = PRICE_HKD * SHARES_BASIC / USD_HKD
    print(f"EV（基本股市值 − 经调整净现金）= US${mcap_usd - NET_CASH:.0f}m；EV/2025 收入 {(mcap_usd - NET_CASH) / 56.239:.1f}x；"
          f"EV/2026H1 年化收入 {(mcap_usd - NET_CASH) / 212.606:.1f}x")
    upfront_2026 = 115 + 32 + 10 + 60 + 18   # 礼来、施维雅（上限）、衡泰、武田（约）、SK（上限）
    upfront_2225 = 7 + 12.5 + 80 + 12 + 20 + 15.3   # 复星 QPCTL、赛诺菲、Exelixis、Stemline×2、2025 管线首付（推断）
    print(f"2026 年已公告首付＋近期款合计约 US${upfront_2026}m；2022–2025 年资产首付年均约 US${upfront_2225 / 4:.0f}m（推断）")
    print(f"2026H1 股权激励 15.690 vs 2025H1 1.467 = {15.690 / 1.467:.1f} 倍；2026H1 软件收入年化 {2.697 * 2:.1f}；"
          f"现金+定存+货基 {CASH + TERM_DEP + MMF:.1f}；2026H1 管理费用年化（含股权激励）{12.577 * 2:.1f}")
    print(f"牛市 V 较现价 {res['bull'][3] / PRICE_HKD - 1:.1%}；合同总额兑现率 308/11000 = {308 / 11000:.1%}")


if __name__ == "__main__":
    main()
