from __future__ import annotations

from typing import Any

from backend.database.supabase_db import (
    supabase_rest_patch,
)

from backend.services.jobs.job_classifier import (
    CLASSIFICATION_VERSION,
    classify_job,
)


def _build_classification_payload(
    classification,
) -> dict[str, Any]:
    """
    Convert JobClassification into a database update payload.
    """

    return {
        "job_domain": classification.domain,
        "job_family": classification.family,
        "job_category": classification.category,
        "classified_experience_level": (
            classification.experience_level
        ),
        "required_skills": (
            classification.required_skills
        ),
        "preferred_skills": (
            classification.preferred_skills
        ),
        "role_signals": (
            classification.role_signals
        ),
        "classification_confidence": (
            classification.confidence
        ),
        "classification_version": (
            classification.classification_version
        ),
        "classified_at": (
            "now()"
        ),
    }


def _is_currently_classified(
    job: dict[str, Any],
) -> bool:
    """
    Return True when the job already has the current
    classification version.
    """

    return (
        job.get("classified_at") is not None
        and int(
            job.get("classification_version") or 0
        ) == CLASSIFICATION_VERSION
    )


def classify_and_persist_job(
    job: dict[str, Any],
    force: bool = False,
) -> bool:
    """
    Classify one job and persist its classification.

    NOTE:
    The classification itself is synchronous.
    Database persistence is performed by the async
    batch function below.
    """

    if not force and _is_currently_classified(job):
        return False

    classification = classify_job(
        title=job.get("title") or "",
        description=job.get("description") or "",
        skills=job.get("skills") or [],
        experience_level=job.get(
            "experience_level"
        ),
    )

    job["_classification"] = classification

    return True


async def classify_jobs(
    supabase=None,
    jobs: list[dict[str, Any]] | None = None,
    force: bool = False,
) -> dict[str, int]:
    """
    Classify jobs and persist classification metadata
    using the project's existing Supabase REST layer.

    `supabase` is retained as an optional compatibility
    parameter so existing callers do not break.

    The actual database persistence is performed through
    supabase_rest_patch().
    """

    if jobs is None:
        jobs = []

    classified_count = 0
    skipped_count = 0

    for job in jobs:

        if (
            not force
            and _is_currently_classified(job)
        ):
            skipped_count += 1
            continue

        classification = classify_job(
            title=job.get("title") or "",
            description=job.get("description") or "",
            skills=job.get("skills") or [],
            experience_level=job.get(
                "experience_level"
            ),
        )

        payload = _build_classification_payload(
            classification
        )

        job_id = job.get("id")

        if not job_id:
            skipped_count += 1
            continue

        await supabase_rest_patch(
            "jobs",
            {
                "id": f"eq.{job_id}",
            },
            payload,
        )

        classified_count += 1

    return {
        "classified": classified_count,
        "skipped": skipped_count,
    }