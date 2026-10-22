"""Stage-1 V-01 reproduction + multi-agent V-03 locality on the full OPV2V test split (CPU).

Streams one scenario at a time from the remote test zip (only .pcd/.yaml written), runs the frozen
AttFuse checkpoint through OpenCOOD's own inference path, caches small per-frame predictions,
then deletes the raw scenario. Resumable: finished scenarios are skipped.

  python runners/stage1_reproduce.py --run_dir runs/<id> [--only SCEN ...]
"""
import argparse
import copy
import glob
import json
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import stage1_spike as S  # noqa: E402  (installs shims, sets paths)

import numpy as np  # noqa: E402
import torch  # noqa: E402

from opencood.data_utils.datasets import build_dataset  # noqa: E402
from opencood.tools import inference_utils, train_utils  # noqa: E402
from opencood.utils import eval_utils  # noqa: E402
import opencood.hypes_yaml.yaml_utils as yaml_utils  # noqa: E402
from tools.ranged_zip import central_directory, stream_extract  # noqa: E402

TEST_URL = ("https://ucla.app.box.com/index.php?rm=box_download_shared_file"
            "&vanity_name=UCLA-MobilityLab-OPV2V&file_id=f_1621736219709")
CKPT = os.path.join(ROOT, "data/opv2v/ckpt/pointpillar_attentive_fusion/pointpillar_attentive_fusion")
IOUS = (0.3, 0.5, 0.7)


def empty_stat():
    return {k: {"tp": [], "fp": [], "gt": 0, "score": []} for k in IOUS}


def ap_of(stat, gs):
    return {f"AP@{i}": round(float(eval_utils.calculate_ap(copy.deepcopy(stat), i, gs)[0]), 4) for i in IOUS}


def frame_seed(scen, i, base):
    import hashlib
    return int.from_bytes(hashlib.sha256(f"{base}|{scen}|{i}".encode()).digest()[:4], "little")


