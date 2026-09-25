from pathlib import Path
from tempfile import TemporaryDirectory
from lp_engine.phase_c_authorship_correction import RENDERER_PROFILE_BY_COMPANY, load_corrected_contracts
from lp_engine.phase_c_visual_composition import PROFILE_CSS, RENDERER_PROFILES, apply_visual_composition

def test_issue74_assigns_distinct_renderer_profiles_to_all_eight_references():
    rows = load_corrected_contracts()
    profiles = [row["public_authorship"]["renderer_profile"] for row in rows]
    assert len(profiles) == 8
    assert len(set(profiles)) == 8
    assert set(profiles) == set(RENDERER_PROFILES)
    assert set(RENDERER_PROFILE_BY_COMPANY.values()) == set(RENDERER_PROFILES)

def test_issue74_profiles_have_material_composition_rules():
    for profile, spec in RENDERER_PROFILES.items():
        css = PROFILE_CSS[profile]
        assert spec["hero"] and spec["core"] and spec["closing"]
        assert f'data-issue74-profile="{profile}"' in css
        assert "nth-child" in css
        assert "grid-template-columns" in css or "display:flex" in css

def test_issue74_html_injection_is_render_level_and_idempotent():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "index.html"
        path.write_text("<html><head></head><body class=\"profile-default\"><main></main></body></html>", encoding="utf-8")
        first = apply_visual_composition(path, "diagnostic-route")
        rendered = path.read_text(encoding="utf-8")
        second = apply_visual_composition(path, "diagnostic-route")
        assert first["status"] == "applied"
        assert second["status"] == "already_applied"
        assert rendered.count("<style data-issue74-profile=") == 1\n        assert rendered.count("<body data-issue74-profile=") == 1
        assert "split-diagnostic" not in rendered
