from __future__ import annotations

import threading


class StoppableWorker:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self, target) -> None:
        self.stop_event.clear()
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
