# Notebook plan

Checkpoint 1, 2026-10-22. Notebooks are organised by scientific segment, not by file quota.

## Acceptance criteria (every completed notebook)

Inherited from [findings 08 §6](findings/08_reproducibility_resources_and_notebook_lessons.md) and extended. Each notebook must:

1. **State** its question, population (units and roles), runtime inputs, equations and assumptions, and a falsification condition.
2. **Show a worked hand example.** Small numbers, computed by hand in markdown and then by the code, with an asserted equality.
3. **Call the real implementation** in `src/mint`. No notebook-only logic.
4. **Display intermediate evidence with units:**
   - range images with no-return masks;
   - per-slot classes;
   - counts;
   - feature slices;
   - attention shares;
   - effects;
   - D labels.
5. **Validate.**
   - At least one meaningful check that can fail (e.g. a slab test vs brute force).
   - At least one counterexample or failure case, displayed.
6. **Show readable plots.** Axis labels with units; the light/dark-safe default palette; no unreadable 3D clutter.
7. **Report complete small grids** with denominators and UNDEFINED cells, never just `head()`.
8. **Conclude** with "established / not established", plus a claim-ledger row ID.
9. **Execute top-to-bottom in a fresh kernel.** The executed copy, exported figures and tables, and a provenance cell (git commit, config hash, input hashes, environment, wall time, peak RSS) are saved under `runs/<id>/notebooks/`.
10. **Never trigger extraction, download or training on open.** Expensive steps sit behind explicit flags and read cached run outputs by hash.

Reporting notebooks (09–12) may read sealed outputs, but they must recompute the displayed metrics from the per-unit records (not copy summaries) and re-verify the seal.

## Sequence

| # | Notebook | Stage | Question | Key contents | Must-show failure or counterexample | Ledger rows |
|---|---|---|---|---|---|---|
| 01 | `01_literature_to_hypotheses.ipynb` | 0/1 | Which ideas are prior art, and what remains testable? | Prior-work table rendered from `comparison_matrix.csv`. Toy 2D scene recomputing CARLO `f_B`/`g_B`, CAD eq. 7 rules and LUCIA eq. 10–12 on hand numbers. The two-worlds identifiability construction. | LUCIA's N = 2 complementary-score artefact; CARLO's porous-object false contradiction | C-01, C-02 |
| 02 | `02_dataset_gt_integrity.ipynb` | 1 | Are coordinates, labels, clocks and placeholders right? | Organized-grid anatomy. Placeholder masks by elevation. Frame transforms on 5 frames per segment. V-04 alignment residual by offset. Keyframe identification. Visibility strata counts. Segment timeline (pilot P3). | A label offset that *looks* right on static objects only (P1-c style) | C-03, C-04 |
| 03 | `03_features_clean_perception.ipynb` | 1 | Is the feature interface real and the clean detector sane? | Checkpoint provenance. Per-scale tensor shapes and strides. Warp check. Clean AP per class with denominators. V-02, V-03 locality test. Per-stage cost on the proxy device. | Locality violation demo with a spatially mixing fusion (e.g. a window-attention toy) | C-05, C-06 |
| 04 | `04_ray_geometry.ipynb` | 2 | When does a receiver ray support, contradict, or say nothing about a box? | Slot-direction fits (V-06). Slab test. Per-slot classes on real boxes. Coverage of effectful tiles. Range-image footprints. | The eight counterexamples ([candidates](methodology_candidates.md)): porous bike, dark car (NR), shadowed pedestrian, moving object with skew, ground in core, NR-as-free fallacy (AB-3) | C-07, C-08 |
| 05 | `05_reliability_model.ipynb` | 3 | Do beta-binomial models fit, and is the calibrated output a probability on C? | Derivation of the log-BF. Hand check. Fitted μ, φ with posterior-predictive checks per bin. Effective sample size. Isotonic calibration. Reliability diagrams (C). Gate θ selection. The LUCIA-bound extension for soft weighting. | Binomial (φ = 0) overconfidence vs beta-binomial on correlated rays | C-09, C-10 |
| 06 | `06_temporal_missingness_benign.ipynb` | 3/4 | How does state behave under silence, stale data, on/off and benign stresses? | `r_inst` vs `r_temp` timelines. STALE transitions. Message drop. Benign B-1..B-12 summaries on T/C. ID-permutation and prefix invariance. Blast-radius test. | History poisoning (A-T3 on dev) slowly raising `r_temp` | C-11, C-12 |
| 07 | `07_raw_cloud_attacks.ipynb` | 5 | Do raw-cloud fabrications realize as intended and cause harm? | Per-family edits in the sender range image. Ray-consistency checks. Re-encoding. Realization ledger. Harm distribution vs GT. | A zero-effect attack, and a harmful attack that MINT cannot see (receiver shadow) | C-13 |
| 08 | `08_feature_attacks_adaptive.ipynb` | 5 | What do feature attacks change, and can an adaptive attacker evade MINT? | Mask in/out ratios. Attention-share changes (SOMBRA). Effect sets. A-F6/A-F7 evasion results on dev. Unknown-policy trade-off. | An adaptive success inside receiver-unobserved tiles (expected by H4) | C-14, C-15 |
| 09 | `09_per_unit_results.ipynb` | 6 | What happened in each held-out unit? | Per-segment/scenario BEV panels: GT, AttFuse, MINT, gated tiles, unknown tiles, attack masks (evaluator view). Per-unit metric tables. | The worst unit for MINT, shown in full | C-16 |
| 10 | `10_grouped_evaluation.ipynb` | 6/7 | Are H1–H4, H6 supported on held-out groups? | Recomputation from per-unit records. Paired differences. Cluster bootstrap (with caveats). Risk–coverage. Calibration on E. Ablations AB-1..AB-9. Failure gallery. | The largest calibration failure on a held-out family | C-17..C-21 |
| 11 | `11_efficiency.ipynb` | 7 | What does MINT cost, end-to-end and incrementally? | Stage timings (p50/p95/max). Peak RSS including children. Sparsity achieved. Bytes on the wire. Proxy vs target labelling. | Worst-case frame (many effects) | C-22 |
| 12 | `12_paper_figures_and_claims.ipynb` | 8 | Is every paper claim backed? | Regenerates every figure and table by exact command. Validates `claim_evidence_ledger.csv` (each claim → run id, table row, hash). Reproduction checks. | Claims marked unsupported or negative, listed explicitly | all |

## Split notebooks if a segment grows

Notebooks 05 and 08 are the likely candidates (e.g. `05a_fits`, `05b_calibration`). Splits are recorded in this table, not as cosmetic files.
