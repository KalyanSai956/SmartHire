from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class NormalizedJob(BaseModel):
    provider: str
    source_job_id: str
    company_id: UUID
    source_id: UUID
    title: str
    description: str = ""
    location: str | None = None
    location_city: str | None = None
    location_region: str | None = None
    location_country: str | None = None
    location_display: str | None = None
    remote_type: Literal["remote", "hybrid", "onsite", "unknown"] = "unknown"
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] = Field(default_factory=list)
    application_url: HttpUrl
    source_url: HttpUrl | None = None
    posted_at: datetime | None = None


class JobResponse(BaseModel):
    id: UUID
    company_id: UUID | None = None
    source_id: UUID | None = None
    provider: str | None = None
    title: str
    description: str
    location: str | None
    location_city: str | None = None
    location_region: str | None = None
    location_country: str | None = None
    location_display: str | None = None
    remote_type: str
    employment_type: str | None
    experience_level: str | None
    skills: list[str]
    application_url: HttpUrl
    source_url: HttpUrl | None
    posted_at: datetime | None
    is_saved: bool = False


class JobPage(BaseModel):
    jobs: list[JobResponse]
    page: int
    page_size: int
    has_more: bool