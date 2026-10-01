from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.core.config import (
    SUPABASE_KEY,
    SUPABASE_URL,
)

from backend.services.jobs.career_profile_builder import (
    build_career_profile,
)

from backend.services.jobs.role_gate import (
    filter_jobs_for_resume,
)

from backend.services.jobs.job_matcher import (
    calculate_job_match,
)

from backend.services.rag.embeddings import (
    embed_text,
)

from backend.services.jobs.experience_matching import (
    experience_compatible,
    profile_experience_level,
)


logger = logging.getLogger("smarthire.job_rag")


# ============================================================
# SUPABASE HELPERS
# ============================================================


def _headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _table_url(table: str) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


def _rpc_url(function_name: str) -> str:
    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/rpc/{function_name}"
    )


# ============================================================
# JOB RETRIEVAL
# ============================================================


async def _get_jobs_by_ids(
    job_ids: List[str],
) -> List[Dict[str, Any]]:

    if not job_ids:
        return []

    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:

        response = await client.get(
            _table_url("jobs"),
            headers=_headers(),
            params={
                "select": (
                    "id,"
                    "company_id,"
                    "source_id,"
                    "provider,"
                    "source_job_id,"
                    "title,"
                    "description,"
                    "location,"
                    "location_city,"
                    "location_region,"
                    "location_country,"
                    "location_display,"
                    "remote_type,"
                    "employment_type,"
                    "experience_level,"
                    "job_domain,"
                    "job_family,"
                    "job_category,"
                    "classified_experience_level,"
                    "required_skills,"
                    "preferred_skills,"
                    "role_signals,"
                    "classification_confidence,"
                    "classification_version,"
                    "classified_at,"
                    "content_hash,"
                    "skills,"
                    "application_url,"
                    "source_url,"
                    "posted_at,"
                    "first_seen_at,"
                    "last_seen_at,"
                    "is_active"
                ),
                "id": (
                    "in.("
                    + ",".join(job_ids)
                    + ")"
                ),
                "is_active": "eq.true",

                # Defense-in-depth:
                # only India jobs can reach the matcher.
                "location_country": "eq.India",
            },
        )

        response.raise_for_status()

        data = response.json()

    return (
        data
        if isinstance(data, list)
        else []
    )


async def _get_companies_by_ids(
    company_ids: List[str],
) -> Dict[str, Dict[str, Any]]:
    """Fetch company branding/metadata for recommendation cards."""

    unique_ids = list(dict.fromkeys(
        str(company_id)
        for company_id in company_ids
        if company_id
    ))

    if not unique_ids:
        return {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            _table_url("companies"),
            headers=_headers(),
            params={
                "select": "id,name,logo_url,website_url,careers_url,brand_color",
                "id": "in.(" + ",".join(unique_ids) + ")",
            },
        )
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, list):
        return {}

    return {
        str(company["id"]): company
        for company in data
        if company.get("id")
    }


# ============================================================
# ACTIVE RESUME
# ============================================================


async def _get_active_resume_chunks(
    user_id: str,
) -> List[Dict[str, Any]]:

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        # ----------------------------------------------------
        # 1. Find the user's active resume
        # ----------------------------------------------------

        resume_response = await client.get(
            _table_url("resume_documents"),
            headers=_headers(),
            params={
                "select": "id",
                "user_id": f"eq.{user_id}",
                "is_active": "eq.true",
                "order": "created_at.desc",
                "limit": "1",
            },
        )

        resume_response.raise_for_status()

        resumes = resume_response.json()

        if not isinstance(resumes, list) or not resumes:
            return []

        resume_id = resumes[0].get("id")

        if not resume_id:
            return []

        # ----------------------------------------------------
        # 2. Get chunks belonging ONLY to active resume
        # ----------------------------------------------------

        response = await client.get(
            _table_url("resume_chunks"),
            headers=_headers(),
            params={
                "select": (
                    "chunk_index,"
                    "section_type,"
                    "title,"
                    "content,"
                    "metadata"
                ),
                "resume_id": f"eq.{resume_id}",
                "user_id": f"eq.{user_id}",
                "order": "chunk_index.asc",
                "limit": "100",
            },
        )

        response.raise_for_status()

        chunks = response.json()

    return (
        chunks
        if isinstance(chunks, list)
        else []
    )


