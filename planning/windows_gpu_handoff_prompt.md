# Handoff prompt: MINT on Windows + RTX 4050 (branch `gpu`)

Paste everything below the line into the coding agent on the Windows laptop, after the repo is cloned there (Part A of the prerequisites must be done on the Mac first).

---

You are working on **MINT**, a pre-registered research pipeline (`https://github.com/lokrim/Mint.git`). It evaluates a defence for cooperative LiDAR perception on OPV2V, using OpenCOOD's PointPillar + AttFuse model. It was built and run on a MacBook M1, CPU only. Your job is to make it run on this Windows laptop (Ryzen 7 7735HS, 8 cores / 16 threads; NVIDIA RTX 4050 Laptop, 6 GB VRAM) and use the GPU to cut runtime, **without breaking the study's pre-registration**. Work on a new branch called `gpu`. Then give the user a complete, copy-pasteable PowerShell command sheet.

Read this whole prompt before doing anything.

## 0. Rules you must not break

These come from the study's protocol. Breaking them invalidates the research.

1. **Never download or open OPV2V test data** (the Box URL in `runners/stage1_reproduce.py` `TEST_URL`), and never run `runners/v3_1_stream.py --user_approved` or any GPU equivalent with `--user_approved`. Only the user starts the final test, after they explicitly approve it in chat. `--dry_run` (hash + budget check, no network) is allowed.
2. **Frozen files.** `runs/20261024-E5/preregistration_v3_1.json` → `frozen_sha256` lists 35 files (source files and the checkpoint `latest.pth`) with SHA-256 hashes. `v3_stream.verify_frozen` refuses to stream if any differs, and also requires `third_party/OpenCOOD` at commit `31ba16025da27ffe4e336f011290dfbc66f9a1f1` with a clean tracked tree.
   - Do **not** edit, reformat, or re-save any frozen file on `main`. Do not edit any of the `preregistration*.json` files, or `planning/decision_log.md`.
   - On the `gpu` branch you **may** change frozen files if the GPU port needs it. But then the v3.1 hashes no longer match, so the GPU path needs a **new** preregistration file (see §4). The CPU path must stay runnable from the unchanged frozen files.
3. **Line endings decide the hashes.** If git converts LF→CRLF on checkout, every frozen `.py` hash fails. `core.autocrlf` must be `false` before cloning (see Prerequisites B). Never let an editor or formatter touch frozen files.
4. **Don't change results silently.** Don't change seeds, thresholds, the PGD settings (10 steps, step ε/4, random start, sign-gradient), the bootstrap (seed 0, 2000 resamples), or any number in a preregistration. If GPU numerics differ from CPU, measure it and report it; don't tune it away.
5. Don't commit large data (`data/`, caches, `*.pkl.gz`, `*.pth`). `.gitignore` already covers them.
6. Commits go to `gpu` only. Never push to or merge into `main`. Push `gpu` only if the user asks.

## 1. Facts about the repo (verified on the Mac, 2026-10-24)

