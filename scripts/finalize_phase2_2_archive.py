"""Bind Phase 2.2 output ledgers to pinned, retrievable Library archives."""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

def readj(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
def writej(p,rows):p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def digest(b):return hashlib.sha256(b).hexdigest()
def finalize(out:Path,archive_dir:Path,mapping_path:Path,prior_zip:Path,prior_manifest_path:Path,prior_index_path:Path):
 mapping=json.loads(mapping_path.read_text());old=json.loads(prior_manifest_path.read_text());registry=json.loads((archive_dir/'archive_registry.json').read_text())
 archive_lookup={};capture_records={}
 for r in registry:
  meta=mapping.get(r['archive_id']);assert meta, f"Missing Library binding for {r['archive_id']}"
  p=archive_dir/r['filename'];assert digest(p.read_bytes())==r['container_sha256'],f"Container digest mismatch: {r['archive_id']}"
  assert meta.get('library_file_id') and meta.get('file_id') and meta.get('version_number') is not None
  r.update({'backend':'CHATGPT_LIBRARY','archive_status':'DURABLE_VERIFIED','library_file_id':meta['library_file_id'],'pinned_file_id':meta['file_id'],'version_id':str(meta['version_number']),'version_number':meta['version_number'],'archive_locator':f"https://chatgpt.com/api/library/files/{meta['library_file_id']}/download",'file_name':meta['file_name'],'file_size_bytes':meta.get('file_size_bytes'),'retention_policy':'Keep at least 3 years after last mechanism use; yearly recheck; version is pinned; no backend retention guarantee is asserted.','verification_policy':'At ingestion and before promotion/reuse, materialize the exact file_id and verify container SHA-256 and every referenced member; monthly retrieval check.','recapture_policy':'If URL content changes, access fails, or hash differs, preserve old record, recapture a new snapshot and re-review claims, scores, and mechanisms.','invalidation_policy':'Mismatch invalidates dependent score/mechanism promotion until re-observed and reviewed.','archive_loss_policy':'Fail closed: mark ARCHIVE_UNAVAILABLE and keep HOLD; never use missing evidence for rank or promotion.'})
  archive_lookup[r['archive_id']]=r
 # Include the previously verified Gold20 archive unchanged, plus its pinned locator.
 prior=archive_dir/prior_zip.name
 if not prior.exists():prior.write_bytes(prior_zip.read_bytes())
 assert digest(prior.read_bytes())==old['archive_sha256']
 oldr={'archive_id':old['archive_id'],'backend':'CHATGPT_LIBRARY','archive_status':'DURABLE_VERIFIED','library_file_id':old['library_file_id'],'pinned_file_id':old['file_id'],'version_id':str(old['version_number']),'version_number':old['version_number'],'archive_locator':old['download_url'],'file_name':old['file_name'],'filename':prior.name,'container_sha256':old['archive_sha256'],'path':str(prior),'entry_count':old['entry_count'],'reference_ids':[],'retention_policy':old['retention_policy'],'verification_policy':old['verification_policy'],'recapture_policy':old['recapture_policy'],'invalidation_policy':old['invalidation_policy'],'archive_loss_policy':old['archive_loss_policy']}
 archive_lookup[oldr['archive_id']]=oldr
 (out/'archive_registry.json').write_text(json.dumps([oldr]+registry,ensure_ascii=False,indent=2)+'\n')
 index=[x for x in readj(out/'creative_mechanism_phase2_2_archive_index.jsonl') if x.get('archive_id')!=oldr['archive_id']]
 for x in index:
  r=archive_lookup[x['archive_id']];x.update({'archive_status':'DURABLE_VERIFIED','backend':r['backend'],'library_file_id':r['library_file_id'],'pinned_file_id':r['pinned_file_id'],'version_id':r['version_id'],'archive_locator':r['archive_locator'],'container_sha256':r.get('container_sha256',r.get('archive_sha256'))})
 # Each reference also receives a durable locator to its exact capture attempt record.
 for r in registry:
  p=archive_dir/r['filename']
  with ZipFile(p) as z:
   manifest_bytes=z.read('manifest_subset.json');manifest=json.loads(manifest_bytes);manifest_hash=digest(manifest_bytes)
   for record in manifest.get('records',[]):capture_records[(record['reference_id'],record['viewport_label'])]=record
   for rid in manifest['reference_ids']:
    index.append({'archive_id':r['archive_id'],'archive_batch':r['archive_batch'],'reference_id':rid,'archive_entry':'manifest_subset.json','content_hash':manifest_hash,'content_type':'CAPTURE_ATTEMPT_MANIFEST','container_sha256':r['container_sha256'],'archive_status':'DURABLE_VERIFIED','backend':'CHATGPT_LIBRARY','library_file_id':r['library_file_id'],'pinned_file_id':r['pinned_file_id'],'version_id':r['version_id'],'archive_locator':r['archive_locator']})
 # Bring forward Phase 2.1.1 members for traceability of the already-reviewed five.
 prior_ix=readj(prior_index_path)
 with ZipFile(prior) as z:
  for x in prior_ix:
   entry=x['archive_entry'];need=entry in z.namelist()
   if need:assert digest(z.read(entry))==x['content_hash']
   if not need:continue
   name=entry.split('/',1)[1];rid=name.split('__',1)[0]
   index.append({'archive_id':oldr['archive_id'],'archive_batch':0,'reference_id':rid,'archive_entry':entry,'content_hash':x['content_hash'],'container_sha256':oldr['container_sha256'],'archive_status':'DURABLE_VERIFIED','backend':'CHATGPT_LIBRARY','library_file_id':oldr['library_file_id'],'pinned_file_id':oldr['pinned_file_id'],'version_id':oldr['version_id'],'archive_locator':oldr['archive_locator']})
 seen=set();index=[x for x in index if not ((x['archive_id'],x.get('reference_id'),x['archive_entry']) in seen or seen.add((x['archive_id'],x.get('reference_id'),x['archive_entry'])))]
 writej(out/'creative_mechanism_phase2_2_archive_index.jsonl',index)
 by_ref_entry={(x['reference_id'],x['archive_entry']):x for x in index}
 by_name=defaultdict(list)
 for x in index:by_name[(x['reference_id'],Path(x['archive_entry']).name)].append(x)
 scenes=readj(out/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl')
 for s in scenes:
  rid=s['reference_id'];crop=s.get('scene_crop_identifier')
  if crop:
   options=by_name.get((rid,crop),[]);x=next((a for a in options if a['archive_entry'].startswith(('scene_crops/','traversal/'))),None)
   if x:s.update({k:x[k] for k in ('archive_id','archive_status','archive_locator','archive_entry','content_hash','container_sha256','library_file_id','pinned_file_id','version_id') if k in x})
  elif s.get('screenshot_identifier'):
   options=by_name.get((rid,s['screenshot_identifier']),[]);x=next((a for a in options if a['archive_entry'].startswith('capture/')),None)
   if x:s.update({k:x[k] for k in ('archive_id','archive_status','archive_locator','archive_entry','content_hash','container_sha256','library_file_id','pinned_file_id','version_id') if k in x})
  if s.get('observation_state')!='OBSERVED':s['mechanism_candidates']=[]
 writej(out/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl',scenes)
 snaps=readj(out/'creative_mechanism_phase2_2_snapshots.jsonl')
 for s in snaps:
  # Preserve the original Phase 2.1 Gold snapshot's content-addressed archive link.
  if s.get('archive_status')=='DURABLE_VERIFIED' and s.get('archive_id')=='GOLD20-FULLPAGE-V1':
   s['storage_state']='DURABLE_VERIFIED'
   continue
  if not s.get('screenshot_identifier'):
   s.update({'archive_status':'NOT_CAPTURED','storage_state':'NOT_CAPTURED','archive_locator':None,'archive_entry':None})
   rec=next((x for x in registry if s['reference_id'] in x['reference_ids']),None)
   if rec:
    manifest_row=next(x for x in index if x.get('archive_id')==rec['archive_id'] and x.get('reference_id')==s['reference_id'] and x.get('content_type')=='CAPTURE_ATTEMPT_MANIFEST')
    s.update({'capture_log_archive_id':rec['archive_id'],'capture_log_archive_locator':rec['archive_locator'],'capture_log_archive_entry':'manifest_subset.json','capture_log_content_hash':manifest_row['content_hash'],'capture_log_archive_status':'DURABLE_VERIFIED'})
   continue
  options=by_name.get((s['reference_id'],Path(s['screenshot_identifier']).name),[]);x=next((a for a in options if a['archive_entry'].startswith('capture/')),None)
  if x:s.update({k:x[k] for k in ('archive_id','archive_status','archive_locator','archive_entry','content_hash','container_sha256','library_file_id','pinned_file_id','version_id') if k in x});s['storage_state']='DURABLE_VERIFIED'
 writej(out/'creative_mechanism_phase2_2_snapshots.jsonl',snaps)
 claims=readj(out/'creative_mechanism_phase2_2_claim_ledger.jsonl')
 scene_map={x['scene_evidence_id']:x for x in scenes}
 for c in claims:
  s=scene_map.get(c.get('scene_evidence_id'),{})
  if s:c.update({'archive_locator':s.get('archive_locator'),'archive_entry':s.get('archive_entry'),'content_hash':s.get('content_hash'),'archive_status':s.get('archive_status','NOT_CAPTURED')})
 writej(out/'creative_mechanism_phase2_2_claim_ledger.jsonl',claims)
 # Update reference archive status and corresponding risk rows without converting unknowns to PASS.
 ref_path=out/'creative_mechanism_phase2_2_reference_master.csv'
 with ref_path.open(newline='',encoding='utf-8') as f:refs=list(csv.DictReader(f));fields=list(refs[0])
 for r in refs:
  ss=[s for s in snaps if s['reference_id']==r['reference_id'] and s['viewport_label'] in ('DESKTOP','MOBILE')]
  r['archive_status']='DURABLE_VERIFIED' if all(x.get('archive_status')=='DURABLE_VERIFIED' for x in ss) and len({x['viewport_label'] for x in ss})==2 else 'PARTIAL_DURABLE_HOLD'
 with ref_path.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(refs)
 risks=readj(out/'creative_mechanism_phase2_2_risk_missingness.jsonl')
 ref_status={r['reference_id']:r['archive_status'] for r in refs}
 failures=[]
 for (rid,vp),record in capture_records.items():
  if record.get('capture_state')=='CAPTURED':continue
  ix=next(x for x in index if x.get('reference_id')==rid and x.get('content_type')=='CAPTURE_ATTEMPT_MANIFEST')
  failures.append({'reference_id':rid,'viewport_label':vp,'capture_state':'NOT_OBSERVED','original_url':record.get('original_url'),'final_url':record.get('final_url'),'http_status':record.get('http_status'),'error':record.get('error'),'captured_at':record.get('captured_at'),'archive_id':ix['archive_id'],'archive_locator':ix['archive_locator'],'archive_entry':ix['archive_entry'],'content_hash':ix['content_hash'],'archive_status':'DURABLE_VERIFIED','promotion_allowed':False})
 writej(out/'creative_mechanism_phase2_2_capture_failures.jsonl',failures)
 for x in risks:
  if x['risk_type']=='DURABLE_ARCHIVE':
   good=ref_status[x['reference_id']]=='DURABLE_VERIFIED';x['state']='DURABLE_VERIFIED' if good else 'HOLD_REVIEW_REQUIRED';x['reason']='All required desktop/mobile evidence snapshots have pinned retrievable archive records.' if good else 'At least one viewport evidence capture is absent or not durably archived.'
   if x['risk_type']=='CAPTURE_TARGET':
    missed=[f for f in failures if f['reference_id']==x['reference_id']]
    if missed:x['reason']='; '.join(f"{f['viewport_label']} HTTP {f.get('http_status')}: {f.get('error','')[:180]}" for f in missed);x['capture_failure_log_durable']=True
 writej(out/'creative_mechanism_phase2_2_risk_missingness.jsonl',risks)
 print(json.dumps({'archives':len(registry),'archive_members':len(index),'old_archive_verified':True,'scene_rows':len(scenes),'snapshot_rows':len(snaps),'claims':len(claims),'capture_failures':len(failures),'references':len(refs)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--archive-dir',type=Path,required=True);p.add_argument('--library-map',type=Path,required=True);p.add_argument('--prior-archive',type=Path,required=True);p.add_argument('--prior-manifest',type=Path,required=True);p.add_argument('--prior-index',type=Path,required=True);a=p.parse_args();finalize(a.output_dir,a.archive_dir,a.library_map,a.prior_archive,a.prior_manifest,a.prior_index)
