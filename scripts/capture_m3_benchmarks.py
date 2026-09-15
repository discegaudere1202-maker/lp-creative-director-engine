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


def _focus_target(page: Any, target: dict[str, Any]) -> dict[str, Any]:
    """Move the live viewport to the intended comparison frame when requested.

    Formal blind comparison must compare like-for-like frame roles. A pricing MID
    frame must not silently become a homepage HERO simply because both screenshots
    exist. focus_text is intentionally human-readable and is recorded in evidence.
    """
    focus_text = str(target.get("focus_text") or "").strip()
    if not focus_text:
        return {"requested": False, "status": "TOP", "text": ""}

    info: dict[str, Any] = {
        "requested": True,
        "status": "NOT_FOUND",
        "text": focus_text,
    }
    locator = page.get_by_text(focus_text, exact=False).first
    try:
        locator.wait_for(state="visible", timeout=int(target.get("focus_timeout_ms", 8_000)))
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(350)
        offset = int(target.get("focus_top_offset", 80))
        if offset:
            page.evaluate("offset => window.scrollBy(0, -offset)", offset)
            page.wait_for_timeout(250)
        info["status"] = "FOUND"
        info["box"] = locator.bounding_box()
        info["scroll_y"] = page.evaluate("() => window.scrollY")
    except PlaywrightTimeoutError:
        info["status"] = "NOT_FOUND"
    return info


def capture(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": 2,
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
                frame_role = str(target.get("frame_role") or "UNSPECIFIED")
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
                        "frame_role": frame_role,
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
                        focus = _focus_target(page, target)

                        screenshot = output_dir / f"{benchmark_id}__{name}.png"
                        page.screenshot(path=str(screenshot), full_page=False)

                        metrics = page.evaluate(
                            """() => ({
                                scrollWidth: document.documentElement.scrollWidth,
                                scrollHeight: document.documentElement.scrollHeight,
                                clientWidth: document.documentElement.clientWidth,
                                clientHeight: document.documentElement.clientHeight,
                                scrollY: window.scrollY,
                                dpr: window.devicePixelRatio
                            })"""
                        )
                        record.update(
                            {
                                "status": "CAPTURED",
                                "http_status": response.status if response else None,
                                "final_url": page.url,
                                "title": page.title(),
                                "focus": focus,
                                "metrics": metrics,
                                "screenshot": screenshot.name,
                                "screenshot_sha256": _sha256(screenshot),
                            }
                        )
                    except PlaywrightTimeoutError as exc:
                        record["error"] = f"timeout: {exc}"
                    except Exception as exc:
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
    focused = sum(
        1
        for r in report["records"]
        if r.get("focus", {}).get("requested") and r.get("focus", {}).get("status") == "FOUND"
    )
    print(f"M3 evidence capture: {captured}/{total} viewport records captured; {focused} focused frames found")

    # External outages and locator drift are evidence, not reasons to counterfeit M3.
    # The workflow remains successful so the artifact can be inspected and held.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
