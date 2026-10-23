"""Online MINT-v0.0 (mint.reliability.pipeline) vs the cache-based evaluation on the saved
24-frame development slice of 2021_08_22_13_37_16 (clean). Checks identical final boxes and
records per-stage latency on the M1 CPU.

  python runners/mint_v0_online_check.py
"""
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
from mint.reliability.pipeline import mint_v0_frame  # noqa: E402

SCEN = "2021_08_22_13_37_16"


def main():
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
        o = mint_v0_frame(model, pp, b, pts, hyp["preprocess"]["cav_lidar_range"], v0.Params(theta=0.0))
        fr = cache["frames"][i]
        c = fr["conditions"]["clean"]
        rel = v0.assess(c["effects"], v0.Params(theta=0.0))
        ch = v0.gating_choice(rel)
        cb, cs = finalize(pp, compose(c["cands"], ch)) if ch else finalize(pp, c["cands"][frozenset()])
        same = o["boxes"].shape == cb.shape and (cb.size == 0 or float(np.abs(o["boxes"] - cb).max()) == 0.0)
        res.append({"frame": i, "same_boxes": bool(same), "same_choice": o["choice"] == ch, "n_gated": len(ch),
                    "units": len(o["reliability"])})
        times.append(o["timing_s"])
        print(res[-1], {k: round(v, 3) for k, v in o["timing_s"].items()}, flush=True)
    keys = times[0].keys()
    out = {"frames": len(res), "all_same_boxes": all(r["same_boxes"] for r in res),
           "all_same_choice": all(r["same_choice"] for r in res),
           "frames_with_gating": sum(r["n_gated"] > 0 for r in res),
           "latency_s_p50": {k: round(float(np.median([t[k] for t in times])), 3) for k in keys},
           "latency_s_p95": {k: round(float(np.percentile([t[k] for t in times], 95)), 3) for k in keys},
           "agents": "2 (scenario 2021_08_22_13_37_16)"}
    tot = [sum(t.values()) for t in times]
    plain = [t["encode"] + t["plain"] for t in times]
    out["overhead_vs_plain_p50"] = round(float(np.median(np.array(tot) / np.array(plain) - 1)), 3)
    json.dump(out, open(os.path.join(ROOT, "runs/20261023-E0/mint_v0_online_check.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
