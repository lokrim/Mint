"""CULVER stream (D-72; runs/20261026-CULVER/plan.json): the frozen v3.2 per-scenario processing on OPV2V Culver City.

Secondary held-out domain-shift evaluation: unseen town, simulated sensor (not real-sensor data). New file only.
  * per scenario: exactly the v3.2 final-test processing, i.e. the frozen v3.1 run_scenario with the D-71 v3_extra,
    installed by v3_2_stream.install() (preregistration_v3_2.json: same levels, sigma_k, tau_k, seeds); block "CULVER";
  * main(): a copy of the frozen v3_stream.main with the Culver archive URL, the 4-scenario allowlist, the member
    prefix test_culver_city/ and the 7e9 byte budget; everything else as v3_stream.main (frozen sha256 + OpenCOOD
    check before network and after the run, interrupted-download STOP, budget checked before the first data byte,
    one scenario on disk, raw cap, free disk, ledger, resume, raw deleted after both cache files are re-read);
  * --sanity_first: download only the first scenario, run clean OpenCOOD inference (stage1_reproduce path), write
    sanity_first_scenario.json (clean AP@0.3/0.5/0.7, default frame-order and global sort) and stop. The extraction
    is kept (.complete_ marker), so the full run reuses it without a second download.

  python runners/culver_stream.py --run_dir runs/20261026-CULVER --dry_run                 (hash + budget, no network)
  python runners/culver_stream.py --run_dir runs/20261026-CULVER --user_approved --sanity_first
  nohup caffeinate -ims .venv/bin/python runners/culver_stream.py --run_dir runs/20261026-CULVER --user_approved \
      > runs/20261026-CULVER/run.log 2>&1 &
"""
import argparse
import copy
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
import e5_stream as S  # noqa: E402
import v3_1_stream as S31  # noqa: E402
import v3_2_stream as S32  # noqa: E402
import v3_stream as S3  # noqa: E402
from stage1_reproduce import CKPT, frame_seed  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

PLAN = "runs/20261026-CULVER/plan.json"
CULVER_FILE_ID = "f_1621693876387"
CULVER_URL = ("https://ucla.app.box.com/index.php?rm=box_download_shared_file"
              "&vanity_name=UCLA-MobilityLab-OPV2V&file_id=" + CULVER_FILE_ID)
TOP = "test_culver_city"
CULVER_SCENARIOS = ("2021_09_03_09_32_17", "2021_09_03_10_53_32", "2021_09_03_20_08_37", "2021_09_03_22_43_57")
BYTE_BUDGET = 7_000_000_000
BLOCK = "CULVER"


def check_allowlist(scens):
    bad = [s for s in scens if s not in CULVER_SCENARIOS]
    if bad or len(set(scens)) != len(scens) or not scens:
        sys.exit(f"refused: not in the D-72 Culver City allowlist (or duplicated/empty): {bad or scens}")


def plan_sizes():
    """Member bytes per scenario recorded in plan.json from the central directory (for the no-network dry run)."""
    sc = json.load(open(os.path.join(ROOT, PLAN)))["data"]["scenarios"]
    return {s: sc[s]["member_csize_bytes"] for s in CULVER_SCENARIOS}


