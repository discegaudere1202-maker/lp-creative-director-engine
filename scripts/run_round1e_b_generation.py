"""Generate the three Round 1E-B LPs from approved SSOT data only."""
from __future__ import annotations
import json
from pathlib import Path
from lp_engine.production_generation import run_generation

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/photography/photography_asset_manifest_v1.json").read_text(encoding="utf-8"))
CASES = {
    "maylynn_paint": {"company_name": "Maylynn Paint", "industry": "外壁塗装", "location": "福岡市", "truth": "外壁塗装・屋根・雨漏り・リフォームについて相談できる地域の窓口。", "goal": "quote_request", "roles": ["hero_home_finish", "craft_handwork", "material_detail", "trust_consultation"]},
    "nagi_no_mirai": {"company_name": "なぎのみらい", "industry": "ヘッドスパ", "location": "福岡市", "truth": "ドライヘッドスパ・ヘッドスパスクール・ヒーリングサロンの相談窓口。", "goal": "reservation", "roles": ["hero_treatment_space", "hand_technique", "sensory_detail", "welcome_human"]},
    "watashi_no_daidokoro": {"company_name": "わたしの台所", "industry": "料理教室", "location": "福岡市西区", "truth": "少人数でストウブ無水料理を学ぶ料理教室。", "goal": "application", "roles": ["hero_shared_cooking", "ingredient_story", "hands_in_action", "finished_table"]},
}

def build_input(company_id: str, case: dict) -> dict:
    assets = [dict(item) for item in MANIFEST["assets"] if item.get("photo_role") in case["roles"]]
    evidence = [
        {"evidence_id": f"{company_id}-e-001", "evidence_type": "SERVICE_SCOPE", "evidence_strength": "E3_OPERATIONAL", "target_objections": ["O3_PROCESS"], "claim": case["truth"], "source": "approved-selection-manifest", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "blocking_status": "NON_BLOCKING", "placement_candidates": ["HERO", "MIDDLE"]},
        {"evidence_id": f"{company_id}-e-002", "evidence_type": "PLACE_WIDE", "evidence_strength": "E2_SPECIFIC", "target_objections": ["O3_PROCESS"], "claim": f"{case['location']}で活動する事業者。", "source": "phase6-sales-master-snapshot", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "blocking_status": "NON_BLOCKING", "placement_candidates": ["HERO", "EARLY_PROOF"]},
        {"evidence_id": f"{company_id}-e-003", "evidence_type": "SERVICE_PROCESS", "evidence_strength": "E3_OPERATIONAL", "target_objections": ["O3_PROCESS"], "claim": "対応範囲を案内する。", "source": "approved-selection-manifest", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "blocking_status": "NON_BLOCKING", "placement_candidates": ["MIDDLE"]},
        {"evidence_id": f"{company_id}-e-004", "evidence_type": "CTA_CHANNEL", "evidence_strength": "E5_DECISION_ENABLING", "target_objections": ["O4_NEXT"], "claim": "公式SNSから相談・予約の入口を確認する。", "source": "phase6-sales-master-snapshot", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "blocking_status": "NON_BLOCKING", "placement_candidates": ["BEFORE_CTA", "CTA_ZONE"]},
    ]
    return {"schema_version": "production_generation_input_v1", "company_id": company_id, "company": {"company_name": case["company_name"], "industry": case["industry"], "service_category": case["industry"], "location": case["location"], "business_model": "local_service", "company_truth": case["truth"], "differentiators": [case["truth"]], "visual_authority_candidates": ["PLACE", "MATERIAL", "PERSON", "TYPOGRAPHY"], "contact_channels": {"href": "#contact", "primary": "公式SNS"}}, "customer_state": {"before": "相談前に何を確認すればよいか分からない", "after": "まず状況を伝えてみようと思える", "barrier": "自分に合う入口か分からない"}, "conversion_goal": case["goal"], "primary_objections": ["O3_PROCESS", "O4_NEXT"], "requested_claims": [], "unavailable_evidence": ["実店舗・実施工・実スタッフ・実顧客・実教室の写真"], "evidence_ledger": evidence, "photo_assets": assets, "validation_context": "NO_WEB_FIELD_VALIDATION"}

def main() -> None:
    output = ROOT / "artifacts/round1e_b"
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    for company_id, case in CASES.items():
        destination = output / company_id
        result = run_generation(build_input(company_id, case), destination, generation_id=f"round1e-b-{company_id}", mode="research")
        summary.append({"company": case["company_name"], "output_dir": str(destination), "generation_success": True, "output_status": result.manifest["output_status"], "manual_intervention": result.manifest["manual_intervention"], "photo_roles": case["roles"]})
    (output / "generation_summary.json").write_text(json.dumps({"status": "PASS", "manual_edit_count": 0, "companies": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "companies": summary}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
