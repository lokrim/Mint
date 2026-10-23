"""v3 final test stream (preregistration_v3; NOT RUN until the user approves the final test).

Per frame, exactly the frozen v2 record (e5_stream.frame_record_e5: E4 record + float64 `yplus_rays`) in
cache/<scen>.pkl.gz, plus a side record in v3extra/<scen>.pkl.gz:
  mabs  per condition (clean + applied families + PGD): per-agent per-scale mean |feature| (B-NORM, D-66)
  pgd   the D-65 PGD families at the pre-registered test level r (preregistration_v3.json), sender 1,
        E4-format condition records + yplus_rays + mabs; n = 1 frames: none (scored as clean)
Then the frozen D-42 timing pass (e5_stream.time_frame_e5, unchanged; PGD and B-NORM are not timed).

Safety (v2 + v3 procedural checks):
  * before any network access: sha256 of every file listed in preregistration_v3.json `frozen_sha256`
    (incl. attfuse_parts.py, opencood_shims.py, stage1_spike.py, latest.pth) and the OpenCOOD commit must match;
  * an interrupted download in the ledger (status not 'complete') -> STOP and ask the user (no restart);
  * allowlist = the 15 D-55 scenarios; test archive only; byte budget 22e9 checked BEFORE the first data byte;
    one scenario on disk; raw <= 3e9; free disk checked; raw deleted after both cache files are re-read.

  python runners/v3_stream.py --run_dir runs/<date>-E5v3 --user_approved     (after approval only)
  python runners/v3_stream.py --run_dir runs/<date>-E5v3 --dry_run           (hash + budget check, no network)
"""
import argparse
import gzip
import hashlib
import json
import os
import pickle
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e0_stream as E  # noqa: E402
import e5_stream as S  # noqa: E402
import v3_common as V  # noqa: E402
from stage1_reproduce import CKPT, TEST_URL, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.geometry.ground import ground_mask  # noqa: E402
from mint.model.attfuse_parts import agent_features  # noqa: E402

PREREG = "runs/20261024-E5/preregistration_v3.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def opencood_commit():
    d = os.path.join(ROOT, "third_party", "OpenCOOD")
    c = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=d, capture_output=True,
                           text=True).stdout.strip()
    return c, dirty == ""


def verify_frozen(pr):
    bad = {p: (h, sha256(os.path.join(ROOT, p))) for p, h in pr["frozen_sha256"].items()
           if not os.path.exists(os.path.join(ROOT, p)) or sha256(os.path.join(ROOT, p)) != h}
    c, clean = opencood_commit()
    oc = pr["opencood"]
    if c != oc["commit"] or not clean:
        bad["OpenCOOD"] = (oc["commit"], c, "clean" if clean else "local diff")
    return bad


def interrupted(ledger):
    return [d for d in ledger.get("downloads", []) if d.get("status") != "complete"]


def v3_extra(model, ds, batch, rec, scen, i, pcr, vs, levels, sigma, thr):
    n = rec["n_agents"]
    cavs = E.cav_contents(ds, i)
    ego = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
    att_pts = E.projected_points(cavs[1][1], pcr) if n >= 2 else None
    with torch.no_grad():
        feats0, _ = agent_features(model, batch["ego"])
    mabs = V.bnorm_extras(model, batch, rec, scen, i, feats0, att_pts, ego, pcr, vs)
    gmask, _ = ground_mask(ego)
    pgd = V.pgd_conditions(model, ds.post_processor, batch, feats0, n, ego, gmask, pcr, scen, i, levels, sigma, thr)
    for c, r in pgd.items():
        mabs[c] = r["mabs"]
    return {"frame": i, "mabs": mabs, "pgd": pgd}


