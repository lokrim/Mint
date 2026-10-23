"""Stage-1 V-02/V-05 and Stage-2 ray-geometry checks on OPV2V *validate* scenarios (development).

Per scenario (streamed one at a time, raw deleted afterwards):
  V-02  AP with OpenCOOD proj_first=True vs own-frame encoding + receiver warp (ours)
  V-05  per-sender message size (dense / non-zero) at the three fusion scales
  RAY   receiver (ego) range image from the unorganized cloud: rings, columns, fill by ring
  EFF   per-sender counterfactual effects (ADD/REMOVE/SHIFT) per 6.4 m tile, with receiver ray
        counts (SUP/TRAV/OCC/NR) and development GT labels; GT-box ray counts for genuine objects

  python runners/stage2_validate.py --run_dir runs/<id> --scenarios S1 S2 ...
"""
import argparse
import copy
import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import stage1_spike as S  # noqa: E402  (shims + paths)
from stage1_reproduce import IOUS, CKPT, ap_of, empty_stat, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

import opencood.data_utils.datasets as odd  # noqa: E402
from opencood.data_utils.datasets import build_dataset  # noqa: E402
from opencood.tools import inference_utils, train_utils  # noqa: E402
from opencood.utils import eval_utils  # noqa: E402
import opencood.hypes_yaml.yaml_utils as yaml_utils  # noqa: E402
from tools.ranged_zip import central_directory, stream_extract  # noqa: E402

from mint.model.attfuse_parts import agent_features, decode, fuse_scale  # noqa: E402
from mint.model.warp import message_bytes, warp_to_receiver  # noqa: E402
from mint.geometry.rays import RangeImage, classify_box, classify_points  # noqa: E402
from mint.effects.effects import effects as get_effects, gt_match, tile_of  # noqa: E402

VAL_URL = ("https://ucla.app.box.com/index.php?rm=box_download_shared_file"
           "&vanity_name=UCLA-MobilityLab-OPV2V&file_id=f_1621863671123")
TILE_M = 6.4


def boxes_np(b):
    return np.zeros((0, 8, 3)) if b is None else b.numpy()


def scores_np(s):
    return np.zeros((0,)) if s is None else s.numpy()


def included_transforms(ds, idx):
    """Sender->ego transforms for CAVs included by the dataset (same order and range filter)."""
    base = ds.retrieve_base_data(idx, cur_ego_pose_flag=ds.cur_ego_pose_flag)
    ego = next(v for v in base.values() if v["ego"])
    ep = ego["params"]["lidar_pose"]
    Ts, ego_pts = [], ego["lidar_np"][:, :3]
    for cid, c in base.items():
        p = c["params"]["lidar_pose"]
        if np.hypot(p[0] - ep[0], p[1] - ep[1]) > odd.COM_RANGE:
            continue
        Ts.append(c["params"]["transformation_matrix"])
    return Ts, ego_pts


def counts_rec(ri, pts, box):
    """Point-wise SUP/TRAV/OCC (each return = one ray) + slot-based no-return count."""
    if box is None:
        return None
    c = classify_points(pts, box)
    if not c["self_box"]:
        sl = classify_box(ri, box)
        c["NR_slots"], c["slot_candidates"] = sl["NR"], sl["candidates"]
    c["range_m"] = round(float(np.linalg.norm(box.mean(0)[:2])), 2)
    return c


