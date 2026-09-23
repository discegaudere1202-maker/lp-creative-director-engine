from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts'/'round3i_br_f'
def test_full_page_contract_and_qa():
    qa=json.loads((OUT/'browser_qa.json').read_text(encoding='utf-8'))
    assert qa['status']=='PASS';assert qa['aoi_formal']=='PENDING_HUMAN_REVIEW'
    assert {r['width'] for r in qa['rows']}=={1440,1280,390,375,320}
    assert all(r['overflow']==0 and not r['console_errors'] and not r['page_errors'] and not r['request_failures'] for r in qa['rows'])
def test_full_page_evidence_and_manifest():
    m=json.loads((OUT/'artifact_manifest.json').read_text(encoding='utf-8'));paths={f['path'] for f in m['files']}
    for p in ('site/index.html','browser_qa.json','aoi_review.json','asset_manifest.json','media_role_manifest.json','evidence_boundary.json','choreography.json','revision_trace.json','final_qa.json','site/assets/material/hero-field.svg','site/assets/material/middle-light.svg','site/assets/material/ending-open.svg'):
        assert p in paths
