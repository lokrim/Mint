# V-02, V-05 and Stage-2 ray-geometry report (OPV2V validate, development)

Run 2026-10-23, user-approved streaming of 2–3 validate scenarios (each ≤ 3 GB).
- Record: [`runs/20261023-S2-validate/`](../runs/20261023-S2-validate/summary.json).
- Runner [`runners/stage2_validate.py`](../runners/stage2_validate.py); summary [`runners/stage2_summarize.py`](../runners/stage2_summarize.py).
- Code under test: [`src/mint/geometry/rays.py`](../src/mint/geometry/rays.py), [`src/mint/model/warp.py`](../src/mint/model/warp.py), [`src/mint/effects/effects.py`](../src/mint/effects/effects.py).
- Tests: `tests/` (14 passing, including a mutation check that fails on the "no-return = free space" bug).

**Development evidence only.** Three validate scenarios: no test data was used and no hypothesis is tested here.

## Data handled

| Scenario | CAVs (used/frame) | Frames | Downloaded | Raw on disk (peak) |
|---|---|---|---|---|
| 2021_08_22_13_37_16 | 2 | 136 | 0.84 GB | 0.82 GB |
| 2021_08_21_17_30_41 | 3 | 158 | 1.59 GB | 1.49 GB |
| 2021_08_20_21_48_35 | 5 in folder, 4 within range | 110 | 1.83 GB | 1.74 GB |

- Total 4.26 GB, one scenario at a time. Raw data deleted afterwards.
- **The validate split has 9 scenarios.** Two of them are 11.1 GB and 21.7 GB (7 CAVs each) and exceed the 3 GB rule. The other 7 total 7.0 GB.
- The MINT fit and calibration pool is therefore small unless the two large scenarios are streamed (needs your approval: R-20).

## V-02: own-frame encoding + receiver warp

Pooled over 404 frames; OpenCOOD default AP:

