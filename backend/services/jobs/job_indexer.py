from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx

from backend.core.config import (
    SUPABASE_KEY,
    SUPABASE_URL,
)
from backend.services.rag.embeddings import (
    embed_texts,
)


logger = logging.getLogger(
    "smarthire.job_indexer"
)

BATCH_SIZE = 50


def _headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _table_url(
    table: str,
) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


def _build_job_text(
    job: dict[str, Any],
) -> str:
    parts: list[str] = []

    company = (
        job.get("company") or {}
    )

    company_name = str(
        company.get("name")
        or job.get("company_name")
        or ""
    ).strip()

    fields = (
        (
            "Company",
            company_name,
        ),
        (
            "Job Title",
            job.get("title"),
        ),
        (
            "Job Domain",
            job.get("job_domain"),
        ),
        (
            "Job Family",
            job.get("job_family"),
        ),
        (
            "Job Category",
            job.get("job_category"),
        ),
        (
            "Required Skills",
            ", ".join(
                str(skill).strip()
                for skill in (
                    job.get(
                        "required_skills"
                    )
                    or []
                )
                if str(skill).strip()
            ),
        ),
        (
            "Preferred Skills",
            ", ".join(
                str(skill).strip()
                for skill in (
                    job.get(
                        "preferred_skills"
                    )
                    or []
                )
                if str(skill).strip()
            ),
        ),
        (
            "Skills",
            ", ".join(
                str(skill).strip()
                for skill in (
                    job.get("skills")
                    or []
                )
                if str(skill).strip()
            ),
        ),
        (
            "Experience Level",
            (
                job.get(
                    "classified_experience_level"
                )
                or job.get(
                    "experience_level"
                )
            ),
        ),
        (
            "Employment Type",
            job.get(
                "employment_type"
            ),
        ),
        (
            "Work Arrangement",
            job.get(
                "remote_type"
            ),
        ),
        (
            "Location",
            (
                job.get(
                    "location_display"
                )
                or job.get(
                    "location"
                )
            ),
        ),
        (
            "Job Description",
            job.get(
                "description"
            ),
        ),
    )

    for label, value in fields:
        text = str(
            value or ""
        ).strip()

        if text:
            parts.append(
                f"{label}: {text}"
            )

    return "\n\n".join(
        parts
    ).strip()


