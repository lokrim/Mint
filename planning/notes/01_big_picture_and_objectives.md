# Part 1 — The big picture

## 1. The project in the simplest possible way

### The story (for a school student) [ANALOGY]

Imagine a car driving down a road. It has a "laser eye" on its roof (a LiDAR) that tells it where things are. It uses this to spot other cars.

But the laser eye cannot see through things. A big bus is parked ahead. Behind the bus, a small car is about to pull out. Our car cannot see it.

Now imagine a second car, further up the road, on the other side of the bus. **That** car can see the hidden small car. The two cars can talk over the radio. The second car sends a message: "Here is what I see." Our car mixes that message with its own view, and now it "sees" the hidden car too. This is **cooperative perception**. It is like having a friend standing at the corner who shouts "car coming!"

Now the problem. What if the friend is lying — or has been hacked?

- It could say "there's a car here" when there is nothing. Our car might **brake for nothing** (a fake, or "phantom", car).
- It could hide a real car. Our car might **not see a real car** and crash into it.
- It could say a car is a little to the left of where it really is. Our car might **misjudge where it is**.

How can our car protect itself without simply ignoring its friend (and losing the useful warnings)?

**MINT's idea, in two steps:**

1. **"What did this friend change?"** Our car works out what it would see **with** the friend's message and what it would see **without** it. The difference is exactly what that friend changed: "you made a car appear here", "you made a car disappear there", "you moved this car".
2. **"Do my own eyes agree?"** For each change, our car checks its **own** laser. If the friend says "there is a car here", but our own laser beams fly straight through that spot and hit a wall behind it, then the spot is empty and the friend is contradicted. If the friend made a car disappear, but our own laser beams stop right on that spot, then something really is there and the friend is contradicted.

Our car switches off the friend's message **only in the small area where its own laser clearly contradicts it**. Everywhere else, and especially wherever our car cannot see at all, it keeps listening to the friend.

### What we are truly trying to achieve (one paragraph)

Cooperative perception makes self-driving cars safer because cars can share what they see. But a sender can send manipulated information that adds fake cars, hides real cars or moves cars in the receiver's view. Our project asks a specific question: **can the receiving car use its own LiDAR — evidence the sender cannot change — to check what each sender's message actually did to its detections, region by region, and undo only the changes that its own sensor clearly contradicts?** The goal is to make cooperative perception **more reliable** when some shared information may be wrong, while keeping as much useful shared information as possible. MINT does **not** guarantee security. In our own experiments it did not stop attacks placed where the receiver cannot see (paper §VI-D), and its advantage over a simpler filter depends on how accuracy is measured (paper §VI-A).

### One-sentence explanation

> MINT lets a self-driving car check each other car's shared message by comparing what it detects with and without that message, and then testing every change against its own laser sensor, so it can switch off a sender only in the small region where its own sensor clearly says the sender is wrong.

### 30-second oral explanation

> Connected cars share what their sensors see, so each car can detect objects hidden from its own view. But a hacked car can send manipulated data that makes fake cars appear, real cars disappear, or cars move. Our method, MINT, checks each sender separately. The receiver compares its detections with and without that sender, in small 6.4-metre squares of the map. Every difference is tested against the receiver's own LiDAR laser rays, which the sender cannot fake. The sender is switched off only in squares where the rays clearly contradict it. We tested this on the OPV2V simulated benchmark.

### 1-minute oral explanation

> Cooperative perception lets connected vehicles share learned feature maps from their LiDAR sensors, so a receiver can see around obstacles. The risk is that one sender can manipulate its feature map and add, remove or shift cars in the receiver's output. Confidence scores and agreement between cars cannot tell whether an object is physically there.
>
> Our method, MINT — Message INfluence Testing — works in three steps. First, for each sender, the receiver decodes the scene with and without that sender and records the differences: an added car, a removed car, or a moved car, each in a 6.4-metre tile. Second, it tests each difference with its own LiDAR rays: a ray that stops inside a box supports it, and a ray that passes through it says the space is empty. Third, it switches the sender off in that tile only if the rays clearly contradict it, using a Wilson 95% interval as a safety margin. If there are too few rays, it keeps the sender.
>
> On the OPV2V test set, under a pre-registered protocol, MINT was the only defense that clearly recovered removal attacks. Against the strongest stealth removal attack it restored 22.50 of the 40.41 lost AP points. But whether it beats a simpler ray-based box filter depends on how AP is computed.

