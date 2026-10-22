# Evidence audit and corrections — 2026-10-08

Audit baseline: repository HEAD `205dfb3c021de7d3ce5321272b2e28d1944d2498`, initially clean working tree. Read all current planning documents and S00–S10 prompts, package modules, tests, runner scripts/configs, source notebooks and stored execution evidence. No applicable AGENTS.md was found in the repository or ancestor locations checked. No sibling project was read. The [code inventory](audit/2026-10-08-code-inventory.json) records the inspected source hashes.

Read-only verification checked **22 existing manifests and 1,172 listed output hashes: zero mismatches**; this verifies byte integrity, not scientific validity. Parsed stored notebook code/output records and execution counts, including failed runs; did not rerun stages or tests during this planning revision. [Verification details](audit/2026-10-08-artifact-verification.json) include failures and notebook counts. Prior bundle failures (socket permissions, S03 KeyError) and H008's packaging correction remain intact. Additional S00/S02 reruns do not add independent scientific observations.

## What exists and what it proves

| Work | Meaningfully exercised computation and evidence | Scope limit |
| --- | --- | --- |
| S00 | Hash/provenance, fresh kernel, import origin and export checks; [6-test gate](../artifacts/20261005T094948Z-b2d74f78/gate.md) | Infrastructure, not science; environment tied to recorded versions/platform |
| S01 | Small seeded scene, rigid-transform round trips, geometry and synthetic JSON reader, absent/empty contracts; [9-test gate](../artifacts/20261005T103202Z-d2f4b72b/gate.md) | One template with small randomized target position; no real sensor noise, time replay or independently sampled scene population |
| S02 | Latest causal motion pairs, units, rotation, stale/future exclusion, half-open counts, explicit availability; [53-test gate and three notebooks](../artifacts/20261005T135710Z-6e4710d8/gate.md) | Literal hand inputs: useful arithmetic/counterexamples; not empirical detection |
| S03 | Quantile fitting/fallback, max combination, unknown coverage and calibration order statistic; [59-test gate](../artifacts/20261008T091758Z-d1642764/gate.md) | Raw numbers generated algebraically; no clouds/odometry processed into fit/calibration observations |
| S04 | 400 fixed tiles, counts and 12 constructed oracle/GT-free comparisons; [67-test gate](../artifacts/20261008T103246Z-cbed4e64/gate.md) | Limited function execution and fixture behavior; incomplete isolation/eligibility tests and constructed calibration |
| Real replay/evaluation | None. No raw PCD/CSV, production Mixed Signals adapter, intervention pipeline or temporal scorer | No dataset-performance, calibrated sensor-FPR, real attack-delay or recovery evidence |

The stored S03 result has 1,200 clean test decisions at A=0, calibration c=0 and 0/400 alarms. This follows `clean_fixture_rows` in [ablations.py](../src/valid_point/ablations.py): seed/frame arithmetic directly emits residuals/counts. Disjoint integers and `illustrative_scene_<seed>` names do not create independent scenes; S01 geometry is not even called. Support across named “segments” exercises bookkeeping only. Frame-level Wilson intervals do not quantify real-scene uncertainty. Component ablations share the max threshold and are diagnostic, not separately calibrated operating-point comparisons.

S04 `_reference_rows` in [evaluation/gap.py](../src/valid_point/evaluation/gap.py) cycles small literal count patterns. `fit_track_calibration` emits `reference.u` or `reference.u+1`, normalizes those directly, and does not run calibration clouds through the operational measurement path. Separate bundles and integer seed ranges are separate objects/IDs, not independently processed clean observations. `kinematic_penalty=0.0` is supplied for every constructed case; K is not measured.

Stored S04 arithmetic is supported: 3/7 attack alarms for tiles versus 5/7 for boxes, 2/5 benign alarms each, one abstention each; common-known attacks 3/6 versus 5/6. [Result ledger](../artifacts/20261008T103246Z-cbed4e64/spatial_gap_result.json) records these **constructed-case counts**, not estimated dataset rates. They demonstrate count blind spots and benign counterexamples, not a universal failure of all GT-free methods.

## Corrections to H009/H010 and prior acceptance rows

