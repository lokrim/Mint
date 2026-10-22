# 02 — Methodology actually implemented, and why it fails the new objective

Revision 2 (2026-10-22). Every equation below was reconstructed by reading current code (`src/valid_point/…`, working tree at HEAD `14371e6`). All 35 R05 package source files hash-match the R05 final manifest ([RP-01](evidence_ledger.csv)), so this code is the code that produced the R05 tables. Finding IDs (e.g. MT-04) resolve in [evidence_ledger.csv](evidence_ledger.csv).

## 1. Dependency graph (R-stage pipeline)

```text
ASCII PCD (organized W×H grid, incl. placeholder slots — see §4)
  └─ strict reader (float32 x y z intensity) ──► finite XYZ, row order kept
        ├─ D: horizontal XY relative to an assumed sensor XY origin ──► 32 cell counts n_j
        │        └─ q50/q95 references from 2 clean segments ──► a_j=clip((n_j−u_j)/b_j,0,1) ──► D=max_j a_j
        └─ G: 0.5 m voxel centroids (r<80 m, ≤50,000) + causal pose (latest past, ≤150 ms)
                 + previous admitted cloud of SAME stream in SAME replay (may be attacked)
                 ──► q90 directed nearest distance ──► same q95/scale clip ──► G
  arm A ∈ {D, G, max(D,G)} — all required factors known, else unknown
  versions: memoryless A, EWMA Z (τ = 1 s primary; 0.25 s, 2 s sensitivities)
  alarm: score > c, c = order statistic of clean calibration scores (n ≥ 200), else null

pose CSV ──► K (motion residual) — implemented, NOT used by any R-stage arm
evaluator (schedules, clean counterparts, attempt ledgers) ──► offline metrics only
NOT PRESENT: learned encoder, intermediate feature tensor, detector, fusion, GT task metric
```

Each stream is scored only from its own data. No cross-agent evidence enters any arm. Poses and RSU constants supply alignment; they are not independent evidence about scene truth.

## 2. Equations as implemented

**K (MT-01).** `evidence/kinematics.py::measure_motion` takes pose/velocity samples only: `K = ||(p1−p0) − R0·v0·(t1−t0)||` m. Point clouds are not an input. No R-stage arm calls it (grep of `evaluation/real.py`, `replay.py`). Point-only edits with fixed poses cannot change K. If velocity is derived from the same displacement, K ≡ 0. The 15 local odometry CSVs do have six variable twist columns (`frame_id=map`, `child_frame_id=base_link_*`) (DA-11). Which frame the twist is expressed in, where it comes from, and whether it is independent of the pose all remain unknown.

**D (MT-02, MT-03).** `evidence/density.py::count_cells` (lines 22–38): radius in the horizontal plane from a fixed XY origin, half-open bands [0,10), [10,25), [25,50), [50,80) m via `searchsorted(side='right')`, eight 45° sectors, all heights. `evaluation/real.py::fit_references` (127–162) computes linear q50 and u=q95 per sensor×cell over two clean reference segments. Then b = 4(u−q50). Status is `LOW_SUPPORT` if fewer than 200 distinct clouds or fewer than 2 segments, `ZERO_SCALE` if b ≤ 0. `normalize` (165–186) falls back from a cell to its same-sensor range ring (all 8 sectors pooled). If neither is `SUPPORTED`, D is unknown. Otherwise `a_j = clip((n_j−u)/b, 0, 1)` and D = max over all 32 cells.

**G (MT-06, MT-07).** `evidence/temporal_geometry.py`: crop r < 80 m from the stream origin, take 0.5 m voxel centroids, keep at most 50,000 by `linspace` over lexicographically sorted voxel keys. The code comment calls this "spatially uniform", but it is uniform in sort order, not in space. The previous cloud is transformed by `inv(T_map_cur)·T_map_prev`. G is computed only if both clouds have ≥ 100 voxels and 0 < gap ≤ 0.5 s. `G_raw = q90_x min_y ||x − y||` (current→previous only). A 2 m bucket search over Chebyshev shells 0–4 certifies each nearest distance. If any one centroid is uncertified (`NEIGHBOR_SEARCH_BOUND`), or more than 10⁷ pair evaluations are needed (`NEIGHBOR_WORK_BUDGET`), the entire G is unknown. G is normalized like D, with gap contexts g0 (≤0.15 s), g1, g2 and fallback `all`.

**History (MT-08).** `replay.py` lines 245–247: any cloud read with reason `VALID`, a valid transform and an origin becomes the stream's history, **including attacked or anomalous clouds**. The R05 memo uses the same rule (`admitted`). `tests/test_replay_isolation.py::test_attacked_geometry_uses_attacked_prior_cloud` asserts this.

