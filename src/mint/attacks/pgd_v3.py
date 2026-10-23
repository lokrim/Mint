"""D-65 PGD feature attacks (evaluation only; never a method input).

Threat model: white-box, one attacker (sender a = 1) perturbs its OWN intermediate features at every
fusion scale k, L-inf bound eps_k = r * sigma_k (sigma_k = std of scale-k sender features on clean block-H
frames, recorded in runs/<date>-PGD/plan.json). Perturbed features are projected back onto the feature
domain (>= 0, the backbone blocks end in ReLU). PGD: random start U(-eps_k, eps_k), `steps` sign-gradient
ascent steps of size eps_k / 4, projection after every step, the final iterate is the attack.

No ground truth: pseudo-labels come from the clean fused output (Y+). Positive anchors = anchors whose
clean score is >= the post-processor's score threshold (the pre-NMS set Y+ is selected from); their clean
regression values are the regression targets.
  pgd_untargeted  maximise detection loss vs Y+: BCE(cls, pos) mean over positives + BCE(cls, neg) mean over
                  negatives + smooth-L1(reg - reg_clean) mean over positives
  pgd_remove      minimise the scores of Y+ boxes: maximise BCE(cls, label 1) mean over positives

Differentiable copy of the frozen AttFuse path (attfuse_parts.fuse_scale / decode are no_grad); a test
checks it equals the frozen path on clean features.
"""
import hashlib
import math

import numpy as np
import torch
import torch.nn.functional as F

FAMILIES = ("pgd_untargeted", "pgd_remove")
STEPS = 10
STEP_FRAC = 0.25


def fuse_scale_grad(x):
    """Same math as attfuse_parts.fuse_scale(x, None)[0], with gradients."""
    n, c, h, w = x.shape
    v = x.reshape(n, c, h * w)
    scores = torch.einsum("cp,ncp->pn", v[0], v) / math.sqrt(c)
    attn = torch.softmax(scores, dim=1)
    return torch.einsum("pn,ncp->cp", attn, v).reshape(c, h, w)


def heads_grad(model, feats):
    """psm, rm of the fused output (batch dim 1), with gradients. Same ops as attfuse_parts.decode."""
    bb = model.backbone
    fused = [fuse_scale_grad(f) for f in feats]
    ups = [bb.deblocks[i](f.unsqueeze(0)) for i, f in enumerate(fused)]
    x = torch.cat(ups, dim=1) if len(ups) > 1 else ups[0]
    if len(bb.deblocks) > len(bb.blocks):
        x = bb.deblocks[-1](x)
    return model.cls_head(x), model.reg_head(x)


def objective(psm, rm, pos, rm_clean, family):
    """Value to MAXIMISE. pos: bool like psm (positive anchors); rm_clean: clean regression map."""
    z = psm
    lp = -F.logsigmoid(z[pos]).mean() if pos.any() else z.sum() * 0
    if family == "pgd_remove":
        return lp
    if family != "pgd_untargeted":
        raise ValueError(family)
    ln = -F.logsigmoid(-z[~pos]).mean() if (~pos).any() else z.sum() * 0
    if pos.any():
        # rm: [1, A*7, H, W]; positive anchor a at (h, w) owns channels a*7 .. a*7+6
        na = z.shape[1]
        r = rm.reshape(1, na, 7, *rm.shape[2:])
        rc = rm_clean.reshape(1, na, 7, *rm.shape[2:])
        m = pos.unsqueeze(2).expand_as(r)
        lr = F.smooth_l1_loss(r[m], rc[m], reduction="mean")
    else:
        lr = z.sum() * 0
    return lp + ln + lr


def rng_for(family, r, scen, frame):
    h = hashlib.sha256(f"V3PGD|{family}|{r}|{scen}|{frame}".encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "little"))


def pgd_attack(model, feats, a, family, eps, rng, score_thr, steps=STEPS, step_frac=STEP_FRAC):
    """feats: list over scales of clean [n, C_k, H_k, W_k]; eps: list of per-scale bounds.
    Returns (perturbed feats, ledger). Only row a changes."""
    assert family in FAMILIES and len(eps) == len(feats)
    model.eval()
    req = [p.requires_grad for p in model.parameters()]
    for p in model.parameters():
        p.requires_grad_(False)
    try:
        with torch.no_grad():
            psm0, rm0 = heads_grad(model, feats)
            pos = torch.sigmoid(psm0) >= score_thr
        base = [f[a].clone() for f in feats]

        def project(d, k):
            d = torch.clamp(d, -eps[k], eps[k])
            return torch.clamp(base[k] + d, min=0.0) - base[k]

        delta = [project(torch.from_numpy(rng.uniform(-eps[k], eps[k], size=tuple(base[k].shape)).astype(np.float32)), k)
                 for k in range(len(feats))]
        hist = []

        def adv_feats(d):
            out = []
            for k, f in enumerate(feats):
                rows = [f[j] if j != a else base[k] + d[k] for j in range(f.shape[0])]
                out.append(torch.stack(rows, 0))
            return out

        for _ in range(steps):
            for d in delta:
                d.requires_grad_(True)
            psm, rm = heads_grad(model, adv_feats(delta))
            obj = objective(psm, rm, pos, rm0, family)
            grads = torch.autograd.grad(obj, delta)
            hist.append(float(obj))
            with torch.no_grad():
                delta = [project(d + step_frac * eps[k] * g.sign(), k) for k, (d, g) in enumerate(zip(delta, grads))]
        with torch.no_grad():
            new = adv_feats(delta)
            psm, rm = heads_grad(model, new)
            final = float(objective(psm, rm, pos, rm0, family))
            rel = [float(d.abs().mean() / (b.abs().mean() + 1e-12)) for d, b in zip(delta, base)]
            linf = [float(d.abs().max()) for d in delta]
    finally:
        for p, q in zip(model.parameters(), req):
            p.requires_grad_(q)
    led = {"family": family, "applied": True, "attacker": a, "eps": [float(e) for e in eps], "steps": steps,
           "step_frac": step_frac, "objective_hist": [round(h, 5) for h in hist] + [round(final, 5)],
           "n_pseudo_pos": int(pos.sum()), "linf_delta": linf, "mean_abs_delta_over_mean_abs_feat": rel}
    return [x.detach() for x in new], led
