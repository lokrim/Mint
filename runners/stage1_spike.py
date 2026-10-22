"""Stage-1 feasibility spike (OPV2V, released AttFuse PointPillar checkpoint, CPU).

Feasibility evidence only: one test scenario, not an evaluation. Writes an immutable run record:
  runs/<UTC>-S1-spike/{record.json, manifest.json}

Checks:
  K1 voxelizer stand-in == brute-force reference on real frames
  K2 inference runs; per-stage CPU time; peak RSS; AP@0.3/0.5/0.7 (OpenCOOD eval code)
  K3 our maskable fusion == OpenCOOD AttFusion (max abs diff)
  K4 V-03 locality: exclude one sender in one tile -> head outputs outside the tile unchanged;
     plus box-level effect counts inside/outside the tile after NMS
"""
import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "third_party", "OpenCOOD"))

from mint.model import opencood_shims  # noqa: E402

opencood_shims.install()

import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

import opencood.hypes_yaml.yaml_utils as yaml_utils  # noqa: E402
from opencood.data_utils.datasets import build_dataset  # noqa: E402
from opencood.tools import train_utils  # noqa: E402
from opencood.utils import eval_utils  # noqa: E402

from mint.model.attfuse_parts import agent_features, decode, fuse_scale, reference_fused  # noqa: E402


def sha256(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(block), b""):
            h.update(b)
    return h.hexdigest()


def brute_voxelize(pts, vsize, pc_range, max_pts, max_vox):
    vox, order = {}, []
    for p in pts:
        idx = np.floor((p[:3] - pc_range[:3]) / vsize).astype(np.int64)
        grid = np.round((pc_range[3:] - pc_range[:3]) / vsize).astype(np.int64)
        if np.any(idx < 0) or np.any(idx >= grid):
            continue
        k = tuple(idx)
        if k not in vox:
            if len(order) >= max_vox:
                continue
            vox[k] = []
            order.append(k)
        if len(vox[k]) < max_pts:
            vox[k].append(p)
    return order, vox


def check_voxelizer(dataset, sample_points, n_check=20000):
    from mint.model.opencood_shims import VoxelGeneratorV2
    pp = dataset.pre_processor
    vg = pp.voxel_generator
    out = vg.generate(sample_points[:n_check])
    order, vox = brute_voxelize(sample_points[:n_check], vg.voxel_size, vg.pc_range,
                                vg.max_num_points, vg.max_voxels)
    ok = len(order) == out["voxels"].shape[0]
    for i, k in enumerate(order):
        ok &= tuple(out["coordinates"][i][::-1]) == k
        ok &= int(out["num_points_per_voxel"][i]) == len(vox[k])
        ok &= np.array_equal(out["voxels"][i, :len(vox[k])], np.stack(vox[k]))
    return {"points_checked": int(min(n_check, len(sample_points))), "voxels": len(order),
            "equal_to_bruteforce": bool(ok), "is_stand_in": isinstance(vg, VoxelGeneratorV2)}


