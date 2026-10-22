# 03 — Dataset, ground truth and feature feasibility

Revision 2 (2026-10-22). Status markers: **[D]** documented by a source; **[L]** locally inspected in this audit; **[R]** reported by an old artifact, not re-checked; **[X]** derived from code; **[S]** simulated or modeled; **[U]** unknown.

## 1. Exact local inventory

**Source and location.** Hugging Face dataset `sberrio/Mixed-Signals-V2X`, recorded revision `1a61aea747aa6bc45da2c2f085a1f1d3abc41f91` [R]. The revision is a pin recorded by the old project, not a fresh remote check. Local root (relative to the old repo): `data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91/` with subfolders `archives/train/`, `raw/PointClouds/<seg>/`, `raw/Odometry/<seg>/` and `manifests/`. All of it is git-ignored.

| Segment | Old role | TAR bytes [L stat] | Extracted PCDs [L] | Odometry CSVs [L] | Label TXT members in saved inventory [L] |
|---|---|---:|---:|---:|---:|
| mini_7 | development | 7,894,272,000 | 1,250 (~6.4 GB) | 3 | 290 (ids 1–290) |
| mini_10 | C0 | 7,853,803,520 | 1,250 | 3 | 291 (1–291) |
| mini_11 | C1 | 7,763,056,640 | 1,246 | 3 | 290 (1–290) |
| mini_12 | C2 | 7,837,788,160 | 1,250 | 3 | 289 (2–290) |
| mini_13 | C3 | 7,802,398,720 | 1,250 | 3 | 290 (1–290) |
| mini_14 | final holdout H | **absent locally** | — | — | not inspected |

