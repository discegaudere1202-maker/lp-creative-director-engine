from __future__ import annotations
from .base import Gate
from ..models import GateResult


class AuthorityConsistencyGate(Gate):
    name = "AuthorityConsistencyGate"

    def evaluate(self, ctx):
        primary = ctx["primary_authority"]
        concept = ctx["concept"]
        if concept.visual_authority == primary:
            return GateResult(
                self.name, "PASS",
                "Creative concept uses the strongest available visual authority.",
                {"primary_authority": primary}
            )
        return GateResult(
            self.name, "HOLD",
            "Creative concept does not use the classifier's strongest authority; manual rationale required.",
            {
                "primary_authority": primary,
                "concept_authority": concept.visual_authority,
                "scores": ctx.get("authority_scores", {})
            }
        )
