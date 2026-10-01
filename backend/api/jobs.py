from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from backend.api.auth import (
    get_current_user,
)

from backend.database.supabase_db import (
    _get_headers,
    _get_rest_url,
    supabase_rest_get,
)


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


def _company_payload(
    company: dict | None,
) -> dict | None:
    if not company:
        return None

    return {
        "id": company.get(
            "id"
        ),
        "name": company.get(
            "name"
        ),
        "slug": company.get(
            "slug"
        ),
        "category": company.get(
            "category"
        ),
        "logo_url": company.get(
            "logo_url"
        ),
        "website_url": company.get(
            "website_url"
        ),
        "careers_url": company.get(
            "careers_url"
        ),
        "priority": company.get(
            "priority"
        ),
    }


async def _saved_ids(
    user_id: str,
) -> set[str]:
    rows = await supabase_rest_get(
        "saved_jobs",
        {
            "user_id": (
                f"eq.{user_id}"
            ),
            "select": "job_id",
        },
    )

    return {
        str(row["job_id"])
        for row in rows
        if row.get("job_id")
    }


async def _companies() -> list[dict]:
    return await supabase_rest_get(
        "companies",
        {
            "is_target_company": (
                "eq.true"
            ),
            "select": (
                "id,name,slug,category,"
                "logo_url,website_url,"
                "careers_url,priority"
            ),
            "limit": "100",
        },
    )


def _sort_jobs(
    jobs: list[dict],
    sort: str,
) -> list[dict]:
    normalized = (
        sort.strip().lower()
    )

    if normalized == "oldest":
        return sorted(
            jobs,
            key=lambda job:
                job.get(
                    "posted_at"
                ) or "",
        )

    if normalized == "company_priority":
        return sorted(
            jobs,
            key=lambda job: (
                int(
                    (
                        job.get(
                            "company"
                        )
                        or {}
                    ).get(
                        "priority"
                    )
                    or 100
                ),
                -(
                    1
                    if job.get(
                        "posted_at"
                    )
                    else 0
                ),
                job.get(
                    "posted_at"
                ) or "",
            ),
        )

    if normalized == "title":
        return sorted(
            jobs,
            key=lambda job:
                str(
                    job.get(
                        "title"
                    )
                    or ""
                ).lower(),
        )

    return sorted(
        jobs,
        key=lambda job:
            job.get(
                "posted_at"
            ) or "",
        reverse=True,
    )


def _apply_filters(
    jobs: list[dict],
    *,
    search: str | None,
    location: str | None,
    remote_type: str | None,
    employment_type: str | None,
    experience: str | None,
    company: str | None,
) -> list[dict]:
    search_value = (
        (search or "")
        .strip()
        .lower()
    )

    location_value = (
        (location or "")
        .strip()
        .lower()
    )

    remote_value = (
        (remote_type or "")
        .strip()
        .lower()
    )

    employment_value = (
        (employment_type or "")
        .strip()
        .lower()
    )

    experience_value = (
        (experience or "")
        .strip()
        .lower()
    )

    company_value = (
        (company or "")
        .strip()
        .lower()
    )

    filtered = []

    for job in jobs:
        company_data = (
            job.get(
                "company"
            )
            or {}
        )

        searchable = " ".join(
            [
                str(
                    job.get(
                        "title"
                    )
                    or ""
                ),
                str(
                    job.get(
                        "description"
                    )
                    or ""
                ),
                " ".join(
                    str(skill)
                    for skill in (
                        job.get(
                            "skills"
                        )
                        or []
                    )
                ),
                str(
                    company_data.get(
                        "name"
                    )
                    or ""
                ),
            ]
        ).lower()

        if (
            search_value
            and search_value
            not in searchable
        ):
            continue

        job_location = str(
            job.get(
                "location_display"
            )
            or job.get(
                "location"
            )
            or ""
        ).lower()

        if (
            location_value
            and location_value
            not in job_location
        ):
            continue

        if remote_value:
            job_remote = str(
                job.get(
                    "remote_type"
                )
                or ""
            ).lower()

            if (
                job_remote
                != remote_value
            ):
                continue

        if employment_value:
            value = str(
                job.get(
                    "employment_type"
                )
                or ""
            ).lower()

            if (
                employment_value
                not in value
            ):
                continue

        if experience_value:
            value = " ".join(
                [
                    str(
                        job.get(
                            "experience_level"
                        )
                        or ""
                    ),
                    str(
                        job.get(
                            "classified_experience_level"
                        )
                        or ""
                    ),
                ]
            ).lower()

            if (
                experience_value
                not in value
            ):
                continue

        if company_value:
            company_match = (
                company_value
                == str(
                    company_data.get(
                        "slug"
                    )
                    or ""
                ).lower()
                or company_value
                == str(
                    company_data.get(
                        "name"
                    )
                    or ""
                ).lower()
            )

            if not company_match:
                continue

        filtered.append(
            job
        )

    return filtered


