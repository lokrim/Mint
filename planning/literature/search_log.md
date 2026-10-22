# Literature search log

Review date: **2026-10-22**. Reviewer: Claude (Opus 5.5) acting as research collaborator.

**Tools.** Web search (standard and extended modes); direct PDF download from arXiv, USENIX, CVF, PMLR and GitHub raw; `pdftotext` (poppler) for full text; GitHub REST API and raw files for code; Hugging Face API for dataset metadata.

**Copies.** Full-text PDFs are kept only in the session scratchpad (not committed: copyright). Their identifiers are in [references.bib](references.bib).

## Access-status vocabulary (used in the bib `note` field and the [matrix](comparison_matrix.csv))

| Status | Meaning |
|---|---|
| `FULL-CLOSE` | Full text obtained. Method, threat model, evaluation and limitations sections read closely, with section/page locators recorded in a reading note. |
| `FULL-SKIM` | Full text obtained. Abstract, method summary and the key equations or tables read. No detailed reading note. |
| `ABSTRACT` | Only the abstract or landing page read. |
| `SNIPPET` | Known only from search-engine summaries. **Never cited as evidence of content.** |
| `PRIOR-KNOWLEDGE` | Classical or foundational reference known to the reviewer. Not re-read this session. Bibliographic details must be re-verified before citing in the paper. |
| `CODE` | Repository or config files read (commit or branch and date recorded). |

## Inclusion and exclusion rules

**Include (deep read)** if the work does any of:
- estimates trust, reliability or anomaly for *received* information in cooperative perception (CP);
- attacks CP intermediate features or raw clouds with insider capability;
- uses LiDAR ray, occlusion or free-space reasoning to verify objects;
- defines a dataset or model that our feature pipeline would use.

**Include (screen)** if the work does any of:
- uncertainty, calibration or selective prediction for (collaborative) detection;
- robustness of CP to benign faults (pose, latency, heterogeneity);
- statistical foundations we would borrow.

**Exclude:**
- camera-only CP without a LiDAR path;
- V2X networking security unrelated to perception content (PKI, misbehaviour detection on CAM/BSM kinematics), except as context;
- surveys (used only to discover);
- works we could not access beyond a snippet (logged, not cited for content).

## Queries (all 2026-10-22)

| # | Query (verbatim) | Mode | Kept leads |
|---|---|---|---|
| Q1 | `malicious agent detection collaborative perception intermediate feature spatial-temporal region-level` | extended | GCP (arXiv 2501.02450), CP-Guard+ (2502.07807) |
| Q2 | `Shadow-Catcher ghost objects LiDAR shadow region detection 3D` | standard | Shadow-Catcher (2008.12008), object-hiding follow-up (2204.13973) |
| Q3 | `MATE multi-agent trust estimation security-aware sensor fusion Hallyburton Pajic` | standard | MATE (2503.04954, CCS 2025) |
| Q4 | `Mixed Signals V2X heterogeneous LiDAR benchmark baseline models checkpoint devkit` | standard | arXiv v3, CVF paper and supplement, devkit and OpenCOOD fork |
| Q5 | `"Latent Guardian" Cerberus collaborative perception feature consistency ICML 2026` | standard | ICML poster; PMLR v306 page; CP-uniGuard (2506.22890, a different paper) |
| Q6 | `collaborative perception defense region-level reliability uncertainty adversarial feature 2025 2026 arXiv LiDAR` | extended | TrustFlip (2605.22122 v2), GLST (2607.23059), PRBI (2603.08498), PoseGuard/PosePert (2605.01301 v2) |
| Q7 | `V2V4Real OpenCOOD pretrained checkpoint attentive fusion PointPillar download model zoo` | standard | V2V4Real arXiv 2303.07601; checkpoint table found later in the repo README |
| Q8 | `HEAL heterogeneous collaborative perception ICLR 2024 arXiv checkpoints OPV2V-H DAIR-V2X` | standard | HEAL (2401.13964); HF checkpoints (from README) |
| Q9 | `"From Threat to Trust" exploiting attention mechanisms attacks defenses cooperative perception USENIX Security 2025 LUCIA` | standard | SOMBRA/LUCIA (USENIX Sec 2025), Zenodo artifact |
| Q10 | `collaborative perception pixel-wise trust map spatially varying reliability fusion weights malicious feature region masking` | extended | CoDS (2608.14085; **SNIPPET only**), confirms TrustReflect and GLST |
| Q11 | `uncertainty-aware collaborative perception calibration conformal object detection V2X uncertainty quantification 2024 2025` | standard | MOT-CUP (2303.14346), TUQCP (2502.02537): both **SNIPPET/ABSTRACT** |
| Q12 | `V2X-Real dataset license download pretrained models GitHub UCLA Mobility Lab` | standard | V2X-Real (2403.16034); repo README read via API |
| Q13 | `DAIR-V2X dataset download access application region restriction CoAlign HEAL checkpoint DAIR-V2X` | standard | DAIR-V2X repo README (Google Drive mirror listed) |
| Q14 | `Ouster OS1 point cloud no return range zero organized point cloud beam_altitude_angles beam_azimuth_angles metadata json` | standard | Ouster SDK docs (XYZ from range + beam LUT); 0.3 m minimum range (datasheet via snippet) |

