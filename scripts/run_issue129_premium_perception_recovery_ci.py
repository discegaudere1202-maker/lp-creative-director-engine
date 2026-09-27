"""CI entrypoint for Issue #129 nested legacy evidence chain.

Issue #129 deliberately clears its output root. Issue #116 historically assumes
its nested premium_contact_sheets destination already exists. Create that exact
compatibility directory *after* Issue #129 cleanup and immediately before the
nested Issue #124 -> #121 -> #116 chain. No gate or evidence condition changes.
"""
from __future__ import annotations

import sys

import run_issue129_premium_perception_recovery as target


_original_run_issue124 = target._run_issue124


def _run_issue124_with_compat_dir(baseline, out):
    (out / "issue124_base" / "issue121_base" / "stage_a" / "premium_contact_sheets").mkdir(
        parents=True, exist_ok=True
    )
    return _original_run_issue124(baseline, out)


target._run_issue124 = _run_issue124_with_compat_dir


if __name__ == "__main__":
    raise SystemExit(target.main())
