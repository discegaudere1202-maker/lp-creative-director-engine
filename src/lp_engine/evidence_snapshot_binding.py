"""Re-derive attribution subjects from canonical reference/capture records.

Digests prove record identity, not the semantic truth of attribution. Family
assertions still require an explicit reviewer and cited source evidence.
"""
from dataclasses import dataclass
import csv
import json
from . import mechanism_runtime as legacy

SCHEMA = 'REFERENCE_EVIDENCE_SNAPSHOT_V1'
ASSERTION_SCHEMA = 'SNAPSHOT_BOUND_FAMILY_ASSERTION_V1'
FIX_DATA = legacy.ROOT / 'data/phase2_2_1d_snapshot_binding_fix'
RECOVERY_DATA = legacy.ROOT / 'data/phase2_2_1a_recovery'
UNIT_FIELDS = ('unit_id', 'candidate_id', 'mechanism_id', 'reference_id',
               'independent_evidence_unit_id', 'official_url', 'page_family')
# Omit absent fields; never synthesize capture times, snapshot IDs or URLs.
CAPTURE_FIELDS = (
    'scene_evidence_id', 'snapshot_id', 'parent_snapshot_id', 'reference_id',
    'viewport_label', 'viewport', 'page_y_range', 'screenshot_identifier',
    'scene_crop_identifier', 'parent_screenshot_identifier', 'content_hash',
    'parent_content_hash', 'archive_id', 'archive_entry', 'archive_locator',
    'archive_status', 'archive_file_id', 'archive_version_number',
    'archive_container_sha256', 'backend', 'library_file_id', 'pinned_file_id',
    'version_id', 'container_sha256', 'captured_at', 'derived_at', 'run_id',
    'capture_run_id', 'original_url', 'final_url', 'manifest_entry',
    'manifest_sha256', 'source_artifact', 'member_kind', 'capture_state',
    'storage_state', 'capture_record_state', 'capture_log_archive_entry',
    'capture_log_archive_id', 'capture_log_archive_locator',
    'capture_log_archive_status', 'capture_log_content_hash')
ARCHIVE_FIELDS = ('archive_id', 'backend', 'archive_status', 'archive_locator',
                  'library_file_id', 'pinned_file_id', 'version_id',
                  'version_number', 'container_sha256', 'file_name', 'filename')


def require(condition, reason):
    if not condition:
        raise ValueError('SNAPSHOT_BINDING:' + reason)


def sha256_value(value):
    return (isinstance(value, str) and len(value) == 64 and
            all(c in '0123456789abcdef' for c in value))


def present(record, fields):
    return {key: record[key] for key in fields if key in record}


def source_record_id(unit):
    value = unit.get('unit_id') or unit.get('candidate_id')
    require(isinstance(value, str) and bool(value), 'SOURCE_RECORD_ID_MISSING')
    return value


@dataclass
class EvidenceSources:
    units: dict
    references: dict
    scenes: dict
    snapshots: list
    archives: dict
    verified_members: dict
    attribution_evidence: dict


def index_unique(records, key):
    result = {}
    for record in records:
        identity = record.get(key)
        require(isinstance(identity, str) and identity and identity not in result,
                'MISSING_OR_DUPLICATE_' + key.upper())
        result[identity] = record
    return result


def load_sources(units, readback, attribution_evidence):
    with (RECOVERY_DATA / 'reference_master.csv').open() as stream:
        references = list(csv.DictReader(stream))
    unit_index = {}
    for unit in units:
        key = source_record_id(unit)
        require(key not in unit_index, 'DUPLICATE_UNIT_SOURCE_RECORD')
        unit_index[key] = unit
    members = {}
    for record in readback['members']:
        if record.get('result') == 'PASS':
            key = (record['archive_id'], record['archive_member'])
            require(key not in members and sha256_value(record.get('sha256')),
                    'DUPLICATE_OR_INVALID_READBACK_MEMBER')
            members[key] = record['sha256']
    return EvidenceSources(
        unit_index, index_unique(references, 'reference_id'),
        index_unique(legacy.load_jsonl(RECOVERY_DATA / 'scene_evidence.jsonl'), 'scene_evidence_id'),
        legacy.load_jsonl(RECOVERY_DATA / 'snapshots.jsonl'),
        index_unique(json.loads((RECOVERY_DATA / 'archive_registry.json').read_text()), 'archive_id'),
        members, index_unique(attribution_evidence, 'attribution_evidence_id'))


