# E3: candidate-tile counterfactual (development, block T, in-sample)

Run 2026-10-23.
- **Pre-registration:** [`runs/20261023-E3/preregistration.json`](../runs/20261023-E3/preregistration.json), committed in `cb442af` before any E3 code ran. It also records the block-T re-stream you approved, which was never needed (see Scope).
- **Results:** `step1_tile_exactness.json` and `step1_diagnostic.json` in `runs/20261023-E3/`.
- **Code:** [`e3_cost.py`](../runners/e3_cost.py); [`pipeline.py`](../src/mint/reliability/pipeline.py) (`cf_mode="trigger"`, `trigger_mask`, `gather_tiles`, `trigger_heads`); [`compose.py`](../src/mint/fusion/compose.py) (`tile_candidates`); [`test_e3.py`](../tests/test_e3.py).

**Scope.** Development / in-sample on the 24-frame dev slice of block T (n = 2). R1 is frozen. Nothing was downloaded: the run stopped at step 1, before the approved re-stream. No calibration or test data was touched. Hardware: M1 CPU, 8 intra-op threads.

## Outcome: step 1 fails as pre-registered → stop

The criterion was max |tile − dense| ≤ 1e-5 on psm and rm, on 24/24 frames. Steps 2–4 were **not run**: no 404-frame recall or AP, no overhead measurement, no projection. So no PASS, PARTIAL or FAIL band applies.

| Tile set | Frames ≤ 1e-5 | Max abs diff | Candidate anchor indices = dense restricted | Max candidate score / corner diff | Tile fraction mean (min–max) |
|---|---|---|---|---|---|
| T(0.05) | **22/24** | 1.24e-5 | 24/24 | 9.2e-7 / 7.6e-6 m | 0.213 (0.145–0.257) |
| T(0.10) | **23/24** | 1.14e-5 | 24/24 | 9.2e-7 / 7.6e-6 m | 0.142 (0.122–0.180) |
| All 572 tiles (reference) | 7/24 | 1.53e-5 | 24/24 | 9.2e-7 / 7.6e-6 m | 1.0 |

Failing frames: f = 0.05 fails on frames 5 and 15; f = 0.10 fails on frame 5.

## Why it is not within 1e-5 (diagnostic, run after the failure)

| Stage | Max abs diff, tile path vs dense |
|---|---|
| Fusion (`fuse_scale` on gathered tiles), all 3 scales | **0 (bitwise equal)** |
| Deblocks + heads (`decode_batch` on the dense-fused tiles) | 1.24e-5 (all of the deviation) |

- **Cause: floating-point rounding, not a pixel-locality violation.** The deblocks (ConvTranspose, kernel = stride) and the 1×1 heads compute the same function on an 8×8 tile as on the full map. The convolution kernels accumulate in a different order at a different spatial size.
- **Size.** The worst elements are 12–13 float32 ULPs (relative 1.3e-6). They are all on cls logits of −9 to −15, i.e. probability ≤ 1.3e-4, far from the 0.20 score threshold. A 1e-5 absolute tolerance is about 10 ULP at that magnitude.
- **Candidates are unchanged.** The candidate sets (anchors above 0.20) have identical indices on 24/24 frames. Scores differ by ≤ 9.2e-7 and corners by ≤ 7.6e-6 m.
- **Not tested** (steps 2–4 were not run): whether such differences ever flip NMS, effects or R1 decisions.

## Interpretation

1. **The method is exact in fusion and pixel-local in decode, but not bitwise equal.** It misses the pre-registered 1e-5 bound by up to 2.4e-6 on 2 frames (f = 0.05) and 1 frame (f = 0.10). Per the pre-registration this is a stop.
2. **Possible next steps (your decision; any of them is a post-hoc revision):**
   - Accept a relative or ULP tolerance for step 1, e.g. ≤ 16 ULP, or the identical-candidate-set test that already passes 24/24. Then run steps 2–4 under the same pre-registration and the approved re-stream.
   - Re-define "exact" as identical candidate sets after the score threshold.
