import importlib.util
import csv
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('phase2_2_process', ROOT / 'scripts/process_phase2_2_capture.py')
processor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processor)
spec2 = importlib.util.spec_from_file_location('phase2_2_mine', ROOT / 'scripts/synthesize_phase2_2_mechanisms.py')
miner = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(miner)


class SemanticTraversalTests(unittest.TestCase):
    def test_heading_anchors_define_scene_ranges_not_fixed_intervals(self):
        facts = {'headings': [
            {'tag': 'h1', 'text': 'A', 'rect': {'y': 100, 'w': 300}},
            {'tag': 'h2', 'text': 'B', 'rect': {'y': 990, 'w': 300}},
            {'tag': 'h2', 'text': 'C', 'rect': {'y': 2540, 'w': 300}},
        ], 'sections': []}
        ranges = processor.make_ranges(facts, 4000)
        self.assertEqual([0, 990, 2540], [x['y0'] for x in ranges])
        self.assertEqual(4000, ranges[-1]['y1'])

    def test_missing_semantic_copy_does_not_become_observed_job(self):
        result = processor.classify({}, {'y0': 500, 'headings': [], 'actions': [], 'sections': ['']}, 1, 3, 3000, {})
        self.assertEqual(['UNCLASSIFIED'], result)

    def test_observed_footer_job_requires_actual_footer_landmark(self):
        seg = {'y0': 2900, 'headings': [{'tag': 'h2', 'text': 'Company information', 'rect': {'y': 2900, 'w': 300}}], 'actions': [], 'sections': []}
        self.assertNotIn('CLOSING_FOOTER_NAVIGATION', processor.classify({}, seg, 2, 3, 3000, {'footer_present': False}))
        self.assertIn('CLOSING_FOOTER_NAVIGATION', processor.classify({}, seg, 2, 3, 3000, {'footer_present': True}))

    def test_mechanism_mining_uses_only_durable_observed_scene_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td); scenes = temp / 'scenes.jsonl'; refs = temp / 'refs.csv'; out = temp / 'out'
            rows = [
                {'scene_evidence_id':'S-OBS','reference_id':'R-1','observation_state':'OBSERVED','scene_job':['PROOF_TRUST'],'observed_facts':["h2 'Case studies'",'Case study: project alpha'],'visible_structure':['h2:Case studies'],'media_observation':[],'layout_observation':{},'archive_status':'DURABLE_VERIFIED','archive_locator':'https://chatgpt.com/api/library/files/libfile_test/download','scene_crop_identifier':'crop.jpg','concrete_locator':'Case studies heading'},
                {'scene_evidence_id':'S-NOTOBS','reference_id':'R-1','observation_state':'NOT_OBSERVED','scene_job':['PROOF_TRUST'],'observed_facts':["h2 'Case studies'",'Case study: project beta'],'visible_structure':['h2:Case studies'],'media_observation':[],'layout_observation':{},'archive_status':'DURABLE_VERIFIED','archive_locator':'https://chatgpt.com/api/library/files/libfile_test/download','scene_crop_identifier':'crop2.jpg','concrete_locator':'Unavailable scene'},
                {'scene_evidence_id':'S-TEMP','reference_id':'R-1','observation_state':'OBSERVED','scene_job':['PROOF_TRUST'],'observed_facts':["h2 'Case studies'",'Case study: project gamma'],'visible_structure':['h2:Case studies'],'media_observation':[],'layout_observation':{},'archive_status':'TEMPORARY_CAPTURE','archive_locator':None,'scene_crop_identifier':'crop3.jpg','concrete_locator':'Temporary scene'}]
            scenes.write_text(''.join(json.dumps(x)+'\n' for x in rows),encoding='utf-8')
            with refs.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=['reference_id','brand','business_archetype','market_scope','design_agency','campaign_family']);w.writeheader();w.writerow({'reference_id':'R-1','brand':'Brand 1','business_archetype':'LOCAL_TRUST_SERVICE','market_scope':'JP','design_agency':'UNKNOWN','campaign_family':'UNKNOWN'})
            out.mkdir();miner.main(scenes,refs,out)
            candidates=[json.loads(x) for x in (out/'creative_mechanism_phase2_2_mechanism_candidates.jsonl').read_text().splitlines()]
            case=next(x for x in candidates if x['mechanism_name']=='CUSTOMER_CASE_PROOF')
            self.assertEqual(['S-OBS'],case['source_scene_evidence_ids'])
            self.assertEqual(1,case['evidence_count']);self.assertEqual(1,case['reference_count']);self.assertEqual(1,case['unique_brand_count'])
            self.assertEqual('CANDIDATE',case['status']);self.assertFalse(case['promotion_allowed'])


if __name__ == '__main__':
    unittest.main()
