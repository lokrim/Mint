"""MINT-v0.0: deterministic receiver-ray evidence, per-sender/per-tile gating, UNKNOWN = keep.

UNCALIBRATED. `h_keep` and `h_remove` are raw scores in [0, 1] built from support ratios; they are
not probabilities and must not be reported as such (D-35, methodology report §7.2).

Per effect e of sender i (Y+ vs Y-(i), effects.py), with s = SUP / (SUP + TRAV) of the receiver's
own rays through the box core (rays.py / ground.py):
  ADD     (box only with i):    h_keep = 1 - s+        h_remove = s+
  REMOVE  (box only without i): h_keep = s-            h_remove = 1 - s-
  SHIFT   (box moved):          h_keep = max(0, s- - s+)   h_remove = max(0, s+ - s-)
Unit (i, u) collects every effect whose box centre lies in u in either version (D-22).
  status  KNOWN iff every effect box has >= n_min receiver rays and is not the receiver's own box;
          NO_EFFECT if the unit has no effect; otherwise UNKNOWN_NO_EVIDENCE / NOT_APPLICABLE_SELF.
  score   sum_e (h_keep - h_remove)  (a raw proxy for the sign of D)
  action  remove sender i in tile u iff status == KNOWN and score > theta; otherwise keep.
Inputs are receiver-side only: detector outputs, the receiver's scan, and its own pose (origin).
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Params:
    theta: float = 0.0
    n_min: int = 3
    variant: str = "std"          # ray count variant: "std" or "gnd" (ground-aware)


@dataclass
class Reliability:
    sender: int
    tile: tuple
    status: str
    h_keep: float | None
    h_remove: float | None
    score: float | None
    gate: bool
    is_probability: bool = False
    effects: list = field(default_factory=list)


def _n(r, variant):
    return r[variant]["SUP"] + r[variant]["TRAV"]


def _s(r, variant):
    n = _n(r, variant)
    return r[variant]["SUP"] / n if n else None


def effect_scores(e, variant="std"):
    sp = None if e["rays_plus"] is None else _s(e["rays_plus"], variant)
    sm = None if e["rays_minus"] is None else _s(e["rays_minus"], variant)
    if e["type"] == "ADD":
        return 1 - sp, sp
    if e["type"] == "REMOVE":
        return sm, 1 - sm
    return max(0.0, sm - sp), max(0.0, sp - sm)


def effect_status(e, p: Params):
    for r in (e["rays_plus"], e["rays_minus"]):
        if r is None:
            continue
        if r["self_box"]:
            return "NOT_APPLICABLE_SELF"
        if _n(r, p.variant) < p.n_min:
            return "UNKNOWN_NO_EVIDENCE"
    return "KNOWN"


def units(effects):
    u = {}
    for e in effects:
        for t in {tuple(t) for t in (e["tile_plus"], e["tile_minus"]) if t is not None}:
            u.setdefault((e["sender"], t), []).append(e)
    return u


def assess(effects, p: Params = Params()):
    """effects: list of effect dicts with receiver ray counts. Returns {(sender, tile): Reliability}."""
    out = {}
    for (i, t), effs in units(effects).items():
        st = [effect_status(e, p) for e in effs]
        if all(s == "KNOWN" for s in st):
            hk, hr = zip(*(effect_scores(e, p.variant) for e in effs))
            score = float(sum(hk) - sum(hr))
            out[(i, t)] = Reliability(i, t, "KNOWN", float(max(hk)), float(max(hr)), score, score > p.theta,
                                      effects=effs)
        else:
            status = "NOT_APPLICABLE_SELF" if "NOT_APPLICABLE_SELF" in st else "UNKNOWN_NO_EVIDENCE"
            out[(i, t)] = Reliability(i, t, status, None, None, None, False, effects=effs)
    return out


def gating_choice(rel):
    """{tile: frozenset(senders to remove)} for mint.fusion.compose / tile_include_masks."""
    ch = {}
    for (i, t), r in rel.items():
        if r.gate:
            ch.setdefault(t, set()).add(i)
    return {t: frozenset(s) for t, s in ch.items()}
