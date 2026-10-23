"""E4: per-frame processing (E0 cache format + spoof_blind) and the block-H held-out stream.

Block H (D-52) = the 4 small remaining OPV2V validate scenarios. Nothing is fitted on them.
Per frame and condition (clean, the 4 E0 families, spoof_blind), exactly the E0 cache record
(runners/e0_stream.py): GT, receiver points, candidates of every excluded-sender subset, per-sender
effects with receiver ray counts, attention shares, attack ledger. Every 10th frame: compose() vs a
real tile-masked pass (must be identical). Then, while the raw scenario is on disk, the D-42 timing
of the frozen method (dense) and of the T(0.05) cost variant on every frame (real n).

Safety (E0 safeguards):
  * allowlist = exactly the 4 block-H scenarios; anything else (incl. any test scenario) is refused;
    only the validate archive URL is used and only members under validate/<allowlisted>/ are read;
  * byte budget 3.2e9 checked for the whole set BEFORE the first byte; new ledger in the run dir;
  * one scenario on disk at a time; raw <= 3e9 bytes; raw deleted after the cache is written and re-read.

  python runners/e4_stream.py --run_dir runs/20261023-E4
"""
import argparse
import gzip
import json
import os
import pickle
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e0_stream as E  # noqa: E402  (shims + paths)
from stage1_reproduce import CKPT, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.attacks.blind import attack_spoof_blind  # noqa: E402
from mint.effects.effects import effects as get_effects, tile_of  # noqa: E402
from mint.fusion.compose import finalize  # noqa: E402
from mint.geometry.ground import ground_mask  # noqa: E402
from mint.geometry.rays import contains_origin  # noqa: E402
from mint.model.attfuse_parts import agent_features, receiver_features  # noqa: E402
from mint.reliability import pipeline as PL  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402

H_SCENARIOS = ("2021_08_22_22_01_17", "2021_08_23_10_51_24", "2021_08_23_13_17_21", "2021_08_23_19_42_07")
FAMILIES = ("clean", "spoof_feat", "remove_feat", "shift_feat", "spoof_pts", "spoof_blind")
BYTE_BUDGET = 3_200_000_000
TRIGGER_F = 0.05


def frame_record(model, ds, batch, scen, i, families=FAMILIES, seed=0, rng_scen=None, compose_check=True,
                 pc_range=None, voxel_size=None):
    """E0-format record of one frame; rng keys = e0_stream.rng_for(family, rng_scen or scen, i, seed)."""
    rk = rng_scen or scen
    n = int(batch["ego"]["record_len"][0])
    cavs = E.cav_contents(ds, i)
    assert len(cavs) == n, (len(cavs), n)
    gt = E.np_boxes(ds.post_processor.generate_gt_bbx(batch))
    ego_pts = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
    gmask, _ = ground_mask(ego_pts)
    rec = {"frame": i, "n_agents": n, "cav_ids": [str(c[0]) for c in cavs], "gt": gt,
           "ego_pts": ego_pts.astype(np.float16), "seed": seed}
    conds, checks = {}, []
    with torch.no_grad():
        feats0, _ = agent_features(model, batch["ego"])
        att_pts = E.projected_points(cavs[1][1], pc_range) if n >= 2 else None
        for fam in families:
            if fam != "clean" and n < 2:
                continue
            rng = E.rng_for(fam, rk, i, seed)
            led = {"family": fam, "applied": fam == "clean"}
            feats = feats0
            if fam in ("spoof_feat", "remove_feat", "shift_feat"):
                feats, led = E.attack_features(fam, feats0, 1, gt, att_pts, rng)
            elif fam == "spoof_blind":
                feats, led = attack_spoof_blind(feats0, 1, gt, att_pts, ego_pts, rng, E.MIN_ATT_PTS, contains_origin)
            elif fam == "spoof_pts":
                f2, led = E.attack_points(model, batch["ego"], gt, att_pts, 1, rng, pc_range, voxel_size)
                if f2 is not None:
                    others = [j for j in range(n) if j != 1]
                    for k in range(3):
                        assert torch.equal(f2[k][others], feats0[k][others])
                    feats = f2
            if fam != "clean" and not led["applied"]:
                conds[fam] = {"ledger": led}
                continue
            cands, attn1 = E.decode_all(model, ds, batch, feats, n)
            yp, sp = finalize(ds.post_processor, cands[frozenset()])
            effs = []
            for s_idx in range(1, n):
                ym, sm = finalize(ds.post_processor, cands[frozenset([s_idx])])
                for e in get_effects(yp, sp, ym, sm):
                    effs.append({"sender": s_idx, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                                 "score_plus": e.get("score_plus"), "score_minus": e.get("score_minus"),
                                 "tile_plus": None if e["plus"] is None else tile_of(e["plus"], pc_range, E.TILE_M),
                                 "tile_minus": None if e["minus"] is None else tile_of(e["minus"], pc_range, E.TILE_M),
                                 "rays_plus": E.ray_rec(ego_pts, gmask, e["plus"]),
                                 "rays_minus": E.ray_rec(ego_pts, gmask, e["minus"])})
            conds[fam] = {"ledger": led, "cands": cands, "effects": effs, "attn_tile": E.tile_attn(attn1, n)}
            if fam == "clean" and compose_check and i % 10 == 0 and n >= 2:
                chk = E.check_compose(model, ds, batch, feats, n, cands, E.rng_for("compose", rk, i))
                chk["frame"] = i
                checks.append(chk)
                if not (chk["same_candidates"] and chk["same_final"]):
                    raise RuntimeError(f"compose mismatch {scen} {i}: {chk}")
    rec["conditions"] = conds
    return rec, checks


