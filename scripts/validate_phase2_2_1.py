#!/usr/bin/env python3
"""Fail-closed Phase 2.2.1 reconciliation / evidence validator."""
import argparse,csv,json,sys
from pathlib import Path

def jl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def durable(x): return x.get('archive_status')=='DURABLE_VERIFIED' and bool(x.get('archive_locator')) and bool(x.get('archive_entry')) and x.get('archive_entry')!='manifest_subset.json' and bool(x.get('content_hash'))
def validate(src,out):
 src=Path(src);out=Path(out);errors=[]
 with (src/'creative_mechanism_phase2_2_reference_master.csv').open(encoding='utf-8-sig',newline='') as f: master=list(csv.DictReader(f))
 snaps=jl(src/'creative_mechanism_phase2_2_snapshots.jsonl');scenes=jl(src/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl')
 claims=jl(src/'creative_mechanism_phase2_2_claim_ledger.jsonl');candidates=jl(src/'creative_mechanism_phase2_2_mechanism_candidates.jsonl');archive=jl(src/'creative_mechanism_phase2_2_archive_index.jsonl')
 ids={r['reference_id'] for r in master};vp={r:set() for r in ids}
 for x in snaps:
  if durable(x):
   width=(x.get('viewport') or {}).get('width');label=x.get('viewport_label') or ('DESKTOP' if width==1440 else 'MOBILE' if width==390 else None)
   if label in ('DESKTOP','MOBILE'): vp[x['reference_id']].add(label)
 states={r for r in ids if {'DESKTOP','MOBILE'}<=vp[r]}
 agg=json.loads((out/'creative_mechanism_phase2_2_1_aggregate.json').read_text())
 with (out/'creative_mechanism_phase2_2_1_reference_master_reconciled.csv').open(encoding='utf-8',newline='') as f: reconciled=list(csv.DictReader(f))
 if sum(x.get('usable_reference_derived')=='true' for x in reconciled)!=agg.get('usable_reference_count'): errors.append('derived Master usable count differs from aggregate')
 expected={'attempted_reference_count':len(ids),'usable_reference_count':len(states),'failed_reference_count':len(ids)-len(states),'desktop_durable_count':sum('DESKTOP'in v for v in vp.values()),'mobile_durable_count':sum('MOBILE'in v for v in vp.values()),'both_viewports_durable_count':len(states),'snapshot_count':len(snaps),'durable_snapshot_count':sum(durable(x) for x in snaps),'scene_count':len(scenes),'OBSERVED':sum(s.get('observation_state')=='OBSERVED' for s in scenes),'NOT_OBSERVED':sum(s.get('observation_state')=='NOT_OBSERVED' for s in scenes),'NOT_APPLICABLE':sum(s.get('observation_state')=='NOT_APPLICABLE' for s in scenes),'durable_scene_count':sum(s.get('observation_state')=='OBSERVED' and durable(s) for s in scenes),'claim_count':len(claims),'candidate_count':len(candidates),'archive_entry_count':len(archive)}
 for k,v in expected.items():
  if agg.get(k)!=v: errors.append(f'aggregate.{k}: expected {v}, got {agg.get(k)}')
 with (out/'creative_mechanism_phase2_2_1_coverage_matrix.csv').open(encoding='utf-8',newline='') as f: matrix=list(csv.DictReader(f))
 if len(matrix)!=20: errors.append(f'coverage matrix expected 20 cells, found {len(matrix)}')
 if sum(int(x['both_viewports_durable_count']) for x in matrix)!=agg['both_viewports_durable_count']: errors.append('coverage matrix sum differs from aggregate')
 if sum(int(x['failed_reference_count']) for x in matrix)!=agg['failed_reference_count']: errors.append('coverage matrix failed count differs from aggregate')
 for summary_name in ('creative_mechanism_phase2_2_1_qa_report.json','creative_mechanism_phase2_2_1_pm_report_summary.json'):
  summary=json.loads((out/summary_name).read_text())
  if summary.get('aggregate')!=agg: errors.append(f'{summary_name} aggregate mismatch')
  if summary.get('phase2600_allowed') is not False: errors.append(f'{summary_name} must preserve the 2,600 hold')
 if agg.get('phase2600_allowed') is not False: errors.append('2,600-reference gate must remain false')
 failure=jl(out/'creative_mechanism_phase2_2_1_failure_recovery_ledger.jsonl')
 if len(failure)!=27 or sum(x.get('failed_viewport_attempts',0) for x in failure)!=54: errors.append('failure ledger must reconcile 27 references / 54 viewport attempts')
 if any('BYPASS' in str(x.get('allowed_recovery','')).upper() and 'NO_SECURITY_BYPASS' not in str(x.get('allowed_recovery','')).upper() for x in failure): errors.append('security bypass path detected')
 # All extracted candidates must link only to observed scene evidence; counts derive from IDs.
 scene_by={x['scene_evidence_id']:x for x in scenes};ms=jl(out/'creative_mechanism_phase2_2_1_atomic_calibration.jsonl')
 for m in ms:
  refs=set()
  for sid in m.get('source_scene_evidence_ids',[]):
   s=scene_by.get(sid)
   if not s: errors.append(f"{m.get('mechanism_id')}: missing scene {sid}");continue
   if s.get('observation_state')!='OBSERVED': errors.append(f"{m.get('mechanism_id')}: non-OBSERVED source {sid}")
   refs.add(s['reference_id'])
  if not m.get('source_scene_evidence_ids'): errors.append(f"{m.get('mechanism_id')}: empty provenance")
  if m.get('evidence_count')!=len(m.get('source_scene_evidence_ids',[])): errors.append(f"{m.get('mechanism_id')}: manual evidence_count mismatch")
  if m.get('reference_count')!=len(refs): errors.append(f"{m.get('mechanism_id')}: reference_count mismatch")
  if m.get('status')!='PROVISIONAL_VARIANT' and m.get('reference_count',0)<2: errors.append(f"{m.get('mechanism_id')}: unsupported promotion")
 refs=jl(out/'creative_mechanism_phase2_2_1_calibration_reference_set.jsonl')
 refset={x.get('reference_id') for x in refs}
 if len(refset)<12: errors.append(f'calibration set must span at least 12 references; found {len(refset)}')
 if len(refset)!=13: errors.append(f'calibration set expected 13 selected references; found {len(refset)}')
 if sum(x.get('viewport_label')=='DESKTOP' for x in refs)!=sum(x.get('viewport_label')=='MOBILE' for x in refs): errors.append('calibration reference set is not paired across viewports')
 for x in refs:
  if x.get('observation_state')!='OBSERVED' or not x.get('scene_evidence_id') or not x.get('content_hash') or not x.get('archive_entry'): errors.append('calibration set has incomplete observed evidence')
 cases=json.loads((out/'creative_mechanism_phase2_2_1_renderability_cases.json').read_text())
 if cases.get('all_cases_production_ready') is not False: errors.append('calibration fixture cannot declare production ready')
 for c in cases.get('cases',[]):
  if not c.get('profile') or not c.get('retrieval_candidate_ids') or not c.get('scene_spec'): errors.append(f"{c.get('case_id')}: incomplete renderability fixture")
 legacy=jl(out/'creative_mechanism_phase2_2_1_legacy_relationships.jsonl')
 if len(legacy)<60: errors.append(f'legacy relationship ledger must preserve at least 60 frozen candidates; found {len(legacy)}')
 if any(x.get('relation')!='UNKNOWN' and not x.get('evidence_scene_ids') for x in legacy): errors.append('legacy relation claimed without scene evidence')
 jobs=json.loads((out/'creative_mechanism_phase2_2_1_scene_job_coverage.json').read_text())
 if any(not x.get('reference_ids') for x in jobs.get('jobs',[])): errors.append('calibration selection lacks one or more required Scene Jobs')
 return errors,agg
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-dir',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args();e,g=validate(a.source_dir,a.out_dir)
 print(json.dumps({'status':'FAIL' if e else 'PASS','errors':e,'aggregate':g},ensure_ascii=False,indent=2));sys.exit(1 if e else 0)
