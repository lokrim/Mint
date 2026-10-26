# Prompt 3: draft the paper in IEEE format (after prompt 2, and after the "Before you run this" list)

## Before you run this (the authors' part, not the session's)

These must be done first. The prompt checks them in step 1 and stops if any is missing.

1. **Re-scope the paper.** `planning/paper_plan.md` (2026-10-22) still describes MINT as a calibrated beta-binomial reliability model. That model was never built or tested (ledger C-09, C-10, C-14 to C-22: NOT-RUN). What was tested is a pre-registered evaluation of B-RAY, R1 and B-NORM on OPV2V. Rewrite the plan's "intended argument" and section table for that paper, choose a working title, and commit it.
2. **Fill the two report gaps** (copy-only, through `src/mint/report`): a runtime-overhead table (`e5_test.json` → `overhead`, p50/p95 by agent count), and the oracle bounds (`e5_test.json`, in the pre-registered comparison set but not shown in `report.md`). Record the machine the timings ran on.
3. **Sign off the interpretation.** Edit `planning/final_report_interpretation_DRAFT.md` until you agree with it, then rename it without `_DRAFT`.
4. **Add ledger rows** in `planning/claim_evidence_ledger.csv` for each claim the paper will make, with a status and a pointer to the report section.
5. **Choose the venue** and fill in `TARGET` below.
6. **Make LaTeX available:** install `tectonic` (`brew install tectonic`), or plan to build on Overleaf.

Paste everything below the line into a new Claude Code session in `/Users/lokrim/Code/mint`.

---

Draft the research paper for the MINT final test (E5, OPV2V) in IEEE format. Every result in the paper comes from the frozen final-test outputs. You write and lay out; you do not compute new results.

**TARGET:** `<venue name>`, `<IEEEtran conference | IEEEtran journal>`, page limit `<N>` plus references. If this line is unfilled, stop and ask.

### 1. Preconditions (stop and tell me if any fails)

- `runs/20261024-E5v3/report/report.md` says "Status: FINAL TEST (one-time)" and contains a runtime-overhead section and an oracle-bounds section.
- `planning/paper_plan.md` describes the evaluation paper (B-RAY / R1 / B-NORM), not the calibrated MINT model, and has a commit dated after 2026-10-26.
- `planning/final_report_interpretation.md` exists (signed off; no `_DRAFT` in the name).
- `planning/claim_evidence_ledger.csv` has rows for the paper's claims.
- `tectonic --version` works, or I said to build on Overleaf (then produce a zip in `paper/build/`).
- `.venv/bin/python -m pytest tests/test_report.py -q` passes.

### 2. Sources of truth (read them all before writing)

- **Numbers:** `runs/20261024-E5v3/e5_v3.json`, `e5_test.json`, and `report/tables/*.csv`. These are the only sources for test results.
- **Interpretation:** `planning/final_report_interpretation.md`.
- **Rules and labels:**
  - `runs/20261024-E5/preregistration_v3_2.json`: D-64 rule, outcome wording, scope_limits, labelling, D-69, D-70, D-71.
  - `runs/20261024-E5/preregistration_v2.json`: the primary, the Holm co-test, the key_secondary statement rule, scope_limits_D54.
- **Story and attribution:** `planning/paper_plan.md`.
- **Prior work:** `planning/pre_final_audit.md` §3 (prior-work table and novelty verdict), and `planning/literature/` (`references.bib`, reading notes, `comparison_matrix.csv`).
- **Method definitions:**
  - `planning/methodology_spec.md`;
  - decisions D-56 (comparison set), D-57/D-58 (how B-RAY became primary), D-65 to D-68 (PGD, B-NORM, stealth) in `planning/decision_log_proposed_appendix.md`;
  - the code in `src/mint/` for exact definitions.
- **Development numbers (blocks T and H):** only from the frozen preregistrations (`development_check_E5a`, `block_H_comparison_E5a_H`, `development_check_v3_H`).

### 3. Hard rules

- **No hand-typed result numbers.**
  - Write `tools/paper_numbers.py`. It reads the JSON/CSV sources and writes `paper/generated/numbers.tex` (one `\newcommand` per number, e.g. `\BRAYdAPglobal`) and `paper/generated/tab_*.tex` (tables).
  - The paper uses only those macros and tables.
  - Rounding matches `report.md`. Add a test, `tests/test_paper_numbers.py`, that checks every macro against `report.md`.
