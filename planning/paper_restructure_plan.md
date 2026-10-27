# Paper restructure plan: claim-centred `paper/main.tex` (FOR REVIEW)

> **Status: proposal only. `paper/main.tex` is not edited.** Written 2026-10-27.
> Every number below is copied from a result file or from `paper/numbers.tex` (macro named next to it). Nothing is
> recomputed. AP numbers are AP points (AP@0.7 × 100) unless marked %. JSON values are fractions; the only
> transformation anywhere in this plan is × 100 to AP points, as `gen_numbers.py` already does.

Sources read: `paper/README.md`, `paper/main.tex`, `paper/numbers.tex`, `paper/tables/*.tex`,
`runs/20261024-E5v3/report/report.md` (+ `tables/*.csv`), `runs/20261026-CULVER/report/report.md` §1–§14 (+ `tables/*.csv`),
`planning/final_report_interpretation_DRAFT.md`, `planning/decision_log_proposed_appendix.md` (D-55..D-73),
`planning/claim_evidence_ledger.csv`, `planning/project_qa_for_reviewers.md`, `paper/figures/r1_method_notes.md`.

Abbreviations used below:

- **T** = `runs/20261024-E5v3/e5_v3.json` (OPV2V test, primary, one-time; 15 scenarios, 2,066 frames).
- **C** = `runs/20261026-CULVER/e5_v3.json` (Culver City: **unseen town, simulated sensor**; secondary; 4 scenarios, 550 frames).
- **T-test / C-test** = the matching `e5_test.json` files (timing, units).
- **G** = global-ranking AP (headline, D-64). **F** = frame-order AP (OpenCOOD default).
- `<ap>` in a key stands for `global` or `frame`.
- Labels: **confirmatory** (the D-64 verdict, the v2 rule, the Holm co-test, the R1 − B-RAY statement, all on the test only);
  **descriptive** (everything else reported and not judged, including every Culver number); **development** (blocks T and H);
  **post hoc †** (chosen after seeing development results: D-70 strong levels; D-50 budget change).

---

## 0. Problems found in the current draft (need your decision; the plan below assumes the fixes shown)

| # | Current text (`main.tex`) | Problem, from the files | Fix used in this plan |
|---|---|---|---|
| P1 | User brief: "R1 positive in all 12 conditions under global AP on both sets" | On the test, R1's scenario CI is above zero in all 12 (T `tables.global.per_family.<c>.R1.ci95_scenario`). On Culver, the **point estimate** is positive in all 12, but the CI includes zero for **clean** (+0.13 [−0.02, +0.29]) and **receiver-blind spoof** (+0.14 [−0.01, +0.29]) (Culver report §5). | Claim C6 states the two sets differently and names the two conditions (no count is computed). |
| P2 | l. 47, 103, 804: R1 is "the only one that recovers removal attacks" | At the strong level†, ego-only also gains (test \dGlobPgdRemStStrongEgo = +19.19; Culver +20.44 [+12.09, +36.44]) and R1-noREMOVE has a CI above zero (test +0.07 [+0.01, +0.14]; Culver +0.09 [+0.04, +0.17]). | Claim C4: "the only defense whose scenario CI is above zero on all four removal conditions under G, on both sets". |
| P3 | l. 740, 805: "No defense recovers the receiver-blind spoof" / "no receiver-ray method helped" | On the test, R1's all-frame G gain on spoof_blind is +0.19 [+0.05, +0.37] (CI above zero). What holds is the **recovery** bound. | Claim C7 defines "unrecovered" as recovery ≤ 0.10 (all-frame) and ≤ 0.06 (realized-only), both sets, both AP definitions. |
| P4 | l. 49, 104: "Free-space filtering … fail[s] against optimized and stealthy attacks" | B-RAY's F gains on untargeted PGD have CIs above zero on both sets (test +0.83, +0.58, +2.09†; Culver +1.80, +0.95, +3.14†). | Claim C9: state recovery (≤ 0.10 test, ≤ 0.13 Culver) and "no gain on PGD removal", not "fails". |
| P5 | l. 51, 378, 745: "simulated, real-city layout"; l. 148: V2V4Real/Mixed Signals "provide real data" | The word "real" outside a limitation. | Use "unseen town, simulated sensor" everywhere; the layout sentence appears once, in §V-A; the real-sensor datasets move to Limitations/Future work. |
| P6 | Title: "… for Robust Cooperative LiDAR Perception" | D-64's success/robustness verdict belongs to B-RAY, not R1; on Culver the D-64 status is "AP-definition-dependent". | Drop "Robust" (§4 below). |
| P7 | — | Culver `report/tables/10_by_agents.csv` lists n = 3 with **1** scenario; Culver report header says "per-agent-count strata have 2 scenarios each". | Not used in the main text (agent-count strata go to the appendix); please check before the appendix cites it. |
| P8 | — | `planning/project_qa_for_reviewers.md` B2 and C5 still say Culver is "in progress" / "no results exist yet". | Not changed here (file not in scope); update before it is shared. |
| P9 | — | Culver runtime overhead is higher than the test's at the same n (dense n = 2: 45.8% vs 20.2% p50; B-RAY 20.2% vs 3.5%). Nothing in the files explains it. | Claim C11 reports both, with no explanation. |

---

## 1. Claims table

Each claim has a test row (primary) and a Culver row (secondary). The two are **never pooled**. "Allowed wording" is the
exact sentence the paper may use; numbers in it are macros (existing unless marked *new*). A *new* macro is a copy of the
listed JSON/CSV key by `gen_numbers.py`, not a new computation.

### C1. B-RAY (pre-registered primary) passes, narrowly under global-ranking AP; on Culver not significant under G

