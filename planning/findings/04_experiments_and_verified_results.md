# 04 — Experiments and verified results

Revision 2 (2026-10-22). All R05 numbers come from my own re-parse of the saved tables in `artifacts/20261012T134149Z-R05/`, produced by [evidence/r2/audit_r2.py](evidence/r2/audit_r2.py) (output [audit_r2_report.json](evidence/r2/audit_r2_report.json)). No replay, training, test or notebook was run. **Detecting a scheduled perturbation is not proof of object correctness, feature usefulness or malicious intent.** No result below measures any of those.

## 1. Earlier experiments (S01–S04, R01–R04): scope only

| Stage | What was executed | What it can support | Status |
|---|---|---|---|
| S01–S02 | Seeded toy geometry; hand-input residuals, counts, availability | Arithmetic and causality counterexamples | constructed_example |
| S03 | `ablations.clean_fixture_rows` generates "clean observations" by seed/frame arithmetic | Quantile/calibration bookkeeping only. Not calibration on real scenes. | constructed_example (SC-01) |
| S04 | 400 fixed tiles vs oracle boxes on 12 constructed cases. The old evidence audit reports attack alarms 3/7 vs 5/7 and benign alarms 2/5 each. Proposal/association states are annotations. | Count blind-spot illustration. No proposal/association rates. | constructed_example / reported_not_reverified (SC-02, SC-04) |
| R01 | mini_7: 250 selected clouds and 3 odometry CSVs; headers, timing, frames | Field feasibility | reported_not_reverified (fresh partial re-check: DA-02, DA-11) |
| R02 | Raw D/G on 250 mini_7 events: D 250/250 known; G 163/250 (82 search-bound, 5 no-history) | Raw pipeline works; G abstains often | reported_not_reverified |
| R03 | 1,250 clean mini_7 events plus one sustained middle-severity episode per family, one burst, noise and alignment controls; exploratory references; thresholds null | Engineering demonstration; no alarm power | reported_not_reverified |
| R04 | Protocol freeze, hash `80694538…039c` | Pre-registration of R05; no outcomes | reported_not_reverified |

## 2. R05 design (frozen)

- **Folds.** Test/calibration/reference = C0/C1/{C2,C3}, C1/C2/{C3,C0}, C2/C3/{C0,C1}, C3/C0/{C1,C2}. C0–C3 are mini_10–13.
- **Episodes.** Per segment: 30 attacks (5 families × 3 severities × sustained [5,15) s or bursts [5,7)+[10,12) s), 5 zero-severity identity controls, 1 clean replay and 26 benign stresses. That is 62 per segment and **248 in total** (EX-01).
- **Sender and edits.** The sender is always `003`. Point-only digital edits: no pose, time or metadata changes, and no intermediate features.
- **Arms.** D-only, G-only and max(D,G), each in four versions (memoryless; EWMA τ = 1, 0.25, 2 s), all separately calibrated.

| Family | Severities | Operation (code: `attacks/overlays.py`) |
|---|---|---|
| random_removal | 0.1, 0.3, 0.6 | remove ⌊fN⌋ random rows |
| localized_removal | 0.25, 0.5, 1 | remove fraction of rows in target cell (**always `r0:a0`**) |
| displacement | 0.2, 1, 3 m | +x shift of 25% random rows |
| rearrangement | 0.2, 1, 3 m | move 25% rows, ≤10 directions, must stay in original D cell |
| addition | 0.01, 0.05, 0.2 | ⌊fN⌋ uniform points in a 2 m cube at the target-cell centroid |

**Targets (DA-05).** All four folds froze target `r0:a0`, with centroids (1.76, 0.81, 1.24), (1.04, 0.42, 1.25), (1.33, 0.61, 1.20) and (1.04, 0.42, 1.25) m in the `003` native frame. The no-return placeholder slots at (0, 0, 1.63) dominate this cell ([02 §4](02_methodology_and_failure_analysis.md)). Localized removal therefore mostly removes placeholders, and addition places a dense blob roughly at the sensor or vehicle.

**Benign stresses** (×2 schedules): coordinate noise σ 0.02/0.1 m; adapter translation 0.05/0.2 m; yaw 0.2/1°; modeled pose-clock skew −50/−10/+10/+50 ms; raw downsampling 0.1/0.3/0.6.

**Population caveat (DA-13).** C0–C3 lie inside a single 208.6 s stretch of recording (gaps 43.7, 46.4, 18.8 s). They are four nearby clips, almost certainly from one session. Repeated interventions on a clip are paired and dependent; they are not new scenes. Folds share reference data.

## 3. Attempt flow and realized change (EX-01, EX-02)

- **Scheduled sender events.** 17,703 non-clean scheduled events: 8,415 attack, 7,293 benign, 1,995 identity. All were reader-valid, with 0 injection failures.
- **Attacks.** Each attack family has 1,683 scheduled events, all with nonzero realized change (from the evaluator `attempts.jsonl.gz` ledgers).
- **Rearrangement.** 64,852 of 110,297,088 intended row moves failed and were kept unchanged. The per-cell count change is 0 for all 1,683 events, as designed.
- **Benign stresses.** Translation, yaw and clock-skew stresses realize 0 changed rows by design: they act on poses only.
- **Sender events per segment.** 250, 249, 250, 250 (C0–C3).

