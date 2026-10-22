# PosePert attack and PoseGuard defense: Zhang, Zhang, Mao, arXiv 2605.01301 v2 (Sep 2026)

- **Citation.** `zhang2026poseguard`.
- **Access.** FULL-CLOSE on §2 (related work: defense taxonomy), §3 (limitations of existing attacks), the threat model, §5.3 (PoseGuard) and §6.1 (setup). Results tables skimmed. Read 2026-10-22. A preprint; peer-review status unknown.

## Question, unit, inputs
- **Question.** Can small, sub-threshold pose perturbations of existing objects in intermediate-fusion CP cause unsafe driving downstream (tracking, prediction, planning) while evading defenses?
- **Defense unit.** One **safety-critical detected object**.
- **Defense inputs.** Fused detections, ego-only detections, each agent's spatial feature map cropped to the box.

## Threat model
- Insider with white-box perception model and no downstream access.
- Heterogeneous models via transfer.
- No same-frame data from others.
- Per-frame budget under 50 ms.

## Attack (PosePert)
- PertNet plus ray casting plus scaling, applied to the attacker's own data so that an existing object appears shifted 0.5–2.0 m (±10°).
- Online scenario-aware planning (move-in → phantom braking; move-out → collision risk).
- Reported: 75–94% single-frame success (IoU > 0.5 shift). Existing defenses detect under 13%.

## Defense (§5.3.2)
1. Select safety-critical objects (trajectory near the ego path).
2. **Fused-vs-ego disagreement filter**: if the fused and ego-only boxes agree (IoU and centre distance), skip.
3. For disagreeing objects:
   - crop each agent's feature map to the box;
   - L2-normalise;
   - pairwise L1 between agents (LUCIA's metric applied locally);
   - flag if above the 95th percentile of clean cases.
- Reported 58–84% detection at 5% FPR.

## Key quantitative insight (§5.3.1)
- A feature map has about 140,000 locations. A pose perturbation touches about 400 voxels (under 0.3%).
- Global L1 signal-to-noise is about 1.0×. Box cropping gives 3–9×.
- The LUCIA trust score moves only 0.509 → 0.494 under attack.
- **This directly motivates a spatially resolved unit.**

## Our explanation
PoseGuard is the closest prior work to "per-object feature-region reliability". Differences from MINT:
- **Detection only.** A flag, no fusion change and no harm estimand.
- **Fused-vs-ego gate.** Only objects the ego also sees are checked; others are *skipped*. Honest unique views are unscored rather than explicitly unknown, and unique-view fabrications pass.
- **Threshold.** The 95th percentile of clean cases, which is not a calibrated probability.
- **Peer dependence.** Pairwise L1 across all agents assumes most peers agree.

## Code
- Not checked.

## What transfers
- The per-object crop-residual feature as an evidence channel, `e_resid` in M5.
- Pose-perturbation attacks as family A-F5 / A-R3.
- Safety-critical stratification as a secondary analysis.

## Experiment
Implement `B-PoseGuard` (crop L1, 95th-percentile threshold) as a baseline at the object level. Map its flags to tiles by box centre. Compare at matched FPR on H1. Report the fraction of harmful contributions it skips because fused and ego agree, or because the object is unseen by the ego.
