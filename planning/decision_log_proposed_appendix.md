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

## Added 2026-10-23 (preflight for MINT-v0.0); also proposed, not applied

| ID | Decision | Alternatives | Rationale | Confidence |
|---|---|---|---|---|
| D-35 | **Harm notation.** `D = L_u(Y⁺) − L_u(Y⁻(i,u))`. HARMFUL iff `D > m`; USEFUL iff `D < −m`; NEUTRAL iff `−m ≤ D ≤ m`; `m = 0.5`. `p_harm_keep = P(D > m | ev)`, `p_harm_remove = P(D < −m | ev)`. Remove sender *i* in tile *u* iff KNOWN and `p_harm_keep > κ·p_harm_remove` (κ = 1). Uncalibrated variants use raw `h_keep`, `h_remove` and are never called probabilities. D-02's `P(D ≤ m | X)` = `1 − p_harm_keep`. Only the boundary differs from contract §5.1 (`D ≥ m` there). | Keep `D ≥ m`; one-sided rule | User request 2026-10-23; makes action rule and variable names agree | High |
| D-36 | E0 pre-registration (before any download): primary recovery metric uses AP@0.7 and the oracle restricted to the attacker's units under the receiver-visibility constraint; criterion < 30% → stop. Details in `runs/20261023-E0/preregistration.json`. | Use the all-sender oracle (mixes benign-harm fixes into "recovery") | Isolates attack-loss recovery | High |
| D-37 | Ground handling for OPV2V ray tests is decided by a pre-registered empirical test on the development scenarios (empty synthetic boxes vs genuine objects, with and without a per-frame receiver-only ground classifier). | Assume flat ground; use GT ground | Envelope test counts ground hits under a fake box as support at near range (§ geometry note in the E0 report) | Medium |

## Added 2026-10-23 (E1, development block T); also proposed, not applied

Source: [e1_report.md](e1_report.md). `decision_log.md` was not edited; D-17 is unchanged.

| ID | Decision | Alternatives | Rationale | Confidence |
|---|---|---|---|---|
| D-38 | **Latency accounting for D-17.** Baseline = receiver-only encode + plain fusion + decode + post-process; encoding of sender point clouds is excluded (reported separately). Overhead = MINT-only stages (counterfactual decodes, effects, ray evidence, rule, composition) / baseline, per frame; report p50 and p95 over frames (per-frame median of ≥ 3 interleaved repetitions on shared hardware). | Count all agents' encoding in the baseline (E0: +16% p50) | Sender encoding is 62% of the old encode time and is not receiver work; E1 A2 | High |
| D-39 | **The gated output is composed** from the decodes already computed (`compose()+finalize()`); an extra decode only for tiles gating ≥ 2 senders. | Final masked decode (E0) | Exact on 24/24 frames; removes up to 0.28 s per gated frame; E1 A1 | High |
| D-40 | **R1 "resolvable evidence"** (Wilson 95% margins on receiver ray counts; ADD/REMOVE/SHIFT gate and mirror conditions; UNKNOWN = keep) replaces the θ = 0 raw-score rule as the candidate MINT-v0 decision rule, labelled a resolvability margin, not a probability. Status: development evidence only (in-sample, 3 scenarios, rule written after E0 on the same data); any calibration remains blocked by the cost criterion. | Keep θ = 0; tune θ or type-specific thresholds on T | E1 B: recovery 0.16–0.28 per family (mean 0.196), clean AP@0.7 loss −0.04%, false rejections 61–73 → 20–24 | Medium |
| D-41 | **Drop the attention-share fallback for blind tiles** (D-29 drop criterion met). | Keep as a module | E1 C: AUROC 0.29–0.47, 0/4 families meet the pre-registered bar; sign unstable across scenarios | High |

Open (needs the user, not proposed here): under D-38 a dense counterfactual costs ≥ ~21% of the receiver's perception at n = 2 on CPU and grows ~linearly with n, so D-17 (≤ 10% p95) is not reachable by implementation changes measured in E1. The options are the user's decision: a different cost model (e.g. counterfactuals only on candidate tiles from a cheaper trigger), different hardware for the budget, or a revised budget.
