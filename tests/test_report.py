"""Reporting pipeline (src/mint/report): status rules, incomplete-test refusal, no cache reads, numbers copied."""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from mint.report import tables as T  # noqa: E402
from mint.report.data import Inputs  # noqa: E402
from mint.report.figures import FIGURES  # noqa: E402
from mint.report.render import IncompleteFinalTest, build  # noqa: E402

DRY = os.path.join(ROOT, "runs/20261024-E5/dryrun_v3_2/n2")
H_V3 = os.path.join(ROOT, "runs/20261024-PGD/pgd_stealth_H_results.json")
H_V2 = os.path.join(ROOT, "runs/20261024-E5/H/e5a_H.json")
PREREG = os.path.join(ROOT, "runs/20261024-E5/preregistration_v3_2.json")
need = pytest.mark.skipif(not os.path.exists(os.path.join(DRY, "e5_v3.json")), reason="dev dry run not present")


def _as_final(tmp_path, complete):
    v3 = json.load(open(os.path.join(DRY, "e5_v3.json")))
    v3 = copy.deepcopy(v3)
    v3["label"] = "FINAL TEST (one-time), v3 analysis"
    if complete is None:
        v3.pop("completeness_check", None)
    else:
        v3["completeness_check"] = {"scenarios": [15, 15], "frames": [2066, 2066], "pass": complete}
    p = tmp_path / "e5_v3.json"
    json.dump(v3, open(p, "w"))
    return str(p)


@need
def test_dev_status_and_build(tmp_path):
    inp = Inputs(os.path.join(DRY, "e5_v3.json"), os.path.join(DRY, "e5_test.json"), PREREG, root=ROOT)
    assert inp.status == "DEVELOPMENT"
    man = build(inp, str(tmp_path), themes=("light",), dpi=60)
    rep = open(tmp_path / "report.md").read()
    assert "DEVELOPMENT / DRY RUN - not results" in rep and "{{" not in rep and "{%" not in rep
    assert len(man["figures"]) == len(FIGURES)
    for f in man["figures"]:
        assert os.path.exists(tmp_path / f["files"]["light_png"]) and os.path.exists(tmp_path / f["files"]["csv"])
        assert f["n_rows"] > 0, f["name"]


@need
@pytest.mark.parametrize("complete", [False, None])
def test_incomplete_final_test_refused(tmp_path, complete):
    inp = Inputs(_as_final(tmp_path, complete), None, PREREG, root=ROOT)
    assert inp.status == "INCOMPLETE"
    with pytest.raises(IncompleteFinalTest):
        build(inp, str(tmp_path / "out"), themes=("light",), dpi=60)
    assert not os.path.exists(tmp_path / "out" / "report.md")


@need
def test_complete_final_test_labelled_final(tmp_path):
    inp = Inputs(_as_final(tmp_path, True), None, PREREG, root=ROOT)
    assert inp.status == "FINAL"
    build(inp, str(tmp_path / "out"), themes=("light",), dpi=60)
    rep = open(tmp_path / "out" / "report.md").read()
    assert "**Status: FINAL TEST (one-time)**" in rep and "not** results of the final test" not in rep


def test_cache_paths_rejected():
    for p in ("runs/x/cache/a.json", "runs/x/v3extra/b.json", "runs/x/a.pkl.gz"):
        with pytest.raises(ValueError):
            Inputs(p)


@need
def test_numbers_are_copied_not_recomputed():
    inp = Inputs(os.path.join(DRY, "e5_v3.json"), os.path.join(DRY, "e5_test.json"), PREREG, root=ROOT)
    v3 = json.load(open(os.path.join(DRY, "e5_v3.json")))
    p = v3["point"]["global"]["mean_delta_orig|B-RAY"]
    ci = v3["bootstrap"]["global"]["block10"]["mean_delta_orig|B-RAY"]["ci95"]
    tab = T.headline(inp)
    assert f"{p * 100:+.2f}" in tab and f"[{ci[0] * 100:+.2f}, {ci[1] * 100:+.2f}]" in tab
    st = v3["criteria_v3"]["frame"]["R1_minus_BRAY"]["statement"]
    assert st in T.r1_minus_bray(inp)
    assert T.verdict(inp)["verdict"] == v3["criteria_v3"]["D-64"]["verdict"]


@pytest.mark.skipif(not os.path.exists(H_V3), reason="block-H development file not present")
def test_block_h_format_builds(tmp_path):
    inp = Inputs(H_V3, H_V2, PREREG, root=ROOT)
    assert inp.status == "DEVELOPMENT" and inp.n_scenarios() == 4
    build(inp, str(tmp_path), themes=("light",), dpi=60)
    rep = open(tmp_path / "report.md").read()
    assert "not recorded (development file)" in rep            # no completeness check in a dev file


@need
def test_all_agent_strata(tmp_path):
    """e5_analyze.by_agents uses strata "2", "3", "4+" (the dev files only have "2"; the test has all three)."""
    v2 = json.load(open(os.path.join(DRY, "e5_test.json")))
    g = v2["by_agents"]["2"]
    v2["by_agents"] = {"4+": dict(g, frames=101), "2": g, "3": dict(g, frames=500)}
    p = tmp_path / "e5_test.json"
    json.dump(v2, open(p, "w"))
    inp = Inputs(os.path.join(DRY, "e5_v3.json"), str(p), PREREG, root=ROOT)
    build(inp, str(tmp_path / "out"), themes=("light",), dpi=60)
    import csv
    rows = list(csv.DictReader(open(tmp_path / "out" / "tables" / "10_by_agents.csv")))
    assert [r["n_agents"] for r in rows][::len({r["method"] for r in rows})] == ["2", "3", "4+"]


def test_notebook_is_valid():
    nbformat = pytest.importorskip("nbformat")
    sys.path.insert(0, os.path.join(ROOT, "notebooks"))
    import build_final_report_notebook as B
    nb = B.build()
    nbformat.validate(nb)
    src = "\n".join(c.source for c in nb.cells)
    assert "cache" not in src.replace("cache/", "").lower() or "never" in src
    assert "INCOMPLETE" in src and len([c for c in nb.cells if c.cell_type == "code"]) >= len(FIGURES)
