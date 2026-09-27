"""Issue #116 nine-width public display-heading semantic optical hard gate.

Aoi Human-visible QA found mid-word / mid-meaning-unit breaks outside Hero that
page-level overflow checks and the original Hero-only gate could not detect.
This gate validates Hero, every public chapter/display H2, and the final CTA
across all nine samples and nine required widths.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
PROTECTED_UNITS = ("から", "次へ", "ここから", "違い", "情報", "ポイント")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--premium-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.premium_root).resolve()
    out = Path(args.out).resolve()
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    heading_checks = 0

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
                    (protectedUnits) => {
                      const viewWidth = document.documentElement.clientWidth;
                      const specs = [
                        {kind:'hero', selector:'.premium-hero h1', unitSelector:'.premium-headline-unit', requireAuthored:false},
                        {kind:'display', selector:'.offer-guide h2, .scene-copy h2, .premium-closing h2', unitSelector:'.premium-display-unit', requireAuthored:true},
                      ];
                      const headings = [];
                      for (const spec of specs) {
                        const nodes = [...document.querySelectorAll(spec.selector)];
                        for (const node of nodes) {
                          const parentRect = node.getBoundingClientRect();
                          const units = [...node.querySelectorAll(spec.unitSelector)].map(unit => {
                            const rect = unit.getBoundingClientRect();
                            const range = document.createRange();
                            range.selectNodeContents(unit);
                            const lineRects = [...range.getClientRects()];
                            return {
                              text:(unit.textContent || '').trim(),
                              left:rect.left,
                              right:rect.right,
                              width:rect.width,
                              line_rect_count:lineRects.length,
                              fits_parent:rect.left >= parentRect.left - 0.75 && rect.right <= parentRect.right + 0.75,
                              fits_viewport:rect.left >= -0.75 && rect.right <= viewWidth + 0.75,
                            };
                          });
                          const text = (node.textContent || '').trim();
                          const protected = protectedUnits
                            .filter(token => text.includes(token))
                            .map(token => ({token, contained_in_one_unit:units.some(unit => unit.text.includes(token))}));
                          headings.push({
                            kind:spec.kind,
                            text,
                            authored_marker:node.dataset.semanticHeading || null,
                            require_authored_marker:spec.requireAuthored,
                            units,
                            protected,
                          });
                        }
                      }
                      return {viewport_width:viewWidth, headings};
                    }
                    """,
                    list(PROTECTED_UNITS),
                )
                page_failures = []
                for heading in metrics.get("headings", []):
                    heading_checks += 1
                    units = heading.get("units") or []
                    heading_pass = bool(
                        units
                        and (not heading.get("require_authored_marker") or heading.get("authored_marker") == "authored")
                        and all(
                            unit["line_rect_count"] == 1
                            and unit["fits_parent"]
                            and unit["fits_viewport"]
                            for unit in units
                        )
                        and all(item["contained_in_one_unit"] for item in heading.get("protected", []))
                    )
                    heading["pass"] = heading_pass
                    if not heading_pass:
                        page_failures.append(heading)
                row = {
                    "case_id": case_id,
                    "width": width,
                    **metrics,
                    "heading_count": len(metrics.get("headings", [])),
                    "heading_failures": page_failures,
                    "pass": bool(metrics.get("headings")) and not page_failures,
                }
                rows.append(row)
                if not row["pass"]:
                    failures.append(row)
                context.close()
        browser.close()

    report = {
        "schema_version": "issue116_nine_width_public_display_heading_semantic_gate_v2",
        "samples": list(SAMPLES),
        "widths": list(WIDTHS),
        "page_checks": len(rows),
        "heading_checks": heading_checks,
        "failures": failures,
        "protected_units": list(PROTECTED_UNITS),
        "all_public_display_heading_meaning_units_atomic_and_visible": not failures,
        "scope": ["hero_h1", "offer_guide_h2", "all_scene_h2", "final_cta_h2"],
        "reason": "Direct per-heading/per-unit geometry plus protected-token containment prevents overflow clipping and mid-meaning-unit Japanese breaks across the complete responsive matrix.",
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "page_checks": len(rows),
        "heading_checks": heading_checks,
        "failures": len(failures),
        "pass": not failures,
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