# ------------------------------------------------------------------ D-42 timing (cost, D-50)
def _recv_encode(model, b):
    with torch.no_grad():
        t0 = time.perf_counter()
        receiver_features(model, b["ego"])
        return time.perf_counter() - t0


def _plain_only(model, pp, b, feats):
    t0 = time.perf_counter()
    n = feats[0].shape[0]
    PL.OpenCOODPost.finalize(pp, PL._cands(pp, b["ego"], *PL._heads(model, feats, n)))
    return time.perf_counter() - t0


def _mint(model, pp, b, pts, pcr, feats, mode, f=None):
    return PL.mint_frame(model, pp, b, pts, pcr, v0.Params(), feats=feats, rule=r1, cf_mode=mode, trigger_f=f)


TIMING_MODES = (("dense", "sequential", None), (f"trigger_{TRIGGER_F}", "trigger", TRIGGER_F))


def time_frame(model, pp, b, pts, pcr, reps=3, warm=False):
    """E3 step-4 protocol on one real frame (clean): isolated receiver encode (5 reps, median);
    then `reps` interleaved repetitions of baseline-only (receiver encode + plain_only) and, for
    each mode, receiver encode + MINT. Returns per-frame medians over repetitions."""
    with torch.no_grad():
        feats, _ = agent_features(model, b["ego"])
    n = feats[0].shape[0]
    if warm:
        _recv_encode(model, b)
        _plain_only(model, pp, b, feats)
        for _, mode, f in TIMING_MODES:
            _mint(model, pp, b, pts, pcr, feats, mode, f)
    iso = float(np.median([_recv_encode(model, b) for _ in range(5)]))
    reps_ = {m[0]: [] for m in TIMING_MODES}
    for _ in range(reps):
        tr0 = _recv_encode(model, b)
        tp0 = _plain_only(model, pp, b, feats)
        for name, mode, f in TIMING_MODES:
            _recv_encode(model, b)
            o = _mint(model, pp, b, pts, pcr, feats, mode, f)
            t = o["timing_s"]
            ex = t["counterfactual"] + t["evidence"] + t["compose"]
            reps_[name].append({"baseline_s": tr0 + tp0, "encode_baseline_s": tr0, "plain_baseline_s": tp0,
                                "mint_extra_s": ex, "overhead": ex / (tr0 + tp0),
                                "tiles": None if o["trigger"] is None else int(o["trigger"].sum()),
                                "counterfactual_s": t["counterfactual"], "evidence_s": t["evidence"],
                                "compose_s": t["compose"]})
    out = {"n_agents": n, "encode_isolated_s": iso}
    for name, *_ in TIMING_MODES:
        R = reps_[name]
        out[name] = {k: (None if R[0][k] is None else float(np.median([x[k] for x in R]))) for k in R[0]}
    return out


