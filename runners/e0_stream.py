"""E0 data pass on the three development (block T) OPV2V validate scenarios.

Streams ONLY the allowlisted scenarios, one at a time, and caches everything E0 and MINT-v0.0
need so that no scenario has to be downloaded again:
  per frame: GT corners; receiver points (fp16); receiver ground mask stats; GT-box ray counts
  (standard and ground-aware); null (empty synthetic) box ray counts; self-box (D-24) checks;
  per condition (clean + 4 random-placement attacks): pre-NMS candidates of one decode per
  excluded-sender subset (exact tile-wise composition, mint.fusion.compose), per-sender effects
  with receiver ray counts (standard and ground-aware), per-tile attention shares, attack ledger.
Every 10th frame: compose() vs a real tile-masked fusion pass (must be identical).

Safety:
  * scenario allowlist (D-25 block T); anything else is refused;
  * a persistent download ledger with a byte budget (default 4.6e9 for the approved 4.26 GB);
  * raw data <= 3e9 bytes on disk (checked after extraction; one scenario at a time);
  * resumable: finished scenarios are skipped; an extraction is reused only if its marker exists;
  * raw data is deleted only after the cache has been written and re-read.

  python runners/e0_stream.py --run_dir runs/20261023-E0 [--scenarios ...] [--max_frames N]
"""
import argparse
import gzip
import hashlib
import itertools
import json
import os
import pickle
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import stage1_spike as S  # noqa: E402,F401  (shims + paths)
from stage1_reproduce import CKPT, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

import opencood.data_utils.datasets as odd  # noqa: E402
from opencood.data_utils.datasets import build_dataset  # noqa: E402
from opencood.tools import train_utils  # noqa: E402
from opencood.utils import box_utils  # noqa: E402
from opencood.utils.pcd_utils import mask_ego_points, mask_points_by_range  # noqa: E402
import opencood.hypes_yaml.yaml_utils as yaml_utils  # noqa: E402
from tools.ranged_zip import central_directory, stream_extract  # noqa: E402

from mint.model.attfuse_parts import agent_features, decode, fuse_scale  # noqa: E402
from mint.fusion.compose import candidates, compose, finalize, tile_include_masks  # noqa: E402
from mint.geometry.rays import RangeImage, classify_points, contains_origin  # noqa: E402
from mint.geometry.ground import classify_points_ground, ground_at, ground_mask  # noqa: E402
from mint.effects.effects import effects as get_effects, tile_of  # noqa: E402
from mint.attacks import patches as P  # noqa: E402

VAL_URL = ("https://ucla.app.box.com/index.php?rm=box_download_shared_file"
           "&vanity_name=UCLA-MobilityLab-OPV2V&file_id=f_1621863671123")
DEV_SCENARIOS = ("2021_08_22_13_37_16", "2021_08_21_17_30_41", "2021_08_20_21_48_35")   # D-25, block T
FAMILIES = ("clean", "spoof_feat", "remove_feat", "shift_feat", "spoof_pts")
TILE_M = 6.4
RAW_CAP = 3_000_000_000
MIN_ATT_PTS, MIN_ATT_PTS_PTS = 20, 50


def du(path):
    tot = 0
    for r, _, fs in os.walk(path):
        for f in fs:
            tot += os.path.getsize(os.path.join(r, f))
    return tot


def rng_for(family, scen, frame, seed=0):
    h = hashlib.sha256(f"E0|{family}|{scen}|{frame}|{seed}".encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "little"))


def np_boxes(b):
    return np.zeros((0, 8, 3), np.float32) if b is None else b.numpy().astype(np.float32)


def ray_rec(pts, gmask, box):
    if box is None:
        return None
    a = classify_points(pts, box)
    g = classify_points_ground(pts, gmask, box)
    return {"std": {k: a[k] for k in ("SUP", "TRAV", "OCC", "candidates")},
            "gnd": {k: g[k] for k in ("SUP", "TRAV", "OCC", "TRAV_GROUND", "candidates")},
            "self_box": bool(a["self_box"]), "range_m": round(float(np.linalg.norm(np.asarray(box).mean(0)[:2])), 2)}


