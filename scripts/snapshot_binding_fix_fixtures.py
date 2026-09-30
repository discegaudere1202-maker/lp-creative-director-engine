"""Declared synthetic capture/review records; never research or live evidence."""
from copy import deepcopy
from lp_engine import evidence_snapshot_binding as b
from lp_engine import independence_calibration as d
from lp_engine import mechanism_runtime as legacy


def replace_capture(unit, sources, label, version, *, keep_scene_id=False):
    key = 'desktop_scene_ids' if label == 'DESKTOP' else 'mobile_scene_ids'
    scene_id = unit[key][0] if keep_scene_id else unit['reference_id'] + '-' + label + '-SCENE-V' + str(version)
    previous = sources.scenes.get(unit[key][0], {})
    snapshot_id = previous.get('parent_snapshot_id') if keep_scene_id else unit['reference_id'] + '-' + label + '-SNAPSHOT-V' + str(version)
    member = previous.get('archive_entry') if keep_scene_id else snapshot_id + '.synthetic'
    record = {'snapshot_id': snapshot_id, 'reference_id': unit['reference_id'],
              'viewport_label': label, 'viewport': {'width':1440 if label == 'DESKTOP' else 390,'height':900},
              'archive_id':'SYNTHETIC-ARCHIVE', 'archive_entry':member,
              'archive_locator':'https://evidence.example.test/synthetic-archive',
              'archive_status':'DURABLE_VERIFIED', 'content_hash':legacy.digest({'declared_synthetic_pixels':member,'version':version}),
              'container_sha256':sources.archives['SYNTHETIC-ARCHIVE']['container_sha256'],
              'screenshot_identifier':member, 'captured_at':'2000-01-%02dT00:00:00+00:00' % version,
              'original_url':unit['official_url'], 'final_url':unit['official_url']}
    sources.snapshots = [s for s in sources.snapshots if s.get('snapshot_id') != snapshot_id] + [record]
    sources.scenes[scene_id] = {**record, 'scene_evidence_id':scene_id, 'observation_state':'OBSERVED',
                               'parent_snapshot_id':snapshot_id, 'parent_content_hash':record['content_hash'],
                               'parent_screenshot_identifier':member, 'page_y_range':[0,900]}
    sources.verified_members[(record['archive_id'], member)] = record['content_hash']
    unit[key] = [scene_id]
    sources.units[b.source_record_id(unit)] = deepcopy(unit)


def reviewed_relation(left, right, sources):
    """Explicit *synthetic* reviewer action at current subjects, not migration."""
    subjects = {u['independent_evidence_unit_id']:b.evidence_snapshot(u,sources)['evidence_snapshot_sha256']
                for u in (left,right)}
    relation = {'unit_ids':sorted(subjects), 'dimensions':{}}
    for family in d.FAMILIES:
        identity = 'SYNTHETIC-ATTRIBUTION-' + family
        evidence = {'attribution_evidence_id':identity, 'family':family,
                    'snapshot_bindings':deepcopy(subjects), 'primary_source_url':'https://evidence.example.test/' + family,
                    'observation':'Declared synthetic source statement, no real-world attribution claim'}
        sources.attribution_evidence[identity] = evidence
        relation['dimensions'][family] = {
            'schema':b.ASSERTION_SCHEMA, 'assertion_id':'SYNTHETIC-REVIEW-' + family,
            'family':family, 'status':'VERIFIED_INDEPENDENT', 'snapshot_bindings':deepcopy(subjects),
            'basis':'Explicit synthetic review control only',
            'review':{'status':'REVIEWED','reviewer':'SYNTHETIC_TEST_REVIEWER','reviewed_at':'2000-02-01T00:00:00+00:00'},
            'attribution_evidence_digests':{identity:legacy.digest(evidence)}}
    return relation


def snapshot_pair():
    mechanism = {'mechanism_id':'SYNTHETIC-MECHANISM','scene_job':'ENTRY'}
    units = []
    for label in ('A','B'):
        unit = {'unit_id':'SYNTHETIC-SOURCE-' + label, 'reference_id':'SYNTHETIC-' + label,
                'mechanism_id':mechanism['mechanism_id'], 'page_family':label.lower()+'.example.test/',
                'official_url':'https://'+label.lower()+'.example.test/',
                'independent_evidence_unit_id':'SYNTHETIC-PAGE-' + label,
                'source_contract_sha256':legacy.digest(mechanism), 'discovery_source':'SYNTHETIC_TEST_ONLY',
                'desktop_scene_ids':['placeholder-desktop'], 'mobile_scene_ids':['placeholder-mobile'],
                'mechanism_match_basis':{axis:{'status':'MATCH','observation':'Synthetic control'} for axis in d.AXES}}
        units.append(unit)
    sources = b.EvidenceSources({},
        {u['reference_id']:{'reference_id':u['reference_id'],'canonical_url':u['official_url'],
                             'active_in_recovered_corpus':'true'} for u in units}, {}, [],
        {'SYNTHETIC-ARCHIVE':{'archive_id':'SYNTHETIC-ARCHIVE', 'archive_status':'DURABLE_VERIFIED',
                            'archive_locator':'https://evidence.example.test/synthetic-archive',
                            'container_sha256':legacy.digest('DECLARED_SYNTHETIC_ARCHIVE')}}, {}, {})
    for unit in units:
        for label in ('DESKTOP','MOBILE'):
            replace_capture(unit,sources,label,1)
    relation = reviewed_relation(*units,sources)
    return *units, relation, sources
