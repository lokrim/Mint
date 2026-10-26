# DRAFT: interpretation of the E5 final test (for the authors)

> **DRAFT for the authors. Not part of `report.md`. Nothing here is confirmed wording for the paper.**
> Source: `runs/20261024-E5v3/report/report.md` (Status: FINAL TEST (one-time)), its `tables/*.csv`, and, for development numbers only, the frozen preregistrations `runs/20261024-E5/preregistration_v2.json` and `preregistration_v3_2.json`.
> Every number below is copied from those files, not recomputed. AP numbers are in AP points (×100) unless marked as %. Headline AP is global-ranking AP (D-64); frame-order AP is the OPV2V-comparable one.

How to read this draft: each answer is split into three kinds of numbers, kept apart.

- **Confirmatory**: the D-64 verdict, the v2 success rule, and the R1 − B-RAY statements. These are the only numbers that support a claim.
- **Descriptive**: PGD conditions, B-NORM, realized-only, by agent count, and the box/unit breakdowns. These are reported and not judged.
- **Development**: blocks T and H. They are labelled as such, and none of them is a test result.

---

## Q1. Does the pre-registered verdict hold under both AP definitions, and how large is the headline effect?

**Confirmatory.**

- **Verdict: success under both AP definitions** (report §3). The v2 rule passes under global-ranking AP and under frame-order AP.
- Pre-registered success rule (D-64, quoted): "The v2 success rule (B-RAY Holm-rejected in the co-test with R1 vs no defense on the scenario bootstrap, and B-RAY clean relative loss scenario-CI high <= 1%) is evaluated separately per AP definition, Holm within each definition. A success/robustness claim requires a pass under BOTH."
- **Headline, global-ranking AP.** B-RAY mean ΔAP@0.7 over the 4 original attacks is **+0.15**.
  - 95% CI, scenario bootstrap: [−0.01, +0.30]. 95% CI, 10-frame bootstrap: [+0.06, +0.22].
  - One-sided p = 0.0335. Holm-rejected, because R1's p = 0.0005 was the smaller p and was rejected at 0.025, so B-RAY is tested at 0.05.
- **Frame-order AP.** B-RAY **+0.76**, scenario CI [+0.49, +1.27], p = 0.0005, Holm-rejected.
- **Wording point for the authors.** Under the headline AP, the two-sided 95% scenario CI includes 0, while the pre-registered one-sided Holm test rejects. These two facts are consistent: p falls between 0.025 and 0.05. The paper should state both and not describe the CI as excluding zero.
- **Size.** The headline effect is small in absolute terms. No-defense AP@0.7 is 0.8668 to 0.8837 across the four original attacks (Appendix, global). The all-frame attack losses these attacks cause are themselves small: spoof-feature 1.52, remove-feature 1.01, shift-feature 1.97, spoof-points 0.27 AP points (global; `tables/07_attack_strength.csv`).

## Q2. Is the clean cost within the 1% limit, and what does B-RAY remove that it should not?

**Confirmatory: B-RAY's clean-cost criterion.**

- B-RAY's clean relative AP@0.7 loss passes the ≤ 1% limit under both definitions:
  - **Global:** 0.13%, scenario CI [+0.01, +0.30]%.
  - **Frame-order:** −0.05%, scenario CI [−0.30, +0.18]%.
- Under global-ranking AP the CI lies entirely above 0. B-RAY therefore has a small but detectable clean cost there: clean ΔAP −0.11 [−0.26, −0.01].

**Descriptive** (report §10, `tables/08_bray_boxes.csv`):

- **On clean frames**, B-RAY removes 148 of 31106 boxes:
  - 105 match no ground-truth car (removed as intended);
  - **43 match a real car** (the cost).
- **Under every attack condition**, B-RAY removes 37 to 48 GT-matched boxes. The exception is PGD remove stealth r=1.0 †, with 10. So the real-car removals look like a stable clean-scene cost, not a reaction to the attacks.
- **Under remove - feature**, B-RAY's ΔAP is negative under global AP: −0.11 [−0.27, −0.00]. This is consistent with the pre-registered scope limit "B-RAY cannot restore removed objects".

**Descriptive: R1's clean cost (R1 has no success criterion).**

- **Global:** −0.16%, scenario CI [−0.35, −0.01]%.
- **Frame-order:** 0.62%, scenario CI [+0.18, +1.75]%. The upper end of this CI is above 1%.
- On clean frames, R1 switches off 718 contributions. Of these, 521 are useful contributions (cost) and 190 are harmful ones, a precision of 0.27 (`tables/09_r1_units.csv`).