### 3-minute oral explanation

> **Problem.** A single vehicle sees only what its sensors can reach. A truck or a corner can hide a car. In cooperative perception, connected vehicles share information. The most common design is intermediate fusion: each vehicle turns its LiDAR scan into a bird's-eye-view feature map — a grid of numbers that summarises the scene seen from above — and the receiver combines all these maps and then detects 3D boxes around cars.
>
> Sharing means trusting. A malicious or faulty sender can change its feature map. Through the fusion, it can add a car that does not exist, remove a real car, or shift a car. A fake car can cause sudden braking; a missing car can cause a crash.
>
> **Why it is hard.** First, a feature map is not human-readable, and a manipulated map can still produce confident detections. Second, an honest sender is useful precisely because it sees what the receiver cannot — so disagreeing with the receiver is not proof of an attack. Third, a defense that only deletes suspicious boxes can never bring back a car that was removed.
>
> **Our method, MINT.** For each sender, the receiver runs its detector twice: once with all senders, once without that one sender. The difference between the two outputs is that sender's influence. We match boxes between the two outputs with the Hungarian algorithm on bird's-eye-view overlap, and classify differences as ADD, REMOVE or SHIFT. We assign each difference to a 6.4-metre tile, so we can decide locally. Then we test each difference using the receiver's own LiDAR rays. A ray that ends inside a box is support; a ray that passes through and ends behind it is traversal. We compute the share of support rays and put a Wilson 95% interval around it. An added car is contradicted if the interval is entirely below one half. A removed car is contradicted if the interval is entirely above one half — something really is there. If any box has fewer than three informative rays, the result is UNKNOWN and we keep the sender. The sender is switched off in a tile only if at least one change is contradicted and none is confirmed. Then each tile is decoded without its switched-off senders.
>
> **Evaluation.** We used the released AttFuse detector unchanged, on the OPV2V test set — 15 scenarios, 2,066 frames, 12 conditions: clean plus 11 attacks, including PGD and stealth PGD. We also ran a second test on an unseen simulated town, Culver City. We compared with no defense, ego-only, a feature-norm check B-NORM, and a ray-based box filter B-RAY. Everything was pre-registered and the test was run once.
>
> **Results.** A simple box filter already helps. MINT clearly helps against removal: against the strongest stealth removal it gained 22.50 AP points, recovering about 56% of the loss, while the box filter gained nothing. But MINT versus B-RAY depends on the AP definition: +0.31 points for MINT under global-ranking AP, but −0.57 under the benchmark's default frame-order AP. Attacks placed where the receiver cannot see were not defended by anyone. MINT also costs extra computation — about 20% at two vehicles and 123% at four or more on our CPU.
>
> **Conclusion.** Physical evidence from the receiver's own sensor can make shared perception more trustworthy, especially against removal attacks, but it is not a complete solution.

### Non-technical version (for a parent or a general audience)

> Self-driving cars can "talk" to each other and share what they see, like friends warning each other about a car around the corner. But if one car is hacked, it could lie — invent a car that isn't there, or hide one that is. Our project gives each car a way to fact-check its friends. It asks: "What did this friend's message change in what I see?" and then "Does my own laser sensor agree?" It ignores a friend only in the small spot where its own sensor clearly proves the friend wrong, and keeps listening everywhere else. We tested this in a driving simulator. It worked best against the "hiding a real car" kind of lie, but it is not perfect — it can't check places its own sensor cannot see, and it makes the computer work harder.

### Technical version (for a faculty evaluator)

