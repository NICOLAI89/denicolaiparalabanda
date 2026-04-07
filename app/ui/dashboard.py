from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class Dashboard(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Dashboard")
        self.vars = {k: tk.StringVar(value="-") for k in ["app", "active", "mode", "profile", "window", "vision", "detector"]}
        labels = [
            ("App", "app"),
            ("Active Macros", "active"),
            ("Send Mode", "mode"),
            ("Profile", "profile"),
            ("Target Window", "window"),
            ("Vision", "vision"),
            ("Detector", "detector"),
        ]
        for i, (title, key) in enumerate(labels):
            ttk.Label(self, text=f"{title}:").grid(row=i // 4, column=(i % 4) * 2, sticky="w", padx=6, pady=4)
            ttk.Label(self, textvariable=self.vars[key]).grid(row=i // 4, column=(i % 4) * 2 + 1, sticky="w", padx=6, pady=4)

    def update_values(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if k in self.vars:
                self.vars[k].set(v)
