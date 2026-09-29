import json,os,shutil,tempfile,unittest
from pathlib import Path
from scripts.validate_phase2_1_1 import ROOT,NAMES,lines,validate

class DurableTraversalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get('PHASE2_1_1_ARCHIVE')
        if not path: raise RuntimeError('PHASE2_1_1_ARCHIVE is required: tests fail closed without materialized bytes')
        cls.archive=Path(path)

    def test_roundtrip_and_full_coverage(self):
        result=validate(archive_path=self.archive)
        self.assertEqual((result['gold'],result['archive_entries'],result['viewports']), (20,230,10))
        self.assertEqual((result['traversal_scenes'],result['observed_traversal_scenes']), (71,70))

    def fixture(self):
        t=tempfile.TemporaryDirectory();root=Path(t.name);(root/'data').mkdir();(root/'config').mkdir()
        for name in NAMES.values():shutil.copyfile(ROOT/'data'/name,root/'data'/name)
        for name in ('creative_mechanism_phase2_1_1_archive_manifest.json','creative_mechanism_phase2_1_1_traversal_coverage.json','creative_mechanism_phase2_1_1_fullpage_claims.jsonl','creative_mechanism_phase2_1_architecture_issues.jsonl','creative_mechanism_phase2_pilot_references.csv'):
            shutil.copyfile(ROOT/'data'/name,root/'data'/name)
        shutil.copyfile(ROOT/'config/creative_mechanism_db_architecture_v1_3_1.json',root/'config/creative_mechanism_db_architecture_v1_3_1.json')
        return t,root

    def mutate(self, filename, change):
        t,root=self.fixture()
        try:
            path=root/'data'/filename; rows=lines(path);change(rows)
            path.write_text(''.join(json.dumps(x)+'\n' for x in rows))
            with self.assertRaises(AssertionError):validate(root,archive_path=self.archive)
        finally:t.cleanup()

    def test_not_observed_provenance_fails(self):
        def change(rows):rows[0]['source_scene_evidence_ids']=['GOLD-P12-R01-MOBILE-TRAV-08'];rows[0]['evidence_count']=1
        self.mutate(NAMES['new_mechs'],change)

    def test_derived_count_fails(self):
        self.mutate(NAMES['new_mechs'],lambda rows:rows[0].update(evidence_count=999))

    def test_temporary_locator_fails(self):
        self.mutate(NAMES['snap'],lambda rows:rows[0].update(archive_status='TEMPORARY_CAPTURE'))

    def test_per_record_gate_cannot_be_global_pass(self):
        self.mutate(NAMES['gates'],lambda rows:rows[0].update(gate_result='PASS',strong_promotion_allowed=True))

    def test_hash_fails(self):
        self.mutate(NAMES['snap'],lambda rows:rows[0].update(content_hash='0'*64))

    def test_archive_loss_fails_closed(self):
        with self.assertRaises(AssertionError):validate(archive_path=Path('/no/such/durable/archive.zip'))

    def test_missing_closing_is_not_mined(self):
        scenes=lines(ROOT/'data'/NAMES['new']);missing=[s for s in scenes if s['observation_state']!='OBSERVED']
        self.assertEqual([s['scene_evidence_id'] for s in missing],['GOLD-P12-R01-MOBILE-TRAV-08'])
        mechs=lines(ROOT/'data'/NAMES['new_mechs'])
        self.assertFalse(any(missing[0]['scene_evidence_id'] in m['source_scene_evidence_ids'] for m in mechs))

if __name__=='__main__':unittest.main()
