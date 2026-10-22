# Selected source excerpts

These are evidence, not a runnable migrated implementation. Original paths are repository-relative; hashes are fresh SHA-256 of the entire original file.

## src/valid_point/ablations.py::clean_fixture_rows

Original lines 6–23; file SHA-256 `fe2d4876b0ab7e11aa8a8be0e7292122b0e7591afd8e8c1d265c89297b455ea6`.

```python
   6 def clean_fixture_rows(seeds: list[int], role: str) -> list[dict]:
   7     """Deterministic clean raw fixtures; no LiDAR replay or empirical distribution claim."""
   8     rows = []
   9     for seed in seeds:
  10         segment = f'illustrative_scene_{seed}'
  11         for frame in range(40):
  12             # Each sender/frame has one K residual and three frozen 5 m tile counts.
  13             k = round(.02 + .01*((seed*7 + frame*3) % 19), 4)
  14             for factor, region, value, bin_id, units in (
  15                 ('K', 'motion', k, 'dt_0p5s', 'm'),
  16                 ('S', 'gt_free:A', float(4 + (seed + frame*3) % 9), 'A_near', 'points'),
  17                 ('S', 'gt_free:B', float(5 if frame < 20 else 2 + (seed*3 + frame) % 7), 'B_constant' if frame < 20 else 'B_near', 'points'),
  18                 ('S', 'gt_free:C', float(1 + (seed + frame) % 5), 'C_far_sparse' if seed % 10 < 4 else 'C_near', 'points')):
  19                 rows.append({'split_role':role,'clean':True,'seed':seed,'segment':segment,
  20                              'frame':frame,'factor':factor,'region_id':region,'sensor_class':'vehicle',
  21                              'bin_id':bin_id,'value':value,'units':units,
  22                              'deadline_ns':1550000000+frame*100000000,'track':'gt_free'})
  23     return rows
```

## src/valid_point/evaluation/gap.py::_reference_rows

Original lines 31–47; file SHA-256 `def62317ceccf326510861a363e71dbddbc7ade16766d5e80f3c5f491dad0b64`.

```python
  31 def _reference_rows(track: str, seeds: Iterable[int], frames_per_seed: int) -> list[dict]:
  32     patterns = {
  33         "gt_free": (0, 1, 2, 3, 4),
  34         "oracle_box": (0, 1, 1, 2),
  35     }
  36     pattern = patterns[track]
  37     rows = []
  38     for seed in seeds:
  39         for frame in range(frames_per_seed):
  40             rows.append({
  41                 "split_role": "reference", "clean": True, "seed": seed,
  42                 "segment": f"{track}_reference_{seed}", "frame": frame,
  43                 "factor": "S", "region_id": f"{track}:broad",
  44                 "value": pattern[(seed + frame) % len(pattern)], "units": "points",
  45                 "sensor_class": "vehicle", "bin_id": f"{track}_count",
  46             })
  47     return rows
```

## src/valid_point/evaluation/gap.py::fit_track_calibration

Original lines 71–95; file SHA-256 `def62317ceccf326510861a363e71dbddbc7ade16766d5e80f3c5f491dad0b64`.

```python
  71 def fit_track_calibration(track: str, reference: Reference, config: Mapping) -> tuple[Calibration, dict]:
  72     """Calibrate only against that track's separately declared clean seeds."""
  73     seeds = tuple(config["splits"][track]["calibration_seeds"])
  74     frames_per_seed = int(config["splits"][track]["frames_per_seed"])
  75     rows = []
  76     index = 0
  77     for seed in seeds:
  78         for frame in range(frames_per_seed):
  79             # Four deterministic clean tails in 400 decisions. The fitted threshold
  80             # is retained even when it yields low power; no attack row tunes it.
  81             raw_max = reference.u + 1 if index % 100 == 99 else reference.u
  82             anomaly = max(0.0, min(1.0, (raw_max - reference.u) / reference.b))
  83             rows.append({
  84                 "split_role": "calibration", "clean": True, "seed": seed,
  85                 "segment": f"{track}_calibration_{seed}", "status": "known", "A": anomaly,
  86             })
  87             index += 1
  88     calibration = calibrate(
  89         rows, alpha=float(config["calibration"]["alpha"]),
  90         min_known=int(config["calibration"]["min_known"]), allowed_seeds=set(seeds),
  91     )
  92     return calibration, {
  93         **asdict(calibration), "track": track, "calibration_seeds": list(seeds),
  94         "reference_context": reference.context,
  95     }
```

## src/valid_point/evaluation/real.py::fit_references

Original lines 127–162; file SHA-256 `8c162114ec136d9e95e1d7bf1c9bd135377614a2ab884f2927feaec7fe7c0a6e`.

```python
 127 def fit_references(records: dict[str, list[RawFactorRecord]], fold) -> dict:
 128     if set(records) != set(fold.reference):
 129         raise ValueError('exact frozen reference segments required')
 130     groups = defaultdict(list)
 131     for segment, rows in records.items():
 132         seen = set()
 133         for r in rows:
 134             key = (r.stream, r.cloud_id)
 135             if key in seen or not r.input_sha256:
 136                 if key in seen: raise ValueError('duplicate clean raw input')
 137                 continue
 138             seen.add(key)
 139             identity = f'{segment}:{r.stream}:{r.cloud_id}:{r.input_sha256}'
 140             if r.density.counts is not None:
 141                 if len(r.density.counts) != 32: raise ValueError('incomplete D universe')
 142                 for cell, value in zip(CELL_IDS, r.density.counts):
 143                     for ctx in (cell, 'range:'+cell.split(':')[0]):
 144                         groups[(r.stream,'D',ctx)].append((segment,identity,float(value)))
 145             if r.geometry.distance_m is not None:
 146                 for ctx in ('all', _gap_context(r.geometry.gap_s)):
 147                     if ctx: groups[(r.stream,'G',ctx)].append((segment,identity,r.geometry.distance_m))
 148     reference_id = canonical_hash({'fold':fold.id, 'raw':{s:[r.as_dict() for r in rows] for s,rows in records.items()}})
 149     refs = {}
 150     for sensor in ('003','004','laser','top','dome'):
 151         for factor, contexts in (('D', (*CELL_IDS, *(f'range:r{i}' for i in range(4)))),
 152                                  ('G', ('g0','g1','g2','all'))):
 153             for ctx in contexts:
 154                 values = groups[(sensor,factor,ctx)]
 155                 ids = tuple(sorted({v[1] for v in values}))
 156                 segments = tuple(sorted({v[0] for v in values}))
 157                 counts = {s:len({i for seg,i,_ in values if seg==s}) for s in fold.reference}
 158                 q50,u = map(float,np.quantile([v[2] for v in values],[.5,.95])) if values else (None,None)
 159                 b = None if u is None else 4*(u-q50)
 160                 status = 'LOW_SUPPORT' if len(ids)<200 or len(segments)<2 else 'ZERO_SCALE' if b<=0 else 'SUPPORTED'
 161                 refs[(sensor,factor,ctx)] = Reference(sensor,factor,ctx,u,b,q50,len(values),len(ids),segments,counts,ids,status,reference_id)
 162     return refs
```

