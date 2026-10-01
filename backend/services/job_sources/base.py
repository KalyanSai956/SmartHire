from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JobSourceJob(BaseModel):
    company_id: str
    source_id: str
    provider: str
    source_job_id: str
    title: str
    description: str = ""
    location: str | None = None
    remote_type: str | None = None
    employment_type: str | None = "full_time"
    experience_level: str | None = None
    skills: list[str] = Field(default_factory=list)
    application_url: str
    source_url: str
    posted_at: datetime | None = None


class JobSourceAdapter(ABC):
    provider: str

    @abstractmethod
    async def fetch_jobs(self, *, company_id: str, source_id: str, config: dict[str, Any]) -> list[JobSourceJob]:
        raise NotImplementedError
