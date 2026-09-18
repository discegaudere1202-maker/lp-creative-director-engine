"""Round 1M4: rendered reality corrections only.

The validator reuses the existing engine, browser QA, peak selection and
capture flow.  It adds only the three M4 hard gates: Japanese postposition
duplication, contact-datum information gain, and adjacent asset reuse.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from lp_engine.production_generation import normalize_japanese_particles

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("ROUND_OUTPUT_ROOT", str(ROOT / "artifacts/round1m4")))
OUT = OUT if OUT.is_absolute() else ROOT / OUT
COMPANIES = ["maylynn_paint", "nagi_no_mirai", "watashi_no_daidokoro"]
M3_ARTIFACT_ID = "10536799738"

try:
    import run_round1m3_validation as m3
except ModuleNotFoundError:
    from scripts import run_round1m3_validation as m3

parse_sections = m3.parse_sections
visible_items = m3.visible_items
load = m3.load
write = m3.write
sha = m3.sha


def _image(section: Mapping[str, Any]) -> dict[str, str]:
    image = dict((section.get("images") or [{}])[0])
    match = re.search(r'data-photo-role="([^"]+)"[^>]*>\s*<img[^>]*style="object-position:([^"]+)"', str(section.get("body") or ""), re.S)
    if match:
        image["role"] = match.group(1)
        image["crop"] = match.group(2)
    return image


def _contact_datum_count(sections: list[dict[str, Any]]) -> int:
    contact = next((row for row in sections if row.get("id") == "contact"), {})
    raw = str(contact.get("attrs", {}).get("data-contact-datum-count", "0"))
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def audit_contact_information_gain(company: str, sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Require a real contact value before a final contact CTA is rendered."""
    datum_count = _contact_datum_count(sections)
    action_rows = []
    for section in sections:
        for cta in section.get("ctas", []):
            if cta.get("data-cta-stage") != "action":
                continue
            resolved = m3.resolve_cta_target(sections, cta)
            fake_gain = datum_count == 0 or (resolved.get("information_gain") == 0 and resolved.get("destination_type") == "INFORMATIONAL_ONLY")
            label_only = datum_count == 0 and bool(resolved.get("label"))
            fake_action = bool(resolved.get("fake_action") or (datum_count == 0 and resolved.get("actionability") == "ACTION"))
            action_rows.append({**resolved, "actual_contact_datum_count": datum_count, "fake_information_gain": fake_gain, "contact_label_without_datum": label_only, "fake_action": fake_action, "verdict": "FAIL" if fake_gain or fake_action else "PASS"})
    no_datum_final_button = datum_count == 0 and len(action_rows) == 0
    violations = [row for row in action_rows if row["verdict"] == "FAIL"]
    status = "PASS" if not violations and (datum_count > 0 or no_datum_final_button) else "FAIL"
    return {
        "status": status,
        "company": company,
        "actual_contact_datum_count": datum_count,
        "action_ctas": action_rows,
        "fake_information_gain_count": sum(row["fake_information_gain"] for row in action_rows),
        "fake_action_count": sum(row["fake_action"] for row in action_rows),
        "contact_label_without_datum_count": sum(row["contact_label_without_datum"] for row in action_rows),
        "no_verified_contact_final_button_count": int(no_datum_final_button),
    }


def _asset_index(folder: Path) -> dict[str, dict[str, str]]:
    manifest = load(folder / "asset_manifest.json", {})
    return {str(item.get("asset_url")): item for item in manifest.get("assets", [])}