async def _enrich_companies(
    jobs: list[dict],
    companies: list[dict],
) -> list[dict]:
    company_map = {
        str(company["id"]): (
            _company_payload(
                company
            )
        )
        for company in companies
        if company.get("id")
    }

    result = []

    for job in jobs:
        item = dict(
            job
        )

        item["company"] = (
            company_map.get(
                str(
                    job.get(
                        "company_id"
                    )
                    or ""
                )
            )
        )

        result.append(
            item
        )

    return result


@router.get("")
async def list_jobs(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int | None = Query(
        None,
        ge=1,
        le=50,
    ),
    limit: int | None = Query(
        None,
        ge=1,
        le=50,
    ),
    search: str | None = Query(
        None,
        max_length=100,
    ),
    location: str | None = Query(
        None,
        max_length=100,
    ),
    remote_type: str | None = Query(
        None,
        max_length=20,
    ),
    employment_type: str | None = Query(
        None,
        max_length=50,
    ),
    experience: str | None = Query(
        None,
        max_length=50,
    ),
    company: str | None = Query(
        None,
        max_length=100,
    ),
    sort: str = Query(
        "newest",
        max_length=30,
    ),
    user_id: str = Depends(
        get_current_user
    ),
):
    requested_page_size = (
        limit
        or page_size
        or 20
    )

    params = {
        "select": (
            "id,company_id,source_id,"
            "provider,title,description,"
            "location,location_city,"
            "location_region,"
            "location_country,"
            "location_display,"
            "remote_type,"
            "employment_type,"
            "experience_level,"
            "classified_experience_level,"
            "skills,application_url,"
            "source_url,posted_at,"
            "first_seen_at,last_seen_at,"
            "job_domain,job_family,"
            "job_category,"
            "required_skills,"
            "preferred_skills"
        ),
        "is_active": "eq.true",
        "location_country": "eq.India",
        "limit": "500",
    }

    if remote_type:
        params[
            "remote_type"
        ] = (
            f"eq.{remote_type.strip().lower()}"
        )

    if employment_type:
        params[
            "employment_type"
        ] = (
            f"ilike.*"
            f"{employment_type.strip()}"
            f"*"
        )

    rows = await supabase_rest_get(
        "jobs",
        params,
    )

    companies = await _companies()

    jobs = await _enrich_companies(
        rows,
        companies,
    )

    jobs = _apply_filters(
        jobs,
        search=search,
        location=location,
        remote_type=remote_type,
        employment_type=employment_type,
        experience=experience,
        company=company,
    )

    jobs = _sort_jobs(
        jobs,
        sort,
    )

    saved = await _saved_ids(
        user_id
    )

    total = len(
        jobs
    )

    offset = (
        (page - 1)
        * requested_page_size
    )

    page_jobs = jobs[
        offset:
        offset
        + requested_page_size
    ]

    for job in page_jobs:
        job[
            "is_saved"
        ] = (
            str(
                job["id"]
            )
            in saved
        )

    return {
        "jobs": page_jobs,
        "page": page,
        "page_size": (
            requested_page_size
        ),
        "has_more": (
            offset
            + requested_page_size
            < total
        ),
        "total": total,
    }


