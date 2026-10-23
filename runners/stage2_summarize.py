"""Summarise runs/<id> from stage2_validate.py into summary.json + summary.md.

Development data only. Effect labels are a GT approximation of D (contract §5):
  ADD   useful if added box matches GT (BEV IoU >= 0.5), harmful otherwise (added FP)
  REMOVE harmful if removed box matched GT (lost TP), useful otherwise (removed FP)
  SHIFT useful if GT IoU improves by > 0.1, harmful if it drops by > 0.1, else neutral
"""
import glob
import json
import os
import sys
import copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "third_party", "OpenCOOD"))
from mint.model import opencood_shims  # noqa: E402

opencood_shims.install()
import numpy as np  # noqa: E402
from opencood.utils import eval_utils  # noqa: E402

IOUS = (0.3, 0.5, 0.7)


def pooled_ap(stats):
    s = {k: {"tp": [], "fp": [], "gt": 0, "score": []} for k in IOUS}
    for st in stats:
        for k in IOUS:
            kk = str(k)
            for f in ("tp", "fp", "score"):
                s[k][f] += st[kk][f]
            s[k]["gt"] += st[kk]["gt"]
    return {f"AP@{k}": round(float(eval_utils.calculate_ap(copy.deepcopy(s), k, False)[0]), 4) for k in IOUS}


def label(e):
    if e["type"] == "ADD":
        return "useful" if e["gt_iou_plus"] >= 0.5 else "harmful"
    if e["type"] == "REMOVE":
        return "harmful" if e["gt_iou_minus"] >= 0.5 else "useful"
    d = e["gt_iou_plus"] - e["gt_iou_minus"]
    return "useful" if d > 0.1 else ("harmful" if d < -0.1 else "neutral")


SELF_RANGE_M = 1.5   # post-hoc proxy for runs made before the BEV self-box fix (OPV2V: vehicles only)


def is_self(c):
    return bool(c.get("self_box")) or c.get("range_m", 99.0) < SELF_RANGE_M


def nvis(c):
    return None if c is None or is_self(c) else c["SUP"] + c["TRAV"]


def effect_nvis(e):
    vals = [nvis(e["rays_plus"]) if e["rays_plus"] is not None else None,
            nvis(e["rays_minus"]) if e["rays_minus"] is not None else None]
    boxes = [v for v, c in zip(vals, (e["rays_plus"], e["rays_minus"])) if c is not None]
    if any(v is None for v in boxes):
        return None                                  # self box -> not applicable
    return min(boxes)


def support_ratio(c):
    n = nvis(c)
    return None if not n else c["SUP"] / n


def auroc(pos, neg):
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if pos.size == 0 or neg.size == 0:
        return None
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort() + 1.0
    # average ranks for ties
    for v in np.unique(allv):
        m = allv == v
        ranks[m] = ranks[m].mean()
    return float((ranks[:pos.size].sum() - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))


