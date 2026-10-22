"""PILOT P1 (disposable, development data only: mini_7, already exposed).

Questions:
 Q1. Is each organized PCD a beam grid (row ~ fixed elevation, column ~ azimuth),
     so that placeholder (no-return) slots get a recoverable direction?
 Q2. Where do placeholder slots point (sky vs ground vs near field)?
 Q3. Does label file k match point-cloud sync index k (vs k-1, k+1)?

Not final evidence. Prints JSON-ish summaries only.
"""
import json, sys, tarfile, io, os, glob
import numpy as np

ROOT = "/Users/lokrim/Code/valid-point/data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91"
SEG = "mini_7"
PCD_DIR = f"{ROOT}/raw/PointClouds/{SEG}"
TOP_FROM_MAP = np.array([41.551, 51.878, 1.077])
DOME_FROM_MAP = np.array([41.507, 51.864, 1.340])


def read_pcd(path):
    with open(path, "rb") as f:
        header = {}
        while True:
            line = f.readline().decode().strip()
            k, *v = line.split()
            header[k] = v
            if k == "DATA":
                break
        w, h = int(header["WIDTH"][0]), int(header["HEIGHT"][0])
        arr = np.loadtxt(f, dtype=np.float32)
    assert arr.shape == (w * h, 4), arr.shape
    return arr.reshape(h, w, 4), header


def find(stream, k):
    c = glob.glob(f"{PCD_DIR}/{stream}_{k}_*.pcd")
    return c[0] if c else None


def grid_stats(stream, k, origin):
    g, _ = read_pcd(find(stream, k))
    xyz = g[..., :3].astype(np.float64)
    vals, counts = np.unique(xyz.reshape(-1, 3), axis=0, return_counts=True)
    ph_xyz = vals[np.argmax(counts)]
    ph = np.all(xyz == ph_xyz, axis=-1)
    d = xyz - origin
    r = np.linalg.norm(d, axis=-1)
    valid = (~ph) & (r > 0.3)
    elev = np.degrees(np.arctan2(d[..., 2], np.linalg.norm(d[..., :2], axis=-1)))
    az = np.degrees(np.arctan2(d[..., 1], d[..., 0]))
    H, W = ph.shape
    row_std = []
    row_med = []
    for i in range(H):
        e = elev[i][valid[i]]
        if e.size > 50:
            row_med.append(float(np.median(e)))
            row_std.append(float(np.std(e)))
        else:
            row_med.append(None)
            row_std.append(None)
    # column azimuth monotonicity: median az per column (unwrap)
    col_med = np.array([np.median(az[:, j][valid[:, j]]) if valid[:, j].sum() > 5 else np.nan for j in range(W)])
    cm = col_med[~np.isnan(col_med)]
    steps = np.diff(np.unwrap(np.radians(cm)))
    frac_monotone = float(np.mean(np.sign(steps) == np.sign(np.median(steps)))) if steps.size else None
    # placeholder distribution by row (elevation band)
    ph_by_row = ph.mean(axis=1)
    rows_med = np.array([m if m is not None else np.nan for m in row_med])
    out = {
        "stream": stream, "k": k, "H": H, "W": W,
        "placeholder_xyz": ph_xyz.round(3).tolist(),
        "placeholder_frac": round(float(ph.mean()), 4),
        "valid_frac": round(float(valid.mean()), 4),
        "row_elev_std_deg_median": round(float(np.nanmedian([s for s in row_std if s is not None])), 3),
        "row_elev_std_deg_p90": round(float(np.nanpercentile([s for s in row_std if s is not None], 90)), 3),
        "row_elev_median_range_deg": [round(float(np.nanmin(rows_med)), 2), round(float(np.nanmax(rows_med)), 2)],
        "row_order_monotone_frac": round(float(np.mean(np.diff(rows_med[~np.isnan(rows_med)]) < 0)), 3),
        "col_azimuth_step_sign_consistency": None if frac_monotone is None else round(frac_monotone, 3),
        "col_azimuth_median_step_deg": None if steps.size == 0 else round(float(np.degrees(np.median(steps))), 4),
        "placeholder_frac_rows_above_0deg": round(float(ph[rows_med > 0].mean()), 3) if np.any(rows_med > 0) else None,
        "placeholder_frac_rows_below_minus5deg": round(float(ph[rows_med < -5].mean()), 3) if np.any(rows_med < -5) else None,
        "rows_without_elevation_estimate": int(np.isnan(rows_med).sum()),
    }
    return out


