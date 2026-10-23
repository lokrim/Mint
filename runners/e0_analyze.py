"""E0 analysis (offline, uses GT): Stage-2 geometry verification, clean effects, attack realization,
oracle and visibility-limited-oracle headroom. Pre-registration: runs/20261023-E0/preregistration.json.

  python runners/e0_analyze.py runs/20261023-E0 [--glob '*.pkl.gz'] [--boot 200]
"""
import argparse
import copy
import glob
import gzip
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "third_party", "OpenCOOD"))
from mint.model import opencood_shims  # noqa: E402

opencood_shims.install()
import numpy as np  # noqa: E402
import torch  # noqa: E402
from opencood.utils import eval_utils  # noqa: E402
import opencood.hypes_yaml.yaml_utils as yaml_utils  # noqa: E402
from opencood.data_utils.post_processor import build_postprocessor  # noqa: E402

from mint.fusion.compose import compose, finalize  # noqa: E402
from mint.eval.harm_labels import harm_D  # noqa: E402
from mint.effects.effects import bev_iou_matrix  # noqa: E402

IOUS = (0.3, 0.5, 0.7)
FAMILIES = ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts")
CKPT = os.path.join(ROOT, "data/opv2v/ckpt/pointpillar_attentive_fusion/pointpillar_attentive_fusion")
M = 0.5
BANDS = [(0, 20), (20, 40), (40, 70), (70, 300)]


def post_processor():
    class Opt:
        model_dir = CKPT
    hyp = yaml_utils.load_yaml(None, Opt)
    return build_postprocessor(hyp["postprocess"], train=False)


def empty_stat():
    return {k: {"tp": [], "fp": [], "gt": 0, "score": []} for k in IOUS}


def frame_stat(boxes, scores, gt):
    st = empty_stat()
    det = None if len(boxes) == 0 else torch.from_numpy(np.asarray(boxes, np.float32))
    sc = None if len(boxes) == 0 else torch.from_numpy(np.asarray(scores, np.float32))
    g = torch.from_numpy(np.asarray(gt, np.float32))
    for k in IOUS:
        eval_utils.caluclate_tp_fp(det, sc, g, st, k)
    return st


def merge(stats):
    s = empty_stat()
    for st in stats:
        for k in IOUS:
            for f in ("tp", "fp", "score"):
                s[k][f] += list(st[k][f])
            s[k]["gt"] += st[k]["gt"]
    return s


def ap(stat):
    return {k: float(eval_utils.calculate_ap(copy.deepcopy(stat), k, False)[0]) for k in IOUS}


def auroc(pos, neg):
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if pos.size == 0 or neg.size == 0:
        return None
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort() + 1.0
    for v in np.unique(allv):
        m = allv == v
        ranks[m] = ranks[m].mean()
    return float((ranks[:pos.size].sum() - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))


def nvis(r):
    return None if r is None or r["self_box"] else r["std"]["SUP"] + r["std"]["TRAV"]


def sratio(r, variant):
    n = nvis(r)
    return None if not n else r[variant]["SUP"] / n


def effect_known(e, k=3):
    for r in (e["rays_plus"], e["rays_minus"]):
        if r is not None and (r["self_box"] or nvis(r) < k):
            return False
    return True


def units_of(effects):
    """{(sender, tile): [effects]}; an effect belongs to its tile in either version (D-22)."""
    u = {}
    for e in effects:
        ts = {tuple(t) for t in (e["tile_plus"], e["tile_minus"]) if t is not None}
        for t in ts:
            u.setdefault((e["sender"], t), []).append(e)
    return u


def cond_of(fr, fam):
    c = fr["conditions"].get(fam)
    if c is None or "cands" not in c:
        return fr["conditions"]["clean"], False
    return c, True


def tiles_differing(ya, yb):
    """Tiles whose set of box centres (to 1 cm) differs between two outputs."""
    from mint.eval.harm_labels import tiles_of
    def key(y):
        d = {}
        for t, b in zip(map(tuple, tiles_of(y)), y):
            d.setdefault(t, set()).add(tuple(np.round(np.asarray(b).mean(0), 2)))
        return d
    ka, kb = key(ya), key(yb)
    return {t for t in set(ka) | set(kb) if ka.get(t) != kb.get(t)}


