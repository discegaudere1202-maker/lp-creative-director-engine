"""Production Architecture v1 contracts.

This module turns the Issue #44 research proposal into deliberately small,
machine-checkable boundaries.  It is an architecture contract, not a layout
generator: families describe creative decision logic and modules describe
composition/persuasion grammar.  Feasibility is evaluated only after fit.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

CREATIVE_FIT_SCHEMA = "creative_fit_profile_v1"
FEASIBILITY_SCHEMA = "production_feasibility_profile_v1"
SELECTION_SCHEMA = "family_module_selection_contract_v1"
RESEMBLANCE_SCHEMA = "template_resemblance_contract_v0"
PROVENANCE_SCHEMA = "production_architecture_provenance_v1"

FAMILY_IDS = tuple(f"BW-F0{i}" for i in range(1, 9))
FIT_DIMENSIONS = (
    "premium_authority_need", "warmth", "naturalness", "clinical_expertise",
    "craftsmanship", "modernity", "softness", "calmness", "boldness",
    "intimacy", "local_relationship_weight", "desired_state_change_intensity",
    "trust_requirement", "decision_commitment_pressure", "owner_personality_importance",
    "visual_storytelling_need", "information_density_need", "emotional_purchase_weight",
    "category_education_need", "choice_guidance_need", "process_inspectability_need",
    "sensory_experience_weight", "human_relationship_weight",
)
FEASIBILITY_DIMENSIONS = (
    "photo_asset_quantity", "evidence_quantity_available", "scraping_difficulty",
    "source_coverage", "rights_clarity", "staff_photo_availability",
    "facility_photo_availability", "pricing_completeness", "social_proof_availability",
)
RESEMBLANCE_DIMENSIONS = (
    "hero_silhouette", "section_topology", "module_sequence", "dominant_grid",
    "typography_hierarchy", "color_topology", "media_framing", "rhythm",
    "material_grammar", "cta_choreography", "motion_pattern", "screenshot_gestalt",
)


def _require(obj: dict[str, Any], fields: Iterable[str], label: str) -> None:
    missing = sorted(set(fields) - obj.keys())
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _score(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        raise ValueError(f"{label} must be a number between 0 and 1")
    return float(value)


def validate_creative_fit(profile: dict[str, Any]) -> dict[str, Any]:
    _require(profile, ("schema_version", "profile_id", "dimensions", "dominant_family", "secondary_families", "source_refs"), "creative fit")
    if profile["schema_version"] != CREATIVE_FIT_SCHEMA:
        raise ValueError("creative fit schema mismatch")
    if profile["dominant_family"] not in FAMILY_IDS:
        raise ValueError("dominant family must be a taxonomy candidate")
    if not isinstance(profile["secondary_families"], list) or profile["dominant_family"] in profile["secondary_families"]:
        raise ValueError("secondary families must be a distinct list")
    if not set(profile["secondary_families"]).issubset(FAMILY_IDS):
        raise ValueError("unknown secondary family")
    forbidden = set(profile).intersection(FEASIBILITY_DIMENSIONS)
    forbidden.update(set(profile["dimensions"]).intersection(FEASIBILITY_DIMENSIONS))
    if forbidden:
        raise ValueError(f"feasibility leaked into creative fit: {sorted(forbidden)}")
    dimensions = profile["dimensions"]
    if set(dimensions) != set(FIT_DIMENSIONS):
        raise ValueError("creative fit must contain exactly the fit dimensions")
    for name, value in dimensions.items():
        _score(value, f"creative fit {name}")
    if not profile["source_refs"]:
        raise ValueError("creative fit needs deterministic source references")
    return profile


def validate_production_feasibility(profile: dict[str, Any]) -> dict[str, Any]:
    _require(profile, ("schema_version", "profile_id", "dimensions", "adaptation_policy", "source_refs"), "production feasibility")
    if profile["schema_version"] != FEASIBILITY_SCHEMA:
        raise ValueError("production feasibility schema mismatch")
    if set(profile["dimensions"]) != set(FEASIBILITY_DIMENSIONS):
        raise ValueError("production feasibility must contain exactly the feasibility dimensions")
    for name, value in profile["dimensions"].items():
        _score(value, f"production feasibility {name}")
    if "dominant_family" in profile or "creative_fit" in profile:
        raise ValueError("creative fit must not be embedded in feasibility")
    if not isinstance(profile["adaptation_policy"], dict) or profile["adaptation_policy"].get("may_change_family") is not False:
        raise ValueError("feasibility adaptation must explicitly preserve family selection")
    return profile


def select_family(*, fit: dict[str, Any], feasibility: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Select from fit signals, then return feasibility only as adaptation context."""
    validate_creative_fit(fit)
    validate_production_feasibility(feasibility)
    if not candidates:
        raise ValueError("family candidates are required")
    ids = {row.get("family_id") for row in candidates}
    if fit["dominant_family"] not in ids:
        raise ValueError("dominant family is not among selector candidates")
    return {
        "schema_version": SELECTION_SCHEMA,
        "dominant_family": fit["dominant_family"],
        "secondary_families": list(fit["secondary_families"]),
        "candidate_ids": sorted(ids),
        "selection_basis": "creative_fit",
        "feasibility_stage": "post_selection_adaptation",
        "family_change_allowed": False,
        "adaptation_notes": feasibility["adaptation_policy"].get("notes", []),
    }


