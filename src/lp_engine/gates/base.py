from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from ..models import GateResult


class Gate(ABC):
    name: str

    @abstractmethod
    def evaluate(self, ctx: dict[str, Any]) -> GateResult:
        raise NotImplementedError
