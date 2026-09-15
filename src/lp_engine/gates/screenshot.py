from __future__ import annotations
from .base import Gate
from ..models import GateResult


class ScreenshotPeakGate(Gate):
    name = "ScreenshotPeakGate"

    def evaluate(self, ctx):
        scores = ctx.get("screenshot_scores", [])
        passing = [
            s for s in scores
            if s.total >= 48
            and s.owner_specificity >= 8
            and s.share_impulse >= 8
        ]

        if len(passing) >= 2:
            return GateResult(
                self.name, "PASS",
                "At least two screenshot-worthy frames meet the premium threshold.",
                {"passing_frames": [s.frame_id for s in passing],
                 "scores": {s.frame_id: s.total for s in scores}}
            )
        if len(passing) == 1:
            return GateResult(
                self.name, "HOLD",
                "One premium frame exists; a second independent peak is required.",
                {"passing_frames": [s.frame_id for s in passing],
                 "scores": {s.frame_id: s.total for s in scores}}
            )
        return GateResult(
            self.name, "FAIL",
            "No frame currently reaches the premium screenshot threshold.",
            {"scores": {s.frame_id: s.total for s in scores}}
        )
