# Stage-1 feasibility spike report (OPV2V-first, CPU)

Run 2026-10-22. Record: [`runs/20261022T165007Z-S1-spike/`](../runs/20261022T165007Z-S1-spike/record.json) (`record.json` and `manifest.json`).

**Feasibility evidence only.** One test scenario, a released detector, no MINT method. **Not a reproduction or an evaluation.**

## What was done

| Item | Detail |
|---|---|
| Decision | User, 2026-10-22: no GPU, so OPV2V-first with the released AttFuse checkpoint; ask before any download over 5 GB |
| Environment | `uv` venv Python 3.10.20, torch 2.2.2 (CPU), numpy 1.26.4, open3d 0.18.0 (used only in the check script). Lock: [`env/requirements-stage1-spike.lock.txt`](../env/requirements-stage1-spike.lock.txt) |
| OpenCOOD | `third_party/OpenCOOD` at commit `31ba16025da27ffe4e336f011290dfbc66f9a1f1` (2024-08-16), **tracked source unmodified**. Only ignored build artefacts were added: Cython `box_overlaps` (CPU) |
| Checkpoint | `pointpillar_attentive_fusion.zip`, 45 MB, from the UCLA Box link in the OpenCOOD README. zip sha256 `9d263ec9…cab5`; `latest.pth` `f6df2f54…a77c` (file date 2021-09-09); `config.yaml` `af55429f…75ed` |
| Data | One OPV2V **test** scenario, `2021_08_23_12_58_19`: 2 CAVs, 104 frames, 0.70 GB compressed. Fetched with HTTP range requests from inside `test-012.zip` (21.1 GB total, 16 scenarios) by [`tools/ranged_zip.py`](../tools/ranged_zip.py) in 72 s. Nothing else downloaded. |
| Code (ours) | [`src/mint/model/opencood_shims.py`](../src/mint/model/opencood_shims.py), [`src/mint/model/attfuse_parts.py`](../src/mint/model/attfuse_parts.py), [`runners/stage1_spike.py`](../runners/stage1_spike.py), [`tools/check_pcd_shim.py`](../tools/check_pcd_shim.py) |

## Checkpoint configuration (read from its `config.yaml`, so V-01 provenance is partly answered)

- Name `point_pillar_intermediate_fusion_low_res`.
- Voxel 0.4 × 0.4 × 4 m; range [−140.8, −40, −3, 140.8, 40, 1] m, so a 704 × 200 pillar grid.
- Backbone [3, 5, 8] / strides [2, 2, 2] / [64, 128, 256] ch. Fusion scales are 352×100, 176×50 and 88×25 (0.8 / 1.6 / 3.2 m). Head grid 352×100.
- Anchors 3.9 × 1.6 × 1.56 m, 2 rotations. Score threshold 0.20, NMS 0.15.
- `root_dir: opv2v_data_dumping/train`, `validate_dir: .../test`: **trained on `train`**, as the README implies.
- **`proj_first` is effectively True** (OpenCOOD default; the config sets no override). Senders' points are projected into the ego frame before encoding. Our own-frame protocol (D-13) is therefore a distribution shift for this checkpoint: V-02 is still open.

## Results

| Check | Result | Status |
|---|---|---|
| CPU run of the unmodified OpenCOOD stack | Works, with three stand-ins (below) | ✅ |
| **Stand-in 1**: spconv v1 voxelizer (NumPy) | Equals a brute-force reference on 20,000 real points / 5,270 voxels (K1) | ✅ logic verified. Equivalence to *real* spconv is not testable here. |
| **Stand-in 2**: `cumm.tensorview` | Import placeholder only (code path unused with spconv v1 semantics) | ✅ |
| **Stand-in 3**: `open3d.io.read_point_cloud` | Needed because **importing open3d makes torch matmul deadlock** (OpenMP runtime clash; reproduced in isolation). Byte-identical to real open3d on all 208 PCDs of the scenario (max abs diff 0.0, points and colours) | ✅ |
| Clean detection, one scenario (default OpenCOOD AP) | AP@0.3 0.872, **AP@0.5 0.859, AP@0.7 0.748**; 2,021 GT, 1,897 predictions. Global-sort variant: 0.897 / 0.888 / 0.803 | Plausible and non-degenerate. **Not comparable** to the published 0.815 (all 16 test scenarios). |
| CPU cost per frame (M1, 8 threads, batch 1, 104 frames) | Load + voxelize p50 0.41 s / p95 0.61 s. VFE + scatter 0.07 / 0.14. **Backbone + fusion + heads 0.50 / 0.67**. NMS 0.02 / 0.06. Total wall 122 s for 104 frames, including locality tests. | Proxy timings only |
| Peak RSS | 1.30 GB (self; children 0) | Fits in 8 GB |
| Our fusion re-implementation vs OpenCOOD `AttFusion` | Max abs diff 1.2 × 10⁻⁶ (fp32 summation order) | ✅ not bit-identical (see note) |
| **V-03 locality** (16 frames; sender excluded from attention in one 6.4 m tile that contains a predicted box centre) | **16/16 bit-identical** cls and reg head outputs outside the tile. **0** post-NMS boxes changed outside the tile. **31** changed inside (inside psm change up to 4.48). The sender's attention mass in the tiles ranged 0.11–0.54. | ✅ **supported for this checkpoint** (2-agent scenario) |

## Observations that change the plan

