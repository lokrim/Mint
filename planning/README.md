# MINT (Multi-agent Inbound Node Trust): planning package

**Status (2026-10-22):** Planning checkpoint 1 is done. Path chosen: no GPU, so OPV2V-first.

The **Stage-1 OPV2V feasibility work is done**; see [stage1_spike_report.md](stage1_spike_report.md):
- The released AttFuse checkpoint reproduces the published test AP@0.7: **0.8155 vs 0.815** (16 scenarios, CPU).
- Fusion locality held in **93/93** tile tests with 2–5 agents.

Still open in Stage 1: V-02 (own-frame encoding) and V-05 (message size). No MINT method results exist yet.

MINT asks whether a cooperative-perception receiver can estimate, per received feature contribution (sender × BEV tile × time), the calibrated probability that including it *harms* 3D detection. It then asks whether gating on that estimate preserves clean accuracy and limits attack harm, measured against ground truth.

## Reading order

1. [research_charter.md](research_charter.md): objective, estimand, hypotheses H1–H6, contribution candidates, non-goals.
2. [information_and_threat_model.md](information_and_threat_model.md): representations, targets, data flow and trust boundary, notation, the GT label bridge, settings A/B/C, threats, identifiability, deployment placement.
3. Literature:
   - [literature/search_log.md](literature/search_log.md): queries, rules, citation trails, access status;
   - [literature/comparison_matrix.csv](literature/comparison_matrix.csv);
   - [literature/references.bib](literature/references.bib);
   - 13 [reading notes](literature/reading_notes/).
4. [dataset_and_feature_feasibility.md](dataset_and_feature_feasibility.md): Mixed Signals vs OPV2V vs V2V4Real vs DAIR-V2X-C vs V2X-Real; exact pipelines; GT contract; resources; the sanity-check gate.
5. [methodology_candidates.md](methodology_candidates.md): M0–M5, including the ray idea (M3) and its statistical version (M4); counterexamples; complexity.
6. [methodology_spec.md](methodology_spec.md): the recommended MINT-v0, with every assumption's status.
7. [evaluation_protocol.md](evaluation_protocol.md) and [attack_and_benign_protocol.md](attack_and_benign_protocol.md): the preregistration drafts.
8. [compute_memory_and_communication_budget.md](compute_memory_and_communication_budget.md).
9. [implementation_roadmap.md](implementation_roadmap.md) and [notebook_plan.md](notebook_plan.md).
10. [paper_plan.md](paper_plan.md) and [claim_evidence_ledger.csv](claim_evidence_ledger.csv).
11. Choices and state:
    - [decision_log.md](decision_log.md);
    - [risks_and_open_questions.md](risks_and_open_questions.md);
    - [exposure_ledger.csv](exposure_ledger.csv);
    - [next_session_brief.md](next_session_brief.md).
12. [pilots/](pilots/README.md): three disposable pilot checks (not final evidence).
13. [findings/](findings/README.md): inherited Valid Point audit, preserved unchanged.

## Key conclusions of this checkpoint

1. **The ray support/traversal idea is prior art** as an object check: CARLO's laser-penetration ratio, Shadow-Catcher, and CAD's free-space conflict rules. It is feasible only with the **receiver's own scan**: latent features carry no rays, and sender-supplied rays are self-verification. It says nothing where the receiver cannot see.
2. **Closest prior work for the unit and estimand:**
   - PoseGuard (2026: per-object feature-crop anomaly, detection only);
   - LUCIA (2025: per-agent trust inside attention);
   - TrustReflect (2026: region masking);
   - MADE/GCP (conformal per-agent tests);
   - MATE (2025: Beta trust per track).
   None was found to output a calibrated, spatially resolved probability of task harm with explicit unknowns. That is a search-limited statement.
3. **Structural opportunity.** For per-pixel attentive fusion, each contribution's counterfactual effect is computable (derived from code; to verify). This makes harm labels exact and turns reliability into verifying concrete add/remove/shift claims.
4. **Mixed Signals.**
   - No released checkpoint (the README literally says `???`).
   - 214 GB of labelled archives.
   - All public segments come from **one ~35-minute session** (pilot P3).
   - Organized Ouster grids allow cheap range-image ray checks (pilots P1/P2).
   Under the current hardware (M1, no CUDA, 21 GB free), the recommended path is **OPV2V-first with released checkpoints**, V2V4Real as the real-data replication, and Mixed Signals when GPU and storage exist.
5. **Recommended minimal method (MINT-v0).** Beta-binomial receiver-ray evidence for each effect, isotonic-calibrated, with explicit unknowns and hard tile gating. Fallback: a feature-only calibrated combiner.

## Decisions needed

Q1–Q4 in [risks_and_open_questions.md](risks_and_open_questions.md): GPU/storage, deployment class, receiver inputs, time budget.
