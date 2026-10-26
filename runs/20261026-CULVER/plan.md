# CULVER: unseen-town (Culver City) evaluation plan

**Label: unseen town, simulated sensor.** OPV2V Culver City is CARLA-simulated with the same 64-beam LiDAR model as the OPV2V test. The town is a digital model of the real city of Culver City's layout. It was unseen during detector training and during all MINT development. **It is not real-sensor data.**

Written 2026-10-26, before any Culver City data byte was downloaded; only the archive's central directory (member names and sizes) was read. Machine-readable plan: [`plan.json`](plan.json). Decision: D-72 (proposed, `planning/decision_log_proposed_appendix.md`).

## Role

A **secondary, held-out domain-shift evaluation** of the frozen v3.2 comparison set. The OPV2V test (`runs/20261024-E5v3`) remains the primary, one-time final test. Culver City numbers are reported separately and never pooled with it. The v3.2 success rule is reported **descriptively** with the Holm results, and it does not re-open the test verdict.

## Data

The archive is `test_culver_city-011.zip` (4,909,598,200 bytes; file_id `f_1621693876387`). It sits on the same public UCLA Box share as the test archive, with no registration. Byte budget is 7e9; planned download is 4.91e9.

| Scenario | CAVs | Frames | Bytes (members) |
|---|---|---|---|
| 2021_09_03_09_32_17 | 2 | 90 | 0.608e9 |
| 2021_09_03_10_53_32 | 2 | 118 | 0.805e9 |
| 2021_09_03_20_08_37 | 3 | 135 | 1.411e9 |
| 2021_09_03_22_43_57 | 3 | 207 | 2.083e9 |
| **Total** | | **550** | **4.907e9** |

## Frozen pieces (unchanged)

- **Code:** frozen commit `c883753`, with the full `frozen_sha256` list of `preregistration_v3_2.json` and OpenCOOD `31ba160`. Both are verified before network access and after the run.
- **Checkpoint:** the released `pointpillar_attentive_fusion` (sha `f6df2f54…`), trained on OPV2V train. Its README reports Culver City AP@0.7 of 0.735 (frame-order AP).
- **Methods:** no defense, ego-only, B-NORM, B-RAY, R1, R1-noREMOVE (oracle bounds as in v2).
- **Conditions:** clean, the 4 original families, spoof_blind, plain PGD (r = 0.25), stealth PGD at the selected levels (0.5 / 0.25), and the D-70 r = 1.0 levels (labelled post hoc).
- **Parameters:** σ_k and τ_k are reused unchanged (same checkpoint and sensor). Nothing is fitted on Culver City.
- **Metrics:** both D-64 AP definitions (global ranking is the headline), scenario and 10-frame bootstrap (2000 draws, seed 0), Holm co-test.
- **New code:** new files only (`runners/culver_*.py` and a report template). Their sha256 values go in `code_freeze.json`, which is committed before the first download.

**Coarse CIs.** With 4 scenarios, the scenario bootstrap has at most 35 distinct resamples. Agent-count strata have only 2 scenarios each, so they get 10-frame CIs only.

## Sanity check

Right after the first scenario (`2021_09_03_09_32_17`) downloads, run clean OpenCOOD inference and compute AP@0.7 (frame order). The value should be near 0.735. A single scenario can vary: on the OPV2V test, per-scenario values ranged 0.72–0.97. **Below 0.6, stop and investigate.** This is detector-level exposure only.

## Expected outcomes (stated from the OPV2V test only, before any Culver number)

- **Clean detector:** frame-order AP@0.7 within about ±0.05 of 0.735; global-ranking AP higher.
- **Headline (mean of 4):** same signs as the test.
  - Global AP: R1 > B-RAY ≥ 0, both below 1 AP point.
  - Frame-order AP: B-RAY > R1.
  - R1 − B-RAY is again AP-definition-dependent. The v2 rule may fail for lack of power.
- **Clean cost:**
  - B-RAY below 1% (point).
  - R1 positive under frame-order AP, and about 0 or negative under global AP.
- **B-NORM:** about 100% catch on plain PGD and ≤ 5% on stealth PGD. The clean false-flag rate and cost are at least as large as on the test.
- **PGD:**
  - B-RAY recovers about 0.
  - R1 recovers about 0.5 on `pgd_remove_stealth@r1.0`, and more than 0 on the r = 0.25 remove families (global AP).
- **spoof_blind:** not recovered by any method.

## Run

```bash
nohup caffeinate -ims .venv/bin/python runners/culver_stream.py --run_dir runs/20261026-CULVER --user_approved > runs/20261026-CULVER/run.log 2>&1 &
```

Estimate: about 8 h (6–11 h). To resume, re-run the same command; finished scenarios are skipped. Then run `runners/culver_analyze.py` once over all scenarios, followed by `runners/culver_report.py`.