1. **The counterfactual label bridge works as derived** ([contract](information_and_threat_model.md) §5.2). Removing a sender's tile changes outputs only in that tile, and post-NMS effects stayed inside the tile in all 16 tests. Cross-tile NMS effects are possible in principle and must still be counted at scale.
2. **CPU inference is fast enough.**
   - At about 1 s per frame end to end, all 16 test scenarios (about 2,100 frames [E]) would take about 40 min.
   - MINT's extra deblock+head pass per sender is part of the 0.50 s "backbone + fusion + heads" figure. Its share must be timed separately (Stage 7).
3. **Fusion baseline definition.** Our re-implementation differs from OpenCOOD's by about 10⁻⁶. All MINT comparisons must use **one** fusion implementation for both "with" and "without" (ours), and report the AP difference against OpenCOOD's own fusion once.
4. **Full test reproduction (V-01) needs about 21 GB** (test-012.zip, 16 scenarios), plus 4.9 GB for Culver City. That exceeds your 5 GB rule. **Disk has 17 GB free**, so the full test set can only be streamed scenario by scenario, deleting raw data after caching. Approval is needed.
5. **Exposure.** This scenario's clean detector outputs and AP have now been seen. To keep the E set clean, **move `2021_08_23_12_58_19` to development** (exposure ledger updated).

## Full test-split reproduction and multi-agent locality (run 2026-10-23, user-approved streaming)

Record: [`runs/20261023-S1-reproduce/`](../runs/20261023-S1-reproduce/summary.md).
- Per-scenario JSON plus cached per-frame predictions (`preds/*.npz`).
- Runner [`runners/stage1_reproduce.py`](../runners/stage1_reproduce.py); summary [`runners/stage1_summarize.py`](../runners/stage1_summarize.py).

**How the data was handled.**
- All 16 OPV2V test scenarios were streamed one at a time from `test-012.zip`: **21.14 GB downloaded** in total.
- Only `.pcd`/`.yaml` files were written; camera images were never written to disk.
- Peak raw data on disk was **2.62 GB** (largest scenario), within the ≤ ~3 GB rule. Each scenario was deleted after inference.
- Only the predictions cache remains.

**Determinism fix.** OpenCOOD shuffles points at test time with an unseeded `np.random.permutation`. That changes which points survive the 32-points-per-pillar cap: about 4% of pillars are full. The runner seeds NumPy per frame from SHA-256(seed | scenario | frame).
- Measured on one scenario with 4 seeds: class logits change by up to 0.92 and scores by ≤ 0.026, but no TP/FP outcome changed, so the scenario AP was identical.
- An earlier unseeded run differed by 3 × 10⁻⁴ AP@0.5.

**V-01 result: published AP reproduced** (OpenCOOD default AP, scenarios in OpenCOOD's sorted order, 2,170 frames, 33,003 predictions):

| Metric | Ours | Published (README, Default Towns) |
|---|---|---|
| AP@0.3 / 0.5 / **0.7** | 0.914 / 0.906 / **0.8155** | — / — / **0.815** |
| AP@0.3 / 0.5 / 0.7, global sort | 0.941 / 0.936 / 0.881 | not reported |

- The difference at AP@0.7 is +0.0005, within the ±0.01 gate.
- This also indirectly supports the voxelizer and PCD stand-ins.
- Per-scenario AP@0.7 ranges **0.720–0.966** (table in the summary). Scenario-level variation is large, so scenario-grouped uncertainty is required.

**Cost** (M1 CPU, 8 threads; median per scenario of the per-frame `inference_intermediate_fusion` time, which includes post-processing):
- 0.25 s with 1.3 agents, 0.55–0.62 s with 2 agents, 0.82–0.92 s with 3 agents, 1.19 s with 4.6 agents.
- Roughly linear in agent count. Data loading and voxelization come on top (≈ 0.4 s in the spike).

**V-03 result: locality holds for multi-agent frames.**
- 93 tile tests across all scenarios (single-agent frames skipped): 39 with 2 agents, 46 with 3, 2 with 4, 6 with 5.
- **93/93 bit-identical head outputs outside the masked tile**, and every test changed outputs inside it.
- After NMS, 209 changed boxes had centres inside their tile and **2 (≈ 1%) outside**. In both cases the head outputs outside the tile were bit-identical and the box count was unchanged: one box's regressed centre moved across the tile border. This is the anticipated straddling-box case, not a fusion leak. The effect-attribution rule must handle it (D-22).

**Exposure.** Clean detector outputs and AP for all 16 test scenarios have now been seen (detector level only, for V-01, as the roadmap planned). No MINT method or attack has touched them. Recorded in the [exposure ledger](exposure_ledger.csv).

**Gate S1-G (OPV2V part).**
- Reproduction ✅.
- Locality ✅ (cross-tile ≈ 1% < 5%).
- Non-degenerate clean AP ✅.
- Costs measured on the proxy ✅.
- Still open: V-02 (own-frame encoding) and V-05 (message size).

## Not done or not established

- V-01 full reproduction (blocked on download approval).
- V-02 own-frame encoding.
- V-05 message size.
- Scenarios with 3+ agents.
- Multi-sender locality.
- Any MINT component.
- Any MPS (GPU on Apple Silicon) timing.

## Next bounded steps (pending your approval of the download)

1. **Stream the remaining 15 test scenarios** one at a time (each ≤ 2.8 GB, about 21 GB in total, never more than about 3 GB on disk at once). Run the reproduction, cache only detector outputs and multi-scale features at keyframe stride, then delete the raw PCDs.
2. Same for `validate` (≈ 40 GB total, needed for MINT fit/calibration), only after (1).
3. Then Stage 2: no-return and ray geometry for OPV2V's simulated LiDAR, and receiver coverage of effectful tiles.
