"""Pre-final-test resume test (no network): the FROZEN v3_stream.main(), unchanged, on local dev-slice data.

What is replaced at runtime (frozen files untouched):
  * sockets: any connect raises (proves no network),
  * tools.ranged_zip.central_directory / stream_extract: a fake "archive" whose members are local files
    (copying them = the "download"); the ledger counts their byte sizes,
  * e5_stream.TEST_SCENARIOS: the two local scenarios (the D-55 allowlist itself is not used here),
  * e5_stream.frame_record_e5 / time_frame_e5: same functions, plus one progress line per frame.
Scenarios: A = 2021_08_22_13_37_16 (the 24-frame block-T dev slice), B = 2099_12_31_00_00_08 (a copy of A's
first 8 frames under a fake name, so the "skip a finished scenario" path is exercised too).

  python runners/v3_resume_test.py prepare
  python runners/v3_resume_test.py drive --out runs/20261024-E5/resume_test     (reference run + killed/resumed run)
  python runners/v3_resume_test.py compare --out runs/20261024-E5/resume_test
DEVELOPMENT procedural test; numbers are not results.
"""
import argparse
import gzip
import json
import os
import pickle
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, ROOT)

A, B = "2021_08_22_13_37_16", "2099_12_31_00_00_08"
DEV = os.path.join(ROOT, "data/opv2v/devslice/validate", A)
SRC = os.environ.get("RESUME_SRC", os.path.join(ROOT, "data/opv2v/resume_src"))   # local fake archive content
STREAM_PARENT = os.path.join(ROOT, "data/opv2v/stream")
TIME_KEYS = {"frame_s", "v3_s", "attack_s"}


def prepare():
    shutil.rmtree(SRC, ignore_errors=True)
    shutil.copytree(DEV, os.path.join(SRC, "test", A))
    stamps = sorted({f[:-4] for cav in os.listdir(DEV) if os.path.isdir(os.path.join(DEV, cav))
                     for f in os.listdir(os.path.join(DEV, cav)) if f.endswith(".pcd")})[:8]
    dst = os.path.join(SRC, "test", B)
    os.makedirs(dst)
    for x in os.listdir(DEV):
        p = os.path.join(DEV, x)
        if os.path.isdir(p):
            os.makedirs(os.path.join(dst, x))
            for f in os.listdir(p):
                if f.rsplit(".", 1)[0] in stamps:
                    shutil.copy2(os.path.join(p, f), os.path.join(dst, x, f))
        else:
            shutil.copy2(p, os.path.join(dst, x))
    print("prepared", SRC, "B frames:", stamps)


def _entries():
    out, lho = [], 0
    for scen in (A, B):
        base = os.path.join(SRC, "test", scen)
        for dp, _, fs in sorted(os.walk(base)):
            for f in sorted(fs):
                p = os.path.join(dp, f)
                sz = os.path.getsize(p)
                out.append({"name": os.path.relpath(p, SRC), "csize": sz, "usize": sz, "lho": lho, "method": 0})
                lho += sz + 100
    return out


def run(argv):
    def no_net(*a, **k):
        raise RuntimeError("network access attempted in the no-network resume test")
    socket.socket.connect = no_net
    socket.create_connection = no_net
    import e5_stream as S
    import tools.ranged_zip as RZ
    S.TEST_SCENARIOS = (A, B)
    RZ.central_directory = lambda url: (_entries(), None)

    def fake_extract(url, entries, prefix, outdir, **kw):
        sel = [e for e in entries if e["name"].startswith(prefix)]
        for e in sel:
            d = os.path.join(outdir, e["name"])
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(os.path.join(SRC, e["name"]), d)
        print("EXTRACT", prefix, len(sel), "files", flush=True)
        n = sum(e["csize"] for e in sel)
        return {"members": len(sel), "files_written": len(sel), "bytes_written": n, "bytes_downloaded": n}
    RZ.stream_extract = fake_extract
    fr, tf = S.frame_record_e5, S.time_frame_e5

    def frame_record(model, ds, batch, scen, i, *a, **k):
        r = fr(model, ds, batch, scen, i, *a, **k)
        print("FRAME", scen, i, time.strftime("%H:%M:%S"), flush=True)
        return r

    def time_frame(*a, **k):
        r = tf(*a, **k)
        print("TIMING", time.strftime("%H:%M:%S"), flush=True)
        return r
    S.frame_record_e5, S.time_frame_e5 = frame_record, time_frame
    import v3_stream as S3
    sys.argv = ["v3_stream.py"] + argv
    S3.main()


