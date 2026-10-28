# Part 6 — Viva preparation

Format: **Q** → **Short answer** → *Why/how (longer)* → Follow-up → ⚠️ warning where a detail must be exact.

---

## 30. Question bank

### 1. Basic understanding

**Q1. What is your project in one sentence?**
A receiver-side defense for cooperative LiDAR perception that checks what each sender changed, tile by tile, against the receiver's own laser rays, and switches a sender off only where the rays clearly contradict it.

**Q2. What does MINT stand for?**
Message INfluence Testing. *(Old internal name of the method: R1. Early project name "Multi-agent Inbound Node Trust" was dropped.)*

**Q3. What problem are you solving?**
A malicious sender in cooperative perception can add, remove or move cars in the receiver's detections. We want the receiver to resist this without throwing away useful shared information.
*Why:* a phantom car can cause needless braking; a missing car can cause a collision (paper §I).

**Q4. Who benefits?**
Connected automated vehicles that use intermediate-fusion cooperative perception. In our study, the receiving vehicle.

**Q5. Is this a real car system?**
No. Everything is in simulation (OPV2V, made with CARLA). No real vehicles or real sensors.

### 2. Introduction and problem

**Q6. Why can't one car see everything?**
Light travels in straight lines; trucks, buses and corners block LiDAR (occlusion).

**Q7. What is intermediate fusion and why use it?**
Sharing learned BEV feature maps instead of raw points or final boxes. It balances accuracy and bandwidth, and is the most common design in recent work (paper §II-A).

**Q8. Why doesn't encryption solve this?**
The attacker is an authenticated insider. "The message is genuine, but its content is wrong" (paper §III-B). Crypto proves who sent it, not that it's true.

**Q9. Why is detection confidence not enough?**
A manipulated feature map can produce detections with high confidence (paper §I).

**Q10. Why is disagreement with the receiver not enough?**
An honest sender is useful precisely because it sees what the receiver can't — so it disagrees most. And an attacker close to the receiver's view may look normal (paper §II-C).

### 3. Objectives and research gap

**Q11. What are your objectives?**
(1) Measure each sender's influence; (2) classify it as ADD/REMOVE/SHIFT per tile; (3) verify with the receiver's own LiDAR, keeping when UNKNOWN; (4) evaluate fairly against baselines; (5) quantify trade-offs.
⚠️ The paper has no "Objectives" section; these are derived from its research question and contributions.

**Q12. What is the research gap?**
Consensus/anomaly defenses decide per whole agent using agreement; ray-based checks use physics but act on final boxes and can't restore removed cars. Missing: a per-sender, per-region test of what a sender changed, judged by the receiver's own rays.

**Q13. Is MINT completely new?**
No. "Neither of its ingredients is new on its own" (paper §II-E). The with/without question appears in ROBOSAC and MADE; ray checks in CARLO and CAD. What's new is their combination at sender × tile level, with physics instead of agreement, and the explicit UNKNOWN = keep rule.
⚠️ Don't say "no one has done this before". Novelty statements in the planning files are "to our knowledge".

### 4. Related work

**Q14. Name the two main families of prior defenses.**
Consensus/anomaly (ROBOSAC, MADE, CP-Guard, GCP, GLST, LUCIA, MATE, Latent Guardian) and sensor-grounded verification (CARLO, Shadow-Catcher, CAD).

**Q15. How is MINT different from MADE?**
MADE also compares outputs with and without each agent, but decides per **agent** and uses a reconstruction loss and conformal p-values. MINT decides per **sender and tile**, and judges each change with the receiver's own LiDAR rays.

**Q16. How is MINT different from CARLO / CAD?**
CARLO checks a detected box against the vehicle's own free space; CAD uses shared occupancy maps per region. Applied to final boxes, they can delete fakes but can't restore removed cars or say which sender caused an error. MINT applies the ray test to each sender's counterfactual changes.

