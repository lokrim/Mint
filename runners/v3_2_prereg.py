"""Write runs/20261024-E5/preregistration_v3_2.json = preregistration_v3_1.json + D-71 (v1/v2/v3/v3.1 unchanged).

  python runners/v3_2_prereg.py [--frozen_commit <sha>] [--dryrun runs/20261024-E5/dryrun_v3_2]
"""
import argparse
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
from v3_1_prereg import diff_paths, sha  # noqa: E402

V31 = "runs/20261024-E5/preregistration_v3_1.json"
OUT = "runs/20261024-E5/preregistration_v3_2.json"
NEW_FROZEN = ("runners/v3_2_stream.py", "runners/v3_2_dryrun.py", "tests/test_v3_2.py")
CRASHED_RUN = "runs/20261024-E5v3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen_commit", default=None)
    ap.add_argument("--dryrun", default=None)
    a = ap.parse_args()
    v31 = json.load(open(os.path.join(ROOT, V31)))
    changed = {p: (h, sha(p)) for p, h in v31["frozen_sha256"].items() if sha(p) != h}
    if changed:
        sys.exit(f"STOP: a v3.1-frozen file changed: {changed}")
    ledger = json.load(open(os.path.join(ROOT, CRASHED_RUN, "download_ledger.json")))
    pr = copy.deepcopy(v31)
    pr["D-71"] = {
        "decision": "D-71 (planning/decision_log_proposed_D71_crash_fix.md; the user's approval in chat, 2026-10-24)",
        "kind": "stream bug fix; NO change to any method, attack, level, seed, condition, criterion, the primary or "
                "the analysis code",
        "bug": "the stream's v3_extra (runners/v3_1_stream.py:72-73, and the same line in runners/v3_stream.py:97) "
               "copied r['mabs'] for every PGD record; a stealth-infeasible record (D-68 amendment 2: not applied, "
               "scored as clean) is {'ledger': ...} without 'mabs' -> KeyError",
        "fix": "runners/v3_2_stream.py: v3_extra = the v3.1 v3_extra with the copy loop replaced by copy_mabs: a record "
               "without 'mabs' is skipped after asserting ledger reason == 'stealth_infeasible' (any other cause still "
               "fails). Same reading as the frozen v3_analyze.frames_test ('if \"mabs\" in rec') and cond_of (no "
               "'cands' -> clean, not applied). install() = v3.1 install() + v3_extra and preregistration swapped; "
               "v3/v3.1 frozen files byte-identical",
        "crashed_attempt": {
            "run_dir": CRASHED_RUN, "code": "runners/v3_1_stream.py (frozen 605a978), preregistration_v3_1.json",
            "started": ledger["precheck"]["time"],
            "crash": "KeyError 'mabs' at runners/v3_1_stream.py:73 on frame 1-3 of the first scenario, 20:04:10",
            "downloads": ledger["downloads"],
            "results_written": "none (cache/ and v3extra/ empty; results are written per completed scenario)",
            "seen_before_D71": "the frame-0 timing line of 2021_08_18_19_48_05 (6.4 s + 22.8 s) and the fact that "
                               ">= 1 stealth condition was infeasible on >= 1 of its frames 1-3 (condition and count "
                               "unknown); no AP, loss, flag or recovery value"},
        "restart": "the frozen v3_stream.main reuses the complete extraction of 2021_08_18_19_48_05 "
                   "(data/opv2v/stream/.complete_<scen>, no second download; ledger has no interrupted download)"}
    pr["id"] = v31["id"].replace("E5 v3.1", "E5 v3.2", 1) + "; + D-71 (stream bug fix on stealth-infeasible frames)"
    pr["version"] = ("v3.2 (supersedes v3.1 runs/20261024-E5/preregistration_v3_1.json only by D-71; v1, v2, v3 and "
                     "v3.1 kept unchanged)")
    pr["written"] = ("2026-10-24, after the v3.1 final-test attempt crashed on scenario 1 with no results written. "
                     "NOT RUN: relaunching the stream needs the user's explicit approval.")
    pr["base"] = ("Every field of preregistration_v3_1.json holds as written unless listed in difference_from_v3_1 "
                  "(and through v3.1, every field of v3 and v2)")
    pr["user_decisions"] = v31["user_decisions"] + "; D-71 (the user's approval in chat, 2026-10-24)"
    pr["frozen_code_commit"] = a.frozen_commit or "pending: set at the v3.2 code-freeze commit (the hashes below are what the stream enforces)"
    for p in NEW_FROZEN:
        pr["frozen_sha256"][p] = sha(p)
    pr["frozen_note"] = ("v3.1's frozen files (all re-checked equal to preregistration_v3_1.json) + "
                         + ", ".join(NEW_FROZEN) + ". The v3.2 stream verifies every hash and the OpenCOOD commit "
                         "before any network access and again after the run (frozen v3_stream.main/verify_frozen).")
    pr["streaming"] = copy.deepcopy(v31["streaming"])
    pr["streaming"]["runner"] = ("caffeinate -ims .venv/bin/python runners/v3_2_stream.py --run_dir runs/<date>-E5v3 "
                                 "--user_approved (refuses without it; = the frozen v3_stream.main with the v3.1 "
                                 "run_scenario, the D-71 v3_extra and this preregistration)")
    pr["analysis"] = [s.replace("preregistration_v3_1.json", "preregistration_v3_2.json") for s in v31["analysis"]]
    pr["dry_run_v3_2"] = (json.load(open(os.path.join(ROOT, a.dryrun, "dryrun_v3.json"))) if a.dryrun else "pending")
    pr["user_decisions_v3_2"] = "D-71 (the user's approval in chat, 2026-10-24)"
    pr["difference_from_v3_1"] = diff_paths(v31, pr)
    json.dump(pr, open(os.path.join(ROOT, OUT), "w"), indent=1, default=str)
    print("written", OUT)
    print("\n".join(pr["difference_from_v3_1"]))


if __name__ == "__main__":
    main()
