# OPV2V (Xu et al., ICRA 2022) and V2V4Real (Xu et al., CVPR 2023): candidate alternative pipelines

- **Citations.** `xu2022opv2v` (arXiv 2109.07644), `xu2023v2v4real` (arXiv 2303.07601).
- **Access.**
  - OPV2V: FULL-SKIM (dataset §III, attentive fusion §IV).
  - V2V4Real: FULL-SKIM (dataset and benchmark sections).
  - CODE: DerrickXuNu/OpenCOOD README (pushed 2024-08-17) and ucla-mobility/V2V4Real README (pushed 2024-08-14).
- Read 2026-10-22.

## OPV2V
- **Data.** CARLA + OpenCDA co-simulation. 73 scenes, 11,464 frames, 232,913 boxes, 2–7 CAVs, 64-channel simulated LiDAR. Default towns plus a digital Culver City (4 scenes, about 600 frames) for domain-shift testing.
- **Attentive Intermediate Fusion.** Metadata sharing, then PointPillars feature extraction, optional encoder–decoder compression, feature sharing, per-pixel self-attention fusion, and prediction.
  - During training a random CAV is the ego.
  - Training all models took "14 days on 4 RTX 3090".
- **Checkpoints (README).** Google Drive links for PointPillar Attentive Fusion (AP@0.7 0.815/0.810 Default, 0.735/0.731 Culver; 126.8 / 1.98 Mbit before/after compression), F-Cooper, CoAlign, V2VAM, and more.
  - Data on UCLA Box, split into chunks.
  - Sizes not fetched: open item L-10.
- **Prior-security ecosystem on OPV2V:**
  - CAD (Adv-OPV2V benchmark and models);
  - LUCIA/SOMBRA;
  - PoseGuard;
  - TrustFlip;
  - Latent Guardian;
  - GLST.
  **The most directly comparable setting.**
- **Ray semantics.** Simulated rays; no real no-return handling; unorganized clouds as stored [U: verify].
- **Licence.** OpenCOOD academic licence (as for the Mixed Signals fork). OPV2V data licence not checked.

## V2V4Real
- **Data.** 2 vehicles (Tesla and Ford), each with a Velodyne VLP-32. 410 km. 67 scenarios of 10–20 s at 10 Hz, about 20K LiDAR frames, 240K boxes. Inter-vehicle asynchrony under 50 ms. Columbus, Ohio, mostly highway (347 of 410 km).
- **Checkpoints released** on UCLA Box: No/Late/Early fusion, F-Cooper, **AttFuse (Sync AP@0.5 64.5, AP@0.7 34.3; Async 56.4 / 28.5)**, V2VNet, V2X-ViT, CoBEVT. Python 3.7, PyTorch 1.12, spconv 2.x (cu113).
- **Limitation for MINT.** Only **one sender**. There is no independent third view, so cross-peer corroboration is impossible. Receiver rays are the only trusted evidence. This makes it a strong *stress test* for H4.
- **Ray semantics.** VLP-32: whether stored clouds keep a ring/beam index is [U].

## What transfers
- Both provide **released AttFuse PointPillars checkpoints**. This removes the detector-training commitment (decisive under the current no-GPU hardware).
- V2V4Real is real data. OPV2V allows direct comparison with prior defenses.

## Experiment
Stage-1 reproduction check: load the AttFuse checkpoint and reproduce the published AP within tolerance on its own test split, in our clean environment. Measure CPU/MPS inference cost per frame. See [feasibility](../../dataset_and_feature_feasibility.md).