def locality_test(model, dataset, batch, rng, tile_px_coarse=2):
    ego = batch["ego"]
    feats, rl = agent_features(model, ego)
    n = int(rl[0])
    res = {"n_agents": n}
    if n < 2:
        res["skipped"] = "single agent"
        return res
    ref = reference_fused(model, feats, rl)
    ours = [fuse_scale(f[:n])[0] for f in feats]
    res["fusion_reimpl_max_abs_diff"] = float(max((a - b).abs().max() for a, b in zip(ref, ours)))
    psm0, rm0 = decode(model, ours)
    b0, s0, _ = dataset.post_process(batch, {"ego": {"psm": psm0, "rm": rm0}})
    # tile in coarsest-scale pixels; map to each scale by stride ratio
    hc, wc = feats[-1].shape[2:]
    rng_ = dataset.params["preprocess"]["cav_lidar_range"]
    cell_c = (rng_[3] - rng_[0]) / wc            # metres per coarse pixel
    sender = int(rng.integers(1, n))
    if b0 is not None and b0.shape[0] > 0:
        # choose a tile containing the centre of a predicted box (where effects can occur)
        c = b0[int(rng.integers(0, b0.shape[0]))].mean(0).numpy()
        cx = int((c[0] - rng_[0]) / cell_c)
        cy = int((c[1] - rng_[1]) / cell_c)
        tx = int(np.clip(cx - tile_px_coarse // 2, 0, wc - tile_px_coarse))
        ty = int(np.clip(cy - tile_px_coarse // 2, 0, hc - tile_px_coarse))
        res["tile_choice"] = "contains predicted box centre"
    else:
        ty = int(rng.integers(0, hc - tile_px_coarse))
        tx = int(rng.integers(0, wc - tile_px_coarse))
        res["tile_choice"] = "random (no boxes)"
    fused_m = []
    for f in feats:
        h, w = f.shape[2:]
        s = h // hc
        inc = torch.ones((n, h, w), dtype=torch.bool)
        inc[sender, ty * s:(ty + tile_px_coarse) * s, tx * s:(tx + tile_px_coarse) * s] = False
        fused_m.append(fuse_scale(f[:n], inc)[0])
    psm1, rm1 = decode(model, fused_m)
    ho, wo = psm0.shape[2:]
    so = ho // hc
    inside = torch.zeros((ho, wo), dtype=torch.bool)
    inside[ty * so:(ty + tile_px_coarse) * so, tx * so:(tx + tile_px_coarse) * so] = True
    d_psm = (psm1 - psm0).abs()[0].amax(0)
    d_rm = (rm1 - rm0).abs()[0].amax(0)
    res.update({
        "sender_index": sender, "tile_coarse_yx": [ty, tx], "tile_px_coarse": tile_px_coarse,
        "coarse_grid_hw": [int(hc), int(wc)], "head_grid_hw": [int(ho), int(wo)],
        "max_abs_change_outside_tile_psm": float(d_psm[~inside].max()),
        "max_abs_change_outside_tile_rm": float(d_rm[~inside].max()),
        "bit_identical_outside": bool((d_psm[~inside] == 0).all() and (d_rm[~inside] == 0).all()),
        "max_abs_change_inside_tile_psm": float(d_psm[inside].max()),
        "sender_attention_mass_in_tile": float(
            fuse_scale(feats[0][:n])[1][sender][
                ty * (feats[0].shape[2] // hc):(ty + tile_px_coarse) * (feats[0].shape[2] // hc),
                tx * (feats[0].shape[2] // hc):(tx + tile_px_coarse) * (feats[0].shape[2] // hc)].mean()),
    })
    # box-level effect after NMS: which boxes differ, and are their centres inside the tile?
    b1, s1, _ = dataset.post_process(batch, {"ego": {"psm": psm1, "rm": rm1}})
    x0m, y0m = rng_[0] + tx * cell_c, rng_[1] + ty * cell_c
    x1m, y1m = x0m + tile_px_coarse * cell_c, y0m + tile_px_coarse * cell_c

    def boxes(b):
        return np.zeros((0, 8, 3)) if b is None else b.numpy()

    def unmatched(a, b):
        out = []
        for i in range(a.shape[0]):
            if not any(np.allclose(a[i], b[j], atol=1e-4) for j in range(b.shape[0])):
                out.append(a[i].mean(0))
        return out

    B0, B1 = boxes(b0), boxes(b1)
    changed = unmatched(B0, B1) + unmatched(B1, B0)
    inside_t = [x0m <= c[0] < x1m and y0m <= c[1] < y1m for c in changed]
    res.update({"tile_metres_xy": [round(x0m, 2), round(y0m, 2), round(x1m, 2), round(y1m, 2)],
                "boxes_full": int(B0.shape[0]), "boxes_masked": int(B1.shape[0]),
                "changed_boxes_centre_inside_tile": int(sum(inside_t)),
                "changed_boxes_centre_outside_tile": int(len(inside_t) - sum(inside_t))})
    return res


def ap_summary(result_stat):
    import copy
    out = {}
    for gs in (False, True):
        for iou in (0.3, 0.5, 0.7):
            # calculate_ap mutates the tp/fp lists in place (cumulative sums): copy per call
            ap, _, _ = eval_utils.calculate_ap(copy.deepcopy(result_stat), iou, gs)
            out[f"AP@{iou}{'_globalsort' if gs else ''}"] = round(float(ap), 4)
    for iou in (0.3, 0.5, 0.7):
        out[f"n_gt@{iou}"] = int(result_stat[iou]["gt"])
        out[f"n_pred@{iou}"] = int(len(result_stat[iou]["tp"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt_dir", required=True)
    ap.add_argument("--data_dir", required=True, help="folder containing scenario folders")
    ap.add_argument("--max_frames", type=int, default=10 ** 9)
    ap.add_argument("--locality_frames", type=int, default=8)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261022)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    t_start = time.time()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-S1-spike"
    out_dir = os.path.join(ROOT, "runs", run_id)
    os.makedirs(out_dir)

    class Opt:
        model_dir = a.ckpt_dir
    hypes = yaml_utils.load_yaml(None, Opt)
    hypes["validate_dir"] = a.data_dir
    dataset = build_dataset(hypes, visualize=False, train=False)
    loader = DataLoader(dataset, batch_size=1, num_workers=0, shuffle=False,
                        collate_fn=dataset.collate_batch_test)
    model = train_utils.create_model(hypes)
    _, model = train_utils.load_saved_model(a.ckpt_dir, model)
    model.eval()

    rec = {"run_id": run_id, "kind": "FEASIBILITY_SPIKE (not an evaluation)",
           "n_frames_dataset": len(dataset), "config": {
               "voxel_size": hypes["preprocess"]["args"]["voxel_size"],
               "cav_lidar_range": hypes["preprocess"]["cav_lidar_range"],
               "fusion": hypes["fusion"], "proj_first_effective": bool(dataset.proj_first),
               "score_threshold": hypes["postprocess"]["target_args"]["score_threshold"],
               "nms_thresh": hypes["postprocess"]["nms_thresh"]}}
    rng = np.random.default_rng(a.seed)
    stat = {k: {"tp": [], "fp": [], "gt": 0, "score": []} for k in (0.3, 0.5, 0.7)}
    timings = {"load_voxelize_s": [], "vfe_scatter_s": [], "backbone_fusion_heads_s": [],
               "postprocess_nms_s": [], "eval_s": []}
    agents, locality, vox_check = [], [], None
    t_prev = time.perf_counter()
    for i, batch in enumerate(loader):
        if i >= a.max_frames:
            break
        timings["load_voxelize_s"].append(time.perf_counter() - t_prev)
        ego = batch["ego"]
        agents.append(int(ego["record_len"][0]))
        if vox_check is None:
            import glob
            from opencood.utils.pcd_utils import pcd_to_np
            pcd0 = sorted(glob.glob(os.path.join(a.data_dir, "*", "*", "*.pcd")))[0]
            vox_check = {"pcd": os.path.relpath(pcd0, ROOT),
                         **check_voxelizer(dataset, pcd_to_np(pcd0))}
        with torch.no_grad():
            t0 = time.perf_counter()
            bd = {"voxel_features": ego["processed_lidar"]["voxel_features"],
                  "voxel_coords": ego["processed_lidar"]["voxel_coords"],
                  "voxel_num_points": ego["processed_lidar"]["voxel_num_points"],
                  "record_len": ego["record_len"]}
            bd = model.scatter(model.pillar_vfe(bd))
            t1 = time.perf_counter()
            bd = model.backbone(bd)
            x = bd["spatial_features_2d"]
            out = {"psm": model.cls_head(x), "rm": model.reg_head(x)}
            t2 = time.perf_counter()
            pb, ps, gb = dataset.post_process(batch, {"ego": out})
            t3 = time.perf_counter()
            for iou in (0.3, 0.5, 0.7):
                eval_utils.caluclate_tp_fp(pb, ps, gb, stat, iou)
            t4 = time.perf_counter()
        timings["vfe_scatter_s"].append(t1 - t0)
        timings["backbone_fusion_heads_s"].append(t2 - t1)
        timings["postprocess_nms_s"].append(t3 - t2)
        timings["eval_s"].append(t4 - t3)
        if i % max(1, len(dataset) // a.locality_frames) == 0 and len(locality) < a.locality_frames:
            locality.append({"frame": i, **locality_test(model, dataset, batch, rng)})
        t_prev = time.perf_counter()

    def q(v):
        v = np.asarray(v)
        return {"p50": round(float(np.percentile(v, 50)), 4), "p95": round(float(np.percentile(v, 95)), 4),
                "max": round(float(v.max()), 4), "n": int(v.size)}

    ru_self = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    ru_child = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    rec.update({
        "frames_processed": len(agents),
        "agents_per_frame": {"min": int(min(agents)), "max": int(max(agents)), "mean": round(float(np.mean(agents)), 2)},
        "K1_voxelizer_check": vox_check,
        "K2_ap_one_scenario": ap_summary(stat),
        "K2_timing_cpu": {k: q(v) for k, v in timings.items()},
        "K2_peak_rss_bytes": {"self": int(ru_self), "children": int(ru_child),
                              "note": "macOS ru_maxrss is bytes"},
        "K3_K4_locality": locality,
        "wall_s": round(time.time() - t_start, 1),
    })
    git = lambda d: subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    manifest = {
        "run_id": run_id, "argv": sys.argv, "python": sys.version, "platform": platform.platform(),
        "machine": platform.machine(), "torch": torch.__version__, "numpy": np.__version__,
        "torch_threads": torch.get_num_threads(),
        "opencood_commit": git(os.path.join(ROOT, "third_party", "OpenCOOD")),
        "checkpoint_sha256": sha256(os.path.join(a.ckpt_dir, "latest.pth")),
        "config_sha256": sha256(os.path.join(a.ckpt_dir, "config.yaml")),
        "source_sha256": {p: sha256(os.path.join(ROOT, p)) for p in
                          ["runners/stage1_spike.py", "src/mint/model/opencood_shims.py",
                           "src/mint/model/attfuse_parts.py"]},
        "data_dir": a.data_dir,
    }
    with open(os.path.join(out_dir, "record.json"), "w") as f:
        json.dump(rec, f, indent=1)
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps(rec, indent=1))
    print("RUN", out_dir)


if __name__ == "__main__":
    main()
