"""Revision-2 read-only audit of saved Valid Point R05 evidence.

Usage:  python3 -I audit_r2.py <valid_point_repo_root> <output_dir>

Standard library only. Reads saved CSV/JSON/JSONL.GZ evidence, recomputes summaries,
re-derives R05 thresholds from saved calibration scores, and hashes bounded files.
It never writes outside <output_dir> and never reads holdout (mini_14) data.
"""
from __future__ import annotations
import csv, gzip, hashlib, json, math, os, sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
RUN = os.path.join(ROOT, 'artifacts', '20261012T134149Z-R05')
SEGS = ('C0', 'C1', 'C2', 'C3')
FOLD_OF = {'C0': 'F0', 'C1': 'F1', 'C2': 'F2', 'C3': 'F3'}
CAL_OF = {'C0': 'C1', 'C1': 'C2', 'C2': 'C3', 'C3': 'C0'}
SENSORS = ('003', '004', 'laser', 'top', 'dome')
ARMS = ('D-only', 'G-only', 'max(D,G)')
VERSIONS = ('memoryless', 'EWMA', 'EWMA_tau_0.25', 'EWMA_tau_2')
MAX_HASH_BYTES = 12_000_000
os.makedirs(OUT, exist_ok=True)


def rd(name):
    with open(os.path.join(RUN, name), newline='') as h:
        return list(csv.DictReader(h))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def wcsv(name, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(os.path.join(OUT, name), 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def fnum(x):
    return None if x in ('', None) else float(x)


report = {'run': '20261012T134149Z-R05', 'script': 'audit_r2.py'}

# ---------------------------------------------------------------- calibration
cs = rd('T_R05_clean_support.csv')
cal = [r for r in cs if r['support_type'] == 'calibration']
ref = [r for r in cs if r['support_type'] == 'reference']
report['reference_contexts'] = {'rows': len(ref), 'status': Counter(r['status'] for r in ref),
                                'by_factor_status': Counter(f"{r['factor']}:{r['status']}" for r in ref)}
low_support = Counter((r['sensor'], r['factor'], r['context']) for r in ref if r['status'] == 'LOW_SUPPORT')
zero_scale = Counter((r['sensor'], r['factor'], r['context']) for r in ref if r['status'] == 'ZERO_SCALE')
report['reference_low_support_contexts'] = sorted(f'{a}|{b}|{c}|folds={n}' for (a, b, c), n in low_support.items())
report['reference_zero_scale_contexts'] = sorted(f'{a}|{b}|{c}|folds={n}' for (a, b, c), n in zero_scale.items())

# Re-derive thresholds from saved calibration score records.
recomputed = {}
for seg in SEGS:
    fold = FOLD_OF[seg]
    vals = defaultdict(list)
    attempts = Counter()
    with gzip.open(os.path.join(RUN, 'calibration', fold, 'scores.jsonl.gz'), 'rt') as h:
        for line in h:
            r = json.loads(line)
            k = (r['sensor'], r['arm'], r['version'])
            attempts[k] += 1
            if r['score'] is not None:
                vals[k].append(float(r['score']))
    for s in SENSORS:
        for a in ARMS:
            for v in VERSIONS:
                x = sorted(vals[(s, a, v)]); n = len(x); k = math.ceil((n + 1) * .99)
                c = None if n < 200 else 1.0 if k > n else x[k - 1]
                recomputed[(seg, s, a, v)] = {'n': n, 'attempts': attempts[(s, a, v)], 'k': k, 'c': c,
                                              'n_at_one': sum(1 for y in x if y >= 1.0),
                                              'n_unique': len(set(x)), 'n_zero': sum(1 for y in x if y == 0.0),
                                              'n_above_c': None if c is None else sum(1 for y in x if y > c)}
cal_rows = []
mismatch = 0
for r in cal:
    key = (r['segment'], r['sensor'], r['arm'], r['version'])
    rc = recomputed[key]
    c = fnum(r['threshold'])
    same = (c is None and rc['c'] is None) or (c is not None and rc['c'] is not None and abs(c - rc['c']) < 1e-12)
    mismatch += (not same) or int(r['known']) != rc['n']
    if r['status'] == 'INSUFFICIENT_KNOWN':
        meaning = 'THRESHOLD_NULL_FEWER_THAN_200_KNOWN'; can_alarm = False
    elif r['status'] == 'NO_POWER' and c is not None and c >= 1:
        meaning = 'THRESHOLD_1_FROM_CLIPPED_SATURATED_CALIBRATION_SCORES_CANNOT_ALARM'; can_alarm = False
    elif r['status'] == 'NO_POWER':
        meaning = 'CONSTANT_CALIBRATION_SCORES_THRESHOLD_%g_CAN_ALARM_ON_SCORE_ABOVE' % c; can_alarm = True
    else:
        meaning = 'AVAILABLE'; can_alarm = True
    cal_rows.append({'test_segment': r['segment'], 'fold': r['fold'], 'calibration_segment': r['calibration_segment'],
                     'sensor': r['sensor'], 'arm': r['arm'], 'version': r['version'], 'saved_status': r['status'],
                     'saved_threshold': r['threshold'], 'saved_known': r['known'], 'saved_attempts': r['attempts'],
                     'order_index_k': r['order_index'], 'recomputed_threshold': '' if rc['c'] is None else rc['c'],
                     'recomputed_known': rc['n'], 'threshold_matches': same,
                     'calibration_scores_at_1': rc['n_at_one'], 'calibration_scores_zero': rc['n_zero'],
                     'calibration_unique_values': rc['n_unique'], 'meaning': meaning, 'alarm_possible': can_alarm})
wcsv('calibration_cells_r2.csv', cal_rows)
thr = {(r['test_segment'], r['sensor'], r['arm'], r['version']): r for r in cal_rows}
report['calibration'] = {'cells': len(cal_rows), 'saved_status': Counter(r['saved_status'] for r in cal_rows),
                         'meaning': Counter(r['meaning'].split('_%')[0] if 'CONSTANT' not in r['meaning'] else 'CONSTANT_CALIBRATION_SCORES' for r in cal_rows),
                         'recompute_mismatches': mismatch,
                         'k_exceeds_n_cases': sum(1 for v in recomputed.values() if v['n'] >= 200 and v['k'] > v['n']),
                         'no_power_c1_min_scores_at_1': min((r['calibration_scores_at_1'] for r in cal_rows if r['meaning'].startswith('THRESHOLD_1')), default=None),
                         'available_by_sensor_arm': Counter(f"{r['sensor']}|{r['arm']}" for r in cal_rows if r['alarm_possible']),
                         'sender003': [{k: r[k] for k in ('test_segment', 'arm', 'version', 'saved_status', 'saved_threshold', 'saved_known', 'calibration_scores_at_1', 'meaning')}
                                       for r in cal_rows if r['sensor'] == '003']}

# ---------------------------------------------------------------- metrics
metrics = rd('T_R05_metrics.csv')
M = {}
for r in metrics:
    M[(r['segment'], r['kind'], r['family'], r['severity'], r['schedule'], r['sensor'], r['arm'], r['version'], r['population'], r['metric'])] = r

grouped = rd('T_R05_grouped.csv')
gmis = 0
G = defaultdict(lambda: [0, 0, 0])
for (seg, k, f, sv, sc, s, a, v, pop, m), r in M.items():
    acc = G[(k, f, sv, sc, s, a, v, m)]
    acc[0] += int(r['numerator']); acc[1] += int(r['denominator']); acc[2] += 1
for g in grouped:
    n, d, segs = G[(g['kind'], g['family'], g['severity'], g['schedule'], g['sensor'], g['arm'], g['version'], g['metric'])]
    if n != int(g['micro_numerator']) or d != int(g['micro_denominator']) or segs != 4:
        gmis += 1
report['grouped_reconciliation'] = {'grouped_rows': len(grouped), 'metric_rows': len(metrics), 'micro_mismatches': gmis}

specs = sorted({(r['kind'], r['family'], r['severity'], r['schedule']) for r in metrics})
attack_specs = [s for s in specs if s[0] == 'attack']
grid = []
for (k, f, sv, sc) in attack_specs:
    for a in ARMS:
        for v in VERSIONS:
            row = {'family': f, 'severity': sv, 'schedule': sc, 'arm': a, 'version': v}
            tot_n = tot_d = cap_n = cap_d = elig_n = elig_d = 0; capable = []
            for seg in SEGS:
                rec = M[(seg, k, f, sv, sc, '003', a, v, 'scheduled_sender', 'all_attempt_recall')]
                el = M[(seg, k, f, sv, sc, '003', a, v, 'scheduled_sender', 'eligible_recall')]
                n, d = int(rec['numerator']), int(rec['denominator'])
                t = thr[(seg, '003', a, v)]
                row[f'{seg}_alarms'] = n; row[f'{seg}_attempts'] = d
                row[f'{seg}_eligible'] = int(el['denominator'])
                row[f'{seg}_threshold'] = t['saved_threshold']; row[f'{seg}_calibration'] = t['saved_status']
                row[f'{seg}_alarm_possible'] = t['alarm_possible']
                tot_n += n; tot_d += d; elig_n += int(el['numerator']); elig_d += int(el['denominator'])
                if t['alarm_possible']:
                    cap_n += n; cap_d += d; capable.append(seg)
            row.update(all_attempt_alarms=tot_n, all_attempts=tot_d, eligible_alarms=elig_n, eligible_events=elig_d,
                       alarm_capable_segments=';'.join(capable), alarms_in_capable_segments=cap_n,
                       attempts_in_capable_segments=cap_d)
            grid.append(row)
wcsv('sender003_attack_grid_r2.csv', grid)
report['attack_grid'] = {'cells': len(grid), 'positive_cells': sum(1 for r in grid if r['all_attempt_alarms'] > 0),
                         'cells_with_no_alarm_capable_segment': sum(1 for r in grid if not r['alarm_capable_segments']),
                         'cells_with_capable_segment_but_zero_alarms': sum(1 for r in grid if r['alarm_capable_segments'] and r['all_attempt_alarms'] == 0),
                         'positive': [{k: r[k] for k in ('family', 'severity', 'schedule', 'arm', 'version', 'all_attempt_alarms', 'all_attempts', 'alarm_capable_segments', 'alarms_in_capable_segments', 'attempts_in_capable_segments', 'C0_alarms', 'C1_alarms', 'C2_alarms', 'C3_alarms')} for r in grid if r['all_attempt_alarms'] > 0]}

# Control rates: clean, identity (pooled over families) and benign, every sensor.
ctrl = []
for (k, f, sv, sc) in specs:
    if k == 'attack':
        continue
    for s in SENSORS:
        for a in ARMS:
            for v in VERSIONS:
                pop = k
                row = {'kind': k, 'family': f, 'severity': sv, 'schedule': sc, 'sensor': s, 'arm': a, 'version': v}
                tn = te = ta = 0
                for seg in SEGS:
                    fp = M[(seg, k, f, sv, sc, s, a, v, pop, 'eligible_fpr')]
                    aa = M[(seg, k, f, sv, sc, s, a, v, pop, 'all_attempt_alarm_rate')]
                    row[f'{seg}_alarms'] = int(fp['numerator']); row[f'{seg}_eligible'] = int(fp['denominator'])
                    row[f'{seg}_attempts'] = int(aa['denominator'])
                    tn += int(fp['numerator']); te += int(fp['denominator']); ta += int(aa['denominator'])
                row.update(alarms=tn, eligible=te, attempts=ta, eligible_fpr='' if te == 0 else tn / te,
                           status='UNDEFINED_NO_ELIGIBLE' if te == 0 else 'defined')
                ctrl.append(row)
wcsv('control_rates_r2.csv', ctrl)
clean = {(r['sensor'], r['arm'], r['version']): r for r in ctrl if r['kind'] == 'clean'}
report['clean_controls'] = {f'{s}|{a}|{v}': f"{clean[(s,a,v)]['alarms']}/{clean[(s,a,v)]['eligible']} (attempts {clean[(s,a,v)]['attempts']}) " + ' '.join(f"{seg}:{clean[(s,a,v)][seg+'_alarms']}/{clean[(s,a,v)][seg+'_eligible']}" for seg in SEGS)
                            for s in SENSORS for a in ARMS for v in ('memoryless', 'EWMA')}
ben003 = [r for r in ctrl if r['kind'] == 'benign' and r['sensor'] == '003' and r['arm'] == 'D-only' and r['version'] == 'memoryless']
report['benign_003_D_memoryless'] = [f"{r['family']}={r['severity']} {r['schedule']}: {r['alarms']}/{r['eligible']}" for r in ben003]
iden = [r for r in ctrl if r['kind'] == 'identity' and r['sensor'] == '003' and r['arm'] == 'D-only' and r['version'] == 'memoryless']
report['identity_003_D_memoryless'] = [f"{r['family']}: {r['alarms']}/{r['eligible']}" for r in iden]

# ---------------------------------------------------------------- attempt flow
flow = rd('T_R05_attempt_flow.csv')
fl = Counter()
for r in flow:
    fl[f"episodes:{r['kind']}"] += 1
    for c in ('attempts', 'scheduled_events', 'reader_valid', 'injection_failed', 'sender_events', 'companion_events'):
        fl[f"{r['kind']}:{c}"] += int(r[c] or 0)
report['attempt_flow'] = {'rows': len(flow), 'per_segment_kinds': Counter(f"{r['segment']}:{r['kind']}" for r in flow), 'totals': fl,
                          'sender_events_per_segment': {seg: sorted({int(r['sender_events']) for r in flow if r['segment'] == seg and r['sender_events']}) for seg in SEGS}}

fails = rd('T_R05_failures.csv')
att = [r for r in fails if r['kind'] == 'attack' and r['cloud_id']]
fam = defaultdict(Counter)
for r in att:
    c = fam[r['family']]
    c['events'] += 1
    c['reader_valid'] += r['reader_valid'] == 'True'
    c['injection_failed'] += r['injection_failed'] == 'True'
    c['zero_realized'] += (r['realized_changed_rows'] or '0') in ('0', '0.0')
    c['failed_rows'] += int(float(r['failed_rows'] or 0)); c['intended_rows'] += int(float(r['intended_rows'] or 0))
    c['nonzero_cell_l1'] += (r['changed_cell_count_l1'] or '0') not in ('0', '0.0')
report['attack_event_ledger_from_failures_csv'] = {k: dict(v) for k, v in fam.items()}
report['failures_csv_status'] = Counter(r['status'] for r in fails)

# Realized change per family from compact evaluator attempt ledgers (small gz files).
real = defaultdict(Counter)
for r in flow:
    if r['kind'] == 'clean':
        continue
    p = os.path.join(RUN, 'evaluator', r['segment'], r['episode'], 'attempts.jsonl.gz')
    key = f"{r['kind']}:{r['family']}"
    with gzip.open(p, 'rt') as h:
        for line in h:
            a = json.loads(line)
            c = real[key]
            c['events'] += 1
            c['reader_valid'] += bool(a.get('reader_valid'))
            c['injection_failed'] += bool(a.get('injection_failed'))
            c['realized_nonzero'] += (a.get('realized_changed_rows') or 0) > 0
            c['failed_rows'] += int(a.get('failed_rows') or 0)
            c['intended_rows'] += int(a.get('intended_rows') or 0)
            c['changed_rows'] += int(a.get('realized_changed_rows') or 0)
            c['nonzero_cell_l1_events'] += (a.get('changed_cell_count_l1') or 0) > 0
            c['status:' + str(a.get('status'))] += 1
report['realized_by_kind_family'] = {k: dict(v) for k, v in sorted(real.items())}

# ---------------------------------------------------------------- outcomes
outc = rd('T_R05_episode_outcomes.csv')
st = Counter(); rec = Counter(); fin = Counter(); pre = 0
seen_final = {}
for r in outc:
    st[json.loads(r['delay'])['status']] += 1
    rec[json.loads(r['recovery'])['status']] += 1
    pre += r['preexisting_alarm'] == 'True'
    seen_final[(r['segment'], r['episode'], r['sensor'], r['arm'], r['version'])] = json.loads(r['final_recovery'])['status']
for v in seen_final.values():
    fin[v] += 1
det = [r for r in outc if json.loads(r['delay'])['status'] == 'DETECTED']
report['episode_outcomes'] = {'interval_rows': len(outc), 'delay_status': st, 'interval_recovery_status': rec,
                              'preexisting_alarm_rows': pre, 'final_recovery_status_dedup_episode_arm_version': fin,
                              'detected_rows': [f"{r['segment']} {r['family']} {r['severity']} {r['schedule']} {r['arm']} {r['version']} int{r['interval']} delay={json.loads(r['delay'])['value_s']} rec={json.loads(r['recovery'])}" for r in det]}

# ---------------------------------------------------------------- paired effects
pe = rd('T_R05_paired_effects.csv')
pf = defaultdict(list)
for r in pe:
    if r['sensor'] == '003' and r['arm'] == 'D-only' and r['version'] == 'memoryless' and r['field'] == 'C' and r['kind'] == 'attack':
        pf[r['family']].append(float(r['mean_attacked_minus_clean']))
report['paired_C_003_D_memoryless'] = {f: {'cells': len(v), 'min': min(v), 'max': max(v), 'exact_zero_cells': sum(1 for x in v if x == 0.0)} for f, v in pf.items()}
report['paired_effect_fields'] = Counter(r['field'] for r in pe)

# ---------------------------------------------------------------- integrity / sessions
report['integrity'] = Counter(f"{r['check']}={r['pass']}" for r in rd('T_R05_integrity.csv'))
ses = rd('T_R05_sessions.csv')
report['sessions'] = [{**r, 'duration_s': (int(r['last_source_ns']) - int(r['first_source_ns'])) / 1e9} for r in ses]
gaps = []
for a, b in zip(ses, ses[1:]):
    gaps.append({'from': a['segment'], 'to': b['segment'], 'gap_s': (int(b['first_source_ns']) - int(a['last_source_ns'])) / 1e9})
report['session_gaps_between_segments'] = gaps
report['comparison_span_s'] = (int(ses[-1]['last_source_ns']) - int(ses[0]['first_source_ns'])) / 1e9

# ---------------------------------------------------------------- targets
report['attack_targets'] = {seg: json.load(open(os.path.join(RUN, 'evaluator', seg, 'target.json'))) for seg in SEGS}
for seg in SEGS:
    report['attack_targets'][seg].pop('prefix_cloud_ids', None)

# ---------------------------------------------------------------- hashes
man = json.load(open(os.path.join(RUN, 'manifest.json')))
hc = Counter(); mism = []; skipped_bytes = 0; hashed_bytes = 0
for rel, expected in man['output_sha256'].items():
    p = os.path.join(RUN, rel)
    if not os.path.exists(p):
        hc['missing'] += 1; mism.append(rel); continue
    size = os.path.getsize(p)
    if size > MAX_HASH_BYTES:
        hc['skipped_large'] += 1; skipped_bytes += size; continue
    got = sha(p); hashed_bytes += size
    if got == expected:
        hc['match'] += 1
    else:
        hc['mismatch'] += 1; mism.append(rel)
src = Counter(); smis = []
for rel, expected in man['source_sha256'].items():
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        src['missing'] += 1; smis.append(rel); continue
    if sha(p) == expected:
        src['match'] += 1
    else:
        src['mismatch'] += 1; smis.append(rel)
report['hash_checks'] = {'manifest_sealed_utc': man['sealed_utc'], 'manifest_sha256': sha(os.path.join(RUN, 'manifest.json')),
                         'output_entries': len(man['output_sha256']), 'output_result': hc, 'output_mismatch_or_missing': mism[:50],
                         'hashed_bytes': hashed_bytes, 'skipped_bytes_over_limit': skipped_bytes, 'per_file_limit_bytes': MAX_HASH_BYTES,
                         'source_entries': len(man['source_sha256']), 'source_result': src, 'source_mismatch_or_missing': smis,
                         'prediction_seal_sha256': sha(os.path.join(RUN, 'prediction_seal.json'))}
post = []
seal_mtime = os.path.getmtime(os.path.join(RUN, 'manifest.json'))
for dp, dn, fn in os.walk(RUN):
    for n in fn:
        p = os.path.join(dp, n)
        if n != '.DS_Store' and os.path.getmtime(p) > seal_mtime + 1:
            post.append(os.path.relpath(p, RUN))
report['files_modified_after_manifest_mtime_excluding_DS_Store'] = post

json.dump(report, open(os.path.join(OUT, 'audit_r2_report.json'), 'w'), indent=1, default=str, sort_keys=True)
print(json.dumps({k: report[k] for k in ('calibration', 'grouped_reconciliation', 'attack_grid', 'hash_checks')}, indent=1, default=str)[:6000])
