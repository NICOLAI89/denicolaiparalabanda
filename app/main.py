from __future__ import annotations

import tkinter as tk

from app.ui import main_window
from app.ui.main_window import MainWindow
from app.ui_autopot import ArgentumAutoPotFrame

# En tu UI principal, agregar:
autopot_frame = ArgentumAutoPotFrame(main_window)
autopot_frame.pack(fill='x', padx=10, pady=5)

def run() -> None:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    run()
