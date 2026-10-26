"""Load the analysis summaries and give uniform access to points and confidence intervals.

Status rules (shown on every figure and at the top of the report):
  * FINAL     - label says "FINAL TEST" and the completeness check passed (15 scenarios, 2066 frames);
  * INCOMPLETE - label says "FINAL TEST" but the completeness check is missing or failed: NOT RESULTS;
  * DEVELOPMENT - anything else (dry runs, blocks T/H): NOT RESULTS.
"""
import datetime as dt
import hashlib
import json
import os
import subprocess

DEFS = ("global", "frame")                     # D-69: global-ranking AP is the headline
DEF_NAME = {"global": "global-ranking AP (headline)", "frame": "frame-order AP (OPV2V-comparable)"}
ORIG = ("spoof_feat", "remove_feat", "shift_feat", "spoof_pts")
METHOD_ORDER = ("B-RAY", "R1", "R1_noREMOVE", "B-NORM", "ego_only")
METHOD_NAME = {"B-RAY": "B-RAY (primary)", "R1": "R1 (key secondary)", "R1_noREMOVE": "R1-noREMOVE (ablation)",
               "B-NORM": "B-NORM (baseline)", "ego_only": "Ego-only", "undefended": "No defense"}
FORBIDDEN_PARTS = ("cache", "v3extra")        # the per-frame records are never read here

STATUS_TEXT = {"FINAL": "FINAL TEST (one-time)",
               "INCOMPLETE": "INCOMPLETE FINAL TEST - NOT RESULTS, do not interpret",
               "DEVELOPMENT": "DEVELOPMENT / DRY RUN - not results"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _check_path(p):
    parts = os.path.normpath(p).split(os.sep)
    if any(x in FORBIDDEN_PARTS for x in parts) or p.endswith(".pkl.gz"):
        raise ValueError(f"the reporting pipeline reads only the analysis JSON files, not {p}")
    return p


def git_head(root):
    try:
        return subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return None


class Inputs:
    """v3: e5_v3.json (required). v2: e5_test.json (optional). prereg: the preregistration (optional)."""

    def __init__(self, v3_path, v2_path=None, prereg_path=None, root=None):
        self.root = root or os.getcwd()
        self.v3_path = _check_path(v3_path)
        self.v2_path = _check_path(v2_path) if v2_path and os.path.exists(v2_path) else None
        self.v3 = json.load(open(v3_path))
        self.v2 = json.load(open(self.v2_path)) if self.v2_path else None
        if prereg_path is None and self.v3.get("preregistration"):
            cand = os.path.join(self.root, self.v3["preregistration"])
            prereg_path = cand if os.path.exists(cand) else None
        self.prereg_path = prereg_path
        self.prereg = json.load(open(prereg_path)) if prereg_path else None
        self.label = self.v3.get("label", "(no label)")
        self.status = self._status()

    # ------------------------------------------------------------------ status and provenance
    def _status(self):
        if "FINAL TEST" in self.label.upper():
            cc = self.v3.get("completeness_check") or {}
            return "FINAL" if cc.get("pass") is True else "INCOMPLETE"
        return "DEVELOPMENT"

    @property
    def status_text(self):
        return STATUS_TEXT[self.status]

    def provenance(self):
        rel = lambda p: os.path.relpath(p, self.root) if p else None  # noqa: E731
        return {"generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "status": self.status, "label": self.label,
                "inputs": {k: {"path": rel(p), "sha256": sha256(p)} for k, p in
                           (("e5_v3.json", self.v3_path), ("e5_test.json", self.v2_path),
                            ("preregistration", self.prereg_path)) if p},
                "git_head": git_head(self.root),
                "frozen_code_commit": (self.prereg or {}).get("frozen_code_commit"),
                "preregistration_version": (self.prereg or {}).get("version")}

    # ------------------------------------------------------------------ access
    @property
    def conditions(self):
        return list(self.v3["conditions"])

    @property
    def pgd_conditions(self):
        return [c for c in self.conditions if c.startswith("pgd_")]

    @property
    def methods(self):
        have = set(self.v3["methods"])
        return [m for m in METHOD_ORDER if m in have]

    def point(self, d, key):
        return self.v3["point"][d].get(key)

    def ci(self, d, key, kind="scenario"):
        r = self.v3["bootstrap"][d][kind].get(key)
        return tuple(r["ci95"]) if r and r.get("ci95") is not None else None

    def stat(self, d, key):
        """{point, ci_scenario, ci_block10} for one statistic and AP definition."""
        return {"point": self.point(d, key), "ci_scenario": self.ci(d, key, "scenario"),
                "ci_block10": self.ci(d, key, "block10")}

    def per_family(self, d, cond, method):
        return ((self.v3.get("tables") or {}).get(d, {}).get("per_family", {}).get(cond, {}) or {}).get(method)

    def n_scenarios(self):
        return self.v3.get("scenarios")

    def n_frames(self):
        return self.v3.get("frames")


def run_dir_inputs(run_dir, prereg_path=None, root=None):
    return Inputs(os.path.join(run_dir, "e5_v3.json"), os.path.join(run_dir, "e5_test.json"), prereg_path, root)
