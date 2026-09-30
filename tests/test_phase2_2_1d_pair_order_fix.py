"""Declared synthetic pair/set permutation properties; no research evidence."""
from copy import deepcopy
from itertools import combinations, permutations, product
import sys
import unittest
from lp_engine import independence_calibration as d
from lp_engine import evidence_snapshot_binding as b
from lp_engine import mechanism_runtime as legacy
sys.path.insert(0, str(legacy.ROOT / 'scripts'))
from snapshot_binding_fix_fixtures import snapshot_pair, replace_capture, reviewed_relation

LABELS = ('GALLERY_DUPLICATE', 'ARCHIVE_MIRROR', 'LOCALIZATION_ONLY')
MODES = ('matched', 'canonical_caller_omitted', 'canonical_caller_contradictory',
         'caller_only', 'canonical_caller_other_derivative')


def relation_for_registered(left, right, sources):
    return reviewed_relation(*(sources.units[b.source_record_id(u)] for u in (left, right)), sources)


def derivative_context(label, subject, mode):
    a, z, relation, sources = snapshot_pair()
    units = [a, z]
    unit = units[subject]
    if mode != 'caller_only':
        sources.units[b.source_record_id(unit)]['discovery_source'] = label
        relation = relation_for_registered(a, z, sources)
    if mode in ('matched', 'caller_only'):
        unit['discovery_source'] = label
    elif mode == 'canonical_caller_omitted':
        unit.pop('discovery_source')
    elif mode == 'canonical_caller_other_derivative':
        unit['discovery_source'] = LABELS[(LABELS.index(label) + 1) % len(LABELS)]
    # Contradictory caller keeps the original non-derivative value.
    return units, relation, sources


def reviewed_three():
    a, z, _, sources = snapshot_pair()
    third = deepcopy(z)
    third.update(unit_id='SYNTHETIC-SOURCE-C', reference_id='SYNTHETIC-C',
                 independent_evidence_unit_id='SYNTHETIC-PAGE-C',
                 official_url='https://c.example.test/', page_family='c.example.test/')
    sources.references[third['reference_id']] = {
        'reference_id': third['reference_id'], 'canonical_url': third['official_url'],
        'active_in_recovered_corpus': 'true'}
    for label in ('DESKTOP', 'MOBILE'):
        replace_capture(third, sources, label, 1)
    units = [a, z, third]
    relations = []
    # Give each pair's cited source its own identity. Generic fixture IDs must
    # not overwrite the citation of a previously reviewed pair.
    for left, right in combinations(units, 2):
        relation = reviewed_relation(left, right, sources)
        suffix = '-'.join(relation['unit_ids'])
        for claim in relation['dimensions'].values():
            old_id = next(iter(claim['attribution_evidence_digests']))
            evidence = sources.attribution_evidence.pop(old_id)
            new_id = old_id + '-' + suffix
            evidence['attribution_evidence_id'] = new_id
            sources.attribution_evidence[new_id] = evidence
            claim['attribution_evidence_digests'] = {new_id: legacy.digest(evidence)}
        relations.append(relation)
    return units, relations, sources


