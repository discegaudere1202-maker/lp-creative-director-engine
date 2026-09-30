"""Persist actual independence denials with replayable specimens, separate from prior failures."""
from copy import deepcopy
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lp_engine import independence_calibration as d
from lp_engine import mechanism_runtime as legacy

def synthetic_pair():
    a={'reference_id':'SYNTHETIC-A','page_family':'a.example.test/','independent_evidence_unit_id':'SYNTHETIC-PAGE-A','source_contract_sha256':'a'*64,'discovery_source':'SYNTHETIC_TEST_ONLY'}
    b={'reference_id':'SYNTHETIC-B','page_family':'b.example.test/','independent_evidence_unit_id':'SYNTHETIC-PAGE-B','source_contract_sha256':'b'*64,'discovery_source':'SYNTHETIC_TEST_ONLY'}
    r={'unit_ids':['SYNTHETIC-PAGE-A','SYNTHETIC-PAGE-B'],'dimensions':{f:{'status':'VERIFIED_INDEPENDENT','basis':'Synthetic declared relationship for pure-function negative test only','snapshot_binding':'VERIFIED','snapshot_contract_digests':['a'*64,'b'*64],'primary_source_urls':['https://evidence.example.test/'+f]} for f in d.FAMILIES}}
    return a,b,r

def cases():
    result=[]
    for title,family in [('Same brand different URL','brand_family'),('Same campaign','campaign_family'),('Same agency','agency'),('Same production company','production_company'),('Same template family','template_family'),('Same source family','source_family')]:
        a,b,r=synthetic_pair()
        a['verified_family_ids']={family:['SYNTHETIC-SHARED']};b['verified_family_ids']={family:['SYNTHETIC-SHARED']}
        result.append((title,{'kind':'PAIR','left':a,'right':b,'relation':r},'NOT_INDEPENDENT'))
    a,b,r=synthetic_pair();b['discovery_source']='GALLERY_DUPLICATE';result.append(('Gallery duplicate',{'kind':'PAIR','left':a,'right':b,'relation':r},'NOT_INDEPENDENT'))
    a,b,r=synthetic_pair();b=deepcopy(a);b['viewport']='MOBILE';result.append(('Desktop Mobile duplicate',{'kind':'PAIR','left':a,'right':b,'relation':r},'NOT_INDEPENDENT'))
    for family,title in [('agency','Unknown agency'),('campaign_family','Unknown campaign'),('template_family','Unknown template family')]:
        a,b,r=synthetic_pair();r['dimensions'][family]['status']='UNKNOWN'
        result.append((title,{'kind':'PAIR','left':a,'right':b,'relation':r},'PARTIALLY_INDEPENDENT'))
    a,b,r=synthetic_pair();result.append(('Different domains without attribution',{'kind':'PAIR','left':a,'right':b,'relation':None},'UNKNOWN'))
    a,b,r=synthetic_pair()
    for claim in r['dimensions'].values():claim['snapshot_binding']='UNVERIFIED_HISTORICAL_CASE'
    result.append(('Historical maker without snapshot binding',{'kind':'PAIR','left':a,'right':b,'relation':r},'UNKNOWN'))
    a,b,r=synthetic_pair()
    for claim in r['dimensions'].values():claim['primary_source_urls']=[]
    result.append(('Attribution assertion without primary source',{'kind':'PAIR','left':a,'right':b,'relation':r},'UNKNOWN'))
    mechanisms,_=legacy.database();c=deepcopy(d.read('candidate_reviews.json')[0]);m=mechanisms[c['mechanism_id']]
    c['mechanism_match_basis']={a:{'status':'MATCH','observation':'Synthetic assertion, not admitted evidence'} for a in d.AXES}
    c['mechanism_match_basis']['media_role']['status']='PARTIAL'
    result.append(('Weak mechanism similarity',{'kind':'MATCH','candidate':c},'HOLD'))
    c=deepcopy(c);c['mobile_scene_ids']=[]
    result.append(('Evidence trace missing',{'kind':'MATCH','candidate':c},'REJECT'))
    c=deepcopy(d.read('candidate_reviews.json')[0]);c['source_contract_sha256']='0'*64
    result.append(('Contract trace missing',{'kind':'MATCH','candidate':c},'REJECT'))
    c=deepcopy(d.read('candidate_reviews.json')[0]);c['mechanism_match_basis']['composition']['status']='MISMATCH'
    result.append(('Atomic mismatch despite similar style',{'kind':'MATCH','candidate':c},'REJECT'))
    return result

def replay(specimen):
    if specimen['kind']=='PAIR':
        return d.pair_independence(specimen['left'],specimen['right'],specimen['relation'])
    mechanisms,_=legacy.database()
    scenes={r['scene_evidence_id']:r for r in legacy.load_jsonl(ROOT/'data/phase2_2_1a_recovery/scene_evidence.jsonl')}
    rb=d.read('corpus_readback.json')
    verified={(r['archive_id'],r['archive_member']):r['sha256'] for r in rb['members'] if r['result']=='PASS'}
    state,reason=d.match_decision(specimen['candidate'],mechanisms[specimen['candidate']['mechanism_id']],scenes,verified)
    return {'status':state,'reason':reason}

def run():
    rows=[]
    for n,(title,specimen,expected) in enumerate(cases()):
        actual=replay(specimen)
        passed=actual['status']==expected and actual['status']!='VERIFIED_INDEPENDENT'
        rows.append({'failure_id':'P221D-NEG-%03d'%(n+1),'category':'INDEPENDENCE_OR_MATCH_REJECT','case':title,
            'specimen':specimen,'input_sha256':legacy.digest(specimen),'expected_status':expected,'actual':actual,
            'result':'FAIL_CLOSED_PASS' if passed else 'FAIL','intentional_negative':True,'render_executed':False,
            'synthetic_test_only':True,'phase2600_allowed':False})
    report={'cases':len(rows),'passed':sum(r['result']=='FAIL_CLOSED_PASS' for r in rows),'failed':sum(r['result']!='FAIL_CLOSED_PASS' for r in rows),'records':rows,'phase2600_allowed':False}
    (d.DATA/'negative_test_report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    report=run();print(json.dumps({k:v for k,v in report.items() if k!='records'}));sys.exit(bool(report['failed']))
