# MINT paper draft (IEEEtran, conference)

Working title: *MINT: Physically Verified Counterfactual Gating for Robust Cooperative LiDAR Perception*.

**Status (2026-10-27): revision skeleton.** `main.tex` was rebuilt from the revision action plan (problem → gap → method → evidence → interpretation; target 8–9 pages before the supplementary material). All sections are written; no placeholders remain. The method is named **MINT** (`\mint`, full name `\mintfull` = "Message INfluence Testing", defined once in the preamble); the name "R1" is retired everywhere, including generated tables, macro names and figures. The previous evaluation-centred draft is kept at `archive/main_evaluation_draft.tex` (it uses the old `RONE` macro names and no longer compiles against `numbers.tex`).

## Revision schedule (skeleton v2, 2026-10-27)

Both evaluation sets appear in every results subsection: the OPV2V test (primary, confirmatory) first, Culver City (unseen town, simulated sensor; secondary, descriptive) second, never pooled.

| # | Section | Pages | Main items |
|---|---|---|---|
| – | Abstract | 0.3 | problem, gap, objective, MINT, OPV2V + unseen town, AP-definition dependence, societal relevance |
| 1 | Introduction | 1.0 | problem → difficulty → gap → "Hence, this work investigates…" → 3 contributions |
| 2 | Related Work | 1.0 | fusion; attacks (incl. adaptive); consensus/anomaly defenses; sensor-grounded checks; positioning + Table (positioning) |
| 3 | Problem Formulation and Threat Model | 0.4 | setting, threat model, defender's goal and trusted evidence |
| 4 | The MINT Method | 1.8 | intuition, Algorithm 1, method figure (to be simplified to 5 stages), attribution, ray verification + Wilson margin, gating/composition, baselines |
| 5 | Experimental Setup | 1.0 | both datasets (Table splits), attacks (Table attacks), two AP definitions, pre-registered protocol, environment |
| 6 | Results | 1.8 | does it help (Table verdict, forest plot); which attacks (Table conditions); ablation (MINT-noREMOVE); what is not defended; costs (Table clean); optional qualitative figure |
| 7 | Discussion | 1.0 | why verification helps; why the AP definition flips the ranking; transfer to the unseen town; practical implications; limitations and threats to validity |
| 8 | Conclusion and Future Work | 0.3 | no limitations list |
| – | References | ~0.6 | |
| A–E | Supplementary | – | pre-registration history; development vs test; full per-condition tables; implementation details + runtime; harm labels + agent count |

Suggested writing order (each later section depends on the earlier ones being fixed): 3 Problem/Threat model → 4 Method → 5 Setup → 6 Results → 7 Discussion → 2 Related Work → 1 Introduction → 8 Conclusion → Abstract.

## Files

| Path | What |
|---|---|
| `main.tex` | The paper. Every result number is a macro from `numbers.tex` or a table from `tables/`. |
| `numbers.tex` | Generated. ~1,250 `\newcommand` macros (Culver City macros are prefixed `\Cul`) (AP points = AP × 100). MINT macros contain `MINT`/`Mint` (e.g. `\VGlobMINTDelta`, `\MintCleanGated`), the ablation `MINTNoRem`/`MintNoRem`; the values are identical to the former `RONE`/`Rone`/`RNoRem` macros (checked by diff, 2026-10-27). |
| `tables/*.tex` | Generated table bodies. In the paper: splits (`tab_splits`), attacks on both sets (`tab_attacks_both`), verdict test vs Culver (`tab_verdict_both`, full width), per-condition B-RAY/MINT test vs Culver (`tab_conditions`, full width), clean cost (`tab_clean_both`), runtime (`tab_runtime_both`); appendix: development vs test (`tab_dev_vs_test`), every defense and condition for both sets (`tab_full_global`, `tab_full_frame`, full width). `tab_main_{global,frame}` are kept as the cross-check for `tab_full_*`; `tab_verdict`, `tab_clean`, `tab_runtime`, `tab_attacks` and `tab_culver` are still generated but no longer used. |
| `figures/mint_method.tex` | MINT methodology figure (TikZ, `figure*`, drawn at final size, no scaling), label `fig:mintmethod`. The R1-named original, its notes and preview SVG are in `archive/`. |
| `figures/forest.pdf` | Forest plot (test vs Culver, both AP definitions); `forest.png` is a preview. |
| `figures/forest.py` | Regenerates the forest plot from both `e5_v3.json` files (asserts equality with `criteria_v3` and the report CSVs). Needs matplotlib: `.venv-report/bin/python paper/figures/forest.py`. |
| `figures/0*.png` | Copied unchanged from `runs/20261024-E5v3/report/figures/`; no longer used by `main.tex` (kept for reference). |
| `refs.bib` | Subset of `planning/literature/references.bib`, entries unchanged except that the provenance `note={access: ...}` field is renamed `mintaccess` so it does not print. |
| `gen_numbers.py` | Regenerates `numbers.tex` and `tables/` from the frozen outputs (stdlib only). |
| `mint_paper_overleaf.zip` | What Overleaf needs: `main.tex`, `numbers.tex`, `refs.bib`, `figures/mint_method.tex`, `figures/forest.pdf`, the nine tables used by `main.tex`, and `archive/main_evaluation_draft.tex` for reference. |

