from __future__ import annotations

import time

import cv2

from app.vision.base_detector import DetectionResult


class BaseTracker:
    def reset(self) -> None:
        raise NotImplementedError


class OpticalFlowTracker(BaseTracker):
    """Lightweight placeholder tracker using template refresh around last bbox."""

    def __init__(self) -> None:
        self.last_bbox: tuple[int, int, int, int] | None = None
        self.last_update = 0.0

    def reset(self) -> None:
        self.last_bbox = None
        self.last_update = 0.0

    def update_from_detection(self, bbox: tuple[int, int, int, int]) -> None:
        self.last_bbox = bbox
        self.last_update = time.time()

    def track(self, frame, threshold: float = 0.8) -> DetectionResult:
        if not self.last_bbox:
            return DetectionResult(found=False)
        x, y, w, h = self.last_bbox
        crop = frame[max(0, y): y + h, max(0, x): x + w]
        if crop.size == 0:
            return DetectionResult(found=False)
        result = cv2.matchTemplate(frame, crop, cv2.TM_CCOEFF_NORMED)
        _, conf, _, loc = cv2.minMaxLoc(result)
        return DetectionResult(found=conf >= threshold, confidence=float(conf), bbox=(loc[0], loc[1], w, h))
