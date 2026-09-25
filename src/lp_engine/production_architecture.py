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

INFERENCE_OUTPUT_FIELDS = (
    "dominant_family", "secondary_influences", "acceptable_alternatives",
    "prohibited_or_misfit", "ambiguity_state", "human_review_required",
    "customer_decision_job", "fit_dimensions_used",
    "feasibility_ignored_at_selection", "reasoning", "provenance_refs",
)
FEASIBILITY_INPUT_FIELDS = set(FEASIBILITY_DIMENSIONS)

_FAMILY_JOBS = {
    "BW-F01": ("make the desired sensory/experiential state imaginable before dense explanation", {"sensory_experience_weight", "emotional_purchase_weight", "visual_storytelling_need"}),
    "BW-F02": ("reduce wrong-choice/safety anxiety with boundaries, suitability and structured reassurance", {"clinical_expertise", "trust_requirement", "information_density_need", "calmness"}),
    "BW-F03": ("establish aspirational/premium authority while carrying rational support into commitment", {"premium_authority_need", "visual_storytelling_need", "emotional_purchase_weight", "decision_commitment_pressure"}),
    "BW-F04": ("make maker, practitioner, material provenance or craft process indispensable to trust/meaning", {"craftsmanship", "human_relationship_weight", "process_inspectability_need", "intimacy"}),
    "BW-F05": ("route a customer who already accepts the category through ambiguous services/options toward the right fit", {"choice_guidance_need", "information_density_need", "trust_requirement"}),
    "BW-F06": ("prove that a method/mechanism/process is credible and causally capable of producing the desired change", {"process_inspectability_need", "desired_state_change_intensity", "trust_requirement", "clinical_expertise"}),
    "BW-F07": ("make ongoing local/community/human relationship itself a reason to choose", {"local_relationship_weight", "human_relationship_weight", "intimacy", "warmth"}),
    "BW-F08": ("help a low-readiness customer understand the category and self-place before asking for commitment", {"category_education_need", "choice_guidance_need", "information_density_need"}),
}
_COLLISION_RULES = (
    {"id": "C02_C06", "pair": frozenset(("BW-F02", "BW-F06")), "left": ("safety", "suitable", "appropriate", "wrong choice", "risk", "counseling", "condition", "reassurance"), "right": ("mechanism", "measurable", "repeatable", "causal", "evidence", "proof", "visible change"), "left_family": "BW-F02", "right_family": "BW-F06", "left_reason": "safety/suitability reassurance leads", "right_reason": "mechanism efficacy proof leads"},
    {"id": "C05_C08", "pair": frozenset(("BW-F05", "BW-F08")), "left": ("cannot self-select", "self-select", "personalized", "personalised", "recommendation", "routing", "what care is appropriate", "right care"), "right": ("category itself", "category curious", "first-timer", "first timer", "beginner", "understandable", "low commitment", "low-commitment"), "left_family": "BW-F05", "right_family": "BW-F08", "left_reason": "category accepted with option ambiguity", "right_reason": "category/fit understanding precedes option choice"},
    {"id": "C01_C04", "pair": frozenset(("BW-F01", "BW-F04")), "left": ("sensory", "sensory", "ritual", "fragrance", "forest", "scent", "atmosphere", "lifestyle fit", "experience"), "right": ("maker", "material", "provenance", "craft", "technique", "practitioner", "factory", "human maker", "expert hands-on", "method grew"), "left_family": "BW-F01", "right_family": "BW-F04", "left_reason": "experience imagination leads", "right_reason": "provenance/human technique is indispensable"},
    {"id": "C03_C04", "pair": frozenset(("BW-F03", "BW-F04")), "left": ("high-class", "high class", "aspirational", "desired self-image", "premium authority", "specialist authority", "specialist proof", "authorship"), "right": ("maker", "material", "provenance", "craft", "technique", "factory", "human maker"), "left_family": "BW-F03", "right_family": "BW-F04", "left_reason": "aspirational authority leads", "right_reason": "maker/provenance authority leads"},
    {"id": "C04_C07", "pair": frozenset(("BW-F04", "BW-F07")), "left": ("maker", "material", "provenance", "craft", "technique", "practitioner", "method"), "right": ("local", "community", "nearby", "neighborhood", "neighbourhood", "generations", "familiarity", "continuity", "daily life"), "left_family": "BW-F04", "right_family": "BW-F07", "left_reason": "human craft without decision-relevant locality", "right_reason": "ongoing local relationship changes choice"},
    {"id": "C06_C08", "pair": frozenset(("BW-F06", "BW-F08")), "left": ("mechanism", "measurable", "repeatable", "causal", "evidence", "proof", "research", "visible change"), "right": ("category itself", "category curious", "category education", "first-timer", "first timer", "beginner", "understandable", "low commitment", "low-commitment"), "left_family": "BW-F06", "right_family": "BW-F08", "left_reason": "method credibility is the gating question", "right_reason": "category understanding is the gating question"},
)
_TEXT_MARKERS = {
    "BW-F01": ("sensory", "ritual", "fragrance", "forest", "scent", "atmosphere", "lifestyle fit", "experience"),
    "BW-F02": ("safety", "suitable", "appropriate", "wrong choice", "risk", "counseling", "condition", "reassurance"),
    "BW-F03": ("high-class", "high class", "aspirational", "desired self-image", "premium authority", "specialist authority", "specialist proof", "authorship"),
    "BW-F04": ("maker", "material", "provenance", "craft", "technique", "practitioner", "factory", "human maker", "expert hands-on", "method grew"),
    "BW-F05": ("cannot self-select", "self-select", "personalized", "personalised", "recommendation", "routing", "what care is appropriate", "right care"),
    "BW-F06": ("mechanism", "measurable", "repeatable", "causal", "evidence", "research", "visible change"),
    "BW-F07": ("local", "community", "nearby", "neighborhood", "neighbourhood", "generations", "familiarity", "continuity", "daily life"),
    "BW-F08": ("category itself", "category curious", "category education", "first-timer", "first timer", "beginner", "understandable", "low commitment", "low-commitment"),
}


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


