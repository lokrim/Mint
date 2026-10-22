# Primary source verification — 2026-10-08

Documentation, repository JSON metadata and small reader/calibration text files were inspected; no dataset archive was downloaded and no detector framework was installed or imported. Commit API checks distinguish commit IDs from their tree IDs (devkit commit date 2025-07-03; ACFR 2025-07-30). Exact retrieved-text hashes and candidate archive metadata are in [the verification ledger](audit/2026-10-08-source-verification.json). Earlier 2026-10-05 evidence is preserved in the dated snapshot.

| ID | Primary source and pinned revision | Verified scope |
| --- | --- | --- |
| HF | [Dataset card](https://huggingface.co/datasets/sberrio/Mixed-Signals-V2X/blob/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91/README.md), revision `1a61aea747aa6bc45da2c2f085a1f1d3abc41f91` | Native train/val layout, competition TXT labels, archive packaging and license; not raw headers |
| HF-tree | [Pinned train metadata](https://huggingface.co/api/datasets/sberrio/Mixed-Signals-V2X/tree/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91/train) | 29 entries; exact sizes and LFS SHA-256 for candidates; LFS hash is not a locally verified archive hash |
| SITE | [Project overview](https://mixedsignalsdataset.cs.cornell.edu/) and [download page](https://mixedsignalsdataset.cs.cornell.edu/download/) | Official links to IEEE Dataport, devkit and ACFR; three vehicles plus dual-LiDAR RSU. Direct retrieval returned 502/connection closure; indexed official pages were readable, crawled about three months earlier. No site commit/revision is exposed; verification has this freshness limitation. |
| DK-reader | [mixed_signals_utils.py](https://github.com/quan-dao/mixed-signals-devkit/blob/4f1f259e0d0fdc9ccfaf9f22b9627c02e263fe3d/mixedsignals/utils/mixed_signals_utils.py), commit `4f1f259e0d0fdc9ccfaf9f22b9627c02e263fe3d` | `read_pointcloud`, `SequenceOdomAgent`, `_legacy_check_stamp`, `SequencePointClouds`; exact consumed columns and time parsing |
| DK-frame | [mixed_signals.py](https://github.com/quan-dao/mixed-signals-devkit/blob/4f1f259e0d0fdc9ccfaf9f22b9627c02e263fe3d/mixedsignals/mixed_signals.py) and [geometry.py](https://github.com/quan-dao/mixed-signals-devkit/blob/4f1f259e0d0fdc9ccfaf9f22b9627c02e263fe3d/mixedsignals/utils/geometry.py), same commit | RSU translations, vehicle paired z shifts, intensity preprocessing, quaternion and transform composition |
| ACFR | [README](https://github.com/acfr/Mixed-Signals-Dataset/blob/8b670c80e248a25924fb1e72dc649992292064db/README.md), commit `8b670c80e248a25924fb1e72dc649992292064db` (`release-msig`) | Filename convention; examples show different timestamps at the same synchronization index |
| ACFR-reader | [msig_base_dataset.py](https://github.com/acfr/Mixed-Signals-Dataset/blob/8b670c80e248a25924fb1e72dc649992292064db/opencood/data_utils/datasets/msig_base_dataset.py) | Uses `top_se3_map @ map_se3_agent`, top receiver, modeled 70 m communication filter; this is not arrival telemetry |
| ACFR-eval | [msig_dataset_preprocessing.py](https://github.com/acfr/Mixed-Signals-Dataset/blob/8b670c80e248a25924fb1e72dc649992292064db/opencood/tools/msig_dataset_preprocessing.py) | `gt_visibility` is constructed from GT-box point membership, not independent visibility measurement; old JSON/PKL annotation path differs from HF TXT release |

## Consequences of reading code, not just schema names

DK-reader consumes `field.header.stamp`, `field.pose.pose.position.{x,y,z}` and `field.pose.pose.orientation.{w,x,y,z}` from vehicle CSVs. It does not read velocity/twist. The nav_msgs/Odometry schema name alone does not establish populated or measured velocity, covariance, frame IDs or arrival time. R01 must print actual CSV columns and characterize values before use.

DK-frame treats raw `top`/`dome` XYZ as map-frame clouds and maps them back to agent coordinates. `map_se3_top` has identity rotation and translation (-41.551, -51.878, -1.077) m; dome uses (-41.507, -51.864, -1.340) m. Vehicles have cloud z shifted by -3.25 m and pose right-composed with translation +3.25 m. These cancel when composed consistently, and are preprocessing conventions, not independently verified physical mounting extrinsics. Local HF archive compatibility remains unverified. Do not apply the published physical mounting angle again without evidence it is absent from released XYZ.

The reader divides intensity by 3500 and clips to [0,1]. That is model preprocessing, not a radiometric calibration or proof of cross-device comparability. Preserve raw intensity; no initial intensity factor.

The odometry lookup selects the nearest sample on either side of the query; it can select a future pose. The cloud reader sorts timestamps and indexes lists, while names contain synchronization indices. Reproduce these behaviors only as offline reference checks; the operational adapter must join explicit IDs and select past poses. Preserve integer nanoseconds and raw strings. The legacy filename helper left-pads subsecond strings shorter than nine digits (a nanosecond-field convention, not ordinary decimal-fraction padding). R01 must quantify whether this occurs; unresolved ambiguity blocks time-dependent factors.

The old devkit constructor requires `V2X_dataset-v0.4-labels.json`. Do not instantiate it in operational replay, and do not manufacture that file from the HF labels. The small new adapter must read clouds/poses without any label dependency. Competition labels and original paper annotations are distinct releases.

## Published archive metadata (unchanged since prior planning check)

| Role | Path | Bytes | Published LFS SHA-256 |
| --- | --- | ---: | --- |
| Development | `train/mini_7.tar` | 7894272000 | `46e9dbe9f6e952be9186a6271abbcaaf11c965a5589d785fc278afd3eb235663` |
| C0 | `train/mini_10.tar` | 7853803520 | `ba831ae3e82df52953f70929505faf3e8783b7dc588da7e9ccc5912feeb56a37` |
| C1 | `train/mini_11.tar` | 7763056640 | `c0ce489d33f7ee951edba2e811282b9c0069a054aa8c27e93a112d1ac6024ddf` |
| C2 | `train/mini_12.tar` | 7837788160 | `103fcd519b7284ee7690bddd86b68ce34d559f39d3a6ff8dc0a50b60e270eec0` |
| C3 | `train/mini_13.tar` | 7802398720 | `2d193aaed3b60cfeddd6197ac84b4034418e2e7013065e16320f5e04db3bd83a` |
| H | `train/mini_14.tar` | 7768442880 | `ffdb2c4d04a5debd628c511184262ca970879740743b5bfda88b21473e8471c8` |

HF card: CC BY-NC-SA 4.0; carry attribution and source citation in manifests. No content checks on comparison/final archives were performed. No arrival logs, packet loss measurements, visibility truth or measured independent velocity have been established from these sources. “Unavailable” in this plan means unavailable to the verified input contract, not a claim about all unreleased data.
