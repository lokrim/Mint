"""CPU stand-ins for GPU-only modules that OpenCOOD imports, so the *unmodified*
OpenCOOD source can run on a machine without CUDA/spconv.

`install()` registers fake `spconv.utils` and `cumm.tensorview` modules in sys.modules.
The voxelizer reproduces spconv v1 `VoxelGeneratorV2.generate` semantics as used by
OpenCOOD's SpVoxelPreprocessor:
  * voxel index = floor((p - range_min) / voxel_size), kept iff 0 <= idx < grid;
  * voxels are created in order of first point appearance; once `max_voxels`
    voxels exist, points falling in new voxels are dropped;
  * at most `max_num_points` points per voxel, in input order; extra points dropped;
  * coordinates returned as (z, y, x) int32; features zero-padded.
Equivalence to real spconv is NOT verified here (no spconv on this machine); the
reproduction-AP check in Stage 1 is the end-to-end test of this assumption.
"""
import sys
import types

import numpy as np


class VoxelGeneratorV2:
    def __init__(self, voxel_size, point_cloud_range, max_num_points, max_voxels=20000, **_):
        self.voxel_size = np.asarray(voxel_size, dtype=np.float32)
        self.pc_range = np.asarray(point_cloud_range, dtype=np.float32)
        self.grid = np.round((self.pc_range[3:] - self.pc_range[:3]) / self.voxel_size).astype(np.int64)
        self.max_num_points = int(max_num_points)
        self.max_voxels = int(max_voxels)

    def generate(self, points):
        pts = np.asarray(points, dtype=np.float32)
        idx = np.floor((pts[:, :3] - self.pc_range[:3]) / self.voxel_size).astype(np.int64)
        ok = np.all((idx >= 0) & (idx < self.grid), axis=1)
        pts, idx = pts[ok], idx[ok]
        key = (idx[:, 2] * self.grid[1] + idx[:, 1]) * self.grid[0] + idx[:, 0]
        uniq, first, inv = np.unique(key, return_index=True, return_inverse=True)
        order = np.argsort(first, kind="stable")          # voxel creation order
        rank = np.empty_like(order)
        rank[order] = np.arange(order.size)
        vox_id = rank[inv]                                 # voxel slot per point
        keep_vox = vox_id < self.max_voxels
        pts, idx, vox_id = pts[keep_vox], idx[keep_vox], vox_id[keep_vox]
        n_vox = int(min(order.size, self.max_voxels))
        # position of each point within its voxel, in input order
        sort = np.argsort(vox_id, kind="stable")
        sv = vox_id[sort]
        start = np.searchsorted(sv, np.arange(n_vox))
        pos_sorted = np.arange(sv.size) - start[sv]
        pos = np.empty_like(pos_sorted)
        pos[sort] = pos_sorted
        keep_pt = pos < self.max_num_points
        voxels = np.zeros((n_vox, self.max_num_points, pts.shape[1]), dtype=np.float32)
        voxels[vox_id[keep_pt], pos[keep_pt]] = pts[keep_pt]
        num = np.minimum(np.bincount(vox_id, minlength=n_vox), self.max_num_points).astype(np.int32)
        coords = np.zeros((n_vox, 3), dtype=np.int32)
        coords[vox_id, :] = idx[:, ::-1]                   # (z, y, x)
        return {"voxels": voxels, "coordinates": coords, "num_points_per_voxel": num}


class _PointCloud:
    def __init__(self, points, colors):
        self.points = points
        self.colors = colors


def read_point_cloud(path, *_, **__):
    """Minimal stand-in for open3d.io.read_point_cloud for ASCII PCD with fields x y z rgb.

    Real open3d cannot be imported alongside torch here (OpenMP runtime clash -> deadlock).
    Decodes rgb as open3d does: float32 bits -> uint32 0x00RRGGBB -> channels / 255.
    Byte-equality with real open3d is checked by tools/check_pcd_shim.py.
    """
    with open(path, "rb") as f:
        fields = None
        while True:
            line = f.readline().decode("ascii").strip()
            if line.startswith("FIELDS"):
                fields = line.split()[1:]
            if line.startswith("DATA"):
                if line.split()[1] != "ascii":
                    raise NotImplementedError("only ASCII PCD supported by the stand-in")
                break
        arr = np.loadtxt(f, dtype=np.float64, ndmin=2)
    if fields != ["x", "y", "z", "rgb"]:
        raise NotImplementedError(f"unsupported PCD fields {fields}")
    points = arr[:, :3].copy()
    packed = arr[:, 3].astype(np.float32).view(np.uint32)
    colors = np.stack([(packed >> 16) & 255, (packed >> 8) & 255, packed & 255], axis=1).astype(np.float64) / 255.0
    return _PointCloud(points, colors)


def install():
    if "open3d" not in sys.modules:
        o3d = types.ModuleType("open3d")
        io = types.ModuleType("open3d.io")
        io.read_point_cloud = read_point_cloud
        o3d.io = io
        sys.modules["open3d"] = o3d
        sys.modules["open3d.io"] = io
    if "spconv" not in sys.modules:
        spconv = types.ModuleType("spconv")
        utils = types.ModuleType("spconv.utils")
        utils.VoxelGeneratorV2 = VoxelGeneratorV2
        spconv.utils = utils
        sys.modules["spconv"] = spconv
        sys.modules["spconv.utils"] = utils
    if "cumm" not in sys.modules:
        cumm = types.ModuleType("cumm")
        tv = types.ModuleType("cumm.tensorview")
        cumm.tensorview = tv
        sys.modules["cumm"] = cumm
        sys.modules["cumm.tensorview"] = tv
