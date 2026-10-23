"""Split an (unmodified) OpenCOOD PointPillarIntermediate / AttBEVBackbone forward pass into
(1) per-agent multi-scale features, (2) maskable per-pixel attentive fusion, (3) deblock+heads.

AttFusion in OpenCOOD has no learned parameters: at each pixel the ego row of
softmax(X X^T / sqrt(C)) X is kept. `fuse_scale` re-implements exactly that, with an optional
boolean `include` mask per agent and pixel (False = agent excluded from the softmax there).
The ego (agent 0 of each sample) is never excluded.
"""
import math

import torch


@torch.no_grad()
def agent_features(model, batch_ego):
    """Return list over scales of per-agent feature maps [N_agents, C_k, H_k, W_k] and record_len."""
    pp = batch_ego["processed_lidar"]
    bd = {"voxel_features": pp["voxel_features"], "voxel_coords": pp["voxel_coords"],
          "voxel_num_points": pp["voxel_num_points"], "record_len": batch_ego["record_len"]}
    bd = model.pillar_vfe(bd)
    bd = model.scatter(bd)
    bb = model.backbone
    assert not getattr(bb, "compress", False), "compression variant not supported here"
    x = bd["spatial_features"]
    feats = []
    for blk in bb.blocks:
        x = blk(x)
        feats.append(x)
    return feats, bd["record_len"]


@torch.no_grad()
def fuse_scale(x, include=None):
    """x: [N, C, H, W] for ONE sample (agent 0 = ego). include: bool [N, H, W] or None."""
    n, c, h, w = x.shape
    v = x.reshape(n, c, h * w)                       # N, C, P
    scores = torch.einsum("cp,ncp->pn", v[0], v) / math.sqrt(c)   # ego query vs each agent: P, N
    if include is not None:
        inc = include.reshape(n, h * w).T.clone()     # P, N
        inc[:, 0] = True
        scores = scores.masked_fill(~inc, float("-inf"))
    attn = torch.softmax(scores, dim=1)              # P, N
    out = torch.einsum("pn,ncp->cp", attn, v)
    return out.reshape(c, h, w), attn.T.reshape(n, h, w)


@torch.no_grad()
def decode(model, fused):
    """fused: list over scales of [C_k, H_k, W_k] (one sample). Returns psm, rm with batch dim 1."""
    bb = model.backbone
    ups = [bb.deblocks[i](f.unsqueeze(0)) for i, f in enumerate(fused)]
    x = torch.cat(ups, dim=1) if len(ups) > 1 else ups[0]
    if len(bb.deblocks) > len(bb.blocks):
        x = bb.deblocks[-1](x)
    return model.cls_head(x), model.reg_head(x)


@torch.no_grad()
def reference_fused(model, feats, record_len):
    """OpenCOOD's own AttFusion outputs, for equality checks (sample 0 only)."""
    return [model.backbone.fuse_modules[i](f, record_len)[0] for i, f in enumerate(feats)]


@torch.no_grad()
def receiver_features(model, batch_ego):
    """Per-scale features of the receiver (agent 0) only, encoding only its own pillars.

    This is the receiver's encode cost in deployment: sender features arrive over the wire, so the
    encoding of sender point clouds is not receiver work. Returns a list of [1, C_k, H_k, W_k].
    """
    pp = batch_ego["processed_lidar"]
    keep = pp["voxel_coords"][:, 0] == 0
    bd = {"voxel_features": pp["voxel_features"][keep], "voxel_coords": pp["voxel_coords"][keep],
          "voxel_num_points": pp["voxel_num_points"][keep], "record_len": torch.ones_like(batch_ego["record_len"][:1])}
    bd = model.pillar_vfe(bd)
    bd = model.scatter(bd)
    x = bd["spatial_features"]
    feats = []
    for blk in model.backbone.blocks:
        x = blk(x)
        feats.append(x)
    return feats


@torch.no_grad()
def decode_batch(model, fused):
    """fused: list over scales of [B, C_k, H_k, W_k] (B counterfactuals in one forward pass)."""
    bb = model.backbone
    ups = [bb.deblocks[i](f) for i, f in enumerate(fused)]
    x = torch.cat(ups, dim=1) if len(ups) > 1 else ups[0]
    if len(bb.deblocks) > len(bb.blocks):
        x = bb.deblocks[-1](x)
    return model.cls_head(x), model.reg_head(x)
