# E2: cost diagnosis and R1 uncertainty (development, block T, in-sample)

Run 2026-10-23.
- **Pre-registration:** [`runs/20261023-E2/preregistration.json`](../runs/20261023-E2/preregistration.json), committed in `d64a02b` before any E2 code ran.
- **Results:** `a1_substages.json`, `encode_isolation_check.json`, `a3_overhead_opencood.json`, `partB_bootstrap.json`, `partC_remove_fr.json` and `remove_fr/*.png`, all in `runs/20261023-E2/`.
- **Code:** [`e2_cost.py`](../runners/e2_cost.py), [`e2_rules.py`](../runners/e2_rules.py), [`pipeline.py`](../src/mint/reliability/pipeline.py) (optional sub-stage timer only), [`test_e2.py`](../tests/test_e2.py).

**Scope.** Everything here is **development / in-sample** on block T. R1 is frozen, nothing was downloaded, and no calibration or test scenario was opened. Timings are from an M1 CPU with 8 intra-op threads and 1 inter-op thread.

## Outcome: > 25% p95 band → stop

At n = 2, the best exact mode (batched, 24/24 identical to sequential) has an overhead of **33% p50 / 59% p95**. Post-processing was not the bottleneck, so no faster replacement was built (pre-registered trigger, step 2). The structural floor is the network forward of one counterfactual: **22% p50 / 30% p95** of the baseline. The 4 small scenarios are **not** recommended for streaming.

## Part A: cost

**A1. Sub-stages at n = 2** (sequential, OpenCOOD post-processing, 5 interleaved reps; p50 / p95 in ms)

| | Fusion | Deblocks + heads | candidates() | finalize() | effects() | Total |
|---|---|---|---|---|---|---|
| Plain path | 18.9 / 25.7 | 47.7 / 56.2 | 4.0 / 7.1 | 7.3 / 9.4 | n/a | 80.0 / 92.7 |
| Counterfactual stage | 18.9 / 22.7 | 45.6 / 53.7 | 3.8 / 4.7 | 6.3 / 8.9 | 1.8 / 2.1 | 77.3 / 88.9 |

- **(finalize + effects) share of the counterfactual stage: 10.1% p50 / 13.8% p95.** The 40% trigger is not met.
- NMS only sees 31–42 candidates per decode, so a vectorised NMS has little to save.
- Other stages: evidence 7.7 / 25 ms; compose 0 / 39 ms.

**Measurement caveat (found in A1, not pre-registered).** The receiver encode takes **0.136 s** p50 when timed alone (`encode_isolation_check.json`; the inter-op setting makes no difference). Right after the MINT stages it takes **0.23–0.32 s**.
- A mode's own *plain* time is also inflated by whatever ran before it: in batched mode the plain path measured 0.21 s, against 0.08 s sequential.
- A3 therefore times a baseline-only run (encode + plain) in the same sequence, shares it across both modes, and reports the isolated-encode version as a sensitivity check. That check uses a smaller denominator, so it gives a *higher* overhead.

**A3. Overhead (D-38) vs n.** OpenCOOD post-processing in both baseline and MINT; 3 reps; rule R1. Cells are p50 / p95. The "isolated" columns use the isolated-encode denominator.

| n | Sequential | Batched | Sequential, isolated (p95) | Batched, isolated (p95) | Forward share, best mode | Batched exact |
|---|---|---|---|---|---|---|
| 2 | 33% / 60% | 33% / **59%** | 76% | 85% | 22% / 30% | 24/24 |
| 3 | 72% / 107% | 64% / 90% | 130% | 101% | 53% / 60% | 24/24 |
| 4 | 135% / 264% | 132% / 282% | 262% | 285% | 121% / 132% | 24/24 |
| 5 | 187% / 300% | 182% / 300% | 312% | 301% | 158% / 186% | 24/24 |

- **n = 2.** MINT extra is 84–90 ms p50, of which counterfactual forward is 66–68 ms, post-processing 9 ms and evidence 7 ms.
- **n > 2.** Senders are replicated (timing only). Replicas make the counterfactuals near-null and force subset decodes on 1–3 frames, so the evidence and compose costs at n > 2 are not representative.
- **E1 comparison.** The n = 2 p95 (60%) is higher than E1's 47–52%. This is consistent with the run-to-run spread in the baseline.

