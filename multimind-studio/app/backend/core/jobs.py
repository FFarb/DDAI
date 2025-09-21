from __future__ import annotations

import threading
from queue import Empty, Queue
from typing import Any, Callable, Dict, Optional, Tuple


JobPayload = Tuple[str, Dict[str, Any]]


class JobQueue:
    """Minimal in-process job queue with a dedicated worker thread."""

    def __init__(self) -> None:
        self._queue: "Queue[JobPayload]" = Queue()
        self._handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def register(self, job_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        self._handlers[job_type] = handler

    def enqueue(self, job_type: str, payload: Dict[str, Any]) -> None:
        self._queue.put((job_type, payload))

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                job_type, payload = self._queue.get(timeout=0.5)
            except Empty:
                continue
            handler = self._handlers.get(job_type)
            if handler:
                try:
                    handler(payload)
                except Exception as exc:  # pragma: no cover - logged only
                    print(f"[JobQueue] Job {job_type} failed: {exc}")
            self._queue.task_done()
