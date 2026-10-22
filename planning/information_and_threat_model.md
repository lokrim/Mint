# Information, trust boundary, threat model and deployment contract

Checkpoint 1, 2026-10-22. Notation is a typed contract, not a chosen formula. Items marked **[P]** are provisional assumptions awaiting a decision. Items marked **[V]** are verified in a source, cited inline. Items marked **[X]** are derived from code read in this session.

## 1. Representations: keep them apart

| Level | What it is | Example in our stack | Who can forge it | Role in MINT |
|---|---|---|---|---|
| Raw points | Per-beam returns with an implicit origin; organized grids also carry no-return slots | Mixed Signals ASCII PCD, W×H beam grid [V: findings 02 §4; pilot P1] | The owning agent; a physical spoofer | Receiver's **own** scan only, as trusted evidence (setting B). Never the senders' clouds at inference. |
| Engineered geometric statistics | Counts, densities, free-space ratios, occupancy polygons | CARLO f_B/g_B, CAD occupancy maps, old D/G | Whoever computes them | Receiver-computed only. A sender-supplied version is setting C. |
| Learned intermediate features | Encoder/backbone tensors in a BEV grid | PointPillars scatter (64 ch) and AttBEVBackbone stages (64/128/256 ch at strides 2/4/8) [X: Mixed Signals fork `msig_pillar_attnfuse.yaml`, `att_bev_backbone.py`] | The sender, fully | **The object whose reliability is estimated.** |
| Object queries/proposals | Decoded anchors/boxes before or after NMS | AttFuse head on fused or single-source features | Computed by the receiver from received tensors | Allowed receiver-side derived evidence **[P, decision Q3]** |
| Final detections | Post-NMS boxes | Late-fusion messages | The sender, fully, if sent | Not exchanged in MINT (a different fusion setting). Receiver's final boxes are the evaluated output. |

We do **not** switch to late fusion to make verification easier. Receiver-side decoding of a received tensor is not the same as receiving boxes. The sender never asserted those boxes, and the receiver can evaluate counterfactuals.

## 2. Targets: what each quantity would measure

| Target | Definition | Role |
|---|---|---|
| Corruption presence | Was the message altered relative to the clean counterpart? | Evaluator diagnostic. Not the estimand: harmless edits exist, and benign faults are harmful without alteration. |
| Geometric consistency | Agreement between a contribution and receiver-observed geometry | **Evidence channel**, not the target |
| Object correctness | A decoded hypothesis matches a GT box (IoU rule) | Evaluator diagnostic and part of the label bridge |
| Marginal task utility / harm | Change in GT-evaluated local detection error from including vs excluding `c[i,t,u]` | **Primary target** (§5) |
| Model uncertainty | Epistemic or aleatoric uncertainty of the detector | Possible evidence channel. Not the target. |
| Agent honesty / intent | Is the sender malicious? | **Out of scope.** Never inferred from inconsistency. |

## 3. End-to-end information flow and boundaries

```
OFFLINE (training/caching; GT allowed on its designated splits)
  raw scans ─► [train/fit detector if no checkpoint] ─► frozen encoder E, fusion F, head H
  clean + train-family attacked scenes ─► counterfactual labels D (GT) ─► fit/calibrate reliability R
                                                     (calibration split separate from fit split)
ONLINE, per sender i (UNTRUSTED principal)
  sensor_i ─► points_i ─► E ─► z[i,t] (sender frame, multi-scale) ─► (quantize/compress?) ─► channel
                                  metadata m[i,t] = (claimed pose, claimed stamp)  ─────────► channel
ONLINE, receiver 0 (TRUSTED computing base = receiver hardware + own sensors + frozen models)
  channel ─► decode ─► warp z[i,t] into receiver grid using m[i,t] ─► ẑ[i,t]
  own sensors ─► points_0 (incl. no-return slots) ─► E ─► z[0,t]
            └──────────────► receiver evidence e[t] (range image, visibility, own detections)
  history h[<t] (receiver-held state; may contain previously accepted attacked data)
  ┌──────────────────── MINT reliability module (new) ─────────────────────┐
  │ inputs: ẑ[·,t], z[0,t], e[t], m[·,t], h[<t]; derived single-source and  │
  │ fused decodes                                                            │
  │ outputs: r[i,t,u] = (status, value) per sender×tile; updated h[≤t]       │
  └──────────────────────────────────────────────────────────────────────────┘
  ─► reliability-aware fusion F_r (per-pixel attention with log r prior, or gate) ─► H ─► boxes
EVALUATOR ONLY (separate process / store; never readable by inference)
  GT boxes, visibility-by-agent, attack schedules, masks, clean counterparts, attacker logs
  ─► D labels, task metrics, reliability metrics, realization checks
```

