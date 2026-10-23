# Compute, memory and communication budget

Checkpoint 1, 2026-10-22.

**Nothing below is measured on target hardware.** Rows marked **[E]** are arithmetic estimates. **[L]** rows are measured locally, in pilots only. **[A]** marks a budget assumption awaiting decisions Q1/Q2.

## 1. Where MINT runs

MINT runs where fusion runs: on the **receiver**.
- Mixed Signals: an RSU edge computer.
- OPV2V/V2V4Real: the ego vehicle's central compute.

Senders' compute is unchanged in settings A/B. A sensor microcontroller has no fusion features, so **no on-sensor claim will be made** ([contract](information_and_threat_model.md) §9).

## 2. Provisional hardware profiles [A]

| Profile | Example class | Assumed resources | Budget for the *incremental* MINT step |
|---|---|---|---|
| P-RSU-hi | Jetson AGX Orin–class or x86 + mid GPU at the roadside | GPU with ≥ 8 GB, ARM/x86 CPU ≥ 8 cores | p95 ≤ 10% of end-to-end receiver perception latency; state ≤ 1 MB; model ≤ 1 MB |
| P-RSU-lo | Embedded CPU-only edge box | 4–8 ARM cores, no GPU | Ray evidence + combiner ≤ 5 ms p95 on CPU; counterfactual pass budgeted with fusion |
| P-ECU | Automotive SoC running perception | Shared GPU/NPU | Same as P-RSU-hi; **plus** a fixed share of a 100 ms cycle [V CAD §3.3, LUCIA §2] |
| P-SENSOR | Sensor MCU / sensor-adjacent embedded | < 1 W, < 1 MB SRAM | Out of scope. At most per-beam range statistics (no features). |

**The one hardware decision needed (Q2):** is the target an RSU-class edge GPU, an RSU-class CPU-only box, or a vehicle SoC? If unknown, we benchmark on proxies and withhold deployment claims.

## 3. Cost model per frame [E]

Mixed Signals AttFuse config: 512² pillars at 0.2 m, 5 receiver-side agent maps (TOP, DOME + 3 senders), scales 256²×64, 128²×128, 64²×256 [V yaml].

