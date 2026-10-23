# Pre-final-test audit (MINT / B-RAY, OPV2V)

2026-10-24. Independent review before the one-time final test (`runs/20261024-E5/preregistration_v2.json`, frozen code `5e06497`). No test scenario was opened, downloaded or referenced beyond its name in the frozen allowlist. No frozen file was changed (all 19 sha256 in v2 re-checked: identical). New code: `src/mint/audit/`, `runners/audit_*.py`, `tests/test_audit.py`. Smoke-test plan committed before any run: [`runs/20261024-AUDIT/plan.json`](../runs/20261024-AUDIT/plan.json) (`29f91ed`).

Labels used below: **T** = block T (3 validate scenarios, 404 frames, n = 2–4), development, in-sample. **H** = block H (4 validate scenarios, 371 frames, n = 2 only), development, exposed. **slice** = 24 frames of one block-T scenario (n = 2), smoke test only.

## 1. The method in plain English

**Setting.** Several cars drive together (OPV2V simulation). The *receiver* (the car we protect) runs a 3D car detector (AttFuse PointPillars, released checkpoint, CPU). Each other car (*sender*) turns its LiDAR scan into a feature map (a bird's-eye "image" of what it saw) and sends it. The receiver blends all feature maps pixel by pixel (attention) and decodes boxes. Because senders' points are projected into the receiver's frame before encoding (OpenCOOD `proj_first`, D-13b), the maps arrive aligned.

**Threat.** One sender (always sender 1) is malicious. It edits its feature map (or its points) so the receiver sees a fake car (*spoof*), loses a real car (*remove*) or sees a car in the wrong place (*shift*).

**What the receiver trusts.** Only its own LiDAR scan. Each laser return is a ray from the receiver's roof to a hit point. For a box that the receiver outputs, a ray crossing the box can (a) end inside it = *support* (something is there), (b) pass through and end behind it = *traversal* (the box is empty along that ray), or (c) end before it = *occluded* (no information). Rays that return nothing are never counted as "empty".

```
 sender 1..n-1 ──feature maps──┐
 receiver scan ─encode─────────┤
                               ▼
                    attention fusion ─► decode ─► boxes Y+   (no defense)
                               │
      ┌────────────────────────┼─────────────────────────────┐
      ▼                        ▼                             ▼
   B-RAY (primary)          R1 / MINT (key secondary)      ego-only
   for each box in Y+:      for each sender i: decode       drop all
   count receiver rays      without i (Y-(i)); compare      senders
   SUP / TRAV in the box    Y+ vs Y-(i) -> ADD/REMOVE/SHIFT
   drop iff KNOWN and       effects; test each effect box
   Wilson-95 upper bound    with receiver rays; gate sender
   of SUP/(SUP+TRAV) < 0.5  i in a 6.4 m tile if resolvably
                            harmful and nothing resolvably useful
   UNKNOWN (<3 rays, or the receiver's own box) = keep, in both
```

**"UNKNOWN = keep".** If the receiver's own rays cannot see a box (fewer than 3 informative rays, e.g. behind a truck or far away) or the box is the receiver itself, nothing is changed. The defense only acts where the receiver can check. Consequence: it cannot stop anything placed where the receiver is blind (measured by `spoof_blind`).

**What each method can do.** B-RAY can only *delete* boxes; it never adds a missing car or moves one back. R1 can also *undo a sender's contribution* in a tile, which in principle restores a removed car (by decoding without the attacker). Ego-only throws away all senders.

**Attacks (all random placement, one attacker, sender 1).** `spoof_feat`: copy the attacker's feature patch around a real car to a random empty spot. `remove_feat`: paste background over a real car's patch. `shift_feat`: remove, then paste the car one 3.2 m cell away. `spoof_pts`: copy the attacker's points on a real car to an empty spot and re-encode. `spoof_blind`: like `spoof_feat`, but only where the receiver has < 3 rays (worst case: the attacker knows the receiver's view). Not tested before this audit: optimized (PGD) feature attacks, destinations chosen to look consistent to the receiver's rays, colluding attackers, benign pose error and latency.

