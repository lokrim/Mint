# Reproducibility, resources and notebook lessons

Preserve reproducible measurements without reproducing heavyweight workflow overhead. This extraction ran standard-library table/record analysis only; no package imports, model training, replay, tests or notebook execution. Scripts live under [evidence](evidence/README.md) and write only this package. [F030–F032,F040–F042,F046–F049]

## Trustworthy practices versus overhead

| Retain/adapt | Avoid inheriting |
|---|---|
| Explicit dataset revision, source hashes, config identity, environment record and immutable outputs | Treating a checksum, successful kernel or gate label as a scientific result |
| Causal event/pose IDs; separate source and availability clocks; inference-access tests | Inference conditioned on evaluator schedules or clean alternatives |
| Deterministic overlays with actual production reload and intended/realized ledgers | Multiple full archive/extraction copies or simultaneous derived episodes |
| Per-scene tables with nulls and failure statuses; paired clean/attack evidence | Counting frames, seeds, repeated companions or shared-fold fits as independent scenes |
| Small reproducible explanation plus complete machine results | Repeated huge Markdown exports, redundant figures and completion-label notebooks |
| Snapshot-specific provenance and resumable checkpoints | Episode IDs tied to iteration order; partial-directory collisions; final-version-only provenance |

## Environment and observed resources

`pyproject.toml` requires Python >=3.11, NumPy >=2,<3 and nbconvert >=7.17.2, with optional Jupyter/matplotlib/pytest stack. Historical locks and stored environment records are separate evidence: final R05 reports Python 3.14.4 and NumPy 2.5.4 on macOS/Clang. Do not import this environment into a detector project without checking the chosen model’s official supported stack. No specific model/library incompatibility was tested here; GPU/runtime/checkpoint support is unresolved. [F032,F037]

| Measurement / exact saved source | Recorded value and scope | What it cannot establish |
|---|---|---|
| R02 `artifacts/20261009T085704Z-R02/environment.json` | CPU 86.327268 s, wall 88.179544 s, peak RSS 209,420,288 bytes for that bounded development run | Per-device worst-case latency or encoder/fusion cost |
| Later R02 `20261012T043451Z-R02/environment.json` | CPU 91.317607 s, wall 92.832765 s, peak RSS 263,815,168 bytes; same development category | Independent scene replication or a universal memory bound |
| R03 `20261010T155346Z-R03/environment_final.json` | Runner before repairs: wall 1,950.328783 s, CPU 1,928.21655 s, peak RSS 429,801,472 bytes | Repairs explicitly not separately instrumented; not historical complete-work peak |
| R05 `resource_amendment.json` | Accepted 4,000,000,000-byte run plus one active derived-episode cap; archives/extracts retained separately | Achieved peak RSS or actual deployment RAM |
| R05 `environment_final.json` | Finalizer peak RSS 179,617,792 bytes; recorded run bytes 2,594,335,265; free disk 22,101,475,328 at that time | Earlier replay processes, notebook child memory, historical scratch peak or present free disk |

These are **saved measurements re-read**, not fresh benchmarks. R05 episode wall times in `execution.log` include different work/reuse paths and interruptions; dividing finalizer memory or cached replay timing by event count would not estimate deployed cost. macOS `ru_maxrss` is stored as bytes here; portable resource instrumentation must identify platform units and child processes. [F032]

## Preserved failures and their correction status

| Failure evidence | Disposition |
|---|---|
| Early S00/S01/S03/R04 fresh kernels denied localhost sockets | Execution-environment failure, later successful runs exist. No evidence against scientific hypothesis. |
| S03 `20261008T091349Z-79149ae5` KeyError `K+S` | Tied-factor summary handling repaired in later accepted S03 artifacts; artificial population remains. |
| R02 `20261009T085343Z-R02/failure.txt` | Native XY D unnecessarily depended on vehicle pose; corrected before accepted run. Font-cache plotting delay also recorded. |
| R03 `20261010T152207Z-R03/failure.txt` | Excessive unbounded candidate work interrupted; deterministic 10-million-pair guard added. Unknown-on-budget behavior needs measurement. |
| R03 `protocol_deviation/`, `execution_repair.log`, `notebook_error.txt` in accepted run | First rearrangement allowed outside-cell changes; corrected constraints and preserved partial failures. Notebook/geometry repairs documented. |
| R04 early blocked attempts | Incorrect metric fixture, missing pandas in fresh kernel, broad test collection of artifact snapshots; later exact-lineage and resample-copy repair. Scoped project suite and authoritative freeze succeeded. |
| R05 four `failure_20261013T*.json` files | One compact-evidence storage cap failure and three FileExistsError restarts; six prediction implementation snapshots remain. |
| R05 clock availability correction | Negative modeled skew must not advance actual pose availability; corrected helper/current test. Historic full-row audit reported no future original poses; not repeated for every row here. |
| R05 review seal / ID repair | Ignore only `.DS_Store`, retain scientific hashes; reconstruct IDs from original config order after canonical equality. Final reports exist; obsolete review commands not run. |

