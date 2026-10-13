"""沪电股份（002463）现有已投产产能的正常化盈利推算（亿元），只做算术，不读仓库文件。

基数 = 2026 年二季度 = 半年报（公告日 2026-08-26）减一季度（H 股申请版本 2026-06-05 的分应用收入与毛利）。
步骤：稼动率由 99.1%（2026Q1 整体，H 股申请版本）降到目标值，PCB 成本的固定部分不随量变；
价格回落到给定毛利率；费用按上半年口径；归母经 §6.5.2.2 股权桥折成模型口径 NOPAT。
用法：python3 data/experiments/exp_growth_reviews_20261013/002463_norm.py
"""
H1 = dict(dc_rev=113.30137462, dc_cost=64.28962624, auto_rev=14.38141833, auto_cost=11.65380062,
          ind_rev=2.26199887, ind_cost=1.34436811, pcb_rev=129.94479182, pcb_cost=77.28779497,
          tot_rev=136.89427504, tot_cost=83.89487706)                      # 2026 半年报，分应用收入与成本
Q1 = dict(dc_rev=50.88745, dc_gp=20.15602, auto_rev=7.34923, auto_gp=1.43817, ind_rev=0.99008, ind_gp=0.41525,
          oth_rev=2.91480, oth_gp=0.13309, tot_rev=62.14156)                # H 股申请版本，2026Q1
q2 = {}
for k in ('dc', 'auto', 'ind'):
    q2[k + '_rev'] = H1[k + '_rev'] - Q1[k + '_rev']
    q2[k + '_gp'] = (H1[k + '_rev'] - H1[k + '_cost']) - Q1[k + '_gp']
q2['oth_rev'] = (H1['tot_rev'] - H1['pcb_rev']) - Q1['oth_rev']
q2['oth_gp'] = ((H1['tot_rev'] - H1['tot_cost']) - (H1['pcb_rev'] - H1['pcb_cost'])) - Q1['oth_gp']
q2['tot_rev'] = H1['tot_rev'] - Q1['tot_rev']

FIXED_COST_SHARE = 0.21          # 2025 年报 PCB 成本：人工 12.60% 的一半 + 制造费用 20.76% 的七成
UTIL_NOW = 0.991                 # 2026Q1 整体稼动率（产量 ÷ 有效产能）
ADMIN, RD = 2.63853541 * 2, 8.63265913 * 2      # 管理、研发费用按上半年年化（研发费用化）
SELL, SURTAX, IMPAIR = 0.0263, 0.0063, 0.015    # 销售费用、税金及附加、减值占收入（上半年 2.63%、0.63%、1.73%）
OTHER_INCOME, ASSOCIATE = 0.9, -0.15            # 其他收益、权益法损益
BRIDGE_ADD = 42.88 - 38.19                      # 2025 年报模型口径 NOPAT − 合并净利（annual_nopat.py）
MINORITY_SHARE = 0.0                            # 生产带 minority_share


def scenario(label, util, gm_dc, gm_auto, gm_ind=0.40, gm_oth=0.03, tax=0.13, impair=IMPAIR):
    vol = util / UTIL_NOW
    cost_factor = (1 - FIXED_COST_SHARE) * vol + FIXED_COST_SHARE
    dc_rev = (q2['dc_rev'] - q2['dc_gp']) * 4 * cost_factor / (1 - gm_dc)
    auto_rev = (q2['auto_rev'] - q2['auto_gp']) * 4 * cost_factor / (1 - gm_auto)
    ind_rev, oth_rev = q2['ind_rev'] * 4 * vol, q2['oth_rev'] * 4 * vol
    rev = dc_rev + auto_rev + ind_rev + oth_rev
    gp = dc_rev * gm_dc + auto_rev * gm_auto + ind_rev * gm_ind + oth_rev * gm_oth
    pbt = gp - rev * (SURTAX + SELL + impair) - ADMIN - RD + OTHER_INCOME + ASSOCIATE
    parent = pbt * (1 - tax)
    nopat = parent / (1 - MINORITY_SHARE) + BRIDGE_ADD
    price = dc_rev / (q2['dc_rev'] * 4 * vol) - 1
    print(f'{label}：稼动率 {util:.0%}、数据通讯毛利率 {gm_dc:.1%}、汽车板 {gm_auto:.1%} → 营收 {rev:.1f}（数据通讯 {dc_rev:.1f}，'
          f'较同量现价 {price:+.1%}）、毛利 {gp:.2f}、综合毛利率 {gp / rev:.1%}、利润总额 {pbt:.2f}、归母 {parent:.2f}、NOPAT {nopat:.2f}')
    return nopat


print('二季度：' + '；'.join(f"{n} 收入 {q2[k + '_rev']:.2f} 毛利率 {q2[k + '_gp'] / q2[k + '_rev']:.2%}"
                           for k, n in (('dc', '数据通讯'), ('auto', '汽车'), ('ind', '工控'), ('oth', '其他'))))
print(f"二季度年化营收 {q2['tot_rev'] * 4:.1f}，其中数据通讯 {q2['dc_rev'] * 4:.1f}、汽车 {q2['auto_rev'] * 4:.1f}、"
      f"工控 {q2['ind_rev'] * 4:.1f}、其他 {q2['oth_rev'] * 4:.1f}")
scenario('中枢', 0.90, 0.38, 0.21)
scenario('保守', 0.85, 0.34, 0.19)
scenario('乐观', 0.95, 0.42, 0.23)
scenario('数据通讯毛利率 +1pp', 0.90, 0.39, 0.21)
scenario('稼动率 +5pp', 0.95, 0.38, 0.21)
scenario('二季度原样（紧缺期峰值）', UTIL_NOW, q2['dc_gp'] / q2['dc_rev'], q2['auto_gp'] / q2['auto_rev'],
         gm_ind=q2['ind_gp'] / q2['ind_rev'], gm_oth=q2['oth_gp'] / q2['oth_rev'], impair=0.0173)
