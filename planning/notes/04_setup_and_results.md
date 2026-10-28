# Parts 4–5 — What was built, how it was tested, what it found

All AP numbers are **AP points** (AP@0.7 × 100) unless marked %. "G" = global-ranking AP, "F" = frame-order AP. Unless said otherwise, numbers are for the **OPV2V test** (primary). Sources are in `paper/main.tex` and the generated tables in `paper/tables/`.

---

# Part 4 — Implementation and experimental design

## 19. What was implemented, and by whom

### Taken from others (not our work)
| Item | Source | How we used it |
|---|---|---|
| OPV2V dataset | Xu et al. 2022, generated with CARLA | Test split (minus one scenario) and Culver City split; validation split for development |
| OpenCOOD framework | Xu et al. 2022 | Used at commit `31ba160` **without local changes** (paper §V-E) |
| AttFuse + PointPillars detector | released OpenCOOD checkpoint | **Used unchanged, never retrained** (paper §III-A). Reproduced the published test AP@0.7: 0.8155 vs 0.815 (`planning/README.md`, Stage 1) |
| Ideas: ray free-space checks | CARLO, Shadow-Catcher, CAD | B-RAY is "in the style of" these; no novelty claimed |
| Idea: with/without-agent comparison | ROBOSAC, MADE | MINT's counterfactual question is shared with them |
| PGD | Madry et al. 2018 | Attack algorithm |

### Built and run by our group (per the repository)
- MINT itself: effect extraction (`src/mint/effects/effects.py`), receiver ray geometry (`src/mint/geometry/rays.py`), the decision rule (`src/mint/reliability/r1.py`), tile-wise composition (`src/mint/fusion/compose.py`).
- Baselines: B-RAY, ego-only, MINT-noREMOVE (`src/mint/reliability/baselines.py`), B-NORM (`src/mint/reliability/bnorm.py`).
- Attacks: copy-paste feature attacks and point spoof (`runners/e0_stream.py`), receiver-blind spoof (`src/mint/attacks/blind.py`), PGD and stealth PGD (`src/mint/attacks/pgd_v3.py`, `pgd_stealth.py`).
- Ground-truth harm labels for diagnostics (`src/mint/eval/harm_labels.py`).
- Pre-registration files, the evaluation runs (`runs/`), statistical analysis, report generation, and the paper.
- Compute: everything on an Apple M1 CPU (8 threads), Python 3.10, PyTorch 2.2.2, NumPy 1.26.4. "About 31 hours of computation on the OPV2V test and about 7 hours on Culver City" (paper §V-E).

### Not done / future work
Real-sensor data (V2V4Real, Mixed Signals), other detectors (e.g. V2X-ViT), learned/consensus defenses as experimental baselines, attacks optimised against the ray test, colluding attackers, GPU timing, the hybrid B-RAY + MINT-REMOVE method (paper §VII-D, §VIII).

## 20. Datasets and test conditions

**Words.**
- **Scenario** = one recorded simulated drive (a short sequence with a few connected cars).
- **Frame** = one moment in a scenario (one LiDAR sweep from each car, with labels).
- **Attack condition** = one setting of the experiment (clean, or one specific attack at one strength) applied to all frames.

**The sets** (`paper/tables/tab_splits.tex`):

| Set | Scenarios | Frames | Agents n | Role |
|---|---|---|---|---|
| Design | 3 | 404 | 2–4 | Development; MINT designed here |
| Validation | 4 | 371 | 2 | Held out to check the frozen MINT; B-RAY chosen as primary here |
| **OPV2V test** | **15** | **2,066** | 1–5 | **Primary, one-time**; only clean detector outputs seen before |
| **Culver City** | **4** | **550** | 1–3 | **Secondary**; unseen town, same simulated sensor |

- The OPV2V test split has 16 scenarios; one was opened earlier (during a feasibility spike) and moved to development, leaving 15 (paper §V-A; `planning/project_qa_for_reviewers.md` B2).
- Test frames by n: n = 1: 119; n = 2: 866; n = 3: 869; n ≥ 4: 212 (paper §V-A). The 119 receiver-alone frames have no sender and count as clean. So 1,947 test frames have a sender.
- Design and validation sets come from OPV2V's validate split. The OPV2V **train** split is never used (we don't train).
- Culver City is "a separate town with a road layout modelled on Culver City, simulated with the same LiDAR model and never seen by the detector or used in our development". It tests transfer **to a new town, not to real sensors**, and its four scenarios give wide confidence intervals (paper §V-A).

