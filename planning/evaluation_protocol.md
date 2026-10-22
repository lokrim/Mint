# Evaluation protocol (to be frozen before any block-E / test exposure)

Checkpoint 1, 2026-10-22. Draft preregistration.

Every **[A]** must be fixed by the end of Stage 4 (development) and hashed into `protocol_freeze.json` before Stage 6. After freezing, changes go in an amendment log with a reason and a statement of whether test outcomes were seen.

## 1. Populations and independence units

| Dataset | Broadest meaningful independence unit | What a "test" means here |
|---|---|---|
| Mixed Signals (MS) | **None truly independent.** One ~35-minute session at one site (pilot P3). Best available: a contiguous time block. | Held-out *time block* of the same session. Claims say "held-out time block", never "unseen sessions". |
| OPV2V (OP) | Scenario (and town); Culver City as a domain-shift set | Held-out scenarios not used to train the detector (the checkpoint's test split) |
| V2V4Real (VR) | Scenario (drive segment); days if recoverable | Official test scenarios |

All agents, all nearby frames, all clean/attacked/benign variants and all cached features of a unit share the unit's role.

## 2. Splits and roles

### 2.1 Mixed Signals [A]
See [feasibility](dataset_and_feature_feasibility.md) §5:
- **T** (train/fit): mini_1–3, 6, 7, 8, 10–16;
- buffer mini_19 (unused);
- **C** (calibration and θ): mini_20, 22–24;
- buffer mini_25 (unused);
- **E** (evaluation): mini_26, 28–35, 37.

Rules:
- mini_7 and mini_10–13 are exposed (Valid Point). They are allowed only in T.
- HF val (mini_9/18/27/36) has no labels. It may be used for *unlabelled* clean-variation diagnostics only. It must not be used for any tuning that sees task outcomes.
- **Alternative to consider at freeze:** a reverse split (E early, T late) as a robustness re-run, labelled as a second development estimate, not a second test.

### 2.2 OPV2V
- Detector checkpoint trained on `train`.
- MINT T = `validate` scenarios (half), C = the other half of `validate`, E = `test` + Culver City (reported separately).
- **⚠** Scenario lists must be read from the data (L-10).

### 2.3 V2V4Real
- The released checkpoint was trained on the V2V4Real `train` scenarios, so those cannot serve as MINT fit or calibration data without overlap with the detector's training data.
- **[A]** If an official validation split exists, use it for T/C and `test` for E.
- Otherwise, use VR only to *evaluate a frozen, OP-fitted MINT*. That is cross-dataset transfer and is labelled as such.

### 2.4 Exposure ledger
- [exposure_ledger.csv](exposure_ledger.csv) records, per unit: role, first exposure date, what was seen (metadata / clean outputs / attacked outputs / metrics), by which stage.
- Block E outcomes are opened only by the Stage-6 runner after the seal.

## 3. Labels, eligibility, strata

- **Unit label** `D[i,t,u]` and classes HARMFUL / NEUTRAL / USEFUL / NO_EFFECT / NEUTRAL_EMPTY, as in the [contract](information_and_threat_model.md) §5. Computed by the evaluator process only.
- **Eligibility for discrimination metrics:** status KNOWN and class ∈ {HARMFUL, NEUTRAL, USEFUL}.
  - NO_EFFECT is counted but excluded (D = 0 by construction).
  - UNKNOWN units are excluded from discrimination metrics but included in the all-attempt and coverage metrics (§6).
- **Strata (evaluator only):**
  - **Visibility:** RECEIVER_SEES / SENDER_ONLY / MULTI_SENDER_ONLY / NOBODY / UNLABELLED_REGION.
  - **Class.**
  - **Range bin.**
  - **Speed bin:** static < 0.5 m/s, slow < 3, fast ≥ 3.
  - **Effect type.**
  - **Condition:** clean, benign-stress family, attack family and severity.
  - **Keyframe vs interpolated** (MS).
- **UNIQUE stratum (for H3):** USEFUL units with visibility SENDER_ONLY.

## 4. Metrics

### 4.1 Reliability behaviour (eligible units; per E-unit, then aggregated)

- **Discrimination.** AUROC and AUPRC for HARMFUL vs not, overall and per stratum.
- **Paired change.** For each attacked unit with a clean counterpart, compute `Δr = r_attacked − r_clean`. Report the distribution, and the fraction with `Δr < 0` among realized harmful attacks and among harmless edits. **No expectation that every attack lowers r.**
- **Severity response.** Median `r` and HARMFUL rate per attack severity, with group-level intervals.
- **Calibration (calibrated variants only).**
  - Reliability diagram (10 equal-mass bins), ECE, Brier score, on block E.
  - The same on block C (in-sample check).
  - M3 is reported as a score: no ECE.
- **Selective prediction.** Risk–coverage curves, where risk = HARMFUL rate among accepted units and coverage = accepted / eligible. Also AURC.
- **Unknown rates.** Fraction UNKNOWN among effectful units, overall and per stratum. This is crucial in SENDER_ONLY.
- **Temporal** (where schedules have onsets and offsets): time to first r < θ after onset; time to recovery after offset (2 s of KNOWN r ≥ θ); censored if not reached within the window. Per burst interval, never across bursts (the old lesson MT-13). `r_inst` and `r_temp` are reported separately.

### 4.2 Task quality against GT (frame-level, aggregated per E-unit)

- **AP.**
  - MS: Vehicle/Bike AP@{0.5, 0.7}, Pedestrian AP@{0.3, 0.5}, BEV rotated IoU, ±51.2 m, TOP frame, keyframes primary [V paper].
  - OP/VR: the dataset's AP@{0.5, 0.7} vehicle.
- **Error counts.** FP, FN and localization error (mean 1 − IoU of TPs), per stratum.
- **Clean retention.** `AP_clean(method) / AP_clean(AttFuse)`.
- **Attacked AP** per family and severity.
- **Unique-view false rejection (H3).** Fraction of UNIQUE units gated or down-weighted, and the resulting FN increase.
- **Compared systems** (identical frozen detector, identical inputs per setting):
  1. ego/receiver-only (no collaboration);
  2. AttFuse (M0);
  3. M1 confidence gate;
  4. B-LUCIA;
  5. B-CAD-local;
  6. B-PoseGuard-tile and B-MADE-tile if budget allows;
  7. M3 gate;
  8. **MINT-v0 (M4)**;
  9. M5 (v1) if built;
  10. **Oracle (evaluator-only diagnostic):** gate exactly the HARMFUL units. An upper bound, never a method.
- **Fairness.** All methods get the same allowed inputs per setting. B-LUCIA is setting A. Every method using receiver rays is marked "setting B". Compute and communication are reported next to accuracy.

### 4.3 System cost

See [compute_memory_and_communication_budget.md](compute_memory_and_communication_budget.md). Report:
- p50/p95 latency of each stage: I/O, decode/warp, backbone, fusion+head, counterfactual pass, ray evidence, combiner, gating;
- peak RSS including children;
- model and state bytes;
- extra communication bytes;
- device, precision, threads, warm-up, batch, power mode.

## 5. Baselines: fixed details [A]

- **B-LUCIA.** Average-pool factor 8, L2-normalise, eq. 10–12 as published. No retraining.
- **B-CAD-local.** Receiver free polygon from the first non-ground hit per 0.5° azimuth sector, up to 50 m [V CAD default], unknown beyond. σ_spoof and σ_remove tuned on block C.
- **M1.** Threshold tuned on block C at the same clean false-gating rate as MINT.
- **All tunable baselines get the same block-C tuning budget** (grid ≤ 20 settings).

## 6. Denominators, abstention, failures (defined in advance)

- **Attempt ledger** for every attack event: intended edit, serialization, reload, realized feature/point change, realized task harm. Failed injections, zero-realized-change and zero-harm events **stay in all-attempt denominators**.
- **Two rates, always side by side.**
  - **FPR on usable decisions** = gated clean non-harmful KNOWN units / clean non-harmful KNOWN units.
  - **All-attempt coverage** = KNOWN units / all effectful units.
- **Harm admitted.** Harmful units not gated, split by status: KNOWN-but-accepted vs UNKNOWN-kept. This exposes abstention-heavy behaviour.
- **Empty classes or denominators** are reported as `UNDEFINED (0/0)`, never 0%.
- **Pre-existing state.** Temporal metrics count only gates that begin after onset. Gates already active at onset are reported separately.
- **Censoring** is explicit.

## 7. Benign controls and integrity tests

- **Benign stresses.** Full list in the [attack/benign protocol](attack_and_benign_protocol.md). Each gets the same metrics as attacks. A method that gates benign sparse or unique views is penalized through H2/H3 metrics.
- **Clean natural variation** across E units (per-unit results table).
- **Blast radius.** When only tile u of sender i is attacked, report the change in r for sender i's *other* tiles. Expectation: none beyond temporal state. TrustFlip-motivated.
- **ID permutation.** Shuffling sender IDs per frame (with state reset) leaves instantaneous outputs bit-identical.
- **Leak tests.** The inference process run with evaluator files changed or withheld gives identical outputs. A deliberate leak through builtin `open` is caught by the OS-level boundary.
- **Prefix invariance.** Perturbing frames after t does not change outputs at or before t.

## 8. Ablations (bounded; preregistered)

| ID | Ablation | Question |
|---|---|---|
| AB-1 | M3 (ratio) vs M4 (beta-binomial + calibration) | Does the statistical model add value over the deterministic ratio? |
| AB-2 | Support only / traversal only / both | The two halves of the ray idea |
| AB-3 | NR slots as unknown (default) vs NR as traversal (unsafe variant) | Quantifies the free-space fallacy |
| AB-4 | Class/range-conditional vs pooled models | Visibility handling |
| AB-5 | v1: + feature residuals; + attention share; + peers; + temporal | Complementary channels; double counting |
| AB-6 | Unknown policy: keep / prior / drop / temporal | H3 vs H4 trade-off |
| AB-7 | Tile size 3.2 m / 6.4 m / 12.8 m | Resolution |
| AB-8 | fp32 vs fp16 vs int8 features | Precision and quantization stress |
| AB-9 | Hard gate vs soft weight | Fusion integration |

No full factorial: each ablation varies one factor from MINT-v0.

## 9. Freezing and sealing

1. End of Stage 4. Freeze:
   - code commit, configs, fitted models, calibrator, θ;
   - attack and benign schedules, seeds, budgets;
   - intended and achieved severity definitions;
   - metric code.
   Hash everything into `protocol_freeze.json`.
2. Stage 6 runner: compute predictions on block E, then seal them (hash manifest) **before** the evaluator computes metrics.
3. Any post-seal change produces a new run labelled exploratory.

## 10. Statistical uncertainty

- **Per-unit tables first** (each E segment or scenario), then an aggregate.
- **Aggregate:**
  - macro mean over units (primary), and micro (pooled) for reference;
  - intervals by cluster bootstrap over E units (B = 2,000): OP/VR at scenario level; MS at segment level, *with the caveat that segments are one session*.
  - With fewer than 10 units, or for MS, intervals are labelled "within-session, descriptive". No population-level CI is claimed.
- **Paired comparisons** (method vs baseline) use the per-unit paired difference, with a sign test as a robustness check.
- **Multiplicity.** Hypotheses H1–H3 are primary, each tested at α = 0.05 with Holm correction across the three. Everything else is descriptive.

## 11. Decision rules

- **Engineering acceptance** (Stage gates; not science): reproduction, locality, leak tests, ledger reconciliation.
- **Scientific outcomes:**
  - H1 supported if the paired AUROC difference vs the best non-oracle baseline has its interval above 0 on E (OP primary; MS within-session).
  - H2 supported if clean retention ≥ 0.98 **[A]** and attacked-AP gain > 0 with the interval above 0.
  - H3 supported if UNIQUE false rejection ≤ corroborated false rejection + 5 pp **[A]**.
  - H4 is evaluated descriptively.
  - H5 is evaluated against the budget profile.
  - H6 is supported if AB-5/AB-2 show a positive paired AUROC gain in RECEIVER_SEES tiles.
- **Negative results** on any hypothesis are reported in the paper with the same prominence.
