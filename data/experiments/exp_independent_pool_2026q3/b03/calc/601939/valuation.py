#!/usr/bin/env python3
"""601939 建设银行 独立估值（OI-291 b03，深度版）。

方法：杜邦驱动的盈利预测 → 股利折现（DDM）与剩余收益（RI，P/B–ROE）互校。
- 2026 年＝上半年实际（2026H1_report）＋下半年预测；2027–2035 年逐年预测；
  2036 年起进入稳态（各比率不变，派息率 = 1 − g/ROE，账面与利润按 g 增长），
  稳态用 200 年长期模拟求和，DDM 与 RI 共用同一组预测，不用闭式终值，避免口径不一致。
- 每股价值按全部普通股 2,616.0038 亿股（A 211.8306 + H 2,404.1732，2026H1_report 第 72 页）。
- 金额单位亿元；价格与 V 为元/股。银行不做净现金调整。

python3 valuation.py 打印三情景 V、加权 V、P/V、8%/10% 下的 V、隐含回报与反向推算。
"""
from datetime import date

# ------------------------------------------------------------------ 统一快照
PRICE = 11.57                     # 2026-10-19 A 股收盘（brief.md）
SHARES = 2616.0038                # 亿股，A+H 全部普通股（2026H1_report 第 72 页 261,600,381,459 股）
T0 = date(2026, 10, 19)
COE = 0.09
PROBS = {'bear': 0.25, 'base': 0.50, 'bull': 0.25}

# ------------------------------------------------------------------ 公告数据（亿元）
A_YE25 = 456318.18                # 2025-12-31 资产总额（2026H1_report 第 8 页）
A_H1 = 473282.44                  # 2026-06-30 资产总额（同上）
B_YE25 = 36634.11 - 1999.77       # 2025-12-31 归属普通股东权益 = 归母权益 − 其他权益工具（第 29 页）
B_H1 = 38101.82 - 2299.77         # 2026-06-30 归属普通股东权益 35,802.05（第 29、203 页）
# 2026 上半年实际（第 12、17–19、219–220 页）
H1 = dict(nii=3109.58, fee=642.89, oth=612.82, opex=937.26, credit=1300.28,
          costs=44.43 + 103.28,   # 税金及附加 + 其他业务成本
          parent=1695.64, at1=7.96)
# 2025 下半年 = 2025 全年（2025_annual_report 第 24、29–31 页）− 2025 上半年（2026H1_report 第 12–19 页）
H2_25 = dict(fee=1103.07 - 652.18, oth=779.68 - 423.46, opex=2156.78 - 908.63,
             credit=1333.17 - 1076.52, parent=3389.06 - 1620.76)
INTERIM_2026 = 525.82             # 2026 中期股息每 10 股 2.010 元（dividend_20260829_643785）
# 其他权益工具：优先股 600 亿 3.57%（12 月付息）、永续债 400 亿 3.20%（8 月）、300 亿 3.29%（7 月）、
# 300 亿 3.37%（9 月）、400 亿 1.99%（5 月）、300 亿 1.92%（6 月，首付 2027）（第 198–203 页），
# 2026-09-22 另发永续债 400 亿 1.83%（2026-09-24 发行完毕公告），合计 2,699.77 亿
AT1_H2_2026 = 21.42 + 12.80 + 9.87 + 10.11
AT1_BAL = 2699.77

# ------------------------------------------------------------------ 结构参数
KAPPA = 0.985        # 平均生息资产 / 期初期末平均总资产（2026H1：45,793 亿 ÷ 46,480 亿）
LAMBDA = 0.61        # 平均贷款 / 平均总资产（2025 年 0.63，2026H1 0.616，债券占比上升）
LOANS_2026 = 291000  # 2026 年平均贷款（上半年 28.64 万亿，下半年约 29.6 万亿）
COSTS_R = 0.00067    # 税金及附加 + 其他业务成本 / 平均总资产（2025 年 0.070%，2026H1 0.064%）
COSTS_H2_2026 = 180.0  # 2026 下半年税金及附加 + 其他业务成本（2025 下半年 170.75）
BIZ_R = 0.00045      # 其中其他业务成本（成本收入比分母扣除项）
MI = 0.007           # 少数股东损益 / 净利润（2025 年 0.3%，2026H1 1.2%）
S_H1 = 0.485         # 上半年归母净利占全年（2023–2025 年 50.3%/49.0%/47.8%）
AT1_COUPON = {2027: 75.24 / AT1_BAL, 2028: 0.0245}  # 2027 起 2022 永续债可赎回、优先股重定价
AT1_COUPON_LR = 0.0230
YEARS = list(range(2027, 2036))
HORIZON = 2235       # 稳态长期模拟终点

