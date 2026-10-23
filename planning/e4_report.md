# E4: held-out validation of frozen MINT (R1, dense counterfactual)

Run 2026-10-23.
- **Pre-registration:** [`runs/20261023-E4/preregistration.json`](../runs/20261023-E4/preregistration.json), committed in `f639c3a`. Frozen code is `0f6b3d0`. Both were committed before any block-H byte was downloaded.
- **Results:** [`e4_heldout.json`](../runs/20261023-E4/e4_heldout.json) (block H) and [`dev_blind/spoof_blind_dev.json`](../runs/20261023-E4/dev_blind/spoof_blind_dev.json) (development).
- **Code:** [`blind.py`](../src/mint/attacks/blind.py), [`e4_stream.py`](../runners/e4_stream.py), [`e4_analyze.py`](../runners/e4_analyze.py), [`test_e4.py`](../tests/test_e4.py).

**Scope.**
- **Block H data:** the 4 small validate scenarios (D-52): 371 frames, all with **n = 2**. Every block-H scenario has only 2 CAVs.
- **Download and safeguards:** 2.765e9 of the 3.2e9 bytes, checked before the first byte. One scenario was on disk at a time, and raw data was deleted after each cache was re-read. 39/39 compose checks were identical. No test scenario was touched.
- **Method:** R1, the attacks and the criteria are unchanged since the pre-registration commit.

## Outcome: success under the pre-registered criteria (held-out, block H)

Criteria use the 10-frame-block bootstrap, stratified by scenario: 39 blocks, 2000 resamples.

| Criterion | Point | 95% CI | Pass |
|---|---|---|---|
| (i) Mean ΔAP@0.7 over the 4 original families, CI low > 0 | +0.0223 | [+0.0172, +0.0274] | ✅ |
| (ii) Clean relative AP@0.7 loss, CI high ≤ 1% | 0.31% | [0.01%, 0.68%] | ✅ |
| (iii) No original family with point Δ < −0.002 | min −0.0009 (remove_feat) | — | ✅ |

**Coarse caveat (pre-registered as reported, not a criterion).** The whole-scenario bootstrap has 4 blocks.
- Its CI for (i) is [−0.0035, +0.0315], which includes 0.
- Its CI for (ii) is [−0.57%, +2.03%].
- So the result holds within these 4 scenarios. Between-scenario variation is not resolved by 4 scenarios.

## Held-out per-condition results (block H, AP@0.7 unless stated)

| Condition | Undefended | R1 | Δ (10-frame CI) | Δ scenario CI (coarse) | Attack loss | Recovery | ΔAP@0.5 |
|---|---|---|---|---|---|---|---|
| clean | 0.8618 | 0.8591 | −0.0026 [−0.0059, −0.0000] | [−0.016, +0.004] | — | — | −0.0013 |
| spoof_feat | 0.7740 | 0.8137 | +0.0397 [+0.029, +0.051] | [−0.001, +0.056] | 0.088 | 0.45 | +0.040 |
| remove_feat | 0.8274 | 0.8264 | −0.0009 [−0.006, +0.003] | [−0.015, +0.006] | 0.034 | −0.03 | +0.001 |
| shift_feat | 0.7726 | 0.8049 | +0.0323 [+0.024, +0.041] | [+0.009, +0.045] | 0.089 | 0.36 | +0.037 |
| spoof_pts | 0.8173 | 0.8356 | +0.0183 [+0.012, +0.025] | [−0.008, +0.025] | 0.044 | 0.41 | +0.020 |
| **spoof_blind** | 0.7643 | 0.7651 | +0.0009 [−0.003, +0.004] | [−0.011, +0.005] | **0.097** | **0.01** | +0.002 |

**Bounds and units (block H).**
- Oracle bounds (E0 definitions; recovery at AP@0.7; attacker-only oracle / visibility-limited attacker-only oracle):

  | Family | Oracle | Vis-limited oracle |
  |---|---|---|
  | spoof_feat | 0.87 | 0.55 |
  | remove_feat | 0.27 | 0.03 |
  | shift_feat | 0.62 | 0.47 |
  | spoof_pts | 0.94 | 0.51 |
  | spoof_blind | 0.88 | 0.05 |

- R1 attains 83% of the visibility-limited bound on spoof_feat, 77% on shift_feat and 80% on spoof_pts.

