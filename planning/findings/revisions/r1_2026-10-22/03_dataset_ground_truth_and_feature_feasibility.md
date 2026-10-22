# Dataset, ground truth and feature feasibility

Local root is repository-relative `data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91/`. Archives are under `archives/train/`; extracts under `raw/PointClouds/<segment>` and `raw/Odometry/<segment>`. The revision string is a recorded HF pin, not a fresh remote-revision availability claim. Full path/size evidence is [local inventory](evidence/local_dataset_inventory.json); old published hashes are in the copied [segment roles](evidence/source/configs/segment_roles.json). **No archive hash or raw cloud body hash was recomputed.** [F033,F048]

| Segment / exposure | Archive bytes (fresh stat) | Extracted PCD files / bytes | Odometry files / bytes | Label members in historical inventory |
|---|---:|---:|---:|---:|
| mini_7 / development | 7,894,272,000 | 1,250 / 6,579,185,738 | 3 / 504,842 | 290 |
| mini_10 / C0 | 7,853,803,520 | 1,250 / 6,553,645,715 | 3 / 504,331 | 291 |
| mini_11 / C1 | 7,763,056,640 | 1,246 / 6,489,308,893 | 3 / 505,692 | 290 |
| mini_12 / C2 | 7,837,788,160 | 1,250 / 6,552,436,500 | 3 / 506,375 | 289 |
| mini_13 / C3 | 7,802,398,720 | 1,250 / 6,519,880,825 | 3 / 505,970 | 290 |

These are selected extracts, not full archive coverage. Label counts come from `safe_member_inventory.json` for mini_7 and `<segment>_safe_member_inventory.json` in local manifests for comparisons. Expected `raw/labels/<segment>` directories are absent for all five inspected segments. Label bodies and TAR contents were not opened. H/mini_14 remains excluded, including its content inventory. [F033–F034]

## Input contract and epistemic status

| Quantity | Status and meaning | What remains unknown |
|---|---|---|
| XYZ/intensity PCD | **Locally inspected headers**: first sorted file per stream/allowed segment, 25 headers, ASCII float32 x/y/z/intensity. Earlier R01 report inspected 250 bodies; that body result is historical here. | No new all-body finite/count validation; intensity physical calibration. |
| Pose/twist CSV | **Locally inspected bodies**: 15 files, each 300 rows/90 columns, six finite variable twist columns; fresh hashes in `odometry_recheck.json`. | Twist coordinate frame, independent measurement, filtering and localization latency. |
| Stream/principal | **Code-derived/documented**: 003,004,laser are vehicle principals; top+dome are one RSU. | Authentication and independence of error sources. |
| Cloud timestamp | **Locally inspected filenames/code**: integer seconds*1e9 + left-padded ns field; sync ID kept separately. | Scan start/end, clock accuracy and point offsets. |
| Pose clock/selection | **Code-derived**: latest source<=event and availability<=deadline, max age 150 ms. | Actual receiver availability and online versus offline localization. |
| Arrival/deadline | **Simulated**: ideal arrival=source, deadline=event time. | Recorded network latency, packet loss, bandwidth; none established. |
| Raw frame/extrinsics | **Documented plus local compatibility checks**, not metrology. Raw RSU map convention; vehicle raw convention and paired height adjustments. | True physical laser origin/extrinsic calibration and deskew accuracy. |
| Labels | **Documented and inventory-only locally**; TXT boxes, separate release from older JSON/PKL. | Annotation quality/completeness, exact alignment for retained revision; not body-validated. |
| Visibility/beam returns | **Unknown** as an independent input. | Emitted/no-return beams, return order, occlusion truth, ring firing semantics. |
| Features/model | **Not implemented** locally. | Compatible encoder/checkpoint, exact tensor semantics and fusion interface. |

Historical R01 timing reports 147/1,495 archive filenames with short subsecond fields, and 50.603–59.893 ms same-index cross-stream skew in its selected 50-index window. These numbers are **reported_not_reverified**, sourced to `artifacts/20261008T192922Z-R01/T_R01_timing.json` and copied field matrix, not extrapolated to all segments. Different streams’ same sync ID does not make them simultaneous. [F036]

