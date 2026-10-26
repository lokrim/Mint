"""Build the report: figures (PNG + SVG, light and dark), CSV tables, report.md and manifest.json."""
import csv
import json
import os

import jinja2
import matplotlib.pyplot as plt

from . import style, tables as T
from .data import DEF_NAME, DEFS, METHOD_NAME
from .figures import FIGURES, cond_label

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


class IncompleteFinalTest(RuntimeError):
    pass


def _write_csv(path, rows):
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def make_figures(inp, out_dir, themes=("light", "dark"), dpi=200, only=None):
    fdir, tdir = os.path.join(out_dir, "figures"), os.path.join(out_dir, "tables")
    os.makedirs(fdir, exist_ok=True)
    os.makedirs(tdir, exist_ok=True)
    made = []
    for name, num, fn, title, caption in FIGURES:
        if only and name not in only:
            continue
        entry = {"name": name, "num": num, "title": title, "caption": caption, "files": {}}
        for theme in themes:
            t = style.apply(theme)
            fig, rows = fn(inp, t)
            suffix = "" if theme == "light" else "_dark"
            for ext in ("png", "svg"):
                p = os.path.join(fdir, f"{name}{suffix}.{ext}")
                fig.savefig(p, dpi=dpi if ext == "png" else None, bbox_inches="tight", pad_inches=0.12,
                            metadata={"Date": None} if ext == "svg" else None)   # reproducible files
                entry["files"][f"{theme}_{ext}"] = os.path.relpath(p, out_dir)
            plt.close(fig)
            if theme == themes[0]:
                p = os.path.join(tdir, f"{name}.csv")
                _write_csv(p, rows)
                entry["files"]["csv"] = os.path.relpath(p, out_dir)
                entry["n_rows"] = len(rows)
        made.append(entry)
    return made


def context(inp, figs):
    pr = inp.prereg or {}
    v3 = inp.v3
    return {
        "status": inp.status, "status_text": inp.status_text, "label": inp.label, "prov": inp.provenance(),
        "n_scenarios": inp.n_scenarios(), "n_frames": inp.n_frames(), "n_agents_hist": v3.get("n_agents_hist"),
        "methods": [METHOD_NAME[m] for m in inp.methods],
        "conditions": [cond_label(c, inp.prereg) for c in inp.conditions],
        "comparison_set": pr.get("comparison_set"), "outcome_rule": pr.get("outcome"),
        "d64_rule": (pr.get("D-64_dual_AP") or {}).get("rule"), "d69": pr.get("D-69_reporting"),
        "scope_limits": pr.get("scope_limits"), "labelling": pr.get("labelling"),
        "deviations": [k for k in ("D-70_strong_level",) if k in (pr.get("pgd_families") or {})] +
                      [k for k in ("D-71",) if k in pr],
        "d71": pr.get("D-71"),
        "fig": {f["name"]: f for f in figs},
        "t": {"headline": T.headline(inp), "clean_cost": T.clean_cost(inp), "criteria": T.criteria(inp),
              "r1_minus_bray": T.r1_minus_bray(inp), "pgd": T.pgd(inp) if inp.pgd_conditions else None,
              "checks": T.checks(inp), "expected": T.expected_outcome_checks(inp), "d70_note": T.d70_note(inp),
              "per_family": {d: T.per_family(inp, d) for d in DEFS},
              "realized_only": {d: T.realized_only(inp, d) for d in DEFS},
              "absolute_ap": {d: T.absolute_ap(inp, d) for d in DEFS}},
        "verdict": T.verdict(inp), "DEFS": DEFS, "DEF_NAME": DEF_NAME,
    }


def build(inp, out_dir, themes=("light", "dark"), dpi=200):
    if inp.status == "INCOMPLETE":
        raise IncompleteFinalTest(
            "The final-test analysis is flagged incomplete (completeness check missing or failed). Pre-registered rule: "
            "no AP or criteria on partial results, so no report is built.")
    os.makedirs(out_dir, exist_ok=True)
    figs = make_figures(inp, out_dir, themes, dpi)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR), undefined=jinja2.StrictUndefined,
                             trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    ctx = context(inp, figs)
    report = env.get_template("final_report.md.j2").render(**ctx)
    rp = os.path.join(out_dir, "report.md")
    open(rp, "w").write(report)
    man = {"provenance": ctx["prov"], "figures": figs, "report": "report.md",
           "note": "Every number is copied from the input analysis JSON files; nothing is recomputed."}
    json.dump(man, open(os.path.join(out_dir, "manifest.json"), "w"), indent=1)
    return man
