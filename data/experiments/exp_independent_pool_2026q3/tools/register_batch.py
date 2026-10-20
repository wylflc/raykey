#!/usr/bin/env python3
"""OI-291：把一批核对通过的代理交付登记进 §6.9 登记表与档案研究数（README「每批步骤」第 5 步）。

1. 逐家用 check_delivery 复核，有错误的跳过；
2. §6.9 登记表追加 `current` 行，同公司旧 `current` 行改 `superseded`，模型 V 取最近一次扫描的候选侧 V；
3. 写 `research/<代码>.json`，调 register_research.py 登记档案研究数（§6.5.2.2 折算）：
   - 只登记 ROIC 路径的公司（§7.3 差距规则只管 ROIC 路径；银行、保险走股利折现，研究数不进带）；
   - 档案已「采用研究数」的不覆盖，列为待裁定；
   - 档案在发布凭据的输入摘要内：最近一次发布的信号日不早于最近收盘日时（清单已发布、尚未执行完），不改档案，研究数留待下次；
4. 重出 §6.9 阅读版；
5. 打印汇总报告用的对照表（模型与独立 P/V、研究数与模型锚的差距、档案现状），预演时也打印。

    python3 tools/register_batch.py b01 [--codes 600066,688041] [--review-date 2026-10-20] [--dry-run] [--no-research] [--revision r1]

口径修订后重登（研究数不变）：`--revision r1 --no-research`，评审编号为 `iv<价格日>_pool_<批次>r1:<代码>`，旧行改 `superseded`。
"""
import argparse
import csv
import io
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
SCRATCH = ROOT / 'data/scratch/experiments/exp_independent_pool_2026q3'
REGISTRY = ROOT / 'data/processed/independent_valuations.csv'
CANDIDATES = ROOT / 'data/processed/daily_buy_candidates.csv'
PUBLICATION = ROOT / 'data/processed/daily_execution_publication.json'
REPORT = 'docs/reports/independent_pool_2026q3.zh.md'
sys.path.insert(0, str(TOOLS))
import check_delivery  # noqa: E402
import register_research  # noqa: E402


def beijing_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)


def latest_close_date() -> str:
    """最近一个已收盘交易日（上证指数日线；当日 15:05 前不算当日）。"""
    now = beijing_now()
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,{(now - timedelta(days=20)).date()},{now.date()},30,"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
    days = [r[0] for r in json.loads(urllib.request.urlopen(req, timeout=30).read())['data']['sh000001']['day']]
    if days and days[-1] == now.date().isoformat() and (now.hour, now.minute) < (15, 5):
        days = days[:-1]
    return days[-1]


def research_window() -> tuple[bool, str]:
    published = json.loads(PUBLICATION.read_text(encoding='utf-8')).get('as_of', '')
    close = latest_close_date()
    ok = published < close
    return ok, (f'最近发布的信号日 {published}，最近收盘日 {close}：' +
                ('可登记档案研究数（下一次扫描读入）' if ok else '清单已发布、尚未到下一次收盘，不改档案，研究数留待下次登记'))


def model_values() -> tuple[str, dict[str, float]]:
    rows = list(csv.DictReader(CANDIDATES.open(encoding='utf-8')))
    last = max(r['trade_date'] for r in rows)
    out = {}
    for r in rows:
        if r['trade_date'] == last and (r.get('model_intrinsic_value') or '').strip():
            out[r['security_code'].zfill(6)] = float(r['model_intrinsic_value'])
    return last, out


