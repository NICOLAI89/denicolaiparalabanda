from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard as pynput_keyboard

from app.utils.logger import LOGGER


class HotkeyManager:
    def __init__(self) -> None:
        self.listener: pynput_keyboard.Listener | None = None
        self.callbacks: dict[str, Callable[[], None]] = {}

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        if hotkey:
            self.callbacks[hotkey.lower()] = callback

    def clear(self) -> None:
        self.callbacks.clear()

    def start(self) -> None:
        if self.listener:
            return
        self.listener = pynput_keyboard.Listener(on_press=self._on_key)
        self.listener.daemon = True
        self.listener.start()
        LOGGER.info("Hotkey listener started")

    def _on_key(self, key) -> None:
        val = None
        try:
            if key.char:
                val = key.char.lower()
        except Exception:
            val = str(key).replace("Key.", "").lower()
        if val in self.callbacks:
            self.callbacks[val]()
