from __future__ import annotations

import tkinter as tk

from app.ui.main_window import MainWindow


def run() -> None:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    run()
