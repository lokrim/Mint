# Dataset, ground truth and feature-pipeline feasibility

Checkpoint 1, 2026-10-22.

Status markers:
- **[V]** verified in a source or code read this session;
- **[L]** measured locally (pilot);
- **[E]** our estimate;
- **[U]** unknown;
- **[P]** proposal.

## 1. Local resource facts that constrain everything [L]

- **Machine.** Apple M1, 8 GB RAM, 8 cores. **No CUDA GPU.**
- **Disk.** 21 GB free of 228 GB.
- **Python.** System `python3` is 3.15.0 without NumPy. `uv` 0.11.17 is available.
- **Existing data (read-only, old project).** Mixed Signals mini_7 and mini_10–13: 5 TARs, 39 GB, plus about 32 GB of extracted first-25 s. All exposed.

Consequence: **training any cooperative detector locally is infeasible** [E]. Downloading the full Mixed Signals labelled set (214 GB) is impossible without external storage. Decision Q1 in [risks](risks_and_open_questions.md).

## 2. Evidence-backed comparison

| Criterion | Mixed Signals (retain) | OPV2V | V2V4Real | DAIR-V2X-C | V2X-Real |
|---|---|---|---|---|---|
| Real vs simulated | Real [V] | Simulated (CARLA + OpenCDA) [V] | Real [V] | Real [V] | Real [V] |
| Agents | 3 CAVs + RSU (2 LiDARs), heterogeneous [V] | 2–7 CAVs, homogeneous 64-ch sim [V] | 2 CAVs, VLP-32 each [V] | 1 vehicle (40-beam) + 1 infra (300-beam, 100° FOV) [V] | 2 CAVs + 2 infra [V] |
| Independent senders available to a receiver | up to 3 vehicles (+ RSU dome is co-owned) | 1–6 | **1** | 1 | up to 3 |
| Independence unit | **One ~35-min session**, one site (pilot P3) [L] | 73 scenes across towns + 4 Culver City [V] | 67 scenarios, 3 days, 410 km [V] | Intersections; scenes of ~20 s [V] | 68 scenarios from 75 h of logs [V] |
| Labels | 29 train segs, 124,668 boxes, 3 meta-classes, TOP frame, ±51.2 m, >5 pts; **1 Hz hand keyframes + interpolation**; val/test withheld [V] | Full sim GT [V] | 240K boxes [V] | Expert labels; CoAlign uses "complemented" labels [V README] | 1.2M boxes [V] |
| Temporal continuity | 10 Hz, 30 s segments [V] | 10 Hz scenarios [V] | 10 Hz, 10–20 s [V] | 10 Hz key frames, ~20 s [V] | [U] |
| Sensor origin and ray semantics | **Organized Ouster grids; no-return slots; directions recoverable after a fitted mount rotation** (P1/P2) [L] | Sim rays; storage organization [U] | VLP-32; ring index [U] | Infra non-repetitive 300-beam (no grid) [V spec] [E] | [U] |
| Synchronization | ≤ 50 ms window, GPS time [V] | Sim sync; async can be modelled [V] | < 50 ms; async benchmark [V] | Async (TCLF) [V] | [U] |
| Feature framework | OpenCOOD fork, PointPillars AttFuse 3-class config [V] | OpenCOOD [V] | OpenCOOD fork [V] | OpenCOOD via CoAlign/HEAL [V] | OpenCOOD fork [V] |
| **Usable pretrained AttFuse checkpoint** | **None** ("`???`") [V] | **Yes** (Google Drive) [V] | **Yes** (UCLA Box; AttFuse AP@0.5 64.5) [V] | CoAlign / HEAL ckpts (spconv 1.2.1 caveat) [V] | **None found** [V README] |
| Checkpoint saw eval scenes? | n/a (we train) | Trained on train split [V README]; test/Culver unseen [E] | Trained on train [E]; verify | Verify | n/a |
| Licence | Data CC BY-NC-SA 4.0 [V]; code UCLA academic, **no transfer of derivatives** [V] | OpenCOOD academic licence [V]; data licence [U] | Research [U]; code academic [V] | Code Apache-2.0 [V]; data terms [U] | [U] |
| Install risk | Python 3.7, CUDA, spconv, Cython NMS [V] | Same stack [V] | Same; spconv cu113 [V] | spconv 1.2.1 for HEAL ckpts [V] | Same |
| Download / storage | 214 GB train TARs (29 × ~7.8 GB; mini_1–3 ~3.4 GB) [V] | Several 100 GB total [U, L-10]; CAD asks for > 40 GB free just for test + models [V] | [U] | [U] | [U] |
| Threat-model fit | **Best**: static RSU receiver, multi-sender, heterogeneous, real | Best for **comparison with prior defenses** (CAD, LUCIA, PoseGuard, TrustFlip all use OPV2V) | Single sender only: good H4 stress test, weak for corroboration | Single sender; V2I only | Good on paper; no ckpt |
| Verdict | Primary *if* GPU + storage exist; ray study either way | **Primary if no GPU** (inference-only) | Real-data replication (inference-only) | Optional | Defer |

