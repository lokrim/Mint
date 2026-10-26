# MINT final test (E5, OPV2V): results report

> **Status: DEVELOPMENT / DRY RUN - not results**
> Source: DEVELOPMENT, block H (exposed, D-53); stealth PGD = attack design on exposed H, POST HOC (D-68 as amended); 4 scenarios, n = 2; not a test
>
> These numbers come from development data. They show what the report will look like; they are **not** results of the final test and must not be quoted as such.

Generated 2026-10-26T12:57:18+05:30 by `runners/report_build.py`. Every number in this report is copied from the analysis outputs listed below; nothing is recomputed. Sections marked **AUTHOR** are left for the authors to write after reading the results.

| Provenance | |
|---|---|
| `e5_v3.json` | `runs/20261024-PGD/pgd_stealth_H_results.json` · sha256 `38b8442555739930…` |
| `e5_test.json` | `runs/20261024-E5/H/e5a_H.json` · sha256 `ce87df11255a20a0…` |
| `preregistration` | `runs/20261024-E5/preregistration_v3_2.json` · sha256 `8756868def368e85…` |
| Repository HEAD | `c83686df3c7bc26bd5a8b17897548dc028040916` |
| Frozen code commit (preregistration) | `c883753f91c75e707d5df5fce8757851fad494de` |
| Preregistration version | v3.2 (supersedes v3.1 runs/20261024-E5/preregistration_v3_1.json only by D-71; v1, v2, v3 and v3.1 kept unchanged) |
| Scenarios / frames | 4 / 371 (agents per frame: {'2': 371}) |

## 1. What was tested

**Defenses compared** (pre-registered comparison set): no defense; ego-only; B-NORM (D-66, new); B-RAY (primary); R1 (key secondary); R1-noREMOVE (ablation); oracle bounds as v2 (frozen e5_analyze).

**Conditions** (14): clean (no attack); spoof - feature; remove - feature; shift - feature; spoof - points; spoof in receiver-blind area; PGD untargeted r=0.25; PGD remove r=0.25; PGD untargeted stealth r=0.25; PGD untargeted stealth r=0.5; PGD untargeted stealth r=1.0 †; PGD remove stealth r=0.25; PGD remove stealth r=0.5; PGD remove stealth r=1.0 †.

† pgd_remove_stealth@r1.0, pgd_untargeted_stealth@r1.0: strong-attack level, added after seeing block-H development results (D-70, secondary; never used for a criterion).

**Metrics.** ΔAP@0.7 = AP of a defense minus AP with no defense on the same frames, in AP points (×100). Recovery = ΔAP / attack loss. Clean cost = relative AP@0.7 loss on unattacked frames. Every statistic is computed under two AP definitions: global-ranking AP (headline) and frame-order AP (OPV2V-comparable).

**Pre-registered rule (D-64).** every primary and key-secondary statistic is computed under both definitions with the same bootstrap (seed 0, 2000 resamples, scenario and 10-frame). The v2 success rule (B-RAY Holm-rejected in the co-test with R1 vs no defense on the scenario bootstrap, and B-RAY clean relative loss scenario-CI high <= 1%) is evaluated separately per AP definition, Holm within each definition. A success/robustness claim requires a pass under BOTH. Headline numbers are quoted with global-ranking AP; frame-order AP is reported for comparability with OPV2V papers. If the two disagree the report states 'AP-definition-dependent'. R1 - B-RAY (statement by scenario CI, v2 wording) is reported under both, side by side.

**Outcome wording.** Success: only if the v2 rule passes under both AP definitions (D-64); headline in global-ranking AP. Disagreement: report 'AP-definition-dependent'. Failure: report as the result; no rescue analysis presented as confirmatory.

## 2. Procedural checks

| Check | Detail | Passed |
|---|---|---|
| Completeness (scenarios, frames) | not recorded (development file) | n/a |
| Frame-order v3 = frozen v2 analysis | 4 statistics, point and scenario CI | n/a |
| NumPy AP vs OpenCOOD AP | max abs. difference 2.7e-14 | yes |
| Compose checks identical (all scenarios) | 4 scenarios | yes |

## 3. Pre-registered verdict

**Success under both AP definitions.** v2 rule under global-ranking AP: passes; under frame-order AP: passes.

