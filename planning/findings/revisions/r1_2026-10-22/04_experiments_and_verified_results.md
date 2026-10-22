# Experiments and verified results

All numbers here describe saved observations or deliberately constructed cases. Source R05 run is `artifacts/20261012T134149Z-R05`, frozen protocol hash `80694538e8549256934b3a314301cc8ca821efe0bf36ff4071eab9681f2c039c`. [Ledger](evidence_ledger.csv) F004–F006, F019–F029, F046–F050 and [results_summary.csv](results_summary.csv) provide filters, units and denominators. No replay was rerun.

## Earlier experiments

S01 uses one toy road template with seeded changes. S02 checks motion/count/availability arithmetic with hand inputs. S03’s source `ablations.clean_fixture_rows` directly generates residual/count values. Its saved calibration and score tables therefore test formula behavior, not independent scenes. S04 uses 400 fixed tiles and twelve constructed cases: tile attack alarms 3/7 versus oracle boxes 5/7; each has 2/5 benign alarms and one abstention. On common-known attacks, counts are 3/6 versus 5/6. These are exact saved constructed-case counts; oracle boxes and annotation strings do not imply an operational proposal detector. [F004–F007]

R01’s accepted intake selects 50 clouds per stream (250 total) from mini_7 plus three odometry CSVs. R02 accepted raw development replay reports D 250/250 and G 163/250, with 82 search-bound unknowns and five initial-history unknowns. R03 expands the development replay to 1,250 clean events over the first 25 seconds: one middle-severity sustained episode for each family, one displacement burst, noise and combined alignment/availability controls, plus five identity writer/reload checks. Its first-ten-second exploratory references require >=50 distinct cloud rows; the [10,25) diagnostic calibration block never reaches 200 known scores. Its null alarms cannot establish recall, delay or recovery. Exact saved gate evidence is preserved in [run status extracts](evidence/run_status_and_failures.json); these old cloud computations were not independently repeated. [F041]

## Frozen R05 design and full intervention population

F0 tests C0, calibrates C1, fits C2/C3; F1 tests C1, calibrates C2, fits C3/C0; F2 tests C2, calibrates C3, fits C0/C1; F3 tests C3, calibrates C0, fits C1/C2. C0–C3 are mini_10–13. Every arm sees the same named episode and time population. Sessions are not verified independent; folds share training observations. Repeated interventions are paired/dependent, not additional scenes. [F039]

| Family | Severity values and exact operation | Schedules / target |
|---|---|---|
| random_removal | 0.1,0.3,0.6 of all sender rows, floor(f*N), without replacement | Sustained [5,15) s; bursts [5,7),[10,12) s |
| localized_removal | 0.25,0.5,1 of rows in frozen target cell | Same schedules; most occupied D cell in sender’s first 3 s |
| displacement | 0.2,1,3 m in local +x, selected 25% of rows | Same schedules; total count preserved, cells may change |
| rearrangement | 0.2,1,3 m horizontal proposals, selected 25%, up to ten directions | Each accepted point remains in original valid D cell; failed moves retained |
| addition | 0.01,0.05,0.2 of current N, synthetic uniform points in 2 m cube | Frozen target-cell centroid; intensity sampled from sender values |

The primary manipulated sender is `003`; poses/timestamps and other streams are unchanged in point-attack episodes. These are digital point-cloud overlays, neither intermediate-feature attacks nor physical laser simulations. Each fold has 30 positive attacks, five family-specific zero-severity identity controls, one natural clean replay and 26 benign stresses: coordinate noise sigma .02/.1 m; assumed adapter translation .05/.2 m; yaw .2/1 degree; modeled source-clock skew −50/−10/+10/+50 ms; raw downsampling .1/.3/.6; each stress under both schedules. Primary arms are D-only, G-only, max(D,G), each memoryless or EWMA tau=1 s; sensitivities tau=.25/2 s are also saved and separately calibrated. Thus the actual tables include **four**, not merely two, temporal versions. [F019]