**Metrics.** AP@0.7 = OpenCOOD average precision for cars at 3D-box overlap ≥ 0.7 (a strict match). ΔAP = AP(method) − AP(no defense) on the same attacked frames. Attack loss = AP(clean, no defense) − AP(attacked, no defense). Recovery = ΔAP / attack loss (fraction of the damage undone). Clean loss = 1 − AP(method, clean)/AP(no defense, clean). Frames where the attack could not be placed, and all n = 1 frames, are scored as clean (they dilute ΔAP equally for all methods).

**Results so far (all development).**

| Data | Frames | B-RAY mean ΔAP@0.7 (4 families) | R1 | R1 − B-RAY | B-RAY clean loss | spoof_blind recovery (B-RAY / R1) |
|---|---|---|---|---|---|---|
| T (in-sample) | 404 | +0.0049 | +0.0052 | +0.0003 | 0.01% | not run on T |
| H (exposed) | 371 | +0.028 [0.023, 0.032] | +0.022 | −0.0056 | 0.09% | 0.03 / 0.01 |

Sources: `runs/20261024-E5/dev/e5a_dev.json`, `runs/20261024-E5/H/e5a_H.json` (10-frame-block CIs). On H, per family B-RAY: spoof_feat +0.049, shift_feat +0.039, spoof_pts +0.024, **remove_feat −0.0005**.

## 2. Code and protocol audit

PASS = correct as written. CONCERN = correct but limits what the result means, or fragile. FAIL = wrong or missing.