- **No new computation.** Don't fit, bootstrap, re-run or derive a statistic that isn't in the sources. A ratio or difference not in the sources is not allowed.
- **Keep the three kinds of numbers apart, in text and in captions:**
  - **Confirmatory:** the D-64 verdict, the v2 rule, the R1 − B-RAY statements.
  - **Descriptive:** PGD, B-NORM, realized-only, by agent count, box/unit breakdowns, runtime.
  - **Development:** blocks T and H. Label them as development wherever they appear. They never sit in the same table column as test numbers without a label.
- **Quote pre-registered statements exactly**, in quotation marks.
- **State AP-definition dependence.**
  - R1 − B-RAY is "AP-definition-dependent". Never write that R1 beats or loses to B-RAY without that qualifier.
  - Headline numbers are global-ranking AP; frame-order AP sits beside them.
- **Mark D-70 conditions.** Use †, with the label "strong-attack level, added after seeing block-H development results", and never use them in a claim.
- **Say "significant" only with the test named**, e.g. "Holm-rejected, one-sided scenario-bootstrap p = …".
  - Under global-ranking AP, B-RAY's two-sided 95% scenario CI includes 0 while the Holm test rejects. Say both.
- **Attribution** (paper_plan.md):
  - Make no novelty claim for ray support/traversal checks. B-RAY applies a known receiver-only free-space check (CARLO's LPD [sun2020carlo], CAD [zhang2024cad], Shadow-Catcher [hau2021shadowcatcher]) to intermediate-fusion CP.
  - R1's tile-level, ray-gated counterfactual is the only possibly new element. Use "to our knowledge", and cite MADE and ROBOSAC as agent-level counterparts.
  - Contributions stay within: the estimand and unit, the label bridge, the evaluation (pre-registered, dual-AP), and possibly efficiency.
- **Limits go in the main text** (a Limitations section), not only an appendix:
  - scope_limits (v3.2) and scope_limits_D54;
  - D-69's receiver-blind statement;
  - simulation only (CARLA LiDAR; no real-world dataset was tested);
  - single attacker; white-box PGD on this checkpoint;
  - the method was chosen on exposed block H;
  - the deviations D-70 and D-71.
- **No combined or selector method.** R1 and B-RAY were tested separately. A combination or a policy for choosing between them goes in Discussion/Future work as untested, with the reason: the test set is now spent.
- **Bibliography:** cite only entries in `planning/literature/references.bib`. Preprints (MVIG, PoseGuard, TrustFlip, GLST) are listed as preprints. If a needed citation is missing, add a `% TODO cite` comment and list it for me. Don't invent bibliographic details.
- **Frozen files:** never edit frozen files, the analysis code, or the report numbers.

### 4. Structure

Build `paper/main.tex` with IEEEtran, one file per section in `paper/sections/`.

1. **Title, abstract** (≤ 200 words; verdict, effect size in AP points with both AP definitions, cost, main limit).
2. **I. Introduction.** Problem: untrusted intermediate features in cooperative perception. What we test and why it is pre-registered. Contributions stated only as supported. A one-paragraph summary of results.
3. **II. Related work.** CP architectures; CP security (CARLO, Shadow-Catcher, CAD, MATE, ROBOSAC, MADE, LUCIA/SOMBRA, PoseGuard, GCP, TrustFlip, CP-Guard); evaluation practice (AP definitions).
4. **III. Threat model and problem.** Receiver's trusted sensor, untrusted senders, single attacker, what the receiver can and cannot verify (the receiver-blind region).
5. **IV. Defenses evaluated.** B-RAY (box-level ray filter, Wilson test), R1 (tile counterfactual with ray-verified ADD/REMOVE effects, UNKNOWN = keep), R1-noREMOVE, B-NORM (sender-level magnitude check), ego-only, no defense, oracle bounds. Give each one's inputs, granularity, tunable parameters (none) and cost.
6. **V. Experimental protocol.** OPV2V and the AttFuse checkpoint; splits and exposure (blocks T and H → freeze → one-time test of 15 scenarios / 2066 frames); attack families (E4 families, PGD, stealth PGD with feasibility rule); metrics (ΔAP@0.7, recovery, clean relative loss, both AP definitions and why); statistics (scenario and 10-frame bootstrap, Holm co-test, statement rule); procedural checks; deviations.
7. **VI. Results.**
   - pre-registered verdict;
   - headline effect;
   - every attack condition;
   - clean cost;
   - R1 vs B-RAY;
   - PGD and B-NORM;
   - by agent count;
   - runtime overhead;
   - what each defense removes (boxes / units).
8. **VII. Discussion.**
   - Why the two AP definitions disagree, and what that means for CP evaluation.
   - Effect size against cooperative benefit: ego-only −20 points.
   - Removal attacks and the blind region.
   - When each defense fits (descriptive only, cost vs threat).
   - Combination as future work.
9. **VIII. Limitations.** IX. **Conclusion.** Reproducibility statement (frozen commits, hashes, run commands).
10. **Appendix / supplement:** full per-condition tables under both AP definitions, realized-only tables, development numbers (T and H, labelled), D-70/D-71 text.

### 5. Figures and illustrations

Make every figure vector PDF, sized for IEEE columns: 3.5 in single, 7.16 in double. Use a serif-compatible font at 8 pt and colour-blind-safe colours that still read in greyscale.

- **Data figures:** add a `paper` style to `src/mint/report/style.py` (presentation only) and export from the existing figure functions to `paper/figures/`. No new figure computes anything.
  - Main text: headline (Fig. 1 of the report), per-condition original attacks (2a), clean cost (3), R1 − B-RAY (4a), PGD recovery (5), B-NORM catch rate (6), runtime overhead vs agent count (new figure from the overhead table).
  - Supplement: 2b, 4b, 7, 8, 9, 10.
- **Illustrations** (TikZ in `paper/figures/tikz/`, or clean SVG→PDF):
  1. **System overview:** receiver and senders, intermediate fusion, where the attacker acts, and where B-NORM (sender level), R1 (tile level, before fusion output) and B-RAY (box level, after detection) act.
  2. **B-RAY mechanism:** the receiver's LiDAR rays against a candidate box, with support vs traversal, the Wilson upper bound, and the receiver-blind case marked.
  3. **R1 mechanism:** with/without-sender counterfactual per 6.4 m tile, effect types ADD/REMOVE/SHIFT, ray verification, UNKNOWN = keep.
  4. **Protocol timeline:** development blocks T and H, decisions, freeze commits, the one-time test, and the deviations D-70 and D-71.
- **Captions** state the AP definition, the CI type, the confirmatory/descriptive/development label, and † where it applies.

### 6. Tables

Generate all tables in `paper/generated/` with booktabs.

- **T1. Defenses compared:** granularity, inputs, needs GT (no), tunable parameters, can restore removed objects, can act in receiver-blind areas, runtime p50 at n = 2.
- **T2. Pre-registered verdict:** both AP definitions; B-RAY and R1 ΔAP, p, Holm, clean-loss CI, rule result; R1 − B-RAY with its exact statement.
- **T3. ΔAP@0.7 per condition:** compact in the main text, full in the appendix.
- **T4. Costs:**
  - clean relative loss (both AP definitions);
  - real cars removed by B-RAY on clean frames;
  - useful contributions switched off by R1 on clean frames;
  - runtime overhead p50/p95 by agent count.
- **T5. PGD and B-NORM:** attack loss, recovery, catch rate, infeasible/applied counts.
- **T6. Development vs test** (appendix), with every development column labelled.

### 7. Process and checkpoints

1. Write `paper/OUTLINE.md`: section headings, the claim each paragraph makes with its evidence pointer (report section + ledger ID), the figure and table list, and the word budget. **Stop and show me the outline before drafting.**
2. After my approval:
   - Write `tools/paper_numbers.py` and its test.
   - Generate the numbers, tables and figures.
   - Draw the illustrations.
   - Draft the sections.
3. Build the PDF (`tectonic paper/main.tex`, or the Overleaf zip). Check the page limit, the absence of overfull boxes, every float referenced in the text, and every figure readable at print size (view each page image).
4. Run checks and write `paper/CHECKS.md` with the results:
   - every number in the `.tex` files is a macro;
   - `tests/test_paper_numbers.py` passes;
   - every claim in the abstract, introduction and conclusion maps to a ledger row;
   - every quoted pre-registered statement matches the JSON exactly;
   - no "novel" or "first" wording near ray checks;
   - every development number is labelled;
   - every † condition is labelled.
5. Commit `paper/`, `tools/paper_numbers.py`, the test and any `style.py` change. Don't push. Give me the PDF path, a list of open TODOs (missing citations, author decisions), and anything that didn't fit the page limit.