class PairOrderFixTest(unittest.TestCase):
    def setUp(self):
        self.order_checks = []

    def pair(self, left, right, relation, sources):
        actual = d.pair_independence(left, right, relation, sources=sources)
        self.order_checks.append({'kind': 'PAIR', 'unit_order': [u['independent_evidence_unit_id'] for u in (left, right)],
                                  'status': actual['status'], 'reason': actual['reason']})
        return actual

    def calibrate(self, units, relations, sources):
        actual = d.calibrate_units(units, relations, sources=sources)
        self.order_checks.append({'kind': 'SET', 'unit_order': [u['independent_evidence_unit_id'] for u in units],
                                  'status': actual['status'], 'reason': actual['reason'],
                                  'distinct_unit_count': actual['distinct_reference_unit_count'],
                                  'pair_count': len(actual['pairs'])})
        return actual

    def assert_both_orders(self, units, relations, sources, expected):
        relation = relations[0] if len(relations) == 1 else None
        forward = self.pair(*units, relation, sources)
        reverse = self.pair(*reversed(units), relation, sources)
        self.assertEqual(forward, reverse)
        self.assertEqual(forward['status'], expected)
        first = self.calibrate(units, relations, sources)
        second = self.calibrate(list(reversed(units)), relations, sources)
        self.assertEqual(first, second)
        self.assertEqual(first['status'], expected)

    def test_reviewed_same_mechanism_distinct_reference_positive_both_orders(self):
        a, z, relation, sources = snapshot_pair()
        self.assertEqual(a['source_contract_sha256'], z['source_contract_sha256'])
        self.assert_both_orders([a, z], [relation], sources, 'VERIFIED_INDEPENDENT')

    def test_three_reviewed_units_all_six_permutations_identical(self):
        units, relations, sources = reviewed_three()
        results = [self.calibrate(list(order), relations, sources) for order in permutations(units)]
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(results[0]['status'], 'VERIFIED_INDEPENDENT')
        self.assertEqual(len(results[0]['pairs']), 3)

    def test_conflicting_duplicate_unit_records_all_24_permutations_identical(self):
        units, relations, sources = reviewed_three()
        changed = deepcopy(units[1]); changed['mobile_scene_ids'] = ['OTHER']
        results = [self.calibrate(list(order), relations, sources) for order in permutations(units + [changed])]
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(results[0]['status'], 'UNKNOWN')
        self.assertEqual(results[0]['distinct_reference_unit_count'], 3)

    def test_identical_duplicate_unit_records_all_six_permutations_identical(self):
        a, z, relation, sources = snapshot_pair()
        results = [self.calibrate(list(order), [relation], sources) for order in permutations([a, z, deepcopy(z)])]
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(results[0]['status'], 'VERIFIED_INDEPENDENT')
        self.assertEqual(results[0]['distinct_reference_unit_count'], 2)

    def test_ambiguous_relation_and_unit_orders_do_not_choose_positive_claim(self):
        a, z, relation, sources = snapshot_pair()
        conflicting = deepcopy(relation); conflicting['dimensions'].clear()
        results = [self.calibrate(list(units), list(relations), sources)
                   for units in permutations([a, z]) for relations in permutations([relation, conflicting])]
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(results[0]['status'], 'UNKNOWN')


def derivative_test(label, subject, mode, reverse, kind):
    def test(self):
        units, relation, sources = derivative_context(label, subject, mode)
        for unit in units:
            self.assertTrue(d.trace_valid(unit, sources.scenes, sources.verified_members))
            self.assertEqual(d.match_decision(unit, {'mechanism_id': 'SYNTHETIC-MECHANISM', 'scene_job': 'ENTRY'},
                                               sources.scenes, sources.verified_members), ('MATCH', None))
        if reverse: units.reverse()
        result = (self.pair(*units, relation, sources) if kind == 'PAIR'
                  else self.calibrate(units, [relation], sources))
        self.assertEqual(result['status'], 'NOT_INDEPENDENT')
        pair = result if kind == 'PAIR' else result['pairs'][0]
        self.assertEqual(pair['reason'], 'DERIVATIVE_DISCOVERY_SOURCE')
    test.order_parameters = {'kind': kind, 'derivative': label, 'subject_index': subject,
                             'caller_mode': mode, 'reverse': reverse}
    return test


for label, subject, mode, reverse, kind in product(LABELS, range(2), MODES, (False, True), ('PAIR', 'SET')):
    name = 'test_derivative_' + '_'.join((kind.lower(), label.lower(), str(subject), mode, 'reverse' if reverse else 'forward'))
    setattr(PairOrderFixTest, name, derivative_test(label, subject, mode, reverse, kind))


