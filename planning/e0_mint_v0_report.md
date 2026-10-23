# E0 headroom, Stage-2 geometry re-verification and MINT-v0.0 (development, block T)

Run 2026-10-23. Pre-registration: [`runs/20261023-E0/preregistration.json`](../runs/20261023-E0/preregistration.json), committed (`492a065`) before any download.
- Results: `runs/20261023-E0/e0_summary.json`, `mint_v0_summary_std.json`, `mint_v0_online_check.json`, `download_ledger.json`.
- Code:
  - [`runners/e0_stream.py`](../runners/e0_stream.py)
  - [`runners/e0_analyze.py`](../runners/e0_analyze.py)
  - [`runners/mint_v0_eval.py`](../runners/mint_v0_eval.py)
  - [`runners/mint_v0_online_check.py`](../runners/mint_v0_online_check.py)
  - [`src/mint/fusion/compose.py`](../src/mint/fusion/compose.py)
  - [`src/mint/geometry/ground.py`](../src/mint/geometry/ground.py)
  - [`src/mint/attacks/patches.py`](../src/mint/attacks/patches.py)
  - [`src/mint/eval/harm_labels.py`](../src/mint/eval/harm_labels.py)
  - [`src/mint/reliability/`](../src/mint/reliability/)

**Development evidence only.**
- The three Stage-2 pilot scenarios (block T, D-25) were used. Everything is in-sample, and nothing is calibrated.
- No calibration or test scenario was downloaded or opened.

## 1. Preflight

| Check | Result |
|---|---|
| `planning/findings/` 73 vs 75 files | All 73 manifest-listed files match their SHA-256 hashes. The 2 extra files are `evidence_manifest.json` (it excludes its own hash by design) and a git-ignored macOS `.DS_Store`. Git tracks 74 = 73 + the manifest. Nothing was modified. |
| Git checkpoint | Tree clean at `a61fe3c`, tagged `checkpoint/pre-e0-2026-10-23`. Git-ignored run outputs (Stage-1 preds, Stage-2 per-scenario JSONs) were archived to `data/checkpoints/runs_ignored_pre_e0_2026-10-23.tar.gz`, with a SHA-256 manifest committed at `runs/CHECKPOINT_pre_e0_2026-10-23.json`. |
| Harm notation | `D = L_u(Y⁺) − L_u(Y⁻(i,u))`. HARMFUL iff `D > m`; USEFUL iff `D < −m`; NEUTRAL otherwise (`m = 0.5`). `p_harm_keep = P(D > m)` and `p_harm_remove = P(D < −m)`. Uncalibrated scores are `h_keep` / `h_remove`. Fixed in the methodology report §3/§7 and proposed as D-35. |
| Streaming | Hard-coded allowlist of the 3 scenarios. Persistent download ledger with a 4.6 GB budget. Raw-size check < 3 GB. One scenario on disk at a time. Resumable through an extraction marker plus a cache-exists skip. Raw data deleted only after the cache is re-read. |
| Downloads | 0.837 + 1.593 + 1.830 = **4.26 GB** (ledger). Peak raw on disk 1.74 GB. Raw data deleted. Caches 142 MB. A 24-frame slice (140 MB) was kept for the online check. |

## 2. Geometry verification (404 frames)

- **D-24 self box: verified.** All 404 frames have exactly one GT box containing the receiver origin in BEV, with centre ≤ 0.51 m. The old 1.5 m proxy agrees in every frame, so the Stage-2 numbers that used the proxy are unchanged.
- **Receiver rays.** 64 rings in every sampled range image.
  - 85% of 7,317 non-self GT boxes have ≥ 3 receiver rays.
  - Support ratio of genuine objects: median 0.91 / 0.92 / 0.96 / 1.00 by range band (0–20, 20–40, 40–70, 70+ m).
- **Ground-contamination question.**
  - A synthetic test confirms the failure mode: an empty box at 9 m gets SUP > 0 from ground hits. `tests/test_e0_parts.py`.
  - On the data, empty synthetic boxes (3,232; 61% with ≥ 3 rays) have median support **0.07** (0–20 m) and 0.00 beyond, against the pre-registered limit of 0.20.
  - AUROC for genuine vs empty is 0.950 with the standard count and 0.948 ground-aware.
  - **A per-frame ground estimate is not required** for valid classification on OPV2V at this resolution (pre-registered rule). MINT-v0.0 uses the standard count.
  - The ground-aware classifier (receiver-only; 4.8% of upper-body GT points flagged as ground) stays available as an ablation.
- **Remaining geometry limitations.**
  - About 10% of empty boxes have support ≥ 0.6 in 0–20 m, in both variants. The likely cause is unlabelled structure in GT-free space, but this was not inspected.
  - Ground-aware counting *lowers* ADD separation slightly (0.819 → 0.783).
  - 15% of genuine objects and 39% of empty boxes are not ray-observable (fewer than 3 rays).
  - CARLA has no porous objects and no sensor noise model.

## 3. Clean-data effects (re-measured with the BEV self rule)

- **Effects.** 1,732 effects: 723 ADD (159 self, 168 KNOWN), 228 REMOVE (155 KNOWN), 781 SHIFT (550 KNOWN). These are identical to Stage 2.
- **Tile labels.** Over all tiles with any output change: 381 HARMFUL, 1,084 USEFUL.
  - **39% of HARMFUL tiles (149/381) have no extractable effect.** Their D ≈ 1: a box crossing the IoU-0.5 boundary under the SHIFT thresholds (0.3 m / 10°). MINT cannot act on them by construction.