`pose_matrix` consumes quaternion **wxyz**; older generic contracts use **xyzw**, requiring explicit conversion. `TOP_FROM_MAP=(+41.551,+51.878,+1.077)` m and `DOME_FROM_MAP=(+41.507,+51.864,+1.340)` m are translations mapping raw map points to those RSU frames. Their map-frame origins are the negatives, not the positive translation vectors. Dome origin in top is `(0.044,0.014,-0.263)` m. The vehicle preprocessing shifts cloud z by −3.25 m and right-composes pose +3.25 m; the consistent composition cancels. The new adapter therefore uses the raw-to-map pose without repeating a physical mounting correction. Round trips demonstrate algebra, not physical alignment or a laser firing origin. [F036]

## Labels and release compatibility

The preserved pin/provenance says HF TXT rows use `cls cx cy cz dx dy dz yaw`, top-frame metres/radians and Vehicle/Bike/Pedestrian classes. Current [primary HF card](https://huggingface.co/datasets/sberrio/Mixed-Signals-V2X) was checked on 22 October 2026 and documents this layout and CC BY-NC-SA 4.0; the pinned card URL could not be retrieved through the browser tool. Current documentation is therefore corroboration, not proof that old archive bytes match it. The current card also describes a label crop and point-support selection; evaluate their effect on a reliability target when the precise revision is checked. [F048]

The older devkit constructor/ACFR preprocessing uses JSON/PKL annotations and generated visibility. Those are **historic primary-source observations** preserved in [sources](evidence/source/planning/sources.md), not newly validated working code/checkpoints. Do not silently copy annotations from another release or treat generated `gt_visibility` (points in GT boxes) as independent operational visibility. Missing label file differs from a present empty annotation. The next study must verify class IDs, dimensions, yaw axis, frame transform, timestamp association, completeness and any point-count filter against the exact release before computing task metrics. [F034,F043,F048]

## Genuine intermediate features require a perception pipeline

A PCD-to-array conversion is insufficient. The next planning gate needs a compatible model and usable weights, their license/source/hash, detector training domain and class mapping, exact voxel/pillar preprocessing (range, voxel size, point caps, intensity scaling), selected encoder layer, tensor shape/stride/channel meanings, coordinate anchoring, timestamp and feature alignment, compression, fusion interface and detection postprocessing. A fixed known frame should reproduce a documented detector output before adding reliability. The checkpoint must be loaded and its provenance tested in the new environment; old citations cannot certify current availability. [F037,F045]

Choose whether the reliability unit is a received spatial feature region, individual representation element, or object hypothesis supported by features. Define how labels or downstream GT error supervise/evaluate that unit without implying every latent channel is directly interpretable. Preserve clean/attacked pairing through the **same encoder**. Feature-message attacks need their own threat model; current point attacks only become feature experiments after this path exists. Keep task-supervised training allowed with grouped splits; deployment inference cannot secretly read GT, schedules or the clean alternative. [F043–F045]

Retained data can support exposed geometry development, strict-reader regression, point-to-feature extraction development and negative controls. Eventual task validation is conditional on labels/model compatibility and a new exposure-aware split. Mini_7 and C0–C3 cannot become untouched test data by renaming the project. Their independent-session status is unverified; repeated overlays and fold fits do not multiply scene independence. [F039]

## Ray reasoning: conditional feasibility, not demonstrated support

Given a defensible 3D origin o and measured endpoint p, the segment `o + λ(p-o), 0<=λ<1` is an **approximate observed ray**. Whether it contradicts proposed occupied space requires origin/pose uncertainty, time alignment, return semantics and a justified visibility/occupancy model. The retained XYZ endpoints do not reveal every emitted beam or every no-return event. Organized WIDTH/HEIGHT and a PCD VIEWPOINT field do not by themselves prove physical ring directions or firing times. [F038,F044]

A return behind a proposal may contradict an actually occupied surface region under stated assumptions. It does not establish that an entire enclosing box is solid; rays may pass through empty portions of a box or unoccupied structure. Missing returns alone are not empty-space measurements. An obscured object or honest unique viewpoint must remain unsupported/unknown rather than automatically false. Moving objects and asynchronous scans can create apparent conflicts. No per-point timing/deskew contract or independent observer coverage was established here.

A feature-only receiver cannot assume access to the sender’s raw rays. Separate three candidate information settings: (a) received features alone plus pose/time metadata; (b) features plus receiver-owned raw scans; (c) features plus communicated occupancy/ray metadata. In (c), metadata from the attacked sender may be jointly fabricated; a claimed support count is not independent evidence. In (b), no receiver coverage is not proof against an honest unique view. Establish each input’s availability and adversarial control before selecting the colleague’s candidate. [F038,F044–F045]
