from __future__ import annotations

import tkinter as tk


class RegionSelector:
    def __init__(self, root: tk.Tk):
        self.root = root

    def select(self) -> tuple[int, int, int, int] | None:
        data: dict[str, int] = {}
        top = tk.Toplevel(self.root)
        top.attributes("-fullscreen", True)
        top.attributes("-alpha", 0.25)
        top.configure(bg="black")
        canvas = tk.Canvas(top, cursor="cross", bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        rect = None

        def on_press(event):
            data["x1"], data["y1"] = event.x_root, event.y_root

        def on_drag(event):
            nonlocal rect
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(data["x1"], data["y1"], event.x_root, event.y_root, outline="red", width=2)

        def on_release(event):
            data["x2"], data["y2"] = event.x_root, event.y_root
            top.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        top.grab_set()
        self.root.wait_window(top)
        if not data:
            return None
        x1, y1 = min(data["x1"], data["x2"]), min(data["y1"], data["y2"])
        x2, y2 = max(data["x1"], data["x2"]), max(data["y1"], data["y2"])
        if x2 - x1 < 5 or y2 - y1 < 5:
            return None
        return x1, y1, x2 - x1, y2 - y1
