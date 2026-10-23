"""X3: benign sender localization error with per-frame, per-sender noise.

OpenCOOD's BaseDataset.add_loc_noise reseeds np.random with a fixed seed on every call, so every frame
and sender get the same offset (a constant bias). We replace the method on one dataset instance (OpenCOOD
is not modified) with Gaussian noise keyed by SHA-256(seed, scenario, timestamp pose). Pose layout in
OPV2V yaml: [x, y, z, roll, yaw, pitch], angles in degrees; as OpenCOOD, only yaw gets angular noise."""
import hashlib

import numpy as np


def keyed_rng(*parts):
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return np.random.default_rng(int.from_bytes(h[:8], "little"))


def install_loc_noise(ds, xyz_std, yaw_std_deg, seed=0, tag="X3"):
    def add_loc_noise(pose, xyz_std_=None, ryp_std_=None):
        rng = keyed_rng(tag, seed, *[round(float(v), 4) for v in pose])
        e = rng.normal(0.0, 1.0, 4)
        return [pose[0] + xyz_std * e[0], pose[1] + xyz_std * e[1], pose[2] + xyz_std * e[2],
                pose[3], pose[4] + yaw_std_deg * e[3], pose[5]]
    ds.add_loc_noise = add_loc_noise
    ds.loc_err_flag = True
    ds.xyz_noise_std, ds.ryp_noise_std = xyz_std, yaw_std_deg
    return ds


def set_async(ds, delay_ms):
    ds.async_flag = delay_ms > 0
    ds.async_mode = "sim"
    ds.async_overhead = delay_ms
    return ds