> MINT is a receiver-side defense for intermediate-fusion cooperative LiDAR perception. Given BEV feature maps from n−1 senders, the receiver computes the fused output Y⁺ and, for each sender i, a leave-one-out counterfactual Y⁻(i). Boxes are matched one-to-one by Hungarian assignment on BEV IoU (match if IoU ≥ 0.1); unmatched boxes in Y⁺ are ADD effects, unmatched boxes in Y⁻(i) are REMOVE effects, and matched pairs with a centre displacement above 0.3 m or heading change above 10° are SHIFT effects. Effects are localised to 6.4 m tiles; the decision unit is the sender–tile pair (i, u). Each effect box is tested against the receiver's own point cloud by counting rays that end inside the box core (SUP) or pass through it and end behind (TRAV). A unit is KNOWN only if every effect box has at least 3 informative rays and none is the ego vehicle. On KNOWN units, a Wilson 95% interval on SUP/(SUP+TRAV) decides: ADD gates if hi < 0.5, REMOVE gates if lo > 0.5, SHIFT gates if the two intervals are disjoint and the old position is better supported. A unit gates if some effect gates and none is resolvably useful. The final output composes each tile's pre-NMS candidates from the decode without its gated senders; for AttFuse's per-pixel fusion this equals tile-masked fusion. Evaluated once under a pre-registered protocol on OPV2V test (15 scenarios, 2,066 frames, 12 conditions) with the released AttFuse checkpoint, and descriptively on Culver City (4 scenarios, 550 frames), with scenario-bootstrap CIs and Holm-corrected one-sided tests, under both global-ranking and frame-order AP.

---

## 2. The five objectives

> **Note [SOURCE check].** The paper has no section called "Objectives". It has a research question (paper §I: "whether such a receiver-grounded, counterfactual test makes cooperative perception more robust, and under which conditions it does or does not") and three contributions (Method, Evaluation, Findings). The five objectives below are written from those, so that each one maps to something the paper actually does. You can present them as "the objectives of our project".

### Objective vs method vs result — know the difference

- An **objective** is **what we set out to investigate or achieve**. ("Find out whether X helps.")
- A **method** is **how we do it**. ("Compare outputs with and without each sender.")
- A **result** is **what we found**. ("It helped against removal attacks, but not against attacks in blind regions.")

An objective does **not** mean we fully achieved it. For example, Objective 4 asked whether MINT improves robustness; the honest result is "yes against removal; against the simpler box filter it depends on the metric".

---

### Objective 1 — Measure each sender's influence

1. **Statement.** To measure how much each individual sender changes the receiver's 3D detections, by comparing the receiver's output with and without that sender.
2. **In simple English.** Find out exactly what each other car's message did to what our car sees.
3. **Why it matters.** When all messages are mixed together, the receiver cannot tell which sender caused which detection. Without this, it can only trust or reject everything.
4. **How MINT addresses it.** Counterfactual attribution: compute Y⁺ (all senders) and Y⁻(i) (all except sender i), then compare (paper §IV-A, Eq. 1–2).
5. **How it is evaluated.** Not scored on its own; it is the first stage of the pipeline. A correctness check was done: the tile-by-tile output equals a decode with switched-off senders masked in their tiles, "checked on every scenario of both evaluation sets" (paper §IV-D). Fusion locality held in 93/93 tile tests during development (`planning/stage1_spike_report.md`).
6. **Viva answer.** "Our first objective was to measure what each sender actually changes. We do this with a counterfactual: we decode the scene with all senders and again without one sender. The difference is that sender's influence. It doesn't prove the sender is malicious; it tells us what to check."

### Objective 2 — Identify suspicious ADD, REMOVE and SHIFT effects

1. **Statement.** To classify each sender's influence into three types — added objects (ADD), removed objects (REMOVE) and moved objects (SHIFT) — and localise them to small map tiles.
2. **In simple English.** Sort the changes into "made a car appear", "made a car disappear", and "moved a car", and note where on the map each one happened.
3. **Why it matters.** The three attack goals in the threat model are exactly these three (paper §III-B). Each needs a different physical test. Localising means a local attack only costs local information.
4. **How MINT addresses it.** Hungarian matching on BEV IoU ≥ 0.1; ADD = unmatched in Y⁺; REMOVE = unmatched in Y⁻(i); SHIFT = matched but centre moved > 0.3 m or heading > 10°; each effect assigned to the 6.4 m tile containing its box centre (paper §IV-A, Eq. 3).
5. **How it is evaluated.** Indirectly, through the ablation MINT-noREMOVE: removing the REMOVE rule collapses the recovery on the strongest removal attack from +22.50 to +0.07 AP points (paper §VI-C). This shows that detecting REMOVE effects is what carries the recovery.
6. **Viva answer.** "Our second objective was to identify what kind of change each sender made. If a box exists only with the sender, it is an ADD. If it exists only without the sender, the sender REMOVED it. If it exists in both but moved, it is a SHIFT. We assign each to a 6.4-metre tile so we can decide locally."

