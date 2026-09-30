"""Write only D test results; never overwrite the approved C report."""
import json
from pathlib import Path
import sys
import unittest
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]

def main():
    suite=unittest.TestSuite();groups={}
    for name in ['test_phase2_2_1d','test_phase2_2_1c','test_phase2_2_1b','test_production_generation']:
        spec=importlib.util.spec_from_file_location('scoped_'+name,ROOT/'tests'/ (name+'.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        tests=unittest.defaultTestLoader.loadTestsFromModule(module)
        if tests.countTestCases()==0:raise RuntimeError('EMPTY_TEST_SUITE:'+name)
        groups[name]=tests.countTestCases();suite.addTests(tests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    failed=len(result.errors)+len(result.failures)
    report={'run':result.testsRun,'passed':result.testsRun-failed-len(result.skipped),'failed':failed,'skipped':len(result.skipped),
        'groups':groups,'errors':[{'test':str(t),'traceback':tb} for t,tb in result.errors+result.failures],'phase2600_allowed':False}
    (ROOT/'data/phase2_2_1d/tests_report.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__':sys.exit(main())
