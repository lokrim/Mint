# Proposed D-71: fix the final-test crash on stealth-infeasible frames (draft, not applied)

Status: **approved by the user in chat (2026-10-24), implemented as new files** (`runners/v3_2_stream.py`,
`runners/v3_2_dryrun.py`, `runners/v3_2_prereg.py`, `tests/test_v3_2.py`,
`runs/20261024-E5/preregistration_v3_2.json`). Not committed; final test not relaunched. Written 2026-10-24 after
the v3.1 final-test stream crashed.

(The number D-71 also appears in `planning/windows_gpu_handoff_prompt.md` as a draft for a GPU entry. That handoff
was never used, so D-71 is free. Renumber if you prefer.)

## 1. What happened

- Run: `runs/20261024-E5v3`, launched 20:00 with `runners/v3_1_stream.py --user_approved` (frozen code 605a978,
  `runs/20261024-E5/preregistration_v3_1.json`). Hash check and budget check passed.
- First scenario `2021_08_18_19_48_05` downloaded completely (ledger status `complete`, 1 128 667 845 bytes, 148 s).
- Processing of that scenario finished frame 0, then crashed at 20:04:10 on a later frame (frame 1, 2 or 3; the log
  only prints every 20th frame):

```
File "runners/v3_1_stream.py", line 73, in v3_extra
    mabs[c] = r["mabs"]
KeyError: 'mabs'
```

- The process exited. No result file was written: `cache/` and `v3extra/` are empty, because results are written
  only after a whole scenario finishes.

## 2. Cause

`V.pgd_conditions` ([runners/v3_common.py:169-172](../runners/v3_common.py)) follows D-68 amendment 2: when a
stealth attack is infeasible, the attack is not applied and the frame is scored as clean. It stores that condition as
`{"ledger": led}` with **no `"mabs"` key**, because no attacked features exist.

`v3_extra` in [runners/v3_1_stream.py:72-73](../runners/v3_1_stream.py) then copies `r["mabs"]` for **every**
condition, with no check, so the first infeasible frame raises `KeyError`.

- The same unchecked line is in the frozen v3 code ([runners/v3_stream.py:97](../runners/v3_stream.py)). The bug
  predates D-70; D-70 only copied it. The v3.1 run does not call the v3 version (v3.1 has its own `v3_extra`).
- It was never triggered before. Infeasible frames did occur on block H (13/371 at r = 0.25, 1/371 at r = 0.5,
  0 at r = 1.0; `runs/20261024-PGD/stealth_feasibility_by_r.json`), but the H runs used `runners/pgd_h_run.py`,
  which stores the `pgd_conditions` records directly and never runs this copy loop. The stream's `v3_extra` ran only
  in the dev-slice dry runs, which had no infeasible frame. (Corrected 2026-10-24 after approval: the first draft
  wrongly said H had 0 infeasible frames at every level.)
- The other code paths already handle the case correctly:
  - the frozen analysis, [runners/v3_analyze.py:105-107](../runners/v3_analyze.py) (`frames_test`), copies
    `rec["mabs"]` only `if "mabs" in rec`, and scores a non-applied condition with the clean magnitudes
    (`use = cond if applied else "clean"`, line 142);
  - `stealth_constraint_check` (v3_analyze.py:533-535) skips records without `mabs` after asserting the ledger
    reason is `stealth_infeasible`.

So the stream is the only part that does not follow the pre-registered rule "infeasible frames not applied, scored as
clean". The rule itself does not need to change.

## 3. Proposed minimal fix

Change the copy loop in `v3_extra` to match the analysis: skip records without `mabs`, and fail loudly if one is
missing for any reason other than stealth infeasibility.

```python
    for c, r in pgd.items():
        if "mabs" not in r:                                  # D-68 am. 2: stealth infeasible, not applied
            assert r["ledger"].get("reason") == "stealth_infeasible", (c, r["ledger"])
            continue
        mabs[c] = r["mabs"]
```

Effect on stored data:
- Feasible frames: byte-identical records (same seeds, same code path).
- Infeasible frames: `pgd[c]` keeps `{"ledger": ..., "attack_s": ...}` exactly as `pgd_conditions` returns it, and
  `mabs` has no entry for `c`. That is the shape the frozen analysis already expects.

No change to any method, attack, level, seed, condition, criterion, the primary, or the analysis code.

### How to apply it without touching frozen files (recommended)

