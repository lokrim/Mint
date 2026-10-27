# MINT paper draft (IEEEtran, conference)

Working title: *Physically Verified Counterfactual Gating for Robust Cooperative LiDAR Perception: A Pre-registered Evaluation*.

## Files

| Path | What |
|---|---|
| `main.tex` | The paper. Every result number is a macro from `numbers.tex` or a table from `tables/`. |
| `numbers.tex` | Generated. ~1,050 `\newcommand` macros (Culver City macros are prefixed `\Cul`) (AP points = AP × 100). |
| `tables/*.tex` | Generated table bodies: splits (I), attacks (II), main results global / frame-order (III a/b), verdict (IV), clean cost (V), runtime (VI), development vs test (VII), OPV2V test vs Culver City (VIII, `tab_culver.tex`). |
| `figures/*.png` | Copied unchanged from `runs/20261024-E5v3/report/figures/` (light versions). |
| `refs.bib` | Subset of `planning/literature/references.bib`, entries unchanged except that the provenance `note={access: ...}` field is renamed `mintaccess` so it does not print. |
| `gen_numbers.py` | Regenerates `numbers.tex` and `tables/` from the frozen outputs (stdlib only). |
| `mint_paper_overleaf.zip` | Everything above, ready to upload. |

## Regenerate numbers

From the repository root (needs the run outputs, not on Overleaf):

```bash
python3 paper/gen_numbers.py
```

Sources read: `runs/20261024-E5v3/e5_v3.json`, `e5_test.json`, `report/tables/*.csv`; `runs/20261024-E5/preregistration_v3_2.json`; `runs/20261024-E5/dev/e5a_dev.json`, `H/e5a_H.json` (block sizes); `runs/20261024-AUDIT/X0_global_sort_bootstrap.json` (development T/H under both AP definitions); `planning/e4_report.md` (timing machine string); `runs/20261026-CULVER/e5_v3.json`, `e5_test.json`, `plan.json`, `sanity_first_scenario.json` (Culver City, secondary held-out domain shift, D-72; the script refuses them unless the label says CULVER CITY and the 4-scenario / 550-frame completeness check passed). The script asserts that the report CSVs equal `e5_v3.json` where they overlap.

## Compile on Overleaf

1. New Project → Upload Project → `mint_paper_overleaf.zip`.
2. Menu → Compiler: pdfLaTeX; Main document: `main.tex`. `IEEEtran.cls` and `IEEEtran.bst` are provided by Overleaf (not vendored here).
3. Compile (BibTeX runs automatically).

The draft was **not compiled locally** (no LaTeX installed). Static checks passed: balanced braces and environments in `main.tex` and every table, every macro used is defined, every `\cite` key is in `refs.bib`. Expect to fix small layout issues (TikZ placement in Figs. 1–2, float positions) on the first Overleaf compile.

## Page estimate

About 5,000 words of text plus 8 figures (2 TikZ, 6 PNG) and 9 tables (2 full width): roughly 9–10 pages including references. To reach 8 + references, candidates to cut or move to an appendix: Fig. 6 (B-NORM catch, also in the text), Fig. 8 (R1 − B-RAY), Table VII, and the Related Work paragraphs on anomaly defenses.

## TODO left in the draft

- `\TODO{...}`: authors, affiliation, email, funding/acknowledgements, venue, Data and Code Availability (repository URL, frozen commit, checksums).
- `[CITATION NEEDED]` (no entry in `references.bib`; never invented): MVIG (Tao et al., CVPR 2026, arXiv 2602.19596 per the audit); PASCAL VOC AP; pre-registration practice; Holm (1979); CARLA simulator. Wilson (1927) and the bootstrap are used without a citation; add them if the venue expects it.
- `refs.bib` entries marked `PRIOR-KNOWLEDGE` or "verify" in `mintaccess` (e.g. `madry2018pgd`, `cao2019advlidar`, `carlini2019evaluating`, `tramer2020adaptive`, `benjamini1995fdr`, venue of `tao2026gcp`, `zhao2024made`) need their bibliographic details checked. `zhang2026poseguard`, `liu2026trustflip`, `he2026glst` are preprints.
- The Related Work line on GLST is based on its title and a skim only.

## Could not verify from the listed files

- **Timing machine.** `e5_test.json` does not record the hardware. "Apple M1 CPU, 8 threads" is taken from `planning/e4_report.md` (the development timing protocol) and decision D-10; the test is assumed to have run on the same machine.
- **Frame-order AP ordering within a frame.** The AP equation (`eq:ap`) describes OpenCOOD's frame-order accumulation as concatenation frame by frame; the within-frame order is as in OpenCOOD's code and was not re-read.
- **Exact PGD loss weights** are paraphrased from `preregistration_v3_1.json` (`pgd_families.threat_model.objectives`).
- The report cites `preregistration_v3_2.json` as governing; it equals v3.1 plus D-71 only. The paper cites the v3 history (v1, v2, v3, v3.1, v3.2) from `decision_log_proposed_appendix.md`.

## Provenance of the test results

`runs/20261024-E5v3/e5_v3.json` (sha256 `70324a707f23e20b…`) and `e5_test.json` (sha256 `4b6823ba3603420a…`), as listed in `runs/20261024-E5v3/report/report.md`.

Culver City (secondary held-out domain shift; simulated, real-city layout, unseen during detector training and during all MINT development; not real-sensor data): `runs/20261026-CULVER/e5_v3.json` (sha256 `fa6325dee8058bac…`) and `e5_test.json` (sha256 `5d4481334d983c9c…`), report `runs/20261026-CULVER/report/report.md`. Never pooled with the test.