SCEN = {
    'base': dict(
        label='基准', gA26=0.065, nimH2=0.0136, feeH2=460.0, othH2=340.0, opexH2g=0.03, creditH2=430.0, taxH2=0.13,
        nim={2027: 0.0134, 2028: 0.0132}, nim_lr=0.0130,
        feeg=0.03, theta={2027: 0.0014}, theta_lr=0.0013, cir=0.28,
        cc={2027: 0.0058}, cc_lr=0.0055, tax=0.125,
        p26=0.31, pol={2027: 0.31, 2028: 0.31}, ramp_from=2028, g_T=0.025),
    'bear': dict(
        label='熊', gA26=0.06, nimH2=0.0134, feeH2=445.0, othH2=280.0, opexH2g=0.04, creditH2=520.0, taxH2=0.13,
        nim={2027: 0.0128, 2028: 0.0124}, nim_lr=0.0120,
        feeg=0.01, theta={}, theta_lr=0.0010, cir=0.30,
        cc={2027: 0.0080, 2028: 0.0080, 2029: 0.0072}, cc_lr=0.0068, tax=0.13,
        p26=0.30, pol={y: 0.30 for y in YEARS}, ramp_from=None, g_T=0.02),
    'bull': dict(
        label='牛', gA26=0.07, nimH2=0.0137, feeH2=470.0, othH2=380.0, opexH2g=0.02, creditH2=330.0, taxH2=0.13,
        nim={2027: 0.0138}, nim_lr=0.0138,
        feeg=0.05, theta={2027: 0.0015}, theta_lr=0.0014, cir=0.27,
        cc={2027: 0.0052}, cc_lr=0.0048, tax=0.12,
        p26=0.31, pol={2027: 0.33, 2028: 0.35}, ramp_from=2028, g_T=0.025),
}


def yf(d1, d2):
    return (d2 - d1).days / 365.0