- **Inference trust boundary.** The receiver trusts only its own hardware, sensors, clock and frozen models. Everything arriving over the channel is untrusted: features, poses, timestamps, any side evidence. Authentication identifies the source. It does not make the claims true.
- **Co-located trusted sensors.** In Mixed Signals the receiver is the RSU (`top`). The `dome` LiDAR is the same principal [V: findings 03 §2]. **[P]** We treat `dome` as receiver-owned evidence, not as a peer.
- **Evaluation boundary.** The following are evaluator inputs only:
  - GT;
  - GT-derived visibility (ACFR `gt_visibility` is a points-in-box count [V: Mixed Signals fork `msig_base_dataset.py`]);
  - attack schedules and masks;
  - clean counterparts.
- **Process separation.** Inference runs in a separate process with read access only to an allow-listed input store. This is enforced at the OS level (a separate directory mount or container), not by monkeypatching `open`. Lesson SC-05 is in [findings](findings/06_requirements_for_the_new_study.md).

## 4. Notation and typed contract

| Symbol | Type / shape | Meaning |
|---|---|---|
| `i ∈ {0..N}` | int | Agent. `0` = receiver. In Mixed Signals: 0 = `top`, receiver-owned `dome`, senders `003`, `004`, `laser`. |
| `t` | int64 ns | Receiver fusion time. Each message has a claimed source stamp `s[i,t] ≤ t`. |
| `z_k[i,t]` | float `[C_k, H_k, W_k]` | Sender `i`'s feature at fusion scale `k`, after warping into the receiver grid. AttFuse/Mixed Signals: `C=(64,128,256)`, grid 512² at 0.2 m pillars, scales at strides 2/4/8, so 256²/128²/64² at 0.4/0.8/1.6 m [X: yaml + backbone] |
| `u` | tile id | Receiver-frame BEV tile. **[P]** 6.4 m × 6.4 m = 4×4 cells at the coarsest scale, 16×16 at 0.4 m. This gives 16×16 = 256 tiles over ±51.2 m. Must align to stride 8. |
| `c[i,t,u]` | tuple of tensor slices | All of sender `i`'s fusion-scale vectors whose pixel centres lie in `u` |
| `e[t]` | struct | Receiver evidence: own range images (organized grids + no-return mask), own features, own decodes, visibility polygons |
| `h[<t]` | struct | Receiver-held causal state per (sender, tile): discounted evidence counts, last-update time, attack-agnostic |
| `X[t]` | — | `(ẑ[·,t], m[·,t], e[t], h[<t])`. The only inputs to `R`. |
| `r[i,t,u]` | `(status: enum, value: float32 ∈ [0,1] or NaN, aux)` | MINT output. `aux` holds instantaneous vs temporal parts and evidence counts for audit. |
| `D[i,t,u]` | int or float | Evaluator label (§5). Never an input. |

Rules:
- A value in [0,1] is called a *probability* only after held-out calibration of the event `{D ≤ m}`. Otherwise it is a *score*.
- `UNKNOWN_*` statuses never default silently to 0 or 1. The fusion policy for unknowns is a declared parameter.
- Changing only the sender identifier must not change `r` unless the declared state `h` is keyed on it. This is tested by the ID-permutation test in the [evaluation protocol](evaluation_protocol.md).

## 5. Observable target and the evaluation bridge

Feature tensors have no "correct feature" label. We use a **controlled counterfactual on the downstream output**, computed by the evaluator with GT.

### 5.1 Definition (primary)

For sender `i`, time `t` and tile `u`:
1. Let `Y⁺` be the receiver's post-NMS detections with all contributions fused.
2. Let `Y⁻(i,u)` be the same with `c[i,t,u]` removed from fusion. Removal means sender `i` is excluded from the attention set at pixels in `u` at all scales, so the softmax renormalizes over the remaining agents.
3. Let `E(Y; u)` be the local error of `Y` against GT boxes whose BEV centres lie in `u`, plus predicted boxes whose centres lie in `u`:
   `E = w_FP·#FP + w_FN·#FN + w_loc·Σ_TP (1 − IoU)`.
   - Matching is class-wise Hungarian on BEV rotated IoU. The paper reports AP at {0.5, 0.7} for vehicle and bike and {0.3, 0.5} for pedestrian [V: paper §4.2, Table 3]. **[P]** We use the lower threshold of each pair (vehicle and bike 0.5, pedestrian 0.3) for the label and report the stricter one as a sensitivity check.
   - **[P]** Weights default to `w_FP = w_FN = 1`, `w_loc = 0.5`.
