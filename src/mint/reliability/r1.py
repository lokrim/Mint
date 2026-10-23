"""MINT rule R1 "resolvable evidence" (E1 pre-registration, runs/20261023-E1/preregistration.json).

Gate a unit (sender i, tile u) only if the receiver-ray evidence is statistically resolvable.
Per effect, with the Wilson 95% interval [lo, hi] on each support ratio s = SUP / (SUP + TRAV)
of the receiver's own rays through the effect box (standard count):
  ADD     gates iff hi(s+) < 0.5                       useful iff lo(s+) > 0.5
  REMOVE  gates iff lo(s-) > 0.5                       useful iff hi(s-) < 0.5
  SHIFT   gates iff intervals disjoint and s+ < s-     useful iff intervals disjoint and s+ > s-
A KNOWN unit gates iff at least one effect gates and no effect is resolvably useful; otherwise keep.
UNKNOWN units (status as MINT-v0.0: any effect box with < 3 rays or the receiver's own box) = keep.

CAVEAT: rays through one box are spatially correlated (neighbouring beams hit the same surface),
so they are not independent Bernoulli trials. The Wilson interval is therefore a resolvability
margin on the ray counts, NOT a calibrated probability or confidence statement about harm.
R1 has no tunable threshold. Inputs are receiver-side only (detector outputs, own scan, own pose).
"""
import math

from mint.reliability.v0 import Params, Reliability, effect_status, gating_choice, units  # noqa: F401

Z95 = 1.959964


def wilson(k, n, z=Z95):
    """Wilson score interval for k successes in n trials; (lo, hi)."""
    if n <= 0:
        return 0.0, 1.0
    z2 = z * z
    c = (k + z2 / 2) / (n + z2)
    h = z / (n + z2) * math.sqrt(k * (n - k) / n + z2 / 4)
    return max(0.0, c - h), min(1.0, c + h)


def _ks(r, variant):
    return r[variant]["SUP"], r[variant]["SUP"] + r[variant]["TRAV"]


def effect_verdict(e, variant="std"):
    """'gate', 'useful' or 'none' for one KNOWN effect."""
    if e["type"] == "ADD":
        lo, hi = wilson(*_ks(e["rays_plus"], variant))
        return "gate" if hi < 0.5 else ("useful" if lo > 0.5 else "none")
    if e["type"] == "REMOVE":
        lo, hi = wilson(*_ks(e["rays_minus"], variant))
        return "gate" if lo > 0.5 else ("useful" if hi < 0.5 else "none")
    kp, np_ = _ks(e["rays_plus"], variant)
    km, nm = _ks(e["rays_minus"], variant)
    lp, hp = wilson(kp, np_)
    lm, hm = wilson(km, nm)
    if not (hp < lm or hm < lp):
        return "none"
    return "gate" if kp / np_ < km / nm else "useful"


def assess(effects, p: Params = Params()):
    """Same interface as v0.assess; score = #gating effects - #useful effects (diagnostic only)."""
    out = {}
    for (i, t), effs in units(effects).items():
        st = [effect_status(e, p) for e in effs]
        if all(s == "KNOWN" for s in st):
            v = [effect_verdict(e, p.variant) for e in effs]
            g = "gate" in v and "useful" not in v
            out[(i, t)] = Reliability(i, t, "KNOWN", None, None, float(v.count("gate") - v.count("useful")), g,
                                      effects=effs)
            out[(i, t)].verdicts = v
        else:
            status = "NOT_APPLICABLE_SELF" if "NOT_APPLICABLE_SELF" in st else "UNKNOWN_NO_EVIDENCE"
            out[(i, t)] = Reliability(i, t, status, None, None, None, False, effects=effs)
    return out