**Not chosen by default:** V2XSet (sim, V2X-ViT), V2X-Sim (5 Hz sim, used by ROBOSAC/MADE/GCP), TUMTraf-V2X, HoloVIC, RCooper (region-restricted per the Mixed Signals Table 1). Each is discussed only if a decision changes.

## 3. Exact raw → feature → GT path for each viable option

### 3.1 Option MS (Mixed Signals, train our own AttFuse) [requires GPU]

1. **Raw.** HF TAR members `PointClouds/mini_N/<agent>_<k>_<ts>.pcd`, ASCII float32 xyzi, organized W×H [V].
   - Read with a strict reader that keeps (row, col).
   - Placeholders = the most frequent repeated coordinate at the sensor origin, marked `NO_RETURN_SLOT` [L].
2. **Frames.**
   - TOP/DOME raw xyz are in the map frame; to TOP by `+(41.551, 51.878, 1.077)` and identity rotation (devkit) [V].
   - Vehicles: native frame → map via odometry (quaternion x, y, z, w by name) → TOP. The devkit applies z −3.25 m to vehicle clouds, which cancels in its composition [V: findings 03].
   - **[P]** Receiver = TOP. DOME is co-owned evidence and also enters fusion as a receiver-side agent (as in the fork).
3. **Preprocess.**
   - Drop placeholders before voxelization. This is a deviation from the official fork, which keeps them [V], so the clean AP may differ.
   - Crop to [−51.2, 51.2]² × [−6, 1] m; pillars 0.2 × 0.2 × 7 m; ≤ 32 points per pillar; ≤ 32k/70k pillars (train/test) [V yaml].
   - Intensity: divide by 3500, clip to [0, 1]; EVs have 0 [V].
4. **Encoder.** PillarVFE(64) → scatter → per-agent pseudo-image `[N_agents, 64, 512, 512]` [V].
5. **Sender message (our protocol, [P]).**
   - The sender encodes in **its own frame** (`proj_first=False`).
   - It transmits the per-agent backbone outputs at each fusion scale: `[64, 256, 256]`, `[128, 128, 128]`, `[256, 64, 64]` [X].
   - By our arithmetic that is about 7.3 M floats, or **~29 MB float32 dense per sender-frame**. The paper reports 5.26 MB for Attentive Fusion [V]. The definitions differ (sparsity, dtype or measured layer): **measure (V-05)**.
   - **[P]** fp16 transmission, with an int8 quantization stress.
6. **Receiver alignment.**
   - Warp each scale with the claimed pose (affine grid sample, bilinear). The receiver is static.
   - **Deviation risk**: training must use the same warp path (V-02).
7. **Fusion and head.**
   - Per-scale `AttFusion` (per-pixel softmax over agents, TOP row).
   - ConvTranspose upsampling to 256² × 128 each, concatenated to 384 ch.
   - 1×1 cls (3 classes × 2 anchors) and reg heads.
   - `VoxelPostprocessorMulti` NMS 0.15, score 0.2 [V].
