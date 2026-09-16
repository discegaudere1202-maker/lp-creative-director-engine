"""Round 1E-A2 photography binary preflight."""
from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GENERATED = [
    ("maylynn_paint", "hero_home_finish", "c140090c-9549-4fba-8074-c60b0abd32e8", "assets/photography/generated/maylynn_paint/hero_home_finish.png", "maylynn_paint_hero_home_finish_generated_v1.json"),
    ("nagi_no_mirai", "hero_treatment_space", "baf79d66-7fe7-4080-96b4-01aad7cae1fd", "assets/photography/generated/nagi_no_mirai/hero_treatment_space.png", "nagi_no_mirai_hero_generated_v1.json"),
    ("nagi_no_mirai", "sensory_detail", "51ba4f8e-4e6c-415d-bc79-df36d8c0e2b1", "assets/photography/generated/nagi_no_mirai/sensory_detail.png", "nagi_no_mirai_sensory_detail_generation_v1.json"),
    ("nagi_no_mirai", "welcome_human", "f06d5132-017f-4227-94ae-a1d511021055", "assets/photography/generated/nagi_no_mirai/welcome_human.png", "nagi_no_mirai_welcome_human_generation_v1.json"),
    ("watashi_no_daidokoro", "hero_shared_cooking", "76923b73-3b6c-4222-b910-cbd02a00ce39", "assets/photography/generated/watashi_no_daidokoro/hero_shared_cooking.png", "watashi_no_daidokoro_hero_shared_cooking_generation_v1.json"),
    ("watashi_no_daidokoro", "finished_table", "a7c2d1c5-2e46-433e-a3d4-a6527485fc26", "assets/photography/generated/watashi_no_daidokoro/finished_table.png", "watashi_no_daidokoro_finished_table_generation_v1.json"),
]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results, hashes = [], {}
    for company, role, gen_id, rel, metadata_name in GENERATED:
        path = ROOT / rel
        errors = []
        metadata = ROOT / "data" / "photography" / metadata_name
        if not metadata.exists():
            errors.append("required_metadata_missing")
        else:
            raw = json.loads(metadata.read_text(encoding="utf-8"))
            selected = raw.get("selected_asset", {})
            actual_gen_id = selected.get("gen_id") or selected.get("generation_reference", {}).get("gen_id")
            if actual_gen_id != gen_id or selected.get("photo_role") != role:
                errors.append("metadata_identity_mismatch")
            if selected.get("approval_status") != "RESEARCH_APPROVED_GENERATED_VISUAL":
                errors.append("approval_status_invalid")
        if not path.is_file() or path.stat().st_size == 0:
            errors.append("binary_missing_or_empty")
        width = height = None
        if not errors or path.is_file():
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
                    if image.format not in {"PNG", "JPEG"}:
                        errors.append("invalid_image_type")
            except Exception:
                errors.append("invalid_image")
        if path.is_file() and path.stat().st_size:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in hashes:
                errors.append(f"duplicate_hash:{hashes[digest]}")
            hashes[digest] = role
        results.append({"company": company, "photo_role": role, "gen_id": gen_id, "canonical_local_path": rel, "status": "AVAILABLE_BINARY" if not errors else "BLOCKED_BY_ASSET_BINARY", "errors": errors, "width": width, "height": height, "file_hash": digest if path.is_file() and path.stat().st_size else ""})
    passed = all(x["status"] == "AVAILABLE_BINARY" for x in results)
    payload = {"schema_version": "photography_asset_preflight_v1", "status": "PASS" if passed else "BLOCKED_BY_ASSET_BINARY", "engine_wiring_allowed": passed, "generated": results}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if payload["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
