# E5a: baselines, ablation and final-test pre-registration

Run 2026-10-24. **Development, block T only** (3 scenarios, 404 frames, n = 2–4; in-sample). No download. Block H was not used for anything.
- **Proposals:** D-55 and D-56 were recorded first, in `03b512f` (appendix only).
- **Frozen code:** `a9468e0`. It contains [`baselines.py`](../src/mint/reliability/baselines.py), [`e5_stream.py`](../runners/e5_stream.py), [`e5_analyze.py`](../runners/e5_analyze.py) and [`test_e5.py`](../tests/test_e5.py). The full suite passes: 66 tests.
- **Results:** [`e5a_dev.json`](../runs/20261024-E5/dev/e5a_dev.json).
- **Pre-registration:** [`preregistration.json`](../runs/20261024-E5/preregistration.json). It is not run.

## Methods (D-56; none has a tunable parameter)

- **B-RAY.** For every final Y+ box, the receiver's ray counts are computed with R1's code (`classify_points`, std count). A box is dropped iff it is KNOWN and the Wilson-95 upper bound of s is < 0.5. A test checks that this equals R1's ADD gate on 500 random count pairs.
- **Ego-only.** `cands[all senders excluded]`.
- **R1-noREMOVE.** REMOVE "gate" verdicts become "none"; the mirror conditions are unchanged.
- **R1 is unchanged.** `r1.py` has the same sha256 as in E4.

## Development check (block T, in-sample; AP@0.7, Δ vs no defense)

| Condition | No defense | Ego-only | B-RAY | **R1** | R1-noREMOVE | Vis-limited oracle |
|---|---|---|---|---|---|---|
| clean | 0.8737 | −0.293 | −0.0001 | **+0.0003** | +0.0008 | +0.0020 |
| spoof_feat | 0.8323 | −0.251 | +0.0081 | **+0.0069** | +0.0071 | +0.0085 |
| remove_feat | 0.8631 | −0.282 | −0.0001 | **+0.0017** | +0.0008 | +0.0034 |
| shift_feat | 0.8278 | −0.247 | +0.0080 | **+0.0081** | +0.0069 | +0.0165 |
| spoof_pts | 0.8595 | −0.279 | +0.0037 | **+0.0040** | +0.0044 | +0.0060 |
| mean of 4 | | −0.265 | +0.0049 | **+0.0052** | +0.0048 | |

- **R1 reproduces E1/E2 exactly.** NumPy AP matches OpenCOOD to 1e-13, and 42/42 compose checks are identical.
- **R1 − B-RAY, mean of 4 families:** +0.0003. The 10-frame CI is [−0.002, +0.002]. The 3-scenario CI is [−0.005, +0.0003]; with only 3 blocks it is coarse and does not even contain the point estimate.
  - By n, R1 − B-RAY is −0.005 at n = 2, 0.000 at n = 3 and +0.0004 at n = 4.
  - **On development data, the counterfactual adds nothing measurable over a box-level ray filter.** The pre-registered key secondary is therefore likely to report "not established".
- **noREMOVE removes all 20–24 false rejections of USEFUL units.** Gated-unit precision rises from 0.71–0.89 to 0.71–0.98. The mean Δ is about the same (+0.0048), and remove_feat drops from +0.0017 to +0.0008.
- **B-RAY drops 12 clean boxes**, 7 of which match GT. Under the spoof attacks it drops 78–139 boxes, 91–95% of them unmatched to GT.
- **B-RAY cost (development):** 0.055 s p50 / 0.126 s p95 per frame for about 15 boxes. These figures are from the float16 cache. The float16 ray counts give the same verdict as the float64 counts on 1504/1504 boxes (identical counts on 1475).
  - D-42 overhead on the 24-frame dev slice (smoke test): 10% p50 / 18% p95 at n = 2, against 39% / 64% for dense R1.

## Pre-registered final test (`runs/20261024-E5/preregistration.json`)

- **Data and methods.** 15 test scenarios (D-55; 2066 frames; n = 1–5). Methods as D-56. Attacks: the 4 original families + spoof_blind, with the E4 seeds.
- **Primary metric.** Mean ΔAP@0.7 of R1 over the 4 original families.
  - Primary CI: scenario bootstrap (15 blocks).
  - Secondary CI: 10-frame-block bootstrap.
- **Success requires both:**
  - primary CI low > 0;
  - clean relative loss CI high ≤ 1% (scenario bootstrap).
- **Key secondary.** R1 − B-RAY paired ΔAP@0.7 with a scenario CI. If that CI includes 0, the report must state "the counterfactual's benefit over a box-level filter is not established". The code emits this sentence.
- **Strata by agents.** n = 2 / 3 / 4+ for ΔAP and for overhead (dense, T(0.05), B-RAY). Only the 10-frame CI is reported for the 4+ stratum, because it covers about 2 scenarios. n = 1 frames are pooled, not stratified.
- **Scope limits (D-54).** spoof_blind and n-coverage are reported next to the headline.
- **Stream.**
  - Ranged reads of the V-01 test archive, restricted to the allowlist. The runner refuses `2021_08_23_12_58_19` and any validate scenario.
  - Budget 22e9, checked before the first data byte. Planned: 20.44e9 × 1.01 = 20.64e9.
  - One scenario at a time, ≤ 3e9 raw (largest 2.62e9), raw deleted after the cache is re-read.
  - The runner refuses to start without `--user_approved`.
- **Estimated runtime:** about 8 h (range 7–10 h). That is about 0.5 h of download and about 7.5 h of processing; the n = 4–5 scenario alone takes about 1.4 h.

**Fixed before freezing (no method change).** Smoke tests on the dev slice exposed two n = 1 crashes in the new stream's timing code. The trigger path has no senders, and a progress print assumed a dense timing record. Block H never had n = 1. Both are fixed; `pipeline.py` is untouched.

**Waiting on you:** approval of the ~20.4 GB test stream. Nothing has been downloaded.
