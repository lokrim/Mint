import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
from mint.effects.effects import effects  # noqa: E402
from mint.model.warp import warp_to_receiver  # noqa: E402
from test_rays import corners  # noqa: E402

RANGE = [-140.8, -40, -3, 140.8, 40, 1]


def test_warp_moves_feature_by_sender_to_receiver_transform():
    h, w = 25, 88                                    # 3.2 m cells
    f = torch.zeros(1, h, w)
    # sender-frame point (x=16, y=8) -> cell
    q, r = int((16 + 140.8) / 3.2), int((8 + 40) / 3.2)
    f[0, r, q] = 1.0
    yaw = np.pi / 2                                  # sender rotated 90 deg, offset (+6.4, -3.2)
    T = np.array([[np.cos(yaw), -np.sin(yaw), 0, 6.4], [np.sin(yaw), np.cos(yaw), 0, -3.2],
                  [0, 0, 1, 0], [0, 0, 0, 1]])
    g = warp_to_receiver(f, T, RANGE)
    x_s = (q + 0.5) * 3.2 - 140.8
    y_s = (r + 0.5) * 3.2 - 40
    pe = T @ np.array([x_s, y_s, 0, 1])
    q2, r2 = int((pe[0] + 140.8) / 3.2), int((pe[1] + 40) / 3.2)
    # 90 deg rotation maps cell centres onto cell corners: bilinear spreads mass over 4 cells
    assert g[0, r2, q2].item() > 0.2
    assert abs(g[0].sum().item() - 1.0) < 1e-5
    # whole-cell translation keeps the peak intact at the predicted cell
    T2 = np.eye(4); T2[0, 3], T2[1, 3] = 6.4, -3.2
    g2 = warp_to_receiver(f, T2, RANGE)
    assert g2[0].argmax().item() == (r - 1) * w + (q + 2)
    assert abs(g2[0, r - 1, q + 2].item() - 1.0) < 1e-5


def test_identity_warp_is_noop():
    f = torch.randn(4, 25, 88)
    # float32 sampling-grid rounding gives ~2e-5 deviations; anything larger is a real bug
    assert torch.allclose(warp_to_receiver(f, np.eye(4), RANGE), f, atol=1e-4)


def test_effects_types():
    a = corners(10, 0, 0, 4, 2, 1.5, 0)
    b = corners(20, 5, 0, 4, 2, 1.5, 0)
    a_shift = corners(10.8, 0, 0, 4, 2, 1.5, 0)
    assert effects(np.stack([a, b]), [0.9, 0.8], np.stack([a, b]), [0.9, 0.8]) == []
    e = effects(np.stack([a, b]), [0.9, 0.8], np.stack([a]), [0.9])
    assert [x["type"] for x in e] == ["ADD"]
    e = effects(np.stack([a]), [0.9], np.stack([a, b]), [0.9, 0.8])
    assert [x["type"] for x in e] == ["REMOVE"]
    e = effects(np.stack([a_shift]), [0.9], np.stack([a]), [0.9])
    assert [x["type"] for x in e] == ["SHIFT"]
