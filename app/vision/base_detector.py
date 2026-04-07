from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class DetectionResult:
    found: bool
    confidence: float = 0.0
    bbox: tuple[int, int, int, int] | None = None

    @property
    def center(self) -> tuple[int, int] | None:
        if not self.bbox:
            return None
        x, y, w, h = self.bbox
        return x + w // 2, y + h // 2


class BaseDetector(Protocol):
    detector_type: str

    def detect(self, frame, target, threshold: float) -> DetectionResult:
        ...
