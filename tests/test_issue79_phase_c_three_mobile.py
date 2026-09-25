from pathlib import Path
from tempfile import TemporaryDirectory
from lp_engine.phase_c_visual_composition import F01_COMPOSITION_CSS,apply_f01_composition

def test_issue79_three_mobile_rule_is_scoped_and_readable():
    css=F01_COMPOSITION_CSS["three"]
    assert "@media (max-width:767px)" in css
    assert "word-break:keep-all" in css
    assert "overflow-wrap:normal" in css
    assert "nth-child(3)" in css

def test_issue79_mobile_injection_is_idempotent():
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/"index.html"
        path.write_text("<html><head></head><body class=\"x\"><main></main></body></html>",encoding="utf-8")
        assert apply_f01_composition(path,"three")["status"]=="applied"
        assert apply_f01_composition(path,"three")["status"]=="already_applied"
        text=path.read_text(encoding="utf-8")
        assert text.count("<style data-issue77-f01=")==1
