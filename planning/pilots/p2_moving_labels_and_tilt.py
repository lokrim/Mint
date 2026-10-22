"""PILOT P2 (disposable; mini_7 development data only).

Q3b. Label k vs cloud k+off for MOVING boxes only (centre displacement > 1 m over +/-2 labels).
Q1b. For tilted streams (003, top), does a single fitted mounting rotation make each grid
     row a constant-elevation beam?  (Needed to give no-return slots a direction.)
"""
import json
import numpy as np
from p1_grid_and_labels import (ROOT, SEG, read_pcd, find, load_labels, boxes_from_txt,
                                points_in_boxes, rsu_points_top, TOP_FROM_MAP)


def rot(rx, ry):
    cx, sx, cy, sy = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return Ry @ Rx


def row_std_after(d, valid, R):
    q = d @ R.T
    el = np.degrees(np.arctan2(q[..., 2], np.linalg.norm(q[..., :2], axis=-1)))
    s = [np.std(el[i][valid[i]]) for i in range(el.shape[0]) if valid[i].sum() > 50]
    return float(np.median(s))


def fit_tilt(stream, k, origin):
    g, _ = read_pcd(find(stream, k))
    xyz = g[..., :3].astype(np.float64)
    vals, counts = np.unique(xyz.reshape(-1, 3), axis=0, return_counts=True)
    ph = np.all(xyz == vals[np.argmax(counts)], axis=-1)
    d = xyz - origin
    valid = (~ph) & (np.linalg.norm(d, axis=-1) > 0.3)
    best = (row_std_after(d, valid, np.eye(3)), 0.0, 0.0)
    for coarse in (np.radians(np.arange(-30, 31, 2.5)), None):
        if coarse is None:
            c0x, c0y = best[1], best[2]
            gx = c0x + np.radians(np.arange(-2.5, 2.6, 0.25))
            gy = c0y + np.radians(np.arange(-2.5, 2.6, 0.25))
        else:
            gx = gy = coarse
        for rx in gx:
            for ry in gy:
                s = row_std_after(d, valid, rot(rx, ry))
                if s < best[0]:
                    best = (s, rx, ry)
    return {"stream": stream, "row_elev_std_before_deg": round(row_std_after(d, valid, np.eye(3)), 3),
            "row_elev_std_after_deg": round(best[0], 3),
            "fitted_rx_deg": round(float(np.degrees(best[1])), 2), "fitted_ry_deg": round(float(np.degrees(best[2])), 2)}


if __name__ == "__main__":
    out = {"pilot": "P2", "segment": SEG}
    out["tilt_fit"] = [fit_tilt("003", 125, np.array([0, 0, 1.63])), fit_tilt("top", 125, -TOP_FROM_MAP)]
    ks = list(range(40, 231, 30))
    need = {k + o for k in ks for o in range(-3, 4)}
    labels, _ = load_labels(f"{ROOT}/archives/train/{SEG}.tar", SEG, need)
    rows = []
    for k in ks:
        b0 = boxes_from_txt(labels.get(k, ""))
        bm, bp = boxes_from_txt(labels.get(k - 2, "")), boxes_from_txt(labels.get(k + 2, ""))
        if len(b0) == 0 or len(bm) == 0 or len(bp) == 0:
            continue
        # moving = nearest box in k-2 and k+2 differ by > 1 m (no track ids in TXT; nearest-centre proxy)
        mov = []
        for b in b0:
            dm = np.min(np.linalg.norm(bm[:, 1:3] - b[1:3], axis=1))
            dp = np.min(np.linalg.norm(bp[:, 1:3] - b[1:3], axis=1))
            if dm > 0.5 and dp > 0.5 and dm < 4 and dp < 4:
                mov.append(b)
        if not mov:
            continue
        mov = np.array(mov)
        r = {"label_k": k, "n_moving": int(len(mov))}
        for off in range(-3, 4):
            r[f"off{off:+d}"] = int(points_in_boxes(rsu_points_top(k + off), mov).sum())
        r["argmax_offset"] = max(range(-3, 4), key=lambda o: r[f"off{o:+d}"])
        rows.append(r)
    out["moving_box_label_sync"] = rows
    print(json.dumps(out, indent=1))
