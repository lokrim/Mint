# Part 2 — The paper, section by section

Order follows `paper/main.tex`: Abstract → I Introduction → II Related Work → III Problem Formulation and Threat Model → IV Method (Part 3 of these notes) → V Setup → VI Results → VII Discussion → VIII Conclusion (Parts 4–5) → Appendices.

Paper title: **"MINT: Physically Verified Counterfactual Gating for Robust Cooperative LiDAR Perception."**
- *Physically verified* = checked against real LiDAR rays.
- *Counterfactual* = "with vs without this sender".
- *Gating* = switching contributions off.
- *Cooperative LiDAR perception* = cars sharing LiDAR-based information.

---

## 4. Abstract

**What it is about.** A one-paragraph summary of the whole paper.
**Why included.** Readers decide from the abstract whether to read on. It must state the problem, method, evidence and result.

### Idea by idea

| Abstract says (paraphrased) | Plain English |
|---|---|
| Cooperative perception lets connected vehicles share what their sensors see, so each can detect objects hidden from its own view. | **Context.** Sharing helps cars see more. |
| A sender can manipulate what it shares and add, remove or move objects in the receiver's detections. | **Problem.** A bad sender can create fake cars, hide real cars or move cars. |
| Detection confidence and agreement between vehicles cannot show whether a reported object is physically there. | **Gap.** Existing signals (confidence, agreement) don't prove physical existence. |
| This work investigates whether the receiver's own sensor can verify the effect of each sender's message. | **Research question.** |
| We propose MINT. For each sender, the receiver compares its detections with and without that sender, region by region. It then tests every change against its own LiDAR rays… A sender is switched off only where the rays clearly contradict it. | **Method.** Counterfactual + ray test + local switch-off. |
| Evaluated on OPV2V under a pre-registered protocol, 15 test scenarios, 2,066 frames, 12 attack conditions, plus an unseen simulated town. | **Evidence.** |
| Compared with no defense, receiver-only perception, a feature-statistics check and a ray-based box filter. | **Baselines** (= no defense, ego-only, B-NORM, B-RAY). |
| MINT recovers removal attacks that box filtering cannot, restoring 22.50 of 40.41 lost AP points against the strongest attack. | **Key result.** Note: 40.41 is the **loss**, 22.50 is what MINT **restored** (≈ 56%). |
| Its advantage over the box filter depends on how AP is computed: +0.31 points under one common definition and −0.57 under the benchmark's default. | **Honest caveat.** |
| Physical evidence from a vehicle's own sensor can make shared perception more trustworthy. | **Take-home message.** |

> ⚠️ **Do not say** "MINT recovers 40.41 AP points". 40.41 AP points is how much the strongest stealth removal attack **cost** the undefended receiver (global-ranking AP, OPV2V test). MINT **restored 22.50** of them. Recovery = 22.50 / 40.41 ≈ 0.56 (paper §VI-B; `paper/tables/tab_attacks_both.tex`, `tab_conditions.tex`).

**Short spoken abstract.**
> "Connected cars share sensor information, but a malicious sender can add, remove or move objects in the receiver's view. We propose MINT, which compares the receiver's detections with and without each sender, tile by tile, and tests each change against the receiver's own LiDAR rays. It switches a sender off only where the rays clearly contradict it. On a pre-registered OPV2V evaluation, MINT recovered removal attacks that a box filter cannot — 22.50 of 40.41 lost AP points under the strongest attack — but its advantage over the box filter depends on the AP definition."

**Likely questions.**
- *What is the main contribution in one line?* — Checking each sender's actual influence, per tile, with the receiver's own LiDAR, so that removed objects can be restored.
- *Why mention the AP definition in the abstract?* — Because it changes the ranking against the main competitor; hiding it would overclaim.

**Mistakes to avoid.** Saying MINT "beats all baselines"; saying it "detects attackers"; mixing 22.50 and 40.41.

---

## 5. Introduction and background (paper §I)

