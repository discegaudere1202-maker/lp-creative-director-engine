"""Fail-closed Gold archive and semantic traversal validation."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
NAMES={
 'refs':'creative_mechanism_phase2_1_gold_references.csv',
 'snap':'creative_mechanism_phase2_1_gold_snapshots.jsonl',
 'old':'creative_mechanism_phase2_1_gold_scene_evidence.jsonl',
 'new':'creative_mechanism_phase2_1_1_fullpage_scenes.jsonl',
 'mechs':'creative_mechanism_phase2_1_gold_mechanisms.jsonl',
 'new_mechs':'creative_mechanism_phase2_1_1_fullpage_mechanisms.jsonl',
 'scores':'creative_mechanism_phase2_1_gold_scores.jsonl',
 'gates':'creative_mechanism_phase2_1_1_record_gates.jsonl',
 'index':'creative_mechanism_phase2_1_1_archive_index.jsonl'}

def lines(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def sha(blob):return hashlib.sha256(blob).hexdigest()

def validate(root=ROOT, archive_path=None):
 d=root/'data'; archive_path=Path(archive_path) if archive_path else None
 manifest=json.loads((d/'creative_mechanism_phase2_1_1_archive_manifest.json').read_text())
 cfg=json.loads((root/'config/creative_mechanism_db_architecture_v1_3_1.json').read_text())
 data={k:lines(d/v) for k,v in NAMES.items() if k!='refs'}
 with (d/NAMES['refs']).open(newline='') as f:refs=list(csv.DictReader(f))
 with (d/'creative_mechanism_phase2_pilot_references.csv').open(newline='') as f:pilot=list(csv.DictReader(f))
 assert len(pilot)==100 and len(refs)==20 and len({r['slot_id'] for r in refs})==20
 assert {r['reference_id'] for r in refs}<={r['reference_id'] for r in pilot}
 assert len(data['snap'])==118 and len(data['old'])==80 and len(data['new'])==71
 assert len(data['index'])==230 and len(data['gates'])==20*7
 assert archive_path and archive_path.is_file(), 'Pinned durable archive must be materialized; fail closed'
 assert sha(archive_path.read_bytes())==manifest['archive_sha256']
 assert manifest['backend']=='CHATGPT_LIBRARY' and manifest['library_file_id'] in manifest['download_url']
 assert manifest['file_id'] and manifest['version_number']==0
 assert cfg['archive_contract']['archive_id']==manifest['archive_id']
 assert cfg['phase2_gate']['remaining_80_allowed'] is False and cfg['phase2_gate']['bulk_collection_allowed'] is False
 index={x['archive_entry']:x['content_hash'] for x in data['index']}
 assert len(index)==230
 with ZipFile(archive_path) as z:
  assert set(z.namelist())==set(index)
  for name,digest in index.items():assert sha(z.read(name))==digest,('archive byte mismatch',name)
  all_scenes={x['scene_evidence_id']:x for x in data['old']+data['new']}
  assert len(all_scenes)==151
  for kind in ('snap','old','new'):
   for x in data[kind]:
    if x.get('observation_state') in ('NOT_APPLICABLE','MISSING','NOT_OBSERVED') and not x.get('screenshot_identifier'):
     assert x['archive_entry'] is None
     continue
    assert x['archive_status']=='DURABLE_VERIFIED' and x['archive_locator']==manifest['download_url']
    assert x['archive_file_id']==manifest['file_id'] and x['archive_version_number']==0
    assert x['archive_container_sha256']==manifest['archive_sha256']
    assert x['archive_entry'] in index and index[x['archive_entry']]==x['content_hash']
    assert sha(z.read(x['archive_entry']))==x['content_hash']
  for s in data['new']:
   assert s['reference_id'] in {r['reference_id'] for r in refs}
   assert s['parent_content_hash']==index['capture/'+s['parent_screenshot_identifier']]
   assert s['page_y_range'][0]<s['page_y_range'][1]
   assert s['concrete_locator'] and s['captured_at'] and s['original_url'] and s['final_url']
   if s['observation_state']=='OBSERVED':
    assert s['observed_facts'] and s['visible_structure']
    assert not any('Observed when capture exists' in f or 'Scene structure recorded' in f for f in s['observed_facts'])
   else:
    assert s['observation_state']=='NOT_OBSERVED' and s['scene_evidence_id']=='GOLD-P12-R01-MOBILE-TRAV-08'
    assert not s['observed_facts']
   assert s['motion_observation'].startswith('NOT_OBSERVED') and s['interaction_observation'].startswith('NOT_OBSERVED')
  claims=lines(d/'creative_mechanism_phase2_1_1_fullpage_claims.jsonl')
  assert {x['reference_id'] for x in claims}=={'P05-R04','P06-R02','P12-R01'}
  for claim in claims:
   scene=all_scenes[claim['scene_evidence_id']]
   assert scene['observation_state']=='OBSERVED' and scene['reference_id']==claim['reference_id']
   assert scene['screenshot_identifier']==claim['screenshot_identifier']
   assert claim['evidence_status'] not in ('PASS','VERIFIED_OUTCOME') and claim['risk_flag']
  coverage=json.loads((d/'creative_mechanism_phase2_1_1_traversal_coverage.json').read_text())
  assert len(coverage)==10
  for c in coverage:
   group=sorted((s for s in data['new'] if (s['reference_id'],s['viewport_label'])==(c['reference_id'],c['viewport_label'])),key=lambda x:x['page_y_range'][0])
   assert len(group)==c['scene_count'] and group[0]['page_y_range'][0]==0
   assert all(a['page_y_range'][1]==b['page_y_range'][0] for a,b in zip(group,group[1:]))
   assert group[-1]['page_y_range'][1]==c['page_coverage'][1]
   assert sum(x['observation_state']=='OBSERVED' for x in group)==c['observed_count']
   assert set(c['semantic_coverage'])=={'ENTRY','PROPOSITION_SOLUTION','SERVICE_PRODUCT','PROOF_TRUST','CONVERSION_CTA','CLOSING_NAVIGATION'}
   assert all(x['state'] in ('OBSERVED','NOT_OBSERVED','NOT_APPLICABLE') for x in c['semantic_coverage'].values())
  by_ref={r['reference_id']:r for r in refs}
  for m in data['mechs']+data['new_mechs']:
   src=m['source_scene_evidence_ids']
   assert src and len(src)==len(set(src))==m['evidence_count']
   assert m['status']=='CANDIDATE'
   assert all(all_scenes[s]['observation_state']=='OBSERVED' for s in src)
   refset=sorted({all_scenes[s]['reference_id'] for s in src})
   assert m['reference_lps']==refset and m['reference_count']==len(refset)
   assert m['unique_brand_count']==len({by_ref[r]['brand'] for r in refset})
   for field,source in [('unique_agency_count','design_agency'),('unique_campaign_count','campaign_family')]:
    vals={by_ref[r][source] for r in refset}
    assert m[field]==('UNKNOWN' if 'UNKNOWN' in vals else len(vals))
  assert all(r['evidence_status']=='DURABLE_VERIFIED' and r['strong_hold_reject']=='HOLD' for r in refs)
  assert all(not x['promotion_allowed'] and not x['corpus_ranking_allowed'] and not x['canonical_promotion_allowed'] and x['full_lp_score_status']=='NOT_SCORED' for x in data['scores'])
  assert all(x['score_scope']=='CAPTURED_ENTRY_AND_FIRST_SCROLL_ONLY' for x in data['scores'])
  issue_types={x['type'] for x in lines(d/'creative_mechanism_phase2_1_architecture_issues.jsonl')}
  expected={'DISCOVERY_TRACE','CAPTURE_TARGET','RESPONSIVE_SUBJECT','TEMPORAL_MOTION','ACCESSIBILITY_RUNTIME','CLAIM_TERMS','CROP_SELECTOR'}
  assert expected<=issue_types
  assert {(g['reference_id'],g['issue_type']) for g in data['gates']}=={(r['reference_id'],t) for r in refs for t in expected}
  assert all((g['gate_result']=='HOLD_AFFECTED_USE' and g['this_issue_blocks_promotion'] is True)
             if g['applicability']=='APPLICABLE' else
             (g['gate_result']=='NOT_APPLICABLE' and g['this_issue_blocks_promotion'] is False)
             for g in data['gates'])
  assert not any('TEMPORARY_CAPTURE' in x.get('archive_status','') for kind in ('snap','old','new') for x in data[kind])
  return {'pilot_preserved':len(pilot),'gold':len(refs),'snapshots':len(data['snap']),'archive_entries':len(index),
          'traversal_references':5,'viewports':len(coverage),'traversal_scenes':len(data['new']),
          'observed_traversal_scenes':sum(x['observation_state']=='OBSERVED' for x in data['new']),
          'new_candidates':len(data['new_mechs']),'per_record_gates':len(data['gates'])}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True)
 a=p.parse_args();print('PASS',json.dumps(validate(archive_path=a.archive)))