def frame_policies(pp, fr, fam, n):
    """Return {policy: (boxes, scores)} plus unit records for one frame and condition."""
    c, applied = cond_of(fr, fam)
    cands, gt = c["cands"], fr["gt"]
    yp, sp = finalize(pp, cands[frozenset()])
    units = units_of(c["effects"])
    D = {}
    for i in range(1, n):
        ym, _ = finalize(pp, cands[frozenset([i])])
        for t, d in harm_D(yp, ym, gt).items():
            D[(i, t)] = d
    recs = []
    for key in set(D) | set(units):
        d = D.get(key, 0.0)
        effs = units.get(key, [])
        recs.append({"sender": key[0], "tile": key[1], "D": d, "n_eff": len(effs),
                     "known": bool(effs) and all(effect_known(e) for e in effs)})
    touched = set()
    if fam != "clean" and applied:
        yc, _ = finalize(pp, fr["conditions"]["clean"]["cands"][frozenset()])
        touched = tiles_differing(yc, yp)
    for r in recs:
        r["touched"] = r["tile"] in touched
    out = {"undefended": (yp, sp)}
    for name, pred in (("oracle_all", lambda r: True), ("oracle_attacker", lambda r: r["sender"] == 1),
                       ("vis_oracle_all", lambda r: r["known"]),
                       ("vis_oracle_attacker", lambda r: r["known"] and r["sender"] == 1),
                       ("oracle_touched", lambda r: r["sender"] == 1 and r["touched"]),
                       ("vis_oracle_touched", lambda r: r["known"] and r["sender"] == 1 and r["touched"])):
        choice = {}
        for r in recs:
            if r["D"] > M and pred(r):
                choice.setdefault(r["tile"], set()).add(r["sender"])
        choice = {t: frozenset(s) for t, s in choice.items()}
        out[name] = finalize(pp, compose(cands, choice)) if choice else (yp, sp)
    return out, recs, applied, c