## src/valid_point/evaluation/real.py::normalize

Original lines 165–186; file SHA-256 `8c162114ec136d9e95e1d7bf1c9bd135377614a2ab884f2927feaec7fe7c0a6e`.

```python
 165 def normalize(row: RawFactorRecord, refs: dict) -> NormalizedFactors:
 166     reference_id = next(iter(refs.values())).reference_id
 167     ds, contexts = [], []
 168     reason = row.density.reason
 169     if row.density.counts is not None:
 170         if len(row.density.counts)!=32: raise ValueError('incomplete D universe')
 171         for cell, count in zip(CELL_IDS,row.density.counts):
 172             ref = refs.get((row.stream,'D',cell))
 173             if ref is None or ref.status!='SUPPORTED': ref=refs.get((row.stream,'D','range:'+cell.split(':')[0]))
 174             if ref is None or ref.status!='SUPPORTED':
 175                 reason='UNSUPPORTED_CELL:'+cell; break
 176             ds.append(float(np.clip((count-ref.u)/ref.b,0,1))); contexts.append(ref.context)
 177         else: reason='VALID'
 178     d = max(ds) if len(ds)==32 and reason=='VALID' else None
 179     g, gc, gr = None,None,row.geometry.reason
 180     if row.geometry.distance_m is not None:
 181         ref=refs.get((row.stream,'G',_gap_context(row.geometry.gap_s)))
 182         if ref is None or ref.status!='SUPPORTED': ref=refs.get((row.stream,'G','all'))
 183         if ref is None or ref.status!='SUPPORTED': gr='UNSUPPORTED_G_REFERENCE'
 184         else:
 185             g=float(np.clip((row.geometry.distance_m-ref.u)/ref.b,0,1)); gc=ref.context; gr='VALID'
 186     return NormalizedFactors(row.cloud_id,row.stream,row.source_ns,d,g,reason,gr,tuple(contexts),gc,reference_id)
```

## src/valid_point/evaluation/real.py::score_records

Original lines 189–214; file SHA-256 `8c162114ec136d9e95e1d7bf1c9bd135377614a2ab884f2927feaec7fe7c0a6e`.

```python
 189 def score_records(records, refs: dict, *, episode: str, first_ns: int, thresholds=None):
 190     """Typed raw-only path: no evaluator inputs or filesystem access."""
 191     states={v:TemporalEWMA(tau) for v,tau in VERSIONS.items() if tau is not None}
 192     rows=[]
 193     for raw in records:
 194         normalized=normalize(raw,refs)
 195         for arm in ARMS:
 196             inst=decide(raw,normalized,arm)
 197             for version,tau in VERSIONS.items():
 198                 state=None if tau is None else states[version].update(episode=episode,principal=raw.principal,
 199                     sensor=raw.stream,method_arm=arm,reference_version=inst.reference_id,
 200                     source_ns=raw.source_ns,A=inst.A,reason=inst.reason)
 201                 score=inst.A if state is None else state.Z if state.ready else None
 202                 threshold=None if thresholds is None else thresholds[(raw.stream,arm,version)]
 203                 c=None if threshold is None else threshold['threshold']
 204                 why=(inst.reason if inst.A is None else 'VALID') if state is None else state.reason
 205                 if score is not None and c is None: why='UNAVAILABLE_CALIBRATION'
 206                 rows.append({'episode':episode,'cloud_id':raw.cloud_id,'sensor':raw.stream,'principal':raw.principal,
 207                     'source_ns':raw.source_ns,'time_s':(raw.source_ns-first_ns)/1e9,'cloud_sha256':raw.input_sha256,
 208                     'raw_record_id':canonical_hash(raw.as_dict()),'arm':arm,'version':version,
 209                     'normalized':normalized.as_dict(),'A':inst.A,'C':inst.C,
 210                     'state':None if state is None else state.as_dict(), 'score':score,
 211                     'threshold':c,'threshold_id':None if threshold is None else threshold['threshold_id'],
 212                     'alarm':None if c is None or score is None else bool(score>c),'reason':why,
 213                     'reference_id':inst.reference_id})
 214     return rows,{v:s.checkpoint() for v,s in states.items()}
```

## src/valid_point/evaluation/real.py::calibrate

Original lines 217–234; file SHA-256 `8c162114ec136d9e95e1d7bf1c9bd135377614a2ab884f2927feaec7fe7c0a6e`.

```python
 217 def calibrate(rows: list[dict], fold, refs: dict) -> dict:
 218     result={}
 219     for sensor in ('003','004','laser','top','dome'):
 220         for arm in ARMS:
 221             for version in VERSIONS:
 222                 sample=[r for r in rows if (r['sensor'],r['arm'],r['version'])==(sensor,arm,version)]
 223                 values=sorted(r['score'] for r in sample if r['score'] is not None)
 224                 n=len(values); k=ceil((n+1)*.99)
 225                 c=None if n<200 else 1. if k>n else values[k-1]
 226                 lineage={'fold':fold.id,'sensor':sensor,'arm':arm,'version':version,
 227                     'reference_segments':list(fold.reference),'calibration_segment':fold.calibration,'test_segment':fold.test,
 228                     'reference_id':next(iter(refs.values())).reference_id,
 229                     'calibration_raw_ids':[r['raw_record_id'] for r in sample],
 230                     'calibration_record_ids':[canonical_hash(r) for r in sample]}
 231                 result[(sensor,arm,version)]={**lineage,'threshold_id':canonical_hash(lineage),
 232                     'threshold':c,'known':n,'attempts':len(sample),'order_index':k,
 233                     'status':'INSUFFICIENT_KNOWN' if c is None else 'NO_POWER' if c>=1 or len(set(values))==1 else 'AVAILABLE'}
 234     return result
```

