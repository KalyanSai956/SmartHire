from __future__ import annotations

from fastapi import Depends, Request

from backend.api.auth import get_current_user
from backend.core.config import (
    RATE_LIMIT_HISTORY_PDF,
    RATE_LIMIT_LLM_CONNECT,
    RATE_LIMIT_JOB_RECOMMENDATIONS,
    RATE_LIMIT_PDF,
    RATE_LIMIT_PROFILE_RESUME,
    RATE_LIMIT_RESUME_ANALYSIS,
    RATE_LIMIT_RESUME_SEARCH,
    RATE_LIMIT_WINDOW_SECONDS,
)
from backend.services.cache.rate_limiter import (
    enforce_rate_limit,
)


def _rate_limit_dependency(
    operation: str,
    limit: int,
):
    async def dependency(
        request: Request,
        user_id: str = Depends(
            get_current_user
        ),
    ) -> str:

        redis = getattr(
            request.app.state,
            "redis",
            None,
        )

        await enforce_rate_limit(
            redis,
            key=(
                f"smarthire:rate:{operation}:"
                f"{user_id}"
            ),
            limit=limit,
            window_seconds=(
                RATE_LIMIT_WINDOW_SECONDS
            ),
        )

        return user_id

    return dependency


resume_analysis_rate_limit = (
    _rate_limit_dependency(
        "resume-analysis",
        RATE_LIMIT_RESUME_ANALYSIS,
    )
)


job_recommendation_rate_limit = (
    _rate_limit_dependency(
        "job-recommendations",
        RATE_LIMIT_JOB_RECOMMENDATIONS,
    )
)


resume_search_rate_limit = (
    _rate_limit_dependency(
        "resume-search",
        RATE_LIMIT_RESUME_SEARCH,
    )
)


pdf_rate_limit = (
    _rate_limit_dependency(
        "pdf",
        RATE_LIMIT_PDF,
    )
)


history_pdf_rate_limit = (
    _rate_limit_dependency(
        "history-pdf",
        RATE_LIMIT_HISTORY_PDF,
    )
)


profile_resume_rate_limit = (
    _rate_limit_dependency(
        "profile-resume",
        RATE_LIMIT_PROFILE_RESUME,
    )
)


llm_connect_rate_limit = (
    _rate_limit_dependency(
        "llm-connect",
        RATE_LIMIT_LLM_CONNECT,
    )
)