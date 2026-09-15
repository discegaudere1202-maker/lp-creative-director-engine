from __future__ import annotations
from .base import Gate
from ..models import GateResult


BAD_ENDINGS = ("を", "に", "へ", "が", "は", "と", "で", "や", "の", "も", "ば", "て")


def _static_copy_issues(text: str) -> list[str]:
    issues = []
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for idx, line in enumerate(lines):
        if len(line) <= 2:
            issues.append(f"line {idx+1} is only {len(line)} chars: {line!r}")
        if line in BAD_ENDINGS:
            issues.append(f"line {idx+1} is an isolated particle: {line!r}")
    return issues


class StaticTextGate(Gate):
    name = "StaticTextGate"

    def evaluate(self, ctx):
        issues = []
        for s in ctx.get("sections", []):
            for text in s.copy:
                for issue in _static_copy_issues(text):
                    issues.append(f"{s.id}: {issue}")

        if issues:
            return GateResult(
                self.name, "FAIL",
                "Static copy contains obvious fragment risks.",
                {"issues": issues}
            )
        return GateResult(
            self.name, "PASS",
            "No obvious static fragment risks. Browser runtime line-box QA is still required.",
            {"runtime_linebox_required": True}
        )