⚠️ **Never add the two sets together.** The paper: "We use two evaluation sets and always report them side by side, never pooled." There is no source-supported reason to quote "2,616 frames" or "19 scenarios".

**12 conditions** = clean + 11 attacks (5 copy-paste + 6 PGD).

**Why both clean and attacked conditions?** Clean frames show the **cost** of the defense when nobody attacks (it should not hurt normal driving). Attacked frames show the **benefit**. A defense that helps under attack but ruins clean accuracy is useless.

## 21. Attack types and strength (paper §V-B, App. A; `planning/project_qa_for_reviewers.md` B3)

Common setup: one attacker, **always sender 1**; attempted on every frame with ≥ 2 agents; reproducible seeds. The attacker picks a target car it can see itself (≥ 20 of its own LiDAR points); it uses ground truth for this choice (attacker knowledge — the defenses never see ground truth). An attack is **realized** on a frame only if it actually changes the undefended output; frames where it can't be placed are scored as clean.

### Copy-paste attacks (edit feature maps in patches on a 3.2 m grid, random targets)
| Attack | What it does | Realized on test |
|---|---|---|
| Spoof (feature) | Copy a car's feature patch into an empty location → fake car | 1,136 |
| Remove (feature) | Overwrite a car's patch with background → erase a car | 176 |
| Shift (feature) | Erase a car and paste it one 3.2 m cell away → move a car | 206 |
| Spoof (points) | Copy a car's **LiDAR points** to an empty spot **before** encoding → fake at sensor level | 563 |
| Receiver-blind spoof | Like spoof, but placed only where the receiver has **< 3 rays** — aimed at MINT's known blind spot | 1,412 |

The first four are the **"four original attacks"** whose mean is the pre-registered headline.

### Optimised attacks (PGD)
- **PGD** [plain words]: start from a small random change to the attacker's features; compute which direction of change hurts the detector most (the gradient); take a small step that way; clip the change back within the allowed limit; repeat. Here: **10 steps**, step size ε/4, limit ‖δₖ‖∞ ≤ r·σₖ per scale (σₖ = standard deviation of clean sender features on the validation set), features kept non-negative. The loss uses the clean fused output as pseudo-labels, **never ground truth** (App. A).
- **Untargeted**: damage all detections. **Removal**: lower the scores of real cars.
- **Stealth**: after every step, also project the perturbation so the mean feature magnitude stays below **0.95 × B-NORM's threshold** — invisible to B-NORM by construction. Adaptive to B-NORM, **not** to MINT or B-RAY.
- Levels used: plain untargeted r = 0.25, plain removal r = 0.25, stealth untargeted r = 0.5, stealth removal r = 0.25 (each the smallest r with ≥ 2 AP points loss on the validation set, by a pre-fixed rule), plus **two strong stealth levels r = 1.0, marked †**, added **after** seeing development results; they "never enter a pass or fail decision".
- Stealth infeasible frames (no perturbation fits the constraint) are not attacked and scored clean: 10, 44, 3, 3 of 1,947 sender frames for the four stealth conditions (App. A).

**Threat-model reminder:** the attacks act on **learned features** (except the point spoof, which acts on raw points before encoding). They are digital attacks by a compromised sender, not physical laser spoofing.

## 22. Experimental design and fairness