3. **Tile fractions (incidental, from step 1, clean, n = 2).** The trigger keeps 14% (f = 0.10) to 21% (f = 0.05) of tiles. This is **not** an overhead measurement: per-tile decode cost and fixed costs (evidence, compose, post-processing ≈ 10% of the counterfactual stage in E2) were not measured.

Proposed log entries: [`decision_log_proposed_appendix.md`](decision_log_proposed_appendix.md) (D-45 and an open item).

## Step 1 under the corrected criterion (D-46): fails → stop; steps 2–4 not run

Development / in-sample, 24-frame dev slice of block T (n = 2). **Correction:** you set it on 2026-10-23, after the original step-1 failure above and before any step 2–4 result existed. It is recorded in `preregistration.json` → `correction_2026-10-23` (commit `201b362`) and as proposed D-46. The JSON from the first step-1 run had no per-element ULP counts, so step 1 alone was re-run: `python runners/e3_cost.py exact_ulp`, written to [`step1_revised.json`](../runs/20261023-E3/step1_revised.json). Nothing was downloaded: the block-T re-stream was not started, 0 bytes. No calibration or test data was touched.

| Tile set | (a) candidate indices = dense restricted | (b) score ≤ 1e-5 and corner ≤ 1e-4 m | (c) all psm/rm ≤ 32 ULP | All three |
|---|---|---|---|---|
| T(0.05) | 24/24 | 24/24 (max 9.2e-7 / 7.6e-6 m) | **0/24** | **0/24** |
| T(0.10) | 24/24 | 24/24 (max 9.2e-7 / 7.6e-6 m) | **0/24** | **0/24** |
| All 572 tiles (reference) | 24/24 | 24/24 | 0/24 | 0/24 |

**Part (c) detail.**

| Tile set | Elements over 32 ULP | Max ULP, psm | Max ULP, rm |
|---|---|---|---|
| T(0.05) | 135,505 of 2,966,016 (4.6%) | 9,255 | 1,367,408 |
| T(0.10) | 86,671 of 1,984,000 (4.4%) | 9,255 | 1,367,408 |

- **Where the failures are.** About 5% of rm elements and 0.04–0.07% of psm elements exceed 32 ULP.
- **Why.** The failing elements are values near zero. Example: a dense rm value of 2.4e-7 differs by 1.9e-8, which is 1.37 million ULP of that value. The same accumulation-order rounding gives an absolute error of a fixed size, about 1e-8 to 4e-6 here. Near zero that error is a very large number of ULPs of the result.
- **Absolute size is unchanged.** Among the worst ULP elements, the largest absolute diff is 3.9e-6. Fusion is still bitwise equal (diagnostic above).
- **The dense-equivalent path fails too.** The all-572-tile path fails (c) on 0/24 frames, so a per-element ULP bound relative to the dense value does not separate "tile path" from "dense recomputation". It fails for the same reason the 1e-5 absolute bound did.

**Outcome:** the corrected criterion fails on 24/24 frames. Per your instruction, steps 2–4 were **not run**: no re-stream, no effect recall, no NMS/effect/R1 disagreement counts, no AP, no overhead. No PASS, PARTIAL or FAIL band applies. Parts (a) and (b), the candidate-level checks, pass 24/24 at both f.

**Possible next step (your decision; it would be a second post-hoc correction):** a bound that does not use the dense value's own ULP near zero. Examples: ULPs of max(|dense|, 1) or of the tensor's scale, or an absolute bound per head set from the all-tile reference path. Or (a)+(b) alone. Nothing here is proposed as a rule; see the open item in the appendix.

## Steps 2–4 under the final step-1 criterion (D-48): FAIL

Development / in-sample, block T only (3 scenarios, 404 frames, clean + 4 families). R1 frozen (`v0.Params()`). No calibration or test scenario was downloaded, opened or referenced.

**Second correction (D-48).** You set it on 2026-10-23, before any step 2–4 result existed. It is recorded in `preregistration.json` → `correction_2_2026-10-23`, commit `6929ab2`. Criterion (c) is dropped; step 1 = (a) + (b) on 24/24 frames. This is the last change to step 1. Steps 2–4 and the outcome bands are unchanged.

