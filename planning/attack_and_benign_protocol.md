# Attack and benign-stress protocol

Checkpoint 1, 2026-10-22. Families, budgets, schedules and seeds are frozen before block-E exposure ([evaluation protocol](evaluation_protocol.md) §9). Threat classes T1–T6 are defined in the [contract](information_and_threat_model.md) §7.

## 0. Rules that apply to every family

- **Knowledge separation.**
  - The *attacker* sees its own stream, the shared model (white-box unless stated), previously broadcast messages and the receiver's position. It does not see same-frame receiver data.
  - The *evaluator* additionally sees GT, schedules and clean counterparts.
  - **GT-targeted attacks** (target chosen from GT boxes) are labelled `GT-TARGETED`: a convenience that grants the attacker oracle target selection. Where feasible, a matched `SELF-TARGETED` variant chooses targets from the attacker's own detections.
- **Labels stay physical.** GT describes the real world. A fabricated object never becomes a GT box. A removed real object stays in GT.
- **Realization ledger, per event.** Columns:
  - `intended`: family, severity, target, mask;
  - `serialized_ok`, `reload_ok` (byte round-trip of the edited cloud or tensor);
  - `realized_change`: point count / slot count changed, feature ℓ₂/ℓ∞ in mask and outside mask;
  - `realized_effect`: the effect set ℰ in the receiver output;
  - `realized_harm`: D summed over affected tiles, ΔFP, ΔFN.
  Zero-effect, failed and harmless events stay in every all-attempt denominator.
- **No physical-realizability claim for digital edits.** Raw-cloud edits are "insider fabrication consistent with the sender's beam geometry". Feature edits are "message manipulation".
- **Determinism.** Every random choice is keyed by SHA-256 of (family, severity, unit id, frame, seed). Same key, same bytes.
- **Frozen at Stage 5.** The family list, severities, schedules, seeds, the attack-family split for learned combiners, and the definitions of intended and achieved severity.

## 1. Raw-cloud alterations before encoding (T1; re-encoded through the frozen sender encoder)

Using the organized beam grid makes edits ray-consistent from the sender's viewpoint: each slot is one ray.

| ID | Family | Operation (sender frame, per slot) | Severities **[A]** | Notes |
|---|---|---|---|---|
| A-R1 | Object removal | For slots whose return lies in the target object's box (dilated 0.2 m), replace range with the background: the intersection with the fitted ground plane or the next surface from the sender's previous-frame range at that slot. Else `NO_RETURN`. | Fraction of target slots: 0.5 / 1.0 | GT-TARGETED and SELF-TARGETED |
| A-R2 | Ghost injection | Ray-cast a mesh (car / bike / pedestrian templates) placed on the ground at a target pose. Slots whose ray hits the mesh before their measured return get the hit range. | Distance from sender 10/25/40 m; object class | CAD §4.2-style; placements in receiver-visible free space **and** in receiver shadow (two strata) |
| A-R3 | Displacement | Remove the target (A-R1), then re-inject its own point set ray-cast at a pose shifted 0.5 / 1 / 2 m (± up to 10° yaw) | 0.5 / 1 / 2 m | PosePert-like at the raw level |
| A-R4 | Count-preserving distortion | Scale the target's points about its centre (0.8× / 1.2×) along heading, re-ray-cast so the slot count is preserved | 0.8 / 1.2 | Size and shape attacks; tests SHIFT/class effects |
| A-R5 | Random sparsification | Drop 30 / 60% of valid slots, set to `NO_RETURN` | 0.3 / 0.6 | Low-harm control at the attack level. Also appears as benign B-2. |

**Placeholder rule.** Placeholder slots are no-returns. They are never moved, counted as points, or chosen as targets. This is the lesson of DA-05.

## 2. Received intermediate-feature alterations (T2; applied to the transmitted tensor at every fusion scale)

| ID | Family | Operation | Budget **[A]** | Access |
|---|---|---|---|---|
| A-F1 | Masked targeted PGD (spoof / remove) | Online: 1 PGD step per frame, reused and re-indexed; offline variant with 25 steps. Mask 5 m × 5 m around the target. CAD loss eq. 4. Values clipped to per-channel clean [p0.1, p99.9] from block T. | lr per CAD; ℓ∞ unbounded inside the mask but range-clipped | White-box detector |
| A-F2 | Patch replacement / suppression | Replace the mask region with (a) the sender's own feature patch of a real object from another place or time (copy-paste spoof), or (b) its background patch from a free region (suppression) | Mask 3 m / 5 m | Black-box |
| A-F3 | Attention hijack | SOMBRA-style: maximise the attention share `L_attn` plus a removal loss, under ε_max ∈ {0.5%, 1%, 2%} of the feature ℓ∞ range | ε as above | White-box fusion |
| A-F4 | Bounded untargeted PGD | Tu et al.: ℓ∞ ε ∈ {0.05, 0.1, 0.2} × feature std, 10 steps, whole map | — | White-box |
| A-F5 | Feature pose shift | Translate a target object's feature patch by 0.5 / 1 / 2 m. Fill the vacated area with background (A-F2b). | — | Black-box |
| A-F6 | Blind-area attack | Any of A-F1/A-F2 restricted to tiles that the attacker *estimates* are unobserved by the receiver. The attacker ray-casts the receiver's view from its known position using the attacker's own scan. | Same as base family | Gray-box (knows the receiver location, not its exact scan) |
| A-F7 | Adaptive against MINT | (a) A-F6 with the *true* receiver-visibility mask (white-box upper bound). (b) SHIFT just below the effect threshold, accumulated over frames. (c) Spoof co-located with a real object to induce a class flip or duplicate. (d) For M5: PGD with an extra term `−λ log r` through a differentiable surrogate of the combiner. | Same as base families | White-box MINT |
| A-F8 | Channel corruption / scaling | Zero or scale ×0.1/×10 a random 10% / 50% of channels in a region or globally | — | Fault-like |

