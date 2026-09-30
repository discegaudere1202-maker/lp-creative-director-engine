#!/usr/bin/env python3
"""Run scoped meaningful suites and save counts from real unittest results."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tests'))


def main():
    suite = unittest.TestSuite()
    groups = {}
    for module in ['test_phase2_2_1c', 'test_phase2_2_1b', 'test_production_generation']:
        tests = unittest.defaultTestLoader.loadTestsFromName(module)
        groups[module] = tests.countTestCases()
        suite.addTests(tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failed = len(result.failures) + len(result.errors)
    report = {'run': result.testsRun, 'passed': result.testsRun - failed - len(result.skipped),
              'failed': failed, 'skipped': len(result.skipped), 'groups': groups,
              'errors': [str(test) for test, _ in result.errors + result.failures], 'phase2600_allowed': False}
    (ROOT / 'data/phase2_2_1c/tests_report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
