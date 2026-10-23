"""D-66 baseline B-NORM: sender-level feature-magnitude check (no ground truth, no attack ledger).

For sender i and fusion scale k, ratio_ik = mean |feature_i,k| / mean |feature_receiver,k| (means over all
elements of that agent's scale-k map). Sender i is dropped entirely in the frame iff ratio_ik > tau_k at any
scale k; tau_k = 99.5th percentile of ratio_ik over clean block-H frames (recorded in the PGD plan; the
only fitted quantity). Output = candidates decoded without the dropped senders.
"""
import numpy as np


def mean_abs(feats):
    """[n, K] float64: mean |x| of each agent's map at each scale (feats: list over scales of [n, C, H, W])."""
    return np.stack([f.abs().double().mean(dim=(1, 2, 3)).numpy() for f in feats], 1)


def ratios(mabs):
    """[n-1, K] ratios of senders 1..n-1 to the receiver (row 0 of mabs)."""
    m = np.asarray(mabs, np.float64)
    return m[1:] / m[0][None]


def flagged(mabs, tau):
    """Senders (1-based record indices) with ratio > tau at any scale."""
    r = ratios(mabs)
    tau = np.asarray(tau, np.float64)
    return [i + 1 for i in range(r.shape[0]) if bool(np.any(r[i] > tau))]


def output_cands(cands, mabs, tau):
    """Candidate set B-NORM decodes: cands[frozenset(flagged senders)] (all subsets are in cands)."""
    return cands[frozenset(flagged(mabs, tau))]