def state(run_dir):
    rd = os.path.join(ROOT, run_dir)
    led = json.load(open(os.path.join(rd, "download_ledger.json"))) if os.path.exists(os.path.join(rd, "download_ledger.json")) else {}
    ls = lambda d: sorted(os.listdir(d)) if os.path.isdir(d) else []
    return {"cache": ls(os.path.join(rd, "cache")), "v3extra": ls(os.path.join(rd, "v3extra")),
            "stream_dir": ls(STREAM_PARENT), "ledger_downloads": [(d["scenario"], d["status"], d["bytes_downloaded"])
                                                                  for d in led.get("downloads", [])],
            "mtimes": {f: os.path.getmtime(os.path.join(rd, "cache", f)) for f in ls(os.path.join(rd, "cache"))}}


def launch(run_dir, log, kill_after=None):
    """Run the frozen stream; if kill_after=(scen, frame), SIGKILL it right after that frame's record line."""
    cmd = [sys.executable, os.path.abspath(__file__), "_run", "--run_dir", run_dir, "--user_approved",
           "--scenarios", A, B]
    t0 = time.time()
    with open(log, "a") as lf:
        lf.write(f"\n=== launch {time.strftime('%H:%M:%S')} kill_after={kill_after}\n")
        lf.flush()
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
        killed = False
        for line in p.stdout:
            lf.write(line)
            lf.flush()
            if kill_after and line.startswith(f"FRAME {kill_after[0]} {kill_after[1]} "):
                p.send_signal(signal.SIGKILL)
                killed = True
        rc = p.wait()
        lf.write(f"=== exit rc={rc} killed={killed} {time.time() - t0:.0f}s\n")
    return {"rc": rc, "killed": killed, "seconds": round(time.time() - t0), "state_after": state(run_dir)}


