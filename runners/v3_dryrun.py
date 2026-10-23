"""v3 no-network dry run: the frozen v3 final-test pipeline end to end on the local block-T dev slice.

v3_stream.run_scenario (frozen v2 record + timing, v3 side record: B-NORM magnitudes, PGD at the
pre-registered test levels) on the dev slice of 2021_08_22_13_37_16 (data/opv2v/devslice; on disk, no
network), then exactly what the final analysis runs: e5_analyze analyze() + criteria() + analyze_v2()
(frozen v2, writes e5_test.json) and v3_analyze.run_test (writes e5_v3.json). Three runs:
  n2  real n = 2 (24 frames)
  n1  OpenCOOD train_params.max_cav = 1 (only the receiver; 24 frames)
  n5  replicated features: the dataset's base data gets 3 extra copies of sender 1 (same pose and scan, new
      ids), so every frame has n = 5 and senders 2-4 send features identical to sender 1 (exercises the
      16-subset decode, R1/B-NORM with several senders, PGD and timing at n = 5; 6 frames)
DEVELOPMENT smoke test; numbers are not results (1 scenario).

  python runners/v3_dryrun.py --out runs/20261024-E5/dryrun_v3 [--n_boot 200]
"""
import argparse
import copy
import json
import os
import sys
import time
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e5_analyze as X  # noqa: E402
import v3_analyze as Y  # noqa: E402
import v3_stream as S3  # noqa: E402
from stage1_reproduce import CKPT  # noqa: E402

import torch  # noqa: E402

SCEN = "2021_08_22_13_37_16"
DEV_ROOT = os.path.join(ROOT, "data/opv2v/devslice/validate")


def replicate_hook(copies=3):
    def hook(ds):
        orig = ds.retrieve_base_data

        def wrapped(idx, *args, **kw):
            base = orig(idx, *args, **kw)
            ids = list(base.keys())
            assert base[ids[0]]["ego"] and len(ids) >= 2
            src = ids[1]
            out = OrderedDict(base)
            for k in range(1, copies + 1):
                out[str(int(src) + 100000 * k)] = copy.deepcopy(base[src])
            return out
        ds.retrieve_base_data = wrapped
    return hook


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/20261024-E5/dryrun_v3")
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", nargs="*", default=None)
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
    pr = json.load(open(os.path.join(ROOT, S3.PREREG)))
    bad = S3.verify_frozen(pr)
    conds = ("clean",) + X.ORIG + ("spoof_blind",)
    summary = {"label": "DRY RUN (development, block-T dev slice, no network); not results", "scenario": SCEN,
               "preregistration": S3.PREREG, "frozen_check_before_run": bad or "OK", "n_boot": a.n_boot, "runs": {}}
    runs = (("n2", None, None, None), ("n1", 1, None, None), ("n5", None, replicate_hook(3), 6))
    for tag, max_cav, hook, nf in runs:
        if a.only and tag not in a.only:
            continue
        h = copy.deepcopy(hyp)
        if max_cav is not None:
            h.setdefault("train_params", {})["max_cav"] = max_cav
        rd = os.path.join(ROOT, a.out, tag)
        for sub in ("cache", "v3extra"):
            os.makedirs(os.path.join(rd, sub), exist_ok=True)
        p, px = os.path.join(rd, "cache", f"{SCEN}.pkl.gz"), os.path.join(rd, "v3extra", f"{SCEN}.pkl.gz")
        t0 = time.time()
        res, extras = S3.run_scenario(SCEN, DEV_ROOT, model, h, p, px, pr, reps=a.reps, max_frames=nf, block="DRYRUN",
                                      ds_hook=hook)
        t_stream = time.time() - t0
        nag = sorted({f["n_agents"] for f in res["frames"]})
        t1 = time.time()
        out = X.analyze([p], conds, False, a.n_boot)                       # frozen v2 analysis
        out["criteria"] = X.analyze_v2([p], conds, out, a.n_boot)
        json.dump(out, open(os.path.join(rd, "e5_test.json"), "w"), indent=1, default=str)
        v3 = Y.run_test(os.path.relpath(rd, ROOT), S3.PREREG, a.n_boot, dry=True)
        pgd_conds = sorted({c for e in extras for c in e["pgd"]})
        summary["runs"][tag] = {
            "frames": len(res["frames"]), "n_agents": nag, "stream_s": round(t_stream),
            "v3_extra_s_per_frame": round(sum(e["v3_s"] for e in extras) / len(extras), 2),
            "analysis_s": round(time.time() - t1),
            "compose_all_identical": all(c["same_candidates"] and c["same_final"] for c in res["compose_checks"]),
            "timing_frames": len(res["timing"]), "pgd_conditions": pgd_conds,
            "pgd_frames": sum(bool(e["pgd"]) for e in extras),
            "subsets_decoded_per_condition": sorted({len(f["conditions"]["clean"]["cands"]) for f in res["frames"]}),
            "B-NORM_flags": v3["B-NORM_flags"], "criteria_v3_D-64": v3["criteria_v3"]["D-64"],
            "consistency_vs_frozen_v2": v3.get("consistency_vs_frozen_v2"),
            "v2_criteria_success": out["criteria"]["success"]}
        print(tag, json.dumps(summary["runs"][tag], default=str)[:1500], flush=True)
    summary["frozen_check_after_run"] = S3.verify_frozen(pr) or "OK"
    os.makedirs(os.path.join(ROOT, a.out), exist_ok=True)
    json.dump(summary, open(os.path.join(ROOT, a.out, "dryrun_v3.json"), "w"), indent=1, default=str)
    print("dry run done", flush=True)


if __name__ == "__main__":
    main()