def table_row(j: dict, model_v: float | None, path: str, spec: dict | None) -> str:
    """汇总报告对照表一行；研究数按 §6.5.2.2 现算，档案现状读档案。"""
    sc, price = j['scenarios'], j['price']
    mv = f"{model_v:.2f} | {price / model_v:.3f}" if model_v else '— | —'
    head = (f"| {j['security_code']} | {j['security_name']} | {price:.2f} | {mv} | {j['v_weighted']:.2f}"
            f"（{sc['bear']['v']:.2f}～{sc['bull']['v']:.2f}） | {j['pv']:.3f} | {j['verdict']} |")
    if spec is None:
        return head + f" —（{path}，研究数不进带） | — | — | — |"
    r = register_research.compute(spec)
    d = register_research.dossier_state(j['security_code'])
    c, gap = r['conv'], r['gap']
    adopted = d['conclusion'] == '采用研究数'
    # §7.3：生产所用的锚高于另一数时冻结。采用研究数的行生产用档案现有研究数（新数不覆盖），故按现有数判。
    in_use = float(d['research']) if adopted and d['research'] else c['base']
    flag = ''
    if gap > 0.30 + 1e-9:
        flag = '，入队' + ('，冻结新增买入' if (in_use > r['model_yi'] if adopted else c['base'] < r['model_yi']) else '')
    if adopted:
        state = f"已采用研究数 {d['research']}（{d['date']}），新数不覆盖，待裁定"
    elif d['research']:
        state = f"替换旧研究数 {d['research']}（{d['date']}）"
    else:
        state = '新登记'
    return head + (f" {c['base']:.2f}（{c['bear']:.2f}～{c['bull']:.2f}） | {r['model_yi']:.2f} | "
                   f"{gap:.1%}{flag} | {state} |")


