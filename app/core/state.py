from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MacroRuntimeState:
    running: bool = False
    last_detection_ts: float = 0.0
    last_status: str = "idle"


@dataclass
class AppRuntimeState:
    running_any: bool = False
    selected_window_hwnd: int | None = None
    selected_window_label: str = ""
    macro_states: dict[int, MacroRuntimeState] = field(default_factory=dict)

    def ensure_macro_state(self, idx: int) -> MacroRuntimeState:
        if idx not in self.macro_states:
            self.macro_states[idx] = MacroRuntimeState()
        return self.macro_states[idx]
