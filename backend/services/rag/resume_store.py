from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from backend.core.config import (
    SUPABASE_KEY,
    SUPABASE_URL,
)

logger = logging.getLogger(
    "smarthire.resume_rag"
)


def _headers() -> Dict[str, str]:

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Supabase configuration is missing."
        )

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": (
            f"Bearer {SUPABASE_KEY}"
        ),
        "Content-Type": "application/json",
    }


def _table_url(
    table: str,
) -> str:

    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/{table}"
    )


def _rpc_url(
    function_name: str,
) -> str:

    return (
        f"{SUPABASE_URL.rstrip('/')}"
        f"/rest/v1/rpc/{function_name}"
    )


async def _get(
    table: str,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.get(
            _table_url(table),
            headers=_headers(),
            params=params,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data
            if isinstance(data, list)
            else []
        )


async def _post(
    table: str,
    payload: Any,
    *,
    params: Optional[
        Dict[str, Any]
    ] = None,
    prefer: str = (
        "return=representation"
    ),
) -> List[Dict[str, Any]]:

    headers = {
        **_headers(),
        "Prefer": prefer,
    }

    async with httpx.AsyncClient(
        timeout=60.0
    ) as client:

        response = await client.post(
            _table_url(table),
            headers=headers,
            params=params or {},
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data
            if isinstance(data, list)
            else []
        )


async def _patch(
    table: str,
    params: Dict[str, Any],
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:

    headers = {
        **_headers(),
        "Prefer": "return=representation",
    }

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.patch(
            _table_url(table),
            headers=headers,
            params=params,
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data
            if isinstance(data, list)
            else []
        )


async def create_resume_document(
    *,
    user_id: str,
    resume_name: str,
    source_analysis_id: Optional[str],
) -> Dict[str, Any]:

    # ---------------------------------------------------------
    # Determine next version
    # ---------------------------------------------------------

    previous = await _get(
        "resume_documents",
        {
            "user_id": f"eq.{user_id}",
            "select": "version",
            "order": "version.desc",
            "limit": "1",
        },
    )

    next_version = 1

    if previous:

        try:
            next_version = (
                int(
                    previous[0].get(
                        "version",
                        0,
                    )
                )
                + 1
            )
        except (
            ValueError,
            TypeError,
        ):
            next_version = 1

    # ---------------------------------------------------------
    # Deactivate previous active resume
    # ---------------------------------------------------------

    await _patch(
        "resume_documents",
        {
            "user_id": f"eq.{user_id}",
            "is_active": "eq.true",
        },
        {
            "is_active": False,
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        },
    )

    # ---------------------------------------------------------
    # Create new resume document
    # ---------------------------------------------------------

    document = {
        "user_id": user_id,
        "resume_name": (
            resume_name
            or "resume"
        ),
        "source_analysis_id": (
            source_analysis_id
        ),
        "version": next_version,
        "is_active": True,
    }

    rows = await _post(
        "resume_documents",
        document,
    )

    if not rows:
        raise RuntimeError(
            "Failed to create resume document."
        )

    return rows[0]


async def insert_resume_chunks(
    *,
    resume_id: str,
    user_id: str,
    chunks: List[Dict[str, Any]],
) -> int:

    if not chunks:
        return 0

    now = datetime.now(
        timezone.utc
    ).isoformat()

    rows = []

    for chunk in chunks:

        embedding = chunk.get(
            "embedding"
        )

        if not embedding:
            continue

        rows.append(
            {
                "resume_id": resume_id,
                "user_id": user_id,
                "chunk_index": int(
                    chunk["chunk_index"]
                ),
                "section_type": chunk[
                    "section_type"
                ],
                "title": chunk.get(
                    "title",
                    "",
                ),
                "content": chunk[
                    "content"
                ],
                "metadata": chunk.get(
                    "metadata",
                    {},
                ),
                "embedding": embedding,
                "created_at": now,
            }
        )

    if not rows:
        return 0

    inserted = 0

    # Small batches prevent oversized requests.
    batch_size = 50

    for start in range(
        0,
        len(rows),
        batch_size,
    ):

        batch = rows[
            start:start + batch_size
        ]

        result = await _post(
            "resume_chunks",
            batch,
            params={
                "on_conflict": (
                    "resume_id,chunk_index"
                )
            },
            prefer=(
                "resolution=merge-duplicates,"
                "return=representation"
            ),
        )

        inserted += len(result)

    return inserted


async def search_resume_chunks(
    *,
    user_id: str,
    query_embedding: List[float],
    match_threshold: float = 0.25,
    match_count: int = 8,
) -> List[Dict[str, Any]]:

    payload = {
        "p_user_id": user_id,
        "p_query_embedding": query_embedding,
        "p_match_threshold": (
            float(match_threshold)
        ),
        "p_match_count": min(
            max(int(match_count), 1),
            20,
        ),
    }

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.post(
            _rpc_url(
                "match_resume_chunks"
            ),
            headers=_headers(),
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data
            if isinstance(data, list)
            else []
        )


async def get_active_resume(
    user_id: str,
) -> Optional[Dict[str, Any]]:

    rows = await _get(
        "resume_documents",
        {
            "user_id": f"eq.{user_id}",
            "is_active": "eq.true",
            "select": "*",
            "limit": "1",
        },
    )

    return (
        rows[0]
        if rows
        else None
    )


async def count_active_resume_chunks(
    user_id: str,
) -> int:

    rows = await _get(
        "resume_chunks",
        {
            "user_id": f"eq.{user_id}",
            "select": "id",
        },
    )

    return len(rows)