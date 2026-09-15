from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


DEFAULT_CONFIG = Path("config/prototype_capture_targets_v1.json")
DEFAULT_OUTPUT = Path("artifacts/prototype_capture")


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
                source = Path(target["path"])
                html = source.read_text(encoding="utf-8")
                source_sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
                for viewport in config["viewports"]:
                    page = browser.new_page(
                        viewport={"width": viewport["width"], "height": viewport["height"]},
                        locale="ja-JP",
                        timezone_id="Asia/Tokyo",
                        device_scale_factor=1,
                    )
                    try:
                        page.set_content(html, wait_until="load")
                        page.wait_for_timeout(int(target.get("wait_ms", 250)))
                        name = viewport["name"]
                        screenshot = output_dir / f"{target['prototype_id']}__{name}.png"
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
                        report["records"].append(
                            {
                                "prototype_id": target["prototype_id"],
                                "frame_role": target["frame_role"],
                                "source_path": str(source),
                                "source_sha256": source_sha,
                                "viewport": viewport,
                                "status": "CAPTURED",
                                "metrics": metrics,
                                "screenshot": screenshot.name,
                                "screenshot_sha256": _sha256(screenshot),
                            }
                        )
                    except Exception as exc:
                        report["records"].append(
                            {
                                "prototype_id": target["prototype_id"],
                                "frame_role": target["frame_role"],
                                "source_path": str(source),
                                "source_sha256": source_sha,
                                "viewport": viewport,
                                "status": "ERROR",
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                    finally:
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
    print(f"Prototype capture: {captured}/{total} viewport records captured")
    return 0 if captured == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
