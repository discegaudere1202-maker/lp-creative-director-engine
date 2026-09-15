from __future__ import annotations
from .base import Gate
from ..models import GateResult


class OwnerSpecificityGate(Gate):
    name = "OwnerSpecificityGate"

    def evaluate(self, ctx):
        profile = ctx["profile"]
        concept = ctx["concept"]
        fact_keys = {f.key for f in profile.facts}
        used = [k for k in concept.owner_truth_keys if k in fact_keys]

        if len(used) >= 3 and concept.business_verb.strip():
            return GateResult(
                self.name, "PASS",
                "Creative concept is anchored in multiple confirmed owner truths.",
                {"owner_truths_used": used}
            )
        if len(used) >= 1:
            return GateResult(
                self.name, "HOLD",
                "Concept has owner-specific evidence but is not yet strongly anchored.",
                {"owner_truths_used": used}
            )
        return GateResult(
            self.name, "FAIL",
            "Concept can drift into a generic industry template because no confirmed owner truths are encoded.",
            {"owner_truths_used": used}
        )
