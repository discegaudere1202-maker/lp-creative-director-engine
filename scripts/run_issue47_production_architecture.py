"""Build the auditable Issue #47 architecture contract package."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "issue47_production_architecture"
ARCH = ROOT / "data" / "production_architecture"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(ARCH.glob("*.json")):
        shutil.copy2(path, OUT / path.name)
    test = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_production_architecture_contract.py"], cwd=ROOT, text=True, capture_output=True)
    (OUT / "dedicated_tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    write(OUT / "architecture_validation.json", {"status": "PASS" if test.returncode == 0 else "FAIL", "exit_code": test.returncode, "contract_scope": "Issue #47 Production Architecture v1", "human_screenshot_review": "REQUIRED_FOR_RESEMBLANCE", "visual_output_changed": False})
    write(OUT / "provenance.json", {"research_issue": 44, "research_head": "135e15276da07279731d48ff2b1306fae2411db4", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "source": "data/production_architecture/provenance_manifest_v1.json"})
    files = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "manifest.sha256"}:
            files.append({"path": path.relative_to(OUT).as_posix(), "sha256": sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    manifest = {"schema_version": "issue47_artifact_manifest_v1", "status": "PASS" if test.returncode == 0 else "FAIL", "files": files}
    write(OUT / "manifest.json", manifest)
    (OUT / "manifest.sha256").write_text(canonical_manifest_hash(manifest) + "  manifest.json\n", encoding="utf-8")
    return test.returncode


def canonical_manifest_hash(manifest: dict[str, object]) -> str:
    return sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
