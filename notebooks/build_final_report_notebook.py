"""Generate notebooks/final_report.ipynb and optionally execute a copy against given inputs.

  # (re)generate the notebook (inputs default to the block-H development files):
  .venv-report/bin/python notebooks/build_final_report_notebook.py
  # execute a copy against any inputs (saved next to the report outputs):
  .venv-report/bin/python notebooks/build_final_report_notebook.py --execute \
      --v3 runs/20261024-E5v3/e5_v3.json --v2 runs/20261024-E5v3/e5_test.json --out runs/20261024-E5v3/report

The notebook reads only the analysis summaries (never cache/ or v3extra/) and stops on an incomplete final test.
Use .venv-report (notebook tooling), not .venv (the frozen analysis environment).
"""
import argparse
import os
import sys
import time

import nbformat as nbf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from mint.report.figures import FIGURES  # noqa: E402
NB = os.path.join(ROOT, "notebooks", "final_report.ipynb")
DEV_V3 = "runs/20261024-PGD/pgd_stealth_H_results.json"
DEV_V2 = "runs/20261024-E5/H/e5a_H.json"


def cells(v3, v2, prereg):
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    c = [md("# MINT final test (E5, OPV2V): results notebook\n\n"
            "Reads **only** the two analysis summaries (`e5_v3.json` from `v3_analyze`, `e5_test.json` from the frozen "
            "v2 `e5_analyze`) and shows every pre-registered statistic, figure and check. Nothing is recomputed; the "
            "numbers are those in the files. The status banner says whether these are final-test results or "
            "development numbers. An incomplete final test stops the notebook (pre-registered rule: no AP or "
            "criteria on partial results).\n\n"
            "To point it at the final test, change the paths in the next cell to `runs/20261024-E5v3/e5_v3.json` and "
            "`runs/20261024-E5v3/e5_test.json`."),
         code(f"# Inputs (relative to the repository root)\nV3 = {v3!r}\nV2 = {v2!r}\nPREREG = {prereg!r}\n",
              metadata={"tags": ["parameters"]}),
         code("import os, sys, time, platform\n"
              "from IPython.display import Markdown, display\n"
              "ROOT = os.path.abspath('..') if os.path.basename(os.getcwd()) == 'notebooks' else os.getcwd()\n"
              "sys.path.insert(0, os.path.join(ROOT, 'src'))\n"
              "import io\nimport matplotlib.pyplot as plt\nfrom IPython.display import Image\n"
              "from mint.report import style, tables as T\n"
              "from mint.report.data import Inputs, DEFS, DEF_NAME\n"
              "from mint.report.figures import FIGURES\n"
              "T0 = time.time()\n"
              "inp = Inputs(os.path.join(ROOT, V3), os.path.join(ROOT, V2) if V2 else None,\n"
              "             os.path.join(ROOT, PREREG) if PREREG else None, root=ROOT)\n"
              "if inp.status == 'INCOMPLETE':\n"
              "    raise SystemExit('STOP: the final-test analysis is flagged incomplete; no AP or criteria on partial results.')\n"
              "display(Markdown(f'> **Status: {inp.status_text}**  \\n> {inp.label}'))"),
         md("## Provenance"),
         code("p = inp.provenance()\n"
              "rows = [[k, f\"`{v['path']}`\", f\"`{v['sha256'][:16]}...`\"] for k, v in p['inputs'].items()]\n"
              "rows += [['git HEAD', f\"`{p['git_head']}`\", ''], ['frozen code commit', f\"`{p['frozen_code_commit']}`\", ''],\n"
              "         ['scenarios / frames', f'{inp.n_scenarios()} / {inp.n_frames()}', '']]\n"
              "display(Markdown(T.md(['item', 'value', 'sha256'], rows)))"),
         md("## Procedural checks"),
         code("display(Markdown(T.checks(inp)))"),
         md("## Pre-registered verdict (D-64) and key secondary"),
         code("v = T.verdict(inp)\n"
              "display(Markdown(f\"**Verdict:** {v['verdict']}  \\nv2 rule, global-ranking AP: {v['pass_global']}; "
              "frame-order AP: {v['pass_frame']}\"))\n"
              "display(Markdown(T.criteria(inp)))\n"
              "display(Markdown(T.r1_minus_bray(inp)))"),
         md("## Headline table"),
         code("display(Markdown(T.headline(inp)))\ndisplay(Markdown(T.clean_cost(inp)))"),
         md("## Figures\n\nEach figure is drawn by the same function that writes the report figures; the table of "
            "plotted values is shown under it (`rows`).")]
    for name, num, _, title, caption in FIGURES:
        c.append(md(f"### Figure {num}. {title}\n\n{caption}"))
        c.append(code(f"t = style.apply('light')\n"
                      f"fn = dict((n, f) for n, _, f, _, _ in FIGURES)[{name!r}]\n"
                      f"fig, rows = fn(inp, t)\n"
                      f"buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=110, bbox_inches='tight'); plt.close(fig)\n"
                      f"display(Image(buf.getvalue()))\n"
                      f"print(f'{{len(rows)}} plotted values; first rows:'); [print(r) for r in rows[:4]]"))
    c += [md("## Per-condition tables"),
          code("for d in DEFS:\n    display(Markdown(f'**{DEF_NAME[d]}**'))\n    display(Markdown(T.per_family(inp, d)))"),
          md("## PGD, B-NORM and descriptive expected-outcome checks"),
          code("if inp.pgd_conditions:\n    display(Markdown(T.pgd(inp)))\n    e = T.expected_outcome_checks(inp)\n"
               "    display(Markdown(e or 'no operational checks in the preregistration'))\n"
               "    n = T.d70_note(inp)\n    display(Markdown(n)) if n else None"),
          md("## Realized-only effects"),
          code("for d in DEFS:\n    display(Markdown(f'**{DEF_NAME[d]}**'))\n    display(Markdown(T.realized_only(inp, d)))"),
          md("## Interpretation (AUTHOR)\n\n*To be written after reading the cells above. Keep to what the numbers "
             "support; quote the pre-registered statements as emitted.*"),
          md("## Run provenance"),
          code("import matplotlib, numpy, jinja2\n"
               "print('python', platform.python_version(), '| numpy', numpy.__version__, '| matplotlib', matplotlib.__version__,\n"
               "      '| jinja2', jinja2.__version__)\n"
               "print('platform', platform.platform())\n"
               "print('wall time %.1f s' % (time.time() - T0))")]
    return c


