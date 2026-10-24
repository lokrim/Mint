"""v3.1 final-test stream: preregistration_v3_1.json = preregistration_v3.json + D-70 (NOT RUN until the user
approves the final test).

D-70 adds the stealth PGD families at r = 1.0 (pgd_untargeted_stealth@r1.0, pgd_remove_stealth@r1.0) as extra
SECONDARY conditions next to the v3 test levels. The frozen v3_stream supports one r per family, so this file:
  * levels_v31(pr): v3 test levels + the D-70 conditions -> {family: [r, ...]},
  * run_scenario: the frozen v3_stream.run_scenario with exactly two changes: the levels come from
    levels_v31(pr), and PGD cost is timed per (family, r) instead of per family (wall clock only; every
    condition is seeded by V3PGD|family|r|scenario|frame, so records do not depend on the loop),
  * install(): points v3_stream.PREREG at preregistration_v3_1.json and v3_stream.run_scenario at the
    function above. Everything else (hash and OpenCOOD checks, allowlist, budget, ledger, interrupted-download
    STOP, one scenario on disk, raw cap, resume, post-run hash check) is the frozen v3_stream.main, unchanged.

  python runners/v3_1_stream.py --run_dir runs/<date>-E5v3 --user_approved     (after approval only)
  python runners/v3_1_stream.py --run_dir runs/<date>-E5v3 --dry_run           (hash + budget check, no network)
"""
import gzip
import os
import pickle
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e0_stream as E  # noqa: E402
import e5_stream as S  # noqa: E402
import v3_common as V  # noqa: E402
import v3_stream as S3  # noqa: E402
from stage1_reproduce import frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.geometry.ground import ground_mask  # noqa: E402
from mint.model.attfuse_parts import agent_features  # noqa: E402

PREREG_V31 = "runs/20261024-E5/preregistration_v3_1.json"


def levels_v31(pr):
    pf = pr["pgd_families"]
    lv = {f: [v["r"]] for f, v in pf["test_levels"].items()}           # v3 (unchanged)
    for c in pf["D-70_strong_level"]["conditions"]:                     # D-70
        assert c["family"] in lv and c["r"] not in lv[c["family"]], c
        lv[c["family"]].append(c["r"])
    names = [V.cond_name(f, r) for f, rs in lv.items() for r in rs]
    assert sorted(names) == sorted(pf["test_conditions"]), (names, pf["test_conditions"])
    return lv


def v3_extra(model, ds, batch, rec, scen, i, pcr, vs, levels, sigma, thr, tau):
    """frozen v3_stream.v3_extra, PGD timed per (family, r)."""
    n = rec["n_agents"]
    cavs = E.cav_contents(ds, i)
    ego = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
    att_pts = E.projected_points(cavs[1][1], pcr) if n >= 2 else None
    with torch.no_grad():
        feats0, _ = agent_features(model, batch["ego"])
    mabs = V.bnorm_extras(model, batch, rec, scen, i, feats0, att_pts, ego, pcr, vs)
    gmask, _ = ground_mask(ego)
    pgd = {}
    for fam, rs in levels.items():
        for r in rs:
            t0 = time.perf_counter()
            got = V.pgd_conditions(model, ds.post_processor, batch, feats0, n, ego, gmask, pcr, scen, i, {fam: [r]},
                                   sigma, thr, tau)
            c = V.cond_name(fam, r)
            if c in got:
                got[c]["attack_s"] = round(time.perf_counter() - t0, 3)
            pgd.update(got)
    for c, r in pgd.items():
        mabs[c] = r["mabs"]
    return {"frame": i, "mabs": mabs, "pgd": pgd}


def run_scenario(scen, data_root, model, hyp, out_tmp, extra_tmp, pr, reps=3, max_frames=None, block="TEST",
                 ds_hook=None):
    """frozen v3_stream.run_scenario; levels from levels_v31(pr)."""
    from opencood.data_utils.datasets import build_dataset
    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    if ds_hook is not None:
        ds_hook(ds)
    assert ds.proj_first
    pcr = hyp["preprocess"]["cav_lidar_range"]
    vs = hyp["preprocess"]["args"]["voxel_size"]
    thr = ds.post_processor.params["target_args"]["score_threshold"]
    levels = levels_v31(pr)
    sigma = pr["pgd_families"]["sigma_k"]
    tau = pr["B-NORM"]["tau_k"]
    nf = len(ds) if max_frames is None else min(len(ds), max_frames)
    frames, checks, timing, extras = [], [], [], []
    t_start = time.time()
    for i in range(nf):
        t0 = time.perf_counter()
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        rec, ch = S.frame_record_e5(model, ds, batch, scen, i, pcr, vs)
        rec["frame_s"] = round(time.perf_counter() - t0, 3)
        frames.append(rec)
        checks += ch
        t1 = time.perf_counter()
        ex = v3_extra(model, ds, batch, rec, scen, i, pcr, vs, levels, sigma, thr, tau)
        ex["v3_s"] = round(time.perf_counter() - t1, 3)
        extras.append(ex)
        if i % 20 == 0:
            print(f"  {scen} frame {i}/{nf} n={rec['n_agents']} {rec['frame_s']:.1f}s + v3 {ex['v3_s']:.1f}s "
                  f"elapsed {time.time() - t_start:.0f}s", flush=True)
    for i in range(nf):                        # frozen timing pass (unchanged)
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        pts = np.asarray(E.cav_contents(ds, i)[0][1]["lidar_np"][:, :3], np.float64)
        tf = S.time_frame_e5(model, ds.post_processor, batch, pts, pcr, reps=reps, warm=(i == 0))
        tf["frame"] = i
        timing.append(tf)
    res = {"scenario": scen, "block": block, "frames": frames, "compose_checks": checks, "timing": timing,
           "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads()}
    with gzip.open(out_tmp, "wb", compresslevel=3) as f:
        pickle.dump(res, f, protocol=4)
    with gzip.open(extra_tmp, "wb", compresslevel=3) as f:
        pickle.dump({"scenario": scen, "preregistration": PREREG_V31, "levels": levels, "sigma": sigma,
                     "frames": extras}, f, protocol=4)
    return res, extras


def install():
    S3.PREREG = PREREG_V31
    S3.run_scenario = run_scenario


def main():
    install()
    S3.main()


if __name__ == "__main__":
    main()