- **Archive contents.** Each TAR holds about 1,485–1,495 PCD members (297–299 per stream), 3 odometry CSVs and the label TXTs (from `*_safe_member_inventory.json`; mini_7's inventory is in `artifacts/20261008T192922Z-R01/`).
- **Extracts.** Only the first ~25 s (≤300 sync indices) were extracted.
- **Labels.** No `raw/labels/` directory exists. Label bodies were never extracted or read by the old pipeline.
- **Hashes.** I recomputed no TAR or bulk-PCD hashes. R05 intake reports TAR and 5,008 extract hashes matching the pins [R]. I hashed only 15 odometry CSVs and 25 sampled PCDs ([placeholder_probe.json](evidence/r2/placeholder_probe.json)).

**Licence and release [D, current card fetched 2026-10-22].**
- CC BY-NC-SA 4.0 (non-commercial, share-alike).
- 37 segments mini_1–mini_37. Train: 29 with labels; validation: 4 and test: 4, labels withheld.
- Label files `labels/mini_N/mini_N_<syncIndex>.txt`, one box per line `cls cx cy cz dx dy dz yaw`. Classes 1 Vehicle, 2 Bike, 3 Pedestrian. Metres/radians, **in the `top` RSU frame**. Boxes are restricted to x, y ∈ [−51.2, 51.2] m and to more than 5 aggregated LiDAR points. **An empty file means no labelled objects.**

The card was fetched at its current revision, not the pinned one. Byte equality with the local archives is not established. The older ACFR/devkit JSON/PKL annotations are a different release: do not mix them in silently (preserved notes: [sources.md](evidence/source/planning/sources.md)).

**Label index risk (DA-07).** Label IDs run 1–290 (mini_12 starts at 2), while cloud sync IDs run 0–298. Whether label k matches sync index k, or k−1, is **unverified** and must be checked against geometry before any task metric. A missing file (e.g. sync 0, or IDs above 290) is not the same as an empty file. Label filtering (>5 points, ±51.2 m crop) means labels are *not* complete ground truth for sparse or far objects. This matters for judging an "honest unique view".

## 2. Fields, frames and clocks

| Quantity | Status | Detail |
|---|---|---|
| PCD layout | [L] | ASCII `x y z intensity` float32. **Organized**: 003/004 2048×128, laser/dome 1024×128, top 1024×64; POINTS = W×H; header `VIEWPOINT 0 0 0 1 0 0 0`. |
| Placeholder slots | [L] counts, [U] meaning | One fixed coordinate repeated in every cloud: 003 (0,0,1.63) ~21–25%; 004 (0,0,1.90) ~23–25%; laser (0,0,1.90) ~2–6%; dome = published dome origin ~11–13%; top = published top origin ~37–39% (25 clouds; DA-02). Probably no-return beams; not documented. |
| Intensity | [L]/[R] | 003 and 004 exactly 0 in sampled clouds; other streams have device-specific integer-like values. Excluded from scoring. |
| Stream → principal | [X] `STREAM_PRINCIPAL` | 003, 004, laser = vehicles; top + dome = **one RSU principal**. Four principals, five streams. |
| Cloud time | [X] `parse_stamp` | `<stream>_<sync>_<sec>.<sub>.pcd`; a short sub-second field is **left-padded** to ns. The sync index is kept separately, and the same sync index does not mean the same time. R01 reports 147/1,495 short sub-second names in mini_7 and 50.6–59.9 ms cross-stream skew [R]. |
| Scan timing / deskew | [U] | No per-point time, no scan start/end and no clock-accuracy statement. |
| Odometry | [L] | 15 CSVs, each 300 rows × 90 columns. `frame_id=map`, `child_frame_id=base_link_<veh>`. Orientation columns ordered x, y, z, w; the code reads them by name into `pose_matrix(…, wxyz)`. Six twist columns, finite and variable in all 15 (DA-11). Twist frame, provenance and independence are [U]. |
| Pose selection | [X] | Latest past pose with source ≤ event and availability ≤ deadline, age ≤ 150 ms. Availability = recorded stamp [S]. Recorded poses may be offline-smoothed [U]. |
| Receiver arrival | [S] | Arrival = source time; deadline = event time. No network data exists. |
| RSU frame | [X]+[L] | Raw top/dome XYZ are in a map frame. `TOP_FROM_MAP=(+41.551,+51.878,+1.077)` and `DOME_FROM_MAP=(+41.507,+51.864,+1.340)` with identity rotation. Sensor origins in raw coordinates are the negatives. **The placeholder points sit exactly at these origins**, which independently corroborates them (DA-09). |
| Vehicle frame | [X]+[L] | Raw vehicle XYZ are in a native frame. D/G assume the XY origin is (0, 0). Placeholders at (0, 0, 1.63/1.90) suggest the sensor origin is at that native z [hypothesis]. The devkit's paired −3.25/+3.25 m z adjustments cancel in the code's composition [X]. Physical extrinsics are [U]. |
| Labels | [D]+[L inventory only] | See §1. Bodies not opened. |
| Visibility / occlusion truth | [U] | ACFR `gt_visibility` is derived from points inside GT boxes. It is not an independent measurement and must not be used at inference. |

## 3. What genuine intermediate features would require

Nothing in the old repo produces features: there is no encoder, detector, fusion module or checkpoint, and the dependencies are numpy and matplotlib (DA-15). Turning these clouds into intermediate features is a model-integration project, not a format conversion. It needs:

1. A **cooperative LiDAR model with available weights** that is compatible with Mixed Signals: heterogeneous sensors, top-frame labels, 3 classes. Record its licence and hash, and load it in the new environment before trusting any citation. The current card mentions a competition, but no baseline checkpoint was verified here.
2. **Exact preprocessing**: point range, voxel/pillar size, max points, intensity handling (vehicle intensity is all zero), and **placeholder removal**. Placeholders would otherwise become a dense fake cluster at each sensor origin.
3. **The chosen layer and representation**: tensor shape, stride, channel semantics, BEV grid anchoring in the `top` frame, compression.
4. **Alignment**: per-agent transform to the ego/top frame, timestamp association across asynchronous scans, and feature warping.
5. **Labels**: verified sync-index mapping, class conventions, box frame; empty versus missing files.
6. **Reproduction check**: one fixed clean frame reproduces a documented detection output before any reliability work begins.
7. **Pairing**: clean and attacked inputs pass through the *same* frozen encoder. Direct feature-message attacks need their own threat model.

## 4. What the retained data is good for

| Use | Suitability |
|---|---|
| Strict-reader, frame and time regression tests | Good. Small fixtures can be cut from mini_7. |
| Geometry/ray feasibility pilots (origins, placeholders, beam index) | Good for **development only**. All five segments are exposed. |
| Feature-extraction development | Possible once a model is chosen; labels need extracting and their mapping verifying. |
| Negative controls (benign noise, downsampling, segment shift) | Useful. EX-05 already shows strong shift between neighbouring clips. |
| Final validation | **Not suitable as untouched test data.** mini_7 and C0–C3 outcomes were exposed in R03/R05. They span one ~3.5-minute stretch (C0–C3) plus mini_7; session independence is unverified. A new exposure-aware split must use other train segments. Val/test segments have no public labels. mini_14 was never opened by this repo (R05 manifest `H_opened=false`; no local copy), but its exposure elsewhere is unknown. |

## 5. Can the verified inputs support ray reasoning?

| Requirement | Evidence state |
|---|---|
| 3D sensor origin | RSU: published constants, corroborated by placeholders [L]. Vehicles: native (0, 0) XY assumed; z = 1.63/1.90 suggested by placeholders [hypothesis]. No metrology. |
| Beam direction / emitted beams | The organized grid suggests (row, column) = beam slot [hypothesis]. Elevation/azimuth tables are not provided. A no-return slot's direction cannot be recovered from its XYZ (it sits at the origin), only from its index and an intrinsic model [U]. |
| Return semantics | Single return per slot; meaning of placeholders, max range, multi-return and filtering are [U]. |
| Timing / motion distortion | No per-point time or deskew status [U]. Vehicle motion during a ~0.1 s scan smears rays. |
| Occlusion and independent coverage | Other agents' clouds exist and can be aligned approximately: R02 measured 44–77 ms skew and voxel Jaccard 0.05–0.14 on 9 top–vehicle pairs [R]. Overlap is not visibility. |
| Box solidity | Not assumed. Labels are boxes; a ray through a box may cross empty space within it. |

**Conclusion.** XYZ endpoints with a justified origin give approximate *observed* rays. The placeholder grid *might* also give no-return beams, which is exactly what the colleague's traversal idea needs. Both claims are unvalidated.

Keep three information settings separate:
- **(a) Received features alone, plus pose and time.** No rays are available.
- **(b) Features plus receiver-owned raw scans.** These provide independent rays, but only where the receiver actually sees. Lack of coverage is "unknown", never "false".
- **(c) Features plus sender-supplied rays or occupancy.** This is not independent: the sender can forge it consistently.
