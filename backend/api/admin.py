from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.api.auth import get_current_user
from backend.core.config import SUPABASE_KEY, SUPABASE_URL
from backend.database.supabase_db import supabase_rest_get

logger = logging.getLogger("smarthire")

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
)


async def get_current_admin(
    user_id: str = Depends(get_current_user),
) -> str:
    try:
        rows = await supabase_rest_get(
            "admin_users",
            {
                "user_id": f"eq.{user_id}",
                "is_active": "eq.true",
                "select": "user_id,role,is_active",
                "limit": "1",
            },
        )
    except Exception:
        logger.exception("Admin authorization lookup failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin service is temporarily unavailable.",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is required.",
        )

    return user_id


async def _count_rows(
    table: str,
    filters: dict[str, str] | None = None,
) -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase is not configured.")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "count=exact",
        "Range": "0-0",
    }

    params = {
        "select": "id",
        **(filters or {}),
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=30.0,
        pool=10.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(
            url,
            headers=headers,
            params=params,
        )

    response.raise_for_status()

    content_range = response.headers.get(
        "content-range",
        "",
    )

    match = re.search(
        r"/(\d+|\*)$",
        content_range,
    )

    if match and match.group(1) != "*":
        return int(match.group(1))

    data = response.json()

    return len(data) if isinstance(data, list) else 0


async def _auth_users() -> list[dict[str, Any]]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase is not configured.")

    url = (
        f"{SUPABASE_URL.rstrip('/')}"
        "/auth/v1/admin/users"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=30.0,
        pool=10.0,
    )

    users: list[dict[str, Any]] = []
    page = 1
    per_page = 1000

    async with httpx.AsyncClient(timeout=timeout) as client:
        while True:
            response = await client.get(
                url,
                headers=headers,
                params={
                    "page": page,
                    "per_page": per_page,
                },
            )

            response.raise_for_status()

            payload = response.json()

            page_users = payload.get(
                "users",
                [],
            )

            if not isinstance(page_users, list):
                break

            users.extend(page_users)

            if len(page_users) < per_page:
                break

            page += 1

            if page > 100:
                break

    return users


def _user_payload(
    user: dict[str, Any],
) -> dict[str, Any]:
    metadata = user.get(
        "user_metadata"
    ) or {}

    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "email_confirmed": bool(
            user.get("email_confirmed_at")
        ),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "last_sign_in_at": user.get(
            "last_sign_in_at"
        ),
        "full_name": metadata.get(
            "full_name"
        ),
    }


async def _system_status(
    request: Request,
) -> dict[str, bool]:
    redis = getattr(
        request.app.state,
        "redis",
        None,
    )

    redis_status = False

    if redis is not None:
        try:
            redis_status = bool(
                await redis.ping()
            )
        except Exception:
            redis_status = False

    supabase_status = False

    try:
        await supabase_rest_get(
            "companies",
            {
                "select": "id",
                "limit": "1",
            },
        )
        supabase_status = True
    except Exception:
        supabase_status = False

    return {
        "api": True,
        "supabase": supabase_status,
        "redis": redis_status,
        "embeddings": bool(
            getattr(
                request.app.state,
                "embedder",
                None,
            )
        ),
    }


@router.get("/overview")
async def admin_overview(
    request: Request,
    _: str = Depends(get_current_admin),
):
    try:
        auth_users = await _auth_users()

        active_jobs = await _count_rows(
            "jobs",
            {
                "is_active": "eq.true",
            },
        )

        job_embeddings = await _count_rows(
            "job_embeddings",
        )

        resume_analyses = await _count_rows(
            "analyses",
        )

        usage_rows = await supabase_rest_get(
            "llm_usage",
            {
                "select": (
                    "usage_source,total_tokens"
                ),
                "limit": "5000",
            },
        )

        platform_tokens = sum(
            int(row.get("total_tokens") or 0)
            for row in usage_rows
            if row.get("usage_source")
            == "platform"
        )

        byok_tokens = sum(
            int(row.get("total_tokens") or 0)
            for row in usage_rows
            if row.get("usage_source")
            == "byok"
        )

        return {
            "stats": {
                "users": len(auth_users),
                "active_jobs": active_jobs,
                "job_embeddings": job_embeddings,
                "resume_analyses": resume_analyses,
                "platform_tokens": platform_tokens,
                "byok_tokens": byok_tokens,
            },
            "system": await _system_status(
                request
            ),
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Admin overview failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Admin dashboard is temporarily "
                "unavailable."
            ),
        )