Sources are preserved in [run status extracts](evidence/run_status_and_failures.json), original run directories and [history](01_project_history_and_actual_state.md). Technical repairs do not retroactively establish independent labels, calibrated future FPR or task utility. [F030–F031,F041]

## Source notebooks versus executed evidence

All 99 notebook files in the included source/artifact categories were parsed for cell source, execution counts, output types/text and errors. Image payloads were not visually rendered; text extracts are bounded. This is content inspection, not execution or exhaustive visual QA. Fourteen source notebooks exist; only R01 contains executed code outputs in the source file (five code cells); the others are templates with null counts. Executed copies live in dated artifacts. [notebook cell inventory](evidence/notebook_cells.json)

| Source notebook(s) | What code actually computes or displays | Executed scope |
|---|---|---|
| `00_bootstrap` | Imports/environment/provenance and trivial exports, fresh-kernel checks | Infrastructure only; stored failures and successes |
| `01_synthetic_scenes` | Small seeded scene and transform/contract views | One synthetic family, no real perception |
| `02_kinematics`, `02_spatial_surplus`, `02_availability` | Calls importable hand-evidence routines, shows residual/count/eligibility tables and plots | Arithmetic/causality fixtures |
| `03_clean_references`, `03_score_and_ablations` | Invokes fixture generation, quantile fitting/scoring/calibration and exports | Algebraic S03 observations; no raw-cloud calibration |
| `04_gt_free_oracle_gap` | Constructs fixed tiles/box cases, calls comparison and plots | Twelve constructed cases; not proposals/association algorithms |
| `R01_development_intake` | Reads recorded schema/timing/geometry evidence and plots retained bounded geometry | Source file stored outputs; intake work performed by script |
| `R02_causal_factors` | Loads raw tables, displays timelines/alignment and boundary/resource records | Saved actual development measurements, not new comparison fit |
| `R03_replay_temporal` | Loads sealed predictions, contrasts geometry/timelines, computes diagnostic summaries; reads poses for display | Development-only; null alarm thresholds |
| `R04_protocol_freeze` | Loads config/roles, renders split/schedule diagrams, executes small metric arithmetic fixture | Metadata/protocol, not outcome evidence |
| `R05_segment_timelines` | Checks seal, reads saved raw/thresholds, previews tables, displays existing figures | Four executed segment notebooks, seven code cells each |
| `R05_grouped_evaluation` | Checks seal, previews saved tables, displays ablation/severity/failure figures | One executed grouped notebook, seven code cells |

R05 notebooks have meaningful source/provenance checks but mostly present existing results. Fresh execution of them does not independently regenerate raw measurements or train/evaluate a detector. The final stored suite records 134 tests, no failures; it was not rerun. Old report counts and stored output are evidence of the recorded execution, not current compatibility. [F040,F042]

## Next-project notebook acceptance

Each notebook should state one research question, population, deployment inputs and falsification condition; show a small real example with units/coordinate/time provenance; compute preprocessing and the selected feature/evidence step visibly through importable functions; derive the equation and one hand counterexample; expose intermediate arrays/summaries, unknown reasons and input dependencies; then evaluate against compatible GT and explain a success, a miss, a benign rejection and an unsupported unique view. Keep evaluator overlays visually distinct.

Include a bounded executable path with cached immutable large inputs, a reproducible full-table command, fresh-kernel execution, exact environment/model identity, resource measurement and a claim ledger. Present complete small grids and aggregate counts, not just `head()` rows plus “PASS.” Keep expensive replay optional and explicit; never make opening an explanatory notebook copy archives or start training. No generated notebook is supplied here because this task is an extraction, not the new study.