## src/valid_point/evaluation/real.py::alignment_poses

Original lines 458–476; file SHA-256 `8c162114ec136d9e95e1d7bf1c9bd135377614a2ab884f2927feaec7fe7c0a6e`.

```python
 458 def alignment_poses(poses, *, family, severity, first_ns, intervals):
 459     """Upstream benign stress; metadata skew cannot move actual availability earlier."""
 460     from dataclasses import replace
 461     transformed=[]
 462     for p in poses:
 463         matrix=None if p.matrix is None else p.matrix.copy()
 464         stamp=p.source_ns
 465         if any(a<=(stamp-first_ns)/1e9<b for a,b in intervals):
 466             if family=='modeled_source_clock_skew_ms': stamp+=int(severity*1e6)
 467             elif matrix is not None:
 468                 delta=np.eye(4)
 469                 if family=='assumed_adapter_translation_m': delta[0,3]=severity
 470                 elif family=='assumed_adapter_yaw_deg':
 471                     angle=np.deg2rad(severity)
 472                     delta[:2,:2]=[[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]
 473                 else: raise ValueError('unknown alignment stress')
 474                 matrix=matrix@delta
 475         transformed.append(replace(p,source_ns=stamp,matrix=matrix))
 476     return sorted(transformed,key=lambda p:(p.source_ns,p.pose_id))
```

## src/valid_point/development_scores.py::decide

Original lines 129–136; file SHA-256 `d74b5419f7e6486f05df45dce928e400c77994da0d110ba7ec49ca893ed85256`.

```python
 129 def decide(row: RawFactorRecord, factors: NormalizedFactors, arm: str) -> InstantaneousDecision:
 130     required={"D-only":(factors.d,),"G-only":(factors.g,),"max(D,G)":(factors.d,factors.g)}
 131     if arm not in required: raise ValueError("unknown arm")
 132     known=all(x is not None for x in required[arm])
 133     A=max(required[arm]) if known else None
 134     why="VALID" if known else ";".join(x for x in (factors.d_reason if factors.d is None else "",factors.g_reason if factors.g is None and arm!="D-only" else "") if x)
 135     return InstantaneousDecision(row.cloud_id,row.stream,row.principal,row.source_ns,arm,
 136                                   "known" if known else "unknown",why,A,None if A is None else 1-A,factors.reference_id)
```

## src/valid_point/evidence/kinematics.py::measure_motion

Original lines 36–115; file SHA-256 `8030cddf92da8c47e7c1982c7d7fea8d8c3e4a0a824e1c946cfefebe84540e2c`.

```python
  36 def measure_motion(key: DecisionKey, samples: tuple[MotionSample, ...], *,
  37                    anchor_ns: int, sensor_role: str = "vehicle", max_age_ns: int,
  38                    min_dt_s: float, max_dt_s: float, clock_verified: bool = True) -> MotionResult:
  39     """Latest two samples at/before anchor, received by deadline, without value-based fallback.
  40 
  41     A sample at a future source time or received after the deadline is never used.
  42     Unknown fields in the selected pair do not cause a search for a more favorable pair.
  43     """
  44     if not (0 <= anchor_ns <= key.deadline_ns and max_age_ns >= 0
  45             and np.isfinite([min_dt_s, max_dt_s]).all() and 0 < min_dt_s <= max_dt_s):
  46         raise ValueError("invalid motion engineering bounds")
  47     if sensor_role not in ("vehicle", "static_rsu"):
  48         raise ValueError("unsupported sensor role")
  49     selected = ()
  50     excluded = []
  51     dt = None
  52 
  53     def result(status, reason, value=None, displacement=None, predicted=None, vector=None):
  54         ids = tuple(s.sample_id for s in selected)
  55         available = max((s.available_ns for s in selected), default=None)
  56         return MotionResult(RawMeasurement(key, "motion_residual", value, "m", status,
  57                                           reason, available, ids), dt, displacement,
  58                             predicted, vector, ids, tuple(excluded))
  59 
  60     if sensor_role == "static_rsu":
  61         return result(Status.NOT_APPLICABLE, "NOT_APPLICABLE_STATIC")
  62     if not clock_verified:
  63         return result(Status.UNKNOWN, "CLOCK_UNVERIFIED")
  64     if len({s.sample_id for s in samples}) != len(samples):
  65         return result(Status.INVALID, "DUPLICATE_SAMPLE_ID")
  66     causal = []
  67     for sample in samples:
  68         if (not sample.sample_id or type(sample.source_ns) is not int
  69                 or type(sample.available_ns) is not int or sample.source_ns < 0
  70                 or sample.available_ns < sample.source_ns):
  71             return result(Status.INVALID, "MALFORMED_SAMPLE_CLOCK")
  72         reason = ("FUTURE_SAMPLE" if sample.source_ns > anchor_ns else
  73                   "LATE" if sample.available_ns > key.deadline_ns else
  74                   "STALE_SAMPLE" if anchor_ns - sample.source_ns > max_age_ns else None)
  75         if reason:
  76             excluded.append((sample.sample_id, reason))
  77         else:
  78             causal.append(sample)
  79     selected = tuple(sorted(causal, key=lambda s: (s.source_ns, s.sample_id))[-2:])
  80     if len(selected) < 2:
  81         return result(Status.UNKNOWN, "INSUFFICIENT_CAUSAL_SAMPLES")
  82     prior, current = selected
  83     dt = (current.source_ns - prior.source_ns) / 1e9
  84     if not min_dt_s <= dt <= max_dt_s:
  85         return result(Status.INVALID, "INVALID_DT")
  86     if any(s.position_frame != "receiver" or s.position_unit != "m" for s in selected):
  87         return result(Status.UNKNOWN, "UNSUPPORTED_POSITION_CONVENTION")
  88     if prior.velocity_frame not in ("body", "receiver") or prior.velocity_unit != "m/s":
  89         return result(Status.UNKNOWN, "UNSUPPORTED_VELOCITY_CONVENTION")
  90     if prior.position is None or current.position is None:
  91         return result(Status.UNKNOWN, "POSITION_MISSING")
  92     if prior.velocity is None:
  93         return result(Status.UNKNOWN, "VELOCITY_MISSING")
  94     if prior.velocity_frame == "body" and prior.rotation is None:
  95         return result(Status.UNKNOWN, "ORIENTATION_MISSING")
  96     try:
  97         p0, p1, v0 = [np.asarray(v, dtype=float) for v in
  98                       (prior.position, current.position, prior.velocity)]
  99         rotation = np.eye(3) if prior.velocity_frame == "receiver" else np.asarray(prior.rotation, dtype=float)
 100         if any(v.shape != (3,) or not np.isfinite(v).all() for v in (p0, p1, v0)):
 101             return result(Status.INVALID, "MALFORMED_MOTION_VECTOR")
 102         if (rotation.shape != (3, 3) or not np.isfinite(rotation).all()
 103                 or not np.allclose(rotation.T @ rotation, np.eye(3), rtol=0, atol=1e-9)
 104                 or not np.isclose(np.linalg.det(rotation), 1, rtol=0, atol=1e-9)):
 105             return result(Status.INVALID, "ORIENTATION_INVALID")
 106     except (ValueError, TypeError):
 107         return result(Status.INVALID, "MALFORMED_MOTION_FIELDS")
 108     displacement = p1 - p0
 109     predicted = rotation @ v0 * dt
 110     vector = displacement - predicted
 111     residual = float(np.linalg.norm(vector))
 112     if not np.isfinite(residual):
 113         return result(Status.INVALID, "NONFINITE_RESIDUAL")
 114     return result(Status.KNOWN, "SELF_REPORT_ONLY", residual,
 115                   tuple(displacement), tuple(predicted), tuple(vector))
```

