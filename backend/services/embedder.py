"""
Lightweight embedding backend (ONNX via fastembed) that replaces
torch + sentence-transformers.

It mimics the small part of the SentenceTransformer API that SmartHire
uses (.encode / .get_embedding_dimension / .eval), so the scoring code
does not need to change. Same model (all-MiniLM-L6-v2, 384-dim).
"""
from __future__ import annotations

import threading
from typing import Any, List, Optional, Union

import numpy as np

_ALIASES = {
    "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
}


class FastEmbedder:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,  # accepted for API compatibility, ignored
        threads: Optional[int] = None,
        **_ignored: Any,
    ) -> None:
        from fastembed import TextEmbedding

        self.model_name = _ALIASES.get(model_name, model_name)
        self._model = TextEmbedding(model_name=self.model_name, threads=threads)
        self._dim: Optional[int] = None
        self._lock = threading.Lock()

    def encode(
        self,
        sentences: Union[str, List[str]],
        batch_size: int = 32,
        normalize_embeddings: bool = False,
        **_ignored: Any,  # convert_to_tensor, show_progress_bar, ...
    ) -> np.ndarray:
        single = isinstance(sentences, str)
        texts = [sentences] if single else list(sentences)

        if not texts:
            return np.zeros((0, self.get_embedding_dimension()), dtype=np.float32)

        with self._lock:
            vectors = np.asarray(
                list(self._model.embed(texts, batch_size=batch_size)),
                dtype=np.float32,
            )

        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / np.clip(norms, 1e-12, None)

        return vectors[0] if single else vectors

    def get_embedding_dimension(self) -> int:
        if self._dim is None:
            self._dim = int(len(self.encode("dimension probe")))
        return self._dim

    # older sentence-transformers name
    get_sentence_embedding_dimension = get_embedding_dimension

    def eval(self) -> "FastEmbedder":
        return self
