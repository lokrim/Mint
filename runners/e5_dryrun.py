"""E5 no-network dry run (D-59): the frozen final-test pipeline end to end on the local block-T dev slice.

e5_stream.run_scenario (data pass + time_frame_e5 timing, incl. B-RAY) on the 24-frame dev slice of
2021_08_22_13_37_16 (data/opv2v/devslice; already on disk, no network), once at its real n = 2 and once
with n forced to 1 (OpenCOOD train_params.max_cav = 1: only the receiver is loaded); then, on each cache,
exactly what `e5_analyze.py test` computes: analyze(), criteria() (v1, superseded) and analyze_v2()
(criteria_v2). DEVELOPMENT smoke test; numbers are not results (1 scenario, 24 frames).

  python runners/e5_dryrun.py --out runs/20261024-E5/dryrun [--n_boot 200]
"""
import argparse
import copy
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e5_stream as S  # noqa: E402
import e5_analyze as X  # noqa: E402
from stage1_reproduce import CKPT  # noqa: E402

import torch  # noqa: E402

SCEN = "2021_08_22_13_37_16"
DEV_ROOT = os.path.join(ROOT, "data/opv2v/devslice/validate")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261024-E5/dryrun")
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    conds = ("clean",) + X.ORIG + ("spoof_blind",)
    summary = {"label": "DRY RUN (development, block-T dev slice, no network); not results",
               "scenario": SCEN, "n_boot": a.n_boot, "runs": {}}
    for tag, max_cav in (("n2", None), ("n1", 1)):
        h = copy.deepcopy(hyp)
        if max_cav is not None:
            h.setdefault("train_params", {})["max_cav"] = max_cav
        cdir = os.path.join(ROOT, a.out, tag, "cache")
        os.makedirs(cdir, exist_ok=True)
        p = os.path.join(cdir, f"{SCEN}.pkl.gz")
        t0 = time.time()
        res = S.run_scenario(SCEN, DEV_ROOT, model, h, p, reps=a.reps)
        t_stream = time.time() - t0
        nag = sorted({f["n_agents"] for f in res["frames"]})
        tm = res["timing"]
        bray_all = all("B-RAY" in t and t["B-RAY"]["baseline_s"] > 0 for t in tm)
        shared = all(t[m]["baseline_s"] == t["B-RAY"]["baseline_s"] for t in tm for m in ("dense", "trigger_0.05")
                     if m in t)
        t1 = time.time()
        out = X.analyze([p], conds, False, a.n_boot)
        v1 = X.criteria(out) if max_cav is None else "not computed: no senders at n = 1 (R1 = no defense)"
        v2 = X.analyze_v2([p], conds, out, a.n_boot)
        summary["runs"][tag] = {
            "frames": len(res["frames"]), "n_agents": nag, "stream_s": round(t_stream), "analysis_s": round(time.time() - t1),
            "compose_checks": len(res["compose_checks"]),
            "compose_all_identical": all(c["same_candidates"] and c["same_final"] for c in res["compose_checks"]),
            "yplus_rays_present": all("yplus_rays" in c for f in res["frames"] for c in f["conditions"].values()
                                      if "cands" in c),
            "timing_frames": len(tm), "bray_timed_every_frame": bray_all, "bray_shares_mint_baseline": shared,
            "overhead": out.get("overhead"), "criteria_v2": v2,
            "criteria_v1_superseded_success": v1 if isinstance(v1, str) else v1["success"]}
        print(tag, json.dumps({k: v for k, v in summary["runs"][tag].items() if k not in ("criteria_v2", "overhead")}),
              flush=True)
    json.dump(summary, open(os.path.join(ROOT, a.out, "dryrun.json"), "w"), indent=1, default=str)
    print("dry run done", flush=True)


if __name__ == "__main__":
    main()
