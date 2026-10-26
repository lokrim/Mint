# Prompt 2: generate the final-test report (after prompt 1 succeeded)

Paste everything below the line into a new Claude Code session in `/Users/lokrim/Code/mint`.

---

The pre-registered final-test analysis has finished (`runs/20261024-E5v3/e5_test.json` and `e5_v3.json`). Build the report with the reporting pipeline (`src/mint/report`, `runners/report_build.py`, `notebooks/build_final_report_notebook.py`). It copies numbers from those two files and never recomputes them.

**1. Preconditions (stop and tell me if any fails).**
- Both JSON files exist.
- `e5_v3.json` has `completeness_check.pass` true and a label containing "FINAL TEST".
- `.venv/bin/python -m pytest tests/test_report.py -q` passes.

**2. Build:**
```
.venv/bin/python runners/report_build.py --run_dir runs/20261024-E5v3
.venv-report/bin/python notebooks/build_final_report_notebook.py --execute --v3 runs/20261024-E5v3/e5_v3.json --v2 runs/20261024-E5v3/e5_test.json --out runs/20261024-E5v3/report
```
The report must say **"Status: FINAL TEST (one-time)"**. If it says INCOMPLETE or DEVELOPMENT, stop.

**3. Look at every figure** in `runs/20261024-E5v3/report/figures/` (light versions), checking for clipped labels, overlaps, off-scale points and empty panels.
- You may fix **presentation code only** in `src/mint/report/` (layout, labels, axis ranges), then rebuild and rerun `tests/test_report.py`.
- Never change a number, a statistic, the analysis code or the frozen files.

**4. Draft the interpretation** in a separate file, `planning/final_report_interpretation_DRAFT.md`, marked as a draft for the authors. Don't write it into `report.md`. In it:
- Answer the five questions in the report's "Interpretation (AUTHOR)" section, using only the report's numbers.
- Quote the pre-registered statements exactly.
- Keep three things apart: confirmatory (D-64 verdict, v2 rule, R1 − B-RAY statements), descriptive (PGD, B-NORM, realized-only, by agent count), and development numbers (blocks T and H, labelled as such).
- State the limits from the preregistration's `scope_limits`, and D-71.
- Make no novelty claim for ray support/traversal checks (see `planning/paper_plan.md`, attribution rules).

**5. Update the ledger and commit.**
- Update `planning/claim_evidence_ledger.csv` rows that this test now supports or refutes: status plus evidence pointer to the report section.
- Commit the report folder (`report.md`, figures, tables, `manifest.json`, the executed notebook), the draft and the ledger changes.

**6. Share:** offer to publish the report as a private artifact page, and wait for my yes.
