"""v3 step 1: re-stream block H (D-52; 4 allowlisted validate scenarios) and cache what PGD needs.

Per frame, exactly e4_stream.frame_record (same seeds; E4 cache format -> runs/<run>/cache/<scen>.pkl.gz) and a
side record (runs/<run>/extra/<scen>.pkl.gz):
  inputs      lossless compact model inputs (voxel points/coords/counts, record_len, transformation matrix);
              rebuilt tensors asserted equal to the batch, and rebuilt features asserted equal to the stream's
  ego_xyz     receiver scan xyz as float32 (= OpenCOOD's lidar_np, exact)
  moments     clean per-agent per-scale [count, sum, sum sq, sum |x|]   (sigma_k for D-65)
  mabs        per condition (clean + applied families): per-agent per-scale mean |feature| (B-NORM, D-66),
              from the attacked features recomputed with the same rng (ledger asserted equal)
  yplus_rays  per condition: receiver ray counts of every final Y+ box from the float64 scan (as the test)
No timing pass (E4 timing exists; cost is not part of v3 development). No PGD here: PGD runs only after the
PGD plan is committed (runners/pgd_h_run.py).

Safety (E0/E4 safeguards): allowlist = the 4 block-H scenarios; validate archive only; byte budget 3.2e9
checked for the whole set BEFORE the first data byte (new ledger in the run dir); one scenario on disk;
raw <= 3e9; raw deleted after both cache files are written and re-read.

  python runners/pgd_h_stream.py --run_dir runs/20261024-PGD
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
import e0_stream as E  # noqa: E402
import e4_stream as E4  # noqa: E402
import v3_common as V  # noqa: E402
from stage1_reproduce import CKPT, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.model.attfuse_parts import agent_features  # noqa: E402


def frame_extra(model, ds, batch, rec, scen, i, pcr, vs, inp):
    pp = ds.post_processor
    rb = V.rebuild_batch(inp, pp.generate_anchor_box())
    assert V.inputs_equal(batch, rb), f"compact inputs do not rebuild the batch ({scen} {i})"
    with torch.no_grad():
        feats0, _ = agent_features(model, batch["ego"])
        f_rb, _ = agent_features(model, rb["ego"])
    assert all(torch.equal(a, b) for a, b in zip(feats0, f_rb)), f"rebuilt features differ ({scen} {i})"
    cavs = E.cav_contents(ds, i)
    xyz = np.asarray(cavs[0][1]["lidar_np"][:, :3])
    ego64 = xyz.astype(np.float64)
    n = rec["n_agents"]
    att_pts = E.projected_points(cavs[1][1], pcr) if n >= 2 else None
    mabs = V.bnorm_extras(model, batch, rec, scen, i, feats0, att_pts, ego64, pcr, vs)
    yr = {c: V.yplus_rays(pp, cond, ego64) for c, cond in rec["conditions"].items() if "cands" in cond}
    return {"frame": i, "inputs": inp, "ego_xyz": xyz.astype(np.float32), "moments": V.feat_moments(feats0),
            "mabs": mabs, "yplus_rays": yr}


def run_scenario(scen, data_root, model, hyp, out_tmp, extra_tmp, max_frames=None):
    from opencood.data_utils.datasets import build_dataset
    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    assert ds.proj_first
    pcr = hyp["preprocess"]["cav_lidar_range"]
    vs = hyp["preprocess"]["args"]["voxel_size"]
    nf = len(ds) if max_frames is None else min(len(ds), max_frames)
    frames, checks, extras = [], [], []
    t_start = time.time()
    for i in range(nf):
        t0 = time.perf_counter()
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        inp = V.compact_inputs(batch)                       # before frame_record (detects any mutation)
        rec, ch = E4.frame_record(model, ds, batch, scen, i, pc_range=pcr, voxel_size=vs)
        rec["frame_s"] = round(time.perf_counter() - t0, 3)
        frames.append(rec)
        checks += ch
        extras.append(frame_extra(model, ds, batch, rec, scen, i, pcr, vs, inp))
        if i % 20 == 0:
            print(f"  {scen} frame {i}/{nf} n={rec['n_agents']} {time.perf_counter() - t0:.1f}s "
                  f"elapsed {time.time() - t_start:.0f}s", flush=True)
    res = {"scenario": scen, "block": "H", "frames": frames, "compose_checks": checks, "timing": [],
           "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads(),
           "note": "v3 re-stream of block H; e4_stream.frame_record unchanged; no timing pass"}
    with gzip.open(out_tmp, "wb", compresslevel=3) as f:
        pickle.dump(res, f, protocol=4)
    with gzip.open(extra_tmp, "wb", compresslevel=3) as f:
        pickle.dump({"scenario": scen, "frames": extras}, f, protocol=4)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", default=list(E4.H_SCENARIOS))
    ap.add_argument("--byte_budget", type=int, default=E4.BYTE_BUDGET)
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    E4.check_allowlist(a.scenarios)
    if a.byte_budget > E4.BYTE_BUDGET:
        sys.exit("refused: budget above the approved 3.2e9 bytes")
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    from tools.ranged_zip import central_directory, stream_extract

    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(1)
    run_dir = os.path.join(ROOT, a.run_dir)
    cache_dir, extra_dir = os.path.join(run_dir, "cache"), os.path.join(run_dir, "extra")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(extra_dir, exist_ok=True)
    ledger_p = os.path.join(run_dir, "download_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else {
        "note": "v3 block-H re-stream (user approval 2026-10-24); allowlist = 4 small validate scenarios",
        "allowlist": list(E4.H_SCENARIOS), "byte_budget": a.byte_budget, "downloads": []}
    url = E.VAL_URL
    assert "f_1621863671123" in url                   # the validate archive (never the test archive)
    entries, _ = central_directory(url)
    names = {e["name"].split("/")[1] for e in entries if e["name"].count("/") >= 2}
    assert all(e["name"].startswith("validate/") for e in entries), "unexpected archive layout"
    assert set(E4.H_SCENARIOS) <= names
    need_all = {s: sum(e["csize"] for e in entries if e["name"].startswith(f"validate/{s}/")) for s in a.scenarios}
    spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    done_p = lambda s: (os.path.join(cache_dir, f"{s}.pkl.gz"), os.path.join(extra_dir, f"{s}.pkl.gz"))
    todo = [s for s in a.scenarios if not all(map(os.path.exists, done_p(s)))
            and not os.path.exists(os.path.join(stream_parent, f".complete_{s}"))]
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
        done, done_x = done_p(scen)
        if os.path.exists(done) and os.path.exists(done_x):
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
        tmp, tmp_x = done + ".tmp", done_x + ".tmp"
        run_scenario(scen, stream_root, model, hyp, tmp, tmp_x)
        with gzip.open(tmp, "rb") as f:                              # re-read before deleting raw
            chk = pickle.load(f)
        with gzip.open(tmp_x, "rb") as f:
            chx = pickle.load(f)
        assert chk["scenario"] == scen and len(chk["frames"]) > 0 and len(chx["frames"]) == len(chk["frames"])
        assert all(c["same_candidates"] and c["same_final"] for c in chk["compose_checks"])
        os.replace(tmp, done)
        os.replace(tmp_x, done_x)
        print(scen, f"processed {len(chk['frames'])} frames in {time.time() - t1:.0f}s; cache {os.path.getsize(done) / 1e6:.0f} MB, "
              f"extra {os.path.getsize(done_x) / 1e6:.0f} MB", flush=True)
        shutil.rmtree(stream_parent, ignore_errors=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