@router.get("/users")
async def admin_users(
    _: str = Depends(get_current_admin),
):
    try:
        users = await _auth_users()

        users = [
            _user_payload(user)
            for user in users
        ]

        users.sort(
            key=lambda item:
                item.get("created_at")
                or "",
            reverse=True,
        )

        return {
            "users": users,
            "total": len(users),
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Admin users failed"
        )

        raise HTTPException(
            status_code=503,
            detail="Users are temporarily unavailable.",
        )


@router.get("/jobs")
async def admin_jobs(
    _: str = Depends(get_current_admin),
):
    try:
        rows = await supabase_rest_get(
            "jobs",
            {
                "select": (
                    "id,title,company_id,"
                    "provider,location_display,"
                    "remote_type,employment_type,"
                    "experience_level,"
                    "classified_experience_level,"
                    "application_url,source_url,"
                    "posted_at,first_seen_at,"
                    "last_seen_at,is_active"
                ),
                "order": "posted_at.desc.nullslast",
                "limit": "100",
            },
        )

        companies = await supabase_rest_get(
            "companies",
            {
                "select": "id,name,slug,logo_url",
                "limit": "100",
            },
        )

        company_map = {
            str(company.get("id")): company
            for company in companies
        }

        jobs = []

        for job in rows:
            company = company_map.get(
                str(
                    job.get("company_id")
                    or ""
                )
            )

            jobs.append(
                {
                    **job,
                    "company": (
                        company.get("name")
                        if company
                        else "Unknown"
                    ),
                    "company_logo": (
                        company.get("logo_url")
                        if company
                        else None
                    ),
                }
            )

        total = await _count_rows(
            "jobs"
        )

        active = await _count_rows(
            "jobs",
            {
                "is_active": "eq.true",
            },
        )

        return {
            "jobs": jobs,
            "total": total,
            "active": active,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Admin jobs failed"
        )

        raise HTTPException(
            status_code=503,
            detail="Jobs are temporarily unavailable.",
        )


@router.get("/sources")
async def admin_sources(
    _: str = Depends(get_current_admin),
):
    try:
        rows = await supabase_rest_get(
            "job_sources",
            {
                "select": "*",
                "order": "created_at.desc",
                "limit": "100",
            },
        )

        return {
            "sources": rows,
            "total": len(rows),
        }

    except Exception:
        logger.exception(
            "Admin sources failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Job sources are temporarily "
                "unavailable."
            ),
        )


@router.get("/embeddings")
async def admin_embeddings(
    _: str = Depends(get_current_admin),
):
    try:
        total_jobs = await _count_rows(
            "jobs"
        )

        total_embeddings = await _count_rows(
            "job_embeddings"
        )

        active_jobs = await _count_rows(
            "jobs",
            {
                "is_active": "eq.true",
            },
        )

        coverage = (
            round(
                (
                    total_embeddings
                    / total_jobs
                )
                * 100,
                2,
            )
            if total_jobs
            else 0
        )

        active_coverage = (
            round(
                (
                    total_embeddings
                    / active_jobs
                )
                * 100,
                2,
            )
            if active_jobs
            else 0
        )

        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "total_embeddings": total_embeddings,
            "coverage": min(
                coverage,
                100,
            ),
            "active_coverage": min(
                active_coverage,
                100,
            ),
            "healthy": (
                total_embeddings > 0
            ),
        }

    except Exception:
        logger.exception(
            "Admin embeddings failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Embedding information is "
                "temporarily unavailable."
            ),
        )


@router.get("/llm-usage")
async def admin_llm_usage(
    _: str = Depends(get_current_admin),
):
    try:
        rows = await supabase_rest_get(
            "llm_usage",
            {
                "select": (
                    "id,user_id,provider,model,"
                    "feature,usage_source,"
                    "input_tokens,output_tokens,"
                    "total_tokens,request_id,"
                    "created_at"
                ),
                "order": "created_at.desc",
                "limit": "500",
            },
        )

        platform_tokens = 0
        byok_tokens = 0

        provider_totals: dict[str, int] = {}

        for row in rows:
            tokens = int(
                row.get("total_tokens")
                or 0
            )

            source = row.get(
                "usage_source"
            )

            provider = row.get(
                "provider"
            ) or "unknown"

            if source == "platform":
                platform_tokens += tokens

            if source == "byok":
                byok_tokens += tokens

            provider_totals[provider] = (
                provider_totals.get(
                    provider,
                    0,
                )
                + tokens
            )

        return {
            "usage": rows,
            "platform_tokens": platform_tokens,
            "byok_tokens": byok_tokens,
            "provider_totals": provider_totals,
            "total_requests": len(rows),
        }

    except Exception:
        logger.exception(
            "Admin LLM usage failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "LLM usage is temporarily "
                "unavailable."
            ),
        )