8. **GT.** HF TXT labels `cls cx cy cz dx dy dz yaw` in TOP [V].
   - Mapping label k ↔ sync k is stated by the card [V]. Our moving-object pilot was inconclusive (P2) [L], so Stage-1 test V-04 is required.
   - Evaluate in BEV rotated IoU within ±51.2 m.
9. **Training.** 30 epochs, Adam 2e-3, batch 1 [V yaml].
   - **[E]** 1–3 GPU-days on one 24 GB GPU. The basis: OPV2V reported 14 days on 4× RTX 3090 for its whole benchmark suite. Needs a timing pilot.
   - Training uses only training-block segments (§5).

### 3.2 Option OP (OPV2V with released AttFuse PointPillar checkpoint) [CPU-feasible inference, E]

1. Raw OPV2V PCD per CAV + yaml metadata (OpenCOOD format) [V].
2. OpenCOOD `point_pillar_intermediate` AttFuse config for OPV2V.
   - **Exact config to be read from the checkpoint's `config.yaml`, not assumed.** The OpenCOOD default for OPV2V AttFuse is commonly a 0.4 m voxel and a [−140.8, 140.8] × [−40, 40] m range [E, from memory; verify].
3. **Checkpoint:** "pointpillar_attentive_fusion" (README AP@0.7 0.815 Default / 0.735 Culver) [V].
4. **Reproduction gate:** reproduce test AP@0.7 within ±0.01 on the OPV2V test split. If `proj_first` must be True to reproduce, record that and run our own-frame-encoding variant as a sensitivity check.
5. GT = OPV2V boxes. Evaluation range follows the OpenCOOD evaluation [V code, to read].
6. **Splits.** The detector was trained on OPV2V train. MINT uses OPV2V `validate` (fit/calibration) and `test` + Culver City (evaluation), grouped by scenario.
7. **Ray evidence.** The receiver's own simulated cloud. Origin = the LiDAR pose from yaml. No-return semantics [U]: assume none and test.

### 3.3 Option VR (V2V4Real with released AttFuse checkpoint) [CPU-feasible inference, E]

- Same as OP. Tesla is the fixed test ego [V]. The single sender is Ford.
- The async test mode exists (100 ms) [V], which makes it a good benign-stress set.
- Use as the **real-data replication** and the H4 stress set.

## 4. Ground-truth contract (all options)

- **GT may:**
  - train the detector (MS only) and the reliability combiner;
  - tune development choices on development blocks;
  - calibrate `r` on the calibration block;
  - evaluate on test blocks.
- **GT must not:** reach the inference process, be used for test-time thresholds, or select attacks after test exposure.
- **Unlabelled ≠ empty.**
  - MS boxes require more than 5 points and |x|, |y| ≤ 51.2 m [V]. A sender-only object with ≤ 5 aggregated points is unlabelled. A prediction there must be scored with a separate `UNLABELLED_REGION` flag; the evaluator determines this from aggregated points of all agents.
  - Missing label files (sync 0, ≥ 291) are unlabelled frames [L]. Empty files are frames with no objects [V].
- **Keyframes.** **[P]** Primary metrics on 1 Hz keyframes. Their sync indices must be identified first (V-04): the TXT format does not flag them; derive them from the interpolation linearity of tracks, or ask the authors.
- **Class mapping.**
  - MS: 10 classes → 3 [V].
  - OPV2V: vehicle only in the standard benchmark [V: Mixed Signals App. A notes OpenCOOD is single-class].
  - Results are never pooled across class sets.
- **Visibility for stratification (evaluator only).** For each GT box, count points inside it per agent (as ACFR `gt_visibility`). Strata:
  - `RECEIVER_SEES` (TOP or DOME > 5 points);
  - `SENDER_ONLY` (only one sender > 5);
  - `MULTI_SENDER_ONLY`;
  - `NOBODY` (labelled from aggregate but no single agent > 5).

## 5. Splits (detail in [evaluation_protocol.md](evaluation_protocol.md) §2)