def fmt(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def registry_row(j: dict, batch: str, review_date: str, model_v: float | None, evidence_rel: str, revision: str = '') -> dict:
    sc = j['scenarios']
    price, v = j['price'], j['v_weighted']
    batch_id = f"iv{j['price_date'].replace('-', '')}_pool_{batch}{revision}"
    fals = '；'.join(f"{'①②③④⑤⑥'[i]} {x['condition']}（{x['deadline']} 前）" +
                    (f"：独立 V 约 {x['v_if_triggered']:.2f}" if isinstance(x.get('v_if_triggered'), (int, float)) else '')
                    for i, x in enumerate(j['falsifiers'][:6]))
    return dict(
        review_id=f"{batch_id}:{j['security_code']}", batch_id=batch_id, review_date=review_date, reviewer_type='own',
        reviewer='独立代理（不读仓库）', market='A', security_code=j['security_code'], security_name=j['security_name'],
        status='current', superseded_by='', price_date=j['price_date'], evidence_cutoff=j['evidence_cutoff'], currency='CNY',
        unit='元/股', price=fmt(price), v_base=fmt(v), v_bear=fmt(sc['bear']['v']), v_bull=fmt(sc['bull']['v']), pv=fmt(price / v, 3),
        scenarios=(f"熊 {sc['bear']['v']:.2f}（{sc['bear']['p']:.0%}）／基准 {sc['base']['v']:.2f}（{sc['base']['p']:.0%}）／"
                   f"牛 {sc['bull']['v']:.2f}（{sc['bull']['p']:.0%}）"),
        verdict=j['verdict'], confidence=j['confidence'],
        coe=f"{j['coe']:.0%}（8%／10%：P/V {price / j['v_at_coe_8']:.2f}／{price / j['v_at_coe_10']:.2f}）",
        method=j['method'], implied_irr=fmt(j['implied_irr'], 3),
        model_v=fmt(model_v) if model_v else '', model_pv=fmt(price / model_v, 3) if model_v else '',
        conclusion=j['conclusion'], basis=j['basis'], key_events=j['key_events'], key_metrics=j['key_metrics'], risks=j['risks'],
        falsifiers=fals, next_check=j['next_check'], report=REPORT, evidence=evidence_rel)


def append_registry(rows: list[dict]) -> None:
    raw = REGISTRY.read_bytes().decode('utf-8')
    newline = '\r\n' if '\r\n' in raw else '\n'
    reader = csv.DictReader(io.StringIO(raw, newline=''))
    fields, old = reader.fieldnames, list(reader)
    ids = {r['review_id'] for r in old}
    for new in rows:
        if new['review_id'] in ids:
            raise SystemExit(f"登记表已有 {new['review_id']}")
        for r in old:
            if r['market'] == 'A' and r['security_code'] == new['security_code'] and r['status'] == 'current':
                r['status'], r['superseded_by'] = 'superseded', new['review_id']
    out = io.StringIO(newline='')
    w = csv.DictWriter(out, fieldnames=fields, lineterminator=newline)
    w.writeheader()
    w.writerows(old + rows)
    REGISTRY.write_text(out.getvalue(), encoding='utf-8', newline='')


def evidence_date(batch: str, code: str, price_date: str) -> str:
    """研究数证据日：价格日与所用定期报告公告日的较晚者（晚间公告记次日）。"""
    best = price_date
    with (SCRATCH / batch / 'raw' / code / 'INDEX.tsv').open(encoding='utf-8') as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            if row['category'] == 'periodic' and row['notice_date'] > best and not row['error']:
                best = row['notice_date']
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('batch')
    ap.add_argument('--codes', default='')
    ap.add_argument('--review-date', default=beijing_now().date().isoformat())
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-research', action='store_true', help='只登记 §6.9 登记表，不动档案')
    ap.add_argument('--revision', default='', help='口径修订后重登的编号后缀，如 r1')
    args = ap.parse_args()
    kit = {s['code']: s for s in json.loads((SCRATCH / args.batch / 'kit_summary.json').read_text(encoding='utf-8'))}
    codes = [c.strip() for c in args.codes.split(',') if c.strip()] or list(kit)
    model_date, mv = model_values()
    paths = {r['security_code']: r['valuation_path'] for r in csv.DictReader((EXP / 'queue.csv').open(encoding='utf-8'))}
    rows, specs, table = [], [], []
    for code in codes:
        errors, warns, j = check_delivery.check(code, args.batch, kit.get(code, {}))
        if errors:
            print(f'{code} 跳过（核对错误）：' + '；'.join(errors))
            continue
        md = next(m for m in (EXP / args.batch / 'companies').glob(f'{code}_*.md') if not m.name.endswith('_q3.md'))
        evidence_rel = str(md.relative_to(ROOT))
        rows.append(registry_row(j, args.batch, args.review_date, mv.get(code), evidence_rel, args.revision))
        npn = j['normalized_parent_np_2026_yi']
        if not paths.get(code, '').startswith('ROIC'):
            print(f"{code} {j['security_name']}：{paths.get(code)} 路径，不登记档案研究数")
        else:
            specs.append(dict(
                security_code=code, security_name=j['security_name'], review_id=rows[-1]['review_id'],
                evidence_date=evidence_date(args.batch, code, j['price_date']),
                parent_yi={k: round(float(npn[k]), 2) for k in ('bear', 'base', 'bull')},
                falsifier='；'.join(f"{x['condition']}（{x['deadline']} 前）" for x in j['falsifiers'][:3]),
                source=f"OI-291 池内独立审计（{REPORT}，{evidence_rel}）"))
        print(f"{code} {j['security_name']}：独立 V {j['v_weighted']:.2f}，P/V {j['pv']:.3f}（{j['verdict']}）；"
              f"模型 V {mv.get(code, float('nan')):.2f}" + (f"；提示：{'；'.join(warns)}" if warns else ''))
        spec = specs[-1] if specs and specs[-1]['security_code'] == code else None
        table.append(table_row(j, mv.get(code), paths.get(code, ''), spec))
    if table:
        print(f"\n模型 V 取 {model_date} 扫描；研究数按 §6.5.2.2 折算（亿元），差距 = 研究数与模型锚的较大者 ÷ 较小者 − 1。\n")
        print('| 代码 | 名称 | 现价 | 模型 V | 模型 P/V | 独立 V（熊～牛） | 独立 P/V | 独立分档 | 研究数（熊～牛） | 模型锚 | 差距 | 档案 |')
        print('| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |')
        print('\n'.join(table))
    if args.dry_run or not rows:
        return
    append_registry(rows)
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_independent_valuations.py')], cwd=ROOT, check=True)
    for spec in specs:
        (EXP / 'research' / f"{spec['security_code']}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if args.no_research:
        print('只登记了 §6.9 登记表；研究数输入已写 research/，档案未动')
        return
    ok, msg = research_window()
    print(msg)
    if not ok:
        return
    for spec in specs:
        res = subprocess.run([sys.executable, str(TOOLS / 'register_research.py'), str(EXP / 'research' / f"{spec['security_code']}.json")],
                             cwd=ROOT, capture_output=True, text=True)
        print((res.stdout + res.stderr).strip())


if __name__ == '__main__':
    main()
