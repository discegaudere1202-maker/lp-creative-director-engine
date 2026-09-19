"""Run the Round 2F-B2 Maylynn Creative Direction Fidelity package."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.environ["ROUND2F_VARIANT"] = "B2"
os.environ.setdefault("ROUND2F_B_OUTPUT_ROOT", str(ROOT / "artifacts" / "round2f_b2"))

import run_round2f_b_maylynn as runner


if __name__ == "__main__":
    raise SystemExit(runner.main())
