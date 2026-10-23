"""X1: white-box L-inf PGD on the attacker's intermediate features (evaluation only).

Differentiable copy of the frozen AttFuse path (attfuse_parts.fuse_scale is decorated no_grad):
per pixel, the ego row of softmax(X X^T / sqrt(C)) X; then the model's own deblocks and heads.
Budgets follow the literature (plan.json): eps in {0.1, 0.5}, 15 sign-gradient steps, step eps/5.
"""
import math

import torch


def fuse_scale_grad(x):
    """Same math as attfuse_parts.fuse_scale(x, None)[0], with gradients."""
    n, c, h, w = x.shape
    v = x.reshape(n, c, h * w)
    scores = torch.einsum("cp,ncp->pn", v[0], v) / math.sqrt(c)
    attn = torch.softmax(scores, dim=1)
    return torch.einsum("pn,ncp->cp", attn, v).reshape(c, h, w)


def decode_grad(model, fused):
    bb = model.backbone
    ups = [bb.deblocks[i](f.unsqueeze(0)) for i, f in enumerate(fused)]
    x = torch.cat(ups, dim=1) if len(ups) > 1 else ups[0]
    if len(bb.deblocks) > len(bb.blocks):
        x = bb.deblocks[-1](x)
    return model.cls_head(x)


def logits(model, feats):
    return decode_grad(model, [fuse_scale_grad(f) for f in feats])


def objective(z, y, variant):
    """z: cls logits, y: bool pseudo-labels (clean score >= threshold). Value to MAXIMIZE."""
    pos = -torch.nn.functional.logsigmoid(z[y]).mean() if y.any() else z.sum() * 0
    if variant == "pgd_remove":
        return pos
    neg = -torch.nn.functional.logsigmoid(-z[~y]).mean() if (~y).any() else z.sum() * 0
    if variant == "pgd_untargeted":
        return pos + neg
    raise ValueError(variant)


def pgd_attack(model, feats, a, variant, eps, steps=15, step=None, score_thr=0.2):
    """feats: list of [n, C, H, W] (clean). Perturbs agent a's maps at every scale. Returns (new feats, ledger)."""
    step = eps / 5 if step is None else step
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    with torch.no_grad():
        y = torch.sigmoid(logits(model, feats)) >= score_thr
    delta = [torch.zeros_like(f[a]) for f in feats]
    hist = []
    for _ in range(steps):
        for d in delta:
            d.requires_grad_(True)
        adv = []
        for f, d in zip(feats, delta):
            g = f.clone()
            g[a] = torch.clamp(f[a] + d, min=0.0)
            adv.append(g)
        obj = objective(logits(model, adv), y, variant)
        grads = torch.autograd.grad(obj, delta)
        hist.append(float(obj))
        with torch.no_grad():
            delta = [torch.clamp(d + step * gr.sign(), -eps, eps) for d, gr in zip(delta, grads)]
    with torch.no_grad():
        new = []
        for f, d in zip(feats, delta):
            g = f.clone()
            g[a] = torch.clamp(f[a] + d, min=0.0)
            new.append(g)
        rel = [float(d.abs().mean() / (f[a].abs().mean() + 1e-12)) for f, d in zip(feats, delta)]
    led = {"family": f"{variant}_eps{eps}", "attacker": a, "applied": True, "eps": eps, "steps": steps, "step": step,
           "objective_first_last": [round(hist[0], 4), round(hist[-1], 4)], "n_pseudo_pos": int(y.sum()),
           "mean_abs_delta_over_mean_abs_feat": [round(r, 4) for r in rel]}
    return new, led
