"""Execute bounded fix regressions; write new engineering reports only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
from lp_engine import independence_calibration as d
from lp_engine import evidence_snapshot_binding as b
from lp_engine import mechanism_runtime as legacy
from snapshot_binding_fix_fixtures import snapshot_pair,replace_capture
from exercise_phase2_2_1d_rejections import replay
from validate_phase2_2_1d_snapshot_binding_fix import BASE,binding_index,validate

def write(name,value):
    (d.FIX_DATA/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.execution_records=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.execution_records.append({'test':test.id(),'result':'PASS'})
    def addFailure(self,test,error):
        super().addFailure(test,error);self.execution_records.append({'test':test.id(),'result':'FAIL'})
    def addError(self,test,error):
        super().addError(test,error);self.execution_records.append({'test':test.id(),'result':'ERROR'})
    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.execution_records.append({'test':test.id(),'result':'SKIPPED','reason':reason})

def reproduce_old_module():
    raw=subprocess.check_output(['git','show',BASE+':src/lp_engine/independence_calibration.py'],cwd=ROOT)
    digest=hashlib.sha256(raw).hexdigest()
    if digest!='2c7b21ca3d9e02c2cde526470ce039305216d604935c195262534ca6223a6f5f':raise ValueError('WRONG_PM_REVIEWED_MODULE')
    old=types.ModuleType('lp_engine._reviewed_phase_d');old.__package__='lp_engine'
    exec(compile(raw,'<exact-reviewed-D-module>','exec'),old.__dict__)
    rows=[]
    for keep_ids in (False,True):
        a,z,_,sources=snapshot_pair()
        relation={'unit_ids':[a['independent_evidence_unit_id'],z['independent_evidence_unit_id']],
            'dimensions':{family:{'status':'VERIFIED_INDEPENDENT','basis':'Declared synthetic PM reproduction',
                'primary_source_urls':['https://evidence.example.test/'+family],'snapshot_binding':'VERIFIED',
                'snapshot_contract_digests':[a['source_contract_sha256']]*2} for family in d.FAMILIES}}
        positive=old.pair_independence(a,z,relation)['status']
        for label in ('DESKTOP','MOBILE'):replace_capture(z,sources,label,2,keep_scene_id=keep_ids)
        trace=old.trace_valid(z,sources.scenes,sources.verified_members)
        match=old.match_decision(z,{'mechanism_id':'SYNTHETIC-MECHANISM','scene_job':'ENTRY'},sources.scenes,sources.verified_members)[0]
        result=old.pair_independence(a,z,relation)['status']
        if not trace or match!='MATCH' or result!='VERIFIED_INDEPENDENT' or positive!='VERIFIED_INDEPENDENT':raise ValueError('PM_FINDING_NOT_REPRODUCED')
        rows.append({'case':'SAME_SCENE_IDS_NEW_REGISTERED_HASH' if keep_ids else 'NEW_PC_MOBILE_SCENE_IDS',
            'same_mechanism_contract':a['source_contract_sha256']==z['source_contract_sha256'],
            'positive_control':positive,'trace_valid':trace,'match_decision':match,'old_result':result,
            'old_safety_assertion':'FAIL','synthetic_only':True})
    return {'reviewed_commit':BASE,'reviewed_module_sha256':digest,'mutation_cases':rows,
            'scope':'Isolated exact old module / declared synthetic records; no capture or production bypass claimed'}

def main():
    # This re-derives subjects/summary ONLY. Stored reviewer assertions and cited
    # evidence are never generated, migrated or updated by this command.
    assertions=(d.FIX_DATA/'family_assertions.json').read_bytes()
    attribution=(d.FIX_DATA/'attribution_evidence.json').read_bytes()
    write('calibration.json',d.derive())
    write('snapshot_binding_index.json',binding_index(d.evidence_sources()))
    write('pm_reproduction.json',reproduce_old_module())
    records=[]
    for saved in d.read('negative_test_report.json')['records']:
        specimen=saved['specimen'];actual=replay(specimen)
        expected='UNKNOWN' if saved['expected_status']=='PARTIALLY_INDEPENDENT' else saved['expected_status']
        passed=legacy.digest(specimen)==saved['input_sha256'] and actual['status']==expected and actual['status']!='VERIFIED_INDEPENDENT'
        records.append({'historical_failure_id':saved['failure_id'],'historical_specimen_sha256':saved['input_sha256'],
            'historical_expected':saved['expected_status'],'current_expected':expected,'actual':actual,
            'passed':passed,'kind':specimen['kind'],'engineering_replay_only':True})
    negative={'run':len(records),'passed':sum(r['passed'] for r in records),'failed':sum(not r['passed'] for r in records),
              'records':records,'historical_failure_count_unchanged':108,'phase2600_allowed':False}
    write('legacy_negative_replay.json',negative)
    suite=unittest.TestSuite();groups={};source_paths=[]
    for name in ('test_phase2_2_1d_snapshot_binding_fix','test_phase2_2_1d','test_phase2_2_1c','test_phase2_2_1b','test_production_generation'):
        path=ROOT/'tests'/(name+'.py')
        spec=importlib.util.spec_from_file_location('snapshot_fix_'+name,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        group=unittest.defaultTestLoader.loadTestsFromModule(module)
        groups[name]=group.countTestCases();suite.addTests(group);source_paths.append(str(path.relative_to(ROOT)))
    for path in ('src/lp_engine/independence_calibration.py','src/lp_engine/evidence_snapshot_binding.py',
                 'src/lp_engine/production_eligibility.py','scripts/snapshot_binding_fix_fixtures.py',
                 'scripts/validate_phase2_2_1d_snapshot_binding_fix.py','scripts/verify_phase2_2_1d_snapshot_binding_fix.py'):
        source_paths.append(path)
    result=unittest.TextTestRunner(verbosity=1,resultclass=RecordedResult).run(suite)
    errors=[{'test':str(test),'traceback':traceback} for test,traceback in result.errors+result.failures]
    report={'run':result.testsRun,'passed':result.testsRun-len(errors)-len(result.skipped),'failed':len(errors),
            'skipped':len(result.skipped),'groups':groups,'errors':errors,
            'execution_records':result.execution_records,'executed_at_utc':datetime.now(timezone.utc).isoformat(),
            'tested_source_sha256':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths},
            'local_execution':True,'historical_66_report_unchanged':True,'phase2600_allowed':False}
    history_path=d.FIX_DATA/'test_execution_history.json'
    history=json.loads(history_path.read_text()) if history_path.exists() else []
    report['execution_id']='LOCAL_FIX_RUN_'+str(len(history)+1)
    write('tests_report.json',report)
    write('test_execution_history.json',history+[report])
    if not result.wasSuccessful() or negative['failed']:return 1
    require_unchanged=(assertions==(d.FIX_DATA/'family_assertions.json').read_bytes() and attribution==(d.FIX_DATA/'attribution_evidence.json').read_bytes())
    if not require_unchanged:raise ValueError('ASSERTIONS_OR_ATTRIBUTION_SILENTLY_REWRITTEN')
    validation=validate(require_execution=True)
    write('validator_report.json',validation)
    write('preservation_report.json',validation['historical_preservation'])
    print(json.dumps({'tests':{k:v for k,v in report.items() if k not in ('tested_source_sha256','errors')},
        'legacy_negative_replay':{k:v for k,v in negative.items() if k!='records'},'validator':validation['validator'],
        'live_holds':13,'promotion':0,'customer_production_approved':0,'phase2600_allowed':False}))
    return 0

if __name__=='__main__':sys.exit(main())
