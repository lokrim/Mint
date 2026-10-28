# MINT unseen-town evaluation (OPV2V Culver City): results report

> **Status: DEVELOPMENT / DRY RUN - not results**
> Source: DRY RUN of the CULVER analysis (development dev slice; not results)
>
> These numbers come from development data. They show what the report will look like; they are **not** Culver City results and must not be quoted as such.
>
> **Unseen town, simulated sensor.** OPV2V Culver City: simulated (CARLA) 64-beam LiDAR, the same sensor model as the OPV2V test; a digital town modelled on the layout of the real city of Culver City; unseen during detector training and during all MINT development. NOT real-sensor data.
>
> **Role.** SECONDARY held-out domain-shift evaluation. The OPV2V test (runs/20261024-E5v3, preregistration_v3_2.json) stays the primary, one-time final test. Culver City results are reported separately and never pooled with the test. The primary result is the OPV2V final test (`runs/20261024-E5v3/report/report.md`).

Generated 2026-10-26T20:40:38+05:30 by `runners/culver_report.py` (the `src/mint/report` pipeline, unchanged). Every number in this report is copied from the analysis outputs listed below; nothing is recomputed. Sections marked **AUTHOR** are left for the authors to write after reading the results.

**Few scenarios.** 4 scenarios only: the scenario bootstrap has at most 35 distinct resamples (multisets of 4 from 4), so scenario CIs and p-values are coarse; 10-frame CIs are reported next to them but are not the pre-registered primary CI. frames have n <= 3; per-agent-count strata have 2 scenarios each, so only 10-frame CIs exist there (frozen MIN_SCEN_FOR_SCEN_BOOT = 5).

| Provenance | |
|---|---|
| `e5_v3.json` | `runs/20261026-CULVER/dryrun/e5_v3.json` · sha256 `e4f0cca87536120e…` |
| `e5_test.json` | `runs/20261026-CULVER/dryrun/e5_test.json` · sha256 `6df93cdee3b2a420…` |
| `preregistration` | `runs/20261024-E5/preregistration_v3_2.json` · sha256 `8756868def368e85…` |
| Repository HEAD | `d48fde8ca69a57db11add9ad6d15e8eab50a7788` |
| Frozen code commit (preregistration) | `c883753f91c75e707d5df5fce8757851fad494de` |
| Preregistration version | v3.2 (supersedes v3.1 runs/20261024-E5/preregistration_v3_1.json only by D-71; v1, v2, v3 and v3.1 kept unchanged) |
| Scenarios / frames | 1 / 12 (agents per frame: {'2': 12}) |

## 1. What was tested

**Defenses compared** (pre-registered comparison set): no defense; ego-only; B-NORM (D-66, new); B-RAY (primary); R1 (key secondary); R1-noREMOVE (ablation); oracle bounds as v2 (frozen e5_analyze).

**Conditions** (12): clean (no attack); spoof - feature; remove - feature; shift - feature; spoof - points; spoof in receiver-blind area; PGD untargeted r=0.25; PGD remove r=0.25; PGD untargeted stealth r=0.5; PGD remove stealth r=0.25; PGD untargeted stealth r=1.0 †; PGD remove stealth r=1.0 †.

† pgd_remove_stealth@r1.0, pgd_untargeted_stealth@r1.0: strong-attack level, added after seeing block-H development results (D-70, secondary; never used for a criterion).

**Metrics.** ΔAP@0.7 = AP of a defense minus AP with no defense on the same frames, in AP points (×100). Recovery = ΔAP / attack loss. Clean cost = relative AP@0.7 loss on unattacked frames. Every statistic is computed under two AP definitions: global-ranking AP (headline) and frame-order AP (OPV2V-comparable).

**Pre-registered rule (D-64).** every primary and key-secondary statistic is computed under both definitions with the same bootstrap (seed 0, 2000 resamples, scenario and 10-frame). The v2 success rule (B-RAY Holm-rejected in the co-test with R1 vs no defense on the scenario bootstrap, and B-RAY clean relative loss scenario-CI high <= 1%) is evaluated separately per AP definition, Holm within each definition. A success/robustness claim requires a pass under BOTH. Headline numbers are quoted with global-ranking AP; frame-order AP is reported for comparability with OPV2V papers. If the two disagree the report states 'AP-definition-dependent'. R1 - B-RAY (statement by scenario CI, v2 wording) is reported under both, side by side.

**Outcome wording.** Success: only if the v2 rule passes under both AP definitions (D-64); headline in global-ranking AP. Disagreement: report 'AP-definition-dependent'. Failure: report as the result; no rescue analysis presented as confirmatory.

**Parameters.** σ_k, B-NORM τ_k, attack levels, seeds and every method are those of `preregistration_v3_2.json`, reused unchanged (same checkpoint and sensor); nothing was fitted or tuned on Culver City.

## 2. Procedural checks

| Check | Detail | Passed |
|---|---|---|
| Completeness (scenarios, frames) | 1/4 scenarios, 12/550 frames | no |
| Frame-order v3 = frozen v2 analysis | 4 statistics, point and scenario CI | yes |
| NumPy AP vs OpenCOOD AP | max abs. difference 2.6e-15 | yes |
| Compose checks identical (all scenarios) | 1 scenarios | yes |

## 3. Pre-registered rule, reported descriptively (secondary evaluation)

