"""688235 百济神州（BeOne Medicines）独立估值（OI-291 b13，价格日 2026-10-20）。

运行：python3 valuation.py
口径：经营模型以美元（百万）建模（公司报告货币为美元，指引为美元），最后按 USD/CNY 6.722 折成人民币。
所有者收益 = 经营利润（剔除安进 IMDELLTRA 特许权使用费收入，股份支付照常作费用）×(1-税率) - (资本开支-折旧 + 营运资金增量)。
特许权使用费已售予 Royalty Pharma（无追索，只以该特许权使用费偿付）：收入与实际利率法利息同时剔除，负债不再扣除。
经调整净现金为正，按无杠杆口径：经营价值 + 经调整净现金（已全额扣除有息负债与租赁）+ 非经营资产。
"""

# ---------------- 快照与换算 ----------------
PRICE_A = 262.00            # 元，科创板 2026-10-20 收盘（brief）
SHARES_M = 1542.29          # 百万股，brief 总股本 15.4229 亿（含子公司为股权激励持有的预留股）
RESERVED_M = 71.697         # 百万股，2026-06-30 子公司为股权激励持有的已发行未流通股（2026H1_report 第 89-90 页）
FX = 6.722                  # USD/CNY，中国外汇交易中心中间价 2026-10-16（网络，10-20 未查到）
FX_H1 = 6.904               # 2026H1 平均（CAS 营收 222.19 亿 / US GAAP 32.185 亿美元）
FX_H2 = 6.75                # 2026H2 折算假设
ADS_PRICE_USD = 369.06      # ONC 2026-10-16 收盘（Yahoo，网络）；1 ADS = 13 股
ADS_RATIO = 13

# ---------------- 2026H1 实际（US GAAP，百万美元；2026H1_report 第 13-22、86-92 页） ----------------
H1 = dict(rev=3218.509, prod=3167.123, other=51.386, amgen_roy=37.120, cogs=341.745,
          rd=1153.504, sga=1148.311, op=574.949, int_inc=55.564, int_exp=72.626,
          oth=13.787, pretax=571.674, tax=107.310, ni=464.364, sbc=260.815, da=81.659,
          capex=68.265, ocf=664.156, onetime_tax=52.8)
CAS_H1_NP_YI = 16.08 + 16.63          # 亿元，数据包单季表（CAS 归母）
CAS_MINUS_GAAP_H1_YI = CAS_H1_NP_YI - H1['ni'] * FX_H1 / 100   # CAS 与 US GAAP 的 H1 差额（亿元）

# ---------------- 2026-06-30 资产负债（百万美元；2026H1_report 第 88-89、23-26、33 页） ----------------
CASH = 5098.041             # 现金及现金等价物（不含受限）
RESTRICTED = 161.046 + 21.587   # 受限现金：多为结算员工股权激励代扣税款与信用证保证金，不计入
DEBT = 190.896 + 882.163    # 短期借款 + 长期借款（银团 A/B 段）
LEASES = 21.953 + 48.200    # 经营租赁负债
UTP_ETC = 127.367 / 6.99 + 1.21 * 100 / 6.81   # 美国不确定税务状况（2025 年报第 233 页，千元→百万美元）+ 长期应付职工薪酬 1.21 亿
OP_RESERVE = 410.0          # 经营备付：约 1 个月现金成本（营业成本+费用-折旧-股份支付 ≈ 49.5 亿美元/年）
ROYALTY_LIAB = 89.278 + 817.035   # 未来特许权使用费出售负债（不扣，见说明）
NONOP = (1.58 + 2.91) * 100 / 6.81  # 长期股权投资 + 其他非流动金融资产（数据包，亿元→百万美元）

NET_CASH_ADJ = CASH - OP_RESERVE - DEBT - LEASES - UTP_ETC   # 无杠杆口径经调整净现金（百万美元）