## Q3. Does R1 add anything over B-RAY?

**Confirmatory: key secondary.** The pre-registered rule (v2 key_secondary, quoted) is: "statement chosen by the scenario CI (e5_analyze.paired_statement): includes 0 -> 'the counterfactual's benefit over a box-level filter is not established'; entirely < 0 -> 'the counterfactual performs worse than the box-level filter'; entirely > 0 -> 'the counterfactual improves over the box-level filter'".

| AP definition | R1 − B-RAY | 95% CI scen. | Statement emitted by the frozen analysis |
|---|---|---|---|
| global-ranking AP (headline) | +0.31 | [+0.12, +0.55] | “the counterfactual improves over the box-level filter” |
| frame-order AP (OPV2V-comparable) | −0.57 | [−1.64, −0.11] | “the counterfactual performs worse than the box-level filter” |

- **The key secondary is AP-definition-dependent.** D-64 requires the report to state this, and it does (§3).
- The two definitions do not merely differ in significance: their statements point in opposite directions. This is not a success/robustness claim for R1 under D-64. A paper sentence such as "R1 improves over B-RAY" without the qualifier would not be supported.
- R1's own Holm co-test result:
  - **Global:** +0.45, p = 0.0005, rejected.
  - **Frame-order:** +0.19, p = 0.2259, not rejected.

**Descriptive.**

- **PGD conditions** (Fig. 4b, not part of the key secondary). R1 − B-RAY is large only for PGD remove stealth r=1.0 †: R1 ΔAP +22.50 global and +20.94 frame-order. This is a D-70 strong-attack level, added after block-H results and "never used for a criterion".
- **R1-noREMOVE ablation** (mean of 4 original attacks): +0.26 global, +0.66 frame-order.

## Q4. Which attacks are not recovered by any method, and is that the expected identifiability limit?

All of this is **descriptive**; none of it is a criterion.

**Spoof in the receiver-blind area.**

- B-RAY ΔAP is −0.01 [−0.18, +0.14] (global) and +0.14 [−0.05, +0.41] (frame-order).
- Realized-only recovery: B-RAY 0.00 / 0.02, R1 0.04 / −0.06 (global / frame-order).
- R1's all-frame ΔAP has opposite signs under the two definitions: +0.19 [+0.05, +0.37] global, −0.34 [−1.04, −0.02] frame-order.
- No method recovers a meaningful fraction. This matches the pre-registered scope limits ("spoof_blind bypass"; D-69: "R1 cannot verify removals in receiver-blind regions"). The authors should decide whether to call it an identifiability limit. The data show non-recovery; they do not by themselves show impossibility.

**Stealth PGD and B-NORM.**

- B-NORM catches 0% of the attacker on all four stealth conditions and 100% on the two non-stealth PGD conditions (Fig. 6).
- The pre-stated expected outcome "B-NORM ≤ 5%" holds on every stealth condition.
- B-NORM lowers AP in every condition. On clean frames its false-flag rate is 17% (339/1947), and its clean relative loss is 6.92% (global) and 9.45% (frame-order).

**B-RAY on PGD.**

- Point recovery is below 0.10 under both definitions on 5 of 6 PGD conditions. The exception is PGD untargeted stealth r=1.0 †, where the frame-order recovery is 0.10 (B-RAY ΔAP +2.09 [+1.00, +3.70]).
- This matches the pre-stated expectation "B-RAY ≈ 0" except at that D-70 level.

**R1 on PGD remove.**

- At r=0.25, the expected outcome "R1 > 0 under both AP definitions" does **not** hold, for both the standard and the stealth attack. Global-AP recovery is 0.37, but frame-order recovery is −0.05 and −0.13.
- It holds only at the D-70 level r=1.0 †.

**Removal attacks in general.**

- Frame-order AP registers small all-frame losses for PGD remove: 1.26 at r=0.25 (scenario CI [−0.01, +2.45]) and 1.14 for stealth r=0.25.
- The corresponding global-AP losses are 3.25 and 3.06.

## Q5. How do the final-test numbers compare with the development numbers (blocks T and H)?

**Development numbers are labelled.** The preregistration's labelling reads (quoted): "Test numbers are the one-time final test. All E0-E5a numbers (blocks T and H) are development or held-out-but-exposed and are reported separately. v2 is the governing pre-registration." These numbers are **not** in `report.md`. They are copied from the frozen preregistrations and converted to AP points (×100) for comparison.

