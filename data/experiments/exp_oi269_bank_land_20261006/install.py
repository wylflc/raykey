"""银行 BV 年增速封顶安装（v4.235）：NEW 三份逐日状态（候选侧、B2、持仓侧）替换正式文件；`bank_valuation.BV_GROWTH_CAP` 随后改 0.07。

先验：CONTROL 逐字节复现安装前正式状态（`build_check.json`）；NEW 摘要与文件一致。

    python3 install.py     # → publication.json
"""
import os
import shutil

from common import EXP, PROC, STATE_FILES, digest, load, save


def main():
    check = load('build_check.json')
    for name in STATE_FILES:
        rep = check['reproduction'][name]
        assert rep['identical'], (name, 'CONTROL 未复现正式状态')
        assert digest(PROC / name) == rep['current'], (name, '正式状态已变')
        assert digest(EXP / 'states/NEW' / name) == rep['NEW'], name
    installed = {}
    for name in STATE_FILES:
        tmp = (PROC / name).with_name('.' + name + '.v4235')
        shutil.copyfile(EXP / 'states/NEW' / name, tmp)
        os.replace(tmp, PROC / name)
        installed[name] = dict(before=check['reproduction'][name]['current'], after=digest(PROC / name))
        assert installed[name]['after'] == check['reproduction'][name]['NEW'], name
        print('INSTALLED', name, flush=True)
    save('publication.json', dict(arm='NEW', version='v4.235', installed=installed, old_states='states/CONTROL（与安装前正式状态逐字节相同）'))


if __name__ == '__main__':
    main()
