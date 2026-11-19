"""Async job tracking for long-running Unreal operations."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    method: str
    state: JobState = JobState.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    error: str | None = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, method: str) -> Job:
        job = Job(id=str(uuid.uuid4()), method=method, state=JobState.RUNNING)
        self._jobs[job.id] = job
        return job

    def complete(self, job_id: str, result: dict[str, Any]) -> Job:
        job = self._jobs[job_id]
        job.state = JobState.COMPLETED
        job.result = result
        job.updated_at = time.time()
        return job

    def fail(self, job_id: str, error: str) -> Job:
        job = self._jobs[job_id]
        job.state = JobState.FAILED
        job.error = error
        job.updated_at = time.time()
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def to_dict(self, job: Job) -> dict[str, Any]:
        return {
            "job_id": job.id,
            "method": job.method,
            "state": job.state.value,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "result": job.result,
            "error": job.error,
        }