def shared_test(family, canonical_only):
    def test(self):
        a, z, relation, sources = snapshot_pair()
        for unit in (a, z):
            target = sources.units[b.source_record_id(unit)] if canonical_only else unit
            target['verified_family_ids'] = {family: ['SYNTHETIC-SHARED']}
        self.assert_both_orders([a, z], [relation], sources, 'NOT_INDEPENDENT')
    return test


for family, canonical_only in product(d.FAMILIES, (False, True)):
    setattr(PairOrderFixTest, 'test_shared_' + family + ('_canonical' if canonical_only else '_caller'), shared_test(family, canonical_only))


def duplicate_test(field):
    def test(self):
        a, z, relation, sources = snapshot_pair()
        if field == 'independent_evidence_unit_id':
            z = deepcopy(a)
        else:
            z[field] = a[field]
        self.assert_both_orders([a, z], [relation], sources, 'NOT_INDEPENDENT')
    return test


for field in ('reference_id', 'page_family', 'independent_evidence_unit_id'):
    setattr(PairOrderFixTest, 'test_duplicate_' + field + '_both_orders', duplicate_test(field))


def stale_test(mutation, subject):
    def test(self):
        a, z, relation, sources = snapshot_pair()
        unit = (a, z)[subject]
        if mutation in ('scene', 'pixels'):
            for label in ('DESKTOP', 'MOBILE'):
                replace_capture(unit, sources, label, 2, keep_scene_id=mutation == 'pixels')
        elif mutation == 'capture_metadata':
            sources.scenes[unit['mobile_scene_ids'][0]]['captured_at'] = '2000-04-01T00:00:00+00:00'
        elif mutation == 'old_readback_hash':
            sources.scenes[unit['mobile_scene_ids'][0]]['content_hash'] = '0' * 64
        elif mutation == 'swapped_snapshot':
            for claim in relation['dimensions'].values():
                mapping = claim['snapshot_bindings']
                claim['snapshot_bindings'] = dict(zip(mapping, reversed(list(mapping.values()))))
        elif mutation == 'citation':
            for evidence in sources.attribution_evidence.values(): evidence['observation'] = 'Changed source statement'
        elif mutation == 'missing_mobile':
            unit['mobile_scene_ids'] = []; sources.units[b.source_record_id(unit)] = deepcopy(unit)
        elif mutation == 'partial_family':
            relation['dimensions'].pop('agency')
        elif mutation == 'unreviewed':
            for claim in relation['dimensions'].values(): claim['review'].clear()
        self.assert_both_orders([a, z], [relation], sources, 'PARTIALLY_INDEPENDENT' if mutation == 'partial_family' else 'UNKNOWN')
    return test


for mutation, subject in product(('scene', 'pixels', 'capture_metadata', 'old_readback_hash', 'swapped_snapshot', 'citation', 'missing_mobile', 'partial_family', 'unreviewed'), range(2)):
    setattr(PairOrderFixTest, 'test_stale_' + mutation + '_' + str(subject) + '_both_orders', stale_test(mutation, subject))


def mixed_set_test(label, canonical_only):
    def test(self):
        units, relations, sources = reviewed_three()
        sources.units[b.source_record_id(units[2])]['discovery_source'] = label
        if not canonical_only: units[2]['discovery_source'] = label
        else: units[2].pop('discovery_source')
        results = [self.calibrate(list(order), relations, sources) for order in permutations(units)]
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(results[0]['status'], 'PARTIALLY_INDEPENDENT')
        self.assertEqual(sorted(p['status'] for p in results[0]['pairs']), ['NOT_INDEPENDENT', 'NOT_INDEPENDENT', 'VERIFIED_INDEPENDENT'])
    return test


for label, canonical_only in product(LABELS, (False, True)):
    setattr(PairOrderFixTest, 'test_mixed_set_' + label.lower() + ('_canonical_only' if canonical_only else '_matched'), mixed_set_test(label, canonical_only))


if __name__ == '__main__': unittest.main()