- **Why baselines?** To know whether MINT's complexity is needed. B-RAY asks: "does a simple box filter already do the job?"
- **Same frames, same attacks.** Every ΔAP compares a defense with no defense **on the same frames** under the same condition (paper Eq. 9).
- **Separate tuning from testing.** MINT's constants were fixed on the **design** set, checked on the **validation** set, and frozen before the test. B-NORM's threshold and PGD budgets were set on development data. "None of them has a parameter fitted on test data" (§IV-F).
- **Held-out test** = data never used for any decision, opened once at the end. Before the final run, only the undefended detector's clean outputs had been seen on the test (§V-A).
- **Pre-registration** (§V-D): "every method, threshold, attack level and analysis was committed before the OPV2V test data were opened, and the test was run once." Culver City was planned the same way, committed before its data were downloaded, and run once after the test. SHA-256 checksums of frozen files were verified before the run (§V-E). This reduces cherry-picking: we couldn't adjust anything after seeing the test.
- **Honest consequence:** on the validation set MINT did **not** beat B-RAY under frame-order AP (MINT − B-RAY = −0.56). A rule fixed in advance then made **B-RAY the primary hypothesis** and MINT vs B-RAY the **key secondary** comparison (§V-D, App. C).
- **Why two AP definitions?** An audit before the test found the sign of MINT − B-RAY on the validation set depends on the AP definition. Rather than switch the primary again, the final plan required success under **both** (App. C).
- **Statistics.** Frames within one scenario are correlated, so uncertainty uses a **scenario bootstrap** (B = 2,000 resamples of whole scenarios; 95% CI = 2.5th–97.5th percentile). One-sided bootstrap p-values; **Holm** correction for testing two methods against no defense (§V-D).
- **Success rule** (for B-RAY): under both AP definitions, (i) its mean ΔAP over the four original attacks is significant after Holm, and (ii) the upper CI end of its clean loss ≤ 1%.
- **Three pre-written statements** for MINT vs B-RAY: "improves" (CI > 0), "performs worse" (CI < 0), "not established" (CI includes 0).
- **Labels.** Only the success rule, the Holm tests and the three-way statement on the OPV2V test are **confirmatory**; everything else, including every Culver City number, is **descriptive**; post-hoc choices are marked †.
- **One deviation**: a software bug crashed the first test attempt before any result was written; it was fixed "without changing any method, condition or criterion" (App. C).

**What the experiments can establish:** how these defenses behave on this simulated benchmark, with this detector, against these attacks. **What they cannot:** real-sensor performance, other detectors, colluding or MINT-aware attackers, real-time feasibility on vehicle hardware.

---

# Part 5 — Results and discussion

## 23. Metrics from zero

- **Object detection performance:** how many real cars the detector finds (with tight boxes), and how few fake ones it reports.
- **Precision** = of the boxes I reported, what fraction were real cars? **Recall** = of the real cars, what fraction did I find? Both: higher is better.
- **AP (Average Precision):** sort detections in some order; walk down the list; after each detection compute precision and recall; AP is the area under the resulting precision–recall curve (with precision made non-increasing). 0 to 1, or 0 to 100 "AP points". **Higher is better** (paper Eq. 11–12).
- **AP@0.7:** a detection counts as a true positive only if its IoU with a real car is ≥ 0.7 (tight). Cars only.
- **ΔAP = AP_defense − AP_no defense**, on the same frames (paper Eq. 9). Positive = the defense helps under that condition. **It is not a count of cars.** "+1 AP point" means the AP score went up by 0.01 on the 0–1 scale.
- **Loss L** = AP of no defense on clean frames − AP of no defense on attacked frames (how much the attack hurts).
- **Recovery Rec = ΔAP / L** — 1 means the defense undoes the whole attack, 0 nothing. Not reported when L < 0.5 points (paper Eq. 10).
- **Relative clean loss CL = 1 − AP_clean,defense / AP_clean,none** — positive = the defense costs accuracy on clean frames. **Lower is better** (negative = small gain).
- **Global-ranking AP:** sort **all** detections of the whole set by confidence score (as in PASCAL VOC).
- **Frame-order AP:** go through the frames **in order**; the default in OpenCOOD and therefore in most OPV2V papers. Our implementation matches OpenCOOD's to within 1.9 × 10⁻¹³ (§V-C).
- **False-positive rate (B-NORM):** share of clean frames with a sender where B-NORM wrongly flags the honest sender. Lower is better.
- **Computational overhead:** extra time per frame relative to the receiver's own perception, median (p50) and 95th percentile (p95). Lower is better.

## 24. Main numerical results (verified)

