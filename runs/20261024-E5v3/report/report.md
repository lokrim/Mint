# MINT final test (E5, OPV2V): results report

> **Status: FINAL TEST (one-time)**
> Source: FINAL TEST (one-time), v3 analysis

Generated 2026-10-26T17:49:29+05:30 by `runners/report_build.py`. Every number in this report is copied from the analysis outputs listed below; nothing is recomputed. Sections marked **AUTHOR** are left for the authors to write after reading the results.

| Provenance | |
|---|---|
| `e5_v3.json` | `runs/20261024-E5v3/e5_v3.json` · sha256 `70324a707f23e20b…` |
| `e5_test.json` | `runs/20261024-E5v3/e5_test.json` · sha256 `4b6823ba3603420a…` |
| `preregistration` | `runs/20261024-E5/preregistration_v3_2.json` · sha256 `8756868def368e85…` |
| Repository HEAD | `76509be7c67e5dd058ff78e0d5aa9ca955f3e6af` |
| Frozen code commit (preregistration) | `c883753f91c75e707d5df5fce8757851fad494de` |
| Preregistration version | v3.2 (supersedes v3.1 runs/20261024-E5/preregistration_v3_1.json only by D-71; v1, v2, v3 and v3.1 kept unchanged) |
| Scenarios / frames | 15 / 2066 (agents per frame: {'1': 119, '2': 866, '3': 869, '4': 111, '5': 101}) |

## 1. What was tested

**Defenses compared** (pre-registered comparison set): no defense; ego-only; B-NORM (D-66, new); B-RAY (primary); R1 (key secondary); R1-noREMOVE (ablation); oracle bounds as v2 (frozen e5_analyze).

**Conditions** (12): clean (no attack); spoof - feature; remove - feature; shift - feature; spoof - points; spoof in receiver-blind area; PGD untargeted r=0.25; PGD remove r=0.25; PGD untargeted stealth r=0.5; PGD remove stealth r=0.25; PGD untargeted stealth r=1.0 †; PGD remove stealth r=1.0 †.

† pgd_remove_stealth@r1.0, pgd_untargeted_stealth@r1.0: strong-attack level, added after seeing block-H development results (D-70, secondary; never used for a criterion).

**Metrics.** ΔAP@0.7 = AP of a defense minus AP with no defense on the same frames, in AP points (×100). Recovery = ΔAP / attack loss. Clean cost = relative AP@0.7 loss on unattacked frames. Every statistic is computed under two AP definitions: global-ranking AP (headline) and frame-order AP (OPV2V-comparable).

**Pre-registered rule (D-64).** every primary and key-secondary statistic is computed under both definitions with the same bootstrap (seed 0, 2000 resamples, scenario and 10-frame). The v2 success rule (B-RAY Holm-rejected in the co-test with R1 vs no defense on the scenario bootstrap, and B-RAY clean relative loss scenario-CI high <= 1%) is evaluated separately per AP definition, Holm within each definition. A success/robustness claim requires a pass under BOTH. Headline numbers are quoted with global-ranking AP; frame-order AP is reported for comparability with OPV2V papers. If the two disagree the report states 'AP-definition-dependent'. R1 - B-RAY (statement by scenario CI, v2 wording) is reported under both, side by side.

**Outcome wording.** Success: only if the v2 rule passes under both AP definitions (D-64); headline in global-ranking AP. Disagreement: report 'AP-definition-dependent'. Failure: report as the result; no rescue analysis presented as confirmatory.

## 2. Procedural checks

| Check | Detail | Passed |
|---|---|---|
| Completeness (scenarios, frames) | 15/15 scenarios, 2066/2066 frames | yes |
| Frame-order v3 = frozen v2 analysis | 4 statistics, point and scenario CI | yes |
| NumPy AP vs OpenCOOD AP | max abs. difference 1.9e-13 | yes |
| Compose checks identical (all scenarios) | 15 scenarios | yes |

