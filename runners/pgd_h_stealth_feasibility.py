"""D-68 (amended) feasibility on block H from clean features only (no attack): per frame, scale and r, is the
stealth constraint reachable inside the box, i.e. mean(max(f_k - eps_k, 0)) <= 0.95 tau_k mean|f_receiver,k|?

  python runners/pgd_h_stealth_feasibility.py --run_dir runs/20261024-PGD
"""
import argparse
import glob
import gzip
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import pgd_h_run as HR  # noqa: E402
import v3_common as V  # noqa: E402
import e0_analyze as A  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
from mint.model.attfuse_parts import agent_features  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    a = ap.parse_args()
    rd = os.path.join(ROOT, a.run_dir)
    pl = json.load(open(os.path.join(rd, "plan_stealth.json")))
    sig, tau, levels = np.array(pl["sigma_k"]), np.array(pl["tau_k"]), pl["levels_r"]
    torch.set_num_threads(8)
    model, _ = HR.load_model()
    anchor = A.post_processor().generate_anchor_box()
    rows = []
    for p in sorted(glob.glob(os.path.join(rd, "extra", "20*_[0-9][0-9].pkl.gz"))):
        X = pickle.load(gzip.open(p))
        scen = X["scenario"]
        for ex in X["frames"]:
            with torch.no_grad():
                f, _ = agent_features(model, V.rebuild_batch(ex["inputs"], anchor)["ego"])
            rec = [f[k][0].abs().double().mean().item() for k in range(3)]
            for r in levels:
                minr = [torch.clamp(f[k][1].double() - r * sig[k], min=0).mean().item() / rec[k] for k in range(3)]
                rows.append({"scen": scen, "frame": ex["frame"], "r": r, "min_ratio": minr,
                             "feasible": [m <= 0.95 * t for m, t in zip(minr, tau)]})
        print("done", scen, flush=True)
    out = {"label": "DEVELOPMENT, block H clean features only (no attack); D-68 amended feasibility", "bound": (0.95 * tau).tolist()}
    for r in levels:
        R = [x for x in rows if x["r"] == r]
        inf = [x for x in R if not all(x["feasible"])]
        out[f"r{r}"] = {"frames": len(R), "infeasible_frames": len(inf),
                        "infeasible_by_scale": [sum(not x["feasible"][k] for x in R) for k in range(3)],
                        "by_scenario": {s: sum(x["scen"] == s for x in inf) for s in sorted({x["scen"] for x in R})},
                        "examples": [{k: x[k] for k in ("scen", "frame", "min_ratio")} for x in inf[:5]]}
    json.dump(out, open(os.path.join(rd, "stealth_feasibility_by_r.json"), "w"), indent=1)
    print(json.dumps({k: {kk: v[kk] for kk in ("infeasible_frames", "infeasible_by_scale", "by_scenario")}
                      for k, v in out.items() if k.startswith("r")}, indent=1))


if __name__ == "__main__":
    main()
