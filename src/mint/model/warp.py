"""Receiver-side warping of sender BEV features into the receiver grid (protocol D-13, check V-02).

The sender encodes in its OWN LiDAR frame (proj_first=False). The receiver resamples each fusion-
scale feature map with the claimed sender->receiver transform T (4x4, LiDAR frames), bilinear,
zero outside the sender's grid. Grid convention (OpenCOOD PointPillarScatter): rows = y, cols = x,
pixel (r, q) centre = (xmin + (q + .5) * cx, ymin + (r + .5) * cy).
"""
import numpy as np
import torch
import torch.nn.functional as F


def warp_to_receiver(feat, T_sender_to_receiver, pc_range):
    """feat: [C, H, W] in sender frame. Returns [C, H, W] in receiver frame (same grid extent)."""
    c, h, w = feat.shape
    xmin, ymin, _, xmax, ymax, _ = pc_range
    cx, cy = (xmax - xmin) / w, (ymax - ymin) / h
    xs = xmin + (np.arange(w) + 0.5) * cx
    ys = ymin + (np.arange(h) + 0.5) * cy
    X, Y = np.meshgrid(xs, ys)                                   # receiver pixel centres
    Tinv = np.linalg.inv(np.asarray(T_sender_to_receiver, dtype=np.float64))
    pr = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size), np.ones(X.size)])
    ps = Tinv @ pr                                               # in sender frame (z ignored)
    gx = 2 * (ps[0] - xmin) / (xmax - xmin) - 1
    gy = 2 * (ps[1] - ymin) / (ymax - ymin) - 1
    grid = torch.from_numpy(np.stack([gx, gy], -1).reshape(1, h, w, 2)).to(feat.dtype)
    return F.grid_sample(feat.unsqueeze(0), grid, mode="bilinear", padding_mode="zeros",
                         align_corners=False)[0]


def message_bytes(feats_one_agent):
    """V-05: bytes of one sender's multi-scale message (list of [C,H,W]) dense and non-zero."""
    dense = sum(f.numel() for f in feats_one_agent)
    nz_pixels = [int((f.abs().sum(0) > 0).sum()) for f in feats_one_agent]
    nz_bytes_fp16 = sum(n * f.shape[0] * 2 + n * 4 for n, f in zip(nz_pixels, feats_one_agent))
    return {"dense_floats": int(dense), "dense_MB_fp32": round(dense * 4 / 1e6, 3),
            "dense_MB_fp16": round(dense * 2 / 1e6, 3),
            "nonzero_pixel_frac": [round(n / (f.shape[1] * f.shape[2]), 4) for n, f in zip(nz_pixels, feats_one_agent)],
            "sparse_MB_fp16_with_int32_index": round(nz_bytes_fp16 / 1e6, 3)}
