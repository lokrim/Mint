"""Assemble the 2026-10-22 findings revision from bounded audit outputs. No project execution."""
from pathlib import Path
import json,csv,hashlib,ast,collections,re,os
ROOT=Path(__file__).resolve().parents[3]; O=ROOT/'planning/findings'; E=O/'evidence'; R='artifacts/20261012T134149Z-R05'; HEAD='14371e6bee024544678481c0976641ba495dbda6'
def readcsv(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def writecsv(p,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)
def doc(n,s): (O/n).write_text(s.strip()+'\n')
def sh(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
findings=[]
def F(i,claim,status,path,loc,verification,limits,reuse,units='',n='',d='',population='',version=None):
 findings.append(dict(finding_id=f'F{i:03}',claim=claim,status=status,source_path=path,source_locator_filter=loc,run_version=version or HEAD,verification=verification,units=units,numerator=n,denominator=d,applicable_population=population,limits=limits,reuse_decision=reuse))
F(1,'Audit baseline HEAD with untracked planning/; no applicable AGENTS.md found in checked repository/ancestor paths.','verified_current_code','.git; planning/','git status --short; rev-parse HEAD; ancestor AGENTS checks','Read-only git/status and instruction discovery','Untracked planning predates this audit; not covered by HEAD alone','Preserve; manifest working-tree evidence',population='2026-10-22 initial working tree')
F(2,'R05 final technical PASS and final artifacts exist; pending-report claims are stale.','verified_saved_result',R+'/manifest.json; '+R+'/gate.md; planning/progressplan.md; planning/checklist.md; artifacts/20261017T190338Z-R05-review/README.md','sealed_utc; technical_status; final gate; R05 status rows','Read final files; selected output hashes compared; parsed executed notebooks/JUnit','Technical completion is not scientific support; local evidence only','Use final artifacts; do not execute continuation commands',population='R05',version='sealed 2026-10-17T19:30:20.963181+00:00')
F(3,'No R06/R07 run artifacts were found; H is recorded unopened.','reported_not_reverified','planning/progressplan.md; '+R+'/manifest.json','R06/R07 rows; H_opened=false; artifact category inventory','Inspected run inventory and final manifest, not H content','Cannot prove global non-exposure; no H content opened in this audit','Retain exposure warning; defer H',population='repository-visible history')
F(4,'S03 clean observations are algebraic fixtures rather than measured sensor observations.','verified_current_code','src/valid_point/ablations.py','clean_fixture_rows','Read formula and callers; retained source excerpt','Distinct seed IDs are not independent scenes','Keep arithmetic examples; discard empirical claims',population='S03 fixtures')
F(5,'S04 reference/calibration inputs are constructed; proposal and association failures are annotations.','verified_current_code','src/valid_point/evaluation/gap.py','_reference_rows; fit_track_calibration; EvaluatorOutcome; spatial_case_fixtures','Read source: literal patterns and reference.u or u+1','No proposal-generation or association performance measured','Keep counterexamples only',population='S04')
F(6,'S04 saved tile versus oracle attack alarms are 3/7 versus 5/7, benign alarms 2/5 each.','constructed_example','artifacts/20261008T103246Z-cbed4e64/spatial_gap_result.json','cases and summaries; common-known attack 3/6 vs 5/6','Read saved JSON and fixture code','Constructed cases; includes abstention; not real detection rates','Keep narrow illustrative gap',units='case alarms',n='3;5;2;2',d='7;7;5;5',population='7 attack and 5 benign constructed cases',version='20261008T103246Z-cbed4e64')
F(7,'The S04 withheld/permuted-GT test changes unused local variables.','verified_current_code','tests/test_gt_isolation.py','test_withholding_and_permuting_evaluator_labels_leaves_gt_free_scores_identical','Read complete test and unchanged _operational_scores calls','Does not establish end-to-end isolation; does not itself prove leakage','Replace test design; preserve historical correction',population='S04 test')
F(8,'Later boundary tests exercise evaluator mutation/withholding, deny reads, prefix changes and leakage-positive controls.','verified_current_code','tests/test_replay_isolation.py; tests/test_evaluation.py; scripts/check_r03_boundary.py','test_changed_withheld_evaluator_and_positive_leakage_control; test_evaluator_withheld_changed_and_leaky_positive_control','Read tests and R03 boundary saved evidence; no fresh test execution','R05 fixture checks mostly D path without real poses; not universal leakage proof','Adapt typed/allowlisted inference boundary',population='R-stage tested paths')
F(9,'Kinematic residual has no point input; fixed pose/velocity means point-only edits cannot affect it.','analytic_limitation','src/valid_point/evidence/kinematics.py','measure_motion: norm((p1-p0)-R0*v0*dt)','Read equation and inputs; dependency analysis','Independent velocity could support motion verification, not automatically cloud correctness','Keep optional motion diagnostic',units='metres',population='point-only interventions with fixed metadata')
F(10,'Linear and angular twist columns are present, finite and variable in all 15 inspected local odometry CSVs.','verified_saved_result','planning/findings/evidence/odometry_recheck.json','all 5 segments x 3 vehicles; six field.twist.twist columns','Parsed all rows and recomputed small CSV hashes','Frame, sensor provenance, online availability and independence remain unverified','Do not repeat velocity-absent claim',units='files; rows/file',n=15,d=15,population='mini_7 and mini_10–13; 300 rows/file')
F(11,'R pipeline computes D from 32 sensor-relative horizontal cells with fixed [0,10,25,50,80) m boundaries and eight sectors.','verified_current_code','src/valid_point/evidence/density.py; src/valid_point/evaluation/real.py','count_cells; fit_references; normalize','Read full implementation','All heights; excludes radius >=80 m; origin convention conditional','Reuse counting only after geometry validation',units='points/cell/frame',population='R02–R05')
F(12,'D cannot increase under pure removal at fixed references and is invariant to exact per-cell-count-preserving changes.','analytic_limitation','src/valid_point/evaluation/real.py; src/valid_point/evidence/density.py','normalize; count_cells','Monotonicity of clip((count-u)/b), b>0, and max','Some removal may lower anomaly (raise conformity); G need not share invariance','Use as negative control; not reliability target',population='known D at fixed context')
F(13,'R05 normalization uses q95 and scale 4*(q95-q50), same-sensor fallback and all-required eligibility.','verified_current_code','src/valid_point/evaluation/real.py; src/valid_point/development_scores.py','fit_references; normalize; decide','Read support rules, sector pooling and G gap fallback','Pooled sectors add values but distinct-cloud count guards support; no guarantee of comparable distribution','Reimplement calibration for new estimand',units='D points; G metres',population='R05 fold fit')
F(14,'Clipping loses severity information; max combination can mask a changed factor and inherits intersection coverage.','analytic_limitation','src/valid_point/evaluation/real.py; src/valid_point/development_scores.py','normalize; decide','Algebraic counterexamples in methodology document','Not proof every alternative combination works','Do not inherit arbitrary score semantics',population='bounded D/G arms')
F(15,'G is q90 current-to-compensated-previous nearest voxel-centroid distance, not occupancy contradiction.','verified_current_code','src/valid_point/evidence/temporal_geometry.py','voxel_centroids; directed_novelty','Read crop, centroids, transforms, quantile direction','Removal/small affected support can be invisible; motion, disocclusion and pose error confound','Keep geometry primitive as baseline only',units='metres',population='valid causal pairs')
F(16,'A single unresolved nearest-neighbor query or work cap can abstain the entire G measurement.','verified_current_code','src/valid_point/evidence/temporal_geometry.py','_directed_distances: NEIGHBOR_SEARCH_BOUND / NEIGHBOR_WORK_BUDGET','Read exact bounded-search and chunk logic','50,000-centroid cap is approximate; cap is not a latency guarantee','Profile/replace under explicit accuracy budget',units='2 m buckets; 4 shells; 10,000,000 pairs/event',population='R03 corrected and R05 G')
F(17,'Valid current clouds become history even when anomalous; attacks can change subsequent G comparisons.','verified_current_code','src/valid_point/replay.py; tests/test_replay_isolation.py','replay history update; test_attacked_geometry_uses_attacked_prior_cloud','Read update and exercised test definition','Freezing scalar references does not prevent history contamination','Adapt with explicit threat/ablation; no clean shadow',population='same-stream replay history')
F(18,'EWMA uses elapsed time, missing holds, >0.5 s reset and warm-up; no forced post-attack recovery.','verified_current_code','src/valid_point/temporal.py; src/valid_point/evaluation/real.py','TemporalEWMA.update; score_records; VERSIONS','Read recurrence, state key, readiness, null alarm gating','Short missing gaps can bridge with elapsed weight; long gaps reset; not probability','Adapt state machine only if selected',units='seconds; dimensionless anomaly',population='memoryless; tau 1 primary and 0.25/2 sensitivities')
F(19,'R05 saved grid has 248 episodes: each fold 30 attacks, five identity, one clean and 26 benign stresses.','verified_saved_result',R+'/T_R05_attempt_flow.csv','group by segment,kind','Parsed every flow row; grid config checked','Episodes reuse four base segments; not 248 independent scenes','Keep complete factorial accounting',units='episodes',n=248,d=248,population='C0–C3',version='R05')
F(20,'Calibration statuses are 156 insufficient-known, 31 no-power and 53 available out of 240 cells.','verified_saved_result',R+'/T_R05_clean_support.csv','support_type=calibration; group status','Recounted; portable cells preserved','4 folds x 5 streams x 3 arms x 4 temporal versions','Preserve nulls and status meaning',units='calibration cells',n='156;31;53',d=240,population='R05 calibration grid',version='R05')
F(21,'Of 31 NO_POWER cells, 21 have threshold 1 and ten threshold 0; the latter can alarm on future positive scores.','analytic_limitation',R+'/T_R05_clean_support.csv; src/valid_point/evaluation/real.py','calibrate; score_records; status=NO_POWER','Recounted thresholds; inspected strict alarm comparison','NO_POWER label conflates constant-zero calibration and impossible-to-exceed bound; unused metrics.threshold_power differs too','Separate support, degeneracy and mathematical impossibility',units='cells',n='21;10',d=31,population='R05',version='R05')
F(22,'Sender 003 clean D-only memoryless alarms are 29/999; all 29 occur in C1 (29/249).','verified_saved_result',R+'/T_R05_grouped.csv; '+R+'/T_R05_metrics.csv','kind=clean,sensor=003,arm=D-only,version=memoryless,metric=eligible_fpr','Reconciled CSVs; independently traced eight saved clean/addition score streams','Conditional event FPR; no independent-scene confidence bound','Keep counterexample to promised 1% future FPR',units='eligible event alarms',n=29,d=999,population='four clean sender streams',version='R05')
F(23,'For sender 003, nonzero all-attempt attack recall occurs only in eight addition/arm/version/schedule cells.','verified_saved_result',R+'/T_R05_grouped.csv','kind=attack,sensor=003,metric=all_attempt_recall,micro_numerator>0','Scanned complete grid; all grouped counts reconciled','Not evidence geometric methods cannot work; many arms cannot alarm','Preserve entire grid',units='positive cells',n=8,d=360,population='30 attacks x 3 arms x 4 versions',version='R05')
F(24,'Sustained 0.2 addition D-only memoryless alarms are 199/399; segment counts 0/99,99/99,100/100,0/101.','verified_saved_result',R+'/T_R05_metrics.csv; '+R+'/predictions','family=addition,severity=0.2,schedule=sustained,sensor=003,arm=D-only,version=memoryless,metric=all_attempt_recall','Recomputed from selected compact scores and attempt ledger joins','Alarms require reader-valid realized change; detection of perturbation is not task correctness','Keep scoped observation',units='scheduled event alarms',n=199,d=399,population='C0,C1,C2,C3 sender events',version='R05')
F(25,'003 G-only/max arms have zero clean alarm eligibility; memoryless calibration known counts are 181,180,199,116 (<200).','verified_saved_result',R+'/T_R05_clean_support.csv; '+R+'/T_R05_grouped.csv','sensor=003, arms G-only/max(D,G); F0–F3 memoryless','Read all cells and clean raw reasons','Raw G exists on many events; inability to calibrate is not zero geometric response','Diagnose coverage before effectiveness',units='known calibration scores',n='181;180;199;116',d='249;250;250;250',population='F0–F3 calibration segments',version='R05')
F(26,'All five attack families have 1,683 reader-valid scheduled events, no full injection failures or zero-realized events; rearrangement has partial failed moves.','verified_saved_result',R+'/evaluator','all 244 non-clean attempts.jsonl.gz; kind=attack','Streamed compact attempt ledgers; counted by kind/family','64,852/110,297,088 intended rearrangement row moves fail; all 1,683 rearrangement events partially constrained; row opportunities repeat scenes','Retain intended/injected/realized distinction',units='events; row-move opportunities',n='1683 each;64852',d='1683 each;110297088',population='R05 attacks',version='R05')
F(27,'D-only memoryless conformity paired effects are exactly zero for localized removal and within-cell rearrangement in all 24 cells per family.','verified_saved_result',R+'/T_R05_paired_effects.csv','sensor=003,arm=D-only,version=memoryless,field=C','Parsed all paired rows; random removal range +0.0059004 to +0.460390','24 cells=4 segments x3 severities x2 schedules; known-pair means, not independent samples','Keep metric-objective counterexample',units='dimensionless paired mean C change',n=24,d=24,population='each named family',version='R05')
F(28,'Honest-companion predictions are unchanged by attacked sender in saved integrity rows; clean companions still alarm.','verified_saved_result',R+'/T_R05_integrity.csv; '+R+'/T_R05_grouped.csv','all integrity pass rows; clean eligible_fpr each sensor','Parsed integrity rows and complete clean control grid; no full independent prediction replay','Self-stream factors explain invariance; it is not preservation of downstream viewpoint utility','Keep invariant test; add task utility metric',units='integrity rows',n=248,d=248,population='R05 episodes',version='R05')
F(29,'Saved interval delay statuses: 21 detected, 519 censored no detection, 1,620 no eligible alarm out of 2,160.','verified_saved_result',R+'/T_R05_episode_outcomes.csv','JSON delay.status, all rows','Parsed JSON status fields; inspected metric code','Intervals x arms x versions are dependent; 20 recovered interval records, one censored after alarm; final_recovery separate','Preserve censoring; do not average only detections',units='interval-arm-version rows',n='21;519;1620',d=2160,population='R05 sender attack intervals',version='R05')
F(30,'R05 has resource cap interruption, three FileExistsError restarts, six prediction snapshots and later reporting repairs.','verified_saved_result',R+'/failure_20261013T072953Z.json; '+R+'/manifest.json; artifacts/20261017T190338Z-R05-review/README.md','failure files; prediction_implementation_snapshots; review repair notes','Read files, snapshot source hashes, source correction','Snapshot identity per episode not fully certified here; preserving bytes is not one-version execution proof','Preserve failure provenance and checkpoint discipline',population='R05 execution',version='R05')
F(31,'Clock-skew helper was corrected to preserve availability; later audit reports no future original pose use.','reported_not_reverified',R+'/implementation_correction_clock_availability.json; artifacts/20261017T190338Z-R05-review/audit.json','clock correction; raw-record audit','Current alignment_poses and test read; historic full-row assertion read, not repeated across all 309,752 rows','Correction note alone cannot certify every snapshot; source time and availability differ','Keep dual-clock boundary and negative-skew test',population='R05 benign clock stresses')
F(32,'Finalization peak RSS 179,617,792 bytes is the finalizer process, not historical replay peak or deployment benchmark.','verified_saved_result',R+'/environment_final.json; src/valid_point/evaluation/statistics.py','peak_rss_bytes; finalize_run getrusage(RUSAGE_SELF)','Read measurement site and saved environment','Child notebook memory and earlier replay processes excluded; platform unit semantics matter','Do not use as hardware sizing result',units='bytes',n=179617792,population='macOS finalization process',version='R05 final')
F(33,'Local revision has extracted clouds and odometry for mini_7 and mini_10–13; expected raw/labels directories absent.','verified_saved_result','planning/findings/evidence/local_dataset_inventory.json','allowlisted segment paths and stat sizes','Fresh stat/existence check; 25 PCD headers only, 15 full small odometry files','No raw cloud body validation or archive rehash; no label bodies inspected','Keep data provenance; labels require compatible extraction later',units='PCD files',n=6246,population='five allowed local segments')
F(34,'Historical archive member inventories contain label TXT files: 290,291,290,289,290 for mini_7,10,11,12,13.','verified_saved_result','artifacts/20261008T192922Z-R01/safe_member_inventory.json; data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91/manifests','kind=file,path starts labels/','Parsed inventories, not TAR contents','Inventory assertion not fresh archive verification or annotation quality validation','Reject dataset-has-no-GT claim',units='listed label members',n='290;291;290;289;290',population='listed archives')
F(35,'Five streams map to four physical principals; top/dome share RSU.','verified_current_code','src/valid_point/io/mixed_signals.py','STREAM_PRINCIPAL','Read mapping and pinned/source card provenance','Identity strings are not authentication or independent observer proof','Keep explicit stream/principal mapping',units='streams/principals',n=5,d=4,population='Mixed Signals adapter')
F(36,'Timestamp parser left-pads short nanoseconds; causal pose selector checks source and availability; transforms preserve paired vehicle z offsets.','verified_current_code','src/valid_point/io/mixed_signals.py; src/valid_point/replay.py','parse_stamp; pose_matrix; raw_to_top; _select_pose; _frame','Read full adapter and tests; sampled headers and actual CSVs','Inverse round trips do not certify physical alignment, origin or deskew; source times asynchronous','Adapt explicit coordinate/time contract',population='local release adapter')
F(37,'No operational learned encoder, detector/fusion backbone, or GT object detection evaluation was found in current package/scripts/configs.','not_implemented','src/valid_point; scripts; configs; pyproject.toml','module/AST imports and function inventory; scoring call graph','Content inspection and keyword/dependency search, not README inference','External primary sources may offer models; none validated here','New feature/model/label path required',population='current repository implementation')
F(38,'Verified XYZ endpoints do not establish all emitted beams, no-return events, physical 3D origins or deskew timing.','unresolved','planning/dataset_field_matrix.md; planning/findings/evidence/pcd_header_samples.json; src/valid_point/io/mixed_signals.py','FIELDS x y z intensity; frame convention; VIEWPOINT','Header samples and contract inspection','Approximate endpoint rays possible only with justified origin; latent features do not expose rays','Gate ray candidate on independent evidence feasibility',population='inspected local inputs')
F(39,'Old data exposure persists: mini_7 development, mini_10–13 fit/calibration/test across folds; sessions unverified independent.','verified_saved_result','configs/segment_roles.json; '+R+'/T_R05_sessions.csv','folds F0–F3; all sessions','Read splits, time ranges and saved session qualification','Renaming project does not restore untouched status; cross-fold fit overlap','Use as exposed development; freeze new evaluation policy',population='old study data')
F(40,'R05 notebooks mainly validate seals, preview records/tables and display existing figures; they do not recompute perception.','verified_current_code','notebooks/R05_segment_timelines.ipynb; notebooks/R05_grouped_evaluation.ipynb','cells 1–7; executed counterparts','Parsed every code/output cell; no execution','Fresh execution validates display path, not independent end-to-end experiment','Adapt explanatory notebook structure; expand substantive computation',population='five R05 executed notebooks')
F(41,'R03 interrupted expensive unbounded neighbor work and corrected invalid outside-cell rearrangement before final gate.','verified_saved_result','artifacts/20261010T152207Z-R03/failure.txt; artifacts/20261010T155346Z-R03/gate.md; scripts/repair_r03_rearrangement.py','failure; protocol_deviation; corrected constraints','Read failures, repair script and later gate','Repair timings not instrumented separately; invalid first result remains historical','Keep corrected generator and negative test',population='R03 development')
F(42,'Stored final R05 test report records 134 passing tests; no fresh test suite was run for this extraction.','verified_saved_result',R+'/test_results_final.xml; '+R+'/test_final.log','testsuite attributes; final log','Parsed JUnit and compared final manifest hash','Tests establish specified engineering behavior only','Reuse selected tests with new semantics',units='tests',n=134,d=134,population='stored final R05 suite',version='R05 final')
F(43,'No downstream correctness, feature usefulness, object AP, honest unique-view utility or fusion improvement is established by D/G tables.','analytic_limitation','src/valid_point/evaluation/metrics.py; src/valid_point/evaluation/statistics.py','event_metrics; summarize_episode; paired fields A,C,score','Read evaluated labels/targets and absence of detector integration','Scheduled perturbation is not GT harmfulness or intent','Require task-level GT and honest-view evaluation',population='S/R evidence')
F(44,'Support/traversal evidence is an unvalidated informal idea supplied by the user’s colleague, not SVM or a novelty claim.','hypothesis','planning/findings/07_literature_questions_and_candidate_methods.md','candidate support/traversal row; user brief restated','Preserved attribution without invented identity','Boxes are not solid; missing returns not free space; independence and timing required','Defer selection pending literature and observability',population='new study candidate')
F(45,'New study should evaluate per-time feature/region/object reliability with GT permitted in training/development/evaluation and excluded from hidden deployment inputs.','hypothesis','planning/findings/06_requirements_for_the_new_study.md','requirements N01–N12','Translated user objective and missing evidence into acceptance checks','Proposed requirements do not validate a method or select a winner','Use as next planning contract',population='new project')
F(46,'All 12,240 grouped CSV rows reconcile with 48,960 segment metric rows for sums, micro and defined-segment macro.','verified_saved_result',R+'/T_R05_grouped.csv; '+R+'/T_R05_metrics.csv','all rows, eight-key grouping','Independent standard-library aggregation with assertions in audit_extract.py','Checks reporting consistency, not raw replay scientific validity','Keep reproducible summary checks',units='grouped rows',n=12240,d=12240,population='R05 report grid')
F(47,'65 selected source/output/score-stream hashes match the R05 manifest or prediction seal.','verified_saved_result','planning/findings/evidence/saved_record_checks.json','hash_checks','Fresh SHA-256 on selected files; includes all 33 current package files listed by manifest','Not all 748 predictions, raw clouds or large archives rehashed; historical assertions kept separate','Use scoped integrity evidence',units='hash checks',n=65,d=65,population='explicit paths in hash_checks')
F(48,'The pinned HF card could not be freshly retrieved; current primary card documents TXT labels, top-frame boxes and CC BY-NC-SA 4.0.','reported_not_reverified','planning/sources.md; https://huggingface.co/datasets/sberrio/Mixed-Signals-V2X','historic pinned card; current card schema/license','Current card verified via web 2026-10-22; pinned URL inaccessible in browser tool','Current card is not proof of old archive byte compatibility; no legal interpretation','Retain pinned provenance; verify release and license before migration',population='dataset documentation')
F(49,'Current source agrees with all 33 R05 final-manifest package source hashes; earlier prediction snapshots differ.','verified_saved_result',R+'/manifest.json; '+R+'/implementation_predict_*','source_sha256; six snapshot directories','Recomputed final current source hashes; inspected snapshot real.py hashes and changes','Final source agreement does not prove every prediction used final source','Keep snapshot-specific provenance',units='package source hashes',n=33,d=33,population='current src/valid_point')
F(50,'D-only clean FPR differs across sensors and EWMA does not uniformly lower false alarms.','verified_saved_result',R+'/T_R05_grouped.csv','kind=clean,metric=eligible_fpr; all sensors; memoryless/EWMA','Reconciled complete clean grid','Different eligible populations/thresholds; no causal universal comparison','Keep separate coverage and common-support evaluation',population='C0–C3 clean controls')
writecsv(O/'evidence_ledger.csv',findings)
# Portable source excerpts selected by named function/class with exact line ranges and whole-file hashes.
selections={'src/valid_point/ablations.py':['clean_fixture_rows'], 'src/valid_point/evaluation/gap.py':['_reference_rows','fit_track_calibration'], 'src/valid_point/evaluation/real.py':['fit_references','normalize','score_records','calibrate','alignment_poses'], 'src/valid_point/development_scores.py':['decide'],'src/valid_point/evidence/kinematics.py':['measure_motion'],'src/valid_point/evidence/density.py':['count_cells'],'src/valid_point/evidence/temporal_geometry.py':['_directed_distances','directed_novelty'],'src/valid_point/replay.py':['_select_pose','replay'],'src/valid_point/temporal.py':['TemporalEWMA'],'src/valid_point/evaluation/metrics.py':['event_metrics','episode_metrics'],'src/valid_point/evaluation/statistics.py':['grouped_rates','final_recovery'],'tests/test_gt_isolation.py':['test_withholding_and_permuting_evaluator_labels_leaves_gt_free_scores_identical'],'tests/test_evaluation.py':['test_evaluator_withheld_changed_and_leaky_positive_control']}
parts=['# Selected source excerpts\n\nThese are evidence, not a runnable migrated implementation. Original paths are repository-relative; hashes are fresh SHA-256 of the entire original file.']
for path,names in selections.items():
 text=(ROOT/path).read_text();lines=text.splitlines();tree=ast.parse(text)
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names:
   parts.append(f'\n## {path}::{node.name}\n\nOriginal lines {node.lineno}–{node.end_lineno}; file SHA-256 `{sh(ROOT/path)}`.\n\n```python\n'+ '\n'.join(f'{i+1:4} {lines[i]}' for i in range(node.lineno-1,node.end_lineno))+'\n```')
(E/'source_excerpts.md').write_text('\n'.join(parts)+'\n')
doc('README.md', '''# Valid Point: evidence handoff

Current revision: **2026-10-22, revision 1**, Asia/Kolkata. No previous `planning/findings/` package existed. This package retires the old direction; it authorizes no experiment, later stage, download or replacement implementation. Repository baseline: `14371e6bee024544678481c0976641ba495dbda6`; `planning/` was already untracked. Working-tree sources, not HEAD alone, define the audited evidence. [F001]

**Actual terminal state:** R05 has a final technical PASS, saved result tables/figures, five executed notebooks and a stored 134-test passing suite. The manifest was sealed at 2026-10-17 19:30:20.963181 UTC, **18 October 2026 01:00:20.963181 IST**. `planning/progressplan.md`, `planning/checklist.md`, history H020 and the R05 review README incorrectly still say reporting/GR5 is pending. Do not run their continuation commands. No R06/R07 execution was found; H is recorded unopened and its content was excluded from this audit. [F002–F003, F042]

The strongest retained result is a bounded, inspectable real-cloud replay, with deterministic intervention ledgers and explicit unknowns. The central failure is a mismatch with the new objective: it measures sender-stream count surplus and temporal novelty, not individual feature correctness or downstream usefulness. Early S03/S04 detection examples are constructed fixtures. Later R-stage isolation tests materially improve the engineering boundary, but cannot supply missing task-level validation. [F004–F018, F037, F043]

R05 has 248 dependent episodes on four exposed comparison segments. Of 240 calibration cells, 156 lack sufficient known scores, 31 are tagged `NO_POWER`, and 53 are available. For sender `003`, nonzero all-attempt recall occurs only in some addition cases; G-only/max arms cannot produce calibrated alarms. D-only memoryless clean alarms are 29/999; sustained 20% addition yields 199/399, with large segment variation. These are scoped table results, not universal rates. [F019–F029]

Reuse strict I/O, explicit clocks/frames, causal boundaries, deterministic overlays, intended/injected/realized records, pairing and provenance **after adaptation and validation**. Do not inherit arbitrary scoring constants, clean-only learning restrictions, sender reputation semantics, fixture-based scientific claims, independence assumptions, or the old Python environment. D/G tables are neither latent features nor reliability labels. A colleague’s support/traversal idea remains an informal hypothesis; primary-literature review and observable-input checks come first. [F035–F045]

## Reading order and package map

1. [Portable handoff](09_portable_handoff.md) — standalone entry point for another environment.
2. [History and actual state](01_project_history_and_actual_state.md) — chronology and contradiction register.
3. [Methodology and failures](02_methodology_and_failure_analysis.md) — equations, dependencies and repaired/unrepaired limitations.
4. [Dataset, GT and feature feasibility](03_dataset_ground_truth_and_feature_feasibility.md) — exact inventory and ray prerequisites.
5. [Experiments and verified results](04_experiments_and_verified_results.md) — complete grid, denominators and negative evidence.
6. [Reusable assets and migration](05_reusable_assets_and_migration_spec.md) — contracts and validation checks.
7. [New study requirements](06_requirements_for_the_new_study.md) — testable obligations, not a chosen method.
8. [Literature questions and candidates](07_literature_questions_and_candidate_methods.md) — verified leads, explicit unread/full-review status.
9. [Reproducibility and notebooks](08_reproducibility_resources_and_notebook_lessons.md) — resource scope, failures and notebook lessons.

Machine-readable companions: [finding ledger](evidence_ledger.csv), [asset inventory](asset_inventory.csv), [results summary](results_summary.csv), [audit scope](audit_scope.json), [evidence manifest](evidence_manifest.json). [Evidence guide](evidence/README.md) explains portable excerpts and reproducible scripts. Every F-ID resolves to an exact claim, locator/filter, version, verification, population, units/denominator where relevant, limitation and reuse decision in the ledger. Bracketed F-IDs in prose are cross-references, not external citations.

## Evidence vocabulary

| Status | Meaning |
|---|---|
| `verified_current_code` | Directly inspected current implementation; does not assert runtime efficacy. |
| `verified_saved_result` | Parsed/reconciled existing records; verification scope is specified. |
| `reported_not_reverified` | Historical/source assertion retained without repeating the underlying check. |
| `analytic_limitation` | Consequence of inspected equations or missing evaluation link. |
| `constructed_example` | Deliberate toy/fixture, never a population estimate. |
| `hypothesis` | Proposed idea or acceptance requirement, unvalidated. |
| `contradicted` | An old assertion conflicts with stronger evidence; see contradiction register. |
| `not_implemented` | No implementation found in the audited scope. |
| `unresolved` | Evidence remains insufficient to decide. |

This is a **bounded category audit**, not a fresh full integrity audit. It combines close reading of critical planning/code, content scans of all planning/prompts and source definitions, parsed notebook cells/stored text/error outputs, complete R05 table arithmetic, selected compact-record traces, small-file hashes and allowlisted local input inspection. Large raw bodies/archives, holdout content, sibling repositories, environment internals and full visual rendering of old figures were excluded. Exact depth and exclusions are recorded, including where only inventory or historical assertions were used. No tests, training, replay or notebooks were executed. [F046–F049]
''')
doc('01_project_history_and_actual_state.md', '''# History and actual state

Read F001–F010, F019, F030–F043 and F049 in the [ledger](evidence_ledger.csv) alongside this narrative. “Implemented,” “executed,” and “supported” are deliberately different predicates.

## Trajectory

The archived October contract asked whether ground-truth-free **sender/frame conformity** could detect specified corruptions and later guide byte quotas while retaining honest viewpoints. Mandatory kinematic/spatial factors, oracle boxes, consensus and future bandwidth policy occupied much of the plan. Even that contract cautioned that conformity was not honesty or usefulness. Source: `planning/archive/2026-10-08-pre-replan/01_research_contract.md`, sections Question, Decision and Allowed claims. These were intentions, not completed downstream results.

| Stage | Code/intention | Executed evidence and credited scope |
|---|---|---|
| S00 | Environment, provenance, fresh kernels | Infrastructure gates and notebooks; no research outcome. |
| S01 | Seeded geometry/contracts | One toy template and coordinate round trips; seeds do not yield independent real scenes. |
| S02 | Kinematics, half-open counts, availability | Hand-calculated residuals and absent/empty/late cases. Useful arithmetic tests, not attack detection estimates. |
| S03 | Quantile references, max scores, calibration | `clean_fixture_rows` emits seed/frame arithmetic, not raw sensor measurements. Later source/artifact labels say illustrative. |
| S04 | Fixed-grid versus oracle box counts | Twelve constructed comparisons; proposal/association states are labels. Constant `technical=PASS` and `G3=FAIL_NEGATIVE_RESULT` do not estimate viability. |
| S05–S10 | Consensus, bandwidth, overlays, evaluation, real data, paper | Historical prompts; not completed as that chain. Superseded by October replan. Do not execute. |
| R01 | Real data feasibility | `20261008T192922Z-R01`: small mini_7 intake, schema/timing/geometry evidence; source notebook contains stored outputs. |
| R02 | Causal raw D/G path | `20261009T085704Z-R02`: real raw counts/geometry and boundary checks. Later `20261012T043451Z-R02` is another saved development run, not a new independent scene. |
| R03 | Overlays, temporal state | `20261010T155346Z-R03`: corrected development demonstration; threshold support insufficient, alarms null. Prior interrupted and invalid rearrangement attempts preserved. |
| R04 | Protocol freeze | Authoritative `20261010T211551Z-R04-80694538e854`; earlier seals superseded after exact lineage/group-resample fixes. No test-data efficacy from a freeze. |
| R05 | Four comparison folds | `20261012T134149Z-R05`: final manifest, full tables, five executed notebooks, final technical PASS. Conditional descriptive results in [04](04_experiments_and_verified_results.md). |
| R06/R07 | Final H check / paper evidence | Prompts and plan only; no run evidence found. H content excluded; historical unopened assertion is not a global access proof. |

Sources for stage populations and saved gates: [run status extracts](evidence/run_status_and_failures.json), [notebook cells](evidence/notebook_cells.json), [planning content index](evidence/planning_content_index.json). Stage-specific source versions are recorded in old manifests; the handoff hashes current source and selected evidence, without asserting all historic code matched HEAD.

The 8 October replan replaced the mandatory K/S/oracle/quota chain with causal **real-cloud** interventions and D/G trajectories. It explicitly deferred detector/AP, learned fusion and bandwidth. That was a real improvement in measurement provenance, but narrowed the question away from task usefulness. The new project’s individual feature/region/object evidence is a further change of estimand, not a renamed sender score. [F011–F018, F037, F043]

## Contradiction register

| Old claim / location | Conflicting evidence | Resolution and remaining uncertainty |
|---|---|---|
| R05 reporting, notebooks and GR5 absent: progressplan R05 row, checklist, history H020, review README | Final CSVs, manifest, notebook execution JSON, JUnit and gate [F002] | **Contradicted as current state**. Final seal is 18 October IST. Preserve stale documents; do not rerun obsolete commands. |
| Root README/setup language implies no algorithms or future-only intake | Actual source and S/R artifacts | Historical setup descriptions only. Source and dated run artifacts govern present claims. |
| S03 distinct seeds/segments support clean empirical calibration | Arithmetic `clean_fixture_rows` [F004] | **Contradicted** as empirical scene independence. Bookkeeping and quantile arithmetic remain useful. |
| S04 demonstrates measured proposal/association failure and complete GT isolation | Annotated `EvaluatorOutcome`; test modifies unused locals [F005,F007] | Retracted by `planning/evidence_audit.md`; retain constructed count examples. Later R tests assessed separately. |
| No real replay exists: 8 October audit | R01–R05 later artifacts | True at that audit date, stale today. Do not extend early audit’s absence claim to later stages. |
| Velocity absent/unavailable because old reader does not consume it | Local finite variable twist columns [F010] | Blanket absence inference rejected. Frame/provenance/independence unresolved; K still point-insensitive. |
| All `NO_POWER` means no future alarm possible | Ten constant-zero calibration cells, strict score > 0 rule [F021] | Label is overbroad. Threshold 1 on bounded score cannot alarm; threshold 0 can. No old result rewritten. |
| Comparison TARs absent/resource blocked: H018/prerequisite run | Current explicit archive stats and later resource amendment/intake | Historical absence not current absence. Acquisition history outside records unresolved. No reacquisition performed. |
| Labels absent in extracted directory means no GT | Saved TAR inventories contain label members [F033–F034] | Absence of extracted/consumed annotations does not imply dataset lacks labels. Body semantics/quality not checked here. |
| Finalizer peak RSS measures replay/deployment | `getrusage(RUSAGE_SELF)` in finalization [F032] | Only that process at that time. Historical replay peak and target deployment cost unresolved. |
| Same sync ID means same time / top+dome are separate agents | Explicit acquisition stamps; shared RSU mapping [F035–F036] | Preserve asynchronous stamps and four principals. Physical clock accuracy remains unknown. |

## Repair versus unresolved validity

Engineering repairs include S03 tied-factor `K+S` handling; R02 removal of unnecessary pose dependency for native XY D; R03 bounded neighbor work and per-cell rearrangement constraints; R04 numerator exclusion of failed/zero-realized injections, exact split lineage and repeated bootstrap-group IDs; R05 clock availability, Finder-metadata seal handling and episode-order reconstruction. Each has source/tests or saved failure evidence. They should not be repeated as if still uncorrected. [F008,F026,F030–F031,F041]

R05 preserves six prediction snapshots. The final current package matches its 33 recorded source hashes, while earlier orchestration snapshots differ. The prior review reports all 748 scientific prediction hashes and 309,752 raw-record checks passing; this extraction rechecks a **selected 65 hash comparisons**, complete table arithmetic and eight important score streams, not the whole claim. No generic corruption claim follows from Finder changes; no one-version execution guarantee follows from the final manifest. [F047–F049]

The project is scientifically limited rather than uniformly invalid. Exact arithmetic, strict decoding, deterministic perturbations, causal selection and saved negative comparisons survive. Generalization, feature reliability, object correctness, independent corroboration and fusion utility do not. [F043]
''')
doc('02_methodology_and_failure_analysis.md', '''# Actual methodology and failure mechanisms

All equations below reconstruct inspected code, not a proposed replacement. Exact named functions and line-numbered excerpts are in [source excerpts](evidence/source_excerpts.md); claims and populations are in [ledger](evidence_ledger.csv), F004–F018, F020–F029 and F043.

## Dependency graph

```text
PCD bytes -> strict ASCII float32 reader -> finite XYZ
   | -> sensor identity + fixed origin XY -> 32 counts n_j -> D references -> D
   | -> voxel centroids + current causal pose
   |       + previous eligible cloud/pose FROM SAME REPLAY -> directed G -> G references
   |                                                                  |
   +----------------------------------------------------> all-required arm A
                                                                     |
                                                        per-arm/time-version EWMA
                                                                     |
                                       independent clean calibration threshold -> alarm/null

pose pair + prior velocity (+ prior orientation) -> K diagnostic [not primary R score]
evaluator: schedules, clean counterpart, changed-row ledger -> OFFLINE metrics only
No learned encoder -> no intermediate feature tensor -> no detector/fusion -> no GT task metric
```

Pose/calibration provide alignment assumptions, not independent evidence of scene truth. Other streams are replayed but D/G score each stream from itself; companion invariance is structurally expected. R05’s trusted arrival equals source time and pose availability equals recorded pose stamp are modeled, not measured network facts. [F009,F028,F036–F038]

## K: motion self-consistency

`measure_motion` selects the latest two eligible samples, takes prior velocity, rotates it into the position frame when needed, and returns

`K_raw = ||(p1-p0) - R0 v0 (t1-t0)||_2` metres.

Point clouds are absent from the function signature. Alter every point while retaining pose/velocity and K remains identical. Choosing `v0=R0^-1(p1-p0)/dt` from the very displacement under test makes the residual identically zero: a constructed tautology, not independent validation. Earlier-interval pose differences avoid that exact identity but still share pose errors and measure trajectory smoothness. Legitimate acceleration can raise the residual. Same-sender consistent spoofed pose/velocity can pass. Variable local twist exists, but neither its independence nor frame/online latency is established. Excluding K from R primary scoring repairs the earlier dependency mismatch; it does not solve geometric reliability. [F009–F010]

## D: count surplus and normalization

`count_cells` uses radius in native horizontal XY relative to a declared origin, half-open radial bands `[0,10),[10,25),[25,50),[50,80)` m, eight 45° sectors and all finite heights. It records excluded points; no surface, ray or object identity is represented. For each sensor-cell, reference fitting computes linear empirical quantiles:

`u_j=q95(n_j); b_j=4(q95(n_j)-q50(n_j)); a_j=clip((n_j-u_j)/b_j,0,1); D=max_j a_j`.

R05 requires at least 200 distinct clean clouds across both declared reference segments and positive scale. Unsupported cell references fall back only to same-sensor, same-range sector-pooled distributions. Pooled observations count eight sector values per cloud, while support counts distinct clouds. G has sensor-gap contexts and sensor-wide fallback. No cross-sensor fallback is implemented. All 32 D cells must normalize; otherwise D is unknown. [F011,F013]

**Removal blind spot (analytic):** with fixed references, removing points makes every count nonincreasing, therefore D cannot increase. Removing all points from a supported present cloud can yield D=0, even if the lost objects matter. Absence/malformed input instead yields unknown. Rearranging points within each cell leaves D exactly unchanged even if object geometry is destroyed. Moving outside the crop or adding below reference tails can also be invisible. These are properties of this score, not software errors. Saved R05 localized removal and constrained rearrangement have zero paired D conformity change in every corresponding segment/severity/schedule cell. [F012,F027]

**Benign confounding:** legitimate traffic density, crop crossings and sampling changes can raise counts. R03 benign noise raises anomaly in its development demonstration; R05 clean D-only sender `003` alarms 29/999, concentrated in C1. Calling this score “reliability” would not distinguish a correct rare viewpoint from malicious surplus. [F022,F043]

**Scale/quantile degeneracy:** constant reference values produce b=0; an ad hoc epsilon would convert ordinary small changes into arbitrary large scores. The code uses fallback/unknown instead, which is safer arithmetic but changes the effective baseline and coverage. For b>0, all counts <=u map to zero and all counts >=u+b map to one. Constructed example: u=10,b=4 maps n=10 to 0, n=12 to .5 and both n=14 and n=100 to 1. The loss of magnitude is real by construction. R05’s 800 reference contexts contain 712 `SUPPORTED`, 40 `LOW_SUPPORT`, 48 `ZERO_SCALE`; these are context counts, not independent observations. [F013–F014; numeric_audit.json]

## G: directed novelty, support and computational abstention

Crop each cloud at horizontal radius <80 m, voxelize at 0.5 m, represent occupied voxels by centroids, and deterministically cap at 50,000 centroids by lexicographic-index spacing. Transform previous centroids into the current coordinate convention using `inv(T_map_current) @ T_map_previous`. If both have >=100 occupied voxels and 0<gap<=0.5 s, compute

`G_raw = q90({ min_{y in previous_compensated} ||x-y|| : x in current_centroids })` metres,

then the same q95/scale/clipping normalization. Centroid cap/downsampling is reported as approximation. Ego-motion compensation does not deskew a scan or remove moving objects. [F015–F016]

**Direction counterexample (constructed):** if current occupied centroids are a nonempty subset of the previous set at identical positions, every directed distance is zero despite removal. This exact example holds centroid locations fixed; actual voxel centroids may move after removing rows. There is no previous-to-current free-space test. A sufficiently small changed fraction can remain below the q90 tail; finite-sample interpolation and mixed-voxel centroid shifts prevent interpreting “10%” as a universal sharp boundary. A moving car or disoccluded wall can produce novelty while being correct. [F015]

The 2 m bucket search tries Chebyshev shells 0–4 and certifies a distance only when no unsearched bucket can improve it. If even one query cannot be certified, G becomes `NEIGHBOR_SEARCH_BOUND`; exceeding 10,000,000 candidate pairs yields `NEIGHBOR_WORK_BUDGET`. Chunked distances limit temporary memory, but Python bucket loops and voxel sorting remain substantial. Extreme novelty can cause abstention instead of an alarm. In clean C0–C3 sender `003`, G is valid on 116/250,181/249,180/250,199/250 events respectively; the remaining rows are one initial-history unknown per segment and bounded-search failures. These saved raw reasons were freshly recounted. [F016,F025; saved_record_checks.json]

**History contamination:** after measuring a valid current cloud with valid transform/origin, replay caches it even if anomalous or G was unknown. A persistent fake structure can become its own reference; after an attack stops, the clean cloud is compared with attacked history. Tests explicitly demonstrate changed prior geometry changing later G. A clean shadow would be an oracle, not a deployment fix. Policy alternatives need separate calibration/coverage evaluation. [F017]

## Combination, temporal state and calibration

For D-only, G-only or max(D,G), **all required factors must be known**; `A=max(required factors)`, `C=1-A`. A high existing D can hide a G change: max(.9,.1)=max(.9,.8)=.9. Adding G to a D arm can reduce coverage to an intersection even though max cannot decrease on common numeric inputs. Separately calibrated thresholds mean there is no universal alarm ordering between arms. [F014]

EWMA keeps state by `(episode,principal,sensor,arm,reference_version)`:

`rho=exp(-dt/tau); Z_t=rho Z_prev+(1-rho)A_t; C_time=1-Z_t`.

First eligible A initializes Z. Readiness requires >=10 eligible updates and elapsed contiguous span >=3*tau. Missing A holds internal state but publishes unknown. Time since last eligible update >0.5 s resets; shorter missing gaps can be bridged using elapsed dt. Duplicate/reversed timestamps reject without ordinary update. Tau=1 s is primary; .25 and 2 s are separately calibrated sensitivities. The two-second sensitivity has fewer than 200 known calibration rows throughout this grid, so its threshold is unavailable; silence is not recovery. [F018,F020]

Each sensor/arm/version uses a separate clean calibration segment and `k=ceil((n+1)*.99)`. If n<200, threshold null; otherwise c is the kth sorted score, or 1 when k>n. Alarm is strictly `score>c`. The nominal 1% is a target, not demonstrated future FPR under correlated frames/distribution shift. With roughly 250 frames, a few upper-tail values and clipping can determine c. Two reference segments and one calibration segment do not establish independent acquisition sessions. [F020–F022,F039]

`NO_POWER` in `real.calibrate` means c>=1 **or constant calibration scores**. Ten constant-zero cells can alarm at score>0; 21 c=1 cells mathematically cannot alarm on score<=1. The separate helper `metrics.threshold_power` uses `max(scores)<=threshold`, a different criterion; it is not the R05 calibration writer. Keep these labels as saved while explaining their meanings. [F021]

## Failure classification and repair status

| Class | Evidence/mechanism | Later correction? |
|---|---|---|
| Mathematical degeneracy | b=0 and clipping; strictly bounded score at c=1 | Explicit fallback/unknown implemented; loss of information remains. |
| Objective mismatch | Counts/novelty versus individual feature or object usefulness | Not repaired; no detector/GT task path. |
| Insufficient support | Calibration nulls, short warm-up and correlated scenes | Distinct-cloud and segment guards improved; data limitation remains. |
| Benign confounding | Density, moving structure, viewpoint, pose/clock perturbations | Controls retained; cannot infer intent. |
| Unavailable inputs | Physical origins, visibility, online pose latency, independent velocity | Still unresolved. |
| Software/boundary defects | Vacuous early isolation, incorrect rearrangement, clock skew and episode IDs | Later R tests/generator/report repairs exist; preserve original failed evidence. |
| Execution/resource failures | Neighbor work, scratch cap, restart collisions, notebook dependencies | Bounds and repairs permit completed R05; deployment budget still untested. |
| Stale documentation | Pending GR5 and absent exports after final seal | Corrected in this handoff only; original documents preserved. |

Changing the word “trust” to “reliability” fixes none of the dependencies, loss of information, calibration support, independent-evidence requirements or absent task validation. A new score needs a new unit, measurable target and falsifiable link to perception correctness. [F043–F045]
''')
doc('03_dataset_ground_truth_and_feature_feasibility.md', '''# Dataset, ground truth and feature feasibility

Local root is repository-relative `data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91/`. Archives are under `archives/train/`; extracts under `raw/PointClouds/<segment>` and `raw/Odometry/<segment>`. The revision string is a recorded HF pin, not a fresh remote-revision availability claim. Full path/size evidence is [local inventory](evidence/local_dataset_inventory.json); old published hashes are in the copied [segment roles](evidence/source/configs/segment_roles.json). **No archive hash or raw cloud body hash was recomputed.** [F033,F048]

| Segment / exposure | Archive bytes (fresh stat) | Extracted PCD files / bytes | Odometry files / bytes | Label members in historical inventory |
|---|---:|---:|---:|---:|
| mini_7 / development | 7,894,272,000 | 1,250 / 6,579,185,738 | 3 / 504,842 | 290 |
| mini_10 / C0 | 7,853,803,520 | 1,250 / 6,553,645,715 | 3 / 504,331 | 291 |
| mini_11 / C1 | 7,763,056,640 | 1,246 / 6,489,308,893 | 3 / 505,692 | 290 |
| mini_12 / C2 | 7,837,788,160 | 1,250 / 6,552,436,500 | 3 / 506,375 | 289 |
| mini_13 / C3 | 7,802,398,720 | 1,250 / 6,519,880,825 | 3 / 505,970 | 290 |

These are selected extracts, not full archive coverage. Label counts come from `safe_member_inventory.json` for mini_7 and `<segment>_safe_member_inventory.json` in local manifests for comparisons. Expected `raw/labels/<segment>` directories are absent for all five inspected segments. Label bodies and TAR contents were not opened. H/mini_14 remains excluded, including its content inventory. [F033–F034]

## Input contract and epistemic status

| Quantity | Status and meaning | What remains unknown |
|---|---|---|
| XYZ/intensity PCD | **Locally inspected headers**: first sorted file per stream/allowed segment, 25 headers, ASCII float32 x/y/z/intensity. Earlier R01 report inspected 250 bodies; that body result is historical here. | No new all-body finite/count validation; intensity physical calibration. |
| Pose/twist CSV | **Locally inspected bodies**: 15 files, each 300 rows/90 columns, six finite variable twist columns; fresh hashes in `odometry_recheck.json`. | Twist coordinate frame, independent measurement, filtering and localization latency. |
| Stream/principal | **Code-derived/documented**: 003,004,laser are vehicle principals; top+dome are one RSU. | Authentication and independence of error sources. |
| Cloud timestamp | **Locally inspected filenames/code**: integer seconds*1e9 + left-padded ns field; sync ID kept separately. | Scan start/end, clock accuracy and point offsets. |
| Pose clock/selection | **Code-derived**: latest source<=event and availability<=deadline, max age 150 ms. | Actual receiver availability and online versus offline localization. |
| Arrival/deadline | **Simulated**: ideal arrival=source, deadline=event time. | Recorded network latency, packet loss, bandwidth; none established. |
| Raw frame/extrinsics | **Documented plus local compatibility checks**, not metrology. Raw RSU map convention; vehicle raw convention and paired height adjustments. | True physical laser origin/extrinsic calibration and deskew accuracy. |
| Labels | **Documented and inventory-only locally**; TXT boxes, separate release from older JSON/PKL. | Annotation quality/completeness, exact alignment for retained revision; not body-validated. |
| Visibility/beam returns | **Unknown** as an independent input. | Emitted/no-return beams, return order, occlusion truth, ring firing semantics. |
| Features/model | **Not implemented** locally. | Compatible encoder/checkpoint, exact tensor semantics and fusion interface. |

Historical R01 timing reports 147/1,495 archive filenames with short subsecond fields, and 50.603–59.893 ms same-index cross-stream skew in its selected 50-index window. These numbers are **reported_not_reverified**, sourced to `artifacts/20261008T192922Z-R01/T_R01_timing.json` and copied field matrix, not extrapolated to all segments. Different streams’ same sync ID does not make them simultaneous. [F036]

`pose_matrix` consumes quaternion **wxyz**; older generic contracts use **xyzw**, requiring explicit conversion. `TOP_FROM_MAP=(+41.551,+51.878,+1.077)` m and `DOME_FROM_MAP=(+41.507,+51.864,+1.340)` m are translations mapping raw map points to those RSU frames. Their map-frame origins are the negatives, not the positive translation vectors. Dome origin in top is `(0.044,0.014,-0.263)` m. The vehicle preprocessing shifts cloud z by −3.25 m and right-composes pose +3.25 m; the consistent composition cancels. The new adapter therefore uses the raw-to-map pose without repeating a physical mounting correction. Round trips demonstrate algebra, not physical alignment or a laser firing origin. [F036]

## Labels and release compatibility

The preserved pin/provenance says HF TXT rows use `cls cx cy cz dx dy dz yaw`, top-frame metres/radians and Vehicle/Bike/Pedestrian classes. Current [primary HF card](https://huggingface.co/datasets/sberrio/Mixed-Signals-V2X) was checked on 22 October 2026 and documents this layout and CC BY-NC-SA 4.0; the pinned card URL could not be retrieved through the browser tool. Current documentation is therefore corroboration, not proof that old archive bytes match it. The current card also describes a label crop and point-support selection; evaluate their effect on a reliability target when the precise revision is checked. [F048]

The older devkit constructor/ACFR preprocessing uses JSON/PKL annotations and generated visibility. Those are **historic primary-source observations** preserved in [sources](evidence/source/planning/sources.md), not newly validated working code/checkpoints. Do not silently copy annotations from another release or treat generated `gt_visibility` (points in GT boxes) as independent operational visibility. Missing label file differs from a present empty annotation. The next study must verify class IDs, dimensions, yaw axis, frame transform, timestamp association, completeness and any point-count filter against the exact release before computing task metrics. [F034,F043,F048]

## Genuine intermediate features require a perception pipeline

A PCD-to-array conversion is insufficient. The next planning gate needs a compatible model and usable weights, their license/source/hash, detector training domain and class mapping, exact voxel/pillar preprocessing (range, voxel size, point caps, intensity scaling), selected encoder layer, tensor shape/stride/channel meanings, coordinate anchoring, timestamp and feature alignment, compression, fusion interface and detection postprocessing. A fixed known frame should reproduce a documented detector output before adding reliability. The checkpoint must be loaded and its provenance tested in the new environment; old citations cannot certify current availability. [F037,F045]

Choose whether the reliability unit is a received spatial feature region, individual representation element, or object hypothesis supported by features. Define how labels or downstream GT error supervise/evaluate that unit without implying every latent channel is directly interpretable. Preserve clean/attacked pairing through the **same encoder**. Feature-message attacks need their own threat model; current point attacks only become feature experiments after this path exists. Keep task-supervised training allowed with grouped splits; deployment inference cannot secretly read GT, schedules or the clean alternative. [F043–F045]

Retained data can support exposed geometry development, strict-reader regression, point-to-feature extraction development and negative controls. Eventual task validation is conditional on labels/model compatibility and a new exposure-aware split. Mini_7 and C0–C3 cannot become untouched test data by renaming the project. Their independent-session status is unverified; repeated overlays and fold fits do not multiply scene independence. [F039]

## Ray reasoning: conditional feasibility, not demonstrated support

Given a defensible 3D origin o and measured endpoint p, the segment `o + λ(p-o), 0<=λ<1` is an **approximate observed ray**. Whether it contradicts proposed occupied space requires origin/pose uncertainty, time alignment, return semantics and a justified visibility/occupancy model. The retained XYZ endpoints do not reveal every emitted beam or every no-return event. Organized WIDTH/HEIGHT and a PCD VIEWPOINT field do not by themselves prove physical ring directions or firing times. [F038,F044]

A return behind a proposal may contradict an actually occupied surface region under stated assumptions. It does not establish that an entire enclosing box is solid; rays may pass through empty portions of a box or unoccupied structure. Missing returns alone are not empty-space measurements. An obscured object or honest unique viewpoint must remain unsupported/unknown rather than automatically false. Moving objects and asynchronous scans can create apparent conflicts. No per-point timing/deskew contract or independent observer coverage was established here.

A feature-only receiver cannot assume access to the sender’s raw rays. Separate three candidate information settings: (a) received features alone plus pose/time metadata; (b) features plus receiver-owned raw scans; (c) features plus communicated occupancy/ray metadata. In (c), metadata from the attacked sender may be jointly fabricated; a claimed support count is not independent evidence. In (b), no receiver coverage is not proof against an honest unique view. Establish each input’s availability and adversarial control before selecting the colleague’s candidate. [F038,F044–F045]
''')
doc('04_experiments_and_verified_results.md', '''# Experiments and verified results

All numbers here describe saved observations or deliberately constructed cases. Source R05 run is `artifacts/20261012T134149Z-R05`, frozen protocol hash `80694538e8549256934b3a314301cc8ca821efe0bf36ff4071eab9681f2c039c`. [Ledger](evidence_ledger.csv) F004–F006, F019–F029, F046–F050 and [results_summary.csv](results_summary.csv) provide filters, units and denominators. No replay was rerun.

## Earlier experiments

S01 uses one toy road template with seeded changes. S02 checks motion/count/availability arithmetic with hand inputs. S03’s source `ablations.clean_fixture_rows` directly generates residual/count values. Its saved calibration and score tables therefore test formula behavior, not independent scenes. S04 uses 400 fixed tiles and twelve constructed cases: tile attack alarms 3/7 versus oracle boxes 5/7; each has 2/5 benign alarms and one abstention. On common-known attacks, counts are 3/6 versus 5/6. These are exact saved constructed-case counts; oracle boxes and annotation strings do not imply an operational proposal detector. [F004–F007]

R01’s accepted intake selects 50 clouds per stream (250 total) from mini_7 plus three odometry CSVs. R02 accepted raw development replay reports D 250/250 and G 163/250, with 82 search-bound unknowns and five initial-history unknowns. R03 expands the development replay to 1,250 clean events over the first 25 seconds: one middle-severity sustained episode for each family, one displacement burst, noise and combined alignment/availability controls, plus five identity writer/reload checks. Its first-ten-second exploratory references require >=50 distinct cloud rows; the [10,25) diagnostic calibration block never reaches 200 known scores. Its null alarms cannot establish recall, delay or recovery. Exact saved gate evidence is preserved in [run status extracts](evidence/run_status_and_failures.json); these old cloud computations were not independently repeated. [F041]

## Frozen R05 design and full intervention population

F0 tests C0, calibrates C1, fits C2/C3; F1 tests C1, calibrates C2, fits C3/C0; F2 tests C2, calibrates C3, fits C0/C1; F3 tests C3, calibrates C0, fits C1/C2. C0–C3 are mini_10–13. Every arm sees the same named episode and time population. Sessions are not verified independent; folds share training observations. Repeated interventions are paired/dependent, not additional scenes. [F039]

| Family | Severity values and exact operation | Schedules / target |
|---|---|---|
| random_removal | 0.1,0.3,0.6 of all sender rows, floor(f*N), without replacement | Sustained [5,15) s; bursts [5,7),[10,12) s |
| localized_removal | 0.25,0.5,1 of rows in frozen target cell | Same schedules; most occupied D cell in sender’s first 3 s |
| displacement | 0.2,1,3 m in local +x, selected 25% of rows | Same schedules; total count preserved, cells may change |
| rearrangement | 0.2,1,3 m horizontal proposals, selected 25%, up to ten directions | Each accepted point remains in original valid D cell; failed moves retained |
| addition | 0.01,0.05,0.2 of current N, synthetic uniform points in 2 m cube | Frozen target-cell centroid; intensity sampled from sender values |

The primary manipulated sender is `003`; poses/timestamps and other streams are unchanged in point-attack episodes. These are digital point-cloud overlays, neither intermediate-feature attacks nor physical laser simulations. Each fold has 30 positive attacks, five family-specific zero-severity identity controls, one natural clean replay and 26 benign stresses: coordinate noise sigma .02/.1 m; assumed adapter translation .05/.2 m; yaw .2/1 degree; modeled source-clock skew −50/−10/+10/+50 ms; raw downsampling .1/.3/.6; each stress under both schedules. Primary arms are D-only, G-only, max(D,G), each memoryless or EWMA tau=1 s; sensitivities tau=.25/2 s are also saved and separately calibrated. Thus the actual tables include **four**, not merely two, temporal versions. [F019]

All 248 flow rows were parsed. Across non-clean episodes there are 17,703 scheduled attempts and 17,703 reader-valid records, with zero full injection failures. These include identity and benign controls and must not be called positive attacks. Each of five positive families has 1,683 reader-valid/nonzero-realized scheduled events. All 1,683 rearrangement events contain partial failed moves: 64,852 of 110,297,088 intended row moves remain unchanged; every recorded per-cell-count delta is zero. Row opportunities reuse scenes and are not statistical replicates. [F026; saved_record_checks.json]

## Calibration and coverage before effectiveness

Of 800 reference contexts, 712 are supported, 40 low-support and 48 zero-scale. Of 240 calibration cells (4 folds ×5 sensors ×3 arms ×4 versions), 156 are `INSUFFICIENT_KNOWN`, 31 `NO_POWER` and 53 `AVAILABLE`. `NO_POWER` splits into 21 c=1 cells and ten constant-zero c=0 cells. A c=0 cell can produce later positive alarms. Threshold availability, known score, warm-up readiness and known alarm are distinct. [F020–F021]

For sender `003`, D-only memoryless calibration is available numerically in each fold, but F0/F3 c=1 cannot alarm. G-only and max(D,G) have no available threshold in any version; memoryless known calibration counts F0–F3 are 181,180,199,116, all below 200. Tau=2 has insufficient calibration for every sensor/arm cell. The saved “common support” table intersects all three methods and all four temporal versions; this makes it empty and uninformative for this grid. It does not mean useful pairwise common-support comparisons are mathematically impossible. [F025; r05_calibration_cells.csv]

## Complete primary attack grid

Cells below are **alarm numerator / all scheduled sender attempts**, pooled across four segments. `0/d †` for G or max means no calibrated alarm eligibility, not observed clean-like evidence. D results still include c=1 and other inability-to-alarm conditions; inspect thresholds and segment rows before calling all zeros confident misses. Full four-version results, eligible/realized and episode denominators, per-segment variation and omissions are in [complete grid](evidence/r05_sender_complete_grid.csv). No family/severity/schedule is omitted.
''')
g=readcsv(ROOT/R/'T_R05_grouped.csv'); m=readcsv(ROOT/R/'T_R05_metrics.csv')
def get(**filters):return next(r for r in g if all(r[k]==str(v) for k,v in filters.items()))
lines=['\n| Family | Severity | Schedule | D memoryless | D EWMA | G memoryless / EWMA | max memoryless / EWMA |','|---|---:|---|---:|---:|---|---|']
base=[r for r in g if r['sensor']=='003' and r['kind']=='attack' and r['arm']=='D-only' and r['version']=='memoryless' and r['metric']=='all_attempt_recall']
for r in base:
 filt={k:r[k] for k in ['family','severity','schedule','sensor','kind','metric']}
 def val(arm,v):
  x=get(**filt,arm=arm,version=v);return x['micro_numerator']+'/'+x['micro_denominator']
 lines.append('| '+' | '.join([r['family'],r['severity'],r['schedule'],val('D-only','memoryless'),val('D-only','EWMA'),val('G-only','memoryless')+' † / '+val('G-only','EWMA')+' †',val('max(D,G)','memoryless')+' † / '+val('max(D,G)','EWMA')+' †'])+' |')
with (O/'04_experiments_and_verified_results.md').open('a') as f:f.write('\n'.join(lines)+'\n')
with (O/'04_experiments_and_verified_results.md').open('a') as f:f.write('''
Only eight of the 360 sender attack/arm/version/schedule cells have a positive all-attempt numerator, all D-only addition cases: .05 sustained/burst at tau=1; .2 sustained/burst memoryless, tau=1 and tau=.25. Tau=2 is unavailable. This is a complete-grid observation, not a universal attack ranking. [F023]

Sustained .2 addition D memoryless: C0 0/99, C1 99/99, C2 100/100, C3 0/101 =199/399 micro; equal-weight macro=.5. Clean D memoryless: C0 0/250, C1 29/249, C2 0/250, C3 0/250 =29/999 micro. All eight source score streams were freshly hashed against the seal and these counts independently rebuilt with compact attempt joins. [F022,F024,F047; saved_record_checks.json]

## Clean and benign controls, all sensor streams

The table gives clean eligible alarm counts, with `0/0` meaning **undefined**, never zero FPR. Sensor rows are not independent principals; top/dome share RSU. [F028,F035,F050]

| Sensor | D memoryless | D EWMA | G memoryless | G EWMA | max memoryless | max EWMA |
|---|---:|---:|---:|---:|---:|---:|
''')
with (O/'04_experiments_and_verified_results.md').open('a') as f:
 for sensor in ['003','004','laser','top','dome']:
  vals=[]
  for arm in ['D-only','G-only','max(D,G)']:
   for v in ['memoryless','EWMA']:
    r=get(kind='clean',sensor=sensor,arm=arm,version=v,metric='eligible_fpr');vals.append(r['micro_numerator']+'/'+r['micro_denominator'])
  f.write('| '+' | '.join([sensor]+vals)+' |\n')
 f.write('''
All benign stress values/schedules and all sensors/versions are preserved in [control rates](evidence/r05_all_sensor_control_rates.csv). For 003 D memoryless, coordinate noise yields 155/999 eligible alarms under sustained stress at both sigma values, and 80/999 (.02 m) or 81/999 (.1 m) under bursts. Every adapter-translation, yaw, clock-skew and downsampling control has 29/999, equal to its clean whole-episode alarm count. These denominators span **the whole episode**, not just stress windows; equality cannot prove the stressed interval is harmless. D uses native XY and ignores pose perturbation; its unchanged response is not alignment robustness. [F050; exact grouped filters in results_summary.csv]

Honest-companion invariance passes in all 248 saved integrity rows. It is expected from independent per-stream factors, not evidence that suppressing sender features would preserve useful unique viewpoints. Clean companions alarm substantially (for example 004 D memoryless 141/999, EWMA 339/877). Repeated unchanged companion traces across attacks must not be counted as fresh clean data. [F028,F050]

## Paired effects, delay and recovery

`T_R05_paired_effects.csv` reports known-pair mean attacked-minus-clean A,C,score over scheduled events, counting unknown pairs. It contains no raw D/G paired-effect field despite broader prose in the plan. For 003 D memoryless C, random removal has positive means ranging +.005900439 to +.460389828 across 24 segment/severity/schedule cells; localized removal and constrained rearrangement are exactly zero in all 24 each. Displacement ranges −.905834598 to +.021989941; addition −.994099561 to zero. A harmful edit need not lower conformity. These are per-cell means, not pooled IID effects. [F027; r05_sender_paired_effects.csv]

The 2,160 interval-arm-version outcome rows have 21 detected, 519 right-censored no detection and 1,620 no eligible alarm. Of 21 in-window alarm rows, 20 interval recoveries are recorded and one is right-censored; other 2,139 interval recovery fields are not applicable. Counts multiply dependent versions and burst intervals. `final_recovery` is the separate after-last-offset field; its repeated occurrence on burst interval rows must be deduplicated by segment/episode/arm/version before episode analysis. Full status/value fields are preserved. [F029]

Metric code uses scheduled attempted events in all-attempt denominators, but counts only alarms with reader-valid, nonzero realized change and no injection failure. Eligible recall excludes unknown alarms; realized recall conditions on realized change but retains possible unknown scores. Empty denominators remain null/status. Delay excludes a preexisting alarm; the implementation flags an entire interval preexisting if its last pre-onset event is alarmed, rather than searching for later re-onsets. Recovery needs two seconds of continuous eligible quiet, no reset or >.5 s gap; reported value is **confirmation time**, not the start of that quiet run. [F029; metrics.event_metrics/episode_metrics; statistics.final_recovery]

## Reporting discrepancies and claim limits

The CSVs reconcile arithmetically, but that is not a fresh raw-data replay. `NO_POWER` has the overbroad meaning above; prose event-recall definitions sometimes omit the actual realized-change condition; the complete-common-support intersection includes an uncalibratable tau=2; paired tables omit raw factor effects; old status documents are stale. No files were “repaired” to hide these discrepancies.

Detecting a scheduled perturbation differs from identifying incorrect objects, harmful features, malicious intent or an improvement in fusion. There is no GT object detection evaluation to decide whether the observed perturbation damaged a task. No geometry-family-wide impossibility or new-method validation follows. [F037,F043]
''')
# Bounded machine summary: 744 sender cells pivot all metrics; 48 clean companion primary/sensitivity cells as pivot; calibration counts separately.
summary=[]
for r in readcsv(E/'r05_sender_complete_grid.csv'):
 summary.append({'finding_id':'F019-F029','source_path':R+'/T_R05_grouped.csv','source_filter':';'.join(k+'='+r[k] for k in ['kind','family','severity','schedule','sensor','arm','version']),'run_version':'R05','units':'event/episode ratios dimensionless; numerator/denominator in metric-prefixed columns','population':'four dependent comparison segments; not independent episodes',**r})
for r in g:
 if r['kind']=='clean' and r['sensor']!='003' and r['metric']=='eligible_fpr':summary.append({'finding_id':'F028;F050','source_path':R+'/T_R05_grouped.csv','source_filter':f"kind=clean;sensor={r['sensor']};arm={r['arm']};version={r['version']};metric=eligible_fpr",'run_version':'R05','units':'eligible event alarms','population':'clean companion once per segment',**r})
writecsv(O/'results_summary.csv',summary)
assets=[]
def A(path,typ,role,dep,exposure,disposition,contract,limits,work,check,verified='source read; not freshly executed'):
 p=ROOT/path
 assets.append({'original_path':path,'type':typ,'size_bytes':p.stat().st_size if p.is_file() else '', 'role':role,'verification_status':verified,'dependency':dep,'exposure_split':exposure,'migration_disposition':disposition,'input_output_contract':contract,'limitations':limits,'adaptation_work':work,'validation_check':check})
A('src/valid_point/io/mixed_signals.py','code','Strict PCD and pose adapter','NumPy; release-specific conventions','all retained segments','adapt','ASCII float32 PCD -> header/field array; wxyz pose -> rigid matrix','No binary PCD; whole-body parsing; physical origin not proven','Split parser from release adapter; retain raw field names and units','Malformed-token/count/nonfinite tests; exact known transform and independently checked landmark alignment')
A('src/valid_point/replay.py','code','Causal inputs and raw records','adapter; D/G modules','development and comparisons','adapt','CloudEvent/PoseEvent + allowlisted files -> RawFactorRecord','Ideal availability; history policy tied to D/G; no peer corroboration','New inference boundary and time/feature event schema','Withheld evaluator, denied filesystem read, negative clock skew and future-prefix perturbation tests')
A('src/valid_point/evidence/density.py','code','Count primitive / negative baseline','NumPy','development and comparisons','adapt','XYZ + origin XY -> 32 counts/excluded count','Arbitrary cells and one-sided score downstream','Make crop/frame explicit; do not use as reliability labels','Exact half-open boundary and per-cell-preserving counterexample')
A('src/valid_point/evidence/temporal_geometry.py','code','Directed geometry baseline','NumPy; trusted transforms','development and comparisons','reimplement','Cloud pair/poses/gap -> q90 distance or reasoned unknown','CPU bucket loops, max query failure, centroid approximation','Benchmark spatial index and error/abstention tradeoff','Compare bounded small cases to exact nearest neighbors; dynamic/occlusion and work-budget tests')
A('src/valid_point/evidence/kinematics.py','code','Optional motion diagnostic','contracts; NumPy','hand fixtures','defer','Pose pair + prior velocity -> residual metres','No point input; velocity independence unknown','Only use if motion question and provenance justify','Point-only invariance; known acceleration and consistent spoof examples')
A('src/valid_point/temporal.py','code','Explicit missing/warm-up state machine','standard library','R03–R05','adapt','Elapsed-time A or null -> state/readiness/reset','Tau constants and C semantics are not new-study defaults','Separate unit identity and calibration; profile history cost','Irregular-time recurrence; missing/reset; checkpoint/prefix invariance')
A('src/valid_point/attacks/overlays.py','code','Deterministic point interventions','NumPy; density cells','R03 repaired; R05','adapt','float32 Nx4 + key/target/severity -> values and selected/changed/failed IDs','Digital XYZ, not physical or feature attack; target not object','Preserve controls/realization; add fixed encoder and independent feature attacks','Identity reload; same-key reproducibility; exact per-cell constraints; GT task change')
A('src/valid_point/evaluation/real.py','code','Lineage, scoring, replay orchestration','full local package and frozen paths','R05','reimplement','Fold raw records -> refs/calibration/scores; runner -> artifacts','Mixed orchestration/science; helper constants; source snapshots; raw memo assumptions','Keep interface/provenance patterns, rewrite study-specific scoring and stable IDs','No evaluator inference access; exact split roles; cache equivalence under changed history')
A('src/valid_point/evaluation/metrics.py','code','Explicit denominators and censoring','standard library','R04 fixtures/R05','adapt','Sealed evaluator joins -> rates/status/delay','Perturbation target; preexisting-delay and confirmation-time semantics','Define correctness/usefulness targets and risk-coverage; keep nulls','Hand-calculated failed injection, zero support, preexisting alarm and recovery cases')
A('src/valid_point/evaluation/statistics.py','code','Paired/grouped summaries','NumPy; matplotlib; notebook stack','R05','adapt','Saved score/attempt tables -> per-scene/aggregate reports','All-method/version common support collapses; notebook previews thin','Pairwise support; scene weighting; functional versus descriptive claims','Independent table reconciliation; duplicate segment/episode checks; null preservation')
A('src/valid_point/evaluation/splits.py','code','Split and lineage guards','standard library','R04–R05','adapt','Role config -> validated fold identities','Old splits exposed; session identity unresolved','Group by broadest verified acquisition and retain exposure ledger','No frame leakage, shared target/clean variants grouped, exact required reference sets')
A('src/valid_point/provenance.py','code','Hash/export pattern','old S-stage notebook dependencies','S stages','adapt','Config/source/env -> manifest and immutable exports','Stage-specific schemas; integrity not validity; output proliferation','Minimal versioned provenance and artifact allowlist','Byte mutation detected, no overwrite, manifest excludes itself')
A('src/valid_point/ablations.py','code','Algebraic examples','old scoring/reference modules','S03 fixtures','discard-as-research','Seeds -> generated residual/count rows','Not empirical calibration','Keep explicitly labeled illustration only','Never cite as measured scene population')
A('src/valid_point/evaluation/gap.py','code','Constructed tile/box gap','gt_free/oracle/regions','S04 fixtures','discard-as-research','Constructed arrays/annotations -> comparison','No proposal detector; hard-coded gate; artificial calibration','Separate optional teaching fixture','No dataset/association rate claim')
A('tests/test_gt_isolation.py','test','Historical incomplete isolation check','S04','fixtures','discard-as-research','Unused local label mutations -> same function calls','Vacuous withholding/permutation test','Replace with exercised read-denial and mutation boundary','Deliberate leak must fail identical harness')
for path,role in [('tests/test_mixed_signals.py','Time/frame/reader contracts'),('tests/test_replay_isolation.py','Mutation/prefix/history boundary'),('tests/test_evaluation.py','Split/clock/seal/report tests'),('tests/test_overlays.py','Deterministic perturbation constraints'),('tests/test_temporal.py','Temporal invariants')]:
 A(path,'test',role,'pytest; NumPy; package','fixtures','adapt','Small explicit fixtures -> assertions','Passing old tests does not prove new semantics','Retain meaningful checks; change expected new contract','Include failure-triggering controls and exact input provenance')
A('configs/replay_evaluation.json','configuration','Historical exact experiment','R04 freeze','exposed','keep','Frozen design -> R05 grid','Not new method defaults','Copy as provenance only','Current hash matches used version')
A('configs/segment_roles.json','configuration','Historical exposure and hashes','dataset revision','development/comparison/H metadata','adapt','Roles/published hashes -> folds','Do not relabel exposed data untouched','New versioned exposure-aware grouping','No holdout opening during planning; all variants grouped')
A('notebooks','notebooks','Research explanation examples','old Python notebook stack','S/R','adapt','Source notebooks + saved records -> visible explanation','Many display artifacts rather than recompute; stored outputs not fresh','Bounded substantive calculation, failures, units, links','Fresh kernel in new environment; one trace from input to task result')
A(R,'run','Historical negative/conditional evidence','saved tables/ledgers/manifests','C0–C3 exposed','keep','Sealed records -> descriptive results','Not feature tensors or reliability ground truth','Retain original; migrate compact evidence only','Selected hash checks + full table reconciliation; never claim full fresh integrity')
A('reports','reports','Historical figures/tables','S/R exports','constructed/development','keep','Saved table/provenance -> figure','Redundant exports and constructed populations','Carry representative counterexamples only','Caption identifies population and fixture status')
A('requirements.lock','environment','Historical resolved dependencies','CPython 3.14/macOS context','not data','defer','Old environment lock','No model-library compatibility established','Build separate model-supported environment later','Minimal encoder load and deterministic preprocessing check')
A('uv.lock','environment','Later dependency record','pyproject','not data','defer','Lock resolution','Not portability proof','Record separately from old requirements lock','New runtime compatibility and imported versions')
for segment in ['mini_7','mini_10','mini_11','mini_12','mini_13']:
 prefix='data/mixed_signals/1a61aea747aa6bc45da2c2f085a1f1d3abc41f91'
 A(prefix+'/archives/train/'+segment+'.tar','archive','Retained source data','exact release and license','development' if segment=='mini_7' else 'comparison exposed','keep','Archive -> future authorized selective extraction','Archive hashes historical, not recomputed','Reuse in place; avoid duplicate copies','Compare recorded size/hash before authorized future processing','stat only; historical hash assertion')
 A(prefix+'/raw/PointClouds/'+segment,'dataset','Selected clouds','release adapter','exposed','adapt','ASCII point clouds -> geometry/possible future features','Labels not extracted; actual firing origins/timing unresolved','Use in place; validate feature path','Known frame and task labels align; no hidden data leakage','fresh file stats; sampled headers only')
writecsv(O/'asset_inventory.csv',assets)
doc('05_reusable_assets_and_migration_spec.md','''# Reusable assets and migration specification

Reuse engineering contracts without importing the old estimand. The [asset inventory](asset_inventory.csv) gives original path, dependency, exposure, input/output contract, limitations, adaptation work and a concrete validation check for each item. The table below is its readable disposition summary. Exact original files stay in Valid Point; only selected evidence excerpts/configuration are included here. [F008,F011–F018,F026,F030–F043]

| Asset | Disposition | Migration purpose / required validation |
|---|---|---|
'''+ '\n'.join('| `'+a['original_path']+'` | '+a['migration_disposition']+' | '+a['role']+'; '+a['validation_check']+' |' for a in assets if a['type']!='archive' and a['type']!='dataset')+'''

## Minimal migration contract

**Keep:** immutable raw-source identity, release attribution, exact event timestamps and clock meanings, stream/principal mapping, attempted/eligible/realized counters, original failure artifacts, deterministic seed keys, clean/attacked pairing, explicit unavailable values and per-scene reporting. Keep old tables as old-study evidence only. [F026,F033–F039,F046]

**Adapt:** strict input parser; transforms verified independently on the chosen release; inference-access boundary; state lifecycle; attack serialization; metrics and provenance. Adaptation must be validated against new feature unit, receiver inputs and task labels. Do not carry hidden hard-coded dataset roots, enum ordering in IDs, or implicit same-sender evidence independence. Hash canonical episode content with an explicit version instead of mapping enumeration order. [F008,F030,F036]

**Reimplement:** the perception feature-extraction/fusion interface and the actual reliability target. Existing `NormalizedFactors`, D/G CSVs and A/C/Z values are statistics of point clouds, not learned intermediate tensors or GT labels. Current point attacks can test feature robustness only by passing their realized clouds through the same frozen encoder/preprocessing; separately define direct feature attacks. [F037,F043]

**Discard as research evidence:** artificial S03 calibration/generalization, S04 proposal/association rates, vacuous early isolation claims, and a guaranteed descending severity curve. Preserve those files historically and retain useful arithmetic counterexamples with constructed labels. [F004–F007]

**Defer:** old dependency environment, quota/consensus policy, independent-velocity interpretation, unverified checkpoints, H access and any final paper novelty claim. Low memory/compute is a requirement to measure, not a reason to reuse old constants or claim the finalizer RSS as deployment cost. [F003,F009,F032,F044–F045]

A recommended reused asset passes its validation check in the new environment before contributing a scientific claim. A whole old runner is not a migration unit: it mixes path conventions, old scientific equations, artifact ownership and resource assumptions. New documentation should state what was borrowed, what was revalidated and what changed.
''')
doc('06_requirements_for_the_new_study.md', '''# Requirements and open choices for the new study

These are proposed, testable requirements [F045], motivated by verified gaps; no method wins by being listed. The primary output must describe reliability of an **individual received feature, spatial feature region or feature-supported object hypothesis at a defined time**, not persistent sender reputation. No requirement forces scores to descend under all manipulations.

| ID | Requirement / open choice | Motivation | Acceptance check before stronger claims |
|---|---|---|---|
| N01 | Define unit and meaning: probability of task correctness, bounded evidential support, expected utility change, or selective acceptance risk. Choose and label one primary estimand. | F012,F014,F043 | A written target maps each output to time/space/task and a measurable GT evaluation; changing sender ID alone cannot change content reliability. |
| N02 | Declare inference inputs and adversarial control for every field. Separate feature-only from feature+receiver raw scans or occupancy metadata. | F009,F035–F038 | Dependency graph and executable access boundary; outputs unchanged when withheld GT, attack schedules and clean counterparts are changed/denied. Deliberate leak fails. |
| N03 | GT may be used for supervised training, development and evaluation with proper splits. Hidden GT, attack schedules and clean counterparts are prohibited at deployment inference. | F004–F008,F039,F043 | Training/development/test acquisition groups and supervision provenance recorded; identical deployment API on clean/attacked data; no unnecessary blanket ban on training labels. |
| N04 | Establish genuine intermediate-feature pipeline and fusion boundary. Choose model/checkpoint, layer, tensor unit, preprocessing/alignment, class conventions and output detector metrics. | F037,F048 | Reproduce a bounded clean perception result against compatible labels, verify known transforms, save exact tensor schema/hash and encoder identity. |
| N05 | Separate threat models: raw point edits before encoding; received feature edits; pose/time/occupancy metadata control; physical attacks only with separate evidence. | F019,F026,F031,F038 | Threat matrix lists attacker knowledge/control, feasible constraints and target; every intended edit has realized effect and task harm measured, including failures. |
| N06 | Preserve honest unique viewpoints and uncertainty under no independent support. | F015,F028,F038,F043 | Evaluate complementary/occluded objects and unsupported regions; a correct unique view is not rejected solely for peer absence. Quantify utility/recall lost by filtering. |
| N07 | Benign controls include dynamics, occlusion/disocclusion, sparsity, range, noise, transform/timing uncertainty and sensor degradation. | F022,F025,F050 | Same evaluation pipeline on benign/attack strata; report false rejection and abstention with denominators, task metrics and severity distributions. |
| N08 | Calibration/uncertainty must match the chosen unit and support population. Separate insufficient support, degenerate score, threshold saturation and unknown. | F013,F020–F021,F039 | Held-out grouped calibration; risk/coverage and reliability diagnostics where applicable; predeclared null behavior; no frame-IID guarantees or conflating no power with zero future alarms. |
| N09 | Temporal policy must address moving objects, attacked history, resets and delayed evidence without future access. | F015–F018,F029 | Prefix invariance, contaminated-history counterexample, onset/censoring and post-offset recovery evaluated; no clean shadow or forced recovery. |
| N10 | Define deployment budget after input/model feasibility; low compute/memory matters but hardware is open. | F016,F030,F032 | Measure end-to-end latency distribution, peak working set, state growth, encoder/fusion overhead, throughput, serialization and failure under budget on named hardware. Include worst observed workloads, not only finalizer. |
| N11 | Start with primary-literature review and observability before method selection. Compare simple baselines and a justified lightweight learned option. | F038,F044 | Review matrix in [07](07_literature_questions_and_candidate_methods.md), full-paper reads, official code/checkpoint availability check, explicit retain/reject reasons. No novelty claim from names alone. |
| N12 | Research notebooks and paper claims must expose real computation and falsifiable results. | F004–F007,F040,F043 | Fresh bounded notebooks trace inputs→features→evidence→decision→GT task outcome; all grid cells and unknowns retained; claims cite populations/versions. Publishable benefit requires downstream improvement and honest-view safeguards, or report a negative result. |

## Choices deliberately left open

Feature element versus spatial region versus object-supported hypothesis; semantic definition of “useful” versus “correct”; deployment evidence available independently of a sender; model/checkpoint/release; independent acquisition groups and new test exposure policy; calibration loss and abstention cost; accepted perturbation realism; spatial and temporal resolution; hardware/budget; and deterministic/statistical/learned/hybrid combination. Resolve these through literature and bounded feasibility evidence, not a preferred-looking plot.

Compare a no-filter fusion baseline, a simple declared reliability baseline, and candidate method under matched feature/communication/compute settings. Ground truth supplies evaluation, not runtime evidence. A supervised lightweight combiner is permissible if its inputs, grouped supervision, calibration and resource cost are justified. Its training labels must not silently become deployment features.

A successful scientific result may be that an evidence source is non-identifying, unavailable, too expensive or harmful to unique viewpoints. Technical completion requires reproducible evidence and honest disposition, not positive benefit. The handoff does not implement or validate any new candidate.
''')
doc('07_literature_questions_and_candidate_methods.md', '''# Literature questions and candidate methods

The colleague’s informal lead, attributed only as **the user’s colleague**, is to count supporting LiDAR returns and traversing measured rays. A compatible return can support a proposed surface/object; a ray passing through an allegedly occupied portion and ending behind it may contradict it under justified assumptions. This is **unvalidated**, is **not support vector machines**, and is not asserted novel. A box is not solid; no-return is not automatically free space; a latent tensor does not supply rays. [F038,F044]

## Candidate comparison: hypotheses, not recommendations of a winner

| Family / specific question | Required observable inputs | Independent trust assumptions | Likely blind spots | Computational bottleneck | Retain/reject evidence |
|---|---|---|---|---|---|
| Support/traversal evidence: can compatible returns and verified traversals distinguish false proposals while retaining unique objects? | Proposed occupied/surface region, actual return endpoints, justified 3D firing origin/time, transforms, uncertainty and visibility coverage. Feature-to-proposal mapping if output is feature reliability. | At least some rays from receiver or independent observer; sender-supplied counts/rays can be jointly forged. | Box empty volume, porous/partial objects, glass/multiple returns, occlusion, sparse coverage, moving objects, origin/time error. | Ray-region intersection, spatial indexing and per-return processing; raw-scan bandwidth. | Bounded hand geometry with known occupancy and uncertainty; real aligned independent coverage; GT false-proposal and unique-view false-rejection curves. Reject core use if required origin/coverage absent or contradictions mostly benign. |
| Visibility-aware occupancy consistency baseline: can free/occupied/unknown maps identify task-relevant contradictions? | Sensor origin, raw returns or trusted occupancy maps, alignment/time, explicit unknown and visibility regions. | Occupancy provenance and uncompromised comparator; maps derived from attacked same source are not corroboration. | Shared occlusion, coarse cells, stale map, moving structures, colluding observers. | Ray integration plus sparse grid/octree update and cross-map intersection; memory scales with active space/resolution. | Compare with raw support/traversal at equal resolution/budget; retain only if calibrated coverage and task benefit survive benign noise. |
| Temporal/cross-view feature residuals: does a local residual predict incorrect/harmful evidence rather than normal novelty? | Exact feature layer, comparable encoders, pose/time alignment, causal history or independent view, overlap/visibility validity. | Trusted reference encoder/pose and explicit compromised-source model. | Honest unique viewpoint, semantic shifts, feature scaling, compression, attack adaptation and contaminated history. | Warping, local matching, feature similarity and history cache; channel/spatial size. | Residual versus GT error and fusion utility on grouped splits, occlusion/pose stress, non-identifying examples; reject if only sender identity or novelty predicts scores. |
| Simple statistical/evidential models: can interpretable support/conflict/uncertainty summaries yield useful selective risk? | Validated features such as coverage, residuals, support/conflict and observation quality with units. | Evidence channels’ correlation and availability modeled; a pseudo-count is not independent evidence. | Misspecified likelihoods, dependent rays, small calibration, distribution shift, confident conflict. | Small scalar updates cheap; upstream evidence may dominate. | Compare logistic/simple likelihood/evidence-count alternatives; calibrate and assess risk-coverage, ablate assumptions, retain uncertainty on absent support. |
| Small learned combiner: can supervised nonlinear combination improve over simple baselines within budget? | Same deployable evidence plus grouped training labels and a defined target. | Training label quality, no hidden evaluator features, representative development groups. | Shortcut learning, source/site identity, unseen attacks/benign shifts, overconfident extrapolation. | Training/sweep cost and feature computation; inference architecture should be measured. | Group-held-out calibration/task utility, feature ablation, ID-leak checks and runtime versus linear baseline. Reject if gains disappear outside familiar scenes or cost exceeds budget. |

## Verified primary-source leads (22 October 2026)

These are **lead verification only**: landing pages/abstracts or specified snippets were read, not full papers. No reported performance is adopted here, and no code/checkpoint has been installed, loaded or certified available. Old source pins remain separate from current availability.

| Lead / verified page | Why inspect next; full-review questions |
|---|---|
| [OPV2V, Xu et al.](https://arxiv.org/abs/2109.07644) | Abstract describes early/late/intermediate LiDAR fusion benchmark and intermediate pipeline. Read exact encoder/fusion boundaries, dataset assumptions and official implementations; do not presume Mixed Signals transfer. |
| [Where2comm, Hu et al.](https://arxiv.org/abs/2209.12836) | Spatial confidence maps and communication selection are relevant to spatial feature units. Determine whether confidence is calibrated correctness, utility, or only selection signal; inspect adversarial sender control and unique-view treatment. |
| [Adversarial Attacks On Multi-Agent Communication, Tu et al.](https://arxiv.org/abs/2101.06560) | Author abstract explicitly studies attacks on shared learned intermediate representations. Read attack knowledge, feature alignment, transfer and evaluation targets before defining feature corruption. |
| [On Data Fabrication in Collaborative Vehicular Perception, Zhang et al., USENIX Security 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/zhang-qingzhao) | Primary abstract verifies collaborative fabrication/defense topic; [paper lead](https://www.usenix.org/system/files/usenixsecurity24-zhang-qingzhao.pdf) and prepublication search excerpt describe occupancy consistency. Read full occupancy/free/unknown construction, independence, timing and failure assumptions before using as baseline. |
| [Towards Robust LiDAR-based Perception…, Sun et al., USENIX Security 2020](https://www.usenix.org/conference/usenixsecurity20/presentation/sun) | Abstract identifies occlusion patterns, CARLO and SVF. Read geometric evidence and exact assumptions; compare colleague’s idea against established occlusion/free-space approaches before any novelty assertion. |
| [OctoMap project / Hornung et al. paper link](https://octomap.github.io/) | Official project describes probabilistic 3D occupancy and memory-efficient octrees. Read sensor-model assumptions, free/occupied/unknown handling and dynamic-world limitations; implementation availability is not suitability. |
| [A Gentle Introduction to Conformal Prediction…, Angelopoulos and Bates](https://arxiv.org/abs/2107.07511) | Verified author tutorial lead for calibration, shift, time series and abstention. Read assumptions before importing finite-sample claims to dependent scene/frame data. |
| [The Latent Guardian…, Zhang et al., PMLR 2026](https://proceedings.mlr.press/v306/zhang26cs.html) | Current primary abstract describes feature-level consistency. Full paper and independent reproduction not read/performed; inspect exact unit, threat model, noise/unique-view controls and lightweight feasibility. Do not adopt abstract performance claims. |
| [Mixed Signals, Luo et al.](https://arxiv.org/abs/2502.14156), [current HF card](https://huggingface.co/datasets/sberrio/Mixed-Signals-V2X) | Dataset/release feasibility leads. Read original paper and exact release conventions, labels/splits/point support, sensor calibration and compatible models. Historical pinned devkit/ACFR sources are listed in [preserved sources](evidence/source/planning/sources.md); no fresh checkpoint claim. |

## Search agenda and decisions to record

| Area | Search strings | Evidence sought |
|---|---|---|
| Intermediate cooperative perception | `cooperative LiDAR intermediate fusion feature spatial confidence unique viewpoint`; `Mixed Signals heterogeneous LiDAR checkpoint preprocessing` | Exact transmitted tensor, alignment, classes, fusion and compatible weights; reproduce bounded baseline. |
| Byzantine/feature corruption | `adversarial multi-agent communication intermediate features Byzantine cooperative perception`; `cooperative perception stealthy feature injection defense` | Sender control, collusion/metadata assumptions, adaptive attacks and task metrics; distinguish reputation from local evidence. |
| Object/free-space/rays | `LiDAR object consistency ray traversal free space CARLO`; `collaborative perception occupancy consistency CAD unknown` | What counts as physically contradictory, surface versus box interior, independent evidence and return semantics. |
| Occupancy/visibility | `probabilistic occupancy ray inverse sensor model occlusion dynamic objects`; `visibility aware cooperative perception occupancy unknown` | Unobserved versus free, time/motion handling and maps under compromised senders. |
| Calibration/selective prediction | `spatial structured selective prediction risk coverage conformal temporal dependence`; `calibration cooperative perception uncertainty` | Correct target, finite support, grouping, uncertainty and distribution shift assumptions. |
| Temporal evidence | `cooperative perception temporal consistency feature delay pose error history poisoning` | Causality, asynchronous scans, clean versus attacked history, contamination mitigation without oracle. |
| Efficient implementation | `ray traversal sparse occupancy edge inference memory latency`; `cooperative LiDAR feature reliability lightweight` | Measured full-path costs, data structures, approximation-error/coverage tradeoffs and deployment inputs. |

For each paper, record version, sections actually read, task/unit, observable inputs, assumptions, GT role, splits/exposure, baseline/attack fairness, unknown handling, compute and official code/weight checks. Then produce a gap matrix and a small falsification experiment plan. The agenda is intentionally not a broad review, novelty verdict or implementation design. [F044–F045]
''')
doc('08_reproducibility_resources_and_notebook_lessons.md', '''# Reproducibility, resources and notebook lessons

Preserve reproducible measurements without reproducing heavyweight workflow overhead. This extraction ran standard-library table/record analysis only; no package imports, model training, replay, tests or notebook execution. Scripts live under [evidence](evidence/README.md) and write only this package. [F030–F032,F040–F042,F046–F049]

## Trustworthy practices versus overhead

| Retain/adapt | Avoid inheriting |
|---|---|
| Explicit dataset revision, source hashes, config identity, environment record and immutable outputs | Treating a checksum, successful kernel or gate label as a scientific result |
| Causal event/pose IDs; separate source and availability clocks; inference-access tests | Inference conditioned on evaluator schedules or clean alternatives |
| Deterministic overlays with actual production reload and intended/realized ledgers | Multiple full archive/extraction copies or simultaneous derived episodes |
| Per-scene tables with nulls and failure statuses; paired clean/attack evidence | Counting frames, seeds, repeated companions or shared-fold fits as independent scenes |
| Small reproducible explanation plus complete machine results | Repeated huge Markdown exports, redundant figures and completion-label notebooks |
| Snapshot-specific provenance and resumable checkpoints | Episode IDs tied to iteration order; partial-directory collisions; final-version-only provenance |

## Environment and observed resources

`pyproject.toml` requires Python >=3.11, NumPy >=2,<3 and nbconvert >=7.17.2, with optional Jupyter/matplotlib/pytest stack. Historical locks and stored environment records are separate evidence: final R05 reports Python 3.14.4 and NumPy 2.5.4 on macOS/Clang. Do not import this environment into a detector project without checking the chosen model’s official supported stack. No specific model/library incompatibility was tested here; GPU/runtime/checkpoint support is unresolved. [F032,F037]

| Measurement / exact saved source | Recorded value and scope | What it cannot establish |
|---|---|---|
| R02 `artifacts/20261009T085704Z-R02/environment.json` | CPU 86.327268 s, wall 88.179544 s, peak RSS 209,420,288 bytes for that bounded development run | Per-device worst-case latency or encoder/fusion cost |
| Later R02 `20261012T043451Z-R02/environment.json` | CPU 91.317607 s, wall 92.832765 s, peak RSS 263,815,168 bytes; same development category | Independent scene replication or a universal memory bound |
| R03 `20261010T155346Z-R03/environment_final.json` | Runner before repairs: wall 1,950.328783 s, CPU 1,928.21655 s, peak RSS 429,801,472 bytes | Repairs explicitly not separately instrumented; not historical complete-work peak |
| R05 `resource_amendment.json` | Accepted 4,000,000,000-byte run plus one active derived-episode cap; archives/extracts retained separately | Achieved peak RSS or actual deployment RAM |
| R05 `environment_final.json` | Finalizer peak RSS 179,617,792 bytes; recorded run bytes 2,594,335,265; free disk 22,101,475,328 at that time | Earlier replay processes, notebook child memory, historical scratch peak or present free disk |

These are **saved measurements re-read**, not fresh benchmarks. R05 episode wall times in `execution.log` include different work/reuse paths and interruptions; dividing finalizer memory or cached replay timing by event count would not estimate deployed cost. macOS `ru_maxrss` is stored as bytes here; portable resource instrumentation must identify platform units and child processes. [F032]

## Preserved failures and their correction status

| Failure evidence | Disposition |
|---|---|
| Early S00/S01/S03/R04 fresh kernels denied localhost sockets | Execution-environment failure, later successful runs exist. No evidence against scientific hypothesis. |
| S03 `20261008T091349Z-79149ae5` KeyError `K+S` | Tied-factor summary handling repaired in later accepted S03 artifacts; artificial population remains. |
| R02 `20261009T085343Z-R02/failure.txt` | Native XY D unnecessarily depended on vehicle pose; corrected before accepted run. Font-cache plotting delay also recorded. |
| R03 `20261010T152207Z-R03/failure.txt` | Excessive unbounded candidate work interrupted; deterministic 10-million-pair guard added. Unknown-on-budget behavior needs measurement. |
| R03 `protocol_deviation/`, `execution_repair.log`, `notebook_error.txt` in accepted run | First rearrangement allowed outside-cell changes; corrected constraints and preserved partial failures. Notebook/geometry repairs documented. |
| R04 early blocked attempts | Incorrect metric fixture, missing pandas in fresh kernel, broad test collection of artifact snapshots; later exact-lineage and resample-copy repair. Scoped project suite and authoritative freeze succeeded. |
| R05 four `failure_20261013T*.json` files | One compact-evidence storage cap failure and three FileExistsError restarts; six prediction implementation snapshots remain. |
| R05 clock availability correction | Negative modeled skew must not advance actual pose availability; corrected helper/current test. Historic full-row audit reported no future original poses; not repeated for every row here. |
| R05 review seal / ID repair | Ignore only `.DS_Store`, retain scientific hashes; reconstruct IDs from original config order after canonical equality. Final reports exist; obsolete review commands not run. |

Sources are preserved in [run status extracts](evidence/run_status_and_failures.json), original run directories and [history](01_project_history_and_actual_state.md). Technical repairs do not retroactively establish independent labels, calibrated future FPR or task utility. [F030–F031,F041]

## Source notebooks versus executed evidence

All 99 notebook files in the included source/artifact categories were parsed for cell source, execution counts, output types/text and errors. Image payloads were not visually rendered; text extracts are bounded. This is content inspection, not execution or exhaustive visual QA. Fourteen source notebooks exist; only R01 contains executed code outputs in the source file (five code cells); the others are templates with null counts. Executed copies live in dated artifacts. [notebook cell inventory](evidence/notebook_cells.json)

| Source notebook(s) | What code actually computes or displays | Executed scope |
|---|---|---|
| `00_bootstrap` | Imports/environment/provenance and trivial exports, fresh-kernel checks | Infrastructure only; stored failures and successes |
| `01_synthetic_scenes` | Small seeded scene and transform/contract views | One synthetic family, no real perception |
| `02_kinematics`, `02_spatial_surplus`, `02_availability` | Calls importable hand-evidence routines, shows residual/count/eligibility tables and plots | Arithmetic/causality fixtures |
| `03_clean_references`, `03_score_and_ablations` | Invokes fixture generation, quantile fitting/scoring/calibration and exports | Algebraic S03 observations; no raw-cloud calibration |
| `04_gt_free_oracle_gap` | Constructs fixed tiles/box cases, calls comparison and plots | Twelve constructed cases; not proposals/association algorithms |
| `R01_development_intake` | Reads recorded schema/timing/geometry evidence and plots retained bounded geometry | Source file stored outputs; intake work performed by script |
| `R02_causal_factors` | Loads raw tables, displays timelines/alignment and boundary/resource records | Saved actual development measurements, not new comparison fit |
| `R03_replay_temporal` | Loads sealed predictions, contrasts geometry/timelines, computes diagnostic summaries; reads poses for display | Development-only; null alarm thresholds |
| `R04_protocol_freeze` | Loads config/roles, renders split/schedule diagrams, executes small metric arithmetic fixture | Metadata/protocol, not outcome evidence |
| `R05_segment_timelines` | Checks seal, reads saved raw/thresholds, previews tables, displays existing figures | Four executed segment notebooks, seven code cells each |
| `R05_grouped_evaluation` | Checks seal, previews saved tables, displays ablation/severity/failure figures | One executed grouped notebook, seven code cells |

R05 notebooks have meaningful source/provenance checks but mostly present existing results. Fresh execution of them does not independently regenerate raw measurements or train/evaluate a detector. The final stored suite records 134 tests, no failures; it was not rerun. Old report counts and stored output are evidence of the recorded execution, not current compatibility. [F040,F042]

## Next-project notebook acceptance

Each notebook should state one research question, population, deployment inputs and falsification condition; show a small real example with units/coordinate/time provenance; compute preprocessing and the selected feature/evidence step visibly through importable functions; derive the equation and one hand counterexample; expose intermediate arrays/summaries, unknown reasons and input dependencies; then evaluate against compatible GT and explain a success, a miss, a benign rejection and an unsupported unique view. Keep evaluator overlays visually distinct.

Include a bounded executable path with cached immutable large inputs, a reproducible full-table command, fresh-kernel execution, exact environment/model identity, resource measurement and a claim ledger. Present complete small grids and aggregate counts, not just `head()` rows plus “PASS.” Keep expensive replay optional and explicit; never make opening an explanatory notebook copy archives or start training. No generated notebook is supplied here because this task is an extraction, not the new study.
''')
doc('09_portable_handoff.md', '''# Portable handoff: retiring Valid Point

This brief is self-contained. The accompanying folder is documentation/evidence, not a runnable replacement project. Audit date: **22 October 2026 (Asia/Kolkata)**. Original repository HEAD: `14371e6bee024544678481c0976641ba495dbda6`; the planning directory was untracked and preserved. Paths below are relative to the old repository or to this package, never dependent solely on a user-specific absolute path.

## Objective for the next project

Investigate dynamic reliability of individual received intermediate features, spatial feature regions or feature-supported object hypotheses in cooperative LiDAR perception. The output must refer to evidence at a defined time/spatial/task unit, not persistent sender reputation. Test whether manipulations reduce correctness/usefulness, how benign conditions confound that relationship, and whether reliability improves perception against GT while retaining honest unique viewpoints. Negative results are allowed. Deterministic, statistical, lightweight learned or hybrid approaches remain open. Low compute/memory matters; hardware is undecided.

## What the old study actually did

Early S stages used toy geometry and algebraically generated observations for sender/frame conformity. S03’s clean calibration was not measured from sensors; S04’s proposal/association states were annotations and its old isolation test changed unused variables. Later R stages implemented real ASCII PCD/odometry replay with causal input checks, deterministic XYZ manipulations, count surplus D, directed temporal novelty G, separate instantaneous/EWMA states, clean reference fitting and calibration. Later access/prefix/leakage-positive tests materially improved engineering isolation. There is **no learned intermediate-feature extractor, operational perception fusion/backbone or GT object-detection evaluation** in the audited implementation. [F004–F018,F037,F043]

D takes the maximum clipped positive excess over 32 sensor-relative count references. Pure removal cannot increase it; per-cell-preserving rearrangement cannot change it. G is the 90th percentile of current-to-previous motion-compensated voxel-centroid distances: it is novelty, not independent occupied/free-space truth. Moving objects, disocclusion and alignment error confound it; missing history/search bounds can make it unavailable. Current attacked clouds become later history. Calling these quantities “reliability” would not fix their objective mismatch. [F011–F018]

## Verified terminal state and most useful results

R05 is technically finalized, with a final seal on **18 October 2026 01:00:20 IST**, complete tables, five executed notebooks and a stored 134-test passing suite. Old progress/checklist/history/review documents still incorrectly say reporting and GR5 are pending. Do not run their obsolete continuation commands. No R06/R07 run was found; H/mini_14 is recorded unopened and was not inspected here. [F002–F003,F042]

The saved R05 study reuses four comparison segments in 248 episodes (each segment: 30 attacks, five identity, one clean, 26 benign stresses). There are 240 calibration cells: 156 insufficient known scores, 31 tagged no-power and 53 available. Of the no-power cells, 21 thresholds equal one and cannot be exceeded by the bounded score; ten constant-zero calibrations can still alarm on later positive scores. For sender 003, positive all-attempt recall occurs only in certain addition cases; G-only and max arms cannot produce calibrated alarms. D memoryless clean alarms are 29/999 eligible events; sustained 20% addition gives 199/399 scheduled events, with segment counts 0/99,99/99,100/100,0/101. These are dependent event counts, not universal rates. [F019–F029]

All 12,240 grouped rows were reconciled with 48,960 segment metric rows. Eight important saved score streams were traced against compact attempt records. Selected 65 hash comparisons match their recorded manifest/seal. Large cloud bodies/archives and the full 748-prediction seal were **not** freshly audited. Historic assertions are identified separately. Byte integrity and passing tests do not establish scientific validity. [F046–F049]

## Data and engineering that can be reused carefully

Local data revision is recorded as `1a61aea747aa6bc45da2c2f085a1f1d3abc41f91` of `sberrio/Mixed-Signals-V2X`. Old repository `data/mixed_signals/<revision>/archives/train/` retains mini_7 and mini_10–13 TARs; selected extracts are under `raw/PointClouds/` and `raw/Odometry/`. Five streams represent four principals: vehicles 003/004/laser and an RSU with top+dome sensors. Retained data is exposed development/comparison data; renaming cannot restore untouched test status. Session independence is unverified. [F033–F039]

Variable twist columns exist in all fifteen inspected local odometry CSVs. Their frame/provenance/independence remains unresolved. Label TXT filenames exist in historical archive inventories; expected extracted labels are absent. Do not infer no GT, silently substitute older JSON/PKL labels, or treat label-derived visibility as runtime evidence. Known coordinate conventions include wxyz quaternions, raw RSU map coordinates, paired vehicle −3.25/+3.25 m adjustments and legacy short-subsecond **left-padding**. These are adapter conventions, not independently verified physical laser origins or deskew. Arrival=source and pose availability=stamp are replay assumptions. [F010,F034–F038]

Reuse candidates: strict reader rejection/empty-versus-absent semantics; explicit frames/clocks; causal read allowlists; deterministic seed/overlay generation; actual production reload; intended/injected/realized ledgers; paired comparisons; unknown/censoring semantics; state/prefix tests and compact provenance. Revalidate each in the new environment. Do not inherit old score equations/constants, clean-only training restrictions, scene independence claims or environment locks. D/G tables are neither latent tensors nor reliability supervision. [05](05_reusable_assets_and_migration_spec.md) supplies contracts and acceptance checks.

## Candidate idea and unresolved prerequisites

The user’s colleague informally suggested supporting returns versus traversing rays. It is not SVM and is not selected or claimed novel. A verified ray ending behind an allegedly occupied region may contradict it under justified origin/time/visibility assumptions; a bounding box is not solid and a missing return is not proof of free space. Features alone do not expose emitted rays. Establish whether receiver raw scans or trusted occupancy metadata provide independent coverage; sender-supplied evidence can be jointly corrupted. [F038,F044]

Resolve: reliability unit/target; actual deployable inputs and adversarial control; compatible perception model/checkpoint and encoder layer; preprocessing and feature alignment; compatible label/class/frame conventions; new exposure-aware split; independent evidence availability; benign/attack matrix; uncertainty/abstention costs; resource budget and hardware. Supervised GT training is allowed with proper splits, while deployment inference must not read hidden GT, schedules or clean counterparts. No new methodology is validated by this package. [F045]

## Included evidence and what stays behind

Included locally: ten narrative documents; stable finding ledger; migration inventory; bounded complete-grid summaries with denominators; parsed notebook/code/planning indexes; selected source excerpts/configurations; local metadata and small-file checks; compact-record examples; audit/reconciliation scripts; SHA-256 manifest. Start with [README](README.md), [evidence guide](evidence/README.md), [results](04_experiments_and_verified_results.md) and [requirements](06_requirements_for_the_new_study.md).

Still in the old repository: bulk TARs/PCDs, complete prediction/raw histories, derived geometry arrays, all original figures/notebooks, source trees, historical manifests and logs. Source paths in the ledger identify them; they may be unavailable in a new environment. No bulk data, full old source tree or third-party paper was copied. The included excerpts are evidence, not a complete executable migration.

Next planning actions: read primary literature and compare exact assumptions; verify chosen dataset/model/labels and observable evidence on a bounded exposed example; define estimand/inference/threat/split contracts; choose a minimal set of falsifiable baselines with GT task evaluation and honest-view safeguards; specify resource measurement and substantive notebook outputs. Do not restart Valid Point or open the old holdout as part of this handoff.
''')
