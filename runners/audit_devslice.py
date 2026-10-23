"""AUDIT X1-X3 on the 24-frame block-T dev slice (data/opv2v/devslice; no network). runs/20261024-AUDIT/plan.json.
DEVELOPMENT smoke tests (1 scenario, n = 2, 24 frames): not estimates.

  python runners/audit_devslice.py --exp X1|X2|X3 [--max_frames N]
"""
import argparse
import copy
import gzip
import json
import os
import pickle
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import audit_common as C  # noqa: E402
import e0_stream as E  # noqa: E402
from stage1_reproduce import CKPT, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.audit.noise import install_loc_noise, set_async  # noqa: E402
from mint.audit.pgd import pgd_attack  # noqa: E402
from mint.audit.raycons import attack_spoof_raycons  # noqa: E402
from mint.geometry.ground import ground_mask  # noqa: E402
from mint.geometry.rays import contains_origin  # noqa: E402
from mint.model.attfuse_parts import agent_features  # noqa: E402

SCEN = "2021_08_22_13_37_16"
DEV_ROOT = os.path.join(ROOT, "data/opv2v/devslice/validate")
OUT = os.path.join(ROOT, "runs/20261024-AUDIT")
X3_CONDS = {"nominal": (0.0, 0.0, 0), "pose": (0.2, 0.2, 0), "pose_large": (0.5, 1.0, 0), "async": (0.0, 0.0, 100),
            "pose_async": (0.2, 0.2, 100)}


def load():
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    return model, hyp


def dataset(hyp):
    from opencood.data_utils.datasets import build_dataset
    ds = build_dataset(dict(copy.deepcopy(hyp), validate_dir=DEV_ROOT), visualize=False, train=False)
    assert ds.proj_first
    return ds


def base(ds, i, model, pcr):
    np.random.seed(frame_seed(SCEN, i, 0))
    batch = ds.collate_batch_test([ds[i]])
    n = int(batch["ego"]["record_len"][0])
    cavs = E.cav_contents(ds, i)
    gt = E.np_boxes(ds.post_processor.generate_gt_bbx(batch))
    ego = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
    gmask, _ = ground_mask(ego)
    with torch.no_grad():
        feats0, _ = agent_features(model, batch["ego"])
    att = E.projected_points(cavs[1][1], pcr) if n >= 2 else None
    fr = {"frame": i, "n_agents": n, "gt": gt, "ego_pts": ego.astype(np.float16), "conditions": {}}
    return batch, n, gt, ego, gmask, feats0, att, fr


def run_attacks(exp, model, hyp, nf):
    ds = dataset(hyp)
    pcr = hyp["preprocess"]["cav_lidar_range"]
    frames, extra = [], []
    nf = min(nf, len(ds))
    for i in range(nf):
        t0 = time.perf_counter()
        batch, n, gt, ego, gmask, feats0, att, fr = base(ds, i, model, pcr)
        fr["conditions"]["clean"] = C.cond_record(model, ds, batch, feats0, n, ego, gmask, pcr, {"applied": True})
        if exp == "X1":
            fams = [(v, e) for v in ("pgd_untargeted", "pgd_remove") for e in (0.1, 0.5)]
            for v, e in fams:
                f2, led = pgd_attack(model, feats0, 1, v, e)
                fr["conditions"][f"{v}_eps{e}"] = C.cond_record(model, ds, batch, f2, n, ego, gmask, pcr, led)
        else:
            rng = E.rng_for("spoof_raycons", SCEN, i, 0)
            f2, led = attack_spoof_raycons(feats0, 1, gt, att, ego, rng, E.MIN_ATT_PTS, contains_origin)
            if led["applied"]:
                c = C.cond_record(model, ds, batch, f2, n, ego, gmask, pcr, led)
                fr["conditions"]["spoof_raycons"] = c
                extra.append({"frame": i, "ledger": led, "boxes_near_dst": C.spoof_box_outcomes(fr, c)})
            else:
                fr["conditions"]["spoof_raycons"] = {"ledger": led}
                extra.append({"frame": i, "ledger": led})
        frames.append((SCEN, fr))
        print(f"{exp} frame {i} n={n} {time.perf_counter() - t0:.1f}s", flush=True)
    return frames, extra