def run_scenario(scen, data_root, model, hyp, out_tmp, extra_tmp, pr, reps=3, max_frames=None, block="TEST",
                 ds_hook=None):
    from opencood.data_utils.datasets import build_dataset
    ds = build_dataset(dict(hyp, validate_dir=data_root), visualize=False, train=False)
    if ds_hook is not None:
        ds_hook(ds)
    assert ds.proj_first
    pcr = hyp["preprocess"]["cav_lidar_range"]
    vs = hyp["preprocess"]["args"]["voxel_size"]
    thr = ds.post_processor.params["target_args"]["score_threshold"]
    levels = {f: [v["r"]] for f, v in pr["pgd_families"]["test_levels"].items()}
    sigma = pr["pgd_families"]["sigma_k"]
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
        ex = v3_extra(model, ds, batch, rec, scen, i, pcr, vs, levels, sigma, thr)
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
        pickle.dump({"scenario": scen, "preregistration": PREREG, "levels": levels, "sigma": sigma, "frames": extras}, f,
                    protocol=4)
    return res, extras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", default=list(S.TEST_SCENARIOS))
    ap.add_argument("--byte_budget", type=int, default=S.BYTE_BUDGET)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--user_approved", action="store_true", help="the user approved the final-test stream in chat")
    a = ap.parse_args()
    S.check_allowlist(a.scenarios)
    if a.byte_budget > S.BYTE_BUDGET:
        sys.exit("refused: budget above the pre-registered 22e9 bytes")
    pr = json.load(open(os.path.join(ROOT, PREREG)))
    bad = verify_frozen(pr)
    if bad:
        sys.exit(f"refused: frozen files differ from preregistration_v3: {bad}")
    print("frozen sha256 + OpenCOOD commit verified", flush=True)
    run_dir = os.path.join(ROOT, a.run_dir)
    ledger_p = os.path.join(run_dir, "download_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else {
        "note": "E5 v3 final-test stream (D-55, preregistration_v3)", "allowlist": list(S.TEST_SCENARIOS),
        "excluded": list(S.EXCLUDED), "byte_budget": a.byte_budget, "downloads": []}
    if interrupted(ledger):
        sys.exit(f"STOP: interrupted download(s) in the ledger {interrupted(ledger)}; ask the user before any restart")
    if a.dry_run:
        sz = S.s1_sizes()
        ok, proj = S.budget_ok(0, sz, a.scenarios, a.byte_budget)
        print(json.dumps({"scenarios": len(a.scenarios), "stage1_bytes_total": sum(sz.values()), "projected_with_1pct": proj,
                          "budget": a.byte_budget, "within_budget": ok}, indent=1))
        return
    if not a.user_approved:
        sys.exit("refused: the final-test stream needs the user's explicit approval (--user_approved); 0 bytes")
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    from tools.ranged_zip import central_directory, stream_extract

    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(1)
    cache_dir, extra_dir = os.path.join(run_dir, "cache"), os.path.join(run_dir, "v3extra")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(extra_dir, exist_ok=True)
    url = TEST_URL
    assert S.TEST_FILE_ID in url                          # the test archive only
    entries, _ = central_directory(url)
    assert all(e["name"].startswith("test/") for e in entries), "unexpected archive layout"
    names = {e["name"].split("/")[1] for e in entries if e["name"].count("/") >= 2}
    assert set(S.TEST_SCENARIOS) <= names
    need_all = {s: sum(e["csize"] for e in entries if e["name"].startswith(f"test/{s}/")) for s in a.scenarios}
    spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    done_p = lambda s: (os.path.join(cache_dir, f"{s}.pkl.gz"), os.path.join(extra_dir, f"{s}.pkl.gz"))
    todo = [s for s in a.scenarios if not all(map(os.path.exists, done_p(s)))
            and not os.path.exists(os.path.join(stream_parent, f".complete_{s}"))]
    ok, projected = S.budget_ok(spent, need_all, todo, a.byte_budget)
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
        done, done_x = done_p(scen)
        if os.path.exists(done) and os.path.exists(done_x):
            print(scen, "cached, skip", flush=True)
            continue
        marker = os.path.join(stream_parent, f".complete_{scen}")
        if not os.path.exists(marker):
            need = need_all[scen]
            spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
            if need == 0 or need > S.RAW_CAP or spent + need > a.byte_budget:
                sys.exit(f"refused {scen}: need {need}, already downloaded {spent}, budget {a.byte_budget}")
            shutil.rmtree(stream_parent, ignore_errors=True)
            if shutil.disk_usage(ROOT).free < need + S.DISK_MARGIN:
                sys.exit(f"refused {scen}: free disk {shutil.disk_usage(ROOT).free} < {need + S.DISK_MARGIN}")
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
            print(scen, f"downloaded {info['bytes_downloaded'] / 1e9:.3f} GB (total {spent / 1e9:.3f}), raw {raw / 1e9:.2f} GB",
                  flush=True)
            if raw > S.RAW_CAP or spent > a.byte_budget:
                shutil.rmtree(stream_parent, ignore_errors=True)
                sys.exit(f"raw {raw} or total {spent} over the cap/budget; deleted")
            open(marker, "w").write(json.dumps(info))
        else:
            print(scen, "reusing complete extraction", flush=True)
        got = sorted(os.listdir(stream_root))
        assert got == [scen], f"unexpected content on disk: {got}"
        t1 = time.time()
        tmp, tmp_x = done + ".tmp", done_x + ".tmp"
        run_scenario(scen, stream_root, model, hyp, tmp, tmp_x, pr, reps=a.reps)
        with gzip.open(tmp, "rb") as f:
            chk = pickle.load(f)
        with gzip.open(tmp_x, "rb") as f:
            chx = pickle.load(f)
        assert chk["scenario"] == scen and len(chk["frames"]) > 0 and len(chk["timing"]) == len(chk["frames"])
        assert len(chx["frames"]) == len(chk["frames"])
        assert all(c["same_candidates"] and c["same_final"] for c in chk["compose_checks"])
        os.replace(tmp, done)
        os.replace(tmp_x, done_x)
        print(scen, f"processed {len(chk['frames'])} frames in {time.time() - t1:.0f}s; cache {os.path.getsize(done) / 1e6:.0f} MB, "
              f"v3extra {os.path.getsize(done_x) / 1e6:.0f} MB", flush=True)
        shutil.rmtree(stream_parent, ignore_errors=True)
    bad = verify_frozen(pr)                            # post-run re-check
    print("post-run frozen check:", "OK" if not bad else bad, flush=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
