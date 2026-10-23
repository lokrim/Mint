"""Per-frame, receiver-only ground classification and a ground-aware ray test.

Why (E0 geometry note): `classify_points` counts a return as SUP when it lies inside the box
envelope along the ray. The envelope extends 0.2 m below the box bottom, so a ray that crosses an
EMPTY box's core while descending and then hits the ground inside the footprint is counted as
support. For a 4 m-long box seen from a ~1.9 m-high roof sensor this can happen up to roughly
20 m range. A real vehicle blocks such rays before they reach the ground under it.

Ground estimate: only the receiver's own scan. BEV cells of `cell` metres; each cell's ground
height is the minimum z over a (win x win)-cell neighbourhood, accepted only if it is at least
`min_drop` below the sensor (rejects vehicle roofs in cells with no visible ground). A return
is GROUND if z <= local ground + band. No ground truth is used.
"""
import numpy as np

from mint.geometry.rays import contains_origin, core_and_envelope, ray_obb


def ground_height_map(xyz, cell=1.0, win=5, min_drop=1.0):
    p = np.asarray(xyz, dtype=np.float64)
    ix = np.floor(p[:, 0] / cell).astype(np.int64)
    iy = np.floor(p[:, 1] / cell).astype(np.int64)
    x0, y0 = ix.min(), iy.min()
    gx, gy = ix - x0, iy - y0
    nx, ny = gx.max() + 1, gy.max() + 1
    zmin = np.full((nx, ny), np.inf)
    np.minimum.at(zmin, (gx, gy), p[:, 2])
    zmin[zmin > -min_drop] = np.inf                     # not plausibly ground
    r = win // 2
    pad = np.pad(zmin, r, constant_values=np.inf)
    out = np.full_like(zmin, np.inf)
    for dx in range(win):
        for dy in range(win):
            out = np.minimum(out, pad[dx:dx + nx, dy:dy + ny])
    return {"z": out, "x0": x0, "y0": y0, "cell": cell}


def ground_at(gmap, x, y):
    ix = np.floor(np.asarray(x) / gmap["cell"]).astype(np.int64) - gmap["x0"]
    iy = np.floor(np.asarray(y) / gmap["cell"]).astype(np.int64) - gmap["y0"]
    nx, ny = gmap["z"].shape
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    z = np.full(np.shape(ix), np.inf)
    z[ok] = gmap["z"][ix[ok], iy[ok]]
    return z


def ground_mask(xyz, band=0.15, **kw):
    gmap = ground_height_map(xyz, **kw)
    p = np.asarray(xyz)
    return p[:, 2] <= ground_at(gmap, p[:, 0], p[:, 1]) + band, gmap


def classify_points_ground(xyz, is_ground, corners, tau0=0.05, tau_rel=0.01, **kw):
    """Like rays.classify_points, but a GROUND return on a ray that crossed the box core is
    traversal (the ray passed through the claimed volume and reached the ground), never support.
    """
    out = {"SUP": 0, "TRAV": 0, "OCC": 0, "TRAV_GROUND": 0, "candidates": 0, "self_box": False}
    if contains_origin(corners, margin=0.2):
        out["self_box"] = True
        return out
    (cc, ax, ch), (ec, _, eh) = core_and_envelope(corners, **kw)
    p = np.asarray(xyz, dtype=np.float64)
    g = np.asarray(is_ground, bool)
    rho = np.linalg.norm(p, axis=1)
    keep = rho > 0.5
    p, rho, g = p[keep], rho[keep], g[keep]
    cdir = cc / np.linalg.norm(cc)
    rad = np.linalg.norm(eh) / max(np.linalg.norm(cc), 1e-6)
    cosmin = np.cos(min(np.arctan(rad) + 0.02, np.pi / 2))
    d = p / rho[:, None]
    near = d @ cdir >= cosmin
    d, rho, g = d[near], rho[near], g[near]
    if d.shape[0] == 0:
        return out
    t_in, t_out = ray_obb(d, cc, ax, ch)
    hit = t_in <= t_out
    d, rho, g, t_in = d[hit], rho[hit], g[hit], t_in[hit]
    e_in, e_out = ray_obb(d, ec, ax, eh)
    tau = tau0 + tau_rel * rho
    occ = rho < e_in - tau
    trav_far = rho > e_out + tau
    trav_g = ~occ & ~trav_far & g & (rho > t_in)
    sup = ~occ & ~trav_far & ~trav_g
    out.update({"SUP": int(sup.sum()), "TRAV": int((trav_far | trav_g).sum()), "OCC": int(occ.sum()),
                "TRAV_GROUND": int(trav_g.sum()), "candidates": int(hit.sum())})
    return out
