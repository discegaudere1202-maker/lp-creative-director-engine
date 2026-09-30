"""Bounded research evidence gate, independent of maturity and client publication.

Family relations require evidence bound to the compared snapshots. Different
domain/brand labels and a collection count are never a proof of independence.
Phase D is a conservative overlay: the approved C author-owned fixture path
and all its truth/rights/compatibility constraints stay in force.
"""
from copy import deepcopy
import json
from pathlib import Path
from itertools import combinations
from urllib.parse import urlsplit
from . import mechanism_runtime as legacy
from . import evidence_snapshot_binding as binding

DATA = legacy.ROOT / 'data/phase2_2_1d'
FIX_DATA = binding.FIX_DATA
AXES = ('composition', 'hierarchy', 'typography', 'media_role', 'spatial_behavior',
        'responsive_behavior', 'implementation_boundary', 'scene_job')
FAMILIES = ('brand_family', 'campaign_family', 'agency', 'production_company',
            'source_family', 'template_family')
DERIVATIVE_SOURCES = ('GALLERY_DUPLICATE', 'ARCHIVE_MIRROR', 'LOCALIZATION_ONLY')

def read(name):
    return json.loads((DATA / name).read_text())

def fix_read(name):
    return json.loads((FIX_DATA / name).read_text())

def evidence_sources(units=None, readback=None):
    if units is None:
        units = read('baseline_units.json') + read('candidate_reviews.json')
    return binding.load_sources(units, readback or read('corpus_readback.json'),
                                fix_read('attribution_evidence.json'))

def trace_valid(unit, scenes, verified_members):
    """Both viewports must trace to hashed, verified scenes of THIS reference."""
    for label, key in [('DESKTOP', 'desktop_scene_ids'), ('MOBILE', 'mobile_scene_ids')]:
        ids = unit.get(key)
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            return False
        for sid in ids:
            s = scenes.get(sid)
            if (not s or s.get('scene_evidence_id') != sid or
                s.get('reference_id') != unit.get('reference_id') or s.get('viewport_label') != label):
                return False
            if s.get('observation_state') != 'OBSERVED' or s.get('archive_status') != 'DURABLE_VERIFIED':
                return False
            if (not binding.sha256_value(s.get('content_hash')) or not s.get('archive_entry') or
                verified_members.get((s.get('archive_id'), s.get('archive_entry'))) != s['content_hash']):
                return False
    return True

def match_decision(candidate, mechanism, scenes, verified_members):
    if candidate.get('source_contract_sha256') != legacy.digest(mechanism):
        return 'REJECT', 'MECHANISM_CONTRACT_TRACE_MISMATCH'
    if not trace_valid(candidate, scenes, verified_members):
        return 'REJECT', 'EVIDENCE_TRACE_MISSING'
    axes = candidate.get('mechanism_match_basis', {})
    if set(axes) != set(AXES) or any(not axes[a].get('observation') for a in AXES):
        return 'HOLD', 'ATOMIC_MATCH_UNRESOLVED'
    if any(axes[a].get('status') == 'MISMATCH' for a in AXES):
        return 'REJECT', 'ATOMIC_CORE_MISMATCH'
    # MATCH refers to the atomic kernel, not identical styling. Partial/unknown
    # critical observations require explicit further evidence, never a score.
    if any(axes[a].get('status') != 'MATCH' for a in AXES):
        return 'HOLD', 'ATOMIC_MATCH_UNRESOLVED'
    if mechanism['scene_job'] == 'UNCLASSIFIED':
        return 'HOLD', 'SOURCE_SCENE_JOB_UNCLASSIFIED'
    return 'MATCH', None

