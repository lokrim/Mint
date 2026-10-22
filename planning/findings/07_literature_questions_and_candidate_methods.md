# 07 — Literature questions and candidate methods

Revision 2 (2026-10-22). This is a research agenda, not a review, a novelty judgement or a method choice.

## The colleague's lead (LT-01, hypothesis)

An informal suggestion from the user's colleague; no author or paper is attached. The idea:
- LiDAR returns compatible with a proposed object **support** it;
- a measured ray that passes through an allegedly occupied part of the proposal and ends behind it **contradicts** it, under stated assumptions.

What it is not:
- It is not support vector machines.
- It does not assume boxes are solid; rays may cross empty parts of a box.
- It does not treat a missing return as free space.
- It is not available from latent tensors alone.

**Revision-2 observation relevant to this idea.** The organized PCD grids with origin-placed placeholder slots ([03 §5](03_dataset_ground_truth_and_feature_feasibility.md)) *might* identify per-beam no-return events and confirm sensor origins. If validated, this lets a receiver reason over its *own* raw scan, including where it got no return. It does not help a feature-only receiver. Prior art already covers ray/occlusion-based checks: CARLO (Sun et al. 2020) and the occupancy-based CAD (Zhang et al. 2024) are listed below. Novelty therefore has to be established, not assumed.

## Candidate families (hypotheses, none selected)

| Family | Specific question | Required observable inputs | Independent-trust assumption | Likely blind spots | Compute bottleneck | Evidence to retain / reject |
|---|---|---|---|---|---|---|
| Support/traversal counts | Do receiver-observed returns and pass-through rays separate fabricated from real object hypotheses while keeping unique true objects? | Object hypothesis (from fused features) with an occupied-region model; receiver's own endpoints; validated 3D origin; beam index/no-return mask; time alignment | Receiver scan is uncompromised; sender rays are not trusted | Box interiors; porous/thin objects; glass; occlusion; sparse far range; motion during scan; asynchronous sensors | Ray–region intersection per beam: ~65k–262k beams per scan, needs spatial indexing | GT false-proposal vs true-unique-object curves on grouped sessions. Reject as core if receiver coverage of attacked regions is small, or if benign conflicts dominate. |
| Visibility-aware occupancy consistency (baseline; cf. CAD) | Do free/occupied/unknown maps catch task-relevant contradictions? | Origin, rays or trusted occupancy, explicit unknown | Comparator map independent of the attacked sender | Shared occlusion; coarse cells; dynamic objects; colluding senders | Ray integration into a sparse grid or octree | Compare to traversal at matched resolution and budget. Retain only if calibrated and useful downstream. |
| Temporal or cross-view feature residuals (cf. Latent Guardian/Cerberus) | Does a local feature inconsistency predict a harmful contribution rather than ordinary novelty? | Exact feature layer; warping by pose/time; overlap/visibility mask | Trusted ego encoder and pose | Unique views; semantic shift; attacker adapting to the check; contaminated history | Warp + local similarity per cell | Residual vs GT-measured harm, stratified by corroboration. Reject if it mainly tracks overlap or novelty. |
| Simple statistical / evidential combination | Do interpretable support/conflict/uncertainty counts give useful selective risk? | Validated evidence channels with units | Channel dependence modeled | Correlated rays; misspecified likelihoods; small calibration sets | Cheap; dominated by upstream evidence | Risk–coverage vs logistic baseline; uncertainty preserved when support is absent. |
| Small learned combiner | Does supervised nonlinear combination beat the simple baselines within budget? | Same deployable evidence; grouped GT labels | No hidden evaluator features; representative sessions | Shortcuts (sender ID, site); unseen attacks; overconfidence | Training sweeps; tiny inference | Group-held-out gains, ablations, ID-leak test; reject if gains vanish across sessions. |

## Verified primary-source leads (checked 2026-10-22, abstract/landing page only, none read in full)

