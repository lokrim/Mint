"""v3.2 final-test stream: preregistration_v3_2.json = preregistration_v3_1.json + D-71 (bug fix, no method change).

D-71: the frozen stream's v3_extra copied r["mabs"] for every PGD record, but a stealth-infeasible record
(D-68 amendment 2: attack not applied, scored as clean) is {"ledger": ...} with no "mabs", so the v3.1 final-test
attempt crashed (KeyError) on the first infeasible frame. This file:
  * v3_extra: the v3.1 v3_extra with exactly one change: a record without "mabs" is skipped when copying B-NORM
    magnitudes, after asserting its ledger reason is "stealth_infeasible" (any other cause still fails). This is
    how the frozen v3_analyze.frames_test already reads the records,
  * install(): runs the v3.1 install(), then points v3_1_stream.v3_extra at the function above and every
    preregistration reference at preregistration_v3_2.json. v3_1_stream.run_scenario looks both up at call time.
    Everything else is the frozen v3.1 run_scenario and the frozen v3_stream.main, unchanged.
v3, v3.1 frozen files are unchanged (byte-identical; checked by their sha256 at start and end of the run).

  python runners/v3_2_stream.py --run_dir runs/<date>-E5v3 --user_approved     (after approval only)
  python runners/v3_2_stream.py --run_dir runs/<date>-E5v3 --dry_run           (hash + budget check, no network)
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)
import e0_stream as E  # noqa: E402
import v3_1_stream as S31  # noqa: E402
import v3_common as V  # noqa: E402
import v3_stream as S3  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

from mint.geometry.ground import ground_mask  # noqa: E402
from mint.model.attfuse_parts import agent_features  # noqa: E402

PREREG_V32 = "runs/20261024-E5/preregistration_v3_2.json"


def copy_mabs(mabs, pgd):
    """D-71: B-NORM magnitudes of the PGD conditions into mabs; stealth-infeasible records have none."""
    for c, r in pgd.items():
        if "mabs" not in r:                                  # D-68 am. 2: stealth infeasible, not applied
            assert r["ledger"].get("reason") == "stealth_infeasible", (c, r["ledger"])
            continue
        mabs[c] = r["mabs"]
    return mabs


def v3_extra(model, ds, batch, rec, scen, i, pcr, vs, levels, sigma, thr, tau):
    """v3.1 v3_extra (frozen runners/v3_1_stream.py), the final copy loop replaced by copy_mabs (D-71)."""
    n = rec["n_agents"]
    cavs = E.cav_contents(ds, i)
    ego = np.asarray(cavs[0][1]["lidar_np"][:, :3], np.float64)
    att_pts = E.projected_points(cavs[1][1], pcr) if n >= 2 else None
    with torch.no_grad():
        feats0, _ = agent_features(model, batch["ego"])
    mabs = V.bnorm_extras(model, batch, rec, scen, i, feats0, att_pts, ego, pcr, vs)
    gmask, _ = ground_mask(ego)
    pgd = {}
    for fam, rs in levels.items():
        for r in rs:
            t0 = time.perf_counter()
            got = V.pgd_conditions(model, ds.post_processor, batch, feats0, n, ego, gmask, pcr, scen, i, {fam: [r]},
                                   sigma, thr, tau)
            c = V.cond_name(fam, r)
            if c in got:
                got[c]["attack_s"] = round(time.perf_counter() - t0, 3)
            pgd.update(got)
    copy_mabs(mabs, pgd)
    return {"frame": i, "mabs": mabs, "pgd": pgd}


def install():
    S31.install()
    S31.v3_extra = v3_extra
    S31.PREREG_V31 = PREREG_V32           # written into each v3extra record as its "preregistration"
    S3.PREREG = PREREG_V32


def main():
    install()
    S3.main()


if __name__ == "__main__":
    main()