| Stage | Who | Estimate | Basis |
|---|---|---|---|
| PillarVFE + scatter | each agent | small (≤ 1 GMAC) | 64-filter linear over ≤ 70k pillars × 32 points |
| Backbone blocks (per agent) | sender encodes its own; receiver encodes TOP/DOME | ≈ 46 GMAC per agent | 3×3 convs: [3, 5, 8] layers at 256²/128²/64² with 64/128/256 ch (plus the strided first conv) |
| Fusion attention (3 scales) | receiver | ≈ 0.18 GMAC (N = 5) | N²·C per pixel |
| Deblocks + heads | receiver | ≈ 5 GMAC | ConvT 64→128 (k1), 128→128 (k2 s2), 256→128 (k4 s4); 1×1 heads 384→6, 384→42 at 256² |
| **MINT counterfactual pass, per sender** | receiver | ≈ 5 GMAC dense; less if restricted to tiles with sender attention mass | Reuses logits; reruns deblock+head |
| NMS + effect matching | receiver | ≤ 1 ms CPU [E] | Tens to hundreds of boxes |
| Ray evidence (M3/M4) | receiver | ~10⁵–10⁶ FLOPs; ≪ 1 ms CPU in compiled code [E] | Angular footprint × slab test |
| Combiner (M4 / M5-LR) | receiver | < 10⁴ FLOPs | Lookup + log-gamma / 25-feature dot |
| Temporal state update | receiver | O(#tiles × senders) | 768 triples |

Implications:
- **Receiver baseline per frame.** Own backbones (TOP+DOME) ≈ 92 GMAC, plus fusion+head ≈ 5 GMAC, so ≈ 97 GMAC.
- **Dense MINT with 3 senders.** Counterfactual passes add ≈ 15 GMAC. That is **≈ 3× the fusion+head cost**, or **≈ 15% of the receiver's end-to-end perception compute**.
- **The incremental cost is dominated by counterfactual deblock+head passes, not by the ray mathematics.**
- Hence H5 is stated relative to the end-to-end receiver pipeline (≤ 10% p95), and **tile-sparse evaluation is required** to meet it. Sparse means only tiles where sender i has attention mass above 5% **[A]** and a non-empty base output. The achieved sparsity must be measured.
- If sparsity is insufficient, H5 fails and is reported as such.

OPV2V AttFuse: if the config is 0.4 m over 281.6 × 80 m, the grid is 704 × 200 [E, verify]. That is about 25 GMAC per agent backbone.

## 4. Memory [E]

| Item | Size |
|---|---|
| Receiver range images (MS: TOP 64×1024 + DOME 128×1024, uint16) | 0.39 MB |
| Slot direction LUTs (fp16, 2 angles) | 0.79 MB (static) |
| Static ground map (256² fp16) | 0.13 MB |
| Beta-binomial tables (≈ 480 floats) | 2 KB |
| Calibrator (isotonic, ≤ 200 knots) | 2 KB |
| Temporal state (3 senders × 256 tiles × 12 B) | 9 KB |
| Extra activations for one counterfactual pass (fp32, 384×256² concat) | ≈ 100 MB dense; ≈ 10 MB if tile-sparse |

The model plus state is about 1 MB, within budget. **Peak working memory is dominated by the counterfactual activations.**

## 5. Communication

| Variant | Extra bytes per sender-frame |
|---|---|
| MINT-v0, settings A/B | **0** (uses the existing feature message and claimed pose and stamp) |
| Setting-C ablation (CAD-style occupancy) | ≈ 10 KB [V CAD §6.4.3] |
| Baseline message itself (MS AttFuse dense fp32, 3 scales) | ≈ 29 MB by our arithmetic. The paper reports 5.26 MB [V] (definition mismatch, V-05). |

The message size makes the *baseline* unrealistic for real V2X links (OpenCOOD's own note assumes 27 Mbps at 10 Hz, so < 2.7 Mb per frame). The study reports this honestly. MINT does not depend on it, and the quantization stress (B-3) is included.

## 6. Training and offline budget (separate from deployment)

| Item | Estimate | Condition |
|---|---|---|
| AttFuse training on MS | 1–3 GPU-days on one 24 GB GPU [E] | Only if option MS; needs a timing pilot |
| Label counterfactuals (MS, ~8.4k labelled frames, keyframes primary ~0.9k) | 2 passes per sender per frame of deblock+head; GPU minutes, CPU hours [E] | — |
| Beta-binomial fits / isotonic calibration | seconds to minutes on CPU | — |
| OP/VR inference-only on M1 | ≈ 0.3–1.5 s per frame on CPU [E] → thousands of frames in hours | Needs measurement (Stage 1) |
| Attack generation | A-F1/A-F3 PGD: 1–25 backward passes per frame (GPU strongly preferred) | Restrict to keyframe windows on CPU |

## 7. Benchmark plan (Stage 7)

- **Devices.** (1) Proxy: Apple M1 (CPU, and MPS if PyTorch supports all ops), 8 GB. (2) Target device, if provided (Q2). Report device, OS, library versions, precision, threads, power mode.
- **Protocol.**
  - 50 warm-up frames, then ≥ 500 measured frames from block E (clean) and from attacked episodes. The effect count varies, so the attacked load matters.
  - Batch 1. Time per stage with monotonic clocks.
  - p50/p95/max. Peak RSS including children (measured, not the finalize-only RSS of lesson RP-06). Bytes on the wire.
- **Separate:** disk I/O, decode/warp (no receiver warp under the OPV2V `proj_first` convention, D-13b; the per-recipient sender encoding cost is assumption A-P2 and is **not measured** by the current single-process benchmark), backbone, fusion+head, counterfactual pass, ray evidence, combiner, gating.
- **Worst case.** Many effects per frame: dense traffic plus A-F4 untargeted attacks.
- **Amortization.** Ray ranges and directions reuse the receiver's existing scan. Claim this as shared preprocessing only if the receiver's perception stack already computes it (measured).
- **Energy.** Only if measured with a power meter. Otherwise not reported.
- **Claims.** Proxy numbers are labelled "proxy". No P-SENSOR or target-device claim without target measurements.
