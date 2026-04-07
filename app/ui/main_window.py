from __future__ import annotations

import ast
import tkinter as tk
from tkinter import messagebox, ttk

from app.core.hotkeys import HotkeyManager
from app.core.input_sender import InputSender
from app.core.macro_engine import MacroRunner
from app.core.models import AppProfile
from app.core.window_manager import WindowManager
from app.profiles.profile_manager import ProfileManager
from app.ui.dashboard import Dashboard
from app.ui.dialogs import ask_profile_name
from app.ui.macro_slot_widget import MacroSlotWidget
from app.ui.region_selector import RegionSelector
from app.ui.theme import THEMES
from app.ui.tooltip import Tooltip
from app.utils.logger import LOGGER
from app.vision.detector_manager import DetectorManager
from app.vision.screen_capture import ScreenCapture
from app.vision.target_manager import TargetManager


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Macro Tool v2")
        self.root.geometry("1240x920")

        self.profile_manager = ProfileManager()
        self.window_manager = WindowManager()
        self.sender = InputSender()
        self.detector_manager = DetectorManager()
        self.capture = ScreenCapture()
        self.target_manager = TargetManager()
        self.hotkeys = HotkeyManager()
        self.hotkeys.start()

        self.profile = self.profile_manager.ensure_default()
        self.current_window_map: dict[str, int] = {}
        self.runners: dict[int, MacroRunner] = {}
        self.tooltips: list[Tooltip] = []

        self._build_ui()
        self.apply_profile(self.profile)
        self.refresh_windows()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        LOGGER.info("Application started")

    def _add_tooltip(self, widget, text: str) -> None:
        tip = Tooltip(widget, text)
        self.tooltips.append(tip)

    def _build_ui(self):
        self.theme_var = tk.StringVar(value=self.profile.theme)
        self.topmost_var = tk.BooleanVar(value=self.profile.topmost)
        self.send_mode = tk.StringVar(value="global")

        self.dashboard = Dashboard(self.root)
        self.dashboard.pack(fill="x", padx=10, pady=(10, 6))
        self._add_tooltip(self.dashboard, "Resumen en tiempo real del estado de la app y macros activas.")

        self._build_profile_bar()
        self._build_global_options()
        self._build_macro_cards_scrollable()
        self.apply_theme(self.theme_var.get())

    def _build_profile_bar(self):
        bar = ttk.LabelFrame(self.root, text="Perfiles", padding=8)
        bar.pack(fill="x", padx=10, pady=6)

        self.profile_name = tk.StringVar(value=self.profile.name)
        profile_entry = ttk.Entry(bar, textvariable=self.profile_name, width=24)
        profile_entry.pack(side="left", padx=6)
        new_btn = ttk.Button(bar, text="Nuevo", command=self.new_profile)
        load_btn = ttk.Button(bar, text="Cargar", command=self.load_profile)
        save_btn = ttk.Button(bar, text="Guardar", command=self.save_profile)
        save_as_btn = ttk.Button(bar, text="Guardar como", command=self.save_profile_as)
        delete_btn = ttk.Button(bar, text="Eliminar", command=self.delete_profile)
        for btn in [new_btn, load_btn, save_btn, save_as_btn, delete_btn]:
            btn.pack(side="left", padx=2)

        theme_btn = ttk.Button(bar, text="Cambiar tema", command=self.toggle_theme)
        topmost_cb = ttk.Checkbutton(bar, text="Siempre arriba", variable=self.topmost_var, command=self.apply_topmost)
        theme_btn.pack(side="right", padx=6)
        topmost_cb.pack(side="right")

        self._add_tooltip(bar, "Gestiona perfiles: crear, cargar, guardar y borrar configuraciones.")
        self._add_tooltip(theme_btn, "Alterna entre modo claro y oscuro y lo guarda en el perfil.")
        self._add_tooltip(topmost_cb, "Mantiene la ventana por encima de otras aplicaciones.")
        self._add_tooltip(profile_entry, "Nombre del perfil actual.")

    def _build_global_options(self):
        frm = ttk.LabelFrame(self.root, text="Controles globales", padding=8)
        frm.pack(fill="x", padx=10, pady=6)

        global_rb = ttk.Radiobutton(frm, text="Global", variable=self.send_mode, value="global", command=self.refresh_dashboard)
        window_rb = ttk.Radiobutton(frm, text="Ventana", variable=self.send_mode, value="window", command=self.refresh_dashboard)
        global_rb.grid(row=0, column=0, sticky="w")
        window_rb.grid(row=0, column=1, sticky="w")

        self.window_var = tk.StringVar(value="")
        self.window_combo = ttk.Combobox(frm, textvariable=self.window_var, width=68, state="readonly")
        self.window_combo.grid(row=0, column=2, padx=6, sticky="ew")
        refresh_btn = ttk.Button(frm, text="Actualizar ventanas", command=self.refresh_windows)
        refresh_btn.grid(row=0, column=3, sticky="e")

        ttk.Label(frm, text="Hotkey maestro").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.master_hotkey = tk.StringVar(value=self.profile.master_hotkey)
        hk_entry = ttk.Entry(frm, textvariable=self.master_hotkey, width=12)
        hk_entry.grid(row=1, column=1, sticky="w", pady=(8, 0))
        apply_hk_btn = ttk.Button(frm, text="Aplicar hotkeys", command=self.rebind_hotkeys)
        toggle_btn = ttk.Button(frm, text="Alternar todas", command=self.toggle_all)
        apply_hk_btn.grid(row=1, column=2, sticky="w", pady=(8, 0))
        toggle_btn.grid(row=1, column=3, sticky="e", pady=(8, 0))

        self.status_var = tk.StringVar(value="Listo")
        ttk.Label(frm, textvariable=self.status_var).grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))

        frm.columnconfigure(2, weight=1)

        self._add_tooltip(frm, "Modo de envío, ventana objetivo y hotkeys generales.")
        self._add_tooltip(global_rb, "Envía teclas/clicks al sistema completo.")
        self._add_tooltip(window_rb, "Envía acciones a la ventana seleccionada usando Win32.")
        self._add_tooltip(self.window_combo, "Elige la ventana objetivo cuando uses modo Ventana.")
        self._add_tooltip(hk_entry, "Atajo para iniciar/detener todas las macros. Ej: f6, mouse4.")
        self._add_tooltip(refresh_btn, "Recarga las ventanas visibles del sistema.")

    def _build_macro_cards_scrollable(self):
        wrapper = ttk.Frame(self.root)
        wrapper.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self.canvas = tk.Canvas(wrapper, highlightthickness=0)
        yscroll = ttk.Scrollbar(wrapper, orient="vertical", command=self.canvas.yview)
        self.cards_frame = ttk.Frame(self.canvas)

        self.cards_frame.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=yscroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.cards: list[MacroSlotWidget] = []
        for i in range(1, len(self.profile.macros) + 1):
            card = MacroSlotWidget(self.cards_frame, i, self.toggle_macro, self.capture_region, self.capture_target, self.test_detection)
            card.pack(fill="x", pady=6)
            self.cards.append(card)
            for widget, text in card.tooltip_targets:
                self._add_tooltip(widget, text)

    def apply_theme(self, theme_name: str):
        theme_name = "dark" if theme_name == "dark" else "light"
        self.theme_var.set(theme_name)
        palette = THEMES[theme_name]
        self.root.configure(bg=palette["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=palette["bg"])
        style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
        style.configure("TLabelframe", background=palette["panel"], foreground=palette["fg"])
        style.configure("TLabelframe.Label", background=palette["panel"], foreground=palette["fg"])
        style.configure("TButton", padding=6)
        style.configure("TCheckbutton", background=palette["panel"], foreground=palette["fg"])
        style.configure("TRadiobutton", background=palette["panel"], foreground=palette["fg"])
        style.configure("TEntry", fieldbackground=palette["panel"], foreground=palette["fg"])
        style.configure("TCombobox", fieldbackground=palette["panel"], foreground=palette["fg"])
        self.canvas.configure(bg=palette["bg"])

        tip_bg = "#111827" if theme_name == "dark" else "#111111"
        tip_fg = "#f9fafb"
        for tip in self.tooltips:
            tip.configure_theme(tip_bg, tip_fg)

    def toggle_theme(self):
        self.apply_theme("light" if self.theme_var.get() == "dark" else "dark")

    def apply_topmost(self):
        self.root.attributes("-topmost", bool(self.topmost_var.get()))

    def selected_hwnd(self) -> int | None:
        return self.current_window_map.get(self.window_var.get())

    def refresh_windows(self):
        windows = self.window_manager.enumerate_windows()
        values = [f"{w.title} [HWND {w.hwnd}]" for w in windows]
        self.current_window_map = {f"{w.title} [HWND {w.hwnd}]": w.hwnd for w in windows}
        self.window_combo["values"] = values

        wanted = getattr(self, "_desired_window_label", "") or self.profile.target_window_label
        if wanted and wanted in values:
            self.window_var.set(wanted)
        elif values:
            self.window_var.set(values[0])
            if wanted:
                self.status_var.set("Ventana guardada no disponible; se seleccionó la primera visible.")
        else:
            self.window_var.set("")
            self.status_var.set("No hay ventanas visibles para modo Ventana.")
        self.refresh_dashboard()

    def capture_region(self, idx: int):
        region = RegionSelector(self.root).select()
        if region:
            self.cards[idx - 1].region.set(str(region))

    def capture_target(self, idx: int):
        region = RegionSelector(self.root).select()
        if not region:
            return
        frame = self.capture.capture(region)
        path = self.target_manager.save_target(frame, self.profile_name.get() or "default", idx)
        self.cards[idx - 1].target_path.set(str(path))

    def test_detection(self, idx: int):
        config = self.cards[idx - 1].to_config()
        if not config.vision_target_path:
            messagebox.showwarning("Detección", "Primero captura una imagen objetivo")
            return
        frame = self.capture.capture(config.search_region)
        target = self.target_manager.load_target(config.vision_target_path)
        result = self.detector_manager.detect(config.detector_type, frame, target, config.match_threshold)
        messagebox.showinfo("Detección", f"Found={result.found} confidence={result.confidence:.3f}")

    def _macro_config(self, idx: int):
        cfg = self.cards[idx - 1].to_config()
        region = cfg.search_region
        if isinstance(region, str):
            try:
                cfg.search_region = ast.literal_eval(region)
            except Exception:
                cfg.search_region = None
        return cfg

    def toggle_macro(self, idx: int):
        if idx not in self.runners:
            self.runners[idx] = MacroRunner(idx, self.sender, self.detector_manager, self.capture, self.target_manager, self.on_macro_stopped)
        runner = self.runners[idx]
        card = self.cards[idx - 1]
        if runner.thread and runner.thread.is_alive():
            runner.stop()
            card.set_running_state(False)
        else:
            cfg = self._macro_config(idx)
            if not cfg.enabled:
                messagebox.showwarning("Macro", f"Macro {idx} está deshabilitada")
                return
            runner.start(cfg, self.send_mode.get(), self.selected_hwnd())
            card.set_running_state(True)
        self.refresh_dashboard()

    def on_macro_stopped(self, idx: int, reason: str | None = None) -> None:
        def _update_ui() -> None:
            card = self.cards[idx - 1]
            card.set_running_state(False)
            if reason:
                self.status_var.set(f"Macro {idx} detenida por error: {reason}")
            self.refresh_dashboard()

        self.root.after(0, _update_ui)

    def toggle_all(self):
        for i, _ in enumerate(self.cards, start=1):
            cfg = self._macro_config(i)
            running = i in self.runners and self.runners[i].thread and self.runners[i].thread.is_alive()
            if cfg.enabled and not running:
                self.toggle_macro(i)
            elif running:
                self.toggle_macro(i)

    def rebind_hotkeys(self):
        self.hotkeys.clear()
        master = self.master_hotkey.get().strip().lower()
        if master:
            self.hotkeys.register(master, self.toggle_all)
        for idx, card in enumerate(self.cards, start=1):
            hk = card.hotkey.get().strip().lower()
            if hk:
                self.hotkeys.register(hk, lambda i=idx: self.toggle_macro(i))
        self.status_var.set("Hotkeys actualizadas")

    def snapshot_profile(self) -> AppProfile:
        macros = [self._macro_config(i) for i in range(1, len(self.cards) + 1)]
        return AppProfile(
            name=self.profile_name.get().strip() or "default",
            theme=self.theme_var.get(),
            topmost=self.topmost_var.get(),
            master_hotkey=self.master_hotkey.get().strip().lower() or "f6",
            send_mode="window" if self.send_mode.get() == "window" else "global",
            target_window_label=self.window_var.get(),
            macros=macros,
        )

    def apply_profile(self, profile: AppProfile):
        self.profile = profile
        self.profile_name.set(profile.name)
        self.master_hotkey.set(profile.master_hotkey)
        self.send_mode.set(profile.send_mode)
        self.theme_var.set(profile.theme)
        self.topmost_var.set(profile.topmost)
        self._desired_window_label = profile.target_window_label

        for i, macro in enumerate(profile.macros[: len(self.cards)], start=1):
            self.cards[i - 1].load_config(macro)
        self.apply_theme(profile.theme)
        self.apply_topmost()
        self.rebind_hotkeys()
        self.refresh_dashboard()

    def new_profile(self):
        self.apply_profile(AppProfile(name="new_profile"))

    def load_profile(self):
        names = self.profile_manager.list_profiles()
        if not names:
            return
        selected = ask_profile_name(self.root, "Load Profile", initial=names[0])
        if not selected:
            return
        try:
            self.apply_profile(self.profile_manager.load(selected))
            self.refresh_windows()
            self.status_var.set(f"Perfil cargado: {selected}")
        except FileNotFoundError:
            messagebox.showerror("Perfil", "Perfil no encontrado")

    def save_profile(self):
        profile = self.snapshot_profile()
        self.profile_manager.save(profile)
        self.profile = profile
        self.status_var.set(f"Perfil guardado: {profile.name}")
        self.refresh_dashboard()

    def save_profile_as(self):
        name = ask_profile_name(self.root, "Save Profile As", initial=self.profile_name.get())
        if not name:
            return
        profile = self.snapshot_profile()
        self.profile_manager.save(profile, new_name=name)
        self.profile = profile
        self.profile_name.set(name)
        self.status_var.set(f"Perfil guardado como: {name}")
        self.refresh_dashboard()

    def delete_profile(self):
        name = self.profile_name.get().strip()
        if not name:
            return
        self.profile_manager.delete(name)
        self.apply_profile(self.profile_manager.ensure_default())
        self.refresh_windows()
        self.status_var.set(f"Perfil eliminado: {name}")

    def refresh_dashboard(self):
        active = sum(1 for r in self.runners.values() if r.thread and r.thread.is_alive())
        detector = ", ".join(sorted({c.detector_type.get() for c in self.cards if c.vision_enabled.get()})) or "n/a"
        self.dashboard.update_values(
            app="running" if active else "stopped",
            active=str(active),
            mode=self.send_mode.get(),
            profile=self.profile_name.get(),
            window=self.window_var.get() or "n/a",
            vision=f"{sum(1 for c in self.cards if c.vision_enabled.get())} macros enabled",
            detector=detector,
        )

    def on_close(self):
        LOGGER.info("Closing app")
        for runner in self.runners.values():
            runner.stop()
        self.root.destroy()
