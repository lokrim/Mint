"""Read selected members of a remote ZIP over HTTP range requests (stdlib only).

Used to fetch single OPV2V scenarios without downloading the whole split archive.
Supports ZIP64 and stored/deflated members. Usage:

  python -I tools/ranged_zip.py list URL [--prefix test/]
  python -I tools/ranged_zip.py fetch URL PREFIX OUTDIR [--max-bytes N]
"""
import argparse
import os
import struct
import sys
import urllib.request
import zlib
from collections import defaultdict

UA = {"User-Agent": "Mozilla/5.0 (research; MINT ranged_zip)"}


def get_range(url, start, end):
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        if r.status != 206:
            raise RuntimeError(f"expected 206, got {r.status}")
        total = int(r.headers["Content-Range"].split("/")[-1])
        return r.read(), total


def central_directory(url):
    tail, total = get_range(url, 0, 0)
    tail_len = min(total, 1 << 16)
    tail, _ = get_range(url, total - tail_len, total - 1)
    eocd = tail.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise RuntimeError("EOCD not found")
    cd_size, cd_off = struct.unpack("<II", tail[eocd + 12:eocd + 20])
    if cd_off == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:
        loc = tail.rfind(b"PK\x06\x07")
        z64_off = struct.unpack("<Q", tail[loc + 8:loc + 16])[0]
        rec, _ = get_range(url, z64_off, z64_off + 55)
        assert rec[:4] == b"PK\x06\x06"
        cd_size, cd_off = struct.unpack("<QQ", rec[40:56])
    cd, _ = get_range(url, cd_off, cd_off + cd_size - 1)
    entries, p = [], 0
    while p + 46 <= len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        (method,) = struct.unpack("<H", cd[p + 10:p + 12])
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, xlen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        (lho,) = struct.unpack("<I", cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + xlen]
        q = 0
        while q + 4 <= len(extra):
            hid, hlen = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals, k = extra[q + 4:q + 4 + hlen], 0
                if usize == 0xFFFFFFFF:
                    usize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF:
                    csize = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
                if lho == 0xFFFFFFFF:
                    lho = struct.unpack("<Q", vals[k:k + 8])[0]; k += 8
            q += 4 + hlen
        entries.append(dict(name=name, method=method, csize=csize, usize=usize, lho=lho))
        p += 46 + nlen + xlen + clen
    return entries, total