| Lead | What was verified | Questions for full reading |
|---|---|---|
| [Mixed Signals dataset paper, Luo et al., arXiv 2502.14156](https://arxiv.org/abs/2502.14156) | Title/authors; 3 vehicles + dual-LiDAR RSU; 45.1k clouds, 240.6k boxes, 10 classes | Sensor models, beam layout, no-return encoding, calibration, sessions, baselines |
| [HF card, sberrio/Mixed-Signals-V2X](https://huggingface.co/datasets/sberrio/Mixed-Signals-V2X) (current revision) | CC BY-NC-SA 4.0; TXT labels `cls cx cy cz dx dy dz yaw` in top frame; ±51.2 m; >5 points; empty file = no objects; 29/4/4 split | Compare with pinned revision `1a61aea…`; is there a checkpoint? |
| [OPV2V, Xu et al., ICRA 2022, arXiv 2109.07644](https://arxiv.org/abs/2109.07644) | Early/late/intermediate fusion benchmark; attentive intermediate fusion | Exact tensor and fusion boundary; code/weights today |
| [Where2comm, Hu et al., NeurIPS 2022, arXiv 2209.12836](https://arxiv.org/abs/2209.12836) | Spatial confidence maps for selective sharing | Is confidence calibrated correctness or a selection heuristic? Behaviour under adversarial senders? |
| [Adversarial Attacks on Multi-Agent Communication, Tu et al., ICCV 2021, arXiv 2101.06560](https://arxiv.org/abs/2101.06560) | Attacks on shared intermediate representations | Attacker knowledge, transferability, feature-space threat model |
| [On Data Fabrication in Collaborative Vehicular Perception (CAD), Zhang et al., USENIX Security 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/zhang-qingzhao); [arXiv 2309.12955](https://arxiv.org/abs/2309.12955) | Fabrication attacks; anomaly detection with abstract-reported 91.5% detection at 3% FPR in simulation. **Occupancy-map details come from a search summary only, not verified from the paper.** | Free/occupied/unknown construction; independence; timing |
| [Towards Robust LiDAR-based Perception (CARLO/SVF), Sun et al., USENIX Security 2020](https://www.usenix.org/conference/usenixsecurity20/presentation/sun) | Occlusion patterns used as physical invariants against spoofing | Exact free-space/ray test; overlap with the colleague's idea |
| [The Latent Guardian (Cerberus), Zhang et al., ICML 2026, PMLR v306](https://proceedings.mlr.press/v306/zhang26cs.html) | Feature-level consistency checks (topology, semantic direction, energy) | Unit, threat model, unique-view treatment, cost; do not adopt reported numbers |
| [Adversarial Trust Poisoning (TrustFlip), Liu et al., arXiv 2605.22122](https://arxiv.org/abs/2605.22122) | Physical objects make benign vehicles appear inconsistent, so consistency/trust defenses evict them (LT-03) | Direct evidence that sender-level trust can be weaponized; their "uncertain disputed regions" mitigation |
| [Conformal prediction tutorial, Angelopoulos & Bates, arXiv 2107.07511](https://arxiv.org/abs/2107.07511) | Verified in revision 1 only; not re-checked in revision 2 | Exchangeability under correlated frames; group-conditional calibration |
| [OctoMap project](https://octomap.github.io/) | Verified in revision 1 only; not re-checked in revision 2 | Inverse sensor model; unknown versus free; dynamic scenes |

## Search strings

- `cooperative perception intermediate fusion feature reliability adversarial message`
- `collaborative perception Byzantine feature attack defense spatial`
- `LiDAR spoofing occlusion free space ray consistency defense`
- `collaborative perception occupancy map consistency fabricated object`
- `organized point cloud no-return beam mask range image invalid pixels`
- `selective prediction risk coverage object detection calibration spatial`
- `conformal prediction dependent data group conditional`
- `temporal consistency collaborative perception pose error latency`
- `sparse ray casting GPU edge efficient occupancy`
- `Mixed Signals V2X baseline checkpoint heterogeneous LiDAR`

For each paper, record: version read; sections read; unit and target; runtime inputs; independence assumptions; GT role; splits; attack realism; unknown handling; cost; official code and weights checked on a date. Finish with a gap matrix and a minimal falsification experiment.