4. Then `D[i,t,u] = E(Y⁺;u) − E(Y⁻(i,u);u)`, and:
   - `HARMFUL` if `D ≥ m`;
   - `USEFUL` if `D ≤ −m`;
   - `NEUTRAL` otherwise.
   **[P]** `m = 0.5`, so a full extra FP or FN counts and small localization changes are neutral.

### 5.2 Why this is tractable for pixel-local fusion [X, to verify as V-03]

- In the Mixed Signals AttFuse fork, each backbone stage runs on per-agent un-fused features.
- `AttFusion` is a per-pixel softmax over agents.
- The fused map then goes only through stride-equal `ConvTranspose2d` (kernel = stride, so no overlap) and 1×1 heads.

So the head output at a pixel depends only on that pixel's (and its parent coarse pixels') fused vectors. Removing sender `i` at a tile changes outputs only inside that tile, except through box decoding and NMS of boxes that straddle tile borders. Two forward passes per sender (with/without `i` everywhere) and per-tile mixing give `Y⁻(i,u)` for all tiles exactly, before NMS. This **does not hold** for Where2comm, V2X-ViT, CoBEVT or other fusion with spatial mixing after fusion. That is a reason to fix AttFuse as the primary model.

### 5.3 Limits of the bridge (must be reported, not hidden)

- **Not feature correctness.** A useful decoded object does not certify every latent channel. `D` measures task effect through this head.
- **Proposal and NMS dependence.** Effects can cross tile borders via boxes larger than a tile (buses, trucks) and NMS suppression. We use a centre-in-tile rule and report a cross-tile-effect rate.
- **Missed objects.** If `Y⁺` and `Y⁻` both miss a GT object, `D = 0` (neutral). Usefulness can only be measured where the detector can respond.
- **Unmatched and empty regions.** A tile with no GT and no predictions in either variant is `NEUTRAL_EMPTY`. It is excluded from discrimination metrics and counted separately.
- **Unlabelled is not empty.**
  - Mixed Signals labels require more than 5 aggregated points and lie within ±51.2 m [V: HF card].
  - Labels are hand-made at 1 Hz keyframes and interpolated in between [V: paper §3.3].
  - Mitigations:
    - **[P]** Primary metrics are computed on keyframes only, with interpolated frames as a secondary analysis.
    - Predictions in regions that no agent observes (evaluator visibility) count as FP only if inside the label crop.
    - Report sensitivity to excluding "unlabelled-but-observed" clusters (see R-06).
- **Receptive-field ambiguity on the input side.** `c[i,t,u]` depends on sender points outside `u`. The unit is the *transmitted* contribution, not the source points.
- **Cost.** Exact labels need 2 forward passes of fusion+head per sender per frame, plus matching. For a 3-sender frame that is about 7 passes of the post-backbone part. Cheap relative to training (estimate in the [budget](compute_memory_and_communication_budget.md)).

### 5.4 Secondary bridges (diagnostics)

- **Anchor-loss change.** The detector's own focal and regression loss on anchors in `u`, with/without `c`.
- **Object-level correctness of sender-only decodes.** Does a box decoded from `ẑ[i,t]` alone match GT?
- **Local occupancy error.** Only where receiver rays give observed free/occupied cells. Never for unobserved cells.

## 6. Information settings: which inputs the receiver may use

| Setting | Inputs to `R` | Ray evidence? | Spoofability of evidence | Status |
|---|---|---|---|---|
| A: feature-only | `ẑ`, `m`, own features `z[0]`, own decodes, `h` | none | Senders control their own features. Peers may collude. | Must work: the baseline information model. |
| B: + receiver's own raw scan (`top`+`dome` in Mixed Signals) | A + `e[t]` range images | Yes, but **only along receiver lines of sight** | Not spoofable by senders. A physical spoofer at the receiver is out of scope. | **[P] primary**, pending decision Q3 |
| C: + sender-supplied evidence (CAD-style occupancy, ~10 KB/frame [V: CAD §6.4.3]) | B + claimed occupancy | Sender-claimed rays | Fully forgeable consistently with its features; useful only via cross-peer conflict | Optional ablation only, budgeted as extra communication |

We do **not** give the receiver the senders' clean raw clouds. OpenCOOD's `proj_first=True` path (points projected into the ego frame before encoding [X: `msig_intermediate_fusion_dataset.py`]) is a simulation shortcut. It assumes the sender encodes in the receiver frame. **[P]** Our feature path is: the sender encodes in its own frame, and the receiver warps features with the claimed pose. If a released checkpoint only works with `proj_first=True`, we record that as a protocol deviation and test its effect (V-02).