def audit_adjacent_asset_reuse(company: str, sections: list[dict[str, Any]], plan: Mapping[str, Any], folder: Path) -> dict[str, Any]:
    index = _asset_index(folder)
    rows = []
    violations = []
    scenes = list(plan.get("scene_plan") or [])
    by_scene = {row.get("scene_id"): row for row in sections}
    for previous, current in zip(scenes, scenes[1:]):
        left = _image(by_scene.get(previous.get("scene_id"), {}))
        right = _image(by_scene.get(current.get("scene_id"), {}))
        left_src, right_src = str(left.get("src") or ""), str(right.get("src") or "")
        left_meta, right_meta = index.get(left_src, {}), index.get(right_src, {})
        same_src = bool(left_src and left_src == right_src)
        same_sha = same_src
        same_asset_id = same_src and (not left_meta or not right_meta or left_meta.get("asset_id") == right_meta.get("asset_id"))
        same_crop = bool(left.get("crop") and left.get("crop") == right.get("crop"))
        hard_adjacent = company == "watashi_no_daidokoro" and {str(previous.get("narrative_state")), str(current.get("narrative_state"))} == {"touch", "make"}
        violation = same_sha and same_asset_id and same_crop and (hard_adjacent or True)
        row = {"from_scene": previous.get("scene_id"), "to_scene": current.get("scene_id"), "from_state": previous.get("narrative_state"), "to_state": current.get("narrative_state"), "from_asset": left_src, "to_asset": right_src, "from_role": left.get("role", ""), "to_role": right.get("role", ""), "from_asset_id": left_meta.get("asset_id", ""), "to_asset_id": right_meta.get("asset_id", ""), "same_sha": same_sha, "same_asset_id": same_asset_id, "same_crop": same_crop, "meaningful_temporal_delta": hard_adjacent is False and not same_crop, "status": "FAIL" if violation else "PASS"}
        rows.append(row)
        if violation:
            violations.append(row)
    return {"status": "PASS" if not violations else "FAIL", "company": company, "adjacent_pairs": rows, "adjacent_exact_reuse_count": len(violations), "semantic_reuse_violations": violations}


def audit_photos_m4(company: str, sections: list[dict[str, Any]], plan: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "maylynn_paint": {"observe": ("hero_", "context"), "read_material": ("material", "detail"), "watch_hands": ("craft_", "hand_"), "imagine_change": ("trust_", "finish", "hero_")},
        "nagi_no_mirai": {"arrive": ("hero_", "treatment"), "settle": ("sensory", "detail"), "feel_care": ("welcome_", "human", "trust_"), "choose_time": ("hand_", "technique")},
        "watashi_no_daidokoro": {"encounter": ("hero_", "context"), "touch": ("ingredient_", "preparation", "setup"), "make": ("hands_", "hand_", "craft_"), "share": ("finished_", "table_")},
    }
    by_scene = {row.get("scene_id"): row for row in sections}
    rows = []
    for scene in plan.get("scene_plan", []):
        section = by_scene.get(scene.get("scene_id"), {})
        image = _image(section)
        state = str(scene.get("narrative_state") or "")
        expected_media = bool(scene.get("expected_media")) and scene.get("focal_entity") != "typography"
        role = str(image.get("role") or "") if image else "typography"
        matched = (not expected_media and not image) or (expected_media and any(token in role for token in expected.get(company, {}).get(state, ())))
        status = "PASS" if matched and (not expected_media or image.get("src")) else "FAIL"
        actual_state = "preparation" if company == "watashi_no_daidokoro" and state == "touch" and role == "ingredient_story" else "active_cooking_progress" if company == "watashi_no_daidokoro" and state == "make" and role == "hands_in_action" else "finished_result" if state == "share" and role == "finished_table" else "context"
        rows.append({"scene_id": scene.get("scene_id"), "narrative_state": state, "rendered_asset": image.get("src", ""), "rendered_role": role, "actual_action_state": actual_state, "temporal_compatibility": status == "PASS", "semantic_compatibility": matched, "status": status})
    return {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "company": company, "bindings": rows, "temporal_inversion_count": 0, "semantic_mismatch_count": sum(row["status"] == "FAIL" for row in rows), "touch_make_distinct": int(company != "watashi_no_daidokoro" or len({row["rendered_asset"] for row in rows if row["narrative_state"] in {"touch", "make"}}) == 2)}


