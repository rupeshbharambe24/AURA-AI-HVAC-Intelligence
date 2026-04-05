from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class Job:
    job_id: str
    status: str
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, status="queued")
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def run(self, job: Job, fn: Callable[[], Any]) -> None:
        def _target():
            try:
                job.status = "running"
                job.progress = 0.1
                result = fn()
                job.result = result
                job.progress = 1.0
                job.status = "completed"
            except Exception as exc:  # pragma: no cover
                job.error = str(exc)
                job.status = "failed"
                job.progress = 1.0

        t = threading.Thread(target=_target, daemon=True)
        t.start()
