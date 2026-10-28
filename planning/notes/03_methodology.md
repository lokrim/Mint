# Part 3 — The method from zero (paper §IV)

The chain we will follow:

```
senders share features → receiver makes normal output (Y+) → receiver drops one sender and recomputes (Y-(i))
→ compare outputs (Hungarian matching) → classify changes (ADD / REMOVE / SHIFT) → put each change in a 6.4 m tile
→ count receiver LiDAR rays (SUP / TRAV) → KNOWN or UNKNOWN? → Wilson interval → gate rule per effect
→ gate per (sender, tile) → rebuild each tile without its switched-off senders → NMS → final detections
```

The paper groups this into **five stages** (paper Fig. "mint_method", `paper/figures/mint_method.tex`):
1. **Inputs** — receiver's scan P₀ and features f₀ (trusted); senders' features fᵢ (untrusted).
2. **Counterfactual attribution** — Y⁺ and Y⁻(i); differences = ADD / REMOVE / SHIFT effects of i in tile u.
3. **Receiver-ray verification** — count SUP and TRAV rays per effect box; too few → UNKNOWN.
4. **Gating decision** — switch sender i off in tile u only if rays resolvably contradict an effect and confirm none; UNKNOWN keeps.
5. **Filtered detections** — each tile takes the decode without its switched-off senders; NMS gives Y_MINT.

---

## 9. System model: the vehicles and the data

### Who is who
- **Receiver / ego vehicle (agent 0):** the car that detects and defends. It trusts **only** its own LiDAR scan P₀ and its own pose (position and orientation).
- **Senders (agents 1…n−1):** other connected cars. Their messages may be wrong. In the OPV2V test, frames have 1 to 5 agents (paper Table "splits").

### What a sender transmits
BEV **feature maps** fᵢ at three scales (paper §III-A). Each message is about 15.8 MB in this setup (`planning/README.md`, Stage-2 note).

**What is a feature map?** [ANALOGY] Imagine a sheet of graph paper laid over the road map, seen from above. In every small square, instead of a colour, the network writes a long list of numbers that mean things like "there's probably a car edge here" or "this looks like road". It is **not a photo**. A human can't read it. It is a compressed, learned summary that only the detector understands. "Three scales" means three such sheets with different square sizes (fine, medium, coarse).

### What fusion does
**Fuse** combines the receiver's own map with the senders' maps into one. AttFuse does this **per pixel** with attention: at each grid square, it decides how much weight to give each car's numbers at that same square. (This "per-pixel" property is why MINT's tile-by-tile output is exact for AttFuse; paper §IV-D.)

### What the detection head does
**Dec** reads the fused map and outputs **candidate boxes** with **confidence scores**, then **NMS** (non-maximum suppression: when several boxes overlap the same object, keep the highest-scoring one) gives the final detections.

### What a 3D bounding box tells us
Centre position (x, y, z), size (length, width, height), and heading (which way the car points). A confidence score says how sure the detector is.

### Why the receiver's own LiDAR is useful
"A message cannot change where the receiver's own laser rays stop" (paper §II-D). It is evidence **outside the attacker's control** (unless the attacker physically spoofs the receiver's sensor, which is out of scope).

### Text flowchart

```
 Sender 1 LiDAR ─► encode ─► f1 ─┐
 Sender 2 LiDAR ─► encode ─► f2 ─┤            (untrusted messages)
       ...                       ├─► Fuse ─► Dec ─► 3D boxes  (Y+)
 Receiver LiDAR ─► encode ─► f0 ─┘
       │
       └──────────── own scan P0 (trusted) ───────────► ray verification stage (MINT)
```

Arrow by arrow:
- **LiDAR → encode → f:** each car turns its point cloud into feature maps (PointPillars encoder).
- **f → Fuse:** the receiver gathers all maps (its own included).
- **Fuse → Dec:** the fused map is decoded into boxes.
- **P₀ → verification:** the receiver's **raw points** go straight to MINT's ray test, **never through fusion**. This is why the sender cannot influence the evidence.

### MINT is not a reputation score
MINT does not keep a running "trust score" per car. It looks at **one frame**, asks what each sender changed **in this frame, in this tile**, and decides there. A sender can be switched off in one tile and kept in the next tile of the same frame.

**Viva answer.**
> "Each car encodes its LiDAR into bird's-eye-view feature maps — learned summaries, not images — and sends them. The receiver fuses all maps with per-pixel attention and decodes 3D boxes. MINT uses the receiver's own raw LiDAR scan, which never passes through fusion, as the only trusted evidence. It decides per frame and per tile, not as a long-term reputation."