def main(run_dir):
    R = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(run_dir, "scenarios", "*.json")))]
    out = {"run_dir": os.path.relpath(run_dir, ROOT), "scenarios": [r["scenario"] for r in R],
           "frames": sum(r["frames_used"] for r in R)}
    # V-02
    out["V02_pooled_AP"] = {"opencood_proj_first": pooled_ap([r["stats"]["pf"] for r in R]),
                            "own_frame_plus_warp": pooled_ap([r["stats"]["own"] for r in R])}
    out["V02_per_scenario"] = {r["scenario"]: {"agents": r["agents"], "pf": r["ap_opencood_projfirst"],
                                               "ours_pf": r["ap_ours_projfirst"], "own": r["ap_own_frame_warp"]}
                               for r in R}
    # V-05
    msg = [m for r in R for m in r["message"]]
    out["V05_message"] = {"n_sender_frames": len(msg), "dense_MB_fp32": msg[0]["dense_MB_fp32"],
                          "dense_MB_fp16": msg[0]["dense_MB_fp16"],
                          "nonzero_pixel_frac_min": [min(m["nonzero_pixel_frac"][k] for m in msg) for k in range(3)]}
    # range-image no-return semantics
    ri = [x for r in R for x in r["range_images"]]
    fb = np.array([x["fill_by_ring"] for x in ri])
    el = np.array(ri[0]["ring_elev_deg"])
    out["RAY_range_image"] = {"samples": len(ri), "rings": int(fb.shape[1]),
                              "elev_deg": [float(el.min()), float(el.max())],
                              "fill_frac_rings_above_0deg": round(float(fb[:, el > 0].mean()), 3),
                              "fill_frac_rings_below_minus10deg": round(float(fb[:, el < -10].mean()), 3),
                              "slot_collisions_median": float(np.median([x["slot_collisions"] for x in ri]))}
    # genuine objects (GT boxes) seen by the receiver
    g = [x for r in R for x in r["gt_rays"]]
    gn = np.array([x["SUP"] + x["TRAV"] for x in g if not is_self(x)])
    gs = [x for x in g if not is_self(x) and x["SUP"] + x["TRAV"] >= 5]
    rr = np.array([x["range_m"] for x in gs])
    sr = np.array([x["SUP"] / (x["SUP"] + x["TRAV"]) for x in gs])
    bands = [(0, 20), (20, 40), (40, 70), (70, 200)]
    out["RAY_gt_objects"] = {
        "gt_boxes": len(g), "self_boxes": int(sum(is_self(x) for x in g)),
        "frac_nvis_ge3": round(float((gn >= 3).mean()), 3), "frac_nvis_ge5": round(float((gn >= 5).mean()), 3),
        "support_ratio_by_range": {f"{a}-{b}m": {"n": int(((rr >= a) & (rr < b)).sum()),
                                                  "median": None if not ((rr >= a) & (rr < b)).any() else round(float(np.median(sr[(rr >= a) & (rr < b)])), 3),
                                                  "p10": None if not ((rr >= a) & (rr < b)).any() else round(float(np.percentile(sr[(rr >= a) & (rr < b)], 10)), 3)}
                                   for a, b in bands}}
    # effects and coverage (gate S2-G)
    E = [dict(e, scen=r["scenario"]) for r in R for e in r["effects"]]
    for e in E:
        e["label"] = label(e)
        e["nvis"] = effect_nvis(e)
    units = {}
    for e in E:
        t = e["tile_plus"] if e["tile_plus"] is not None else e["tile_minus"]
        key = (e.get("scen", ""), e["frame"], e["sender"], tuple(t))
        units.setdefault(key, []).append(e)
    cov = {}
    for k in (3, 5):
        ok = [all(x["nvis"] is not None and x["nvis"] >= k for x in u) for u in units.values()]
        cov[f"units_all_effects_nvis_ge{k}"] = round(float(np.mean(ok)), 3) if ok else None
    by = {}
    for e in E:
        d = by.setdefault(f"{e['type']}/{e['label']}", {"n": 0, "self": 0, "nvis_ge3": 0})
        d["n"] += 1
        d["self"] += int(e["nvis"] is None)
        d["nvis_ge3"] += int(e["nvis"] is not None and e["nvis"] >= 3)
    out["EFF"] = {"effects": len(E), "effect_units": len(units), "coverage": cov, "by_type_label": by,
                  "cross_tile_effects": int(sum(1 for e in E if e["tile_plus"] is not None and e["tile_minus"] is not None
                                               and tuple(e["tile_plus"]) != tuple(e["tile_minus"])))}
    # development pilot: does receiver support separate harmful from useful effects (covered only)?
    pil = {}
    for typ, box_key in (("ADD", "rays_plus"), ("REMOVE", "rays_minus")):
        h = [support_ratio(e[box_key]) for e in E if e["type"] == typ and e["label"] == "harmful"
             and e["nvis"] is not None and e["nvis"] >= 3]
        u = [support_ratio(e[box_key]) for e in E if e["type"] == typ and e["label"] == "useful"
             and e["nvis"] is not None and e["nvis"] >= 3]
        # ADD: claim "object present" -> harmful should have LOW support; REMOVE: harmful should have HIGH support
        if typ == "ADD":
            a = auroc(u, h)
        else:
            a = auroc(h, u)
        pil[typ] = {"n_harmful": len(h), "n_useful": len(u), "auroc_support_ratio_pilot": None if a is None else round(a, 3),
                    "median_support_harmful": None if not h else round(float(np.median(h)), 3),
                    "median_support_useful": None if not u else round(float(np.median(u)), 3)}
    out["PILOT_dev_signal"] = pil
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(os.path.join(ROOT, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1])
