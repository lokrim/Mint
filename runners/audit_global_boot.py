"""AUDIT X0 follow-up: bootstrap CIs of mean dAP@0.7 (4 original families) with global-sort AP vs the frozen
non-global AP, blocks T and H (development). Same resampling as e5_analyze.bootstrap (scenario; 10-frame blocks
within scenario), 2000 resamples, seed 0. GT for scoring only."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import audit_common as C  # noqa: E402
import audit_cache_checks as K  # noqa: E402

import numpy as np  # noqa: E402

FAM4 = ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts")
M = ("undefended", "B-RAY", "R1")


def arrays(stats):
    out = []
    for s in stats:
        r = s[0.7]
        out.append((np.asarray(r["tp"], np.int64), np.asarray(r["fp"], np.int64), np.asarray(r["score"], float), int(r["gt"])))
    return out


def ap(parts, idx, glob):
    tp = np.concatenate([parts[j][0] for j in idx])
    fp = np.concatenate([parts[j][1] for j in idx])
    gt = sum(parts[j][3] for j in idx)
    if glob:
        sc = np.concatenate([parts[j][2] for j in idx])
        o = np.argsort(-sc, kind="stable")
        tp, fp = tp[o], fp[o]
    return C.Z.ap_from([(tp, fp, gt)])


def stat(P, idx, glob):
    d = {m: float(np.mean([ap(P[(f, m)], idx, glob) - ap(P[(f, "undefended")], idx, glob) for f in FAM4])) for m in M[1:]}
    d["R1-B-RAY"] = d["R1"] - d["B-RAY"]
    d["clean_rel_loss|B-RAY"] = 1 - ap(P[("clean", "B-RAY")], idx, glob) / ap(P[("clean", "undefended")], idx, glob)
    return d


def units_of(keys, kind):
    scen = list(dict.fromkeys(k[0] for k in keys))
    pos = {s: [j for j, k in enumerate(keys) if k[0] == s] for s in scen}
    if kind == "scenario":
        return [pos[s] for s in scen], [list(range(len(scen)))]
    U, S = [], []
    for s in scen:
        f = len(U)
        U += [pos[s][k:k + 10] for k in range(0, len(pos[s]), 10)]
        S.append(list(range(f, len(U))))
    return U, S


def main(n_boot=2000):
    out = {"label": "DEVELOPMENT; T in-sample, H exposed", "statistic": "mean over 4 original families of dAP@0.7 vs no defense"}
    for blk, (d, conds, label) in K.BLOCKS.items():
        frames = list(K.frames_of(d))
        _, _, stats, keys = C.evaluate(frames, conds)
        P = {k: arrays(v) for k, v in stats.items() if k[1] in M and k[0] in ("clean",) + FAM4}
        res = {"label": label}
        for glob in (False, True):
            name = "global_sort" if glob else "nonglobal_frozen"
            pt = stat(P, list(range(len(keys))), glob)
            r = {"point": {k: round(v, 5) for k, v in pt.items()}}
            for kind in ("scenario", "block10"):
                U, S = units_of(keys, kind)
                rng = np.random.default_rng(0)
                draws = {k: [] for k in pt}
                for _ in range(n_boot):
                    pick = [u for st in S for u in rng.choice(st, len(st))]
                    idx = sorted(j for u in pick for j in U[u])
                    for k, v in stat(P, idx, glob).items():
                        draws[k].append(v)
                r[kind] = {k: {"ci95": [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)],
                               "p_one_sided_le0": round(float((np.sum(np.asarray(v) <= 0) + 1) / (len(v) + 1)), 4)}
                           for k, v in draws.items()}
            res[name] = r
        out[blk] = res
        print(blk, json.dumps(res), flush=True)
    json.dump(out, open(os.path.join(ROOT, "runs/20261024-AUDIT/X0_global_sort_bootstrap.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