def run_scenario(scen, data_root, model, hypes, out_dir, rng, loc_per_scen, threads, np_seed_base=0, tag=""):
    hypes = copy.deepcopy(hypes)
    hypes["validate_dir"] = data_root
    ds = build_dataset(hypes, visualize=False, train=False)

    def loader():
        # OpenCOOD shuffles points at test time with unseeded np.random: seed per frame for determinism
        for i in range(len(ds)):
            np.random.seed(frame_seed(scen, i, np_seed_base))
            yield ds.collate_batch_test([ds[i]])
    stat = empty_stat()
    preds, agents, t_inf, loc = {}, [], [], []
    every = max(1, len(ds) // max(1, loc_per_scen))
    for i, batch in enumerate(loader()):
        n = int(batch["ego"]["record_len"][0])
        agents.append(n)
        t0 = time.perf_counter()
        with torch.no_grad():
            pb, ps, gb = inference_utils.inference_intermediate_fusion(batch, model, ds)
        t_inf.append(time.perf_counter() - t0)
        for iou in IOUS:
            eval_utils.caluclate_tp_fp(pb, ps, gb, stat, iou)
        preds[f"f{i:04d}_pred"] = np.zeros((0, 8, 3), np.float32) if pb is None else pb.numpy().astype(np.float32)
        preds[f"f{i:04d}_score"] = np.zeros((0,), np.float32) if ps is None else ps.numpy().astype(np.float32)
        preds[f"f{i:04d}_gt"] = gb.numpy().astype(np.float32)
        # prefer multi-agent frames for locality tests
        if (i % every == 0 or (n >= 3 and len(loc) < loc_per_scen and rng.random() < 0.05)) and len(loc) < loc_per_scen:
            loc.append({"frame": i, **S.locality_test(model, ds, batch, rng)})
    np.savez_compressed(os.path.join(out_dir, "preds", f"{scen}{tag}.npz"), **preds)
    return {"scenario": scen, "np_seed_base": np_seed_base, "frames": len(ds), "agents": {"min": min(agents), "max": max(agents),
            "mean": round(float(np.mean(agents)), 2)}, "stat": stat,
            "ap_scenario": ap_of(stat, False), "infer_s": {"p50": round(float(np.median(t_inf)), 4),
            "p95": round(float(np.percentile(t_inf, 95)), 4)}, "locality": loc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--loc_per_scen", type=int, default=6)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--max_raw_bytes", type=int, default=3_300_000_000)
    ap.add_argument("--extra_np_seeds", type=int, nargs="*", default=[],
                    help="re-run inference with these point-shuffle seeds (variability check)")
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    run_dir = os.path.join(ROOT, a.run_dir) if not os.path.isabs(a.run_dir) else a.run_dir
    os.makedirs(os.path.join(run_dir, "scenarios"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "preds"), exist_ok=True)
    log = open(os.path.join(run_dir, "log.txt"), "a")

    def say(*x):
        msg = " ".join(str(v) for v in x)
        print(msg, flush=True)
        log.write(time.strftime("%H:%M:%S ") + msg + "\n")
        log.flush()

    class Opt:
        model_dir = CKPT
    hypes = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hypes)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    entries, total = central_directory(TEST_URL)
    scens = sorted({e["name"].split("/")[1] for e in entries if e["name"].count("/") >= 2})
    if a.only:
        scens = [s for s in scens if s in a.only]
    say(f"archive {total} bytes; {len(scens)} scenarios")
    stream_root = os.path.join(ROOT, "data/opv2v/stream/test")
    for k, scen in enumerate(scens):
        done = os.path.join(run_dir, "scenarios", f"{scen}.json")
        if os.path.exists(done):
            say(f"[{k + 1}/{len(scens)}] {scen}: done, skip")
            continue
        rng = np.random.default_rng(a.seed + k)
        shutil.rmtree(os.path.dirname(stream_root), ignore_errors=True)
        os.makedirs(stream_root)
        need = sum(e["csize"] for e in entries if e["name"].startswith(f"test/{scen}/"))
        if need > a.max_raw_bytes * 1.6:
            say(f"{scen}: compressed span {need} too large for raw-disk budget; skipped")
            continue
        t0 = time.time()
        info = stream_extract(TEST_URL, entries, f"test/{scen}/", os.path.dirname(stream_root))
        raw = sum(os.path.getsize(p) for p in glob.glob(os.path.join(stream_root, "**", "*"), recursive=True)
                  if os.path.isfile(p))
        say(f"[{k + 1}/{len(scens)}] {scen}: downloaded {info['bytes_downloaded'] / 1e9:.2f} GB in "
            f"{time.time() - t0:.0f}s; raw on disk {raw / 1e9:.2f} GB")
        if raw > a.max_raw_bytes:
            say(f"  WARNING raw on disk exceeds budget ({raw})")
        t1 = time.time()
        res = run_scenario(scen, stream_root, model, hypes, run_dir, rng, a.loc_per_scen, a.threads)
        res["seed_variability"] = []
        for sb in a.extra_np_seeds:
            r2 = run_scenario(scen, stream_root, model, hypes, run_dir, np.random.default_rng(0), 0, a.threads,
                              np_seed_base=sb, tag=f"_seed{sb}")
            res["seed_variability"].append({"np_seed_base": sb, "ap_scenario": r2["ap_scenario"]})
        res.update({"download": info, "raw_bytes_on_disk": raw, "wall_infer_s": round(time.time() - t1, 1)})
        with open(done, "w") as f:
            json.dump(res, f)
        say(f"  frames {res['frames']} agents {res['agents']} AP {res['ap_scenario']} "
            f"loc_ok {all(x.get('bit_identical_outside', True) for x in res['locality'])}")
        shutil.rmtree(os.path.dirname(stream_root), ignore_errors=True)
    say("all scenarios processed")


if __name__ == "__main__":
    main()