| # | Item | Verdict | Evidence |
|---|---|---|---|
| a1 | B-RAY uses no GT or attack ledger | PASS | Inputs are boxes, scores and the receiver scan only: `baselines.py:28-59`. Test-time counts come from the receiver's own `lidar_np` (float64): `e5_stream.py:85-90`. |
| a2 | R1 / KNOWN status / self-box use no GT | PASS | `r1.py:38-69`, `v0.py:60-68`; self-box is geometric (BEV footprint contains the sensor, 0.2 m margin): `rays.py:120-128`; `pipeline.py:229-305` takes no GT. |
| a3 | Evaluation keeps GT out of method outputs | PASS | `e5_analyze.py:90-112`: B-RAY/R1/ego-only are built from cached candidates/effects; GT enters only `frame_policies` oracles (bounds) and scoring. |
| a4 | spoof_blind uses the receiver scan + GT | PASS (attacker side) | `blind.py:40-77`. Allowed worst-case attacker knowledge; never a method input. |
| a5 | Purity test claimed in `harm_labels.py:2` ("tests/test_purity.py enforces it") | FAIL (missing file) → fixed | No such test existed. Added `tests/test_audit.py::test_inference_modules_do_not_import_gt_or_attack_code` and `..._have_no_gt_parameter` (pass; `effects.gt_match` is an offline helper used only by `stage2_validate.py:148`). |
| b1 | Which boxes B-RAY tests | CONCERN | Every final Y+ box, including boxes from the receiver's own data (`e5_stream.py:89-90`), at every n including n = 1. B-RAY is therefore also a single-agent CARLO-style filter; on clean H it drops 16 boxes, 9 of them GT-matched (`e5a_H.json` B-RAY_boxes). |
| b2 | Ray geometry | CONCERN | Core = box shrunk 15% (≥ 0.15 m) and vertically [bottom + 0.3, top − 0.1]; SUP if the return lies inside the box dilated by 0.2 m ± (0.05 + 0.01·range) (`rays.py:105-117, 156-163`). Ground hits inside the dilated footprint count as support (`ground.py:3-7`; the ground-aware variant exists but R1/B-RAY use `std`, `v0.py:25`). Vegetation, walls and poles inside an envelope also count as support. |
| b3 | Wilson formula and n_min | PASS / CONCERN | Formula correct (`r1.py:24-31`). But with the drop rule hi < 0.5 a box is droppable only with **≥ 4 rays and 0 support** (n = 4–7), or ≤ 1 support at n = 8 (checked numerically). One stray return keeps a fake box. |
| b4 | float16 scan | CONCERN (minor) | E5a-H B-RAY used the float16 cached scan (`e5_analyze.py:64-76`; E4 caches have no `yplus_rays`); the test uses float64. On T, counts identical on 1475/1504 boxes, verdict identical 1504/1504 (`e5a_dev.json` ray_count_check_dev). |
| b5 | n = 1 | PASS | B-RAY applied, MINT = no defense (`e5_analyze.py:92`); dry run with forced n = 1 ran end to end (`runs/20261024-E5/dryrun/dryrun.json`). |
| c1 | What attacks modify | CONCERN | Feature attacks copy a 3.2 m-aligned patch of the attacker's own maps at all three scales (`patches.py:43-48`, `e0_stream.py:173-212`); `spoof_pts` appends attacker points and re-encodes (`e0_stream.py:215-237`). None is optimized against the detector; none is the literature's standard PGD feature attack. |
| c2 | Realization | CONCERN (must be reported) | H: remove_feat realized 38/362 applied (10%), shift_feat 46/366 (13%), spoof_feat 248/370 (67%), spoof_pts 187/363 (52%), spoof_blind 308/366 (`e5a_H.json` realization). Not-applied frames are scored as clean (`e0_stream.py:315`, `e0_analyze.py:111-115`); applied-but-unrealized frames are scored as attacked but are effectively clean. All-frame ΔAP is therefore a diluted number. |
| c3 | Seeds | PASS | Per family/scenario/frame SHA-256 rng (`e0_stream.py:73-75`); OpenCOOD shuffle seeded per frame (`e5_stream.py:164`). |
| c4 | Same attack for all methods | PASS | All methods are computed from the same cached candidates of the same attacked features (`e5_analyze.py:90-112`). |
| d1 | AP order dependence | see §4 (X0) | `ap_from` integrates TP/FP in frame order without a global score sort (`e4_analyze.py:47-57`; OpenCOOD `calculate_ap(..., False)`). A box deleted in an early frame shifts precision for all later frames. Audit recomputed with a global sort. |
| d2 | Pooled AP, bootstrap | CONCERN | AP pooled over frames; scenario bootstrap with 15 clusters of very unequal size (1–5 agents, 1.33–4.6 mean). Percentile p = (k+1)/(B+1) (`e5_analyze.py:467-470`) is the bootstrap distribution's mass ≤ 0, not a null-calibrated test; with 15 clusters percentile intervals tend to under-cover. |
| d3 | Holm | PASS | `e5_analyze.py:473-483`: sorted p, thresholds α/2 then α, stop at first non-rejection. |
| d4 | Success rule = pre-registration | PASS | `e5_analyze.py:518-525` = v2 `success_criteria` (a) and (b). |
| d5 | Primary averages remove_feat | CONCERN | B-RAY only deletes boxes, so it cannot recover removals (H: −0.0005); including remove_feat dilutes the mean by ~¼ and hides that removal is undefended. |
| e1 | Allowlist | PASS | `e5_stream.py:48-63` (15 scenarios, `2021_08_23_12_58_19` excluded), test-archive id asserted (`:226`). |
| e2 | Budget | PASS / CONCERN | Pre-check before data (`:236-242`), per scenario (`:260`), after download (`:278`). Headroom is only 1.36e9 (22e9 − 20.64e9): an interrupted download is counted at full size, so a restart of any scenario > ~1.35 GB is refused. Safe, but may halt the test mid-way. |
| e3 | Frozen hashes | PASS / CONCERN | All 19 v2 hashes match. Not hashed in v2: `src/mint/model/attfuse_parts.py` (0e46d06d…), `opencood_shims.py` (0e645dd8…), `runners/stage1_spike.py` (d9ec82cc…), checkpoint `latest.pth` (f6df2f54…); OpenCOOD is an untracked directory at 31ba160 with no local diff. These produce every number. |
| e4 | Resume | PASS | Cached scenarios skipped; extraction reused only with its marker; raw deleted after the cache is re-read and compose checks pass (`:252-296`). |
| e5 | n = 1 / n = 5 | PASS / CONCERN | n = 1 tested (dry run). n = 5 (scenario `2021_08_22_07_52_02`) never run anywhere (T max n = 4): 16 decodes per condition, untested path. |
| e6 | Analysis completeness check | CONCERN | `e5_analyze.py:566` globs whatever caches exist; nothing asserts 15 scenarios / 2066 frames. |
| f | Pre-registration ↔ code | PASS | Primary = `mean_delta_orig|B-RAY` over ORIG (`e5_analyze.py:200`), scenario bootstrap seed 0, 2000 resamples; Holm; clean bound; paired statement (`:486-491`); strata with ≥ 5-scenario rule (`:348`). Every criterion is computed as written. |

## 3. Threat model and literature

