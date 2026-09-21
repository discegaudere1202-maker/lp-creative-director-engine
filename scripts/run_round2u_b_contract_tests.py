"""Static contract checks for Round 2U-B blocker closure."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2u_b", ROOT / "scripts" / "run_round2u_b_nagi_shun_review_blocker_closure.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load Round 2U-B runner")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.STARTING_HEAD == "bf0bdf378b3d6b73f6416a297898c72ef766148e"
assert "authored-line" in module.TYPOGRAPHY_CSS
assert "制作時" in module.PUBLIC_STATE_WORDS
assert "実際の担当者" in module.TRUST_FABRICATION_WORDS
assert len(module.BASE.SCENES) == 12
for token in ("今の目的は、", "その前に、知りたいこと。", "確認できます。", "料金と時間の詳細"):
    assert token in inspect.getsource(module.authored_markup)
print("Round 2U-B contract tests: PASS")
