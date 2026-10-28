# MINT: questions and answers for friends and evaluators

Written 2026-10-27 from the repository, not from memory. Every number is copied from a result file named next to it; AP numbers are **AP points** (AP@0.7 × 100) unless marked %. Nothing here is a new result.

Main sources:
- Final test report: [`runs/20261024-E5v3/report/report.md`](../runs/20261024-E5v3/report/report.md) and its `tables/*.csv`.
- Governing preregistration: [`runs/20261024-E5/preregistration_v3_2.json`](../runs/20261024-E5/preregistration_v3_2.json).
- Decisions: [`decision_log.md`](decision_log.md) (D-01..D-25) and [`decision_log_proposed_appendix.md`](decision_log_proposed_appendix.md) (D-26..D-72).
- Attack code: [`runners/e0_stream.py`](../runners/e0_stream.py) (`attack_features`, `attack_points`), [`src/mint/attacks/blind.py`](../src/mint/attacks/blind.py), [`src/mint/attacks/pgd_v3.py`](../src/mint/attacks/pgd_v3.py), dispatch in [`runners/v3_common.py`](../runners/v3_common.py) (`attacked_feats`).

Two AP definitions appear everywhere (D-64):
- **Global-ranking AP** (headline): detections from all frames are sorted together by score.
- **Frame-order AP** (OpenCOOD default, comparable with OPV2V papers): frames concatenated in order, no global sort.

They can disagree, and on one key question they do. Both are always reported.

---

## Part A. The project in one paragraph

