# Actual methodology and failure mechanisms

All equations below reconstruct inspected code, not a proposed replacement. Exact named functions and line-numbered excerpts are in [source excerpts](evidence/source_excerpts.md); claims and populations are in [ledger](evidence_ledger.csv), F004–F018, F020–F029 and F043.

## Dependency graph

```text
PCD bytes -> strict ASCII float32 reader -> finite XYZ
   | -> sensor identity + fixed origin XY -> 32 counts n_j -> D references -> D
   | -> voxel centroids + current causal pose
   |       + previous eligible cloud/pose FROM SAME REPLAY -> directed G -> G references
   |                                                                  |
   +----------------------------------------------------> all-required arm A
                                                                     |
                                                        per-arm/time-version EWMA
                                                                     |
                                       independent clean calibration threshold -> alarm/null

pose pair + prior velocity (+ prior orientation) -> K diagnostic [not primary R score]
evaluator: schedules, clean counterpart, changed-row ledger -> OFFLINE metrics only
No learned encoder -> no intermediate feature tensor -> no detector/fusion -> no GT task metric
```

Pose/calibration provide alignment assumptions, not independent evidence of scene truth. Other streams are replayed but D/G score each stream from itself; companion invariance is structurally expected. R05’s trusted arrival equals source time and pose availability equals recorded pose stamp are modeled, not measured network facts. [F009,F028,F036–F038]

## K: motion self-consistency

`measure_motion` selects the latest two eligible samples, takes prior velocity, rotates it into the position frame when needed, and returns

`K_raw = ||(p1-p0) - R0 v0 (t1-t0)||_2` metres.

Point clouds are absent from the function signature. Alter every point while retaining pose/velocity and K remains identical. Choosing `v0=R0^-1(p1-p0)/dt` from the very displacement under test makes the residual identically zero: a constructed tautology, not independent validation. Earlier-interval pose differences avoid that exact identity but still share pose errors and measure trajectory smoothness. Legitimate acceleration can raise the residual. Same-sender consistent spoofed pose/velocity can pass. Variable local twist exists, but neither its independence nor frame/online latency is established. Excluding K from R primary scoring repairs the earlier dependency mismatch; it does not solve geometric reliability. [F009–F010]

## D: count surplus and normalization

`count_cells` uses radius in native horizontal XY relative to a declared origin, half-open radial bands `[0,10),[10,25),[25,50),[50,80)` m, eight 45° sectors and all finite heights. It records excluded points; no surface, ray or object identity is represented. For each sensor-cell, reference fitting computes linear empirical quantiles:

`u_j=q95(n_j); b_j=4(q95(n_j)-q50(n_j)); a_j=clip((n_j-u_j)/b_j,0,1); D=max_j a_j`.

R05 requires at least 200 distinct clean clouds across both declared reference segments and positive scale. Unsupported cell references fall back only to same-sensor, same-range sector-pooled distributions. Pooled observations count eight sector values per cloud, while support counts distinct clouds. G has sensor-gap contexts and sensor-wide fallback. No cross-sensor fallback is implemented. All 32 D cells must normalize; otherwise D is unknown. [F011,F013]

**Removal blind spot (analytic):** with fixed references, removing points makes every count nonincreasing, therefore D cannot increase. Removing all points from a supported present cloud can yield D=0, even if the lost objects matter. Absence/malformed input instead yields unknown. Rearranging points within each cell leaves D exactly unchanged even if object geometry is destroyed. Moving outside the crop or adding below reference tails can also be invisible. These are properties of this score, not software errors. Saved R05 localized removal and constrained rearrangement have zero paired D conformity change in every corresponding segment/severity/schedule cell. [F012,F027]

**Benign confounding:** legitimate traffic density, crop crossings and sampling changes can raise counts. R03 benign noise raises anomaly in its development demonstration; R05 clean D-only sender `003` alarms 29/999, concentrated in C1. Calling this score “reliability” would not distinguish a correct rare viewpoint from malicious surplus. [F022,F043]

**Scale/quantile degeneracy:** constant reference values produce b=0; an ad hoc epsilon would convert ordinary small changes into arbitrary large scores. The code uses fallback/unknown instead, which is safer arithmetic but changes the effective baseline and coverage. For b>0, all counts <=u map to zero and all counts >=u+b map to one. Constructed example: u=10,b=4 maps n=10 to 0, n=12 to .5 and both n=14 and n=100 to 1. The loss of magnitude is real by construction. R05’s 800 reference contexts contain 712 `SUPPORTED`, 40 `LOW_SUPPORT`, 48 `ZERO_SCALE`; these are context counts, not independent observations. [F013–F014; numeric_audit.json]

## G: directed novelty, support and computational abstention

Crop each cloud at horizontal radius <80 m, voxelize at 0.5 m, represent occupied voxels by centroids, and deterministically cap at 50,000 centroids by lexicographic-index spacing. Transform previous centroids into the current coordinate convention using `inv(T_map_current) @ T_map_previous`. If both have >=100 occupied voxels and 0<gap<=0.5 s, compute

`G_raw = q90({ min_{y in previous_compensated} ||x-y|| : x in current_centroids })` metres,

