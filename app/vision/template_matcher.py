from __future__ import annotations

import cv2

from app.vision.base_detector import DetectionResult


class TemplateMatchingDetector:
    detector_type = "template"

    def detect(self, frame, target, threshold: float) -> DetectionResult:
        if frame is None or target is None:
            return DetectionResult(found=False)
        if frame.shape[0] < target.shape[0] or frame.shape[1] < target.shape[1]:
            return DetectionResult(found=False)
        result = cv2.matchTemplate(frame, target, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, max_loc = cv2.minMaxLoc(result)
        if confidence < threshold:
            return DetectionResult(found=False, confidence=float(confidence))
        h, w = target.shape[:2]
        return DetectionResult(found=True, confidence=float(confidence), bbox=(max_loc[0], max_loc[1], w, h))
