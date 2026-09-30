"""Independently aggregate immutable traces, authored axes and replayed gate denials.

This is structural/trace QA, not an independent human semantic approval. PM can
inspect every observation against the pinned archive members before PASS.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from lp_engine import independence_calibration as d
from lp_engine import mechanism_runtime as legacy
from exercise_phase2_2_1d_rejections import replay

SOURCE='b3d4607277c3e13a24505e70b94bf3ec03b67362'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(condition,reason):
    if not condition:raise ValueError(reason)

def validate_c_regression():
    """Validate approved C in isolation; never rewrite its signed hash manifest.

    The only intentional change to an existing C-hashed file is the D live
    admission call. Check that exact additive delta, then execute the original
    C validator against its original git bytes. D tests exercise current code.
    """
    changed='src/lp_engine/production_eligibility.py'
    approved=subprocess.run(['git','show',SOURCE+':'+changed],cwd=ROOT,
                            check=True,capture_output=True).stdout
    anchor=b"    if mode == 'production' and contract['evidence_independence_status'] != 'VERIFIED_INDEPENDENT':\n"
    addition=(b"    if mode == 'production':\n"
              b"        from .independence_calibration import require_live_independence\n"
              b"        require_live_independence(contract['mechanism_id'])\n")
    require(approved.count(anchor)==1,'APPROVED_C_GATE_ANCHOR')
    require((ROOT/changed).read_bytes()==approved.replace(anchor,addition+anchor),
            'C_GATE_DELTA_NOT_EXACT_ADDITIVE_INDEPENDENCE_CHECK')
    for name,h in json.loads((ROOT/'data/phase2_2_1c/output_hashes.json').read_text()).items():
        if name==changed:
            require(hashlib.sha256(approved).hexdigest()==h,'C_APPROVED_CODE_HASH_MISMATCH')
        else:
            require(sha(ROOT/name)==h,'C_OUTPUT_BYTES_CHANGED:'+name)
    with tempfile.TemporaryDirectory(prefix='phase221d-approved-c-') as directory:
        checkout=Path(directory);archive=checkout/'approved.tar'
        scopes={'src','scripts','data','docs','assets'}
        for manifest in ('output_hashes.json','phase_b_preservation.json'):
            for name in json.loads((ROOT/'data/phase2_2_1c'/manifest).read_text()):
                scopes.add('/'.join(Path(name).parts[:2]) if name.startswith('artifacts/') else Path(name).parts[0])
        subprocess.run(['git','archive','--format=tar','--output',str(archive),SOURCE,
                        *sorted(scopes)],
                       cwd=ROOT,check=True,capture_output=True)
        subprocess.run(['tar','-xf',str(archive),'-C',str(checkout)],check=True,capture_output=True)
        result=subprocess.run([sys.executable,'scripts/validate_phase2_2_1c.py'],
                              cwd=checkout,capture_output=True,text=True)
        require(result.returncode==0,'APPROVED_C_VALIDATOR_FAILED:\n'+result.stderr)
        prior=json.loads(result.stdout)
    require(prior['validator']=='PASS','APPROVED_C_REGRESSION_VALIDATOR')
    return prior

def validate(archive_directory=None):
    saved=d.read('final_report.json');rb=d.read('corpus_readback.json')
    cs=d.ledger();ms,ss=legacy.database()
    require(len(cs)==len(ms)==13,'ATOMIC_COVERAGE')
    require(rb['source_commit']==SOURCE and rb['active_reference_count']==100,'CORPUS_SOURCE_OR_COUNT')
    require(len(rb['archive_checks'])==16 and all(r['result']=='PASS' for r in rb['archive_checks']),'CORPUS_ARCHIVE_QA')
    require(len(rb['members'])==rb['verified_member_count']==1414 and all(r['result']=='PASS' for r in rb['members']),'CORPUS_MEMBER_QA')
    require(rb['scenes']==1024 and len(rb['reference_views'])==100,'CORPUS_SCENE_OR_VIEW_COVERAGE')
    verified={(r['archive_id'],r['archive_member']):r['sha256'] for r in rb['members']}
    require(len(verified)==1414,'DUPLICATE_READBACK_MEMBER')
    all_scenes=legacy.load_jsonl(ROOT/'data/phase2_2_1a_recovery/scene_evidence.jsonl')
    scene_index={r['scene_evidence_id']:r for r in all_scenes}
    screen=d.read('corpus_screening.json');require(len(screen)==len({r['reference_id'] for r in screen})==100,'SCREENING_COVERAGE')
    for s in screen:
        require(set(s['mechanisms_considered'])==set(ms) and s['viewports_reviewed']==['DESKTOP','MOBILE'],'SCREENING_SCOPE')
        for p in s['snapshot_locators']:
            require(verified[(p['archive_id'],p['archive_member'])]==p['sha256'],'SCREENING_TRACE')
    for name,h in d.read('phase_b_c_preservation.json').items():
        require(sha(ROOT/name)==h,'PRIOR_EVIDENCE_MUTATED:'+name)
        # Check against actual approved git object, not only the new manifest.
        raw=subprocess.run(['git','show',SOURCE+':'+name],cwd=ROOT,check=True,capture_output=True).stdout
        require(hashlib.sha256(raw).hexdigest()==h,'PRESERVATION_MANIFEST_NOT_APPROVED_SOURCE:'+name)
    bfail=legacy.load_jsonl(legacy.DATA/'failure_evidence.jsonl')
    cfail=legacy.load_jsonl(ROOT/'data/phase2_2_1c/failure_evidence.jsonl')
    require(len(bfail)==17 and len(cfail)==23,'PRIOR_FAILURE_COUNT')
    candidates=d.read('candidate_reviews.json');require(len(candidates)==26,'DETAILED_CANDIDATE_BOUND')
    derived_reject=derived_hold=0
    for candidate in candidates:
        axes=candidate['mechanism_match_basis']
        require(set(axes)==set(d.AXES),'COMPARISON_DIMENSION_MISSING')
        require(all(axes[a]['status'] in ('MATCH','PARTIAL','MISMATCH','UNKNOWN') and axes[a]['observation'] for a in d.AXES),'EMPTY_AXIS_OBSERVATION')
        require(candidate['source_contract_sha256']==legacy.digest(ms[candidate['mechanism_id']]),'CANDIDATE_CONTRACT_TRACE')
        require(d.trace_valid(candidate,scene_index,verified),'CANDIDATE_PIXEL_TRACE')
        # Separate aggregation of authored critical axes, not saved outcome flags.
        if any(x['status']=='MISMATCH' for x in axes.values()):derived_reject+=1
        elif any(x['status']!='MATCH' for x in axes.values()):derived_hold+=1
        else:raise ValueError('NEW_MATCH_REQUIRES_EXTRA_CALIBRATION_AUDIT')
        require(candidate['accept_as_independent_evidence'] is False and candidate['independence_status']=='UNKNOWN','UNVERIFIED_CANDIDATE_ADMITTED')
    require(derived_reject==25 and derived_hold==1,'CANDIDATE_MATCH_AGGREGATE')
    audit=d.read('source_attribution_audit.json')
    require({r['mechanism_id'] for r in audit['records']}==set(ms),'ATTRIBUTION_COVERAGE')
    require(all(r['agency_independence']==r['campaign_independence']=='UNKNOWN' for r in audit['records']),'UNBOUND_ATTRIBUTION_CREDIT')
    targets=d.read('targeted_outcomes.json')['records'];require(len(targets)==2,'TARGETED_BOUND')
    precap=d.read('targeted_precapture.json');cap=d.read('targeted_capture_manifest.json')
    require(cap['precapture_sha256']==sha(d.DATA/'targeted_precapture.json'),'PRECAPTURE_GATE_NOT_BOUND')
    require({c['reference_id'] for c in precap['candidates']}=={t['reference_id'] for t in targets},'TARGETED_ID_MISMATCH')
    require(all(not t['accept_as_independent_evidence'] and not(t['desktop_scene_ids'] or t['mobile_scene_ids']) for t in targets),'INCOMPLETE_TARGET_ADMITTED')
    registry=d.read('discovery_archive_registry.json');archive=ROOT/registry['archive_path']
    require(sha(archive)==registry['container_sha256'],'DISCOVERY_ARCHIVE_CHANGED')
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist())==registry['member_count']==5,'ARCHIVE_MEMBERS')
        for r in registry['members']:
            require(hashlib.sha256(z.read(r['archive_member'])).hexdigest()==r['sha256']==sha(ROOT/r['archive_member']),'ARCHIVE_MEMBER_READBACK')
    for image in registry['images']:
        require(sha(ROOT/image['path'])==image['sha256'] and image['accepted'] is False,'FAILURE_PIXEL_TRACE')
    require(all(r['new_eligibility']==r['previous_eligibility']=='HOLD' and not r['eligibility_recalculated'] for r in cs.values()),'UNJUSTIFIED_ELIGIBILITY_CHANGE')
    require(all(r['independence']['distinct_reference_unit_count']==1 and r['independence']['status']=='NOT_INDEPENDENT' for r in cs.values()),'INDEPENDENCE_COUNT_INFLATION')
    neg=d.read('negative_test_report.json');require(neg['failed']==0 and neg['cases']==neg['passed']==18,'NEGATIVE_SUITE')
    for r in neg['records']:
        require(legacy.digest(r['specimen'])==r['input_sha256'] and replay(r['specimen'])==r['actual'],'NEGATIVE_REPLAY')
        require(r['actual']['status']!='VERIFIED_INDEPENDENT' and r['render_executed'] is False,'NEGATIVE_FAIL_OPEN')
    tests=d.read('tests_report.json');require(tests['failed']==tests['skipped']==0 and tests['run']==tests['passed']==66,'SCOPED_TESTS')
    require(tests['groups']['test_phase2_2_1c']==26 and tests['groups']['test_phase2_2_1d']==16,'TEST_MODULE_SHADOWING')
    prior=validate_c_regression()
    failures=legacy.load_jsonl(d.DATA/'failure_evidence.jsonl')
    require(len({r['failure_id'] for r in failures})==len(failures)==68,'NEW_FAILURE_COUNT_OR_ID')
    require(saved['failure_evidence_count_total']==108,'TOTAL_FAILURE_COUNT')
    require(saved['rejected_candidate_count']==27 and saved['unresolved_match_candidate_count']==1,'FINAL_CANDIDATE_COUNTS')
    require(saved['hold_released_count']==0 and saved['remaining_hold_count']==13,'FINAL_HOLD_COUNTS')
    require(len(saved['mechanisms'])==13 and all(r['new_eligibility']=='HOLD' for r in saved['mechanisms']),'FINAL_MECHANISM_REPORT')
    require(saved['promotion_count']==saved['customer_production_approved_count']==0,'PROMOTION_OR_CUSTOMER_RELEASE')
    require(saved['phase2600_allowed'] is False and all(r['phase2600_allowed'] is False for r in failures),'EXPANSION_FORBIDDEN')
    for path,h in d.read('output_hashes.json').items():require(sha(ROOT/path)==h,'REVIEW_OUTPUT_CHANGED:'+path)
    gate_revalidation=d.read('production_gate_revalidation.json')
    require(gate_revalidation['blocked']==5 and all(r['result']=='FAIL_CLOSED_PASS' and not r['output_directory_created'] for r in gate_revalidation['profiles']),'ACTUAL_PRODUCTION_ROUTE_GATE')
    if archive_directory:
        registry_a=json.loads((ROOT/'data/phase2_2_1a_recovery/archive_registry.json').read_text())
        verified_zips={}
        try:
            for item in registry_a:
                p=archive_directory/(item.get('file_name') or item['filename'])
                require(sha(p)==item['container_sha256'],'ACTUAL_CORPUS_CONTAINER_READBACK')
                verified_zips[item['archive_id']]=zipfile.ZipFile(p)
            for item in rb['members']:
                raw=verified_zips[item['archive_id']].read(item['archive_member'])
                require(hashlib.sha256(raw).hexdigest()==item['sha256'],'ACTUAL_CORPUS_MEMBER_READBACK')
        finally:
            for z in verified_zips.values():z.close()
    return {'validator':'PASS','scope':'Structural, snapshot trace, immutable bytes, gate replay and preserved C regression; semantic observations await Sarah PM review',
        'atomic_mechanism_count':len(cs),'candidate_count':len(candidates)+len(targets),'candidate_rejects':derived_reject+len(targets),'candidate_match_holds':derived_hold,
        'holds_released':0,'holds_remaining':13,'prior_failures_preserved':40,'phase_d_failures':len(failures),'total_failures':40+len(failures),
        'negative_tests_passed':neg['passed'],'scoped_tests_passed':tests['passed'],'evidence_trace_qa':'PASS',
        'actual_original_corpus_archive_readback':'PASS_16_CONTAINERS_1414_MEMBERS' if archive_directory else 'NOT_RERUN_USE_PINNED_PRIOR_DIGEST_REPORT',
        'changed_eligibility_render_revalidation':'NOT_APPLICABLE_ZERO_ELIGIBILITY_CHANGES',
        'prior_c_saved_browser_evidence_validator':'PASS_8_DESKTOP_8_MOBILE_HISTORICAL_NOT_NEW_RUNS','phase2600_allowed':False,
        'status':'PHASE_2_2_1_INDEPENDENCE_ELIGIBILITY_READY_FOR_PM_REVIEW'}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--archive-directory',type=Path);args=parser.parse_args()
    report=validate(args.archive_directory)
    (d.DATA/'validator_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
