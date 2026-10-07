#!/usr/bin/env python3
"""烟蒂池草案 D 类（低市净率金融型）的算例：平安银行，2026-06-30 余额、2026-09-30 收盘。

输入取自独立评审全文 `exp_independent_pab_20261007/companies/000001_平安银行.md`（2026 年半年报，页码见该文），
ROE 取 `data/raw/financials/` 年报加权 ROE。只演示草案口径，不进任何判定。
"""
PRICE = 11.57
SHARES = 194.06            # 亿股
BVPS0 = 23.88              # 普通股 BVPS 24.13 扣 09-24 中期息 0.249
RESERVE = 795.63           # 贷款减值准备，亿元
TAX = 0.25
NPL = 150.2 + 8.0 + 89.8 + 57.2 + 57.5          # 不良：对公、按揭、信用卡、消费贷、经营贷
SPECIAL = 631.8                                   # 关注类
RESTRUCTURED_NORMAL = 139.9                       # 仍列正常类的重组贷款（评审假设占重组贷款 419.7 的三分之一）
NORMAL = dict(corporate=(1941.2 + 14238.7, 0.0035), mortgage=(3628.3, 0.0015),
              retail_other=(4551.9 + 4941.0, 0.025), credit_card=(3936.1, 0.05))
ROE = dict(y2023=11.38, y2024=10.08, y2025=9.15, ttm=9.15 + 5.22 - 5.25, y2025_ex_reversal=8.05)
COE, G = 11.0, 3.0         # 股份行 COE；终值增长
GATES = dict(cet1=9.32, cet1_requirement=7.75, coverage=219.58, provision_to_loans=2.30,
             npl_plus_special=1.05 + 1.83, roe_min_3y=min(ROE['y2023'], ROE['y2024'], ROE['y2025']))


def main():
    normal_loss = sum(balance * rate for balance, rate in NORMAL.values())
    expected = NPL * 0.60 + SPECIAL * 0.25 + RESTRUCTURED_NORMAL * 0.10 + normal_loss
    shortfall = max(0.0, expected - RESERVE)
    stressed = BVPS0 - shortfall * (1 - TAX) / SHARES
    print(f'预期损失 {expected:.1f} 亿（不良 {NPL * 0.6:.1f}、关注 {SPECIAL * 0.25:.1f}、重组 {RESTRUCTURED_NORMAL * 0.1:.1f}、'
          f'正常类一年 {normal_loss:.1f}）− 准备 {RESERVE:.1f} = 缺口 {shortfall:.1f} 亿')
    print(f'压力后普通股 BVPS {stressed:.2f}（每股 −{BVPS0 - stressed:.2f}）')
    for label, roe in (('报告 ROE（三年与 TTM 较低者）', min(ROE['y2023'], ROE['y2024'], ROE['y2025'], ROE['ttm'])),
                       ('剔除非信贷减值转回', ROE['y2025_ex_reversal'])):
        pb = min(1.0, (roe - G) / (COE - G))
        v = stressed * pb
        print(f'{label} {roe:.2f}%：合理 P/B {pb:.3f}，V_cb {v:.2f}，P/V_cb {PRICE / v:.3f}')
    print('闸门：核心一级 {cet1}% 对要求 {cet1_requirement}% + 1.5pp；拨备覆盖率 {coverage}%；拨贷比 {provision_to_loans}%；'
          '不良 + 关注 {npl_plus_special:.2f}%；三年最低 ROE {roe_min_3y}%'.format(**GATES))


if __name__ == '__main__':
    main()