### Why vehicles use sensors
A self-driving car must know where other cars are to plan safely. It uses sensors: cameras, radar, and **LiDAR** (light detection and ranging). LiDAR fires laser pulses in many directions and measures distance from the time each pulse takes to return. The result is a **point cloud**.

### Why one vehicle may not see everything
Light travels in straight lines. "A truck ahead, a parked bus or a sharp corner can hide a car that is about to cross its path" (paper §I). This is called **occlusion**.

### Why sharing helps
**[ANALOGY] Road example.** You are at a T-junction. A high wall blocks your view to the right. A car coming from the right is invisible to you. Another connected car is already on that road and sees it. If it shares what it sees, your car "knows" about the hidden car before it appears.

### Three ways to share (paper §II-A)
| Fusion type | What is shared | Trade-off |
|---|---|---|
| Early | Raw points | Most information, huge bandwidth |
| **Intermediate** | **Feature maps** (learned summaries) | **Good accuracy and bandwidth — our setting** |
| Late | Final boxes | Small, but loses information |

**Intermediate fusion** step by step: each car encodes its LiDAR scan into a **bird's-eye-view (BEV) feature map**; the receiver combines (fuses) all maps; a detection head reads the fused map and outputs 3D boxes.

### Why sharing creates risk
"Sharing, however, also means trusting" (paper §I). A sender that is faulty or malicious can change what it transmits. Through fusion, this changes what the receiver detects:
- a **phantom car** → needless emergency braking;
- a **missing car** → possible collision;
- a **moved car** → wrong distance or direction.

### Why feature-level attacks matter
Feature maps are **opaque**: a receiver "cannot look at a feature map and tell whether it describes the real scene" (paper §II-A). And messages can be **authenticated** (cryptographically signed) yet still lie — cryptography proves **who** sent it, not that the content is **true** (paper §III-B).

### Why a defense must handle both fake and missing objects
The paper's three reasons it is hard (§I):
1. Confidence alone does not show an object is physically there; a manipulated map can produce confident detections.
2. A benign sender is useful **because** it sees what the receiver can't; so "being different from the receiver's view is not, by itself, a sign of an attack".
3. "Some attacks remove objects, and a defense that only deletes suspicious detections can never bring a removed car back."

### What the introduction claims MINT adds
"What is missing is a check that asks, region by region, what a sender actually changed in the receiver's output, and tests that change against evidence the sender cannot forge: the receiver's own laser rays" (paper §I).

### Contributions (paper §I)
1. **Method:** MINT — attributes each change to one sender and one 6.4 m tile, verifies with the receiver's own rays, keeps senders when evidence is insufficient.
2. **Evaluation:** pre-registered, one-time comparison with no defense, ego-only, B-NORM and B-RAY under 12 conditions including PGD and stealth attacks, on OPV2V and an unseen town.
3. **Findings:** (a) verifying each sender's influence recovers removal attacks that box filters cannot; (b) the ranking between MINT and B-RAY reverses between two AP definitions; (c) regions the receiver can't see bound what any receiver-side defense can achieve.

**Viva answer (Introduction).**
> "A single car can't see behind obstacles, so connected cars share LiDAR feature maps. But that means trusting the sender — a malicious one can add, remove or move cars. This is hard to defend because feature maps aren't readable, honest senders naturally disagree with the receiver, and a removed car can't be restored by deleting boxes. We propose checking each sender's actual influence with the receiver's own LiDAR."

**Likely questions.**
- *Why not just use encryption?* — The attacker is an **insider**: an authenticated participant. Encryption proves who sent the message, not that its content is true (paper §III-B).
- *Why is "disagreement with the receiver" a bad signal?* — Because the most useful honest sender is the one that sees what the receiver can't, so it disagrees the most (paper §II-C).

**Mistakes to avoid.** Saying LiDAR "sees through" objects; saying feature maps are images.

---

## 6. Problem statement and research gap

### The exact problem (paper §I and §III)
A receiver fuses feature maps from n−1 senders. One sender may be malicious and can change anything it transmits. Can the receiver, using only its own LiDAR and pose, keep detection accurate on attacked frames while losing as little as possible on clean frames?