# ---------------- 情景参数 ----------------
YEARS = list(range(2027, 2041))
SCEN = {
    'bear': dict(
        p=0.25, op2026=1000.0, bru2026=4950.0, oth2026=1650.0,
        bru_g=[0.08, 0.04, 0.01, -0.02, -0.03, -0.03, -0.04, -0.07, -0.06, -0.10, -0.30, -0.50, -0.40, -0.25],
        oth_g=[0.04, 0.08, 0.10, 0.10, 0.10, 0.08, 0.07, 0.06, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03],
        margin=[0.16, 0.18, 0.195, 0.205, 0.215, 0.22, 0.22, 0.22, 0.22, 0.21, 0.18, 0.16, 0.16, 0.17],
        term_margin=0.18, g=0.020),
    'base': dict(
        p=0.50, op2026=1080.0, bru2026=5000.0, oth2026=1672.0,
        bru_g=[0.17, 0.11, 0.07, 0.05, 0.03, 0.02, 0.00, -0.03, -0.03, -0.06, -0.28, -0.50, -0.40, -0.25],
        oth_g=[0.12, 0.18, 0.22, 0.22, 0.20, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03],
        margin=[0.18, 0.22, 0.25, 0.275, 0.295, 0.305, 0.31, 0.31, 0.31, 0.30, 0.27, 0.24, 0.24, 0.25],
        term_margin=0.25, g=0.025),
    'bull': dict(
        p=0.25, op2026=1150.0, bru2026=5050.0, oth2026=1690.0,
        bru_g=[0.21, 0.15, 0.11, 0.08, 0.06, 0.04, 0.03, 0.00, 0.00, -0.03, -0.20, -0.40, -0.30, -0.20],
        oth_g=[0.15, 0.25, 0.28, 0.28, 0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04],
        margin=[0.20, 0.25, 0.29, 0.32, 0.34, 0.35, 0.36, 0.36, 0.36, 0.35, 0.33, 0.30, 0.30, 0.30],
        term_margin=0.30, g=0.025),
}
TAX = {2026: 0.13, 2027: 0.14, 2028: 0.15, 2029: 0.16, 2030: 0.17}   # 之后 18%
TAX_LT = 0.18
K_UP = 0.15      # 收入增加时：(资本开支-折旧)+营运资金 = 15% × 收入增量
K_DOWN = 0.07    # 收入下降时：营运资金释放 7% × 收入减量
BRU_TAIL_DECAY = 0.25   # 2040 年后百悦泽残余收入每年 -25%
AMGEN_ROY_2026 = 78.0   # 2026 全年安进特许权使用费收入估计（H1 37.1），剔除
ROY_INT_2026 = 110.0    # 2026 全年特许权使用费负债利息（H1 30 付 + 25 计提）


def tax(y):
    return TAX.get(y, TAX_LT)


def build(s):
    """返回逐年 (年份, 营收, 百悦泽, 其他, 经营利润, NOPAT, 再投资, 所有者收益)。"""
    rev26 = s['bru2026'] + s['oth2026']
    op26_ex = s['op2026'] - AMGEN_ROY_2026
    rows = [(2026, rev26, s['bru2026'], s['oth2026'], op26_ex, op26_ex * (1 - tax(2026)), None, None)]
    bru, oth, prev = s['bru2026'], s['oth2026'], rev26
    for i, y in enumerate(YEARS):
        bru *= 1 + s['bru_g'][i]
        oth *= 1 + s['oth_g'][i]
        rev = bru + oth
        op = rev * s['margin'][i]
        nopat = op * (1 - tax(y))
        d = rev - prev
        reinv = K_UP * d if d > 0 else K_DOWN * d
        rows.append((y, rev, bru, oth, op, nopat, reinv, nopat - reinv))
        prev = rev
    return rows


def oe_2026_full(s):
    rows = build(s)
    rev26 = rows[0][1]
    reinv26 = K_UP * (rev26 - 5360.0)   # 2025 经营收入约 53.6 亿美元（剔除特许权使用费）
    return rows[0][5] - reinv26


