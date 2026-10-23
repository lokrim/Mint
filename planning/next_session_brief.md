# Next-session brief

Updated 2026-10-23, after the Stage-2 checks.

## Where we are

- **Stage 1 (OPV2V) done.**
  - V-01: AP@0.7 0.8155 vs 0.815.
  - V-03: locality 93/93.
  - V-05: message 15.77 MB/sender dense fp32.
  - V-02: own-frame + warp drops AP@0.7 to 0.515, so the OPV2V study uses OpenCOOD's `proj_first` coordinate convention (D-13b, user decision 2026-10-23). The threat model §6 separates what the code does from deployment assumptions A-P1..A-P4.
- **Stage 2 done on 3 validate scenarios** ([stage2_report.md](stage2_report.md)):
  - 64-ring receiver geometry recovered;
  - no-returns proven not free;
  - self-box rule (D-24);
  - coverage gate passed (49.7%), but only 30% of useful ADD effects are receiver-visible;
  - dev pilot support-ratio AUROC 0.82 (ADD, n_harmful = 13) and 0.80 (REMOVE).
- **Disk:** about 41 GB free; no raw data on disk.

## Waiting on you

1. **Your broader methodology review** before the final MINT-v0 design is fixed. Per your instruction (2026-10-23): **no further validate downloads and no Stage 3** until then.
2. After that review: whether to stream the remaining validate data. That is 4 small scenarios (≈ 2.9 GB) plus 2 large ones (11.1 GB, 21.7 GB) needed for a usable calibration block (R-20).

## Candidate next actions (only after the review and approval)

1. Stage 3:
   - empty-region sampling for the ∅ model;
   - beta-binomial fits of μ, φ (genuine vs empty) by range bin on block T, with posterior-predictive checks;
   - effect-level log-BF;
   - isotonic calibration on block C;
   - baselines M1 and B-LUCIA.
2. Notebooks 02–04 executed from the cached run records (no re-download).

## Do not

- Download over 5 GB without asking.
- Use the 3 pilot scenarios for calibration (D-25).
- Run MINT or attacks on test scenarios before the freeze.
- Treat no-return slots as free.
