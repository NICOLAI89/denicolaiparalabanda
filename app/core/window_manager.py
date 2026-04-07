from __future__ import annotations

from dataclasses import dataclass

from app.utils.logger import LOGGER

try:
    import win32gui
except Exception:  # pragma: no cover
    win32gui = None


@dataclass
class WindowInfo:
    title: str
    hwnd: int


class WindowManager:
    def enumerate_windows(self) -> list[WindowInfo]:
        if win32gui is None:
            return []
        windows: list[WindowInfo] = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                return
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                windows.append(WindowInfo(title=title, hwnd=hwnd))

        win32gui.EnumWindows(callback, None)
        windows.sort(key=lambda w: w.title.lower())
        return windows

    def is_valid(self, hwnd: int | None) -> bool:
        return bool(win32gui and hwnd and win32gui.IsWindow(hwnd))

    def get_label(self, hwnd: int | None) -> str:
        if not self.is_valid(hwnd):
            return ""
        try:
            return win32gui.GetWindowText(hwnd)
        except Exception as exc:
            LOGGER.warning("Failed to read window label: %s", exc)
            return ""
