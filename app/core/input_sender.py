from __future__ import annotations

import time

import keyboard
from pynput import mouse

from app.utils.logger import LOGGER

try:
    import win32api
    import win32con
    import win32gui
except Exception:  # pragma: no cover
    win32api = None
    win32con = None
    win32gui = None


class InputSender:
    SPECIAL_KEYS = {
        "space": 0x20,
        "enter": 0x0D,
        "tab": 0x09,
        "esc": 0x1B,
        "escape": 0x1B,
        "backspace": 0x08,
        "delete": 0x2E,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
        "home": 0x24,
        "end": 0x23,
        "pgup": 0x21,
        "pgdn": 0x22,
    }
    MODIFIERS = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12}

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
        if win32api is None or win32con is None or win32gui is None:
            raise RuntimeError("Window mode requires pywin32")
        if not win32gui.IsWindow(hwnd):
            raise ValueError("Target window is not valid")
        for action in self.parse_sequence(raw):
            if action in {"click", "rightclick", "doubleclick"}:
                if not click_point:
                    raise ValueError("Click point required in window mode")
                self._click_window(hwnd, click_point, action)
            else:
                self._send_keys_to_window(hwnd, action)

    def _vk_from_token(self, token: str) -> int | None:
        if token in self.MODIFIERS:
            return self.MODIFIERS[token]
        if token in self.SPECIAL_KEYS:
            return self.SPECIAL_KEYS[token]
        if token.startswith("f") and token[1:].isdigit():
            num = int(token[1:])
            if 1 <= num <= 24:
                return 0x6F + num
        if len(token) == 1:
            vk = win32api.VkKeyScan(token)
            return vk & 0xFF if vk != -1 else None
        return None

    def _post_key(self, hwnd: int, vk_code: int, down: bool) -> None:
        msg = win32con.WM_KEYDOWN if down else win32con.WM_KEYUP
        scan = win32api.MapVirtualKey(vk_code, 0)
        lparam = 1 | (scan << 16)
        if not down:
            lparam |= 0xC0000000
        win32api.PostMessage(hwnd, msg, vk_code, lparam)

    def _send_keys_to_window(self, hwnd: int, action: str) -> None:
        tokens = [t.strip() for t in action.split("+") if t.strip()]
        if not tokens:
            return
        mods: list[int] = []
        main = tokens[-1]
        for token in tokens[:-1]:
            vk = self._vk_from_token(token)
            if vk:
                mods.append(vk)

        main_vk = self._vk_from_token(main)
        if main_vk is None:
            LOGGER.warning("Unsupported key token for window mode: %s", action)
            return

        win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        for vk in mods:
            self._post_key(hwnd, vk, True)
            time.sleep(0.005)
        self._post_key(hwnd, main_vk, True)
        time.sleep(0.01)
        self._post_key(hwnd, main_vk, False)
        for vk in reversed(mods):
            time.sleep(0.005)
            self._post_key(hwnd, vk, False)

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


    def click_window_screen(self, hwnd: int, x: int, y: int, button: str = "left", count: int = 1) -> None:
        if win32gui is None:
            return
        client_x, client_y = win32gui.ScreenToClient(hwnd, (x, y))
        action = "rightclick" if button == "right" else ("doubleclick" if count > 1 else "click")
        self._click_window(hwnd, (client_x, client_y), action)

    def click_screen(self, x: int, y: int) -> None:
        self.mouse_controller.position = (x, y)
        self.mouse_controller.click(mouse.Button.left)
        LOGGER.info("Clicked screen at (%s,%s)", x, y)