def validate_selection_contract(selection: dict[str, Any]) -> None:
    _require(selection, ("schema_version", "dominant_family", "secondary_families", "selection_basis", "feasibility_stage", "family_change_allowed"), "family selection")
    if selection["schema_version"] != SELECTION_SCHEMA or selection["selection_basis"] != "creative_fit":
        raise ValueError("family selection must be fit-led")
    if selection["feasibility_stage"] != "post_selection_adaptation" or selection["family_change_allowed"] is not False:
        raise ValueError("feasibility cannot silently change creative family")
    if selection["dominant_family"] not in FAMILY_IDS:
        raise ValueError("unknown selected family")


def validate_resemblance_contract(contract: dict[str, Any]) -> None:
    _require(contract, ("schema_version", "dimensions", "hard_fail_candidates", "human_review_required", "calibration_status", "labeled_pair_basis"), "resemblance")
    if contract["schema_version"] != RESEMBLANCE_SCHEMA:
        raise ValueError("resemblance schema mismatch")
    if set(contract["dimensions"]) != set(RESEMBLANCE_DIMENSIONS):
        raise ValueError("resemblance dimensions are incomplete")
    if contract["human_review_required"] is not True or contract["calibration_status"] != "CANDIDATE_NO_NUMERIC_THRESHOLD":
        raise ValueError("resemblance requires human review and must not invent a threshold")
    if "threshold" in contract or "numeric_threshold" in contract:
        raise ValueError("numeric resemblance threshold is not calibrated")
    if not contract["hard_fail_candidates"]:
        raise ValueError("resemblance hard-fail candidates are required")
    basis = contract["labeled_pair_basis"]
    _require(basis, ("source_artifact", "source_sha256", "pair_count", "class_counts", "classes", "same_template_looking_pairs"), "resemblance labeled-pair basis")
    if basis["source_artifact"] != "artifacts/issue44_riko/closure/template_resemblance_labeled_pairs_v1.json":
        raise ValueError("resemblance labeled-pair source must be the accepted Issue #44 closure artifact")
    if basis["pair_count"] != 24 or sum(basis["class_counts"].values()) != basis["pair_count"]:
        raise ValueError("resemblance labeled-pair basis must contain all 24 pairs")
    if set(basis["class_counts"]) != set(basis["classes"]):
        raise ValueError("resemblance labeled-pair classes are incomplete")
    if basis["same_template_looking_pairs"] != "obvious_same_template_skin_swap":
        raise ValueError("same-template calibration class must be explicit")


def evaluate_resemblance(*, observed: dict[str, Any], token_only_change: bool, human_review: str = "PENDING") -> dict[str, Any]:
    if set(observed) != set(RESEMBLANCE_DIMENSIONS):
        raise ValueError("observed resemblance dimensions are incomplete")
    if token_only_change:
        return {"status": "FAIL", "reason": "TOKEN_ONLY_CHANGE", "human_review": human_review}
    return {"status": "HUMAN_REVIEW_REQUIRED", "reason": "SCREENSHOT_GESTALT_REVIEW", "human_review": human_review}


def validate_provenance(manifest: dict[str, Any]) -> None:
    _require(manifest, ("schema_version", "research_issue", "research_head", "source_artifacts", "contract_versions"), "provenance")
    if manifest["schema_version"] != PROVENANCE_SCHEMA or manifest["research_issue"] != 44:
        raise ValueError("provenance must point to Issue #44 research")
    if len(manifest["research_head"]) != 40 or not manifest["source_artifacts"]:
        raise ValueError("research provenance is incomplete")
    if not all(isinstance(path, str) and path for path in manifest["source_artifacts"]):
        raise ValueError("source artifact paths must be explicit")
    for key in (CREATIVE_FIT_SCHEMA, FEASIBILITY_SCHEMA, SELECTION_SCHEMA, RESEMBLANCE_SCHEMA):
        if manifest["contract_versions"].get(key) is None:
            raise ValueError(f"missing contract version: {key}")


def canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
