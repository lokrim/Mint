"""Read-only repository extraction; writes only this findings directory. No project imports.
Run: python3 planning/findings/evidence/audit_extract.py
Does not read raw PCD bodies, archives, holdout directories, or rerun experiments.
"""
from pathlib import Path
import csv, json, hashlib, os, collections, ast, re, subprocess, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parents[1]; EV=OUT/'evidence'
RUN=ROOT/'artifacts/20261012T134149Z-R05'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def dump(name,obj): (EV/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def table(name,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with (EV/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def rows(name):
 with (RUN/name).open() as f:return list(csv.DictReader(f))
def walk(base):
 for d,dirs,files in os.walk(base):
  dirs[:]=[x for x in dirs if x not in ['.git','.venv','.cache','.pytest_cache','__pycache__','findings','mini_14']]
  for n in sorted(files):
   if 'mini_14' in n or n=='.DS_Store':continue
   yield Path(d)/n
# Preserve initial non-holdout metadata snapshot for final write-scope comparison.
files=list(walk(ROOT))
baseline=EV/'initial_file_state.json'
if not baseline.exists():
 baseline.write_text(json.dumps({str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files},indent=2)+'\n')
# All planning content read programmatically. Digest includes every paragraph; human close reading is separately scoped.
planning=[]
for p in sorted((ROOT/'planning').rglob('*.md')):
 if OUT in p.parents:continue
 text=p.read_text(); lines=text.splitlines()
 planning.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p),'headings':[f'{i+1}: {s}' for i,s in enumerate(lines) if s.startswith('#')], 'decision_excerpt':[f'{i+1}: {s}' for i,s in enumerate(lines) if re.search(r'(?i)(supersed|retract|pending|complete|blocked|not run|not implemented|PASS|FAIL|H00[0-9]|H01[0-9])',s)]})
dump('planning_content_index.json',planning)
# AST-level source/scripts/tests inspection, including function/test inventories and imports.
code=[]
for base in ['src','scripts','tests']:
 for p in sorted((ROOT/base).rglob('*.py')):
  text=p.read_text(); tree=ast.parse(text)
  code.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'lines':len(text.splitlines()),'docstring':ast.get_docstring(tree),'definitions':[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))],'imports':[ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]})
dump('code_content_index.json',code)
# Parse ALL notebook cells and output types/text/errors; never execute. Omit image payloads.
nb=[]
for p in files:
 if p.suffix!='.ipynb':continue
 d=json.loads(p.read_text()); cells=[]
 for i,c in enumerate(d.get('cells',[])):
  outputs=[]
  for o in c.get('outputs',[]):
   plain=''.join(o.get('text',[])) or ''.join(o.get('data',{}).get('text/plain',[]))
   outputs.append({'type':o.get('output_type'),'ename':o.get('ename'),'evalue':o.get('evalue'),'text_excerpt':plain[:2200],'mime_types':list(o.get('data',{}))})
  cells.append({'cell':i,'type':c['cell_type'],'execution_count':c.get('execution_count'),'source':''.join(c.get('source',[])),'outputs':outputs})
 nb.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'cells':cells})
dump('notebook_cells.json',nb)
# Saved gate/test/failure/environment/log content across stages; inspect bounded text, not dense tables or source snapshots.
records=[]
for p in files:
 if 'artifacts' not in p.parts:continue
 n=p.name
 if n.startswith(('gate','failure','environment','resource','implementation_correction')) or n in ['execution.log','predict.log','test_final.log','test_results_final.xml']:
  if p.stat().st_size>150000 or p.suffix in ['.py','.pyc']:continue
  txt=p.read_text(errors='replace')
  records.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'text':txt})
dump('run_status_and_failures.json',records)
# Whole table numeric reconciliation, complete compact grids.
group=rows('T_R05_grouped.csv'); metrics=rows('T_R05_metrics.csv'); support=rows('T_R05_clean_support.csv'); flow=rows('T_R05_attempt_flow.csv')
keyfields=['family','severity','schedule','kind','sensor','arm','version','metric']
agg=collections.defaultdict(list)
for r in metrics: agg[tuple(r[k] for k in keyfields)].append(r)
checks=[]
for r in group:
 rr=agg[tuple(r[k] for k in keyfields)]; n=sum(int(x['numerator']) for x in rr); d=sum(int(x['denominator']) for x in rr)
 vals=[float(x['value']) for x in rr if x['value']!='']; macro=sum(vals)/len(vals) if vals else None
 assert n==int(r['micro_numerator']) and d==int(r['micro_denominator'])
 assert (r['micro']=='' and d==0) or abs(float(r['micro'])-n/d)<1e-12
 assert (r['macro']=='' and macro is None) or abs(float(r['macro'])-macro)<1e-12
 checks.append(True)
# Pivot complete primary + sensitivity sender grid; contains all rates with explicit denominators.
pivot={}
for r in group:
 if r['sensor']!='003':continue
 k=tuple(r[x] for x in keyfields[:-1]); out=pivot.setdefault(k,{x:r[x] for x in keyfields[:-1]})
 for field in ['micro_numerator','micro_denominator','micro','macro','segment_values','omitted_segments']:
  out[r['metric']+'__'+field]=r[field]
