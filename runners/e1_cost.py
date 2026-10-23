"""E1 Part A3: counterfactual cost vs number of agents (development slice, block T; timing only).

For each of the 24 dev-slice frames (2021_08_22_13_37_16, 2 real agents) and n = 2..5 agents
(n > 2 replicates sender 1's features; timing only), runs the full online MINT frame
(mint.reliability.pipeline.mint_frame, rule MINT-v0.0 theta = 0) with each counterfactual mode:
  sequential       n-1 counterfactual decodes one after another (as implemented in E0)
  batched          the n-1 counterfactual decodes in one forward pass
  footprint_literal sender i's non-zero feature footprint (pre-registered wording). Measured to be
                   100% of pixels at every scale (BatchNorm bias), i.e. identical to sequential;
                   reported as such, not re-timed.
  footprint_pillar diagnostic (not pre-registered): decode only tiles holding any of sender i's
                   pillars (dilation 0 / 1 tile); inexact in principle (softmax renormalisation)
  joint            diagnostic (not pre-registered): Y+ and the n-1 counterfactuals in one pass

Per frame: baseline = receiver-only encode + plain fusion/decode/post-process (timed separately);
overhead = MINT-only stages / baseline (pre-registered definition), MINT-only = counterfactual +
evidence + compose (joint: joint pass + post-process - plain-only time). Each (frame, n, mode) is
run --reps times interleaved and the per-frame median is used (M1 scheduler noise). Exactness: final boxes of
every counterfactual and of the gated output equal to the sequential mode.

  python runners/e1_cost.py [--out runs/20261023-E1/cost.json]
"""
import argparse
import json
import os
import sys
import time

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

from mint.fusion.compose import finalize  # noqa: E402
from mint.model.attfuse_parts import agent_features, decode_batch, fuse_scale, receiver_features  # noqa: E402
from mint.reliability import v0  # noqa: E402
from mint.reliability import pipeline as PL  # noqa: E402

SCEN = "2021_08_22_13_37_16"
NS = (2, 3, 4, 5)
MODES = ("sequential", "batched", "footprint_pillar_d0", "footprint_pillar_d1", "joint")


def same(a, b):
    return a.shape == b.shape and (a.size == 0 or float(np.abs(a - b).max()) == 0.0)


@torch.no_grad()
def joint_frame(model, pp, b, pts, pc_range, feats):
    """Y+ and all counterfactuals in one decode pass; then the same downstream stages."""
    t = {}
    ego = b["ego"]
    n = feats[0].shape[0]
    t1 = time.perf_counter()
    fused = [[fuse_scale(f[:n], None if m is None else m[k])[0] for k, f in enumerate(feats)]
             for m in [None] + [PL._exclude_masks(feats, n, [i]) for i in range(1, n)]]
    psm, rm = decode_batch(model, [torch.stack([fz[k] for fz in fused]) for k in range(len(feats))])
    t["joint_pass"] = time.perf_counter() - t1
    # downstream identical to mint_frame: reuse it with precomputed heads via footprint-free path
    t2 = time.perf_counter()
    cands = {frozenset(): PL._cands(pp, ego, psm[:1], rm[:1])}
    yp, sp = finalize(pp, cands[frozenset()])
    eff = []
    for j, i in enumerate(range(1, n), start=1):
        cands[frozenset([i])] = PL._cands(pp, ego, psm[j:j + 1], rm[j:j + 1])
        ym, sm = finalize(pp, cands[frozenset([i])])
        for e in PL.get_effects(yp, sp, ym, sm):
            eff.append({"sender": i, "type": e["type"], "plus": e["plus"], "minus": e["minus"],
                        "tile_plus": None if e["plus"] is None else PL.tile_of(e["plus"], pc_range, PL.TILE_M),
                        "tile_minus": None if e["minus"] is None else PL.tile_of(e["minus"], pc_range, PL.TILE_M)})
    t["post"] = time.perf_counter() - t2
    t3 = time.perf_counter()
    gm = np.zeros(len(pts), bool)
    for e in eff:
        e["rays_plus"] = PL.receiver_ray_record(pts, gm, e["plus"])
        e["rays_minus"] = PL.receiver_ray_record(pts, gm, e["minus"])
    rel = v0.assess(eff, v0.Params(theta=0.0))
    t["evidence"] = time.perf_counter() - t3
    t4 = time.perf_counter()
    ch = v0.gating_choice(rel)
    extra = 0
    for s in set(ch.values()) - set(cands):
        cands[s] = PL._cands(pp, ego, *PL._heads(model, feats, n, PL._exclude_masks(feats, n, s)))
        extra += 1
    if ch:
        yp, sp = finalize(pp, PL.compose(cands, ch))
    t["compose"] = time.perf_counter() - t4
    return {"boxes": yp, "cands": cands, "timing_s": t, "extra_decodes": extra}


