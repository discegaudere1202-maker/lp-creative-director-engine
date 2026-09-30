import json,sys,tempfile,unittest,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_phase2_2_1a_recovery import build,hard_gate,GATES
from validate_phase2_2_1a_recovery import validate_outputs
REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parent
class RecoveryTests(unittest.TestCase):
    def test_every_under100_count_closes_gate(self):
        for key in GATES:
            counts=dict.fromkeys(GATES,100);counts[key]=99
            self.assertFalse(hard_gate(counts),key)
    def test_preflight_cannot_override_failed_capture(self):
        with tempfile.TemporaryDirectory() as d:
            inputs=Path(d)/'inputs';shutil.copytree(REPO/'data/phase2_2_1a_recovery_inputs',inputs)
            p=inputs/'official_visual_qa.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
            for r in rows:
                if r['attempt_id']=='36682051500:P16-R04-REP03':r.update(visual_state='PASS',official_state='PASS')
            p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            result=build(ROOT/'source_bundle',ROOT/'archive_audit',inputs,Path(d)/'out')
            attempts=[json.loads(x) for x in (Path(d)/'out/candidate_attempts.jsonl').read_text().splitlines()]
            self.assertFalse(next(r for r in attempts if r['attempt_id']=='36682051500:P16-R04-REP03')['accepted'])
    def test_archive_loss_fails_before_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):build(ROOT/'source_bundle',Path(d)/'missing',REPO/'data/phase2_2_1a_recovery_inputs',Path(d)/'out')
    def test_final_recovered_outputs_and_all_durable_chains(self):
        result=validate_outputs(REPO/'data/phase2_2_1a_recovery',ROOT/'archive_audit')
        self.assertEqual(result['validator'],'PASS')
    def test_missing_actual_visual_review_leaves99_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            inputs=Path(d)/'inputs';shutil.copytree(REPO/'data/phase2_2_1a_recovery_inputs',inputs)
            p=inputs/'official_visual_qa.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
            for r in rows:
                if r['attempt_id']=='36688082056:P16-R04-REP05':r.update(visual_state='PREFLIGHT_ONLY')
            p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            result=build(ROOT/'source_bundle',ROOT/'archive_audit',inputs,Path(d)/'out')
            self.assertEqual(result['aggregate']['final_usable_reference_count'],99)
            self.assertEqual(result['status'],'FAIL_CLOSED_CAPTURE_RECOVERY_INCOMPLETE')
            with self.assertRaisesRegex(ValueError,'hard gate below 100'):validate_outputs(Path(d)/'out',ROOT/'archive_audit')
    def test_output_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'out';shutil.copytree(REPO/'data/phase2_2_1a_recovery',target)
            p=target/'aggregate.json';a=json.loads(p.read_text());a['final_usable_reference_count']=100;p.write_text(json.dumps(a))
            with self.assertRaisesRegex(ValueError,'output changed'):validate_outputs(target,ROOT/'archive_audit')
if __name__=='__main__':unittest.main()