def cav_contents(ds, idx):
    """Base content of the CAVs included by the dataset, in record order (ego first)."""
    base = ds.retrieve_base_data(idx, cur_ego_pose_flag=ds.cur_ego_pose_flag)
    ego = next(v for v in base.values() if v["ego"])
    ep = ego["params"]["lidar_pose"]
    out = []
    for cid, c in base.items():
        p = c["params"]["lidar_pose"]
        if np.hypot(p[0] - ep[0], p[1] - ep[1]) > odd.COM_RANGE:
            continue
        out.append((cid, c))
    return out


def projected_points(c, pc_range):
    pts = mask_ego_points(np.array(c["lidar_np"], copy=True))
    pts[:, :3] = box_utils.project_points_by_matrix_torch(pts[:, :3], c["params"]["transformation_matrix"])
    return mask_points_by_range(pts, pc_range)


def subsets(n):
    senders = list(range(1, n))
    for k in range(len(senders) + 1):
        for s in itertools.combinations(senders, k):
            yield frozenset(s)


def decode_all(model, ds, batch, feats, n):
    """Candidates for every excluded-sender subset; full post-NMS for {} and singletons."""
    ego = batch["ego"]
    cands, fused0, attn1 = {}, None, None
    for s in subsets(n):
        inc = None
        if s:
            inc = []
            for f in feats:
                m = torch.ones((n, f.shape[2], f.shape[3]), dtype=torch.bool)
                for i in s:
                    m[i] = False
                inc.append(m)
        outs = [fuse_scale(f[:n], None if inc is None else inc[k]) for k, f in enumerate(feats)]
        if not s:
            attn1 = outs[0][1]
        psm, rm = decode(model, [o[0] for o in outs])
        cands[s] = candidates(ds.post_processor, psm, rm, ego["anchor_box"], ego["transformation_matrix"])
    return cands, attn1


