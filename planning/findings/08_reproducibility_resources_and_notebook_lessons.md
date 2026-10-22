# 08 — Reproducibility, resources and notebook lessons

Revision 2 (2026-10-22).

## 1. Practices worth keeping versus overhead to drop

| Keep | Drop |
|---|---|
| Dataset revision and member hashes; config and source hashes; immutable run directories | Treating a hash, a gate label or "134 passed" as scientific support |
| Separate source, availability and decision clocks; causal pose selection | Implicit sync-index alignment |
| Deterministic attack keys; intended/injected/realized ledgers; failures in denominators | Writing every derived episode to disk; repeated full Markdown copies of multi-MB CSVs (R05 stores both a `.csv` and a `.md` for every table, ~30 MB duplicated) |
| Explicit `UNDEFINED` / `CANNOT_ALARM` states; per-segment tables | Gates that only check that files exist |
| Independent reconciliation scripts (e.g. [audit_r2.py](evidence/r2/audit_r2.py)) | Status documents updated by hand (they went stale: ST-03) |
| Resumable checkpoints with idempotent output paths | Episode IDs derived from enumeration order (needed the R05 repair); restarts colliding with partial directories (three `FileExistsError`s) |

## 2. Environment and compatibility

- `pyproject.toml`: Python ≥ 3.11, `numpy>=2,<3`, optional `matplotlib`, `nbconvert ≥ 7.17.2`, Jupyter, pytest. **No ML stack.**
- R05 `environment_start.json`: Python 3.14.4, **NumPy 2.5.3**, macOS 27 arm64. Git HEAD `c9f56f7` with a dirty tree; `real.py` was untracked at start (preserved in `source_snapshot/` and six `implementation_predict_*` snapshots).
- R05 `environment_final.json`: **NumPy 2.5.4**. The library changed between prediction and finalization (RP-03).
- Detector/fusion stacks (PyTorch, spconv, OpenCOOD-style code) typically pin older Python/CUDA versions. Pick the environment from the chosen model, not from these locks. System `python3` here has no NumPy; old scripts need `.venv`.

## 3. Measured resources and their scope (RP-06, RP-02)

| Measurement | Value | Scope / what it is not |
|---|---|---|
| R02 `environment.json` (reported) | CPU 86.3 s, wall 88.2 s, peak RSS 209,420,288 B for 250 events | One development run |
| R03 `environment_final.json` (reported) | wall 1,950 s, peak RSS 429,801,472 B | Before repairs |
| R05 prediction phase (`execution.log` timestamps, read) | Start 2026-10-12 13:43Z; fold calibration starts 14:14Z, 18:22Z, 00:23Z, 05:30Z; sealed 2026-10-13 10:22Z (~20.6 h elapsed). Per fold ~4.1, 6.0, 5.1, 4.9 h, each covering 62 episodes plus calibration replay. | Elapsed time including interruptions and memo hits. Single process. Not CPU time. |
| R05 failures | 07:29Z compact-evidence 2 GB cap; 07:32–07:34Z three `FileExistsError` restarts | Execution failures, not science |
| R05 resource amendment | 4,000,000,000 B cap for run plus one active derived episode | A budget, not a measurement |
| R05 finalize `peak_rss_bytes` | 179,617,792 B | **Finalize process only.** Replay peak is unknown; not a deployment benchmark. |
| R05 run size | 2,594,335,265 B recorded; 2.5 GB on disk | — |
| R05 notebooks | Executed in ~1.3–1.8 s each (log timestamps) | They only display saved data |

## 4. Avoiding repeated archive copies and unbounded replay

- Keep one immutable archive copy (here 39.15 GB of TARs plus ~32 GB of extracts already exist; do not re-extract).
- Read members on demand or extract only what is needed into a separate cache.
- Bound every run with a declared event window and a per-frame work cap, recording abstentions.
- Cache per-frame derived features keyed by (input hash, model hash, preprocessing hash).
- Run attacks as on-the-fly transforms, not stored copies.
- Measure peak memory including child processes.

## 5. Notebooks: source versus executed

- **Inventory.** 14 source notebooks in `notebooks/`; 99 `.ipynb` files including artifacts. Only `R01_development_intake.ipynb` has stored outputs in the source copy (5 code cells, 7 outputs). The rest are templates whose executed copies live in artifact runs.
- **R05 notebooks** (`R05_segment_timelines.ipynb` ×4, `R05_grouped_evaluation.ipynb`): 7 code cells each. They verify the prediction seal, then `display(rows[:8])`, `display(grouped[:18])` and saved PNGs. They compute nothing new; re-running them only re-displays.
- **S notebooks** call the fixture generators; their outputs illustrate arithmetic only.
- R01–R04 notebooks load saved tables/figures and run small checks.

## 6. Acceptance criteria for the next project's notebooks

Each notebook should:

1. State one question, the population, the runtime inputs and the falsification condition.
2. Load one real frame with units, frame and clock provenance. Show placeholders/no-returns explicitly.
3. Run the actual preprocessing → encoder → reliability step through importable functions, and display intermediate arrays (feature-map slices, support/conflict counts, unknown masks).
4. Derive the equation and work one hand counterexample.
5. Evaluate against GT, and show one success, one miss, one benign false rejection and one honest unique view.
6. Report the complete small grid with denominators and undefined cells, not `head()`.
7. Record environment, model hash and resource use. Keep expensive steps optional, explicit and cached. Opening a notebook must not trigger extraction or training.
