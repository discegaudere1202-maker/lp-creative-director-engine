from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2qb", ROOT / "scripts" / "run_round2q_b_public_leak_closure.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load Round 2Q-B runner")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
manifest = {key: {"output": f"assets/{key}.png", "source": "generated", "evidence_state": "PROVISIONAL"} for key in ("A01", "A02", "A04", "A05", "A06", "A07")}
before, after = B.build_html_qb(manifest)
assert "DETAIL → RELATIONSHIP" in B.visible_text(before)
assert "DETAIL → RELATIONSHIP" not in B.visible_text(after)
assert "hero-motion-note" in after
assert B.public_leak_audit(after)["status"] == "PASS"
assert before.replace('<p class="hero-motion-note">DETAIL → RELATIONSHIP</p>', "") == after
print("Round 2Q-B contract tests: PASS")