1. **GT isolation was overclaimed.** [test_gt_isolation.py](../tests/test_gt_isolation.py) assigns local `withheld=None` and reversed labels, then calls `_operational_scores()` again with unchanged inputs. Neither alteration is passed across an evaluator/inference boundary. Signature inspection excludes a few top-level argument names but `cases` is a generic mapping and this is not an end-to-end access test. Source separation is encouraging; invariance under withheld/changed GT, attack schedules and evaluator data is **not demonstrated**. Previous checklist G01 and H010's “tests prove” sentence are corrected here and in H011. R02 requires actual boundary tests and a leakage-positive control.
2. **S04 does not enforce the S02 operational contract.** [gt_free.py](../src/valid_point/gt_free.py) accepts already transformed arrays, availability and caller-supplied K. It checks receipt versus deadline and grid freeze versus deadline, but receives no source time/anchor, transform validity, pose age or transform provenance. S02 `measure_availability` is not called. Context is computed but not used to choose/verify the supplied reference. `decide` applies one broad reference to every count without the S03 `required_regions` eligibility function. Default counting emits all 400 tiles, but that is not full contextual reference/eligibility validation; caller-constructed partial measurements can bypass the intended universe. The vehicle role is hard-coded. No production replay path joins these contracts yet.
3. **Proposal/association failures are annotations.** There is no proposal generator or association algorithm whose miss/merge/split rate was measured. `proposal_state`/`association_state` strings are fixture labels; oracle passes association state through. Measured tile/box count differences are valid; measured proposal/association performance is not. Do not carry those labels into a failure-rate claim.
4. **Gate labels exceed their scope.** S04 `run_spatial_experiment` returns constant `technical='PASS'` and `G3='FAIL_NEGATIVE_RESULT'`; runner/test require this exact failure marker. Preserve that artifact as a constructed negative finding and a justified block on readiness, but not a learned/estimated scientific viability test. Technical execution succeeded; complete operational eligibility, empirical calibration and adversarial GT-boundary claims remain incomplete. New gates compute technical checks separately from scientific outcomes; no expected sign of effect is required.
5. **Old status documents are stale.** Root README says no scientific algorithms and offers “run all stages”; package already includes S01–S04. The earlier empty-package and synthetic-first descriptions remain historically true only at setup. Current canonical plan supersedes them; do not follow the old runner chain automatically. R02 will align execution documentation as implementation changes occur.

## Kinematic feasibility

[measure_motion](../src/valid_point/evidence/kinematics.py) computes `||(p1-p0)-R0*v0*(t1-t0)||` in metres using the latest two eligible positions and **prior** velocity (body or receiver frame) plus orientation when needed. Tests meaningfully cover a 3-4-5 residual, legitimate acceleration (0.25 m), missing velocity and a self-consistent spoof (0 m). There is no point-cloud input. Point-only interventions holding pose/velocity fixed cannot change K by construction; that is an analytic limitation, not a dataset result.

Pinned [dataset reader evidence](sources.md) establishes documented positions, orientation and odometry stamps, but no populated measured velocity. Deriving velocity from the same displacement under test is tautological. A prior-interval difference predicts subsequent displacement but measures trajectory smoothness, with shared pose dependency and acceleration/turning confounds. K is therefore kept as a tested optional motion diagnostic, removed from required cloud-integrity scoring. Real CSV inspection can refine feasibility, not manufacture independence.

## Module disposition

| Module/group | Decision | Required action before real research |
| --- | --- | --- |
| `provenance.py`, immutable runners/export patterns | Keep/adapt | Preserve new-run semantics; generalize S00-only schemas and record new clocks, factor and state versions; avoid hard-coded scientific gates |
| `contracts.py`, `evidence/availability.py` | Adapt | Typed replay event/provenance boundary; enforce source/arrival/pose/transform validity in the actual call path, retain partial and unknown records |
| `evidence/kinematics.py` | Keep diagnostic; defer core use | Require measured velocity provenance or explicitly pose-derived diagnostic; never infer point integrity |
| `io/pointcloud.py` | Keep for toy regression; add real adapter | Current reader is synthetic JSON, not PCD. Clean and attacked PCDs must share the new production reader |
| `evidence/spatial.py`, `regions.py` | Keep count/geometry primitives; adapt | Benchmark vectorized bounded counting; do not preserve 5 m/[-1,1) tiles as dataset defaults |
| `references.py`, `calibration.py`, `scoring.py` | Adapt | Real raw lineage, sensor contexts, per-arm calibration, configurable required factors; no fake seed scenes or IID confidence claims |
| `gt_free.py` | Replace operational wrapper | Connect actual eligibility, typed inputs, full context/support requirements; preserve fixture behavior as historical regression |
| `synthetic.py`, `ablations.py`, `evaluation/gap.py`, `oracle.py` | Keep illustrative evidence; defer oracle research | Separate toy adapters from actual fitting/evaluation; no promoted dataset claims |
| `evidence/__init__.py`, old notebooks/scripts/tests | Keep historical | Reuse valid hand checks; new R notebooks/runners and meaningful integration tests |
| Replay, PCD overlays, temporal state, real metrics | Missing | Implement only in separately invoked R stages |
| Consensus, bandwidth, detector/AP, learned combination | Defer | No evidence or dependency needed for primary question |

Existing artifacts and code were not repaired or rewritten in this planning turn. The audit makes missing integration explicit instead of retrospectively awarding a broader pass.
