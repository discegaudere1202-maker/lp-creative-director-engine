from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_CONFIG = Path("config/m3_capture_targets_v1.json")
DEFAULT_OUTPUT = Path("artifacts/m3_capture")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def capture(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path),
        "rule": config.get("rule", ""),
        "records": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for target in config["targets"]:
                benchmark_id = target["benchmark_id"]
                for viewport in config["viewports"]:
                    name = viewport["name"]
                    page = browser.new_page(
                        viewport={"width": viewport["width"], "height": viewport["height"]},
                        locale="ja-JP",
                        timezone_id="Asia/Tokyo",
                        device_scale_factor=1,
                    )
                    record: dict[str, Any] = {
                        "benchmark_id": benchmark_id,
                        "requested_url": target["url"],
                        "viewport": viewport,
                        "status": "ERROR",
                    }
                    try:
                        response = page.goto(
                            target["url"],
                            wait_until="domcontentloaded",
                            timeout=45_000,
                        )
                        page.wait_for_timeout(int(target.get("wait_ms", 3000)))

                        # Capture the live viewport, not a stitched full-page image.
                        # Motion is not force-disabled because M3 evidence should show the
                        # real responsive state; reviewers judge a stable captured moment.
                        screenshot = output_dir / f"{benchmark_id}__{name}.png"
                        page.screenshot(path=str(screenshot), full_page=False)

                        metrics = page.evaluate(
                            """() => ({
                                scrollWidth: document.documentElement.scrollWidth,
                                scrollHeight: document.documentElement.scrollHeight,
                                clientWidth: document.documentElement.clientWidth,
                                clientHeight: document.documentElement.clientHeight,
                                dpr: window.devicePixelRatio
                            })"""
                        )
                        record.update(
                            {
                                "status": "CAPTURED",
                                "http_status": response.status if response else None,
                                "final_url": page.url,
                                "title": page.title(),
                                "metrics": metrics,
                                "screenshot": screenshot.name,
                                "screenshot_sha256": _sha256(screenshot),
                            }
                        )
                    except PlaywrightTimeoutError as exc:
                        record["error"] = f"timeout: {exc}"
                    except Exception as exc:  # evidence capture must report per-target errors
                        record["error"] = f"{type(exc).__name__}: {exc}"
                    finally:
                        report["records"].append(record)
                        page.close()
        finally:
            browser.close()

    (output_dir / "capture_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = capture(args.config, args.output)
    captured = sum(1 for r in report["records"] if r["status"] == "CAPTURED")
    total = len(report["records"])
    print(f"M3 evidence capture: {captured}/{total} viewport records captured")

    # Do not fail the workflow for an individual external-site outage. The report is
    # the evidence and M3 promotion remains a separate visual-review action.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
