"""v3.1 no-network dry run: the frozen v3_dryrun (n2 / forced n1 / forced n5 on the block-T dev slice) with the
v3.1 stream installed (preregistration_v3_1.json, D-70 levels), then a check that every v3 record is unchanged:
for each run, cache/ (frozen v2 record) and v3extra/ (B-NORM magnitudes + the 4 v3 PGD conditions) must equal
the committed v3 dry run (runs/20261024-E5/dryrun_v3) except wall-clock fields, and the only new records are the
D-70 conditions. DEVELOPMENT smoke test; numbers are not results.

  python runners/v3_1_dryrun.py [--out runs/20261024-E5/dryrun_v3_1] [--n_boot 200]
"""
import gzip
import json
import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import v3_1_stream as S31  # noqa: E402

V3_DRY = "runs/20261024-E5/dryrun_v3"
WALL = {"frame_s", "v3_s", "attack_s"}


def _load(p):
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in WALL}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def unchanged_vs_v3(out, tag, scen, new_conds):
    import v3_common as V
    d31, d3 = os.path.join(ROOT, out, tag), os.path.join(ROOT, V3_DRY, tag)
    a, b = _load(os.path.join(d31, "cache", f"{scen}.pkl.gz")), _load(os.path.join(d3, "cache", f"{scen}.pkl.gz"))
    a.pop("timing"), b.pop("timing")
    cache_same = V.same(_strip(a), _strip(b))
    x, y = _load(os.path.join(d31, "v3extra", f"{scen}.pkl.gz")), _load(os.path.join(d3, "v3extra", f"{scen}.pkl.gz"))
    old_same, new_seen = len(x["frames"]) == len(y["frames"]), set()
    for fx, fy in zip(x["frames"], y["frames"]):
        new_seen |= set(fx["pgd"]) - set(fy["pgd"])
        old_same &= set(fy["pgd"]) <= set(fx["pgd"]) and set(fy["mabs"]) <= set(fx["mabs"])
        old_same &= V.same(_strip({c: fx["pgd"][c] for c in fy["pgd"]}), _strip(fy["pgd"]))
        old_same &= V.same({c: fx["mabs"][c] for c in fy["mabs"]}, fy["mabs"])
    return {"cache_v2_record_identical": cache_same, "v3extra_v3_conditions_identical": old_same,
            "new_conditions": sorted(new_seen), "only_D70_new": new_seen <= set(new_conds)}


def main():
    if "--out" not in sys.argv:
        sys.argv += ["--out", "runs/20261024-E5/dryrun_v3_1"]
    out = sys.argv[sys.argv.index("--out") + 1]
    S31.install()
    import v3_dryrun as D
    D.main()
    pr = json.load(open(os.path.join(ROOT, S31.PREREG_V31)))
    new = [f"{c['family']}@r{c['r']}" for c in pr["pgd_families"]["D-70_strong_level"]["conditions"]]
    p = os.path.join(ROOT, out, "dryrun_v3.json")
    summ = json.load(open(p))
    summ["unchanged_vs_v3_dryrun"] = {tag: unchanged_vs_v3(out, tag, D.SCEN, new) for tag in summ["runs"]}
    json.dump(summ, open(p, "w"), indent=1, default=str)
    print("unchanged vs v3:", json.dumps(summ["unchanged_vs_v3_dryrun"]), flush=True)


if __name__ == "__main__":
    main()