**Q17. Did you compare experimentally with LUCIA, MADE or CP-Guard?**
**No.** "We did not run learned or consensus defenses, and make no claim relative to them" (paper §VII-E). B-NORM is the only feature-statistics stand-in.

### 5. Methodology and counterfactual

**Q18. Explain the counterfactual.**
Y⁺ = decode with all senders; Y⁻(i) = decode without sender i. The detector is not retrained; fusion gets one map fewer. Differences are sender i's influence.

**Q19. How can an output change reveal a sender's influence?**
Because the only thing that changed between the two decodes is whether sender i's map was included. So any difference is caused by that map.

**Q20. Does a detected change prove an attack?**
No. Honest senders change the output too — that's the point of cooperation. A change is a **claim** to be tested with the rays.

**Q21. Why is the counterfactual needed — why not just check final boxes?**
Final boxes can only show fakes. A removed car isn't in the final output, so a box check never sees it. The counterfactual shows "what would have been there", which the rays can then confirm (paper §VII-A). Also, it tells which sender caused the change.

**Q22. Why not reject the entire sender?**
Attacks are often local. Rejecting the whole sender "stops the attack but also discards everything useful it sent" (§II-C). Ego-only (rejecting everyone) costs ≈ 20 AP points even on clean frames.

**Q23. What does MINT trust?**
Only the receiver's own LiDAR scan and pose. It never sees ground truth.

**Q24. Why is MINT exact tile by tile?**
AttFuse fuses per pixel with attention and its head is local, so masking a sender in one tile changes only that tile. Checked on every scenario of both evaluation sets (§IV-D). Fusion locality held in 93/93 development tile tests.
Follow-up: *Other detectors?* — Ones that mix information across space (e.g. V2X-ViT) would need re-checking.

**Q25. What is the cost of the counterfactual?**
One extra decode per sender (§IV-D). Median overhead +20% (n = 2), +53% (n = 3), +123% (n ≥ 4) on an M1 CPU.

### 6. ADD, REMOVE, SHIFT

**Q26. Define ADD, REMOVE and SHIFT.**
ADD: box in Y⁺ unmatched in Y⁻(i). REMOVE: box in Y⁻(i) unmatched in Y⁺. SHIFT: matched pair with centre moved > 0.3 m or heading > 10° (ignoring a 180° flip).

**Q27. How do you match boxes?**
Hungarian algorithm on BEV IoU; a match needs IoU ≥ 0.1 (§IV-A; `src/mint/effects/effects.py`).
Follow-up: *Why so low?* — So a moved car is still matched and becomes a SHIFT, rather than a REMOVE plus an ADD. [INTERPRETATION]

**Q28. Why are ADD and REMOVE handled differently?**
They claim opposite things. ADD claims "something is here" → contradicted when rays pass through (hi(s⁺) < 0.5). REMOVE claims "nothing is here" → contradicted when rays stop on it (lo(s⁻) > 0.5). ADD tests the box in Y⁺; REMOVE tests the box in Y⁻(i).

**Q29. What is the tile size and why tiles?**
6.4 m. Decisions are per (sender, tile), so a local attack costs only local information.
⚠️ Attack patches use a 3.2 m grid — don't confuse it with the 6.4 m tile.

### 7. LiDAR, SUP, TRAV, UNKNOWN

**Q30. What are SUP and TRAV?**
SUP: a receiver ray that ends inside the box core (something is there). TRAV: a ray that passes through and ends behind (empty space). Rays ending before the box are blocked and ignored; rays with no return are never TRAV.

**Q31. Why is "no return" not counted as traversal?**
"A missing return does not prove free space" (§IV-B) — e.g. dark or glass surfaces may not reflect.

**Q32. What is KNOWN vs UNKNOWN?**
KNOWN: every effect box in the unit has ≥ 3 informative rays (SUP + TRAV) and none is the receiver's own vehicle. Otherwise UNKNOWN → keep.

**Q33. Why is UNKNOWN not treated as false?**
"I don't have enough evidence" isn't "the object is fake". The most valuable honest information is about places the receiver can't see. Switching those off would destroy the benefit of cooperation.