- Python 3.10.20, created with `uv` (uv 0.11.x). No `pyproject.toml`. The pinned environment is `env/requirements-stage1-spike.lock.txt` (`torch==2.2.2`, `torchvision==0.17.2`, `numpy==1.26.4`, `open3d==0.18.0`, `numba==0.59.1`, `scipy==1.11.4`, `Cython`, ...).
- `third_party/OpenCOOD` is **gitignored**: it is a separate clone of `https://github.com/DerrickXuNu/OpenCOOD.git` at `31ba16025da27ffe4e336f011290dfbc66f9a1f1`, tracked source unmodified. It is not pip-installed: runners put it on `sys.path`. The only build artefact is the Cython extension `opencood/utils/box_overlaps` (CPU), built from `opencood/utils/setup.py`.
- `src/mint/model/opencood_shims.py` installs fake `spconv` / `cumm` modules with a NumPy voxelizer, so OpenCOOD runs without CUDA/spconv. **Keep using the shim on GPU too.** Do not install real spconv: it would change voxelization and the frozen results.
- **Nothing uses CUDA today.** No `.to(device)`, no `.cuda()`, no `map_location`. Tensors are made on CPU in `src/mint/fusion/compose.py` (~16 places), `runners/v3_common.py` (~13), `src/mint/attacks/patches.py`, `pgd_v3.py`, `pgd_stealth.py`, `reliability/pipeline.py`, `reliability/bnorm.py`, `model/warp.py`, `runners/e0_stream.py`, `e4_stream.py`, `e5_stream.py`, `stage1_reproduce.py`. Many results go through `.numpy()`, which fails on CUDA tensors.
- Runners set `torch.set_num_threads(8)` and `torch.set_num_interop_threads(1)`. `DataLoader` uses `num_workers=0`.
- **Final-test entry point:** `runners/v3_1_stream.py`. It swaps in preregistration v3.1 and its own `run_scenario`, then calls the frozen `v3_stream.main`. Per frame, it runs: the v2 record (`e5_stream.frame_record_e5`), then the v3 side record (B-NORM magnitudes plus 6 PGD conditions: `pgd_untargeted@r0.25`, `pgd_remove@r0.25`, `pgd_untargeted_stealth@r0.5`, `pgd_remove_stealth@r0.25`, `pgd_untargeted_stealth@r1.0`, `pgd_remove_stealth@r1.0`). Then a separate **D-42 timing pass** (`e5_stream.time_frame_e5`, 3 reps per frame) measures per-frame latency.
- It streams 15 test scenarios (about 20.4 GB, budget 22e9 bytes), one scenario on disk at a time. Raw data is capped at 3e9 bytes, and it needs free disk ≥ member size + 5e9. Raw data is deleted after the caches are re-read. Interrupted downloads in the ledger → STOP (no automatic restart). Finished scenarios are skipped on resume.
- Mac runtime estimate (`runs/20261024-E5/v3_runtime_estimate.json`): v2 part about 8 h, v3 side record about 11.2 h, plus PGD cost per family. PGD (10 forward+backward passes through decode, × 6 conditions × every frame with n ≥ 2) is the most likely GPU win.
- Analysis: `runners/v3_analyze.py test --run_dir <run> --prereg runs/20261024-E5/preregistration_v3_1.json`. It asserts 15 scenarios and 2066 frames.
- Dev checks with no network: `runners/v3_dryrun.py`, `runners/v3_1_dryrun.py` (asserts its records equal the Mac's `runs/20261024-E5/dryrun_v3` except wall-clock fields), `runners/v3_resume_test.py prepare|drive|compare`, and the `pytest` suite in `tests/` (`test_v3.py`, `test_v3_1.py`, ...).

## 2. Prerequisites (user does these; check them and stop if any are missing)

**A. On the Mac, before cloning (the user does this, not you):**
`runs/20261024-E5/preregistration_v3_1.json` and `runners/v3_resume_test.py` were untracked on the Mac. They must be committed on `main` and pushed, or the Windows clone won't have them. The gitignored data must be copied over as one archive (`mint_windows_data.tar.gz`). It contains `data/opv2v/ckpt`, `data/opv2v/devslice`, `data/opv2v/resume_src`, and the ignored dry-run/resume caches under `runs/20261024-E5/`.

**B. On Windows (PowerShell):**
```powershell
git config --global core.autocrlf false
git config --global core.longpaths true
git clone https://github.com/lokrim/Mint.git mint
cd mint
git clone https://github.com/DerrickXuNu/OpenCOOD.git third_party/OpenCOOD
git -C third_party/OpenCOOD checkout 31ba16025da27ffe4e336f011290dfbc66f9a1f1
tar -xzf $HOME\Downloads\mint_windows_data.tar.gz
```
Also needed:
- NVIDIA driver ≥ 531 (`nvidia-smi` works).
- Visual Studio 2022 Build Tools with the "Desktop development with C++" workload (for the Cython build).
- `uv` installed (`winget install astral-sh.uv`).
- Windows long paths enabled (admin: `New-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force`).
- The repo folder excluded from Defender real-time scanning. This is optional, but makes things faster and avoids `rmtree` lock errors.

Changing system settings is the user's job. If something is missing, tell them the exact command and wait.

## 3. Phase 1: CPU parity on Windows, no code changes (do this first, on `main`)

Goal: show that the unchanged frozen pipeline runs on Windows CPU, and measure how far Windows CPU numerics are from the Mac's.

1. `git checkout -b gpu` right away, but **don't edit anything yet**. Phase 1 runs the frozen code exactly as cloned.
2. Environment:
   ```powershell
   uv python install 3.10.20
   uv venv --python 3.10.20 .venv
   uv pip install --python .venv\Scripts\python.exe -r env\requirements-stage1-spike.lock.txt
   ```
   If a pinned package has no Windows wheel for cp310, don't change versions silently. Record which one, then try the nearest version that does have one. Report every deviation in the Phase-1 report.
3. Build the Cython extension in place, without changing tracked OpenCOOD files (`git -C third_party/OpenCOOD status --porcelain --untracked-files=no` must stay empty):
   ```powershell
   cd third_party\OpenCOOD; ..\..\.venv\Scripts\python.exe opencood\utils\setup.py build_ext --inplace; cd ..\..
   ```
4. Set for every session: `$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"`. Many files use `open()` without `encoding=`, and Windows defaults to cp1252. This avoids touching frozen files.
5. Run, and save every log under `runs/<today>-WIN/`:
   - `.venv\Scripts\python.exe runners\v3_1_stream.py --run_dir runs/<today>-WIN-dry --dry_run`. It must print `frozen sha256 + OpenCOOD commit verified`. If any hash fails, find out why (CRLF? missing file? wrong `latest.pth`?) and fix the **checkout**, never the hash.
   - `.venv\Scripts\python.exe -m pytest tests -x -q`
   - `.venv\Scripts\python.exe runners\v3_1_dryrun.py --out runs/<today>-WIN/dryrun_v3_1_cpu`. If its equality asserts fail, that is **Mac-vs-Windows CPU numeric drift** (Apple Accelerate vs MKL/OpenBLAS). Don't change the code. Write a small separate comparison script (new file, e.g. `tools/compare_records.py`) and quantify the drift: max abs diff of features/scores, and whether candidate box sets, final box sets, B-RAY/R1 decisions and AP per condition are identical.
   - Time 3 frames end to end with `cProfile`, and report where the time goes: model forward, PGD, ray geometry (`mint.geometry.rays`), compose, timing pass. **This decides what the GPU can actually speed up.**
6. Write `runs/<today>-WIN/phase1_report.md` (environment, `uv pip freeze`, CPU/GPU info from `nvidia-smi` and `wmic cpu get name`, hash check, test results, drift numbers, profile). Commit it on `gpu`, then **stop and show the user the summary**. Phase 1 alone makes the Windows machine usable in a way that keeps the protocol intact (see the parallel-CPU option in §6).

## 4. Phase 2: GPU port on branch `gpu`

Only after Phase 1 passes.

**Design (follow it):**
- Add one new module, `src/mint/device.py`. `DEVICE = torch.device(os.environ.get("MINT_DEVICE", "cpu"))` plus small helpers (`to_dev(x)`, `to_np(t)` = `t.detach().cpu().numpy()`, `batch_to(batch, dev)`, which may wrap OpenCOOD's `train_utils.to_device`). **The default must be CPU.**
- Port only what the profile says is worth it. Usually that means:
  - model `.to(DEVICE)`;
  - the batch dicts moved to device;
  - tensors created with `device=` in `compose.py`, `pgd_v3.py`, `pgd_stealth.py`, `v3_common.py`, `bnorm.py`, `warp.py`, `pipeline.py`, `patches.py`, `e0/e4/e5_stream.py`;
  - every `.numpy()` on a tensor that might be on CUDA replaced with `to_np`.

  Leave NumPy geometry (rays, ground, effects, harm labels) on CPU.
- **With `MINT_DEVICE=cpu` the edited code must give bit-identical records to the frozen code on this machine.** Check this by running `v3_1_dryrun.py` on both and comparing every non-wall-clock field exactly. This is the gate for every edit.
- GPU determinism, set once at start-up when on CUDA:
  - `torch.backends.cuda.matmul.allow_tf32 = False`
  - `torch.backends.cudnn.allow_tf32 = False` (TF32 is on by default on this GPU and would lower precision)
  - `torch.backends.cudnn.deterministic = True`
  - `torch.backends.cudnn.benchmark = False`
  - `torch.use_deterministic_algorithms(True, warn_only=True)`
  - env `CUBLAS_WORKSPACE_CONFIG=:4096:8`

  Keep float32. No AMP/half precision.
- PyTorch with CUDA, same version: `uv pip install --python .venv\Scripts\python.exe torch==2.2.2+cu121 torchvision==0.17.2+cu121 --index-url https://download.pytorch.org/whl/cu121` (cu121 supports the RTX 4050 / sm_89). Record that this replaces the CPU wheel. CPU mode must still work with this wheel; check that in Phase 1 numbers too.
- The PGD seeds are NumPy-based (`sha256('V3PGD|family|r|scenario|frame')`). Keep random starts drawn in NumPy on CPU and then moved to device, so they are identical across devices.
- **The D-42 timing pass measures CPU latency in the pre-registration.** Add a flag `--timing_device {cpu,cuda}` to the new GPU runner, **default `cpu`** (a CPU copy of the model, 8 threads, unchanged `time_frame_e5`), so the latency claims stay comparable. Say in the report how long the CPU timing pass costs, so the user can decide.
- New runner `runners/v3_2_gpu_stream.py`, built like `v3_1_stream.py`: wrap the frozen `v3_stream.main` via `install()`, and change as little as possible. It reads a new **draft** preregistration `runs/20261024-E5/preregistration_v3_2_gpu_DRAFT.json` = v3.1 + `device`/`timing_device` fields + a `frozen_sha256` with the new hashes of every edited file + a `difference_from_v3_1` list. Mark it `"status": "DRAFT – needs the user's approval; NOT RUN"`. The runner must refuse `--user_approved` unless that status was changed by the user.
- Also draft (don't apply) a decision entry, **D-71**, in a new file `planning/decision_log_gpu_proposal.md`. It should state what changed, why, the measured CPU↔GPU differences, and the alternatives (pure CPU; parallel CPU on two machines).
- Fix Windows problems in **non-frozen** files only:
  - `runners/v3_resume_test.py`: `signal.SIGKILL` doesn't exist on Windows → use `p.kill()`; `os.path.relpath` gives backslashes → `.replace(os.sep, "/")` for archive member names.
  - `caffeinate` in the printed runner hint → document a PowerShell keep-awake instead.
  - Any `open(..., "w")` you write → `encoding="utf-8"`.

  If a frozen file has a Windows bug, do not fix it on the CPU path. Report it.

**Phase 2 validation (all must be in `runs/<today>-WIN/phase2_report.md`):**
1. `pytest tests -q` passes in both `MINT_DEVICE=cpu` and `MINT_DEVICE=cuda`. If a test asserts bitwise equality that CUDA can't meet, report it, don't weaken it.
2. CPU mode on `gpu` branch = frozen code on Windows CPU, bit-identical (non-wall-clock fields).
3. CUDA vs CPU on the dev slice (`v3_1_dryrun` n=1/2/5 equivalents, plus `v3_resume_test` drive/compare in CUDA mode). Per condition and method, report:
   - max |Δ| of scores/features;
   - % of frames with identical candidate and final box sets;
   - whether every `compose_checks` `same_candidates`/`same_final` still holds;
   - stealth-constraint assertions;
   - number of PGD sign flips;
   - ΔAP@0.7/0.5 under both AP definitions;
   - B-NORM flags.
4. Speed: seconds/frame CPU vs CUDA for n=1, 2, 5. Peak VRAM (`torch.cuda.max_memory_allocated`). Must stay under about 5 GB; if not, report it. Don't batch frames if that changes results. Then a projected full-test wall time for: (a) CPU only, (b) CUDA + CPU timing pass, (c) CUDA + CUDA timing.
5. `v3_2_gpu_stream.py --dry_run` verifies the draft hashes, and `v3_1_stream.py --dry_run` still verifies the v3.1 hashes. (Expect it to fail on the `gpu` branch if you edited frozen files. That is correct; it must still pass on `main`.)

Commit in small, clearly described steps on `gpu`. Don't amend or rebase anything that came from `main`.

## 5. Final deliverable to the user

Stop after Phase 2 and give the user:

1. A short summary: what changed, the CPU↔GPU equivalence table, the speedup, and a plain recommendation among the three options in §6.
2. **A complete PowerShell command sheet** in `planning/windows_runbook.md` (committed on `gpu`). Every command is copy-pasteable and in run order, with expected output and what to do if it fails. It must cover:
   - one-time setup: git config, clone, OpenCOOD checkout, data archive, uv/Python, both torch variants, Cython build, env vars, long paths, Defender exclusion, NVIDIA/power settings ("Best performance" power mode, plugged in, sleep off: `powercfg /change standby-timeout-ac 0`, `powercfg /change hibernate-timeout-ac 0`);
   - checks: `nvidia-smi`, `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"`, hash dry runs, pytest, dry runs;
   - **the final-test commands for each option, with `--user_approved` shown but clearly marked "run only after you approve the final test"**;
   - how to start it so it survives closing the terminal and screen-off (e.g. `Start-Process` with output redirected to a log, or a dedicated PowerShell window plus a keep-awake), how to watch progress (`Get-Content -Wait`), how to resume after a crash (the ledger rules: an interrupted download means STOP and ask);
   - the post-run commands: `v3_analyze.py test ... --prereg <the right file>`, post-run hash check, and how to copy the caches back to the Mac if analysis happens there.
3. Anything you could not do or verify, said plainly.

## 6. The options the user will choose between (put this in your summary)

- **(a) CPU only, frozen, on one machine.** No protocol change. Slowest.
- **(b) Parallel CPU on Mac + Windows.** Both run the unchanged frozen `v3_1_stream.py --scenarios <disjoint subset>` into separate run dirs; then merge the cache dirs and analyse once. No code change, but it needs a short decision entry. The scenario subsets are fixed in advance. Windows↔Mac CPU drift (Phase 1) must be negligible. D-42 timing then mixes two machines' hardware, so report timing per machine.
- **(c) GPU via the `gpu` branch + draft v3.2.** Fastest. Needs the user to approve D-71 and freeze the new preregistration before any test byte.

Recommend based on your measured numbers, not on this prompt.
