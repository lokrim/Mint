# R1 methodology figure: notes

Files: `r1_method.tex` (TikZ, `figure*`, label `fig:r1method`), `r1_method_preview.svg` (hand-laid preview, same
coordinates at 1 cm = 50 px, Times instead of Computer Modern). The figure is **not** `\input` in `main.tex` yet.
No result, number or code was changed.

## Draft caption

R1 per receiver frame. The frozen AttFuse detector decodes once with all agents ($Y^{+}$, step 1) and once
without each sender ($Y^{-}(i)$, step 2). Their differences are ADD, REMOVE and SHIFT effects, each attributed
to a sender $i$ and a 6.4 m tile $u$ (step 3), and every effect box is checked against the receiver's own LiDAR
rays with a Wilson-95 resolvability margin; too few rays or the receiver's own box give UNKNOWN, which keeps the
sender (step 4, inset). Sender $i$ is switched off in tile $u$ only if an effect resolvably contradicts the rays
and none is resolvably confirmed (step 5), and the output is composed tile by tile from the decodes already
computed, before NMS, together with a per-(sender, tile) reliability record (step 6).

## Plain-English explanation

1. The receiver runs the unchanged detector once on everything it received: that is the normal output.
2. Then, for each sender, it runs the detector again as if that sender had stayed silent.
3. Comparing the two outputs shows what each sender changed: a car it added, a car it made disappear, or a car it moved.
4. Each change is tied to one sender and one 6.4 m square of the map.
5. The receiver checks each change against its own laser returns: rays that stop inside a claimed car confirm it, rays that fly straight through it refute it.
6. If too few of its own rays reach the spot (hidden or far away), the receiver cannot tell, and it keeps the sender there.
7. A sender is switched off in a square only when its rays clearly refute one of that sender's changes there and clearly confirm none of them.
8. The final boxes are stitched square by square from the runs already done, so no extra detector run is needed (except where two senders are switched off in the same square), and the receiver also keeps a per-sender, per-square log of what it found.

## Checked against the code

| Figure element | Source |
|---|---|
| $Y^{+}$, $Y^{-}(i)$ for $i=1..n-1$ (`senders = range(1, n)`), one decode each | `pipeline.py` `mint_frame`, `counterfactual_heads` |
| Effects on post-NMS boxes; Hungarian on BEV IoU, match iff IoU ≥ 0.1; SHIFT iff centre > 0.3 m or yaw > 10° | `effects.py` `effects()` |
| Tile of the box centre, 6.4 m; SHIFT/either version → unit $(i,u)$ | `effects.tile_of`, `pipeline.TILE_M`, `v0.units` |
| SUP / TRAV / OCC (ends before = ignored); $N=\mathrm{SUP}+\mathrm{TRAV}$; $N<3$ → UNKNOWN; own box → not applicable | `rays.classify_points`, `v0.effect_status` (`n_min=3`) |
| Wilson-95 gate/useful rules for ADD, REMOVE, SHIFT; "none" otherwise | `r1.effect_verdict`, `r1.wilson` |
| Unit gated iff all effects KNOWN, ≥1 gate, no useful | `r1.assess` |
| Composition per tile on pre-NMS candidates, then box filters + rotated NMS + range; extra decode only if ≥2 senders gated in a tile | `compose.compose`, `compose.finalize`, `pipeline.mint_frame` (`extra`) |
| Inset numbers: 0/4 → hi = 0.490 (gates); 4/4 → lo = 0.510 (useful) | computed with the formula of `r1.wilson` |

## Could not verify, or simplified (please check)

1. **Notation.** The request used $F_0..F_n$ and "$n$ senders". The paper uses agents $0..n-1$, features
   $f_{i,k}$, and $\mathrm{Fuse}$/$\mathrm{Dec}$ (eq. `eq:cf`), so the figure has senders $1..n-1$ and $n-1$
   counterfactual decodes. $P_0$ for the receiver's scan is **new notation** (the paper says "the receiver's own scan");
   it needs one sentence in the Method section if kept.
2. **"Crosses the effect box."** In the code a ray counts only if it crosses the box **core** (footprint shrunk by
   15 % per side, at least 0.15 m; vertical band 0.3 m above the bottom to 0.1 m below the top), and SUP/TRAV are
   judged against an **envelope** dilated by 0.2 m with tolerance 0.05 m + 1 % of range (`rays.classify_points`).
   The figure and the paper both simplify this to "the box".
3. **Own-vehicle box** is a separate status in the code (`NOT_APPLICABLE_SELF`: sensor inside the box footprint in BEV,
   0.2 m margin) and is kept like UNKNOWN. The figure lumps it with UNKNOWN; the record lists three statuses
   (KNOWN, UNKNOWN_NO_EVIDENCE, NOT_APPLICABLE_SELF). The record also stores a diagnostic score (#gate − #useful),
   which is not shown.
4. **UNKNOWN is per unit.** One effect without evidence makes the whole unit $(i,u)$ UNKNOWN, even if another effect in
   it gates. That is why the inset places the hidden box in a different tile $u'$.
5. **Tile assignment in composition.** `compose()` assigns pre-NMS candidates to tiles by their **anchor** cell
   (head grid, 8 cells × 0.8 m). Effects are assigned by the **box centre** (`tile_of` with `pc_range`). Eq. `eq:compose`
   in `main.tex` says "$b$ centred in $u$", which describes the effect rule, not the composition. That is a possible wording
   issue in the paper; I did not change it. I did not check that the two tile grids line up exactly (that depends on
   `pc_range` in the config, which was not on the reading list).
6. **"Post-fusion is pixel-local"** is taken from the `compose.py`/`pipeline.py` docstrings (check V-03). I did not re-read
   the model code (`attfuse_parts.py`, not on the list).
7. **Ray-count variant.** `Params.variant` defaults to `"std"` (shown here). I did not check whether the frozen test
   configuration used `"std"` or `"gnd"` (ground-aware), because the run config was not on the list.
8. **Counterfactual mode.** "Run $n$ times" assumes the exact modes (`sequential` / `batched`). `footprint` and
   `trigger` are diagnostic or rejected (D-49) and are not shown.
9. **Not compiled.** No LaTeX is installed locally. Node heights use fixed minimum heights, and Computer Modern at
   `\scriptsize` may wrap more than the Times preview, so check the compile on Overleaf. At full width the figure is
   about 18 × 9.6 cm. If that is too tall: drop the contrast box (keep one line under the flow), or move the inset
   beside the contrast box at about 2/3 of its height.
10. **Overlap with existing figures.** `fig:pipeline` (Fig. 1) and `fig:r1` (Fig. 2) already cover parts of this figure.
    Whether this figure replaces `fig:r1` is your call.
