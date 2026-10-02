from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

import spacy
from fastapi import (
    FastAPI,
    Request,
)
from backend.api.admin import (
    router as admin_router,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer

from backend.api.jobs import (
    router as jobs_router,
)
from backend.api.job_rag import (
    router as job_rag_router,
)
from backend.api.llm_settings import (
    router as llm_settings_router,
)
from backend.api.profile import (
    router as profile_router,
)
from backend.api.resume_rag import (
    router as resume_rag_router,
)
from backend.api.routes import (
    router,
)
from backend.api.usage import (
    router as usage_router,
)
from backend.core.config import (
    ALLOWED_ORIGINS,
    APP_DESCRIPTION,
    APP_ENV,
    APP_TITLE,
    APP_VERSION,
    SENTENCE_TRANSFORMER_MODEL,
    SPACY_MODEL_PRIMARY,
    SPACY_MODEL_SECONDARY,
)
from backend.services.cache.redis_client import (
    close_redis_client,
    create_redis_client,
)


logger = logging.getLogger(
    "smarthire"
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """
    Application startup/shutdown lifecycle.
    """

    logger.info(
        "Starting SmartHire ATS API..."
    )

    # --------------------------------------------------------
    # Redis
    # --------------------------------------------------------

    app.state.redis = (
        await create_redis_client()
    )

    if app.state.redis is not None:
        logger.info(
            "Redis caching and rate limiting enabled."
        )
    else:
        logger.warning(
            "Redis unavailable. "
            "Cache will be bypassed."
        )

    # --------------------------------------------------------
    # spaCy
    # --------------------------------------------------------

    logger.info(
        "Loading spaCy model: %s",
        SPACY_MODEL_PRIMARY,
    )

    try:
        app.state.nlp = spacy.load(
            SPACY_MODEL_PRIMARY
        )

        logger.info(
            "Loaded spaCy model: %s",
            SPACY_MODEL_PRIMARY,
        )

    except OSError:

        logger.warning(
            "%s not found. "
            "Using fallback model: %s",
            SPACY_MODEL_PRIMARY,
            SPACY_MODEL_SECONDARY,
        )

        app.state.nlp = spacy.load(
            SPACY_MODEL_SECONDARY
        )

    # --------------------------------------------------------
    # Sentence Transformer
    # --------------------------------------------------------

    logger.info(
        "Loading embedding model: %s",
        SENTENCE_TRANSFORMER_MODEL,
    )

    app.state.embedder = (
        SentenceTransformer(
            SENTENCE_TRANSFORMER_MODEL
        )
    )

    logger.info(
        "All SmartHire models loaded."
    )

    try:
        yield

    finally:

        logger.info(
            "Shutting down SmartHire ATS API..."
        )

        await close_redis_client(
            app.state.redis
        )


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url=(
        "/docs"
        if APP_ENV != "production"
        else None
    ),
    redoc_url=(
        "/redoc"
        if APP_ENV != "production"
        else None
    ),
)


@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next,
):
    incoming_request_id = (
        request.headers.get(
            "X-Request-ID"
        )
    )

    try:
        uuid.UUID(
            incoming_request_id
        )
        request_id = incoming_request_id

    except (
        ValueError,
        TypeError,
        AttributeError,
    ):
        request_id = str(
            uuid.uuid4()
        )

    request.state.request_id = (
        request_id
    )

    try:
        response = await call_next(
            request
        )

    except Exception:
        logger.exception(
            "Unhandled request failure "
            "request_id=%s path=%s",
            request_id,
            request.url.path,
        )

        response = JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": (
                        "SERVICE_UNAVAILABLE"
                    ),
                    "message": (
                        "SmartHire is temporarily "
                        "unavailable. Please try again "
                        "in a few moments."
                    ),
                    "request_id": request_id,
                }
            },
        )

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)

app.include_router(
    profile_router
)

app.include_router(
    usage_router
)

app.include_router(
    llm_settings_router
)

app.include_router(
    jobs_router
)

app.include_router(
    resume_rag_router
)

app.include_router(
    job_rag_router
)
app.include_router(
    admin_router
)

@app.get("/")
async def root():
    return {
        "name": "SmartHire ATS API",
        "version": APP_VERSION,
        "endpoints": {
            "POST /api/v1/analyze-resume": (
                "Analyze a resume"
            ),
            "GET /api/v1/history": (
                "Get user history"
            ),
            "DELETE /api/v1/history/:id": (
                "Delete a history entry"
            ),
            "GET /api/v1/health": (
                "Health check"
            ),
            "POST /api/v1/generate-pdf": (
                "Generate PDF report"
            ),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )