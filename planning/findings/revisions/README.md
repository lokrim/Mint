# Revisions

| Revision | Date | Location | Status |
|---|---|---|---|
| r1 | 2026-10-22 (files dated 16:13–16:53 IST) | [r1_2026-10-22/](r1_2026-10-22/README.md) | **Superseded.** Copied byte-for-byte (SHA-256 verified) before r2 overwrote the top-level files. |
| r2 | 2026-10-22 | [../README.md](../README.md) | **Current.** |

Notes on r1:
- **Links.** r1's relative links were written for `planning/findings/`, not for this subfolder, so most of them do not resolve from here. r1's `evidence/` files were not moved and live in [../evidence/](../evidence/).
- **Missing files.** r1's README linked `audit_scope.json`, `evidence_manifest.json` and `evidence/README.md`, which did not exist when r1 was written. r2 creates them.

What changed in r2:
- **Placeholders.** New finding: organized clouds contain placeholder points, and these dominated the attack targets (DA-02–DA-05).
- **Alarm capability.** Attack results are separated into could-not-alarm and failed-to-alarm (EX-06/07).
- **Saturation.** Calibration saturation across segments (EX-05). All 240 thresholds are re-derived from saved scores, and the c = 1 cases are explained.
- **Re-hashing.** Full output re-hash: 15,561/15,565 (RP-01).
- **Sessions.** Session span: 208.6 s (DA-13).
- **Labels.** Label index-range risk and current HF card terms (DA-07/08).
- **Environment.** NumPy version drift during R05 (RP-03).
- **Leakage guard.** Partial leakage guard in the R-stage tests (SC-05).
- **Results table.** A compact `results_summary.csv` replaces r1's 570 KB dump.

r1 finding IDs `F001–F050` are cross-referenced in the r2 ledger's `r1_crossref` column where they match.
