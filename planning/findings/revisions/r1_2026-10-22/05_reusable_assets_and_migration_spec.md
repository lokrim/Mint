# Reusable assets and migration specification

Reuse engineering contracts without importing the old estimand. The [asset inventory](asset_inventory.csv) gives original path, dependency, exposure, input/output contract, limitations, adaptation work and a concrete validation check for each item. The table below is its readable disposition summary. Exact original files stay in Valid Point; only selected evidence excerpts/configuration are included here. [F008,F011–F018,F026,F030–F043]

| Asset | Disposition | Migration purpose / required validation |
|---|---|---|
| `src/valid_point/io/mixed_signals.py` | adapt | Strict PCD and pose adapter; Malformed-token/count/nonfinite tests; exact known transform and independently checked landmark alignment |
| `src/valid_point/replay.py` | adapt | Causal inputs and raw records; Withheld evaluator, denied filesystem read, negative clock skew and future-prefix perturbation tests |
| `src/valid_point/evidence/density.py` | adapt | Count primitive / negative baseline; Exact half-open boundary and per-cell-preserving counterexample |
| `src/valid_point/evidence/temporal_geometry.py` | reimplement | Directed geometry baseline; Compare bounded small cases to exact nearest neighbors; dynamic/occlusion and work-budget tests |
| `src/valid_point/evidence/kinematics.py` | defer | Optional motion diagnostic; Point-only invariance; known acceleration and consistent spoof examples |
| `src/valid_point/temporal.py` | adapt | Explicit missing/warm-up state machine; Irregular-time recurrence; missing/reset; checkpoint/prefix invariance |
| `src/valid_point/attacks/overlays.py` | adapt | Deterministic point interventions; Identity reload; same-key reproducibility; exact per-cell constraints; GT task change |
| `src/valid_point/evaluation/real.py` | reimplement | Lineage, scoring, replay orchestration; No evaluator inference access; exact split roles; cache equivalence under changed history |
| `src/valid_point/evaluation/metrics.py` | adapt | Explicit denominators and censoring; Hand-calculated failed injection, zero support, preexisting alarm and recovery cases |
| `src/valid_point/evaluation/statistics.py` | adapt | Paired/grouped summaries; Independent table reconciliation; duplicate segment/episode checks; null preservation |
| `src/valid_point/evaluation/splits.py` | adapt | Split and lineage guards; No frame leakage, shared target/clean variants grouped, exact required reference sets |
| `src/valid_point/provenance.py` | adapt | Hash/export pattern; Byte mutation detected, no overwrite, manifest excludes itself |
| `src/valid_point/ablations.py` | discard-as-research | Algebraic examples; Never cite as measured scene population |
| `src/valid_point/evaluation/gap.py` | discard-as-research | Constructed tile/box gap; No dataset/association rate claim |
| `tests/test_gt_isolation.py` | discard-as-research | Historical incomplete isolation check; Deliberate leak must fail identical harness |
| `tests/test_mixed_signals.py` | adapt | Time/frame/reader contracts; Include failure-triggering controls and exact input provenance |
| `tests/test_replay_isolation.py` | adapt | Mutation/prefix/history boundary; Include failure-triggering controls and exact input provenance |
| `tests/test_evaluation.py` | adapt | Split/clock/seal/report tests; Include failure-triggering controls and exact input provenance |
| `tests/test_overlays.py` | adapt | Deterministic perturbation constraints; Include failure-triggering controls and exact input provenance |
| `tests/test_temporal.py` | adapt | Temporal invariants; Include failure-triggering controls and exact input provenance |
| `configs/replay_evaluation.json` | keep | Historical exact experiment; Current hash matches used version |
| `configs/segment_roles.json` | adapt | Historical exposure and hashes; No holdout opening during planning; all variants grouped |
| `notebooks` | adapt | Research explanation examples; Fresh kernel in new environment; one trace from input to task result |
| `artifacts/20261012T134149Z-R05` | keep | Historical negative/conditional evidence; Selected hash checks + full table reconciliation; never claim full fresh integrity |
| `reports` | keep | Historical figures/tables; Caption identifies population and fixture status |
| `requirements.lock` | defer | Historical resolved dependencies; Minimal encoder load and deterministic preprocessing check |
| `uv.lock` | defer | Later dependency record; New runtime compatibility and imported versions |

## Minimal migration contract

**Keep:** immutable raw-source identity, release attribution, exact event timestamps and clock meanings, stream/principal mapping, attempted/eligible/realized counters, original failure artifacts, deterministic seed keys, clean/attacked pairing, explicit unavailable values and per-scene reporting. Keep old tables as old-study evidence only. [F026,F033–F039,F046]

**Adapt:** strict input parser; transforms verified independently on the chosen release; inference-access boundary; state lifecycle; attack serialization; metrics and provenance. Adaptation must be validated against new feature unit, receiver inputs and task labels. Do not carry hidden hard-coded dataset roots, enum ordering in IDs, or implicit same-sender evidence independence. Hash canonical episode content with an explicit version instead of mapping enumeration order. [F008,F030,F036]

**Reimplement:** the perception feature-extraction/fusion interface and the actual reliability target. Existing `NormalizedFactors`, D/G CSVs and A/C/Z values are statistics of point clouds, not learned intermediate tensors or GT labels. Current point attacks can test feature robustness only by passing their realized clouds through the same frozen encoder/preprocessing; separately define direct feature attacks. [F037,F043]

**Discard as research evidence:** artificial S03 calibration/generalization, S04 proposal/association rates, vacuous early isolation claims, and a guaranteed descending severity curve. Preserve those files historically and retain useful arithmetic counterexamples with constructed labels. [F004–F007]

**Defer:** old dependency environment, quota/consensus policy, independent-velocity interpretation, unverified checkpoints, H access and any final paper novelty claim. Low memory/compute is a requirement to measure, not a reason to reuse old constants or claim the finalizer RSS as deployment cost. [F003,F009,F032,F044–F045]

A recommended reused asset passes its validation check in the new environment before contributing a scientific claim. A whole old runner is not a migration unit: it mixes path conventions, old scientific equations, artifact ownership and resource assumptions. New documentation should state what was borrowed, what was revalidated and what changed.