def pair_independence(left, right, relation=None, *, sources=None):
    """A relation is a reviewed attribution assertion, not a URL heuristic."""
    if left.get('reference_id') == right.get('reference_id') or left.get('independent_evidence_unit_id') == right.get('independent_evidence_unit_id'):
        return {'status':'NOT_INDEPENDENT', 'reason':'SAME_REFERENCE_OR_VIEWPORT_DUPLICATE', 'dimensions':{}}
    if left.get('page_family') == right.get('page_family'):
        return {'status':'NOT_INDEPENDENT', 'reason':'SAME_PAGE_OR_MIRROR_FAMILY', 'dimensions':{}}
    if any(unit.get('discovery_source') in DERIVATIVE_SOURCES for unit in (left, right)):
        return {'status':'NOT_INDEPENDENT', 'reason':'DERIVATIVE_DISCOVERY_SOURCE', 'dimensions':{}}
    relation = relation if isinstance(relation, dict) else {}
    expected = sorted([left['independent_evidence_unit_id'], right['independent_evidence_unit_id']])
    subject_ids = relation.get('unit_ids', [])
    if (not isinstance(subject_ids, list) or len(subject_ids) != 2 or
        not all(isinstance(identity, str) for identity in subject_ids) or sorted(subject_ids) != expected):
        relation = {}
    # A contract digest is shared by same-mechanism references. Attribution
    # subjects are instead re-derived from the registered unit/capture tables.
    # Legacy assertions are never stamped with new subject digests here.
    sources = sources if sources is not None else evidence_sources()
    canonical_units = []
    for unit in (left, right):
        try:
            canonical_units.append(sources.units.get(binding.source_record_id(unit), {}))
        except (ValueError, TypeError):
            canonical_units.append({})
    if any(unit.get('discovery_source') in DERIVATIVE_SOURCES for unit in canonical_units):
        return {'status':'NOT_INDEPENDENT', 'reason':'DERIVATIVE_DISCOVERY_SOURCE', 'dimensions':{}}
    try:
        snapshots = [binding.evidence_snapshot(u, sources) for u in (left, right)]
        bindings = {s['unit_id']: s['evidence_snapshot_sha256'] for s in snapshots}
    except (ValueError, KeyError, TypeError):
        bindings = None
    dimensions = {}
    for family in FAMILIES:
        claims = relation.get('dimensions', {})
        claim = claims.get(family, {}) if isinstance(claims, dict) else {}
        if not isinstance(claim, dict):
            claim = {}
        state = claim.get('status', 'UNKNOWN')
        # A known shared family already establishes dependence without a
        # negative-independence claim. Parent/source aliases must be resolved
        # to reviewed family IDs, never display names or inferred domains.
        # Canonical known dependencies cannot disappear because a caller
        # omits/changes its copy of family metadata. Caller-shared assertions
        # remain conservative denials too; neither path grants independence.
        a = set(left.get('verified_family_ids', {}).get(family, []))
        a.update(canonical_units[0].get('verified_family_ids', {}).get(family, []))
        b = set(right.get('verified_family_ids', {}).get(family, []))
        b.update(canonical_units[1].get('verified_family_ids', {}).get(family, []))
        if a.intersection(b):
            dimensions[family] = 'NOT_INDEPENDENT'
            continue
        if (state not in ('VERIFIED_INDEPENDENT', 'NOT_INDEPENDENT') or
            bindings is None or not binding.assertion_bound(claim, family, bindings, sources)):
            state = 'UNKNOWN'
        dimensions[family] = state
    if 'NOT_INDEPENDENT' in dimensions.values():
        state, reason = 'NOT_INDEPENDENT', 'SHARED_PRODUCTION_OR_BRAND_CAMPAIGN_TEMPLATE_FAMILY'
    elif all(v == 'VERIFIED_INDEPENDENT' for v in dimensions.values()):
        state, reason = 'VERIFIED_INDEPENDENT', 'ALL_FAMILY_RELATIONS_BOUND_TO_SNAPSHOT_EVIDENCE'
    elif 'VERIFIED_INDEPENDENT' in dimensions.values():
        state, reason = 'PARTIALLY_INDEPENDENT', 'UNRESOLVED_FAMILY_RELATION_REMAINS'
    else:
        state, reason = 'UNKNOWN', 'ATTRIBUTION_OR_CAMPAIGN_SNAPSHOT_BINDING_UNKNOWN'
    return {'status':state, 'reason':reason, 'dimensions':dimensions}

def calibrate_units(units, relations, *, sources=None):
    if not units:
        return {'status':'UNKNOWN', 'distinct_reference_unit_count':0, 'pairs':[], 'reason':'NO_TRACEABLE_UNIT'}
    unique = {}
    ambiguous = False
    for unit in units:
        identity = unit['independent_evidence_unit_id']
        if identity in unique and legacy.digest(unique[identity]) != legacy.digest(unit):
            ambiguous = True
        unique[identity] = unit
    if ambiguous:
        return {'status':'UNKNOWN', 'distinct_reference_unit_count':len(unique),
                'pairs':[], 'reason':'AMBIGUOUS_UNIT_SNAPSHOT_RECORD'}
    pairs = []
    for left, right in combinations((unique[key] for key in sorted(unique)), 2):
        key = sorted([left['independent_evidence_unit_id'],right['independent_evidence_unit_id']])
        # Multiple reviews for the same subjects are ambiguous; do not choose
        # an arbitrary first relation that might hide a stale/conflicting one.
        relations_for_pair = [r for r in relations if sorted(r.get('unit_ids',[])) == key]
        relation = relations_for_pair[0] if len(relations_for_pair) == 1 else None
        pairs.append({'unit_ids':key, **pair_independence(left,right,relation,sources=sources)})
    if len(unique) == 1:
        status = 'NOT_INDEPENDENT'
    elif all(p['status']=='NOT_INDEPENDENT' for p in pairs):
        status = 'NOT_INDEPENDENT'
    elif all(p['status']=='VERIFIED_INDEPENDENT' for p in pairs):
        status = 'VERIFIED_INDEPENDENT'
    elif any(p['status'] in ('VERIFIED_INDEPENDENT','PARTIALLY_INDEPENDENT') for p in pairs):
        status = 'PARTIALLY_INDEPENDENT'
    else:
        status = 'UNKNOWN'
    return {'status':status,'distinct_reference_unit_count':len(unique),'pairs':pairs,
            'reason':'ONE_APPROVED_REFERENCE_ONLY' if len(unique)==1 else 'PAIRWISE_FAMILY_EVIDENCE_REQUIRED_NO_COUNT_THRESHOLD'}