## Regenerate numbers

From the repository root (needs the run outputs, not on Overleaf):

```bash
python3 paper/gen_numbers.py
.venv-report/bin/python paper/figures/forest.py
```

Sources read: `runs/20261024-E5v3/e5_v3.json`, `e5_test.json`, `report/tables/*.csv`; `runs/20261024-E5/preregistration_v3_2.json`; `runs/20261024-E5/dev/e5a_dev.json`, `H/e5a_H.json` (block sizes); `runs/20261024-AUDIT/X0_global_sort_bootstrap.json` (development T/H under both AP definitions); `planning/e4_report.md` (timing machine string); `runs/20261026-CULVER/e5_v3.json`, `e5_test.json`, `plan.json`, `sanity_first_scenario.json` (Culver City, secondary held-out domain shift, D-72; the script refuses them unless the label says CULVER CITY and the 4-scenario / 550-frame completeness check passed). The script asserts that the report CSVs equal `e5_v3.json` where they overlap.

## Compile on Overleaf

1. New Project → Upload Project → `mint_paper_overleaf.zip`.
2. Menu → Compiler: pdfLaTeX; Main document: `main.tex`. `IEEEtran.cls` and `IEEEtran.bst` are provided by Overleaf (not vendored here).
3. Compile (BibTeX runs automatically).

**Local compile (2026-10-27).** Compiled with `tectonic` (XeTeX, TeX Gyre Termes standing in for Times; Overleaf uses pdfLaTeX with Times, so line breaks can differ slightly): 11 pages, 0 overfull boxes, every figure and table at natural size (no `\resizebox` on tables). To reproduce from `paper/`, copy the sources to a scratch folder, add `\usepackage{fontspec}\setmainfont{TeX Gyre Termes}` after `\IEEEoverridecommandlockouts` in the copy only, and run `tectonic main.tex`.

**Layout rules used** (IEEE conference): all floats `[!t]`; table captions above, figure captions below; single-column tables in `\footnotesize` (wide CI blocks in `\scriptsize`), full-width tables as `table*`; appendices before the acknowledgment and the references. Table bodies are read with `\tabin{...}` (the primitive `\@@input`), not `\input`: since LaTeX 2020-10 `\input` is robust, and a `\bottomrule` after an `\input`-ed tabular body fails with "Misplaced \noalign", which silently drops table rules on Overleaf.

## Page layout

Full draft (2026-10-27): abstract to the end of Data and Code Availability fits in 9 pages (about 8.85); references start on page 9; Appendices A--D (implementation, harm labels, pre-registration history, additional results with the large tables last) follow on a new page; 14 pages in all.

## TODO left in the draft

- `\TODO{...}`: authors, affiliation, email, funding/acknowledgements, venue, Data and Code Availability (repository URL, frozen commit, checksums).
- `[CITATION NEEDED]`: none left in `main.tex` (MVIG, PASCAL VOC, pre-registration, Holm, CARLA, Wilson and the bootstrap are now cited from `refs.bib`).
- `refs.bib` entries marked `PRIOR-KNOWLEDGE` or "verify" in `mintaccess` (e.g. `madry2018pgd`, `cao2019advlidar`, `carlini2019evaluating`, `tramer2020adaptive`, `benjamini1995fdr`, venue of `tao2026gcp`, `zhao2024made`) need their bibliographic details checked. `zhang2026poseguard`, `liu2026trustflip`, `he2026glst` are preprints.
- The Related Work line on GLST is based on its title and a skim only.

## Could not verify from the listed files

- **Timing machine.** `e5_test.json` does not record the hardware. "Apple M1 CPU, 8 threads" is taken from `planning/e4_report.md` (the development timing protocol) and decision D-10; the test is assumed to have run on the same machine.
- **Frame-order AP ordering within a frame.** The AP equation (`eq:ap`) describes OpenCOOD's frame-order accumulation as concatenation frame by frame; the within-frame order is as in OpenCOOD's code and was not re-read.
- **Exact PGD loss weights** are paraphrased from `preregistration_v3_1.json` (`pgd_families.threat_model.objectives`).
- The report cites `preregistration_v3_2.json` as governing; it equals v3.1 plus D-71 only. The paper cites the v3 history (v1, v2, v3, v3.1, v3.2) from `decision_log_proposed_appendix.md`.

## Provenance of the test results

`runs/20261024-E5v3/e5_v3.json` (sha256 `70324a707f23e20b…`) and `e5_test.json` (sha256 `4b6823ba3603420a…`), as listed in `runs/20261024-E5v3/report/report.md`.

Culver City (secondary; unseen town, simulated sensor; unseen during detector training and during all MINT development; not real-sensor data): `runs/20261026-CULVER/e5_v3.json` (sha256 `fa6325dee8058bac…`) and `e5_test.json` (sha256 `5d4481334d983c9c…`), report `runs/20261026-CULVER/report/report.md`. Never pooled with the test.