| # | Set | Condition | Method | Metric | Value | Compared with | Plain meaning | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | Test | mean of 4 original attacks | B-RAY | ΔAP G | **+0.15** [−0.01, +0.30], p = 0.0335 (Holm: significant) | no defense | Small gain; significant one-sided, but the two-sided CI touches 0 | §VI-A; `tab_verdict_both.tex` |
| 2 | Test | same | B-RAY | ΔAP F | **+0.76** [+0.49, +1.27], p = 0.0005 | no defense | Clear gain under frame-order | same |
| 3 | Test | same | B-RAY | success rule | **pass under both AP definitions** | pre-registered rule | The primary hypothesis (B-RAY) succeeded | same |
| 4 | Test | same | MINT | ΔAP G | **+0.45** [+0.29, +0.70], p = 0.0005 | no defense | Three times B-RAY's gain; significant | same |
| 5 | Test | same | MINT | ΔAP F | **+0.19** [−0.45, +0.52], p = 0.2259 | no defense | **Not significant** | same |
| 6 | Test | same | MINT − B-RAY | paired ΔAP G | **+0.31** [+0.12, +0.55] | B-RAY | Statement: MINT "**improves**" over B-RAY | same |
| 7 | Test | same | MINT − B-RAY | paired ΔAP F | **−0.57** [−1.64, −0.11] | B-RAY | Statement: MINT "**performs worse**" | same |
| 8 | Culver | same | B-RAY | ΔAP G / F | +0.05 (p = 0.1209, not sig.) / +0.54 | no defense | Rule fails under G, passes under F → "AP-definition-dependent" | same |
| 9 | Culver | same | MINT | ΔAP G / F | +0.32 / +0.40 (both sig.) | no defense | Descriptive | same |
| 10 | Culver | same | MINT − B-RAY | G / F | +0.27 "improves" / −0.14 [−0.40, +0.19] "not established" | B-RAY | Same signs as test | same |
| 11 | Test | stealth PGD remove r = 1.0† | (attack) | loss G / F | **40.41** / 36.51 | clean | The strongest attack's damage | `tab_attacks_both.tex` |
| 12 | Test | same | MINT | ΔAP G | **+22.50** [+18.41, +27.48]; recovery **0.56** | no defense | Restores more than half the loss | §VI-B; `tab_full_global.tex` |
| 13 | Test | same | MINT | ΔAP F | +20.94 (recovery 0.57) | no defense | Same under frame-order | `tab_full_frame.tex`; `numbers.tex` |
| 14 | Test | same | B-RAY | ΔAP G / F | −0.01 / +0.06 | no defense | Box filter cannot restore removed cars | `tab_conditions.tex` |
| 15 | Test | same | Ego-only | ΔAP G / F | +19.19 / +9.99 | no defense | Here the attack destroys more than cooperation adds | `tab_full_*.tex` |
| 16 | Test | same | MINT-noREMOVE | ΔAP G | +0.07 | no defense | REMOVE test carries the recovery | §VI-C |
| 17 | Culver | same | MINT / noREM / ego | ΔAP G | +19.53 (rec. 0.49) / +0.09 / +20.44 | no defense | Pattern repeats in the unseen town (loss 39.82) | §VI-B, §VI-C |
| 18 | Test | stealth PGD remove r = 0.25 | MINT | ΔAP G; recovery | +1.13; 0.37 (F: −0.14, rec. −0.13) | no defense | Partial recovery under G only | §VII-A; `tab_conditions.tex` |
| 19 | Test | all 12 conditions | MINT | ΔAP G | CI above 0 in **all 12** (Culver: all but two) | no defense | Under G, never clearly harmful | §VI-B |
| 20 | Test | clean | MINT | ΔAP F | −0.51 | no defense | Under F, costs accuracy on clean frames | §VI-B |
| 21 | Test | plain PGD | B-NORM | catch rate | **100%** | — | Catches crude attacks | §VI-D |
| 22 | Test | stealth PGD | B-NORM | catch rate | **0%** (both sets) | — | Evaded by construction | §VI-D |
| 23 | Test | clean | B-NORM | false-flag rate | **17.4%** (339/1,947); Culver 18.4%; dev 1.6% | — | Threshold didn't transfer from dev | §VI-D; `tab_clean_both.tex` |
| 24 | Test | clean | B-NORM | ΔAP G | **−6.13** [−10.03, −2.40] | no defense | False alarms cost accuracy | `tab_full_global.tex` |
| 25 | Test | mean of 4 original attacks | B-NORM | ΔAP G / F | −5.85 / −7.13 (Culver G −6.72) | no defense | Worse than no defense | §VI-D; Q&A B1 |
| 26 | Test | clean | B-RAY / MINT / B-NORM | relative clean loss G; F | 0.13% / −0.16% / 6.92%; F: −0.05% / **0.62%** [0.18, 1.75] / 9.45% | no defense | B-RAY within 1%; MINT's F cost CI exceeds 1% | §VI-E; `tab_clean_both.tex` |
| 27 | Test | clean | MINT | units switched off | 718 of 8,160; 521 were useful (false switch-offs); 512 of those from REMOVE | ground-truth labels | Most of MINT's clean mistakes come from REMOVE | §VI-C; App. B |
| 28 | Test | clean | MINT-noREMOVE | false switch-offs | 10 (of 62 switched off) | — | Removing REMOVE removes the errors (and the benefit) | `tab_clean_both.tex` |
| 29 | Test | receiver-blind spoof | all defenses | recovery | **≤ 0.10** on either set, either AP | — | Not defended | §VI-D |
| 30 | Test | receiver-blind spoof | (diagnostic) | placements | 1,381 of 1,412 realized spoofs had < 3 receiver rays; 0 touched a checkable unit (Culver 396 / 400, 0) | — | The fakes were placed where rays can't judge | §VI-D |
| 31 | Test | receiver-blind spoof | oracle | recovery F | 0.99 (any unit) vs 0.10 (only where receiver can check) | — | Limit of the evidence, not of the rule | §VI-D |
| 32 | Test | runtime | MINT (full) | p50 / p95 overhead | n = 2: **20% / 46%**; n = 3: 53% / 102%; n ≥ 4: **123%** / 170% | receiver-only perception | Grows with number of senders | §VI-E; `tab_runtime_both.tex` |
| 33 | Test | runtime | B-RAY | p50 / p95 overhead | n = 2: **4% / 11%**; n = 3: 9% / 20%; n ≥ 4: 11% / 16% (n = 1: 8% / 14%) | same | Cheap | `tab_runtime_both.tex` |
| 34 | Culver | runtime | MINT / B-RAY | p50 | n = 2: 46% / 20%; n = 3: 105% / 27% | same | Higher on Culver | `tab_runtime_both.tex` |
| 35 | Test | 4 original attacks | (attack losses) | loss G | 1.52, 1.01, 1.97, 0.27 (spoof feat., remove, shift, spoof pts) | clean | Original attacks are mild averaged over all frames | §VI-A |
| 36 | Test | mean of 4 original attacks | Ego-only | ΔAP G / F | −20.02 / −24.20 | no defense | Cooperation is worth a lot | Q&A B1; `numbers.tex` |

