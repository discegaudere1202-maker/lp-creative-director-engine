from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lp_engine import mechanism_runtime as legacy
from lp_engine import production_eligibility as gate
from lp_engine.production_generation import render_html, run_generation


class Phase221CTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = gate.read('profiles.json')
        cls.cs = gate.contracts()
        cls.p = cls.profiles[0]
        cls.raw = gate.read('inputs/local-trust.json')
        cls.c = cls.cs[cls.p['selected_mechanism_ids'][0]]
        cls.context = cls.raw['mechanism_eligibility_context']
        cls.ms, _ = legacy.database()
        cls.edges = legacy.load_jsonl(legacy.DATA / 'compatibility_edges.jsonl')
        cls.records = {r['record_id']: r for r in json.loads((legacy.DATA / 'render_records.json').read_text())}

    def test_13_source_derived_contracts_separate_maturity_and_eligibility(self):
        self.assertEqual(set(self.cs), set(self.ms))
        self.assertEqual(sum(c['adapter_status'] == 'IMPLEMENTED' for c in self.cs.values()), 10)
        self.assertEqual(sum(c['adapter_status'] == 'HOLD' for c in self.cs.values()), 3)
        self.assertTrue(all(c['current_status'] == 'PROVISIONAL_VARIANT' and c['evidence_maturity'] == 'CANDIDATE'
                            and c['production_eligibility'] == 'HOLD' and c['promotion_count'] == 0 for c in self.cs.values()))

    def test_two_viewports_cannot_be_independent_units(self):
        for r in gate.independence_records():
            self.assertEqual(r['reference_count'], 1)
            self.assertEqual(r['independent_evidence_unit_count'], 1)
            self.assertEqual(r['status'], 'NOT_INDEPENDENT')
            self.assertEqual(r['agency_independence'], 'UNKNOWN')
            self.assertEqual(len(r['sources'][0]['evidence_scene_ids']), 2)

    def test_adapterless_mechanisms_fail_closed(self):
        for c in self.cs.values():
            if c['adapter_status'] == 'HOLD':
                with self.subTest(mid=c['mechanism_id']), self.assertRaisesRegex(ValueError, 'ADAPTER_HOLD'):
                    gate.check_mechanism(c, self.p['scene_content'][0], self.context, mode='test')

    def test_insufficient_independence_blocks_actual_live_generation_without_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'blocked'
            with self.assertRaisesRegex(ValueError, 'INDEPENDENCE_INSUFFICIENT_LIVE_REJECT'):
                run_generation(self.raw, target, mode='production')
            self.assertFalse(target.exists())

    def test_missing_context_cannot_bypass_gate_via_legacy_live_route(self):
        raw = deepcopy(self.raw); raw.pop('mechanism_eligibility_context')
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'ELIGIBILITY_CONTEXT_REQUIRED'):
            run_generation(raw, t, mode='production')

    def test_rights_gap_blocks_generation_before_render(self):
        raw = deepcopy(self.raw); raw['mechanism_eligibility_context']['asset_rights'] = {}
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'RIGHTS_INSUFFICIENT'):
            run_generation(raw, t, mode='test')
        raw = deepcopy(self.raw); raw['mechanism_eligibility_context']['rights_scope'] = 'UNKNOWN'
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'RIGHTS_INSUFFICIENT'):
            run_generation(raw, t, mode='test')

    def test_truth_gap_blocks_generation(self):
        raw = deepcopy(self.raw); raw['mechanism_eligibility_context']['truth_evidence'] = []
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'TRUTH_EVIDENCE_INSUFFICIENT'):
            run_generation(raw, t, mode='test')

    def test_changed_company_truth_cannot_keep_registered_fixture_permission(self):
        raw = deepcopy(self.raw); raw['company']['company_truth'] = 'Invented award and achievement'
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'FIXTURE_TRUTH_PROFILE_INPUT_TRACE_MISMATCH'):
            run_generation(raw, t, mode='test')

    def test_mobile_unsupported_rejected(self):
        c = deepcopy(self.c); c['mobile_support']['status'] = 'UNSUPPORTED'
        with self.assertRaisesRegex(ValueError, 'MOBILE_UNSUPPORTED'):
            gate.check_mechanism(c, self.p['scene_content'][0], self.context, mode='test')

    def test_motion_unknown_and_invented_animation_rejected(self):
        c = deepcopy(self.c); c['motion_support'] = 'UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'MOTION_UNOBSERVED_REJECT'):
            gate.check_mechanism(c, self.p['scene_content'][0], self.context, mode='test')
        raw = deepcopy(self.raw); raw['mechanism_eligibility_context']['requested_motion'] = 'ANIMATION'
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'MOTION_UNOBSERVED_REJECT'):
            run_generation(raw, t, mode='test')

    def test_reduced_motion_required(self):
        ctx = deepcopy(self.context); ctx['reduced_motion'] = 'UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'REDUCED_MOTION_REQUIREMENT_UNMET'):
            gate.check_mechanism(self.c, self.p['scene_content'][0], ctx, mode='test')

    def test_evidence_trace_missing_rejected(self):
        c = deepcopy(self.c); c['evidence_scene_ids'] = []
        with self.assertRaisesRegex(ValueError, 'EVIDENCE_TRACE_MISSING'):
            gate.check_mechanism(c, self.p['scene_content'][0], self.context, mode='test')

    def test_each_accessibility_constraint_fails_closed(self):
        for key in gate.ACCESSIBILITY:
            raw = deepcopy(self.raw); raw['mechanism_eligibility_context']['accessibility'][key] = False
            with self.subTest(key=key), tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'ACCESSIBILITY_CONSTRAINT_UNMET'):
                run_generation(raw, t, mode='test')

    def test_each_implementation_constraint_fails_closed(self):
        for key in gate.IMPLEMENTATION:
            raw = deepcopy(self.raw); raw['mechanism_eligibility_context']['implementation'][key] = False
            with self.subTest(key=key), tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError, 'IMPLEMENTATION_CONSTRAINT_UNMET'):
                run_generation(raw, t, mode='test')

    def test_conditional_missing_conditions_rejected_by_solver_after_gate(self):
        for key in legacy.REQUIRED_CONDITIONS:
            p = deepcopy(self.p); p['conditions'][key] = False
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'CONDITIONAL_REQUIREMENT_REJECTED'):
                legacy.solve(p['selected_mechanism_ids'], self.edges, p, records=self.records)

    def test_unknown_edge_rejected_by_solver(self):
        p = deepcopy(self.p); p['combination_scope'] = 'SAME_SCENE'
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_PAIR_REJECTED'):
            legacy.solve(p['selected_mechanism_ids'], self.edges, p, records=self.records)

    def test_incompatible_edge_rejected_by_solver(self):
        p = deepcopy(self.p); p['combination_scope'] = 'SAME_SCENE'
        ids = ['CM-VIS-ENVIRONMENTAL-HERO-01', 'CM-VIS-CINEMATIC-DESTINATION-ENTRY-01']
        with self.assertRaisesRegex(ValueError, 'INCOMPATIBLE_PAIR_REJECTED'):
            legacy.solve(ids, self.edges, p, records=self.records)

    def test_generated_image_cannot_be_proof(self):
        scene = deepcopy(self.p['scene_content'][0]); scene['assets'][0]['evidence_role'] = 'CLIENT_PROOF'
        with self.assertRaisesRegex(ValueError, 'GENERATED_VISUAL_CANNOT_SUPPLY_PROOF'):
            gate.check_mechanism(self.c, scene, self.context, mode='test')

    def test_all_eight_generate_through_real_path_but_never_client_approved(self):
        for p in self.profiles:
            with self.subTest(pid=p['profile_id']), tempfile.TemporaryDirectory() as t:
                raw = gate.read('inputs/' + p['profile_id'] + '.json')
                r = run_generation(raw, t, mode='test')
                self.assertFalse(r.production_output_allowed)
                self.assertEqual(r.manifest['output_status'], 'NOT_PRODUCTION_APPROVED')
                self.assertTrue(Path(t, 'production_eligibility_plan.json').is_file())
                self.assertEqual(len(r.manifest['production_eligibility']['decisions']), len(p['selected_mechanism_ids']))

    def test_renderer_cannot_bypass_or_forge_eligibility_trace(self):
        plan = gate.build_plan('local-trust', self.raw, mode='test')
        plan['eligibility_gate']['customer_publication_allowed'] = True
        with self.assertRaisesRegex(ValueError, 'ELIGIBILITY_RENDER_TRACE_MISMATCH'):
            render_html({'production_eligibility_plan': plan})

    def test_contract_and_independence_forgery_rejected(self):
        original = gate.read
        def bad(name):
            data = original(name)
            if name == 'eligibility_contracts.json':
                data[0]['production_eligibility'] = 'ELIGIBLE'
            return data
        with patch.object(gate, 'read', bad), self.assertRaisesRegex(ValueError, 'ELIGIBILITY_CONTRACT_NOT_SOURCE_DERIVED'):
            gate.build_plan('local-trust', self.raw, mode='test')
        def independent(name):
            data = original(name)
            if name == 'independence.json':
                data[0]['status'] = 'VERIFIED_INDEPENDENT'
            return data
        with patch.object(gate, 'read', independent), self.assertRaisesRegex(ValueError, 'INDEPENDENCE_LEDGER_NOT_SOURCE_DERIVED'):
            gate.build_plan('local-trust', self.raw, mode='test')

    def test_no_reference_pixels_required_for_specs(self):
        original = Path.read_bytes
        def no_pixels(p):
            if any(x in str(p) for x in ['scene_crops', 'original_archives', 'durable_readback']):
                raise AssertionError('Reference pixels forbidden')
            return original(p)
        with patch.object(Path, 'read_bytes', no_pixels), patch('zipfile.ZipFile', side_effect=AssertionError('Reference archives forbidden')):
            for p in self.profiles:
                plan = gate.build_plan(p['profile_id'], gate.read('inputs/' + p['profile_id'] + '.json'), mode='test')
                self.assertTrue(plan['base_plan']['scenes'])

    def test_unclassified_scene_job_is_not_guessed(self):
        c = self.cs['CM-VIS-CULTURE-FULLBLEED-WORK-ENTRY-01']
        self.assertEqual(c['supported_scene_jobs'], [])
        self.assertEqual(c['adapter_status'], 'HOLD')

    def test_phase_b_17_failures_byte_preserved(self):
        import hashlib
        hashes = gate.read('phase_b_preservation.json')
        for name, expected in hashes.items():
            self.assertEqual(hashlib.sha256((gate.ROOT / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(len((legacy.DATA / 'failure_evidence.jsonl').read_text().splitlines()), 17)

    def test_independent_validator_rejects_missing_phase_c_pixels(self):
        import sys
        sys.path.insert(0, str(gate.ROOT / 'scripts'))
        from validate_phase2_2_1c import validate
        original = Path.read_bytes
        def lost(p):
            if 'artifacts/phase2_2_1c' in str(p) and p.name == 'mobile-eligibility-full.png':
                raise FileNotFoundError('Injected missing Phase C mobile screenshot')
            return original(p)
        with patch.object(Path, 'read_bytes', lost), self.assertRaises(FileNotFoundError):
            validate()

    def test_independent_validator_rejects_forged_final_mobile_pass(self):
        import sys
        sys.path.insert(0, str(gate.ROOT / 'scripts'))
        from validate_phase2_2_1c import validate
        original = gate.read
        def bad(name):
            x = original(name)
            if name == 'render_records.json':
                x[0]['mobile']['checks']['overflow'] = False
                x[0]['mobile']['status'] = 'PASS'
            return x
        with patch.object(gate, 'read', bad), self.assertRaises(AssertionError):
            validate()


if __name__ == '__main__':
    unittest.main()