| Set | AP | Evidence | Source key | Label |
|---|---|---|---|---|
| Test | G | Mean ΔAP, 4 original attacks: **+0.15** [−0.01, +0.30]; one-sided p = 0.0335, Holm thr. 0.050, reject; clean rel. loss CI [+0.01, +0.30]%; v2 rule **passes** | T `criteria_v3.global.co_test_vs_no_defense.B-RAY.{point,ci95_scenario,p_one_sided,holm}`, `criteria_v3.global.{clean_rel_loss.B-RAY,B-RAY_clean_ci_hi_le_0.01,pass}`; macros \VGlobBRAYDelta, \VGlobBRAYCI, \VGlobBRAYP, \VGlobBRAYHolmThr, \VGlobBRAYCleanCI, \VGlobPass | confirmatory |
| Test | F | **+0.76** [+0.49, +1.27]; p = 0.0005, thr. 0.025, reject; clean CI [−0.30, +0.18]%; v2 rule **passes** | T `criteria_v3.frame.…` (same keys); \VFrameBRAYDelta, \VFrameBRAYCI, \VFrameBRAYP | confirmatory |
| Test | both | D-64 verdict: "success under both AP definitions" | T `criteria_v3.D-64.verdict` | confirmatory |
| Culver | G | **+0.05** [−0.03, +0.13]; p = 0.1209, **not rejected**; v2 rule **does not pass** | C `criteria_v3.global.…`; \CulHeadGlobBRAY, \CulHeadGlobBRAYCI, \CulVGlobBRAYP, \CulVGlobPass | descriptive |
| Culver | F | **+0.54** [+0.22, +0.92]; p = 0.0005, rejected; v2 rule passes | C `criteria_v3.frame.…`; \CulHeadFrameBRAY, \CulHeadFrameBRAYCI, \CulVFrameBRAYP, \CulVFramePass | descriptive |
| Culver | both | D-64 status: "AP-definition-dependent" | C `criteria_v3.D-64.verdict` | descriptive |

**Allowed wording.** "On the OPV2V test, the pre-registered primary B-RAY passes its success rule under both AP definitions.
Under global-ranking AP the pass is narrow: \VGlobBRAYDelta\pts{}, one-sided $p=\VGlobBRAYP$ (Holm threshold
\VGlobBRAYHolmThr), while the two-sided 95\% scenario CI \VGlobBRAYCI{} includes zero. On the unseen town (simulated
sensor), the same rule, applied descriptively, does not pass under global-ranking AP (\CulHeadGlobBRAY\pts{}
\CulHeadGlobBRAYCI, $p=\CulVGlobBRAYP$) and passes under frame-order AP (\CulHeadFrameBRAY\pts{} \CulHeadFrameBRAYCI)."

**Not allowed.** "B-RAY's CI excludes zero" (G); "Culver confirms / replicates the verdict"; "B-RAY is robust"; any pooled
test+Culver estimate; reading the Culver non-rejection as a failure of the test result (D-73).

### C2. R1 in the Holm co-test against no defense

| Set | AP | Evidence | Source key | Label |
|---|---|---|---|---|
| Test | G | **+0.45** [+0.29, +0.70]; p = 0.0005, thr. 0.025, reject | T `criteria_v3.global.co_test_vs_no_defense.R1.*`; \VGlobRONEDelta, \VGlobRONECI, \VGlobRONEP | confirmatory |
| Test | F | **+0.19** [−0.45, +0.52]; p = 0.2259, **not rejected** | T `criteria_v3.frame.co_test_vs_no_defense.R1.*`; \VFrameRONEDelta, \VFrameRONECI, \VFrameRONEP | confirmatory |
| Culver | G | **+0.32** [+0.21, +0.48]; p = 0.0005, reject | C same keys; \CulHeadGlobRONE, \CulHeadGlobRONECI, \CulVGlobRONEP | descriptive |
| Culver | F | **+0.40** [+0.21, +0.73]; p = 0.0005, reject | C same keys; \CulHeadFrameRONE, \CulHeadFrameRONECI, \CulVFrameRONEP | descriptive |

**Allowed wording.** "R1, co-tested as the key secondary, gains \VGlobRONEDelta\pts{} \VGlobRONECI{} under global-ranking AP
(rejected) and \VFrameRONEDelta\pts{} \VFrameRONECI{} under frame-order AP (not rejected) on the test; on the unseen town it
is rejected under both (\CulHeadGlobRONE{} and \CulHeadFrameRONE\pts)."

**Not allowed.** "R1 passes the success rule" (R1 has no success rule); "R1 is significant under both AP definitions" (false on the test).

### C3. R1 − B-RAY reverses with the AP definition

| Set | AP | Evidence | Source key | Label |
|---|---|---|---|---|
| Test | G | **+0.31** [+0.12, +0.55]: "the counterfactual improves over the box-level filter" | T `tables.global.R1_minus_BRAY.mean_of_4.{point,ci95_scenario}`, `criteria_v3.global.R1_minus_BRAY.statement`; \VGlobRmB, \VGlobRmBCI, \VGlobRmBStatement | confirmatory (key secondary) |
| Test | F | **−0.57** [−1.64, −0.11]: "the counterfactual performs worse than the box-level filter" | T `tables.frame.R1_minus_BRAY.mean_of_4.*`; \VFrameRmB, \VFrameRmBCI, \VFrameRmBStatement | confirmatory (key secondary) |
| Test | — | `R1_minus_BRAY_AP_definition_dependent` = true | T `criteria_v3.D-64.R1_minus_BRAY_AP_definition_dependent` | confirmatory |
| Culver | G | **+0.27** [+0.12, +0.48]: "improves" | C same keys; \CulVGlobRmB, \CulVGlobRmBCI | descriptive |
| Culver | F | **−0.14** [−0.40, +0.19]: "the counterfactual's benefit over a box-level filter is not established" | C same keys; \CulVFrameRmB, \CulVFrameRmBCI, \CulVFrameRmBStatement | descriptive |
| Dev H | G / F | +0.29 [+0.05, +0.57] / −0.56 [−1.73, +0.32] | `paper/tables/tab_dev_vs_test.tex` (from `runs/20261024-AUDIT/X0_global_sort_bootstrap.json`); \DevHFrameRmB | development (appendix only) |
| Test | G vs F | Spoof (feature) attack loss: \LossGlobSpoofFeat = 1.52 (G) vs \LossFrameSpoofFeat = 3.57 (F) | T `point.<ap>.attack_loss|spoof_feat` | descriptive (supports the definitional explanation) |

**Allowed wording.** "Whether R1 improves on B-RAY depends on the AP definition. On the test, R1 − B-RAY is \VGlobRmB\pts{}
\VGlobRmBCI{} under global-ranking AP (pre-registered statement: ``\VGlobRmBStatement'') and \VFrameRmB\pts{} \VFrameRmBCI{}
under frame-order AP (``\VFrameRmBStatement''). On the unseen town, the global-ranking statement is the same
(\CulVGlobRmB\pts{} \CulVGlobRmBCI); the frame-order difference has the same sign but is not resolved (\CulVFrameRmB\pts{}
\CulVFrameRmBCI)." Explanation sentence (definitional, allowed): "The two definitions differ in where a low-score false
positive is charged: at the tail of the global ranking, or at its frame's position in the frame-order accumulation."
Permitted link: "consistent with this, the same spoof costs \LossFrameSpoofFeat{} vs.\ \LossGlobSpoofFeat\pts."

**Not allowed.** "R1 beats B-RAY" without the AP qualifier; "the flip replicates on Culver" (frame-order side not resolved);
"we show that frame-order AP is wrong" (not tested); a causal mechanism stated as a result.