def capture_record(record, sources, reference_id, viewport_label):
    require(record.get('reference_id') == reference_id and
            record.get('viewport_label') == viewport_label, 'CAPTURE_SUBJECT_MISMATCH')
    require(record.get('archive_status') == 'DURABLE_VERIFIED' and
            sha256_value(record.get('content_hash')), 'CAPTURE_NOT_HASHED_AND_DURABLE')
    archive = sources.archives.get(record.get('archive_id'), {})
    require(archive.get('archive_status') == 'DURABLE_VERIFIED' and
            archive.get('archive_locator') and sha256_value(archive.get('container_sha256')),
            'ARCHIVE_IDENTITY_MISSING')
    require(record.get('archive_entry') and record.get('archive_locator') == archive['archive_locator'],
            'ARCHIVE_LOCATOR_MISMATCH')
    for field in ('library_file_id', 'pinned_file_id', 'version_id', 'container_sha256'):
        if field in record:
            require(record[field] == archive.get(field), 'ARCHIVE_' + field.upper() + '_MISMATCH')
    if 'archive_container_sha256' in record:
        require(record['archive_container_sha256'] == archive['container_sha256'], 'ARCHIVE_CONTAINER_MISMATCH')
    require(sources.verified_members.get((record['archive_id'], record['archive_entry'])) == record['content_hash'],
            'CAPTURE_MEMBER_HASH_MISMATCH')
    return {'capture': present(record, CAPTURE_FIELDS),
            'archive': present(archive, ARCHIVE_FIELDS)}


def parent_snapshot(scene, sources):
    parent_id = scene.get('parent_snapshot_id')
    if parent_id:
        matches = [s for s in sources.snapshots if s.get('snapshot_id') == parent_id]
    else:
        require(scene.get('parent_screenshot_identifier') and sha256_value(scene.get('parent_content_hash')),
                'PARENT_SNAPSHOT_IDENTITY_MISSING')
        matches = [s for s in sources.snapshots
                   if s.get('reference_id') == scene.get('reference_id') and
                   s.get('viewport_label') == scene.get('viewport_label') and
                   s.get('screenshot_identifier') == scene['parent_screenshot_identifier'] and
                   s.get('content_hash') == scene['parent_content_hash']]
    require(len(matches) == 1, 'PARENT_SNAPSHOT_MISSING_OR_AMBIGUOUS')
    snapshot = matches[0]
    if 'parent_content_hash' in scene:
        require(scene['parent_content_hash'] == snapshot.get('content_hash'), 'PARENT_PIXEL_HASH_MISMATCH')
    else:
        # Recovery scene records can point at a whole captured snapshot. This
        # path is allowed only when the existing source fields prove equality.
        require(scene.get('snapshot_id') == parent_id and
                all(scene.get(k) == snapshot.get(k) for k in ('archive_id', 'archive_entry', 'content_hash')),
                'PARENT_PIXEL_BINDING_MISSING')
    if 'parent_screenshot_identifier' in scene:
        require(scene['parent_screenshot_identifier'] == snapshot.get('screenshot_identifier'),
                'PARENT_SCREENSHOT_MISMATCH')
    return snapshot


