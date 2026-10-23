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

## Block H comparison (E5a-H; D-57)

Run 2026-10-24. **Development / quasi-held-out.** Block H is exposed (D-53): 4 scenarios, 371 frames, all with n = 2. B-RAY had never been run on H, and nothing was tuned. This is not a test result, and nothing was downloaded.
- **D-57** was committed first, in `e5fe9d6`, before any B-RAY number on H existed.
- **Frozen code.** The run used `e5_analyze.analyze` at `a9468e0`, unchanged. The new driver [`e5_block_h.py`](../runners/e5_block_h.py) only calls `analyze` and applies the D-57 rule.
- **Results:** [`e5a_H.json`](../runs/20261024-E5/H/e5a_H.json).
- **R1 reproduces E4 exactly.** All AP@0.7 and AP@0.5 values match `e4_heldout.json`.
  - Mean ΔAP@0.7 is +0.02233, 10-frame CI [0.0172, 0.0274].
  - The scenario CI is [−0.0035, 0.0315].
  - The clean relative loss is 0.31%, CI [0.01%, 0.68%].

**ΔAP@0.7 / ΔAP@0.5 vs no defense** (block H):

| Condition | No defense AP@0.7 / 0.5 | Ego-only | **B-RAY** | **R1** | R1-noREMOVE | Vis-limited oracle |
|---|---|---|---|---|---|---|
| clean | 0.8618 / 0.9101 | −0.210 / −0.173 | −0.0008 / −0.0013 | −0.0026 / −0.0013 | −0.0002 / −0.0001 | +0.0013 / +0.0124 |
| spoof_feat | 0.7740 / 0.8213 | −0.122 / −0.084 | +0.0490 / +0.0484 | +0.0397 / +0.0404 | +0.0417 / +0.0412 | +0.0479 / +0.0584 |
| remove_feat | 0.8274 / 0.8824 | −0.175 / −0.145 | −0.0005 / −0.0010 | −0.0009 / +0.0008 | +0.0011 / +0.0001 | +0.0012 / +0.0147 |
| shift_feat | 0.7726 / 0.8246 | −0.121 / −0.088 | +0.0393 / +0.0408 | +0.0323 / +0.0370 | +0.0343 / +0.0376 | +0.0420 / +0.0575 |
| spoof_pts | 0.8173 / 0.8647 | −0.165 / −0.128 | +0.0238 / +0.0239 | +0.0183 / +0.0201 | +0.0207 / +0.0212 | +0.0227 / +0.0344 |
| spoof_blind | 0.7643 / 0.8127 | −0.112 / −0.076 | +0.0032 / +0.0027 | +0.0009 / +0.0019 | +0.0026 / +0.0026 | +0.0045 / +0.0163 |

The attacker-unit oracle (bound) on spoof_feat / remove_feat / shift_feat / spoof_pts / spoof_blind is +0.076 / +0.009 / +0.055 / +0.042 / +0.086.

**Mean of the 4 original families, AP@0.7.** Each CI cell gives the 10-frame-block CI, then the 4-scenario CI.

| Method | Mean ΔAP@0.7 | CI | Clean relative loss | CI | Mean recovery |
|---|---|---|---|---|---|
| B-RAY | **+0.0279** | [0.0234, 0.0324] / [0.0071, 0.0403] | 0.09% | [−0.09, 0.26]% / [−0.13, 0.41]% | 0.38 |
| R1 | +0.0223 | [0.0172, 0.0274] / [−0.0035, 0.0315] | 0.31% | [0.01, 0.68]% / [−0.57, 2.03]% | 0.30 |
| R1-noREMOVE | +0.0244 | [0.0202, 0.0289] / [0.0064, 0.0350] | 0.02% | [−0.12, 0.15]% / [−0.14, 0.27]% | — |
| Ego-only | −0.146 | [−0.174, −0.119] / [−0.196, −0.126] | 24.3% | | — |