### What can go wrong when vehicles share features
The attacker can **add** (spoof), **remove**, or **shift** cars in the receiver's output (paper §III-B).

### Why a normal detector does not know which sender caused a change
Fusion mixes all maps into one before detection. The detector outputs a final list of boxes; it does not label "this box came from sender 2". **[ANALOGY]** A soup tastes salty, but you don't know which cook added the salt.

### Why rejecting all cooperative information wastes information
Ego-only (drop all senders) cannot be attacked, but on the OPV2V test it loses **about 20 AP points** even on clean frames (clean ΔAP −21.21 global, −26.52 frame-order; `paper/tables/tab_full_global.tex`, `tab_full_frame.tex`). Cooperation is worth defending, not switching off.

### Why rejecting a whole sender wastes information
Most existing defenses decide **per agent** (paper §II-C). But many attacks are **local** (one fake car in one place). Rejecting the whole sender "stops the attack but also discards everything useful it sent."

### Why checking feature magnitude may fail
A stealth attacker can keep its features within normal statistics. Our B-NORM baseline caught **100%** of plain PGD attacker frames but **0%** of stealth PGD (paper §VI-D). It also falsely flagged the honest sender on **17.4%** of clean test frames with a sender.

### Why detecting added objects alone is insufficient
Box filters (like CARLO-style free-space checks, and our B-RAY) "can delete a fake object but cannot restore one that an attacker removed, and they do not say which sender caused an error" (paper §II-D).

### The gap MINT addresses
A check that is (a) **per sender and per small region**, (b) based on **physical evidence the sender cannot forge**, and (c) able to **restore removed objects** — and that **keeps** senders where the receiver cannot check.

> **What the paper does NOT claim.** It says "Neither of its ingredients is new on its own" (paper §II-E). Counterfactual "with/without a sender" appears in ROBOSAC and MADE; ray free-space checks go back to CARLO and CAD. The claimed novelty is **their combination at a finer grain** (sender × tile), judged by physics instead of agreement. Do not claim "no prior work exists".

**Viva answer.**
> "The problem is that a receiver can't tell which sender caused which detection, and existing defenses either reject whole senders based on agreement, or delete boxes based on physics. Agreement can't prove an object exists, whole-sender rejection throws away useful information, and box deletion can't restore a removed car. MINT combines the counterfactual question with the receiver's own ray evidence, per sender and per tile."

---

## 7. Related work (paper §II)

The paper organises prior work in four groups. Only papers actually cited in `paper/main.tex` are listed.

### 7.1 Cooperative perception and intermediate fusion
- **OPV2V and OpenCOOD** (Xu et al. 2022): the benchmark dataset and code framework; established **AttFuse** (attention fusion) with a **PointPillars** encoder (Lang et al. 2019). *We use exactly this detector.*
- **V2X-ViT** (Xu et al. 2022): fuses agents with vision transformers. *Relevant because it mixes information across space, so MINT's tile exactness would need re-checking (paper §VII-E).*
- **Where2comm** (Hu et al. 2022): chooses what to transmit from spatial confidence maps.
- Real-world datasets: **V2V4Real** (Xu et al. 2023), **Mixed Signals** (Luo et al. 2025). *Not evaluated by us.*

### 7.2 Attacks on cooperative perception
- **Tu et al. 2021**: small bounded perturbations of one sender's intermediate message can mislead the detector.
- **CAD / Zhang et al. 2024**: occlusion-consistent fabrication via ray casting; online feature perturbations to spoof or remove.
- **SOMBRA** (in the LUCIA paper, Wang et al. 2025): hijacks AttFuse attention to make objects disappear.
- **PosePert** (PoseGuard paper, Zhang et al. 2026): shifts objects via stealthy pose perturbations.
- **Blind Area Confusion** (GCP paper, Tao et al. 2026): places perturbations in the victim's blind areas. *Similar spirit to our receiver-blind spoof.*
- **MVIG** (Tao et al. 2026): learns a graph of agents' mutual views to adapt its attack.
- **TrustFlip** (Liu et al. 2026): turns trust-based defenses against benign vehicles.
- **Physical LiDAR spoofing** (Cao et al. 2019): spoofs the victim's own sensor. *Out of scope: no defense that trusts the receiver's sensor, including MINT, can stop it.*
- **Adaptive-attack lesson** (Carlini et al. 2019; Tramèr et al. 2020; Madry et al. 2018 for PGD): defenses must be tested against attackers who know them.

