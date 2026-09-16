"""QA contract for generated Production outputs.

When Playwright is installed, this command also runs the existing real-browser
QA at all required widths.  ``--static-only`` is intended for environments
without browser dependencies and never claims visual QA passed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

DEFAULT_WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]


FORBIDDEN_UNSUPPORTED = (
    "無理な勧誘", "秘密厳守", "完全無料", "No.1", "満足度", "全額返金", "保証",
    "決めきらなくても", "決めてからでなく", "まとまっていなくても",
)


def static_report(output_dir: Path, *, allow_non_production: bool = False) -> dict:
    manifest = json.loads((output_dir / "generation_manifest.json").read_text(encoding="utf-8"))
    html = (output_dir / "index.html").read_text(encoding="utf-8")
    approved_ids = {str(item["evidence_id"]) for item in manifest.get("evidence_used", [])}
    referenced_ids = set(re.findall(r"(?:andy|[a-z0-9_-]+)-e-[a-z0-9_-]+", html))
    issues = []
    expected_status = "NOT_PRODUCTION_APPROVED" if allow_non_production else "PRODUCTION_APPROVED"
    if manifest.get("output_status") != expected_status:
        issues.append(f"output status must be {expected_status}")
    if manifest.get("manual_intervention") != []:
        issues.append("manual intervention is not empty")
    if not approved_ids:
        issues.append("no Safety-approved evidence is traceable")
    if not referenced_ids.issubset(approved_ids):
        issues.append("HTML references an evidence id not present in the approved manifest")
    if any(marker in html for marker in FORBIDDEN_UNSUPPORTED):
        issues.append("unsupported reassurance or guarantee marker found")
    if html.count('data-role=') != 5:
        issues.append("expected five generated sections")
    if "@media (max-width:760px)" not in html:
        issues.append("mobile re-art media rule missing")
    return {
        "mode": "static_only",
        "allow_non_production": allow_non_production,
        "required_widths": DEFAULT_WIDTHS,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "manual_intervention": manifest.get("manual_intervention", []),
        "approved_evidence_ids": sorted(approved_ids),
        "html_bytes": len(html.encode("utf-8")),
        "exact_capture": {"desktop": "1440x1000_pending_browser_qa", "mobile": "390x844_pending_browser_qa"},
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument("--out")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument(
        "--allow-non-production",
        action="store_true",
        help="Explicit TEST_ONLY/Research QA mode; never approves a production output.",
    )
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    report = static_report(output_dir, allow_non_production=args.allow_non_production)
    if not args.static_only:
        from lp_engine.browser_qa import run_browser_qa_sync
        browser = run_browser_qa_sync(
            str(output_dir / "index.html"),
            str(output_dir / "browser_qa"),
            DEFAULT_WIDTHS,
            1000,
            screenshot_widths=[390, 1440],
        )
        report["mode"] = "static_and_browser"
        report["allow_non_production"] = args.allow_non_production
        report["browser"] = browser.to_dict()
        report["status"] = "PASS" if report["status"] == "PASS" and browser.status == "PASS" else "FAIL"
        report["exact_capture"] = {"desktop": "1440x1000", "mobile": "390x844"}
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