@torch.no_grad()
def plain_only(model, pp, b, feats):
    t0 = time.perf_counter()
    n = feats[0].shape[0]
    finalize(pp, PL._cands(pp, b["ego"], *PL._heads(model, feats, n)))
    return time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "runs/20261023-E1/cost.json"))
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--threads", type=int, default=8)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    ds = build_dataset(dict(hyp, validate_dir=os.path.join(ROOT, "data/opv2v/devslice/validate")), visualize=False, train=False)
    pp = ds.post_processor
    pcr = hyp["preprocess"]["cav_lidar_range"]
    rec = {(n, m): [] for n in NS for m in MODES}
    exact = {(n, m): [] for n in NS for m in MODES}
    feat_nonzero = []
    fp_frac = {0: [], 1: []}
    for fi in range(min(args.frames, len(ds))):
        np.random.seed(frame_seed(SCEN, fi, 0))
        b = ds.collate_batch_test([ds[fi]])
        pts = np.asarray(E.cav_contents(ds, fi)[0][1]["lidar_np"][:, :3], np.float64)
        with torch.no_grad():
            if fi == 0:
                receiver_features(model, b["ego"])
            t0 = time.perf_counter()
            receiver_features(model, b["ego"])
            t_recv = time.perf_counter() - t0
            feats2, _ = agent_features(model, b["ego"])
        assert feats2[0].shape[0] == 2
        feat_nonzero.append([float((f[1].abs().sum(0) > 0).float().mean()) for f in feats2])
        fps = {d: PL.pillar_footprints(b["ego"], 2, dilate=d)[1] for d in (0, 1)}
        for d in (0, 1):
            fp_frac[d].append(float(fps[d].float().mean()))
        for n in NS:
            feats = [torch.cat([f] + [f[1:2]] * (n - 2)) for f in feats2]
            if fi == 0:                                    # warm-up per n (not recorded)
                PL.mint_frame(model, pp, b, pts, pcr, v0.Params(), feats=feats)
                joint_frame(model, pp, b, pts, pcr, feats)
            reps = {m: [] for m in MODES}
            for _rep in range(args.reps):
                t_plain = plain_only(model, pp, b, feats)
                base = t_recv + t_plain
                ref = None
                for m in MODES:
                    if m == "joint":
                        o = joint_frame(model, pp, b, pts, pcr, feats)
                        ex = o["timing_s"]["joint_pass"] + o["timing_s"]["post"] - t_plain + \
                            o["timing_s"]["evidence"] + o["timing_s"]["compose"]
                    else:
                        mode = "footprint" if m.startswith("footprint") else m
                        fpd = None if mode != "footprint" else {i: fps[int(m[-1])] for i in range(1, n)}
                        o = PL.mint_frame(model, pp, b, pts, pcr, v0.Params(theta=0.0), feats=feats,
                                          cf_mode=mode, footprints=fpd)
                        ex = o["timing_s"]["counterfactual"] + o["timing_s"]["evidence"] + o["timing_s"]["compose"]
                    reps[m].append({"baseline_s": base, "mint_extra_s": ex, "overhead": ex / base,
                                    "extra_decodes": o.get("extra_decodes", 0), **o["timing_s"]})
                    if m == "sequential":
                        ref = o
                    elif _rep == 0:
                        cf_ok = all(same(finalize(pp, o["cands"][frozenset([i])])[0],
                                         finalize(pp, ref["cands"][frozenset([i])])[0]) for i in range(1, n))
                        exact[(n, m)].append((bool(same(o["boxes"], ref["boxes"]) and cf_ok),
                                              bool(same(o["boxes"], ref["boxes"])), bool(cf_ok)))
            for m in MODES:
                r = reps[m]
                med = {k: float(np.median([x[k] for x in r])) for k in r[0]}
                med["frame"] = fi
                rec[(n, m)].append(med)
        print("frame", fi, {f"{n}/{m}": round(rec[(n, m)][-1]["overhead"], 3) for n in NS for m in ("sequential", "batched")},
              flush=True)

    out = {"note": "development block T, 24-frame slice of 2021_08_22_13_37_16; M1 CPU; per-frame median of reps; n > 2 replicates "
                   "sender 1's features (timing only); rule MINT-v0.0 theta=0; in-sample",
           "threads": args.threads, "reps": args.reps,
           "baseline": "receiver-only encode + plain fusion + decode + post-process (sender encoding excluded)",
           "D17_budget_p95": 0.10,
           "sender_feature_nonzero_pixel_fraction_by_scale_min": [round(min(x[k] for x in feat_nonzero), 4) for k in range(3)],
           "footprint_literal": "non-zero feature footprint = 100% of pixels at all scales on every frame -> identical to "
                                "sequential (no saving); not timed separately",
           "pillar_footprint_tile_fraction_mean": {f"d{d}": round(float(np.mean(v)), 3) for d, v in fp_frac.items()},
           "table": {}}
    for n in NS:
        row = {}
        for m in MODES:
            r = rec[(n, m)]
            ov = np.array([x["overhead"] for x in r])
            row[m] = {"overhead_p50": round(float(np.median(ov)), 3), "overhead_p95": round(float(np.percentile(ov, 95)), 3),
                      "baseline_s_p50": round(float(np.median([x["baseline_s"] for x in r])), 3),
                      "mint_extra_s_p50": round(float(np.median([x["mint_extra_s"] for x in r])), 3),
                      "frames_with_extra_decodes": int(sum(x["extra_decodes"] > 0 for x in r)),
                      "meets_D17_p95": bool(np.percentile(ov, 95) <= 0.10)}
            if m != "sequential":
                ex = exact[(n, m)]
                row[m]["exact_vs_sequential"] = f"{sum(x[0] for x in ex)}/{len(ex)}"
                row[m]["same_gated_output"] = f"{sum(x[1] for x in ex)}/{len(ex)}"
                row[m]["same_all_counterfactual_outputs"] = f"{sum(x[2] for x in ex)}/{len(ex)}"
        out["table"][str(n)] = row
    out["raw"] = {f"{n}/{m}": rec[(n, m)] for n in NS for m in MODES}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "raw"}, indent=1))


if __name__ == "__main__":
    main()
