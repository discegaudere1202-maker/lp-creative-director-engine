#!/usr/bin/env python3
"""Independent fail-closed validation; pixels/specs/HTML are hash-addressed."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lp_engine.mechanism_runtime import DATA,database,load_jsonl,multi_profile_gate,validate_edge,validate_scene_plan,render_pass


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def validate():
    if not __debug__:
        raise RuntimeError('FAIL_CLOSED: optimization may not disable validation assertions')
    m,scenes=database();profiles=json.loads((DATA/'profiles.json').read_text())
    records=json.loads((DATA/'render_records.json').read_text());idx={r['record_id']:r for r in records}
    assert len(idx)==len(records)==len(profiles)==5,'MULTI_PROFILE_COHORT_MISMATCH'
    assert multi_profile_gate(records),'MULTI_PROFILE_RENDER_GATE_FAILED'
    assert {r['profile_id'] for r in records}=={p['profile_id'] for p in profiles}
    edges=load_jsonl(DATA/'compatibility_edges.jsonl')
    assert len(edges)==83 and len({e['edge_id'] for e in edges})==83
    assert len([e for e in edges if e['scope']=='SAME_SCENE'])==78
    for e in edges:validate_edge(e,m,render_records=idx)
    count=Counter(e['compatibility_state'] for e in edges)
    assert count=={'UNKNOWN':76,'INCOMPATIBLE':2,'CONDITIONAL':5},'UNREVIEWED_EDGE_STATE_CHANGED'
    hashes=json.loads((ROOT/'data/phase2_2_1a_recovery/output_hashes.json').read_text())
    for name,h in hashes.items():assert sha(ROOT/'data/phase2_2_1a_recovery'/name)==h,'CORPUS_CHANGED'
    audit=json.loads((DATA/'source_audit.json').read_text())
    assert sha(ROOT/'data/creative_mechanism_phase2_2_1_atomic_calibration.jsonl')==audit['atomic_db_sha256'],'ATOMIC_SOURCE_DB_CHANGED'
    assert len(audit['atomic_evidence'])==26 and all(e['verified'] for e in audit['atomic_evidence'])
    statuses=json.loads((DATA/'mechanism_status.json').read_text())
    assert len(statuses)==13 and all(x['status']=='PROVISIONAL_VARIANT' and x['promotion_state']=='CANDIDATE' and x['promotion_count']==0 for x in statuses)
    total_scenes=0
    for p in profiles:
        r=idx['RENDER-'+p['profile_id']];out=ROOT/'artifacts/phase2_2_1b'/p['profile_id']
        plan=json.loads((out/'mechanism_scene_plan.json').read_text());manifest=json.loads((out/'generation_manifest.json').read_text())
        assert manifest['mode']=='test' and manifest['output_status']=='NOT_PRODUCTION_APPROVED'
        assert manifest['mechanism_rendering']['recipe_status']=='CONDITIONALLY_ACCEPTED'
        assert plan['customer_publication_allowed'] is False and plan['phase2600_allowed'] is False
        validate_scene_plan(plan,p,m,edges,idx)
        assert sha(out/'mechanism_scene_plan.json')==r['scene_spec_sha256']
        assert sha(out/'index.html')==r['html_sha256']
        total_scenes+=len(plan['scenes'])
        for label,width in [('desktop',1440),('mobile',390)]:
            v=r[label];assert v['width']==width and v['status']=='PASS'
            for key in ['screenshot','reduced_screenshot']:
                pic=(ROOT/v[key]).resolve();assert ROOT in pic.parents and pic.read_bytes().startswith(b'\x89PNG')
                assert sha(pic)==v[key+'_sha256'],'SCREENSHOT_MISSING_OR_CHANGED'
            assert len(v['metrics']['images'])==sum(len(s['content'].get('assets',[])) for s in plan['scenes'])
            assert not v['errors'] and not v['requestFailures']
        assert {b['width'] for b in r['breakpoints']}=={320,360,375,430,768,1024,1280}
        for b in r['breakpoints']:
            assert all(v for k,v in b['checks'].items() if k!='reduced_motion'),'BREAKPOINT_FAILED'
    assert total_scenes==10
    hash_manifest=DATA/'output_hashes.json'
    if hash_manifest.exists():
        for name,h in json.loads(hash_manifest.read_text()).items():
            p=(ROOT/name).resolve();assert ROOT in p.parents and sha(p)==h,'DURABLE_OUTPUT_CHANGED_OR_LOST'
    return {'validator':'PASS','atomic_mechanism_count':13,'compatibility_edge_count':83,
            'compatibility_states':dict(count),'multi_profile_count':5,'scene_spec_count':total_scenes,
            'production_path_executed_profile_count':5,'desktop_pass':5,'desktop_fail':0,'mobile_pass':5,'mobile_fail':0,
            'promotion_count':0,'evidence_trace_qa':'PASS','reference_screenshot_required_for_regeneration':False,
            'actual_customer_output_approved_count':0,'phase2600_allowed':False}


if __name__=='__main__':
    report=validate();(DATA/'validator_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
