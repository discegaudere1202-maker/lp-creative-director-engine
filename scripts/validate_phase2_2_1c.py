#!/usr/bin/env python3
"""Independent counts, immutable evidence, source dedupe and real browser gates."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lp_engine import production_eligibility as gate
from lp_engine import mechanism_runtime as legacy

REQUIRED_FIELDS = {'mechanism_id', 'current_status', 'adapter_status', 'adapter_id', 'adapter_version',
    'evidence_independence_status', 'compatibility_requirement', 'mobile_support', 'desktop_support',
    'motion_support', 'reduced_motion_support', 'asset_requirement', 'truth_requirement', 'rights_requirement',
    'accessibility_requirement', 'implementation_constraints', 'known_failure_modes', 'supported_scene_jobs',
    'unsupported_scene_jobs', 'production_eligibility', 'eligibility_reason', 'evidence_reference_ids', 'evidence_scene_ids'}
STAGES = ['Company Truth', 'Buyer State', 'Sales Story', 'Creative Profile', 'Mechanism Retrieval',
          'Eligibility Gate', 'Compatibility Solver', 'Combination Recipe', 'Scene Spec', 'Production Render']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    if not __debug__:
        raise RuntimeError('FAIL_CLOSED: optimized Python cannot disable validation assertions')
    cs = gate.contracts(); mechanisms, scenes = legacy.database()
    independence = gate.read('independence.json')
    assert len(cs) == len(mechanisms) == len(independence) == 13
    assert set(cs) == set(mechanisms)
    assert len({r['mechanism_id'] for r in independence}) == 13
    for mid, c in cs.items():
        assert REQUIRED_FIELDS <= set(c)
        assert c['production_eligibility'] in gate.ELIGIBILITY_STATES
        assert c['evidence_independence_status'] in gate.INDEPENDENCE_STATES
        assert c['motion_support'] == 'STATIC_ONLY' and c['source_motion_state'] == 'NOT_OBSERVED'
        assert c['current_status'] == 'PROVISIONAL_VARIANT' and c['evidence_maturity'] == 'CANDIDATE'
        assert c['promotion_count'] == 0 and c['phase2600_allowed'] is False
        source_refs = {e['reference_id'] for e in mechanisms[mid]['source_evidence']}
        assert len(source_refs) == 1 and source_refs == set(c['evidence_reference_ids'])
        for sid in c['evidence_scene_ids']:
            s = scenes[sid]
            assert s['observation_state'] == 'OBSERVED' and s['archive_status'] == 'DURABLE_VERIFIED'
    for r in independence:
        assert r['status'] == 'NOT_INDEPENDENT'
        assert len({s['independent_evidence_unit'] for s in r['sources']}) == r['independent_evidence_unit_count'] == 1
        assert r['agency_independence'] == r['campaign_independence'] == 'UNKNOWN'
    for name, h in gate.read('phase_b_preservation.json').items():
        assert sha(ROOT / name) == h, 'PHASE_B_MUTATED: ' + name
    assert len(legacy.load_jsonl(legacy.DATA / 'failure_evidence.jsonl')) == 17
    edge_states = Counter(e['compatibility_state'] for e in legacy.load_jsonl(legacy.DATA / 'compatibility_edges.jsonl'))
    assert edge_states == {'CONDITIONAL': 5, 'INCOMPATIBLE': 2, 'UNKNOWN': 76}
    profiles = gate.read('profiles.json'); records = gate.read('render_records.json')
    assert len(profiles) == len(records) == 8
    baseline = json.loads((legacy.DATA / 'profiles.json').read_text())
    assert profiles[:5] == baseline
    assert {r['profile_id'] for r in records} == {p['profile_id'] for p in profiles}
    assert len({r['record_id'] for r in records}) == 8
    idx = {r['profile_id']: r for r in records}; scene_count = 0
    for p in profiles:
        r = idx[p['profile_id']]; out = ROOT / 'artifacts/phase2_2_1c' / p['profile_id']
        raw = gate.read('inputs/' + p['profile_id'] + '.json')
        plan = json.loads((out / 'production_eligibility_plan.json').read_text())
        manifest = json.loads((out / 'generation_manifest.json').read_text())
        assert plan == gate.build_plan(p['profile_id'], raw, mode='test'), 'TRACE_REGENERATION_FAILED'
        assert manifest['mode'] == 'test' and manifest['output_status'] == 'NOT_PRODUCTION_APPROVED'
        assert manifest['production_eligibility'] == plan['eligibility_gate']
        assert plan['trace']['stages'] == STAGES == r['trace_stages']
        assert r['eligibility_gate_executed'] is True and legacy.render_pass(r)
        assert r['eligibility_plan_sha256'] == sha(out / 'production_eligibility_plan.json')
        assert r['scene_spec_sha256'] == sha(out / 'mechanism_scene_plan.json')
        assert r['html_sha256'] == sha(out / 'index.html')
        assert r['profile_digest'] == legacy.digest(p)
        assert plan['customer_publication_allowed'] is False and plan['phase2600_allowed'] is False
        for label, width in [('desktop', 1440), ('mobile', 390)]:
            v = r[label]; assert v['status'] == 'PASS' and v['width'] == width
            assert not v['errors'] and not v['requestFailures']
            assert v['metrics']['accessible'] is True and all(x['pass'] for x in v['metrics']['contrastReport'])
            assert all(x['pass'] for x in v['interactions'])
            for key in ['screenshot', 'reduced_screenshot']:
                pic = (ROOT / v[key]).resolve()
                assert ROOT in pic.parents and 'phase2_2_1c' in str(pic)
                assert pic.read_bytes().startswith(b'\x89PNG') and sha(pic) == v[key + '_sha256']
            assert v['screenshot_sha256'] == v['reduced_screenshot_sha256']
        for b in r['breakpoints']:
            assert b['metrics']['accessible'] and all(v is True for k, v in b['checks'].items() if k != 'reduced_motion')
        scene_count += len(plan['base_plan']['scenes'])
    assert scene_count == 13
    failures = legacy.load_jsonl(gate.DATA / 'failure_evidence.jsonl')
    assert len({r['failure_id'] for r in failures}) == len(failures)
    neg = gate.read('negative_test_report.json')
    actual = [r for r in failures if r.get('intentional_negative')]
    assert len(actual) == neg['negative_cases'] == neg['pass'] >= 10 and neg['fail'] == 0
    assert all(r['result'] == 'FAIL_CLOSED_PASS' and r['render_executed'] is False for r in actual)
    assert all(legacy.digest(r['specimen']) == r['input_sha256'] for r in actual)
    hashes = gate.read('output_hashes.json')
    assert hashes and all(sha(ROOT / name) == h for name, h in hashes.items()), 'OUTPUT_BYTES_CHANGED'
    adapter_counts = Counter(c['adapter_status'] for c in cs.values())
    counts = Counter(c['production_eligibility'] for c in cs.values())
    istates = Counter(r['status'] for r in independence)
    tests = gate.read('tests_report.json')
    assert tests['failed'] == 0 and tests['passed'] >= 48
    return {'status': 'PHASE_2_2_1_PRODUCTION_ELIGIBILITY_READY_FOR_PM_REVIEW',
        'validator': 'PASS', 'atomic_mechanism_count': 13,
        'adapter_implemented_count': adapter_counts['IMPLEMENTED'], 'adapter_hold_count': adapter_counts['HOLD'],
        'eligibility_counts': {k: counts[k] for k in ['ELIGIBLE', 'CONDITIONAL', 'HOLD', 'INELIGIBLE']},
        'independence_counts': {k: istates[k] for k in ['VERIFIED_INDEPENDENT', 'PARTIALLY_INDEPENDENT', 'NOT_INDEPENDENT', 'UNKNOWN']},
        'agency_independence_unknown_count': 13, 'campaign_independence_unknown_count': 13,
        'production_solver_gate': 'PASS_FAIL_CLOSED', 'multi_profile_test_count': 5,
        'additional_single_adapter_test_count': 3, 'desktop_pass': 8, 'desktop_fail': 0, 'mobile_pass': 8, 'mobile_fail': 0,
        'required_five_profile_desktop_pass': 5, 'required_five_profile_mobile_pass': 5,
        'browser_page_executions': 72, 'scene_spec_count': scene_count, 'negative_tests': neg,
        'failure_evidence_count_phase_b': 17, 'failure_evidence_count_phase_c': len(failures),
        'failure_evidence_count_total': 17 + len(failures), 'promotion_count': 0,
        'evidence_trace_qa': 'PASS', 'phase_b_preservation': 'PASS', 'tests': tests,
        'actual_customer_output_approved_count': 0, 'unresolved_checkpoint_blockers': [],
        'remaining_live_production_holds': ['All 13 mechanisms have one independent reference unit only.',
            'Agency/campaign/parent-brand relationships remain unverified; no cross-reference independence inferred.',
            'Two carousel mechanisms and one unclassified Scene Job have adapter HOLD.',
            'No client-specific truth/rights or unobserved motion is approved.'],
        'phase2600_allowed': False}


if __name__ == '__main__':
    report = validate()
    (gate.DATA / 'validator_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
