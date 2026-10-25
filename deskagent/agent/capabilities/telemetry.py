import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


class Telemetry:
    def __init__(self, path: str | None = None):
        self.path = Path(path).expanduser() if path else None
        self.lock = threading.Lock()
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, **data):
        item = {"event": event, "time": datetime.now().astimezone().isoformat(), **data}
        if self.path:
            with self.lock, self.path.open("a") as file:
                file.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
        return item

    @contextmanager
    def span(self, event: str, **data):
        started = time.perf_counter()
        try:
            yield
            self.record(event, success=True, duration=time.perf_counter() - started, **data)
        except Exception as exc:
            self.record(event, success=False, error=str(exc), duration=time.perf_counter() - started, **data)
            raise
