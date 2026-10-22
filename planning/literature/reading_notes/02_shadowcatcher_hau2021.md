# Shadow-Catcher: Hau, Demetriou, Muñoz-González, Lupu, ESORICS 2021 (+ object-hiding follow-up, 2022)

- **Citation.** `hau2021shadowcatcher`, `hau2022hiding`. arXiv 2008.12008. DOI 10.1007/978-3-030-88418-5_33.
- **Access.** FULL-SKIM: §3 motivation, §4 shadow analysis, §5 method (Phases 1–3). Follow-up: ABSTRACT only. Read 2026-10-22.

## Question, unit, inputs
- **Question.** Do detected objects cast the LiDAR "shadow" (point-void region behind them) that real objects must cast?
- **Unit.** One detected 3D box.
- **Inputs.** The single-vehicle point cloud and the detector's boxes.

## Method
- **Phase 1 (2D/3D shadow region proposal).** Ray optics from the LiDAR origin through the box's ground-projected corners gives the boundary lines. The shadow length is bounded by the sensor range. The 3D version adds a height band.
- **Phase 2 (genuine-shadow verification).** Points inside the shadow region get exponentially decaying weights by distance from the shadow start (α parameter). The aggregate anomaly score (eq. 4) is thresholded empirically.
- **Phase 3 (adversarial shadow classification).** DBSCAN density features inside anomalous shadows separate ghost shadows from invalidated genuine shadows.
- **KITTI motivation.** In 120 manually annotated scenes, objects co-occur with shadow regions. The ground-reflection density falls sharply with range, which limits the effective distance.

## Our explanation
- "Points behind the box inside its shadow" are counted as *contradiction* evidence (rays that traversed the object). This is the same physics as CARLO LPD, organised around the shadow rather than the box frustum.
- Their noise weighting is an ad hoc way of saying that not every traversing ray proves absence: porous objects, edges and calibration matter.

## Threat model and limits
- Ghost injection by a physical spoofer.
- The follow-up paper states the key blind spot: with **object hiding** there is no box, so Shadow-Catcher cannot run. Detecting removals needs a search over void regions.
- Range limit from ground-return sparsity.

## Compute
- Reported about 0.003–0.021 s per object on commodity hardware (from the abstract and search summary; table not re-read).

## Code
- Not checked.

## What transfers
- Shadow geometry as a second ray test, complementary to LPD (behind-object region vs inside-box).
- An explicit range limit beyond which contradiction evidence is weak, so the status is unknown.

## What does not transfer
- The single-sensor assumption.
- The empirical threshold.
- Phase-3 classifier trained on ghost vs invalidation types we do not use.

## Experiment
Ablation inside candidate M3: inside-core traversal only, shadow-region returns only, or both. Measure the false-contradiction rate on GT-matched genuine objects by class and range ([evaluation protocol](../../evaluation_protocol.md) §8 ablation AB-2).