### 7.3 Consensus and anomaly defenses (decide per agent, evidence = agreement)
| Defense | High-level idea |
|---|---|
| **ROBOSAC** (Li et al. 2023) | Samples subsets of senders until the fused result agrees with ego-only perception. |
| **MADE** (Zhao et al. 2024) | Compares outputs with and without each agent, adds a reconstruction loss, controls false alarms with conformal p-values and Benjamini–Hochberg. |
| **CP-Guard** (Hu et al. 2025) | Detects malicious agents via consistency with the receiver. |
| **GCP** (Tao et al. 2026) | Adds spatial and temporal cues. |
| **GLST** (He et al. 2026) | Targets stealthy feature injection by several attackers. |
| **LUCIA** (Wang et al. 2025) | Scales each agent's attention by a trust score from feature agreement. |
| **MATE** (Hallyburton et al. 2025) | Maintains trust over agents and tracks. |
| **Latent Guardian** (Zhang et al. 2026) | Compares collaborator features with the receiver's in structure, direction and energy. |

**Limitation relevant to MINT (paper §II-C):** (1) the decision unit is the whole agent, while attacks are often local; (2) evidence is **agreement, not physics** — the most useful honest sender disagrees most, and an attacker close to the receiver's view may look normal.

### 7.4 Sensor-grounded verification (evidence = physics, unit = box or region)
| Defense | High-level idea |
|---|---|
| **CARLO** (Sun et al. 2020) | Tests whether a detected box is consistent with free space and laser penetration in the vehicle's own point cloud. |
| **Shadow-Catcher** (Hau et al. 2021) | Checks for the "shadow" a real object must cast behind it in the point cloud. |
| **CAD** (Zhang et al. 2024) | Vehicles share occupancy maps (free/occupied/unknown); the receiver flags regions where the fused result contradicts them. Strongest form needs another benign vehicle observing the region; a local variant uses only the receiver's own map. |

**Limitation relevant to MINT (paper §II-D):** applied to final boxes, they can delete fakes but not restore removed objects, and don't say which sender caused an error.

### 7.5 Comparison table (paper Table "positioning", §II-E)
| Defense | Decides per | Evidence used |
|---|---|---|
| ROBOSAC | sender subset | agreement with receiver's own output |
| MADE | agent | output change without the agent; reconstruction |
| CP-Guard, GCP | agent | consistency with receiver (GCP: spatial + temporal) |
| LUCIA, Latent Guardian | agent | feature agreement |
| MATE | agent, track | track agreement, field of view |
| CARLO | box | own LiDAR free space |
| CAD | region | shared occupancy maps |
| B-RAY (our baseline) | box | receiver's own rays |
| **MINT** | **sender and tile** | **counterfactual change, tested with the receiver's own rays** |

### 7.6 The four approach categories in plain words
- **Consensus / agreement** — "Do the others agree with you?" Good at noticing the odd one out; can't tell whether the odd one out is lying or simply sees more.
- **Free-space / ray-based** — "Do my laser beams pass through where you say a car is?" Physical, hard to forge; but only where the receiver can see, and on boxes only.
- **Feature-norm anomaly** — "Are your numbers unusually large?" Cheap; a stealth attacker stays within normal size (our B-NORM: 0% catch on stealth PGD).
- **Counterfactual sender-influence testing** — "What exactly changes if I ignore you?" Tells which sender did what; MINT combines this with the ray test, per tile.

**Viva answer.**
> "Prior defenses fall into two groups. Consensus and anomaly methods like ROBOSAC, MADE, CP-Guard and LUCIA decide per agent using agreement. Sensor-grounded checks like CARLO, Shadow-Catcher and CAD use LiDAR physics but act on boxes or regions. MINT isn't new in either ingredient; it combines the counterfactual question with the receiver's own ray test, at the level of one sender in one 6.4-metre tile."