### Checking the prompt's candidate numbers

| Prompt's claim | Verdict |
|---|---|
| +22.50 AP points, MINT, strongest stealth removal, global-ranking | **Verified** (row 12). It is ΔAP vs no defense under stealth PGD remove r = 1.0†, on the OPV2V test. |
| "40.41 lost AP points recovered" | **Wrong wording.** 40.41 is the attack's **loss** (row 11). MINT restored 22.50 **of** the 40.41. The two numbers are different quantities. |
| MINT ≈ +0.31 over B-RAY, global-ranking | **Verified** (row 6) — mean of the four original attacks, OPV2V test. |
| MINT ≈ −0.57 vs B-RAY, frame-order | **Verified** (row 7). |
| B-NORM 100% catch for plain PGD, 0% for stealth PGD | **Verified** (rows 21–22). |
| B-NORM 17.4% false positives on clean test frames | **Verified** (row 23) — share of clean frames with a sender where the honest sender was flagged. |
| B-NORM −6.13 AP points global-ranking | **Verified, but specify the condition**: that is B-NORM's ΔAP on **clean** frames. Its mean over the four original attacks is −5.85 (row 25). Don't mix them. |
| MINT overhead +20% (n = 2) to +123% (n ≥ 4) | **Verified** as **median (p50)** on the OPV2V test, M1 CPU (row 32). |
| B-RAY +4–11% | **Verified** as B-RAY's **p50** on the test for n = 2…≥4 (row 33). Note: n = 1 is 8%, p95 up to 20%, and Culver City p50 is 20–27%. |

### What each key result means, and does not mean

