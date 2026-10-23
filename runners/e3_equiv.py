"""E3 steps 1 (final criterion), 2-3 (equivalence on block T) and the step-4 projection.

Development block T only (D-25); in-sample. Pre-registration: runs/20261023-E3/preregistration.json
(original + correction_2026-10-23 + correction_2_2026-10-23).

  step1    evaluate the final step-1 criterion ((a) + (b), D-48) from the existing step1_revised.json
  stream   approved block-T re-stream (E0 allowlist, new ledger, 4.6e9-byte budget, one scenario on disk,
           raw deleted after the cache is written and re-read). Per frame and condition, with the E0 code
           and seeds: reproduce dense Y+ and check it against the E0 cache (bitwise); store the Y+ tile max
           probability (T(f)); the real trigger-mode decode vs the restriction of the cached dense Y-(i)
           (secondary check); trigger effects Y+ vs Y-(i)_T with receiver rays for boxes new to E3.
  analyze  effect recall by type, NMS / effect / R1 gating differences, AP@0.7 and recovery (step 3)
  project  n = 3, 4, 5 projection from step4_overhead.json and the re-streamed tile fractions (step 4)

  python runners/e3_equiv.py step1|stream|analyze|project
"""
import argparse
import glob
import gzip
import json
import os
import pickle
import shutil
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "runs/20261023-E3")
E0_DIR = os.path.join(ROOT, "runs/20261023-E0")
E0_GLOB = "20*_[0-9][0-9].pkl.gz"
FS = (0.05, 0.10)
N_TILES = 572
TYPES = ("ADD", "REMOVE", "SHIFT")
TILE_M = 6.4


def fkey(f):
    return f"T({f})"


