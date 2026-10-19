#!/usr/bin/env python3
"""OI-291：核对一批代理交付（framework.md「交付」）。

逐家检查：
- `.json` 字段齐全、数值类型、概率和为 1、加权 V 与三情景一致、`P/V` = 现价 ÷ 加权 V、分档与 `P/V` 一致；
- 现价与股本同批快照一致；2025 年营收与归母净利、TTM 归母净利、最新归母权益与东财 F10 原始数据一致；
- 正常化归母净利三档有序、证伪条件 3～5 条、联网不超过 15 次；
- `calc/<代码>/valuation.py` 能运行，输出含三情景 V 与加权 V；全文存在且有来源节。

    python3 tools/check_delivery.py b01 [--codes 600066,688041]
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
EXP = TOOLS.parent
ROOT = EXP.parents[2]
SCRATCH = ROOT / 'data/scratch/experiments/exp_independent_pool_2026q3'
REQUIRED = ['security_code', 'security_name', 'price_date', 'price', 'shares_yi', 'latest_report', 'evidence_cutoff', 'q3_report_date',
            'coe', 'scenarios', 'v_weighted', 'pv', 'verdict', 'confidence', 'v_at_coe_8', 'v_at_coe_10', 'implied_irr', 'reverse_dcf',
            'normalized_parent_np_2026_yi', 'reported', 'net_cash_adj_yi', 'non_operating_assets_yi', 'growth_path', 'method', 'basis',
            'conclusion', 'key_events', 'key_metrics', 'risks', 'falsifiers', 'next_check', 'spot_checks', 'web_facts', 'web_calls']
VERDICTS = ('明显低估', '温和低估', '大致合理', '偏贵或价值陷阱风险高')


def bucket(pv: float) -> str:
    if pv <= 0.75:
        return VERDICTS[0]
    if pv <= 0.90:
        return VERDICTS[1]
    if pv <= 1.10:
        return VERDICTS[2]
    return VERDICTS[3]


def num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def f10_facts(code: str, batch: str) -> dict:
    d = json.loads((SCRATCH / batch / 'raw' / code / 'f10.json').read_text(encoding='utf-8'))
    inc = {(r.get('REPORT_DATE') or '')[:10]: r for r in d['income']}
    bal = {(r.get('REPORT_DATE') or '')[:10]: r for r in d['balance']}
    val = lambda r, k: float(r.get(k) or 0) / 1e8
    latest = max(bal) if bal else ''
    out = dict(latest=latest)
    if '2025-12-31' in inc:
        out['revenue_2025_yi'] = val(inc['2025-12-31'], 'TOTAL_OPERATE_INCOME')
        out['parent_np_2025_yi'] = val(inc['2025-12-31'], 'PARENT_NETPROFIT')
    if latest:
        out['parent_equity_latest_yi'] = val(bal[latest], 'TOTAL_PARENT_EQUITY')
    lat_inc = max(inc) if inc else ''
    if lat_inc and not lat_inc.endswith('12-31'):
        prev_end, same = f"{int(lat_inc[:4]) - 1}-12-31", f"{int(lat_inc[:4]) - 1}{lat_inc[4:]}"
        if prev_end in inc and same in inc:
            out['parent_np_ttm_yi'] = (val(inc[lat_inc], 'PARENT_NETPROFIT') + val(inc[prev_end], 'PARENT_NETPROFIT')
                                       - val(inc[same], 'PARENT_NETPROFIT'))
    elif lat_inc:
        out['parent_np_ttm_yi'] = val(inc[lat_inc], 'PARENT_NETPROFIT')
    return out


def run_script(path: Path) -> tuple[bool, str]:
    try:
        res = subprocess.run([sys.executable, '-I', path.name], cwd=path.parent, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return False, '超时'
    return res.returncode == 0, (res.stdout + res.stderr)


def check(code: str, batch: str, kit: dict) -> tuple[list[str], list[str], dict]:
    errors, warns = [], []
    comp = EXP / batch / 'companies'
    jpath = comp / f'{code}.json'
    if not jpath.exists():
        return [f'缺 {jpath.name}'], [], {}
    try:
        j = json.loads(jpath.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        return [f'json 解析失败：{exc}'], [], {}
    for k in REQUIRED:
        if k not in j:
            errors.append(f'缺字段 {k}')
    sc = j.get('scenarios') or {}
    ps, vs = [], []
    for name in ('bear', 'base', 'bull'):
        s = sc.get(name) or {}
        if not (num(s.get('v')) and num(s.get('p'))):
            errors.append(f'情景 {name} 缺 v 或 p')
        else:
            ps.append(s['p'])
            vs.append(s['v'])
    if len(ps) == 3:
        if abs(sum(ps) - 1) > 0.011:
            errors.append(f'概率和 {sum(ps):.3f}')
        wv = sum(p * v for p, v in zip(ps, vs))
        if num(j.get('v_weighted')) and abs(wv - j['v_weighted']) > max(0.02, 0.005 * abs(wv)):
            errors.append(f'加权 V {j["v_weighted"]} ≠ Σp·v {wv:.2f}')
        if not (vs[0] <= vs[1] <= vs[2]):
            warns.append(f'情景 V 未按熊≤基准≤牛排列：{vs}')
    price = j.get('price')
    if num(price) and num(j.get('v_weighted')) and j['v_weighted'] > 0:
        pv = price / j['v_weighted']
        if not num(j.get('pv')) or abs(pv - j['pv']) > 0.006:
            errors.append(f'P/V {j.get("pv")} ≠ 现价÷加权 V {pv:.3f}')
        if j.get('verdict') != bucket(pv):
            errors.append(f'分档「{j.get("verdict")}」与 P/V {pv:.3f} 的档「{bucket(pv)}」不符')
    if kit:
        if num(price) and abs(price - kit['price']) > 0.011:
            errors.append(f'现价 {price} ≠ 快照 {kit["price"]:.2f}')
        if num(j.get('shares_yi')) and abs(j['shares_yi'] / kit['shares_yi'] - 1) > 0.01:
            warns.append(f'股本 {j["shares_yi"]} 与快照 {kit["shares_yi"]:.4f} 相差 {j["shares_yi"] / kit["shares_yi"] - 1:+.1%}（A+H 或摊薄口径须在正文写明）')
    facts = f10_facts(code, batch)
    rep = j.get('reported') or {}
    for k, tol in (('revenue_2025_yi', 0.01), ('parent_np_2025_yi', 0.01), ('parent_np_ttm_yi', 0.02), ('parent_equity_latest_yi', 0.01)):
        if k in facts and facts[k]:
            if not num(rep.get(k)):
                errors.append(f'reported.{k} 缺')
            elif abs(rep[k] / facts[k] - 1) > tol:
                warns.append(f'reported.{k} {rep[k]:.2f} 与 F10 {facts[k]:.2f} 相差 {rep[k] / facts[k] - 1:+.1%}')
    npn = j.get('normalized_parent_np_2026_yi') or {}
    if all(num(npn.get(k)) for k in ('bear', 'base', 'bull')):
        if not (npn['bear'] <= npn['base'] <= npn['bull']):
            errors.append(f'正常化归母净利三档无序：{npn}')
    else:
        errors.append('normalized_parent_np_2026_yi 缺数')
    fals = j.get('falsifiers') or []
    if not 3 <= len(fals) <= 6:
        warns.append(f'证伪条件 {len(fals)} 条')
    for x in fals:
        if not (isinstance(x, dict) and x.get('condition') and x.get('deadline')):
            errors.append('证伪条件缺 condition 或 deadline')
            break
    if num(j.get('web_calls')) and j['web_calls'] > 15:
        warns.append(f'联网 {j["web_calls"]} 次，超过 15')
    if j.get('verdict') not in VERDICTS:
        errors.append(f'分档写法不在四档内：{j.get("verdict")}')
    script = EXP / batch / 'calc' / code / 'valuation.py'
    if not script.exists():
        errors.append('缺 valuation.py')
    else:
        ok, out = run_script(script)
        if not ok:
            errors.append(f'valuation.py 运行失败：{out[-200:]}')
        else:
            nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', out.replace(',', ''))]
            for label, v in [('加权 V', j.get('v_weighted'))] + list(zip(('熊', '基准', '牛'), vs)):
                if num(v) and not any(abs(n - v) <= max(0.011, 0.002 * abs(v)) for n in nums):
                    errors.append(f'valuation.py 输出未见{label} {v}')
    md = list(comp.glob(f'{code}_*.md'))
    md = [m for m in md if not m.name.endswith('_q3.md')]
    if not md:
        errors.append('缺全文')
    else:
        text = md[0].read_text(encoding='utf-8')
        if '来源' not in text:
            warns.append('全文没有「来源」')
        if len(text) < 8000:
            warns.append(f'全文仅 {len(text)} 字符')
    return errors, warns, j


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('batch')
    ap.add_argument('--codes', default='')
    args = ap.parse_args()
    kit = {s['code']: s for s in json.loads((SCRATCH / args.batch / 'kit_summary.json').read_text(encoding='utf-8'))}
    codes = [c.strip() for c in args.codes.split(',') if c.strip()] or list(kit)
    bad = 0
    print('| 代码 | 名称 | 现价 | 熊／基准／牛 | 加权 V | P/V | 分档 | 正常化归母（基准） | 联网 | 结果 |')
    print('| --- | --- | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |')
    notes = []
    for code in codes:
        errors, warns, j = check(code, args.batch, kit.get(code, {}))
        sc = j.get('scenarios') or {}
        trio = '／'.join(f"{(sc.get(k) or {}).get('v', '—')}" for k in ('bear', 'base', 'bull'))
        npb = (j.get('normalized_parent_np_2026_yi') or {}).get('base', '—')
        status = '错误' if errors else ('提示' if warns else '通过')
        bad += bool(errors)
        print(f"| {code} | {j.get('security_name', kit.get(code, {}).get('name', ''))} | {j.get('price', '—')} | {trio} | {j.get('v_weighted', '—')} | "
              f"{j.get('pv', '—')} | {j.get('verdict', '—')} | {npb} | {j.get('web_calls', '—')} | {status} |")
        notes += [f'{code} 错误：{e}' for e in errors] + [f'{code} 提示：{w}' for w in warns]
    if notes:
        print()
        print('\n'.join(notes))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
