"""E5 final test: stream the 15 OPV2V test scenarios (D-55) and cache every frame (NOT RUN in E5a).

Requires the user's explicit approval of the ~20.4e9-byte stream; refuses without --user_approved.

Per frame and condition (clean, the 4 original families, spoof_blind): exactly the E4 record
(runners/e4_stream.frame_record: GT, receiver points, candidates of every excluded-sender subset,
per-sender effects with receiver ray counts, attack ledger; compose() check every 10th frame) plus,
for B-RAY (D-56), `yplus_rays`: the receiver's ray counts (R1's standard count, float64 scan) of every
final Y+ box. Then, while the raw scenario is on disk, the D-42 timing of dense R1 and T(0.05)
(e4_stream.time_frame, unchanged) and of B-RAY (same protocol: receiver encode + plain baseline, then
B-RAY on the plain output) on every frame at its real n.

Safety:
  * allowlist = exactly the 15 D-55 scenarios; 2021_08_23_12_58_19 (development) and anything else
    are refused; only the test archive URL is used and only members under test/<allowlisted>/ are read;
  * byte budget 22e9 checked for the whole set BEFORE the first data byte (only the archive's central
    directory is read before the check); counted at full member size; ledger in the run dir;
  * one scenario on disk at a time; raw <= 3e9 bytes; free disk checked; raw deleted after the
    scenario cache is written and re-read.

  python runners/e5_stream.py --run_dir runs/<date>-E5 --user_approved   (after approval only)
  python runners/e5_stream.py --run_dir runs/<date>-E5 --dry_run          (no network)
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
import e4_stream as E4  # noqa: E402
from stage1_reproduce import CKPT, TEST_URL, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.fusion.compose import finalize  # noqa: E402
from mint.reliability import baselines as BL  # noqa: E402
from mint.reliability import pipeline as PL  # noqa: E402

TEST_SCENARIOS = ("2021_08_18_19_48_05", "2021_08_20_21_10_24", "2021_08_21_09_28_12", "2021_08_22_07_52_02",
                  "2021_08_22_09_08_29", "2021_08_22_21_41_24", "2021_08_23_15_19_19", "2021_08_23_16_06_26",
                  "2021_08_23_17_22_47", "2021_08_23_21_07_10", "2021_08_23_21_47_19", "2021_08_24_07_45_41",
                  "2021_08_24_11_37_54", "2021_08_24_20_09_18", "2021_08_24_20_49_54")
EXCLUDED = ("2021_08_23_12_58_19",)          # moved to development (exposure ledger, D-55)
BYTE_BUDGET = 22_000_000_000
RAW_CAP = 3_000_000_000
DISK_MARGIN = 5_000_000_000                  # free space required beyond the raw scenario (caches, temp)
TEST_FILE_ID = "f_1621736219709"
S1_DIR = os.path.join(ROOT, "runs/20261023-S1-reproduce/scenarios")


def check_allowlist(scens):
    bad = [s for s in scens if s not in TEST_SCENARIOS or s in EXCLUDED]
    if bad or len(set(scens)) != len(scens) or not scens:
        sys.exit(f"refused: not in the D-55 test allowlist (or duplicated/empty): {bad or scens}")


def s1_sizes():
    """Bytes downloaded per scenario in the Stage-1 reproduction (planning only; the real check uses the
    archive's central directory)."""
    out = {}
    for s in TEST_SCENARIOS:
        p = os.path.join(S1_DIR, f"{s}.json")
        out[s] = json.load(open(p))["download"]["bytes_downloaded"] if os.path.exists(p) else None
    return out


def budget_ok(spent, need, todo, budget=BYTE_BUDGET):
    """Projected total (already downloaded + 1.01 x member sizes still to fetch) within budget."""
    proj = spent + int(sum(need[s] for s in todo) * 1.01)
    return proj <= budget, proj


def frame_record_e5(model, ds, batch, scen, i, pc_range, voxel_size):
    rec, checks = E4.frame_record(model, ds, batch, scen, i, families=E4.FAMILIES, pc_range=pc_range,
                                  voxel_size=voxel_size)
    pts = np.asarray(E.cav_contents(ds, i)[0][1]["lidar_np"][:, :3], np.float64)
    for c in rec["conditions"].values():
        if "cands" not in c:
            continue
        yp, _ = finalize(ds.post_processor, c["cands"][frozenset()])
        c["yplus_rays"] = [BL.box_rays(pts, b) for b in yp]
    return rec, checks


def time_bray(model, pp, b, pts, reps=3):
    """D-42-style B-RAY timing: per repetition, receiver encode + plain baseline (timed), then B-RAY on
    the plain output; overhead = B-RAY time / baseline of the same repetition; per-frame medians."""
    with torch.no_grad():
        feats, _ = E4.agent_features(model, b["ego"])
    n = feats[0].shape[0]
    R = []
    for _ in range(reps):
        tr0 = E4._recv_encode(model, b)
        with torch.no_grad():
            t0 = time.perf_counter()
            yp, sp = PL.OpenCOODPost.finalize(pp, PL._cands(pp, b["ego"], *PL._heads(model, feats, n)))
            tp0 = time.perf_counter() - t0
        t1 = time.perf_counter()
        BL.b_ray(yp, sp, pts=pts)
        tb = time.perf_counter() - t1
        R.append({"baseline_s": tr0 + tp0, "encode_baseline_s": tr0, "plain_baseline_s": tp0, "mint_extra_s": tb,
                  "overhead": tb / (tr0 + tp0), "tiles": None, "counterfactual_s": 0.0, "boxes": len(yp)})
    return {k: (None if R[0][k] is None else float(np.median([x[k] for x in R]))) for k in R[0]}


def run_scenario(scen, data_root, model, hyp, out_tmp, reps=3):
    from opencood.data_utils.datasets import build_dataset
    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    assert ds.proj_first
    pcr = hyp["preprocess"]["cav_lidar_range"]
    vs = hyp["preprocess"]["args"]["voxel_size"]
    frames, checks, timing = [], [], []
    t_start = time.time()
    for i in range(len(ds)):
        t0 = time.perf_counter()
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        rec, ch = frame_record_e5(model, ds, batch, scen, i, pcr, vs)
        rec["frame_s"] = round(time.perf_counter() - t0, 3)
        frames.append(rec)
        checks += ch
        if i % 20 == 0:
            print(f"  {scen} frame {i}/{len(ds)} n={rec['n_agents']} {rec['frame_s']:.1f}s "
                  f"elapsed {time.time() - t_start:.0f}s", flush=True)
    for i in range(len(ds)):                   # timing pass (separate, after the data pass)
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        pts = np.asarray(E.cav_contents(ds, i)[0][1]["lidar_np"][:, :3], np.float64)
        if int(batch["ego"]["record_len"][0]) >= 2:
            tf = E4.time_frame(model, ds.post_processor, batch, pts, pcr, reps=reps, warm=(i == 0))
        else:       # n = 1: no sender, MINT does nothing (the T(0.05) path cannot run without senders)
            tf = {"n_agents": 1, "encode_isolated_s": float(np.median([E4._recv_encode(model, batch) for _ in range(5)])),
                  "mint": "not timed: n = 1, no counterfactual (MINT overhead 0 by construction)"}
        tf["B-RAY"] = time_bray(model, ds.post_processor, batch, pts, reps=reps)
        tf["frame"] = i
        timing.append(tf)
        if i % 20 == 0:
            dense = tf["dense"]["overhead"] if "dense" in tf else float("nan")
            print(f"  {scen} timing {i}/{len(ds)} n={tf['n_agents']} dense {dense:.3f} "
                  f"bray {tf['B-RAY']['overhead']:.3f}", flush=True)
    res = {"scenario": scen, "block": "TEST", "frames": frames, "compose_checks": checks, "timing": timing,
           "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads()}
    with gzip.open(out_tmp, "wb", compresslevel=3) as f:
        pickle.dump(res, f, protocol=4)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", default=list(TEST_SCENARIOS))
    ap.add_argument("--byte_budget", type=int, default=BYTE_BUDGET)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--dry_run", action="store_true", help="allowlist + planning budget from Stage-1 sizes; no network")
    ap.add_argument("--user_approved", action="store_true", help="the user approved the final-test stream in chat")
    a = ap.parse_args()
    check_allowlist(a.scenarios)
    if a.byte_budget > BYTE_BUDGET:
        sys.exit("refused: budget above the pre-registered 22e9 bytes")
    if a.dry_run:
        sz = s1_sizes()
        ok, proj = budget_ok(0, sz, a.scenarios, a.byte_budget)
        print(json.dumps({"scenarios": len(a.scenarios), "stage1_bytes": sz, "projected_with_1pct": proj,
                          "budget": a.byte_budget, "within_budget": ok, "max_raw_stage1": RAW_CAP}, indent=1))
        return
    if not a.user_approved:
        sys.exit("refused: the final-test stream needs the user's explicit approval (--user_approved); 0 bytes")
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
        "note": "E5 final-test stream (D-55); allowlist = 15 OPV2V test scenarios", "allowlist": list(TEST_SCENARIOS),
        "excluded": list(EXCLUDED), "byte_budget": a.byte_budget, "downloads": []}
    url = TEST_URL
    assert TEST_FILE_ID in url                          # the test archive only
    entries, _ = central_directory(url)
    assert all(e["name"].startswith("test/") for e in entries), "unexpected archive layout"
    names = {e["name"].split("/")[1] for e in entries if e["name"].count("/") >= 2}
    assert set(TEST_SCENARIOS) <= names
    need_all = {s: sum(e["csize"] for e in entries if e["name"].startswith(f"test/{s}/")) for s in a.scenarios}
    spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    todo = [s for s in a.scenarios if not os.path.exists(os.path.join(cache_dir, f"{s}.pkl.gz"))
            and not os.path.exists(os.path.join(stream_parent, f".complete_{s}"))]
    ok, projected = budget_ok(spent, need_all, todo, a.byte_budget)
    ledger["precheck"] = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "need_csize": need_all, "spent": spent,
                          "projected_with_1pct_headers": projected, "budget": a.byte_budget}
    json.dump(ledger, open(ledger_p, "w"), indent=1)
    print("need", need_all, "spent", spent, "projected", projected, "budget", a.byte_budget, flush=True)
    if not ok:
        sys.exit(f"refused: stream would exceed the byte budget ({projected} > {a.byte_budget}); 0 bytes downloaded")

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    stream_root = os.path.join(stream_parent, "test")
    for scen in a.scenarios:
        done = os.path.join(cache_dir, f"{scen}.pkl.gz")
        if os.path.exists(done):
            print(scen, "cached, skip", flush=True)
            continue
        marker = os.path.join(stream_parent, f".complete_{scen}")
        if not os.path.exists(marker):
            need = need_all[scen]
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            if need == 0 or need > RAW_CAP or spent + need > a.byte_budget:
                sys.exit(f"refused {scen}: need {need}, already downloaded {spent}, budget {a.byte_budget}")
            shutil.rmtree(stream_parent, ignore_errors=True)        # never two scenarios on disk
            if shutil.disk_usage(ROOT).free < need + DISK_MARGIN:
                sys.exit(f"refused {scen}: free disk {shutil.disk_usage(ROOT).free} < {need + DISK_MARGIN}")
            os.makedirs(stream_parent)
            t0 = time.time()
            ledger["downloads"].append({"scenario": scen, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "bytes_downloaded": need, "status": "started (counted at full size)"})
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            info = stream_extract(url, entries, f"test/{scen}/", stream_parent)
            ledger["downloads"][-1].update(bytes_downloaded=info["bytes_downloaded"], status="complete",
                                           bytes_written=info["bytes_written"], seconds=round(time.time() - t0))
            json.dump(ledger, open(ledger_p, "w"), indent=1)
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            raw = E.du(stream_parent)
            print(scen, f"downloaded {info['bytes_downloaded'] / 1e9:.3f} GB (total {spent / 1e9:.3f}), "
                  f"raw {raw / 1e9:.2f} GB", flush=True)
            if raw > RAW_CAP or spent > a.byte_budget:
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
        assert all(c["same_candidates"] and c["same_final"] for c in chk["compose_checks"])
        os.replace(tmp, done)
        print(scen, f"processed {len(chk['frames'])} frames in {time.time() - t1:.0f}s; "
              f"cache {os.path.getsize(done) / 1e6:.0f} MB", flush=True)
        shutil.rmtree(stream_parent, ignore_errors=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
