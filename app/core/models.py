from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from app.utils.validation import coerce_float, coerce_int

DetectorType = Literal["template", "feature", "object_stub"]
SendMode = Literal["global", "window"]


@dataclass
class MacroConfig:
    enabled: bool = False
    sequence: str = ""
    interval_ms: int = 1000
    hotkey: str = ""
    click_point: tuple[int, int] | None = None

    vision_enabled: bool = False
    detector_type: DetectorType = "template"
    vision_target_path: str = ""
    search_region: tuple[int, int, int, int] | None = None
    match_threshold: float = 0.9
    click_on_match: bool = True
    trigger_sequence_on_match: bool = False
    click_offset_x: int = 0
    click_offset_y: int = 0
    vision_cooldown_ms: int = 400
    track_after_detect: bool = False
    tracker_timeout_ms: int = 1200

    def normalized(self) -> "MacroConfig":
        self.interval_ms = coerce_int(self.interval_ms, 1000, min_value=1)
        self.vision_cooldown_ms = coerce_int(self.vision_cooldown_ms, 400, min_value=1)
        self.tracker_timeout_ms = coerce_int(self.tracker_timeout_ms, 1200, min_value=100)
        self.match_threshold = coerce_float(self.match_threshold, 0.9, 0.1, 0.99)
        return self

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AppProfile:
    schema_version: int = 2
    name: str = "default"
    theme: str = "light"
    topmost: bool = True
    master_hotkey: str = "f6"
    send_mode: SendMode = "global"
    target_window_label: str = ""
    macros: list[MacroConfig] = field(default_factory=lambda: [MacroConfig() for _ in range(6)])

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["macros"] = [m.to_dict() for m in self.macros]
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> "AppProfile":
        profile = cls(
            schema_version=coerce_int(data.get("schema_version"), 2, min_value=1),
            name=str(data.get("name") or "default"),
            theme=str(data.get("theme") or "light"),
            topmost=bool(data.get("topmost", True)),
            master_hotkey=str(data.get("master_hotkey") or "f6"),
            send_mode="window" if str(data.get("send_mode")) == "window" else "global",
            target_window_label=str(data.get("target_window_label") or ""),
        )
        macros = data.get("macros") or []
        parsed: list[MacroConfig] = []
        for entry in macros:
            if not isinstance(entry, dict):
                continue
            parsed.append(MacroConfig(**{k: entry.get(k) for k in MacroConfig.__annotations__.keys() if k in entry}).normalized())
        if len(parsed) < 6:
            parsed.extend(MacroConfig() for _ in range(6-len(parsed)))
        profile.macros = parsed[:6]
        return profile
