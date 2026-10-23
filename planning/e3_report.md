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