def _content_hash(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


async def _get_active_jobs() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:
        response = await client.get(
            _table_url("jobs"),
            headers=_headers(),
            params={
                "select": (
                    "id,company_id,title,"
                    "description,location,"
                    "location_display,"
                    "remote_type,"
                    "employment_type,"
                    "experience_level,"
                    "classified_experience_level,"
                    "skills,required_skills,"
                    "preferred_skills,"
                    "job_domain,job_family,"
                    "job_category,"
                    "classification_version,"
                    "provider,source_job_id,"
                    "application_url,source_url"
                ),
                "is_active": "eq.true",
                "location_country": "eq.India",
                "limit": "500",
            },
        )

        response.raise_for_status()

        rows = response.json()

    return (
        rows
        if isinstance(rows, list)
        else []
    )


async def _get_company_map(
    company_ids: set[str],
) -> dict[str, dict[str, Any]]:
    if not company_ids:
        return {}

    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:
        response = await client.get(
            _table_url("companies"),
            headers=_headers(),
            params={
                "id": (
                    "in.("
                    + ",".join(company_ids)
                    + ")"
                ),
                "select": (
                    "id,name,slug,category,"
                    "priority,logo_url"
                ),
            },
        )

        response.raise_for_status()

        rows = response.json()

    if not isinstance(
        rows,
        list,
    ):
        return {}

    return {
        str(row["id"]): row
        for row in rows
        if row.get("id")
    }


async def _get_existing_embeddings() -> dict[
    str,
    dict[str, Any],
]:
    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:
        response = await client.get(
            _table_url(
                "job_embeddings"
            ),
            headers=_headers(),
            params={
                "select": (
                    "job_id,metadata,"
                    "source_hash,"
                    "classification_version"
                ),
                "limit": "10000",
            },
        )

        response.raise_for_status()

        rows = response.json()

    if not isinstance(
        rows,
        list,
    ):
        return {}

    return {
        str(row["job_id"]): row
        for row in rows
        if row.get("job_id")
    }


def _build_embedding_payload(
    job: dict[str, Any],
    text: str,
    embedding: list[float],
) -> dict[str, Any]:
    content_hash = _content_hash(
        text
    )

    company = (
        job.get("company") or {}
    )

    return {
        "job_id": job["id"],
        "embedding": embedding,
        "searchable_text": text,
        "metadata": {
            "provider": job.get(
                "provider"
            ),
            "source_job_id": job.get(
                "source_job_id"
            ),
            "company_id": job.get(
                "company_id"
            ),
            "company_name": company.get(
                "name"
            ),
            "company_slug": company.get(
                "slug"
            ),
            "company_priority": company.get(
                "priority"
            ),
            "title": job.get(
                "title"
            ),
            "skills": job.get(
                "skills"
            ) or [],
            "required_skills": job.get(
                "required_skills"
            ) or [],
            "preferred_skills": job.get(
                "preferred_skills"
            ) or [],
            "job_domain": job.get(
                "job_domain"
            ),
            "job_family": job.get(
                "job_family"
            ),
            "job_category": job.get(
                "job_category"
            ),
            "content_hash": content_hash,
        },
        "source_hash": content_hash,
        "classification_version": job.get(
            "classification_version"
        ),
    }


async def index_jobs(
    *,
    embedder,
) -> dict[str, int]:
    jobs = await _get_active_jobs()

    if not jobs:
        return {
            "jobs_found": 0,
            "jobs_indexed": 0,
            "jobs_skipped": 0,
        }

    company_map = await _get_company_map(
        {
            str(job["company_id"])
            for job in jobs
            if job.get("company_id")
        }
    )

    for job in jobs:
        job["company"] = (
            company_map.get(
                str(
                    job.get(
                        "company_id"
                    )
                    or ""
                )
            )
        )

    existing = (
        await _get_existing_embeddings()
    )

    jobs_to_index: list[
        dict[str, Any]
    ] = []

    skipped_count = 0

    for job in jobs:
        job_id = str(
            job.get("id") or ""
        )

        if not job_id:
            continue

        text = _build_job_text(
            job
        )

        current_hash = _content_hash(
            text
        )

        existing_row = existing.get(
            job_id
        )

        if existing_row:
            metadata = (
                existing_row.get(
                    "metadata"
                )
                or {}
            )

            existing_hash = (
                metadata.get(
                    "content_hash"
                )
                or existing_row.get(
                    "source_hash"
                )
            )

            if (
                existing_hash
                == current_hash
            ):
                skipped_count += 1
                continue

        jobs_to_index.append(
            {
                "job": job,
                "text": text,
            }
        )

    if not jobs_to_index:
        return {
            "jobs_found": len(jobs),
            "jobs_indexed": 0,
            "jobs_skipped": skipped_count,
        }

    indexed_count = 0

    for start in range(
        0,
        len(jobs_to_index),
        BATCH_SIZE,
    ):
        batch = jobs_to_index[
            start:start + BATCH_SIZE
        ]

        texts = [
            item["text"]
            for item in batch
        ]

        embeddings = await embed_texts(
            embedder,
            texts,
        )

        if len(embeddings) != len(
            batch
        ):
            raise RuntimeError(
                "Embedding count does not "
                "match job batch size."
            )

        rows = [
            _build_embedding_payload(
                item["job"],
                item["text"],
                embedding,
            )
            for item, embedding in zip(
                batch,
                embeddings,
            )
        ]

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:
            response = await client.post(
                _table_url(
                    "job_embeddings"
                ),
                headers={
                    **_headers(),
                    "Prefer": (
                        "resolution="
                        "merge-duplicates,"
                        "return=minimal"
                    ),
                },
                params={
                    "on_conflict": "job_id"
                },
                json=rows,
            )

            response.raise_for_status()

        indexed_count += len(
            rows
        )

    return {
        "jobs_found": len(jobs),
        "jobs_indexed": indexed_count,
        "jobs_skipped": skipped_count,
    }


async def reindex_job(
    *,
    job: dict[str, Any],
    embedder,
) -> None:
    text = _build_job_text(
        job
    )

    embeddings = await embed_texts(
        embedder,
        [text],
    )

    if not embeddings:
        raise RuntimeError(
            "Could not generate job embedding."
        )

    payload = _build_embedding_payload(
        job,
        text,
        embeddings[0],
    )

    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:
        response = await client.post(
            _table_url(
                "job_embeddings"
            ),
            headers={
                **_headers(),
                "Prefer": (
                    "resolution="
                    "merge-duplicates,"
                    "return=minimal"
                ),
            },
            params={
                "on_conflict": "job_id"
            },
            json=[payload],
        )

        response.raise_for_status()