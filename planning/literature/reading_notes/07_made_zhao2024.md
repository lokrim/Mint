# MADE: Zhao, Xiang, Yin, Pang, Wang, Chen, arXiv 2310.11901 v2 (IROS 2024 per handoff and search; verify)

- **Citation.** `zhao2024made`.
- **Access.** FULL-CLOSE on §III-B (attack), §IV (detector: match loss, collaborative reconstruction loss, conformal multi-test) and §V-A (setup). Read 2026-10-22.

## Question, unit, inputs
- **Question.** Can the ego detect which collaborators are malicious, with statistical false-detection control and no GT at inference?
- **Unit.** One agent per frame (accept or reject).
- **Inputs.**
  - ego detections with and without agent i;
  - fused-feature residual `R = f_G(F_ego; F_i) − f_G(F_ego; 0)`;
  - a benign calibration set `D_B` collected from past instances.

## Statistics
- **Match loss** `L_m`. Class-wise Hungarian matching between ego-only and ego+i proposals. The per-box loss is `max(p_c − p'_c, 0) + φ(1 − IoU)`.
- **Collaborative reconstruction loss** `L_r = ‖R − f_AE(R)‖²`. The autoencoder is trained on benign residuals from pairs in `D_B`.
- **Conformal p-values**: `p̂ = (1 + #{cal ≥ obs})/(1 + n)`.
- Combined by the Benjamini-Hochberg rule for 2 tests: reject if `min p ≤ α/2` or `max p ≤ α`.

## Our explanation and critique
- This is the cleanest *calibrated* agent-level test in the CP-security literature read here. It is the reference design for our calibration machinery.
- The conformal validity needs exchangeability of calibration and test statistics. Frames from the same scene are dependent, and the calibration/test split is by frames:
  - DAIR-V2X: 4,800 frames train detector; the remaining 1,800 frames for detection and evaluation;
  - V2X-Sim: scenes reserved by agent count.
  So the nominal FPR guarantee is not established across sessions.
- The match loss treats divergence from the ego as malicious. **Honest unique views increase it.**
- Agent-level output.

## Attack
Tu et al.-style PGD on the attacker's feature map:
- V2X-Sim: ε ∈ {0.05, 0.1, 0.2}, 10 steps.
- DAIR-V2X: ε ∈ {1.0, 1.5, 2.0}, 80 steps.

## Compute
- Two extra fusion and decode passes per agent, plus an autoencoder pass. Not reported in the sections read.

## Code
- Not checked.

## What transfers
- Conformal calibration of a residual statistic, computed **per tile** and with **session-grouped** calibration in MINT.
- The "with vs without agent i" counterfactual idea. In MINT this becomes the *evaluator's* GT label at tile level, not the inference statistic.

## Experiment
`B-MADE-tile`: apply MADE's two statistics per tile (match loss restricted to boxes centred in the tile; residual AE per tile). Use conformal p-values calibrated on held-out *sessions*. Measure the realized clean false-flag rate per held-out group against nominal α.
