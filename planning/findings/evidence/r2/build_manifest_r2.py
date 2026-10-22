"""Build planning/findings/evidence_manifest.json (SHA-256 of evidence used and package files).

Usage: python3 -I build_manifest_r2.py <valid_point_repo_root>
The manifest excludes its own hash. Large inputs are listed with historical hashes only.
"""
import hashlib, json, os, sys, datetime
ROOT = os.path.abspath(sys.argv[1]); PKG = os.path.join(ROOT, 'planning', 'findings')
RUN = 'artifacts/20261012T134149Z-R05'

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

sources = [
 'src/valid_point/evidence/density.py', 'src/valid_point/evidence/temporal_geometry.py', 'src/valid_point/evidence/kinematics.py',
 'src/valid_point/temporal.py', 'src/valid_point/evaluation/real.py', 'src/valid_point/evaluation/metrics.py',
 'src/valid_point/evaluation/statistics.py', 'src/valid_point/development_scores.py', 'src/valid_point/replay.py',
 'src/valid_point/io/mixed_signals.py', 'src/valid_point/attacks/overlays.py', 'src/valid_point/ablations.py',
 'src/valid_point/evaluation/gap.py', 'tests/test_gt_isolation.py', 'tests/test_replay_isolation.py', 'tests/test_evaluation.py',
 'pyproject.toml', 'configs/replay_evaluation.json', 'configs/segment_roles.json',
 'planning/evidence_audit.md', 'planning/progressplan.md', 'planning/checklist.md', 'planning/history.md',
 'planning/03_phase1_evidence.md', 'planning/06_attack_simulation.md', 'planning/dataset_field_matrix.md', 'planning/sources.md',
 'artifacts/20261017T190338Z-R05-review/README.md',
] + [f'{RUN}/{x}' for x in ('manifest.json', 'gate.md', 'notebook_execution.json', 'test_final.log', 'environment_start.json',
    'environment_final.json', 'resource_amendment.json', 'implementation_correction_clock_availability.json', 'execution.log',
    'prediction_seal.json', 'T_R05_attempt_flow.csv', 'T_R05_clean_support.csv', 'T_R05_metrics.csv', 'T_R05_grouped.csv',
    'T_R05_paired_effects.csv', 'T_R05_episode_outcomes.csv', 'T_R05_integrity.csv', 'T_R05_sessions.csv', 'T_R05_failures.csv',
    'calibration/F0/scores.jsonl.gz', 'calibration/F1/scores.jsonl.gz', 'calibration/F2/scores.jsonl.gz', 'calibration/F3/scores.jsonl.gz',
    'evaluator/C0/target.json', 'evaluator/C1/target.json', 'evaluator/C2/target.json', 'evaluator/C3/target.json')]
base = 'data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91'
sources += [f'{base}/manifests/mini_{i}_safe_member_inventory.json' for i in (10, 11, 12, 13)] + ['artifacts/20261008T192922Z-R01/safe_member_inventory.json']
sources += sorted(os.path.relpath(os.path.join(dp, f), ROOT) for dp, _, fs in os.walk(os.path.join(ROOT, base, 'raw', 'Odometry')) for f in fs if f.endswith('.csv'))
local = {p: sha(os.path.join(ROOT, p)) for p in sources}
probe = json.load(open(os.path.join(PKG, 'evidence/r2/placeholder_probe.json')))
for x in probe:
    local[f"{base}/raw/{x['file']}"] = x['sha256']
pkg = {}
for dp, dn, fs in os.walk(PKG):
    for f in fs:
        p = os.path.join(dp, f); rel = os.path.relpath(p, PKG)
        if rel == 'evidence_manifest.json' or f == '.DS_Store': continue
        pkg[rel] = sha(p)
man = {
 'schema': 'valid_point.findings.evidence_manifest.r2',
 'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repository_head': '14371e6bee024544678481c0976641ba495dbda6',
 'note': 'locally_recomputed hashes were computed by this script on the date above. historical hashes are assertions copied from old manifests and were NOT recomputed here. The manifest excludes its own hash.',
 'locally_recomputed_source_evidence_sha256': dict(sorted(local.items())),
 'locally_recomputed_in_audit_not_listed_individually': 'audit_r2.py re-hashed 15,561/15,565 R05 manifest outputs and 35/35 source entries against artifacts/20261012T134149Z-R05/manifest.json (see evidence/r2/audit_r2_report.json hash_checks)',
 'historical_hash_assertions_not_recomputed': {
   'R05 freeze canonical hash': '80694538e8549256934b3a314301cc8ca821efe0bf36ff4071eab9681f2c039c',
   'TAR archives and 5,008 C0-C3 extracted files': 'asserted matching pins in artifacts/20261012T134149Z-R05/intake/*.json and history H019; not recomputed',
   'mini_7 TAR': 'asserted in artifacts/20261008T192922Z-R01 and history H013; not recomputed',
   'all 748 prediction files / 309,752 raw rows': 'asserted by artifacts/20261017T190338Z-R05-review/audit.json; prediction files are covered by the r2 output re-hash, raw-row semantics not rechecked'},
 'package_files_sha256': dict(sorted(pkg.items())),
}
json.dump(man, open(os.path.join(PKG, 'evidence_manifest.json'), 'w'), indent=1)
print(len(local), 'source hashes;', len(pkg), 'package files')
