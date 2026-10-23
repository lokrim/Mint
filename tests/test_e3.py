"""E3: trigger mask T(f), tile gather for fusion, tile-native candidates, tile decode vs dense decode."""
import os
import sys

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import e0_analyze as A  # noqa: E402  (installs shims, paths)
from mint.fusion.compose import TILE_PX, candidates, tile_candidates  # noqa: E402
from mint.model.attfuse_parts import decode, decode_batch, fuse_scale  # noqa: E402
from mint.reliability import pipeline as PL  # noqa: E402

H, W = 100, 352


def _logit(p):
    return float(np.log(p / (1 - p)))


def test_trigger_mask_threshold_dilation_and_padding():
    psm = torch.full((1, 2, H, W), -20.0)
    psm[0, 1, 50, 100] = _logit(0.10)          # tile (6, 12)
    psm[0, 0, 99, 0] = _logit(0.06)            # last, half-padded tile row (12, 0)
    t10 = PL.trigger_mask(psm, 0.10)
    assert t10.shape == (13, 44)
    assert set(map(tuple, torch.nonzero(t10).tolist())) == {(r, c) for r in (5, 6, 7) for c in (11, 12, 13)}
    t05 = PL.trigger_mask(psm, 0.05)
    assert int(t05.sum()) == 9 + 4             # corner tile dilated within the grid: rows 11-12, cols 0-1
    assert bool(t05[12, 0]) and bool(t05[11, 1]) and not bool(t05[12, 2])
    assert int(PL.trigger_mask(psm, 0.10, dilate=0).sum()) == 1
    assert int(PL.trigger_mask(psm, 0.11).sum()) == 0
    assert float(PL.tile_max_prob(psm)[6, 12]) == float(torch.sigmoid(torch.tensor(_logit(0.10))))


def _feats(n, seed=0):
    g = torch.Generator().manual_seed(seed)
    return [torch.randn(n, 8, H, W, generator=g), torch.randn(n, 16, H // 2, W // 2, generator=g),
            torch.randn(n, 32, H // 4, W // 4, generator=g)]


def test_tile_fusion_bitwise_equals_dense():
    n = 3
    feats = _feats(n)
    sel = torch.tensor([[0, 0], [5, 7], [12, 43], [12, 3], [6, 20]])
    g = PL.gather_tiles(feats, n, sel)
    for k, (f, x) in enumerate(zip(feats, g)):
        px = x.shape[3]
        for i in (1, 2):
            md = torch.ones((n, f.shape[2], f.shape[3]), dtype=torch.bool)
            md[i] = False
            mt = torch.ones((n, x.shape[2], x.shape[3]), dtype=torch.bool)
            mt[i] = False
            dense = PL._to_tiles(fuse_scale(f, md)[0], px)[sel[:, 0], sel[:, 1]]
            y = fuse_scale(x, mt)[0]
            tiles = y.reshape(y.shape[0], len(sel), px, px).permute(1, 0, 2, 3)
            assert torch.equal(tiles, dense)


class _Backbone(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks = [None, None, None]
        self.deblocks = torch.nn.ModuleList([
            torch.nn.Sequential(torch.nn.ConvTranspose2d(c, 12, s, s, bias=False), torch.nn.BatchNorm2d(12), torch.nn.ReLU())
            for c, s in ((8, 1), (16, 2), (32, 4))])


class _Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(0)
        self.backbone = _Backbone()
        self.cls_head = torch.nn.Conv2d(36, 2, 1)
        self.reg_head = torch.nn.Conv2d(36, 14, 1)
        for m in self.modules():
            if isinstance(m, torch.nn.BatchNorm2d):
                m.running_mean.uniform_(-0.5, 0.5)
                m.running_var.uniform_(0.5, 2.0)
        self.eval()


@torch.no_grad()
def test_trigger_heads_match_dense_counterfactual():
    model, n = _Model(), 3
    feats = _feats(n, 1)
    sel = torch.tensor([[0, 0], [5, 7], [12, 43], [6, 20]])
    th = PL.trigger_heads(model, feats, n, [1, 2], sel)
    for i in (1, 2):
        m = PL._exclude_masks(feats, n, [i])
        psm, rm = decode(model, [fuse_scale(f, m[k])[0] for k, f in enumerate(feats)])
        for dn, tt in ((psm, th[i][0]), (rm, th[i][1])):
            d = PL._to_tiles(dn[0], TILE_PX)[sel[:, 0], sel[:, 1]]
            rows = sel[:, 0, None] * TILE_PX + torch.arange(TILE_PX)
            valid = (rows < H)[:, None, :, None].expand_as(d)
            assert float((d - tt).abs()[valid].max()) <= 1e-4 * max(1.0, float(d.abs().max()))
    assert PL.trigger_heads(model, feats, n, [1], sel[:0]) == {1: None}
    assert decode_batch is not None


def test_tile_candidates_equal_dense_restricted():
    pp = A.post_processor()
    anchors = torch.from_numpy(np.asarray(pp.generate_anchor_box(), np.float32))
    assert anchors.shape == (H, W, 2, 7)
    g = torch.Generator().manual_seed(3)
    psm = torch.randn(1, 2, H, W, generator=g) * 2 - 2
    rm = torch.randn(1, 14, H, W, generator=g) * 0.3
    tm = torch.eye(4)
    dense = candidates(pp, psm, rm, anchors, tm)
    assert len(dense.idx) > 50
    sel = torch.tensor([[12, 43], [0, 0], [5, 7], [12, 3], [6, 20]])            # unsorted on purpose
    pt = PL._to_tiles(psm[0], TILE_PX)[sel[:, 0], sel[:, 1]]
    rt = PL._to_tiles(rm[0], TILE_PX)[sel[:, 0], sel[:, 1]]
    tc = tile_candidates(pp, pt, rt, sel, anchors, tm, (H, W))
    mask = torch.zeros(13, 44, dtype=torch.bool)
    mask[sel[:, 0], sel[:, 1]] = True
    r, c = dense.tiles()
    ref = dense.take(mask.numpy()[r, c])
    assert len(ref.idx) > 0 and np.array_equal(tc.idx, ref.idx)
    assert np.array_equal(tc.scores, ref.scores)
    np.testing.assert_allclose(tc.corners, ref.corners, rtol=0, atol=1e-5)
    assert (tc.idx // 2 // W < H).all()
    empty = tile_candidates(pp, pt[:0], rt[:0], sel[:0], anchors, tm, (H, W))
    assert len(empty.idx) == 0 and empty.corners.shape == (0, 8, 3)
