"""Assemble one uniform 100-reference view while retaining legacy evidence."""
from __future__ import annotations
import argparse,csv,json,urllib.parse
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def writej(p,rows):p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))
def loadcsv(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def writecsv(p,rows):
 fields=list(rows[0]);
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def domain(u):return urllib.parse.urlsplit(u or '').netloc.lower()
def main(capture_root,processed_dir,out):
 out.mkdir(parents=True,exist_ok=True)
 pilot=loadcsv(DATA/'creative_mechanism_phase2_pilot_references.csv')
 targets=json.loads((ROOT/'config/phase2_2_fullpage_capture_targets.json').read_text())
 assert len(pilot)==100 and len({x['reference_id'] for x in pilot})==100
 manifest=json.loads((capture_root/'capture_manifest.json').read_text())
 proc_scenes=lines(processed_dir/'creative_mechanism_phase2_2_fullpage_scenes.jsonl')
 proc_snaps=lines(processed_dir/'creative_mechanism_phase2_2_snapshots.jsonl')
 proc_coverage=json.loads((processed_dir/'creative_mechanism_phase2_2_traversal_coverage.json').read_text())
 base_scenes=lines(DATA/'creative_mechanism_phase2_1_1_fullpage_scenes.jsonl')
 base_snaps=lines(DATA/'creative_mechanism_phase2_1_gold_snapshots.jsonl')
 base_gold=loadcsv(DATA/'creative_mechanism_phase2_1_gold_references.csv')
 base_gold={x['reference_id']:x for x in base_gold}
 claims=lines(DATA/'creative_mechanism_phase2_1_claim_evidence.jsonl')+lines(DATA/'creative_mechanism_phase2_1_1_fullpage_claims.jsonl')+lines(processed_dir/'creative_mechanism_phase2_2_claims.jsonl')
 manifest_map={(x['reference_id'],x['viewport_label']):x for x in manifest['records']}
 coverage_map={(x['reference_id'],x['viewport_label']):x for x in proc_coverage}
 gold5={'P01-R01','P05-R04','P06-R02','P08-R02','P12-R01'}
 gold20=set(base_gold)
 masters=[];risks=[]
 for r in pilot:
  rid=r['reference_id'];is_gold=rid in gold20;fullpage_old=rid in gold5
  row=dict(r)
  if fullpage_old:
   ds=ms='CAPTURED';scope='PHASE_2_1_1_ARCHIVED_FULLPAGE'
  else:
   ds=manifest_map[rid,'DESKTOP'].get('capture_state','MISSING');ms=manifest_map[rid,'MOBILE'].get('capture_state','MISSING');scope='PHASE_2_2_FULLPAGE_CAPTURE'
  row.update({'desktop_fullpage_state':ds,'mobile_fullpage_state':ms,'fullpage_evidence_scope':scope,
   'archive_status':'DURABLE_VERIFIED' if fullpage_old else ('PENDING_ARCHIVE' if ds=='CAPTURED' or ms=='CAPTURED' else 'NOT_CAPTURED'),
   'score_scope':'NOT_SCORED_FULLPAGE','legacy_score_scope':base_gold[rid].get('score_scope') if is_gold else 'PHASE2_INITIAL_SCORE_UNAUDITED','legacy_score_status':'EVIDENCE_BACKED_SCOPED_ENTRY_FIRST_SCROLL' if is_gold else 'PROVISIONAL_UNAUDITED',
   'fullpage_score_status':'NOT_SCORED','corpus_ranking_allowed':False,'strong_promotion_allowed':False,'mechanism_promotion_allowed':False,
   'strong_hold_reject':'HOLD','decision_reason':'Full-page evidence added; full-page scoring, runtime testing and PM promotion review remain open.',
   'gold_status':'GOLD_EXISTING_FULLPAGE' if fullpage_old else ('GOLD_BACKFILL' if is_gold else 'REMAINING_80'),
   'desktop_capture_run_id':manifest_map.get((rid,'DESKTOP'),{}).get('capture_run_id','INHERITED_PHASE_2_1_1') if hasattr(manifest_map.get((rid,'DESKTOP'),{}),'get') else None,
   'mobile_capture_run_id':manifest_map.get((rid,'MOBILE'),{}).get('capture_run_id','INHERITED_PHASE_2_1_1') if hasattr(manifest_map.get((rid,'MOBILE'),{}),'get') else None,
   'fullpage_scene_count':sum(s['reference_id']==rid for s in (base_scenes if fullpage_old else proc_scenes))})
  masters.append(row)
  # Per-record independent risk states; Unknown remains unresolved, never PASS.
  source_url=r.get('discovery_source_url','');full_desktop=manifest_map.get((rid,'DESKTOP'),{});full_mobile=manifest_map.get((rid,'MOBILE'),{})
  desktop_domain=domain(full_desktop.get('final_url'));mobile_domain=domain(full_mobile.get('final_url'));expected=domain(r.get('canonical_url'))
  target_mismatch=bool((desktop_domain and expected and desktop_domain!=expected) or (mobile_domain and expected and mobile_domain!=expected))
  capture_missing=full_desktop.get('capture_state')!='CAPTURED' or full_mobile.get('capture_state')!='CAPTURED'
  if rid in gold5:target_mismatch=False;capture_missing=False
  regulated=r.get('industry') in ('FINANCE_INSURANCE','MEDICAL_DENTAL_CLINIC','BEAUTY_SALON_BODYCARE')
  pairs=[('DISCOVERY_TRACE',r.get('discovery_source_class')!='ORIGINAL_SITE_DIRECT' and not source_url.startswith('http'),'Source listing trace is generic or absent.'),
   ('CAPTURE_TARGET',target_mismatch or capture_missing,'Capture final URL mismatch or incomplete desktop/mobile capture.'),
   ('RESPONSIVE_SUBJECT',capture_missing,'Compare desktop and mobile subject before transfer; screenshots alone do not prove equivalent intent.'),
   ('TEMPORAL_MOTION',None,'Motion remains NOT_OBSERVED in still-image captures; hold only if a motion mechanism is proposed.'),
   ('ACCESSIBILITY_RUNTIME',r.get('industry') in ('MEDICAL_DENTAL_CLINIC','PUBLIC_NONPROFIT'),'Keyboard/focus/contrast/reduced-motion runtime was not tested.'),
   ('CLAIM_TERMS',regulated or any(x['reference_id']==rid for x in claims),'Verify visible claims and terms at claim-unit level.'),
   ('CROP_SELECTOR',False,'Full-page-derived crop is hash-linked; no selector-only crop establishes a mechanism.'),
   ('DURABLE_ARCHIVE',True,'New captures are pending archive until a pinned Library file and entry hash are verified.')]
  for typ,applies,reason in pairs:
   risks.append({'reference_id':rid,'risk_type':typ,'applicability':'CONDITIONAL' if applies is None else ('APPLICABLE' if applies else 'NOT_APPLICABLE'),
    'state':'NOT_OBSERVED' if applies is None else ('HOLD_REVIEW_REQUIRED' if applies else 'NOT_APPLICABLE'),'reason':reason,'strong_promotion_allowed':False,
    'claim_verification':'UNKNOWN' if typ=='CLAIM_TERMS' and applies else 'NOT_REQUIRED_OR_NOT_APPLICABLE'})
  for vp in ('DESKTOP','MOBILE'):
   if fullpage_old:
    c=next((x for x in base_scenes if x['reference_id']==rid and x['viewport_label']==vp),None)
    if c and c['observation_state']!='OBSERVED':risks.append({'reference_id':rid,'risk_type':'SCENE_MISSINGNESS','applicability':'APPLICABLE','state':c['observation_state'],'reason':c.get('missingness_reason'),'strong_promotion_allowed':False})
   else:
    cov=coverage_map[rid,vp]
    for job,item in cov['semantic_jobs'].items():
     if item['state']!='OBSERVED':risks.append({'reference_id':rid,'risk_type':'SCENE_'+job,'applicability':'APPLICABLE','state':item['state'],'reason':item.get('reason'),'strong_promotion_allowed':False})
 # Gold 20 legacy scene evidence is preserved as a separate scope; 5 full-page records are inherited.
 full_scenes=base_scenes+proc_scenes
 ids=[x['scene_evidence_id'] for x in full_scenes]
 assert len(ids)==len(set(ids))
 # Normalize viewport labels while preserving the original 1.2.1 snapshot rows.
 base_snaps=[dict(x,viewport_label=('DESKTOP' if (x.get('viewport') or {}).get('width')==1440 else 'MOBILE' if (x.get('viewport') or {}).get('width')==390 else 'UNKNOWN'),storage_state='DURABLE_VERIFIED') for x in base_snaps]
 role_map={'ENTRY':'ENTRY','PROBLEM':'PROBLEM_PROPOSITION_SOLUTION','PROPOSITION':'PROBLEM_PROPOSITION_SOLUTION','SOLUTION':'PROBLEM_PROPOSITION_SOLUTION','GUIDED':'PROBLEM_PROPOSITION_SOLUTION','SERVICE':'SERVICE_PRODUCT_EXPLANATION','PRODUCT':'SERVICE_PRODUCT_EXPLANATION','TECHNICAL':'SERVICE_PRODUCT_EXPLANATION','PROOF':'PROOF_TRUST','TRUST':'PROOF_TRUST','NEWS':'PROOF_TRUST','CASE':'PROOF_TRUST','HUMAN':'PROOF_TRUST','PERSON':'PROOF_TRUST','AUTHORITY':'PROOF_TRUST','CONVERSION':'CONVERSION_CTA','CTA':'CONVERSION_CTA','CLOSING':'CLOSING_FOOTER_NAVIGATION','FOOTER':'CLOSING_FOOTER_NAVIGATION','NAVIGATION':'CLOSING_FOOTER_NAVIGATION'}
 for s in base_scenes:
  if s.get('scene_role') and not s.get('scene_job'):
   role=str(s['scene_role']).upper();s['scene_job']=sorted(set(job for token,job in role_map.items() if token in role)) or ['UNCLASSIFIED']
 snapshots=base_snaps+proc_snaps
 present={(x['reference_id'],x['viewport_label']) for x in snapshots}
 for (rid,vp),rec in manifest_map.items():
  if (rid,vp) not in present and rec.get('capture_state')!='CAPTURED':
   snapshots.append({'snapshot_id':f'P22-SNAP-{rid}-{vp}-MISSING','reference_id':rid,'viewport_label':vp,'screenshot_identifier':None,'content_hash':None,'captured_at':rec.get('captured_at'),'viewport':rec.get('viewport'),'original_url':rec.get('original_url'),'final_url':rec.get('final_url'),'capture_state':'NOT_OBSERVED','missingness_reason':rec.get('error'),'archive_status':'NOT_CAPTURED','archive_locator':None,'archive_entry':None,'evidence_source_role':'ORIGINAL_LIVE','capture_run_id':manifest.get('run_id')})
 runtime=lines(processed_dir/'creative_mechanism_phase2_2_runtime_observations.jsonl')
 for rid in sorted(gold5):
  for vp,width in (('DESKTOP',1440),('MOBILE',390)):
   runtime.append({'runtime_observation_id':f'P22-RUNTIME-{rid}-{vp}','reference_id':rid,'viewport_label':vp,'capture_state':'INHERITED_PHASE_2_1_1','viewport':{'width':width},'motion_quality':'NOT_OBSERVED_STATIC_SCREENSHOTS_ONLY','site_reduced_motion_response':'NOT_OBSERVED_RUNTIME_NOT_TESTED','scroll_jank_observed':'NOT_OBSERVED_NOT_PERFORMANCE_PROFILED','blocking_animation':'NOT_OBSERVED_NOT_RUNTIME_PROFILED','heavy_video':'NOT_DETERMINED','keyboard_navigation':'NOT_OBSERVED','focus_visibility':'NOT_OBSERVED','contrast':'NOT_OBSERVED','alt_text_or_media_alternative':'NOT_OBSERVED_ACCESSIBILITY_AUDIT_NOT_RUN','heading_structure':'NOT_OBSERVED_ACCESSIBILITY_AUDIT_NOT_RUN','performance_metrics':'NOT_MEASURED'})
 semantic=proc_coverage.copy();covered={(x['reference_id'],x['viewport_label']) for x in semantic}
 for rid in sorted(gold5):
  for vp in ('DESKTOP','MOBILE'):
   if (rid,vp) in covered:continue
   observed_by=defaultdict(list)
   for s in base_scenes:
    if s['reference_id']!=rid or s['viewport_label']!=vp or s.get('observation_state')!='OBSERVED':continue
    role=str(s.get('scene_role','')).upper()
    for job in set(role for token,role in role_map.items() if token in role):
     observed_by[job].append(s['scene_evidence_id'])
   semantic.append({'reference_id':rid,'viewport_label':vp,'capture_state':'INHERITED_PHASE_2_1_1','semantic_jobs':{j:{'state':'OBSERVED' if observed_by[j] else 'NOT_OBSERVED','scene_evidence_ids':observed_by[j],'reason':None if observed_by[j] else 'No positive semantic scene evidence in inherited full-page traversal'} for j in ('ENTRY','PROBLEM_PROPOSITION_SOLUTION','SERVICE_PRODUCT_EXPLANATION','PROOF_TRUST','CONVERSION_CTA','CLOSING_FOOTER_NAVIGATION')}})
 # Canonical URL and brand duplicates remain explicit even when the initial matrix is expected unique.
 canon=defaultdict(list)
 for r in masters:
  u=urllib.parse.urlsplit(r.get('canonical_url') or '');q=urllib.parse.urlencode(sorted((k,v) for k,v in urllib.parse.parse_qsl(u.query) if not k.lower().startswith('utm_')))
  canon[f'{u.scheme.lower()}://{u.netloc.lower()}{u.path.rstrip("/") or "/"}'+(f'?{q}' if q else '')].append(r['reference_id'])
 duplicates=[{'canonical_key':k,'reference_ids':v} for k,v in canon.items() if len(v)>1]
 writecsv(out/'creative_mechanism_phase2_2_reference_master.csv',masters)
 writej(out/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl',full_scenes)
 writej(out/'creative_mechanism_phase2_2_snapshots.jsonl',snapshots)
 writej(out/'creative_mechanism_phase2_2_claim_ledger.jsonl',claims)
 writej(out/'creative_mechanism_phase2_2_runtime_observations.jsonl',runtime)
 writej(out/'creative_mechanism_phase2_2_semantic_job_coverage.jsonl',semantic)
 writej(out/'creative_mechanism_phase2_2_risk_missingness.jsonl',risks)
 writej(out/'creative_mechanism_phase2_2_canonical_url_duplicates.jsonl',duplicates)
 (out/'creative_mechanism_phase2_2_capture_coverage.json').write_text(json.dumps(proc_coverage,ensure_ascii=False,indent=2)+'\n')
 # Validation coverage is intentionally a 20-cell roll-up, independent of market quota.
 cell_rows=[];byref={x['reference_id']:x for x in masters}
 for cell in loadcsv(DATA/'creative_mechanism_phase1_2_pilot_coverage_matrix.csv'):
  group=[x for x in masters if x['slot_id']==cell['slot_id']]
  group_ids={x['reference_id'] for x in group};ss=[x for x in full_scenes if x['reference_id'] in group_ids]
  jobs=defaultdict(int)
  for s in ss:
   sj=s.get('scene_job') or []
   if isinstance(sj,str):sj=[sj]
   if s.get('observation_state')=='OBSERVED':
    for j in sj:jobs[j]+=1
  cell_rows.append({'slot_id':cell['slot_id'],'pool_type':cell['pool_type'],'business_archetype':cell['business_archetype'],'industry':cell['industry'],'market_scope':cell['market_scope'],'discovery_source_class':cell['discovery_source_class'],'planned_count':cell['planned_count'],'reference_count':len(group),'both_viewports_durable_count':sum(x['archive_status']=='DURABLE_VERIFIED' for x in group),'partial_or_missing_archive_count':sum(x['archive_status']!='DURABLE_VERIFIED' for x in group),'scene_count':len(ss),'observed_scene_count':sum(x['observation_state']=='OBSERVED' for x in ss),'not_observed_scene_count':sum(x['observation_state']=='NOT_OBSERVED' for x in ss),'observed_job_counts':json.dumps(jobs,ensure_ascii=False,sort_keys=True)})
 writecsv(out/'creative_mechanism_phase2_2_coverage_matrix.csv',cell_rows)
 print(json.dumps({'references':len(masters),'fullpage_scenes':len(full_scenes),'snapshots':len(snapshots),'claims':len(claims),'risk_rows':len(risks),'canonical_url_duplicates':len(duplicates),'capture_results':len(manifest['records'])}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture-root',type=Path,required=True);p.add_argument('--processed-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.capture_root,a.processed_dir,a.out)
