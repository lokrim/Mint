"""Tile-wise composition of counterfactual decodes (contract §5.2).

AttFuse post-fusion computation is pixel-local (V-03), so the head output at an anchor pixel in
tile u with sender set S excluded *in u only* equals the output of a decode with S excluded
*everywhere*. Any tile-wise gating policy can therefore be evaluated exactly from one decode per
excluded-sender subset:

  candidates(): post_process up to (but excluding) the box filters and NMS, keeping the anchor
                index of every candidate above the score threshold;
  compose():    pick, per tile, the candidates of the subset excluded there, in anchor order;
  finalize():   the remaining post_process steps (large/abnormal-z filters, rotated NMS, range).

finalize(candidates(psm, rm)) reproduces OpenCOOD VoxelPostprocessor.post_process for a single
(ego) sample; compose() equals a real masked fusion pass. Both are checked on data by the runner.
"""
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F

from opencood.utils import box_utils

HEAD_STRIDE_M = 0.8      # head grid cell (352 x 100 for the released AttFuse checkpoint)
TILE_PX = 8              # 6.4 m tiles on the head grid


@dataclass
class Candidates:
    idx: np.ndarray        # (N,) int64 flat anchor index (h, w, anchor) in post_process order
    corners: np.ndarray    # (N, 8, 3) float32, receiver frame
    scores: np.ndarray     # (N,) float32
    hw: tuple              # head grid (H, W)
    n_anchor: int

    def tiles(self):
        a = self.idx // self.n_anchor
        h, w = a // self.hw[1], a % self.hw[1]
        return h // TILE_PX, w // TILE_PX

    def take(self, m):
        return Candidates(self.idx[m], self.corners[m], self.scores[m], self.hw, self.n_anchor)


def candidates(post_processor, psm, rm, anchor_box, transformation_matrix):
    """Mirror of VoxelPostprocessor.post_process up to the per-cav concatenation (one cav)."""
    _, n_anchor, hh, ww = psm.shape
    prob = F.sigmoid(psm.permute(0, 2, 3, 1)).reshape(1, -1)
    box3d = post_processor.delta_to_boxes3d(rm, anchor_box)
    mask = torch.gt(prob, post_processor.params["target_args"]["score_threshold"]).view(-1)
    idx = torch.nonzero(mask).view(-1)
    boxes3d = box3d[0][idx]
    scores = prob[0][idx]
    if len(boxes3d):
        corners = box_utils.boxes_to_corners_3d(boxes3d, order=post_processor.params["order"])
        corners = box_utils.project_box3d(corners, transformation_matrix)
    else:
        corners = torch.zeros((0, 8, 3))
    return Candidates(idx.numpy().astype(np.int64), corners.float().numpy(), scores.float().numpy(),
                      (hh, ww), n_anchor)