def value(s, r, g=None, detail=False):
    g = s['g'] if g is None else g
    rows = build(s)
    # 2026H2 所有者收益（H1 已含在 6-30 现金里）：全年减 H1
    h1_op_ex = H1['op'] - H1['amgen_roy']
    oe26_full = oe_2026_full(s)
    h1_oe = h1_op_ex * (1 - tax(2026)) - (H1['capex'] - H1['da'])  # H1 部分按实际净资本开支
    oe26_h2 = oe26_full - h1_oe
    pv = oe26_h2  # t≈0
    pv_rows = []
    for (y, rev, bru, oth, op, nopat, reinv, oe) in rows[1:]:
        t = (y - 2027) + 0.70
        df = (1 + r) ** -t
        pv += oe * df
        pv_rows.append((y, oe, df))
    # 终值：其他业务按 g 永续；百悦泽残余按 -25%/年衰减；二者用终值利润率
    y_last = rows[-1]
    rev40, bru40, oth40 = y_last[1], y_last[2], y_last[3]
    m, t_lt = s['term_margin'], TAX_LT
    oth41 = oth40 * (1 + g)
    oe_oth41 = oth41 * m * (1 - t_lt) - K_UP * (oth41 - oth40)
    bru41 = bru40 * (1 - BRU_TAIL_DECAY)
    oe_bru41 = bru41 * m * (1 - t_lt) - K_DOWN * (bru41 - bru40)
    tv = oe_oth41 / (r - g) + oe_bru41 / (r + BRU_TAIL_DECAY)
    t_tv = (2040 - 2027) + 0.70 + 0.5
    pv_tv = tv * (1 + r) ** -t_tv
    ev = pv + pv_tv
    eq = ev + NET_CASH_ADJ + NONOP
    v_cny = eq * FX / SHARES_M
    if detail:
        return dict(rows=rows, pv_explicit=pv, pv_tv=pv_tv, ev=ev, eq=eq, v=v_cny,
                    tv_share=pv_tv / ev, oe26_full=oe26_full, oe26_h2=oe26_h2)
    return v_cny


def weighted(r, overrides=None):
    tot = 0.0
    for k, s in SCEN.items():
        ss = dict(s)
        if overrides and k in overrides:
            ss.update(overrides[k])
        tot += ss['p'] * value(ss, r)
    return tot


def solve(f, lo, hi, target, it=200):
    flo = f(lo) - target
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_dcf(price_cny, r=0.09, g_term=0.025):
    """现价隐含：以 2026 正常化所有者收益为基数，10 年（2027-2036）恒定增速后接 2.5% 永续。"""
    base = SCEN['base']
    oe0 = oe_2026_full(base)
    target_eq = price_cny * SHARES_M / FX
    target_ev = target_eq - NET_CASH_ADJ - NONOP

    def ev_at(gr):
        pv, oe = 0.0, oe0
        for i in range(10):
            oe *= 1 + gr
            pv += oe * (1 + r) ** -(i + 0.70)
        tv = oe * (1 + g_term) / (r - g_term)
        return pv + tv * (1 + r) ** -(9 + 0.70 + 0.5)
    g10 = solve(ev_at, -0.2, 0.6, target_ev)

    def ev_perp(gp):  # 永续增速（从 2027 起恒定）
        oe1 = oe0 * (1 + gp)
        return oe1 / (r - gp) * (1 + r) ** 0.30
    gp = solve(ev_perp, -0.05, r - 0.001, target_ev)
    return g10, gp, oe0


def implied_irr(price_cny, s=None):
    s = SCEN['base'] if s is None else s
    return solve(lambda r: value(s, r), 0.03, 0.30, price_cny)


