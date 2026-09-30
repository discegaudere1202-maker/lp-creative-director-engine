"""Collect actual holds/failures and deterministic research review outputs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lp_engine import independence_calibration as d
from lp_engine import mechanism_runtime as legacy
from lp_engine import production_eligibility as c
from lp_engine.production_generation import run_generation

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,v):(d.DATA/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')

def main():
    calibration=d.ledger(); failures=[]
    for r in calibration.values():
        for decision in r['candidate_decisions']:
            failures.append({'failure_id':'P221D-MATCH-'+decision['candidate_id'],'mechanism_id':r['mechanism_id'],
                'category':'MECHANISM_MATCH_REJECT' if decision['match_decision']=='REJECT' else 'MECHANISM_MATCH_HOLD',
                'decision':decision,'input_sha256':decision['candidate_digest'],'source':'data/phase2_2_1d/candidate_reviews.json#'+decision['candidate_id'],
                'render_executed':False,'phase2600_allowed':False})
        try:d.require_live_independence(r['mechanism_id'])
        except ValueError as e:
            failures.append({'failure_id':'P221D-HOLD-'+r['mechanism_id'],'mechanism_id':r['mechanism_id'],
                'category':'ELIGIBILITY_HOLD','observed_exception':'ValueError','observed_reason':str(e),
                'calibration_digest':legacy.digest(r),'render_executed':False,'phase2600_allowed':False})
        else:raise RuntimeError('UNEXPECTED_LIVE_RELEASE')
    targets=d.read('targeted_outcomes.json')['records']
    for r in targets:
        failures.append({'failure_id':'P221D-TARGET-'+r['reference_id'],'mechanism_id':r['mechanism_id'],
            'category':'TARGETED_MATCH_AND_TRACE_REJECT','input_sha256':legacy.digest(r),'reason':r['rejection_reason'],
            'render_executed':False,'phase2600_allowed':False})
    manifest=d.read('targeted_capture_manifest.json')
    for rec in manifest['records']:
        for v in rec['viewports']:
            if v['capture_state']!='CAPTURED_TEMPORARY':
                failures.append({'failure_id':'P221D-CAPTURE-'+rec['reference_id']+'-'+v['viewport_label'],
                    'mechanism_id':rec['mechanism_id'],'category':'CAPTURE_FAILURE','input_sha256':legacy.digest(v),
                    'reason':v['failure_reason'],'viewport':v['viewport'],'source_url':rec['source_url'],
                    'bot_detection_observed':False,'render_executed':False,'phase2600_allowed':False})
    failures.extend(d.read('negative_test_report.json')['records'])
    blocked=[]
    for p in c.read('profiles.json')[:5]:
        raw=c.read('inputs/'+p['profile_id']+'.json')
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'output'
            try:run_generation(raw,target,mode='production')
            except ValueError as e:
                if 'INDEPENDENCE_INSUFFICIENT_LIVE_REJECT' not in str(e) or target.exists():raise
                b={'failure_id':'P221D-LIVE-'+p['profile_id'],'category':'PRODUCTION_ELIGIBILITY_REJECT',
                    'profile_id':p['profile_id'],'selected_mechanism_ids':p['selected_mechanism_ids'],
                    'input_sha256':legacy.digest(raw),'observed_reason':str(e),'result':'FAIL_CLOSED_PASS',
                    'output_directory_created':False,'render_executed':False,'phase2600_allowed':False}
                blocked.append(b);failures.append(b)
            else:raise RuntimeError('UNEXPECTED_LIVE_OUTPUT')
    (d.DATA/'failure_evidence.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in failures))
    write('production_gate_revalidation.json',{'profiles':blocked,'blocked':len(blocked),'render_revalidation_required':0,
        'reason':'No eligibility changed. No changed-eligibility desktop/mobile render is asserted; five actual live routes fail before render.',
        'prior_c_desktop_mobile':'8/8 historical PASS preserved and independently revalidated from saved pixels/records, not new browser runs',
        'phase2600_allowed':False})
    archive=ROOT/'artifacts/phase2_2_1d/discovery_failure_archive.zip'
    names=['data/phase2_2_1d/targeted_precapture.json','data/phase2_2_1d/targeted_capture_manifest.json','data/phase2_2_1d/targeted_outcomes.json']+[r['failure_image'] for r in targets]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(names):
            # Stable archive timestamps; actual capture timestamps are in the
            # capture manifest, not reconstructed from ZIP timestamps.
            info=zipfile.ZipInfo(name,date_time=(2026,9,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(ROOT/name).read_bytes())
    checks=[]
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            raw=z.read(name)
            if hashlib.sha256(raw).hexdigest()!=sha(ROOT/name):raise RuntimeError('ARCHIVE_READBACK_MISMATCH')
            checks.append({'archive_member':name,'sha256':sha(ROOT/name),'bytes':len(raw),'readback':'PASS'})
    images=[]
    for r in targets:
        file=ROOT/r['failure_image'];im=Image.open(file)
        images.append({'reference_id':r['reference_id'],'path':r['failure_image'],'sha256':sha(file),'dimensions':list(im.size),
            'capture_timestamp':'NOT_RECORDED_BY_CLOUD_SCREENSHOT_CALL_NOT_ADMISSIBLE',
            'persisted_at':datetime.fromtimestamp(file.stat().st_mtime,timezone.utc).isoformat(),
            'evidence_role':'REJECTION_AND_CAPTURE_LIMITATION_ONLY','paired_1440_390_durable':'FAIL','accepted':False})
    write('discovery_archive_registry.json',{'archive_path':str(archive.relative_to(ROOT)),
        'archive_locator':'GIT_REPOSITORY_PATH_PINNED_BY_FINAL_COMMIT_IN_ISSUE_143',
        'container_sha256':sha(archive),'bytes':archive.stat().st_size,'member_count':len(checks),'members':checks,'images':images,
        'result':'PASS_REJECTION_ARCHIVE_BYTES_ONLY','new_reference_admission_count':0,'phase2600_allowed':False})
    report=[]
    for mid,r in calibration.items():
        targeted=[t for t in targets if t['mechanism_id']==mid]
        copied=dict(r)
        copied.update(discovered_candidate_count=len(r['candidate_decisions'])+len(targeted),
            rejected_candidate_count=sum(v['match_decision']=='REJECT' for v in r['candidate_decisions'])+len(targeted),
            unresolved_match_candidate_count=sum(v['match_decision']=='HOLD' for v in r['candidate_decisions']),
            rejection_reasons=[v['reason'] for v in r['candidate_decisions']]+[t['rejection_reason'] for t in targeted],
            VERIFIED_INDEPENDENT_count=0,PARTIALLY_INDEPENDENT_count=0,NOT_INDEPENDENT_count=1,UNKNOWN_count=0,
            candidate_independence_unknown_count=len(r['candidate_decisions'])+len(targeted),
            failure_evidence_count=sum(f.get('mechanism_id')==mid for f in failures),
            validator='PENDING_FINAL_VALIDATOR',tests_report='data/phase2_2_1d/tests_report.json',
            unresolved_blockers=r['eligibility_change_reason'])
        report.append(copied)
    tests=d.read('tests_report.json');neg=d.read('negative_test_report.json')
    final={'source_commit':'b3d4607277c3e13a24505e70b94bf3ec03b67362','source_pm_comment':5914339229,
        'branch':'phase2-2-1d/independence-eligibility-20261001','final_commit_binding':'Exact commit supplied by GitHub Issue #143 final report; no self-referential SHA field',
        'status':'PENDING_FINAL_VALIDATOR','atomic_mechanism_count':13,'adapter_implemented_count':10,'adapter_hold_count':3,
        'existing_corpus_reviewed':100,'existing_corpus_pixel_scope':'100 entry viewport pairs; 26 detailed candidates; not an exhaustive visual review of all full-page pixels',
        'existing_corpus_archives_verified':16,'existing_corpus_members_verified':1414,'existing_corpus_scene_records_verified':1024,
        'existing_corpus_candidates_compared':26,'targeted_candidate_count':2,'total_candidate_count':28,
        'rejected_candidate_count':sum(r['rejected_candidate_count'] for r in report),'unresolved_match_candidate_count':sum(r['unresolved_match_candidate_count'] for r in report),
        'new_validated_atomic_match_count':0,'accepted_new_independent_evidence_count':0,
        'eligibility_counts':{'ELIGIBLE':0,'CONDITIONAL':0,'HOLD':13,'INELIGIBLE':0},'hold_released_count':0,'remaining_hold_count':13,
        'independence_counts':{'VERIFIED_INDEPENDENT':0,'PARTIALLY_INDEPENDENT':0,'NOT_INDEPENDENT':13,'UNKNOWN':0},
        'agency_independence_unknown_count':13,'campaign_independence_unknown_count':13,'production_solver_gate':'PASS_FAIL_CLOSED_NO_RELAXATION',
        'production_routes_blocked_before_output':len(blocked),'changed_eligibility_render_test_count':0,'desktop_new_render_result':'NOT_APPLICABLE_UNCHANGED','mobile_new_render_result':'NOT_APPLICABLE_UNCHANGED',
        'targeted_required_desktop_capture_failures':2,'targeted_required_mobile_capture_failures':2,
        'motion_support':'STATIC_ONLY_ALL_13','promotion_count':0,'customer_production_approved_count':0,
        'negative_test_result':{k:v for k,v in neg.items() if k!='records'},'tests':tests,
        'failure_evidence_count_phase_b':17,'failure_evidence_count_phase_c':23,'failure_evidence_count_phase_d':len(failures),
        'failure_evidence_count_total':40+len(failures),'failure_categories_phase_d':dict(Counter(f['category'] for f in failures)),
        'mechanisms':report,'checkpoint_blockers':[],'remaining_live_blockers':['No fully validated cross-reference atomic match plus snapshot-bound agency/campaign/source-family independence pair','Three adapter semantics/job holds','Client-specific truth/rights/current output QA remain required'],
        'discovery_limitations':['Entry viewport screening is not an exhaustive pixel search of every lower scene','Required-size local browser acquisition failed for two candidates; cloud screenshots are rejection evidence only','No exact current creator/campaign relationship verified from historical/adjacent-page cases'],
        'phase2600_allowed':False}
    write('final_report.json',final)
    print(json.dumps({'failure_evidence_phase_d':len(failures),'failure_total':40+len(failures),'candidate_rejects':final['rejected_candidate_count'],'candidate_match_holds':final['unresolved_match_candidate_count'],'archive_sha256':sha(archive),'tests':tests['passed']}))

if __name__=='__main__':main()
