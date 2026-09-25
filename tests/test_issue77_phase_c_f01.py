from lp_engine.phase_c_authorship_correction import PAIR_IDS,load_corrected_contracts
from lp_engine.phase_c_visual_composition import F01_COMPOSITION_CSS,apply_f01_composition
from pathlib import Path
from tempfile import TemporaryDirectory

def test_issue77_has_two_f01_profiles_with_material_rules():
    assert set(F01_COMPOSITION_CSS)=={"three","baum"}
    for css in F01_COMPOSITION_CSS.values():
        assert "nth-child(1)" in css and "nth-child(2)" in css and "nth-child(4)" in css
        assert "grid-template-columns" in css or "display:block" in css

def test_issue77_injects_actual_f01_render_attributes_idempotently():
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/"index.html"
        path.write_text("<html><head></head><body class=\"x\"><main></main></body></html>",encoding="utf-8")
        first=apply_f01_composition(path,"three")
        second=apply_f01_composition(path,"three")
        rendered=path.read_text(encoding="utf-8")
        assert first["status"]=="applied"
        assert second["status"]=="already_applied"
        assert rendered.count("<style data-issue77-f01=")==1
        assert rendered.count("<body data-issue77-f01=")==1

def test_issue77_preserves_accepted_non_f01_pairs():
    rows={r["company_id"]:r for r in load_corrected_contracts()}
    for family,(left,right) in PAIR_IDS.items():
        if family=="BW-F01": continue
        assert rows[left]["public_authorship"]["renderer_profile"] != rows[right]["public_authorship"]["renderer_profile"]