| Condition | Units KNOWN / UNKNOWN / self | Gated | Precision (D > 0.5) | False rejections of USEFUL units (ADD / REMOVE / SHIFT) | Attacker harmful units: KNOWN / gated |
|---|---|---|---|---|---|
| clean | 45% / 26% / 29% | 87 | 0.23 | 65 (6 / 59 / 0) | — |
| spoof_feat | 48% / 29% / 22% | 278 | 0.76 | 65 (6 / 59 / 0) | 214 / 191 of 352 |
| remove_feat | 46% / 25% / 29% | 97 | 0.28 | 65 (5 / 60 / 0) | 14 / 7 of 25 |
| shift_feat | 53% / 23% / 24% | 268 | 0.74 | 65 (6 / 59 / 0) | 213 / 179 of 255 |
| spoof_pts | 47% / 28% / 25% | 190 | 0.65 | 64 (6 / 58 / 0) | 117 / 105 of 194 |
| spoof_blind | 35% / 43% / 22% | 98 | 0.33 | 64 (6 / 58 / 0) | 21 / 12 of 389 |

- **spoof_blind behaves as designed.** 308/366 attacks were realized. 299 of these landed where the receiver has < 3 rays. R1 gated 2 of them.
- **Realization of the other families.** spoof_feat 248/370, of which 105 were blind by chance. spoof_pts 187/363. remove_feat 38/362. shift_feat 46/366.

**Cost (D-50: measured, no pass/fail).** All 371 block-H frames, n = 2, Apple M1, 8 threads, D-42 protocol.

| Mode | Overhead p50 / p95 | Isolated-encode overhead p50 / p95 | MINT extra p50 / p95 (s) | Tile fraction mean |
|---|---|---|---|---|
| Dense (frozen method) | 32% / 54% | 43% / 89% | 0.092 / 0.188 | 1.0 |
| T(0.05) (cost variant only) | 15% / 43% | 25% / 68% | 0.052 / 0.146 | 0.19 |

There is no block-H measurement for n ≥ 3, because block H has none. The n = 3–5 figures remain the E3 projections (development, not measurements).

## Development numbers (block T; in-sample; not held-out)

- **spoof_blind smoke test.** 24-frame dev slice × 4 seeds = 96 attacks.
  - 55 realized; 53 of them at < 3 rays; R1 gated 1.
  - Attack loss 0.041, R1 Δ −0.005, recovery −0.13.
  - It was developed here, not on the block-T caches as you asked: the caches have no features, so a new feature attack cannot be replayed from them (pre-registration → `deviation_from_request`).
  - Seeds repeat frames, so this is a smoke test, not an estimate.
- **E1/E2 block T (404 frames, n = 2–4).**
  - R1 Δ: +0.007 spoof_feat, +0.002 remove_feat, +0.008 shift_feat, +0.004 spoof_pts.
  - Clean Δ: +0.0003.
  - Recovery: 0.16–0.28.

## Interpretation

1. **The frozen method passes its pre-registered held-out check.** On the original families it recovers about a third of the attack loss: mean recovery 0.30 [0.23, 0.37]. remove_feat is the exception, at about 0, as on block T. The clean cost is 0.3% relative.
2. **Recovery is higher on H than on T** (0.36–0.45 vs 0.16–0.28). Two differences could explain it:
   - Block H has only n = 2, so attacks lose 2–3× more AP. On T, n = 2–4 diluted the attacks.
   - The 4 scenarios differ from T.

   E4 cannot separate these two causes. The held-out result covers n = 2 only.
3. **The known bypass is real and total.** A visibility-aware spoofer causes the largest loss of all families (0.097 AP@0.7), and R1 recovers 0.01 of it. Even the visibility-limited oracle reaches only 0.05. No receiver-ray method can close this gap. It bounds every claim: MINT defends the receiver's observable region only.
4. **The remaining clean cost comes from REMOVE.** 59 of 65 false rejections are REMOVE gates on USEFUL units, the same pattern as E2 Part C.
5. **Cost is far above D-17's 10%.** Dense costs 32% p50 / 54% p95 at n = 2 on this CPU. Under D-50 this is reported, not judged.

**Recommendation (per the pre-registered outcome rule).** Use the frozen method (MINT-v0 + R1, dense) for the one-time final test. That test is a separate decision, yours, and not part of E4. No rule changes.

## Appendix: proposals (not applied; also in `decision_log_proposed_appendix.md`)

| ID | Proposal |
|---|---|
| D-53 | Record the E4 outcome: success on block H (criteria (i)–(iii) pass under the 10-frame bootstrap). The coarse scenario bootstrap includes 0 for (i) and is reported next to it. Block H is now exposed (method-level outcomes seen) and cannot serve as a test set. |
| D-54 | In any final-test report, state the spoof_blind result (recovery ≈ 0 against the largest attack loss) as a scope limit next to the headline. Also state that the held-out evidence covers n = 2 only. |
| Open (yours) | Whether to run the one-time final test on the OPV2V test split with the frozen method and the E4 attack set (including spoof_blind). Whether its pre-registration should add an n-stratified analysis (test has n > 2). |
