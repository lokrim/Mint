# Evidence folder guide

## Revision 2 (current): `r2/`

| File | What it is | How produced |
|---|---|---|
| [r2/audit_r2.py](r2/audit_r2.py) | Read-only audit of saved R05 evidence: re-derives thresholds, joins attack metrics with alarm capability, control rates, flow, realized changes, outcomes, sessions, targets, SHA-256 checks | `python3 -I planning/findings/evidence/r2/audit_r2.py <repo> planning/findings/evidence/r2` (standard library; ~10 s plus hashing 2.5 GB) |
| [r2/audit_r2_report.json](r2/audit_r2_report.json) | All computed summaries | output of the above |
| [r2/calibration_cells_r2.csv](r2/calibration_cells_r2.csv) | 240 calibration cells: saved vs recomputed threshold, count of scores equal to 1, meaning, whether an alarm was possible | output |
| [r2/sender003_attack_grid_r2.csv](r2/sender003_attack_grid_r2.csv) | 360 attack × arm × version cells with per-segment alarms/attempts/eligible/threshold/capability | output |
| [r2/control_rates_r2.csv](r2/control_rates_r2.csv) | Clean, identity and benign alarm rates for every sensor/arm/version, per segment | output |
| [r2/placeholder_probe.py](r2/placeholder_probe.py) and [r2/placeholder_probe.json](r2/placeholder_probe.json) | Placeholder (repeated-coordinate) counts in 25 sampled local clouds, with per-file SHA-256 | `.venv/bin/python -I placeholder_probe.py <repo>/data/mixed_signals/<rev>/raw out.json` (needs NumPy; reads ~130 MB) |
| [r2/build_tables_r2.py](r2/build_tables_r2.py) | Builds `evidence_ledger.csv`, `results_summary.csv` and `asset_inventory.csv` from the above | `python3 -I … <repo>` |
| [r2/build_manifest_r2.py](r2/build_manifest_r2.py) | Builds `evidence_manifest.json` | `python3 -I … <repo>` |

Scripts only read the old repository and write only inside `planning/findings/`. They never touch `mini_14`.

## Revision 1 (superseded, kept unchanged)

Everything else here (`audit_extract.py`, `build_handoff.py`, `trace_records.py`, `*_index.json`, `r05_*.csv`, `saved_record_checks.json`, `source_excerpts.md`, `source/`) was written by revision 1. These files are retained as-is and r2 has not independently re-validated them. Exceptions:
- `source/` holds small byte copies of old files (provenance in `copied_source_provenance.json`), which r2 still links.
- Some r1 tables agree with r2's recomputation, e.g. the 248-row flow and the 240 calibration statuses.

`initial_file_state.json` (4 MB) records r1's view of the tree. Do not treat r1 CSVs as current where they differ from `r2/`.
