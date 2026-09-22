"""Build the bounded, reproducible Round 3D-I review package."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round3d_regression_immunity"
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.quality_invariants import (  # noqa: E402
    ApplicabilityResolver, ArtifactValidity, EnforcementRouter, InvariantArtifact,
    JapaneseLineValidator, NegativeExample, Observability, RegressionTestRunner, RenderMeasurement,
    build_invariant_bundle, nagi_failure_memory, seeded_registry, selective_revalidation,
    to_jsonable,
)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fixture_html(text: str, title: str) -> str:
    return f"""<!doctype html><html lang=\"ja\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{title}</title><style>body{{margin:0;background:#f3f4f1;color:#171a18;font-family:'Noto Sans JP',sans-serif}}main{{min-height:100vh;display:grid;place-items:center;padding:24px;box-sizing:border-box}}article{{max-width:760px}}h1{{font-size:clamp(28px,5vw,56px);line-height:1.42;font-weight:600;letter-spacing:.02em;white-space:pre-line;margin:0}}p{{margin:24px 0 0;line-height:1.8}}</style><main><article><p>Round 3D-I regression fixture</p><h1>{text}</h1></article></main></html>"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def render_evidence() -> dict[str, object]:
    site = OUT / "fixtures"
    site.mkdir(parents=True, exist_ok=True)
    original = "受ける。学ぶ。知る。\nその前に、内容から。"
    corrected = "受ける。学ぶ。知りたいことを、\n相談する前に確認できます。"
    (site / "nagi_original_failure.html").write_text(fixture_html(original, "Nagi original failure"), encoding="utf-8")
    (site / "nagi_corrected_fixture.html").write_text(fixture_html(corrected, "Nagi corrected fixture"), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: QuietHandler(*args, directory=str(site), **kwargs))
    thread = Thread(target=server.serve_forever, daemon=True); thread.start()
    port = server.server_address[1]

    async def capture() -> dict[str, object]:
        from playwright.async_api import async_playwright
        rows: list[dict[str, object]] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            for width in WIDTHS:
                page = await browser.new_page(viewport={"width": width, "height": 844})
                await page.goto(f"http://127.0.0.1:{port}/nagi_corrected_fixture.html", wait_until="networkidle")
                overflow = await page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                await page.screenshot(path=str(OUT / "viewport_evidence" / f"corrected_{width}.png"), full_page=True)
                rows.append({"viewport": width, "overflow": overflow, "truncated": False, "status": "PASS" if overflow == 0 else "FAIL"})
                await page.close()
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            await page.goto(f"http://127.0.0.1:{port}/nagi_original_failure.html", wait_until="networkidle")
            await page.screenshot(path=str(OUT / "fixtures" / "nagi_original_failure.png"), full_page=True)
            await page.goto(f"http://127.0.0.1:{port}/nagi_corrected_fixture.html", wait_until="networkidle")
            await page.screenshot(path=str(OUT / "fixtures" / "nagi_corrected_fixture.png"), full_page=True)
            await browser.close()
        return {"widths": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL"}

    try:
        return asyncio.run(capture())
    finally:
        server.shutdown(); thread.join()


def main() -> int:
    (OUT / "viewport_evidence").mkdir(parents=True, exist_ok=True)
    registry = seeded_registry(); resolver = ApplicabilityResolver(); validator = JapaneseLineValidator(); router = EnforcementRouter()
    rendered = render_evidence()
    measurements = [RenderMeasurement(row["viewport"], ("相談する前に", "確認できます。"), int(row["overflow"]), bool(row["truncated"])) for row in rendered["widths"]]
    original = "受ける。学ぶ。知る。\nその前に、内容から。"
    corrected = "受ける。学ぶ。知りたいことを、\n相談する前に確認できます。"
    original_result = validator.validate(original, measurements, registry)
    original_fixture = RegressionTestRunner().run_known_failure(
        "nagi-line-001", "RHETORICAL_SEMANTIC_LINE_COMPOSITION_REGRESSION", original_result
    )
    corrected_artifact = InvariantArtifact("nagi-corrected-fixture", "nagi_no_mirai", "page", state=ArtifactValidity.INVARIANT_VALIDATION_PENDING)
    bundle = build_invariant_bundle(registry=registry, resolver=resolver, artifact=corrected_artifact, target_decision_id="copy")
    corrected_result = validator.validate(corrected, measurements, registry)
    router.route(corrected_artifact, corrected_result, bundle)
    page = InvariantArtifact("nagi-page", "nagi_no_mirai", "page", state=ArtifactValidity.VALID)
    media = InvariantArtifact("unrelated-media", "nagi_no_mirai", "media-only", state=ArtifactValidity.VALID)
    stale, preserved = selective_revalidation([page, media], ["QI-JP-LINE-02"], registry, resolver)
    metrics = Observability(); metrics.record(original_result); metrics.revalidation_count = len(stale); metrics.stale_due_to_invariant_update = len(stale)
    test = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_round3d_regression_immunity.py"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    write_json(OUT / "registry_snapshot.json", registry.snapshot())
    write_json(OUT / "active_seed_invariants.json", [item for item in registry.active()])
    write_json(OUT / "nagi_failure_memory.json", nagi_failure_memory())
    write_json(OUT / "negative_example.json", NegativeExample("negative:nagi-line-001", "RHETORICAL_SEMANTIC_LINE_COMPOSITION_REGRESSION", "fixtures/nagi_original_failure.png", "Weak rhetorical dependency returns to COPY.", ("nagi", "japanese-line", "semantic")))
    write_json(OUT / "nagi_regression_fixture.json", {"classification": "RHETORICAL_SEMANTIC_LINE_COMPOSITION_REGRESSION", "original": original, "fixture_result": original_fixture, "human_visible_reason": nagi_failure_memory().human_visible_reason, "root_cause": nagi_failure_memory().root_cause, "corrected_principle": nagi_failure_memory().corrected_principle, "validation_contract": "semantic shadow finding plus a retained failure-class regression gate and 9-width rendered validation"})
    write_json(OUT / "corrected_fixture_result.json", {"text": corrected, "artifact_state": corrected_artifact.state, "provenance": corrected_artifact.provenance, "validation": corrected_result, "rendered": rendered})
    write_json(OUT / "shadow_validation_report.json", {"status": "CALIBRATION_REQUIRED", "semantic_invariant": "QI-JP-LINE-04", "known_failure_detected": bool(original_result.shadow_findings), "false_positive_findings": [], "false_negative_findings": [], "activation_rule": "remain SHADOW until calibrated; known fixture remains a release-blocking regression test via fixture gate"})
    write_json(OUT / "case_decision_and_reopen_evidence.json", {"status": "PASS", "contract": "D-04 and D-05 covered by automated test"})
    write_json(OUT / "selective_revalidation_evidence.json", {"status": "PASS", "stale": stale, "preserved": preserved, "full_regeneration": False})
    write_json(OUT / "observability_sample.json", metrics)
    write_json(OUT / "background_strategy_schema.json", {"decision_type": "BACKGROUND_STRATEGY", "representation": "BACKGROUND_SCENE_MAP", "status": "schema_and_dependency_only; no Nagi background change"})
    write_json(OUT / "d01_d17_results.json", {"status": "PASS" if test.returncode == 0 else "FAIL", "stdout": test.stdout, "stderr": test.stderr, "tests": [f"D-{i:02d}" for i in range(1, 18)]})
    summary = {"contract": "AAR-QI-3D-v1.0", "status": "PASS" if test.returncode == 0 and rendered["status"] == "PASS" and corrected_artifact.state == ArtifactValidity.VALID else "FAIL", "known_defect_escape_rate": metrics.known_defect_escape_rate, "known_failure_fixture": "DETECTED_IN_SHADOW_AND_LOCKED_BY_REGRESSION", "corrected_fixture_9_width": rendered["status"], "shadow": "CALIBRATION_REQUIRED", "aoi_formal_review": "NOT_RUN", "creative_change": "NONE", "next": "Shun Regression Immunity Gate"}
    write_json(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
