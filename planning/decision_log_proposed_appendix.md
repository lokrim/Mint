# Proposed append-only decision updates (NOT yet applied)

2026-10-23. Source: [methodology_research_report.md](methodology_research_report.md). **`decision_log.md` was not edited.** If accepted, append these rows to the log unchanged; no existing entry (D-01…D-25, D-13b) is modified. Status for all: **Proposed (pending user)**.

| ID | Decision | Alternatives | Rationale (report section) | Confidence |
|---|---|---|---|---|
| D-26 | The 2% clean-accuracy limit is **relative**: `AP@0.7_clean(MINT) ≥ 0.98 × AP@0.7_clean(AttFuse)` (OpenCOOD default AP, scenario-pooled; floor 0.7992 for the reproduced 0.8155). Non-inferiority needs the upper 95% scenario-clustered paired-bootstrap bound of relative loss ≤ 2%. AP@0.3/0.5 reported. | Absolute 2 AP points (allows 2.45% relative loss) | §8.1; matches charter H2 | High |
| D-27 | Decisions are **two-sided**: per effect, compare P(harm of keeping) with c × P(harm of removing). The existence of a box is the single latent variable for ADD / REMOVE / SHIFT. | One-sided "reject if suspicious" | §3; 110 benign REMOVE/harmful effects on clean data | Medium-high |
| D-28 | Cross-agent corroboration is **not** in the v0 method. It is a baseline (ego/solo consensus) and a ≥3-agent stratum analysis. | Include as a v0 module | §1, §5: thin in effect tiles, undefined with 2 agents, spoofable (Pretend Benign) | Medium |
| D-29 | Temporal consistency and the feature/output fallback are optional modules with pre-registered drop criteria (ΔAUROC < 0.03 in UNKNOWN; blind-stratum AUROC < 0.60). Feature signals are **logged from the first prototype** but not used in the v0 decision. | Build them into v0 | §5, §8.6 | Medium |
| D-30 | Run E0 (oracle and visibility-limited-oracle headroom) before further method work; abandon gating as the headline if the visibility-limited oracle recovers < 30% of attack-induced AP loss under random-placement attacks. | Skip to calibration | §8.6 | Medium |
| D-31 | Minimum further validate data for calibration = the 4 small scenarios (≈2.9 GB); the two large ones (11.1 and 21.7 GB) only if the calibration-count criterion fails. Calibration by leave-one-scenario-out, Platt before isotonic. All three examined scenarios remain block T (D-25). Requires user approval before any download. | Stream all 6 | §8.2 | Medium |
| D-32 | First milestone = MINT-v0.0 end-to-end (deterministic ray ratio, hard gating, UNKNOWN=keep, uncalibrated threshold) on the three development scenarios, with E0 bounds. Needs re-streaming 4.26 GB (raw data was deleted). | Report-only milestone | §9 | High |
| D-33 | OPV2V receivers move: v0 ray tests must not use the Mixed-Signals static ground map; a per-frame receiver-only ground estimate is a prerequisite item if ground contamination appears (currently unimplemented). | Reuse spec §3 ground map | §3 point 7 | Medium |
| D-34 | Novelty wording: say "to our knowledge", compare against MADE (with/without-sender), MATE (beta trust + FOV gating), CAD/CARLO (free space) and TrustReflect (uncertain mask); recheck the search before submission. | Claim novelty of counterfactual or ray evidence | §4 | High |

Related claim-ledger changes to propose (not applied): C-02 stays PROVISIONAL (search-limited); add a claim "visibility-limited oracle bound" (NOT-RUN).
