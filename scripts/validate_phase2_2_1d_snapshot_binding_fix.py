"""Versioned fix validator. Never writes historical D/B/C evidence or reports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lp_engine import independence_calibration as d
from lp_engine import evidence_snapshot_binding as b

BASE='4ae3f53be9cc48f13b22145f1e0a54e68b367c79'
EDITED_EXISTING={'src/lp_engine/independence_calibration.py','tests/test_phase2_2_1d.py'}
HISTORICAL_SCOPES=('data/phase2_2_1a_recovery/', 'data/phase2_2_1b/', 'data/phase2_2_1c/',
                   'data/phase2_2_1d/', 'artifacts/phase2_2_1b/', 'artifacts/phase2_2_1c/',
                   'artifacts/phase2_2_1d/')

def require(value,reason):
    if not value:raise ValueError(reason)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def historical_preservation():
    entries=subprocess.check_output(['git','ls-tree','-r','-z',BASE],cwd=ROOT).split(b'\0')
    changed=[];historical={};edited={}
    for entry in entries:
        if not entry:continue
        metadata,name=entry.split(b'\t',1);path=name.decode();mode,kind,object_sha=metadata.decode().split()
        require(kind=='blob','UNEXPECTED_NON_BLOB_BASE_ENTRY:'+path)
        data=(ROOT/path).read_bytes()
        git_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if git_sha!=object_sha:changed.append(path)
        if path.startswith(HISTORICAL_SCOPES) or path=='data/creative_mechanism_phase2_2_1_atomic_calibration.jsonl':
            require(git_sha==object_sha,'HISTORICAL_EVIDENCE_CHANGED:'+path)
            historical[path]=hashlib.sha256(data).hexdigest()
        if path in EDITED_EXISTING:
            old=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
            edited[path]={'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(data).hexdigest()}
    require(set(changed)==EDITED_EXISTING,'UNEXPECTED_EXISTING_FILE_DELTA:'+repr(changed))
    return {'base_commit':BASE,'existing_modified_files':sorted(changed),
            'all_other_base_files_unchanged':True,'historical_evidence_files_preserved':len(historical),
            'historical_evidence_sha256_index_digest':d.legacy.digest(historical),
            'edited_code_hashes':edited,'historical_failure_count':108,'historical_scoped_test_count':66}

def binding_index(sources):
    result=[]
    for unit in sources.units.values():
        snapshot=b.evidence_snapshot(unit,sources)
        result.append({'source_record_id':b.source_record_id(unit),
            'independent_evidence_unit_id':snapshot['unit_id'],'reference_id':unit['reference_id'],
            'desktop_scene_ids':unit['desktop_scene_ids'],'mobile_scene_ids':unit['mobile_scene_ids'],
            'evidence_snapshot_sha256':snapshot['evidence_snapshot_sha256']})
    return result

def validate(*,require_execution=False,require_manifest=False):
    # Also exercise preservation of old rejection bytes. No new capture/QA.
    registry=d.read('discovery_archive_registry.json')
    require(sha(ROOT/registry['archive_path'])==registry['container_sha256'],'DISCOVERY_ARCHIVE_CHANGED')
    for image in registry['images']:require(sha(ROOT/image['path'])==image['sha256'],'DISCOVERY_PIXEL_CHANGED')
    preservation=historical_preservation()
    sources=d.evidence_sources();index=binding_index(sources)
    require(d.fix_read('snapshot_binding_index.json')==index,'SNAPSHOT_INDEX_NOT_SOURCE_DERIVED')
    records=d.ledger()
    require(len(records)==13,'ATOMIC_COVERAGE_CHANGED')
    original=d.read('calibration.json')
    stripped=[{key:value for key,value in row.items() if key not in ('snapshot_binding_schema','evidence_snapshot_bindings')}
              for row in records.values()]
    require(stripped==original,'HISTORICAL_CANDIDATE_OR_ELIGIBILITY_OUTCOME_CHANGED')
    require(len(index)==39,'CANONICAL_SOURCE_RECORD_COVERAGE')
    require(d.read('family_relations.json')==[] and d.fix_read('family_assertions.json')==[] and
            d.fix_read('attribution_evidence.json')==[],'UNAUTHORIZED_ATTRIBUTION_ADDITION')
    gate_denials=[]
    for mid,record in records.items():
        require(record['new_eligibility']=='HOLD' and record['accepted_new_independent_evidence_count']==0 and
                record['promotion_count']==0 and record['phase2600_allowed'] is False,'UNAUTHORIZED_LIVE_UNLOCK')
        require(record['snapshot_binding_schema']==b.SCHEMA and len(record['evidence_snapshot_bindings'])==1,'BASELINE_BINDING_COVERAGE')
        try:d.require_live_independence(mid)
        except ValueError as error:
            require(str(error).startswith('INDEPENDENCE_INSUFFICIENT_LIVE_REJECT:PHASE_D_CALIBRATION'),'UNEXPECTED_GATE_REASON')
            gate_denials.append({'mechanism_id':mid,'actual_error':str(error)})
        else:raise ValueError('LIVE_GATE_FAIL_OPEN:'+mid)
    saved=d.read('final_report.json')
    require(saved['failure_evidence_count_total']==108 and saved['remaining_hold_count']==13 and
            saved['promotion_count']==saved['customer_production_approved_count']==0 and
            saved['phase2600_allowed'] is False,'HISTORICAL_RESULT_CHANGED')
    if require_execution:
        tests=d.fix_read('tests_report.json')
        require(tests['run']==tests['passed']>0 and tests['failed']==tests['skipped']==0,'FIX_TESTS_NOT_ALL_PASSED')
        for path,digest in tests['tested_source_sha256'].items():require(sha(ROOT/path)==digest,'TESTED_SOURCE_CHANGED:'+path)
        replay=d.fix_read('legacy_negative_replay.json')
        require(replay['run']==replay['passed']==18 and replay['failed']==0,'LEGACY_NEGATIVE_REPLAY_FAILED')
        old=d.fix_read('pm_reproduction.json')
        require(len(old['mutation_cases'])==2 and all(row['old_result']=='VERIFIED_INDEPENDENT' and
                row['trace_valid'] and row['match_decision']=='MATCH' for row in old['mutation_cases']), 'PM_REPRODUCTION_INCOMPLETE')
    if require_manifest:
        manifest=d.fix_read('output_hashes.json')
        require(bool(manifest),'EMPTY_FIX_MANIFEST')
        for path,digest in manifest.items():require(sha(ROOT/path)==digest,'FIX_OUTPUT_CHANGED:'+path)
    return {'validator':'PASS','schema':b.SCHEMA,'scope':'Canonical record binding, source-derived versioned ledger, immutable historical evidence and live gate denials; semantic PM review pending',
        'source_record_bindings':len(index),'selected_scene_links':sum(len(row['desktop_scene_ids'])+len(row['mobile_scene_ids']) for row in index),
        'live_holds':13,'hold_released':0,'promotion':0,'customer_production_approved':0,'phase2600_allowed':False,
        'historical_preservation':preservation,'actual_live_gate_denials':gate_denials,
        'historical_scoped_tests':66,'historical_failure_evidence':108,
        'original_corpus_archive_readback':'NOT_RERUN','fresh_desktop_mobile_render':'N/A_ZERO_ELIGIBILITY_CHANGES',
        'current_test_execution_checked':require_execution,'fix_manifest_checked':require_manifest,
        'status':'PHASE_2_2_1D_SNAPSHOT_BINDING_FIX_READY_FOR_PM_REVIEW'}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check-manifest',action='store_true')
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    report=validate(require_execution=True,require_manifest=args.check_manifest)
    if args.output:
        require(args.output.resolve().parent==d.FIX_DATA.resolve(),'OUTPUT_MUST_BE_VERSIONED_FIX_DIRECTORY')
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
