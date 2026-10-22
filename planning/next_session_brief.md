# Next-session brief

Updated 2026-10-23, after the OPV2V Stage-1 reproduction.

## Where we are

- **OPV2V-first, CPU only** (D-10a). Ask before any single download over 5 GB. The user approved streaming the test split, and that is now done.
- **V-01 passed.** AP@0.7 = 0.8155 vs the published 0.815 on all 16 test scenarios.
- **V-03 passed.** 93/93 tile tests bit-identical outside the tile (2–5 agents). 2/211 boxes crossed a tile border (D-22).
- **Determinism.** Per-frame NumPy seeding (D-23).
- **Cost.** About 0.25–1.2 s per frame, roughly linear in agent count. 1.3 GB peak RSS.
- **Disk.** 41 GB free. Raw test data deleted; predictions cached in `runs/20261023-S1-reproduce/preds/`.
- **Exposure.** All test scenarios have detector-level exposure only. They remain the MINT E set (D-21b).
- Details: [stage1_spike_report.md](stage1_spike_report.md).

## Next bounded actions

1. **V-02.** Own-frame encoding (`proj_first=False`) on 2–3 *validate* scenarios: report the AP change. Needs streaming from `validate-002.zip` (≈ 40 GB total; one scenario ≤ 3 GB at a time). **Ask before the full validate stream.**
2. **V-05.** Measure the AttFuse message size: per-scale tensor bytes; dense vs non-zero.
3. **Stage 2 on validate.**
   - OPV2V LiDAR ray semantics: origin, organized or not, no-returns.
   - Range-image or slab tests.
   - Receiver coverage of effectful tiles (gate S2-G).
4. **Decide on caching.** Re-streaming validate for each later stage costs about 40 GB of transfer. Caching multi-scale features at keyframe stride costs about 8 MB per agent-frame in fp16.

## Do not

- Download over 5 GB without asking.
- Modify `third_party/OpenCOOD` tracked files.
- Import real open3d alongside torch.
- Use OpenCOOD's `AttFusion` and ours in the same comparison.
- Run MINT methods or attacks on test scenarios before the protocol freeze.