**R1 − B-RAY, paired ΔAP@0.7** (10-frame CI / scenario CI):
- **Mean of the 4 families: −0.0056, [−0.0090, −0.0023] / [−0.0173, +0.0032].**
- spoof_feat: −0.0093, [−0.0138, −0.0048].
- shift_feat: −0.0070, [−0.0121, −0.0018].
- spoof_pts: −0.0056, [−0.0092, −0.0022].
- remove_feat: −0.0004, [−0.0051, +0.0033].
- clean: −0.0018, [−0.0055, +0.0013].
- spoof_blind: −0.0024, [−0.0054, +0.0006].
- For comparison, R1 − R1-noREMOVE is −0.0021, [−0.0054, +0.0005].

**B-RAY dropped boxes** (GT-matched means BEV IoU ≥ 0.5 to a GT box):

| Condition | Dropped | GT-matched | Unmatched | Share of boxes KNOWN |
|---|---|---|---|---|
| clean | 16 | 9 | 7 | 0.85 |
| spoof_feat | 221 | 9 | 212 | 0.83 |
| remove_feat | 16 | 8 | 8 | 0.86 |
| shift_feat | 195 | 9 | 186 | 0.86 |
| spoof_pts | 121 | 9 | 112 | 0.84 |
| spoof_blind | 33 | 9 | 24 | 0.78 |

- The float16 cached scan and the float64 counts give the same B-RAY verdict on 894/895 clean ADD/SHIFT boxes, with identical counts on 880.
- **R1 on clean, by comparison:** it gates 87 units. 65 of them are false rejections of USEFUL units, and 59 of those 65 come from REMOVE gates.

**B-RAY overhead on H: not measured under D-42.** The E4 caches time only the dense and T(0.05) modes.
- The only B-RAY timing is from this analysis pass, on the float16 scan: 0.027 s p50 / 0.076 s p95 per frame, for 8 / 21 boxes. The JSON note for this timing says "block-T caches"; that wording is fixed in the frozen code.
- Dividing by E4's baseline (0.383 s p50) gives about 7% p50. That ratio mixes two runs, so it is not a D-42 figure.
- Dense R1 on the same frames (E4 timing, reproduced): 32% p50 / 54% p95. T(0.05): 15% / 43%.

### D-57, applied mechanically

The 10-frame CI lower bound of R1 − B-RAY is −0.0090, which is not > 0. **B-RAY becomes the final-test primary and R1 the key secondary.** On H the counterfactual is slightly *worse* than the box filter:
- **Where R1 loses:** in the three families B-RAY handles at the box level (spoof_feat, shift_feat, spoof_pts).
- **Clean cost:** R1's REMOVE gates cost it clean AP (−0.0026 vs −0.0008), and R1-noREMOVE sits between the two.
- **Scope:** this is n = 2 only and from an exposed block.

### Step 2 stopped: preregistration_v2.json not written

D-57 requires that **both methods are tested against no defense, with Holm correction over the two.** The frozen `e5_analyze.py` (`a9468e0`) cannot compute that:
- `bootstrap()` stores only 95% percentile CIs. It keeps no resample draws, no one-sided p-values, and no 97.5% CI, which a Holm step at α/2 would need.
- `criteria()` hard-codes R1 as the primary (`mean_delta_orig|R1`, `rel_loss|R1`) and R1 − B-RAY as the key secondary. It also emits the "not established" sentence keyed to that pair.

So v2 needs a code change, and under the task rule it stops here. v1 is unchanged. Nothing else in the frozen code needs to change. The B-RAY point estimate and its 95% CIs, including `rel_loss|B-RAY`, are already in the analysis output.

**Minimal change, for your decision.** Add a separate function, e.g. `criteria_v2()`, and leave `analyze` and `bootstrap` untouched. It would:
1. Re-run the scenario bootstrap (same seed, units and resamples) to get the one-sided bootstrap p-value of mean ΔAP@0.7 > 0 for B-RAY and for R1.
2. Apply Holm at α = 0.05 over the two.
3. Keep the clean-loss criterion for the primary. Should it also apply to the secondary? That is for you to decide.
4. Report R1 − B-RAY as the key secondary, with the wording below.

That would be a new frozen commit and new sha256 values in v2. Suggested key-secondary wording: "R1 − B-RAY paired ΔAP@0.7 (mean of 4 families; scenario CI). If the CI includes 0: 'the counterfactual's benefit over a box-level filter is not established'. If the CI upper bound < 0: 'the counterfactual underperforms a box-level filter'."