def _flatten_truth(company_truth: dict[str, Any], customer_decision_state: Any) -> str:
    values: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            values.append(str(value))
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(company_truth)
    visit(customer_decision_state)
    return " ".join(values).lower()


def _contains_feasibility_key(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(set(value).intersection(FEASIBILITY_INPUT_FIELDS)) or any(_contains_feasibility_key(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_feasibility_key(child) for child in value)
    return False


def _require_inference_inputs(company_truth: dict[str, Any], customer_decision_state: Any, creative_fit: dict[str, Any]) -> dict[str, float]:
    if not isinstance(company_truth, dict) or company_truth.get("verified") is not True:
        raise ValueError("company_truth must be verified before family inference")
    if not isinstance(customer_decision_state, (str, dict)) or not customer_decision_state:
        raise ValueError("customer_decision_state is required for family inference")
    if _contains_feasibility_key(company_truth) or _contains_feasibility_key(customer_decision_state):
        raise ValueError("production feasibility fields are forbidden at inference stage")
    if not isinstance(creative_fit, dict) or set(creative_fit) != {"schema_version", "profile_id", "dimensions", "source_refs"}:
        if isinstance(creative_fit, dict) and FEASIBILITY_INPUT_FIELDS.intersection(creative_fit):
            raise ValueError("production feasibility fields are forbidden at inference stage")
        raise ValueError("inference requires exactly Creative Fit dimensions without a pre-supplied family")
    if creative_fit["schema_version"] != CREATIVE_FIT_SCHEMA:
        raise ValueError("creative fit schema mismatch")
    dimensions = creative_fit["dimensions"]
    if set(dimensions) != set(FIT_DIMENSIONS):
        if FEASIBILITY_INPUT_FIELDS.intersection(dimensions):
            raise ValueError("production feasibility fields are forbidden at inference stage")
        raise ValueError("inference requires exactly the accepted Creative Fit dimensions")
    return {name: _score(value, f"creative fit {name}") for name, value in dimensions.items()}


def _resolve_collision(candidates: set[str], text: str) -> tuple[str | None, str | None, str | None]:
    for rule in _COLLISION_RULES:
        if not rule["pair"].issubset(candidates):
            continue
        left_hit = any(marker in text for marker in rule["left"])
        right_hit = any(marker in text for marker in rule["right"])
        if left_hit and not right_hit:
            return rule["left_family"], rule["id"], rule["left_reason"]
        if right_hit and not left_hit:
            return rule["right_family"], rule["id"], rule["right_reason"]
        return None, rule["id"], "collision remains co-dominant after explicit rule"
    return None, None, None


def infer_creative_family(*, company_truth: dict[str, Any], customer_decision_state: Any, creative_fit: dict[str, Any]) -> dict[str, Any]:
    """Infer a family from verified truth, customer decision job and ordinal fit signals.

    This deliberately returns an ambiguity state instead of pretending expert ordinal
    annotations are calibrated probabilities. It is a pre-validation stage; callers
    freeze the result before passing feasibility to ``select_family``.
    """
    _require_inference_inputs(company_truth, customer_decision_state, creative_fit)
    decision_text = _flatten_truth({}, customer_decision_state)
    truth_text = _flatten_truth(company_truth, {})
    text = decision_text or truth_text
    candidates = {family for family, markers in _TEXT_MARKERS.items() if any(marker in text for marker in markers)}
    dominant, collision_rule, collision_reason = _resolve_collision(candidates, text)
    if dominant is None and len(candidates) == 1:
        dominant = next(iter(candidates))
        collision_reason = "single explicit decision-job family"
    if dominant is None:
        return {
            "dominant_family": None, "secondary_influences": sorted(candidates),
            "acceptable_alternatives": sorted(candidates),
            "prohibited_or_misfit": list(company_truth.get("prohibited_families", [])),
            "ambiguity_state": "CO_DOMINANT_HUMAN_REVIEW", "human_review_required": True,
            "customer_decision_job": "undetermined between competing decision jobs",
            "fit_dimensions_used": list(FIT_DIMENSIONS), "feasibility_ignored_at_selection": True,
            "reasoning": collision_reason or "No explicit decision-job signal resolved the family.",
            "provenance_refs": list(creative_fit["source_refs"]),
            "collision_rule": collision_rule,
        }

    prohibited = list(company_truth.get("prohibited_families", []))
    if dominant in prohibited:
        return {
            "dominant_family": None, "secondary_influences": sorted(candidates - {dominant}),
            "acceptable_alternatives": sorted(candidates - {dominant}),
            "prohibited_or_misfit": prohibited, "ambiguity_state": "PROHIBITED_DOMINANT_HUMAN_REVIEW",
            "human_review_required": True, "customer_decision_job": _FAMILY_JOBS[dominant][0],
            "fit_dimensions_used": list(FIT_DIMENSIONS), "feasibility_ignored_at_selection": True,
            "reasoning": "The explicit decision-job family is prohibited; no silent substitution was made.",
            "provenance_refs": list(creative_fit["source_refs"]), "collision_rule": collision_rule,
        }

    secondary = sorted(candidates - {dominant})
    acceptable = list(secondary)
    job = _FAMILY_JOBS[dominant][0]
    return {
        "dominant_family": dominant,
        "secondary_influences": secondary,
        "acceptable_alternatives": acceptable,
        "prohibited_or_misfit": list(company_truth.get("prohibited_families", [])),
        "ambiguity_state": "EXPLICIT_ALTERNATIVE" if secondary else "RESOLVED",
        "human_review_required": False,
        "customer_decision_job": job,
        "fit_dimensions_used": list(FIT_DIMENSIONS),
        "feasibility_ignored_at_selection": True,
        "reasoning": f"Explicit decision-job rule {collision_rule or 'single-family rule'} identifies {dominant}: {collision_reason or job}.",
        "provenance_refs": list(creative_fit["source_refs"]),
        "collision_rule": collision_rule,
    }


def infer_and_select_family(*, company_truth: dict[str, Any], customer_decision_state: Any, creative_fit: dict[str, Any], feasibility: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Run inference first, then pass a frozen Creative Fit to selection.

    Feasibility is intentionally accepted only by the second stage. An unresolved
    inference is returned for human review and never converted into a guessed family.
    """
    inference = infer_creative_family(
        company_truth=company_truth,
        customer_decision_state=customer_decision_state,
        creative_fit=creative_fit,
    )
    if inference["human_review_required"]:
        return {"inference": inference, "selection": None}
    frozen_fit = {
        "schema_version": CREATIVE_FIT_SCHEMA,
        "profile_id": creative_fit["profile_id"],
        "dimensions": dict(creative_fit["dimensions"]),
        "dominant_family": inference["dominant_family"],
        "secondary_families": list(inference["secondary_influences"]),
        "source_refs": list(inference["provenance_refs"]),
    }
    return {"inference": inference, "selection": select_family(fit=frozen_fit, feasibility=feasibility, candidates=candidates)}


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