---

## 10. Counterfactual testing — the core idea

### Everyday analogy first [ANALOGY]
A group of five students solves a puzzle and gets answer A. The teacher wonders: "What did Priya contribute?" So the group solves it **again without Priya**, and gets answer B. Whatever differs between A and B is **Priya's influence**.

Limits of the analogy:
- Students may change their thinking when re-solving; MINT's detector is **fixed** — the same frozen network simply receives one map fewer. Nothing is retrained (paper §IV-A).
- A difference shows **influence**, not **guilt**. Maybe Priya contributed the correct idea! That is why MINT next checks the difference against evidence.

### The two outputs

**Output A — all senders included:**

  Y⁺ = Dec( Fuse( f₀, f₁, …, f_{n−1} ) )        (paper Eq. 1)

**Output B — sender i excluded:**

  Y⁻(i) = Dec( Fuse( { f_j : j ≠ i } ) )        (paper Eq. 2)

| Symbol | Plain meaning |
|---|---|
| f_i | the feature maps (all three scales) of agent i; f₀ is the receiver's own |
| Fuse | the fusion module (AttFuse) — combines the maps |
| Dec | the detection head — turns the fused map into boxes |
| Y⁺ | the normal cooperative output: boxes detected with everyone |
| Y⁻(i) | the **counterfactual** output: "what the receiver would have detected if sender i had stayed silent" |
| i | the sender being tested; MINT loops over i = 1 … n−1 |

