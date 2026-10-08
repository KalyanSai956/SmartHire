# SmartHire slim-image changes

Copy these files over your repo (same paths), then rebuild.

| File | Change |
|---|---|
| Dockerfile | Multi-stage, no compilers/Java/Chromium, sm spaCy model only, bakes MiniLM ONNX model, honours $PORT |
| requirements.txt | torch/sentence-transformers/playwright/language-tool/PyPDF2 removed; fastembed + weasyprint added |
| .dockerignore | Excludes .env, logs, pyc, screenshots, frontend |
| backend/services/embedder.py | NEW: FastEmbedder, same .encode() API as SentenceTransformer |
| backend/main.py | torch config removed; loads FastEmbedder |
| backend/services/{jd_matcher,resume_analyzer,ats_scorer,advanced_ats_engine}.py, backend/scripts/ingest_jobs.py | one import line swapped |
| backend/services/pdf_export.py | Playwright -> WeasyPrint |
| backend/templates/summary.html | JS colouring moved to inline styles (WeasyPrint runs no JS); bar widths now follow scores |
| backend/services/resume_parser.py | PyPDF2 -> pypdf |

Build + check:
    docker build -t smarthire .
    docker images smarthire
    docker run --rm -p 8000:8000 --env-file backend/.env smarthire
    docker stats   # keep RSS under ~450 MB for Render free