**Result A — B-RAY passes the pre-registered rule (rows 1–3).**
1. *Measured:* mean ΔAP over 4 original attacks + clean loss. 2. *Means:* a simple ray box filter significantly improves robustness and costs < 1% clean accuracy. 3. Higher ΔAP better. 4. Vs no defense. 5. *Supports:* "physical verification helps" — even in its simplest form. 6. *Does not prove:* that MINT is needed for this; and the global-ranking gain is narrow (CI touches 0).

**Result B — MINT vs B-RAY reverses (rows 6–7).**
1. Paired difference on the same frames. 2. Under G, MINT is better by 0.31 points; under F, worse by 0.57. 3. Positive favours MINT. 4. Vs B-RAY. 5. *Supports:* "MINT's advantage over the box filter depends on the AP definition". 6. *Does not prove:* that MINT is better or worse overall. Saying "MINT beats B-RAY" without the qualifier is unsupported.

**Result C — removal recovery (rows 11–17).**
1. ΔAP under the strongest stealth removal. 2. MINT restores 22.50 of 40.41 lost points (56%); the box filter restores nothing. 3. Higher better. 4. Vs no defense. 5. *Supports:* the clearest claim of the paper — testing each sender's REMOVE effects with rays recovers removals that box filters can't; the ablation shows the REMOVE test is responsible. 6. *Does not prove:* general robustness; this condition was added post hoc (†), so it's descriptive, not confirmatory. At this level ego-only gets almost as much (+19.19).

