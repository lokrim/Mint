# MINT-v0 specification (recommended minimal method)

Checkpoint 1, 2026-10-22. **Proposal for review; nothing implemented.**

Derivations and alternatives: [methodology_candidates.md](methodology_candidates.md) M4. Contract: [information_and_threat_model.md](information_and_threat_model.md).

Assumption status legend:
- **V**: verified (source or code);
- **L**: pilot-measured;
- **A**: assumption needing development justification;
- **⚠**: unresolved, blocks the stage named.

## 1. Scope

| Item | Value | Status |
|---|---|---|
| Fusion model | AttFuse PointPillars (OpenCOOD lineage), per-scale per-pixel attention | V (code) |
| Pixel locality of post-fusion computation | Required | ⚠ V-03 (Stage 1) |
| Receiver | MS: TOP (+ DOME, co-owned). OP/VR: ego vehicle | A (decision Q3) |
| Information setting | B (receiver's own scan allowed) with A-channels optional | A (decision Q3) |
| Unit | (sender i, fusion time t, tile u); tiles 6.4 m × 6.4 m aligned to stride 8 | A |
| Output | `r = (status, value, aux)`; value = calibrated `P(D ≤ m | X)` | A (calibration on block C) |
| Primary policy | Hard gate at θ; unknown → keep (`U_keep`) | A |

## 2. Inference algorithm (per frame t)

```
inputs: ẑ[i,t] for i in senders (warped by claimed pose), receiver features z[0,t] (+dome),
        receiver range images R_k (k in receiver sensors) with NR mask, receiver ground map Gm,
        frozen detector parts (fusion F, deblock+head H, NMS), fitted models (μ,φ tables), calibrator g, θ
1. logits ← attention logits at each scale and pixel (shared with plain AttFuse)
2. Y⁺ ← NMS(H(F(all agents; logits)))
3. for each sender i:
     Y⁻(i) ← NMS(H(F(all agents except i; logits masked)))     # deblock+head only
     for each tile u where sender i has nonzero attention mass:  # sparsity: skip others
        ℰ ← effects(Y⁺|u, Y⁻(i)|u)                              # ADD / REMOVE / SHIFT
        if ℰ = ∅: r ← (NO_EFFECT, 1); continue
        for e in ℰ: counts_e ← ray_counts(e.box(es), R_k, Gm)    # range-image footprint + slab test
                    ℓ_e ← logBF(counts_e; μ,φ by class, range, incidence)
                    status_e ← UNKNOWN if n_eff<3 or bin OOD or bin uninformative
        if any status_e UNKNOWN: r ← (UNKNOWN_*, NaN, aux)
        else: r ← (KNOWN, g(min_e σ(ℓ_e + logit π_type(e))), aux)
4. output tile u uses Y⁻(i)|u for every sender i with KNOWN r < θ (gate); else Y⁺|u
   (gating several senders in one tile: mask all of them; one extra local pass)
5. update temporal state h (reported only; not used under U_keep)
```

## 3. Components and parameters

| Component | Definition | Default | Status |
|---|---|---|---|
| Effect matching | Class-wise Hungarian on BEV IoU | IoU ≥ 0.1 | A |
| SHIFT thresholds | Centre > 0.3 m, or yaw > 10°, or class change | — | A |
| Box core | Shrink horizontally by max(0.15 m, 15%); z ∈ [z_g + 0.3, z_top − 0.1] | — | A |
| Envelope | Dilate by v̂·Δt + σ_pose; v̂ = 15 m/s; Δt ≤ 0.05 s; σ_pose 0.15 m + ρ·tan 0.4° | — | A (bounds V from the paper) |
| Range tolerance τ | 0.05 m + 0.01·ρ | — | A |
| Slot directions | Per-row elevation + per-column azimuth + mount rotation, fitted on block-T frames | 003: Ry −15° (L); TOP: (−22.25°, −6.75°) (L) | ⚠ V-06 |
| No-return slots | Excluded from counts | — | V (findings) / L (P1) |
| Ground map | Static receiver: median ground height per 0.4 m BEV cell from block-T clean scans | — | A |
| Real-object model | Beta-binomial (μ_G, φ_G) by class × 4 range bins × 2 incidence bins, hierarchical pooling | Bins 0–15/15–30/30–45/45–52 m | A |
| Empty model | Beta-binomial (μ_∅, φ_∅) on synthetic boxes in GT-empty, receiver-visible space with ≤ 5 aggregated points | Same bins | A |
| Unknown rules | n_eff < 3; bin < 30 fits; \|μ_G − μ_∅\| < 0.1 | — | A |
| Prior π | Base rate of true claims by effect type, block C | — | A |
| Calibrator g | Isotonic regression of 1{D ≤ m} on q, block C | — | A |
| Gate θ | Max θ such that the clean false-gating rate of USEFUL effects on block C is ≤ 5% | — | A |
| Temporal | Discounted counts λ = 0.5/s; STALE after 2 s; reported only | — | A |

## 4. Typed interfaces (to implement in Stage 3)

```python
@dataclass(frozen=True)
class Reliability:
    status: Literal["KNOWN","NO_EFFECT","UNKNOWN_NO_EVIDENCE","UNKNOWN_OOD",
                    "UNKNOWN_UNINFORMATIVE","UNKNOWN_STALE","NOT_APPLICABLE_EMPTY"]
    value: float | None          # calibrated P(D <= m | X) iff status == KNOWN and calibrator fitted
    is_probability: bool         # False for uncalibrated variants (M3, M4-precalibration)
    effects: tuple[EffectEvidence, ...]   # audit: type, boxes, counts, logBF, bin
    r_temp: float | None; temp_status: str

def mint_reliability(frame: ReceiverFrame, models: FrozenModels, params: Params,
                     state: TileState) -> tuple[dict[tuple[str,int], Reliability], TileState]: ...
```

- **Purity.** No evaluator object is importable from the inference package. `ReceiverFrame` cannot hold GT, schedules or clean counterparts by construction.
- **Process separation.** The OS-level separation is tested in Stage 2.

## 5. Training and fitting data flow (offline, block T then block C)

1. **Detector.** Use a released checkpoint (OP/VR), or train on block T (MS).
2. **Cache.** Clean features, plus outputs Y⁺ and Y⁻(i) for every block-T and block-C frame. Keyframes are primary.
3. **Fit μ, φ** on clean block-T GT-matched objects and synthetic empty boxes. **No attacked data is used** to fit the physics models.
4. **Compute effects and D labels** on block C (clean + train-family attacks). Fit the prior π and the calibrator g. Choose θ.
5. **Freeze and hash** everything, then seal the predictions before opening block E outcomes ([evaluation protocol](evaluation_protocol.md) §9).

## 6. What MINT-v0 explicitly does not do

- Judge contributions in tiles without receiver evidence. Unknown there means keep (`U_keep`); the consequences are measured by H3/H4.
- Use peers as trusted evidence.
- Use sender-supplied side information.
- Detect intent, or produce per-sender reputation decisions.
- Modify the backbone or retrain the detector.

## 7. Extension path (only after v0 passes Stage 4 gates)

- **MINT-v1.** M5 combiner using v0 evidence plus feature-residual, attention-share, peer and temporal channels.
- **MINT-v1-A.** Setting A only. Fallback if ray evidence is infeasible.
- **Soft weighting variant.**
