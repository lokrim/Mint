# R05 completion review — 2026-10-18 (Asia/Kolkata)

The computational replay is complete. R05 reporting and GR5 finalization remain pending. No point-cloud replay, acquisition, extraction, archive rehash or notebook execution was started in this review.

Verified 55 frozen source/config hashes and 23 GR4 output hashes; all 748 scientific prediction files match the unchanged prediction seal. Only two Finder `.DS_Store` hashes differ. All four folds have exactly 62 episodes: 30 attacks, five identity controls, one clean replay and 26 benign stresses. All raw/score/state triplets and 244 non-clean evaluator ledger sets exist.

The raw-record audit checked 309,752 records, complete sensor populations in every episode, exact honest-companion/pre-onset raw equality, attempt-flow reconciliation and zero future original pose timestamps. References, separate calibration scores/state, thresholds and lineage were recomputed from existing saved raw measurements and matched exactly in all four folds. No raw cloud bodies were reread for that scalar recheck. See `audit.json` and `fit_calibration_checks.json`.

Two reporting repairs were necessary: ignore only Finder metadata in prediction validation while retaining the original seal, and reconstruct original episode IDs from the pinned config's original mapping order after verifying canonical equality with the sorted protocol copy. Final manifests now omit Finder metadata too. The 18 focused evaluation tests passed in 0.48 seconds; the full final suite and executed notebooks remain pending.

There are 240 calibration cells: 156 insufficient-support, 31 tagged NO_POWER (21 at threshold 1, ten with constant-zero calibration), and 53 AVAILABLE. Constant-zero calibration does not mean future alarms are impossible. These are support findings, not held-out recall/FPR results.

The run contains preserved resource-limit/FileExistsError interruptions and multiple implementation snapshots. The initial clock-availability correction note alone does not establish that every episode used the corrected helper; the complete raw-record check found zero selected poses originating after their event deadline. The final report must retain these implementation/resource qualifications. Compact run size at review is approximately 2.42 GB; historical peak scratch/RSS has not been certified by this audit.

The report command generates CSV/Markdown tables and PDF/SVG/PNG figures from saved predictions. Finalize rechecks input hashes, runs tests, executes four segment notebooks plus the grouped notebook in fresh kernels, and writes the final manifest and GR5 gate. It rereads source data for hashing but does not regenerate replay episodes.

```sh
cd /Users/lokrim/Code/valid-point
.venv/bin/python scripts/evaluate_replay.py --run artifacts/20261012T134149Z-R05 --phase report
.venv/bin/python scripts/evaluate_replay.py --run artifacts/20261012T134149Z-R05 --phase finalize
```

Run the second command after the first succeeds. Inspect figures/notebooks and the resulting technical gate before accepting R05 completion. H/mini_14 remains outside this review; no subsequent R stage was invoked.
