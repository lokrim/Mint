# MINT research charter

**MINT: Multi-agent Inbound Node Trust.** Planning checkpoint 1, 2026-10-22.
Status: proposal under review. Nothing here is a result.

## 1. Objective

Can a lightweight receiver estimate, for each received intermediate-feature contribution at a given time and place, whether including it will hurt or help perception? And does acting on that estimate keep or improve 3D detection quality against ground truth, under both corruption and benign conditions?

## 2. The scientific object (summary)

The full contract is in [information_and_threat_model.md](information_and_threat_model.md). In brief:

- **Unit.** One received *contribution* `c[i,t,u]`: sender `i`'s transmitted BEV feature vectors that fall in receiver-frame tile `u` at fusion time `t`, at every fusion scale. Not a sender, a frame, a point or a box.
- **Primary estimand.** `ρ[i,t,u] = P(D[i,t,u] ≤ m | X[t])`.
  - `D` is the GT-evaluated change in local detection error caused by including `c[i,t,u]` rather than excluding it. Positive `D` means harm.
  - `m` is a predeclared margin.
  - `X[t]` is the allowed receiver inputs.
  - So `ρ` is a **calibrated probability that this contribution is not harmful**.
  - Secondary estimand: the expected marginal utility `E[−D | X]`, to support weighting.
- **Output contract.** `r[i,t,u] = (status, value)` with `status ∈ {KNOWN, UNKNOWN_NO_EVIDENCE, UNKNOWN_STALE, NOT_APPLICABLE_EMPTY}`. The value is a probability only after calibration on a held-out calibration split. Uncalibrated variants must be labelled *scores*.
- **Not the estimand** (diagnostics only): corruption presence, geometric consistency, object correctness, model uncertainty, sender honesty or intent.

## 3. Hypotheses (falsifiable; preregistered in [evaluation_protocol.md](evaluation_protocol.md))

- **H1. Evidence tracks harm.** On held-out session groups, `r` ranks harmful contributions below non-harmful ones better than the detector-confidence and LUCIA-style baselines. Measured by AUROC and AUPRC on the D-labels among `KNOWN` units.
  - Falsified if the paired difference to the best baseline has a group-level interval that includes 0, or is negative.
- **H2. Utility.** Fusing with `r` (gating or weighting) retains at least 98% of clean AP of plain AttFuse (non-inferiority margin, an assumption) and improves attacked AP over plain AttFuse and the baselines, at matched compute and communication.
  - Falsified if the clean loss exceeds the margin, or the attacked gain is not positive across held-out groups.
- **H3. Honest unique views are kept.** Among useful contributions that no other source observes (`UNIQUE` stratum, defined by evaluator-only visibility), the false-rejection rate under the deployed policy is no higher than for corroborated useful contributions plus 5 percentage points (assumption).
  - Falsified otherwise. This is expected to be the hardest hypothesis.
- **H4. Identifiability boundary (expected negative, reported either way).** In regions that no trusted source observes, no allowed-input method beats chance against an attacker who imitates honest feature statistics. The method should return `UNKNOWN` there, not confident scores.
  - Tested by the blind-area attack ([attack protocol](attack_and_benign_protocol.md) A-F6).
- **H5. Cost.** On the same device, the incremental p95 latency of MINT (counterfactual passes, evidence, combiner and gating) is at most 10% of the receiver's end-to-end perception latency (own encoding, fusion and head). Extra state is at most 1 MB. Extra communication is 0 bytes in the core variant.
  - All three are budget assumptions pending the hardware decision.
  - By arithmetic, dense counterfactual passes cost about 15% (see the [budget](compute_memory_and_communication_budget.md) §3). Meeting H5 therefore depends on tile-sparse evaluation, which may fail.
- **H6. Ray evidence adds information.** Adding receiver-own ray support/contradiction to feature-only evidence improves H1 metrics within receiver-observed tiles.
  - Falsified if the ablation shows no gain. Ray evidence can be dropped without breaking H1–H3.

## 4. Candidate contributions (none assumed; see the [closest prior work](literature/comparison_matrix.csv))

The ideas below are **not novel by themselves**:
- Ray support/contradiction checks: CARLO 2020, Shadow-Catcher 2021, CAD 2024.
- Per-agent feature-consistency trust inside attention: LUCIA 2025.
- Per-object local feature anomaly scores: PoseGuard 2026.
- Region masking of disputed areas: TrustReflect 2026.
- Conformal per-agent tests: MADE 2024, GCP 2026.
- Beta-trust per track: MATE 2025.

What could still be a contribution, to be assessed only after evidence exists:
1. **A different estimand and unit.** A spatially resolved, calibrated probability that a received feature tile is *harmful to the downstream task*, with an explicit unknown state. Prior work outputs per-agent decisions or uncalibrated per-object anomaly flags.
2. **An exact counterfactual label bridge.** It exists for pixel-local attentive fusion. In the AttFuse/AttBEVBackbone code read here, per-scale fusion is a per-pixel softmax, followed only by stride-matched transposed convolutions and 1×1 heads. So a contribution's leave-one-tile-out effect can be computed exactly in two forward passes per sender. This was **derived from code, not yet verified by experiment** (verification check V-03 in the roadmap). Whether prior work used this is unverified.
3. **Rigorous evaluation that prior CP defenses lack:**
   - session-grouped splits;
   - an honest-unique-view stratum;
   - adaptive attacks aimed at the reliability module;
   - benign stresses;
   - calibration and risk–coverage reporting.
   It would be the first study on real heterogeneous V2X data with organized LiDAR grids, if Mixed Signals is feasible. That "first" is from our searches only.
4. **Efficiency.** Range-image (z-buffer) ray checks use the organized beam grid instead of 3D ray marching.
5. **An informative failure study.** How much of the cooperative benefit lies in regions where *no* trusted evidence exists, which bounds every consistency defense.

## 5. Non-goals

- Inferring malicious intent or certifying honesty.
- Global sender reputation as the decision variable.
- Physical laser-spoofing realizability: digital attacks are labelled as such.
- Late fusion (sending boxes) as the main setting. It may appear only as a reported comparison.
- Training a new cooperative detector architecture. We may train a standard AttFuse PointPillars model if no checkpoint exists for the chosen dataset.
- Claims about on-sensor microcontroller deployment.
- Publication promises.

## 6. Inherited constraints from Valid Point ([findings](findings/09_portable_handoff.md))

- Do not reuse the D/G statistics, their constants, thresholds or results.
- Placeholders are no-return slots. Handle them explicitly, never as points.
- mini_7 and mini_10 to mini_13 are exposed development data. They are never test data.
- Neighbouring clips are not independent sessions.
- Undefined, cannot-decide and failed-injection cases stay visible in every denominator.

## 7. Where things are decided

- Choices and alternatives: [decision_log.md](decision_log.md).
- Blockers: [risks_and_open_questions.md](risks_and_open_questions.md).
- What happens next: [next_session_brief.md](next_session_brief.md).