### C4. R1 recovers removal attacks

| Condition | Test G ΔAP [CI] | Test F | Culver G | Culver F | Label |
|---|---|---|---|---|---|
| remove (feature) | **+0.27** [+0.10, +0.56] | −0.38 [−1.31, +0.05] | **+0.23** [+0.12, +0.40] | +0.04 [−0.10, +0.28] | descriptive |
| PGD remove, r = 0.25 | **+1.22** [+0.61, +2.15] | −0.07 [−1.34, +0.84] | **+0.97** [+0.73, +1.42] | **+0.40** [+0.24, +0.92] | descriptive |
| stealth PGD remove, r = 0.25 | **+1.13** [+0.55, +1.99] | −0.14 [−1.40, +0.73] | **+0.96** [+0.70, +1.41] | **+0.41** [+0.25, +0.98] | descriptive (family designed on dev H after plain PGD, D-68) |
| stealth PGD remove, r = 1.0† | **+22.50** [+18.41, +27.48] | **+20.94** [+16.96, +25.78] | **+19.53** [+14.78, +31.02] | **+17.93** [+13.52, +29.19] | post hoc † (D-70) |
| Attack loss at r = 1.0† | 40.41 | 36.51 | 39.82 | 36.90 | post hoc † |
| R1 recovery at r = 1.0† | 0.56 | 0.57 | 0.49 | 0.49 | post hoc † |
| B-RAY at r = 1.0† (G ΔAP) | −0.01 | +0.06 | −0.03 | +0.02 | post hoc † |
| Ego-only at r = 1.0† (G ΔAP) | +19.19 [+14.29, +25.04] | +9.99 | +20.44 [+12.09, +36.44] | +14.24 | post hoc † |

Sources: T/C `tables.<ap>.per_family.{remove_feat, pgd_remove@r0.25, pgd_remove_stealth@r0.25, pgd_remove_stealth@r1.0}.{R1,B-RAY,ego_only}.{point,ci95_scenario,recovery}`;
`point.<ap>.attack_loss|pgd_remove_stealth@r1.0`. Macros: \dGlobRemoveFeatRONE, \ciGlobRemoveFeatRONE, \dGlobPgdRemRONE,
\dGlobPgdRemStRONE, \dGlobPgdRemStStrongRONE, \ciGlobPgdRemStStrongRONE, \dFramePgdRemStStrongRONE, \LossGlobPgdRemStStrong,
\RecGlobPgdRemStStrongRONE; \CulDGlobRemoveFeatRONE, \CulDGlobPgdRemRONE, \CulDGlobPgdRemStRONE, \CulDGlobPgdRemStStrongRONE,
\CulLossGlobPgdRemStStrong, \CulRecGlobPgdRemStStrongRONE, \CulDFramePgdRem(St)(Strong)RONE; Culver CIs *new* (\CulCiGlob…RONE, \CulCiFrame…RONE).

**C4b (ablation).** R1-noREMOVE at r = 1.0†: +0.07 (test G), +0.09 (Culver G); on remove (feature): −0.01 / −0.07.
Source: T/C `tables.global.per_family.<c>.R1_noREMOVE`; \dGlobPgdRemStStrongRNoRem, \CulDGlobRemoveFeatRNoRem. Descriptive.

**Allowed wording.** "Under global-ranking AP, R1 is the only defense whose scenario CI lies above zero on all four removal
conditions, on the test and on the unseen town. On the strongest stealth removal$^\dagger$ it restores
\dGlobPgdRemStStrongRONE{} of \LossGlobPgdRemStStrong\pts{} on the test (recovery \RecGlobPgdRemStStrongRONE; frame-order
\dFramePgdRemStStrongRONE) and \CulDGlobPgdRemStStrongRONE{} of \CulLossGlobPgdRemStStrong\pts{} on the unseen town (recovery
\CulRecGlobPgdRemStStrongRONE); at that level ego-only also gains (\dGlobPgdRemStStrongEgo{} and *new* \CulDGlobPgdRemStStrongEgo\pts),
because the attack costs more than cooperation is worth. Under frame-order AP, R1's removal gain is resolved only at the strong
level$^\dagger$ on the test, and on the two PGD removals at $r=0.25$ and the strong level on the unseen town. Without REMOVE
verdicts (R1-noREMOVE) the strong-level gain is \dGlobPgdRemStStrongRNoRem\pts, so the REMOVE test carries the recovery."

**Not allowed.** "the only defense that recovers removals" (P2); any strong-level† number used for a criterion or in the
abstract without †; "R1 recovers removals under both AP definitions" at r = 0.25 on the test.

### C5. (folded into C4b: REMOVE test carries removal recovery)

### C6. R1 is positive in all 12 conditions under global-ranking AP

| Set | AP | Evidence | Source key | Label |
|---|---|---|---|---|
| Test | G | Scenario CI above zero in **all 12** conditions (incl. clean, +0.14 [+0.01, +0.31], and 2 † levels); no other defense does this | T `tables.global.per_family.<c>.<m>.ci95_scenario` for all 12 `<c>`; `paper/tables/tab_main_global.tex` (bold column) | descriptive (2 conditions †) |
| Test | F | Not so: clean −0.51 [−1.44, −0.15]; spoof_blind −0.34 [−1.04, −0.02]; CIs include zero on most attacks | T `tables.frame.per_family.*.R1`; \dFrameCleanRONE, \ciFrameCleanRONE | descriptive |
| Culver | G | **Point estimate** positive in all 12; CI above zero in all but **clean** (+0.13 [−0.02, +0.29]) and **receiver-blind spoof** (+0.14 [−0.01, +0.29]) | C `tables.global.per_family.<c>.R1.{point,ci95_scenario}`; Culver report §5 | descriptive |
| Culver | F | Point estimate negative on clean (−0.04 [−0.26, +0.19]) | C `tables.frame.per_family.clean.R1` | descriptive |

**Allowed wording.** "Under global-ranking AP, R1 is the only defense whose scenario CI lies above zero in all
\NumConditions{} conditions of the test, clean frames included. On the unseen town its point estimate is positive in all
\NumConditions, and its CI lies above zero in all but two (clean frames and the receiver-blind spoof). Under frame-order AP
this does not hold on either set."

**Not allowed.** "R1 is positive in every condition" (no AP qualifier); "on both sets, R1's CI is above zero in all 12" (P1).

### C7. The receiver-blind spoof is not recovered

