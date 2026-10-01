from __future__ import annotations

import asyncio
from typing import List

import numpy as np

from backend.core.config import (
    SENTENCE_TRANSFORMER_MODEL,
)


EXPECTED_DIMENSION = 384


def _validate_embedding_model(
    embedder,
) -> None:

    dimension = (
        embedder.get_embedding_dimension()
    )

    if dimension != EXPECTED_DIMENSION:

        raise ValueError(
            f"Embedding dimension mismatch. "
            f"Expected {EXPECTED_DIMENSION}, "
            f"got {dimension} from "
            f"{SENTENCE_TRANSFORMER_MODEL}."
        )


def _encode(
    embedder,
    texts: List[str],
) -> List[List[float]]:

    _validate_embedding_model(
        embedder
    )

    if not texts:
        return []

    embeddings = embedder.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    if isinstance(
        embeddings,
        np.ndarray,
    ):

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(
                1,
                -1,
            )

        return [
            [
                float(value)
                for value in row
            ]
            for row in embeddings
        ]

    return [
        [
            float(value)
            for value in row
        ]
        for row in embeddings
    ]


async def embed_texts(
    embedder,
    texts: List[str],
) -> List[List[float]]:
    """
    Generate normalized embeddings without blocking
    FastAPI's event loop.
    """

    return await asyncio.to_thread(
        _encode,
        embedder,
        texts,
    )


async def embed_text(
    embedder,
    text: str,
) -> List[float]:

    results = await embed_texts(
        embedder,
        [text],
    )

    if not results:
        raise ValueError(
            "Embedding generation returned no result."
        )

    return results[0]