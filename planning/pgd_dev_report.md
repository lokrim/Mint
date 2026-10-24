# PGD development on block H — STOPPED at the B-NORM stop condition

2026-10-24. All numbers are **development, exposed block H** (4 validate scenarios, 371 frames, n = 2). No test byte was downloaded or opened. `preregistration_v3.json` was **not written**: the user's rule "B-NORM catches > 95% of attacked frames at every r → report it and stop" fired.

Commits: D-64..D-66 recorded `8f561cf` (before any computation); re-stream code `9e83b9b`; plan committed `0563fa8` **before** any PGD run on H. Results: [`runs/20261024-PGD/pgd_H_results.json`](../runs/20261024-PGD/pgd_H_results.json), plan [`plan.json`](../runs/20261024-PGD/plan.json), reproduction [`reproduction_check.json`](../runs/20261024-PGD/reproduction_check.json).

## 1. Re-stream and reproduction (step 1): pass

- 2.765e9 bytes downloaded (budget 3.2e9; pre-check before the first byte, one scenario on disk, raw deleted after both cache files were re-read). Ledger: 4/4 complete.
- **Bitwise identical to E4** on 371/371 frames: GT, receiver scan, every condition's ledger, candidates of every subset, effects, attention tiles, compose checks. The frozen `e4_analyze` and `e5_analyze` rerun on the new cache give every accuracy field of `e4_heldout.json` and `e5a_H.json` exactly.
- One deviation from the check as I first wrote it. Attempt 1 also compared two wall-clock fields: `B-RAY_cost_dev`, seconds measured during analysis, and `overhead`, from E4's timing pass, which this re-stream skips by design. Those differ by nature. They were the only mismatches, and they were excluded in attempt 2. Attempt 1 is kept as `reproduction_check_attempt1.json`.
- Side records (exact model inputs, asserted to rebuild the batch and features bitwise on every frame; float64 Y+ rays; feature moments; B-NORM magnitudes) are in `runs/20261024-PGD/extra/` (643 MB, not in git).

## 2. Plan values (fixed before PGD)

| scale k | σ_k (sender, clean H) | mean \|f\| | ε_k at r = 0.25 / 0.5 / 1.0 | B-NORM τ_k (99.5th pct of clean ratio) |
|---|---|---|---|---|
| 1 (64×100×352) | 0.493 | 0.207 | 0.123 / 0.247 / 0.493 | 1.020 |
| 2 (128×50×176) | 0.123 | 0.0259 | 0.031 / 0.061 / 0.123 | 1.035 |
| 3 (256×25×88) | 0.0266 | 0.0019 | 0.0067 / 0.013 / 0.027 | 1.195 |

Clean sender/receiver magnitude ratios lie in a narrow band, 0.85–1.23 at every scale. B-NORM flags 6/371 clean frames (1.6%).

## 3. Result: B-NORM catches every PGD frame at every level

| condition | attack loss AP@0.7 global (frame-order) | B-NORM catch | min ratio, scale 3 (τ₃ = 1.195) | median \|δ\|/\|f\| scale 1/2/3 |
|---|---|---|---|---|
| pgd_untargeted r = 0.25 | **0.039** (0.202) | 371/371 | 1.99 | 0.40 / 0.80 / 1.21 |
| pgd_untargeted r = 0.5 | 0.282 (0.680) | 371/371 | 3.08 | 0.73 / 1.59 / 2.45 |
| pgd_untargeted r = 1.0 | 0.804 (0.852) | 371/371 | 5.48 | 1.26 / 3.13 / 5.20 |
| pgd_remove r = 0.25 | **0.034** (0.016) | 371/371 | 1.73 | 0.21 / 0.32 / 0.88 |
| pgd_remove r = 0.5 | 0.135 (0.117) | 371/371 | 2.56 | 0.41 / 0.64 / 1.76 |
| pgd_remove r = 1.0 | 0.513 (0.503) | 371/371 | 4.16 | 0.78 / 1.27 / 3.52 |
| (E4 families, for contrast) | | 3–20 of ~365 (0.8–5.5%) | | |