## 3. Pre-registered verdict

**Success under both AP definitions.** v2 rule under global-ranking AP: passes; under frame-order AP: passes.

| AP definition | B-RAY ΔAP | B-RAY p (1-sided) | B-RAY Holm reject | R1 ΔAP | R1 p | R1 Holm reject | B-RAY clean loss CI (%) | clean CI high ≤ 1% | v2 rule passes |
|---|---|---|---|---|---|---|---|---|---|
| global-ranking AP (headline) | +0.15 | 0.0335 | yes | +0.45 | 0.0005 | yes | [+0.01, +0.30] | yes | yes |
| frame-order AP (OPV2V-comparable) | +0.76 | 0.0005 | yes | +0.19 | 0.2259 | no | [-0.30, +0.18] | yes | yes |

**Key secondary (R1 − B-RAY), statements emitted by the frozen analysis:**

| AP definition | R1 − B-RAY (pts) | 95% CI scen. | 95% CI 10-frame | Pre-registered statement |
|---|---|---|---|---|
| global-ranking AP (headline) | +0.31 | [+0.12, +0.55] | [+0.22, +0.40] | “the counterfactual improves over the box-level filter” |
| frame-order AP (OPV2V-comparable) | -0.57 | [-1.64, -0.11] | [-0.75, -0.43] | “the counterfactual performs worse than the box-level filter” |

The key secondary is **AP-definition-dependent** (the two definitions give different statements).

## 4. Headline: mean ΔAP@0.7 over the 4 original attacks

![Headline: mean ΔAP@0.7 over the 4 original attacks](figures/01_headline.png)

*Figure 1. Each defense's mean change in AP@0.7 against no defense, over spoof/remove/shift (feature) and spoof (points). Dot = point estimate; thick line = 95% CI from the scenario bootstrap (the pre-registered primary CI); thin line = 10-frame-block bootstrap. Ego-only is far off-scale and is listed in the table only.* Data: [`tables/01_headline.csv`](tables/01_headline.csv) · dark version: [`figures/01_headline_dark.png`](figures/01_headline_dark.png)

| Method | ΔAP@0.7 global | 95% CI scen. global | 95% CI 10-frame global | ΔAP@0.7 frame | 95% CI scen. frame | 95% CI 10-frame frame |
|---|---|---|---|---|---|---|
| B-RAY (primary) | +0.15 | [-0.01, +0.30] | [+0.06, +0.22] | +0.76 | [+0.49, +1.27] | [+0.63, +0.90] |
| R1 (key secondary) | +0.45 | [+0.29, +0.70] | [+0.37, +0.54] | +0.19 | [-0.45, +0.52] | [-0.00, +0.35] |
| R1-noREMOVE (ablation) | +0.26 | [+0.18, +0.36] | [+0.21, +0.30] | +0.66 | [+0.48, +1.03] | [+0.57, +0.77] |
| B-NORM (baseline) | -5.85 | [-9.65, -2.30] | [-7.04, -4.63] | -7.13 | [-11.82, -2.73] | [-8.61, -5.63] |
| Ego-only | -20.02 | [-23.10, -16.04] | [-21.08, -18.94] | -24.20 | [-29.44, -18.65] | [-25.62, -22.75] |

## 5. Every attack condition

![ΔAP@0.7 per condition: clean and original attacks](figures/02_per_family.png)

*Figure 2a. Every non-PGD condition × defense, both AP definitions, 95% CI from the scenario bootstrap. Ego-only in the table only.* Data: [`tables/02_per_family.csv`](tables/02_per_family.csv) · dark version: [`figures/02_per_family_dark.png`](figures/02_per_family_dark.png)

![ΔAP@0.7 per condition: optimized (PGD) attacks](figures/02b_per_family_pgd.png)

