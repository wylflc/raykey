"""Daily input provenance and all-or-fail publication; workflow §8/§9.1."""
from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import math
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def stamp(path, as_of=None, inputs=()):
    """A successful writer proves even an empty CSV belongs to the requested day."""
    path = Path(path)
    value = dict(as_of=as_of or datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat(),
                 generated_at_utc=datetime.now(timezone.utc).isoformat(),
                 sha256=digest(path), inputs={str(Path(p).resolve()): digest(p) for p in inputs})
    atomic_json(path.with_suffix(path.suffix + '.meta.json'), value)


def verify_stamp(path, as_of):
    path = Path(path)
    meta = json.loads(path.with_suffix(path.suffix + '.meta.json').read_text())
    if meta['as_of'] != as_of or meta['sha256'] != digest(path):
        raise ValueError(f'文件日期或摘要不符：{path}')
    for p, expected in meta.get('inputs', {}).items():
        if digest(p) != expected:
            raise ValueError(f'上游输入已改变，须重建 {path}：{p}')
    return meta


def read_required(path, columns, allow_empty=False):
    path = Path(path)
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not set(columns) <= set(reader.fieldnames or ()):
            raise ValueError(f'缺必要列 {set(columns) - set(reader.fieldnames or ())}：{path}')
        rows = list(reader)
    if not rows and not allow_empty:
        raise ValueError(f'必需输入为空：{path}')
    seen = set()
    for row in rows:
        code = row.get('security_code')
        if code is not None:
            if not code.isdigit() or len(code) != 6 or code in seen:
                raise ValueError(f'代码为空、无效或重复：{path} {code}')
            seen.add(code)
    return rows