## 4. Calibration and coverage come first (EX-03, EX-04, EX-05)

**References.** 800 reference contexts: 712 `SUPPORTED`, 40 `LOW_SUPPORT` (all G gap contexts g1/g2, every sensor and fold), 48 `ZERO_SCALE` (all far top/dome D cells).

**Calibration.** 240 cells (4 folds × 5 sensors × 3 arms × 4 versions):
- **156 `INSUFFICIENT_KNOWN`**: fewer than 200 known clean scores, so the threshold is null.
- **31 `NO_POWER`**, which splits into **21 with c = 1**, from saturated clipped clean scores, which cannot alarm; and **10 with constant scores and c = 0**, which can alarm on any positive score.
- **53 `AVAILABLE`.**

All 240 thresholds re-derive exactly from the saved calibration scores.

Sender `003` thresholds (test segment, version → status/c):

| Arm | C0 (cal C1) | C1 (cal C2) | C2 (cal C3) | C3 (cal C0) |
|---|---|---|---|---|
| D memoryless | c=1 (229/249 cal scores =1) | 0.2964 | 0.3853 | c=1 (121/250 =1) |
| D EWMA τ=1 | c=1 | 0.1293 | 0.1611 | 0.9996 (available) |
| D EWMA τ=0.25 | c=1 | 0.2803 | 0.2901 | c=1 |
| D EWMA τ=2 | null (n=189) | null | null | null |
| G-only, max(D,G), all versions | null (n ≤ 199 every fold) | null | null | null |

So "zero alarms" has two very different meanings. Rows marked ✗ below **could not alarm**. Zeros in alarm-capable segments **failed to alarm with a usable threshold**.

## 5. Complete sender-`003` attack grid, D-only

Each cell shows all-attempt alarms / scheduled attempts (all four segments), then the same count restricted to segments where an alarm was possible, with those segments in brackets. ✗ = no segment could alarm. **G-only and max(D,G): all 240 cells (30 attacks × 2 arms × 4 versions) are 0 alarms with no alarm-capable segment.** Source: [sender003_attack_grid_r2.csv](evidence/r2/sender003_attack_grid_r2.csv), which also holds per-segment eligible counts and thresholds.

| Family | Sev. | Schedule | memoryless | EWMA τ=1 | EWMA τ=0.25 | EWMA τ=2 |
|---|---:|---|---|---|---|---|
| random_removal | 0.1 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| random_removal | 0.1 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| random_removal | 0.3 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| random_removal | 0.3 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| random_removal | 0.6 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| random_removal | 0.6 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| localized_removal | 0.25 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| localized_removal | 0.25 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| localized_removal | 0.5 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| localized_removal | 0.5 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| localized_removal | 1 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| localized_removal | 1 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| displacement | 0.2 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| displacement | 0.2 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| displacement | 1 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| displacement | 1 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| displacement | 3 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| displacement | 3 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| rearrangement | 0.2 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| rearrangement | 0.2 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| rearrangement | 1 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| rearrangement | 1 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| rearrangement | 3 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| rearrangement | 3 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| addition | 0.01 | burst | 0/162 · cap 0/80 [C1C2] | 0/162 · cap 0/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| addition | 0.01 | sustained | 0/399 · cap 0/199 [C1C2] | 0/399 · cap 0/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| addition | 0.05 | burst | 0/162 · cap 0/80 [C1C2] | 4/162 · cap 4/121 [C1C2C3] | 0/162 · cap 0/80 [C1C2] | — (0/162) ✗ |
| addition | 0.05 | sustained | 0/399 · cap 0/199 [C1C2] | 10/399 · cap 10/300 [C1C2C3] | 0/399 · cap 0/199 [C1C2] | — (0/399) ✗ |
| addition | 0.2 | burst | 80/162 · cap 80/80 [C1C2] | 76/162 · cap 76/121 [C1C2C3] | 78/162 · cap 78/80 [C1C2] | — (0/162) ✗ |
| addition | 0.2 | sustained | 199/399 · cap 199/199 [C1C2] | 220/399 · cap 220/300 [C1C2C3] | 198/399 · cap 198/199 [C1C2] | — (0/399) ✗ |

**Summary of 360 sender cells (EX-06).**
- 270 could not alarm in any segment: all 240 G/max cells and the 30 τ=2 cells.
- 82 had at least one alarm-capable segment and still produced 0 alarms.
- 8 produced alarms, all of them D-only addition cells.

**Reading the 0.2 addition result (EX-07).** The all-attempt figure of 199/399 is really two different things:
- **100% in the segments where an alarm was possible:** C1 99/99, C2 100/100.
- **Structurally zero in C0 and C3,** where the threshold was 1.

The EWMA τ=1 cell reaches C3 (23/101) only because its C3 threshold, 0.9996, sits just below 1.

Given the target placement, this is a reaction to roughly 52,000 extra points in a 2 m cube about 1–2 m from the sensor. That raises the `r0:a0` count past u + b. It is not evidence about realistic fabricated objects.

