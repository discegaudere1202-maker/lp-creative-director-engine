from __future__ import annotations
from .base import Gate
from ..models import GateResult


class RhythmGate(Gate):
    name = "RhythmGate"

    def evaluate(self, ctx):
        sections = ctx.get("sections", [])
        modes = [s.mode for s in sections]
        unique_modes = len(set(modes))
        quiet_count = sum(1 for s in sections if s.quiet)
        peak_count = sum(1 for s in sections if s.screenshot_peak)

        repeated_three = any(
            modes[i] == modes[i+1] == modes[i+2]
            for i in range(max(0, len(modes) - 2))
        )

        energies = [s.energy for s in sections]
        densities = [s.density for s in sections]
        motions = [s.motion for s in sections]

        flat = (
            len(set(energies)) <= 1
            and len(set(densities)) <= 1
            and len(set(motions)) <= 1
        )

        failures = []
        if repeated_three:
            failures.append("same composition mode repeated 3+ times")
        if unique_modes < 4 and len(sections) >= 6:
            failures.append("fewer than 4 composition modes in a long LP")
        if quiet_count < 1 and len(sections) >= 6:
            failures.append("no quiet chapter")
        if peak_count < 2 and len(sections) >= 6:
            failures.append("fewer than 2 screenshot peaks")
        if peak_count > 4:
            failures.append("too many screenshot peaks")
        if flat:
            failures.append("energy/density/motion curve is flat")

        if failures:
            return GateResult(
                self.name, "FAIL",
                "Section rhythm does not yet meet the premium pattern.",
                {"issues": failures, "unique_modes": unique_modes,
                 "quiet_count": quiet_count, "peak_count": peak_count}
            )
        return GateResult(
            self.name, "PASS",
            "Section rhythm has sufficient variation, restraint and peak spacing.",
            {"unique_modes": unique_modes,
             "quiet_count": quiet_count, "peak_count": peak_count}
        )
