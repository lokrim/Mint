# MINT methodology research report (bounded research phase)

Written 2026-10-23. **Research and design only: no code changed, nothing trained, nothing downloaded, `planning/findings/` untouched, `decision_log.md` untouched.** Proposed decision entries are in [decision_log_proposed_appendix.md](decision_log_proposed_appendix.md).

How to read evidence tags in this report:
- **[repo]**: read from this repository's code, runs or planning files in this session.
- **[web-checked]**: the title, authors, venue/status and mechanism were re-read from the paper's arXiv/proceedings page (abstract level) this session.
- **[notes]**: taken from this project's earlier close-reading notes in `planning/literature/reading_notes/` (full-text reads on 2026-10-22). Not re-read today, but consistent with what was re-checked.
- **[recalled]**: classical references cited from memory (not re-fetched); verify before citing in a paper.
- A finding with no tag is my inference.

---

## 1. Executive summary (plain English)

**What MINT is trying to do.** When several cars share intermediate neural-network features, one car may send harmful ones (fake objects, erased objects, shifted objects). MINT tries to estimate, for each *sender × map tile × moment*, how likely it is that keeping that sender's contribution makes detection worse than leaving it out. If the answer is "probably harmful", drop it in that tile only. If we cannot tell, keep it.

**What the repository already proves** [repo]:
- The released AttFuse checkpoint reproduces OPV2V (AP@0.7 0.8155 vs 0.815) on CPU.
- Removing one sender from one tile changes results only inside that tile (93/93 bit-identical tests). So the "with vs without this sender" comparison is exact and cheap.
- A receiver's own LiDAR rays can check a claimed object: on 3 development scenarios the support ratio ranks harmful vs useful effects with AUROC 0.82 (added objects, only 13 harmful cases) and 0.80 (removed objects).
- **The hard limit**: only 30% of *useful* added objects, and 13 of 39 (33%) of the *harmful* added objects, are visible to the receiver's rays. Physical evidence alone can never judge the other two-thirds.

**Main conclusions of this review.**
1. **The core idea survives, but it must be sold as what it is.** Counterfactual "with vs without sender" tests are prior art at sender level (MADE, CP-Guard: [notes]/[web-checked]). Free-space/ray checks are prior art for objects (CARLO, Shadow-Catcher, CAD). Beta-binomial trust with a visibility gate is prior art in late-fusion tracking (MATE). What I could not find is the *combination* at this resolution: intermediate-fusion, per-sender-per-tile, receiver-own-ray evidence, calibrated to a ground-truth harm label, with an explicit unknown state. That statement is search-limited.
2. **Reduce the problem to one question.** Every counterfactual effect (ADD, REMOVE, SHIFT) is a claim about whether a box is *real*. One existence-probability per effect box, plus the effect type, determines both the harm probability of keeping and the harm probability of removing. This is why "removal can itself be harmful" falls out naturally (§3).
3. **Cross-agent corroboration is mostly redundant in the tiles that matter.** With softmax-attention fusion, an effect appears only when a sender is the *deciding* source. A box supported by two senders mostly survives removing one of them, so it is not an effect. Corroboration only adds a soft signal in ≥3-agent frames and is exposed to collusion. Defer it.
4. **Temporal behavior is the only mechanism that can say anything about blind areas**, but only weakly: a persistent fake looks like a persistent real object, and a legitimate pop-in looks like a fake. OPV2V sequences are about 14 s long, so history is short. Make it an optional second module, gated by a pre-set benefit test.
5. **A small feature/output fallback** (attention share, score jump, solo-decode agreement) costs almost nothing because it comes from the same pass. Log those signals from day one, do *not* use them for the v0 decision, and test them as a fallback after v0.
6. **First thing to measure is the headroom, not the method.** An oracle that gates using ground-truth harm labels, and a *visibility-limited* oracle that may only act where receiver rays exist, bound what any physical-evidence method can achieve. If the visibility-limited oracle recovers little of the attack damage, we simplify the claim before building more.

**Recommendation.** GO for a bounded MINT-v0 prototype: counterfactual effects → receiver-ray existence evidence → calibrated harm probability → keep/gate with explicit UNKNOWN=keep. Temporal and feature fallback are optional modules with pre-registered kill criteria. Corroboration is a baseline and a stratified analysis, not a module. NO-GO on any claim about blind-area attacks until measured.

---

## 2. Literature review (categorized)

Scope: about 40 works, searched through 2026. **No code or results of any prior defense have been reproduced here**; "comparable" below means same problem setting, not that we ran it.

### 2.1 Directly relevant defenses and attacks for intermediate-fusion LiDAR/BEV cooperative perception

