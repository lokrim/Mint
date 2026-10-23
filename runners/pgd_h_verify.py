"""v3 step 1 check: the re-streamed block H must reproduce E4 / E5a-H exactly; stop if not.

(1) Record level: every frame of runs/<run>/cache equals runs/20261023-E4/cache (all fields except the
    wall-clock `frame_s`; timing is not re-run): GT, receiver scan, agents, every condition's ledger,
    candidates of every subset, effects with ray counts, attention tiles; compose checks equal.
(2) Number level: e5_analyze.analyze (frozen) on the new cache vs runs/20261024-E5/H/e5a_H.json (every field
    except paths and the two wall-clock timing fields B-RAY_cost_dev / overhead; attempt 1 compared those too and
    differed only there: reproduction_check_attempt1.json), and
    e4_analyze.run('H') (frozen) on the new cache vs runs/20261023-E4/e4_heldout.json (everything except
    file paths and the E4 timing/overhead section).

  python runners/pgd_h_verify.py --run_dir runs/20261024-PGD
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
import v3_common as V  # noqa: E402

OLD = os.path.join(ROOT, "runs/20261023-E4")
E5A_H = os.path.join(ROOT, "runs/20261024-E5/H/e5a_H.json")


def load(p):
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def record_check(new_dir):
    res, ok = {}, True
    for p in sorted(glob.glob(os.path.join(OLD, "cache", "20*_[0-9][0-9].pkl.gz"))):
        s = os.path.basename(p)
        a, b = load(p), load(os.path.join(new_dir, "cache", s))
        fa, fb = a["frames"], b["frames"]
        bad = []
        if len(fa) != len(fb):
            bad.append("frame count")
        for x, y in zip(fa, fb):
            kx = {k: v for k, v in x.items() if k != "frame_s"}
            ky = {k: v for k, v in y.items() if k != "frame_s"}
            if not V.same(kx, ky):
                diff = [k for k in kx if k not in ky or not V.same(kx[k], ky[k])]
                if "conditions" in diff:
                    diff += [f"cond:{c}" for c in kx["conditions"] if not V.same(kx["conditions"][c], ky["conditions"].get(c))]
                bad.append({"frame": x["frame"], "fields": diff})
        cc = V.same(a["compose_checks"], b["compose_checks"])
        res[a["scenario"]] = {"frames": [len(fa), len(fb)], "mismatches": bad[:10], "n_mismatch": len(bad),
                              "compose_checks_equal": cc}
        ok = ok and not bad and cc
    return ok, res


def strip(d, drop):
    return {k: v for k, v in d.items() if k not in drop}


def number_check(new_dir):
    import e5_analyze as X
    import e4_analyze as Z
    files = sorted(glob.glob(os.path.join(new_dir, "cache", "20*_[0-9][0-9].pkl.gz")))
    conds = ("clean",) + X.ORIG + ("spoof_blind",)
    out = X.analyze(files, conds, True)
    ref = json.load(open(E5A_H))
    drop = ("files", "mode", "label", "code", "D57")
    timing = ("B-RAY_cost_dev", "overhead")          # wall-clock seconds; the re-stream has no timing pass
    a = json.loads(json.dumps(strip(out, drop + timing), default=str))
    b = strip(ref, drop + timing)
    e5 = {k: a.get(k) == b.get(k) for k in sorted(set(a) | set(b))}
    Z.RUN = new_dir                                    # e4_analyze reads RUN/cache and writes RUN/e4_heldout.json
    o4 = json.loads(json.dumps(Z.run("H"), default=str))
    r4 = json.load(open(os.path.join(OLD, "e4_heldout.json")))
    drop4 = ("files", "overhead", "scenarios")
    e4 = {k: o4.get(k) == r4.get(k) for k in sorted(set(strip(o4, drop4)) | set(strip(r4, drop4)))}
    sc = [strip(x, ()) for x in o4["scenarios"]] == [strip(x, ()) for x in r4["scenarios"]]
    e4["scenarios(frames, compose checks)"] = sc
    return all(e5.values()) and all(e4.values()), {"e5a_H_fields_equal": e5, "e4_heldout_fields_equal": e4}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    a = ap.parse_args()
    d = os.path.join(ROOT, a.run_dir)
    ok1, r1 = record_check(d)
    print("record-level identical:", ok1, json.dumps(r1)[:2000], flush=True)
    ok2, r2 = number_check(d)
    res = {"label": "v3 step 1: block-H re-stream reproduction check (development, exposed H)",
           "record_level_identical": ok1, "records": r1, "numbers_identical": ok2, "numbers": r2,
           "reproduces_exactly": bool(ok1 and ok2)}
    json.dump(res, open(os.path.join(d, "reproduction_check.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "records"}, indent=1))
    if not res["reproduces_exactly"]:
        sys.exit("STOP: re-streamed H does not reproduce E4/E5a-H exactly")


if __name__ == "__main__":
    main()
