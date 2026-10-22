# CARLO / SVF: Sun, Cao, Chen, Mao, USENIX Security 2020

- **Citation.** `sun2020carlo` (references.bib). URL: https://www.usenix.org/system/files/sec20-sun.pdf
- **Access.** FULL-CLOSE on §5.3 (occlusion patterns) and §7 (CARLO design and evaluation). §6 (attack) and §8 (SVF) skimmed. Read 2026-10-22.

## Question, unit, inputs
- **Question.** Can occlusion physics ("free space") expose spoofed front-near vehicles that detectors accept?
- **Unit.** One detected bounding box in a single-vehicle LiDAR frame.
- **Inference inputs.** The ego LiDAR cloud and the detector's boxes. Single agent, no cooperation.

## Threat model and trusted evidence
- A physical spoofer injects up to ~60–200 points (Adv-LiDAR-class capability).
- The point cloud is the attacked object itself. The defense relies on the attacker being *unable* to remove genuine returns or create consistent occlusion: sensor-attack capability is limited.
- A white-box adaptive attacker tries to shrink box volume (§7.2.1, eq. 7).

## Core equations (p. 885–886)
- **FSD (§7.1.1, eq. 5).**
  - Grid the space into 0.25³ m³ cells.
  - `FS(c) = 1` if a cell lies on any ray segment from the sensor origin to a measured point.
  - `f_B = Σ_{c∈B} FS(c) / |B|`, the fraction of box cells that are free space.
  - Genuine vehicles have small `f_B` (they occlude their own interior). Spoofed ones have large `f_B`.
- **LPD (§7.1.2, eq. 6).** The frustum of B is split into B↑ (in front), B and B↓ (behind).
  - `g_B = #points in B↓ / #points in B ∪ B↓ ∪ B↑`, the fraction of rays that penetrate the box and return behind it.
  - **This is the colleague's support/traversal ratio, almost exactly.**
- **Hierarchy (§7.1.3).** LPD with two thresholds filters clear cases. Uncertain boxes go to FSD.

## Our explanation
- `g_B` counts "traversing" rays relative to all rays in the box frustum. `f_B` is the volumetric version.
- Both are uncalibrated ratios. Thresholds come from empirical CDFs of KITTI training boxes vs 600 rendered attack traces.
- The authors themselves show that the `g` distributions **overlap** once detector box error is included (Fig. 11). The cause is ground-plane points, not object physics.

## Data, labels, fairness, realism
- KITTI train/val. Attack traces rendered at 5–8 m in front of the victim.
- Precision ≥ 99.5% on validation. The misses are vehicles over 40 m away.
- Attack realism: limited-point spoofing. Not insider fabrication.

## Compute
- FSD about 100 ms per vehicle (C++, i7-6700K CPU).
- LPD about 5 ms per box (Python, RTX 2080).
- Hierarchy about 8.5 ms mean per vehicle.
- Cost of building the ray-occupancy grid per frame: not reported separately.

## Code and licence
- Not checked this session. No link noted in the text we read.

## What transfers to MINT
- The FSD and LPD definitions are the canonical prior art for "support vs traversal". MINT must cite them as the source of any ray ratio.
- The hierarchical cheap-then-expensive design.

## What does not transfer
- **Single-agent assumption.** CARLO checks the box against the *same* cloud that produced it. In CP the receiver must check a sender's contribution against the *receiver's own* rays. These only cover the receiver's lines of sight.
- **Point-count spoofing assumption.** A white-box insider can render fully occlusion-consistent fake points from its own viewpoint (CAD's ray-casting attack). CAD showed that CARLO then drops to near chance (CAD §6.4.4: naive RC makes CARLO "close to random guessing"; adaptive Sampled-RC gives TPR 63.8%, FPR 14.7%).
- **Uncalibrated thresholds.** Distribution-overlap thresholds are not probabilities.

## Experiment to test transfer
Compute receiver-own `g_B` and `f_B`, using range-image indexing, for:
- sender-decoded hypotheses in receiver-observed tiles;
- GT-matched true objects;
- injected fakes (A-R2).

Then compare AUROC per class and range against the MINT target `D`. Expect pedestrians and bikes to have high `g` even when genuine (porosity), as Shadow-Catcher notes. See [methodology candidates](../../methodology_candidates.md) M3/M4.