def derive():
    from . import production_eligibility as gate
    mechanisms, _ = legacy.database()
    rb = read('corpus_readback.json')
    if rb.get('source_commit') != 'b3d4607277c3e13a24505e70b94bf3ec03b67362' or rb.get('phase2600_allowed') is not False:
        raise ValueError('CALIBRATION_CORPUS_TRACE_MISMATCH')
    verified = {(r['archive_id'],r['archive_member']):r['sha256'] for r in rb['members'] if r['result']=='PASS'}
    baseline = read('baseline_units.json'); candidates = read('candidate_reviews.json')
    sources = evidence_sources(baseline + candidates, rb)
    scenes = sources.scenes
    if {u['mechanism_id'] for u in baseline} != set(mechanisms) or len(baseline)!=13:
        raise ValueError('CALIBRATION_BASELINE_COVERAGE_MISMATCH')
    if len({c['candidate_id'] for c in candidates})!=len(candidates):
        raise ValueError('CALIBRATION_CANDIDATE_DUPLICATE')
    # Historical records remain immutable. Only separately stored, explicitly
    # reviewed V1 assertions can establish a new snapshot-bound relation.
    relations = read('family_relations.json') + fix_read('family_assertions.json')
    base_contracts = {c['mechanism_id']:c for c in gate.derive_contracts()}
    result=[]
    for mid,m in mechanisms.items():
        base=[u for u in baseline if u['mechanism_id']==mid]
        source_ids=sorted({e['scene_evidence_id'] for e in m['source_evidence']})
        if (len(base)!=1 or not trace_valid(base[0],scenes,verified) or
            base[0]['source_contract_sha256']!=legacy.digest(m) or
            sorted(base[0]['desktop_scene_ids']+base[0]['mobile_scene_ids'])!=source_ids):
            raise ValueError('CALIBRATION_BASELINE_EVIDENCE_TRACE_MISMATCH')
        decisions=[]; matched=[]
        for c in candidates:
            if c['mechanism_id']==mid:
                state, reason = match_decision(c,m,scenes,verified)
                decisions.append({'candidate_id':c['candidate_id'],'reference_id':c['reference_id'],'match_decision':state,
                                  'reason':reason,'candidate_digest':legacy.digest(c),'independence_status':'UNKNOWN'})
                if state=='MATCH':matched.append(c)
        snapshots = [binding.evidence_snapshot(u, sources) for u in base + matched]
        independence=calibrate_units(base+matched,relations,sources=sources)
        # No new matching evidence is presently admitted. Recalculation is
        # explicit only for new matched evidence; copied C contract fields are
        # not silently promoted. Any future unlock also needs reviewed adapter
        # bounds and all per-output C gates, and is not inferred here.
        c=deepcopy(base_contracts[mid])
        reasons=['NO_NEW_VALIDATED_ATOMIC_MATCH_AND_INDEPENDENT_UNIT']
        if independence['status']!='VERIFIED_INDEPENDENT':reasons.append('INDEPENDENCE_INSUFFICIENT')
        if c['adapter_status']=='HOLD':reasons.append('ADAPTER_HOLD')
        reasons.append('CLIENT_TRUTH_RIGHTS_AND_CURRENT_OUTPUT_QA_STILL_REQUIRED')
        result.append({'mechanism_id':mid,'snapshot_binding_schema':binding.SCHEMA,
            'evidence_snapshot_bindings':snapshots,
            'existing_evidence_unit_count':1,'candidate_decisions':decisions,
            'new_matching_reference_count':len(matched),'accepted_new_independent_evidence_count':0,
            'independence':independence,'agency_independence':'UNKNOWN','campaign_independence':'UNKNOWN',
            'source_family_independence':independence['status'],'adapter_status':c['adapter_status'],
            'previous_eligibility':c['production_eligibility'],'new_eligibility':'HOLD',
            'eligibility_recalculated':bool(matched),'eligibility_change_reason':reasons,
            'production_revalidation':'NOT_APPLICABLE_ELIGIBILITY_UNCHANGED','desktop_result':'NOT_RERUN_UNCHANGED',
            'mobile_result':'NOT_RERUN_UNCHANGED','motion_support':'STATIC_ONLY','promotion_count':0,'phase2600_allowed':False})
    return result

def ledger():
    expected=derive()
    if fix_read('calibration.json')!=expected:
        raise ValueError('INDEPENDENCE_CALIBRATION_NOT_SOURCE_DERIVED')
    return {r['mechanism_id']:r for r in expected}

def require_live_independence(mechanism_id):
    record=ledger().get(mechanism_id)
    if not record or record['independence']['status']!='VERIFIED_INDEPENDENT':
        raise ValueError('INDEPENDENCE_INSUFFICIENT_LIVE_REJECT:PHASE_D_CALIBRATION')
    if record['new_eligibility'] not in ('ELIGIBLE','CONDITIONAL'):
        raise ValueError('PRODUCTION_ELIGIBILITY_HOLD:PHASE_D_CALIBRATION')
