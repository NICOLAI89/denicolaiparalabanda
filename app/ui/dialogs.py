from __future__ import annotations

from tkinter import simpledialog


def ask_profile_name(parent, title: str, initial: str = "") -> str | None:
    return simpledialog.askstring(title, "Profile name", initialvalue=initial, parent=parent)
