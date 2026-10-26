# CULVER run: how to monitor, resume and finish

Stream launched 2026-10-26 (detached) after code freeze `9b8a8c1` and the passing sanity check (`sanity_first_scenario.json`).

Monitor:
```bash
tail -f runs/20261026-CULVER/run.log
ls runs/20261026-CULVER/cache/*.pkl.gz | wc -l     # finished scenarios (of 4)
```

Resume after an interruption (finished scenarios are skipped; a complete extraction is reused). If the ledger
shows a download whose status is not "complete", the stream STOPs: ask the user first.
```bash
nohup caffeinate -ims .venv/bin/python runners/culver_stream.py --run_dir runs/20261026-CULVER --user_approved > runs/20261026-CULVER/run.log 2>&1 &
```

When run.log ends with "post-run frozen check: OK" and "all done" (4/4 caches), and not before (no AP on partial results):
```bash
.venv/bin/python runners/culver_analyze.py --run_dir runs/20261026-CULVER > runs/20261026-CULVER/analysis.log 2>&1
.venv/bin/python runners/culver_report.py --run_dir runs/20261026-CULVER
python3 paper/gen_numbers.py
```
Then: exposure ledger + outcome decision (D-73 proposed), paper subsection, overleaf zip (see the original task prompt).