### What comparing them tells us
Every difference between Y⁺ and Y⁻(i) is **caused by sender i's message** (because that's the only thing that changed). It reveals **influence**. It does **not**:
- prove the sender is malicious (honest senders change outputs too — that's their purpose);
- reveal the sender's identity or intent;
- inspect the sender's internal workings.

### Three miniature examples [TEACHING EXAMPLE]

**Example 1 — a box appears only with the sender**
- Output A (with sender 2): cars at P, Q, **R**.
- Output B (without sender 2): cars at P, Q.
- Change: R exists only because of sender 2 → **ADD**.
- Next question: does the receiver's laser show something at R?

**Example 2 — a real car disappears when the sender is included**
- Output A (with sender 1): cars at P, Q.
- Output B (without sender 1): cars at P, Q, **S**.
- Change: S is there without sender 1, but sender 1 made it vanish → **REMOVE**.
- Next question: do the receiver's laser rays stop at S (something really there)?

**Example 3 — a box stays but moves**
- Output A (with sender 1): car at P, Q, and T at (25.0, 4.0) heading 0°.
- Output B (without sender 1): car at P, Q, and T at (25.0, 1.0) heading 0°.
- Change: T matched in both, but its centre moved 3.0 m (> 0.3 m) → **SHIFT**.
- Next question: which position do the rays support better — the old (B) or the new (A)?

**Viva answer.**
> "The counterfactual is: decode once with all senders, and once with one sender left out. The detector isn't retrained; fusion just gets one map fewer. Whatever differs is that sender's influence. It doesn't prove an attack — honest senders change the output too — so we then test the difference with the receiver's own LiDAR."

---

## 11. ADD, REMOVE and SHIFT

Formal definitions (paper §IV-A, Eq. 3), with M_i the matched pairs:
- **ADD_i** = { b ∈ Y⁺ : b unmatched in Y⁻(i) }
- **REMOVE_i** = { b ∈ Y⁻(i) : b unmatched in Y⁺ }
- **SHIFT_i** = { (b⁺, b⁻) ∈ M_i : d_c > 0.3 m **or** d_ψ > 10° }
  (d_c = distance between BEV centres; d_ψ = heading difference, ignoring a 180° flip)

Thresholds verified in code: `src/mint/effects/effects.py` — `iou_match=0.1, d_shift=0.3, yaw_shift_deg=10.0`.

### ADD
- **Meaning:** a car that exists **only because of** sender i.
- **How the outputs reveal it:** in Y⁺ (with), not in Y⁻(i) (without).
- **Danger:** a phantom car → sudden braking, swerving.
- **Road example:** the receiver suddenly "sees" a car stopped in its lane 30 m ahead, but only when sender 1 is included.
- **What MINT checks next:** the box in Y⁺. If the receiver's rays mostly **pass through** it → contradicted (gate).
- **Note:** an honest sender also creates ADDs — e.g. a car hidden behind a bus that only the sender sees. If the receiver has too few rays there → UNKNOWN → kept. If its rays clearly stop on it → **useful**.

### REMOVE
- **Meaning:** a car that exists **without** sender i but disappears **with** it.
- **How the outputs reveal it:** in Y⁻(i) (without), not in Y⁺ (with).
- **Danger:** a missing real car → collision.
- **Road example:** without sender 1, the receiver sees a car at the junction; with sender 1, that car is gone.
- **What MINT checks next:** the box in Y⁻(i). If the receiver's rays mostly **stop inside** it → something really is there → the removal is contradicted (gate). Switching the sender off in that tile brings the car back.
- **Why a box filter can't fix it:** a filter that only looks at the final boxes Y⁺ never sees the removed car — it's not in Y⁺. It can only delete boxes, not create them. MINT can restore it because the car is still present in Y⁻(i) (paper §VII-A).

### SHIFT
- **Meaning:** the same car in both outputs (matched), but moved > 0.3 m or turned > 10°.
- **Difference from ADD/REMOVE:** the car exists in both; it's a position/heading change, not an appearance/disappearance.
- **Why position and heading matter:** planning depends on where a car is and where it's going; a wrong heading predicts the wrong path.
- **What MINT checks:** both boxes. It gates if the two Wilson intervals do not overlap (written "dis", disjoint) **and** the old position is better supported (s⁺ < s⁻). Useful if disjoint and the new position is better supported (s⁺ > s⁻) (paper Eq. 6).
- **Tile:** a SHIFT belongs to the tiles of **both** versions of the box (paper §IV-A).

### Comparison table

| Effect | In Y⁺ (with sender i)? | In Y⁻(i) (without sender i)? | Box tested with rays | Gate if (KNOWN) | Useful if (KNOWN) |
|---|---|---|---|---|---|
| ADD | yes | no (unmatched) | b⁺ | hi(s⁺) < 0.5 | lo(s⁺) > 0.5 |
| REMOVE | no (unmatched) | yes | b⁻ | lo(s⁻) > 0.5 | hi(s⁻) < 0.5 |
| SHIFT | yes (b⁺) | yes (b⁻), matched | both | intervals disjoint and s⁺ < s⁻ | intervals disjoint and s⁺ > s⁻ |

⚠️ These are **sender-associated changes**, not comparisons with ground truth. MINT never sees ground truth. An ADD can be a real hidden car; a REMOVE can be the correct removal of a duplicate or false box.

---

## 12. Matching detections: BEV IoU and Hungarian assignment

### The problem
Before saying "a box appeared", we must decide which box in Y⁺ is "the same car" as which box in Y⁻(i). The two outputs are just lists of boxes; nothing links them.

### BEV
Look at both outputs from above (bird's-eye view), ignoring height. Each box becomes a rectangle on the ground.

### IoU
**IoU = area of overlap ÷ area covered by either box.**
[TEACHING EXAMPLE] Two 4 m × 2 m rectangles, one slid 2 m along the length:
- overlap = 2 m × 2 m = 4 m²; union = 8 + 8 − 4 = 12 m²; IoU = 4/12 ≈ 0.33.

The threshold 0.1 is about **the two boxes being compared**, not about the road: they count as the same car if their overlap is at least 10% of the area the two boxes jointly cover. 0.1 is deliberately loose so that a **moved** car is still matched (and then classified as SHIFT) rather than counted as one REMOVE plus one ADD. (Scoring against ground truth uses the much stricter 0.7.)

### Hungarian assignment
An algorithm that pairs items **one-to-one** so that the total match quality is best, and **no box is used twice**. Here it maximises BEV IoU; pairs with IoU < 0.1 are rejected (paper §IV-A).

[ANALOGY] Pairing dance partners: each person gets at most one partner, and you choose pairings that work best overall, not greedily.

### Tiny example [TEACHING EXAMPLE]

```
 Y+  (with sender 1):    A+ at (10.0, 0.0)   B+ at (20.0, 5.0)   C+ at (30.0, -3.0)
 Y-  (without sender 1): A- at (10.1, 0.0)   B- at (21.0, 5.0)                        D- at (40.0, 8.0)
```
(cars ≈ 4.5 m × 1.9 m, all pointing along x)

- A⁺–A⁻: almost identical, IoU ≈ 0.96 → matched; moved 0.1 m (< 0.3 m) → **no effect**.
- B⁺–B⁻: shifted 1 m along the length, IoU = (3.5 × 1.9)/(2 × 4.5 × 1.9 − 3.5 × 1.9) = 3.5/5.5 ≈ 0.64 → matched; moved 1.0 m (> 0.3 m) → **SHIFT**.
- C⁺: no box in Y⁻ overlaps it → unmatched in Y⁻ → **ADD**.
- D⁻: no box in Y⁺ overlaps it → unmatched in Y⁺ → **REMOVE**.

Without matching, you could not tell "B moved" from "B disappeared and a new car appeared".

---

## 13. Spatial localisation and 6.4 m tiles

### Why not reject the whole sender?
A sender may add one fake car in one place while giving useful information everywhere else. Rejecting the whole sender "stops the attack but also discards everything useful it sent" (paper §II-C).

### Tiles
"The BEV map is divided into square tiles of 6.4 m, and each effect belongs to the tile u that contains its box centre (for a SHIFT, the tiles of both versions). The unit of every decision is a pair (i, u): sender i in tile u" (paper §IV-A). E_{i,u} = the effects of sender i in tile u.

[ANALOGY] A chessboard laid on the road map. Each square is 6.4 m × 6.4 m (roughly one and a half car lengths). For each friend and each square, you decide separately: listen or mute.

```
 [TEACHING EXAMPLE] — sender 1's effects in one frame
 +------+------+------+------+
 |      |  ADD |      |      |    tile (1,0): ADD contradicted by rays → mute sender 1 HERE ONLY
 |      | (✗)  |      |      |
 +------+------+------+------+
 |      |      | ADD  |      |    tile (2,1): ADD in a spot the receiver can't see → UNKNOWN → keep
 |      |      | (?)  |      |
 +------+------+------+------+
 | REM  |      |      | ADD  |    tile (0,2): REMOVE contradicted → mute sender 1 here (car comes back)
 | (✗)  |      |      | (✓)  |    tile (3,2): ADD supported by rays → useful → keep
 +------+------+------+------+
```
Sender 1 is muted in 2 tiles and kept in all others.

### What localisation does not prove
It does not prove the sender is malicious in that tile, nor that the rest of its message is honest. It only limits each decision's scope to where the evidence is.

---

## 14. LiDAR physical verification: SUP and TRAV

### LiDAR in one picture [ANALOGY]
The LiDAR spins and fires many laser pulses. Each pulse travels in a straight line until it hits a surface and bounces back. The sensor measures the distance. So each **ray** goes from the sensor to one **return point**. Everything **between** the sensor and the return point was empty space (the light passed through it). Things **behind** the return point are unknown (the light was blocked).

### The candidate box
A box is an imaginary 3D outline where an effect claims a car is (or was). MINT tests the receiver's rays that **cross the inner core** of this box. The core is the box shrunk slightly so that ground and roof returns don't count: shrunk horizontally by 15% of each side (at least 0.15 m), trimmed 0.3 m at the bottom and 0.1 m at the top; returns are compared with the box enlarged by 0.2 m, with a range tolerance of 0.05 m + 1% of range (paper App. A).

### Three cases (paper §IV-B)

```
  receiver LiDAR                       candidate box
       (S) ─────────────────────────► [ ●      ]               SUP: ray ENDS INSIDE the box
                                                                 → something is there
       (S) ──────────────────────────[──────────]──────► ●      TRAV: ray PASSES THROUGH and ends BEHIND
                                                                 → the box space is empty
       (S) ──────────► ●             [          ]               BLOCKED: ray ends BEFORE the box
                                                                 → says nothing about the box
```

- **SUP (support):** ray ends inside the box → "something is there".
- **TRAV (traversal):** ray ends behind the box → "the laser passed through empty space".
- **Blocked:** ray ends before the box → no information; not counted.
- **No return at all:** **never** counted as traversal, "because a missing return does not prove free space" (paper §IV-B). (Dark or glass surfaces may not reflect.)

**Why the endpoint matters:** a ray is only evidence of emptiness for the part of its path **before** its endpoint. If it stops inside the box, it hit something there.

### Support ratio (paper Eq. 4)

  s(b) = SUP(b) / N(b),    N(b) = SUP(b) + TRAV(b)

- SUP(b) = number of support rays for box b
- TRAV(b) = number of traversal rays for box b
- N(b) = number of **informative** rays
- s(b) = fraction of informative rays that say "something is there"

[TEACHING EXAMPLE] 4 SUP, 2 TRAV → N = 6, s = 4/6 ≈ 0.67. Meaning: two-thirds of the informative rays stopped inside the box. It does **not** mean "67% chance a car is there", and with only 6 rays it is too uncertain to decide (see §16).

**Edge case — zero rays:** if N = 0 the ratio is undefined; MINT never computes a decision then, because N < 3 makes the unit UNKNOWN (§15). (The code's Wilson function returns the uninformative interval [0, 1] for N = 0; `src/mint/reliability/r1.py`.)

### Rays are clues, not truth
Evidence can be incomplete or misleading because of:
- **occlusion** — another object blocks the rays;
- **sparse points** — far away, fewer rays hit a box;
- **sensor angle / blind regions** — some areas are never reached;
- in real sensors (not tested): dark or glass surfaces (no returns → more UNKNOWN), vegetation or spray (false support) (paper §VII-E).

---

## 15. KNOWN versus UNKNOWN evidence

**Rule (paper §IV-B; code `src/mint/reliability/r1.py`):** a unit (i, u) is **KNOWN** if **every** box in E_{i,u} has **N ≥ 3** informative rays **and none of them is the receiver's own vehicle**. Otherwise it is **UNKNOWN**: "the receiver does not have enough evidence, and the sender is kept." (The receiver can't use its own LiDAR to check a box around itself.)

[TEACHING EXAMPLE] Two cases:
- **Enough rays.** A sender adds a car 15 m ahead in open road. 12 receiver rays cross its core → KNOWN → go to the Wilson test.
- **Too few rays.** A sender adds a car behind a building the receiver can't see. 1 ray crosses it → UNKNOWN → keep the sender in that tile.

**Key principle:** *"I do not have enough evidence" is not the same as "the object is false."*

**Why keep under UNKNOWN?** The most valuable thing an honest sender provides is information about places the receiver **cannot see** (non-line-of-sight). If MINT switched senders off whenever it couldn't verify, it would destroy exactly the benefit of cooperation. So "UNKNOWN units are always kept, so MINT never removes information that the receiver cannot check" (paper §IV-C).

**The cost of this choice:** an attacker who places fakes where the receiver can't see is **not stopped**. The receiver-blind spoof did exactly this: of 1,412 realized blind spoofs on the test, 1,381 landed where the receiver had fewer than three rays, and 0 touched a unit the receiver could check (paper §VI-D). This cautious fallback **does not guarantee** the kept contribution is correct.

---

## 16. Wilson confidence interval and the gating thresholds

### Layer 1 — the plain idea
A ratio from 3 rays is much less reliable than one from 30. 2 out of 3 and 20 out of 30 are both "67%", but you should trust the second far more. MINT puts a **range** around the ratio — wide when there are few rays, narrow when there are many — and only decides when the **whole range** is clearly on one side of one half.

### Layer 2 — what a confidence interval is (beginner version)
A confidence interval is a range of values for an underlying proportion that are **reasonably consistent with what you observed**. A 95% interval is built by a procedure that, under its assumptions, captures the true value in about 95% of repeated experiments. The more data, the narrower it gets.

**Important — how the paper reads it.** "Rays that hit the same object are not independent trials, so we read this interval as a **resolvability margin** on the ray counts, not as a probability" (paper §IV-B). So in the viva, say: *"We use the Wilson interval as a safety margin that says whether the ray counts are clear enough to decide. We don't claim it's a calibrated probability."* (This choice is explained in App. C: an early plan to report calibrated probabilities was dropped.)

### Layer 3 — the formula (paper Eq. 5)
With a = SUP(b) support rays out of N = N(b) informative rays, z = 1.96 (the 95% level):

  [lo, hi] = ( a + z²/2 ∓ z·√( a(N−a)/N + z²/4 ) ) / ( N + z² )

- **z = 1.96** is the number of standard deviations that covers the central 95% of a normal (bell) curve. The code uses 1.959964 (`src/mint/reliability/r1.py`).
- **lo(s)** = lower end: "the support share is at least about this much".
- **hi(s)** = upper end: "the support share is at most about this much".

### Why compare with 0.5?
0.5 means "half the informative rays stopped inside, half passed through" — the evidence is balanced. If the **whole interval is below 0.5**, rays mostly pass through → the box is resolvably **empty**. If the **whole interval is above 0.5**, rays mostly stop → the box is resolvably **occupied**. If the interval contains 0.5, the evidence is **not clear enough** → neither verdict.

### Worked numbers [TEACHING EXAMPLE — computed with the paper's formula, not experimental results]

| SUP a | N | s = a/N | Wilson [lo, hi] | Reading |
|---|---|---|---|---|
| 0 | 3 | 0.00 | [0.00, 0.56] | hi > 0.5 → **not** resolvably empty (paper: "three give 0.56") |
| 0 | 4 | 0.00 | [0.00, 0.49] | hi < 0.5 → resolvably empty (paper: "four give hi = 0.49") |
| 0 | 10 | 0.00 | [0.00, 0.28] | clearly empty |
| 4 | 6 | 0.67 | [0.30, 0.90] | contains 0.5 → undecided |
| 20 | 30 | 0.67 | [0.49, 0.81] | still just contains 0.5 → undecided |
| 40 | 60 | 0.67 | [0.54, 0.77] | lo > 0.5 → resolvably occupied |
| 9 | 10 | 0.90 | [0.60, 0.98] | resolvably occupied |
| 3 | 3 | 1.00 | [0.44, 1.00] | lo < 0.5 → **not** resolvably occupied |

Lessons:
- The same ratio (0.67) is undecided with 6 or 30 rays but decided with 60. **The interval adds caution that the raw ratio lacks.**
- With exactly 3 rays, no verdict is possible either way (0/3 gives hi = 0.56; 3/3 gives lo = 0.44). So **in practice a box needs at least 4 rays** to be judged — the paper's example: "a box supported by no ray is called empty only if at least four rays cross it" (§IV-B).

### The gate rules (paper Eq. 6) — in words
With s⁺ the support ratio of the effect's box in Y⁺ and s⁻ that of its box in Y⁻(i):

| Effect | Gate (contradicted) | Useful (confirmed) | In words |
|---|---|---|---|
| ADD | hi(s⁺) < 0.5 | lo(s⁺) > 0.5 | "An added car is contradicted when the rays mostly pass through it." |
| REMOVE | lo(s⁻) > 0.5 | hi(s⁻) < 0.5 | "A removed car is contradicted when the rays mostly stop on it, because then something really is there." |
| SHIFT | intervals disjoint **and** s⁺ < s⁻ | intervals disjoint **and** s⁺ > s⁻ | "A moved car is contradicted when its old position is clearly better supported than its new one." |

Otherwise: **neither** (no gate, not useful).

Why ADD and REMOVE are mirror images: ADD says "something **is** here" → contradicted by emptiness (low interval). REMOVE says "nothing is here" → contradicted by occupancy (high interval).

### The unit rule (paper Eq. 7)

  g_{i,u} = 1 [ KNOWN_{i,u} ∧ ∃ e ∈ E_{i,u} : gate(e) ∧ ∄ e ∈ E_{i,u} : useful(e) ]

In words: switch sender i off in tile u **only if** (1) the unit is KNOWN, (2) **at least one** effect is contradicted, and (3) **no** effect is confirmed. "If a sender adds one real car and one doubtful car in the same tile, it is kept" (paper §IV-C).

---

## 17. Full algorithm — step by step

Matches Algorithm 1 in the paper ("MINT for one receiver frame").

| # | Step | Input | Operation | Output | Why it matters | One-line viva sentence |
|---|---|---|---|---|---|---|
| 1 | Receive | f₀…f_{n−1}, own scan P₀ | Collect messages and own scan | All inputs | Defines what is trusted (P₀, pose) and untrusted (fᵢ) | "We take everyone's feature maps plus our own raw LiDAR." |
| 2 | Full output | all fᵢ | Y⁺ = Dec(Fuse(all)) | Y⁺ | The normal cooperative output to defend | "First we decode normally with all senders." |
| 3 | Counterfactual | all fᵢ except i | Y⁻(i) = Dec(Fuse(f_{j≠i})), for each sender i | Y⁻(1)…Y⁻(n−1) | Isolates each sender's influence | "Then we decode once without each sender." |
| 4 | Match | Y⁺, Y⁻(i) | Hungarian on BEV IoU, accept IoU ≥ 0.1 | matched pairs Mᵢ + unmatched boxes | Links "same car" across outputs | "We match boxes one-to-one by overlap." |
| 5 | Classify | matches | ADD / REMOVE / SHIFT (0.3 m, 10°) | effects Eᵢ | Names what the sender did | "Unmatched with-boxes are ADDs, unmatched without-boxes are REMOVEs, moved pairs are SHIFTs." |
| 6 | Localise | Eᵢ | Assign each effect to the 6.4 m tile of its box centre (SHIFT: both tiles) | E_{i,u} per unit | Decisions become local | "Each change goes into a 6.4-metre tile." |
| 7 | Count rays | effect boxes, P₀ | SUP and TRAV for each box core | SUP, TRAV, N per box | Physical evidence the sender can't forge | "We count our own rays that stop inside or pass through each box." |
| 8 | KNOWN? | N per box | KNOWN iff every box N ≥ 3 and none is the ego car | KNOWN / UNKNOWN | Avoids deciding without evidence | "With fewer than three rays, it's UNKNOWN." |
| 9 | Verdicts (KNOWN) | SUP, N | Wilson 95% → gate / useful / none per effect | verdicts | Only decide when evidence is resolvable | "A Wilson interval must be clearly on one side of one half." |
| 10 | Fallback (UNKNOWN) | — | g_{i,u} = 0 | keep | Protects honest unique views | "If we can't check, we keep the sender." |
| 11 | Unit gate | verdicts | g_{i,u} = 1 iff some gate and no useful | switched-off set S_u per tile | Switch off only clearly contradicted, not useful contributions | "We mute a sender in a tile only if something is contradicted and nothing is confirmed." |
| 12 | Compose | S_u, decodes | For each tile, take the pre-NMS candidates from the decode without S_u; then NMS | Y_MINT | Restores removed cars; removes fakes locally | "Each tile is rebuilt without its muted senders, then NMS gives the final boxes." |

Notes that are easy to get wrong:
- Tiles with no switched-off sender use the candidates of Y⁺ (C_u(∅)).
- "Because AttFuse fuses agents pixel by pixel and its head is local, this assembly equals a decode in which the switched-off senders are masked out in their tiles only; we checked this on every scenario of both evaluation sets" (paper §IV-D).
- "It re-uses the decodes of Eq. (2), so MINT costs one extra decode per sender" (paper §IV-D).
- All constants (0.5, three rays, 95%, tile size, matching thresholds) "were fixed on the design set and frozen before the validation and test data were opened" (paper §IV-D).
- **Not every change is treated the same:** ADD tests b⁺, REMOVE tests b⁻, SHIFT compares both.

### Pseudocode

```
function MINT(f[0..n-1], P0):
    Yplus = Dec(Fuse(f[0..n-1]))
    for each sender i in 1..n-1:
        Yminus[i] = Dec(Fuse(f without f[i]))
        E = effects(Yplus, Yminus[i])            # Hungarian, IoU>=0.1; ADD/REMOVE/SHIFT
        for each tile u touched by E:
            Eu = effects of E in tile u
            if any box in Eu has N<3 rays or is the ego car:
                g[i,u] = 0                       # UNKNOWN -> keep
            else:
                v = [verdict(e, P0) for e in Eu] # Wilson 95%: gate / useful / none
                g[i,u] = ("gate" in v) and ("useful" not in v)
    for each tile u:
        S = {i : g[i,u] == 1}
        C[u] = pre-NMS candidates in u from decode without senders S
    return NMS(union of C[u])
```

### Text flowchart

```
          ┌──────────── for each sender i ─────────────┐
 inputs ─► Y+ ──┐                                       │
          Y-(i)─┴─► match ─► ADD/REMOVE/SHIFT ─► tiles ─► count rays (own P0)
                                                          │
                                         N<3 or ego box? ─┼─ yes ─► UNKNOWN ─► KEEP
                                                          │
                                                         no ─► Wilson verdicts
                                                                │
                                   some gate AND no useful? ─── yes ─► switch i OFF in tile u
                                                                └─ no ─► KEEP
          └──────────────────────────────────────────────┘
 rebuild every tile without its switched-off senders ─► NMS ─► Y_MINT
```

### Tell it to the examiner in 45 seconds
> "For each frame, the receiver decodes once with all senders and once without each sender. It matches boxes between the two by bird's-eye-view overlap with the Hungarian algorithm. Unmatched boxes with the sender are ADDs, unmatched boxes without it are REMOVEs, moved boxes are SHIFTs. Each goes into a 6.4-metre tile. For each box, it counts its own LiDAR rays that stop inside — support — or pass through — traversal. Fewer than three rays: UNKNOWN, keep. Otherwise a Wilson 95% interval: an ADD is contradicted if the interval is below a half, a REMOVE if it's above a half. A sender is switched off in a tile only if something is contradicted and nothing is confirmed. Finally each tile is rebuilt without its switched-off senders."

### Worked example: one removed car, start to finish [TEACHING EXAMPLE]
1. **Setup.** n = 3 (receiver + senders 1, 2). A real car K sits 20 m ahead of the receiver in open road.
2. **Attack.** Sender 1 overwrites K's patch in its feature map with background (a "remove" attack).
3. **Y⁺** (all senders): K is **missing** (the attack worked).
4. **Y⁻(1)** (without sender 1): K is **present** (receiver + sender 2 still see it).
5. **Match.** K in Y⁻(1) has no partner in Y⁺ → **REMOVE** effect of sender 1.
6. **Tile.** K's centre falls in tile u = (3, 0) → unit (1, (3, 0)).
7. **Rays.** 9 receiver rays end inside K's core, 1 passes through → SUP = 9, TRAV = 1, N = 10 ≥ 3, not ego → **KNOWN**.
8. **Wilson.** a = 9, N = 10 → [0.60, 0.98]. lo = 0.60 > 0.5 → REMOVE **gates**.
9. **Other effects.** Sender 1 has no other effect in this tile, so none is useful.
10. **Unit gate.** g_{1,(3,0)} = 1 → sender 1 is switched off in tile (3, 0) only.
11. **Y⁻(2)** check: sender 2 caused no effect here → nothing to do.
12. **Compose.** Tile (3, 0) takes candidates from the decode without sender 1 → K is there. All other tiles take Y⁺ candidates → sender 1's other contributions are kept.
13. **Result.** K is **restored** in Y_MINT. A box filter on Y⁺ could not do this: K was never in Y⁺.

### The three hardest algorithm questions

**Q1. "If two senders both add the same fake car, does MINT catch it?"**
> "Probably not. Removing one sender at a time, the other still adds the fake, so neither counterfactual shows a change. That's why we assume one non-colluding attacker and list collusion as a limitation." (paper §VII-E)

**Q2. "Why is the tile-by-tile output correct? Couldn't switching a sender off in one tile change other tiles?"**
> "For AttFuse it is exact: fusion is per-pixel attention and the head is local, so masking a sender in one tile only changes that tile. We checked this on every scenario of both evaluation sets. For detectors that mix information across space, like V2X-ViT, it would need re-checking." (paper §IV-D, §VII-E)

**Q3. "Why does a unit need 'no useful effect' to be gated?"**
> "To protect senders that do useful work. If a sender adds one real car that our rays confirm and one doubtful car in the same tile, switching it off would lose the real car. So we only switch off when something is contradicted and nothing is confirmed." (paper §IV-C)

---

## 18. Baselines and alternatives (paper §IV-F)

"None of them has a parameter fitted on test data."

| Method | What it does | Evidence | Strength | Limitation | Difference from MINT |
|---|---|---|---|---|---|
| **No defense** | Uses Y⁺ as it is | none | Full benefit of cooperation | Fully exposed to attacks | Reference for every ΔAP |
| **Ego-only** | Drops all senders | receiver only | Cannot be attacked through messages | Gives up all of cooperation: clean ΔAP −21.21 (global) on test | MINT keeps senders except where contradicted |
| **B-NORM** | Drops sender i for the **whole frame** if, at any scale k, mean feature magnitude ratio \|fᵢ,ₖ\|/\|f₀,ₖ\| > τₖ (99.5th percentile on clean development frames; τ₁ = 1.020, τ₃ = 1.195) | feature statistics | Cheap; catches crude, large perturbations (100% of plain PGD attacker frames) | Stealth attack stays under the threshold (0% caught); 17.4% false flags on clean test frames; whole-sender decision | MINT uses physics, not statistics; decides per tile |
| **B-RAY** | Deletes every final box in Y⁺ that the receiver's rays resolvably show empty (KNOWN and Wilson hi < 0.5 — same test as MINT's ADD gate) | receiver's own rays | Cheap (no counterfactual decode; +4–11% median time on test at n = 2…≥4); handles added cars well | Can only delete boxes → cannot restore removed cars; doesn't say which sender | MINT tests each sender's changes, so it can also restore REMOVEs and localise |
| **MINT-noREMOVE** (ablation) | MINT, but a REMOVE effect can never gate (it can still be "useful") | receiver's own rays | Very few false switch-offs on clean frames (10 vs 521) | Loses the removal recovery (+0.07 vs +22.50 on strongest stealth removal) | Shows that the REMOVE test carries MINT's main benefit |

**On B-RAY specifically.** The paper says: "We claim no novelty for B-RAY. It is the pre-registered primary and the strongest simple competitor: it asks whether a box filter alone already does the job" (§IV-F). It is "in the style of CARLO and the local check of CAD".

**On B-NORM specifically.** It "stands in for the family of anomaly checks on features, in its simplest form" — its failure on stealth PGD is a weakness **of this simple detector under these tested conditions**, not proof that all feature-anomaly methods fail.

**On Ego-only.** Useful as a comparison because it shows the value of cooperation. Note one exception: at the strongest stealth removal, the attack destroys more than cooperation adds, so ego-only gains +19.19 (global) over no defense — but MINT reaches +22.50 **while keeping the benign senders** (paper §VI-B).