| AP definition | B-RAY ΔAP | B-RAY p (1-sided) | B-RAY Holm reject | R1 ΔAP | R1 p | R1 Holm reject | B-RAY clean loss CI (%) | clean CI high ≤ 1% | v2 rule passes |
|---|---|---|---|---|---|---|---|---|---|
| global-ranking AP (headline) | +0.56 | 0.0005 | yes | +0.85 | 0.0005 | yes | [+0.03, +0.49] | yes | yes |
| frame-order AP (OPV2V-comparable) | +2.79 | 0.0005 | yes | +2.23 | 0.0550 | no | [-0.19, +0.41] | yes | yes |

**Key secondary (R1 − B-RAY), statements emitted by the frozen analysis:**

| AP definition | R1 − B-RAY (pts) | 95% CI scen. | 95% CI 10-frame | Pre-registered statement |
|---|---|---|---|---|
| global-ranking AP (headline) | +0.29 | [+0.05, +0.57] | [+0.10, +0.47] | “the counterfactual improves over the box-level filter” |
| frame-order AP (OPV2V-comparable) | -0.56 | [-1.75, +0.32] | [-0.91, -0.24] | “the counterfactual's benefit over a box-level filter is not established” |

The key secondary is **AP-definition-dependent** (the two definitions give different statements).

## 4. Headline: mean ΔAP@0.7 over the 4 original attacks

![Headline: mean ΔAP@0.7 over the 4 original attacks](figures/01_headline.png)

*Figure 1. Each defense's mean change in AP@0.7 against no defense, over spoof/remove/shift (feature) and spoof (points). Dot = point estimate; thick line = 95% CI from the scenario bootstrap (the pre-registered primary CI); thin line = 10-frame-block bootstrap. Ego-only is far off-scale and is listed in the table only.* Data: [`tables/01_headline.csv`](tables/01_headline.csv) · dark version: [`figures/01_headline_dark.png`](figures/01_headline_dark.png)

| Method | ΔAP@0.7 global | 95% CI scen. global | 95% CI 10-frame global | ΔAP@0.7 frame | 95% CI scen. frame | 95% CI 10-frame frame |
|---|---|---|---|---|---|---|
| B-RAY (primary) | +0.56 | [+0.24, +0.82] | [+0.38, +0.73] | +2.79 | [+0.71, +4.04] | [+2.34, +3.24] |
| R1 (key secondary) | +0.85 | [+0.55, +0.98] | [+0.65, +1.04] | +2.23 | [-0.35, +3.15] | [+1.72, +2.74] |
| R1-noREMOVE (ablation) | +0.64 | [+0.35, +0.88] | [+0.49, +0.79] | +2.44 | [+0.64, +3.50] | [+2.02, +2.89] |
| B-NORM (baseline) | -0.42 | [-0.59, -0.05] | [-0.91, -0.11] | -0.44 | [-0.62, -0.09] | [-0.97, -0.11] |
| Ego-only | -15.23 | [-18.53, -12.94] | [-17.68, -12.87] | -14.58 | [-19.64, -12.64] | [-17.37, -11.93] |

## 5. Every attack condition

![ΔAP@0.7 per condition: clean and original attacks](figures/02_per_family.png)

*Figure 2a. Every non-PGD condition × defense, both AP definitions, 95% CI from the scenario bootstrap. Ego-only in the table only.* Data: [`tables/02_per_family.csv`](tables/02_per_family.csv) · dark version: [`figures/02_per_family_dark.png`](figures/02_per_family_dark.png)

![ΔAP@0.7 per condition: optimized (PGD) attacks](figures/02b_per_family_pgd.png)

