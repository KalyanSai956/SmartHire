from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from backend.api.dependencies import (
    job_recommendation_rate_limit,
)

from backend.core.config import (
    JOB_RECOMMENDATION_CACHE_TTL_SECONDS,
)

from backend.services.cache.cache_service import (
    build_cache_key,
    get_json,
    set_json,
)
from backend.api.auth import (
    get_current_user,
)

from backend.services.rag.job_rag import (
    recommend_jobs,
)


router = APIRouter(
    prefix="/api/v1/job-rag",
    tags=["Job RAG"],
)

@router.get("/recommendations")
async def get_job_recommendations(
    request: Request,
    match_threshold: float = Query(
        0.25,
        ge=0.0,
        le=1.0,
    ),
    candidate_count: int = Query(
        30,
        ge=5,
        le=100,
    ),
    result_count: int = Query(
        10,
        ge=1,
        le=50,
    ),
    remote_type: Optional[str] = Query(
        None
    ),
    employment_type: Optional[str] = Query(
        None
    ),
    user_id: str = Depends(
        job_recommendation_rate_limit
    ),
):
    """
    Return personalized job recommendations.

    Results are cached briefly because the operation
    performs embedding generation, vector search and
    deterministic matching.
    """

    redis = getattr(
        request.app.state,
        "redis",
        None,
    )

    cache_key = build_cache_key(
        "job-recommendations",
        {
            "user_id": user_id,
            "match_threshold": match_threshold,
            "candidate_count": candidate_count,
            "result_count": result_count,
            "remote_type": remote_type,
            "employment_type": employment_type,
        },
    )

    cached = await get_json(
        redis,
        cache_key,
    )

    if isinstance(cached, dict):
        return cached

    try:
        result = await recommend_jobs(
            user_id=user_id,
            embedder=request.app.state.embedder,
            match_threshold=match_threshold,
            candidate_count=candidate_count,
            result_count=result_count,
            remote_type=remote_type,
            employment_type=employment_type,
        )

        await set_json(
            redis,
            cache_key,
            result,
            JOB_RECOMMENDATION_CACHE_TTL_SECONDS,
        )

        return result

    except Exception as exc:

        import logging

        logging.getLogger(
            "smarthire.job_rag"
        ).exception(
            "Job recommendation search failed "
            "for user=%s",
            user_id,
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": (
                    "JOB_RECOMMENDATIONS_UNAVAILABLE"
                ),
                "message": (
                    "SmartHire could not load job "
                    "recommendations right now. "
                    "Please try again in a few moments."
                ),
            },
        ) from exc