def build(v3=DEV_V3, v2=DEV_V2, prereg="runs/20261024-E5/preregistration_v3_2.json"):
    nb = nbf.v4.new_notebook()
    nb.cells = cells(v3, v2, prereg)
    for i, c in enumerate(nb.cells):              # fixed ids: regenerating the notebook gives no spurious diff
        c["id"] = f"cell-{i:02d}"
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3 (.venv-report)", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    return nb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v3", default=DEV_V3)
    ap.add_argument("--v2", default=DEV_V2)
    ap.add_argument("--prereg", default="runs/20261024-E5/preregistration_v3_2.json")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--out", default=None, help="folder for the executed copy (default: next to the notebook)")
    a = ap.parse_args()
    nbf.write(build(), NB)
    print("written", os.path.relpath(NB, ROOT))
    if a.execute:
        from nbclient import NotebookClient
        nb = build(a.v3, a.v2, a.prereg)
        t0 = time.time()
        NotebookClient(nb, timeout=600, kernel_name="python3",
                       resources={"metadata": {"path": os.path.join(ROOT, "notebooks")}}).execute()
        out = a.out or os.path.join(ROOT, "notebooks")
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, "final_report_executed.ipynb")
        nbf.write(nb, p)
        print(f"executed in {time.time() - t0:.0f}s -> {os.path.relpath(p, ROOT)}")


if __name__ == "__main__":
    main()