| Quantity (frame-order AP unless stated) | Block T: DEVELOPMENT, in-sample, 3 scen., 404 frames, n = 2–4 | Block H: DEVELOPMENT / quasi-held-out (exposed), n = 2, 371 frames | Final test, 15 scen., 2066 frames |
|---|---|---|---|
| B-RAY mean ΔAP@0.7, 4 original attacks | +0.49 | +2.79 (p = 0.0005) | +0.76 (p = 0.0005) |
| R1 mean ΔAP@0.7 | +0.52 | +2.23 (p = 0.055) | +0.19 (p = 0.2259) |
| R1 − B-RAY | +0.03 | −0.56 | −0.57 [−1.64, −0.11] |
| B-RAY clean relative loss | 0.01% | 0.09% [−0.13, 0.41] | −0.05% [−0.30, +0.18] |
| R1 − B-RAY, global-ranking AP (v3 on H) | — | +0.29 [+0.05, +0.57], “the counterfactual improves over the box-level filter” | +0.31 [+0.12, +0.55], same statement |
| R1 − B-RAY statement, frame-order (v3 on H) | — | “the counterfactual's benefit over a box-level filter is not established” | “the counterfactual performs worse than the box-level filter” |
| B-NORM flag rate on clean frames (descriptive) | — | 1.6% | 17% |

Descriptive reading for the authors to check:

- **B-RAY's effect on the test is smaller than on block H.** In frame-order AP, block H gave +2.79 and the test gives +0.76.
- **Block H covered n = 2 only.** On the test, the n = 2 stratum gives B-RAY +1.80, 10-frame CI [+1.54, +2.07]. The n = 3 stratum gives +0.65 and n ≥ 4 gives +0.39 (`tables/10_by_agents.csv`, 10-frame bootstrap, frame-order). Agent-count coverage may account for part of the gap. This is descriptive; strata were not a criterion.
- **The AP-definition dependence of R1 − B-RAY was already visible on block H.** Global-ranking AP gave “improves” and frame-order gave “not established”. It recurs on the test, with the frame-order side now “performs worse”.
- **B-NORM's clean false-flag rate rises from 1.6% on H to 17% on the test.** Its threshold was fitted on clean H, which is a pre-registered scope limit.

## Limits to state with the results

**Pre-registered scope limits** (v3.2 `scope_limits`, quoted): "D-54 and D-63 (single attacker; random placement for the E4 families; spoof_blind bypass; ray-consistent / low-ray spoofs; B-RAY cannot restore removed objects; receiver sensor trusted; CARLA LiDAR; method chosen on exposed H), plus: PGD is white-box on this checkpoint with budgets relative to its clean H feature scale; B-NORM's threshold is fitted on clean H"

**v2 `scope_limits_D54`, n-coverage** (quoted): "the held-out evidence before this test covered n = 2 only (block H), the test covers n = 1-5 with few n >= 4 frames from 2 scenarios"

**D-69 reporting scope limit** (quoted): "R1 cannot verify removals in receiver-blind regions (a removed object the receiver cannot see is UNKNOWN = keep)"

**D-70.** The two r=1.0 † stealth conditions were "added after seeing block-H development results (D-70, secondary; never used for a criterion)".

**D-71, the stream bug fix.**

- The preregistration describes the fix as a "stream bug fix; NO change to any method, attack, level, seed, condition, criterion, the primary or the analysis code".
- The first v3.1 attempt crashed with KeyError 'mabs' on frame 1-3 of the first scenario. It wrote no results.
- Seen before the fix (quoted): "the frame-0 timing line of 2021_08_18_19_48_05 (6.4 s + 22.8 s) and the fact that >= 1 stealth condition was infeasible on >= 1 of its frames 1-3 (condition and count unknown); no AP, loss, flag or recovery value".
- Procedural checks passed: completeness 15/15 scenarios and 2066/2066 frames; frame-order v3 equals the frozen v2 analysis; NumPy AP equals OpenCOOD AP (max diff 1.9e-13).

## Attribution (paper_plan.md rules)

- **No novelty claim for ray support/traversal checks.** B-RAY is a receiver-only free-space check. Ray ratios are prior work: CARLO FSD/LPD [`sun2020carlo`], the Shadow test [`hau2021shadowcatcher`], and free-space conflict rules [`zhang2024cad`].
- The B-RAY result should be framed as an evaluation of applying a known check to intermediate-fusion CP on OPV2V.
- Contribution claims stay within "the estimand and unit, the label bridge, the evaluation, and possibly efficiency".
- Any claim about R1 must carry the AP-definition-dependence stated in Q3.
