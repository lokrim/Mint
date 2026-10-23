"""Receiver-ray geometry for MINT (methodology_candidates.md, M3).

All quantities are in the receiver's LiDAR frame (metres), sensor origin at (0, 0, 0).

* `RangeImage.from_points`: build a (ring x column) range image from an UNORGANIZED cloud by
  clustering elevation angles into rings and binning azimuth into columns. Empty cells mean
  "no return recorded in this slot" -- they are NOT free space (decision D-06).
* `ray_obb`: entry/exit distances of unit rays through an oriented box (slab test).
* `classify_box`: per-slot SUP / TRAV / OCC / NR counts for one box claim.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class RangeImage:
    ring_elev: np.ndarray      # (R,) ring centre elevations, radians, descending
    n_cols: int
    rng: np.ndarray            # (R, C) range in metres, NaN = no return
    az0: float                 # azimuth of column 0 left edge, radians
    stats: dict

    @staticmethod
    def from_points(xyz, n_rings=None, n_cols=None, elev_bin_deg=0.02):
        xyz = np.asarray(xyz, dtype=np.float64)
        r = np.linalg.norm(xyz, axis=1)
        ok = r > 0.5
        xyz, r = xyz[ok], r[ok]
        elev = np.arcsin(np.clip(xyz[:, 2] / r, -1, 1))
        az = np.arctan2(xyz[:, 1], xyz[:, 0])
        # ring discovery: fine histogram of elevations, peaks separated by empty bins
        b = np.radians(elev_bin_deg)
        lo = elev.min() - b
        idx = np.floor((elev - lo) / b).astype(np.int64)
        hist = np.bincount(idx)
        occupied = hist > 0
        # group contiguous occupied bins into rings
        edges = np.flatnonzero(np.diff(np.concatenate([[0], occupied.astype(np.int8), [0]])))
        starts, ends = edges[0::2], edges[1::2]
        centres = []
        bin_to_ring = np.full(hist.size, -1, np.int64)
        for k, (s, e) in enumerate(zip(starts, ends)):
            w = hist[s:e]
            centres.append(lo + b * (np.arange(s, e) + 0.5) @ w / w.sum())
            bin_to_ring[s:e] = k
        centres = np.array(centres)
        ring = bin_to_ring[idx]
        order = np.argsort(-centres)               # ring 0 = highest elevation
        remap = np.empty_like(order)
        remap[order] = np.arange(order.size)
        ring = remap[ring]
        centres = centres[order]
        if n_rings is not None and centres.size != n_rings:
            raise ValueError(f"found {centres.size} rings, expected {n_rings}")
        if n_cols is None:
            # columns: median number of returns per ring is a lower bound; use angular spacing
            per_ring = [np.sort(az[ring == k]) for k in range(centres.size)]
            gaps = np.concatenate([np.diff(a) for a in per_ring if a.size > 10])
            step = np.median(gaps[gaps > 1e-6])
            n_cols = int(round(2 * np.pi / step))
        az0 = -np.pi
        col = np.floor((az - az0) / (2 * np.pi) * n_cols).astype(np.int64) % n_cols
        img = np.full((centres.size, n_cols), np.nan)
        # keep the nearest return if two points share a slot
        o = np.argsort(-r)
        img[ring[o], col[o]] = r[o]
        collisions = int(r.size - np.isfinite(img).sum())
        stats = {"points": int(r.size), "rings": int(centres.size), "cols": int(n_cols),
                 "slots": int(img.size), "filled": int(np.isfinite(img).sum()),
                 "slot_collisions": collisions,
                 "elev_deg_range": [round(float(np.degrees(centres.min())), 3),
                                    round(float(np.degrees(centres.max())), 3)]}
        return RangeImage(centres, n_cols, img, az0, stats)

    def directions(self, rows, cols):
        el = self.ring_elev[rows]
        az = self.az0 + (cols + 0.5) * 2 * np.pi / self.n_cols
        return np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], axis=-1)


def box_frame(corners):
    """corners (8,3) in OpenCOOD order -> centre, axes (3,3 rows unit), half extents (3,)."""
    c = np.asarray(corners, dtype=np.float64)
    u, v, w = c[0] - c[3], c[1] - c[0], c[4] - c[0]
    ext = np.array([np.linalg.norm(u), np.linalg.norm(v), np.linalg.norm(w)]) / 2
    axes = np.stack([u / (2 * ext[0]), v / (2 * ext[1]), w / (2 * ext[2])])
    return c.mean(0), axes, ext


def ray_obb(dirs, centre, axes, half, origin=np.zeros(3)):
    """Slab test for unit rays origin + t*d. Returns (t_in, t_out); t_in > t_out means miss."""
    d = np.asarray(dirs, dtype=np.float64) @ axes.T          # direction in box frame
    o = (np.asarray(origin, dtype=np.float64) - centre) @ axes.T
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (-half - o) / d
        t2 = (half - o) / d
    tmin = np.where(np.abs(d) < 1e-12, np.where(np.abs(o) <= half, -np.inf, np.inf), np.minimum(t1, t2))
    tmax = np.where(np.abs(d) < 1e-12, np.where(np.abs(o) <= half, np.inf, -np.inf), np.maximum(t1, t2))
    t_in = np.max(tmin, axis=-1)
    t_out = np.min(tmax, axis=-1)
    return np.maximum(t_in, 0.0), t_out


def core_and_envelope(corners, shrink_frac=0.15, shrink_min=0.15, ground_band=0.3, top_band=0.1,
                      dilate=0.2):
    centre, axes, half = box_frame(corners)
    core_half = half.copy()
    core_half[:2] = np.maximum(half[:2] - np.maximum(shrink_frac * half[:2] * 2, shrink_min), 0.05)
    # vertical: [bottom + ground_band, top - top_band]
    z_lo, z_hi = -half[2] + ground_band, half[2] - top_band
    if z_hi <= z_lo:
        z_lo, z_hi = -half[2] * 0.2, half[2] * 0.2
    core_half[2] = (z_hi - z_lo) / 2
    core_centre = centre + axes[2] * (z_lo + z_hi) / 2
    env_half = half + dilate
    return (core_centre, axes, core_half), (centre, axes, env_half)


def contains_origin(corners, margin=0.0):
    """True if the receiver sensor lies inside the box footprint in BEV (x, y only).

    BEV, not 3D: roof-mounted sensors sit ABOVE their own vehicle's box, and simulators such as
    CARLA do not return the sensor's own vehicle, so its rays pass through its own box.
    """
    cen, ax, half = box_frame(corners)
    q = (-cen) @ ax.T
    return bool(np.all(np.abs(q[:2]) <= half[:2] + margin))


def classify_points(xyz, corners, tau0=0.05, tau_rel=0.01, **kw):
    """Point-wise version: every recorded return is one ray (no azimuth binning).

    Counts SUP / TRAV / OCC among returns whose ray crosses the box CORE. No-returns are not
    observable point-wise and are reported separately from the range image. Boxes that contain
    the receiver origin (e.g. the receiver vehicle itself) are NOT_APPLICABLE.
    """
    out = {"SUP": 0, "TRAV": 0, "OCC": 0, "candidates": 0, "self_box": False}
    if contains_origin(corners, margin=0.2):
        out["self_box"] = True
        return out
    (cc, ax, ch), (ec, _, eh) = core_and_envelope(corners, **kw)
    p = np.asarray(xyz, dtype=np.float64)
    rho = np.linalg.norm(p, axis=1)
    keep = rho > 0.5
    p, rho = p[keep], rho[keep]
    # cheap angular prefilter around the box (bounding cone)
    cdir = cc / np.linalg.norm(cc)
    rad = np.linalg.norm(eh) / max(np.linalg.norm(cc), 1e-6)
    cosmin = np.cos(min(np.arctan(rad) + 0.02, np.pi / 2))
    d = p / rho[:, None]
    near = d @ cdir >= cosmin
    d, rho = d[near], rho[near]
    if d.shape[0] == 0:
        return out
    t_in, t_out = ray_obb(d, cc, ax, ch)
    hit = t_in <= t_out
    d, rho = d[hit], rho[hit]
    e_in, e_out = ray_obb(d, ec, ax, eh)
    tau = tau0 + tau_rel * rho
    occ = rho < e_in - tau
    trav = rho > e_out + tau
    sup = ~occ & ~trav
    out.update({"SUP": int(sup.sum()), "TRAV": int(trav.sum()), "OCC": int(occ.sum()),
                "candidates": int(hit.sum())})
    return out


def classify_box(ri: RangeImage, corners, tau0=0.05, tau_rel=0.01, **kw):
    """Count receiver slots whose ray crosses the box CORE: SUP / TRAV / OCC / NR."""
    (cc, ax, ch), (ec, _, eh) = core_and_envelope(corners, **kw)
    pts = np.asarray(corners, dtype=np.float64)
    el = np.arcsin(np.clip(pts[:, 2] / np.linalg.norm(pts, axis=1), -1, 1))
    az = np.arctan2(pts[:, 1], pts[:, 0])
    rows = np.flatnonzero((ri.ring_elev >= el.min() - 0.01) & (ri.ring_elev <= el.max() + 0.01))
    # azimuth span (handle wrap by unwrapping around the box centre direction)
    c0 = np.arctan2(pts[:, 1].mean(), pts[:, 0].mean())
    daz = np.angle(np.exp(1j * (az - c0)))
    a_lo, a_hi = c0 + daz.min() - 0.01, c0 + daz.max() + 0.01
    step = 2 * np.pi / ri.n_cols
    cols = (np.arange(int(np.floor((a_lo - ri.az0) / step)), int(np.ceil((a_hi - ri.az0) / step)) + 1)
            % ri.n_cols)
    out = {"SUP": 0, "TRAV": 0, "OCC": 0, "NR": 0, "candidates": 0}
    if rows.size == 0 or cols.size == 0:
        return out
    R, C = np.meshgrid(rows, cols, indexing="ij")
    R, C = R.ravel(), C.ravel()
    d = ri.directions(R, C)
    t_in, t_out = ray_obb(d, cc, ax, ch)
    hit = t_in <= t_out
    if not hit.any():
        return out
    R, C, d = R[hit], C[hit], d[hit]
    ce_in, ce_out = t_in[hit], t_out[hit]
    e_in, e_out = ray_obb(d, ec, ax, eh)
    rho = ri.rng[R, C]
    tau = tau0 + tau_rel * np.nan_to_num(rho, nan=0.0)
    nr = ~np.isfinite(rho)
    occ = ~nr & (rho < e_in - tau)
    trav = ~nr & (rho > e_out + tau)          # returned beyond the whole envelope
    sup = ~nr & ~occ & ~trav
    out.update({"SUP": int(sup.sum()), "TRAV": int(trav.sum()), "OCC": int(occ.sum()),
                "NR": int(nr.sum()), "candidates": int(hit.sum())})
    return out
