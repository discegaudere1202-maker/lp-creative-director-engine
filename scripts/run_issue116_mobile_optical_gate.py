"""Issue #116 nine-width Hero optical hard gate.

`overflow-x: clip` can hide a headline wider than its authored canvas while
page-level overflow still reports false. This validates every public Hero
meaning unit against the actual H1, Hero canvas, and viewport at all 9 widths.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--premium-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.premium_root).resolve()
    out = Path(args.out).resolve()
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in SAMPLES:
            uri = (root / "cases" / case_id / "index.html").resolve().as_uri()
            for width in WIDTHS:
                context = browser.new_context(viewport={"width": width, "height": 900})
                page = context.new_page()
                page.goto(uri, wait_until="load")
                page.wait_for_load_state("networkidle")
                metrics = page.evaluate(
                    """
                    () => {
                      const h1 = document.querySelector('.premium-hero h1');
                      const units = [...document.querySelectorAll('.premium-headline-unit')];
                      const hero = document.querySelector('.premium-hero');
                      if (!h1 || !hero || units.length === 0) {
                        return {present:false, units:[]};
                      }
                      const h1Rect = h1.getBoundingClientRect();
                      const heroRect = hero.getBoundingClientRect();
                      const viewWidth = document.documentElement.clientWidth;
                      return {
                        present: true,
                        viewport_width: viewWidth,
                        h1_left: h1Rect.left,
                        h1_right: h1Rect.right,
                        hero_left: heroRect.left,
                        hero_right: heroRect.right,
                        units: units.map(node => {
                          const rect = node.getBoundingClientRect();
                          const range = document.createRange();
                          range.selectNodeContents(node);
                          const lineRects = [...range.getClientRects()];
                          return {
                            text: (node.textContent || '').trim(),
                            left: rect.left,
                            right: rect.right,
                            width: rect.width,
                            line_rect_count: lineRects.length,
                            fits_h1: rect.left >= h1Rect.left - 0.75 && rect.right <= h1Rect.right + 0.75,
                            fits_hero: rect.left >= heroRect.left - 0.75 && rect.right <= heroRect.right + 0.75,
                            fits_viewport: rect.left >= -0.75 && rect.right <= viewWidth + 0.75,
                          };
                        }),
                      };
                    }
                    """
                )
                row = {"case_id": case_id, "width": width, **metrics}
                row["pass"] = bool(
                    metrics.get("present")
                    and metrics.get("units")
                    and all(
                        unit["line_rect_count"] == 1
                        and unit["fits_h1"]
                        and unit["fits_hero"]
                        and unit["fits_viewport"]
                        for unit in metrics["units"]
                    )
                )
                rows.append(row)
                if not row["pass"]:
                    failures.append(row)
                context.close()
        browser.close()

    report = {
        "schema_version": "issue116_nine_width_hero_optical_gate_v1",
        "samples": list(SAMPLES),
        "widths": list(WIDTHS),
        "checks": len(rows),
        "failures": failures,
        "all_headline_meaning_units_atomic_and_visible": not failures,
        "reason": "Direct bounding geometry prevents overflow-x:clip from masking Hero semantic-unit clipping at any validation width.",
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "checks": len(rows),
        "failures": len(failures),
        "pass": not failures,
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