# ----------------------------------------------------------------------------------------- step 1
def part_step1(_args):
    d = json.load(open(os.path.join(OUT, "step1_revised.json")))
    out = {"note": "E3 step 1 under the final criterion (correction_2_2026-10-23, D-48): (a) candidate anchor indices "
                   "identical to dense restricted to T(f) and (b) candidate score diff <= 1e-5 and corner diff <= 1e-4 m, "
                   "on 24/24 frames for T(0.05) and T(0.10). Evaluated from step1_revised.json (not re-run). "
                   "24-frame dev slice, n = 2; development / in-sample",
           "source": "runs/20261023-E3/step1_revised.json", "per_f": {}}
    ok_all = True
    for name in ("T(0.05)", "T(0.1)"):
        rows = [r[name] for r in d["raw"]]
        a = sum(bool(x["a_cand_idx_equal"]) for x in rows)
        b = sum(bool(x["b_ok"]) for x in rows)
        ab = sum(bool(x["a_cand_idx_equal"] and x["b_ok"]) for x in rows)
        ok = ab == 24 and len(rows) == 24
        ok_all &= ok
        out["per_f"][name] = {"a_frames": f"{a}/{len(rows)}", "b_frames": f"{b}/{len(rows)}",
                              "a_and_b_frames": f"{ab}/{len(rows)}",
                              "max_score_diff": max(x["b_score_maxabs"] or 0.0 for x in rows),
                              "max_corner_diff": max(x["b_corner_maxabs"] or 0.0 for x in rows), "pass": ok}
    out["criterion_24of24"] = bool(ok_all)
    json.dump(out, open(os.path.join(OUT, "step1_final.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


# ----------------------------------------------------------------------------------------- stream
def boxkey(b):
    return None if b is None else np.ascontiguousarray(np.asarray(b, np.float32)).tobytes()


def stream_scenario(scen, data_root, model, hyp, e0_frames, out_tmp, max_frames=None):
    import torch
    import e0_stream as E
    from opencood.data_utils.datasets import build_dataset
    from stage1_reproduce import frame_seed
    from mint.fusion.compose import candidates, finalize
    from mint.geometry.ground import ground_mask
    from mint.effects.effects import effects as get_effects, tile_of
    from mint.reliability import pipeline as PL

    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    pc_range = hyp["preprocess"]["cav_lidar_range"]
    voxel_size = hyp["preprocess"]["args"]["voxel_size"]
    pp = ds.post_processor
    n_frames = len(ds) if max_frames is None else min(len(ds), max_frames)
    assert max_frames is not None or len(ds) == len(e0_frames), (len(ds), len(e0_frames))
    frames, t_start = [], time.time()
    for i in range(n_frames):
        t0 = time.perf_counter()
        fr0 = e0_frames[i]
        assert fr0["frame"] == i
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        n = int(batch["ego"]["record_len"][0])
        cavs = E.cav_contents(ds, i)
        assert n == fr0["n_agents"] == len(cavs)
        gt = E.np_boxes(pp.generate_gt_bbx(batch))
        assert np.array_equal(gt, fr0["gt"]), f"GT mismatch {scen} {i}"
        ego_pts = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
        gmask, _ = ground_mask(ego_pts)
        rec = {"frame": i, "n_agents": n, "conditions": {}}
        with torch.no_grad():
            feats0, _ = PL.agent_features(model, batch["ego"])
            att_pts = E.projected_points(cavs[1][1], pc_range) if n >= 2 else None
            for fam in E.FAMILIES:
                if fam != "clean" and n < 2:
                    continue
                c0 = fr0["conditions"][fam]
                rng = E.rng_for(fam, scen, i)
                led = {"family": fam, "applied": fam == "clean"}
                feats = feats0
                if fam in ("spoof_feat", "remove_feat", "shift_feat"):
                    feats, led = E.attack_features(fam, feats0, 1, gt, att_pts, rng)
                elif fam == "spoof_pts":
                    f2, led = E.attack_points(model, batch["ego"], gt, att_pts, 1, rng, pc_range, voxel_size)
                    if f2 is not None:
                        feats = f2
                if led != c0["ledger"]:
                    raise RuntimeError(f"attack ledger mismatch {scen} {i} {fam}: {led} vs {c0['ledger']}")
                if fam != "clean" and not led["applied"]:
                    rec["conditions"][fam] = {"ledger": led}
                    continue
                # (1) reproduce dense Y+ and compare with the E0 cache (bitwise)
                base = PL._heads(model, feats, n)
                yc = candidates(pp, *base, batch["ego"]["anchor_box"], batch["ego"]["transformation_matrix"])
                cc = c0["cands"][frozenset()]
                if not (np.array_equal(yc.idx, cc.idx) and np.array_equal(yc.scores, cc.scores)
                        and np.array_equal(yc.corners, cc.corners)):
                    raise RuntimeError(f"dense Y+ mismatch vs E0 cache {scen} {i} {fam}")
                tmax = PL.tile_max_prob(base[0]).numpy().astype(np.float32)
                yp, sp = finalize(pp, cc)
                # ray records of every box in the cached dense effects (identical box -> identical rays)
                known = {}
                for e in c0["effects"]:
                    for side in ("plus", "minus"):
                        if e[side] is not None:
                            known[boxkey(e[side])] = e[f"rays_{side}"]
                cond = {"ledger": led, "tile_max_prob": tmax, "trig": {}}
                senders = list(range(1, n))
                for f in FS:
                    m = PL.trigger_mask(base[0], f)
                    sel = torch.nonzero(m)
                    # (2) secondary check: real trigger-mode decode vs restriction of cached dense Y-(i)
                    th = PL.trigger_heads(model, feats, n, senders, sel)
                    chk = []
                    effs, n_new_rays = [], 0
                    for s_idx in senders:
                        dense_i = c0["cands"][frozenset([s_idx])]
                        r, k = dense_i.tiles()
                        rc = dense_i.take(m.numpy()[r, k])
                        tc = PL._tile_cands(pp, batch["ego"], th[s_idx], sel, base)
                        same = bool(np.array_equal(tc.idx, rc.idx))
                        chk.append({"sender": s_idx, "idx_equal": same, "n": int(len(rc.idx)),
                                    "score_maxabs": float(np.abs(tc.scores - rc.scores).max()) if same and len(rc.idx) else (0.0 if same else None),
                                    "corner_maxabs": float(np.abs(tc.corners - rc.corners).max()) if same and len(rc.idx) else (0.0 if same else None)})
                        # (3) primary trigger effects: Y+ vs finalize(restricted dense Y-(i))
                        ym, sm = finalize(pp, rc)
                        for e in get_effects(yp, sp, ym, sm):
                            rr = {}
                            for side in ("plus", "minus"):
                                kb = boxkey(e[side])
                                if kb is None:
                                    rr[side] = None
                                elif kb in known:
                                    rr[side] = known[kb]
                                else:
                                    rr[side] = E.ray_rec(ego_pts, gmask, e[side])
                                    known[kb] = rr[side]
                                    n_new_rays += 1
                            effs.append({"sender": s_idx, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                                         "score_plus": e.get("score_plus"), "score_minus": e.get("score_minus"),
                                         "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pc_range, TILE_M),
                                         "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pc_range, TILE_M),
                                         "rays_plus": rr["plus"], "rays_minus": rr["minus"]})
                    cond["trig"][fkey(f)] = {"mask": m.numpy(), "tiles": int(len(sel)), "decode_check": chk,
                                             "effects": effs, "new_ray_boxes": n_new_rays}
                rec["conditions"][fam] = cond
        rec["frame_s"] = round(time.perf_counter() - t0, 3)
        frames.append(rec)
        if i % 20 == 0:
            print(f"  {scen} frame {i}/{n_frames} n={n} {rec['frame_s']:.1f}s elapsed {time.time() - t_start:.0f}s", flush=True)
    with gzip.open(out_tmp, "wb", compresslevel=3) as fh:
        pickle.dump({"scenario": scen, "frames": frames}, fh, protocol=4)


def part_stream(args):
    import torch
    import e0_stream as E
    from stage1_reproduce import CKPT
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    from tools.ranged_zip import central_directory, stream_extract

    scens = list(E.DEV_SCENARIOS)
    bad = [s for s in scens if s not in E.DEV_SCENARIOS]
    if bad:
        sys.exit(f"refused: not in the development allowlist: {bad}")
    torch.set_num_threads(args.threads)
    cache_dir = os.path.join(OUT, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    ledger_p = os.path.join(OUT, "download_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else {
        "note": "E3 approved block-T re-stream (preregistration deviation_approved_before_running)",
        "byte_budget": args.byte_budget, "downloads": []}

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    stream_root = os.path.join(stream_parent, "validate")
    VAL_URL = E.VAL_URL
    entries, _ = central_directory(VAL_URL)
    need_all = {s: sum(e["csize"] for e in entries if e["name"].startswith(f"validate/{s}/")) for s in scens}
    spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
    todo = [s for s in scens if not os.path.exists(os.path.join(cache_dir, f"{s}.pkl.gz"))]
    total = spent + sum(need_all[s] for s in todo if not os.path.exists(os.path.join(stream_parent, f".complete_{s}")))
    print("need", need_all, "spent", spent, "projected total", total, "budget", args.byte_budget, flush=True)
    if total > args.byte_budget:
        sys.exit(f"refused: re-stream would exceed the byte budget ({total} > {args.byte_budget})")
    for scen in scens:
        done = os.path.join(cache_dir, f"{scen}.pkl.gz")
        if os.path.exists(done):
            print(scen, "cached, skip", flush=True)
            continue
        marker = os.path.join(stream_parent, f".complete_{scen}")
        if not os.path.exists(marker):
            need = need_all[scen]
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            if need == 0 or need > E.RAW_CAP or spent + need > args.byte_budget:
                sys.exit(f"refused {scen}: need {need}, already downloaded {spent}, budget {args.byte_budget}")
            shutil.rmtree(stream_parent, ignore_errors=True)
            os.makedirs(stream_parent)
            t0 = time.time()
            ledger["downloads"].append({"scenario": scen, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "bytes_downloaded": need, "status": "started (counted at full size)"})
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            info = stream_extract(VAL_URL, entries, f"validate/{scen}/", stream_parent)
            ledger["downloads"][-1].update(bytes_downloaded=info["bytes_downloaded"], status="complete",
                                           bytes_written=info["bytes_written"], seconds=round(time.time() - t0))
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            raw = E.du(stream_parent)
            print(scen, f"downloaded {info['bytes_downloaded'] / 1e9:.2f} GB, raw {raw / 1e9:.2f} GB", flush=True)
            if raw > E.RAW_CAP:
                shutil.rmtree(stream_parent, ignore_errors=True)
                sys.exit(f"raw {raw} exceeds cap; deleted")
            open(marker, "w").write(json.dumps(info))
        else:
            print(scen, "reusing complete extraction", flush=True)
        e0 = pickle.load(gzip.open(os.path.join(E0_DIR, "cache", f"{scen}.pkl.gz")))
        t1 = time.time()
        tmp = done + ".tmp"
        stream_scenario(scen, stream_root, model, hyp, e0["frames"], tmp)
        with gzip.open(tmp, "rb") as fh:
            chk = pickle.load(fh)
        assert chk["scenario"] == scen and len(chk["frames"]) == len(e0["frames"])
        os.replace(tmp, done)
        print(scen, f"processed {len(chk['frames'])} frames in {time.time() - t1:.0f}s; "
              f"cache {os.path.getsize(done) / 1e6:.0f} MB", flush=True)
        shutil.rmtree(stream_parent, ignore_errors=True)
    print("all done", flush=True)


# ----------------------------------------------------------------------------------------- analyze
def same_box(a, b):
    if a is None or b is None:
        return a is None and b is None
    return np.array_equal(np.asarray(a), np.asarray(b))


def match_effects(dense, trig):
    """(reproduced flags for dense effects, spurious flags for trigger effects): same sender, type,
    bitwise-identical plus and minus boxes."""
    used = [False] * len(trig)
    rep = []
    for e in dense:
        hit = False
        for j, t in enumerate(trig):
            if not used[j] and t["sender"] == e["sender"] and t["type"] == e["type"] \
                    and same_box(t["plus"], e["plus"]) and same_box(t["minus"], e["minus"]):
                used[j] = hit = True
                break
        rep.append(hit)
    return rep, [not u for u in used]


def restrict(c, mask):
    r, k = c.tiles()
    return c.take(mask[r, k])


def boxes_equal(a, b):
    return a[0].shape == b[0].shape and np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def in_mask(boxes, mask, pc_range):
    from mint.effects.effects import tile_of
    out = []
    for b in boxes:
        r, c = tile_of(b, pc_range, TILE_M)
        out.append(0 <= r < mask.shape[0] and 0 <= c < mask.shape[1] and bool(mask[r, c]))
    return np.asarray(out, bool)


def part_analyze(args):
    import e0_analyze as A
    from mint.fusion.compose import compose, finalize
    from mint.reliability import r1, v0

    pp = A.post_processor()
    import opencood.hypes_yaml.yaml_utils as yaml_utils

    class Opt:
        model_dir = A.CKPT
    pc_range = yaml_utils.load_yaml(None, Opt)["preprocess"]["cav_lidar_range"]
    conds = ("clean",) + A.FAMILIES
    pols = ("undefended", "R1_dense") + tuple(f"R1_{fkey(f)}" for f in FS)
    stats = {}
    rec = {f: {"recall": {c: {t: [0, 0] for t in TYPES} for c in conds},
               "spurious": {c: {t: 0 for t in TYPES} for c in conds},
               "evals": 0, "evals_with_senders": 0, "effect_sets_differ": 0,
               "nms_sender_outputs": 0, "nms_differ_in_T": 0, "nms_differ_any": 0, "dense_boxes_outside_T": 0,
               "gating_choice_equal": 0, "units_gated_both": 0, "units_gated_dense_only": 0,
               "units_gated_trigger_only": 0, "gated_tiles_outside_T": 0, "final_output_differs": 0,
               "remove_misses": [], "other_misses": [], "spurious_examples": [], "gating_diffs": [],
               "decode_check": {"sender_evals": 0, "idx_differs": 0, "max_score_diff": 0.0, "max_corner_diff": 0.0},
               "tile_frac": {}} for f in FS}
    e0_files = sorted(glob.glob(os.path.join(E0_DIR, "cache", E0_GLOB)))
    assert len(e0_files) == 3, e0_files
    for fpath in e0_files:
        R = pickle.load(gzip.open(fpath))
        scen = R["scenario"]
        T3 = pickle.load(gzip.open(os.path.join(OUT, "cache", f"{scen}.pkl.gz")))
        assert T3["scenario"] == scen and len(T3["frames"]) == len(R["frames"])
        for fr, tr in zip(R["frames"], T3["frames"]):
            assert fr["frame"] == tr["frame"]
            n = fr["n_agents"]
            for cond in conds:
                use = cond if n >= 2 else "clean"
                c, applied = A.cond_of(fr, use)
                tc = tr["conditions"][use if applied else "clean"]
                cands = c["cands"]
                yp, sp = finalize(pp, cands[frozenset()])
                stats.setdefault((cond, "undefended"), []).append(A.frame_stat(yp, sp, fr["gt"]))
                rel_d = r1.assess(c["effects"], v0.Params())
                ch_d = v0.gating_choice(rel_d)
                out_d = finalize(pp, compose(cands, ch_d)) if ch_d else (yp, sp)
                stats.setdefault((cond, "R1_dense"), []).append(A.frame_stat(*out_d, fr["gt"]))
                for f in FS:
                    S = rec[f]
                    S["evals"] += 1
                    if n < 2:
                        stats.setdefault((cond, f"R1_{fkey(f)}"), []).append(A.frame_stat(yp, sp, fr["gt"]))
                        continue
                    S["evals_with_senders"] += 1
                    t = tc["trig"][fkey(f)]
                    mask = t["mask"]
                    S["tile_frac"].setdefault(f"{cond}|n={n}", []).append(t["tiles"] / N_TILES)
                    for d in t["decode_check"]:
                        S["decode_check"]["sender_evals"] += 1
                        if not d["idx_equal"]:
                            S["decode_check"]["idx_differs"] += 1
                        else:
                            S["decode_check"]["max_score_diff"] = max(S["decode_check"]["max_score_diff"], d["score_maxabs"])
                            S["decode_check"]["max_corner_diff"] = max(S["decode_check"]["max_corner_diff"], d["corner_maxabs"])
                    teff = t["effects"]
                    rep, spur = match_effects(c["effects"], teff)
                    if not (all(rep) and not any(spur)):
                        S["effect_sets_differ"] += 1
                    for e, ok in zip(c["effects"], rep):
                        S["recall"][cond][e["type"]][1] += 1
                        S["recall"][cond][e["type"]][0] += int(ok)
                        if not ok:
                            box = e["minus"] if e["type"] == "REMOVE" else e["plus"]
                            tl = tuple(e["tile_minus"] if e["type"] == "REMOVE" else e["tile_plus"])
                            inb = 0 <= tl[0] < mask.shape[0] and 0 <= tl[1] < mask.shape[1]
                            ex = {"scen": scen, "frame": fr["frame"], "cond": cond, "sender": e["sender"],
                                  "type": e["type"], "tile": list(tl), "tile_in_T": bool(inb and mask[tl]),
                                  "yplus_tile_max_prob": float(tc["tile_max_prob"][tl]) if inb else None,
                                  "score_minus": e.get("score_minus"), "score_plus": e.get("score_plus"),
                                  "centre_xy": [round(float(v), 2) for v in np.asarray(box).mean(0)[:2]]}
                            (S["remove_misses"] if e["type"] == "REMOVE" else S["other_misses"]).append(ex)
                    for e, sp_ in zip(teff, spur):
                        if sp_:
                            S["spurious"][cond][e["type"]] += 1
                            if len(S["spurious_examples"]) < 20:
                                S["spurious_examples"].append({"scen": scen, "frame": fr["frame"], "cond": cond,
                                                               "sender": e["sender"], "type": e["type"],
                                                               "tile_plus": e["tile_plus"], "tile_minus": e["tile_minus"]})
                    # NMS outputs per sender: finalize(Y-(i)_T) vs finalize(dense Y-(i))
                    ctr = {frozenset(): cands[frozenset()]}
                    for s_idx in range(1, n):
                        dense_i = cands[frozenset([s_idx])]
                        rc = restrict(dense_i, mask)
                        ctr[frozenset([s_idx])] = rc
                        a, b = finalize(pp, dense_i), finalize(pp, rc)
                        S["nms_sender_outputs"] += 1
                        S["nms_differ_any"] += int(not boxes_equal(a, b))
                        ia, ib = in_mask(a[0], mask, pc_range), in_mask(b[0], mask, pc_range)
                        S["dense_boxes_outside_T"] += int((~ia).sum())
                        S["nms_differ_in_T"] += int(not boxes_equal((a[0][ia], a[1][ia]), (b[0][ib], b[1][ib])))
                    for s, cs in cands.items():
                        if len(s) >= 2:
                            ctr[s] = cs
                    rel_t = r1.assess(teff, v0.Params())
                    ch_t = v0.gating_choice(rel_t)
                    gd = {k for k, r in rel_d.items() if r.gate}
                    gt_ = {k for k, r in rel_t.items() if r.gate}
                    S["units_gated_both"] += len(gd & gt_)
                    S["units_gated_dense_only"] += len(gd - gt_)
                    S["units_gated_trigger_only"] += len(gt_ - gd)
                    if ch_t == ch_d:
                        S["gating_choice_equal"] += 1
                    elif len(S["gating_diffs"]) < 20:
                        S["gating_diffs"].append({"scen": scen, "frame": fr["frame"], "cond": cond,
                                                  "dense": {str(k): sorted(v) for k, v in ch_d.items()},
                                                  "trigger": {str(k): sorted(v) for k, v in ch_t.items()}})
                    for tl in ch_t:
                        inb = 0 <= tl[0] < mask.shape[0] and 0 <= tl[1] < mask.shape[1]
                        S["gated_tiles_outside_T"] += int(not (inb and mask[tl]))
                    out_t = finalize(pp, compose(ctr, ch_t)) if ch_t else (yp, sp)
                    S["final_output_differs"] += int(not boxes_equal(out_d, out_t))
                    stats.setdefault((cond, f"R1_{fkey(f)}"), []).append(A.frame_stat(*out_t, fr["gt"]))
        print("done", scen, flush=True)

    ap = {k: A.ap(A.merge(v)) for k, v in stats.items()}
    clean_u = ap[("clean", "undefended")][0.7]
    tab = {}
    for cond in conds:
        row = {}
        for pol in pols:
            v = ap[(cond, pol)][0.7]
            row[pol] = {"AP@0.7": round(v, 4), "AP@0.5": round(ap[(cond, pol)][0.5], 4)}
            if cond == "clean" and pol != "undefended":
                row[pol]["rel_loss_AP@0.7"] = round(1 - v / clean_u, 4)
            if cond != "clean" and pol != "undefended":
                und = ap[(cond, "undefended")][0.7]
                loss = clean_u - und
                row[pol]["recovery_AP@0.7"] = None if loss < 0.005 else round((v - und) / loss, 4)
                row[pol]["recovery_AP@0.7_unrounded"] = None if loss < 0.005 else (v - und) / loss
        tab[cond] = row
    # reproduction of E1 R1 numbers by the dense reference
    e1 = json.load(open(os.path.join(ROOT, "runs/20261023-E1/rules_and_blind.json")))["AP"]
    repro = {}
    for cond in conds:
        r = {"E1_R1_AP@0.7": e1[cond]["R1"]["AP@0.7"], "E3_R1_dense_AP@0.7": tab[cond]["R1_dense"]["AP@0.7"],
             "E1_undef_AP@0.7": e1[cond]["undefended"]["AP@0.7"], "E3_undef_AP@0.7": tab[cond]["undefended"]["AP@0.7"]}
        if cond != "clean":
            r["E1_recovery"] = e1[cond]["R1"]["recovery_AP@0.7"]
            r["E3_dense_recovery"] = None if tab[cond]["R1_dense"]["recovery_AP@0.7"] is None else round(tab[cond]["R1_dense"]["recovery_AP@0.7"], 3)
        r["match"] = all(r[a] == r[b] for a, b in (("E1_R1_AP@0.7", "E3_R1_dense_AP@0.7"), ("E1_undef_AP@0.7", "E3_undef_AP@0.7"))) and \
            (cond == "clean" or r["E1_recovery"] == r["E3_dense_recovery"])
        repro[cond] = r
    out = {"note": "E3 steps 2-3, development block T (3 scenarios, 404 frames), all conditions, R1 frozen (v0.Params()); "
                   "Y-(i)_T = cached dense Y-(i) candidates restricted to T(f) (pre-registered primary); trigger effects "
                   "computed during the re-stream; in-sample",
           "dense_reproduces_E1": {"all": all(r["match"] for r in repro.values()), "per_condition": repro},
           "AP": tab, "per_f": {}}
    for f in FS:
        S = rec[f]
        pooled = {t: [sum(S["recall"][c][t][0] for c in conds), sum(S["recall"][c][t][1] for c in conds)] for t in TYPES}
        rec_t = {t: None if pooled[t][1] == 0 else pooled[t][0] / pooled[t][1] for t in TYPES}
        dif = {fam: abs(tab[fam][f"R1_{fkey(f)}"]["recovery_AP@0.7_unrounded"] - tab[fam]["R1_dense"]["recovery_AP@0.7_unrounded"])
               for fam in A.FAMILIES}
        tf_all = [x for k, v in S["tile_frac"].items() for x in v]
        tfr = {}
        for k, v in sorted(S["tile_frac"].items()):
            tfr[k] = {"n": len(v), "mean": round(float(np.mean(v)), 4), "p50": round(float(np.percentile(v, 50)), 4),
                      "p95": round(float(np.percentile(v, 95)), 4)}
        out["per_f"][fkey(f)] = {
            "effect_recall_pooled": {t: {"reproduced": pooled[t][0], "dense": pooled[t][1],
                                         "recall": None if rec_t[t] is None else round(rec_t[t], 5)} for t in TYPES},
            "effect_recall_by_condition": {c: {t: {"reproduced": S["recall"][c][t][0], "dense": S["recall"][c][t][1],
                                                   "recall": None if not S["recall"][c][t][1] else round(S["recall"][c][t][0] / S["recall"][c][t][1], 4)}
                                               for t in TYPES} for c in conds},
            "spurious_by_condition": S["spurious"],
            "recall_criterion_ge_0.98_every_type": all(rec_t[t] is not None and rec_t[t] >= 0.98 for t in TYPES),
            "recovery_abs_diff_vs_dense": {k: round(v, 4) for k, v in dif.items()},
            "ap_criterion_within_0.02_every_family": all(v <= 0.02 for v in dif.values()),
            "counts": {k: S[k] for k in ("evals", "evals_with_senders", "effect_sets_differ", "nms_sender_outputs",
                                         "nms_differ_in_T", "nms_differ_any", "dense_boxes_outside_T",
                                         "gating_choice_equal", "units_gated_both", "units_gated_dense_only",
                                         "units_gated_trigger_only", "gated_tiles_outside_T", "final_output_differs")},
            "decode_check_secondary": S["decode_check"],
            "remove_misses": S["remove_misses"], "other_misses": S["other_misses"][:50],
            "n_other_misses": len(S["other_misses"]), "spurious_examples": S["spurious_examples"],
            "gating_diff_examples": S["gating_diffs"],
            "tile_fraction_all_evals": {"n": len(tf_all), "mean": round(float(np.mean(tf_all)), 4)},
            "tile_fraction_by_condition_and_n": tfr}
        out["per_f"][fkey(f)]["recall_and_ap_pass"] = bool(out["per_f"][fkey(f)]["recall_criterion_ge_0.98_every_type"]
                                                          and out["per_f"][fkey(f)]["ap_criterion_within_0.02_every_family"])
    json.dump(out, open(os.path.join(OUT, "step3_equivalence.json"), "w"), indent=1, default=str)
    show = {k: v for k, v in out.items() if k != "per_f"}
    show["per_f"] = {k: {kk: vv for kk, vv in v.items() if kk not in ("remove_misses", "other_misses", "spurious_examples",
                                                                     "gating_diff_examples", "tile_fraction_by_condition_and_n",
                                                                     "effect_recall_by_condition", "spurious_by_condition")}
                     for k, v in out["per_f"].items()}
    print(json.dumps(show, indent=1, default=str))


# ----------------------------------------------------------------------------------------- project
def part_project(_args):
    ov = json.load(open(os.path.join(OUT, "step4_overhead.json")))
    base_n = ov["baseline_only_replicated_s"]
    base_n["2"] = ov["baseline_only_n2_s"]
    tf = {}
    for fpath in sorted(glob.glob(os.path.join(OUT, "cache", E0_GLOB))):
        T3 = pickle.load(gzip.open(fpath))
        for fr in T3["frames"]:
            n = fr["n_agents"]
            if n < 2:
                continue
            for f in FS:
                tf.setdefault((f, n), []).append(fr["conditions"]["clean"]["trig"][fkey(f)]["tiles"])
    out = {"note": "E3 step 4 projection (not a measurement): projected extra = (n - 1) * (|T(f)| * c_tile + c_sender) + "
                   "c_fixed, per real block-T frame (clean), divided by the baseline-only p50 at n agents measured on the "
                   "slice with n - 1 replicated sender features (timing only). Costs measured at n = 2 on the 24-frame "
                   "slice (p50 over frames); evidence and compose held at their n = 2 values. n = 5 has no real block-T "
                   "frames: tile counts of all multi-agent frames (n = 3 and 4) are used, labelled as such. In-sample.",
           "per_f": {}}
    for f in FS:
        raw = ov["raw"][f"trigger_{f}"]                      # unrounded per-frame medians (24 frames)
        c_tile = float(np.median([r["fwd_s"] / r["tiles"] for r in raw if r["tiles"]]))
        c_sender = float(np.median([r["sender_post_s"] for r in raw]))
        c_fixed = float(np.median([r["trigger_s"] + r["evidence"] + r["compose"] for r in raw]))
        d = {"c_tile_s": c_tile, "c_sender_s": c_sender, "c_fixed_s": c_fixed, "n": {}}
        for n in (3, 4, 5):
            tiles = tf.get((f, n)) or (tf.get((f, 3), []) + tf.get((f, 4), []))
            src = f"real block-T frames with n = {n}" if tf.get((f, n)) else "tile counts of all multi-agent (n = 3, 4) block-T frames"
            b = base_n[str(n)]["p50"]
            ex = [(n - 1) * (t * c_tile + c_sender) + c_fixed for t in tiles]
            ovr = [x / b for x in ex]
            d["n"][str(n)] = {"tile_source": src, "frames": len(tiles),
                              "tile_fraction": {"mean": round(float(np.mean(tiles)) / N_TILES, 4),
                                                "p50": round(float(np.percentile(tiles, 50)) / N_TILES, 4),
                                                "p95": round(float(np.percentile(tiles, 95)) / N_TILES, 4)},
                              "baseline_only_p50_s": b,
                              "projected_extra_s": {"p50": float(np.percentile(ex, 50)), "p95": float(np.percentile(ex, 95))},
                              "projected_overhead": {"p50": round(float(np.percentile(ovr, 50)), 4),
                                                     "p95": round(float(np.percentile(ovr, 95)), 4)}}
        tiles2 = tf.get((f, 2), [])
        d["n2_block_T_tile_fraction"] = {"frames": len(tiles2), "mean": round(float(np.mean(tiles2)) / N_TILES, 4)}
        out["per_f"][fkey(f)] = d
    json.dump(out, open(os.path.join(OUT, "step4_projection.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=("step1", "stream", "analyze", "project"))
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--byte_budget", type=int, default=4_600_000_000)
    args = ap.parse_args()
    if args.part == "stream":
        import e0_stream  # noqa: F401  (installs shims and paths first)
    else:
        import e0_analyze  # noqa: F401
    {"step1": part_step1, "stream": part_stream, "analyze": part_analyze, "project": part_project}[args.part](args)


if __name__ == "__main__":
    main()
