"""D-68 (amended) B-NORM-aware PGD: pgd_untargeted_stealth / pgd_remove_stealth (evaluation only).

Same objective, steps, step size (eps_k / 4), random start U(-eps_k, eps_k) and no-GT pseudo-labels as D-65
(src/mint/attacks/pgd_v3.py, reused unchanged). After the random start and after every step, per scale k,
the attacker's delta_k is replaced by its exact Euclidean projection onto
    box   lo = max(-eps_k, -f_k) <= delta_k <= hi = eps_k        (so f_k + delta_k >= 0)
    mean  mean(f_k + delta_k) <= bound_k = 0.95 * tau_k * mean|f_receiver,k|
(amendment 2: if the constraint is unreachable at any scale, mean(f_k + lo_k) > bound_k, the attack is not applied
on the frame: returns (None, ledger with reason 'stealth_infeasible'); the frame is scored as clean)
which is delta_k <- clip(delta_k - lambda_k, lo, hi) with lambda_k = 0 if the mean constraint holds, else the
smallest lambda_k >= 0 satisfying it (bisection, tolerance 1e-7 relative to the bracket). f_k >= 0 (ReLU), so
mean|f_k + delta_k| = mean(f_k + delta_k): the B-NORM ratio of the attacker stays <= 0.95 tau_k.
"""
import hashlib

import numpy as np
import torch

from mint.attacks import pgd_v3 as P

FAMILIES = ("pgd_untargeted_stealth", "pgd_remove_stealth")
BOUND_FRAC = 0.95
REL_TOL = 1e-7
ASSERT_TOL = 1e-6


class Infeasible(RuntimeError):
    pass


def base_family(fam):
    return fam[:-len("_stealth")]


def project(delta, f, eps, mean_bound, rel_tol=REL_TOL):
    """Exact projection of delta onto {lo <= d <= hi} with lo = max(-eps, -f), hi = eps, and mean(f + d) <= mean_bound.
    Works in float64; returns (projected delta in delta's dtype, lambda)."""
    d = delta.double()
    f64 = f.double()
    lo = torch.maximum(torch.full_like(f64, -eps), -f64)
    hi = torch.full_like(f64, eps)
    n = f64.numel()
    cap = mean_bound * n - float(f64.sum())                  # constraint: sum(d) <= cap
    x = torch.clamp(d, lo, hi)
    if float(x.sum()) <= cap:
        return x.to(delta.dtype), 0.0
    if float(lo.sum()) > cap:
        raise Infeasible(f"mean bound {mean_bound} below the smallest reachable mean {float((f64 + lo).mean())}")
    a, b = 0.0, float((d - lo).max())                        # at lambda = b every element sits at lo
    tol = rel_tol * max(b, 1e-30)
    while b - a > tol:
        m = 0.5 * (a + b)
        if float(torch.clamp(d - m, lo, hi).sum()) <= cap:
            b = m
        else:
            a = m
    return torch.clamp(d - b, lo, hi).to(delta.dtype), b


def feasibility(feats, a, eps, tau, bound_frac=BOUND_FRAC):
    """D-68 amendment 2: per scale, feasible iff mean(f_k + lo_k) <= bound_frac tau_k mean|f_receiver,k|
    (lo_k = max(-eps_k, -f_k)); the same float64 arithmetic as project()'s infeasibility test.
    Returns (all feasible, per-scale flags, per-scale lowest reachable ratio)."""
    ok, minr = [], []
    for k, f in enumerate(feats):
        f64 = f[a].double()
        lo = torch.maximum(torch.full_like(f64, -float(eps[k])), -f64)
        rec = float(f[0].abs().double().mean())
        mean_bound = bound_frac * float(tau[k]) * rec
        cap = mean_bound * f64.numel() - float(f64.sum())
        ok.append(not float(lo.sum()) > cap)
        minr.append(float((f64 + lo).mean()) / rec)
    return all(ok), ok, minr


def rng_for(family, r, scen, frame):
    h = hashlib.sha256(f"V3PGDS|{family}|{r}|{scen}|{frame}".encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "little"))


def ratios(feats, a):
    """Attacker / receiver mean|f| per scale (float64), as B-NORM computes it."""
    return [float(f[a].abs().double().mean() / f[0].abs().double().mean()) for f in feats]