## 7. Threat model

### 7.1 Principals

- Receiver 0 (trusted).
- Senders 1..N (each may be honest, faulty or compromised).
- A physical-world adversary (only for the benign-but-adversarial TrustFlip-style case, which is out of the core scope but listed).

### 7.2 Attacker capability, in separate threat classes, reported separately

| Class | Control | Knowledge | Constraints | Forges side evidence? |
|---|---|---|---|---|
| T1 raw-cloud fabrication before encoding (insider) | Own sensor stream | Own scan, the shared model (white-box, as in CAD/LUCIA/PoseGuard [V]), previous messages; not same-frame data from others [V: CAD §3.3] | Sensor geometry (beam grid), per-frame time budget | Can send consistent claimed occupancy in setting C |
| T2 feature-message manipulation (insider) | Own transmitted tensor | White-box encoder, fusion and head; optionally white-box MINT | Norm bound or spatial mask; values within clean ranges [V: CAD feature clipping] | Same |
| T3 metadata spoofing | Claimed pose and stamp | — | Plausible kinematics | — |
| T4 replay/stale | Resend old tensors | — | — | — |
| T5 collusion | k ≥ 2 senders coordinate | Shared | — | Yes, mutually |
| T6 adaptive against MINT | Any of T1–T5 plus knowledge of `R` | White-box `R`, or gray-box (architecture without calibration data) | As above | As above |

- **Never assumed:** compromise of the receiver, its sensors or clock; breaking cryptography; physical laser spoofing claims for digital edits.
- **Temporal knowledge.** The attacker sees previously broadcast messages and its own stream. It does not see same-frame receiver data. It knows the receiver's position (static RSU).

### 7.3 Benign faults (not attacks, often harmful)

- Pose/heading error. Mixed Signals reports at most 15 cm and 0.4° [V: paper §3.2.1].
- Skew up to 50 ms by construction [V: paper §3.2.1].
- Asynchronous delay.
- Sparse far returns, occlusion, unique views.
- Moving objects.
- Heterogeneous sensors: EVs tilted 15° with zero intensity [V: paper §3.1, Fig. A2].
- Quantization and compression.
- Dropped messages.

## 8. Identifiability: when two worlds give identical allowed inputs

- **W1.** Honest sender `i` reports a real pedestrian in tile `u`, which lies in the receiver's ray shadow behind a bus and outside all other senders' coverage.
- **W2.** Malicious `i` fabricates a pedestrian at the same place with the same feature statistics. A white-box T2 attacker can approximate the honest encoder's output for a plausible object, as the CAD/PoseGuard initializations do.

The receiver's rays end on the bus in both worlds. No peer covers `u`. `X[t]` can have the same distribution in W1 and W2, while `D` is negative in W1 and positive in W2.

**No function of `X` can separate them.** The only defensible output is `UNKNOWN_NO_EVIDENCE`. The fusion policy for unknowns then sets a fixed trade-off between losing honest unique views and admitting fabrications. Consequences:
- The headline metrics are always reported per evidence-coverage stratum.
- An abstention-heavy method is never scored as robust by hiding unknowns. All-attempt coverage is reported (see [evaluation protocol](evaluation_protocol.md) §6).
- GCP's blind-area attack [V: GCP §III-C] and the PB attack [V: GLST abstract] are concrete instances of exploiting this region.

## 9. Deployment placement

| Profile | Where `R` runs | Example class (not measured) | Plausible? |
|---|---|---|---|
| P-RSU | Roadside edge computer that already runs fusion | Jetson AGX Orin–class or small x86+GPU | **[P] primary for Mixed Signals** (receiver = RSU) |
| P-ECU | Vehicle central compute that runs fusion | Orin / automotive SoC | Primary if OPV2V or V2V4Real is chosen (receiver = ego car) |
| P-SENSOR | Sensor microcontroller or sensor-adjacent embedded | Cortex-M/A-class, < 1 W | **Not plausible** for feature-level reliability: no fusion features exist there. At most per-beam summary statistics. No claim will be made. |

- Devices are heterogeneous: senders may have weaker compute than the receiver. MINT adds nothing to sender compute in setting A/B.
- Budgets, the separation of incremental from end-to-end cost, and the benchmark plan are in [compute_memory_and_communication_budget.md](compute_memory_and_communication_budget.md).
- **The single hardware decision needed** is listed as Q1/Q2 in [risks_and_open_questions.md](risks_and_open_questions.md).