@router.get("/saved")
async def list_saved_jobs(
    user_id: str = Depends(
        get_current_user
    ),
):
    rows = await supabase_rest_get(
        "saved_jobs",
        {
            "user_id": (
                f"eq.{user_id}"
            ),
            "select": (
                "job_id,created_at"
            ),
            "order": (
                "created_at.desc"
            ),
        },
    )

    if not rows:
        return {
            "jobs": []
        }

    job_ids = ",".join(
        str(row["job_id"])
        for row in rows
        if row.get(
            "job_id"
        )
    )

    if not job_ids:
        return {
            "jobs": []
        }

    jobs = await supabase_rest_get(
        "jobs",
        {
            "id": (
                f"in.({job_ids})"
            ),
            "select": (
                "id,company_id,"
                "source_id,provider,"
                "title,description,"
                "location,location_city,"
                "location_region,"
                "location_country,"
                "location_display,"
                "remote_type,"
                "employment_type,"
                "experience_level,"
                "classified_experience_level,"
                "skills,application_url,"
                "source_url,posted_at,"
                "first_seen_at,last_seen_at,"
                "job_domain,job_family,"
                "job_category,"
                "required_skills,"
                "preferred_skills,"
                "is_active"
            ),
        },
    )

    companies = await _companies()

    jobs = await _enrich_companies(
        jobs,
        companies,
    )

    by_id = {
        str(
            job["id"]
        ): job
        for job in jobs
        if job.get("id")
    }

    return {
        "jobs": [
            {
                **by_id[
                    str(
                        row["job_id"]
                    )
                ],
                "is_saved": True,
                "saved_at": (
                    row["created_at"]
                ),
            }
            for row in rows
            if str(
                row.get(
                    "job_id"
                )
            ) in by_id
        ]
    }


@router.post(
    "/{job_id}/save"
)
async def save_job(
    job_id: UUID,
    user_id: str = Depends(
        get_current_user
    ),
):
    existing = await supabase_rest_get(
        "jobs",
        {
            "id": (
                f"eq.{job_id}"
            ),
            "select": "id",
            "limit": "1",
        },
    )

    if not existing:
        raise HTTPException(
            404,
            "Job not found",
        )

    async with httpx.AsyncClient(
        timeout=20
    ) as client:
        response = await client.post(
            _get_rest_url(
                "saved_jobs"
            ),
            headers={
                **_get_headers(),
                "Prefer": (
                    "resolution="
                    "ignore-duplicates,"
                    "return=minimal"
                ),
            },
            params={
                "on_conflict": (
                    "user_id,job_id"
                )
            },
            json={
                "user_id": user_id,
                "job_id": str(
                    job_id
                ),
            },
        )

        response.raise_for_status()

    return {
        "saved": True,
        "job_id": str(
            job_id
        ),
    }


@router.delete(
    "/{job_id}/save"
)
async def unsave_job(
    job_id: UUID,
    user_id: str = Depends(
        get_current_user
    ),
):
    async with httpx.AsyncClient(
        timeout=20
    ) as client:
        response = await client.delete(
            _get_rest_url(
                "saved_jobs"
            ),
            headers=_get_headers(),
            params={
                "user_id": (
                    f"eq.{user_id}"
                ),
                "job_id": (
                    f"eq.{job_id}"
                ),
            },
        )

        response.raise_for_status()

    return {
        "saved": False,
        "job_id": str(
            job_id
        ),
    }


@router.get(
    "/{job_id}"
)
async def get_job(
    job_id: UUID,
    user_id: str = Depends(
        get_current_user
    ),
):
    rows = await supabase_rest_get(
        "jobs",
        {
            "id": (
                f"eq.{job_id}"
            ),
            "select": "*",
            "limit": "1",
        },
    )

    if not rows:
        raise HTTPException(
            404,
            "Job not found",
        )

    companies = await _companies()

    jobs = await _enrich_companies(
        rows,
        companies,
    )

    saved = await _saved_ids(
        user_id
    )

    return {
        **jobs[0],
        "is_saved": (
            str(job_id)
            in saved
        ),
    }