## Part B: R1 uncertainty (404 frames; paired bootstrap, 2000 resamples)

| Condition | AP@0.7 undefended → R1 | Δ abs | Recovery | CI, scenario blocks (3) | CI, 10-frame blocks (42) |
|---|---|---|---|---|---|
| clean | 0.8737 → 0.8741 | +0.0003 | rel. loss −0.04% | −0.27% … 0.62% | −0.24% … 0.19% |
| spoof_feat | 0.8323 → 0.8392 | +0.0069 | 0.167 | **0.156 … 0.580** | **0.111 … 0.236** |
| remove_feat | 0.8631 → 0.8649 | +0.0017 | 0.162 | −0.256 … 0.530 | −0.040 … 0.412 |
| shift_feat | 0.8278 → 0.8358 | +0.0081 | 0.176 | **0.114 … 0.390** | **0.113 … 0.270** |
| spoof_pts | 0.8595 → 0.8634 | +0.0040 | 0.279 | **0.129 … 0.692** | **0.108 … 0.471** |
| mean of 4 families | | | 0.196 | **0.126 … 0.408** | **0.095 … 0.328** |

- **Recovery CIs exclude 0** for spoof_feat, shift_feat and spoof_pts and for the mean, under both bootstraps. **remove_feat does not.** The clean relative-loss CI includes 0 under both.
- Absolute deltas are 0.2–0.8 AP points. The Δ CIs exclude 0 for the same three families.
- The 3-block bootstrap is coarse: only 10 distinct resample sets exist.
- The 10-frame bootstrap is stratified by scenario, so it ignores between-scenario variation. It is optimistic.
- The numpy AP mirror equals OpenCOOD to 9e-14. Resampled frames keep their original order, because OpenCOOD's AP here does not sort globally.

## Part C: REMOVE false rejections (descriptive)

There are **28 unique cases**: 20/20/24/23/20 per condition (clean / spoof_feat / remove_feat / shift_feat / spoof_pts). 19 occur in all five conditions; 4 only in remove_feat and 4 only in shift_feat.

| Pre-registered class | n | What the cases look like |
|---|---|---|
| Label/IoU artefact | 11 | **4** have GT IoU 0.67–0.77 with the GT centre in the neighbouring tile: R1 restored a true positive and the tile-local label D scored it as harm. All 4 are remove_feat or shift_feat only. The other 7 sit on a labelled car with a wrong heading or offset (IoU 0.13–0.33). |
| Unclear | 11 | 10 are sparse returns from 1 or 2 scan lines on a wall or fence line at 55–117 m, with 3–9 points. One (case 27) is a duplicate squeezed between two GT cars that Y+ already detects; its support comes from their faces. |
| Receiver FP on unlabelled structure | 5 | Layered returns 0.3–1.8 m high on a compact footprint, or a sloped surface (case 0). |
| Genuine R1 error | 1 | Road-surface returns inside a low box 4.3 m from the receiver: ground contamination (D-33 / D-37). |

- The plot inspection agreed with every rule-based class (notes in the JSON).
- **15/28 cases rest on ≤ 6 rays** (SUP+TRAV). At 4/4 rays the Wilson lower bound is 0.51, i.e. R1's minimum resolvable evidence.
- Range is 4–117 m, median 58 m.

## Interpretation

1. **Cost is set by the network, not by post-processing.**
   - One counterfactual forward costs about 22–30% of the receiver's baseline on this CPU at n = 2, and grows about linearly with n.
   - No implementation change measured in E1 or E2 brings p95 near 10%.
   - Per the pre-registration, this stops here. Revising D-17 or the cost model is the user's decision and would be a post-hoc revision.
2. **R1's gain is small but resolvable in-sample** for 3 of 4 families. remove_feat is not distinguishable from 0, and clean is unchanged.
3. **About half the REMOVE "false rejections" are not R1 errors.** 11 are label/IoU artefacts, including 4 where R1 restored a true positive. Most of the 11 unclear cases look like unlabelled walls or fences seen with minimal evidence. Only 1 is clearly an R1 error (ground).
4. **None of this changes R1.** Every number above is development / in-sample on 3 scenarios.

Proposed log entries: [`decision_log_proposed_appendix.md`](decision_log_proposed_appendix.md) (D-42 to D-44, plus an open item).