## src/valid_point/evidence/density.py::count_cells

Original lines 22–38; file SHA-256 `fd86a452008aecb6ccc14d49d0456f0469eacd2a1099f49bbff2b04c55a776aa`.

```python
  22 def count_cells(xyz_native: np.ndarray | None, *, origin_xy_m: tuple[float, float] | None,
  23                 origin_id: str | None, valid_origin: bool) -> DensityRaw:
  24     if not valid_origin or origin_xy_m is None or origin_id is None:
  25         return DensityRaw(None, None, None, "unknown", "SENSOR_ORIGIN_UNVERIFIED", origin_id)
  26     if xyz_native is None:
  27         return DensityRaw(None, None, None, "unknown", "CLOUD_UNAVAILABLE", origin_id)
  28     xyz = np.asarray(xyz_native)
  29     if xyz.ndim != 2 or xyz.shape[1] != 3 or not np.isfinite(xyz).all():
  30         return DensityRaw(None, None, None, "invalid", "NONFINITE_OR_BAD_XYZ", origin_id)
  31     delta = xyz[:, :2] - np.asarray(origin_xy_m)
  32     radius = np.hypot(delta[:, 0], delta[:, 1])
  33     radial = np.searchsorted(RANGES_M, radius, side="right") - 1
  34     sector = np.floor(np.mod(np.arctan2(delta[:, 1], delta[:, 0]), 2*np.pi) / (np.pi/4)).astype(int)
  35     inside = (radial >= 0) & (radial < 4)
  36     counts = np.bincount(radial[inside]*8 + sector[inside], minlength=32)
  37     result = tuple(int(x) for x in counts)
  38     return DensityRaw(result, int((~inside).sum()), sum(x > 0 for x in result), "known", "VALID", origin_id)
```

## src/valid_point/evidence/temporal_geometry.py::_directed_distances

Original lines 41–96; file SHA-256 `7c9afb1a515d029be70eea43f2ee247e729ef3e8e1ee14d13b9e8e45f51f400e`.

```python
  41 def _directed_distances(current: np.ndarray, previous: np.ndarray, *, bucket_m: float = 2.0,
  42                         max_shell: int = 4, max_pair_evaluations: int = 10_000_000) -> tuple[np.ndarray | None, str]:
  43     """Exact within searched buckets; return None if a point needs farther search.
  44 
  45     The bounded 2 m bucket index searches up to four Chebyshev shells. A nearest
  46     point found within the inner boundary of the last searched shell is exact;
  47     otherwise the whole G measurement is unknown rather than capped numeric.
  48     """
  49     from collections import defaultdict
  50     buckets: dict[tuple[int,int,int], list[int]] = defaultdict(list)
  51     pk = np.floor(previous / bucket_m).astype(np.int32)
  52     for i, key in enumerate(pk):
  53         buckets[tuple(int(x) for x in key)].append(i)
  54     out = np.empty(len(current), dtype=np.float64)
  55     pair_evaluations = 0
  56     ck = np.floor(current / bucket_m).astype(np.int32)
  57     # Group current centroids by bucket to reuse neighbor lookup.
  58     groups: dict[tuple[int,int,int], list[int]] = defaultdict(list)
  59     for i, key in enumerate(ck):
  60         groups[tuple(int(x) for x in key)].append(i)
  61     for key, indexes in groups.items():
  62         remaining = np.asarray(indexes, dtype=int)
  63         best = np.full(len(remaining), np.inf)
  64         for shell in range(max_shell + 1):
  65             candidates = []
  66             for dx in range(-shell,shell+1):
  67                 for dy in range(-shell,shell+1):
  68                     for dz in range(-shell,shell+1):
  69                         if max(abs(dx),abs(dy),abs(dz)) != shell:
  70                             continue
  71                         candidates.extend(buckets.get((key[0]+dx,key[1]+dy,key[2]+dz), ()))
  72             if candidates:
  73                 target = previous[candidates]
  74                 # Chunk for bounded memory; no N x N global matrix.
  75                 for start in range(0, len(remaining), 128):
  76                     subset = current[remaining[start:start+128]]
  77                     for cstart in range(0, len(target), 256):
  78                         chunk = target[cstart:cstart+256]
  79                         pair_evaluations += len(subset) * len(chunk)
  80                         if pair_evaluations > max_pair_evaluations:
  81                             return None, "NEIGHBOR_WORK_BUDGET"
  82                         squared = ((subset[:,None,:]-chunk[None,:,:])**2).sum(axis=2)
  83                         best[start:start+len(subset)] = np.minimum(best[start:start+len(subset)], np.sqrt(squared.min(axis=1)))
  84             # Any point with distance <= distance to all unsearched bucket faces is final.
  85             low = np.asarray(key)*bucket_m
  86             high = low + bucket_m
  87             pts = current[remaining]
  88             boundary = np.min(np.column_stack((pts-low, high-pts)), axis=1) + shell*bucket_m
  89             done = best <= boundary
  90             out[remaining[done]] = best[done]
  91             remaining, best = remaining[~done], best[~done]
  92             if len(remaining) == 0:
  93                 break
  94         if len(remaining):
  95             return None, "NEIGHBOR_SEARCH_BOUND"
  96     return out, "VALID"
```

