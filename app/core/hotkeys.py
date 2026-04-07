from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from app.utils.logger import LOGGER


class HotkeyManager:
    def __init__(self) -> None:
        self.keyboard_listener: pynput_keyboard.Listener | None = None
        self.mouse_listener: pynput_mouse.Listener | None = None
        self.callbacks: dict[str, Callable[[], None]] = {}

    def normalize_hotkey(self, hotkey: str) -> str:
        token = hotkey.strip().lower().replace(" ", "")
        alias = {"x1": "mouse4", "x2": "mouse5", "mouse_button_4": "mouse4", "mouse_button_5": "mouse5"}
        return alias.get(token, token)

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        key = self.normalize_hotkey(hotkey)
        if key:
            self.callbacks[key] = callback
            LOGGER.info("Hotkey bound: %s", key)

    def clear(self) -> None:
        self.callbacks.clear()

    def start(self) -> None:
        if self.keyboard_listener or self.mouse_listener:
            return
        self.keyboard_listener = pynput_keyboard.Listener(on_press=self._on_key)
        self.keyboard_listener.daemon = True
        self.keyboard_listener.start()
        self.mouse_listener = pynput_mouse.Listener(on_click=self._on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()
        LOGGER.info("Hotkey listeners started")

    def _trigger(self, name: str) -> None:
        callback = self.callbacks.get(name)
        if callback:
            callback()

    def _on_key(self, key) -> None:
        val = None
        try:
            if key.char:
                val = key.char.lower()
        except Exception:
            val = str(key).replace("Key.", "").lower()
        if val:
            self._trigger(self.normalize_hotkey(val))

    def _on_click(self, _x, _y, button, pressed) -> None:
        if not pressed:
            return
        name = str(button).split(".")[-1].lower()
        mouse_map = {"x1": "mouse4", "x2": "mouse5"}
        normalized = mouse_map.get(name, name)
        self._trigger(self.normalize_hotkey(normalized))