def pgd_attack_stealth(model, feats, a, family, eps, tau, rng, score_thr, steps=P.STEPS, step_frac=P.STEP_FRAC,
                       bound_frac=BOUND_FRAC):
    """feats: clean per-scale [n, C, H, W]; eps, tau: per-scale lists. Returns (perturbed feats, ledger).
    Asserts f + delta >= 0, |delta| <= eps_k and ratio_k <= bound_frac * tau_k on the returned features."""
    assert family in FAMILIES and len(eps) == len(feats) == len(tau)
    feas, ok, minr = feasibility(feats, a, eps, tau, bound_frac)
    if not feas:                                    # D-68 amendment 2: attack not applied (scored as clean)
        return None, {"family": family, "applied": False, "reason": "stealth_infeasible", "attacker": a,
                      "eps": [float(e) for e in eps], "tau": [float(t) for t in tau], "bound_frac": bound_frac,
                      "feasible_by_scale": ok, "min_reachable_ratio": minr, "clean_ratio": ratios(feats, a)}
    fam0 = base_family(family)
    model.eval()
    req = [p.requires_grad for p in model.parameters()]
    for p in model.parameters():
        p.requires_grad_(False)
    base = [f[a].clone() for f in feats]
    mean_bound = [bound_frac * float(t) * float(f[0].abs().double().mean()) for t, f in zip(tau, feats)]
    lam_hist = [[] for _ in feats]

    def proj(d, k):
        x, lam = project(d, base[k], float(eps[k]), mean_bound[k])
        lam_hist[k].append(lam)
        return x

    def adv(d):
        return [torch.stack([f[j] if j != a else base[k] + d[k] for j in range(f.shape[0])], 0)
                for k, f in enumerate(feats)]

    try:
        with torch.no_grad():
            psm0, rm0 = P.heads_grad(model, feats)
            pos = torch.sigmoid(psm0) >= score_thr
        delta = [proj(torch.from_numpy(rng.uniform(-eps[k], eps[k], size=tuple(base[k].shape)).astype(np.float32)), k)
                 for k in range(len(feats))]
        hist = []
        for _ in range(steps):
            for d in delta:
                d.requires_grad_(True)
            psm, rm = P.heads_grad(model, adv(delta))
            obj = P.objective(psm, rm, pos, rm0, fam0)
            grads = torch.autograd.grad(obj, delta)
            hist.append(float(obj))
            with torch.no_grad():
                delta = [proj(d + step_frac * eps[k] * g.sign(), k) for k, (d, g) in enumerate(zip(delta, grads))]
        with torch.no_grad():
            new = adv(delta)
            psm, rm = P.heads_grad(model, new)
            final = float(P.objective(psm, rm, pos, rm0, fam0))
    finally:
        for p, q in zip(model.parameters(), req):
            p.requires_grad_(q)
    rat = ratios(new, a)
    for k, (f, d) in enumerate(zip(new, delta)):
        assert float(f[a].min()) >= 0.0, ("negative feature", k)
        assert float(d.abs().max()) <= eps[k] * (1 + ASSERT_TOL), ("L-inf", k)
        assert rat[k] <= bound_frac * tau[k] * (1 + ASSERT_TOL), ("stealth ratio", k, rat[k], bound_frac * tau[k])
    led = {"family": family, "applied": True, "attacker": a, "eps": [float(e) for e in eps], "steps": steps,
           "step_frac": step_frac, "bound_frac": bound_frac, "tau": [float(t) for t in tau],
           "objective_hist": [round(h, 5) for h in hist] + [round(final, 5)], "n_pseudo_pos": int(pos.sum()),
           "ratio": rat, "clean_ratio": ratios(feats, a),
           "lambda_active_steps": [int(sum(x > 0 for x in L)) for L in lam_hist],
           "lambda_final": [L[-1] for L in lam_hist],
           "linf_delta": [float(d.abs().max()) for d in delta],
           "mean_abs_delta_over_mean_abs_feat": [float(d.abs().mean() / (b.abs().mean() + 1e-12)) for d, b in zip(delta, base)]}
    return [x.detach() for x in new], led