In cooperative perception, cars send each other intermediate LiDAR features (bird's-eye-view feature maps), and the receiver fuses them with its own to detect cars. A malicious sender can edit its features to make fake cars appear (spoof), real cars disappear (remove) or cars move (shift). MINT's method, **R1**, asks for each sender and each 6.4 m × 6.4 m tile: *"what does my output look like with this sender versus without it here?"* Each difference is a concrete claim (ADD a box, REMOVE a box, SHIFT a box). R1 checks the claim against the **receiver's own LiDAR rays**, and switches the contribution off only if the rays contradict it with a Wilson 95% margin. Where the receiver cannot see, the verdict is UNKNOWN and the contribution is kept. The detector is the released OpenCOOD AttFuse (PointPillars) checkpoint, unchanged; everything runs on an M1 CPU.

---

## Part B. Your friends' questions

### B1. What are the results, and how do they compare with the baselines?

**Methods compared** (frozen before the test, D-56, D-66):

| Method | What it does | Role |
|---|---|---|
| No defense | Plain AttFuse fusion of all senders | Reference |
| Ego-only | Ignore every sender | Lower bound: value of cooperation |
| **B-RAY** | Box-level free-space filter: drop a final box if the receiver's rays pass through it (Wilson 95% upper bound of support < 0.5). Known prior idea (CARLO 2020, Shadow-Catcher 2021, CAD 2024) | **Pre-registered primary** |
| **R1** | The proposed per-sender, per-tile counterfactual with ray verification | Key secondary |
| R1-noREMOVE | R1 but never acts on REMOVE verdicts | Ablation |
| B-NORM | Drop a sender whose feature magnitude exceeds the 99.5th percentile seen on clean data | Simple feature-statistics baseline |

Why is B-RAY the primary and not our own method? Because on the development block H, B-RAY beat R1 under the frozen metric, and a rule fixed beforehand (D-57) said the better one becomes the primary (D-58). This is honest but means the "headline pass" belongs to the known baseline, not to R1.

**Final test** (one-time, 15 OPV2V test scenarios, 2,066 frames; report §3–§6):

Mean ΔAP@0.7 versus no defense over the 4 original attacks, 95% scenario-bootstrap CI:

| Method | Global-ranking AP | Frame-order AP |
|---|---|---|
| B-RAY (primary) | **+0.15** [−0.01, +0.30] | **+0.76** [+0.49, +1.27] |
| R1 | **+0.45** [+0.29, +0.70] | +0.19 [−0.45, +0.52] |
| R1-noREMOVE | +0.26 [+0.18, +0.36] | +0.66 [+0.48, +1.03] |
| B-NORM | −5.85 [−9.65, −2.30] | −7.13 [−11.82, −2.73] |
| Ego-only | −20.02 | −24.20 |

Plain-English reading:

1. **The pre-registered verdict is "success under both AP definitions"**, but for B-RAY, and narrowly. Under global AP its one-sided Holm test passes (p = 0.0335) while the two-sided CI touches 0. Both facts must be stated.
2. **The effects are small in absolute terms.** No-defense AP@0.7 under the original attacks is 0.867–0.884 (global); the attacks themselves only cost 0.27–1.97 AP points over all frames (`tables/07_attack_strength.csv`), because many attack attempts do not change the output.
3. **R1 vs B-RAY depends on the AP definition.** R1 − B-RAY = **+0.31** [+0.12, +0.55] under global AP ("improves"), **−0.57** [−1.64, −0.11] under frame-order AP ("performs worse"). This was visible on development data too. You cannot honestly say "R1 beats B-RAY" without that qualifier.
4. **Where R1 clearly wins: removal attacks.** B-RAY can only delete boxes, so it cannot restore a deleted car. On the strongest stealth removal attack (PGD remove stealth r = 1.0†), no-defense AP drops to 0.48; R1 gives **+22.50** (global) / **+20.94** (frame-order) AP points, B-RAY gives −0.01 / +0.06. This condition was added after seeing development results (D-70), so it is secondary and labelled †.
5. **R1 is the only defense positive in all 12 conditions under global AP** (report §5). Under frame-order AP it is negative in several, including clean (−0.51).
6. **B-NORM fails both ways.** It catches 100% of plain PGD but 0% of stealth PGD (which is designed to stay under its threshold), and it costs 6.9% (global) / 9.5% (frame-order) relative AP on clean frames, with a 17% clean false-flag rate.
7. **Ego-only is far worse than any defense** (−20 AP points), so cooperation is worth defending rather than switching off. Exception: under PGD remove stealth r = 1.0†, ego-only beats no defense (+19.19), but R1 is still higher (+22.50).

**Clean cost** (relative AP@0.7 loss on unattacked frames, report §6): B-RAY 0.13% / −0.05%; R1 −0.16% / **0.62% (CI up to 1.75%)**; B-NORM 6.92% / 9.45%. On clean frames R1 switches off 718 contributions, of which 521 were useful and 190 harmful, so its precision there is 0.27 (`tables/09_r1_units.csv`).

**Compute** (paper Table runtime, test set, M1 CPU, p50 / p95 overhead over receiver-only perception): dense R1 20/46% at n = 2, 53/102% at n = 3, 123/170% at n ≥ 4. B-RAY 4–11% p50. The original 10% p95 budget was not met by any R1 variant (D-50, labelled post hoc).

### B2. What are the dataset splits?

Dataset: **OPV2V** (CARLA-simulated, 64-beam LiDAR, 1–5 connected cars per frame). The detector is the released AttFuse checkpoint trained by its authors on the OPV2V train split; MINT never trains or fine-tunes it. It reproduces the published test AP@0.7 (0.8155 vs 0.815, Stage 1).

MINT never uses the OPV2V train split. Its own blocks (paper `tables/tab_splits.tex`, exposure ledger):

| Block | Source | Scenarios | Frames | Cars/frame | Role |
|---|---|---|---|---|---|
| **T** | OPV2V validate (3 scenarios) | 3 | 404 | 2–4 | Development, in-sample. R1's rule was written here. |
| **H** | OPV2V validate (4 other scenarios) | 4 | 371 | 2 only | Held out for E4, then **exposed**. B-RAY selected as primary here (D-57/58). B-NORM threshold and PGD budgets fitted here. |
| **Test** | OPV2V test minus `2021_08_23_12_58_19` | 15 | 2,066 | 1–5 | **One-time final test.** Before it, only clean detector AP had been seen (Stage-1 reproduction); no MINT, baseline or attack outcome. |
| Spike scenario | OPV2V test `2021_08_23_12_58_19` | 1 | — | — | Moved to development (its clean AP was inspected in the Stage-1 spike, D-21). |
| **Culver City** | OPV2V `test_culver_city` | 4 | 550 | — | **In progress.** Secondary "unseen town, simulated sensor" check (D-72). Stream still running at the time of writing; no results exist yet. Never pooled with the test. |

Splits are by **whole scenario**, never by frame, because frames within a scenario are strongly correlated. Confidence intervals use a scenario bootstrap (primary) and a 10-frame-block bootstrap (secondary), seed 0, 2,000 resamples.

Test frame mix by number of cars: n=1: 119, n=2: 866, n=3: 869, n=4: 111, n=5: 101. Frames with only the receiver (n = 1) cannot be attacked and are scored as clean.

Not used: Mixed Signals (real data, but no released checkpoint, 214 GB, one ~35-min session) and V2V4Real (planned real-data replication, not started).

### B3. What synthetic injections and attacks are used?

Common setup for all attacks (preregistration scope limits, `v3_common.attacked_feats`):
- **One attacker per frame, always sender index 1** (the first non-receiver car). The defenses are not told who it is.
- The attack is attempted on **every frame with ≥ 2 cars** (1,947 of 2,066 test frames), with a seed derived from (family, scenario, frame), so it is reproducible.
- The attacker picks a target real car that it can see itself (≥ 20 of its own LiDAR points in the box). It uses ground-truth boxes for this choice; that is attacker knowledge, and the defenses never see ground truth.
- An attempt is **"realized"** only if it actually changes the receiver's output. Many do not, because attentive fusion often overrides one sender. Results are reported over all frames (primary) and realized frames only (secondary).

**Group 1: hand-crafted "original" attacks (the primary mean averages the first four)**

| Name in tables | Level | What it does | Realized on test |
|---|---|---|---|
| spoof – feature (`spoof_feat`) | Feature map | Copy the feature patch of a real car the attacker sees and paste it into a random empty location: a **fake car**. | 1,136 frames |
| remove – feature (`remove_feat`) | Feature map | Overwrite a real car's feature patch with a background patch from elsewhere: **erase a car**. | 176 |
| shift – feature (`shift_feat`) | Feature map | Erase a car and paste it one coarse cell (3.2 m) away in a random direction: **move a car**. | 206 |
| spoof – points (`spoof_pts`) | Raw points | Copy the attacker's LiDAR points of a real car to a random empty spot, then encode honestly: a fake car **at the sensor level**, before the network. | 563 |
| spoof in receiver-blind area (`spoof_blind`) | Feature map | Like `spoof_feat`, but the fake car is placed where the **receiver has fewer than 3 LiDAR rays** (it cannot check). A visibility-aware attacker that targets the method's known blind spot. Reported separately, not in the primary mean. | 1,412 |

**Group 2: optimized white-box attacks (PGD), secondary** (D-65..D-68, D-70)
- The attacker knows the model weights, the receiver's features, fusion and heads. It perturbs only its own features, at all 3 fusion scales.
- Budget: L∞ per scale, ε_k = r × σ_k, where σ_k is the standard deviation of clean sender features on block H; r ∈ {0.25, 0.5, 1.0}. 10 steps, step ε/4, random start. No ground truth: the target is the clean fused output.
- **Untargeted**: degrade everything (scores and box regression). **Remove**: suppress all currently detected cars.
- **Stealth** versions add a constraint so the feature magnitude stays below 95% of B-NORM's threshold. In other words, they are adaptive to the B-NORM baseline (not to R1 or B-RAY).
- Levels on test: plain untargeted r = 0.25 and remove r = 0.25; stealth untargeted r = 0.5 and remove r = 0.25 (each the smallest r with ≥ 2 AP points of loss on block H, by a rule fixed in advance); plus both stealth families at r = 1.0† (added after block-H results, D-70).

**Total conditions: 12** = clean + 5 hand-crafted + 6 PGD.

**Benign stresses** (pose and latency noise at V2X-ViT's standard levels) were checked only on a development slice (0 B-RAY drops, D-63); they are not part of the final test.

---

## Part C. Questions evaluators are likely to ask, with honest answers

### C1. Novelty and positioning

**Q: Ray-based free-space checks already exist (CARLO, Shadow-Catcher, CAD). What is new?**
A: We claim no novelty for the ray check; B-RAY is exactly that idea and is framed as "applying a known check to intermediate-fusion CP on OPV2V". The candidate contributions are: (1) the unit (sender × tile × time) with explicit UNKNOWN, rather than a per-sender or per-box decision; (2) the exact counterfactual "with vs without this sender in this tile", which is cheap and exact for AttFuse because its fusion is per-pixel (verified on 93/93 locality tests); (3) a pre-registered, one-time evaluation with both AP definitions, scenario-level statistics, adaptive attacks and a receiver-blind attack. Novelty statements are "to our knowledge" (D-34) and the search should be rechecked before submission.

**Q: How does this compare with LUCIA, PoseGuard, MADE, TrustReflect?**
A: Not compared experimentally; they were positioned in the literature matrix only (`literature/comparison_matrix.csv`). A reviewer may count this as a gap. B-NORM is the only learned-free feature-statistics stand-in.

### C2. Results and claims

**Q: Your own method is not the primary. Isn't that a failure?**
A: It is the honest result of a rule fixed before the comparison (D-57). The supportable claims are: B-RAY passes narrowly; R1 adds clear value on removal attacks; whether R1 beats B-RAY overall depends on the AP definition.

**Q: Why do the two AP definitions disagree?**
A: Frame-order AP does not sort detections globally, so the order in which frames are concatenated affects the precision–recall curve. Removing low-confidence boxes in some frames changes ranking differently under the two schemes. We found this during the pre-final audit (D-60) and, before the test, committed to reporting both (D-64). The disagreement itself is a finding for the field: defense comparisons on OPV2V can flip with the AP implementation.

**Q: Are gains of 0.15–0.76 AP points meaningful?**
A: They are statistically detectable but small, mostly because the attacks themselves cost little over all frames (0.27–1.97 points). On frames where the attack actually changed the output, losses are larger (e.g. shift 8.03 points global) and R1 recovers 25–51% of them. The big effect is the strong removal attack (+22.5 points).

**Q: Why did results shrink from development (block H) to test?**
A: B-RAY frame-order gain fell from +2.79 (H) to +0.76 (test). H had only 2-car frames; on the test the 2-car stratum gives +1.80 and larger groups less (`tables/10_by_agents.csv`, descriptive). Selection on H (winner's curse) likely contributes too.

### C3. Data, leakage and test exposure

**Q: Can ground truth leak into the defense?**
A: The decision code ([`r1.py`](../src/mint/reliability/r1.py), [`baselines.py`](../src/mint/reliability/baselines.py), `bnorm.py`) takes no ground-truth argument and never references it (checked by search, 2026-10-27; the typed `ReceiverFrame` boundary from the methodology spec §4 was not implemented as such, so this is a code-reading check, not an enforced one). R1 and B-RAY use only the fused outputs, the counterfactual outputs and the receiver's own point cloud. Ground truth is used only for (a) scoring AP, (b) labelling harm in diagnostics and (c) the attacker's target choice.

**Q: Was the test set touched before the final run?**
A: Only at detector level: clean AttFuse AP was computed on all 16 test scenarios in Stage 1 to verify the checkpoint (V-01), and one scenario whose AP was inspected was moved out (15 remain). No MINT, baseline or attack number was computed on the test before the one-time run. The exposure ledger records every touch.

**Q: Was anything changed after the test started?**
A: One stream bug fix (D-71): a crash on an infeasible stealth frame, before any result was written. No method, attack, seed or analysis changed; what was seen before the fix is logged. All frozen files are checked by SHA-256 before and after the run.

**Q: What was decided after seeing data (post hoc)?**
A: Labelled in the log: the stealth PGD families (designed on H after plain PGD results, D-68), the r = 1.0 stealth levels (D-70), dropping the 10% latency budget as a pass/fail claim (D-50), and two corrections of a numerical tolerance (D-46, D-48). None was changed after the test.

### C4. Threat model realism

**Q: The attacker is always sender 1 and there is only one. Realistic?**
A: It is a stated scope limit. Colluding attackers are not tested. R1 does not use other senders as evidence, so collusion would not fool its ray check directly, but it would make the counterfactual "remove one sender" less informative.

**Q: Are the attacks adaptive against R1?**
A: Partly. `spoof_blind` targets R1's known blind spot, and it succeeds: neither R1 nor B-RAY recovers it (realized-only recovery ≤ 0.04). The PGD attacks are white-box against the detector and the stealth ones are adaptive to B-NORM, but **no attack was optimized against R1's own ray rule** (e.g. ray-consistent spoofs placed behind real occluders). That is the most likely reviewer objection.

**Q: Feature-level attacks are digital. Can a real attacker do this?**
A: A compromised car controls what it transmits, so feature editing is realistic for a malicious sender. Physical laser spoofing is out of scope. `spoof_pts` covers the point-level case.

**Q: Are PGD budgets realistic?**
A: They are relative to this model's own feature scale (σ_k on clean H), because literature budgets were 14–105× the feature scale and trivially caught by a norm check (D-66).

### C5. Generalization

**Q: Simulation only?**
A: Yes: OPV2V is CARLA. No real-sensor result exists. Culver City (in progress) is an unseen town but still simulated. Real data (V2V4Real, Mixed Signals) was planned but blocked by hardware (no GPU to train a detector; no released checkpoint for Mixed Signals).

**Q: One detector only?**
A: Yes, AttFuse. R1's exactness relies on per-pixel attentive fusion; for models with spatial mixing after fusion (V2X-ViT, CoBEVT) the counterfactual is no longer tile-local and would need re-verification.

### C6. Cost and deployment

**Q: Is it real-time?**
A: Not as implemented. Dense R1 adds 20% (n = 2) to 123% (n ≥ 4) at p50 on an M1 CPU, because it decodes once per sender. A cheaper tile trigger exists but is not exact (D-49), so no accuracy number uses it. On a GPU the absolute times would differ; not measured.

**Q: What does R1 cost on clean traffic?**
A: Under frame-order AP 0.62% relative loss (CI up to 1.75%); it switches off 521 useful contributions on clean frames. The ablation R1-noREMOVE shows most of the clean cost comes from REMOVE verdicts.

### C7. Methodology and statistics

**Q: Why a scenario bootstrap, and why Holm?**
A: Frames within a scenario are dependent, so resampling scenarios is the honest unit (15 clusters, so CIs are wide). Holm controls family-wise error for the two co-tests (B-RAY and R1 vs no defense).

**Q: Why was the original "calibrated probability" estimand dropped?**
A: Calibration needed a separate calibration block; the 4 small validate scenarios planned for it became the held-out block H instead (D-52), and R1's Wilson margin is labelled a resolvability margin, not a probability (D-40). The charter's hypotheses H1 (AUROC vs baselines), H3 (honest unique views) and the calibration claims were therefore not tested as originally stated. An evaluator comparing the charter with the paper will notice this; it should be stated as a scope change.

**Q: What is the oracle upper bound?**
A: On development, a visibility-limited oracle (perfect decisions, but only where the receiver can see) recovers about a third of the attack loss (0.326 mean on T, D-36), and only 36–55% of the attacker's harmful tiles are receiver-observable. That bounds any receiver-ray defense.

### C8. Questions with no good answer yet (be ready to say so)

- No comparison with learned defenses (LUCIA, PoseGuard, MADE).
- No attack optimized against R1 itself.
- No real-sensor data; one detector; one attacker.
- R1's advantage over B-RAY is AP-definition-dependent.
- Compute is above the original budget.