- **Code:** [`e3_equiv.py`](../runners/e3_equiv.py) (`step1`, `stream`, `analyze`, `project`); [`e3_cost.py`](../runners/e3_cost.py) `overhead` (unchanged); tests in [`test_e3.py`](../tests/test_e3.py).
- **Results** in `runs/20261023-E3/`: `step1_final.json`, `step3_equivalence.json`, `step4_overhead.json`, `step4_projection.json`, `download_ledger.json`.

### Outcome

| Criterion (pre-registered) | T(0.05) | T(0.10) |
|---|---|---|
| Step 1: (a) + (b) on 24/24 frames | **pass** (24/24) | **pass** (24/24) |
| Effect recall ≥ 0.98 for every type (pooled) | pass (REMOVE 0.984) | **fail** (REMOVE 0.900) |
| AP@0.7 recovery within 0.02 of dense, every family | **fail** (remove_feat 0.033, spoof_pts 0.024) | **fail** (remove_feat 0.028, spoof_pts 0.027) |
| n = 2 overhead p95 ≤ 10% (isolated-encode ≤ 15%) | **fail** (25.4%; 41.9%) | **fail** (28.8%; 50.5%) |

**Band: FAIL.** PARTIAL needs the recall and AP criteria to pass for some f, and neither f passes both. Per the pre-registration: the counterfactual cost cannot be reduced exactly on this CPU with this trigger. Nothing was chosen post hoc. Both f are reported.

### Re-stream and reproduction (safeguards)

- **Data.** Only the 3 allowlisted block-T scenarios were streamed, one on disk at a time.
- **Bytes.** 4.26e9 bytes downloaded (new ledger), within the 4.6e9 budget. The budget was checked before the first byte. Raw data was deleted after each cache was written and re-read.
- **Reproduction.** Every (frame, condition) was recomputed with the E0 code and seeds. Attack ledgers, GT and dense Y+ candidates matched the E0 cache bitwise on all 404 frames. A single mismatch would have stopped the run.
- **Dense reference reproduces E1 exactly.** R1-dense AP@0.7 matches on all 5 conditions (clean 0.8741; spoof_feat 0.8392; remove_feat 0.8649; shift_feat 0.8358; spoof_pts 0.8634), and so does recovery (0.167 / 0.162 / 0.176 / 0.279).
- **Secondary check.** The real trigger-mode decode gives the same candidate anchor indices as the restriction of the dense Y-(i) on 3925/3925 sender evaluations at both f. Max score diff 2.9e-6; max corner diff 1.5e-5 m.

### Step 3: effect recall (2020 evaluations = 404 frames × 5 conditions)

| Type | Dense effects | Reproduced, T(0.05) | Reproduced, T(0.10) |
|---|---|---|---|
| ADD | 4348 | 4348 (1.000) | 4348 (1.000) |
| **REMOVE** | **1354** | **1332 (0.984)** | **1219 (0.900)** |
| SHIFT | 3928 | 3928 (1.000) | 3928 (1.000) |

**REMOVE recall per condition.**

| Condition | T(0.05) | T(0.10) |
|---|---|---|
| clean | 224/228 (0.982) | 203/228 (0.890) |
| spoof_feat | **291/297 (0.980)** | 264/297 (0.889) |
| remove_feat | 240/244 (0.984) | 218/244 (0.893) |
| shift_feat | 320/324 (0.988) | 299/324 (0.923) |
| spoof_pts | 257/261 (0.985) | 235/261 (0.900) |

- **Spurious effects:** 0 of any type at both f. A trigger effect never appears without an identical dense one.
- **ADD and SHIFT recall is 1.000 by construction.** Their Y+ box has score ≥ 0.20 ≥ f, so its tile is in T.
- **Every miss is a REMOVE effect whose tile is outside T(f).** A REMOVE box exists in Y-(i) (score ≥ 0.20) where Y+ has no anchor ≥ f. The trigger looks only at Y+, so by design it cannot see these.