def evidence_snapshot(unit, sources):
    """Return a new digest from records; ignore any digest supplied on unit."""
    identity = source_record_id(unit)
    canonical = sources.units.get(identity)
    require(canonical is not None, 'UNIT_SOURCE_RECORD_NOT_REGISTERED')
    for field in UNIT_FIELDS + ('desktop_scene_ids', 'mobile_scene_ids', 'source_contract_sha256',
                               'discovery_source', 'verified_family_ids'):
        require(unit.get(field) == canonical.get(field), 'UNIT_SOURCE_RECORD_MISMATCH:' + field)
    reference_id = canonical.get('reference_id')
    reference = sources.references.get(reference_id, {})
    require(reference.get('canonical_url') == canonical.get('official_url') and
            reference.get('active_in_recovered_corpus') in (True, 'true'), 'REFERENCE_PAGE_IDENTITY_MISMATCH')
    from urllib.parse import urlsplit
    url = urlsplit(reference['canonical_url'])
    require(url.scheme in ('http', 'https') and url.netloc and
            canonical.get('page_family') == url.netloc + (url.path.rstrip('/') or '/'), 'PAGE_FAMILY_MISMATCH')
    require(canonical.get('independent_evidence_unit_id') and reference_id, 'UNIT_IDENTITY_MISSING')
    viewports = {}
    for label, key in (('DESKTOP', 'desktop_scene_ids'), ('MOBILE', 'mobile_scene_ids')):
        ids = canonical.get(key)
        require(isinstance(ids, list) and ids and len(ids) == len(set(ids)), 'MISSING_OR_DUPLICATE_' + label)
        records = []
        for scene_id in ids:
            scene = sources.scenes.get(scene_id, {})
            require(scene.get('scene_evidence_id') == scene_id and scene.get('observation_state') == 'OBSERVED',
                    'SCENE_NOT_OBSERVED_OR_WRONG_ID')
            snapshot = parent_snapshot(scene, sources)
            records.append({'scene': capture_record(scene, sources, reference_id, label),
                            'snapshot': capture_record(snapshot, sources, reference_id, label)})
        viewports[label] = records
    payload = {'schema': SCHEMA, 'source_record_id': identity,
               'unit': present(canonical, UNIT_FIELDS),
               'reference': present(reference, ('reference_id', 'canonical_url', 'url', 'captured_at', 'record_origin')),
               'viewports': viewports}
    return {'schema': SCHEMA, 'unit_id': canonical['independent_evidence_unit_id'],
            'evidence_snapshot_sha256': legacy.digest(payload), 'snapshot': payload}


def assertion_bound(claim, family, bindings, sources):
    """A stored review must match BOTH unit subjects and every cited record."""
    if not isinstance(claim, dict) or claim.get('schema') != ASSERTION_SCHEMA:
        return False
    review = claim.get('review', {})
    if not isinstance(review, dict):
        return False
    text_fields = (claim.get('assertion_id'), claim.get('basis'),
                   review.get('reviewer'), review.get('reviewed_at'))
    if (not all(isinstance(value, str) and value.strip() for value in text_fields) or
            claim.get('family') != family or
            claim.get('snapshot_bindings') != bindings or
            review.get('status') != 'REVIEWED' or not review.get('reviewer') or
            not review.get('reviewed_at') or not claim.get('basis')):
        return False
    citations = claim.get('attribution_evidence_digests')
    if not isinstance(citations, dict) or not citations:
        return False
    for identity, expected_digest in citations.items():
        evidence = sources.attribution_evidence.get(identity, {})
        if (not isinstance(evidence, dict) or not evidence or not sha256_value(expected_digest) or legacy.digest(evidence) != expected_digest or
                evidence.get('attribution_evidence_id') != identity or evidence.get('family') != family or
                evidence.get('snapshot_bindings') != bindings or
                not isinstance(evidence.get('observation'), str) or not evidence['observation'].strip() or
                not isinstance(evidence.get('primary_source_url'), str) or not evidence['primary_source_url'].strip()):
            return False
        from urllib.parse import urlsplit
        try:
            url = urlsplit(evidence['primary_source_url'])
        except ValueError:
            return False
        if url.scheme not in ('http', 'https') or not url.netloc:
            return False
    return True
