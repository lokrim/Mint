# 01 — Project history and actual terminal state

Revision 2 (2026-10-22). Four predicates are kept apart throughout: **intended** (in a plan), **code present**, **executed** (saved run evidence), and **scientifically supported**.

## 1. Original question and S stages (5–8 Oct 2026)

The archived contract (`planning/archive/2026-10-08-pre-replan/01_research_contract.md`) asked whether ground-truth-free sender/frame **conformity** could detect corruption and later steer bandwidth quotas, using mandatory kinematic (K), spatial-count (S) and oracle-box parts.

| Stage | Code present | Executed | Supported scientifically |
|---|---|---|---|
| S00 | provenance, export, fresh-kernel infrastructure | yes, 6-test gate | infrastructure only |
| S01 | seeded toy scene, transform contracts | yes | arithmetic only |
| S02 | K residual, half-open counts, availability | yes, hand inputs | counterexamples only |
| S03 | quantile references, max score, calibration | yes, on **algebraic fixtures** (SC-01) | none: no real observations |
| S04 | tiles vs oracle boxes, GT-free wrapper | yes, 12 constructed cases | constructed gap only; isolation test vacuous (SC-03) |
| S05–S10 | prompts only (consensus, bandwidth, overlays, evaluation, real data, paper) | no | superseded |

## 2. October replan and R stages (8–18 Oct 2026)

The 8 October replan (history H011) retracted the S03/S04 overclaims (`planning/evidence_audit.md`) and replaced the program with **causal real-cloud replay**:
- D = per-cell count surplus; G = directed temporal novelty;
- memoryless and EWMA versions;
- deterministic point overlays;
- separate clean fit and calibration segments.

It explicitly deferred detectors/AP, learned fusion, consensus and bandwidth.

| Stage | Executed evidence (authoritative run) | Credited scope |
|---|---|---|
| R01 | `artifacts/20261008T192922Z-R01` | mini_7 schema, timing, frames for 250 clouds |
| R02 | `artifacts/20261009T085704Z-R02` (earlier failed run `…085343Z-R02` preserved) | raw D/G on development data; boundary checks |
| R03 | `artifacts/20261010T155346Z-R03` (interrupted `…152207Z-R03` preserved) | overlays, EWMA demonstration; thresholds null |
| R04 | `artifacts/20261010T211551Z-R04-80694538e854` (two blocked runs and one superseded seal preserved) | protocol freeze only |
| R05 | `artifacts/20261012T134149Z-R05` | four-fold comparison; **finalized** (ST-02) |
| R06/R07 | prompts only | **not run**: no artifact directory; mini_14 not local (ST-04) |

