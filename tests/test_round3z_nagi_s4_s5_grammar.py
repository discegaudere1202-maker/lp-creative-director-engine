import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'artifacts/round3z_nagi_s4_s5_grammar'

def test_round3z_qa_and_artifact():
    q=json.loads((OUT/'browser_qa.json').read_text(encoding='utf-8')); g=json.loads((OUT/'fixed_header_measurements.json').read_text(encoding='utf-8'))
    assert q['status']=='PASS' and q['total']==9 and q['pass']==9 and g['status']=='PASS'
    assert json.loads((OUT/'round3z_contract_report.json').read_text(encoding='utf-8'))['HR-01']=='PASS'

def test_round3z_holds_human_gate():
    s=json.loads((OUT/'summary.json').read_text(encoding='utf-8')); assert s['status']=='HOLD — SARAH HUMAN VISUAL REVIEW PENDING'; assert s['formal_human_quality_pass'] is False; assert s['human_review_ready']=='YES'

def test_round3z_copy_and_scene_preserve():
    html=(OUT/'site/index.html').read_text(encoding='utf-8'); assert all(f'id="s{i}"' in html for i in range(1,9)); assert 'class="scene receive"' in html and 'class="scene trust"' in html and 'class="scene action"' in html; assert '何を学べるのか。受講条件はどうか。' in html