| Path | AP@0.3 | AP@0.5 | AP@0.7 |
|---|---|---|---|
| OpenCOOD `proj_first=True` (checkpoint's training protocol) | 0.954 | 0.944 | 0.874 |
| Ours, same features (our fusion re-implementation) | 0.954 | 0.944 | 0.874 (identical in every scenario) |
| **Own-frame encoding + receiver bilinear warp (D-13 protocol)** | **0.853** | **0.762** | **0.515** |

- The drop is large in every scenario (AP@0.7: 0.887 → 0.676; 0.896 → 0.374; 0.847 → 0.603).
- The checkpoint was trained on features computed in the receiver frame. Warped own-frame features are out of distribution (resampling, and rotated pillar grids).
- Our warp code is unit-tested: direction, identity, and translation by whole cells.

**Consequence.** With this checkpoint, D-13 cannot be used without retraining, which needs a GPU.
- **Paper vs code.**
  - The OPV2V paper (§IV, "Metadata Sharing and Feature Extraction") *describes* a deployment pipeline: CAVs broadcast relative poses, and neighbours project their point clouds into the ego LiDAR frame before extracting features.
  - OpenCOOD *implements* this as a central dataloader transform. One process projects every agent's points with dataset poses (noise-free, synchronous in this configuration), then one batched model call encodes all agents. No pose is broadcast and no message is exchanged.
  - The [threat model](information_and_threat_model.md) §6 has the verified code trace.
- **Decision D-13b (user, 2026-10-23).** The OPV2V study uses this `proj_first` *coordinate convention*, matching the checkpoint.
  - Pose sharing, per-recipient encoding cost, honest projection and synchrony are recorded as **protocol assumptions A-P1..A-P4**, not verified behaviour.
  - Sender-side pose manipulation is an attack scenario (A-M1), not implemented.
  - Received features remain untrusted.

## V-05: message size

| Item | Value |
|---|---|
| Per-sender message (3 fusion scales: 64×100×352 + 128×50×176 + 256×25×88) | 3,942,400 values |
| Dense fp32 / fp16 | **15.77 MB / 7.89 MB** per sender per frame |
| Non-zero pixel fraction (minimum over 785 sender-frames) | 1.00 at every scale: no sparsity to exploit |
| OpenCOOD README "126.8 Mbit before compression" | 15.85 MB (our count is within 0.5%, so the README measures the same dense 3-scale fp32 message) |

At 10 Hz that is about 1.26 Gbit/s per sender, far beyond V2X links. This confirms R-15: the uncompressed baseline is a research setting. The compressed checkpoint variant (1.98 Mbit) exists in the same zip but is not used here.

## Ray semantics of OPV2V receiver scans

- **Geometry.** 64 rings, evenly spaced every 0.43° from −25.0° to +2.0°, recovered from the unorganized cloud by elevation clustering. CARLA's ray directions are on a fixed elevation grid.
- **Azimuth is not on a fixed grid:** about 8,190 slot collisions per frame with ~1,016 columns. Hence ray counting is **point-wise** (each recorded return is one ray; `classify_points`). The range image is used only for no-return rates.
- **No-returns are not free space** (supports D-06 with direct evidence). On rings below −10°, every ray must hit the road within range, yet only **76.3%** of slots hold a return; above the horizon, 67.2%. About a quarter of certainly-blocked rays leave no return: CARLA drop-off and/or azimuth binning.
- **Self box (new D-24).** OPV2V ground truth includes the **ego vehicle itself** (other CAVs see it), and senders' contributions "add" it as an effect (159 ADD effects).
  - The roof-mounted CARLA LiDAR does not see its own vehicle, so the ego's rays pass straight through its own box.
  - My first self-box check was 3D and missed this, because the sensor sits *above* the box. It is now BEV-based, with a regression test.
  - This run used a documented post-hoc proxy (box centre within 1.5 m of the sensor). Such effects are NOT_APPLICABLE for ray evidence. The receiver could validate them from its own pose, which is out of scope for now.

**Genuine objects** (7,721 GT boxes; 404 self-boxes excluded):
- 85% are seen by ≥ 3 receiver rays, 80% by ≥ 5.
- Support ratio SUP/(SUP+TRAV), median (p10) by range: 0–20 m 0.91 (0.87); 20–40 m 0.93 (0.82); 40–70 m 0.96 (0.83); 70+ m 1.00 (0.82).
- Real, visible objects are strongly supported; traversal through genuine objects is uncommon in simulation (no porous classes in OPV2V).

## Counterfactual effects on clean data (development labels approximate D)

| Effect / label | n | not applicable (self) | seen by ≥ 3 receiver rays |
|---|---|---|---|
| ADD / useful (added real object) | 684 | 159 | 155 |
| ADD / harmful (added FP) | 39 | 0 | 13 |
| REMOVE / useful (removed FP) | 118 | 0 | 86 |
| REMOVE / harmful (removed a real object) | 110 | 0 | 69 |
| SHIFT / useful, neutral, harmful | 456 / 262 / 63 | 0 | 328 / 181 / 41 |

- 1,732 effects in 1,705 (frame, sender, tile) units.
- **Benign harm exists:** 212 harmful effects on clean data (12%), most of them senders *suppressing* real objects (110 REMOVE/harmful).
- **Cross-tile effects:** 76/1,732 = **4.4%** of effects have their box centre in different tiles with and without the contribution. That is close to the 5% tolerance used in gate S1-G, so D-22's two-tile attribution is needed.

## Gate S2-G (receiver coverage of effectful tiles): **passes**

| Criterion | Value | Gate |
|---|---|---|
| Effectful units whose every effect has ≥ 3 receiver rays | **49.7%** | ≥ 20% ✅ |
| Same with ≥ 5 rays | 38.9% | (reported) |

As predicted in R-07, **coverage is weakest exactly where collaboration helps.** Of the 525 non-self *useful ADD* effects, only 155 (30%) are seen by ≥ 3 receiver rays. The other 70% are objects the receiver cannot observe, which receiver-ray evidence cannot verify (H4 region).

## Development pilot: does receiver support track harm? (not a hypothesis test)

Effects seen by ≥ 3 rays only; support ratio = SUP/(SUP+TRAV) of the claimed box:

| Effect | Harmful n | Useful n | Median support, harmful vs useful | AUROC (direction as specified in M3) |
|---|---|---|---|---|
| ADD (claims "object here") | 13 | 155 | 0.13 vs 0.89 | 0.82 |
| REMOVE (claims "nothing here") | 69 | 86 | 1.00 vs 0.50 | 0.80 |

- The direction matches the M3/M4 physics: fakes lack support, and wrongly removed real objects keep it.
- With 13 harmful ADDs from 3 scenarios, this is **a feasibility signal only**. These 3 scenarios have now been used for a method-level look, so they move to the fit block T and must not be used for calibration (D-25).

## Decisions and items opened

- **D-13b (user decision, appended to the log; D-13 kept):** the OPV2V study uses the `proj_first` coordinate convention. The own-frame variant needs retraining.
- **D-24:** BEV self-box rule.
- **D-25:** the 3 pilot scenarios go to block T only.
- **R-20:** validate split = 7 small scenarios (7.0 GB) + 2 large (11.1 GB, 21.7 GB); the calibration pool is small.
- Next: Stage 3 (beta-binomial fits, calibration) needs more validate data: **ask before streaming the rest.**
