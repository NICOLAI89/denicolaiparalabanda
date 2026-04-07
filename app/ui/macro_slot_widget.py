from __future__ import annotations

import ast
import tkinter as tk
from tkinter import ttk

from app.core.models import MacroConfig


class MacroSlotWidget(ttk.LabelFrame):
    def __init__(self, parent, index: int, on_start_stop, on_capture_region, on_capture_target, on_test_detection):
        super().__init__(parent, text=f"Macro {index}", padding=10)
        self.index = index
        self._tooltip_cb = None

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

        top = ttk.Frame(self)
        top.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 6))
        self.status_pill = tk.Label(top, textvariable=self.running, bg="#7f1d1d", fg="white", padx=8, pady=3)
        self.status_pill.pack(side="left")
        ttk.Checkbutton(top, text="Habilitada", variable=self.enabled).pack(side="left", padx=8)
        ttk.Button(top, text="Iniciar / Detener", command=lambda: on_start_stop(self.index)).pack(side="right")

        ttk.Label(self, text="Secuencia").grid(row=1, column=0, sticky="w")
        seq_entry = ttk.Entry(self, textvariable=self.sequence, width=36)
        seq_entry.grid(row=1, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(self, text="Intervalo (ms)").grid(row=1, column=2, sticky="w")
        ttk.Entry(self, textvariable=self.interval_ms, width=10).grid(row=1, column=3, sticky="w")

        ttk.Label(self, text="Hotkey macro").grid(row=2, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.hotkey, width=12).grid(row=2, column=1, sticky="w")

        ttk.Separator(self, orient="horizontal").grid(row=3, column=0, columnspan=4, sticky="ew", pady=8)

        vision_cb = ttk.Checkbutton(self, text="Usar detección visual", variable=self.vision_enabled)
        vision_cb.grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Label(self, text="Detector").grid(row=4, column=2, sticky="w")
        detector_combo = ttk.Combobox(self, textvariable=self.detector_type, values=["template", "feature"], state="readonly", width=12)
        detector_combo.grid(row=4, column=3, sticky="w")

        cap_target_btn = ttk.Button(self, text="Capturar imagen objetivo", command=lambda: on_capture_target(self.index))
        cap_target_btn.grid(row=5, column=0, sticky="w")
        ttk.Label(self, textvariable=self.target_path).grid(row=5, column=1, columnspan=3, sticky="w")

        cap_region_btn = ttk.Button(self, text="Capturar región", command=lambda: on_capture_region(self.index))
        cap_region_btn.grid(row=6, column=0, sticky="w")
        ttk.Label(self, textvariable=self.region).grid(row=6, column=1, columnspan=3, sticky="w")

        ttk.Label(self, text="Umbral").grid(row=7, column=0, sticky="w")
        threshold_entry = ttk.Entry(self, textvariable=self.match_threshold, width=8)
        threshold_entry.grid(row=7, column=1, sticky="w")
        ttk.Label(self, text="Cooldown (ms)").grid(row=7, column=2, sticky="w")
        ttk.Entry(self, textvariable=self.cooldown, width=8).grid(row=7, column=3, sticky="w")

        click_match_cb = ttk.Checkbutton(self, text="Click al detectar", variable=self.click_on_match)
        click_match_cb.grid(row=8, column=0, sticky="w")
        seq_match_cb = ttk.Checkbutton(self, text="Ejecutar secuencia al detectar", variable=self.trigger_seq)
        seq_match_cb.grid(row=8, column=1, sticky="w")
        track_cb = ttk.Checkbutton(self, text="Tracking opcional", variable=self.track)
        track_cb.grid(row=8, column=2, sticky="w")
        test_btn = ttk.Button(self, text="Probar detección", command=lambda: on_test_detection(self.index))
        test_btn.grid(row=8, column=3, sticky="e")

        ttk.Label(self, text="Offset X/Y").grid(row=9, column=0, sticky="w")
        ox_entry = ttk.Entry(self, textvariable=self.offset_x, width=8)
        oy_entry = ttk.Entry(self, textvariable=self.offset_y, width=8)
        ox_entry.grid(row=9, column=1, sticky="w")
        oy_entry.grid(row=9, column=2, sticky="w")

        for c in range(4):
            self.columnconfigure(c, weight=1)

        self.tooltip_targets = [
            (self, "Tarjeta de macro: aquí configuras y ejecutas esta automatización."),
            (seq_entry, "Secuencia separada por comas. Ejemplo: ctrl+a, click, enter."),
            (threshold_entry, "Nivel mínimo de coincidencia (0.1 a 0.99). Sube si hay falsos positivos."),
            (vision_cb, "Activa búsqueda visual antes de hacer acciones."),
            (detector_combo, "Template para UI fija, Feature para objetivos 2D en movimiento."),
            (cap_target_btn, "Recorta la imagen exacta que quieres detectar en pantalla."),
            (cap_region_btn, "Limita el área de búsqueda para ahorrar CPU y mejorar precisión."),
            (click_match_cb, "Hace click al centro detectado más el offset configurado."),
            (seq_match_cb, "Ejecuta la secuencia si se detecta el objetivo visual."),
            (ox_entry, "Desplaza el click en X e Y desde el centro encontrado."),
            (oy_entry, "Desplaza el click en X e Y desde el centro encontrado."),
            (test_btn, "Prueba una detección única con la configuración actual."),
            (track_cb, "Seguimiento ligero tras detectar para menos trabajo de búsqueda."),
        ]

    def set_running_state(self, is_running: bool) -> None:
        self.running.set("ON" if is_running else "OFF")
        self.status_pill.configure(bg="#166534" if is_running else "#7f1d1d")

    def to_config(self) -> MacroConfig:
        return MacroConfig(
            enabled=self.enabled.get(),
            sequence=self.sequence.get().strip(),
            interval_ms=int(self.interval_ms.get() or "1000"),
            hotkey=self.hotkey.get().strip().lower(),
            vision_enabled=self.vision_enabled.get(),
            detector_type=self.detector_type.get(),
            vision_target_path="" if self.target_path.get() == "No target" else self.target_path.get(),
            search_region=None if self.region.get() == "Full screen" else ast.literal_eval(self.region.get()),
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
        self.set_running_state(running)
