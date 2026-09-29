"""Fail-closed validation for the uniform 100-reference Phase 2.2 package."""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
def readj(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(b):return hashlib.sha256(b).hexdigest()
def loadcsv(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def validate(out:Path,archive:Path):
 errors=[]
 def need(ok,msg):
  if not ok:errors.append(msg)
 refs=loadcsv(out/'creative_mechanism_phase2_2_reference_master.csv')
 pilot=loadcsv(DATA/'creative_mechanism_phase2_pilot_references.csv')
 matrix=loadcsv(DATA/'creative_mechanism_phase1_2_pilot_coverage_matrix.csv')
 scenes=readj(out/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl')
 semantic=readj(out/'creative_mechanism_phase2_2_semantic_job_coverage.jsonl')
 snapshots=readj(out/'creative_mechanism_phase2_2_snapshots.jsonl')
 risks=readj(out/'creative_mechanism_phase2_2_risk_missingness.jsonl')
 claims=readj(out/'creative_mechanism_phase2_2_claim_ledger.jsonl')
 failures=readj(out/'creative_mechanism_phase2_2_capture_failures.jsonl')
 candidates=readj(out/'creative_mechanism_phase2_2_mechanism_candidates.jsonl')
 duplicates=readj(out/'creative_mechanism_phase2_2_canonical_url_duplicates.jsonl')
 need(len(refs)==100,'Reference count != 100')
 ids=[r['reference_id'] for r in refs];need(len(set(ids))==100,'Duplicate reference_id')
 need(set(ids)=={r['reference_id'] for r in pilot},'100 pilot membership changed')
 need(not duplicates,'Canonical URL duplicates exist')
 gold_ids={x['reference_id'] for x in loadcsv(DATA/'creative_mechanism_phase2_1_gold_references.csv')}
 need(all(r.get('score_scope')=='NOT_SCORED_FULLPAGE' and r.get('fullpage_score_status')=='NOT_SCORED' and r.get('corpus_ranking_allowed')=='False' and r.get('strong_promotion_allowed')=='False' and r.get('mechanism_promotion_allowed')=='False' for r in refs),'Full-page score/ranking/promotion scope is not fail-closed')
 need(all((r.get('legacy_score_status')=='EVIDENCE_BACKED_SCOPED_ENTRY_FIRST_SCROLL') if r['reference_id'] in gold_ids else (r.get('legacy_score_status')=='PROVISIONAL_UNAUDITED') for r in refs),'Legacy score scope/status drifted')
 # Preserve 20 matrix cells with five references per slot/cell.
 pilot_cell=Counter(r.get('slot_id') for r in pilot)
 need(len(pilot_cell)==20 and set(pilot_cell.values())=={5},'Pilot matrix is not 20 cells x 5')
 for row in matrix:
  matching=[r for r in pilot if r.get('slot_id')==row.get('slot_id')]
  if row.get('slot_id') is not None: need(len(matching)==5,f"Matrix cell count changed: {row.get('slot_id')}")
 sceneids=[s['scene_evidence_id'] for s in scenes]
 need(len(sceneids)==len(set(sceneids)),'Duplicate scene_evidence_id')
 need(set(ids)<=set(s['reference_id'] for s in scenes),'Some references lack full-page scene ledger rows')
 byref=defaultdict(list)
 for s in scenes:byref[s['reference_id']].append(s)
 for rid in ids:
  ss=byref[rid]
  need(any(s.get('viewport_label')=='DESKTOP' for s in ss),f'{rid}: desktop full-page rows missing')
  need(any(s.get('viewport_label')=='MOBILE' for s in ss),f'{rid}: mobile full-page rows missing')
  for s in byref[rid]:
   state=s.get('observation_state')
   need(state in {'OBSERVED','MISSING','NOT_OBSERVED','NOT_APPLICABLE'},f"{s.get('scene_evidence_id')}: missingness state invalid")
   if state=='OBSERVED':
    need(bool(s.get('concrete_locator')) and bool(s.get('observed_facts')),f"{s.get('scene_evidence_id')}: observed evidence is not concrete")
    need(bool(s.get('screenshot_identifier') or s.get('scene_crop_identifier')),f"{s.get('scene_evidence_id')}: observed scene lacks capture ID")
   else: need(not s.get('mechanism_candidates'),f"{s.get('scene_evidence_id')}: non-observed scene has mechanisms")
 need(len(semantic)==200,'Semantic Scene coverage must be explicit for 100 refs x 2 viewports')
 expected_jobs={'ENTRY','PROBLEM_PROPOSITION_SOLUTION','SERVICE_PRODUCT_EXPLANATION','PROOF_TRUST','CONVERSION_CTA','CLOSING_FOOTER_NAVIGATION'}
 for row in semantic:
  need(row.get('reference_id') in set(ids) and row.get('viewport_label') in {'DESKTOP','MOBILE'},'Invalid semantic coverage key')
  need(set(row.get('semantic_jobs',{}))==expected_jobs,f"{row.get('reference_id')}: semantic job coverage incomplete")
  for job,item in row.get('semantic_jobs',{}).items():
   need(item.get('state') in {'OBSERVED','NOT_OBSERVED','NOT_APPLICABLE','MISSING'},f"{row.get('reference_id')}/{job}: implicit missingness")
   if item.get('state')!='OBSERVED':need(not item.get('scene_evidence_ids'),f"{row.get('reference_id')}/{job}: non-observed job has evidence IDs")
   else:
    need(bool(item.get('scene_evidence_ids')),f"{row.get('reference_id')}/{job}: observed job lacks scene IDs")
    need(all(any(s['scene_evidence_id']==sid and s['observation_state']=='OBSERVED' for s in scenes) for sid in item['scene_evidence_ids']),f"{row.get('reference_id')}/{job}: provenance is not observed-only")
 # Per-view capture and archive evidence.
 viewset={(s.get('reference_id'),s.get('viewport_label')) for s in snapshots}
 for rid in ids:
  for vp in ('DESKTOP','MOBILE'):
   need((rid,vp) in viewset,f'{rid}/{vp}: snapshot row missing')
 index=readj(out/'creative_mechanism_phase2_2_archive_index.jsonl')
 registry=json.loads((out/'archive_registry.json').read_text())
 need(bool(registry),'Archive registry empty')
 reg={x['archive_id']:x for x in registry}
 zips=list(archive.glob('*.zip'))
 need(len(zips)==len(registry), 'Local archive batch count does not match registry')
 for rec in registry:
  p=archive/rec['filename']
  need(p.exists(),f"Archive missing: {rec['filename']}")
  if not p.exists():continue
  b=p.read_bytes();need(sha(b)==rec['container_sha256'],f"Archive container SHA mismatch: {rec['archive_id']}")
  need(rec.get('archive_status')=='DURABLE_VERIFIED',f"Archive not durable-verified: {rec['archive_id']}")
  need(bool(rec.get('library_file_id') and rec.get('pinned_file_id') and rec.get('version_id') is not None),f"Archive locator not pinned: {rec['archive_id']}")
  need(rec.get('archive_locator')==f"https://chatgpt.com/api/library/files/{rec.get('library_file_id')}/download",f"Archive locator malformed: {rec['archive_id']}")
  with ZipFile(p) as z:
   members=set(z.namelist())
   if rec['archive_id']!='GOLD20-FULLPAGE-V1':need('manifest_subset.json' in members,f"Manifest absent in {rec['archive_id']}")
   for row in [x for x in index if x['archive_id']==rec['archive_id']]:
    need(row['archive_entry'] in members,f"Archive entry missing {row['archive_entry']}")
    if row['archive_entry'] in members:need(sha(z.read(row['archive_entry']))==row['content_hash'],f"Entry SHA mismatch: {row['archive_entry']}")
 # Every archive-backed scene/snapshot points to exact member/hash.
 idx={(x['reference_id'],x['archive_entry']):x for x in index}
 for s in scenes+snapshots:
  if s.get('archive_status')=='DURABLE_VERIFIED':
   need(bool(s.get('archive_locator') and s.get('archive_entry') and s.get('content_hash')),f"{s.get('scene_evidence_id',s.get('snapshot_id'))}: incomplete archive link")
   match=next((x for x in index if x.get('archive_id')==s.get('archive_id') and x.get('reference_id')==s.get('reference_id') and x.get('archive_entry')==s.get('archive_entry')),None)
   need(match is not None,f"Evidence archive entry not indexed: {s.get('archive_entry')}")
   if match:need(match['content_hash']==s.get('content_hash'),f"Evidence hash mismatch: {s.get('archive_entry')}")
  if s.get('capture_log_archive_status')=='DURABLE_VERIFIED':
   row=next((x for x in index if x.get('archive_id')==s.get('capture_log_archive_id') and x.get('reference_id')==s.get('reference_id') and x.get('content_type')=='CAPTURE_ATTEMPT_MANIFEST'),None)
   need(bool(row) and row.get('content_hash')==s.get('capture_log_content_hash') and row.get('archive_locator')==s.get('capture_log_archive_locator'),f"{s.get('snapshot_id')}: durable capture-failure log link invalid")
 need(all(x.get('archive_status')=='DURABLE_VERIFIED' and x.get('archive_locator') and x.get('archive_entry')=='manifest_subset.json' and len(x.get('content_hash',''))==64 for x in failures),'Capture failures lack durable attempt evidence')
 need(all(x.get('promotion_allowed') is False for x in failures),'Capture failure marked promotion-eligible')
 # Provenance and all counts are recomputed from observed scene IDs.
 refmap={r['reference_id']:r for r in refs}
 for c in candidates:
  src=c.get('source_scene_evidence_ids',[]);need(bool(src),f"{c.get('mechanism_id')}: empty provenance")
  source=[s for s in scenes if s['scene_evidence_id'] in src]
  need(len(source)==len(set(src)),f"{c.get('mechanism_id')}: unknown/duplicate scene IDs")
  need(all(s.get('observation_state')=='OBSERVED' for s in source),f"{c.get('mechanism_id')}: non-observed provenance")
  need(c.get('evidence_count')==len(set(src)),f"{c.get('mechanism_id')}: evidence count not derived")
  rids={s['reference_id'] for s in source}; brands={refmap[r]['brand'] for r in rids}
  need(set(c.get('reference_lps',[]))==rids and c.get('reference_count')==len(rids),f"{c.get('mechanism_id')}: reference count not derived")
  need(c.get('brand_count')==len(brands) and c.get('unique_brand_count')==len(brands),f"{c.get('mechanism_id')}: brand count not derived")
  need(c.get('status')=='CANDIDATE' and c.get('promotion_allowed') is False,f"Unsupported promotion: {c.get('mechanism_id')}")
  need(c.get('unique_agency_count')=='UNKNOWN' or isinstance(c.get('unique_agency_count'),int),f"{c.get('mechanism_id')}: invalid agency independence")
  need(c.get('unique_campaign_count')=='UNKNOWN' or isinstance(c.get('unique_campaign_count'),int),f"{c.get('mechanism_id')}: invalid campaign independence")
 # Risk ledger must preserve each record and explicit unknowns.
 risk_refs={x['reference_id'] for x in risks};need(set(ids)<=risk_refs,'Risk/missingness ledger missing references')
 need(any(x.get('risk_type')=='TEMPORAL_MOTION' and x.get('state')=='NOT_OBSERVED' for x in risks),'Motion NOT_OBSERVED state missing')
 need(len(readj(out/'creative_mechanism_phase2_2_runtime_observations.jsonl'))==200,'Runtime/motion/accessibility missingness must cover 100 x 2 viewports')
 # Claim truth must never be promoted from visible page text.
 need(all(c.get('claim_truth') in (None,'UNKNOWN') and c.get('evidence_status')!='VERIFIED_TRUE' for c in claims),'Claim text incorrectly treated as verified truth')
 cfg=json.loads((ROOT/'config/creative_mechanism_db_architecture_v1_3_1.json').read_text())
 gate=cfg.get('phase2_gate',{})
 need(cfg.get('status')=='PHASE_2_2_100_REFERENCE_PILOT_READY_FOR_PM_REVIEW','Architecture status does not match Phase 2.2 review gate')
 need(gate.get('remaining_80_allowed') is True,'Remaining80 gate not open')
 need(gate.get('bulk_collection_allowed') is False,'2,600 bulk gate is not held')
 need(gate.get('collection_started') is True,'Pilot collection state invalid')
 need(cfg.get('phase2_2_completion',{}).get('bulk_2600_allowed') is False,'Completion status must keep 2,600 gate false')
 report={'status':'PASS' if not errors else 'FAIL','errors':errors,'reference_count':len(refs),'scene_count':len(scenes),'scene_states':dict(Counter(x['observation_state'] for x in scenes)),'snapshot_count':len(snapshots),'snapshot_durable_count':sum(x.get('archive_status')=='DURABLE_VERIFIED' for x in snapshots),'scene_durable_count':sum(x.get('archive_status')=='DURABLE_VERIFIED' for x in scenes),'semantic_coverage_rows':len(semantic),'runtime_observation_rows':len(readj(out/'creative_mechanism_phase2_2_runtime_observations.jsonl')),'archive_batch_count':len(registry),'archive_index_entries':len(index),'capture_failure_records':len(failures),'claim_count':len(claims),'risk_row_count':len(risks),'candidate_count':len(candidates),'exact_rule_family_count':len({x['mechanism_id'] for x in candidates}),'all_candidates_unpromoted':all(x.get('status')=='CANDIDATE' for x in candidates),'phase2600_allowed':gate.get('bulk_collection_allowed')}
 (out/'creative_mechanism_phase2_2_qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 if errors:
  print(json.dumps(report,ensure_ascii=False,indent=2));return 1
 print(json.dumps(report,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--archive-dir',type=Path,required=True);a=p.parse_args();raise SystemExit(validate(a.output_dir,a.archive_dir))
