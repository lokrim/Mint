# Methodology candidates: mathematics, counterexamples, identifiability, complexity

Checkpoint 1, 2026-10-22. These are candidates. Selection criteria use literature and clean-development feasibility only. Numeric defaults marked **[A]** are assumptions that need development justification. Contract and notation: [information_and_threat_model.md](information_and_threat_model.md).

## 0. A structural fact all candidates use: the *effect* of a contribution is observable

For pixel-local attentive fusion (AttFuse; see §5.2 of the contract), the receiver can compute without GT:
- `Y⁺`: post-NMS output with every contribution;
- `Y⁻(i)`: output with sender `i` masked out of the attention softmax at every pixel.

Masking reuses the already-computed attention logits. Only the deblock+head part reruns.

**Tile-wise effect.** Because fusion is pixel-local, the output in tile `u` with `c[i,t,u]` removed equals `Y⁻(i)` restricted to `u`, up to boxes straddling tile borders. Match `Y⁺|u` against `Y⁻(i)|u` class-wise (Hungarian, BEV IoU ≥ 0.1 **[A]**). The effect set is `ℰ[i,t,u] = {e}`, with each `e` one of:
- `ADD(b)`: box `b ∈ Y⁺` unmatched in `Y⁻`. The contribution *asserts an object*.
- `REMOVE(b)`: box `b ∈ Y⁻` unmatched in `Y⁺`. The contribution *asserts absence*.
- `SHIFT(b⁻→b⁺)`: matched, with centre displacement > 0.3 m **[A]**, or yaw change > 10° **[A]**, or a class change. The contribution *asserts a different pose or class*.
- `ℰ = ∅`: no material change at the operating threshold. Then `D = 0` by construction, and the unit is `NO_EFFECT`. It is not scored for discrimination, only counted.

**Why this matters.**
1. It makes the target concrete. Each effect is a *claim about the physical world* (object here / no object here / object posed here). The GT label `D` is harmful exactly when the claimed change makes local errors worse.
2. It limits work to effectful tiles. We expect a few per frame **[E]**, to be measured.
3. **Hard gating of tile `u` means outputting `Y⁻(i)` there.** That is exact, with no retraining.

**Honest labelling.** The verification step is *object-level verification of a feature contribution's counterfactual effect*. The decision acts on the *feature contribution* (tile-level fusion gate or weight), not on final boxes. It is not "feature-channel correctness".

**What it misses.**
- Harm below the operating threshold (score changes that do not cross it). These matter only for AP-at-all-thresholds; reported via AP with and without MINT.
- Second-order interactions between gated tiles. These are none for pixel-local fusion, except NMS across borders.

---

## M0. No reliability (reference)

`r ≡ (KNOWN, 1)`. This is plain AttFuse.

## M1. Detector-confidence baseline (not a reliability estimate)

`r[i,t,u] = max_{e∈ℰ} score(e)` for `ADD`/`SHIFT`, and `1` for `REMOVE`. Alternatively, the sender-only objectness in `u`, Where2comm-style.

