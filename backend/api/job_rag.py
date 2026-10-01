from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
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
    match_threshold: float = Query(0.25, ge=0.0, le=1.0),
    candidate_count: int = Query(30, ge=5, le=100),
    result_count: int = Query(10, ge=1, le=50),
    remote_type: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
):
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

        print("\n========== JOB RAG DEBUG ==========", flush=True)
        print("COUNT:", result.get("count"), flush=True)
        print("ROLE GATE:", result.get("role_gate"), flush=True)
        print("EXPERIENCE GATE:", result.get("experience_gate"), flush=True)

        jobs = result.get("jobs") or []

        print("TOTAL JOBS:", len(jobs), flush=True)

        for job in jobs:
            company = job.get("company") or {}
            if isinstance(company, dict):
                company_name = company.get("name") or "Unknown"
            else:
                company_name = str(company)

            print(
                "JOB:",
                company_name,
                "|",
                job.get("title"),
                "| SCORE:",
                job.get("match_score"),
                flush=True,
            )

        print("========== END JOB RAG DEBUG ==========\n", flush=True)

        return result

    except Exception as exc:
        import logging

        logging.getLogger("smarthire.job_rag").exception(
            "Job recommendation search failed for user=%s",
            user_id,
        )

        raise HTTPException(
            status_code=503,
            detail={
                "code": "JOB_RECOMMENDATIONS_UNAVAILABLE",
                "message": (
                    "SmartHire could not load job recommendations right now. "
                    "Please try again in a few moments."
                ),
            },
        ) from exc