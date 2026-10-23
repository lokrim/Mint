# Implementation roadmap

Checkpoint 1, 2026-10-22. Stages are gated: each must pass its scientific gate before the next starts. Resource figures are **[E]** estimates. The dataset path depends on decision Q1:
- **OP-first** if there is no GPU;
- **MS-first** if a GPU and ≥ 300 GB storage exist.

Both paths share the code.

## Repository layout (proposed)

```
mint/
  planning/                 # this package (findings/ preserved verbatim)
  src/mint/                 # importable package; NO OpenCOOD code copied (licence R-09)
    io/        readers (organized PCD, OPV2V), placeholder/no-return masks, frames, clocks
    geometry/  slot directions, mount fits, range images, box/ray slab tests, ground map
    model/     thin adapter around an external, unmodified OpenCOOD install (feature hooks, masked fusion)
    effects/   counterfactual passes, effect matching (ADD/REMOVE/SHIFT)
    evidence/  ray counts (M3), beta-binomial models (M4), feature residuals (M5 channels)
    reliability/ combiners, calibration, statuses, temporal state
    fusion/    gating / soft weighting policies
    attacks/   raw (A-R*), feature (A-F*), metadata/temporal (A-M*, A-T*, A-C*), ledgers
    eval/      evaluator-only: GT matching, D labels, strata, metrics, bootstrap (separate import root)
    bench/     timing and memory harness
    provenance/ run records, hashing, manifests
  configs/                  # versioned YAML per stage; hashed into run records
  runners/                  # thin CLIs: one per stage
  tests/                    # unit, property and boundary tests
  notebooks/                # source notebooks; executed copies under runs/<id>/notebooks
  runs/                     # immutable run records (git-ignored payloads; manifests tracked)
```

**Environment.** Pinned after Stage 1 from the selected model's stack. Do **not** inherit Python 3.14/3.15 from Valid Point.
- Expect Python 3.8–3.10 and PyTorch ≥ 1.12. spconv is only needed if the voxelizer requires it; PointPillars voxelization can be reimplemented in NumPy.
- Lock with `uv` (or conda if CUDA wheels need it).
- Record full `pip freeze` and hardware into every run record.

**Run records.** `runs/<UTC>-<stage>-<shorthash>/` with `manifest.json`: config hash, git commit, input artefact hashes, environment, start/end, peak RSS (including children), outputs hash. Idempotent, deterministic seeds, resumable by content-addressed caches keyed on (input hash, model hash, preprocessing hash). No copies of archives or source trees.

## Verification checks referenced across the package

| ID | Check | Stage |
|---|---|---|
| V-01 | Checkpoint provenance: hash; config; training split; reported AP reproduced within ±0.01 (OP/VR) or the training-log AP (MS) | 1 |
| V-02 | Sender-frame encoding + receiver warp vs `proj_first=True`: AP difference reported | 1 (**done** 2026-10-23: AP@0.7 0.874 → 0.515; coordinate convention fixed by D-13b) |
| V-03 | Locality: masking sender i in tile u leaves head outputs outside u bit-identical before NMS; cross-tile NMS effects counted | 1 |
| V-04 | MS label↔sync alignment (box-centre vs cluster-centroid residual per offset −3..+3 on moving objects; ≥ 50 objects) and keyframe identification | 1 |
| V-05 | Message size definition and measurement | 1 |
| V-06 | Slot-direction LUT and mount fit: reconstruct xyz from range + LUT, median error < 2 cm, p99 < 5 cm at ≤ 50 m, per sensor; TOP tilt cross-checked by a ground-plane fit | 2 |
| V-07 | Placeholder semantics: fraction of no-return slots by elevation, by azimuth sector, and inside GT boxes | 2 |
| V-08 | OS-level inference boundary: the inference process cannot open evaluator paths (container or bind-mount); a deliberate leak via builtin `open` fails | 2 |

## Stages

### Stage 0: planning (this checkpoint) ✔ pending review
- **Deliverables.** This package.
- **Gate.** User decisions Q1–Q4 ([risks](risks_and_open_questions.md)) and an approved methodology direction.

### Stage 1: dataset, labels, feature and clean-perception feasibility
- **Inputs.** A small dev subset only:
  - OP: about 2 validate scenarios;
  - VR: about 2 val scenarios;
  - MS: block-T segments mini_6 and mini_8 via ranged member fetch, plus the local exposed mini_7.
- **Tasks.**
  1. Pin the environment. Install unmodified OpenCOOD (or the V2V4Real fork) **outside** `src/mint`.
  2. Load the checkpoint. Reproduce AP on a small slice, then on the full eval split once only (V-01).
  3. Feature hooks: extract per-scale tensors; implement masked attention (V-03).
  4. MS: readers with no-return masks, frames, V-04, label overlays.
  5. Measure per-stage cost on M1 (proxy).
