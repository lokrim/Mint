"""Bounded read-only probe: placeholder (repeated fixed-coordinate) points in organized PCDs.
Reads the middle-sorted cloud per stream per segment. Writes JSON to argv[2]."""
import glob, os, sys, json, hashlib
import numpy as np
root = sys.argv[1]; out = sys.argv[2]
ORIG = {'top': (-41.551, -51.878), 'dome': (-41.507, -51.864)}
R = (0., 10., 25., 50., 80.)
res = []
for seg in ('mini_7', 'mini_10', 'mini_11', 'mini_12', 'mini_13'):
    files = sorted(glob.glob(f'{root}/PointClouds/{seg}/*.pcd'))
    by = {}
    for f in files: by.setdefault(os.path.basename(f).split('_')[0], []).append(f)
    for s, fs in sorted(by.items()):
        f = sorted(fs, key=lambda p: int(os.path.basename(p).split('_')[1]))[len(fs)//2]
        raw = open(f, 'rb').read()
        head, body = raw.split(b'DATA ascii\n', 1)
        hdr = dict((l.split(' ', 1)[0], l.split(' ', 1)[1]) for l in head.decode().splitlines() if ' ' in l and not l.startswith('#'))
        a = np.loadtxt(body.decode().splitlines(), dtype=np.float32)
        u, c = np.unique(a[:, :3], axis=0, return_counts=True)
        mode = u[np.argmax(c)]; eq = np.all(a[:, :3] == mode, axis=1)
        o = np.array(ORIG.get(s, (0., 0.)))
        d = a[:, :2] - o; r = np.hypot(d[:, 0], d[:, 1])
        radial = np.searchsorted(R, r, side='right') - 1
        sector = np.floor(np.mod(np.arctan2(d[:, 1], d[:, 0]), 2*np.pi)/(np.pi/4)).astype(int)
        cell00 = (radial == 0) & (sector == 0)
        res.append({'segment': seg, 'stream': s, 'file': os.path.relpath(f, root), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'width': int(hdr['WIDTH']), 'height': int(hdr['HEIGHT']), 'points': len(a),
                    'mode_xyz': [round(float(x), 4) for x in mode], 'mode_count': int(c.max()),
                    'mode_fraction': round(float(eq.mean()), 4), 'second_highest_repeat': int(np.sort(c)[-2]),
                    'r0a0_count': int(cell00.sum()), 'r0a0_placeholder_count': int((cell00 & eq).sum()),
                    'inside_crop_count': int(((radial >= 0) & (radial < 4)).sum())})
        print(res[-1]['segment'], s, res[-1]['mode_xyz'], res[-1]['mode_fraction'], res[-1]['r0a0_count'], res[-1]['r0a0_placeholder_count'], flush=True)
json.dump(res, open(out, 'w'), indent=1)