**Q34. What if the receiver cannot see the object?**
Then MINT can't judge it and keeps the sender. That's why the receiver-blind spoof succeeded: 1,381 of 1,412 realized blind spoofs had < 3 receiver rays, and no defense recovered more than 0.10 of its loss (§VI-D).

### 8. Wilson interval and gating

**Q35. What does the Wilson interval add over a simple ratio?**
Caution with few rays. 2/3 and 40/60 are both 0.67, but only the second is resolvably above 0.5. The interval is wide for few rays and narrow for many.

**Q36. Why z = 1.96?**
It gives the 95% level of a normal distribution.

**Q37. Is the interval a probability that the car exists?**
No. Rays on the same object aren't independent trials, so the paper reads it as a **resolvability margin**, not a probability (§IV-B).

**Q38. What is the minimum number of rays to call a box empty?**
Four. 0 SUP out of 3 gives hi = 0.56 (not < 0.5); 0 out of 4 gives hi = 0.49 (§IV-B).

**Q39. When is a unit switched off?**
When it's KNOWN, at least one effect gates, and no effect is resolvably useful (Eq. 7).

**Q40. What is the SHIFT rule?**
Gate if the two Wilson intervals (old and new box) don't overlap and the old position is better supported (s⁺ < s⁻). Useful if they don't overlap and the new position is better supported.

**Q41. Where did 0.5, 3 rays, 95% and 6.4 m come from?**
Fixed on the design set and frozen before the validation and test data were opened (§IV-D). None was fitted on test data.

### 9. Data, attacks, baselines, design

**Q42. Which dataset?**
OPV2V test: 15 scenarios, 2,066 frames, primary. Culver City (an OPV2V town unseen by the detector): 4 scenarios, 550 frames, secondary. Never pooled.

**Q43. Why 15 and not 16 test scenarios?**
One test scenario had been opened during an early feasibility spike, so it was moved to development (paper §V-A; Q&A B2).

**Q44. What are the 12 conditions?**
Clean + 5 copy-paste (spoof feature, remove feature, shift feature, spoof points, receiver-blind spoof) + 6 PGD (plain untargeted r = 0.25, plain remove r = 0.25, stealth untargeted r = 0.5, stealth remove r = 0.25, stealth untargeted r = 1.0†, stealth remove r = 1.0†).

**Q45. What is PGD?**
Projected gradient descent: repeatedly nudge the attacker's features in the direction that most hurts the detector, then clip back into an allowed range. Here 10 steps, step ε/4, ε = r × σ (σ = std. of clean sender features).

**Q46. What makes an attack "stealth"?**
It's projected after every step to keep mean feature magnitude below 0.95 × B-NORM's threshold, so B-NORM can't see it by construction.

**Q47. Is any attack adaptive to MINT?**
Partly: the receiver-blind spoof targets MINT's known blind spot. But no attack was optimised against the ray test itself — a stated limitation.

**Q48. Who is the attacker in your experiments?**
Always sender 1, one per frame; the defenses aren't told.

**Q49. What are the baselines?**
No defense, ego-only, B-NORM (feature-norm check), B-RAY (ray box filter), plus the ablation MINT-noREMOVE.

**Q50. Why is B-RAY the primary hypothesis and not MINT?**
A rule fixed in advance: if MINT didn't beat B-RAY on the validation set (frame-order), B-RAY would become primary. It didn't (−0.56), so B-RAY became primary and MINT vs B-RAY the key secondary (§V-D, App. C).
Follow-up: *Isn't that a failure?* — It's the honest result of a pre-registered rule. It means the headline "pass" belongs to the known baseline, and MINT's claims are about removal recovery and the AP-definition-dependent comparison.

**Q51. What is pre-registration and why?**
Committing all methods, thresholds, attacks and analyses before opening the test, then running it once. It prevents tuning the evaluation in our favour (§V-D).