def check_compose(model, ds, batch, feats, n, cands, rng):
    """Random tile-wise gating: composed result must equal a real masked pass."""
    hh, ww = cands[frozenset()].hw
    tiles = [(r, c) for r in range((hh + 7) // 8) for c in range(ww // 8)]
    pick = rng.choice(len(tiles), size=min(25, len(tiles)), replace=False)
    choice = {}
    for j in pick:
        s = frozenset(int(x) for x in range(1, n) if rng.random() < 0.6)
        if s:
            choice[tiles[j]] = s
    masks = tile_include_masks(n, [(f.shape[2], f.shape[3]) for f in feats], choice)
    psm, rm = decode(model, [fuse_scale(f[:n], m)[0] for f, m in zip(feats, masks)])
    real = candidates(ds.post_processor, psm, rm, batch["ego"]["anchor_box"], batch["ego"]["transformation_matrix"])
    comp = compose(cands, choice)
    same_idx = np.array_equal(real.idx, comp.idx)
    dmax = float(np.abs(real.corners - comp.corners).max()) if same_idx and len(real.idx) else 0.0
    bf, sf = finalize(ds.post_processor, real)
    cf, scf = finalize(ds.post_processor, comp)
    same_final = bf.shape == cf.shape and (bf.size == 0 or float(np.abs(bf - cf).max()) == 0.0)
    return {"tiles_gated": len(choice), "same_candidates": bool(same_idx), "max_abs_corner_diff": dmax,
            "same_final": bool(same_final)}


def tile_attn(attn1, n):
    """Mean attention share per sender per 6.4 m tile at fusion scale 1 ([n, 13, 44])."""
    a = attn1[:n]
    h, w = a.shape[1], a.shape[2]
    hp = (h + 7) // 8 * 8
    pad = torch.nn.functional.pad(a, (0, 0, 0, hp - h), value=float("nan"))
    t = pad.reshape(n, hp // 8, 8, w // 8, 8)
    return torch.nanmean(torch.nanmean(t, dim=4), dim=2).numpy().astype(np.float16)


def attack_features(family, feats, a, gt, att_pts, rng):
    """Return (new feats, ledger) for a feature-level family; feats untouched if not applicable."""
    gt_xy = gt.mean(1)[:, :2] if len(gt) else np.zeros((0, 2))
    vis = [j for j in range(len(gt)) if P.points_in_box(att_pts, gt[j]).sum() >= MIN_ATT_PTS
           and not contains_origin(gt[j], 0.2)]
    led = {"family": family, "attacker": a, "eligible_targets": len(vis), "applied": False}
    if not vis:
        return feats, led
    j = int(rng.choice(vis))
    cx, cy = gt_xy[j]
    src = P.coarse_patch(cx, cy, P.box_half(gt[j]))
    if not P.in_grid(src, feats):
        return feats, led
    new = [f.clone() for f in feats]
    if family == "spoof_feat":
        dst = P.sample_free_patch(rng, src, feats, gt_xy)
        if dst is None:
            return feats, led
        P.copy_patch(new, a, src, dst)
        led.update(applied=True, source_gt=j, dst_center=[round(v, 2) for v in P.patch_center(dst)])
    elif family == "remove_feat":
        bg = P.sample_free_patch(rng, src, feats, gt_xy)
        if bg is None:
            return feats, led
        P.copy_patch(new, a, bg, src)
        led.update(applied=True, target_gt=j, bg_center=[round(v, 2) for v in P.patch_center(bg)])
    elif family == "shift_feat":
        bg = P.sample_free_patch(rng, src, feats, gt_xy)
        dc, dr = [(1, 0), (-1, 0), (0, 1), (0, -1)][int(rng.integers(4))]
        dst = P.shift_patch(src, dc, dr)
        if bg is None or not P.in_grid(dst, feats):
            return feats, led
        orig = [f.clone() for f in feats]
        P.copy_patch(new, a, bg, src)
        for k, f in enumerate(new):                       # paste original object one cell away
            rs, cs = P._slices(src, k)
            rd, cd = P._slices(dst, k)
            f[a, :, rd, cd] = orig[k][a, :, rs, cs]
        led.update(applied=True, target_gt=j, shift_m=[dc * P.COARSE_M, dr * P.COARSE_M])
    return new, led


def attack_points(model, batch_ego, gt, att_pts, a, rng, pc_range, voxel_size):
    gt_xy = gt.mean(1)[:, :2] if len(gt) else np.zeros((0, 2))
    counts = [int(P.points_in_box(att_pts, g).sum()) if not contains_origin(g, 0.2) else 0 for g in gt]
    vis = [j for j, c in enumerate(counts) if c >= MIN_ATT_PTS_PTS]
    led = {"family": "spoof_pts", "attacker": a, "eligible_targets": len(vis), "applied": False}
    if not vis:
        return None, led
    j = int(rng.choice(vis))
    sel = att_pts[P.points_in_box(att_pts, gt[j])]
    cx, cy = gt_xy[j]
    for _ in range(300):
        x, y = rng.uniform(-60, 60), rng.uniform(-35, 35)
        if np.hypot(x, y) < 6 or (len(gt_xy) and np.min(np.hypot(gt_xy[:, 0] - x, gt_xy[:, 1] - y)) < 6):
            continue
        moved = sel.copy()
        moved[:, 0] += x - cx
        moved[:, 1] += y - cy
        pl = P.append_points_to_voxels(batch_ego["processed_lidar"], a, moved, pc_range, voxel_size)
        b2 = {**batch_ego, "processed_lidar": pl}
        feats, _ = agent_features(model, b2)
        led.update(applied=True, source_gt=j, n_points=int(len(moved)), dst_center=[round(x, 2), round(y, 2)])
        return feats, led
    return None, led


def null_boxes(rng, gt, gmap, k=8):
    """Empty synthetic vehicle boxes in GT-free space; bottom on the receiver ground estimate."""
    out = []
    gt_xy = gt.mean(1)[:, :2] if len(gt) else np.zeros((0, 2))
    gt_bottom = float(np.median(gt[:, :, 2].min(1))) if len(gt) else -1.9
    for _ in range(200):
        if len(out) >= k:
            break
        x, y = rng.uniform(-50, 50), rng.uniform(-35, 35)
        if np.hypot(x, y) < 4 or (len(gt_xy) and np.min(np.hypot(gt_xy[:, 0] - x, gt_xy[:, 1] - y)) < 5):
            continue
        zg = float(ground_at(gmap, np.array([x]), np.array([y]))[0])
        src = "receiver_ground"
        if not np.isfinite(zg):
            zg, src = gt_bottom, "gt_median_bottom"
        yaw = rng.uniform(-np.pi, np.pi)
        box = np.array([[x, y, zg + 0.78, 1.56, 1.6, 3.9, yaw]], np.float32)   # hwl order
        c = box_utils.boxes_to_corners_3d(torch.from_numpy(box), order="hwl").numpy()[0]
        out.append((c, src))
    return out


def run_scenario(scen, data_root, model, hyp, args, out_tmp):
    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    assert ds.proj_first
    pc_range = hyp["preprocess"]["cav_lidar_range"]
    voxel_size = hyp["preprocess"]["args"]["voxel_size"]
    frames, compose_checks = [], []
    n_frames = len(ds) if args.max_frames is None else min(len(ds), args.max_frames)
    t_start = time.time()
    for i in range(n_frames):
        t0 = time.perf_counter()
        seed = frame_seed(scen, i, 0)
        np.random.seed(seed)
        batch = ds.collate_batch_test([ds[i]])
        n = int(batch["ego"]["record_len"][0])
        cavs = cav_contents(ds, i)
        assert len(cavs) == n, (len(cavs), n)
        gt = np_boxes(ds.post_processor.generate_gt_bbx(batch))
        ego_pts = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
        gmask, gmap = ground_mask(ego_pts)
        rec = {"frame": i, "n_agents": n, "cav_ids": [str(c[0]) for c in cavs], "gt": gt,
               "ego_pts": ego_pts.astype(np.float16), "ground_mask": np.packbits(gmask),
               "ground_frac": float(gmask.mean())}
        # D-24 and geometry checks
        selfs = [j for j in range(len(gt)) if contains_origin(gt[j], 0.2)]
        rec["self_gt"] = {"n": len(selfs), "centre_dist": [round(float(np.linalg.norm(gt[j].mean(0)[:2])), 2) for j in selfs],
                          "proxy_n": int(sum(np.linalg.norm(g.mean(0)[:2]) < 1.5 for g in gt))}
        if i % 10 == 0:
            ri = RangeImage.from_points(ego_pts)
            rec["range_image"] = {**ri.stats, "fill_by_ring": np.isfinite(ri.rng).mean(1).round(3).tolist()}
        rec["gt_rays"] = [ray_rec(ego_pts, gmask, g) for g in gt]
        rec["null_rays"] = [{**ray_rec(ego_pts, gmask, c), "z_source": s} for c, s in
                            null_boxes(rng_for("null", scen, i), gt, gmap)]
        with torch.no_grad():
            feats0, _ = agent_features(model, batch["ego"])
            att_pts = projected_points(cavs[1][1], pc_range) if n >= 2 else None
            conds = {}
            for fam in FAMILIES:
                if fam != "clean" and n < 2:
                    continue
                rng = rng_for(fam, scen, i)
                led = {"family": fam, "applied": fam == "clean"}
                feats = feats0
                if fam in ("spoof_feat", "remove_feat", "shift_feat"):
                    feats, led = attack_features(fam, feats0, 1, gt, att_pts, rng)
                elif fam == "spoof_pts":
                    f2, led = attack_points(model, batch["ego"], gt, att_pts, 1, rng, pc_range, voxel_size)
                    if f2 is not None:
                        # untouched agents must be bit-identical after re-encoding
                        for k in range(3):
                            others = [j for j in range(n) if j != 1]
                            assert torch.equal(f2[k][others], feats0[k][others])
                        feats = f2
                if fam != "clean" and not led["applied"]:
                    conds[fam] = {"ledger": led}           # frame unchanged: evaluate as clean
                    continue
                cands, attn1 = decode_all(model, ds, batch, feats, n)
                yp, sp = finalize(ds.post_processor, cands[frozenset()])
                effs = []
                for s_idx in range(1, n):
                    ym, sm = finalize(ds.post_processor, cands[frozenset([s_idx])])
                    for e in get_effects(yp, sp, ym, sm):
                        effs.append({"sender": s_idx, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                                     "score_plus": e.get("score_plus"), "score_minus": e.get("score_minus"),
                                     "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pc_range, TILE_M),
                                     "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pc_range, TILE_M),
                                     "rays_plus": ray_rec(ego_pts, gmask, e["plus"]),
                                     "rays_minus": ray_rec(ego_pts, gmask, e["minus"])})
                conds[fam] = {"ledger": led, "cands": cands, "effects": effs, "attn_tile": tile_attn(attn1, n)}
                if fam == "clean" and i % 10 == 0 and n >= 2:
                    chk = check_compose(model, ds, batch, feats, n, cands, rng_for("compose", scen, i))
                    chk["frame"] = i
                    compose_checks.append(chk)
                    if not (chk["same_candidates"] and chk["same_final"]):
                        raise RuntimeError(f"compose mismatch {scen} {i}: {chk}")
            rec["conditions"] = conds
        rec["frame_s"] = round(time.perf_counter() - t0, 3)
        frames.append(rec)
        if i % 20 == 0:
            print(f"  {scen} frame {i}/{n_frames} n={n} {rec['frame_s']:.1f}s "
                  f"elapsed {time.time() - t_start:.0f}s", flush=True)
    res = {"scenario": scen, "frames": frames, "compose_checks": compose_checks}
    with gzip.open(out_tmp, "wb", compresslevel=3) as f:
        pickle.dump(res, f, protocol=4)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", default=list(DEV_SCENARIOS))
    ap.add_argument("--max_frames", type=int, default=None)
    ap.add_argument("--byte_budget", type=int, default=4_600_000_000)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--keep_raw", action="store_true", help="debug: keep the extraction after processing")
    a = ap.parse_args()
    bad = [s for s in a.scenarios if s not in DEV_SCENARIOS]
    if bad:
        sys.exit(f"refused: not in the development allowlist: {bad}")
    torch.set_num_threads(a.threads)
    run_dir = os.path.join(ROOT, a.run_dir)
    cache_dir = os.path.join(run_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    ledger_p = os.path.join(run_dir, "download_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else {"downloads": []}

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    stream_root = os.path.join(stream_parent, "validate")
    entries = None
    for scen in a.scenarios:
        tag = "" if a.max_frames is None else f".first{a.max_frames}"
        done = os.path.join(cache_dir, f"{scen}{tag}.pkl.gz")
        if os.path.exists(done):
            print(scen, "cached, skip", flush=True)
            continue
        marker = os.path.join(stream_parent, f".complete_{scen}")
        if not os.path.exists(marker):
            if entries is None:
                entries, _ = central_directory(VAL_URL)
            need = sum(e["csize"] for e in entries if e["name"].startswith(f"validate/{scen}/"))
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            if need == 0 or need > RAW_CAP or spent + need > a.byte_budget:
                sys.exit(f"refused {scen}: need {need}, already downloaded {spent}, budget {a.byte_budget}")
            shutil.rmtree(stream_parent, ignore_errors=True)        # never two scenarios on disk
            os.makedirs(stream_parent)
            t0 = time.time()
            ledger["downloads"].append({"scenario": scen, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "bytes_downloaded": need, "status": "started (counted at full size)"})
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            info = stream_extract(VAL_URL, entries, f"validate/{scen}/", stream_parent)
            ledger["downloads"][-1].update(bytes_downloaded=info["bytes_downloaded"], status="complete",
                                           bytes_written=info["bytes_written"], seconds=round(time.time() - t0))
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            raw = du(stream_parent)
            print(scen, f"downloaded {info['bytes_downloaded'] / 1e9:.2f} GB, raw {raw / 1e9:.2f} GB", flush=True)
            if raw > RAW_CAP:
                shutil.rmtree(stream_parent, ignore_errors=True)
                sys.exit(f"raw {raw} exceeds cap; deleted")
            open(marker, "w").write(json.dumps(info))
        else:
            print(scen, "reusing complete extraction", flush=True)
        t1 = time.time()
        tmp = done + ".tmp"
        run_scenario(scen, stream_root, model, hyp, a, tmp)
        with gzip.open(tmp, "rb") as f:                              # re-read before deleting raw
            chk = pickle.load(f)
        assert chk["scenario"] == scen and len(chk["frames"]) > 0
        os.replace(tmp, done)
        print(scen, f"processed {len(chk['frames'])} frames in {time.time() - t1:.0f}s; "
              f"cache {os.path.getsize(done) / 1e6:.0f} MB", flush=True)
        if not a.keep_raw:
            shutil.rmtree(stream_parent, ignore_errors=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
