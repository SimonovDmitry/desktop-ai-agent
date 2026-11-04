from __future__ import annotations

import threading

from deskagent.autopilot.models import SessionStatus


class AutopilotWorker:
    """Fair background worker. One tick per runnable session per polling round."""

    def __init__(self, engine, poll_interval: float = 0.25):
        self.engine = engine
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self):
        if self.running:
            return self
        self.engine.recover_incomplete()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="deskagent-autopilot", daemon=True)
        self._thread.start()
        return self

    def stop(self, timeout: float = 5.0):
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout)

    def wake(self):
        self._wake.set()

    def _run(self):
        while not self._stop.is_set():
            sessions = self.engine.store.list((SessionStatus.RUNNING.value,))
            progressed = False
            for session in sessions:
                if self._stop.is_set():
                    break
                if not self.engine.store.acquire_lease(session.id, self.engine.owner_id):
                    continue
                try:
                    progressed = self.engine.tick(session.id) or progressed
                finally:
                    self.engine.store.release_lease(session.id, self.engine.owner_id)
            if not progressed:
                self._wake.wait(self.poll_interval)
                self._wake.clear()