**Q52. Why a scenario bootstrap?**
Frames in one scenario are correlated; resampling whole scenarios is the honest unit of independence.

**Q53. Why Holm correction?**
We test two methods (B-RAY and MINT) against no defense; Holm controls the chance of any false "significant" among them.

### 10. Results and metrics

**Q54. What is AP@0.7?**
Average precision for cars, where a detection is correct only if IoU with a real car ≥ 0.7. Higher is better.

**Q55. Define ΔAP.**
AP of the defense minus AP of no defense on the same frames and condition. Positive = helps. Not a count of cars.

**Q56. What is your headline result?**
Pre-registered: B-RAY passes under both AP definitions (+0.15 G, +0.76 F on the four original attacks). MINT: +0.45 G (significant), +0.19 F (not significant). MINT − B-RAY: +0.31 G, −0.57 F.

**Q57. What is MINT's strongest result?**
Strongest stealth removal: loss 40.41 points; MINT +22.50 (recovery 0.56); B-RAY −0.01. Culver City: +19.53 (recovery 0.49).
⚠️ That condition was added after development results (†), so it's descriptive, not confirmatory. And 40.41 is the loss, not what MINT recovered.

**Q58. Why might the metric change the ranking?**
Global ranking puts low-score errors at the end of one list (cheap); frame order charges them at their frame and lowers precision of all later frames. B-RAY deletes low-score fakes (helps most under frame order); MINT's false switch-offs remove some correct boxes (costs most under frame order).

**Q59. Which AP definition is right?**
Neither is wrong; they weight errors differently. Frame order is OpenCOOD's default (comparable with OPV2V papers); global ranking is the PASCAL VOC style. We report both.

**Q60. Why are the gains so small (0.15–0.76 points)?**
The four original attacks cost little averaged over all frames (0.27–1.97 points G) because many attempts don't change the output. The strong attacks separate the methods clearly (§VI-A).

**Q61. What did B-NORM do?**
Caught 100% of plain PGD attacker frames, 0% of stealth PGD; falsely flagged the honest sender on 17.4% of clean test frames (1.6% on development); mean ΔAP −5.85 G on the original attacks; clean ΔAP −6.13 G.

**Q62. What does MINT cost on clean frames?**
Relative clean loss −0.16% G (a tiny gain), 0.62% F (CI up to 1.75%). It switched off 718 of 8,160 units on clean test frames; 521 were useful by ground-truth labels, 512 of those from REMOVE verdicts.

**Q63. What does the ablation show?**
Without REMOVE, the strongest-removal gain drops from +22.50 to +0.07, and false switch-offs drop from 521 to 10. The REMOVE test is "both MINT's strength and its main cost" (§VI-C).

### 11. Discussion, limitations, future work

**Q64. Does the result prove MINT works in real vehicles?**
No. All data are simulated; Culver City is a new town, not real sensors. One detector, one attacker. Real-sensor validation is future work.

**Q65. What is the biggest limitation?**
It can only judge what the receiver can see; attacks in blind regions pass (no defense recovered more than 0.10 of the receiver-blind spoof). Close second: its advantage over the simple box filter is AP-definition-dependent.

**Q66. What if two senders collude?**
Both could add the same fake; removing one at a time leaves it in place. Not tested (§VII-E).

**Q67. Could an attacker fool the ray test?**
Possibly, e.g. by placing fakes where fewer than four rays cross them. No attack was optimised against the ray test (§VII-E).

**Q68. Is it real-time?**
Not as implemented on CPU: +20% to +123% median. A cheaper triggered variant exists but wasn't exact on development data, so no accuracy number uses it. GPU timing not measured.

**Q69. What would you do next?**
Hybrid (B-RAY for added cars + MINT REMOVE test), real-sensor data (V2V4Real, Mixed Signals), ray-aware and colluding attackers, evidence for blind regions, cheaper counterfactual.

