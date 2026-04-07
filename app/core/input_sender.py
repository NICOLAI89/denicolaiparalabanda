from __future__ import annotations

import time

import keyboard
from pynput import mouse

from app.utils.logger import LOGGER

try:
    import win32api
    import win32con
except Exception:  # pragma: no cover
    win32api = None
    win32con = None


class InputSender:
    def __init__(self) -> None:
        self.mouse_controller = mouse.Controller()

    @staticmethod
    def parse_sequence(raw: str) -> list[str]:
        return [part.strip().lower() for part in raw.split(",") if part.strip()]

    def send_sequence_global(self, raw: str) -> None:
        for idx, action in enumerate(self.parse_sequence(raw)):
            self._send_action_global(action)
            if idx:
                time.sleep(0.02)

    def _send_action_global(self, action: str) -> None:
        if action == "click":
            self.mouse_controller.click(mouse.Button.left)
        elif action == "rightclick":
            self.mouse_controller.click(mouse.Button.right)
        elif action == "doubleclick":
            self.mouse_controller.click(mouse.Button.left, 2)
        else:
            keyboard.send(action)

    def send_sequence_window(self, hwnd: int, raw: str, click_point: tuple[int, int] | None = None) -> None:
        if win32api is None or win32con is None:
            raise RuntimeError("Window mode requires pywin32")
        for action in self.parse_sequence(raw):
            if action in {"click", "rightclick", "doubleclick"}:
                if not click_point:
                    raise ValueError("Click point required in window mode")
                self._click_window(hwnd, click_point, action)
            else:
                keyboard.send(action)

    def _click_window(self, hwnd: int, point: tuple[int, int], action: str) -> None:
        x, y = point
        lparam = win32api.MAKELONG(x, y)
        if action == "rightclick":
            down, up, wp = win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON
            count = 1
        else:
            down, up, wp = win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON
            count = 2 if action == "doubleclick" else 1
        for _ in range(count):
            win32api.PostMessage(hwnd, down, wp, lparam)
            time.sleep(0.01)
            win32api.PostMessage(hwnd, up, 0, lparam)

    def click_screen(self, x: int, y: int) -> None:
        self.mouse_controller.position = (x, y)
        self.mouse_controller.click(mouse.Button.left)
        LOGGER.info("Clicked screen at (%s,%s)", x, y)