def tile_candidates(post_processor, psm_t, rm_t, sel, anchor_box, transformation_matrix, hw):
    """candidates() for head outputs computed on tiles only (E3 trigger mode).

    psm_t [T, A, 8, 8], rm_t [T, 7A, 8, 8]: head outputs of tiles sel [T, 2] (tile row, col) of the
    head grid hw. Anchors outside the tiles are absent. Cells beyond the grid (padded last tile row)
    are dropped. Same operations and anchor order (full-grid flat index) as candidates().
    """
    hh, ww = hw
    t, n_anchor = psm_t.shape[0], psm_t.shape[1]
    if t == 0:
        return Candidates(np.zeros(0, np.int64), np.zeros((0, 8, 3), np.float32), np.zeros(0, np.float32), hw, n_anchor)
    px = psm_t.shape[2]
    prob = F.sigmoid(psm_t.permute(0, 2, 3, 1))                           # T, 8, 8, A
    ys = sel[:, 0, None] * px + torch.arange(px)                           # T, 8
    xs = sel[:, 1, None] * px + torch.arange(px)
    idx = ((ys[:, :, None] * ww + xs[:, None, :])[..., None] * n_anchor + torch.arange(n_anchor))  # T, 8, 8, A
    valid = (ys < hh)[:, :, None, None].expand_as(idx)
    mask = torch.gt(prob, post_processor.params["target_args"]["score_threshold"]) & valid
    sel_flat = torch.nonzero(mask.reshape(-1)).view(-1)
    order = torch.argsort(idx.reshape(-1)[sel_flat])
    sel_flat = sel_flat[order]
    anc = F.pad(anchor_box.permute(2, 3, 0, 1).reshape(-1, hh, ww), (0, 0, 0, -(-hh // px) * px - hh))
    c = anc.shape[0]
    anc = anc.reshape(c, -1, px, ww // px, px)[:, sel[:, 0], :, sel[:, 1], :]      # T, C, 8, 8 (advanced idx first)
    anc = anc.permute(0, 2, 3, 1).reshape(t * px, px, n_anchor, 7)
    deltas = rm_t.permute(1, 0, 2, 3).reshape(1, rm_t.shape[1], t * px, px)
    box3d = post_processor.delta_to_boxes3d(deltas, anc)
    boxes3d = box3d[0][sel_flat]
    scores = prob.reshape(-1)[sel_flat]
    if len(boxes3d):
        corners = box_utils.boxes_to_corners_3d(boxes3d, order=post_processor.params["order"])
        corners = box_utils.project_box3d(corners, transformation_matrix)
    else:
        corners = torch.zeros((0, 8, 3))
    return Candidates(idx.reshape(-1)[sel_flat].numpy().astype(np.int64), corners.float().numpy(),
                      scores.float().numpy(), hw, n_anchor)


def finalize(post_processor, c: Candidates):
    """Remaining post_process steps; returns (corners (M,8,3) np, scores (M,) np)."""
    if len(c.idx) == 0:
        return np.zeros((0, 8, 3), np.float32), np.zeros((0,), np.float32)
    box = torch.from_numpy(c.corners)
    sc = torch.from_numpy(c.scores)
    keep = torch.logical_and(box_utils.remove_large_pred_bbx(box), box_utils.remove_bbx_abnormal_z(box))
    box, sc = box[keep], sc[keep]
    keep = box_utils.nms_rotated(box, sc, post_processor.params["nms_thresh"])
    box, sc = box[keep], sc[keep]
    m = box_utils.get_mask_for_boxes_within_range_torch(box)
    return box[m, :, :].numpy(), sc[m].numpy()


def compose(cands, choice):
    """cands: {frozenset(excluded senders): Candidates}; choice: {(tile_r, tile_c): frozenset}.

    Tiles not in `choice` use cands[frozenset()] (all contributions). Returns Candidates in
    anchor order, as a masked fusion pass would produce them.
    """
    base = cands[frozenset()]
    if not choice:
        return base
    parts = []
    gated = {}
    for t, s in choice.items():
        gated.setdefault(frozenset(s), set()).add(t)
    def in_tiles(c, ts):
        r, k = c.tiles()
        code = np.asarray([a * 10000 + b for a, b in ts], np.int64)
        return np.isin(r.astype(np.int64) * 10000 + k, code)
    in_any = np.zeros(len(base.idx), bool)
    for s, ts in gated.items():
        in_any |= in_tiles(base, ts)
    parts.append(base.take(~in_any))
    for s, ts in gated.items():
        parts.append(cands[s].take(in_tiles(cands[s], ts)))
    idx = np.concatenate([p.idx for p in parts])
    o = np.argsort(idx, kind="stable")
    return Candidates(idx[o], np.concatenate([p.corners for p in parts])[o],
                      np.concatenate([p.scores for p in parts])[o], base.hw, base.n_anchor)


def tile_include_masks(n, shapes, choice):
    """Fusion include masks [n, H_k, W_k] per scale excluding sender set s in each chosen tile.

    shapes: list of (H_k, W_k) per fusion scale; scale k's cell is HEAD_STRIDE_M * (W_head / W_k).
    """
    w_head = shapes[0][1]
    out = []
    for hk, wk in shapes:
        px = TILE_PX * wk // w_head          # tile size in cells at this scale (8 / 4 / 2)
        m = torch.ones((n, hk, wk), dtype=torch.bool)
        for (r, c), s in choice.items():
            for i in s:
                m[i, r * px:(r + 1) * px, c * px:(c + 1) * px] = False
        out.append(m)
    return out