**Q70. Why was the "calibrated probability" from your early plan dropped?**
Calibration needed a separate calibration set; the small set planned for it became the held-out validation set instead. So the Wilson interval is used only as a resolvability margin (App. C; Q&A C7).

### 12. Our group's contribution

**Q71. What exactly did your group implement versus use?**
*Implemented (per the repository):* MINT (effects, ray geometry, decision rule, tile composition), B-RAY, B-NORM, ego-only, the ablation, all attacks including PGD and stealth PGD, ground-truth harm labels, the pre-registration, the evaluation runs, statistics, report and paper.
*Used from others:* the OPV2V dataset, the OpenCOOD framework, the released AttFuse checkpoint (unchanged, never retrained), PGD as a known algorithm, and the ray-check idea from CARLO/CAD.

**Q72. Did you train a model?**
No. We used OpenCOOD's released AttFuse checkpoint and verified it reproduces the published test AP@0.7 (0.8155 vs 0.815).

**Q73. Did you run the experiments yourselves?**
Yes — the repository contains the runs (`runs/20261024-E5v3/` for the OPV2V test, `runs/20261026-CULVER/` for Culver City). About 31 h CPU for the test and 7 h for Culver City on an M1 machine.
⚠️ Each member should only claim the parts they personally did (see §31).

**Q74. What did *you* do?** → Use the template in §31.

---

## 31. Honest answer about the team's work

### What the materials show
- The MINT paper is **our group's own paper**. Authors: Ahmed Zyed K.A., Alan Saji, Farhaan Nizam, Sreyas S Warrier, Shameem Ansar A and Chinnu Jacob (TKM College of Engineering).
- The repository contains our implementation, attack code, baselines, pre-registration files, run logs and result files, and the analysis scripts that generate every number in the paper (`paper/gen_numbers.py`).
- The repository's commits are under one account, so it **doesn't record who did what**. Each member should state their own part truthfully.

### Response pattern
1. **What we built:** "We designed and implemented MINT, a receiver-side defense for cooperative LiDAR perception, on top of the OpenCOOD framework."
2. **What we used, not built:** "We used the OPV2V dataset and OpenCOOD's released AttFuse detector unchanged. We didn't train any model."
3. **What we evaluated:** "We implemented four baselines and eleven attacks, pre-registered the evaluation, and ran it once on the OPV2V test — 15 scenarios, 2,066 frames — and on Culver City, on a CPU."
4. **What we found:** "A ray box filter already helps; MINT clearly recovers removal attacks; MINT vs the box filter depends on the AP definition; blind regions remain open."
5. **My part:** "[Say truthfully what you personally did — e.g. literature review, attack implementation, ray geometry, analysis, writing — and be ready to explain that part in detail.]"
6. **Not done / future work:** "Real-sensor data, other detectors, learned-defense comparisons, attacks that target the ray test."

### Never say
- "We trained the detector." / "We collected the data." / "We tested on real cars."
- "MINT beats all defenses." / "MINT detects all attacks." / "MINT guarantees security."
- "We compared against LUCIA / MADE / CP-Guard" (only in the literature review).

---

# Part 7 — Rapid revision sheets

## The 10 most important facts
1. **MINT = Message INfluence Testing** (old code name **R1**).
2. **Counterfactual:** Y⁺ with all senders vs Y⁻(i) without sender i. Detector unchanged.
3. **Effects:** Hungarian on BEV IoU ≥ 0.1 → **ADD** (only with), **REMOVE** (only without), **SHIFT** (> 0.3 m or > 10°).
4. **Unit:** sender × **6.4 m** tile.
5. **Rays:** SUP ends inside; TRAV passes through and ends behind; **N ≥ 3** for KNOWN, else UNKNOWN = **keep**.
6. **Wilson 95%** (z = 1.96): ADD gates if **hi(s⁺) < 0.5**; REMOVE gates if **lo(s⁻) > 0.5**; gate a unit only if some gate and **no useful**.
7. **Data:** OPV2V test **15 scenarios / 2,066 frames / 12 conditions** (primary); **Culver City 4 / 550** (secondary). Never pooled. Released **AttFuse** checkpoint, never retrained.
8. **Pre-registered verdict:** B-RAY (primary) passes under both AP definitions (+0.15 G, +0.76 F).
9. **MINT − B-RAY:** **+0.31 G ("improves") / −0.57 F ("performs worse")**.
10. **Strongest stealth removal†:** loss 40.41; **MINT +22.50 (≈ 56%)**; B-RAY −0.01; noREMOVE +0.07. Blind spoof: nobody > 0.10 recovery. Overhead +20% (n = 2) to +123% (n ≥ 4) median.

