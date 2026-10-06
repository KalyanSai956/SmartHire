from __future__ import annotations

import os
from pathlib import Path


# ============================================================
# ENVIRONMENT
# ============================================================

try:
    from dotenv import load_dotenv

    _ENV_PATH = (
        Path(__file__).resolve().parents[2]
        / ".env"
    )

    load_dotenv(_ENV_PATH)

except ImportError:
    pass


def _env_bool(
    name: str,
    default: bool,
) -> bool:

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# ============================================================
# APPLICATION
# ============================================================

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).strip().lower()


APP_TITLE = "ATS RESUME ANALYZER API"

APP_VERSION = "1.0.0"

APP_DESCRIPTION = (
    "Analyse resumes against job descriptions "
    "using NLP and ML."
)


# ============================================================
# CORS
# ============================================================

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
]


ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        ",".join(_default_origins),
    ).split(",")
    if origin.strip()
]


# ============================================================
# FILE UPLOADS
# ============================================================

MAX_FILE_SIZE_MB = 5

MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)


SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}


# ============================================================
# NLP / EMBEDDINGS
# ============================================================

SPACY_MODEL_PRIMARY = os.getenv(
    "SPACY_MODEL_PRIMARY",
    "en_core_web_sm",
)


SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRANSFORMER_MODEL",
    "all-MiniLM-L6-v2",
)


# ============================================================
# PYTORCH / SENTENCE TRANSFORMER OPTIMIZATION
# ============================================================

# SmartHire currently uses Sentence Transformers for
# semantic ATS matching.
#
# CPU is intentional here:
# - avoids CUDA memory usage
# - avoids GPU dependency
# - keeps Docker deployment portable
# - works well with all-MiniLM-L6-v2

PYTORCH_DEVICE = os.getenv(
    "PYTORCH_DEVICE",
    "cpu",
).strip().lower()


# Number of CPU threads used by PyTorch intra-op operations.
#
# Default: 4
#
# This prevents PyTorch from aggressively consuming every
# available CPU core during embedding inference.

PYTORCH_NUM_THREADS = int(
    os.getenv(
        "PYTORCH_NUM_THREADS",
        "4",
    )
)


# Number of threads used for PyTorch inter-op operations.
#
# Keep this low for a FastAPI server so embedding inference
# does not create excessive CPU contention.

PYTORCH_NUM_INTEROP_THREADS = int(
    os.getenv(
        "PYTORCH_NUM_INTEROP_THREADS",
        "1",
    )
)


# Batch size used when generating Sentence Transformer
# embeddings.

SENTENCE_TRANSFORMER_BATCH_SIZE = int(
    os.getenv(
        "SENTENCE_TRANSFORMER_BATCH_SIZE",
        "16",
    )
)


# SentenceTransformer will normalize embeddings during
# inference.
#
# Normalized vectors allow cosine similarity to be calculated
# efficiently using a dot product.

SENTENCE_TRANSFORMER_NORMALIZE = _env_bool(
    "SENTENCE_TRANSFORMER_NORMALIZE",
    True,
)


# Maximum characters passed to semantic matching functions.
#
# This keeps embedding workloads bounded while preserving
# the existing ATS matching behavior.

SENTENCE_TRANSFORMER_MAX_TEXT_LENGTH = int(
    os.getenv(
        "SENTENCE_TRANSFORMER_MAX_TEXT_LENGTH",
        "5000",
    )
)


# ============================================================
# ATS SCORING
# ============================================================

SCORE_WEIGHTS = {
    "formatting": 20,
    "keywords": 25,
    "content": 25,
    "skill_validation": 15,
    "ats_compatibility": 15,
}


JD_KEYWORD_WEIGHT = 0.6

JD_SEMANTIC_WEIGHT = 0.4


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "",
)


SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "",
)


SUPABASE_ANON_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "",
)


SUPABASE_JWT_SECRET = os.getenv(
    "SUPABASE_JWT_SECRET",
    "",
)


# ============================================================
# AI
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    "",
)


LLM_CREDENTIAL_ENCRYPTION_KEY = (
    os.getenv(
        "LLM_CREDENTIAL_ENCRYPTION_KEY",
        "",
    ).strip()
)


PLATFORM_AI_TOKEN_LIMIT = int(
    os.getenv(
        "PLATFORM_AI_TOKEN_LIMIT",
        "100000",
    )
)


# ============================================================
# REDIS
# ============================================================

REDIS_ENABLED = _env_bool(
    "REDIS_ENABLED",
    True,
)


REDIS_REQUIRED = _env_bool(
    "REDIS_REQUIRED",
    False,
)


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
).strip()


REDIS_CONNECT_TIMEOUT = float(
    os.getenv(
        "REDIS_CONNECT_TIMEOUT",
        "2.0",
    )
)


# ============================================================
# CACHE TTL
# ============================================================

JOB_CACHE_TTL_SECONDS = int(
    os.getenv(
        "JOB_CACHE_TTL_SECONDS",
        "60",
    )
)


COMPANY_CACHE_TTL_SECONDS = int(
    os.getenv(
        "COMPANY_CACHE_TTL_SECONDS",
        "600",
    )
)


JOB_RECOMMENDATION_CACHE_TTL_SECONDS = int(
    os.getenv(
        "JOB_RECOMMENDATION_CACHE_TTL_SECONDS",
        "120",
    )
)


# ============================================================
# RATE LIMITING
# ============================================================

RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv(
        "RATE_LIMIT_WINDOW_SECONDS",
        "60",
    )
)


RATE_LIMIT_RESUME_ANALYSIS = int(
    os.getenv(
        "RATE_LIMIT_RESUME_ANALYSIS",
        "5",
    )
)


RATE_LIMIT_JOB_RECOMMENDATIONS = int(
    os.getenv(
        "RATE_LIMIT_JOB_RECOMMENDATIONS",
        "20",
    )
)


RATE_LIMIT_RESUME_SEARCH = int(
    os.getenv(
        "RATE_LIMIT_RESUME_SEARCH",
        "30",
    )
)


RATE_LIMIT_PDF = int(
    os.getenv(
        "RATE_LIMIT_PDF",
        "10",
    )
)


RATE_LIMIT_HISTORY_PDF = int(
    os.getenv(
        "RATE_LIMIT_HISTORY_PDF",
        "10",
    )
)


RATE_LIMIT_PROFILE_RESUME = int(
    os.getenv(
        "RATE_LIMIT_PROFILE_RESUME",
        "5",
    )
)


RATE_LIMIT_LLM_CONNECT = int(
    os.getenv(
        "RATE_LIMIT_LLM_CONNECT",
        "5",
    )
)