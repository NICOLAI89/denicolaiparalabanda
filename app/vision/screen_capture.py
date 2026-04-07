from __future__ import annotations

import cv2
import mss
import numpy as np


class ScreenCapture:
    def __init__(self) -> None:
        self.sct = mss.mss()

    def capture(self, region: tuple[int, int, int, int] | None = None):
        if region:
            left, top, width, height = region
            monitor = {"left": left, "top": top, "width": width, "height": height}
        else:
            monitor = self.sct.monitors[1]
        img = np.array(self.sct.grab(monitor))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