## src/valid_point/evidence/temporal_geometry.py::directed_novelty

Original lines 99–125; file SHA-256 `7c9afb1a515d029be70eea43f2ee247e729ef3e8e1ee14d13b9e8e45f51f400e`.

```python
  99 def directed_novelty(current_xyz: np.ndarray | None, previous_xyz: np.ndarray | None,
 100                      *, current_origin_xy: tuple[float,float], previous_origin_xy: tuple[float,float],
 101                      map_from_current: np.ndarray | None, map_from_previous: np.ndarray | None,
 102                      gap_s: float | None, previous_cloud_id: str | None,
 103                      current_pose_id: str | None, previous_pose_id: str | None,
 104                      min_voxels: int = 100, max_gap_s: float = .5) -> GeometryRaw:
 105     def unknown(reason, nc=None, np_=None, dc=0, dp=0):
 106         return GeometryRaw(None,"unknown",reason,nc,np_,gap_s,previous_cloud_id,current_pose_id,previous_pose_id,dc,dp)
 107     if current_xyz is None or previous_xyz is None or previous_cloud_id is None:
 108         return unknown("NO_CAUSAL_HISTORY")
 109     if gap_s is None or gap_s <= 0 or gap_s > max_gap_s:
 110         return unknown("GAP_OUT_OF_RANGE")
 111     for transform in (map_from_current,map_from_previous):
 112         if transform is None or transform.shape != (4,4) or not np.isfinite(transform).all() or not np.allclose(transform[3], [0,0,0,1]) or not np.allclose(transform[:3,:3].T@transform[:3,:3], np.eye(3), atol=1e-3) or np.linalg.det(transform[:3,:3]) < .999:
 113             return unknown("INVALID_TRANSFORM")
 114     if not np.isfinite(current_xyz).all() or not np.isfinite(previous_xyz).all():
 115         return unknown("NONFINITE_XYZ")
 116     current, dc = voxel_centroids(current_xyz, current_origin_xy)
 117     previous, dp = voxel_centroids(previous_xyz, previous_origin_xy)
 118     if len(current) < min_voxels or len(previous) < min_voxels:
 119         return unknown("INSUFFICIENT_VOXEL_SUPPORT",len(current),len(previous),dc,dp)
 120     transform = np.linalg.inv(map_from_current) @ map_from_previous
 121     previous_in_current = previous @ transform[:3,:3].T + transform[:3,3]
 122     distances, search_reason = _directed_distances(current, previous_in_current)
 123     if distances is None:
 124         return unknown(search_reason,len(current),len(previous),dc,dp)
 125     return GeometryRaw(float(np.quantile(distances,.9)),"known","VALID",len(current),len(previous),gap_s,previous_cloud_id,current_pose_id,previous_pose_id,dc,dp,dc>0 or dp>0)
```

## src/valid_point/replay.py::_select_pose

Original lines 155–165; file SHA-256 `7c6fa388713a5f8b64b44ce5292042938dc56596ae3e3b999885962fc075de4f`.

```python
 155 def _select_pose(poses: list[PoseEvent], source_ns: int, deadline_ns: int,
 156                  max_age_ns: int) -> tuple[PoseEvent | None,str]:
 157     eligible=[p for p in poses if p.source_ns <= source_ns and p.available_ns <= deadline_ns]
 158     if not eligible:
 159         return None,"NO_CAUSAL_POSE"
 160     pose=max(eligible,key=lambda p:(p.source_ns,p.pose_id))
 161     if source_ns-pose.source_ns > max_age_ns:
 162         return None,"STALE_POSE"
 163     if not pose.valid or pose.matrix is None:
 164         return None,"INVALID_POSE"
 165     return pose,"VALID"
```

## src/valid_point/replay.py::replay

Original lines 183–248; file SHA-256 `7c6fa388713a5f8b64b44ce5292042938dc56596ae3e3b999885962fc075de4f`.

