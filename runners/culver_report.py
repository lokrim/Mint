"""Build the CULVER report (D-72) with the existing report pipeline (src/mint/report), unchanged.

Same figures, CSV tables and sections as the OPV2V final-test report, plus: the clean-detector sanity check, the
plan's expected outcomes, runtime by number of cars, and one comparison table OPV2V test vs Culver City for the
headline numbers (kept separate; never pooled). Status "CULVER CITY (held-out domain shift)" only if the analysis
label says CULVER CITY and the completeness check (4 scenarios, 550 frames) passed. Reads only the analysis JSON
files (never cache/ or v3extra/); every number is copied, nothing is recomputed.

  python runners/culver_report.py --run_dir runs/20261026-CULVER
  python runners/culver_report.py --run_dir <dry-run dir> --out <dir>        (dry run: status DEVELOPMENT)
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import jinja2  # noqa: E402

from mint.report import data as D  # noqa: E402
from mint.report import figures as F  # noqa: E402
from mint.report import render as R  # noqa: E402
from mint.report import tables as T  # noqa: E402

TEST_RUN = "runs/20261024-E5v3"
PLAN = "runs/20261026-CULVER/plan.json"
TEMPLATE = "culver_report.md.j2"
D.STATUS_TEXT["CULVER"] = "CULVER CITY (held-out domain shift)"
F.STATUS_INK["CULVER"] = "ink2"


class CulverInputs(D.Inputs):
    def _status(self):
        lab = self.label.upper()
        if "INCOMPLETE" in lab or "FINAL TEST" in lab:
            return "INCOMPLETE"
        if lab.startswith("CULVER CITY"):
            cc = self.v3.get("completeness_check") or {}
            return "CULVER" if cc.get("pass") is True else "INCOMPLETE"
        return "DEVELOPMENT"


def _pc(v3, d, key):
    """(point, scenario CI, 10-frame CI) of one statistic."""
    b = v3["bootstrap"][d]
    ci = lambda kind: (b[kind].get(key) or {}).get("ci95")  # noqa: E731
    return v3["point"][d].get(key), ci("scenario"), ci("block10")


def _cell(p, ci, pts=True):
    if p is None:
        return "n/a"
    if pts:
        return f"{T.f_pts(p)} {T.f_ci(ci)}" if ci else T.f_pts(p)
    return f"{p * 100:.2f}% {T.f_ci(ci, 100)}" if ci else f"{p * 100:.2f}%"


def comparison(test, cul):
    """Headline numbers, OPV2V test vs Culver City (both already computed by the frozen analyses)."""
    rows, csv = [], []

    def add(name, d, f):
        a, b = f(test, d), f(cul, d)
        rows.append([name, D.DEF_NAME[d] if d else "-", a, b])
        csv.append({"statistic": name, "ap_definition": d or "", "opv2v_test": a, "culver_city": b})

    add("Scenarios / frames", None, lambda v, d: f"{v['scenarios'] if isinstance(v['scenarios'], int) else len(v['scenarios'])} / {v['frames']}")
    add("Agents per frame", None, lambda v, d: str(v.get("n_agents_hist")))
    for d in D.DEFS:
        add("No-defense clean AP@0.7 (absolute)", d, lambda v, d: f"{v['AP'][d]['clean']['undefended']['AP@0.7']:.4f}")
    for m in ("B-RAY", "R1", "R1_noREMOVE", "B-NORM", "ego_only"):
        for d in D.DEFS:
            add(f"{D.METHOD_NAME[m]}: mean ΔAP@0.7, 4 original attacks (pts, scen. CI)", d,
                lambda v, d, m=m: _cell(*_pc(v, d, f"mean_delta_orig|{m}")[:2]))
    for m in ("B-RAY", "R1"):
        for d in D.DEFS:
            add(f"{D.METHOD_NAME[m]}: clean relative AP@0.7 loss (scen. CI)", d,
                lambda v, d, m=m: _cell(*_pc(v, d, f"rel_loss|{m}")[:2], pts=False))
    for d in D.DEFS:
        def holm(v, d):
            c = v["criteria_v3"][d]["co_test_vs_no_defense"]
            return "; ".join(f"{m} p={T.f_p(c[m]['p_one_sided'])} {'reject' if c[m]['holm']['reject'] else 'no reject'}"
                             for m in ("B-RAY", "R1"))
        add("Holm co-test vs no defense (1-sided, scenario bootstrap)", d, holm)
    for d in D.DEFS:
        add("v2 success rule (B-RAY Holm reject and clean CI high <= 1%)", d,
            lambda v, d: "passes" if v["criteria_v3"][d]["pass"] else "does not pass")
    add("D-64 verdict", None, lambda v, d: v["criteria_v3"]["D-64"]["verdict"])
    for d in D.DEFS:
        add("R1 − B-RAY, mean of 4 (pts, scen. CI) and statement", d,
            lambda v, d: f"{_cell(*_pc(v, d, 'paired_mean_orig|R1-B-RAY')[:2])}: “{v['criteria_v3'][d]['R1_minus_BRAY']['statement']}”")
    for c in ("spoof_blind", "pgd_remove_stealth@r0.25", "pgd_remove_stealth@r1.0", "pgd_untargeted_stealth@r1.0"):
        for d in D.DEFS:
            def pg(v, d, c=c):
                al = v["point"][d].get(f"attack_loss|{c}")
                parts = [f"loss {T.f_pts(al)}"]
                for m in ("B-RAY", "R1"):
                    rec = v["point"][d].get(f"recovery|{m}|{c}")
                    parts.append(f"{m} {T.f_pts(v['point'][d].get(f'delta|{m}|{c}'))}"
                                 + (f" (rec. {rec:.2f})" if rec is not None else ""))
                return "; ".join(parts)
            add(f"{F.cond_label(c)}: attack loss, ΔAP (recovery)", d, pg)
    for c in ("clean", "pgd_untargeted@r0.25", "pgd_untargeted_stealth@r0.5"):
        add(f"B-NORM sender-1 flag rate, {F.cond_label(c)}", None,
            lambda v, d, c=c: T.f_pct((v.get("B-NORM_flags", {}).get(c) or {}).get("catch_rate")))
    return T.md(["Statistic", "AP definition", "OPV2V test (primary, 15 scen.)", "Culver City (secondary, 4 scen.)"], rows), csv


def runtime(test2, cul2):
    """Measured overhead by number of cars (frozen v2 timing pass), test vs Culver."""
    rows = []
    for name, v in (("OPV2V test", test2), ("Culver City", cul2)):
        st = ((v or {}).get("overhead") or {}).get("by_stratum") or {}
        for s in sorted(st):
            for mode in ("dense", "trigger_0.05", "B-RAY"):
                r = st[s].get(mode)
                if r:
                    rows.append([name, s, st[s]["frames"], mode, f"{r['overhead']['p50'] * 100:.1f}%",
                                 f"{r['overhead']['p95'] * 100:.1f}%", f"{r['extra_s']['p50']:.3f}",
                                 f"{r['baseline_s']['p50']:.3f}"])
    return T.md(["Data", "cars", "frames", "mode", "overhead p50", "overhead p95", "extra s p50", "baseline s p50"], rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--themes", nargs="+", default=["light", "dark"])
    a = ap.parse_args()
    rd = os.path.join(ROOT, a.run_dir)
    out = a.out or os.path.join(rd, "report")
    v3p, v2p = os.path.join(rd, "e5_v3.json"), os.path.join(rd, "e5_test.json")
    if not os.path.exists(v3p):
        sys.exit(f"STOP: {v3p} does not exist (run runners/culver_analyze.py first)")
    inp = CulverInputs(v3p, v2p, None, root=ROOT)
    if inp.status == "INCOMPLETE":
        sys.exit("STOP: the Culver City analysis is flagged incomplete; no report on partial results")
    test = D.Inputs(os.path.join(ROOT, TEST_RUN, "e5_v3.json"), os.path.join(ROOT, TEST_RUN, "e5_test.json"), None, ROOT)
    assert test.status == "FINAL"
    os.makedirs(out, exist_ok=True)
    figs = R.make_figures(inp, out, tuple(a.themes))
    ctx = R.context(inp, figs)
    cmp_md, cmp_csv = comparison(test.v3, inp.v3)
    R._write_csv(os.path.join(out, "tables", "11_test_vs_culver.csv"), cmp_csv)
    sanity_p = os.path.join(rd, "sanity_first_scenario.json")
    plan = json.load(open(os.path.join(ROOT, PLAN)))
    ctx.update(culver={"comparison": cmp_md, "runtime": runtime(test.v2, inp.v2), "plan": plan,
                       "sanity": json.load(open(sanity_p)) if os.path.exists(sanity_p) else None,
                       "test_report": f"{TEST_RUN}/report/report.md", "test_status": test.status_text})
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(R.TEMPLATE_DIR), undefined=jinja2.StrictUndefined,
                             trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    open(os.path.join(out, "report.md"), "w").write(env.get_template(TEMPLATE).render(**ctx))
    man = {"provenance": ctx["prov"], "figures": figs, "report": "report.md",
           "extra_tables": ["tables/11_test_vs_culver.csv"],
           "comparison_source": {"opv2v_test": test.provenance()["inputs"]},
           "note": "Every number is copied from the input analysis JSON files; nothing is recomputed."}
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(f"{inp.status_text}: report -> {os.path.join(out, 'report.md')} ({len(figs)} figures)")


if __name__ == "__main__":
    main()
