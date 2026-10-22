# SOMBRA attack and LUCIA defense: Wang et al., USENIX Security 2025

- **Citation.** `wang2025lucia`. URL: https://www.usenix.org/system/files/usenixsecurity25-wang-chenyi.pdf
- **Access.** FULL-CLOSE on §4.2 (attentive fusion, attacker influence, p. 7391), §5.1–5.3 (LUCIA, p. 7394). Adaptive-attack section (Table 7) and limitations skimmed. Read 2026-10-22.

## Question, unit, inputs
- **Question.** Can a single insider remove objects by hijacking attentive fusion? Can trust-aware attention mitigate it cheaply?
- **Unit (defense).** One **trust score per agent per frame**, `T_i`.
- **Inputs.** The intermediate feature maps already exchanged. No extra communication.

## Attack (§4.2–4.3)
- AttFuse per-pixel attention: `A(x) = softmax(X(x)X(x)^T/√C)` (eq. 3). Fused vector `Σ_j α_j(x) X_j(x)` (eq. 4).
- **Attention-share bound (eq. 6).** If benign pre-softmax scores are bounded and the perturbation raises the attacker's score by Δ, then `α_a ≤ e^Δ/(e^Δ + N − 1)`, with `Δ ≤ ε_max‖X_v(x)‖₁/√C`.
  - Influence grows exponentially in Δ and only linearly with the number of benign agents.
- **SOMBRA objectives.** Attention-boost loss `L_attn = mean_x α_a(x)` (eq. 5) plus targeted or mass object-removal losses.
- Reported about 99% success with under 1% perturbation strength, and no knowledge of benign agents beyond the victim (abstract).

## Defense (§5.2)
- Compress each agent's map by average pooling and normalise it. Compute pairwise L1 distances.
- `T_i = 1 − softmax(Σ_{j≠i} ‖X_i − X_j‖₁)[i]` (eq. 10).
- Multiply both logits and normalised weights by `T`:
  - `Â(x) = softmax(X X^T T/√C)` (eq. 11);
  - `Â_T = Â ⊘ ÂJ` (eq. 12).
- No retraining.

## Our explanation
- LUCIA is the closest prior work to *reliability-aware fusion*. MINT's fusion hook (log-prior on attention logits) is a spatially resolved analogue.
- Weaknesses as written:
  1. **Global per-agent score.** PoseGuard measured dilution: the trust score changes about 0.015 under a local pose attack (PoseGuard §5.3.1).
  2. **Softmax over agents' total L1 distances is relative.** With N = 2 (V2I), the two agents get complementary scores no matter who is wrong.
  3. **Honest unique views raise L1 distance.** They are penalised by construction.
  4. Not calibrated.
- The attention-share bound is a useful formal lens for our adaptive attack A-F7, and for why per-tile prior weights cap attacker influence: with prior `r`, the bound becomes roughly `r·e^Δ/(r·e^Δ + N − 1)`. *Our extension, to be derived and checked.*

## Evaluation
- OPV2V, with Attentive Fusion, CoAlign, Where2comm and V2VAM.
- Single compromised vehicle (stated limitation).
- Adaptive attacker evaluated (Table 7).
- Overhead about 10⁻² s (as quoted by Latent Guardian's comparison).

## Code and licence
- Zenodo 15523769 (v "initial", 2025-05-27) and 16740921 (v1.1, 2025-08).
- `SOMBRA_LUCIA.zip` (small) plus `traffic_jam_data.zip` (0.197 GB). CC-BY-4.0.
- **Not downloaded.**

## What transfers
- AttFuse is the target fusion.
- The SOMBRA attack as an evaluation attack: family A-F3 attention hijack.
- LUCIA as the closest feasible prior baseline `B-LUCIA`.
- The attention-share bound.

## What does not transfer
- Per-agent granularity.
- Relative-softmax trust.

## Experiment
`B-LUCIA` vs MINT under:
- local attacks (PosePert-like A-F5, masked PGD A-F1);
- global attacks (SOMBRA mass removal);
- the honest unique-view stratum.

Expected: LUCIA competitive on global attacks, weaker on local ones. Unknown on unique views. All measured on grouped held-out sessions.
