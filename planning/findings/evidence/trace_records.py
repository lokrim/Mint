"""Bounded saved-record checks; no replay, fitting, notebooks, raw-cloud bodies or archives."""
from pathlib import Path
import json,csv,gzip,hashlib,collections,math
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent; RUN=ROOT/'artifacts/20261012T134149Z-R05'
def sh(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def stream(p):
 with gzip.open(p,'rt') as f:
  for line in f:yield json.loads(line)
def save(n,d): (OUT/n).write_text(json.dumps(d,indent=2)+'\n')
def csvrows(n):
 with (RUN/n).open() as f:return list(csv.DictReader(f))
manifest=json.loads((RUN/'manifest.json').read_text()); checked=[]
# Selected important outputs and all current source hashes (no raw archive rehash).
for rel,expected in manifest['source_sha256'].items():
 p=ROOT/rel; actual=sh(p);checked.append({'path':rel,'expected':expected,'sha256':actual,'match':actual==expected,'historical_source':'R05 manifest source_sha256'})
chosen=list(RUN.glob('T_R05_*.csv'))+[RUN/x for x in ['gate.md','notebook_execution.json','test_results_final.xml','environment_final.json','protocol.json']]+list(RUN.glob('*.executed.ipynb'))
for p in chosen:
 rel=str(p.relative_to(RUN));expected=manifest['output_sha256'].get(rel);actual=sh(p)
 checked.append({'path':str(p.relative_to(ROOT)),'expected':expected,'sha256':actual,'match':actual==expected,'historical_source':'R05 manifest output_sha256'})
flows=csvrows('T_R05_attempt_flow.csv'); metrics=csvrows('T_R05_metrics.csv'); traces=[]; rawstats=[]; examples=[]
seal=json.loads((RUN/'prediction_seal.json').read_text())
for segment in ['C0','C1','C2','C3']:
 fold='F'+segment[-1]
 rawpath=RUN/'clean_raw'/f'{segment}.jsonl.gz'; raw=list(stream(rawpath))
 for sensor in ['003','004','laser','top','dome']:
  rr=[r for r in raw if r['stream']==sensor]
  rawstats.append({'segment':segment,'sensor':sensor,'events':len(rr),'density_reasons':dict(collections.Counter(r['density']['reason'] for r in rr)),'geometry_reasons':dict(collections.Counter(r['geometry']['reason'] for r in rr))})
 for spec in [r for r in flows if r['segment']==segment and (r['kind']=='clean' or (r['family']=='addition' and r['severity']=='0.2' and r['schedule']=='sustained'))]:
  path=RUN/'predictions'/fold/spec['episode']/'scores.jsonl.gz'
  expected=seal['files'][str(path.relative_to(RUN/'predictions'))];actual=sh(path)
  checked.append({'path':str(path.relative_to(ROOT)),'expected':expected,'sha256':actual,'match':actual==expected,'historical_source':'prediction seal'})
  attemptpath=RUN/'evaluator'/segment/spec['episode']/'attempts.jsonl.gz'
  attempts={r['cloud_id']:r for r in stream(attemptpath)} if attemptpath.exists() else {}
  rr=[r for r in stream(path) if r['sensor']=='003' and r['arm']=='D-only' and r['version']=='memoryless']
  if spec['kind']=='clean': chosenrows=rr;n=sum(r['alarm'] is True for r in rr);d=sum(r['alarm'] is not None for r in rr);metric='eligible_fpr'
  else:
   chosenrows=[r for r in rr if 5<=r['time_s']<15];d=len(chosenrows)
   n=sum(r['alarm'] is True and attempts[r['cloud_id']]['reader_valid'] and attempts[r['cloud_id']]['realized_changed_rows']>0 and not attempts[r['cloud_id']]['injection_failed'] for r in chosenrows);metric='all_attempt_recall'
  saved=next(r for r in metrics if r['segment']==segment and r['episode']==spec['episode'] and r['sensor']=='003' and r['arm']=='D-only' and r['version']=='memoryless' and r['metric']==metric)
  assert n==int(saved['numerator']) and d==int(saved['denominator'])
  traces.append({'segment':segment,'episode':spec['episode'],'kind':spec['kind'],'metric':metric,'numerator':n,'denominator':d,'scores_path':str(path.relative_to(ROOT)),'attempts_path':str(attemptpath.relative_to(ROOT)) if attempts else None,'match':True})
  for r in chosenrows[:1]+[x for x in chosenrows if x['alarm'] is True][:1]:examples.append({'segment':segment,'path':str(path.relative_to(ROOT)),'record':r,'attempt':attempts.get(r['cloud_id'])})
# All compact attempt records, one episode at a time, retain partial moves separately from injection failure.
att=collections.defaultdict(collections.Counter)
for spec in flows:
 p=RUN/'evaluator'/spec['segment']/spec['episode']/'attempts.jsonl.gz'
 if not p.exists():continue
 for r in stream(p):
  c=att[(spec['kind'],spec['family'])];c['events']+=1
  for k in ['reader_valid','injection_failed']:c[k]+=bool(r[k])
  c['zero_realized_events']+=r['realized_changed_rows']==0;c['partial_move_events']+=r.get('failed_rows',0)>0
  for k in ['failed_rows','intended_rows','realized_changed_rows']:c[k]+=r.get(k,0)
  if spec['family']=='rearrangement':c['nonzero_cell_delta_events']+=r.get('changed_cell_count_l1',0)!=0
save('saved_record_checks.json',{'hash_checks':checked,'traces':traces,'examples':examples,'clean_raw_reasons':rawstats,'attempts_by_kind_family':[{'kind':k[0],'family':k[1],**dict(v)} for k,v in att.items()]})
print('hash matches',sum(r['match'] for r in checked),'/',len(checked));print('traces',traces)
print('raw G',[(r['segment'],r['sensor'],r['geometry_reasons']) for r in rawstats]);print('attempts',[{'kind':k[0],'family':k[1],**dict(v)} for k,v in att.items() if k[0]=='attack'])