## 3. Metadata, temporal and collusion (T3–T5)

| ID | Family | Operation | Severities **[A]** |
|---|---|---|---|
| A-M1 | Pose spoofing | Claimed sender pose offset by 0.5/1/2 m or 1/3/5° yaw (features unchanged) | as listed |
| A-M2 | Timestamp spoofing | Claimed stamp shifted by ±50/100 ms | as listed |
| A-T1 | Replay / stale | Send the message from t − k, k ∈ {1, 5, 10} frames, unchanged or with tiny noise | as listed |
| A-T2 | On/off | Any spatial family active in 1 s bursts with 1/3 s gaps | duty cycle |
| A-T3 | History poisoning | 10 s honest, then a slow drift (A-F5 with displacement ramping 0 → 2 m over 5 s) | ramp rate |
| A-C1 | Collusion | Two senders apply the same A-R2/A-F2 fabrication at the same pose | 2 colluders |

## 4. Schedules

- Each attacked episode is a contiguous window inside a segment or scenario, with clean context before and after:
  - **sustained**: 5 s on;
  - **burst**: 2 × 1 s with a 3 s gap;
  - **ramp**: A-T3.
- One attacker at a time, except A-C1.
- Attacker choice is rotated across senders. Never always the same vehicle (lesson EX-01).
- Targets lie within ±51.2 m and the label crop. For MS keyframe metrics, at least one keyframe must fall inside the window.

## 5. Benign stresses and natural controls

| ID | Stress | Parameters **[A]** | Notes |
|---|---|---|---|
| B-1 | Sender range noise | σ = 2 / 5 cm per slot | |
| B-2 | Sender sparsification | 30 / 60% of valid slots → `NO_RETURN` | Legitimate sparse returns |
| B-3 | Feature quantization | fp16 / int8 (per-channel affine) | Also ablation AB-8 |
| B-4 | Pose error | N(0, 0.15 m) translation, N(0, 0.4°) yaw per frame (MS bounds [V]) | |
| B-5 | Delay | 100 ms stale message (honest) | Benign twin of A-T1 |
| B-6 | Message drop | 10 / 30% of sender frames missing | Tests the STALE state |
| B-7 | Receiver-scan degradation | Receiver slots sparsified 30%; receiver-side noise | Evidence availability, not sender honesty |
| B-8 | Natural heterogeneity | EV (tilted, zero intensity) vs laser vehicle | Stratum, not an injection |
| B-9 | Natural unique views / occlusion | SENDER_ONLY stratum | H3 |
| B-10 | Natural moving objects | Speed strata | |
| B-11 | Viewpoint-dependent or porous objects | Natural bikes, trailers, fences in effects | TrustFlip-like benign confusion |
| B-12 | Cross-block shift | Natural: T vs C vs E | Calibration transfer |

## 6. Attack-family split for learned components (M5 only)

- **Seen in T/C:** A-R2, A-F1, A-F2, A-M1, A-T1.
- **Held out to E only:** A-R1, A-R3, A-R4, A-F3, A-F5, A-F6, A-F7, A-F8, A-M2, A-T2, A-T3, A-C1.
- MINT-v0 (M4) fits **no attack data** (physics models on clean data only; calibration on clean + seen families). Its calibration on held-out families is therefore a genuine transfer test.

## 7. Realization checks (Stage 5 gate)

For every family, on block T/C only:
1. Byte round-trip of the edited artefact.
2. The realized change is non-zero, or explicitly zero.
3. **Task harm against GT** distribution: fraction with D > 0. Families with < 10% harmful events are *reported as low-harm*, not dropped.
4. Raw attacks: visual overlay of the sender's edited range image and the receiver's view, for 5 random events.
5. Feature attacks: an in-mask vs out-of-mask change ratio ≥ 10 for masked families.

## 8. Explicitly out of scope

- Physical laser spoofing.
- Receiver compromise.
- Jamming and DoS.
- Cryptographic attacks.
- Physical adversarial meshes (TrustFlip), except through the benign proxy B-11.
