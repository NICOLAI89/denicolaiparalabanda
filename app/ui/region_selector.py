from __future__ import annotations

import tkinter as tk


class RegionSelector:
    def __init__(self, root: tk.Tk):
        self.root = root

    def select(self) -> tuple[int, int, int, int] | None:
        selection: dict[str, int] = {}

        top = tk.Toplevel(self.root)
        top.attributes("-fullscreen", True)
        top.attributes("-alpha", 0.35)
        top.configure(bg="black")
        top.title("Seleccionar región")

        canvas = tk.Canvas(top, bg="black", highlightthickness=0, cursor="crosshair")
        canvas.pack(fill="both", expand=True)

        rect_id: int | None = None

        def on_press(event):
            selection["cx1"], selection["cy1"] = event.x, event.y
            selection["x1"], selection["y1"] = event.x_root, event.y_root

        def on_drag(event):
            nonlocal rect_id
            if "cx1" not in selection:
                return
            if rect_id is not None:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(
                selection["cx1"],
                selection["cy1"],
                event.x,
                event.y,
                outline="#ff4d4d",
                width=2,
            )

        def on_release(event):
            selection["x2"], selection["y2"] = event.x_root, event.y_root
            top.destroy()

        def on_cancel(_event=None):
            selection.clear()
            top.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        top.bind("<Escape>", on_cancel)

        top.grab_set()
        top.focus_force()
        self.root.wait_window(top)

        if not {"x1", "y1", "x2", "y2"}.issubset(selection.keys()):
            return None

        x1, y1 = min(selection["x1"], selection["x2"]), min(selection["y1"], selection["y2"])
        x2, y2 = max(selection["x1"], selection["x2"]), max(selection["y1"], selection["y2"])
        width, height = x2 - x1, y2 - y1
        if width < 5 or height < 5:
            return None
        return (x1, y1, width, height)
