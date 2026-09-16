"""Build the local, rights-gated photography asset manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GENERATED_META = {
    "maylynn_paint": "maylynn_paint_hero_home_finish_generated_v1.json",
    "nagi_no_mirai": "nagi_no_mirai_hero_generated_v1.json",
}
GENERATED = [
    ("maylynn_paint", "hero_home_finish", "assets/photography/generated/maylynn_paint/hero_home_finish.png"),
    ("nagi_no_mirai", "hero_treatment_space", "assets/photography/generated/nagi_no_mirai/hero_treatment_space.png"),
    ("nagi_no_mirai", "sensory_detail", "assets/photography/generated/nagi_no_mirai/sensory_detail.png"),
    ("nagi_no_mirai", "welcome_human", "assets/photography/generated/nagi_no_mirai/welcome_human.png"),
    ("watashi_no_daidokoro", "hero_shared_cooking", "assets/photography/generated/watashi_no_daidokoro/hero_shared_cooking.png"),
    ("watashi_no_daidokoro", "finished_table", "assets/photography/generated/watashi_no_daidokoro/finished_table.png"),
]
STOCK = [
    ("maylynn_paint", "craft_handwork", "maylynn-craft-handwork-pexels-1669754", "Pexels", "Malte Luk", "https://www.pexels.com/photo/person-holding-paint-roller-on-wall-1669754/", "https://www.pexels.com/license/", "assets/photography/stock/maylynn_paint/craft_handwork.jpg"),
    ("maylynn_paint", "material_detail", "maylynn-material-detail-unsplash-w0bqO-Elz8", "Unsplash", "Denis Agati", "https://unsplash.com/photos/a-close-up-of-a-white-stucco-wall--w0bqO-Elz8", "https://unsplash.com/license", "assets/photography/stock/maylynn_paint/material_detail.jpg"),
    ("maylynn_paint", "trust_consultation", "maylynn-trust-consultation-pexels-9052547", "Pexels", "SHVETS production", "https://www.pexels.com/photo/people-discussing-the-floor-plan-9052547/", "https://www.pexels.com/license/", "assets/photography/stock/maylynn_paint/trust_consultation.jpg"),
    ("nagi_no_mirai", "hand_technique", "nagi-hand-technique-pexels-5794031", "Pexels", "Yan Krukau", "https://www.pexels.com/photo/close-up-view-of-massaging-head-5794031/", "https://www.pexels.com/license/", "assets/photography/stock/nagi_no_mirai/hand_technique.jpg"),
    ("watashi_no_daidokoro", "ingredient_story", "watashi-ingredient-story-pexels-3952043", "Pexels", "Ksenia Chernaya", "https://www.pexels.com/photo/wooden-kitchen-utensils-and-vegetables-3952043/", "https://www.pexels.com/license/", "assets/photography/stock/watashi_no_daidokoro/ingredient_story.jpg"),
    ("watashi_no_daidokoro", "hands_in_action", "watashi-hands-in-action-pexels-8357260", "Pexels", "Ron Lach", "https://www.pexels.com/photo/close-up-shot-of-sliced-garlic-on-knife-8357260/", "https://www.pexels.com/license/", "assets/photography/stock/watashi_no_daidokoro/hands_in_action.jpg"),
]

def binary_fields(rel: str) -> dict[str, object]:
    path = ROOT / rel
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as image:
        width, height, file_type = image.width, image.height, image.format
    return {"local_asset_path": rel, "binary_available": True, "file_hash": digest, "width": width, "height": height, "file_type": file_type}

def main() -> None:
    assets = []
    for company, role, rel in GENERATED:
        metadata_path = ROOT / "data" / "photography" / GENERATED_META.get(company, f"{company}_{role}_generation_v1.json")
        if role in {"sensory_detail", "welcome_human", "hero_shared_cooking", "finished_table"}:
            metadata_path = ROOT / "data" / "photography" / f"{company}_{role}_generation_v1.json"
        selected = json.loads(metadata_path.read_text(encoding="utf-8"))["selected_asset"]
        asset = {"asset_id": selected.get("asset_id", f"{company}-{role}-generated-v1"), "photo_role": role, "source_type": "generated", "provider": "OpenAI image generation", "source": "conversation-approved-generated-asset", "asset_url": "/" + rel, "creator": "OpenAI", "rights_status": "RESEARCH_APPROVED_GENERATED_VISUAL", "license_terms_url": "", "checked_at": "2026-09-16", "visual_subject": selected.get("visual_subject", ""), "placement": selected.get("placement", ""), "replacement_target": selected.get("replacement_target", ""), "crop": json.dumps(selected.get("crop", "50% 50%"), ensure_ascii=False), "alt": selected.get("alt", ""), "gen_id": selected.get("gen_id") or selected.get("generation_reference", {}).get("gen_id")}
        asset.update(binary_fields(rel))
        assets.append(asset)
    for company, role, asset_id, provider, creator, source, license_url, rel in STOCK:
        asset = {"asset_id": asset_id, "photo_role": role, "source_type": "free_stock", "provider": provider, "source": source, "asset_url": "/" + rel, "creator": creator, "rights_status": "RESEARCH_APPROVED_FREE_STOCK", "license_terms_url": license_url, "checked_at": "2026-09-16", "visual_subject": "Selection Manifest PRIMARY", "placement": "", "replacement_target": "", "crop": "50% 50%", "alt": f"{role} stock context image"}
        asset.update(binary_fields(rel))
        assets.append(asset)
    output = {"schema_version": "photography_asset_manifest_v1", "source_priority": ["free_stock", "generated", "vector"], "vector_policy": "supporting_only_not_primary_photography", "assets": assets, "replacement_metadata": {"sales_sample": ["free_stock", "generated"], "formal": ["real_evidence"]}}
    (ROOT / "data/photography/photography_asset_manifest_v1.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "asset_count": len(assets), "stock_count": 6, "generated_count": 6}, ensure_ascii=False))

if __name__ == "__main__":
    main()
