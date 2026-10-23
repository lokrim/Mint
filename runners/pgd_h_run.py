"""v3 step 2b: PGD families on block H (development, exposed), from the re-stream caches. No network.

Reads runs/<run>/plan.json (must be committed: sigma_k, levels), rebuilds the exact model inputs of every
frame from runs/<run>/extra, asserts the rebuilt clean candidates equal the cached clean candidates
(all subsets, bitwise), then runs pgd_untargeted and pgd_remove at every r on sender 1 and writes E4-format
condition records (+ yplus_rays, + B-NORM magnitudes 'mabs') to runs/<run>/pgd/<scen>.pkl.gz.

  python runners/pgd_h_run.py --run_dir runs/20261024-PGD
"""
import argparse
import glob
import gzip
import json
import os
import pickle
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e0_analyze as A  # noqa: E402  (shims, post-processor)
import v3_common as V  # noqa: E402
from stage1_reproduce import CKPT  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.geometry.ground import ground_mask  # noqa: E402
from mint.model.attfuse_parts import agent_features  # noqa: E402


def load_model():
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    return model, hyp


def plan_committed(path):
    rel = os.path.relpath(path, ROOT)
    st = subprocess.run(["git", "status", "--porcelain", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    tracked = subprocess.run(["git", "ls-files", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return bool(tracked) and not st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--max_frames", type=int, default=None, help="smoke test only")
    ap.add_argument("--out_sub", default="pgd")
    a = ap.parse_args()
    rd = os.path.join(ROOT, a.run_dir)
    plan_p = os.path.join(rd, "plan.json")
    if a.max_frames is None and not plan_committed(plan_p):
        sys.exit("refused: plan.json must be committed before any PGD run on block H")
    plan = json.load(open(plan_p))
    sigma = plan["feature_scale_clean_H"]["sigma_k"]
    levels = {f: list(plan["threat_model"]["levels_r"]) for f in ("pgd_untargeted", "pgd_remove")}
    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(1)
    model, hyp = load_model()
    pp = A.post_processor()
    thr = pp.params["target_args"]["score_threshold"]
    pcr = hyp["preprocess"]["cav_lidar_range"]
    anchor = pp.generate_anchor_box()
    out_dir = os.path.join(rd, a.out_sub)
    os.makedirs(out_dir, exist_ok=True)
    for p in sorted(glob.glob(os.path.join(rd, "cache", "20*_[0-9][0-9].pkl.gz"))):
        scen = os.path.basename(p)[:-7]
        out_p = os.path.join(out_dir, f"{scen}.pkl.gz")
        if os.path.exists(out_p):
            print(scen, "done, skip", flush=True)
            continue
        R = pickle.load(gzip.open(p))
        X = pickle.load(gzip.open(os.path.join(rd, "extra", f"{scen}.pkl.gz")))
        frames = []
        t_s = time.time()
        for fr, ex in list(zip(R["frames"], X["frames"]))[:a.max_frames]:
            t0 = time.perf_counter()
            i = fr["frame"]
            assert ex["frame"] == i
            n = fr["n_agents"]
            batch = V.rebuild_batch(ex["inputs"], anchor)
            ego = np.asarray(ex["ego_xyz"], np.float64)
            gmask, _ = ground_mask(ego)
            with torch.no_grad():
                feats0, _ = agent_features(model, batch["ego"])
            assert np.allclose(bnorm_mabs(feats0), ex["mabs"]["clean"], rtol=0, atol=0), f"features differ {scen} {i}"
            clean = V.cond_record(model, pp, batch, feats0, n, ego, gmask, pcr, {"applied": True})
            assert V.same(clean["cands"], fr["conditions"]["clean"]["cands"]), f"clean candidates differ {scen} {i}"
            assert V.same(clean["effects"], fr["conditions"]["clean"]["effects"]), f"clean effects differ {scen} {i}"
            conds = V.pgd_conditions(model, pp, batch, feats0, n, ego, gmask, pcr, scen, i, levels, sigma, thr)
            frames.append({"frame": i, "n_agents": n, "conditions": conds, "frame_s": round(time.perf_counter() - t0, 2)})
            if i % 20 == 0:
                print(f"  {scen} frame {i} n={n} {time.perf_counter() - t0:.1f}s elapsed {time.time() - t_s:.0f}s", flush=True)
        with gzip.open(out_p + ".tmp", "wb", compresslevel=3) as f:
            pickle.dump({"scenario": scen, "plan": os.path.relpath(plan_p, ROOT), "levels": levels, "sigma": sigma,
                         "frames": frames}, f, protocol=4)
        os.replace(out_p + ".tmp", out_p)
        print(scen, f"{len(frames)} frames in {time.time() - t_s:.0f}s", flush=True)
    print("all done", flush=True)


def bnorm_mabs(feats):
    from mint.reliability import bnorm
    return bnorm.mean_abs(feats)


if __name__ == "__main__":
    main()
