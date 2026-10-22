# Valid Point findings package — current index

**Current revision: r2, 2026-10-22 (Asia/Kolkata).**
- Revision 1 (written earlier the same day) is preserved byte-for-byte in [revisions/r1_2026-10-22/](revisions/r1_2026-10-22/README.md); see the [revision notes](revisions/README.md). Its evidence files remain in `evidence/` (everything except `evidence/r2/`).
- Repository audited: HEAD `14371e6bee024544678481c0976641ba495dbda6`, with `planning/` untracked and `src/.DS_Store` modified before this audit. Nothing outside `planning/findings/` was changed.
- This package retires the old research direction. It authorizes no experiment and validates no new method.

## Executive brief

**Terminal state.** Stage R05 (four-fold comparison) is **finalized**:
- manifest sealed 2026-10-17 19:30:20.963181 UTC (2026-10-18 01:00:20 IST);
- gate PASS, five executed notebooks, stored 134-test pass;
- 15,561 of 15,565 outputs and 35/35 sources re-hashed matching in this audit.

Four status documents still say "GR5 pending" and are **stale**: `planning/progressplan.md`, `planning/checklist.md`, `planning/history.md` H020 and `artifacts/20261017T190338Z-R05-review/README.md`. R06/R07 never ran; mini_14 is not present locally. [ST-02–ST-04]

**What it measured.** Self-referential per-stream point-cloud statistics:
- D, count surplus in 32 cells;
- G, directed temporal voxel novelty;
- each memoryless or EWMA, on one sender's digitally edited clouds.

There was no learned feature, detector or ground-truth evaluation. [MT-01–MT-15, DA-15]

**Strongest useful findings.**
- Engineering: strict I/O, causal clocks, evaluator-isolation tests, deterministic attack ledgers, explicit undefined states.
- Complete negative tables that reconcile exactly.
- RSU sensor origins corroborated by data.
- Label format and licence verified on the current HF card.

**Most important failures.**
1. The objective is mismatched: D is blind to removal and within-cell moves; nothing scores correctness.
2. **New:** organized clouds contain repeated placeholder points at sensor origins, likely no-returns: 21–25% of vehicle `003`/`004` points, 37–39% of `top`, 2–13% of `laser`/`dome`. They dominated the D near cell and the attack targets.
3. 270/360 attack cells for the sender **could not alarm at all**. Null or saturated thresholds were caused by 156 under-supported and 21 saturated calibration cells.
4. Clean clips 1–2 minutes apart look maximally anomalous to each other (229/249 saturated). The four test clips span 208.6 s of one recording.
5. Early S03/S04 "results" are algebraic fixtures and annotations.

**Do not inherit:** D/G equations and constants, the 1% target, sender reputation, clean-only training bans, S03/S04 numbers, exposed segments as test data, or the old environment.

## Reading order

1. [09 Portable handoff](09_portable_handoff.md): standalone; start here in a new environment.
2. [01 History and actual state](01_project_history_and_actual_state.md), including the contradiction register.
3. [02 Methodology and failure analysis](02_methodology_and_failure_analysis.md), including placeholders (§4).
4. [03 Dataset, GT and feature feasibility](03_dataset_ground_truth_and_feature_feasibility.md), including ray feasibility.
5. [04 Experiments and verified results](04_experiments_and_verified_results.md), with the complete grid and could-not-alarm vs missed.
6. [05 Reusable assets and migration](05_reusable_assets_and_migration_spec.md).
7. [06 Requirements for the new study](06_requirements_for_the_new_study.md).
8. [07 Literature questions and candidates](07_literature_questions_and_candidate_methods.md).
9. [08 Reproducibility, resources, notebooks](08_reproducibility_resources_and_notebook_lessons.md).

**Machine-readable files:**
- [evidence_ledger.csv](evidence_ledger.csv): every finding ID cited in prose;
- [asset_inventory.csv](asset_inventory.csv);
- [results_summary.csv](results_summary.csv): compact, with filters and denominators;
- [audit_scope.json](audit_scope.json);
- [evidence_manifest.json](evidence_manifest.json): SHA-256 of sources used and of package files.

**Scripts and evidence:** [evidence/README.md](evidence/README.md).

## Evidence status vocabulary

| Status | Meaning |
|---|---|
| `verified_current_code` | Read in the current working tree; says nothing about efficacy |
| `verified_saved_result` | Re-parsed or recomputed from saved records or local files in this audit (scope stated) |
| `reported_not_reverified` | Taken from an old artifact or document without repeating the check |
| `analytic_limitation` | Follows mathematically from inspected code |
| `constructed_example` | Toy or fixture case; never a population estimate |
| `hypothesis` | Proposed interpretation or idea, unvalidated |
| `contradicted` | Old claim refuted by stronger evidence |
| `not_implemented` | Absent from the audited code |
| `unresolved` | Evidence insufficient |

## Audit scope in one paragraph

Read closely:
- all current planning documents and R-stage prompts, plus the archived contract and audit;
- all R-stage scoring, replay, overlay, calibration and metric code;
- the S03/S04 fixtures and the isolation test;
- the R-stage boundary tests.

Parsed: all R05 tables, the calibration score records, the 244 attempt ledgers, the manifest, logs and environment records; source notebooks by cell.

Read-only data inspection: 15 odometry CSVs, 25 sampled PCD bodies, saved archive inventories, TAR sizes.

Excluded: mini_14 (absent), TAR and bulk-PCD hashing (historic hashes only), label bodies, sibling repositories, test and notebook execution, visual review of every figure.

Details are in [audit_scope.json](audit_scope.json).
