from __future__ import annotations
from .base import Gate
from ..models import GateResult


class MotionGate(Gate):
    name = "MotionGate"

    def evaluate(self, ctx):
        motions = ctx.get("motions", [])
        issues = []
        semantic_count = 0

        for m in motions:
            if m.semantic_reason.strip():
                semantic_count += 1
            if m.blocking:
                issues.append(f"{m.id}: blocks user interaction")
            if m.infinite and not m.semantic_reason.strip():
                issues.append(f"{m.id}: infinite loop without semantic reason")
            if m.kind != "signature" and m.duration_ms > 500:
                issues.append(f"{m.id}: ordinary UI motion exceeds 500ms")
            if m.stagger_ms and not (40 <= m.stagger_ms <= 160):
                issues.append(f"{m.id}: stagger outside review range")
            if m.child_count >= 10 and m.stagger_ms:
                issues.append(f"{m.id}: long stagger across 10+ children")

        if issues:
            return GateResult(
                self.name, "FAIL",
                "Motion timing/restraint issues detected.",
                {"issues": issues, "semantic_motion_count": semantic_count}
            )
        if motions and semantic_count == 0:
            return GateResult(
                self.name, "HOLD",
                "Motion exists but no semantic motion is declared.",
                {"semantic_motion_count": 0}
            )
        return GateResult(
            self.name, "PASS",
            "Motion is restrained and at least one motion communicates meaning.",
            {"semantic_motion_count": semantic_count}
        )
