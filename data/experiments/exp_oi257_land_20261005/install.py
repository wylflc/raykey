"""OI-257 安装（v4.230）：NEW 七份逐日状态与 v4.230 受限资产表替换正式文件。

先验：CONTROL 逐字节复现安装前正式状态（`build_check.json`）；正式状态与受限资产表仍是冻结版本；NEW 摘要与文件一致。
旧口径状态即 `states/CONTROL`（与安装前正式状态逐字节相同），保留作复现。

    python3 install.py     # → publication.json
"""
import os
import shutil

from common import EXP, PROC, RESTRICTED, ROOT, STATE_FILES, digest, load, save

TABLE = ROOT / 'data/reference/restricted_cash_items.csv'


def replace(src, target, tag):
    tmp = target.with_name('.' + target.name + tag)
    shutil.copyfile(src, tmp)
    os.replace(tmp, target)


def main():
    check, inputs = load('build_check.json'), load('inputs_summary.json')
    for name in STATE_FILES:
        rep = check['reproduction'][name]
        assert rep['identical'], (name, 'CONTROL 未复现正式状态')
        assert digest(PROC / name) == rep['current'], (name, '正式状态已不是冻结版本')
        assert digest(EXP / 'states/NEW' / name) == rep['new'], name
    assert digest(TABLE) == inputs['digests']['control'], '正式受限资产表已不是 v4.229 版本'
    assert digest(RESTRICTED['NEW']) == inputs['digests']['new']
    installed = {}
    for name in STATE_FILES:
        before = check['reproduction'][name]['current']
        replace(EXP / 'states/NEW' / name, PROC / name, '.v4230')
        installed[name] = dict(before=before, after=digest(PROC / name))
        assert installed[name]['after'] == check['reproduction'][name]['new'], name
        print('INSTALLED', name, flush=True)
    replace(RESTRICTED['NEW'], TABLE, '.v4230')
    installed['data/reference/restricted_cash_items.csv'] = dict(before=inputs['digests']['control'], after=digest(TABLE))
    gaps_new, gaps_prod = EXP / 'states/NEW/gaps.csv', ROOT / 'data/interim/valuation_statement_gaps.csv'
    gaps_same = gaps_new.exists() and gaps_prod.exists() and gaps_new.read_bytes() == gaps_prod.read_bytes()
    save('publication.json', dict(arm='NEW', version='v4.230', installed=installed, statement_gaps_identical=gaps_same,
                                  old_states='states/CONTROL（与安装前正式状态逐字节相同）',
                                  old_table='inputs/restricted_cash_items_v4229.csv（v4.229 正式表）'))
    print('statement gaps identical to production:', gaps_same)


if __name__ == '__main__':
    main()
