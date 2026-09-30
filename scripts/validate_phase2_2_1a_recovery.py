"""Independent consumer QA of integrated recovery outputs and pinned durable bytes."""
import argparse,csv,hashlib,json,zipfile
from collections import Counter
from pathlib import Path

GATES=('final_usable_reference_count','desktop_1440_durable_count','mobile_390_durable_count','both_viewports_durable_count')
CELL=('business_archetype','industry','market_scope','discovery_source_class')
STOP='PHASE_2_2_1_CAPTURE_RECOVERY_READY_FOR_PM_REVIEW'
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def csvrows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def validate_outputs(out,archive_dir):
    out=Path(out);archive_dir=Path(archive_dir)
    hashes=json.loads((out/'output_hashes.json').read_text())
    require(set(hashes)=={p.name for p in out.iterdir() if p.is_file() and p.name!='output_hashes.json'},'output manifest incomplete')
    for name,digest in hashes.items():require(sha((out/name).read_bytes())==digest,'output changed: '+name)
    agg=json.loads((out/'aggregate.json').read_text());qa=json.loads((out/'qa_report.json').read_text());pm=json.loads((out/'pm_summary.json').read_text())
    require(agg==qa['aggregate']==pm['aggregate'],'Aggregate/QA/PM mismatch')
    require(all(agg[k]==100 for k in GATES),'hard gate below 100')
    require(qa['status']==pm['status']==STOP and not qa['unresolved_exceptions'] and not pm['unresolved_exceptions'],'unresolved recovery')
    require(agg['phase2600_allowed'] is qa['phase2600_allowed'] is pm['phase2600_allowed'] is False,'expansion enabled')
    require(agg['security_bypass_count']==qa['security_bypass_count']==pm['security_bypass_count']==0,'security bypass')
    master=csvrows(out/'reference_master.csv');active=[r for r in master if r['active_in_recovered_corpus']=='true'];originals={r['reference_id']:r for r in master if r['record_origin']=='ORIGINAL_PILOT_IMMUTABLE_SOURCE'}
    require(len(originals)==100 and len(active)==100 and len({r['reference_id'] for r in master})==len(master),'master count/IDs invalid')
    require(sum(r['active_in_recovered_corpus']=='true' for r in originals.values())==73,'original 73 changed')
    matrix=csvrows(out/'coverage_matrix.csv');require(len(matrix)==20,'cell count changed')
    for k in GATES:require(sum(int(r[k]) for r in matrix)==agg[k],'matrix aggregate mismatch')
    for row in matrix:
        refs=[r for r in active if r['slot_id']==row['slot_id']]
        require(len(refs)==int(row[GATES[0]])==5,'slot missing')
        require(all(all(r[k]==row[k] for k in CELL) for r in refs),'near-cell substitution')
    for field,key in [('desktop_durable_derived',GATES[1]),('mobile_durable_derived',GATES[2]),('both_viewports_durable_derived',GATES[3])]:require(sum(r[field]=='true' for r in active)==agg[key],'master durable count mismatch')
    attempts=jl(out/'candidate_attempts.jsonl');accepted=[a for a in attempts if a['accepted']];ledger=jl(out/'failure_replacement_ledger.jsonl')
    require(len(attempts)==agg['candidate_attempts'] and len(accepted)==agg['successful_replacements']==27,'attempt accounting mismatch')
    require(sum(not a['accepted'] for a in attempts)==agg['failed_attempts'],'failed audit trail missing')
    require(len({a['replaces_reference_id'] for a in accepted})==len(ledger)==27,'replacement coverage invalid')
    require(all(r['replacement_status']=='DURABLE_ACCEPTED' and r['replacement_reference_id'] in {a['reference_id'] for a in accepted} for r in ledger),'unresolved ledger')
    registry=json.loads((out/'archive_registry.json').read_text());regs={r['archive_id']:r for r in registry};containers={}
    for reg in registry:
        require(reg['archive_status']=='DURABLE_VERIFIED' and reg['library_file_id'].startswith('libfile_') and reg['pinned_file_id'].startswith('file_') and str(reg['version_id'])=='0','durable pin missing')
        p=archive_dir/reg.get('file_name',reg.get('filename'));require(sha(p.read_bytes())==reg['container_sha256'],'durable container mismatch');containers[reg['archive_id']]=zipfile.ZipFile(p)
    index=jl(out/'archive_index.jsonl');indexed={(r['archive_id'],r['archive_entry'],r['content_hash']) for r in index}
    snaps=jl(out/'snapshots.jsonl');snapshot_ids={s['snapshot_id']:s for s in snaps if 'snapshot_id' in s};scenes=jl(out/'scene_evidence.jsonl')
    require(len(snaps)==agg['snapshot_count'] and len(scenes)==agg['scene_evidence_count'],'evidence count mismatch')
    for a in accepted:
        rid=a['reference_id'];fid=a['replaces_reference_id'];c=a['candidate'];require(all(c[k]==originals[fid][k] for k in CELL),'accepted same-cell mismatch')
        require(a['visual_state']=='PASS' and a['official_state']=='PASS' and a['capture_state']=='CAPTURED_TEMPORARY','preflight-only promotion')
        ss=[s for s in snaps if s['reference_id']==rid];cc=[s for s in scenes if s['reference_id']==rid and s['observation_state']=='OBSERVED']
        require(len(ss)==len(cc)==4,'replacement scene/snapshot chain missing')
        require({(s['viewport_label'],s['member_kind']) for s in ss}=={(v,k) for v in ('DESKTOP','MOBILE') for k in ('VIEWPORT','FULL_PAGE')},'required pixels missing')
        for scene in cc:
            snapshot=snapshot_ids.get(scene['parent_snapshot_id']);require(snapshot is not None and snapshot['reference_id']==rid,'broken scene parent')
            for k in ('archive_id','archive_entry','content_hash','container_sha256','pinned_file_id','library_file_id','version_id'):require(scene[k]==snapshot[k],'scene/archive binding mismatch')
            require((scene['archive_id'],scene['archive_entry'],scene['content_hash']) in indexed,'archive index member missing')
            reg=regs[scene['archive_id']];require(reg['container_sha256']==scene['container_sha256'],'scene container digest mismatch')
            require(sha(containers[scene['archive_id']].read(scene['archive_entry']))==scene['content_hash'],'scene pixel digest mismatch')
        require(sha(containers[a['archive']['archive_id']].read(a['manifest_entry']))==a['manifest_sha256'],'attempt manifest digest mismatch')
    for z in containers.values():z.close()
    return {'validator':'PASS','hard_gate':{k:agg[k] for k in GATES},'same_cell_qa':'27/27 PASS','aggregate_invariant':'PASS','durable_chain':'27/27 PASS','phase2600_allowed':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out-dir',required=True);p.add_argument('--archive-dir',required=True);a=p.parse_args();print(json.dumps(validate_outputs(a.out_dir,a.archive_dir),indent=2))
