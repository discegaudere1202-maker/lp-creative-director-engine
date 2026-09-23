import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'artifacts/round3k_r_nagi_architecture'
def test_independent_scene_and_copy_contract():
    qa=json.loads((OUT/'browser_qa.json').read_text(encoding='utf-8')); line=json.loads((OUT/'line_composition_qa.json').read_text(encoding='utf-8')); ledger=json.loads((OUT/'customer_copy_ledger.json').read_text(encoding='utf-8')); legacy=json.loads((OUT/'legacy_copy_qa.json').read_text(encoding='utf-8')); order=json.loads((OUT/'scene_order_qa.json').read_text(encoding='utf-8'))
    assert qa['status']=='PASS' and qa['total']==9 and line['status']=='PASS'
    assert legacy['known_legacy_count']==0 and ledger['status']=='PASS' and [x['scene_id'] for x in order['scenes']]==[f'S{i}' for i in range(1,9)]
    html=(OUT/'reproduction/index.html').read_text(encoding='utf-8'); assert '今したいことから' not in html and '選んだサービス' not in html and '内容から読む' not in html
def test_media_boundary_and_hold():
    media=json.loads((OUT/'media_role_manifest.json').read_text(encoding='utf-8')); boundary=json.loads((OUT/'evidence_boundary.json').read_text(encoding='utf-8')); final=json.loads((OUT/'final_qa.json').read_text(encoding='utf-8'))
    assert media['human_perception_qa']=='PASS' and {x['scene'] for x in media['assets']}=={'S1','S3','S4','S5','S8'} and boundary['status']=='PASS' and final['status'].startswith('HOLD')