def load_labels(tar_path, seg, ks):
    want = {f"labels/{seg}/{seg}_{k}.txt": k for k in ks}
    got = {}
    names = []
    with tarfile.open(tar_path, "r:") as t:
        for m in t:
            if m.name.startswith("labels/"):
                names.append(m.name)
            if m.name in want:
                got[want[m.name]] = t.extractfile(m).read().decode()
    return got, names


def boxes_from_txt(txt):
    rows = [list(map(float, l.split())) for l in txt.strip().splitlines() if l.strip()]
    return np.array(rows) if rows else np.zeros((0, 8))


def points_in_boxes(pts, boxes):
    """pts (N,3) in top frame; boxes (M,8) cls cx cy cz dx dy dz yaw. Returns count per box."""
    counts = []
    for b in boxes:
        _, cx, cy, cz, dx, dy, dz, yaw = b
        p = pts - np.array([cx, cy, cz])
        c, s = np.cos(-yaw), np.sin(-yaw)
        x = c * p[:, 0] - s * p[:, 1]
        y = s * p[:, 0] + c * p[:, 1]
        m = (np.abs(x) <= dx / 2) & (np.abs(y) <= dy / 2) & (np.abs(p[:, 2]) <= dz / 2)
        counts.append(int(m.sum()))
    return np.array(counts)


def rsu_points_top(k):
    pts = []
    for stream, off in (("top", TOP_FROM_MAP), ("dome", DOME_FROM_MAP)):
        g, _ = read_pcd(find(stream, k))
        xyz = g[..., :3].reshape(-1, 3).astype(np.float64)
        vals, counts = np.unique(xyz, axis=0, return_counts=True)
        ph = np.all(xyz == vals[np.argmax(counts)], axis=1)
        # both RSU clouds raw in map frame; top frame = map + TOP_FROM_MAP (identity rotation, per devkit)
        pts.append(xyz[~ph] + TOP_FROM_MAP)
    return np.concatenate(pts)


if __name__ == "__main__":
    res = {"pilot": "P1", "segment": SEG, "status": "pilot evidence on exposed development data"}
    origins = {"003": np.array([0, 0, 1.63]), "004": np.array([0, 0, 1.90]), "laser": np.array([0, 0, 1.90]),
               "top": -TOP_FROM_MAP, "dome": -DOME_FROM_MAP}
    res["grid"] = [grid_stats(s, 125, origins[s]) for s in ("003", "004", "laser", "top", "dome")]
    ks = [60, 61, 62, 125, 126, 127, 200, 201, 202]
    tar = f"{ROOT}/archives/train/{SEG}.tar"
    labels, names = load_labels(tar, SEG, set(ks) | {k - 1 for k in ks} | {k + 1 for k in ks})
    idx = sorted(int(n.rsplit("_", 1)[1].split(".")[0]) for n in names)
    res["label_members"] = {"count": len(names), "min": idx[0], "max": idx[-1],
                            "missing_between": [i for i in range(idx[0], idx[-1] + 1) if i not in set(idx)]}
    cmp = []
    for k in (61, 126, 201):
        b = boxes_from_txt(labels.get(k, ""))
        row = {"label_k": k, "n_boxes": int(len(b))}
        for off in (-1, 0, 1):
            pts = rsu_points_top(k + off)
            c = points_in_boxes(pts, b)
            row[f"cloud_k{off:+d}_sum_pts_in_boxes"] = int(c.sum())
            row[f"cloud_k{off:+d}_boxes_with_gt5"] = int((c > 5).sum())
        cmp.append(row)
    res["label_sync_check"] = cmp
    print(json.dumps(res, indent=1))
