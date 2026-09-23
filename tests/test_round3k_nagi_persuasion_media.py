import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"artifacts/round3k_nagi_persuasion_media"
def test_copy_media_and_line_contract():
    qa=json.loads((OUT/"browser_qa.json").read_text(encoding='utf-8'));line=json.loads((OUT/"line_composition_qa.json").read_text(encoding='utf-8'));copy=json.loads((OUT/"copy_ssot.json").read_text(encoding='utf-8'));media=json.loads((OUT/"media_role_manifest.json").read_text(encoding='utf-8'))
    assert qa['status']=='PASS' and qa['total']==9 and line['status']=='PASS' and line['orphan_line_count']==0
    assert set(media['material_media_scenes'])=={'S1','S3','S4','S5','S8'} and copy['status']=='COPY_READY'
    html=(OUT/"reproduction/index.html").read_text(encoding='utf-8');assert '公式Instagramを開く' in html and '内容を見てから、' not in html
def test_evidence_and_stop_status():
    asset=json.loads((OUT/"asset_manifest.json").read_text(encoding='utf-8'));boundary=json.loads((OUT/"evidence_boundary.json").read_text(encoding='utf-8'));final=json.loads((OUT/"final_qa.json").read_text(encoding='utf-8'))
    assert len(asset['assets'])==5 and boundary['status']=='PASS' and final['status'].startswith('HOLD')