All 248 flow rows were parsed. Across non-clean episodes there are 17,703 scheduled attempts and 17,703 reader-valid records, with zero full injection failures. These include identity and benign controls and must not be called positive attacks. Each of five positive families has 1,683 reader-valid/nonzero-realized scheduled events. All 1,683 rearrangement events contain partial failed moves: 64,852 of 110,297,088 intended row moves remain unchanged; every recorded per-cell-count delta is zero. Row opportunities reuse scenes and are not statistical replicates. [F026; saved_record_checks.json]

## Calibration and coverage before effectiveness

Of 800 reference contexts, 712 are supported, 40 low-support and 48 zero-scale. Of 240 calibration cells (4 folds ×5 sensors ×3 arms ×4 versions), 156 are `INSUFFICIENT_KNOWN`, 31 `NO_POWER` and 53 `AVAILABLE`. `NO_POWER` splits into 21 c=1 cells and ten constant-zero c=0 cells. A c=0 cell can produce later positive alarms. Threshold availability, known score, warm-up readiness and known alarm are distinct. [F020–F021]

For sender `003`, D-only memoryless calibration is available numerically in each fold, but F0/F3 c=1 cannot alarm. G-only and max(D,G) have no available threshold in any version; memoryless known calibration counts F0–F3 are 181,180,199,116, all below 200. Tau=2 has insufficient calibration for every sensor/arm cell. The saved “common support” table intersects all three methods and all four temporal versions; this makes it empty and uninformative for this grid. It does not mean useful pairwise common-support comparisons are mathematically impossible. [F025; r05_calibration_cells.csv]

## Complete primary attack grid

Cells below are **alarm numerator / all scheduled sender attempts**, pooled across four segments. `0/d †` for G or max means no calibrated alarm eligibility, not observed clean-like evidence. D results still include c=1 and other inability-to-alarm conditions; inspect thresholds and segment rows before calling all zeros confident misses. Full four-version results, eligible/realized and episode denominators, per-segment variation and omissions are in [complete grid](evidence/r05_sender_complete_grid.csv). No family/severity/schedule is omitted.

| Family | Severity | Schedule | D memoryless | D EWMA | G memoryless / EWMA | max memoryless / EWMA |
|---|---:|---|---:|---:|---|---|
| random_removal | 0.1 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| random_removal | 0.1 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| random_removal | 0.3 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| random_removal | 0.3 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| random_removal | 0.6 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| random_removal | 0.6 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| localized_removal | 0.25 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| localized_removal | 0.25 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| localized_removal | 0.5 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| localized_removal | 0.5 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| localized_removal | 1.0 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| localized_removal | 1.0 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| displacement | 0.2 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| displacement | 0.2 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| displacement | 1.0 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| displacement | 1.0 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| displacement | 3.0 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| displacement | 3.0 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| rearrangement | 0.2 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| rearrangement | 0.2 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| rearrangement | 1.0 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| rearrangement | 1.0 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| rearrangement | 3.0 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| rearrangement | 3.0 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| addition | 0.01 | sustained | 0/399 | 0/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| addition | 0.01 | burst | 0/162 | 0/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| addition | 0.05 | sustained | 0/399 | 10/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| addition | 0.05 | burst | 0/162 | 4/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |
| addition | 0.2 | sustained | 199/399 | 220/399 | 0/399 † / 0/399 † | 0/399 † / 0/399 † |
| addition | 0.2 | burst | 80/162 | 76/162 | 0/162 † / 0/162 † | 0/162 † / 0/162 † |

Only eight of the 360 sender attack/arm/version/schedule cells have a positive all-attempt numerator, all D-only addition cases: .05 sustained/burst at tau=1; .2 sustained/burst memoryless, tau=1 and tau=.25. Tau=2 is unavailable. This is a complete-grid observation, not a universal attack ranking. [F023]

Sustained .2 addition D memoryless: C0 0/99, C1 99/99, C2 100/100, C3 0/101 =199/399 micro; equal-weight macro=.5. Clean D memoryless: C0 0/250, C1 29/249, C2 0/250, C3 0/250 =29/999 micro. All eight source score streams were freshly hashed against the seal and these counts independently rebuilt with compact attempt joins. [F022,F024,F047; saved_record_checks.json]

## Clean and benign controls, all sensor streams