The selection rule would pick **r = 0.25 for both families** (the smallest r with global-AP loss ≥ 0.02). At r = 0.25 every frame is still caught, with no margin to spare: the smallest attacked ratio is 1.45–1.7× the threshold. **Why:** scale-3 features are sparse (σ₃ is 14× mean |f₃|), so an L∞ ball of 0.25σ₃ is about 3.5× the typical feature value. Sign-gradient PGD saturates that ball, raising the attacker's mean magnitude 1.7–6×. Defining "realistic" by σ_k does not keep the perturbation inside the clean feature distribution for this model.

**What catching costs.** B-NORM's action is to drop the sender, which equals ego-only (clean AP loss 20–24%). It therefore helps only when the attack does more damage than losing cooperation does (untargeted r ≥ 0.5, remove r = 1.0: recovery 0.35–0.77). At the selected r = 0.25, B-NORM *lowers* AP relative to no defense: global ΔAP −0.144 (untargeted) and −0.149 (remove). On the E4 families it is slightly harmful (mean-of-4 ΔAP −0.004 under both definitions) because of false flags.

## 4. Other development results on H (both AP definitions; scenario CI, 4 coarse blocks)

| statistic | frame-order | global (headline per D-64) |
|---|---|---|
| B-RAY mean ΔAP@0.7, 4 families | +0.0279 [0.007, 0.040], p = 0.0005, Holm reject | +0.0056 [0.002, 0.008], p = 0.0005, Holm reject |
| R1 mean ΔAP@0.7, 4 families | +0.0223 [−0.004, 0.032], p = 0.055, not rejected | +0.0085 [0.006, 0.010], p = 0.0005, Holm reject |
| B-RAY clean loss | 0.09% [−0.19, 0.41]% | 0.18% [0.03, 0.49]% |
| v2 rule pass | yes | yes → D-64: **pass under both** (on H) |
| R1 − B-RAY, 4 families | −0.0056 [−0.018, 0.003]: "not established" | **+0.0029 [0.0005, 0.0057]: "R1 improves"** → AP-definition-dependent |
| mean of 3 (no remove_feat): B-RAY / R1 | +0.037 / +0.030 | +0.008 / +0.011 |

Frame-order numbers reproduce E5a-H exactly (`consistency_vs_e5a_H`). The B-RAY numbers above use the float64 scan, as the test will; they equal the float16 E5a-H value to 4 decimals.

**PGD expectations (D-65), r = 0.25, global AP; recovery with 10-frame CI.** As expected, B-RAY recovers ≈ 0: 0.04 on untargeted and −0.04 on remove. R1 recovers 0.17 on untargeted (ΔAP +0.007 [0.003, 0.011]) and 0.33 on remove (ΔAP +0.011 [0.006, 0.016]); at r = 1.0, R1 recovers 0.53 on remove. One frame-order artifact: B-RAY "recovers" 0.26 of untargeted r = 0.25 under frame-order AP but only 0.04 under global AP.

**Realized-only (global AP), loss → ΔAP B-RAY / R1:**
- spoof_feat (248 frames): 0.044 → +0.019 / +0.020
- remove_feat (38): 0.086 → −0.003 / +0.007
- shift_feat (46): 0.146 → +0.003 / +0.012
- spoof_blind (308): 0.056 → +0.001 / +0.002
- pgd_remove r = 0.25 (193): 0.050 → −0.002 / +0.016

## 5. Decision needed (not taken)

By the stop rule I have not written v3, frozen code or run the dry runs. Options:

1. **Pre-register PGD as planned (r = 0.25 both families) and report "trivially detected by B-NORM at every tested budget" as a finding.** The D-65 rule and τ stay unchanged. The test then shows B-NORM catching ~100% while costing ego-only AP.
2. **Add a B-NORM-aware (adaptive) PGD** that also keeps every scale's magnitude ratio ≤ τ_k, e.g. by projecting onto the ratio constraint. This is the realistic white-box attacker against B-NORM. It is a new family and needs a new plan on H before any run.
3. **A magnitude-relative budget**, e.g. per-element |δ| ≤ r·|f| or a smaller r grid, re-selected on H under a new committed plan.

Options 2 and 3 are new post-hoc design choices on exposed H and would be labelled as such. Everything is development; the final test has not been touched.
