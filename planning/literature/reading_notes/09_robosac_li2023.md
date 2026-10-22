# ROBOSAC: Li, Fang, Bai, Chen, Juefei-Xu, Feng, ICCV 2023

- **Citation.** `li2023robosac`. arXiv 2303.09495.
- **Access.** FULL-CLOSE on §3 (setup, ROBOSAC, A2CP) and §4 setup. Read 2026-10-22.
- **Code.** github.com/coperception/ROBOSAC (MIT), pushed 2024-02-18. Not run.

## Question, unit, inputs
- **Question.** Choose a benign subset of teammates by hypothesize-and-verify consensus.
- **Unit.** A teammate subset per frame.
- **Inputs.**
  - ego-only result `Ŷ0`;
  - results fused with sampled subsets;
  - difference measure `d`, threshold ε (0.3 in the experiments).

## Algorithm
- Sample `s` teammates. If `d(Ŷ_s, Ŷ_0) ≤ ε`, accept; else resample, up to budget N. On dissensus, fall back to ego-only.
- `s = ⌊ln[1−(1−p)^{1/N}] / ln(1−η)⌋` (eq. 1) and `N = ⌈ln(1−p)/ln[1−(1−η)^s]⌉` (eq. 2): RANSAC-style sample counts for attacker ratio η.
- A2CP estimates η when unknown.

## Critique
- **Consensus with the ego is the acceptance criterion.** Any teammate that adds information the ego lacks (the point of collaboration) increases `d`. Honest unique views are structurally at risk of rejection. This is the clearest example of the failure mode H3 tests.
- Sender-subset granularity.
- Compute scales with the number of samples: reported FPS around 14–15 vs higher without defense on V2X-Sim.

## Evaluation
- V2X-Sim (5 Hz). PGD, C&W and BIM feature attacks (15 iterations, Δ = 0.5). AP@IoU.

## What transfers
- The cost model for sampling defenses (a baseline cost reference).
- The hard example for H3.

## Experiment
Optional baseline `B-ROBOSAC`, only if compute permits (it multiplies fusion passes). Report its unique-view false-rejection rate on the UNIQUE stratum.
