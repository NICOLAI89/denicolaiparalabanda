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
from app.utils.logger import LOGGER
from app.vision.detector_manager import DetectorManager
from app.vision.screen_capture import ScreenCapture
from app.vision.target_manager import TargetManager


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Macro Tool v2")
        self.root.geometry("1200x900")

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

        self.dashboard = Dashboard(root)
        self.dashboard.pack(fill="x", padx=10, pady=8)

        self._build_profile_bar()
        self._build_global_options()
        self._build_macro_cards()

        self.apply_profile(self.profile)
        self.refresh_windows()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_profile_bar(self):
        bar = ttk.LabelFrame(self.root, text="Profiles")
        bar.pack(fill="x", padx=10, pady=6)
        self.profile_name = tk.StringVar(value=self.profile.name)
        ttk.Entry(bar, textvariable=self.profile_name, width=22).pack(side="left", padx=6, pady=6)
        ttk.Button(bar, text="New", command=self.new_profile).pack(side="left")
        ttk.Button(bar, text="Load", command=self.load_profile).pack(side="left", padx=4)
        ttk.Button(bar, text="Save", command=self.save_profile).pack(side="left")
        ttk.Button(bar, text="Save As", command=self.save_profile_as).pack(side="left", padx=4)
        ttk.Button(bar, text="Delete", command=self.delete_profile).pack(side="left")

    def _build_global_options(self):
        frm = ttk.LabelFrame(self.root, text="Global")
        frm.pack(fill="x", padx=10, pady=6)

        self.send_mode = tk.StringVar(value="global")
        ttk.Radiobutton(frm, text="Global", variable=self.send_mode, value="global", command=self.refresh_dashboard).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frm, text="Window", variable=self.send_mode, value="window", command=self.refresh_dashboard).grid(row=0, column=1, sticky="w")

        self.window_var = tk.StringVar(value="")
        self.window_combo = ttk.Combobox(frm, textvariable=self.window_var, width=70, state="readonly")
        self.window_combo.grid(row=0, column=2, padx=6)
        ttk.Button(frm, text="Refresh windows", command=self.refresh_windows).grid(row=0, column=3)

        ttk.Label(frm, text="Master hotkey").grid(row=1, column=0, sticky="w")
        self.master_hotkey = tk.StringVar(value=self.profile.master_hotkey)
        ttk.Entry(frm, textvariable=self.master_hotkey, width=10).grid(row=1, column=1, sticky="w")
        ttk.Button(frm, text="Apply hotkeys", command=self.rebind_hotkeys).grid(row=1, column=2, sticky="w")
        ttk.Button(frm, text="Toggle all macros", command=self.toggle_all).grid(row=1, column=3, sticky="e")

    def _build_macro_cards(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=8)
        self.cards: list[MacroSlotWidget] = []
        for i in range(1, len(self.profile.macros) + 1):
            card = MacroSlotWidget(container, i, self.toggle_macro, self.capture_region, self.capture_target, self.test_detection)
            card.pack(fill="x", pady=6)
            self.cards.append(card)

    def selected_hwnd(self) -> int | None:
        return self.current_window_map.get(self.window_var.get())

    def refresh_windows(self):
        windows = self.window_manager.enumerate_windows()
        values = [f"{w.title} [HWND {w.hwnd}]" for w in windows]
        self.current_window_map = {f"{w.title} [HWND {w.hwnd}]": w.hwnd for w in windows}
        self.window_combo["values"] = values
        if values and self.window_var.get() not in values:
            self.window_var.set(values[0])
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
            messagebox.showwarning("Detection", "Capture a target image first")
            return
        frame = self.capture.capture(config.search_region)
        target = self.target_manager.load_target(config.vision_target_path)
        result = self.detector_manager.detect(config.detector_type, frame, target, config.match_threshold)
        messagebox.showinfo("Detection", f"Found={result.found} confidence={result.confidence:.3f}")

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
            self.runners[idx] = MacroRunner(idx, self.sender, self.detector_manager, self.capture, self.target_manager)
        runner = self.runners[idx]
        if runner.thread and runner.thread.is_alive():
            runner.stop()
            self.cards[idx - 1].running.set("OFF")
        else:
            cfg = self._macro_config(idx)
            if not cfg.enabled:
                messagebox.showwarning("Macro", f"Macro {idx} is disabled")
                return
            runner.start(cfg, self.send_mode.get(), self.selected_hwnd())
            self.cards[idx - 1].running.set("ON")
        self.refresh_dashboard()

    def toggle_all(self):
        for i, _ in enumerate(self.cards, start=1):
            cfg = self._macro_config(i)
            if cfg.enabled and not (i in self.runners and self.runners[i].thread and self.runners[i].thread.is_alive()):
                self.toggle_macro(i)
            elif i in self.runners and self.runners[i].thread and self.runners[i].thread.is_alive():
                self.toggle_macro(i)

    def rebind_hotkeys(self):
        self.hotkeys.clear()
        if self.master_hotkey.get().strip():
            self.hotkeys.register(self.master_hotkey.get().strip().lower(), self.toggle_all)
        for idx, card in enumerate(self.cards, start=1):
            hk = card.hotkey.get().strip().lower()
            if hk:
                self.hotkeys.register(hk, lambda i=idx: self.toggle_macro(i))

    def snapshot_profile(self) -> AppProfile:
        macros = [self._macro_config(i) for i in range(1, len(self.cards) + 1)]
        return AppProfile(
            name=self.profile_name.get().strip() or "default",
            theme=self.profile.theme,
            topmost=self.profile.topmost,
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
        for i, macro in enumerate(profile.macros, start=1):
            self.cards[i - 1].load_config(macro)
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
        except FileNotFoundError:
            messagebox.showerror("Profile", "Profile not found")

    def save_profile(self):
        profile = self.snapshot_profile()
        self.profile_manager.save(profile)
        self.profile = profile
        self.refresh_dashboard()

    def save_profile_as(self):
        name = ask_profile_name(self.root, "Save Profile As", initial=self.profile_name.get())
        if not name:
            return
        profile = self.snapshot_profile()
        self.profile_manager.save(profile, new_name=name)
        self.profile = profile
        self.profile_name.set(name)
        self.refresh_dashboard()

    def delete_profile(self):
        name = self.profile_name.get().strip()
        if not name:
            return
        self.profile_manager.delete(name)
        self.apply_profile(self.profile_manager.ensure_default())

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