*Figure 2b. As 2a for the PGD conditions, on its own scale (PGD effects are much larger than the original attacks').* Data: [`tables/02b_per_family_pgd.csv`](tables/02b_per_family_pgd.csv) · dark version: [`figures/02b_per_family_pgd_dark.png`](figures/02b_per_family_pgd_dark.png)

**global-ranking AP (headline)** (ΔAP@0.7 in AP points, 95% CI scenario bootstrap)

| Condition | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|
| clean (no attack) | -0.16 [-0.42, -0.02] | +0.10 [-0.23, +0.45] | -0.09 [-0.27, +0.00] | -0.31 [-0.45, -0.10] | -18.29 [-21.41, -15.64] |
| spoof - feature | +1.50 [+0.58, +2.01] | +1.65 [+0.92, +1.86] | +1.46 [+0.72, +1.88] | -0.74 [-1.00, -0.21] | -14.78 [-18.42, -11.94] |
| remove - feature | -0.14 [-0.34, -0.02] | +0.25 [-0.23, +0.59] | -0.03 [-0.23, +0.09] | -0.15 [-0.31, +0.00] | -15.35 [-19.09, -13.19] |
| shift - feature | +0.68 [+0.41, +0.94] | +1.10 [+1.02, +1.24] | +0.90 [+0.60, +1.27] | -0.23 [-0.43, +0.00] | -13.17 [-17.22, -10.06] |
| spoof - points | +0.21 [-0.02, +0.40] | +0.42 [+0.22, +0.58] | +0.24 [+0.07, +0.38] | -0.56 [-0.96, +0.00] | -17.64 [-20.66, -15.01] |
| spoof in receiver-blind area | +0.12 [-0.38, +0.41] | +0.31 [-0.06, +0.51] | +0.13 [-0.20, +0.31] | -0.80 [-1.21, -0.16] | -13.49 [-16.43, -11.43] |
| PGD untargeted r=0.25 | +0.14 [+0.03, +0.24] | +0.68 [+0.29, +1.23] | +0.38 [+0.14, +0.99] | -14.38 [-15.43, -12.25] | -14.38 [-15.43, -12.25] |
| PGD remove r=0.25 | -0.14 [-0.38, +0.00] | +1.11 [+0.35, +1.46] | -0.02 [-0.09, +0.00] | -14.93 [-16.15, -13.44] | -14.93 [-16.15, -13.44] |
| PGD untargeted stealth r=0.25 | -0.13 [-0.41, +0.01] | +0.02 [-0.45, +0.54] | -0.22 [-0.43, -0.03] | -0.21 [-0.44, +0.00] | -17.48 [-20.45, -15.14] |
| PGD untargeted stealth r=0.5 | -0.03 [-0.29, +0.10] | +0.40 [+0.04, +0.72] | -0.03 [-0.26, +0.22] | -0.18 [-0.44, +0.00] | -14.97 [-15.70, -13.05] |
| PGD untargeted stealth r=1.0 † | +0.40 [+0.24, +0.53] | +1.46 [+1.25, +1.98] | +1.16 [+0.77, +1.87] | +0.00 [+0.00, +0.00] | -6.51 [-8.90, -0.65] |
| PGD remove stealth r=0.25 | -0.12 [-0.35, +0.00] | +0.99 [+0.18, +1.33] | -0.08 [-0.21, -0.00] | -0.22 [-0.45, +0.00] | -15.16 [-16.48, -13.48] |
| PGD remove stealth r=0.5 | -0.10 [-0.14, -0.04] | +5.88 [+4.48, +7.06] | -0.06 [-0.15, +0.00] | -0.20 [-0.47, +0.00] | -4.83 [-5.97, -2.49] |
| PGD remove stealth r=1.0 † | -0.01 [-0.04, +0.02] | +27.29 [+23.07, +33.13] | +0.18 [+0.08, +0.33] | +0.00 [+0.00, +0.00] | +31.99 [+27.49, +37.91] |

**frame-order AP (OPV2V-comparable)** (ΔAP@0.7 in AP points, 95% CI scenario bootstrap)

| Condition | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|
| clean (no attack) | -0.08 [-0.32, +0.16] | -0.26 [-1.60, +0.44] | -0.02 [-0.23, +0.11] | -0.37 [-0.57, -0.11] | -20.97 [-23.35, -19.95] |
| spoof - feature | +4.90 [+1.38, +6.94] | +3.97 [-0.12, +5.60] | +4.17 [+1.18, +5.86] | -0.74 [-1.02, -0.32] | -12.19 [-19.09, -9.21] |
| remove - feature | -0.05 [-0.28, +0.18] | -0.10 [-1.54, +0.56] | +0.11 [-0.16, +0.23] | -0.19 [-0.44, +0.00] | -17.53 [-21.13, -15.95] |
| shift - feature | +3.93 [+0.69, +5.76] | +3.23 [+0.85, +4.52] | +3.43 [+0.68, +5.01] | -0.21 [-0.55, +0.00] | -12.06 [-17.19, -10.80] |
| spoof - points | +2.38 [+0.53, +3.42] | +1.83 [-0.81, +2.54] | +2.07 [+0.46, +2.89] | -0.63 [-1.02, +0.00] | -16.53 [-21.15, -14.48] |
| spoof in receiver-blind area | +0.33 [-0.10, +0.70] | +0.09 [-1.11, +0.50] | +0.26 [-0.04, +0.48] | -0.73 [-1.09, -0.24] | -11.22 [-17.63, -7.33] |
| PGD untargeted r=0.25 | +5.25 [+3.36, +6.86] | +4.77 [+3.23, +5.71] | +4.58 [+2.93, +5.69] | -0.79 [-5.40, +2.75] | -0.79 [-5.40, +2.75] |
| PGD remove r=0.25 | -0.10 [-0.33, +0.04] | +0.42 [-3.77, +1.21] | +0.01 [-0.08, +0.15] | -19.41 [-25.13, -18.90] | -19.41 [-25.13, -18.90] |
| PGD untargeted stealth r=0.25 | +0.70 [-0.00, +1.07] | +0.15 [-0.93, +0.86] | +0.23 [+0.10, +0.37] | -0.23 [-0.56, +0.00] | -17.48 [-18.87, -16.64] |
| PGD untargeted stealth r=0.5 | +3.02 [+1.53, +3.88] | +2.60 [+1.28, +2.88] | +2.37 [+1.80, +2.68] | -0.19 [-0.51, +0.00] | -8.09 [-10.06, -5.01] |
| PGD untargeted stealth r=1.0 † | +6.61 [+4.23, +8.44] | +6.58 [+4.57, +8.06] | +6.33 [+4.34, +8.11] | +0.00 [+0.00, +0.00] | +16.22 [+10.69, +20.97] |
| PGD remove stealth r=0.25 | -0.10 [-0.33, +0.04] | +0.31 [-3.61, +1.04] | -0.06 [-0.16, +0.00] | -0.24 [-0.58, +0.00] | -19.62 [-25.33, -18.93] |
| PGD remove stealth r=0.5 | -0.08 [-0.12, +0.03] | +5.35 [+0.77, +6.74] | -0.05 [-0.16, +0.02] | -0.21 [-0.57, +0.00] | -9.69 [-14.47, -7.90] |
| PGD remove stealth r=1.0 † | +0.12 [+0.06, +0.16] | +27.28 [+23.49, +30.49] | +0.33 [+0.20, +0.43] | +0.00 [+0.00, +0.00] | +27.73 [+24.71, +28.74] |

## 6. Cost on clean frames

![Clean cost (relative AP@0.7 loss)](figures/03_clean_cost.png)

*Figure 3. Relative AP@0.7 loss on clean frames. The pre-registered success rule requires B-RAY's scenario-CI high ≤ 1% under both AP definitions.* Data: [`tables/03_clean_cost.csv`](tables/03_clean_cost.csv) · dark version: [`figures/03_clean_cost_dark.png`](figures/03_clean_cost_dark.png)

| Method | rel. loss global | 95% CI scen. (%) global | rel. loss frame | 95% CI scen. (%) frame |
|---|---|---|---|---|
| B-RAY (primary) | 0.18% | [+0.03, +0.49] | 0.09% | [-0.19, +0.41] |
| R1 (key secondary) | -0.11% | [-0.56, +0.26] | 0.31% | [-0.57, +2.03] |
| R1-noREMOVE (ablation) | 0.10% | [-0.00, +0.29] | 0.02% | [-0.14, +0.27] |
| B-NORM (baseline) | 0.34% | [+0.12, +0.53] | 0.43% | [+0.14, +0.73] |
| Ego-only | 20.49% | [+17.35, +24.43] | 24.33% | [+21.38, +29.65] |

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
| PGD untargeted r=0.25 | +3.91 | +20.18 | 0.04 / 0.26 | 0.17 / 0.24 | 0.10 / 0.23 | -3.68 / -0.04 | -3.68 / -0.04 | 100% | 0/371 | 328/371 |
| PGD remove r=0.25 | +3.35 | +1.56 | -0.04 / -0.07 | 0.33 / 0.27 | -0.01 / 0.01 | -4.45 / -12.46 | -4.45 / -12.46 | 100% | 0/371 | 193/371 |
| PGD untargeted stealth r=0.25 | +0.81 | +3.49 | -0.16 / 0.20 | 0.03 / 0.04 | -0.27 / 0.07 | -0.26 / -0.07 | -21.51 / -5.01 | 0% | 13/371 | 192/358 |
| PGD untargeted stealth r=0.5 | +3.32 | +12.88 | -0.01 / 0.23 | 0.12 / 0.20 | -0.01 / 0.18 | -0.05 / -0.01 | -4.51 / -0.63 | 0% | 1/371 | 285/370 |
| PGD untargeted stealth r=1.0 † | +11.78 | +37.19 | 0.03 / 0.18 | 0.12 / 0.18 | 0.10 / 0.17 | 0.00 / 0.00 | -0.55 / 0.44 | 0% | 0/371 | 358/371 |
| PGD remove stealth r=0.25 | +3.13 | +1.35 | -0.04 / -0.07 | 0.32 / 0.23 | -0.03 / -0.05 | -0.07 / -0.18 | -4.84 / -14.55 | 0% | 13/371 | 181/358 |
| PGD remove stealth r=0.5 | +13.45 | +11.28 | -0.01 / -0.01 | 0.44 / 0.47 | -0.00 / -0.00 | -0.01 / -0.02 | -0.36 / -0.86 | 0% | 1/371 | 298/370 |
| PGD remove stealth r=1.0 † | +50.27 | +48.70 | -0.00 / 0.00 | 0.54 / 0.56 | 0.00 / 0.01 | 0.00 / 0.00 | 0.64 / 0.57 | 0% | 0/371 | 370/371 |

**Expected outcomes, checked descriptively** (rules stated in the preregistration before any PGD run; not criteria):

| Condition | B-RAY ≈ 0 (point recovery < 0.10 under both AP definitions) | R1 > 0 (R1 dAP@0.7 scenario-CI low > 0 under both AP definitions) | B-NORM ≤ 5% (sender-1 flag rate over attacked frames <= 0.05) |
|---|---|---|---|
| PGD untargeted r=0.25 | no | not applicable | not applicable |
| PGD remove r=0.25 | yes | no | not applicable |
| PGD untargeted stealth r=0.25 | no | not applicable | yes |
| PGD untargeted stealth r=0.5 | no | not applicable | yes |
| PGD untargeted stealth r=1.0 † | no | not applicable | yes |
| PGD remove stealth r=0.25 | yes | no | yes |
| PGD remove stealth r=0.5 | yes | yes | yes |
| PGD remove stealth r=1.0 † | yes | yes | yes |

## 9. Attack strength and realized-only effects

![Attack strength](figures/07_attack_strength.png)

*Figure 7. Attack loss per condition over all frames (with CI) and over the frames where the attack was realized.* Data: [`tables/07_attack_strength.csv`](tables/07_attack_strength.csv) · dark version: [`figures/07_attack_strength_dark.png`](figures/07_attack_strength_dark.png)

**Realized frames only, global-ranking AP (headline)** (ΔAP@0.7 in AP points, recovery in brackets)

| Condition | realized frames | attack loss | B-RAY (primary) ΔAP (recovery) | R1 (key secondary) ΔAP (recovery) | R1-noREMOVE (ablation) ΔAP (recovery) | B-NORM (baseline) ΔAP (recovery) | Ego-only ΔAP (recovery) |
|---|---|---|---|---|---|---|---|
| spoof - feature | 248 | +4.38 | +1.87 (0.43) | +2.01 (0.46) | +1.76 (0.40) | -0.90 (-0.21) | -13.57 (-3.10) |
| remove - feature | 38 | +8.61 | -0.31 (-0.04) | +0.65 (0.07) | -0.31 (-0.04) | -0.87 (-0.10) | -15.44 (-1.79) |
| shift - feature | 46 | +14.60 | +0.28 (0.02) | +1.20 (0.08) | +1.04 (0.07) | +0.00 (0.00) | -10.42 (-0.71) |
| spoof - points | 187 | +1.10 | +0.59 (0.53) | +0.71 (0.65) | +0.52 (0.48) | -0.62 (-0.57) | -16.06 (-14.61) |
| spoof in receiver-blind area | 308 | +5.56 | +0.13 (0.02) | +0.24 (0.04) | +0.14 (0.03) | -0.98 (-0.18) | -12.81 (-2.30) |
| PGD untargeted r=0.25 | 328 | +3.97 | +0.16 (0.04) | +0.68 (0.17) | +0.35 (0.09) | -14.30 (-3.60) | -14.30 (-3.60) |
| PGD remove r=0.25 | 193 | +5.04 | -0.19 (-0.04) | +1.64 (0.33) | -0.04 (-0.01) | -14.59 (-2.90) | -14.59 (-2.90) |
| PGD untargeted stealth r=0.25 | 192 | +1.03 | -0.13 (-0.12) | +0.12 (0.12) | -0.27 (-0.26) | +0.00 (0.00) | -17.32 (-16.81) |
| PGD untargeted stealth r=0.5 | 285 | +3.70 | -0.03 (-0.01) | +0.43 (0.12) | -0.06 (-0.02) | +0.00 (0.00) | -14.61 (-3.95) |
| PGD untargeted stealth r=1.0 † | 358 | +11.75 | +0.40 (0.03) | +1.46 (0.12) | +1.15 (0.10) | +0.00 (0.00) | -6.36 (-0.54) |
| PGD remove stealth r=0.25 | 181 | +5.04 | -0.20 (-0.04) | +1.64 (0.33) | -0.08 (-0.02) | +0.00 (0.00) | -14.07 (-2.79) |
| PGD remove stealth r=0.5 | 298 | +15.22 | -0.11 (-0.01) | +6.62 (0.43) | -0.07 (-0.00) | +0.00 (0.00) | -3.50 (-0.23) |
| PGD remove stealth r=1.0 † | 370 | +50.34 | -0.01 (-0.00) | +27.33 (0.54) | +0.18 (0.00) | +0.00 (0.00) | +32.03 (0.64) |

**Realized frames only, frame-order AP (OPV2V-comparable)** (ΔAP@0.7 in AP points, recovery in brackets)

| Condition | realized frames | attack loss | B-RAY (primary) ΔAP (recovery) | R1 (key secondary) ΔAP (recovery) | R1-noREMOVE (ablation) ΔAP (recovery) | B-NORM (baseline) ΔAP (recovery) | Ego-only ΔAP (recovery) |
|---|---|---|---|---|---|---|---|
| spoof - feature | 248 | +11.17 | +6.03 (0.54) | +4.97 (0.44) | +4.99 (0.45) | -0.91 (-0.08) | -9.40 (-0.84) |
| remove - feature | 38 | +8.59 | -0.21 (-0.02) | +0.14 (0.02) | -0.24 (-0.03) | -1.13 (-0.13) | -17.38 (-2.02) |
| shift - feature | 46 | +15.26 | +1.06 (0.07) | +1.24 (0.08) | +1.41 (0.09) | +0.00 (0.00) | -11.44 (-0.75) |
| spoof - points | 187 | +8.09 | +4.38 (0.54) | +3.60 (0.45) | +3.69 (0.46) | -0.57 (-0.07) | -11.62 (-1.44) |
| spoof in receiver-blind area | 308 | +11.32 | +0.34 (0.03) | +0.10 (0.01) | +0.27 (0.02) | -0.90 (-0.08) | -9.79 (-0.86) |
| PGD untargeted r=0.25 | 328 | +21.12 | +5.09 (0.24) | +4.52 (0.21) | +4.33 (0.20) | -0.16 (-0.01) | -0.16 (-0.01) |
| PGD remove r=0.25 | 193 | +0.83 | -0.14 (-0.17) | +0.16 (0.19) | +0.01 (0.01) | -21.01 (-25.32) | -21.01 (-25.32) |
| PGD untargeted stealth r=0.25 | 192 | +5.63 | +1.04 (0.18) | +0.31 (0.05) | +0.38 (0.07) | +0.00 (0.00) | -15.99 (-2.84) |
| PGD untargeted stealth r=0.5 | 285 | +15.27 | +3.42 (0.22) | +3.03 (0.20) | +2.75 (0.18) | +0.00 (0.00) | -6.43 (-0.42) |
| PGD untargeted stealth r=1.0 † | 358 | +37.50 | +6.59 (0.18) | +6.52 (0.17) | +6.28 (0.17) | +0.00 (0.00) | +16.63 (0.44) |
| PGD remove stealth r=0.25 | 181 | +0.88 | -0.20 (-0.23) | +0.11 (0.12) | -0.08 (-0.09) | +0.00 (0.00) | -20.69 (-23.46) |
| PGD remove stealth r=0.5 | 298 | +12.34 | -0.09 (-0.01) | +5.81 (0.47) | -0.05 (-0.00) | +0.00 (0.00) | -9.26 (-0.75) |
| PGD remove stealth r=1.0 † | 370 | +48.77 | +0.13 (0.00) | +27.32 (0.56) | +0.33 (0.01) | +0.00 (0.00) | +27.76 (0.57) |

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
| clean (no attack) | 0.8926 | 0.8910 | 0.8936 | 0.8917 | 0.8895 | 0.7097 |
| spoof - feature | 0.8575 | 0.8725 | 0.8740 | 0.8721 | 0.8501 | 0.7097 |
| remove - feature | 0.8632 | 0.8618 | 0.8657 | 0.8629 | 0.8616 | 0.7097 |
| shift - feature | 0.8414 | 0.8483 | 0.8525 | 0.8504 | 0.8391 | 0.7097 |
| spoof - points | 0.8861 | 0.8882 | 0.8903 | 0.8885 | 0.8805 | 0.7097 |
| spoof in receiver-blind area | 0.8446 | 0.8459 | 0.8477 | 0.8459 | 0.8366 | 0.7097 |
| PGD untargeted r=0.25 | 0.8535 | 0.8550 | 0.8603 | 0.8573 | 0.7097 | 0.7097 |
| PGD remove r=0.25 | 0.8591 | 0.8576 | 0.8702 | 0.8588 | 0.7097 | 0.7097 |
| PGD untargeted stealth r=0.25 | 0.8845 | 0.8832 | 0.8847 | 0.8823 | 0.8824 | 0.7097 |
| PGD untargeted stealth r=0.5 | 0.8594 | 0.8591 | 0.8634 | 0.8591 | 0.8576 | 0.7097 |
| PGD untargeted stealth r=1.0 † | 0.7748 | 0.7788 | 0.7894 | 0.7864 | 0.7748 | 0.7097 |
| PGD remove stealth r=0.25 | 0.8613 | 0.8601 | 0.8712 | 0.8604 | 0.8591 | 0.7097 |
| PGD remove stealth r=0.5 | 0.7581 | 0.7571 | 0.8169 | 0.7575 | 0.7561 | 0.7097 |
| PGD remove stealth r=1.0 † | 0.3899 | 0.3898 | 0.6628 | 0.3916 | 0.3899 | 0.7097 |

**frame-order AP (OPV2V-comparable)**

| Condition | No defense | B-RAY (primary) | R1 (key secondary) | R1-noREMOVE (ablation) | B-NORM (baseline) | Ego-only |
|---|---|---|---|---|---|---|
| clean (no attack) | 0.8618 | 0.8610 | 0.8591 | 0.8616 | 0.8581 | 0.6521 |
| spoof - feature | 0.7740 | 0.8230 | 0.8137 | 0.8157 | 0.7666 | 0.6521 |
| remove - feature | 0.8274 | 0.8269 | 0.8264 | 0.8285 | 0.8255 | 0.6521 |
| shift - feature | 0.7726 | 0.8120 | 0.8049 | 0.8069 | 0.7705 | 0.6521 |
| spoof - points | 0.8173 | 0.8412 | 0.8356 | 0.8380 | 0.8110 | 0.6521 |
| spoof in receiver-blind area | 0.7643 | 0.7675 | 0.7651 | 0.7669 | 0.7569 | 0.6521 |
| PGD untargeted r=0.25 | 0.6600 | 0.7125 | 0.7077 | 0.7058 | 0.6521 | 0.6521 |
| PGD remove r=0.25 | 0.8462 | 0.8451 | 0.8504 | 0.8463 | 0.6521 | 0.6521 |
| PGD untargeted stealth r=0.25 | 0.8269 | 0.8339 | 0.8284 | 0.8292 | 0.8246 | 0.6521 |
| PGD untargeted stealth r=0.5 | 0.7329 | 0.7631 | 0.7589 | 0.7566 | 0.7310 | 0.6521 |
| PGD untargeted stealth r=1.0 † | 0.4898 | 0.5559 | 0.5556 | 0.5532 | 0.4898 | 0.6521 |
| PGD remove stealth r=0.25 | 0.8483 | 0.8473 | 0.8514 | 0.8476 | 0.8459 | 0.6521 |
| PGD remove stealth r=0.5 | 0.7490 | 0.7482 | 0.8025 | 0.7485 | 0.7469 | 0.6521 |
| PGD remove stealth r=1.0 † | 0.3748 | 0.3760 | 0.6476 | 0.3781 | 0.3748 | 0.6521 |