def normalized_np_2026_yi(s):
    """2026 正常化归母净利（报表 CAS 口径，含净利息与特许权使用费的报表处理，剔除一次性项目），亿元。"""
    op = s['op2026']
    int_inc, int_exp, oth = 115.0, 35.0 + ROY_INT_2026, 25.0
    pretax = op + int_inc - int_exp + oth
    h2_pretax = pretax - H1['pretax']
    h2_ni = h2_pretax * (1 - tax(2026))
    ni_gaap = H1['ni'] + h2_ni
    one_off = H1['onetime_tax'] - 20.0 * (1 - tax(2026))   # 中国子公司税务稽查和解（+）、Q1 非经常性毛转净调整（-）
    cas_yi = CAS_H1_NP_YI + h2_ni * FX_H2 / 100 + CAS_MINUS_GAAP_H1_YI   # H2 差额同 H1
    norm_yi = cas_yi + one_off * FX_H1 / 100
    return dict(ni_gaap=ni_gaap, cas_2026e_yi=cas_yi, norm_yi=norm_yi, pretax=pretax)


def main():
    print('=== 688235 百济神州 独立估值（价格日 2026-10-20） ===')
    print(f'A股价 {PRICE_A:.2f} 元；总股本 {SHARES_M/100:.4f} 亿股；USD/CNY {FX}；A股价×总股本 {PRICE_A*SHARES_M/100:,.1f} 亿元')
    ads_cny = ADS_PRICE_USD / ADS_RATIO * FX
    print(f'ADS {ADS_PRICE_USD} 美元/13 股 → 每股 {ADS_PRICE_USD/ADS_RATIO:.2f} 美元 = {ads_cny:.2f} 元；A股相对 ADS 溢价 {PRICE_A/ads_cny-1:.1%}')
    print(f'经调整净现金（无杠杆）{NET_CASH_ADJ:,.0f} 百万美元 = {NET_CASH_ADJ*FX/100:,.1f} 亿元；'
          f'非经营资产 {NONOP*FX/100:.1f} 亿元；特许权使用费出售负债（不扣）{ROYALTY_LIAB*FX/100:.1f} 亿元')
    print(f'  现金 {CASH:,.0f} − 经营备付 {OP_RESERVE:,.0f} − 有息负债 {DEBT:,.0f} − 租赁 {LEASES:,.0f} − 税务等 {UTP_ETC:,.0f}（受限现金 {RESTRICTED:,.0f} 未计入现金）')
    print()
    res = {}
    for k, s in SCEN.items():
        d = value(s, 0.09, detail=True)
        res[k] = d
        print(f'[{k}] p={s["p"]:.2f}  V={d["v"]:.2f} 元/股  EV={d["ev"]*FX/100:,.0f} 亿元  终值占 EV {d["tv_share"]:.1%}  '
              f'2026 全年所有者收益 {d["oe26_full"]:,.0f} 百万美元，2026H2 {d["oe26_h2"]:,.0f}')
        print('   年份  营收  百悦泽  其他  经营利润  NOPAT  再投资  所有者收益  OE增速')
        prev_oe = d['oe26_full']
        for (y, rev, bru, oth, op, nopat, reinv, oe) in d['rows']:
            if y == 2026:
                print(f'   {y} {rev:7,.0f} {bru:7,.0f} {oth:6,.0f} {op:8,.0f} {nopat:7,.0f}      —   {prev_oe:8,.0f}')
                continue
            print(f'   {y} {rev:7,.0f} {bru:7,.0f} {oth:6,.0f} {op:8,.0f} {nopat:7,.0f} {reinv:6,.0f} {oe:9,.0f}  {oe/prev_oe-1:6.1%}')
            prev_oe = oe
    vw = sum(SCEN[k]['p'] * res[k]['v'] for k in SCEN)
    pv = PRICE_A / vw
    tier = '明显低估' if pv <= 0.75 else '温和低估' if pv <= 0.90 else '大致合理' if pv <= 1.10 else '偏贵或价值陷阱风险高'
    print()
    print(f'加权 V = {vw:.2f} 元/股；P/V = {pv:.3f} → {tier}')
    print(f'剔除预留股（{(SHARES_M-RESERVED_M)/100:.4f} 亿股）对照：V = {vw*SHARES_M/(SHARES_M-RESERVED_M):.2f}，P/V = {PRICE_A/(vw*SHARES_M/(SHARES_M-RESERVED_M)):.3f}')
    print(f'ADS 折算价 {ads_cny:.2f} 元 / V = {ads_cny/vw:.3f}；每 ADS 价值 {vw/FX*ADS_RATIO:.1f} 美元')
    v8, v10 = weighted(0.08), weighted(0.10)
    print(f'股权成本 8%：加权 V = {v8:.2f}（P/V {PRICE_A/v8:.3f}）；10%：加权 V = {v10:.2f}（P/V {PRICE_A/v10:.3f}）')
    for k in SCEN:
        print(f'   {k}: 8% {value(SCEN[k],0.08):.2f}  9% {res[k]["v"]:.2f}  10% {value(SCEN[k],0.10):.2f}')
    irr = implied_irr(PRICE_A)
    irr_ads = implied_irr(ads_cny)
    print(f'现价隐含回报（基准情景现金流）：A股 {irr:.2%}；ADS 折算价 {irr_ads:.2%}')
    g10, gp, oe0 = reverse_dcf(PRICE_A)
    g10a, gpa, _ = reverse_dcf(ads_cny)
    print(f'反向 DCF（9%，2026 正常化所有者收益 {oe0:,.0f} 百万美元为基数）：A股价隐含 10 年增速 {g10:.1%} 后接 2.5%，或永续增速 {gp:.2%}；'
          f'ADS 折算价隐含 10 年 {g10a:.1%}、永续 {gpa:.2%}')
    print()
    for k, s in SCEN.items():
        n = normalized_np_2026_yi(s)
        print(f'2026 正常化归母净利 [{k}]：{n["norm_yi"]:.1f} 亿元（CAS 2026E 报表 {n["cas_2026e_yi"]:.1f}；US GAAP 净利 {n["ni_gaap"]:,.0f} 百万美元）')
    # 增长路径（基准）
    rows = res['base']['rows']
    oe = [res['base']['oe26_full']] + [r_[7] for r_ in rows[1:6]]
    gpath = [oe[i + 1] / oe[i] - 1 for i in range(5)]
    reinv = sum(r_[6] for r_ in rows[1:6]); nop = sum(r_[5] for r_ in rows[1:6])
    d_nopat = rows[5][5] - rows[0][5]
    print('基准所有者收益增速 2027-2031：' + '、'.join(f'{x:.1%}' for x in gpath))
    print(f'基准再投资率（有形：资本开支净额+营运资金，2027-2031）{reinv/nop:.1%}；增量回报（ΔNOPAT 2026→2031 / 有形再投资）{d_nopat/reinv:.0%}')
    rd = [0.36, 0.33, 0.31, 0.29, 0.27]   # 研发费率路径（2026-2030，说明用）
    rd_cum = sum(rows[i][1] * rd[i] * (1 - tax(2026 + i)) for i in range(5))
    print(f'含研发的经济再投资：2026-2030 税后研发约 {rd_cum:,.0f} 百万美元 + 有形 {reinv:,.0f}；ΔNOPAT/(两者合计) = {d_nopat/(rd_cum+reinv):.0%}')
    # 证伪情景
    print()
    fz = {
        '百悦泽增速失速（2027H1 全球同比 <10%）→ 熊 0.5／基 0.5／牛 0': dict(bear=dict(p=0.5), base=dict(p=0.5), bull=dict(p=0.0)),
        '美国净价下调 ≥15%（MFN/GUARD 扩至联邦医保）→ 百悦泽各年 -15%、利润率 -3pp': None,
        'CELESTIAL-301 PFS 失败且 tacabrutideg 3 期失败 → 其他业务增速各年 ×0.6': None,
        '2027 GAAP 经营利润率 <15%（费用失控）→ 各情景利润率路径 -3pp': None,
        '仿制药提前至 2034 年进入美国 → 百悦泽 2034 起断崖': None,
    }
    out = {}
    k1 = list(fz)[0]
    out[k1] = weighted(0.09, fz[k1])
    # 价格冲击
    def shock_price(s):
        ss = dict(s)
        ss['bru2026'] = s['bru2026']
        ss['bru_g'] = [s['bru_g'][0] - 0.15] + s['bru_g'][1:]
        ss['margin'] = [m_ - 0.03 for m_ in s['margin']]
        ss['term_margin'] = s['term_margin'] - 0.01
        return ss
    def shock_pipe(s):
        ss = dict(s); ss['oth_g'] = [x * 0.6 for x in s['oth_g']]; return ss
    def shock_margin(s):
        ss = dict(s); ss['margin'] = [m_ - 0.03 for m_ in s['margin']]; ss['term_margin'] = s['term_margin'] - 0.03; return ss
    def shock_loe(s):
        ss = dict(s); g_ = list(s['bru_g'])
        g_[7], g_[8], g_[9], g_[10], g_[11], g_[12], g_[13] = -0.30, -0.50, -0.40, -0.25, -0.15, -0.10, -0.10
        ss['bru_g'] = g_; return ss
    for name, fn in zip(list(fz)[1:], [shock_price, shock_pipe, shock_margin, shock_loe]):
        out[name] = sum(SCEN[k]['p'] * value(fn(SCEN[k]), 0.09) for k in SCEN)
    out['上行：2027 年营收 ≥ 85 亿美元且 GAAP 经营利润率 ≥ 22% → 熊 0／基 0.5／牛 0.5'] = weighted(0.09, dict(bear=dict(p=0.0), base=dict(p=0.5), bull=dict(p=0.5)))
    out['上行：tacabrutideg 对匹妥布替尼 3 期成功且 ZS 固定疗程获批 → 全部按牛市情景'] = value(SCEN['bull'], 0.09)
    for k_, v_ in out.items():
        print(f'证伪：{k_}：V = {v_:.2f}（P/V {PRICE_A/v_:.3f}）')
    # 三季度估计（基准，三季报 2026-11-10 预约）
    s_ = SCEN['base']
    h2_rev = s_['bru2026'] + s_['oth2026'] + AMGEN_ROY_2026 - H1['rev']
    h2_op = s_['op2026'] - H1['op']
    q3_rev, q3_op = h2_rev * 0.49, h2_op * 0.49
    q3_ni = (q3_op + 30 - 36 + 6) * (1 - tax(2026))
    print(f'2026Q3 估计（基准）：营收 {q3_rev:,.0f} 百万美元 ≈ {q3_rev*6.73/100:.1f} 亿元；GAAP 经营利润 {q3_op:,.0f}；净利 {q3_ni:,.0f} 百万美元 ≈ {q3_ni*6.73/100:.1f} 亿元（2025Q3 CAS 归母 6.89 亿）')
    # 进入各档的价格（V 不变）
    print()
    print(f'V 不变时各档价格：≤{0.75*vw:.1f} 明显低估；{0.75*vw:.1f}～{0.90*vw:.1f} 温和低估；{0.90*vw:.1f}～{1.10*vw:.1f} 大致合理；>{1.10*vw:.1f} 偏贵')
    # 特许权使用费对照
    roy_alt = (- ROYALTY_LIAB + 1.15 * ROYALTY_LIAB) * FX / SHARES_M
    print(f'对照：若把特许权使用费负债按账面全扣、同时计入 9% 折现的特许权使用费现值（约账面 1.15 倍），每股 V 约变动 {roy_alt:+.2f} 元')


if __name__ == '__main__':
    main()