| Set | AP | All-frame loss; ΔAP B-RAY / R1 [CI]; all-frame recovery B-RAY / R1 | Realized-only recovery B-RAY / R1 | Label |
|---|---|---|---|---|
| Test | G | 2.21; −0.01 [−0.18, +0.14] / +0.19 [+0.05, +0.37]; −0.00 / 0.09 | 0.00 / 0.04 | descriptive |
| Test | F | 4.39; +0.14 [−0.05, +0.41] / −0.34 [−1.04, −0.02]; 0.03 / −0.08 | 0.02 / −0.06 | descriptive |
| Culver | G | 1.45; −0.07 [−0.14, −0.03] / +0.14 [−0.01, +0.29]; −0.05 / 0.10 | −0.03 / 0.06 | descriptive |
| Culver | F | 2.73; +0.07 [−0.04, +0.16] / +0.01 [−0.23, +0.20]; 0.03 / 0.00 | 0.03 / −0.00 | descriptive |

Placement facts (test): 1,412 realized, 1,381 landed where the receiver had < 3 rays (or on itself), 0 touched a KNOWN unit
(\RealizedSpoofBlind, \BlindRealizedLowRay, \BlindRealizedKnownHit; T `realization.spoof_blind.*`). Visibility-limited oracle
recovery bound 0.10 (F; \VisOracleRecSpoofBlind), unconstrained oracle 0.99 (\OracleRecSpoofBlind).
Sources: T/C `tables.<ap>.per_family.spoof_blind.*`, `realized_only.spoof_blind.<ap>.<m>.recovery`; Culver report §12
(all-frame recoveries); test/Culver report §9 (realized-only). Culver placement counts: C `realization.spoof_blind.*` (*new* macros).

**Allowed wording.** "No defense recovers more than 0.10 of the receiver-blind spoof's loss on either set under either AP
definition, and at most 0.06 on the frames where the spoof changed the output. On the test, \BlindRealizedLowRay{} of the
\RealizedSpoofBlind{} realized spoofs landed where the receiver had fewer than three rays, and \BlindRealizedKnownHit{} touched
a KNOWN unit; R1's global-ranking gain on this condition (\dGlobSpoofBlindRONE\pts) is of the same size as its gain on clean
frames (\dGlobCleanRONE\pts)."

**Not allowed.** "No defense helps" (P3); "provably unrecoverable" / "identifiability limit" stated as shown (the data show
non-recovery, not impossibility; interpretation draft Q4).

### C8. B-NORM is evaded by B-NORM-aware stealth PGD

| Quantity | Test | Culver | Source | Label |
|---|---|---|---|---|
| Catch rate, plain PGD (untargeted / remove, r = 0.25) | 100% / 100% | 100% / 100% | T/C `B-NORM_flags.<c>.catch_rate`; \CatchPgdUnt, \CatchPgdRem, \CulCatchPgdUnt, \CulCatchPgdRem | descriptive |
| Catch rate, all four stealth conditions | 0% | 0% | same; \CatchPgd{Unt,Rem}St(Strong), \CulCatchPgd… | descriptive; 2 levels † |
| False-flag rate on clean sender frames | 17.4% (339/1,947) | 18.4% | \CatchClean, \BnormFalseFlagN, \CulCatchClean | descriptive |
| Same, dev block H (threshold fitted here) | 1.6% | — | \BnormFalseFlagH | development |
| Clean rel. loss G / F | 6.92% / 9.45% | 8.77% / 9.30% | \CleanGlobBNORM, \CleanFrameBNORM, \CulCleanGlobBNORM, \CulCleanFrameBNORM | descriptive |
| Mean ΔAP, 4 original attacks G / F | −5.85 / −7.13 | −6.72 / −6.72 | `tables.<ap>.mean_of_4_orig.B-NORM` | descriptive |
| Stealth remove r = 0.25 attack loss G | 3.06 | 4.38 | \LossGlobPgdRemSt, \CulLossGlobPgdRemSt | descriptive |
| Stealth-infeasible frames (unt. 0.5 / rem. 0.25 / unt. 1.0† / rem. 1.0†) | 10 / 44 / 3 / 3 of 1,947 | 0 / 32 / 0 / 0 of 478 | `pgd_by_scenario.<c>.total.infeasible`; \Infeasible…, \CulInfeasible… | descriptive |

**Allowed wording.** "B-NORM flags the attacker on \CatchPgdUnt{} of plain PGD frames on both sets, and on \CatchPgdUntSt{} of
frames under every B-NORM-aware stealth condition, on both sets, while the stealth removal still costs \LossGlobPgdRemSt\pts{}
(test) and \CulLossGlobPgdRemSt\pts{} (unseen town). On clean frames B-NORM flags the benign sender on \CatchClean{} (test) and
\CulCatchClean{} (unseen town) of sender frames, against \BnormFalseFlagH{} on the development block where its threshold was fitted."

**Not allowed.** "feature-statistics defenses are broken" in general (only B-NORM was tested); "B-NORM is a fair stand-in for
Latent Guardian / learned defenses".

### C9. B-RAY on optimized attacks

| Quantity | Test | Culver | Label |
|---|---|---|---|
| Max point recovery on the 6 PGD conditions, G / F | 0.01 / 0.10 (strong untargeted†) | 0.01 / 0.13 (PGD untargeted r = 0.25) | descriptive |
| G ΔAP on PGD removals (r = 0.25, stealth 0.25, stealth 1.0†) | −0.10, −0.10, −0.01 | −0.12, −0.12, −0.03 | descriptive |
| F ΔAP on untargeted PGD (0.25, stealth 0.5, stealth 1.0†) | +0.83 [+0.40, +1.57], +0.58 [+0.16, +1.34], +2.09 [+1.00, +3.70] | +1.80 [+0.76, +3.17], +0.95 [+0.33, +1.41], +3.14 [+1.33, +4.25] | descriptive |
| Pre-stated expectation "B-RAY recovery < 0.10 under both AP definitions" | held in 5 of 6 (fails at strong untargeted†) | held in 4 of 6 (fails at PGD untargeted r = 0.25 and strong untargeted†) | descriptive |

Sources: T/C `tables.<ap>.per_family.pgd_*.B-RAY.{point,ci95_scenario,recovery}`, `expected_outcomes.<c>.<ap>`; report §8 both;
\RecGlobPgdUntStStrongBRAY, \RecFramePgdUntStStrongBRAY, \CulRecFramePgdUntBRAY, \CulRecFramePgdUntStStrongBRAY.

**Allowed wording.** "B-RAY recovers at most \RecFramePgdUntStStrongBRAY{} (test) and \CulRecFramePgdUntBRAY{} (unseen town) of
any PGD attack's loss, and gains nothing on PGD removal on either set; it can only delete boxes."

**Not allowed.** "B-RAY fails against PGD" (P4).

