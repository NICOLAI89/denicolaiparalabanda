from __future__ import annotations

from app.vision.base_detector import DetectionResult
from app.vision.feature_matcher import FeatureMatchingDetector
from app.vision.template_matcher import TemplateMatchingDetector


class ObjectDetectionDetector:
    detector_type = "object_stub"

    def detect(self, frame, target, threshold: float) -> DetectionResult:
        return DetectionResult(found=False, confidence=0.0)


class DetectorManager:
    def __init__(self) -> None:
        self.detectors = {
            "template": TemplateMatchingDetector(),
            "feature": FeatureMatchingDetector(),
            "object_stub": ObjectDetectionDetector(),
        }

    def detect(self, detector_type: str, frame, target, threshold: float) -> DetectionResult:
        detector = self.detectors.get(detector_type, self.detectors["template"])
        return detector.detect(frame, target, threshold)
