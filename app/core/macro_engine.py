from __future__ import annotations

import threading
import time

from app.core.input_sender import InputSender
from app.core.models import MacroConfig
from app.utils.logger import LOGGER
from app.vision.detector_manager import DetectorManager
from app.vision.screen_capture import ScreenCapture
from app.vision.target_manager import TargetManager
from app.vision.tracker import OpticalFlowTracker


class MacroRunner:
    def __init__(self, index: int, sender: InputSender, detector_manager: DetectorManager, capture: ScreenCapture, target_manager: TargetManager) -> None:
        self.index = index
        self.sender = sender
        self.detector_manager = detector_manager
        self.capture = capture
        self.target_manager = target_manager
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.tracker = OpticalFlowTracker()

    def start(self, config: MacroConfig, send_mode: str, hwnd: int | None) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, args=(config, send_mode, hwnd), daemon=True)
        self.thread.start()
        LOGGER.info("Macro %s started", self.index)

    def stop(self) -> None:
        self.stop_event.set()
        LOGGER.info("Macro %s stop requested", self.index)

    def _loop(self, config: MacroConfig, send_mode: str, hwnd: int | None) -> None:
        next_allowed = 0.0
        while not self.stop_event.is_set():
            try:
                if config.vision_enabled:
                    now = time.time()
                    if now < next_allowed:
                        self.stop_event.wait(0.02)
                        continue
                    if self._run_vision(config, send_mode, hwnd):
                        next_allowed = now + (config.vision_cooldown_ms / 1000.0)
                else:
                    self._run_sequence(config, send_mode, hwnd)
                self.stop_event.wait(config.interval_ms / 1000.0)
            except Exception:
                LOGGER.exception("Macro %s failed", self.index)
                self.stop_event.set()

    def _run_sequence(self, config: MacroConfig, send_mode: str, hwnd: int | None) -> None:
        if send_mode == "window" and hwnd:
            self.sender.send_sequence_window(hwnd, config.sequence, config.click_point)
        else:
            self.sender.send_sequence_global(config.sequence)

    def _run_vision(self, config: MacroConfig, send_mode: str, hwnd: int | None) -> bool:
        frame = self.capture.capture(config.search_region)
        target = self.target_manager.load_target(config.vision_target_path)
        if target is None:
            return False

        result = self.detector_manager.detect(config.detector_type, frame, target, config.match_threshold)
        if not result.found and config.track_after_detect and self.tracker.last_bbox:
            result = self.tracker.track(frame, threshold=max(0.6, config.match_threshold - 0.2))
        if not result.found:
            return False

        if config.track_after_detect and result.bbox:
            self.tracker.update_from_detection(result.bbox)

        if config.trigger_sequence_on_match:
            self._run_sequence(config, send_mode, hwnd)
        if config.click_on_match and result.center:
            cx, cy = result.center
            ox, oy = config.click_offset_x, config.click_offset_y
            if config.search_region:
                sx, sy, _, _ = config.search_region
                cx, cy = cx + sx, cy + sy
            final_x, final_y = cx + ox, cy + oy
            if send_mode == "window" and hwnd:
                self.sender.click_window_screen(hwnd, final_x, final_y)
            else:
                self.sender.click_screen(final_x, final_y)
        LOGGER.info("Macro %s vision match with %s (%.3f)", self.index, config.detector_type, result.confidence)
        return True
