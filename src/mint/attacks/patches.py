"""Development attack injectors on the receiver grid (OPV2V proj_first, D-13b).

Feature attacks edit the attacker's three fusion-scale feature maps in a metric patch aligned to
the coarsest cell (3.2 m), so one patch has identical metric extent at 0.8 / 1.6 / 3.2 m:
  A-F2a spoof   copy the attacker's own patch around a real object to a random free location;
  A-F2b remove  overwrite a real object's patch with a background patch from a free location;
  A-F5  shift   A-F2b at the target, then paste the original patch one coarse cell away.
Point attack (A-R2-lite): copy the attacker's own points on a real object to a random free
location and append them to the attacker's pillars (other pillars untouched).

All randomness comes from the caller's np.random.Generator (keyed per family/scenario/frame).
The attacker uses ground truth only to choose targets, which the threat model allows.
"""
import numpy as np
import torch

PC_MIN = np.array([-140.8, -40.0])
COARSE_M = 3.2
SCALE_M = (0.8, 1.6, 3.2)


def coarse_patch(cx, cy, half):
    """Coarse-cell index box [c0, c1) x [r0, r1) covering the square of half-size `half`."""
    c0 = int(np.floor((cx - half - PC_MIN[0]) / COARSE_M))
    c1 = int(np.floor((cx + half - PC_MIN[0]) / COARSE_M)) + 1
    r0 = int(np.floor((cy - half - PC_MIN[1]) / COARSE_M))
    r1 = int(np.floor((cy + half - PC_MIN[1]) / COARSE_M)) + 1
    return c0, c1, r0, r1


def _slices(p, k):
    f = int(round(COARSE_M / SCALE_M[k]))
    c0, c1, r0, r1 = p
    return slice(r0 * f, r1 * f), slice(c0 * f, c1 * f)


def in_grid(p, feats):
    c0, c1, r0, r1 = p
    h, w = feats[-1].shape[2], feats[-1].shape[3]
    return c0 >= 0 and r0 >= 0 and c1 <= w and r1 <= h


def copy_patch(feats, a, src, dst):
    """feats: list of [n, C, H, W] (cloned by caller). Copies src patch of agent a onto dst."""
    for k, f in enumerate(feats):
        rs, cs = _slices(src, k)
        rd, cd = _slices(dst, k)
        f[a, :, rd, cd] = f[a, :, rs, cs].clone()


def shift_patch(p, dc, dr):
    c0, c1, r0, r1 = p
    return c0 + dc, c1 + dc, r0 + dr, r1 + dr


def patch_center(p):
    c0, c1, r0, r1 = p
    return PC_MIN[0] + COARSE_M * (c0 + c1) / 2, PC_MIN[1] + COARSE_M * (r0 + r1) / 2


def free_of(p, gt_xy, clear):
    """True if no GT centre lies within the patch dilated by `clear` metres."""
    c0, c1, r0, r1 = p
    x0, x1 = PC_MIN[0] + COARSE_M * c0 - clear, PC_MIN[0] + COARSE_M * c1 + clear
    y0, y1 = PC_MIN[1] + COARSE_M * r0 - clear, PC_MIN[1] + COARSE_M * r1 + clear
    if len(gt_xy) == 0:
        return True
    g = np.asarray(gt_xy)
    return not np.any((g[:, 0] >= x0) & (g[:, 0] <= x1) & (g[:, 1] >= y0) & (g[:, 1] <= y1))


def sample_free_patch(rng, shape_p, feats, gt_xy, region=(60.0, 35.0), clear=3.0, avoid_origin=6.0,
                      tries=300):
    """Random patch of the same cell shape as shape_p, free of GT, inside |x|,|y| <= region."""
    c0, c1, r0, r1 = shape_p
    wc, hc = c1 - c0, r1 - r0
    for _ in range(tries):
        x = rng.uniform(-region[0], region[0])
        y = rng.uniform(-region[1], region[1])
        if np.hypot(x, y) < avoid_origin:
            continue
        cc = int(np.floor((x - PC_MIN[0]) / COARSE_M)) - wc // 2
        rr = int(np.floor((y - PC_MIN[1]) / COARSE_M)) - hc // 2
        p = (cc, cc + wc, rr, rr + hc)
        if in_grid(p, feats) and free_of(p, gt_xy, clear):
            return p
    return None


def box_half(corners):
    c = np.asarray(corners)
    lw = np.ptp(c[:, :2], axis=0)
    return 0.5 * float(lw.max()) + 1.0


def points_in_box(pts, corners, pad=0.1):
    from mint.geometry.rays import box_frame
    cen, axes, half = box_frame(corners)
    q = (np.asarray(pts)[:, :3] - cen) @ axes.T
    return np.all(np.abs(q) <= half + pad, axis=1)


def append_points_to_voxels(pl, agent, pts, pc_range, voxel_size, max_pts=32):
    """Append points (N, 4: x y z i) to agent's pillars in a collated processed_lidar dict.

    Existing pillars receive points until the cap; new pillars are appended. Returns a new dict.
    """
    vf = pl["voxel_features"].clone()
    vc = pl["voxel_coords"].clone()
    vn = pl["voxel_num_points"].clone()
    pc_min = np.asarray(pc_range[:3], np.float32)
    vs = np.asarray(voxel_size, np.float32)
    grid = np.round((np.asarray(pc_range[3:]) - pc_min) / vs).astype(np.int64)
    idx = np.floor((pts[:, :3] - pc_min) / vs).astype(np.int64)
    ok = np.all((idx >= 0) & (idx < grid), axis=1)
    pts, idx = pts[ok], idx[ok]
    mine = np.flatnonzero(vc[:, 0].numpy() == agent)
    key = {(int(vc[j, 2]), int(vc[j, 3])): j for j in mine}      # (y, x) -> row (z index is 0)
    new_f, new_c, new_n = [], [], []
    pending = {}
    for p, (ix, iy, iz) in zip(pts, idx):
        j = key.get((iy, ix))
        if j is not None:
            if vn[j] < max_pts:
                vf[j, vn[j]] = torch.from_numpy(p.astype(np.float32))
                vn[j] += 1
        else:
            pending.setdefault((iy, ix, iz), []).append(p)
    for (iy, ix, iz), ps in pending.items():
        ps = np.asarray(ps[:max_pts], np.float32)
        f = np.zeros((max_pts, vf.shape[2]), np.float32)
        f[:len(ps)] = ps
        new_f.append(f)
        new_c.append([agent, iz, iy, ix])
        new_n.append(len(ps))
    if new_f:
        vf = torch.cat([vf, torch.from_numpy(np.stack(new_f))])
        vc = torch.cat([vc, torch.tensor(new_c, dtype=vc.dtype)])
        vn = torch.cat([vn, torch.tensor(new_n, dtype=vn.dtype)])
    return {**pl, "voxel_features": vf, "voxel_coords": vc, "voxel_num_points": vn}
