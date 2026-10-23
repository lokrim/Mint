"""E2 Parts B and C from the E0 caches (development block T; in-sample; R1 frozen; no new data).

Part B: AP@0.7 of undefended and R1 per condition, absolute deltas, and paired bootstrap 95% CIs
(scenario blocks; contiguous 10-frame blocks within scenarios) for recovery, mean recovery, clean
relative loss and the deltas.
Part C: the USEFUL units that R1 gates through a REMOVE effect (false rejections): descriptive
record, BEV plot and pre-registered rule-based class per case.

AP is OpenCOOD's with global_sort_detections=False (as E0/E1), which depends on frame order; a
bootstrap resample concatenates its frames in their original (scenario, frame) order, so the
point estimate equals E1's. Pre-registration: runs/20261023-E2/preregistration.json.

  python runners/e2_rules.py runs/20261023-E0 --out runs/20261023-E2
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
import e0_analyze as A  # noqa: E402  (installs shims, paths)

import numpy as np  # noqa: E402
import shapely  # noqa: E402
from mint.effects.effects import bev_iou_matrix  # noqa: E402
from mint.fusion.compose import compose, finalize  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402

IOU = 0.7
POL = ("undefended", "R1")
BLOCK = 10
N_BOOT = 2000


# ---------------------------------------------------------------- AP (numpy mirror of OpenCOOD)
def frame_tpfp(st):
    s = st[IOU]
    return np.asarray(s["tp"], np.int64), np.asarray(s["fp"], np.int64), int(s["gt"])


def ap_from(parts):
    """OpenCOOD calculate_ap(global_sort_detections=False) + voc_ap on concatenated frames."""
    tp = np.concatenate([p[0] for p in parts]) if parts else np.zeros(0, np.int64)
    fp = np.concatenate([p[1] for p in parts]) if parts else np.zeros(0, np.int64)
    gt = sum(p[2] for p in parts)
    ctp, cfp = np.cumsum(tp), np.cumsum(fp)
    rec = np.concatenate([[0.0], ctp / gt, [1.0]])
    prec = np.concatenate([[0.0], ctp / (ctp + cfp), [0.0]])
    prec = np.maximum.accumulate(prec[::-1])[::-1]
    i = np.nonzero(rec[1:] != rec[:-1])[0] + 1
    return float(np.sum((rec[i] - rec[i - 1]) * prec[i]))


def metrics(F, idx, conds):
    """F[(cond, pol)] = list of per-frame (tp, fp, gt); idx = frame indices in original order."""
    ap = {k: ap_from([F[k][j] for j in idx]) for k in F}
    out = {}
    clean = ap[("clean", "undefended")]
    out["clean_rel_loss"] = 1 - ap[("clean", "R1")] / clean
    rec = []
    for c in conds:
        out[f"delta_{c}"] = ap[(c, "R1")] - ap[(c, "undefended")]
        if c == "clean":
            continue
        loss = clean - ap[(c, "undefended")]
        r = None if loss < 0.005 else (ap[(c, "R1")] - ap[(c, "undefended")]) / loss
        out[f"recovery_{c}"] = r
        rec.append(r)
    out["mean_recovery"] = None if any(r is None for r in rec) else float(np.mean(rec))
    return out, ap


def bootstrap(F, frames, conds, kind, seed=0):
    """frames: list of (scen, frame) in original order. Returns {metric: (lo, hi, n_valid)}."""
    scen = sorted({s for s, _ in frames}, key=lambda s: [f[0] for f in frames].index(s))
    pos = {s: [j for j, f in enumerate(frames) if f[0] == s] for s in scen}
    if kind == "scenario":
        units = [pos[s] for s in scen]
        strata = [list(range(len(units)))]
    else:
        units, strata = [], []
        for s in scen:
            p = pos[s]
            first = len(units)
            units += [p[k:k + BLOCK] for k in range(0, len(p), BLOCK)]
            strata.append(list(range(first, len(units))))
    rng = np.random.default_rng(seed)
    vals = {}
    for _ in range(N_BOOT):
        pick = []
        for st in strata:
            pick += list(rng.choice(st, len(st)))
        idx = sorted(j for u in pick for j in units[u])      # original order, duplicates adjacent
        m, _ = metrics(F, idx, conds)
        for k, v in m.items():
            vals.setdefault(k, []).append(v)
    out = {}
    for k, v in vals.items():
        ok = [x for x in v if x is not None]
        lo, hi = (None, None) if not ok else (float(np.percentile(ok, 2.5)), float(np.percentile(ok, 97.5)))
        out[k] = {"ci95": None if lo is None else [round(lo, 4), round(hi, 4)], "dropped": len(v) - len(ok),
                  "excludes_0": None if lo is None else bool(lo > 0 or hi < 0)}
    out["_blocks"] = len(units)
    return out


# ---------------------------------------------------------------- Part C
def in_poly(pts, box):
    return shapely.contains_xy(shapely.Polygon(np.asarray(box)[:4, :2]), pts[:, 0], pts[:, 1])


def principal_extent(xy):
    if len(xy) < 3:
        return None, None
    c = xy - xy.mean(0)
    _, vec = np.linalg.eigh(np.cov(c.T))
    p = c @ vec
    ext = p.max(0) - p.min(0)
    return float(ext[1]), float(ext[0])         # length (major), width (minor)


def classify(c):
    if c["gt_max_iou"] >= 0.1:
        return "label/IoU artefact"
    if (c["gt_nearest_centre_m"] is not None and c["gt_nearest_centre_m"] < 2.0) or c["pts_in_box"] < 10:
        return "unclear"
    if c["pts_nonground"] >= 10 and c["z_extent_nonground_m"] is not None and c["z_extent_nonground_m"] >= 0.5:
        return "receiver FP on unlabelled structure"
    return "genuine R1 error"


def case_record(pp, fr, c, i, tile, D, e, cache_ro):
    box = np.asarray(e["minus"])
    ctr = box.mean(0)
    gt = np.asarray(fr["gt"])
    r = e["rays_minus"]["std"]
    k, nn = r["SUP"], r["SUP"] + r["TRAV"]
    lo, hi = r1.wilson(k, nn)
    ro_b, ro_s = cache_ro
    if len(ro_b):
        iou = bev_iou_matrix(box[None], ro_b)[0]
        j = int(iou.argmax())
        ro = {"receiver_only_score": None if iou[j] < 0.1 else round(float(ro_s[j]), 3),
              "receiver_only_match_iou": round(float(iou[j]), 3)}
    else:
        ro = {"receiver_only_score": None, "receiver_only_match_iou": 0.0}
    if len(gt):
        gi = bev_iou_matrix(box[None], gt)[0]
        gd = np.linalg.norm(gt.mean(1)[:, :2] - ctr[:2], axis=1)
        gtr = {"gt_max_iou": round(float(gi.max()), 3), "gt_nearest_centre_m": round(float(gd.min()), 2)}
    else:
        gtr = {"gt_max_iou": 0.0, "gt_nearest_centre_m": None}
    pts = np.asarray(fr["ego_pts"])
    m = in_poly(pts, box)
    zb, zt = float(box[:, 2].min()), float(box[:, 2].max())
    p = pts[m]
    ng = p[p[:, 2] > zb + 0.3]
    zr = (p[:, 2] - zb) if len(p) else np.zeros(0)
    L, W = principal_extent(ng[:, :2]) if len(ng) else (None, None)
    rec = {"tile": list(tile), "sender": i, "D": round(float(D), 3), "range_m": round(float(np.linalg.norm(ctr[:2])), 2),
           "SUP": k, "TRAV": r["TRAV"], "OCC": r["OCC"], "s_minus": round(k / nn, 3) if nn else None,
           "wilson95": [round(lo, 3), round(hi, 3)], "score_minus": None if e.get("score_minus") is None else round(float(e["score_minus"]), 3),
           **ro, **gtr, "box_z_bottom_m": round(zb, 2), "box_height_m": round(zt - zb, 2),
           "box_bev_lw_m": [round(float(np.linalg.norm(box[0, :2] - box[1, :2])), 2), round(float(np.linalg.norm(box[1, :2] - box[2, :2])), 2)],
           "pts_in_box": int(m.sum()), "pts_nonground": int(len(ng)),
           "z_rel_bottom_p5_p50_p95": None if not len(zr) else [round(float(np.percentile(zr, q)), 2) for q in (5, 50, 95)],
           "z_extent_nonground_m": None if len(ng) < 2 else round(float(np.percentile(ng[:, 2], 95) - np.percentile(ng[:, 2], 5)), 2),
           "nonground_extent_lw_m": None if L is None else [round(L, 2), round(W, 2)]}
    # descriptive extras (not used by the pre-registered class)
    poly = shapely.Polygon(box[:4, :2])
    me = shapely.contains_xy(poly.buffer(0.2), pts[:, 0], pts[:, 1])
    pe = pts[me]
    rec["pts_in_envelope_0.2m"] = int(me.sum())
    rec["z_abs_in_envelope_p5_p50_p95"] = None if not len(pe) else [round(float(np.percentile(pe[:, 2], q)), 2) for q in (5, 50, 95)]
    if len(gt):
        from mint.eval.harm_labels import tiles_of
        j = int(gd.argmin())
        rec["nearest_gt_centre_same_tile"] = bool(np.array_equal(tiles_of(box[None])[0], tiles_of(gt[j:j + 1])[0]))
    rec["class"] = classify(rec)
    return rec, box


def plot_case(path, fr, box, yplus, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ctr = box.mean(0)[:2]
    pts = np.asarray(fr["ego_pts"])
    R = 15.0
    m = (np.abs(pts[:, 0] - ctr[0]) < R) & (np.abs(pts[:, 1] - ctr[1]) < R)
    fig, ax = plt.subplots(1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [1.3, 1]})
    sc = ax[0].scatter(pts[m, 0], pts[m, 1], c=pts[m, 2], s=1.5, cmap="viridis", vmin=box[:, 2].min() - 0.2, vmax=box[:, 2].min() + 2.5)
    fig.colorbar(sc, ax=ax[0], label="z (sensor frame, m)")

    def draw(a, b, col, lw, ls="-"):
        q = np.vstack([b[:4, :2], b[:1, :2]])
        a.plot(q[:, 0], q[:, 1], color=col, lw=lw, ls=ls)
    for g in fr["gt"]:
        draw(ax[0], np.asarray(g), "tab:green", 1.5)
    for y in yplus:
        draw(ax[0], np.asarray(y), "tab:blue", 1.2, "--")
    draw(ax[0], box, "tab:red", 2.0)
    d = -ctr / max(np.linalg.norm(ctr), 1e-6)
    ax[0].annotate("", xy=ctr + 4 * d, xytext=ctr + 1 * d, arrowprops=dict(arrowstyle="->", color="k"))
    ax[0].set_xlim(ctr[0] - R, ctr[0] + R); ax[0].set_ylim(ctr[1] - R, ctr[1] + R); ax[0].set_aspect("equal")
    ax[0].set_title("BEV: red removed box (Y-), blue Y+, green GT; arrow -> receiver", fontsize=8)
    inb = in_poly(pts, box)
    p = pts[inb]
    u = (box[0, :2] - box[3, :2]); u = u / max(np.linalg.norm(u), 1e-6)
    if len(p):
        ax[1].scatter((p[:, :2] - box.mean(0)[:2]) @ u, p[:, 2] - box[:, 2].min(), s=4)
    ax[1].axhline(0, color="tab:red", lw=1); ax[1].axhline(0.3, color="tab:red", lw=0.8, ls=":")
    ax[1].axhline(box[:, 2].max() - box[:, 2].min(), color="tab:red", lw=1)
    ax[1].set_xlabel("along box heading (m)"); ax[1].set_ylabel("z above box bottom (m)")
    ax[1].set_title(f"receiver points inside box ({len(p)})", fontsize=8)
    fig.suptitle(title, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("run_dir")
    ap_.add_argument("--out", default=os.path.join(ROOT, "runs/20261023-E2"))
    ap_.add_argument("--glob", default="20*_[0-9][0-9].pkl.gz")
    a = ap_.parse_args()
    run_dir = a.run_dir if os.path.isabs(a.run_dir) else os.path.join(ROOT, a.run_dir)
    out_dir = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.join(out_dir, "remove_fr"), exist_ok=True)
    pp = A.post_processor()
    conds = ("clean",) + A.FAMILIES
    F = {(c, p): [] for c in conds for p in POL}
    stats = {(c, p): [] for c in conds for p in POL}
    frames, cases = [], {}
    for fpath in sorted(glob.glob(os.path.join(run_dir, "cache", a.glob))):
        R = pickle.load(gzip.open(fpath))
        scen = R["scenario"]
        for fr in R["frames"]:
            n = fr["n_agents"]
            frames.append((scen, fr["frame"]))
            ro = None
            for cond in conds:
                use = cond if n >= 2 else "clean"
                pol, recs, applied, c = A.frame_policies(pp, fr, use, n)
                lab = {(r["sender"], r["tile"]): r["D"] for r in recs}
                st_u = A.frame_stat(*pol["undefended"], fr["gt"])
                rel = r1.assess(c["effects"], v0.Params())
                ch = v0.gating_choice(rel)
                yb, ys = finalize(pp, compose(c["cands"], ch)) if ch else pol["undefended"]
                st_r = A.frame_stat(yb, ys, fr["gt"])
                for p, st in (("undefended", st_u), ("R1", st_r)):
                    F[(cond, p)].append(frame_tpfp(st))
                    stats[(cond, p)].append(st)
                for k, r in rel.items():
                    if not r.gate or lab.get(k, 0.0) >= -A.M:
                        continue
                    for e, v in zip(r.effects, r.verdicts):
                        if e["type"] != "REMOVE" or v != "gate":
                            continue
                        key = (scen, fr["frame"], k[0], tuple(np.round(np.asarray(e["minus"]).mean(0), 2)))
                        if key not in cases:
                            if ro is None:
                                ro = finalize(pp, fr["conditions"]["clean"]["cands"][frozenset(range(1, n))])
                            cro = ro if not applied else finalize(pp, c["cands"][frozenset(range(1, n))])
                            rec, box = case_record(pp, fr, c, k[0], k[1], lab[k], e, cro)
                            cases[key] = {"scen": scen, "frame": fr["frame"], "n_agents": n, **rec, "conditions": [],
                                          "_box": box, "_fr": fr, "_yplus": pol["undefended"][0]}
                        cases[key]["conditions"].append(cond)
        print("done", scen, len(frames), len(cases), flush=True)

    # ---- Part B
    idx = list(range(len(frames)))
    point, apv = metrics(F, idx, conds)
    ref = {k: A.ap(A.merge(v))[IOU] for k, v in stats.items()}       # OpenCOOD's own AP, for the check
    maxdiff = max(abs(apv[k] - ref[k]) for k in ref)
    B = {"note": "E2 Part B, development block T (3 scenarios, 404 frames), in-sample; R1 frozen; AP@0.7 OpenCOOD "
                 "(non-global sort, frames in original order); paired bootstrap, 2000 resamples, seed 0, percentile CI",
         "numpy_ap_vs_opencood_max_abs_diff": maxdiff,
         "AP@0.7": {c: {p: round(apv[(c, p)], 4) for p in POL} for c in conds},
         "point": {k: None if v is None else round(v, 4) for k, v in point.items()}}
    B["bootstrap_scenario_blocks"] = bootstrap(F, frames, conds, "scenario")
    B["bootstrap_scenario_blocks"]["_caveat"] = "3 blocks: the resampling distribution has at most 10 distinct frame sets; coarse"
    B["bootstrap_10frame_blocks"] = bootstrap(F, frames, conds, "block10")
    B["bootstrap_10frame_blocks"]["_caveat"] = "within-scenario blocks of 10 consecutive frames (stratified); ignores between-scenario variation"
    exc = {}
    for kind in ("bootstrap_scenario_blocks", "bootstrap_10frame_blocks"):
        exc[kind] = {f: B[kind][f"recovery_{f}"]["excludes_0"] for f in A.FAMILIES}
        exc[kind]["mean_recovery"] = B[kind]["mean_recovery"]["excludes_0"]
        exc[kind]["clean_rel_loss"] = B[kind]["clean_rel_loss"]["excludes_0"]
    B["recovery_ci_excludes_0"] = exc
    json.dump(B, open(os.path.join(out_dir, "partB_bootstrap.json"), "w"), indent=1)
    print(json.dumps(B, indent=1))

    # ---- Part C
    C = []
    for j, (key, cs) in enumerate(sorted(cases.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]))):
        name = f"case{j:02d}_{cs['scen']}_f{cs['frame']:03d}_s{cs['sender']}.png"
        plot_case(os.path.join(out_dir, "remove_fr", name), cs["_fr"], cs["_box"], cs["_yplus"],
                  f"{cs['scen']} frame {cs['frame']} sender {cs['sender']} | D={cs['D']} range={cs['range_m']} m | "
                  f"SUP/TRAV {cs['SUP']}/{cs['TRAV']} | s-={cs['s_minus']} | rule class: {cs['class']} | conds: {','.join(cs['conditions'])}")
        C.append({"case": j, "plot": f"remove_fr/{name}", **{k: v for k, v in cs.items() if not k.startswith("_")}})
    per_cond = {c: sum(c in x["conditions"] for x in C) for c in conds}
    classes = {}
    for x in C:
        classes[x["class"]] = classes.get(x["class"], 0) + 1
    out = {"note": "E2 Part C, descriptive only; development block T, in-sample; R1 unchanged. Cases = USEFUL units "
                   "(D < -0.5) gated by R1 via a REMOVE effect, deduplicated across conditions",
           "n_cases_unique": len(C), "per_condition": per_cond, "classes_rule_based": classes, "cases": C}
    json.dump(out, open(os.path.join(out_dir, "partC_remove_fr.json"), "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "cases"}, indent=1))


if __name__ == "__main__":
    main()