**REMOVE misses (Y+ score = max Y+ anchor probability in the missed box's tile).**

| | T(0.05) | T(0.10) |
|---|---|---|
| Missed (sender, condition) effects | 22 | 135 |
| Distinct boxes (frames) | 6 (6) | 35 (31) |
| Y+ score at missed box, min / median / max | 0.014 / 0.039 / 0.049 | 0.011 / 0.063 / 0.098 |
| Y-(i) score of missed box, min / median / max | 0.206 / 0.235 / 0.491 | 0.201 / 0.229 / 0.519 |

**Examples (T(0.05); block-T scenario, frame, sender, tile, Y+ score, Y-(i) score, centre).**

| Scenario | Frame | Sender | Tile | Y+ score | Y-(i) score | Centre (m) |
|---|---|---|---|---|---|---|
| …21_48_35 | 3 | 2 | (8, 31) | 0.035 | 0.235 | (60.8, 13.2) |
| …21_48_35 | 86 | 2 | (5, 16) | 0.017 | 0.491 | (−35.9, −3.0) |
| …21_48_35 | 87 | 2 | (5, 14) | 0.014 | 0.327 | (−49.9, −2.0) |
| …13_37_16 | 9 | 1 | (7, 12) | 0.039 | 0.206 | (−62.7, 6.5) |
| …13_37_16 | 14 | 1 | (7, 11) | 0.047 | 0.257 | (−66.5, 8.7) |

### Step 3: what differs from dense

| Count (2020 evaluations; 3925 sender evaluations) | T(0.05) | T(0.10) |
|---|---|---|
| Sender NMS outputs that differ from dense (any box) | 22 | 115 |
| … differing among boxes centred in T(f) | **0** | **0** |
| Dense post-NMS Y-(i) boxes centred outside T(f) (dropped) | 22 | 135 |
| Evaluations whose effect set differs | 22 | 115 |
| Evaluations whose R1 gating choice differs | 5 | 20 |
| Gated units: both / dense only / trigger only | 724 / 5 / 0 | 709 / 20 / 0 |
| Gated tiles outside T(f) | 0 | 0 |
| Evaluations whose final gated output differs | 5 | 20 |

- **Inside T(f), the method is exact end to end.** No NMS output, effect or gating unit differs there.
- **All differences come from REMOVE boxes outside T(f).** The trigger never gates a unit that dense R1 does not gate. It only misses units, all of them REMOVE-driven.
- **At T(0.05) the 5 gating differences are a single unit.** Scenario …21_48_35, frame 3, sender 2, tile (8, 31) is gated by dense R1 in all 5 conditions and missed by the trigger.

### Step 3: AP@0.7 and recovery

| Condition | Undefended | R1 dense | R1 T(0.05) | R1 T(0.10) |
|---|---|---|---|---|
| clean (rel. loss) | 0.8737 | 0.8741 (−0.04%) | 0.8744 (−0.08%) | 0.8745 (−0.09%) |
| spoof_feat (recovery) | 0.8323 | 0.8392 (0.167) | 0.8394 (0.173) | 0.8395 (0.175) |
| remove_feat (recovery) | 0.8631 | 0.8649 (0.162) | 0.8652 (**0.195**) | 0.8651 (**0.190**) |
| shift_feat (recovery) | 0.8278 | 0.8358 (0.176) | 0.8360 (0.180) | 0.8361 (0.182) |
| spoof_pts (recovery) | 0.8595 | 0.8634 (0.279) | 0.8638 (**0.303**) | 0.8638 (**0.306**) |

- **The trigger's recovery is higher than dense in every family.** The criterion is on the absolute difference, so it fails anyway: |Δ| > 0.02 on remove_feat and spoof_pts at both f.
- **Absolute AP differences are small.** They are ≤ 0.0004 AP@0.7. The recovery differences are large because the attack losses are small (0.0106 for remove_feat, 0.0143 for spoof_pts).
- **Direction.** Some REMOVE-driven gates of dense R1 lower AP@0.7 here, and the trigger drops them. This is in-sample and rests on few units: 5 at T(0.05), all one box. It is not evidence that the trigger is better.

### Step 4: overhead at n = 2 (24-frame slice, D-42 protocol, M1 CPU, 8 threads, 3 interleaved reps)

| Mode | Overhead p50 / p95 | Isolated-encode p50 / p95 | MINT extra p50 / p95 (s) | Tile fraction mean (p95) |
|---|---|---|---|---|
| Dense sequential (reference) | 34.3% / 49.0% | 37.5% / 76.6% | 0.082 / 0.162 | 1.0 |
| Trigger T(0.05) | 16.3% / **25.4%** | 20.4% / **41.9%** | 0.044 / 0.091 | 0.213 (0.250) |
| Trigger T(0.10) | 12.2% / **28.8%** | 14.8% / **50.5%** | 0.032 / 0.111 | 0.143 (0.167) |

- **Baseline.** Baseline-only p50 is 0.293 s (p95 0.448 s). The isolated receiver encode p50 is 0.141 s.
- **Both f are in the > 25% p95 band.** T(0.05) is just over the 25% line.
- **The p95 comes from a few frames.** Only 2/24 frames exceed 25% at each f. The heavy tail is in evidence and compose (compose p95 0.021 s at T(0.05) and 0.068 s at T(0.10), on 2–3 gated frames) and in the baseline itself.

**Cost split at n = 2 (p50 over frames).**

| | T(0.05) | T(0.10) |
|---|---|---|
| Per-tile: gather + fusion + deblocks/heads | 0.0265 s (c_tile = 0.211 ms/tile) | 0.0180 s (0.225 ms/tile) |
| Per sender: candidates + NMS + effects | 0.0100 s | 0.0088 s |
| Fixed: trigger mask + evidence + compose | 0.0060 s | 0.0022 s |

- **Tile-proportional work is 56–61% of the trigger's extra cost** (p50). The trigger mask itself costs 0.4 ms.
- **The model fits the measurement.** At n = 2 it predicts 0.042 s extra for T(0.05) against 0.044 s measured.

**Tile fractions on real block-T frames (clean condition).**

| n | Frames | T(0.05) mean | T(0.10) mean |
|---|---|---|---|
| 2 | 135 | 0.209 | 0.154 |
| 3 | 157 | 0.193 | 0.181 |
| 4 | 112 | 0.253 | 0.211 |

### Step 4: projection for n = 3–5 (not a measurement)

| n | Tile source | T(0.05) projected overhead p50 / p95 | T(0.10) projected overhead p50 / p95 |
|---|---|---|---|
| 3 | 157 real n = 3 frames | 34.2% / 38.7% | 31.2% / 36.2% |
| 4 | 112 real n = 4 frames | 54.0% / 59.5% | 48.6% / 53.2% |
| 5 | **all 269 multi-agent frames (no real n = 5)** | 58.7% / 74.8% | 53.9% / 66.9% |

- **Formula.** As pre-registered: (n − 1)·(|T|·c_tile + c_sender) + c_fixed, divided by baseline-only p50 at n. The baseline was measured with replicated sender features: 0.215 / 0.251 / 0.257 s for n = 3 / 4 / 5.
- **Evidence and compose are held at their n = 2 values.** The real cost would be higher.
- **The baselines are not comparable.** The replicated-feature baselines are lower than the interleaved n = 2 baseline (0.293 s), because they were timed in a separate loop without MINT stages in between (the D-42 context effect). So n ≥ 3 projections are not directly comparable with the n = 2 measurement.

### Interpretation

1. **The trigger is exact where it looks, but it cannot see REMOVE effects.** Fusion and post-processing on T(f) reproduce dense outputs (0 differences inside T). Every miss is a box that appears only when a sender is removed, in a tile where Y+ is below f. Lowering f widens T and raises the cost. At f = 0.05, REMOVE recall just meets 0.98, but one missed unit still moves remove_feat and spoof_pts recovery by more than 0.02.
2. **Cost.** At n = 2 the trigger halves the dense extra at p50 (34% → 16% / 12%), but p95 stays above 25%. The projections grow roughly linearly with n, to 34–75%.
3. **Possible next steps (your decision; not proposed as rules):**
   - A trigger that also covers REMOVE candidates (Y+ score alone cannot), at extra cost.
   - A different cost budget or hardware (D-17).
   - Accepting non-exact REMOVE coverage as a stated approximation. That would need its own pre-registration.

Proposed log entry: D-49 in [`decision_log_proposed_appendix.md`](decision_log_proposed_appendix.md).
