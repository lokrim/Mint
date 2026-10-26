"""Markdown tables and checks for the report. Every number is copied from the analysis summaries.

The 'descriptive expected-outcome checks' apply the operational rules written in the preregistration
(pgd_families.expected_outcomes.operational_checks, stated before any PGD run). They are NOT criteria."""
from .data import DEF_NAME, DEFS, METHOD_NAME, ORIG
from .figures import cond_label, d70_conditions

PTS = 100.0


def f_pts(v, nd=2):
    return "n/a" if v is None else f"{v * PTS:+.{nd}f}"


def f_ci(ci, scale=PTS, nd=2):
    return "n/a" if ci is None else f"[{ci[0] * scale:+.{nd}f}, {ci[1] * scale:+.{nd}f}]"


def f_pct(v, nd=1):
    return "n/a" if v is None else f"{v * 100:.{nd}f}%"


def f_p(v):
    return "n/a" if v is None else (f"{v:.4f}" if v >= 0.0001 else f"{v:.1e}")


def yes(v):
    return "n/a" if v is None else ("yes" if v else "no")


def md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------------- tables
def headline(inp):
    rows = []
    for m in inp.methods:
        r = [METHOD_NAME[m]]
        for d in DEFS:
            s = inp.stat(d, f"mean_delta_orig|{m}")
            r += [f_pts(s["point"]), f_ci(s["ci_scenario"]), f_ci(s["ci_block10"])]
        rows.append(r)
    h = ["Method"] + [f"{lab} {d}" for d in DEFS for lab in ("ΔAP@0.7", "95% CI scen.", "95% CI 10-frame")]
    return md(h, rows)


def per_family(inp, d):
    rows = []
    for c in inp.conditions:
        r = [cond_label(c, inp.prereg)]
        for m in inp.methods:
            s = inp.stat(d, f"delta|{m}|{c}")
            r.append(f"{f_pts(s['point'])} {f_ci(s['ci_scenario'])}" if s["point"] is not None else "n/a")
        rows.append(r)
    return md(["Condition"] + [METHOD_NAME[m] for m in inp.methods], rows)


def clean_cost(inp):
    rows = []
    for m in inp.methods:
        r = [METHOD_NAME[m]]
        for d in DEFS:
            s = inp.stat(d, f"rel_loss|{m}")
            r += [f_pct(s["point"], 2), f_ci(s["ci_scenario"], 100, 2)]
        rows.append(r)
    return md(["Method"] + [f"{lab} {d}" for d in DEFS for lab in ("rel. loss", "95% CI scen. (%)")], rows)


def absolute_ap(inp, d):
    ap = (inp.v3.get("AP") or {}).get(d) or {}
    ms = ["undefended"] + inp.methods
    rows = [[cond_label(c, inp.prereg)] + [("n/a" if (ap.get(c) or {}).get(m) is None
                                            else f"{ap[c][m]['AP@0.7']:.4f}") for m in ms] for c in inp.conditions]
    return md(["Condition"] + [METHOD_NAME[m] for m in ms], rows)


def criteria(inp):
    cv = inp.v3.get("criteria_v3") or {}
    rows = []
    for d in DEFS:
        c = cv.get(d)
        if not c:
            continue
        co = c.get("co_test_vs_no_defense", {})
        b, r = co.get("B-RAY", {}), co.get("R1", {})
        cl = (c.get("clean_rel_loss") or {}).get("B-RAY", {})
        rows.append([DEF_NAME[d], f_pts(b.get("point")), f_p(b.get("p_one_sided")), yes((b.get("holm") or {}).get("reject")),
                     f_pts(r.get("point")), f_p(r.get("p_one_sided")), yes((r.get("holm") or {}).get("reject")),
                     f_ci(cl.get("ci95_scenario"), 100, 2), yes(c.get("B-RAY_clean_ci_hi_le_0.01")), yes(c.get("pass"))])
    return md(["AP definition", "B-RAY ΔAP", "B-RAY p (1-sided)", "B-RAY Holm reject", "R1 ΔAP", "R1 p",
               "R1 Holm reject", "B-RAY clean loss CI (%)", "clean CI high ≤ 1%", "v2 rule passes"], rows)


def verdict(inp):
    d64 = (inp.v3.get("criteria_v3") or {}).get("D-64") or {}
    st = d64.get("R1_minus_BRAY_statements") or {}
    return {"verdict": d64.get("verdict"), "success": d64.get("success"), "pass_frame": d64.get("pass_frame_order"),
            "pass_global": d64.get("pass_global"), "r1_statements": st,
            "r1_ap_dependent": d64.get("R1_minus_BRAY_AP_definition_dependent")}


def r1_minus_bray(inp):
    cv = inp.v3.get("criteria_v3") or {}
    rows = []
    for d in DEFS:
        x = (cv.get(d) or {}).get("R1_minus_BRAY") or {}
        rows.append([DEF_NAME[d], f_pts(x.get("point")), f_ci(x.get("ci95_scenario")), f_ci(x.get("ci95_block10")),
                     f"“{x.get('statement', 'n/a')}”"])
    return md(["AP definition", "R1 − B-RAY (pts)", "95% CI scen.", "95% CI 10-frame", "Pre-registered statement"], rows)