| Work | Venue / status | What it actually does | Comparable to MINT? |
|---|---|---|---|
| **CAD**, Zhang et al., *On Data Fabrication in Collaborative Vehicular Perception* [notes] | USENIX Security 2024 | Each vehicle shares an occupancy map (free/occupied/unknown); others check an attacked region against *their own* map plus object motion; region-level alerts, not agent eviction. Introduces Adv-OPV2V [web-checked] | **Closest on physics.** Uses sender-broadcast maps (~10 KB) and a rule-based alert; MINT would use the receiver's own scan only, probabilistic, per-effect. Baseline B-CAD-local |
| **LUCIA / SOMBRA**, Wang et al., *From Threat to Trust* [web-checked + notes] | USENIX Security 2025 | SOMBRA hijacks attentive-fusion attention for removal; LUCIA scales attention by a per-agent-per-frame trust from pairwise pooled-feature L1 distance; no retraining | **Comparable** (same AttFuse). Unit is sender×frame, no calibration, no unknown. Baseline B-LUCIA. Code on Zenodo (not run) |
| **PoseGuard / PosePert**, Zhang, Zhang, Mao, arXiv 2605.01301 [web-checked + notes] | Preprint (v2 Sep 2026) | Fused-vs-ego disagreement filter on safety-critical objects, then per-object feature-crop anomaly detection; detection only, no recovery | Closest on *local unit*. Different output (alarm), object-based |
| **MADE**, Zhao et al., arXiv 2310.11901 [notes] | arXiv; IROS 2024 per notes, not re-verified | Per agent per frame: ego detections with vs without agent i (match loss) + autoencoder residual loss; conformal p-values; BH combination | **Closest on the counterfactual mechanism**, at agent level. Treats divergence as malice, so honest unique views raise it |
| **GCP**, Tao et al., arXiv 2501.02450 [web-checked] | IEEE TDSC (per arXiv comments) | Spatial concordance loss + temporal BEV-flow reconstruction in low-confidence regions; joint Benjamini-Hochberg test; BAC (blind-area-confusion) attack | **Comparable**; also the only reviewed defense that explicitly targets blind areas. Sender-level, tests not calibrated to task harm |
| **CP-Guard** (AAAI 2025), **CP-Guard+** (arXiv 2502.07807), **CP-uniGuard** (arXiv 2506.22890), Hu et al. [web-checked] | AAAI 2025 / preprints | Probability-agnostic sample consensus (split collaborators into groups, fuse each, compare to the ego's own result); consistency loss; later an adaptive threshold over sliding windows; CP-Guard+ moves to feature level | **Comparable baselines** ("ego-consensus" family). Need a trusted ego result as reference |
| **ROBOSAC / "Among Us"**, Li et al. [notes] | ICCV 2023 | Random-sample consensus over sender subsets; needs the prior malicious fraction | Comparable older baseline |
| **PRBI**, Yu et al., *All Vehicles Can Lie*, arXiv 2603.08498 [web-checked] | CVPR 2026 | Treats every vehicle as untrusted; uses last frame's perception as a reference; pseudo-random grouping, ~2.5 verifications/frame; Bayesian estimate of how many/which vehicles are malicious | Comparable, **sender-level with temporal reference**; different assumption (no trusted ego) |
| **Latent Guardian / Cerberus**, Zhang et al. [web-checked] | ICML 2026 (poster) | Feature-space consistency: topological structure, semantic direction, energy distribution | Comparable (feature-only fallback family). Datasets not confirmed from the page |
| **GLST**, He et al., arXiv 2607.23059 [web-checked] | Preprint | Global feature consistency + multi-scale local residual + ego semantic topology; trust weights for fusion; targets multi-attacker injection on confidence-driven (Where2comm) fusion | Comparable idea (weighted fusion); different fusion model |
| **HetShield / HetPoison**, Wang, Liu, Zhang, Li, arXiv 2609.17856 [web-checked] | Preprint | ConvGRU forecasts each agent's next feature map; a malicious feature must contradict both its own recent past and what benign vehicles see at the same place; reports 83–95% recovery | Closest *learned temporal* competitor; needs training (not feasible here) |
| **Pretend Benign (PB)**, Lin et al. [web-checked] | ICCV 2025 | Attack: picks regions by confidence and perturbs while *keeping consensus with other agents* so consensus defenses trust the attacker | **Threat to every consensus-based design**, including a corroboration module |
| **MVIG**, Tao et al., arXiv 2602.19596 [web-checked] | CVPR 2026 | Adaptive attack: learned risk maps over location, timing and persistence; reports up to 62% lower defense success, evaluated on OPV2V and Adv-OPV2V | Threat to temporal and consensus defenses |
| **TrustFlip / TrustReflect**, Liu et al., arXiv 2605.22122 [web-checked] | Preprint (v2 Aug 2026) | Physical adversarial objects make *honest* vehicles disagree, so consistency defenses lower an honest vehicle's trust (removing it in up to 87.7% of scenarios). TrustReflect: honest vehicles mark disputed regions uncertain and exclude them from trust scoring | **Different threat model** (trust poisoning), but its "uncertain region" mask is the nearest published analogue of MINT's UNKNOWN. Argues for tile-level, not sender-level, trust |
| **Tu et al.**, *Adversarial Attacks on Multi-Agent Communication* [notes] | ICCV 2021 | First feature-level attacks on V2V communication | Attack baseline (A-F4) |

### 2.2 Physical, geometric and trust foundations

| Work | Venue / status | What it does | Role for MINT |
|---|---|---|---|
| **CARLO**, Sun et al. [notes] | USENIX Security 2020 | Frustum-based free-space/occlusion consistency to detect injected LiDAR objects (laser-penetration and free-space-detection ratios) | Prior art for ray support/traversal; establishes that the ratio itself is not novel |
| **Shadow-Catcher**, Hau et al. [notes] | ESORICS 2021 (DOI 10.1007/978-3-030-88418-5_33) | Looks for shadow/occlusion consistency to detect ghost objects | Same |
| **MATE**, Hallyburton & Pajic, arXiv 2503.04954 [web-checked + notes] | ACM CCS 2025 | Beta-distributed agent *and track* trust; pseudo-measurements: an aggregator track unmatched *inside* agent k's LiDAR-derived FOV lowers trust, *outside* gives no evidence; negativity-biased update; trust-weighted Kalman fusion | **Closest on the statistical model and the unknown/visibility logic**, but late-fusion tracks with a trusted aggregator and sender-supplied FOV. Not directly comparable; must be cited in the novelty argument |
| **TruPercept**, Hurl et al. [notes] | arXiv 2019 | Trust for cooperative perception from synthetic data | Early baseline idea (object-level trust) |
| Occupancy / evidence theory: Elfes 1989; Thrun, Burgard, Fox *Probabilistic Robotics* 2005; Hornung et al. OctoMap 2013; Amanatides & Woo 1987 ray traversal; Dempster–Shafer [recalled, in project bib] | classical | Log-odds occupancy; grid ray traversal | Background for ray model. Not needed for v0 |

### 2.3 Benign difficulty that MINT must not mistake for attack

| Work | Venue / status | Relevance |
|---|---|---|
| **CoAlign**, Lu et al., arXiv 2211.07214 [web-checked] | ICRA 2023 | Pose errors degrade cooperative perception; a follow-up reports CoAlign's pose-graph optimization fails under heavy noise (3 m / 3°) |
| **CoBEVFlow**, Wei et al., arXiv 2309.16940 [web-checked] | NeurIPS 2023 | Asynchrony: motion-guided shifting of delayed BEV features; not evaluated on OPV2V per search results |
| **V2X-ViT** [notes], **Where2comm** [notes] | ECCV 2022 / NeurIPS 2022 | Alternative fusion architectures; Where2comm-style confidence fusion is the target of GLST |
| **World4V2X**, Wang et al. [web-checked] | IJCAI 2026 (paper 195) | A world model for robustness to *occlusion and degradation*; **no adversarial threat model on the page**; not a defense and not comparable. Its "spatial observability" module is conceptually related to MINT's visibility but is learned and diffusion-based |
| **UECP** (June 2026), **ER-CoPe**, **GevBEV** [snippet-level only from search; titles/venues not verified] | preprints | Uncertainty/evidence maps for fusion weighting under benign degradation (UECP uses LiDAR point density as physical evidence). Not read; treat as leads only |

### 2.4 Calibration, uncertainty, decision-making

| Work | Venue / status | Relevance |
|---|---|---|
| **MOT-CUP**, Su et al., arXiv 2303.14346 [web-checked] | RA-L 2024 (per arXiv comments) | Conformal uncertainty for collaborative detection → tracking, V2X-Sim; no adversaries |
| **TUQCP**, arXiv 2502.02537 [web-checked, title only] | Preprint | Learned uncertainty + conformal calibration under adversarial attacks on V2X-Sim; requires adversarial training. Authors/venue not verified |
| Jøsang & Ismail, beta reputation system (2002) [recalled] | Bled eCommerce | Beta-binomial reputation; MINT's statistical core is a per-effect, per-bin variant |
| Wald sequential test (1945), Page CUSUM [recalled] | classical | Sequential evidence accumulation for the temporal module |
| Platt (1999); Zadrozny & Elkan (2002); Niculescu-Mizil & Caruana (2005) [recalled] | classical | Parametric vs isotonic calibration. Isotonic over-fits when positives are few |
| Vovk et al. conformal prediction; Geifman & El-Yaniv selective classification (NeurIPS 2017) [recalled] | classical | Abstention with risk control; MADE/GCP already use conformal p-values at sender level. Exchangeability across correlated frames is doubtful [notes] |
| Shapley attribution in multi-agent RL, arXiv 2110.01307 [web-checked via search] | arXiv | Exact Shapley is exponential in agents; for ≤5 agents leave-one-out is enough. No cooperative-perception Shapley/leave-one-out paper found beyond MADE-style tests |

### 2.5 Gaps identified by the search

- **No published work found** that (a) keeps the unit at sender×tile, (b) labels it with ground-truth *task harm* offline, (c) supplies independent receiver-side physical evidence per counterfactual effect, and (d) outputs an explicit unknown. This is a search statement (queries on Google-style web search and arXiv pages, not a full systematic review) and must be rechecked before any novelty claim.
- **Blind-area attacks** are acknowledged by GCP (BAC), PB, MVIG. None of the reviewed defenses *verifies* blind-area content with independent physical evidence; they use temporal or consistency heuristics.
- **Calibration against task harm** (rather than against sender maliciousness) appears absent in the reviewed defenses; MADE/GCP calibrate false-detection rate of a sender-level hypothesis test.
- **Evaluation hygiene**: reviewed papers report few clustered confidence intervals; MADE's exchangeability caveat is noted in our notes. Not a criticism of correctness, a reason to be strict ourselves.

---

## 3. Reassessing the objective: the counterfactual definition of harm

**Definition** (consistent with D-02). For sender *i*, tile *u*, time *t*, let `Y⁺` be detections with all contributions, `Y⁻(i)` detections with sender *i* excluded in tile *u*, and `L_u(·)` a local loss against ground truth (false positives, misses, localization error). Offline only:

`D(i,u,t) = L_u(Y⁺) − L_u(Y⁻(i,u))`, where `Y⁺` includes sender *i* and `Y⁻(i,u)` removes its contribution in tile *u* (contract §5.1 loss: `L_u = #FP + #FN + 0.5·Σ_TP(1 − IoU)`, BEV IoU ≥ 0.5, `m = 0.5`). Three disjoint cases (notation resolved 2026-10-23, proposed D-35):
- **HARMFUL (to keep):** `D > m`, i.e. keeping the contribution adds more than `m` local error.
- **USEFUL (harmful to remove):** `D < −m`, i.e. removing it adds more than `m` local error.
- **NEUTRAL:** `−m ≤ D ≤ m`.

The two inference targets are `p_harm_keep = P(D > m | evidence)` and `p_harm_remove = P(D < −m | evidence)`; `p_neutral = 1 − p_harm_keep − p_harm_remove`. D-02's `P(D ≤ m | X)` equals `1 − p_harm_keep`. The only change from contract §5.1 is the boundary: the contract labels `D ≥ m` as HARMFUL; from MINT-v0 on, `D = m` exactly is NEUTRAL (it needs fractional localization terms to occur at all).

**Action rule.** Remove sender *i* in tile *u* (output `Y⁻(i,u)` there) iff the status is KNOWN and `p_harm_keep > κ · p_harm_remove` (cost ratio κ, default 1). Otherwise keep `Y⁺`. The uncalibrated MINT-v0.0 uses raw scores `h_keep`, `h_remove` in place of the probabilities and must not call them probabilities.

**Consequences I checked against the repo and logic**:

1. **Removal is also an action with a harm probability.** Gating a sender in a tile outputs `Y⁻(i)`, which can lose a real object. The repo's own numbers: on clean data 110 of 1,732 effects are REMOVE/harmful (the sender's inclusion erased a real object) and 118 are REMOVE/useful; 12% of all effects are harmful with *no attack* [repo, Stage-2 report]. The honest decision rule is two-sided: act on the side with lower expected harm, using a cost ratio.
2. **One latent variable explains all effect types.** For each effect box *b*:
   - ADD (box only in `Y⁺`): inclusion is useful iff *b* is real.
   - REMOVE (box only in `Y⁻`): inclusion is harmful iff *b* is real.
   - SHIFT: compare the existence/position support of the two boxes.
   So the evidence problem is "is there an object at *b*?", the decision flips by effect type. The existing spec's `min_e σ(ℓ_e + logit π_type)` already encodes this.
