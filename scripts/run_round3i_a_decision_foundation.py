from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.nagi_decision_foundation import build_phase_a, write_artifact_manifest  # noqa: E402


def main() -> int:
    out = ROOT / "artifacts" / "round3i_a"
    result = build_phase_a(ROOT, out)
    write_artifact_manifest(out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["phase_a_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
