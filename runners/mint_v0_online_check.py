"""Online MINT-v0.0 (mint.reliability.pipeline) vs the cache-based evaluation on the saved
24-frame development slice of 2021_08_22_13_37_16 (clean). Checks identical final boxes and
records per-stage latency on the M1 CPU.

Latency accounting (E1 A2): baseline = receiver-only encode + plain fusion + decode + post-process.
Encoding the senders' point clouds is not receiver work (their features arrive on the wire); it is
measured separately (encode_all - encode_receiver) and excluded. MINT overhead = counterfactual +
evidence + compose. The gated output is composed from the already-computed decodes (E1 A1).

  python runners/mint_v0_online_check.py [--out runs/20261023-E1/online_check.json]
"""
import argparse
import gzip
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import stage1_spike as S  # noqa: E402,F401
from stage1_reproduce import CKPT, frame_seed  # noqa: E402
import e0_stream as E  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
from opencood.data_utils.datasets import build_dataset  # noqa: E402
from opencood.tools import train_utils  # noqa: E402
import opencood.hypes_yaml.yaml_utils as yaml_utils  # noqa: E402

from mint.fusion.compose import compose, finalize  # noqa: E402
from mint.reliability import v0  # noqa: E402
from mint.model.attfuse_parts import agent_features, receiver_features  # noqa: E402
from mint.reliability.pipeline import mint_v0_frame  # noqa: E402
import time  # noqa: E402

SCEN = "2021_08_22_13_37_16"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "runs/20261023-E1/online_check.json"))
    args = ap.parse_args()
    torch.set_num_threads(8)

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    ds = build_dataset(dict(hyp, validate_dir=os.path.join(ROOT, "data/opv2v/devslice/validate")), visualize=False, train=False)
    pp = ds.post_processor
    cache = pickle.load(gzip.open(os.path.join(ROOT, "runs/20261023-E0/cache", f"{SCEN}.pkl.gz")))
    res, times = [], []
    for i in range(len(ds)):
        np.random.seed(frame_seed(SCEN, i, 0))
        b = ds.collate_batch_test([ds[i]])
        pts = np.asarray(E.cav_contents(ds, i)[0][1]["lidar_np"][:, :3], np.float64)
        with torch.no_grad():
            if i == 0:                                   # warm-up (not timed)
                agent_features(model, b["ego"]); receiver_features(model, b["ego"])
            t0 = time.perf_counter()
            feats, _ = agent_features(model, b["ego"])
            t_all = time.perf_counter() - t0
            t0 = time.perf_counter()
            fr0 = receiver_features(model, b["ego"])
            t_recv = time.perf_counter() - t0
            assert all(torch.equal(a[0], r[0]) for a, r in zip(feats, fr0))
        o = mint_v0_frame(model, pp, b, pts, hyp["preprocess"]["cav_lidar_range"], v0.Params(theta=0.0), feats=feats)
        o["timing_s"] = {"encode_receiver": t_recv, "encode_all": t_all, **o["timing_s"]}
        fr = cache["frames"][i]
        c = fr["conditions"]["clean"]
        rel = v0.assess(c["effects"], v0.Params(theta=0.0))
        ch = v0.gating_choice(rel)
        cb, cs = finalize(pp, compose(c["cands"], ch)) if ch else finalize(pp, c["cands"][frozenset()])
        same = o["boxes"].shape == cb.shape and (cb.size == 0 or float(np.abs(o["boxes"] - cb).max()) == 0.0)
        res.append({"frame": i, "same_boxes": bool(same), "same_choice": o["choice"] == ch, "n_gated": len(ch),
                    "units": len(o["reliability"]), "extra_decodes": o["extra_decodes"]})
        times.append(o["timing_s"])
        print(res[-1], {k: round(v, 3) for k, v in o["timing_s"].items()}, flush=True)
    keys = times[0].keys()
    out = {"frames": len(res), "all_same_boxes": all(r["same_boxes"] for r in res),
           "all_same_choice": all(r["same_choice"] for r in res),
           "frames_with_gating": sum(r["n_gated"] > 0 for r in res),
           "latency_s_p50": {k: round(float(np.median([t[k] for t in times])), 3) for k in keys},
           "latency_s_p95": {k: round(float(np.percentile([t[k] for t in times], 95)), 3) for k in keys},
           "agents": "2 (scenario 2021_08_22_13_37_16)"}
    base = np.array([t["encode_receiver"] + t["plain"] for t in times])
    extra = np.array([t["counterfactual"] + t["evidence"] + t["compose"] for t in times])
    ov = extra / base
    out["final_step"] = "compose()+finalize() over the already-computed decodes (no final masked decode)"
    out["extra_decodes_total"] = sum(r["extra_decodes"] for r in res)
    out["baseline"] = "receiver-only encode + plain fusion + decode + post-process"
    out["overhead_p50"] = round(float(np.median(ov)), 3)
    out["overhead_p95"] = round(float(np.percentile(ov, 95)), 3)
    out["sender_encode_s_p50"] = round(float(np.median([t["encode_all"] - t["encode_receiver"] for t in times])), 3)
    out["sender_encode_share_of_encode_all_p50"] = round(float(np.median(
        [(t["encode_all"] - t["encode_receiver"]) / t["encode_all"] for t in times])), 3)
    old = np.array([t["encode_all"] + t["plain"] for t in times])
    out["overhead_old_accounting_p50"] = round(float(np.median(extra / old)), 3)
    out["note"] = "development block T, 24-frame slice, M1 CPU 8 threads, in-sample"
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
