"""Issue #111 final runner preserving the accepted authored-media rights enum.

The Visual Asset Library supplies verified licensed media, so the authored input
contract must use the existing `licensed` value rather than inventing a new enum.
"""
from __future__ import annotations

import run_issue111_stage_a_sales_sample_qa as issue111


_ORIGINAL_FIXTURE = issue111.fixture


def _licensed_fixture(*args, **kwargs):
    raw = _ORIGINAL_FIXTURE(*args, **kwargs)
    for role in raw.get("media_roles", []):
        role["rights"] = "licensed"
    return raw


def main() -> int:
    issue111.fixture = _licensed_fixture
    return issue111.main()


if __name__ == "__main__":
    raise SystemExit(main())
