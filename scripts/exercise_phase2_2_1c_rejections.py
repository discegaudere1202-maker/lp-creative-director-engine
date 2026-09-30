#!/usr/bin/env python3
"""Execute deliberate bad inputs and preserve observed denials, never fabricate PASS."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lp_engine import production_eligibility as gate
from lp_engine import mechanism_runtime as legacy
from lp_engine.production_generation import run_generation, render_html


def exercise():
    target = gate.DATA / 'failure_evidence.jsonl'
    if target.exists():
        raise RuntimeError('Failure checkpoint already exists; do not overwrite')
    p = gate.read('profiles.json')[0]; raw = gate.read('inputs/local-trust.json')
    cs = gate.contracts(); c = cs[p['selected_mechanism_ids'][0]]
    ctx = raw['mechanism_eligibility_context']; scene = p['scene_content'][0]
    records = []
    def attempt(name, category, expected, specimen, call):
        try:
            call()
        except ValueError as e:
            assert expected in str(e), (name, str(e))
            records.append({'failure_id': 'P221C-REJECT-' + str(len(records) + 1).zfill(3),
                'case': name, 'category': category, 'intentional_negative': True,
                'input_sha256': legacy.digest(specimen), 'specimen': specimen,
                'observed_exception': type(e).__name__, 'observed_reason': str(e),
                'result': 'FAIL_CLOSED_PASS', 'render_executed': False, 'phase2600_allowed': False})
        else:
            raise AssertionError('FAIL_OPEN: ' + name)
    def direct(contract=c, content=scene, context=ctx, mode='test'):
        return gate.check_mechanism(contract, content, context, mode=mode)
    for contract in cs.values():
        if contract['adapter_status'] == 'HOLD':
            attempt(contract['mechanism_id'], 'Adapter Failure', 'ADAPTER_HOLD', contract,
                    lambda contract=contract: direct(contract=contract))
    attempt('insufficient independence live', 'Independence Hold', 'INDEPENDENCE_INSUFFICIENT_LIVE_REJECT', c,
            lambda: direct(mode='production'))
    for name, key, value, reason, category in [
        ('truth empty', 'truth_evidence', [], 'TRUTH_EVIDENCE_INSUFFICIENT', 'Truth Hold'),
        ('rights unknown', 'rights_scope', 'UNKNOWN', 'RIGHTS_INSUFFICIENT', 'Rights Hold'),
        ('asset rights missing', 'asset_rights', {}, 'RIGHTS_INSUFFICIENT', 'Rights Hold'),
        ('invented motion', 'requested_motion', 'ANIMATION', 'MOTION_UNOBSERVED_REJECT', 'Eligibility Reject'),
        ('reduced motion absent', 'reduced_motion', 'UNKNOWN', 'REDUCED_MOTION_REQUIREMENT_UNMET', 'Eligibility Reject'),
    ]:
        bad = deepcopy(ctx); bad[key] = value
        attempt(name, category, reason, bad, lambda bad=bad: direct(context=bad))
    for name, key, value, reason in [
        ('mobile unsupported', 'mobile_support', {'status': 'UNSUPPORTED'}, 'MOBILE_UNSUPPORTED'),
        ('desktop unsupported', 'desktop_support', {'status': 'UNSUPPORTED'}, 'DESKTOP_UNSUPPORTED'),
        ('unknown motion', 'motion_support', 'UNKNOWN', 'MOTION_UNOBSERVED_REJECT'),
        ('trace missing', 'evidence_scene_ids', [], 'EVIDENCE_TRACE_MISSING'),
    ]:
        bad = deepcopy(c); bad[key] = value
        attempt(name, 'Eligibility Reject', reason, bad, lambda bad=bad: direct(contract=bad))
    for field, key, reason in [('accessibility', 'keyboard_focus', 'ACCESSIBILITY_CONSTRAINT_UNMET'),
                              ('implementation', 'mobile_recomposition', 'IMPLEMENTATION_CONSTRAINT_UNMET')]:
        bad = deepcopy(ctx); bad[field][key] = False
        attempt(field + ' missing', 'Eligibility Reject', reason, bad, lambda bad=bad: direct(context=bad))
    bad = deepcopy(scene); bad['assets'][0]['evidence_role'] = 'CLIENT_PROOF'
    attempt('illustration as proof', 'Truth Hold', 'GENERATED_VISUAL_CANNOT_SUPPLY_PROOF', bad,
            lambda: direct(content=bad))
    edges = legacy.load_jsonl(legacy.DATA / 'compatibility_edges.jsonl')
    ri = {r['record_id']: r for r in json.loads((legacy.DATA / 'render_records.json').read_text())}
    bad = deepcopy(p); bad['conditions']['mobile_recompose'] = False
    attempt('conditional condition absent', 'Solver Reject', 'CONDITIONAL_REQUIREMENT_REJECTED', bad,
            lambda: legacy.solve(bad['selected_mechanism_ids'], edges, bad, records=ri))
    unknown = deepcopy(p); unknown['combination_scope'] = 'SAME_SCENE'
    attempt('unknown required edge', 'Solver Reject', 'UNKNOWN_PAIR_REJECTED', unknown,
            lambda: legacy.solve(unknown['selected_mechanism_ids'], edges, unknown, records=ri))
    incompatible = deepcopy(unknown)
    incompatible['selected_mechanism_ids'] = ['CM-VIS-ENVIRONMENTAL-HERO-01', 'CM-VIS-CINEMATIC-DESTINATION-ENTRY-01']
    attempt('incompatible edge', 'Solver Reject', 'INCOMPATIBLE_PAIR_REJECTED', incompatible,
            lambda: legacy.solve(incompatible['selected_mechanism_ids'], edges, incompatible, records=ri))
    forged = deepcopy(raw); forged['company']['company_truth'] = 'Unverified achievement'
    with tempfile.TemporaryDirectory() as t:
        attempt('changed client truth with fixture token', 'Truth Hold', 'FIXTURE_TRUTH_PROFILE_INPUT_TRACE_MISMATCH', forged,
                lambda: run_generation(forged, Path(t) / 'blocked', mode='test'))
        assert not (Path(t) / 'blocked').exists()
    plan = gate.build_plan('local-trust', raw, mode='test')
    plan['eligibility_gate']['customer_publication_allowed'] = True
    attempt('forged renderer permission', 'Eligibility Reject', 'ELIGIBILITY_RENDER_TRACE_MISMATCH', plan,
            lambda: render_html({'production_eligibility_plan': plan}))
    records.append({'failure_id': 'P221C-INFRA-001', 'case': 'first standalone browser attempt',
        'category': 'Browser Infrastructure Failure', 'intentional_negative': False,
        'observed_reason': 'page.goto net::ERR_CONNECTION_REFUSED at loopback port 8765 before any profile QA',
        'result': 'INFRASTRUCTURE_FAILED_NO_PASS_CREDIT', 'render_executed': False,
        'resolution': 'Run loopback HTTP server and Chromium inside one bounded collector process.',
        'phase2600_allowed': False})
    target.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in records))
    report = {'negative_cases': len(records) - 1, 'pass': len(records) - 1, 'fail': 0,
              'infrastructure_failures_retained': 1, 'phase2600_allowed': False}
    (gate.DATA / 'negative_test_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    exercise()
