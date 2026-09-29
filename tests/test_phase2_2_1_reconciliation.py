import importlib.util, pathlib, unittest
p=pathlib.Path(__file__).parents[1]/'scripts'/'validate_phase2_2_1.py'
s=importlib.util.spec_from_file_location('phase221_validator',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ReconciliationTest(unittest.TestCase):
 def test_aggregate_from_snapshot_ledger(self):
  errors,agg=m.validate('p221-recovery/work','p221-recovery/out')
  self.assertEqual([],errors)
  self.assertEqual(100,agg['attempted_reference_count'])
  self.assertEqual(73,agg['usable_reference_count'])
  self.assertEqual(27,agg['failed_reference_count'])
  with open('p221-recovery/out/creative_mechanism_phase2_2_1_calibration_reference_set.jsonl') as f: refs=[__import__('json').loads(x) for x in f]
  self.assertEqual(13,len({r['reference_id'] for r in refs}))
  self.assertEqual(13,sum(r['viewport_label']=='DESKTOP' for r in refs))
  self.assertEqual(13,sum(r['viewport_label']=='MOBILE' for r in refs))
  self.assertFalse(agg['phase2600_allowed'])
 def test_canonical_promotion_not_inferred(self):
  errors,agg=m.validate('p221-recovery/work','p221-recovery/out')
  self.assertFalse(any('unsupported promotion' in e for e in errors))
 def test_report_truth_is_not_claimed_as_ready(self):
  body=pathlib.Path('p221-recovery/out/docs/CREATIVE_MECHANISM_DB_PHASE2_2_1_SYNTHESIS_CALIBRATION_REPORT.md').read_text()
  self.assertIn('Status: BLOCKED — NOT READY FOR PM REVIEW',body)
  self.assertIn('100 usable references: **FAIL (73/100)**',body)
if __name__=='__main__': unittest.main()
