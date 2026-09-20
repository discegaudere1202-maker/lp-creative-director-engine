"""Deterministic, dependency-light contract runner for Round 2H-H CI."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("round2h_h_nagi", ROOT / "scripts" / "run_round2h_h_nagi.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def main() -> int:
    manifest = {key: {"output": f"assets/{key}.png"} for key in MODULE.F.ASSETS}
    markup = MODULE.build_html_h(manifest)
    propagation = MODULE.provisional_propagation_gate(MODULE.FACTS, MODULE.DERIVED_COPY)
    assert propagation["status"] == "PASS", propagation
    assert "60分 8,800円 / 90分 12,100円" in markup
    assert "1日講座 33,000円、約5時間" in markup
    assert "ヒアリング → 施術 → 余韻の確認" in markup
    assert "料金を相談時に確認" not in markup
    assert "施術・講座の時間を事前に確認" not in markup
    for token in ("body.in-entry .sticky-cta", "body.in-guide .sticky-cta", "anchor-active .header", "scroll-margin-top", "data-derived-key"):
        assert token in markup, token
    assert len(re.findall(r'data-derived-key=', markup)) >= 5
    print("Round 2H-H contract tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
