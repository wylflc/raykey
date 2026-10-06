"""第一批修正重装（v4.232，用户 2026-10-06 裁定负税率加 −5% 门槛）：修正后的 ALL 七份逐日状态替换首轮安装的 ALL（凡负即纠版）。

先验：本轮 CONTROL 仍逐字节等于首轮安装前的正式状态（`v1_negative_all/build_check.json` 的 current）；现行正式状态是首轮安装的 ALL；
修正后 ALL 摘要与文件一致。首轮读数留 `v1_negative_all/`。

    python3 reinstall.py     # → publication.json
"""
import json
import os
import shutil

from common import EXP, PROC, ROOT, STATE_FILES, digest, load, save


def main():
    v1 = json.loads((EXP / 'v1_negative_all/build_check.json').read_text(encoding='utf-8'))
    check = load('build_check.json')
    installed = {}
    for name in STATE_FILES:
        assert check['reproduction'][name]['CONTROL'] == v1['reproduction'][name]['current'], (name, 'CONTROL 未复现首轮安装前状态')
        assert digest(PROC / name) == v1['reproduction'][name]['ALL'], (name, '正式状态已不是首轮安装的 ALL')
        assert digest(EXP / 'states/ALL' / name) == check['reproduction'][name]['ALL'], name
    for name in STATE_FILES:
        tmp = (PROC / name).with_name('.' + name + '.v4232b')
        shutil.copyfile(EXP / 'states/ALL' / name, tmp)
        os.replace(tmp, PROC / name)
        installed[name] = dict(before=v1['reproduction'][name]['ALL'], after=digest(PROC / name), pre_v4232=v1['reproduction'][name]['current'])
        assert installed[name]['after'] == check['reproduction'][name]['ALL'], name
        print('REINSTALLED', name, flush=True)
    save('publication.json', dict(arm='ALL', version='v4.232', reinstall='负税率加 −5% 门槛（用户 2026-10-06）', installed=installed,
                                  old_states='states/CONTROL（与首轮安装前正式状态逐字节相同）', v1='v1_negative_all/（凡负即纠版读数与安装凭据）'))


if __name__ == '__main__':
    main()
