"""Build the E5 report (figures, CSV tables, report.md) from the analysis summaries only.

  # final test, after the stream and both analyses finished:
  python runners/report_build.py --run_dir runs/20261024-E5v3
  # development inputs (any e5_v3-format file, e5_test-format file optional):
  python runners/report_build.py --v3 <e5_v3.json> [--v2 <e5_test.json>] [--prereg <prereg.json>] --out <dir>

Reads only e5_v3.json / e5_test.json (never cache/ or v3extra/). Refuses to build from a final-test file that is
flagged incomplete (pre-registered rule: no AP or criteria on partial results). Output: <out>/report.md,
<out>/figures/*.png|svg (light + _dark), <out>/tables/*.csv, <out>/manifest.json.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from mint.report.data import Inputs  # noqa: E402
from mint.report.render import IncompleteFinalTest, build  # noqa: E402

DEFAULT_PREREG = "runs/20261024-E5/preregistration_v3_2.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", default=None)
    ap.add_argument("--v3", default=None)
    ap.add_argument("--v2", default=None)
    ap.add_argument("--prereg", default=None, help=f"default: the file named in e5_v3.json, else {DEFAULT_PREREG}")
    ap.add_argument("--out", default=None, help="default: <run_dir>/report")
    ap.add_argument("--themes", nargs="+", default=["light", "dark"])
    a = ap.parse_args()
    if a.run_dir:
        a.v3 = a.v3 or os.path.join(a.run_dir, "e5_v3.json")
        a.v2 = a.v2 or os.path.join(a.run_dir, "e5_test.json")
        a.out = a.out or os.path.join(a.run_dir, "report")
    if not a.v3 or not a.out:
        ap.error("give --run_dir, or --v3 and --out")
    if not os.path.exists(a.v3):
        sys.exit(f"STOP: {a.v3} does not exist (run the analysis first; the report never reads the caches)")
    import json
    prereg = a.prereg or (None if json.load(open(a.v3)).get("preregistration") else os.path.join(ROOT, DEFAULT_PREREG))
    inp = Inputs(a.v3, a.v2, prereg, root=ROOT)
    try:
        man = build(inp, a.out, themes=tuple(a.themes))
    except IncompleteFinalTest as e:
        sys.exit(f"STOP: {e}")
    print(f"{inp.status_text}: report -> {os.path.join(a.out, 'report.md')} ({len(man['figures'])} figures)")


if __name__ == "__main__":
    main()