- **Tests.**
  - Reader round-trip.
  - Placeholder mask equals the repeated-origin count.
  - Transform composition against the devkit on 5 frames.
  - Locality test.
  - Reproduction tolerance.
- **Notebooks.** 02 (dataset/GT integrity), 03 (features and clean perception).
- **Budget.** OP/VR: ≤ 60 GB download, ≤ 2 CPU-days. MS: ≤ 25 GB.
- **Gate S1-G.** Every item of [feasibility](dataset_and_feature_feasibility.md) §8 passes.
  - Locality holds, or cross-tile effects are under 5% of effects.
  - Clean per-class AP is non-degenerate.
- **Fallback.**
  - If locality fails: restrict labels to tiles of 12.8 m and count cross-tile effects, or change the unit to "effect" (object-level).
  - If the OP checkpoint fails to reproduce: try VR, or another OpenCOOD checkpoint.

### Stage 2: geometry, ray evidence feasibility and the inference boundary
- **Tasks.**
  - Slot directions and mount fits (V-06); no-return analysis (V-07).
  - Range-image footprint and slab tests with property tests.
  - Ground map for the static receiver.
  - Receiver coverage of effectful tiles on clean dev data.
  - OS-level boundary (V-08).
- **Tests.**
  - Slab test vs brute-force sampling on random boxes and rays.
  - Each ray counted once.
  - Monotonicity (P1).
  - Unknown on zero coverage (P3).
- **Notebooks.** 04 (ray geometry, counterexamples).
- **Gate S2-G.** V-06 passes, and the coverage of effectful tiles with `n_eff ≥ 3` is at least 20% **[A]**.
- **Fallback.** Switch MINT-v0 to M5-A (feature-only) and report the ray study as a negative feasibility result ([candidates](methodology_candidates.md), fallback rule).

### Stage 3: minimal method (M3, M4) and evaluator
- **Tasks.**
  - Effects (ADD/REMOVE/SHIFT).
  - Evaluator D labels and strata.
  - M3 counts; M4 beta-binomial fits on clean block T, with posterior-predictive checks.
  - Calibration on block C.
  - Gating policies.
  - Baselines M1, B-LUCIA, B-CAD-local.
- **Tests.**
  - Hand-computed D on constructed frames.
  - Calibration code against a known synthetic.
  - ID-permutation invariance.
  - Prefix invariance.
- **Notebooks.** 05 (derivation, hand checks, fits, calibration), 06 (temporal, missingness, sparse support, benign controls).
- **Gate S3-G (clean development only).**
  - Posterior-predictive checks pass in ≥ 50% of bins.
  - Clean false-gating of USEFUL effects ≤ 5% on block C at θ.
  - Clean AP retention ≥ 0.98 on block C.

### Stage 4: clean and controlled pilot (development)
- **Tasks.** Run the seen attack families and benign stresses on blocks T/C only. Tune [A] parameters within the preregistered grid. Write `protocol_freeze.json`.
- **Gate S4-G.** All metric code reconciles with an independent recount script (pattern from findings evidence/r2). Freeze recorded.
- **Decision.** Whether v1 (M5) is built: only if harmful labels in T are ≥ 500 and v0 leaves headroom on development data.

### Stage 5: frozen attacks and baselines
- **Tasks.** Implement every family in the [attack protocol](attack_and_benign_protocol.md). Realization checks on T/C. Freeze schedules and seeds.
- **Notebooks.** 07 (raw-cloud attacks), 08 (feature attacks, targeted effects, adaptive evasion).
- **Budget.** PGD families are GPU-preferred. On CPU, restrict to keyframe windows and record the restriction.
- **Gate S5-G.** Ledgers complete. Each family's harm distribution is reported. Low-harm families are kept and labelled.

### Stage 6: held-out evaluation (block E / test scenarios)
- **Tasks.** Single sealed run of all systems on E. Seal predictions, then compute metrics.
- **Notebooks.** 09 (per-unit clean/attacked visualizations), 10 (grouped evaluation, uncertainty, failure analysis).
- **Gate.** None on outcomes: results are reported whatever they are.

### Stage 7: efficiency and ablations
- **Tasks.** The benchmark plan ([budget](compute_memory_and_communication_budget.md) §7). Ablations AB-1..AB-9 on E. These are labelled as post-freeze analyses of preregistered ablations.
- **Notebooks.** 11 (latency, memory, communication).

### Stage 8: paper and reproducibility
- **Tasks.** Figures and tables from run records via exact commands. Claim ledger complete. Reproduction from a clean clone on a second machine, if available.
- **Notebooks.** 12 (paper figures, claim ledger, reproduction checks).

## Early-feasibility principle

Stages 1–2 answer the questions that could make the objective untestable:
- Can we get features and a working detector?
- Is fusion local?
- Do receiver rays cover effectful tiles?

They do this **before** any attack infrastructure is built. Expected effort: Stage 1 at 1–2 weeks, Stage 2 at 1 week **[E]**, depending on Q1.