### Objective 3 — Verify suspicious changes with the receiver's own LiDAR

1. **Statement.** To test each change against physical evidence from the receiver's own LiDAR rays, and to act only when that evidence is clear, keeping the sender when evidence is insufficient.
2. **In simple English.** Check every change with our own laser. Only act when our laser clearly disagrees. If we can't see, don't punish the sender.
3. **Why it matters.** The sender can edit its message, but it cannot change where the receiver's own laser beams stop (paper §II-D, §VII-A). Agreement-based checks can't tell whether an object physically exists.
4. **How MINT addresses it.** Count SUP and TRAV rays; KNOWN if every effect box has N ≥ 3 informative rays and none is the ego vehicle; Wilson 95% interval; gate rules per effect type; UNKNOWN = keep (paper §IV-B, §IV-C).
5. **How it is evaluated.** Through robustness results (Objective 4), the clean-frame cost (false switch-offs: 521 useful units switched off out of 718 switched off, 8,160 units in total, on clean test frames; paper §VI-C), and the receiver-blind attack, which tests the limit of the evidence (paper §VI-D).
6. **Viva answer.** "Our third objective was to verify each change with evidence the sender can't fake: the receiver's own laser rays. A ray that stops inside a box supports it; a ray that passes through it shows empty space. We only act when a Wilson 95% interval is clearly on one side of one half. If there are fewer than three rays, we say UNKNOWN and keep the sender."

### Objective 4 — Evaluate robustness against attacks and compare with baselines

1. **Statement.** To evaluate, under a pre-registered one-time protocol, whether MINT improves detection accuracy under attack compared with no defense, ego-only perception, a feature-norm check (B-NORM) and a ray-based box filter (B-RAY).
2. **In simple English.** Test fairly whether MINT actually helps, and whether it beats simpler ideas.
3. **Why it matters.** A defense idea is only worth something if it is tested against realistic and strong attacks, against simple competitors, on data it was not tuned on.
4. **How MINT addresses it.** OPV2V test (15 scenarios, 2,066 frames, 12 conditions) as primary; Culver City (4 scenarios, 550 frames) as secondary; ΔAP@0.7 vs no defense; scenario bootstrap; Holm correction; pre-registered statements (paper §V).
5. **How it is evaluated.** Mean ΔAP@0.7 over the four original attacks; per-condition ΔAP; recovery; paired difference MINT − B-RAY (paper §VI-A, §VI-B).
6. **Viva answer.** "Our fourth objective was a fair, pre-registered evaluation. We fixed every method, threshold and attack before opening the test data, and ran the test once. We compared against no defense, ego-only, a feature-norm check and a ray-based box filter, under 12 conditions including stealth PGD attacks."

### Objective 5 — Understand the trade-offs

1. **Statement.** To quantify MINT's costs and limits: accuracy lost on clean frames, extra computation, sensitivity of conclusions to the AP definition, and regions the receiver cannot verify.
2. **In simple English.** Be honest about what MINT costs and where it doesn't work.
3. **Why it matters.** A defense that damages normal driving, is too slow, or only looks good under one metric is not useful. Knowing the limits tells future work where to go.
4. **How MINT addresses it.** Reports both AP definitions; clean relative loss; false switch-offs; runtime p50/p95 by number of agents; receiver-blind attack and visibility-limited oracle (paper §VI-D, §VI-E, §VII).
5. **How it is evaluated.** Clean relative loss (MINT: −0.16% global, 0.62% frame-order); runtime (+20% / +53% / +123% median at n = 2 / 3 / ≥4); MINT − B-RAY: +0.31 (global) vs −0.57 (frame-order); receiver-blind: no defense recovers more than 0.10 of the loss.
6. **Viva answer.** "Our fifth objective was to understand the trade-offs. MINT costs extra computation because it decodes once per sender — about 20% extra at two vehicles, 123% at four or more on our CPU. It switches off some useful information on clean frames. And its ranking against the simple box filter reverses between the two AP definitions — that's a finding in itself."

