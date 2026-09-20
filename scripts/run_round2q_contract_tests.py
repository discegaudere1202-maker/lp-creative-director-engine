"""Fast deterministic contract checks for Round 2Q without browser startup."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2q", ROOT / "scripts" / "run_round2q_nagi_growth.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load Round 2Q runner")
Q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)

manifest = {key: {"output": f"assets/{key}.png", "source": "generated", "evidence_state": "PROVISIONAL"} for key in ("A01", "A02", "A04", "A05", "A06", "A07")}
markup = Q.build_html_q(manifest)
required = ("DETAIL_TO_RELATIONSHIP", "guided-preview-click-lock", "dataLayer", "service_preview", "service_selected", "price_view", "instagram_click", "path-merge")
missing = [token for token in required if token not in markup]
forbidden = [token for token in ("入口を見る", "三つの入口", "HUMAN CINEMA") if token in markup]
if missing or forbidden:
    raise SystemExit(f"Round 2Q contract tests: FAIL missing={missing} forbidden={forbidden}")
print("Round 2Q contract tests: PASS")