def run_scenario(scen, data_root, model, hyp_pf, hyp_own, args):
    ds_pf = build_dataset(dict(copy.deepcopy(hyp_pf), validate_dir=data_root), visualize=False, train=False)
    ds_own = build_dataset(dict(copy.deepcopy(hyp_own), validate_dir=data_root), visualize=False, train=False)
    assert ds_pf.proj_first and not ds_own.proj_first
    rng_ = hyp_pf["preprocess"]["cav_lidar_range"]
    stat_pf, stat_own, stat_ours_pf = empty_stat(), empty_stat(), empty_stat()
    msg, ri_stats, eff_recs, gt_recs, agents, t_frame = [], [], [], [], [], []
    for i in range(0, len(ds_pf), args.stride):
        t0 = time.perf_counter()
        seed = frame_seed(scen, i, 0)
        np.random.seed(seed)
        b_pf = ds_pf.collate_batch_test([ds_pf[i]])
        np.random.seed(seed)
        b_own = ds_own.collate_batch_test([ds_own[i]])
        n = int(b_pf["ego"]["record_len"][0])
        agents.append(n)
        with torch.no_grad():
            # V-02 baseline: OpenCOOD's own path
            pb, ps, gb = inference_utils.inference_intermediate_fusion(b_pf, model, ds_pf)
            for k in IOUS:
                eval_utils.caluclate_tp_fp(pb, ps, gb, stat_pf, k)
            # ours, proj_first features (reference for the warp comparison)
            f_pf, rl = agent_features(model, b_pf["ego"])
            fused_all = [fuse_scale(f[:n])[0] for f in f_pf]
            p0, r0 = decode(model, fused_all)
            Bp, Sp, _ = ds_pf.post_process(b_pf, {"ego": {"psm": p0, "rm": r0}})
            for k in IOUS:
                eval_utils.caluclate_tp_fp(Bp, Sp, gb, stat_ours_pf, k)
            # V-02: own-frame encoding + receiver warp
            Ts, ego_pts = included_transforms(ds_own, i)
            f_own, rl2 = agent_features(model, b_own["ego"])
            n2 = int(rl2[0])
            assert n2 == len(Ts), (n2, len(Ts))
            warped = []
            for f in f_own:
                fw = [f[0]] + [warp_to_receiver(f[j], Ts[j], rng_) for j in range(1, n2)]
                warped.append(torch.stack(fw))
            p1, r1 = decode(model, [fuse_scale(w)[0] for w in warped])
            Bo, So, go = ds_own.post_process(b_own, {"ego": {"psm": p1, "rm": r1}})
            for k in IOUS:
                eval_utils.caluclate_tp_fp(Bo, So, go, stat_own, k)
            # V-05 message sizes (own-frame, as transmitted)
            for j in range(1, n2):
                msg.append(message_bytes([f[j] for f in f_own]))
            # RAY: receiver range image
            ri = RangeImage.from_points(ego_pts)
            if i % (args.stride * 10) == 0:
                fill_by_ring = np.isfinite(ri.rng).mean(1)
                ri_stats.append({**ri.stats, "frame": i,
                                 "fill_by_ring": [round(float(v), 3) for v in fill_by_ring],
                                 "ring_elev_deg": [round(float(np.degrees(v)), 3) for v in ri.ring_elev]})
            gtn = boxes_np(gb)
            for g in gtn:
                gt_recs.append({"frame": i, **counts_rec(ri, ego_pts, g)})
            # EFF: per-sender counterfactual effects
            Bpn, Spn = boxes_np(Bp), scores_np(Sp)
            for s_idx in range(1, n):
                inc = []
                for f in f_pf:
                    m = torch.ones((n, f.shape[2], f.shape[3]), dtype=torch.bool)
                    m[s_idx] = False
                    inc.append(m)
                pm, rm = decode(model, [fuse_scale(f[:n], m)[0] for f, m in zip(f_pf, inc)])
                Bm, Sm, _ = ds_pf.post_process(b_pf, {"ego": {"psm": pm, "rm": rm}})
                for e in get_effects(Bpn, Spn, boxes_np(Bm), scores_np(Sm)):
                    rec = {"frame": i, "sender": s_idx, "n_agents": n, "type": e["type"],
                           "tile_plus": None if e["plus"] is None else tile_of(e["plus"], rng_, TILE_M),
                           "tile_minus": None if e["minus"] is None else tile_of(e["minus"], rng_, TILE_M),
                           "gt_iou_plus": round(gt_match(e["plus"], gtn, 0.5), 3),
                           "gt_iou_minus": round(gt_match(e["minus"], gtn, 0.5), 3),
                           "score_plus": e.get("score_plus"), "score_minus": e.get("score_minus"),
                           "rays_plus": counts_rec(ri, ego_pts, e["plus"]), "rays_minus": counts_rec(ri, ego_pts, e["minus"])}
                    eff_recs.append(rec)
        t_frame.append(time.perf_counter() - t0)
    return {"scenario": scen, "frames_used": len(agents), "stride": args.stride,
            "agents": {"min": min(agents), "max": max(agents), "mean": round(float(np.mean(agents)), 2)},
            "ap_opencood_projfirst": ap_of(stat_pf, False), "ap_ours_projfirst": ap_of(stat_ours_pf, False),
            "ap_own_frame_warp": ap_of(stat_own, False), "stats": {"pf": stat_pf, "own": stat_own},
            "message": msg, "range_images": ri_stats, "effects": eff_recs, "gt_rays": gt_recs,
            "frame_s": {"p50": round(float(np.median(t_frame)), 3), "p95": round(float(np.percentile(t_frame, 95)), 3)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", required=True)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--max_compressed_bytes", type=int, default=3_000_000_000)
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    run_dir = os.path.join(ROOT, a.run_dir)
    os.makedirs(os.path.join(run_dir, "scenarios"), exist_ok=True)

    class Opt:
        model_dir = CKPT
    hyp_pf = yaml_utils.load_yaml(None, Opt)
    hyp_own = copy.deepcopy(hyp_pf)
    hyp_own["fusion"]["args"] = {"proj_first": False}
    model = train_utils.create_model(hyp_pf)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    entries, total = central_directory(VAL_URL)
    stream_root = os.path.join(ROOT, "data/opv2v/stream/validate")
    for scen in a.scenarios:
        done = os.path.join(run_dir, "scenarios", f"{scen}.json")
        if os.path.exists(done):
            print(scen, "done, skip", flush=True)
            continue
        need = sum(e["csize"] for e in entries if e["name"].startswith(f"validate/{scen}/"))
        if need == 0 or need > a.max_compressed_bytes:
            print(scen, f"refused: compressed size {need}", flush=True)
            continue
        shutil.rmtree(os.path.dirname(stream_root), ignore_errors=True)
        os.makedirs(stream_root)
        t0 = time.time()
        info = stream_extract(VAL_URL, entries, f"validate/{scen}/", os.path.dirname(stream_root))
        print(scen, f"downloaded {info['bytes_downloaded'] / 1e9:.2f} GB in {time.time() - t0:.0f}s, "
              f"raw {info['bytes_written'] / 1e9:.2f} GB", flush=True)
        t1 = time.time()
        res = run_scenario(scen, stream_root, model, hyp_pf, hyp_own, a)
        res.update({"download": info, "wall_s": round(time.time() - t1, 1)})
        with open(done, "w") as f:
            json.dump(res, f, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
        print(scen, "AP pf/ours/own", res["ap_opencood_projfirst"], res["ap_ours_projfirst"],
              res["ap_own_frame_warp"], "effects", len(res["effects"]), flush=True)
        shutil.rmtree(os.path.dirname(stream_root), ignore_errors=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