**Combination and EWMA (MT-09, MT-14).** `development_scores.decide`: A = max(required factors) only if all are known. `temporal.py`: ρ = exp(−Δt/τ), Z ← ρZ + (1−ρ)A. The state is keyed by episode/principal/sensor/arm/reference version. It is initialised at the first eligible event. It is "ready" after ≥ 10 updates and ≥ 3τ seconds of contiguous span. Missing A holds Z and publishes unknown. A gap of more than 0.5 s since the last eligible update resets the state. Duplicate or reversed timestamps are rejected without an update. The EWMA score is Z only when ready.

**Calibration (MT-10, MT-11).** `real.py::calibrate` (217–234): per fold × sensor × arm × version, n = number of known clean calibration scores. If n < 200, c is null. Otherwise k = ⌈0.99(n+1)⌉ and c is the k-th sorted value. The alarm fires when score > c. The status is `NO_POWER` if c ≥ 1 **or** all calibration values are identical. For n ≥ 200, k ≤ n always holds, so the "k > n ⇒ c=1" branch never fires. I re-derived all 240 thresholds from the saved `calibration/F*/scores.jsonl.gz`: 0 mismatches, and 0 cases with k > n. **Every c = 1 threshold therefore comes from clipped calibration scores saturating at 1** (at least 2, and up to 229 of 249, values equal to 1). It does not come from a small sample. A strict alarm can never exceed c = 1 on a score bounded by 1. The ten constant-score `NO_POWER` cells have c = 0 and *can* alarm on any positive score. The separate helper `metrics.threshold_power` uses a different rule (`max(scores) ≤ threshold`) and is not what R05 used.

**Metrics (MT-12, MT-13).** `evaluation/metrics.py`:
- Recall counts an alarm only on a reader-valid, nonzero-realized, non-failed event. The all-attempt denominator keeps every scheduled event.
- Clean, identity and benign rates (`false_alarm_metrics`, called from `statistics.summarize_episode`) use **all events of the 25 s episode**, not only the stress window.
- Episode recall (`statistics.py` line 100) counts any in-window alarm, including a preexisting one. R05 recorded 0 preexisting alarms, so this had no effect here.
- Interval recovery for burst interval 0 runs past the second burst. For example, the saved C1 EWMA burst interval-0 recovery is 9.10 s because the quiet run is broken by burst 2 at 10 s.

## 3. Failure mechanisms, each with a counterexample or measurement

| ID | Mechanism | Counterexample / measured evidence | Class | Later repaired? |
|---|---|---|---|---|
| MT-04 | **Count-surplus blind spots.** With fixed references, removing rows makes every n_j non-increasing, so D cannot rise. Moving rows within a cell leaves every n_j, and so D, unchanged. | Saved R05: `003` D-only memoryless paired ΔC is exactly 0 in 24/24 localized-removal and 24/24 rearrangement cells. Random removal *raises* conformity (+0.0059 to +0.4604) because counts drop below the tail. | objective mismatch (analytic) | No; inherent |
| MT-05 | **Clipping/quantile degeneracy.** All n ≤ u map to 0; all n ≥ u+b map to 1. Constructed: u=10, b=4 ⇒ n=12→0.5, n=14→1, n=100→1. | 48 D contexts `ZERO_SCALE` (all far top/dome cells, all folds); 40 G gap contexts `LOW_SUPPORT` (g1/g2 for every sensor). 21 calibration thresholds equal 1 because clean scores saturate. | mathematical defect | Fallback/unknown avoid divide-by-zero; information loss remains |
| EX-05 | **References do not transfer between neighbouring segments.** | Fold F0 (refs C2+C3, calibrate C1): 229/249 clean `003` D scores are exactly 1. Fold F3 (refs C1+C2, calibrate C0): 121/250 are exactly 1. Clean C1 sits at the maximal anomaly for references from segments recorded ~1–2 min later. | benign confounding / insufficient support | No |
| MT-14 | **Max combination and coverage.** max(0.9, 0.1) = max(0.9, 0.8): a G change is hidden under high D. Requiring both factors intersects coverage. | `003` G and max(D,G) never reach n ≥ 200 in any fold or version (memoryless known 181/180/199/116), so 240 of 360 attack cells for these arms *cannot* alarm. | coverage loss | No |
| MT-06 | **Directed novelty only.** If current centroids are a subset of previous ones at identical positions, every distance is 0 even though content was removed. A q90 tail ignores changes to less than ~10% of support. Moving objects and disocclusion are legitimately novel. | Constructed (and R03 test). No calibrated G alarm exists for `003`. | objective mismatch | No |
| MT-07 | **Bounded-search abstention.** One uncertifiable query makes the entire frame unknown, so extreme novelty can produce abstention instead of an alarm. | R02 development: G known 163/250, 82 search-bound unknowns. R05 `003` clean G memoryless calibration known 116–199 of ~250. | compute/coverage | Bound added in R03 to stop runaway cost; abstention persists |
| MT-08 | **History contamination.** Attacked clouds become G's reference, so a persistent fake can become "normal". After the attack ends, clean frames are compared with attacked history. | Code lines above; unit test asserts it. Not quantified in R05 because G could not alarm for `003`. | design limitation | No (a clean shadow would be an oracle) |
| MT-15 | **No independent corroboration.** Every arm uses the sender's own stream. | Honest-companion invariance passes 248/248 (EX-13). This is structurally guaranteed, not evidence of fairness to unique views. | objective mismatch | No |
| EX-03/04 | **Small, correlated calibration support.** ~250 frames from one ~25 s clip per fold. The 1% target has no IID basis. | 156/240 calibration cells have fewer than 200 known scores. τ=2 s never calibrates for any sensor. C0–C3 span 208.6 s in total (DA-13). | insufficient data | Distinct-cloud and segment guards added; data limit remains |
| — | **Artificial early observations.** | S03 `ablations.clean_fixture_rows` produces values by seed/frame arithmetic. S04 `gap._reference_rows` cycles literal patterns, and `fit_track_calibration` emits `u` or `u+1` (SC-01, SC-02). | fixture, not data | Retracted 2026-10-08; R stages use real clouds |
| EX-14 | **No task-level correctness.** No detector, no labels read, no AP, no honest-unique-view utility. | grep: dependencies are `numpy` and `matplotlib` only. No model code exists (DA-15). | missing validation | No |
| **DA-04/05** | **Placeholder slots contaminate D and the attack targets** (new in revision 2, §4) | All four R05 targets are cell `r0:a0`, centred 1.0–1.8 m from the `003` origin at z ≈ 1.2 m. | software/design defect, undetected | **Never noticed or corrected** |

