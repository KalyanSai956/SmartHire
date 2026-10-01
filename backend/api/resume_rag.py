from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from backend.api.dependencies import (
    resume_search_rate_limit,
)

from backend.api.auth import (
    get_current_user,
)

from backend.services.rag.resume_rag import (
    get_resume_rag_status,
    search_resume,
)


router = APIRouter(
    prefix="/api/v1/resume-rag",
    tags=["Resume RAG"],
)


@router.get("/status")
async def resume_rag_status(
    user_id: str = Depends(
        get_current_user
    ),
):
    """
    Check whether the user's resume
    has been indexed into the RAG store.
    """

    try:

        return await get_resume_rag_status(
            user_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load resume RAG status."
            ),
        ) from exc


@router.get("/search")
async def resume_rag_search(
    request: Request,
    q: str = Query(
        ...,
        min_length=2,
        max_length=500,
    ),
    match_threshold: float = Query(
        0.25,
        ge=0.0,
        le=1.0,
    ),
    match_count: int = Query(
        8,
        ge=1,
        le=20,
    ),
    user_id: str = Depends(
    resume_search_rate_limit
),
):
    """
    Semantic search against the user's
    active resume.
    """

    try:

        results = await search_resume(
            user_id=user_id,
            query=q,
            embedder=request.app.state.embedder,
            match_threshold=match_threshold,
            match_count=match_count,
        )

        return {
            "query": q,
            "results": results,
            "count": len(results),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Resume semantic search failed."
            ),
        ) from exc