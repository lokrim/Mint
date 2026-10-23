"""E5a: B-RAY, ego-only, R1-noREMOVE, E5 metrics/bootstrap and the final-test allowlist/budget."""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e5_analyze as X  # noqa: E402  (installs shims, paths)
import e5_stream as S  # noqa: E402
from mint.reliability import baselines as BL  # noqa: E402
from mint.reliability import r1, v0  # noqa: E402


def _box(cx, cy, l=3.9, w=1.6, h=1.56, zb=-1.9):
    x0, x1, y0, y1 = cx - l / 2, cx + l / 2, cy - w / 2, cy + w / 2
    top = [[x1, y0], [x1, y1], [x0, y1], [x0, y0]]
    return np.array([[*p, zb] for p in top] + [[*p, zb + h] for p in top], np.float64)


def _wall(x=15.0):
    ys, zs = np.meshgrid(np.linspace(-10, 10, 400), np.linspace(-1.8, 1.0, 40))
    return np.stack([np.full(ys.size, x), ys.ravel(), zs.ravel()], 1)


def _rays(sup, trav, self_box=False):
    return {"std": {"SUP": sup, "TRAV": trav, "OCC": 0, "candidates": sup + trav},
            "gnd": {"SUP": sup, "TRAV": trav, "OCC": 0, "TRAV_GROUND": 0, "candidates": sup + trav},
            "self_box": self_box, "range_m": 10.0}


def _eff(typ, plus=None, minus=None, tile=(1, 1), sender=1):
    return {"sender": sender, "type": typ, "tile_plus": tile if plus else None, "tile_minus": tile if minus else None,
            "rays_plus": None if plus is None else _rays(*plus), "rays_minus": None if minus is None else _rays(*minus),
            "plus": None, "minus": None}


# ------------------------------------------------------------------ B-RAY
def test_bray_verdicts():
    assert BL.b_ray_verdict({"SUP": 0, "TRAV": 0, "self_box": True}) == "keep_self"
    assert BL.b_ray_verdict({"SUP": 0, "TRAV": 2, "self_box": False}) == "keep_unknown"
    assert BL.b_ray_verdict({"SUP": 0, "TRAV": 10, "self_box": False}) == "drop"       # Wilson hi 0.28
    assert BL.b_ray_verdict({"SUP": 5, "TRAV": 5, "self_box": False}) == "keep"
    assert BL.b_ray_verdict({"SUP": 0, "TRAV": 3, "self_box": False}) == "keep"        # Wilson hi 0.56: not resolvable


def test_bray_equals_r1_add_gate():
    """B-RAY drops a box iff R1 would gate an ADD effect with the same (KNOWN) counts."""
    rng = np.random.default_rng(0)
    for _ in range(500):
        n = int(rng.integers(0, 60))
        k = int(rng.integers(0, n + 1))
        e = _eff("ADD", plus=(k, n - k))
        known = v0.effect_status(e, v0.Params()) == "KNOWN"
        gate = known and r1.effect_verdict(e) == "gate"
        assert (BL.b_ray_verdict({"SUP": k, "TRAV": n - k, "self_box": False}) == "drop") == gate


def test_bray_geometry_and_filter():
    pts = _wall(15.0)
    before, at, behind, ego = _box(10.0, 0.0), _box(15.0, 0.0), _box(22.0, 0.0), _box(0.0, 0.0)
    boxes = np.stack([before, at, behind, ego]).astype(np.float32)
    scores = np.array([0.9, 0.8, 0.7, 0.6], np.float32)
    kb, ks, verd, rays = BL.b_ray(boxes, scores, pts=pts)
    assert verd == ["drop", "keep", "keep_unknown", "keep_self"]
    assert len(kb) == 3 and np.allclose(ks, [0.8, 0.7, 0.6])
    # precomputed rays give the same result; std counts are R1's (classify_points)
    kb2, _, verd2, _ = BL.b_ray(boxes, scores, rays=rays)
    assert verd2 == verd and np.array_equal(kb2, kb)
    assert BL.b_ray(np.zeros((0, 8, 3)), np.zeros(0), pts=pts)[2] == []


# ------------------------------------------------------------------ ego-only
def test_ego_only_subset():
    cands = {frozenset(): "all", frozenset([1]): "m1", frozenset([2]): "m2", frozenset([1, 2]): "ego"}
    assert BL.ego_only(cands, 3) == "ego"
    assert BL.ego_only({frozenset(): "ego"}, 1) == "ego"


# ------------------------------------------------------------------ R1-noREMOVE
def test_noremove_never_gates_on_remove():
    rm_gate = [_eff("REMOVE", minus=(20, 0))]                     # lo(s-) > 0.5 -> R1 gates
    assert r1.assess(rm_gate)[(1, (1, 1))].gate
    assert not BL.assess_noremove(rm_gate)[(1, (1, 1))].gate


def test_noremove_keeps_mirror_and_add():
    add_gate = _eff("ADD", plus=(0, 20))
    rm_useful = _eff("REMOVE", minus=(0, 20))                    # hi(s-) < 0.5 -> useful (mirror)
    for effs, want in (([add_gate], True), ([add_gate, rm_useful], False)):
        assert r1.assess(effs)[(1, (1, 1))].gate == want
        assert BL.assess_noremove(effs)[(1, (1, 1))].gate == want
    shift = _eff("SHIFT", plus=(0, 20), minus=(20, 0))
    assert BL.assess_noremove([shift])[(1, (1, 1))].gate == r1.assess([shift])[(1, (1, 1))].gate is True


