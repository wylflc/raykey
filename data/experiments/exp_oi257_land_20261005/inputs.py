"""NEW 臂受限资产表：v4.230 `fetch_restricted_cash_items.py`（受限分项、法定存款准备金、扩大的抽取范围）写到 `inputs/`，
生产表不动。先拷 v4.229 生产表作起点（与生产运行同一合并语义：清单外的旧行保留），联网定位并下载新进清单的年报（与附注
现金类共用缓存 `data/raw/annual_reports/`），再全量解析。逐行对照 v4.229 表，汇总到 `inputs_summary.json`。

    WORKERS=2 python3 inputs.py    # 需外网（巨潮检索接口；2026-10-05 计算节点访问超时，改在交互节点跑）
    python3 inputs.py --parse-only # 只用缓存文本
"""
import os
import shutil
import sys
from collections import Counter

from common import EXP, RESTRICTED, ROOT, digest, read, save
sys.path.insert(0, str(ROOT / 'scripts'))
import fetch_cash_note_items as cn  # noqa: E402
import fetch_restricted_cash_items as rc  # noqa: E402


def num(x) -> float:
    return cn._num(x)


def main():
    old_path, new_path = RESTRICTED['CONTROL'], RESTRICTED['NEW']
    assert digest(old_path) == digest(rc.OUT), 'v4.229 冻结副本须与生产表相同'
    shutil.copyfile(old_path, new_path)
    rc.OUT = new_path
    sys.argv = ['fetch_restricted_cash_items', '--workers', os.environ.get('WORKERS', '16')] + (['--parse-only'] if '--parse-only' in sys.argv[1:] else [])
    assert rc.main() == 0
    key = lambda r: (r['security_code'], int(r['fiscal_year']))
    old, new = {key(r): r for r in read(old_path)}, {key(r): r for r in read(new_path)}
    moves, changed = Counter(), []
    for k in sorted(old.keys() | new.keys()):
        o, n = old.get(k, {}), new.get(k, {})
        moves[f"{o.get('status', 'absent')}→{n.get('status', 'absent')}"] += 1
        d_counted = num(n.get('counted_yuan')) - num(o.get('counted_yuan'))
        reserve = num(n.get('reserve_yuan'))
        if abs(d_counted) > 0.5 or reserve > 0:
            changed.append(dict(code=k[0], name=n.get('security_name') or o.get('security_name'), year=k[1],
                                status=n.get('status'), notes_payable_yi=num(n.get('notes_payable')) / 1e8,
                                counted_before_yi=num(o.get('counted_yuan')) / 1e8, counted_after_yi=num(n.get('counted_yuan')) / 1e8,
                                fallback_yi=num(n.get('fallback_yuan')) / 1e8, reserve_yi=reserve / 1e8,
                                loan_manual_yi=num(n.get('loan_pledge_manual_yuan')) / 1e8, reserve_source=n.get('reserve_source'),
                                breakdown_source=n.get('breakdown_source'), breakdown_items=n.get('breakdown_items')))
    ok_new = [r for r in new.values() if r.get('status') == 'ok']
    summary = dict(rows_before=len(old), rows_after=len(new), status_moves=dict(moves.most_common()),
                   counted_before_yi=sum(num(r['counted_yuan']) for r in old.values() if r.get('status') == 'ok') / 1e8,
                   counted_after_yi=sum(num(r['counted_yuan']) for r in ok_new) / 1e8,
                   fallback_yi=sum(num(r.get('fallback_yuan')) for r in ok_new) / 1e8,
                   fallback_rows=sum(num(r.get('fallback_yuan')) > 0 for r in ok_new),
                   fallback_codes=len({r['security_code'] for r in ok_new if num(r.get('fallback_yuan')) > 0}),
                   reserve_rows=sum(num(r.get('reserve_yuan')) > 0 for r in new.values()),
                   reserve_codes=sorted({r['security_code'] for r in new.values() if num(r.get('reserve_yuan')) > 0}),
                   reserve_yi=sum(num(r.get('reserve_yuan')) for r in new.values()) / 1e8,
                   carve_rows=sum(1 for c in changed if c['counted_after_yi'] < c['counted_before_yi'] - 1e-8),
                   digests={'control': digest(old_path), 'new': digest(new_path)})
    save('inputs_summary.json', dict(summary, changed=changed))
    print({k: v for k, v in summary.items() if k != 'reserve_codes'})


if __name__ == '__main__':
    main()
