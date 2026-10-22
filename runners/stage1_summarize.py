"""Summarise a stage1_reproduce run: pooled AP (OpenCOOD default and global-sort), per-scenario
AP, locality results by agent count, download/disk/timing. Writes summary.json and summary.md.

  python runners/stage1_summarize.py runs/<id> [--exclude SCEN ...]
"""
import argparse
import copy
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "third_party", "OpenCOOD"))
from mint.model import opencood_shims  # noqa: E402

opencood_shims.install()
import numpy as np  # noqa: E402
from opencood.utils import eval_utils  # noqa: E402

IOUS = (0.3, 0.5, 0.7)
PUBLISHED = {"AP@0.7": 0.815, "source": "OpenCOOD README, PointPillar Attentive Fusion, Default Towns, no compression"}


def pooled(stats):
    s = {k: {"tp": [], "fp": [], "gt": 0, "score": []} for k in IOUS}
    for st in stats:                       # in OpenCOOD's sorted scenario order
        for k in IOUS:
            kk = str(k) if str(k) in st else k
            for f in ("tp", "fp", "score"):
                s[k][f] += st[kk][f]
            s[k]["gt"] += st[kk]["gt"]
    out = {}
    for gs in (False, True):
        for k in IOUS:
            out[f"AP@{k}{'_globalsort' if gs else ''}"] = round(
                float(eval_utils.calculate_ap(copy.deepcopy(s), k, gs)[0]), 4)
    out["n_gt"] = s[0.7]["gt"]
    out["n_pred"] = len(s[0.7]["tp"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--exclude", nargs="*", default=[])
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.run_dir, "scenarios", "*.json")))
    R = [json.load(open(f)) for f in files]
    R = [r for r in R if r["scenario"] not in a.exclude]
    loc = [dict(x, scenario=r["scenario"]) for r in R for x in r["locality"] if "skipped" not in x]
    by_n = {}
    for x in loc:
        d = by_n.setdefault(x["n_agents"], {"tests": 0, "bit_identical_outside": 0, "changed_inside": 0,
                                            "changed_outside": 0, "tests_with_inside_change": 0})
        d["tests"] += 1
        d["bit_identical_outside"] += int(x["bit_identical_outside"])
        d["changed_inside"] += x["changed_boxes_centre_inside_tile"]
        d["changed_outside"] += x["changed_boxes_centre_outside_tile"]
        d["tests_with_inside_change"] += int(x["max_abs_change_inside_tile_psm"] > 0)
    summ = {
        "run_dir": os.path.relpath(a.run_dir, ROOT), "scenarios": len(R),
        "excluded": a.exclude,
        "frames": sum(r["frames"] for r in R),
        "pooled_ap": pooled([r["stat"] for r in R]),
        "published_reference": PUBLISHED,
        "per_scenario": [{"scenario": r["scenario"], "frames": r["frames"], "agents": r["agents"],
                          **r["ap_scenario"], "infer_p50_s": r["infer_s"]["p50"],
                          "download_GB": round(r["download"]["bytes_downloaded"] / 1e9, 3),
                          "raw_on_disk_GB": round(r["raw_bytes_on_disk"] / 1e9, 3)} for r in R],
        "locality_by_n_agents": by_n,
        "locality_tests_total": len(loc),
        "locality_all_bit_identical_outside": all(x["bit_identical_outside"] for x in loc),
        "max_raw_on_disk_GB": round(max(r["raw_bytes_on_disk"] for r in R) / 1e9, 3),
        "total_download_GB": round(sum(r["download"]["bytes_downloaded"] for r in R) / 1e9, 2),
        "infer_p50_s_median_over_scenarios": round(float(np.median([r["infer_s"]["p50"] for r in R])), 4),
    }
    with open(os.path.join(a.run_dir, "summary.json"), "w") as f:
        json.dump(summ, f, indent=1)
    lines = [f"# Stage-1 reproduction summary ({summ['run_dir']})", "",
             f"Scenarios {summ['scenarios']}, frames {summ['frames']}, excluded {a.exclude or 'none'}", "",
             "| metric | value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in summ["pooled_ap"].items()]
    lines += ["", "| scenario | frames | agents (min/max/mean) | AP@0.5 | AP@0.7 | infer p50 s | DL GB | raw GB |",
              "|---|---|---|---|---|---|---|---|"]
    for p in summ["per_scenario"]:
        g = p["agents"]
        lines.append(f"| {p['scenario']} | {p['frames']} | {g['min']}/{g['max']}/{g['mean']} | {p['AP@0.5']} | "
                     f"{p['AP@0.7']} | {p['infer_p50_s']} | {p['download_GB']} | {p['raw_on_disk_GB']} |")
    lines += ["", "| agents | tests | bit-identical outside | boxes changed inside | boxes changed outside |",
              "|---|---|---|---|---|"]
    for n in sorted(by_n):
        d = by_n[n]
        lines.append(f"| {n} | {d['tests']} | {d['bit_identical_outside']} | {d['changed_inside']} | {d['changed_outside']} |")
    open(os.path.join(a.run_dir, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