`runners/v3_1_stream.py` is listed in `frozen_sha256`, so editing it would make the stream refuse to start. Follow
the same pattern as v3 → v3.1 (new files only):

1. **New file `runners/v3_2_stream.py`:** imports `v3_1_stream as S31`, defines the fixed `v3_extra` (a copy of
   `S31.v3_extra` with only the loop above changed), and `install()`:
   `S31.install()`, then `S31.v3_extra = v3_extra`, `S31.PREREG_V31 = PREREG_V32`, `S3.PREREG = PREREG_V32`.
   `S31.run_scenario` looks up `v3_extra` and `PREREG_V31` at call time, so both patches take effect.
2. **New `runs/20261024-E5/preregistration_v3_2.json`** = v3.1 + exactly this difference: a D-71 entry, and
   `frozen_sha256` = the v3.1 list + `runners/v3_2_stream.py` (+ its test). The `test_conditions` and every
   criterion are unchanged.
3. **Test** (`tests/test_v3_2.py`): (a) a stubbed `pgd_conditions` returning one infeasible record → `v3_extra`
   runs, the condition is absent from `mabs` and present in `pgd` with its ledger; (b) a record missing `mabs` with
   any other ledger reason → `AssertionError`; (c) `install()` wiring, as in `tests/test_v3_1.py`.
4. **Dry run** (development data only, no test bytes): fixed `v3_extra` output identical to the v3.1 output on the
   dry-run frames (none are infeasible there), as `runners/v3_1_dryrun.py` already checks for v3 → v3.1.
5. Code freeze commit, then `--dry_run` (hash + budget), then relaunch on the user's approval.

Alternative: edit line 73 of `v3_1_stream.py` in place and re-freeze its hash in a v3.2 preregistration. Smaller diff,
but it changes a frozen file, which the project has avoided so far.

## 4. Restarting the run

- The ledger has no interrupted download, so the stream's STOP rule does not trigger.
- `data/opv2v/stream/.complete_2021_08_18_19_48_05` exists, so a restart prints "reusing complete extraction" and
  **does not download scenario 1 again**. Bytes already counted: 1.129 GB of the 22.0 GB budget (projected total
  20.64 GB, unchanged).
- Suggested: reuse the same run dir `runs/20261024-E5v3` (its ledger already holds the precheck and the scenario-1
  download), with `run.log` moved aside to `run_crash_20261024T2004.log`. Or start a fresh run dir and copy the
  ledger, if you'd rather keep the crashed attempt untouched.

## 5. Exposure note (for exposure_ledger.csv)

What was seen from test data before this decision:
- the frame-0 timing line for scenario `2021_08_18_19_48_05` (6.4 s + 22.8 s);
- the crash itself, which implies **at least one stealth condition was infeasible on at least one of frames 1-3 of
  that scenario**. Which condition, and how many frames, is not known.

Infeasible counts are a pre-registered *reported* quantity (D-68 amendment 2), not a criterion, and no AP, loss,
flag or recovery value was seen. The fix is mechanical and was chosen to match the frozen analysis, not any
result.

## 6. Decision row (for decision_log_proposed_appendix.md, if approved)

| ID | Decision | Alternatives | Reason | Source |
|---|---|---|---|---|
| D-71 | **Stream bug fix, no method change:** in the stream's `v3_extra`, a PGD record without `mabs` (stealth infeasible, D-68 am. 2) is skipped when copying B-NORM magnitudes, with an assertion that the ledger reason is `stealth_infeasible`. This matches the frozen `v3_analyze.frames_test`. Applied as new files `runners/v3_2_stream.py` + `preregistration_v3_2.json` (v3.1 + exactly this); v3/v3.1 frozen files unchanged. The v3.1 final-test attempt crashed on the first infeasible frame (scenario `2021_08_18_19_48_05`, frame 1-3) before writing any results; the run restarts from the already-downloaded scenario. Seen before this decision: one frame-0 timing line and the fact of ≥ 1 infeasible frame. | Edit `v3_1_stream.py` in place and re-freeze its hash; treat the crash as ending the final test | The pre-registered rule (infeasible → not applied, scored as clean) is unchanged; only the stream failed to follow it. The H runs used a different runner (`pgd_h_run.py`) without this loop, and the dev-slice dry runs had no infeasible frame, so the branch was never exercised | User decision (approved in chat, 2026-10-24) |