### C10. Clean cost

| Method | Test G rel. loss [CI] | Test F | Culver G | Culver F | Label |
|---|---|---|---|---|---|
| B-RAY | 0.13% [+0.01, +0.30] | −0.05% [−0.30, +0.18] | 0.14% [+0.08, +0.19] | −0.07% [−0.18, +0.07] | test: **confirmatory** (rule's ≤ 1% bound); Culver descriptive |
| R1 | −0.16% [−0.35, −0.01] | **0.62% [+0.18, +1.75]** | −0.17% [−0.35, +0.03] | 0.06% [−0.23, +0.37] | descriptive |
| R1-noREMOVE | 0.01% [−0.01, +0.03] | −0.03% [−0.10, −0.01] | 0.09% [+0.00, +0.27] | 0.02% [−0.09, +0.20] | descriptive |
| R1 clean ΔAP (pts) | +0.14 [+0.01, +0.31] | −0.51 [−1.44, −0.15] | +0.13 [−0.02, +0.29] | −0.04 [−0.26, +0.19] | descriptive |

What is removed on clean frames (descriptive):

| | Test | Culver | Source |
|---|---|---|---|
| B-RAY boxes dropped / boxes; GT-matched | 148 / 31,106; 43 | 79 / 20,973; 45 | T/C `B-RAY_boxes.clean.{drop,boxes,dropped_gt_matched}`; \BrayCleanDrop, \BrayCleanBoxes, \BrayCleanDropGT, \CulBrayCleanDrop, \CulBrayCleanBoxes, \CulBrayCleanDropGT |
| R1 units gated / units; USEFUL gated (false switch-offs); precision | 718 / 8,160; 521 (512 via REMOVE); 0.27 | 161 / 6,093; 34; 0.714 | test: \RoneClean…; Culver: `runs/20261026-CULVER/report/tables/09_r1_units.csv` row `clean` (*new* macros; REMOVE split for Culver: from C-test `units`, *new*) |
| R1-noREMOVE gated; USEFUL gated | 62; 10 | from Culver `09_r1_units.csv` (*new*) | \RNoRemCleanGated, \RNoRemCleanFalseSwitch |

**Allowed wording.** "B-RAY's clean relative loss stays inside the pre-registered 1\% bound under both AP definitions on the
test (\CleanGlobBRAY, \CleanFrameBRAY) and on the unseen town (\CulCleanGlobBRAY, \CulCleanFrameBRAY). R1's clean cost depends
on the AP definition: \CleanGlobRONE{} under global ranking and \CleanFrameRONE{} \CleanFrameRONECI{} under frame order on the
test, where it switches off \RoneCleanGated{} of \RoneCleanUnits{} units, \RoneCleanFalseSwitch{} of them useful
(\RoneCleanFalseSwitchRemove{} via REMOVE); on the unseen town the frame-order cost is \CulCleanFrameRONE{} \CulCleanFrameRONECI."

**Not allowed.** "R1 has no clean cost"; "R1's clean cost is within 1%" (test F CI reaches 1.75%); any explanation of why the
Culver frame-order cost is lower (not analysed).

### C11. Runtime

| n | Test: frames; base s; R1 dense p50/p95; T(0.05); B-RAY | Culver: frames; base s; dense; T(0.05); B-RAY |
|---|---|---|
| 1 | 119; 0.39; —; —; 8 / 14% | 72; 0.463; —; —; 21.0 / 31.2% |
| 2 | 866; 0.39; 20 / 46%; 10 / 34%; 4 / 11% | 355; 0.441; 45.8 / 81.2%; 41.8 / 83.5%; 20.2 / 32.4% |
| 3 | 869; 0.42; 53 / 102%; 40 / 93%; 9 / 20% | 123; 0.485; 105.4 / 171.7%; 98.5 / 165.2%; 27.2 / 38.9% |
| 4+ | 212; 0.52; 123 / 170%; 77 / 128%; 11 / 16% | — (Culver has n ≤ 3) |

Sources: T-test / C-test `overhead.by_stratum.<n>.<mode>.overhead.{p50,p95}`; `paper/tables/tab_runtime.tex`; Culver report §11.
Macros: \Ov…, \CulOvDenseTwoPfifty, \CulOvBrayTwoPfifty, \CulOvDenseThreePfifty, \CulOvBrayThreePfifty; Culver p95, T(0.05) and n = 1
are *new*. Machine: \TimingMachine (from `planning/e4_report.md`; README "could not verify": assumed same machine).
Label: descriptive. The 10% p95 budget was dropped as a pass/fail claim **post hoc** (D-50).

**Allowed wording.** "Dense R1's overhead over receiver-only perception grows with the number of cars: on the test
\OvDenseTwoPfifty, \OvDenseThreePfifty{} and \OvDenseFourPlusPfifty{} (p50) at $n=2$, 3 and $\ge 4$; on the unseen town
\CulOvDenseTwoPfifty{} and \CulOvDenseThreePfifty{} at $n=2$ and 3 (\TimingMachine). The cheaper trigger T(0.05) is a cost
variant only; no accuracy number uses it. The original 10\% p95 budget is not met by any R1 variant; we report cost and do not
judge it (a post hoc change, D-50)."

**Not allowed.** "real-time"; any GPU projection; an explanation of the test-vs-Culver timing difference (P9).

### C12. Detector and pipeline sanity (engineering facts, one sentence each)

| Fact | Evidence | Source | Label |
|---|---|---|---|
| Released checkpoint reproduces published test AP | 0.8155 vs 0.815 (16 test scenarios, frame order) | ledger C-06, `runs/20261023-S1-reproduce/summary.json` | engineering |
| NumPy AP = OpenCOOD AP | max abs. diff 1.9e-13 (test), 1.8e-13 (Culver) | report §2 both; \NumpyOpencoodDiff | engineering |
| Tile composition = direct masked decode | identical on 15/15 and 4/4 scenarios | T/C `scenario_files[].compose_all_identical`; report §2 | engineering |
| AttFuse post-fusion computation is pixel-local | 93/93 head outputs bit-identical outside tile | ledger C-05 | engineering |
| Culver clean AP | no-defense 77.46 (G) / 73.59 (F); published 73.5; first-scenario sanity 91.68 (F, 90 frames) | \CulAPCleanGlob, \CulAPCleanFrame, \CulPublishedAP, \CulSanityAP | descriptive (planned check) |
| Test clean AP | 88.64 (G) / 82.17 (F) | `tab_culver.tex` row 1 | descriptive |

### C13. Novelty (literature)

"To our knowledge, a tile-level, ray-verified counterfactual has not been evaluated before; the ray check itself is not new
\cite{sun2020carlo,zhang2024cad}." Label: literature, **provisional** (ledger C-02 PROVISIONAL, "must re-search"; C-01: no novelty
for the ray ratio). Must be re-checked before submission.