def project(name, mods=None):
    """返回 2026–2235 年预测：年度行、半年 RI 序列与现金股利（日期, 金额）。mods 用于证伪与反向推算。"""
    s = dict(SCEN[name])
    if mods:
        s.update(mods)
    nim_shift = s.get('nim_shift', 0.0)
    cc_shift = s.get('cc_shift', 0.0)
    roe_x = s.get('roe_override')           # 反向推算：2027 年起普通股 ROE（期初权益）固定
    # ---- 2026：上半年实际 + 下半年预测 ----
    A26 = A_YE25 * (1 + s['gA26'])
    avgA_h2 = (A_H1 + A26) / 2
    nii_h2 = s['nimH2'] * KAPPA * avgA_h2 * 184 / 365
    rev_h2 = nii_h2 + s['feeH2'] + s['othH2']
    opex_h2 = H2_25['opex'] * (1 + s['opexH2g'])
    pbt_h2 = rev_h2 - COSTS_H2_2026 - opex_h2 - s['creditH2']
    parent_h2 = pbt_h2 * (1 - s['taxH2']) * (1 - MI)
    common_h2 = parent_h2 - AT1_H2_2026
    parent26 = H1['parent'] + parent_h2
    common26 = parent26 - H1['at1'] - AT1_H2_2026
    final26 = s['p26'] * parent26 - INTERIM_2026
    B26 = B_H1 + common_h2 - INTERIM_2026
    L = A26 / B26                                  # 年末资产/普通股权益，此后保持不变
    avgA26 = (A_YE25 + A26) / 2
    nii26, fee26, oth26 = H1['nii'] + nii_h2, H1['fee'] + s['feeH2'], H1['oth'] + s['othH2']
    opex26, credit26 = H1['opex'] + opex_h2, H1['credit'] + s['creditH2']
    rev26 = nii26 + fee26 + oth26
    costs26 = H1['costs'] + COSTS_H2_2026
    # 2026 正常化：其他非息收入与信用成本取情景长期口径，税率取长期口径，其余取 2026 预测
    pbt_norm = nii26 + fee26 + s['theta_lr'] * avgA26 - costs26 - opex26 - s['cc_lr'] * LOANS_2026
    parent_norm26 = pbt_norm * (1 - s['tax']) * (1 - MI)
    y26 = dict(y=2026, parent=parent26, common=common26, nii=nii26, fee=fee26, oth=oth26, rev=rev26,
               opex=opex26, credit=credit26, cc=credit26 / LOANS_2026,
               A=A26, B=B26, roe=common26 / ((B_YE25 + B26) / 2), dps=s['p26'] * parent26 / SHARES,
               p=s['p26'], parent_norm=parent_norm26, nim=(nii26 / (KAPPA * avgA26)), avgA=avgA26,
               costs=costs26, pbt=nii26 + fee26 + oth26 - costs26 - opex26 - credit26)
    halves = [dict(end=date(2026, 12, 31), common=common_h2, B0=B_H1)]
    cash = [(date(2026, 12, 11), INTERIM_2026), (date(2027, 7, 13), final26)]
    rows = [y26]
    A_prev, B_prev, final_prev = A26, B26, final26
    fee_ratio_prev = fee26 / avgA26
    fee_prev = fee26
    pT_par = None
    for y in range(2027, HORIZON + 1):
        yy = min(y, 2035)
        nim = s['nim'].get(yy, s['nim_lr']) + nim_shift
        theta = s['theta'].get(yy, s['theta_lr'])
        cc = s['cc'].get(yy, s['cc_lr']) + cc_shift
        at1c = AT1_COUPON.get(yy, AT1_COUPON_LR)
        A_y = A_prev * 1.05
        for _ in range(60):                         # 资产随普通股权益增长（杠杆 L 不变），年内迭代
            avgA = (A_prev + A_y) / 2
            fee = fee_prev * (1 + s['feeg']) if y <= 2035 else fee_ratio_prev * avgA
            nii = nim * KAPPA * avgA
            oth = theta * avgA
            rev = nii + fee + oth
            biz = BIZ_R * avgA
            opex = s['cir'] * (rev - biz)
            credit = cc * LAMBDA * avgA
            pbt = rev - COSTS_R * avgA - opex - credit
            parent = pbt * (1 - s['tax']) * (1 - MI)
            at1 = at1c * AT1_BAL / A26 * avgA
            common = parent - at1
            if roe_x is not None:
                common = roe_x * B_prev
                parent = common + at1
            roe_open = common / B_prev
            if y > 2035:
                p = pT_par
            elif s['ramp_from'] is None or y <= s['ramp_from']:
                p = s['pol'][y]
            else:                                   # 线性过渡到稳态派息率（2035 年到位）
                p0 = s['pol'][s['ramp_from']]
                pt = max((1 - s['g_T'] / roe_open) * common / parent, p0)
                w = (y - s['ramp_from']) / (2035 - s['ramp_from'])
                p = p0 + w * (pt - p0)
            if y == 2035:
                pT_par = max((1 - s['g_T'] / roe_open), 0.0) * common / parent
                if s['ramp_from'] is not None:
                    p = max(pT_par, s['pol'][s['ramp_from']])
            interim = S_H1 * p * parent
            final = p * parent - interim
            B_y = B_prev + common - final_prev - interim
            A_new = L * B_y
            if abs(A_new - A_y) < 1e-7:
                break
            A_y = A_new
        A_y = A_new
        c1 = S_H1 * common
        halves.append(dict(end=date(y, 6, 30), common=c1, B0=B_prev))
        halves.append(dict(end=date(y, 12, 31), common=common - c1, B0=B_prev + c1 - final_prev))
        cash.append((date(y, 12, 11), interim))
        cash.append((date(y + 1, 7, 13), final))
        rows.append(dict(y=y, nim=nim, cc=cc, fee=fee, oth=oth, rev=rev, opex=opex, credit=credit, nii=nii,
                         costs=COSTS_R * avgA, pbt=pbt, avgA=avgA, at1=at1, tax=s['tax'],
                         parent=parent, common=common, p=p, dps=p * parent / SHARES, A=A_y, B=B_y,
                         roe=common / ((B_prev + B_y) / 2), g=B_y / B_prev - 1, fee_r=fee / avgA,
                         roa=common / avgA))
        A_prev, B_prev, final_prev, fee_prev, fee_ratio_prev = A_y, B_y, final, fee, fee / avgA
    return dict(rows=rows, halves=halves, cash=cash, L=L, pT=pT_par, g_T=s['g_T'], label=s['label'])