def run_noise(model, hyp, nf):
    pcr = hyp["preprocess"]["cav_lidar_range"]
    out, gt_ref = {}, {}
    for name, (sxyz, syaw, delay) in X3_CONDS.items():
        ds = dataset(hyp)
        if sxyz or syaw:
            install_loc_noise(ds, sxyz, syaw, seed=0, tag=f"X3-{name}")
        set_async(ds, delay)
        frames = []
        for i in range(min(nf, len(ds))):
            batch, n, gt, ego, gmask, feats0, att, fr = base(ds, i, model, pcr)
            if name == "nominal":
                gt_ref[i] = gt
            else:
                assert np.allclose(gt, gt_ref[i], atol=1e-4), "GT must not depend on sender noise"
            fr["conditions"]["clean"] = C.cond_record(model, ds, batch, feats0, n, ego, gmask, pcr, {"applied": True})
            frames.append((SCEN, fr))
        print("X3", name, "done", flush=True)
        out[name] = frames
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True, choices=("X1", "X2", "X3"))
    ap.add_argument("--max_frames", type=int, default=24)
    a = ap.parse_args()
    torch.set_num_threads(8)
    model, hyp = load()
    t0 = time.time()
    res = {"label": "DEVELOPMENT smoke test, block-T dev slice (1 scenario, n = 2), not an estimate",
           "plan": "runs/20261024-AUDIT/plan.json", "experiment": a.exp, "scenario": SCEN}
    if a.exp in ("X1", "X2"):
        frames, extra = run_attacks(a.exp, model, hyp, a.max_frames)
        conds = tuple(frames[0][1]["conditions"].keys())
        realized = None
        if a.exp == "X2":
            realized = {"spoof_raycons": {(SCEN, e["frame"]) for e in extra
                                          if e["ledger"]["applied"] and e.get("boxes_near_dst")}}
        summ, bray, _, _ = C.evaluate(frames, conds, realized)
        res.update(summary=summ, bray_boxes=bray, frames=len(frames))
        if a.exp == "X1":
            res["ledgers"] = [{c: fr["conditions"][c]["ledger"] for c in conds if c != "clean"} for _, fr in frames]
        else:
            res["spoof_records"] = extra
            near = [b for e in extra for b in (e.get("boxes_near_dst") or [])]
            res["spoof_box_verdicts"] = {"applied": sum(e["ledger"]["applied"] for e in extra),
                                         "realized_frames": len(realized["spoof_raycons"]),
                                         "boxes_near_dst": len(near),
                                         "verdicts": {v: sum(b["verdict"] == v for b in near)
                                                      for v in ("drop", "keep", "keep_unknown", "keep_self")}}
        cache = frames
    else:
        allf = run_noise(model, hyp, a.max_frames)
        res["conditions"] = {}
        for name, frames in allf.items():
            summ, bray, _, _ = C.evaluate(frames, ("clean",))
            res["conditions"][name] = {"setting": dict(zip(("xyz_std_m", "yaw_std_deg", "delay_ms"), X3_CONDS[name])),
                                       "AP": summ["all_frames"]["clean"], "bray_boxes": bray["clean"]}
        cache = allf
    res["runtime_s"] = round(time.time() - t0)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"{a.exp}_devslice.json"), "w"), indent=1, default=str)
    with gzip.open(os.path.join(OUT, f"{a.exp}_devslice_cache.pkl.gz"), "wb") as f:
        pickle.dump(cache, f, protocol=4)
    print(json.dumps({k: v for k, v in res.items() if k not in ("ledgers", "spoof_records")}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