### C14. Development vs test (appendix only)

Values exactly as `paper/tables/tab_dev_vs_test.tex` (e.g. B-RAY F: H +2.79, test +0.76). Label: development. Allowed
wording: "Gains are smaller on the test than on the exposed development block H under both definitions; the sign pattern of
R1 − B-RAY is the same on H and on the test." Not allowed in the main text, the abstract or any claim of the contributions list.

### C15. Agent-count strata (appendix only)

Test frame-order 10-frame CIs: B-RAY \ByNTwoBRAY{} (n = 2) → \ByNFourPlusBRAY{} (n ≥ 4); R1 \ByNTwoRONE{} → \ByNFourPlusRONE{}
(\ByNFourPlusScen{} scenarios at n ≥ 4). Culver from `runs/20261026-CULVER/report/tables/10_by_agents.csv` (n = 2: B-RAY +0.77,
R1 +0.45; check P7 first). Label: descriptive.

---

## 2. Section outline (IEEEtran conference, 8 pages + references)

**Space estimate.** ~1,000 words per full text page. Floats in the main body (§3): ≈ 2.0 pages; equations ≈ 0.4; title block ≈ 0.35.
That leaves ≈ 5.2 text pages, so the body target is **≈ 4,700 words** (current draft ≈ 5,000 words with 8 figures and 9 tables,
README estimate 9–10 pages).

**Fixed pattern for every result.** One claim sentence (from §1), then "On the OPV2V test (primary) …", then "On the unseen
town (simulated sensor; secondary, \CulScenarios{} scenarios) …". Never a pooled number, never "both sets" averaged.

| § | Title | Words | Content | Claims |
|---|---|---|---|---|
| — | Abstract | 190 | §4 options | C1–C4, C7, C11 |
| I | Introduction | 520 | Problem; 3 defense families (one paragraph); R1 in one paragraph; evaluation design in 3 sentences (pre-registered one-time test; unseen-town secondary; two AP definitions); contributions (4 items, each = one claim ID) | C13, C1, C3, C4 |
| II | Related work | 380 | Attacks (90); consensus/counterfactual + anomaly defenses merged (150); free-space (80); evaluation practice: AP definitions, adaptive attacks (60) | C13 |
| III | Threat model | 230 | System, attacker, defender, goal (current text, tightened) | — |
| IV | Method | 700 | Counterfactual effects (eq. cf, effects); ray evidence (eq. s); Wilson gate (eq. wilson, gate); tile gating and composition (eq. unitgate, compose); baselines B-RAY, B-NORM, ego-only (eq. bray); GT harm labels (eq. harm, 2 sentences). One `figure*`: `figures/r1_method.tex` | C12 (composition) |
| V | Evaluation protocol | 600 | A. Two evaluation sets (Table I): test = primary one-time; Culver = secondary, unseen town, simulated sensor, planned before download (D-72), nothing fitted; never pooled; dev blocks named once. B. Attacks (Table II), PGD eq., stealth in one sentence (eq. → appendix). C. Metrics: ΔAP, recovery, clean loss, two AP definitions (eq. ap). D. Statistics: scenario bootstrap, p eq., Holm, v2 rule in 2 sentences. E. Labels: confirmatory / descriptive / † legend; one sentence pointing to Appendix A for the pre-registration history | C12 |
| VI-A | Pre-registered verdict | 270 | Table III (verdict, test vs Culver) + forest plot (Fig. 2) | C1, C2 |
| VI-B | Removal attacks | 250 | Table IV rows 3, 8, 10, 12 | C4, C4b |
| VI-C | All conditions | 170 | Table IV | C6 |
| VI-D | The AP-definition flip | 260 | Fig. 2 bottom row; definitional explanation | C3 |
| VI-E | What is not defended | 260 | Receiver-blind spoof; B-NORM vs stealth; B-RAY on PGD | C7, C8, C9 |
| VI-F | Costs | 240 | Table V (clean + runtime) | C10, C11 |
| VII | Discussion and limitations | 420 | Receiver-blind regions; adaptive attackers (none optimized against R1); baselines (no learned defenses); single attacker; single detector; simulation (incl. Culver = same simulated sensor; real sensors untested); statistics (15 / 4 clusters, bootstrap p); exposed development data | §5 objections |
| VIII | Conclusion | 110 | 4 sentences, one per contribution, each with its AP and set qualifier | C1, C3, C4, C7 |
| — | Data and code availability | 40 | TODO stays | — |
| App. A | Pre-registration history | 450 | v1 → D-57/D-58 → v2 (D-59) → D-60 audit → v3 (D-64..D-68, D-68 amendments) → v3.1 (D-70 †) → v3.2 (D-71) → Culver (D-72/D-73); exposure ledger | — |
| App. B | Development vs test | 120 + table | Table A1 (= `tab_dev_vs_test.tex`) | C14 |
| App. C | Full per-condition results | 60 + tables | Tables A2/A3: all 5 defenses × 12 conditions × {test, Culver}, G and F, with CIs | C6 detail |
| App. D | Stealth projection, infeasible counts, expected outcomes | 200 | eq. stealth; infeasible counts both sets; expected-outcome checks both sets | C8, C9 |
| App. E | Agent-count strata, realized-only | 100 + table | C15; realized-only recoveries | C7, C15 |

**Open decision (yours):** whether the appendix sits inside the 8 pages (then cut App. C/E to supplementary material) or after
the references as supplementary material. The budgets above assume supplementary.

### What to cut or move

- **Abstract:** the long condition list; "real-city layout" (P5); "the only one that recovers" (P2); "fail against optimized" (P4).
- **Intro ¶4** (D-57 narrative, ~90 words) → one sentence + App. A. **Contributions 4 → 4 items** tied to C1, C3, C4, C7; item 5 (limits) merged into VII.
- **Related work:** anomaly paragraph merged into consensus paragraph; "V2V4Real … provide real data" moved to VII/VIII (P5); MVIG \CITENEEDED{} kept only if a citation is found.
- **§Pre-registration history** (~200 words) → App. A.
- **eq. stealth** and infeasible-count sentence → App. D (one sentence stays).
- **"Expected outcomes checked descriptively" paragraph** (~110 words) → App. D.
- **§Development versus test** and Table VII → App. B.
- **§Unseen-town evaluation** as a separate section → dissolved; its numbers move into VI-A..F per claim; its setup into V-A.
- **Discussion "Agent count"** → App. E; **"No fresh data for tuning"** merged into "Adaptive attackers".
- **Conclusion future work (iii)** per-frame checkpointing → cut.
- **Figs. 1 and 2 (TikZ)** → replaced by `figures/r1_method.tex` (one `figure*`).
- **PNG figures 01, 02/02b, 03, 04, 05, 06** → cut from the paper (all stay in the run reports; numbers in tables/text).

