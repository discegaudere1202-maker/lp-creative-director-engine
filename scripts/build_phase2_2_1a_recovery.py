"""Integrated capture recovery builder: verified bytes, explicit QA, immutable originals.

No calibration, rendering verdict, ranking or expansion promotion is produced.
Archive paths are local CLI inputs; archive identities and digests are version pinned.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,zipfile,re
from collections import defaultdict,Counter
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO
from validate_phase2_2_1a_replacement import validate,CELL

PILOT_SHA='dc6a369ac79f93a9e83aa0c75073757181c5bee15c892627f1cb5f06c2982c4d'
FAILURE_SHA='9ca6f2608452851885d763fd3c8efee4f996bc97a28461aff30b295db172b67e'
VP={'DESKTOP':{'width':1440,'height':1000},'MOBILE':{'width':390,'height':844}}
GATES=('final_usable_reference_count','desktop_1440_durable_count','mobile_390_durable_count','both_viewports_durable_count')
STOP='PHASE_2_2_1_CAPTURE_RECOVERY_READY_FOR_PM_REVIEW'

def sha(data):return hashlib.sha256(data).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def jl(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def json_file(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def json_lines(path,rows):path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
def csv_file(path,rows):
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def durable(row):return row.get('archive_status')=='DURABLE_VERIFIED' and row.get('archive_entry') and row.get('archive_entry')!='manifest_subset.json' and row.get('content_hash') and row.get('archive_locator')
def hard_gate(counts):return all(counts.get(k)==100 for k in GATES)
def archive_binding(reg):
    return {'archive_id':reg['archive_id'],'archive_status':'DURABLE_VERIFIED','backend':'CHATGPT_LIBRARY','archive_locator':reg['archive_locator'],'library_file_id':reg['library_file_id'],'pinned_file_id':reg['pinned_file_id'],'version_id':str(reg['version_id']),'container_sha256':reg['container_sha256']}

def build(source,archive_dir,inputs,out):
    source=Path(source);archive_dir=Path(archive_dir);inputs=Path(inputs);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    require(sha((root/'data/creative_mechanism_phase2_pilot_references.csv').read_bytes())==PILOT_SHA,'original pilot changed')
    require(sha((root/'data/creative_mechanism_phase2_2_1_failure_recovery_ledger.jsonl').read_bytes())==FAILURE_SHA,'original failure ledger changed')
    config=json.loads((inputs/'recovery_inputs.json').read_text())
    require(config['phase2600_allowed'] is False,'expansion prohibited')
    for name,digest in config['source_file_sha256'].items():require(sha((source/name).read_bytes())==digest,'source changed: '+name)
    registry=json.loads((source/'archive_registry.json').read_text())+config['production_archives']
    require(len({r['archive_id'] for r in registry})==len(registry),'duplicate container id')
    zips={};verification=[]
    for r in registry:
        require(r['backend']=='CHATGPT_LIBRARY' and r['archive_status']=='DURABLE_VERIFIED','not durable')
        require(r['library_file_id'].startswith('libfile_') and r['pinned_file_id'].startswith('file_') and str(r['version_id'])=='0','unpinned archive')
        path=archive_dir/r.get('file_name',r.get('filename'))
        require(sha(path.read_bytes())==r['container_sha256'],'container hash mismatch: '+r['archive_id'])
        z=zipfile.ZipFile(path);require(z.testzip() is None,'ZIP corrupt')
        require(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()),'unsafe ZIP member')
        zips[r['archive_id']]=z
        verification.append({'archive_id':r['archive_id'],'container_sha256':r['container_sha256'],'zip_integrity':'PASS','verified_member_count':0})
    regs={r['archive_id']:r for r in registry};verified=set()
    def member(row):
        aid=row['archive_id'];name=row['archive_entry']
        data=zips[aid].read(name);require(sha(data)==row['content_hash'],'member hash mismatch: '+name)
        require(row.get('container_sha256',row.get('archive_container_sha256',regs[aid]['container_sha256']))==regs[aid]['container_sha256'],'container binding mismatch')
        verified.add((aid,name));return data
    master0=read_csv(source/'creative_mechanism_phase2_2_reference_master.csv')
    pilot=read_csv(root/'data/creative_mechanism_phase2_pilot_references.csv');require(len(pilot)==len(master0)==100,'original count changed')
    require({x['reference_id'] for x in pilot}=={x['reference_id'] for x in master0},'source IDs changed')
    originals={r['reference_id']:r for r in pilot};fail0=jl(root/'data/creative_mechanism_phase2_2_1_failure_recovery_ledger.jsonl')
    failids={r['reference_id'] for r in fail0};require(len(failids)==27,'original failure count changed')
    snaps=jl(source/'creative_mechanism_phase2_2_snapshots.jsonl');scenes=jl(source/'creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl')
    index=jl(source/'creative_mechanism_phase2_2_archive_index.jsonl');coverage=json.loads((source/'creative_mechanism_phase2_2_capture_coverage.json').read_text())
    for x in index:member(x)
    byref=defaultdict(set);scene_vp=defaultdict(set)
    for x in snaps:
        if durable(x):
            member(x);v=x.get('viewport_label') or ('DESKTOP' if x['viewport']['width']==1440 else 'MOBILE' if x['viewport']['width']==390 else None)
            require(x['viewport']['width']==VP[v]['width'],'original viewport invalid');byref[x['reference_id']].add(v)
    for x in scenes:
        if x.get('observation_state')=='OBSERVED' and durable(x):member(x);scene_vp[x['reference_id']].add(x['viewport_label'])
    # Legacy five have durably hashed full-page traversal scene sequences in the source bundle.
    traversal_vp=defaultdict(set)
    for x in coverage:
        if x['capture_state']=='CAPTURED':traversal_vp[x['reference_id']].add(x['viewport_label'])
    for rid in ('P01-R01','P05-R04','P06-R02','P08-R02','P12-R01'):
        require(scene_vp[rid]==set(VP),'legacy full-page scenes missing');traversal_vp[rid]=set(VP)
    oldusable={rid for rid in originals if byref[rid]==scene_vp[rid]==traversal_vp[rid]==set(VP)}
    require(len(oldusable)==73 and oldusable.isdisjoint(failids),'original 73 not proved')
    decisions={x['attempt_id']:x for x in jl(inputs/'official_visual_qa.jsonl')}
    attempts=[];accepted={};candidates_all=[];new_snaps=[];new_scenes=[]
    for batch in config['batches']:
        candidates=jl(inputs/batch['candidate_ledger']);validate(candidates,'approved_batch');candidates_all+=candidates
        cmap={x['replacement_reference_id']:x for x in candidates};reg=regs[batch['archive_id']];z=zips[batch['archive_id']]
        raw=z.read('capture_manifest.json');manifest_digest=sha(raw)
        require(z.read('manifest.sha256').decode().split()[0]==manifest_digest,'manifest hash mismatch')
        manifest=json.loads(raw);require(manifest['mode']=='approved_batch' and manifest['phase2600_allowed'] is False,'nonproduction manifest')
        require(set(cmap)=={x['replacement_reference_id'] for x in manifest['records']},'manifest/candidate mismatch')
        binding=archive_binding(reg)
        index.append(dict(binding,reference_id=None,archive_entry='capture_manifest.json',content_hash=manifest_digest,member_kind='CAPTURE_MANIFEST',run_id=batch['run_id']))
        for rec in manifest['records']:
            rid=rec['replacement_reference_id'];candidate=cmap[rid];fid=candidate['replaces_reference_id'];attempt_id=f"{batch['run_id']}:{rid}"
            require(attempt_id in decisions,'explicit actual image/official review required: '+attempt_id);qa=decisions[attempt_id]
            require(rec['replaces_reference_id']==fid and rec['requested_url']==candidate['original_official_url'],'record target changed')
            require(all(rec['replacement_metadata'][k]==candidate[k]==originals[fid][k] for k in CELL),'same-cell mismatch')
            require(rec['production_eligible'] is True and rec['record_kind']=='PRODUCTION_CANDIDATE','smoke row')
            views={v['viewport_label']:v for v in rec['viewports']};require(set(views)==set(VP),'viewports missing')
            image_rows=[]
            for label,v in views.items():
                require(v['viewport']==VP[label],'wrong viewport')
                for s in v.get('screenshots',[]):
                    row=dict(binding,reference_id=rid,archive_entry=s['screenshot_identifier'],content_hash=s['content_sha256'],member_kind=s['kind'],viewport_label=label,run_id=batch['run_id'])
                    data=member(row);im=Image.open(BytesIO(data));im.verify();require(Image.open(BytesIO(data)).width==VP[label]['width'],'pixel width mismatch')
                    index.append(row);image_rows.append(row)
            accept=qa['visual_state']=='PASS' and qa['official_state']=='PASS' and rec['capture_state']=='CAPTURED_TEMPORARY'
            attempt=dict(qa,reference_id=rid,replaces_reference_id=fid,slot_id=candidate['slot_id'],candidate=candidate,candidate_sha=batch['candidate_sha'],capture_state=rec['capture_state'],failure_class=rec.get('failure_class'),http_statuses=rec['http_statuses'],manifest_sha256=manifest_digest,artifact_id=batch['artifact_id'],artifact_digest=batch['artifact_digest'],run_id=batch['run_id'],accepted=accept,archive=binding,manifest_entry='capture_manifest.json',viewports=rec['viewports'])
            attempts.append(attempt)
            if not accept:continue
            require(fid not in accepted,'two accepted replacements for one slot')
            require(fid in failids and fid not in oldusable,'replacing usable original')
            require(candidate['original_official_url'].rstrip('/') not in {o['url'].rstrip('/') for o in pilot},'reusing original URL')
            require(candidate['slot_id']==originals[fid]['slot_id'],'slot changed')
            require('ORIGINAL_LIVE' in candidate['evidence_source_roles'] or 'OFFICIAL_BRAND' in candidate['evidence_source_roles'],'official role missing')
            for label,v in views.items():
                require(v['capture_state']=='CAPTURED_TEMPORARY' and 200<=v['http_status']<300,'failed viewport accepted')
                t=v['traversal_facts'];require(t['state']=='OBSERVED' and t['complete_to_bottom'] is True,'no complete traversal')
                require(t['final_height']>VP[label]['height'] and t['final_height']<=30000,'locked or incomplete page')
                if t.get('position_measurement')=='ACTUAL_WINDOW_SCROLLY':
                    end=t['scroll_samples'][-1];require(end['scroll_y']+end['viewport_height']>=t['final_height']-2 and t['stable_bottom_samples']>=2,'bottom not reached')
                facts=v['page_facts'];require(facts['inner_width']==VP[label]['width'],'viewport facts mismatch')
                observed=(facts['title']+' '+facts['visible_text']).casefold();require(any(token.casefold() in observed for token in qa['official_identity_tokens']),'official identity missing')
                require(urlparse(facts['url']).hostname in qa['verified_final_hosts'],'unreviewed redirect')
                vp_images=[x for x in image_rows if x['viewport_label']==label];kinds={x['member_kind'] for x in vp_images}
                require({'VIEWPORT','FULL_PAGE'}<=kinds,'viewport/full-page pixels missing')
                for s in vp_images:
                    im=Image.open(BytesIO(member(s)))
                    require(im.height==(VP[label]['height'] if s['member_kind']=='VIEWPORT' else t['final_height']),'pixel height mismatch')
                    snapshot=dict(s,snapshot_id=f"P221A-{batch['run_id']}-{rid}-{label}-{s['member_kind']}",viewport=VP[label],original_url=rec['requested_url'],final_url=facts['url'],captured_at=v['captured_at'],manifest_entry='capture_manifest.json',manifest_sha256=manifest_digest)
                    new_snaps.append(snapshot)
                    new_scenes.append(dict(snapshot,scene_evidence_id=snapshot['snapshot_id']+'-SCENE',scene_role='ENTRY' if s['member_kind']=='VIEWPORT' else 'FULL_PAGE_TRAVERSAL',observation_state='OBSERVED',page_y_range=[0,im.height],parent_snapshot_id=snapshot['snapshot_id'],observed_facts=[facts['title'],'Static pixels audited; full-page traversal recorded in capture manifest.'],motion_observation='NOT_OBSERVED_STATIC_PIXEL_CAPTURE',interaction_observation='NOT_OBSERVED_EXCEPT_NON_BINDING_DISMISS_RECORDED_IN_MANIFEST',score_scope='FULL_PAGE_STATIC_OBSERVATION_ONLY'))
            accepted[fid]=(candidate,rec,batch,qa)
    require(len({a['attempt_id'] for a in attempts})==len(attempts),'duplicate attempt')
    require(set(decisions)=={a['attempt_id'] for a in attempts},'QA references unknown attempt')
    all_snaps=snaps+new_snaps;all_scenes=scenes+new_scenes
    master=[]
    for r in master0:
        usable=r['reference_id'] in oldusable
        master.append(dict(r,record_origin='ORIGINAL_PILOT_IMMUTABLE_SOURCE',active_in_recovered_corpus=str(usable).lower(),usable_reference_derived=str(usable).lower(),desktop_durable_derived=str(usable).lower(),mobile_durable_derived=str(usable).lower(),both_viewports_durable_derived=str(usable).lower(),fullpage_traversal_derived=str(usable).lower(),replacement_reference_id=accepted.get(r['reference_id'],({},))[0].get('replacement_reference_id',''),phase2600_allowed='false'))
    for a in attempts:
        c=a['candidate'];valid=a['accepted']
        # Original scores and mechanisms are never transferred to a new brand.
        master.append(dict(reference_id=a['reference_id'],slot_id=c['slot_id'],brand=c['brand'],url=c['original_official_url'],canonical_url=a['viewports'][-1].get('final_url'),**{k:c[k] for k in CELL},discovery_source_url=c['discovery_source_url'],evidence_source_roles=json.dumps(c['evidence_source_roles']),record_origin='REPLACEMENT_ATTEMPT',replaces_reference_id=a['replaces_reference_id'],active_in_recovered_corpus=str(valid).lower(),usable_reference_derived=str(valid).lower(),desktop_durable_derived=str(valid).lower(),mobile_durable_derived=str(valid).lower(),both_viewports_durable_derived=str(valid).lower(),fullpage_traversal_derived=str(valid).lower(),fullpage_score_status='NOT_SCORED_CAPTURE_RECOVERY_ONLY',corpus_ranking_allowed='false',strong_promotion_allowed='false',mechanism_promotion_allowed='false',phase2600_allowed='false'))
    active=[r for r in master if r['active_in_recovered_corpus']=='true']
    require(len({r['reference_id'] for r in master})==len(master),'master IDs duplicated')
    matrix=[]
    for slot in sorted({o['slot_id'] for o in pilot}):
        pp=[r for r in pilot if r['slot_id']==slot];rr=[r for r in active if r['slot_id']==slot]
        require(all(all(r[k]==pp[0][k] for k in CELL) for r in rr),'matrix cell mismatch')
        matrix.append(dict(slot_id=slot,**{k:pp[0][k] for k in CELL},original_reference_count=len(pp),original_usable_count=sum(r['record_origin']=='ORIGINAL_PILOT_IMMUTABLE_SOURCE' for r in rr),successful_replacement_count=sum(r['record_origin']=='REPLACEMENT_ATTEMPT' for r in rr),final_usable_reference_count=len(rr),desktop_1440_durable_count=len(rr),mobile_390_durable_count=len(rr),both_viewports_durable_count=len(rr)))
    counts={k:sum(r[k] for r in matrix) for k in GATES}
    counts.update(original_attempted=100,original_usable=len(oldusable),candidate_attempts=len(attempts),successful_replacements=len(accepted),failed_attempts=sum(not a['accepted'] for a in attempts),capture_failed_attempts=sum(a['capture_state']!='CAPTURED_TEMPORARY' for a in attempts),visual_qa_rejected_attempts=sum(a['capture_state']=='CAPTURED_TEMPORARY' and not a['accepted'] for a in attempts),reference_master_row_count=len(master),snapshot_count=len(all_snaps),scene_evidence_count=len(all_scenes),observed_scene_evidence_count=sum(s.get('observation_state')=='OBSERVED' for s in all_scenes),replacement_scene_evidence_count=len(new_scenes),archive_container_count=len(registry),archive_index_entry_count=len(index),security_bypass_count=0,phase2600_allowed=False)
    for v in verification:v['verified_member_count']=sum(a==v['archive_id'] for a,n in verified)
    counts['verified_archive_member_count']=len(verified)
    require(len(active)==counts[GATES[0]],'master/matrix mismatch')
    require(all(len([r for r in active if r[f]=='true'])==counts[k] for f,k in [('desktop_durable_derived',GATES[1]),('mobile_durable_derived',GATES[2]),('both_viewports_durable_derived',GATES[3])]),'master viewport mismatch')
    ready=hard_gate(counts);payload={'status':STOP if ready else 'FAIL_CLOSED_CAPTURE_RECOVERY_INCOMPLETE','aggregate':counts,'phase2600_allowed':False,'same_cell_qa':'PASS','aggregate_invariant':'Master == Matrix == Aggregate == QA == PM Summary','security_bypass_count':0,'unresolved_exceptions':[] if ready else sorted(failids-set(accepted)),'compatibility_calibration':'HOLD_NOT_RUN','production_renderability':'HOLD_NOT_RUN','phase2600_expansion':'HOLD_NOT_ALLOWED'}
    ledger=[dict(r,replacement_reference_id=accepted.get(r['reference_id'],({},))[0].get('replacement_reference_id'),replacement_status='DURABLE_ACCEPTED' if r['reference_id'] in accepted else 'UNRESOLVED',candidate_attempt_ids=[a['attempt_id'] for a in attempts if a['replaces_reference_id']==r['reference_id']]) for r in fail0]
    clean_registry=[{k:v for k,v in r.items() if k!='path'} for r in registry]
    csv_file(out/'reference_master.csv',master);csv_file(out/'coverage_matrix.csv',matrix)
    json_file(out/'aggregate.json',counts);json_file(out/'qa_report.json',payload);json_file(out/'pm_summary.json',payload)
    json_file(out/'archive_registry.json',clean_registry);json_file(out/'archive_verification.json',verification)
    json_lines(out/'archive_index.jsonl',index);json_lines(out/'snapshots.jsonl',all_snaps);json_lines(out/'scene_evidence.jsonl',all_scenes)
    json_lines(out/'failure_replacement_ledger.jsonl',ledger);json_lines(out/'candidate_attempts.jsonl',attempts)
    json_lines(out/'accepted_replacements.jsonl',[dict(c,run_id=b['run_id'],candidate_sha=b['candidate_sha'],official_visual_qa=q) for c,r,b,q in accepted.values()])
    json_file(out/'output_hashes.json',{p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file() and p.name!='output_hashes.json'})
    return payload

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-dir',required=True);p.add_argument('--archive-dir',required=True);p.add_argument('--inputs-dir',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args()
    result=build(a.source_dir,a.archive_dir,a.inputs_dir,a.out_dir);print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if hard_gate(result['aggregate']) else 2)
