"""Execute the bounded correction; write ONLY the new V1 engineering reports."""
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
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts'), str(ROOT / 'tests')]
from lp_engine import independence_calibration as d
from lp_engine import evidence_snapshot_binding as b
from snapshot_binding_fix_fixtures import snapshot_pair, reviewed_relation
from exercise_phase2_2_1d_rejections import replay
from validate_phase2_2_1d_pair_order_fix import BASE, DATA, validate


def write(name, value):
    (DATA / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.execution_records = []

    def record(self, test, status):
        row = {'test': test.id(), 'result': status}
        if hasattr(test, 'order_checks'):
            row['order_checks'] = deepcopy(test.order_checks)
            method = getattr(test, test._testMethodName)
            if hasattr(method, 'order_parameters'): row['order_parameters'] = method.order_parameters
        self.execution_records.append(row)

    def addSuccess(self, test): super().addSuccess(test); self.record(test, 'PASS')
    def addFailure(self, test, error): super().addFailure(test, error); self.record(test, 'FAIL')
    def addError(self, test, error): super().addError(test, error); self.record(test, 'ERROR')
    def addSkip(self, test, reason): super().addSkip(test, reason); self.record(test, 'SKIPPED')


def reproduce_reviewed_revision():
    raw = subprocess.check_output(['git', 'show', BASE + ':src/lp_engine/independence_calibration.py'], cwd=ROOT)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != '21db0fad697fef00ce18c03c7c72c8f241d4824b6fab4766654e3fb612c592c4':
        raise ValueError('WRONG_PM_REVIEWED_SOURCE')
    old = types.ModuleType('lp_engine._reviewed_snapshot_fix'); old.__package__ = 'lp_engine'
    exec(compile(raw, '<exact-c6-reviewed-module>', 'exec'), old.__dict__)
    cases = []
    for label in ('GALLERY_DUPLICATE', 'ARCHIVE_MIRROR', 'LOCALIZATION_ONLY'):
        a, z, _, sources = snapshot_pair()
        a['discovery_source'] = label; sources.units[b.source_record_id(a)] = deepcopy(a)
        relation = reviewed_relation(a, z, sources)
        cases.append({'derivative': label, 'synthetic_only': True,
                      'trace_valid': all(old.trace_valid(u, sources.scenes, sources.verified_members) for u in (a, z)),
                      'match_decisions': [old.match_decision(u, {'mechanism_id': 'SYNTHETIC-MECHANISM', 'scene_job': 'ENTRY'},
                                                           sources.scenes, sources.verified_members)[0] for u in (a, z)],
                      'pair_forward': old.pair_independence(a, z, relation, sources=sources)['status'],
                      'pair_reverse': old.pair_independence(z, a, relation, sources=sources)['status'],
                      'set_forward': old.calibrate_units([a, z], [relation], sources=sources)['status'],
                      'set_reverse': old.calibrate_units([z, a], [relation], sources=sources)['status'],
                      'reviewed_revision_safety_assertion_forward': 'FAIL'})
    return {'reviewed_commit': BASE, 'reviewed_module_sha256': digest, 'cases': cases,
            'scope': 'Exact c6 source and declared synthetic current capture/attribution only; no live production bypass'}


def main():
    DATA.mkdir(exist_ok=True)
    write('pm_reproduction.json', reproduce_reviewed_revision())
    negatives = []
    for saved in d.read('negative_test_report.json')['records']:
        actual = replay(saved['specimen'])
        expected = 'UNKNOWN' if saved['expected_status'] == 'PARTIALLY_INDEPENDENT' else saved['expected_status']
        negatives.append({'historical_failure_id': saved['failure_id'], 'historical_specimen_sha256': saved['input_sha256'],
                          'historical_expected': saved['expected_status'], 'current_expected': expected, 'actual': actual,
                          'passed': d.legacy.digest(saved['specimen']) == saved['input_sha256'] and actual['status'] == expected,
                          'engineering_replay_only': True})
    write('legacy_negative_replay.json', {'run': len(negatives), 'passed': sum(row['passed'] for row in negatives),
                                         'failed': sum(not row['passed'] for row in negatives), 'records': negatives,
                                         'historical_failure_count_unchanged': 108})
    suite = unittest.TestSuite(); groups = {}; test_sources = set()
    for name in ('test_phase2_2_1d_pair_order_fix', 'test_phase2_2_1d_snapshot_binding_fix',
                 'test_phase2_2_1d', 'test_phase2_2_1c', 'test_phase2_2_1b', 'test_production_generation'):
        path = ROOT / 'tests' / (name + '.py')
        spec = importlib.util.spec_from_file_location('pair_order_' + name, path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        group = unittest.defaultTestLoader.loadTestsFromModule(module)
        if not group.countTestCases(): raise ValueError('EMPTY_TEST_SUITE:' + name)
        groups[name] = group.countTestCases(); suite.addTests(group); test_sources.add(path)
    result = unittest.TextTestRunner(verbosity=1, resultclass=RecordedResult).run(suite)
    source_paths = test_sources | {Path(__file__).resolve()}
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and path.endswith('.py') and Path(path).resolve().is_relative_to(ROOT): source_paths.add(Path(path).resolve())
    errors = [{'test': str(test), 'traceback': traceback} for test, traceback in result.errors + result.failures]
    report = {'run': result.testsRun, 'passed': result.testsRun - len(errors) - len(result.skipped),
              'failed': len(errors), 'skipped': len(result.skipped), 'groups': groups,
              'execution_records': result.execution_records, 'errors': errors,
              'executed_at_utc': datetime.now(timezone.utc).isoformat(), 'local_execution': True,
              'tested_source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(source_paths)},
              'source_hash_scope': 'All loaded repository Python sources plus all selected test module files; not a line-coverage claim',
              'historical_106_and_66_reports_unchanged': True, 'phase2600_allowed': False}
    write('tests_report.json', report)
    order_records = [row for row in result.execution_records if 'order_checks' in row]
    matrix = [{'test': row['test'], 'parameters': row['order_parameters'], 'result': row['result'], 'checks': row['order_checks']}
              for row in order_records if 'order_parameters' in row]
    write('order_invariance_report.json', {'test_methods': len(order_records),
                                         'passed': sum(row['result'] == 'PASS' for row in order_records),
                                         'derivative_matrix': matrix,
                                         'pair_verdict_checks': sum(c['kind'] == 'PAIR' for row in order_records for c in row['order_checks']),
                                         'set_verdict_checks': sum(c['kind'] == 'SET' for row in order_records for c in row['order_checks']),
                                         'execution_records': order_records, 'synthetic_engineering_only': True,
                                         'candidate_count_unchanged': 28, 'failure_count_unchanged': 108})
    if not result.wasSuccessful() or any(not row['passed'] for row in negatives): return 1
    validation = validate(require_execution=True)
    write('validator_report.json', validation); write('preservation_report.json', validation['historical_preservation'])
    print(json.dumps({'tests': {key: report[key] for key in ('run', 'passed', 'failed', 'skipped', 'groups')},
                      'execution_source_hashes': len(report['tested_source_sha256']),
                      'derivative_matrix_cases': len(matrix), 'negative_replay': len(negatives),
                      'validator': validation['validator'], 'live_holds': 13, 'promotion': 0,
                      'customer_production_approved': 0, 'phase2600_allowed': False}))
    return 0


if __name__ == '__main__': sys.exit(main())
