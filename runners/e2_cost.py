"""E2 Part A: where the time goes, exact faster post-processing, overhead vs n (development block T).

Frames: the 24-frame dev slice of 2021_08_22_13_37_16 (2 real agents; n > 2 replicates sender 1's
features, timing only). Rule: frozen R1. Pre-registration: runs/20261023-E2/preregistration.json.

  a1     sub-stage split (fusion, deblocks+heads, candidates, finalize, effects) of the plain path
         and of the counterfactual stage, n = 2, sequential and batched, OpenCOOD post-processing
  exact  FastPost vs OpenCOOD on every candidate set (Y+, each Y-(i), composed output), n = 2..5
  a3     D-38 overhead p50/p95 at n = 2..5, sequential and batched, --post opencood|fast (same
         implementation in baseline and MINT)

  python runners/e2_cost.py a1|exact|a3 [--post fast] [--out runs/20261023-E2/...]
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

from mint.model.attfuse_parts import agent_features, receiver_features  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402
from mint.reliability import pipeline as PL  # noqa: E402

SCEN = "2021_08_22_13_37_16"
OUT = os.path.join(ROOT, "runs/20261023-E2")
SUB = ("fusion", "deblocks_heads", "candidates", "finalize", "effects")


def posts():
    """Post-processing implementations; 'fast' exists only if the A2 trigger was met (it was not)."""
    class Lazy(dict):
        def __missing__(self, k):
            from mint.fusion import fastpost  # noqa: F401  (not implemented: A2 trigger not met)
            return fastpost.FastPost
    return Lazy(opencood=PL.OpenCOODPost)


def setup(threads):
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)

    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    model = train_utils.create_model(hyp)
    _, model = train_utils.load_saved_model(CKPT, model)
    model.eval()
    ds = build_dataset(dict(hyp, validate_dir=os.path.join(ROOT, "data/opv2v/devslice/validate")), visualize=False, train=False)
    return model, ds, ds.post_processor, hyp["preprocess"]["cav_lidar_range"]


def frame_inputs(model, ds, fi):
    np.random.seed(frame_seed(SCEN, fi, 0))
    b = ds.collate_batch_test([ds[fi]])
    pts = np.asarray(E.cav_contents(ds, fi)[0][1]["lidar_np"][:, :3], np.float64)
    with torch.no_grad():
        feats2, _ = agent_features(model, b["ego"])
    return b, pts, feats2


def recv_encode(model, b):
    with torch.no_grad():
        t0 = time.perf_counter()
        receiver_features(model, b["ego"])
        return time.perf_counter() - t0


def run(model, pp, b, pts, pcr, feats, mode, post, prof=PL.NOPROF):
    return PL.mint_frame(model, pp, b, pts, pcr, v0.Params(), feats=feats, rule=r1, cf_mode=mode, post=post, prof=prof)


def pq(x):
    x = np.asarray(x, float)
    return {"p50": round(float(np.median(x)), 4), "p95": round(float(np.percentile(x, 95)), 4)}


def part_a1(model, ds, pp, pcr, args):
    post = PL.OpenCOODPost
    modes = ("sequential", "batched")
    rec = {m: [] for m in modes}
    nbox = []
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats = frame_inputs(model, ds, fi)
        if fi == 0:
            recv_encode(model, b)
            for m in modes:
                run(model, pp, b, pts, pcr, feats, m, post)
        reps = {m: [] for m in modes}
        for _ in range(args.reps):
            tr = recv_encode(model, b)
            for m in modes:
                pr = PL.Prof()
                o = run(model, pp, b, pts, pcr, feats, m, post, pr)
                t = o["timing_s"]
                row = {"encode_receiver": tr, **{k: v for k, v in t.items()}, **pr.acc}
                for st in ("plain", "counterfactual"):
                    row[f"{st}.other"] = t[st] - sum(pr.acc.get(f"{st}.{k}", 0.0) for k in SUB)
                reps[m].append(row)
        n_c = {k: len(c.idx) for k, c in o["cands"].items()}
        nbox.append({"cands_plus": n_c[frozenset()], "cands_minus": n_c[frozenset([1])]})
        for m in modes:
            keys = set().union(*[r.keys() for r in reps[m]])
            rec[m].append({k: float(np.median([r.get(k, 0.0) for r in reps[m]])) for k in keys})
        print("frame", fi, {k: round(v, 4) for k, v in sorted(rec["sequential"][-1].items())}, flush=True)
    out = {"note": "E2 A1, development block T, 24-frame slice, n = 2, rule R1, OpenCOOD post-processing; per-frame median "
                   "of interleaved reps, then p50/p95 over frames; in-sample",
           "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads(), "reps": args.reps,
           "candidates_before_nms": {"plus": pq([x["cands_plus"] for x in nbox]), "minus": pq([x["cands_minus"] for x in nbox])}}
    for m in modes:
        R = rec[m]
        d = {}
        for st in ("plain", "counterfactual"):
            d[st] = {"total_s": pq([r[st] for r in R])}
            for k in SUB + ("other",):
                if st == "plain" and k == "effects":
                    continue
                d[st][k + "_s"] = pq([r.get(f"{st}.{k}", 0.0) for r in R])
        for k in ("encode_receiver", "evidence", "compose"):
            d[k + "_s"] = pq([r[k] for r in R])
        share = [(r.get("counterfactual.finalize", 0) + r.get("counterfactual.effects", 0)) / r["counterfactual"] for r in R]
        d["postprocessing_share_of_counterfactual"] = pq(share)
        d["finalize_share_of_plain"] = pq([r.get("plain.finalize", 0) / r["plain"] for r in R])
        base = [r["encode_receiver"] + r["plain"] for r in R]
        ex = [r["counterfactual"] + r["evidence"] + r["compose"] for r in R]
        d["overhead_D38"] = pq(np.array(ex) / np.array(base))
        out[m] = d
    sh = out["sequential"]["postprocessing_share_of_counterfactual"]["p50"]
    out["trigger_A2"] = {"share_p50_sequential": sh, "threshold": 0.40, "implement_fast_postprocessing": bool(sh >= 0.40)}
    out["raw"] = rec
    return out


def same(a, b):
    return a.shape == b.shape and (a.size == 0 or bool(np.array_equal(a, b)))


def same_effects(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x.keys() != y.keys():
            return False
        for k in x:
            u, v = x[k], y[k]
            if isinstance(u, np.ndarray) or isinstance(v, np.ndarray):
                if u is None or v is None or not same(np.asarray(u), np.asarray(v)):
                    return False
            elif u != v:
                return False
    return True


def part_exact(model, ds, pp, pcr, args):
    """FastPost vs OpenCOOD: nms keep indices, finalize outputs, effects, gated output."""
    from opencood.utils import box_utils
    from mint.fusion import fastpost
    from mint.fusion.compose import compose
    P = posts()
    res = []
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats2 = frame_inputs(model, ds, fi)
        ok = {}
        for n in (2, 3, 4, 5):
            feats = [torch.cat([f] + [f[1:2]] * (n - 2)) for f in feats2]
            for mode in ("sequential", "batched"):
                ref = run(model, pp, b, pts, pcr, feats, mode, P["opencood"])
                new = run(model, pp, b, pts, pcr, feats, mode, P["fast"])
                sets = list(ref["cands"].values()) + ([compose(ref["cands"], ref["choice"])] if ref["choice"] else [])
                nms_ok, fin_ok = True, True
                for c in sets:
                    box, sc = fastpost.prefilter(c)
                    k_ref = box_utils.nms_rotated(torch.from_numpy(box), torch.from_numpy(sc), pp.params["nms_thresh"])
                    k_new = fastpost.nms_rotated(box, sc, pp.params["nms_thresh"])
                    nms_ok &= k_ref.dtype == k_new.dtype and np.array_equal(k_ref, k_new)
                    a, bb = PL.OpenCOODPost.finalize(pp, c), fastpost.FastPost.finalize(pp, c)
                    fin_ok &= same(a[0], bb[0]) and same(a[1], bb[1])
                eff_ok = True
                yp, sp = PL.OpenCOODPost.finalize(pp, ref["cands"][frozenset()])
                for i in range(1, n):
                    ym, sm = PL.OpenCOODPost.finalize(pp, ref["cands"][frozenset([i])])
                    eff_ok &= same_effects(PL.OpenCOODPost.effects(yp, sp, ym, sm), fastpost.FastPost.effects(yp, sp, ym, sm))
                out_ok = same(ref["boxes"], new["boxes"]) and same(ref["scores"], new["scores"]) and \
                    ref["choice"] == new["choice"] and same_effects(
                        [{k: v for k, v in e.items() if not k.startswith("rays")} for e in ref["effects"]],
                        [{k: v for k, v in e.items() if not k.startswith("rays")} for e in new["effects"]])
                ok[f"{n}/{mode}"] = {"nms_keep": bool(nms_ok), "finalize": bool(fin_ok), "effects": bool(eff_ok),
                                     "pipeline_output": bool(out_ok), "n_sets": len(sets)}
        res.append({"frame": fi, **ok})
        print(fi, {k: all(v[x] for x in ("nms_keep", "finalize", "effects", "pipeline_output")) for k, v in ok.items()}, flush=True)
    keys = [k for k in res[0] if k != "frame"]
    summ = {k: {c: f"{sum(r[k][c] for r in res)}/{len(res)}" for c in ("nms_keep", "finalize", "effects", "pipeline_output")}
            for k in keys}
    allok = all(r[k][c] for r in res for k in keys for c in ("nms_keep", "finalize", "effects", "pipeline_output"))
    return {"note": "E2 A2 exactness of mint.fusion.fastpost vs OpenCOOD nms_rotated / compose.finalize / effects.effects; "
                    "24-frame dev slice, n = 2 real, n = 3..5 replicated; candidate sets = Y+, every Y-(i), composed gated output",
            "n2_criterion_24of24": all(r["2/sequential"][c] for r in res for c in ("nms_keep", "finalize", "effects", "pipeline_output")),
            "all_exact": bool(allok), "summary": summ, "raw": res}


@torch.no_grad()
def plain_only(model, pp, b, feats, post):
    """Baseline after the receiver encode: plain fusion + decode + candidates + finalize."""
    t0 = time.perf_counter()
    n = feats[0].shape[0]
    post.finalize(pp, PL._cands(pp, b["ego"], *PL._heads(model, feats, n)))
    return time.perf_counter() - t0


def part_a3(model, ds, pp, pcr, args):
    """Per repetition, in this order, each preceded by its own receiver encode (as a deployed receiver
    runs encode -> fusion -> ...): baseline-only (encode + plain_only), sequential MINT, batched MINT.
    Primary overhead = MINT extra / baseline-only time of the same repetition (shared by both modes;
    A1 showed that a mode's own `plain` is context-inflated in batched mode). Sensitivity: MINT extra /
    (isolated receiver encode p50 from encode_isolation_check.json + plain_only)."""
    post = posts()[args.post]
    iso = json.load(open(os.path.join(OUT, "encode_isolation_check.json")))["encode_receiver_s"]
    enc_iso = float(np.median([x["p50"] for v in iso.values() for x in v]))
    NS, modes = (2, 3, 4, 5), ("sequential", "batched")
    rec = {(n, m): [] for n in NS for m in modes}
    exact = {n: [] for n in NS}
    for fi in range(min(args.frames, len(ds))):
        b, pts, feats2 = frame_inputs(model, ds, fi)
        for n in NS:
            feats = [torch.cat([f] + [f[1:2]] * (n - 2)) for f in feats2]
            if fi == 0:
                recv_encode(model, b)
                plain_only(model, pp, b, feats, post)
                for m in modes:
                    run(model, pp, b, pts, pcr, feats, m, post)
            reps = {m: [] for m in modes}
            for rep in range(args.reps):
                tr0 = recv_encode(model, b)
                tp0 = plain_only(model, pp, b, feats, post)
                base = tr0 + tp0
                outs = {}
                for m in modes:
                    tr = recv_encode(model, b)
                    pr = PL.Prof()
                    o = run(model, pp, b, pts, pcr, feats, m, post, pr)
                    outs[m] = o
                    t = o["timing_s"]
                    ex = t["counterfactual"] + t["evidence"] + t["compose"]
                    fwd = pr.acc.get("counterfactual.fusion", 0) + pr.acc.get("counterfactual.deblocks_heads", 0)
                    post_t = pr.acc.get("counterfactual.finalize", 0) + pr.acc.get("counterfactual.effects", 0)
                    reps[m].append({"baseline_s": base, "encode_baseline_s": tr0, "plain_baseline_s": tp0,
                                    "mint_extra_s": ex, "overhead": ex / base,
                                    "overhead_own_run": ex / (tr + t["plain"]),
                                    "overhead_isolated_encode": ex / (enc_iso + tp0),
                                    "forward_share": fwd / base, "forward_share_isolated_encode": fwd / (enc_iso + tp0),
                                    "post_share": (post_t + t["compose"]) / base, "cf_forward_s": fwd, "cf_post_s": post_t,
                                    "extra_decodes": o["extra_decodes"], "encode_in_run_s": tr, **t})
                if rep == 0:
                    a, c = outs["sequential"], outs["batched"]
                    exact[n].append(bool(same(a["boxes"], c["boxes"]) and a["choice"] == c["choice"] and all(
                        same(post.finalize(pp, a["cands"][frozenset([i])])[0], post.finalize(pp, c["cands"][frozenset([i])])[0])
                        for i in range(1, n))))
            for m in modes:
                rec[(n, m)].append({k: float(np.median([x[k] for x in reps[m]])) for k in reps[m][0]})
        print("frame", fi, {f"{n}/{m[:3]}": round(rec[(n, m)][-1]["overhead"], 3) for n in NS for m in modes}, flush=True)
    out = {"note": f"E2 A3, development block T, 24-frame slice; post-processing = {args.post} in baseline AND MINT; rule R1; "
                   "D-38 accounting; per-frame median of interleaved reps; n > 2 replicates sender 1 (timing only); in-sample",
           "post": args.post, "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads(),
           "reps": args.reps, "D17_budget_p95": 0.10, "encode_isolated_p50_s": enc_iso,
           "baseline_definition": "per repetition: receiver-only encode + plain_only, timed in sequence just before the MINT runs; "
                                  "shared by both modes", "table": {}}
    for n in NS:
        row = {}
        for m in modes:
            r = rec[(n, m)]
            ov = [x["overhead"] for x in r]
            row[m] = {"overhead": pq(ov), "overhead_isolated_encode": pq([x["overhead_isolated_encode"] for x in r]),
                      "overhead_own_run": pq([x["overhead_own_run"] for x in r]),
                      "forward_share": pq([x["forward_share"] for x in r]),
                      "forward_share_isolated_encode": pq([x["forward_share_isolated_encode"] for x in r]),
                      "post_share": pq([x["post_share"] for x in r]),
                      "baseline_s": pq([x["baseline_s"] for x in r]), "encode_baseline_s": pq([x["encode_baseline_s"] for x in r]),
                      "plain_baseline_s": pq([x["plain_baseline_s"] for x in r]),
                      "mint_extra_s": pq([x["mint_extra_s"] for x in r]), "cf_forward_s": pq([x["cf_forward_s"] for x in r]),
                      "cf_post_s": pq([x["cf_post_s"] for x in r]), "evidence_s": pq([x["evidence"] for x in r]),
                      "compose_s": pq([x["compose"] for x in r]),
                      "frames_with_extra_decodes": int(sum(x["extra_decodes"] > 0 for x in r)),
                      "meets_D17_p95": bool(np.percentile(ov, 95) <= 0.10)}
        row["batched_exact_vs_sequential"] = f"{sum(exact[n])}/{len(exact[n])}"
        out["table"][str(n)] = row
    t2 = out["table"]["2"]
    best = min(("sequential", "batched"), key=lambda m: t2[m]["overhead"]["p95"])
    v = t2[best]["overhead"]["p95"]
    out["outcome"] = {"n2_best_mode": best, "n2_overhead_p95": v,
                      "band": "<=10%" if v <= 0.10 else ("10-25%" if v <= 0.25 else ">25%"),
                      "n2_overhead_p95_isolated_encode": t2[best]["overhead_isolated_encode"]["p95"],
                      "n2_forward_share_floor": t2[best]["forward_share"],
                      "n2_forward_share_floor_isolated_encode": t2[best]["forward_share_isolated_encode"]}
    out["raw"] = {f"{n}/{m}": rec[(n, m)] for n in NS for m in modes}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=("a1", "exact", "a3"))
    ap.add_argument("--post", default="opencood", choices=("opencood", "fast"))
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    args.reps = args.reps or {"a1": 5, "a3": 3, "exact": 1}[args.part]
    model, ds, pp, pcr = setup(args.threads)
    out = {"a1": part_a1, "exact": part_exact, "a3": part_a3}[args.part](model, ds, pp, pcr, args)
    name = args.out or os.path.join(OUT, {"a1": "a1_substages.json", "exact": "a2_exactness.json",
                                          "a3": f"a3_overhead_{args.post}.json"}[args.part])
    os.makedirs(os.path.dirname(name), exist_ok=True)
    json.dump(out, open(name, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "raw"}, indent=1, default=str))


if __name__ == "__main__":
    main()
