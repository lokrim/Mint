# Data fabrication attacks and CAD: Zhang, Jin, Zhu, Sun, Zhang, Chen, Mao, USENIX Security 2024

- **Citation.** `zhang2024cad`. URL: https://www.usenix.org/system/files/usenixsecurity24-zhang-qingzhao.pdf
- **Access.** FULL-CLOSE: §3 (problem, threat model, constraints, pp. 6311–6312), §4.3 (intermediate-fusion attack, p. 6314), §5 (CAD, pp. 6314–6316), §6.1–6.2, §6.4 (defense evaluation and overhead, pp. 6320–6321). Attack §4.2 skimmed. Read 2026-10-22.

## Question, unit, inputs
- **Question.** Can an insider vehicle spoof or remove targeted objects in early- or intermediate-fusion CP, in real time and stealthily? Can benign vehicles detect it collaboratively?
- **Defense unit.** Regions of 2D space (polygons) and predicted boxes. The decision is region alerts, not agent eviction.
- **Defense inputs.**
  - Each vehicle's own occupancy map (free / occupied / unknown polygons) plus per-object motion.
  - Broadcast maps from others (about 10 KB each).
  - The fused perception result.

## Threat model (§3.2–3.3)
- An insider controls at least one CAV: sensors, software, transmitted data. White-box model access.
- At least one benign vehicle exists. No physical sensor or GPS spoofing. Crypto is not broken.
- **Constraints the attacker must respect:**
  - realistic point density and occlusion (to evade CARLO);
  - features within normal value ranges;
  - targeted region;
  - no same-frame victim data;
  - real-time (T − 2t_T).
- These constraints are a useful template for our T1/T2 realism rules.

## Attacks
- **Early fusion: black-box ray casting (§4.2).** Fake object meshes are rendered with the attacker's LiDAR ray geometry: points occluded by the fake are removed, and points on the fake surface are added. The "Sampled-RC" variant limits density.
- **Intermediate fusion (§4.3).** Online PGD on the attacker's feature map:
  - one iteration per frame, reusing the perturbation;
  - initialized by a ray-cast spoof (black-box init);
  - masked to the target region (5 m × 5 m);
  - values clipped to clean ranges;
  - loss eq. 4: `l_spoof = Σ IoU(z', z_t)·log(1 − σ(z'))`, `l_remove = −Σ IoU·log(1 − σ)`.
- **Datasets.**
  - Adv-OPV2V: 300 spoof + 300 removal scenarios, 10 frames, 3–5 CAVs, target within 30 m of the victim.
  - Adv-MCity: 8 real scenarios, 3 Lincoln MKZs with VLP-32C.

## Defense equations (§5.4)
- Conflicts: `ε_occ = ∪_{i,j} S_O^(i) ∩ S_F^(j)` (eq. 5). Area threshold σ_occ.
- Merged map (eq. 6): the ego map is always trusted; others are added minus conflicts.
- **Perception–occupancy checks (eq. 7):**
  - `ε_spoof = ∪_y (y ∩ S'_F)`: predicted boxes in free space.
  - `ε_remove = ∪ (s'_O − Y)`: occupied regions without boxes.
  - Thresholds σ_spoof and σ_remove are swept through ROC.
- **Free space construction (§5.3).** HD-map road filter, RANSAC ground removal, density clustering. For each angular sector from the sensor, the region up to the nearest non-ground point is free. Beyond 50 m is unknown.

## Our explanation
- CAD is the closest *cooperative* version of the ray idea. It reduces each agent's rays to a 2D free polygon (first non-ground hit per sector) and checks fused boxes against it.
- It relies on the ego map being trusted plus "at least one benign observer of the region". Adaptive attackers fake their own map consistently.
- The free-region rule assumes on-road obstacles always leave above-ground points when observable.

## Results and limitations (as reported)
- About 90% of their attacks detected.
- FPR < 3%; TPR > 80% (spoof) / 38% (removal). Low removal TPR is attributed to benign faults outside map range.
- Pedestrians and cyclists have much worse FPR/TPR (§6.4.2).
- §5.5: detection requires a benign observer of the attacked region (otherwise no conflict). Detection does not resolve or attribute the anomaly.
- "False alarms" are counted when predicted boxes have IoU < 0.5 with GT. So the target mixes attacks and benign perception faults (§6.4.1). **This is closer to our harm target than to intent detection.**

## Compute and communication
- Map about 10 KB, transmission about 10 ms.
- Consistency checks about 15 ms. End-to-end about 92 ms (in-vehicle ROS setup).
- Segmentation and clustering are the expensive part.

## Code, data, licence
- github.com/zqzqz/AdvCollaborativePerception, Apache-2.0, pushed 2025-10-19.
- The setup script downloads models, data and the OPV2V test set from Google Drive. More than 40 GB of free space is required.
- PyTorch 1.9.1 / CUDA 10.2 by default.
- **Not run.**

## What transfers to MINT
- The threat-model realism constraints.
- The ray-cast spoofing attack (A-R2 in our protocol) and the masked online PGD feature attack (A-F1).
- The perception–occupancy rules as a baseline (`B-CAD-local`): using only the receiver's own occupancy is CAD's lower-bound variant (they quote TPR 71.7%/24.0% etc. for local-only).
- Region-level alerts.

## What does not transfer
- **Polygon free space from first non-ground hit.** This ignores object height and overhangs.
- **The HD map dependency.** No HD map is shipped with Mixed Signals [U].
- **Binary alerts.** Not a calibrated probability of harm.
- **Box-level output.** It does not modify the fusion.
- Setting C (sender-shared maps) is extra communication and is forgeable.

## Experiment to test transfer
Implement `B-CAD-local` (receiver-only occupancy, eq. 7 rules) on the same frozen detector. Compare against MINT M3/M5 on H1/H2 within receiver-observed tiles. Optionally add setting-C shared maps as an ablation with honest and forged maps.
