"""Check the open3d PCD stand-in against real open3d (run in a process WITHOUT torch).

  python tools/check_pcd_shim.py <folder with .pcd files, searched recursively>
Prints per-file max abs differences of points and colors, and a summary.
"""
import glob
import importlib.util
import json
import os
import sys

import numpy as np
import open3d as o3d

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("shims", os.path.join(ROOT, "src/mint/model/opencood_shims.py"))
shims = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shims)

files = sorted(glob.glob(os.path.join(sys.argv[1], "**", "*.pcd"), recursive=True))
worst_p = worst_c = 0.0
mismatched_shape = 0
for fp in files:
    a = o3d.io.read_point_cloud(fp)
    b = shims.read_point_cloud(fp)
    pa, ca = np.asarray(a.points), np.asarray(a.colors)
    if pa.shape != b.points.shape or ca.shape != b.colors.shape:
        mismatched_shape += 1
        continue
    worst_p = max(worst_p, float(np.abs(pa - b.points).max()))
    worst_c = max(worst_c, float(np.abs(ca - b.colors).max()))
print(json.dumps({"files": len(files), "shape_mismatches": mismatched_shape,
                  "max_abs_diff_points": worst_p, "max_abs_diff_colors": worst_c,
                  "open3d": o3d.__version__}))