async def _get_user_career_profile(user_id: str) -> Dict[str, Any]:
    from backend.database.supabase_db import get_user_profile

    profile = await get_user_profile(user_id)
    return profile or {}


def _build_profile_context(profile: Dict[str, Any]) -> str:
    parts: list[str] = []

    fields = (
        ("Career interests", profile.get("career_interests")),
        ("Specializations", profile.get("specializations")),
        ("Skills", profile.get("skills")),
        ("Target roles", profile.get("target_roles")),
        ("Experience", profile.get("experience")),
        ("Graduation year", profile.get("graduation_year")),
    )

    for label, value in fields:
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value if item)
        if value is not None and str(value).strip():
            parts.append(f"{label}: {value}")

    return "\n".join(parts)


def _experience_allowed_jobs(
    jobs: List[Dict[str, Any]],
    profile_experience: Any,
) -> tuple[List[Dict[str, Any]], int]:
    if not profile_experience:
        return jobs, 0

    allowed: List[Dict[str, Any]] = []
    rejected = 0

    for job in jobs:
        compatible = experience_compatible(
            profile_experience,
            job_title=job.get("title") or "",
            job_description=job.get("description") or "",
            job_experience_level=(
                job.get("classified_experience_level")
                or job.get("experience_level")
            ),
            source_experience_level=job.get("experience_level"),
        )

        if compatible:
            allowed.append(job)
        else:
            rejected += 1

    return allowed, rejected


# ============================================================
# RESUME CONTEXT
# ============================================================


def _build_resume_context(
    chunks: List[Dict[str, Any]],
) -> str:

    parts: List[str] = []

    for chunk in chunks:

        section = str(
            chunk.get("section_type")
            or ""
        ).strip()

        title = str(
            chunk.get("title")
            or ""
        ).strip()

        content = str(
            chunk.get("content")
            or ""
        ).strip()

        if not content:
            continue

        parts.append(
            f"[{section}] {title}\n"
            f"{content}"
        )

    context = "\n\n".join(parts)

    # Prevent an enormous embedding input.
    return context[:12000]


def _build_resume_text(
    chunks: List[Dict[str, Any]],
) -> str:
    """
    Compact resume representation used for:
    - career classification
    - role gating
    - deterministic matching
    """

    parts: List[str] = []

    for chunk in chunks:

        title = chunk.get("title") or ""
        section_type = chunk.get("section_type") or ""
        content = chunk.get("content") or ""

        if title:
            parts.append(str(title))

        if section_type:
            parts.append(str(section_type))

        if content:
            parts.append(str(content))

    return "\n".join(parts)


# ============================================================
# RESUME SKILLS
# ============================================================


def _get_resume_skills(
    chunks: List[Dict[str, Any]],
) -> List[str]:

    from backend.services.jobs.job_classifier import _extract_skill_mentions

    collected: List[str] = []
    source_parts: List[str] = []

    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        skills = metadata.get("skills")

        if isinstance(skills, list):
            source_parts.extend(
                str(skill)
                for skill in skills
                if skill is not None
            )

        title = chunk.get("title") or ""
        content = chunk.get("content") or ""

        if title:
            source_parts.append(str(title))

        if content:
            source_parts.append(str(content))

    detected = _extract_skill_mentions(
        "\n".join(source_parts)
    )

    for skill in detected:
        if skill not in collected:
            collected.append(skill)

    return collected


# ============================================================
# JOB VECTOR SEARCH
# ============================================================


