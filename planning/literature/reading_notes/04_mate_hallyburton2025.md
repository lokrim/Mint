# MATE: Hallyburton & Pajic, ACM CCS 2025

- **Citation.** `hallyburton2025mate`. arXiv 2503.04954 v1. DOI 10.1145/3719027.3765193 (from search; verify).
- **Access.** FULL-CLOSE on §3 (agent and fusion pipeline), §4–5 (threats, problem), §6 (MATE: propagation, PSMs, Beta updates), §7 (trust-informed fusion). Evaluation §8 skimmed. Read 2026-10-22.

## Question, unit, inputs
- **Question.** Can a data aggregator (AGG) estimate time-varying trust distributions for agents and tracks, and use them to limit compromised insiders in multi-agent tracking?
- **Units.** Agent trust `τ_a^k` and **track trust** `τ_c^j` (per fused object track), each a Beta PDF on [0,1].
- **Inputs.** Each agent sends:
  - its own pose;
  - locally tracked objects (late fusion);
  - **a LiDAR-derived FOV estimate**: ray tracing plus concave hulls with occlusion (§3; Appendix A).

## Threat model (§4)
- Insider or physical attacks producing FP, FN, translations or pose errors.
- Temporal characteristic: static, Markovian or trajectory-consistent (implausible dynamics get filtered).
- AGG is a "trusted computing centre".

## Core algorithm (§6)
- Hidden-Markov trust with transition "propagators" that pull back to the prior or towards a target mean over time (eq. 4).
- **Trust pseudomeasurements (PSMs)** `ρ = (v, c)`, value and confidence. They come from assignment between agent tracks and AGG tracks:
  - AGG track matched by agent k → track gets `v=1`, `c=E[τ_a^k]`; agent gets `v=E[τ_c^j]`.
  - AGG track unmatched but **inside agent k's FOV** → track `v=0`; agent `v=1−E[τ_c^j]`.
  - Outside the FOV → no PSM.
- Beta–Bernoulli-style update (eq. 9): `α += Σ c·v`, `β += Σ c·(1−v)`.
- A **negativity-biased** weighted update departs from conjugacy on purpose ("trust lost easily").
- **Fusion.** Track thresholding on `E[τ_c]` (flagged tracks kept, not deleted). Kalman gain scaled by `E[τ_a]^ω_K`.

## Our explanation
- The closest Bayesian/evidential formulation at object level. Visibility gates who is "expected to see" what. This is exactly the support / unknown distinction we need.
- **But:**
  1. the FOV is **sender-reported** (agents send their own FOV), so a compromised agent can shape the visibility used to judge it;
  2. PSMs are heuristic pseudo-observations, not a likelihood of a defined event; the "probability" semantics are nominal;
  3. evidence from different agents about the same track is not independent, yet it is accumulated as if it were;
  4. agent trust remains a global sender reputation, which TrustFlip shows can be poisoned.

## Data and evaluation
- CARLA Monte-Carlo smart-city intersections (infrastructure + vehicles).
- Reported about 94% reduction in adversary-driven OSPA and about 90% agent-detection accuracy (abstract).
- Simulation only.

## Compute
- Gibbs-style decomposition into track/agent subproblems; multi-process real-time pipeline (§8.5).
- Exact figures not extracted.

## Code
- Built on AVstack (cited). Repository not checked.

## What transfers
- The Beta evidence update with discounting, as a candidate *temporal state* per (sender, tile), with explicit "outside visibility → no update".
- Separating instantaneous PSM from accumulated trust.

## What does not transfer
- Late fusion (tracks).
- Sender-reported FOV.
- Global agent trust as a fusion weight.
- Uncalibrated Beta means.

## Experiment
In candidate M4, compare the discounted beta-binomial tile state against memoryless evidence under on/off attacks and history poisoning (A-T1..A-T3). Use the receiver-computed FOV, not the sender-reported one. Measure calibration (ECE) of the posterior mean against held-out `D` labels. A nominal Beta mean is expected to be miscalibrated until refit.