- **Estimand.** None. It measures objectness. A white-box attacker can raise confidence (CAD's loss eq. 4 does exactly this).
- **Role.** Shows whether MINT beats "trust confident things".
- **Cost.** O(#effects).

## M2. Closest feasible prior-work baselines (same frozen detector, same inputs)

- **B-LUCIA.** Per-agent `T_i` (LUCIA eq. 10) in attention (eq. 11–12) [`wang2025lucia`].
- **B-PoseGuard-tile.** Crop L1 between agents' L2-normalised features in each effect box, flagged at the clean 95th percentile [`zhang2026poseguard`]. Mapped to tiles.
- **B-CAD-local.** The receiver's own free/occupied/unknown polygons from its own scan:
  - first non-ground hit per azimuth sector;
  - ε_spoof = ADD boxes overlapping receiver free space by more than σ;
  - ε_remove = receiver-occupied clusters left without a box.
  This is CAD's "local-only" lower bound [`zhang2024cad`].
- **B-MADE-tile.** Match-loss and residual-AE conformal p-values computed per tile, BH-combined [`zhao2024made`].

---

## M3. Deterministic receiver-ray support / traversal / occlusion counts (the ray idea, narrowed)

### Information setting

B: the receiver's own organized scans (TOP+DOME for Mixed Signals; the ego cloud for OPV2V/V2V4Real). Only receiver rays are used. **Senders never supply rays.**

### Variables (per effect box `b` and receiver sensor `k`)

- **Origin and directions.**
  - Origin `o_k` (m, receiver frame). Mixed Signals: published constants, corroborated by placeholder location [V/L].
  - Slot direction `d_k(s)`: a unit vector per beam slot `s = (row, col)`, from the fitted mount rotation plus per-row elevation and per-column azimuth tables (pilot P2) [L]. Validation V-06 is needed.
- **Measured range** `ρ_k(s)` (m), or `NR` for a no-return slot.
- **Core** `B°`. Box `b` shrunk by `κ = max(0.15 m, 15%)` per horizontal side **[A]**. Height `[z_g + h_g, z_top − 0.1 m]`, where `z_g` is the local ground height and `h_g = 0.3 m` **[A]**.
  - Ground: for the static RSU, from a receiver-owned ground map fitted on block-T clean data (trusted, offline).
  - Moving ego (OPV2V/V2V4Real): from a per-frame RANSAC ground fit.
- **Envelope** `B^+`. Box `b` dilated by `δ_motion = v̂·Δt + σ_pose`.
  - **[A]** `v̂ = 15 m/s` worst case, or a per-object speed estimate from the receiver's track.
  - `Δt` = |receiver scan time − sender claimed stamp| ≤ 50 ms by dataset construction [V].
  - `σ_pose = 0.15 m + 50 m·tan(0.4°) ≈ 0.5 m` at 50 m, using the Mixed Signals bounds [V].
- **Ray intersections.** `[a_s, b_s]` = entry/exit range of ray `s` with `B°` (slab test). `[a_s^+, b_s^+]` for `B^+`.

### Per-slot classification (only for slots whose ray intersects `B°`)

| Condition | Class | Meaning |
|---|---|---|
| `ρ < a_s^+ − τ` | `OCC` | Ray stopped before the envelope. No information about `b`. |
| `a_s^+ − τ ≤ ρ ≤ b_s^+ + τ` | `SUP` | Return inside the envelope: compatible with an object. |
| `ρ > b_s + τ` | `TRAV` | Ray passed through the **core** and returned beyond it: contradicts solid occupancy of the core. |
| `NR` | `UNK_NR` | No return. **Never** counted as `TRAV`, unless a validated no-return model exists (§M3 failure cases). |

- `τ = 0.05 m + 0.01·ρ` **[A]**: sensor noise plus range-proportional slack.
- Each ray is counted **once**, on its outgoing path. Return paths are not separate rays.

**Counts.** `n_S`, `n_T`, `n_O`, `n_NR`. Coverage `n_vis = n_S + n_T`.

### Score

- For a claim of **presence** (`ADD`, the `SHIFT` target `b⁺`): `s_pres = (n_S + 1)/(n_vis + 2)` (Laplace-smoothed support ratio).
- For a claim of **absence** (`REMOVE`): `s_abs = (n_T + 1)/(n_vis + 2)`.
- For `SHIFT`: `s_shift = s_pres(b⁺) − s_pres(b⁻)`, mapped to [0,1] by `(1 + s_shift)/2`. Positive means the receiver's rays favour the new pose.
- **Status.** `UNKNOWN_NO_EVIDENCE` if `n_vis < n_min = 5` **[A]**.
- **Tile value.** `r = min_e s_e` over effects. The tile is `KNOWN` only if every effect is `KNOWN` **[A]**; per-effect details go in `aux`.

### Why the evidence should track the target

An `ADD` is harmful iff the added box is not a real object (FP), or is a duplicate or mislocalized object.
- If a real object occupies the core and the receiver sees it, rays reaching the core mostly return inside the envelope.
- If the core is empty and visible, rays traverse it.

The receiver's rays are generated by the physical scene, independently of the sender's honesty. They are not forgeable by T1–T5 attackers (the receiver is trusted). This is the CARLO LPD physics [`sun2020carlo` eq. 6], applied *cross-agent*: the verifier's rays, not the claimant's.

### Properties that can actually be shown

- **(P1) Monotonicity.** `s_pres` is non-decreasing in `n_S` and non-increasing in `n_T`.
- **(P2) Sender-invariance of evidence.** Given the effect geometry, the counts depend only on receiver data. An attacker affects `r` only by choosing *where* effects occur.
- **(P3) No-evidence neutrality.** `n_vis = 0` gives `UNKNOWN`, never a numeric score.
- **(P4) Ray-count bound.** For each sensor, `n_vis ≤` the number of slots in the box's angular footprint.

**Not shown:** that `s` is a probability, or that `s` thresholds transfer across sessions.

### Failure cases and falsifiers

| Case | Effect on M3 | Mitigation / test |
|---|---|---|
| Porous or thin genuine objects (bikes, pedestrians at range, trailers) | Genuine `ADD` gets `TRAV` → false contradiction | Class/range-conditional models (M4); report by class |
| Dark or wet surfaces with no return | `UNK_NR`, coverage drops → `UNKNOWN` (not a false contradiction) | Rate of `UNK_NR` inside GT boxes, by class |
| Moving object + skew | Real object appears outside `B°` → `TRAV` | `δ_motion`; stratify by evaluator speed |
| Receiver occluded (shadow) | `OCC` only → `UNKNOWN` | Inherent: H4 |
| Fake placed on a real object (duplicate, class flip) | High support → passes | Class check via receiver-only decode (M5); duplicates mostly removed by NMS |
| `SHIFT` of a sparsely observed object | Both poses weakly supported → small difference | Report `SHIFT` separately; PosePert-type attacks A-F5 |
| Ground or kerb returns inside the core | False support | `h_g` band; ground map |
| Vegetation, glass, fences | Partial traversal of *real* obstacles that are not labelled objects | Only matters if they are effects; report |

**Two worlds, identical receiver evidence.** (W1) a real pedestrian in the receiver's ray shadow; (W2) a fabricated one there. `n_vis = 0` in both, so M3 says `UNKNOWN` in both. Correct, and the reason H4 exists.

### Complexity per frame (receiver)

- Range images: given by the organized grid, so O(#slots) to compute ranges. MS: 196,608 slots for TOP+DOME (64×1024 + 128×1024).
- Per effect: the box's angular footprint in each range image, times one slab test (≈ 30 FLOPs per slot).
  - Car at 20 m: TOP ≈ 40 cols × 8 rows ≈ 320 slots; DOME similar [E].
  - Distant pedestrian: tens of slots.
- Total ≈ `Σ_e footprint(e)·30` FLOPs. With tens of effects that is about 10⁵–10⁶ FLOPs: **negligible next to the ~5 GMAC deblock+head pass** [E, to measure].
- Memory: uint16 range image (0.4 MB) plus a direction LUT (MS: 2 × 196,608 × fp16 ≈ 0.8 MB) plus the ground map (static BEV at 0.4 m: 256² × fp16 = 128 KB).
- Communication: 0 extra bytes.

---

## M4. Evidential / statistical version: beta-binomial ray likelihoods with overdispersion, calibrated (recommended core)

### Estimand link

For an effect claim `κ ∈ {present, absent, pose b⁺}`, the receiver evidence gives a posterior `P(κ true | rays)`. The harm label follows from the claim's truth: a false presence claim is an FP; a false absence claim removes a TP. Duplicates and class errors break this link and are measured.

`ρ` is then estimated as `P(D ≤ m | X)` by a monotone calibration map applied to the evidence, fitted on block C.

### Observation model (fitted on clean block-T data only; no attack model)

- **Real-object model `G`.** For GT-matched receiver-visible objects of class `c`, in range bin `ρ_bin` and incidence bin `θ_bin`:
  - `n_S | n_vis ~ BetaBinomial(n_vis, μ_G, φ_G)`, mean `μ_G(c, ρ_bin, θ_bin)` and overdispersion `φ_G`.
  - Fitted by maximum likelihood with partial pooling across bins (hierarchical beta prior).
- **Empty-region model `∅`.** Same statistic for boxes of the same class geometry, placed in GT-empty, receiver-visible space at the same range and incidence. Background clutter is included.
  - Placement must avoid unlabelled objects: require ≤ 5 aggregated points from *all* agents.
- **Why beta-binomial, not binomial.**
  - Neighbouring beams hitting the same surface are positively correlated.
  - Binomial independence would make 300 rays look like 300 independent votes and give absurd confidence.
  - Overdispersion `φ` (intra-object correlation) yields an effective sample size `n_eff ≈ n_vis/(1 + (n_vis − 1)φ)`.
  - **Assumption to test:** a single `φ` per bin captures the dependence. Check with a posterior predictive test on block T, by class.

### Evidence and posterior

- Log Bayes factor: `ℓ_e = log BB(n_S; n_vis, μ_G, φ_G) − log BB(n_S; n_vis, μ_∅, φ_∅)`.
  - For a presence claim, use `ℓ_e`. For an absence claim, use `−ℓ_e`.
  - For `SHIFT`: `ℓ = ℓ(b⁺) − ℓ(b⁻)`.
- Prior odds `π` = base rate of true claims among `KNOWN` effects, by effect type, on block C.
- Posterior `q_e = σ(ℓ_e + logit π)`.
- Tile value `q = min_e q_e`.
- **Calibration.** Isotonic regression of `1{D ≤ m}` on `q`, fitted on block C. This gives `ρ̂`. Report the reliability diagram and ECE on block E.

### Unknown conditions

- `UNKNOWN_NO_EVIDENCE` if `n_eff < 3` **[A]** for any effect.
- `UNKNOWN_OOD` if `(c, ρ_bin, θ_bin)` had fewer than 30 fitting objects **[A]**.

### Temporal state (optional; reported separately)

- For static receivers, tiles are world-fixed. Keep per (sender `i`, tile `u`) discounted counts:
  - `A ← λ^{Δt} A + 1{q_e > ½}·w_e`, `B ← λ^{Δt} B + 1{q_e ≤ ½}·w_e`, with `w_e = min(1, n_eff/10)` **[A]** and `λ = 0.5` per second **[A]**.
  - `r_temp = (A + 1)/(A + B + 2)`. Status `STALE` if there was no update for more than 2 s **[A]**.
- **Use.**
  - `r_inst` decides whenever it is `KNOWN`.
  - `r_temp` is used **only** as the prior for `UNKNOWN` instantaneous tiles, under policy `U_temporal`. This is not the primary policy.
- **Why so restricted.** Temporal state is sender-local reputation and is poisonable (TrustFlip; on/off attacks). It never overrides instantaneous evidence. It is never reset at evaluator-known attack times.
- Both `r_inst` and `r_temp` are reported.

### Properties

- (P1)–(P3) of M3 still hold.
- **(P5)** With calibrated isotonic mapping, `ρ̂` is a probability **on the calibration distribution**. The guarantee does not transfer to unseen sessions or attacks; this is measured, not assumed.
- **(P6) Equal-likelihood neutrality.** If `μ_G = μ_∅` in some bin (e.g. far range), then `ℓ ≈ 0`, the posterior equals the prior, and the status should be unknown. We flag bins with `|μ_G − μ_∅| < 0.1` as `UNKNOWN_UNINFORMATIVE`.

### Failure cases

- All M3 cases, softened by class and range conditioning.
- Shift between block T and block E (EX-05 showed strong clip-to-clip shift for count statistics). **Gate:** fit on T, check predictive calibration on C.
- `μ_∅` contamination by unlabelled objects.

### Complexity

- M3 plus O(#effects) log-gamma evaluations. Negligible.
- Parameters: 2 models × |c| × |bins| × 2 ≈ 3 × 10 × 4 × 2 × 2 ≈ 480 floats.
- State: one (A, B, t) triple per (sender, tile). MS: 3 senders × 256 tiles × 12 B ≈ 9 KB.

---

## M5. Small learned, calibrated combiner (if data and deployment support it)

### Inputs per effect (all receiver-computable)

| Group | Features |
|---|---|
| Ray evidence (setting B) | `ℓ_e`, `n_eff`, `n_S/n_vis`, `n_O/(n_O + n_vis)`, `n_NR` fraction, status flags |
| Effect descriptors | Type (ADD/REMOVE/SHIFT), class, effect score, displacement, range and bearing from the receiver (**not absolute xy**), box size |
| Receiver-only decode | Does the receiver alone detect a matching box? IoU, score |
| Peer corroboration (untrusted, independent unless colluding) | Number of other senders whose single-source decode supports the effect; number of peers whose BEV coverage includes the tile |
| Feature residuals (co-observed tiles only) | PoseGuard crop L1 (sender vs receiver features); cosine; energy ratio [`zhang2026latentguardian`] |
| Fusion internals | Sender's attention share `α_i` in the tile (SOMBRA indicator [`wang2025lucia`]) |
| Temporal | Feature change vs the sender's previous warped message in the tile; exact-replay flag |
| Metadata | Claimed sender pose vs the receiver's own detection of the sender vehicle, if visible (trusted check of T3) |

### Model

- L2-regularised logistic regression **(primary)**.
- Optional depth-3 gradient-boosted trees (≤ 100 trees) **[A]**.
- Fit on block T: clean + **train-family** attacks only. Calibrate (isotonic) on block C.
- Abstain (`UNKNOWN`) when every trusted-evidence channel is unavailable. **Peers alone never make a tile `KNOWN`** (collusion risk); this is ablated.

### Shortcut controls

- No sender ID, no absolute position, no segment index.
- Permutation test: shuffle sender IDs, so outputs are identical.
- Leave-attack-family-out evaluation.
- Group-held-out (block E) evaluation only.

### Properties

None beyond calibration on C. Whether it generalises to unseen families is measured, not assumed.

### Failure cases

- Learns attack artefacts (e.g. PGD texture) rather than physics. Detected by family-held-out tests.
- Few harmful labels in block T. **Gate:** fewer than 500 harmful effects in T means drop GBDT and keep LR.

### Complexity

- LR: about 25 MACs per effect.
- GBDT: about 300 comparisons per effect.
- Feature extraction is dominated by single-source decodes: one deblock+head pass per sender. That is *additional* to M4's pass, unless they are shared (the receiver-only decode is shared with B-MADE).

---

## Fusion integration (all candidates)

- **Hard gate** (primary). If `r[i,t,u] < θ`, output `Y⁻(i)` in tile `u`.
  - Equivalently, mask sender `i` from attention at those pixels and rerun deblock+head locally.
  - `θ` is chosen on block C to keep the clean false-gating rate of USEFUL effects ≤ 5% **[A]**.
- **Soft weight** (secondary). Add `log(r + 10⁻³)` to sender `i`'s attention logits at pixels in `u`.
  - Using the LUCIA bound, the attacker's attention share becomes ≤ `r·e^Δ/(r·e^Δ + N − 1)`. *Derivation to be checked in notebook 05.*
  - Requires one more deblock+head pass.
- **Unknown policy**, declared and reported in full:
  - `U_keep` (r := 1, **primary**: MINT never acts without evidence, so clean behaviour in unknown regions equals AttFuse);
  - `U_prior` (r := calibrated base rate);
  - `U_drop` (r := 0);
  - `U_temporal` (r := `r_temp`).

## Counterexample suite (to be built as unit tests and notebook cases)

1. Honest unique view in the receiver's shadow, and a fabricated twin: both must be `UNKNOWN` (M3/M4). M5 must not be more confident than its peer evidence allows.
2. Genuine bicycle with 60% traversal: M3 false contradiction; M4 with the bike model should not reject.
3. Fake car in receiver-visible free space: M3/M4 must contradict. M1 may accept.
4. SOMBRA removal of a receiver-visible car: `REMOVE` effect with high `n_S`, so it is contradicted.
5. A 1 m pose shift of a well-observed car: `SHIFT` with `ℓ(b⁺) − ℓ(b⁻) < 0`.
6. Dark car with 80% `NR`: `UNKNOWN`, not a contradiction.
7. Replay of a 1 s old message: SHIFT effects on moving objects contradicted where visible; exact-replay flag in M5.
8. Collusion: two senders fabricate the same object in the receiver's shadow. Peer corroboration = 2 but trusted evidence is none, so `UNKNOWN` (by the peer-alone rule).

## Shortlist and recommendation

| Candidate | Keep? | Reason |
|---|---|---|
| M0, M1 | Yes (baselines) | Required references |
| M2 (B-LUCIA, B-PoseGuard-tile, B-CAD-local, B-MADE-tile) | Yes, B-LUCIA and B-CAD-local mandatory; others if budget allows | Closest feasible prior work |
| M3 | Yes, as the **deterministic support/traversal baseline** and ablation of M4 | User-requested idea; CARLO-equivalent; narrowed to receiver rays |
| **M4** | **Recommended minimal method (MINT-v0)** | Physically grounded, trusted evidence; explicit unknowns; calibrated; tiny cost |
| M5 | Planned extension; also the **fallback** if ray evidence is unavailable (setting A) | Combines complementary channels; needs enough labels |

**Fallback rule (preregistered).** Switch MINT-v0 to M5-A (feature-only channels, setting A) if any of these holds on clean development data:
- V-06 fails: direction LUT reconstruction error > 5 cm at 50 m;
- receiver coverage is too low: under 20% of effectful tiles with `n_eff ≥ 3` **[A]**;
- the beta-binomial models fail their posterior-predictive check in more than half the bins.

The ray study is then reported as a negative feasibility result.

## Unresolved assumptions (also in [risks](risks_and_open_questions.md))

- **[A] numbers:** κ, h_g, τ, δ_motion, n_min, n_eff thresholds, λ, θ, effect thresholds.
- Locality of AttFuse in the trained model and code (V-03).
- Direction LUT and mount rotations (V-06).
- Keyframe identification (V-04).
- Whether receiver coverage of *effectful* tiles is non-trivial. This decides whether H6 can matter at all.