**Mistakes to avoid.** Claiming we compared experimentally against LUCIA, MADE or CP-Guard — **we did not** (paper §VII-E: "We did not run learned or consensus defenses, and make no claim relative to them"). Inventing details of these papers beyond what is written above.

---

## 8. Problem formulation and threat model (paper §III)

### Setting
- n connected vehicles. Agent 0 = **receiver**. Agents 1…n−1 = **senders**.
- Each sender encodes its LiDAR point cloud into BEV feature maps f_{i,k} at **three scales** k ∈ {1, 2, 3} and transmits them.
- OpenCOOD convention: a sender first moves its points into the **receiver's coordinate frame** before encoding, so its maps arrive aligned with the receiver's BEV grid. (In development, encoding in the sender's own frame "collapses this checkpoint", so the study uses this convention; `planning/README.md`.)
- The receiver fuses all maps (its own f₀ included) and decodes: **Y⁺ = Dec(Fuse(f₀, …, f_{n−1}))**.
- Detector: **AttFuse** (per-pixel attention) on **PointPillars**, the **released checkpoint, never retrained**.

### Threat model
- **One** malicious sender, an **insider**: authenticated, participates normally — "the message is genuine, but its content is wrong."
- It can change its feature maps (all three scales) **or** its point cloud before encoding.
- Goal: **add**, **remove** or **shift** a car.
- For optimised attacks: **white-box** — knows detector weights, receiver's features, fusion, head.
- It does **not** control the receiver's sensor, pose or software, and does **not** collude.
- In experiments the attacker is **always sender 1**. Frames with n = 1 have no sender → counted as clean.
- **Stealth** attacker: keeps features below B-NORM's threshold. **Receiver-blind** attacker: places fakes where the receiver's LiDAR can't see.
- **No attacker is optimised against MINT's LiDAR check** (stated as a limitation).

### Defender's goal and trusted evidence
- Trusts only its own scan P₀ and its own pose.
- May decode received features as often as it likes (e.g. with and without a sender).
- **Never sees ground truth.**
- Goal: keep AP@0.7 on attacked frames high while losing as little as possible on clean frames.
- Possible action levels: drop a sender for the whole frame; delete boxes; or (MINT) switch off one sender in one tile.

**Viva answer.**
> "We assume one authenticated insider attacker who can change anything it sends — features or points — to add, remove or shift a car. For optimised attacks it's white-box. It can't touch the receiver's sensor or software and doesn't collude. The receiver trusts only its own LiDAR and pose and never sees ground truth."

**Likely follow-ups.**
- *Is one attacker realistic?* — It's a stated scope limit. Two colluding senders could both add the same fake; removing one at a time would leave it (paper §VII-E).
- *What if the receiver's own LiDAR is spoofed physically?* — Out of scope; MINT trusts the receiver's sensor (paper §II-B, §VII-E).

---

## 9. Objectives (as a section)

The paper has no "Objectives" section (see Part 1 §2). If your project report needs one, use the five objectives from Part 1 and connect them like this:

| Objective | Connects to problem | Connects to method |
|---|---|---|
| 1. Measure each sender's influence | Detector can't tell which sender caused which change | Counterfactual Y⁺ vs Y⁻(i) |
| 2. Classify ADD / REMOVE / SHIFT per tile | Attack goals are add / remove / shift; attacks are local | Hungarian matching, thresholds, 6.4 m tiles |
| 3. Verify with receiver LiDAR; keep if UNKNOWN | Agreement can't prove existence; honest unique views must survive | SUP / TRAV, N ≥ 3, Wilson rule, gating |
| 4. Fair robustness evaluation vs baselines | Defenses must face strong and adaptive attacks | Pre-registered OPV2V test + Culver City; 12 conditions |
| 5. Quantify trade-offs | A defense must be usable and honestly reported | Clean loss, runtime, two AP definitions, blind attack |

**Memorise:** *Measure → Classify → Verify → Evaluate → Trade-offs.*