def fetch_member(url, e, outdir):
    hdr, _ = get_range(url, e["lho"], e["lho"] + 29)
    assert hdr[:4] == b"PK\x03\x04", "bad local header"
    nlen, xlen = struct.unpack("<HH", hdr[26:30])
    start = e["lho"] + 30 + nlen + xlen
    data = b""
    if e["csize"]:
        data, _ = get_range(url, start, start + e["csize"] - 1)
    if e["method"] == 8:
        data = zlib.decompress(data, -15)
    elif e["method"] != 0:
        raise RuntimeError(f"unsupported method {e['method']}")
    assert len(data) == e["usize"], (e["name"], len(data), e["usize"])
    path = os.path.join(outdir, e["name"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def stream_extract(url, entries, prefix, outdir, keep_suffixes=(".pcd", ".yaml"), log=print):
    """Stream one contiguous byte span and write only wanted members (no temp file on disk).

    Returns dict with bytes downloaded and files written. Members must be stored or deflated.
    """
    sel = sorted((e for e in entries if e["name"].startswith(prefix) and not e["name"].endswith("/")),
                 key=lambda e: e["lho"])
    if not sel:
        raise RuntimeError(f"no members under {prefix}")
    lo = sel[0]["lho"]
    last = sel[-1]
    hi = last["lho"] + 30 + len(last["name"].encode()) + 65535 + last["csize"]
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={lo}-{hi - 1}"})
    pos, written, wbytes = lo, 0, 0
    with urllib.request.urlopen(req, timeout=300) as r:
        def read_exact(n):
            nonlocal pos
            buf = bytearray()
            while len(buf) < n:
                chunk = r.read(min(n - len(buf), 1 << 22))
                if not chunk:
                    raise RuntimeError("stream ended early")
                buf += chunk
            pos += n
            return bytes(buf)

        for i, e in enumerate(sel):
            if e["lho"] < pos:
                raise RuntimeError("overlapping members")
            while pos < e["lho"]:                      # skip gaps (e.g. directory entries)
                read_exact(min(e["lho"] - pos, 1 << 22))
            hdr = read_exact(30)
            assert hdr[:4] == b"PK\x03\x04", e["name"]
            nlen, xlen = struct.unpack("<HH", hdr[26:30])
            read_exact(nlen + xlen)
            data = read_exact(e["csize"]) if e["csize"] else b""
            if e["name"].endswith(tuple(keep_suffixes)):
                if e["method"] == 8:
                    data = zlib.decompress(data, -15)
                elif e["method"] != 0:
                    raise RuntimeError(f"unsupported method {e['method']}")
                assert len(data) == e["usize"], e["name"]
                path = os.path.join(outdir, e["name"])
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as g:
                    g.write(data)
                written += 1
                wbytes += len(data)
    return {"members": len(sel), "files_written": written, "bytes_written": wbytes,
            "bytes_downloaded": pos - lo}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "fetch"])
    ap.add_argument("url")
    ap.add_argument("prefix", nargs="?", default="")
    ap.add_argument("outdir", nargs="?", default=".")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--max-bytes", type=int, default=5_000_000_000)
    a = ap.parse_args()
    entries, total = central_directory(a.url)
    if a.cmd == "list":
        agg = defaultdict(lambda: [0, 0])
        for e in entries:
            if e["name"].startswith(a.prefix):
                key = "/".join(e["name"].split("/")[:a.depth])
                agg[key][0] += 1
                agg[key][1] += e["csize"]
        print(f"archive bytes {total}, members {len(entries)}")
        for k in sorted(agg):
            print(f"{k}\t{agg[k][0]}\t{agg[k][1] / 1e9:.3f} GB")
        return
    sel = [e for e in entries if e["name"].startswith(a.prefix) and not e["name"].endswith("/")]
    need = sum(e["csize"] for e in sel)
    print(f"{len(sel)} members, {need / 1e9:.3f} GB compressed")
    if need > a.max_bytes:
        sys.exit(f"refusing: {need} bytes exceeds --max-bytes {a.max_bytes}")
    # Members of one folder are usually contiguous: fetch one byte span, then unpack locally.
    lo = min(e["lho"] for e in sel)
    hi = max(e["lho"] + 30 + len(e["name"].encode()) + e["csize"] + 4096 for e in sel)
    print(f"span {lo}..{hi} = {(hi - lo) / 1e9:.3f} GB (members {need / 1e9:.3f} GB)")
    if hi - lo > a.max_bytes * 1.05:
        sys.exit("refusing: span not contiguous enough")
    part = os.path.join(a.outdir, ".span.part")
    os.makedirs(a.outdir, exist_ok=True)
    have = os.path.getsize(part) if os.path.exists(part) else 0
    if have < hi - lo:
        req = urllib.request.Request(a.url, headers={**UA, "Range": f"bytes={lo + have}-{hi - 1}"})
        with urllib.request.urlopen(req, timeout=300) as r, open(part, "ab") as f:
            got = have
            while True:
                chunk = r.read(1 << 22)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if (got // (1 << 22)) % 25 == 0:
                    print(f"  {got / 1e9:.2f} GB", flush=True)
    with open(part, "rb") as f:
        for e in sel:
            f.seek(e["lho"] - lo)
            hdr = f.read(30)
            assert hdr[:4] == b"PK\x03\x04", e["name"]
            nlen, xlen = struct.unpack("<HH", hdr[26:30])
            f.seek(e["lho"] - lo + 30 + nlen + xlen)
            data = f.read(e["csize"])
            if e["method"] == 8:
                data = zlib.decompress(data, -15)
            assert len(data) == e["usize"], e["name"]
            path = os.path.join(a.outdir, e["name"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as g:
                g.write(data)
    os.remove(part)
    print("done")


if __name__ == "__main__":
    main()