def realization(pp, fr, fam, c_att, applied):
    if not applied:
        return {"applied": False}
    led, gt = c_att["ledger"], fr["gt"]
    out = {"applied": True}
    if fam in ("spoof_feat", "spoof_pts"):
        dx, dy = led["dst_center"]
        hits = [e for e in c_att["effects"] if e["sender"] == 1 and e["type"] in ("ADD", "SHIFT") and e["plus"] is not None
                and np.hypot(*(np.asarray(e["plus"]).mean(0)[:2] - [dx, dy])) < 3.0]
        out["realized"] = bool(hits)
        out["dst_receiver_rays"] = None if not hits else nvis(hits[0]["rays_plus"])
    else:
        j = led["target_gt"]
        yc, _ = finalize(pp, fr["conditions"]["clean"]["cands"][frozenset()])
        ya, _ = finalize(pp, c_att["cands"][frozenset()])
        det = lambda y: len(y) > 0 and float(bev_iou_matrix(gt[j][None], y).max()) >= 0.5
        out["target_detected_clean"] = bool(det(yc))
        out["realized"] = bool(det(yc) and not det(ya))
    return out


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("run_dir")
    ap_.add_argument("--glob", default="20*_[0-9][0-9].pkl.gz")
    ap_.add_argument("--boot", type=int, default=200)
    a = ap_.parse_args()
    run_dir = a.run_dir if os.path.isabs(a.run_dir) else os.path.join(ROOT, a.run_dir)
    files = sorted(glob.glob(os.path.join(run_dir, "cache", a.glob)))
    pp = post_processor()
    S = {}
    geo = {"self": [], "rings": [], "gt": [], "null": [], "ground_frac": [], "gt_ground_pts": []}
    clean_effects, unit_recs = [], {f: [] for f in ("clean",) + FAMILIES}
    stats = {}          # (fam, policy) -> list of (scen, frame, stat)
    real = {f: [] for f in FAMILIES}
    files_gt = {}
    for fpath in files:
        R = pickle.load(gzip.open(fpath))
        scen = R["scenario"]
        for fr in R["frames"]:
            files_gt[(scen, fr["frame"])] = fr["gt"]
        S[scen] = {"frames": len(R["frames"]), "compose_checks": len(R["compose_checks"]),
                   "compose_all_identical": all(c["same_candidates"] and c["same_final"] for c in R["compose_checks"])}
        for fr in R["frames"]:
            n = fr["n_agents"]
            geo["self"].append(fr["self_gt"])
            if "range_image" in fr:
                geo["rings"].append(fr["range_image"]["rings"])
            geo["ground_frac"].append(fr["ground_frac"])
            geo["gt"] += [g for g in fr["gt_rays"]]
            geo["null"] += fr["null_rays"]
            # ground classifier sanity: fraction of points inside GT box cores flagged as ground
            if fr["frame"] % 10 == 0 and len(fr["gt"]):
                from mint.attacks.patches import points_in_box
                pts = fr["ego_pts"].astype(np.float64)
                gm = np.unpackbits(fr["ground_mask"])[:len(pts)].astype(bool)
                for g in fr["gt"]:
                    if np.linalg.norm(g.mean(0)[:2]) < 2.5:
                        continue
                    inb = points_in_box(pts, g, pad=0.0)
                    zb = g[:, 2].min()
                    upper = inb & (pts[:, 2] > zb + 0.3)
                    if upper.sum() >= 5:
                        geo["gt_ground_pts"].append(float(gm[upper].mean()))
            for fam in ("clean",) + FAMILIES:
                if fam != "clean" and n < 2:
                    pol, recs, applied, c = frame_policies(pp, fr, "clean", n)
                else:
                    pol, recs, applied, c = frame_policies(pp, fr, fam, n)
                for r in recs:
                    unit_recs[fam].append(dict(r, scen=scen, frame=fr["frame"], applied=applied))
                for name, (b, s) in pol.items():
                    stats.setdefault((fam, name), []).append((scen, fr["frame"], frame_stat(b, s, fr["gt"])))
                if fam == "clean":
                    for e in c["effects"]:
                        clean_effects.append(dict(e, scen=scen, frame=fr["frame"]))
                elif n >= 2:
                    real[fam].append(realization(pp, fr, fam, c, applied))
        print("loaded", scen, flush=True)

    out = {"scenarios": S, "files": [os.path.basename(f) for f in files]}
    # ---- geometry ----
    sg = geo["self"]
    out["D24_self_box"] = {"frames": len(sg), "frames_exactly_one_self_gt": sum(x["n"] == 1 for x in sg),
                           "frames_zero": sum(x["n"] == 0 for x in sg), "frames_multiple": sum(x["n"] > 1 for x in sg),
                           "self_centre_dist_max": max([d for x in sg for d in x["centre_dist"]] or [None]),
                           "frames_proxy_disagrees": sum(x["n"] != x["proxy_n"] for x in sg)}
    out["range_image"] = {"samples": len(geo["rings"]), "rings_values": sorted(set(geo["rings"]))}
    out["ground_classifier"] = {"ground_frac_median": round(float(np.median(geo["ground_frac"])), 3),
                                "gt_box_upper_points_flagged_ground_mean": round(float(np.mean(geo["gt_ground_pts"])), 4)
                                if geo["gt_ground_pts"] else None, "n_boxes": len(geo["gt_ground_pts"])}

    def by_range(recs, variant):
        res = {}
        for lo, hi in BANDS:
            v = [sratio(r, variant) for r in recs if nvis(r) is not None and nvis(r) >= 3 and lo <= r["range_m"] < hi]
            v = [x for x in v if x is not None]
            res[f"{lo}-{hi}m"] = {"n": len(v), "median": None if not v else round(float(np.median(v)), 3),
                                  "p90": None if not v else round(float(np.percentile(v, 90)), 3),
                                  "p10": None if not v else round(float(np.percentile(v, 10)), 3)}
        return res
    gtr = [r for r in geo["gt"] if not r["self_box"]]
    out["ray_gt_objects"] = {"n": len(gtr), "frac_nvis_ge3": round(float(np.mean([nvis(r) >= 3 for r in gtr])), 3),
                             "std": by_range(gtr, "std"), "gnd": by_range(gtr, "gnd")}
    out["ray_null_boxes"] = {"n": len(geo["null"]), "frac_nvis_ge3": round(float(np.mean([nvis(r) >= 3 for r in geo["null"]])), 3),
                             "z_source": {s: sum(r["z_source"] == s for r in geo["null"]) for s in {r["z_source"] for r in geo["null"]}},
                             "std": by_range(geo["null"], "std"), "gnd": by_range(geo["null"], "gnd")}
    au = {}
    for v in ("std", "gnd"):
        pos = [sratio(r, v) for r in gtr if nvis(r) is not None and nvis(r) >= 3]
        neg = [sratio(r, v) for r in geo["null"] if nvis(r) is not None and nvis(r) >= 3]
        au[v] = auroc(pos, neg)
        for lo, hi in BANDS:
            p = [sratio(r, v) for r in gtr if nvis(r) is not None and nvis(r) >= 3 and lo <= r["range_m"] < hi]
            q = [sratio(r, v) for r in geo["null"] if nvis(r) is not None and nvis(r) >= 3 and lo <= r["range_m"] < hi]
            au[f"{v}_{lo}-{hi}m"] = auroc(p, q)
    out["auroc_gt_vs_null"] = {k: None if x is None else round(x, 3) for k, x in au.items()}
    null_med = [out["ray_null_boxes"]["std"][f"{lo}-{hi}m"]["median"] for lo, hi in BANDS[:3]]
    req = any(m is not None and m > 0.20 for m in null_med) or (au["gnd"] is not None and au["std"] is not None
                                                               and au["gnd"] - au["std"] >= 0.05)
    out["ground_estimate_required"] = {"decision": bool(req), "null_std_median_by_band": null_med,
                                       "auroc_gain": None if au["gnd"] is None else round(au["gnd"] - au["std"], 3)}
    variant = "gnd" if req else "std"

    # ---- clean effects (per-effect Stage-2 labels and unit labels) ----
    E = clean_effects
    by = {}
    for e in E:
        k = e["type"]
        d = by.setdefault(k, {"n": 0, "self": 0, "known": 0})
        d["n"] += 1
        d["self"] += int(any(r is not None and r["self_box"] for r in (e["rays_plus"], e["rays_minus"])))
        d["known"] += int(effect_known(e))
    U = unit_recs["clean"]
    lab = lambda d: "HARMFUL" if d > M else ("USEFUL" if d < -M else "NEUTRAL")
    out["clean_effects"] = {"effects": len(E), "by_type": by, "units": len(U),
                            "unit_labels": {l: sum(lab(r["D"]) == l for r in U) for l in ("HARMFUL", "USEFUL", "NEUTRAL")},
                            "units_known_frac": round(float(np.mean([r["known"] for r in U])), 3) if U else None,
                            "harmful_units_known": sum(lab(r["D"]) == "HARMFUL" and r["known"] for r in U),
                            "useful_units_known": sum(lab(r["D"]) == "USEFUL" and r["known"] for r in U),
                            "units_with_D_but_no_effect": sum(r["n_eff"] == 0 and r["D"] != 0 for r in U)}

    # raw support separation on clean effects (re-measured with the BEV self rule; development, in-sample)
    def gt_iou(box, gt):
        return 0.0 if box is None or len(gt) == 0 else float(bev_iou_matrix(np.asarray(box)[None], gt).max())
    pil = {}
    for typ, key in (("ADD", "rays_plus"), ("REMOVE", "rays_minus")):
        for v in ("std", "gnd"):
            h, u = [], []
            for e in E:
                if e["type"] != typ or not effect_known(e):
                    continue
                gt = files_gt[(e["scen"], e["frame"])]
                real_obj = gt_iou(e["plus"] if typ == "ADD" else e["minus"], gt) >= 0.5
                harmful = (not real_obj) if typ == "ADD" else real_obj
                (h if harmful else u).append(sratio(e[key], v))
            a_ = auroc(u, h) if typ == "ADD" else auroc(h, u)
            pil[f"{typ}_{v}"] = {"n_harmful": len(h), "n_useful": len(u), "auroc": None if a_ is None else round(a_, 3),
                                 "median_harmful": None if not h else round(float(np.median(h)), 3),
                                 "median_useful": None if not u else round(float(np.median(u)), 3)}
    out["clean_support_separation_dev"] = pil

    # ---- attacks: realization ----
    rz = {}
    for fam in FAMILIES:
        rr = real[fam]
        app = [r for r in rr if r["applied"]]
        d = {"frames_with_sender": len(rr), "applied": len(app)}
        d["realized"] = sum(r["realized"] for r in app)
        if fam in ("remove_feat", "shift_feat"):
            d["target_detected_clean"] = sum(r["target_detected_clean"] for r in app)
        if fam in ("spoof_feat", "spoof_pts"):
            vis = [r["dst_receiver_rays"] for r in app if r["realized"]]
            d["realized_at_receiver_visible_dst(>=3 rays)"] = sum(v is not None and v >= 3 for v in vis)
        rz[fam] = d
    out["attack_realization"] = rz

    # ---- E0: AP, attack loss, oracle headroom, recovery ----
    def ap_of(fam, pol, idx=None):
        L = stats[(fam, pol)]
        st = [x[2] for x in L] if idx is None else [L[j][2] for j in idx]
        return ap(merge(st))
    keys = [(x[0], x[1]) for x in stats[("clean", "undefended")]]
    res = {}
    clean_ap = ap_of("clean", "undefended")
    res["clean"] = {p: ap_of("clean", p) for p in ("undefended", "oracle_all", "vis_oracle_all")}
    for fam in FAMILIES:
        r = {p: ap_of(fam, p) for p in ("undefended", "oracle_all", "oracle_attacker", "vis_oracle_all", "vis_oracle_attacker",
                                        "oracle_touched", "vis_oracle_touched")}
        loss = {k: clean_ap[k] - r["undefended"][k] for k in IOUS}
        rec = {}
        for p in ("oracle_all", "oracle_attacker", "vis_oracle_all", "vis_oracle_attacker", "oracle_touched", "vis_oracle_touched"):
            rec[p] = {k: (None if loss[k] < 0.005 else round((r[p][k] - r["undefended"][k]) / loss[k], 3)) for k in IOUS}
        res[fam] = {"AP": {p: {str(k): round(v, 4) for k, v in x.items()} for p, x in r.items()},
                    "attack_loss": {str(k): round(v, 4) for k, v in loss.items()}, "recovery": rec}
    res["clean"] = {p: {str(k): round(v, 4) for k, v in x.items()} for p, x in res["clean"].items()}
    out["E0"] = res

    # attacker units: how many harmful ones are receiver-visible?
    au_ = {}
    for fam in FAMILIES:
        U = [r for r in unit_recs[fam] if r["applied"] and r["sender"] == 1]
        hu = [r for r in U if r["D"] > M]
        ht = [r for r in hu if r["touched"]]
        au_[fam] = {"attacker_units": len(U), "attacker_harmful": len(hu),
                    "attacker_harmful_known": sum(r["known"] for r in hu),
                    "attacker_harmful_touched": len(ht), "attacker_harmful_touched_known": sum(r["known"] for r in ht)}
    out["attacker_unit_visibility"] = au_

    # primary decision (pre-registered)
    vals = [res[f]["recovery"]["vis_oracle_attacker"][0.7] for f in FAMILIES]
    used = [v for v in vals if v is not None]
    prim = None if not used else float(np.mean(used))

    # block bootstrap (10-frame blocks within scenario) for the primary quantity
    rng = np.random.default_rng(0)
    blocks = {}
    for j, (s, f) in enumerate(keys):
        blocks.setdefault((s, f // 10), []).append(j)
    bl = list(blocks.values())
    boot = []
    for _ in range(a.boot):
        pick = [bl[k] for k in rng.integers(0, len(bl), len(bl))]
        idx = [j for b in pick for j in b]
        c = ap_of("clean", "undefended", idx)[0.7]
        rv = []
        for fam in FAMILIES:
            u_ = ap_of(fam, "undefended", idx)[0.7]
            v_ = ap_of(fam, "vis_oracle_attacker", idx)[0.7]
            if c - u_ >= 0.005:
                rv.append((v_ - u_) / (c - u_))
        if rv:
            boot.append(float(np.mean(rv)))
    sec = [res[f]["recovery"]["vis_oracle_touched"][0.7] for f in FAMILIES]
    out["secondary_attack_touched"] = {"metric": "vis_oracle_touched recovery at AP@0.7 (not pre-registered; gates only "
                                       "attacker tiles whose output the attack changed)",
                                       "per_family": dict(zip(FAMILIES, sec)),
                                       "mean": None if not [v for v in sec if v is not None] else
                                       round(float(np.mean([v for v in sec if v is not None])), 3)}
    out["primary_decision"] = {"metric": "mean over families of vis_oracle_attacker recovery at AP@0.7",
                               "per_family": dict(zip(FAMILIES, vals)), "value": None if prim is None else round(prim, 3),
                               "block_bootstrap_95": None if not boot else [round(float(np.percentile(boot, 2.5)), 3),
                                                                             round(float(np.percentile(boot, 97.5)), 3)],
                               "threshold": 0.30, "proceed": None if prim is None else bool(prim >= 0.30),
                               "variant_for_mint": variant}
    with open(os.path.join(run_dir, "e0_summary.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