---

## 3. Figure and table plan

| Float now | Decision | Reason / replacement |
|---|---|---|
| Fig. 1 pipeline (TikZ) | **Cut** | Superseded by `r1_method.tex` (shows senders, decodes, effects, ray check, composition) |
| Fig. 2 R1 mechanism (TikZ) | **Cut** | Same |
| `figures/r1_method.tex` (draft, not in main.tex) | **New in main** (`figure*`, label `fig:r1method`) | Caption from `r1_method_notes.md` |
| Fig. 3 `01_headline.png` | **Cut** | Replaced by the forest plot (test + Culver) |
| Fig. 4 `02_per_family` / `02b` (`figure*`) | **Cut** | Table IV carries it; full CIs in App. C |
| Fig. 5 `05_pgd_recovery.png` | **Cut** | Recoveries quoted in VI-B/E |
| Fig. 6 `06_bnorm_catch.png` | **Cut** | Four numbers, in text (C8) |
| Fig. 7 `03_clean_cost.png` | **Cut** | Table V |
| Fig. 8 `04_r1_minus_bray.png` | **Cut** | Forest plot bottom row; per-condition R1 − B-RAY in App. C |
| **New Fig. 2: forest plot** | **New** (column width) | Spec below |
| Table I splits | **Keep** | Already has the Culver row ("unseen town, simulated sensor") |
| Table II attacks | **Keep**, test only; trim "Mechanism" column | Culver attack losses in App. C |
| Table V verdict + Table IX `tab_culver` | **Merge → new Table III** "Pre-registered verdict (test, confirmatory) and the same rule applied descriptively (unseen town)" | Columns Test G, Culver G, Test F, Culver F; rows: B-RAY ΔAP [CI], p (Holm thr.), reject, clean CI, v2 rule; R1 ΔAP [CI], p, reject; R1 − B-RAY [CI] + statement; strong-removal rows dropped (in C4 text) |
| Tables III/IV `tab_main_global` / `tab_main_frame` (two `table*`) | **Replace → new Table IV** (one `table*`) | 12 rows × {B-RAY, R1} × {Test, Culver} × {G, F} = 8 columns, point estimates only; bold = CI above zero, italic = CI below zero. Full CIs and R1-noREMOVE / B-NORM / ego-only in App. C (Tables A2/A3) |
| Table VI clean | **Merge with runtime → new Table V** | Top: rel. loss B-RAY / R1 / R1-noREMOVE × {Test, Culver} × {G, F}; middle: what is removed (C10, both sets); bottom: runtime p50/p95 by n (C11, both sets) |
| Table VII runtime | Merged into Table V | — |
| Table VIII dev vs test | **Move → App. B** | Development |

Main body: 2 figures, 4 tables (I, II, III, IV `table*`, V) — 5 tables. New tables need `gen_numbers.py` writers (copy only, with
the existing assertion that report CSVs equal `e5_v3.json`).

### New Fig. 2: forest plot (spec)

- **Rows (top to bottom):** B-RAY, R1, R1-noREMOVE (mean ΔAP@0.7 over the 4 original attacks), a gap, then R1 − B-RAY (paired).
  B-NORM and ego-only are off scale (−5.85 … −24.20) and stay in Table III / App. C.
- **Panels:** left = global-ranking AP, right = frame-order AP; shared x-axis in AP points; vertical line at 0.
- **Per row, two markers, vertically offset:** OPV2V test (filled, primary) above Culver (open, secondary). Whiskers = 95%
  scenario-bootstrap CI only (pre-registered primary CI). **No pooled diamond, no combined estimate.**
- **Annotations:** test rows labelled with the Holm decision (`reject` / `no`); R1 − B-RAY rows labelled with the emitted
  statement in short form ("improves" / "worse" / "not established").
- **Caption:** "… OPV2V test (primary, \TestScenarios{} scenarios) and Culver City (unseen town, simulated sensor; secondary,
  \CulScenarios{} scenarios; coarse CIs). Never pooled."
- **Data sources (exact keys; × 100 to AP points):**
  - Means: `T` and `C` → `tables.global.mean_of_4_orig.{B-RAY,R1,R1_noREMOVE}.{point,ci95_scenario}` and
    `tables.frame.mean_of_4_orig.{B-RAY,R1,R1_noREMOVE}.{point,ci95_scenario}`.
  - Paired: `T` and `C` → `tables.global.R1_minus_BRAY.mean_of_4.{point,ci95_scenario}` and `tables.frame.R1_minus_BRAY.mean_of_4.{point,ci95_scenario}`.
  - Annotations: `criteria_v3.<ap>.co_test_vs_no_defense.{B-RAY,R1}.holm.reject`; `criteria_v3.<ap>.R1_minus_BRAY.statement`.
  - Cross-checks the script must assert equal: `criteria_v3.<ap>.co_test_vs_no_defense.{B-RAY,R1}.{point,ci95_scenario}`
    (= the mean rows), `criteria_v3.<ap>.R1_minus_BRAY.{point,ci95_scenario}`, `runs/20261024-E5v3/report/tables/01_headline.csv`,
    `runs/20261026-CULVER/report/tables/01_headline.csv`, `runs/20261026-CULVER/report/tables/11_test_vs_culver.csv`.
  - Values it will plot (copied from the keys above, for review): test G B-RAY 0.00147 [−0.0001, 0.003], R1 0.00454
    [0.0029, 0.007], R1-noREM 0.00258 [0.0018, 0.0036], R1 − B-RAY 0.00307 [0.0012, 0.0055]; test F 0.00758 [0.0049, 0.0127],
    0.00187 [−0.0045, 0.0052], 0.00664 [0.0048, 0.0103], −0.0057 [−0.0164, −0.0011]; Culver G 0.00052 [−0.0003, 0.0013],
    0.00319 [0.0021, 0.0048], 0.00084 [−0.0005, 0.0018], 0.00266 [0.0012, 0.0048]; Culver F 0.00536 [0.0022, 0.0092],
    0.00401 [0.0021, 0.0073], 0.0038 [0.0023, 0.0063], −0.00135 [−0.004, 0.0019].
- **Implementation:** a new `paper/figures/forest.py` (matplotlib, stdlib JSON), writing `figures/forest.pdf`; colours from
  one categorical pair (test / Culver), colour-blind safe, marker shape also differs. Not written yet.

