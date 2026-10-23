"""AUDIT X0 (+ the X2 cache check) on the block-T (in-sample) and block-H (exposed) caches.
runs/20261024-AUDIT/plan.json. Frozen methods via e5_analyze.frame_methods; GT for scoring only.

  python runners/audit_cache_checks.py
"""
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import audit_common as C  # noqa: E402

import gzip  # noqa: E402
import pickle  # noqa: E402

import numpy as np  # noqa: E402
from mint.reliability import baselines as BL  # noqa: E402

BLOCKS = {"T": ("runs/20261023-E0/cache", ("clean", "spoof_feat", "remove_feat", "shift_feat", "spoof_pts"),
                "DEVELOPMENT, block T, in-sample"),
          "H": ("runs/20261023-E4/cache", ("clean", "spoof_feat", "remove_feat", "shift_feat", "spoof_pts", "spoof_blind"),
                "DEVELOPMENT / exposed, block H (n = 2)")}


def frames_of(d):
    for p in sorted(glob.glob(os.path.join(ROOT, d, "20*_[0-9][0-9].pkl.gz"))):
        R = pickle.load(gzip.open(p))
        for fr in R["frames"]:
            yield R["scenario"], fr


def main():
    out = {"plan": "runs/20261024-AUDIT/plan.json (X0, X2 cache check)"}
    for blk, (d, conds, label) in BLOCKS.items():
        t0 = time.time()
        frames = list(frames_of(d))
        pp = C.A.post_processor()
        realized = {c: set() for c in conds if c != "clean"}
        spoof_boxes = {c: [] for c in ("spoof_feat", "spoof_pts", "spoof_blind") if c in conds}
        null = []
        for scen, fr in frames:
            n = fr["n_agents"]
            for c in realized:
                cc, applied = C.A.cond_of(fr, c)
                if n < 2 or not applied:
                    continue
                rz = C.A.realization(pp, fr, "spoof_feat" if c == "spoof_blind" else c, cc, applied)
                if rz.get("realized"):
                    realized[c].add((scen, fr["frame"]))
                    if c in spoof_boxes:
                        spoof_boxes[c] += C.spoof_box_outcomes(fr, cc) or []
            for r in fr.get("null_rays", []):
                null.append(BL.b_ray_verdict({"SUP": r["std"]["SUP"], "TRAV": r["std"]["TRAV"], "self_box": r["self_box"]}))
        summ, bray, stats, keys = C.evaluate(frames, conds, realized)
        res = {"label": label, "frames": len(frames), "summary": summ, "bray_boxes": bray,
               "realized_frames": {c: len(v) for c, v in realized.items()}}
        fam3 = ("spoof_feat", "shift_feat", "spoof_pts")
        fam4 = fam3 + ("remove_feat",)
        A = summ["all_frames"]
        for m in ("B-RAY", "R1", "ego_only"):
            res[f"mean4_dAP@0.7|{m}"] = round(float(np.mean([A[f][m]["dAP@0.7"] for f in fam4])), 5)
            res[f"mean4_dAP@0.7_global|{m}"] = round(float(np.mean([A[f][m]["dAP@0.7_global"] for f in fam4])), 5)
            res[f"mean3_noremove_dAP@0.7|{m}"] = round(float(np.mean([A[f][m]["dAP@0.7"] for f in fam3])), 5)
        res["R1-BRAY_mean4_nonglobal"] = round(res["mean4_dAP@0.7|R1"] - res["mean4_dAP@0.7|B-RAY"], 5)
        res["R1-BRAY_mean4_global"] = round(res["mean4_dAP@0.7_global|R1"] - res["mean4_dAP@0.7_global|B-RAY"], 5)
        R = summ.get("realized_only", {})
        res["realized_only_dAP@0.7"] = {c: {"frames": R[c]["frames"],
                                            "attack_loss": R[c][c]["undefended"].get("attack_loss@0.7"),
                                            **{m: R[c][c][m]["dAP@0.7"] for m in ("B-RAY", "R1", "ego_only")}}
                                        for c in R}
        res["realized_spoof_boxes_near_dst"] = {c: {"boxes": len(v), **{k: sum(b["verdict"] == k for b in v)
                                                                       for k in ("drop", "keep", "keep_unknown", "keep_self")},
                                                    "gt_iou_ge_0.5": sum(b["gt_iou"] >= 0.5 for b in v)}
                                                for c, v in spoof_boxes.items()}
        if null:
            k = sum(v in ("drop", "keep") for v in null)
            res["null_boxes"] = {"what": "E0 empty synthetic boxes in GT-free space (8/frame), B-RAY verdicts",
                                 "boxes": len(null), **{v: null.count(v) for v in ("drop", "keep", "keep_unknown", "keep_self")},
                                 "kept_share_of_KNOWN": round(null.count("keep") / k, 4) if k else None}
        per = {}
        for s in sorted({k[0] for k in keys}):
            idx = [j for j, kk in enumerate(keys) if kk[0] == s]
            t = C.summarize({kk: [v[j] for j in idx] for kk, v in stats.items()}, [keys[j] for j in idx], conds)["all_frames"]
            per[s] = {m: round(float(np.mean([t[f][m]["dAP@0.7"] for f in fam4])), 5) for m in ("B-RAY", "R1")}
        res["per_scenario_mean4_dAP@0.7"] = per
        res["runtime_s"] = round(time.time() - t0)
        out[blk] = res
        print(blk, json.dumps({k: v for k, v in res.items() if k != "summary"}, default=str), flush=True)
    json.dump(out, open(os.path.join(ROOT, "runs/20261024-AUDIT/X0_cache_checks.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
