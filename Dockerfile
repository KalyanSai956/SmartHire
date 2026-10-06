FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


# ============================================================
# System dependencies
# ============================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    curl \
    git \
    default-jre-headless \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgdk-pixbuf-2.0-0 \
    fonts-liberation \
    fonts-unifont \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


# ============================================================
# Python dependencies
# ============================================================

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch==2.14.1+cpu \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/requirements.txt


# ============================================================
# Verify PyTorch CPU installation
# ============================================================

RUN python -c "import torch; print('Torch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); assert '+cpu' in torch.__version__; assert not torch.cuda.is_available()"


# ============================================================
# Verify Java for LanguageTool
# ============================================================

RUN java -version


# ============================================================
# spaCy models
# ============================================================

RUN python -m spacy download en_core_web_sm && \
    python -m spacy download en_core_web_md


# ============================================================
# Playwright
# ============================================================

RUN playwright install chromium


# ============================================================
# Application
# ============================================================

COPY backend /app/backend


# ============================================================
# Non-root user
# ============================================================

RUN useradd \
    --create-home \
    --shell /bin/bash \
    appuser && \
    chown -R appuser:appuser /app

USER appuser

RUN java -version

RUN python -c "import language_tool_python; print('LanguageTool Python installed successfully')"
WORKDIR /app


# ============================================================
# Network / health
# ============================================================

EXPOSE 8000

HEALTHCHECK --interval=30s \
    --timeout=10s \
    --start-period=60s \
    --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1


# ============================================================
# Start FastAPI
# ============================================================

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]