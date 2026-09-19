"""Round 2G-B4: close the Maylynn Hero visual relationship defect."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_round2g_b2_direction_fidelity_motion as b3

STARTING_HEAD = "2dabc7f840d09992d3f775b5a85c84de75c8fd5f"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    result = b3.main()
    if result != 0:
        return result
    out = b3.OUT
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    source_head = summary["source_head"]
    review = out / "hero_review"
    review.mkdir(parents=True, exist_ok=True)
    before = ROOT / "artifacts" / "round2f_b2" / "captures" / "desktop_V01.png"
    after_desktop = out / "captures" / "desktop_V01.png"
    after_mobile = out / "captures" / "mobile_V01.png"
    if not all(path.is_file() for path in (before, after_desktop, after_mobile)):
        return 1
    shutil.copy2(before, review / "before_hero.png")
    shutil.copy2(after_desktop, review / "after_hero_1440.png")
    shutil.copy2(after_mobile, review / "after_hero_390.png")
    relation = summary["hero_visual_relationship"]
    visual_artifact = {
        "schema_version": "round2g_b4_hero_visual_relationship_v1",
        "starting_head": STARTING_HEAD,
        "source_head": source_head,
        "root_cause": "A03 was presented as a zoom-like inset beside distinct asset A01 without a semantic relationship contract.",
        "final_relation": relation["relation_type"],
        "before": "hero_review/before_hero.png",
        "after": ["hero_review/after_hero_1440.png", "hero_review/after_hero_390.png"],
        "contract": relation["contract"],
        "validation": relation,
        "human_review_required": True,
    }
    write(review / "visual_relationship_manifest.json", visual_artifact)
    regression = {
        "status": "PASS" if summary["status"] == "PASS" else "FAIL",
        "unchanged_contracts": [
            "hero_full_bleed", "hero_copy", "V02_contact_sheet", "V03_full_screen_documentary",
            "ground_to_drone", "living_side_copy", "typography", "mobile", "evidence_safety",
        ],
        "changed_contract": "hero_visual_relationship_only",
    }
    write(out / "reports" / "round2g_b4_regression.json", regression)
    artifact = {
        "name": f"round2g-b4-hero-visual-relationship-{source_head}",
        "source_head": source_head,
        "includes": [
            "hero_review/before_hero.png", "hero_review/after_hero_1440.png", "hero_review/after_hero_390.png",
            "hero_review/visual_relationship_manifest.json", "reports/visual_relationship_qa.json",
            "reports/round2g_b4_regression.json", "maylynn_field_documentary/index.html",
            "human_review_html/index.html", "captures/", "motion/", "motion_evidence/", "summary.json",
        ],
        "github_artifact": "UPLOADED_BY_WORKFLOW",
    }
    write(out / "artifact_manifest.json", artifact)
    final = {
        "schema_version": "round2g_b4_hero_visual_relationship_v1",
        "status": "PASS" if summary["status"] == "PASS" and relation["status"] == "PASS" else "HOLD",
        "round": "2G-B4",
        "starting_head": STARTING_HEAD,
        "source_head": source_head,
        "root_cause": visual_artifact["root_cause"],
        "final_maylynn_relation": relation["relation_type"],
        "visual_relationship_contract": relation,
        "general_engine_rule": "co-visible media requires relation_type; CROP_FROM_MASTER is fail-closed; secondary media requires narrative_function",
        "before": visual_artifact["before"],
        "after": visual_artifact["after"],
        "regression": regression,
        "qa": summary["qa"],
        "captures": summary["captures"],
        "artifact": artifact,
        "machine_technical_ready": "YES" if summary["status"] == "PASS" else "NO",
        "human_review_required": True,
        "manual_lp_edit": 0,
        "nagi_no_mirai": "NOT_STARTED",
        "watashi_no_daidokoro": "NOT_STARTED",
        "one_million_yen_gate": "NOT_ASSESSED",
    }
    write(out / "summary.json", final)
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0 if final["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