**Scope drift relative to the new objective.**
- *Unit.* The intended unit (a sender's frame) is already coarser than the new unit (an individual feature region or object hypothesis).
- *Evidence.* It became even more self-referential: each stream is judged only against its own past and against clean statistics from other clips.
- *Validation.* No task (GT) evaluation was ever in scope.
- *What R05 measured.* D on sender `003`, where by construction only additions can register. The tested additions were also mis-targeted at the sensor's own placeholder cell (DA-05).

The engineering improved steadily. The estimand moved away from usefulness.

## 3. Actual terminal state

- R05 has a final manifest sealed **2026-10-17T19:30:20.963181Z**, which is **2026-10-18 01:00:20 IST**.
- `gate.md` reads "Final GR5 technical status: PASS".
- `notebook_execution.json` lists five executed notebooks with status PASS, and `test_final.log` records "134 passed".
- I re-hashed 15,561 of 15,565 manifest outputs (4 SVGs over 12 MB skipped) and all 35 source entries. **All match.** No file other than Finder `.DS_Store` was modified after the manifest (RP-01).
- A technical PASS is not a scientific result.

## 4. Contradiction register

| Old claim (location) | Conflicting evidence | Resolution | Remaining uncertainty |
|---|---|---|---|
| "Predictions complete; reporting/notebooks and GR5 pending" (`planning/progressplan.md` R05 row; `planning/checklist.md` COMPARE row; `planning/history.md` H020; `artifacts/20261017T190338Z-R05-review/README.md`) | R05 `manifest.json` sealed 19:30:20Z on 17 Oct, gate PASS, 5 executed notebooks, `test_final.xml`, all `T_R05_*`/`F_R05_*` present and hash-matching | **Contradicted.** The status documents (last edited 18 Oct 00:35 IST) predate the finalize run (~00:59–01:00 IST). Do not run their continuation commands. | Who triggered finalize after H020 is not recorded in planning |
| S03 clean calibration across "segments"/seeds (H009, old checklist) | `ablations.clean_fixture_rows` arithmetic | Contradicted; retracted 8 Oct | — |
| S04 GT isolation verified (H010, old G01) | `tests/test_gt_isolation.py` lines 41–46 change unused locals | Contradicted; retracted 8 Oct | — |
| S04 proposal/association failure rates | `EvaluatorOutcome` annotations | Contradicted; retracted | — |
| R-stage boundary "verified" (checklist BOUNDARY) | Tests do rerun real pipelines with changed/withheld evaluator files, but the leak controls are toy functions and the guard patches only `Path.open` (SC-05) | Partially supported. Stronger than S04, not a sandbox. | Builtin `open`/`np.load` bypass not tested |
| Velocity unavailable / not populated (`dataset_field_matrix.md`, `overview.md`) | 6 variable twist columns in all 15 local CSVs | Contradicted as a blanket claim | Frame, provenance and independence unknown |
| `NO_POWER` = cannot alarm (common reading) | 10 constant-score cells have c = 0 and can alarm | Label is overbroad (MT-11) | — |
| c = 1 arises when k > n (`03_phase1_evidence.md` wording) | k ≤ n for every n ≥ 200; all 21 c = 1 cells come from saturated clean scores | Contradicted as an explanation (MT-10) | — |
| Localized removal / addition test "sender-observable geometry" (`06_attack_simulation.md`) | All targets are `r0:a0`, dominated by no-return placeholders, centred ~1–2 m from the sensor | **Newly contradicted in revision 2** (DA-05) | Placeholder semantics unverified |
| "All selected XYZ rows are finite" implies valid points (R01) | Finite, but ~21–25% of vehicle points are repeated placeholders | Correct but misleading (DA-02) | — |
| Comparison TARs absent (H018) | All four TARs present locally (H019; stat today) | Superseded | Acquisition history unrecorded |
| Labels absent ⇒ no GT | 289–291 label TXT members per archive inventory; HF card documents format | Contradicted | Index mapping and body validity unverified |
| Finalizer peak RSS 179,617,792 B as R05 cost | `environment_final.json` measures only the finalize process | Scope limited (RP-06) | Replay peak unmeasured |
| Revision 1 of this package is complete | Its README links `audit_scope.json`, `evidence_manifest.json` and `evidence/README.md`, which did not exist; it missed the placeholders and did not separate "could not alarm" from "missed" | Superseded by revision 2; r1 kept in [revisions/r1_2026-10-22/](revisions/r1_2026-10-22/) (ST-05) | — |
| Root `README.md` "current stage R02" | R03–R05 exist | Stale setup document | — |

## 5. Repairs and their scope

These repairs happened and are preserved with failure evidence:
- S03 KeyError for tied factors;
- R02 vehicle-D pose coupling;
- R03 unbounded neighbour work and outside-cell rearrangement (invalid ledgers retained);
- R04 failed-injection numerator, reference-subset lineage and grouped resample keys;
- R05 clock-skew availability (recorded as pre-outcome), the compact-evidence cap failure, three `FileExistsError` restarts (six prediction snapshots), the Finder-metadata seal exception and the episode-ID order reconstruction.

They make the old study internally consistent. None of them addresses the objective mismatch, the placeholder issue or the cross-segment shift.

The project is not "invalid" as a whole. Its strict I/O, causal boundaries, deterministic overlays, ledgers and full negative tables survive as engineering and as negative evidence. Its scientific claims cannot be generalized.