## One-page methodology cheat sheet

```
INPUT   f0 (own, trusted), f1..f(n-1) (untrusted), P0 own LiDAR (trusted)
STEP 1  Y+    = Dec(Fuse(all))
STEP 2  Y-(i) = Dec(Fuse(all but i))          for each sender i
STEP 3  Hungarian match on BEV IoU >= 0.1
          ADD    = in Y+ only         (test b+)
          REMOVE = in Y-(i) only      (test b-)
          SHIFT  = matched, >0.3 m or >10 deg  (test both)
STEP 4  assign to 6.4 m tile -> unit (i, u)
STEP 5  rays through box core:  SUP = ends inside, TRAV = ends behind
          blocked (ends before) & no-return: not counted
          s = SUP / (SUP + TRAV),  N = SUP + TRAV
STEP 6  KNOWN iff every box N >= 3 and not ego box;  else UNKNOWN -> KEEP
STEP 7  Wilson 95% [lo, hi]
          ADD:    gate hi(s+) < 0.5     useful lo(s+) > 0.5
          REMOVE: gate lo(s-) > 0.5     useful hi(s-) < 0.5
          SHIFT:  gate disjoint & s+ < s-   useful disjoint & s+ > s-
STEP 8  g(i,u) = KNOWN and (some gate) and (no useful)
STEP 9  each tile: candidates from decode without its gated senders -> NMS -> Y_MINT
FACTS   0 SUP needs >= 4 rays to be "empty" (3 -> hi 0.56; 4 -> hi 0.49)
        exact for AttFuse (per-pixel fusion); 1 extra decode per sender
        constants fixed on design set, frozen before validation/test
```

## One-page results cheat sheet

| What | Global-ranking (G) | Frame-order (F) |
|---|---|---|
| B-RAY, mean 4 original attacks | +0.15 [−0.01, +0.30], p = 0.0335 ✓ | +0.76 [+0.49, +1.27] ✓ |
| MINT, same | +0.45 [+0.29, +0.70] ✓ | +0.19 [−0.45, +0.52] ✗ n.s. |
| MINT − B-RAY | **+0.31** improves | **−0.57** performs worse |
| Culver: MINT − B-RAY | +0.27 improves | −0.14 not established |
| Strongest stealth removal† loss | 40.41 | 36.51 |
| — MINT | **+22.50** (rec. 0.56) | +20.94 |
| — B-RAY / ego / noREM | −0.01 / +19.19 / +0.07 | +0.06 / +9.99 / +0.10 |
| Clean relative loss B-RAY / MINT / B-NORM | 0.13% / −0.16% / 6.92% | −0.05% / 0.62% / 9.45% |
| B-NORM catch: plain / stealth PGD | 100% / 0% | |
| B-NORM clean false flags | 17.4% (test), 18.4% (Culver), 1.6% (dev) | |
| MINT clean switch-offs | 718 / 8,160; 521 useful (512 via REMOVE) | |
| Blind spoof recovery, any defense | ≤ 0.10 | ≤ 0.10 |
| Runtime p50 MINT (n = 2 / 3 / ≥4) | 20% / 53% / 123% | |
| Runtime p50 B-RAY (n = 2 / 3 / ≥4) | 4% / 9% / 11% | |
| Ego-only, mean 4 attacks | −20.02 | −24.20 |

