"""v4.235 在册 BASE 剔除集 A 行补登（§12.326）：OI-269 银行落地重登时 A 行沿用 OI-257 旧集（含陕煤），而 v4.235 BASE 自身
2011-11-01 锚点前五是茅台替陕煤；按 §12.272 先例「改按现行锚点前五重登」，用本目录 `run_27679999/`（作业 27679999）CONTROL（＝v4.235 BASE）在 A 组
（CONTROL 锚点前五）上的 14 行替换在册 A 行。全样本 14 行与台账其余行不动（对照写入前的工作区台账逐行核对）。

    python3 register_v4235_a.py    # → data/backtest/summary_BASE*ex5.csv、scan_summaries.csv、registration_v4235_a.json
"""
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
ROOT = EXP.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import sweep_backtest_configs as sw  # noqa: E402
import clean_derived_artifacts as ledger  # noqa: E402


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def main():
    RUN = EXP / 'run_27679999'
    res = json.loads((RUN / 'readings.json').read_text())
    a_set = res['A']
    rows = [r for r in read(RUN / 'summary_rows.csv') if r['arm'] == 'CONTROL' and r['group'] == 'A']
    assert len(rows) == 14 and all(r['负现金日数'] == '0' and r['计量版本'] == sw.METRIC_VERSION for r in rows)
    full = next(r for r in read(RUN / 'summary_rows.csv') if r['arm'] == 'CONTROL' and r['group'] == 'full' and r['start'] == sw.EX5_ANCHOR_START)
    assert sorted(c for c in full[sw.EX5_FIELD].split('/') if c) == a_set, '剔除集须为 CONTROL 自身锚点前五'
    key = lambda r: (r['扫描标签'], r['策略'], r['计量版本'])
    before = {key(r): r for r in read(ledger.MERGED)}
    paths, published, touched = [], [], set()
    for r in rows:
        tag = sw.summary_tag('BASE', r['start'], ','.join(a_set))
        clean = {k: x for k, x in r.items() if k not in ('group', 'arm', 'start', 'tag')}
        suffix = '_' + r['tag']
        assert clean['策略'].endswith(suffix)
        clean['策略'] = clean['策略'][:-len(suffix)] + '_' + tag
        target = sw.OUT_DIR / f'summary_{tag}.csv'
        old = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        tmp = target.with_name('.' + target.name + '.v4235a')
        with tmp.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(clean)); w.writeheader(); w.writerow(clean)
        tmp.replace(target); paths.append(target); touched.add((tag, clean['策略'], clean['计量版本']))
        published.append(dict(path=str(target.relative_to(ROOT)), before_sha256=old, after_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    names = {p.name for p in paths}
    with os.scandir(sw.OUT_DIR) as it:
        entries = [e for e in it if e.name in names]
    ledger.write_ledger(entries)
    after = {key(r): r for r in read(ledger.MERGED)}
    assert before.keys() <= after.keys(), '旧键不得删除'
    assert touched <= after.keys() and len(touched) == 14 and touched <= before.keys()
    assert all(after[k] == r for k, r in before.items() if k not in touched), '本批之外的已登记行不得改写'
    (EXP / 'registration_v4235_a.json').write_text(json.dumps(dict(registered_base_rows=14, group='A', A=a_set, replaced_A=res['RC'],
        input_epoch='v4235_20261006', precedent='§12.272 剔除集 A 改按现行锚点前五重登', run_job='27679999',
        entry_point='clean_derived_artifacts.write_ledger', published=published), ensure_ascii=False, indent=2) + '\n')
    print(f"REGISTERED 14 BASE ex5 summaries with A = {'/'.join(a_set)}; other ledger rows preserved.")


if __name__ == '__main__':
    main()
