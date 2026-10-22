# 09 — Portable handoff: retiring Valid Point

Standalone brief, revision 2, audited 2026-10-22 (Asia/Kolkata). Old-repo HEAD `14371e6bee024544678481c0976641ba495dbda6`; its `planning/` directory was untracked and was preserved. This package documents evidence. It is not runnable software and validates no new method.

## Objective of the next project

Estimate the time-varying reliability of **individual received intermediate features, feature regions or feature-supported object hypotheses** in cooperative LiDAR perception. Reliability means correct/useful versus misleading at a defined time and spatial/task unit, **not a persistent sender reputation**.

The project should test:
- whether harmful point or feature manipulations reduce reliability;
- how benign conditions confound it;
- whether using it improves downstream perception against ground truth, while honest unique viewpoints are preserved.

Negative results are acceptable. Low compute and memory matter; hardware is open.

## What Valid Point actually did

It replayed real Mixed Signals V2X LiDAR clips (three vehicles `003`, `004`, `laser`; one roadside unit with `top` and `dome` sensors). It edited one vehicle's raw points with deterministic digital overlays and scored each sensor stream per frame with two self-referential statistics:
- **D**: the maximum clipped surplus of point counts in 32 range/sector cells, relative to clean quantiles from two other clips;
- **G**: the 90th-percentile distance from current to previous voxel centroids after ego-motion compensation.

These came in memoryless and smoothed (EWMA) versions, each with thresholds calibrated on a third clean clip. There was no neural network, no intermediate feature, no detector and no ground-truth evaluation. The final four-fold comparison (R05) is technically complete: sealed 2026-10-18 01:00 IST, every output re-hash-verified here. Status files that still say it is "pending" are stale. The final holdout (mini_14) and the paper stage were never run.

## Five most consequential findings

1. **The old score cannot measure what the new project needs.** D cannot rise when points are removed, and is unchanged when points move within a cell. G only measures novelty against the stream's own (possibly attacked) history. Each stream is judged only by itself. Nothing links any score to object or feature correctness.
2. **Placeholder points (new).** Every cloud is an organized beam grid. 21–25% of vehicle `003`/`004` points, and 37–39% of RSU `top` points, are identical placeholder coordinates at the sensor origin, probably no-return beams (undocumented). They dominate the innermost count cell, so the old attack targeting picked that cell in every fold. "Localized removal" mostly deleted placeholders, and "addition" dropped a 2 m blob about 1–2 m from the sensor. Any new pipeline must handle placeholders explicitly. They may also be useful as a no-return mask for ray reasoning.
3. **Many "misses" were impossible to avoid.** For the attacked sender, 270 of 360 attack-grid cells had no fold where an alarm was mathematically possible: thresholds were null with fewer than 200 clean scores, or equal to 1 because clean scores saturated. The only alarms were D-only additions. The large addition alarmed on 199 of 199 events where alarming was possible, and could not alarm on the other 200.
4. **Neighbouring clips do not share a "normal" range.** References fitted on two clips labelled up to 92% of clean frames in another clip as maximally anomalous (229/249). Clean false alarms concentrate in particular clips (up to 98%). The four comparison clips span only 208.6 s of one recording, so they are not independent sessions.
5. **Engineering patterns are sound and worth reusing.** These are the strict reader, causal pose and time selection, evaluator/inference separation tests, deterministic keyed attacks with intended/injected/realized ledgers, explicit undefined/abstain states, and an independent reconciliation script. Their equations and constants are not.

## Verified reusable knowledge

- **Licence.** CC BY-NC-SA 4.0.
- **Labels.** One TXT file per sync index, `cls cx cy cz dx dy dz yaw`, in the `top` RSU frame. Boxes are limited to ±51.2 m and to more than 5 points; an empty file means no objects. Label IDs run 1–290 versus cloud sync IDs 0–298, so **verify the mapping**.
- **Frames.** RSU raw XYZ are in a map frame, with sensor origins (−41.551, −51.878, −1.077) and (−41.507, −51.864, −1.340); the placeholders sit exactly there. Vehicle clouds are native; placeholders at (0, 0, 1.63 or 1.90) suggest the sensor height.
- **Poses.** Quaternions are stored x, y, z, w by column name. A short sub-second field in filenames is left-padded. Streams are asynchronous, with ~50–60 ms skew between streams.
- **Velocity.** Six variable twist columns exist in the odometry; their frame and independence are unknown.
- **Intensity.** All zero for `003`/`004`.

## Warnings

- Do not inherit D/G, their constants, the 1% target, "clean-only" training bans, sender-level reputation or any S03/S04 number.
- mini_7 and mini_10–13 are exposed development data. Renaming the project does not make them test data.
- Sender-level trust can be weaponized: recent work (TrustFlip, arXiv 2605.22122) makes benign vehicles look inconsistent.
- A ray through a box is not proof of free space unless the box is truly occupied there. A missing return is not free space. Latent features contain no rays.

## Candidate ideas (unvalidated)

- The colleague's support/traversal-ray idea. Prior art includes CARLO and CAD; novelty is unestablished.
- Visibility-aware occupancy consistency.
- Feature-residual checks (cf. Latent Guardian).
- Simple evidential combination.
- A small learned combiner.

See [07](07_literature_questions_and_candidate_methods.md) for the inputs, assumptions and rejection criteria of each.

## Prerequisites still open

Reliability unit and target; runtime inputs and who controls them; a compatible model and checkpoint with placeholder-aware preprocessing; label mapping; session-grouped splits; realistic threat locations; honest-unique-view evaluation; calibration under shift; resource budget.

## What is in this package and what stays behind

**Included here:**
- ten narrative files;
- [evidence_ledger.csv](evidence_ledger.csv), [asset_inventory.csv](asset_inventory.csv), [results_summary.csv](results_summary.csv), [audit_scope.json](audit_scope.json), [evidence_manifest.json](evidence_manifest.json);
- audit scripts and outputs in [evidence/r2/](evidence/r2/);
- small source copies in [evidence/source/](evidence/source/);
- revision-1 files in [revisions/r1_2026-10-22/](revisions/r1_2026-10-22/).

**Stays in the old repo:** raw TARs and extracts (~71 GB), R05 run (2.5 GB), all source code, notebooks and logs. Paths are given relative to the old repo root.

## Next planning actions

1. Primary-literature review with full reads.
2. Pick candidate models and verify that their checkpoints load.
3. Verify labels and placeholder semantics on a few exposed frames.
4. Write the unit, target, inference and threat contracts.
5. Define session-grouped splits using unexposed train segments.
6. Preregister a small falsifiable comparison against a no-filter baseline.