---

## 4. Title and abstract options

All say "simulated". "Real-world" / "real data" do not appear; "real sensors" appears only as a limitation.

**Titles**

1. *Ray-Verified Tile-Level Counterfactual Gating for Cooperative LiDAR Perception: A Pre-registered Evaluation in Simulation*
2. *Does a Physically Verified Counterfactual Help Cooperative Perception? A Pre-registered Simulated Evaluation with an Unseen-Town Check*
3. *Counterfactual Gating Against Malicious Senders in Simulated Cooperative LiDAR Perception: Pre-registered Results and an AP-Definition Reversal*

(Recommendation: 1; it names the method, the design and the setting without a robustness claim.)

**Abstract A (method-first, ≈ 190 words)**

> Intermediate-fusion cooperative perception lets a malicious sender spoof, remove or shift objects by editing the features it
> transmits. We evaluate R1, a defense that asks, per sender and 6.4\,m tile, what changes if the sender is removed there, and
> switches the contribution off only when the receiver's own LiDAR rays resolvably contradict the change. In a pre-registered,
> one-time test on simulated OPV2V data (\TestScenarios{} scenarios, \TestFrames{} frames, \NumConditions{} conditions including
> white-box and B-NORM-aware stealth PGD), the pre-registered primary, a receiver-only box-level free-space filter (B-RAY), passes
> its success rule under both AP definitions, narrowly under global-ranking AP (\VGlobBRAYDelta\pts, one-sided Holm
> $p=\VGlobBRAYP$, two-sided CI \VGlobBRAYCI). R1 gains \VGlobRONEDelta\pts{} and is the only defense with a CI above zero in all
> \NumConditions{} conditions under global-ranking AP; on the strongest stealth removal$^\dagger$ it restores
> \dGlobPgdRemStStrongRONE{} of \LossGlobPgdRemStStrong\pts. Whether R1 beats B-RAY depends on the AP definition (\VGlobRmB{}
> vs.\ \VFrameRmB\pts). On a held-out unseen town (Culver City, simulated sensor, \CulFrames{} frames) the signs of these mean
> effects repeat, but
> B-RAY's global-ranking gain is not significant (\CulHeadGlobBRAY\pts, $p=\CulVGlobBRAYP$). Receiver-blind spoofs stay
> unrecovered, and R1's compute grows with the number of cars. Transfer to real sensors is untested.

**Abstract B (finding-first, ≈ 170 words)**

> A ranking of cooperative-perception defenses can depend on which average-precision definition is used. We show this in a
> pre-registered, one-time evaluation on simulated OPV2V data (\TestScenarios{} test scenarios) with a secondary check on an unseen
> simulated town (Culver City, \CulScenarios{} scenarios). We compare R1, a tile-level counterfactual that removes a sender where
> the receiver's own LiDAR rays contradict its effect, with a box-level free-space filter (B-RAY, the pre-registered primary), a
> feature-norm check (B-NORM) and ego-only perception, under \NumConditions{} attack conditions. B-RAY passes its success rule
> on the test, narrowly under global-ranking AP (\VGlobBRAYDelta\pts, $p=\VGlobBRAYP$); on the unseen town it does not reach
> significance under that definition. R1 minus B-RAY is \VGlobRmB\pts{} under global-ranking AP and \VFrameRmB\pts{} under
> OpenCOOD's default frame-order AP. Under global-ranking AP, R1 is the only defense whose CI is above zero on all four removal
> attacks, on both sets;
> B-NORM is evaded by stealth PGD on both. Receiver-blind spoofs remain undefended. Results are from simulation only.

---

## 5. Reviewer objections (`project_qa_for_reviewers.md` Part C8) and where the paper answers them

| Objection (C8, verbatim topic) | Where answered | How (claim / wording) |
|---|---|---|
| "No comparison with learned defenses (LUCIA, PoseGuard, MADE)." | §II (positioning, per-agent vs per-tile decisions); §VII *Baselines* (new paragraph) | State plainly that no learned defense was run; B-NORM is the only feature-statistics baseline and is not claimed to stand in for Latent Guardian or learned detectors (C8 "Not allowed"). No comparative claim against them anywhere. |
| "No attack optimized against R1 itself." | §III (attacker knowledge); §VI-E; §VII *Adaptive attackers* | The receiver-blind spoof is the only R1-aware attack (C7); stealth PGD adapts to B-NORM only (C8); an attacker placing fakes where rays are ambiguous (< 4 traversing rays) or unseen is not stopped (current Discussion text, kept). |
| "No real-sensor data; one detector; one attacker." | Title, abstract (§4: "simulated", "real sensors untested"); §V-A (Culver = unseen town, simulated sensor, same CARLA LiDAR model); §VII *Simulation*, *Single detector* (new: R1's exactness relies on AttFuse's per-pixel fusion, ledger C-05; models with spatial mixing after fusion would need re-verification, QA C5), *Single attacker* | Culver is never described as a realism or real-data test (C1/C12 wording). |
| "R1's advantage over B-RAY is AP-definition-dependent." | Abstract; contribution 2; §VI-D; Fig. 2 (forest plot, both definitions, both sets); §VIII | C3 wording only; "R1 beats B-RAY" never appears without the AP qualifier. |
| "Compute is above the original budget." | §VI-F, Table V; §VII *Compute* | C11 wording: overhead by n on both sets; budget dropped post hoc (D-50); T(0.05) is cost-only. |

Other Part C questions, for completeness (no restructuring needed beyond the above): C1 novelty → §I/§II + C13 (provisional);
C2 "own method not primary" → §I (one sentence) + App. A; C2 "gains small" → §VI-A states absolute AP points next to every
recovery (D-69); C2 "shrink from H to test" → App. B (C14); C3 leakage / exposure / post-hoc decisions → §V-A, §V-E, App. A;
C4 PGD budgets → §V-B; C6 clean cost → C10; C7 statistics and dropped calibration estimand → §V-D, §VII *Statistics*, App. A
(scope change stated); C7 oracle bound → C7 (visibility-limited oracle 0.10).

---

## 6. After approval (not done now)

1. `gen_numbers.py`: add the *new* copy-only macros (Culver per-condition CIs, Culver clean ΔAP, Culver R1/B-RAY clean
   breakdown, Culver runtime p95/T(0.05)/n = 1, Culver ego-only strong removal, Culver spoof_blind placement counts) and writers
   for Tables III, IV, V, A2, A3; add `figures/forest.py`.
2. Rewrite `main.tex` to the outline in §2 using only the allowed wordings in §1.
3. Rebuild the Overleaf zip; update `paper/README.md` (page estimate, figure list).
