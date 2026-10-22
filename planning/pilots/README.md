# Pilot evidence (disposable; NOT final evaluation)

These two checks were run on 2026-10-22 to answer concrete design questions. Both used only
`mini_7` of Mixed Signals, a segment already exposed by the old Valid Point project
(see [exposure ledger](../exposure_ledger.csv)). They read the old project's data folder
read-only (`~/Code/valid-point/data/mixed_signals/1a61aea…/`). They wrote nothing there and
imported no old code.

- Environment: a throwaway `uv` venv with Python 3.12.13 and NumPy 2.1.3. It is not the project environment.
- Hardware: Apple M1, 8 GB RAM. Runtime: 2.8 s (P1) and 17.4 s (P2).
- To rerun, adjust `ROOT` inside the scripts, then:
  ```
  python -I p1_grid_and_labels.py > p1_out.json
  python -I p2_moving_labels_and_tilt.py > p2_out.json
  ```

| ID | Question | Result | What it does **not** establish |
|---|---|---|---|
| P1-a | Is each organized PCD a beam grid? | `laser`: per-row elevation spread 0.08° (median std), column azimuth step −0.352°, rows strictly ordered. Tilted streams (003, 004, top) show 10–14° per-row spread before correction. | Holds for one frame per stream. Firing order and per-point time are still unknown. |
| P1-b | Where do placeholder (repeated-origin) slots point? | 003: 38% of rows below −5° are placeholders (004: 46%; laser: 1.4%). top: 61% of rows above 0° (sky). | Why a slot is empty (sky, self-occlusion, min-range, low reflectivity) is unknown. **No placeholder may be treated as free-space evidence.** |
| P1-c | Are label members contiguous? | mini_7: 290 members, ids 1–290, no gaps. Sync ids 0 and 291–298 have no label file, so they are *unlabelled*, not *empty*. | Says nothing about other segments. |
| P2-a | Can one mounting rotation make every row constant-elevation? | 003: rotation about y of −15.0° brings the row spread from 9.92° to 0.117°, matching the paper's stated 15° EV tilt. top: (rx, ry) = (−22.25°, −6.75°) brings it from 13.7° to 0.109°. This tilt is undocumented. | Coarse grid search on one frame. No metrology. The top tilt must be cross-checked (e.g. ground-plane fit) before use. |
| P2-b | Does label k match cloud k? Moving boxes only, RSU points counted inside boxes. | Best offset per sampled frame: 0, +1, +1, +3 (n = 4 frames, 1–2 moving boxes each). **Inconclusive.** | The points-in-box count is confounded by objects moving into denser regions. Labels are 1 Hz keyframes plus interpolation (paper §3.3). A stronger test is planned in Stage 1 ([roadmap](../implementation_roadmap.md)). |

## P3: segment recording times (metadata only)

- **Method.** For each of the 33 public train and val archives on Hugging Face (sha `1a61aea…`), an HTTP range request fetched only the first 64 KB. That holds the tar headers plus the first rows of the first odometry CSV. Content cost: about 2 MB in total. No point clouds and no labels were read, so nothing was exposed.
- **Output.** [p3_segment_start_times.csv](p3_segment_start_times.csv).
- **Result.**
  - All 33 public segments start within **34.9 minutes** of each other: mini_1 at 1712120748.6 s (2024-04-03 UTC), mini_37 at +34.86 min.
  - Consecutive gaps are 38–237 s, and each segment lasts about 30 s.
  - The four withheld test segments must fall in the larger gaps:
    - mini_4/5 between mini_3 and mini_6 (gap 236.8 s);
    - mini_17 between mini_16 and mini_18 (130.8 s);
    - mini_21 between mini_20 and mini_22 (104.9 s).
  - mini_1–3 have empty 003/004 odometry: only the `laser` vehicle is present.
- **Consequence.**
  - Mixed Signals is effectively **one ~35-minute session at one intersection**, with the same vehicles looping.
  - The paper's "no temporal overlap" holds only in the sense of no shared frames: test segments are tens of seconds from training segments.
  - Any MINT test on Mixed Signals is a **held-out time block of a single session**, not an independent session. Claims must be worded that way (D-12, R-08).
- **Does not establish.** Exact segment end times; whether the paper's "two hours" refers to the raw logging span.

Decisions informed: D-07, D-11 and D-12 in the [decision log](../decision_log.md), and R-04, R-05 and R-08 in [risks](../risks_and_open_questions.md).

SHA-256 of the files at creation:
- `p1_grid_and_labels.py` c00044936ee0ea17b68e160a3d262916162ade5379a62cc65330afd7f1fa897d
- `p1_out.json` 788b36c1f64217809d4de6d4440c6df31693cbf83a6ba1097d9e9e6c4a8dd7d9
- `p2_moving_labels_and_tilt.py` 116d01d851bcd8357dcd81559f95dfc95c20c979dcb11e11dab66ace353dd73f
- `p2_out.json` 3ea78a81a02b8a420d906aab0a44f0a1c452a63cb4c8032ae53b3697fcb4ef57