def action_rows(path=None):
    """事件库逐笔明细，按代码分组。"""
    from backtest_valuation_strategy import ACTIONS
    by_code = {}
    with Path(path or ACTIONS).open(newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            by_code.setdefault((row.get('security_code') or '').strip(), []).append(row)
    return by_code


def stale_exright_bands(bands, as_of, actions=None):
    """§9.1 第 2～3 步：带文件中除权事件未折到信号日的行，[(代码, 名称, 应折事件, 已折事件)]。

    应折事件按事件库与 §11.4 价格口径重算（`exright_events`），与 `exright_note` 所记逐事件比对；
    新除权日、事后登记的价格口径和事件库订正都会检出。银行与保险不在带文件折算，不检查。
    """
    from apply_forecast_band_overlay import exright_events, exright_hits
    with Path(bands).open(newline='', encoding='utf-8-sig') as f:
        rows = [r for r in csv.DictReader(f) if exright_events(r, [], as_of) is not None]
    if not rows:
        return []
    by_code = action_rows() if actions is None else actions
    stale = []
    for band in rows:
        code = (band.get('security_code') or '').strip()
        due = '；'.join(exright_hits(exright_events(band, by_code.get(code, []), as_of)))
        done = (band.get('exright_note') or '').partition('：')[2].strip()
        if due != done:
            stale.append((code, band.get('security_name') or code, due, done))
    return stale


def report_exright(as_of, since, model_bands, hold_bands):
    """§9.1 第 2 步检出：列出须核对实施公告的除权池成员，以及带未折到信号日的行；后者非空返回 1。"""
    from corporate_actions import company_events
    by_code = action_rows()
    with Path(model_bands).open(newline='', encoding='utf-8-sig') as f:
        members = {(r.get('security_code') or '').strip(): r.get('security_name') or '' for r in csv.DictReader(f)}
    due = [(e['ex_dividend_date'][:10], code, name, e) for code, name in sorted(members.items())
           for e in company_events(by_code.get(code, []), price_basis=True)
           if since < (e.get('ex_dividend_date') or '')[:10] <= as_of]
    print(f'池成员除权（{since}，{as_of}]：{len(due)} 起' + ('，逐只按实施公告核对价格口径（§11.4）' if due else ''))
    for ex, code, name, e in sorted(due):
        registered = e['price_terms_source'] != 'unverified_actual_fallback'
        print(f"  {ex} {code} {name}：除权参考价口径 现金 {float(e['cash_per_share']):.10g}／送转 {float(e['share_ratio']):.10g}"
              f"／配股 {float(e['rights_ratio']):.10g}｜"
              + (f"已登记（{e['price_terms_source']}）" if registered else '未登记，现按实付值'))
    failed = 0
    for path in (model_bands, hold_bands):
        stale = stale_exright_bands(path, as_of, by_code)
        failed += len(stale)
        print(f'{Path(path).name}：带未折到信号日 {len(stale)} 行' + ('，须跑 §6.7 第 4～6 步' if stale else ''))
        for code, name, want, have in stale:
            print(f"  {code} {name}：应折 {want or '无'}｜已折 {have or '无'}")
    return 1 if failed else 0


def validate_inputs(args):
    import screen_daily_volume_price_signals as s
    required = {
        args.input: (('security_code',), False),
        args.review_queue: (('security_code', 'buy_blocked', 'as_of'), True),
        args.tiers: (('security_code', 'quality_tier', 'tactical_thesis'), False),
        args.holdings: (('security_code', 'current_shares', 'cost_basis', 'entry_stop_price'), True),
        args.triage: (('security_code', 'attention_class'), False),
        args.model_bands: (('security_code', 'intrinsic_value', 'available_at'), False),
        args.hold_bands: (('security_code', 'intrinsic_value', 'available_at'), False),
    }
    if getattr(args, 'cigar_pool', None) is not None:   # §6.10 第 5 条：烟蒂股持仓的判定输入
        required[args.cigar_pool] = (('security_code', 'status', 'price', 'market_cap_yi', 'v_cb_yi', 'v_cb_reviewed_yi'), True)
    rows = {p: read_required(p, *spec) for p, spec in required.items()}
    if args.symbols:
        raise ValueError('执行模式须扫描完整输入池；按代码预览不发布交易计划')
    if not math.isfinite(args.nav) or args.nav <= 0 or args.funds is None or not math.isfinite(args.funds):
        raise ValueError('执行模式需要当日有效 --nav 与 --funds')
    for row in rows[args.holdings]:
        shares = float(row['current_shares'])
        if not math.isfinite(shares) or shares < 0:
            raise ValueError('持仓股数无效')
        for key in ('cost_basis', 'entry_stop_price'):
            if row[key] and (not math.isfinite(float(row[key])) or float(row[key]) <= 0):
                raise ValueError(f'持仓 {key} 无效')
    for row in rows[args.review_queue]:
        if row['as_of'] != s.evidence_iso_for_signal(args.as_of):
            raise ValueError('复核队列不是信号日快照')
    verify_stamp(args.review_queue, args.as_of)
    triage = rows[args.triage]
    if any(r['attention_class'] not in {'worth_attention', 'boundary_pending', 'garbage', 'documented_not_attention'} for r in triage):
        raise ValueError('三类表含未知状态')
    members = {r['security_code'] for r in triage if r['attention_class'] == 'worth_attention'}
    tiers = {r['security_code']: r for r in rows[args.tiers]}
    pool_codes = {r['security_code'] for r in rows[args.input]}
    if any(c not in tiers or tiers[c]['quality_tier'] not in {'L1', 'L2', 'L3', 'L4'} for c in pool_codes & members):
        raise ValueError('名单内候选缺有效分层')
    proof = json.loads(args.evidence_proof.read_text())
    if proof.get('as_of') != args.as_of or proof.get('status') != 'complete':
        raise ValueError('缺同日证据阶段完成证明')
    for path, expected in proof['inputs'].items():
        if digest(path) != expected:
            raise ValueError(f'证据阶段后输入已改变：{path}')
    if not pool_codes <= set(proof.get('covered_codes', [])):
        raise ValueError('新增候选未被证据阶段覆盖，须重新同步证据')
    for path in (args.model_bands, args.hold_bands):   # §9.1 第 3 步：两侧带须已折到信号日
        stale = stale_exright_bands(path, args.as_of)
        if stale:
            raise ValueError(f'带未折到信号日（{Path(path).name}），先按 §9.1 第 2 步跑 §6.7 第 4～6 步：'
                             + '、'.join(f'{name}（应折 {want or "无"}｜已折 {have or "无"}）'
                                        for _, name, want, have in stale[:8]))
    from backtest_valuation_strategy import ACTIONS, load_actions
    from apply_holdings_corporate_action import DEFAULT_LEDGER, load_ledger, ledger_index
    applied = ledger_index(load_ledger(DEFAULT_LEDGER))
    acts = load_actions()
    for h in rows[args.holdings]:
        if float(h['current_shares']) <= 0:
            continue
        code = h['security_code']
        if code not in proof.get('covered_codes', []):
            raise ValueError(f'持仓未被证据阶段覆盖：{code}')
        # The daily proof covers the gap since the prior successful scan.
        for day in acts.get(code, {}):
            if proof['since'] < day <= args.as_of and (code, day) not in applied:
                raise ValueError(f'公司行动尚未回写持仓：{code} {day}，先按 §11.4 处理')
    paths = set(required) | {args.evidence_proof, args.review_queue.with_suffix('.csv.meta.json'), ACTIONS}
    paths.update(Path(p) for p in proof['inputs'])
    if DEFAULT_LEDGER.exists():
        paths.add(DEFAULT_LEDGER)
    from check_report_day_price_divergence import DEFAULT_REVIEWS   # §7.5.2 复带登记：登记后解除拦截
    if DEFAULT_REVIEWS.exists():
        paths.add(DEFAULT_REVIEWS)
    from screen_pool_events import DEFAULT_REGISTER   # §7.4 负面事件登记：待复核行冻结买入，处置后须重建队列
    if DEFAULT_REGISTER.exists():
        paths.add(DEFAULT_REGISTER)
    for extra in (getattr(args, 'business', None), getattr(args, 'dossiers', None)):   # §9.3.6 成长股登记与重点复核记录
        if extra is not None and Path(extra).exists():
            paths.add(Path(extra))
    if args.cash is None or args.debt is None:
        s.account_cash_debt(args.as_of, args.cash, args.debt)
        paths.add(s.SEC93_ACCOUNT_SNAPSHOT)
    else:
        s.account_cash_debt(args.as_of, args.cash, args.debt)
    return {str(p.resolve()): digest(p) for p in paths}


class Publication:
    """Manifest is the commit record. Recover an interrupted run before reading state."""
    def __init__(self, status, as_of, outputs):
        self.status, self.as_of = Path(status), as_of
        self.outputs = [Path(p).resolve() for p in outputs]
        if len(set(self.outputs)) != len(self.outputs) or self.status.resolve() in self.outputs:
            raise ValueError('发布路径不能重复')
        self.committed = False
        self.installing = False

    def __enter__(self):
        self.status.parent.mkdir(parents=True, exist_ok=True)
        self.lock = self.status.with_suffix('.lock').open('a')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = json.loads(self.status.read_text()) if self.status.exists() else {}
        if previous.get('status') == 'running' and previous.get('phase') == 'installing':
            self.restore(previous['backups'])
        self.directory = Path(tempfile.mkdtemp(prefix='.daily_publish_', dir=self.status.parent))
        self.backups = {}
        for i, path in enumerate(self.outputs):
            backup = self.directory / f'backup_{i}'
            if path.exists():
                shutil.copyfile(path, backup)
            self.backups[str(path)] = str(backup) if backup.exists() else None
        atomic_json(self.status, dict(status='running', phase='prepared', as_of=self.as_of, backups=self.backups))
        return self

    @staticmethod
    def restore(backups):
        for path, backup in backups.items():
            if backup is None:
                Path(path).unlink(missing_ok=True)
            else:
                shutil.copyfile(backup, path)

    def stage(self, path):
        target = self.directory / ('stage_' + str(self.outputs.index(Path(path).resolve())))
        if Path(path).exists() and not target.exists():
            shutil.copyfile(path, target)
        return target

    def publish(self, staged, inputs, before_commit=lambda: None):
        for path, expected in inputs.items():
            if digest(path) != expected:
                raise ValueError(f'运行期间输入变化，须重跑：{path}')
        for path, backup in self.backups.items():
            current = digest(path) if Path(path).exists() else None
            original = digest(backup) if backup else None
            if current != original:
                raise ValueError(f'运行期间输出被其他任务修改：{path}')
        atomic_json(self.status, dict(status='running', phase='installing', as_of=self.as_of, backups=self.backups))
        self.installing = True
        for target, source in staged.items():
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
        before_commit()
        atomic_json(self.status, dict(status='complete', as_of=self.as_of, inputs=inputs,
                                     outputs={str(p): digest(p) for p in self.outputs if p.exists()}))
        self.committed = True

    def __exit__(self, kind, error, traceback):
        try:
            if not self.committed:
                if self.installing:
                    self.restore(self.backups)
                atomic_json(self.status, dict(status='failed', as_of=self.as_of, reason=str(error or '未提交')))
            shutil.rmtree(self.directory)
        finally:
            fcntl.flock(self.lock, fcntl.LOCK_UN)
            self.lock.close()


def verify_publication(status, as_of):
    value = json.loads(Path(status).read_text())
    if value.get('status') != 'complete' or value.get('as_of') != as_of:
        raise ValueError('本信号日没有成功发布的执行计划')
    for path, expected in {**value.get('inputs', {}), **value['outputs']}.items():
        if digest(path) != expected:
            raise ValueError(f'发布后产物已改变：{path}')
    return value


def finish_evidence(as_of, since):
    """Called only after all evidence collectors succeeded; queue may be rebuilt later."""
    if since >= as_of:
        raise ValueError('证据起点须早于信号日')
    paths = [ROOT / p for p in ('data/interim/a_share_report_disclosures.csv',
                                'data/interim/a_share_earnings_forecasts.csv',
                                'data/raw/corporate_actions/a_share_corporate_actions.csv')]
    for p in list(paths):
        verify_stamp(p, as_of)
        paths.append(p.with_suffix(p.suffix + '.meta.json'))
    paths.append(ROOT / 'data/reference/a_share_action_component_exclusions.csv')
    paths.append(ROOT / 'data/reference/a_share_exright_terms.csv')
    paths.append(ROOT / 'data/reference/a_share_action_component_corrections.csv')
    for name in ('announcements', 'corporate_actions', 'market_context'):
        path = ROOT / f'data/interim/daily_{name}_{as_of}.json'
        value = json.loads(path.read_text())
        if value['signal_date'] != as_of:
            raise ValueError(f'证据日期不符：{path}')
        paths.append(path)
        if name == 'announcements':
            if value['query_start'] > since or value['queried_all_market_rows'] < value['reported_total_hits']:
                raise ValueError('公告证据区间或分页不完整')
            covered = value['locally_filtered_codes']
    path = ROOT / f'data/interim/pool_event_hits_{as_of}.json'   # §7.4 负面事件筛查：当日、同区间、全覆盖
    value = json.loads(path.read_text())
    if value['signal_date'] != as_of or value['since'] > since:
        raise ValueError(f'负面事件筛查的日期或区间不符：{path}')
    if not set(covered) <= set(value['covered_codes']):
        raise ValueError('负面事件筛查未覆盖全部池与持仓代码，须重跑 screen_pool_events.py')
    if value['news_failed_codes'] and not value.get('news_gaps_allowed'):
        raise ValueError('负面事件筛查的新闻源有缺口，重跑或加 --allow-news-gaps')
    paths.append(path)
    atomic_json(ROOT / f'data/interim/daily_evidence_{as_of}.json',
                dict(status='complete', as_of=as_of, since=since, covered_codes=covered,
                     inputs={str(p.resolve()): digest(p) for p in paths}))


def verify_strategy_columns(as_of, snapshot=None):
    """§9.1 第 5 步／§10.3：信号日账户快照行存在，且到信号日为止的策略列已登记并与重算一致。"""
    import strategy_return_tracker as tracker
    path = Path(snapshot) if snapshot else tracker.SNAPSHOT
    _, rows = tracker.load(path)
    if not any(row.get('as_of') == as_of for row in rows):
        raise ValueError(f'账户快照缺少 {as_of} 行（§10.3）')
    problems = tracker.check_rows(rows, upto=as_of, require_filled=True)
    if problems:
        raise ValueError('§10.3 策略列未登记或与重算不一致：' + '；'.join(problems[:5]))


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('evidence', 'verify', 'exright'))
    parser.add_argument('--as-of', required=True)
    parser.add_argument('--since')
    parser.add_argument('--publication', type=Path, default=ROOT / 'data/processed/daily_execution_publication.json')
    parser.add_argument('--model-bands', type=Path, default=ROOT / 'data/processed/a_share_pool_model_bands_adopted.csv')
    parser.add_argument('--hold-bands', type=Path, default=ROOT / 'data/processed/a_share_pool_model_bands_hold.csv')
    args = parser.parse_args()
    if args.action == 'verify':
        verify_publication(args.publication, args.as_of)
        verify_strategy_columns(args.as_of)
        print('执行批次日期、产物摘要与 §10.3 策略列均通过')
        return 0
    if not args.since:
        parser.error(f'{args.action} requires --since (previous successful scan date)')
    if args.action == 'exright':
        return report_exright(args.as_of, args.since, args.model_bands, args.hold_bands)
    finish_evidence(args.as_of, args.since)
    print('同日证据阶段完成')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
