"""Validate and annotate the Round 3F-M2E browser evidence for sharing.

This research-only check validates files and recorded measurements; it does
not judge creative quality or mobile art direction.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "mobile_pixel_evidence_round3fm2e"
EXPECTED_CASES = {
    "sanu_2nd_home", "sanu_stay_booking", "yoom_main_lp", "yoom_flowbot",
    "findy_corporate", "findy_recruit", "ai_model_brand", "ai_model_careers",
    "timee_corporate", "timee_recruit_special", "kaiho_bank",
}
LOCAL_ORIGINAL = {
    "archive": "artifacts/mobile_pixel_evidence_round3fm2e.zip",
    "bytes": 31582077,
    "sha256": "8ed1a7a6ac2db31b4f0a9543dedac152f9fa35ceddab23c6303848b4ca836f08",
    "cases": 11, "390px": 11, "375px": 11, "320px": 11,
    "desktop_references": 6, "screenshots": 172,
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def read_json(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path.relative_to(ROOT)}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate() -> dict:
    manifest = read_json(EVIDENCE / "capture_manifest.json")
    summary = read_json(EVIDENCE / "viewport_summary.json")
    limitations = read_json(EVIDENCE / "capture_limitations.json")
    unavailable = json.loads((EVIDENCE / "unavailable_cases.json").read_text(encoding="utf-8"))
    handoff = EVIDENCE / "HANDOFF_FOR_KANADE.md"
    assert handoff.is_file() and handoff.stat().st_size > 0, "Kanade handoff is missing"
    assert manifest.get("case_count") == 11
    manifest_ids = {item["case_id"] for item in manifest["cases"]}
    assert manifest_ids == EXPECTED_CASES, f"Unexpected case IDs: {manifest_ids ^ EXPECTED_CASES}"
    assert summary["attempted_cases"] == summary["successfully_captured_cases"] == 11
    assert all(summary[f"{width}px_count"] == 11 for width in (390, 375, 320))
    assert summary["desktop_reference_count"] == 6
    assert summary["kanade_review_ready"] is True

    viewport_counts = {390: 0, 375: 0, 320: 0}
    desktop_count = 0
    screenshot_count = 0
    case_reports = []
    for case_id in sorted(EXPECTED_CASES):
        case_path = EVIDENCE / case_id / "case_evidence.json"
        case = read_json(case_path)
        assert case.get("case_id") == case_id
        for width in viewport_counts:
            viewport = case["viewports"][str(width)]
            assert viewport.get("page_loaded") == "YES", f"{case_id}: {width}px did not load"
            viewport_counts[width] += 1
            filenames = set(viewport.get("screenshots", []))
            assert f"mobile_{width}_hero.png" in filenames, f"Missing {case_id} {width}px hero"
            assert f"mobile_{width}_ending.png" in filenames, f"Missing {case_id} {width}px ending"
            if width in (390, 375):
                assert f"mobile_{width}_late.png" in filenames, f"Missing {case_id} {width}px late page"
                assert f"mobile_{width}_final_cta.png" in filenames, f"Missing {case_id} {width}px final CTA"
            for filename in filenames:
                image_path = case_path.parent / filename
                assert image_path.is_file(), f"Missing screenshot: {image_path.relative_to(ROOT)}"
                assert image_path.read_bytes()[:8] == PNG_SIGNATURE, f"Invalid PNG: {image_path.relative_to(ROOT)}"
                screenshot_count += 1
        desktop = case.get("desktop_reference") or {}
        if desktop.get("page_loaded") == "YES":
            desktop_count += 1
        for filename in desktop.get("screenshots", []):
            image_path = case_path.parent / filename
            assert image_path.is_file() and image_path.read_bytes()[:8] == PNG_SIGNATURE
            screenshot_count += 1
        case_reports.append({
            "case_id": case_id,
            "mobile_loaded": {str(width): case["viewports"][str(width)]["page_loaded"] for width in viewport_counts},
            "desktop_1440_loaded": desktop.get("page_loaded") == "YES",
            "runtime_error_counts": {str(width): len(case["viewports"][str(width)].get("runtime_errors", [])) for width in viewport_counts},
            "failed_request_counts": {str(width): len(case["viewports"][str(width)].get("failed_requests", [])) for width in viewport_counts},
        })
    assert viewport_counts == {390: 11, 375: 11, 320: 11}
    assert desktop_count == 6
    assert unavailable == [], "One or more cases are marked unavailable"
    assert limitations.get("items"), "Capture limitations must be retained"

    capture_environment = manifest.get("capture_environment", {})
    try:
        local_playwright_version = importlib.metadata.version("playwright")
    except importlib.metadata.PackageNotFoundError:
        local_playwright_version = "NOT_INSTALLED_IN_VALIDATION_ENVIRONMENT"
    environment = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "playwright_python": local_playwright_version,
        "chromium_version": capture_environment.get("chromium", "NOT_RECORDED_BY_CAPTURE_RUNNER"),
        "capture_runner_environment": capture_environment or "NOT_RECORDED_BY_CAPTURE_RUNNER",
    }
    local_counts = {"cases": 11, "390px": 11, "375px": 11, "320px": 11, "desktop_references": 6, "screenshots": 172}
    ci_counts = {"cases": len(manifest_ids), **{f"{width}px": viewport_counts[width] for width in viewport_counts}, "desktop_references": desktop_count, "screenshots": screenshot_count}
    comparison = {key: {"local": value, "ci": ci_counts[key], "same": value == ci_counts[key]} for key, value in local_counts.items()}
    report = {
        "schema_version": "mobile_pixel_distribution_report_v1",
        "status": "PASS",
        "creative_judgment": "NOT_PERFORMED",
        "local_original": LOCAL_ORIGINAL,
        "ci_capture_environment": environment,
        "structural_comparison": comparison,
        "binary_pixel_comparison": "NOT_PERFORMED: the local original archive is not present in the CI runner; public pages can also change between captures.",
        "ci_summary": ci_counts,
        "unavailable_case_count": len(unavailable),
        "capture_limitations": limitations["items"],
        "cases": case_reports,
        "kanade_handoff_file": "HANDOFF_FOR_KANADE.md",
    }
    report_path = EVIDENCE / "distribution_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = []
    for path in sorted(EVIDENCE.rglob("*")):
        if path.is_file() and path.name not in {"distribution_artifact_manifest.json", "distribution_report.json"}:
            files.append({"path": path.relative_to(EVIDENCE).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    dist_manifest = {
        "schema_version": "mobile_pixel_distribution_files_v1",
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "excluded_from_file_hashes": ["distribution_report.json", "distribution_artifact_manifest.json"],
        "files": files,
    }
    (EVIDENCE / "distribution_artifact_manifest.json").write_text(json.dumps(dist_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["artifact_file_count"] = len(files) + 2
    report["artifact_total_bytes"] = dist_manifest["total_bytes"]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
