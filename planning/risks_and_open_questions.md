# Risks and open questions

Checkpoint 1, 2026-10-22.

## Decisions needed from you (bundled; everything else proceeds on stated provisional assumptions)

| Q | Question | Why it matters | Provisional assumption if unanswered |
|---|---|---|---|
| **Q1** | **Training hardware and storage.** Do you have a CUDA GPU (≥ 16–24 GB VRAM, about 1–3 GPU-days) and ≥ 300 GB of storage (or an external disk)? | Mixed Signals has **no released checkpoint**: training is required. This machine (M1, 8 GB, no CUDA, 21 GB free) cannot train or hold the 214 GB labelled set. | **OP-first**: OPV2V with the released AttFuse checkpoint, inference-only on CPU. VR replication. MS limited to the ray-geometry study and small dev subsets. |
| **Q2** | **Target deployment class.** RSU edge GPU, RSU CPU-only box, or vehicle SoC? A specific board? | Sets the H5 budget and the benchmark device | Benchmarks on the M1 proxy only. No deployment claim. |
| **Q3** | **Permissible receiver inputs.** (a) May the receiver use its own raw LiDAR scan (setting B)? (b) May it decode received tensors and run counterfactual fusion passes (no extra messages)? (c) May senders send any extra metadata (e.g. a CAD-style occupancy map, ~10 KB)? | (a) decides whether ray evidence exists at all. (b) is the core of MINT's effect computation. (c) is only an ablation. | (a) yes, (b) yes, (c) ablation only |
| **Q4** | **Time budget, and real-data priority.** How many weeks, and is an OPV2V-first (simulated) primary result acceptable, with real data as replication? | Determines the stage order and whether to wait for GPU access | ~8–12 weeks; OP-first acceptable |
| Q5 | *(optional)* May we contact the Mixed Signals authors for checkpoints, the keyframe list and the old JSON labels of test segments? | Could remove the training and V-04 blockers | Not contacted |

## Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner/stage |
|---|---|---|---|---|---|
| R-01 | No GPU, so the MS detector cannot be trained | High (current machine) | High | Q1; OP/VR checkpoints | Stage 0 |
| R-02 | Storage: 21 GB free vs 214 GB for MS | High | High | Ranged member fetch of needed frames; range-image cache; external disk | Stage 1 |
| R-03 | AttFuse not pixel-local in the actual checkpoint (e.g. a variant with spatial mixing after fusion) | Low | High | V-03; fallback to the effect-level unit | Stage 1 |
| R-04 | TOP mount tilt (−22°, −7°) undocumented; direction LUT errors | Medium | Medium | V-06 ground-plane cross-check; error budget in τ | Stage 2 |
| R-05 | Label↔sync misalignment; interpolated non-keyframe labels | Medium | High for MS metrics | V-04; keyframes primary | Stage 1 |
| R-06 | Unlabelled real objects (≤ 5 points, outside the crop) corrupt D labels and the empty-region model | Medium | Medium | Aggregate-points rule; UNLABELLED_REGION flag; sensitivity analysis | Stage 3 |
| R-07 | Receiver rays cover few *effectful* tiles, so H6 is untestable or MINT-v0 mostly returns UNKNOWN | **Medium-high** (collaboration helps most where the receiver cannot see) | High | Gate S2-G; fallback M5-A; report as a finding | Stage 2 |
| R-08 | MS is one ~35-min session, so generalization is unestablished | Certain | Medium | Wording; OP/VR replication | All |
| R-09 | OpenCOOD licence forbids transferring derivatives, constraining code release | Certain | Medium | External dependency; adapter only; seek clarification before release | Stage 1/8 |
| R-10 | OPV2V simulated rays lack real failure modes (no-returns, porosity) | High | Medium | Report as simulated; VR/MS replication | Stage 6 |
| R-11 | Too few harmful labels for M5 | Medium | Low | LR only; v0 needs no attack data | Stage 4 |
| R-12 | Adaptive attacks in receiver-unobserved regions succeed | Certain (H4) | Inherent | Measure and report harm admitted; unknown policies | Stage 6 |
| R-13 | OP/VR checkpoint training-split provenance unclear | Medium | Medium | Read the checkpoint `config.yaml`; never evaluate on train scenarios | Stage 1 |
| R-14 | PGD-based attacks too slow on CPU | High (no GPU) | Medium | Keyframe windows; fewer steps; record the restriction | Stage 5 |
| R-15 | Baseline feature message (~29 MB dense) is unrealistic for V2X | High | Low for the science, medium for the deployment narrative | Report; quantization stress | Stage 7 |
| R-16 | Calibration shift between blocks (precedent EX-05) | Medium | High for H1/calibration claims | Measure on E; per-unit calibration; never assume transfer | Stage 6 |
| R-17 | Old OpenCOOD stack (Python 3.7, CUDA kernels for NMS/IoU) may not run on Apple Silicon CPU | Medium-high | High for OP-first on this machine | Python 3.8–3.10 + PyTorch CPU; CPU NMS/IoU fallbacks; test in the first Stage-1 hour | Stage 1 |
| R-17-update | (2026-10-22) The CPU stack runs. NMS and IoU are CPU code paths (Cython/shapely). **New:** open3d + torch deadlock, so a verified stand-in is used. Remaining: equivalence of the voxelizer stand-in to real spconv is unverifiable without spconv; the full-test AP reproduction (V-01) is the end-to-end check. | — | — | Full reproduction after download approval | Stage 1 |
| R-19 | Disk: 17 GB free; full OPV2V test 21 GB, validate 40 GB | Certain | High | Stream scenario by scenario; cache features at keyframe stride; delete raw data | Stage 1 |
| R-20 | OPV2V validate = 9 scenarios: 7 small (7.0 GB total) + 2 large (11.1 GB, 21.7 GB, 7 CAVs). 3 small ones are now block T (D-25), so calibration C has at most 4 small scenarios unless the large ones are streamed. | Certain | High for calibration claims | Ask to stream the large scenarios (each > 3 GB, so they need a chunked fetch-process-delete); or split C by time within large scenarios (weaker) | Stage 3 |
| R-07-update | (2026-10-23) Coverage gate passed overall (49.7%), but only 30% of *useful ADD* effects are receiver-visible. Most cooperative benefit lies outside receiver-ray evidence, as feared. | Confirmed | High for H6 framing | Report; feature-only channels (M5) for unobserved tiles; H4 analysis | Stage 3+ |
| R-18 | Novelty overlap with recent preprints (PoseGuard, TrustReflect, GLST) grows | Medium | Medium | Re-search before writing; contribution framed on the estimand and evaluation | Stage 8 |

## Open scientific questions (not blocking Stage 1)

- How large is the fraction of *useful* cooperative effects that lie in receiver-unobserved tiles? This bounds every trusted-evidence defense. To be measured on clean data in Stage 2.
- Does the real-object beta-binomial overdispersion φ vary strongly by class and range, so that small classes lack data?
- Should SHIFT effects use a likelihood-ratio test between poses (current proposal), or a continuous localization residual?
- Can the receiver's own detection of the sender vehicle validate claimed sender poses (T3) reliably at the RSU?

## Literature items still open

L-01..L-10 are listed in [literature/search_log.md](literature/search_log.md).