3. **Harm is not maliciousness.** Honest senders cause harm (110 benign suppressions). The target is detection quality, so honest-but-harmful contributions should be gated and malicious-but-harmless ones kept. This is a feature of the definition and must be said in the paper.
4. **Label noise and threshold dependence.** `D` depends on the score threshold (0.20), NMS (0.15), IoU thresholds and the matching rule. Cross-tile effects are 4.4% (close to the 5% tolerance); D-22 handles two-tile attribution [repo].
5. **Sparse positives.** On clean data only 39 harmful ADD effects exist across three scenarios (13 receiver-visible). Calibration of the "fake object" tail is data-starved without synthetic attacks, so attack injection is needed for *labels*, not just for testing.
6. **Interaction among senders.** Leave-one-out is exact for one sender; several simultaneously harmful senders in one tile need a joint mask (spec §2 step 4 covers it with one extra local pass). For ≤5 agents, full Shapley is unnecessary.
7. **Ground truth must stay offline.** Offline: `D` labels, empty-space sampling for the null model, calibration, thresholds. Online: only detector outputs, features, receiver scan, receiver pose, bounded history. Watch for these concrete leaks: (a) the dev "self-box" proxy used GT box centres (`D-24` replaces it with the receiver's own pose, which is legitimate); (b) any ground map built from GT; (c) the `static receiver ground map` in spec §3 is MS-specific and OPV2V receivers move, so OPV2V needs a per-frame ground estimate from the receiver's own scan (not implemented: `rays.py` has no ground model) [repo].

---

## 4. Novelty comparison against the closest work

| Defining mechanism of MINT-v0 | Closest prior work | Verdict |
|---|---|---|
| With-vs-without-sender comparison of outputs | MADE (agent-level, match loss), CP-Guard/ROBOSAC (subset consensus) | **Not novel.** MINT's version is tile-level and exact because of pixel locality (V-03). Novelty only in resolution and in using it to *extract effects*, not as the anomaly score |
| Ray support / traversal as object evidence | CARLO, Shadow-Catcher, CAD | **Not novel.** Source of evidence differs (receiver-own rays on intermediate-fusion effects) |
| Beta-style trust with "inside FOV counts, outside FOV does not" | MATE (late fusion; sender-supplied FOV; trusted aggregator) | **Not novel as a statistical pattern.** Differences: intermediate fusion, receiver rays, per-tile effects, calibrated to GT harm |
| Per-region masking of uncertain content | TrustReflect | Related; different purpose (protect honest senders from trust poisoning) |
| Local (object/tile) unit rather than sender | PoseGuard (per object), CAD (per region), LUCIA gets diluted globally (PoseGuard §5.3.1 [notes]) | Partly prior |
| **Calibrated probability that this sender's tile harms detection, with ground-truth-derived labels and an explicit UNKNOWN state** | None found | **Candidate novelty, search-limited.** Claim narrowly: "to our knowledge"; recheck before submission |
| Explicit measurement of how much attack harm is *unreachable* by receiver-side physical evidence | GCP/PB/MVIG discuss blind areas qualitatively | Candidate contribution (an observability bound), only if measured |

**Directly comparable (same setting, can be baselined on OPV2V AttFuse):** CAD, LUCIA, ROBOSAC, MADE, CP-Guard/uniGuard, GCP, PRBI, Cerberus, GLST. **Different threat model or representation:** MATE (late fusion, aggregator), CARLO/Shadow-Catcher (single-vehicle injection), TrustReflect (trust poisoning), World4V2X, CoAlign/CoBEVFlow (benign errors), TUQCP/MOT-CUP (V2X-Sim). Honest reproduction plan: implement `B-LUCIA` (parameter-free, eq. 10–12 in [notes]) and `B-CAD-local`; report the rest as *not reproduced*.

---

## 5. Candidate architectures

Legend for "Needs GT at inference": none of these needs it. The risk column notes where accidental use could creep in.

| # | Architecture | Signals actually available in our code [repo] | Works in receiver-blind tiles? | Main failure under targeted/coordinated attack | Fitting & calibration | Cost (CPU, M1) | Smallest experiment |
|---|---|---|---|---|---|---|---|
| 1a | **Ray-ratio baseline (M3)**: SUP/(SUP+TRAV) threshold | `classify_points`, effects | No (unknown) | Blind-area attack (A-F6) is invisible; moving objects with skew; fakes near real objects | Threshold only (block C) | ray test per effect box; not yet timed | Done as a pilot: AUROC 0.82/0.80 on n_harmful 13/69 |
| 1b | **Calibrated beta-binomial (M4)** | Same counts, plus range/incidence bins; empty-space model | No | Same, plus mis-specified bins; unknown if bin uninformative | μ,φ on block T clean data (no attacks); calibrator on C | Same + table lookup | PPC per range bin on T; ΔAUROC/Brier vs 1a on C |
| 2 | 1b + **cross-agent corroboration** | Solo decodes (deblock+head per sender, extra pass), leave-one-out score margins | Only if a third agent sees the region (≥3 agents) | PB-style consensus-preserving attacks; colluders; effect tiles are by construction places where others do not decide | Combiner weights on T/C | +n head passes | Fraction of effectful units in ≥3-agent frames; AUROC lift in that stratum |
| 3 | 1b + **short temporal consistency** | Previous-frame `Y⁺`, `Y⁻(i)`, track state over K≈5 frames | Weakly (newborn/flicker/jump) | Persistent or slow-ramp attacks (A-T3, MVIG), pop-ins that are legitimate, history poisoning | Discount rate λ, STALE window; fit on T | O(K·boxes) memory | Detection of A-T1 replay and flicker; false flags on benign pop-ins in clean data |
| 4 | 1b + corroboration + temporal | Both | Weakly | Adaptive attacker can satisfy both | Combiner learns interactions; overfits | Sum | Only after 2 and 3 show independent lift |
| 5 | **Feature/output fallback** (logistic on attention share, `s⁺−s⁻`, effect score, ego-vs-sender cosine, solo score) | Free from the fusion pass | Yes (this is its point) but weak and attackable | Attention-hijack and PB attacks shape exactly these features; honest unique views look the same | Scenario-grouped CV on T∪C | negligible | AUROC in blind stratum ≥ 0.60? |
| 6a | Ego-consensus (CP-Guard / PoseGuard filter style) as a **baseline** | Ego-only decode | No (needs ego to see) | Honest unique views flagged | Threshold on C | 1 pass | Required baseline |
| 6b | Learned temporal forecaster (HetShield-style ConvGRU) | Would need training | Partly | Needs GPU/training; none available | Training | — | **Defer** (out of constraints) |
| 6c | Evidential/Dempster–Shafer grids | Not available without a learned evidence head | — | Extra machinery without a clear gain over 1b | — | — | **Reject for v0** |

**Selection (complementary signals only).**
- **Minimum viable (v0):** counterfactual effects + receiver-ray existence evidence (1b, with 1a as its ablation) + calibrator + UNKNOWN=keep policy. Rationale: each piece is independent evidence (output change vs physics), cheap, interpretable, and testable on existing code.
- **Optional module A:** temporal (3). It is the only candidate that addresses the replay/flicker families (A-T1/T2), and is cheap. Include only if the benefit test in §8 passes.
- **Optional module B:** feature fallback (5), logged from day one but not used for the v0 decision; promoted only for blind areas.
- **Not a module:** corroboration (2). Reasons: structurally thin in effect tiles (§1, point 3), undefined with 2 agents (a large share of OPV2V scenes have 2–3 agents [repo]), and PB shows consensus can be spoofed. Keep it as an analysis stratum and a baseline.
- **Do not** combine 4 until 2 and 3 each show independent value.

---

## 6. Recommended MINT methodology (lightweight, interpretable)

### 6.1 Pipeline

```
per frame t (receiver = agent 0, proj_first convention D-13b):
 1. feats[i,k] ← agent_features(model)                          # existing, unchanged
 2. Y⁺ ← decode(fuse_scale(feats, include=None))                # existing
    also keep attn[i,k,pixel]                                    # free, logged
 3. for sender i with nonzero attention mass:
      Y⁻(i) ← decode(fuse_scale(feats, include=¬sender i))      # existing include-mask hook
      effects(i) ← effects(Y⁺, Y⁻(i))  (ADD/REMOVE/SHIFT, D-22 attribution)
 4. for each effect e in tile u:
      counts ← classify_points(receiver_xyz, e.box(es))          # existing: SUP/TRAV/OCC
      status/evidence ← existence test(counts, class, range bin) # beta-binomial or ratio
 5. r(i,u,t) ← Reliability(status, value, effects, aux features)  # §7
 6. final output: tile u uses Y⁻(i) iff status==KNOWN and P(harm|keep) > c·P(harm|remove)
    else Y⁺                                                      # unknown → keep
 7. update bounded temporal state (module A) if enabled
```

### 6.2 Where it plugs into AttFuse (verified in `src/mint/model/attfuse_parts.py`) [repo]
- `agent_features` and `fuse_scale(x, include)` already provide per-agent features, the attention weights and the **sender-exclusion mask**. AttFusion has no learned parameters: it keeps the ego row of `softmax(XXᵀ/√C)X` per pixel; the ego is never excluded.
- `decode` runs deblock+heads. The pixel-local property (93/93 bit-identical) means `Y⁻(i)` need not recompute the backbone; decoding only the pixels of candidate tiles is sufficient *in principle*, but the current code decodes the full map. REMOVE effects require looking at tiles where `Y⁺` shows nothing, so the first version should decode the full map per sender and optimise later.
- **Additional inference passes:** one `fuse_scale`+`decode`+NMS per sender (≈ n_senders), plus at most one final pass if any tile is gated. If nothing is gated the final output is `Y⁺` for free. Cost not yet measured separately; the Stage-1 figure (backbone+fusion+heads 0.50 s/frame for 2 agents) lumps them [repo].
- No change to OpenCOOD (D-14); no training; no new bytes on the wire.

### 6.3 Preventing collateral suppression
- Action space is `{Y⁺, Y⁻(i)}` per *tile and sender* only. Tiles with no effect are never touched (property test: output outside gated tiles is bit-identical to `Y⁺`).
- No sender-level escalation: a sender flagged in many tiles is reported, not banned (D-01).
- The ego and other senders remain in the softmax inside a gated tile.

### 6.4 Short history without unbounded growth (module A)
- Ring buffer of K=5 frames of `(Y⁺ boxes, per-sender effect boxes)`; tracks expire after 2 s; hard cap on track count; per-track discounted counts with λ=0.5/s (spec §3).
- **New sender / new object:** no history means `temp_status=UNKNOWN_NO_HISTORY`, which is neutral, never suspicious. Newborn alone is not evidence: legitimate objects appear at occluder edges and range limits.
- Stale (>2 s) state is dropped, not decayed forever.

### 6.5 Soft weighting versus hard gating
- v0 is hard gating per tile (exact counterfactual, interpretable).
- Soft weighting (add `log w` to the sender's attention logit in a tile) is an ablation: it is not a counterfactual-exact pass and cannot be reasoned about as simply. Test only after v0 works.

---

## 7. Inference-time signals and output format

### 7.1 Signals (all receiver-computable; none uses GT)

| Signal | Source | In v0 decision? | Notes |
|---|---|---|---|
| Effect type, boxes, score jump (`s⁺`, `s⁻` read from the score map at the anchor) | `Y⁺`, `Y⁻(i)` | Yes (type), logged (scores) | Score at the matching anchor in the *other* version is a free soft-support measure |
| Ray counts SUP / TRAV / OCC and candidate-ray count | receiver scan, effect box | **Yes** | Self-box NOT_APPLICABLE (D-24). Point-wise rays only; no-returns never free space (D-06) |
| Range, class, incidence bin, `n_eff` | geometry | Yes (model index / UNKNOWN rule) | |
| Attention share of sender i in tile | `fuse_scale` | Logged | Fallback candidate and attack signature (A-F3) |
| Ego–sender feature cosine / energy in tile | features | Logged | Fallback candidate |
| Sender-solo and ego-solo decode scores at the box | extra heads | Logged for baselines only | Used by B-consensus |
| Temporal: newborn, persistence k, jump distance, STALE | previous frames | Module A only | |

### 7.2 Output record (per sender, tile, time)

```
Reliability(
  status ∈ {KNOWN, NO_EFFECT, UNKNOWN_NO_EVIDENCE, UNKNOWN_OOD,
            UNKNOWN_UNINFORMATIVE, UNKNOWN_STALE, NOT_APPLICABLE_EMPTY},
  p_harm_keep : float | None     # calibrated P(D > m | evidence) iff status==KNOWN and calibrator fitted
  p_harm_remove: float | None    # calibrated P(D < −m | evidence), same conditions
  h_keep, h_remove: float | None # raw uncalibrated scores (MINT-v0.0); never reported as probabilities
  is_probability: bool           # False for uncalibrated variants (1a, pre-calibration 1b)
  effects: tuple[EffectEvidence] # type, boxes, counts, log-BF, bin (audit)
  aux: dict                      # attention share, score jump, … (logged, unused in v0 decision)
  temp_status: str | None
)
```
This tightens the existing spec §4 by exposing both harm directions; the spec's single `value` can be derived. `p_harm_*` is `None` unless a fitted calibrator exists.

### 7.3 Policy for unknown / insufficient evidence

- UNKNOWN when: fewer than 3 effective rays; the range/class bin is out-of-distribution or has fewer than 30 fitting samples; the two classes' fitted success rates differ by less than 0.1 (uninformative); the box is the receiver's own vehicle (NOT_APPLICABLE); or history is stale (module A).
- **Default policy `U_keep`**: UNKNOWN keeps the sender's contribution in that tile, so clean behaviour in unobservable regions equals plain AttFuse.
- Report, not hide: the fraction of tiles/harm that fall in UNKNOWN and the attack success inside UNKNOWN, because that is the admitted vulnerability (blind-area attacker, A-F6/A-F7).
- Ablations (not primary): `U_prior` (act on the prior), `U_drop`, `U_temporal`, and a **safety-aware** variant that is stricter only for UNKNOWN effects inside the ego's forward corridor (PoseGuard's safety-critical-object idea).
- "Low reliability" and "insufficient evidence" are different statuses: the first is `KNOWN` with a high `p_harm_keep`; the second is any `UNKNOWN_*`.

---

## 8. Evaluation plan

### 8.1 Frozen definitions (decide now, before any tuning)

- **2% clean-loss limit = relative.** `AP@0.7_clean(MINT) ≥ 0.98 × AP@0.7_clean(AttFuse)` on the OpenCOOD default AP, scenario-pooled. For the checkpoint's 0.8155 this means at least **0.7992** (1.63 AP points). I recommend relative because an absolute 2-point limit would allow 2.45% relative loss, and because the charter (H2) already says "98% retention" [repo]. Non-inferiority is claimed only if the upper 95% bound of the relative loss, from a **scenario-clustered paired bootstrap**, is ≤ 2%. Also report AP@0.3 and AP@0.5, and AP@0.7 with the global-sort variant once (0.881) for context.
- Same detector, same fusion implementation for with/without (D-20).
- Harm margin `m` and the loss `L_u` are fixed on block T before any C data is seen, and written down in the decision log.

### 8.2 Data separation (what exists and what is needed)

| Block | Scenarios | Use | Status |
|---|---|---|---|
| T (fit) | 3 validate scenarios already examined | fit μ,φ, ground model, tune nothing | On record only; **raw data was deleted**, so using it again requires re-streaming 4.26 GB (under the 5 GB rule) |
| C (calibration + tuning of θ and attack parameters) | The other 6 validate scenarios | calibrator, gate θ, baseline tuning | Needs download |
| E (final) | 16 test scenarios | one frozen evaluation | Clean AP already seen; MINT/attacks untouched. Clean detector features were not cached, so re-streaming 21.1 GB is needed at the end |

**Minimum calibration data**: stream only the **4 small validate scenarios (≈2.9 GB)**, which is below the 5 GB rule. Do **not** request the two large ones (11.1 GB and 21.7 GB) unless the calibration criterion below fails. Calibration criterion: at least ~150 harmful and ~150 useful KNOWN units after attack injection (the count is my estimate for stable parametric calibration, not a derived bound), calibrated with **leave-one-scenario-out** folds. Use Platt-style logistic calibration first; move to isotonic only if positives are ≥ ~200 per effect type. Do not download anything in this phase.

### 8.3 Attacks and benign stress (use the existing protocol, adapted to OPV2V)

Existing protocol is Mixed-Signals-oriented (organized beam grids). OPV2V clouds are unorganized (azimuth not on a fixed grid [repo]), so raw-cloud attacks must be point-wise. First prototype set, all deterministic and keyed by hash (protocol §0):

| Family | ID | Implementation on OPV2V | Frozen to |
|---|---|---|---|
| False objects | A-R2 point-level injection (sender frame, ray-cast mesh) and A-F2a copy-paste feature patch | Needs sender re-encoding (R2) or only features (F2) | A-R2, A-F2 in T/C; others E only (protocol §split) |
| Real object suppressed | A-R1, A-F2b | Remove points in box / paste background patch | |
| Shifted objects | A-R3, A-F5 | 0.5/1/2 m | |
| Feature perturbation | A-F8 (channel zero/scale) in T/C; A-F1/F3/F4 PGD only later (needs gradient passes on CPU) | | |
| Selective/targeted (honest elsewhere) | Mask-limited versions of the above (5 m × 5 m) | By construction | |
| Persistent / multi-frame | A-T1 replay, A-T2 on/off, A-T3 ramp | Needs the temporal module | E only |
| Blind-area | A-F6/A-F7 | The key stress for the physical-evidence ceiling | E only, and a dev version on T |

Benign difficult cases are the existing B-1…B-12: pose error, delay, drops, sparse returns, honest unique views, natural pop-ins, occlusions. OPV2V provides no noise-free pose in the real world; its pose/delay options are available in OpenCOOD but unverified here.

### 8.4 Metrics (defined before tuning)

- Clean and attacked AP@0.3/0.5/0.7; absolute and relative AP recovery `(AP_def − AP_att)/(AP_clean − AP_att)`.
- Harm detection on KNOWN units: precision, recall, AUROC, AUPRC, per stratum (receiver-visible / blind / SENDER_ONLY).
- False rejection of useful contributions, and *retention of useful unique views* (H3 stratum).
- Calibration: reliability diagram (equal-mass bins), ECE, Brier score, on held-out scenarios.
- Fractions retained / gated / UNKNOWN, overall and per stratum; harm admitted inside UNKNOWN.
- Latency (p50/p95, per-sender pass vs total), memory, bytes (0 extra by design).
- Uncertainty: cluster by scenario; with only 3–6 development scenarios report intervals, not significance.

### 8.5 Baselines and ablations
M0 (plain AttFuse); M1 (detector-confidence filter tuned at equal clean false-gating); M3 ray-ratio; B-LUCIA; B-CAD-local; B-consensus (ego-solo agreement, CP-Guard/PoseGuard-style); M4 without calibration; M4 without UNKNOWN (always act); +temporal; +feature fallback; oracle gate; visibility-limited oracle. **Unavailable honestly:** ROBOSAC, MADE (needs autoencoder training), GCP, PRBI, Cerberus, GLST, HetShield are not reproduced; they are cited and compared only qualitatively.

### 8.6 Minimal experiment matrix

| ID | Question | Data | Compare | Metric | Go / failure criterion |
|---|---|---|---|---|---|
| E0 | What is the headroom? | T (re-stream), clean + simple dev attacks | oracle gate; visibility-limited oracle (acts only where ≥3 receiver rays); M0 | AP gain; fraction of attack loss recoverable | If the visibility-limited oracle recovers **< 30% of attack-induced AP loss** under random-placement attacks, physical evidence cannot be the headline: re-scope to an observability study plus temporal. Clean-data oracle gain also reported (12% of effects harmful) |
| E1 | Is ray evidence better than confidence? | T→C | M1, M3, M4 | AUROC/AUPRC, KNOWN-stratum; Brier | M4 must beat M1 by a clear margin on visible ADD/REMOVE. If M3 = M4 within 0.02 AUROC and Brier, drop beta-binomial and ship M3 + Platt |
| E2 | Is the probability calibrated? | C by leave-one-scenario-out | M4 raw vs calibrated | ECE, Brier, reliability | Fail if ECE > 0.05 after calibration or if scenario folds disagree strongly |
| E3 | Does gating preserve clean accuracy? | C (clean) | M0 | relative AP@0.7 loss | Fail if upper bound > 2% at the threshold that achieves useful attack recovery |
| E4 | Does gating recover attacked AP? | C (R2, F2, F5, F8) | M0, M1, B-LUCIA, B-CAD-local | relative recovery; false rejections | Fail if recovery ≤ best baseline or collateral suppression > 0 |
| E5 | Does temporal add independent value? | C (A-T1, flicker), clean pop-ins | v0 | ΔAUROC in UNKNOWN stratum; false flags on clean | Drop if ΔAUROC < 0.03 or clean false flags rise |
| E6 | Does the feature fallback help blind tiles? | C blind stratum | v0 | AUROC in blind stratum | Drop if < 0.60 or if A-F3-style attacks reduce it below chance |
| E7 | Does corroboration add anything? | ≥3-agent frames only | v0 | ΔAUROC | Drop if < 25% of effectful frames have ≥3 agents or ΔAUROC < 0.03 |
| E8 | Cost | M1 CPU | M0 | ms per sender pass; RSS | Fail if total overhead exceeds the budget set by the user (current H5: ≤10% p95 of receiver perception, D-17; dense counterfactual may exceed it, so sparsity is required) |
| E9 | Frozen final evaluation | 16 test scenarios, once | all | all of the above | Hash-sealed predictions before metrics (protocol §9) |

Pilot AUROCs (0.82/0.80) rest on 13 harmful ADD and 69 harmful REMOVE effects from 3 scenarios; the sampling uncertainty on the ADD figure is large (roughly ±0.07 by the usual AUROC variance approximations: my estimate), so they are a feasibility signal only. They also used a post-hoc self-box proxy and have not been rerun under the corrected BEV rule (claim ledger C-07/C-25) [repo].

---

## 9. Implementation roadmap (small verifiable steps)

0. **Freeze definitions** (2% relative, `m`, `L_u`, status enum, two-sided decision) via the decision appendix. No code.
1. **Oracle and visibility-limited oracle** (E0) in a runner reusing `effects.py`, `rays.py` and `fuse_scale`. Verification: oracle-gated output equals `Y⁻(i)` inside gated tiles and bit-equals `Y⁺` outside (extends V-03). Requires re-streaming the 3 T scenarios (4.26 GB).
2. **`mint.reliability` package, pure inference**: dataclass `Reliability`; `mint_reliability(frame, models, params, state)`; no GT importable (import-linter-style test). Unit tests: permutation of sender IDs, prefix (no future frames), self-box, no-return, UNKNOWN rules.
3. **Deterministic v0.0**: M3 ratio + threshold, gating, UNKNOWN=keep, end-to-end `process_frame` returning boxes + `Reliability`. Verify on T: clean AP loss and dev-attack recovery with an uncalibrated threshold. *This is the first working prototype.*
4. **Dev attack injectors** A-F2, A-F5, A-F8, A-R2 (point-level) with realization ledgers (intended vs achieved effect). Verify determinism by hash.
5. **Fit and calibrate** (needs approval to stream the 4 small validate scenarios): μ,φ (T), calibrator (C), PPC, reliability diagrams.
6. **Baselines**: M1, B-LUCIA, B-CAD-local, B-consensus.
7. **Timing** of the per-sender pass; sparsification by attention mass.
8. **Optional modules** per §8.6 criteria (temporal, feature fallback).
9. **Freeze and hash**, then the single test-split run (needs approval for the 21.1 GB stream; features are not cached).

### First milestone (precise)
**M-A: "MINT-v0.0 end-to-end on development data."** Deliverable: a runnable command that, for each frame of the three development scenarios, outputs fused boxes plus a `Reliability` record per (sender, tile), applies hard gating with UNKNOWN=keep, and writes a table with: clean AP retention (relative), AP under three injected attacks, recovery fraction, fraction KNOWN/UNKNOWN/gated, collateral-change count (must be 0), and per-sender-pass milliseconds. It uses the deterministic ray ratio with an explicitly *uncalibrated* threshold, so no calibration claim is made. Exit test: all unit tests pass, hash-identical re-run, and the E0 oracle bounds are reported next to the result. It needs approval to re-stream the 4.26 GB of development scenarios and nothing else.

---

## 10. Go / no-go and risks

**Decision: GO** for the bounded prototype (M-A) and E0/E1. **NO-GO** for claims about blind-area attacks, corroboration, or learned temporal models until measured. Everything else stays out of v0.

**Remaining technical risks**
1. **Observability ceiling**: 30% of useful and 33% of harmful ADD effects are receiver-visible; a blind-area attacker gets through by construction. Mitigation: measure and report; do not oversell.
2. **Few harmful examples**: 13 visible harmful ADD effects. Mitigation: synthetic attacks for labels; scenario-grouped calibration; Platt before isotonic.
3. **Benign harm (12% of clean effects)**: gating them would raise clean AP but mixes "harm" and "attack"; report both.
4. **Cost**: per-sender full-map decode may exceed the 10% budget (D-17); measure before optimising.
5. **Ground estimation on a moving receiver** is not implemented; the dev pilot did not need it, final ray tests might (porous or ground-level objects, TRAV contamination from ground hits).
6. **Consensus-spoofing and adaptive attacks** (PB, MVIG, A-F7) apply to any corroboration or temporal module; the physical module is only fooled in blind areas.
7. **Only AttFuse on OPV2V under `proj_first`** is tested; claims on other fusion models or on real data are unsupported (D-13b, V2V4Real/Mixed Signals replication deferred). Pose, delay, and honest synchrony are protocol assumptions, not verified behaviour.
8. **Novelty claim** must be rechecked; MADE already uses with/without-sender comparison and MATE already uses beta trust with FOV gating.

### Prioritized recommendation

| Do first | Defer | Measure | Abandon or simplify if |
|---|---|---|---|
| Freeze definitions; E0 oracle + visibility-limited oracle; M-A deterministic prototype; then M4+calibration | Corroboration module; learned temporal forecaster; soft weighting; PGD attacks; Mixed Signals; Where2comm/other fusion models | Headroom (E0); AUROC and Brier on visible effects; clean relative AP loss with scenario-clustered bound; fraction UNKNOWN and harm admitted there; per-sender pass milliseconds | **Abandon gating as headline** if visibility-limited oracle recovers <30% of attack loss, or if clean loss bound > 2% at any useful threshold. **Simplify to M3+Platt** if M4 gives <0.02 AUROC and no Brier gain. **Drop temporal** if ΔAUROC < 0.03 in UNKNOWN. **Drop feature fallback** if blind-stratum AUROC < 0.60. **Drop corroboration** if <25% of effectful frames have ≥3 agents |

---

## Appendix A. Reference list (primary sources)

Status column: **P** = peer-reviewed venue per the page or the project's notes; **Pre** = preprint only as far as checked.

| Key | Reference | URL / identifier | Status |
|---|---|---|---|
| CAD | Zhang, Jin, Zhu, Sun, Zhang, Chen, Mao. *On Data Fabrication in Collaborative Vehicular Perception: Attacks and Countermeasures.* USENIX Security 2024 | arXiv 2309.12955; usenix.org/system/files/usenixsecurity24-zhang-qingzhao.pdf | P |
| LUCIA | Wang, Muller, Song, Monteuuis, Petit, Man, Gerdes, Celik, Li. *From Threat to Trust.* USENIX Security 2025, pp. 7387–7406 | usenix.org/conference/usenixsecurity25/presentation/wang-chenyi | P |
| PoseGuard | Zhang, Zhang, Mao. *From Stealthy Data Fabrication to Unsafe Driving.* arXiv 2605.01301 (v2 Sep 2026) | arxiv.org/abs/2605.01301 | Pre |
| MADE | Zhao, Xiang, Yin, Pang, Wang, Chen. arXiv 2310.11901 (IROS 2024 per project notes, not re-verified) | arxiv.org/abs/2310.11901 | P? |
| GCP | Tao, Hu, Hu, An, Cao, Fang. arXiv 2501.02450; IEEE TDSC per arXiv comments | arxiv.org/abs/2501.02450 | P (per arXiv comments) |
| CP-Guard | Hu, Tao, Xu, Deng, Chen, Fang, Kwong. AAAI 2025 | arXiv 2412.12000; ojs.aaai.org/index.php/AAAI/article/view/34486 | P |
| CP-Guard+ | Hu et al. arXiv 2502.07807 | arxiv.org/abs/2502.07807 | Pre |
| CP-uniGuard | Hu et al. arXiv 2506.22890 | arxiv.org/abs/2506.22890 | Pre |
| ROBOSAC | Li, Fang, Bai, Chen, Juefei-Xu, Feng. *Among Us.* ICCV 2023 | arXiv 2303.09495 | P |
| PRBI | Yu, Wu, Zhang, Qiu, Huo, Feng. CVPR 2026 | arxiv.org/abs/2603.08498 | P (per arXiv page) |
| Latent Guardian / Cerberus | Zhang, Li, Wu, Lee, Wang. ICML 2026 | icml.cc/virtual/2026/poster/64455; proceedings.mlr.press/v306/zhang26cs.html | P |
| GLST | He, Wang, Zheng, Zhu, Shen, Jiang. arXiv 2607.23059 | arxiv.org/abs/2607.23059 | Pre |
| HetShield / HetPoison | Wang, Liu, Zhang, Li. arXiv 2609.17856 | arxiv.org/abs/2609.17856 | Pre |
| Pretend Benign | Lin, Pan et al. ICCV 2025, pp. 19947–19956 | openaccess.thecvf.com/content/ICCV2025/html/Lin_Pretend_Benign_A_Stealthy_Adversarial_Attack_by_Exploiting_Vulnerabilities_in_ICCV_2025_paper.html | P |
| MVIG | Tao, Hu, An, Fang, Cao, Fang. CVPR 2026 | arxiv.org/abs/2602.19596 | P (per CVPR listing) |
| TrustFlip / TrustReflect | Liu, Wang, Li, Zhang. arXiv 2605.22122 (v2 Aug 2026) | arxiv.org/abs/2605.22122 | Pre |
| Tu et al. | *Adversarial Attacks on Multi-Agent Communication.* ICCV 2021 | arXiv 2101.06560 | P |
| CARLO | Sun, Cao, Chen, Mao. USENIX Security 2020, pp. 877–894 | usenix.org/system/files/sec20-sun.pdf | P |
| Shadow-Catcher | Hau, Demetriou, Muñoz-González, Lupu. ESORICS 2021 | doi 10.1007/978-3-030-88418-5_33; arXiv 2008.12008 | P |
| MATE | Hallyburton, Pajic. ACM CCS 2025 | arXiv 2503.04954; doi 10.1145/3719027.3765193 | P |
| TruPercept | Hurl, Cohen, Czarnecki, Waslander | arXiv 1909.07867 | Pre |
| World4V2X | Wang, Wang, Qin, Yu, Tan. IJCAI 2026 | ijcai.org/proceedings/2026/195 | P |
| CoAlign | Lu, Li, Liu, Dianati, Feng, Chen, Wang. ICRA 2023 | arXiv 2211.07214 | P |
| CoBEVFlow | Wei et al. NeurIPS 2023 | arXiv 2309.16940 | P |
| V2X-ViT | Xu et al. ECCV 2022 | arXiv 2203.10638 | P |
| Where2comm | Hu, Fang, Lei, Zhong, Chen. NeurIPS 2022 | arXiv 2209.12836 | P |
| OPV2V | Xu, Xiang, Xia, Han, Li, Ma. ICRA 2022 | arXiv 2109.07644 | P |
| MOT-CUP | Su, Han, Li, Zhang, Feng, Ding, Miao. RA-L 2024 (per arXiv comments) | arXiv 2303.14346 | P (per arXiv comments) |
| TUQCP | *Uncertainty Quantification for Collaborative Object Detection Under Adversarial Attacks.* | arXiv 2502.02537 | Pre (authors not verified) |
| Shapley in MARL | *Collective eXplainable AI … Shapley Values.* | arXiv 2110.01307 | Pre |
| Classical [recalled, not re-fetched] | Jøsang & Ismail 2002; Wald 1945; Platt 1999; Zadrozny & Elkan 2002; Niculescu-Mizil & Caruana 2005; Geifman & El-Yaniv NeurIPS 2017; Vovk et al.; Elfes 1989; Thrun et al. 2005; Hornung et al. 2013; Amanatides & Woo 1987 | project bib / standard | — |
| Lead only (not read) | UECP (June 2026), ER-CoPe, GevBEV, Multi-View Trust Evaluation via EDL (arXiv 2608.25235), CoDS (arXiv 2608.14085) | search snippets | unverified |

Caveats: arXiv IDs and dates in 2026 come from the pages fetched in this session. For several works only the abstract page was read this session; their detailed mechanisms rest on the abstract or on earlier notes, as tagged.
