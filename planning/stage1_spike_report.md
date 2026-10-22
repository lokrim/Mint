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
