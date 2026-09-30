from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from lp_engine import independence_calibration as d
from lp_engine import mechanism_runtime as legacy
from lp_engine import production_eligibility as c
from lp_engine.production_generation import run_generation
sys.path.insert(0,str(legacy.ROOT/'scripts'))
from exercise_phase2_2_1d_rejections import cases, replay, synthetic_pair

class Phase221DTest(unittest.TestCase):
    def test_required_negative_cases_fail_closed(self):
        for name,specimen,expected in cases():
            with self.subTest(name=name):
                actual=replay(specimen)
                self.assertEqual(actual['status'],expected)
                self.assertNotEqual(actual['status'],'VERIFIED_INDEPENDENT')

    def test_synthetic_positive_control_requires_every_bound_family_dimension(self):
        a,b,r=synthetic_pair()
        self.assertEqual(d.pair_independence(a,b,r)['status'],'VERIFIED_INDEPENDENT')
        for family in d.FAMILIES:
            with self.subTest(family=family):
                partial=deepcopy(r);partial['dimensions'][family]['snapshot_contract_digests']=['0'*64]
                self.assertEqual(d.pair_independence(a,b,partial)['status'],'PARTIALLY_INDEPENDENT')

    def test_one_unit_never_independent(self):
        a,_,_=synthetic_pair()
        self.assertEqual(d.calibrate_units([a],[])['status'],'NOT_INDEPENDENT')
        self.assertEqual(d.calibrate_units([a,a,a],[])['distinct_reference_unit_count'],1)

    def test_pairwise_source_family_links_cannot_hide_in_three_units(self):
        a,b,r=synthetic_pair();third=deepcopy(b);third.update(reference_id='SYNTHETIC-C',independent_evidence_unit_id='SYNTHETIC-PAGE-C',page_family='c.example.test/')
        result=d.calibrate_units([a,b,third],[r])
        self.assertEqual(len(result['pairs']),3)
        self.assertEqual(result['status'],'PARTIALLY_INDEPENDENT')

    def test_changed_scene_reference_or_pixel_hash_invalidates_trace(self):
        units=d.read('baseline_units.json');ms,ss=legacy.database();u=units[0]
        rb=d.read('corpus_readback.json');verified={(r['archive_id'],r['archive_member']):r['sha256'] for r in rb['members']}
        self.assertTrue(d.trace_valid(u,ss,verified))
        changed=deepcopy(ss);sid=u['mobile_scene_ids'][0];changed[sid]['reference_id']='OTHER_REFERENCE'
        self.assertFalse(d.trace_valid(u,changed,verified))
        changed=deepcopy(ss);changed[sid]['content_hash']='0'*64
        self.assertFalse(d.trace_valid(u,changed,verified))

    def test_forged_summary_cannot_unlock(self):
        original=d.read
        def bad(name):
            v=original(name)
            if name=='calibration.json':v[0]['new_eligibility']='ELIGIBLE'
            return v
        with patch.object(d,'read',bad), self.assertRaisesRegex(ValueError,'NOT_SOURCE_DERIVED'):
            d.ledger()

    def test_forged_baseline_source_cannot_unlock(self):
        original=d.read
        def bad(name):
            v=original(name)
            if name=='baseline_units.json':v[0]['source_contract_sha256']='0'*64
            return v
        with patch.object(d,'read',bad), self.assertRaisesRegex(ValueError,'BASELINE_EVIDENCE_TRACE_MISMATCH'):
            d.ledger()

    def test_real_all_13_holds_have_no_promotion(self):
        rs=d.ledger();self.assertEqual(len(rs),13)
        self.assertTrue(all(r['new_eligibility']=='HOLD' and r['independence']['status']=='NOT_INDEPENDENT' and r['promotion_count']==0 and r['phase2600_allowed'] is False for r in rs.values()))
        self.assertEqual(sum(r['adapter_status']=='HOLD' for r in rs.values()),3)
        self.assertTrue(all(r['eligibility_recalculated'] is False for r in rs.values()))

    def test_all_five_actual_production_routes_block_before_output(self):
        for profile in c.read('profiles.json')[:5]:
            with self.subTest(profile=profile['profile_id']), tempfile.TemporaryDirectory() as t:
                dest=Path(t)/'never-written'
                with self.assertRaisesRegex(ValueError,'INDEPENDENCE_INSUFFICIENT_LIVE_REJECT'):
                    run_generation(c.read('inputs/'+profile['profile_id']+'.json'),dest,mode='production')
                self.assertFalse(dest.exists())

    def test_unregistered_fixture_permission_is_not_research_admission(self):
        raw=c.read('inputs/local-trust.json');raw['mechanism_eligibility_context']['requested_motion']='ANIMATION'
        with tempfile.TemporaryDirectory() as t, self.assertRaisesRegex(ValueError,'MOTION_UNOBSERVED_REJECT'):
            run_generation(raw,t,mode='test')

    def test_required_capture_failure_never_becomes_durable_match(self):
        outcomes=d.read('targeted_outcomes.json')['records']
        self.assertEqual(len(outcomes),2)
        for r in outcomes:
            self.assertFalse(r['accept_as_independent_evidence'])
            self.assertEqual(r['required_desktop_1440'],'FAIL_CAPTURE')
            self.assertEqual(r['required_mobile_390'],'FAIL_CAPTURE')
            self.assertFalse(r['desktop_scene_ids'] or r['mobile_scene_ids'])

    def test_prior_evidence_bytes_preserved(self):
        import hashlib
        for name,sha in d.read('phase_b_c_preservation.json').items():
            self.assertEqual(hashlib.sha256((legacy.ROOT/name).read_bytes()).hexdigest(),sha,name)

    def test_missing_calibration_fails_closed(self):
        original=d.read
        def missing(name):
            if name=='calibration.json':raise FileNotFoundError('Injected missing ledger')
            return original(name)
        with patch.object(d,'read',missing),self.assertRaises(FileNotFoundError):
            d.require_live_independence(next(iter(c.contracts())))

    def test_match_cannot_be_a_score_or_an_independence_assertion(self):
        v=d.read('candidate_reviews.json')[0];v['independence_status']='VERIFIED_INDEPENDENT';v['accept_as_independent_evidence']=True
        self.assertNotEqual(replay({'kind':'MATCH','candidate':v})['status'],'MATCH')

    def test_independent_validator_rejects_missing_discovery_pixel(self):
        from validate_phase2_2_1d import validate
        original=Path.read_bytes
        def missing(p):
            if 'phase2_2_1d/discovery_failures/' in str(p):raise FileNotFoundError('Injected missing discovery rejection image')
            return original(p)
        with patch.object(Path,'read_bytes',missing),self.assertRaises(FileNotFoundError):validate()

    def test_independent_validator_rejects_corrupt_discovery_archive(self):
        from validate_phase2_2_1d import validate
        original=Path.read_bytes
        def corrupt(p):
            if p.name=='discovery_failure_archive.zip':return b'Injected corrupted ZIP bytes'
            return original(p)
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'DISCOVERY_ARCHIVE_CHANGED'):validate()

if __name__=='__main__':unittest.main()