### Memorise this list

1. Measure each sender's influence (with vs without).
2. Classify it as ADD / REMOVE / SHIFT, per 6.4 m tile.
3. Verify it with the receiver's own LiDAR rays; keep when UNKNOWN.
4. Evaluate robustness fairly against baselines, pre-registered, one-time test.
5. Quantify trade-offs: clean cost, computation, metric sensitivity, blind regions.

---

## 3. Core vocabulary for absolute beginners

| Term | Very simple definition | In our project | Example / analogy |
|---|---|---|---|
| **V2X** | "Vehicle-to-everything": a vehicle talking by radio to other vehicles, traffic lights, roadside units. | We study **V2V** (vehicle to vehicle), a part of V2X. OPV2V is a V2V dataset. | Cars texting each other. |
| **Cooperative perception** | Several vehicles combine what their sensors see, so each sees more. | The whole setting of the project. | Friends at different corners describing the street to you. |
| **Ego vehicle / receiver** | The car doing the detecting — "me". | Agent 0. The only party MINT trusts (its own LiDAR and pose). | You, standing at your corner. |
| **Sender / collaborator** | Another car that sends its information to the receiver. | Agents 1…n−1. In experiments, the attacker is always sender 1. | The friends shouting to you. |
| **LiDAR** | A sensor that sends out laser pulses and measures how far they travel before bouncing back. | Every car has one; the receiver's LiDAR is the trusted evidence. | A bat's echolocation, but with light. |
| **Point cloud** | The set of 3D points where the laser pulses hit something. | The receiver's own scan is called P₀. | A "dot drawing" of the surroundings. |
| **Feature map** | A grid of numbers produced by a neural network that summarises useful patterns in the data. Not a photo. | Each car turns its point cloud into BEV feature maps at three scales and sends them. Each message is about 15.8 MB (`planning/README.md`). | A compressed summary note, written in a code only the network understands. |
| **Feature fusion** | Combining feature maps from several cars into one. | AttFuse: per-pixel attention fusion (paper §III-A). | Merging several friends' notes into one. |
| **Intermediate fusion** | Sharing feature maps (in the middle of the network), not raw points (early fusion) or final boxes (late fusion). | Our setting; the most common design (paper §II-A). | Sharing summary notes, not raw photos or final conclusions. |
| **Detection head (Dec)** | The last part of the network that turns the fused feature map into boxes with scores. | "Dec" in the equations. | The person who reads the merged note and says "car here, car there". |
| **3D bounding box** | A box drawn around an object: centre position, size, heading (direction). | Every detection is a box. | A shoebox placed around each car. |
| **Adversarial attack** | Deliberately changing input so an AI makes a mistake. | The attacker edits its feature maps or points. | Writing a fake note to mislead you. |
| **Phantom object** | A fake detection of something that isn't there. | Created by spoof attacks → ADD effects. | A "ghost car". |
| **ADD** | A box that exists only **with** the sender. | Effect type; tested for "is it really there?" | Friend says "car here"; without friend, you'd see none. |
| **REMOVE** | A box that exists only **without** the sender. | Effect type; tested for "was something really there?" | Without friend, you'd see a car; with friend, it vanishes. |
| **SHIFT** | A box that exists in both but moved > 0.3 m or turned > 10°. | Effect type; compares old vs new position. | Friend says the car is two steps to the left. |
| **Counterfactual** | "What would have happened if…" — the same situation with one thing changed. | Y⁻(i): the output if sender i had stayed silent. | "What would the group decide if Ravi weren't in the meeting?" |
| **Gating** | Switching a contribution off. | g_{i,u} = 1 means sender i is switched off in tile u. | Muting one friend for one part of the map. |
| **Support ray (SUP)** | A receiver laser ray that **ends inside** a box. | Evidence that something is there. | You throw a ball at the spot and it bounces off something. |
| **Traversal ray (TRAV)** | A receiver laser ray that **passes through** a box and ends **behind** it. | Evidence that the box is empty. | The ball flies through the spot and hits the wall behind. |
| **KNOWN evidence** | Enough informative rays (≥ 3 for every effect box, none is the ego car). | MINT may decide. | You've thrown enough balls to judge. |
| **UNKNOWN evidence** | Too few rays (< 3) or the box is the receiver itself. | MINT keeps the sender. | You couldn't throw at that spot — you don't punish your friend. |
| **BEV** | Bird's-eye view: looking down from above. | Feature maps, tiles and IoU are all in BEV. | A map on a table. |
| **IoU** | Intersection over Union: overlapping area ÷ total covered area of two boxes. 1 = identical, 0 = no overlap. | Matching (≥ 0.1) and scoring (≥ 0.7). | Two stickers on a map: how much do they overlap? |
| **Hungarian assignment** | An algorithm that pairs items one-to-one in the best overall way. | Pairs boxes in Y⁺ with boxes in Y⁻(i). | Pairing dancers so that the total "fit" is best and nobody has two partners. |
| **AP (Average Precision)** | One number (0–1, or 0–100 "AP points") summarising how accurate and complete the detections are. Higher is better. | Main accuracy measure. | An exam score for the detector. |
| **AP@0.7** | AP where a detection counts as correct only if IoU with a real car ≥ 0.7. | Used everywhere in the paper. | Strict marking: the box must fit tightly. |
| **ΔAP** | AP of a defense minus AP of no defense, on the same frames. Positive = helps. | Main measure of benefit (paper Eq. 9). | "How many marks did the tutor add?" |
| **Baseline** | A simple reference method to compare with. | No defense, ego-only, B-NORM, B-RAY. | The "control group". |
| **Stealth attack** | An attack designed to avoid a specific detector. | Stealth PGD keeps feature magnitude under B-NORM's threshold. | A thief who walks slowly so the motion sensor doesn't trigger. |
| **PGD** | Projected Gradient Descent: repeatedly nudge the input in the direction that most hurts the model, then pull it back inside an allowed limit. | 10 steps on the attacker's features, limit r·σ_k (paper §V-B, App. A). | Adjusting a lie step by step to be maximally convincing, without making it too extreme. |
| **False positive** | A detection that isn't a real object (or a wrong alarm). | Phantom cars; B-NORM flagging a benign sender. | A fire alarm with no fire. |
| **Computational overhead** | Extra time the defense adds. | MINT: +20% to +123% median vs receiver-only perception (paper §VI-E). | A security check that slows the queue. |
| **Wilson confidence interval** | A range of plausible values for a proportion, which behaves well even with few samples. | Around SUP/(SUP+TRAV), at 95% (z = 1.96). Read as a "resolvability margin", not a probability (paper §IV-B). | "Between 30% and 90% of throws hit" — too wide to decide. |
| **Global-ranking AP** | AP computed after sorting all detections of the whole dataset by confidence. | Headline AP in the paper. | Ranking all students in the country by score. |
| **Frame-order AP** | AP computed by going through frames in order (OpenCOOD default). | OPV2V-comparable AP. | Marking papers in the order they were handed in. |
| **Scenario / frame** | Scenario = one recorded drive (a short simulation). Frame = one moment (one LiDAR sweep) in it. | Test: 15 scenarios, 2,066 frames. | A video clip, and one picture from it. |
| **Pre-registration** | Writing down and committing your methods, thresholds and analysis before looking at test data. | Done for the OPV2V test and Culver City (paper §V-D). | Sealing your prediction in an envelope before the match. |
| **Bootstrap** | Estimating uncertainty by re-sampling your data many times. | Scenario bootstrap, B = 2000 (paper §V-D). | Re-drawing the class many times from the register to see how much the average varies. |