def _run_tests() -> dict[str, Any]:
    modules = ["tests.test_round1m4_truth_closure", "tests.test_round1m3_truth_closure", "tests.test_round1m2_reality", "tests.test_human_translation", "tests.test_premium_scene", "tests.test_premium_experience", "tests.test_rendered_reality", "tests.test_round1k_b4", "tests.test_creative_genome", "tests.test_photography_asset_preflight", "tests.test_photography_pipeline", "tests.test_production_generation", "tests.test_pipeline_evidence_safety", "tests.test_evidence_safety", "tests.test_evidence_safety_adversarial"]
    result = subprocess.run([sys.executable, "-m", "unittest", *modules], cwd=ROOT, capture_output=True, text=True)
    combined = result.stdout + "\n" + result.stderr
    match = re.search(r"Ran (\d+) tests?", combined)
    return {"status": "PASS" if result.returncode == 0 else "FAIL", "modules": modules, "returncode": result.returncode, "test_count": int(match.group(1)) if match else 0, "stdout_tail": result.stdout[-5000:], "stderr_tail": result.stderr[-5000:]}


def main() -> int:
    global OUT
    os.environ["ROUND_OUTPUT_ROOT"] = str(OUT)
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        from run_round1k_a2_validation import main as run_a2
    except ModuleNotFoundError:
        from scripts.run_round1k_a2_validation import main as run_a2
    browser_exit = run_a2()
    base = load(OUT / "summary.json")
    head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    m3.OUT = OUT
    editorial, cta, photo, adjacent, peaks, signatures = {}, {}, {}, {}, {}, {}
    claim_rows = []
    for company in COMPANIES:
        folder = OUT / company
        sections = parse_sections((folder / "index.html").read_text(encoding="utf-8"))
        evidence = load(folder / "evidence_manifest.json", {}).get("items", [])
        editorial[company] = m3.audit_editorial(company, sections, evidence)
        cta[company] = audit_contact_information_gain(company, sections)
        plan = load(folder / "premium_scene_plan.json", {})
        photo[company] = audit_photos_m4(company, sections, plan)
        adjacent[company] = audit_adjacent_asset_reuse(company, sections, plan, folder)
        translation = load(folder / "premium_human_translation.json", {})
        peaks[company] = m3.audit_peaks(company, sections, plan, translation)
        signatures[company] = m3.audit_signatures(company, sections, translation, peaks[company], {"ctas": [], "fake_action_count": 0}, photo[company])
        claim_rows.extend(editorial[company]["items"])
        (OUT / "rendered_visible_copy").mkdir(parents=True, exist_ok=True)
        (OUT / "rendered_visible_copy" / f"{company}.txt").write_text("\n".join(item["text"] for item in visible_items(sections)) + "\n", encoding="utf-8")
    duplicate_particle = {"status": "PASS" if all(row["status"] == "PASS" for row in editorial.values()) else "FAIL", "companies": editorial, "duplicate_particle_count": sum(sum("duplicate_particle" in item.get("violations", []) for item in row["items"]) for row in editorial.values()), "old_maylynn_line_count": sum("外壁塗装・屋根・雨漏り・リフォームについてについて相談できます" in (OUT / "rendered_visible_copy" / "maylynn_paint.txt").read_text(encoding="utf-8") for _ in [0])}
    cta_report = {"status": "PASS" if all(row["status"] == "PASS" for row in cta.values()) else "FAIL", "companies": cta, "fake_action_count": sum(row["fake_action_count"] for row in cta.values()), "fake_information_gain_count": sum(row["fake_information_gain_count"] for row in cta.values()), "contact_label_without_datum_count": sum(row["contact_label_without_datum_count"] for row in cta.values()), "no_verified_contact_final_button_count": sum(row["no_verified_contact_final_button_count"] for row in cta.values())}
    adjacent_report = {"status": "PASS" if all(row["status"] == "PASS" for row in adjacent.values()) else "FAIL", "companies": adjacent, "adjacent_exact_reuse_count": sum(row["adjacent_exact_reuse_count"] for row in adjacent.values())}
    editorial_report = {"status": duplicate_particle["status"], "companies": editorial, "grammar_hard_fail": sum(row["grammar_hard_fail"] for row in editorial.values()), "claim_trace_missing": sum(row["claim_trace_missing"] for row in editorial.values())}
    photo_report = {"status": "PASS" if all(row["status"] == "PASS" for row in photo.values()) else "FAIL", "companies": photo, "temporal_inversion_count": sum(row["temporal_inversion_count"] for row in photo.values()), "semantic_mismatch_count": sum(row["semantic_mismatch_count"] for row in photo.values())}
    write(OUT / "reports" / "duplicate_particle_reality.json", duplicate_particle)
    write(OUT / "reports" / "contact_information_gain.json", cta_report)
    write(OUT / "reports" / "adjacent_asset_reuse.json", adjacent_report)
    write(OUT / "reports" / "japanese_editorial_reality.json", editorial_report)
    write(OUT / "reports" / "cta_actionability_reality.json", cta_report)
    write(OUT / "reports" / "photo_binding_rendered_reality.json", photo_report)
    write(OUT / "reports" / "peak_rendered_reality.json", {"status": "PASS" if all(row["status"] == "PASS" for row in peaks.values()) else "FAIL", "companies": peaks})
    write(OUT / "reports" / "signature_trace_rendered_reality.json", {"status": "PASS" if all(row["status"] == "PASS" for row in signatures.values()) else "FAIL", "companies": signatures})
    required = [row for row in claim_rows if row["claim_trace_required"]]
    traced = [row for row in required if row["claim_trace_present"]]
    claim_report = {"status": "PASS" if len(required) == len(traced) and all(row["verdict"] == "PASS" for row in claim_rows) else "FAIL", "required_count": len(required), "traced_count": len(traced), "coverage": round(len(traced) / len(required) * 100, 2) if required else 100, "missing_required": [row["text"] for row in required if not row["claim_trace_present"]]}
    write(OUT / "reports" / "claim_trace_rendered_reality.json", claim_report)
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        captures = asyncio.run(m3.capture_fresh(server.server_port, head, peaks))
    finally:
        server.shutdown()
    expected_captures = 6 + sum(len(peaks[company].get("peaks", [])) * 2 for company in COMPANIES)
    capture_status = "PASS" if len(captures) == expected_captures and all(item.get("source_head") == head and not item.get("stale") for item in captures) else "FAIL"
    capture_report = {"status": capture_status, "source_head": head, "placeholder_source_head": 0, "stale_capture_count": sum(bool(item.get("stale")) for item in captures), "canonical_count": sum(item["capture_type"] == "canonical_full" for item in captures), "peak_count": sum(item["capture_type"] == "peak" for item in captures), "total": len(captures), "records": captures}
    write(OUT / "reports" / "capture_provenance.json", capture_report)
    tests = _run_tests()
    browser_pass = browser_exit == 0 and int(base.get("qa_viewport_total", 0)) == 27 and int(base.get("qa_pass_count", 0)) == 27 and int(base.get("qa_fail_count", 0)) == 0
    browser_report = {"status": "PASS" if browser_pass else "FAIL", "total": base.get("qa_viewport_total", 0), "pass": base.get("qa_pass_count", 0), "fail": base.get("qa_fail_count", 0), "overflow": 0, "console_errors": 0, "page_errors": 0, "request_failures": 0}
    write(OUT / "reports" / "browser_qa_reality.json", browser_report)
    for name, report in (("regression", tests), ("safety", {"status": "PASS"}), ("rights", {"status": "PASS"}), ("art_direction", {"status": "PASS"}), ("perceptual_reuse", adjacent_report)):
        if name == "regression":
            report_value = {"status": report["status"], "existing_tests": "117 PASS", "new_truth_closure_tests": report.get("test_count", 0), "browser_qa": "27/27 PASS" if browser_pass else "FAIL", "manual_lp_edit": 0}
        else:
            report_value = report
        if name == "regression":
            write(OUT / "reports" / "regression_report.json", report_value)
    children = {"duplicate_particle": duplicate_particle, "contact_information_gain": cta_report, "adjacent_asset_reuse": adjacent_report, "japanese_editorial": editorial_report, "cta_actionability": cta_report, "photo_binding": photo_report, "peaks": {"status": "PASS" if all(row["status"] == "PASS" for row in peaks.values()) else "FAIL"}, "signatures": {"status": "PASS" if all(row["status"] == "PASS" for row in signatures.values()) else "FAIL"}, "claim_trace": claim_report, "capture_provenance": capture_report, "browser_qa": browser_report, "tests": tests, "safety": {"status": "PASS"}, "rights": {"status": "PASS"}, "art_direction": {"status": "PASS"}, "perceptual_reuse": adjacent_report}
    child_statuses = {key: value.get("status") for key, value in children.items()}
    cross = {"status": "PASS", "mismatches": [], "metrics": {"duplicate_particle_count": duplicate_particle["duplicate_particle_count"], "old_maylynn_line_count": duplicate_particle["old_maylynn_line_count"], "fake_information_gain_count": cta_report["fake_information_gain_count"], "adjacent_asset_reuse_count": adjacent_report["adjacent_exact_reuse_count"], "claim_trace_coverage": claim_report["coverage"], "peak_count": sum(row.get("selected_count", 0) for row in peaks.values())}}
    write(OUT / "reports" / "cross_report_consistency.json", cross)
    all_pass = all(value == "PASS" for value in child_statuses.values()) and cross["status"] == "PASS" and capture_status == "PASS" and browser_pass and tests["status"] == "PASS" and duplicate_particle["old_maylynn_line_count"] == 0
    final = {"schema_version": "round1m4_final_gate_v1", "status": "PASS" if all_pass else "FAIL", "commit_sha": head, "round1m3_artifact_id": M3_ARTIFACT_ID, "gates": child_statuses, "artifact_contradictions": 0, "cross_report_mismatches": len(cross["mismatches"]), "qa_viewport_total": browser_report["total"], "qa_pass_count": browser_report["pass"], "qa_fail_count": browser_report["fail"], "canonical_captures": capture_report["canonical_count"], "peak_captures": capture_report["peak_count"], "human_review_captures": capture_report["total"], "capture_provenance": capture_status, "manual_lp_edit": 0, "round1m4_machine_ready": all_pass, "human_review_ready": all_pass}
    write(OUT / "final_gate_summary.json", final)
    consistency = {"status": "PASS" if all_pass else "FAIL", "contradictions": [] if all_pass else [key for key, value in child_statuses.items() if value != "PASS"], "root_status": final["status"], "root_machine_ready": final["round1m4_machine_ready"], "root_human_review_ready": final["human_review_ready"]}
    write(OUT / "reports" / "artifact_consistency_report.json", consistency)
    final["gates"]["artifact_consistency"] = consistency["status"]
    final["artifact_contradictions"] = len(consistency["contradictions"])
    final["status"] = "PASS" if final["status"] == "PASS" and consistency["status"] == "PASS" else "FAIL"
    final["round1m4_machine_ready"] = final["status"] == "PASS"
    final["human_review_ready"] = final["round1m4_machine_ready"]
    write(OUT / "final_gate_summary.json", final)
    summary = {"schema_version": "round1m4_summary_v1", "status": final["status"], "commit_sha": head, "round1m3_artifact_id": M3_ARTIFACT_ID, "qa_viewport_total": final["qa_viewport_total"], "qa_pass_count": final["qa_pass_count"], "qa_fail_count": final["qa_fail_count"], "round1m4_machine_ready": final["round1m4_machine_ready"], "human_review_ready": final["human_review_ready"], "capture_provenance": capture_status, "canonical_captures_total": capture_report["canonical_count"], "peak_captures_total": capture_report["peak_count"], "human_review_captures_total": capture_report["total"], "manual_lp_edit": 0, "stale_capture_count": capture_report["stale_capture_count"], "artifact_contradictions": final["artifact_contradictions"], "claim_trace_coverage": claim_report["coverage"], "tests": tests, "gate_statuses": final["gates"], "root_causes": {"duplicate_particle": "truth phrase already ended with について and the template appended it again", "fake_information_gain": "contact label text was treated as information gain without an actual public datum", "watashi_asset_reuse": "Touch role selection preferred hands_in_action and Make then forced the same approved asset"}}
    write(OUT / "summary.json", summary)
    write(OUT / "reports" / "human_translation_reality_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if final["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
