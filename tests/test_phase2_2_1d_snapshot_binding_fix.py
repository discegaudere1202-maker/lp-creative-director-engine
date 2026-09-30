"""Snapshot subjects, immutable reviews, re-derivation and production admission."""
from copy import deepcopy
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from lp_engine import independence_calibration as d
from lp_engine import evidence_snapshot_binding as b
from lp_engine import mechanism_runtime as legacy
from lp_engine import production_eligibility as c
from lp_engine.production_generation import run_generation
sys.path.insert(0,str(legacy.ROOT/'scripts'))
from snapshot_binding_fix_fixtures import snapshot_pair, replace_capture, reviewed_relation


class SnapshotBindingFixTest(unittest.TestCase):
    def setUp(self):
        self.a,self.z,self.relation,self.sources = snapshot_pair()
        self.mechanism = {'mechanism_id':'SYNTHETIC-MECHANISM','scene_job':'ENTRY'}

    def verdict(self):
        return d.pair_independence(self.a,self.z,self.relation,sources=self.sources)

    def assert_current_match(self):
        self.assertTrue(d.trace_valid(self.z,self.sources.scenes,self.sources.verified_members))
        self.assertEqual(d.match_decision(self.z,self.mechanism,self.sources.scenes,self.sources.verified_members),('MATCH',None))

    def test_same_mechanism_distinct_references_reviewed_control(self):
        self.assertEqual(self.a['source_contract_sha256'],self.z['source_contract_sha256'])
        self.assertNotEqual(b.evidence_snapshot(self.a,self.sources)['evidence_snapshot_sha256'],b.evidence_snapshot(self.z,self.sources)['evidence_snapshot_sha256'])
        self.assertEqual(self.verdict()['status'],'VERIFIED_INDEPENDENT')
        self.assert_current_match()

    def test_pm_reproduction_changed_pc_mobile_scene_selection(self):
        for label in ('DESKTOP','MOBILE'):replace_capture(self.z,self.sources,label,2)
        self.assert_current_match()
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_pm_reproduction_same_scene_ids_changed_registered_pixel_hash(self):
        ids=deepcopy((self.z['desktop_scene_ids'],self.z['mobile_scene_ids']))
        for label in ('DESKTOP','MOBILE'):replace_capture(self.z,self.sources,label,2,keep_scene_id=True)
        self.assertEqual(ids,(self.z['desktop_scene_ids'],self.z['mobile_scene_ids']))
        self.assert_current_match()
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_explicit_new_review_required_after_new_snapshot(self):
        replace_capture(self.z,self.sources,'MOBILE',2)
        self.assertEqual(self.verdict()['status'],'UNKNOWN')
        # Explicit reviewer fixture action updates the cited evidence AND claim.
        self.relation=reviewed_relation(self.a,self.z,self.sources)
        self.assertEqual(self.verdict()['status'],'VERIFIED_INDEPENDENT')

    def test_legacy_contract_digest_assertions_are_not_migrated(self):
        from exercise_phase2_2_1d_rejections import synthetic_pair
        _,_,old=synthetic_pair();old['unit_ids']=self.relation['unit_ids']
        for claim in old['dimensions'].values():claim['snapshot_contract_digests']=[self.a['source_contract_sha256']]*2
        self.relation=old
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_unit_digest_supplied_by_caller_is_ignored(self):
        replace_capture(self.z,self.sources,'MOBILE',2)
        self.z['evidence_snapshot_sha256']=next(iter(self.relation['dimensions'].values()))['snapshot_bindings'][self.z['independent_evidence_unit_id']]
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_unit_to_snapshot_mapping_swapped(self):
        for claim in self.relation['dimensions'].values():
            keys=list(claim['snapshot_bindings']);values=list(claim['snapshot_bindings'].values())
            claim['snapshot_bindings']=dict(zip(keys,reversed(values)))
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_missing_mobile_subject_mapping(self):
        self.z['mobile_scene_ids']=[];self.sources.units[b.source_record_id(self.z)]=deepcopy(self.z)
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_missing_mobile_source_scene(self):
        del self.sources.scenes[self.z['mobile_scene_ids'][0]]
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_old_image_hash_readback_no_longer_matches_scene(self):
        self.sources.scenes[self.z['mobile_scene_ids'][0]]['content_hash']='0'*64
        self.assertFalse(d.trace_valid(self.z,self.sources.scenes,self.sources.verified_members))
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_capture_metadata_change_without_pixel_change_invalidates_review(self):
        sid=self.z['mobile_scene_ids'][0]
        self.sources.scenes[sid]['captured_at']='2000-03-01T00:00:00+00:00'
        self.assert_current_match()
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_archive_locator_change_invalidates_review(self):
        self.sources.archives['SYNTHETIC-ARCHIVE']['archive_locator']='https://evidence.example.test/new-archive-version'
        for record in list(self.sources.scenes.values())+self.sources.snapshots:record['archive_locator']=self.sources.archives['SYNTHETIC-ARCHIVE']['archive_locator']
        self.assert_current_match()
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_parent_snapshot_identity_change_invalidates_review(self):
        sid=self.z['mobile_scene_ids'][0];scene=self.sources.scenes[sid]
        parent=next(s for s in self.sources.snapshots if s.get('snapshot_id')==scene['parent_snapshot_id'])
        parent['snapshot_id']='SYNTHETIC-NEW-PARENT'
        scene['snapshot_id']=scene['parent_snapshot_id']=parent['snapshot_id']
        self.assert_current_match()
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_reference_page_identity_change_invalidates_review(self):
        self.sources.references[self.z['reference_id']]['canonical_url']='https://other.example.test/'
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_unregistered_unit_source_record_rejected(self):
        self.z['unit_id']='OTHER_SOURCE'
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_caller_scene_selection_not_in_canonical_unit_rejected(self):
        self.z['mobile_scene_ids']=self.a['mobile_scene_ids']
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_citation_missing_from_source_registry(self):
        self.sources.attribution_evidence.clear()
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_citation_subject_mapping_wrong_even_with_current_citation_digest(self):
        for evidence in self.sources.attribution_evidence.values():
            evidence['snapshot_bindings']={self.a['independent_evidence_unit_id']:'0'*64,self.z['independent_evidence_unit_id']:'1'*64}
        for claim in self.relation['dimensions'].values():
            claim['attribution_evidence_digests']={key:legacy.digest(self.sources.attribution_evidence[key]) for key in claim['attribution_evidence_digests']}
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_changed_cited_source_record_invalidates_old_review_digest(self):
        for evidence in self.sources.attribution_evidence.values():evidence['observation']='Different synthetic source statement'
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_missing_explicit_reviewer_not_verified_by_flag(self):
        for claim in self.relation['dimensions'].values():claim['review'].clear();claim['snapshot_binding']='VERIFIED'
        self.assertEqual(self.verdict()['status'],'UNKNOWN')

    def test_missing_one_family_remains_unknown_dimension(self):
        del self.relation['dimensions']['agency']
        result=self.verdict();self.assertEqual(result['dimensions']['agency'],'UNKNOWN')
        self.assertEqual(result['status'],'PARTIALLY_INDEPENDENT')

    def test_order_of_pair_does_not_change_unit_mapping(self):
        self.assertEqual(d.pair_independence(self.z,self.a,self.relation,sources=self.sources)['status'],'VERIFIED_INDEPENDENT')

    def test_contract_digest_is_separate_from_snapshot_digest(self):
        before=b.evidence_snapshot(self.z,self.sources)['evidence_snapshot_sha256']
        self.z['source_contract_sha256']='0'*64;self.sources.units[b.source_record_id(self.z)]=deepcopy(self.z)
        self.assertEqual(before,b.evidence_snapshot(self.z,self.sources)['evidence_snapshot_sha256'])
        self.assertEqual(d.match_decision(self.z,self.mechanism,self.sources.scenes,self.sources.verified_members)[0],'REJECT')

    def test_conflicting_unit_records_cannot_be_silently_deduplicated(self):
        changed=deepcopy(self.z);changed['mobile_scene_ids']=['OTHER']
        result=d.calibrate_units([self.a,self.z,changed],[self.relation],sources=self.sources)
        self.assertEqual(result['status'],'UNKNOWN')

    def test_ambiguous_assertions_not_arbitrarily_selected(self):
        result=d.calibrate_units([self.a,self.z],[self.relation,deepcopy(self.relation)],sources=self.sources)
        self.assertEqual(result['status'],'UNKNOWN')

    def test_duplicate_reference_and_viewport_derivatives_remain_dependent(self):
        self.assertEqual(d.pair_independence(self.a,deepcopy(self.a),self.relation,sources=self.sources)['status'],'NOT_INDEPENDENT')

    def test_gallery_and_mirror_derivatives_remain_dependent(self):
        for label in ('GALLERY_DUPLICATE','ARCHIVE_MIRROR','LOCALIZATION_ONLY'):
            self.z['discovery_source']=label
            self.assertEqual(self.verdict()['status'],'NOT_INDEPENDENT')

    def test_same_page_family_remains_dependent(self):
        self.z['page_family']=self.a['page_family']
        self.assertEqual(self.verdict()['status'],'NOT_INDEPENDENT')

    def test_real_source_bindings_are_rederived_and_holds_preserved(self):
        sources=d.evidence_sources();records=list(sources.units.values())
        self.assertEqual(len(records),39)
        for unit in records:self.assertEqual(b.evidence_snapshot(unit,sources),b.evidence_snapshot(deepcopy(unit),sources))
        self.assertTrue(all(r['new_eligibility']=='HOLD' and r['phase2600_allowed'] is False for r in d.ledger().values()))

    def integration_fixture(self):
        # Real canonical record structure, synthetic all-MATCH/review additions
        # in memory only. No saved candidate judgement or source is changed.
        original_read=d.read;original_fix=d.fix_read
        base=original_read('baseline_units.json');candidates=original_read('candidate_reviews.json')
        candidate=candidates[0];mid=candidate['mechanism_id'];left=next(u for u in base if u['mechanism_id']==mid)
        candidate['mechanism_match_basis']={axis:{'status':'MATCH','observation':'Explicit synthetic integration override only'} for axis in d.AXES}
        sources=d.evidence_sources(base+candidates,original_read('corpus_readback.json'))
        relation=reviewed_relation(left,candidate,sources)
        cache={}
        def read(name):return deepcopy(candidates) if name=='candidate_reviews.json' else original_read(name)
        def fix_read(name):
            if name=='family_assertions.json':return deepcopy([relation])
            if name=='calibration.json':return deepcopy(cache['ledger'])
            return original_fix(name)
        return candidate,left,mid,sources,relation,cache,read,fix_read

    def test_ledger_rederive_and_production_gate_positive_provenance_still_hold(self):
        candidate,left,mid,sources,relation,cache,read,fix=self.integration_fixture()
        with patch.object(d,'read',read),patch.object(d,'fix_read',fix),patch.object(d,'evidence_sources',return_value=sources):
            cache['ledger']=d.derive();record=d.ledger()[mid]
            self.assertEqual(record['independence']['status'],'VERIFIED_INDEPENDENT')
            self.assertEqual(record['new_eligibility'],'HOLD')
            with self.assertRaisesRegex(ValueError,'PRODUCTION_ELIGIBILITY_HOLD:PHASE_D_CALIBRATION'):d.require_live_independence(mid)
            with tempfile.TemporaryDirectory() as directory:
                dest=Path(directory)/'never-created'
                with self.assertRaisesRegex(ValueError,'PRODUCTION_ELIGIBILITY_HOLD:PHASE_D_CALIBRATION'):
                    run_generation(c.read('inputs/local-trust.json'),dest,mode='production')
                self.assertFalse(dest.exists())

    def test_ledger_regeneration_does_not_reapprove_changed_capture_assertion(self):
        candidate,left,mid,sources,relation,cache,read,fix=self.integration_fixture()
        before=deepcopy(relation)
        scene=sources.scenes[candidate['mobile_scene_ids'][0]];scene['captured_at']='2000-04-01T00:00:00+00:00'
        with patch.object(d,'read',read),patch.object(d,'fix_read',fix),patch.object(d,'evidence_sources',return_value=sources):
            cache['ledger']=d.derive();self.assertEqual(d.ledger()[mid]['independence']['status'],'UNKNOWN')
            self.assertEqual(relation,before)
            with tempfile.TemporaryDirectory() as directory:
                dest=Path(directory)/'never-created'
                with self.assertRaisesRegex(ValueError,'INDEPENDENCE_INSUFFICIENT_LIVE_REJECT:PHASE_D_CALIBRATION'):
                    run_generation(c.read('inputs/local-trust.json'),dest,mode='production')
                self.assertFalse(dest.exists())

    def test_forged_v2_ledger_summary_rejected_by_production(self):
        original=d.fix_read
        mechanism_id=next(iter(d.ledger()))
        def forged(name):
            value=original(name)
            if name=='calibration.json':value[0]['new_eligibility']='ELIGIBLE';value[0]['independence']['status']='VERIFIED_INDEPENDENT'
            return value
        with patch.object(d,'fix_read',forged),self.assertRaisesRegex(ValueError,'NOT_SOURCE_DERIVED'):
            d.require_live_independence(mechanism_id)


def shared_family_test(family):
    def test(self):
        self.a['verified_family_ids']={family:['SYNTHETIC-SHARED']}
        self.z['verified_family_ids']={family:['SYNTHETIC-SHARED']}
        self.assertEqual(self.verdict()['status'],'NOT_INDEPENDENT')
    return test

for family in d.FAMILIES:
    setattr(SnapshotBindingFixTest,'test_shared_'+family+'_denial_preserved',shared_family_test(family))

if __name__=='__main__':unittest.main()