- **MS** (single session, pilot P3). Contiguous **time blocks** with one discarded buffer segment between blocks. **[P]**
  - Block T (detector training + reliability fit): mini_1–3, 6, 8, 14–16 and the exposed mini_7, 10–13.
    - The exposed segments are usable for training and development. Valid Point exposed D/G outcomes, not detector outcomes.
  - Buffer: mini_19.
  - Block C (calibration): mini_20, 22–24.
  - Buffer: mini_25.
  - Block E (evaluation): mini_26, 28–35, 37.
  - val mini_9/18/27/36 have no labels and are usable only for unlabelled clean-variation diagnostics.
  - **Caveat: E is 10 segments of the same session ~2 min after C.** Statistical uncertainty is computed over E segments, but the population is one session.
- **OP.** By scenario. The detector's train split is never used for MINT evaluation.
- **VR.** By scenario, following the official test split.

## 6. Resource estimates [E unless marked]

| Item | MS | OP | VR |
|---|---|---|---|
| Raw download | 214 GB for full TARs [V]. **Alternative [P]**: the TARs are uncompressed, so member headers can be walked with HTTP range requests (pilot P3 showed range reads work). Then fetch only the needed members, e.g. 1 Hz keyframes ±1 frame: ~0.75 GB × 3 per segment, so ~65 GB for 29 segments; keyframes alone ~22 GB [E]. Temporal methods need contiguous 10 Hz windows, budgeted per block. | test + validate subset: tens to 100+ GB [U] | [U] |
| Working cache (MINT) | Range images uint16 + direction LUT, ~1.7 MB/frame (5 sensors) → ~15 GB for 29 × 300 frames, if V-06 lossless-enough holds; else ~59 GB for int16 cm xyz + slot | Feature cache per frame: 3 scales × agents fp16 ≈ 2–6 MB/agent-frame, so cache keyframes only | similar |
| GPU training | 1–3 GPU-days (24 GB) + debugging | none | none |
| CPU inference (M1) | ~230 GMAC/frame (5 agents × ~46 GMAC) → ~2–5 s/frame | ~25 GMAC/agent → ~0.3–1.5 s/frame | similar |
| Label counterfactuals | +2 post-backbone passes per sender (cheap; the backbone is cached) | same | same |

## 7. Missing assets and unknowns (blockers marked ★)

- ★ MS checkpoint. Train it, or ask the authors (open question Q5).
- ★ GPU and storage (Q1).
- ★ V-04 label↔sync alignment and keyframe identification for MS.
- Ouster beam intrinsics for MS sensors. Not shipped; fitted from data (P2) [L]. TOP mount tilt (−22°, −7°) undocumented.
- No-return semantics (sky / self-occlusion / min-range / low reflectivity) [U]. **Treated as unknown evidence.**
- Per-point timing / deskew [U]. Scan skew up to 100 ms per rotation; ≤ 50 ms inter-agent [V].
- OPV2V data sizes and licence (L-10); V2V4Real data licence.
- OpenCOOD licence: no redistribution of derivatives [V]. Our code must stay **separate** (R-09).

## 8. Clean end-to-end sanity check (Stage 1 gate S1-G; not a test set)

On development data only (MS: block T; OP/VR: validate):
1. **Coordinates.** Overlay all agents' clouds and GT in TOP/ego for 5 frames per segment. Check placeholders are removed, and that alignment residual on static structure is < 0.2 m.
2. **Labels.** V-04 alignment test. Box-in-points rate per class.
3. **Predictions.** Clean AP within ±0.03 of the published or our training-log validation AP. Non-degenerate per class (AP > 0.1 for every class).
4. **Feature interface.**
   - Per-scale tensor shapes, strides and frame are hashed.
   - Warping a sender's feature twice with identity is a no-op.
   - **V-03 locality**: removing a sender in tile u leaves head outputs outside u bit-identical (fp32) before NMS.
5. **Costs.** Measured per-stage time and peak RSS on the proxy device.

Failure of any item stops the study at Stage 1 with a written diagnosis.