def sanity_clean_ap(scen, data_root, model, hyp, out_p):
    """Clean OpenCOOD inference on one scenario (stage1_reproduce path, per-frame seed); detector-level only."""
    import stage1_reproduce as R
    from opencood.data_utils.datasets import build_dataset
    from opencood.tools import inference_utils
    from opencood.utils import eval_utils
    h = copy.deepcopy(hyp)
    h["validate_dir"] = data_root
    ds = build_dataset(h, visualize=False, train=False)
    stat, agents, t0 = R.empty_stat(), [], time.time()
    for i in range(len(ds)):
        np.random.seed(frame_seed(scen, i, 0))
        batch = ds.collate_batch_test([ds[i]])
        agents.append(int(batch["ego"]["record_len"][0]))
        with torch.no_grad():
            pb, ps, gb = inference_utils.inference_intermediate_fusion(batch, model, ds)
        for iou in R.IOUS:
            eval_utils.caluclate_tp_fp(pb, ps, gb, stat, iou)
    res = {"label": "CULVER sanity check (D-72 plan): clean detector only, first scenario; no MINT method or attack",
           "scenario": scen, "frames": len(ds), "agents_hist": {str(k): agents.count(k) for k in sorted(set(agents))},
           "ap_frame_order_opencood_default": R.ap_of(stat, False), "ap_global_sort": R.ap_of(stat, True),
           "published_culver_ap07_all_scenarios": 0.735, "stop_if_ap07_below": 0.6, "seconds": round(time.time() - t0)}
    res["pass"] = res["ap_frame_order_opencood_default"]["AP@0.7"] >= 0.6
    json.dump(res, open(out_p, "w"), indent=1)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--scenarios", nargs="+", default=list(CULVER_SCENARIOS))
    ap.add_argument("--byte_budget", type=int, default=BYTE_BUDGET)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--sanity_first", action="store_true", help="download the first scenario, clean AP only, stop")
    ap.add_argument("--user_approved", action="store_true", help="the user approved the Culver City stream in chat")
    a = ap.parse_args()
    check_allowlist(a.scenarios)
    if a.byte_budget > BYTE_BUDGET:
        sys.exit("refused: budget above the planned 7e9 bytes")
    S32.install()                                       # v3.1 run_scenario + D-71 v3_extra + preregistration_v3_2
    assert S3.PREREG == S32.PREREG_V32 and S31.v3_extra is S32.v3_extra
    pr = json.load(open(os.path.join(ROOT, S3.PREREG)))
    bad = S3.verify_frozen(pr)
    if bad:
        sys.exit(f"refused: frozen files differ from preregistration_v3_2: {bad}")
    print("frozen sha256 (preregistration_v3_2) + OpenCOOD commit verified", flush=True)
    run_dir = os.path.join(ROOT, a.run_dir)
    os.makedirs(run_dir, exist_ok=True)
    ledger_p = os.path.join(run_dir, "download_ledger.json")
    ledger = json.load(open(ledger_p)) if os.path.exists(ledger_p) else {
        "note": "CULVER stream (D-72, plan runs/20261026-CULVER/plan.json; frozen v3.2 processing)",
        "url_file_id": CULVER_FILE_ID, "allowlist": list(CULVER_SCENARIOS), "byte_budget": a.byte_budget,
        "downloads": []}
    if S3.interrupted(ledger):
        sys.exit(f"STOP: interrupted download(s) in the ledger {S3.interrupted(ledger)}; ask the user before any restart")
    if a.dry_run:
        sz = plan_sizes()
        ok, proj = S.budget_ok(0, sz, a.scenarios, a.byte_budget)
        print(json.dumps({"scenarios": len(a.scenarios), "plan_bytes_total": sum(sz.values()), "projected_with_1pct": proj,
                          "budget": a.byte_budget, "within_budget": ok}, indent=1))
        return
    if not a.user_approved:
        sys.exit("refused: the Culver City stream needs the user's explicit approval (--user_approved); 0 bytes")
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    from tools.ranged_zip import central_directory, stream_extract

    torch.set_num_threads(a.threads)
    torch.set_num_interop_threads(1)
    cache_dir, extra_dir = os.path.join(run_dir, "cache"), os.path.join(run_dir, "v3extra")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(extra_dir, exist_ok=True)
    url = CULVER_URL
    entries, total = central_directory(url)
    assert all(e["name"].startswith(f"{TOP}/") for e in entries), "unexpected archive layout"
    names = {e["name"].split("/")[1] for e in entries if e["name"].count("/") >= 2}
    assert set(CULVER_SCENARIOS) <= names, names
    need_all = {s: sum(e["csize"] for e in entries if e["name"].startswith(f"{TOP}/{s}/")) for s in a.scenarios}
    assert need_all == {s: plan_sizes()[s] for s in a.scenarios}, ("member sizes differ from plan.json", need_all)
    spent = sum(d["bytes_downloaded"] for d in ledger["downloads"])
    stream_parent = os.path.join(ROOT, "data/opv2v/stream")
    done_p = lambda s: (os.path.join(cache_dir, f"{s}.pkl.gz"), os.path.join(extra_dir, f"{s}.pkl.gz"))  # noqa: E731
    todo = [s for s in a.scenarios if not all(map(os.path.exists, done_p(s)))
            and not os.path.exists(os.path.join(stream_parent, f".complete_{s}"))]
    ok, projected = S.budget_ok(spent, need_all, todo, a.byte_budget)
    ledger["precheck"] = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "archive_bytes": total, "need_csize": need_all,
                          "spent": spent, "projected_with_1pct_headers": projected, "budget": a.byte_budget}
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
    stream_root = os.path.join(stream_parent, TOP)
    scens = a.scenarios[:1] if a.sanity_first else a.scenarios
    for scen in scens:
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
            info = stream_extract(url, entries, f"{TOP}/{scen}/", stream_parent)
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
        if a.sanity_first:
            r = sanity_clean_ap(scen, stream_root, model, hyp, os.path.join(run_dir, "sanity_first_scenario.json"))
            print("sanity (clean detector):", json.dumps(r), flush=True)
            print("extraction kept for the full run (no second download)", flush=True)
            return
        t1 = time.time()
        tmp, tmp_x = done + ".tmp", done_x + ".tmp"
        S31.run_scenario(scen, stream_root, model, hyp, tmp, tmp_x, pr, reps=a.reps, block=BLOCK)
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
    bad = S3.verify_frozen(pr)                          # post-run re-check
    print("post-run frozen check:", "OK" if not bad else bad, flush=True)
    print("all done", flush=True)


if __name__ == "__main__":
    main()
