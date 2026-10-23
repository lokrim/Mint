"""E4 step 1: develop and smoke-test spoof_blind on block T (development; no download).

The E0/E3 block-T caches hold decoded candidates but no features, so a new feature attack cannot be
replayed from them. The only block-T raw data on disk is the 24-frame dev slice of
2021_08_22_13_37_16 (data/opv2v/devslice, n = 2). To reach >= 50 realized attacks, each frame is
attacked with K independent seeds (rng_for(family, "devslice:<scen>", frame, seed), seeds 0..K-1).
spoof_feat is run with the same frames and seeds as a reference. Output: an E0-format cache with one
record per (seed, frame); analysis in runners/e4_analyze.py (mode dev).

  python runners/e4_blind_dev.py --seeds 4
"""
import argparse
import gzip
import os
import pickle
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e4_stream as S  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
from stage1_reproduce import CKPT, frame_seed  # noqa: E402

SCEN = "2021_08_22_13_37_16"
OUT = os.path.join(ROOT, "runs/20261023-E4/dev_blind")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    from opencood.data_utils.datasets import build_dataset
    from opencood.tools import train_utils
    import opencood.hypes_yaml.yaml_utils as yaml_utils
    torch.set_num_threads(a.threads)

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    ds = build_dataset(dict(hyp, validate_dir=os.path.join(ROOT, "data/opv2v/devslice/validate")), visualize=False,
                       train=False)
    pcr = hyp["preprocess"]["cav_lidar_range"]
    vs = hyp["preprocess"]["args"]["voxel_size"]
    os.makedirs(os.path.join(OUT, "cache"), exist_ok=True)
    frames = []
    t0 = time.time()
    for k in range(a.seeds):
        for i in range(min(a.frames, len(ds))):
            np.random.seed(frame_seed(SCEN, i, 0))
            b = ds.collate_batch_test([ds[i]])
            rec, _ = S.frame_record(model, ds, b, SCEN, i, families=("clean", "spoof_feat", "spoof_blind"), seed=k,
                                    rng_scen=f"devslice:{SCEN}", compose_check=False, pc_range=pcr, voxel_size=vs)
            rec["scen_key"] = f"devslice/seed{k}"
            frames.append(rec)
        print("seed", k, "done", f"{time.time() - t0:.0f}s", flush=True)
    p = os.path.join(OUT, "cache", "devslice_blind.pkl.gz")
    with gzip.open(p, "wb", compresslevel=3) as f:
        pickle.dump({"scenario": SCEN, "block": "T (dev slice)", "seeds": a.seeds, "frames": frames}, f, protocol=4)
    print("wrote", p, len(frames), flush=True)


if __name__ == "__main__":
    main()