```python
 183 def replay(events: Iterable[CloudEvent], source: AllowedSource, *, config: ReplayConfig = ReplayConfig(),
 184            poses: dict[str,list[PoseEvent]] | None = None) -> tuple[RawFactorRecord,...]:
 185     event_list=list(events)
 186     if poses is None:
 187         poses={stream:source.read_poses(stream) for stream in VEHICLES}
 188     history: dict[str,tuple[CloudEvent,np.ndarray,np.ndarray,tuple[float,float],str | None,DensityRaw]]={}
 189     output=[]
 190     for event in event_list:
 191         pose=None; pose_reason="STATIC_RSU"
 192         if event.stream in VEHICLES:
 193             pose,pose_reason=_select_pose(poses.get(event.stream,[]),event.source_ns,event.deadline_ns,config.max_pose_age_ns)
 194         transform,origin,origin_id=_frame(event.stream,pose)
 195         if event.stream not in config.validated_origins:
 196             origin,origin_id=None,None
 197         prior=history.get(event.stream)
 198         xyz=None; digest=None; reason="VALID"
 199         if event.state == "absent":
 200             reason="CLOUD_ABSENT"
 201         elif event.source_ns > event.deadline_ns:
 202             reason="FUTURE_SOURCE"
 203         elif event.arrival_ns > event.deadline_ns:
 204             reason="LATE_ARRIVAL"
 205         elif event.arrival_ns < event.source_ns:
 206             reason="ARRIVAL_BEFORE_SOURCE"
 207         elif event.deadline_ns-event.source_ns > config.max_cloud_age_ns:
 208             reason="STALE_CLOUD"
 209         else:
 210             try:
 211                 xyz,digest=source.read_cloud(event)
 212             except (ValueError,OSError,PermissionError,UnicodeError) as exc:
 213                 reason="MALFORMED_OR_FORBIDDEN_CLOUD:"+type(exc).__name__
 214         if reason != "VALID":
 215             density=DensityRaw(None,None,None,"unknown",reason,origin_id)
 216         else:
 217             density=count_cells(xyz,origin_xy_m=origin,origin_id=origin_id,valid_origin=origin is not None)
 218         if reason != "VALID":
 219             g_reason=reason
 220         elif origin is None:
 221             g_reason="SENSOR_ORIGIN_UNVERIFIED"
 222         elif transform is None:
 223             g_reason=pose_reason
 224         elif prior is None:
 225             g_reason="NO_CAUSAL_HISTORY"
 226         else:
 227             g_reason="VALID"
 228         if g_reason == "VALID" and prior is not None:
 229             old_event,old_xyz,old_transform,old_origin,old_pose_id,old_density=prior
 230             geometry=directed_novelty(xyz,old_xyz,current_origin_xy=origin,previous_origin_xy=old_origin,
 231                 map_from_current=transform,map_from_previous=old_transform,
 232                 gap_s=(event.source_ns-old_event.source_ns)/1e9,previous_cloud_id=old_event.cloud_id,
 233                 current_pose_id=pose.pose_id if pose else None,previous_pose_id=old_pose_id,
 234                 min_voxels=config.min_voxels,max_gap_s=config.max_gap_s)
 235         else:
 236             geometry=GeometryRaw(None,"unknown",g_reason,None,None,None,
 237                 prior[0].cloud_id if prior else None,pose.pose_id if pose else None,
 238                 prior[4] if prior else None)
 239         delta=occupancy_change(density,prior[5] if prior else None)
 240         output.append(RawFactorRecord(event.cloud_id,event.stream,event.principal,event.sync_id,
 241             event.source_ns,event.arrival_ns,event.deadline_ns,event.state,digest,
 242             pose.pose_id if pose else None,(event.source_ns-pose.source_ns)/1e9 if pose else None,
 243             prior[0].cloud_id if prior else None,prior[4] if prior else None,density,geometry,delta,
 244             reason if reason != "VALID" else pose_reason if transform is None else "VALID"))
 245         # The most recent eligible cloud, even if geometrically unusual, becomes history.
 246         if reason == "VALID" and transform is not None and origin is not None and (prior is None or event.source_ns > prior[0].source_ns):
 247             history[event.stream]=(event,xyz,transform,origin,pose.pose_id if pose else None,density)
 248     return tuple(output)
```

## src/valid_point/temporal.py::TemporalEWMA

Original lines 31–96; file SHA-256 `97bd54bfa4fdcfe4ba8463837676b6d9341a5fe77b019017db12026838ee5638`.

```python
  31 class TemporalEWMA:
  32     def __init__(self, tau_s: float = 1., g_reset_s: float = .5,
  33                  min_updates: int = 10):
  34         if not isfinite(tau_s) or tau_s <= 0 or not isfinite(g_reset_s) or g_reset_s <= 0 or min_updates < 1:
  35             raise ValueError("invalid temporal settings")
  36         self.tau_s=tau_s; self.g_reset_s=g_reset_s; self.min_updates=min_updates
  37         self._states: dict[tuple, dict] = {}
  38         self._versions: dict[tuple, str] = {}
  39 
  40     def update(self, *, episode: str, principal: str, sensor: str,
  41                method_arm: str, reference_version: str, source_ns: int,
  42                A: float | None, reason: str = "VALID") -> TemporalRecord:
  43         if type(source_ns) is not int or not all((episode,principal,sensor,method_arm,reference_version)):
  44             raise ValueError("invalid temporal identity/time")
  45         if A is not None and (not isfinite(A) or not 0 <= A <= 1):
  46             raise ValueError("A outside [0,1]")
  47         base=(episode,principal,sensor,method_arm)
  48         old_version=self._versions.get(base)
  49         version_reset=old_version is not None and old_version != reference_version
  50         if version_reset:
  51             self._states.pop(base+(old_version,),None)
  52         self._versions[base]=reference_version
  53         key=base+(reference_version,)
  54         state=self._states.get(key)
  55         if state is not None and source_ns <= state["last_event_ns"]:
  56             why="DUPLICATE_TIME" if source_ns == state["last_event_ns"] else "REVERSED_TIME"
  57             return self._record(key,source_ns,"unknown",why,state,None,False)
  58         if state is not None:
  59             state["last_event_ns"]=source_ns
  60         if A is None:
  61             return self._record(key,source_ns,"unknown",reason,state,None,False)
  62         reset=version_reset
  63         if state is None or (source_ns-state["last_eligible_ns"])/1e9 > self.g_reset_s:
  64             reset=reset or state is not None
  65             state={"Z":float(A),"first_ns":source_ns,"last_eligible_ns":source_ns,
  66                    "last_event_ns":source_ns,"updates":1}
  67             self._states[key]=state
  68         else:
  69             dt=(source_ns-state["last_eligible_ns"])/1e9
  70             rho=exp(-dt/self.tau_s)
  71             state["Z"]=rho*state["Z"]+(1-rho)*A
  72             state["last_eligible_ns"]=source_ns
  73             state["updates"]+=1
  74         ready=state["updates"]>=self.min_updates and (source_ns-state["first_ns"])/1e9 >= 3*self.tau_s
  75         return self._record(key,source_ns,"known","VALID" if ready else "WARM_UP",state,state["Z"],reset)
  76 
  77     def _record(self,key,source_ns,status,reason,state,public_z,reset):
  78         age=None if state is None else max(0.,(source_ns-state["last_eligible_ns"])/1e9)
  79         duration=0. if state is None else (state["last_eligible_ns"]-state["first_ns"])/1e9
  80         ready=public_z is not None and state["updates"]>=self.min_updates and duration>=3*self.tau_s
  81         return TemporalRecord(*key,source_ns,status,reason,public_z,
  82                               None if public_z is None else 1-public_z,
  83                               None if state is None else state["Z"],age,
  84                               0 if state is None else state["updates"],duration,ready,reset)
  85 
  86     def checkpoint(self) -> dict:
  87         return {"tau_s":self.tau_s,"g_reset_s":self.g_reset_s,"min_updates":self.min_updates,
  88                 "states":[{"key":list(key),**state} for key,state in sorted(self._states.items())],
  89                 "versions":[{"key":list(key),"version":value} for key,value in sorted(self._versions.items())]}
  90 
  91     @classmethod
  92     def resume(cls, checkpoint: dict) -> "TemporalEWMA":
  93         result=cls(checkpoint["tau_s"],checkpoint["g_reset_s"],checkpoint["min_updates"])
  94         result._states={tuple(row["key"]):{k:v for k,v in row.items() if k!="key"} for row in checkpoint["states"]}
  95         result._versions={tuple(row["key"]):row["version"] for row in checkpoint["versions"]}
  96         return result
```

