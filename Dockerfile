# ============================================================
# SmartHire ATS - Multi-stage CPU Runtime
# ============================================================

# ------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Build-time dependencies only.
# These will NOT exist in the final runtime image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python -m venv /opt/venv

WORKDIR /build

COPY requirements.txt /build/requirements.txt

# Upgrade pip inside the venv
RUN pip install --upgrade pip

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    torch==2.14.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install SmartHire dependencies
RUN pip install --no-cache-dir \
    -r /build/requirements.txt

# Install ONLY the required spaCy model
RUN python -m spacy download en_core_web_sm

# Verify PyTorch installation
RUN python -c "import torch; print('Torch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); assert '+cpu' in torch.__version__; assert not torch.cuda.is_available()"

# Verify spaCy model
RUN python -c "import spacy; nlp=spacy.load('en_core_web_sm'); print('spaCy model: en_core_web_sm OK')"


# ------------------------------------------------------------
# Stage 2: Runtime
# ------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Runtime-only system packages.
#
# curl:
#   Required by Docker HEALTHCHECK.
#
# ca-certificates:
#   Required for HTTPS connections to external APIs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy only the prepared Python environment.
# Build tools such as gcc/g++/git do NOT enter runtime.
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY backend /app/backend

# Create non-root user
RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser \
    && chown -R appuser:appuser /app /opt/venv

USER appuser

WORKDIR /app

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s \
    --timeout=10s \
    --start-period=90s \
    --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]