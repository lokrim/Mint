Superseded by paper/ (evaluation-paper framing, 2026-10)

# Paper plan (intended argument; no results exist)

Checkpoint 1, 2026-10-22. Working title (to be revisited after results): *MINT: Calibrated, Region-Level Reliability of Received Features in Cooperative LiDAR Perception*. Publication suitability is a conclusion to reach after the evidence exists; no venue is assumed.

## Intended argument, conditional on evidence

1. **Problem.** Cooperative perception fuses untrusted intermediate features. Current defenses decide per sender, threshold uncalibrated consistency scores, and penalise honest unique views. Sender-level trust can be poisoned (TrustFlip).
2. **Reframing.** The quantity a receiver needs is the probability that a *specific received contribution* (sender × tile × time) harms the downstream output. For pixel-local attentive fusion, the effect of each contribution is computable, and the GT harm label is exact.
3. **Method.** Verify each contribution's effect claims (add / remove / shift) against the receiver's *own* rays, with a calibrated beta-binomial evidence model and explicit unknowns. Gate fusion at tile level.
4. **Identifiability.** Where no trusted evidence exists, no allowed-input method can separate honest unique views from fabrications. We measure how much of cooperative benefit (and attack harm) falls there.
5. **Evidence.** OPV2V (prior-work comparability), V2V4Real (real, single sender), Mixed Signals (real heterogeneous RSU; single session) as available. Grouped held-out evaluation, adaptive attacks, benign stresses, calibration, cost.
6. **Honest outcome.** Any of H1–H6 may be negative. In particular, H6 (ray evidence adds value) and H3 (unique views) may fail, and the identifiability result may dominate.

## Section outline and evidence required

| § | Content | Evidence needed (ledger IDs) | Status |
|---|---|---|---|
| 1 Introduction | Motivation; contributions stated only as supported | C-01, C-16..C-22 | not started |
| 2 Related work | CP architectures; CP security (CARLO, Shadow-Catcher, CAD, MATE, ROBOSAC, MADE, LUCIA, PoseGuard, GCP, TrustFlip, Latent Guardian, GLST, CP-Guard family); occupancy and evidential methods; calibration and selective prediction | literature package; C-01, C-02 | draftable after review |
| 3 Problem and threat model | Unit, estimand, settings A/B/C, threats T1–T6, identifiability | [contract](information_and_threat_model.md); C-02 | draftable |
| 4 Method | Effects; M3 → M4 derivation; calibration; gating; complexity | C-05, C-07..C-10 | blocked on Stages 1–3 |
| 5 Experimental setup | Datasets, splits and exposure, detectors, attacks, benign stresses, baselines, metrics | C-03..C-06, C-13 | blocked on Stages 1–5 |
| 6 Results | Reliability discrimination and calibration; task AP; unique-view analysis; adaptive attacks; benign controls | C-14..C-21 | blocked on Stage 6 |
| 7 Efficiency | Incremental vs end-to-end; memory; communication; proxy vs target | C-22 | blocked on Stage 7 |
| 8 Ablations | AB-1..AB-9 | C-21 | blocked |
| 9 Limitations | Single-session MS; simulated OP; 1 Hz labels; unknown-region bound; white-box assumptions; licence-constrained code | all | continuous |
| 10 Failure gallery | Worst units; adaptive successes; benign false gates | C-16, C-17 | blocked |
| Appendix | Reproduction commands; run hashes; protocol freeze; amendments; exposure ledger | all | continuous |

## Attribution rules

- **Ray ratios:** CARLO FSD/LPD [`sun2020carlo`]. Shadow test: [`hau2021shadowcatcher`]. Free-space conflict rules: [`zhang2024cad`].
- **Beta evidence updates for trust:** [`hallyburton2025mate`]. Beta-binomial overdispersion is a standard model (cite a statistics text at writing time; to be verified).
- **Attention trust:** [`wang2025lucia`]. Local feature-crop residuals: [`zhang2026poseguard`]. Conformal agent tests: [`zhao2024made`], [`tao2026gcp`].
- **Our contribution** may be claimed only for what the evidence supports: the estimand and unit, the label bridge, the evaluation, and possibly efficiency. **No novelty claim for "support/traversal ratios".**
