"""Static contract checks for the standalone Round 2S-B Motion Lab."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2s_b", ROOT / "scripts" / "run_round2s_b_nagi_motion_lab.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load Round 2S-B runner")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert len(module.EXPERIMENTS) == 6
assert [len(exp["variants"]) for exp in module.EXPERIMENTS[:3]] == [3, 2, 4]
required = {"benchmark_source", "observed_motion", "why_premium", "function", "nagi_translation", "start_state", "mid_state", "end_state", "understanding_delta", "emotional_delta", "what_not_to_copy"}
assert all(required.issubset(exp) for exp in module.EXPERIMENTS)
assert all(exp["variants"] for exp in module.EXPERIMENTS)
assert module.STARTING_HEAD == "687977c8062cdd61234ddbdfc75a80aa2b8a668b"
print("Round 2S-B contract tests: PASS")
