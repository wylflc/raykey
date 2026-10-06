"""第二批修正安装（v4.233）：ALL2 七份逐日状态替换正式文件，附注类债务（含人工核定）、弃置专户与受限资产 v2 四张表落 data/reference/。

先验：CONTROL 逐字节复现安装前正式状态（`build_check.json`）；正式状态仍是 v4.232 安装版本；ALL2 摘要与文件一致。
旧口径状态即 `states/CONTROL`（与安装前 v4.232 正式状态逐字节相同），保留作复现。

    python3 install.py     # → publication.json
"""
import os
import shutil

from common import DEBT, EXP, FUND, PROC, RESTRICTED_V2, ROOT, STATE_FILES, digest, load, save


def replace(src, target, tag):
    tmp = target.with_name('.' + target.name + tag)
    shutil.copyfile(src, tmp)
    os.replace(tmp, target)


def main():
    check = load('build_check.json')
    for name in STATE_FILES:
        rep = check['reproduction'][name]
        assert rep['identical'], (name, 'CONTROL 未复现正式状态')
        assert digest(PROC / name) == rep['current'], (name, '正式状态已不是冻结版本')
        assert digest(EXP / 'states/ALL2' / name) == rep['ALL2'], name
    installed = {}
    for name in STATE_FILES:
        before = check['reproduction'][name]['current']
        replace(EXP / 'states/ALL2' / name, PROC / name, '.v4233')
        installed[name] = dict(before=before, after=digest(PROC / name))
        assert installed[name]['after'] == check['reproduction'][name]['ALL2'], name
        print('INSTALLED', name, flush=True)
    manual = ROOT / 'data/experiments/exp_oi261_263_20261006/debt_note_manual.csv'
    for src, dst in ((DEBT, 'debt_note_items.csv'), (FUND, 'decom_fund_items.csv'), (RESTRICTED_V2, 'restricted_cash_items.csv'),
                     (manual, 'debt_note_manual.csv')):
        replace(src, ROOT / 'data/reference' / dst, '.v4233')
        installed['data/reference/' + dst] = digest(ROOT / 'data/reference' / dst)
    gaps_new, gaps_prod = EXP / 'states/ALL2/gaps.csv', ROOT / 'data/interim/valuation_statement_gaps.csv'
    gaps_same = gaps_new.exists() and gaps_prod.exists() and gaps_new.read_bytes() == gaps_prod.read_bytes()
    save('publication.json', dict(arm='ALL2', version='v4.233', installed=installed, statement_gaps_identical=gaps_same,
                                  old_states='states/CONTROL（与安装前 v4.232 正式状态逐字节相同）'))
    print('statement gaps identical to production:', gaps_same)


if __name__ == '__main__':
    main()