The table gives clean eligible alarm counts, with `0/0` meaning **undefined**, never zero FPR. Sensor rows are not independent principals; top/dome share RSU. [F028,F035,F050]

| Sensor | D memoryless | D EWMA | G memoryless | G EWMA | max memoryless | max EWMA |
|---|---:|---:|---:|---:|---:|---:|
| 003 | 29/999 | 39/877 | 0/0 | 0/0 | 0/0 | 0/0 |
| 004 | 141/999 | 339/877 | 36/270 | 19/24 | 64/270 | 24/24 |
| laser | 0/999 | 212/877 | 4/149 | 46/63 | 15/149 | 0/63 |
| top | 19/1000 | 48/880 | 45/360 | 98/132 | 0/360 | 0/132 |
| dome | 10/999 | 59/876 | 0/0 | 0/0 | 0/0 | 0/0 |

All benign stress values/schedules and all sensors/versions are preserved in [control rates](evidence/r05_all_sensor_control_rates.csv). For 003 D memoryless, coordinate noise yields 155/999 eligible alarms under sustained stress at both sigma values, and 80/999 (.02 m) or 81/999 (.1 m) under bursts. Every adapter-translation, yaw, clock-skew and downsampling control has 29/999, equal to its clean whole-episode alarm count. These denominators span **the whole episode**, not just stress windows; equality cannot prove the stressed interval is harmless. D uses native XY and ignores pose perturbation; its unchanged response is not alignment robustness. [F050; exact grouped filters in results_summary.csv]

Honest-companion invariance passes in all 248 saved integrity rows. It is expected from independent per-stream factors, not evidence that suppressing sender features would preserve useful unique viewpoints. Clean companions alarm substantially (for example 004 D memoryless 141/999, EWMA 339/877). Repeated unchanged companion traces across attacks must not be counted as fresh clean data. [F028,F050]

## Paired effects, delay and recovery

`T_R05_paired_effects.csv` reports known-pair mean attacked-minus-clean A,C,score over scheduled events, counting unknown pairs. It contains no raw D/G paired-effect field despite broader prose in the plan. For 003 D memoryless C, random removal has positive means ranging +.005900439 to +.460389828 across 24 segment/severity/schedule cells; localized removal and constrained rearrangement are exactly zero in all 24 each. Displacement ranges −.905834598 to +.021989941; addition −.994099561 to zero. A harmful edit need not lower conformity. These are per-cell means, not pooled IID effects. [F027; r05_sender_paired_effects.csv]

The 2,160 interval-arm-version outcome rows have 21 detected, 519 right-censored no detection and 1,620 no eligible alarm. Of 21 in-window alarm rows, 20 interval recoveries are recorded and one is right-censored; other 2,139 interval recovery fields are not applicable. Counts multiply dependent versions and burst intervals. `final_recovery` is the separate after-last-offset field; its repeated occurrence on burst interval rows must be deduplicated by segment/episode/arm/version before episode analysis. Full status/value fields are preserved. [F029]

Metric code uses scheduled attempted events in all-attempt denominators, but counts only alarms with reader-valid, nonzero realized change and no injection failure. Eligible recall excludes unknown alarms; realized recall conditions on realized change but retains possible unknown scores. Empty denominators remain null/status. Delay excludes a preexisting alarm; the implementation flags an entire interval preexisting if its last pre-onset event is alarmed, rather than searching for later re-onsets. Recovery needs two seconds of continuous eligible quiet, no reset or >.5 s gap; reported value is **confirmation time**, not the start of that quiet run. [F029; metrics.event_metrics/episode_metrics; statistics.final_recovery]

## Reporting discrepancies and claim limits

The CSVs reconcile arithmetically, but that is not a fresh raw-data replay. `NO_POWER` has the overbroad meaning above; prose event-recall definitions sometimes omit the actual realized-change condition; the complete-common-support intersection includes an uncalibratable tau=2; paired tables omit raw factor effects; old status documents are stale. No files were “repaired” to hide these discrepancies.

Detecting a scheduled perturbation differs from identifying incorrect objects, harmful features, malicious intent or an improvement in fusion. There is no GT object detection evaluation to decide whether the observed perturbation damaged a task. No geometry-family-wide impossibility or new-method validation follows. [F037,F043]
