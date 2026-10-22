# 06 — Requirements for the new study

Revision 2 (2026-10-22). These are testable requirements and open choices. They are **not** a selected method. Each row names the failure or gap that motivates it (IDs in [evidence_ledger.csv](evidence_ledger.csv)) and an acceptance check. A negative result is an acceptable outcome. No requirement asks for a descending score curve.

| ID | Requirement / open choice | Motivated by | Acceptance check |
|---|---|---|---|
| N01 Unit | Define the reliability unit: a BEV feature cell/region, a per-message spatial block, or an object hypothesis with its supporting feature region, at a defined time. Not a sender score. | MT-15, EX-14, LT-03 (sender-trust poisoning) | A written definition maps each output to (time, location/object, sender message). Changing only the sender ID cannot change the output unless declared state uses it. |
| N02 Meaning | Choose one primary target. Options: P(the unit's contribution is correct w.r.t. GT); expected change in downstream detection error if the unit is fused; or calibrated selective-acceptance risk. | MT-04, EX-07 (perturbation detection ≠ correctness) | The target can be computed from GT on held-out data. A "useful but surprising" unit (an honest unique view) is scored as useful. |
| N03 Inference inputs | Declare every runtime input and who can control it: received features, sender pose/time metadata, receiver raw scan, receiver features, history. Keep separate the information settings (a) features only, (b) + receiver raw scan, (c) + sender-supplied ray/occupancy metadata. | DA-16, MT-08, SC-05 | Dependency graph plus an executable boundary. Inference runs in a process that cannot read GT, schedules or clean counterparts. A deliberate leak through builtin `open` fails the test. |
| N04 GT roles | GT **may** supervise training, tune development choices and evaluate, with session-grouped splits. GT, attack schedules and clean counterparts are **prohibited at deployment inference**. The old blanket ban on training labels is dropped. | SC-01–SC-03, DA-14 | Split manifest groups by acquisition session/time window. Supervision provenance is recorded. The deployment API has the same signature on clean and attacked data. |
| N05 Feature pipeline | Select a model and checkpoint; the encoder layer and tensor schema; preprocessing (**including placeholder handling**); alignment; class conventions; postprocessing. | DA-02, DA-15 | A bounded clean frame reproduces a reference detection output. Tensor shape/stride/frame are documented and hashed. Placeholders demonstrably excluded or explicitly modeled. |
| N06 Labels | Verify the label↔sync-index mapping, frame (`top`), classes, crop (±51.2 m) and point filter (>5 points); empty versus missing files. | DA-07, DA-08 | Overlay of boxes on aligned clouds for sampled frames in each segment. Mapping error rate reported. Objects with ≤5 points treated as "unlabelled", not "absent". |
| N07 Threat model | Separate threat models: raw point edits before encoding; direct feature-message edits; metadata (pose/time) spoofing; collusion; physical attacks only with separate evidence. Attack locations must be realistic (on objects, free space within sensor range), not sensor-adjacent artefacts. | DA-05, EX-01 | Threat matrix of attacker knowledge, control and constraints. Every intended edit has a realized-change record **and** a measured task harm (GT delta). Harmless edits are reported as such. |
| N08 Honest unique views | Preserve correct evidence that no other agent corroborates. | MT-15, EX-13, LT-03 | Stratify evaluation by corroboration status (seen by another agent / occluded for others / out of others' range). Report false rejection of correct unique units and the resulting task-recall loss. |
| N09 Benign controls | Dynamics, occlusion/disocclusion, sparsity, range, noise, downsampling, pose/time error, **cross-segment shift**. | EX-05, EX-09, EX-10 | Same pipeline on benign and attack strata. Window-specific denominators. Benign rejection rates by stratum. |
| N10 Calibration/uncertainty | Calibration matches the unit and target. Separate states: insufficient support, degenerate/saturated score, cannot-alarm, abstain. Calibrate on sessions other than the test sessions. | MT-05, MT-10, MT-11, EX-04 | Reliability diagrams or risk–coverage on grouped held-out sessions. Explicit `CANNOT_DECIDE` counts. No IID claims across frames of one clip. |
| N11 Temporal evidence | Handle moving objects, attacked history, resets, delayed evidence, with no future access. | MT-08, MT-13 | Prefix invariance; a contaminated-history counterexample; per-burst recovery windows. |
| N12 Resource budget | Fix after model feasibility. Low compute and memory matter; hardware is open. | RP-06 | End-to-end latency distribution, peak working set (including children), state growth, bytes per message, on named hardware; worst-case workloads included. |
| N13 Literature first | Primary-literature review and an observability check before choosing a method. | LT-01, LT-02 | Review matrix ([07](07_literature_questions_and_candidate_methods.md)) with full-paper reads, code/checkpoint availability verified now, and retain/reject reasons. |
| N14 Notebooks | Research notebooks that compute and explain, not display. | RP-07 | See the acceptance list in [08](08_reproducibility_resources_and_notebook_lessons.md). |
| N15 Paper claims | Claims cite population, version and denominators. A benefit claim requires downstream improvement against GT plus honest-view safeguards; otherwise report the negative result. | all EX | Claim ledger links each sentence to a table row and run hash. |

## Choices deliberately left open

- Feature cell versus region versus object unit; "correct" versus "useful" target.
- Feature-only versus raw-augmented receiver.
- Model, dataset and release (Mixed Signals or another).
- Deterministic, statistical, learned or hybrid estimator.
- Calibration loss and abstention cost; spatial/temporal resolution; hardware.

Comparisons must be fair: a no-filter fusion baseline, a simple declared reliability baseline and the candidate, under matched feature, communication and compute settings.