def drive(out):
    assert not os.path.exists(STREAM_PARENT), "data/opv2v/stream exists; refusing"
    ref, res = os.path.join(out, "uninterrupted"), os.path.join(out, "resumed")
    for d in (ref, res):
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
        os.makedirs(os.path.join(ROOT, d))
    rep = {"label": "DEVELOPMENT procedural test (no network, dev slice); not results", "scenarios": {A: 24, B: 8}}
    rep["uninterrupted"] = launch(ref, os.path.join(ROOT, ref, "run.log"))
    rep["resumed"] = {
        "1_kill_during_A_after_frame_10": launch(res, os.path.join(ROOT, res, "run.log"), (A, 10)),
        "2_restart_kill_during_B_after_frame_3": launch(res, os.path.join(ROOT, res, "run.log"), (B, 3)),
        "3_restart_to_completion": launch(res, os.path.join(ROOT, res, "run.log"))}
    json.dump(rep, open(os.path.join(ROOT, out, "resume_runs.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


# ------------------------------------------------------------------ comparison
def _load(p):
    import e0_stream  # noqa: F401  (shims + paths, needed to unpickle the records)
    with gzip.open(p, "rb") as f:
        return pickle.load(f)


def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in TIME_KEYS}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def diffs(a, b, path="", out=None, limit=20):
    import numpy as np
    import torch
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            out.append((path, "keys"))
            return out
        for k in a:
            diffs(a[k], b[k], f"{path}/{k}", out, limit)
    elif isinstance(a, (list, tuple)):
        if not isinstance(b, (list, tuple)) or len(a) != len(b):
            out.append((path, "len"))
            return out
        for i, (x, y) in enumerate(zip(a, b)):
            diffs(x, y, f"{path}[{i}]", out, limit)
    elif torch.is_tensor(a) or isinstance(a, np.ndarray):
        aa, bb = np.asarray(a), np.asarray(b)
        if aa.dtype != bb.dtype or aa.shape != bb.shape or not np.array_equal(aa, bb, equal_nan=aa.dtype.kind == "f"):
            out.append((path, "array"))
    else:
        import v3_common as V
        if not V.same(a, b):
            out.append((path, f"{a!r} != {b!r}"[:200]))
    return out


def cmp_caches(d1, d2, scen, ignore_top=("timing", "block")):
    r = {}
    for sub in ("cache", "v3extra"):
        x, y = _load(os.path.join(ROOT, d1, sub, f"{scen}.pkl.gz")), _load(os.path.join(ROOT, d2, sub, f"{scen}.pkl.gz"))
        if sub == "cache":
            x = {k: v for k, v in x.items() if k not in ignore_top}
            y = {k: v for k, v in y.items() if k not in ignore_top}
        d = diffs(_strip(x), _strip(y))
        r[sub] = {"frames": len(x["frames"]), "identical_excluding_wallclock": not d, "first_diffs": d}
    return r


def json_diffs(a, b, path="", out=None, skip=("overhead", "scenario_files", "label", "analysis_s", "eval_s", "files")):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in skip:
                continue
            if k not in a or k not in b:
                out.append(f"{path}/{k}: missing")
            else:
                json_diffs(a[k], b[k], f"{path}/{k}", out, skip)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            json_diffs(x, y, f"{path}[{i}]", out, skip)
    elif a != b:
        out.append(f"{path}: {str(a)[:80]} != {str(b)[:80]}")
    return out


def analyze_dir(rd, n_boot):
    import e5_analyze as X
    import v3_analyze as Y
    import v3_stream as S3
    files = [os.path.join(ROOT, rd, "cache", f"{s}.pkl.gz") for s in (B, A)]
    files = sorted(files)
    conds = ("clean",) + X.ORIG + ("spoof_blind",)
    out = X.analyze(files, conds, False, n_boot)
    out["criteria"] = X.analyze_v2(files, conds, out, n_boot)
    json.dump(out, open(os.path.join(ROOT, rd, "e5_test.json"), "w"), indent=1, default=str)
    Y.run_test(rd, S3.PREREG, n_boot, dry=True)


def compare(out, n_boot):
    ref, res = os.path.join(out, "uninterrupted"), os.path.join(out, "resumed")
    rep = {"label": "DEVELOPMENT procedural test (no network, dev slice); not results",
           "excluded_from_comparison": "wall-clock fields only: cache 'timing' (D-42 timing pass), frame_s, v3_s, "
                                       "attack_s; analysis 'overhead' (built from the timing pass)",
           "caches_resumed_vs_uninterrupted": {s: cmp_caches(ref, res, s) for s in (A, B)},
           "cache_A_resumed_vs_committed_v3_dryrun_n2": cmp_caches("runs/20261024-E5/dryrun_v3/n2", res, A)}
    for rd in (ref, res):
        analyze_dir(rd, n_boot)
    rep["analysis_n_boot"] = n_boot
    for f in ("e5_test.json", "e5_v3.json"):
        a, b = (json.load(open(os.path.join(ROOT, d, f))) for d in (ref, res))
        d = json_diffs(a, b)
        rep[f"analysis_{f}_resumed_vs_uninterrupted"] = {"identical_excluding_overhead": not d, "diffs": d[:20]}
    json.dump(rep, open(os.path.join(ROOT, out, "resume_compare.json"), "w"), indent=1, default=str)
    print(json.dumps(rep, indent=1, default=str)[:6000])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_run":
        return run(sys.argv[2:])
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("prepare", "drive", "compare"))
    ap.add_argument("--out", default="runs/20261024-E5/resume_test")
    ap.add_argument("--n_boot", type=int, default=200)
    a = ap.parse_args()
    if a.mode == "prepare":
        prepare()
    elif a.mode == "drive":
        drive(a.out)
    else:
        compare(a.out, a.n_boot)


if __name__ == "__main__":
    main()