The v3.2 success rule is applied unchanged and reported **descriptively**; it does not re-open the OPV2V test verdict.

**Success under both AP definitions.** v2 rule under global-ranking AP: passes; under frame-order AP: passes.

| AP definition | B-RAY ΔAP | B-RAY p (1-sided) | B-RAY Holm reject | R1 ΔAP | R1 p | R1 Holm reject | B-RAY clean loss CI (%) | clean CI high ≤ 1% | v2 rule passes |
|---|---|---|---|---|---|---|---|---|---|
| global-ranking AP (headline) | +0.44 | 0.0050 | yes | +0.44 | 0.0050 | yes | [+0.00, +0.00] | yes | yes |
| frame-order AP (OPV2V-comparable) | +1.27 | 0.0050 | yes | +1.07 | 0.0050 | yes | [+0.00, +0.00] | yes | yes |

**Key secondary (R1 − B-RAY), statements emitted by the frozen analysis:**

| AP definition | R1 − B-RAY (pts) | 95% CI scen. | 95% CI 10-frame | Pre-registered statement |
|---|---|---|---|---|
| global-ranking AP (headline) | +0.00 | [+0.00, +0.00] | [+0.00, +0.00] | “the counterfactual's benefit over a box-level filter is not established” |
| frame-order AP (OPV2V-comparable) | -0.19 | [-0.19, -0.19] | [-0.24, +0.00] | “the counterfactual performs worse than the box-level filter” |

The key secondary is **AP-definition-dependent** (the two definitions give different statements).

## 4. Headline: mean ΔAP@0.7 over the 4 original attacks

![Headline: mean ΔAP@0.7 over the 4 original attacks](figures/01_headline.png)

*Figure 1. Each defense's mean change in AP@0.7 against no defense, over spoof/remove/shift (feature) and spoof (points). Dot = point estimate; thick line = 95% CI from the scenario bootstrap (the pre-registered primary CI); thin line = 10-frame-block bootstrap. Ego-only is far off-scale and is listed in the table only.* Data: [`tables/01_headline.csv`](tables/01_headline.csv) · dark version: [`figures/01_headline_dark.png`](figures/01_headline_dark.png)

| Method | ΔAP@0.7 global | 95% CI scen. global | 95% CI 10-frame global | ΔAP@0.7 frame | 95% CI scen. frame | 95% CI 10-frame frame |
|---|---|---|---|---|---|---|
| B-RAY (primary) | +0.44 | [+0.44, +0.44] | [+0.39, +0.52] | +1.27 | [+1.27, +1.27] | [+0.93, +1.44] |
| R1 (key secondary) | +0.44 | [+0.44, +0.44] | [+0.40, +0.52] | +1.07 | [+1.07, +1.07] | [+0.93, +1.19] |
| R1-noREMOVE (ablation) | +0.44 | [+0.44, +0.44] | [+0.40, +0.52] | +1.07 | [+1.07, +1.07] | [+0.93, +1.19] |
| B-NORM (baseline) | +0.00 | [+0.00, +0.00] | [+0.00, +0.00] | +0.00 | [+0.00, +0.00] | [+0.00, +0.00] |
| Ego-only | -14.24 | [-14.23, -14.23] | [-14.32, -14.23] | -14.88 | [-14.88, -14.88] | [-22.30, -14.12] |

## 5. Every attack condition

![ΔAP@0.7 per condition: clean and original attacks](figures/02_per_family.png)

*Figure 2a. Every non-PGD condition × defense, both AP definitions, 95% CI from the scenario bootstrap. Ego-only in the table only.* Data: [`tables/02_per_family.csv`](tables/02_per_family.csv) · dark version: [`figures/02_per_family_dark.png`](figures/02_per_family_dark.png)

![ΔAP@0.7 per condition: optimized (PGD) attacks](figures/02b_per_family_pgd.png)