def test_noremove_equals_r1_without_remove_gates():
    rng = np.random.default_rng(1)
    for _ in range(300):
        effs = []
        for _ in range(int(rng.integers(1, 4))):
            t = str(rng.choice(["ADD", "REMOVE", "SHIFT"]))
            c = lambda: (int(rng.integers(0, 15)), int(rng.integers(0, 15)))
            effs.append(_eff(t, plus=c() if t != "REMOVE" else None, minus=c() if t != "ADD" else None,
                             tile=(int(rng.integers(0, 2)), 0)))
        a, b = r1.assess(effs), BL.assess_noremove(effs)
        assert a.keys() == b.keys()
        for k in a:
            assert a[k].status == b[k].status
            rv = [v for e, v in zip(a[k].effects, getattr(a[k], "verdicts", [])) if e["type"] == "REMOVE" and v == "gate"]
            if not rv:
                assert a[k].gate == b[k].gate
            else:
                assert not b[k].gate or "gate" in [v for e, v in zip(b[k].effects, b[k].verdicts) if e["type"] != "REMOVE"]


# ------------------------------------------------------------------ metrics / bootstrap
def _F(conds, methods, n_frames=40, seed=0):
    rng = np.random.default_rng(seed)
    F = {}
    for c in conds:
        for m in methods:
            F[(c, m)] = []
            for j in range(n_frames):
                tp = rng.integers(0, 2, 5)
                F[(c, m)].append((tp, 1 - tp, 6))
    return F


def test_metrics_consistency():
    conds = ("clean",) + X.ORIG
    F = _F(conds, X.METHODS)
    idx = list(range(40))
    m = X.metrics(F, idx, conds)
    for a, b in X.PAIRS:
        for c in conds:
            assert m[f"paired|{a}-{b}|{c}"] == pytest.approx(m[f"delta|{a}|{c}"] - m[f"delta|{b}|{c}"])
        assert m[f"paired_mean_orig|{a}-{b}"] == pytest.approx(m[f"mean_delta_orig|{a}"] - m[f"mean_delta_orig|{b}"])
    # identical method -> zero deltas
    G = dict(F)
    for c in conds:
        G[(c, "R1")] = F[(c, "undefended")]
    assert X.metrics(G, idx, conds)["mean_delta_orig|R1"] == 0.0


def test_bootstrap_blocks():
    conds = ("clean",) + X.ORIG
    F = _F(conds, X.METHODS)
    keys = [("a", j) for j in range(25)] + [("b", j) for j in range(15)]
    bs = X.bootstrap(F, keys, conds, "scenario", n_boot=5)
    b10 = X.bootstrap(F, keys, conds, "block10", n_boot=5)
    assert bs["_blocks"] == 2 and b10["_blocks"] == 3 + 2
    sub = [j for j in range(40) if j >= 25]
    assert X.bootstrap(F, keys, conds, "scenario", subset=sub, n_boot=3)["_scenarios"] == 1


def test_strata():
    assert [X.stratum_of(n) for n in (1, 2, 3, 4, 5)] == ["1", "2", "3", "4+", "4+"]


def test_criteria_rule():
    def out(lo, hi, rl_hi, p_lo, p_hi):
        ci = lambda a, b: {"ci95": [a, b]}
        return {"point": {"mean_delta_orig|R1": 0.01, "rel_loss|R1": 0.002, "paired_mean_orig|R1-B-RAY": 0.0},
                "bootstrap_scenario": {"mean_delta_orig|R1": ci(lo, hi), "rel_loss|R1": ci(-0.001, rl_hi),
                                       "paired_mean_orig|R1-B-RAY": ci(p_lo, p_hi)},
                "bootstrap_block10": {"mean_delta_orig|R1": ci(lo, hi), "rel_loss|R1": ci(-0.001, rl_hi),
                                      "paired_mean_orig|R1-B-RAY": ci(p_lo, p_hi)}}
    c = X.criteria(out(0.001, 0.02, 0.01, -0.01, 0.01))
    assert c["success"] and c["key_secondary_R1_minus_BRAY"]["ci_includes_0"]
    assert "not established" in c["key_secondary_R1_minus_BRAY"]["required_statement"]
    assert not X.criteria(out(-0.001, 0.02, 0.005, 0.001, 0.01))["success"]
    assert not X.criteria(out(0.001, 0.02, 0.0101, 0.001, 0.01))["success"]
    assert X.criteria(out(0.001, 0.02, 0.005, 0.001, 0.01))["key_secondary_R1_minus_BRAY"]["required_statement"] is None


# ------------------------------------------------------------------ final-test stream safeguards
def test_allowlist():
    assert len(S.TEST_SCENARIOS) == 15 and not set(S.EXCLUDED) & set(S.TEST_SCENARIOS)
    S.check_allowlist(list(S.TEST_SCENARIOS))
    for bad in (["2021_08_23_12_58_19"], ["2021_08_22_13_37_16"], [S.TEST_SCENARIOS[0]] * 2, []):
        with pytest.raises(SystemExit):
            S.check_allowlist(bad)


def test_budget_and_sizes():
    sz = S.s1_sizes()
    assert all(v is not None for v in sz.values())
    ok, proj = S.budget_ok(0, sz, list(S.TEST_SCENARIOS))
    assert ok and 20.0e9 < proj < S.BYTE_BUDGET
    assert not S.budget_ok(2.0e9, sz, list(S.TEST_SCENARIOS))[0]
    assert max(sz.values()) <= S.RAW_CAP


def test_stream_refuses_without_approval(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["e5_stream.py", "--run_dir", "runs/_never"])
    with pytest.raises(SystemExit, match="approval"):
        S.main()
    monkeypatch.setattr(sys, "argv", ["e5_stream.py", "--run_dir", "runs/_never", "--byte_budget", "23000000000",
                                      "--user_approved"])
    with pytest.raises(SystemExit, match="budget"):
        S.main()
    assert not os.path.exists(os.path.join(ROOT, "runs/_never"))
