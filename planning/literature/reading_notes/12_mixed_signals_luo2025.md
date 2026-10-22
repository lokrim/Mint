# Mixed Signals: Luo, Dao, Liu, et al., ICCV 2025 (dataset) + code

- **Citation.** `luo2025mixedsignals`. arXiv 2502.14156 v3 (28 Aug 2025), including the appendix.
- **Access.** FULL-CLOSE on the whole paper and appendix. **CODE**: `acfr/Mixed-Signals-Dataset` (branch `release-msig`, pushed 2026-08-26) and `quan-dao/mixed-signals-devkit` (main, pushed 2025-07-04). **HF card**: `sberrio/Mixed-Signals-V2X` at sha `1a61aea747aa6bc45da2c2f085a1f1d3abc41f91` (lastModified 2026-07-08; the same revision the old project pinned). Read 2026-10-22.

## Facts verified in the paper
- **Collection.**
  - 3 CAVs: two EVs with OS1-128 tilted 15° down at 1.63 m; one urban "Laser" car with OS1-128 horizontal at 1.9 m.
  - RSU with OS1-64 (TOP) and OS Dome-128 (DOME) on a pole about 2.5 m high (§3.1, Fig. 2, Table A3).
  - Location: the intersection of Abercrombie St and Myrtle St, Sydney. **Two hours of rush-hour recording**, vehicles repeatedly passing (§3.2).
- **Synchronization.** GPS timestamps at 10 Hz. Samples matched within a 50 ms window (§3.2.1, App. C.1).
- **Localization.** Scan matching against a dense LIO-SAM map. Maximum positioning error 15 cm, heading 0.4° (§3.2.1).
- **Scenes.** 37 scenes × 30 s. The paper says 33 train / 4 test, "no temporal overlap between training and test and among test scenes" (§3.2.2).
  - The HF card says 29 train / 4 val / 4 test, with val and test labels withheld for a Codabench competition (dev Aug 1–28, final Aug 29 – Sep 4, 2026).
- **Labels.**
  - Professional annotators. Boxes fitted in the TOP frame.
  - **Keyframes annotated at 1 Hz; non-keyframes by linear interpolation of box pose** (§3.3).
  - Discrepancy rule: prioritise the RSU points, then EVs, then the urban vehicle (App. B.3).
  - The spec document embedded in the appendix says 2 Hz and 40–41 frames per 20 s sequence: an **internal inconsistency** with §3.3's 1 Hz.
- **Classes.** 10 fine-grained classes, grouped as Vehicle / Bike / Pedestrian (Table 2).
- **Benchmarks.** All models use a PointPillars backbone in an OpenCOOD fork, with 3-class heads via 1×1 convolutions (App. A.1).
  - Range ±51.2 m in TOP. Visibility threshold 5 points from any agent. BEV IoU matching (§4.2).
  - Attentive Fusion: Vehicle AP@0.5 0.82, Bike 0.71, Pedestrian AP@0.3 0.74, 5.26 MB uncompressed (Table 3).
  - "Benchmarks will be made available at a later date" (App. A).
- **EV intensity is absent** (App. A, Fig. A2).

## Facts verified in code (`release-msig`)
- **Checkpoints not released.** The README says "Download check points from `???`".
- **Environment.** Python 3.7.11; PyTorch 1.8–1.12 + CUDA; spconv; Ubuntu 18.04; GPU of at least 6 GB recommended.
- **Licence.** UCLA Academic Software License: academic or non-profit only, **"prohibited from further transferring the Software — including any derivatives"**.
- **`msig_pillar_attnfuse.yaml`.**
  - voxel (0.2, 0.2, 7) m; range [−51.2, −51.2, −6, 51.2, 51.2, 1];
  - PillarVFE 64; backbone layers [3, 5, 8], strides [2, 2, 2], filters [64, 128, 256], upsample [1, 2, 4] to 128 ch each;
  - anchors: car 5.13×2.12×1.84, bike 1.76×0.6×1.73, ped 0.8×0.6×1.73, 2 rotations;
  - NMS 0.15; score threshold 0.2; 30 epochs, Adam lr 0.002, batch 1.
- **Train/test sequences.** `MSigBaseDataset` hard-codes test sequences {4, 5, 17, 21}. The labels come from `V2X_dataset-v0.4-labels.json`, an **older release format** than the HF TXT labels.
- **Frames and points.**
  - Communication range 70 m. GT range ±70 m for gt_infos. `num_min_points_in_boxes = 5`. `gt_visibility` is per agent.
  - Intensity normalised by /3500, clipped to [0, 1].
  - Vehicle clouds shifted z −3.25 m.
  - RSU clouds converted from map to the agent frame.
  - **No placeholder removal.**
- **`MSigIntermediateFusion.proj_first = True`.** Each agent's points are transformed into the TOP frame *before* voxelization. Velocity and time-delay inputs are zeros.
- **`AttBEVBackbone`.**
  - Each block runs on **un-fused** per-agent features.
  - `AttFusion` (per-pixel scaled dot-product self-attention over agents, ego row output) runs per scale.
  - Each fused map is upsampled by `ConvTranspose2d(k=stride, s=stride)` and concatenated (384 ch). 1×1 cls/reg heads.
  - **So fusion effects are pixel-local** (basis of the MINT label bridge; to be verified empirically as V-03).

## Relevance
- **The real heterogeneous data with an RSU receiver** make it scientifically attractive. The organized Ouster beam grids carry no-return slots (pilot P1/P2: row/column directions recoverable after a fitted mount rotation). This makes receiver-side range-image ray checks cheap.
- **Blockers:**
  - no checkpoint, so training is needed (GPU);
  - 214 GB of labelled archives (29 TARs);
  - a single site and a single 2-hour session, so independence is limited;
  - 1 Hz keyframe GT;
  - licence restrictions on the code.

## Experiment
See [dataset_and_feature_feasibility.md](../../dataset_and_feature_feasibility.md) §3 (Stage 1 gates).