Verified this session (title, authors, venue, year; settings from the paper text unless marked). "Notes" = the project's earlier close reading in `planning/literature/reading_notes/`.

| Work | Verified | What it does | Evaluation protocol | Relation to MINT / B-RAY |
|---|---|---|---|---|
| Tu et al., *Adversarial Attacks On Multi-Agent Communication*, ICCV 2021 (arXiv 2101.06560) | arXiv page + PDF text | White-box perturbation of a sender's intermediate message; transfer attacks | ε = 0.1 bound on δ, PGD via Adam (lr 0.1); 15 steps on ShapeNet, **1 step online** in V2V; AP@0.7; split by number of agents, one attacker; a multi-attacker section | The canonical "realistic" CP attack. Not in MINT's frozen set. |
| Li et al., *Among Us* (ROBOSAC), ICCV 2023 (arXiv 2303.09495) | search result quoting the paper + notes 09 | Sample sender subsets until the result agrees with ego-only (consensus) | V2X-Sim; PGD/BIM 15 iterations, step 0.1, magnitude Δ = 0.5; C&W 30 | Same family of with/without-sender reasoning as R1, but at subset level and against ego consensus. |
| Zhao et al., *Malicious Agent Detection for Robust Multi-Agent Collaborative Perception* (MADE), IROS 2024 (arXiv 2310.11901) | arXiv comments "Accepted by IROS 2024" | Per-agent hypothesis test: match loss (with vs without agent) + reconstruction loss, conformal p-values, BH | PGD ε ∈ {0.05, 0.1, 0.2}, 10 steps (V2X-Sim); ε ∈ {1.0, 1.5, 2.0}, 80 steps (DAIR-V2X) (notes 07) | Closest *counterfactual* prior art to R1; agent-level, calibrated. |
| Hu et al., *CP-Guard*, AAAI 2025 (arXiv 2412.12000) | arXiv comments "Accepted by AAAI'25" | Consensus-based malicious agent detection on BEV | PGD-type feature attacks on V2X-Sim (search snippet: 15 iterations; not re-read) | Agent-level; same attack family MINT lacks. |
| Zhang et al., *On Data Fabrication in Collaborative Vehicular Perception* (CAD), USENIX Security 2024 | notes 03 (full close read) | Attacks: ray-cast point fabrication (spoof/remove, occlusion-consistent from the attacker's view) and online masked PGD on features; defense: shared occupancy maps + free-space checks | Adv-OPV2V (300 spoof + 300 removal cases, 3–5 CAVs, target ≤ 30 m); CAD ~90% detection, removal TPR 38% | B-RAY is essentially CAD's *receiver-only* free-space check (CAD's "local-only" variant) applied to boxes. Adv-OPV2V is the closest standard benchmark on our data. |
| Sun et al., CARLO, USENIX Security 2020 | notes 01 (full close read) | Free-space / laser-penetration checks on single-vehicle boxes | KITTI, physical point spoofing | B-RAY's ratio is CARLO's LPD `g_B` with a Wilson margin. CAD showed occlusion-consistent fabrication defeats CARLO (§6.4.4). |
| Cao et al., *Adversarial Sensor Attack on LiDAR-based Perception in Autonomous Driving*, CCS 2019 (arXiv 1907.06826; pp. 2267–2281) | search (ACM/arXiv metadata) | Physical laser spoofing of the victim's own LiDAR | Spoofed obstacles in front of the victim | Breaks B-RAY's trust anchor: a spoofed return inside a fake box's envelope turns traversal into support. Out of scope only if stated. |
| Wang et al., *From Threat to Trust* (SOMBRA attack, LUCIA defense), USENIX Security 2025 | notes 05 | Attention hijacking on **AttFuse/OPV2V** for object removal; trust-scaled attention | OPV2V, single compromised vehicle, adaptive attacker | Same model and data as MINT; removal is exactly what B-RAY cannot undo. |
| Tao et al., *Learning Mutual View Information Graph for Adaptive Adversarial Collaborative Perception* (MVIG), CVPR 2026 per arXiv 2602.19596 comments | arXiv page | Adaptive attack choosing location/timing to evade consensus defenses | OPV2V and Adv-OPV2V; "reduces defense success rates by up to 62%" | Defense-aware placement: the same idea as `spoof_blind` / X2, optimized. |
| Xu et al., V2X-ViT, ECCV 2022 (arXiv 2203.10638) | PDF text §5 | Noisy setting: sender position/heading Gaussian σ = 0.2 m / 0.2°, 100 ms delay; sensitivity to 0.5 m / 1.0° | | Source of X3's benign noise levels. |

Preprints: MVIG (CVPR per comments, CVF listing seen in search), PoseGuard (arXiv 2605.01301), TrustFlip (2605.22122), GLST (2607.23059) remain preprints in the project's bib; not re-checked here.

**Does the novelty claim survive?** B-RAY alone: no. It is a receiver-only free-space check (CARLO's LPD; CAD's local occupancy check) with a Wilson margin; any claim must be "applying a known check to intermediate-fusion CP". The with/without-sender counterfactual (R1) is close to MADE/ROBOSAC at agent level; its tile-level, ray-gated form is the only plausibly new element (D-34 wording "to our knowledge" stays).

**Standard realistic benchmark we are missing.** PGD feature perturbation of one sender (Tu/ROBOSAC/MADE/CP-Guard), and CAD's Adv-OPV2V spoof/removal cases (ray-cast fabrication + online PGD). For AttFuse specifically, SOMBRA-style removal.

## 4. Holes and failure modes (ranked)

Audit results: [`X0_cache_checks.json`](../runs/20261024-AUDIT/X0_cache_checks.json), [`X0_global_sort_bootstrap.json`](../runs/20261024-AUDIT/X0_global_sort_bootstrap.json) (post-hoc addendum, [`plan_addendum.json`](../runs/20261024-AUDIT/plan_addendum.json)), [`X1_devslice.json`](../runs/20261024-AUDIT/X1_devslice.json), [`X2_devslice.json`](../runs/20261024-AUDIT/X2_devslice.json), [`X3_devslice.json`](../runs/20261024-AUDIT/X3_devslice.json). The audit code reproduces the frozen block-H numbers exactly (B-RAY +0.02789, p = 0.0005; R1 +0.02233, p = 0.055).

### 4.1 Key numbers

**Metric (X0, mean ΔAP@0.7 over 4 families; scenario-bootstrap 95% CI).** "Global" = detections ranked by score across all frames (standard VOC/KITTI-style AP); "frozen" = OpenCOOD `global_sort_detections = False`, which accumulates TP/FP in frame order.

| Block | AP | B-RAY | R1 | R1 − B-RAY | B-RAY clean loss |
|---|---|---|---|---|---|
| T (in-sample) | frozen | +0.0049 [0.0044, 0.0187] | +0.0052 [0.0043, 0.0136] | +0.0003 [−0.0051, 0.0003] | 0.01% |
| T | global | +0.0013 [0.0010, 0.0039] | +0.0044 [0.0032, 0.0082] | **+0.0032 [0.0022, 0.0043]** | 0.10% |
| H (exposed) | frozen | +0.0279 [0.0071, 0.0403] | +0.0223 [−0.0035, 0.0315] | −0.0056 [−0.0173, 0.0032] | 0.09% |
| H | global | +0.0056 [0.0024, 0.0082] | +0.0085 [0.0055, 0.0098] | **+0.0029 [0.0005, 0.0057]** | 0.18% |

Attack loss on H (no defense) also shrinks under global AP, e.g. spoof_feat 0.088 → 0.035 (`X0_cache_checks.json`). The frozen metric charges a low-score fake box at its position in frame order instead of at the tail of the ranking, which inflates both the damage of spoofs and the gain from deleting them. The 4-scenario CIs on H are coarse.

**PGD (X1, slice, 24 frames, n = 2; smoke test).** Recovery of AP@0.7 (frozen AP; global AP in brackets where it differs in meaning).

| Attack | Attack loss | B-RAY | R1 | Ego-only | Note |
|---|---|---|---|---|---|
| pgd_untargeted ε = 0.1 | 0.178 (global 0.026) | 0.07 | 0.06 | 0.00 | fakes mostly kept: 42 UNKNOWN vs 10 dropped |
| pgd_untargeted ε = 0.5 | 0.880 (AP → 0.001) | **0.00** | 0.02 | 0.80 | 7251 boxes, 62% UNKNOWN |
| pgd_remove ε = 0.1 | 0.018 | 0.00 | −0.63 | — | loss below the 0.05 bar |
| pgd_remove ε = 0.5 | 0.477 | **0.00** | **0.72** | 0.63 | only the counterfactual restores cars |

Budgets are the literature's absolute ε (Tu 0.1; ROBOSAC 0.5). For this model they are large relative to the coarse-scale features (mean |δ|/mean |feature| = 14× at ε = 0.1 and 105× at ε = 0.5 for the untargeted attack), so a feature-statistics check would see them. B-RAY does not look at features.

**Ray-consistent spoof (X2).** Slice: a destination where the fake box is KNOWN and kept by B-RAY was found in 24/24 frames, but only 6 spoofs produced a box; B-RAY kept 5/6 (all-frame loss 0.0198, just under the 0.02 bar; realized-only loss 0.055, B-RAY recovery 0.11). Caches: B-RAY keeps **15.1% of KNOWN empty synthetic boxes** on T (296/1963) → plan criterion met (≥ 10%). Of realized random spoofs on H, B-RAY drops 136/257 (spoof_feat) and 104/187 (spoof_pts); 42% / 41% are UNKNOWN. Several chosen destinations had exactly 3 traversing rays, which B-RAY cannot drop (§2 b3).

**Pose / latency (X3, slice, clean).** σ = 0.2 m / 0.2°: B-RAY drops 0 boxes; 100 ms delay: 0; both: 0; σ = 0.5 m / 1.0°: 3 drops (1 GT-matched), ΔAP +0.011. Not a hole for B-RAY at these settings (24 frames). Benign noise itself costs up to 0.11 AP@0.7 (pose + async), which no method recovers.

**Realized-only (H, frozen AP).** spoof_feat: loss 0.112, B-RAY +0.060, R1 +0.050. shift_feat: loss 0.153, B-RAY +0.011 (7%). remove_feat: loss 0.086, B-RAY −0.002, R1 +0.001. spoof_blind: loss 0.113, B-RAY +0.003.

### 4.2 Ranked table

| # | Hole | Why it matters for AP@0.7 under real attacks | Evidence | Severity | Smallest resolving check |
|---|---|---|---|---|---|
| 1 | **Primary-method selection depends on the AP definition** | D-57 chose B-RAY because R1 − B-RAY < 0 on H. Under global-sort AP, R1 − B-RAY > 0 on T and H with CIs excluding 0, and B-RAY's gain is 5× smaller | §4.1 table | **Blocks the test as framed** (the headline would be metric-dependent) | Pre-register global-sort AP for every primary/key-secondary statistic and a reporting rule (§5) |
| 2 | **Optimized feature attacks not in the test** | The literature's standard attack. B-RAY recovers 0 under every PGD variant; under removal PGD R1 recovers 72% and B-RAY 0 | X1 | **Must be reported**; add as secondary | Freeze PGD families on T/H (needs features: re-stream, see §5) |
| 3 | **Removal is undefended by the primary** | B-RAY only deletes. remove_feat realized-only loss 0.086, B-RAY −0.002; pgd_remove 0.48, B-RAY 0. The primary's mean includes remove_feat at ≈ 0, hiding this | X0, X1, `baselines.py:45-59` | Must be reported | Per-family and mean-of-3 reporting (no new run) |
| 4 | **Ray-consistent and low-ray spoofs** | Wilson rule drops only boxes with 0 support and ≥ 4 rays (n ≤ 7); 15% of KNOWN empty boxes are kept; ground/vegetation/walls inside the envelope count as support | X2, §2 b2–b3 | Must be reported | Optimized destination search on T caches (null boxes) is enough to state the rate |
| 5 | **Visibility-aware (defense-aware) attacker** | spoof_blind: loss 0.097–0.113, recovery ≤ 0.03 for every method; MVIG (CVPR 2026) optimizes placement against consensus defenses | `e5a_H.json`, X0 | Must be reported (D-54 already) | — |
| 6 | **Realization dilution and unrealized frames scored as clean** | remove/shift realize in 10–13% of frames; all-frame ΔAP is ~¼–⅛ of the realized effect; n = 1 frames dilute too (≈ 2/3 of one test scenario) | §2 c2 | Must be reported | Realized-only table (computable from the frozen caches) |
| 7 | Selection bias | B-RAY was chosen on H after H's attacks were seen; attacks were designed by the same team; H is exposed | D-57/D-58 | Must be reported | Only a new attack family frozen before the test helps |
| 8 | Receiver sensor spoofing (Cao et al. CCS 2019) | B-RAY's only trusted evidence is the receiver scan; a few injected returns turn traversal into support | literature | Scope limit | — |
| 9 | Collusion / multiple attackers | Attacker fixed to sender 1; two attackers can corroborate; R1's per-sender counterfactual cannot see a fake both send | `e4_stream.py` frame_record (attacker = 1) | Scope limit | — |
| 10 | Real-sensor effects | Glass, dark cars, rain return nothing (not counted as free, D-06) → more UNKNOWN; vegetation/spray give false support. CARLA LiDAR has none of these | design | Scope limit | — |
| 11 | B-RAY does not assess features or identify the sender | It cannot attribute, warn or exclude a sender; fakes in UNKNOWN regions persist every frame | `baselines.py` | Scope limit | — |
| 12 | Pose error / latency | Not a hole for B-RAY at standard settings (0 drops); large noise drops 1 true box | X3 | Minor (report) | — |
| 13 | Runner fragility | Budget headroom 1.36e9 (restart refusal), no 15-scenario/2066-frame assertion, n = 5 path never run, model code/checkpoint not hashed | §2 e2–e6 | Minor (procedural) | Manual pre-run and post-run checks in v3 |

## 5. Recommendation

**GO-WITH-CHANGES.** The frozen code is correct and leak-free as far as this audit can tell (§2: no FAIL in the method or runner code; the one FAIL is a missing test, now added). But the v2 headline would be fragile on two counts the final test cannot fix afterwards: (1) the B-RAY-over-R1 choice reverses under the standard global-sort AP, and B-RAY's gain shrinks 5×; (2) against the literature's standard optimized attack B-RAY recovers nothing, and it cannot recover removals at all. Running v2 unchanged would likely "succeed" on a number that a reviewer can overturn by changing one AP flag.

**Proposed preregistration_v3 (minimal diff; not written until you approve).**

1. **Primary unchanged** (B-RAY, frozen non-global AP, Holm co-test with R1, clean bound). Rationale: changing the primary after H again would be a second post-hoc selection.
2. **Pre-registered robustness of the headline:** compute every primary and key-secondary statistic also with global-sort AP (same bootstrap, seed, Holm). **Reporting rule fixed now:** the headline may be called robust only if B-RAY is Holm-rejected under both AP definitions; if the two disagree, the report states the result is AP-definition-dependent. The R1 − B-RAY statement is given under both, side by side. (Analysis-only; needs a new analysis file, no change to frozen code.)
3. **Per-family, mean-of-3 (excluding remove_feat) and realized-only tables** as pre-registered secondary outputs, computed from the same caches.
4. **Secondary attack families (optional, costs time):** `pgd_untargeted ε = 0.1` and `pgd_remove ε = 0.5` (definitions in `plan.json` X1). Expected outcomes, stated before any test run: B-RAY recovery ≈ 0 on both; R1 recovery on pgd_remove substantially > 0. **Caveat:** they are developed only on 24 frames. Freezing them on T/H needs features, which the caches do not hold: re-streaming block H (2.77 GB) is the smallest meaningful development set. Adds roughly 3–5 h to the ~8 h test run. If you do not want the re-stream, report X1 as a development smoke test and list PGD as an untested threat.
5. **Pose/latency:** report X3 as development evidence and a scope note; do not add test conditions.
6. **Procedural:** before streaming, record sha256 of `attfuse_parts.py`, `opencood_shims.py`, `stage1_spike.py`, `latest.pth` and OpenCOOD 31ba160 (values in §2 e3) and re-check them after; after analysis, check 15 scenarios / 2066 frames; if a download is interrupted, stop and ask (budget headroom 1.36e9).

**Scope limits to state in the final report regardless:** single attacker (sender 1), random placement; spoof_blind bypass (known); ray-consistent / low-ray spoofs (15% of KNOWN empty boxes kept on T); B-RAY cannot restore removed objects; no optimized attack unless (4) is adopted; receiver's own sensor trusted (no physical spoofing); CARLA LiDAR (no glass, rain, dark-paint dropouts); n ≥ 4 covered by ~2 scenarios; method chosen on exposed block H; AP@0.7 uses OpenCOOD's frame-order AP (and global-sort if (2) is adopted).