# ------------------------------------------------------------------ block-H stream
def run_scenario(scen, data_root, model, hyp, out_tmp, max_frames=None, reps=3):
    from opencood.data_utils.datasets import build_dataset
    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    assert ds.proj_first
    pcr = hyp["preprocess"]["cav_lidar_range"]
    vs = hyp["preprocess"]["args"]["voxel_size"]
    nf = len(ds) if max_frames is None else min(len(ds), max_frames)
    frames, checks, timing = [], [], []
    t_start = time.time()
    for i in range(nf):
        t0 = time.perf_counter()
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        rec, ch = frame_record(model, ds, batch, scen, i, pc_range=pcr, voxel_size=vs)
        rec["frame_s"] = round(time.perf_counter() - t0, 3)
        frames.append(rec)
        checks += ch
        if i % 20 == 0:
            print(f"  {scen} frame {i}/{nf} n={rec['n_agents']} {rec['frame_s']:.1f}s elapsed {time.time() - t_start:.0f}s",
                  flush=True)
    for i in range(nf):                       # timing pass (separate, after the data pass)
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        pts = np.asarray(E.cav_contents(ds, i)[0][1]["lidar_np"][:, :3], np.float64)
        tf = time_frame(model, ds.post_processor, batch, pts, pcr, reps=reps, warm=(i == 0))
        tf["frame"] = i
        timing.append(tf)
        if i % 20 == 0:
            print(f"  {scen} timing {i}/{nf} n={tf['n_agents']} dense {tf['dense']['overhead']:.3f} "
                  f"trig {tf[f'trigger_{TRIGGER_F}']['overhead']:.3f}", flush=True)
    res = {"scenario": scen, "block": "H", "frames": frames, "compose_checks": checks, "timing": timing,
           "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads()}
    with gzip.open(out_tmp, "wb", compresslevel=3) as f:
        pickle.dump(res, f, protocol=4)
    return res


def check_allowlist(scens):
    bad = [s for s in scens if s not in H_SCENARIOS]
    if bad or len(set(scens)) != len(scens):
        sys.exit(f"refused: not in the block-H allowlist (or duplicated): {bad or scens}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", default=list(H_SCENARIOS))
    ap.add_argument("--byte_budget", type=int, default=BYTE_BUDGET)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    check_allowlist(a.scenarios)
    if a.byte_budget > BYTE_BUDGET:
        sys.exit("refused: budget above the approved 3.2e9 bytes")
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    from tools.ranged_zip import central_directory, stream_extract

    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(1)
    run_dir = os.path.join(ROOT, a.run_dir)
    cache_dir = os.path.join(run_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    ledger_p = os.path.join(run_dir, "download_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else {
        "note": "E4 block-H held-out stream (D-52); allowlist = 4 small validate scenarios", "allowlist": list(H_SCENARIOS),
        "byte_budget": a.byte_budget, "downloads": []}
    url = E.VAL_URL
    assert "f_1621863671123" in url                   # the validate archive (never the test archive)
    entries, _ = central_directory(url)
    names = {e["name"].split("/")[1] for e in entries if e["name"].count("/") >= 2}
    assert all(e["name"].startswith("validate/") for e in entries), "unexpected archive layout"
    assert set(H_SCENARIOS) <= names
    need_all = {s: sum(e["csize"] for e in entries if e["name"].startswith(f"validate/{s}/")) for s in a.scenarios}
    spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    todo = [s for s in a.scenarios if not os.path.exists(os.path.join(cache_dir, f"{s}.pkl.gz"))
            and not os.path.exists(os.path.join(stream_parent, f".complete_{s}"))]
    # local-header overhead: count 1% on top of the member sizes when checking the budget
    projected = spent + int(sum(need_all[s] for s in todo) * 1.01)
    ledger["precheck"] = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "need_csize": need_all, "spent": spent,
                          "projected_with_1pct_headers": projected, "budget": a.byte_budget}
    json.dump(ledger, open(ledger_p, "w"), indent=1)
    print("need", need_all, "spent", spent, "projected", projected, "budget", a.byte_budget, flush=True)
    if projected > a.byte_budget:
        sys.exit(f"refused: stream would exceed the byte budget ({projected} > {a.byte_budget}); 0 bytes downloaded")

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    stream_root = os.path.join(stream_parent, "validate")
    for scen in a.scenarios:
        done = os.path.join(cache_dir, f"{scen}.pkl.gz")
        if os.path.exists(done):
            print(scen, "cached, skip", flush=True)
            continue
        marker = os.path.join(stream_parent, f".complete_{scen}")
        if not os.path.exists(marker):
            need = need_all[scen]
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            if need == 0 or need > E.RAW_CAP or spent + need > a.byte_budget:
                sys.exit(f"refused {scen}: need {need}, already downloaded {spent}, budget {a.byte_budget}")
            shutil.rmtree(stream_parent, ignore_errors=True)        # never two scenarios on disk
            os.makedirs(stream_parent)
            t0 = time.time()
            ledger["downloads"].append({"scenario": scen, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "bytes_downloaded": need, "status": "started (counted at full size)"})
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            info = stream_extract(url, entries, f"validate/{scen}/", stream_parent)
            ledger["downloads"][-1].update(bytes_downloaded=info["bytes_downloaded"], status="complete",
                                           bytes_written=info["bytes_written"], seconds=round(time.time() - t0))
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            raw = E.du(stream_parent)
            print(scen, f"downloaded {info['bytes_downloaded'] / 1e9:.3f} GB (total {spent / 1e9:.3f}), raw {raw / 1e9:.2f} GB",
                  flush=True)
            if raw > E.RAW_CAP or spent > a.byte_budget:
                shutil.rmtree(stream_parent, ignore_errors=True)
                sys.exit(f"raw {raw} or total {spent} over the cap/budget; deleted")
            open(marker, "w").write(json.dumps(info))
        else:
            print(scen, "reusing complete extraction", flush=True)
        got = sorted(os.listdir(stream_root))
        assert got == [scen], f"unexpected content on disk: {got}"
        t1 = time.time()
        tmp = done + ".tmp"
        run_scenario(scen, stream_root, model, hyp, tmp, reps=a.reps)
        with gzip.open(tmp, "rb") as f:                              # re-read before deleting raw
            chk = pickle.load(f)
        assert chk["scenario"] == scen and len(chk["frames"]) > 0 and len(chk["timing"]) == len(chk["frames"])
        os.replace(tmp, done)
        print(scen, f"processed {len(chk['frames'])} frames in {time.time() - t1:.0f}s; "
              f"cache {os.path.getsize(done) / 1e6:.0f} MB", flush=True)
        shutil.rmtree(stream_parent, ignore_errors=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