*Figure 2b. As 2a for the PGD conditions, on its own scale (PGD effects are much larger than the original attacks').* Data: [`tables/02b_per_family_pgd.csv`](tables/02b_per_family_pgd.csv) · dark version: [`figures/02b_per_family_pgd_dark.png`](figures/02b_per_family_pgd_dark.png)

**global-ranking AP (headline)** (ΔAP@0.7 in AP points, 95% CI scenario bootstrap)

| Condition | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|
| clean (no attack) | -0.11 [-0.26, -0.01] | +0.14 [+0.01, +0.31] | -0.01 [-0.03, +0.01] | -6.13 [-10.03, -2.40] | -21.21 [-24.26, -17.27] |
| spoof - feature | +0.51 [+0.25, +0.83] | +0.68 [+0.45, +1.02] | +0.55 [+0.35, +0.82] | -5.95 [-9.70, -2.41] | -19.69 [-22.75, -15.79] |
| remove - feature | -0.11 [-0.27, -0.00] | +0.27 [+0.10, +0.56] | -0.01 [-0.05, +0.02] | -5.67 [-9.45, -2.13] | -20.21 [-23.28, -16.15] |
| shift - feature | +0.17 [+0.03, +0.36] | +0.61 [+0.39, +0.93] | +0.38 [+0.24, +0.59] | -5.61 [-9.33, -2.13] | -19.25 [-22.51, -15.05] |
| spoof - points | +0.02 [-0.14, +0.13] | +0.25 [+0.10, +0.44] | +0.11 [+0.06, +0.18] | -6.18 [-10.06, -2.47] | -20.94 [-23.95, -17.08] |
| spoof in receiver-blind area | -0.01 [-0.18, +0.14] | +0.19 [+0.05, +0.37] | +0.05 [+0.00, +0.11] | -5.81 [-9.43, -2.29] | -19.00 [-22.11, -15.15] |
| PGD untargeted r=0.25 | -0.02 [-0.14, +0.09] | +0.28 [+0.08, +0.58] | +0.13 [+0.03, +0.30] | -8.19 [-11.93, -4.80] | -17.27 [-20.15, -13.53] |
| PGD remove r=0.25 | -0.10 [-0.23, -0.01] | +1.22 [+0.61, +2.15] | -0.04 [-0.08, -0.01] | -8.89 [-13.01, -5.08] | -17.97 [-20.77, -14.14] |
| PGD untargeted stealth r=0.5 | -0.06 [-0.21, +0.05] | +0.20 [+0.03, +0.46] | +0.06 [-0.03, +0.17] | -2.83 [-4.94, -0.80] | -18.45 [-21.49, -14.47] |
| PGD remove stealth r=0.25 | -0.10 [-0.24, -0.01] | +1.13 [+0.55, +1.99] | -0.04 [-0.09, -0.01] | -2.61 [-4.14, -1.06] | -18.15 [-20.98, -14.29] |
| PGD untargeted stealth r=1.0 † | +0.12 [-0.02, +0.30] | +0.40 [+0.14, +0.80] | +0.33 [+0.12, +0.66] | -4.32 [-7.28, -1.37] | -12.36 [-16.32, -7.39] |
| PGD remove stealth r=1.0 † | -0.01 [-0.05, +0.02] | +22.50 [+18.41, +27.48] | +0.07 [+0.01, +0.14] | -3.06 [-5.36, -1.03] | +19.19 [+14.29, +25.04] |

**frame-order AP (OPV2V-comparable)** (ΔAP@0.7 in AP points, 95% CI scenario bootstrap)

| Condition | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|
| clean (no attack) | +0.04 [-0.15, +0.24] | -0.51 [-1.44, -0.15] | +0.03 [+0.01, +0.08] | -7.76 [-12.97, -3.07] | -26.52 [-31.42, -21.36] |
| spoof - feature | +1.47 [+0.96, +2.41] | +0.68 [+0.21, +1.12] | +1.20 [+0.83, +1.94] | -6.93 [-11.57, -2.54] | -22.95 [-28.09, -17.45] |
| remove - feature | +0.05 [-0.12, +0.24] | -0.38 [-1.31, +0.05] | +0.04 [+0.00, +0.11] | -7.16 [-12.02, -2.69] | -25.36 [-30.51, -19.82] |
| shift - feature | +1.00 [+0.55, +1.78] | +0.55 [-0.22, +1.16] | +0.99 [+0.53, +1.67] | -6.73 [-11.19, -2.64] | -23.11 [-28.87, -17.25] |
| spoof - points | +0.51 [+0.26, +0.98] | -0.09 [-0.77, +0.20] | +0.43 [+0.31, +0.73] | -7.69 [-12.62, -3.00] | -25.40 [-30.41, -20.13] |
| spoof in receiver-blind area | +0.14 [-0.05, +0.41] | -0.34 [-1.04, -0.02] | +0.11 [+0.05, +0.24] | -6.70 [-11.23, -2.38] | -22.13 [-27.04, -16.81] |
| PGD untargeted r=0.25 | +0.83 [+0.40, +1.57] | +0.24 [-0.51, +0.77] | +0.76 [+0.44, +1.38] | -3.64 [-7.72, -0.92] | -15.50 [-22.71, -8.70] |
| PGD remove r=0.25 | -0.02 [-0.19, +0.10] | -0.07 [-1.34, +0.84] | -0.03 [-0.06, +0.01] | -13.40 [-19.41, -8.43] | -25.26 [-30.23, -20.36] |
| PGD untargeted stealth r=0.5 | +0.58 [+0.16, +1.34] | +0.03 [-0.65, +0.53] | +0.53 [+0.24, +1.07] | -4.00 [-7.69, -1.01] | -19.00 [-25.85, -11.66] |
| PGD remove stealth r=0.25 | -0.02 [-0.20, +0.12] | -0.14 [-1.40, +0.73] | -0.02 [-0.06, +0.01] | -3.51 [-5.76, -1.40] | -25.38 [-30.51, -20.36] |
| PGD untargeted stealth r=1.0 † | +2.09 [+1.00, +3.70] | +1.33 [+0.19, +2.44] | +1.93 [+1.01, +3.27] | -5.87 [-10.77, -1.58] | -6.42 [-17.85, +3.34] |
| PGD remove stealth r=1.0 † | +0.06 [-0.01, +0.14] | +20.94 [+16.96, +25.78] | +0.10 [+0.04, +0.19] | -3.62 [-6.63, -1.13] | +9.99 [+3.88, +16.79] |

## 6. Cost on clean frames

![Clean cost (relative AP@0.7 loss)](figures/03_clean_cost.png)

*Figure 3. Relative AP@0.7 loss on clean frames. The pre-registered success rule requires B-RAY's scenario-CI high ≤ 1% under both AP definitions.* Data: [`tables/03_clean_cost.csv`](tables/03_clean_cost.csv) · dark version: [`figures/03_clean_cost_dark.png`](figures/03_clean_cost_dark.png)

| Method | rel. loss global | 95% CI scen. (%) global | rel. loss frame | 95% CI scen. (%) frame |
|---|---|---|---|---|
| B-RAY (primary) | 0.13% | [+0.01, +0.30] | -0.05% | [-0.30, +0.18] |
| R1 (key secondary) | -0.16% | [-0.35, -0.01] | 0.62% | [+0.18, +1.75] |
| R1-noREMOVE (ablation) | 0.01% | [-0.01, +0.03] | -0.03% | [-0.10, -0.01] |
| B-NORM (baseline) | 6.92% | [+2.72, +11.33] | 9.45% | [+3.66, +15.70] |
| Ego-only | 23.93% | [+19.84, +27.10] | 32.27% | [+26.89, +37.04] |

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
| PGD untargeted r=0.25 | +3.95 | +11.02 | -0.00 / 0.08 | 0.07 / 0.02 | 0.03 / 0.07 | -2.07 / -0.33 | -4.37 / -1.41 | 100% | 0/1947 | 1541/1947 |
| PGD remove r=0.25 | +3.25 | +1.26 | -0.03 / -0.02 | 0.37 / -0.05 | -0.01 / -0.02 | -2.74 / -10.66 | -5.53 / -20.10 | 100% | 0/1947 | 1233/1947 |
| PGD untargeted stealth r=0.5 | +2.77 | +7.52 | -0.02 / 0.08 | 0.07 / 0.00 | 0.02 / 0.07 | -1.02 / -0.53 | -6.67 / -2.53 | 0% | 10/1947 | 1402/1937 |
| PGD remove stealth r=0.25 | +3.06 | +1.14 | -0.03 / -0.02 | 0.37 / -0.13 | -0.01 / -0.02 | -0.85 / -3.09 | -5.92 / -22.36 | 0% | 44/1947 | 1193/1903 |
| PGD untargeted stealth r=1.0 † | +8.86 | +20.10 | 0.01 / 0.10 | 0.04 / 0.07 | 0.04 / 0.10 | -0.49 / -0.29 | -1.39 / -0.32 | 0% | 3/1947 | 1709/1944 |
| PGD remove stealth r=1.0 † | +40.41 | +36.51 | -0.00 / 0.00 | 0.56 / 0.57 | 0.00 / 0.00 | -0.08 / -0.10 | 0.47 / 0.27 | 0% | 3/1947 | 1944/1944 |

**Expected outcomes, checked descriptively** (rules stated in the preregistration before any PGD run; not criteria):

| Condition | B-RAY ≈ 0 (point recovery < 0.10 under both AP definitions) | R1 > 0 (R1 dAP@0.7 scenario-CI low > 0 under both AP definitions) | B-NORM ≤ 5% (sender-1 flag rate over attacked frames <= 0.05) |
|---|---|---|---|
| PGD untargeted r=0.25 | yes | not applicable | not applicable |
| PGD remove r=0.25 | yes | no | not applicable |
| PGD untargeted stealth r=0.5 | yes | not applicable | yes |
| PGD remove stealth r=0.25 | yes | no | yes |
| PGD untargeted stealth r=1.0 † | no | not applicable | yes |
| PGD remove stealth r=1.0 † | yes | yes | yes |

## 9. Attack strength and realized-only effects

![Attack strength](figures/07_attack_strength.png)

*Figure 7. Attack loss per condition over all frames (with CI) and over the frames where the attack was realized.* Data: [`tables/07_attack_strength.csv`](tables/07_attack_strength.csv) · dark version: [`figures/07_attack_strength_dark.png`](figures/07_attack_strength_dark.png)

**Realized frames only, global-ranking AP (headline)** (ΔAP@0.7 in AP points, recovery in brackets)

| Condition | realized frames | attack loss | B-RAY (primary) ΔAP (recovery) | R1 (key secondary) ΔAP (recovery) | R1-noREMOVE (ablation) ΔAP (recovery) | B-NORM (baseline) ΔAP (recovery) | Ego-only ΔAP (recovery) |
|---|---|---|---|---|---|---|---|
| spoof - feature | 1136 | +2.37 | +0.82 (0.35) | +0.90 (0.38) | +0.83 (0.35) | -7.47 (-3.15) | -20.47 (-8.64) |
| remove - feature | 176 | +6.51 | -0.22 (-0.03) | +1.79 (0.28) | -0.03 (-0.01) | -9.05 (-1.39) | -20.60 (-3.16) |
| shift - feature | 206 | +8.03 | +0.30 (0.04) | +2.04 (0.25) | +1.10 (0.14) | -8.27 (-1.03) | -17.20 (-2.14) |
| spoof - points | 563 | +0.83 | +0.30 (0.36) | +0.42 (0.51) | +0.35 (0.42) | -7.85 (-9.48) | -21.99 (-26.57) |
| spoof in receiver-blind area | 1412 | +2.94 | +0.00 (0.00) | +0.13 (0.04) | +0.07 (0.02) | -6.51 (-2.21) | -19.69 (-6.69) |
| PGD untargeted r=0.25 | 1541 | +4.61 | -0.01 (-0.00) | +0.34 (0.07) | +0.15 (0.03) | -8.89 (-1.93) | -18.29 (-3.97) |
| PGD remove r=0.25 | 1233 | +5.00 | -0.13 (-0.03) | +1.87 (0.37) | -0.05 (-0.01) | -8.47 (-1.70) | -18.32 (-3.67) |
| PGD untargeted stealth r=0.5 | 1402 | +3.32 | -0.05 (-0.02) | +0.27 (0.08) | +0.07 (0.02) | -3.14 (-0.95) | -19.37 (-5.84) |
| PGD remove stealth r=0.25 | 1193 | +4.86 | -0.14 (-0.03) | +1.79 (0.37) | -0.06 (-0.01) | -2.22 (-0.46) | -18.25 (-3.75) |
| PGD untargeted stealth r=1.0 † | 1709 | +10.10 | +0.16 (0.02) | +0.45 (0.04) | +0.38 (0.04) | -4.69 (-0.47) | -12.53 (-1.24) |
| PGD remove stealth r=1.0 † | 1944 | +42.71 | -0.02 (-0.00) | +23.73 (0.56) | +0.07 (0.00) | -3.19 (-0.07) | +20.12 (0.47) |

**Realized frames only, frame-order AP (OPV2V-comparable)** (ΔAP@0.7 in AP points, recovery in brackets)

| Condition | realized frames | attack loss | B-RAY (primary) ΔAP (recovery) | R1 (key secondary) ΔAP (recovery) | R1-noREMOVE (ablation) ΔAP (recovery) | B-NORM (baseline) ΔAP (recovery) | Ego-only ΔAP (recovery) |
|---|---|---|---|---|---|---|---|
| spoof - feature | 1136 | +6.32 | +2.46 (0.39) | +1.45 (0.23) | +2.05 (0.32) | -8.48 (-1.34) | -23.00 (-3.64) |
| remove - feature | 176 | +6.24 | -0.16 (-0.03) | +0.89 (0.14) | -0.03 (-0.01) | -11.94 (-1.92) | -24.04 (-3.85) |
| shift - feature | 206 | +10.34 | +1.24 (0.12) | +2.05 (0.20) | +1.80 (0.17) | -10.35 (-1.00) | -19.56 (-1.89) |
| spoof - points | 563 | +4.38 | +1.74 (0.40) | +0.93 (0.21) | +1.51 (0.34) | -9.45 (-2.15) | -25.09 (-5.72) |
| spoof in receiver-blind area | 1412 | +6.58 | +0.15 (0.02) | -0.41 (-0.06) | +0.15 (0.02) | -7.23 (-1.10) | -22.91 (-3.48) |
| PGD untargeted r=0.25 | 1541 | +14.43 | +1.03 (0.07) | +0.46 (0.03) | +1.00 (0.07) | -2.63 (-0.18) | -15.17 (-1.05) |
| PGD remove r=0.25 | 1233 | +1.63 | -0.12 (-0.07) | +0.23 (0.14) | -0.04 (-0.03) | -14.12 (-8.64) | -26.79 (-16.40) |
| PGD untargeted stealth r=0.5 | 1402 | +10.64 | +0.87 (0.08) | +0.29 (0.03) | +0.83 (0.08) | -4.25 (-0.40) | -18.37 (-1.73) |
| PGD remove stealth r=0.25 | 1193 | +1.54 | -0.12 (-0.08) | +0.06 (0.04) | -0.05 (-0.03) | -3.01 (-1.95) | -26.62 (-17.30) |
| PGD untargeted stealth r=1.0 † | 1709 | +24.49 | +2.54 (0.10) | +1.69 (0.07) | +2.35 (0.10) | -6.20 (-0.25) | -4.61 (-0.19) |
| PGD remove stealth r=1.0 † | 1944 | +39.22 | +0.01 (0.00) | +22.38 (0.57) | +0.11 (0.00) | -3.91 (-0.10) | +10.16 (0.26) |

## 10. How the defenses act

![B-RAY removals](figures/08_bray_boxes.png)

*Figure 8. Boxes B-RAY removed, split by whether they matched a real car.* Data: [`tables/08_bray_boxes.csv`](tables/08_bray_boxes.csv) · dark version: [`figures/08_bray_boxes_dark.png`](figures/08_bray_boxes_dark.png)

![R1 gating against ground truth](figures/09_r1_units.png)

*Figure 9. Contributions (sender × 6.4 m tile) R1 switched off, by their ground-truth label.* Data: [`tables/09_r1_units.csv`](tables/09_r1_units.csv) · dark version: [`figures/09_r1_units_dark.png`](figures/09_r1_units_dark.png)

## 11. By number of cars

![Effect by number of cars](figures/10_by_agents.png)

*Figure 10. Mean ΔAP@0.7 over the 4 original attacks per agent count (frozen v2 analysis, frame-order AP).* Data: [`tables/10_by_agents.csv`](tables/10_by_agents.csv) · dark version: [`figures/10_by_agents_dark.png`](figures/10_by_agents_dark.png)

## 12. Interpretation (AUTHOR)

<!-- AUTHOR: write this section only after reading sections 2-11. Keep to what the numbers support. -->
*To be written by the authors.* Suggested questions, answered from the tables above:

1. Does the pre-registered verdict hold under both AP definitions, and how large is the headline effect in AP points?
2. Is the clean cost within the 1% limit, and what does B-RAY remove that it should not (section 10)?
3. Does R1 add anything over B-RAY (section 7)? Quote the pre-registered statement as written.
4. Which attacks are not recovered by any method (spoof in blind areas, stealth PGD), and is that the expected identifiability limit?
5. How do the final-test numbers compare with the development numbers (blocks T and H), reported separately?

## 13. Scope, labelling and deviations

**Scope limits (pre-registered).** D-54 and D-63 (single attacker; random placement for the E4 families; spoof_blind bypass; ray-consistent / low-ray spoofs; B-RAY cannot restore removed objects; receiver sensor trusted; CARLA LiDAR; method chosen on exposed H), plus: PGD is white-box on this checkpoint with budgets relative to its clean H feature scale; B-NORM's threshold is fitted on clean H

**Labelling.** Test numbers are the one-time final test. All E0-E5a numbers (blocks T and H) are development or held-out-but-exposed and are reported separately. v2 is the governing pre-registration.

**Reporting rules (D-69).** Headline AP: global-ranking AP (D-64). absolute dAP in AP points next to every recovery. Scope: R1 cannot verify removals in receiver-blind regions (a removed object the receiver cannot see is UNKNOWN = keep).

**Deviation D-71 (stream bug fix, no method change).** runners/v3_2_stream.py: v3_extra = the v3.1 v3_extra with the copy loop replaced by copy_mabs: a record without 'mabs' is skipped after asserting ledger reason == 'stealth_infeasible' (any other cause still fails). Same reading as the frozen v3_analyze.frames_test ('if "mabs" in rec') and cond_of (no 'cands' -> clean, not applied). install() = v3.1 install() + v3_extra and preregistration swapped; v3/v3.1 frozen files byte-identical Crashed attempt: KeyError 'mabs' at runners/v3_1_stream.py:73 on frame 1-3 of the first scenario, 20:04:10; results written before the fix: none (cache/ and v3extra/ empty; results are written per completed scenario). Seen before the fix: the frame-0 timing line of 2021_08_18_19_48_05 (6.4 s + 22.8 s) and the fact that >= 1 stealth condition was infeasible on >= 1 of its frames 1-3 (condition and count unknown); no AP, loss, flag or recovery value.

## Appendix: absolute AP@0.7

**global-ranking AP (headline)**

| Condition | No defense | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|---|
| clean (no attack) | 0.8864 | 0.8853 | 0.8878 | 0.8864 | 0.8251 | 0.6743 |
| spoof - feature | 0.8712 | 0.8763 | 0.8780 | 0.8767 | 0.8117 | 0.6743 |
| remove - feature | 0.8764 | 0.8753 | 0.8791 | 0.8762 | 0.8197 | 0.6743 |
| shift - feature | 0.8668 | 0.8685 | 0.8729 | 0.8706 | 0.8107 | 0.6743 |
| spoof - points | 0.8837 | 0.8839 | 0.8862 | 0.8849 | 0.8219 | 0.6743 |
| spoof in receiver-blind area | 0.8643 | 0.8642 | 0.8662 | 0.8648 | 0.8062 | 0.6743 |
| PGD untargeted r=0.25 | 0.8470 | 0.8468 | 0.8497 | 0.8483 | 0.7650 | 0.6743 |
| PGD remove r=0.25 | 0.8540 | 0.8530 | 0.8661 | 0.8536 | 0.7650 | 0.6743 |
| PGD untargeted stealth r=0.5 | 0.8588 | 0.8582 | 0.8607 | 0.8593 | 0.8305 | 0.6743 |
| PGD remove stealth r=0.25 | 0.8558 | 0.8547 | 0.8671 | 0.8554 | 0.8297 | 0.6743 |
| PGD untargeted stealth r=1.0 † | 0.7979 | 0.7991 | 0.8018 | 0.8012 | 0.7547 | 0.6743 |
| PGD remove stealth r=1.0 † | 0.4824 | 0.4823 | 0.7074 | 0.4830 | 0.4518 | 0.6743 |

**frame-order AP (OPV2V-comparable)**

| Condition | No defense | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|---|
| clean (no attack) | 0.8217 | 0.8221 | 0.8166 | 0.8219 | 0.7440 | 0.5565 |
| spoof - feature | 0.7859 | 0.8006 | 0.7927 | 0.7979 | 0.7166 | 0.5565 |
| remove - feature | 0.8100 | 0.8106 | 0.8062 | 0.8105 | 0.7385 | 0.5565 |
| shift - feature | 0.7876 | 0.7976 | 0.7931 | 0.7975 | 0.7203 | 0.5565 |
| spoof - points | 0.8105 | 0.8156 | 0.8096 | 0.8148 | 0.7336 | 0.5565 |
| spoof in receiver-blind area | 0.7777 | 0.7791 | 0.7744 | 0.7788 | 0.7107 | 0.5565 |
| PGD untargeted r=0.25 | 0.7115 | 0.7198 | 0.7139 | 0.7191 | 0.6751 | 0.5565 |
| PGD remove r=0.25 | 0.8091 | 0.8089 | 0.8084 | 0.8088 | 0.6751 | 0.5565 |
| PGD untargeted stealth r=0.5 | 0.7465 | 0.7523 | 0.7468 | 0.7518 | 0.7065 | 0.5565 |
| PGD remove stealth r=0.25 | 0.8103 | 0.8101 | 0.8089 | 0.8101 | 0.7752 | 0.5565 |
| PGD untargeted stealth r=1.0 † | 0.6207 | 0.6416 | 0.6340 | 0.6399 | 0.5620 | 0.5565 |
| PGD remove stealth r=1.0 † | 0.4566 | 0.4572 | 0.6660 | 0.4576 | 0.4204 | 0.5565 |

