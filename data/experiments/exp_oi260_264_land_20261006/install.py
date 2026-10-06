"""第一批修正安装（v4.232）：ALL 七份逐日状态替换正式文件。

先验：CONTROL 逐字节复现安装前正式状态（`build_check.json`）；正式状态仍是 v4.230 安装版本；ALL 摘要与文件一致。
旧口径状态即 `states/CONTROL`（与安装前正式状态逐字节相同），保留作复现。

    python3 install.py     # → publication.json
"""
import os
import shutil

from common import EXP, PROC, ROOT, STATE_FILES, digest, load, save


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
        assert digest(EXP / 'states/ALL' / name) == rep['ALL'], name
    installed = {}
    for name in STATE_FILES:
        before = check['reproduction'][name]['current']
        replace(EXP / 'states/ALL' / name, PROC / name, '.v4232')
        installed[name] = dict(before=before, after=digest(PROC / name))
        assert installed[name]['after'] == check['reproduction'][name]['ALL'], name
        print('INSTALLED', name, flush=True)
    gaps_new, gaps_prod = EXP / 'states/ALL/gaps.csv', ROOT / 'data/interim/valuation_statement_gaps.csv'
    gaps_same = gaps_new.exists() and gaps_prod.exists() and gaps_new.read_bytes() == gaps_prod.read_bytes()
    save('publication.json', dict(arm='ALL', version='v4.232', installed=installed, statement_gaps_identical=gaps_same,
                                  old_states='states/CONTROL（与安装前正式状态逐字节相同）'))
    print('statement gaps identical to production:', gaps_same)


if __name__ == '__main__':
    main()
