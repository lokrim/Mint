# Prompt 1: run the pre-registered final-test analysis (evaluation phase)

Paste everything below the line into a new Claude Code session in `/Users/lokrim/Code/mint`.

---

Approved: run the one-time pre-registered analysis of the MINT final test, per `runs/20261024-E5/preregistration_v3_2.json` (frozen code `c883753`, D-71). The stream in `runs/20261024-E5v3` has finished. This runs on this Mac only.

**1. Preconditions (read-only; stop and tell me if any fails).**
- `runs/20261024-E5v3/run.log` ends with `post-run frozen check: OK` and `all done`; no `v3_2_stream.py` process is running.
- `cache/` and `v3extra/` each hold 15 `.pkl.gz` files and no `.tmp` files; `download_ledger.json` has 15 downloads, all `complete`.
- `git merge-base --is-ancestor c883753 HEAD` succeeds.
- `.venv/bin/python runners/v3_2_stream.py --run_dir runs/20261024-E5v3 --dry_run` prints `frozen sha256 + OpenCOOD commit verified` (no network).
- Neither `runs/20261024-E5v3/e5_test.json` nor `e5_v3.json` exists yet. If either exists, stop and ask me.

**2. Run the two pre-registered analyses, in this order** (the v3 analysis checks itself against the frozen v2 output). Each can take 1–2.5 h. Run each in the background with `caffeinate`, wait for its completion notification, and don't poll:
```
caffeinate -ims .venv/bin/python runners/e5_analyze.py test --run_dir runs/20261024-E5v3 > runs/20261024-E5v3/analysis_e5.log 2>&1
caffeinate -ims .venv/bin/python runners/v3_analyze.py test --run_dir runs/20261024-E5v3 --prereg runs/20261024-E5/preregistration_v3_2.json > runs/20261024-E5v3/analysis_v3.log 2>&1
```
`--prereg …v3_2.json` is required: the script's default is the v3 file, which lacks the D-70 conditions.

**3. Procedural checks after both finish (stop and report if any fails; never rerun or work around):**
- `e5_v3.json` → `completeness_check.pass` is true (15/15 scenarios, 2066/2066 frames).
- `e5_v3.json` → `consistency_vs_frozen_v2.identical` is true.
- `e5_test.json` → `numpy_ap_vs_opencood_max_abs_diff` is tiny (below 1e-9), and every scenario has `compose_all_identical` true.
- The `--dry_run` hash check above still passes.

**4. Report back, quoting the files and not interpreting beyond them:**
- The D-64 verdict string, and the v2 rule pass/fail under each AP definition (global-ranking AP is the headline).
- The B-RAY and R1 co-test (ΔAP, one-sided p, Holm decision) and B-RAY's clean-loss CI, per AP definition.
- The R1 − B-RAY statements, exactly as emitted.
- Headline mean ΔAP@0.7 over the 4 original attacks per method, with scenario and 10-frame CIs (AP points), both definitions.
- B-NORM catch rates and stealth-infeasible counts for the PGD conditions (descriptive).
- Label everything **"FINAL TEST (one-time)"**. Keep development numbers (blocks T and H) separate if you mention them.

**5. Record and commit.**
- Add a row for the 15 test scenarios to `planning/exposure_ledger.csv` (role: final test; seen: the analysis outputs).
- Commit `e5_test.json`, `e5_v3.json` and the ledger row. The logs are gitignored. Leave out the caches and the unrelated `runs/20261023-E4/dev_blind/run.log`.

**Rules (pre-registered):** never change code, criteria, thresholds, seeds or bootstrap settings. Don't rerun an analysis with different options. Run no extra or "rescue" analysis presented as confirmatory. A failure is reported as the result. Don't build the report in this session; that's prompt 2.
