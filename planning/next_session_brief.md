# Next-session brief

Updated 2026-10-22, after the Stage-1 feasibility spike.

## Where we are

- **Path:** OPV2V-first. No GPU (decision D-10a). Ask before any download over 5 GB.
- **Spike done:** [stage1_spike_report.md](stage1_spike_report.md).
  - The released AttFuse checkpoint runs on CPU in `.venv` (Python 3.10, torch 2.2.2), with verified stand-ins for spconv, cumm and open3d.
  - About 1 s per frame; 1.3 GB peak memory.
  - V-03 locality: 16/16 tile tests bit-identical outside the tile.
- **Data on disk:** one OPV2V test scenario (moved to development), plus the checkpoint. 17 GB of disk free.

## Waiting on you

Approval to stream the full OPV2V test split: about 21 GB in total, fetched scenario by scenario, never more than about 3 GB on disk at once, raw PCDs deleted after caching. This is needed for V-01 (reproduce the published AP@0.7 0.815). Culver City (4.9 GB) and `validate` (≈ 40 GB, for MINT fit/calibration) follow later and need separate approval.

## Next bounded actions after approval

1. Add a `--keep-only` cache mode to the runner: store detector outputs plus multi-scale features at keyframe stride, then delete the raw scenario.
2. Run the full test reproduction. Locality tests on scenarios with 3+ agents (multi-sender).
3. V-02 (own-frame encoding, `proj_first=False`) on a few scenarios.
4. Stage 2: ray geometry for OPV2V's simulated LiDAR. Measure receiver coverage of effectful tiles (gate S2-G).

## Do not

- Download over 5 GB without asking.
- Modify `third_party/OpenCOOD` tracked files.
- Import real open3d in a process that uses torch.
- Use OpenCOOD's `AttFusion` and ours in the same comparison.
- Present the one-scenario AP as a reproduction.