def value(pr, r):
    """DDM（现金股利按派付日折现到 2026-10-19）与 RI（半年，从 2026-06-30 起算再滚到 10-19）。"""
    cut = date(2035, 12, 31)
    pv = sum(cf / (1 + r) ** yf(T0, d) for d, cf in pr['cash'])
    pv_post = sum(cf / (1 + r) ** yf(T0, d) for d, cf in pr['cash'] if d > date(2036, 7, 13))
    rh = (1 + r) ** 0.5 - 1
    base = date(2026, 6, 30)
    ri = sum((h['common'] - rh * h['B0']) / (1 + r) ** (0.5 * k) for k, h in enumerate(pr['halves'], 1))
    v_ri = (B_H1 + ri) * (1 + r) ** yf(base, T0)
    return dict(v_ddm=pv / SHARES, v_ri=v_ri / SHARES, tv_share=pv_post / pv,
                ri_part=(v_ri - B_H1 * (1 + r) ** yf(base, T0)) / SHARES, cut=cut)


def irr(pr, target=PRICE):
    lo, hi = 0.03, 0.30
    for _ in range(80):
        mid = (lo + hi) / 2
        if value(pr, mid)['v_ddm'] > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_roe(target=PRICE, r=COE):
    lo, hi = 0.03, 0.15
    for _ in range(60):
        mid = (lo + hi) / 2
        if value(project('base', {'roe_override': mid}), r)['v_ddm'] > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def weighted(r=COE, mods=None, probs=PROBS):
    vs = {k: value(project(k, (mods or {}).get(k)), r)['v_ddm'] for k in PROBS}
    return sum(probs[k] * vs[k] for k in vs), vs


def band(pv):
    if pv <= 0.75:
        return '明显低估'
    if pv <= 0.90:
        return '温和低估'
    if pv <= 1.10:
        return '大致合理'
    return '偏贵或价值陷阱风险高'


