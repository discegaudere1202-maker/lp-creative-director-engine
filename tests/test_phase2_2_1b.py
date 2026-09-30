from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lp_engine.mechanism_runtime import (
    ROOT,DATA,database,derive_scene_plan,load_jsonl,multi_profile_gate,
    promotion_allowed,render_pass,render_scene_html,solve,validate_edge,validate_scene_plan,
)
from lp_engine.production_generation import run_generation


class Phase221BTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,_=database()
        cls.edges=load_jsonl(DATA/'compatibility_edges.jsonl')
        cls.profiles=json.loads((DATA/'profiles.json').read_text())
        cls.records=json.loads((DATA/'render_records.json').read_text())
        cls.idx={r['record_id']:r for r in cls.records}

    def test_unsupported_edge_cannot_become_compatible(self):
        e=deepcopy(next(e for e in self.edges if e['compatibility_state']=='UNKNOWN'))
        e['compatibility_state']='COMPATIBLE'
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_EDGE'):
            validate_edge(e,self.m,render_records=self.idx)

    def test_unknown_pair_not_automatically_promoted(self):
        p=deepcopy(self.profiles[0]);p['combination_scope']='SAME_SCENE'
        with self.assertRaisesRegex(ValueError,'UNKNOWN_PAIR_REJECTED'):
            solve(p['selected_mechanism_ids'],self.edges,p,records=self.idx)
        self.assertEqual(sum(e['compatibility_state']=='UNKNOWN' for e in self.edges),76)

    def test_incompatible_pair_not_in_recipe(self):
        p=deepcopy(self.profiles[0]);p['combination_scope']='SAME_SCENE'
        ids=['CM-VIS-ENVIRONMENTAL-HERO-01','CM-VIS-CINEMATIC-DESTINATION-ENTRY-01']
        with self.assertRaisesRegex(ValueError,'INCOMPATIBLE_PAIR_REJECTED'):
            solve(ids,self.edges,p,records=self.idx)

    def test_conditional_pair_rejects_each_missing_condition(self):
        for condition in self.profiles[0]['conditions']:
            p=deepcopy(self.profiles[0]);p['conditions'][condition]=False
            with self.subTest(condition=condition),self.assertRaisesRegex(ValueError,'CONDITIONAL_REQUIREMENT_REJECTED'):
                solve(p['selected_mechanism_ids'],self.edges,p,records=self.idx)

    def test_profile_digest_is_part_of_scoped_constraint(self):
        p=deepcopy(self.profiles[0]);p['buyer_problem']='different job'
        with self.assertRaisesRegex(ValueError,'PROFILE_OUTSIDE_TESTED_DIGEST'):
            solve(p['selected_mechanism_ids'],self.edges,p,records=self.idx)

    def test_scene_spec_traces_every_grammar_and_scene(self):
        for p in self.profiles:
            plan=json.loads((ROOT/'artifacts/phase2_2_1b'/p['profile_id']/'mechanism_scene_plan.json').read_text())
            validate_scene_plan(plan,p,self.m,self.edges,self.idx)
            bad=deepcopy(plan);bad['scenes'][0]['grammar']['composition_primitive']='untraced composition'
            with self.assertRaisesRegex(ValueError,'SCENE_SPEC_NOT_REGENERABLE_FROM_EVIDENCE'):
                validate_scene_plan(bad,p,self.m,self.edges,self.idx)

    def test_spec_regenerates_with_all_reference_images_and_archives_inaccessible(self):
        original=Path.read_bytes
        def restricted(path):
            if any(marker in str(path) for marker in ['traversal','scene_crops','original_archives','durable_readback']):
                raise AssertionError('Reference pixels may not generate Scene Specs')
            return original(path)
        with patch.object(Path,'read_bytes',restricted),patch('zipfile.ZipFile',side_effect=AssertionError('No source archive reads')):
            for p in self.profiles:
                recipe=solve(p['selected_mechanism_ids'],self.edges,p,records=self.idx)
                regenerated=derive_scene_plan(p,self.m,recipe)
                saved=json.loads((ROOT/'artifacts/phase2_2_1b'/p['profile_id']/'mechanism_scene_plan.json').read_text())
                self.assertEqual(regenerated,saved)

    def test_unexecuted_production_or_browser_never_passes(self):
        for key in ['browser_executed','production_path_executed']:
            r=deepcopy(self.records[0]);r[key]=False
            self.assertFalse(render_pass(r))
        e=deepcopy(next(e for e in self.edges if e['compatibility_state']=='CONDITIONAL'))
        rid=e['render_evidence_ids'][0];idx=deepcopy(self.idx);idx[rid]['production_path_executed']=False
        with self.assertRaisesRegex(ValueError,'UNEXECUTED_OR_FAILED_EDGE'):
            validate_edge(e,self.m,render_records=idx)

    def test_single_profile_cannot_pass_multi_profile_gate(self):
        self.assertFalse(multi_profile_gate([self.records[0]]*5))
        self.assertTrue(multi_profile_gate(self.records))

    def test_mobile_failure_not_hidden_by_desktop_pass(self):
        r=deepcopy(self.records[0]);self.assertEqual(r['desktop']['status'],'PASS')
        r['mobile']['status']='FAIL';r['mobile']['checks']['overflow']=False
        self.assertFalse(render_pass(r));self.assertFalse(multi_profile_gate([r]+self.records[1:]))

    def test_intermediate_width_failure_cannot_pass_pair_calibration(self):
        r=deepcopy(self.records[0]);r['breakpoints'][0]['checks']['responsive_recomposition']=False
        self.assertFalse(render_pass(r))

    def test_actual_screenshot_loss_fails_independent_validator(self):
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        from validate_phase2_2_1b import validate
        original=Path.read_bytes
        def lost(path):
            if path.suffix=='.png' and 'accepted' in path.name:
                raise FileNotFoundError('Injected actual screenshot loss')
            return original(path)
        with patch.object(Path,'read_bytes',lost),self.assertRaises(FileNotFoundError):
            validate()

    def test_promotion_requires_all_evidence_dimensions(self):
        full={'independent_reference_count':2,'cross_profile_count':2,'source_family_independence':'VERIFIED','renderability':True,'compatibility':True}
        self.assertFalse(promotion_allowed(self.m[next(iter(self.m))],full))
        for key in full:
            e=deepcopy(full);e[key]=False
            self.assertFalse(promotion_allowed(self.m[next(iter(self.m))],e))
        self.assertTrue(all(m['promotion_state']=='CANDIDATE' for m in self.m.values()))

    def test_mock_only_check_set_is_insufficient(self):
        r=deepcopy(self.records[0]);r['desktop']['checks']={'html_generated':True}
        self.assertFalse(render_pass(r))

    def test_asset_resolution_or_hash_loss_fails_closed(self):
        p=deepcopy(self.profiles[0]);p['scene_content'][0]['assets'][0]['sha256']='0'*64
        recipe=solve(self.profiles[0]['selected_mechanism_ids'],self.edges,self.profiles[0],records=self.idx)
        with self.assertRaisesRegex(ValueError,'ASSET_HASH_OR_PATH_MISMATCH'):
            derive_scene_plan(p,self.m,recipe)

    def test_renderer_rejects_untraced_scene_plan(self):
        p=self.profiles[0]
        plan=derive_scene_plan(p,self.m,solve(p['selected_mechanism_ids'],self.edges,p,records=self.idx))
        plan['scenes'][0]['content']['headline']='Unverified outcome guarantee'
        with self.assertRaisesRegex(ValueError,'SCENE_SPEC_NOT_REGENERABLE_FROM_EVIDENCE'):
            render_scene_html(plan)

    def test_fixture_cannot_be_production_approved(self):
        raw=json.loads((DATA/'inputs/local-trust.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'CALIBRATION_FIXTURE_CANNOT_BE_CUSTOMER_PRODUCTION'):
                run_generation(raw,tmp,mode='production')
            r=run_generation(raw,tmp,mode='test')
            self.assertFalse(r.production_output_allowed)
            self.assertEqual(r.manifest['mechanism_rendering']['recipe_status'],'CONDITIONALLY_ACCEPTED')

    def test_unimplemented_mechanism_fails_closed(self):
        p=self.profiles[0]
        with self.assertRaisesRegex(ValueError,'IMPLEMENTATION_BLOCKER_UNIMPLEMENTED_GRAMMAR'):
            solve(['CM-VIS-CLINICAL-HUMAN-HERO-01'],self.edges,p,records=self.idx)


if __name__=='__main__':unittest.main()
