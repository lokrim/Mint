# E1 — cache-only diagnostics (development, block T, in-sample)

Run 2026-10-23.
- **Pre-registration:** [`runs/20261023-E1/preregistration.json`](../runs/20261023-E1/preregistration.json), committed in `0b9d4e8` before any E1 code ran.
- **Results:** `runs/20261023-E1/online_check.json`, `cost.json`, `rules_and_blind.json`.
- **Code:**
  - [`pipeline.py`](../src/mint/reliability/pipeline.py)
  - [`r1.py`](../src/mint/reliability/r1.py)
  - [`e1_cost.py`](../runners/e1_cost.py)
  - [`e1_rules.py`](../runners/e1_rules.py)
  - [`mint_v0_online_check.py`](../runners/mint_v0_online_check.py)
  - [`test_e1.py`](../tests/test_e1.py)

**Scope.** Everything here is **development / in-sample** on the 3 block-T scenarios and the 24-frame block-T slice. Nothing was downloaded, and no calibration or test scenario was opened. Timings are from an M1 CPU, 8 threads.

## Outcome against the pre-registered stop criteria

| Criterion | Value | Pass |
|---|---|---|
| R1 mean AP@0.7 recovery ≥ 0.10 | **0.196** | yes |
| R1 clean AP@0.7 relative loss ≤ 1% | **−0.04%** | yes |
| R1: no family < −0.05 | min **0.162** | yes |
| Some Part A variant ≤ 10% p95 overhead at n = 2 | best exact **47%** (batched); best of all 44% (footprint, inexact) | **no** |
| **→ Recommend downloading calibration scenarios** | | **NO** (cost criterion fails) |
| Blind-tile attention: AUROC ≥ 0.70, CI lower bound > 0.60 in ≥ 3/4 families | 0/4 (AUROC 0.30–0.47) | **no → drop** |

## Part A: cost

**A1.** The final masked decode is replaced by `compose()+finalize()` over the decodes already computed. Boxes and gating choice are **identical on 24/24 frames**, with 0 extra decodes.
- Multi-sender tiles (only possible with n ≥ 3) trigger one extra subset decode, and only then.
- `compose()` tile selection was vectorised; existing tests still pass.

