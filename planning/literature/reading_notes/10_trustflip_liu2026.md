# TrustFlip attack and TrustReflect mitigation: Liu, Wang, Li, Zhang, arXiv 2605.22122 v2 (28 Aug 2026)

- **Citation.** `liu2026trustflip`.
- **Access.** FULL-SKIM: abstract, introduction, threat model (§III), design outline (§IV) and TrustReflect (§IV-F). Results skimmed. Read 2026-10-22.

## Question
Can consistency- and trust-based CP defenses be weaponized to evict *benign* vehicles?

## Attack
- A **physical adversarial object**, optimised as a mesh with physically biased shape priors (attached to a car or standalone). It is perceived differently from different viewpoints.
- The defense attributes the cross-view inconsistency to the targeted benign vehicle, so its trust drops and it is down-weighted or excluded.
- Passive and persistent: no digital intrusion at runtime.
- Evaluated on OPV2V and V2X-Real, four CP backbones and four defenses:
  - victim flagged or suppressed in up to 87.76% of scenarios;
  - AP reduced by up to 6.0 points.
- Real-world fabricated prototypes.

## TrustReflect (mitigation)
- Each benign vehicle re-runs the defense on its own view. Where it would itself look malicious, it marks the region **uncertain** in a per-frame trust mask sent alongside its data.
- Consumers exclude masked regions from trust computation and fusion.
- Reported 35–100% reduction in attack success.
- Limitations noted in the search summary and partly in the text:
  - it cannot separate benign from malicious uncertainty;
  - a compromised agent can mask its own manipulated region to avoid penalty.

## Relevance to MINT
- **Primary motivation for dropping global sender reputation** (LT-03 in findings).
- MINT's per-tile unit limits blast radius: an inconsistency poisons only the tiles where it occurs, not the sender's other tiles.
- Physically induced viewpoint-dependent disagreement is a **benign-but-adversarial** case. Lower `r` there is not evidence of malice, which is why intent is a non-goal.
- TrustReflect's sender-supplied uncertainty mask is setting-C evidence (forgeable). It is not adopted.

## Experiment
Not reproducible without their meshes. Approximate with a benign stress B-11: viewpoint-dependent object (a porous or thin object visible only to some agents). Check that MINT's tile scores for the *honest* sender's other tiles are unchanged: the blast-radius test in the [evaluation protocol](../../evaluation_protocol.md) §7.