**Result D — B-NORM fails both ways (rows 21–25).**
Catches plain PGD, misses stealth PGD completely, and false-flags honest senders on 17.4% of clean frames. *Supports:* a simple feature-statistics check is fragile under these conditions. *Does not prove:* all feature-anomaly defenses fail (we didn't test learned ones).

**Result E — blind spots (rows 29–31).**
No defense recovers more than 0.10 of the receiver-blind spoof's loss. Even an oracle restricted to visible regions recovers only 0.10 (frame-order). *Supports:* a limit of receiver-side evidence. *Does not prove:* that no future method could do better with other evidence.

**Result F — cost (rows 26–28, 32–34).**
MINT's clean cost depends on the AP definition (−0.16% G, 0.62% F; F CI up to 1.75%). Its false switch-offs come mostly from REMOVE verdicts. Runtime grows with senders: +20% to +123% median.

## 25. The results as a story

1. **Without a defense:** attacks hurt. The four original attacks are mild averaged over all frames (0.27–1.97 points G), because many attempts don't change the output; strong stealth removal costs 40.41 points.
2. **What baselines try:** ego-only avoids the attack but loses ≈ 20 points always. B-NORM tries to catch odd-looking features. B-RAY deletes boxes the receiver's rays show empty.
3. **Where MINT helps:** removal attacks. Under G, MINT is the only defense whose CI is above zero on all four removal conditions, on both sets (§VI-B). Spoofing and shifting: both ray-based defenses help.
4. **Under stealth attacks:** B-NORM is blind to stealth PGD by construction (0%). MINT still partly undoes the stealth removal (recovery 0.37 at r = 0.25, 0.56 at r = 1.0†, G), because "a sender can edit its message, but not the receiver's laser rays" (§VII-A).
5. **Trade-off on clean data:** B-RAY stays within 1%. MINT switches off 521 useful units on clean test frames (mostly via REMOVE), which costs 0.62% under F but nothing under G.
6. **Computation:** MINT needs one extra decode per sender: +20% (n = 2) to +123% (n ≥ 4) median. B-RAY: +4–11%.
7. **Why the metric changes the comparison:** see §26.
8. **Most defensible conclusion:** physical verification with the receiver's own LiDAR helps; a simple box filter already does a lot; MINT adds clear value against removal attacks; MINT vs the box filter overall is AP-definition-dependent; blind regions remain unsolved.

**Careful phrasing to use:**
- B-NORM: "a weakness of this simple feature-norm detector under the tested conditions."
- B-RAY: "box-level filtering can reject some fabricated boxes but cannot, by itself, restore information removed from the fused representation."
- Ego-only: "avoids collaborative attacks but sacrifices about 20 AP points of cooperative benefit."

## 26. Global-ranking AP versus frame-order AP

### The mechanism in words
AP is built by walking down an ordered list of detections. **Precision is cumulative**: every mistake counted early lowers the precision of everything after it.
- **Global ranking:** a **low-score** error is placed at the **end** of one long list, after almost all correct detections. It costs little.
- **Frame order:** the same error is counted **at its frame's position**, and "lowers the precision of every later frame" (§VII-B).

So the **same feature spoof costs 1.52 points under G but 3.57 under F** (§VII-B).

The two defenses make different kinds of low-score changes:
- **B-RAY deletes low-score fakes** → helps little under G, a lot under F.
- **MINT's occasional false switch-offs remove a few correct boxes** → costs almost nothing under G, but is charged in full under F.
Together these flip the comparison. "Neither definition is wrong; they weight errors differently" (§VII-B).

### A tiny fictional example [TEACHING EXAMPLE — invented numbers, not MINT results]
4 real cars in 4 frames. Each method makes exactly **one** mistake (one fake box). Detections are (score, correct?):

| Frame | Method X | Method Y |
|---|---|---|
| 1 | (0.9 ✓), **(0.3 ✗ fake)** | (0.9 ✓) |
| 2 | (0.9 ✓), (0.8 ✓) | (0.9 ✓), (0.8 ✓) |
| 3 | (0.85 ✓) | (0.85 ✓) |
| 4 | — | **(0.95 ✗ fake)** |

- **Global ranking** (sort all by score):
  - X: ✓ ✓ ✓ ✓ ✗ → the fake is last → **AP = 1.00**
  - Y: ✗ ✓ ✓ ✓ ✓ → the fake is first → **AP = 0.80**
- **Frame order** (frame 1, 2, 3, 4):
  - X: ✓ ✗ ✓ ✓ ✓ → the fake is early → **AP = 0.85**
  - Y: ✓ ✓ ✓ ✓ ✗ → the fake is last → **AP = 1.00**

Global ranking says X is better; frame order says Y is better. Same detections, same number of mistakes — the ranking flips because the two definitions charge an error at different places. (Computed with the paper's AP formula, Eq. 11–12.)

### The real comparison (verified)
- Global ranking: MINT − B-RAY = **+0.31** [+0.12, +0.55] → "improves".
- Frame order: MINT − B-RAY = **−0.57** [−1.64, −0.11] → "performs worse".
- "Both statements are confirmatory, and both are true: they answer the same question under two different rules for counting errors" (§VI-A).

### Why it matters scientifically
Any claim must name the metric and protocol. Since frame-order is the OpenCOOD default and most OPV2V papers don't say which they use, "a ranking between cooperative-perception defenses can therefore depend on an evaluation setting that papers rarely state" — the paper recommends reporting which definition is used, preferably both (§VII-B).

## 27. Discussion I — what the results mean

| Point | Direct evidence [SOURCE] | Interpretation |
|---|---|---|
| Sender-specific influence testing is useful | Removal recovery only for MINT; ablation collapses it (+22.50 → +0.07) | Knowing *what each sender changed* is what lets you restore removed cars |
| Counterfactual + physics both matter | Stealth removal evades B-NORM but is partly undone by MINT; B-RAY (physics without counterfactual) can't restore | Physics gives evidence the attacker can't forge; the counterfactual turns it into recovery |
| REMOVE attacks are subtle | B-RAY's effect on removal is zero or slightly negative | A missing car leaves no box to inspect; you must look at "what would have been" |
| Local gating preserves information | At the strongest removal, MINT (+22.50) ≥ ego-only (+19.19) "while keeping the benign senders" | Tile-level decisions cost only local information |
| Robustness | MINT's G CI above 0 in all 12 test conditions | Under G it never clearly hurts; under F it does in some (clean −0.51) |
| What's needed before claiming real-world safety | All data simulated; one detector; one attacker; no ray-aware attacker | Real-sensor validation, other detectors, adaptive attacks |

Transfer (§VII-C): in Culver City the main pattern carried over (MINT significant, gains on all four removal attacks, same signs vs B-RAY). Only B-RAY's small G gain did not. The detector itself is worse there (clean F AP 73.59 vs 82.17), so it is a real change of conditions — but not real sensors, and only four scenarios.

Practical implication (§VII-D): B-RAY is cheap and handles added cars; MINT is needed for removals. This suggests a **hybrid** (B-RAY for ADDs, MINT's REMOVE test for removals) — **not tested**.

## 28. Discussion II — limitations and threats to validity (§VII-E)

- **Computation:** one extra decode per sender → overhead grows with agents (+20% → +123% median). A cheaper "triggered" variant (run the counterfactual only when a fast trigger fires) was timed (p50 10% at n = 2, 77% at n ≥ 4) but "was not exact on development data and no accuracy number uses it" (App. A).
- **Blind regions / occlusion / sparse points:** rays only judge what the receiver sees; UNKNOWN keeps, so blind fakes pass.
- **UNKNOWN risk:** the cautious fallback protects honest unique views but lets blind attacks through.
- **Attacker assumptions:** single, non-colluding; no attack optimised against the ray test (e.g. placing fakes where fewer than four rays cross them).
- **Detector:** one detector (AttFuse); exactness relies on per-pixel fusion.
- **Data:** all simulated (CARLA). Real LiDAR misses dark/glass surfaces and returns from vegetation/spray. Real datasets not evaluated. The receiver's sensor is assumed honest.
- **Baselines:** no learned or consensus defenses run.
- **Statistics:** bootstrap p-values not calibrated under a null; percentile intervals over 15 or 4 scenarios may be too narrow.
- **Development choices:** attack levels, the primary, the stealth attacks were set on development data; the r = 1.0 levels were added post hoc.
- **Metric choice:** the MINT vs B-RAY ranking depends on the AP definition.
- **Scope change from the original plan:** the early research charter (`planning/research_charter.md`) aimed at a *calibrated probability of harm* per tile, with hypotheses on AUROC and honest unique views. Those were not tested as stated; the Wilson interval is used only as a resolvability margin (App. C; `planning/project_qa_for_reviewers.md` C7). If an evaluator has seen the charter, say this openly.

### Balanced table

| Strengths | Limitations | Unknown |
|---|---|---|
| Evidence the sender can't forge (receiver's own rays) | Can't judge where the receiver can't see | Real-sensor performance |
| Restores removed cars (+22.50 vs B-RAY −0.01) | Ranking vs B-RAY flips with AP definition | Behaviour with other detectors |
| Local decisions keep useful information | 521 false switch-offs on clean test frames; F clean loss 0.62% | Behaviour against ray-aware or colluding attackers |
| Keeps senders when evidence is insufficient | Overhead +20% to +123% median | GPU / embedded runtime |
| Pre-registered, one-time test, two AP definitions, second town | One detector, one attacker, simulation only | Comparison with learned defenses |
| No parameters fitted on test data; no retraining | Strongest result is a post-hoc condition (†) | Whether the untested hybrid would be best |

## 29. Conclusion and future work (paper §VIII)

**Conclusion bullets**
- A receiver can check each sender's influence with evidence the sender cannot forge: its own LiDAR rays.
- In a pre-registered OPV2V evaluation, physical verification helped; a simple ray box filter already improved robustness.
- MINT went further against removal: the only defense with a clearly positive gain on all four removal attacks (G), on the test and in an unseen town.
- Whether MINT beats the box filter overall depends on how AP is computed.
- Regions the receiver cannot see remain undefended.

**Spoken conclusion.**
> "Our results show that the receiver's own LiDAR can verify what each sender changes. A simple ray filter already helps, and MINT adds the ability to restore removed cars, which box filters can't do. But MINT's overall advantage depends on the AP definition, it costs extra computation, and it cannot check places the receiver can't see. A received message should not only look plausible; its effect should agree with what the receiver can physically observe."

**Future work (from §VII-D and §VIII)**
1. **Hybrid defense:** cheap B-RAY for added objects + MINT's REMOVE test for removals.
2. **Blind regions:** find evidence for regions the receiver cannot see (e.g. other benign vehicles' scans — which reopens the question of whom to trust).
3. **Real-world validation:** V2V4Real, Mixed Signals.
4. **Lower cost:** run the counterfactual only when needed (a trigger that is exact enough to trust).
5. **Broader attacks:** attackers that target the ray test, and colluding attackers.

**Already shown vs future work:** shown = removal recovery on simulated OPV2V and Culver City, B-RAY success, AP-definition dependence, blind-spot limit. Future = everything about real sensors, other detectors, adaptive/colluding attackers, hybrid, speed-up.
