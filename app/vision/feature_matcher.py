from __future__ import annotations

import cv2
import numpy as np

from app.vision.base_detector import DetectionResult


class FeatureMatchingDetector:
    detector_type = "feature"

    def __init__(self) -> None:
        self.orb = cv2.ORB_create(500)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def detect(self, frame, target, threshold: float) -> DetectionResult:
        if frame is None or target is None:
            return DetectionResult(found=False)
        kp1, des1 = self.orb.detectAndCompute(target, None)
        kp2, des2 = self.orb.detectAndCompute(frame, None)
        if des1 is None or des2 is None:
            return DetectionResult(found=False)
        knn = self.matcher.knnMatch(des1, des2, k=2)
        good = [m for m, n in knn if m.distance < 0.75 * n.distance]
        confidence = min(1.0, len(good) / max(20, len(kp1)))
        if len(good) < 8 or confidence < threshold * 0.75:
            return DetectionResult(found=False, confidence=confidence)

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if matrix is None:
            return DetectionResult(found=False, confidence=confidence)

        h, w = target.shape[:2]
        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        projected = cv2.perspectiveTransform(corners, matrix).reshape(-1, 2)
        x, y, bw, bh = cv2.boundingRect(projected.astype(np.float32))
        return DetectionResult(found=True, confidence=float(confidence), bbox=(int(x), int(y), int(bw), int(bh)))
