"""Static contract checks for the isolated Round 2U Nagi prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2u", ROOT / "scripts" / "run_round2u_nagi_creative_translation.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load Round 2U runner")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.STARTING_HEAD == "967480464c614642732774575f22377ebc681d93"
assert len(module.SCENES) == 12
assert [scene[2] for scene in module.SCENES] == [
    "ORIENT", "SELF-IDENTIFY", "CHOOSE", "UNDERSTAND", "EVALUATE", "EVALUATE",
    "UNDERSTAND", "TRUST", "COMPARE", "RESOLVE", "CONTACT", "CONTACT",
]
assert {scene[1] for scene in module.SCENES} >= {"HERO", "SELECTOR", "TREATMENT", "SCHOOL", "HEALING", "CONTACT"}
assert "ORIENT → SELF-IDENTIFY → CHOOSE → UNDERSTAND → EVALUATE → TRUST → COMPARE → RESOLVE → CONTACT" in module.BLUEPRINT["source"] or module.BLUEPRINT["schema_version"]
for token in ("hero", "selector", "service", "contact", "prefers-reduced-motion"):
    assert token in module.CSS.casefold()
for token in ("setHero", "setService", "instagram_click", "serviceData"):
    assert token in module.JS
assert module.INSTAGRAM.endswith("happyfuture_02/")
print("Round 2U contract tests: PASS")
