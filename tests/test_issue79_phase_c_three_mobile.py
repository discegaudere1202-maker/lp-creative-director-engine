from pathlib import Path
from tempfile import TemporaryDirectory
from lp_engine.phase_c_visual_composition import F01_COMPOSITION_CSS,apply_f01_composition

def test_issue79_three_mobile_rule_is_scoped_and_readable():
    css=F01_COMPOSITION_CSS["three"]
    assert "@media (max-width:767px)" in css
    assert "word-break:keep-all" in css
    assert "overflow-wrap:normal" in css
    assert ".scene-layered-copy" in css

def test_issue79_mobile_injection_is_idempotent():
    with TemporaryDirectory() as tmp:
        path=Path(tmp)/"index.html"
        path.write_text("<html><head></head><body class=\"x\"><main></main></body></html>",encoding="utf-8")
        assert apply_f01_composition(path,"three")["status"]=="applied"
        assert apply_f01_composition(path,"three")["status"]=="already_applied"
        text=path.read_text(encoding="utf-8")
        assert text.count("<style data-issue77-f01=")==1
def test_issue81_three_fit_uses_mobile_meaning_break_without_clipping():
    from inspect import getsource
    from lp_engine import production_generation

    source = getsource(production_generation._render_premium_html)
    assert "暮らしに置いたときの相性を見る。" in source
    assert "headline-optical-three-fit" in source
    assert "headline-optical-mobile" in source
    assert "@media(max-width:767px)" in source
