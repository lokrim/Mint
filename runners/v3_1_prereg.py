"""Write runs/20261024-E5/preregistration_v3_1.json = preregistration_v3.json + D-70 (v1/v2/v3 unchanged), and
the runtime estimate runs/20261024-E5/v3_1_runtime_estimate.json from the v3.1 dry run.

  python runners/v3_1_prereg.py --frozen_commit <sha> [--dryrun runs/20261024-E5/dryrun_v3_1]
"""
import argparse
import copy
import glob
import gzip
import hashlib
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3 = "runs/20261024-E5/preregistration_v3.json"
OUT = "runs/20261024-E5/preregistration_v3_1.json"
RT = "runs/20261024-E5/v3_1_runtime_estimate.json"
NEW_FROZEN = ("runners/v3_1_stream.py", "runners/v3_1_dryrun.py")
D70 = (("pgd_untargeted_stealth", 1.0), ("pgd_remove_stealth", 1.0))
LABEL = "strong-attack level, added after seeing block-H development results"
S1 = "runs/20261023-S1-reproduce/scenarios"
EXCLUDED = "2021_08_23_12_58_19"


def sha(p):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, p), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def diff_paths(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in list(a) + [k for k in b if k not in a]:
            if k not in b:
                out.append(f"{path}/{k}: removed")
            elif k not in a:
                out.append(f"{path}/{k}: added")
            else:
                out += diff_paths(a[k], b[k], f"{path}/{k}")
        return out
    return [] if a == b else [f"{path}: changed"]


def runtime(dry, v3_est):
    """v3 estimate (unchanged) + the D-70 conditions' PGD cost measured per condition in the v3.1 dry run
    (attack_s; n = 1: 0), linear in n between n = 1, 2, 5, applied to the 2066 test frames with the Stage-1
    mean agent count per scenario (the v3 method)."""
    sys.path.insert(0, os.path.join(ROOT, "runners"))
    import e0_stream  # noqa: F401  (shims + paths, needed to unpickle the records)
    cost = {}
    for tag in ("n2", "n5"):
        ex = []
        for p in glob.glob(os.path.join(ROOT, dry, tag, "v3extra", "*.pkl.gz")):
            with gzip.open(p, "rb") as f:
                ex += pickle.load(f)["frames"]
        for c in {c for e in ex for c in e["pgd"]}:
            v = [e["pgd"][c]["attack_s"] for e in ex if "attack_s" in e["pgd"].get(c, {})]
            cost.setdefault(c, {})[tag] = round(sum(v) / len(v), 2)
    rows = []
    for p in sorted(glob.glob(os.path.join(ROOT, S1, "*.json"))):
        d = json.load(open(p))
        if d["scenario"] != EXCLUDED:
            rows.append((d["frames"], d["agents"]["mean"]))
    assert sum(f for f, _ in rows) == 2066 and len(rows) == 15

    def s(n, c2, c5):
        return (n - 1) * c2 if n <= 2 else c2 + (n - 2) * (c5 - c2) / 3
    hours = {c: round(sum(f * s(n, v["n2"], v["n5"]) for f, n in rows) / 3600, 2) for c, v in cost.items()}
    new = [f"{f}@r{r}" for f, r in D70]
    add = round(sum(hours[c] for c in new), 2)
    est = {"basis": "v3 estimate (preregistration_v3.json estimated_runtime, unchanged) plus the cost of the two D-70 "
                    "conditions, measured per condition (PGD attack_s) in the v3.1 dry run on this machine "
                    f"({dry}; n = 1: none), linear in n between n = 1, 2, 5, applied to the 2066 test frames "
                    "with the Stage-1 mean agent count per scenario; estimate only",
           "v3_total_h": v3_est["total_h"], "v3_range_h": v3_est["range_h"],
           "pgd_cost_per_condition_s_per_frame_v3_1_dryrun": cost,
           "pgd_cost_per_condition_h_v3_1_dryrun": hours,
           "D-70_added_h": add,
           "total_h": round(v3_est["total_h"] + add, 1),
           "range_h": [round(v3_est["range_h"][0] + 0.85 * add, 1), round(v3_est["range_h"][1] + 1.25 * add, 1)],
           "analysis": "e5_analyze test (frozen v2) under 1 h; v3_analyze test about 1.5-2.5 h (16 conditions x 6 "
                       "methods x 2 AP definitions x 2 bootstraps of 2000 + realized-only)"}
    return est


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen_commit", required=True)
    ap.add_argument("--dryrun", default=None)
    a = ap.parse_args()
    v3 = json.load(open(os.path.join(ROOT, V3)))
    changed = {p: (h, sha(p)) for p, h in v3["frozen_sha256"].items() if sha(p) != h}
    if changed:
        sys.exit(f"STOP: a v3-frozen file changed: {changed}")
    H = json.load(open(os.path.join(ROOT, "runs/20261024-PGD/pgd_stealth_H_results.json")))
    feas = json.load(open(os.path.join(ROOT, "runs/20261024-PGD/stealth_feasibility_by_r.json")))
    pr = copy.deepcopy(v3)
    pf = pr["pgd_families"]
    sig = pf["sigma_k"]
    conds = []
    for fam, r in D70:
        c = f"{fam}@r{r}"
        assert H["pgd_selection"][fam]["selected_r"] != r
        conds.append({"family": fam, "r": r, "eps_k": [r * x for x in sig], "condition": c,
                      "H_development_seen_before_D70_global": {
                          "attack_loss": H["point"]["global"][f"attack_loss|{c}"],
                          "B-NORM_catch": H["B-NORM_flags"][c]["catch_rate"],
                          "recovery": {m: H["point"]["global"].get(f"recovery|{m}|{c}") for m in ("B-RAY", "R1", "B-NORM")}}})
    pf["D-70_strong_level"] = {
        "decision": "D-70 (planning/decision_log_proposed_appendix.md; the user's decision in chat, 2026-10-24; post hoc)",
        "label": LABEL,
        "role": "additional pre-registered SECONDARY conditions, run IN ADDITION to the v3 test levels (which are unchanged); "
                "reported per family like every PGD condition (per-family table, realized-only, B-NORM flags, stealth-infeasible "
                "counts); NOT part of the primary, the v2 success rule, D-64, the mean-of-3 or any criterion",
        "attack": "D-68 as amended twice, unchanged (objective, 10 steps, step eps_k/4, random start, exact stealth projection, "
                  "infeasible frames not applied and scored as clean, seed V3PGD|family|r|scenario|frame); eps_k = 1.0 x sigma_k",
        "conditions": conds,
        "stealth_feasibility_H_r1.0": {k: feas["r1.0"][k] for k in ("frames", "infeasible_frames", "infeasible_by_scale")},
        "expected_outcomes": "the D-68 expectations and operational checks are reported for these conditions too (descriptive)",
        "code": "runners/v3_1_stream.py: levels_v31 = v3 test levels + these conditions; run_scenario = the frozen "
                "v3_stream.run_scenario with these levels (PGD timed per condition); install() swaps v3_stream.PREREG and "
                "v3_stream.run_scenario, then the frozen v3_stream.main runs unchanged. Analysis: frozen v3_analyze with "
                "--prereg preregistration_v3_1.json (conditions are read from test_conditions; no code change)"}
    pf["test_conditions"] = pf["test_conditions"] + [c["condition"] for c in conds]
    pr["id"] = "E5 v3.1 - preregistration_v3 plus D-70 (stealth PGD families also at r = 1.0, secondary, " + LABEL + ")"
    pr["version"] = ("v3.1 (supersedes v3 runs/20261024-E5/preregistration_v3.json only by D-70; v1, v2 and v3 kept "
                     "unchanged)")
    pr["written"] = ("2026-10-24, after the v3 dry run and before any test-scenario byte is downloaded. NOT RUN: the "
                     "stream needs the user's explicit approval of the final test.")
    pr["base"] = ("Every field of preregistration_v3.json holds as written unless listed in difference_from_v3 "
                  "(and through v3, every field of preregistration_v2.json)")
    pr["user_decisions"] = v3["user_decisions"] + "; D-70 (the user's decision in chat, 2026-10-24; committed 2c50ef0 before any v3.1 code or run)"
    pr["frozen_code_commit"] = a.frozen_commit
    for p in NEW_FROZEN:
        pr["frozen_sha256"][p] = sha(p)
    pr["frozen_note"] = ("v3's frozen files (all re-checked equal to preregistration_v3.json) + runners/v3_1_stream.py and "
                         "runners/v3_1_dryrun.py. The v3.1 stream verifies every hash and the OpenCOOD commit before any "
                         "network access and again after the run (frozen v3_stream.main/verify_frozen).")
    pr["streaming"]["runner"] = ("caffeinate -ims .venv/bin/python runners/v3_1_stream.py --run_dir runs/<date>-E5v3 "
                                 "--user_approved (refuses without it; = the frozen v3_stream.main with the v3.1 "
                                 "levels and preregistration)")
    pr["analysis"] = ["python runners/e5_analyze.py test --run_dir runs/<date>-E5v3   (frozen v2 analysis -> e5_test.json)",
                      "python runners/v3_analyze.py test --run_dir runs/<date>-E5v3 --prereg runs/20261024-E5/preregistration_v3_1.json   "
                      "(v3 -> e5_v3.json: criteria_v3 per AP definition, D-64 verdict, tables incl. the D-70 conditions)"]
    if a.dryrun:
        est = runtime(a.dryrun, v3["estimated_runtime"])
        json.dump(est, open(os.path.join(ROOT, RT), "w"), indent=1)
        pr["estimated_runtime"] = est
        pr["dry_run_v3_1"] = json.load(open(os.path.join(ROOT, a.dryrun, "dryrun_v3.json")))
    else:
        pr["dry_run_v3_1"] = "pending"
    pr["user_decisions_v3_1"] = "D-70 (committed 2c50ef0 before any v3.1 code or run)"
    pr["difference_from_v3"] = diff_paths(v3, pr)
    json.dump(pr, open(os.path.join(ROOT, OUT), "w"), indent=1, default=str)
    print("written", OUT)
    print("\n".join(pr["difference_from_v3"]))


if __name__ == "__main__":
    main()