table('r05_sender_complete_grid.csv',list(pivot.values()))
# Full clean companion grid and all stresses available for every stream (compact eligible FPR + coverage).
table('r05_all_sensor_control_rates.csv',[r for r in group if r['kind']!='attack' and r['metric'] in ['eligible_fpr','eligible_coverage']])
table('r05_sender_segment_metrics.csv',[r for r in metrics if r['sensor']=='003'])
cal=[r for r in support if r['support_type']=='calibration'];table('r05_calibration_cells.csv',cal)
table('r05_attempt_flow.csv',flow)
paired=rows('T_R05_paired_effects.csv');table('r05_sender_paired_effects.csv',[r for r in paired if r['sensor']=='003'])
outcomes=rows('T_R05_episode_outcomes.csv');table('r05_sender_interval_outcomes.csv',outcomes)
summary={'grouped_rows_reconciled':len(checks),'metric_rows':len(metrics),'episode_counts':dict(collections.Counter((r['segment']+':'+r['kind']) for r in flow)),
 'calibration_status':dict(collections.Counter(r['status'] for r in cal)), 'no_power_thresholds':dict(collections.Counter(r['threshold'] for r in cal if r['status']=='NO_POWER')),
 'reference_status':dict(collections.Counter(r['status'] for r in support if r['support_type']=='reference')),
 'clean_primary_003':[r for r in group if r['kind']=='clean' and r['sensor']=='003' and r['version'] in ['memoryless','EWMA']],
 'nonzero_attack_recall_003':[r for r in group if r['kind']=='attack' and r['sensor']=='003' and r['metric']=='all_attempt_recall' and int(r['micro_numerator'])>0],
 'delay_status_all':dict(collections.Counter(json.loads(r['delay'])['status'] for r in outcomes)),
 'recovery_status_all':dict(collections.Counter(json.loads(r['recovery'])['status'] for r in outcomes)),
 'flow_totals':{k:sum(int(r[k]) for r in flow if r[k]) for k in ['attempts','injection_failed','reader_valid','scheduled_events','sender_events']}}
dump('numeric_audit.json',summary)
# Exact local paths/sizes from allowlisted segments only; small odometry content rechecked.
rev='1a61aea747aa6bc45da2c2f085a1f1d3abc41f91'; data=ROOT/'data/mixed_signals'/rev
inv=[]; odom=[]; headers=[]
for s in ['mini_7','mini_10','mini_11','mini_12','mini_13']:
 a=data/'archives/train'/f'{s}.tar'; inv.append({'path':str(a.relative_to(ROOT)),'bytes':a.stat().st_size,'verification':'stat only; historical hash not recomputed'})
 for kind in ['PointClouds','Odometry']:
  directory=data/'raw'/kind/s; fs=sorted(directory.glob('*'))
  inv.append({'path':str(directory.relative_to(ROOT)),'files':len(fs),'bytes':sum(x.stat().st_size for x in fs),'verification':'stat only'})
  if kind=='Odometry':
   for p in fs:
    with p.open() as f:rd=csv.DictReader(f);rr=list(rd)
    twists={k:{'finite':all(__import__('math').isfinite(float(r[k])) for r in rr),'min':min(float(r[k]) for r in rr),'max':max(float(r[k]) for r in rr),'distinct':len({r[k] for r in rr})} for k in rd.fieldnames if k.startswith('field.twist.twist.')}
    odom.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rows':len(rr),'columns':rd.fieldnames,'twist':twists})
  else:
   for stream in ['003','004','laser','top','dome']:
    candidates=[p for p in fs if p.name.startswith(stream+'_')]
    if candidates:
     p=candidates[0]
     with p.open('rb') as f:
      lines=[]
      for _ in range(32):
       line=f.readline(4096).decode('ascii');lines.append(line)
       if line.startswith('DATA'):break
     headers.append({'path':str(p.relative_to(ROOT)),'inspection':'header only, body not opened/hash not recomputed','header':''.join(lines)})
 inv.append({'path':str((data/'raw/labels'/s).relative_to(ROOT)),'exists':(data/'raw/labels'/s).exists(),'verification':'existence only'})
dump('local_dataset_inventory.json',inv);dump('odometry_recheck.json',odom);dump('pcd_header_samples.json',headers)
# Copy selected small original evidence with original-path and source-hash map; never bulk data.
selected=['configs/replay_evaluation.json','configs/segment_roles.json','pyproject.toml',
 'planning/evidence_audit.md','planning/sources.md','planning/dataset_field_matrix.md',
 'artifacts/20261012T134149Z-R05/gate.md','artifacts/20261012T134149Z-R05/notebook_execution.json',
 'artifacts/20261012T134149Z-R05/environment_final.json','artifacts/20261012T134149Z-R05/implementation_correction_clock_availability.json',
 'artifacts/20261012T134149Z-R05/T_R05_sessions.csv','artifacts/20261012T134149Z-R05/test_final.log',
 'artifacts/20261017T190338Z-R05-review/README.md']
copyindex=[]
for rel in selected:
 p=ROOT/rel; dest=EV/'source'/rel; dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 copyindex.append({'original_path':rel,'copy':str(dest.relative_to(OUT)),'sha256':sha(p),'verification':'fresh SHA-256; contents read'})
dump('copied_source_provenance.json',copyindex)
print(json.dumps({k:v for k,v in summary.items() if k not in ['clean_primary_003','nonzero_attack_recall_003']},indent=2))
print('notebooks parsed',len(nb),'planning documents content-indexed',len(planning))
