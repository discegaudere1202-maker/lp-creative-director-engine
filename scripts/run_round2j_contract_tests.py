"""Deterministic source contract runner for Round 2J."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("round2j_nagi", ROOT / "scripts" / "run_round2j_nagi_quality_ceiling.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def main() -> int:
    manifest = {key: {"output": f"assets/{key}.png", "source": "fixture", "evidence_state": "representative"} for key in MODULE.H.F.ASSETS}
    markup = MODULE.build_html_j(manifest)
    for text in ("受けたい。学びたい。", "ヒーリングについて知りたい。", "今の目的に合わせて、", "3つから選べます。", "料金・時間・場所・流れを、", "まとめて確認。"):
        assert text in markup, text
    assert '<div class="hero-context"' not in markup
    assert "purpose-stage" in markup and "choice-image" in markup
    assert "service-ledger" in markup and "data-derived-key" in markup
    assert "choiceStage" in MODULE.J_SCRIPT_TEMPLATE and "purposeDetails" in MODULE.J_SCRIPT_TEMPLATE
    contract = {field: [field] for field in MODULE.CEILING_CONTRACT_FIELDS}
    assert MODULE.validate_ceiling_director_contract(contract)["status"] == "PASS"
    assert MODULE.H.provisional_propagation_gate(MODULE.H.FACTS, MODULE.DERIVED_COPY)["status"] == "PASS"
    assert not re.search(r"<p class=\"eyebrow\">(?:01 /|02 /|03 /)", markup)
    print("Round 2J contract tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
