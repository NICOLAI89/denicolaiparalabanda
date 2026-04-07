from __future__ import annotations

import cv2
import mss
import numpy as np


class ScreenCapture:
    def capture(self, region: tuple[int, int, int, int] | None = None):
        # mss keeps thread-local native handles internally; sharing one instance across
        # worker threads can crash with missing thread-local attributes.
        with mss.mss() as sct:
            if region:
                left, top, width, height = region
                monitor = {"left": left, "top": top, "width": width, "height": height}
            else:
                monitor = sct.monitors[1]
            img = np.array(sct.grab(monitor))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
