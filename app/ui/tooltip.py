from __future__ import annotations

import tkinter as tk


class Tooltip:
    """Reusable hover tooltip with theme-aware colors."""

    def __init__(self, widget: tk.Widget, text: str, *, bg: str = "#111827", fg: str = "#f9fafb") -> None:
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.tipwindow: tk.Toplevel | None = None
        self.widget.bind("<Enter>", self._show, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")

    def configure_theme(self, bg: str, fg: str) -> None:
        self.bg = bg
        self.fg = fg

    def _show(self, _event=None) -> None:
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tipwindow,
            text=self.text,
            justify="left",
            background=self.bg,
            foreground=self.fg,
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            wraplength=280,
            font=("Segoe UI", 9),
        )
        label.pack(ipadx=1)

    def _hide(self, _event=None) -> None:
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