## 4. New in revision 2: organized clouds and placeholder points

Every inspected PCD is an organized grid (`003`/`004` 2048×128, `laser`/`dome` 1024×128, `top` 1024×64, POINTS = W×H). Every cloud repeats one fixed coordinate tens of thousands of times (DA-02; fresh read of 25 local clouds, middle file per stream per segment, [placeholder_probe.json](evidence/r2/placeholder_probe.json)):

| Stream | Repeated coordinate | Share of points (5 segments) |
|---|---|---|
| 003 | (0, 0, 1.63) native | 20.9–24.9% |
| 004 | (0, 0, 1.90) native | 22.7–25.2% |
| laser | (0, 0, 1.90) native | 2.5–5.6% |
| dome | (−41.507, −51.864, −1.340) raw/map = published dome origin | 10.9–13.2% |
| top | (−41.551, −51.878, −1.077) raw/map = published top origin | 36.6–39.3% |

**Hypothesis (DA-03):** these are no-return or invalid beam slots written at the sensor origin. This is not documented on the HF card. For `003` they make up 70–77% of cell `r0:a0` in the sampled clouds (e.g. 55,117/74,453). Consequences:

1. D's innermost ring mostly counts no-return beams, not near-field geometry. The C0 fold reference for `003` r0:a0 has q50 = 74,823 points.
2. `freeze_target` picks the "most occupied" D cell, which is `r0:a0` in all four folds. **Localized removal therefore deletes mostly placeholders**, and **addition injects a 2 m cube of points about 1–2 m from the vehicle sensor**, probably on or inside the ego vehicle. The R05 "addition detection" (EX-07) is a reaction to a dense synthetic blob next to the sensor. It is not a test of a plausible fabricated object.
3. Random removal and displacement act on placeholders in proportion to their share, so about 21–25% of `003` "attacked rows" are not measurements.
4. Totals per frame are fixed by the grid. That explains R02's near-constant `003` crop totals (261,908–261,947 of 262,144).
5. **Opportunity for the ray question:** if the hypothesis holds, the (row, column) index of a placeholder may identify a beam that produced no return. The repeated coordinates also give empirical sensor-origin estimates (RSU origins match the published constants; vehicle sensors at native z = 1.63/1.90 m). Beam elevation/azimuth tables, firing times and the precise meaning of "no return" are still unverified.

## 5. What later stages repaired, and what renaming would not fix

Repaired with evidence: S03 tied-factor KeyError; R02 removal of the pose dependency for vehicle D; R03 work bound and the within-cell rearrangement constraint (invalid run preserved); R04 numerator excluding failed or zero-realized injections, exact reference-set lineage and grouped resample keys; R05 clock-skew availability correction (pre-outcome, reported), Finder `.DS_Store` seal exception and episode-ID order reconstruction (RP-04, RP-05). These are engineering repairs. None of them makes D or G measure feature correctness.

Calling C "reliability" instead of "trust" or "conformity" leaves every mechanism above unchanged:
- the unit is still a whole sender frame;
- the evidence is still self-referential count or novelty statistics;
- clipping and quantile saturation still discard magnitude;
- calibration still rests on one correlated clip;
- placeholders still dominate the near cell;
- nothing links the score to whether an object or feature is correct.

A new unit, a new target that can be checked against ground truth, and independent evidence are required ([06](06_requirements_for_the_new_study.md)).