- **Pilot separation, re-measured** (development, in-sample):
  - ADD AUROC 0.819 (13 harmful / 155 useful);
  - REMOVE 0.799 (69 / 86).
  - These are still preliminary: 13 harmful ADD cases.
- **Oracle headroom on clean data.** AP@0.7 0.8737 → 0.8799 (all-sender oracle); → 0.8766 (visibility-limited).

## 4. E0: attacks, attack loss and oracle headroom (AP@0.7 unless noted)

| Family (random placement) | Realized | Attack loss | Oracle (attacker) | **Vis-oracle (attacker), pre-registered** | Vis-oracle, attack-touched tiles only (post hoc) |
|---|---|---|---|---|---|
| spoof_feat (copy-paste feature) | 261/401 (103 at receiver-visible destination) | 0.041 | 0.88 | **0.21** | 0.16 |
| remove_feat | 42/400 | 0.011 | 0.40 | **0.32** | 0.11 |
| shift_feat (3.2 m) | 66/402 targets lost | 0.046 | 0.65 | **0.36** | 0.32 |
| spoof_pts (point copy) | 166/404 (70 visible) | 0.014 | 1.01 | **0.42** | 0.28 |
| **Mean** | | | | **0.326** (block bootstrap 95%: 0.20–0.49) | 0.216 |

- **Pre-registered decision: 0.326 ≥ 0.30, so proceed.** It is borderline: the interval includes values below 0.30.
- The pre-registered "attacker-unit" oracle also repairs the attacker's *benign* harm (recovery above 1 occurs). The cleaner post-hoc variant, which gates only tiles the attack changed, gives 0.22.
- **Physical ceiling.** Only 36–55% of the attacker's harmful tiles are receiver-observable (e.g. spoof_feat 203/538).
- **Attentive fusion resists removal.** Removing an object's features from the attacker rarely removes the detection (42/400), because the receiver usually sees the object itself. Loss for that family is small.

## 5. MINT-v0.0 (deterministic ray ratio, per-sender/per-tile gating, UNKNOWN = keep; uncalibrated)

**Online prototype.** `mint.reliability.pipeline.mint_v0_frame` was checked against the cache-based evaluation: identical boxes and gating on 24/24 frames.
- Latency on M1 CPU, 2 agents, p50: encode 0.46 s, plain decode 0.10 s, counterfactual 0.07 s, ray evidence 0.007 s.
- When gating fires, the final masked decode costs 0.18–0.28 s.
- **Overhead over plain AttFuse: +16% at p50** (budget 10%, D-17).
- The final decode is avoidable: exact composition of the already-computed decodes gives the same output.

**Clean, pre-registered θ = 0.**
- AP@0.7 0.8737 → 0.8691: relative loss **0.53%** (within 2%).
- AP@0.5 0.9437 → 0.9461 (+0.25%).

**Attacked, recovery of attack loss.**

| θ | Metric | spoof_feat | remove_feat | shift_feat | spoof_pts |
|---|---|---|---|---|---|
| **0 (pre-registered)** | AP@0.7 | 0.06 | −0.31 | 0.17 | −0.03 |
| **0 (pre-registered)** | AP@0.5 | 0.22 | 0.46 | 0.39 | 0.45 |
| 0.5 (sweep, in-sample; not a selection) | AP@0.7 | 0.16 | 0.11 | 0.17 | 0.27 |

At θ = 0.5 the clean AP@0.7 loss is 0.0%.

**Tile level (θ = 0).**
- About 50% of effectful tiles are KNOWN.
- AUROC of the raw score vs HARMFUL on KNOWN tiles: 0.77 (clean) to 0.88 (spoof_feat).
- Recall of KNOWN harmful tiles: 0.69–0.84. Precision: 0.37–0.59.
- **False rejection of useful tiles: 61–73 of about 950 (6.5%).**
- No tile without an effect was ever changed (by construction).

**Interpretation.**
- The evidence ranks harm reasonably well, but the θ = 0 rule gates too many tiles with small margins, especially SHIFT effects. That removes the sender's localization benefit: AP@0.5 improves while AP@0.7 does not.
- Even the best in-sample threshold reaches about half of the visibility-limited ceiling.

## 6. Exact next decision (needs you)

The pre-registered criterion is met only narrowly, and the first prototype captures little of it at AP@0.7. Options:

1. **(Recommended) One bounded rule revision, then calibrate.**
   - Change: a margin for SHIFT effects and type-specific thresholds, fixed on T by a pre-registered rule.
   - Data: stream the 4 small calibration scenarios (≈ 2.9 GB, D-31) to fit M4/Platt and choose θ out of sample.
   - Stop if calibrated recovery at AP@0.7 is < 0.15 on C, or the clean loss bound is > 2%.
2. **Re-scope as an observability study.**
   - Report the measured ceiling: 36–55% of attacker harm is receiver-observable; the oracle bound is 0.22–0.33.
   - Also report attentive fusion's natural removal resistance and the 39% effect-free harmful tiles.
   - No further downloads.
3. **Test a different signal first** (feature/attention fallback for blind tiles, or temporal) using the existing caches, which already hold per-tile attention shares. No download needed.

Nothing further was run after this report.