*Figure 2b. As 2a for the PGD conditions, on its own scale (PGD effects are much larger than the original attacks').* Data: [`tables/02b_per_family_pgd.csv`](tables/02b_per_family_pgd.csv) · dark version: [`figures/02b_per_family_pgd_dark.png`](figures/02b_per_family_pgd_dark.png)

**global-ranking AP (headline)** (ΔAP@0.7 in AP points, 95% CI scenario bootstrap)

| Condition | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|
| clean (no attack) | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -15.41 [-15.41, -15.41] |
| spoof - feature | +1.11 [+1.11, +1.11] | +1.11 [+1.11, +1.11] | +1.11 [+1.11, +1.11] | +0.00 [+0.00, +0.00] | -14.30 [-14.30, -14.30] |
| remove - feature | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -13.47 [-13.47, -13.47] |
| shift - feature | +0.63 [+0.63, +0.63] | +0.64 [+0.64, +0.64] | +0.64 [+0.64, +0.64] | +0.00 [+0.00, +0.00] | -14.14 [-14.14, -14.14] |
| spoof - points | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -15.03 [-15.03, -15.03] |
| spoof in receiver-blind area | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -14.12 [-14.12, -14.12] |
| PGD untargeted r=0.25 | +0.01 [+0.01, +0.01] | +0.01 [+0.01, +0.01] | +0.01 [+0.01, +0.01] | -16.71 [-16.71, -16.71] | -16.71 [-16.71, -16.71] |
| PGD remove r=0.25 | +0.00 [+0.00, +0.00] | +0.68 [+0.68, +0.68] | +0.00 [+0.00, +0.00] | -13.86 [-13.86, -13.86] | -13.86 [-13.86, -13.86] |
| PGD untargeted stealth r=0.5 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -15.51 [-15.51, -15.51] |
| PGD remove stealth r=0.25 | +0.00 [+0.00, +0.00] | +0.65 [+0.65, +0.65] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -13.14 [-13.14, -13.14] |
| PGD untargeted stealth r=1.0 † | +0.03 [+0.03, +0.03] | +0.03 [+0.04, +0.04] | +0.03 [+0.04, +0.04] | +0.00 [+0.00, +0.00] | -12.17 [-12.17, -12.17] |
| PGD remove stealth r=1.0 † | +0.00 [+0.00, +0.00] | +28.00 [+28.00, +28.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +31.32 [+31.32, +31.32] |

**frame-order AP (OPV2V-comparable)** (ΔAP@0.7 in AP points, 95% CI scenario bootstrap)

| Condition | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|
| clean (no attack) | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -17.15 [-17.15, -17.15] |
| spoof - feature | +2.04 [+2.04, +2.04] | +1.27 [+1.28, +1.28] | +1.27 [+1.28, +1.28] | +0.00 [+0.00, +0.00] | -15.10 [-15.10, -15.10] |
| remove - feature | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -14.29 [-14.29, -14.29] |
| shift - feature | +3.02 [+3.02, +3.02] | +3.02 [+3.02, +3.02] | +3.02 [+3.02, +3.02] | +0.00 [+0.00, +0.00] | -13.79 [-13.79, -13.79] |
| spoof - points | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -16.32 [-16.32, -16.32] |
| spoof in receiver-blind area | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -14.35 [-14.35, -14.35] |
| PGD untargeted r=0.25 | +0.79 [+0.79, +0.79] | +0.79 [+0.79, +0.79] | +0.79 [+0.79, +0.79] | -15.87 [-15.87, -15.87] | -15.87 [-15.87, -15.87] |
| PGD remove r=0.25 | +0.00 [+0.00, +0.00] | -0.21 [-0.21, -0.21] | +0.00 [+0.00, +0.00] | -16.97 [-16.97, -16.97] | -16.97 [-16.97, -16.97] |
| PGD untargeted stealth r=0.5 | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -15.65 [-15.65, -15.65] |
| PGD remove stealth r=0.25 | +0.00 [+0.00, +0.00] | -0.93 [-0.93, -0.93] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | -16.81 [-16.81, -16.81] |
| PGD untargeted stealth r=1.0 † | +4.20 [+4.20, +4.20] | +4.20 [+4.20, +4.20] | +4.20 [+4.20, +4.20] | +0.00 [+0.00, +0.00] | -1.16 [-1.16, -1.16] |
| PGD remove stealth r=1.0 † | +0.00 [+0.00, +0.00] | +26.75 [+26.75, +26.75] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +25.46 [+25.46, +25.46] |

## 6. Cost on clean frames

![Clean cost (relative AP@0.7 loss)](figures/03_clean_cost.png)

*Figure 3. Relative AP@0.7 loss on clean frames. The pre-registered success rule requires B-RAY's scenario-CI high ≤ 1% under both AP definitions.* Data: [`tables/03_clean_cost.csv`](tables/03_clean_cost.csv) · dark version: [`figures/03_clean_cost_dark.png`](figures/03_clean_cost_dark.png)

| Method | rel. loss global | 95% CI scen. (%) global | rel. loss frame | 95% CI scen. (%) frame |
|---|---|---|---|---|
| B-RAY (primary) | 0.00% | [+0.00, +0.00] | 0.00% | [+0.00, +0.00] |
| R1 (key secondary) | 0.00% | [+0.00, +0.00] | 0.00% | [+0.00, +0.00] |
| R1-noREMOVE (ablation) | 0.00% | [+0.00, +0.00] | 0.00% | [+0.00, +0.00] |
| B-NORM (baseline) | 0.00% | [+0.00, +0.00] | 0.00% | [+0.00, +0.00] |
| Ego-only | 17.01% | [+17.01, +17.01] | 19.86% | [+19.86, +19.86] |

## 7. Key secondary: R1 versus B-RAY

![Key secondary: R1 − B-RAY](figures/04_r1_minus_bray.png)

*Figure 4a. Paired difference R1 − B-RAY in ΔAP@0.7, the pre-registered means and each non-PGD condition. Each panel quotes the statement the frozen analysis emitted.* Data: [`tables/04_r1_minus_bray.csv`](tables/04_r1_minus_bray.csv) · dark version: [`figures/04_r1_minus_bray_dark.png`](figures/04_r1_minus_bray_dark.png)

![R1 − B-RAY under PGD attacks](figures/04b_r1_minus_bray_pgd.png)

*Figure 4b. Paired difference per PGD condition (descriptive; not part of the key secondary).* Data: [`tables/04b_r1_minus_bray_pgd.csv`](tables/04b_r1_minus_bray_pgd.csv) · dark version: [`figures/04b_r1_minus_bray_pgd_dark.png`](figures/04b_r1_minus_bray_pgd_dark.png)

## 8. Optimized (PGD) feature attacks and B-NORM

![PGD attacks: recovery](figures/05_pgd_recovery.png)

*Figure 5. Recovery = ΔAP@0.7 / attack loss per optimized-attack condition. n/a when the attack loss is < 0.005.* Data: [`tables/05_pgd_recovery.csv`](tables/05_pgd_recovery.csv) · dark version: [`figures/05_pgd_recovery_dark.png`](figures/05_pgd_recovery_dark.png)

![B-NORM catch rate](figures/06_bnorm_catch.png)

*Figure 6. Share of frames with a sender in which B-NORM flags the attacker; on 'clean' this is the false-flag rate.* Data: [`tables/06_bnorm_catch.csv`](tables/06_bnorm_catch.csv) · dark version: [`figures/06_bnorm_catch_dark.png`](figures/06_bnorm_catch_dark.png)

| Condition | attack loss global | attack loss frame | recovery B-RAY (primary) (global / frame) | recovery R1 (key secondary) (global / frame) | recovery R1-noREMOVE (ablation) (global / frame) | recovery B-NORM (baseline) (global / frame) | recovery Ego-only (global / frame) | B-NORM catch | stealth-infeasible / frames with sender | realized / applied |
|---|---|---|---|---|---|---|---|---|---|---|
| PGD untargeted r=0.25 | -1.29 | +1.27 | n/a / 0.62 | n/a / 0.62 | n/a / 0.62 | n/a / -12.45 | n/a / -12.45 | 100% | 0/12 | 9/12 |
| PGD remove r=0.25 | +1.55 | +0.17 | 0.00 / n/a | 0.44 / n/a | 0.00 / n/a | -8.92 / n/a | -8.92 / n/a | 100% | 0/12 | 5/12 |
| PGD untargeted stealth r=0.5 | -0.10 | +1.50 | n/a / 0.00 | n/a / 0.00 | n/a / 0.00 | n/a / 0.00 | n/a / -10.45 | 0% | 0/12 | 6/12 |
| PGD remove stealth r=0.25 | +2.27 | +0.33 | 0.00 / n/a | 0.28 / n/a | 0.00 / n/a | 0.00 / n/a | -5.78 / n/a | 0% | 0/12 | 7/12 |
| PGD untargeted stealth r=1.0 † | +3.24 | +15.99 | 0.01 / 0.26 | 0.01 / 0.26 | 0.01 / 0.26 | 0.00 / 0.00 | -3.76 / -0.07 | 0% | 0/12 | 11/12 |
| PGD remove stealth r=1.0 † | +46.74 | +42.60 | 0.00 / 0.00 | 0.60 / 0.63 | 0.00 / 0.00 | 0.00 / 0.00 | 0.67 / 0.60 | 0% | 0/12 | 12/12 |

**Expected outcomes, checked descriptively** (rules stated in the preregistration before any PGD run; not criteria):

| Condition | B-RAY ≈ 0 (point recovery < 0.10 under both AP definitions) | R1 > 0 (R1 dAP@0.7 scenario-CI low > 0 under both AP definitions) | B-NORM ≤ 5% (sender-1 flag rate over attacked frames <= 0.05) |
|---|---|---|---|
| PGD untargeted r=0.25 | n/a | not applicable | not applicable |
| PGD remove r=0.25 | n/a | no | not applicable |
| PGD untargeted stealth r=0.5 | n/a | not applicable | yes |
| PGD remove stealth r=0.25 | n/a | no | yes |
| PGD untargeted stealth r=1.0 † | no | not applicable | yes |
| PGD remove stealth r=1.0 † | yes | yes | yes |

## 9. Attack strength and realized-only effects

![Attack strength](figures/07_attack_strength.png)

*Figure 7. Attack loss per condition over all frames (with CI) and over the frames where the attack was realized.* Data: [`tables/07_attack_strength.csv`](tables/07_attack_strength.csv) · dark version: [`figures/07_attack_strength_dark.png`](figures/07_attack_strength_dark.png)

**Realized frames only, global-ranking AP (headline)** (ΔAP@0.7 in AP points, recovery in brackets)

| Condition | realized frames | attack loss | B-RAY (primary) ΔAP (recovery) | R1 (key secondary) ΔAP (recovery) | R1-noREMOVE (ablation) ΔAP (recovery) | B-NORM (baseline) ΔAP (recovery) | Ego-only ΔAP (recovery) |
|---|---|---|---|---|---|---|---|
| spoof - feature | 4 | +2.89 | +2.89 (1.00) | +2.89 (1.00) | +2.89 (1.00) | +0.00 (0.00) | -19.05 (-6.60) |
| remove - feature | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| shift - feature | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| spoof - points | 1 | +2.56 | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | -20.98 (-8.18) |
| spoof in receiver-blind area | 6 | +2.09 | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | -13.21 (-6.31) |
| PGD untargeted r=0.25 | 9 | -1.67 | +0.01 (n/a) | +0.01 (n/a) | +0.01 (n/a) | -15.70 (n/a) | -15.70 (n/a) |
| PGD remove r=0.25 | 5 | +3.53 | +0.00 (0.00) | +1.68 (0.47) | +0.00 (0.00) | -7.85 (-2.22) | -7.85 (-2.22) |
| PGD untargeted stealth r=0.5 | 6 | +0.64 | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | -12.77 (-20.05) |
| PGD remove stealth r=0.25 | 7 | +2.42 | +0.00 (0.00) | +1.14 (0.47) | +0.00 (0.00) | +0.00 (0.00) | -12.95 (-5.36) |
| PGD untargeted stealth r=1.0 † | 11 | +3.36 | +0.03 (0.01) | +0.04 (0.01) | +0.04 (0.01) | +0.00 (0.00) | -12.56 (-3.74) |
| PGD remove stealth r=1.0 † | 12 | +46.74 | +0.00 (0.00) | +28.00 (0.60) | +0.00 (0.00) | +0.00 (0.00) | +31.32 (0.67) |

**Realized frames only, frame-order AP (OPV2V-comparable)** (ΔAP@0.7 in AP points, recovery in brackets)

| Condition | realized frames | attack loss | B-RAY (primary) ΔAP (recovery) | R1 (key secondary) ΔAP (recovery) | R1-noREMOVE (ablation) ΔAP (recovery) | B-NORM (baseline) ΔAP (recovery) | Ego-only ΔAP (recovery) |
|---|---|---|---|---|---|---|---|
| spoof - feature | 4 | +5.20 | +5.20 (1.00) | +3.71 (0.71) | +3.71 (0.71) | +0.00 (0.00) | -18.57 (-3.57) |
| remove - feature | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| shift - feature | 0 | n/a | n/a | n/a | n/a | n/a | n/a |
| spoof - points | 1 | +2.56 | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | -20.98 (-8.18) |
| spoof in receiver-blind area | 6 | +5.35 | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | -10.51 (-1.96) |
| PGD untargeted r=0.25 | 9 | +3.03 | +1.52 (0.50) | +1.52 (0.50) | +1.52 (0.50) | -13.08 (-4.32) | -13.08 (-4.32) |
| PGD remove r=0.25 | 5 | +2.49 | +0.00 (0.00) | +1.45 (0.58) | +0.00 (0.00) | -11.75 (-4.71) | -11.75 (-4.71) |
| PGD untargeted stealth r=0.5 | 6 | +4.78 | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | +0.00 (0.00) | -13.45 (-2.81) |
| PGD remove stealth r=0.25 | 7 | +0.46 | +0.00 (n/a) | -0.19 (n/a) | +0.00 (n/a) | +0.00 (n/a) | -16.73 (n/a) |
| PGD untargeted stealth r=1.0 † | 11 | +17.23 | +4.32 (0.25) | +4.32 (0.25) | +4.32 (0.25) | +0.00 (0.00) | -0.64 (-0.04) |
| PGD remove stealth r=1.0 † | 12 | +42.60 | +0.00 (0.00) | +26.75 (0.63) | +0.00 (0.00) | +0.00 (0.00) | +25.46 (0.60) |

## 10. How the defenses act

![B-RAY removals](figures/08_bray_boxes.png)

*Figure 8. Boxes B-RAY removed, split by whether they matched a real car.* Data: [`tables/08_bray_boxes.csv`](tables/08_bray_boxes.csv) · dark version: [`figures/08_bray_boxes_dark.png`](figures/08_bray_boxes_dark.png)

![R1 gating against ground truth](figures/09_r1_units.png)

*Figure 9. Contributions (sender × 6.4 m tile) R1 switched off, by their ground-truth label.* Data: [`tables/09_r1_units.csv`](tables/09_r1_units.csv) · dark version: [`figures/09_r1_units_dark.png`](figures/09_r1_units_dark.png)

## 11. By number of cars

![Effect by number of cars](figures/10_by_agents.png)

*Figure 10. Mean ΔAP@0.7 over the 4 original attacks per agent count (frozen v2 analysis, frame-order AP).* Data: [`tables/10_by_agents.csv`](tables/10_by_agents.csv) · dark version: [`figures/10_by_agents_dark.png`](figures/10_by_agents_dark.png)

**Runtime by number of cars** (frozen D-42 timing pass; overhead = extra time / receiver baseline, same machine; Culver City frames have at most 3 cars)

| Data | cars | frames | mode | overhead p50 | overhead p95 | extra s p50 | baseline s p50 |
|---|---|---|---|---|---|---|---|
| OPV2V test | 1 | 119 | B-RAY | 8.4% | 14.3% | 0.029 | 0.395 |
| OPV2V test | 2 | 866 | dense | 20.2% | 46.0% | 0.075 | 0.391 |
| OPV2V test | 2 | 866 | trigger_0.05 | 9.6% | 34.3% | 0.035 | 0.391 |
| OPV2V test | 2 | 866 | B-RAY | 3.5% | 11.3% | 0.013 | 0.391 |
| OPV2V test | 3 | 869 | dense | 52.9% | 102.2% | 0.218 | 0.422 |
| OPV2V test | 3 | 869 | trigger_0.05 | 39.9% | 92.7% | 0.149 | 0.422 |
| OPV2V test | 3 | 869 | B-RAY | 9.2% | 20.3% | 0.034 | 0.422 |
| OPV2V test | 4+ | 212 | dense | 122.7% | 169.7% | 0.649 | 0.517 |
| OPV2V test | 4+ | 212 | trigger_0.05 | 77.0% | 128.2% | 0.372 | 0.517 |
| OPV2V test | 4+ | 212 | B-RAY | 11.1% | 16.4% | 0.051 | 0.517 |
| Culver City | 2 | 12 | dense | 36.8% | 63.3% | 0.083 | 0.223 |
| Culver City | 2 | 12 | trigger_0.05 | 18.8% | 23.4% | 0.043 | 0.223 |
| Culver City | 2 | 12 | B-RAY | 12.0% | 13.8% | 0.025 | 0.223 |

## 12. OPV2V test vs Culver City (headline numbers, kept separate)

Two separate evaluations of the same frozen code, never pooled. Left: the OPV2V final test (FINAL TEST (one-time), primary). Right: Culver City (this report, secondary, 4 scenarios: coarse scenario CIs). ΔAP in AP points. Data: [`tables/11_test_vs_culver.csv`](tables/11_test_vs_culver.csv)

| Statistic | AP definition | OPV2V test (primary, 15 scen.) | Culver City (secondary, 4 scen.) |
|---|---|---|---|
| Scenarios / frames | - | 15 / 2066 | 1 / 12 |
| Agents per frame | - | {'1': 119, '2': 866, '3': 869, '4': 111, '5': 101} | {'2': 12} |
| No-defense clean AP@0.7 (absolute) | global-ranking AP (headline) | 0.8864 | 0.9062 |
| No-defense clean AP@0.7 (absolute) | frame-order AP (OPV2V-comparable) | 0.8217 | 0.8635 |
| B-RAY (primary): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | global-ranking AP (headline) | +0.15 [-0.01, +0.30] | +0.44 [+0.44, +0.44] |
| B-RAY (primary): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | frame-order AP (OPV2V-comparable) | +0.76 [+0.49, +1.27] | +1.27 [+1.27, +1.27] |
| R1 (key secondary): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | global-ranking AP (headline) | +0.45 [+0.29, +0.70] | +0.44 [+0.44, +0.44] |
| R1 (key secondary): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | frame-order AP (OPV2V-comparable) | +0.19 [-0.45, +0.52] | +1.07 [+1.07, +1.07] |
| R1-noREMOVE (ablation): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | global-ranking AP (headline) | +0.26 [+0.18, +0.36] | +0.44 [+0.44, +0.44] |
| R1-noREMOVE (ablation): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | frame-order AP (OPV2V-comparable) | +0.66 [+0.48, +1.03] | +1.07 [+1.07, +1.07] |
| B-NORM (baseline): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | global-ranking AP (headline) | -5.85 [-9.65, -2.30] | +0.00 [+0.00, +0.00] |
| B-NORM (baseline): mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | frame-order AP (OPV2V-comparable) | -7.13 [-11.82, -2.73] | +0.00 [+0.00, +0.00] |
| Ego-only: mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | global-ranking AP (headline) | -20.02 [-23.10, -16.04] | -14.24 [-14.23, -14.23] |
| Ego-only: mean ΔAP@0.7, 4 original attacks (pts, scen. CI) | frame-order AP (OPV2V-comparable) | -24.20 [-29.44, -18.65] | -14.88 [-14.88, -14.88] |
| B-RAY (primary): clean relative AP@0.7 loss (scen. CI) | global-ranking AP (headline) | 0.13% [+0.01, +0.30] | 0.00% [+0.00, +0.00] |
| B-RAY (primary): clean relative AP@0.7 loss (scen. CI) | frame-order AP (OPV2V-comparable) | -0.05% [-0.30, +0.18] | 0.00% [+0.00, +0.00] |
| R1 (key secondary): clean relative AP@0.7 loss (scen. CI) | global-ranking AP (headline) | -0.16% [-0.35, -0.01] | 0.00% [+0.00, +0.00] |
| R1 (key secondary): clean relative AP@0.7 loss (scen. CI) | frame-order AP (OPV2V-comparable) | 0.62% [+0.18, +1.75] | 0.00% [+0.00, +0.00] |
| Holm co-test vs no defense (1-sided, scenario bootstrap) | global-ranking AP (headline) | B-RAY p=0.0335 reject; R1 p=0.0005 reject | B-RAY p=0.0050 reject; R1 p=0.0050 reject |
| Holm co-test vs no defense (1-sided, scenario bootstrap) | frame-order AP (OPV2V-comparable) | B-RAY p=0.0005 reject; R1 p=0.2259 no reject | B-RAY p=0.0050 reject; R1 p=0.0050 reject |
| v2 success rule (B-RAY Holm reject and clean CI high <= 1%) | global-ranking AP (headline) | passes | passes |
| v2 success rule (B-RAY Holm reject and clean CI high <= 1%) | frame-order AP (OPV2V-comparable) | passes | passes |
| D-64 verdict | - | success under both AP definitions | success under both AP definitions |
| R1 − B-RAY, mean of 4 (pts, scen. CI) and statement | global-ranking AP (headline) | +0.31 [+0.12, +0.55]: “the counterfactual improves over the box-level filter” | +0.00 [+0.00, +0.00]: “the counterfactual's benefit over a box-level filter is not established” |
| R1 − B-RAY, mean of 4 (pts, scen. CI) and statement | frame-order AP (OPV2V-comparable) | -0.57 [-1.64, -0.11]: “the counterfactual performs worse than the box-level filter” | -0.19 [-0.19, -0.19]: “the counterfactual performs worse than the box-level filter” |
| spoof in receiver-blind area: attack loss, ΔAP (recovery) | global-ranking AP (headline) | loss +2.21; B-RAY -0.01 (rec. -0.00); R1 +0.19 (rec. 0.09) | loss +1.29; B-RAY +0.00 (rec. 0.00); R1 +0.00 (rec. 0.00) |
| spoof in receiver-blind area: attack loss, ΔAP (recovery) | frame-order AP (OPV2V-comparable) | loss +4.39; B-RAY +0.14 (rec. 0.03); R1 -0.34 (rec. -0.08) | loss +2.80; B-RAY +0.00 (rec. 0.00); R1 +0.00 (rec. 0.00) |
| PGD remove stealth r=0.25: attack loss, ΔAP (recovery) | global-ranking AP (headline) | loss +3.06; B-RAY -0.10 (rec. -0.03); R1 +1.13 (rec. 0.37) | loss +2.27; B-RAY +0.00 (rec. 0.00); R1 +0.65 (rec. 0.28) |
| PGD remove stealth r=0.25: attack loss, ΔAP (recovery) | frame-order AP (OPV2V-comparable) | loss +1.14; B-RAY -0.02 (rec. -0.02); R1 -0.14 (rec. -0.13) | loss +0.33; B-RAY +0.00; R1 -0.93 |
| PGD remove stealth r=1.0: attack loss, ΔAP (recovery) | global-ranking AP (headline) | loss +40.41; B-RAY -0.01 (rec. -0.00); R1 +22.50 (rec. 0.56) | loss +46.74; B-RAY +0.00 (rec. 0.00); R1 +28.00 (rec. 0.60) |
| PGD remove stealth r=1.0: attack loss, ΔAP (recovery) | frame-order AP (OPV2V-comparable) | loss +36.51; B-RAY +0.06 (rec. 0.00); R1 +20.94 (rec. 0.57) | loss +42.60; B-RAY +0.00 (rec. 0.00); R1 +26.75 (rec. 0.63) |
| PGD untargeted stealth r=1.0: attack loss, ΔAP (recovery) | global-ranking AP (headline) | loss +8.86; B-RAY +0.12 (rec. 0.01); R1 +0.40 (rec. 0.04) | loss +3.24; B-RAY +0.03 (rec. 0.01); R1 +0.03 (rec. 0.01) |
| PGD untargeted stealth r=1.0: attack loss, ΔAP (recovery) | frame-order AP (OPV2V-comparable) | loss +20.10; B-RAY +2.09 (rec. 0.10); R1 +1.33 (rec. 0.07) | loss +15.99; B-RAY +4.20 (rec. 0.26); R1 +4.20 (rec. 0.26) |
| B-NORM sender-1 flag rate, clean (no attack) | - | 17.4% | 0.0% |
| B-NORM sender-1 flag rate, PGD untargeted r=0.25 | - | 100.0% | 100.0% |
| B-NORM sender-1 flag rate, PGD untargeted stealth r=0.5 | - | 0.0% | 0.0% |

**Expected outcomes stated in the plan before any Culver City number** (from the OPV2V test only; descriptive, not criteria):

- *clean_detector*: no-defense frame-order AP@0.7 over the 4 scenarios within about +-0.05 of 0.735 (lower than the test's 0.822); global-ranking AP higher than frame-order, as on the test (0.886 vs 0.822)
- *headline_mean4*: same signs as the test: global AP R1 > B-RAY >= 0, both below 1 AP point (test +0.45 / +0.15); frame-order AP B-RAY > R1 (test +0.76 / +0.19); R1 - B-RAY AP-definition-dependent as on the test; wider CIs, so the v2 rule may fail under one or both definitions by lack of power
- *clean_cost*: B-RAY relative loss below 1% (point); R1 clean cost under frame-order AP positive (test 0.62%) and near zero or negative under global AP; R1-noREMOVE near 0
- *domain_shift*: more detector false positives in an unseen town may give B-RAY more boxes to remove; whether that helps or hurts clean AP is not predicted
- *B-NORM*: catch ~100% on plain PGD; <= 5% on stealth PGD; clean false-flag rate and AP cost at least as large as on the test (tau_k fitted on default-town block H), so B-NORM clean cost likely several AP points
- *PGD*: B-RAY recovery ~0 on every PGD condition; R1 recovery on pgd_remove_stealth@r1.0 around 0.5 (test 0.56) and > 0 on the r = 0.25 remove families under global AP
- *spoof_blind*: no defense recovers it (identifiability limit), as on the test
- *fewer_agents*: Culver frames have n <= 3 (test up to 5), so per-agent-count comparisons cover n = 2, 3 only

## 13. Interpretation (AUTHOR)

<!-- AUTHOR: write this section only after reading sections 2-12. Keep to what the numbers support. -->
*To be written by the authors.* Suggested questions, answered from the tables above:

1. Does the v3.2 rule hold on Culver City under both AP definitions, and how large are the effects in AP points? (Descriptive; the test verdict stands.)
2. Is the clean cost within the 1% limit in an unseen town, and what does B-RAY remove (section 10)?
3. Does the R1 − B-RAY statement match the test's under each AP definition?
4. Which attacks remain unrecovered, and is the picture the same as on the test?
5. Which differences from the test (section 12) exceed what 4 scenarios can resolve?

## 14. Scope, labelling and deviations

**Domain shift, not real data.** Culver City is simulated with the same CARLA LiDAR model as the OPV2V test; it tests transfer to an unseen town layout, not to real sensors, real traffic or real attacks.

**Scope limits (pre-registered).** D-54 and D-63 (single attacker; random placement for the E4 families; spoof_blind bypass; ray-consistent / low-ray spoofs; B-RAY cannot restore removed objects; receiver sensor trusted; CARLA LiDAR; method chosen on exposed H), plus: PGD is white-box on this checkpoint with budgets relative to its clean H feature scale; B-NORM's threshold is fitted on clean H

**Labelling (OPV2V test preregistration).** Test numbers are the one-time final test. All E0-E5a numbers (blocks T and H) are development or held-out-but-exposed and are reported separately. v2 is the governing pre-registration. Culver City numbers are a separate, secondary held-out evaluation (D-72) and are labelled "unseen town, simulated sensor".

**Reporting rules (D-69).** Headline AP: global-ranking AP (D-64). absolute dAP in AP points next to every recovery. Scope: R1 cannot verify removals in receiver-blind regions (a removed object the receiver cannot see is UNKNOWN = keep).

**D-71 (part of the frozen v3.2 code used here).** runners/v3_2_stream.py: v3_extra = the v3.1 v3_extra with the copy loop replaced by copy_mabs: a record without 'mabs' is skipped after asserting ledger reason == 'stealth_infeasible' (any other cause still fails). Same reading as the frozen v3_analyze.frames_test ('if "mabs" in rec') and cond_of (no 'cands' -> clean, not applied). install() = v3.1 install() + v3_extra and preregistration swapped; v3/v3.1 frozen files byte-identical (The crash it fixed happened on the OPV2V test stream, not on Culver City.)

## Appendix: absolute AP@0.7

**global-ranking AP (headline)**

| Condition | No defense | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|---|
| clean (no attack) | 0.9062 | 0.9062 | 0.9062 | 0.9062 | 0.9062 | 0.7521 |
| spoof - feature | 0.8951 | 0.9062 | 0.9062 | 0.9062 | 0.8951 | 0.7521 |
| remove - feature | 0.8868 | 0.8868 | 0.8868 | 0.8868 | 0.8868 | 0.7521 |
| shift - feature | 0.8935 | 0.8998 | 0.8999 | 0.8999 | 0.8935 | 0.7521 |
| spoof - points | 0.9024 | 0.9024 | 0.9024 | 0.9024 | 0.9024 | 0.7521 |
| spoof in receiver-blind area | 0.8933 | 0.8933 | 0.8933 | 0.8933 | 0.8933 | 0.7521 |
| PGD untargeted r=0.25 | 0.9192 | 0.9192 | 0.9192 | 0.9192 | 0.7521 | 0.7521 |
| PGD remove r=0.25 | 0.8907 | 0.8907 | 0.8975 | 0.8907 | 0.7521 | 0.7521 |
| PGD untargeted stealth r=0.5 | 0.9072 | 0.9072 | 0.9072 | 0.9072 | 0.9072 | 0.7521 |
| PGD remove stealth r=0.25 | 0.8835 | 0.8835 | 0.8899 | 0.8835 | 0.8835 | 0.7521 |
| PGD untargeted stealth r=1.0 † | 0.8739 | 0.8741 | 0.8742 | 0.8742 | 0.8739 | 0.7521 |
| PGD remove stealth r=1.0 † | 0.4389 | 0.4389 | 0.7188 | 0.4389 | 0.4389 | 0.7521 |

**frame-order AP (OPV2V-comparable)**

| Condition | No defense | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|---|
| clean (no attack) | 0.8635 | 0.8635 | 0.8635 | 0.8635 | 0.8635 | 0.6921 |
| spoof - feature | 0.8431 | 0.8635 | 0.8558 | 0.8558 | 0.8431 | 0.6921 |
| remove - feature | 0.8349 | 0.8349 | 0.8349 | 0.8349 | 0.8349 | 0.6921 |
| shift - feature | 0.8300 | 0.8602 | 0.8602 | 0.8602 | 0.8300 | 0.6921 |
| spoof - points | 0.8553 | 0.8553 | 0.8553 | 0.8553 | 0.8553 | 0.6921 |
| spoof in receiver-blind area | 0.8355 | 0.8355 | 0.8355 | 0.8355 | 0.8355 | 0.6921 |
| PGD untargeted r=0.25 | 0.8508 | 0.8586 | 0.8586 | 0.8586 | 0.6921 | 0.6921 |
| PGD remove r=0.25 | 0.8618 | 0.8618 | 0.8597 | 0.8618 | 0.6921 | 0.6921 |
| PGD untargeted stealth r=0.5 | 0.8485 | 0.8485 | 0.8485 | 0.8485 | 0.8485 | 0.6921 |
| PGD remove stealth r=0.25 | 0.8602 | 0.8602 | 0.8509 | 0.8602 | 0.8602 | 0.6921 |
| PGD untargeted stealth r=1.0 † | 0.7036 | 0.7456 | 0.7456 | 0.7456 | 0.7036 | 0.6921 |
| PGD remove stealth r=1.0 † | 0.4375 | 0.4375 | 0.7050 | 0.4375 | 0.4375 | 0.6921 |

