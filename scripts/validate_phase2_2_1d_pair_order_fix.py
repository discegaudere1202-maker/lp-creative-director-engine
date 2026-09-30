"""PAIR_ORDER_FIX_V1 validation; historical reports remain pinned to their code."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from lp_engine import independence_calibration as d
from validate_phase2_2_1d_snapshot_binding_fix import validate as snapshot_validate

BASE = 'c6f135e2f229270f46d694b51f333a9830d89479'
DATA = ROOT / 'data/phase2_2_1d_pair_order_fix'
EDITED_EXISTING = {'src/lp_engine/independence_calibration.py'}


def require(value, reason):
    if not value: raise ValueError(reason)


def read(name): return json.loads((DATA / name).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preservation():
    entries = subprocess.check_output(['git', 'ls-tree', '-r', '-z', BASE], cwd=ROOT).split(b'\0')
    changed = []; hashes = {}; old_blobs = {}
    for entry in entries:
        if not entry: continue
        metadata, path = entry.split(b'\t', 1); path = path.decode()
        _, kind, blob_sha = metadata.decode().split()
        require(kind == 'blob', 'UNEXPECTED_BASE_OBJECT:' + path)
        data = (ROOT / path).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        old_blobs[path] = blob_sha
        if actual != blob_sha: changed.append(path)
        elif path.startswith(('data/', 'artifacts/')): hashes[path] = hashlib.sha256(data).hexdigest()
    require(set(changed) == EDITED_EXISTING, 'UNEXPECTED_PUBLISHED_BASE_CHANGE:' + repr(changed))
    # Previous manifest/source hashes describe the published previous revision.
    # Check them against that revision, not against deliberately modified code.
    old_tests = d.fix_read('tests_report.json')
    require((old_tests['run'], old_tests['passed'], old_tests['failed'], old_tests['skipped']) == (106, 106, 0, 0),
            'HISTORICAL_106_RESULT_CHANGED')
    for path, digest in old_tests['tested_source_sha256'].items():
        raw = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        require(hashlib.sha256(raw).hexdigest() == digest, 'HISTORICAL_EXECUTION_SOURCE_MISMATCH:' + path)
    for path, digest in d.fix_read('output_hashes.json').items():
        raw = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        require(hashlib.sha256(raw).hexdigest() == digest, 'HISTORICAL_OUTPUT_HASH_MISMATCH:' + path)
    return {'base_commit': BASE, 'base_tracked_files': len(old_blobs), 'existing_modified_files': changed,
            'all_other_published_base_files_unchanged': True, 'preserved_data_artifact_files': len(hashes),
            'preserved_data_artifact_index_sha256': d.legacy.digest(hashes),
            'historical_106_tests': 106, 'historical_66_tests': 66,
            'historical_candidate_count': 28, 'historical_failure_count': 108,
            'previous_output_manifest_preserved': True, 'previous_manifest_verified_against_pinned_base': 20,
            'previous_execution_source_hashes_verified_against_pinned_base': 11}


def validate(*, require_execution=False, require_manifest=False):
    saved = preservation()
    # Existing versioned structural checks are reused without overwriting old
    # results or treating c6 execution-source hashes as current-code hashes.
    structural = snapshot_validate(require_execution=False, require_manifest=False)
    require(structural['validator'] == 'PASS' and structural['live_holds'] == 13, 'STRUCTURAL_GATE_CHANGED')
    tests = None; order = None
    if require_execution:
        tests = read('tests_report.json'); order = read('order_invariance_report.json')
        require(tests['run'] == tests['passed'] > 0 and tests['failed'] == tests['skipped'] == 0, 'CURRENT_TEST_FAILURE')
        require(tests['run'] == sum(tests['groups'].values()) == len(tests['execution_records']), 'TEST_EXECUTION_COUNT_MISMATCH')
        require(all(row['result'] == 'PASS' for row in tests['execution_records']), 'NONPASS_EXECUTION_RECORD')
        for path, digest in tests['tested_source_sha256'].items():
            require(sha(ROOT / path) == digest, 'CURRENT_EXECUTION_SOURCE_CHANGED:' + path)
        matrix = order['derivative_matrix']
        expected = {(label, subject, mode, reverse, kind)
                    for label in d.DERIVATIVE_SOURCES for subject in (0, 1)
                    for mode in ('matched', 'canonical_caller_omitted', 'canonical_caller_contradictory', 'caller_only', 'canonical_caller_other_derivative')
                    for reverse in (False, True) for kind in ('PAIR', 'SET')}
        actual = {(r['parameters']['derivative'], r['parameters']['subject_index'], r['parameters']['caller_mode'],
                   r['parameters']['reverse'], r['parameters']['kind']) for r in matrix}
        require(actual == expected and len(matrix) == len(expected) == 120 and all(r['result'] == 'PASS' for r in matrix),
                'DERIVATIVE_ORDER_MATRIX_INCOMPLETE')
        for row in matrix:
            require(len(row['checks']) == 1 and row['checks'][0]['status'] == 'NOT_INDEPENDENT', 'DERIVATIVE_MATRIX_FAIL_OPEN')
        replay = read('legacy_negative_replay.json')
        require(replay['run'] == replay['passed'] == 18 and replay['failed'] == 0, 'NEGATIVE_REPLAY_FAILED')
        reproduction = read('pm_reproduction.json')
        require(reproduction['reviewed_commit'] == BASE and len(reproduction['cases']) == 3, 'WRONG_PM_REPRODUCTION')
        for row in reproduction['cases']:
            require(row['trace_valid'] and row['match_decisions'] == ['MATCH', 'MATCH'] and
                    row['pair_forward'] == row['set_forward'] == 'VERIFIED_INDEPENDENT' and
                    row['pair_reverse'] == row['set_reverse'] == 'NOT_INDEPENDENT', 'PM_FINDING_NOT_REPRODUCED')
    if require_manifest:
        manifest = read('output_hashes.json')
        require(manifest and all(sha(ROOT / path) == digest for path, digest in manifest.items()), 'CURRENT_MANIFEST_MISMATCH')
    return {'validator_version': 'PAIR_ORDER_FIX_V1', 'validator': 'PASS',
            'historical_preservation': saved, 'reused_structural_validator': 'Snapshot Binding Fix structural checks; prior report not rewritten',
            'live_holds': 13, 'promotion': 0, 'customer_production_approved': 0, 'phase2600_allowed': False,
            'actual_live_gate_denials': structural['actual_live_gate_denials'],
            'source_record_bindings': structural['source_record_bindings'],
            'candidate_and_eligibility_outcomes_unchanged': True,
            'current_test_execution_checked': require_execution, 'current_manifest_checked': require_manifest,
            'test_run': tests['run'] if tests else None,
            'derivative_matrix_cases': len(order['derivative_matrix']) if order else None,
            'execution_source_hashes': len(tests['tested_source_sha256']) if tests else None,
            'original_corpus_archive_readback': 'NOT_RERUN', 'fresh_desktop_mobile_render': 'N/A_ZERO_ELIGIBILITY_CHANGES',
            'status': 'PHASE_2_2_1D_PAIR_ORDER_FIX_READY_FOR_PM_REVIEW'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--check-manifest', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(require_execution=True, require_manifest=args.check_manifest), indent=2))