## Seed references (from the user) and their verification

| Seed | Access | Notes |
|---|---|---|
| Sun et al. 2020, CARLO/SVF, USENIX Sec 2020 (sec20-sun.pdf) | FULL-CLOSE | PDF loaded from the given USENIX URL |
| Zhang et al. 2024, data fabrication / CAD, USENIX Sec 2024 | FULL-CLOSE | PDF loaded from the given URL. **Correction to findings 07:** the occupancy-map details are now verified from the paper (§5.3–5.4), not just a search summary. |
| Mixed Signals, ICCV 2025 | FULL-CLOSE (arXiv v3, 28 Aug 2025, including appendix) | CVF PDF URL exists. We read arXiv v3, which includes the appendix. CVF supplement downloaded and skimmed. |
| Mixed Signals implementation and devkit | CODE | `acfr/Mixed-Signals-Dataset` branch `release-msig` (pushed 2026-08-26). `quan-dao/mixed-signals-devkit` main (pushed 2025-07-04). **The README says checkpoints are at `???`, i.e. not released.** |
| OPV2V, arXiv 2109.07644 | FULL-SKIM | Dataset statistics and the attentive fusion section read |
| DAIR-V2X repository | CODE (README) + FULL-SKIM (CVPR 2022 paper) | Apache-2.0 code. Data via the official site and a Google Drive mirror listed in the README. |

## Backward and forward citation trails

- **CAD → backward:**
  - CARLO [69] (followed, read);
  - LIFE [55] (not followed: camera–LiDAR);
  - MDS [23] (not followed: box sharing, majority vote; known via CAD §6.4.4 only);
  - Tu et al. [72] (followed, FULL-SKIM).
- **CAD → forward (same group):** PosePert/PoseGuard (2605.01301), followed. TrustFlip (2605.22122, Q. Zhang co-author), followed.
- **PoseGuard → backward:** LUCIA [55] (followed, FULL-CLOSE on §4.2 and §5); MADE [69]; CP-Guard+ [25]; ROBOSAC [32]; MATE [24]. All followed.
- **LUCIA → backward:** Attention-Fool (Lovisotto et al.), noted but not read. ROBOSAC, CP-Guard and CAD were followed.
- **GCP → backward:** ROBOSAC [11] and MADE [12] (followed); Tu [71]; CAD [9]; PB attack (via GLST).
- **GLST → backward:** Pretend Benign (PB) attack, known only through GLST; the PB primary paper was **not located this session** (open item L-01).
- **MATE → backward:** TruPercept (Hurl et al. 2019; followed, ABSTRACT); Bayesian trust (CDC 2024; not read).
- **Mixed Signals → backward:**
  - Laly fusion (Dao et al., T-ITS 2024; not read: open item L-02, asynchronous late+early hybrid);
  - CoAlign (followed, ABSTRACT);
  - V2V4Real (followed, FULL-SKIM);
  - V2X-ViT (ABSTRACT).
- **Shadow-Catcher → forward:** object-hiding 3D shadow detection (2204.13973, ABSTRACT + snippet).

## Searches that found nothing decisive (recorded so they are not mistaken for absence of prior art)

- **No paper was found** that outputs a *calibrated, spatially resolved, per-sender-per-region probability of task harm* for intermediate features, with an explicit unknown state and an exact counterfactual label. We ran 3 searches (Q6, Q10, Q11). This is weak evidence of a gap, not proof.
- **No CP-security evaluation on Mixed Signals** was found. We searched only within Q4 and Q6 results. **[To re-check before any novelty claim.]**

## Open literature items

| ID | Item | Why it matters | Next action |
|---|---|---|---|
| L-01 | Pretend Benign (PB) attack primary paper | Blind-area attack against confidence-driven sharing | Search GLST's references by title |
| L-02 | Laly fusion (Dao et al. 2024, T-ITS) | Mixed Signals' recommended practical fusion; asynchronous | Read the method if late-hybrid baselines are added |
| L-03 | MDS (CAD ref [23]) | Box-sharing defense with a local occupancy check | Optional |
| L-04 | Attention-Fool (Lovisotto et al., CVPR 2022) | Attention-logit attacks, the basis for SOMBRA | Read before designing the adaptive attack A-F7 |
| L-05 | CoDS (2608.14085) | Pixel-wise reliability map from feature variance (benign) | Get the full text; check whether it overlaps our estimand |
| L-06 | TUQCP (2502.02537), MOT-CUP (2303.14346) | Conformal uncertainty for collaborative detection | Full read before writing the calibration section |
| L-07 | Calibration of 3D detectors (e.g. Küppers et al. 2020) and conformal object detection | Calibration metrics for box-level outputs | Verify bibliographic details |
| L-08 | Forward citations of CARLO and CAD from 2025–2026 that use range images | Efficiency novelty | Targeted search |
| L-09 | V2X-Real license and checkpoint availability (website not fetched) | Alternative real dataset with 4 agents | Fetch the website |
| L-10 | OPV2V dataset sizes per split | Download budget | Fetch the UCLA Box listing |