def main():
    res = {}
    for k in ['bear', 'base', 'bull']:
        pr = project(k)
        res[k] = (pr, value(pr, COE))
    print('=== 601939 建设银行 独立估值（股权成本 9%，价格日 2026-10-19，现价 11.57 元，股本 2,616.0038 亿股）===')
    for k in ['bear', 'base', 'bull']:
        pr, v = res[k]
        z = pr['rows'][0]
        print(f"\n[{pr['label']}] p={PROBS[k]:.2f}  V(DDM)={v['v_ddm']:.2f}  V(RI)={v['v_ri']:.2f}  差 {v['v_ri']/v['v_ddm']-1:+.2%}"
              f"  2036 年后现值占比 {v['tv_share']:.1%}  杠杆 L={pr['L']:.2f}  稳态派息率 {pr['pT']:.1%}  g={pr['g_T']:.1%}")
        print(f"  2026E 归母 {z['parent']:.0f}（同比 {z['parent']/3389.06-1:+.1%}）正常化 {z['parent_norm']:.0f}  NII {z['nii']:.0f}"
              f"  手续费 {z['fee']:.0f}  其他非息 {z['oth']:.0f}  业务及管理费 {z['opex']:.0f}  信用减值 {z['credit']:.0f}"
              f"（{z['cc']:.2%}）ROE {z['roe']:.2%}  DPS {z['dps']:.3f}")
        for rw in pr['rows'][1:10]:
            print(f"  {rw['y']} NIM {rw['nim']:.2%} 信用成本 {rw['cc']:.2%} 手续费/资产 {rw['fee_r']:.3%} 归母 {rw['parent']:.0f}"
                  f" 普通股净利 {rw['common']:.0f} ROE {rw['roe']:.2%} 派息率 {rw['p']:.1%} DPS {rw['dps']:.3f}"
                  f" 账面增速 {rw['g']:.2%} BVPS {rw['B']/SHARES:.2f}")
        rw = pr['rows'][10]
        print(f"  2036 稳态 ROE {rw['roe']:.2%}  派息率 {rw['p']:.1%}  DPS {rw['dps']:.3f}  账面增速 {rw['g']:.2%}")
    vw = sum(PROBS[k] * res[k][1]['v_ddm'] for k in PROBS)
    vw_ri = sum(PROBS[k] * res[k][1]['v_ri'] for k in PROBS)
    pv = PRICE / vw
    print(f"\n加权 V（DDM）= {vw:.2f}  加权 V（RI）= {vw_ri:.2f}  P/V = {pv:.3f} → {band(pv)}")
    print(f"V 不变时各档价格：≤{0.75*vw:.2f} 明显低估；{0.75*vw:.2f}–{0.90*vw:.2f} 温和低估；"
          f"{0.90*vw:.2f}–{1.10*vw:.2f} 大致合理；>{1.10*vw:.2f} 偏贵")
    for r in (0.08, 0.10):
        w, vs = weighted(r)
        print(f"股权成本 {r:.0%}：熊 {vs['bear']:.2f} 基准 {vs['base']:.2f} 牛 {vs['bull']:.2f} 加权 {w:.2f}  P/V {PRICE/w:.3f}")
    ir = irr(res['base'][0])
    print(f"隐含回报（基准股利流含稳态，现值 = 现价）= {ir:.2%}；熊 {irr(res['bear'][0]):.2%}；牛 {irr(res['bull'][0]):.2%}")
    ix = implied_roe()
    print(f"反向推算：现价隐含 2027 年起长期普通股 ROE（期初权益口径）≈ {ix:.2%}（9% 股权成本、基准派息与 2.5% 终值增长）")
    b = res['base'][0]
    roeT = b['rows'][10]['roe']
    pb_ss = (roeT - 0.025) / (COE - 0.025)
    print(f"单阶段 P/B–ROE：基准稳态 ROE {roeT:.2%} → 合理 P/B {pb_ss:.2f}，×2026-06-30 BVPS {B_H1/SHARES:.2f} = {pb_ss*B_H1/SHARES:.2f}；"
          f"现价 P/B {PRICE/(B_H1/SHARES):.3f}，隐含 ROE {0.025 + PRICE/(B_H1/SHARES)*(COE-0.025):.2%}")
    print(f"基准 RI 拆分：账面（滚到 10-19）{B_H1/SHARES*(1+COE)**yf(date(2026,6,30),T0):.2f} + 超额收益现值 {res['base'][1]['ri_part']:.2f}")
    # 增长路径（基准，普通股净利）
    rows = b['rows']
    gp = [rows[i]['common'] / rows[i - 1]['common'] - 1 for i in range(1, 6)]
    ret = [1 - rows[i]['p'] * rows[i]['parent'] / rows[i]['common'] for i in range(1, 6)]
    roes = [rows[i]['roe'] for i in range(1, 6)]
    print('基准增长路径（归属普通股东净利）2027–2031：' + ' / '.join(f'{x:.1%}' for x in gp)
          + f'；平均留存率 {sum(ret)/5:.1%}；平均 ROE {sum(roes)/5:.2%}')
    print('基准每股分红 2026–2031：' + ' / '.join(f"{rows[i]['dps']:.3f}" for i in range(0, 6)))
    # 证伪触发后的 V（加权）
    fal = {
        'F1 2026 年报净息差 < 1.32% 或 2027 中报 < 1.28%（基准路径整体下移 8bp，牛情景下移 4bp）':
            dict(mods={'base': {'nim_shift': -0.0008}, 'bull': {'nim_shift': -0.0004}}, probs=PROBS),
        'F2 2026 年报信用成本 > 0.70% 或 2027 中报不良率 > 1.40%/关注类 > 2.0%（基准与牛 +20bp；熊不变）':
            dict(mods={'base': {'cc_shift': 0.0020}, 'bull': {'cc_shift': 0.0020}}, probs=PROBS),
        'F3 个人贷款不良率 > 1.60% 或房贷不良率 > 1.20%（基准与牛信用成本 +10bp，熊 0.30/基准 0.50/牛 0.20）':
            dict(mods={'base': {'cc_shift': 0.0010}, 'bull': {'cc_shift': 0.0010}},
                 probs={'bear': 0.30, 'base': 0.50, 'bull': 0.20}),
        'F4 2026 年报现金分红率 < 30% 或宣布普通股再融资或核心一级 < 13.0%（熊 0.40/基准 0.50/牛 0.10）':
            dict(mods=None, probs={'bear': 0.40, 'base': 0.50, 'bull': 0.10}),
        'F5 2026 三季报前三季度归母净利同比 < +2% 且单季年化 ROE < 9%（熊 0.35/基准 0.50/牛 0.15）':
            dict(mods=None, probs={'bear': 0.35, 'base': 0.50, 'bull': 0.15}),
    }
    print('\n证伪触发后的加权 V：')
    for kf, cfg in fal.items():
        w, vs = weighted(COE, cfg['mods'], cfg['probs'])
        print(f"  {kf}：V = {w:.2f}（熊 {vs['bear']:.2f} 基准 {vs['base']:.2f} 牛 {vs['bull']:.2f}），P/V {PRICE/w:.3f}")
    # ROE 拆解（占期初期末平均总资产）
    print('\nROE 拆解（占平均总资产；2025A 为公告数，其余为模型）：')
    a25 = (405711.49 + A_YE25) / 2         # 2024-12-31 资产总额 40,571,149 百万元
    b25 = (33221.27 - 1599.77 + B_YE25) / 2
    hdr = '  口径            NII    手续费  其他非息  税费及其他  业务管理费  信用减值  税前    普通股净利  杠杆   ROE'
    print(hdr)
    print(f"  2025A         {5727.74/a25:.3%} {1103.07/a25:.3%} {779.68/a25:.3%}  {303.81/a25:.3%}   {2156.78/a25:.3%}   {1333.59/a25:.3%}"
          f"  {3806.23/a25:.3%}  {3334.86/a25:.3%}   {a25/b25:.2f}  {3334.86/b25:.2%}")
    def line(tag, rw, Bavg):
        A = rw['avgA']
        print(f"  {tag:<12}  {rw['nii']/A:.3%} {rw['fee']/A:.3%} {rw['oth']/A:.3%}  {rw['costs']/A:.3%}   {rw['opex']/A:.3%}   {rw['credit']/A:.3%}"
              f"  {rw['pbt']/A:.3%}  {rw['common']/A:.3%}   {A/Bavg:.2f}  {rw['common']/Bavg:.2%}")
    r26 = res['base'][0]['rows'][0]
    line('2026E 基准', r26, (B_YE25 + r26['B']) / 2)
    for k in ['base', 'bear', 'bull']:
        rr = res[k][0]['rows']
        for i in (1, 9):
            line(f"{rr[i]['y']}E {SCEN[k]['label']}", rr[i], (rr[i-1]['B'] + rr[i]['B']) / 2)
    # 敏感性：基准派息率维持 31% 至 2035 年（资产约 6% 增长），2036 年起稳态
    alt = project('base', {'ramp_from': None, 'pol': {y: 0.31 for y in YEARS}})
    print(f"\n敏感性：基准派息率 31% 维持到 2035 年（不提前过渡）V = {value(alt, COE)['v_ddm']:.2f}；"
          f"终值增长 2.0% 时基准 V = {value(project('base', {'g_T': 0.02}), COE)['v_ddm']:.2f}；"
          f"长期净息差 1.35% 时基准 V = {value(project('base', {'nim_lr': 0.0135, 'nim': {2027: 0.0136, 2028: 0.0135}}), COE)['v_ddm']:.2f}")
    # 资本与拨备缓冲（只讨论，不计入价值）
    npl, cov = 3789.76, 2.3869
    exc = (cov - 1.50) * npl
    print(f"拨备覆盖率 238.69% 高于 150% 的部分 {exc:.0f} 亿（税前，约 {exc*0.75/SHARES:.2f} 元/股税后，不计入 V）；"
          f"核心一级资本充足率 14.24% 高于 9.0% 要求的部分 {(0.1424-0.09)*251325.50:.0f} 亿（{(0.1424-0.09)*251325.50/SHARES:.2f} 元/股，不计入 V）")
    # 参考读数
    h_rmb = 9.865 * 0.8510
    print(f"\n参考：H 股 2026-10-16 收盘 9.865 港元 × 0.8510 = {h_rmb:.2f} 元，A/H 溢价 {PRICE/h_rmb-1:.1%}，H 股 P/V {h_rmb/vw:.3f}")
    print(f"参考：2026 中期股息 0.201 元 + 末期预测 {(res['base'][0]['rows'][0]['dps']-0.201):.3f} 元，"
          f"前瞻股息率 {res['base'][0]['rows'][0]['dps']/PRICE:.2%}；过去 12 个月 0.3887 元，股息率 {0.3887/PRICE:.2%}")


if __name__ == '__main__':
    main()