## src/valid_point/evaluation/metrics.py::event_metrics

Original lines 26–49; file SHA-256 `b922a5251bf809e0bd894005b4ec79399e22f9f19fff2ff9de0272c151b524b7`.

```python
  26 def event_metrics(rows: list[dict]) -> dict:
  27     """One row per scheduled attempted event, including failures and unknowns."""
  28     keys = [(r["segment"], r["episode"], r["principal"], r["sensor"], r["cloud_id"]) for r in rows]
  29     if len(keys) != len(set(keys)):
  30         raise ValueError("duplicate attempted event")
  31     for r in rows:
  32         if r["alarm"] not in (True, False, None):
  33             raise ValueError("invalid alarm")
  34         if r["alarm"] is not None and r.get("score") is None:
  35             raise ValueError("known alarm without score")
  36         if r.get("score") is not None and (not isfinite(r["score"]) or not 0 <= r["score"] <= 1):
  37             raise ValueError("invalid score")
  38     eligible = [r for r in rows if r["alarm"] is not None]
  39     realized = [r for r in rows if r.get("reader_valid") is True and r.get("realized_changed_rows", 0) > 0]
  40     alarmed = lambda sample: sum(r["alarm"] is True and r.get("reader_valid") is True
  41                                  and r.get("realized_changed_rows", 0) > 0
  42                                  and not r.get("injection_failed", False) for r in sample)
  43     return {"all_attempt_recall": ratio(alarmed(rows), len(rows)),
  44             "eligible_recall": ratio(alarmed(eligible), len(eligible), empty_reason="NO_ELIGIBLE_SCORES"),
  45             "realized_recall": ratio(alarmed(realized), len(realized), empty_reason="NO_REALIZED_CHANGE"),
  46             "eligible_coverage": ratio(len(eligible), len(rows)),
  47             "failed_injection_count": sum(r.get("injection_failed", False) for r in rows),
  48             "reader_rejected_count": sum(r.get("reader_valid") is False for r in rows),
  49             "missing_score_count": sum(r.get("score") is None for r in rows)}
```

## src/valid_point/evaluation/metrics.py::episode_metrics

Original lines 60–108; file SHA-256 `b922a5251bf809e0bd894005b4ec79399e22f9f19fff2ff9de0272c151b524b7`.

```python
  60 def episode_metrics(rows: list[dict], *, onset_s: float, offset_s: float,
  61                     end_s: float, g_reset_s: float = .5, recovery_hold_s: float = 2.) -> dict:
  62     if onset_s >= offset_s or end_s < offset_s:
  63         raise ValueError("invalid episode times")
  64     sample = sorted(rows, key=lambda r: r["time_s"])
  65     if any(a["time_s"] == b["time_s"] for a, b in zip(sample, sample[1:])):
  66         raise ValueError("duplicate event time")
  67     inside = [r for r in sample if onset_s <= r["time_s"] < offset_s]
  68     before = [r for r in sample if r["time_s"] < onset_s]
  69     preexisting = bool(before and before[-1]["alarm"] is True)
  70     realized = [r for r in inside if r.get("reader_valid") is True and r.get("realized_changed_rows", 0) > 0]
  71     exposure = bool(realized)
  72     alarms = [r for r in inside if r["alarm"] is True and r.get("reader_valid") is True
  73               and r.get("realized_changed_rows", 0) > 0 and not r.get("injection_failed", False)]
  74     new_alarms = [r for r in alarms if not preexisting]
  75     if preexisting:
  76         delay = {"value_s": None, "status": "PREEXISTING_ALARM", "censor_s": None}
  77     elif not exposure:
  78         delay = {"value_s": None, "status": "NO_REALIZED_EXPOSURE", "censor_s": offset_s - onset_s}
  79     elif not any(r["alarm"] is not None for r in inside):
  80         delay = {"value_s": None, "status": "NO_ELIGIBLE_ALARM", "censor_s": offset_s - onset_s}
  81     elif not new_alarms:
  82         delay = {"value_s": None, "status": "RIGHT_CENSORED_NO_DETECTION", "censor_s": offset_s - onset_s}
  83     else:
  84         delay = {"value_s": new_alarms[0]["time_s"] - onset_s, "status": "DETECTED", "censor_s": None}
  85     first_realized = realized[0]["time_s"] if realized else None
  86     delay["first_realized_onset_s"] = first_realized
  87     delay["from_first_realized_s"] = None if first_realized is None or not new_alarms else new_alarms[0]["time_s"] - first_realized
  88     recovery = {"value_s": None, "status": "NOT_APPLICABLE_NEVER_ALARMED"}
  89     if alarms:
  90         recovery = {"value_s": None, "status": "RIGHT_CENSORED_NO_PERSISTENCE"}
  91         after = [r for r in sample if offset_s <= r["time_s"] <= end_s]
  92         start = None; previous = None
  93         for r in after:
  94             valid = r["alarm"] is False and not r.get("reset", False)
  95             gap = previous is not None and r["time_s"] - previous > g_reset_s
  96             if not valid or gap:
  97                 start = None
  98             if valid and start is None:
  99                 start = r["time_s"]
 100             if start is not None and r["time_s"] - start >= recovery_hold_s:
 101                 recovery = {"value_s": r["time_s"] - offset_s, "status": "RECOVERED"}
 102                 break
 103             previous = r["time_s"] if valid else None
 104         if recovery["value_s"] is None and any(r["alarm"] is None or r.get("reset", False) for r in after):
 105             recovery["status"] = "UNDEFINED_INTERRUPTED_SUPPORT"
 106     return {"attempted_episode": True, "realized_nonzero_episode": exposure,
 107             "alarm_in_window": bool(alarms), "preexisting_alarm": preexisting,
 108             "delay": delay, "recovery": recovery}
```

