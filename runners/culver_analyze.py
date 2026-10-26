"""CULVER analysis (D-72): the frozen final-test analyses, unchanged, on the Culver City caches. Offline; GT for scoring only.

Secondary held-out domain-shift evaluation (unseen town, simulated sensor). Exactly what the OPV2V test ran:
  1. frozen v2: e5_analyze analyze() + criteria() (v1, superseded) + analyze_v2() -> e5_test.json
  2. frozen v3: v3_analyze.run_test (preregistration_v3_2.json)                      -> e5_v3.json
Only two things differ, both outside the frozen files: the completeness constants are the Culver plan's
(4 scenarios, 550 frames instead of 15 / 2066), and both outputs are relabelled "CULVER CITY (held-out domain
shift) ..." so nothing can be mistaken for the one-time final test. No method, statistic or bootstrap changes.

  python runners/culver_analyze.py --run_dir runs/20261026-CULVER                    (after the stream finished)
  python runners/culver_analyze.py --run_dir <dry-run dir> --dry --n_boot 200       (dry run; no 4/550 assertion)
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e5_analyze as X  # noqa: E402
import v3_analyze as Y  # noqa: E402

PLAN = "runs/20261026-CULVER/plan.json"
PREREG = "runs/20261024-E5/preregistration_v3_2.json"
LABEL = "CULVER CITY (held-out domain shift; secondary, D-72; unseen town, simulated sensor)"
DRY_LABEL = "DRY RUN of the CULVER analysis (development dev slice; not results)"


def relabel(p, label, extra):
    d = json.load(open(p))
    d["label_frozen_code"] = d.get("label")
    d["label"] = label
    d.update(extra)
    json.dump(d, open(p, "w"), indent=1, default=str)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--n_boot", type=int, default=X.N_BOOT)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    plan = json.load(open(os.path.join(ROOT, PLAN)))
    rd = os.path.join(ROOT, a.run_dir)
    files = sorted(glob.glob(os.path.join(rd, "cache", "20*_[0-9][0-9].pkl.gz")))
    label = DRY_LABEL if a.dry else LABEL
    extra = {"evaluation": "CULVER", "plan": PLAN, "data_label": plan["label"], "role": plan["role"]}

    conds = ("clean",) + X.ORIG + ("spoof_blind",)                     # 1. frozen v2 analysis (e5_analyze main, test)
    out = {"mode": "culver", "label": label}
    out.update(X.analyze(files, conds, False, a.n_boot))
    out["criteria_v1_superseded"] = X.criteria(out)
    out["criteria"] = X.analyze_v2(files, conds, out, a.n_boot)
    out.update(extra)
    json.dump(out, open(os.path.join(rd, "e5_test.json"), "w"), indent=1, default=str)
    print("e5_test.json written", flush=True)

    Y.TEST_SCEN = plan["data"]["expected_scenarios"]                  # 2. frozen v3 analysis, Culver completeness
    Y.TEST_FRAMES = plan["data"]["expected_frames"]
    p3 = os.path.join(rd, "e5_v3.json")
    try:
        Y.run_test(os.path.relpath(rd, ROOT), PREREG, a.n_boot, dry=a.dry)
    except SystemExit:
        relabel(p3, "INCOMPLETE " + label, extra)
        raise
    v3 = relabel(p3, label, extra)
    show = {k: v3[k] for k in ("frames", "criteria_v3", "completeness_check", "consistency_vs_frozen_v2") if k in v3}
    print(json.dumps(show, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