**Reading the zeros.** The D zeros for removal and rearrangement are guaranteed by construction (MT-04): D cannot rise under removal and cannot change under within-cell moves. Displacement can only change D through cell crossings, and none crossed enough to alarm. These are not empirical findings about attack difficulty.

## 6. Clean and benign controls (EX-08, EX-09, EX-10)

Clean eligible alarms / eligible events, pooled over C0–C3. **0/0 = undefined**, not 0%. Rates use the whole 25 s episode. Full per-segment and per-version data: [control_rates_r2.csv](evidence/r2/control_rates_r2.csv).

| Sensor | D memoryless | D EWMA | G memoryless | G EWMA | max memoryless | max EWMA |
|---|---|---|---|---|---|---|
| 003 | 29/999 (C1 29/249; C0, C3 cannot alarm) | 39/877 (all C1) | 0/0 | 0/0 | 0/0 | 0/0 |
| 004 | 141/999 (all C1: 141/249) | 339/877 (C1 215/219, C3 124/220) | 36/270 | 19/24 | 64/270 | 24/24 |
| laser | 0/999 | 212/877 (C3 212/219) | 4/149 | 46/63 | 15/149 | 0/63 |
| top (RSU) | 19/1000 | 48/880 | 45/360 | 98/132 | 0/360 | 0/132 |
| dome (RSU) | 10/999 | 59/876 | 0/0 | 0/0 | 0/0 | 0/0 |

Clean false alarms cluster in particular test segments, for example `004` D EWMA: 98% of clean C1 events alarm. This is the same cross-segment shift seen in calibration (EX-05). The nominal 1% target is not achieved, and no IID rate exists. Among `003` D-memoryless alarm-capable segments (C1, C2), the clean rate is 29/499. `top` and `dome` are one RSU principal and are not independent evidence.

**`003` D-memoryless benign stresses (whole-episode denominators).**
- Coordinate noise: 155/999 sustained at both σ values; 80/999 and 81/999 for bursts.
- Every translation, yaw, clock-skew and downsampling stress: 29/999, the same as clean.
- That equality is structural. D uses native XY and ignores poses, and downsampling is removal, which D cannot see. It shows insensitivity, not robustness. All five identity controls also give 29/999.

## 7. Paired effects, delay and recovery (EX-11, EX-12)

**Paired effects.** `T_R05_paired_effects.csv` holds mean attacked − clean of A, C and score only; there are no raw D/G fields. For `003` D memoryless C, over 24 segment/severity/schedule cells per family:

| Family | Range of mean ΔC | Exactly-zero cells |
|---|---|---|
| random_removal | +0.0059 to +0.4604 | 0/24 |
| localized_removal | exactly 0 | 24/24 |
| rearrangement | exactly 0 | 24/24 |
| displacement | −0.9058 to +0.0220 | 0/24 |
| addition | −0.9941 to 0 | 7/24 |

A harmful edit can *raise* conformity.

**Interval outcomes.** 2,160 rows (sender × arm × version × interval):
- Delay: 21 `DETECTED`, 519 `RIGHT_CENSORED_NO_DETECTION`, 1,620 `NO_ELIGIBLE_ALARM`.
- Interval recovery: 20 recovered, 1 right-censored.
- Deduplicated per episode/arm/version: 14 final recoveries, 1 censored, 1,425 never alarmed.

All 21 detections are D-only addition cells in C1, C2 or C3. Most fire on the first scheduled event (delay ≤ 0.2 s); one C1 0.05 sustained EWMA detection takes 5.2 s and one C3 0.2 EWMA takes 7.8 s. Recovery is "confirmation time after 2 s of eligible quiet". Burst interval-0 values (up to 9.1 s) are inflated by the second burst (MT-13). Counts multiply dependent versions and intervals.

## 8. Integrity, reconciliation, and what is not evaluated

- **Companion invariance (EX-13).** 248/248 episodes pass the honest-companion and pre-onset prefix check. Per-stream scoring guarantees this; it is not evidence about unique-viewpoint fairness. Unchanged companion traces repeated across episodes are not new clean data.
- **Reconciliation (EX-15).** All 12,240 grouped rows reconcile with 48,960 segment metric rows: micro numerators and denominators match exactly, and each group has 4 segments.
- **Not evaluated (EX-14).** Object detection, AP, labels, feature usefulness, honest unique-view utility, fusion benefit, intent and physical attack realism. Nothing in R05 can support claims about these.

## 9. Discrepancies recorded, not repaired

- The `NO_POWER` label mixes "cannot alarm" (c = 1) with "constant, can alarm" (c = 0).
- Plan prose for "event recall" omits the realized-change condition used in code.
- The saved "common support" table intersects all arms and all versions including uncalibratable τ = 2, so it is uninformative.
- Paired tables omit raw factors.
- Interval recovery is confounded across bursts.
- The attack target and the D near ring are dominated by placeholders (DA-04/05).
- Revision 1 of this package presented the all-attempt rates without separating could-not-alarm from failed-to-alarm, and missed the placeholder issue (ST-05).
