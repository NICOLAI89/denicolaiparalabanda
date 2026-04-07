from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.models import MacroConfig


class MacroSlotWidget(ttk.LabelFrame):
    def __init__(self, parent, index: int, on_start_stop, on_capture_region, on_capture_target, on_test_detection):
        super().__init__(parent, text=f"Macro {index}")
        self.index = index
        self.on_start_stop = on_start_stop

        self.enabled = tk.BooleanVar(value=False)
        self.sequence = tk.StringVar(value="")
        self.interval_ms = tk.StringVar(value="1000")
        self.hotkey = tk.StringVar(value="")
        self.running = tk.StringVar(value="OFF")

        self.vision_enabled = tk.BooleanVar(value=False)
        self.detector_type = tk.StringVar(value="template")
        self.target_path = tk.StringVar(value="No target")
        self.region = tk.StringVar(value="Full screen")
        self.match_threshold = tk.StringVar(value="0.90")
        self.click_on_match = tk.BooleanVar(value=True)
        self.trigger_seq = tk.BooleanVar(value=False)
        self.track = tk.BooleanVar(value=False)
        self.offset_x = tk.StringVar(value="0")
        self.offset_y = tk.StringVar(value="0")
        self.cooldown = tk.StringVar(value="400")

        ttk.Label(self, text="Status:").grid(row=0, column=0, sticky="w")
        ttk.Label(self, textvariable=self.running).grid(row=0, column=1, sticky="w")
        ttk.Button(self, text="Start/Stop", command=lambda: on_start_stop(self.index)).grid(row=0, column=2, sticky="e")
        ttk.Checkbutton(self, text="Enabled", variable=self.enabled).grid(row=0, column=3, sticky="w")

        ttk.Label(self, text="Sequence").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.sequence, width=24).grid(row=1, column=1, sticky="ew")
        ttk.Label(self, text="Interval (ms)").grid(row=1, column=2, sticky="w")
        ttk.Entry(self, textvariable=self.interval_ms, width=8).grid(row=1, column=3, sticky="w")

        ttk.Label(self, text="Hotkey").grid(row=2, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.hotkey, width=12).grid(row=2, column=1, sticky="w")

        ttk.Separator(self, orient="horizontal").grid(row=3, column=0, columnspan=4, sticky="ew", pady=6)

        ttk.Checkbutton(self, text="Use visual detection", variable=self.vision_enabled).grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Label(self, text="Detector").grid(row=4, column=2, sticky="w")
        ttk.Combobox(self, textvariable=self.detector_type, values=["template", "feature"], state="readonly", width=12).grid(row=4, column=3, sticky="w")

        ttk.Button(self, text="Capture target", command=lambda: on_capture_target(self.index)).grid(row=5, column=0, sticky="w")
        ttk.Label(self, textvariable=self.target_path).grid(row=5, column=1, columnspan=3, sticky="w")
        ttk.Button(self, text="Capture region", command=lambda: on_capture_region(self.index)).grid(row=6, column=0, sticky="w")
        ttk.Label(self, textvariable=self.region).grid(row=6, column=1, columnspan=3, sticky="w")

        ttk.Label(self, text="Threshold").grid(row=7, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.match_threshold, width=8).grid(row=7, column=1, sticky="w")
        ttk.Label(self, text="Cooldown ms").grid(row=7, column=2, sticky="w")
        ttk.Entry(self, textvariable=self.cooldown, width=8).grid(row=7, column=3, sticky="w")

        ttk.Checkbutton(self, text="Click on match", variable=self.click_on_match).grid(row=8, column=0, sticky="w")
        ttk.Checkbutton(self, text="Run sequence on match", variable=self.trigger_seq).grid(row=8, column=1, sticky="w")
        ttk.Checkbutton(self, text="Track after detect", variable=self.track).grid(row=8, column=2, sticky="w")
        ttk.Button(self, text="Test detection", command=lambda: on_test_detection(self.index)).grid(row=8, column=3, sticky="e")

        ttk.Label(self, text="Offset X/Y").grid(row=9, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.offset_x, width=8).grid(row=9, column=1, sticky="w")
        ttk.Entry(self, textvariable=self.offset_y, width=8).grid(row=9, column=2, sticky="w")

        for c in range(4):
            self.columnconfigure(c, weight=1)

    def to_config(self) -> MacroConfig:
        return MacroConfig(
            enabled=self.enabled.get(),
            sequence=self.sequence.get().strip(),
            interval_ms=int(self.interval_ms.get() or "1000"),
            hotkey=self.hotkey.get().strip().lower(),
            vision_enabled=self.vision_enabled.get(),
            detector_type=self.detector_type.get(),
            vision_target_path="" if self.target_path.get() == "No target" else self.target_path.get(),
            search_region=None if self.region.get() == "Full screen" else __import__("ast").literal_eval(self.region.get()),
            match_threshold=float(self.match_threshold.get() or "0.9"),
            click_on_match=self.click_on_match.get(),
            trigger_sequence_on_match=self.trigger_seq.get(),
            click_offset_x=int(self.offset_x.get() or "0"),
            click_offset_y=int(self.offset_y.get() or "0"),
            vision_cooldown_ms=int(self.cooldown.get() or "400"),
            track_after_detect=self.track.get(),
        ).normalized()

    def load_config(self, config: MacroConfig, running: bool = False) -> None:
        self.enabled.set(config.enabled)
        self.sequence.set(config.sequence)
        self.interval_ms.set(str(config.interval_ms))
        self.hotkey.set(config.hotkey)
        self.vision_enabled.set(config.vision_enabled)
        self.detector_type.set(config.detector_type)
        self.target_path.set(config.vision_target_path or "No target")
        self.region.set(str(config.search_region) if config.search_region else "Full screen")
        self.match_threshold.set(str(config.match_threshold))
        self.click_on_match.set(config.click_on_match)
        self.trigger_seq.set(config.trigger_sequence_on_match)
        self.offset_x.set(str(config.click_offset_x))
        self.offset_y.set(str(config.click_offset_y))
        self.cooldown.set(str(config.vision_cooldown_ms))
        self.track.set(config.track_after_detect)
        self.running.set("ON" if running else "OFF")