def pgd(inp):
    flags = inp.v3.get("B-NORM_flags") or {}
    by = inp.v3.get("pgd_by_scenario") or {}
    ms = [m for m in ("B-RAY", "R1", "R1_noREMOVE", "B-NORM", "ego_only") if m in inp.methods]
    rows = []
    for c in inp.pgd_conditions:
        tot = (by.get(c) or {}).get("total") or {}
        r = [cond_label(c, inp.prereg)]
        for d in DEFS:
            r.append(f_pts(inp.point(d, f"attack_loss|{c}")))
        for m in ms:
            r.append(" / ".join("n/a" if inp.point(d, f"recovery|{m}|{c}") is None else
                                f"{inp.point(d, f'recovery|{m}|{c}'):.2f}" for d in DEFS))
        r += [f_pct((flags.get(c) or {}).get("catch_rate"), 0),
              f"{tot.get('infeasible', 'n/a')}/{tot.get('frames_with_sender', 'n/a')}",
              f"{tot.get('realized', 'n/a')}/{tot.get('applied', 'n/a')}"]
        rows.append(r)
    h = (["Condition", "attack loss global", "attack loss frame"] + [f"recovery {METHOD_NAME[m]} (global / frame)" for m in ms]
         + ["B-NORM catch", "stealth-infeasible / frames with sender", "realized / applied"])
    return md(h, rows)


def realized_only(inp, d):
    ro = inp.v3.get("realized_only") or {}
    ms = [m for m in inp.methods]
    rows = []
    for c in inp.conditions:
        x = ro.get(c)
        if not x or not x.get("frames"):
            if x is not None:
                rows.append([cond_label(c, inp.prereg), 0, "n/a"] + ["n/a"] * len(ms))
            continue
        y = x.get(d) or {}
        rows.append([cond_label(c, inp.prereg), x["frames"], f_pts(y.get("attack_loss"))] +
                    [("n/a" if not y.get(m) else f"{f_pts(y[m].get('dAP@0.7'))} ({'n/a' if y[m].get('recovery') is None else format(y[m]['recovery'], '.2f')})")
                     for m in ms])
    return md(["Condition", "realized frames", "attack loss"] + [f"{METHOD_NAME[m]} ΔAP (recovery)" for m in ms], rows)


def checks(inp):
    """Procedural checks recorded in the analysis output."""
    out = []
    cc = inp.v3.get("completeness_check")
    if cc:
        out.append(["Completeness (scenarios, frames)", f"{cc['scenarios'][0]}/{cc['scenarios'][1]} scenarios, "
                    f"{cc['frames'][0]}/{cc['frames'][1]} frames", yes(cc.get("pass"))])
    else:
        out.append(["Completeness (scenarios, frames)", "not recorded (development file)", "n/a"])
    cons = inp.v3.get("consistency_vs_frozen_v2")
    out.append(["Frame-order v3 = frozen v2 analysis", "4 statistics, point and scenario CI",
                yes(cons.get("identical")) if cons else "n/a"])
    if inp.v2 is not None:
        diff = inp.v2.get("numpy_ap_vs_opencood_max_abs_diff")
        out.append(["NumPy AP vs OpenCOOD AP", f"max abs. difference {diff:.1e}" if diff is not None else "n/a",
                    yes(diff is not None and diff < 1e-9) if diff is not None else "n/a"])
        sc = inp.v2.get("scenarios") or []
        if sc and isinstance(sc[0], dict) and "compose_all_identical" in sc[0]:
            out.append(["Compose checks identical (all scenarios)", f"{len(sc)} scenarios",
                        yes(all(s.get("compose_all_identical") for s in sc))])
    return md(["Check", "Detail", "Passed"], out)


def expected_outcome_checks(inp):
    """Descriptive application of the pre-registered operational checks (not criteria)."""
    pr = inp.prereg or {}
    oc = (((pr.get("pgd_families") or {}).get("expected_outcomes") or {}).get("operational_checks")) or {}
    if not oc:
        return None
    flags = inp.v3.get("B-NORM_flags") or {}
    rows = []
    for c in inp.pgd_conditions:
        rec = [inp.point(d, f"recovery|B-RAY|{c}") for d in DEFS]
        bray = "n/a" if any(v is None for v in rec) else yes(all(v < 0.10 for v in rec))
        if "remove" in c:
            lows = [((inp.stat(d, f"delta|R1|{c}")["ci_scenario"]) or (None,))[0] for d in DEFS]
            r1 = "n/a" if any(v is None for v in lows) else yes(all(v > 0 for v in lows))
        else:
            r1 = "not applicable"
        if "stealth" in c:
            cr = (flags.get(c) or {}).get("catch_rate")
            bn = "n/a" if cr is None else yes(cr <= 0.05)
        else:
            bn = "not applicable"
        rows.append([cond_label(c, inp.prereg), bray, r1, bn])
    return md(["Condition", f"B-RAY ≈ 0 ({oc.get('B-RAY approx 0', '')})", f"R1 > 0 ({oc.get('R1 > 0', '')})",
               f"B-NORM ≤ 5% ({oc.get('B-NORM <= 5%', '')})"], rows)


def d70_note(inp):
    c = sorted(d70_conditions(inp.prereg))
    if not c:
        return None
    lab = ((inp.prereg.get("pgd_families") or {}).get("D-70_strong_level") or {}).get("label", "")
    return f"† {', '.join(c)}: {lab} (D-70, secondary; never used for a criterion)."


ORIG_TEXT = ", ".join(ORIG)