**A2. Latency accounting.**
- **Baseline** = receiver-only encode (bit-identical to the receiver's slice of the joint encode) + plain fusion, decode and post-process.
- **Sender encoding** was **0.30 s p50**, i.e. **62%** of the old "encode" time. The E0 figure of +16% p50 counted it as receiver work.
- **Corrected overhead (online check, n = 2): 33% p50 / 69% p95.**
- **Components (p50 / p95):**
  - receiver encode 0.17 / 0.26 s
  - plain 0.08 / 0.12 s
  - counterfactual 0.07 / 0.09 s
  - evidence 0.009 / 0.021 s
  - compose 0 / 0.086 s (post-process of the gated output, mostly NMS)

**A3. Overhead p50 / p95 vs number of agents.**
- Method: per-frame median of 3 interleaved repetitions. For n > 2, sender features are replicated (timing only). Exactness is measured against sequential on 24 frames.
- Overhead = (counterfactual + evidence + compose) / baseline. The diagnostic joint variant is computed differently, as joint pass + post-process − plain-only time.

| Variant | n = 2 | n = 3 | n = 4 | n = 5 | Exact |
|---|---|---|---|---|---|
| Sequential (as implemented) | 26% / 52% | 55% / 150% | 112% / 213% | 153% / 235% | reference |
| Batched n−1 counterfactuals | 32% / 47% | 53% / 160% | 107% / 218% | 148% / 246% | 24/24 |
| Footprint, literal ("non-zero features") | = sequential | | | | (footprint = 100% of pixels) |
| Footprint, pillar tiles (diagnostic) | 29% / 44% | 49% / 152% | 105% / 203% | 146% / 223% | **0/24** (gated output 20/24 at n = 2) |
| Joint Y⁺ + counterfactuals (diagnostic) | 48% / 75% | 46% / 162% | 115% / 214% | 154% / 247% | 24/24 |

- **D-17 (≤ 10% p95): no variant, at any n.**
- **The floor at n = 2 is structural.** One dense decode (0.07 s) against a 0.33 s receiver-only baseline is already about 21%. Batching gives no gain on CPU.
- **The footprint idea fails twice.**
  - The sender's features are non-zero everywhere, because of the BatchNorm bias.
  - Even restricted to the tiles that hold its points, the result is inexact. The sender's constant feature still takes a share of the attention softmax, so excluding it changes the fused feature in every tile.
- **The n ≥ 3 p95 values are inflated.** Replicated senders gate the same tiles, which forces subset decodes (2–4 frames).
- **Recording gap.** The joint row did not record its own extra-decode count; the code is fixed, but the JSON was not regenerated.

## Part B: R1 vs θ = 0 (MINT-v0.0)

The θ = 0 rows reproduce E0 exactly.

**AP@0.7 and recovery of attack loss** (AP@0.5 recovery in brackets):

| Condition | Undefended | θ = 0 | R1 |
|---|---|---|---|
| clean (relative loss) | 0.8737 | 0.8691 (0.53%) | **0.8741 (−0.04%)** |
| spoof_feat | 0.8323 | 0.06 (0.22) | **0.17 (0.23)** |
| remove_feat | 0.8631 | −0.31 (0.45) | **0.16 (0.63)** |
| shift_feat | 0.8278 | 0.17 (0.38) | **0.18 (0.32)** |
| spoof_pts | 0.8595 | −0.03 (0.45) | **0.28 (0.50)** |

**Gated units.** Effect types are given as ADD / REMOVE / SHIFT; a unit counts once for each type that gates in it.

| Condition | Rule | Gated (harmful / neutral) | Precision | Recall of KNOWN harmful | False rejections of USEFUL (A / R / S) |
|---|---|---|---|---|---|
| clean | θ = 0 | 243 (90 / 92) | 0.37 | 0.69 | 61 (6 / 41 / 15) |
| clean | R1 | 76 (54 / 2) | 0.71 | 0.41 | **20 (0 / 20 / 0)** |
| spoof_feat | θ = 0 / R1 | 373 / 198 | 0.58 / **0.89** | 0.84 / 0.68 | 62 / **20 (all REMOVE)** |
| remove_feat | θ = 0 / R1 | 256 / 92 | 0.39 / **0.72** | 0.73 / 0.49 | 63 / **24 (all REMOVE)** |
| shift_feat | θ = 0 / R1 | 418 / 221 | 0.59 / **0.87** | 0.80 / 0.62 | 73 / **23 (all REMOVE)** |
| spoof_pts | θ = 0 / R1 | 313 / 142 | 0.51 / **0.85** | 0.80 / 0.60 | 61 / **20 (all REMOVE)** |

**SHIFT displacement d.**
- Under θ = 0, SHIFT drives 121–139 gates per condition. Most land on NEUTRAL tiles (92–97 per condition, median d 0.42 m, all < 1 m except two), and 13–20 are false rejections (median d ≈ 0.5 m).
- Under θ = 0, harmful SHIFT gates have median d 0.53 m on clean. On shift_feat it is **2.27 m** (13/26 ≥ 2 m), i.e. the attack's own shift.
- R1 gates SHIFT in only 1–3 units per condition (2 harmful ones at d ≥ 2 m). Its recovery on shift_feat comes through ADD/REMOVE effects.

## Part C: blind-tile attention (UNKNOWN_NO_EVIDENCE units)

| | clean | spoof_feat | remove_feat | shift_feat | spoof_pts |
|---|---|---|---|---|---|
| AUROC (higher share → HARMFUL) | 0.29 | 0.47 | 0.30 | 0.41 | 0.43 |
| 95% CI (scenario bootstrap, 3 blocks) | 0.20–0.78 | 0.26–0.64 | 0.19–0.78 | 0.29–0.77 | 0.24–0.85 |
| n units (harmful) | 725 (101) | 1000 (328) | 719 (102) | 809 (192) | 837 (196) |

- Per-scenario AUROC ranges from 0.19 to 0.85: the sign is not even stable across scenarios.
- The opposite direction looks better in pooled data, but it was not pre-registered and is scenario-dependent, so it is not a finding.
- **Caveat:** attention is computed from the attacker's own features, so even a positive result would cover a non-adaptive attacker only.

## Interpretation

1. **R1 fixes the failure diagnosed in E0.**
   - Requiring resolvable evidence removes almost all small-margin SHIFT gating, which is what destroyed the sender's localisation benefit.
   - Precision rises from about 0.5 to about 0.85 and clean AP@0.7 is untouched.
   - Recovery on every family is positive (0.16–0.28) but modest. Recall falls to 0.4–0.7.
   - The remaining false rejections are all REMOVE effects.
   - These numbers are in-sample on 3 scenarios, and R1 was written after seeing E0 on the same data.
2. **Cost blocks the download decision.**
   - With honest accounting, a dense counterfactual on CPU costs about 21% or more of the receiver's own perception at n = 2. It grows linearly with n.
   - No implementation variant changes this; meeting D-17 would need a different cost model, not an optimisation.
   - By the pre-registered rule, the calibration scenarios are **not** recommended for download.
3. **The attention fallback for blind tiles is dropped** (D-29 drop criterion).

Nothing further was run after this report. Proposed log entries are in [`decision_log_proposed_appendix.md`](decision_log_proposed_appendix.md) (D-38 to D-41).
