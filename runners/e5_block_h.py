"""E5a-H: the frozen D-56 comparison set on the block-H caches (D-57). Driver only.

Calls runners/e5_analyze.analyze() (frozen at a9468e0, unchanged) on runs/20261023-E4/cache with
clean + 4 original families + spoof_blind, and applies the D-57 rule. Block H is exposed (D-53): the
output is development / quasi-held-out, not a test result. dev=True only adds the float16-vs-float64
ray-count check (analyze's sole use of that flag). B-RAY ray counts come from the float16 cached scan.

  python runners/e5_block_h.py --out runs/20261024-E5/H
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e5_analyze as E  # noqa: E402

H_CACHE = os.path.join(ROOT, "runs/20261023-E4/cache")
D57_KEY = "paired_mean_orig|R1-B-RAY"


def d57(out):
    ci = out["bootstrap_block10"][D57_KEY]["ci95"]
    keep_r1 = ci[0] > 0
    return {"rule": "D-57: R1 - B-RAY paired dAP@0.7, mean of 4 original families, 10-frame-block bootstrap "
                    "stratified by scenario, 2000 resamples, seed 0; CI low > 0 -> R1 primary, else B-RAY primary "
                    "and R1 key secondary",
            "point": out["point"][D57_KEY], "ci95_block10": ci,
            "ci95_scenario_4blocks": out["bootstrap_scenario"][D57_KEY]["ci95"],
            "ci_low_gt_0": bool(keep_r1),
            "primary": "R1" if keep_r1 else "B-RAY", "key_secondary": "R1 - B-RAY" if keep_r1 else "R1"}


def v2_check(files, conds, out_dir, n_boot):
    """D-59 verification (development): criteria_v2 on the block-H caches against the stored e5a_H.json;
    B-RAY / R1 point estimates and 95% CIs must be reproduced exactly."""
    h = json.load(open(os.path.join(ROOT, out_dir, "e5a_H.json")))
    c = E.analyze_v2(files, conds, h, n_boot)
    t = c["co_test_vs_no_defense"]
    chk = {}
    for m in ("B-RAY", "R1"):
        k = f"mean_delta_orig|{m}"
        chk[k] = {"point": [t[m]["point"], h["point"][k]], "ci95_scenario": [t[m]["ci95_scenario"],
                  h["bootstrap_scenario"][k]["ci95"]], "ci95_block10": [t[m]["ci95_block10"], h["bootstrap_block10"][k]["ci95"]]}
        k = f"rel_loss|{m}"
        r = (c["primary"] if m == "B-RAY" else c["key_secondary"])["clean_rel_loss"]
        chk[k] = {"point": [r["point"], h["point"][k]], "ci95_scenario": [r["ci95_scenario"], h["bootstrap_scenario"][k]["ci95"]]}
    k = "paired_mean_orig|R1-B-RAY"
    chk[k] = {"point": [c["R1_minus_BRAY"]["point"], h["point"][k]],
              "ci95_scenario": [c["R1_minus_BRAY"]["ci95_scenario"], h["bootstrap_scenario"][k]["ci95"]]}
    exact = all(a == b for v in chk.values() for a, b in v.values())
    res = {"label": "DEVELOPMENT, block H (exposed, D-53); verification of criteria_v2, not a test",
           "reproduces_e5a_H_exactly": exact, "comparison_[criteria_v2, e5a_H]": chk, "criteria_v2": c}
    json.dump(res, open(os.path.join(ROOT, out_dir, "criteria_v2_H.json"), "w"), indent=1, default=str)
    print(json.dumps({"reproduces_e5a_H_exactly": exact, "co_test": t, "success": c["success"],
                      "R1_minus_BRAY": c["R1_minus_BRAY"], "oracle": c["B-RAY_oracle_reference"]}, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261024-E5/H")
    ap.add_argument("--n_boot", type=int, default=E.N_BOOT)
    ap.add_argument("--v2_check", action="store_true", help="criteria_v2 on H vs the stored e5a_H.json")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(H_CACHE, "20*_[0-9][0-9].pkl.gz")))
    conds = ("clean",) + E.ORIG + ("spoof_blind",)
    if a.v2_check:
        return v2_check(files, conds, a.out, a.n_boot)
    out = {"mode": "block_H", "label": "DEVELOPMENT / quasi-held-out, block H (exposed, D-53); not a test",
           "code": "runners/e5_analyze.analyze at a9468e0, unchanged"}
    out.update(E.analyze(files, conds, True, a.n_boot))
    out["D57"] = d57(out)
    os.makedirs(os.path.join(ROOT, a.out), exist_ok=True)
    p = os.path.join(ROOT, a.out, "e5a_H.json")
    json.dump(out, open(p, "w"), indent=1, default=str)
    print(json.dumps({k: out[k] for k in ("frames", "n_agents_hist", "numpy_ap_vs_opencood_max_abs_diff", "D57")},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
