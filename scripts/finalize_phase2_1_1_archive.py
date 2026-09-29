"""Bind Gold evidence ledgers to a verified, pinned Library archive."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
ARCHIVE={
 'archive_id':'GOLD20-FULLPAGE-V1',
 'backend':'CHATGPT_LIBRARY',
 'library_file_id':'libfile_82b0e73d52fc8191a1bba85895a23ebe',
 'file_id':'file_000000005b588209a215e3daf141e7cd',
 'version_number':0,
 'file_name':'creative_mechanism_gold20_fullpage_v1_sha256-4929f73c.zip',
 'archive_sha256':'4929f73c81d7b8028ad986380ebeb789642a9800cd23685866355c5b41885028',
 'download_url':'https://chatgpt.com/api/library/files/libfile_82b0e73d52fc8191a1bba85895a23ebe/download',
 'entry_count':230,
 'retention_policy':'Keep for at least 3 years after last mechanism use; review yearly, never replace this version; no backend retention guarantee is asserted.',
 'verification_policy':'On ingestion and before promotion or reuse, pin file_id/version, materialize, verify container SHA-256 and each referenced entry SHA-256. Recheck monthly.',
 'recapture_policy':'If stale, inaccessible or content changed, keep original immutable ledger, recapture from original URL with new snapshot/version and re-review claims and scores.',
 'invalidation_policy':'Changed page or mismatched hash invalidates downstream score, mechanism and promotion until new observed evidence is approved.',
 'archive_loss_policy':'Fail closed: set ARCHIVE_UNAVAILABLE and HOLD; never promote or rank from absent bytes.'
}

def lines(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def write(path, rows):path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows))

def bind(row, prefix, image_key, hash_key='content_hash'):
    if not row[image_key]:
        assert row.get('observation_state') in ('NOT_APPLICABLE','NOT_OBSERVED','MISSING')
        row['archive_locator']=None
        row['archive_entry']=None
        row['archive_status']='NOT_APPLICABLE_NO_CAPTURE'
        return row
    row['archive_locator']=ARCHIVE['download_url']
    row['archive_entry']=prefix+'/'+row[image_key]
    row['archive_status']='DURABLE_VERIFIED'
    row['archive_id']=ARCHIVE['archive_id']
    row['archive_file_id']=ARCHIVE['file_id']
    row['archive_version_number']=ARCHIVE['version_number']
    row['archive_container_sha256']=ARCHIVE['archive_sha256']
    assert len(row[hash_key])==64
    return row

def main():
    (DATA/'creative_mechanism_phase2_1_1_archive_manifest.json').write_text(json.dumps(ARCHIVE,ensure_ascii=False,indent=2)+'\n')
    for fname,prefix,key in (
      ('creative_mechanism_phase2_1_gold_snapshots.jsonl','capture','screenshot_identifier'),
      ('creative_mechanism_phase2_1_gold_scene_evidence.jsonl','capture','screenshot_identifier'),
      ('creative_mechanism_phase2_1_1_fullpage_scenes.jsonl','traversal','screenshot_identifier')):
        path=DATA/fname
        write(path,[bind(x,prefix,key) for x in lines(path)])
    path=DATA/'creative_mechanism_phase2_1_gold_references.csv'
    with path.open(newline='') as f: rows=list(csv.DictReader(f));fields=list(rows[0])
    for r in rows:
        r['evidence_status']='DURABLE_VERIFIED'
        r['decision_reason']=r['decision_reason'].replace('TEMPORARY_CAPTURE; ','')
        reason='full LP score and runtime checks not complete; HOLD'
        if reason not in r['decision_reason']:r['decision_reason']+='; '+reason
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
    # Numeric ratings were made on entry/first-scroll and remain scoped there.
    path=DATA/'creative_mechanism_phase2_1_gold_scores.jsonl'
    scores=lines(path)
    traversals=lines(DATA/'creative_mechanism_phase2_1_1_fullpage_scenes.jsonl')
    by_ref={r:sorted(x['scene_evidence_id'] for x in traversals if x['reference_id']==r and x['observation_state']=='OBSERVED') for r in {x['reference_id'] for x in traversals}}
    for x in scores:
        x['corpus_ranking_allowed']=False
        x['canonical_promotion_allowed']=False
        x['numeric_score_scope']='CAPTURED_ENTRY_AND_FIRST_SCROLL_ONLY'
        x['additional_fullpage_static_scene_ids']=by_ref.get(x['reference_id'],[])
        x['full_lp_score_status']='NOT_SCORED'  # no score inflation from cropped imagery
    write(path,scores)
    print({'snapshots':118,'original_scenes':80,'traversal_scenes':len(traversals),'scores':len(scores)})

if __name__=='__main__':main()