async def _search_job_vectors(
    *,
    query_embedding: List[float],
    match_threshold: float,
    match_count: int,
    remote_type: Optional[str] = None,
    employment_type: Optional[str] = None,
) -> List[Dict[str, Any]]:

    payload = {
        "p_query_embedding": query_embedding,
        "p_match_threshold": match_threshold,
        "p_match_count": match_count,
        "p_remote_type": remote_type,
        "p_employment_type": employment_type,
    }

    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:

        response = await client.post(
            _rpc_url("match_jobs"),
            headers=_headers(),
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

    return (
        data
        if isinstance(data, list)
        else []
    )


# ============================================================
# JOB RECOMMENDATIONS
# ============================================================


async def recommend_jobs(
    *,
    user_id: str,
    embedder,
    match_threshold: float = 0.25,
    candidate_count: int = 50,
    result_count: int = 20,
    remote_type: Optional[str] = None,
    employment_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resume → Job RAG pipeline.

    Pipeline:

    1. Retrieve active resume chunks.
    2. Build resume context.
    3. Build structured career profile.
    4. Embed resume.
    5. Retrieve semantically similar India jobs.
    6. Apply deterministic role/domain gate.
    7. Calculate transparent match score.
    8. Sort by match score.
    9. Return recommendations + career profile.
    """

    # ========================================================
    # 1. ACTIVE RESUME
    # ========================================================

    chunks = await _get_active_resume_chunks(
        user_id=user_id,
    )

    if not chunks:

        return {
            "indexed": False,
            "message": (
                "Analyze a resume before "
                "requesting job recommendations."
            ),
            "jobs": [],
            "count": 0,
        }

    # ========================================================
    # 2. RESUME CONTEXT
    # ========================================================

    profile = await _get_user_career_profile(user_id)
    profile_context = _build_profile_context(profile)

    resume_context = _build_resume_context(
        chunks,
    )

    if profile_context:
        resume_context = (
            "Candidate career profile:\n"
            + profile_context
            + "\n\nResume:\n"
            + resume_context
        )

    if not resume_context:

        return {
            "indexed": False,
            "message": (
                "The active resume has no "
                "searchable content."
            ),
            "jobs": [],
            "count": 0,
        }

    # ========================================================
    # 3. RESUME TEXT + SKILLS
    # ========================================================

    resume_text = _build_resume_text(
        chunks,
    )

    resume_skills = _get_resume_skills(
        chunks,
    )

    # ========================================================
    # 4. CAREER PROFILE
    # ========================================================

    onboarding_roles = profile.get("target_roles") or []
    onboarding_skills = profile.get("skills") or []
    onboarding_specializations = profile.get("specializations") or []
    onboarding_interests = profile.get("career_interests") or []

    enriched_resume_text = resume_text
    profile_fields = [
        onboarding_interests,
        onboarding_specializations,
        onboarding_skills,
        onboarding_roles,
    ]

    profile_terms = [
        str(item)
        for values in profile_fields
        for item in values
        if item
    ]

    if profile_terms:
        enriched_resume_text += "\n" + "\n".join(profile_terms)

    resume_skills = list(dict.fromkeys(
        [str(skill) for skill in resume_skills if skill]
        + [str(skill) for skill in onboarding_skills if skill]
    ))

    career_profile = build_career_profile(
        resume_text=enriched_resume_text,
        resume_skills=resume_skills,
        target_roles=onboarding_roles or None,
    )

    logger.info(
        "CAREER PROFILE | "
        "domain=%s | "
        "family=%s | "
        "primary_role=%s | "
        "experience=%s | "
        "skills=%d | "
        "confidence=%.2f",
        career_profile.domain,
        career_profile.role_family,
        career_profile.primary_role,
        career_profile.experience_level,
        len(career_profile.skills),
        career_profile.confidence,
    )

    # ========================================================
    # 5. EMBED RESUME
    # ========================================================

    resume_embedding = await embed_text(
        embedder,
        resume_context,
    )

    # ========================================================
    # 6. SEMANTIC JOB RETRIEVAL
    # ========================================================

    retrieval_count = min(100, max(candidate_count, result_count * 5))

    candidates = await _search_job_vectors(
        query_embedding=resume_embedding,
        match_threshold=match_threshold,
        match_count=retrieval_count,
        remote_type=remote_type,
        employment_type=employment_type,
    )

    if not candidates:

        return {
            "indexed": True,
            "count": 0,
            "jobs": [],
            "career_profile": career_profile.to_dict(),
            "role_gate": {
                "input": 0,
                "allowed": 0,
                "rejected_domain": 0,
                "rejected_role": 0,
                "rejected_unknown": 0,
            },
        }

    # ========================================================
    # 7. FETCH FULL JOB RECORDS
    # ========================================================

    job_ids = [
        str(candidate["job_id"])
        for candidate in candidates
        if candidate.get("job_id")
    ]

    jobs = await _get_jobs_by_ids(
        job_ids,
    )
    print("\n========== RETRIEVED JOBS ==========", flush=True)
    print("RETRIEVED COUNT:", len(jobs), flush=True)

    for job in jobs:
        print(
        "JOB:",
        job.get("provider"),
        "|",
        job.get("title"),
        "| DOMAIN:",
        job.get("job_domain"),
        "| FAMILY:",
        job.get("job_family"),
        "| EXPERIENCE:",
        job.get("classified_experience_level"),
        flush=True,
    )

    print("========== END RETRIEVED JOBS ==========\n", flush=True)

    if not jobs:

        return {
            "indexed": True,
            "count": 0,
            "jobs": [],
            "career_profile": career_profile.to_dict(),
            "role_gate": {
                "input": len(candidates),
                "allowed": 0,
                "rejected_domain": 0,
                "rejected_role": 0,
                "rejected_unknown": 0,
            },
        }

    # ========================================================
    # 7.5 COMPANY METADATA
    # ========================================================

    company_map = await _get_companies_by_ids(
        [
            str(job.get("company_id"))
            for job in jobs
            if job.get("company_id")
        ]
    )

    for job in jobs:
        company_id = str(job.get("company_id") or "")
        if company_id:
            job["company"] = company_map.get(company_id)

    # ========================================================
    # 8. EXPERIENCE GATE
    # ========================================================

    profile_experience = profile.get("experience")
    experience_jobs, experience_rejected = _experience_allowed_jobs(
        jobs,
        profile_experience,
    )

    jobs = experience_jobs

    if not jobs:
        return {
            "indexed": True,
            "count": 0,
            "jobs": [],
            "career_profile": career_profile.to_dict(),
            "experience_gate": {
                "profile": profile_experience,
                "rejected": experience_rejected,
            },
            "message": "No active jobs matched your experience level.",
        }

    allowed_experience_job_ids = {
        str(job["id"])
        for job in jobs
        if job.get("id")
    }

    candidates = [
        candidate
        for candidate in candidates
        if str(candidate.get("job_id") or "") in allowed_experience_job_ids
    ]

    # ========================================================
    # 9. ROLE / DOMAIN GATE
    # ========================================================

    filtered_jobs, resume_classification, gate_stats = (
        filter_jobs_for_resume(
            jobs=jobs,
            resume_text=enriched_resume_text,
            resume_skills=resume_skills,
            target_roles=career_profile.target_roles,
        )
    )
    from collections import Counter

    candidate_companies = Counter()

    for job in jobs:
        company = job.get("company") or {}
    if isinstance(company, dict):
        name = company.get("name") or "Unknown"
    else:
        name = str(company)

    candidate_companies[name] += 1

    allowed_companies = Counter()

    for job in filtered_jobs:
        company = job.get("company") or {}
    if isinstance(company, dict):
        name = company.get("name") or "Unknown"
    else:
        name = str(company)

    allowed_companies[name] += 1

    print("SEMANTIC CANDIDATE COMPANIES:", dict(candidate_companies), flush=True)
    print("ROLE GATE ALLOWED COMPANIES:", dict(allowed_companies), flush=True)

    # IMPORTANT:
    # Only these jobs are allowed to continue to scoring.
    allowed_job_ids = {
        str(job["id"])
        for job in filtered_jobs
        if job.get("id")
    }

    jobs_by_id = {
        str(job["id"]): job
        for job in filtered_jobs
        if job.get("id")
    }

    logger.info(
        "ROLE GATE | "
        "domain=%s | "
        "family=%s | "
        "confidence=%.2f | "
        "input=%d | "
        "allowed=%d | "
        "domain_rejected=%d | "
        "role_rejected=%d | "
        "unknown_rejected=%d",
        resume_classification.domain,
        resume_classification.family,
        resume_classification.confidence,
        gate_stats["input"],
        gate_stats["allowed"],
        gate_stats["rejected_domain"],
        gate_stats["rejected_role"],
        gate_stats["rejected_unknown"],
    )

    # ========================================================
    # 9. MATCH SCORING
    # ========================================================

    results: List[Dict[str, Any]] = []

    for candidate in candidates:

        job_id = candidate.get("job_id")

        if not job_id:
            continue

        job_id = str(job_id)

        # CRITICAL:
        # Skip anything rejected by role gating.
        if job_id not in allowed_job_ids:
            continue

        job = jobs_by_id.get(job_id)

        if not job:
            continue

        semantic_similarity = float(
            candidate.get(
                "similarity",
                0.0,
            )
        )

        role_gate = job.get(
            "_role_gate"
        ) or {}

        match = calculate_job_match(
            semantic_similarity=semantic_similarity,
            resume_skills=resume_skills,
            job_skills=job.get("skills") or [],
            resume_text=resume_text,
            job_title=job.get("title") or "",
            resume_family=resume_classification.family,
            job_family=(job.get("job_family") or role_gate.get("family")),
            resume_domain=resume_classification.domain,
            job_domain=(job.get("job_domain") or role_gate.get("domain")),
            required_skills=(job.get("required_skills") or job.get("skills") or []),
            preferred_skills=(job.get("preferred_skills") or []),
            resume_experience_level=(
                profile_experience_level(profile_experience)
                if profile_experience
                else career_profile.experience_level
            ),
            job_experience_level=(job.get("classified_experience_level") or job.get("experience_level")),
            posted_at=job.get("posted_at"),
        )

        logger.info(
            "JOB MATCH | "
            "title=%s | company=%s | score=%.1f | role=%.1f | "
            "required=%.1f | semantic=%.1f | experience=%.1f | "
            "preferred=%.1f | freshness=%.1f",
            job.get("title"),
            (job.get("company") or {}).get("name"),
            match["match_score"],
            match.get("role_score", 0.0),
            match.get("required_skill_score", 0.0),
            match.get("semantic_score", 0.0),
            match.get("experience_score", 0.0),
            match.get("preferred_skill_score", 0.0),
            match.get("freshness_score", 0.0),
        )

        results.append(
            {
                **job,

                "similarity": round(
                    semantic_similarity,
                    4,
                ),

                "role_gate": role_gate,

                **match,
            }
        )

    # ========================================================
    # 10. SORT
    # ========================================================

    results.sort(
        key=lambda item: item["match_score"],
        reverse=True,
    )

    # Deduplicate by company + normalized title.
    deduped: List[Dict[str, Any]] = []
    seen_job_keys = set()

    for item in results:
        company = item.get("company") or {}
        company_key = str(company.get("id") or item.get("company_id") or "").strip().lower()
        title_key = " ".join(str(item.get("title") or "").lower().split())
        dedupe_key = (company_key, title_key)

        if dedupe_key in seen_job_keys:
            continue

        seen_job_keys.add(dedupe_key)
        deduped.append(item)

    # Soft diversity cap: no more than four jobs from one company
    # in the first pass, then use overflow to fill remaining slots.
    company_cap = 4
    final_results: List[Dict[str, Any]] = []
    overflow: List[Dict[str, Any]] = []
    company_counts: Dict[str, int] = {}

    for item in deduped:
        company = item.get("company") or {}
        company_key = str(company.get("id") or item.get("company_id") or "unknown")
        count = company_counts.get(company_key, 0)

        if count < company_cap:
            final_results.append(item)
            company_counts[company_key] = count + 1
        else:
            overflow.append(item)

        if len(final_results) >= result_count:
            break

    if len(final_results) < result_count:
        for item in overflow:
            if len(final_results) >= result_count:
                break
            final_results.append(item)

    logger.info(
        "Job recommendations | semantic_candidates=%d | role_allowed=%d | deduped=%d | returned=%d",
        len(candidates),
        len(results),
        len(deduped),
        len(final_results),
    )

    # ========================================================
    # 11. RESPONSE
    # ========================================================

    return {
        "indexed": True,

        "count": len(final_results),

        "jobs": final_results,

        "career_profile": (
            career_profile.to_dict()
        ),

        "role_gate": gate_stats,
    }