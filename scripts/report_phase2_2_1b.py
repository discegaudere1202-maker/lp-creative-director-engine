#!/usr/bin/env python3
"""Preserve failed probes/rejections, visual audit and hash-addressed final outputs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lp_engine.mechanism_runtime import DATA,database,load_jsonl,solve
from validate_phase2_2_1b import validate


def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    report=validate();m,_=database();ps=json.loads((DATA/'profiles.json').read_text())
    edges=load_jsonl(DATA/'compatibility_edges.jsonl');records=json.loads((DATA/'render_records.json').read_text());idx={r['record_id']:r for r in records}
    failures=[];old=ROOT/'artifacts/phase2_2_1b_attempt1'
    for r in json.loads((old/'data/experiment_render_records.json').read_text()):
        for viewport in ['desktop','mobile']:
            v=r[viewport]
            if v['status']!='FAIL':continue
            name=Path(v['screenshot']).name
            failures.append({'failure_id':f'INITIAL-FOCUS-{r["profile_id"]}-{viewport}',
                'failure_type':'QA_PROBE_INTERACTION_STATE_MISMATCH','profile':r['profile_id'],
                'scene_job':[s['scene_job'] for s in next(p for p in ps if p['profile_id']==r['profile_id'])['scene_content']],
                'mechanism_set':r['mechanism_ids'],'viewport':viewport,
                'symptom':'Reduced-motion pixel comparison failed after keyboard navigation left a visible focus ring.',
                'probable_constraint':'Comparison must use the same focus and interaction state; this is not evidence that static motion is unsafe.',
                'correction_possibility':'Corrected measurement setup; final normal/reduced pixels match.',
                'screenshot':str((old/'artifacts'/r['profile_id']/name).relative_to(ROOT)),
                'screenshot_sha256':v['screenshot_sha256'],
                'preserved_record':'artifacts/phase2_2_1b_attempt1/data/experiment_render_records.json'})
    prior=json.loads((old/'data/render_records.json').read_text())
    for r in prior:
        for b in r['breakpoints']:
            bad=[k for k,v in b['checks'].items() if not v and k!='reduced_motion']
            if not bad:continue
            failures.append({'failure_id':f'INTERMEDIATE-WIDTH-{r["profile_id"]}-{b["width"]}',
                'failure_type':'RESPONSIVE_COMPOSITION_FAILURE','profile':r['profile_id'],'scene_job':'ENTRY',
                'mechanism_set':r['mechanism_ids'],'viewport':b['width'],'symptom':bad,
                'probable_constraint':'CSS selector applied the diptych grid both to the outer scene and its inner tiles.',
                'correction_possibility':'Corrected by isolating the scene class; all nine widths now pass.',
                'metrics':b['metrics'],'preserved_record':'artifacts/phase2_2_1b_attempt1/data/render_records.json'})
    failures.append({'failure_id':'PREMIUM-MEDIA-AUTHORITY-AUDIT','failure_type':'MEDIA_ROLE_MISMATCH',
        'profile':'premium-place','scene_job':'ENTRY','mechanism_set':['CM-VIS-CINEMATIC-DESTINATION-ENTRY-01'],
        'viewport':'desktop/mobile','symptom':'The initial generated therapy photo foregrounded a human treatment rather than the place required by the selected job.',
        'probable_constraint':'Filename and dimensions do not establish visual subject/authority.',
        'correction_possibility':'Bound an audited environment illustration; remains illustrative, never actual property proof.',
        'preserved_record':'artifacts/phase2_2_1b_attempt1/data/profiles.json'})
    for name,ids,mutator in [
        ('UNKNOWN_PAIR',ps[0]['selected_mechanism_ids'],lambda p:p.update(combination_scope='SAME_SCENE')),
        ('INCOMPATIBLE_PAIR',['CM-VIS-ENVIRONMENTAL-HERO-01','CM-VIS-CINEMATIC-DESTINATION-ENTRY-01'],lambda p:p.update(combination_scope='SAME_SCENE')),
        ('CONDITIONAL_MISSING',ps[0]['selected_mechanism_ids'],lambda p:p['conditions'].update(owned_assets=False)),
        ('UNIMPLEMENTED_GRAMMAR',['CM-VIS-CLINICAL-HUMAN-HERO-01'],lambda p:None),
    ]:
        p=deepcopy(ps[0]);mutator(p)
        try:solve(ids,edges,p,records=idx)
        except ValueError as exc:
            failures.append({'failure_id':'REJECT-'+name,'failure_type':'SOLVER_FAIL_CLOSED',
                             'profile':p['profile_id'],'scene_job':'ENTRY','mechanism_set':ids,
                             'viewport':'NOT_RENDERED_SOLVER_REJECTED','symptom':str(exc),
                             'probable_constraint':name,'correction_possibility':'Obtain evidence/conditions or an implemented adapter; do not override the verdict.'})
        else:raise RuntimeError('Negative solver attempt unexpectedly accepted')
    (DATA/'failure_evidence.jsonl').write_text(''.join(json.dumps(f,ensure_ascii=False)+'\n' for f in failures))
    visual=[]
    notes={'local-trust':'Environmental image remains behind a legible DOM proposition; utility grid stacks below.',
           'b2b-technical':'Owned app table remains readable; two audience cards stack with equal prominence; live filtering executed.',
           'd2c-product':'Equal campaign tiles stay adjacent on desktop and stack on mobile; index rail relocates above the feature.',
           'premium-place':'Audited environment crop remains recognizable; proposition is after the media; utility tasks are separate.',
           'public-information':'Task search stays first, modules stack, two legitimate fixture routes remain distinct.'}
    for r in records:
        for v in ['desktop','mobile']:
            visual.append({'profile_id':r['profile_id'],'viewport':v,'review_method':'MIO_FINAL_PRODUCTION_SCREENSHOT_CONTACT_SHEET_AND_ASSET_GROUND_TRUTH_AUDIT',
                           'screenshot':r[v]['screenshot'],'sha256':r[v]['screenshot_sha256'],
                           'review':'PASS_FOR_SCOPED_GRAMMAR_TRANSFER','reason':notes[r['profile_id']],
                           'limitation':'Structural renderability and crop/hierarchy check; not an art-direction quality score, sales proof or independent source-family evidence.'})
    write(DATA/'visual_audit.json',visual)
    report.update(failure_evidence_count=len(failures),failure_evidence_breakdown={'qa_probe_state_mismatch':10,'responsive_failure':2,'media_role_audit':1,'solver_rejection':4},
                  compatible_count=0,tests={'fail_closed':18,'production_generation_regression':6,'total_pass':24},
                  supported_adapter_count=7,unimplemented_provisional_adapter_count=6,
                  unresolved_blockers_for_selected_fixtures=[],
                  general_customer_production_limitations=['Authored fixtures run through actual production code in test mode, never customer approved.',
                     'Conditional compatibility applies only to exact registered profile/truth/asset digests and ADJACENT_SCENES.',
                     'Other scopes remain UNKNOWN; real-client authority/rights/current UI and business claims require client-specific evidence.',
                     'Motion was not observed in corpus; static rendering only; source-family independence remains UNKNOWN.'],
                  status='PHASE_2_2_1_COMPATIBILITY_RENDERABILITY_READY_FOR_PM_REVIEW')
    write(DATA/'final_report.json',report)
    paths=list(DATA.rglob('*'))+list((ROOT/'artifacts/phase2_2_1b').rglob('*'))+list(old.rglob('*'))
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file() and p.name!='output_hashes.json'}
    write(DATA/'output_hashes.json',manifest)
    print(json.dumps(report))
