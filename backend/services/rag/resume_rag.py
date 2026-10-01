from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.services.rag.embeddings import (
    embed_text,
    embed_texts,
)
from backend.services.rag.resume_chunker import (
    chunk_resume,
)
from backend.services.rag.resume_store import (
    count_active_resume_chunks,
    create_resume_document,
    insert_resume_chunks,
    search_resume_chunks,
)

logger = logging.getLogger(
    "smarthire.resume_rag"
)


async def index_resume(
    *,
    user_id: str,
    resume_name: str,
    resume_profile: Dict[str, Any],
    embedder,
    source_analysis_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete resume RAG indexing pipeline.

    Structured resume
        ↓
    meaningful chunks
        ↓
    embeddings
        ↓
    pgvector
    """

    # ---------------------------------------------------------
    # 1. Chunk
    # ---------------------------------------------------------

    chunks = chunk_resume(
        resume_profile
    )

    if not chunks:

        raise ValueError(
            "No meaningful resume content "
            "was available for RAG indexing."
        )

    logger.info(
        "Resume RAG created %s chunks for user=%s",
        len(chunks),
        user_id,
    )

    # ---------------------------------------------------------
    # 2. Generate embeddings
    # ---------------------------------------------------------

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    embeddings = await embed_texts(
        embedder,
        texts,
    )

    if len(embeddings) != len(chunks):

        raise RuntimeError(
            "Embedding count does not match "
            "resume chunk count."
        )

    # Attach embeddings
    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):

        chunk["embedding"] = embedding

    # ---------------------------------------------------------
    # 3. Create versioned resume document
    # ---------------------------------------------------------

    document = await create_resume_document(
        user_id=user_id,
        resume_name=resume_name,
        source_analysis_id=source_analysis_id,
    )

    resume_id = document["id"]

    # ---------------------------------------------------------
    # 4. Persist chunks
    # ---------------------------------------------------------

    inserted = await insert_resume_chunks(
        resume_id=resume_id,
        user_id=user_id,
        chunks=chunks,
    )

    logger.info(
        "Resume RAG indexed %s chunks "
        "for resume=%s user=%s",
        inserted,
        resume_id,
        user_id,
    )

    return {
        "resume_id": resume_id,
        "version": document.get(
            "version"
        ),
        "chunk_count": inserted,
        "status": "indexed",
    }


async def search_resume(
    *,
    user_id: str,
    query: str,
    embedder,
    match_threshold: float = 0.25,
    match_count: int = 8,
) -> List[Dict[str, Any]]:
    """
    Semantic search over the user's active resume.
    """

    query = query.strip()

    if not query:
        return []

    query_embedding = await embed_text(
        embedder,
        query,
    )

    return await search_resume_chunks(
        user_id=user_id,
        query_embedding=query_embedding,
        match_threshold=match_threshold,
        match_count=match_count,
    )


async def get_resume_rag_status(
    user_id: str,
) -> Dict[str, Any]:

    chunk_count = (
        await count_active_resume_chunks(
            user_id
        )
    )

    return {
        "indexed": chunk_count > 0,
        "chunk_count": chunk_count,
    }