## src/valid_point/evaluation/statistics.py::grouped_rates

Original lines 42–61; file SHA-256 `a1c20bc4481a9e188b11473810fa5ced1ba79444bcd660f39e551d10938e8eeb`.

```python
  42 def grouped_rates(rows):
  43     groups=defaultdict(list)
  44     for r in rows:
  45         if 'numerator' not in r: continue
  46         key=tuple(r[k] for k in ('family','severity','schedule','kind','sensor','arm','version','metric'))
  47         groups[key].append(r)
  48     output=[]
  49     for key,sample in groups.items():
  50         if len({r['segment'] for r in sample})!=len(sample): raise ValueError('duplicate segment metric')
  51         values={r['segment']:r['value'] for r in sample if r['value'] is not None}
  52         omitted=sorted({'C0','C1','C2','C3'}-set(values))
  53         n=sum(r['numerator'] for r in sample); d=sum(r['denominator'] for r in sample)
  54         base=dict(zip(('family','severity','schedule','kind','sensor','arm','version','metric'),key))
  55         output.append({**base,'macro':sum(values.values())/len(values) if values else None,
  56             'micro':n/d if d else None,'micro_numerator':n,'micro_denominator':d,
  57             'contributing_segments':len(values),'omitted_segments':omitted,
  58             'segment_values':values,'range':None if not values else [min(values.values()),max(values.values())],
  59             'leave_one_segment':{s:sum(v for k,v in values.items() if k!=s)/(len(values)-1) for s in values if len(values)>1},
  60             'uncertainty':'descriptive only; shared cross-fold training; session independence unverified; no between-session CI'})
  61     return output
```

## src/valid_point/evaluation/statistics.py::final_recovery

Original lines 388–404; file SHA-256 `a1c20bc4481a9e188b11473810fa5ced1ba79444bcd660f39e551d10938e8eeb`.

```python
 388 def final_recovery(sample, intervals):
 389     """Recovery after the LAST intervention, even when only an earlier burst alarmed."""
 390     last=intervals[-1][1]
 391     alarmed=any(r['alarm'] is True and r['reader_valid'] and r['realized_changed_rows']>0
 392         and not r['injection_failed'] and any(a<=r['time_s']<b for a,b in intervals) for r in sample)
 393     if not alarmed: return {'value_s':None,'status':'NOT_APPLICABLE_NEVER_ALARMED','last_offset_s':last}
 394     start=None; previous=None; interrupted=False
 395     for r in sorted((r for r in sample if r['time_s']>=last),key=lambda r:r['time_s']):
 396         valid=r['alarm'] is False and not r.get('reset',False)
 397         gap=previous is not None and r['time_s']-previous>.5
 398         if not valid or gap:
 399             start=None; interrupted|=r['alarm'] is None or r.get('reset',False) or gap
 400         if valid and start is None: start=r['time_s']
 401         if start is not None and r['time_s']-start>=2:
 402             return {'value_s':r['time_s']-last,'status':'RECOVERED','last_offset_s':last}
 403         previous=r['time_s'] if valid else None
 404     return {'value_s':None,'status':'UNDEFINED_INTERRUPTED_SUPPORT' if interrupted else 'RIGHT_CENSORED_NO_PERSISTENCE','last_offset_s':last}
```

## tests/test_gt_isolation.py::test_withholding_and_permuting_evaluator_labels_leaves_gt_free_scores_identical

Original lines 41–47; file SHA-256 `8ec6dea4ce24ec34e9fcdb085588e5ab3a01bd2bb39735b132de17ccb57fcfd2`.

```python
  41 def test_withholding_and_permuting_evaluator_labels_leaves_gt_free_scores_identical():
  42     scores, labels = _operational_scores()
  43     withheld = None
  44     permuted = tuple(reversed(labels))
  45     scores_again, _ = _operational_scores()
  46     assert withheld is None and permuted != labels
  47     assert scores_again == scores
```

## tests/test_evaluation.py::test_evaluator_withheld_changed_and_leaky_positive_control

Original lines 103–119; file SHA-256 `a99b117e4ca49e9e4ccd13414c10c396d36fa04d8c7829ba4bc945cc4159bf36`.

```python
 103 def test_evaluator_withheld_changed_and_leaky_positive_control(tmp_path,monkeypatch):
 104     events,extras,evaluator,run=fixture_pipeline(tmp_path)
 105     secret=evaluator/'labels_GT_schedule_masks_clean_outcomes.json'
 106     secret.write_text('{"value":1}')
 107     first=run(events)
 108     def deliberately_leaky_pipeline(): return run(events),secret.read_text()
 109     leaked_before=deliberately_leaky_pipeline()
 110     secret.write_text('{"value":999}')
 111     assert first==run(events)
 112     with pytest.raises(AssertionError): assert leaked_before==deliberately_leaky_pipeline()
 113     original_open=Path.open
 114     def guarded(path,*args,**kwargs):
 115         if evaluator in path.parents: raise PermissionError('evaluator boundary')
 116         return original_open(path,*args,**kwargs)
 117     monkeypatch.setattr(Path,'open',guarded)
 118     assert first==run(events)
 119     with pytest.raises(PermissionError): deliberately_leaky_pipeline()
```