## Hardest terms, one line each
- **Counterfactual:** the output if one sender had stayed silent.
- **Effect:** a difference between Y⁺ and Y⁻(i): ADD, REMOVE, SHIFT.
- **Unit:** one sender in one 6.4 m tile.
- **SUP / TRAV:** receiver ray ends inside / passes through and ends behind.
- **KNOWN / UNKNOWN:** ≥ 3 informative rays for every box (and not the ego box) / otherwise.
- **Wilson interval:** a range around the support share that is wide with few rays; used as a resolvability margin.
- **Gate / useful:** rays clearly contradict / clearly confirm the effect.
- **Global-ranking vs frame-order AP:** sort all detections by score vs go frame by frame.
- **Recovery:** ΔAP ÷ attack loss.
- **Pre-registration:** everything fixed before opening the test; test run once.
- **Holm:** correction for testing two methods.
- **Scenario bootstrap:** resample whole drives to get CIs.
- **Stealth PGD:** PGD kept under B-NORM's threshold.
- **Receiver-blind spoof:** fake placed where the receiver has < 3 rays.

## Five mistakes to avoid
1. Saying MINT "recovered 40.41 points" (it restored 22.50 **of** 40.41).
2. Saying MINT beats B-RAY without naming the AP definition.
3. Claiming we trained the detector, used real data, or compared with learned defenses.
4. Calling the Wilson interval "the probability the car exists".
5. Pooling OPV2V test and Culver City, or presenting the † conditions as confirmatory.

## Ten questions to answer without notes
1. What is MINT in one sentence?
2. What are Y⁺ and Y⁻(i)?
3. Define ADD, REMOVE, SHIFT and their thresholds.
4. What are SUP and TRAV, and why don't no-return rays count?
5. Why keep the sender when evidence is UNKNOWN?
6. State the ADD and REMOVE gate rules.
7. Why can B-RAY not fix REMOVE attacks?
8. What do +0.31 and −0.57 mean, and why do they differ?
9. What is the biggest limitation?
10. What did our group build, and what did we use from others?

## Final 60-second project explanation
> "Connected cars share LiDAR feature maps so each can see around obstacles, but a malicious sender can add, remove or move cars in the receiver's view. Our method, MINT — Message INfluence Testing — lets the receiver check each sender. It decodes the scene with and without that sender and records the differences as added, removed or shifted cars, each in a 6.4-metre tile. Then it tests each difference with its own LiDAR rays, which the sender can't fake. If the rays clearly contradict a change, measured with a Wilson 95% margin, the sender is switched off in that tile only; if there are too few rays, the sender is kept. We tested it once, under a pre-registered protocol, on OPV2V — 15 scenarios, 2,066 frames, 12 conditions — and on an unseen town. MINT was the only defense that clearly recovered removal attacks, restoring 22.50 of 40.41 lost AP points under the strongest one. But its advantage over a simple ray box filter depends on the AP definition, it adds computation, and it can't check places the receiver can't see."

## Final 30-second algorithm explanation
> "Decode with all senders and without each sender. Match boxes by bird's-eye-view overlap; unmatched-with is ADD, unmatched-without is REMOVE, moved is SHIFT. Put each in a 6.4-metre tile. Count own rays that stop inside or pass through each box. Fewer than three rays: keep. Otherwise, an ADD is contradicted if the Wilson interval is below a half, a REMOVE if it's above a half. Switch the sender off in that tile only if something is contradicted and nothing is confirmed, then rebuild the tile without it."

## Final 30-second results and limitations
> "A simple ray box filter already passes our pre-registered test. MINT adds clear recovery of removal attacks — 22.50 points under the strongest stealth removal, where the box filter gets nothing. Against the box filter overall, MINT is +0.31 points under global-ranking AP but −0.57 under frame-order AP, so the ranking depends on the metric. Limits: attacks in the receiver's blind regions aren't stopped, MINT costs 20 to 123 percent extra time, and everything is simulated with one detector and one attacker."