then the same q95/scale/clipping normalization. Centroid cap/downsampling is reported as approximation. Ego-motion compensation does not deskew a scan or remove moving objects. [F015–F016]

**Direction counterexample (constructed):** if current occupied centroids are a nonempty subset of the previous set at identical positions, every directed distance is zero despite removal. This exact example holds centroid locations fixed; actual voxel centroids may move after removing rows. There is no previous-to-current free-space test. A sufficiently small changed fraction can remain below the q90 tail; finite-sample interpolation and mixed-voxel centroid shifts prevent interpreting “10%” as a universal sharp boundary. A moving car or disoccluded wall can produce novelty while being correct. [F015]

The 2 m bucket search tries Chebyshev shells 0–4 and certifies a distance only when no unsearched bucket can improve it. If even one query cannot be certified, G becomes `NEIGHBOR_SEARCH_BOUND`; exceeding 10,000,000 candidate pairs yields `NEIGHBOR_WORK_BUDGET`. Chunked distances limit temporary memory, but Python bucket loops and voxel sorting remain substantial. Extreme novelty can cause abstention instead of an alarm. In clean C0–C3 sender `003`, G is valid on 116/250,181/249,180/250,199/250 events respectively; the remaining rows are one initial-history unknown per segment and bounded-search failures. These saved raw reasons were freshly recounted. [F016,F025; saved_record_checks.json]

**History contamination:** after measuring a valid current cloud with valid transform/origin, replay caches it even if anomalous or G was unknown. A persistent fake structure can become its own reference; after an attack stops, the clean cloud is compared with attacked history. Tests explicitly demonstrate changed prior geometry changing later G. A clean shadow would be an oracle, not a deployment fix. Policy alternatives need separate calibration/coverage evaluation. [F017]

## Combination, temporal state and calibration

For D-only, G-only or max(D,G), **all required factors must be known**; `A=max(required factors)`, `C=1-A`. A high existing D can hide a G change: max(.9,.1)=max(.9,.8)=.9. Adding G to a D arm can reduce coverage to an intersection even though max cannot decrease on common numeric inputs. Separately calibrated thresholds mean there is no universal alarm ordering between arms. [F014]

EWMA keeps state by `(episode,principal,sensor,arm,reference_version)`:

`rho=exp(-dt/tau); Z_t=rho Z_prev+(1-rho)A_t; C_time=1-Z_t`.

First eligible A initializes Z. Readiness requires >=10 eligible updates and elapsed contiguous span >=3*tau. Missing A holds internal state but publishes unknown. Time since last eligible update >0.5 s resets; shorter missing gaps can be bridged using elapsed dt. Duplicate/reversed timestamps reject without ordinary update. Tau=1 s is primary; .25 and 2 s are separately calibrated sensitivities. The two-second sensitivity has fewer than 200 known calibration rows throughout this grid, so its threshold is unavailable; silence is not recovery. [F018,F020]

Each sensor/arm/version uses a separate clean calibration segment and `k=ceil((n+1)*.99)`. If n<200, threshold null; otherwise c is the kth sorted score, or 1 when k>n. Alarm is strictly `score>c`. The nominal 1% is a target, not demonstrated future FPR under correlated frames/distribution shift. With roughly 250 frames, a few upper-tail values and clipping can determine c. Two reference segments and one calibration segment do not establish independent acquisition sessions. [F020–F022,F039]

`NO_POWER` in `real.calibrate` means c>=1 **or constant calibration scores**. Ten constant-zero cells can alarm at score>0; 21 c=1 cells mathematically cannot alarm on score<=1. The separate helper `metrics.threshold_power` uses `max(scores)<=threshold`, a different criterion; it is not the R05 calibration writer. Keep these labels as saved while explaining their meanings. [F021]

## Failure classification and repair status

| Class | Evidence/mechanism | Later correction? |
|---|---|---|
| Mathematical degeneracy | b=0 and clipping; strictly bounded score at c=1 | Explicit fallback/unknown implemented; loss of information remains. |
| Objective mismatch | Counts/novelty versus individual feature or object usefulness | Not repaired; no detector/GT task path. |
| Insufficient support | Calibration nulls, short warm-up and correlated scenes | Distinct-cloud and segment guards improved; data limitation remains. |
| Benign confounding | Density, moving structure, viewpoint, pose/clock perturbations | Controls retained; cannot infer intent. |
| Unavailable inputs | Physical origins, visibility, online pose latency, independent velocity | Still unresolved. |
| Software/boundary defects | Vacuous early isolation, incorrect rearrangement, clock skew and episode IDs | Later R tests/generator/report repairs exist; preserve original failed evidence. |
| Execution/resource failures | Neighbor work, scratch cap, restart collisions, notebook dependencies | Bounds and repairs permit completed R05; deployment budget still untested. |
| Stale documentation | Pending GR5 and absent exports after final seal | Corrected in this handoff only; original documents preserved. |

Changing the word “trust” to “reliability” fixes none of the dependencies, loss of information, calibration support, independent-evidence requirements or absent task validation. A new score needs a new unit, measurable target and falsifiable link to perception correctness. [F043–F045]
